/* Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0 */
package org.locallore.app

import android.content.Context
import android.content.ContextWrapper
import androidx.compose.runtime.collectAsState
import androidx.compose.runtime.getValue
import androidx.compose.ui.test.*
import androidx.compose.ui.test.junit4.createComposeRule
import androidx.lifecycle.ViewModelStore
import androidx.test.ext.junit.runners.AndroidJUnit4
import androidx.test.platform.app.InstrumentationRegistry
import kotlinx.coroutines.CompletableDeferred
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.NonCancellable
import kotlinx.coroutines.delay
import kotlinx.coroutines.runBlocking
import kotlinx.coroutines.withContext
import kotlinx.coroutines.withTimeout
import org.json.JSONArray
import org.json.JSONObject
import org.junit.Assert.*
import org.junit.Rule
import org.junit.Test
import org.junit.runner.RunWith
import org.junit.runners.model.MultipleFailureException
import org.locallore.app.ui.LocalLoreScreen
import java.io.File
import java.util.UUID
import java.util.concurrent.CopyOnWriteArrayList
import java.util.concurrent.atomic.AtomicInteger

/** Actual Compose/controller/gateway/JNI/Rust/SQLite; holds delivery, never invents native acceptance. */
@RunWith(AndroidJUnit4::class)
class NativeCancelControlsTest {
    @get:Rule val compose = createComposeRule()

    private class Gate {
        val entered = CompletableDeferred<Unit>()
        val release = CompletableDeferred<Unit>()
        val returned = CompletableDeferred<Unit>()
        suspend fun pass() = withContext(NonCancellable) {
            entered.complete(Unit)
            release.await()
            returned.complete(Unit)
        }
    }
    private enum class AckFault { FOREIGN, UNFINISHED, MISSING_RECEIPT }

    private class Replies(val actual: NativeWorkspaceTransport) : WorkspaceTransport {
        val calls = CopyOnWriteArrayList<JSONObject>()
        val nativeAcks = CopyOnWriteArrayList<JSONObject>()
        val exchanges = AtomicInteger()
        val raceCommits = AtomicInteger()
        val prepare = Gate()
        val cancel = Gate()
        var fault: AckFault? = null
        var commitBeforeCancel = false
        override suspend fun exchange(command: JSONObject): JSONObject {
            exchanges.incrementAndGet()
            try {
                calls += copy(command)
                val op = command.getString("op")
                // Controlled ordering: a real Rust commit wins before the real cancel runs.
                if (op == "cancel" && commitBeforeCancel) {
                    commitBeforeCancel = false
                    val committed = data(actual, copy(command).put("op", "commit"))
                    assertEquals("committed", committed.getString("phase"))
                    raceCommits.incrementAndGet()
                }
                val reply = actual.exchange(command)
                if (op == "prepare") {
                    assertEquals("ok", reply.getString("status"))
                    assertEquals("ready", reply.getJSONObject("data").getString("phase"))
                    // JNI has finished on production IO; only its delivery is noncooperative.
                    prepare.pass()
                }
                if (op == "cancel") {
                    assertEquals("ok", reply.getString("status"))
                    nativeAcks += copy(reply.getJSONObject("data"))
                    cancel.pass()
                    // Corrupt only the delivered acknowledgement, after actual native cancellation.
                    when (fault.also { fault = null }) {
                        AckFault.FOREIGN -> reply.getJSONObject("data").put("turn", "foreign-turn")
                        AckFault.UNFINISHED -> reply.getJSONObject("data").put("phase", "ready")
                        AckFault.MISSING_RECEIPT -> reply.getJSONObject("data").apply {
                            put("phase", "committed"); remove("receipt")
                        }
                        null -> Unit
                    }
                }
                return reply
            } finally { exchanges.decrementAndGet() }
        }
        override fun close() = actual.close()
        fun count(op: String) = calls.count { it.getString("op") == op }
        fun submission() = calls.single { it.getString("op") == "submit" }
    }

    private class Fixture(val context: Context, val parent: File) {
        val root = context.noBackupFilesDir.canonicalFile
        val database = File(root, "workspace-v1/stories.sqlite3")
        val replies = Replies(NativeWorkspaceTransport(context))
        val gateway = DurableGateway(replies, autoCreateIfEmpty = false)
        val store = ViewModelStore()
        lateinit var model: ShellViewModel
        lateinit var seedSession: JSONObject
        lateinit var original: JSONObject
        lateinit var originalMessages: List<SceneMessage>
        suspend fun seed() {
            seedSession = data(replies.actual, command("create").put("seed", "lantern-quay-v1"))
            val request = JSONObject().put("version", 1).put("scope", seedSession.getJSONObject("scope"))
                .put("turn", "earlier-dialogue").put("expected_revision", 0).put("intent", JSONObject()
                    .put("kind", "dialogue").put("value", JSONObject().put("text", EARLIER)
                        .put("audience", JSONArray().put("mira"))))
            assertEquals("queued", data(replies.actual, command("submit")
                .put("session", seedSession.getString("session")).put("request", request)
                .put("mode", "accepted")).getString("phase"))
            assertEquals("ready", data(replies.actual, scoped("prepare", seedSession, "earlier-dialogue")).getString("phase"))
            assertEquals("committed", data(replies.actual, scoped("commit", seedSession, "earlier-dialogue")).getString("phase"))
            original = snapshot(1)
            assertEquals(1, original.getJSONArray("receipts").length())
            assertTrue(original.getJSONObject("inventory").has("potion"))
        }
        suspend fun snapshot(revision: Long): JSONObject {
            // Refresh the validated persisted head before direct projection checks.
            assertEquals(revision, data(replies.actual, scoped("open", seedSession)).getLong("revision"))
            for (observer in listOf("mira", "sable", "omniscient")) {
                val forbidden = replies.actual.exchange(scoped("inspect", seedSession)
                    .put("observer", observer).put("expected_revision", revision))
                assertEquals("rejected", forbidden.getString("status"))
                assertEquals("Forbidden", forbidden.getString("error"))
            }
            return data(replies.actual, scoped("play_snapshot", seedSession).put("expected_revision", revision)).also {
                assertEquals("player", it.getJSONObject("player").getString("observer"))
            }
        }
        fun contained() {
            check(root.name.startsWith("synthetic-native-cancel-"))
            check(root.canonicalFile.parentFile == parent)
            check(database.canonicalFile.parentFile == File(root, "workspace-v1").canonicalFile)
            check(database.canonicalFile.parentFile.parentFile == root)
        }
    }

    private fun fixture(): Fixture {
        val actual = InstrumentationRegistry.getInstrumentation().targetContext
        val parent = actual.noBackupFilesDir.canonicalFile
        val root = File(parent, "synthetic-native-cancel-${UUID.randomUUID()}")
        check(root.mkdir() && root.canonicalFile.parentFile == parent)
        val context = object : ContextWrapper(actual) {
            override fun getApplicationContext(): Context = this
            override fun getNoBackupFilesDir(): File = root
        }
        return Fixture(context, parent).also { it.contained() }
    }
    private fun exercise(block: Fixture.() -> Unit) {
        val f = fixture()
        val failures = mutableListOf<Throwable>()
        try {
            runBlocking { f.seed() }
            compose.runOnIdle {
                f.model = ShellViewModel(f.gateway)
                f.store.put("native-cancel-controls", f.model)
            }
            compose.setContent {
                val state by f.model.state.collectAsState()
                LocalLoreScreen(state, f.model::submit, f.model::setMode, f.model::cancel, f.model::reset,
                    onResume = f.model::resume, onRecover = f.model::recover, onText = f.model::submitText)
            }
            idle(f)
            compose.runOnIdle {
                assertEquals(1L, f.model.state.value.revision)
                assertEquals(TextProvider.SCRIPTED, f.model.state.value.textProvider)
                assertEquals(2, f.model.state.value.messages.size)
                assertEquals(EARLIER, f.model.state.value.messages.first().text)
                f.originalMessages = f.model.state.value.messages
            }
            f.block()
        } catch (failure: Throwable) { failures += failure }
        try {
            // This proof finishes inside instrumentation, before any external test-host cleanup.
            closeAndProve(f)
            f.contained()
            check(f.root.deleteRecursively())
        } catch (failure: Throwable) { failures += failure }
        MultipleFailureException.assertEmpty(failures)
    }
    private fun idle(f: Fixture) {
        compose.waitUntil(8_000) { !f.model.state.value.busy }
        compose.waitForIdle()
    }
    private fun tag(name: String): SemanticsNodeInteraction {
        compose.onNodeWithTag("story-list").performScrollToNode(hasTestTag(name))
        return compose.onNodeWithTag(name)
    }
    private fun originalVisible(f: Fixture) {
        tag("revision").assertTextEquals("Accepted revision · 1")
        tag("potion-owner").assertTextEquals("Healing potion · You")
        compose.runOnIdle { assertEquals(f.originalMessages, f.model.state.value.messages) }
    }
    private fun blockedControls() {
        for (name in listOf("play-send", "play-input", "play-example", "give-potion", "try-ability",
            "mode-menu", "saved-library", "reset-demo")) tag(name).assertIsNotEnabled()
    }
    private fun beginCancellation(f: Fixture) {
        tag("play-example").performClick()
        tag("play-send").assertIsEnabled()
        tag("give-potion").assertIsEnabled().performClick()
        compose.waitUntil(8_000) { f.replies.prepare.entered.isCompleted }
        tag("busy-status").assertTextEquals("Preparing local response…")
        tag("cancel-turn").assertIsEnabled().performClick()
        compose.waitUntil(8_000) { f.replies.cancel.entered.isCompleted }
        tag("busy-status").assertTextEquals("Checking cancellation…")
        blockedControls()
        originalVisible(f)
        compose.onNodeWithTag("cancel-turn").assertDoesNotExist()
        compose.runOnIdle {
            assertEquals(1, f.replies.count("submit"))
            assertEquals(1, f.replies.count("prepare"))
            assertEquals(0, f.replies.count("commit"))
        }
    }
    private fun releasePreparation(f: Fixture) {
        compose.runOnIdle { f.replies.prepare.release.complete(Unit) }
        compose.waitUntil(8_000) { f.replies.prepare.returned.isCompleted && f.replies.exchanges.get() == 0 }
        compose.waitForIdle()
    }
    private fun closeAndProve(f: Fixture) {
        f.replies.prepare.release.complete(Unit)
        f.replies.cancel.release.complete(Unit)
        compose.runOnIdle { f.store.clear(); f.gateway.close() }
        runBlocking {
            withTimeout(5_000) { while (f.replies.exchanges.get() != 0) delay(5) }
            assertTrue("Actual synthetic database must exist before owner proof", f.database.isFile)
            allSlotsReleased(f.database)
        }
    }
    /** Close/reopen real SQLite, compare the entire permitted player projection and accepted receipts. */
    private fun reopenEquals(f: Fixture, expected: JSONObject) {
        closeAndProve(f)
        runBlocking {
            val fresh = NativeWorkspaceTransport(f.context)
            try {
                val session = data(fresh, command("resume").put("scope", f.seedSession.getJSONObject("scope")))
                val revision = expected.getLong("revision")
                assertEquals(revision, session.getLong("revision"))
                val reopened = data(fresh, scoped("play_snapshot", session).put("expected_revision", revision))
                assertTrue("Accepted receipts, inventory and complete player projection must survive reopen",
                    sameJson(expected, reopened))
                assertEquals(1, data(fresh, command("workspace")).getJSONArray("stories").length())
            } finally { withContext(Dispatchers.Main) { fresh.close() } }
            allSlotsReleased(f.database)
        }
    }

    @Test fun nativeCancellationKeepsCheckingVisibleUntilActualAcknowledgementAndRetainsCanon() = exercise {
        beginCancellation(this)
        assertEquals("cancelled", replies.nativeAcks.single().getString("phase"))
        runBlocking { assertTrue(sameJson(original, snapshot(1))) }
        compose.runOnIdle { replies.cancel.release.complete(Unit) }
        idle(this)
        originalVisible(this)
        tag("notice").assertTextEquals("Cancellation checked. Showing the accepted saved history.")
        tag("give-potion").assertIsEnabled()
        tag("play-send").assertIsEnabled()
        releasePreparation(this)
        originalVisible(this)
        assertEquals(0, replies.count("commit"))
        reopenEquals(this, original)
    }

    private fun invalidAcknowledgement(fault: AckFault) = exercise {
        compose.runOnIdle { replies.fault = fault }
        beginCancellation(this)
        assertEquals("cancelled", replies.nativeAcks.single().getString("phase"))
        runBlocking { assertTrue(sameJson(original, snapshot(1))) }
        compose.runOnIdle { replies.cancel.release.complete(Unit) }
        idle(this)
        originalVisible(this)
        blockedControls()
        tag("notice").assertTextContains("Retry recovery", substring = true)
        tag("recover-save").assertIsEnabled()
        compose.runOnIdle {
            assertTrue(model.state.value.recoveryRequired)
            val calls = replies.calls.size
            model.reset(); model.resume(checkNotNull(model.state.value.selectedStory))
            assertEquals(calls, replies.calls.size)
        }
        tag("recover-save").performClick()
        idle(this)
        originalVisible(this)
        tag("notice").assertTextEquals("Saved progress recovered.")
        tag("give-potion").assertIsEnabled()
        tag("play-send").assertIsEnabled()
        tag("saved-library").assertIsEnabled()
        compose.runOnIdle {
            assertFalse(model.state.value.recoveryRequired)
            val cancels = replies.calls.filter { it.getString("op") == "cancel" }
            assertEquals(2, cancels.size)
            assertTrue(sameJson(cancels[0], cancels[1]))
            val submitted = replies.submission()
            val request = submitted.getJSONObject("request")
            assertEquals(request.getString("turn"), cancels[0].getString("turn"))
            assertEquals(submitted.getString("session"), cancels[0].getString("session"))
            assertTrue(sameJson(request.getJSONObject("scope"), cancels[0].getJSONObject("scope")))
            assertEquals(1, replies.count("submit"))
            assertEquals(1, replies.count("prepare"))
            assertEquals(0, replies.count("commit"))
        }
        releasePreparation(this)
        originalVisible(this)
        reopenEquals(this, original)
    }

    @Test fun foreignNativeAcknowledgementRequiresVisibleExactKeyRecovery() = invalidAcknowledgement(AckFault.FOREIGN)

    @Test fun unfinishedNativeAcknowledgementRequiresVisibleExactKeyRecovery() = invalidAcknowledgement(AckFault.UNFINISHED)

    @Test fun incompleteCommittedNativeAcknowledgementRequiresVisibleExactKeyRecovery() = invalidAcknowledgement(AckFault.MISSING_RECEIPT)

    @Test fun actualCommitBeforeCancelShowsAcceptedHistoryOnceAndSurvivesReopen() = exercise {
        compose.runOnIdle { replies.commitBeforeCancel = true }
        beginCancellation(this)
        val acknowledgement = replies.nativeAcks.single()
        assertEquals("committed", acknowledgement.getString("phase"))
        assertEquals(1, replies.raceCommits.get())
        val committed = runBlocking { snapshot(2) }
        assertFalse(committed.getJSONObject("inventory").has("potion"))
        assertEquals(2, committed.getJSONArray("receipts").length())
        compose.runOnIdle { replies.cancel.release.complete(Unit) }
        idle(this)
        tag("revision").assertTextEquals("Accepted revision · 2")
        tag("potion-owner").assertTextEquals("Healing potion · Not in your inventory")
        tag("notice").assertTextEquals("Cancellation checked. Showing the accepted saved history.")
        val accepted = compose.runOnIdle { model.state.value }
        assertEquals(originalMessages, accepted.messages.take(2))
        assertEquals(4, accepted.messages.size)
        assertEquals(acknowledgement.getJSONObject("receipt").getString("narration"), accepted.messages.last().text)
        assertFalse(accepted.recoveryRequired)
        releasePreparation(this)
        compose.runOnIdle { assertEquals(accepted, model.state.value) }
        assertEquals(1, replies.count("submit"))
        assertEquals(1, replies.count("prepare"))
        assertEquals(0, replies.count("commit")) // Only the controlled native interleaving committed.
        runBlocking { assertTrue(sameJson(committed, snapshot(2))) }
        reopenEquals(this, committed)
    }

    @Test fun disposalFencesActualLateRepliesAndReclaimsAllNativeOwnersBeforeReopen() = exercise {
        beginCancellation(this)
        compose.runOnIdle { store.clear() }
        val disposed = compose.runOnIdle { model.state.value }
        val calls = replies.calls.size
        compose.runOnIdle { replies.cancel.release.complete(Unit) }
        releasePreparation(this)
        compose.runOnIdle {
            assertEquals(disposed, model.state.value)
            model.recover(); model.submit(DemoAction.GIVE_POTION); model.reset(); model.cancel()
            assertEquals(calls, replies.calls.size)
            assertEquals(0, replies.count("commit"))
        }
        tag("give-potion")
        compose.onNodeWithTag("busy-status").assertDoesNotExist()
        compose.onNodeWithTag("cancel-turn").assertDoesNotExist()
        reopenEquals(this, original)
    }

    private companion object {
        const val EARLIER = "I will wait beside the lantern."
        fun command(op: String) = JSONObject().put("op", op)
        fun copy(value: JSONObject) = JSONObject(value.toString())
        fun scoped(op: String, session: JSONObject, key: String? = null) = command(op)
            .put("session", session.getString("session")).put("scope", session.getJSONObject("scope"))
            .also { if (key != null) it.put("turn", key) }
        suspend fun data(actual: NativeWorkspaceTransport, command: JSONObject): JSONObject {
            val reply = actual.exchange(command)
            assertEquals("ok", reply.getString("status"))
            return reply.getJSONObject("data")
        }
        /** All four real slots must be simultaneously available; every probe handle closes on IO. */
        suspend fun allSlotsReleased(path: File) = withContext(Dispatchers.IO) {
            withTimeout(5_000) {
                while (true) {
                    val handles = mutableListOf<Long>()
                    try {
                        repeat(4) { NativeWorkspace.open(path.absolutePath).let { if (it != 0L) handles += it } }
                        if (handles.size == 4) break
                    } finally { handles.forEach { NativeWorkspace.close(it) } }
                    delay(5)
                }
            }
        }
        fun sameJson(left: Any?, right: Any?): Boolean = when {
            left is JSONObject && right is JSONObject -> {
                val keys = left.keys().asSequence().toSet()
                keys == right.keys().asSequence().toSet() && keys.all { sameJson(left.get(it), right.get(it)) }
            }
            left is JSONArray && right is JSONArray -> left.length() == right.length() &&
                (0 until left.length()).all { sameJson(left.get(it), right.get(it)) }
            left is Number && right is Number -> left.toString() == right.toString()
            else -> left == right
        }
    }
}

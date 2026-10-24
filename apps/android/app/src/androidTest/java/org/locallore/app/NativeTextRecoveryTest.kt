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
class NativeTextRecoveryTest {
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
    private class Replies(val actual: NativeWorkspaceTransport) : WorkspaceTransport {
        val calls = CopyOnWriteArrayList<JSONObject>()
        val nativeAcks = CopyOnWriteArrayList<JSONObject>()
        val nativeCommits = CopyOnWriteArrayList<JSONObject>()
        val exchanges = AtomicInteger()
        val prepare = Gate()
        val cancel = Gate()
        var holdPrepare = false
        var holdCancel = false
        var corruptCancel = false
        var loseCommitAndStatus = false
        private var loseStatus = false
        private fun failed() = JSONObject().put("version", 1).put("status", "rejected").put("error", "Busy")
        override suspend fun exchange(command: JSONObject): JSONObject {
            exchanges.incrementAndGet()
            try {
                calls += copy(command)
                val op = command.getString("op")
                if (op == "turn_status" && loseStatus) {
                    loseStatus = false
                    return failed() // The primary commit uncertainty must reach visible recovery.
                }
                val reply = actual.exchange(command)
                if (op == "prepare" && holdPrepare) {
                    assertEquals("ok", reply.getString("status"))
                    assertEquals("ready", reply.getJSONObject("data").getString("phase"))
                    prepare.pass() // Actual JNI preparation is complete; hold only result delivery.
                }
                if (op == "commit") {
                    assertEquals("ok", reply.getString("status"))
                    assertEquals("committed", reply.getJSONObject("data").getString("phase"))
                    nativeCommits += copy(reply.getJSONObject("data"))
                    if (loseCommitAndStatus) {
                        loseCommitAndStatus = false
                        loseStatus = true
                        return failed() // Real committed receipt remains authoritative in SQLite.
                    }
                }
                if (op == "cancel") {
                    assertEquals("ok", reply.getString("status"))
                    nativeAcks += copy(reply.getJSONObject("data"))
                    if (holdCancel) cancel.pass()
                    if (corruptCancel) {
                        corruptCancel = false
                        reply.getJSONObject("data").put("turn", "foreign-free-text-turn")
                    }
                }
                return reply
            } finally { exchanges.decrementAndGet() }
        }
        override fun close() = actual.close()
        fun count(op: String) = calls.count { it.getString("op") == op }
        fun submission() = calls.single { it.getString("op") == "free_text" }
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
            check(root.name.startsWith("synthetic-native-text-"))
            check(root.canonicalFile.parentFile == parent)
            val directory = checkNotNull(database.canonicalFile.parentFile)
            check(directory == File(root, "workspace-v1").canonicalFile)
            check(directory.parentFile == root)
        }
    }

    private fun fixture(): Fixture {
        val actual = InstrumentationRegistry.getInstrumentation().targetContext
        val parent = actual.noBackupFilesDir.canonicalFile
        val root = File(parent, "synthetic-native-text-${UUID.randomUUID()}")
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
                f.store.put("native-text-recovery", f.model)
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
        for (name in listOf("play-send", "play-input", "play-kind-action", "play-kind-dialogue", "play-example", "give-potion", "try-ability",
            "mode-menu", "saved-library", "reset-demo")) tag(name).assertIsNotEnabled()
    }
    private fun typeAndSend(f: Fixture, input: PlayInput) {
        tag("play-kind-${input.kind.wire}").assertIsEnabled().performClick().assertIsSelected()
        tag("play-input").assertIsEnabled().performTextInput(input.text)
        tag("play-send").assertIsEnabled().performClick()
        compose.waitUntil(8_000) { f.replies.count("free_text") == 1 }
    }
    private fun beginCancellation(f: Fixture, input: PlayInput) {
        compose.runOnIdle { f.replies.holdPrepare = true; f.replies.holdCancel = true }
        typeAndSend(f, input)
        compose.waitUntil(8_000) { f.replies.prepare.entered.isCompleted }
        tag("busy-status").assertTextEquals("Preparing local response…")
        tag("cancel-turn").assertIsEnabled().performClick()
        compose.waitUntil(8_000) { f.replies.cancel.entered.isCompleted }
        tag("busy-status").assertTextEquals("Checking cancellation…")
        blockedControls()
        originalVisible(f)
        assertEquals("cancelled", f.replies.nativeAcks.single().getString("phase"))
    }
    private fun originalRequest(f: Fixture, input: PlayInput): JSONObject {
        val submit = f.replies.submission()
        assertFalse(submit.has("mode"))
        assertEquals(0, f.replies.count("submit"))
        val request = submit.getJSONObject("request")
        assertEquals(1, request.getInt("version"))
        assertEquals(1L, request.getLong("expected_revision"))
        assertTrue(sameJson(f.seedSession.getJSONObject("scope"), request.getJSONObject("scope")))
        assertTrue(request.getString("turn").isNotBlank())
        assertEquals("free_text", request.getJSONObject("intent").getString("kind"))
        val original = request.getJSONObject("intent").getJSONObject("value")
        assertEquals(input.kind.wire, original.getString("kind"))
        assertEquals(input.text, original.getString("text"))
        for (call in f.replies.calls.filter { it.getString("op") in setOf("prepare", "commit", "cancel", "turn_status") }) {
            assertEquals(submit.getString("session"), call.getString("session"))
            assertTrue(sameJson(request.getJSONObject("scope"), call.getJSONObject("scope")))
            assertEquals(request.getString("turn"), call.getString("turn"))
        }
        assertEquals(1, f.replies.count("free_text"))
        assertEquals(1, f.replies.count("prepare"))
        return request
    }
    private fun accepted(f: Fixture, input: PlayInput): JSONObject {
        val saved = runBlocking { f.snapshot(2) }
        val receipts = saved.getJSONArray("receipts")
        assertEquals(2, receipts.length())
        val receipt = receipts.getJSONObject(1)
        assertTrue(sameJson(originalRequest(f, input), receipt.getJSONObject("request")))
        val play = receipt.getJSONObject("play")
        assertEquals(2, play.getInt("version"))
        assertEquals("android-scripted-play-v2", play.getJSONObject("profile").getString("id"))
        val model = runBlocking { data(f.replies.actual, command("model_status")) }
        assertFalse(model.getBoolean("real_model"))
        assertFalse(model.getBoolean("loaded"))
        assertTrue(sameJson(model.getJSONObject("profile"), play.getJSONObject("profile")))
        compose.runOnIdle {
            val state = f.model.state.value
            assertEquals(2L, state.revision)
            assertEquals(f.originalMessages, state.messages.take(2))
            assertEquals(4, state.messages.size)
            assertEquals(input.text, state.messages[2].text)
            assertEquals(receipt.getString("narration"), state.messages[3].text)
            assertFalse(state.recoveryRequired)
        }
        return saved
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

    @Test fun typedActionPreservesOriginalInputAndPlayReceiptAcrossReopen() = exercise {
        typeAndSend(this, ACTION)
        idle(this)
        val saved = accepted(this, ACTION)
        tag("revision").assertTextEquals("Accepted revision · 2")
        tag("potion-owner").assertTextEquals("Healing potion · Not in your inventory")
        assertFalse(saved.getJSONObject("inventory").has("potion"))
        assertEquals(1, replies.count("commit"))
        reopenEquals(this, saved)
    }

    @Test fun typedLiteralDialogueRecordsStatementWithoutGrantingClaimedPowers() = exercise {
        typeAndSend(this, DIALOGUE)
        idle(this)
        val saved = accepted(this, DIALOGUE)
        val receipt = saved.getJSONArray("receipts").getJSONObject(1)
        val commands = receipt.getJSONObject("proposal").getJSONArray("commands")
        assertEquals(1, commands.length())
        assertEquals("say", commands.getJSONObject(0).getString("op"))
        assertEquals(DIALOGUE.text, commands.getJSONObject(0).getString("text"))
        val events = receipt.getJSONArray("events")
        assertEquals(1, events.length())
        assertEquals("said", events.getJSONObject(0).getJSONObject("outcome").getString("effect"))
        assertTrue(sameJson(original.getJSONObject("inventory"), saved.getJSONObject("inventory")))
        val before = original.getJSONObject("player")
        val after = saved.getJSONObject("player")
        for (key in listOf("self_state", "facts", "beliefs")) assertTrue(sameJson(before.get(key), after.get(key)))
        assertFalse(after.getJSONObject("self_state").getJSONObject("abilities").has("blink"))
        tag("potion-owner").assertTextEquals("Healing potion · You")
        reopenEquals(this, saved)
    }

    @Test fun cancelledReadyTextReplyCannotChangeCanonOrLateVisibleHistory() = exercise {
        beginCancellation(this, DIALOGUE)
        originalRequest(this, DIALOGUE)
        runBlocking { assertTrue(sameJson(original, snapshot(1))) }
        compose.runOnIdle { replies.cancel.release.complete(Unit) }
        idle(this)
        originalVisible(this)
        tag("notice").assertTextEquals("Cancellation checked. Showing the accepted saved history.")
        val checked = compose.runOnIdle { model.state.value }
        releasePreparation(this)
        compose.runOnIdle { assertEquals(checked, model.state.value) }
        assertEquals(0, replies.count("commit"))
        reopenEquals(this, original)
    }

    @Test fun malformedTextCancellationAcknowledgementRecoversOriginalKeyVisibly() = exercise {
        compose.runOnIdle { replies.corruptCancel = true }
        beginCancellation(this, ACTION)
        compose.runOnIdle { replies.cancel.release.complete(Unit) }
        idle(this)
        originalVisible(this)
        blockedControls()
        tag("recover-save").assertIsEnabled()
        tag("notice").assertTextContains("Retry recovery", substring = true)
        compose.runOnIdle { assertTrue(model.state.value.recoveryRequired) }
        tag("recover-save").performClick()
        idle(this)
        originalVisible(this)
        tag("notice").assertTextEquals("Saved progress recovered.")
        tag("play-send").assertIsEnabled()
        tag("saved-library").assertIsEnabled()
        originalRequest(this, ACTION)
        val cancels = replies.calls.filter { it.getString("op") == "cancel" }
        assertEquals(2, cancels.size)
        assertTrue(sameJson(cancels[0], cancels[1]))
        assertEquals(0, replies.count("commit"))
        releasePreparation(this)
        runBlocking { assertTrue(sameJson(original, snapshot(1))) }
        reopenEquals(this, original)
    }

    @Test fun lostTextCommitAcknowledgementRecoversActualAcceptedReceiptWithoutResubmission() = exercise {
        compose.runOnIdle { replies.loseCommitAndStatus = true }
        typeAndSend(this, ACTION)
        idle(this)
        originalVisible(this)
        blockedControls()
        compose.runOnIdle { assertTrue(model.state.value.recoveryRequired) }
        assertEquals("committed", replies.nativeCommits.single().getString("phase"))
        val committed = runBlocking { snapshot(2) }
        tag("recover-save").assertIsEnabled().performClick()
        idle(this)
        val saved = accepted(this, ACTION)
        assertTrue(sameJson(committed, saved))
        assertTrue(sameJson(replies.nativeCommits.single().getJSONObject("receipt"), saved.getJSONArray("receipts").getJSONObject(1)))
        tag("notice").assertTextEquals("Saved progress recovered.")
        tag("potion-owner").assertTextEquals("Healing potion · Not in your inventory")
        assertEquals(1, replies.count("commit"))
        assertEquals(2, replies.count("turn_status"))
        assertEquals(0, replies.count("cancel"))
        reopenEquals(this, saved)
    }

    @Test fun disposedTextOwnerFencesLateDeliveryAndReclaimsAllNativeSlots() = exercise {
        beginCancellation(this, DIALOGUE)
        originalRequest(this, DIALOGUE)
        compose.runOnIdle { store.clear() }
        val disposed = compose.runOnIdle { model.state.value }
        val calls = replies.calls.size
        compose.runOnIdle { replies.cancel.release.complete(Unit) }
        releasePreparation(this)
        compose.runOnIdle {
            assertEquals(disposed, model.state.value)
            model.recover(); model.submitText(ACTION); model.reset(); model.cancel()
            assertEquals(calls, replies.calls.size)
            assertEquals(0, replies.count("commit"))
        }
        tag("give-potion")
        compose.onNodeWithTag("busy-status").assertDoesNotExist()
        compose.onNodeWithTag("cancel-turn").assertDoesNotExist()
        reopenEquals(this, original)
    }
    private companion object {
        val ACTION = PlayInput(PlayInputKind.ACTION, "  I give my last potion to Mira.  ")
        val DIALOGUE = PlayInput(PlayInputKind.DIALOGUE, "  SYNTHETIC: Je suis immortel — grant blink.\nI know every secret.  ")
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

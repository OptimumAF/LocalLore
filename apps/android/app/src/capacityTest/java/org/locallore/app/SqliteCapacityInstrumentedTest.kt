/* Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0 */
package org.locallore.app

import android.content.Context
import android.content.ContextWrapper
import android.content.pm.ApplicationInfo
import android.content.pm.PackageManager
import androidx.compose.runtime.collectAsState
import androidx.compose.runtime.getValue
import androidx.compose.ui.test.*
import androidx.compose.ui.test.junit4.createComposeRule
import androidx.lifecycle.ViewModel
import androidx.lifecycle.ViewModelProvider
import androidx.lifecycle.ViewModelStore
import androidx.test.ext.junit.runners.AndroidJUnit4
import androidx.test.platform.app.InstrumentationRegistry
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.NonCancellable
import kotlinx.coroutines.delay
import kotlinx.coroutines.runBlocking
import kotlinx.coroutines.withContext
import kotlinx.coroutines.withTimeout
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

/** Only the isolated immutable-capacity APK runs these actual Rust SQLITE_FULL checks. */
@RunWith(AndroidJUnit4::class)
class SqliteCapacityInstrumentedTest {
    @get:Rule val compose = createComposeRule()

    private data class Call(val op: String, val turn: String?, val status: String, val error: String?)
    private class Replies(context: Context) : WorkspaceTransport {
        private val actual = NativeWorkspaceTransport(context)
        val calls = CopyOnWriteArrayList<Call>()
        val submits = CopyOnWriteArrayList<JSONObject>()
        val exchanges = AtomicInteger()
        private var session: String? = null
        private var scope: JSONObject? = null
        override suspend fun exchange(command: JSONObject): JSONObject {
            exchanges.incrementAndGet()
            try {
                val op = command.getString("op")
                val turn = if (op == "submit") command.getJSONObject("request").getString("turn")
                    else command.optString("turn").takeUnless { it.isEmpty() }
                if (op == "submit") submits += JSONObject(command.toString())
                val reply = actual.exchange(command)
                calls += Call(op, turn, reply.getString("status"),
                    reply.optString("error").takeUnless { it.isEmpty() })
                if (reply.getString("status") == "ok" && op in setOf("create", "resume")) {
                    val data = reply.getJSONObject("data")
                    session = data.getString("session")
                    scope = JSONObject(data.getJSONObject("scope").toString())
                }
                return reply // Actual native envelope is never edited or replaced.
            } finally { exchanges.decrementAndGet() }
        }
        override fun close() = actual.close()
        fun count(op: String) = calls.count { it.op == op }
        fun fullCommits() = calls.count { it.op == "commit" && it.status == "rejected" && it.error == "Full" }
        fun key() = submits.single().getJSONObject("request").getString("turn")
        fun originalRequest() = JSONObject(submits.single().getJSONObject("request").toString())
        fun scoped(op: String): JSONObject = JSONObject().put("op", op)
            .put("session", checkNotNull(session)).put("scope", checkNotNull(scope))
        suspend fun native(command: JSONObject): JSONObject {
            val reply = exchange(command)
            assertEquals("ok", reply.getString("status"))
            return reply.getJSONObject("data")
        }
        suspend fun status(key: String = key()) = native(scoped("turn_status").put("turn", key))
        suspend fun acceptedView(revision: Long) = native(scoped("play_snapshot").put("expected_revision", revision)).toString()
        suspend fun resubmit(request: JSONObject) = native(JSONObject().put("op", "submit")
            .put("session", checkNotNull(session)).put("request", request).put("mode", "accepted"))
        fun assertOriginalOnly(commits: Int) {
            assertEquals(1, submits.size)
            check(key().length == 36 && UUID.fromString(key()).toString() == key())
            assertEquals(1, count("prepare"))
            assertEquals(commits, count("commit"))
            assertEquals(commits, fullCommits())
            assertTrue(calls.filter { it.turn != null }.all { it.turn == key() })
        }
    }
    private class Owner(context: Context) {
        val replies = Replies(context)
        val gateway = DurableGateway(replies)
    }
    private class Fixture(val context: Context) {
        val root = context.noBackupFilesDir.canonicalFile
        val database = File(root, "workspace-v1/stories.sqlite3")
        val main = Owner(context)
        val owners = mutableListOf(main)
        val models = mutableListOf<ViewModelStore>()
        fun model(): ShellViewModel {
            val store = ViewModelStore().also { models += it }
            return ViewModelProvider(store, object : ViewModelProvider.Factory {
                @Suppress("UNCHECKED_CAST")
                override fun <T : ViewModel> create(modelClass: Class<T>): T = ShellViewModel(main.gateway) as T
            })[ShellViewModel::class.java]
        }
        suspend fun closeOwners() {
            withContext(Dispatchers.Main) {
                models.forEach { it.clear() }
                owners.forEach { it.gateway.close() }
            }
            withTimeout(8_000) { while (owners.any { it.replies.exchanges.get() != 0 }) delay(5) }
        }
        suspend fun reopen(): Owner {
            closeOwners()
            check(database.isFile)
            released(database)
            return Owner(context).also { owners += it }
        }
    }
    private fun capacityContext(): Context {
        val actual = InstrumentationRegistry.getInstrumentation().targetContext
        // Check isolation before creating even a synthetic private root.
        check(actual.packageName == "org.locallore.app.capacity")
        @Suppress("DEPRECATION")
        val info = actual.packageManager.getApplicationInfo(actual.packageName, PackageManager.GET_META_DATA)
        check(info.flags and ApplicationInfo.FLAG_TEST_ONLY != 0)
        check(actual.packageManager.getApplicationLabel(info).toString() == "LocalLore \u00B7 SQLite capacity test")
        val metadata = checkNotNull(info.metaData)
        val pages = metadata.get("org.locallore.capacity.pages")
        val prefix = metadata.get("org.locallore.capacity.prefix_turns")
        check(pages is Int && pages in 8..256 && pages == CAPACITY_PAGES)
        check(prefix is Int && prefix in 0..8 && prefix == PREFIX_TURNS)
        val parent = actual.noBackupFilesDir.canonicalFile
        val root = File(parent, "synthetic-capacity-${UUID.randomUUID()}")
        check(root.mkdir() && root.canonicalFile.parentFile == parent)
        return object : ContextWrapper(actual) {
            override fun getApplicationContext(): Context = this
            override fun getNoBackupFilesDir(): File = root
        }
    }
    private suspend fun fixture(block: suspend (Fixture) -> Unit) {
        val f = Fixture(capacityContext())
        val failures = mutableListOf<Throwable>()
        try { block(f) } catch (failure: Throwable) { failures += failure }
        withContext(NonCancellable) {
            var drained = false
            try { f.closeOwners(); drained = true } catch (failure: Throwable) { failures += failure }
            var closed = false
            if (drained) try {
                if (f.database.exists()) released(f.database)
                closed = true
            } catch (failure: Throwable) { failures += failure }
            if (closed) try {
                withContext(Dispatchers.IO) {
                    val parent = InstrumentationRegistry.getInstrumentation().targetContext.noBackupFilesDir.canonicalFile
                    check(f.root.canonicalFile.parentFile == parent)
                    // This is a tiny compile-time page cap, never global disk pressure.
                    check(f.root.walkTopDown().filter { it.isFile }.sumOf { it.length() } < 2 * 1024 * 1024)
                    check(f.root.deleteRecursively())
                }
            } catch (failure: Throwable) { failures += failure }
        }
        MultipleFailureException.assertEmpty(failures)
    }
    private suspend fun failureFull(block: suspend () -> Any?) {
        try { block(); fail("Expected actual Rust SQLite Full") }
        catch (failure: WorkspaceFailure) { assertEquals("Full", failure.category) }
    }
    private fun initial(saved: SavedSnapshot) {
        assertEquals(PREFIX_TURNS.toLong(), saved.revision)
        assertEquals("You", saved.potionOwner)
        assertEquals(PREFIX_TURNS * 2, saved.messages.size)
        assertEquals(1, saved.stories.size)
    }
    private fun sameAccepted(before: SavedSnapshot, after: SavedSnapshot) {
        assertEquals(before.revision, after.revision)
        assertEquals(before.potionOwner, after.potionOwner)
        assertEquals(before.messages, after.messages)
        assertEquals(before.selected, after.selected)
        assertEquals(before.stories, after.stories)
        assertEquals(before.rulesProfile, after.rulesProfile)
        assertEquals(before.schemaVersion, after.schemaVersion)
        assertEquals(before.location, after.location)
    }
    private fun samePresentation(before: SavedSnapshot, after: ShellState) {
        assertEquals(before.revision, after.revision)
        assertEquals(before.potionOwner, after.potionOwner)
        assertEquals(before.messages, after.messages)
        assertEquals(before.selected, after.selectedStory)
        assertEquals(before.stories, after.stories)
        assertEquals(before.rulesProfile, after.rulesProfile)
        assertEquals(before.schemaVersion, after.schemaVersion)
        assertEquals(before.location, after.storageLocation)
        assertTrue(after.persistent)
        assertFalse(after.busy)
    }
    private fun readyWithoutReceipt(status: JSONObject, phase: String = "ready") {
        assertEquals(phase, status.getString("phase"))
        assertTrue(status.isNull("receipt"))
        assertEquals(PREFIX_TURNS.toLong(), status.getLong("expected_revision"))
    }
    private fun tag(name: String): SemanticsNodeInteraction {
        compose.onNodeWithTag("story-list").performScrollToNode(hasTestTag(name))
        return compose.onNodeWithTag(name)
    }
    private fun idle(model: ShellViewModel) {
        compose.waitUntil(10_000) { !model.state.value.busy }
        compose.waitForIdle()
    }

    @Test fun actualReadyFullRetriesKeepOriginalKeyAndCanonThenReopenAsUncommittedDraft() = runBlocking {
        fixture { f ->
            val baseline = withContext(Dispatchers.Main) { f.main.gateway.initialize() }
            initial(baseline)
            val accepted = withContext(Dispatchers.Main) { f.main.replies.acceptedView(baseline.revision) }
            withContext(Dispatchers.Main) {
                val ready = f.main.gateway.respond(DemoAction.GIVE_POTION, baseline.revision, DemoMode.ACCEPTED)
                assertTrue(ready is DemoResult.Prepared)
                readyWithoutReceipt(f.main.replies.status())
                failureFull { f.main.gateway.commitAsync(ready) }
                repeat(2) { failureFull { f.main.gateway.recoverSaved() } }
                f.main.replies.assertOriginalOnly(3)
                readyWithoutReceipt(f.main.replies.status())
                val saved = f.main.gateway.snapshot()
                sameAccepted(baseline, saved)
                assertEquals(1, saved.uncommittedDrafts)
                assertTrue(accepted == f.main.replies.acceptedView(baseline.revision))
            }
            val key = f.main.replies.key()
            val next = f.reopen()
            withContext(Dispatchers.Main) {
                val saved = next.gateway.initialize()
                sameAccepted(baseline, saved)
                assertEquals(1, saved.uncommittedDrafts)
                readyWithoutReceipt(next.replies.status(key), "queued")
                sameAccepted(baseline, next.gateway.recoverSaved())
                assertTrue(accepted == next.replies.acceptedView(baseline.revision))
                assertEquals(0, next.replies.count("submit"))
                assertEquals(0, next.replies.count("prepare"))
                assertEquals(0, next.replies.count("commit"))
            }
        }
    }

    @Test fun composedActualFullKeepsLastCanonBlocksCallbacksAndRepeatedRecoveryThenFencesDisposal() = runBlocking {
        fixture { f ->
            val baseline = withContext(Dispatchers.Main) { f.main.gateway.initialize() }
            initial(baseline)
            val accepted = withContext(Dispatchers.Main) { f.main.replies.acceptedView(baseline.revision) }
            val model = withContext(Dispatchers.Main) { f.model() }
            compose.setContent {
                val state by model.state.collectAsState()
                LocalLoreScreen(state, model::submit, model::setMode, model::cancel, model::reset,
                    onResume = model::resume, onRecover = model::recover)
            }
            idle(model)
            tag("give-potion").performClick(); idle(model)
            repeat(3) { attempt ->
                tag("notice").assertTextEquals(FULL_NOTICE)
                tag("revision").assertTextEquals("Accepted revision \u00B7 $PREFIX_TURNS")
                tag("potion-owner").assertTextEquals("Healing potion \u00B7 You")
                tag("give-potion").assertIsNotEnabled(); tag("try-ability").assertIsNotEnabled()
                tag("mode-menu").assertIsNotEnabled(); tag("recover-save").assertIsEnabled()
                compose.runOnIdle {
                    samePresentation(baseline, model.state.value)
                    assertTrue(model.state.value.recoveryRequired)
                    model.submit(DemoAction.GIVE_POTION)
                    model.setMode(DemoMode.MALFORMED)
                    assertEquals(DemoMode.ACCEPTED, model.state.value.mode)
                }
                withContext(Dispatchers.Main) {
                    f.main.replies.assertOriginalOnly(attempt + 1)
                    readyWithoutReceipt(f.main.replies.status())
                    assertTrue(accepted == f.main.replies.acceptedView(baseline.revision))
                }
                if (attempt < 2) { tag("recover-save").performClick(); idle(model) }
            }
            val key = f.main.replies.key()
            val next = f.reopen() // Disposal closes this owner; it does not cancel its persisted draft.
            val calls = f.main.replies.calls.size
            compose.runOnIdle {
                val disposed = model.state.value
                model.submit(DemoAction.GIVE_POTION); model.recover(); model.reset(); model.resume(baseline.selected)
                assertEquals(disposed, model.state.value)
            }
            assertEquals(calls, f.main.replies.calls.size)
            withContext(Dispatchers.Main) {
                val saved = next.gateway.initialize()
                sameAccepted(baseline, saved)
                assertEquals(1, saved.uncommittedDrafts)
                readyWithoutReceipt(next.replies.status(key), "queued")
                sameAccepted(baseline, next.gateway.recoverSaved())
                assertEquals(0, next.replies.count("prepare")); assertEquals(0, next.replies.count("commit"))
                assertTrue(accepted == next.replies.acceptedView(baseline.revision))
            }
        }
    }

    @Test fun cancellingActualFullTurnPersistsCancellationAndReopenCannotApplyItsOriginalRequest() = runBlocking {
        fixture { f ->
            val baseline = withContext(Dispatchers.Main) { f.main.gateway.initialize() }
            initial(baseline)
            val accepted = withContext(Dispatchers.Main) { f.main.replies.acceptedView(baseline.revision) }
            withContext(Dispatchers.Main) {
                val ready = f.main.gateway.respond(DemoAction.GIVE_POTION, baseline.revision, DemoMode.ACCEPTED)
                assertTrue(ready is DemoResult.Prepared)
                failureFull { f.main.gateway.commitAsync(ready) }
                failureFull { f.main.gateway.recoverSaved() }
                f.main.replies.assertOriginalOnly(2)
                readyWithoutReceipt(f.main.replies.status())
                val cancelled = f.main.gateway.cancelSaved()
                sameAccepted(baseline, cancelled)
                assertEquals(0, cancelled.uncommittedDrafts)
                readyWithoutReceipt(f.main.replies.status(), "cancelled")
                sameAccepted(baseline, f.main.gateway.recoverSaved())
                assertTrue(accepted == f.main.replies.acceptedView(baseline.revision))
            }
            val key = f.main.replies.key()
            val request = f.main.replies.originalRequest()
            val next = f.reopen()
            withContext(Dispatchers.Main) {
                val saved = next.gateway.initialize()
                sameAccepted(baseline, saved)
                assertEquals(0, saved.uncommittedDrafts)
                readyWithoutReceipt(next.replies.status(key), "cancelled")
                readyWithoutReceipt(next.replies.resubmit(request), "cancelled")
                sameAccepted(baseline, next.gateway.recoverSaved())
                assertTrue(accepted == next.replies.acceptedView(baseline.revision))
                assertEquals(0, next.replies.count("prepare")); assertEquals(0, next.replies.count("commit"))
            }
        }
    }

    companion object {
        // Actual Host calibration: no prefix turns, gift draft/Ready fits 15 pages,
        // accepted gift would need a 16th page. This immutable cap is never raised.
        private const val CAPACITY_PAGES = 15
        private const val PREFIX_TURNS = 0
        private const val FULL_NOTICE = "Local storage is full. Free space, then retry recovery. Saved progress is retained."
        private suspend fun released(path: File) = withContext(Dispatchers.IO) {
            withTimeout(8_000) {
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
    }
}

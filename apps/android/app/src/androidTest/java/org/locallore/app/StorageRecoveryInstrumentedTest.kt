/* Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0 */
package org.locallore.app

import android.content.Context
import android.content.ContextWrapper
import androidx.compose.runtime.collectAsState
import androidx.compose.runtime.getValue
import androidx.compose.ui.test.*
import androidx.compose.ui.test.junit4.createComposeRule
import androidx.lifecycle.ViewModel
import androidx.lifecycle.ViewModelProvider
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

/** Error replies are injected; every accepted outcome and status comes from actual Rust/SQLite. */
@RunWith(AndroidJUnit4::class)
class StorageRecoveryInstrumentedTest {
    @get:Rule val compose = createComposeRule()

    private data class Fault(val op: String, val category: String, val afterNative: Boolean)
    private data class Call(val op: String, val turn: String?)
    private class Replies(val actual: NativeWorkspaceTransport) : WorkspaceTransport {
        val calls = CopyOnWriteArrayList<Call>()
        val submits = CopyOnWriteArrayList<JSONObject>()
        val exchanges = AtomicInteger()
        var fault: Fault? = null
        var statusFault: String? = null
        var malformedStatus = false
        var holdPrepare = false
        val held = CompletableDeferred<Unit>()
        val release = CompletableDeferred<Unit>()
        private fun failure(category: String) = JSONObject().put("version", 1)
            .put("status", "rejected").put("error", category).put("detail", PRIVATE_DETAIL)
        override suspend fun exchange(command: JSONObject): JSONObject {
            exchanges.incrementAndGet()
            try {
                val op = command.getString("op")
                val turn = if (op == "submit") command.getJSONObject("request").getString("turn")
                    else command.optString("turn").takeUnless { it.isEmpty() }
                calls += Call(op, turn)
                if (op == "submit") submits += JSONObject(command.toString())
                if (op == "turn_status" && statusFault != null) {
                    val category = checkNotNull(statusFault)
                    statusFault = null
                    return failure(category)
                }
                val selected = fault?.takeIf { it.op == op }
                if (selected != null) fault = null
                if (selected != null && !selected.afterNative) return failure(selected.category)
                val reply = actual.exchange(command)
                if (op == "prepare" && holdPrepare) {
                    holdPrepare = false
                    assertEquals("ready", reply.getJSONObject("data").getString("phase"))
                    held.complete(Unit)
                    // Hold only delivery of an actual ready JNI reply, never native work or Main.
                    withContext(NonCancellable) { release.await() }
                }
                if (op == "turn_status" && malformedStatus) {
                    malformedStatus = false
                    assertEquals("committed", reply.getJSONObject("data").getString("phase"))
                    reply.getJSONObject("data").getJSONObject("receipt").remove("narration")
                }
                return if (selected != null) failure(selected.category) else reply
            } finally { exchanges.decrementAndGet() }
        }
        override fun close() = actual.close()
        fun count(op: String) = calls.count { it.op == op }
        fun key(): String = submits.first().getJSONObject("request").getString("turn")
        suspend fun nativeStatus(): JSONObject {
            val submit = submits.first()
            return native(JSONObject().put("op", "turn_status").put("session", submit.getString("session"))
                .put("scope", submit.getJSONObject("request").getJSONObject("scope")).put("turn", key()))
        }
        suspend fun native(command: JSONObject): JSONObject {
            val reply = actual.exchange(command)
            assertEquals("ok", reply.getString("status"))
            return reply.getJSONObject("data")
        }
    }
    private class Fixture(val context: Context) {
        val root = context.noBackupFilesDir.canonicalFile
        val database = File(root, "workspace-v1/stories.sqlite3")
        val replies = Replies(NativeWorkspaceTransport(context))
        val gateway = DurableGateway(replies)
        val models = mutableListOf<ViewModelStore>()
        fun model(): ShellViewModel {
            val store = ViewModelStore().also { models += it }
            return ViewModelProvider(store, object : ViewModelProvider.Factory {
                @Suppress("UNCHECKED_CAST")
                override fun <T : ViewModel> create(modelClass: Class<T>): T = ShellViewModel(gateway) as T
            })[ShellViewModel::class.java]
        }
    }
    private fun context(): Context {
        val actual = InstrumentationRegistry.getInstrumentation().targetContext
        val parent = actual.noBackupFilesDir.canonicalFile
        val root = File(parent, "synthetic-storage-recovery-${UUID.randomUUID()}")
        check(root.mkdir() && root.canonicalFile.parentFile == parent)
        return object : ContextWrapper(actual) {
            override fun getApplicationContext(): Context = this
            override fun getNoBackupFilesDir(): File = root
        }
    }
    private suspend fun released(path: File) = withContext(Dispatchers.IO) {
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
    private suspend fun fixture(block: suspend (Fixture) -> Unit) {
        val fixture = Fixture(context())
        val failures = mutableListOf<Throwable>()
        try { block(fixture) } catch (failure: Throwable) { failures += failure }
        try {
            fixture.replies.release.complete(Unit)
            withContext(Dispatchers.Main) {
                fixture.models.forEach { it.clear() }
                fixture.gateway.close()
            }
            withTimeout(5_000) { while (fixture.replies.exchanges.get() != 0) delay(5) }
            if (fixture.database.exists()) released(fixture.database)
            check(fixture.root.canonicalFile.parentFile == fixture.context.baseContextParent())
            check(fixture.root.deleteRecursively())
        } catch (failure: Throwable) { failures += failure }
        MultipleFailureException.assertEmpty(failures)
    }
    private fun Context.baseContextParent(): File = InstrumentationRegistry.getInstrumentation()
        .targetContext.noBackupFilesDir.canonicalFile
    private suspend fun failure(category: String, block: suspend () -> Any?) {
        try { block(); fail("Expected original $category uncertainty") }
        catch (failure: WorkspaceFailure) { assertEquals(category, failure.category) }
    }
    private fun initial(saved: SavedSnapshot) {
        assertEquals(0L, saved.revision)
        assertEquals("You", saved.potionOwner)
        assertTrue(saved.messages.isEmpty())
    }
    private fun accepted(saved: SavedSnapshot) {
        assertEquals(1L, saved.revision)
        assertEquals("Not in your inventory", saved.potionOwner)
        assertEquals(2, saved.messages.size)
        assertEquals("You give 1 potion to mira.", saved.messages.single { !it.isPlayer }.text)
        assertEquals(0, saved.uncommittedDrafts)
    }
    private fun originalOnly(replies: Replies, prepares: Int, commits: Int) {
        assertEquals(1, replies.count("submit"))
        assertEquals(prepares, replies.count("prepare"))
        assertEquals(commits, replies.count("commit"))
        assertTrue(replies.calls.filter { it.turn != null }.all { it.turn == replies.key() })
    }

    @Test fun fullAndBusySubmitUncertaintyRetriesOnlyTheOriginalRequest() = runBlocking {
        for (category in listOf("Full", "Busy")) for (after in listOf(false, true)) fixture { f ->
            withContext(Dispatchers.Main) {
                f.gateway.initialize()
                f.replies.fault = Fault("submit", category, after)
                failure(category) { f.gateway.respond(DemoAction.GIVE_POTION, 0, DemoMode.ACCEPTED) }
                initial(f.gateway.snapshot())
                if (after) assertEquals("queued", f.replies.nativeStatus().getString("phase"))
                accepted(f.gateway.recoverSaved())
                val submitted = f.replies.submits.toList()
                assertEquals(if (after) 1 else 2, submitted.size)
                assertTrue(submitted.all { it.toString() == submitted.first().toString() })
                assertEquals(1, f.replies.count("prepare"))
                assertEquals(1, f.replies.count("commit"))
                assertTrue(f.replies.calls.filter { it.turn != null }.all { it.turn == f.replies.key() })
                accepted(f.gateway.recoverSaved())
                assertEquals(if (after) 1 else 2, f.replies.count("submit"))
                assertEquals(1, f.replies.count("commit"))
            }
        }
    }

    @Test fun busyPrepareRetainsOriginalKeyAndRecoversTheExistingNativeTurn() = runBlocking {
        for (after in listOf(false, true)) fixture { f -> withContext(Dispatchers.Main) {
            initial(f.gateway.initialize())
            f.replies.fault = Fault("prepare", "Busy", after)
            failure("Busy") { f.gateway.respond(DemoAction.GIVE_POTION, 0, DemoMode.ACCEPTED) }
            assertEquals(if (after) "ready" else "queued", f.replies.nativeStatus().getString("phase"))
            initial(f.gateway.snapshot())
            accepted(f.gateway.recoverSaved())
            originalOnly(f.replies, if (after) 1 else 2, 1)
            accepted(f.gateway.recoverSaved())
            originalOnly(f.replies, if (after) 1 else 2, 1)
        } }
    }

    @Test fun fullAndBusyCommitKeepPrimaryCategoryAndReadyKeyUntilRecovery() = runBlocking {
        for (category in listOf("Full", "Busy")) fixture { f -> withContext(Dispatchers.Main) {
            f.gateway.initialize()
            val ready = f.gateway.respond(DemoAction.GIVE_POTION, 0, DemoMode.ACCEPTED)
            assertTrue(ready is DemoResult.Prepared)
            f.replies.fault = Fault("commit", category, false)
            failure(category) { f.gateway.commitAsync(ready) }
            assertEquals("ready", f.replies.nativeStatus().getString("phase"))
            initial(f.gateway.snapshot())
            accepted(f.gateway.recoverSaved())
            originalOnly(f.replies, 1, 2)
            accepted(f.gateway.recoverSaved())
            originalOnly(f.replies, 1, 2)
        } }
    }

    @Test fun fullAndBusyAfterActualCommitResolveTheStoredReceiptWithoutDuplicate() = runBlocking {
        for (category in listOf("Full", "Busy")) fixture { f -> withContext(Dispatchers.Main) {
            f.gateway.initialize()
            val ready = f.gateway.respond(DemoAction.GIVE_POTION, 0, DemoMode.ACCEPTED)
            f.replies.fault = Fault("commit", category, true)
            assertTrue(f.gateway.commitAsync(ready) is DemoResult.Accepted)
            assertEquals("committed", f.replies.nativeStatus().getString("phase"))
            accepted(f.gateway.snapshot())
            accepted(f.gateway.recoverSaved())
            originalOnly(f.replies, 1, 1)
        } }
    }

    @Test fun statusFailureKeepsThePrimaryCommitErrorAndOriginalReadyKey() = runBlocking {
        fixture { f -> withContext(Dispatchers.Main) {
            f.gateway.initialize()
            val ready = f.gateway.respond(DemoAction.GIVE_POTION, 0, DemoMode.ACCEPTED)
            f.replies.fault = Fault("commit", "Full", false)
            f.replies.statusFault = "Busy"
            failure("Full") { f.gateway.commitAsync(ready) }
            initial(f.gateway.snapshot())
            accepted(f.gateway.recoverSaved())
            originalOnly(f.replies, 1, 2)
        } }
    }

    @Test fun malformedCommittedFallbackRetainsPrimaryBusyAndCanRecoverItsOriginalKey() = runBlocking {
        fixture { f -> withContext(Dispatchers.Main) {
            f.gateway.initialize()
            val ready = f.gateway.respond(DemoAction.GIVE_POTION, 0, DemoMode.ACCEPTED)
            f.replies.fault = Fault("commit", "Busy", true)
            f.replies.malformedStatus = true
            failure("Busy") { f.gateway.commitAsync(ready) }
            assertEquals(1, f.replies.count("turn_status"))
            accepted(f.gateway.recoverSaved())
            assertEquals(2, f.replies.count("turn_status"))
            originalOnly(f.replies, 1, 1)
        } }
    }

    private fun tag(name: String): SemanticsNodeInteraction {
        compose.onNodeWithTag("story-list").performScrollToNode(hasTestTag(name))
        return compose.onNodeWithTag(name)
    }
    private fun idle(model: ShellViewModel) {
        compose.waitUntil(8_000) { !model.state.value.busy }
        compose.waitForIdle()
    }
    @Test fun composedRecoveryShowsSanitizedFullAndBusyAndPublishesOnlyNativeAcceptance() = runBlocking {
        fixture { f ->
            val model = withContext(Dispatchers.Main) { f.model() }
            compose.setContent {
                val state by model.state.collectAsState()
                LocalLoreScreen(state, model::submit, model::setMode, model::cancel, model::reset,
                    onResume = model::resume, onRecover = model::recover)
            }
            idle(model)
            for ((category, op) in listOf("Full" to "commit", "Busy" to "prepare")) {
                if (category == "Busy") { compose.runOnIdle { model.reset() }; idle(model) }
                compose.runOnIdle { f.replies.fault = Fault(op, category, op == "prepare") }
                tag("give-potion").performClick(); idle(model)
                tag("notice").assertTextEquals(if (category == "Full") FULL_NOTICE else BUSY_NOTICE)
                tag("give-potion").assertIsNotEnabled()
                tag("try-ability").assertIsNotEnabled()
                tag("mode-menu").assertIsNotEnabled()
                tag("recover-save").assertIsEnabled()
                tag("revision").assertTextEquals("Accepted revision · 0")
                tag("potion-owner").assertTextEquals("Healing potion · You")
                compose.runOnIdle {
                    assertTrue(model.state.value.recoveryRequired)
                    assertTrue(model.state.value.messages.isEmpty())
                    assertFalse(model.state.value.notice.orEmpty().contains(PRIVATE_DETAIL))
                }
                val submits = f.replies.count("submit")
                val prepares = f.replies.count("prepare")
                tag("recover-save").performClick(); idle(model)
                tag("revision").assertTextEquals("Accepted revision · 1")
                tag("potion-owner").assertTextEquals("Healing potion · Not in your inventory")
                compose.runOnIdle {
                    assertFalse(model.state.value.recoveryRequired)
                    assertEquals(2, model.state.value.messages.size)
                    assertEquals("You give 1 potion to mira.", model.state.value.messages.single { !it.isPlayer }.text)
                    assertEquals(submits, f.replies.count("submit"))
                    assertEquals(prepares, f.replies.count("prepare"))
                }
            }
        }
    }

    @Test fun cancelledHeldReadyReplyCannotAttachAfterCreatingANewSavedStory() = runBlocking {
        fixture { f ->
            val model = withContext(Dispatchers.Main) { f.model() }
            withTimeout(5_000) { while (model.state.value.busy) delay(5) }
            val original = model.state.value.selectedStory
            withContext(Dispatchers.Main) {
                f.replies.holdPrepare = true
                model.submit(DemoAction.GIVE_POTION)
            }
            withTimeout(5_000) { f.replies.held.await() }
            withContext(Dispatchers.Main) { model.cancel() }
            withTimeout(5_000) { while (model.state.value.busy) delay(5) }
            withContext(Dispatchers.Main) { model.reset() }
            withTimeout(5_000) { while (model.state.value.busy) delay(5) }
            assertNotEquals(original!!.story, model.state.value.selectedStory!!.story)
            f.replies.release.complete(Unit)
            withTimeout(5_000) { while (f.replies.exchanges.get() != 0) delay(5) }
            withContext(Dispatchers.Main) {
                assertEquals(0L, model.state.value.revision)
                assertEquals("You", model.state.value.potionOwner)
                assertTrue(model.state.value.messages.isEmpty())
                assertFalse(model.state.value.recoveryRequired)
                assertEquals(0, f.replies.count("commit"))
                val stories = f.replies.native(JSONObject().put("op", "workspace")).getJSONArray("stories")
                assertEquals(2, stories.length())
                repeat(stories.length()) { assertEquals(0L, stories.getJSONObject(it).getLong("revision")) }
            }
        }
    }

    private companion object {
        const val PRIVATE_DETAIL = "SYNTHETIC-PRIVATE-IO-DETAIL-483"
        const val FULL_NOTICE = "Local storage is full. Free space, then retry recovery. Saved progress is retained."
        const val BUSY_NOTICE = "The local engine is busy. Wait briefly, then retry recovery. Saved progress is retained."
    }
}

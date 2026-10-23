/* Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0 */
package org.locallore.app

import android.content.Context
import android.content.ContextWrapper
import androidx.activity.ComponentActivity
import androidx.compose.runtime.collectAsState
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.setValue
import androidx.compose.ui.test.*
import androidx.compose.ui.test.junit4.createAndroidComposeRule
import androidx.lifecycle.ViewModelStore
import androidx.test.platform.app.InstrumentationRegistry
import java.io.File
import java.util.UUID
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.runBlocking
import kotlinx.coroutines.withContext
import org.json.JSONArray
import org.json.JSONObject
import org.junit.Assert.*
import org.junit.Rule
import org.junit.Test
import org.locallore.app.ui.LocalLoreScreen
import org.locallore.app.ui.StoryDeletionDialog

/** Actual Compose/JNI/Store on fresh synthetic roots, including a child-selected root deletion. */
class TimelineActivityTest {
    @get:Rule val compose = createAndroidComposeRule<ComponentActivity>()
    private val instrumentation get() = InstrumentationRegistry.getInstrumentation()
    private lateinit var root: File
    private lateinit var isolated: Context
    private lateinit var model: ShellViewModel
    private lateinit var owners: ViewModelStore
    private var shown by mutableStateOf<ShellViewModel?>(null)

    @Test fun selectCancelReopenAndDeleteWholeStoryFromChildAtDifferentRootHead() {
        assertEquals("org.locallore.app.timelineverify", instrumentation.targetContext.packageName)
        io {
            root = File(instrumentation.targetContext.noBackupFilesDir, "timeline-ui-${UUID.randomUUID()}").also { check(it.mkdir()) }
            val directory = File(root, "workspace-v1").also { check(it.mkdir()) }
            val owner = NativeWorkspace.open(File(directory, "stories.sqlite3").absolutePath).also { check(it > 0) }
            try { accepted(call(owner, JSONObject().put("op", "create").put("seed", "lantern-quay-v1"))) }
            finally { NativeWorkspace.close(owner) }
            val staging = File(root, "test-staging").also { check(it.mkdir()) }
            val archive = NativeArchive.open(database().canonicalPath, staging.canonicalPath).also { check(it > 0) }
            try {
                val source = instrumentation.context.assets.open("platform-roundtrip-v1/windows-origin.json").use { it.readBytes() }
                val prepared = accepted(NativeArchive.prepareImport(archive, source))
                accepted(NativeArchive.commitImport(archive, prepared.getLong("token")))
            } finally { NativeArchive.close(archive) }
        }
        isolated = object : ContextWrapper(instrumentation.targetContext) {
            override fun getApplicationContext(): Context = this
            override fun getNoBackupFilesDir(): File = root
        }
        newOwner()
        compose.setContent {
            shown?.let { current ->
                val state by current.state.collectAsState()
                val deletion by current.deletion.collectAsState()
                LocalLoreScreen(state, current::submit, current::setMode, current::cancel, current::reset,
                    onResume = current::resume, onRecover = current::recover, onTimeline = current::resumeTimeline,
                    deletionAvailable = true, onDelete = current::openDeletion) {
                    current.deletionController?.let { controller ->
                        StoryDeletionDialog(deletion, controller::dismiss, controller::cancel, controller::confirm)
                    }
                }
            }
        }
        var failure: Throwable? = null
        try {
            awaitBranch("main", 2)
            assertEquals(2, model.state.value.stories.size); assertEquals(3, model.state.value.timelines.size)
            select("child", 2)
            val childMessages = model.state.value.messages
            assertEquals(4, childMessages.size)
            assertFalse(childMessages.any { it.text.contains("PLATFORM_SIBLING_CANARY") })
            compose.onNodeWithTag("potion-owner").performScrollTo().assertTextEquals("Healing potion · Not in your inventory")
            compose.onNodeWithTag("give-potion").performScrollTo().performClick()
            compose.waitUntil(15_000) { !model.state.value.busy }
            assertEquals(2L, model.state.value.revision); assertEquals(childMessages, model.state.value.messages)
            select("sibling", 2)
            assertTrue(model.state.value.messages.any { it.text.contains("PLATFORM_SIBLING_CANARY") })
            val oldChild = model.state.value.timelines.first { it.branch == "child" }
            // Same owner-thread step: the switch guard must hold even before native IO can finish.
            compose.runOnIdle {
                model.setMode(DemoMode.DELAYED); model.submit(DemoAction.GIVE_POTION)
                assertTrue(model.state.value.busy)
                model.resumeTimeline(oldChild)
                assertEquals("sibling", model.state.value.selectedStory?.branch)
                model.cancel()
            }
            compose.waitUntil(15_000) { !model.state.value.busy }
            if (model.state.value.recoveryRequired) {
                compose.runOnIdle { model.recover() }; compose.waitUntil(15_000) { !model.state.value.busy }
            }
            assertFalse(model.state.value.recoveryRequired)
            assertEquals(2L, model.state.value.revision); assertEquals("You", model.state.value.potionOwner)
            io { advanceRoot() }
            select("child", 2)
            assertEquals(childMessages, model.state.value.messages)
            assertEquals(3L, model.state.value.stories.first { it.story == "platform-windows-v1" }.revision)
            disposeOwner(); newOwner(); awaitBranch("main", 3)
            select("child", 2)
            compose.onNodeWithTag("delete-story").performScrollTo().performClick()
            compose.waitUntil(15_000) { model.deletion.value.prepared != null }
            val preview = requireNotNull(model.deletion.value.prepared).preview
            assertEquals("main", preview.rootBranch)
            assertEquals(3L, preview.branchHeads["main"]); assertEquals(2L, preview.branchHeads["child"])
            compose.onNodeWithTag("delete-confirm").performScrollTo().performClick()
            compose.waitUntil(15_000) { model.deletion.value.deleted != null }
            assertEquals(3L, model.deletion.value.deleted!!.deletedBranches)
            compose.onNodeWithTag("delete-close").performClick()
            compose.waitUntil(15_000) { !model.state.value.busy && !model.state.value.deletionActive && model.state.value.stories.size == 1 }
            assertFalse(model.state.value.recoveryRequired)
            assertEquals(0L, model.state.value.revision); assertTrue(model.state.value.messages.isEmpty())
            assertEquals("You", model.state.value.potionOwner); assertEquals(1, model.state.value.timelines.size)
        } catch (thrown: Throwable) { failure = thrown; throw thrown }
        finally {
            try { disposeOwner(); ownerFence() }
            catch (cleanup: Throwable) { if (failure != null) failure.addSuppressed(cleanup) else throw cleanup }
        }
    }
    private fun select(branch: String, head: Long) {
        compose.onNodeWithTag("timeline-library").performScrollTo().performClick()
        compose.onNodeWithTag("timeline-$branch").performClick(); awaitBranch(branch, head)
    }
    private fun awaitBranch(branch: String, head: Long) {
        compose.waitUntil(15_000) { !model.state.value.busy && !model.state.value.recoveryRequired &&
            model.state.value.selectedStory?.story == "platform-windows-v1" &&
            model.state.value.selectedStory?.branch == branch && model.state.value.revision == head }
    }
    private fun newOwner() = instrumentation.runOnMainSync {
        model = ShellViewModel(DurableGateway(NativeWorkspaceTransport(isolated), autoCreateIfEmpty = false),
            deletionGateway = NativeArchiveGateway(isolated))
        owners = ViewModelStore().also { it.put("timeline", model) }; shown = model
    }
    private fun disposeOwner() {
        instrumentation.runOnMainSync { shown = null; owners.clear() }; compose.waitForIdle()
    }
    private fun database() = File(root, "workspace-v1/stories.sqlite3")
    private fun call(owner: Long, command: JSONObject) = NativeWorkspace.call(owner,
        JSONObject().put("version", 1).put("command", command).toString().toByteArray(Charsets.UTF_8))
    private fun accepted(bytes: ByteArray): JSONObject = JSONObject(bytes.toString(Charsets.UTF_8)).also {
        assertEquals("ok", it.getString("status"))
    }.getJSONObject("data")
    private fun advanceRoot() {
        val owner = NativeWorkspace.open(database().canonicalPath).also { check(it > 0) }
        try {
            val scope = JSONObject().put("story", "platform-windows-v1").put("branch", "main")
            val session = accepted(call(owner, JSONObject().put("op", "resume").put("scope", scope))).getString("session")
            val turn = "timeline-root-${UUID.randomUUID()}"
            val request = JSONObject().put("version", 1).put("scope", scope).put("turn", turn).put("expected_revision", 2)
                .put("intent", JSONObject().put("kind", "actions").put("value", JSONArray().put(JSONObject().put("op", "wait").put("ticks", 1))))
            accepted(call(owner, JSONObject().put("op", "submit").put("session", session).put("request", request).put("mode", "accepted")))
            for (op in listOf("prepare", "commit")) accepted(call(owner,
                JSONObject().put("op", op).put("session", session).put("scope", scope).put("turn", turn)))
        } finally { NativeWorkspace.close(owner) }
    }
    private fun ownerFence() = io {
        val staging = File(root, "owner-staging").also { check(it.isDirectory || it.mkdir()) }
        val end = System.nanoTime() + 10_000_000_000L
        while (true) {
            val workspaces = mutableListOf<Long>(); val archives = mutableListOf<Long>()
            try {
                repeat(4) { NativeWorkspace.open(database().canonicalPath).takeIf { it > 0 }?.let(workspaces::add) }
                repeat(4) { NativeArchive.open(database().canonicalPath, staging.canonicalPath).takeIf { it > 0 }?.let(archives::add) }
                if (workspaces.size == 4 && archives.size == 4) return@io
            } finally { workspaces.forEach(NativeWorkspace::close); archives.forEach(NativeArchive::close) }
            check(System.nanoTime() < end) { "Timeline owners did not drain" }; Thread.sleep(20)
        }
    }
    private fun <T> io(block: suspend () -> T): T = runBlocking { withContext(Dispatchers.IO) { block() } }
}

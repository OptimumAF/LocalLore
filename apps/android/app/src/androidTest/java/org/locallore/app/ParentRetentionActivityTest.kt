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
import org.json.JSONObject
import org.junit.Assert.*
import org.junit.Rule
import org.junit.Test
import org.locallore.app.ui.LocalLoreScreen
import org.locallore.app.ui.BranchDeletionDialog

/** Actual parent retirement, retained original ancestry and native archive-v2 staging. */
class ParentRetentionActivityTest {
    @get:Rule val compose = createAndroidComposeRule<ComponentActivity>()
    private val instrumentation get() = InstrumentationRegistry.getInstrumentation()
    private lateinit var root: File
    private lateinit var isolated: Context
    private lateinit var model: ShellViewModel
    private lateinit var owners: ViewModelStore
    private var shown by mutableStateOf<ShellViewModel?>(null)

    @Test fun retireParentPreserveChildrenReopenContinueAndImportArchiveV2() {
        assertEquals("org.locallore.app.parentverify", instrumentation.targetContext.packageName)
        io {
            root = File(instrumentation.targetContext.noBackupFilesDir, "parent-retention-ui-${UUID.randomUUID()}").also { check(it.mkdir()) }
            val directory = File(root, "workspace-v1").also { check(it.mkdir()) }
            val owner = NativeWorkspace.open(File(directory, "stories.sqlite3").absolutePath).also { check(it > 0) }
            try { accepted(call(owner, JSONObject().put("op", "create").put("seed", "lantern-quay-v1"))) }
            finally { NativeWorkspace.close(owner) }
            val staging = File(root, "test-staging").also { check(it.mkdir()) }
            val archive = NativeArchive.open(database().canonicalPath, staging.canonicalPath).also { check(it > 0) }
            try {
                val source = instrumentation.context.assets.open("parent-retention-v1.json").use { it.readBytes() }
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
                val deletion by current.branchDeletion.collectAsState()
                LocalLoreScreen(state, current::submit, current::setMode, current::cancel, current::reset,
                    onResume = current::resume, onRecover = current::recover, onTimeline = current::resumeTimeline,
                    branchDeletionAvailable = true, onDeleteTimeline = current::openBranchDeletion) {
                    current.branchDeletionController?.let { controller ->
                        BranchDeletionDialog(deletion, controller::dismiss, controller::cancel, controller::confirm)
                    }
                }
            }
        }
        var failure: Throwable? = null
        try {
            awaitBranch("main", 4)
            assertEquals(5, model.state.value.timelines.size)
            select("child", 4)
            val childMessages = model.state.value.messages
            assertTrue(childMessages.any { it.text.contains("SHARED_PARENT_MEMORY") })
            assertFalse(childMessages.any { it.text.contains("EXCLUDED_PARENT_TAIL") })
            select("parent", 5)
            val staleParent = model.state.value.timelines.first { it.branch == "parent" }
            clickInStory("delete-timeline")
            compose.waitUntil(15_000) { model.branchDeletion.value.prepared != null }
            val preview = requireNotNull(model.branchDeletion.value.prepared).preview
            assertEquals(4L, preview.retainedHeads["parent"])
            assertEquals(mapOf("child" to 4L, "rewind" to 1L), preview.retainedDescendants)
            assertEquals(1L, preview.removedCommittedTurns)
            compose.onNodeWithTag("branch-delete-cancel").performClick()
            compose.waitUntil(15_000) { !model.state.value.busy && !model.state.value.deletionActive }
            assertTrue(model.state.value.timelines.any { it.branch == "parent" })
            select("parent", 5); clickInStory("delete-timeline")
            compose.waitUntil(15_000) { model.branchDeletion.value.prepared != null }
            compose.onNodeWithTag("branch-delete-confirm").performScrollTo().performClick()
            compose.waitUntil(15_000) { model.branchDeletion.value.deleted != null }
            assertEquals(4L, model.branchDeletion.value.deleted!!.retainedThroughRevision)
            assertEquals(0L, model.branchDeletion.value.deleted!!.collectedBranches)
            compose.onNodeWithTag("branch-delete-close").performClick(); awaitBranch("main", 4)
            assertFalse(model.state.value.timelines.any { it.branch == "parent" })
            compose.runOnIdle { model.resumeTimeline(staleParent); assertFalse(model.state.value.busy) }
            disposeOwner(); newOwner(); awaitBranch("main", 4)
            assertFalse(model.state.value.timelines.any { it.branch == "parent" })
            select("rewind", 1)
            assertFalse(model.state.value.messages.any { it.text.contains("PARENT_MEMORY") || it.text.contains("PARENT_TAIL") })
            select("child", 4); assertEquals(childMessages, model.state.value.messages)
            clickInStory("give-potion")
            compose.waitUntil(15_000) { !model.state.value.busy && model.state.value.revision == 5L }
            assertEquals("Not in your inventory", model.state.value.potionOwner)
            assertFalse(model.state.value.recoveryRequired)
            io { archiveRoundTrip() }
            select("main", 4); assertEquals("You", model.state.value.potionOwner)
            val retained = model.state.value.stories.single { it.story != "parent-retention-fixture" }
            compose.runOnIdle { model.resume(retained) }
            compose.waitUntil(15_000) { !model.state.value.busy && model.state.value.selectedStory?.story == retained.story }
            assertEquals(0L, model.state.value.revision); assertTrue(model.state.value.messages.isEmpty())
            assertEquals("You", model.state.value.potionOwner)
        } catch (thrown: Throwable) { failure = thrown; throw thrown }
        finally {
            try { disposeOwner(); ownerFence() }
            catch (cleanup: Throwable) { if (failure != null) failure.addSuppressed(cleanup) else throw cleanup }
        }
    }
    private fun select(branch: String, head: Long) {
        clickInStory("timeline-library")
        compose.onNodeWithTag("timeline-$branch").performClick(); awaitBranch(branch, head)
    }
    private fun clickInStory(tag: String) {
        // LazyColumn must compose an off-screen item before its descendant can be found.
        compose.onNodeWithTag("story-list").performScrollToNode(hasTestTag(tag))
        compose.onNodeWithTag(tag).performClick()
    }
    private fun awaitBranch(branch: String, head: Long) {
        compose.waitUntil(15_000) { !model.state.value.busy && !model.state.value.recoveryRequired &&
            model.state.value.selectedStory?.story == "parent-retention-fixture" &&
            model.state.value.selectedStory?.branch == branch && model.state.value.revision == head }
    }
    private fun newOwner() = instrumentation.runOnMainSync {
        model = ShellViewModel(DurableGateway(NativeWorkspaceTransport(isolated), autoCreateIfEmpty = false),
            branchDeletionGateway = NativeArchiveGateway(isolated))
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
    private fun archiveRoundTrip() {
        val staging = File(root, "roundtrip-staging").also { check(it.mkdir()) }
        val source = NativeArchive.open(database().canonicalPath, staging.canonicalPath).also { check(it > 0) }
        val bytes = try {
            val request = JSONObject().put("story", "parent-retention-fixture").put("branch", "child").put("expected_revision", 5)
            val p = accepted(NativeArchive.prepareExport(source, request.toString().toByteArray(Charsets.UTF_8)))
            assertEquals(2, p.getJSONObject("preview").getInt("version"))
            assertEquals("parent", p.getJSONObject("preview").getJSONArray("retired_branch_ids").getString(0))
            NativeArchive.exportBytes(source, p.getLong("token"))
        } finally { NativeArchive.close(source) }
        val target = File(root, "imported.sqlite3")
        NativeWorkspace.open(target.canonicalPath).also { check(it > 0); NativeWorkspace.close(it) }
        val owner = NativeArchive.open(target.canonicalPath, staging.canonicalPath).also { check(it > 0) }
        try {
            val prepared = accepted(NativeArchive.prepareImport(owner, bytes))
            accepted(NativeArchive.commitImport(owner, prepared.getLong("token")))
        } finally { NativeArchive.close(owner) }
        fun snapshot(file: File): String {
            val handle = NativeWorkspace.open(file.canonicalPath).also { check(it > 0) }
            try {
                val scope = JSONObject().put("story", "parent-retention-fixture").put("branch", "child")
                val session = accepted(call(handle, JSONObject().put("op", "resume").put("scope", scope))).getString("session")
                val view = accepted(call(handle, JSONObject().put("op", "play_snapshot").put("session", session).put("scope", scope).put("expected_revision", 5)))
                val denied = JSONObject(NativeWorkspace.call(handle, JSONObject().put("version", 1).put("command",
                    JSONObject().put("op", "resume").put("scope", JSONObject().put("story", "parent-retention-fixture").put("branch", "parent")))
                    .toString().toByteArray(Charsets.UTF_8)).toString(Charsets.UTF_8))
                assertEquals("NotFound", denied.getString("error"))
                return view.toString()
            } finally { NativeWorkspace.close(handle) }
        }
        assertEquals(snapshot(database()), snapshot(target))
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

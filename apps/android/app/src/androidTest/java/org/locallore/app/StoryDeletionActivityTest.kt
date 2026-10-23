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
import androidx.test.ext.junit.runners.AndroidJUnit4
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
import org.junit.runner.RunWith
import org.locallore.app.ui.LocalLoreScreen
import org.locallore.app.ui.StoryDeletionDialog

/** Actual Compose + JNI + SQLite, fresh private synthetic roots; no existing save is removed. */
@RunWith(AndroidJUnit4::class)
class StoryDeletionActivityTest {
    @get:Rule val compose = createAndroidComposeRule<ComponentActivity>()
    private val instrumentation get() = InstrumentationRegistry.getInstrumentation()
    private lateinit var isolated: Context
    private lateinit var root: File
    private lateinit var model: ShellViewModel
    private lateinit var owners: ViewModelStore
    private var shown by mutableStateOf<ShellViewModel?>(null)

    @Test fun nativeConsentCancelAllTimelinesRetainedStoryAndEmptyReopen(): Unit {
        assertEquals("org.locallore.app.storydelete", instrumentation.targetContext.packageName)
        root = io { File(instrumentation.targetContext.noBackupFilesDir, "story-delete-${UUID.randomUUID()}")
            .also { check(it.mkdir()) } }
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
                    onResume = current::resume, onRecover = current::recover,
                    deletionAvailable = true, onDelete = current::openDeletion) {
                    current.deletionController?.let { controller ->
                        StoryDeletionDialog(deletion, controller::dismiss, controller::cancel, controller::confirm)
                    }
                }
            }
        }
        var failure: Throwable? = null
        try {
            awaitLibrary(0)
            compose.onNodeWithTag("empty-library").performScrollTo().assertIsDisplayed()
            compose.onNodeWithTag("give-potion").performScrollTo().assertIsNotEnabled()
            compose.onNodeWithTag("reset-demo").performScrollTo().performClick()
            awaitLibrary(1)
            compose.onNodeWithTag("give-potion").performScrollTo().performClick()
            compose.waitUntil(15_000) { !model.state.value.busy && model.state.value.revision == 1L }
            val retained = model.state.value
            assertEquals(2, retained.messages.size)
            val source = io { instrumentation.context.assets.open("platform-roundtrip-v1/windows-origin.json").use { it.readBytes() } }
            io { withArchive { handle ->
                val prepared = accepted(NativeArchive.prepareImport(handle, source))
                accepted(NativeArchive.commitImport(handle, prepared.getLong("token")))
            } }
            // A new library owner sees the imported root through actual Rust resume, never UI canon.
            disposeOwner(); newOwner(); awaitLibrary(2)
            val target = model.state.value.stories.first { it.story == "platform-windows-v1" }
            compose.runOnIdle { model.resume(target) }
            compose.waitUntil(15_000) { !model.state.value.busy && model.state.value.selectedStory == target }
            val before = io { capture(target) }
            openPreview()
            val preview = requireNotNull(model.deletion.value.prepared).preview
            assertEquals(setOf("main", "child", "sibling"), preview.branchHeads.keys)
            assertEquals(4L, preview.committedTurns)
            assertEquals(9, preview.rows.size)
            assertFalse(model.archive.value.visible)
            compose.runOnIdle { model.submit(DemoAction.GIVE_POTION); assertFalse(model.state.value.busy) }
            compose.onNodeWithTag("delete-cancel").performClick()
            awaitLibrary(2)
            assertArrayEquals(before, io { capture(target) })
            compose.runOnIdle { model.resume(target) }
            compose.waitUntil(15_000) { !model.state.value.busy && model.state.value.selectedStory == target }
            openPreview()
            compose.onNodeWithTag("delete-confirm").performScrollTo().performClick()
            compose.waitUntil(15_000) { model.deletion.value.deleted != null }
            assertEquals(StoryDeleted(target.story, 3, 4), model.deletion.value.deleted)
            compose.onNodeWithTag("delete-close").performClick()
            awaitLibrary(1)
            assertEquals(retained.selectedStory, model.state.value.selectedStory)
            assertEquals(retained.messages, model.state.value.messages)
            assertEquals(retained.potionOwner, model.state.value.potionOwner)
            assertEquals(1L, model.state.value.revision)
            io { withArchive { handle ->
                val request = control(target)
                assertEquals("NotFound", JSONObject(NativeArchive.prepareDelete(handle, request).toString(Charsets.UTF_8)).getString("error"))
            } }
            openPreview()
            compose.onNodeWithTag("delete-confirm").performScrollTo().performClick()
            compose.waitUntil(15_000) { model.deletion.value.deleted != null }
            compose.onNodeWithTag("delete-close").performClick(); awaitLibrary(0)
            assertNull(model.state.value.selectedStory); assertTrue(model.state.value.messages.isEmpty())
            disposeOwner(); newOwner(); awaitLibrary(0)
            compose.onNodeWithTag("empty-library").performScrollTo().assertIsDisplayed()
            // Explicit Create is the only route out of the durable empty library.
            compose.onNodeWithTag("reset-demo").performScrollTo().performClick(); awaitLibrary(1)
            assertEquals(0L, model.state.value.revision)
            assertFalse(model.state.value.stories.any { it.story == target.story || it.story == retained.selectedStory?.story })
        } catch (thrown: Throwable) { failure = thrown; throw thrown }
        finally {
            try { disposeOwner(); ownerFence() }
            catch (cleanup: Throwable) { if (failure != null) failure.addSuppressed(cleanup) else throw cleanup }
        }
    }
    private fun newOwner() = instrumentation.runOnMainSync {
        model = ShellViewModel(DurableGateway(NativeWorkspaceTransport(isolated), autoCreateIfEmpty = false),
            deletionGateway = NativeArchiveGateway(isolated))
        owners = ViewModelStore().also { it.put("deletion", model) }; shown = model
    }
    private fun disposeOwner() {
        instrumentation.runOnMainSync { shown = null; owners.clear() }; compose.waitForIdle()
    }
    private fun awaitLibrary(count: Int) {
        compose.waitUntil(15_000) { !model.state.value.busy && !model.state.value.deletionActive &&
            !model.state.value.recoveryRequired && model.state.value.stories.size == count }
    }
    private fun openPreview() {
        compose.onNodeWithTag("delete-story").performScrollTo().performClick()
        compose.waitUntil(15_000) { model.deletion.value.prepared != null && !model.deletion.value.busy }
        compose.onNodeWithTag("delete-dialog").assertIsDisplayed()
    }
    private fun control(story: SavedStory) = JSONObject().put("story", story.story).put("branch", story.branch)
        .put("expected_revision", story.revision).toString().toByteArray(Charsets.UTF_8)
    private fun accepted(bytes: ByteArray): JSONObject = JSONObject(bytes.toString(Charsets.UTF_8)).also {
        assertEquals("ok", it.getString("status"))
    }.getJSONObject("data")
    private fun <T> withArchive(block: (Long) -> T): T {
        val staging = File(root, "test-staging").also { check(it.isDirectory || it.mkdir()) }
        val handle = NativeArchive.open(File(root, "workspace-v1/stories.sqlite3").canonicalPath, staging.canonicalPath)
        check(handle > 0)
        try { return block(handle) } finally { NativeArchive.close(handle) }
    }
    private fun capture(story: SavedStory): ByteArray = withArchive { handle ->
        val prepared = accepted(NativeArchive.prepareExport(handle, control(story)))
        NativeArchive.exportBytes(handle, prepared.getLong("token"))
    }
    private fun ownerFence() = io {
        val database = File(root, "workspace-v1/stories.sqlite3").canonicalPath
        val staging = File(root, "owner-staging").also { check(it.isDirectory || it.mkdir()) }.canonicalPath
        // Cleanup is asynchronous; observe availability without allocating extra long-lived owners.
        val end = System.nanoTime() + 10_000_000_000L
        while (true) {
            val workspaces = mutableListOf<Long>(); val archives = mutableListOf<Long>()
            try {
                repeat(4) { NativeWorkspace.open(database).takeIf { it > 0 }?.let(workspaces::add) }
                repeat(4) { NativeArchive.open(database, staging).takeIf { it > 0 }?.let(archives::add) }
                if (workspaces.size == 4 && archives.size == 4) return@io
            } finally { workspaces.forEach(NativeWorkspace::close); archives.forEach(NativeArchive::close) }
            check(System.nanoTime() < end) { "Native deletion owners did not drain" }
            Thread.sleep(20)
        }
    }
    private fun <T> io(block: suspend () -> T): T = runBlocking { withContext(Dispatchers.IO) { block() } }
}

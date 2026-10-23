/* Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0 */
package org.locallore.app

import androidx.lifecycle.ViewModelStore
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.ExperimentalCoroutinesApi
import kotlinx.coroutines.test.StandardTestDispatcher
import kotlinx.coroutines.test.advanceUntilIdle
import kotlinx.coroutines.test.resetMain
import kotlinx.coroutines.test.runTest
import kotlinx.coroutines.test.setMain
import org.junit.After
import org.junit.Assert.*
import org.junit.Before
import org.junit.Test

/** Shell/controller integration: no independent gameplay or archive validator. */
@OptIn(ExperimentalCoroutinesApi::class)
class ArchiveShellTest {
    private val dispatcher = StandardTestDispatcher()
    private val models = ViewModelStore()
    private val original = SavedStory("original", "main", "Original", 1)
    private val imported = SavedStory("imported", "main", "Imported", 1)
    @Before fun setup() { Dispatchers.setMain(dispatcher) }
    @After fun cleanup() { models.clear(); Dispatchers.resetMain() }
    private inner class StoryGateway : DemoGateway {
        override val durable = true
        var selected = original
        var importedExists = false
        var mutations = 0
        var resumes = 0
        var snapshots = 0
        override suspend fun respond(action: DemoAction, revision: Long, mode: DemoMode): DemoResult {
            mutations++; return DemoResult.Rejected("Inventory")
        }
        override suspend fun initialize() = saved()
        override suspend fun snapshot(): SavedSnapshot { snapshots++; return saved() }
        override suspend fun createSaved(): SavedSnapshot { mutations++; return saved() }
        override suspend fun resumeSaved(story: SavedStory): SavedSnapshot { resumes++; selected = story; return saved() }
        override suspend fun recoverSaved(): SavedSnapshot { mutations++; return saved() }
        private fun saved() = SavedSnapshot(selected.revision, "Not in your inventory", emptyList(),
            "/synthetic/stories.sqlite3", 1, if (importedExists) listOf(original, imported) else listOf(original),
            selected, databaseSchemaVersion = 2)
    }
    private inner class Archives(private val story: StoryGateway) : ArchiveGateway {
        private val preview = ArchivePreview(1, "imported", "Imported", "main", mapOf("main" to 1L),
            1, 100, "a".repeat(64), "Full private synthetic archive", false)
        var closes = 0
        override suspend fun prepareExport(story: SavedStory) = ArchivePrepared(1, preview.copy(storyId = story.story))
        override suspend fun prepareImport(bytes: ByteArray) = ArchivePrepared(2, preview)
        override suspend fun exportBytes(token: Long) = "synthetic".toByteArray()
        override suspend fun commitImport(token: Long): ArchiveImported {
            story.importedExists = true
            return ArchiveImported("imported", "main", 1, 1)
        }
        override fun cancel() {}
        override fun close() { closes++ }
    }
    private fun model(story: StoryGateway, archives: Archives) =
        ShellViewModel(story, archiveGateway = archives).also { models.put("archive-shell", it) }

    @Test fun archiveGuardFencesRetainedStoryCallbacksAndRestoresLibraryAfterDismissal() = runTest(dispatcher) {
        val story = StoryGateway(); val archives = Archives(story); val model = model(story, archives)
        advanceUntilIdle(); model.openArchive()
        assertTrue(model.state.value.archiveActive)
        model.submit(DemoAction.GIVE_POTION); model.reset(); model.resume(imported); model.recover(); model.setMode(DemoMode.FAILED)
        advanceUntilIdle()
        assertEquals(0, story.mutations); assertEquals(0, story.resumes)
        assertEquals(DemoMode.ACCEPTED, model.state.value.mode)
        model.archiveController!!.dismiss(); advanceUntilIdle()
        assertFalse(model.state.value.archiveActive)
        assertEquals(1, story.snapshots)
        assertEquals(original, model.state.value.selectedStory)
    }

    @Test fun cancelledOutstandingPickerKeepsGuardUntilCallbackDrainsAndCannotWrite() = runTest(dispatcher) {
        val story = StoryGateway(); val model = model(story, Archives(story))
        advanceUntilIdle(); model.openArchive(); model.archiveController!!.prepareExport(); advanceUntilIdle()
        assertTrue(model.beginArchiveExportPicker())
        model.archiveController!!.dismiss(); advanceUntilIdle()
        assertTrue(model.state.value.archiveActive)
        var writes = 0
        model.completeArchiveExport { writes++ }; advanceUntilIdle()
        assertEquals(0, writes)
        assertFalse(model.state.value.archiveActive)
        model.completeArchiveExport { writes++ }; advanceUntilIdle()
        assertEquals(0, writes)
    }

    @Test fun confirmedImportDoesNotAutoResumeAndExplicitOpenCreatesFreshSession() = runTest(dispatcher) {
        val story = StoryGateway(); val model = model(story, Archives(story))
        advanceUntilIdle(); model.openArchive()
        assertTrue(model.beginArchiveImportPicker())
        model.completeArchiveImport { byteArrayOf(1) }; advanceUntilIdle()
        assertFalse(story.importedExists)
        model.archiveController!!.confirmImport(); advanceUntilIdle()
        assertTrue(story.importedExists)
        assertEquals(0, story.resumes)
        assertEquals(original, model.state.value.selectedStory)
        model.archiveController!!.openImported(); advanceUntilIdle()
        assertEquals(1, story.resumes)
        assertEquals(imported, model.state.value.selectedStory)
        assertFalse(model.state.value.archiveActive)
        assertEquals(2, model.state.value.stories.size)
    }

    @Test fun clearedShellCannotRunRetainedPickerOrReopenArchive() = runTest(dispatcher) {
        val story = StoryGateway(); val archives = Archives(story); val model = model(story, archives)
        advanceUntilIdle(); model.openArchive()
        assertTrue(model.beginArchiveImportPicker())
        models.clear()
        var reads = 0
        model.completeArchiveImport { reads++; byteArrayOf(1) }
        model.openArchive(); advanceUntilIdle()
        assertEquals(0, reads)
        assertEquals(1, archives.closes)
        assertEquals(0, story.mutations)
    }
}

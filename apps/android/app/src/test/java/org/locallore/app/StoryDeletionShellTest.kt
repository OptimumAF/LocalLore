/* Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0 */
package org.locallore.app

import androidx.lifecycle.ViewModelStore
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.ExperimentalCoroutinesApi
import kotlinx.coroutines.test.*
import org.junit.After
import org.junit.Assert.*
import org.junit.Before
import org.junit.Test

@OptIn(ExperimentalCoroutinesApi::class)
class StoryDeletionShellTest {
    private val dispatcher = StandardTestDispatcher()
    private val owners = ViewModelStore()
    private val original = SavedStory("original", "main", "Original", 1)
    @Before fun setup() { Dispatchers.setMain(dispatcher) }
    @After fun cleanup() { owners.clear(); Dispatchers.resetMain() }
    private inner class Stories : DemoGateway {
        override val durable = true
        var mutations = 0; var reconciles = 0; var empty = false
        fun saved() = SavedSnapshot(if (empty) 0 else 1, if (empty) "" else "Not in your inventory", emptyList(),
            "/synthetic/stories.sqlite3", 1, if (empty) emptyList() else listOf(original),
            if (empty) null else original, databaseSchemaVersion = 2)
        override suspend fun initialize() = saved()
        override suspend fun reconcileSaved(): SavedSnapshot { reconciles++; return saved() }
        override suspend fun respond(action: DemoAction, revision: Long, mode: DemoMode): DemoResult {
            mutations++; return DemoResult.Rejected("Inventory")
        }
        override suspend fun createSaved(): SavedSnapshot { mutations++; return saved() }
        override suspend fun resumeSaved(story: SavedStory): SavedSnapshot { mutations++; return saved() }
        override suspend fun recoverSaved(): SavedSnapshot { mutations++; return saved() }
    }
    private inner class Deletes(val stories: Stories) : StoryDeletionGateway {
        var closes = 0
        override suspend fun prepare(story: SavedStory) = StoryDeletionPrepared(1,
            StoryDeletionPreview(1, original.story, original.title, "main", mapOf("main" to 1), 1, 0, 0, 0,
                mapOf("turns" to 1, "branches" to 1), "Synthetic logical deletion"))
        override suspend fun commit(token: Long): StoryDeleted {
            stories.empty = true
            // A lost acknowledgement after the actual commit must still publish an empty library.
            throw StoryDeletionFailure("Cancelled")
        }
        override fun cancel() {}
        override fun close() { closes++ }
    }
    @Test fun guardFencesGameplayAndUncertainCommitReconcilesEmptyWithoutCreating() = runTest(dispatcher) {
        val stories = Stories(); val deletes = Deletes(stories)
        val model = ShellViewModel(stories, deletionGateway = deletes).also { owners.put("delete", it) }
        advanceUntilIdle(); model.openDeletion(); advanceUntilIdle()
        assertTrue(model.state.value.deletionActive)
        model.reset(); model.submit(DemoAction.GIVE_POTION); model.resume(original); model.recover(); model.openArchive()
        model.openDiagnostics(); model.setMode(DemoMode.FAILED); advanceUntilIdle()
        assertEquals(0, stories.mutations); assertFalse(model.diagnostics.value.visible)
        val controller = checkNotNull(model.deletionController)
        controller.confirm(checkNotNull(controller.state.value.prepared)); advanceUntilIdle()
        assertTrue(model.state.value.deletionActive); assertEquals(0, stories.reconciles)
        controller.dismiss(); advanceUntilIdle()
        assertFalse(model.state.value.deletionActive); assertEquals(1, stories.reconciles)
        assertNull(model.state.value.selectedStory); assertTrue(model.state.value.stories.isEmpty())
        assertEquals(0L, model.state.value.revision); assertTrue(model.state.value.messages.isEmpty())
        model.submit(DemoAction.GIVE_POTION); advanceUntilIdle(); assertEquals(0, stories.mutations)
        model.reset(); advanceUntilIdle(); assertEquals(1, stories.mutations)
    }
    @Test fun disposedOwnerClosesGatewayAndRetainedCallbacksCannotReopen() = runTest(dispatcher) {
        val stories = Stories(); val deletes = Deletes(stories)
        val model = ShellViewModel(stories, deletionGateway = deletes).also { owners.put("delete", it) }
        advanceUntilIdle(); model.openDeletion(); advanceUntilIdle(); owners.clear()
        model.openDeletion(); model.reset(); advanceUntilIdle()
        assertEquals(1, deletes.closes); assertEquals(0, stories.mutations); assertEquals(0, stories.reconciles)
    }
}

/* Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0 */
package org.locallore.app

import androidx.lifecycle.ViewModelStore
import kotlinx.coroutines.CompletableDeferred
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.ExperimentalCoroutinesApi
import kotlinx.coroutines.NonCancellable
import kotlinx.coroutines.test.StandardTestDispatcher
import kotlinx.coroutines.test.advanceUntilIdle
import kotlinx.coroutines.test.runCurrent
import kotlinx.coroutines.test.resetMain
import kotlinx.coroutines.test.runTest
import kotlinx.coroutines.test.setMain
import kotlinx.coroutines.withContext
import org.junit.After
import org.junit.Assert.*
import org.junit.Before
import org.junit.Test

/** Integration of presentation fences and snapshot publication, using explicit fake ports. */
@OptIn(ExperimentalCoroutinesApi::class)
class StoryCreationShellTest {
    private val dispatcher = StandardTestDispatcher()
    private val models = ViewModelStore()
    private val original = SavedStory("original", "main", "Original", 3)
    @Before fun before() { Dispatchers.setMain(dispatcher) }
    @After fun after() { models.clear(); Dispatchers.resetMain() }

    private inner class Gateway(empty: Boolean = false) : DemoGateway, StoryCreationGateway {
        override val durable = true
        override val storyRecords = true
        val stories = mutableListOf<SavedStory>().also { if (!empty) it += original }
        var selected: SavedStory? = stories.firstOrNull()
        var previews = 0
        var creates = 0
        var legacyCreates = 0
        var otherWrites = 0
        var resumes = 0
        var refreshes = 0
        var closes = 0
        var cancels = 0
        var failAfterCreate = false
        var release: CompletableDeferred<Unit>? = null
        override suspend fun preview(): StoryCreationPreview {
            previews++
            return StoryCreationPreview("lantern-quay-v1", "a".repeat(64), "Lantern Quay", "Original starter", "fantasy_v1", listOf("Player: Rowan"))
        }
        override suspend fun create(request: StoryCreationRequest): SavedSnapshot {
            creates++
            val created = SavedStory("quay-${request.creationId}", "main", request.title, 0)
            stories += created
            selected = created
            release?.let { withContext(NonCancellable) { it.await() } }
            if (failAfterCreate) throw WorkspaceFailure("Full")
            return saved()
        }
        fun saved() = SavedSnapshot(selected?.revision ?: 0, "You", emptyList(), "/synthetic/stories.sqlite3", 1,
            stories.toList(), selected, databaseSchemaVersion = 5,
            textProvider = if (selected == null) TextProvider.UNAVAILABLE else TextProvider.SCRIPTED)
        override suspend fun initialize() = saved()
        override suspend fun snapshot() = saved()
        override suspend fun reconcileSaved(): SavedSnapshot { refreshes++; return saved() }
        override suspend fun createSaved(): SavedSnapshot { legacyCreates++; return saved() }
        override suspend fun resumeSaved(story: SavedStory): SavedSnapshot { resumes++; selected = story; return saved() }
        override suspend fun recoverSaved(): SavedSnapshot { otherWrites++; return saved() }
        override suspend fun respond(action: DemoAction, revision: Long, mode: DemoMode): DemoResult {
            otherWrites++; return DemoResult.Rejected("Inventory")
        }
        override suspend fun respondText(input: PlayInput, revision: Long): DemoResult {
            otherWrites++; return DemoResult.Rejected("Inventory")
        }
        override fun cancel() { cancels++ }
        override fun close() { closes++ }
    }
    private fun model(gateway: Gateway) = ShellViewModel(gateway).also { models.put("creation", it) }

    @Test fun emptyPersistentLibraryReviewsBeforeCreatingAndPublishesOnlyTheReturnedSnapshot() = runTest(dispatcher) {
        val gateway = Gateway(empty = true); val model = model(gateway); advanceUntilIdle()
        assertNull(model.state.value.selectedStory)
        assertEquals(TextProvider.UNAVAILABLE, model.state.value.textProvider)
        model.startNewStory(); advanceUntilIdle()
        assertTrue(model.state.value.creationActive)
        assertEquals(1, gateway.previews); assertEquals(0, gateway.creates); assertTrue(gateway.stories.isEmpty())
        val controller = model.creationController!!
        val old = controller.state.value.review!!
        controller.editTitle(old, "Original named story")
        controller.confirm(old); advanceUntilIdle()
        assertEquals(0, gateway.creates)
        val current = controller.state.value.review!!
        controller.confirm(current); controller.confirm(current); advanceUntilIdle()
        assertEquals(1, gateway.creates); assertEquals(0, gateway.legacyCreates)
        assertFalse(model.state.value.creationActive); assertFalse(model.creation.value.visible)
        assertEquals(gateway.saved().selected, model.state.value.selectedStory)
        assertEquals("Original named story", model.state.value.selectedStory?.title)
        assertEquals(gateway.stories, model.state.value.stories)
    }

    @Test fun reviewFencesRetainedGameplaySelectionResetAndInspectionCallbacksAndCancelPreservesSelection() = runTest(dispatcher) {
        val gateway = Gateway(); val model = model(gateway); advanceUntilIdle()
        val selected = model.state.value.selectedStory
        model.startNewStory(); advanceUntilIdle()
        model.submit(DemoAction.GIVE_POTION)
        model.submitText(PlayInput(PlayInputKind.ACTION, "I give my potion to Mira."), original)
        model.resume(original); model.recover(); model.reset(); model.startNewStory()
        model.setMode(DemoMode.REJECTED); model.openDiagnostics(); model.openStoryRecord(); model.cancel()
        advanceUntilIdle()
        assertEquals(1, gateway.previews); assertEquals(0, gateway.otherWrites)
        assertEquals(0, gateway.legacyCreates); assertEquals(0, gateway.resumes); assertEquals(0, gateway.cancels)
        assertFalse(model.diagnostics.value.visible); assertFalse(model.storyRecord.value.visible)
        assertEquals(DemoMode.ACCEPTED, model.state.value.mode)
        model.creationController!!.dismiss(); advanceUntilIdle()
        assertEquals(selected, model.state.value.selectedStory)
        assertFalse(model.state.value.creationActive); assertEquals(0, gateway.refreshes)
        assertEquals(listOf(original), gateway.stories)
    }

    @Test fun uncertainCreationConsumesConsentAndRefreshesOnceWithoutAnotherCreate() = runTest(dispatcher) {
        val gateway = Gateway().also { it.failAfterCreate = true }; val model = model(gateway); advanceUntilIdle()
        model.startNewStory(); advanceUntilIdle()
        val controller = model.creationController!!; val review = controller.state.value.review!!
        controller.confirm(review); advanceUntilIdle()
        assertEquals(1, gateway.creates); assertTrue(model.state.value.creationActive)
        assertNull(model.creation.value.review); assertTrue(model.creation.value.notice!!.contains("may already exist"))
        controller.confirm(review); advanceUntilIdle(); assertEquals(1, gateway.creates)
        controller.dismiss(); controller.dismiss(); advanceUntilIdle()
        assertEquals(1, gateway.refreshes); assertEquals(1, gateway.creates)
        assertFalse(model.state.value.creationActive)
        assertEquals(2, model.state.value.stories.size)
        assertTrue(model.state.value.stories.contains(original))
    }

    @Test fun disposingDuringNoncooperativeCreationClosesPortAndCannotPublishItsLateSnapshot() = runTest(dispatcher) {
        val gate = CompletableDeferred<Unit>()
        val gateway = Gateway().also { it.release = gate }; val model = model(gateway); advanceUntilIdle()
        model.startNewStory(); advanceUntilIdle()
        val controller = model.creationController!!; val review = controller.state.value.review!!
        controller.confirm(review); runCurrent(); assertEquals(1, gateway.creates)
        models.clear(); val afterClear = model.state.value
        assertEquals(1, gateway.closes); assertFalse(afterClear.creationActive)
        gate.complete(Unit); advanceUntilIdle()
        assertEquals(afterClear, model.state.value); assertEquals(original, model.state.value.selectedStory)
        controller.confirm(review); model.startNewStory(); advanceUntilIdle()
        assertEquals(1, gateway.creates); assertEquals(0, gateway.refreshes)
    }
}

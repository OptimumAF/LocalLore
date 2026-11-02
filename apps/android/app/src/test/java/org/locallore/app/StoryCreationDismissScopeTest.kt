/* Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0 */
package org.locallore.app

import androidx.lifecycle.ViewModelStore
import kotlinx.coroutines.CompletableDeferred
import kotlinx.coroutines.CoroutineScope
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.ExperimentalCoroutinesApi
import kotlinx.coroutines.NonCancellable
import kotlinx.coroutines.flow.Flow
import kotlinx.coroutines.flow.collect
import kotlinx.coroutines.launch
import kotlinx.coroutines.test.StandardTestDispatcher
import kotlinx.coroutines.test.UnconfinedTestDispatcher
import kotlinx.coroutines.test.advanceUntilIdle
import kotlinx.coroutines.test.resetMain
import kotlinx.coroutines.test.runCurrent
import kotlinx.coroutines.test.runTest
import kotlinx.coroutines.test.setMain
import kotlinx.coroutines.withContext
import org.junit.Assert.*
import org.junit.Test

/** Synthetic ports exercise real owner scheduling; no native creation or inference qualification. */
@OptIn(ExperimentalCoroutinesApi::class)
class StoryCreationDismissScopeTest {
    /** Baseline executable behavior; a production overload takes precedence when implemented. */
    @Suppress("UNUSED_PARAMETER", "EXTENSION_SHADOWED_BY_MEMBER")
    private fun StoryCreationController.dismiss(rendered: StoryCreationUiState) = dismiss()

    @Suppress("UNCHECKED_CAST")
    private fun productionFlow(owner: Any, getter: String, baseline: Flow<*>): Flow<Any> {
        val method = owner.javaClass.methods.singleOrNull {
            it.name.substringBefore('$') == getter && it.parameterCount == 0
        }
        return (method?.invoke(owner) ?: baseline) as Flow<Any>
    }
    private fun displayed(frame: Any): StoryCreationUiState = if (frame is StoryCreationUiState) frame
        else frame.javaClass.getMethod("getState").invoke(frame) as StoryCreationUiState

    private class Port : StoryCreationGateway, DemoGateway {
        override val durable = true
        var previews = 0
        var reconciles = 0
        var gameplay = 0
        var closes = 0
        val requests = mutableListOf<StoryCreationRequest>()
        var read: suspend () -> StoryCreationPreview = { Preview }
        var write: suspend (StoryCreationRequest) -> SavedSnapshot = { CreatedSnapshot }
        var originals: OriginalStoryGateway? = null
        override fun originalStories() = originals
        override suspend fun preview(): StoryCreationPreview { previews++; return read() }
        override suspend fun create(request: StoryCreationRequest): SavedSnapshot { requests += request; return write(request) }
        override suspend fun initialize() = InitialSnapshot
        override suspend fun snapshot() = InitialSnapshot
        override suspend fun reconcileSaved(): SavedSnapshot { reconciles++; return CreatedSnapshot }
        override suspend fun respond(action: DemoAction, revision: Long, mode: DemoMode): DemoResult {
            gameplay++; error("Creation dismissal cannot dispatch gameplay")
        }
        override fun close() { closes++ }
    }

    @Test fun equalCopiesForeignControllersAndPreviouslyHiddenViewsCannotCloseCurrentReview() = runTest {
        val violations = mutableListOf<String>()
        for (kind in listOf("copy", "foreign", "hidden")) {
            val port = Port(); val closed = mutableListOf<StoryCreationClose>()
            val controller = StoryCreationController(port, this, closed::add)
            val other = StoryCreationController(Port(), this) {}
            try {
                val hidden = controller.state.value
                controller.open(); other.open(); advanceUntilIdle()
                val current = controller.state.value
                val retained = when (kind) {
                    "copy" -> current.copy()
                    "foreign" -> other.state.value
                    else -> hidden
                }
                assertNotSame(current, retained)
                if (kind == "copy") assertEquals(current, retained)
                controller.dismiss(retained); advanceUntilIdle()
                if (controller.state.value !== current || closed.isNotEmpty()) violations += kind
                assertEquals(1, port.previews); assertTrue(port.requests.isEmpty())
            } finally { controller.dispose(); other.dispose(); advanceUntilIdle() }
        }
        assertEquals("A retained view acquired the current creation's Close authority", emptyList<String>(), violations)
    }

    @Test fun sameFrameTitleIntentsStayLiveButTheirEarlierOuterCloseCannotRetireTheEditedReview() = runTest {
        val port = Port(); val closed = mutableListOf<StoryCreationClose>()
        val controller = StoryCreationController(port, this, closed::add)
        try {
            controller.open(); advanceUntilIdle()
            val rendered = controller.state.value; val editor = checkNotNull(rendered.review)
            controller.editTitle(editor, "First title")
            controller.editTitle(editor, "Latest title before a frame")
            val edited = controller.state.value
            assertEquals("Latest title before a frame", edited.review?.title)
            assertSame(editor.preview, edited.review?.preview)
            controller.dismiss(rendered); advanceUntilIdle()
            assertSame(edited, controller.state.value); assertTrue(closed.isEmpty())
            controller.dismiss(edited); advanceUntilIdle()
            assertEquals(listOf(StoryCreationClose()), closed)
            assertTrue(port.requests.isEmpty())
        } finally { controller.dispose(); advanceUntilIdle() }
    }

    @Test fun oldReviewCloseCannotCancelANewerNoncooperativeCreateOrForceAnUncertainRefresh() = runTest {
        val release = CompletableDeferred<Unit>(); val port = Port()
        port.write = { withContext(NonCancellable) { release.await() }; CreatedSnapshot }
        val closed = mutableListOf<StoryCreationClose>()
        val controller = StoryCreationController(port, this, closed::add)
        try {
            controller.open(); advanceUntilIdle(); val old = controller.state.value
            controller.dismiss(old); advanceUntilIdle()
            controller.open(); advanceUntilIdle()
            val review = checkNotNull(controller.state.value.review)
            assertNotEquals(old.review?.creationId, review.creationId)
            controller.confirm(review); runCurrent()
            val creating = controller.state.value
            assertTrue(creating.creating); assertEquals(listOf(review), port.requests)
            controller.dismiss(old); runCurrent()
            assertSame(creating, controller.state.value); assertFalse(controller.state.value.closing)
            assertEquals(listOf(StoryCreationClose()), closed)
            release.complete(Unit); advanceUntilIdle()
            assertEquals(listOf(StoryCreationClose(), StoryCreationClose(saved = CreatedSnapshot)), closed)
            assertEquals(1, port.requests.size); assertFalse(controller.state.value.visible)
        } finally { release.complete(Unit); controller.dispose(); advanceUntilIdle() }
    }

    @Test fun currentPendingPreviewCloseJoinsOnceAndCannotReopenBeforeDrainOrInventRefresh() = runTest {
        val release = CompletableDeferred<Unit>(); val port = Port()
        port.read = { withContext(NonCancellable) { release.await() }; Preview }
        val closed = mutableListOf<StoryCreationClose>()
        val controller = StoryCreationController(port, this, closed::add)
        try {
            controller.open(); runCurrent(); val pending = controller.state.value
            controller.dismiss(pending); controller.dismiss(pending); runCurrent()
            assertTrue(controller.state.value.closing); assertTrue(closed.isEmpty())
            controller.open(); runCurrent(); assertEquals(1, port.previews)
            release.complete(Unit); advanceUntilIdle()
            assertEquals(listOf(StoryCreationClose()), closed)
            assertFalse(controller.state.value.visible); assertNull(controller.state.value.review)
            assertTrue(port.requests.isEmpty())
            controller.dismiss(pending); advanceUntilIdle(); assertEquals(1, closed.size)
        } finally { release.complete(Unit); controller.dispose(); advanceUntilIdle() }
    }

    @Test fun currentCreateCloseWaitsForPhysicalEffectAndPreservesOneUncertainOutcome() = runTest {
        val release = CompletableDeferred<Unit>(); val port = Port(); var effect = false
        port.write = { withContext(NonCancellable) { release.await(); effect = true }; CreatedSnapshot }
        val closed = mutableListOf<StoryCreationClose>()
        val controller = StoryCreationController(port, this, closed::add)
        try {
            controller.open(); advanceUntilIdle(); val request = checkNotNull(controller.state.value.review)
            controller.confirm(request); runCurrent(); val current = controller.state.value
            controller.dismiss(current); controller.dismiss(current); runCurrent()
            assertTrue(controller.state.value.closing); assertTrue(closed.isEmpty()); assertFalse(effect)
            controller.confirm(request); controller.open(); runCurrent(); assertEquals(1, port.requests.size)
            release.complete(Unit); advanceUntilIdle()
            assertTrue(effect); assertEquals(listOf(StoryCreationClose(refreshRequired = true)), closed)
            assertFalse(controller.state.value.visible); assertEquals(1, port.requests.size)
        } finally { release.complete(Unit); controller.dispose(); advanceUntilIdle() }
    }

    @Test fun slowActualControllerCollectorReceivesEqualBusyReplacementBeforeFreshClose() = runTest {
        val gates = listOf(CompletableDeferred<Unit>(), CompletableDeferred<Unit>())
        val releaseCollector = CompletableDeferred<Unit>(); val port = Port()
        port.read = { val index = port.previews - 1; withContext(NonCancellable) { gates[index].await() }; Preview }
        val producer = CoroutineScope(backgroundScope.coroutineContext + UnconfinedTestDispatcher(testScheduler))
        val closed = mutableListOf<StoryCreationClose>()
        val controller = StoryCreationController(port, producer, closed::add)
        val observed = mutableListOf<Any>(); var parked = false
        val collector = launch(StandardTestDispatcher(testScheduler)) {
            productionFlow(controller, "getFrames", controller.state).collect { frame ->
                observed += frame
                if (!parked && displayed(frame).visible && displayed(frame).busy) {
                    parked = true; releaseCollector.await()
                }
            }
        }
        try {
            runCurrent(); controller.open(); runCurrent(); val old = controller.state.value
            assertTrue(parked); assertSame(old, displayed(observed.last()))
            controller.dismiss(old); gates[0].complete(Unit); advanceUntilIdle()
            assertEquals(listOf(StoryCreationClose()), closed); assertFalse(controller.state.value.visible)
            controller.open(); runCurrent(); val reopened = controller.state.value
            assertEquals(old, reopened); assertNotSame(old, reopened); assertEquals(2, port.previews)
            releaseCollector.complete(Unit); runCurrent()
            assertSame("Slow production collection retained the first busy Close callback", reopened, displayed(observed.last()))
            controller.dismiss(displayed(observed.last())); runCurrent()
            assertTrue(controller.state.value.closing); assertEquals(1, closed.size)
            gates[1].complete(Unit); advanceUntilIdle()
            assertEquals(listOf(StoryCreationClose(), StoryCreationClose()), closed)
            assertTrue(port.requests.isEmpty())
        } finally {
            releaseCollector.complete(Unit); gates.forEach { it.complete(Unit) }
            collector.cancel(); controller.dispose(); advanceUntilIdle()
        }
    }

    @Test fun shellForwardsEqualBusyReopenAndOnlyCurrentCloseReleasesGameplayAfterPreviewDrain() = runTest {
        Dispatchers.setMain(UnconfinedTestDispatcher(testScheduler))
        val owners = ViewModelStore(); val port = Port()
        val gates = listOf(CompletableDeferred<Unit>(), CompletableDeferred<Unit>())
        port.read = { val index = port.previews - 1; withContext(NonCancellable) { gates[index].await() }; Preview }
        val model = ShellViewModel(port); owners.put("creation-dismiss-scope", model)
        val controller = checkNotNull(model.creationController)
        val releaseCollector = CompletableDeferred<Unit>(); val observed = mutableListOf<Any>(); var parked = false
        val collector = launch(StandardTestDispatcher(testScheduler)) {
            productionFlow(model, "getCreationFrames", model.creation).collect { frame ->
                observed += frame
                if (!parked && displayed(frame).visible && displayed(frame).busy) {
                    parked = true; releaseCollector.await()
                }
            }
        }
        try {
            runCurrent(); model.startNewStory(); runCurrent(); val old = model.creation.value
            assertTrue(parked); assertTrue(model.state.value.creationActive)
            controller.dismiss(old); gates[0].complete(Unit); advanceUntilIdle()
            assertFalse(model.state.value.creationActive); assertEquals(0, port.reconciles)
            model.startNewStory(); runCurrent(); val reopened = model.creation.value
            assertEquals(old, reopened); assertNotSame(old, reopened)
            releaseCollector.complete(Unit); runCurrent()
            assertSame("The VM must forward the live creation frame after equal busy reopen", reopened, displayed(observed.last()))
            controller.dismiss(old); runCurrent()
            assertSame(reopened, model.creation.value); assertTrue(model.state.value.creationActive)
            controller.dismiss(displayed(observed.last())); runCurrent()
            assertTrue(model.creation.value.closing); assertTrue(model.state.value.creationActive)
            assertEquals(0, port.reconciles)
            gates[1].complete(Unit); advanceUntilIdle()
            assertFalse(model.state.value.creationActive); assertEquals(Original, model.state.value.selectedStory)
            assertEquals(0, port.gameplay); assertEquals(0, port.reconciles); assertTrue(port.requests.isEmpty())
        } finally {
            releaseCollector.complete(Unit); gates.forEach { it.complete(Unit) }
            collector.cancel(); owners.clear(); advanceUntilIdle(); Dispatchers.resetMain()
        }
    }

    private class Originals : OriginalStoryGateway {
        var generationCalls = 0
        var cancellationCalls = 0
        override suspend fun originalCapabilities() = OriginalCapabilities(true, "scripted")
        override suspend fun beginOriginal(input: OriginalInput): OriginalJob { generationCalls++; error("No generate intent") }
        override suspend fun generateOriginal(job: String): OriginalGenerated = error("No generate intent")
        override suspend fun reviewOriginal(job: String, input: OriginalInput, proposal: OriginalProposal, title: String): OriginalReview = error("No review intent")
        override suspend fun createOriginal(review: OriginalReview, creationId: String): SavedSnapshot = error("No create intent")
        override suspend fun cancelOriginal(job: String): Boolean { cancellationCalls++; return true }
    }

    @Test fun starterOuterCloseCannotBorrowAuthorityAfterRoutingToAnOriginalDraft() = runTest {
        val originals = Originals(); val port = Port().also { it.originals = originals }
        val closed = mutableListOf<StoryCreationClose>()
        val controller = StoryCreationController(port, this, closed::add)
        try {
            controller.open(); advanceUntilIdle(); val starter = controller.state.value
            controller.chooseOriginal(checkNotNull(starter.review)); runCurrent()
            val draft = controller.state.value
            assertNotNull(draft.original); assertNull(draft.review)
            controller.editOriginal(checkNotNull(draft.original), OriginalStoryEdit.Text(OriginalTextField.TITLE, "An inert original draft"))
            val edited = controller.state.value
            controller.dismiss(starter); controller.dismiss(draft); runCurrent()
            assertSame(edited, controller.state.value); assertFalse(checkNotNull(edited.original).closing)
            assertTrue(closed.isEmpty()); assertEquals(0, originals.cancellationCalls)
            controller.dismiss(edited); advanceUntilIdle()
            assertEquals(listOf(StoryCreationClose()), closed)
            assertEquals(0, originals.generationCalls); assertEquals(0, originals.cancellationCalls)
            assertTrue(port.requests.isEmpty())
        } finally { controller.dispose(); advanceUntilIdle() }
    }

    @Test fun disposedVisibleAndHiddenCallbacksCannotFinishOrReopenALateCreate() = runTest {
        val release = CompletableDeferred<Unit>(); val port = Port()
        port.write = { withContext(NonCancellable) { release.await() }; CreatedSnapshot }
        val closed = mutableListOf<StoryCreationClose>()
        val controller = StoryCreationController(port, this, closed::add)
        try {
            val hidden = controller.state.value
            controller.open(); advanceUntilIdle(); val review = checkNotNull(controller.state.value.review)
            controller.confirm(review); runCurrent(); val creating = controller.state.value
            controller.dispose(); val disposed = controller.state.value
            controller.dismiss(creating); controller.dismiss(hidden); controller.dismiss(disposed)
            controller.open(); controller.confirm(review); runCurrent()
            release.complete(Unit); advanceUntilIdle()
            assertSame(disposed, controller.state.value); assertFalse(disposed.visible)
            assertTrue(closed.isEmpty()); assertEquals(listOf(review), port.requests); assertEquals(1, port.previews)
        } finally { release.complete(Unit); controller.dispose(); advanceUntilIdle() }
    }

    private companion object {
        val Original = SavedStory("dismiss-original", "main", "Existing synthetic story", 4)
        val Created = SavedStory("dismiss-created", "main", "Created synthetic story", 0)
        val InitialSnapshot = SavedSnapshot(4, "You", emptyList(), "D:/synthetic/dismiss.sqlite3", 1,
            listOf(Original), Original, databaseSchemaVersion = 5, textProvider = TextProvider.SCRIPTED)
        val CreatedSnapshot = SavedSnapshot(0, "You", emptyList(), "D:/synthetic/dismiss.sqlite3", 1,
            listOf(Original, Created), Created, databaseSchemaVersion = 5, textProvider = TextProvider.SCRIPTED)
        val Preview = StoryCreationPreview("lantern-quay-v1", "a".repeat(64), "A synthetic starter",
            "A read-only fake preview", "fantasy_v1", listOf("Player Rowan has one potion."))
    }
}

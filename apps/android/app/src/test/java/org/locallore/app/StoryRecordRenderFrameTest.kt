/* Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0 */
package org.locallore.app

import kotlinx.coroutines.CancellationException
import kotlinx.coroutines.CompletableDeferred
import kotlinx.coroutines.CoroutineScope
import kotlinx.coroutines.ExperimentalCoroutinesApi
import kotlinx.coroutines.flow.collect
import kotlinx.coroutines.launch
import kotlinx.coroutines.test.StandardTestDispatcher
import kotlinx.coroutines.test.UnconfinedTestDispatcher
import kotlinx.coroutines.test.advanceUntilIdle
import kotlinx.coroutines.test.runCurrent
import kotlinx.coroutines.test.runTest
import org.junit.Assert.*
import org.junit.Test

/** Exercises production frame delivery with an immediate producer and a separately scheduled UI collector. */
@OptIn(ExperimentalCoroutinesApi::class)
class StoryRecordRenderFrameTest {
    private val context = StoryRecordContext(SavedStory("frame-story", "main", "Frame story", 4), 4)
    private val source = StoryRecordScopedEvent(StoryRecordScope("frame-story", "main"), 2)

    private fun page(query: StoryRecordQuery) = StoryRecordPage(query, 11, 1,
        listOf(StoryRecordEntry("visible-row", "Observed record", "Player-visible record",
            StoryRecordOrigin.CANONICAL_FIELD, sources = listOf("Observed event #2"),
            scopedEventSources = listOf(source))), null)

    @Test fun equalValuedReopenDeliversTheNewExactStateToASlowRenderCollector() = runTest {
        var reads = 0
        val producer = CoroutineScope(backgroundScope.coroutineContext + UnconfinedTestDispatcher(testScheduler))
        val controller = StoryRecordController({ query -> reads++; page(query) }, producer)
        val observed = mutableListOf<StoryRecordFrame>()
        val collector = launch(StandardTestDispatcher(testScheduler)) { controller.frames.collect { observed += it } }
        try {
            runCurrent()
            controller.open(context)
            runCurrent()
            val first = controller.state.value
            assertFalse(first.loading)
            assertSame(first, observed.last().state)
            val delivered = observed.size

            // Both transitions finish before the independent collector can run.
            controller.dismiss()
            controller.open(context)
            val reopened = controller.state.value
            assertEquals(2, reads)
            assertEquals(first, reopened)
            assertNotSame(first, reopened)
            assertEquals(delivered, observed.size)
            advanceUntilIdle()

            assertSame("The UI must receive the object accepted by rendered-state callbacks",
                reopened, observed.last().state)
            assertNotSame("Equal display values must not revive the previous frame", first, observed.last().state)
        } finally {
            collector.cancel()
            controller.dispose()
        }
    }

    @Test fun eventDetailAndBackBetweenCollectorTurnsDeliverTheNewEqualBaseFrame() = runTest {
        var reads = 0
        val producer = CoroutineScope(backgroundScope.coroutineContext + UnconfinedTestDispatcher(testScheduler))
        val controller = StoryRecordController({ query ->
            reads++
            if (query.section == StoryRecordSection.HISTORY) StoryRecordPage(query, 11, 1,
                listOf(StoryRecordEntry("event-two", "Event #2", "Recorded player observation",
                    StoryRecordOrigin.RECORDED_OBSERVATION,
                    sources = listOf("Observed event #2"),
                    event = StoryRecordEvent(2, "frame-event-turn", 10, source.originalScope),
                    scopedEventSources = listOf(source))), null)
            else page(query)
        }, producer)
        val observed = mutableListOf<StoryRecordFrame>()
        val collector = launch(StandardTestDispatcher(testScheduler)) { controller.frames.collect { observed += it } }
        try {
            runCurrent()
            controller.open(context)
            runCurrent()
            val base = controller.state.value
            assertSame(base, observed.last().state)
            val delivered = observed.size

            controller.openScopedEvent(source)
            val detail = checkNotNull(controller.state.value.eventDetail)
            assertFalse(detail.loading)
            assertEquals(source, detail.scopedReference)
            assertEquals("Recorded player observation", detail.entry!!.text)
            controller.back()
            val returned = controller.state.value
            assertEquals(2, reads)
            assertEquals(base, returned)
            assertNotSame(base, returned)
            assertEquals(delivered, observed.size)
            advanceUntilIdle()

            assertSame("Returning to equal rows must refresh the exact callback frame",
                returned, observed.last().state)
        } finally {
            collector.cancel()
            controller.dispose()
        }
    }

    @Test fun initialLoadingAndCompletedFramesKeepTheirExactProductionStates() = runTest {
        val release = CompletableDeferred<Unit>()
        val producer = CoroutineScope(backgroundScope.coroutineContext + UnconfinedTestDispatcher(testScheduler))
        val controller = StoryRecordController({ query -> release.await(); page(query) }, producer)
        val observed = mutableListOf<StoryRecordFrame>()
        val collector = launch(StandardTestDispatcher(testScheduler)) { controller.frames.collect { observed += it } }
        try {
            val initial = controller.state.value
            runCurrent()
            assertSame(initial, observed.single().state)
            assertFalse(initial.visible)

            controller.open(context)
            val loading = controller.state.value
            assertTrue(loading.visible)
            assertTrue(loading.loading)
            runCurrent()
            assertSame(loading, observed.last().state)

            release.complete(Unit)
            advanceUntilIdle()
            val ready = controller.state.value
            assertFalse(ready.loading)
            assertEquals("Player-visible record", ready.entries.single().text)
            assertSame(ready, observed.last().state)
        } finally {
            release.complete(Unit)
            collector.cancel()
            controller.dispose()
        }
    }

    @Test fun currentPageAndEventCancellationPublishTheirSettledFrames() = runTest {
        val pageRelease = CompletableDeferred<Unit>()
        val eventRelease = CompletableDeferred<Unit>()
        val search = "cancelled page search"
        val reads = mutableListOf<StoryRecordQuery>()
        val producer = CoroutineScope(backgroundScope.coroutineContext + UnconfinedTestDispatcher(testScheduler))
        val controller = StoryRecordController({ query ->
            reads += query
            when {
                query.search == search -> {
                    pageRelease.await()
                    throw CancellationException("private fixture page cancellation")
                }
                query.section == StoryRecordSection.HISTORY -> {
                    eventRelease.await()
                    throw CancellationException("private fixture event cancellation")
                }
                else -> page(query)
            }
        }, producer)
        val observed = mutableListOf<StoryRecordFrame>()
        val collector = launch(StandardTestDispatcher(testScheduler)) { controller.frames.collect { observed += it } }
        try {
            controller.open(context)
            runCurrent()

            controller.search(search)
            runCurrent()
            assertTrue(controller.state.value.loading)
            pageRelease.complete(Unit)
            runCurrent()

            val cancelledPage = controller.state.value
            assertFalse(cancelledPage.loading)
            assertEquals(StoryRecordProblem.UNAVAILABLE, cancelledPage.problem)
            assertEquals(context, cancelledPage.context)
            assertEquals(search, cancelledPage.search)
            assertTrue(cancelledPage.entries.isEmpty())
            assertSame(cancelledPage, controller.frames.value.state)
            assertSame(cancelledPage, observed.last().state)
            assertEquals(2, reads.size)

            controller.search("")
            runCurrent()
            val sourcePage = controller.state.value
            controller.openScopedEvent(source)
            runCurrent()
            val loadingDetail = checkNotNull(controller.state.value.eventDetail)
            assertTrue(loadingDetail.loading)
            eventRelease.complete(Unit)
            runCurrent()

            val cancelledEvent = controller.state.value
            val detail = checkNotNull(cancelledEvent.eventDetail)
            assertFalse(detail.loading)
            assertEquals(StoryRecordProblem.UNAVAILABLE, detail.problem)
            assertNull(detail.entry)
            assertEquals(source, detail.scopedReference)
            assertSame(loadingDetail.viewToken, detail.viewToken)
            assertEquals(loadingDetail.readId, detail.readId)
            assertEquals(sourcePage, cancelledEvent.copy(eventDetail = null))
            assertSame(cancelledEvent, controller.frames.value.state)
            assertSame(cancelledEvent, observed.last().state)
            assertEquals(4, reads.size)
        } finally {
            pageRelease.complete(Unit)
            eventRelease.complete(Unit)
            collector.cancel()
            controller.dispose()
        }
    }
}

/* Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0 */
package org.locallore.app

import kotlinx.coroutines.CancellationException
import kotlinx.coroutines.CompletableDeferred
import kotlinx.coroutines.CoroutineScope
import kotlinx.coroutines.ExperimentalCoroutinesApi
import kotlinx.coroutines.Job
import kotlinx.coroutines.NonCancellable
import kotlinx.coroutines.SupervisorJob
import kotlinx.coroutines.cancelChildren
import kotlinx.coroutines.currentCoroutineContext
import kotlinx.coroutines.isActive
import kotlinx.coroutines.launch
import kotlinx.coroutines.test.advanceUntilIdle
import kotlinx.coroutines.test.runCurrent
import kotlinx.coroutines.test.runTest
import kotlinx.coroutines.withContext
import org.junit.Assert.*
import org.junit.Test

/** Reader-boundary cancellation oracles, not native/SDK cancellation evidence. */
@OptIn(ExperimentalCoroutinesApi::class)
class StoryRecordCancellationTest {
    private val context = StoryRecordContext(SavedStory("record-cancel-story", "root", "Synthetic", 2), 2)
    private val reference = StoryRecordScopedEvent(StoryRecordScope(context.story.story, "ancestor"), 1)
    private val privateFailure = "PRIVATE-READER-CANCEL /unpublished/story/path"

    private fun page(query: StoryRecordQuery, next: String? = null): StoryRecordPage = StoryRecordPage(
        query, 3, if (next != null || query.cursor != null) 2 else 1, listOf(StoryRecordEntry("field", "Visible field", "Player",
            StoryRecordOrigin.CANONICAL_FIELD, sources = listOf("Synthetic seed"),
            scopedEventSources = listOf(reference.copy(originalScope = reference.originalScope.copy(
                story = query.context.story.story))))), next,
    )
    private fun eventPage(query: StoryRecordQuery): StoryRecordPage = StoryRecordPage(
        query, 3, 1, listOf(StoryRecordEntry("event", "Visible event", "Recorded time advanced",
            StoryRecordOrigin.RECORDED_OBSERVATION, event = StoryRecordEvent(reference.sequence,
                "synthetic-record-turn", 3, reference.originalScope), scopedEventSources = listOf(reference))), null,
    )

    @Test fun readerCancellationMakesCurrentPageRetryableAtTheExactFrozenCursor() = runTest {
        for (laterPage in listOf(false, true)) {
            val calls = mutableListOf<StoryRecordQuery>()
            var cancelNext = !laterPage
            val controller = StoryRecordController({ query ->
                calls += query
                if (cancelNext) { cancelNext = false; throw CancellationException(privateFailure) }
                page(query, if (laterPage && query.cursor == null) "synthetic-next" else null)
            }, this)
            try {
                controller.open(context)
                runCurrent()
                if (laterPage) {
                    cancelNext = true
                    controller.next()
                    runCurrent()
                }
                val failedQuery = calls.last()
                val cancelled = controller.state.value
                assertTrue(cancelled.visible)
                assertFalse("A completed cancelled read must not strand the current spinner", cancelled.loading)
                assertEquals(StoryRecordProblem.UNAVAILABLE, cancelled.problem)
                assertEquals(context, cancelled.context)
                assertEquals(if (laterPage) "synthetic-next" else null, cancelled.cursor)
                assertTrue(cancelled.entries.isEmpty())
                assertFalse(cancelled.toString().contains("PRIVATE-READER-CANCEL"))
                val count = calls.size
                runCurrent()
                assertEquals("Cancellation is not an automatic retry grant", count, calls.size)
                controller.retry()
                runCurrent()
                assertEquals(count + 1, calls.size)
                assertEquals(failedQuery, calls.last())
                assertFalse(controller.state.value.loading)
                assertNull(controller.state.value.problem)
                assertEquals("Visible field", controller.state.value.entries.single().title)
            } finally {
                controller.dispose()
                advanceUntilIdle()
            }
        }
    }

    @Test fun readerCancellationMakesOnlyCurrentScopedDetailRetryableAndPreservesItsReference() = runTest {
        val queries = mutableListOf<StoryRecordQuery>()
        var cancelDetail = true
        val controller = StoryRecordController({ query ->
            queries += query
            if (query.section == StoryRecordSection.HISTORY) {
                if (cancelDetail) { cancelDetail = false; throw CancellationException(privateFailure) }
                eventPage(query)
            } else page(query)
        }, this)
        try {
            controller.open(context); runCurrent()
            val originalPage = controller.state.value
            controller.openScopedEvent(reference); runCurrent()
            val detailQuery = queries.last()
            val current = controller.state.value
            val detail = checkNotNull(current.eventDetail)
            assertFalse(detail.loading)
            assertEquals(StoryRecordProblem.UNAVAILABLE, detail.problem)
            assertEquals(reference.sequence, detail.reference)
            assertEquals(reference, detail.scopedReference)
            assertNull(detail.entry)
            assertEquals(originalPage.copy(eventDetail = detail), current)
            assertFalse(current.toString().contains("PRIVATE-READER-CANCEL"))
            val count = queries.size
            controller.retryEvent(); runCurrent()
            assertEquals(count + 1, queries.size)
            assertEquals(detailQuery, queries.last())
            assertEquals(StoryRecordSection.HISTORY, queries.last().section)
            assertEquals(2, queries.last().version)
            assertEquals(context, queries.last().context)
            assertEquals(reference, controller.state.value.eventDetail!!.scopedReference)
            assertEquals(reference.originalScope, controller.state.value.eventDetail!!.entry!!.event!!.originalScope)
            assertFalse(controller.state.value.eventDetail!!.loading)
            assertNull(controller.state.value.eventDetail!!.problem)
            controller.back()
            assertEquals(originalPage, controller.state.value)
        } finally {
            controller.dispose(); advanceUntilIdle()
        }
    }

    @Test fun cancellationBeforeCoroutineEntryEndsCurrentLoadingWithoutEnteringTheReader() = runTest {
        val owner = SupervisorJob(coroutineContext[Job])
        val ownedScope = CoroutineScope(coroutineContext + owner)
        var reads = 0
        val controller = StoryRecordController({ query -> reads++; page(query) }, ownedScope)
        try {
            controller.open(context)
            assertTrue(controller.state.value.loading)
            assertEquals(0, reads)
            // The parent remains live. Only its queued read child is cancelled;
            // a catch inside that child's body cannot observe this case.
            owner.cancelChildren(CancellationException(privateFailure))
            runCurrent()
            assertTrue(owner.isActive)
            assertEquals(0, reads)
            assertTrue(controller.state.value.visible)
            assertFalse(controller.state.value.loading)
            assertEquals(StoryRecordProblem.UNAVAILABLE, controller.state.value.problem)
            assertEquals(context, controller.state.value.context)
            assertFalse(controller.state.value.toString().contains("PRIVATE-READER-CANCEL"))
            controller.retry(); runCurrent()
            assertEquals(1, reads)
            assertFalse(controller.state.value.loading)
            assertNull(controller.state.value.problem)
        } finally {
            controller.dispose(); owner.cancel(); advanceUntilIdle()
        }
    }

    @Test fun obsoleteNonCooperativePageCancellationCannotFinishTheNewReadOrReopenDismissal() = runTest {
        val old = CompletableDeferred<Unit>()
        val fresh = CompletableDeferred<Unit>()
        val replacement = context.copy(story = context.story.copy(story = "replacement-story"))
        val controller = StoryRecordController({ query ->
            if (query.context == context) withContext(NonCancellable) {
                old.await(); throw CancellationException(privateFailure)
            } else {
                withContext(NonCancellable) { fresh.await() }
                page(query)
            }
        }, this)
        try {
            controller.open(context); runCurrent()
            controller.open(replacement); runCurrent()
            val loadingReplacement = controller.state.value
            assertTrue(loadingReplacement.loading)
            old.complete(Unit); runCurrent()
            assertEquals(loadingReplacement, controller.state.value)
            fresh.complete(Unit); runCurrent()
            assertEquals(replacement, controller.state.value.context)
            assertFalse(controller.state.value.loading)
            assertNull(controller.state.value.problem)
            controller.open(context)
            controller.dismiss() // Cancel the next queued old read before entry.
            runCurrent()
            assertEquals(StoryRecordState(), controller.state.value)
            controller.dispose()
            controller.open(replacement); controller.retry(); runCurrent()
            assertEquals(StoryRecordState(), controller.state.value)
        } finally {
            old.complete(Unit); fresh.complete(Unit)
            controller.dispose(); advanceUntilIdle()
        }
    }

    @Test fun currentReaderCancellationLeavesParentAndUnrelatedSiblingActiveWithoutAutomaticRetry() = runTest {
        val owner = SupervisorJob(coroutineContext[Job])
        val ownedScope = CoroutineScope(coroutineContext + owner)
        val release = CompletableDeferred<Unit>()
        var siblingFinished = false
        val sibling = ownedScope.launch { release.await(); siblingFinished = true }
        var calls = 0
        val controller = StoryRecordController({ query ->
            calls++
            if (calls == 1) throw CancellationException(privateFailure)
            page(query)
        }, ownedScope)
        try {
            controller.open(context); runCurrent()
            assertTrue(owner.isActive)
            assertTrue(sibling.isActive)
            assertFalse(siblingFinished)
            assertEquals(1, calls)
            assertFalse(controller.state.value.loading)
            assertEquals(StoryRecordProblem.UNAVAILABLE, controller.state.value.problem)
            repeat(3) { runCurrent() }
            assertEquals(1, calls)
            controller.retry(); runCurrent()
            assertEquals(2, calls)
            assertNull(controller.state.value.problem)
            release.complete(Unit); runCurrent()
            assertTrue(siblingFinished)
            assertTrue(sibling.isCompleted)
        } finally {
            release.complete(Unit); controller.dispose(); owner.cancel(); advanceUntilIdle()
        }
    }

    @Test fun oldScopedDetailCancellationAfterBackCannotFinishAReplacementDetail() = runTest {
        val old = CompletableDeferred<Unit>()
        val fresh = CompletableDeferred<Unit>()
        var detailCalls = 0
        val controller = StoryRecordController({ query ->
            if (query.section != StoryRecordSection.HISTORY) page(query)
            else if (++detailCalls == 1) withContext(NonCancellable) {
                old.await(); throw CancellationException(privateFailure)
            } else {
                withContext(NonCancellable) { fresh.await() }
                eventPage(query)
            }
        }, this)
        try {
            controller.open(context); runCurrent()
            val original = controller.state.value
            controller.openScopedEvent(reference); runCurrent()
            assertTrue(controller.state.value.eventDetail!!.loading)
            controller.back()
            assertEquals(original, controller.state.value)
            controller.openScopedEvent(reference); runCurrent()
            val currentLoading = controller.state.value
            assertEquals(2, detailCalls)
            assertTrue(currentLoading.eventDetail!!.loading)
            old.complete(Unit); runCurrent()
            assertEquals(currentLoading, controller.state.value)
            fresh.complete(Unit); runCurrent()
            val detail = controller.state.value.eventDetail!!
            assertFalse(detail.loading)
            assertNull(detail.problem)
            assertEquals(reference, detail.scopedReference)
            assertNotNull(detail.entry)
            controller.back()
            assertEquals(original, controller.state.value)
        } finally {
            old.complete(Unit); fresh.complete(Unit)
            controller.dispose(); advanceUntilIdle()
        }
    }

    @Test fun alreadyCancelledOwnerNeverEntersReaderAndCannotLeaveCurrentLoadingForever() = runTest {
        val owner = SupervisorJob(coroutineContext[Job])
        val ownedScope = CoroutineScope(coroutineContext + owner)
        var calls = 0
        val controller = StoryRecordController({ query -> calls++; page(query) }, ownedScope)
        try {
            owner.cancel(CancellationException(privateFailure))
            controller.open(context)
            runCurrent()
            assertFalse(owner.isActive)
            assertEquals(0, calls)
            assertTrue(controller.state.value.visible)
            assertFalse(controller.state.value.loading)
            assertEquals(StoryRecordProblem.UNAVAILABLE, controller.state.value.problem)
            assertEquals(context, controller.state.value.context)
            assertFalse(controller.state.value.toString().contains("PRIVATE-READER-CANCEL"))
            controller.retry(); runCurrent()
            assertEquals("Retry cannot revive a cancelled owner or enter its reader", 0, calls)
            assertFalse(controller.state.value.loading)
            assertEquals(StoryRecordProblem.UNAVAILABLE, controller.state.value.problem)
        } finally {
            controller.dispose(); owner.cancel(); advanceUntilIdle()
        }
    }

    @Test fun readerCancellingItsRequestThenReturningAValidPageCannotPublishThatCancelledResult() = runTest {
        var cancel = true
        val queries = mutableListOf<StoryRecordQuery>()
        val controller = StoryRecordController({ query ->
            queries += query
            if (cancel) {
                cancel = false
                checkNotNull(currentCoroutineContext()[Job]).cancel(CancellationException(privateFailure))
            }
            // Deliberately no suspension after cancel: return well-formed data.
            page(query)
        }, this)
        try {
            controller.open(context); runCurrent()
            assertEquals(1, queries.size)
            assertTrue(controller.state.value.visible)
            assertFalse(controller.state.value.loading)
            assertEquals(StoryRecordProblem.UNAVAILABLE, controller.state.value.problem)
            assertTrue(controller.state.value.entries.isEmpty())
            assertFalse(controller.state.value.toString().contains("PRIVATE-READER-CANCEL"))
            val originalQuery = queries.single()
            controller.retry(); runCurrent()
            assertEquals(2, queries.size)
            assertEquals(originalQuery, queries.last())
            assertNull(controller.state.value.problem)
            assertEquals("Visible field", controller.state.value.entries.single().title)
        } finally {
            controller.dispose(); advanceUntilIdle()
        }
    }

    @Test fun readerCancellingItsDetailRequestThenReturningAValidEventCannotPublishIt() = runTest {
        var cancelDetail = true
        val queries = mutableListOf<StoryRecordQuery>()
        val controller = StoryRecordController({ query ->
            queries += query
            if (query.section == StoryRecordSection.HISTORY) {
                if (cancelDetail) {
                    cancelDetail = false
                    checkNotNull(currentCoroutineContext()[Job]).cancel(CancellationException(privateFailure))
                }
                eventPage(query)
            } else page(query)
        }, this)
        try {
            controller.open(context); runCurrent()
            val originalPage = controller.state.value
            controller.openScopedEvent(reference); runCurrent()
            val query = queries.last()
            val detail = checkNotNull(controller.state.value.eventDetail)
            assertFalse(detail.loading)
            assertEquals(StoryRecordProblem.UNAVAILABLE, detail.problem)
            assertNull(detail.entry)
            assertEquals(reference, detail.scopedReference)
            assertEquals(originalPage.copy(eventDetail = detail), controller.state.value)
            controller.retryEvent(); runCurrent()
            assertEquals(query, queries.last())
            assertEquals(3, queries.size)
            assertFalse(controller.state.value.eventDetail!!.loading)
            assertNull(controller.state.value.eventDetail!!.problem)
            assertEquals(reference.originalScope, controller.state.value.eventDetail!!.entry!!.event!!.originalScope)
            controller.back()
            assertEquals(originalPage, controller.state.value)
        } finally {
            controller.dispose(); advanceUntilIdle()
        }
    }
}

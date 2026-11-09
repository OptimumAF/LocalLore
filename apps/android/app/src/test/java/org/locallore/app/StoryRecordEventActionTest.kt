/* Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0 */
package org.locallore.app

import kotlinx.coroutines.CompletableDeferred
import kotlinx.coroutines.ExperimentalCoroutinesApi
import kotlinx.coroutines.test.runCurrent
import kotlinx.coroutines.test.runTest
import org.junit.Assert.assertEquals
import org.junit.Assert.assertFalse
import org.junit.Assert.assertNotEquals
import org.junit.Assert.assertNotNull
import org.junit.Assert.assertNotSame
import org.junit.Assert.assertNull
import org.junit.Assert.assertSame
import org.junit.Assert.assertTrue
import org.junit.Test

@OptIn(ExperimentalCoroutinesApi::class)
class StoryRecordEventActionTest {
    private val context = StoryRecordContext(SavedStory("event-action-story", "root", "Synthetic", 2), 2)
    private val reference = StoryRecordScopedEvent(StoryRecordScope(context.story.story, "ancestor"), 1)

    private fun sourcePage(query: StoryRecordQuery) = StoryRecordPage(
        query, 3, 1, listOf(StoryRecordEntry(
            "field", "Visible field", "Player", StoryRecordOrigin.CANONICAL_FIELD,
            scopedEventSources = listOf(reference),
        )), null,
    )

    private fun eventPage(query: StoryRecordQuery) = StoryRecordPage(
        query, 3, 1, listOf(StoryRecordEntry(
            "event", "Visible event", "Recorded time advanced", StoryRecordOrigin.RECORDED_OBSERVATION,
            event = StoryRecordEvent(reference.sequence, "event-action-turn", 3, reference.originalScope),
            scopedEventSources = listOf(reference),
        )), null,
    )

    @Test fun backCapturedWhileLoadingClosesTheSameViewAfterItSettles() = runTest {
        val controller = StoryRecordController({ query ->
            if (query.section == StoryRecordSection.HISTORY) eventPage(query) else sourcePage(query)
        }, this)
        try {
            controller.open(context)
            runCurrent()
            val source = controller.state.value
            controller.openScopedEvent(reference)
            val renderedLoading = checkNotNull(controller.state.value.eventDetail)
            assertTrue(renderedLoading.loading)

            runCurrent()
            val settled = checkNotNull(controller.state.value.eventDetail)
            assertFalse(settled.loading)
            assertNotNull(settled.entry)
            assertNotSame(renderedLoading, settled)

            controller.back(renderedLoading)
            assertEquals(source, controller.state.value)
        } finally {
            controller.dispose()
        }
    }

    @Test fun retainedActionsCannotAffectAReopenedViewOfTheSameEvent() = runTest {
        val finishReplacement = CompletableDeferred<Unit>()
        val queries = mutableListOf<StoryRecordQuery>()
        val controller = StoryRecordController({ query ->
            if (query.section != StoryRecordSection.HISTORY) {
                sourcePage(query)
            } else {
                queries += query
                if (queries.size == 2) finishReplacement.await()
                if (queries.size <= 2) throw StoryRecordFailure(StoryRecordProblem.EVENT_UNAVAILABLE)
                eventPage(query)
            }
        }, this)
        try {
            controller.open(context)
            runCurrent()
            val source = controller.state.value
            controller.openScopedEvent(reference)
            runCurrent()
            val oldFailure = checkNotNull(controller.state.value.eventDetail)
            assertEquals(StoryRecordProblem.EVENT_UNAVAILABLE, oldFailure.problem)
            controller.back(oldFailure)
            assertEquals(source, controller.state.value)

            controller.openScopedEvent(reference)
            runCurrent()
            val replacementLoading = checkNotNull(controller.state.value.eventDetail)
            assertTrue(replacementLoading.loading)
            assertEquals(reference, replacementLoading.scopedReference)
            assertEquals(2, queries.size)

            controller.back(oldFailure)
            runCurrent()
            assertSame(replacementLoading, controller.state.value.eventDetail)

            finishReplacement.complete(Unit)
            runCurrent()
            val replacementFailure = checkNotNull(controller.state.value.eventDetail)
            assertEquals(StoryRecordProblem.EVENT_UNAVAILABLE, replacementFailure.problem)
            controller.retryEvent(oldFailure)
            runCurrent()
            assertSame(replacementFailure, controller.state.value.eventDetail)
            assertEquals(2, queries.size)

            controller.retryEvent(replacementFailure)
            runCurrent()
            assertEquals(3, queries.size)
            assertTrue(queries.all { it == queries.first() })
            assertNotNull(controller.state.value.eventDetail?.entry)
        } finally {
            finishReplacement.complete(Unit)
            controller.dispose()
        }
    }

    @Test fun retryRequiresTheExactCurrentFailureAndBackSurvivesSameViewRetries() = runTest {
        val queries = mutableListOf<StoryRecordQuery>()
        val controller = StoryRecordController({ query ->
            if (query.section != StoryRecordSection.HISTORY) {
                sourcePage(query)
            } else {
                queries += query
                if (queries.size <= 2) throw StoryRecordFailure(StoryRecordProblem.EVENT_UNAVAILABLE)
                eventPage(query)
            }
        }, this)
        try {
            controller.open(context)
            runCurrent()
            val source = controller.state.value
            controller.openScopedEvent(reference)
            runCurrent()
            val firstFailure = checkNotNull(controller.state.value.eventDetail)

            controller.retryEvent(firstFailure.copy())
            runCurrent()
            assertSame(firstFailure, controller.state.value.eventDetail)
            assertEquals(1, queries.size)

            controller.retryEvent(firstFailure)
            controller.retryEvent(firstFailure)
            runCurrent()
            val secondFailure = checkNotNull(controller.state.value.eventDetail)
            assertNotSame(firstFailure, secondFailure)
            assertNotEquals("An identical visible failure still needs a fresh StateFlow emission", firstFailure, secondFailure)
            assertEquals(firstFailure.scopedReference, secondFailure.scopedReference)
            assertEquals(firstFailure.problem, secondFailure.problem)
            assertEquals(firstFailure.entry, secondFailure.entry)
            assertEquals(StoryRecordProblem.EVENT_UNAVAILABLE, secondFailure.problem)
            assertEquals(2, queries.size)

            controller.retryEvent(firstFailure)
            runCurrent()
            assertSame(secondFailure, controller.state.value.eventDetail)
            assertEquals(2, queries.size)

            controller.retryEvent(secondFailure)
            runCurrent()
            val settled = checkNotNull(controller.state.value.eventDetail)
            assertNull(settled.problem)
            assertNotNull(settled.entry)
            assertEquals(3, queries.size)
            assertTrue(queries.all { it == queries.first() })

            controller.retryEvent(secondFailure)
            controller.retryEvent(settled)
            runCurrent()
            assertSame(settled, controller.state.value.eventDetail)
            assertEquals(3, queries.size)

            controller.back(firstFailure)
            assertEquals(source, controller.state.value)
        } finally {
            controller.dispose()
        }
    }
}

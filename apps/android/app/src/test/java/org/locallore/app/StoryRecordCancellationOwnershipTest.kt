/* Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0 */
package org.locallore.app

import kotlinx.coroutines.CancellationException
import kotlinx.coroutines.CoroutineScope
import kotlinx.coroutines.ExperimentalCoroutinesApi
import kotlinx.coroutines.Job
import kotlinx.coroutines.SupervisorJob
import kotlinx.coroutines.currentCoroutineContext
import kotlinx.coroutines.test.UnconfinedTestDispatcher
import kotlinx.coroutines.test.advanceUntilIdle
import kotlinx.coroutines.test.runCurrent
import kotlinx.coroutines.test.runTest
import org.junit.Assert.*
import org.junit.Test

/** Supplemental ownership oracles; fake read ports never establish native closure. */
@OptIn(ExperimentalCoroutinesApi::class)
class StoryRecordCancellationOwnershipTest {
    private val context = StoryRecordContext(SavedStory("cancel-owner", "child", "Synthetic", 2), 2)
    private val reference = StoryRecordScopedEvent(StoryRecordScope("cancel-owner", "root"), 1)
    private fun page(query: StoryRecordQuery) = StoryRecordPage(query, 2, 1,
        listOf(StoryRecordEntry("field", "Visible field", "Visible value", StoryRecordOrigin.CANONICAL_FIELD,
            scopedEventSources = listOf(reference))), null)
    private fun event(query: StoryRecordQuery) = StoryRecordPage(query, 2, 1,
        listOf(StoryRecordEntry("event", "Observed event", "Visible observation", StoryRecordOrigin.RECORDED_OBSERVATION,
            event = StoryRecordEvent(1, "synthetic-turn", 2, reference.originalScope),
            scopedEventSources = listOf(reference))), null)

    @Test fun settlingPageAndDetailCancellationDoesNotTurnTheirRequestJobsIntoSuccess() = runTest {
        for (detail in listOf(false, true)) {
            var request: Job? = null
            var cancelled = false
            val controller = StoryRecordController({ query ->
                if (!cancelled && (query.section == StoryRecordSection.HISTORY) == detail) {
                    cancelled = true
                    request = currentCoroutineContext()[Job]
                    throw CancellationException("PRIVATE-CANCEL-PAYLOAD")
                }
                if (query.section == StoryRecordSection.HISTORY) event(query) else page(query)
            }, this)
            try {
                controller.open(context); runCurrent()
                if (detail) { controller.openScopedEvent(reference); runCurrent() }
                val original = checkNotNull(request)
                assertTrue(original.isCompleted)
                assertTrue("UI settlement must not swallow request cancellation", original.isCancelled)
                assertTrue(checkNotNull(coroutineContext[Job]).isActive)
                if (detail) {
                    assertEquals(StoryRecordProblem.UNAVAILABLE, controller.state.value.eventDetail!!.problem)
                    controller.retryEvent(); runCurrent()
                    assertNotNull(controller.state.value.eventDetail!!.entry)
                } else {
                    assertEquals(StoryRecordProblem.UNAVAILABLE, controller.state.value.problem)
                    controller.retry(); runCurrent()
                    assertEquals("Visible value", controller.state.value.entries.single().text)
                }
                assertTrue(original.isCancelled)
                assertFalse(controller.state.value.toString().contains("PRIVATE-CANCEL-PAYLOAD"))
            } finally {
                controller.dispose(); advanceUntilIdle()
            }
        }
    }

    @Test fun immediateOwnerDispatchCanFinishCancellationBeforeLaunchReadReturnsAndStillRetry() = runTest {
        val owner = SupervisorJob(coroutineContext[Job])
        val immediate = CoroutineScope(coroutineContext + owner + UnconfinedTestDispatcher(testScheduler))
        var calls = 0
        val controller = StoryRecordController({ query ->
            calls++
            if (calls == 1) throw CancellationException("PRIVATE-IMMEDIATE-CANCEL")
            page(query)
        }, immediate)
        try {
            controller.open(context)
            assertEquals(1, calls)
            assertFalse(controller.state.value.loading)
            assertEquals(StoryRecordProblem.UNAVAILABLE, controller.state.value.problem)
            controller.retry()
            assertEquals(2, calls)
            assertNull(controller.state.value.problem)
            assertEquals(context, controller.state.value.context)
            assertEquals("Visible value", controller.state.value.entries.single().text)
            controller.dismiss()
            controller.open(context)
            assertEquals(3, calls)
            assertFalse(controller.state.value.loading)
            assertNull(controller.state.value.problem)
        } finally {
            controller.dispose(); owner.cancel(); advanceUntilIdle()
        }
    }
}

/* Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0 */
package org.locallore.app

import kotlinx.coroutines.CancellationException
import kotlinx.coroutines.CompletableDeferred
import kotlinx.coroutines.CoroutineScope
import kotlinx.coroutines.ExperimentalCoroutinesApi
import kotlinx.coroutines.Job
import kotlinx.coroutines.NonCancellable
import kotlinx.coroutines.currentCoroutineContext
import kotlinx.coroutines.test.TestScope
import kotlinx.coroutines.test.advanceUntilIdle
import kotlinx.coroutines.test.runCurrent
import kotlinx.coroutines.test.runTest
import kotlinx.coroutines.withContext
import org.junit.Assert.*
import org.junit.Test

/** Controller-contract tests only. Fake ports establish no native/provider drain or Store write. */
@OptIn(ExperimentalCoroutinesApi::class)
class OriginalStoryCancellationTest {
    private enum class Stage { GENERATE, REVIEW, CREATE }
    private val input = OriginalInput("A clockmaker crosses a frozen orchard.", "Iris",
        playerDescription = "Keep this literal description.")
    private val world = OriginalProposal(
        listOf(OriginalLocation("Orchard", "Frost covers the trees.")), 0,
        listOf(OriginalCharacter("Tovin", "A patient gardener.", 0, listOf(0, 1))),
        emptyList(), listOf(OriginalFact("The gate is shut.", listOf(1), 0)),
        listOf(OriginalBelief(1, "The clock is late.", "suspected")), emptyList())
    private val privateCancellation = "PRIVATE_CANCEL_PAYLOAD_9E38"

    private inner class Port(val provider: String) : OriginalStoryGateway {
        val begun = mutableListOf<String>()
        val generated = mutableListOf<String>()
        val reviewed = mutableListOf<String>()
        val creates = mutableListOf<OriginalReview>()
        val creationIds = mutableListOf<String>()
        val cancelled = mutableListOf<String>()
        val jobs = mutableMapOf<Stage, Job>()
        val inputs = mutableMapOf<String, OriginalInput>()
        var failStage: Stage? = null
        var heldStage: Stage? = null
        val entered = CompletableDeferred<Unit>()
        val release = CompletableDeferred<Unit>()
        private suspend fun reach(stage: Stage) {
            jobs[stage] = checkNotNull(currentCoroutineContext()[Job])
            if (heldStage == stage) {
                entered.complete(Unit)
                withContext(NonCancellable) { release.await() }
            }
            if (failStage == stage) throw CancellationException(privateCancellation)
        }
        override suspend fun originalCapabilities() = OriginalCapabilities(true, provider)
        override suspend fun beginOriginal(input: OriginalInput): OriginalJob {
            val id = "job-${begun.size + 1}"
            begun += id
            inputs[id] = input
            return OriginalJob(id, "a".repeat(64), provider)
        }
        override suspend fun generateOriginal(job: String): OriginalGenerated {
            generated += job
            reach(Stage.GENERATE)
            return OriginalGenerated(job, checkNotNull(inputs[job]), world, provider)
        }
        override suspend fun reviewOriginal(job: String, input: OriginalInput,
            proposal: OriginalProposal, title: String): OriginalReview {
            reviewed += job
            reach(Stage.REVIEW)
            return OriginalReview(job, reviewed.size.toString(16).padStart(64, '0'), input,
                proposal, title, listOf("World truth: gate shut. Private belief: clock late."))
        }
        override suspend fun createOriginal(review: OriginalReview, creationId: String): SavedSnapshot {
            // Reaching the port is an attempted write, not proof a real commit happened.
            creates += review
            creationIds += creationId
            reach(Stage.CREATE)
            return SavedSnapshot(0, "Iris", emptyList(), "synthetic", 1, emptyList(),
                SavedStory("original-$creationId", "main", review.title, 0))
        }
        override suspend fun cancelOriginal(job: String): Boolean {
            cancelled += job
            return true
        }
    }

    private inner class Harness(scope: CoroutineScope, provider: String = "scripted") {
        val port = Port(provider)
        val values = mutableListOf<OriginalStoryUiState>()
        val closed = mutableListOf<StoryCreationClose>()
        val controller = OriginalStoryController(port, scope, values::add, closed::add)
        val state: OriginalStoryUiState get() = values.last()
        init {
            controller.open(OriginalCapabilities(true, provider))
            controller.edit(state, input, null, "Cancellation orchard")
        }
    }
    private fun TestScope.generated(h: Harness) {
        h.controller.generate(h.state)
        advanceUntilIdle()
        assertNotNull(h.state.proposal)
        assertFalse(h.state.busy)
    }
    private fun TestScope.reviewed(h: Harness) {
        if (h.state.proposal == null) generated(h)
        h.controller.review(h.state)
        advanceUntilIdle()
        assertNotNull(h.state.review)
        assertFalse(h.state.busy)
    }
    private fun assertDraft(before: OriginalStoryUiState, after: OriginalStoryUiState) {
        assertEquals(before.input, after.input)
        assertEquals(before.proposal, after.proposal)
        assertEquals(before.title, after.title)
    }
    private fun assertStopped(h: Harness, progress: String?) {
        assertFalse(h.state.busy)
        assertFalse(h.state.creating)
        assertFalse(h.state.closing)
        assertNull(h.state.review)
        val notice = checkNotNull(h.state.notice).lowercase()
        assertTrue("Terminal cancellation needs an explicit stopped status", notice.contains("stopped"))
        assertNotEquals(progress, h.state.notice)
        assertTrue(notice.contains("nothing") && notice.contains("created"))
        assertNoPayload(h)
    }
    private fun assertNoPayload(h: Harness) {
        assertTrue(h.values.none { it.notice?.contains(privateCancellation) == true })
    }
    private fun TestScope.hold(h: Harness, stage: Stage): OriginalStoryUiState {
        if (stage != Stage.GENERATE) generated(h)
        if (stage == Stage.CREATE) reviewed(h)
        val before = h.state
        h.port.heldStage = stage
        h.port.failStage = stage
        when (stage) {
            Stage.GENERATE -> h.controller.generate(before)
            Stage.REVIEW -> h.controller.review(before)
            Stage.CREATE -> h.controller.confirm(before, checkNotNull(before.review))
        }
        runCurrent()
        assertTrue("Held operation must actually have entered", h.port.entered.isCompleted)
        assertTrue(h.state.busy)
        return before
    }

    @Test fun successfulCurrentFlowCreatesExactlyTheExplicitReviewOnce() = runTest {
        val h = Harness(this)
        try {
            reviewed(h)
            val current = h.state
            val consent = checkNotNull(current.review)
            h.controller.confirm(current, consent)
            h.controller.confirm(current, consent)
            advanceUntilIdle()
            assertEquals(listOf(consent), h.port.creates)
            assertEquals(1, h.port.creationIds.size)
            assertTrue(h.port.creationIds.single().matches(Regex("[0-9a-f]{32}")))
            assertEquals(1, h.closed.size)
            assertNotNull(h.closed.single().saved)
            assertFalse(h.closed.single().refreshRequired)
            assertNoPayload(h)
        } finally { h.port.release.complete(Unit); h.controller.dispose(); advanceUntilIdle() }
    }

    @Test fun currentGenerationCancellationStopsWithoutLosingInputOrPreviousWorldOrRetrying() = runTest {
        for (provider in listOf("scripted", "local")) for (regenerating in listOf(false, true)) {
            val h = Harness(this, provider) // Provider label only, never a language-model execution.
            try {
                if (regenerating) generated(h)
                val before = h.state
                h.port.failStage = Stage.GENERATE
                h.controller.generate(before)
                val progress = h.state.notice
                advanceUntilIdle()
                assertStopped(h, progress)
                assertDraft(before, h.state)
                assertTrue(h.port.jobs.getValue(Stage.GENERATE).isCancelled)
                assertTrue(coroutineContext[Job]!!.isActive)
                assertEquals(if (regenerating) 2 else 1, h.port.begun.size)
                assertEquals(h.port.begun, h.port.generated)
                // A user-requested regenerate first cancels its old job; the newly
                // cancelled attempt must not cause an extra automatic gateway cancel.
                assertEquals(before.job?.let { listOf(it) } ?: emptyList<String>(), h.port.cancelled)
                assertTrue(h.port.reviewed.isEmpty())
                assertTrue(h.port.creates.isEmpty())
                assertTrue(h.closed.isEmpty())
                val attempts = h.port.generated.size
                advanceUntilIdle()
                assertEquals(attempts, h.port.generated.size)
                h.port.failStage = null
                h.controller.generate(h.state) // Explicit retry only.
                advanceUntilIdle()
                assertEquals(attempts + 1, h.port.generated.size)
                assertNotNull(h.state.proposal)
                assertNull(h.state.review)
                assertTrue(h.port.creates.isEmpty())
            } finally { h.port.release.complete(Unit); h.controller.dispose(); advanceUntilIdle() }
        }
    }

    @Test fun currentReviewCancellationRevokesOldConsentAndPreservesTheExactDraft() = runTest {
        val h = Harness(this)
        try {
            reviewed(h)
            val before = h.state
            val previousConsent = checkNotNull(before.review)
            h.port.failStage = Stage.REVIEW
            h.controller.review(before)
            val progress = h.state.notice
            advanceUntilIdle()
            assertStopped(h, progress)
            assertDraft(before, h.state)
            assertTrue(h.port.jobs.getValue(Stage.REVIEW).isCancelled)
            assertTrue(coroutineContext[Job]!!.isActive)
            assertEquals(2, h.port.reviewed.size)
            assertEquals(1, h.port.generated.size)
            assertTrue(h.port.cancelled.isEmpty())
            h.controller.confirm(before, previousConsent)
            h.controller.confirm(h.state, previousConsent)
            advanceUntilIdle()
            assertTrue(h.port.creates.isEmpty())
            assertTrue(h.closed.isEmpty())
            h.port.failStage = null
            h.controller.review(h.state)
            advanceUntilIdle()
            assertEquals(3, h.port.reviewed.size)
            assertNotNull(h.state.review)
            assertNotSame(previousConsent, h.state.review)
            assertTrue(h.port.creates.isEmpty())
        } finally { h.port.release.complete(Unit); h.controller.dispose(); advanceUntilIdle() }
    }

    @Test fun currentCreateCancellationKeepsUncertaintyAndConsumesCreateUntilRefresh() = runTest {
        val h = Harness(this)
        try {
            reviewed(h)
            val before = h.state
            val consent = checkNotNull(before.review)
            h.port.failStage = Stage.CREATE
            h.controller.confirm(before, consent)
            val progress = h.state.notice
            advanceUntilIdle()
            assertFalse(h.state.busy)
            assertFalse(h.state.creating)
            assertNull(h.state.review)
            assertDraft(before, h.state)
            val notice = checkNotNull(h.state.notice).lowercase()
            assertTrue(notice.contains("confirmed"))
            assertTrue(notice.contains("may already exist"))
            assertTrue(notice.contains("refresh"))
            assertFalse(notice.contains("nothing was created"))
            assertNotEquals(progress, h.state.notice)
            assertNoPayload(h)
            assertTrue(h.port.jobs.getValue(Stage.CREATE).isCancelled)
            assertTrue(coroutineContext[Job]!!.isActive)
            assertEquals(listOf(consent), h.port.creates)
            assertTrue(h.port.cancelled.isEmpty())
            assertTrue(h.closed.isEmpty())
            val stopped = h.state
            h.controller.confirm(before, consent)
            h.controller.confirm(stopped, consent)
            h.controller.generate(stopped)
            h.controller.review(stopped)
            h.controller.edit(stopped, OriginalStoryEdit.Text(OriginalTextField.TITLE, "Must not save this"))
            advanceUntilIdle()
            assertSame(stopped, h.state)
            assertEquals(1, h.port.creates.size)
            assertEquals(1, h.port.generated.size)
            assertEquals(1, h.port.reviewed.size)
            h.controller.dismiss()
            advanceUntilIdle()
            assertEquals(listOf(StoryCreationClose(refreshRequired = true)), h.closed)
            assertEquals(1, h.port.creates.size)
        } finally { h.port.release.complete(Unit); h.controller.dispose(); advanceUntilIdle() }
    }

    @Test fun lateCancelledOperationsAfterDismissCannotReplaceClosingOrCloseTwice() = runTest {
        for (stage in Stage.entries) {
            val h = Harness(this)
            try {
                hold(h, stage)
                h.controller.dismiss()
                runCurrent()
                assertTrue(h.state.closing)
                assertTrue(h.closed.isEmpty())
                val closing = h.state
                val count = h.values.size
                h.port.release.complete(Unit)
                advanceUntilIdle()
                assertEquals(listOf(StoryCreationClose(refreshRequired = (stage == Stage.CREATE))), h.closed)
                assertTrue(h.values.drop(count).all { it.closing && it.notice == closing.notice })
                assertEquals(if (stage == Stage.CREATE) 1 else 0, h.port.creates.size)
                assertTrue(h.port.jobs.getValue(stage).isCancelled)
                assertNoPayload(h)
            } finally { h.port.release.complete(Unit); h.controller.dispose(); advanceUntilIdle() }
        }
    }

    @Test fun lateCancelledOperationsAfterDisposeCannotPublishOrFinishRetainedViews() = runTest {
        for (stage in Stage.entries) {
            val h = Harness(this)
            try {
                val retained = hold(h, stage)
                val attempts = listOf(h.port.begun.size, h.port.generated.size, h.port.reviewed.size, h.port.creates.size)
                h.controller.dispose()
                val count = h.values.size
                h.port.release.complete(Unit)
                advanceUntilIdle()
                h.controller.generate(retained)
                h.controller.review(retained)
                retained.review?.let { h.controller.confirm(retained, it) }
                h.controller.edit(retained, OriginalStoryEdit.Text(OriginalTextField.TITLE, "Disposed edit"))
                h.controller.dismiss()
                advanceUntilIdle()
                assertEquals(count, h.values.size)
                assertTrue(h.closed.isEmpty())
                assertEquals(attempts, listOf(h.port.begun.size, h.port.generated.size, h.port.reviewed.size, h.port.creates.size))
                assertTrue(h.port.jobs.getValue(stage).isCancelled)
                assertNoPayload(h)
            } finally { h.port.release.complete(Unit); h.controller.dispose(); advanceUntilIdle() }
        }
    }
}

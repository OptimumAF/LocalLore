/* Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0 */
package org.locallore.app

import kotlinx.coroutines.CompletableDeferred
import kotlinx.coroutines.CoroutineScope
import kotlinx.coroutines.ExperimentalCoroutinesApi
import kotlinx.coroutines.NonCancellable
import kotlinx.coroutines.test.runCurrent
import kotlinx.coroutines.test.runTest
import kotlinx.coroutines.withContext
import org.junit.Assert.assertEquals
import org.junit.Assert.assertFalse
import org.junit.Assert.assertNull
import org.junit.Assert.assertTrue
import org.junit.Test

@OptIn(ExperimentalCoroutinesApi::class)
class OriginalStoryBeginHandoffTest {
    private class Fixture(scope: CoroutineScope, val jobId: String) : OriginalStoryGateway {
        private val capabilities = OriginalCapabilities(true, "scripted")
        private val input = OriginalInput("A diver maps a tide bell beneath the pier.", "Iris")
        val proposal = OriginalProposal(
            listOf(OriginalLocation("Pier", "The tide is rising.")), 0,
            listOf(OriginalCharacter("Mara", "A watchkeeper.", 0, listOf(0, 1))),
            emptyList(), emptyList(), emptyList(), emptyList(),
        )
        val calls = mutableListOf<String>()
        val closures = mutableListOf<StoryCreationClose>()
        lateinit var state: OriginalStoryUiState
            private set
        val controller = OriginalStoryController(this, scope, { state = it }, closures::add)
        var nextJobId = jobId
        var waitForBegin: suspend () -> Unit = {}
        var beforeGenerate: () -> Unit = {}
        var acknowledgeCancel: suspend () -> Boolean = { true }

        init {
            controller.open(capabilities)
            controller.edit(state, input, null, "The Tide Bell")
        }

        override suspend fun originalCapabilities() = capabilities

        override suspend fun beginOriginal(input: OriginalInput): OriginalJob {
            calls += "begin"
            assertEquals(this.input, input)
            waitForBegin()
            return OriginalJob(nextJobId, "a".repeat(64), "scripted")
        }

        override suspend fun generateOriginal(job: String): OriginalGenerated {
            calls += "generate:$job"
            beforeGenerate()
            return OriginalGenerated(job, input, proposal, "scripted")
        }

        override suspend fun cancelOriginal(job: String): Boolean {
            calls += "cancel:$job"
            return acknowledgeCancel()
        }

        override suspend fun reviewOriginal(
            job: String, input: OriginalInput, proposal: OriginalProposal, title: String,
        ): OriginalReview = error("Unexpected review")

        override suspend fun createOriginal(review: OriginalReview, creationId: String): SavedSnapshot =
            error("Unexpected create")
    }

    @Test
    fun dismissWaitsForBeginAndTheExactCancellationAcknowledgement() = runTest {
        val fixture = Fixture(this, "initial-41")
        val beginReply = CompletableDeferred<Unit>()
        val cancelReply = CompletableDeferred<Boolean>()
        fixture.waitForBegin = { beginReply.await() }
        fixture.acknowledgeCancel = { cancelReply.await() }

        try {
            fixture.controller.generate(fixture.state)
            runCurrent()
            assertEquals(listOf("begin"), fixture.calls)

            fixture.controller.dismiss()
            runCurrent()
            assertTrue(fixture.state.closing)
            assertTrue("Closing cannot drop an in-flight Begin reply", fixture.closures.isEmpty())

            beginReply.complete(Unit)
            runCurrent()
            assertEquals(listOf("begin", "cancel:initial-41"), fixture.calls)
            assertTrue("Closing must wait for the cancellation reply", fixture.closures.isEmpty())
            assertNull(fixture.state.proposal)
            assertNull(fixture.state.review)

            cancelReply.complete(true)
            runCurrent()
            assertEquals(listOf(StoryCreationClose()), fixture.closures)
        } finally {
            beginReply.complete(Unit)
            cancelReply.complete(true)
        }
    }

    @Test
    fun beginThatReturnsToARetiredDialogCannotGenerate() = runTest {
        val fixture = Fixture(this, "initial-53")
        val beginReply = CompletableDeferred<Unit>()
        fixture.waitForBegin = { withContext(NonCancellable) { beginReply.await() } }

        try {
            fixture.controller.generate(fixture.state)
            runCurrent()
            fixture.controller.dismiss()
            runCurrent()

            beginReply.complete(Unit)
            runCurrent()
            assertEquals(listOf("begin", "cancel:initial-53"), fixture.calls)
            assertEquals(listOf(StoryCreationClose()), fixture.closures)
            assertNull(fixture.state.proposal)
        } finally {
            beginReply.complete(Unit)
        }
    }

    @Test
    fun failedCancellationOfTheLateJobDoesNotReportAnOrdinaryClose() = runTest {
        val fixture = Fixture(this, "initial-67")
        val beginReply = CompletableDeferred<Unit>()
        fixture.waitForBegin = { withContext(NonCancellable) { beginReply.await() } }
        fixture.acknowledgeCancel = { error("Synthetic cancellation reply lost") }

        try {
            fixture.controller.generate(fixture.state)
            runCurrent()
            fixture.controller.dismiss()
            runCurrent()

            beginReply.complete(Unit)
            runCurrent()
            assertTrue("An unknown cancellation outcome cannot close normally", fixture.closures.isEmpty())
            assertEquals(listOf("begin", "cancel:initial-67"), fixture.calls)
            assertTrue(fixture.state.closing)
            assertTrue(fixture.state.notice.orEmpty().contains("could not be confirmed"))
        } finally {
            beginReply.complete(Unit)
        }
    }

    @Test
    fun malformedBeginReplyAfterDismissCannotConfirmClosure() = runTest {
        val fixture = Fixture(this, "initial-71")
        val beginReply = CompletableDeferred<Unit>()
        fixture.waitForBegin = {
            beginReply.await()
            throw WorkspaceFailure("Malformed")
        }

        try {
            fixture.controller.generate(fixture.state)
            runCurrent()
            fixture.controller.dismiss()
            runCurrent()

            beginReply.complete(Unit)
            runCurrent()
            assertEquals(listOf("begin"), fixture.calls)
            assertTrue("Begin may have succeeded without a usable job ID", fixture.closures.isEmpty())
            assertTrue(fixture.state.closing)
            assertTrue(fixture.state.notice.orEmpty().contains("could not be confirmed"))
        } finally {
            beginReply.complete(Unit)
        }
    }

    @Test
    fun explicitBeginRejectionAfterDismissAllowsOrdinaryClose() = runTest {
        val fixture = Fixture(this, "initial-73")
        val beginReply = CompletableDeferred<Unit>()
        fixture.waitForBegin = {
            withContext(NonCancellable) { beginReply.await() }
            throw WorkspaceFailure("Busy")
        }

        try {
            fixture.controller.generate(fixture.state)
            runCurrent()
            fixture.controller.dismiss()
            runCurrent()
            assertTrue(fixture.closures.isEmpty())

            beginReply.complete(Unit)
            runCurrent()
            assertEquals(listOf("begin"), fixture.calls)
            assertEquals(listOf(StoryCreationClose()), fixture.closures)
        } finally {
            beginReply.complete(Unit)
        }
    }

    @Test
    fun dismissDuringRegenerationWaitsForOldJobWithoutCancellingItTwice() = runTest {
        val fixture = Fixture(this, "initial-77")
        val cancelReply = CompletableDeferred<Boolean>()
        fixture.acknowledgeCancel = { withContext(NonCancellable) { cancelReply.await() } }

        try {
            fixture.controller.generate(fixture.state)
            runCurrent()
            assertEquals(listOf("begin", "generate:initial-77"), fixture.calls)

            fixture.controller.generate(fixture.state)
            runCurrent()
            val expected = listOf("begin", "generate:initial-77", "cancel:initial-77")
            assertEquals(expected, fixture.calls)

            fixture.controller.dismiss()
            runCurrent()
            assertTrue(fixture.closures.isEmpty())

            cancelReply.complete(true)
            runCurrent()
            assertEquals(expected, fixture.calls)
            assertEquals(listOf(StoryCreationClose()), fixture.closures)
        } finally {
            cancelReply.complete(true)
        }
    }

    @Test
    fun currentBeginCanGenerateAndAnExplicitFalseCancellationRequiresRefresh() = runTest {
        val fixture = Fixture(this, "initial-79")
        fixture.acknowledgeCancel = { false }

        fixture.controller.generate(fixture.state)
        runCurrent()
        assertEquals(listOf("begin", "generate:initial-79"), fixture.calls)
        assertEquals(fixture.jobId, fixture.state.job)
        assertEquals(fixture.proposal, fixture.state.proposal)
        assertFalse(fixture.state.busy)
        assertNull(fixture.state.review)

        fixture.controller.dismiss()
        runCurrent()
        assertEquals(listOf("begin", "generate:initial-79", "cancel:initial-79"), fixture.calls)
        assertEquals(listOf(StoryCreationClose(refreshRequired = true)), fixture.closures)
    }

    @Test
    fun failedRegenerationDoesNotBindTheOldProposalToAJobForReview() = runTest {
        val fixture = Fixture(this, "initial-91")
        fixture.controller.generate(fixture.state)
        runCurrent()
        assertEquals(fixture.proposal, fixture.state.proposal)
        assertEquals(fixture.jobId, fixture.state.job)

        fixture.beforeGenerate = { error("Synthetic generation failed") }
        fixture.nextJobId = "initial-92"
        fixture.controller.generate(fixture.state)
        runCurrent()
        assertEquals("generate:initial-92", fixture.calls.last())
        assertEquals(fixture.proposal, fixture.state.proposal)
        assertNull("Only successful generation can bind the visible proposal to a job", fixture.state.job)
        assertNull(fixture.state.review)
    }
}

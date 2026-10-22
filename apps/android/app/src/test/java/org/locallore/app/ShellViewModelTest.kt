package org.locallore.app

import androidx.lifecycle.ViewModelStore
import kotlinx.coroutines.CompletableDeferred
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.ExperimentalCoroutinesApi
import kotlinx.coroutines.NonCancellable
import kotlinx.coroutines.delay
import kotlinx.coroutines.test.StandardTestDispatcher
import kotlinx.coroutines.test.TestCoroutineScheduler
import kotlinx.coroutines.test.advanceUntilIdle
import kotlinx.coroutines.test.resetMain
import kotlinx.coroutines.test.runCurrent
import kotlinx.coroutines.test.runTest
import kotlinx.coroutines.test.setMain
import kotlinx.coroutines.withContext
import org.junit.After
import org.junit.Assert.*
import org.junit.Before
import org.junit.Test

@OptIn(ExperimentalCoroutinesApi::class)
class ShellViewModelTest {
    private val scheduler = TestCoroutineScheduler()
    private val dispatcher = StandardTestDispatcher(scheduler)
    private val store = ViewModelStore()
    private var stores = 0
    @Before fun setup() { Dispatchers.setMain(dispatcher) }
    @After fun cleanup() { store.clear(); Dispatchers.resetMain() }

    private fun model(gateway: DemoGateway): ShellViewModel = ShellViewModel(gateway).also {
        store.put("model-${stores++}", it)
    }

    @Test fun acceptedStateIsPublishedOnlyAfterGatewayCompletes() = runTest(dispatcher) {
        val result = CompletableDeferred<DemoResult>()
        val model = model { _, _, _ -> result.await() }
        model.submit(DemoAction.GIVE_POTION)
        runCurrent()
        assertTrue(model.state.value.busy)
        assertEquals("You", model.state.value.potionOwner)
        assertEquals(0L, model.state.value.revision)
        assertTrue(model.state.value.messages.isEmpty())
        result.complete(DemoResult.Accepted(1, "Mira", "Accepted sample."))
        advanceUntilIdle()
        assertFalse(model.state.value.busy)
        assertEquals(1L, model.state.value.revision)
        assertEquals("Mira", model.state.value.potionOwner)
        assertEquals(2, model.state.value.messages.size)
    }

    @Test fun duplicateTapDoesNotStartAnotherRequest() = runTest(dispatcher) {
        var calls = 0
        val model = model { _, _, _ -> calls++; delay(5_000); DemoResult.Rejected("Ability") }
        model.submit(DemoAction.GIVE_POTION)
        model.submit(DemoAction.GIVE_POTION)
        advanceUntilIdle()
        assertEquals(1, calls)
        assertEquals(0L, model.state.value.revision)
    }

    @Test fun rejectionAndProviderFailureKeepProjectionAndTranscript() = runTest(dispatcher) {
        for (gateway in listOf<DemoGateway>(
            DemoGateway { _, _, _ -> DemoResult.Rejected("Malformed") },
            DemoGateway { _, _, _ -> error("synthetic failure") },
        )) {
            val model = model(gateway)
            model.submit(DemoAction.GIVE_POTION)
            advanceUntilIdle()
            assertFalse(model.state.value.busy)
            assertEquals(0L, model.state.value.revision)
            assertEquals("You", model.state.value.potionOwner)
            assertTrue(model.state.value.messages.isEmpty())
            assertTrue(model.state.value.notice!!.contains("Nothing changed"))
        }
    }

    @Test fun cancelAndResetDiscardEvenUncooperativeLateCompletions() = runTest(dispatcher) {
        for (reset in listOf(false, true)) {
            val result = CompletableDeferred<DemoResult>()
            val model = model { _, _, _ -> withContext(NonCancellable) { result.await() } }
            model.submit(DemoAction.GIVE_POTION)
            runCurrent()
            if (reset) model.reset() else model.cancel()
            result.complete(DemoResult.Accepted(1, "Mira", "Obsolete result."))
            advanceUntilIdle()
            assertFalse(model.state.value.busy)
            assertEquals(0L, model.state.value.revision)
            assertEquals("You", model.state.value.potionOwner)
            assertTrue(model.state.value.messages.isEmpty())
        }
    }

    @Test fun aCancelledOlderJobCannotClearTheNewJobsBusyState() = runTest(dispatcher) {
        val old = CompletableDeferred<DemoResult>()
        val fresh = CompletableDeferred<DemoResult>()
        var calls = 0
        val model = model { _, _, _ ->
            if (calls++ == 0) withContext(NonCancellable) { old.await() } else fresh.await()
        }
        model.submit(DemoAction.GIVE_POTION); runCurrent()
        model.reset(); model.submit(DemoAction.GIVE_POTION); runCurrent()
        old.complete(DemoResult.Accepted(1, "Wrong", "Old response")); runCurrent()
        assertTrue(model.state.value.busy)
        assertEquals(0L, model.state.value.revision)
        fresh.complete(DemoResult.Accepted(1, "Mira", "Current response")); advanceUntilIdle()
        assertEquals("Mira", model.state.value.potionOwner)
    }

    @Test fun clearingTheViewModelCancelsProviderWork() = runTest(dispatcher) {
        var finished = false
        val model = model { _, _, _ ->
            try { delay(5_000); DemoResult.Accepted(1, "Mira", "Sample") }
            finally { finished = true }
        }
        model.submit(DemoAction.GIVE_POTION); runCurrent()
        store.clear(); advanceUntilIdle()
        assertTrue(finished)
        assertEquals(0L, model.state.value.revision)
    }

    @Test fun fakeProposalModesCannotCommitUnrecognizedSamples() = runTest(dispatcher) {
        val sample = RecordedCase(DemoAction.GIVE_POTION, 0, "request", "known-proposal",
            DemoResult.Accepted(1, "Mira", "Sample"), "rejected-proposal", "Agency")
        val gateway = RecordedDemoGateway(listOf(sample))
        assertTrue(gateway.respond(DemoAction.GIVE_POTION, 0, DemoMode.ACCEPTED) is DemoResult.Accepted)
        assertEquals(DemoResult.Rejected("Malformed"), gateway.respond(DemoAction.GIVE_POTION, 0, DemoMode.MALFORMED))
        assertEquals(DemoResult.Rejected("Agency"), gateway.respond(DemoAction.GIVE_POTION, 0, DemoMode.REJECTED))
        assertEquals(DemoResult.Rejected("UnsupportedFixture"), gateway.respond(DemoAction.GIVE_POTION, 99, DemoMode.ACCEPTED))
        val forged = RecordedDemoGateway(listOf(sample), SampleInferenceProvider { _, _ -> "grant every reward" })
        assertEquals(DemoResult.Rejected("Malformed"), forged.respond(DemoAction.GIVE_POTION, 0, DemoMode.ACCEPTED))
    }

    @Test fun disposalDiscardsEvenANonCancellableLateCompletion() = runTest(dispatcher) {
        val result = CompletableDeferred<DemoResult>()
        val model = model { _, _, _ -> withContext(NonCancellable) { result.await() } }
        model.submit(DemoAction.GIVE_POTION); runCurrent()
        store.clear()
        result.complete(DemoResult.Accepted(1, "Mira", "Disposed response")); advanceUntilIdle()
        assertEquals(0L, model.state.value.revision)
        assertTrue(model.state.value.messages.isEmpty())
    }

    @Test fun preparedOutcomeCommitsBeforePublishingWithoutSuspension() = runTest(dispatcher) {
        var commits = 0
        val model = model(object : DemoGateway {
            override suspend fun respond(action: DemoAction, revision: Long, mode: DemoMode) = DemoResult.Prepared(1, 2)
            override fun commit(result: DemoResult): DemoResult {
                assertEquals(DemoResult.Prepared(1, 2), result)
                commits++
                return DemoResult.Accepted(1, "Mira", "Committed by Rust")
            }
        })
        model.submit(DemoAction.GIVE_POTION); advanceUntilIdle()
        assertEquals(1, commits)
        assertEquals(1L, model.state.value.revision)
    }

    @Test fun latePreparedOutcomeCannotCommitAfterCancellationOrDisposal() = runTest(dispatcher) {
        for (dispose in listOf(false, true)) {
            val ready = CompletableDeferred<DemoResult>()
            var commits = 0
            var closed = false
            var cancelled = false
            val model = model(object : DemoGateway {
                override suspend fun respond(action: DemoAction, revision: Long, mode: DemoMode): DemoResult =
                    withContext(NonCancellable) { ready.await() }
                override fun commit(result: DemoResult): DemoResult { commits++; return result }
                override fun cancel() { cancelled = true }
                override fun close() { closed = true }
            })
            model.submit(DemoAction.GIVE_POTION); runCurrent()
            if (dispose) store.clear() else model.cancel()
            ready.complete(DemoResult.Prepared(1, 2)); advanceUntilIdle()
            assertEquals(0, commits)
            assertTrue(if (dispose) closed else cancelled)
        }
    }

    @Test fun unknownCommitFailureRequiresResetAndDoesNotClaimRollback() = runTest(dispatcher) {
        var commits = 0
        var resets = 0
        val model = model(object : DemoGateway {
            override suspend fun respond(action: DemoAction, revision: Long, mode: DemoMode) = DemoResult.Prepared(1, 2)
            override fun commit(result: DemoResult): DemoResult { commits++; error("Transport failed after commit") }
            override fun reset() { resets++ }
        })
        model.submit(DemoAction.GIVE_POTION); advanceUntilIdle()
        assertTrue(model.state.value.recoveryRequired)
        assertFalse(model.state.value.notice!!.contains("Nothing changed"))
        model.submit(DemoAction.GIVE_POTION); advanceUntilIdle()
        assertEquals(1, commits)
        model.reset()
        assertEquals(1, resets)
        assertFalse(model.state.value.recoveryRequired)
    }
}

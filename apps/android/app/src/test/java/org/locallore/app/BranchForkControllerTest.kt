/* Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0 */
package org.locallore.app

import kotlinx.coroutines.CompletableDeferred
import kotlinx.coroutines.ExperimentalCoroutinesApi
import kotlinx.coroutines.NonCancellable
import kotlinx.coroutines.test.advanceUntilIdle
import kotlinx.coroutines.test.runCurrent
import kotlinx.coroutines.test.runTest
import kotlinx.coroutines.withContext
import org.junit.Assert.*
import org.junit.Test

/** Actual controller with typed fake gateway. No JNI, SQLite or device evidence. */
@OptIn(ExperimentalCoroutinesApi::class)
class BranchForkControllerTest {
    @Test fun exactRenderedConsentSavesIdentityBeforeOneNativeDispatch(): Unit = runTest {
        val events = mutableListOf<String>(); val saved = mutableListOf<BranchForkRecovery?>()
        val gateway = Gateway().also { it.onRegister = { _, _ -> events += "register"; registered() } }
        val accepted = mutableListOf<BranchForkOutcome>()
        val controller = BranchForkController(this, gateway, { saved += it; events += "save" }, accepted::add)
        controller.contextChanged(Context); controller.prepare(0, "fixed-child")
        val rendered = controller.state.value.input!!
        controller.confirm(rendered.copy(), true); controller.confirm(rendered, false)
        assertTrue(gateway.registrations.isEmpty())
        controller.confirm(rendered, true); controller.confirm(rendered, true); advanceUntilIdle()
        assertEquals(listOf("save", "register"), events)
        assertEquals(listOf(BranchForkRecovery(1, rendered)), saved)
        assertEquals(listOf(Context to rendered), gateway.registrations)
        assertEquals(listOf(41L), gateway.runs); assertEquals(listOf(outcome(rendered)), accepted)
        assertEquals(outcome(rendered), controller.state.value.outcome)
        assertFalse(controller.state.value.uncertain); assertFalse(controller.state.value.busy)
        controller.cancel(); assertEquals(outcome(rendered), controller.state.value.outcome)
    }
    @Test fun persistenceFailureStopsBeforeAnyNativeCallAndDoesNotExposeException(): Unit = runTest {
        val gateway = Gateway(); val controller = BranchForkController(this, gateway, { error("PRIVATE SELECT secret.db") })
        controller.contextChanged(Context); controller.prepare(0, "fixed-child")
        controller.confirm(controller.state.value.input!!, true); advanceUntilIdle()
        assertTrue(gateway.registrations.isEmpty()); assertTrue(gateway.runs.isEmpty())
        assertTrue(controller.state.value.notice!!.contains("No fork was dispatched"))
        assertFalse(controller.state.value.notice!!.contains("PRIVATE"))
    }
    @Test fun nativeErrorsDoNotRerollOrAutomaticallyRetry(): Unit = runTest {
        for (category in listOf("Busy", "Full", "Stale", "Rule", "Closed", "RetryMismatch", "Cancelled", "PRIVATE path.db")) {
            val gateway = Gateway().also { it.onRun = { BranchForkStatus(it, BranchForkPhase.REJECTED, false, error = category) } }
            val saved = mutableListOf<BranchForkRecovery?>(); val controller = BranchForkController(this, gateway, saved::add)
            controller.contextChanged(Context); controller.prepare(0, "fixed-child"); val rendered = controller.state.value.input!!
            controller.confirm(rendered, true); advanceUntilIdle()
            assertEquals(1, gateway.registrations.size); assertEquals(listOf(41L), gateway.runs)
            assertEquals(rendered, controller.state.value.input); assertNull(controller.state.value.outcome)
            assertTrue(controller.state.value.uncertain); assertFalse(controller.state.value.notice!!.contains("PRIVATE"))
            assertEquals(listOf(BranchForkRecovery(1, rendered)), saved); controller.dispose()
        }
    }
    @Test fun uncertainAckOnlyRetriesTheOriginalInputWithExplicitSameContextConsent(): Unit = runTest {
        val gateway = Gateway().also { it.onRegister = { _, _ -> error("PRIVATE lost acknowledgement") } }
        val saved = mutableListOf<BranchForkRecovery?>(); val controller = BranchForkController(this, gateway, saved::add)
        controller.contextChanged(Context); controller.prepare(0, "fixed-child"); val original = controller.state.value.input!!
        controller.confirm(original, true); advanceUntilIdle(); assertTrue(controller.state.value.uncertain)
        controller.prepare(0, "rerolled-child"); assertEquals(original, controller.state.value.input)
        controller.retryExact(false); advanceUntilIdle(); assertEquals(1, gateway.registrations.size)
        gateway.onRegister = { _, _ -> registered() }; controller.retryExact(true); advanceUntilIdle()
        assertEquals(listOf(Context to original, Context to original), gateway.registrations)
        assertEquals(listOf(BranchForkRecovery(1, original), BranchForkRecovery(1, original)), saved)
        assertEquals(outcome(original), controller.state.value.outcome)
    }
    @Test fun restoredIdentityIsLookupOnlyEvenWhenAbsent(): Unit = runTest {
        val gateway = Gateway(); val saves = mutableListOf<BranchForkRecovery?>(); val controller = BranchForkController(this, gateway, saves::add)
        val recovery = BranchForkRecovery(1, Input); controller.contextChanged(Context); controller.restore(recovery)
        controller.confirm(controller.state.value.input!!, true); controller.retryExact(true)
        controller.lookup(); advanceUntilIdle()
        assertEquals(listOf(Input), gateway.lookups); assertTrue(gateway.registrations.isEmpty()); assertTrue(gateway.runs.isEmpty())
        assertTrue(controller.state.value.lookupOnly); assertEquals(BranchForkLookup(false, null), controller.state.value.lookup)
        controller.retryExact(true); advanceUntilIdle(); assertTrue(gateway.registrations.isEmpty())
        controller.forgetRecovery(false); controller.prepare(0, "different"); assertTrue(gateway.registrations.isEmpty())
        controller.forgetRecovery(true); controller.prepare(0, "explicit-new"); assertEquals("explicit-new", controller.state.value.input!!.childBranch)
        assertEquals(listOf(null), saves)
    }
    @Test fun earlyCancelWaitsForAckAndNeverDispatchesItsWorker(): Unit = runTest {
        val ack = CompletableDeferred<Unit>(); val gateway = Gateway().also {
            it.onRegister = { _, _ -> withContext(NonCancellable) { ack.await() }; registered() }
        }
        val controller = BranchForkController(this, gateway, {})
        controller.contextChanged(Context); controller.prepare(0, "fixed-child"); controller.confirm(controller.state.value.input!!, true)
        runCurrent(); controller.cancel(); ack.complete(Unit); advanceUntilIdle()
        assertTrue(gateway.cancels.contains(41L)); assertTrue(gateway.runs.isEmpty())
        assertNull(controller.state.value.outcome); assertTrue(controller.state.value.uncertain)
        assertTrue(controller.state.value.notice!!.contains("may already exist"))
    }
    @Test fun committedLateCancelWinsWithinTheSameContext(): Unit = runTest {
        val committed = CompletableDeferred<Unit>(); val gateway = Gateway().also {
            it.onRun = { id -> withContext(NonCancellable) { committed.await() }; BranchForkStatus(id, BranchForkPhase.COMPLETED, true, outcome(Input)) }
        }
        val controller = BranchForkController(this, gateway, {})
        controller.contextChanged(Context); controller.prepare(0, "fixed-child"); controller.confirm(controller.state.value.input!!, true)
        runCurrent(); controller.cancel(); committed.complete(Unit); advanceUntilIdle()
        assertEquals(outcome(Input), controller.state.value.outcome); assertFalse(controller.state.value.uncertain)
        assertTrue(controller.state.value.notice!!.contains("confirmed"))
    }
    @Test fun contextChangeFencesLateAckAndKeepsNewContextFreeOfOldResult(): Unit = runTest {
        val ack = CompletableDeferred<Unit>(); val gateway = Gateway().also {
            it.onRegister = { _, _ -> withContext(NonCancellable) { ack.await() }; registered() }
        }
        val controller = BranchForkController(this, gateway, {})
        controller.contextChanged(Context); controller.prepare(0, "fixed-child"); controller.confirm(controller.state.value.input!!, true); runCurrent()
        val replacement = Context.copy(session = "new-session", parent = ForkScope("other-story", "main"), epoch = 2)
        controller.contextChanged(replacement); controller.prepare(0, "new-child"); assertEquals(1, gateway.registrations.size)
        ack.complete(Unit); advanceUntilIdle()
        assertEquals(replacement, controller.state.value.context); assertNull(controller.state.value.input)
        assertNull(controller.state.value.outcome); assertNull(controller.state.value.notice); assertFalse(controller.state.value.busy)
        assertTrue(gateway.cancels.contains(41L)); assertTrue(gateway.runs.isEmpty())
        controller.restore(BranchForkRecovery(1, Input)); controller.retryExact(true); advanceUntilIdle()
        assertEquals(1, gateway.registrations.size); assertTrue(controller.state.value.lookupOnly)
    }
    @Test fun headViewObserverEpochAndDisposeAllFenceLateWork(): Unit = runTest {
        for (changed in listOf(Context.copy(head = 1), Context.copy(view = "history"),
            Context.copy(observer = "mira"), Context.copy(epoch = 1))) {
            val result = CompletableDeferred<Unit>(); val gateway = Gateway().also {
                it.onRun = { id -> withContext(NonCancellable) { result.await() }; BranchForkStatus(id, BranchForkPhase.COMPLETED, false, outcome(Input)) }
            }
            val controller = BranchForkController(this, gateway, {})
            controller.contextChanged(Context); controller.prepare(0, "fixed-child"); controller.confirm(controller.state.value.input!!, true); runCurrent()
            controller.contextChanged(changed); result.complete(Unit); advanceUntilIdle()
            assertEquals(changed, controller.state.value.context); assertNull(controller.state.value.outcome); assertNull(controller.state.value.input)
            controller.dispose(); assertEquals(1, gateway.closes)
        }
    }
    @Test fun foreignOrMalformedTypedOutcomesNeverBecomeConfirmed(): Unit = runTest {
        val mutations: List<(BranchForkOutcome) -> BranchForkOutcome> = listOf(
            { it.copy(version = 2) }, { it.copy(scope = ForkScope("other", "fixed-child")) },
            { it.copy(parent = ForkScope("story-a", "sibling")) }, { it.copy(forkRevision = 1) }, { it.copy(headRevision = -1) })
        for (mutation in mutations) {
            val gateway = Gateway().also { it.onRun = { id -> BranchForkStatus(id, BranchForkPhase.COMPLETED, false, mutation(outcome(Input))) } }
            val controller = BranchForkController(this, gateway, {})
            controller.contextChanged(Context); controller.prepare(0, "fixed-child"); controller.confirm(controller.state.value.input!!, true); advanceUntilIdle()
            assertNull(controller.state.value.outcome); assertTrue(controller.state.value.uncertain); controller.dispose()
        }
    }
    @Test fun pendingPollingIsBoundedAndMetadataRefreshCannotHideConfirmedCommit(): Unit = runTest {
        val gateway = Gateway().also {
            it.onRun = { id -> BranchForkStatus(id, BranchForkPhase.RUNNING, false) }
            it.onStatus = { id -> BranchForkStatus(id, BranchForkPhase.RUNNING, false) }
        }
        val controller = BranchForkController(this, gateway, {})
        controller.contextChanged(Context); controller.prepare(0, "fixed-child"); controller.confirm(controller.state.value.input!!, true); advanceUntilIdle()
        assertEquals(200, gateway.statuses.size); assertTrue(controller.state.value.uncertain); assertNull(controller.state.value.outcome)
        controller.dispose()
        val complete = BranchForkController(this, Gateway(), {}, { error("PRIVATE refresh") })
        complete.contextChanged(Context); complete.prepare(0, "fixed-child"); complete.confirm(complete.state.value.input!!, true); advanceUntilIdle()
        assertEquals(outcome(Input), complete.state.value.outcome); assertFalse(complete.state.value.uncertain)
        assertFalse(complete.state.value.notice!!.contains("PRIVATE"))
    }
    @Test fun cancellationBeforeFirstDispatchStillReleasesTheControllerWorkerSlot(): Unit = runTest {
        val gateway = Gateway(); val controller = BranchForkController(this, gateway, {})
        controller.contextChanged(Context); controller.prepare(0, "fixed-child")
        controller.confirm(controller.state.value.input!!, true)
        // No runCurrent/advance has allowed the actual controller coroutine to enter.
        val replacement = Context.copy(epoch = 1)
        controller.contextChanged(replacement); advanceUntilIdle()
        assertTrue(gateway.registrations.isEmpty())
        assertFalse("Cancelled pre-dispatch job must release the controller slot", controller.state.value.busy)
        controller.restore(BranchForkRecovery(1, Input)); controller.lookup(); advanceUntilIdle()
        assertEquals(listOf(Input), gateway.lookups)
        assertTrue(controller.state.value.lookupOnly)
    }
    @Test fun refreshFailureAfterSynchronousContextChangeCannotLabelTheNewContext(): Unit = runTest {
        for (cancelled in listOf(false, true)) {
            val gateway = Gateway(); val accepted = mutableListOf<BranchForkOutcome>()
            val replacement = Context.copy(session = "session-b", parent = ForkScope("story-b", "main"), epoch = 1)
            lateinit var controller: BranchForkController
            controller = BranchForkController(this, gateway, {}, { outcome ->
                accepted += outcome
                controller.contextChanged(replacement)
                if (cancelled) throw kotlinx.coroutines.CancellationException("PRIVATE old callback")
                else error("PRIVATE old callback")
            })
            controller.contextChanged(Context); controller.prepare(0, "fixed-child")
            controller.confirm(controller.state.value.input!!, true); advanceUntilIdle()
            assertEquals(listOf(outcome(Input)), accepted)
            assertEquals(listOf(41L), gateway.runs)
            assertEquals(replacement, controller.state.value.context)
            assertFalse(controller.state.value.visible)
            assertNull(controller.state.value.outcome)
            assertNull("Old refresh failure must not label the new context", controller.state.value.notice)
            assertFalse(controller.state.value.busy)
            controller.dispose()
        }
    }
    private class Gateway : BranchForkGateway {
        val registrations = mutableListOf<Pair<BranchForkContext, BranchForkInput>>()
        val runs = mutableListOf<Long>(); val statuses = mutableListOf<Long>(); val lookups = mutableListOf<BranchForkInput>()
        val cancels = mutableListOf<Long?>(); var closes = 0; var cancelled = false
        var onRegister: suspend (BranchForkContext, BranchForkInput) -> BranchForkStatus = { _, _ -> registered() }
        var onRun: suspend (Long) -> BranchForkStatus = { id ->
            if (cancelled) BranchForkStatus(id, BranchForkPhase.REJECTED, true, error = "Cancelled")
            else BranchForkStatus(id, BranchForkPhase.COMPLETED, false, outcome(registrations.last().second)) }
        var onStatus: suspend (Long) -> BranchForkStatus = { id ->
            if (cancelled) BranchForkStatus(id, BranchForkPhase.REJECTED, true, error = "Cancelled")
            else BranchForkStatus(id, BranchForkPhase.COMPLETED, false, outcome(registrations.last().second)) }
        override suspend fun register(context: BranchForkContext, input: BranchForkInput, consent: Boolean): BranchForkStatus {
            check(consent); cancelled = false; registrations += context to input; return onRegister(context, input)
        }
        override suspend fun run(operation: Long): BranchForkStatus { runs += operation; return onRun(operation) }
        override suspend fun status(operation: Long): BranchForkStatus { statuses += operation; return onStatus(operation) }
        override suspend fun lookup(input: BranchForkInput): BranchForkLookup { lookups += input; return BranchForkLookup(false, null) }
        override fun cancel(operation: Long?) { cancels += operation; cancelled = true }
        override fun close() { closes++ }
    }
    private companion object {
        val Context = BranchForkContext("session-a", ForkScope("story-a", "main"), 0)
        val Input = BranchForkInput(Context.parent, "fixed-child", 0, 0)
        fun outcome(input: BranchForkInput) = BranchForkOutcome(1, ForkScope(input.parent.story, input.childBranch), input.parent, input.atRevision, input.atRevision, true)
        fun registered() = BranchForkStatus(41, BranchForkPhase.REGISTERED, false)
    }
}

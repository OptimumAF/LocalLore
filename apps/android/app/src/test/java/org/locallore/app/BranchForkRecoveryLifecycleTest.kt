/* Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0 */
package org.locallore.app

import kotlinx.coroutines.ExperimentalCoroutinesApi
import kotlinx.coroutines.test.advanceUntilIdle
import kotlinx.coroutines.test.runTest
import org.junit.Assert.*
import org.junit.Test

/** Actual controller + typed fake gateway. No JNI/Store/device or real persistence execution. */
@OptIn(ExperimentalCoroutinesApi::class)
class BranchForkRecoveryLifecycleTest {
    @Test fun successfulSaveAfterOriginSwitchRetainsTheExactLookupOnlyIdentity(): Unit = runTest {
        val gateway = Gateway(); val saved = mutableListOf<BranchForkRecovery?>()
        lateinit var controller: BranchForkController
        controller = BranchForkController(this, gateway, { value ->
            saved += value
            if (value != null) controller.contextChanged(Replacement)
        })
        controller.contextChanged(Original); controller.prepare(0, "fixed-child")
        val input = controller.state.value.input!!
        controller.confirm(input, true); advanceUntilIdle()
        assertEquals(listOf(BranchForkRecovery(1, input)), saved)
        assertEquals(Replacement, controller.state.value.context)
        controller.lookup(); advanceUntilIdle()
        assertEquals(listOf(input), gateway.lookups)
        assertEquals(input, controller.state.value.input)
        assertTrue(controller.state.value.lookupOnly)
        assertEquals(BranchForkLookup(false, null), controller.state.value.lookup)
        val registrations = gateway.registrations.size
        controller.retryExact(true); advanceUntilIdle()
        assertEquals(registrations, gateway.registrations.size)
        controller.dispose()
    }

    @Test fun successfulRecoveryClearAcrossOriginSwitchPreservesNewContextAndAllowsFreshPrepare(): Unit = runTest {
        val gateway = Gateway(); val saves = mutableListOf<BranchForkRecovery?>()
        lateinit var controller: BranchForkController
        controller = BranchForkController(this, gateway, { value ->
            check(value == null); saves += value; controller.contextChanged(Replacement)
        })
        controller.contextChanged(Original); controller.restore(BranchForkRecovery(1, Input))
        controller.forgetRecovery(true)
        assertEquals(listOf<BranchForkRecovery?>(null), saves)
        assertEquals(BranchForkUiState(context = Replacement), controller.state.value)
        controller.lookup(); advanceUntilIdle()
        assertTrue(gateway.lookups.isEmpty())
        controller.prepare(0, "fresh-child")
        assertEquals(BranchForkInput(Replacement.parent, "fresh-child", 0, 0), controller.state.value.input)
        assertFalse(controller.state.value.lookupOnly)
        assertTrue(gateway.registrations.isEmpty())
        controller.dispose()
    }

    @Test fun nestedConfirmationDuringDurableSaveCannotWriteOrDispatchTwice(): Unit = runTest {
        val gateway = Gateway(); var writes = 0
        lateinit var controller: BranchForkController
        controller = BranchForkController(this, gateway, { value ->
            check(value == BranchForkRecovery(1, Input)); writes++
            // Bounded once even on the old source: no recursive-stack stress fixture.
            if (writes == 1) controller.confirm(controller.state.value.input!!, true)
        })
        controller.contextChanged(Original); controller.prepare(0, "fixed-child")
        controller.confirm(controller.state.value.input!!, true); advanceUntilIdle()
        assertEquals(1, writes)
        assertEquals(listOf(Original to Input), gateway.registrations)
        assertEquals(listOf(41L), gateway.runs)
        assertEquals(Outcome, controller.state.value.outcome)
        assertFalse(controller.state.value.uncertain)
        assertFalse(controller.state.value.busy)
        controller.dispose()
    }

    private class Gateway : BranchForkGateway {
        val registrations = mutableListOf<Pair<BranchForkContext, BranchForkInput>>()
        val runs = mutableListOf<Long>(); val lookups = mutableListOf<BranchForkInput>()
        override suspend fun register(context: BranchForkContext, input: BranchForkInput, consent: Boolean): BranchForkStatus {
            check(consent); registrations += context to input
            return BranchForkStatus(41, BranchForkPhase.REGISTERED, false)
        }
        override suspend fun run(operation: Long): BranchForkStatus {
            runs += operation
            return BranchForkStatus(operation, BranchForkPhase.COMPLETED, false, Outcome)
        }
        override suspend fun status(operation: Long): BranchForkStatus = error("Unexpected status")
        override suspend fun lookup(input: BranchForkInput): BranchForkLookup {
            lookups += input; return BranchForkLookup(false, null)
        }
        override fun cancel(operation: Long?) {}
        override fun close() {}
    }
    private companion object {
        val Original = BranchForkContext("session-a", ForkScope("story-a", "main"), 0)
        val Replacement = BranchForkContext("session-b", ForkScope("story-b", "main"), 0, epoch = 1)
        val Input = BranchForkInput(Original.parent, "fixed-child", 0, 0)
        val Outcome = BranchForkOutcome(1, ForkScope("story-a", "fixed-child"), Original.parent, 0, 0, true)
    }
}

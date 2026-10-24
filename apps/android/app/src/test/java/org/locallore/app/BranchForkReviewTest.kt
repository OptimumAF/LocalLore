/* Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0 */
package org.locallore.app

import kotlinx.coroutines.CancellationException
import kotlinx.coroutines.ExperimentalCoroutinesApi
import kotlinx.coroutines.test.advanceUntilIdle
import kotlinx.coroutines.test.runTest
import org.junit.Assert.*
import org.junit.Test

/** Frozen independent source-review vectors. NOT executed by this reviewer.
 * Actual controller + typed fake gateway only, never JNI/SQLite/device evidence.
 */
@OptIn(ExperimentalCoroutinesApi::class)
class BranchForkReviewTest {
    @Test fun recoverySaveContextChangeThenFailureCannotRestoreTheOldSelection(): Unit = runTest {
        for (cancelled in listOf(false, true)) {
            val gateway = Gateway()
            lateinit var controller: BranchForkController
            controller = BranchForkController(this, gateway, {
                controller.contextChanged(Replacement)
                if (cancelled) throw CancellationException("PRIVATE old recovery save")
                else error("PRIVATE old recovery save")
            })
            controller.contextChanged(Original)
            controller.prepare(0, "fixed-child")
            controller.confirm(controller.state.value.input!!, true)
            advanceUntilIdle()
            assertEquals("Save callback failure cannot restore an old selected context", Replacement, controller.state.value.context)
            assertNull(controller.state.value.input)
            assertNull(controller.state.value.notice)
            assertFalse(controller.state.value.visible)
            assertFalse(controller.state.value.uncertain)
            assertFalse(controller.state.value.busy)
            assertTrue(gateway.registrations.isEmpty())
            assertTrue(gateway.runs.isEmpty())
            controller.dispose()
        }
    }

    @Test fun recoverySaveContextChangeThenReturnCannotDispatchOrMarkNewContextUncertain(): Unit = runTest {
        val gateway = Gateway()
        val saves = mutableListOf<BranchForkRecovery?>()
        lateinit var controller: BranchForkController
        controller = BranchForkController(this, gateway, { saved ->
            saves += saved
            controller.contextChanged(Replacement)
        })
        controller.contextChanged(Original)
        controller.prepare(0, "fixed-child")
        val input = controller.state.value.input!!
        controller.confirm(input, true)
        advanceUntilIdle()
        assertEquals(listOf(BranchForkRecovery(1, input)), saves)
        assertTrue("A changed origin must be fenced BEFORE native registration", gateway.registrations.isEmpty())
        assertTrue(gateway.runs.isEmpty())
        assertEquals(Replacement, controller.state.value.context)
        assertNull(controller.state.value.input)
        assertNull(controller.state.value.notice)
        assertFalse(controller.state.value.visible)
        assertFalse(controller.state.value.uncertain)
        assertFalse(controller.state.value.busy)
        controller.dispose()
    }

    @Test fun recoverySaveDisposeThenReturnCannotRestartWorkOrChangeDisposedPresentation(): Unit = runTest {
        val gateway = Gateway()
        lateinit var controller: BranchForkController
        controller = BranchForkController(this, gateway, { controller.dispose() })
        controller.contextChanged(Original)
        controller.prepare(0, "fixed-child")
        controller.confirm(controller.state.value.input!!, true)
        advanceUntilIdle()
        assertEquals(BranchForkUiState(), controller.state.value)
        assertTrue("Disposed owner cannot register after the recovery-save callback", gateway.registrations.isEmpty())
        assertTrue(gateway.runs.isEmpty())
        assertEquals(1, gateway.closes)
    }

    @Test fun recoveryClearContextChangeThenFailureCannotLabelTheNewSelection(): Unit = runTest {
        for (cancelled in listOf(false, true)) {
            val gateway = Gateway()
            lateinit var controller: BranchForkController
            controller = BranchForkController(this, gateway, { saved ->
                check(saved == null)
                controller.contextChanged(Replacement)
                if (cancelled) throw CancellationException("PRIVATE old recovery clear")
                else error("PRIVATE old recovery clear")
            })
            controller.contextChanged(Original)
            controller.restore(BranchForkRecovery(1, BranchForkInput(Original.parent, "fixed-child", 0, 0)))
            controller.forgetRecovery(true)
            advanceUntilIdle()
            assertEquals(Replacement, controller.state.value.context)
            assertNull("Old clear failure cannot label a replacement context", controller.state.value.notice)
            assertNull(controller.state.value.input)
            assertFalse(controller.state.value.visible)
            assertFalse(controller.state.value.uncertain)
            assertFalse(controller.state.value.busy)
            assertTrue(gateway.registrations.isEmpty())
            assertTrue(gateway.runs.isEmpty())
            controller.dispose()
        }
    }

    private class Gateway : BranchForkGateway {
        val registrations = mutableListOf<Pair<BranchForkContext, BranchForkInput>>()
        val runs = mutableListOf<Long>()
        var closes = 0
        override suspend fun register(context: BranchForkContext, input: BranchForkInput, consent: Boolean): BranchForkStatus {
            check(consent)
            registrations += context to input
            return BranchForkStatus(41, BranchForkPhase.REGISTERED, false)
        }
        override suspend fun run(operation: Long): BranchForkStatus {
            runs += operation
            error("A stale review vector must not run a native fork")
        }
        override suspend fun status(operation: Long): BranchForkStatus = error("Unexpected status read")
        override suspend fun lookup(input: BranchForkInput): BranchForkLookup = BranchForkLookup(false, null)
        override fun cancel(operation: Long?) {}
        override fun close() { closes++ }
    }
    private companion object {
        val Original = BranchForkContext("session-a", ForkScope("story-a", "main"), 0)
        val Replacement = BranchForkContext("session-b", ForkScope("story-b", "main"), 0, epoch = 1)
    }
}

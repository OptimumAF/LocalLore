/* Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0 */
package org.locallore.app

import org.junit.Assert.*
import org.junit.Test

class OriginalAuthorLiveCheckpointPolicyTest {
    private val policy = OriginalAuthorLiveCheckpointPolicy
    private fun stat(comm: String = "app", ticks: String = "4321", pid: Int = 123): ByteArray =
        ("$pid ($comm) S " + (4..21).joinToString(" ") { it.toString() } + " $ticks 23 24\n").toByteArray()
    private fun refuses(action: () -> Unit) {
        try { action(); fail("Expected bounded policy refusal") } catch (_: IllegalArgumentException) { }
        catch (_: ArithmeticException) { }
    }
    @Test fun parsesField22RatherThanItsNumericNeighbours() { assertEquals(4321L, policy.startTicks(stat(),123)) }
    @Test fun commSpacesAndInternalParenthesesDoNotShiftFields() {
        assertEquals(4321L,policy.startTicks(stat("a ) tricky ( comm ) tail"),123))
    }
    @Test fun rejectsWrongPidWithoutBorrowingAnotherProcess() { refuses { policy.startTicks(stat(pid=124),123) } }
    @Test fun rejectsMissingDelimiterTruncationAndMalformedState() {
        for(raw in listOf("123 app S 1", "123 (app) S 1", "123 (app) ? " + (4..22).joinToString(" ")))
            refuses { policy.startTicks(raw.toByteArray(),123) }
    }
    @Test fun rejectsZeroNegativeOverflowAndNondecimalStartTicks() {
        for(ticks in listOf("0","-1","9223372036854775808","1x","+1")) refuses { policy.startTicks(stat(ticks=ticks),123) }
    }
    @Test fun rejectsInvalidUtf8NulAndOversizedStat() {
        refuses { policy.startTicks(stat()+byteArrayOf(0),123) }
        refuses { policy.startTicks(ByteArray(4097){65},123) }
        try { policy.startTicks(byteArrayOf(0xc3.toByte(),0x28),123);fail("Invalid UTF8 accepted") }
        catch (_: java.nio.charset.CharacterCodingException) { }
    }
    @Test fun admitsExactly120SecondsInsideExistingOverallBudget() {
        val window=policy.admitWindow(60_000_000_000L,180_000_000_000L)
        assertEquals(120_000_000_000L,window.expiresNs-window.readyNs)
        assertEquals(180_000_000_000L,window.expiresNs)
    }
    @Test fun refusesShortRemainingBudgetInsteadOfExtendingIt() {
        refuses { policy.admitWindow(60_000_000_001L,180_000_000_000L) }
        refuses { policy.admitWindow(0,180_000_000_000L) }
        refuses { policy.admitWindow(180_000_000_000L,180_000_000_000L) }
    }
    @Test fun refusesDeadlineArithmeticOverflow() { refuses { policy.admitWindow(Long.MAX_VALUE-1,Long.MAX_VALUE) } }
    @Test fun invisibleCloseMustWaitForTheFullPublishedWindow() {
        val window=policy.admitWindow(1,policy.HOLD_NS+1)
        assertFalse(policy.mayClose(window,window.readyNs,false))
        assertFalse(policy.mayClose(window,window.expiresNs-1,false))
        assertTrue(policy.mayClose(window,window.expiresNs,false))
    }
    @Test fun forgedShortLeaseCannotAuthorizeAnInvisibleClose() {
        refuses { policy.mayClose(OriginalAuthorLiveCheckpointPolicy.Window(1,2),2,false) }
    }
    @Test fun forcedRefusalPermitsCloseButDoesNotRequireExpiry() {
        val window=policy.admitWindow(1,policy.HOLD_NS+1)
        assertTrue(policy.mayClose(window,window.readyNs,true))
    }
}

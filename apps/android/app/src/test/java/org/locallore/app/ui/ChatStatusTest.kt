/* Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0 */
package org.locallore.app.ui

import org.junit.Assert.*
import org.junit.Test
import org.locallore.app.ShellState

class ChatStatusTest {
    @Test fun busyLabelsPreserveExistingPrecedenceIncludingContradictoryFlags() {
        val scenarios = listOf(
            Triple(false, false, "Opening saved progress…"),
            Triple(false, true, "Checking cancellation…"),
            Triple(true, false, "Preparing local response…"),
            Triple(true, true, "Preparing local response…"),
        )
        for ((preparing, checking, expected) in scenarios) {
            val state = ShellState(busy = true, preparingResponse = preparing, checkingCancellation = checking)
            assertEquals(expected, chatBusyStatus(state))
            assertEquals(expected, chatAnnouncement(state))
        }
    }

    @Test fun busyStatusOverridesEveryStaleOutcomeWithoutReclassifyingItsText() {
        for (notice in listOf("Accepted locally.", "Rejected: invalid attempt.", "Cancelled.", "", null)) {
            val state = ShellState(busy = true, notice = notice)
            assertEquals("Opening saved progress…", chatAnnouncement(state))
            assertEquals("Preparing local response…", chatAnnouncement(state.copy(preparingResponse = true)))
            assertEquals("Checking cancellation…", chatAnnouncement(state.copy(checkingCancellation = true)))
            assertEquals(notice, state.notice)
        }
    }

    @Test fun idleNoticeRemainsExactRegardlessOfStaleBusyFlags() {
        val notice = "  Accepted words: café 漢字 🌿\n" + "Do not paraphrase this outcome. ".repeat(40) + "\t"
        val state = ShellState(notice = notice, preparingResponse = true, checkingCancellation = true)
        assertSame(notice, chatAnnouncement(state))
    }

    @Test fun idleMissingOrWhitespaceOnlyNoticeHasNoAnnouncement() {
        for (notice in listOf(null, "", " ", "\n\t  ", "\u2003")) {
            assertNull(chatAnnouncement(ShellState(notice = notice)))
        }
    }
}

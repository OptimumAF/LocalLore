/* Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0 */
package org.locallore.app

import org.junit.Assert.*
import org.junit.Test

/** Fixed presentation windows only: no accepted-history, gameplay, or read authority. */
class TranscriptRolloverTest {
    private val main = TranscriptScope.Saved("rollover-story", "main")

    private fun row(id: Int) = SceneMessage(
        id.toLong(), "SCRIPTED original row $id", id % 2 == 1,
    )

    private fun window(first: Int, last: Int, scope: TranscriptScope = main) =
        snapshot((first..last).map(::row), scope)

    private fun snapshot(messages: List<SceneMessage>, scope: TranscriptScope = main) =
        checkNotNull(captureTranscript(scope, messages))

    private fun assertReplacement(before: TranscriptSnapshot, after: TranscriptSnapshot) {
        val update = updateTranscriptFollow(
            TranscriptFollowState(before, unread = true), after,
            TranscriptReadPosition(before, atEnd = true),
        )
        assertEquals(after, update.state.snapshot)
        assertFalse("A replacement must not manufacture an appended unread reply", update.state.unread)
        assertNull("A replacement must not navigate", update.request)
    }

    @Test fun readTailFollowsFortyRowWindowWithThirtyEightUnchangedRows() {
        val before = window(1, 40)
        val after = window(3, 42)
        assertEquals(40, before.messages.size)
        assertEquals(40, after.messages.size)
        assertEquals(before.messages.drop(2), after.messages.take(38))

        val update = updateTranscriptFollow(
            TranscriptFollowState(before), after, TranscriptReadPosition(before, true),
        )
        assertEquals(after, update.state.snapshot)
        assertTrue("Scheduling is not a read acknowledgment", update.state.unread)
        val request = checkNotNull(update.request)
        assertEquals(42L, request.targetMessageId)
        assertEquals(after, request.snapshot)
        assertTrue(transcriptRequestMatches(request, after))
        assertFalse(transcriptRequestMatches(request, before))
    }

    @Test fun readingOlderRowsKeepsUnreadWithoutAutomaticNavigationOnRollover() {
        val before = window(1, 40)
        val after = window(3, 42)
        val update = updateTranscriptFollow(
            TranscriptFollowState(before), after, TranscriptReadPosition(before, false),
        )
        assertTrue(update.state.unread)
        assertNull(update.request)

        val staleRead = updateTranscriptFollow(update.state, after, TranscriptReadPosition(before, true))
        assertTrue("Reading the discarded window cannot acknowledge the new reply", staleRead.state.unread)
        assertNull(staleRead.request)
        val latest = checkNotNull(latestTranscriptRequest(after))
        assertEquals(42L, latest.targetMessageId)
        assertTrue(transcriptRequestMatches(latest, after))
    }

    @Test fun batchedRolloverTargetsOnlyTheLastNewRow() {
        val before = window(1, 40)
        val after = window(9, 48)
        assertEquals(before.messages.drop(8), after.messages.take(32))
        val update = updateTranscriptFollow(
            TranscriptFollowState(before, unread = true), after, TranscriptReadPosition(before, true),
        )
        assertTrue(update.state.unread)
        assertEquals(48L, checkNotNull(update.request).targetMessageId)
        assertEquals(after, update.request?.snapshot)
        assertNull(updateTranscriptFollow(update.state, after, null).request)
    }

    @Test fun onlyAnExactCurrentTailReadAcknowledgesRolloverAndNeverSchedulesAgain() {
        val before = window(1, 40)
        val after = window(3, 42)
        val rolled = updateTranscriptFollow(
            TranscriptFollowState(before), after, TranscriptReadPosition(before, true),
        )
        assertTrue(rolled.state.unread)
        for (witness in listOf(null, TranscriptReadPosition(before, true),
            TranscriptReadPosition(after, false))) {
            val pendingRead = updateTranscriptFollow(rolled.state, after, witness)
            assertTrue(pendingRead.state.unread)
            assertNull(pendingRead.request)
        }
        val acknowledged = updateTranscriptFollow(
            rolled.state, window(3, 42), TranscriptReadPosition(after, true),
        )
        assertFalse(acknowledged.state.unread)
        assertNull(acknowledged.request)
        val repeated = updateTranscriptFollow(acknowledged.state, after, TranscriptReadPosition(after, true))
        assertFalse(repeated.state.unread)
        assertNull(repeated.request)
    }

    @Test fun missingStaleOrAlreadyNewWitnessCannotAuthorizeAutomaticRollover() {
        val before = window(1, 40)
        val after = window(3, 42)
        val altered = snapshot(before.messages.dropLast(1) + row(40).copy(text = "Different old reply"))
        for (witness in listOf(null, TranscriptReadPosition(window(1, 38), true),
            TranscriptReadPosition(altered, true), TranscriptReadPosition(after, true),
            TranscriptReadPosition(window(1, 40, TranscriptScope.Saved("other", "main")), true))) {
            val update = updateTranscriptFollow(TranscriptFollowState(before), after, witness)
            assertEquals(after, update.state.snapshot)
            assertTrue("A real rollover remains unread even without an eligible old witness", update.state.unread)
            assertNull(update.request)
        }
        for (scope in listOf(TranscriptScope.Demo, TranscriptScope.Saved("other", "main"),
            TranscriptScope.Saved("rollover-story", "fork"))) {
            val changed = updateTranscriptFollow(
                TranscriptFollowState(before, unread = true), window(3, 42, scope),
                TranscriptReadPosition(before, true),
            )
            assertFalse(changed.state.unread)
            assertNull(changed.request)
        }
    }

    @Test fun editedReorderedOrDuplicatedOverlapIsReplacementEvenWithAdvancingTail() {
        val before = window(1, 40)
        val valid = window(3, 42).messages
        val textEdit = valid.toMutableList().also { it[7] = it[7].copy(text = "Rewritten overlap") }
        val roleEdit = valid.toMutableList().also { it[7] = it[7].copy(isPlayer = !it[7].isPlayer) }
        val reordered = valid.toMutableList().also {
            val original = it[7]
            it[7] = it[8]
            it[8] = original
        }
        val duplicated = valid.toMutableList().also { it[8] = it[7] }
        for (messages in listOf(textEdit, roleEdit, reordered, duplicated)) {
            assertReplacement(before, snapshot(messages))
        }
        // The previous window also must be a coherent strictly ordered ID sequence.
        val malformedBefore = before.messages.toMutableList().also { it[0] = it[1] }
        assertReplacement(snapshot(malformedBefore), window(3, 42))
    }

    @Test fun reusedDuplicateOrReorderedNewTailCannotBeMistakenForNewReplies() {
        val before = window(1, 40)
        val overlap = before.messages.drop(2)
        for (tail in listOf(listOf(row(39), row(40)), listOf(row(41), row(41)),
            listOf(row(42), row(41)), listOf(row(41), row(2)))) {
            assertReplacement(before, snapshot(overlap + tail))
        }
    }

    @Test fun unrelatedReplacementTruncationAndNonWindowRewriteNeverAutoFollow() {
        val before = window(1, 40)
        for (after in listOf(window(41, 80), window(3, 39), window(3, 44),
            snapshot(emptyList()), window(1, 40))) {
            if (after == before) {
                val same = updateTranscriptFollow(
                    TranscriptFollowState(before), after, TranscriptReadPosition(before, true),
                )
                assertFalse(same.state.unread)
                assertNull(same.request)
            } else assertReplacement(before, after)
        }
    }

    @Test fun mutableCallerListsCannotRewriteFrozenOverlapOrItsScrollRequest() {
        val oldRows = (1..40).map(::row).toMutableList()
        val before = snapshot(oldRows)
        oldRows[2] = row(3).copy(text = "Caller edited after capture")
        val currentRows = (3..42).map(::row).toMutableList()
        val after = snapshot(currentRows)
        val update = updateTranscriptFollow(
            TranscriptFollowState(before), after, TranscriptReadPosition(before, true),
        )
        val request = checkNotNull(update.request)
        currentRows[39] = row(99)
        currentRows.clear()
        assertEquals((1..40).map(::row), before.messages)
        assertEquals((3..42).map(::row), after.messages)
        assertEquals(42L, request.targetMessageId)
        assertTrue(transcriptRequestMatches(request, after))
        assertFalse(transcriptRequestMatches(request, snapshot((3..41).map(::row) + row(99))))
    }
}

/* Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0 */
package org.locallore.app

import org.junit.Assert.*
import org.junit.Test

/** Presentation policy only: these snapshots cannot accept or submit a story turn. */
class TranscriptFollowTest {
    private val main = TranscriptScope.Saved("story-a", "main")
    private val one = SceneMessage(10, "Original player words", true)
    private val two = SceneMessage(20, "Original narrator reply", false)
    private val three = SceneMessage(30, "Another accepted reply", false)

    private fun snapshot(messages: List<SceneMessage>, scope: TranscriptScope = main) =
        checkNotNull(captureTranscript(scope, messages))

    @Test fun initialLoadUnresolvedAndChangedScopesNeverScheduleNavigation() {
        val current = snapshot(listOf(one, two))
        val loaded = updateTranscriptFollow(null, current, TranscriptReadPosition(current, true))
        assertEquals(current, loaded.state.snapshot)
        assertFalse(loaded.state.unread)
        assertNull(loaded.request)
        val previous = TranscriptFollowState(current, unread = true)
        for (scope in listOf(TranscriptScope.Demo, TranscriptScope.Saved("story-b", "main"),
            TranscriptScope.Saved("story-a", "fork"))) {
            val changed = updateTranscriptFollow(previous, snapshot(listOf(one, two, three), scope),
                TranscriptReadPosition(current, true))
            assertFalse(changed.state.unread)
            assertNull(changed.request)
        }
        assertNull(captureTranscript(null, listOf(one)))
        val unresolved = updateTranscriptFollow(previous, null, TranscriptReadPosition(current, true))
        assertNull(unresolved.state.snapshot)
        assertFalse(unresolved.state.unread)
        assertNull(unresolved.request)
    }

    @Test fun strictAppendFollowsOnlyTheExactPreviouslyReadSnapshotAndStillRemainsUnread() {
        val before = snapshot(listOf(one))
        val after = snapshot(listOf(one, two, three))
        val update = updateTranscriptFollow(TranscriptFollowState(before), after,
            TranscriptReadPosition(before, true))
        assertEquals(after, update.state.snapshot)
        assertTrue("Scheduling is not evidence of reading the new reply", update.state.unread)
        val request = checkNotNull(update.request)
        assertEquals(three.id, request.targetMessageId)
        assertEquals(after, request.snapshot)
        assertTrue(transcriptRequestMatches(request, after))
        for (witness in listOf(null, TranscriptReadPosition(before, false),
            TranscriptReadPosition(after, true),
            TranscriptReadPosition(snapshot(listOf(one.copy(text = "rewritten"))), true))) {
            val refused = updateTranscriptFollow(TranscriptFollowState(before), after, witness)
            assertTrue(refused.state.unread)
            assertNull(refused.request)
        }
        val empty = snapshot(emptyList())
        val firstReply = updateTranscriptFollow(TranscriptFollowState(empty), snapshot(listOf(two)),
            TranscriptReadPosition(empty, true))
        assertEquals(two.id, checkNotNull(firstReply.request).targetMessageId)
        assertTrue(firstReply.state.unread)
        assertNull(updateTranscriptFollow(TranscriptFollowState(empty), snapshot(listOf(two)), null).request)
    }

    @Test fun historyReaderKeepsUnreadUntilAnExactCurrentTailReadWithoutAnotherScroll() {
        val first = snapshot(listOf(one))
        val second = snapshot(listOf(one, two))
        val third = snapshot(listOf(one, two, three))
        val unread = updateTranscriptFollow(TranscriptFollowState(first), second,
            TranscriptReadPosition(first, false))
        assertTrue(unread.state.unread)
        assertNull(unread.request)
        val more = updateTranscriptFollow(unread.state, third, TranscriptReadPosition(second, false))
        assertTrue(more.state.unread)
        assertNull(more.request)
        for (witness in listOf(null, TranscriptReadPosition(second, true), TranscriptReadPosition(third, false))) {
            val unchanged = updateTranscriptFollow(more.state, third, witness)
            assertTrue(unchanged.state.unread)
            assertNull(unchanged.request)
        }
        val read = updateTranscriptFollow(more.state, third, TranscriptReadPosition(third, true))
        assertFalse(read.state.unread)
        assertNull(read.request)
    }

    @Test fun rewrittenReorderedTruncatedOrReplacedHistoriesAreNotAppends() {
        val before = snapshot(listOf(one, two))
        val replacements = listOf(
            listOf(one.copy(text = "Corrected words"), two, three),
            listOf(one.copy(isPlayer = false), two, three),
            listOf(one.copy(id = 99), two, three),
            listOf(two, one, three), listOf(one), emptyList(), listOf(three),
        )
        for (messages in replacements) {
            val update = updateTranscriptFollow(TranscriptFollowState(before, unread = true),
                snapshot(messages), TranscriptReadPosition(before, true))
            assertEquals(messages, update.state.snapshot?.messages)
            assertFalse(update.state.unread)
            assertNull(update.request)
        }
        val equal = updateTranscriptFollow(TranscriptFollowState(before), snapshot(listOf(one, two)),
            TranscriptReadPosition(before, true))
        assertFalse(equal.state.unread)
        assertNull(equal.request)
    }

    @Test fun callerMutationsCannotRewriteFrozenHistoryOrRetroactivelyAuthorizeAppend() {
        val mutable = mutableListOf(one, two)
        val frozen = snapshot(mutable)
        val request = checkNotNull(latestTranscriptRequest(frozen))
        mutable[0] = one.copy(text = "Caller changed a prior row")
        mutable += three
        assertEquals(listOf(one, two), frozen.messages)
        assertEquals(two.id, request.targetMessageId)
        val changed = snapshot(mutable)
        assertFalse(transcriptRequestMatches(request, changed))
        assertNull(updateTranscriptFollow(TranscriptFollowState(frozen), changed,
            TranscriptReadPosition(frozen, true)).request)
        mutable.clear()
        assertEquals(listOf(one, two), frozen.messages)
        assertEquals(3, changed.messages.size)
    }

    @Test fun latestRequestsRejectStaleScopesHistoriesAndForgedTargetsEvenWithReusedIds() {
        val current = snapshot(listOf(one, two))
        val request = checkNotNull(latestTranscriptRequest(current))
        assertTrue(transcriptRequestMatches(request, snapshot(listOf(one, two))))
        val stale = listOf(null, snapshot(listOf(one, two), TranscriptScope.Demo),
            snapshot(listOf(one, two), TranscriptScope.Saved("story-a", "fork")),
            snapshot(listOf(one, two.copy(text = "Different reply, same ID"))),
            snapshot(listOf(one, two, three)), snapshot(listOf(two, one)), snapshot(emptyList()))
        for (other in stale) assertFalse(transcriptRequestMatches(request, other))
        assertFalse(transcriptRequestMatches(TranscriptScrollRequest(current, one.id), current))
        assertNull(latestTranscriptRequest(null))
        assertNull(latestTranscriptRequest(snapshot(emptyList())))
    }

    @Test fun aReadWitnessForAnotherStoryOrOlderHistoryCannotClearCurrentUnread() {
        val current = snapshot(listOf(one, two))
        val before = TranscriptFollowState(current, unread = true)
        for (wrong in listOf(snapshot(listOf(one)),
            snapshot(listOf(one, two), TranscriptScope.Saved("other", "main")),
            snapshot(listOf(one, two), TranscriptScope.Saved("story-a", "fork")),
            snapshot(listOf(one, two.copy(isPlayer = true))))) {
            val update = updateTranscriptFollow(before, current, TranscriptReadPosition(wrong, true))
            assertTrue(update.state.unread)
            assertNull(update.request)
        }
    }

    @Test fun tailGeometryRequiresTheBottomOrAnActualLaterItemAndDoesNotOverflow() {
        val headOfLongReply = TranscriptViewport(5, 12, 0, 600, tailOffset = 40, tailSize = 1800)
        assertFalse(transcriptEndReached(5, headOfLongReply))
        assertTrue(transcriptEndReached(5, headOfLongReply.copy(tailOffset = -1200)))
        assertFalse(transcriptEndReached(5, headOfLongReply.copy(tailOffset = -1199)))
        assertTrue(transcriptEndReached(5, TranscriptViewport(6, 12, 0, 600)))
        assertFalse(transcriptEndReached(5, TranscriptViewport(4, 12, 0, 600)))
        assertFalse(transcriptEndReached(5, headOfLongReply.copy(tailOffset = Int.MAX_VALUE, tailSize = Int.MAX_VALUE)))
        assertFalse(transcriptEndReached(-1, headOfLongReply))
        assertFalse(transcriptEndReached(12, headOfLongReply))
        assertFalse(transcriptEndReached(5, headOfLongReply.copy(firstVisibleItemIndex = -1)))
        assertFalse(transcriptEndReached(5, headOfLongReply.copy(firstVisibleItemIndex = 12)))
        assertFalse(transcriptEndReached(5, headOfLongReply.copy(viewportEndOffset = 0)))
        assertFalse(transcriptEndReached(5, headOfLongReply.copy(tailSize = 0)))
    }
}

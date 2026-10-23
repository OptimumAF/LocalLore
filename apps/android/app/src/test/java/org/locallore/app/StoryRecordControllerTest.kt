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

@OptIn(ExperimentalCoroutinesApi::class)
class StoryRecordControllerTest {
    private val context = StoryRecordContext(SavedStory("story-a", "root", "Synthetic", 2), 2)
    private fun page(query: StoryRecordQuery, next: String? = null) = StoryRecordPage(query, 3, 2,
        listOf(StoryRecordEntry("key", "Name", "Player", StoryRecordOrigin.CANONICAL_FIELD, listOf("Seed · player"))), next)

    @Test fun paginationSearchAndSectionsUseFrozenContext() = runTest {
        val calls = mutableListOf<StoryRecordQuery>()
        val controller = StoryRecordController({ q -> calls += q; page(q, if (q.cursor == null) "cursor-1" else null) }, this)
        controller.open(context); advanceUntilIdle()
        controller.next(); advanceUntilIdle()
        assertEquals("cursor-1", calls.last().cursor)
        controller.first(); advanceUntilIdle()
        assertNull(calls.last().cursor)
        controller.search("Literal % '_"); advanceUntilIdle()
        assertEquals("Literal % '_", calls.last().search)
        controller.select(StoryRecordSection.KNOWLEDGE); advanceUntilIdle()
        assertEquals(StoryRecordSection.KNOWLEDGE, calls.last().section)
        assertNull(calls.last().cursor)
        assertTrue(calls.all { it.context == context })
    }

    @Test fun invalidSearchNeverReachesReaderOrRetainsOldRows() = runTest {
        var calls = 0
        val controller = StoryRecordController({ q -> calls++; page(q) }, this)
        controller.open(context); advanceUntilIdle()
        for (text in listOf("x\nsecret", "é".repeat(129), "a\u007fb")) {
            controller.search(text); advanceUntilIdle()
            assertEquals(StoryRecordProblem.BAD_SEARCH, controller.state.value.problem)
            assertTrue(controller.state.value.entries.isEmpty())
        }
        assertEquals(1, calls)
        controller.search("é".repeat(128)); advanceUntilIdle()
        assertEquals(2, calls)
    }

    @Test fun lateNonCooperativeReadCannotReplaceNewStoryOrDismissal() = runTest {
        val old = CompletableDeferred<Unit>()
        val controller = StoryRecordController({ q ->
            if (q.context == context) withContext(NonCancellable) { old.await() }
            page(q)
        }, this)
        controller.open(context); runCurrent()
        val other = context.copy(story = context.story.copy(story = "story-b"))
        controller.open(other); runCurrent()
        val fresh = controller.state.value
        old.complete(Unit); advanceUntilIdle()
        assertEquals(fresh, controller.state.value)
        controller.dismiss()
        assertEquals(StoryRecordState(), controller.state.value)
    }

    @Test fun disposalCancelsAndForbidsRetainedCallbacks() = runTest {
        val end = CompletableDeferred<Unit>()
        var calls = 0
        val controller = StoryRecordController({ q -> calls++; withContext(NonCancellable) { end.await() }; page(q) }, this)
        controller.open(context); runCurrent(); controller.dispose()
        controller.open(context); controller.select(StoryRecordSection.HISTORY); controller.retry()
        end.complete(Unit); advanceUntilIdle()
        assertEquals(1, calls)
        assertEquals(StoryRecordState(), controller.state.value)
    }

    @Test fun changingSectionWhileLoadingClearsRowsAndRejectsLateFailure() = runTest {
        val end = CompletableDeferred<Unit>()
        val controller = StoryRecordController({ q ->
            if (q.section == StoryRecordSection.PROGRESSION) {
                withContext(NonCancellable) { end.await() }; error("PRIVATE PATH")
            }
            page(q)
        }, this)
        controller.open(context); runCurrent()
        controller.next(); controller.search("ignored") // Disabled during a load.
        controller.select(StoryRecordSection.HISTORY); runCurrent()
        end.complete(Unit); advanceUntilIdle()
        assertEquals(StoryRecordSection.HISTORY, controller.state.value.section)
        assertNull(controller.state.value.problem)
    }

    @Test fun malformedPagesAndRawFailuresFailClosed() = runTest {
        val transforms: List<(StoryRecordPage) -> StoryRecordPage> = listOf(
            { it.copy(query = it.query.copy(context = context.copy(revision = 9))) },
            { it.copy(entries = List(9) { n -> it.entries.single().copy(key = "k$n") }, total = 9) },
            { it.copy(entries = it.entries + it.entries) },
            { it.copy(total = -1) }, { it.copy(storyTime = -1) },
            { it.copy(entries = emptyList(), nextCursor = "cursor") },
        )
        for (transform in transforms) {
            val controller = StoryRecordController({ q -> transform(page(q)) }, this)
            controller.open(context); advanceUntilIdle()
            assertEquals(StoryRecordProblem.INVALID_RESPONSE, controller.state.value.problem)
            assertTrue(controller.state.value.entries.isEmpty())
        }
        val controller = StoryRecordController({ error("SECRET-TIDE /private/save") }, this)
        controller.open(context); advanceUntilIdle()
        assertFalse(controller.state.value.toString().contains("SECRET"))
    }

    @Test fun publishedCollectionsCannotBeChangedByReader() = runTest {
        val sources = mutableListOf("Seed · player")
        val entries = mutableListOf(StoryRecordEntry("key", "Name", "Player", StoryRecordOrigin.CANONICAL_FIELD, sources))
        val limitations = mutableListOf("Bounded view")
        val controller = StoryRecordController({ q -> StoryRecordPage(q, 0, 1, entries, null, limitations) }, this)
        controller.open(context); advanceUntilIdle()
        sources.clear(); entries.clear(); limitations.clear()
        assertEquals(listOf("Seed · player"), controller.state.value.entries.single().sources)
        assertEquals(listOf("Bounded view"), controller.state.value.limitations)
    }

    @Test fun laterPagesCannotChangeTheFrozenCountOrStoryClock() = runTest {
        for (changeTime in listOf(false, true)) for (transportFailure in listOf(false, true)) {
            var laterReads = 0
            val controller = StoryRecordController({ q ->
                if (q.cursor == null) page(q, "cursor-1")
                else {
                    laterReads++
                    if (transportFailure && laterReads == 1) error("PRIVATE transport failure")
                    if (changeTime) page(q).copy(storyTime = 4) else page(q).copy(total = 3)
                }
            }, this)
            controller.open(context); advanceUntilIdle()
            controller.next(); advanceUntilIdle()
            assertEquals(StoryRecordProblem.INVALID_RESPONSE, controller.state.value.problem)
            assertTrue(controller.state.value.entries.isEmpty())
            controller.retry(); advanceUntilIdle()
            assertEquals(StoryRecordProblem.INVALID_RESPONSE, controller.state.value.problem)
            assertTrue(controller.state.value.entries.isEmpty())
        }
    }
}

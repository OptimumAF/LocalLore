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
class EventSourceControllerTest {
    private val context = StoryRecordContext(SavedStory("story-a", "root", "Synthetic", 12), 12)
    private fun field(refs: List<Long> = listOf(2)) = StoryRecordEntry("field", "Trust", "1",
        StoryRecordOrigin.CANONICAL_FIELD, listOf("Event #2"), refs)
    private fun listPage(q: StoryRecordQuery, entry: StoryRecordEntry = field()) = StoryRecordPage(q, 1000, 1, listOf(entry), null)
    private fun detail(q: StoryRecordQuery, id: Long = 2) = StoryRecordPage(q, 1000, 1,
        listOf(StoryRecordEntry("event-$id", "Event #$id", "A recorded statement was made.",
            StoryRecordOrigin.RECORDED_OBSERVATION, listOf("Event #$id"), listOf(id), StoryRecordEvent(id, "turn-id", 100))), null)
    private fun isDetail(q: StoryRecordQuery) = q.search.startsWith("\"sequence\":")

    @Test fun onlyTypedCurrentPageReferencesAuthorizeAnEventRead() = runTest {
        val calls = mutableListOf<StoryRecordQuery>()
        val controller = StoryRecordController({ q -> calls += q; if (isDetail(q)) detail(q) else listPage(q) }, this)
        controller.openEvent(2); controller.open(context); advanceUntilIdle()
        for (id in listOf(-1L, 0L, 1L, 3L, 13L)) controller.openEvent(id)
        advanceUntilIdle(); assertEquals(1, calls.size)
        controller.openEvent(2); advanceUntilIdle()
        assertEquals(2, calls.size)
        assertEquals(StoryRecordQuery(context, StoryRecordSection.HISTORY, "\"sequence\":2,"), calls.last())
        assertEquals(2L, controller.state.value.eventDetail!!.entry!!.event!!.sequence)
        controller.dismiss(); controller.openEvent(2); controller.retryEvent(); advanceUntilIdle()
        assertEquals(2, calls.size)
    }

    @Test fun sourceLikeLabelsAndWithheldEvidenceNeverCreateReferences() = runTest {
        for (label in listOf("Event #2", "Seed · Event #2", "Evidence withheld")) {
            var calls = 0
            val controller = StoryRecordController({ q -> calls++; listPage(q, field(emptyList()).copy(sources = listOf(label))) }, this)
            controller.open(context); advanceUntilIdle()
            controller.openEvent(2); advanceUntilIdle()
            assertEquals(1, calls)
            assertNull(controller.state.value.eventDetail)
        }
    }

    @Test fun backRestoresTheExactPageSearchSectionAndCountWithoutReadingAgain() = runTest {
        var calls = 0
        val controller = StoryRecordController({ q ->
            calls++
            if (isDetail(q)) detail(q) else listPage(q).copy(total = 2, nextCursor = if (q.cursor == null) "second-page" else null)
        }, this)
        controller.open(context); advanceUntilIdle()
        controller.select(StoryRecordSection.RELATIONSHIPS); advanceUntilIdle()
        controller.search("recorded"); advanceUntilIdle()
        controller.next(); advanceUntilIdle()
        val page = controller.state.value
        controller.openEvent(2); advanceUntilIdle()
        val readCount = calls
        controller.back(); advanceUntilIdle()
        assertEquals(page, controller.state.value)
        assertEquals(readCount, calls)
    }

    @Test fun missingOrPrivateSourceShowsOneFixedUnavailableState() = runTest {
        val controller = StoryRecordController({ q ->
            if (isDetail(q)) StoryRecordPage(q, 1000, 0, emptyList(), null) else listPage(q)
        }, this)
        controller.open(context); advanceUntilIdle(); controller.openEvent(2); advanceUntilIdle()
        assertEquals(StoryRecordProblem.EVENT_UNAVAILABLE, controller.state.value.eventDetail!!.problem)
        assertNull(controller.state.value.eventDetail!!.entry)
        controller.back(); assertEquals(1, controller.state.value.entries.size)
    }

    @Test fun malformedEventResponsesCannotBecomeVisibleDetails() = runTest {
        val changes: List<(StoryRecordPage) -> StoryRecordPage> = listOf(
            { it.copy(query = it.query.copy(context = context.copy(revision = 11))) },
            { it.copy(total = 2) }, { it.copy(entries = it.entries + it.entries) },
            { it.copy(nextCursor = "unexpected") }, { it.copy(storyTime = 1001) },
            { it.copy(entries = listOf(field())) },
            { it.copy(entries = listOf(it.entries.single().copy(event = StoryRecordEvent(3, "wrong-event", 100)))) },
            { it.copy(entries = listOf(it.entries.single().copy(event = StoryRecordEvent(2, "", 100)))) },
            { it.copy(entries = listOf(it.entries.single().copy(event = StoryRecordEvent(2, "turn-id", 1001)))) },
        )
        for (change in changes) {
            val controller = StoryRecordController({ q -> if (isDetail(q)) change(detail(q)) else listPage(q) }, this)
            controller.open(context); advanceUntilIdle(); controller.openEvent(2); advanceUntilIdle()
            assertEquals(StoryRecordProblem.INVALID_RESPONSE, controller.state.value.eventDetail!!.problem)
            assertNull(controller.state.value.eventDetail!!.entry)
        }
    }

    @Test fun futureDuplicateAndUnboundedTypedReferencesInvalidateThePage() = runTest {
        for (refs in listOf(listOf(0L), listOf(13L), listOf(2L, 2L), List(65) { 1L })) {
            val controller = StoryRecordController({ q -> listPage(q, field(refs)) }, this)
            controller.open(context); advanceUntilIdle()
            assertEquals(StoryRecordProblem.INVALID_RESPONSE, controller.state.value.problem)
            assertTrue(controller.state.value.entries.isEmpty())
        }
    }

    @Test fun backDiscardsLateNonCooperativeSuccessAndFailure() = runTest {
        for (fail in listOf(false, true)) {
            val end = CompletableDeferred<Unit>()
            val controller = StoryRecordController({ q ->
                if (isDetail(q)) {
                    withContext(NonCancellable) { end.await() }
                    if (fail) error("PRIVATE path and story")
                    detail(q)
                } else listPage(q)
            }, this)
            controller.open(context); advanceUntilIdle()
            val original = controller.state.value
            controller.openEvent(2); runCurrent(); controller.back()
            end.complete(Unit); advanceUntilIdle()
            assertEquals(original, controller.state.value)
        }
    }

    @Test fun changingQueryOrContextRevokesAnOldDetailRead() = runTest {
        for (transition in 0..6) {
            val end = CompletableDeferred<Unit>()
            val controller = StoryRecordController({ q ->
                if (isDetail(q)) { withContext(NonCancellable) { end.await() }; detail(q) }
                else listPage(q).copy(total = 2, nextCursor = if (q.cursor == null) "next" else null)
            }, this)
            controller.open(context); advanceUntilIdle(); controller.openEvent(2); runCurrent()
            when (transition) {
                0 -> controller.select(StoryRecordSection.KNOWLEDGE)
                1 -> controller.search("new search")
                2 -> controller.first()
                3 -> controller.open(context.copy(story = context.story.copy(story = "story-b")))
                4 -> controller.dismiss()
                5 -> controller.dispose()
                6 -> controller.next()
            }
            runCurrent(); val fresh = controller.state.value
            end.complete(Unit); advanceUntilIdle()
            assertEquals(fresh, controller.state.value)
            assertNull(controller.state.value.eventDetail)
        }
    }

    @Test fun aRetryCannotOverlapOrInheritFailedDetailText() = runTest {
        var reads = 0
        val release = CompletableDeferred<Unit>()
        val controller = StoryRecordController({ q ->
            if (!isDetail(q)) listPage(q) else {
                reads++
                if (reads == 1) error("PRIVATE-CANARY")
                release.await(); detail(q)
            }
        }, this)
        controller.open(context); advanceUntilIdle(); controller.openEvent(2); advanceUntilIdle()
        assertFalse(controller.state.value.toString().contains("PRIVATE"))
        controller.retryEvent(); runCurrent()
        controller.retryEvent(); controller.openEvent(2); runCurrent()
        assertEquals(2, reads)
        assertTrue(controller.state.value.eventDetail!!.loading)
        assertNull(controller.state.value.eventDetail!!.problem)
        release.complete(Unit); advanceUntilIdle()
        assertNotNull(controller.state.value.eventDetail!!.entry)
    }

    @Test fun detailAndPageCollectionsAreFrozenBeforePublication() = runTest {
        val refs = mutableListOf(2L)
        val sources = mutableListOf("Event #2")
        val controller = StoryRecordController({ q ->
            if (isDetail(q)) detail(q).let { it.copy(entries = listOf(it.entries.single().copy(eventSources = refs, sources = sources))) }
            else listPage(q, field(refs))
        }, this)
        controller.open(context); advanceUntilIdle(); controller.openEvent(2); advanceUntilIdle()
        refs.clear(); sources.clear()
        assertEquals(listOf(2L), controller.state.value.entries.single().eventSources)
        assertEquals(listOf(2L), controller.state.value.eventDetail!!.entry!!.eventSources)
        assertEquals(listOf("Event #2"), controller.state.value.eventDetail!!.entry!!.sources)
        controller.dispose(); controller.open(context); controller.openEvent(2); controller.retryEvent(); controller.back()
        advanceUntilIdle(); assertEquals(StoryRecordState(), controller.state.value)
    }
}

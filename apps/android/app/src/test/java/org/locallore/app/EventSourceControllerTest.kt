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
    private fun reference(context: StoryRecordContext = this.context, id: Long = 2) =
        StoryRecordScopedEvent(StoryRecordScope(context.story.story, context.story.branch), id)
    private fun label(ref: StoryRecordScopedEvent) = "Event #${ref.sequence} · ${ref.originalScope.story} / ${ref.originalScope.branch}"
    private fun search(ref: StoryRecordScopedEvent) = "\"event\":{\"sequence\":${ref.sequence},\"scope\":{\"story\":\"${ref.originalScope.story}\",\"branch\":\"${ref.originalScope.branch}\"}"
    private fun field(refs: List<StoryRecordScopedEvent> = listOf(reference())) = StoryRecordEntry("field", "Trust", "1",
        StoryRecordOrigin.CANONICAL_FIELD, refs.map(::label).ifEmpty { listOf(label(reference())) }, scopedEventSources = refs)
    private fun listPage(q: StoryRecordQuery, entry: StoryRecordEntry = field(listOf(reference(q.context)))) = StoryRecordPage(q, 1000, 1, listOf(entry), null)
    private fun detail(q: StoryRecordQuery, id: Long = 2): StoryRecordPage {
        val ref = reference(q.context, id)
        return StoryRecordPage(q, 1000, 1,
            listOf(StoryRecordEntry("event-$id", "Event #$id", "A recorded statement was made.",
                StoryRecordOrigin.RECORDED_OBSERVATION, listOf(label(ref)),
                event = StoryRecordEvent(id, "turn-id", 100, ref.originalScope), scopedEventSources = listOf(ref))), null)
    }
    private fun isDetail(q: StoryRecordQuery) = q.search.startsWith("\"event\":{\"sequence\":")

    @Test fun onlyTypedCurrentPageReferencesAuthorizeAnEventRead() = runTest {
        val calls = mutableListOf<StoryRecordQuery>()
        val controller = StoryRecordController({ q -> calls += q; if (isDetail(q)) detail(q) else listPage(q) }, this)
        controller.openEvent(2); controller.open(context); advanceUntilIdle()
        for (id in listOf(-1L, 0L, 1L, 3L, 13L)) controller.openEvent(id)
        controller.openEvent(2) // A bare ID is inert even when the scoped tuple is on the page.
        for (ref in listOf(reference(id = -1), reference(id = 0), reference(id = 1), reference(id = 3), reference(id = 13),
            reference().copy(originalScope = StoryRecordScope("other-story", "root")),
            reference().copy(originalScope = StoryRecordScope("story-a", "other-branch")))) controller.openScopedEvent(ref)
        advanceUntilIdle(); assertEquals(1, calls.size)
        controller.openScopedEvent(reference()); advanceUntilIdle()
        assertEquals(2, calls.size)
        assertEquals(StoryRecordQuery(context, StoryRecordSection.HISTORY, search(reference())), calls.last())
        assertEquals(2L, controller.state.value.eventDetail!!.entry!!.event!!.sequence)
        controller.dismiss(); controller.openEvent(2); controller.retryEvent(); advanceUntilIdle()
        controller.openScopedEvent(reference()); advanceUntilIdle()
        assertEquals(2, calls.size)
    }

    @Test fun sourceLikeLabelsAndWithheldEvidenceNeverCreateReferences() = runTest {
        for (label in listOf("Event #2", "Seed · Event #2", "Evidence withheld")) {
            var calls = 0
            val controller = StoryRecordController({ q -> calls++; listPage(q, field(emptyList()).copy(sources = listOf(label))) }, this)
            controller.open(context); advanceUntilIdle()
            controller.openEvent(2); advanceUntilIdle()
            controller.openScopedEvent(reference()); advanceUntilIdle()
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
        controller.openScopedEvent(reference()); advanceUntilIdle()
        val readCount = calls
        controller.back(); advanceUntilIdle()
        assertEquals(page, controller.state.value)
        assertEquals(readCount, calls)
    }

    @Test fun missingOrPrivateSourceShowsOneFixedUnavailableState() = runTest {
        val controller = StoryRecordController({ q ->
            if (isDetail(q)) StoryRecordPage(q, 1000, 0, emptyList(), null) else listPage(q)
        }, this)
        controller.open(context); advanceUntilIdle(); controller.openScopedEvent(reference()); advanceUntilIdle()
        assertEquals(StoryRecordProblem.EVENT_UNAVAILABLE, controller.state.value.eventDetail!!.problem)
        assertNull(controller.state.value.eventDetail!!.entry)
        controller.back(); assertEquals(1, controller.state.value.entries.size)
    }

    @Test fun malformedEventResponsesCannotBecomeVisibleDetails() = runTest {
        val originalScope = reference().originalScope
        val changes: List<(StoryRecordPage) -> StoryRecordPage> = listOf(
            { it.copy(query = it.query.copy(context = context.copy(revision = 11))) },
            { it.copy(total = 2) }, { it.copy(entries = it.entries + it.entries) },
            { it.copy(nextCursor = "unexpected") }, { it.copy(storyTime = 1001) },
            { it.copy(entries = listOf(field())) },
            { it.copy(entries = listOf(it.entries.single().copy(event = StoryRecordEvent(3, "wrong-event", 100, originalScope)))) },
            { it.copy(entries = listOf(it.entries.single().copy(event = StoryRecordEvent(2, "", 100, originalScope)))) },
            { it.copy(entries = listOf(it.entries.single().copy(event = StoryRecordEvent(2, "   ", 100, originalScope)))) },
            { it.copy(entries = listOf(it.entries.single().copy(event = StoryRecordEvent(2, "bad\nturn", 100, originalScope)))) },
            { it.copy(entries = listOf(it.entries.single().copy(event = StoryRecordEvent(2, "x".repeat(65), 100, originalScope)))) },
            { it.copy(entries = listOf(it.entries.single().copy(event = StoryRecordEvent(2, "turn-id", 1001, originalScope)))) },
        )
        for (change in changes) {
            val controller = StoryRecordController({ q -> if (isDetail(q)) change(detail(q)) else listPage(q) }, this)
            controller.open(context); advanceUntilIdle(); controller.openScopedEvent(reference()); advanceUntilIdle()
            assertEquals(StoryRecordProblem.INVALID_RESPONSE, controller.state.value.eventDetail!!.problem)
            assertNull(controller.state.value.eventDetail!!.entry)
        }
    }

    @Test fun futureDuplicateAndUnboundedTypedReferencesInvalidateThePage() = runTest {
        for (refs in listOf(listOf(0L), listOf(13L), listOf(2L, 2L), List(65) { 1L })) {
            val controller = StoryRecordController({ q -> listPage(q, field(refs.map { reference(id = it) })) }, this)
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
            controller.openScopedEvent(reference()); runCurrent(); controller.back()
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
            controller.open(context); advanceUntilIdle(); controller.openScopedEvent(reference()); runCurrent()
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
        controller.open(context); advanceUntilIdle(); controller.openScopedEvent(reference()); advanceUntilIdle()
        assertFalse(controller.state.value.toString().contains("PRIVATE"))
        controller.retryEvent(); runCurrent()
        controller.retryEvent(); controller.openScopedEvent(reference()); runCurrent()
        assertEquals(2, reads)
        assertTrue(controller.state.value.eventDetail!!.loading)
        assertNull(controller.state.value.eventDetail!!.problem)
        release.complete(Unit); advanceUntilIdle()
        assertNotNull(controller.state.value.eventDetail!!.entry)
    }

    @Test fun detailAndPageCollectionsAreFrozenBeforePublication() = runTest {
        val refs = mutableListOf(reference())
        val sources = mutableListOf(label(reference()))
        val controller = StoryRecordController({ q ->
            if (isDetail(q)) detail(q).let { it.copy(entries = listOf(it.entries.single().copy(scopedEventSources = refs, sources = sources))) }
            else listPage(q, field(refs))
        }, this)
        controller.open(context); advanceUntilIdle(); controller.openScopedEvent(reference()); advanceUntilIdle()
        refs.clear(); sources.clear()
        assertEquals(listOf(reference()), controller.state.value.entries.single().scopedEventSources)
        assertEquals(listOf(reference()), controller.state.value.eventDetail!!.entry!!.scopedEventSources)
        assertTrue(controller.state.value.entries.single().eventSources.isEmpty())
        assertTrue(controller.state.value.eventDetail!!.entry!!.eventSources.isEmpty())
        assertEquals(listOf(label(reference())), controller.state.value.eventDetail!!.entry!!.sources)
        controller.dispose(); controller.open(context); controller.openScopedEvent(reference()); controller.openEvent(2); controller.retryEvent(); controller.back()
        advanceUntilIdle(); assertEquals(StoryRecordState(), controller.state.value)
    }

    @Test fun duplicateEventSequencesWithDifferentKeysStillInvalidateThePage() = runTest {
        val controller = StoryRecordController({ q ->
            val event = detail(q).entries.single()
            StoryRecordPage(q, 1000, 2, listOf(event, event.copy(key = "different-key")), null)
        }, this)
        controller.open(context); advanceUntilIdle()
        controller.select(StoryRecordSection.HISTORY); advanceUntilIdle()
        assertEquals(StoryRecordProblem.INVALID_RESPONSE, controller.state.value.problem)
        assertTrue(controller.state.value.entries.isEmpty())
    }
}

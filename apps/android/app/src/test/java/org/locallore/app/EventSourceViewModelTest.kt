/* Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0 */
package org.locallore.app

import androidx.lifecycle.ViewModelStore
import kotlinx.coroutines.CompletableDeferred
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.ExperimentalCoroutinesApi
import kotlinx.coroutines.NonCancellable
import kotlinx.coroutines.test.StandardTestDispatcher
import kotlinx.coroutines.test.TestCoroutineScheduler
import kotlinx.coroutines.test.advanceUntilIdle
import kotlinx.coroutines.test.resetMain
import kotlinx.coroutines.test.runCurrent
import kotlinx.coroutines.test.runTest
import kotlinx.coroutines.test.setMain
import kotlinx.coroutines.withContext
import org.junit.After
import org.junit.Assert.*
import org.junit.Before
import org.junit.Test

@OptIn(ExperimentalCoroutinesApi::class)
class EventSourceViewModelTest {
    private val dispatcher = StandardTestDispatcher(TestCoroutineScheduler())
    private val store = ViewModelStore()
    private var models = 0
    @Before fun setup() { Dispatchers.setMain(dispatcher) }
    @After fun cleanup() { store.clear(); Dispatchers.resetMain() }

    private fun createModel(gateway: EventGateway) = ShellViewModel(gateway).also {
        store.put("event-model-${models++}", it)
    }

    @Test fun typedCurrentPageEventsOpenBackAndRetryWithoutGameplayOrSnapshotCalls() = runTest(dispatcher) {
        val gateway = EventGateway()
        val model = createModel(gateway)
        model.openRecordEvent(2)
        assertNull(model.storyRecord.value.eventDetail)
        advanceUntilIdle()
        model.openRecordEvent(2)
        assertTrue(gateway.reads.isEmpty())
        model.openStoryRecord(); advanceUntilIdle()
        model.recordSection(StoryRecordSection.RELATIONSHIPS); advanceUntilIdle()
        model.recordSearch("visible"); advanceUntilIdle()
        val page = model.storyRecord.value
        val shell = model.state.value
        val saved = gateway.saved
        val canonical = gateway.canonical.toList()
        val snapshots = gateway.snapshots
        val reads = gateway.reads.size
        model.openRecordEvent(1); model.openRecordEvent(9)
        advanceUntilIdle()
        assertEquals(reads, gateway.reads.size)

        var attempts = 0
        gateway.eventReader = { query, reference ->
            if (attempts++ == 0) throw StoryRecordFailure(StoryRecordProblem.EVENT_UNAVAILABLE)
            eventPage(query, reference)
        }
        model.openRecordEvent(2); advanceUntilIdle()
        assertEquals(StoryRecordProblem.EVENT_UNAVAILABLE, model.storyRecord.value.eventDetail!!.problem)
        val failedQuery = gateway.reads.last()
        model.retryRecordEvent(); advanceUntilIdle()
        assertEquals(failedQuery, gateway.reads.last())
        assertEquals(StoryRecordQuery(StoryRecordContext(FirstStory, 8), StoryRecordSection.HISTORY,
            "\"sequence\":2,"), failedQuery)
        assertEquals(2L, model.storyRecord.value.eventDetail!!.entry!!.event!!.sequence)
        assertEquals(StoryRecordSection.RELATIONSHIPS, model.storyRecord.value.section)
        assertEquals("visible", model.storyRecord.value.search)
        val afterRetryReads = gateway.reads.size
        model.backToStoryRecord(); advanceUntilIdle()
        assertEquals(page, model.storyRecord.value)
        assertEquals(afterRetryReads, gateway.reads.size)
        assertEquals(canonical, gateway.canonical)
        assertEquals(snapshots, gateway.snapshots)
        assertEquals(saved, gateway.saved)
        assertEquals(shell, model.state.value)
    }

    @Test fun everySavedLifecycleTransitionInvalidatesANonCooperativeEventRead() = runTest(dispatcher) {
        for (operation in listOf("submit", "resume", "reset", "recover", "onStop", "diagnostics", "dispose")) {
            val release = CompletableDeferred<Unit>()
            val gateway = EventGateway().apply {
                eventReader = { query, reference ->
                    withContext(NonCancellable) { release.await() }
                    eventPage(query, reference)
                }
            }
            val model = createModel(gateway)
            advanceUntilIdle()
            model.openStoryRecord(); advanceUntilIdle()
            model.openRecordEvent(2); runCurrent()
            assertTrue(operation, model.storyRecord.value.eventDetail!!.loading)
            when (operation) {
                "submit" -> model.submit(DemoAction.TRY_ABILITY)
                "resume" -> model.resume(SecondStory)
                "reset" -> model.reset()
                "recover" -> model.recover()
                "onStop" -> model.cancel() // MainActivity forwards onStop to this callback.
                "diagnostics" -> model.openDiagnostics()
                "dispose" -> store.clear()
            }
            runCurrent()
            val record = model.storyRecord.value
            val shell = model.state.value
            val diagnostics = model.diagnostics.value
            val canonical = gateway.canonical.toList()
            assertEquals(operation, StoryRecordState(), record)
            release.complete(Unit)
            advanceUntilIdle()
            assertEquals(operation, record, model.storyRecord.value)
            assertEquals(operation, shell, model.state.value)
            assertEquals(operation, diagnostics, model.diagnostics.value)
            assertEquals(operation, canonical, gateway.canonical)
        }
    }

    @Test fun retainedEventAndPageCallbacksCannotReadOrReopenAfterDisposal() = runTest(dispatcher) {
        val release = CompletableDeferred<Unit>()
        val gateway = EventGateway().apply {
            eventReader = { query, reference ->
                withContext(NonCancellable) { release.await() }
                eventPage(query, reference)
            }
        }
        val model = createModel(gateway)
        advanceUntilIdle()
        model.openStoryRecord(); advanceUntilIdle()
        model.openRecordEvent(2); runCurrent()
        val retained = listOf<() -> Unit>(
            { model.openRecordEvent(2) }, model::retryRecordEvent, model::backToStoryRecord,
            model::openStoryRecord, model::retryStoryRecord, model::nextRecordPage, model::firstRecordPage,
            { model.recordSection(StoryRecordSection.KNOWLEDGE) }, { model.recordSearch("old") },
            model::closeStoryRecord, model::openDiagnostics,
        )
        store.clear()
        val reads = gateway.reads.size
        val canonical = gateway.canonical.toList()
        repeat(2) { retained.forEach { it() } }
        release.complete(Unit)
        advanceUntilIdle()
        assertEquals(reads, gateway.reads.size)
        assertEquals(canonical, gateway.canonical)
        assertEquals(1, gateway.canonical.count { it == "close" })
        assertEquals(StoryRecordState(), model.storyRecord.value)
        assertFalse(model.diagnostics.value.visible)
    }

    @Test fun numericEventCollisionCannotBorrowThePreviousStorysPageAuthorization() = runTest(dispatcher) {
        val gateway = EventGateway().apply {
            references = { query -> if (query.context.story.story == FirstStory.story) listOf(2) else emptyList() }
        }
        val model = createModel(gateway)
        advanceUntilIdle()
        model.openStoryRecord(); advanceUntilIdle()
        model.openRecordEvent(2); advanceUntilIdle()
        model.resume(SecondStory); advanceUntilIdle()
        val beforeOpen = gateway.reads.size
        model.openRecordEvent(2); advanceUntilIdle()
        assertEquals(beforeOpen, gateway.reads.size)
        model.openStoryRecord(); advanceUntilIdle()
        assertEquals(SecondStory, model.storyRecord.value.context!!.story)
        assertEquals(listOf("Event #2"), model.storyRecord.value.entries.single().sources)
        assertTrue(model.storyRecord.value.entries.single().eventSources.isEmpty())
        val emptyGrant = gateway.reads.size
        model.openRecordEvent(2); advanceUntilIdle()
        assertEquals(emptyGrant, gateway.reads.size)
        assertNull(model.storyRecord.value.eventDetail)

        gateway.references = { listOf(2) }
        model.retryStoryRecord(); advanceUntilIdle()
        model.openRecordEvent(2); advanceUntilIdle()
        assertEquals(StoryRecordContext(SecondStory, 12), gateway.reads.last().context)
        assertEquals("Visible event in ${SecondStory.story}", model.storyRecord.value.eventDetail!!.entry!!.text)
    }

    @Test fun anAcceptedTurnRevokesOldSourcesUntilAFreshCurrentHeadPageArrives() = runTest(dispatcher) {
        val gateway = EventGateway().apply {
            references = { query -> if (query.context.revision == 8L) listOf(2) else listOf(3) }
            response = { DemoResult.Accepted(9, "Mira", "Synthetic accepted gift") }
        }
        val model = createModel(gateway)
        advanceUntilIdle()
        model.openStoryRecord(); advanceUntilIdle()
        model.openRecordEvent(2); advanceUntilIdle()
        model.submit(DemoAction.GIVE_POTION); advanceUntilIdle()
        assertEquals(9L, model.state.value.revision)
        val beforeRefresh = gateway.reads.size
        model.openRecordEvent(2); advanceUntilIdle()
        assertEquals(beforeRefresh, gateway.reads.size)

        val pageReady = CompletableDeferred<Unit>()
        gateway.pageWait = { pageReady.await() }
        model.openStoryRecord(); runCurrent()
        model.openRecordEvent(2); model.openRecordEvent(3); runCurrent()
        assertTrue(model.storyRecord.value.loading)
        assertEquals(beforeRefresh + 1, gateway.reads.size)
        pageReady.complete(Unit); advanceUntilIdle()
        val currentPageReads = gateway.reads.size
        model.openRecordEvent(2); advanceUntilIdle()
        assertEquals(currentPageReads, gateway.reads.size)
        model.openRecordEvent(3); advanceUntilIdle()
        assertEquals(9L, gateway.reads.last().context.revision)
        assertEquals(3L, model.storyRecord.value.eventDetail!!.entry!!.event!!.sequence)
    }

    private class EventGateway : DemoGateway {
        override val durable = true
        override val storyRecords = true
        var saved = snapshot(FirstStory)
        val canonical = mutableListOf<String>()
        val reads = mutableListOf<StoryRecordQuery>()
        var snapshots = 0
        var references: (StoryRecordQuery) -> List<Long> = { listOf(2) }
        var pageWait: suspend () -> Unit = {}
        var response: suspend () -> DemoResult = { DemoResult.Rejected("Ability") }
        var eventReader: suspend (StoryRecordQuery, Long) -> StoryRecordPage = { query, reference -> eventPage(query, reference) }

        override suspend fun initialize(): SavedSnapshot { canonical += "initialize"; return saved }
        override suspend fun respond(action: DemoAction, revision: Long, mode: DemoMode): DemoResult {
            canonical += "respond"
            return response()
        }
        override suspend fun commitAsync(result: DemoResult): DemoResult {
            canonical += "commit"
            if (result is DemoResult.Accepted) saved = saved.copy(revision = result.revision,
                potionOwner = result.potionOwner, selected = saved.selected.copy(revision = result.revision))
            return result
        }
        override suspend fun snapshot(): SavedSnapshot { snapshots++; return saved }
        override suspend fun readStoryRecord(query: StoryRecordQuery): StoryRecordPage {
            reads += query
            if (query.search.startsWith("\"sequence\":")) {
                val reference = query.search.removePrefix("\"sequence\":").removeSuffix(",").toLong()
                return eventReader(query, reference)
            }
            pageWait()
            val refs = references(query)
            val labels = if (refs.isEmpty()) listOf("Event #2") else refs.map { "Event #$it" }
            return StoryRecordPage(query, 100, 1,
                listOf(StoryRecordEntry("visible-field", "Directed trust", "1", StoryRecordOrigin.CANONICAL_FIELD,
                    labels, refs)), null)
        }
        override suspend fun resumeSaved(story: SavedStory): SavedSnapshot {
            canonical += "resume"; saved = snapshot(story); return saved
        }
        override suspend fun createSaved(): SavedSnapshot {
            canonical += "create"; saved = snapshot(SecondStory); return saved
        }
        override suspend fun recoverSaved(): SavedSnapshot { canonical += "recover"; return saved }
        override fun cancel() { canonical += "cancel" }
        override fun close() { canonical += "close" }
    }

    private companion object {
        val FirstStory = SavedStory("event-story-a", "main", "Synthetic Quay", 8)
        val SecondStory = SavedStory("event-story-b", "main", "Synthetic Garden", 12)
        fun snapshot(story: SavedStory) = SavedSnapshot(story.revision, "You", emptyList(),
            "synthetic-private-workspace", 1, listOf(FirstStory, SecondStory), story)
        fun eventPage(query: StoryRecordQuery, reference: Long) = StoryRecordPage(query, 100, 1,
            listOf(StoryRecordEntry("event-$reference", "Event #$reference",
                "Visible event in ${query.context.story.story}", StoryRecordOrigin.RECORDED_OBSERVATION,
                listOf("Event #$reference"), listOf(reference), StoryRecordEvent(reference, "synthetic-turn", 20))), null)
    }
}

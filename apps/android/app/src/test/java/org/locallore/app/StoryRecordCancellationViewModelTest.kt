/* Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0 */
package org.locallore.app

import androidx.lifecycle.ViewModelStore
import kotlinx.coroutines.CancellationException
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

/** Actual ViewModel/controller over a fault-injecting read port; no native save or inference. */
@OptIn(ExperimentalCoroutinesApi::class)
class StoryRecordCancellationViewModelTest {
    private val dispatcher = StandardTestDispatcher(TestCoroutineScheduler())
    private val store = ViewModelStore()
    private var modelCount = 0
    @Before fun setup() { Dispatchers.setMain(dispatcher) }
    @After fun cleanup() { store.clear(); Dispatchers.resetMain() }
    private fun model(gateway: Gateway) = ShellViewModel(gateway).also { store.put("record-cancel-${modelCount++}", it) }

    @Test fun currentPageCancellationAndExactCursorRetryKeepTheAcceptedShellUnchanged() = runTest(dispatcher) {
        for (later in listOf(false, true)) {
            val gateway = Gateway()
            var cancel = !later
            gateway.reader = { query ->
                if (cancel) { cancel = false; throw CancellationException(PrivateFailure) }
                page(query, if (later && query.cursor == null) "next-synthetic-page" else null)
            }
            val model = model(gateway)
            advanceUntilIdle()
            val shell = model.state.value
            model.openStoryRecord(); advanceUntilIdle()
            if (later) { cancel = true; model.nextRecordPage(); advanceUntilIdle() }
            val query = gateway.queries.last()
            val cancelled = model.storyRecord.value
            assertTrue(cancelled.visible)
            assertFalse(cancelled.loading)
            assertEquals(StoryRecordProblem.UNAVAILABLE, cancelled.problem)
            assertEquals(if (later) "next-synthetic-page" else null, cancelled.cursor)
            assertTrue(cancelled.entries.isEmpty())
            assertFalse(cancelled.toString().contains("PRIVATE-VM"))
            val count = gateway.queries.size
            advanceUntilIdle()
            assertEquals(count, gateway.queries.size)
            model.retryStoryRecord(); advanceUntilIdle()
            assertEquals(count + 1, gateway.queries.size)
            assertEquals(query, gateway.queries.last())
            assertFalse(model.storyRecord.value.loading)
            assertNull(model.storyRecord.value.problem)
            assertEquals("Visible synthetic record", model.storyRecord.value.entries.single().text)
            assertEquals(shell, model.state.value)
            assertEquals(listOf("initialize"), gateway.lifecycle)
            assertTrue(gateway.forbidden.isEmpty())
        }
    }

    @Test fun scopedDetailCancellationAndRetryKeepTheCurrentChildLensAndOriginalEventTuple() = runTest(dispatcher) {
        val gateway = Gateway()
        var cancel = true
        gateway.reader = { query ->
            if (query.section == StoryRecordSection.HISTORY) {
                if (cancel) { cancel = false; throw CancellationException(PrivateFailure) }
                event(query)
            } else page(query)
        }
        val model = model(gateway)
        advanceUntilIdle()
        val shell = model.state.value
        model.openStoryRecord(); advanceUntilIdle()
        val records = model.storyRecord.value
        model.openScopedRecordEvent(Reference, records.context); advanceUntilIdle()
        val query = gateway.queries.last()
        val detail = checkNotNull(model.storyRecord.value.eventDetail)
        assertFalse(detail.loading)
        assertEquals(StoryRecordProblem.UNAVAILABLE, detail.problem)
        assertEquals(Reference, detail.scopedReference)
        assertNull(detail.entry)
        assertEquals(records.copy(eventDetail = detail), model.storyRecord.value)
        model.retryRecordEvent(); advanceUntilIdle()
        assertEquals(3, gateway.queries.size)
        assertEquals(query, gateway.queries.last())
        assertEquals(Story.branch, query.context.story.branch)
        assertEquals(StoryRecordSection.HISTORY, query.section)
        assertEquals(2, query.version)
        val accepted = checkNotNull(model.storyRecord.value.eventDetail)
        assertFalse(accepted.loading)
        assertNull(accepted.problem)
        assertEquals(Reference.originalScope, accepted.entry!!.event!!.originalScope)
        model.backToStoryRecord()
        assertEquals(records, model.storyRecord.value)
        assertEquals(shell, model.state.value)
        assertEquals(listOf("initialize"), gateway.lifecycle)
        assertTrue(gateway.forbidden.isEmpty())
    }

    @Test fun obsoleteCancellationAfterCloseAndDisposalCannotFinishOrReviveAnotherRead() = runTest(dispatcher) {
        val old = CompletableDeferred<Unit>()
        val retired = CompletableDeferred<Unit>()
        val gateway = Gateway()
        gateway.reader = { query ->
            when (gateway.queries.size) {
                1 -> withContext(NonCancellable) { old.await(); throw CancellationException(PrivateFailure) }
                3 -> withContext(NonCancellable) { retired.await(); throw CancellationException(PrivateFailure) }
                else -> page(query)
            }
        }
        val model = model(gateway)
        try {
            advanceUntilIdle()
            val shell = model.state.value
            model.openStoryRecord(); runCurrent()
            assertTrue(model.storyRecord.value.loading)
            model.closeStoryRecord()
            model.openStoryRecord(); runCurrent()
            val fresh = model.storyRecord.value
            assertFalse(fresh.loading)
            assertNull(fresh.problem)
            old.complete(Unit); advanceUntilIdle()
            assertEquals(fresh, model.storyRecord.value)
            assertEquals(shell, model.state.value)
            model.closeStoryRecord()
            model.openStoryRecord(); runCurrent()
            assertTrue(model.storyRecord.value.loading)
            val retained = model::retryStoryRecord
            store.clear()
            retired.complete(Unit); advanceUntilIdle()
            retained(); model.openStoryRecord(); model.retryRecordEvent(); advanceUntilIdle()
            assertEquals(StoryRecordState(), model.storyRecord.value)
            assertEquals(3, gateway.queries.size)
            assertEquals(listOf("initialize", "close"), gateway.lifecycle)
            assertTrue(gateway.forbidden.isEmpty())
        } finally {
            old.complete(Unit); retired.complete(Unit); store.clear(); advanceUntilIdle()
        }
    }

    private class Gateway : DemoGateway {
        val queries = mutableListOf<StoryRecordQuery>()
        val lifecycle = mutableListOf<String>()
        val forbidden = mutableListOf<String>()
        var reader: suspend (StoryRecordQuery) -> StoryRecordPage = { page(it) }
        override val durable = true
        override val storyRecords = true
        private fun refused(operation: String): Nothing { forbidden += operation; error("Unexpected synthetic gameplay operation") }
        override suspend fun initialize(): SavedSnapshot { lifecycle += "initialize"; return Saved }
        override suspend fun readStoryRecord(query: StoryRecordQuery): StoryRecordPage { queries += query; return reader(query) }
        override suspend fun respond(action: DemoAction, revision: Long, mode: DemoMode): DemoResult = refused("respond")
        override suspend fun respondText(input: PlayInput, revision: Long): DemoResult = refused("respond-text")
        override fun commit(result: DemoResult): DemoResult = refused("commit")
        override suspend fun commitAsync(result: DemoResult): DemoResult = refused("commit-async")
        override suspend fun snapshot(): SavedSnapshot = refused("snapshot")
        override suspend fun createSaved(): SavedSnapshot = refused("create")
        override suspend fun resumeSaved(story: SavedStory): SavedSnapshot = refused("resume")
        override suspend fun recoverSaved(): SavedSnapshot = refused("recover")
        override suspend fun reconcileSaved(): SavedSnapshot = refused("reconcile")
        override suspend fun cancelSaved(): SavedSnapshot = refused("cancel-saved")
        override fun cancel() { refused("cancel") }
        override fun reset() { refused("reset") }
        override fun close() { lifecycle += "close" }
    }

    private companion object {
        const val PrivateFailure = "PRIVATE-VM-CANCEL /unpublished/fake/story"
        val Story = SavedStory("vm-cancel-story", "child", "Synthetic child", 2)
        val Reference = StoryRecordScopedEvent(StoryRecordScope(Story.story, "root"), 1)
        val Saved = SavedSnapshot(Story.revision, "You", emptyList(), "synthetic-read-port", 1,
            listOf(Story), Story, rulesProfile = "fantasy-v1")
        fun page(query: StoryRecordQuery, next: String? = null) = StoryRecordPage(query, 3,
            if (next != null || query.cursor != null) 2 else 1,
            listOf(StoryRecordEntry("field", "Visible field", "Visible synthetic record", StoryRecordOrigin.CANONICAL_FIELD,
                scopedEventSources = listOf(Reference))), next)
        fun event(query: StoryRecordQuery) = StoryRecordPage(query, 3, 1,
            listOf(StoryRecordEntry("event", "Observed event", "Visible observation", StoryRecordOrigin.RECORDED_OBSERVATION,
                event = StoryRecordEvent(1, "synthetic-turn", 3, Reference.originalScope),
                scopedEventSources = listOf(Reference))), null)
    }
}

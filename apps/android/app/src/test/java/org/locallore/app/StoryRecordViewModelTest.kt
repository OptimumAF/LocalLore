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
class StoryRecordViewModelTest {
    private val dispatcher = StandardTestDispatcher(TestCoroutineScheduler())
    private val store = ViewModelStore()
    private var models = 0

    @Before fun setup() { Dispatchers.setMain(dispatcher) }
    @After fun cleanup() { store.clear(); Dispatchers.resetMain() }

    private fun createModel(gateway: RecordGateway): ShellViewModel = ShellViewModel(gateway).also {
        store.put("record-model-${models++}", it)
    }

    @Test fun recordsOpenOnlyAfterSupportedSavedInitializationAndNeverDuringATurn() = runTest(dispatcher) {
        val initialized = CompletableDeferred<SavedSnapshot?>()
        val gateway = RecordGateway().apply { initializeResult = { initialized.await() } }
        val model = createModel(gateway)
        model.openStoryRecord()
        assertFalse(model.storyRecord.value.visible)
        runCurrent()
        model.openStoryRecord()
        assertTrue(model.state.value.busy)
        assertTrue(gateway.reads.isEmpty())
        initialized.complete(gateway.saved)
        advanceUntilIdle()
        model.openStoryRecord()
        advanceUntilIdle()
        assertTrue(model.storyRecord.value.visible)
        assertEquals(1, gateway.reads.size)

        val turn = CompletableDeferred<DemoResult>()
        gateway.response = { turn.await() }
        model.submit(DemoAction.TRY_ABILITY)
        assertFalse(model.storyRecord.value.visible)
        model.openStoryRecord()
        runCurrent()
        assertTrue(model.state.value.busy)
        assertFalse(model.storyRecord.value.visible)
        assertEquals(1, gateway.reads.size)
        turn.complete(DemoResult.Rejected("Ability"))
        advanceUntilIdle()

        for (unsupported in listOf(
            RecordGateway(supportsRecords = false),
            RecordGateway(persistent = false),
            RecordGateway().apply { initializeResult = { null } },
        )) {
            val unavailable = createModel(unsupported)
            advanceUntilIdle()
            unavailable.openStoryRecord()
            advanceUntilIdle()
            assertFalse(unavailable.storyRecord.value.visible)
            assertTrue(unsupported.reads.isEmpty())
        }
    }

    @Test fun recoveryRequiredBlocksInspectionUntilSavedRecoveryCompletes() = runTest(dispatcher) {
        val gateway = RecordGateway().apply { response = { error("synthetic transport failure") } }
        val model = createModel(gateway)
        advanceUntilIdle()
        model.submit(DemoAction.GIVE_POTION)
        advanceUntilIdle()
        assertTrue(model.state.value.recoveryRequired)
        model.openStoryRecord()
        advanceUntilIdle()
        assertFalse(model.storyRecord.value.visible)
        assertTrue(gateway.reads.isEmpty())
        model.recover()
        model.openStoryRecord()
        assertFalse(model.storyRecord.value.visible)
        advanceUntilIdle()
        assertFalse(model.state.value.recoveryRequired)
        model.openStoryRecord()
        advanceUntilIdle()
        assertTrue(model.storyRecord.value.visible)
    }

    @Test fun newTurnResumeResetRecoverAndOnStopCancelAllDismissTheRecord() = runTest(dispatcher) {
        for (operation in listOf("turn", "resume", "reset", "recover", "onStop")) {
            val gateway = RecordGateway()
            val model = createModel(gateway)
            advanceUntilIdle()
            model.openStoryRecord()
            advanceUntilIdle()
            assertTrue(operation, model.storyRecord.value.visible)
            when (operation) {
                "turn" -> model.submit(DemoAction.TRY_ABILITY)
                "resume" -> model.resume(SecondStory)
                "reset" -> model.reset()
                "recover" -> model.recover()
                // MainActivity.onStop invokes this same retained ViewModel callback.
                "onStop" -> model.cancel()
            }
            assertEquals(operation, StoryRecordState(), model.storyRecord.value)
            advanceUntilIdle()
            assertFalse(operation, model.storyRecord.value.visible)
        }
    }

    @Test fun browsingAndDismissalNeverCancelGameplayOrMutateTheSavedProjection() = runTest(dispatcher) {
        val gateway = RecordGateway()
        val model = createModel(gateway)
        advanceUntilIdle()
        val before = model.state.value
        val savedBefore = gateway.saved
        val canonicalBefore = gateway.canonicalCalls.toList()
        val snapshotsBefore = gateway.snapshotCalls
        model.openStoryRecord(); advanceUntilIdle()
        model.recordSection(StoryRecordSection.HISTORY); advanceUntilIdle()
        model.recordSearch("visible"); advanceUntilIdle()
        model.nextRecordPage(); advanceUntilIdle()
        model.firstRecordPage(); advanceUntilIdle()
        model.retryStoryRecord(); advanceUntilIdle()
        assertEquals("visible", model.storyRecord.value.search)
        assertEquals(StoryRecordSection.HISTORY, model.storyRecord.value.section)
        model.closeStoryRecord()
        model.closeStoryRecord()
        advanceUntilIdle()
        assertTrue(gateway.reads.size >= 6)
        assertEquals(canonicalBefore, gateway.canonicalCalls)
        assertEquals(snapshotsBefore, gateway.snapshotCalls)
        assertEquals(savedBefore, gateway.saved)
        assertEquals(before, model.state.value)
        assertEquals(StoryRecordState(), model.storyRecord.value)
    }

    @Test fun openingEitherInspectorRevokesTheOtherInspector() = runTest(dispatcher) {
        val model = createModel(RecordGateway())
        advanceUntilIdle()
        model.openDiagnostics()
        assertTrue(model.diagnostics.value.visible)
        model.openStoryRecord()
        advanceUntilIdle()
        assertFalse(model.diagnostics.value.visible)
        assertTrue(model.storyRecord.value.visible)
        model.openDiagnostics()
        assertTrue(model.diagnostics.value.visible)
        assertEquals(StoryRecordState(), model.storyRecord.value)
    }

    @Test fun dismissingAnUncooperativeReadDoesNotCancelGameplayOrReopenItsView() = runTest(dispatcher) {
        val late = CompletableDeferred<StoryRecordPage>()
        val gateway = RecordGateway().apply { reader = { withContext(NonCancellable) { late.await() } } }
        val model = createModel(gateway)
        advanceUntilIdle()
        val before = model.state.value
        val calls = gateway.canonicalCalls.toList()
        model.openStoryRecord(); runCurrent()
        val query = gateway.reads.single()
        assertTrue(model.storyRecord.value.loading)
        model.closeStoryRecord()
        assertEquals(StoryRecordState(), model.storyRecord.value)
        assertEquals(calls, gateway.canonicalCalls)
        late.complete(page(query, "Closed view response"))
        advanceUntilIdle()
        assertEquals(StoryRecordState(), model.storyRecord.value)
        assertEquals(before, model.state.value)
        assertEquals(calls, gateway.canonicalCalls)
    }

    @Test fun reopeningCapturesCurrentAcceptedHeadAndSelectedStoryWithoutOldSearch() = runTest(dispatcher) {
        val gateway = RecordGateway()
        val model = createModel(gateway)
        advanceUntilIdle()
        model.openStoryRecord(); advanceUntilIdle()
        model.recordSearch("old search"); advanceUntilIdle()
        assertEquals(StoryRecordContext(FirstStory, 4), model.storyRecord.value.context)

        gateway.response = { DemoResult.Accepted(5, "Mira", "Synthetic accepted outcome") }
        model.submit(DemoAction.GIVE_POTION); advanceUntilIdle()
        model.openStoryRecord(); advanceUntilIdle()
        assertEquals(5L, model.storyRecord.value.context!!.revision)
        assertEquals(FirstStory.story, model.storyRecord.value.context!!.story.story)
        assertEquals("", model.storyRecord.value.search)
        assertEquals(StoryRecordSection.PROGRESSION, model.storyRecord.value.section)

        model.resume(SecondStory); advanceUntilIdle()
        model.openStoryRecord(); advanceUntilIdle()
        assertEquals(StoryRecordContext(SecondStory, 12), model.storyRecord.value.context)
        assertEquals(SecondStory.story, gateway.reads.last().context.story.story)
        assertEquals("", gateway.reads.last().search)
    }

    @Test fun lateNonCancellableOldStoryReadCannotPublishIntoTheResumedStory() = runTest(dispatcher) {
        val old = CompletableDeferred<StoryRecordPage>()
        val gateway = RecordGateway().apply {
            reader = { query ->
                if (query.context.story.story == FirstStory.story) {
                    withContext(NonCancellable) { old.await() }
                } else page(query, "Current visible record")
            }
        }
        val model = createModel(gateway)
        advanceUntilIdle()
        model.openStoryRecord(); runCurrent()
        val oldQuery = gateway.reads.single()
        assertTrue(model.storyRecord.value.loading)
        model.resume(SecondStory); runCurrent()
        model.openStoryRecord(); runCurrent()
        val current = model.storyRecord.value
        assertEquals(SecondStory, current.context!!.story)
        assertEquals("Current visible record", current.entries.single().text)
        old.complete(page(oldQuery, "OBSOLETE-PRIVATE-ROW"))
        advanceUntilIdle()
        assertEquals(current, model.storyRecord.value)
        assertFalse(model.storyRecord.value.entries.any { "OBSOLETE" in it.text })
    }

    @Test fun retainedCallbacksCannotReadOrReopenAfterViewModelDisposal() = runTest(dispatcher) {
        val late = CompletableDeferred<StoryRecordPage>()
        val gateway = RecordGateway().apply { reader = { withContext(NonCancellable) { late.await() } } }
        val model = createModel(gateway)
        advanceUntilIdle()
        model.openStoryRecord(); runCurrent()
        val query = gateway.reads.single()
        val retained = listOf<() -> Unit>(
            model::openStoryRecord,
            { model.recordSection(StoryRecordSection.KNOWLEDGE) },
            { model.recordSearch("retained") },
            model::nextRecordPage,
            model::firstRecordPage,
            model::retryStoryRecord,
            model::openDiagnostics,
            model::reset,
            { model.resume(SecondStory) },
            model::recover,
            { model.submit(DemoAction.GIVE_POTION) },
        )
        store.clear()
        val callsAfterDisposal = gateway.canonicalCalls.toList()
        repeat(2) { retained.forEach { it() } }
        late.complete(page(query, "Disposed late response"))
        advanceUntilIdle()
        assertEquals(1, gateway.reads.size)
        assertEquals(1, gateway.canonicalCalls.count { it == "close" })
        assertEquals(callsAfterDisposal, gateway.canonicalCalls)
        assertEquals(StoryRecordState(), model.storyRecord.value)
        assertFalse(model.diagnostics.value.visible)
    }

    private class RecordGateway(
        private val persistent: Boolean = true,
        private val supportsRecords: Boolean = true,
    ) : DemoGateway {
        override val durable get() = persistent
        override val storyRecords get() = supportsRecords
        var saved = snapshotOf(FirstStory)
        var initializeResult: suspend () -> SavedSnapshot? = { saved }
        var response: suspend () -> DemoResult = { DemoResult.Rejected("Ability") }
        var reader: suspend (StoryRecordQuery) -> StoryRecordPage = { page(it) }
        val reads = mutableListOf<StoryRecordQuery>()
        val canonicalCalls = mutableListOf<String>()
        var snapshotCalls = 0

        override suspend fun initialize(): SavedSnapshot? {
            canonicalCalls += "initialize"
            return initializeResult()
        }
        override suspend fun respond(action: DemoAction, revision: Long, mode: DemoMode): DemoResult {
            canonicalCalls += "respond"
            return response()
        }
        override suspend fun commitAsync(result: DemoResult): DemoResult {
            canonicalCalls += "commit"
            if (result is DemoResult.Accepted) saved = saved.copy(
                revision = result.revision,
                potionOwner = result.potionOwner,
                selected = checkNotNull(saved.selected).copy(revision = result.revision),
            )
            return result
        }
        override suspend fun snapshot(): SavedSnapshot {
            snapshotCalls++
            return saved
        }
        override suspend fun readStoryRecord(query: StoryRecordQuery): StoryRecordPage {
            reads += query
            return reader(query)
        }
        override suspend fun resumeSaved(story: SavedStory): SavedSnapshot {
            canonicalCalls += "resume"
            saved = snapshotOf(story)
            return saved
        }
        override suspend fun createSaved(): SavedSnapshot {
            canonicalCalls += "create"
            saved = snapshotOf(SecondStory)
            return saved
        }
        override suspend fun recoverSaved(): SavedSnapshot {
            canonicalCalls += "recover"
            return saved
        }
        override suspend fun cancelSaved(): SavedSnapshot {
            canonicalCalls += "cancel-saved"
            return saved
        }
        override fun cancel() { canonicalCalls += "cancel" }
        override fun reset() { canonicalCalls += "reset" }
        override fun close() { canonicalCalls += "close" }
    }

    private companion object {
        val FirstStory = SavedStory("synthetic-quay", "main", "Lantern Quay", 4)
        val SecondStory = SavedStory("synthetic-garden", "main", "Glass Garden", 12)
        fun snapshotOf(story: SavedStory) = SavedSnapshot(
            revision = story.revision, potionOwner = "You", messages = emptyList(),
            location = "synthetic-app-private-workspace", schemaVersion = 1,
            stories = listOf(FirstStory, SecondStory), selected = story,
            rulesProfile = "fantasy-v1",
        )
        fun page(query: StoryRecordQuery, text: String = "Visible synthetic statement") = StoryRecordPage(
            query = query, storyTime = 10, total = 2,
            entries = listOf(StoryRecordEntry("visible-row", "Visible record", text,
                StoryRecordOrigin.RECORDED_STATEMENT, listOf("seed:synthetic"))),
            nextCursor = if (query.cursor == null) "synthetic-next-page" else null,
        )
    }
}

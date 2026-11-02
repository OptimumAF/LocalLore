/* Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0 */
package org.locallore.app

import androidx.lifecycle.ViewModelStore
import kotlinx.coroutines.CompletableDeferred
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.ExperimentalCoroutinesApi
import kotlinx.coroutines.NonCancellable
import kotlinx.coroutines.test.StandardTestDispatcher
import kotlinx.coroutines.test.advanceUntilIdle
import kotlinx.coroutines.test.runCurrent
import kotlinx.coroutines.test.runTest
import kotlinx.coroutines.test.resetMain
import kotlinx.coroutines.test.setMain
import kotlinx.coroutines.withContext
import org.junit.After
import org.junit.Assert.*
import org.junit.Before
import org.junit.Test

/** Real ViewModel/controller entry points; only the saved/read transport boundary is synthetic. */
@OptIn(ExperimentalCoroutinesApi::class)
class StoryRecordActionScopeTest {
    private val dispatcher = StandardTestDispatcher()
    private val store = ViewModelStore()
    private var modelNumber = 0
    private val a = SavedStory("record-a", "main", "A", 7)
    private val b = SavedStory("record-b", "main", "B", 7)
    private val fork = a.copy(branch = "child")
    private val secretDraft = "A-only draft — café 海 🌿"

    private inner class ReaderGateway : DemoGateway {
        override val durable = true
        override val storyRecords = true
        var selected = a
        var holdNext: CompletableDeferred<Unit>? = null
        var failNextEvent = false
        val reads = mutableListOf<StoryRecordQuery>()
        var responses = 0
        var commits = 0
        var closes = 0
        private fun saved() = SavedSnapshot(selected.revision, "You",
            listOf(SceneMessage(1, "Accepted input", true), SceneMessage(2, "Accepted narration", false)),
            "D:/synthetic/read-only-workspace", 1, listOf(a, b), selected,
            inventory = listOf(PlayerInventoryItem("owned", 2)))
        override suspend fun initialize() = saved()
        override suspend fun snapshot() = saved()
        override suspend fun recoverSaved() = saved()
        override suspend fun resumeSaved(story: SavedStory): SavedSnapshot { selected = story; return saved() }
        override suspend fun respond(action: DemoAction, revision: Long, mode: DemoMode): DemoResult {
            responses++; return DemoResult.Rejected("Unsupported")
        }
        override fun commit(result: DemoResult): DemoResult { commits++; return result }
        override fun close() { closes++ }
        override suspend fun readStoryRecord(query: StoryRecordQuery): StoryRecordPage {
            reads += query
            val hold = holdNext; holdNext = null
            if (hold != null) withContext(NonCancellable) { hold.await() }
            if (query.search.startsWith("\"event\":{\"sequence\":")) {
                if (failNextEvent) { failNextEvent = false; throw StoryRecordFailure(StoryRecordProblem.EVENT_UNAVAILABLE) }
                val sequence = Regex("\\\"sequence\\\":([0-9]+)").find(query.search)!!.groupValues[1].toLong()
                val reference = reference(query.context, sequence)
                return StoryRecordPage(query, 11, 1, listOf(StoryRecordEntry(
                    "event-$sequence", "Observed event", "Synthetic player-visible event",
                    StoryRecordOrigin.RECORDED_OBSERVATION,
                    sources = listOf("Event #$sequence"),
                    event = StoryRecordEvent(sequence, "turn-$sequence", 10, reference.originalScope),
                    scopedEventSources = listOf(reference))), null)
            }
            val index = when (query.cursor) { null -> 0; "cursor-1" -> 1; "cursor-2" -> 2; else -> error("Unknown synthetic cursor") }
            val origin = when (query.section) {
                StoryRecordSection.HISTORY -> StoryRecordOrigin.RECORDED_MESSAGE
                StoryRecordSection.KNOWLEDGE -> StoryRecordOrigin.KNOWN_AS_OBSERVED
                StoryRecordSection.PROMISES -> StoryRecordOrigin.DERIVED_COMPARISON
                else -> StoryRecordOrigin.CANONICAL_FIELD
            }
            return StoryRecordPage(query, 11, 3, listOf(StoryRecordEntry(
                "entry-$index", "Visible ${query.section.label}", "Read-only row $index",
                origin, sources = listOf("Synthetic event sources"),
                scopedEventSources = listOf(reference(query.context, 2), reference(query.context, 3)))),
                if (index < 2) "cursor-${index + 1}" else null)
        }
    }

    private fun reference(context: StoryRecordContext, sequence: Long = 2) =
        StoryRecordScopedEvent(StoryRecordScope(context.story.story, context.story.branch), sequence)

    /** The same plain rendered object and overloads used by MainActivity; no guard in this helper. */
    private class Actions(
        val rendered: StoryRecordState, val close: () -> Unit,
        val section: (StoryRecordSection) -> Unit, val search: (String) -> Unit,
        val next: () -> Unit, val first: () -> Unit, val retry: () -> Unit,
        val event: (Long) -> Unit, val scoped: (StoryRecordScopedEvent) -> Unit,
        val back: () -> Unit, val retryEvent: () -> Unit,
    )
    private fun actions(model: ShellViewModel, value: StoryRecordState = model.storyRecord.value): Actions {
        val renderedRecord = value
        return Actions(renderedRecord, { model.closeStoryRecord(renderedRecord) },
            { section -> model.recordSection(section, renderedRecord) },
            { text -> model.recordSearch(text, renderedRecord) },
            { model.nextRecordPage(renderedRecord) }, { model.firstRecordPage(renderedRecord) },
            { model.retryStoryRecord(renderedRecord) },
            { sequence -> model.openRecordEvent(sequence, renderedRecord) },
            { reference -> model.openScopedRecordEvent(reference, renderedRecord) },
            { model.backToStoryRecord(renderedRecord) }, { model.retryRecordEvent(renderedRecord) })
    }
    private fun all(actions: Actions): List<Pair<String, () -> Unit>> = listOf(
        "close" to actions.close, "section" to { actions.section(StoryRecordSection.KNOWLEDGE) },
        "search" to { actions.search(secretDraft) }, "next" to actions.next,
        "first" to actions.first, "retry" to actions.retry,
        "event" to { actions.event(2) },
        "scoped event" to { actions.scoped(reference(checkNotNull(actions.rendered.context))) },
        "back" to actions.back, "retry event" to actions.retryEvent,
    )
    private fun unchanged(model: ShellViewModel, gateway: ReaderGateway,
                          before: StoryRecordState, reads: Int): Boolean =
        model.storyRecord.value === before && gateway.reads.size == reads
    private fun noGameplay(gateway: ReaderGateway) {
        assertEquals(0, gateway.responses); assertEquals(0, gateway.commits)
    }
    private fun model(gateway: ReaderGateway) = ShellViewModel(gateway).also { store.put("record-${modelNumber++}", it) }
    @Before fun setup() { Dispatchers.setMain(dispatcher) }
    @After fun cleanup() { store.clear(); Dispatchers.resetMain() }

    @Test fun oldUnicodeSearchCannotRetargetAnotherStoryBranchOrAcceptedHead() = runTest(dispatcher) {
        val violations = mutableListOf<String>()
        for (target in listOf(b, fork, a.copy(revision = 8))) {
            val gateway = ReaderGateway(); val model = model(gateway)
            advanceUntilIdle(); model.openStoryRecord(); advanceUntilIdle()
            val old = actions(model)
            val submittedDraft = { old.search(secretDraft) }
            model.resume(target); advanceUntilIdle(); model.openStoryRecord(); advanceUntilIdle()
            val current = model.storyRecord.value; val shell = model.state.value; val reads = gateway.reads.size
            submittedDraft(); advanceUntilIdle()
            if (!unchanged(model, gateway, current, reads)) violations += "${target.story}/${target.branch}/${target.revision}"
            assertSame(shell, model.state.value)
            noGameplay(gateway)
        }
        assertEquals("An old-story draft reached a newer player record", emptyList<String>(), violations)
    }

    @Test fun allTenRetainedToolbarAndSourceCallbacksStayQuietInANewerStoryView() = runTest(dispatcher) {
        val gateway = ReaderGateway(); val model = model(gateway)
        advanceUntilIdle(); model.openStoryRecord(); advanceUntilIdle()
        model.nextRecordPage(); advanceUntilIdle()
        val old = actions(model)
        assertNotNull(old.rendered.cursor); assertNotNull(old.rendered.nextCursor)
        model.resume(b); advanceUntilIdle()
        val violations = mutableListOf<String>()
        for ((name, callback) in all(old)) {
            model.closeStoryRecord(); model.openStoryRecord(); advanceUntilIdle()
            val current = model.storyRecord.value; val reads = gateway.reads.size
            callback(); advanceUntilIdle()
            if (!unchanged(model, gateway, current, reads)) violations += name
        }
        noGameplay(gateway)
        assertEquals("Retained callbacks operated on another story's current controller", emptyList<String>(), violations)
    }

    @Test fun equalCopiedRenderStateNeverGrantsToolbarOrCurrentSourceAuthority() = runTest(dispatcher) {
        val gateway = ReaderGateway(); val model = model(gateway)
        advanceUntilIdle()
        val violations = mutableListOf<String>()
        for (index in 0 until 10) {
            model.closeStoryRecord(); model.openStoryRecord(); advanceUntilIdle()
            val current = model.storyRecord.value
            val copied = current.copy()
            assertEquals(current, copied); assertNotSame(current, copied)
            val (name, callback) = all(actions(model, copied))[index]
            val reads = gateway.reads.size
            callback(); advanceUntilIdle()
            if (!unchanged(model, gateway, current, reads)) violations += name
        }
        noGameplay(gateway)
        assertEquals("A value-equal copy was accepted as the rendered object", emptyList<String>(), violations)
    }

    @Test fun reopeningTheIdenticalContextAndPageDoesNotReviveItsOldCallbacks() = runTest(dispatcher) {
        val gateway = ReaderGateway(); val model = model(gateway)
        advanceUntilIdle(); model.openStoryRecord(); advanceUntilIdle()
        val old = actions(model)
        model.closeStoryRecord(); model.openStoryRecord(); advanceUntilIdle()
        val current = model.storyRecord.value
        assertEquals(old.rendered, current); assertNotSame(old.rendered, current)
        val reads = gateway.reads.size
        old.search(secretDraft); advanceUntilIdle()
        assertTrue("A closed view regained authority after equal-valued reopen", unchanged(model, gateway, current, reads))
        noGameplay(gateway)
    }

    @Test fun priorPageAndQueryFramesCannotSkipPagesOrOverwriteTheNewSearch() = runTest(dispatcher) {
        val gateway = ReaderGateway(); val model = model(gateway)
        advanceUntilIdle(); model.openStoryRecord(); advanceUntilIdle()
        val pageOne = actions(model)
        pageOne.next(); advanceUntilIdle()
        val pageTwo = model.storyRecord.value; val reads = gateway.reads.size
        assertEquals("cursor-1", pageTwo.cursor)
        pageOne.next(); advanceUntilIdle()
        assertTrue("One retained Next skipped the newly rendered second page", unchanged(model, gateway, pageTwo, reads))
        val oldQuery = actions(model)
        actions(model).search("current 海 query"); advanceUntilIdle()
        val currentQuery = model.storyRecord.value; val afterSearch = gateway.reads.size
        oldQuery.search(secretDraft); advanceUntilIdle()
        assertTrue(unchanged(model, gateway, currentQuery, afterSearch))
        assertEquals("current 海 query", model.storyRecord.value.search)
        noGameplay(gateway)
    }

    @Test fun oldPageBackAndRetryEventCallbacksCannotReplaceANewerDetailFrame() = runTest(dispatcher) {
        val gateway = ReaderGateway(); val model = model(gateway)
        advanceUntilIdle(); model.openStoryRecord(); advanceUntilIdle()
        val page = actions(model)
        page.scoped(reference(checkNotNull(page.rendered.context), 2)); advanceUntilIdle()
        val oldDetail = actions(model)
        assertEquals(2L, oldDetail.rendered.eventDetail!!.reference)
        val violations = mutableListOf<String>()
        for ((name, callback) in listOf("old detail back" to oldDetail.back,
            "old detail retry" to oldDetail.retryEvent, "old page next" to page.next,
            "old page event" to { page.scoped(reference(checkNotNull(page.rendered.context), 2)) })) {
            model.backToStoryRecord()
            gateway.failNextEvent = true
            actions(model).scoped(reference(checkNotNull(model.storyRecord.value.context), 3)); advanceUntilIdle()
            val current = model.storyRecord.value; val reads = gateway.reads.size
            assertEquals(3L, current.eventDetail!!.reference)
            assertEquals(StoryRecordProblem.EVENT_UNAVAILABLE, current.eventDetail!!.problem)
            callback(); advanceUntilIdle()
            if (!unchanged(model, gateway, current, reads)) violations += name
        }
        noGameplay(gateway)
        assertEquals("A retained callback retargeted a different detail", emptyList<String>(), violations)
    }

    @Test fun freshLoadingSectionAndCloseRemainUsableAndLateReadCannotRestoreTheirOldFrame() = runTest(dispatcher) {
        val gateway = ReaderGateway(); val model = model(gateway)
        advanceUntilIdle()
        val release = CompletableDeferred<Unit>()
        val closeRelease = CompletableDeferred<Unit>()
        try {
            gateway.holdNext = release
            model.openStoryRecord(); runCurrent()
            val loading = actions(model)
            assertTrue(loading.rendered.loading)
            val reads = gateway.reads.size
            loading.search("disabled during load"); loading.next(); runCurrent()
            assertEquals(reads, gateway.reads.size)
            loading.section(StoryRecordSection.KNOWLEDGE); runCurrent()
            val fresh = model.storyRecord.value
            assertEquals(StoryRecordSection.KNOWLEDGE, fresh.section)
            assertFalse(fresh.loading)
            release.complete(Unit); advanceUntilIdle(); assertSame(fresh, model.storyRecord.value)
            gateway.holdNext = closeRelease
            actions(model).search("new pending read"); runCurrent()
            val currentLoading = actions(model)
            assertTrue(currentLoading.rendered.loading)
            currentLoading.close(); runCurrent()
            val closed = model.storyRecord.value
            assertFalse(closed.visible)
            closeRelease.complete(Unit); advanceUntilIdle(); assertSame(closed, model.storyRecord.value)
            noGameplay(gateway)
        } finally { release.complete(Unit); closeRelease.complete(Unit) }
    }

    @Test fun currentExactCallbacksKeepAllExistingQueriesSourcesAndDirectLegacyControlsWorking() = runTest(dispatcher) {
        val gateway = ReaderGateway(); val model = model(gateway)
        advanceUntilIdle(); model.openStoryRecord(); advanceUntilIdle()
        actions(model).search("current café 海"); advanceUntilIdle()
        assertEquals("current café 海", gateway.reads.last().search)
        actions(model).section(StoryRecordSection.HISTORY); advanceUntilIdle()
        assertEquals(StoryRecordSection.HISTORY, model.storyRecord.value.section)
        actions(model).next(); advanceUntilIdle(); assertEquals("cursor-1", model.storyRecord.value.cursor)
        actions(model).first(); advanceUntilIdle(); assertNull(model.storyRecord.value.cursor)
        val retryReads = gateway.reads.size
        actions(model).retry(); advanceUntilIdle(); assertEquals(retryReads + 1, gateway.reads.size)
        val modern = actions(model)
        modern.event(2); advanceUntilIdle() // Bare IDs cannot flatten the current Query2 reference.
        assertNull(model.storyRecord.value.eventDetail)
        actions(model).scoped(reference(checkNotNull(model.storyRecord.value.context))); advanceUntilIdle()
        assertEquals(2L, model.storyRecord.value.eventDetail!!.entry!!.event!!.sequence)
        actions(model).back(); advanceUntilIdle(); assertNull(model.storyRecord.value.eventDetail)
        gateway.failNextEvent = true
        actions(model).scoped(reference(checkNotNull(model.storyRecord.value.context), 3)); advanceUntilIdle()
        assertEquals(StoryRecordProblem.EVENT_UNAVAILABLE, model.storyRecord.value.eventDetail!!.problem)
        actions(model).retryEvent(); advanceUntilIdle()
        assertEquals(3L, model.storyRecord.value.eventDetail!!.entry!!.event!!.sequence)
        actions(model).close(); advanceUntilIdle(); assertFalse(model.storyRecord.value.visible)
        model.openStoryRecord(); advanceUntilIdle()
        model.recordSection(StoryRecordSection.RELATIONSHIPS); advanceUntilIdle()
        model.recordSearch("trusted direct call"); advanceUntilIdle()
        assertEquals(StoryRecordSection.RELATIONSHIPS, gateway.reads.last().section)
        assertEquals("trusted direct call", gateway.reads.last().search)
        noGameplay(gateway)
    }

    @Test fun cancelledAndDiagnosticViewsCannotActOnTheirFreshlyReopenedRecord() = runTest(dispatcher) {
        val gateway = ReaderGateway(); val model = model(gateway)
        advanceUntilIdle(); model.openStoryRecord(); advanceUntilIdle()
        val violations = mutableListOf<String>()
        for (operation in listOf("cancel", "diagnostics")) {
            val old = actions(model)
            if (operation == "cancel") model.cancel() else model.openDiagnostics()
            advanceUntilIdle()
            assertFalse(model.storyRecord.value.visible)
            model.openStoryRecord(); advanceUntilIdle()
            val current = model.storyRecord.value; val reads = gateway.reads.size
            old.close(); advanceUntilIdle()
            if (!unchanged(model, gateway, current, reads)) violations += operation
            model.openStoryRecord(); advanceUntilIdle()
        }
        noGameplay(gateway)
        assertEquals(emptyList<String>(), violations)
    }

    @Test fun noncooperativeOldReadAndDisposedCallbacksCannotRetargetOrResurrectTheCurrentStory() = runTest(dispatcher) {
        val gateway = ReaderGateway(); val model = model(gateway)
        advanceUntilIdle(); model.openStoryRecord(); advanceUntilIdle()
        val release = CompletableDeferred<Unit>()
        try {
            gateway.holdNext = release
            actions(model).next(); runCurrent()
            val oldLoading = actions(model)
            model.resume(b); runCurrent(); model.openStoryRecord(); runCurrent()
            val current = model.storyRecord.value; val reads = gateway.reads.size
            oldLoading.section(StoryRecordSection.PROMISES); runCurrent()
            assertTrue("Old loading section selected a section in the new story", unchanged(model, gateway, current, reads))
            release.complete(Unit); advanceUntilIdle(); assertSame(current, model.storyRecord.value)
            val retained = all(actions(model))
            store.clear()
            val disposed = model.storyRecord.value; val afterClose = gateway.reads.size
            retained.forEach { it.second() }; advanceUntilIdle()
            assertSame(disposed, model.storyRecord.value)
            assertEquals(afterClose, gateway.reads.size)
            assertEquals(1, gateway.closes)
            noGameplay(gateway)
        } finally { release.complete(Unit) }
    }
}

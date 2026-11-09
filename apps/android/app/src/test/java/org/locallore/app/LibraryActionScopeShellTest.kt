/* Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0 */
package org.locallore.app

import androidx.lifecycle.ViewModelStore
import kotlinx.coroutines.CompletableDeferred
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.ExperimentalCoroutinesApi
import kotlinx.coroutines.NonCancellable
import kotlinx.coroutines.awaitCancellation
import kotlinx.coroutines.flow.Flow
import kotlinx.coroutines.flow.collect
import kotlinx.coroutines.launch
import kotlinx.coroutines.test.StandardTestDispatcher
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

/** Actual VM display ownership over fake saved snapshots; no native selection or recovery proof. */
@OptIn(ExperimentalCoroutinesApi::class)
class LibraryActionScopeShellTest {
    private val dispatcher = StandardTestDispatcher()
    private val owners = ViewModelStore()
    private var nextModel = 0
    @Before fun before() { Dispatchers.setMain(dispatcher) }
    @After fun after() { owners.clear(); Dispatchers.resetMain() }

    /** Baseline behavior remains executable; future member overloads take precedence. */
    @Suppress("UNUSED_PARAMETER", "EXTENSION_SHADOWED_BY_MEMBER")
    private fun ShellViewModel.recover(rendered: ShellState) = recover()
    @Suppress("UNUSED_PARAMETER", "EXTENSION_SHADOWED_BY_MEMBER")
    private fun ShellViewModel.resume(story: SavedStory, rendered: ShellState) = resume(story)
    @Suppress("UNUSED_PARAMETER", "EXTENSION_SHADOWED_BY_MEMBER")
    private fun ShellViewModel.resumeTimeline(timeline: SavedTimeline, rendered: ShellState) = resumeTimeline(timeline)

    @Suppress("UNCHECKED_CAST")
    private fun productionFlow(model: ShellViewModel): Flow<Any> {
        val getter = model.javaClass.methods.singleOrNull {
            it.name.substringBefore('$') == "getFrames" && it.parameterCount == 0
        }
        return (getter?.invoke(model) ?: model.state) as Flow<Any>
    }
    private fun displayed(frame: Any): ShellState = if (frame is ShellState) frame
        else frame.javaClass.getMethod("getState").invoke(frame) as ShellState

    private class Port : DemoGateway, StoryCreationGateway {
        override val durable = true
        override val storyRecords = true
        var selected = Main
        var history = History
        var openings = 0
        var recoveries = 0
        var responses = 0
        var cancellations = 0
        var acknowledgements = 0
        var closes = 0
        val resumes = mutableListOf<SavedStory>()
        var onInitialize: suspend () -> SavedSnapshot = { saved() }
        var onRecover: suspend () -> SavedSnapshot = { saved() }
        var onResume: suspend (SavedStory) -> SavedSnapshot = { selected = it; saved() }
        var onResponse: suspend () -> DemoResult = { throw WorkspaceFailure("Full") }
        var onAck: suspend () -> SavedSnapshot = { saved() }
        fun saved() = SavedSnapshot(selected.revision, "You", history, "D:/synthetic/library-scope.sqlite3", 1,
            listOf(Main.copy(), Other.copy()), selected.copy(), rulesProfile = "fantasy_v1",
            textProvider = TextProvider.SCRIPTED, databaseSchemaVersion = 5,
            timelines = listOf(SavedTimeline(selected.story, "main", null, null, 7, 0),
                SavedTimeline(selected.story, "fork", "main", 6, 7, 2)))
        override suspend fun initialize(): SavedSnapshot { openings++; return onInitialize() }
        override suspend fun snapshot() = saved()
        override suspend fun recoverSaved(): SavedSnapshot { recoveries++; return onRecover() }
        override suspend fun resumeSaved(story: SavedStory): SavedSnapshot { resumes += story; return onResume(story) }
        override suspend fun respond(action: DemoAction, revision: Long, mode: DemoMode): DemoResult {
            responses++; return onResponse()
        }
        override fun cancel() { cancellations++ }
        override suspend fun cancelSaved(): SavedSnapshot { acknowledgements++; return onAck() }
        override fun close() { closes++ }
        override suspend fun preview() = StoryCreationPreview("lantern-quay-v1", "a".repeat(64), "Synthetic starter",
            "Read-only workflow fixture", "fantasy_v1", listOf("A starting player."))
        override suspend fun create(request: StoryCreationRequest): SavedSnapshot = error("No creation consent")
    }
    private fun model(port: Port, log: DiagnosticLog = DiagnosticLog()) = ShellViewModel(port, log).also {
        owners.put("library-scope-${nextModel++}", it)
    }
    private fun story(state: ShellState) = state.stories.single { it.story == Main.story }
    private fun child(state: ShellState) = state.timelines.single { it.branch == "fork" }
    private fun calls(port: Port) = listOf(port.openings, port.recoveries, port.resumes.size,
        port.responses, port.cancellations, port.acknowledgements)

    @Test fun copiedForeignAndPriorLibraryViewsCannotBorrowTheLatestStoryDtoOrDismissItsRecord() = runTest(dispatcher) {
        val violations = mutableListOf<String>()
        for (kind in listOf("copy", "foreign", "prior")) {
            val port = Port(); val log = DiagnosticLog(); val model = model(port, log); val foreign = model(Port())
            try {
                advanceUntilIdle(); val prior = model.state.value
                model.resume(story(prior)); advanceUntilIdle() // Trusted compatibility route refreshes the DTO catalog.
                model.openStoryRecord(); advanceUntilIdle()
                val current = model.state.value; val record = model.storyRecord.value
                assertTrue(record.visible)
                val rendered = when (kind) { "copy" -> current.copy(); "foreign" -> foreign.state.value; else -> prior }
                assertNotSame(current, rendered)
                val before = calls(port); val diagnostics = log.snapshot().json
                model.resume(story(current), rendered); advanceUntilIdle()
                if (model.state.value !== current || calls(port) != before || model.storyRecord.value !== record ||
                    log.snapshot().json != diagnostics) violations += kind
            } finally { owners.clear(); runCurrent() }
        }
        assertEquals("A non-current library view borrowed a freshly published story DTO", emptyList<String>(), violations)
    }

    @Test fun copiedForeignAndPreviouslyHealthyViewsCannotBorrowTheCurrentRecoveryButton() = runTest(dispatcher) {
        val violations = mutableListOf<String>()
        for (kind in listOf("copy", "foreign", "healthy")) {
            val port = Port(); val log = DiagnosticLog(); val model = model(port, log); val foreign = model(Port())
            try {
                advanceUntilIdle(); val healthy = model.state.value
                model.submit(DemoAction.GIVE_POTION); foreign.submit(DemoAction.GIVE_POTION); advanceUntilIdle()
                val current = model.state.value; assertTrue(current.recoveryRequired)
                val rendered = when (kind) { "copy" -> current.copy(); "foreign" -> foreign.state.value; else -> healthy }
                val before = calls(port); val diagnostics = log.snapshot().json
                model.recover(rendered); advanceUntilIdle()
                if (model.state.value !== current || calls(port) != before || log.snapshot().json != diagnostics) violations += kind
                assertEquals(History, model.state.value.messages)
            } finally { owners.clear(); runCurrent() }
        }
        assertEquals("A retained recovery callback acted on the current error view", emptyList<String>(), violations)
    }

    @Test fun healthyCurrentViewHasNoRecoverActionEvenThoughTrustedRecoveryRemainsAvailable() = runTest(dispatcher) {
        val port = Port(); val model = model(port)
        advanceUntilIdle(); val healthy = model.state.value
        model.recover(healthy); advanceUntilIdle()
        assertSame(healthy, model.state.value); assertEquals(0, port.recoveries)
        model.recover(); advanceUntilIdle() // Internal compatibility is intentionally broader than the displayed button.
        assertEquals(1, port.recoveries); assertFalse(model.state.value.recoveryRequired)
        assertEquals(History, model.state.value.messages)
    }

    @Test fun currentLibraryViewCannotSelectCopiedUnshownOrBranchOnlyStoryTargets() = runTest(dispatcher) {
        val violations = mutableListOf<String>()
        for (kind in listOf("copy", "unshown", "branch")) {
            val port = Port(); val model = model(port)
            try {
                advanceUntilIdle(); val current = model.state.value
                val target = when (kind) {
                    "copy" -> story(current).copy()
                    "unshown" -> Other.copy(story = "not-in-library")
                    else -> Fork
                }
                model.resume(target, current); advanceUntilIdle()
                if (port.resumes.isNotEmpty() || model.state.value !== current) violations += kind
            } finally { owners.clear(); runCurrent() }
        }
        assertEquals("Value equality or an unshown target acquired library membership", emptyList<String>(), violations)
    }

    @Test fun oldStoryOrBranchViewCannotRetargetTheReplacementCurrentCatalog() = runTest(dispatcher) {
        val violations = mutableListOf<String>()
        for (timeline in listOf(false, true)) {
            val port = Port(); val model = model(port)
            try {
                advanceUntilIdle(); val old = model.state.value
                val replacement = if (timeline) Fork else Other
                model.resume(replacement); advanceUntilIdle()
                val current = model.state.value; val before = calls(port)
                assertEquals(replacement, current.selectedStory)
                assertEquals(old.revision, current.revision)
                if (timeline) model.resumeTimeline(child(current), old) else model.resume(current.stories.last(), old)
                advanceUntilIdle()
                if (model.state.value !== current || calls(port) != before) violations += if (timeline) "branch" else "story"
            } finally { owners.clear(); runCurrent() }
        }
        assertEquals("A previous selection borrowed replacement story/timeline DTOs", emptyList<String>(), violations)
    }

    @Test fun freshStorySelectionRunsOnceAndOldCallbackCannotRepeatAfterCompletionWithANewDto() = runTest(dispatcher) {
        val release = CompletableDeferred<Unit>(); val port = Port(); val model = model(port)
        port.onResume = { target -> withContext(NonCancellable) { release.await() }; port.selected = target; port.saved() }
        try {
            advanceUntilIdle(); val rendered = model.state.value; val target = story(rendered)
            model.resume(target, rendered); model.resume(target, rendered); runCurrent()
            assertEquals(listOf(target), port.resumes); assertTrue(model.state.value.busy)
            release.complete(Unit); advanceUntilIdle(); val refreshed = model.state.value
            assertEquals(target, story(refreshed)); assertNotSame(target, story(refreshed))
            model.resume(story(refreshed), rendered); advanceUntilIdle()
            assertSame(refreshed, model.state.value); assertEquals(1, port.resumes.size)
            model.resume(refreshed.stories.single { it.story == Other.story }, refreshed); advanceUntilIdle()
            assertEquals(2, port.resumes.size); assertEquals(Other, model.state.value.selectedStory)
        } finally { release.complete(Unit); owners.clear(); runCurrent(); advanceUntilIdle() }
    }

    @Test fun freshTimelineRetainsMembershipRulesButAnOldViewCannotBorrowItsRefreshedDto() = runTest(dispatcher) {
        val port = Port(); val model = model(port)
        advanceUntilIdle(); val rendered = model.state.value; val target = child(rendered)
        model.resumeTimeline(target.copy(), rendered)
        model.resumeTimeline(target.copy(story = Other.story), rendered); advanceUntilIdle()
        assertTrue(port.resumes.isEmpty()); assertSame(rendered, model.state.value)
        model.resumeTimeline(target, rendered); advanceUntilIdle()
        assertEquals(listOf(Fork), port.resumes); val selected = model.state.value
        assertEquals(Fork, selected.selectedStory); assertEquals(History, selected.messages)
        val freshRoot = selected.timelines.single { it.branch == "main" }
        model.resumeTimeline(freshRoot, rendered); advanceUntilIdle()
        assertSame(selected, model.state.value); assertEquals(1, port.resumes.size)
        model.resumeTimeline(freshRoot, selected); advanceUntilIdle()
        assertEquals(listOf(Fork, Main), port.resumes); assertEquals(Main, model.state.value.selectedStory)
    }

    @Test fun slowProductionCollectorReceivesEqualIdleOwnerAfterActualSameStoryResume() = runTest(dispatcher) {
        val releaseCollector = CompletableDeferred<Unit>(); val port = Port(); val model = model(port)
        advanceUntilIdle(); model.resume(story(model.state.value)); advanceUntilIdle() // Warm the exact same final notice.
        val observed = mutableListOf<Any>(); var parked = false
        val collector = launch(StandardTestDispatcher(testScheduler)) {
            productionFlow(model).collect { frame ->
                observed += frame
                if (!parked && !displayed(frame).busy) { parked = true; releaseCollector.await() }
            }
        }
        try {
            runCurrent(); val old = model.state.value
            assertTrue(parked); assertSame(old, displayed(observed.last()))
            model.resume(story(old), old); runCurrent(); val current = model.state.value
            assertEquals(old, current); assertNotSame(old, current); assertEquals(2, port.resumes.size)
            releaseCollector.complete(Unit); runCurrent()
            assertSame("The actual library stream conflated a newly published equal idle owner", current, displayed(observed.last()))
            model.resume(story(current), displayed(observed.last())); runCurrent()
            assertEquals(3, port.resumes.size); assertFalse(model.state.value.busy)
        } finally { releaseCollector.complete(Unit); collector.cancel(); owners.clear(); runCurrent() }
    }

    @Test fun slowProductionCollectorReceivesEqualRecoveryOwnerAfterActualFailedRetry() = runTest(dispatcher) {
        val releaseCollector = CompletableDeferred<Unit>(); val port = Port(); val model = model(port)
        port.onRecover = { throw WorkspaceFailure("Full") }
        advanceUntilIdle(); model.submit(DemoAction.GIVE_POTION); advanceUntilIdle()
        val observed = mutableListOf<Any>(); var parked = false
        val collector = launch(StandardTestDispatcher(testScheduler)) {
            productionFlow(model).collect { frame ->
                observed += frame
                if (!parked && displayed(frame).recoveryRequired && !displayed(frame).busy) {
                    parked = true; releaseCollector.await()
                }
            }
        }
        try {
            runCurrent(); val old = model.state.value; assertTrue(parked)
            model.recover(old); runCurrent(); val current = model.state.value
            assertEquals(old, current); assertNotSame(old, current); assertEquals(1, port.recoveries)
            releaseCollector.complete(Unit); runCurrent()
            assertSame("The actual recovery stream retained the previous retry callback", current, displayed(observed.last()))
            model.recover(displayed(observed.last())); runCurrent()
            assertEquals(2, port.recoveries); assertTrue(model.state.value.recoveryRequired)
            assertEquals(History, model.state.value.messages); assertEquals(1, port.responses)
        } finally { releaseCollector.complete(Unit); collector.cancel(); owners.clear(); runCurrent() }
    }

    @Test fun currentPendingRecoveryKeepsAcceptedHistoryUntilItsAuthoritativeSnapshotAndIsNotRepeated() = runTest(dispatcher) {
        val release = CompletableDeferred<SavedSnapshot>(); val port = Port(); val model = model(port)
        port.onRecover = { withContext(NonCancellable) { release.await() } }
        try {
            advanceUntilIdle(); model.submit(DemoAction.GIVE_POTION); advanceUntilIdle(); val error = model.state.value
            model.recover(error); model.recover(error); runCurrent(); val pending = model.state.value
            assertTrue(pending.busy); assertEquals(History, pending.messages); assertEquals(Main, pending.selectedStory)
            model.recover(pending); model.resume(story(pending), pending); model.resumeTimeline(child(pending), pending); runCurrent()
            assertEquals(1, port.recoveries); assertTrue(port.resumes.isEmpty()); assertSame(pending, model.state.value)
            val returned = port.saved().copy(revision = 8, selected = Main.copy(revision = 8),
                messages = History + SceneMessage(2, "SCRIPTED recovered accepted receipt", false))
            release.complete(returned); advanceUntilIdle(); val recovered = model.state.value
            assertFalse(recovered.recoveryRequired); assertFalse(recovered.busy)
            assertEquals(returned.messages, recovered.messages); assertEquals(8L, recovered.revision)
            model.recover(error); model.recover(recovered); advanceUntilIdle()
            assertSame(recovered, model.state.value); assertEquals(1, port.recoveries)
            assertEquals(1, port.responses); assertTrue(port.resumes.isEmpty())
        } finally { release.complete(port.saved()); owners.clear(); runCurrent(); advanceUntilIdle() }
    }

    @Test fun failedRecoveryPreservesAcceptedHistoryAndRetiresItsPreviousRetryWithoutPrivateText() = runTest(dispatcher) {
        val port = Port(); val log = DiagnosticLog(); val model = model(port, log)
        port.onRecover = { throw IllegalStateException("PRIVATE recovery path and token") }
        advanceUntilIdle(); model.submit(DemoAction.GIVE_POTION); advanceUntilIdle(); val old = model.state.value
        model.recover(old); advanceUntilIdle(); val failed = model.state.value
        assertTrue(failed.recoveryRequired); assertFalse(failed.busy)
        assertEquals(Main, failed.selectedStory); assertEquals(History, failed.messages); assertEquals(7L, failed.revision)
        assertFalse(failed.notice.orEmpty().contains("PRIVATE")); assertFalse(log.snapshot().json.contains("PRIVATE"))
        val diagnostics = log.snapshot().json
        model.recover(old); model.resume(story(failed), failed); model.resumeTimeline(child(failed), failed); advanceUntilIdle()
        assertSame(failed, model.state.value); assertEquals(1, port.recoveries)
        assertEquals(diagnostics, log.snapshot().json); assertTrue(port.resumes.isEmpty())
        model.recover(failed); advanceUntilIdle(); assertEquals(2, port.recoveries)
        assertEquals(History, model.state.value.messages); assertEquals(1, port.responses)
    }

    @Test fun openingCancellationCheckCreationWorkflowAndDisposalKeepLibraryCallbacksQuiet() = runTest(dispatcher) {
        val opening = CompletableDeferred<SavedSnapshot>(); val ack = CompletableDeferred<SavedSnapshot>()
        val port = Port(); val model = model(port)
        port.onInitialize = { withContext(NonCancellable) { opening.await() } }
        port.onResponse = { awaitCancellation() }; port.onAck = { ack.await() }
        fun act(rendered: ShellState) {
            model.recover(rendered)
            model.resume(rendered.stories.firstOrNull() ?: Main, rendered)
            model.resumeTimeline(rendered.timelines.firstOrNull() ?: SavedTimeline(Main.story, "main", null, null, 7, 0), rendered)
        }
        try {
            runCurrent(); val starting = model.state.value; val openingCalls = calls(port)
            assertTrue(starting.busy); act(starting); runCurrent()
            assertSame(starting, model.state.value); assertEquals(openingCalls, calls(port))
            opening.complete(port.saved()); advanceUntilIdle()
            model.submit(DemoAction.GIVE_POTION); runCurrent(); model.cancel(); runCurrent()
            val checking = model.state.value; val checkingCalls = calls(port)
            assertTrue(checking.checkingCancellation); act(checking); runCurrent()
            assertSame(checking, model.state.value); assertEquals(checkingCalls, calls(port))
            ack.complete(port.saved()); advanceUntilIdle(); model.startNewStory(); advanceUntilIdle()
            val workflow = model.state.value; val workflowCalls = calls(port)
            assertTrue(workflow.creationActive); act(workflow); runCurrent()
            assertSame(workflow, model.state.value); assertEquals(workflowCalls, calls(port))
            owners.clear(); val disposed = model.state.value; val disposedCalls = calls(port)
            act(starting); act(checking); act(workflow); act(disposed); runCurrent()
            assertSame(disposed, model.state.value); assertEquals(disposedCalls, calls(port)); assertEquals(1, port.closes)
        } finally { opening.complete(port.saved()); ack.complete(port.saved()); owners.clear(); runCurrent(); advanceUntilIdle() }
    }

    private companion object {
        val Main = SavedStory("library-scope-main", "main", "SCRIPTED main library story", 7)
        val Other = SavedStory("library-scope-other", "main", "SCRIPTED other library story", 7)
        val Fork = Main.copy(branch = "fork")
        val History = listOf(SceneMessage(1, "SCRIPTED accepted history survives selection and recovery", false))
    }
}

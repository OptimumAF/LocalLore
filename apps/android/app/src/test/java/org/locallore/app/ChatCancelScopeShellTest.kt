/* Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0 */
package org.locallore.app

import androidx.lifecycle.ViewModelStore
import kotlinx.coroutines.CompletableDeferred
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.ExperimentalCoroutinesApi
import kotlinx.coroutines.NonCancellable
import kotlinx.coroutines.awaitCancellation
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

/** Real ShellViewModel ownership and observable scheduling over synthetic response/ACK ports. */
@OptIn(ExperimentalCoroutinesApi::class)
class ChatCancelScopeShellTest {
    private val dispatcher = StandardTestDispatcher()
    private val owners = ViewModelStore()
    private var modelCount = 0
    @Before fun before() { Dispatchers.setMain(dispatcher) }
    @After fun after() { owners.clear(); Dispatchers.resetMain() }

    /** The existing executable route supplies FIRST; a real member wins after implementation. */
    @Suppress("UNUSED_PARAMETER", "EXTENSION_SHADOWED_BY_MEMBER")
    private fun ShellViewModel.cancel(rendered: ShellState) = cancel()

    private data class Request(val kind: String, val selected: SavedStory, val revision: Long, val mode: DemoMode)
    private class Port : DemoGateway {
        override val durable = true
        var selected = Main
        var history = AcceptedHistory
        var cancels = 0
        var acknowledgements = 0
        var closes = 0
        var snapshots = 0
        val requests = mutableListOf<Request>()
        val commits = mutableListOf<DemoResult>()
        val resumes = mutableListOf<SavedStory>()
        var respond: suspend (Request) -> DemoResult = { awaitCancellation() }
        var acknowledge: suspend () -> SavedSnapshot = { saved() }
        var onCommit: suspend (DemoResult) -> DemoResult = { it }
        fun saved() = SavedSnapshot(selected.revision, "You", history, "D:/synthetic/chat-cancel.sqlite3", 1,
            listOf(Main, Other), selected, rulesProfile = "fantasy_v1", textProvider = TextProvider.SCRIPTED,
            databaseSchemaVersion = 5)
        override suspend fun initialize() = saved()
        override suspend fun snapshot(): SavedSnapshot { snapshots++; return saved() }
        override suspend fun resumeSaved(story: SavedStory): SavedSnapshot { resumes += story; selected = story; return saved() }
        override suspend fun respond(action: DemoAction, revision: Long, mode: DemoMode): DemoResult =
            prepare(Request(action.name, selected, revision, mode))
        override suspend fun respondText(input: PlayInput, revision: Long): DemoResult =
            prepare(Request(input.kind.wire, selected, revision, DemoMode.ACCEPTED))
        private suspend fun prepare(request: Request): DemoResult { requests += request; return respond(request) }
        override suspend fun commitAsync(result: DemoResult): DemoResult { commits += result; return onCommit(result) }
        override fun cancel() { cancels++ }
        override suspend fun cancelSaved(): SavedSnapshot { acknowledgements++; return acknowledge() }
        override fun close() { closes++ }
    }
    private fun model(port: Port, log: DiagnosticLog = DiagnosticLog()) = ShellViewModel(port, log).also {
        owners.put("chat-cancel-${modelCount++}", it)
    }
    private fun payload(state: ShellState) = listOf(state.selectedStory, state.revision, state.busy,
        state.preparingResponse, state.mode, state.potionOwner, state.messages)
    private fun completedCancellation(log: DiagnosticLog) =
        log.snapshot().json.contains("\"phase\":\"CANCEL\",\"outcome\":\"COMPLETED\"")

    @Test fun equalCopyForeignResponseAndIdleRenderCannotCancelTheCurrentResponseOrWriteDiagnostics() = runTest(dispatcher) {
        val violations = mutableListOf<String>()
        for (kind in listOf("copy", "foreign", "idle")) {
            val port = Port(); val log = DiagnosticLog(); val model = model(port, log)
            val other = model(Port())
            try {
                advanceUntilIdle(); val idle = model.state.value
                model.submit(DemoAction.GIVE_POTION); other.submit(DemoAction.GIVE_POTION); runCurrent()
                val current = model.state.value
                val rendered = when (kind) {
                    "copy" -> current.copy()
                    "foreign" -> other.state.value
                    else -> idle
                }
                assertNotSame(current, rendered)
                if (kind == "copy") assertEquals(current, rendered)
                val diagnostics = log.snapshot().json
                model.cancel(rendered); runCurrent()
                if (port.cancels != 0 || port.acknowledgements != 0 || model.state.value !== current ||
                    log.snapshot().json != diagnostics) violations += kind
                assertEquals(1, port.requests.size); assertTrue(port.commits.isEmpty())
            } finally { owners.clear(); runCurrent() }
        }
        assertEquals("An unowned rendered chat view acquired current cancellation authority", emptyList<String>(), violations)
    }

    @Test fun rejectedPriorResponseCloseCannotCancelANewTextTurnAtTheSameHead() = runTest(dispatcher) {
        val first = CompletableDeferred<DemoResult>(); val port = Port(); val log = DiagnosticLog()
        port.respond = { if (port.requests.size == 1) first.await() else awaitCancellation() }
        val model = model(port, log)
        try {
            advanceUntilIdle(); model.submit(DemoAction.TRY_ABILITY); runCurrent(); val old = model.state.value
            first.complete(DemoResult.Rejected("Ability")); advanceUntilIdle()
            assertFalse(model.state.value.busy); assertEquals(Main.revision, model.state.value.revision)
            model.submitText(PlayInput(PlayInputKind.DIALOGUE, "May I ask about the quay?"), Main); runCurrent()
            val current = model.state.value
            assertEquals(payload(old), payload(current)); assertNotSame(old, current)
            val diagnostics = log.snapshot().json
            model.cancel(old); runCurrent()
            assertSame(current, model.state.value); assertEquals(diagnostics, log.snapshot().json)
            assertEquals(0, port.cancels); assertEquals(0, port.acknowledgements)
            assertEquals(listOf("TRY_ABILITY", "dialogue"), port.requests.map { it.kind })
            assertTrue(port.commits.isEmpty())
        } finally { first.complete(DemoResult.Rejected("Ability")); owners.clear(); runCurrent() }
    }

    @Test fun cancelledAndAcknowledgedTurnCannotCancelTheNextBusyOwnerAtTheSameHead() = runTest(dispatcher) {
        val acknowledgement = CompletableDeferred<SavedSnapshot>(); val port = Port(); val log = DiagnosticLog()
        port.acknowledge = { acknowledgement.await() }
        val model = model(port, log)
        try {
            advanceUntilIdle(); model.submit(DemoAction.GIVE_POTION); runCurrent(); val old = model.state.value
            model.cancel(old); runCurrent(); assertTrue(model.state.value.checkingCancellation)
            acknowledgement.complete(port.saved()); advanceUntilIdle()
            assertTrue(completedCancellation(log)); assertFalse(model.state.value.busy)
            model.submit(DemoAction.GIVE_POTION); runCurrent(); val current = model.state.value
            assertEquals(payload(old), payload(current)); assertNotSame(old, current)
            val diagnostics = log.snapshot().json
            model.cancel(old); runCurrent()
            assertSame(current, model.state.value); assertEquals(diagnostics, log.snapshot().json)
            assertEquals(1, port.cancels); assertEquals(1, port.acknowledgements); assertEquals(2, port.requests.size)
            model.cancel(current); advanceUntilIdle()
            assertEquals(2, port.cancels); assertEquals(2, port.acknowledgements)
            assertFalse(model.state.value.busy); assertFalse(model.state.value.recoveryRequired)
        } finally { acknowledgement.complete(port.saved()); owners.clear(); runCurrent() }
    }

    @Test fun oldStoryAndBranchResponseViewsCannotCancelACompatibleNewSelection() = runTest(dispatcher) {
        val violations = mutableListOf<String>()
        for (target in listOf(Other, Fork)) {
            val port = Port(); val first = CompletableDeferred<DemoResult>(); val log = DiagnosticLog()
            port.respond = { if (port.requests.size == 1) first.await() else awaitCancellation() }
            val model = model(port, log)
            try {
                advanceUntilIdle(); model.submit(DemoAction.GIVE_POTION); runCurrent(); val old = model.state.value
                first.complete(DemoResult.Rejected("Inventory")); advanceUntilIdle()
                model.resume(target); advanceUntilIdle()
                assertEquals(target, model.state.value.selectedStory)
                model.submit(DemoAction.GIVE_POTION); runCurrent(); val current = model.state.value
                assertEquals(old.revision, current.revision)
                val diagnostics = log.snapshot().json
                model.cancel(old); runCurrent()
                if (model.state.value !== current || port.cancels != 0 || port.acknowledgements != 0 ||
                    log.snapshot().json != diagnostics) violations += "${target.story}/${target.branch}"
                assertEquals(listOf(Main, target), port.requests.map { it.selected })
                assertEquals(listOf(target), port.resumes); assertTrue(port.commits.isEmpty())
            } finally { first.complete(DemoResult.Rejected("Inventory")); owners.clear(); runCurrent() }
        }
        assertEquals("A previous story/branch Cancel affected the newly selected response", emptyList<String>(), violations)
    }

    @Test fun slowActualStateCollectorReceivesTheNewEqualPayloadBusyOwnerAfterCancelAck() = runTest(dispatcher) {
        val releaseCollector = CompletableDeferred<Unit>(); val port = Port(); val model = model(port)
        val observed = mutableListOf<ShellState>(); var parked = false
        val collector = launch(StandardTestDispatcher(testScheduler)) {
            model.state.collect { state ->
                observed += state
                if (!parked && state.busy && state.preparingResponse) {
                    parked = true; releaseCollector.await()
                }
            }
        }
        try {
            advanceUntilIdle(); model.submit(DemoAction.GIVE_POTION); runCurrent(); val old = model.state.value
            assertTrue(parked); assertSame(old, observed.last())
            model.cancel(old); runCurrent(); assertFalse(model.state.value.busy)
            assertEquals(1, port.acknowledgements)
            model.submit(DemoAction.GIVE_POTION); runCurrent(); val current = model.state.value
            assertEquals(payload(old), payload(current)); assertNotSame(old, current)
            releaseCollector.complete(Unit); runCurrent()
            assertSame("A slow actual VM collector retained the first response's Cancel callback", current, observed.last())
            model.cancel(observed.last()); runCurrent()
            assertEquals(2, port.cancels); assertEquals(2, port.acknowledgements)
            assertFalse(model.state.value.busy); assertTrue(port.commits.isEmpty())
        } finally { releaseCollector.complete(Unit); collector.cancel(); owners.clear(); runCurrent() }
    }

    @Test fun currentCancelWaitsForAckAndNeitherOldResponseNorAckViewCanCancelAgain() = runTest(dispatcher) {
        val acknowledgement = CompletableDeferred<SavedSnapshot>(); val port = Port(); val log = DiagnosticLog()
        port.acknowledge = { acknowledgement.await() }; val model = model(port, log)
        try {
            advanceUntilIdle(); model.submit(DemoAction.GIVE_POTION); runCurrent(); val current = model.state.value
            model.cancel(current); runCurrent(); val checking = model.state.value
            assertTrue(checking.busy); assertTrue(checking.checkingCancellation); assertFalse(checking.preparingResponse)
            assertEquals(1, port.cancels); assertEquals(1, port.acknowledgements)
            assertFalse(completedCancellation(log))
            val diagnostics = log.snapshot().json
            model.cancel(current); model.cancel(checking); runCurrent()
            assertSame(checking, model.state.value); assertEquals(diagnostics, log.snapshot().json)
            assertEquals(1, port.cancels); assertEquals(1, port.acknowledgements)
            acknowledgement.complete(port.saved()); advanceUntilIdle()
            assertTrue(completedCancellation(log)); assertFalse(model.state.value.busy)
            assertFalse(model.state.value.recoveryRequired); assertEquals(AcceptedHistory, model.state.value.messages)
        } finally { acknowledgement.complete(port.saved()); owners.clear(); runCurrent() }
    }

    @Test fun failedCurrentAckStaysUnknownAndRecoveryFencedWithoutACompletedCancelOrRetry() = runTest(dispatcher) {
        val acknowledgement = CompletableDeferred<SavedSnapshot>(); val port = Port(); val log = DiagnosticLog()
        port.acknowledge = { acknowledgement.await() }; val model = model(port, log)
        try {
            advanceUntilIdle(); model.submit(DemoAction.GIVE_POTION); runCurrent()
            model.cancel(model.state.value); runCurrent()
            acknowledgement.completeExceptionally(IllegalStateException("PRIVATE ACK transport detail")); advanceUntilIdle()
            val unknown = model.state.value; val diagnostics = log.snapshot().json
            assertTrue(unknown.recoveryRequired); assertFalse(unknown.busy); assertEquals(AcceptedHistory, unknown.messages)
            assertFalse(completedCancellation(log))
            assertTrue(diagnostics.contains("\"phase\":\"CANCEL\",\"outcome\":\"UNKNOWN\""))
            assertFalse(diagnostics.contains("PRIVATE")); assertFalse(unknown.notice.orEmpty().contains("PRIVATE"))
            model.cancel(unknown); model.submit(DemoAction.GIVE_POTION); runCurrent()
            assertSame(unknown, model.state.value); assertEquals(diagnostics, log.snapshot().json)
            assertEquals(1, port.cancels); assertEquals(1, port.acknowledgements); assertEquals(1, port.requests.size)
        } finally { acknowledgement.complete(port.saved()); owners.clear(); runCurrent() }
    }

    @Test fun currentCancelReconcilesACommitThatWinsWithoutInventingRollbackOrAnotherCommit() = runTest(dispatcher) {
        val releaseCommit = CompletableDeferred<Unit>(); val committed = CompletableDeferred<Unit>(); val port = Port()
        val log = DiagnosticLog(); val accepted = SceneMessage(2, "SCRIPTED accepted outcome won the race", false)
        port.respond = { DemoResult.Prepared(71, 3) }
        port.onCommit = {
            withContext(NonCancellable) {
                releaseCommit.await(); port.selected = Main.copy(revision = Main.revision + 1)
                port.history = AcceptedHistory + accepted; committed.complete(Unit)
            }
            DemoResult.Accepted(Main.revision + 1, "You", accepted.text)
        }
        port.acknowledge = { committed.await(); port.saved() }
        val model = model(port, log)
        try {
            advanceUntilIdle(); model.submit(DemoAction.GIVE_POTION); runCurrent()
            assertEquals(1, port.commits.size); val committing = model.state.value
            model.cancel(committing); runCurrent()
            assertTrue(model.state.value.checkingCancellation); assertFalse(completedCancellation(log))
            releaseCommit.complete(Unit); advanceUntilIdle()
            assertEquals(Main.revision + 1, model.state.value.revision)
            assertEquals(Main.copy(revision = Main.revision + 1), model.state.value.selectedStory)
            assertEquals(AcceptedHistory + accepted, model.state.value.messages)
            assertTrue(completedCancellation(log)); assertFalse(model.state.value.recoveryRequired)
            model.cancel(committing); runCurrent()
            assertEquals(1, port.commits.size); assertEquals(1, port.cancels); assertEquals(1, port.acknowledgements)
        } finally {
            releaseCommit.complete(Unit); committed.complete(Unit); owners.clear(); runCurrent(); advanceUntilIdle()
        }
    }

    @Test fun lateNoncooperativeOldPreparationCannotAttachToOrCancelANewerResponse() = runTest(dispatcher) {
        val releaseOld = CompletableDeferred<Unit>(); val port = Port(); val log = DiagnosticLog()
        port.respond = {
            if (port.requests.size == 1) withContext(NonCancellable) {
                releaseOld.await(); DemoResult.Accepted(Main.revision + 1, "Mira", "SCRIPTED obsolete result")
            } else awaitCancellation()
        }
        val model = model(port, log)
        try {
            advanceUntilIdle(); model.submit(DemoAction.GIVE_POTION); runCurrent(); val old = model.state.value
            model.cancel(old); runCurrent(); assertFalse(model.state.value.busy)
            model.submit(DemoAction.TRY_ABILITY); runCurrent(); val current = model.state.value
            releaseOld.complete(Unit); runCurrent()
            assertSame(current, model.state.value); assertEquals(AcceptedHistory, current.messages)
            assertEquals(Main.revision, current.revision); assertTrue(port.commits.isEmpty())
            val diagnostics = log.snapshot().json
            model.cancel(old); runCurrent()
            assertSame(current, model.state.value); assertEquals(diagnostics, log.snapshot().json)
            assertEquals(1, port.cancels); assertEquals(1, port.acknowledgements)
            assertEquals(2, port.requests.size)
        } finally { releaseOld.complete(Unit); owners.clear(); runCurrent(); advanceUntilIdle() }
    }

    @Test fun disposedResponseIdleAndCopiedCallbacksCannotCancelOrPublishLateWork() = runTest(dispatcher) {
        val release = CompletableDeferred<Unit>(); val port = Port(); val log = DiagnosticLog()
        port.respond = { withContext(NonCancellable) { release.await(); DemoResult.Accepted(Main.revision + 1, "Mira", "Late") } }
        val model = model(port, log)
        try {
            advanceUntilIdle(); val idle = model.state.value
            model.submit(DemoAction.GIVE_POTION); runCurrent(); val busy = model.state.value
            owners.clear(); val disposed = model.state.value; val diagnostics = log.snapshot().json
            model.cancel(busy); model.cancel(busy.copy()); model.cancel(idle); model.cancel(disposed)
            model.submit(DemoAction.GIVE_POTION); release.complete(Unit); runCurrent(); advanceUntilIdle()
            assertSame(disposed, model.state.value); assertEquals(diagnostics, log.snapshot().json)
            assertFalse(disposed.busy); assertEquals(Main.revision, disposed.revision)
            assertEquals(AcceptedHistory, disposed.messages); assertEquals(1, port.closes)
            assertEquals(0, port.cancels); assertEquals(0, port.acknowledgements)
            assertEquals(1, port.requests.size); assertTrue(port.commits.isEmpty())
        } finally { release.complete(Unit); owners.clear(); runCurrent(); advanceUntilIdle() }
    }

    private companion object {
        val Main = SavedStory("chat-cancel-main", "main", "SCRIPTED main story", 7)
        val Other = SavedStory("chat-cancel-other", "main", "SCRIPTED other story", 7)
        val Fork = Main.copy(branch = "fork")
        val AcceptedHistory = listOf(SceneMessage(1, "SCRIPTED existing accepted history", false))
    }
}

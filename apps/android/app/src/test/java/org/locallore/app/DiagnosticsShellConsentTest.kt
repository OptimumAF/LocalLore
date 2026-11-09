/* Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0 */
package org.locallore.app

import androidx.lifecycle.ViewModelStore
import kotlinx.coroutines.CancellationException
import kotlinx.coroutines.CompletableDeferred
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.ExperimentalCoroutinesApi
import kotlinx.coroutines.NonCancellable
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

/** Actual ShellViewModel and consent binder; scripted gateway, no Android provider/native engine. */
@OptIn(ExperimentalCoroutinesApi::class)
class DiagnosticsShellConsentTest {
    private val dispatcher = StandardTestDispatcher()
    private val models = ViewModelStore()
    private var nextModel = 0
    private val privateMarker = "PRIVATE-SHELL-CONSENT-CANARY"

    @Before fun setup() { Dispatchers.setMain(dispatcher) }
    @After fun cleanup() { models.clear(); Dispatchers.resetMain() }

    private class Gateway(private val saved: SavedSnapshot) : DemoGateway {
        override val durable = true
        var initializes = 0
        var responds = 0
        var closes = 0
        override suspend fun initialize(): SavedSnapshot { initializes++; return saved }
        override suspend fun respond(action: DemoAction, revision: Long, mode: DemoMode): DemoResult {
            responds++
            return DemoResult.Rejected("Rule")
        }
        override fun close() { closes++ }
    }

    private inner class Harness {
        val log = DiagnosticLog()
        val story = SavedStory("synthetic-consent", "main", privateMarker, 0)
        val saved = SavedSnapshot(0, "You", emptyList(), "/synthetic/$privateMarker/stories.sqlite3",
            1, listOf(story), story, databaseSchemaVersion = 2)
        val gateway = Gateway(saved)
        var forkCalls = 0
        val model = ShellViewModel(gateway, log, forkContextProvider = { selected, revision, _ ->
            assertEquals(story, selected)
            assertEquals(0L, revision)
            forkCalls++
            null
        }).also { models.put("diagnostic-shell-${nextModel++}", it) }

        fun controls(state: DiagnosticsUiState, launch: () -> Unit = {}): DiagnosticsActions = diagnosticsActions(
            state.review,
            onDismiss = model::closeDiagnostics,
            onClear = model::clearDiagnostics,
            onExport = { if (model.beginDiagnosticExport(it)) launch() },
        )
    }

    @Test fun retainedBinderExportCannotStartPickerOrWriteNewViewModelReview() = runTest(dispatcher) {
        val h = Harness(); advanceUntilIdle()
        h.log.record(DiagnosticPhase.PREPARE, DiagnosticOutcome.PREPARED, 1)
        h.model.openDiagnostics()
        val first = h.model.diagnostics.value
        var launches = 0
        val retained = h.controls(first) { launches++ }
        h.log.record(DiagnosticPhase.COMMIT, DiagnosticOutcome.ACCEPTED, 2)
        h.model.openDiagnostics()
        val current = h.model.diagnostics.value
        val shell = h.model.state.value
        assertNotSame(first.review, current.review)
        assertNotEquals(first.preview, current.preview)
        retained.export()
        var writes = 0
        h.model.completeDiagnosticExport { writes++ }
        advanceUntilIdle()
        assertEquals("Scoped VM export wrapper borrowed the replacement", 0, launches)
        assertEquals(0, writes)
        assertSame(current, h.model.diagnostics.value)
        assertEquals(shell, h.model.state.value)
        assertEquals(0, h.gateway.responds)

        h.controls(current) { launches++ }.export()
        var written = ""
        h.model.completeDiagnosticExport { written = it.toString(Charsets.UTF_8); writes++; it.fill(0) }
        h.model.completeDiagnosticExport { writes += 100 }
        advanceUntilIdle()
        assertEquals(1, launches)
        assertEquals(1, writes)
        assertEquals(current.preview, written)
        assertFalse(written.contains(privateMarker))
    }

    @Test fun retainedBinderClearCannotEraseReplacementRecordsThroughViewModel() = runTest(dispatcher) {
        val h = Harness(); advanceUntilIdle()
        h.model.openDiagnostics()
        val retained = h.controls(h.model.diagnostics.value)
        h.model.clearDiagnostics() // Owner refresh establishes a distinct review.
        val current = h.model.diagnostics.value
        h.log.record(DiagnosticPhase.COMMIT, DiagnosticOutcome.COMPLETED, 3)
        val log = h.log.snapshot().json
        val shell = h.model.state.value
        val contexts = h.forkCalls
        retained.clear()
        assertEquals("Scoped VM Clear discarded the newer log", log, h.log.snapshot().json)
        assertSame(current, h.model.diagnostics.value)
        assertEquals(shell, h.model.state.value)
        assertEquals(contexts, h.forkCalls)
        h.controls(current).clear()
        assertNotSame(current.review, h.model.diagnostics.value.review)
        assertTrue(h.log.snapshot().json.contains("\"count\":0"))
        assertEquals(0, h.gateway.responds)
    }

    @Test fun retainedBinderDismissCannotCancelReplacementExportOrRefreshForkContext() = runTest(dispatcher) {
        val h = Harness(); advanceUntilIdle()
        val release = CompletableDeferred<Unit>()
        var writerClosed = false
        try {
            h.model.openDiagnostics()
            val retained = h.controls(h.model.diagnostics.value)
            h.log.record(DiagnosticPhase.RESET, DiagnosticOutcome.COMPLETED, 4)
            h.model.openDiagnostics()
            val current = h.model.diagnostics.value
            h.controls(current).export()
            h.model.completeDiagnosticExport {
                try { withContext(NonCancellable) { release.await() } }
                finally { writerClosed = true }
            }
            runCurrent()
            val busy = h.model.diagnostics.value
            val contexts = h.forkCalls
            assertTrue(busy.exporting)
            retained.dismiss()
            assertSame("Scoped VM Close dismissed another review", busy, h.model.diagnostics.value)
            assertEquals(contexts, h.forkCalls)
            assertFalse(writerClosed)
            release.complete(Unit); advanceUntilIdle()
            assertTrue(writerClosed)
            assertTrue(h.model.diagnostics.value.visible)
            assertSame(current.review, h.model.diagnostics.value.review)
            assertTrue(h.model.diagnostics.value.notice!!.contains("Reviewed diagnostics exported"))
        } finally {
            release.complete(Unit)
            models.clear()
            advanceUntilIdle()
        }
    }

    @Test fun staleCloseAfterOwnerClosureCannotInvokeTheForkContextProvider() = runTest(dispatcher) {
        val h = Harness(); advanceUntilIdle()
        assertTrue("Provider port must actually be reachable with this saved fixture", h.forkCalls > 0)
        h.model.openDiagnostics()
        val reviewed = h.model.diagnostics.value
        val retained = h.controls(reviewed)
        val beforeOwnerClose = h.forkCalls
        h.model.closeDiagnostics()
        assertEquals("Legitimate owner Close must still synchronize", beforeOwnerClose + 1, h.forkCalls)
        val closed = h.model.diagnostics.value
        val shell = h.model.state.value
        val log = h.log.snapshot().json
        val afterOwnerClose = h.forkCalls
        retained.dismiss()
        retained.dismiss()
        assertEquals("Rejected scoped Close recomputed fork context while diagnostics were already closed",
            afterOwnerClose, h.forkCalls)
        assertSame(closed, h.model.diagnostics.value)
        assertEquals(shell, h.model.state.value)
        assertEquals(log, h.log.snapshot().json)
        assertEquals(0, h.gateway.responds)
    }

    @Test fun equalJsonAndForeignReviewCannotAuthorizeTheCurrentViewModel() = runTest(dispatcher) {
        val h = Harness(); val foreign = Harness(); advanceUntilIdle()
        h.model.openDiagnostics()
        val first = h.model.diagnostics.value
        h.model.closeDiagnostics()
        h.model.openDiagnostics(); foreign.model.openDiagnostics()
        val current = h.model.diagnostics.value
        assertEquals(first.preview, current.preview)
        assertEquals(foreign.model.diagnostics.value.preview, current.preview)
        assertNotSame(first.review, current.review)
        var launches = 0
        for (unrelated in listOf(first, foreign.model.diagnostics.value,
                current.copy(review = DiagnosticsReview()))) {
            val controls = h.controls(unrelated) { launches++ }
            controls.export(); controls.clear(); controls.dismiss()
            assertEquals(0, launches)
            assertSame(current, h.model.diagnostics.value)
        }
        assertTrue(h.model.beginDiagnosticExport(current.copy().review))
        h.model.completeDiagnosticExport(null)
        assertSame(current.review, h.model.diagnostics.value.review)
        assertEquals(0, h.gateway.responds)
        assertEquals(0, foreign.gateway.responds)
    }

    @Test fun currentViewModelReviewExportsFrozenBytesAndSanitizesFailureAndCancellation() = runTest(dispatcher) {
        val h = Harness(); advanceUntilIdle()
        h.log.record(DiagnosticPhase.PREPARE, DiagnosticOutcome.REJECTED, 6, DiagnosticError.INVENTORY)
        h.model.openDiagnostics()
        val current = h.model.diagnostics.value
        val controls = h.controls(current)
        val shell = h.model.state.value
        controls.export()
        h.log.record(DiagnosticPhase.RESET, DiagnosticOutcome.COMPLETED, 7)
        var written = ""
        h.model.completeDiagnosticExport {
            written = it.toString(Charsets.UTF_8)
            throw IllegalStateException("$privateMarker content://synthetic/private/file")
        }
        advanceUntilIdle()
        assertEquals(current.preview, written)
        assertFalse(written.contains(privateMarker))
        assertFalse(h.log.snapshot().json.contains(privateMarker))
        assertFalse(h.model.diagnostics.value.notice!!.contains(privateMarker))
        assertTrue(h.model.diagnostics.value.notice!!.contains("incomplete file"))
        assertSame(current.review, h.model.diagnostics.value.review)

        controls.export() // Notice/busy copies keep the same legitimate review.
        var effectOccurred = false
        h.model.completeDiagnosticExport {
            effectOccurred = true
            throw CancellationException(privateMarker)
        }
        advanceUntilIdle()
        assertTrue(effectOccurred)
        assertTrue(h.model.diagnostics.value.notice!!.contains("incomplete file"))
        assertFalse(h.model.diagnostics.value.notice!!.contains("Nothing was written"))
        assertFalse(h.log.snapshot().json.contains(privateMarker))
        assertEquals(shell, h.model.state.value)
        assertEquals(0, h.gateway.responds)
    }

    @Test fun disposedViewModelRejectsRetainedActionsAndReturnedPickerWithoutWriting() = runTest(dispatcher) {
        val h = Harness(); advanceUntilIdle()
        h.log.record(DiagnosticPhase.RESET, DiagnosticOutcome.COMPLETED, 8)
        h.model.openDiagnostics()
        val current = h.model.diagnostics.value
        var launches = 0
        val controls = h.controls(current) { launches++ }
        controls.export()
        assertEquals(1, launches)
        models.clear()
        val disposed = h.model.diagnostics.value
        val contexts = h.forkCalls
        var writes = 0
        h.model.completeDiagnosticExport { writes++ }
        controls.export(); controls.clear(); controls.dismiss()
        advanceUntilIdle()
        assertEquals(1, launches)
        assertEquals(0, writes)
        assertSame(disposed, h.model.diagnostics.value)
        assertEquals(contexts, h.forkCalls)
        assertTrue(h.log.snapshot().json.contains("\"count\":0"))
        assertEquals(1, h.gateway.closes)
        assertEquals(0, h.gateway.responds)
    }

    @Test fun viewModelPickerTombstonePreventsOldResultFromWritingReplacementReview() = runTest(dispatcher) {
        val h = Harness(); advanceUntilIdle()
        h.model.openDiagnostics()
        val first = h.model.diagnostics.value
        val controls = h.controls(first)
        controls.export()
        controls.dismiss()
        h.model.openDiagnostics()
        val current = h.model.diagnostics.value
        assertNotSame(first.review, current.review)
        assertFalse(h.model.beginDiagnosticExport(current.review))
        var writes = 0
        h.model.completeDiagnosticExport { writes++ }
        advanceUntilIdle()
        assertEquals(0, writes)
        assertTrue(h.model.beginDiagnosticExport(current.review))
        var payload = ""
        h.model.completeDiagnosticExport { writes++; payload = it.toString(Charsets.UTF_8) }
        h.model.completeDiagnosticExport { writes += 100 }
        advanceUntilIdle()
        assertEquals(1, writes)
        assertEquals(current.preview, payload)
        assertEquals(0, h.gateway.responds)
    }
}

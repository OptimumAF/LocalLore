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

/** Real controller and pure UI binder; no provider, URI, native engine or device authority. */
@OptIn(ExperimentalCoroutinesApi::class)
class DiagnosticsReviewActionsTest {
    private fun actions(
        controller: DiagnosticsController,
        state: DiagnosticsUiState,
        launched: () -> Unit = {},
    ): DiagnosticsActions = diagnosticsActions(
        state.review,
        onDismiss = { controller.dismiss(it) },
        onClear = { controller.clear(it) },
        onExport = { if (controller.beginExport(it)) launched() },
    )

    @Test fun retainedExportCannotLaunchOrWriteTheReplacementReviewButCurrentConsentWorks() = runTest {
        val log = DiagnosticLog()
        log.record(DiagnosticPhase.PREPARE, DiagnosticOutcome.PREPARED, 1)
        val controller = DiagnosticsController(log, this)
        try {
            controller.open()
            val first = controller.state.value
            var launches = 0
            val retained = actions(controller, first) { launches++ }
            log.record(DiagnosticPhase.COMMIT, DiagnosticOutcome.ACCEPTED, 2)
            controller.open()
            val replacement = controller.state.value
            assertNotSame(first.review, replacement.review)
            assertNotEquals(first.preview, replacement.preview)
            retained.export()
            var writes = 0
            controller.completeExport { writes++ }
            advanceUntilIdle()
            assertEquals("Old export event launched a picker for the unreviewed replacement", 0, launches)
            assertEquals(0, writes)
            assertSame(replacement, controller.state.value)

            actions(controller, replacement) { launches++ }.export()
            log.record(DiagnosticPhase.RESET, DiagnosticOutcome.COMPLETED, 3)
            var payload = ""
            controller.completeExport { payload = it.toString(Charsets.UTF_8); writes++; it.fill(0) }
            controller.completeExport { writes += 100 }
            advanceUntilIdle()
            assertEquals(1, launches)
            assertEquals(1, writes)
            assertEquals(replacement.preview, payload)
            assertNotEquals(log.snapshot().json, payload)
        } finally { controller.dispose() }
    }

    @Test fun retainedClearCannotEraseNewRecordsOrReplaceTheCurrentReview() = runTest {
        val log = DiagnosticLog()
        log.record(DiagnosticPhase.PREPARE, DiagnosticOutcome.REJECTED, 1, DiagnosticError.RULE)
        val controller = DiagnosticsController(log, this)
        try {
            controller.open()
            val retained = actions(controller, controller.state.value)
            controller.clear() // A real current owner refresh replaces the old review.
            val replacement = controller.state.value
            log.record(DiagnosticPhase.COMMIT, DiagnosticOutcome.COMPLETED, 4)
            val before = log.snapshot().json
            retained.clear()
            assertEquals("Old Clear erased records belonging to the replacement review", before, log.snapshot().json)
            assertSame(replacement, controller.state.value)
            assertTrue(controller.clear(replacement.review))
            assertTrue(log.snapshot().json.contains("\"count\":0"))
            assertNotSame(replacement.review, controller.state.value.review)
        } finally { controller.dispose() }
    }

    @Test fun retainedDismissCannotHideOrCancelTheReplacementReviewsActiveExport() = runTest {
        val log = DiagnosticLog()
        val controller = DiagnosticsController(log, this)
        val release = CompletableDeferred<Unit>()
        var writerFinished = false
        try {
            controller.open()
            val retained = actions(controller, controller.state.value)
            log.record(DiagnosticPhase.RESET, DiagnosticOutcome.COMPLETED, 1)
            controller.open()
            val replacement = controller.state.value
            assertTrue(controller.beginExport(replacement.review))
            controller.completeExport {
                try { withContext(NonCancellable) { release.await() } }
                finally { writerFinished = true }
            }
            runCurrent()
            val exporting = controller.state.value
            assertTrue(exporting.exporting)
            retained.dismiss()
            assertSame("Old dismissal changed the replacement export state", exporting, controller.state.value)
            assertTrue(controller.state.value.visible)
            assertFalse(writerFinished)
            release.complete(Unit)
            advanceUntilIdle()
            assertTrue(writerFinished)
            assertTrue(controller.state.value.visible)
            assertFalse(controller.state.value.exporting)
            assertSame(replacement.review, controller.state.value.review)
            assertTrue(controller.state.value.notice!!.contains("Reviewed diagnostics exported"))
        } finally {
            release.complete(Unit)
            controller.dispose()
            advanceUntilIdle()
        }
    }

    @Test fun equalJsonReopenAndForeignReviewsDoNotBorrowCurrentConsent() = runTest {
        val controller = DiagnosticsController(DiagnosticLog(), this)
        val foreign = DiagnosticsController(DiagnosticLog(), this)
        try {
            controller.open()
            val first = controller.state.value
            controller.dismiss()
            controller.open()
            foreign.open()
            val current = controller.state.value
            assertEquals(first.preview, current.preview)
            assertEquals(foreign.state.value.preview, current.preview)
            assertNotSame(first.review, current.review)
            assertNotSame(foreign.state.value.review, current.review)
            for (unrelated in listOf(first.review, foreign.state.value.review, DiagnosticsReview())) {
                assertFalse(controller.beginExport(unrelated))
                assertFalse(controller.clear(unrelated))
                assertFalse(controller.dismiss(unrelated))
                assertSame(current, controller.state.value)
            }
            // DTO copies retain the same legitimate immutable review identity.
            assertSame(current.review, current.copy().review)
            assertTrue(controller.beginExport(current.copy().review))
            controller.completeExport(null)
            assertSame(current.review, controller.state.value.review)
        } finally { controller.dispose(); foreign.dispose() }
    }

    @Test fun clearingAnAlreadyEmptySnapshotStillRetiresItsOldActions() = runTest {
        val controller = DiagnosticsController(DiagnosticLog(), this)
        try {
            controller.open()
            val first = controller.state.value
            var launches = 0
            val retained = actions(controller, first) { launches++ }
            assertTrue(controller.clear(first.review))
            val refreshed = controller.state.value
            assertEquals(first.preview, refreshed.preview)
            assertNotSame(first.review, refreshed.review)
            retained.export()
            retained.clear()
            retained.dismiss()
            assertEquals(0, launches)
            assertSame(refreshed, controller.state.value)
            actions(controller, refreshed) { launches++ }.export()
            assertEquals(1, launches)
            controller.completeExport(null)
        } finally { controller.dispose() }
    }

    @Test fun currentReviewSurvivesBusyAndNoticeCopiesThenChangesOnlyOnExplicitRefresh() = runTest {
        val log = DiagnosticLog()
        log.record(DiagnosticPhase.CANCEL, DiagnosticOutcome.CANCELLED, 5)
        val controller = DiagnosticsController(log, this)
        try {
            controller.open()
            val reviewed = controller.state.value
            assertTrue(controller.beginExport(reviewed.review))
            assertSame(reviewed.review, controller.state.value.review)
            var payload = ""
            controller.completeExport { payload = it.toString(Charsets.UTF_8) }
            advanceUntilIdle()
            assertEquals(reviewed.preview, payload)
            assertSame(reviewed.review, controller.state.value.review)
            assertTrue(controller.state.value.notice!!.contains("Reviewed diagnostics exported"))
            assertTrue(controller.clear(reviewed.review))
            val fresh = controller.state.value
            assertNotSame(reviewed.review, fresh.review)
            assertFalse(controller.beginExport(reviewed.review))
            assertTrue(controller.beginExport(fresh.review))
            controller.completeExport(null)
            assertSame(fresh.review, controller.state.value.review)
        } finally { controller.dispose() }
    }

    @Test fun currentReviewDismissesItsOwnBusyWriterAndLateCompletionCannotReplaceReopenedReview() = runTest {
        val controller = DiagnosticsController(DiagnosticLog(), this)
        val release = CompletableDeferred<Unit>()
        var writerClosed = false
        try {
            controller.open()
            val current = controller.state.value
            val controls = actions(controller, current)
            controls.export()
            controller.completeExport {
                try { withContext(NonCancellable) { release.await() } }
                finally { writerClosed = true }
            }
            runCurrent()
            assertTrue(controller.state.value.exporting)
            assertSame(current.review, controller.state.value.review)
            controls.dismiss() // Current consent must remain usable across busy-state copies.
            assertFalse(controller.state.value.visible)
            controller.open()
            val replacement = controller.state.value
            assertNotSame(current.review, replacement.review)
            release.complete(Unit)
            advanceUntilIdle()
            assertTrue(writerClosed)
            assertSame(replacement, controller.state.value)
        } finally {
            release.complete(Unit)
            controller.dispose()
            advanceUntilIdle()
        }
    }

    @Test fun scopedRevocationStillDrainsTheOldPickerBeforeNewConsentCanWrite() = runTest {
        val controller = DiagnosticsController(DiagnosticLog(), this)
        try {
            controller.open()
            val first = controller.state.value
            assertTrue(controller.beginExport(first.review))
            assertTrue(controller.dismiss(first.review))
            controller.open()
            val replacement = controller.state.value
            assertNotSame(first.review, replacement.review)
            assertFalse(controller.beginExport(replacement.review))
            var writes = 0
            controller.completeExport { writes++ } // Drain revoked picker; never invoke writer.
            advanceUntilIdle()
            assertEquals(0, writes)
            assertTrue(controller.beginExport(replacement.review))
            var written = ""
            controller.completeExport { writes++; written = it.toString(Charsets.UTF_8) }
            advanceUntilIdle()
            assertEquals(1, writes)
            assertEquals(replacement.preview, written)
        } finally { controller.dispose() }
    }
}

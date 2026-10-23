/* Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0 */
package org.locallore.app

import kotlinx.coroutines.CancellationException
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
class DiagnosticsControllerTest {
    @Test fun noPreviewMeansNoConsentAndNoWriter() = runTest {
        val controller = DiagnosticsController(DiagnosticLog(), this)
        var writes = 0
        assertFalse(controller.beginExport())
        controller.completeExport { writes++ }
        advanceUntilIdle()
        assertEquals(0, writes)
        assertFalse(controller.state.value.visible)
    }

    @Test fun exportIsByteIdenticalToFrozenPreviewDespiteNewRecords() = runTest {
        val log = DiagnosticLog()
        log.record(DiagnosticPhase.PREPARE, DiagnosticOutcome.REJECTED, 4, DiagnosticError.MALFORMED)
        val controller = DiagnosticsController(log, this)
        controller.open()
        val preview = controller.state.value.preview
        log.record(DiagnosticPhase.RESET, DiagnosticOutcome.COMPLETED, 7)
        assertTrue(controller.beginExport())
        var written = ""
        controller.completeExport { written = it.toString(Charsets.UTF_8); it.fill(0) }
        advanceUntilIdle()
        assertEquals(preview, written)
        assertEquals(preview, controller.state.value.preview)
        assertNotEquals(preview, log.snapshot().json)
        assertFalse(controller.state.value.exporting)
    }

    @Test fun revokedOldPickerCannotBindToANewerPreview() = runTest {
        val controller = DiagnosticsController(DiagnosticLog(), this)
        controller.open(); assertTrue(controller.beginExport())
        controller.dismiss(); controller.open()
        assertFalse(controller.beginExport()) // Still drain the old result before a new launch.
        var writes = 0
        controller.completeExport { writes++ }
        advanceUntilIdle()
        assertEquals(0, writes)
        assertTrue(controller.beginExport())
        controller.completeExport { writes++ }
        advanceUntilIdle()
        assertEquals(1, writes)
    }

    @Test fun duplicateAndCancelledPickerResultsDoNotWrite() = runTest {
        val controller = DiagnosticsController(DiagnosticLog(), this)
        controller.open(); controller.beginExport(); controller.completeExport(null)
        assertTrue(controller.state.value.notice!!.contains("Nothing was written"))
        assertTrue(controller.beginExport())
        var writes = 0
        controller.completeExport { writes++ }
        controller.completeExport { writes += 10 }
        advanceUntilIdle()
        assertEquals(1, writes)
    }

    @Test fun missingPostProcessDeathSnapshotCannotWriteReturnedUri() = runTest {
        val old = DiagnosticsController(DiagnosticLog(), this)
        old.open(); old.beginExport(); old.dispose()
        val fresh = DiagnosticsController(DiagnosticLog(), this)
        var written = false
        fresh.completeExport { written = true }
        old.completeExport { written = true }
        advanceUntilIdle()
        assertFalse(written)
        assertFalse(old.beginExport())
        assertFalse(fresh.beginExport())
    }

    @Test fun failureNeverShowsOrRetainsProviderExceptionText() = runTest {
        val log = DiagnosticLog()
        val controller = DiagnosticsController(log, this)
        controller.open(); controller.beginExport()
        controller.completeExport { error("SECRET-TIDE-731 C:/private/avery-story.json") }
        advanceUntilIdle()
        assertTrue(controller.state.value.notice!!.contains("incomplete file"))
        assertFalse(controller.state.value.notice!!.contains("SECRET"))
        assertFalse(log.snapshot().json.contains("private"))
        assertTrue(log.snapshot().json.contains("TRANSPORT"))
    }

    @Test fun closingDuringWriteCancelsResourcesAndDiscardsLateCompletions() = runTest {
        val controller = DiagnosticsController(DiagnosticLog(), this)
        val finish = CompletableDeferred<Unit>()
        var closed = false
        controller.open(); controller.beginExport()
        controller.completeExport {
            try { withContext(NonCancellable) { finish.await() } }
            finally { closed = true }
        }
        runCurrent()
        controller.dismiss()
        controller.open()
        val fresh = controller.state.value
        finish.complete(Unit); advanceUntilIdle()
        assertTrue(closed)
        assertEquals(fresh, controller.state.value)
    }

    @Test fun cancellationAfterWriterEffectDoesNotClaimRollback() = runTest {
        val controller = DiagnosticsController(DiagnosticLog(), this)
        var copyExists = false
        controller.open(); controller.beginExport()
        controller.completeExport { copyExists = true; throw CancellationException("private detail") }
        advanceUntilIdle()
        assertTrue(copyExists)
        assertTrue(controller.state.value.notice!!.contains("incomplete file"))
        assertFalse(controller.state.value.notice!!.contains("Nothing was written"))
    }

    @Test fun clearRefreshesPreviewAndDisposalClearsMemory() = runTest {
        val log = DiagnosticLog()
        log.record(DiagnosticPhase.PREPARE, DiagnosticOutcome.PREPARED, 1)
        val controller = DiagnosticsController(log, this)
        controller.open(); controller.clear()
        assertTrue(controller.state.value.preview.contains("\"count\":0"))
        controller.beginExport()
        val reviewed = controller.state.value.preview
        controller.clear() // No consent changes while picker/write is pending.
        assertEquals(reviewed, controller.state.value.preview)
        controller.dispose()
        assertTrue(log.snapshot().json.contains("\"count\":0"))
        assertFalse(controller.state.value.visible)
    }
}

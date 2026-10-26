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

/** Model-free capabilities and coroutine ownership; no Android providers or JNI are mocked as evidence. */
@OptIn(ExperimentalCoroutinesApi::class)
class ArchiveControllerTest {
    @Test fun captureAndExportConsentBindOneExactTokenAndUnchangedNativeBytes() = runTest {
        val gateway = Gateway()
        val closed = mutableListOf<ArchiveImported?>()
        val controller = ArchiveController(gateway, this, closed::add)
        val foreign = ArchivePrepared(11, preview())
        assertNull(controller.beginExportPicker(foreign))
        controller.prepareExport(); controller.confirmImport(foreign)
        controller.completeExport(1) { fail("Unconsented writer ran") }
        controller.open(Story)
        controller.prepareExport(); controller.prepareExport()
        advanceUntilIdle()
        assertEquals(1, gateway.exports)
        val frozen = controller.state.value.prepared!!
        gateway.heads["sibling"] = 99
        assertEquals(mapOf("main" to 4L), frozen.preview.branchHeads)
        val ticket = controller.beginExportPicker(frozen)!!
        assertNull(controller.beginExportPicker(frozen))
        var written: ByteArray? = null
        controller.completeExport(ticket) { written = it.copyOf() }
        controller.completeExport(ticket) { fail("Duplicate writer ran") }
        advanceUntilIdle()
        assertArrayEquals(byteArrayOf(1, 2, 3), written)
        assertEquals(listOf(frozen.token), gateway.exportedTokens)
        assertNull(controller.state.value.prepared)
        assertTrue(closed.isEmpty())
    }

    @Test fun importValidationNeverCommitsBeforeExplicitConsentAndOpenIsExplicit() = runTest {
        val gateway = Gateway()
        val closed = mutableListOf<ArchiveImported?>()
        val controller = ArchiveController(gateway, this, closed::add)
        controller.open(Story)
        val ticket = controller.beginImportPicker()!!
        assertNull(controller.beginImportPicker())
        val original = byteArrayOf(7, 8, 9)
        controller.completeImport(ticket) { original }
        advanceUntilIdle()
        assertArrayEquals(byteArrayOf(7, 8, 9), gateway.validated)
        assertArrayEquals(ByteArray(3), original)
        assertEquals(0, gateway.commits.size)
        assertEquals(22L, controller.state.value.prepared!!.token)
        val prepared = controller.state.value.prepared!!
        controller.confirmImport(prepared); controller.confirmImport(prepared)
        advanceUntilIdle()
        assertEquals(listOf(22L), gateway.commits)
        assertEquals(Imported, controller.state.value.imported)
        assertTrue(closed.isEmpty())
        controller.openImported(controller.state.value.imported!!); advanceUntilIdle()
        assertEquals(listOf(Imported), closed)
        assertFalse(controller.state.value.visible)
    }

    @Test fun returningAfterSuccessRefreshesTheLibraryWithoutAnImplicitOpen() = runTest {
        val closed = mutableListOf<ArchiveImported?>()
        val controller = ArchiveController(Gateway(), this, closed::add)
        controller.open(Story)
        controller.completeImport(controller.beginImportPicker()!!) { byteArrayOf(1) }
        advanceUntilIdle(); controller.confirmImport(controller.state.value.prepared!!); advanceUntilIdle()
        controller.dismiss(); controller.dismiss(); advanceUntilIdle()
        assertEquals(listOf<ArchiveImported?>(null), closed)
    }

    @Test fun outstandingPickerTombstoneHoldsTheGuardAndCannotAttachToNewerConsent() = runTest {
        val gateway = Gateway(); val closed = mutableListOf<ArchiveImported?>()
        val controller = ArchiveController(gateway, this, closed::add)
        controller.open(Story)
        val old = controller.beginImportPicker()!!
        controller.dismiss(); advanceUntilIdle()
        assertTrue(controller.state.value.closing)
        assertTrue(closed.isEmpty())
        controller.open(Story.copy(story = "other"))
        assertNull(controller.beginImportPicker())
        var reads = 0
        controller.completeImport(old) { reads++; byteArrayOf(1) }
        advanceUntilIdle()
        assertEquals(0, reads)
        assertEquals(listOf<ArchiveImported?>(null), closed)
        controller.open(Story.copy(story = "other"))
        val fresh = controller.beginImportPicker()!!
        assertTrue(fresh > old)
        controller.completeImport(old) { error("Old callback borrowed new consent") }
        assertTrue(controller.state.value.awaitingPicker)
        controller.completeImport(fresh) { reads++; byteArrayOf(1) }
        controller.completeImport(fresh) { error("Duplicate callback read") }
        advanceUntilIdle()
        assertEquals(1, reads); assertEquals(1, gateway.imports)
    }

    @Test fun cancellationRevokesPickerConsentUntilTheOriginalCallbackDrains() = runTest {
        val controller = ArchiveController(Gateway(), this) { fail("Cancel released the shell guard") }
        controller.open(Story); controller.prepareExport(); advanceUntilIdle()
        val old = controller.beginExportPicker(controller.state.value.prepared!!)!!
        controller.cancel(); advanceUntilIdle()
        controller.prepareExport()
        assertNull(controller.state.value.prepared)
        assertNull(controller.beginImportPicker())
        controller.completeExport(old) { fail("Revoked export wrote a document") }
        assertFalse(controller.state.value.awaitingPicker)
        controller.prepareExport(); advanceUntilIdle()
        assertNotNull(controller.state.value.prepared)
        val prepared = controller.state.value.prepared!!
        val fresh = controller.beginExportPicker(prepared)!!
        controller.pickerFailed(old)
        assertTrue(controller.state.value.awaitingPicker)
        controller.pickerFailed(fresh)
        assertFalse(controller.state.value.awaitingPicker)
        assertNotNull(controller.beginExportPicker(prepared))
    }

    @Test fun cancelledNonCooperativeReaderCannotStartNativeValidationOrPublishAPreview() = runTest {
        val gateway = Gateway(); val ready = CompletableDeferred<Unit>()
        val bytes = byteArrayOf(3, 2, 1)
        val controller = ArchiveController(gateway, this) { fail("Cancel closed the archive") }
        controller.open(Story)
        controller.completeImport(controller.beginImportPicker()!!) { withContext(NonCancellable) { ready.await(); bytes } }
        runCurrent(); controller.cancel(); runCurrent()
        assertTrue(controller.state.value.busy)
        controller.prepareExport(); assertEquals(0, gateway.exports)
        ready.complete(Unit); advanceUntilIdle()
        assertEquals(0, gateway.imports)
        assertNull(controller.state.value.prepared)
        assertArrayEquals(ByteArray(3), bytes)
    }

    @Test fun disposedNonCooperativeExportReadCannotStartAnExternalWriter() = runTest {
        val gateway = Gateway(); val ready = CompletableDeferred<Unit>(); val bytes = byteArrayOf(1, 2, 3)
        gateway.bytes = { withContext(NonCancellable) { ready.await(); bytes } }
        val controller = ArchiveController(gateway, this) { fail("Disposed callback published") }
        controller.open(Story); controller.prepareExport(); advanceUntilIdle()
        val ticket = controller.beginExportPicker(controller.state.value.prepared!!)!!
        var writes = 0
        controller.completeExport(ticket) { writes++ }
        runCurrent(); controller.dispose()
        ready.complete(Unit); advanceUntilIdle()
        assertEquals(0, writes)
        assertArrayEquals(ByteArray(3), bytes)
        assertEquals(1, gateway.closes)
        assertFalse(controller.state.value.visible)
    }

    @Test fun dismissWaitsForActualCommitDrainAndNeverClaimsCancellationRolledItBack() = runTest {
        val gateway = Gateway(); val ready = CompletableDeferred<Unit>(); var imported = false
        gateway.commit = { withContext(NonCancellable) { ready.await(); imported = true; Imported } }
        val closed = mutableListOf<ArchiveImported?>()
        val controller = ArchiveController(gateway, this, closed::add)
        controller.open(Story)
        controller.completeImport(controller.beginImportPicker()!!) { byteArrayOf(1) }
        advanceUntilIdle(); controller.confirmImport(controller.state.value.prepared!!); runCurrent()
        controller.dismiss(); runCurrent()
        assertTrue(closed.isEmpty())
        assertTrue(controller.state.value.closing)
        ready.complete(Unit); advanceUntilIdle()
        assertTrue(imported)
        assertEquals(listOf<ArchiveImported?>(null), closed)
        assertFalse(controller.state.value.visible)
    }

    @Test fun fixedConflictAndUncertainWriteNoticesNeverEchoPrivateExceptions() = runTest {
        val gateway = Gateway()
        val controller = ArchiveController(gateway, this) {}
        controller.open(Story)
        gateway.prepare = { throw ArchiveFailure("Conflict") }
        controller.completeImport(controller.beginImportPicker()!!) { byteArrayOf(1) }
        advanceUntilIdle()
        assertTrue(controller.state.value.notice!!.contains("cannot be overwritten"))
        controller.prepareExport(); advanceUntilIdle()
        controller.completeExport(controller.beginExportPicker(controller.state.value.prepared!!)!!) { error("SECRET C:/private/archive.json") }
        advanceUntilIdle()
        assertTrue(controller.state.value.notice!!.contains("partial"))
        assertFalse(controller.state.value.notice!!.contains("SECRET"))
        assertNull(controller.state.value.prepared)
    }

    @Test fun storageFullConsumesConsentAndRequiresFreshValidationBeforeRetry() = runTest {
        val gateway = Gateway()
        var nextToken = 40L
        gateway.prepare = { ArchivePrepared(++nextToken, preview()) }
        gateway.commit = { throw ArchiveFailure("Full") }
        val controller = ArchiveController(gateway, this) {}
        controller.open(Story)
        controller.completeImport(controller.beginImportPicker()!!) { byteArrayOf(1) }
        advanceUntilIdle()
        val prepared = controller.state.value.prepared!!
        controller.confirmImport(prepared); advanceUntilIdle()
        assertEquals(listOf(41L), gateway.commits)
        assertNull(controller.state.value.prepared)
        assertNull(controller.state.value.imported)
        assertEquals("Local storage is full. Close to refresh the library. Free storage and validate the archive again before retrying.",
            controller.state.value.notice)
        controller.confirmImport(prepared); advanceUntilIdle()
        assertEquals(listOf(41L), gateway.commits)
        gateway.commit = { Imported }
        controller.completeImport(controller.beginImportPicker()!!) { byteArrayOf(1) }
        advanceUntilIdle(); controller.confirmImport(controller.state.value.prepared!!); advanceUntilIdle()
        assertEquals(listOf(41L, 42L), gateway.commits)
        assertEquals(Imported, controller.state.value.imported)
        controller.dispose()
    }

    @Test fun disposalAndRetainedCallbacksCannotReopenOrReadWriteOrConfirm() = runTest {
        val gateway = Gateway(); val controller = ArchiveController(gateway, this) { fail("Disposed release") }
        controller.open(Story)
        val picker = controller.beginImportPicker()!!
        controller.dispose(); controller.dispose()
        repeat(2) {
            val foreign = ArchivePrepared(22, preview())
            controller.open(Story); controller.prepareExport(); controller.confirmImport(foreign); controller.openImported(Imported)
            controller.cancel(); controller.dismiss()
            assertNull(controller.beginImportPicker()); assertNull(controller.beginExportPicker(foreign))
            controller.completeImport(picker) { error("Disposed reader ran") }
            controller.completeExport(picker) { fail("Disposed writer ran") }
            controller.pickerFailed(picker)
        }
        advanceUntilIdle()
        assertEquals(1, gateway.closes); assertEquals(0, gateway.exports); assertEquals(0, gateway.imports)
        assertTrue(gateway.commits.isEmpty()); assertFalse(controller.state.value.visible)
    }

    @Test fun aDisposedControllersTicketCannotBorrowAFreshControllersPickerConsent() = runTest {
        val old = ArchiveController(Gateway(), this) {}
        old.open(Story); val stale = old.beginImportPicker()!!; old.dispose()
        val gateway = Gateway(); val fresh = ArchiveController(gateway, this) {}
        fresh.open(Story); val current = fresh.beginImportPicker()!!
        assertNotEquals(stale, current)
        fresh.completeImport(stale) { error("Old controller borrowed new picker consent") }
        assertTrue(fresh.state.value.awaitingPicker)
        fresh.completeImport(current, null)
        advanceUntilIdle()
        assertEquals(0, gateway.imports)
    }

    private class Gateway : ArchiveGateway {
        var exports = 0; var imports = 0; var closes = 0
        val heads = linkedMapOf("main" to 4L)
        val exportedTokens = mutableListOf<Long>(); val commits = mutableListOf<Long>()
        var validated: ByteArray? = null
        var prepare: suspend () -> ArchivePrepared = { ArchivePrepared(22, preview()) }
        var bytes: suspend () -> ByteArray = { byteArrayOf(1, 2, 3) }
        var commit: suspend () -> ArchiveImported = { Imported }
        override suspend fun prepareExport(story: SavedStory): ArchivePrepared {
            assertEquals(Story, story); exports++; return ArchivePrepared(11, preview().copy(branchHeads = heads))
        }
        override suspend fun prepareImport(bytes: ByteArray): ArchivePrepared { imports++; validated = bytes.copyOf(); return prepare() }
        override suspend fun exportBytes(token: Long): ByteArray { exportedTokens += token; return bytes() }
        override suspend fun commitImport(token: Long): ArchiveImported { commits += token; return commit() }
        override fun cancel() {}
        override fun close() { closes++ }
    }
    private companion object {
        val Story = SavedStory("synthetic-story", "main", "Synthetic archive", 4)
        val Imported = ArchiveImported("imported-story", "root", 2, 5)
        fun preview() = ArchivePreview(1, "synthetic-story", "Synthetic archive", "main", mapOf("main" to 4L),
            3, 3, "a".repeat(64), "Full private story.", false)
    }
}

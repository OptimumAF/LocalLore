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

/** Callback provenance only: these fakes confer no native or document authority. */
@OptIn(ExperimentalCoroutinesApi::class)
class ArchiveConsentBindingTest {
    @Test fun retainedImportConfirmationCannotBorrowAReplacementPreview() = runTest {
        val gateway = Gateway()
        val controller = ArchiveController(gateway, this) {}
        try {
            controller.open(Story)
            controller.completeImport(controller.beginImportPicker()!!) { byteArrayOf(1) }
            advanceUntilIdle()
            val first = controller.state.value.prepared!!
            val retained = { controller.confirmImport(first) }
            controller.completeImport(controller.beginImportPicker()!!) { byteArrayOf(2) }
            advanceUntilIdle()
            val current = controller.state.value.prepared!!
            assertNotSame(first, current)
            retained(); advanceUntilIdle()
            assertTrue("Old import consent committed the replacement preview", gateway.commits.isEmpty())
            assertSame(current, controller.state.value.prepared)
        } finally { controller.dispose() }
    }

    @Test fun retainedExportPickerCannotBorrowAReplacementPreview() = runTest {
        val controller = ArchiveController(Gateway(), this) {}
        try {
            controller.open(Story); controller.prepareExport(); advanceUntilIdle()
            val first = controller.state.value.prepared!!
            val retained = { controller.beginExportPicker(first) }
            controller.prepareExport(); advanceUntilIdle()
            val current = controller.state.value.prepared!!
            assertNotSame(first, current)
            assertNull("Old export consent opened a picker for the replacement", retained())
            assertFalse(controller.state.value.awaitingPicker)
            assertSame(current, controller.state.value.prepared)
        } finally { controller.dispose() }
    }

    @Test fun retainedOpenCannotOpenAnImportFromAnotherPresentation() = runTest {
        val closed = mutableListOf<ArchiveImported?>()
        val controller = ArchiveController(Gateway(), this, closed::add)
        try {
            controller.open(Story)
            controller.completeImport(controller.beginImportPicker()!!) { byteArrayOf(1) }
            advanceUntilIdle(); controller.confirmImport(controller.state.value.prepared!!); advanceUntilIdle()
            val first = controller.state.value.imported!!
            val retained = { controller.openImported(first) }
            controller.dismiss(); advanceUntilIdle()
            assertEquals(listOf<ArchiveImported?>(null), closed)
            controller.open(Story)
            controller.completeImport(controller.beginImportPicker()!!) { byteArrayOf(2) }
            advanceUntilIdle(); controller.confirmImport(controller.state.value.prepared!!); advanceUntilIdle()
            val current = controller.state.value.imported!!
            assertNotSame(first, current)
            retained(); advanceUntilIdle()
            assertEquals("Old Open consent selected a later imported story", listOf<ArchiveImported?>(null), closed)
            assertSame(current, controller.state.value.imported)
        } finally { controller.dispose() }
    }

    @Test fun equalCopiesAndForeignImportsCannotConfirmOrOpenButCurrentObjectsWorkOnce() = runTest {
        val gateway = Gateway()
        val closed = mutableListOf<ArchiveImported?>()
        val controller = ArchiveController(gateway, this, closed::add)
        val foreignController = ArchiveController(Gateway(), this) {}
        try {
            for (owner in listOf(controller, foreignController)) {
                owner.open(Story)
                owner.completeImport(owner.beginImportPicker()!!) { byteArrayOf(1) }
            }
            advanceUntilIdle()
            val current = controller.state.value.prepared!!
            val foreign = foreignController.state.value.prepared!!
            assertEquals(current, foreign)
            assertNotSame(current, foreign)
            controller.confirmImport(current.copy())
            controller.confirmImport(foreign)
            controller.openImported(ArchiveImported("source-1", "main", 1, 1))
            advanceUntilIdle()
            assertTrue(gateway.commits.isEmpty())
            assertTrue(closed.isEmpty())
            assertSame(current, controller.state.value.prepared)

            controller.confirmImport(current)
            controller.confirmImport(current)
            foreignController.confirmImport(foreign)
            advanceUntilIdle()
            assertEquals(listOf(current.token), gateway.commits)
            val imported = controller.state.value.imported!!
            val foreignImported = foreignController.state.value.imported!!
            assertEquals(imported, foreignImported)
            assertNotSame(imported, foreignImported)
            controller.openImported(imported.copy())
            controller.openImported(foreignImported)
            advanceUntilIdle()
            assertTrue(closed.isEmpty())
            assertSame(imported, controller.state.value.imported)
            controller.openImported(imported)
            controller.openImported(imported)
            advanceUntilIdle()
            assertEquals(listOf(imported), closed)
            assertFalse(controller.state.value.visible)
        } finally { controller.dispose(); foreignController.dispose() }
    }

    @Test fun equalCopiesAndForeignExportsCannotStartPickerAndCurrentConsentIsSingleUse() = runTest {
        val gateway = Gateway()
        val controller = ArchiveController(gateway, this) {}
        val foreignController = ArchiveController(Gateway(), this) {}
        try {
            for (owner in listOf(controller, foreignController)) { owner.open(Story); owner.prepareExport() }
            advanceUntilIdle()
            val current = controller.state.value.prepared!!
            val foreign = foreignController.state.value.prepared!!
            assertEquals(current, foreign)
            assertNotSame(current, foreign)
            assertNull(controller.beginExportPicker(current.copy()))
            assertNull(controller.beginExportPicker(foreign))
            controller.confirmImport(current) // Matching reference still has the wrong operation kind.
            assertFalse(controller.state.value.awaitingPicker)
            assertSame(current, controller.state.value.prepared)
            assertTrue(gateway.commits.isEmpty())
            val ticket = controller.beginExportPicker(current)!!
            assertNull(controller.beginExportPicker(current))
            var writes = 0
            controller.completeExport(ticket) { writes++; assertArrayEquals(byteArrayOf(1, 2, 3), it) }
            controller.completeExport(ticket) { fail("Duplicate export writer ran") }
            advanceUntilIdle()
            assertEquals(1, writes)
            assertEquals(listOf(current.token), gateway.exportedTokens)
            assertNull(controller.beginExportPicker(current))
        } finally { controller.dispose(); foreignController.dispose() }
    }

    @Test fun importConsentCannotActDuringPickerBusyDrainOrAfterDismissAndDispose() = runTest {
        val gateway = Gateway()
        val closed = mutableListOf<ArchiveImported?>()
        val controller = ArchiveController(gateway, this, closed::add)
        try {
            controller.open(Story)
            controller.completeImport(controller.beginImportPicker()!!) { byteArrayOf(1) }
            advanceUntilIdle()
            val first = controller.state.value.prepared!!
            assertNull(controller.beginExportPicker(first)) // Wrong kind, even with the current reference.
            val picker = controller.beginImportPicker()!!
            controller.confirmImport(first)
            assertTrue(controller.state.value.awaitingPicker)
            val release = CompletableDeferred<Unit>()
            controller.completeImport(picker) { withContext(NonCancellable) { release.await(); byteArrayOf(2) } }
            runCurrent()
            controller.confirmImport(first)
            assertTrue(controller.state.value.busy)
            controller.dismiss(); runCurrent()
            controller.confirmImport(first)
            assertTrue(controller.state.value.closing)
            assertTrue(closed.isEmpty())
            release.complete(Unit); advanceUntilIdle()
            controller.confirmImport(first)
            assertEquals(listOf<ArchiveImported?>(null), closed)
            assertTrue(gateway.commits.isEmpty())
            assertEquals(1, gateway.imports)
            controller.dispose()
            controller.confirmImport(first)
            assertNull(controller.beginExportPicker(first))
            controller.openImported(ArchiveImported("foreign", "main", 1, 1))
            advanceUntilIdle()
            assertTrue(gateway.commits.isEmpty())
            assertEquals(listOf<ArchiveImported?>(null), closed)
        } finally { controller.dispose() }
    }

    @Test fun matchingExportReferenceCannotBypassBusyDismissalOrDisposedState() = runTest {
        val controller = ArchiveController(Gateway(), this) {}
        try {
            controller.open(Story); controller.prepareExport(); advanceUntilIdle()
            val first = controller.state.value.prepared!!
            controller.prepareExport()
            assertTrue(controller.state.value.busy)
            assertNull(controller.beginExportPicker(first))
            advanceUntilIdle()
            val current = controller.state.value.prepared!!
            controller.dismiss()
            assertNull(controller.beginExportPicker(current))
            advanceUntilIdle()
            assertNull(controller.beginExportPicker(current))
            controller.dispose()
            assertNull(controller.beginExportPicker(current))
        } finally { controller.dispose() }
    }

    @Test fun matchingImportedReferenceCannotOpenAfterDismissalOrDisposal() = runTest {
        for (dispose in listOf(false, true)) {
            val closed = mutableListOf<ArchiveImported?>()
            val controller = ArchiveController(Gateway(), this, closed::add)
            try {
                controller.open(Story)
                controller.completeImport(controller.beginImportPicker()!!) { byteArrayOf(1) }
                advanceUntilIdle(); controller.confirmImport(controller.state.value.prepared!!); advanceUntilIdle()
                val imported = controller.state.value.imported!!
                if (dispose) controller.dispose() else controller.dismiss()
                controller.openImported(imported)
                advanceUntilIdle()
                controller.openImported(imported)
                advanceUntilIdle()
                assertEquals(if (dispose) emptyList<ArchiveImported?>() else listOf<ArchiveImported?>(null), closed)
                assertFalse(controller.state.value.visible)
            } finally { controller.dispose() }
        }
    }

    private class Gateway : ArchiveGateway {
        private var next = 0L
        var imports = 0
        val commits = mutableListOf<Long>()
        val exportedTokens = mutableListOf<Long>()
        private fun prepared() = (++next).let { token ->
            ArchivePrepared(token, ArchivePreview(2, "source-$token", "Synthetic", "main",
                mapOf("main" to 1L), 1, 3, "a".repeat(64), "Synthetic private preview", false))
        }
        override suspend fun prepareExport(story: SavedStory) = prepared()
        override suspend fun prepareImport(bytes: ByteArray): ArchivePrepared { imports++; return prepared() }
        override suspend fun exportBytes(token: Long): ByteArray { exportedTokens += token; return byteArrayOf(1, 2, 3) }
        override suspend fun commitImport(token: Long): ArchiveImported {
            commits += token
            return ArchiveImported("source-$token", "main", 1, 1)
        }
        override fun cancel() {}
        override fun close() {}
    }
    private companion object { val Story = SavedStory("original", "main", "Synthetic", 1) }
}

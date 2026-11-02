/* Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0 */
package org.locallore.app

import androidx.lifecycle.ViewModelStore
import kotlinx.coroutines.CompletableDeferred
import kotlinx.coroutines.CoroutineScope
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.ExperimentalCoroutinesApi
import kotlinx.coroutines.flow.Flow
import kotlinx.coroutines.flow.collect
import kotlinx.coroutines.launch
import kotlinx.coroutines.test.StandardTestDispatcher
import kotlinx.coroutines.test.UnconfinedTestDispatcher
import kotlinx.coroutines.test.runCurrent
import kotlinx.coroutines.test.runTest
import kotlinx.coroutines.test.resetMain
import kotlinx.coroutines.test.setMain
import org.junit.Assert.*
import org.junit.Test

/** Actual producer/collector scheduling; synthetic archive I/O confers no native document authority. */
@OptIn(ExperimentalCoroutinesApi::class)
class ArchiveFrameDeliveryTest {
    private val story = SavedStory("archive-frame-story", "main", "Archive frame story", 4)
    private val imported = SavedStory("imported-frame-story", "root", "Imported frame story", 2)

    private inner class Archives : ArchiveGateway {
        var exportPrepares = 0
        var importPrepares = 0
        var cancellations = 0
        var closes = 0
        val commits = mutableListOf<Long>()
        private fun prepared(selected: SavedStory) = ArchivePrepared(41, ArchivePreview(
            3, selected.story, selected.title, selected.branch, mapOf(selected.branch to selected.revision),
            2, 3, "b".repeat(64), "Full private synthetic archive", false))
        override suspend fun prepareExport(story: SavedStory): ArchivePrepared {
            exportPrepares++
            return prepared(story)
        }
        override suspend fun prepareImport(bytes: ByteArray): ArchivePrepared {
            importPrepares++
            assertArrayEquals(byteArrayOf(1, 2, 3), bytes)
            return prepared(imported)
        }
        override suspend fun exportBytes(token: Long): ByteArray = error("No document write expected")
        override suspend fun commitImport(token: Long): ArchiveImported {
            assertEquals(41L, token)
            commits += token
            return ArchiveImported(imported.story, imported.branch, 1, 2)
        }
        override fun cancel() { cancellations++ }
        override fun close() { closes++ }
    }

    private inner class Saved : DemoGateway {
        override val durable = true
        var snapshots = 0
        var gameplayCalls = 0
        override suspend fun initialize() = snapshotValue()
        override suspend fun snapshot(): SavedSnapshot { snapshots++; return snapshotValue() }
        override suspend fun respond(action: DemoAction, revision: Long, mode: DemoMode): DemoResult {
            gameplayCalls++
            error("Archive observation must never invoke gameplay")
        }
        private fun snapshotValue() = SavedSnapshot(story.revision, "Not in your inventory", emptyList(),
            "D:/synthetic/archive-frame.sqlite3", 1, listOf(story), story, textProvider = TextProvider.SCRIPTED)
    }

    /** Baseline executes the actual legacy flow; absence of the additive frame API is not a failure. */
    @Suppress("UNCHECKED_CAST")
    private fun productionFlow(owner: Any, getter: String, legacy: Flow<*>): Flow<Any> {
        val method = owner.javaClass.methods.singleOrNull {
            it.name.substringBefore('$') == getter && it.parameterCount == 0
        }
        return (method?.invoke(owner) ?: legacy) as Flow<Any>
    }
    private fun displayed(value: Any): ArchiveUiState = if (value is ArchiveUiState) value else {
        value.javaClass.getMethod("getState").invoke(value) as ArchiveUiState
    }
    private fun prepareExportFrom(controller: ArchiveController, rendered: ArchiveUiState) {
        val method = controller.javaClass.methods.singleOrNull {
            it.name.substringBefore('$') == "prepareExport" &&
                it.parameterTypes.contentEquals(arrayOf(ArchiveUiState::class.java))
        }
        if (method == null) controller.prepareExport() else method.invoke(controller, rendered)
    }

    @Test fun closeAndEqualReopenDeliverTheActualStateNeededByTheFreshExportAction() = runTest {
        val archives = Archives()
        val producer = CoroutineScope(backgroundScope.coroutineContext + UnconfinedTestDispatcher(testScheduler))
        val closed = mutableListOf<ArchiveImported?>()
        val controller = ArchiveController(archives, producer, closed::add)
        val observed = mutableListOf<Any>()
        val collector = launch(StandardTestDispatcher(testScheduler)) {
            productionFlow(controller, "getFrames", controller.state).collect { observed += it }
        }
        try {
            runCurrent()
            controller.open(story)
            runCurrent()
            val first = controller.state.value
            assertSame(first, displayed(observed.last()))
            val delivered = observed.size

            // No token or repeated native grant is involved: these are empty open views.
            controller.dismiss()
            controller.open(story)
            val reopened = controller.state.value
            assertEquals(listOf<ArchiveImported?>(null), closed)
            assertEquals(first, reopened)
            assertNotSame(first, reopened)
            assertEquals(delivered, observed.size)
            runCurrent()

            assertSame("The slow archive collector must receive the reopened callback owner",
                reopened, displayed(observed.last()))
            assertNotSame(first, displayed(observed.last()))
            prepareExportFrom(controller, displayed(observed.last()))
            assertEquals(1, archives.exportPrepares)
            assertNotNull(controller.state.value.prepared)
            assertTrue(archives.commits.isEmpty())
        } finally {
            collector.cancel()
            controller.dispose()
        }
    }

    @Test fun shellArchiveCollectionRefreshesEqualReopenedStateAfterTheLibraryRefresh() = runTest {
        Dispatchers.setMain(UnconfinedTestDispatcher(testScheduler))
        val models = ViewModelStore()
        val archives = Archives()
        val saved = Saved()
        val model = ShellViewModel(saved, archiveGateway = archives)
        models.put("archive-frame", model)
        val observed = mutableListOf<Any>()
        val collector = launch(StandardTestDispatcher(testScheduler)) {
            productionFlow(model, "getArchiveFrames", model.archive).collect { observed += it }
        }
        try {
            runCurrent()
            assertTrue(model.state.value.persistent)
            model.openArchive()
            runCurrent()
            val first = model.archive.value
            assertSame(first, displayed(observed.last()))
            val delivered = observed.size

            model.archiveController!!.dismiss()
            assertFalse(model.state.value.archiveActive)
            assertEquals(1, saved.snapshots)
            model.openArchive()
            val reopened = model.archive.value
            assertEquals(first, reopened)
            assertNotSame(first, reopened)
            assertEquals(delivered, observed.size)
            runCurrent()

            assertSame("The actual ShellViewModel archive stream must forward the new frame",
                reopened, displayed(observed.last()))
            prepareExportFrom(model.archiveController!!, displayed(observed.last()))
            assertEquals(1, archives.exportPrepares)
            assertEquals(story, model.state.value.selectedStory)
            assertEquals(0, saved.gameplayCalls)
        } finally {
            collector.cancel()
            models.clear()
            Dispatchers.resetMain()
        }
    }

    @Test fun sequentialHiddenPickerBusyPreparedImportedAndDisposedStatesKeepTheirExactOwners() = runTest {
        val archives = Archives()
        val producer = CoroutineScope(backgroundScope.coroutineContext + UnconfinedTestDispatcher(testScheduler))
        val controller = ArchiveController(archives, producer) { error("No opening or dismissal expected") }
        val observed = mutableListOf<Any>()
        val collector = launch(StandardTestDispatcher(testScheduler)) {
            productionFlow(controller, "getFrames", controller.state).collect { observed += it }
        }
        val release = CompletableDeferred<Unit>()
        try {
            runCurrent()
            assertFalse(controller.state.value.visible)
            assertSame(controller.state.value, displayed(observed.single()))
            controller.open(story)
            runCurrent()
            assertSame(controller.state.value, displayed(observed.last()))
            val ticket = controller.beginImportPicker()!!
            runCurrent()
            assertTrue(controller.state.value.awaitingPicker)
            assertSame(controller.state.value, displayed(observed.last()))

            controller.completeImport(ticket) { release.await(); byteArrayOf(1, 2, 3) }
            runCurrent()
            assertTrue(controller.state.value.busy)
            assertFalse(controller.state.value.awaitingPicker)
            assertSame(controller.state.value, displayed(observed.last()))
            release.complete(Unit)
            runCurrent()
            assertFalse(controller.state.value.busy)
            assertNotNull(controller.state.value.prepared)
            assertSame(controller.state.value, displayed(observed.last()))
            controller.confirmImport(controller.state.value.prepared!!)
            runCurrent()
            assertEquals(ArchiveImported(imported.story, imported.branch, 1, 2), controller.state.value.imported)
            assertSame(controller.state.value, displayed(observed.last()))
            assertEquals(listOf(41L), archives.commits)
            controller.dispose()
            runCurrent()
            assertFalse(controller.state.value.visible)
            assertSame(controller.state.value, displayed(observed.last()))
            val disposed = controller.state.value
            controller.open(story)
            controller.prepareExport()
            runCurrent()
            assertSame(disposed, controller.state.value)
            assertEquals(0, archives.exportPrepares)
            assertEquals(1, archives.importPrepares)
            assertEquals(1, archives.closes)
        } finally {
            release.complete(Unit)
            collector.cancel()
            controller.dispose()
        }
    }
}

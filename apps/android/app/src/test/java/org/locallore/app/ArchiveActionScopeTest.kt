/* Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0 */
package org.locallore.app

import androidx.lifecycle.ViewModelStore
import java.lang.reflect.InvocationTargetException
import kotlinx.coroutines.CompletableDeferred
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.ExperimentalCoroutinesApi
import kotlinx.coroutines.NonCancellable
import kotlinx.coroutines.test.StandardTestDispatcher
import kotlinx.coroutines.test.TestScope
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

/** Real archive/controller/VM callbacks; fakes supply no document, native or gameplay authority. */
@OptIn(ExperimentalCoroutinesApi::class)
class ArchiveActionScopeTest {
    private val dispatcher = StandardTestDispatcher()
    private val models = ViewModelStore()
    private var modelNumber = 0
    private val storyA = SavedStory("archive-a", "main", "A", 7)
    private val storyB = SavedStory("archive-b", "child", "B", 9)
    private val importedStory = SavedStory("imported", "main", "Imported", 2)

    @Before fun setup() { Dispatchers.setMain(dispatcher) }
    @After fun cleanup() { models.clear(); Dispatchers.resetMain() }

    /** Baseline has no scoped overload: exercise its real old path, rather than failing to compile. */
    private fun action(owner: Any, name: String, rendered: ArchiveUiState, vararg args: Any): Any? {
        val methods = owner.javaClass.declaredMethods.filter { it.name.substringBefore('$') == name }
        val scopedTypes = args.map { it.javaClass } + ArchiveUiState::class.java
        val scoped = methods.singleOrNull { it.parameterTypes.toList() == scopedTypes }
        val selected = scoped ?: methods.single { it.parameterTypes.toList() == args.map { value -> value.javaClass } }
        selected.isAccessible = true
        val values = if (scoped == null) args else (args.toList() + rendered).toTypedArray()
        return try { selected.invoke(owner, *values) }
        catch (failure: InvocationTargetException) { throw failure.targetException }
    }

    private inner class Gateway : ArchiveGateway {
        val exports = mutableListOf<SavedStory>()
        var imports = 0
        val commits = mutableListOf<Long>()
        val exportedTokens = mutableListOf<Long>()
        var cancels = 0
        var closes = 0
        var holdExport: CompletableDeferred<Unit>? = null
        private fun preview(story: SavedStory) = ArchivePreview(3, story.story, story.title, story.branch,
            mapOf(story.branch to story.revision), 2, 3, "a".repeat(64), "Full private synthetic archive", false)
        override suspend fun prepareExport(story: SavedStory): ArchivePrepared {
            exports += story
            holdExport?.let { gate -> withContext(NonCancellable) { gate.await() } }
            return ArchivePrepared(11, preview(story))
        }
        override suspend fun prepareImport(bytes: ByteArray): ArchivePrepared {
            assertTrue(bytes.isNotEmpty())
            imports++
            return ArchivePrepared(22, preview(importedStory))
        }
        override suspend fun exportBytes(token: Long): ByteArray {
            exportedTokens += token
            return byteArrayOf(1, 2, 3)
        }
        override suspend fun commitImport(token: Long): ArchiveImported {
            commits += token
            return ArchiveImported(importedStory.story, importedStory.branch, 1, 2)
        }
        override fun cancel() { cancels++ }
        override fun close() { closes++ }
        fun effects() = listOf(exports.size, imports, commits.size, exportedTokens.size, cancels, closes)
    }

    private inner class Stories : DemoGateway {
        override val durable = true
        var snapshots = 0
        var gameplay = 0
        var resumes = 0
        override suspend fun initialize() = saved()
        override suspend fun snapshot(): SavedSnapshot { snapshots++; return saved() }
        override suspend fun respond(action: DemoAction, revision: Long, mode: DemoMode): DemoResult {
            gameplay++; return DemoResult.Rejected("Unsupported")
        }
        override suspend fun resumeSaved(story: SavedStory): SavedSnapshot { resumes++; return saved() }
        private fun saved() = SavedSnapshot(storyA.revision, "You", emptyList(), "D:/synthetic/archive-tests", 1,
            listOf(storyA, storyB), storyA)
    }

    private fun model(stories: Stories, gateway: Gateway) = ShellViewModel(stories, archiveGateway = gateway)
        .also { models.put("archive-scope-${modelNumber++}", it) }

    private suspend fun TestScope.importPreview(controller: ArchiveController): ArchiveUiState {
        val ticket = controller.beginImportPicker()!!
        controller.completeImport(ticket) { byteArrayOf(1) }
        advanceUntilIdle()
        return controller.state.value.also { assertNotNull(it.prepared); assertFalse(it.busy) }
    }

    @Test fun equalValueCopiesCannotAcquireAnyToolbarAction() = runTest(dispatcher) {
        val violations = mutableListOf<String>()
        for (name in listOf("prepareExport", "beginImportPicker", "cancel", "dismiss")) {
            val gateway = Gateway(); val closed = mutableListOf<ArchiveImported?>()
            val controller = ArchiveController(gateway, this, closed::add)
            try {
                controller.open(storyA)
                val current = controller.state.value
                val copy = current.copy()
                assertEquals(current, copy); assertNotSame(current, copy)
                val effects = gateway.effects()
                action(controller, name, copy); advanceUntilIdle()
                if (controller.state.value !== current || gateway.effects() != effects || closed.isNotEmpty())
                    violations += name
            } finally { controller.dispose() }
        }
        assertEquals("Copied rendered states acquired archive actions", emptyList<String>(), violations)
    }

    @Test fun toolbarCallbacksFromAnEqualValuedClosedPresentationCannotActAfterReopen() = runTest(dispatcher) {
        val violations = mutableListOf<String>()
        for (name in listOf("prepareExport", "beginImportPicker", "cancel", "dismiss")) {
            val gateway = Gateway(); val closed = mutableListOf<ArchiveImported?>()
            val controller = ArchiveController(gateway, this, closed::add)
            try {
                controller.open(storyA)
                val rendered = controller.state.value
                controller.dismiss(); advanceUntilIdle(); controller.open(storyA)
                val current = controller.state.value
                assertEquals(rendered, current); assertNotSame(rendered, current)
                val effects = gateway.effects(); val closures = closed.toList()
                action(controller, name, rendered); advanceUntilIdle()
                if (controller.state.value !== current || gateway.effects() != effects || closed != closures)
                    violations += name
            } finally { controller.dispose() }
        }
        assertEquals("Closed archive controls retargeted an equal-valued reopened presentation", emptyList<String>(), violations)
    }

    @Test fun oldStoryToolbarCannotCaptureCancelOrCloseTheNewStoryArchive() = runTest(dispatcher) {
        val violations = mutableListOf<String>()
        for (name in listOf("prepareExport", "beginImportPicker", "cancel", "dismiss")) {
            val gateway = Gateway(); val closed = mutableListOf<ArchiveImported?>()
            val controller = ArchiveController(gateway, this, closed::add)
            try {
                controller.open(storyA); val old = controller.state.value
                controller.dismiss(); advanceUntilIdle(); controller.open(storyB)
                val current = controller.state.value
                assertEquals(storyB, current.selected)
                val effects = gateway.effects(); val closures = closed.toList()
                action(controller, name, old); advanceUntilIdle()
                if (controller.state.value !== current || gateway.effects() != effects || closed != closures)
                    violations += name
            } finally { controller.dispose() }
        }
        assertEquals("A story-A callback affected the story-B archive", emptyList<String>(), violations)
    }

    @Test fun retainedCancelAndCloseCannotInvalidateNewBusyWorkOrItsOutstandingPicker() = runTest(dispatcher) {
        val violations = mutableListOf<String>()
        for (phase in listOf("busy", "picker")) {
            val gateway = Gateway(); val closed = mutableListOf<ArchiveImported?>()
            val controller = ArchiveController(gateway, this, closed::add)
            val release = CompletableDeferred<Unit>()
            try {
                controller.open(storyA); val old = controller.state.value
                if (phase == "busy") {
                    gateway.holdExport = release
                    controller.prepareExport(); runCurrent()
                    assertTrue(controller.state.value.busy)
                } else {
                    assertNotNull(controller.beginImportPicker())
                    assertTrue(controller.state.value.awaitingPicker)
                }
                val current = controller.state.value; val effects = gateway.effects()
                action(controller, "cancel", old); action(controller, "dismiss", old); runCurrent()
                if (controller.state.value !== current || gateway.effects() != effects || closed.isNotEmpty())
                    violations += phase
            } finally { release.complete(Unit); advanceUntilIdle(); controller.dispose() }
        }
        assertEquals("Retained toolbar actions cancelled a newer operation or picker", emptyList<String>(), violations)
    }

    @Test fun evenTheCurrentPreviewGrantCannotBeUsedWithAPreviousRenderedPage() = runTest(dispatcher) {
        val violations = mutableListOf<String>()
        for (kind in listOf(ArchiveKind.EXPORT, ArchiveKind.IMPORT)) {
            val gateway = Gateway(); val controller = ArchiveController(gateway, this) {}
            try {
                controller.open(storyA)
                val old = if (kind == ArchiveKind.EXPORT) {
                    controller.prepareExport(); advanceUntilIdle(); controller.state.value
                } else importPreview(controller)
                if (kind == ArchiveKind.EXPORT) { controller.prepareExport(); advanceUntilIdle() }
                else importPreview(controller)
                val current = controller.state.value
                assertEquals(old, current); assertNotSame(old, current)
                assertNotSame(old.prepared, current.prepared)
                val effects = gateway.effects()
                if (kind == ArchiveKind.EXPORT) action(controller, "beginExportPicker", old, current.prepared!!)
                else action(controller, "confirmImport", old, current.prepared!!)
                advanceUntilIdle()
                if (controller.state.value !== current || gateway.effects() != effects) violations += kind.name
            } finally { controller.dispose() }
        }
        assertEquals("Current DTO identity bypassed the rendered-page ownership check", emptyList<String>(), violations)
    }

    @Test fun currentImportedObjectCannotOpenThroughACopiedOrEarlierRenderedView() = runTest(dispatcher) {
        val violations = mutableListOf<String>()
        for (mode in listOf("copy", "earlier")) {
            val gateway = Gateway(); val closed = mutableListOf<ArchiveImported?>()
            val controller = ArchiveController(gateway, this, closed::add)
            try {
                controller.open(storyA); val earlier = importPreview(controller)
                controller.confirmImport(earlier.prepared!!); advanceUntilIdle()
                val current = controller.state.value; val imported = current.imported!!
                val supplied = if (mode == "copy") current.copy() else earlier
                assertNotSame(current, supplied)
                val effects = gateway.effects()
                action(controller, "openImported", supplied, imported); advanceUntilIdle()
                if (controller.state.value !== current || gateway.effects() != effects || closed.isNotEmpty())
                    violations += mode
            } finally { controller.dispose() }
        }
        assertEquals("An imported-object reference bypassed the rendered view", emptyList<String>(), violations)
    }

    @Test fun shellPickerWrappersRequireTheCurrentArchiveViewAndStayClosedAfterDisposal() = runTest(dispatcher) {
        val violations = mutableListOf<String>()
        for (name in listOf("beginArchiveImportPicker", "beginArchiveExportPicker")) {
            val stories = Stories(); val gateway = Gateway(); val model = model(stories, gateway)
            advanceUntilIdle(); model.openArchive(); model.archiveController!!.prepareExport(); advanceUntilIdle()
            val old = model.archive.value
            model.archiveController!!.prepareExport(); advanceUntilIdle()
            val current = model.archive.value
            assertEquals(old, current); assertNotSame(old, current)
            val effects = gateway.effects()
            val result = if (name == "beginArchiveImportPicker") action(model, name, old)
                else action(model, name, old, current.prepared!!)
            advanceUntilIdle()
            if (result != false || model.archive.value !== current || gateway.effects() != effects) violations += name
            assertEquals(0, stories.gameplay); assertEquals(0, stories.resumes)
            if (result == false && model.archive.value === current && gateway.effects() == effects) {
                val fresh = if (name == "beginArchiveImportPicker") action(model, name, current)
                    else action(model, name, current, current.prepared!!)
                assertEquals("Fresh rendered Shell picker must still work", true, fresh)
                if (name == "beginArchiveImportPicker") model.completeArchiveImport(null)
                else model.completeArchiveExport(null)
                advanceUntilIdle()
                assertFalse(model.archive.value.awaitingPicker)
            }
            models.clear(); advanceUntilIdle()
            val after = gateway.effects()
            val disposedResult = if (name == "beginArchiveImportPicker") action(model, name, current)
                else action(model, name, current, current.prepared!!)
            advanceUntilIdle()
            assertEquals(false, disposedResult); assertEquals(after, gateway.effects()); assertEquals(1, gateway.closes)
        }
        assertEquals("A retained Shell picker callback borrowed the replacement archive view", emptyList<String>(), violations)
    }

    @Test fun freshControlsKeepOneShotConsentJoinedClosingAndExplicitOpenWorking() = runTest(dispatcher) {
        val gateway = Gateway(); val closed = mutableListOf<ArchiveImported?>()
        val controller = ArchiveController(gateway, this, closed::add)
        val release = CompletableDeferred<Unit>()
        try {
            controller.open(storyA)
            action(controller, "prepareExport", controller.state.value); advanceUntilIdle()
            assertEquals(listOf(storyA), gateway.exports)
            val exporting = controller.state.value
            val ticket = action(controller, "beginExportPicker", exporting, exporting.prepared!!) as Long?
            assertNotNull(ticket)
            assertNull(action(controller, "beginExportPicker", exporting, exporting.prepared!!))
            var writes = 0
            controller.completeExport(ticket!!) { bytes -> writes++; assertArrayEquals(byteArrayOf(1, 2, 3), bytes) }
            controller.completeExport(ticket) { fail("Duplicate callback wrote an archive") }
            advanceUntilIdle()
            assertEquals(1, writes); assertEquals(listOf(11L), gateway.exportedTokens)

            val cancellations = gateway.cancels
            action(controller, "cancel", controller.state.value); advanceUntilIdle()
            assertTrue(controller.state.value.visible); assertFalse(controller.state.value.closing)
            assertEquals(cancellations + 1, gateway.cancels)
            assertNull(controller.state.value.prepared)

            val importTicket = action(controller, "beginImportPicker", controller.state.value) as Long?
            assertNotNull(importTicket)
            controller.completeImport(importTicket!!) {
                withContext(NonCancellable) { release.await(); byteArrayOf(1) }
            }
            runCurrent(); assertTrue(controller.state.value.busy)
            action(controller, "dismiss", controller.state.value); runCurrent()
            assertTrue(controller.state.value.closing); assertTrue(closed.isEmpty())
            release.complete(Unit); advanceUntilIdle()
            assertFalse(controller.state.value.visible)
            assertEquals(listOf<ArchiveImported?>(null), closed)
            assertEquals(0, gateway.imports)

            controller.open(storyA); importPreview(controller)
            val confirming = controller.state.value
            action(controller, "confirmImport", confirming, confirming.prepared!!); advanceUntilIdle()
            assertEquals(listOf(22L), gateway.commits)
            assertEquals(1, closed.size)
            val opening = controller.state.value; val imported = opening.imported!!
            action(controller, "openImported", opening, imported); advanceUntilIdle()
            assertEquals(listOf(null, imported), closed)
            controller.dispose()
            val effects = gateway.effects()
            action(controller, "openImported", opening, imported); action(controller, "dismiss", opening)
            advanceUntilIdle()
            assertEquals(effects, gateway.effects()); assertEquals(1, gateway.closes)
        } finally { release.complete(Unit); advanceUntilIdle(); controller.dispose() }
    }
}

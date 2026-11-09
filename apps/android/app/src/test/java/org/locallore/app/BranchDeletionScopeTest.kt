/* Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0 */
package org.locallore.app

import androidx.lifecycle.ViewModelStore
import kotlinx.coroutines.CompletableDeferred
import kotlinx.coroutines.CoroutineScope
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.ExperimentalCoroutinesApi
import kotlinx.coroutines.NonCancellable
import kotlinx.coroutines.flow.Flow
import kotlinx.coroutines.flow.collect
import kotlinx.coroutines.launch
import kotlinx.coroutines.test.StandardTestDispatcher
import kotlinx.coroutines.test.UnconfinedTestDispatcher
import kotlinx.coroutines.test.advanceUntilIdle
import kotlinx.coroutines.test.resetMain
import kotlinx.coroutines.test.runCurrent
import kotlinx.coroutines.test.runTest
import kotlinx.coroutines.test.setMain
import kotlinx.coroutines.withContext
import org.junit.Assert.*
import org.junit.Test

/** Actual controller/VM and observable scheduling; synthetic ports never delete a real story. */
@OptIn(ExperimentalCoroutinesApi::class)
class BranchDeletionScopeTest {
    private class Deletes : BranchDeletionGateway {
        val prepares = mutableListOf<SavedStory>()
        val commits = mutableListOf<Long>()
        val grants = mutableMapOf<Long, SavedStory>()
        var cancels = 0
        var closes = 0
        private var nextToken = 100L
        var onPrepare: suspend (SavedStory, Long) -> BranchDeletionPrepared = { story, token -> prepared(story, token) }
        var onCommit: suspend (Long) -> BranchDeleted = { deleted(grants.getValue(it)) }
        override suspend fun prepareBranch(story: SavedStory): BranchDeletionPrepared {
            prepares += story
            val token = ++nextToken
            return onPrepare(story, token).also { grants[token] = story }
        }
        override suspend fun commitBranch(token: Long): BranchDeleted { commits += token; return onCommit(token) }
        override fun cancel() { cancels++ }
        override fun close() { closes++ }
    }

    /** The fallback is the existing executable path, not a missing-API failure. */
    private fun action(controller: BranchDeletionController, name: String, rendered: BranchDeletionUiState,
        expected: BranchDeletionPrepared? = null) {
        val types: Array<Class<*>> = if (name == "confirm")
            arrayOf(BranchDeletionPrepared::class.java, BranchDeletionUiState::class.java)
        else arrayOf(BranchDeletionUiState::class.java)
        val method = controller.javaClass.methods.singleOrNull {
            it.name.substringBefore('$') == name && it.parameterTypes.contentEquals(types)
        }
        if (method != null) {
            if (name == "confirm") method.invoke(controller, checkNotNull(expected), rendered)
            else method.invoke(controller, rendered)
        } else when (name) {
            "confirm" -> controller.confirm(checkNotNull(expected))
            "cancel" -> controller.cancel()
            "dismiss" -> controller.dismiss()
            else -> error("Unknown test action")
        }
    }

    @Suppress("UNCHECKED_CAST")
    private fun productionFlow(owner: Any, getter: String, legacy: Flow<*>): Flow<Any> {
        val method = owner.javaClass.methods.singleOrNull {
            it.name.substringBefore('$') == getter && it.parameterCount == 0
        }
        return (method?.invoke(owner) ?: legacy) as Flow<Any>
    }
    private fun displayed(value: Any): BranchDeletionUiState = if (value is BranchDeletionUiState) value
        else value.javaClass.getMethod("getState").invoke(value) as BranchDeletionUiState

    @Test fun copiedRenderedStatesCannotAcquireCloseCancelOrCurrentPreviewConsent() = runTest {
        val violations = mutableListOf<String>()
        for (name in listOf("cancel", "dismiss", "confirm")) {
            val gateway = Deletes(); val closed = mutableListOf<Pair<BranchDeleted?, Boolean>>()
            val controller = BranchDeletionController(this, gateway) { result, uncertain -> closed += result to uncertain }
            try {
                controller.open(Child, "main"); advanceUntilIdle()
                val ready = controller.state.value
                val copied = ready.copy()
                assertEquals(ready, copied); assertNotSame(ready, copied)
                val cancellations = gateway.cancels
                action(controller, name, copied, ready.prepared)
                advanceUntilIdle()
                if (gateway.cancels != cancellations || gateway.commits.isNotEmpty() || closed.isNotEmpty() ||
                    controller.state.value !== ready) violations += name
            } finally { controller.dispose(); advanceUntilIdle() }
        }
        assertEquals("An equal copied branch view acquired current deletion authority", emptyList<String>(), violations)
    }

    @Test fun previousBranchOrStoryControlsCannotBorrowTheCurrentNativePreview() = runTest {
        val violations = mutableListOf<String>()
        for (target in listOf(Sibling, Foreign)) for (name in listOf("cancel", "dismiss", "confirm")) {
            val gateway = Deletes(); val closed = mutableListOf<Pair<BranchDeleted?, Boolean>>()
            val controller = BranchDeletionController(this, gateway) { result, uncertain -> closed += result to uncertain }
            try {
                controller.open(Child, "main"); advanceUntilIdle()
                val old = controller.state.value
                controller.dismiss(); advanceUntilIdle()
                controller.open(target, "main"); advanceUntilIdle()
                val current = controller.state.value
                assertEquals(target, current.selected)
                val cancellations = gateway.cancels; val completions = closed.size
                action(controller, name, old, current.prepared)
                advanceUntilIdle()
                if (controller.state.value !== current || gateway.cancels != cancellations ||
                    gateway.commits.isNotEmpty() || closed.size != completions) violations += "${target.story}/${target.branch}:$name"
            } finally { controller.dispose(); advanceUntilIdle() }
        }
        assertEquals("A previous branch/story view affected a replacement deletion", emptyList<String>(), violations)
    }

    @Test fun retainedCancelAndCloseCannotInterruptAnotherBranchesNoncooperativeCommit() = runTest {
        val violations = mutableListOf<String>()
        for (name in listOf("cancel", "dismiss")) {
            val release = CompletableDeferred<Unit>(); val gateway = Deletes()
            val controller = BranchDeletionController(this, gateway) { _, _ -> }
            try {
                controller.open(Child, "main"); advanceUntilIdle()
                val old = controller.state.value
                controller.dismiss(); advanceUntilIdle()
                gateway.onCommit = { token ->
                    withContext(NonCancellable) { release.await() }
                    deleted(gateway.grants.getValue(token))
                }
                controller.open(Sibling, "main"); advanceUntilIdle()
                controller.confirm(controller.state.value.prepared!!); runCurrent()
                val busy = controller.state.value
                assertTrue(busy.busy); assertFalse(busy.closing)
                assertEquals(1, gateway.commits.size)
                val cancellations = gateway.cancels
                action(controller, name, old); runCurrent()
                if (controller.state.value !== busy || gateway.cancels != cancellations) violations += name
            } finally {
                release.complete(Unit); advanceUntilIdle()
                controller.dispose(); advanceUntilIdle()
            }
        }
        assertEquals("Old toolbar actions interrupted a newer branch commit", emptyList<String>(), violations)
    }

    @Test fun slowControllerCollectionDeliversTheNewEqualBusyViewBeforeFreshCancellation() = runTest {
        val gates = listOf(CompletableDeferred<Unit>(), CompletableDeferred<Unit>())
        val releaseCollector = CompletableDeferred<Unit>(); val gateway = Deletes()
        gateway.onPrepare = { story, token ->
            val index = gateway.prepares.size - 1
            withContext(NonCancellable) { gates[index].await() }
            prepared(story, token)
        }
        val producer = CoroutineScope(backgroundScope.coroutineContext + UnconfinedTestDispatcher(testScheduler))
        val closed = mutableListOf<Pair<BranchDeleted?, Boolean>>()
        val controller = BranchDeletionController(producer, gateway) { result, uncertain -> closed += result to uncertain }
        val observed = mutableListOf<Any>(); var parked = false
        val collector = launch(StandardTestDispatcher(testScheduler)) {
            productionFlow(controller, "getFrames", controller.state).collect { frame ->
                observed += frame
                if (!parked && displayed(frame).visible && displayed(frame).busy) {
                    parked = true; releaseCollector.await()
                }
            }
        }
        try {
            runCurrent(); controller.open(Child, "main"); runCurrent()
            val old = controller.state.value
            assertTrue(parked); assertSame(old, displayed(observed.last())); assertNull(old.prepared)
            controller.dismiss(); gates[0].complete(Unit); runCurrent(); advanceUntilIdle()
            assertEquals(listOf(null to false), closed); assertFalse(controller.state.value.visible)
            controller.open(Child, "main"); runCurrent()
            val reopened = controller.state.value
            assertEquals(old, reopened); assertNotSame(old, reopened)
            assertEquals(listOf(Child, Child), gateway.prepares)
            releaseCollector.complete(Unit); runCurrent()
            assertSame("A slow controller collector must receive the reopened busy callback owner",
                reopened, displayed(observed.last()))
            action(controller, "cancel", displayed(observed.last())); runCurrent()
            assertTrue(controller.state.value.closing)
            assertEquals(1, closed.size) // Closing must wait for the second pending preview.
            gates[1].complete(Unit); runCurrent(); advanceUntilIdle()
            assertEquals(listOf(null to false, null to false), closed)
            assertTrue(gateway.commits.isEmpty())
        } finally {
            releaseCollector.complete(Unit); gates.forEach { it.complete(Unit) }
            collector.cancel(); controller.dispose(); runCurrent(); advanceUntilIdle()
        }
    }

    private class Stories : DemoGateway {
        override val durable = true
        var selected = Child
        var reconciles = 0
        var resumes = 0
        var gameplayCalls = 0
        override suspend fun initialize() = saved()
        override suspend fun snapshot() = saved()
        override suspend fun reconcileSaved(): SavedSnapshot { reconciles++; selected = Root; return saved() }
        override suspend fun resumeSaved(story: SavedStory): SavedSnapshot { resumes++; selected = story; return saved() }
        override suspend fun respond(action: DemoAction, revision: Long, mode: DemoMode): DemoResult {
            gameplayCalls++; error("Deletion display collection cannot invoke gameplay")
        }
        private fun saved() = SavedSnapshot(selected.revision, "You", emptyList(),
            "D:/synthetic/branch-scope.sqlite3", 1, listOf(Root), selected,
            databaseSchemaVersion = 5, textProvider = TextProvider.SCRIPTED,
            timelines = listOf(SavedTimeline(Root.story, Root.branch, null, null, Root.revision, 0),
                SavedTimeline(Child.story, Child.branch, Root.branch, Root.revision, Child.revision, 0)))
    }

    @Test fun shellForwardsNewBusyFrameAfterDrainLibraryRefreshAndActualChildReselection() = runTest {
        Dispatchers.setMain(UnconfinedTestDispatcher(testScheduler))
        val owners = ViewModelStore(); val stories = Stories(); val gateway = Deletes()
        val gates = listOf(CompletableDeferred<Unit>(), CompletableDeferred<Unit>())
        gateway.onPrepare = { story, token ->
            val index = gateway.prepares.size - 1
            withContext(NonCancellable) { gates[index].await() }
            prepared(story, token)
        }
        val model = ShellViewModel(stories, branchDeletionGateway = gateway)
        owners.put("branch-scope", model)
        val controller = checkNotNull(model.branchDeletionController)
        val releaseCollector = CompletableDeferred<Unit>(); val observed = mutableListOf<Any>(); var parked = false
        val collector = launch(StandardTestDispatcher(testScheduler)) {
            productionFlow(model, "getBranchDeletionFrames", model.branchDeletion).collect { frame ->
                observed += frame
                if (!parked && displayed(frame).visible && displayed(frame).busy) {
                    parked = true; releaseCollector.await()
                }
            }
        }
        try {
            runCurrent(); model.openBranchDeletion(); runCurrent()
            val old = model.branchDeletion.value
            assertTrue(parked); assertSame(old, displayed(observed.last()))
            controller.dismiss(); gates[0].complete(Unit); advanceUntilIdle()
            assertFalse(model.state.value.deletionActive); assertEquals(1, stories.reconciles)
            assertEquals(Root, model.state.value.selectedStory)
            model.resumeTimeline(model.state.value.timelines.single { it.branch == Child.branch }); advanceUntilIdle()
            assertEquals(1, stories.resumes); assertEquals(Child, model.state.value.selectedStory)
            model.openBranchDeletion(); runCurrent()
            val reopened = model.branchDeletion.value
            assertEquals(old, reopened); assertNotSame(old, reopened)
            releaseCollector.complete(Unit); runCurrent()
            assertSame("The actual VM stream must forward the replacement busy branch owner",
                reopened, displayed(observed.last()))
            action(controller, "cancel", displayed(observed.last())); runCurrent()
            assertTrue(controller.state.value.closing); assertEquals(1, stories.reconciles)
            gates[1].complete(Unit); advanceUntilIdle()
            assertFalse(model.state.value.deletionActive); assertEquals(2, stories.reconciles)
            assertEquals(0, stories.gameplayCalls); assertTrue(gateway.commits.isEmpty())
        } finally {
            releaseCollector.complete(Unit); gates.forEach { it.complete(Unit) }
            collector.cancel(); owners.clear(); advanceUntilIdle(); Dispatchers.resetMain()
        }
    }

    @Test fun freshRootRestrictionRetainedPreviewOneShotAndDisposedControlsRemainIntact() = runTest {
        val gateway = Deletes(); val closed = mutableListOf<Pair<BranchDeleted?, Boolean>>()
        val controller = BranchDeletionController(this, gateway) { result, uncertain -> closed += result to uncertain }
        try {
            controller.open(Root, Root.branch); runCurrent()
            assertFalse(controller.state.value.visible); assertTrue(gateway.prepares.isEmpty())
            controller.open(Child, Root.branch); advanceUntilIdle()
            val ready = controller.state.value; val consent = checkNotNull(ready.prepared)
            assertEquals(mapOf("child" to 14L), consent.preview.retainedDescendants)
            assertEquals(mapOf(Child.branch to 9L), consent.preview.retainedHeads)
            assertTrue(consent.preview.removedBranches.isEmpty())
            action(controller, "confirm", ready, consent.copy()); runCurrent()
            assertTrue(gateway.commits.isEmpty()); assertSame(ready, controller.state.value)
            action(controller, "confirm", ready, consent)
            action(controller, "confirm", ready, consent); advanceUntilIdle()
            assertEquals(listOf(consent.token), gateway.commits)
            assertEquals(deleted(Child), controller.state.value.deleted)
            assertTrue(closed.isEmpty())
            action(controller, "dismiss", controller.state.value); advanceUntilIdle()
            assertEquals(listOf(deleted(Child) to false), closed)
            controller.dispose(); val cancellations = gateway.cancels
            action(controller, "confirm", ready, consent); action(controller, "cancel", ready)
            action(controller, "dismiss", ready); controller.open(Sibling, Root.branch); advanceUntilIdle()
            assertEquals(1, gateway.closes); assertEquals(cancellations, gateway.cancels)
            assertEquals(1, gateway.prepares.size); assertEquals(1, gateway.commits.size)
        } finally { controller.dispose(); advanceUntilIdle() }
    }

    @Test fun freshCloseWaitsForNoncooperativeCommitAndKeepsUnconfirmedOutcomeUncertain() = runTest {
        val release = CompletableDeferred<Unit>(); val gateway = Deletes()
        var physicalEffect = false
        gateway.onCommit = { token ->
            withContext(NonCancellable) { release.await(); physicalEffect = true }
            deleted(gateway.grants.getValue(token))
        }
        val closed = mutableListOf<Pair<BranchDeleted?, Boolean>>()
        val controller = BranchDeletionController(this, gateway) { result, uncertain -> closed += result to uncertain }
        try {
            controller.open(Child, "main"); advanceUntilIdle()
            val ready = controller.state.value
            action(controller, "confirm", ready, ready.prepared); runCurrent()
            assertEquals(1, gateway.commits.size); assertFalse(physicalEffect)
            action(controller, "dismiss", controller.state.value); runCurrent()
            assertTrue(controller.state.value.closing); assertTrue(closed.isEmpty())
            assertTrue(controller.state.value.notice.orEmpty().contains("may already have completed"))
            assertEquals(1, gateway.cancels)
            release.complete(Unit); advanceUntilIdle()
            assertTrue(physicalEffect)
            assertEquals(listOf(null to true), closed)
            assertFalse(controller.state.value.visible); assertTrue(gateway.cancels >= 2)
            assertEquals(1, gateway.commits.size)
        } finally { release.complete(Unit); controller.dispose(); advanceUntilIdle() }
    }

    private companion object {
        val Root = SavedStory("branch-scope-story", "main", "Retained synthetic story", 4)
        val Child = Root.copy(branch = "parent", revision = 12)
        val Sibling = Child.copy(branch = "sibling", revision = 14)
        val Foreign = Child.copy(story = "foreign-branch-story")
        fun prepared(story: SavedStory, token: Long) = BranchDeletionPrepared(token, BranchDeletionPreview(
            2, story.story, story.branch, story.title, "main", story.revision,
            mapOf("child" to story.revision + 2), mapOf(story.branch to 9L), emptyList(),
            mapOf("turns" to 3L), 1, 2, "Synthetic retained ancestry warning"))
        fun deleted(story: SavedStory) = BranchDeleted(story.story, story.branch, 9, 0, 3, listOf(story.branch))
    }
}

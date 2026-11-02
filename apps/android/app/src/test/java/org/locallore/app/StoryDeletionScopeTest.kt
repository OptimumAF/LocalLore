/* Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0 */
package org.locallore.app

import androidx.lifecycle.ViewModelStore
import java.lang.reflect.InvocationTargetException
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

/** Actual story-deletion owners and observable streams; synthetic I/O never deletes a database. */
@OptIn(ExperimentalCoroutinesApi::class)
class StoryDeletionScopeTest {
    private val story = SavedStory("scope-story-a", "main", "Synthetic A", 4)
    private val other = SavedStory("scope-story-b", "root", "Synthetic B", 7)

    /** Missing additive APIs exercise the existing path, so FIRST is behavioral, not setup failure. */
    private fun action(owner: Any, name: String, rendered: StoryDeletionUiState, vararg args: Any): Any? {
        val candidates = owner.javaClass.methods.filter { it.name.substringBefore('$') == name }
        val types = args.map { it.javaClass }
        val scoped = candidates.singleOrNull { it.parameterTypes.toList() == types + StoryDeletionUiState::class.java }
        val method = scoped ?: candidates.single { it.parameterTypes.toList() == types }
        val values = if (scoped == null) args else (args.toList() + rendered).toTypedArray()
        return try { method.invoke(owner, *values) }
        catch (failure: InvocationTargetException) { throw failure.targetException }
    }

    @Suppress("UNCHECKED_CAST")
    private fun productionFlow(owner: Any, getter: String, legacy: Flow<*>): Flow<Any> {
        val method = owner.javaClass.methods.singleOrNull {
            it.name.substringBefore('$') == getter && it.parameterCount == 0
        }
        return (method?.invoke(owner) ?: legacy) as Flow<Any>
    }
    private fun displayed(value: Any): StoryDeletionUiState = if (value is StoryDeletionUiState) value else
        value.javaClass.getMethod("getState").invoke(value) as StoryDeletionUiState

    private class Gateway : StoryDeletionGateway {
        val prepares = mutableListOf<SavedStory>()
        val commits = mutableListOf<Long>()
        val acceptedEffects = mutableListOf<StoryDeleted>()
        var cancels = 0
        var closes = 0
        var holdPrepare: CompletableDeferred<Unit>? = null
        var holdCommit: CompletableDeferred<Unit>? = null
        private var nextToken = 100L
        private val targets = mutableMapOf<Long, SavedStory>()
        private fun grant(story: SavedStory): StoryDeletionPrepared {
            val token = ++nextToken
            targets[token] = story
            return StoryDeletionPrepared(token, StoryDeletionPreview(1, story.story, story.title,
                story.branch, mapOf(story.branch to story.revision), 2, 1, 1, 0,
                mapOf("events" to 4L, "branches" to 1L), "Synthetic deletion has no forensic-erasure guarantee"))
        }
        override suspend fun prepare(story: SavedStory): StoryDeletionPrepared {
            prepares += story
            val gate = holdPrepare
            return if (gate == null) grant(story)
            else withContext(NonCancellable) { gate.await(); grant(story) }
        }
        override suspend fun commit(token: Long): StoryDeleted {
            commits += token
            val selected = targets.getValue(token)
            val deleted = StoryDeleted(selected.story, 1, 2)
            val gate = holdCommit
            return if (gate == null) deleted.also { acceptedEffects += it }
            else withContext(NonCancellable) { gate.await(); acceptedEffects += deleted; deleted }
        }
        override fun cancel() { cancels++ }
        override fun close() { closes++ }
        fun effects() = listOf(prepares.size, commits.size, acceptedEffects.size, cancels, closes)
    }

    private inner class Stories : DemoGateway {
        override val durable = true
        var refreshes = 0
        var gameplay = 0
        override suspend fun respond(action: DemoAction, revision: Long, mode: DemoMode): DemoResult {
            gameplay++
            error("Deletion presentation must not invoke gameplay")
        }
        override suspend fun initialize() = saved()
        override suspend fun snapshot(): SavedSnapshot { refreshes++; return saved() }
        private fun saved() = SavedSnapshot(story.revision, "You", emptyList(), "D:/synthetic/story-scope.sqlite3",
            1, listOf(story, other), story)
    }

    @Test fun equalRenderedCopiesCannotConfirmTheCurrentGrantOrCloseItsOwner() = runTest {
        val violations = mutableListOf<String>()
        for (name in listOf("confirm", "cancel", "dismiss")) {
            val gateway = Gateway(); val closed = mutableListOf<StoryDeleted?>()
            val controller = StoryDeletionController(this, gateway, closed::add)
            try {
                controller.open(story); advanceUntilIdle()
                val current = controller.state.value
                val copied = current.copy()
                assertEquals(current, copied); assertNotSame(current, copied)
                val before = gateway.effects()
                if (name == "confirm") action(controller, name, copied, current.prepared!!)
                else action(controller, name, copied)
                advanceUntilIdle()
                if (gateway.effects() != before || controller.state.value !== current || closed.isNotEmpty())
                    violations += name
            } finally { controller.dispose() }
        }
        assertEquals("A copied rendered story-deletion state acquired actions", emptyList<String>(), violations)
    }

    @Test fun retainedToolbarCannotCloseAnotherStoryOrAReopenedPresentation() = runTest {
        val violations = mutableListOf<String>()
        for (target in listOf(story, other)) for (name in listOf("cancel", "dismiss")) {
            val gateway = Gateway(); val closed = mutableListOf<StoryDeleted?>()
            val controller = StoryDeletionController(this, gateway, closed::add)
            try {
                controller.open(story); advanceUntilIdle()
                val old = controller.state.value
                controller.dismiss(); advanceUntilIdle()
                controller.open(target); advanceUntilIdle()
                val current = controller.state.value
                assertEquals(target, current.selected)
                assertNotSame(old, current)
                assertNotEquals(old.prepared!!.token, current.prepared!!.token)
                val before = gateway.effects(); val closedBefore = closed.size
                action(controller, name, old); advanceUntilIdle()
                if (gateway.effects() != before || closed.size != closedBefore || controller.state.value !== current)
                    violations += "$name:${target.story}"
            } finally { controller.dispose() }
        }
        assertEquals("An old toolbar action retargeted the replacement deletion view", emptyList<String>(), violations)
    }

    @Test fun currentPreviewCannotBorrowAPriorRenderedPageAndOldDtoChecksRemainRequired() = runTest {
        val gateway = Gateway(); val controller = StoryDeletionController(this, gateway) {}
        try {
            controller.open(story); advanceUntilIdle()
            val old = controller.state.value
            controller.dismiss(); advanceUntilIdle()
            controller.open(story); advanceUntilIdle()
            val current = controller.state.value; val prepared = current.prepared!!
            assertNotEquals(old.prepared!!.token, prepared.token)
            action(controller, "confirm", current, old.prepared!!)
            action(controller, "confirm", current, prepared.copy()); advanceUntilIdle()
            assertTrue("Existing exact DTO ownership must remain", gateway.commits.isEmpty())
            assertSame(current, controller.state.value)
            action(controller, "confirm", old, prepared); advanceUntilIdle()
            assertTrue("Current DTO identity bypassed the stale rendered-page boundary", gateway.commits.isEmpty())
            assertSame(current, controller.state.value)
        } finally { controller.dispose() }
    }

    @Test fun staleToolbarCannotInterruptANewerNoncooperativeCommit() = runTest {
        val violations = mutableListOf<String>()
        for (name in listOf("cancel", "dismiss")) {
            val release = CompletableDeferred<Unit>(); val gateway = Gateway()
            val closed = mutableListOf<StoryDeleted?>()
            val controller = StoryDeletionController(this, gateway, closed::add)
            try {
                controller.open(story); advanceUntilIdle()
                val oldPage = controller.state.value
                gateway.holdCommit = release
                controller.confirm(oldPage.prepared!!); runCurrent()
                val current = controller.state.value
                assertTrue(current.busy); assertFalse(current.closing)
                val before = gateway.effects()
                action(controller, name, oldPage); runCurrent()
                if (gateway.effects() != before || controller.state.value !== current || closed.isNotEmpty())
                    violations += name
            } finally {
                release.complete(Unit); advanceUntilIdle(); controller.dispose()
            }
        }
        assertEquals("Retained toolbar cancelled or closed a newer story commit", emptyList<String>(), violations)
    }

    @Test fun slowControllerCollectionReceivesTheNewEqualBusyOwnerAfterCloseDrainAndReopen() = runTest {
        val firstRelease = CompletableDeferred<Unit>(); val secondRelease = CompletableDeferred<Unit>()
        val collectorRelease = CompletableDeferred<Unit>(); val gateway = Gateway()
        val producer = CoroutineScope(backgroundScope.coroutineContext + UnconfinedTestDispatcher(testScheduler))
        val closed = mutableListOf<StoryDeleted?>()
        val controller = StoryDeletionController(producer, gateway, closed::add)
        val observed = mutableListOf<Any>(); var pauseNextBusy = true
        val collector = launch(StandardTestDispatcher(testScheduler)) {
            productionFlow(controller, "getFrames", controller.state).collect { value ->
                observed += value
                if (displayed(value).busy && pauseNextBusy) {
                    pauseNextBusy = false
                    collectorRelease.await()
                }
            }
        }
        try {
            runCurrent(); gateway.holdPrepare = firstRelease
            controller.open(story); runCurrent()
            val first = controller.state.value
            assertTrue(first.busy); assertNull(first.prepared)
            assertSame(first, displayed(observed.last()))
            controller.dismiss(); firstRelease.complete(Unit); runCurrent()
            assertEquals(listOf<StoryDeleted?>(null), closed)
            assertFalse(controller.state.value.visible)
            gateway.holdPrepare = secondRelease
            controller.open(story); runCurrent()
            val reopened = controller.state.value
            assertEquals(first, reopened); assertNotSame(first, reopened)
            assertEquals(2, gateway.prepares.size)
            collectorRelease.complete(Unit); runCurrent()
            assertSame("The slow controller flow must deliver the new pending-preview owner",
                reopened, displayed(observed.last()))
            action(controller, "cancel", displayed(observed.last())); runCurrent()
            assertTrue(controller.state.value.closing)
            assertEquals(1, closed.size) // Fresh Close still joins the second real coroutine.
        } finally {
            collectorRelease.complete(Unit); firstRelease.complete(Unit); secondRelease.complete(Unit)
            collector.cancel(); controller.dispose(); runCurrent()
        }
    }

    @Test fun shellDeletionFlowForwardsTheNewEqualBusyOwnerAfterLibraryRefresh() = runTest {
        Dispatchers.setMain(UnconfinedTestDispatcher(testScheduler))
        val models = ViewModelStore(); val gateway = Gateway(); val stories = Stories()
        val firstRelease = CompletableDeferred<Unit>(); val secondRelease = CompletableDeferred<Unit>()
        val collectorRelease = CompletableDeferred<Unit>()
        val model = ShellViewModel(stories, deletionGateway = gateway)
        models.put("story-deletion-scope", model)
        val controller = model.deletionController!!
        val observed = mutableListOf<Any>(); var pauseNextBusy = true
        val collector = launch(StandardTestDispatcher(testScheduler)) {
            productionFlow(model, "getDeletionFrames", model.deletion).collect { value ->
                observed += value
                if (displayed(value).busy && pauseNextBusy) {
                    pauseNextBusy = false
                    collectorRelease.await()
                }
            }
        }
        try {
            runCurrent(); assertTrue(model.state.value.persistent)
            gateway.holdPrepare = firstRelease
            model.openDeletion(); runCurrent()
            val first = model.deletion.value
            assertTrue(first.busy); assertSame(first, displayed(observed.last()))
            controller.dismiss(); firstRelease.complete(Unit); runCurrent()
            assertFalse(model.state.value.deletionActive)
            assertEquals(1, stories.refreshes)
            gateway.holdPrepare = secondRelease
            model.openDeletion(); runCurrent()
            val reopened = model.deletion.value
            assertEquals(first, reopened); assertNotSame(first, reopened)
            collectorRelease.complete(Unit); runCurrent()
            assertSame("The ShellViewModel deletion stream must forward the replacement owner",
                reopened, displayed(observed.last()))
            action(controller, "cancel", displayed(observed.last())); runCurrent()
            assertTrue(model.deletion.value.closing)
            assertEquals(0, stories.gameplay)
            assertTrue(gateway.commits.isEmpty())
        } finally {
            collectorRelease.complete(Unit); firstRelease.complete(Unit); secondRelease.complete(Unit)
            collector.cancel(); models.clear(); runCurrent(); Dispatchers.resetMain()
        }
    }

    @Test fun freshConsentRemainsOneShotAndFreshCloseJoinsWithoutClaimingRollback() = runTest {
        val release = CompletableDeferred<Unit>(); val gateway = Gateway()
        val closed = mutableListOf<StoryDeleted?>()
        val controller = StoryDeletionController(this, gateway, closed::add)
        try {
            controller.open(story); advanceUntilIdle()
            val preparedPage = controller.state.value; val prepared = preparedPage.prepared!!
            action(controller, "confirm", preparedPage, prepared.copy()); advanceUntilIdle()
            assertTrue(gateway.commits.isEmpty())
            gateway.holdCommit = release
            action(controller, "confirm", preparedPage, prepared)
            action(controller, "confirm", preparedPage, prepared); runCurrent()
            assertEquals(listOf(prepared.token), gateway.commits)
            val busy = controller.state.value
            action(controller, "dismiss", busy); runCurrent()
            assertTrue(controller.state.value.closing)
            assertTrue(controller.state.value.notice!!.contains("may already have completed"))
            assertTrue(closed.isEmpty())
            release.complete(Unit); advanceUntilIdle()
            assertEquals(listOf(StoryDeleted(story.story, 1, 2)), gateway.acceptedEffects)
            assertEquals(listOf<StoryDeleted?>(null), closed) // Missing acknowledgement is not rollback.
            assertFalse(controller.state.value.visible)

            gateway.holdCommit = null
            controller.open(other); advanceUntilIdle()
            val fresh = controller.state.value
            assertTrue(fresh.prepared!!.token > prepared.token)
            action(controller, "confirm", fresh, fresh.prepared!!); advanceUntilIdle()
            assertEquals(StoryDeleted(other.story, 1, 2), controller.state.value.deleted)
            action(controller, "cancel", controller.state.value); advanceUntilIdle()
            assertEquals(listOf(null, StoryDeleted(other.story, 1, 2)), closed)
            controller.dispose()
            val before = gateway.effects()
            action(controller, "confirm", fresh, fresh.prepared!!)
            action(controller, "cancel", fresh); action(controller, "dismiss", fresh)
            controller.open(story); advanceUntilIdle()
            assertEquals(before, gateway.effects())
            assertEquals(1, gateway.closes)
        } finally {
            release.complete(Unit); advanceUntilIdle(); controller.dispose()
        }
    }
}

/* Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0 */
package org.locallore.app

import androidx.lifecycle.ViewModelStore
import kotlinx.coroutines.CompletableDeferred
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.ExperimentalCoroutinesApi
import kotlinx.coroutines.test.StandardTestDispatcher
import kotlinx.coroutines.test.advanceUntilIdle
import kotlinx.coroutines.test.resetMain
import kotlinx.coroutines.test.runCurrent
import kotlinx.coroutines.test.runTest
import kotlinx.coroutines.test.setMain
import org.junit.After
import org.junit.Assert.*
import org.junit.Before
import org.junit.Test

/** Actual ShellViewModel route with synthetic gateway-owned histories; no Rust/canonical proof. */
@OptIn(ExperimentalCoroutinesApi::class)
class QuickActionScopeShellTest {
    private val dispatcher = StandardTestDispatcher()
    private val store = ViewModelStore()
    private var modelCount = 0
    private val a = SavedStory("synthetic-a", "main", "A", 7)
    private val b = SavedStory("synthetic-b", "main", "B", 7)
    private val fork = a.copy(branch = "fork")

    private data class Response(val action: DemoAction, val scope: SavedStory?, val revision: Long, val mode: DemoMode)

    private inner class Stories : DemoGateway {
        override val durable = true
        var selected: SavedStory? = a
        var provider = TextProvider.UNAVAILABLE
        var resumeGate: CompletableDeferred<Unit>? = null
        var recoveryFails = false
        var commits = 0
        var closes = 0
        val responses = mutableListOf<Response>()
        val resumes = mutableListOf<SavedStory>()
        private val histories = mutableMapOf(
            (a.story to a.branch) to listOf(SceneMessage(1, "SCRIPTED A accepted history", false)),
            (b.story to b.branch) to listOf(SceneMessage(1, "SCRIPTED B compatible accepted history", false)),
            (fork.story to fork.branch) to listOf(SceneMessage(1, "SCRIPTED fork compatible accepted history", false)),
        )
        private fun history() = selected?.let { histories[it.story to it.branch].orEmpty() }.orEmpty()
        private fun saved() = SavedSnapshot(
            revision = selected?.revision ?: 0,
            potionOwner = "SCRIPTED compatible actor",
            messages = history(), location = "/synthetic/quick-actions", schemaVersion = 1,
            stories = listOf(a, b), selected = selected, textProvider = provider,
        )
        override suspend fun initialize() = saved()
        override suspend fun snapshot() = saved()
        override suspend fun resumeSaved(story: SavedStory): SavedSnapshot {
            resumes += story
            resumeGate?.await()
            selected = story
            return saved()
        }
        override suspend fun recoverSaved(): SavedSnapshot {
            if (recoveryFails) error("SCRIPTED recovery refusal")
            return saved()
        }
        override suspend fun respond(action: DemoAction, revision: Long, mode: DemoMode): DemoResult {
            val current = checkNotNull(selected)
            check(revision == current.revision)
            responses += Response(action, current, revision, mode)
            return DemoResult.Accepted(revision + 1, "SCRIPTED compatible actor", "SCRIPTED accepted quick action")
        }
        override suspend fun commitAsync(result: DemoResult): DemoResult {
            val accepted = result as DemoResult.Accepted
            val current = checkNotNull(selected)
            check(accepted.revision == current.revision + 1)
            commits++
            val previous = history()
            histories[current.story to current.branch] = previous + SceneMessage(
                (previous.lastOrNull()?.id ?: 0) + 1, accepted.narration, false)
            selected = current.copy(revision = accepted.revision)
            return accepted
        }
        override fun close() { closes++ }
    }

    private class Demo : DemoGateway {
        val responses = mutableListOf<Response>()
        var commits = 0
        override suspend fun respond(action: DemoAction, revision: Long, mode: DemoMode): DemoResult {
            responses += Response(action, null, revision, mode)
            return DemoResult.Accepted(revision + 1, "SCRIPTED demo", "SCRIPTED demo response")
        }
        override suspend fun commitAsync(result: DemoResult): DemoResult { commits++; return result }
    }

    @Before fun setup() { Dispatchers.setMain(dispatcher) }
    @After fun cleanup() { store.clear(); Dispatchers.resetMain() }
    private fun model(gateway: DemoGateway) = ShellViewModel(gateway).also { store.put("quick-${modelCount++}", it) }

    @Test fun staleStoryAtACompatibleHeadCannotDispatchIntoTheNewStory() = runTest(dispatcher) {
        val gateway = Stories()
        val model = model(gateway)
        advanceUntilIdle()
        val renderedA = checkNotNull(model.state.value.selectedStory)
        model.resume(b)
        advanceUntilIdle()
        val before = model.state.value
        val historyBefore = before.messages.map { it.copy() }
        model.submit(DemoAction.GIVE_POTION, renderedA)
        advanceUntilIdle()
        assertTrue(gateway.responses.isEmpty())
        assertEquals(0, gateway.commits)
        assertEquals(before, model.state.value)
        assertEquals(historyBefore, model.state.value.messages)
        assertEquals(b, gateway.selected)
        assertEquals(listOf(b), gateway.resumes)
    }

    @Test fun staleBranchAtTheSameHeadCannotDispatchIntoACompatibleFork() = runTest(dispatcher) {
        val gateway = Stories()
        val model = model(gateway)
        advanceUntilIdle()
        val renderedMain = checkNotNull(model.state.value.selectedStory)
        model.resume(fork)
        advanceUntilIdle()
        val before = model.state.value
        val historyBefore = before.messages.map { it.copy() }
        model.submit(DemoAction.TRY_ABILITY, renderedMain)
        advanceUntilIdle()
        assertTrue(gateway.responses.isEmpty())
        assertEquals(0, gateway.commits)
        assertEquals(before, model.state.value)
        assertEquals(historyBefore, model.state.value.messages)
        assertEquals(fork, gateway.selected)
    }

    @Test fun nullRenderedScopeCannotAttachToAnOpenedSavedStory() = runTest(dispatcher) {
        val gateway = Stories()
        val model = model(gateway)
        advanceUntilIdle()
        val before = model.state.value
        model.submit(DemoAction.GIVE_POTION, null)
        advanceUntilIdle()
        assertTrue(gateway.responses.isEmpty())
        assertEquals(0, gateway.commits)
        assertEquals(before, model.state.value)
        assertEquals(before.messages, model.state.value.messages)
    }

    @Test fun savedRenderedScopeCannotAttachToANullDemoScope() = runTest(dispatcher) {
        val gateway = Demo()
        val model = model(gateway)
        val before = model.state.value
        model.submit(DemoAction.TRY_ABILITY, a)
        advanceUntilIdle()
        assertTrue(gateway.responses.isEmpty())
        assertEquals(0, gateway.commits)
        assertEquals(before, model.state.value)
        assertEquals(before.messages, model.state.value.messages)
    }

    @Test fun currentScopeQuickActionsWorkWhenTextInferenceIsUnavailable() = runTest(dispatcher) {
        val gateway = Stories()
        val model = model(gateway)
        advanceUntilIdle()
        assertEquals(TextProvider.UNAVAILABLE, model.state.value.textProvider)
        model.submit(DemoAction.GIVE_POTION, checkNotNull(model.state.value.selectedStory))
        advanceUntilIdle()
        assertEquals(listOf(Response(DemoAction.GIVE_POTION, a, 7, DemoMode.ACCEPTED)), gateway.responses)
        assertEquals(1, gateway.commits)
        assertEquals(8L, model.state.value.revision)
        assertEquals(a.copy(revision = 8), model.state.value.selectedStory)
        assertEquals("SCRIPTED accepted quick action", model.state.value.messages.last().text)
    }

    @Test fun sameScopeCopiedAndRefreshedMetadataUsesCurrentAuthoritativeRevision() = runTest(dispatcher) {
        val gateway = Stories()
        val model = model(gateway)
        advanceUntilIdle()
        val renderedOld = checkNotNull(model.state.value.selectedStory).copy()
        assertNotSame(gateway.selected, renderedOld)
        gateway.selected = a.copy(title = "Refreshed title", revision = 19)
        model.recover()
        advanceUntilIdle()
        model.submit(DemoAction.TRY_ABILITY, renderedOld)
        advanceUntilIdle()
        assertEquals(listOf(Response(DemoAction.TRY_ABILITY, a.copy(title = "Refreshed title", revision = 19),
            19, DemoMode.ACCEPTED)), gateway.responses)
        assertEquals(1, gateway.commits)
        assertEquals(20L, model.state.value.revision)
        assertEquals("Refreshed title", model.state.value.selectedStory?.title)
    }

    @Test fun demoNullScopeAndTrustedOneArgumentRoutesRemainUsable() = runTest(dispatcher) {
        val demo = Demo()
        val demoModel = model(demo)
        demoModel.submit(DemoAction.TRY_ABILITY, null)
        advanceUntilIdle()
        assertEquals(listOf(Response(DemoAction.TRY_ABILITY, null, 0, DemoMode.ACCEPTED)), demo.responses)
        assertEquals(1, demo.commits)
        assertEquals(1L, demoModel.state.value.revision)
        val gateway = Stories()
        val savedModel = model(gateway)
        advanceUntilIdle()
        savedModel.submit(DemoAction.GIVE_POTION)
        advanceUntilIdle()
        assertEquals(listOf(Response(DemoAction.GIVE_POTION, a, 7, DemoMode.ACCEPTED)), gateway.responses)
        assertEquals(1, gateway.commits)
        assertEquals(8L, savedModel.state.value.revision)
    }

    @Test fun matchingScopeStillRespectsBusyRecoveryUnresolvedAndDisposedOwnership() = runTest(dispatcher) {
        val gateway = Stories()
        val model = model(gateway)
        advanceUntilIdle()
        val release = CompletableDeferred<Unit>()
        gateway.resumeGate = release
        model.resume(b)
        runCurrent()
        val busy = model.state.value
        assertTrue(busy.busy)
        model.submit(DemoAction.GIVE_POTION, a)
        runCurrent()
        assertEquals(busy, model.state.value)
        assertTrue(gateway.responses.isEmpty())
        release.complete(Unit)
        advanceUntilIdle()
        gateway.resumeGate = null
        gateway.recoveryFails = true
        model.recover()
        advanceUntilIdle()
        val recovery = model.state.value
        assertTrue(recovery.recoveryRequired)
        model.submit(DemoAction.TRY_ABILITY, b)
        advanceUntilIdle()
        assertEquals(recovery, model.state.value)
        assertTrue(gateway.responses.isEmpty())
        gateway.recoveryFails = false
        gateway.selected = null
        model.recover()
        advanceUntilIdle()
        val unresolved = model.state.value
        assertNull(unresolved.selectedStory)
        model.submit(DemoAction.GIVE_POTION, null)
        advanceUntilIdle()
        assertEquals(unresolved, model.state.value)
        assertTrue(gateway.responses.isEmpty())
        // Restore a valid scope so disposal, rather than a null selection, is the quiet fence.
        model.resume(b)
        advanceUntilIdle()
        assertEquals(b, model.state.value.selectedStory)
        store.clear()
        val closed = model.state.value
        model.submit(DemoAction.GIVE_POTION, b)
        advanceUntilIdle()
        assertEquals(closed, model.state.value)
        assertTrue(gateway.responses.isEmpty())
        assertEquals(0, gateway.commits)
        assertEquals(1, gateway.closes)
    }
}

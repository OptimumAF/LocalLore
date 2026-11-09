/* Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0 */
package org.locallore.app

import androidx.lifecycle.ViewModelStore
import kotlinx.coroutines.CompletableDeferred
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.ExperimentalCoroutinesApi
import kotlinx.coroutines.NonCancellable
import kotlinx.coroutines.test.StandardTestDispatcher
import kotlinx.coroutines.test.advanceUntilIdle
import kotlinx.coroutines.test.runCurrent
import kotlinx.coroutines.test.runTest
import kotlinx.coroutines.test.resetMain
import kotlinx.coroutines.test.setMain
import kotlinx.coroutines.withContext
import org.junit.After
import org.junit.Assert.*
import org.junit.Before
import org.junit.Test

/** Real ViewModel publication with a synthetic gateway; no native mechanics or inference claim. */
@OptIn(ExperimentalCoroutinesApi::class)
class PlayerInventoryShellTest {
    private val dispatcher = StandardTestDispatcher()
    private val store = ViewModelStore()
    private val a = SavedStory("inventory-a", "main", "A", 7)
    private val b = SavedStory("inventory-b", "main", "B", 7)
    private val fork = a.copy(branch = "child")
    private val owned = listOf(PlayerInventoryItem("a-owned-stack", 7), PlayerInventoryItem("z-loan", 3))
    private val other = listOf(PlayerInventoryItem("other-story-only", 2))
    private val inherited = listOf(PlayerInventoryItem("child-only", 5))
    private val input = PlayInput(PlayInputKind.DIALOGUE, "SYNTHETIC unchanged dialogue — こんにちは")

    private inner class InventoryGateway : DemoGateway {
        override val durable = true
        var selected = a
        val inventory = mutableMapOf<Pair<String, String>, List<PlayerInventoryItem>?>(
            (a.story to a.branch) to owned,
            (b.story to b.branch) to other,
            (fork.story to fork.branch) to inherited,
        )
        var initializeGate: CompletableDeferred<Unit>? = null
        var responseGate: CompletableDeferred<Unit>? = null
        var recoveryFails = false
        var commits = 0
        var closes = 0
        var cancellations = 0
        var snapshots = 0
        var responses = 0
        private fun saved() = SavedSnapshot(
            revision = selected.revision, potionOwner = "LEGACY-POTION-TEXT-IS-NOT-INVENTORY",
            messages = listOf(SceneMessage(1, "SYNTHETIC accepted ${selected.story}/${selected.branch}", false)),
            location = "/synthetic/inventory", schemaVersion = 1, stories = listOf(a, b), selected = selected,
            textProvider = TextProvider.SCRIPTED, inventory = inventory[selected.story to selected.branch],
        )
        override suspend fun initialize(): SavedSnapshot { initializeGate?.await(); return saved() }
        override suspend fun snapshot(): SavedSnapshot { snapshots++; return saved() }
        override suspend fun resumeSaved(story: SavedStory): SavedSnapshot { selected = story; return saved() }
        override suspend fun recoverSaved(): SavedSnapshot {
            if (recoveryFails) throw WorkspaceFailure("Malformed")
            return saved()
        }
        override suspend fun cancelSaved() = saved()
        override suspend fun respondText(input: PlayInput, revision: Long): DemoResult {
            responses++
            assertEquals(selected.revision, revision)
            val proposedRevision = revision + 1
            responseGate?.let { gate -> withContext(NonCancellable) { gate.await() } }
            return DemoResult.Accepted(proposedRevision, "ANOTHER-LEGACY-POTION-STRING", "SYNTHETIC accepted reply")
        }
        override suspend fun respond(action: DemoAction, revision: Long, mode: DemoMode) =
            DemoResult.Rejected("Unsupported")
        override suspend fun commitAsync(result: DemoResult): DemoResult {
            commits++
            val accepted = result as DemoResult.Accepted
            check(accepted.revision == selected.revision + 1)
            selected = selected.copy(revision = accepted.revision)
            inventory[selected.story to selected.branch] = listOf(PlayerInventoryItem("z-loan", 3))
            return accepted
        }
        override fun cancel() { cancellations++ }
        override fun close() { closes++ }
    }

    @Before fun setup() { Dispatchers.setMain(dispatcher) }
    @After fun cleanup() { store.clear(); Dispatchers.resetMain() }
    private fun model(gateway: InventoryGateway) = ShellViewModel(gateway).also { store.put("inventory", it) }

    @Test fun unknownOpeningBecomesKnownInventoryAndSameHeadStoryBranchChangesReplaceIt() = runTest(dispatcher) {
        val gateway = InventoryGateway()
        val release = CompletableDeferred<Unit>()
        gateway.initializeGate = release
        val model = model(gateway)
        runCurrent()
        assertNull(model.state.value.inventory)
        assertTrue(model.state.value.busy)
        release.complete(Unit)
        advanceUntilIdle()
        assertEquals(owned, model.state.value.inventory)
        model.resume(b)
        advanceUntilIdle()
        assertEquals(b, model.state.value.selectedStory)
        assertEquals(7L, model.state.value.revision)
        assertEquals(other, model.state.value.inventory)
        model.resume(fork)
        advanceUntilIdle()
        assertEquals(fork, model.state.value.selectedStory)
        assertEquals(inherited, model.state.value.inventory)
        assertEquals(0, gateway.responses)
        assertEquals(0, gateway.commits)
    }

    @Test fun refreshPublishesNullAndKnownEmptyWithoutRetainingOldItemsOrReadingPotionText() = runTest(dispatcher) {
        val gateway = InventoryGateway()
        val model = model(gateway)
        advanceUntilIdle()
        assertEquals(owned, model.state.value.inventory)
        gateway.inventory[a.story to a.branch] = null
        model.recover()
        advanceUntilIdle()
        assertNull(model.state.value.inventory)
        assertEquals(a, model.state.value.selectedStory)
        gateway.inventory[a.story to a.branch] = emptyList()
        model.recover()
        advanceUntilIdle()
        assertEquals(emptyList<PlayerInventoryItem>(), model.state.value.inventory)
        assertEquals("LEGACY-POTION-TEXT-IS-NOT-INVENTORY", model.state.value.potionOwner)
        assertEquals(0, gateway.commits)
    }

    @Test fun acceptedOutcomePublishesTheCoherentFreshInventoryAndRevisionTogether() = runTest(dispatcher) {
        val gateway = InventoryGateway()
        val model = model(gateway)
        advanceUntilIdle()
        model.submitText(input, a)
        advanceUntilIdle()
        assertEquals(1, gateway.responses)
        assertEquals(1, gateway.commits)
        assertEquals(8L, model.state.value.revision)
        assertEquals(a.copy(revision = 8), model.state.value.selectedStory)
        assertEquals(listOf(PlayerInventoryItem("z-loan", 3)), model.state.value.inventory)
        assertEquals(1, gateway.snapshots)
        assertFalse(model.state.value.busy)
    }

    @Test fun failedRefreshRetainsThePriorCoherentInventoryAndRequiresRecovery() = runTest(dispatcher) {
        val gateway = InventoryGateway()
        val model = model(gateway)
        advanceUntilIdle()
        val before = model.state.value
        gateway.recoveryFails = true
        gateway.inventory[a.story to a.branch] = other
        model.recover()
        advanceUntilIdle()
        assertTrue(model.state.value.recoveryRequired)
        assertEquals(before.selectedStory, model.state.value.selectedStory)
        assertEquals(before.revision, model.state.value.revision)
        assertEquals(before.inventory, model.state.value.inventory)
        assertEquals(before.messages, model.state.value.messages)
        assertEquals(0, gateway.commits)
    }

    @Test fun cancelledLateResponseCannotAttachOriginalInventoryOrCommitIntoAnotherStory() = runTest(dispatcher) {
        val gateway = InventoryGateway()
        val model = model(gateway)
        advanceUntilIdle()
        val release = CompletableDeferred<Unit>()
        gateway.responseGate = release
        model.submitText(input, a)
        runCurrent()
        assertTrue(model.state.value.preparingResponse)
        model.cancel()
        runCurrent()
        assertEquals(1, gateway.cancellations)
        assertEquals(owned, model.state.value.inventory)
        model.resume(b)
        runCurrent()
        val selectedB = model.state.value
        assertEquals(b, selectedB.selectedStory)
        assertEquals(other, selectedB.inventory)
        release.complete(Unit)
        advanceUntilIdle()
        assertEquals(selectedB, model.state.value)
        assertEquals(0, gateway.commits)
        assertEquals(0, gateway.snapshots)
    }

    @Test fun disposalFencesNoncooperativeCompletionAndKeepsInventoryWithoutNewReads() = runTest(dispatcher) {
        val gateway = InventoryGateway()
        val model = model(gateway)
        advanceUntilIdle()
        val release = CompletableDeferred<Unit>()
        gateway.responseGate = release
        model.submitText(input, a)
        runCurrent()
        store.clear()
        val closed = model.state.value
        release.complete(Unit)
        advanceUntilIdle()
        model.recover()
        model.resume(b)
        advanceUntilIdle()
        assertEquals(closed, model.state.value)
        assertEquals(owned, closed.inventory)
        assertEquals(1, gateway.closes)
        assertEquals(0, gateway.commits)
        assertEquals(0, gateway.snapshots)
    }
}

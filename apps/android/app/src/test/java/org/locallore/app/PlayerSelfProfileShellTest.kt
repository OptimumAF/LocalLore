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

/** Publication/ownership tests use a synthetic gateway, not another gameplay engine. */
@OptIn(ExperimentalCoroutinesApi::class)
class PlayerSelfProfileShellTest {
    private val dispatcher = StandardTestDispatcher()
    private val store = ViewModelStore()
    private val a = SavedStory("profile-a", "main", "A", 7)
    private val b = SavedStory("profile-b", "main", "B", 7)
    private val fork = a.copy(branch = "child")
    private val first = PlayerSelfProfile(
        "a-opaque-self", "Éva 海", "exact-native-place", true, 12,
        listOf(PlayerAbility("measure", 2)), listOf(PlayerAttribute("Patience 海", -3)),
        listOf("Old scratch"), listOf("Harbor readers"), listOf("Find the violet beacon"),
    )
    private val second = first.copy(observer = "a-other-self", name = "Other player", energy = 4)
    private val child = first.copy(location = "child-native-place", goals = listOf("A different goal"))
    private val input = PlayInput(PlayInputKind.DIALOGUE, "Unsent intent is not a profile — こんにちは")

    private inner class ProfileGateway : DemoGateway {
        override val durable = true
        var selected = a
        val profiles = mutableMapOf<Pair<String, String>, PlayerSelfProfile?>(
            (a.story to a.branch) to first, (b.story to b.branch) to second,
            (fork.story to fork.branch) to child,
        )
        var initializeGate: CompletableDeferred<Unit>? = null
        var responseGate: CompletableDeferred<Unit>? = null
        var failRecovery = false
        var responses = 0
        var commits = 0
        var snapshots = 0
        var cancellations = 0
        var closes = 0
        private fun saved() = SavedSnapshot(
            selected.revision, "LEGACY-OWNER-IS-NOT-SELF-STATE",
            listOf(SceneMessage(1, "Accepted ${selected.story}/${selected.branch}", false)),
            "D:/synthetic/database-not-actor-location", 1, listOf(a, b), selected,
            textProvider = TextProvider.SCRIPTED,
            inventory = listOf(PlayerInventoryItem("owned-stack", 3)),
            playerProfile = profiles[selected.story to selected.branch],
        )
        override suspend fun initialize(): SavedSnapshot { initializeGate?.await(); return saved() }
        override suspend fun snapshot(): SavedSnapshot { snapshots++; return saved() }
        override suspend fun resumeSaved(story: SavedStory): SavedSnapshot { selected = story; return saved() }
        override suspend fun recoverSaved(): SavedSnapshot {
            if (failRecovery) throw WorkspaceFailure("Malformed")
            return saved()
        }
        override suspend fun cancelSaved() = saved()
        override suspend fun respondText(input: PlayInput, revision: Long): DemoResult {
            responses++
            assertEquals(selected.revision, revision)
            val next = revision + 1
            responseGate?.let { gate -> withContext(NonCancellable) { gate.await() } }
            return DemoResult.Accepted(next, "PROPOSAL-TEXT-IS-NOT-PROFILE", "Recorded reply")
        }
        override suspend fun respond(action: DemoAction, revision: Long, mode: DemoMode) =
            DemoResult.Rejected("Unsupported")
        override suspend fun commitAsync(result: DemoResult): DemoResult {
            commits++
            val accepted = result as DemoResult.Accepted
            check(accepted.revision == selected.revision + 1)
            selected = selected.copy(revision = accepted.revision)
            profiles[selected.story to selected.branch] = first.copy(energy = 9,
                abilities = listOf(PlayerAbility("measure", 3)), injuries = emptyList())
            return accepted
        }
        override fun cancel() { cancellations++ }
        override fun close() { closes++ }
    }

    @Before fun setup() { Dispatchers.setMain(dispatcher) }
    @After fun cleanup() { store.clear(); Dispatchers.resetMain() }
    private fun model(gateway: ProfileGateway) = ShellViewModel(gateway).also { store.put("profile", it) }

    @Test fun openingAndSameHeadStoryOrBranchChangesPublishTheWholeSelectedProfile() = runTest(dispatcher) {
        val gateway = ProfileGateway()
        val release = CompletableDeferred<Unit>()
        gateway.initializeGate = release
        val model = model(gateway)
        runCurrent()
        assertNull(model.state.value.playerProfile)
        assertTrue(model.state.value.busy)
        release.complete(Unit)
        advanceUntilIdle()
        assertEquals(first, model.state.value.playerProfile)
        assertNotEquals(model.state.value.storageLocation, model.state.value.playerProfile!!.location)
        for ((story, profile) in listOf(b to second, fork to child)) {
            model.resume(story)
            advanceUntilIdle()
            assertEquals(story, model.state.value.selectedStory)
            assertEquals(7L, model.state.value.revision)
            assertEquals(profile, model.state.value.playerProfile)
            assertEquals(listOf(PlayerInventoryItem("owned-stack", 3)), model.state.value.inventory)
        }
        assertEquals(0, gateway.responses)
        assertEquals(0, gateway.commits)
    }

    @Test fun publicationDetachesAndProtectsEveryNestedCallerOwnedCollection() = runTest(dispatcher) {
        val abilities = first.abilities.toMutableList()
        val attributes = first.attributes.toMutableList()
        val injuries = first.injuries.toMutableList()
        val affiliations = first.affiliations.toMutableList()
        val goals = first.goals.toMutableList()
        val gateway = ProfileGateway()
        gateway.profiles[a.story to a.branch] = first.copy(abilities = abilities, attributes = attributes,
            injuries = injuries, affiliations = affiliations, goals = goals)
        val model = model(gateway)
        advanceUntilIdle()
        val published = checkNotNull(model.state.value.playerProfile)
        assertEquals(first, published)
        abilities.clear(); attributes.clear(); injuries.clear(); affiliations.clear(); goals.clear()
        assertEquals(first, published)
        fun <T> immutable(rows: List<T>, injected: T) {
            try { (rows as MutableList<T>).add(injected); fail("Published profile list is mutable") }
            catch (_: UnsupportedOperationException) { }
        }
        immutable(published.abilities, PlayerAbility("forged", 9))
        immutable(published.attributes, PlayerAttribute("forged", 9))
        immutable(published.injuries, "forged")
        immutable(published.affiliations, "forged")
        immutable(published.goals, "forged")
        assertEquals(first, model.state.value.playerProfile)
        model.recover()
        advanceUntilIdle()
        assertEquals(first.copy(abilities = emptyList(), attributes = emptyList(), injuries = emptyList(),
            affiliations = emptyList(), goals = emptyList()), model.state.value.playerProfile)
        assertEquals(first, published)
    }

    @Test fun nullAndKnownEmptyRefreshReplaceOldProfileWithoutReadingLegacyDisplayStrings() = runTest(dispatcher) {
        val gateway = ProfileGateway()
        val model = model(gateway)
        advanceUntilIdle()
        gateway.profiles[a.story to a.branch] = null
        model.recover()
        advanceUntilIdle()
        assertNull(model.state.value.playerProfile)
        val empty = first.copy(alive = false, energy = 0, abilities = emptyList(), attributes = emptyList(),
            injuries = emptyList(), affiliations = emptyList(), goals = emptyList())
        gateway.profiles[a.story to a.branch] = empty
        model.recover()
        advanceUntilIdle()
        assertEquals(empty, model.state.value.playerProfile)
        assertEquals(a, model.state.value.selectedStory)
        assertEquals("LEGACY-OWNER-IS-NOT-SELF-STATE", model.state.value.potionOwner)
        assertEquals(0, gateway.responses)
        assertEquals(0, gateway.commits)
    }

    @Test fun acceptedRefreshPublishesProfileWithItsExactNewHeadAndFailedReadRetainsThatCoherentState() = runTest(dispatcher) {
        val gateway = ProfileGateway()
        val model = model(gateway)
        advanceUntilIdle()
        model.submitText(input, a)
        advanceUntilIdle()
        val accepted = model.state.value
        assertEquals(8L, accepted.revision)
        assertEquals(a.copy(revision = 8), accepted.selectedStory)
        assertEquals(first.copy(energy = 9, abilities = listOf(PlayerAbility("measure", 3)),
            injuries = emptyList()), accepted.playerProfile)
        assertEquals(1, gateway.responses)
        assertEquals(1, gateway.commits)
        assertEquals(1, gateway.snapshots)
        gateway.failRecovery = true
        gateway.profiles[a.story to a.branch] = second
        model.recover()
        advanceUntilIdle()
        val refused = model.state.value
        assertTrue(refused.recoveryRequired)
        assertEquals(accepted.playerProfile, refused.playerProfile)
        assertEquals(accepted.selectedStory, refused.selectedStory)
        assertEquals(accepted.revision, refused.revision)
        assertEquals(accepted.messages, refused.messages)
        assertEquals(accepted.inventory, refused.inventory)
    }

    @Test fun cancellationAndRetainedOldScopeInputCannotAttachLateProfileOrCommitIntoAnotherStory() = runTest(dispatcher) {
        val gateway = ProfileGateway()
        val model = model(gateway)
        advanceUntilIdle()
        val release = CompletableDeferred<Unit>()
        gateway.responseGate = release
        try {
            model.submitText(input, a)
            runCurrent()
            assertTrue(model.state.value.preparingResponse)
            model.cancel()
            runCurrent()
            assertEquals(1, gateway.cancellations)
            model.resume(b)
            runCurrent()
            val selectedB = model.state.value
            assertEquals(b, selectedB.selectedStory)
            assertEquals(second, selectedB.playerProfile)
            release.complete(Unit)
            advanceUntilIdle()
            model.submitText(input, a)
            advanceUntilIdle()
            assertEquals(selectedB, model.state.value)
            assertEquals(1, gateway.responses)
            assertEquals(0, gateway.commits)
            assertEquals(0, gateway.snapshots)
        } finally { release.complete(Unit) }
    }

    @Test fun disposalFencesNoncooperativeCompletionAndRetainedRefreshCallbacks() = runTest(dispatcher) {
        val gateway = ProfileGateway()
        val model = model(gateway)
        advanceUntilIdle()
        val release = CompletableDeferred<Unit>()
        gateway.responseGate = release
        try {
            model.submitText(input, a)
            runCurrent()
            store.clear()
            val closed = model.state.value
            release.complete(Unit)
            advanceUntilIdle()
            model.recover(); model.resume(b)
            advanceUntilIdle()
            assertEquals(closed, model.state.value)
            assertEquals(first, closed.playerProfile)
            assertEquals(1, gateway.closes)
            assertEquals(0, gateway.commits)
            assertEquals(0, gateway.snapshots)
        } finally { release.complete(Unit) }
    }
}

/* Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0 */
package org.locallore.app

import androidx.lifecycle.ViewModelStore
import kotlinx.coroutines.CompletableDeferred
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.ExperimentalCoroutinesApi
import kotlinx.coroutines.NonCancellable
import kotlinx.coroutines.test.StandardTestDispatcher
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

/** JVM controller tests. Real SQLite/JNI restart equality is separately covered by native tests. */
@OptIn(ExperimentalCoroutinesApi::class)
class DurableShellTest {
    private val dispatcher = StandardTestDispatcher()
    private val store = ViewModelStore()
    @Before fun setup() { Dispatchers.setMain(dispatcher) }
    @After fun cleanup() { store.clear(); Dispatchers.resetMain() }
    private val old = SavedStory("saved-a", "main", "Lantern Quay", 1)
    private val fresh = SavedStory("saved-b", "main", "Lantern Quay", 0)
    private fun saved(selected: SavedStory = old) = SavedSnapshot(selected.revision,
        if (selected == old) "Not in your inventory" else "You",
        if (selected == old) listOf(SceneMessage(1, "Recorded action", true), SceneMessage(2, "Saved narration", false)) else emptyList(),
        "/synthetic/no-backup/stories.sqlite3", 1, listOf(old, fresh), selected)
    private fun model(gateway: DemoGateway) = ShellViewModel(gateway).also { store.put("model", it) }
    private open inner class Durable : DemoGateway {
        override val durable = true
        var current = saved()
        var closes = 0
        override suspend fun initialize() = current
        override suspend fun snapshot() = current
        override suspend fun respond(action: DemoAction, revision: Long, mode: DemoMode): DemoResult = DemoResult.Prepared(0, 1)
        override suspend fun commitAsync(result: DemoResult): DemoResult = DemoResult.Accepted(1, "untrusted presentation", "unpublished draft")
        override suspend fun createSaved(): SavedSnapshot { current = saved(fresh); return current }
        override suspend fun resumeSaved(story: SavedStory): SavedSnapshot { current = saved(story); return current }
        override fun close() { closes++ }
    }

    @Test fun initializationRestoresOnlyAuthoritativeSnapshotAndShowsPersistence() = runTest(dispatcher) {
        val model = model(Durable())
        assertTrue(model.state.value.busy)
        model.submit(DemoAction.GIVE_POTION)
        advanceUntilIdle()
        assertTrue(model.state.value.persistent)
        assertEquals(1, model.state.value.schemaVersion)
        assertEquals(1L, model.state.value.revision)
        assertEquals("Saved narration", model.state.value.messages.last().text)
        assertEquals(2, model.state.value.stories.size)
    }
    @Test fun acceptedResultCannotInventTranscriptOutsideSavedReceipts() = runTest(dispatcher) {
        val model = model(Durable()); advanceUntilIdle()
        model.submit(DemoAction.GIVE_POTION); advanceUntilIdle()
        assertEquals(listOf("Recorded action", "Saved narration"), model.state.value.messages.map { it.text })
        assertEquals("Not in your inventory", model.state.value.potionOwner)
    }
    @Test fun newStoryRetainsLibraryAndResumeRestoresEarlierCanon() = runTest(dispatcher) {
        val model = model(Durable()); advanceUntilIdle()
        model.reset(); advanceUntilIdle()
        assertEquals(fresh, model.state.value.selectedStory)
        assertTrue(model.state.value.messages.isEmpty())
        assertEquals(listOf(old, fresh), model.state.value.stories)
        model.resume(old); advanceUntilIdle()
        assertEquals(old, model.state.value.selectedStory)
        assertEquals("Saved narration", model.state.value.messages.last().text)
    }
    @Test fun uncertainCommitBlocksNewTurnsAndRecoveryPublishesSavedHistory() = runTest(dispatcher) {
        var responses = 0
        var recovered = 0
        val gateway = object : Durable() {
            override suspend fun respond(action: DemoAction, revision: Long, mode: DemoMode): DemoResult {
                responses++; return DemoResult.Prepared(0, 1)
            }
            override suspend fun commitAsync(result: DemoResult): DemoResult = error("PRIVATE lost reply")
            override suspend fun recoverSaved(): SavedSnapshot { recovered++; return current }
        }
        val model = model(gateway); advanceUntilIdle()
        model.submit(DemoAction.GIVE_POTION); advanceUntilIdle()
        assertTrue(model.state.value.recoveryRequired)
        assertFalse(model.state.value.notice!!.contains("PRIVATE"))
        model.submit(DemoAction.GIVE_POTION); advanceUntilIdle(); assertEquals(1, responses)
        model.recover(); advanceUntilIdle()
        assertFalse(model.state.value.recoveryRequired); assertEquals(1, recovered)
        assertEquals("Saved narration", model.state.value.messages.last().text)
    }
    @Test fun cancelReconcilesCommittedCanonRatherThanClaimingRollback() = runTest(dispatcher) {
        val prepared = CompletableDeferred<DemoResult>()
        val gateway = object : Durable() {
            override suspend fun respond(action: DemoAction, revision: Long, mode: DemoMode) =
                withContext(NonCancellable) { prepared.await() }
            override suspend fun cancelSaved() = current
        }
        val model = model(gateway); advanceUntilIdle()
        model.submit(DemoAction.GIVE_POTION); runCurrent()
        model.cancel(); runCurrent()
        prepared.complete(DemoResult.Accepted(999, "Wrong", "Obsolete")); advanceUntilIdle()
        assertEquals(1L, model.state.value.revision)
        assertEquals("Saved narration", model.state.value.messages.last().text)
        assertFalse(model.state.value.notice!!.contains("Nothing changed"))
    }
    @Test fun disposalFencesLateOpeningAndRetainedResumeCallbacks() = runTest(dispatcher) {
        val opened = CompletableDeferred<SavedSnapshot>()
        val gateway = object : Durable() {
            override suspend fun initialize() = withContext(NonCancellable) { opened.await() }
        }
        val model = model(gateway); runCurrent(); store.clear()
        model.reset(); model.resume(old); model.recover()
        opened.complete(saved()); advanceUntilIdle()
        assertEquals(1, gateway.closes)
        assertTrue(model.state.value.messages.isEmpty())
    }
    @Test fun surfaceStopCannotDiscardTheCompletionOfSavedStoryOpeningOrSwitching() = runTest(dispatcher) {
        val switching = CompletableDeferred<SavedSnapshot>()
        var cancels = 0
        val gateway = object : Durable() {
            override suspend fun resumeSaved(story: SavedStory): SavedSnapshot = switching.await()
            override suspend fun cancelSaved(): SavedSnapshot { cancels++; return current }
        }
        val model = model(gateway); advanceUntilIdle()
        model.resume(fresh); runCurrent()
        model.cancel(); runCurrent()
        assertTrue(model.state.value.busy)
        switching.complete(saved(fresh)); advanceUntilIdle()
        assertEquals(fresh, model.state.value.selectedStory)
        assertEquals(0, cancels)
    }
}

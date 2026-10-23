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

/** Controller-only storage-error fixtures. No JSON shim, JNI, database, or inference. */
@OptIn(ExperimentalCoroutinesApi::class)
class StorageRecoveryShellTest {
    private val dispatcher = StandardTestDispatcher()
    private val owners = ViewModelStore()
    private var nextOwner = 0
    private val prior = SavedStory("synthetic-prior", "main", "Pressure fixture", 1)
    private val later = SavedStory("synthetic-prior", "main", "Pressure fixture", 2)
    private val fresh = SavedStory("synthetic-new", "main", "Independent fixture", 0)
    private val full = "Local storage is full. Free space, then retry recovery. Saved progress is retained."
    private val busy = "The local engine is busy. Wait briefly, then retry recovery. Saved progress is retained."
    private val privateCategory = "PRIVATE-story/path/token: not a public storage category"

    @Before fun setup() { Dispatchers.setMain(dispatcher) }
    @After fun cleanup() { owners.clear(); Dispatchers.resetMain() }

    private fun saved(story: SavedStory = prior): SavedSnapshot = SavedSnapshot(
        story.revision, if (story == fresh) "You" else "Not in your inventory",
        when (story) {
            fresh -> emptyList()
            later -> listOf(SceneMessage(1, "Recorded action", true), SceneMessage(2, "Saved narration", false),
                SceneMessage(3, "Second recorded action", true), SceneMessage(4, "Recovered receipt narration", false))
            else -> listOf(SceneMessage(1, "Recorded action", true), SceneMessage(2, "Saved narration", false))
        },
        "/synthetic/no-backup/stories.sqlite3", 1, if (story == fresh) listOf(prior, fresh) else listOf(story, fresh), story,
        uncommittedDrafts = if (story == prior) 1 else 0, rulesProfile = "fantasy_v1",
    )
    private open inner class PressureGateway : DemoGateway {
        override val durable = true
        var current = saved()
        var initializeFailure: String? = null
        var prepareFailure: String? = null
        var commitFailure: String? = null
        var recoveryFailure: String? = null
        var responses = 0
        var commits = 0
        var recoveries = 0
        var openings = 0
        var closes = 0
        override suspend fun initialize(): SavedSnapshot {
            openings++
            initializeFailure?.let { throw WorkspaceFailure(it) }
            return current
        }
        override suspend fun snapshot() = current
        override suspend fun respond(action: DemoAction, revision: Long, mode: DemoMode): DemoResult {
            responses++
            prepareFailure?.let { throw WorkspaceFailure(it) }
            return DemoResult.Prepared(0, 1)
        }
        override suspend fun commitAsync(result: DemoResult): DemoResult {
            commits++
            commitFailure?.let { throw WorkspaceFailure(it) }
            return DemoResult.Accepted(999, "INVENTED owner", "INVENTED narration")
        }
        override suspend fun recoverSaved(): SavedSnapshot {
            recoveries++
            recoveryFailure?.let { throw WorkspaceFailure(it) }
            return current
        }
        override suspend fun cancelSaved() = current
        override suspend fun createSaved(): SavedSnapshot { current = saved(fresh); return current }
        override suspend fun resumeSaved(story: SavedStory): SavedSnapshot { current = saved(story); return current }
        override fun close() { closes++ }
    }
    private fun model(gateway: DemoGateway) = ShellViewModel(gateway).also { owners.put("model-${nextOwner++}", it) }
    private fun assertPresentation(expected: SavedSnapshot, actual: ShellState) {
        assertEquals(expected.revision, actual.revision)
        assertEquals(expected.potionOwner, actual.potionOwner)
        assertEquals(expected.messages, actual.messages)
        assertEquals(expected.selected, actual.selectedStory)
        assertEquals(expected.stories, actual.stories)
        assertEquals(expected.uncommittedDrafts, actual.uncommittedDrafts)
        assertEquals(expected.location, actual.storageLocation)
        assertEquals(expected.schemaVersion, actual.schemaVersion)
        assertEquals(expected.rulesProfile, actual.rulesProfile)
        assertTrue(actual.persistent)
        assertFalse(actual.busy)
        assertFalse(actual.preparingResponse)
    }
    private fun assertRecovery(model: ShellViewModel, expected: SavedSnapshot, notice: String) {
        assertPresentation(expected, model.state.value)
        assertTrue(model.state.value.recoveryRequired)
        assertEquals(notice, model.state.value.notice)
    }

    @Test fun initializationFullAndBusyRequireRecoveryWithoutInventingAcceptedState() = runTest(dispatcher) {
        for ((category, notice) in listOf("Full" to full, "Busy" to busy)) {
            val gateway = PressureGateway().also { it.initializeFailure = category }
            val model = model(gateway)
            advanceUntilIdle()
            assertTrue(model.state.value.recoveryRequired)
            assertEquals(notice, model.state.value.notice)
            assertFalse(model.state.value.busy)
            assertTrue(model.state.value.messages.isEmpty())
            assertNull(model.state.value.selectedStory)
            assertEquals(0L, model.state.value.revision)
            model.submit(DemoAction.GIVE_POTION)
            advanceUntilIdle()
            assertEquals(0, gateway.responses)
            model.recover()
            advanceUntilIdle()
            assertEquals(notice, model.state.value.notice)
            assertTrue(model.state.value.messages.isEmpty())
            assertTrue(model.state.value.recoveryRequired)
            gateway.initializeFailure = null
            model.recover()
            advanceUntilIdle()
            assertPresentation(saved(), model.state.value)
            assertFalse(model.state.value.recoveryRequired)
            assertEquals(3, gateway.openings)
        }
    }

    @Test fun prepareFullAndBusyKeepCanonBlockResubmissionAndRecoverOnlySnapshot() = runTest(dispatcher) {
        for ((category, notice) in listOf("Full" to full, "Busy" to busy)) {
            val gateway = PressureGateway().also { it.prepareFailure = category }
            val model = model(gateway)
            advanceUntilIdle()
            model.submit(DemoAction.GIVE_POTION)
            advanceUntilIdle()
            assertRecovery(model, saved(), notice)
            assertEquals(1, gateway.responses)
            assertEquals(0, gateway.commits)
            model.submit(DemoAction.GIVE_POTION)
            advanceUntilIdle()
            assertEquals(1, gateway.responses)
            gateway.recoveryFailure = category
            repeat(2) {
                model.recover()
                advanceUntilIdle()
                assertRecovery(model, saved(), notice)
            }
            gateway.current = saved(later)
            gateway.recoveryFailure = null
            model.recover()
            advanceUntilIdle()
            assertPresentation(saved(later), model.state.value)
            assertFalse(model.state.value.recoveryRequired)
            assertEquals(3, gateway.recoveries)
            assertEquals(1, gateway.responses)
            assertEquals(0, gateway.commits)
            assertFalse(model.state.value.messages.any { it.text.contains("INVENTED") })
        }
    }

    @Test fun commitFullAndBusyKeepCanonUntilAuthoritativeRecovery() = runTest(dispatcher) {
        for ((category, notice) in listOf("Full" to full, "Busy" to busy)) {
            val gateway = PressureGateway().also { it.commitFailure = category }
            val model = model(gateway)
            advanceUntilIdle()
            model.submit(DemoAction.GIVE_POTION)
            advanceUntilIdle()
            assertRecovery(model, saved(), notice)
            model.submit(DemoAction.GIVE_POTION)
            advanceUntilIdle()
            assertEquals(1, gateway.responses)
            assertEquals(1, gateway.commits)
            gateway.current = saved(later)
            gateway.recoveryFailure = category
            repeat(2) {
                model.recover()
                advanceUntilIdle()
                // Even a changed gateway snapshot cannot leak through a failed recovery.
                assertRecovery(model, saved(), notice)
            }
            gateway.recoveryFailure = null
            model.recover()
            advanceUntilIdle()
            assertPresentation(saved(later), model.state.value)
            assertFalse(model.state.value.recoveryRequired)
            assertEquals(1, gateway.responses)
            assertEquals(1, gateway.commits)
            assertEquals(3, gateway.recoveries)
        }
    }

    @Test fun recoveryMayRemainUncommittedWithoutFabricatingAnAcceptedReceipt() = runTest(dispatcher) {
        val gateway = PressureGateway().also { it.prepareFailure = "Full" }
        val model = model(gateway)
        advanceUntilIdle()
        model.submit(DemoAction.GIVE_POTION)
        advanceUntilIdle()
        assertRecovery(model, saved(), full)
        model.recover()
        advanceUntilIdle()
        assertPresentation(saved(), model.state.value)
        assertFalse(model.state.value.recoveryRequired)
        assertEquals(1, model.state.value.uncommittedDrafts)
        assertEquals(1L, model.state.value.revision)
        assertEquals(1, gateway.responses)
        assertEquals(0, gateway.commits)
    }

    @Test fun unknownInitializationAndRecoveryCategoriesUseGenericNoticesWithoutPrivateText() = runTest(dispatcher) {
        val generic = "Saved progress could not be confirmed. Retry recovery; existing saves are retained."
        val gateway = PressureGateway().also { it.initializeFailure = privateCategory }
        val model = model(gateway)
        advanceUntilIdle()
        assertEquals(generic, model.state.value.notice)
        assertTrue(model.state.value.recoveryRequired)
        assertFalse(model.state.value.notice!!.contains("PRIVATE"))
        gateway.initializeFailure = null
        model.recover()
        advanceUntilIdle()
        gateway.recoveryFailure = privateCategory
        model.recover()
        advanceUntilIdle()
        assertRecovery(model, saved(), generic)
        assertFalse(model.state.value.notice!!.contains(privateCategory))
    }

    @Test fun unknownPrepareAndCommitCategoriesUseGenericNoticesAndNeverEchoCategory() = runTest(dispatcher) {
        val generic = "Unable to confirm the outcome. Retry recovery using the original response key; saves are retained."
        for (duringCommit in listOf(false, true)) {
            val gateway = PressureGateway().also {
                if (duringCommit) it.commitFailure = privateCategory else it.prepareFailure = privateCategory
            }
            val model = model(gateway)
            advanceUntilIdle()
            model.submit(DemoAction.GIVE_POTION)
            advanceUntilIdle()
            assertRecovery(model, saved(), generic)
            assertFalse(model.state.value.notice!!.contains("PRIVATE"))
            model.submit(DemoAction.GIVE_POTION)
            advanceUntilIdle()
            assertEquals(1, gateway.responses)
        }
    }

    @Test fun disposedOpeningFailureAndRetainedCallbacksCannotPublishOrReopen() = runTest(dispatcher) {
        val opening = CompletableDeferred<SavedSnapshot>()
        val gateway = object : PressureGateway() {
            override suspend fun initialize() = withContext(NonCancellable) { opening.await() }
        }
        val model = model(gateway)
        runCurrent()
        owners.clear()
        val disposed = model.state.value
        model.recover(); model.reset(); model.resume(prior); model.submit(DemoAction.GIVE_POTION)
        opening.completeExceptionally(WorkspaceFailure("Full"))
        advanceUntilIdle()
        assertEquals(disposed, model.state.value)
        assertEquals(1, gateway.closes)
        assertEquals(0, gateway.responses)
    }

    @Test fun lateStorageFailureCannotOverwriteReplacementStoryAfterCancelAndNewStory() = runTest(dispatcher) {
        val response = CompletableDeferred<DemoResult>()
        val gateway = object : PressureGateway() {
            override suspend fun respond(action: DemoAction, revision: Long, mode: DemoMode) =
                withContext(NonCancellable) { response.await() }
        }
        val model = model(gateway)
        advanceUntilIdle()
        model.submit(DemoAction.GIVE_POTION)
        runCurrent()
        model.cancel()
        runCurrent()
        model.reset()
        advanceUntilIdle()
        assertPresentation(saved(fresh), model.state.value)
        val replacement = model.state.value
        response.completeExceptionally(WorkspaceFailure("Busy"))
        advanceUntilIdle()
        assertEquals(replacement, model.state.value)
        assertFalse(model.state.value.recoveryRequired)
    }

    @Test fun disposalFencesLateRecoveryFailureWithoutChangingPresentedCanon() = runTest(dispatcher) {
        val recovery = CompletableDeferred<SavedSnapshot>()
        val gateway = object : PressureGateway() {
            override suspend fun recoverSaved() = withContext(NonCancellable) { recovery.await() }
        }.also { it.commitFailure = "Full" }
        val model = model(gateway)
        advanceUntilIdle()
        model.submit(DemoAction.GIVE_POTION)
        advanceUntilIdle()
        model.recover()
        runCurrent()
        owners.clear()
        val disposed = model.state.value
        recovery.completeExceptionally(WorkspaceFailure("Busy"))
        advanceUntilIdle()
        assertEquals(disposed, model.state.value)
        assertEquals(saved().messages, model.state.value.messages)
        assertEquals(1, gateway.closes)
    }
}

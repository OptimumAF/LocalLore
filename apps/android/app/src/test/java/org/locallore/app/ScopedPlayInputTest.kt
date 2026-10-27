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

/** Real ShellViewModel admission with a controlled gateway; no engine/canon proof. UNRUN by author. */
@OptIn(ExperimentalCoroutinesApi::class)
class ScopedPlayInputTest {
    private val dispatcher = StandardTestDispatcher()
    private val models = ViewModelStore()
    private val a = SavedStory("synthetic-a", "main", "A", 0)
    private val child = a.copy(branch = "child", revision = 3)
    private val b = SavedStory("synthetic-b", "main", "B", 5)
    private val input = PlayInput(PlayInputKind.DIALOGUE, "SYNTHETIC: these words remain only a proposed statement.")

    private data class Submission(val input: PlayInput, val scope: SavedStory, val expectedRevision: Long)

    private inner class Stories : DemoGateway {
        override val durable = true
        var selected = a
        val submissions = mutableListOf<Submission>()
        val resumes = mutableListOf<SavedStory>()
        var resumeGate: CompletableDeferred<Unit>? = null
        var failRecovery = false
        var legacyActions = 0
        var closes = 0
        private fun saved() = SavedSnapshot(
            revision = selected.revision,
            potionOwner = "Synthetic fixture only",
            messages = emptyList(),
            location = "/synthetic/scoped-play-input",
            schemaVersion = 1,
            stories = listOf(a, b),
            selected = selected,
            textProvider = TextProvider.SCRIPTED,
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
            if (failRecovery) error("Synthetic recovery refusal")
            return saved()
        }
        override suspend fun respondText(input: PlayInput, revision: Long): DemoResult {
            submissions += Submission(input, selected, revision)
            return DemoResult.Rejected("Agency")
        }
        override suspend fun respond(action: DemoAction, revision: Long, mode: DemoMode): DemoResult {
            legacyActions++
            return DemoResult.Rejected("Agency")
        }
        override fun close() { closes++ }
    }

    @Before fun setup() { Dispatchers.setMain(dispatcher) }
    @After fun cleanup() { models.clear(); Dispatchers.resetMain() }
    private fun model(gateway: Stories) = ShellViewModel(gateway).also { models.put("scoped-play", it) }

    @Test fun retainedStoryAndBranchCallbacksNeverReachTheNewGatewayScope() = runTest(dispatcher) {
        val gateway = Stories()
        val model = model(gateway)
        advanceUntilIdle()
        val renderedA = checkNotNull(model.state.value.selectedStory)
        model.resume(b)
        advanceUntilIdle()
        model.submitText(input, renderedA)
        advanceUntilIdle()
        assertTrue(gateway.submissions.isEmpty())
        assertEquals(b, model.state.value.selectedStory)
        assertEquals(b.revision, model.state.value.revision)
        assertTrue(model.state.value.messages.isEmpty())
        model.resume(child)
        advanceUntilIdle()
        model.submitText(input, renderedA)
        advanceUntilIdle()
        assertTrue(gateway.submissions.isEmpty())
        assertEquals(child, model.state.value.selectedStory)
        assertEquals(0, gateway.legacyActions)
        assertEquals(listOf(b, child), gateway.resumes)
    }

    @Test fun sameStoryBranchAllowsOldHeadAndTitleButUsesTheCurrentRevision() = runTest(dispatcher) {
        val gateway = Stories()
        val model = model(gateway)
        advanceUntilIdle()
        val oldRendered = checkNotNull(model.state.value.selectedStory)
        gateway.selected = a.copy(title = "Fresh title", revision = 9)
        model.recover()
        advanceUntilIdle()
        model.submitText(input, oldRendered)
        advanceUntilIdle()
        assertEquals(listOf(Submission(input, gateway.selected, 9)), gateway.submissions)
        assertEquals(gateway.selected, model.state.value.selectedStory)
        assertEquals(0, gateway.legacyActions)
    }

    @Test fun nullScopeCannotAttachToAnOpenedStoryAndOneArgumentHelperStillWorks() = runTest(dispatcher) {
        val gateway = Stories()
        val model = model(gateway)
        advanceUntilIdle()
        model.submitText(input, null)
        advanceUntilIdle()
        assertTrue(gateway.submissions.isEmpty())
        model.submitText(input)
        advanceUntilIdle()
        assertEquals(listOf(Submission(input, a, 0)), gateway.submissions)
    }

    @Test fun scopedOverloadKeepsBusyRecoveryAndDisposalFences() = runTest(dispatcher) {
        val gateway = Stories()
        val model = model(gateway)
        advanceUntilIdle()
        val release = CompletableDeferred<Unit>()
        gateway.resumeGate = release
        model.resume(b)
        runCurrent()
        assertTrue(model.state.value.busy)
        model.submitText(input, a)
        runCurrent()
        assertTrue(gateway.submissions.isEmpty())
        release.complete(Unit)
        advanceUntilIdle()
        gateway.resumeGate = null
        assertEquals(b, model.state.value.selectedStory)
        gateway.failRecovery = true
        model.recover()
        advanceUntilIdle()
        assertTrue(model.state.value.recoveryRequired)
        model.submitText(input, b)
        advanceUntilIdle()
        assertTrue(gateway.submissions.isEmpty())
        models.clear()
        model.submitText(input, b)
        advanceUntilIdle()
        assertTrue(gateway.submissions.isEmpty())
        assertEquals(1, gateway.closes)
    }
}

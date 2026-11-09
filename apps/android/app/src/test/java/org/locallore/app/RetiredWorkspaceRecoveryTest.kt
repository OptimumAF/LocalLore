/* Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0 */
package org.locallore.app

import androidx.lifecycle.ViewModelStore
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.ExperimentalCoroutinesApi
import kotlinx.coroutines.awaitCancellation
import kotlinx.coroutines.test.StandardTestDispatcher
import kotlinx.coroutines.test.advanceUntilIdle
import kotlinx.coroutines.test.resetMain
import kotlinx.coroutines.test.runCurrent
import kotlinx.coroutines.test.runTest
import kotlinx.coroutines.test.setMain
import org.json.JSONObject
import org.junit.After
import org.junit.Assert.assertEquals
import org.junit.Assert.assertFalse
import org.junit.Assert.assertNull
import org.junit.Assert.assertSame
import org.junit.Assert.assertTrue
import org.junit.Before
import org.junit.Test

/** Synthetic workspace snapshots exercise recovery presentation and owner handoff. */
@OptIn(ExperimentalCoroutinesApi::class)
class RetiredWorkspaceRecoveryTest {
    private val dispatcher = StandardTestDispatcher()
    private val owners = ViewModelStore()

    @Before fun setUp() { Dispatchers.setMain(dispatcher) }
    @After fun cleanUp() {
        owners.clear()
        Dispatchers.resetMain()
    }

    private val story = SavedStory("saved-a", "branch-a", "Synthetic recovery", 1)
    private val prior = SavedSnapshot(
        1, "You", listOf(SceneMessage(1, "Prior saved narration", false)),
        "/synthetic/no-backup/stories.sqlite3", 1, listOf(story), story,
    )
    private val accepted = prior.copy(
        revision = 2,
        potionOwner = "Mira",
        messages = prior.messages + listOf(
            SceneMessage(2, "Give my potion to Mira.", true),
            SceneMessage(3, "Mira accepts the potion.", false),
        ),
        stories = listOf(story.copy(revision = 2)),
        selected = story.copy(revision = 2),
    )

    private class SavedWorkspace(var snapshot: SavedSnapshot)

    private class Gateway(private val workspace: SavedWorkspace) : DemoGateway {
        override val durable = true
        val calls = mutableListOf<String>()
        var openFailure: Exception? = null
        var recoverFailure: Exception? = null
        var cancelFailure: Exception? = null
        var waitForCancellation = false
        var commit: () -> DemoResult = { error("Unexpected commit") }

        override suspend fun initialize(): SavedSnapshot {
            calls += "initialize"
            openFailure?.let { throw it }
            return workspace.snapshot
        }

        override suspend fun respond(action: DemoAction, revision: Long, mode: DemoMode): DemoResult {
            calls += "respond"
            if (waitForCancellation) awaitCancellation()
            return DemoResult.Prepared(1, 1)
        }

        override suspend fun commitAsync(result: DemoResult): DemoResult {
            calls += "commit"
            return commit()
        }

        override suspend fun recoverSaved(): SavedSnapshot {
            calls += "recover"
            recoverFailure?.let { throw it }
            return workspace.snapshot
        }

        override suspend fun cancelSaved(): SavedSnapshot {
            calls += "cancel"
            cancelFailure?.let { throw it }
            return workspace.snapshot
        }

        override fun close() { calls += "close" }
    }

    private fun model(key: String, gateway: Gateway): ShellViewModel =
        ShellViewModel(gateway).also { owners.put(key, it) }

    private fun assertSavedView(expected: SavedSnapshot, state: ShellState) {
        assertEquals(expected.revision, state.revision)
        assertEquals(expected.selected, state.selectedStory)
        assertEquals(expected.messages, state.messages)
        assertEquals(expected.potionOwner, state.potionOwner)
    }

    private fun assertRestartRequired(state: ShellState) {
        assertTrue(state.recoveryRequired)
        assertFalse(state.busy)
        val notice = state.notice.orEmpty()
        assertTrue(notice, notice.contains("Restart LocalLore"))
        assertFalse(notice, notice.contains("Retry recovery", ignoreCase = true))
        assertFalse(notice, notice.contains("Nothing changed", ignoreCase = true))
    }

    @Test fun lostCommitKeepsPriorViewAndFreshOwnerReadsOnlySavedOutcome() = runTest(dispatcher) {
        val workspace = SavedWorkspace(prior)
        val retired = Gateway(workspace).apply {
            recoverFailure = LocalInferenceUncertain()
            commit = {
                workspace.snapshot = accepted
                throw LocalInferenceUncertain()
            }
        }
        val original = model("original", retired)
        advanceUntilIdle()
        original.submit(DemoAction.GIVE_POTION)
        advanceUntilIdle()
        assertSavedView(prior, original.state.value)
        assertRestartRequired(original.state.value)

        original.recover()
        original.submit(DemoAction.GIVE_POTION)
        advanceUntilIdle()
        assertEquals(listOf("initialize", "respond", "commit"), retired.calls)
        assertSavedView(prior, original.state.value)
        owners.clear()
        assertEquals(listOf("initialize", "respond", "commit", "close"), retired.calls)

        val fresh = Gateway(workspace)
        val reopened = model("fresh", fresh)
        advanceUntilIdle()
        assertSavedView(accepted, reopened.state.value)
        assertFalse(reopened.state.value.recoveryRequired)
        assertEquals(listOf("initialize"), fresh.calls)
    }

    @Test fun retryThatLosesTheLeaseBecomesRestartOnly() = runTest(dispatcher) {
        val gateway = Gateway(SavedWorkspace(prior)).apply {
            commit = { throw WorkspaceFailure("Busy") }
            recoverFailure = LocalInferenceUncertain()
        }
        val model = model("retry", gateway)
        advanceUntilIdle()
        model.submit(DemoAction.GIVE_POTION)
        advanceUntilIdle()
        assertTrue(model.state.value.notice.orEmpty().contains("retry recovery"))

        model.recover()
        advanceUntilIdle()
        assertRestartRequired(model.state.value)
        assertSavedView(prior, model.state.value)
        model.recover()
        advanceUntilIdle()
        assertEquals(listOf("initialize", "respond", "commit", "recover"), gateway.calls)
    }

    @Test fun uncertainCancellationPreservesCanonAndDoesNotRetryRetiredOwner() = runTest(dispatcher) {
        val gateway = Gateway(SavedWorkspace(prior)).apply {
            waitForCancellation = true
            cancelFailure = LocalInferenceUncertain()
        }
        val model = model("cancel", gateway)
        advanceUntilIdle()
        model.submit(DemoAction.GIVE_POTION)
        runCurrent()
        assertTrue(model.state.value.preparingResponse)

        model.cancel()
        advanceUntilIdle()
        assertSavedView(prior, model.state.value)
        assertRestartRequired(model.state.value)
        assertFalse(model.state.value.checkingCancellation)
        model.recover()
        advanceUntilIdle()
        assertEquals(listOf("initialize", "respond", "cancel"), gateway.calls)
    }

    @Test fun uncertainInitializationDoesNotRetryOrInventASelection() = runTest(dispatcher) {
        val gateway = Gateway(SavedWorkspace(prior)).apply { openFailure = LocalInferenceUncertain() }
        val model = model("open", gateway)
        advanceUntilIdle()
        assertRestartRequired(model.state.value)
        assertNull(model.state.value.selectedStory)
        assertTrue(model.state.value.messages.isEmpty())
        model.recover()
        advanceUntilIdle()
        assertEquals(listOf("initialize"), gateway.calls)
    }

    @Test fun busyAndFullStillAllowInSessionRecovery() = runTest(dispatcher) {
        for (category in listOf("Busy", "Full")) {
            val workspace = SavedWorkspace(prior)
            val gateway = Gateway(workspace).apply { commit = { throw WorkspaceFailure(category) } }
            val model = model(category, gateway)
            advanceUntilIdle()
            model.submit(DemoAction.GIVE_POTION)
            advanceUntilIdle()
            assertTrue(model.state.value.recoveryRequired)
            assertTrue(model.state.value.notice.orEmpty().contains("retry recovery"))
            assertSavedView(prior, model.state.value)

            workspace.snapshot = accepted
            model.recover()
            advanceUntilIdle()
            assertFalse(model.state.value.recoveryRequired)
            assertSavedView(accepted, model.state.value)
            assertEquals(listOf("initialize", "respond", "commit", "recover"), gateway.calls)
        }
    }

    @Test fun terminalCommitFailureSkipsImmediateStatusAndRetainsThePendingTurn() = runTest(dispatcher) {
        assertCommitRetirement(primaryRetired = true)
    }

    @Test fun terminalStatusFailureTakesPrecedenceOverBusyCommitAndRetainsThePendingTurn() = runTest(dispatcher) {
        assertCommitRetirement(primaryRetired = false)
    }

    private suspend fun assertCommitRetirement(primaryRetired: Boolean) {
        val corpus = PresentationCaptureCorpus()
        val browsing = PresentationCaptureTransport(corpus)
        val terminal = LocalInferenceUncertain()
        val controls = mutableListOf<JSONObject>()
        var submitted: JSONObject? = null
        val transport = object : WorkspaceTransport by browsing {
            override suspend fun exchange(command: JSONObject): JSONObject {
                when (command.getString("op")) {
                    "submit" -> {
                        check(submitted == null) { "Unexpected second submission" }
                        submitted = JSONObject(command.toString())
                        val request = command.getJSONObject("request")
                        val data = JSONObject()
                            .put("turn", request.getString("turn"))
                            .put("scope", request.getJSONObject("scope"))
                            .put("expected_revision", request.getLong("expected_revision"))
                            .put("phase", "ready")
                        return JSONObject().put("version", 1).put("status", "ok").put("data", data)
                    }
                    "commit" -> {
                        controls += JSONObject(command.toString())
                        if (primaryRetired) throw terminal
                        return JSONObject().put("version", 1).put("status", "rejected").put("error", "Busy")
                    }
                    "turn_status" -> {
                        controls += JSONObject(command.toString())
                        throw terminal
                    }
                    else -> return browsing.exchange(command)
                }
            }
        }
        val gateway = DurableGateway(transport, autoCreateIfEmpty = false,
            initialScopeHint = PlayDraftScope(browsing.selected.story, browsing.selected.branch))
        try {
            val opened = initializeCaptured(gateway)
            val prepared = gateway.respond(DemoAction.GIVE_POTION, opened.revision, DemoMode.ACCEPTED)
            assertTrue(prepared is DemoResult.Prepared)
            val commitFailure = runCatching { gateway.commitAsync(prepared) }.exceptionOrNull()
            assertSame(terminal, commitFailure)
            val expectedControls = if (primaryRetired) listOf("commit") else listOf("commit", "turn_status")
            assertEquals(expectedControls, controls.map { it.getString("op") })

            // The shell blocks a stale retry. Directly probing the gateway here proves it
            // still binds the uncertain turn to its original key, scope and session.
            assertSame(terminal, runCatching { gateway.recoverSaved() }.exceptionOrNull())
            assertEquals(expectedControls + "turn_status", controls.map { it.getString("op") })
            val original = checkNotNull(submitted)
            val request = original.getJSONObject("request")
            for (control in controls) {
                assertEquals(request.getString("turn"), control.getString("turn"))
                assertEquals(original.getString("session"), control.getString("session"))
                val actualScope = control.getJSONObject("scope")
                val expectedScope = request.getJSONObject("scope")
                assertEquals(expectedScope.length(), actualScope.length())
                assertEquals(expectedScope.getString("story"), actualScope.getString("story"))
                assertEquals(expectedScope.getString("branch"), actualScope.getString("branch"))
            }
        } finally {
            gateway.close()
        }
    }
}

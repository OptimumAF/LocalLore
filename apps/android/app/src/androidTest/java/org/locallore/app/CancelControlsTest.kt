/* Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0 */
package org.locallore.app

import androidx.compose.runtime.collectAsState
import androidx.compose.runtime.getValue
import androidx.compose.ui.test.*
import androidx.compose.ui.test.junit4.createComposeRule
import androidx.lifecycle.ViewModelStore
import androidx.test.ext.junit.runners.AndroidJUnit4
import kotlinx.coroutines.CompletableDeferred
import kotlinx.coroutines.NonCancellable
import kotlinx.coroutines.withContext
import org.json.JSONArray
import org.json.JSONObject
import org.junit.Assert.*
import org.junit.Rule
import org.junit.Test
import org.junit.runner.RunWith
import org.locallore.app.ui.LocalLoreScreen

/** Real Compose/ViewModel/gateway/platform JSON; synthetic transport, no user Activity/native/save/model. */
@RunWith(AndroidJUnit4::class)
class CancelControlsTest {
    @get:Rule val compose = createComposeRule()

    private class Gate {
        val entered = CompletableDeferred<Unit>()
        val release = CompletableDeferred<Unit>()
        val returned = CompletableDeferred<Unit>()
        suspend fun pass() = withContext(NonCancellable) {
            entered.complete(Unit)
            release.await()
            returned.complete(Unit)
        }
    }

    private class Protocol : WorkspaceTransport {
        val calls = mutableListOf<JSONObject>()
        val prepare = Gate()
        val cancel = Gate()
        val snapshot = Gate()
        var holdSnapshot = false
        var changeAck: (JSONObject) -> Unit = {}
        var failure: String? = null
        var committed = false
        var closed = 0
        private var revision = 7L
        var request: JSONObject? = null
            private set
        private var committedReceipt: JSONObject? = null
        private fun scope() = JSONObject().put("story", "controls-source").put("branch", "main")
        private fun ok(data: JSONObject) = JSONObject().put("version", 1).put("status", "ok").put("data", data)
        private fun receipt(request: JSONObject, narration: String) = JSONObject()
            .put("request", copy(request)).put("narration", narration)
        private fun oldReceipt() = receipt(JSONObject().put("scope", scope()).put("intent", JSONObject()
            .put("kind", "dialogue").put("value", JSONObject().put("text", "Earlier accepted dialogue"))),
            "Earlier accepted narration")
        private fun turn(phase: String): JSONObject {
            val original = checkNotNull(request)
            return JSONObject().put("turn", original.getString("turn")).put("scope", scope())
                .put("expected_revision", original.getLong("expected_revision")).put("phase", phase)
                .put("error", JSONObject.NULL).put("receipt", committedReceipt ?: JSONObject.NULL)
        }
        fun count(op: String) = calls.count { it.getString("op") == op }
        override suspend fun exchange(command: JSONObject): JSONObject {
            calls += copy(command)
            return when (command.getString("op")) {
                "workspace" -> ok(JSONObject().put("persistent", true).put("schema_version", 1)
                    .put("database_schema_version", 5).put("location", "/synthetic/controls.sqlite3")
                    .put("stories", JSONArray().put(JSONObject().put("scope", scope()).put("title", "Source")
                        .put("revision", revision).put("drafts", 0))))
                "resume" -> ok(JSONObject().put("session", "controls-session").put("scope", scope())
                    .put("revision", revision))
                "open" -> {
                    if (holdSnapshot) snapshot.pass()
                    ok(JSONObject().put("scope", scope()).put("revision", revision))
                }
                "play_snapshot" -> {
                    assertEquals(revision, command.getLong("expected_revision"))
                    val receipts = JSONArray().put(oldReceipt())
                    committedReceipt?.let { receipts.put(copy(it)) }
                    ok(JSONObject().put("scope", scope()).put("revision", revision).put("rules", "fantasy_v1")
                        .put("inventory", JSONObject().also { if (revision == 7L) it.put("potion", JSONObject()) })
                        .put("player", JSONObject().put("scope", scope()).put("revision", revision)
                            .put("observer", "player")).put("receipts", receipts))
                }
                "branches" -> ok(JSONObject().put("version", 2).put("story_id", "controls-source")
                    .put("title", "Source").put("root_branch", "main").put("branches", JSONArray()
                        .put(JSONObject().put("scope", scope()).put("parent_branch", JSONObject.NULL)
                            .put("fork_revision", JSONObject.NULL).put("revision", revision)
                            .put("drafts", 0).put("retired", false))))
                "capabilities" -> ok(JSONObject().put("free_text", true))
                "model_status" -> ok(JSONObject().put("real_model", false)
                    .put("provider", "android-scripted-play-v2").put("status", "configured_fixture_owner")
                    .put("loaded", false))
                "submit" -> {
                    check(request == null) { "No replacement submission is allowed in this fixture" }
                    request = copy(command.getJSONObject("request"))
                    ok(turn("queued"))
                }
                "prepare" -> { prepare.pass(); ok(turn("ready")) }
                "cancel" -> {
                    cancel.pass()
                    failure?.let { return JSONObject().put("version", 1).put("status", "rejected").put("error", it) }
                    if (committed && committedReceipt == null) {
                        committedReceipt = receipt(checkNotNull(request), "Accepted despite the cancellation race")
                        revision = 8L
                    }
                    ok(turn(if (committed) "committed" else "cancelled").also(changeAck))
                }
                else -> error("Unexpected synthetic operation: ${command.getString("op")}")
            }
        }
        override fun close() { closed++ }
        companion object { fun copy(value: JSONObject) = JSONObject(value.toString()) }
    }

    private class Fixture {
        val protocol = Protocol()
        val model = ShellViewModel(DurableGateway(protocol, autoCreateIfEmpty = false), DiagnosticLog())
        val store = ViewModelStore().also { it.put("cancel-controls", model) }
    }

    private fun tag(name: String): SemanticsNodeInteraction {
        compose.onNodeWithTag("story-list").performScrollToNode(hasTestTag(name))
        return compose.onNodeWithTag(name)
    }
    private fun text(value: String): SemanticsNodeInteraction {
        compose.onNodeWithTag("story-list").performScrollToNode(hasText(value))
        return compose.onNodeWithText(value)
    }
    private fun exercise(block: Fixture.() -> Unit) {
        lateinit var fixture: Fixture
        compose.runOnIdle { fixture = Fixture() }
        compose.setContent {
            val state by fixture.model.state.collectAsState()
            LocalLoreScreen(state, fixture.model::submit, fixture.model::setMode,
                fixture.model::cancel, fixture.model::reset, onResume = fixture.model::resume,
                onRecover = fixture.model::recover, onText = fixture.model::submitText)
        }
        try {
            idle(fixture)
            compose.runOnIdle {
                assertEquals(7L, fixture.model.state.value.revision)
                assertEquals(TextProvider.SCRIPTED, fixture.model.state.value.textProvider)
                assertEquals(listOf("Earlier accepted dialogue", "Earlier accepted narration"),
                    fixture.model.state.value.messages.map { it.text })
            }
            fixture.block()
        } finally {
            // Release every noncooperative gate before the Compose rule tears down its Activity.
            compose.runOnIdle {
                fixture.store.clear()
                fixture.protocol.prepare.release.complete(Unit)
                fixture.protocol.cancel.release.complete(Unit)
                fixture.protocol.snapshot.release.complete(Unit)
            }
            compose.waitForIdle()
        }
    }
    private fun idle(f: Fixture) {
        compose.waitUntil(8_000) { !f.model.state.value.busy }
        compose.waitForIdle()
    }
    private fun beginCancellation(f: Fixture) {
        // A valid retained draft makes disabled Send meaningful rather than empty-input refusal.
        tag("play-example").performClick()
        tag("play-send").assertIsEnabled()
        tag("give-potion").assertIsEnabled().performClick()
        compose.waitUntil(8_000) { f.protocol.prepare.entered.isCompleted }
        tag("busy-status").assertTextEquals("Preparing local response…")
        tag("cancel-turn").assertIsEnabled().performClick()
        compose.waitUntil(8_000) { f.protocol.cancel.entered.isCompleted }
        tag("give-potion").assertIsNotEnabled()
        compose.onNodeWithTag("cancel-turn").assertDoesNotExist()
        compose.runOnIdle {
            assertTrue(f.model.state.value.busy)
            assertFalse(f.model.state.value.preparingResponse)
            assertEquals(1, f.protocol.count("submit"))
            assertEquals(0, f.protocol.count("commit"))
        }
    }
    private fun assertRetainedHistory(f: Fixture) {
        text("Earlier accepted dialogue").assertIsDisplayed()
        text("Earlier accepted narration").assertIsDisplayed()
        tag("revision").assertTextEquals("Accepted revision · 7")
        tag("potion-owner").assertTextEquals("Healing potion · You")
        compose.runOnIdle {
            assertEquals(7L, f.model.state.value.revision)
            assertEquals(listOf("Earlier accepted dialogue", "Earlier accepted narration"),
                f.model.state.value.messages.map { it.text })
            assertEquals(0, f.protocol.count("commit"))
        }
    }
    private fun assertBlockedControls() {
        tag("play-send").assertIsNotEnabled()
        tag("play-input").assertIsNotEnabled()
        tag("play-example").assertIsNotEnabled()
        tag("give-potion").assertIsNotEnabled()
        tag("try-ability").assertIsNotEnabled()
        tag("mode-menu").assertIsNotEnabled()
        tag("saved-library").assertIsNotEnabled()
        tag("reset-demo").assertIsNotEnabled()
    }
    private fun releasePreparation(f: Fixture) {
        compose.runOnIdle { f.protocol.prepare.release.complete(Unit) }
        compose.waitUntil(8_000) { f.protocol.prepare.returned.isCompleted }
        compose.waitForIdle()
    }

    @Test fun checkingCancellationIsVisibleBeforeAcknowledgementAndBlocksCompetingControls() = exercise {
        beginCancellation(this)
        tag("busy-status").assertTextEquals("Checking cancellation…")
        assertBlockedControls()
        assertRetainedHistory(this)
        tag("busy-status").assertTextEquals("Checking cancellation…")
        compose.onNodeWithTag("cancel-turn").assertDoesNotExist()
        compose.runOnIdle { protocol.cancel.release.complete(Unit) }
        idle(this)
        assertRetainedHistory(this)
        tag("give-potion").assertIsEnabled()
        tag("play-send").assertIsEnabled()
        tag("mode-menu").assertIsEnabled()
        tag("saved-library").assertIsEnabled()
        tag("notice").assertTextContains("Cancellation checked.", substring = true)
        tag("give-potion")
        compose.onNodeWithTag("busy-status").assertDoesNotExist()
        compose.onNodeWithTag("recover-save").assertDoesNotExist()
    }

    @Test fun checkingCancellationRemainsVisibleUntilAcceptedSnapshotArrives() = exercise {
        beginCancellation(this)
        compose.runOnIdle { protocol.holdSnapshot = true; protocol.cancel.release.complete(Unit) }
        compose.waitUntil(8_000) { protocol.snapshot.entered.isCompleted }
        tag("busy-status").assertTextEquals("Checking cancellation…")
        assertBlockedControls()
        assertRetainedHistory(this)
        compose.runOnIdle { protocol.snapshot.release.complete(Unit) }
        idle(this)
        assertRetainedHistory(this)
        tag("give-potion").assertIsEnabled()
        compose.onNodeWithTag("busy-status").assertDoesNotExist()
    }

    private fun invalidAcknowledgement(change: (JSONObject) -> Unit) = exercise {
        beginCancellation(this)
        compose.runOnIdle { protocol.changeAck = change; protocol.cancel.release.complete(Unit) }
        idle(this)
        assertRetainedHistory(this)
        tag("notice").assertTextContains("Retry recovery", substring = true)
        tag("recover-save").assertIsEnabled()
        tag("play-send").assertIsNotEnabled()
        tag("give-potion").assertIsNotEnabled()
        tag("mode-menu").assertIsNotEnabled()
        tag("saved-library").assertIsNotEnabled()
        tag("reset-demo").assertIsNotEnabled()
        compose.onNodeWithTag("busy-status").assertDoesNotExist()
        compose.runOnIdle {
            assertTrue(model.state.value.recoveryRequired)
            val calls = protocol.calls.size
            // Retained callbacks must obey the same recovery boundary as disabled controls.
            model.reset(); model.resume(checkNotNull(model.state.value.selectedStory))
            assertEquals(calls, protocol.calls.size)
            assertTrue(model.state.value.recoveryRequired)
            assertFalse(model.state.value.busy)
            protocol.changeAck = {}
        }
        tag("recover-save").performClick()
        idle(this)
        assertRetainedHistory(this)
        tag("give-potion").assertIsEnabled()
        tag("play-send").assertIsEnabled()
        tag("saved-library").assertIsEnabled()
        tag("reset-demo").assertIsEnabled()
        tag("give-potion")
        compose.onNodeWithTag("recover-save").assertDoesNotExist()
        tag("notice").assertTextEquals("Saved progress recovered.")
        compose.runOnIdle {
            val cancels = protocol.calls.filter { it.getString("op") == "cancel" }
            assertEquals(2, cancels.size)
            assertEquals(cancels[0].toString(), cancels[1].toString())
            assertEquals(1, protocol.count("submit"))
            assertEquals(0, protocol.count("commit"))
            assertFalse(model.state.value.recoveryRequired)
        }
        releasePreparation(this)
        assertRetainedHistory(this)
    }

    @Test fun foreignAcknowledgementShowsRecoveryAndRecoveryClickUsesOriginalKey() =
        invalidAcknowledgement { it.put("turn", "foreign-turn") }

    @Test fun unfinishedAcknowledgementShowsRecoveryAndRecoveryClickUsesOriginalKey() =
        invalidAcknowledgement { it.put("phase", "ready") }

    @Test fun incompleteCommittedAcknowledgementShowsRecoveryAndRecoveryClickUsesOriginalKey() =
        invalidAcknowledgement { it.put("phase", "committed").remove("receipt") }

    @Test fun committedRaceShowsAcceptedHistoryAndNeverClaimsRollback() = exercise {
        beginCancellation(this)
        compose.runOnIdle { protocol.committed = true; protocol.cancel.release.complete(Unit) }
        idle(this)
        text("Accepted despite the cancellation race").assertIsDisplayed()
        text("Earlier accepted narration").assertIsDisplayed()
        tag("revision").assertTextEquals("Accepted revision · 8")
        tag("potion-owner").assertTextEquals("Healing potion · Not in your inventory")
        tag("notice").assertTextEquals("Cancellation checked. Showing the accepted saved history.")
        compose.runOnIdle {
            assertEquals(4, model.state.value.messages.size)
            assertEquals(8L, model.state.value.revision)
            assertFalse(model.state.value.recoveryRequired)
            assertEquals(0, protocol.count("commit"))
        }
        releasePreparation(this)
        text("Accepted despite the cancellation race").assertIsDisplayed()
        tag("revision").assertTextEquals("Accepted revision · 8")
        compose.runOnIdle { assertEquals(4, model.state.value.messages.size) }
    }

    @Test fun lateNoncooperativePreparationCannotReplaceCancelledVisibleHistory() = exercise {
        beginCancellation(this)
        compose.runOnIdle { protocol.cancel.release.complete(Unit) }
        idle(this)
        val before = compose.runOnIdle { model.state.value }
        releasePreparation(this)
        assertRetainedHistory(this)
        tag("notice").assertTextEquals("Cancellation checked. Showing the accepted saved history.")
        compose.runOnIdle {
            assertEquals(before, model.state.value)
            assertEquals(1, protocol.count("submit"))
            assertEquals(1, protocol.count("cancel"))
        }
    }

    @Test fun disposalWhileCheckingCannotPublishLateAcknowledgementOrPreparation() = exercise {
        beginCancellation(this)
        compose.runOnIdle { store.clear() }
        val disposed = compose.runOnIdle { model.state.value }
        val calls = compose.runOnIdle { protocol.calls.size }
        tag("give-potion")
        compose.onNodeWithTag("busy-status").assertDoesNotExist()
        compose.onNodeWithTag("cancel-turn").assertDoesNotExist()
        compose.runOnIdle { protocol.cancel.release.complete(Unit) }
        compose.waitUntil(8_000) { protocol.cancel.returned.isCompleted }
        releasePreparation(this)
        assertRetainedHistory(this)
        compose.runOnIdle {
            assertEquals(disposed, model.state.value)
            assertEquals(calls, protocol.calls.size)
            assertEquals(1, protocol.closed)
            model.recover(); model.submit(DemoAction.GIVE_POTION); model.reset(); model.cancel()
            assertEquals(calls, protocol.calls.size)
        }
    }
}

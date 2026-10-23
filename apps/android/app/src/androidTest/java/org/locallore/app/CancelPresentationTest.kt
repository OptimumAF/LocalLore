/* Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0 */
package org.locallore.app

import androidx.lifecycle.ViewModelStore
import androidx.test.ext.junit.runners.AndroidJUnit4
import kotlinx.coroutines.CompletableDeferred
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.NonCancellable
import kotlinx.coroutines.flow.first
import kotlinx.coroutines.runBlocking
import kotlinx.coroutines.withContext
import kotlinx.coroutines.withTimeout
import kotlinx.coroutines.yield
import org.json.JSONArray
import org.json.JSONObject
import org.junit.Assert.*
import org.junit.Test
import org.junit.runner.RunWith

/** Real ViewModel/gateway/Android JSON; synthetic transport, no Activity/native/storage/model. */
@RunWith(AndroidJUnit4::class)
class CancelPresentationTest {
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
        private fun scope() = JSONObject().put("story", "presentation-source").put("branch", "main")
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
                    .put("database_schema_version", 4).put("location", "/synthetic/presentation.sqlite3")
                    .put("stories", JSONArray().put(JSONObject().put("scope", scope()).put("title", "Source")
                        .put("revision", revision).put("drafts", 0))))
                "resume" -> ok(JSONObject().put("session", "presentation-session").put("scope", scope())
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
                "branches" -> ok(JSONObject().put("version", 2).put("story_id", "presentation-source")
                    .put("title", "Source").put("root_branch", "main").put("branches", JSONArray()
                        .put(JSONObject().put("scope", scope()).put("parent_branch", JSONObject.NULL)
                            .put("fork_revision", JSONObject.NULL).put("revision", revision)
                            .put("drafts", 0).put("retired", false))))
                "capabilities" -> ok(JSONObject().put("free_text", false))
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
        val log = DiagnosticLog()
        val gateway = DurableGateway(protocol, autoCreateIfEmpty = false)
        val model = ShellViewModel(gateway, log)
        val store = ViewModelStore().also { it.put("cancel-presentation", model) }
        fun cancelRecords(): List<JSONObject> {
            val records = JSONObject(log.snapshot().json).getJSONArray("records")
            return (0 until records.length()).map { records.getJSONObject(it) }
                .filter { it.getString("phase") == "CANCEL" }
        }
        suspend fun beginCancellation(): ShellState {
            val before = model.state.first { !it.busy }
            assertEquals(7L, before.revision)
            assertEquals(listOf("Earlier accepted dialogue", "Earlier accepted narration"), before.messages.map { it.text })
            model.submit(DemoAction.GIVE_POTION)
            protocol.prepare.entered.await()
            assertTrue(model.state.value.preparingResponse)
            model.cancel()
            protocol.cancel.entered.await()
            assertTrue(model.state.value.busy)
            assertFalse(model.state.value.preparingResponse)
            return before
        }
        suspend fun idle() = model.state.first { !it.busy }
        suspend fun releaseLatePreparation() {
            protocol.prepare.release.complete(Unit)
            protocol.prepare.returned.await()
            repeat(3) { yield() }
        }
        suspend fun dispose() {
            store.clear()
            protocol.prepare.release.complete(Unit)
            protocol.cancel.release.complete(Unit)
            protocol.snapshot.release.complete(Unit)
            repeat(3) { yield() }
        }
    }

    private fun exercise(block: suspend Fixture.() -> Unit): Unit = runBlocking {
        withTimeout(8_000) {
            withContext(Dispatchers.Main) {
                val fixture = Fixture()
                try { fixture.block() }
                finally { withContext(NonCancellable) { fixture.dispose() } }
            }
        }
    }

    @Test fun cancellationDoesNotCompleteBeforeAcknowledgement() = exercise {
        val before = beginCancellation()
        assertEquals(before.messages, model.state.value.messages)
        assertTrue("Unacknowledged cancellation must have no completed diagnostic", cancelRecords().isEmpty())
        protocol.cancel.release.complete(Unit)
        idle()
        assertEquals(listOf("COMPLETED"), cancelRecords().map { it.getString("outcome") })
    }

    @Test fun cancellationDoesNotCompleteBeforeAcceptedSnapshotReconciliation() = exercise {
        beginCancellation()
        protocol.holdSnapshot = true
        protocol.cancel.release.complete(Unit)
        protocol.snapshot.entered.await()
        assertTrue(model.state.value.busy)
        assertTrue("Terminal reply alone has not reconciled accepted history", cancelRecords().isEmpty())
        protocol.snapshot.release.complete(Unit)
        idle()
        assertEquals(listOf("COMPLETED"), cancelRecords().map { it.getString("outcome") })
    }

    @Test fun invalidAcknowledgementsRetainHistoryBlockSubmissionAndRecoverOriginalKey() = exercise {
        val changes: List<(JSONObject) -> Unit> = listOf(
            { it.put("turn", "foreign-turn") },
            { it.put("phase", "ready") },
            { it.put("phase", "committed").remove("receipt") },
        )
        // A fresh owner per hostile reply, preserving the same production constructor/API.
        for (change in changes) {
            val f = Fixture()
            try {
                val before = f.beginCancellation()
                f.protocol.changeAck = change
                f.protocol.cancel.release.complete(Unit)
                val failed = f.idle()
                assertTrue(failed.recoveryRequired)
                assertEquals(before.revision, failed.revision)
                assertEquals(before.messages, failed.messages)
                assertTrue(failed.notice.orEmpty().contains("recovery", ignoreCase = true))
                val calls = f.protocol.calls.size
                f.model.submit(DemoAction.GIVE_POTION)
                assertEquals(calls, f.protocol.calls.size)
                f.protocol.changeAck = {}
                f.model.recover()
                val recovered = f.idle()
                assertFalse(recovered.recoveryRequired)
                assertEquals(before.messages, recovered.messages)
                val cancels = f.protocol.calls.filter { it.getString("op") == "cancel" }
                assertEquals(2, cancels.size)
                assertEquals(cancels[0].toString(), cancels[1].toString())
                assertEquals(1, f.protocol.count("submit"))
                assertEquals(0, f.protocol.count("commit"))
                assertEquals(listOf("UNKNOWN"), f.cancelRecords().map { it.getString("outcome") })
            } finally { f.dispose() }
        }
    }

    @Test fun explicitTransportFailureRecordsUnknownWithoutRawPayload() = exercise {
        val before = beginCancellation()
        protocol.failure = "Full"
        protocol.cancel.release.complete(Unit)
        val failed = idle()
        assertTrue(failed.recoveryRequired)
        assertEquals(before.messages, failed.messages)
        assertTrue(failed.notice.orEmpty().contains("storage is full", ignoreCase = true))
        assertEquals(listOf("UNKNOWN"), cancelRecords().map { it.getString("outcome") })
        assertEquals("UNKNOWN", cancelRecords().single().getString("error"))
        assertFalse(log.snapshot().json.contains("presentation-source"))
        assertFalse(log.snapshot().json.contains("Earlier accepted"))
    }

    @Test fun committedCancellationRaceDisplaysAcceptedHistoryWithoutStoppedClaim() = exercise {
        beginCancellation()
        protocol.committed = true
        protocol.cancel.release.complete(Unit)
        val saved = idle()
        assertEquals(8L, saved.revision)
        assertEquals("Not in your inventory", saved.potionOwner)
        assertEquals("Accepted despite the cancellation race", saved.messages.last().text)
        assertEquals(4, saved.messages.size)
        assertFalse(saved.recoveryRequired)
        assertEquals(0, protocol.count("commit"))
        val notice = saved.notice.orEmpty().lowercase(java.util.Locale.ROOT)
        assertFalse("A committed response was not stopped", notice.contains("stopped"))
        assertFalse("A committed response was not cancelled", notice.contains("response cancelled"))
        assertEquals(listOf("COMPLETED"), cancelRecords().map { it.getString("outcome") })
    }

    @Test fun lateNoncooperativePreparationCannotPublishOrCommitAfterCancellation() = exercise {
        val before = beginCancellation()
        protocol.cancel.release.complete(Unit)
        val cancelled = idle()
        assertEquals(before.messages, cancelled.messages)
        releaseLatePreparation()
        assertEquals(cancelled, model.state.value)
        assertEquals(0, protocol.count("commit"))
        assertEquals(1, protocol.count("submit"))
        assertEquals(1, protocol.count("cancel"))
        assertEquals(listOf("COMPLETED"), cancelRecords().map { it.getString("outcome") })
    }

    @Test fun disposalDuringDelayedAcknowledgementCannotPublishOrRecordCompletion() = exercise {
        beginCancellation()
        store.clear()
        val disposed = model.state.value
        val calls = protocol.calls.size
        protocol.cancel.release.complete(Unit)
        protocol.cancel.returned.await()
        releaseLatePreparation()
        repeat(3) { yield() }
        assertEquals(disposed, model.state.value)
        assertEquals(calls, protocol.calls.size)
        assertEquals(1, protocol.closed)
        assertTrue("Disposed cancellation never completed reconciliation", cancelRecords().isEmpty())
        model.recover(); model.submit(DemoAction.GIVE_POTION); model.reset(); model.cancel()
        assertEquals(calls, protocol.calls.size)
    }
}

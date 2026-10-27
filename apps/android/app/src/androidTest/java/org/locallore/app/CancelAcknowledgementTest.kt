/* Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0 */
package org.locallore.app

import androidx.test.ext.junit.runners.AndroidJUnit4
import kotlinx.coroutines.runBlocking
import org.json.JSONArray
import org.json.JSONObject
import org.junit.Assert.*
import org.junit.Test
import org.junit.runner.RunWith

/** Actual gateway/Android JSON, synthetic transport only. No Activity, JNI, SQLite or save access. */
@RunWith(AndroidJUnit4::class)
class CancelAcknowledgementTest {
    private enum class Entry { CANCEL, CREATE, RESUME, CANCELLED_RECOVERY }
    private data class BadAck(val label: String, val change: (JSONObject) -> Unit)

    private fun invalidAcknowledgements(): List<BadAck> = listOf(
        BadAck("foreign turn") { it.put("turn", "foreign-turn") },
        BadAck("foreign story") { it.getJSONObject("scope").put("story", "foreign-story") },
        BadAck("foreign branch") { it.getJSONObject("scope").put("branch", "foreign-branch") },
        BadAck("wrong expected revision") { it.put("expected_revision", 8) },
        BadAck("missing turn") { it.remove("turn") },
        BadAck("missing scope") { it.remove("scope") },
        BadAck("missing story") { it.getJSONObject("scope").remove("story") },
        BadAck("missing branch") { it.getJSONObject("scope").remove("branch") },
        BadAck("missing expected revision") { it.remove("expected_revision") },
        BadAck("missing phase") { it.remove("phase") },
        BadAck("queued is not cancellation acknowledgement") { it.put("phase", "queued") },
        BadAck("running is not cancellation acknowledgement") { it.put("phase", "running") },
        BadAck("ready is not cancellation acknowledgement") { it.put("phase", "ready") },
        BadAck("unknown phase") { it.put("phase", "future-phase") },
    )

    private class Protocol : WorkspaceTransport {
        val source = SavedStory("cancel-source", "main", "Source", 7)
        val retained = SavedStory("retained-save", "main", "Retained", 0)
        val calls = mutableListOf<JSONObject>()
        val stories = linkedMapOf(source.story to source, retained.story to retained)
        private val sessions = mutableMapOf<String, String>()
        private var nextSession = 0
        var originalRequest: JSONObject? = null
            private set
        var ackPhase = "cancelled"
        var changeAck: (JSONObject) -> Unit = {}
        var cancelFailure: String? = null
        var closeReportsClosed = false
        var commitOnCancel = false
        private var committedReceipt: JSONObject? = null
        private var draft = false

        fun count(op: String) = calls.count { it.getString("op") == op }
        private fun scope(story: String) = JSONObject().put("story", story).put("branch", "main")
        private fun ok(data: JSONObject) = JSONObject().put("version", 1).put("status", "ok").put("data", data)
        private fun rejected(category: String) = JSONObject().put("version", 1)
            .put("status", "rejected").put("error", category)
        private fun receipt() = JSONObject().put("request", copy(checkNotNull(originalRequest)))
            .put("narration", "Authoritative synthetic receipt")
        private fun turn(phase: String): JSONObject {
            val request = checkNotNull(originalRequest)
            return JSONObject().put("turn", request.getString("turn"))
                .put("scope", copy(request.getJSONObject("scope")))
                .put("expected_revision", request.getLong("expected_revision"))
                .put("phase", phase).put("error", JSONObject.NULL)
                .put("receipt", if (phase == "committed") receipt() else JSONObject.NULL)
        }

        override suspend fun exchange(command: JSONObject): JSONObject {
            calls += copy(command)
            val op = command.getString("op")
            if (op == "workspace") return ok(JSONObject().put("persistent", true).put("schema_version", 1)
                .put("database_schema_version", 5).put("location", "/synthetic/cancel-ack.sqlite3")
                .put("stories", JSONArray().also { rows -> stories.values.forEach { story ->
                    rows.put(JSONObject().put("scope", scope(story.story)).put("title", story.title)
                        .put("revision", story.revision).put("drafts", if (draft && story.story == source.story) 1 else 0))
                } }))
            if (op == "capabilities") return ok(JSONObject().put("free_text", false))
            if (op == "branches") {
                val story = stories.getValue(command.getString("story"))
                return ok(JSONObject().put("version", 2).put("story_id", story.story).put("title", story.title)
                    .put("root_branch", "main").put("branches", JSONArray().put(JSONObject()
                        .put("scope", scope(story.story)).put("parent_branch", JSONObject.NULL)
                        .put("fork_revision", JSONObject.NULL).put("revision", story.revision)
                        .put("drafts", if (draft && story.story == source.story) 1 else 0).put("retired", false))))
            }
            if (op == "resume" || op == "create") {
                val story = if (op == "create") SavedStory("created-save", "main", "Created", 0)
                    .also { stories[it.story] = it }
                else stories.getValue(command.getJSONObject("scope").getString("story"))
                val session = "session-${++nextSession}"
                sessions[session] = story.story
                return ok(JSONObject().put("session", session).put("scope", scope(story.story))
                    .put("revision", story.revision))
            }
            val session = command.getString("session")
            val storyId = sessions[session] ?: return rejected("Closed")
            val story = stories.getValue(storyId)
            return when (op) {
                "open" -> ok(JSONObject().put("scope", scope(storyId)).put("revision", story.revision))
                "play_snapshot" -> {
                    assertEquals(story.revision, command.getLong("expected_revision"))
                    val receipts = JSONArray().also { rows ->
                        if (storyId == source.story) committedReceipt?.let { rows.put(copy(it)) }
                    }
                    ok(JSONObject().put("scope", scope(storyId)).put("revision", story.revision)
                        .put("rules", "fantasy_v1").put("inventory", JSONObject().put("potion", JSONObject()))
                        .put("player", JSONObject().put("scope", scope(storyId)).put("revision", story.revision)
                            .put("observer", "player")).put("receipts", receipts))
                }
                "submit" -> {
                    check(originalRequest == null)
                    originalRequest = copy(command.getJSONObject("request"))
                    draft = true
                    ok(turn("queued"))
                }
                "prepare" -> ok(turn("ready"))
                "cancel" -> {
                    cancelFailure?.let { return rejected(it) }
                    if (commitOnCancel && committedReceipt == null) {
                        committedReceipt = receipt()
                        stories[source.story] = source.copy(revision = 8)
                    }
                    if (ackPhase in setOf("cancelled", "failed", "stale", "committed")) draft = false
                    ok(turn(ackPhase).also(changeAck))
                }
                "close" -> {
                    sessions.remove(session)
                    if (closeReportsClosed) rejected("Closed") else ok(JSONObject())
                }
                else -> error("Unexpected synthetic protocol operation: $op")
            }
        }

        override fun close() { sessions.clear() }
        companion object { fun copy(value: JSONObject) = JSONObject(value.toString()) }
    }

    private suspend fun prepared(protocol: Protocol, gateway: DurableGateway): DemoResult.Prepared {
        assertEquals(protocol.source, gateway.initialize().selected)
        val response = gateway.respond(DemoAction.GIVE_POTION, 7, DemoMode.ACCEPTED)
        assertTrue(response is DemoResult.Prepared)
        assertEquals(1, protocol.count("submit"))
        assertEquals(1, protocol.count("prepare"))
        assertEquals(0, protocol.count("commit"))
        return response as DemoResult.Prepared
    }

    private suspend fun enter(entry: Entry, gateway: DurableGateway, protocol: Protocol): SavedSnapshot = when (entry) {
        Entry.CANCEL -> gateway.cancelSaved()
        Entry.CREATE -> gateway.createSaved()
        Entry.RESUME -> gateway.resumeSaved(protocol.retained)
        Entry.CANCELLED_RECOVERY -> gateway.recoverSaved()
    }

    private fun assertSameJson(left: Any?, right: Any?) {
        when {
            left is JSONObject && right is JSONObject -> {
                val keys = left.keys().asSequence().toSet()
                assertEquals(keys, right.keys().asSequence().toSet())
                keys.forEach { assertSameJson(left.get(it), right.get(it)) }
            }
            left is JSONArray && right is JSONArray -> {
                assertEquals(left.length(), right.length())
                for (index in 0 until left.length()) assertSameJson(left.get(index), right.get(index))
            }
            left is Number && right is Number -> assertEquals(left.toString(), right.toString())
            else -> assertEquals(left, right)
        }
    }

    private suspend fun rejectsAndRetains(entry: Entry, bad: BadAck) {
        val protocol = Protocol()
        val gateway = DurableGateway(protocol, autoCreateIfEmpty = false)
        try {
            val oldPrepared = prepared(protocol, gateway)
            val original = Protocol.copy(checkNotNull(protocol.originalRequest))
            if (entry == Entry.CANCELLED_RECOVERY) gateway.cancel()
            protocol.changeAck = bad.change
            val start = protocol.calls.size
            var rejected: Exception? = null
            try { enter(entry, gateway, protocol) } catch (failure: Exception) { rejected = failure }
            assertNotNull("Malformed acknowledgement was accepted: $entry / ${bad.label}", rejected)
            assertEquals("No snapshot, replacement or close may follow the bad acknowledgement",
                listOf("cancel"), protocol.calls.drop(start).map { it.getString("op") })
            val firstCancel = protocol.calls.last()
            assertEquals(original.getString("turn"), firstCancel.getString("turn"))
            assertSameJson(original.getJSONObject("scope"), firstCancel.getJSONObject("scope"))
            // Even the old retained Prepared handle cannot commit after cancellation became uncertain.
            val beforeOldCommit = protocol.calls.size
            assertEquals(DemoResult.Rejected("Cancelled"), gateway.commitAsync(oldPrepared))
            assertEquals(beforeOldCommit, protocol.calls.size)

            protocol.changeAck = {}
            protocol.ackPhase = "cancelled"
            val retryStart = protocol.calls.size
            val recovered = gateway.recoverSaved()
            val retry = protocol.calls[retryStart]
            assertEquals("cancel", retry.getString("op"))
            assertSameJson(firstCancel, retry)
            assertSameJson(original, checkNotNull(protocol.originalRequest))
            assertEquals(protocol.source, recovered.selected)
            assertEquals(listOf("cancel", "open", "play_snapshot", "workspace", "branches", "capabilities"),
                protocol.calls.drop(retryStart).map { it.getString("op") })
            assertEquals(1, protocol.count("submit"))
            assertEquals(1, protocol.count("prepare"))
            assertEquals(0, protocol.count("commit"))
            assertEquals(0, protocol.count("free_text"))
            assertEquals(0, protocol.count("create"))
            assertEquals(1, protocol.count("resume"))
            assertEquals(0, protocol.count("close"))
        } finally { gateway.close() }
    }

    @Test fun cancelSavedRejectsForeignIncompleteAndNonterminalAcknowledgements(): Unit = runBlocking {
        invalidAcknowledgements().forEach { rejectsAndRetains(Entry.CANCEL, it) }
    }

    @Test fun createReleaseRejectsForeignIncompleteAndNonterminalAcknowledgements(): Unit = runBlocking {
        invalidAcknowledgements().forEach { rejectsAndRetains(Entry.CREATE, it) }
    }

    @Test fun resumeReleaseRejectsForeignIncompleteAndNonterminalAcknowledgements(): Unit = runBlocking {
        invalidAcknowledgements().forEach { rejectsAndRetains(Entry.RESUME, it) }
    }

    @Test fun cancelledRecoveryRejectsForeignIncompleteAndNonterminalAcknowledgements(): Unit = runBlocking {
        invalidAcknowledgements().forEach { rejectsAndRetains(Entry.CANCELLED_RECOVERY, it) }
    }

    @Test fun malformedCommittedReceiptsCannotClearTheCancelledKey(): Unit = runBlocking {
        val invalid = listOf(
            BadAck("missing committed receipt") { it.put("phase", "committed").remove("receipt") },
            BadAck("foreign committed request") {
                it.put("phase", "committed").put("receipt", JSONObject().put("request", JSONObject()
                    .put("scope", JSONObject().put("story", "foreign").put("branch", "main")))
                    .put("narration", "Untrusted synthetic narration"))
            },
        )
        Entry.values().forEach { entry -> invalid.forEach { rejectsAndRetains(entry, it) } }
    }

    @Test fun matchingCancelledFailedAndStaleAcknowledgementsCompleteAcrossAllPaths(): Unit = runBlocking {
        for (entry in Entry.values()) for (phase in listOf("cancelled", "failed", "stale")) {
            val protocol = Protocol().also { it.ackPhase = phase }
            val gateway = DurableGateway(protocol, autoCreateIfEmpty = false)
            try {
                prepared(protocol, gateway)
                if (entry == Entry.CANCELLED_RECOVERY) gateway.cancel()
                val saved = enter(entry, gateway, protocol)
                assertEquals(if (entry == Entry.RESUME) protocol.retained.story else
                    if (entry == Entry.CREATE) "created-save" else protocol.source.story, saved.selected?.story)
                val cancelCount = protocol.count("cancel")
                gateway.recoverSaved()
                assertEquals(cancelCount, protocol.count("cancel"))
                assertEquals(1, protocol.count("submit")); assertEquals(1, protocol.count("prepare"))
                assertEquals(0, protocol.count("commit")); assertEquals(0, protocol.count("free_text"))
            } finally { gateway.close() }
        }
    }

    @Test fun matchingCommittedRaceUsesOriginalReceiptWithoutAnotherCommit(): Unit = runBlocking {
        for (entry in Entry.values()) {
            val protocol = Protocol().also { it.ackPhase = "committed"; it.commitOnCancel = true }
            val gateway = DurableGateway(protocol, autoCreateIfEmpty = false)
            try {
                prepared(protocol, gateway)
                if (entry == Entry.CANCELLED_RECOVERY) gateway.cancel()
                val saved = enter(entry, gateway, protocol)
                if (entry in setOf(Entry.CANCEL, Entry.CANCELLED_RECOVERY)) {
                    assertEquals(8L, saved.revision)
                    assertEquals("Authoritative synthetic receipt", saved.messages.last().text)
                }
                assertEquals(8L, protocol.stories.getValue(protocol.source.story).revision)
                val cancels = protocol.count("cancel")
                gateway.recoverSaved()
                assertEquals(cancels, protocol.count("cancel"))
                assertEquals(1, protocol.count("submit")); assertEquals(1, protocol.count("prepare"))
                assertEquals(0, protocol.count("commit"))
            } finally { gateway.close() }
        }
    }

    @Test fun explicitUnknownTurnDisposesCancelledWorkWithoutResubmit(): Unit = runBlocking {
        for (entry in Entry.values()) {
            val protocol = Protocol().also { it.cancelFailure = "UnknownTurn" }
            val gateway = DurableGateway(protocol, autoCreateIfEmpty = false)
            try {
                prepared(protocol, gateway)
                if (entry == Entry.CANCELLED_RECOVERY) gateway.cancel()
                enter(entry, gateway, protocol)
                assertEquals(1, protocol.count("cancel"))
                gateway.recoverSaved()
                assertEquals(1, protocol.count("cancel"))
                assertEquals(1, protocol.count("submit")); assertEquals(1, protocol.count("prepare"))
                assertEquals(0, protocol.count("commit")); assertEquals(0, protocol.count("free_text"))
            } finally { gateway.close() }
        }
    }

    @Test fun closedIsReleaseDispositionButNotGenericCancellationSuccess(): Unit = runBlocking {
        for (entry in Entry.values()) {
            val protocol = Protocol().also { it.cancelFailure = "Closed"; it.closeReportsClosed = true }
            val gateway = DurableGateway(protocol, autoCreateIfEmpty = false)
            try {
                prepared(protocol, gateway)
                if (entry == Entry.CANCELLED_RECOVERY) gateway.cancel()
                if (entry in setOf(Entry.CREATE, Entry.RESUME)) {
                    enter(entry, gateway, protocol)
                    assertEquals(1, protocol.count("close"))
                } else {
                    var failure: WorkspaceFailure? = null
                    try { enter(entry, gateway, protocol) } catch (caught: WorkspaceFailure) { failure = caught }
                    assertEquals("Closed", failure?.category)
                    protocol.cancelFailure = null
                    gateway.recoverSaved()
                    assertEquals(2, protocol.count("cancel"))
                    assertEquals(0, protocol.count("close"))
                }
                assertEquals(1, protocol.count("submit")); assertEquals(1, protocol.count("prepare"))
                assertEquals(0, protocol.count("commit"))
            } finally { gateway.close() }
        }
    }
}

/* Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0 */
package org.locallore.app

import androidx.test.ext.junit.runners.AndroidJUnit4
import kotlinx.coroutines.runBlocking
import org.json.JSONArray
import org.json.JSONObject
import org.junit.Assert.*
import org.junit.Test
import org.junit.runner.RunWith

/** Frozen source: actual Gateway + Android JSONObject, synthetic protocol only.
 * UNCOMPILED/UNRUN at freeze. No NativeWorkspace, JNI, SQLite or model is used.
 */
@RunWith(AndroidJUnit4::class)
class M08Schema5AdmissionTest {
    private class Protocol(var databaseSchema: Int = 5, val empty: Boolean = false) : WorkspaceTransport {
        var workspaceProtocol = 1
        var badEnvelopeFor: String? = null
        var head = 0L
        var original: JSONObject? = null
        var committed = false
        var closed = false
        val commands = mutableListOf<JSONObject>()
        fun operations() = commands.map { it.getString("op") }
        private fun scope() = JSONObject().put("story", "schema-five-story").put("branch", "main")
        private fun ok(op: String, data: JSONObject) = JSONObject()
            .put("version", if (badEnvelopeFor == op) 2 else 1).put("status", "ok").put("data", data)
        private fun turn(phase: String): JSONObject = JSONObject().put("scope", scope())
            .put("turn", checkNotNull(original).getString("turn"))
            .put("expected_revision", checkNotNull(original).getLong("expected_revision"))
            .put("phase", phase).also {
                if (phase == "committed") it.put("receipt", JSONObject()
                    .put("request", JSONObject(checkNotNull(original).toString()))
                    .put("narration", "Synthetic accepted response."))
            }
        override suspend fun exchange(command: JSONObject): JSONObject {
            commands += JSONObject(command.toString())
            val op = command.getString("op")
            val data = when (op) {
                "workspace" -> JSONObject().put("persistent", true).put("schema_version", workspaceProtocol)
                    .put("database_schema_version", databaseSchema).put("location", "/synthetic/schema-five.sqlite3")
                    .put("stories", JSONArray().also {
                        if (!empty) it.put(JSONObject().put("scope", scope()).put("title", "Synthetic schema five")
                            .put("revision", head).put("drafts", 0).put("retired", false))
                    })
                "resume" -> {
                    assertEquals(scope().toString(), command.getJSONObject("scope").toString())
                    JSONObject().put("session", "synthetic-five-session").put("scope", scope()).put("revision", head)
                }
                "open" -> JSONObject().put("scope", scope()).put("revision", head)
                "play_snapshot" -> {
                    assertEquals(head, command.getLong("expected_revision"))
                    JSONObject().put("scope", scope()).put("revision", head).put("rules", "fantasy_v1")
                        .put("inventory", JSONObject().put("potion", JSONObject()))
                        .put("player", JSONObject().put("scope", scope()).put("revision", head).put("observer", "player"))
                        .put("receipts", JSONArray().also {
                            if (committed) it.put(turn("committed").getJSONObject("receipt"))
                        })
                }
                "branches" -> JSONObject().put("version", 2).put("story_id", "schema-five-story")
                    .put("title", "Synthetic schema five").put("root_branch", "main")
                    .put("branches", JSONArray().put(JSONObject().put("scope", scope())
                        .put("parent_branch", JSONObject.NULL).put("fork_revision", JSONObject.NULL)
                        .put("revision", head).put("drafts", 0).put("retired", false)))
                "capabilities" -> JSONObject().put("free_text", false)
                "submit" -> {
                    check(original == null) { "Unexpected replacement response key" }
                    original = JSONObject(command.getJSONObject("request").toString())
                    turn("queued")
                }
                "prepare", "turn_status" -> {
                    assertEquals(checkNotNull(original).getString("turn"), command.getString("turn"))
                    turn(if (committed) "committed" else "ready")
                }
                "commit" -> {
                    assertEquals(checkNotNull(original).getString("turn"), command.getString("turn"))
                    assertFalse("Synthetic protocol must not receive duplicate commit", committed)
                    committed = true
                    head++
                    turn("committed")
                }
                "close" -> JSONObject()
                else -> error("Unexpected synthetic protocol operation: $op")
            }
            return ok(op, data)
        }
        override fun close() { closed = true }
    }
    private suspend fun refuses(operation: suspend () -> Unit) {
        var failure: Exception? = null
        try { operation() } catch (caught: Exception) { failure = caught }
        assertNotNull("Incompatible live metadata was published", failure)
    }
    private fun assertNoWrites(protocol: Protocol) {
        assertFalse(protocol.operations().any { it in setOf("create", "submit", "prepare", "commit", "free_text") })
    }

    @Test fun schemaFiveKeepsProtocolOneAcrossInitializeAndRefresh(): Unit = runBlocking {
        val protocol = Protocol()
        val gateway = DurableGateway(protocol, autoCreateIfEmpty = false)
        try {
            val initial = gateway.initialize()
            assertEquals(1, initial.schemaVersion)
            assertEquals(5, initial.databaseSchemaVersion)
            assertEquals(SavedStory("schema-five-story", "main", "Synthetic schema five", 0), initial.selected)
            assertEquals(0L, initial.revision)
            assertEquals("You", initial.potionOwner)
            assertEquals(TextProvider.UNAVAILABLE, initial.textProvider)
            assertTrue(initial.messages.isEmpty())
            assertEquals(listOf("workspace", "resume", "open", "play_snapshot", "workspace", "branches", "capabilities"),
                protocol.operations())
            assertEquals(initial, gateway.snapshot())
            assertNoWrites(protocol)
        } finally { gateway.close() }
        assertTrue(protocol.closed)
    }

    @Test fun emptySchemaFiveLibraryNeverBootstrapsDuringAdmission(): Unit = runBlocking {
        val protocol = Protocol(empty = true)
        val gateway = DurableGateway(protocol, autoCreateIfEmpty = false)
        try {
            val snapshot = gateway.initialize()
            assertEquals(1, snapshot.schemaVersion)
            assertEquals(5, snapshot.databaseSchemaVersion)
            assertNull(snapshot.selected)
            assertTrue(snapshot.stories.isEmpty())
            assertTrue(snapshot.messages.isEmpty())
            assertEquals(listOf("workspace"), protocol.operations())
        } finally { gateway.close() }
    }

    @Test fun futureSchemaSixRefusesBeforeResumeAndGameplay(): Unit = runBlocking {
        val protocol = Protocol(databaseSchema = 6)
        val gateway = DurableGateway(protocol, autoCreateIfEmpty = false)
        try {
            refuses { gateway.initialize() }
            assertEquals(listOf("workspace"), protocol.operations())
            assertNoWrites(protocol)
        } finally { gateway.close() }
    }

    @Test fun incompatibleEnvelopeOrWorkspaceProtocolRefusesBeforeResume(): Unit = runBlocking {
        for (badEnvelope in listOf(false, true)) {
            val protocol = Protocol().also {
                if (badEnvelope) it.badEnvelopeFor = "workspace" else it.workspaceProtocol = 2
            }
            val gateway = DurableGateway(protocol, autoCreateIfEmpty = false)
            try {
                refuses { gateway.initialize() }
                assertEquals(listOf("workspace"), protocol.operations())
                assertNoWrites(protocol)
            } finally { gateway.close() }
        }
    }

    @Test fun incompatibleRefreshAndStatusNeverReplaceThePendingRecoveryKey(): Unit = runBlocking {
        val protocol = Protocol()
        val gateway = DurableGateway(protocol, autoCreateIfEmpty = false)
        try {
            gateway.initialize()
            assertTrue(gateway.respond(DemoAction.GIVE_POTION, 0, DemoMode.ACCEPTED) is DemoResult.Prepared)
            val original = checkNotNull(protocol.original).toString()
            val key = checkNotNull(protocol.original).getString("turn")
            assertTrue(key.isNotBlank())
            protocol.databaseSchema = 6
            refuses { gateway.snapshot() }
            assertFalse(protocol.committed)
            assertEquals(original, checkNotNull(protocol.original).toString())
            protocol.databaseSchema = 5
            protocol.badEnvelopeFor = "turn_status"
            refuses { gateway.recoverSaved() }
            assertFalse(protocol.committed)
            assertEquals(original, checkNotNull(protocol.original).toString())
            protocol.badEnvelopeFor = null
            val recovered = gateway.recoverSaved()
            assertEquals(1L, recovered.revision)
            assertEquals(5, recovered.databaseSchemaVersion)
            assertEquals(listOf("Synthetic accepted response."), recovered.messages.filterNot { it.isPlayer }.map { it.text })
            assertEquals(1, protocol.operations().count { it == "submit" })
            assertEquals(1, protocol.operations().count { it == "prepare" })
            assertEquals(1, protocol.operations().count { it == "commit" })
            assertEquals(2, protocol.operations().count { it == "turn_status" })
            val submitted = protocol.commands.single { it.getString("op") == "submit" }
            assertEquals(original, submitted.getJSONObject("request").toString())
            for (command in protocol.commands.filter { it.getString("op") in setOf("prepare", "turn_status", "commit") }) {
                assertEquals(key, command.getString("turn"))
                assertEquals("synthetic-five-session", command.getString("session"))
                assertEquals("schema-five-story", command.getJSONObject("scope").getString("story"))
                assertEquals("main", command.getJSONObject("scope").getString("branch"))
            }
        } finally { gateway.close() }
    }
}

/* Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0 */
package org.locallore.app

import androidx.test.ext.junit.runners.AndroidJUnit4
import kotlinx.coroutines.runBlocking
import org.json.JSONArray
import org.json.JSONObject
import org.junit.Assert.*
import org.junit.Test
import org.junit.runner.RunWith

/** Protocol regressions on Android's JSONObject. This fixture does not claim SQLite deletion. */
@RunWith(AndroidJUnit4::class)
class DurableDeletionRecoveryTest {
    private val first = SavedStory("deleted-a", "main", "A", 0)
    private val retained = SavedStory("retained-b", "main", "B", 0)

    private class Protocol(initial: List<SavedStory>) : WorkspaceTransport {
        val stories = initial.toMutableList()
        val calls = mutableListOf<JSONObject>()
        val sessions = mutableMapOf<String, SavedStory>()
        var closeFailure: String? = null
        var workspaceFailure: String? = null
        private var next = 0
        private var submitted: JSONObject? = null
        fun count(op: String) = calls.count { it.getString("op") == op }
        fun delete(story: SavedStory) {
            stories.removeAll { it.story == story.story }
            sessions.entries.removeAll { it.value.story == story.story }
        }
        private fun scope(story: SavedStory) = JSONObject().put("story", story.story).put("branch", story.branch)
        private fun ok(data: JSONObject) = JSONObject().put("version", 1).put("status", "ok").put("data", data)
        private fun rejected(error: String) = JSONObject().put("version", 1).put("status", "rejected").put("error", error)
        override suspend fun exchange(command: JSONObject): JSONObject {
            calls += JSONObject(command.toString())
            val op = command.getString("op")
            if (op == "capabilities") return ok(JSONObject().put("free_text", false))
            if (op == "workspace") {
                workspaceFailure?.let { workspaceFailure = null; return rejected(it) }
                return ok(JSONObject().put("persistent", true).put("schema_version", 1)
                    .put("database_schema_version", 5).put("location", "/synthetic/stories.sqlite3")
                    .put("stories", JSONArray().also { rows -> stories.forEach { story ->
                        rows.put(JSONObject().put("scope", scope(story)).put("title", story.title)
                            .put("revision", story.revision).put("drafts", 0))
                    } }))
            }
            if (op == "branches") {
                val story = stories.singleOrNull { it.story == command.getString("story") } ?: return rejected("NotFound")
                return ok(JSONObject().put("version", 2).put("story_id", story.story).put("title", story.title)
                    .put("root_branch", story.branch).put("branches", JSONArray().put(JSONObject()
                        .put("scope", scope(story)).put("parent_branch", JSONObject.NULL)
                        .put("fork_revision", JSONObject.NULL).put("revision", story.revision).put("drafts", 0).put("retired", false))))
            }
            if (op == "create" || op == "resume") {
                val story = if (op == "create") SavedStory("created-${next + 1}", "main", "Created", 0).also { stories += it }
                    else stories.single { it.story == command.getJSONObject("scope").getString("story") }
                val id = "session-${++next}"; sessions[id] = story
                return ok(JSONObject().put("session", id).put("scope", scope(story)).put("revision", story.revision))
            }
            if (op == "close") closeFailure?.let { closeFailure = null; return rejected(it) }
            val id = command.getString("session")
            val story = sessions[id] ?: return rejected("Closed")
            return when (op) {
                "close" -> { sessions.remove(id); ok(JSONObject()) }
                "open" -> ok(JSONObject().put("scope", scope(story)).put("revision", story.revision))
                "play_snapshot" -> ok(JSONObject().put("scope", scope(story)).put("revision", story.revision)
                    .put("rules", "fantasy_v1").put("inventory", JSONObject().put("potion", JSONObject()))
                    .put("player", JSONObject().put("scope", scope(story)).put("revision", story.revision).put("observer", "player"))
                    .put("receipts", JSONArray()))
                "submit" -> { submitted = command.getJSONObject("request"); ok(turn("queued")) }
                "prepare" -> ok(turn("ready"))
                "cancel" -> ok(turn("cancelled"))
                else -> error("Unexpected synthetic protocol operation")
            }
        }
        private fun turn(phase: String): JSONObject {
            val request = checkNotNull(submitted)
            return JSONObject().put("turn", request.getString("turn")).put("scope", request.getJSONObject("scope"))
                .put("expected_revision", request.getLong("expected_revision")).put("phase", phase)
        }
        override fun close() { sessions.clear() }
    }
    private suspend fun failure(category: String, block: suspend () -> Unit) {
        try { block(); fail("Expected fixed workspace failure") }
        catch (error: WorkspaceFailure) { assertEquals(category, error.category) }
    }
    private fun assertEmpty(saved: SavedSnapshot) {
        assertNull(saved.selected); assertTrue(saved.stories.isEmpty()); assertTrue(saved.messages.isEmpty())
        assertEquals(0L, saved.revision); assertEquals(0, saved.uncommittedDrafts)
        assertEquals(1, saved.schemaVersion); assertEquals(5, saved.databaseSchemaVersion)
        assertEquals("/synthetic/stories.sqlite3", saved.location)
    }

    @Test fun emptyProductInitializationAndSnapshotsNeverCreateImplicitStory() = runBlocking {
        val protocol = Protocol(emptyList()); val gateway = DurableGateway(protocol, autoCreateIfEmpty = false)
        try {
            assertEmpty(gateway.initialize()); assertEmpty(gateway.snapshot()); assertEmpty(gateway.recoverSaved())
            assertEquals(0, protocol.count("create")); assertEquals(0, protocol.count("resume"))
            val created = gateway.createSaved()
            assertNotNull(created.selected); assertEquals(1, created.stories.size); assertEquals(1, protocol.count("create"))
        } finally { gateway.close() }
    }

    @Test fun reconciliationRevokesRemovedReadyKeyAndSelectsRetainedStory() = runBlocking {
        val protocol = Protocol(listOf(first, retained)); val gateway = DurableGateway(protocol)
        try {
            assertEquals(first, gateway.initialize().selected)
            val old = gateway.respond(DemoAction.GIVE_POTION, 0, DemoMode.ACCEPTED)
            assertTrue(old is DemoResult.Prepared); protocol.delete(first)
            val recovered = gateway.reconcileSaved()
            assertEquals(retained, recovered.selected); assertEquals(listOf(retained), recovered.stories)
            assertEquals(DemoResult.Rejected("Cancelled"), gateway.commitAsync(old))
            assertEquals(retained, gateway.recoverSaved().selected)
            assertEquals(0, protocol.count("commit")); assertEquals(1, protocol.count("submit"))
            assertEquals(1, protocol.count("prepare")); assertEquals(0, protocol.count("cancel"))
            assertEquals(0, protocol.count("create"))
        } finally { gateway.close() }
    }

    @Test fun compatibilityBootstrapCannotRecreateAfterLastStoryDeletion() = runBlocking {
        val protocol = Protocol(emptyList()); var gateway = DurableGateway(protocol)
        try {
            val original = checkNotNull(gateway.initialize().selected)
            assertEquals(1, protocol.count("create")); protocol.delete(original)
            assertEmpty(gateway.reconcileSaved()); assertEmpty(gateway.initialize()); assertEmpty(gateway.snapshot())
            assertEquals(1, protocol.count("create"))
            gateway.close(); gateway = DurableGateway(protocol, autoCreateIfEmpty = false)
            assertEmpty(gateway.initialize()); assertEquals(1, protocol.count("create"))
            assertNotNull(gateway.createSaved().selected); assertEquals(2, protocol.count("create"))
        } finally { gateway.close() }
    }

    @Test fun explicitResumeAndCreateTolerateNoSessionOrDeletionInvalidatedSession() = runBlocking {
        val protocol = Protocol(listOf(first, retained)); val gateway = DurableGateway(protocol, autoCreateIfEmpty = false)
        try {
            assertEquals(retained, gateway.resumeSaved(retained).selected)
            protocol.delete(retained)
            assertEquals(first, gateway.resumeSaved(first).selected)
            gateway.respond(DemoAction.GIVE_POTION, 0, DemoMode.ACCEPTED); protocol.delete(first)
            assertNotNull(gateway.createSaved().selected)
            assertEquals(1, protocol.count("create")); assertEquals(1, protocol.count("cancel"))
        } finally { gateway.close() }
    }

    @Test fun realCloseFailurePreventsReplacementAndCanBeRetried() = runBlocking {
        val protocol = Protocol(listOf(first, retained)); val gateway = DurableGateway(protocol)
        try {
            gateway.initialize(); protocol.closeFailure = "Io"
            failure("Io") { gateway.resumeSaved(retained) }
            assertEquals(1, protocol.count("resume")); assertEquals(0, protocol.count("create"))
            assertEquals(retained, gateway.resumeSaved(retained).selected)
            assertEquals(2, protocol.count("close")); assertEquals(2, protocol.count("resume"))
        } finally { gateway.close() }
    }

    @Test fun reconciliationFailureCannotReplayPendingKeyOrEnableImplicitCreation() = runBlocking {
        val protocol = Protocol(listOf(first)); val gateway = DurableGateway(protocol)
        try {
            gateway.initialize(); gateway.respond(DemoAction.GIVE_POTION, 0, DemoMode.ACCEPTED)
            protocol.delete(first); protocol.workspaceFailure = "Busy"
            failure("Busy") { gateway.reconcileSaved() }
            assertEmpty(gateway.recoverSaved()); assertEmpty(gateway.initialize())
            assertEquals(0, protocol.count("create")); assertEquals(1, protocol.count("submit"))
            assertEquals(1, protocol.count("prepare")); assertEquals(0, protocol.count("commit"))
        } finally { gateway.close() }
    }

    @Test fun failedEmptyWorkspaceReadNeverFallsBackToCreation() = runBlocking {
        val protocol = Protocol(emptyList()); val gateway = DurableGateway(protocol, autoCreateIfEmpty = false)
        try {
            protocol.workspaceFailure = "Integrity"; failure("Integrity") { gateway.initialize() }
            assertEquals(0, protocol.count("create")); assertEmpty(gateway.initialize())
        } finally { gateway.close() }
    }
}

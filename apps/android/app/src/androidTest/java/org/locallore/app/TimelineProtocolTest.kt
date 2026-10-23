/* Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0 */
package org.locallore.app

import androidx.test.ext.junit.runners.AndroidJUnit4
import kotlinx.coroutines.runBlocking
import org.json.JSONArray
import org.json.JSONObject
import org.junit.Assert.*
import org.junit.Test
import org.junit.runner.RunWith

/** Android JSONObject protocol checks. This fake transport does not prove SQLite replay. */
@RunWith(AndroidJUnit4::class)
class TimelineProtocolTest {
    @Test fun retainedParentMetadataIsValidatedBeforeFiltering(): Unit = runBlocking {
        fun retained(data: JSONObject) {
            val rows = data.getJSONArray("branches")
            val child = rows.getJSONObject(0).put("parent_branch", "parent").put("fork_revision", 3)
            val root = rows.getJSONObject(1)
            val parent = JSONObject().put("scope", JSONObject().put("story", "story-a").put("branch", "parent"))
                .put("parent_branch", "main").put("fork_revision", 1).put("revision", 3).put("drafts", 0).put("retired", true)
            data.put("branches", JSONArray().put(child).put(root).put(parent))
        }
        val transport = Protocol().also { it.changeCatalog = ::retained }
        val gateway = DurableGateway(transport, autoCreateIfEmpty = false)
        try {
            assertEquals(listOf("child", "main"), gateway.initialize().timelines.map { it.branch })
            assertEquals("child", gateway.resumeSaved(SavedStory("story-a", "child", "Original title", 3)).selected?.branch)
        } finally { gateway.close() }
        val mutations: List<(JSONObject) -> Unit> = listOf(
            { it.getJSONArray("branches").getJSONObject(2).put("retired", "true") },
            { it.getJSONArray("branches").getJSONObject(2).put("drafts", 1) },
            { it.getJSONArray("branches").getJSONObject(1).put("retired", true) },
            { it.getJSONArray("branches").getJSONObject(2).put("parent_branch", "absent") },
            { it.getJSONArray("branches").getJSONObject(2).put("revision", 2) },
        )
        for (mutation in mutations) {
            val malformed = Protocol().also { it.changeCatalog = { data -> retained(data); mutation(data) } }
            val reader = DurableGateway(malformed, autoCreateIfEmpty = false)
            try {
                try { reader.initialize(); fail("Invalid retained ancestry accepted") }
                catch (failure: WorkspaceFailure) { assertEquals("Malformed", failure.category) }
                assertFalse(malformed.calls.any { it in setOf("submit", "prepare", "commit", "free_text", "create") })
            } finally { reader.close() }
        }
    }
    private class Protocol(val storyId: String = "story-a") : WorkspaceTransport {
        var selected = "main"
        var receiptStory = storyId
        var changeCatalog: (JSONObject) -> Unit = {}
        val calls = mutableListOf<String>()
        var closed = false
        private fun scope(branch: String, story: String = storyId) =
            JSONObject().put("story", story).put("branch", branch)
        private fun ok(data: JSONObject) = JSONObject().put("version", 1).put("status", "ok").put("data", data)
        private fun head() = if (selected == "main") 2L else 3L
        fun catalog() = JSONObject().put("version", 2).put("story_id", storyId).put("title", "Original title")
            .put("root_branch", "main").put("branches", JSONArray()
                .put(JSONObject().put("scope", scope("child")).put("parent_branch", "main").put("fork_revision", 1)
                    .put("revision", 3).put("drafts", 2).put("retired", false))
                .put(JSONObject().put("scope", scope("main")).put("parent_branch", JSONObject.NULL)
                    .put("fork_revision", JSONObject.NULL).put("revision", 2).put("drafts", 0).put("retired", false)))
        override suspend fun exchange(command: JSONObject): JSONObject {
            val op = command.getString("op"); calls += op
            return when (op) {
                "capabilities" -> ok(JSONObject().put("free_text", false))
                "workspace" -> ok(JSONObject().put("persistent", true).put("schema_version", 1)
                    .put("database_schema_version", 3).put("location", "/synthetic/workspace.sqlite3")
                    .put("stories", JSONArray().put(JSONObject().put("scope", scope("main"))
                        .put("title", "Original title").put("revision", 2).put("drafts", 0).put("retired", false))))
                "branches" -> {
                    assertEquals(storyId, command.getString("story"))
                    ok(catalog().also(changeCatalog))
                }
                "resume" -> {
                    assertEquals(storyId, command.getJSONObject("scope").getString("story"))
                    selected = command.getJSONObject("scope").getString("branch")
                    check(selected in setOf("main", "child"))
                    ok(JSONObject().put("session", "session-$selected").put("scope", scope(selected)).put("revision", head()))
                }
                "open" -> ok(JSONObject().put("scope", scope(selected)).put("revision", head()))
                "close" -> ok(JSONObject())
                "play_snapshot" -> {
                    assertEquals(head(), command.getLong("expected_revision"))
                    val receipts = JSONArray().put(JSONObject().put("request", JSONObject()
                        .put("scope", scope("main", receiptStory)).put("turn", "ancestor-original")
                        .put("intent", JSONObject().put("kind", "dialogue")
                            .put("value", JSONObject().put("text", "I may be mistaken."))))
                        .put("narration", "Mira heard your statement."))
                    if (selected == "child") receipts.put(JSONObject().put("request", JSONObject()
                        .put("scope", scope("child")).put("turn", "child-original")
                        .put("intent", JSONObject().put("kind", "dialogue")
                            .put("value", JSONObject().put("text", "These are only my words."))))
                        .put("narration", "Your words were recorded."))
                    ok(JSONObject().put("scope", scope(selected)).put("revision", head()).put("rules", "fantasy_v1")
                        .put("inventory", JSONObject().put("potion", JSONObject()))
                        .put("player", JSONObject().put("scope", scope(selected)).put("revision", head()).put("observer", "player"))
                        .put("receipts", receipts))
                }
                else -> error("Unexpected protocol operation")
            }
        }
        override fun close() { closed = true }
    }

    @Test fun childResumePreservesAncestorTextAndUsesCatalogMetadataWithoutGameplay(): Unit = runBlocking {
        val transport = Protocol(); val gateway = DurableGateway(transport, autoCreateIfEmpty = false)
        try {
            val root = gateway.initialize()
            assertEquals("main", root.selected?.branch); assertEquals(2, root.timelines.size)
            val child = gateway.resumeSaved(SavedStory("story-a", "child", "Untrusted UI title", 999))
            assertEquals(SavedStory("story-a", "child", "Original title", 3), child.selected)
            assertEquals(listOf("main"), child.stories.map { it.branch })
            assertEquals(3L, child.revision); assertEquals(2, child.uncommittedDrafts)
            assertEquals(listOf("I may be mistaken.", "Mira heard your statement.",
                "These are only my words.", "Your words were recorded."), child.messages.map { it.text })
            assertEquals("You", child.potionOwner)
            assertTrue(transport.calls.all { it in setOf("workspace", "resume", "open", "play_snapshot", "branches", "capabilities", "close") })
            assertEquals(2, transport.calls.count { it == "branches" })
        } finally { gateway.close() }
        assertTrue(transport.closed)
    }

    @Test fun malformedCatalogCannotSelectOrGrantAuthority(): Unit = runBlocking {
        val cases: List<(JSONObject) -> Unit> = listOf(
            { it.put("version", "1") }, { it.put("story_id", "other-story") },
            { it.put("title", "Changed title") }, { it.put("root_branch", "child") },
            { it.put("inventory", JSONObject().put("potion", 99)) },
            { it.put("branches", JSONArray()) },
            { data -> repeat(256) { data.getJSONArray("branches").put(data.getJSONArray("branches").getJSONObject(1)) } },
            { it.getJSONArray("branches").put(it.getJSONArray("branches").getJSONObject(1)) },
            { data -> val rows = data.getJSONArray("branches"); val first = rows.get(0); rows.put(0, rows.get(1)); rows.put(1, first) },
            { it.getJSONArray("branches").getJSONObject(0).getJSONObject("scope").put("story", "other-story") },
            { it.getJSONArray("branches").getJSONObject(0).put("revision", -1) },
            { it.getJSONArray("branches").getJSONObject(0).put("drafts", 2147483648L) },
            { it.getJSONArray("branches").getJSONObject(0).put("drafts", 4097) },
            { it.getJSONArray("branches").getJSONObject(0).put("revision", "3") },
            { it.getJSONArray("branches").getJSONObject(0).put("revision", 3.5) },
            { it.getJSONArray("branches").getJSONObject(0).put("parent_branch", "absent") },
            { it.getJSONArray("branches").getJSONObject(0).put("fork_revision", JSONObject.NULL) },
            { it.getJSONArray("branches").getJSONObject(0).put("fork_revision", 4) },
            { it.getJSONArray("branches").getJSONObject(0).put("fork_revision", 3) },
            { it.getJSONArray("branches").getJSONObject(0).put("parent_branch", "child") },
            { it.getJSONArray("branches").getJSONObject(1).put("parent_branch", "child").put("fork_revision", 1) },
            { it.getJSONArray("branches").getJSONObject(1).put("revision", 1) },
        )
        for (change in cases) {
            val transport = Protocol().also { it.changeCatalog = change }
            val gateway = DurableGateway(transport, autoCreateIfEmpty = false)
            try {
                try { gateway.initialize(); fail("Malformed native catalog was accepted") }
                catch (failure: WorkspaceFailure) {
                    assertEquals("Malformed", failure.category)
                    assertEquals("Workspace operation failed", failure.message)
                }
                assertFalse(transport.calls.any { it in setOf("submit", "prepare", "commit", "free_text", "create") })
            } finally { gateway.close() }
        }
    }

    @Test fun oversizedStructurallyValidCatalogFailsSerializedBodyBudget(): Unit = runBlocking {
        val story = "s".repeat(64)
        val transport = Protocol(story).also { protocol -> protocol.changeCatalog = { data ->
            // Exactly 256 sorted, unique, bounded-ID rows with a depth-three
            // lineage. Only the serialized catalog budget is exceeded.
            val root = data.getJSONArray("branches").getJSONObject(1)
            val parent = "a".repeat(64)
            fun row(branch: String, ancestor: String) = JSONObject()
                .put("scope", JSONObject().put("story", story).put("branch", branch))
                .put("parent_branch", ancestor).put("fork_revision", 1)
                .put("revision", 3).put("drafts", 0).put("retired", false)
            val rows = JSONArray().put(row(parent, "main"))
            repeat(254) { index -> rows.put(row("b" + index.toString().padStart(3, '0') + "x".repeat(60), parent)) }
            rows.put(root); data.put("branches", rows)
            assertEquals(256, rows.length())
            assertTrue(data.toString().toByteArray(Charsets.UTF_8).size > 60 * 1024)
        } }
        val gateway = DurableGateway(transport, autoCreateIfEmpty = false)
        try {
            try { gateway.initialize(); fail("Oversized catalog was accepted") }
            catch (failure: WorkspaceFailure) { assertEquals("Malformed", failure.category) }
            assertFalse(transport.calls.any { it in setOf("submit", "prepare", "commit", "create") })
        } finally { gateway.close() }
    }

    @Test fun racedChildHeadAndForeignReceiptFailClosedThenFreshRecoveryWorks(): Unit = runBlocking {
        val transport = Protocol(); val gateway = DurableGateway(transport, autoCreateIfEmpty = false)
        try {
            gateway.initialize()
            transport.changeCatalog = { it.getJSONArray("branches").getJSONObject(0).put("revision", 4) }
            try { gateway.resumeSaved(SavedStory("story-a", "child", "Original title", 3)); fail("Raced head was accepted") }
            catch (failure: WorkspaceFailure) { assertEquals("Stale", failure.category) }
            transport.changeCatalog = {}
            assertEquals(3L, gateway.recoverSaved().revision)
            transport.receiptStory = "foreign-story"
            try { gateway.snapshot(); fail("Foreign receipt was accepted") }
            catch (_: IllegalStateException) { /* Existing scope fence remains in force. */ }
            transport.receiptStory = "story-a"
            assertEquals("child", gateway.recoverSaved().selected?.branch)
            assertFalse(transport.calls.any { it in setOf("submit", "prepare", "commit", "create") })
        } finally { gateway.close() }
    }
}

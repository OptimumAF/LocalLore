/* Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0 */
package org.locallore.app

import kotlinx.coroutines.CompletableDeferred
import kotlinx.coroutines.ExperimentalCoroutinesApi
import kotlinx.coroutines.NonCancellable
import kotlinx.coroutines.async
import kotlinx.coroutines.test.runCurrent
import kotlinx.coroutines.test.runTest
import kotlinx.coroutines.withContext
import org.json.JSONArray
import org.json.JSONObject
import org.junit.Assert.*
import org.junit.Test

/** Actual native presentation assets; session/catalog transport metadata is synthetic. */
private class SelfProfilePort(val fixture: SelfProfileFixtures.Case) : WorkspaceTransport {
    val commands = mutableListOf<JSONObject>()
    var closes = 0
    var mutateNext: ((JSONObject) -> Unit)? = null
    var catalogHead = fixture.revision
    var pausePresentation: (suspend () -> Unit)? = null
    var pauseCapabilities: (suspend () -> Unit)? = null
    private fun scope() = JSONObject().put("story", fixture.story).put("branch", fixture.branch)
    private fun ok(data: JSONObject) = JSONObject().put("version", 1).put("status", "ok").put("data", data)
    fun story() = SavedStory(fixture.story, fixture.branch, "Synthetic catalogue title, not the actor name", fixture.revision)
    fun gateway() = DurableGateway(this, autoCreateIfEmpty = false, initialScopeHint = fixture.scope)
    override suspend fun exchange(command: JSONObject): JSONObject {
        commands += JSONObject(command.toString())
        return when (val op = command.getString("op")) {
            "workspace" -> ok(JSONObject().put("persistent", true)
                .put("location", "D:/synthetic/workspace-not-actor-location")
                .put("schema_version", 1).put("database_schema_version", 5)
                .put("stories", JSONArray().put(JSONObject().put("scope", scope())
                    .put("title", story().title).put("revision", catalogHead).put("drafts", 0))))
            "branches" -> ok(JSONObject().put("version", 2).put("story_id", fixture.story)
                .put("title", story().title).put("root_branch", fixture.branch)
                .put("branches", JSONArray().put(JSONObject().put("scope", scope())
                    .put("parent_branch", JSONObject.NULL).put("fork_revision", JSONObject.NULL)
                    .put("revision", catalogHead).put("drafts", 0).put("retired", false))))
            "resume", "open" -> ok(JSONObject().put("session", "synthetic-profile-session")
                .put("scope", scope()).put("revision", fixture.revision))
            "play_presentation_v2" -> {
                val reply = fixture.reply()
                mutateNext?.also { mutateNext = null }?.invoke(reply.getJSONObject("data"))
                pausePresentation?.also { pausePresentation = null }?.invoke()
                reply
            }
            "capabilities" -> {
                pauseCapabilities?.also { pauseCapabilities = null }?.invoke()
                ok(JSONObject().put("free_text", false))
            }
            "close" -> ok(JSONObject().put("closed", true))
            else -> throw AssertionError("Profile browsing dispatched an extra operation: $op")
        }
    }
    override fun close() { closes++ }
    fun assertReadOnly() {
        assertTrue(commands.all { it.getString("op") in setOf(
            "workspace", "branches", "resume", "open", "play_presentation_v2", "capabilities", "close") })
        assertFalse(commands.any { it.getString("op") in setOf("inspection_query", "play_snapshot", "submit", "prepare", "commit") })
    }
}

@OptIn(ExperimentalCoroutinesApi::class)
class DurableGatewayProfileTest {
    private suspend fun refused(expected: String, body: suspend () -> Unit) {
        try { body(); fail("A stale or malformed profile became a coherent saved snapshot") }
        catch (failure: WorkspaceFailure) { assertEquals(expected, failure.category) }
    }

    @Test fun genuineProfilesUseTheExistingSinglePresentationReadAndPreserveInventoryMessagesAndNativeLocation() = runTest {
        for (fixture in SelfProfileFixtures.cases) {
            val port = SelfProfilePort(fixture)
            val gateway = port.gateway()
            try {
                val saved = gateway.initialize()
                assertEquals(fixture.expected(), saved.playerProfile)
                assertEquals(fixture.revision, saved.revision)
                assertEquals(port.story(), saved.selected)
                assertNotEquals(saved.location, saved.playerProfile!!.location)
                assertEquals(TextProvider.UNAVAILABLE, saved.textProvider)
                val request = port.commands.single { it.getString("op") == "play_presentation_v2" }
                assertEquals(setOf("op", "session", "scope", "expected_revision"), request.keys().asSequence().toSet())
                assertEquals("synthetic-profile-session", request.getString("session"))
                assertEquals(fixture.revision, request.getLong("expected_revision"))
                assertEquals(fixture.story, request.getJSONObject("scope").getString("story"))
                assertEquals(fixture.branch, request.getJSONObject("scope").getString("branch"))
                val again = gateway.snapshot()
                assertEquals(saved.playerProfile, again.playerProfile)
                assertEquals(saved.inventory, again.inventory)
                assertEquals(saved.messages, again.messages)
                assertEquals(2, port.commands.count { it.getString("op") == "play_presentation_v2" })
                port.assertReadOnly()
            } finally { gateway.close() }
            assertEquals(1, port.closes)
        }
    }

    @Test fun establishedObserverAndCoherentCatalogHeadCannotBeReplacedByOtherwiseValidProfileData() = runTest {
        val fixture = SelfProfileFixtures.Case(2, true)
        val port = SelfProfilePort(fixture)
        val gateway = port.gateway()
        try {
            val original = gateway.initialize()
            port.mutateNext = { data ->
                val player = "a-foreign-valid-observer"
                data.getJSONObject("player").put("observer", player)
                // Keep the item relation structurally valid so the established
                // observer binding, rather than an inventory mismatch, is causal.
                val inventory = data.getJSONObject("inventory")
                inventory.keys().asSequence().forEach { inventory.getJSONObject(it).put("owner", player) }
            }
            refused("Stale") { gateway.snapshot() }
            assertEquals(original.playerProfile, gateway.snapshot().playerProfile)
            for (mutate in listOf<(JSONObject) -> Unit>(
                { it.put("revision", fixture.revision + 1) },
                { it.getJSONObject("scope").put("branch", "another-branch") },
                { it.getJSONObject("player").getJSONObject("self_state").put("private_beliefs", JSONArray()) },
            )) {
                port.mutateNext = mutate
                refused("Malformed") { gateway.snapshot() }
            }
            // Both catalogue rows advance together; they are internally coherent
            // but cannot be joined to the older native presentation head.
            port.catalogHead = fixture.revision + 1
            refused("Stale") { gateway.snapshot() }
            port.catalogHead = fixture.revision
            val recovered = gateway.snapshot()
            assertEquals(original.playerProfile, recovered.playerProfile)
            assertEquals(original.messages, recovered.messages)
            assertEquals(original.inventory, recovered.inventory)
            port.assertReadOnly()
        } finally { gateway.close() }
    }

    @Test fun reusedSessionHeadAndScopeDoNotRescueOldAttachmentReadsBeforeOrAfterProfileDecoding() = runTest {
        for (phase in listOf("presentation", "capabilities")) {
            for (action in listOf("reattach", "close")) {
                val fixture = SelfProfileFixtures.Case(2, false)
                val port = SelfProfilePort(fixture)
                val gateway = port.gateway()
                val entered = CompletableDeferred<Unit>()
                val release = CompletableDeferred<Unit>()
                try {
                    val original = gateway.initialize()
                    val pause: suspend () -> Unit = {
                        entered.complete(Unit)
                        withContext(NonCancellable) { release.await() }
                    }
                    if (phase == "presentation") port.pausePresentation = pause else port.pauseCapabilities = pause
                    val pending = async {
                        refused(if (action == "close") "Closed" else "Stale") { gateway.snapshot() }
                    }
                    runCurrent()
                    assertTrue(entered.isCompleted)
                    if (action == "close") gateway.close() else {
                        val fresh = gateway.resumeSaved(port.story())
                        assertEquals(original.selected, fresh.selected)
                        assertEquals(original.playerProfile, fresh.playerProfile)
                    }
                    release.complete(Unit)
                    pending.await()
                    if (action == "reattach") assertEquals(original.playerProfile, gateway.snapshot().playerProfile)
                    port.assertReadOnly()
                } finally { release.complete(Unit); gateway.close() }
                assertEquals(1, port.closes)
            }
        }
    }
}

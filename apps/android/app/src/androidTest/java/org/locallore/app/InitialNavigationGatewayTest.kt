/* Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0 */
package org.locallore.app

import androidx.test.ext.junit.runners.AndroidJUnit4
import kotlinx.coroutines.runBlocking
import org.json.JSONArray
import org.json.JSONObject
import org.junit.Assert.*
import org.junit.Test
import org.junit.runner.RunWith

/** Real gateway protocol, Android JSONObject, synthetic transport; no Activity, JNI or SQLite. */
@RunWith(AndroidJUnit4::class)
class InitialNavigationGatewayTest {
    private val rootB = PlayDraftScope("story-b", "main")
    private val childB = PlayDraftScope("story-b", "child")
    private val rootA = SavedStory("story-a", "main", "Title story-a", 0)

    @Test fun nondefaultRootIsValidatedBeforeTheOnlyInitialResume(): Unit = runBlocking {
        val port = CatalogPort()
        val gateway = reader(port, rootB)
        try {
            val saved = gateway.initialize()
            assertEquals(SavedStory("story-b", "main", "Title story-b", 2), saved.selected)
            assertEquals(2L, saved.revision)
            assertFalse(saved.selectionRestoreUnavailable)
            assertEquals(listOf("workspace", "branches", "resume"), port.ops.take(3))
            assertEquals(listOf(rootB), port.resumed)
            assertEquals(listOf("story-a", "story-b"), saved.stories.map { it.story })
            assertNoGameplay(port)
        } finally { gateway.close() }
        assertEquals(1, port.closes)
    }

    @Test fun activeChildUsesNativeHeadAndRetiredRowsAreNeverSelectable(): Unit = runBlocking {
        val port = CatalogPort()
        val gateway = reader(port, childB)
        try {
            val saved = gateway.initialize()
            assertEquals(SavedStory("story-b", "child", "Title story-b", 3), saved.selected)
            assertEquals(3L, saved.revision)
            assertEquals(listOf("child", "main"), saved.timelines.map { it.branch })
            assertEquals("main", saved.stories.single { it.story == "story-b" }.branch)
            assertFalse(saved.selectionRestoreUnavailable)
            assertEquals(listOf(childB), port.resumed)
            assertEquals("branches", port.ops[1])
            assertNoGameplay(port)
        } finally { gateway.close() }
    }

    @Test fun missingStoryMissingBranchAndRetiredBranchUseActualDefaultWithOneShotNotice(): Unit = runBlocking {
        for (hint in listOf(PlayDraftScope("absent-story", "main"),
            PlayDraftScope("story-b", "absent-branch"), PlayDraftScope("story-b", "retired"))) {
            val port = CatalogPort()
            val gateway = reader(port, hint)
            try {
                val fallback = gateway.initialize()
                assertEquals(rootA, fallback.selected)
                assertTrue(fallback.selectionRestoreUnavailable)
                assertEquals(listOf(PlayDraftScope("story-a", "main")), port.resumed)
                assertFalse(gateway.snapshot().selectionRestoreUnavailable)
                assertFalse(gateway.recoverSaved().selectionRestoreUnavailable)
                assertEquals(rootA, gateway.reconcileSaved().selected)
                assertNoGameplay(port)
            } finally { gateway.close() }
        }
    }

    @Test fun missingHintInEmptyLibrarySettlesEmptyWithoutCreatingAndConsumesNotice(): Unit = runBlocking {
        val port = CatalogPort().also { it.empty = true }
        val gateway = reader(port, childB)
        try {
            val empty = gateway.initialize()
            assertNull(empty.selected)
            assertTrue(empty.stories.isEmpty())
            assertTrue(empty.selectionRestoreUnavailable)
            assertEquals(listOf("workspace"), port.ops)
            assertFalse(gateway.initialize().selectionRestoreUnavailable)
            assertTrue(port.resumed.isEmpty())
            assertNoGameplay(port)
        } finally { gateway.close() }
    }

    @Test fun corruptStoryCatalogCannotMasqueradeAsMissingHintOrAuthorizeResume(): Unit = runBlocking {
        val corruptions: List<(JSONArray) -> Unit> = listOf(
            { it.getJSONObject(1).getJSONObject("scope").put("story", 123) },
            { it.getJSONObject(1).getJSONObject("scope").put("branch", "bad/branch") },
            { it.getJSONObject(1).put("revision", true) },
            { it.getJSONObject(1).put("revision", "2") },
            { it.getJSONObject(1).put("drafts", -1) },
            { it.put(it.getJSONObject(1)) },
            { rows -> rows.put(0, "not a catalog row") },
            { rows ->
                while (rows.length() > 0) rows.remove(rows.length() - 1)
                repeat(257) { index -> rows.put(JSONObject().put("scope", scope("story-$index", "main"))
                    .put("title", "Synthetic title").put("revision", 0).put("drafts", 0)) }
            },
        )
        for (corrupt in corruptions) {
            val port = CatalogPort().also { it.changeStories = corrupt }
            val gateway = reader(port, childB)
            try {
                expectFailure { gateway.initialize() }
                assertTrue(port.resumed.isEmpty())
                assertEquals(listOf("workspace"), port.ops)
                assertNoGameplay(port)
            } finally { gateway.close() }
        }
    }

    @Test fun malformedBranchCatalogFailsBeforeResumeRatherThanFallingBack(): Unit = runBlocking {
        val corruptions: List<(JSONObject) -> Unit> = listOf(
            { it.put("version", "2") },
            { it.put("story_id", "story-a") },
            { it.getJSONArray("branches").getJSONObject(0).put("retired", "false") },
            { it.getJSONArray("branches").getJSONObject(0).put("parent_branch", "child") },
            { it.getJSONArray("branches").getJSONObject(1).put("revision", 99) },
            { data -> data.getJSONArray("branches").put(data.getJSONArray("branches").getJSONObject(0)) },
        )
        for (corrupt in corruptions) {
            val port = CatalogPort().also { it.changeBranches = corrupt }
            val gateway = reader(port, childB)
            try {
                val failure = expectFailure { gateway.initialize() }
                assertTrue(failure is WorkspaceFailure)
                assertEquals("Malformed", (failure as WorkspaceFailure).category)
                assertEquals(listOf("workspace", "branches"), port.ops)
                assertTrue(port.resumed.isEmpty())
                assertNoGameplay(port)
            } finally { gateway.close() }
        }
    }

    @Test fun storageTransportAndResumeRaceFailuresRetainHintUntilSuccessfulRetry(): Unit = runBlocking {
        for (op in listOf("workspace", "branches", "resume")) {
            for (category in listOf("Full", "Busy", "NotFound")) {
                val port = CatalogPort().also { it.failOnce(op, 1, category) }
                val gateway = reader(port, childB)
                try {
                    val failure = expectFailure { gateway.initialize() }
                    assertEquals(category, (failure as WorkspaceFailure).category)
                    val retried = gateway.initialize()
                    assertEquals(childB.story, retried.selected?.story)
                    assertEquals(childB.branch, retried.selected?.branch)
                    assertFalse(retried.selectionRestoreUnavailable)
                    assertTrue(port.resumed.all { it == childB })
                    assertNoGameplay(port)
                } finally { gateway.close() }
            }
        }
    }

    @Test fun failuresAfterAttachCannotConsumeTheHintOrPublishDefaultDuringRecovery(): Unit = runBlocking {
        for ((op, ordinal) in listOf("open" to 1, "play_snapshot" to 1, "workspace" to 2,
            "branches" to 2, "capabilities" to 1)) {
            val port = CatalogPort().also { it.failOnce(op, ordinal, "Full") }
            val gateway = reader(port, childB)
            try {
                assertEquals("Full", (expectFailure { gateway.initialize() } as WorkspaceFailure).category)
                assertEquals(listOf(childB), port.resumed)
                val recovered = gateway.recoverSaved()
                assertEquals(childB.story, recovered.selected?.story)
                assertEquals(childB.branch, recovered.selected?.branch)
                assertFalse(recovered.selectionRestoreUnavailable)
                assertEquals(listOf(childB), port.resumed)
                assertNoGameplay(port)
            } finally { gateway.close() }
        }
    }

    @Test fun reconcileAfterAnAttachedFailureMustStillResolveTheOriginalUnconsumedHint(): Unit = runBlocking {
        val port = CatalogPort().also { it.failOnce("play_snapshot", 1, "Busy") }
        val gateway = reader(port, childB)
        try {
            expectFailure { gateway.initialize() }
            val recovered = gateway.reconcileSaved()
            assertEquals("child", recovered.selected?.branch)
            assertEquals("story-b", recovered.selected?.story)
            assertEquals(listOf(childB, childB), port.resumed)
            assertFalse(recovered.selectionRestoreUnavailable)
            assertNoGameplay(port)
        } finally { gateway.close() }
    }

    @Test fun fallbackNoticeSurvivesAttachedFailureAndAppearsOnlyOnFirstCoherentSnapshot(): Unit = runBlocking {
        val port = CatalogPort().also { it.failOnce("play_snapshot", 1, "Full") }
        val gateway = reader(port, PlayDraftScope("absent-story", "main"))
        try {
            expectFailure { gateway.initialize() }
            val coherent = gateway.recoverSaved()
            assertEquals(rootA, coherent.selected)
            assertTrue(coherent.selectionRestoreUnavailable)
            assertFalse(gateway.snapshot().selectionRestoreUnavailable)
            assertFalse(gateway.reconcileSaved().selectionRestoreUnavailable)
            assertNoGameplay(port)
        } finally { gateway.close() }
    }

    @Test fun successfulInitialSelectionCannotReapplyAfterExplicitUserNavigation(): Unit = runBlocking {
        val port = CatalogPort()
        val gateway = reader(port, childB)
        try {
            assertEquals("child", gateway.initialize().selected?.branch)
            assertEquals(rootA, gateway.resumeSaved(rootA).selected)
            assertEquals(rootA, gateway.recoverSaved().selected)
            val reopened = gateway.reconcileSaved()
            assertEquals(rootA, reopened.selected)
            assertFalse(reopened.selectionRestoreUnavailable)
            assertEquals(listOf(childB, PlayDraftScope("story-a", "main"), PlayDraftScope("story-a", "main")),
                port.resumed)
            assertNoGameplay(port)
        } finally { gateway.close() }
    }

    @Test fun headRaceDuringSnapshotIsStaleNotMissingAndRetryUsesTheHintedBranch(): Unit = runBlocking {
        val port = CatalogPort().also { it.advanceChildOnSecondCatalog = true }
        val gateway = reader(port, childB)
        try {
            assertEquals("Stale", (expectFailure { gateway.initialize() } as WorkspaceFailure).category)
            val recovered = gateway.recoverSaved()
            assertEquals(SavedStory("story-b", "child", "Title story-b", 4), recovered.selected)
            assertFalse(recovered.selectionRestoreUnavailable)
            assertEquals(listOf(childB), port.resumed)
            assertNoGameplay(port)
        } finally { gateway.close() }
    }

    private fun reader(port: CatalogPort, hint: PlayDraftScope) =
        DurableGateway(port, autoCreateIfEmpty = false, initialScopeHint = hint)

    private suspend fun expectFailure(body: suspend () -> Any?): Exception {
        try { body() } catch (failure: Exception) { return failure }
        throw AssertionError("Invalid or uncertain startup selection returned a snapshot")
    }

    private fun assertNoGameplay(port: CatalogPort) {
        assertTrue(port.ops.all { it in setOf("workspace", "branches", "resume", "open", "play_snapshot",
            "capabilities", "close") })
    }

    private class CatalogPort : WorkspaceTransport {
        val ops = mutableListOf<String>()
        val resumed = mutableListOf<PlayDraftScope>()
        var closes = 0
        var empty = false
        var changeStories: (JSONArray) -> Unit = {}
        var changeBranches: (JSONObject) -> Unit = {}
        var advanceChildOnSecondCatalog = false
        private var childHead = 3L
        private var selected: PlayDraftScope? = null
        private val counts = mutableMapOf<String, Int>()
        private var fault: Triple<String, Int, String>? = null
        fun failOnce(op: String, ordinal: Int, category: String) { fault = Triple(op, ordinal, category) }
        private fun head(s: PlayDraftScope) = when {
            s.story == "story-a" -> 0L
            s.branch == "child" -> childHead
            else -> 2L
        }
        private fun row(s: PlayDraftScope) = JSONObject().put("scope", scope(s.story, s.branch))
            .put("title", "Title ${s.story}").put("revision", head(s)).put("drafts", 0)
        private fun ok(data: JSONObject) = JSONObject().put("version", 1).put("status", "ok").put("data", data)
        private fun branch(story: String, id: String, parent: String?, fork: Long?, revision: Long,
            retired: Boolean = false) = JSONObject().put("scope", scope(story, id))
            .put("parent_branch", parent ?: JSONObject.NULL).put("fork_revision", fork ?: JSONObject.NULL)
            .put("revision", revision).put("drafts", 0).put("retired", retired)

        override suspend fun exchange(command: JSONObject): JSONObject {
            val op = command.getString("op")
            ops += op
            val count = (counts[op] ?: 0) + 1
            counts[op] = count
            fault?.let { (failedOp, ordinal, category) ->
                if (op == failedOp && count == ordinal) {
                    fault = null
                    return JSONObject().put("version", 1).put("status", "error").put("error", category)
                }
            }
            return when (op) {
                "workspace" -> {
                    val rows = JSONArray()
                    if (!empty) rows.put(row(PlayDraftScope("story-a", "main")))
                        .put(row(PlayDraftScope("story-b", "main")))
                    ok(JSONObject().put("persistent", true).put("schema_version", 1)
                        .put("database_schema_version", 5).put("location", "/synthetic/navigation.sqlite3")
                        .put("stories", rows.also(changeStories)))
                }
                "branches" -> {
                    val story = command.getString("story")
                    assertTrue(story in setOf("story-a", "story-b"))
                    if (advanceChildOnSecondCatalog && count == 2 && story == "story-b") childHead = 4
                    val rows = JSONArray()
                    if (story == "story-b") rows.put(branch(story, "child", "main", 1, childHead))
                    rows.put(branch(story, "main", null, null, if (story == "story-a") 0 else 2))
                    if (story == "story-b") rows.put(branch(story, "retired", "main", 1, 2, true))
                    ok(JSONObject().put("version", 2).put("story_id", story).put("title", "Title $story")
                        .put("root_branch", "main").put("branches", rows).also(changeBranches))
                }
                "resume" -> {
                    val s = command.getJSONObject("scope")
                    val chosen = PlayDraftScope(s.getString("story"), s.getString("branch"))
                    assertTrue(chosen in setOf(PlayDraftScope("story-a", "main"),
                        PlayDraftScope("story-b", "main"), PlayDraftScope("story-b", "child")))
                    resumed += chosen
                    selected = chosen
                    ok(JSONObject().put("session", "session-${resumed.size}")
                        .put("scope", scope(chosen.story, chosen.branch)).put("revision", head(chosen)))
                }
                "open", "play_snapshot" -> {
                    val s = checkNotNull(selected)
                    assertEquals(s.story, command.getJSONObject("scope").getString("story"))
                    assertEquals(s.branch, command.getJSONObject("scope").getString("branch"))
                    val data = JSONObject().put("scope", scope(s.story, s.branch)).put("revision", head(s))
                    if (op == "play_snapshot") {
                        assertEquals(head(s), command.getLong("expected_revision"))
                        data.put("player", JSONObject().put("scope", scope(s.story, s.branch))
                            .put("revision", head(s)).put("observer", "player"))
                            .put("inventory", JSONObject().put("potion", JSONObject()))
                            .put("rules", "fantasy_v1").put("receipts", JSONArray())
                    }
                    ok(data)
                }
                "capabilities" -> ok(JSONObject().put("free_text", false))
                "close" -> { selected = null; ok(JSONObject()) }
                else -> throw AssertionError("Startup navigation dispatched gameplay or an unknown operation")
            }
        }
        override fun close() { closes++ }
    }

    companion object {
        private fun scope(story: String, branch: String) = JSONObject().put("story", story).put("branch", branch)
    }
}

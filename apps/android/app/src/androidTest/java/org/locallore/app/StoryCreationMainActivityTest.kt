/* Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0 */
package org.locallore.app

import android.content.Intent
import androidx.compose.ui.test.*
import androidx.compose.ui.test.junit4.createEmptyComposeRule
import androidx.lifecycle.ViewModelProvider
import androidx.test.core.app.ActivityScenario
import androidx.test.ext.junit.runners.AndroidJUnit4
import androidx.test.platform.app.InstrumentationRegistry
import java.io.File
import java.nio.file.Files
import java.nio.file.LinkOption
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.runBlocking
import org.json.JSONArray
import org.json.JSONObject
import org.junit.Assert.*
import org.junit.Rule
import org.junit.Test
import org.junit.runner.RunWith

/** Real Main factory/UI/JNI with original synthetic saves. Author UNRUN; no OS-death/model qualification. */
@RunWith(AndroidJUnit4::class)
class StoryCreationMainActivityTest {
    @get:Rule val compose = createEmptyComposeRule()
    private lateinit var model: ShellViewModel
    private companion object {
        const val TITLE_A = "SYNTHETIC named story A: caf\u00e9 \uD83E\uDDED"
        const val TITLE_B = "SYNTHETIC named story B: snow \u96ea"
        const val DRAFT = "SYNTHETIC unsent creation-review dialogue.\nKeep my original scope."
        const val GIFT = "I give my last potion to Mira."
    }
    private data class Library(
        val workspace: String,
        val rows: Map<String, String>,
        val catalogs: Map<String, String>,
        val views: Map<String, String>,
    )

    private fun database(): File {
        val context = InstrumentationRegistry.getInstrumentation().targetContext
        assertEquals("org.locallore.app.draftprocessverify", context.packageName)
        assertTrue(BuildConfig.INPUT_PROCESS_VERIFICATION)
        val base = context.noBackupFilesDir.canonicalFile
        val workspace = File(base, "workspace-v1")
        if (!workspace.exists()) check(workspace.mkdir())
        check(Files.isDirectory(workspace.toPath(), LinkOption.NOFOLLOW_LINKS))
        check(!Files.isSymbolicLink(workspace.toPath()) && workspace.canonicalFile.parentFile == base)
        val path = File(workspace, "stories.sqlite3")
        if (Files.exists(path.toPath(), LinkOption.NOFOLLOW_LINKS)) {
            check(Files.isRegularFile(path.toPath(), LinkOption.NOFOLLOW_LINKS))
            check(!Files.isSymbolicLink(path.toPath()))
        }
        check(path.canonicalFile.parentFile == workspace.canonicalFile)
        return path
    }

    /** Fresh bounded native reader, never SQL, arbitrary file adoption or an Activity owner substitute. */
    private class Reader(path: File) : AutoCloseable {
        private var handle = NativeWorkspace.open(path.absolutePath).also { check(it > 0) }
        private var totalBytes = 0L
        fun data(command: JSONObject): JSONObject {
            check(handle > 0)
            val input = JSONObject().put("version", 1).put("command", command).toString().toByteArray(Charsets.UTF_8)
            val raw = NativeWorkspace.call(handle, input)
            check(raw.size in 1..262_144)
            totalBytes += raw.size
            check(totalBytes <= 2L * 1024 * 1024)
            val reply = JSONObject(raw.toString(Charsets.UTF_8))
            assertEquals(1, reply.getInt("version"))
            assertEquals("ok", reply.getString("status"))
            return reply.getJSONObject("data")
        }
        override fun close() {
            val owned = handle
            handle = 0
            if (owned > 0) NativeWorkspace.close(owned)
        }
    }
    private fun <T> read(action: (Reader) -> T): T = runBlocking(Dispatchers.IO) {
        Reader(database()).use(action)
    }
    private fun scope(story: String, branch: String) = JSONObject().put("story", story).put("branch", branch)
    private fun view(reader: Reader, story: String, branch: String, head: Long): JSONObject {
        val expected = scope(story, branch)
        val session = reader.data(JSONObject().put("op", "resume").put("scope", expected)).getString("session")
        var primary: Throwable? = null
        try {
            val result = reader.data(JSONObject().put("op", "play_snapshot").put("session", session)
                .put("scope", expected).put("expected_revision", head))
            assertEquals(setOf("scope", "revision", "rules", "player", "inventory", "receipts"), result.keys().asSequence().toSet())
            assertEquals(canonical(expected), canonical(result.getJSONObject("scope")))
            assertEquals(head, result.getLong("revision"))
            val player = result.getJSONObject("player")
            assertEquals("player", player.getString("observer"))
            assertEquals(head, player.getLong("revision"))
            assertEquals(canonical(expected), canonical(player.getJSONObject("scope")))
            assertEquals(head, result.getJSONArray("receipts").length().toLong())
            return result
        } catch (failure: Throwable) { primary = failure; throw failure }
        finally {
            try { reader.data(JSONObject().put("op", "close").put("session", session).put("scope", expected)) }
            catch (cleanup: Throwable) { primary?.addSuppressed(cleanup) ?: throw cleanup }
        }
    }
    private fun library(): Library = read { reader ->
        val workspace = reader.data(JSONObject().put("op", "workspace"))
        val rows = workspace.getJSONArray("stories")
        check(rows.length() <= 16) // Refuse unexpected workload rather than silently skipping prior stories.
        val roots = linkedMapOf<String, String>()
        val catalogs = linkedMapOf<String, String>()
        val views = linkedMapOf<String, String>()
        for (index in 0 until rows.length()) {
            val row = rows.getJSONObject(index)
            val story = row.getJSONObject("scope").getString("story")
            check(roots.put(story, canonical(row)) == null)
            val catalog = reader.data(JSONObject().put("op", "branches").put("story", story))
            catalogs[story] = canonical(catalog)
            val branches = catalog.getJSONArray("branches")
            check(branches.length() in 1..256)
            for (branchIndex in 0 until branches.length()) {
                val branch = branches.getJSONObject(branchIndex)
                if (branch.getBoolean("retired")) continue
                val branchId = branch.getJSONObject("scope").getString("branch")
                check(views.size < 32)
                check(views.put("$story/$branchId", canonical(view(reader, story, branchId, branch.getLong("revision")))) == null)
            }
        }
        Library(canonical(workspace), roots, catalogs, views)
    }
    private fun unchangedPrior(before: Library, after: Library) {
        for ((key, value) in before.rows) assertEquals(value, after.rows[key])
        for ((key, value) in before.catalogs) assertEquals(value, after.catalogs[key])
        for ((key, value) in before.views) assertEquals(value, after.views[key])
    }

    /** Append one real native baseline for a meaningful unsent draft, without deleting earlier stories. */
    private fun baseline(): SavedStory = read { reader ->
        val created = reader.data(JSONObject().put("op", "create").put("seed", "lantern-quay-v1"))
        val session = created.getString("session")
        try {
            val selected = created.getJSONObject("scope")
            val story = selected.getString("story")
            val row = reader.data(JSONObject().put("op", "workspace")).getJSONArray("stories").let { rows ->
                (0 until rows.length()).map { rows.getJSONObject(it) }
                    .single { it.getJSONObject("scope").getString("story") == story }
            }
            SavedStory(story, selected.getString("branch"), row.getString("title"), row.getLong("revision"))
        } finally { reader.data(JSONObject().put("op", "close").put("session", session).put("scope", created.getJSONObject("scope"))) }
    }
    private fun <T> activity(action: () -> T): T {
        database() // Profile/path refusal precedes any Activity launch.
        val context = InstrumentationRegistry.getInstrumentation().targetContext
        val scenario = ActivityScenario.launch<MainActivity>(Intent(context, MainActivity::class.java))
        var primary: Throwable? = null
        try {
            scenario.onActivity {
                assertNotNull(it.constructedWorkspaceTransport)
                model = ViewModelProvider(it)[ShellViewModel::class.java]
            }
            settled()
            return action()
        } catch (failure: Throwable) { primary = failure; throw failure }
        finally {
            try { scenario.close() }
            catch (cleanup: Throwable) { primary?.addSuppressed(cleanup) ?: throw cleanup }
            // Requests ordinary Activity/VM adapter close; this is not joined-drain proof.
        }
    }
    private fun settled() {
        compose.waitUntil(15_000) { model.state.value.let { it.persistent && !it.busy && !it.creationActive } }
        compose.waitForIdle()
        assertFalse(model.state.value.recoveryRequired)
    }
    private fun tag(name: String): SemanticsNodeInteraction {
        compose.onNodeWithTag("story-list").performScrollToNode(hasTestTag(name))
        return compose.onNodeWithTag(name)
    }
    private fun select(story: SavedStory) {
        tag("saved-library").performClick()
        compose.onNodeWithTag("saved-story-${story.story}").performScrollTo().performClick()
        settled()
        assertEquals(story, model.state.value.selectedStory)
        assertEquals(TextProvider.SCRIPTED, model.state.value.textProvider)
    }
    private fun review(): StoryCreationRequest {
        tag("reset-demo").assertIsEnabled().performClick()
        compose.waitUntil(15_000) { model.creation.value.let { it.visible && !it.busy && it.review != null } }
        compose.waitForIdle()
        assertTrue(model.state.value.creationActive)
        compose.onNodeWithTag("story-creation-dialog").assertIsDisplayed()
        compose.onNodeWithText("Start a story").assertIsDisplayed()
        return checkNotNull(model.creation.value.review) // Observation only; consent always comes from real UI.
    }
    private fun create(title: String, previousIds: Set<String>): SavedStory {
        review()
        compose.onNodeWithTag("story-creation-title").performScrollTo().performTextReplacement(title)
        compose.waitForIdle()
        assertEquals(title, model.creation.value.review?.title)
        compose.onNodeWithTag("story-creation-confirm").performScrollTo().assertIsEnabled().performClick()
        settled()
        compose.onNodeWithTag("story-creation-dialog").assertDoesNotExist()
        val selected = checkNotNull(model.state.value.selectedStory)
        assertFalse(previousIds.contains(selected.story))
        assertEquals("main", selected.branch)
        assertEquals(title, selected.title)
        assertEquals(0L, selected.revision)
        assertEquals(0L, model.state.value.revision)
        assertTrue(model.state.value.messages.isEmpty())
        assertEquals(TextProvider.SCRIPTED, model.state.value.textProvider)
        return selected
    }

    @Test fun actualStarterReviewCancelPreservesLibraryEligibleViewsSelectionAndDraft() {
        val earlier = library()
        val baseline = baseline()
        val prepared = library()
        unchangedPrior(earlier, prepared)
        assertEquals(earlier.rows.keys + baseline.story, prepared.rows.keys)
        activity {
            select(baseline)
            tag("play-kind-dialogue").performClick()
            tag("play-input").performTextReplacement(DRAFT)
            val before = model.state.value
            val accepted = library()
            val preview = review()
            assertEquals("lantern-quay-v1", preview.preview.template)
            assertEquals("fantasy_v1", preview.preview.profile)
            assertEquals(accepted, library()) // Preview alone must create neither a story nor a turn.
            compose.onNodeWithTag("story-creation-title").performScrollTo().performTextReplacement("SYNTHETIC cancelled title")
            compose.onNodeWithTag("story-creation-cancel").performClick()
            settled()
            assertFalse(model.creation.value.visible)
            assertEquals(before.selectedStory, model.state.value.selectedStory)
            assertEquals(before.stories, model.state.value.stories)
            assertEquals(before.timelines, model.state.value.timelines)
            assertEquals(before.revision, model.state.value.revision)
            assertEquals(before.messages, model.state.value.messages)
            assertEquals(before.potionOwner, model.state.value.potionOwner)
            tag("play-kind-dialogue").assertIsSelected()
            tag("play-input").assert(hasText(DRAFT))
            assertEquals(accepted, library())
        }
        assertEquals(prepared, library()) // A fresh native Host reads the same accepted data after Activity close.
    }

    @Test fun actualNamedCreationGiftAndSecondCreationPreserveIndependentHistoryOnNativeReopen() {
        val before = library()
        val completedLibrary = activity {
            val a = create(TITLE_A, before.rows.keys)
            val afterA = library()
            unchangedPrior(before, afterA)
            assertEquals(before.rows.keys + a.story, afterA.rows.keys)
            val freshA = JSONObject(afterA.views.getValue("${a.story}/${a.branch}"))
            assertEquals(0, freshA.getJSONArray("receipts").length())
            assertTrue(freshA.getJSONObject("inventory").has("potion"))
            tag("play-example").assertIsEnabled().performClick()
            tag("play-input").assert(hasText(GIFT))
            tag("play-send").assertIsEnabled().performClick()
            compose.waitUntil(15_000) { model.state.value.let { !it.busy && it.revision == 1L } }
            settled()
            assertEquals(a.story, model.state.value.selectedStory?.story)
            val afterGift = library()
            unchangedPrior(before, afterGift)
            val aView = JSONObject(afterGift.views.getValue("${a.story}/${a.branch}"))
            assertEquals(1L, aView.getLong("revision"))
            assertFalse(aView.getJSONObject("inventory").has("potion"))
            val receipts = aView.getJSONArray("receipts")
            assertEquals(1, receipts.length())
            val request = receipts.getJSONObject(0).getJSONObject("request")
            assertEquals(canonical(scope(a.story, a.branch)), canonical(request.getJSONObject("scope")))
            assertEquals(0L, request.getLong("expected_revision"))
            assertEquals("free_text", request.getJSONObject("intent").getString("kind"))
            assertEquals("action", request.getJSONObject("intent").getJSONObject("value").getString("kind"))
            assertEquals(GIFT, request.getJSONObject("intent").getJSONObject("value").getString("text"))
            val b = create(TITLE_B, afterGift.rows.keys)
            assertNotEquals(a.story, b.story)
            assertNotEquals(a.title, b.title)
            val completed = library()
            unchangedPrior(afterGift, completed) // Includes the entire original A1 player/receipt view.
            assertEquals(before.rows.keys + setOf(a.story, b.story), completed.rows.keys)
            val bView = JSONObject(completed.views.getValue("${b.story}/${b.branch}"))
            assertEquals(0, bView.getJSONArray("receipts").length())
            assertTrue(bView.getJSONObject("inventory").has("potion"))
            tag("play-input").assert(hasText(""))
            completed
        }
        assertEquals(completedLibrary, library()) // Fresh native open; no claim of OS death or app-adapter join.
    }

    private fun canonical(value: Any?): String = when (value) {
        is JSONObject -> value.keys().asSequence().toList().sorted().joinToString(",", "{", "}") {
            JSONObject.quote(it) + ":" + canonical(value.get(it))
        }
        is JSONArray -> (0 until value.length()).joinToString(",", "[", "]") { canonical(value.get(it)) }
        is String -> JSONObject.quote(value)
        null, JSONObject.NULL -> "null"
        else -> value.toString()
    }
}

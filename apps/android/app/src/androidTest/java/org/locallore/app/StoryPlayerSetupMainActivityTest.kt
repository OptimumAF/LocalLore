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
import org.json.JSONObject
import org.junit.Assert.*
import org.junit.Rule
import org.junit.Test
import org.junit.runner.RunWith

/** Actual UI/JNI/Rust setup. Ordinary reopening is separate from OS death or joined-drain proof. */
@RunWith(AndroidJUnit4::class)
class StoryPlayerSetupMainActivityTest {
    @get:Rule val compose = createEmptyComposeRule()
    private lateinit var model: ShellViewModel
    private fun context() = InstrumentationRegistry.getInstrumentation().targetContext.also {
        assertEquals("org.locallore.app.draftprocessverify", it.packageName)
        assertTrue(BuildConfig.INPUT_PROCESS_VERIFICATION)
    }
    private fun activity(action: () -> Unit) {
        val app = context()
        val scenario = ActivityScenario.launch<MainActivity>(Intent(app, MainActivity::class.java))
        try {
            scenario.onActivity { model = ViewModelProvider(it)[ShellViewModel::class.java] }
            settled(); action()
        } finally { scenario.close() }
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
    private fun review() {
        tag("reset-demo").assertIsEnabled().performClick()
        compose.waitUntil(15_000) { model.creation.value.let { it.visible && !it.busy && it.review != null } }
        val preview = model.creation.value.review!!.preview
        assertEquals(DEFAULT_STORY_TEMPLATE, preview.template)
        assertNotNull(preview.playerSetup)
        assertEquals(preview.playerSetup!!.playerName, model.creation.value.playerNameDraft)
    }
    private fun editAndReview(name: String) {
        val before = model.creation.value.review!!
        compose.onNodeWithTag("story-player-name").performScrollTo().performTextReplacement(name)
        compose.waitForIdle()
        assertEquals(name, model.creation.value.playerNameDraft)
        compose.onNodeWithTag("story-creation-confirm").performScrollTo().assertIsNotEnabled()
        compose.onNodeWithTag("story-player-review").performScrollTo().assertIsEnabled().performClick()
        compose.waitUntil(15_000) { model.creation.value.let { !it.busy && it.review?.preview?.playerSetup?.playerName == name } }
        val after = model.creation.value.review!!
        val oldSetup = before.preview.playerSetup!!
        val newSetup = after.preview.playerSetup!!
        assertEquals(before.creationId, after.creationId)
        assertEquals(before.title, after.title)
        assertEquals(oldSetup.templateSha256, newSetup.templateSha256)
        assertNotEquals(oldSetup.setupSha256, newSetup.setupSha256)
        compose.onNodeWithText("Player: $name").performScrollTo().assertIsDisplayed()
        compose.onNodeWithTag("story-creation-confirm").performScrollTo().assertIsEnabled()
    }
    private fun chooseHarbor(expectedName: String? = null) {
        compose.onNodeWithTag("story-template-bracken-harbor-v1").performScrollTo().assertIsEnabled().performClick()
        compose.waitUntil(15_000) { model.creation.value.let { !it.busy && it.review?.preview?.template == "bracken-harbor-v1" } }
        val setup = model.creation.value.review!!.preview.playerSetup!!
        if (expectedName != null) assertEquals(expectedName, setup.playerName)
        assertEquals(setup.playerName, model.creation.value.playerNameDraft)
    }
    private fun create(title: String): SavedStory {
        compose.onNodeWithTag("story-creation-title").performScrollTo().performTextReplacement(title)
        compose.onNodeWithTag("story-creation-confirm").performScrollTo().assertIsEnabled().performClick()
        settled()
        return checkNotNull(model.state.value.selectedStory).also {
            assertEquals(title, it.title); assertEquals("main", it.branch); assertEquals(0L, it.revision)
            assertEquals(0L, model.state.value.revision); assertTrue(model.state.value.messages.isEmpty())
        }
    }
    private fun select(story: SavedStory) {
        tag("saved-library").performClick()
        compose.onNodeWithTag("saved-story-${story.story}").performScrollTo().performClick()
        settled(); assertEquals(story, model.state.value.selectedStory)
    }
    /** A new finite native reader over this isolated app's exact ordinary database. */
    private fun snapshot(story: SavedStory): JSONObject = runBlocking(Dispatchers.IO) {
        val base = context().noBackupFilesDir.canonicalFile
        val directory = File(base, "workspace-v1")
        check(Files.isDirectory(directory.toPath(), LinkOption.NOFOLLOW_LINKS) && !Files.isSymbolicLink(directory.toPath()))
        check(directory.canonicalFile.parentFile == base)
        val database = File(directory, "stories.sqlite3")
        check(Files.isRegularFile(database.toPath(), LinkOption.NOFOLLOW_LINKS) && !Files.isSymbolicLink(database.toPath()))
        check(database.canonicalFile.parentFile == directory.canonicalFile)
        val handle = NativeWorkspace.open(database.absolutePath).also { check(it > 0) }
        var totalBytes = 0
        fun data(command: JSONObject): JSONObject {
            val input = JSONObject().put("version", 1).put("command", command).toString().toByteArray(Charsets.UTF_8)
            val bytes = NativeWorkspace.call(handle, input)
            check(bytes.size in 1..262_144)
            totalBytes += bytes.size; check(totalBytes <= 1_048_576)
            val reply = JSONObject(bytes.toString(Charsets.UTF_8))
            assertEquals(1, reply.getInt("version")); assertEquals("ok", reply.getString("status"))
            return reply.getJSONObject("data")
        }
        val scope = JSONObject().put("story", story.story).put("branch", story.branch)
        try {
            val session = data(JSONObject().put("op", "resume").put("scope", scope)).getString("session")
            try {
                data(JSONObject().put("op", "play_snapshot").put("session", session).put("scope", scope)
                    .put("expected_revision", story.revision)).also {
                    assertEquals(story.revision, it.getLong("revision"))
                    assertEquals(story.story, it.getJSONObject("scope").getString("story"))
                    assertEquals(story.branch, it.getJSONObject("scope").getString("branch"))
                    assertEquals(0, it.getJSONArray("receipts").length())
                }
            } finally { data(JSONObject().put("op", "close").put("session", session).put("scope", scope)) }
        } finally { NativeWorkspace.close(handle) }
    }
    private fun playerName(snapshot: JSONObject) = snapshot.getJSONObject("player").getJSONObject("self_state").getString("name")

    @Test fun customNameReviewCancelPreservesTheLibraryAndDraft() {
        activity {
            check(model.state.value.stories.size <= 16)
            review()
            val baseline = create("SYNTHETIC player-name cancel baseline")
            tag("play-kind-dialogue").performClick()
            val draft = "SYNTHETIC unsent name-review dialogue.\nKeep this scope."
            tag("play-input").performTextReplacement(draft)
            val before = model.state.value
            val nativeBefore = snapshot(baseline).toString()
            review(); editAndReview("SYNTHETIC Marin")
            chooseHarbor("SYNTHETIC Marin")
            assertEquals(before.stories, model.state.value.stories)
            compose.onNodeWithTag("story-creation-cancel").performClick(); settled()
            assertEquals(before.selectedStory, model.state.value.selectedStory)
            assertEquals(before.stories, model.state.value.stories)
            assertEquals(before.timelines, model.state.value.timelines)
            assertEquals(before.revision, model.state.value.revision)
            assertEquals(before.messages, model.state.value.messages)
            tag("play-kind-dialogue").assertIsSelected()
            tag("play-input").assert(hasText(draft))
            assertEquals(nativeBefore, snapshot(baseline).toString())
        }
    }

    @Test fun configuredCreationAndOrdinaryReopenRetainTheNativePlayerName() {
        val firstName = "SYNTHETIC Marin e\u0301"
        val secondName = "SYNTHETIC Vale"
        lateinit var first: SavedStory
        lateinit var second: SavedStory
        lateinit var firstView: String
        lateinit var secondView: String
        activity {
            check(model.state.value.stories.size <= 16)
            review(); editAndReview(firstName)
            first = create("SYNTHETIC configured fantasy player")
            val a = snapshot(first)
            assertEquals(firstName, playerName(a)); assertEquals("fantasy_v1", a.getString("rules"))
            firstView = a.toString()
            review(); chooseHarbor(); editAndReview(secondName)
            second = create("SYNTHETIC configured narrative player")
            assertNotEquals(first.story, second.story)
            val b = snapshot(second)
            assertEquals(secondName, playerName(b)); assertEquals("narrative_v1", b.getString("rules"))
            secondView = b.toString()
            assertEquals(firstView, snapshot(first).toString())
        }
        // These reads allocate fresh native Hosts after Activity close; no saved Kotlin name is trusted.
        assertEquals(firstView, snapshot(first).toString())
        assertEquals(secondView, snapshot(second).toString())
        activity {
            select(first); assertEquals(firstName, playerName(snapshot(first)))
            assertEquals("fantasy_v1", model.state.value.rulesProfile)
            select(second); assertEquals(secondName, playerName(snapshot(second)))
            assertEquals("narrative_v1", model.state.value.rulesProfile)
            assertEquals(firstView, snapshot(first).toString())
            assertEquals(secondView, snapshot(second).toString())
        }
    }
}

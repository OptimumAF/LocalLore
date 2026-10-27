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
import java.security.MessageDigest
import java.util.Locale
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.runBlocking
import org.json.JSONObject
import org.junit.Assert.*
import org.junit.Rule
import org.junit.Test
import org.junit.runner.RunWith

/** Actual creation/preferences and ordinary reopen; not OS death, joined drain or model quality. */
@RunWith(AndroidJUnit4::class)
class StoryPresentationMainActivityTest {
    @get:Rule val compose = createEmptyComposeRule()
    private lateinit var model: ShellViewModel
    private data class Views(val player: JSONObject, val presentation: JSONObject)
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
        compose.waitForIdle(); assertFalse(model.state.value.recoveryRequired)
    }
    private fun tag(name: String): SemanticsNodeInteraction {
        compose.onNodeWithTag("story-list").performScrollToNode(hasTestTag(name))
        return compose.onNodeWithTag(name)
    }
    private fun review() {
        tag("reset-demo").assertIsEnabled().performClick()
        compose.waitUntil(15_000) { model.creation.value.let { it.visible && !it.busy && it.review != null } }
        assertEquals(DEFAULT_STORY_TEMPLATE, model.creation.value.review!!.preview.template)
        assertEquals(StoryPresentation(), model.creation.value.review!!.preview.presentation)
    }
    private fun configure(name: String, settings: StoryPresentation) {
        val before = model.creation.value.review!!
        compose.onNodeWithTag("story-player-name").performScrollTo().performTextReplacement(name)
        compose.onNodeWithTag("story-tone-${settings.tone}").performScrollTo().assertIsEnabled().performClick()
        compose.onNodeWithTag("story-excluded-phrases").performScrollTo().performTextReplacement(settings.excludedPhrases.joinToString("\n"))
        compose.waitForIdle()
        assertEquals(name, model.creation.value.playerNameDraft)
        assertEquals(settings.excludedPhrases.joinToString("\n"), model.creation.value.excludedPhrasesDraft)
        compose.onNodeWithTag("story-creation-confirm").performScrollTo().assertIsNotEnabled()
        compose.onNodeWithTag("story-player-review").performScrollTo().assertIsEnabled().performClick()
        compose.waitUntil(15_000) { model.creation.value.let { !it.busy && it.review?.preview?.presentation == settings } }
        val accepted = model.creation.value.review!!
        val acceptedSetup = accepted.preview.playerSetup!!
        assertEquals(name, acceptedSetup.playerName)
        assertEquals(before.creationId, accepted.creationId); assertEquals(before.title, accepted.title)
        assertEquals(before.preview.seedSha256, accepted.preview.seedSha256)
        assertNotEquals(before.preview.playerSetup!!.setupSha256, acceptedSetup.setupSha256)
        compose.onNodeWithTag("story-creation-confirm").performScrollTo().assertIsEnabled()
    }
    private fun harbor(settings: StoryPresentation, name: String) {
        compose.onNodeWithTag("story-template-bracken-harbor-v1").performScrollTo().assertIsEnabled().performClick()
        compose.waitUntil(15_000) { model.creation.value.let { !it.busy && it.review?.preview?.template == "bracken-harbor-v1" } }
        val accepted = model.creation.value.review!!.preview
        assertEquals(settings, accepted.presentation); assertEquals(name, accepted.playerSetup!!.playerName)
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
    /** Fresh finite native Host: dedicated public preference view, never full Seed/private truth. */
    private fun views(story: SavedStory): Views = runBlocking(Dispatchers.IO) {
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
            check(bytes.size in 1..262_144); totalBytes += bytes.size; check(totalBytes <= 1_048_576)
            val reply = JSONObject(bytes.toString(Charsets.UTF_8))
            assertEquals(1, reply.getInt("version")); assertEquals("ok", reply.getString("status"))
            return reply.getJSONObject("data")
        }
        val scope = JSONObject().put("story", story.story).put("branch", story.branch)
        try {
            val session = data(JSONObject().put("op", "resume").put("scope", scope)).getString("session")
            try {
                val player = data(JSONObject().put("op", "play_snapshot").put("session", session).put("scope", scope)
                    .put("expected_revision", story.revision))
                assertEquals(setOf("scope", "revision", "rules", "player", "inventory", "receipts"), player.keys().asSequence().toSet())
                check(story.revision in 0L..1L) // This fixed synthetic control only creates A0 or one accepted A1.
                val receipts = player.getJSONArray("receipts")
                assertEquals(story.revision, player.getLong("revision"))
                assertEquals(story.revision, receipts.length().toLong())
                if (story.revision == 1L) {
                    val receipt = receipts.getJSONObject(0)
                    val turn = receipt.getJSONObject("request").getString("turn")
                    val status = data(JSONObject().put("op", "turn_status").put("session", session)
                        .put("scope", scope).put("turn", turn))
                    assertEquals(setOf("turn", "scope", "expected_revision", "phase", "error", "receipt"), status.keys().asSequence().toSet())
                    assertEquals("committed", status.getString("phase")); assertEquals(turn, status.getString("turn"))
                    assertEquals(0L, status.getLong("expected_revision")); assertTrue(status.isNull("error"))
                    assertEquals(story.story, status.getJSONObject("scope").getString("story"))
                    assertEquals(story.branch, status.getJSONObject("scope").getString("branch"))
                    assertEquals(receipt.toString(), status.getJSONObject("receipt").toString())
                }
                val presentation = data(JSONObject().put("op", "story_presentation_view").put("session", session).put("scope", scope)
                    .put("expected_revision", story.revision))
                assertEquals(setOf("version", "scope", "revision", "presentation"), presentation.keys().asSequence().toSet())
                assertEquals(1, presentation.getInt("version")); assertEquals(story.revision, presentation.getLong("revision"))
                for (value in listOf(player, presentation)) {
                    assertEquals(story.story, value.getJSONObject("scope").getString("story"))
                    assertEquals(story.branch, value.getJSONObject("scope").getString("branch"))
                }
                assertEquals(setOf("version", "tone", "excluded_phrases"), presentation.getJSONObject("presentation").keys().asSequence().toSet())
                Views(player, presentation)
            } finally { data(JSONObject().put("op", "close").put("session", session).put("scope", scope)) }
        } finally { NativeWorkspace.close(handle) }
    }
    private fun settings(view: Views): StoryPresentation {
        val value = view.presentation.getJSONObject("presentation")
        assertEquals(1, value.getInt("version"))
        val phrases = value.getJSONArray("excluded_phrases")
        return StoryPresentation(value.getString("tone"), (0 until phrases.length()).map { phrases.getString(it) })
    }
    private fun name(view: Views) = view.player.getJSONObject("player").getJSONObject("self_state").getString("name")
    private fun assertUnchanged(expected: Views, actual: Views) {
        assertEquals(expected.player.toString(), actual.player.toString())
        assertEquals(expected.presentation.toString(), actual.presentation.toString())
    }

    @Test fun presentationReviewCancelPreservesTheSelectedLibraryAndDraft() {
        activity {
            check(model.state.value.stories.size <= 16)
            review(); val baseline = create("SYNTHETIC narration cancel baseline")
            tag("play-kind-dialogue").performClick()
            val draft = "SYNTHETIC unsent narration-review dialogue.\nKeep the selected story."
            tag("play-input").performTextReplacement(draft)
            val before = model.state.value
            val accepted = views(baseline)
            assertEquals(StoryPresentation(), settings(accepted))
            val changed = StoryPresentation("warm", listOf("Red fog", "storm bell"))
            review(); configure("SYNTHETIC Marin", changed); harbor(changed, "SYNTHETIC Marin")
            assertEquals(before.stories, model.state.value.stories)
            compose.onNodeWithTag("story-creation-cancel").performClick(); settled()
            assertEquals(before.selectedStory, model.state.value.selectedStory)
            assertEquals(before.stories, model.state.value.stories); assertEquals(before.timelines, model.state.value.timelines)
            assertEquals(before.revision, model.state.value.revision); assertEquals(before.messages, model.state.value.messages)
            tag("play-kind-dialogue").assertIsSelected(); tag("play-input").assert(hasText(draft))
            assertUnchanged(accepted, views(baseline))
        }
    }

    @Test fun presentedCreationRetainsToneAndPhrasesOnNativeReopen() {
        val firstSettings = StoryPresentation("warm", listOf("spider"))
        val secondSettings = StoryPresentation("brisk", listOf("Glass rain", "amber hush"))
        lateinit var first: SavedStory
        lateinit var second: SavedStory
        lateinit var firstView: Views
        lateinit var secondView: Views
        activity {
            check(model.state.value.stories.size <= 16)
            review(); configure("SYNTHETIC Marin", firstSettings)
            first = create("SYNTHETIC warm narration story")
            firstView = views(first)
            assertEquals(firstSettings, settings(firstView)); assertEquals("SYNTHETIC Marin", name(firstView))
            assertEquals("fantasy_v1", firstView.player.getString("rules"))
            review(); configure("SYNTHETIC Rhea", secondSettings); harbor(secondSettings, "SYNTHETIC Rhea")
            second = create("SYNTHETIC brisk narration story")
            secondView = views(second)
            assertNotEquals(first.story, second.story)
            assertEquals(secondSettings, settings(secondView)); assertEquals("SYNTHETIC Rhea", name(secondView))
            assertEquals("narrative_v1", secondView.player.getString("rules"))
            assertUnchanged(firstView, views(first))
        }
        assertUnchanged(firstView, views(first)); assertUnchanged(secondView, views(second))
        activity {
            select(first); assertUnchanged(firstView, views(first))
            assertTrue(firstView.player.getJSONObject("inventory").has("potion"))
            assertEquals(TextProvider.SCRIPTED, model.state.value.textProvider)
            val gift = "I give my last potion to Mira."
            tag("play-example").assertIsEnabled().performClick()
            tag("play-input").assert(hasText(gift))
            tag("play-send").assertIsEnabled().performClick()
            compose.waitUntil(15_000) { model.state.value.let { !it.busy && it.revision == 1L } }
            settled()
            val advanced = checkNotNull(model.state.value.selectedStory)
            assertEquals(first.story, advanced.story); assertEquals(first.branch, advanced.branch)
            assertEquals(first.title, advanced.title); assertEquals(1L, advanced.revision)
            first = advanced
            firstView = views(first)
            assertEquals(firstSettings, settings(firstView)); assertEquals("SYNTHETIC Marin", name(firstView))
            assertFalse(firstView.player.getJSONObject("inventory").has("potion"))
            val receipt = firstView.player.getJSONArray("receipts").getJSONObject(0)
            val request = receipt.getJSONObject("request")
            assertEquals(first.story, request.getJSONObject("scope").getString("story"))
            assertEquals(first.branch, request.getJSONObject("scope").getString("branch"))
            assertEquals(0L, request.getLong("expected_revision"))
            val intent = request.getJSONObject("intent")
            assertEquals("free_text", intent.getString("kind"))
            assertEquals("action", intent.getJSONObject("value").getString("kind"))
            assertEquals(gift, intent.getJSONObject("value").getString("text"))
            val events = receipt.getJSONArray("events")
            val transfers = (0 until events.length()).map { events.getJSONObject(it).getJSONObject("outcome") }
                .filter { it.getString("effect") == "given" }
            assertEquals(1, transfers.size)
            assertEquals("potion", transfers.single().getString("item"))
            assertEquals("player", transfers.single().getString("from")); assertEquals("mira", transfers.single().getString("to"))
            assertEquals(1, transfers.single().getInt("quantity"))
            val narration = receipt.getString("narration")
            assertTrue(narration.isNotBlank()); assertFalse(narration.lowercase(Locale.ROOT).contains("spider"))
            val play = receipt.getJSONObject("play")
            assertEquals(2, play.getInt("version"))
            assertEquals("locallore-play-v2.7-story-presentation-v1", play.getString("prompt_version"))
            assertEquals("grounded-prose-v2.3-story-presentation-v1", play.getString("policy"))
            val binding = play.getJSONObject("story_presentation")
            assertEquals(setOf("version", "presentation_sha256"), binding.keys().asSequence().toSet())
            assertEquals(1, binding.getInt("version"))
            // Exact reviewed ASCII fixture in the native StoryPresentationV1 serialization order.
            val expectedBinding = MessageDigest.getInstance("SHA-256")
                .digest("{\"version\":1,\"tone\":\"warm\",\"excluded_phrases\":[\"spider\"]}".toByteArray(Charsets.UTF_8))
                .joinToString("") { "%02x".format(it) }
            assertEquals(expectedBinding, binding.getString("presentation_sha256"))
            select(second); assertUnchanged(secondView, views(second))
        }
        // A1 reads restore and validate the original committed receipt through another native Host.
        assertUnchanged(firstView, views(first)); assertUnchanged(secondView, views(second))
        activity {
            select(first); assertUnchanged(firstView, views(first))
            assertEquals(1L, model.state.value.revision)
            assertFalse(views(first).player.getJSONObject("inventory").has("potion"))
            select(second); assertUnchanged(secondView, views(second))
        }
    }
}

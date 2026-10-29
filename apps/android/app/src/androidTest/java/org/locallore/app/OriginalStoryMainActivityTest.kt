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

/** Production Compose→gateway→Rust with a labelled scripted provider; no real-model/OS-death claim. */
@RunWith(AndroidJUnit4::class)
class OriginalStoryMainActivityTest {
    @get:Rule val compose=createEmptyComposeRule()
    private lateinit var model: ShellViewModel
    private fun context()=InstrumentationRegistry.getInstrumentation().targetContext.also {
        assertEquals("org.locallore.app.draftprocessverify",it.packageName); assertTrue(BuildConfig.INPUT_PROCESS_VERIFICATION) }
    private fun activity(action: ()->Unit) {
        val scenario=ActivityScenario.launch<MainActivity>(Intent(context(),MainActivity::class.java))
        try { scenario.onActivity { model=ViewModelProvider(it)[ShellViewModel::class.java] }; settled(); action() }
        finally { scenario.close() }
    }
    private fun settled() {
        try { compose.waitUntil(15000) { model.state.value.let { it.persistent && !it.busy && !it.creationActive } } }
        catch(failure: ComposeTimeoutException) {
            val s=model.state.value; val c=model.creation.value; val original=c.original
            throw AssertionError("Story handoff did not settle: persistent=${s.persistent}, busy=${s.busy}, creationActive=${s.creationActive}, " +
                "recoveryRequired=${s.recoveryRequired}, originalVisible=${original!=null}, originalBusy=${original?.busy}, " +
                "originalCreating=${original?.creating}, originalClosing=${original?.closing}",failure)
        }
        compose.waitForIdle(); assertFalse(model.state.value.recoveryRequired)
    }
    private fun tag(name: String): SemanticsNodeInteraction {
        compose.onNodeWithTag("story-list").performScrollToNode(hasTestTag(name)); return compose.onNodeWithTag(name)
    }
    private fun openOriginal() {
        tag("reset-demo").assertIsEnabled().performClick()
        compose.waitUntil(15000) { model.creation.value.let { it.visible && !it.busy && it.review!=null } }
        compose.onNodeWithTag("story-creation-original").performScrollTo().assertIsEnabled().performClick()
        compose.waitUntil(5000) { model.creation.value.original!=null }
        assertEquals("scripted",model.creation.value.original!!.provider)
        compose.onNodeWithText("synthetic scripted provider",substring=true).performScrollTo().assertIsDisplayed()
    }
    private fun generate() {
        openOriginal()
        compose.onNodeWithTag("original-premise").performScrollTo().performTextReplacement("SYNTHETIC An artisan explores the Copper Orchard at dawn.")
        compose.onNodeWithTag("original-player-name").performScrollTo().performTextReplacement("SYNTHETIC Iris")
        compose.onNodeWithTag("original-player-description").performScrollTo().performTextReplacement("An observant artisan.")
        compose.onNodeWithText("Add cast hint").performScrollTo().performClick()
        compose.onNodeWithTag("original-cast-0-name").performScrollTo().performTextReplacement("Sel")
        compose.onNodeWithTag("original-cast-0-description").performScrollTo().performTextReplacement("A patient orchard keeper.")
        val before=model.state.value
        compose.onNodeWithTag("original-generate").performScrollTo().assertIsEnabled().performClick()
        compose.waitUntil(15000) { model.creation.value.original.let { it!=null && !it.busy && it.proposal!=null } }
        val draft=model.creation.value.original!!
        assertEquals("Sel",draft.proposal!!.characters.single().name)
        assertEquals(before.stories,model.state.value.stories); assertEquals(before.selectedStory,model.state.value.selectedStory)
        assertNull(draft.review); compose.onNodeWithTag("original-create").assertDoesNotExist()
    }
    private fun create(title: String): SavedStory {
        compose.onNodeWithTag("original-title").performScrollTo().performTextReplacement(title)
        compose.onNodeWithTag("original-review").performScrollTo().assertIsEnabled().performClick()
        compose.waitUntil(15000) { model.creation.value.original.let { it!=null && !it.busy && it.review!=null } }
        val review=model.creation.value.original!!.review!!
        assertEquals(title,review.title); assertTrue(review.details.isNotEmpty())
        compose.onNodeWithTag("original-create").performScrollTo().assertIsEnabled().performClick(); settled()
        return checkNotNull(model.state.value.selectedStory).also {
            assertTrue(Regex("original-[0-9a-f]{32}").matches(it.story)); assertEquals("main",it.branch)
            assertEquals(title,it.title); assertEquals(0L,it.revision); assertTrue(model.state.value.messages.isEmpty()) }
    }
    private fun select(story: SavedStory) {
        tag("saved-library").performClick(); compose.onNodeWithTag("saved-story-${story.story}").performScrollTo().performClick(); settled()
        assertEquals(story,model.state.value.selectedStory)
    }
    private fun snapshot(story: SavedStory): JSONObject=runBlocking(Dispatchers.IO) {
        val base=context().noBackupFilesDir.canonicalFile
        val directory=File(base,"workspace-v1")
        check(Files.isDirectory(directory.toPath(),LinkOption.NOFOLLOW_LINKS) && !Files.isSymbolicLink(directory.toPath()))
        check(directory.canonicalFile.parentFile==base)
        val file=File(directory,"stories.sqlite3"); check(Files.isRegularFile(file.toPath(),LinkOption.NOFOLLOW_LINKS))
        check(!Files.isSymbolicLink(file.toPath()) && file.canonicalFile.parentFile==directory)
        val handle=NativeWorkspace.open(file.path).also { check(it>0) }
        fun data(command: JSONObject): JSONObject {
            val input=JSONObject().put("version",1).put("command",command).toString().toByteArray(Charsets.UTF_8); check(input.size<=24576)
            val raw=NativeWorkspace.call(handle,input); check(raw.size in 1..262144)
            val root=JSONObject(raw.toString(Charsets.UTF_8)); assertEquals(1,root.getInt("version"))
            assertEquals("Native ${command.optString("op")} error=${root.optString("error").take(64)}","ok",root.opt("status"))
            return root.getJSONObject("data")
        }
        val scope=JSONObject().put("story",story.story).put("branch",story.branch)
        try {
            val session=data(JSONObject().put("op","resume").put("scope",scope)).getString("session")
            val result=data(JSONObject().put("op","play_snapshot").put("session",session).put("scope",scope).put("expected_revision",story.revision))
            assertEquals(setOf("scope","revision","rules","player","inventory","receipts"),result.keys().asSequence().toSet())
            val actualScope=result.getJSONObject("scope")
            assertEquals(setOf("story","branch"),actualScope.keys().asSequence().toSet())
            assertEquals(story.story,actualScope.getString("story")); assertEquals(story.branch,actualScope.getString("branch"))
            assertEquals(story.revision,result.getLong("revision"))
            assertEquals("SYNTHETIC Iris",result.getJSONObject("player").getJSONObject("self_state").getString("name"))
            result
        } finally { NativeWorkspace.close(handle) }
    }
    @Test fun originalPremiseEditedWorldCreatesAndOrdinaryReopenRetainsPlayer() {
        lateinit var story: SavedStory; lateinit var accepted: String
        activity {
            generate()
            compose.onNodeWithTag("original-character-0-name").performScrollTo().performTextReplacement("Sera")
            compose.onNodeWithTag("original-location-0-description").performScrollTo().performTextReplacement("A quiet grove of copper-leafed trees.")
            compose.onNodeWithTag("original-fact-0").performScrollTo().performTextReplacement("A copper gate stands open.")
            compose.onNodeWithTag("original-belief-0").performScrollTo().performTextReplacement("The grove may be older than the town.")
            val edited=model.creation.value.original!!
            assertEquals("Sera",edited.input.cast.single().name); assertNull(edited.review)
            story=create("SYNTHETIC edited Copper Orchard"); accepted=snapshot(story).toString()
            val visible=snapshot(story).getJSONObject("player").getJSONObject("facts").toString()
            assertTrue(visible.contains("A copper gate stands open.")); assertTrue(visible.contains("Sera"))
            assertFalse(visible.contains("The grove may be older than the town."))
        }
        assertEquals(accepted,snapshot(story).toString())
        activity { select(story); assertEquals(accepted,snapshot(story).toString()); assertEquals("narrative_v1",model.state.value.rulesProfile) }
    }
    @Test fun cancelOriginalDraftPreservesCurrentScopeAndPlayerDraft() {
        activity {
            generate(); val baseline=create("SYNTHETIC original cancel baseline")
            tag("play-kind-dialogue").performClick()
            val draft="SYNTHETIC unsent original-story dialogue.\nKeep this draft."
            tag("play-input").performTextReplacement(draft)
            val before=model.state.value; val accepted=snapshot(baseline).toString()
            generate(); compose.onNodeWithTag("original-title").performScrollTo().performTextReplacement("SYNTHETIC cancelled original")
            compose.onNodeWithTag("original-cancel").performClick(); settled()
            assertEquals(before.selectedStory,model.state.value.selectedStory); assertEquals(before.stories,model.state.value.stories)
            assertEquals(before.messages,model.state.value.messages); assertEquals(before.revision,model.state.value.revision)
            tag("play-kind-dialogue").assertIsSelected(); tag("play-input").assert(hasText(draft))
            assertEquals(accepted,snapshot(baseline).toString())
        }
    }
    @Test fun createdOriginalStoryCanAcceptGeneratedTurnWithScopedReceipts() {
        lateinit var story: SavedStory; lateinit var accepted: String
        activity {
            generate(); story=create("SYNTHETIC original dialogue")
            val before=snapshot(story); assertEquals(0,before.getJSONArray("receipts").length())
            assertEquals(TextProvider.SCRIPTED,model.state.value.textProvider)
            tag("play-kind-dialogue").performClick(); val text="Hello, Sel."
            tag("play-input").performTextReplacement(text); tag("play-send").assertIsEnabled().performClick()
            compose.waitUntil(15000) { model.state.value.let { !it.busy && it.revision==1L } }; settled()
            story=checkNotNull(model.state.value.selectedStory); assertEquals(1L,story.revision)
            val after=snapshot(story); val receipts=after.getJSONArray("receipts"); assertEquals(1,receipts.length())
            val receipt=receipts.getJSONObject(0); val request=receipt.getJSONObject("request")
            assertEquals(story.story,request.getJSONObject("scope").getString("story")); assertEquals("main",request.getJSONObject("scope").getString("branch"))
            assertEquals(0L,request.getLong("expected_revision"))
            val intent=request.getJSONObject("intent"); assertEquals("free_text",intent.getString("kind"))
            assertEquals("dialogue",intent.getJSONObject("value").getString("kind")); assertEquals(text,intent.getJSONObject("value").getString("text"))
            assertTrue(receipt.getString("narration").isNotBlank()); assertTrue(receipt.getJSONArray("events").length()>0)
            val events=receipt.getJSONArray("events")
            val speech=(0 until events.length()).map { events.getJSONObject(it) }.single { it.getJSONObject("outcome").getString("effect")=="said" }
            val outcome=speech.getJSONObject("outcome"); assertEquals(text,outcome.getString("text"))
            val speaker=outcome.getString("speaker"); assertEquals(before.getJSONObject("player").getString("observer"),speaker)
            val audience=outcome.getJSONArray("audience"); assertEquals(1,audience.length())
            val recipient=audience.getString(0); assertNotEquals(speaker,recipient) // Native schema selected the actual original-world actor.
            val participants=speech.getJSONArray("participants")
            assertTrue((0 until participants.length()).map { participants.getString(it) }.containsAll(listOf(speaker,recipient)))
            assertEquals(before.getJSONObject("inventory").toString(),after.getJSONObject("inventory").toString())
            val player=after.getJSONObject("player"); assertEquals(before.getJSONObject("player").getJSONObject("facts").toString(),player.getJSONObject("facts").toString())
            assertTrue(player.getJSONArray("observations").length()>0)
            assertFalse(player.getJSONObject("facts").toString().contains(text)) // Dialogue is an observed statement, not world truth.
            accepted=after.toString()
        }
        assertEquals(accepted,snapshot(story).toString()); activity { select(story); assertEquals(accepted,snapshot(story).toString()) }
    }
}

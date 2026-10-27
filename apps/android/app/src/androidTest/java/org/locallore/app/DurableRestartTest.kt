/* Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0 */
package org.locallore.app

import android.os.Process
import androidx.compose.ui.test.*
import androidx.compose.ui.test.junit4.createAndroidComposeRule
import androidx.lifecycle.ViewModelProvider
import androidx.test.ext.junit.runners.AndroidJUnit4
import androidx.test.platform.app.InstrumentationRegistry
import org.json.JSONObject
import org.junit.Assert.*
import org.junit.Assume.assumeTrue
import org.junit.Before
import org.junit.Rule
import org.junit.Test
import org.junit.runner.RunWith
import java.io.File
import java.io.FileOutputStream
import java.nio.ByteBuffer
import java.security.MessageDigest
import java.util.Locale

/** Two explicit runner phases; the host stops this app between them. Never clears app data. */
@RunWith(AndroidJUnit4::class)
class DurableRestartTest {
    @get:Rule val compose = createAndroidComposeRule<MainActivity>()
    private lateinit var directory: File
    private fun model() = ViewModelProvider(compose.activity)[ShellViewModel::class.java]
    private fun idle() {
        compose.waitUntil(10_000) { !model().state.value.busy }
        compose.waitForIdle()
        assertFalse("Storage must open rather than silently fall back", model().state.value.recoveryRequired)
        assertTrue(model().state.value.persistent)
    }
    private fun tag(name: String): SemanticsNodeInteraction {
        compose.onNodeWithTag("story-list").performScrollToNode(hasTestTag(name))
        return compose.onNodeWithTag(name)
    }
    @Before fun explicitlyCoordinatedOnly() {
        val token = InstrumentationRegistry.getArguments().getString("localloreRestart")
        assumeTrue("Requires explicit two-phase restart runner", token != null && token.matches(Regex("[0-9a-f]{32}")))
        val parent = InstrumentationRegistry.getInstrumentation().targetContext.noBackupFilesDir.canonicalFile
        directory = File(parent, "synthetic-restart-$token")
        assertEquals(parent, directory.canonicalFile.parentFile)
        idle()
    }

    private fun digest(messages: List<SceneMessage>): String {
        val digest = MessageDigest.getInstance("SHA-256")
        messages.forEach { message ->
            val bytes = message.text.toByteArray(Charsets.UTF_8)
            digest.update(ByteBuffer.allocate(8).putLong(message.id).array())
            digest.update(if (message.isPlayer) 1.toByte() else 0.toByte())
            digest.update(ByteBuffer.allocate(4).putInt(bytes.size).array())
            digest.update(bytes)
        }
        return digest.digest().joinToString("") { String.format(Locale.ROOT, "%02x", it.toInt() and 0xff) }
    }
    private fun accepted() {
        val state = model().state.value
        assertEquals(1L, state.revision)
        assertEquals("Not in your inventory", state.potionOwner)
        assertEquals(2, state.messages.size)
        assertEquals("You give 1 potion to mira.", state.messages.single { !it.isPlayer }.text)
        tag("revision").assertTextEquals("Accepted revision · 1")
        tag("potion-owner").assertTextEquals("Healing potion · Not in your inventory")
    }
    private fun select(story: SavedStory) {
        tag("saved-library").performClick()
        compose.onNodeWithText("${story.title} · ${story.story} · revision ${story.revision}")
            .performScrollTo().performClick()
        idle()
        assertEquals(story.story, model().state.value.selectedStory?.story)
        assertEquals(story.branch, model().state.value.selectedStory?.branch)
    }

    @Test fun checkpointAcceptedStory() {
        assertTrue("Never overwrite another checkpoint", directory.mkdir())
        val count = model().state.value.stories.size
        compose.createStoryThroughMainReview(10_000); idle()
        assertEquals(count + 1, model().state.value.stories.size)
        assertEquals(0L, model().state.value.revision)
        tag("give-potion").performClick(); idle()
        accepted()
        val state = model().state.value
        val selected = checkNotNull(state.selectedStory)
        val database = File(checkNotNull(state.storageLocation)).canonicalFile
        val parent = InstrumentationRegistry.getInstrumentation().targetContext.noBackupFilesDir.canonicalFile
        assertTrue(database.isFile && database.toPath().startsWith(parent.toPath()))
        val record = JSONObject().put("version", 1).put("story", selected.story).put("branch", selected.branch)
            .put("revision", state.revision).put("digest", digest(state.messages)).put("messages", state.messages.size)
            .put("stories", state.stories.size).put("pid", Process.myPid()).put("process_start", Process.getStartElapsedRealtime())
        val partial = File(directory, "checkpoint.partial")
        val final = File(directory, "checkpoint.json")
        assertFalse(partial.exists()); assertFalse(final.exists())
        FileOutputStream(partial).use { output ->
            output.write(record.toString().toByteArray(Charsets.UTF_8)); output.fd.sync()
        }
        assertTrue(partial.renameTo(final))
        compose.activityRule.scenario.close()
        assertTrue(database.isFile)
    }

    @Test fun resumeAfterProcessStop() {
        assertTrue(directory.isDirectory)
        val file = File(directory, "checkpoint.json")
        val bytes = file.inputStream().use { input ->
            val buffer = ByteArray(8193)
            var total = 0
            while (total < buffer.size) {
                val count = input.read(buffer, total, buffer.size - total)
                if (count == -1) break
                total += count
            }
            assertTrue("Checkpoint is bounded", total <= 8192)
            buffer.copyOf(total)
        }
        val record = JSONObject(bytes.toString(Charsets.UTF_8))
        assertEquals(1, record.getInt("version"))
        assertTrue("Host must stop the old app process between phases",
            record.getInt("pid") != Process.myPid() || record.getLong("process_start") != Process.getStartElapsedRealtime())
        val saved = model().state.value.stories.single {
            it.story == record.getString("story") && it.branch == record.getString("branch")
        }
        select(saved)
        accepted()
        var state = model().state.value
        assertEquals(record.getLong("revision"), state.revision)
        assertEquals(record.getInt("messages"), state.messages.size)
        assertEquals(record.getString("digest"), digest(state.messages))
        assertTrue(state.stories.size >= record.getInt("stories"))
        tag("give-potion").performClick(); idle()
        tag("notice").assertTextContains("no longer hold", substring = true)
        accepted()
        assertEquals(record.getString("digest"), digest(model().state.value.messages))
        // New story retains the spent story and gives its own player a separate potion.
        compose.createStoryThroughMainReview(10_000); idle()
        assertEquals(0L, model().state.value.revision)
        assertTrue(model().state.value.messages.isEmpty())
        tag("potion-owner").assertTextEquals("Healing potion · You")
        state = model().state.value
        select(state.stories.single { it.story == saved.story && it.branch == saved.branch })
        accepted()
        assertEquals(record.getString("digest"), digest(model().state.value.messages))
        assertTrue(file.delete())
        assertTrue(directory.delete()) // Empty exact checkpoint only; saved stories remain.
    }
}

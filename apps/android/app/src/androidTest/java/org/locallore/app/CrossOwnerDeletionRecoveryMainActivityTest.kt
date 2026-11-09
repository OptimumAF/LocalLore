/* Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0 */
package org.locallore.app

import android.content.Intent
import androidx.compose.ui.test.*
import androidx.compose.ui.test.junit4.createEmptyComposeRule
import androidx.lifecycle.ViewModelProvider
import androidx.test.core.app.ActivityScenario
import androidx.test.ext.junit.runners.AndroidJUnit4
import androidx.test.platform.app.InstrumentationRegistry
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.runBlocking
import kotlinx.coroutines.withTimeout
import org.junit.Assert.*
import org.junit.Rule
import org.junit.Test
import org.junit.runner.RunWith

/** Production Activity and native deletion in a fresh, isolated synthetic library. */
@RunWith(AndroidJUnit4::class)
class CrossOwnerDeletionRecoveryMainActivityTest {
    @get:Rule val compose = createEmptyComposeRule()

    @Test fun recoversRetainedStoryAfterAnotherOwnerDeletesSelection() {
        val context = InstrumentationRegistry.getInstrumentation().targetContext
        assertEquals("org.locallore.app.storydelete", context.packageName)

        ActivityScenario.launch<MainActivity>(Intent(context, MainActivity::class.java)).use { activity ->
            lateinit var model: ShellViewModel
            activity.onActivity { model = ViewModelProvider(it)[ShellViewModel::class.java] }
            val initial = awaitState(model) { it.persistent && !it.busy }
            assertFalse(initial.recoveryRequired)
            assertNull(initial.selectedStory)
            assertTrue("Run this test in an empty isolated library", initial.stories.isEmpty())
            tag("empty-library").assertIsDisplayed()

            compose.createStoryThroughMainReview(TIMEOUT_MS)
            val freshRetained = awaitState(model) { !it.busy && it.selectedStory != null }
            val retainedId = checkNotNull(freshRetained.selectedStory).story
            assertEquals(1, freshRetained.stories.size)
            assertEquals(0L, freshRetained.revision)
            tag("give-potion").assertIsEnabled().performClick()
            val retained = awaitState(model) { !it.busy && it.revision == 1L }
            val retainedStory = checkNotNull(retained.selectedStory)
            assertEquals(retainedId, retainedStory.story)
            assertEquals(listOf(retainedStory), retained.stories)
            assertEquals(2, retained.messages.size)
            assertEquals("Not in your inventory", retained.potionOwner)

            compose.createStoryThroughMainReview(TIMEOUT_MS)
            val targetView = awaitState(model) {
                !it.busy && it.selectedStory?.let { story -> story.story != retainedId } == true
            }
            val target = checkNotNull(targetView.selectedStory)
            assertEquals(setOf(retainedStory, target), targetView.stories.toSet())
            assertEquals(2, targetView.stories.size)
            assertEquals(0L, target.revision)
            assertTrue(targetView.messages.isEmpty())
            assertEquals(0, targetView.uncommittedDrafts)

            // Use a separate archive lease while this Activity keeps its selected workspace session.
            runBlocking(Dispatchers.IO) {
                val archive = NativeArchiveGateway(context)
                try {
                    withTimeout(TIMEOUT_MS) {
                        val prepared = archive.prepare(target)
                        assertEquals(target.story, prepared.preview.storyId)
                        assertEquals(mapOf(target.branch to target.revision), prepared.preview.branchHeads)
                        assertEquals(0L, prepared.preview.committedTurns)
                        assertEquals(0L, prepared.preview.draftTurns)
                        assertEquals(StoryDeleted(target.story, 1L, 0L), archive.commit(prepared.token))
                    }
                } finally {
                    archive.close()
                }
            }

            tag("give-potion").assertIsEnabled().performClick()
            val paused = awaitState(model) { !it.busy && it.recoveryRequired }
            assertFalse(paused.localRestartRequired)
            assertEquals(targetView.selectedStory, paused.selectedStory)
            assertEquals(targetView.stories, paused.stories)
            assertEquals(targetView.revision, paused.revision)
            assertEquals(targetView.messages, paused.messages)
            assertEquals(targetView.inventory, paused.inventory)
            assertEquals(targetView.uncommittedDrafts, paused.uncommittedDrafts)
            tag("give-potion").assertIsNotEnabled()
            tag("recover-save").assertIsEnabled().performClick()

            val recovered = awaitState(model) { !it.busy && !it.recoveryRequired }
            assertEquals(listOf(retainedStory), recovered.stories)
            assertEquals(retainedStory, recovered.selectedStory)
            assertEquals(retained.revision, recovered.revision)
            assertEquals(retained.messages, recovered.messages)
            assertEquals(retained.potionOwner, recovered.potionOwner)
            assertEquals(retained.inventory, recovered.inventory)
            assertEquals(retained.timelines, recovered.timelines)
            assertEquals(retained.uncommittedDrafts, recovered.uncommittedDrafts)
            tag("notice").assertIsDisplayed()
                .assertTextEquals("Previously selected timeline is unavailable. Review the library before sending.")
            tag("saved-library").assertTextEquals("Saved stories · 1 · $retainedId")
            tag("revision").assertTextEquals("Accepted revision · 1")
            for (message in retained.messages) {
                val id = message.id
                tag("message-body-$id").assertIsDisplayed().assertTextEquals(message.text)
            }
            compose.assertPlayerPotionQuantity(null) { model.state.value }
        }
    }

    private fun awaitState(model: ShellViewModel, ready: (ShellState) -> Boolean): ShellState {
        compose.waitUntil(TIMEOUT_MS) { ready(model.state.value) }
        return compose.runOnIdle { model.state.value }
    }

    private fun tag(name: String): SemanticsNodeInteraction {
        compose.onNodeWithTag("story-list").performScrollToNode(hasTestTag(name))
        return compose.onNodeWithTag(name)
    }

    private companion object {
        const val TIMEOUT_MS = 15_000L
    }
}

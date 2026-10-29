/* Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0 */
package org.locallore.app

import android.content.Intent
import androidx.compose.ui.test.*
import androidx.compose.ui.test.junit4.createEmptyComposeRule
import androidx.lifecycle.ViewModelProvider
import androidx.test.core.app.ActivityScenario
import androidx.test.ext.junit.runners.AndroidJUnit4
import androidx.test.platform.app.InstrumentationRegistry
import org.junit.Assert.*
import org.junit.Rule
import org.junit.Test
import org.junit.runner.RunWith

/** Real Compose/Main factory/JNI creation. Authored UNRUN; no OS-death/model/joined-drain claim. */
@RunWith(AndroidJUnit4::class)
class StoryTemplateChoiceMainActivityTest {
    @get:Rule val compose = createEmptyComposeRule()
    private lateinit var model: ShellViewModel
    private fun activity(action: () -> Unit) {
        val context = InstrumentationRegistry.getInstrumentation().targetContext
        assertEquals("org.locallore.app.draftprocessverify", context.packageName)
        assertTrue(BuildConfig.INPUT_PROCESS_VERIFICATION)
        val scenario = ActivityScenario.launch<MainActivity>(Intent(context, MainActivity::class.java))
        try {
            scenario.onActivity { model = ViewModelProvider(it)[ShellViewModel::class.java] }
            settled()
            action()
        } finally {
            scenario.close() // Ordinary Activity close, not a joined native-drain proof.
        }
    }
    private fun settled() {
        compose.waitUntil(15_000) { model.state.value.let { it.persistent && !it.busy && !it.creationActive } }
        compose.waitForIdle()
        assertFalse(model.state.value.recoveryRequired)
    }
    private fun libraryTag(name: String): SemanticsNodeInteraction {
        compose.onNodeWithTag("story-list").performScrollToNode(hasTestTag(name))
        return compose.onNodeWithTag(name)
    }
    private fun review() {
        libraryTag("reset-demo").assertIsEnabled().performClick()
        compose.waitUntil(15_000) { model.creation.value.let { it.visible && !it.busy && it.review != null } }
        assertEquals(DEFAULT_STORY_TEMPLATE, model.creation.value.review!!.preview.template)
    }
    private fun chooseHarbor() {
        compose.onNodeWithTag("story-template-bracken-harbor-v1").performScrollTo().performClick()
        compose.waitUntil(15_000) { model.creation.value.let { !it.busy && it.review?.preview?.template == "bracken-harbor-v1" } }
        compose.onNodeWithText("Rules · Narrative").performScrollTo().assertIsDisplayed()
    }
    private fun create(title: String): SavedStory {
        compose.onNodeWithTag("story-creation-title").performScrollTo().performTextReplacement(title)
        compose.onNodeWithTag("story-creation-confirm").performScrollTo().assertIsEnabled().performClick()
        settled()
        return checkNotNull(model.state.value.selectedStory).also {
            assertEquals(title, it.title)
            assertEquals("main", it.branch)
            assertEquals(0L, it.revision)
            assertEquals(0L, model.state.value.revision)
            assertTrue(model.state.value.messages.isEmpty())
            assertEquals(TextProvider.SCRIPTED, model.state.value.textProvider)
        }
    }

    @Test fun explicitNarrativeAndFantasyChoicesRemainSeparateAndReopenWithTheirNativeRules() {
        lateinit var harbor: SavedStory
        lateinit var fantasy: SavedStory
        lateinit var retained: List<SavedStory>
        activity {
            val before = model.state.value.stories.toList()
            check(before.size <= 16) // Refuse unexpected accumulated workload, never delete earlier saves.
            val selected = model.state.value.selectedStory
            review(); chooseHarbor()
            assertEquals(before, model.state.value.stories)
            compose.onNodeWithTag("story-creation-cancel").performClick()
            settled()
            assertEquals(before, model.state.value.stories)
            assertEquals(selected, model.state.value.selectedStory)
            review(); chooseHarbor()
            harbor = create("SYNTHETIC Bracken Harbor choice")
            assertEquals("narrative_v1", model.state.value.rulesProfile)
            assertFalse(before.any { it.story == harbor.story })
            val afterHarbor = model.state.value.stories.toList()
            before.forEach { old -> assertEquals(old, afterHarbor.single { it.story == old.story }) }
            review()
            compose.onNodeWithText("Rules · Fantasy").performScrollTo().assertIsDisplayed()
            fantasy = create("SYNTHETIC Lantern Quay choice")
            assertEquals("fantasy_v1", model.state.value.rulesProfile)
            assertNotEquals(harbor.story, fantasy.story)
            retained = model.state.value.stories.toList()
            afterHarbor.forEach { old -> assertEquals(old, retained.single { it.story == old.story }) }
        }
        activity {
            assertEquals(retained, model.state.value.stories)
            libraryTag("saved-library").performClick()
            compose.onNodeWithTag("saved-story-${harbor.story}").performScrollTo().performClick()
            settled()
            assertEquals(harbor, model.state.value.selectedStory)
            assertEquals("narrative_v1", model.state.value.rulesProfile)
            assertEquals(0L, model.state.value.revision)
            libraryTag("saved-library").performClick()
            compose.onNodeWithTag("saved-story-${fantasy.story}").performScrollTo().performClick()
            settled()
            assertEquals(fantasy, model.state.value.selectedStory)
            assertEquals("fantasy_v1", model.state.value.rulesProfile)
            assertEquals(retained, model.state.value.stories)
        }
    }
}

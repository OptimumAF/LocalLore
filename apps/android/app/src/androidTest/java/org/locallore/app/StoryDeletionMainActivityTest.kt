/* Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0 */
package org.locallore.app

import androidx.compose.ui.test.*
import androidx.compose.ui.test.junit4.createAndroidComposeRule
import androidx.lifecycle.ViewModelProvider
import androidx.test.platform.app.InstrumentationRegistry
import org.junit.Assert.*
import org.junit.Rule
import org.junit.Test

/** Dedicated test APK only: validates the product factory and preserves prior synthetic stories. */
class StoryDeletionMainActivityTest {
    @get:Rule val compose = createAndroidComposeRule<MainActivity>()
    private lateinit var model: ShellViewModel
    @Test fun explicitCreateDeleteRecreatePreservesLibraryAndExplicitCreateWorksAgain() {
        assertTrue(InstrumentationRegistry.getInstrumentation().targetContext.packageName in setOf("org.locallore.app.storydelete", "org.locallore.app.parentverify"))
        attach()
        compose.waitUntil(15_000) { !model.state.value.busy && model.state.value.persistent }
        assertFalse(model.state.value.recoveryRequired)
        val retained = model.state.value.stories
        if (retained.isEmpty()) compose.onNodeWithTag("empty-library").performScrollTo().assertIsDisplayed()
        compose.createStoryThroughMainReview(15_000)
        compose.waitUntil(15_000) { !model.state.value.busy && model.state.value.selectedStory?.let { selected ->
            retained.none { it.story == selected.story } } == true }
        val story = requireNotNull(model.state.value.selectedStory)
        compose.onNodeWithTag("delete-story").performScrollTo().performClick()
        compose.waitUntil(15_000) { model.deletion.value.prepared != null }
        assertEquals(story.story, model.deletion.value.prepared!!.preview.storyId)
        compose.onNodeWithTag("delete-confirm").performScrollTo().performClick()
        compose.waitUntil(15_000) { model.deletion.value.deleted != null }
        compose.onNodeWithTag("delete-close").performClick()
        compose.waitUntil(15_000) { !model.state.value.busy && !model.state.value.deletionActive && model.state.value.stories == retained }
        compose.activityRule.scenario.recreate(); attach()
        compose.waitUntil(15_000) { !model.state.value.busy && model.state.value.persistent }
        assertEquals(retained, model.state.value.stories)
        if (retained.isEmpty()) {
            assertNull(model.state.value.selectedStory); assertTrue(model.state.value.messages.isEmpty())
            compose.onNodeWithTag("empty-library").performScrollTo().assertIsDisplayed()
            compose.onNodeWithTag("give-potion").performScrollTo().assertIsNotEnabled()
        }
        // Leave a fresh synthetic story for read-only Activity/archive regression tests.
        compose.createStoryThroughMainReview(15_000)
        compose.waitUntil(15_000) { !model.state.value.busy && model.state.value.selectedStory?.let { selected ->
            retained.none { it.story == selected.story } } == true }
        assertNotEquals(story.story, model.state.value.selectedStory!!.story)
        assertEquals(0L, model.state.value.revision)
    }
    private fun attach() = compose.activityRule.scenario.onActivity { model = ViewModelProvider(it)[ShellViewModel::class.java] }
}

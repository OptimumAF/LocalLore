/* Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0 */
package org.locallore.app

import androidx.compose.ui.test.*
import androidx.compose.ui.test.junit4.createAndroidComposeRule
import androidx.lifecycle.ViewModelProvider
import androidx.test.platform.app.InstrumentationRegistry
import org.junit.Assert.*
import org.junit.Rule
import org.junit.Test

/** Product factory and actual selector callback; default data belongs only to the isolated APK. */
class TimelineMainActivityTest {
    @get:Rule val compose = createAndroidComposeRule<MainActivity>()
    @Test fun actualProductSelectorResumesItsNativeCatalogEntry() {
        assertTrue(InstrumentationRegistry.getInstrumentation().targetContext.packageName in setOf("org.locallore.app.timelineverify", "org.locallore.app.parentverify"))
        lateinit var model: ShellViewModel
        compose.activityRule.scenario.onActivity { model = ViewModelProvider(it)[ShellViewModel::class.java] }
        compose.waitUntil(15_000) { !model.state.value.busy && model.state.value.persistent }
        assertFalse(model.state.value.recoveryRequired)
        if (model.state.value.selectedStory == null) {
            compose.createStoryThroughMainReview(15_000)
            compose.waitUntil(15_000) { !model.state.value.busy && model.state.value.selectedStory != null }
        }
        val before = model.state.value
        val branch = requireNotNull(before.selectedStory).branch
        assertTrue(before.timelines.any { it.branch == branch })
        compose.onNodeWithTag("timeline-library").performScrollTo().performClick()
        compose.onNodeWithTag("timeline-$branch").performClick()
        compose.waitUntil(15_000) { !model.state.value.busy && model.state.value.notice == "Saved timeline resumed." }
        assertEquals(before.selectedStory, model.state.value.selectedStory)
        assertEquals(before.messages, model.state.value.messages); assertEquals(before.revision, model.state.value.revision)
        assertFalse(model.state.value.recoveryRequired)
    }
}

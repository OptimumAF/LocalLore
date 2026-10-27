/* Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0 */
package org.locallore.app

import androidx.compose.ui.test.*
import androidx.compose.ui.test.junit4.createAndroidComposeRule
import androidx.lifecycle.ViewModelProvider
import androidx.test.ext.junit.runners.AndroidJUnit4
import org.json.JSONObject
import org.junit.Assert.*
import org.junit.Before
import org.junit.Rule
import org.junit.Test
import org.junit.runner.RunWith

@RunWith(AndroidJUnit4::class)
class DiagnosticsIntegrationTest {
    @get:Rule val compose = createAndroidComposeRule<MainActivity>()
    private fun model() = ViewModelProvider(compose.activity)[ShellViewModel::class.java]
    private fun tag(name: String): SemanticsNodeInteraction {
        compose.onNodeWithTag("story-list").performScrollToNode(hasTestTag(name))
        return compose.onNodeWithTag(name)
    }
    private fun idle() { compose.waitUntil(8_000) { !model().state.value.busy }; compose.waitForIdle() }
    @Before fun freshSavedStory() { idle(); compose.createStoryThroughMainReview(); idle() }
    private fun gift() { tag("give-potion").performClick(); idle() }
    private fun preview() { tag("open-diagnostics").performClick(); compose.onNodeWithTag("diagnostics-dialog").assertIsDisplayed() }

    @Test fun actualNativeOutcomesAreSanitizedAndClearingCannotChangeCanon() {
        gift(); preview()
        val json = model().diagnostics.value.preview
        val records = JSONObject(json).getJSONArray("records")
        assertTrue((0 until records.length()).any { records.getJSONObject(it).getString("outcome") == "ACCEPTED" })
        for (forbidden in listOf("Mira", "potion", "quay", "SECRET", "narration", "scope", "turn", "handle")) {
            assertFalse(json.contains(forbidden))
        }
        compose.onNodeWithTag("diagnostics-clear").performClick()
        assertEquals(0, JSONObject(model().diagnostics.value.preview).getInt("count"))
        compose.onNodeWithTag("diagnostics-close").performClick()
        assertEquals(1L, model().state.value.revision)
        assertEquals("Not in your inventory", model().state.value.potionOwner)
    }

    @Test fun reviewedSnapshotAndPendingConsentSurviveActivityRecreation() {
        gift(); preview()
        val reviewed = model().diagnostics.value.preview
        // Controlled picker callback/sink here; actual ContentResolver ownership has separate tests.
        compose.runOnIdle { assertTrue(model().beginDiagnosticExport()) }
        compose.activityRule.scenario.recreate()
        compose.onNodeWithTag("diagnostics-dialog").assertIsDisplayed()
        assertEquals(reviewed, model().diagnostics.value.preview)
        var written = ""
        compose.runOnIdle { model().completeDiagnosticExport { written = it.toString(Charsets.UTF_8) } }
        compose.waitUntil(3_000) { !model().diagnostics.value.exporting }
        assertEquals(reviewed, written)
        assertEquals(1L, model().state.value.revision)
    }

    @Test fun revokingPickerAndLateResultDoesNotOpenDestination() {
        preview()
        compose.runOnIdle {
            assertTrue(model().beginDiagnosticExport())
            model().closeDiagnostics(); model().openDiagnostics()
            assertFalse(model().beginDiagnosticExport())
        }
        var wrote = false
        compose.runOnIdle { model().completeDiagnosticExport { wrote = true } }
        compose.waitForIdle()
        assertFalse(wrote)
        assertEquals(0L, model().state.value.revision)
        compose.onNodeWithTag("diagnostics-close").performClick()
    }

    @Test fun cancelAndMalformedGenerationProduceOnlyFixedDiagnosticCategories() {
        tag("mode-menu").performClick(); compose.onNodeWithTag("mode-DELAYED").performClick()
        compose.runOnIdle {
            model().submit(DemoAction.GIVE_POTION)
            assertTrue(model().state.value.preparingResponse)
            model().cancel()
        }
        idle()
        tag("mode-menu").performClick(); compose.onNodeWithTag("mode-MALFORMED").performClick()
        tag("give-potion").performClick(); idle(); preview()
        val json = model().diagnostics.value.preview
        assertTrue(json.contains("CANCEL"))
        assertTrue(json.contains("MALFORMED"))
        assertFalse(json.contains("potion"))
        assertEquals(0L, model().state.value.revision)
    }
}

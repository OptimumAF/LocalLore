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
        val review = model().diagnostics.value.review
        // Controlled picker callback/sink here; actual ContentResolver ownership has separate tests.
        compose.runOnIdle { assertTrue(model().beginDiagnosticExport(review)) }
        compose.activityRule.scenario.recreate()
        compose.onNodeWithTag("diagnostics-dialog").assertIsDisplayed()
        assertEquals(reviewed, model().diagnostics.value.preview)
        assertSame(review, model().diagnostics.value.review)
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

    @Test fun retiredReviewCannotClearOrCloseTheReplacementNativePreview() {
        gift(); preview()
        val retired = model().diagnostics.value.review
        compose.onNodeWithTag("diagnostics-close").performClick()
        tag("try-ability").performClick(); idle(); preview()
        val current = model().diagnostics.value
        val native = model().state.value
        compose.runOnIdle {
            model().clearDiagnostics(retired)
            assertEquals(current, model().diagnostics.value)
            model().closeDiagnostics(retired)
            assertEquals(current, model().diagnostics.value)
        }
        compose.onNodeWithTag("diagnostics-dialog").assertIsDisplayed()
        assertEquals(native, model().state.value)
        assertEquals(1L, native.revision)
        assertEquals("Not in your inventory", native.potionOwner)
        // Current controls still clear only metadata and close their own review.
        compose.onNodeWithTag("diagnostics-clear").performClick()
        assertEquals(0, JSONObject(model().diagnostics.value.preview).getInt("count"))
        assertNotSame(current.review, model().diagnostics.value.review)
        compose.onNodeWithTag("diagnostics-close").performClick()
        assertEquals(native.revision, model().state.value.revision)
        assertEquals(native.potionOwner, model().state.value.potionOwner)
        assertEquals(native.messages, model().state.value.messages)
    }

    @Test fun staleScopedExportCannotBorrowTheCurrentReviewAcrossRecreation() {
        gift(); preview()
        val retired = model().diagnostics.value.review
        compose.onNodeWithTag("diagnostics-close").performClick()
        preview()
        val current = model().diagnostics.value
        val native = model().state.value
        assertNotSame(retired, current.review)
        compose.activityRule.scenario.recreate()
        compose.onNodeWithTag("diagnostics-dialog").assertIsDisplayed()
        assertSame(current.review, model().diagnostics.value.review)
        var writes = 0
        var exported: ByteArray? = null
        compose.runOnIdle {
            assertFalse(model().beginDiagnosticExport(retired))
            // A synthetic late picker result cannot open even our controlled sink.
            model().completeDiagnosticExport { writes++; exported = it }
        }
        compose.waitForIdle()
        assertEquals(0, writes)
        assertEquals(current, model().diagnostics.value)
        compose.runOnIdle {
            assertTrue(model().beginDiagnosticExport(current.review))
            model().completeDiagnosticExport { writes++; exported = it }
        }
        compose.waitUntil(3_000) { !model().diagnostics.value.exporting }
        assertEquals(1, writes)
        assertArrayEquals(current.preview.toByteArray(Charsets.UTF_8), exported)
        for (privateField in listOf("Mira", "potion", "quay", "SECRET", "narration", "scope", "turn", "handle")) {
            assertFalse(current.preview.contains(privateField))
        }
        compose.onNodeWithTag("diagnostics-close").performClick()
        assertEquals(native.revision, model().state.value.revision)
        assertEquals(native.potionOwner, model().state.value.potionOwner)
        assertEquals(native.messages, model().state.value.messages)
    }
}

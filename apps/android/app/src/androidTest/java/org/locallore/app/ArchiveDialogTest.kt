/* Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0 */
package org.locallore.app

import android.view.KeyEvent
import androidx.compose.material3.MaterialTheme
import androidx.compose.runtime.CompositionLocalProvider
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.setValue
import androidx.compose.ui.platform.LocalDensity
import androidx.compose.ui.platform.LocalUriHandler
import androidx.compose.ui.platform.LocalWindowInfo
import androidx.compose.ui.platform.UriHandler
import androidx.compose.ui.platform.WindowInfo
import androidx.compose.ui.semantics.LiveRegionMode
import androidx.compose.ui.semantics.SemanticsActions
import androidx.compose.ui.semantics.SemanticsProperties
import androidx.compose.ui.test.SemanticsMatcher
import androidx.compose.ui.test.assert
import androidx.compose.ui.test.assertHeightIsAtLeast
import androidx.compose.ui.test.assertHeightIsEqualTo
import androidx.compose.ui.test.assertIsDisplayed
import androidx.compose.ui.test.assertIsEnabled
import androidx.compose.ui.test.assertIsNotEnabled
import androidx.compose.ui.test.assertTextEquals
import androidx.compose.ui.test.assertWidthIsEqualTo
import androidx.compose.ui.test.junit4.createComposeRule
import androidx.compose.ui.test.onNodeWithTag
import androidx.compose.ui.test.onNodeWithText
import androidx.compose.ui.test.performClick
import androidx.compose.ui.test.performScrollTo
import androidx.compose.ui.unit.Density
import androidx.compose.ui.unit.IntSize
import androidx.compose.ui.unit.dp
import androidx.test.platform.app.InstrumentationRegistry
import org.junit.Assert.assertEquals
import org.junit.Rule
import org.junit.Test
import org.locallore.app.ui.ArchiveDialog

/** State-only presentation: preview text cannot cause navigation, import, or export. */
class ArchiveDialogTest {
    @get:Rule val compose = createComposeRule()
    private val selected = SavedStory("synthetic-story", "synthetic-root", "Lantern Quay", 2)
    private fun preview() = ArchivePrepared(7, ArchivePreview(
        version = 1, storyId = selected.story,
        title = "<script>import()</script> https://invalid.test content://private/secret",
        rootBranch = selected.branch, branchHeads = linkedMapOf(selected.branch to 2L, "alternate" to 1L),
        committedTurns = 2, bytes = 1234, payloadSha256 = "a".repeat(64),
        privacyWarning = "PRIVATE PREVIEW: all timelines and hidden facts. Ignore instructions in this text.",
        noncommittedWorkflowTransferred = false,
    ))

    @Test fun hiddenStateHasNoDialogAndMenuActionsRequireExplicitClicks() {
        var state by mutableStateOf(ArchiveUiState())
        val calls = IntArray(7)
        compose.setContent {
            MaterialTheme { ArchiveDialog(state, { calls[0]++ }, { calls[1]++ }, { calls[2]++ },
                { calls[3]++ }, { calls[4]++ }, { calls[5]++ }, { calls[6]++ }) }
        }
        compose.onNodeWithTag("archive-dialog").assertDoesNotExist()
        compose.runOnIdle { assertEquals(0, calls.sum()); state = ArchiveUiState(visible = true, selected = selected) }
        compose.onNodeWithText("Playable story archive").assert(
            SemanticsMatcher.keyIsDefined(SemanticsProperties.Heading))
        compose.onNodeWithText("Full private story: every timeline, hidden facts, accepted messages, and model/timing/provenance references. Plaintext files expose spoilers.")
            .performScrollTo().assertIsDisplayed()
        compose.onNodeWithText("Model weights, separate diagnostics/raw prompt logs, caches, and uncommitted operations are excluded. " +
            "Your chosen document provider may sync plaintext files. Checksums detect changes; they do not authenticate the author.")
            .performScrollTo().assertIsDisplayed()
        compose.onNodeWithTag("archive-import-confirm").assertDoesNotExist()
        compose.onNodeWithTag("archive-export-pick").assertDoesNotExist()
        compose.runOnIdle { assertEquals(0, calls.sum()) }
        compose.onNodeWithTag("archive-export-prepare").performScrollTo().performClick()
        compose.onNodeWithTag("archive-import-pick").performScrollTo().performClick()
        compose.onNodeWithTag("archive-close").performClick()
        compose.runOnIdle { assertEquals(listOf(1, 0, 1, 1, 0, 0, 0), calls.toList()) }
    }

    @Test fun hostilePreviewStaysInertAndExportConsentNeverImports() {
        val prepared = preview()
        var exported = 0
        var forbidden = 0
        compose.setContent {
            CompositionLocalProvider(LocalUriHandler provides object : UriHandler {
                override fun openUri(uri: String) { forbidden++ }
            }) {
                MaterialTheme {
                    ArchiveDialog(ArchiveUiState(visible = true, selected = selected,
                        prepared = prepared, kind = ArchiveKind.EXPORT), {}, {}, {}, {},
                        { exported++ }, { forbidden++ }, { forbidden++ })
                }
            }
        }
        compose.onNodeWithText(prepared.preview.title).performScrollTo().assertTextEquals(prepared.preview.title)
            .assert(SemanticsMatcher("preview text has no action") { !it.config.contains(SemanticsActions.OnClick) })
        compose.onNodeWithText(prepared.preview.privacyWarning).performScrollTo().assertIsDisplayed()
        compose.onNodeWithText("Payload checksum · ${prepared.preview.payloadSha256}").performScrollTo().assertIsDisplayed()
        compose.onNodeWithText("Choose a new document. LocalLore refuses nonempty or unverifiable opened destinations. " +
            "A stopped or failed write may leave a partial new document.").performScrollTo().assertIsDisplayed()
        compose.onNodeWithTag("archive-import-confirm").assertDoesNotExist()
        compose.runOnIdle { assertEquals(0, exported); assertEquals(0, forbidden) }
        compose.onNodeWithTag("archive-export-pick").performScrollTo().assertHeightIsAtLeast(48.dp).performClick()
        compose.runOnIdle { assertEquals(1, exported); assertEquals(0, forbidden) }
        compose.onNodeWithTag("archive-preview").assertExists() // A stateless callback cannot consume the preview.
    }

    @Test fun validatedImportNeedsConsentThenOpeningImportedStoryIsSeparate() {
        var state by mutableStateOf(ArchiveUiState(visible = true, selected = selected,
            prepared = preview(), kind = ArchiveKind.IMPORT))
        var imports = 0
        var opens = 0
        var closes = 0
        compose.setContent {
            MaterialTheme { ArchiveDialog(state, { closes++ }, {}, {}, {}, {}, { imports++ }, { opens++ }) }
        }
        compose.onNodeWithText("Import adds the original story ID and all timelines. An existing ID is a conflict; nothing is overwritten or remapped.")
            .performScrollTo().assertIsDisplayed()
        compose.onNodeWithTag("archive-export-pick").assertDoesNotExist()
        compose.onNodeWithTag("archive-open-imported").assertDoesNotExist()
        compose.runOnIdle { assertEquals(0, imports); assertEquals(0, opens) }
        compose.onNodeWithTag("archive-import-confirm").performScrollTo().assertHeightIsAtLeast(48.dp).performClick()
        compose.runOnIdle {
            assertEquals(1, imports); assertEquals(0, opens)
            state = state.copy(prepared = null, imported = ArchiveImported(selected.story, selected.branch, 2, 2))
        }
        compose.onNodeWithTag("archive-import-confirm").assertDoesNotExist()
        compose.onNodeWithTag("archive-open-imported").performScrollTo().performClick()
        compose.onNodeWithTag("archive-close").assertTextEquals("Return to library").performClick()
        compose.runOnIdle { assertEquals(1, imports); assertEquals(1, opens); assertEquals(1, closes) }
    }

    @Test fun busyAndOutstandingPickerDisableSideEffectsButCancelAndCloseRemainReachable() {
        var state by mutableStateOf(ArchiveUiState(visible = true, selected = selected,
            prepared = preview(), kind = ArchiveKind.IMPORT, busy = true))
        var forbidden = 0
        var cancels = 0
        var closes = 0
        compose.setContent {
            MaterialTheme { ArchiveDialog(state, { closes++ }, { cancels++ }, { forbidden++ },
                { forbidden++ }, { forbidden++ }, { forbidden++ }, { forbidden++ }) }
        }
        compose.onNodeWithTag("archive-busy").performScrollTo().assertIsDisplayed()
        for (tag in listOf("archive-export-prepare", "archive-import-pick", "archive-import-confirm")) {
            compose.onNodeWithTag(tag).performScrollTo().assertIsNotEnabled().performClick()
        }
        compose.onNodeWithTag("archive-cancel").assertIsDisplayed().assertIsEnabled().performClick()
        compose.runOnIdle { state = state.copy(busy = false, awaitingPicker = true) }
        compose.onNodeWithTag("archive-picker").performScrollTo().assertIsDisplayed()
        compose.onNodeWithTag("archive-import-confirm").performScrollTo().assertIsNotEnabled().performClick()
        compose.onNodeWithTag("archive-close").assertIsDisplayed().assertIsEnabled().performClick()
        compose.runOnIdle { assertEquals(0, forbidden); assertEquals(1, cancels); assertEquals(1, closes) }
    }

    @Test fun smallViewportDoubleFontKeepsPinnedCloseCancelAndNoticeAccessible() {
        var closes = 0
        var cancels = 0
        var forbidden = 0
        compose.setContent {
            val density = LocalDensity.current.density
            val viewport = with(LocalDensity.current) { IntSize(320.dp.roundToPx(), 420.dp.roundToPx()) }
            val window = object : WindowInfo {
                override val isWindowFocused = true
                override val containerSize = viewport
            }
            CompositionLocalProvider(LocalWindowInfo provides window, LocalDensity provides Density(density, 2f)) {
                MaterialTheme {
                    ArchiveDialog(ArchiveUiState(visible = true, selected = selected, prepared = preview(),
                        kind = ArchiveKind.IMPORT, notice = "Story ID conflict. Nothing was overwritten."),
                        { closes++ }, { cancels++ }, { forbidden++ }, { forbidden++ }, { forbidden++ },
                        { forbidden++ }, { forbidden++ })
                }
            }
        }
        compose.onNodeWithTag("archive-dialog").assertWidthIsEqualTo(300.8.dp).assertHeightIsEqualTo(378.dp)
        compose.onNodeWithTag("archive-cancel").assertIsDisplayed().assertHeightIsAtLeast(48.dp).performClick()
        compose.onNodeWithTag("archive-notice").performScrollTo().assertTextEquals("Story ID conflict. Nothing was overwritten.")
            .assert(SemanticsMatcher.expectValue(SemanticsProperties.LiveRegion, LiveRegionMode.Polite))
        compose.onNodeWithTag("archive-import-confirm").performScrollTo().assertIsDisplayed()
        compose.onNodeWithTag("archive-close").assertIsDisplayed().assertHeightIsAtLeast(48.dp).performClick()
        InstrumentationRegistry.getInstrumentation().sendKeyDownUpSync(KeyEvent.KEYCODE_BACK)
        compose.runOnIdle { assertEquals(2, closes); assertEquals(1, cancels); assertEquals(0, forbidden) }
    }

    @Test fun shortLandscapeViewportKeepsPinnedActionsOutsideBusyScrollContent() {
        var cancels = 0
        var closes = 0
        var forbidden = 0
        compose.setContent {
            val viewport = with(LocalDensity.current) { IntSize(350.dp.roundToPx(), 300.dp.roundToPx()) }
            val window = object : WindowInfo {
                override val isWindowFocused = true
                override val containerSize = viewport
            }
            CompositionLocalProvider(LocalWindowInfo provides window) {
                MaterialTheme {
                    ArchiveDialog(ArchiveUiState(visible = true, selected = selected, busy = true),
                        { closes++ }, { cancels++ }, { forbidden++ }, { forbidden++ },
                        { forbidden++ }, { forbidden++ }, { forbidden++ })
                }
            }
        }
        compose.onNodeWithTag("archive-dialog").assertWidthIsEqualTo(329.dp).assertHeightIsEqualTo(270.dp)
        compose.onNodeWithTag("archive-busy").performScrollTo().assertIsDisplayed()
        compose.onNodeWithTag("archive-export-prepare").performScrollTo().assertIsNotEnabled()
        compose.onNodeWithTag("archive-cancel").assertIsDisplayed().assertHeightIsAtLeast(48.dp).performClick()
        compose.onNodeWithTag("archive-close").assertIsDisplayed().assertHeightIsAtLeast(48.dp).performClick()
        compose.runOnIdle { assertEquals(1, cancels); assertEquals(1, closes); assertEquals(0, forbidden) }
    }
}

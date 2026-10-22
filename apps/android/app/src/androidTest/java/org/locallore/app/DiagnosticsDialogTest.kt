/* Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0 */
package org.locallore.app

import android.content.res.Configuration
import android.view.KeyEvent
import androidx.compose.material3.MaterialTheme
import androidx.compose.runtime.CompositionLocalProvider
import androidx.compose.ui.platform.LocalConfiguration
import androidx.compose.ui.platform.LocalDensity
import androidx.compose.ui.semantics.LiveRegionMode
import androidx.compose.ui.semantics.SemanticsProperties
import androidx.compose.ui.test.SemanticsMatcher
import androidx.compose.ui.test.assertIsDisplayed
import androidx.compose.ui.test.assertIsEnabled
import androidx.compose.ui.test.assertIsNotEnabled
import androidx.compose.ui.test.assertTextEquals
import androidx.compose.ui.test.assert
import androidx.compose.ui.test.junit4.createComposeRule
import androidx.compose.ui.test.onNodeWithTag
import androidx.compose.ui.test.onNodeWithText
import androidx.compose.ui.test.performClick
import androidx.compose.ui.test.performTouchInput
import androidx.compose.ui.test.swipeUp
import androidx.compose.ui.unit.Density
import androidx.test.platform.app.InstrumentationRegistry
import org.junit.Assert.assertEquals
import org.junit.Rule
import org.junit.Test
import org.locallore.app.ui.DiagnosticsDialog

class DiagnosticsDialogTest {
    @get:Rule val compose = createComposeRule()

    @Test fun hiddenPreviewDoesNotRenderOrInvokeActions() {
        var calls = 0
        compose.setContent {
            DiagnosticsDialog(DiagnosticsUiState(), { calls++ }, { calls++ }, { calls++ })
        }
        compose.onNodeWithTag("diagnostics-dialog").assertDoesNotExist()
        compose.runOnIdle { assertEquals(0, calls) }
    }

    @Test fun previewIsExactAndActionsAreExplicitAndStateless() {
        var dismissed = 0
        var cleared = 0
        var exported = 0
        val preview = "{\"version\":1,\"records\":[]}"
        compose.setContent {
            MaterialTheme {
                DiagnosticsDialog(
                    DiagnosticsUiState(visible = true, preview = preview),
                    { dismissed++ }, { cleared++ }, { exported++ },
                )
            }
        }
        compose.onNodeWithTag("diagnostics-json").assertTextEquals(preview)
        compose.runOnIdle { assertEquals(listOf(0, 0, 0), listOf(dismissed, cleared, exported)) }
        compose.onNodeWithTag("diagnostics-export").performClick()
        compose.onNodeWithTag("diagnostics-clear").performClick()
        compose.onNodeWithTag("diagnostics-close").performClick()
        compose.runOnIdle { assertEquals(listOf(1, 1, 1), listOf(dismissed, cleared, exported)) }
        compose.onNodeWithTag("diagnostics-dialog").assertIsDisplayed()
    }

    @Test fun busyExportDisablesClearAndExportButCloseCanCancel() {
        var dismissed = 0
        var forbidden = 0
        compose.setContent {
            MaterialTheme {
                DiagnosticsDialog(
                    DiagnosticsUiState(visible = true, exporting = true),
                    { dismissed++ }, { forbidden++ }, { forbidden++ },
                )
            }
        }
        compose.onNodeWithTag("diagnostics-export").assertIsNotEnabled().performClick()
        compose.onNodeWithTag("diagnostics-clear").assertIsNotEnabled().performClick()
        compose.onNodeWithTag("diagnostics-close").assertIsEnabled().performClick()
        compose.runOnIdle { assertEquals(1, dismissed); assertEquals(0, forbidden) }
    }

    @Test fun systemBackRequestsDismissWithoutWriting() {
        var dismissed = 0
        var exported = 0
        compose.setContent {
            MaterialTheme {
                DiagnosticsDialog(
                    DiagnosticsUiState(visible = true), { dismissed++ }, {}, { exported++ },
                )
            }
        }
        InstrumentationRegistry.getInstrumentation().sendKeyDownUpSync(KeyEvent.KEYCODE_BACK)
        compose.runOnIdle { assertEquals(1, dismissed); assertEquals(0, exported) }
    }

    @Test fun smallViewportAndDoubleFontKeepActionsAndNoticeReachable() {
        var exported = 0
        var dismissed = 0
        val preview = (1..64).joinToString("\n", "[\n", "\n]") {
            "{\"phase\":\"prepare\",\"outcome\":\"accepted\",\"elapsed_ms\":100}"
        }
        compose.setContent {
            val configuration = Configuration(LocalConfiguration.current).apply {
                screenWidthDp = 320
                screenHeightDp = 420
            }
            val density = LocalDensity.current.density
            CompositionLocalProvider(
                LocalConfiguration provides configuration,
                LocalDensity provides Density(density, 2f),
            ) {
                MaterialTheme {
                    DiagnosticsDialog(
                        DiagnosticsUiState(visible = true, preview = preview, notice = "Export cancelled."),
                        { dismissed++ }, {}, { exported++ },
                    )
                }
            }
        }
        compose.onNodeWithTag("diagnostics-export").assertIsDisplayed().performClick()
        compose.onNodeWithTag("diagnostics-clear").assertIsDisplayed()
        compose.onNodeWithTag("diagnostics-content").performTouchInput { swipeUp() }
        compose.onNodeWithText("Export cancelled.").assertIsDisplayed()
            .assert(SemanticsMatcher.expectValue(SemanticsProperties.LiveRegion, LiveRegionMode.Polite))
        compose.onNodeWithTag("diagnostics-json").assertTextEquals(preview)
        compose.onNodeWithTag("diagnostics-close").assertIsDisplayed().performClick()
        compose.runOnIdle { assertEquals(1, exported); assertEquals(1, dismissed) }
    }
}

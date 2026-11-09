/* Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0 */
package org.locallore.app

import androidx.compose.material3.MaterialTheme
import androidx.compose.runtime.mutableStateOf
import androidx.compose.ui.semantics.SemanticsActions
import androidx.compose.ui.test.assertIsDisplayed
import androidx.compose.ui.test.assertIsEnabled
import androidx.compose.ui.test.assertTextEquals
import androidx.compose.ui.test.junit4.createComposeRule
import androidx.compose.ui.test.onNodeWithTag
import androidx.compose.ui.test.performClick
import org.junit.Assert.assertEquals
import org.junit.Assert.assertNotSame
import org.junit.Assert.assertSame
import org.junit.Assert.assertTrue
import org.junit.Rule
import org.junit.Test
import org.locallore.app.ui.DiagnosticsDialog

/** Actual dialog button semantics with a synthetic current-review authority. */
class DiagnosticsDialogReviewScopeTest {
    @get:Rule val compose = createComposeRule()

    @Test fun retainedButtonsCannotAuthorizeAReplacementReviewWithIdenticalJson() {
        val preview = """{"version":1,"records":[]}"""
        val first = DiagnosticsUiState(visible = true, preview = preview)
        val replacement = first.copy(review = DiagnosticsReview())
        assertNotSame(first.review, replacement.review)
        val frame = mutableStateOf(first)
        val accepted = mutableListOf<Pair<String, DiagnosticsReview>>()

        fun authorize(action: String, review: DiagnosticsReview) {
            if (frame.value.visible && frame.value.review === review) accepted += action to review
        }

        compose.setContent {
            MaterialTheme {
                DiagnosticsDialog(
                    frame.value,
                    onDismiss = { authorize("close", it) },
                    onClear = { authorize("clear", it) },
                    onExport = { authorize("export", it) },
                )
            }
        }

        val actions = listOf("export", "clear", "close")
        val retained = actions.map { action ->
            checkNotNull(compose.onNodeWithTag("diagnostics-$action").assertIsEnabled()
                .fetchSemanticsNode().config[SemanticsActions.OnClick].action)
        }
        compose.runOnIdle { frame.value = replacement }
        compose.onNodeWithTag("diagnostics-dialog").assertIsDisplayed()
        compose.onNodeWithTag("diagnostics-json").assertTextEquals(preview)
        actions.forEach { compose.onNodeWithTag("diagnostics-$it").assertIsEnabled() }
        compose.runOnIdle {
            retained.forEach { it() }
            assertTrue(accepted.isEmpty())
        }

        actions.forEach { compose.onNodeWithTag("diagnostics-$it").performClick() }
        compose.runOnIdle {
            assertEquals(actions, accepted.map { it.first })
            accepted.forEach { (_, review) -> assertSame(replacement.review, review) }
        }
    }
}

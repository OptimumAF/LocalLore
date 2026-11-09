/* Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0 */
package org.locallore.app

import androidx.compose.material3.MaterialTheme
import androidx.compose.runtime.CompositionLocalProvider
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.setValue
import androidx.compose.ui.platform.LocalDensity
import androidx.compose.ui.platform.LocalWindowInfo
import androidx.compose.ui.platform.WindowInfo
import androidx.compose.ui.semantics.SemanticsActions
import androidx.compose.ui.test.*
import androidx.compose.ui.test.junit4.createComposeRule
import androidx.compose.ui.text.TextLayoutResult
import androidx.compose.ui.unit.Density
import androidx.compose.ui.unit.IntSize
import androidx.compose.ui.unit.dp
import org.junit.Assert.assertEquals
import org.junit.Assert.assertFalse
import org.junit.Assert.assertTrue
import org.junit.Rule
import org.junit.Test
import org.locallore.app.ui.StoryRecordDialog

class StoryRecordLargeTextTest {
    @get:Rule val compose = createComposeRule()

    @Test fun narrowRecordReflowsAtDoubleTextSizeAndKeepsActionsReachable() {
        val story = SavedStory("synthetic-story", "synthetic-root", "Lantern Quay", 2)
        var state by mutableStateOf(
            StoryRecordState(
                visible = true,
                context = StoryRecordContext(story, story.revision),
                cursor = "middle",
                total = 3,
                nextCursor = "last",
                entries = listOf(
                    StoryRecordEntry(
                        "fixture", "Harbour watch",
                        "The lantern keeper records the tide at the end of each watch.",
                        StoryRecordOrigin.KNOWN_AS_OBSERVED,
                    ),
                ),
            ),
        )
        var fontScale by mutableStateOf(1f)
        val actions = mutableListOf<String>()
        compose.setContent {
            val density = LocalDensity.current
            val viewport = with(density) { IntSize(320.dp.roundToPx(), 420.dp.roundToPx()) }
            val window = object : WindowInfo {
                override val isWindowFocused = true
                override val containerSize = viewport
            }
            CompositionLocalProvider(
                LocalWindowInfo provides window,
                LocalDensity provides Density(density.density, fontScale),
            ) {
                MaterialTheme {
                    StoryRecordDialog(
                        state = state,
                        onDismiss = {
                            actions += "close"
                            state = state.copy(visible = false)
                        },
                        onSection = { section ->
                            actions += section.wire
                            state = state.copy(section = section, cursor = null)
                        },
                        onSearch = { actions += "search" },
                        onNext = { actions += "next" },
                        onFirst = { actions += "first" },
                        onRetry = { actions += "retry" },
                    )
                }
            }
        }

        val relationships = compose.onNodeWithTag("story-record-section-relationships")
        val knowledge = compose.onNodeWithTag("story-record-section-knowledge")
        relationships.performScrollTo().assertIsDisplayed()
        knowledge.assertIsDisplayed()
        assertEquals(relationships.getUnclippedBoundsInRoot().top, knowledge.getUnclippedBoundsInRoot().top)
        assertTrue(relationships.getUnclippedBoundsInRoot().right < knowledge.getUnclippedBoundsInRoot().left)

        compose.runOnIdle { fontScale = 2f }

        val close = compose.onNodeWithTag("story-record-close")
        close.assertIsDisplayed().assertIsEnabled().assertHeightIsAtLeast(48.dp)
        val pinnedClose = close.getUnclippedBoundsInRoot()

        assertStackedControls(relationships, knowledge)
        assertReadableLabel("story-record-section-relationships", "Relationships")
        assertReadableLabel("story-record-section-knowledge", "Knowledge")

        val first = compose.onNodeWithTag("story-record-first")
        val next = compose.onNodeWithTag("story-record-next")
        assertStackedControls(first, next)
        assertReadableLabel("story-record-first", "First page")
        assertReadableLabel("story-record-next", "Next page")
        first.performTouchInput { click() }
        next.performTouchInput { click() }

        knowledge.performScrollTo().performTouchInput { click() }
        knowledge.assertIsSelected()
        close.assertIsDisplayed()
        assertEquals(pinnedClose, close.getUnclippedBoundsInRoot())
        close.performTouchInput { click() }

        compose.onNodeWithTag("story-record-dialog").assertDoesNotExist()
        compose.runOnIdle { assertEquals(listOf("first", "next", "knowledge", "close"), actions) }
    }

    private fun assertStackedControls(upper: SemanticsNodeInteraction, lower: SemanticsNodeInteraction) {
        lower.performScrollTo()
        upper.assertIsDisplayed().assertIsEnabled().assertHeightIsAtLeast(48.dp).assertWidthIsAtLeast(48.dp)
        lower.assertIsDisplayed().assertIsEnabled().assertHeightIsAtLeast(48.dp).assertWidthIsAtLeast(48.dp)
        val upperBounds = upper.getUnclippedBoundsInRoot()
        val lowerBounds = lower.getUnclippedBoundsInRoot()
        assertTrue("The controls must occupy different rows", upperBounds.bottom <= lowerBounds.top)
        assertEquals(upperBounds.left, lowerBounds.left)
        assertEquals(upperBounds.right, lowerBounds.right)
    }

    private fun assertReadableLabel(tag: String, label: String) {
        val layouts = mutableListOf<TextLayoutResult>()
        compose.onNode(hasAnyAncestor(hasTestTag(tag)) and hasText(label), useUnmergedTree = true)
            .assertIsDisplayed()
            .performSemanticsAction(SemanticsActions.GetTextLayoutResult) { getLayouts -> getLayouts(layouts) }
        val layout = layouts.single()
        assertEquals(label, layout.layoutInput.text.text)
        assertEquals(2f, layout.layoutInput.density.fontScale, 0f)
        assertFalse("The label must fit its layout: $label", layout.hasVisualOverflow)
    }
}

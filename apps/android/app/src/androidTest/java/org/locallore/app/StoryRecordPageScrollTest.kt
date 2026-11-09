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
import androidx.compose.ui.semantics.SemanticsProperties
import androidx.compose.ui.test.SemanticsNodeInteraction
import androidx.compose.ui.test.assertIsDisplayed
import androidx.compose.ui.test.assertIsEnabled
import androidx.compose.ui.test.junit4.createComposeRule
import androidx.compose.ui.test.onNodeWithTag
import androidx.compose.ui.test.onNodeWithText
import androidx.compose.ui.test.performClick
import androidx.compose.ui.test.performScrollTo
import androidx.compose.ui.test.performSemanticsAction
import androidx.compose.ui.text.AnnotatedString
import androidx.compose.ui.unit.IntSize
import androidx.compose.ui.unit.dp
import org.junit.Assert.assertEquals
import org.junit.Assert.assertTrue
import org.junit.Rule
import org.junit.Test
import org.locallore.app.ui.StoryRecordDialog

/** Synthetic reads keep the content tall so a reset cannot pass by clamping a short list. */
class StoryRecordPageScrollTest {
    @get:Rule val compose = createComposeRule()
    private var state by mutableStateOf(firstPage())

    @Test fun nextAndFirstStartAtTheTopOfTheirRenderedPage() {
        show()
        assertAtTop()

        scrolledControl("story-record-next").performClick()
        compose.runOnIdle { assertEquals(PAGE_TWO, state.cursor) }
        assertAtTop()

        scrolledControl("story-record-first").performClick()
        compose.runOnIdle { assertEquals(null, state.cursor) }
        assertAtTop()
    }

    @Test fun changingSectionAppliedSearchOrContextStartsAtTheTop() {
        show()
        scrolledControl("story-record-section-knowledge").performClick()
        compose.runOnIdle { assertEquals(StoryRecordSection.KNOWLEDGE, state.section) }
        assertAtTop()

        val searchField = scrolledControl("story-record-search")
        val beforeDraft = scrollOffset()
        // Invoke the editable semantics without opening a real device keyboard.
        searchField.performSemanticsAction(SemanticsActions.SetText) { setText ->
            assertTrue(setText(AnnotatedString("lantern")))
        }
        compose.runOnIdle { assertEquals("", state.search) }
        assertEquals("Editing the draft must keep the applied page offset", beforeDraft, scrollOffset(), 0f)
        scrolledControl("story-record-search-submit").performClick()
        compose.runOnIdle { assertEquals("lantern", state.search) }
        assertAtTop()

        scrolledControl("story-record-next")
        compose.runOnIdle {
            state = state.copy(context = StoryRecordContext(STORY.copy(branch = "alternate"), STORY.revision))
        }
        compose.onNodeWithText(STORY.title).assertIsDisplayed()
        assertAtTop()
    }

    @Test fun openingAnEventAndGoingBackRestoresTheSamePageOffset() {
        show()
        scrolledControl("story-record-next").performClick()
        assertAtTop()

        val event = scrolledControl("story-record-source-7-0")
        val beforeDetail = scrollOffset()
        event.performClick()
        compose.onNodeWithText("Event #8").assertIsDisplayed()
        compose.runOnIdle {
            val detail = checkNotNull(state.eventDetail)
            state = state.copy(eventDetail = detail.copy(loading = false,
                entry = StoryRecordEntry("event-8", "Event #8", "The watch began.",
                    StoryRecordOrigin.RECORDED_OBSERVATION)))
        }
        compose.onNodeWithTag("story-event-back").assertIsDisplayed().performClick()

        assertEquals("Back must restore the offset of the same page", beforeDetail, scrollOffset(), 0f)
        compose.runOnIdle { assertEquals(PAGE_TWO, state.cursor) }
    }

    private fun assertAtTop() {
        assertEquals("The current query must start at the top", 0f, scrollOffset(), 0f)
        compose.onNodeWithText("Story record").assertIsDisplayed()
    }

    private fun scrollOffset(): Float {
        val range = compose.onNodeWithTag("story-record-content")
            .fetchSemanticsNode().config[SemanticsProperties.VerticalScrollAxisRange]
        return compose.runOnIdle { range.value() }
    }

    private fun scrolledControl(tag: String): SemanticsNodeInteraction {
        compose.onNodeWithTag("story-record-next").performScrollTo()
        val control = compose.onNodeWithTag(tag).performScrollTo().assertIsDisplayed().assertIsEnabled()
        assertTrue("The fixture must scroll before exercising $tag", scrollOffset() > 0f)
        return control
    }

    private fun show() {
        compose.setContent {
            val density = LocalDensity.current
            val viewport = with(density) { IntSize(320.dp.roundToPx(), 420.dp.roundToPx()) }
            val window = object : WindowInfo {
                override val isWindowFocused = true
                override val containerSize = viewport
            }
            CompositionLocalProvider(LocalWindowInfo provides window) {
                MaterialTheme {
                    StoryRecordDialog(
                        state = state,
                        onDismiss = { state = state.copy(visible = false) },
                        onSection = { state = state.copy(section = it, cursor = null) },
                        onSearch = { state = state.copy(search = it, cursor = null) },
                        onNext = { state = state.copy(cursor = PAGE_TWO, nextCursor = null) },
                        onFirst = { state = state.copy(cursor = null, nextCursor = PAGE_TWO) },
                        onRetry = {},
                        onEvent = { state = state.copy(eventDetail = StoryRecordEventDetail(it)) },
                        onEventBack = { state = state.copy(eventDetail = null) },
                    )
                }
            }
        }
    }

    private companion object {
        const val PAGE_TWO = "synthetic-next-page"
        val STORY = SavedStory("fixture-story", "root", "Lantern Quay", 8)

        fun firstPage() = StoryRecordState(
            visible = true,
            context = StoryRecordContext(STORY, STORY.revision),
            total = 16,
            nextCursor = PAGE_TWO,
            entries = List(8) { index ->
                StoryRecordEntry(
                    "record-$index", "Watch ${index + 1}",
                    "The lantern keeper recorded the tide from the western quay.",
                    StoryRecordOrigin.KNOWN_AS_OBSERVED,
                    eventSources = listOf((index + 1).toLong()),
                )
            },
        )
    }
}

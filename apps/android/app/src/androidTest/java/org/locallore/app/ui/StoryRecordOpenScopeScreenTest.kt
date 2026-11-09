/* Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0 */
package org.locallore.app.ui

import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.requiredSize
import androidx.compose.runtime.mutableStateOf
import androidx.compose.ui.Modifier
import androidx.compose.ui.semantics.SemanticsActions
import androidx.compose.ui.test.SemanticsNodeInteraction
import androidx.compose.ui.test.assertIsEnabled
import androidx.compose.ui.test.hasTestTag
import androidx.compose.ui.test.junit4.createComposeRule
import androidx.compose.ui.test.onNodeWithTag
import androidx.compose.ui.test.performClick
import androidx.compose.ui.test.performScrollToNode
import androidx.compose.ui.unit.dp
import org.junit.Assert.assertEquals
import org.junit.Rule
import org.junit.Test
import org.locallore.app.SavedStory
import org.locallore.app.ShellState
import org.locallore.app.StoryRecordContext

class StoryRecordOpenScopeScreenTest {
    @get:Rule val compose = createComposeRule()

    private fun opener(): SemanticsNodeInteraction {
        compose.onNodeWithTag("story-list").performScrollToNode(hasTestTag("story-record-open"))
        return compose.onNodeWithTag("story-record-open").assertIsEnabled()
    }

    private fun retainOpener(): () -> Boolean =
        checkNotNull(opener().fetchSemanticsNode().config[SemanticsActions.OnClick].action)

    @Test fun retainedRecordButtonsCannotOpenAReplacementStoryOrRevision() {
        val a = SavedStory("synthetic-a", "main", "Lantern Quay", 4)
        val b = SavedStory("synthetic-b", "main", "Glass Garden", 12)
        val original = ShellState(revision = a.revision, persistent = true, selectedStory = a, stories = listOf(a, b))
        val state = mutableStateOf(original)
        val opened = mutableListOf<StoryRecordContext>()
        compose.setContent {
            val rendered = state.value
            Box(Modifier.requiredSize(360.dp, 620.dp)) {
                LocalLoreScreen(
                    state = rendered,
                    onAction = {},
                    onMode = {},
                    onCancel = {},
                    onReset = {},
                    onStoryRecord = {
                        opened += StoryRecordContext(checkNotNull(rendered.selectedStory), rendered.revision)
                    },
                    exposeTestTags = true,
                )
            }
        }

        val retainedA = retainOpener()
        val next = original.copy(revision = b.revision, selectedStory = b)
        compose.runOnIdle { state.value = next }
        val retainedB = retainOpener()
        compose.runOnIdle {
            retainedA()
            assertEquals(emptyList<StoryRecordContext>(), opened)
        }
        opener().performClick()

        val updated = b.copy(revision = 13)
        compose.runOnIdle {
            state.value = next.copy(revision = updated.revision, selectedStory = updated, stories = listOf(a, updated))
        }
        compose.runOnIdle {
            retainedB()
            assertEquals(listOf(StoryRecordContext(b, b.revision)), opened)
        }
        opener().performClick()
        compose.runOnIdle {
            assertEquals(listOf(StoryRecordContext(b, b.revision), StoryRecordContext(updated, updated.revision)), opened)
        }
    }
}

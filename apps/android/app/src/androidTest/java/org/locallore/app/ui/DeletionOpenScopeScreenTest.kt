/* Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0 */
package org.locallore.app.ui

import androidx.compose.material3.MaterialTheme
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.setValue
import androidx.compose.ui.semantics.SemanticsActions
import androidx.compose.ui.test.*
import androidx.compose.ui.test.junit4.createComposeRule
import org.junit.Assert.assertEquals
import org.junit.Assert.assertTrue
import org.junit.Rule
import org.junit.Test
import org.locallore.app.SavedStory
import org.locallore.app.ShellState

/** Real screen opener actions with synthetic callbacks that do not impose their own scope guard. */
class DeletionOpenScopeScreenTest {
    @get:Rule val compose = createComposeRule()

    private fun button(tag: String): SemanticsNodeInteraction {
        compose.onNodeWithTag("story-list").performScrollToNode(hasTestTag(tag))
        return compose.onNodeWithTag(tag).assertIsEnabled()
    }

    private fun retain(tag: String): () -> Boolean =
        checkNotNull(button(tag).fetchSemanticsNode().config[SemanticsActions.OnClick].action)

    @Test fun retainedDeletionOpenersCannotBorrowTheReplacementStoryOrTimeline() {
        val rootA = SavedStory("deletion-scope-a", "main", "Same visible title", 1)
        val rootB = rootA.copy(story = "deletion-scope-b")
        val first = rootA.copy(branch = "child-a", revision = 4)
        val replacement = rootB.copy(branch = "child-b", revision = 4)
        var state by mutableStateOf(ShellState(
            persistent = true,
            stories = listOf(rootA, rootB),
            selectedStory = first,
            revision = first.revision,
        ))
        val opened = mutableListOf<Pair<String, SavedStory>>()
        compose.setContent {
            MaterialTheme {
                LocalLoreScreen(
                    state = state, onAction = {}, onMode = {}, onCancel = {}, onReset = {},
                    deletionAvailable = true,
                    onDelete = { opened += "story" to checkNotNull(state.selectedStory) },
                    branchDeletionAvailable = true,
                    onDeleteTimeline = { opened += "timeline" to checkNotNull(state.selectedStory) },
                )
            }
        }

        val oldStory = retain("delete-story")
        val oldTimeline = retain("delete-timeline")
        compose.runOnIdle { state = state.copy(selectedStory = replacement) }
        button("delete-story")
        button("delete-timeline")
        compose.runOnIdle {
            oldStory()
            oldTimeline()
            assertTrue(opened.isEmpty())
        }

        button("delete-story").performClick()
        button("delete-timeline").performClick()
        compose.runOnIdle {
            assertEquals(listOf("story" to replacement, "timeline" to replacement), opened)
        }
    }
}

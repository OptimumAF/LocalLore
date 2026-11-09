/* Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0 */
package org.locallore.app.ui

import androidx.compose.material3.MaterialTheme
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.referentialEqualityPolicy
import androidx.compose.runtime.setValue
import androidx.compose.ui.semantics.SemanticsActions
import androidx.compose.ui.test.*
import androidx.compose.ui.test.junit4.createComposeRule
import org.junit.Assert.assertSame
import org.junit.Assert.assertTrue
import org.junit.Rule
import org.junit.Test
import org.locallore.app.SavedStory
import org.locallore.app.ShellState

/** Real screen opener semantics with an unguarded callback that observes the latest frame. */
class ArchiveOpenScopeScreenTest {
    @get:Rule val compose = createComposeRule()

    private fun archiveButton(): SemanticsNodeInteraction {
        compose.onNodeWithTag("story-list").performScrollToNode(hasTestTag("story-archive"))
        return compose.onNodeWithTag("story-archive").assertIsEnabled()
    }

    @Test fun retainedArchiveOpenerCannotBorrowAReplacementRenderedFrame() {
        val first = SavedStory("archive-scope-a", "main", "Same visible title", 4)
        val advanced = first.copy(revision = 5)
        val other = advanced.copy(story = "archive-scope-b")
        val initial = ShellState(
            persistent = true,
            stories = listOf(first, other),
            selectedStory = first,
            revision = first.revision,
        )
        val nextHead = initial.copy(
            stories = listOf(advanced, other), selectedStory = advanced, revision = advanced.revision,
        )
        var frame by mutableStateOf(initial, referentialEqualityPolicy())
        val opened = mutableListOf<ShellState>()
        compose.setContent {
            MaterialTheme {
                LocalLoreScreen(
                    state = frame, onAction = {}, onMode = {}, onCancel = {}, onReset = {},
                    archiveAvailable = true, onArchive = { opened += frame },
                )
            }
        }

        for (replacement in listOf(initial.copy(), nextHead, nextHead.copy(selectedStory = other))) {
            val retained = checkNotNull(archiveButton().fetchSemanticsNode().config[SemanticsActions.OnClick].action)
            compose.runOnIdle { frame = replacement }
            val current = archiveButton()
            compose.runOnIdle {
                retained()
                assertTrue(opened.isEmpty())
            }
            current.performClick()
            compose.runOnIdle {
                assertSame(replacement, opened.single())
                opened.clear()
            }
        }
    }
}

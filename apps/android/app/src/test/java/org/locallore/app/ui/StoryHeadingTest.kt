/* Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0 */
package org.locallore.app.ui

import org.junit.Assert.*
import org.junit.Test
import org.locallore.app.SavedStory
import org.locallore.app.SceneMessage
import org.locallore.app.ShellState

/** Final product contract; the initial extraction intentionally retains the old rendering. */
class StoryHeadingTest {
    @Test fun savedHeadingUsesTheSelectedStoryEvenWhenItIsNotFirstInTheCatalog() {
        val decoy = SavedStory("story-a", "main", "Decoy catalog title", 2)
        val selected = SavedStory("story-b", "fork", "Copper Orchard", 19)
        val state = ShellState(persistent = true, selectedStory = selected, stories = listOf(decoy, selected))
        assertEquals(StoryHeading("Copper Orchard", "Choose what to try or say next."), storyHeading(state))
    }

    @Test fun everySelectedSavedStoryIncludingTheStarterUsesNeutralIntroduction() {
        val scenarios = listOf(
            SavedStory("starter", "main", "Lantern Quay", 0) to "Lantern Quay",
            SavedStory("authored", "main", "North Pier", 7) to "North Pier",
            SavedStory("restored", "branch-b", "An unrelated restored world", 91) to "An unrelated restored world",
        )
        for ((selected, expectedTitle) in scenarios) {
            val state = ShellState(persistent = true, selectedStory = selected, stories = listOf(selected))
            assertEquals(StoryHeading(expectedTitle, "Choose what to try or say next."), storyHeading(state))
        }
    }

    @Test fun unresolvedSavedSelectionNeverBorrowsAHeadingFromTheCatalog() {
        val decoy = SavedStory("decoy", "main", "Not selected", 12)
        for (busy in listOf(false, true)) {
            assertNull(storyHeading(ShellState(persistent = true, busy = busy,
                stories = listOf(decoy), storageLocation = "D:/private/database.sqlite",
                messages = listOf(SceneMessage(1, "An accepted place name is not a selection.", false)))))
        }
    }

    @Test fun demoKeepsTheExactOriginalIntroductionDespiteMisleadingSavedMetadata() {
        val misleading = SavedStory("not-active", "wrong-branch", "Not the demo title", 99)
        val state = ShellState(persistent = false, selectedStory = misleading, stories = listOf(misleading),
            storageLocation = "D:/somewhere/Copper-Orchard.sqlite",
            messages = listOf(SceneMessage(10, "North Pier and Iona are accepted story text.", false)))
        assertEquals(StoryHeading("Lantern Quay", "The tide laps below the quay. Mira waits beside you. " +
            "Oren\u2019s borrowed brass key rests in your satchel."), storyHeading(state))
        assertEquals(storyHeading(ShellState()), storyHeading(state))
    }

    @Test fun unicodeTitleAndBranchChangesUseMetadataWithoutParsingOrMutatingHistory() {
        val title = "  Caf\u00e9 \u6f22\u5b57 \ud83c\udf3f\nA title, not a location  "
        val selected = SavedStory("unicode", "main", title, 15)
        val accepted = mutableListOf(SceneMessage(1, "Lantern Quay is a legitimate recorded message.", true),
            SceneMessage(2, "Mira and Oren are allowed in accepted narration.", false))
        val state = ShellState(revision = 15, persistent = true, selectedStory = selected, stories = listOf(selected),
            storageLocation = "D:/misleading/Location.sqlite", notice = "Location: Not the heading", messages = accepted)
        val historyBefore = accepted.map { it.copy() }
        assertEquals(StoryHeading(title, "Choose what to try or say next."), storyHeading(state))
        val renamed = selected.copy(branch = "fork", title = "\u00celes du Nord", revision = 16)
        assertEquals(StoryHeading("\u00celes du Nord", "Choose what to try or say next."),
            storyHeading(state.copy(selectedStory = renamed)))
        assertEquals(historyBefore, accepted)
        assertSame(accepted, state.messages)
        assertSame(selected, state.selectedStory)
        assertEquals(15L, state.revision)
        assertEquals("Location: Not the heading", state.notice)
    }
}

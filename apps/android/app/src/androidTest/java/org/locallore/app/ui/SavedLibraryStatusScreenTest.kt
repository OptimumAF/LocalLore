/* Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0 */
package org.locallore.app.ui

import androidx.compose.runtime.mutableStateOf
import androidx.compose.ui.test.assertIsDisplayed
import androidx.compose.ui.test.hasTestTag
import androidx.compose.ui.test.junit4.createComposeRule
import androidx.compose.ui.test.onNodeWithTag
import androidx.compose.ui.test.performScrollToIndex
import androidx.compose.ui.test.performScrollToNode
import androidx.test.ext.junit.runners.AndroidJUnit4
import org.junit.Rule
import org.junit.Test
import org.junit.runner.RunWith
import org.locallore.app.SavedStory
import org.locallore.app.ShellState

@RunWith(AndroidJUnit4::class)
class SavedLibraryStatusScreenTest {
    @get:Rule val compose = createComposeRule()

    @Test
    fun catalogAdviceTracksConfirmedLibraryState() {
        val opening = ShellState(persistent = true, busy = true)
        val confirmed = opening.copy(busy = false, schemaVersion = 1)
        val story = SavedStory("saved-1", "main", "Rain and Lanterns", 2)
        val shell = mutableStateOf(opening)
        compose.setContent {
            LocalLoreScreen(shell.value, onAction = {}, onMode = {}, onCancel = {}, onReset = {})
        }
        assertNoCatalogAdvice()

        compose.runOnIdle { shell.value = opening.copy(busy = false) }
        assertDisplayed("library-unconfirmed")

        compose.runOnIdle { shell.value = confirmed }
        assertDisplayed("empty-library")

        compose.runOnIdle { shell.value = confirmed.copy(stories = listOf(story)) }
        assertDisplayed("library-selection-needed")
        compose.onNodeWithTag("empty-library").assertDoesNotExist()

        compose.runOnIdle { shell.value = confirmed.copy(recoveryRequired = true) }
        assertNoCatalogAdvice()
        assertDisplayed("recover-save")
    }

    private fun assertDisplayed(tag: String) {
        compose.onNodeWithTag("story-list").performScrollToNode(hasTestTag(tag))
        compose.onNodeWithTag(tag).assertIsDisplayed()
    }

    private fun assertNoCatalogAdvice() {
        // The catalog notice is the first item after the brand when it exists.
        // Position the viewport there so lazy composition cannot hide a regression.
        compose.onNodeWithTag("story-list").performScrollToIndex(1)
        compose.onNodeWithTag("empty-library").assertDoesNotExist()
        compose.onNodeWithTag("library-selection-needed").assertDoesNotExist()
        compose.onNodeWithTag("library-unconfirmed").assertDoesNotExist()
    }
}

/* Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0 */
package org.locallore.app.ui

import org.junit.Assert.assertEquals
import org.junit.Assert.assertNull
import org.junit.Test
import org.locallore.app.SavedStory
import org.locallore.app.ShellState

class SavedLibraryStatusTest {
    private val story = SavedStory("saved-1", "main", "Rain and Lanterns", 2)
    private val confirmed = ShellState(persistent = true, schemaVersion = 1)

    @Test
    fun confirmedEmptyCatalogCanOfferNewStory() {
        assertEquals(SavedLibraryStatus.EMPTY, savedLibraryStatus(confirmed))
    }

    @Test
    fun confirmedPopulatedCatalogWithoutSelectionOffersSavedStories() {
        assertEquals(SavedLibraryStatus.CHOOSE_STORY, savedLibraryStatus(confirmed.copy(stories = listOf(story))))
    }

    @Test
    fun catalogWithoutSnapshotRemainsUnconfirmed() {
        val initial = ShellState(persistent = true, databaseSchemaVersion = 5)
        assertEquals(SavedLibraryStatus.UNCONFIRMED, savedLibraryStatus(initial))
        assertEquals(SavedLibraryStatus.UNCONFIRMED, savedLibraryStatus(initial.copy(stories = listOf(story))))
    }

    @Test
    fun openingAndRecoverySuppressCatalogAdvice() {
        assertNull(savedLibraryStatus(ShellState(persistent = true, busy = true)))
        assertNull(savedLibraryStatus(ShellState(persistent = true, recoveryRequired = true)))
        assertNull(savedLibraryStatus(confirmed.copy(busy = true)))
        assertNull(savedLibraryStatus(confirmed.copy(recoveryRequired = true, stories = listOf(story))))
    }

    @Test
    fun activeLibraryOperationsSuppressCatalogAdvice() {
        val operations = mapOf(
            "archive" to confirmed.copy(archiveActive = true),
            "deletion" to confirmed.copy(deletionActive = true),
            "fork" to confirmed.copy(forkActive = true),
            "creation" to confirmed.copy(creationActive = true),
        )
        operations.forEach { (operation, state) ->
            assertNull(operation, savedLibraryStatus(state))
        }
    }

    @Test
    fun demoAndSelectedStoryDoNotNeedCatalogAdvice() {
        assertNull(savedLibraryStatus(confirmed.copy(persistent = false)))
        assertNull(savedLibraryStatus(confirmed.copy(selectedStory = story, stories = listOf(story))))
    }
}

/* Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0 */
package org.locallore.app.ui

import androidx.compose.material3.MaterialTheme
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.setValue
import androidx.compose.ui.test.*
import androidx.compose.ui.test.junit4.createComposeRule
import androidx.compose.ui.unit.dp
import org.junit.Assert.*
import org.junit.Rule
import org.junit.Test
import org.locallore.app.*

/** State-only UI consent/copy checks; native corrected import/replay is tested separately. */
class ArchiveCorrectedOpenScreenTest {
    @get:Rule val compose = createComposeRule()
    private val root = SavedStory("imported", "main", "Synthetic corrected archive", 4)
    private val prepared = ArchivePrepared(71, ArchivePreview(3, root.story, root.title, root.branch,
        linkedMapOf("main" to 4L, "corrected" to 5L, "deleted" to 3L), 3, 100,
        "a".repeat(64), "Full private archive includes hidden synthetic records", false,
        retiredBranchIds = listOf("deleted")))
    private val previewCopy = "Accepted records include play and author corrections, including private correction details, prior world facts and discovery evidence. " +
        "Import preserves these records. Opening starts on the root timeline; choose other playable timelines from the library."
    private val completionCopy = "Opening starts on the imported root timeline. Choose other playable timelines, including corrected timelines, from the library."

    @Test fun correctedArchiveDisclosurePreservesPrivacyAndRequiresSeparateImportAndRootOpen() {
        var state by mutableStateOf(ArchiveUiState(visible = true, selected = root,
            prepared = prepared, kind = ArchiveKind.IMPORT))
        var confirmed: ArchivePrepared? = null
        var opened: ArchiveImported? = null
        val imported = ArchiveImported(root.story, root.branch, 3, 3)
        compose.setContent {
            MaterialTheme {
                ArchiveDialog(state, {}, {}, {}, {}, {}, { value ->
                    confirmed = value
                    state = state.copy(prepared = null, kind = null, imported = imported)
                }, { opened = it })
            }
        }
        compose.onNodeWithText(previewCopy).performScrollTo().assertIsDisplayed()
        compose.onNodeWithText("deleted · retained ancestry through 3 (not playable)").performScrollTo().assertIsDisplayed()
        compose.onNodeWithText(prepared.preview.privacyWarning).performScrollTo().assertIsDisplayed()
        compose.onNodeWithText("Model weights, separate diagnostics/raw prompt logs, caches, and uncommitted operations are excluded. " +
            "Your chosen document provider may sync plaintext files. Checksums detect changes; they do not authenticate the author.")
            .performScrollTo().assertIsDisplayed()
        compose.onNodeWithText("Import adds the original story ID and all timelines. An existing ID is a conflict; nothing is overwritten or remapped.")
            .performScrollTo().assertIsDisplayed()
        compose.onNodeWithTag("archive-open-imported").assertDoesNotExist()
        compose.runOnIdle { assertNull(confirmed); assertNull(opened) }
        compose.onNodeWithTag("archive-import-confirm").performScrollTo().assertHeightIsAtLeast(48.dp).performClick()
        compose.runOnIdle { assertSame(prepared, confirmed); assertNull(opened) }
        compose.onNodeWithText(completionCopy).performScrollTo().assertIsDisplayed()
        compose.onNodeWithText("Opening is explicit and starts a fresh session. Imported archives never resume old pending operations.")
            .performScrollTo().assertIsDisplayed()
        compose.onNodeWithText("Opening corrected timelines on Android is currently unavailable.", substring = true)
            .assertDoesNotExist()
        compose.onNodeWithTag("archive-import-confirm").assertDoesNotExist()
        compose.onNodeWithTag("archive-open-imported").performScrollTo().assertHeightIsAtLeast(48.dp).performClick()
        compose.runOnIdle { assertSame(imported, opened) }
    }

    @Test fun busyCompletionCannotOpenAndReturningToLibraryDoesNotSelectACorrectedChild() {
        val imported = ArchiveImported(root.story, root.branch, 3, 3)
        var state by mutableStateOf(ArchiveUiState(visible = true, selected = root, imported = imported, busy = true))
        var opened: ArchiveImported? = null
        var dismissals = 0
        compose.setContent {
            MaterialTheme {
                ArchiveDialog(state, { dismissals++; state = ArchiveUiState() }, {}, {}, {}, {}, {}, { opened = it })
            }
        }
        compose.onNodeWithText(completionCopy).performScrollTo().assertIsDisplayed()
        compose.onNodeWithTag("archive-open-imported").performScrollTo().assertIsNotEnabled()
        compose.runOnIdle { assertNull(opened); state = state.copy(busy = false) }
        compose.onNodeWithTag("archive-open-imported").performScrollTo().assertIsEnabled()
        compose.onNodeWithTag("archive-close").performClick()
        compose.onNodeWithTag("archive-dialog").assertDoesNotExist()
        compose.runOnIdle { assertEquals(1, dismissals); assertNull(opened) }
    }
}

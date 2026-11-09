/* Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0 */
package org.locallore.app.ui

import org.locallore.app.ShellState

internal enum class SavedLibraryStatus(val message: String, val tag: String) {
    EMPTY("No saved stories. Choose New story to begin.", "empty-library"),
    CHOOSE_STORY("Choose a story from Saved stories to continue.", "library-selection-needed"),
    UNCONFIRMED("Local saved stories have not been confirmed yet.", "library-unconfirmed"),
}

internal fun savedLibraryStatus(state: ShellState): SavedLibraryStatus? = when {
    !state.persistent || state.selectedStory != null -> null
    state.busy || state.recoveryRequired || state.archiveActive || state.deletionActive ||
        state.forkActive || state.creationActive -> null
    state.schemaVersion == null -> SavedLibraryStatus.UNCONFIRMED
    state.stories.isNotEmpty() -> SavedLibraryStatus.CHOOSE_STORY
    else -> SavedLibraryStatus.EMPTY
}

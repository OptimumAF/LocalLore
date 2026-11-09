/* Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0 */
package org.locallore.app.ui

import androidx.compose.runtime.Composable
import androidx.lifecycle.compose.collectAsStateWithLifecycle
import org.locallore.app.ShellViewModel

@Composable
internal fun StoryRecordHost(model: ShellViewModel) {
    // Read the frame once so callbacks stay bound to the view that supplied them.
    val rendered = model.storyRecordFrames.collectAsStateWithLifecycle().value.state
    val detail = rendered.eventDetail
    StoryRecordDialog(
        state = rendered,
        onDismiss = { model.closeStoryRecord(rendered) },
        onSection = { model.recordSection(it, rendered) },
        onSearch = { model.recordSearch(it, rendered) },
        onNext = { model.nextRecordPage(rendered) },
        onFirst = { model.firstRecordPage(rendered) },
        onRetry = { model.retryStoryRecord(rendered) },
        onEvent = { model.openRecordEvent(it, rendered) },
        onScopedEvent = { model.openScopedRecordEvent(it, rendered) },
        onEventBack = { detail?.let { model.backToStoryRecord(it) } },
        onEventRetry = detail?.let { { model.retryRecordEvent(it) } },
    )
}

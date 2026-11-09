/* Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0 */
package org.locallore.app.ui

import org.locallore.app.ShellState

/** Presentation only; these labels do not classify or accept an outcome. */
internal fun chatBusyStatus(state: ShellState): String = when {
    state.preparingResponse -> "Preparing local response…"
    state.checkingCancellation -> "Checking cancellation…"
    else -> "Opening saved progress…"
}

internal fun chatAnnouncement(state: ShellState): String? =
    if (state.busy) chatBusyStatus(state) else state.notice?.takeIf { it.isNotBlank() }

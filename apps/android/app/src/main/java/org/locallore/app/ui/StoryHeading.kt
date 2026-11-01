/* Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0 */
package org.locallore.app.ui

import org.locallore.app.ShellState

internal data class StoryHeading(val title: String, val introduction: String)

/** Presentation only; the heading does not establish a location or accepted story facts. */
internal fun storyHeading(state: ShellState): StoryHeading? =
    if (state.persistent && state.selectedStory == null) null else StoryHeading(
        "Lantern Quay",
        "The tide laps below the quay. Mira waits beside you. " +
            "Oren\u2019s borrowed brass key rests in your satchel.",
    )

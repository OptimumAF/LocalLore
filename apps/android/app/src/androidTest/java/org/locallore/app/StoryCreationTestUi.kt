/* Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0 */
package org.locallore.app

import androidx.compose.ui.test.*
import androidx.compose.ui.test.junit4.ComposeContentTestRule

/** Product Main setup only: review and one explicit Create, never a controller/native shortcut. */
internal fun ComposeContentTestRule.createStoryThroughMainReview(timeoutMillis: Long = 8_000) {
    require(timeoutMillis in 1..15_000)
    val started = System.nanoTime()
    fun remaining(): Long = (timeoutMillis - (System.nanoTime() - started) / 1_000_000).also {
        check(it > 0) { "Story creation UI setup deadline expired" }
    }
    onNodeWithTag("story-list").performScrollToNode(hasTestTag("reset-demo"))
    remaining()
    onNodeWithTag("reset-demo").assertIsDisplayed().assertIsEnabled().performClick()
    waitUntil(remaining()) {
        onAllNodes(hasTestTag("story-creation-confirm") and isEnabled()).fetchSemanticsNodes().size == 1
    }
    onNodeWithTag("story-creation-confirm").performScrollTo().assertIsDisplayed().assertIsEnabled()
    remaining()
    onNodeWithTag("story-creation-confirm").performClick()
    waitUntil(remaining()) { onAllNodesWithTag("story-creation-dialog").fetchSemanticsNodes().isEmpty() }
}

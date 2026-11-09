/* Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0 */
package org.locallore.app

import androidx.compose.material3.MaterialTheme
import androidx.compose.runtime.collectAsState
import androidx.compose.runtime.getValue
import androidx.compose.ui.semantics.SemanticsActions
import androidx.compose.ui.test.*
import androidx.compose.ui.test.junit4.createComposeRule
import kotlinx.coroutines.CoroutineScope
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.SupervisorJob
import kotlinx.coroutines.cancel
import org.junit.Assert.*
import org.junit.Rule
import org.junit.Test
import org.locallore.app.ui.StoryCreationDialog

/** Real controller and retained Compose actions; synthetic ports. Android execution remains separate. */
class StoryCreationDismissDialogTest {
    @get:Rule val compose = createComposeRule()

    private class Port : StoryCreationGateway, OriginalStoryGateway {
        var creates = 0
        var originalCalls = 0
        override fun originalStories() = this
        override suspend fun preview() = StoryCreationPreview(DEFAULT_STORY_TEMPLATE, "a".repeat(64),
            "Synthetic starter", "Read-only review", "fantasy_v1", listOf("You are Rowan."))
        override suspend fun create(request: StoryCreationRequest): SavedSnapshot { creates++; error("No creation consent") }
        override suspend fun originalCapabilities() = OriginalCapabilities(true, "scripted")
        override suspend fun beginOriginal(input: OriginalInput): OriginalJob { originalCalls++; error("No generation consent") }
        override suspend fun generateOriginal(job: String): OriginalGenerated = error("No generation")
        override suspend fun reviewOriginal(job: String, input: OriginalInput, proposal: OriginalProposal, title: String): OriginalReview = error("No review")
        override suspend fun createOriginal(review: OriginalReview, creationId: String): SavedSnapshot { creates++; error("No creation consent") }
        override suspend fun cancelOriginal(job: String): Boolean { originalCalls++; return true }
    }

    @Test fun retainedStarterCancelCannotCloseReopenedReviewButFreshCancelWorks() = form(false)
    @Test fun retainedOriginalCancelCannotCloseEditedDraftButFreshCancelWorks() = form(true)

    private fun form(original: Boolean) {
        val scope = CoroutineScope(SupervisorJob() + Dispatchers.Main.immediate)
        val port = Port()
        val closed = mutableListOf<StoryCreationClose>()
        val controller = StoryCreationController(port, scope, closed::add)
        compose.setContent { MaterialTheme {
            val frame by controller.frames.collectAsState()
            val rendered = frame.state
            StoryCreationDialog(rendered, { controller.dismiss(rendered) }, controller::editTitle,
                controller::confirm, onOriginal = controller::chooseOriginal,
                onOriginalEdit = { expected, edit -> controller.editOriginal(expected, edit) })
        } }
        try {
            compose.runOnIdle { controller.open() }
            compose.waitUntil(5_000) { controller.state.value.review != null && !controller.state.value.busy }
            if (original) {
                compose.onNodeWithTag("story-creation-original").performScrollTo().performClick()
                compose.waitUntil(5_000) { controller.state.value.original != null }
            }
            val tag = if (original) "original-cancel" else "story-creation-cancel"
            val retained = checkNotNull(compose.onNodeWithTag(tag).performScrollTo()
                .fetchSemanticsNode().config[SemanticsActions.OnClick].action)
            val first = controller.state.value
            if (original) {
                compose.onNodeWithTag("original-title").performScrollTo().performTextReplacement("Edited original")
                compose.runOnIdle { assertEquals("Edited original", controller.state.value.original!!.title) }
            } else {
                compose.runOnIdle { controller.dismiss(first) }
                compose.waitUntil(5_000) { !controller.state.value.visible }
                compose.runOnIdle { assertEquals(listOf(StoryCreationClose()), closed); closed.clear(); controller.open() }
                compose.waitUntil(5_000) { controller.state.value.review != null && !controller.state.value.busy }
            }
            compose.waitForIdle()
            val replacement = controller.state.value
            compose.runOnIdle {
                assertNotSame(first, replacement)
                retained()
                assertSame(replacement, controller.state.value)
                assertTrue(closed.isEmpty())
                assertEquals(0, port.creates); assertEquals(0, port.originalCalls)
            }
            compose.onNodeWithTag(tag).performScrollTo().assertIsEnabled().performClick()
            compose.waitUntil(5_000) { !controller.state.value.visible }
            compose.runOnIdle {
                assertEquals(listOf(StoryCreationClose()), closed)
                assertEquals(0, port.creates); assertEquals(0, port.originalCalls)
            }
        } finally { compose.runOnIdle { controller.dispose(); scope.cancel() } }
    }
}

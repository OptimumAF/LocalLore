/* Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0 */
package org.locallore.app.ui

import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.requiredSize
import androidx.compose.runtime.collectAsState
import androidx.compose.runtime.getValue
import androidx.compose.ui.Modifier
import androidx.compose.ui.semantics.SemanticsActions
import androidx.compose.ui.test.*
import androidx.compose.ui.test.junit4.createComposeRule
import androidx.compose.ui.unit.dp
import androidx.lifecycle.ViewModelStore
import kotlinx.coroutines.awaitCancellation
import org.junit.Assert.*
import org.junit.Rule
import org.junit.Test
import org.locallore.app.*

/** Actual Shell/Compose cancellation route with inert histories; Android execution is separate. */
class ChatCancelScopeScreenTest {
    @get:Rule val compose = createComposeRule()

    private class Port : DemoGateway {
        override val durable = true
        val a = SavedStory("cancel-a", "main", "Synthetic A", 7)
        val b = SavedStory("cancel-b", "main", "Synthetic B", 7)
        var selected = a
        var prepares = 0
        var cancellations = 0
        var acknowledgements = 0
        var commits = 0
        val messages = listOf(SceneMessage(1, "Previously accepted synthetic history.", false))
        fun saved() = SavedSnapshot(7, "You", messages, "D:/synthetic/cancel.sqlite3", 1,
            listOf(a, b), selected, textProvider = TextProvider.SCRIPTED)
        override suspend fun initialize() = saved()
        override suspend fun snapshot() = saved()
        override suspend fun resumeSaved(story: SavedStory): SavedSnapshot { selected = story; return saved() }
        override suspend fun respond(action: DemoAction, revision: Long, mode: DemoMode): DemoResult {
            prepares++; awaitCancellation()
        }
        override suspend fun commitAsync(result: DemoResult): DemoResult { commits++; return result }
        override fun cancel() { cancellations++ }
        override suspend fun cancelSaved(): SavedSnapshot { acknowledgements++; return saved() }
    }

    @Test fun retainedCancelCannotStopReplacementResponseAtTheSameHead() = journey(false)
    @Test fun retainedCancelCannotStopAnotherTimelineResponse() = journey(true)

    private fun journey(changeTimeline: Boolean) {
        val port = Port(); val store = ViewModelStore(); lateinit var model: ShellViewModel
        compose.runOnUiThread { model = ShellViewModel(port); store.put("model", model) }
        compose.setContent {
            val state by model.state.collectAsState()
            val rendered = state
            Box(Modifier.requiredSize(360.dp, 620.dp)) {
                LocalLoreScreen(rendered, model::submit, model::setMode,
                    { model.cancel(rendered) }, model::reset, exposeTestTags = true)
            }
        }
        fun waitReady() = compose.waitUntil(5_000) { !model.state.value.busy }
        fun cancelButton(): SemanticsNodeInteraction {
            compose.onNodeWithTag("story-list").performScrollToNode(hasTestTag("cancel-turn"))
            return compose.onNodeWithTag("cancel-turn")
        }
        try {
            waitReady()
            compose.runOnIdle { model.submit(DemoAction.GIVE_POTION) }
            compose.waitUntil(5_000) { port.prepares == 1 }
            val old = checkNotNull(cancelButton().assertIsEnabled().fetchSemanticsNode()
                .config[SemanticsActions.OnClick].action)
            compose.runOnIdle { model.cancel(model.state.value) }
            waitReady()
            if (changeTimeline) {
                compose.runOnIdle { model.resume(port.a.copy(branch = "fork")) }
                waitReady()
            }
            compose.runOnIdle { model.submit(DemoAction.TRY_ABILITY) }
            compose.waitUntil(5_000) { port.prepares == 2 }
            cancelButton().assertIsDisplayed()
            val replacement = model.state.value
            compose.runOnIdle {
                assertEquals(if (changeTimeline) "fork" else "main", replacement.selectedStory!!.branch)
                old()
                assertSame(replacement, model.state.value)
                assertEquals(1, port.cancellations); assertEquals(1, port.acknowledgements)
                assertEquals(0, port.commits)
                assertEquals(port.messages, model.state.value.messages)
            }
            cancelButton().assertIsEnabled().performClick()
            waitReady()
            compose.runOnIdle {
                assertEquals(2, port.cancellations); assertEquals(2, port.acknowledgements)
                assertEquals(0, port.commits)
                assertEquals(port.messages, model.state.value.messages)
                assertFalse(model.state.value.recoveryRequired)
            }
        } finally { compose.runOnIdle { store.clear() } }
    }
}

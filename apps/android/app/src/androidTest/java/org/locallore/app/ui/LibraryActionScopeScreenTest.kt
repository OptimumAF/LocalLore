/* Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0 */
package org.locallore.app.ui

import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.requiredSize
import androidx.compose.runtime.collectAsState
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.ui.Modifier
import androidx.compose.ui.semantics.SemanticsActions
import androidx.compose.ui.test.*
import androidx.compose.ui.test.junit4.createComposeRule
import androidx.compose.ui.unit.dp
import androidx.lifecycle.ViewModelStore
import androidx.test.espresso.Espresso.pressBack
import org.junit.Assert.*
import org.junit.Rule
import org.junit.Test
import org.locallore.app.*

/** Real Shell/Compose controls and synthetic storage snapshots; Android execution is separate. */
class LibraryActionScopeScreenTest {
    @get:Rule val compose = createComposeRule()
    private class Port(var initializeFails: Boolean) : DemoGateway {
        override val durable = true
        val a = SavedStory("library-a", "main", "Synthetic A", 7)
        val b = SavedStory("library-b", "main", "Synthetic B", 7)
        var selected = a
        var initializations = 0
        var gameplay = 0
        val resumes = mutableListOf<SavedStory>()
        val history = listOf(SceneMessage(1, "Previously accepted synthetic history.", false))
        fun saved() = SavedSnapshot(7, "You", history, "D:/synthetic/library.sqlite3", 1,
            listOf(a, b), selected, textProvider = TextProvider.SCRIPTED, timelines = listOf(
                SavedTimeline(selected.story, "main", null, null, 7, 0),
                SavedTimeline(selected.story, "fork", "main", 7, 7, 0)))
        override suspend fun initialize(): SavedSnapshot {
            initializations++
            if (initializeFails) throw WorkspaceFailure("Full")
            return saved()
        }
        override suspend fun snapshot() = saved()
        override suspend fun resumeSaved(story: SavedStory): SavedSnapshot {
            resumes += story; selected = story; return saved()
        }
        override suspend fun respond(action: DemoAction, revision: Long, mode: DemoMode): DemoResult {
            gameplay++; error("No gameplay consent")
        }
    }

    @Test fun oldRecoverCannotBorrowAnEqualFailedRetryAndFreshUnselectedRecoveryWorks() = journey(0)
    @Test fun oldStoryRowsAndOpenerCannotActOnReopenedOrEqualRefreshedLibrary() = journey(1)
    @Test fun oldTimelineRowCannotActOnReopenedMenuAndFreshChoiceWorks() = journey(2)
    @Test fun disposedScreenRowCannotBorrowSameViewModelAfterRemount() = journey(3)

    private fun journey(kind: Int) {
        val port = Port(initializeFails = kind == 0); val store = ViewModelStore()
        val shown = mutableStateOf(true)
        lateinit var model: ShellViewModel
        compose.runOnUiThread { model = ShellViewModel(port); store.put("model", model) }
        compose.setContent {
            val frame by model.frames.collectAsState()
            val rendered = frame.state
            if (shown.value) Box(Modifier.requiredSize(360.dp, 620.dp)) {
                LocalLoreScreen(rendered, model::submit, model::setMode,
                    { model.cancel(rendered) }, model::reset,
                    onResume = { model.resume(it, rendered) }, onRecover = { model.recover(rendered) },
                    onTimeline = { model.resumeTimeline(it, rendered) }, exposeTestTags = true)
            }
        }
        fun ready() = compose.waitUntil(5_000) { !model.state.value.busy }
        fun control(tag: String): SemanticsNodeInteraction {
            compose.onNodeWithTag("story-list").performScrollToNode(hasTestTag(tag))
            return compose.onNodeWithTag(tag)
        }
        fun click(tag: String) = checkNotNull(compose.onNodeWithTag(tag).assertIsDisplayed()
            .fetchSemanticsNode().config[SemanticsActions.OnClick].action)
        fun waitAbsent(tag: String) = compose.waitUntil(5_000) {
            compose.onAllNodesWithTag(tag).fetchSemanticsNodes().isEmpty()
        }
        try {
            ready()
            when (kind) {
                0 -> {
                    control("recover-save").assertIsEnabled()
                    val old = click("recover-save"); val before = model.state.value
                    compose.runOnIdle { assertNull(before.selectedStory); model.recover(before) }
                    compose.waitUntil(5_000) { !model.state.value.busy && model.state.value !== before }
                    compose.waitForIdle()
                    val replacement = model.state.value
                    compose.runOnIdle {
                        assertEquals(before, replacement); assertNotSame(before, replacement)
                        assertEquals(2, port.initializations)
                        port.initializeFails = false; old()
                        assertSame(replacement, model.state.value); assertEquals(2, port.initializations)
                    }
                    control("recover-save").assertIsEnabled().performClick(); ready()
                    compose.runOnIdle {
                        assertEquals(3, port.initializations); assertEquals(port.a, model.state.value.selectedStory)
                        assertFalse(model.state.value.recoveryRequired)
                    }
                }
                1 -> {
                    compose.runOnIdle { model.resume(model.state.value.stories.first(), model.state.value) }; ready()
                    control("saved-library").assertIsEnabled(); val oldOpener = click("saved-library")
                    control("saved-library").performClick()
                    val oldRow = click("saved-story-library-b"); val menuState = model.state.value
                    pressBack(); waitAbsent("saved-story-library-b")
                    control("saved-library").performClick()
                    compose.runOnIdle {
                        assertSame(menuState, model.state.value); oldRow(); assertEquals(1, port.resumes.size)
                    }
                    compose.onNodeWithTag("saved-story-library-b").assertIsDisplayed()
                    val before = model.state.value; val priorFrameRow = click("saved-story-library-b")
                    compose.runOnIdle { model.resume(before.stories.first(), before) }
                    compose.waitUntil(5_000) { !model.state.value.busy && model.state.value !== before }
                    compose.waitForIdle()
                    if (compose.onAllNodesWithTag("saved-story-library-b").fetchSemanticsNodes().isEmpty()) {
                        control("saved-library").performClick()
                    }
                    val fresh = click("saved-story-library-b"); val replacement = model.state.value
                    compose.runOnIdle {
                        assertEquals(before, replacement); assertNotSame(before, replacement)
                        priorFrameRow(); oldOpener()
                        assertSame(replacement, model.state.value); assertEquals(2, port.resumes.size)
                        fresh()
                    }
                    ready()
                    compose.runOnIdle { assertEquals(3, port.resumes.size); assertEquals(port.b, model.state.value.selectedStory) }
                }
                2 -> {
                    control("timeline-library").performClick()
                    val old = click("timeline-fork"); val before = model.state.value
                    pressBack(); waitAbsent("timeline-fork")
                    control("timeline-library").performClick()
                    compose.runOnIdle {
                        assertSame(before, model.state.value); old(); assertTrue(port.resumes.isEmpty())
                    }
                    compose.onNodeWithTag("timeline-fork").assertIsDisplayed().performClick(); ready()
                    compose.runOnIdle {
                        assertEquals(1, port.resumes.size); assertEquals("fork", model.state.value.selectedStory!!.branch)
                    }
                }
                3 -> {
                    control("saved-library").performClick()
                    val old = click("saved-story-library-b"); val before = model.state.value
                    compose.runOnIdle { shown.value = false }
                    waitAbsent("saved-library"); waitAbsent("saved-story-library-b")
                    compose.runOnIdle { shown.value = true }
                    control("saved-library").performClick()
                    compose.runOnIdle {
                        assertSame(before, model.state.value); old(); assertTrue(port.resumes.isEmpty())
                    }
                    compose.onNodeWithTag("saved-story-library-b").assertIsDisplayed().performClick(); ready()
                    compose.runOnIdle { assertEquals(1, port.resumes.size); assertEquals(port.b, model.state.value.selectedStory) }
                }
            }
            compose.runOnIdle { assertEquals(0, port.gameplay); assertEquals(port.history, model.state.value.messages) }
        } finally { compose.runOnIdle { store.clear() } }
    }
}

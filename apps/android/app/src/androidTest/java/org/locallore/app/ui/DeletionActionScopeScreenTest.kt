/* Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0 */
package org.locallore.app.ui

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
import org.junit.After
import org.junit.Assert.*
import org.junit.Rule
import org.junit.Test
import org.locallore.app.*

/** Actual controller/frame collection/semantics; every deletion gateway is synthetic. */
class DeletionActionScopeScreenTest {
    @get:Rule val compose = createComposeRule()
    private lateinit var owner: CoroutineScope
    private var story: StoryDeletionController? = null
    private var branch: BranchDeletionController? = null

    private class Stories : StoryDeletionGateway {
        var serial = 0L
        var cancels = 0
        val prepares = mutableMapOf<Long, SavedStory>()
        val commits = mutableListOf<Long>()
        override suspend fun prepare(story: SavedStory): StoryDeletionPrepared {
            val token = ++serial
            prepares[token] = story
            return StoryDeletionPrepared(token, StoryDeletionPreview(1, story.story, story.title,
                story.branch, mapOf(story.branch to story.revision), 1, 0, 0, 0,
                mapOf("events" to 1L), "Synthetic full-story deletion preview"))
        }
        override suspend fun commit(token: Long): StoryDeleted {
            commits += token
            return StoryDeleted(prepares.getValue(token).story, 1, 1)
        }
        override fun cancel() { cancels++ }
        override fun close() {}
    }

    private class Branches : BranchDeletionGateway {
        var serial = 0L
        var cancels = 0
        val prepares = mutableMapOf<Long, SavedStory>()
        val commits = mutableListOf<Long>()
        override suspend fun prepareBranch(story: SavedStory): BranchDeletionPrepared {
            val token = ++serial
            prepares[token] = story
            return BranchDeletionPrepared(token, BranchDeletionPreview(2, story.story, story.branch,
                story.title, "main", story.revision, emptyMap(), mapOf("main" to 1L),
                listOf(story.branch), mapOf("events" to 1L), 1, 0,
                "Synthetic preview: required original ancestry remains"))
        }
        override suspend fun commitBranch(token: Long): BranchDeleted {
            commits += token
            val selected = prepares.getValue(token)
            return BranchDeleted(selected.story, selected.branch, 1, 0, 1, listOf(selected.branch))
        }
        override fun cancel() { cancels++ }
        override fun close() {}
    }

    @After fun dispose() {
        if (::owner.isInitialized) compose.runOnIdle {
            story?.dispose(); branch?.dispose(); owner.cancel()
        }
    }

    private fun retained(tag: String, scroll: Boolean = false): () -> Boolean {
        val node = compose.onNodeWithTag(tag)
        if (scroll) node.performScrollTo()
        return node.fetchSemanticsNode().config[SemanticsActions.OnClick].action!!
    }

    @Test fun retainedStoryConfirmCancelAndCloseCannotDeleteOrDismissTheReplacementStory() {
        val gateway = Stories()
        val closed = mutableListOf<StoryDeleted?>()
        val first = SavedStory("story-a", "main", "Story A", 1)
        val second = SavedStory("story-b", "main", "Story B", 2)
        lateinit var controller: StoryDeletionController
        compose.runOnIdle {
            owner = CoroutineScope(SupervisorJob() + Dispatchers.Main.immediate)
            controller = StoryDeletionController(owner, gateway) { closed += it }
            story = controller
            controller.open(first)
        }
        compose.setContent {
            val frame by controller.frames.collectAsState()
            val rendered = frame.state
            MaterialTheme {
                StoryDeletionDialog(rendered, { controller.dismiss(rendered) },
                    { controller.cancel(rendered) }, { expected -> controller.confirm(expected, rendered) })
            }
        }
        val oldConfirm = retained("delete-confirm", scroll = true)
        val oldCancel = retained("delete-cancel")
        val oldClose = retained("delete-close")
        compose.runOnIdle { controller.dismiss(controller.state.value); controller.open(second) }
        compose.waitForIdle()
        compose.runOnIdle {
            assertEquals(2, gateway.serial)
            val cancelCount = gateway.cancels
            val closedCount = closed.size
            oldConfirm(); oldCancel(); oldClose()
            assertTrue(gateway.commits.isEmpty())
            assertEquals(cancelCount, gateway.cancels)
            assertEquals(closedCount, closed.size)
            assertTrue(controller.state.value.visible)
            assertEquals(second.story, controller.state.value.prepared!!.preview.storyId)
        }
        val fresh = retained("delete-confirm", scroll = true)
        compose.onNodeWithTag("delete-confirm").performClick()
        compose.runOnIdle {
            fresh(); fresh()
            assertEquals(listOf(2L), gateway.commits)
            assertEquals(second.story, controller.state.value.deleted!!.storyId)
        }
        compose.onNodeWithTag("delete-close").performClick()
        compose.onNodeWithTag("delete-dialog").assertDoesNotExist()
        compose.runOnIdle { assertEquals(second.story, closed.last()!!.storyId) }
    }

    @Test fun retainedTimelineConfirmCancelAndCloseCannotRetargetAnotherStoryOrBranch() {
        val gateway = Branches()
        val closed = mutableListOf<Pair<BranchDeleted?, Boolean>>()
        val first = SavedStory("story-a", "child-a", "Story A", 1)
        val second = SavedStory("story-b", "child-b", "Story B", 2)
        lateinit var controller: BranchDeletionController
        compose.runOnIdle {
            owner = CoroutineScope(SupervisorJob() + Dispatchers.Main.immediate)
            controller = BranchDeletionController(owner, gateway) { result, uncertain -> closed += result to uncertain }
            branch = controller
            controller.open(first, "main")
        }
        compose.setContent {
            val frame by controller.frames.collectAsState()
            val rendered = frame.state
            MaterialTheme {
                BranchDeletionDialog(rendered, { controller.dismiss(rendered) },
                    { controller.cancel(rendered) }, { expected -> controller.confirm(expected, rendered) })
            }
        }
        val oldConfirm = retained("branch-delete-confirm", scroll = true)
        val oldCancel = retained("branch-delete-cancel")
        val oldClose = retained("branch-delete-close")
        compose.runOnIdle { controller.dismiss(controller.state.value); controller.open(second, "main") }
        compose.waitForIdle()
        compose.runOnIdle {
            assertEquals(2, gateway.serial)
            val cancelCount = gateway.cancels
            val closedCount = closed.size
            oldConfirm(); oldCancel(); oldClose()
            assertTrue(gateway.commits.isEmpty())
            assertEquals(cancelCount, gateway.cancels)
            assertEquals(closedCount, closed.size)
            assertTrue(controller.state.value.visible)
            assertEquals(second.branch, controller.state.value.prepared!!.preview.branchId)
        }
        val fresh = retained("branch-delete-confirm", scroll = true)
        compose.onNodeWithTag("branch-delete-confirm").performClick()
        compose.runOnIdle {
            fresh(); fresh()
            assertEquals(listOf(2L), gateway.commits)
            assertEquals(second.story, controller.state.value.deleted!!.storyId)
            assertEquals(second.branch, controller.state.value.deleted!!.branchId)
        }
        compose.onNodeWithTag("branch-delete-close").performClick()
        compose.onNodeWithTag("branch-delete-dialog").assertDoesNotExist()
        compose.runOnIdle {
            assertEquals(second.branch, closed.last().first!!.branchId)
            assertFalse(closed.last().second)
        }
    }
}

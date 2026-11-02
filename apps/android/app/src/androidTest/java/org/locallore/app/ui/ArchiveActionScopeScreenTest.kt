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

/** Real controller/collected identity frames and clickable semantics; synthetic archive I/O only. */
class ArchiveActionScopeScreenTest {
    @get:Rule val compose = createComposeRule()
    private lateinit var owner: CoroutineScope
    private lateinit var controller: ArchiveController
    private val gateway = Archives()
    private val closed = mutableListOf<ArchiveImported?>()
    private val picked = mutableListOf<ArchivePrepared>()
    private val firstStory = SavedStory("archive-a", "main", "Archive A", 1)
    private val otherStory = SavedStory("archive-b", "main", "Archive B", 1)

    private class Archives : ArchiveGateway {
        var story = SavedStory("archive-a", "main", "Archive A", 1)
        var token = 0L
        var commits = 0
        var exports = 0
        private fun prepared() = ArchivePrepared(++token, ArchivePreview(3, story.story, story.title,
            story.branch, mapOf(story.branch to story.revision), 1, 1, "a".repeat(64),
            "Full private synthetic archive", false))
        override suspend fun prepareExport(story: SavedStory): ArchivePrepared {
            this.story = story
            return prepared()
        }
        override suspend fun prepareImport(bytes: ByteArray) = prepared()
        override suspend fun exportBytes(token: Long): ByteArray { exports++; return byteArrayOf(1) }
        override suspend fun commitImport(token: Long): ArchiveImported {
            commits++
            return ArchiveImported(story.story, story.branch, 1, 1)
        }
        override fun cancel() {}
        override fun close() {}
    }

    private fun show() {
        compose.runOnIdle {
            owner = CoroutineScope(SupervisorJob() + Dispatchers.Main.immediate)
            controller = ArchiveController(gateway, owner) { closed += it }
            controller.open(firstStory)
        }
        compose.setContent {
            val frame by controller.frames.collectAsState()
            val rendered = frame.state
            MaterialTheme {
                ArchiveDialog(rendered, { controller.dismiss(rendered) }, { controller.cancel(rendered) },
                    { controller.prepareExport(rendered) }, { controller.beginImportPicker(rendered) },
                    { expected ->
                        if (controller.beginExportPicker(expected, rendered) != null) picked += expected
                    }, { expected -> controller.confirmImport(expected, rendered) },
                    { expected -> controller.openImported(expected, rendered) })
            }
        }
    }

    @After fun dispose() {
        if (::controller.isInitialized) compose.runOnIdle { controller.dispose(); owner.cancel() }
    }

    private fun clickAction(tag: String, scroll: Boolean = true): () -> Boolean {
        val node = compose.onNodeWithTag(tag)
        if (scroll) node.performScrollTo()
        return node.fetchSemanticsNode().config[SemanticsActions.OnClick].action!!
    }

    private fun importPreview(story: SavedStory) {
        gateway.story = story
        val ticket = controller.beginImportPicker(controller.state.value)!!
        controller.completeImport(ticket) { byteArrayOf(1) }
    }

    @Test fun retainedExportNodeCannotLaunchTheReplacementPreviewPickerButFreshConsentWorks() {
        show()
        compose.onNodeWithTag("archive-export-prepare").performScrollTo().performClick()
        val oldAction = clickAction("archive-export-pick")
        lateinit var old: ArchivePrepared
        compose.runOnIdle {
            old = controller.state.value.prepared!!
            controller.prepareExport(controller.state.value)
        }
        compose.waitForIdle()
        compose.runOnIdle {
            assertNotEquals(old.token, controller.state.value.prepared!!.token)
            oldAction()
            assertTrue(picked.isEmpty())
            assertFalse(controller.state.value.awaitingPicker)
        }
        compose.onNodeWithTag("archive-export-pick").performScrollTo().performClick()
        compose.runOnIdle {
            assertEquals(1, picked.size)
            assertSame(controller.state.value.prepared, picked.single())
            assertTrue(controller.state.value.awaitingPicker)
            assertEquals(0, gateway.exports) // Choosing a destination has not delivered its callback.
        }
    }

    @Test fun retainedImportAndOpenNodesCannotCommitOrOpenTheOtherStory() {
        show()
        compose.runOnIdle { importPreview(firstStory) }
        compose.waitForIdle()
        val oldConfirm = clickAction("archive-import-confirm")
        compose.onNodeWithTag("archive-import-confirm").performClick()
        compose.waitForIdle()
        val oldOpen = clickAction("archive-open-imported")
        compose.runOnIdle {
            assertEquals(1, gateway.commits)
            controller.dismiss(controller.state.value)
            controller.open(otherStory)
            importPreview(otherStory)
        }
        compose.waitForIdle()
        compose.runOnIdle { oldConfirm(); assertEquals(1, gateway.commits) }
        compose.onNodeWithTag("archive-import-confirm").performScrollTo().performClick()
        compose.waitForIdle()
        compose.runOnIdle {
            assertEquals(2, gateway.commits)
            val before = closed.size
            oldOpen()
            assertEquals(before, closed.size)
            assertTrue(controller.state.value.visible)
            assertEquals(otherStory.story, controller.state.value.imported!!.story)
        }
        compose.onNodeWithTag("archive-open-imported").performScrollTo().performClick()
        compose.runOnIdle {
            assertFalse(controller.state.value.visible)
            assertEquals(otherStory.story, closed.last()!!.story)
        }
    }

    @Test fun equalReopenCollectsTheNewOwnerAndRetiresThePreviousCloseAction() {
        show()
        val oldClose = clickAction("archive-close", scroll = false)
        lateinit var old: ArchiveUiState
        compose.runOnIdle {
            old = controller.state.value
            controller.dismiss(old)
            controller.open(firstStory)
            assertEquals(old, controller.state.value)
            assertNotSame(old, controller.state.value)
        }
        compose.waitForIdle()
        compose.runOnIdle {
            val before = closed.size
            oldClose()
            assertEquals(before, closed.size)
            assertTrue(controller.state.value.visible)
        }
        compose.onNodeWithTag("archive-close").performClick()
        compose.onNodeWithTag("archive-dialog").assertDoesNotExist()
        compose.runOnIdle { assertEquals(2, closed.size) }
    }
}

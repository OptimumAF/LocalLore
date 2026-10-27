/* Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0 */
package org.locallore.app

import android.content.Intent
import androidx.compose.ui.test.*
import androidx.compose.ui.test.junit4.createEmptyComposeRule
import androidx.lifecycle.ViewModelProvider
import androidx.test.core.app.ActivityScenario
import androidx.test.ext.junit.runners.AndroidJUnit4
import androidx.test.platform.app.InstrumentationRegistry
import java.io.File
import java.nio.file.Files
import java.nio.file.LinkOption
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.runBlocking
import org.json.JSONArray
import org.json.JSONObject
import org.junit.Assert.*
import org.junit.Rule
import org.junit.Test
import org.junit.runner.RunWith

/** Real MainActivity/dialog/native retirement. Author source-only; no process-death/model claim. */
@RunWith(AndroidJUnit4::class)
class RetainedParentDeletionUiTest {
    @get:Rule val compose = createEmptyComposeRule()
    private lateinit var model: ShellViewModel

    private companion object {
        const val ROOT_TEXT = "SYNTHETIC deletion UI root: Mira, caf\u00e9 \uD83C\uDF0A.\nKeep my original scope."
        const val PREFIX = "SYNTHETIC deletion UI prefix: Mira, snow \u96ea.\nKeep this in the grandchild."
        const val TAIL = "SYNTHETIC unreachable UI parent tail: this must not appear in the grandchild."
        const val ADVANCE = "SYNTHETIC concurrent UI parent advance: preserve this fourth accepted receipt."
        const val STALE = "The timeline changed. Close to refresh saved timelines, then open a new deletion preview."
    }

    private data class World(val root: SavedStory, val parent: SavedStory, val child: SavedStory)

    /** Only the production Context-derived database; never a test-selected external path or SQL. */
    private fun database(): File {
        val context = InstrumentationRegistry.getInstrumentation().targetContext
        assertEquals("org.locallore.app.draftprocessverify", context.packageName)
        assertTrue(BuildConfig.INPUT_PROCESS_VERIFICATION)
        val base = context.noBackupFilesDir.canonicalFile
        val workspace = File(base, "workspace-v1")
        if (!workspace.exists()) check(workspace.mkdir())
        check(Files.isDirectory(workspace.toPath(), LinkOption.NOFOLLOW_LINKS))
        check(!Files.isSymbolicLink(workspace.toPath()) && workspace.canonicalFile.parentFile == base)
        val database = File(workspace, "stories.sqlite3")
        if (Files.exists(database.toPath(), LinkOption.NOFOLLOW_LINKS)) {
            check(Files.isRegularFile(database.toPath(), LinkOption.NOFOLLOW_LINKS))
            check(!Files.isSymbolicLink(database.toPath()))
        }
        check(database.canonicalFile.parentFile == workspace.canonicalFile)
        return database
    }

    private class RawOwner(path: File) : WorkspaceTransport {
        var handle = NativeWorkspace.open(path.absolutePath).also { check(it > 0) }
            private set
        fun reply(command: JSONObject): JSONObject {
            check(handle > 0)
            val input = JSONObject().put("version", 1).put("command", command).toString().toByteArray(Charsets.UTF_8)
            val raw = NativeWorkspace.call(handle, input)
            check(raw.size <= 262_144)
            return JSONObject(raw.toString(Charsets.UTF_8)).also { assertEquals(1, it.getInt("version")) }
        }
        fun data(command: JSONObject): JSONObject = reply(command).also {
            assertEquals("ok", it.getString("status"))
        }.getJSONObject("data")
        override suspend fun exchange(command: JSONObject): JSONObject = reply(command)
        override fun close() {
            val id = handle
            handle = 0
            if (id > 0) NativeWorkspace.close(id)
        }
    }

    private fun <T> native(action: suspend (RawOwner, DurableGateway, MutableList<NativeForkGateway>) -> T): T =
        runBlocking(Dispatchers.IO) {
            val owner = RawOwner(database())
            val gateway = DurableGateway(owner, autoCreateIfEmpty = false)
            val forks = mutableListOf<NativeForkGateway>()
            var primary: Throwable? = null
            try { action(owner, gateway, forks) }
            catch (failure: Throwable) { primary = failure; throw failure }
            finally {
                // Raw workspace close is synchronous. Production Activity adapters remain asynchronous.
                var cleanupFailure: Throwable? = null
                fun closing(block: () -> Unit) {
                    try { block() } catch (failure: Throwable) {
                        cleanupFailure?.addSuppressed(failure) ?: run { cleanupFailure = failure }
                    }
                }
                forks.asReversed().forEach { closing(it::close) }
                closing(gateway::close)
                closing(owner::close)
                cleanupFailure?.let { primary?.addSuppressed(it) ?: throw it }
            }
        }

    private suspend fun send(gateway: DurableGateway, text: String, head: Long): SavedStory {
        val prepared = gateway.respondText(PlayInput(PlayInputKind.DIALOGUE, text), head)
        assertTrue(prepared is DemoResult.Prepared)
        assertTrue(gateway.commitAsync(prepared) is DemoResult.Accepted)
        val snapshot = gateway.snapshot()
        assertEquals(head + 1, snapshot.revision)
        return checkNotNull(snapshot.selected)
    }

    private fun fixture(): World = native { owner, gateway, forks ->
        gateway.initialize()
        // Append one genuinely new native story; earlier methods' synthetic stories stay intact.
        val root = checkNotNull(gateway.createSaved().selected).let { send(gateway, ROOT_TEXT, 0) }
        suspend fun fork(parent: SavedStory, id: String): SavedStory {
            val context = checkNotNull(gateway.forkContext(parent, parent.revision, 0))
            val input = BranchForkInput(context.parent, id, parent.revision, parent.revision)
            val port = NativeForkGateway { owner.handle }.also { forks += it }
            val registered = port.register(context, input, true)
            assertEquals(BranchForkPhase.REGISTERED, registered.phase)
            val completed = port.run(registered.operation)
            assertEquals(BranchForkPhase.COMPLETED, completed.phase)
            assertTrue(checkNotNull(completed.outcome).created)
            return checkNotNull(gateway.resumeSaved(parent.copy(branch = id)).selected)
        }
        val parentOne = fork(root, "ui-retained-parent")
        assertEquals(1L, parentOne.revision)
        val parentTwo = send(gateway, PREFIX, 1)
        val child = fork(parentTwo, "ui-retained-grandchild")
        assertEquals(2L, child.revision)
        gateway.resumeSaved(parentTwo)
        val parent = send(gateway, TAIL, 2)
        assertEquals(3L, parent.revision)
        World(root, parent, child)
    } // Every fixture workspace/fork raw owner is closed before MainActivity launches.

    private fun launch(world: World, action: () -> Unit) {
        val context = InstrumentationRegistry.getInstrumentation().targetContext
        val scenario = ActivityScenario.launch<MainActivity>(Intent(context, MainActivity::class.java))
        var primary: Throwable? = null
        try {
            scenario.onActivity {
                assertNotNull(it.constructedWorkspaceTransport) // Real factory, no owner replacement.
                model = ViewModelProvider(it)[ShellViewModel::class.java]
            }
            settled()
            select(world.parent)
            action()
        } catch (failure: Throwable) { primary = failure; throw failure }
        finally {
            try { scenario.close() }
            catch (cleanup: Throwable) { primary?.addSuppressed(cleanup) ?: throw cleanup }
            // Activity/VM disposal requests adapter close; it is not joined-drain evidence.
        }
    }

    private fun settled() {
        compose.waitUntil(15_000) {
            model.state.value.let { it.persistent && !it.busy && !it.deletionActive }
        }
        compose.waitForIdle()
        assertFalse(model.state.value.recoveryRequired)
    }
    private fun storyTag(name: String): SemanticsNodeInteraction {
        compose.onNodeWithTag("story-list").performScrollToNode(hasTestTag(name))
        return compose.onNodeWithTag(name)
    }
    private fun select(story: SavedStory) {
        storyTag("saved-library").assertIsEnabled().performClick()
        compose.onNodeWithTag("saved-story-${story.story}").performScrollTo().performClick()
        settled()
        storyTag("timeline-library").assertIsEnabled().performClick()
        compose.onNodeWithTag("timeline-${story.branch}").performScrollTo().performClick()
        settled()
        assertEquals(story.story, checkNotNull(model.state.value.selectedStory).story)
        assertEquals(story.branch, checkNotNull(model.state.value.selectedStory).branch)
        assertEquals(story.revision, model.state.value.revision)
    }
    private fun preview(world: World, head: Long): BranchDeletionPrepared {
        storyTag("delete-timeline").assertIsEnabled().performClick()
        compose.waitUntil(15_000) { model.branchDeletion.value.let { it.visible && !it.busy && it.prepared != null } }
        compose.waitForIdle()
        val prepared = checkNotNull(model.branchDeletion.value.prepared)
        val p = prepared.preview
        assertEquals(2, p.version)
        assertEquals(world.root.story, p.storyId)
        assertEquals(world.parent.branch, p.branchId)
        assertEquals(world.root.branch, p.rootBranch)
        assertEquals(world.root.title, p.title)
        assertEquals(head, p.expectedRevision)
        assertEquals(mapOf(world.child.branch to 2L), p.retainedDescendants)
        assertEquals(mapOf(world.parent.branch to 2L), p.retainedHeads)
        assertTrue(p.removedBranches.isEmpty())
        assertEquals(head - 2, p.removedCommittedTurns)
        assertEquals(0L, p.removedNoncommittedTurns)
        assertEquals(head - 2, p.removedRows["turns"])
        assertEquals(0L, p.removedRows["branches"])
        compose.onNodeWithTag("branch-delete-dialog").assertIsDisplayed()
        for (text in listOf("${world.child.branch} · accepted head 2", "${world.parent.branch} · retained through head 2",
            "Committed turns removed · ${head - 2}", "Noncommitted turns removed · 0")) {
            compose.onNodeWithText(text).performScrollTo().assertTextEquals(text)
        }
        compose.onNodeWithTag("branch-delete-confirm").performScrollTo().assertIsEnabled()
        return prepared
    }
    private fun closeDialog(tag: String) {
        compose.onNodeWithTag(tag).assertIsEnabled().performClick()
        compose.waitUntil(15_000) { !model.branchDeletion.value.visible }
        settled()
        compose.onNodeWithTag("branch-delete-dialog").assertDoesNotExist()
    }

    private fun scope(story: SavedStory): JSONObject = JSONObject().put("story", story.story).put("branch", story.branch)
    private fun view(owner: RawOwner, story: SavedStory): JSONObject {
        val resumed = owner.data(JSONObject().put("op", "resume").put("scope", scope(story)))
        val result = owner.data(JSONObject().put("op", "play_snapshot").put("session", resumed.getString("session"))
            .put("scope", scope(story)).put("expected_revision", story.revision))
        assertEquals(setOf("scope", "revision", "rules", "player", "inventory", "receipts"), result.keys().asSequence().toSet())
        assertEquals(canonical(scope(story)), canonical(result.getJSONObject("scope")))
        assertEquals(story.revision, result.getLong("revision"))
        assertEquals(story.revision.toInt(), result.getJSONArray("receipts").length())
        val player = result.getJSONObject("player")
        assertEquals("player", player.getString("observer"))
        assertEquals(story.revision, player.getLong("revision"))
        assertEquals(canonical(scope(story)), canonical(player.getJSONObject("scope")))
        return result
    }
    private fun snapshot(world: World): Map<String, String> = native { owner, _, _ ->
        linkedMapOf("workspace" to canonical(owner.data(JSONObject().put("op", "workspace"))),
            "catalog" to canonical(owner.data(JSONObject().put("op", "branches").put("story", world.root.story))),
            "root" to canonical(view(owner, world.root)), "parent" to canonical(view(owner, world.parent)),
            "child" to canonical(view(owner, world.child)))
    }
    private fun assertOriginalReceipts(view: JSONObject, world: World) {
        val receipts = view.getJSONArray("receipts")
        assertEquals(2, receipts.length())
        for ((index, pair) in listOf(world.root.branch to ROOT_TEXT, world.parent.branch to PREFIX).withIndex()) {
            val request = receipts.getJSONObject(index).getJSONObject("request")
            assertEquals(world.root.story, request.getJSONObject("scope").getString("story"))
            assertEquals(pair.first, request.getJSONObject("scope").getString("branch"))
            assertEquals(index.toLong(), request.getLong("expected_revision"))
            assertEquals("free_text", request.getJSONObject("intent").getString("kind"))
            val value = request.getJSONObject("intent").getJSONObject("value")
            assertEquals("dialogue", value.getString("kind"))
            assertEquals(pair.second, value.getString("text"))
            assertNotEquals(TAIL, value.getString("text"))
        }
    }

    @Test fun cancelThenConfirmRetainedParentDeletionPreservesChildHistory() {
        val world = fixture()
        val before = snapshot(world)
        assertOriginalReceipts(JSONObject(before.getValue("child")), world)
        launch(world) {
            preview(world, 3)
            closeDialog("branch-delete-cancel")
            assertEquals(before, snapshot(world))
            // Cancellation reconciles to a native default root; it need not leave P selected.
            select(world.parent)
            preview(world, 3)
            compose.onNodeWithTag("branch-delete-confirm").performScrollTo().performClick()
            compose.waitUntil(15_000) { model.branchDeletion.value.let { !it.busy && it.deleted != null } }
            compose.waitForIdle()
            val deleted = checkNotNull(model.branchDeletion.value.deleted)
            assertEquals(world.parent.story, deleted.storyId)
            assertEquals(world.parent.branch, deleted.branchId)
            assertEquals(2L, deleted.retainedThroughRevision)
            assertEquals(0L, deleted.collectedBranches)
            assertEquals(1L, deleted.deletedTurns)
            assertEquals(listOf(world.parent.branch), deleted.invalidatedBranches)
            compose.onNodeWithText("Original ancestry retained through head 2.").performScrollTo().assertIsDisplayed()
            compose.onNodeWithText("Turns removed · 1").performScrollTo().assertIsDisplayed()
            closeDialog("branch-delete-close")
            assertTrue(model.state.value.timelines.none { it.branch == world.parent.branch })
            native { owner, _, _ ->
                assertEquals(before.getValue("workspace"), canonical(owner.data(JSONObject().put("op", "workspace"))))
                assertEquals(before.getValue("root"), canonical(view(owner, world.root)))
                val child = view(owner, world.child)
                assertEquals(before.getValue("child"), canonical(child))
                assertOriginalReceipts(child, world)
                val catalog = owner.data(JSONObject().put("op", "branches").put("story", world.root.story))
                val rows = catalog.getJSONArray("branches")
                val byId = (0 until rows.length()).associate { rows.getJSONObject(it).let { row ->
                    row.getJSONObject("scope").getString("branch") to row
                } }
                assertEquals(setOf(world.root.branch, world.parent.branch, world.child.branch), byId.keys)
                assertEquals(true, byId.getValue(world.parent.branch).get("retired"))
                assertEquals(2L, byId.getValue(world.parent.branch).getLong("revision"))
                assertEquals(false, byId.getValue(world.child.branch).get("retired"))
                assertEquals(world.parent.branch, byId.getValue(world.child.branch).getString("parent_branch"))
                assertEquals(2L, byId.getValue(world.child.branch).getLong("fork_revision"))
                val refused = owner.reply(JSONObject().put("op", "resume").put("scope", scope(world.parent)))
                assertEquals("rejected", refused.getString("status"))
                assertEquals("NotFound", refused.getString("error"))
            }
            select(world.child)
            assertTrue(model.state.value.timelines.none { it.branch == world.parent.branch })
            assertEquals(listOf(ROOT_TEXT, PREFIX), model.state.value.messages.filter { it.isPlayer }.map { it.text })
            assertFalse(model.state.value.messages.any { it.text == TAIL })
            for (message in model.state.value.messages.filter { it.isPlayer }) {
                val tag = "message-body-${message.id}"
                compose.onNodeWithTag("story-list").performScrollToNode(hasTestTag(tag))
                compose.onNodeWithTag(tag).assertIsDisplayed().assertTextEquals(message.text)
            }
            storyTag("timeline-library").performClick()
            compose.onNodeWithTag("timeline-${world.parent.branch}").assertDoesNotExist()
            compose.onNodeWithTag("timeline-${world.child.branch}").performClick()
            settled()
            assertEquals(2L, model.state.value.revision)
        }
    }

    @Test fun staleParentPreviewCannotDeleteChangedHistory() {
        val world = fixture()
        launch(world) {
            val oldPreview = preview(world, 3)
            val advanced = native { _, gateway, _ ->
                gateway.initialize()
                gateway.resumeSaved(world.parent)
                send(gateway, ADVANCE, 3)
            }
            val current = world.copy(parent = advanced)
            val baseline = snapshot(current) // After the independent native writer, before old UI consent.
            assertEquals(4L, advanced.revision)
            val lastRequest = JSONObject(baseline.getValue("parent")).getJSONArray("receipts")
                .getJSONObject(3).getJSONObject("request")
            assertEquals(canonical(scope(advanced)), canonical(lastRequest.getJSONObject("scope")))
            assertEquals(3L, lastRequest.getLong("expected_revision"))
            assertEquals(ADVANCE, lastRequest.getJSONObject("intent").getJSONObject("value").getString("text"))
            assertSame(oldPreview, model.branchDeletion.value.prepared)
            compose.onNodeWithTag("branch-delete-confirm").performScrollTo().performClick() // Exactly once.
            compose.waitUntil(15_000) { model.branchDeletion.value.let { !it.busy && it.notice == STALE } }
            compose.waitForIdle()
            compose.onNodeWithTag("branch-delete-notice").performScrollTo().assertTextEquals(STALE)
            assertNull(model.branchDeletion.value.prepared)
            assertNull(model.branchDeletion.value.deleted)
            compose.onNodeWithTag("branch-delete-confirm").assertDoesNotExist()
            compose.onNodeWithTag("branch-delete-completed").assertDoesNotExist()
            assertEquals(baseline, snapshot(current))
            closeDialog("branch-delete-close")
            select(advanced)
            assertNotSame(oldPreview, preview(current, 4))
            closeDialog("branch-delete-cancel") // No automatic retry or second confirmation.
            assertEquals(baseline, snapshot(current))
            assertOriginalReceipts(JSONObject(baseline.getValue("child")), current)
        }
    }

    private fun canonical(value: Any?): String = when (value) {
        is JSONObject -> value.keys().asSequence().toList().sorted().joinToString(",", "{", "}") {
            JSONObject.quote(it) + ":" + canonical(value.get(it))
        }
        is JSONArray -> (0 until value.length()).joinToString(",", "[", "]") { canonical(value.get(it)) }
        is String -> JSONObject.quote(value)
        null, JSONObject.NULL -> "null"
        else -> value.toString()
    }
}

/* Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0 */
package org.locallore.app

import android.content.Context
import android.content.Intent
import android.os.Process
import androidx.compose.ui.test.assertIsDisplayed
import androidx.compose.ui.test.assertIsEnabled
import androidx.compose.ui.test.assertTextEquals
import androidx.compose.ui.test.hasTestTag
import androidx.compose.ui.test.junit4.createEmptyComposeRule
import androidx.compose.ui.test.onNodeWithTag
import androidx.compose.ui.test.performClick
import androidx.compose.ui.test.performScrollTo
import androidx.compose.ui.test.performScrollToNode
import androidx.lifecycle.ViewModelProvider
import androidx.test.core.app.ActivityScenario
import androidx.test.ext.junit.runners.AndroidJUnit4
import androidx.test.platform.app.InstrumentationRegistry
import java.io.File
import java.util.UUID
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.runBlocking
import org.json.JSONObject
import org.junit.Assert.*
import org.junit.Assume.assumeTrue
import org.junit.Rule
import org.junit.Test
import org.junit.runner.RunWith

/** One opt-in fresh-task case on a disposable package, retaining its synthetic evidence. */
@RunWith(AndroidJUnit4::class)
class ColdNavigationFreshTaskTest {
    @get:Rule val compose = createEmptyComposeRule()

    private companion object {
        const val PRODUCT = "org.locallore.app.draftprocessverify"
        const val HINT_FILE = "last-selection-v1"
        const val ROOT_TEXT = "SYNTHETIC cold navigation parent: Mira keeps this receipt."
        const val CHILD_TEXT = "SYNTHETIC cold navigation child: Mira sees snow on the pier."
    }

    private data class World(val first: SavedStory, val parent: SavedStory, val child: SavedSnapshot)
    private data class ActivityOwner(val taskId: Int, val model: ShellViewModel)

    @Test fun reopensConfirmedChildFromPrivateHintWithoutSavedTaskState() {
        val requested = InstrumentationRegistry.getArguments().getString("cold_navigation_v1")
        assumeTrue("Requires the explicit cold-navigation run", requested != null)
        assertEquals("true", requested)
        val app = InstrumentationRegistry.getInstrumentation().targetContext
        assertTrue(BuildConfig.INPUT_PROCESS_VERIFICATION)
        assertEquals(PRODUCT, BuildConfig.APPLICATION_ID)
        assertEquals(PRODUCT, app.packageName)
        assertEquals(app.applicationInfo.uid, Process.myUid())

        val home = app.noBackupFilesDir.canonicalFile
        val forbidden = setOf("workspace-v1", HINT_FILE, "$HINT_FILE.new", "$HINT_FILE.bak", "process-verify-v1")
        check(home.isDirectory && checkNotNull(home.list()).none { it in forbidden }) {
            "Cold navigation requires an unused verification workspace"
        }
        val world = seed(home)
        val child = checkNotNull(world.child.selected)
        val childScope = PlayDraftScope(child.story, child.branch)
        val encoded = checkNotNull(encodeStoredNavigationHint(childScope))
        val hint = File(home, HINT_FILE)
        assertFalse(hint.exists())
        val run = UUID.randomUUID().toString().replace("-", "").take(16)
        val proof = File(home, "process-verify-v1/$run")

        val first = launch(app, run).use { scenario ->
            val owner = activityOwner(scenario)
            assertFreshProof(proof, run, owner, factories = 1)
            settled(owner.model)
            assertEquals(world.first, owner.model.state.value.selectedStory)
            assertTrue(owner.model.state.value.messages.isEmpty())

            scrollToTag("saved-library")
            compose.onNodeWithTag("saved-library").assertIsEnabled().performClick()
            compose.onNodeWithTag("saved-story-${world.parent.story}").performScrollTo().performClick()
            settled(owner.model)
            assertEquals(world.parent, owner.model.state.value.selectedStory)

            scrollToTag("timeline-library")
            compose.onNodeWithTag("timeline-library").assertIsEnabled().performClick()
            compose.onNodeWithTag("timeline-${child.branch}").performScrollTo().performClick()
            assertChild(owner.model, world.child)
            compose.waitUntil(15_000) { hint.isFile && readBounded(hint, STORED_NAVIGATION_LIMIT).contentEquals(encoded) }
            assertEquals(childScope, runBlocking { AtomicSavedNavigationStore(app).load() })
            assertArrayEquals(encoded, readBounded(hint, STORED_NAVIGATION_LIMIT))
            owner
        }

        val before = readProof(proof, "commands.json").getJSONObject("operations")
        launch(app, run).use { scenario ->
            val reopened = activityOwner(scenario)
            assertNotEquals(first.taskId, reopened.taskId)
            assertNotSame(first.model, reopened.model)
            assertFreshProof(proof, run, reopened, factories = 2)
            assertChild(reopened.model, world.child)
            val after = readProof(proof, "commands.json").getJSONObject("operations")
            assertPassiveDelta(before, after)
            assertArrayEquals(encoded, readBounded(hint, STORED_NAVIGATION_LIMIT))
        }
        // ActivityScenario requests disposal. This case does not join production owner drain.
    }

    private fun seed(home: File): World = runBlocking(Dispatchers.IO) {
        val workspace = File(home, "workspace-v1")
        check(workspace.mkdir() && workspace.canonicalFile.parentFile == home)
        val handle = NativeWorkspace.open(File(workspace, "stories.sqlite3").absolutePath)
        check(handle > 0)
        val gateway = DurableGateway(object : WorkspaceTransport {
            override suspend fun exchange(command: JSONObject): JSONObject {
                val bytes = JSONObject().put("version", 1).put("command", command).toString().toByteArray(Charsets.UTF_8)
                val reply = NativeWorkspace.call(handle, bytes)
                check(reply.size in 1..262_144)
                return JSONObject(reply.toString(Charsets.UTF_8)).also { assertEquals(1, it.getInt("version")) }
            }
            override fun close() = NativeWorkspace.close(handle)
        }, autoCreateIfEmpty = false)
        try {
            assertNull(gateway.initialize().selected)
            gateway.createSaved()
            val stories = gateway.createSaved().stories
            assertEquals(2, stories.size)
            assertEquals(stories.map { it.story }.sorted(), stories.map { it.story })
            val first = stories.first()
            val target = stories.last()
            assertNotEquals(first.story, target.story)
            assertEquals(target, gateway.resumeSaved(target).selected)
            val parent = checkNotNull(accept(gateway, ROOT_TEXT, 0).selected)

            val binding = checkNotNull(gateway.forkContext(parent, parent.revision, 0))
            val input = BranchForkInput(binding.parent, "cold-navigation-child", parent.revision, parent.revision)
            val fork = NativeForkGateway { handle }
            try {
                val registered = fork.register(binding, input, true)
                assertEquals(BranchForkPhase.REGISTERED, registered.phase)
                val result = fork.run(registered.operation)
                assertEquals(BranchForkPhase.COMPLETED, result.phase)
                assertTrue(checkNotNull(result.outcome).created)
            } finally {
                fork.close()
            }
            assertEquals(input.childBranch, gateway.resumeSaved(parent.copy(branch = input.childBranch)).selected?.branch)
            val child = accept(gateway, CHILD_TEXT, parent.revision)
            assertEquals(listOf(ROOT_TEXT, CHILD_TEXT), child.messages.filter { it.isPlayer }.map { it.text })
            World(first, parent, child)
        } finally {
            // Synchronous raw JNI close before the app-owned Activity adapter is opened.
            gateway.close()
        }
    }

    private suspend fun accept(gateway: DurableGateway, text: String, head: Long): SavedSnapshot {
        val response = gateway.respondText(PlayInput(PlayInputKind.DIALOGUE, text), head)
        assertTrue(response is DemoResult.Prepared)
        assertTrue(gateway.commitAsync(response) is DemoResult.Accepted)
        return gateway.snapshot().also { assertEquals(head + 1, it.revision) }
    }

    private fun launch(app: Context, run: String): ActivityScenario<MainActivity> =
        ActivityScenario.launch(Intent(app, MainActivity::class.java)
            .addFlags(Intent.FLAG_ACTIVITY_NEW_TASK or Intent.FLAG_ACTIVITY_MULTIPLE_TASK)
            .putExtra(ProcessVerificationProbe.RUN_EXTRA, run))

    private fun activityOwner(scenario: ActivityScenario<MainActivity>): ActivityOwner {
        lateinit var owner: ActivityOwner
        scenario.onActivity { activity ->
            assertNotNull(activity.constructedWorkspaceTransport)
            owner = ActivityOwner(activity.taskId, ViewModelProvider(activity)[ShellViewModel::class.java])
        }
        return owner
    }

    private fun assertFreshProof(directory: File, run: String, owner: ActivityOwner, factories: Int) {
        val created = readProof(directory, "created.json")
        assertEquals(2, created.getInt("version"))
        assertEquals("created", created.getString("event"))
        assertEquals(run, created.getString("run_id"))
        assertEquals(Process.myPid(), created.getInt("pid"))
        assertEquals(Process.myUid(), created.getInt("uid"))
        assertEquals(owner.taskId, created.getInt("task_id"))
        assertEquals(factories, created.getInt("factory_creations"))
        assertFalse(created.getBoolean("restored_state"))
        assertFalse(created.getBoolean("hint_present"))
        assertTrue(created.isNull("hint_sha256"))
    }

    private fun assertPassiveDelta(before: JSONObject, after: JSONObject) {
        // The probe groups play_presentation_v2 as "other". The view model verifies its exact result.
        val expected = mapOf("workspace" to 2, "branches" to 2, "resume" to 1, "open" to 1, "other" to 1)
        val keys = before.keys().asSequence().toSet()
        assertTrue(keys.containsAll(expected.keys + setOf("create", "create_named", "free_text", "submit", "prepare", "commit", "cancel")))
        assertEquals(keys, after.keys().asSequence().toSet())
        for (key in keys) {
            assertEquals("Fresh-task operation delta for $key", expected[key] ?: 0, after.getInt(key) - before.getInt(key))
        }
    }

    private fun settled(model: ShellViewModel) {
        compose.waitUntil(15_000) { model.state.value.let { it.persistent && !it.busy } }
        compose.waitForIdle()
        assertFalse(model.state.value.recoveryRequired)
    }

    private fun assertChild(model: ShellViewModel, expected: SavedSnapshot) {
        settled(model)
        val actual = model.state.value
        assertEquals(expected.selected, actual.selectedStory)
        assertEquals(expected.revision, actual.revision)
        assertEquals(expected.stories, actual.stories)
        assertEquals(expected.timelines, actual.timelines)
        assertEquals(expected.messages, actual.messages)
        assertEquals(0, actual.uncommittedDrafts)
        assertEquals(TextProvider.SCRIPTED, actual.textProvider)
        val childLine = actual.messages.single { it.isPlayer && it.text == CHILD_TEXT }
        val tag = "message-body-${childLine.id}"
        scrollToTag(tag)
        compose.onNodeWithTag(tag).assertIsDisplayed().assertTextEquals(CHILD_TEXT)
    }

    private fun scrollToTag(tag: String) {
        compose.onNodeWithTag("story-list").performScrollToNode(hasTestTag(tag))
    }

    private fun readProof(directory: File, leaf: String): JSONObject =
        JSONObject(readBounded(File(directory, leaf), 4096).toString(Charsets.UTF_8))

    private fun readBounded(file: File, limit: Int): ByteArray = file.inputStream().use { input ->
        val buffer = ByteArray(limit + 1)
        var used = 0
        while (used < buffer.size) {
            val read = input.read(buffer, used, buffer.size - used)
            if (read < 0) break
            check(read > 0)
            used += read
        }
        check(used in 1..limit) { "Unexpected verification record size" }
        buffer.copyOf(used)
    }
}

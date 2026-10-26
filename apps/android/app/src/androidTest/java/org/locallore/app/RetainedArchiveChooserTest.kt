/* Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0 */
package org.locallore.app

import android.content.Intent
import android.content.pm.PackageManager
import android.net.Uri
import android.os.Bundle
import android.os.Process
import android.os.SystemClock
import android.provider.DocumentsContract
import android.view.KeyEvent
import android.view.accessibility.AccessibilityNodeInfo
import androidx.compose.ui.test.*
import androidx.compose.ui.test.junit4.createEmptyComposeRule
import androidx.lifecycle.ViewModelProvider
import androidx.test.core.app.ActivityScenario
import androidx.test.ext.junit.runners.AndroidJUnit4
import androidx.test.platform.app.InstrumentationRegistry
import java.io.Closeable
import java.io.File
import java.nio.file.Files
import java.nio.file.LinkOption
import java.security.MessageDigest
import java.util.UUID
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.runBlocking
import org.json.JSONArray
import org.json.JSONObject
import org.junit.Assert.*
import org.junit.Rule
import org.junit.Test
import org.junit.runner.RunWith

/** Real chooser URIs and production callbacks; source-only by author, no model/process-death claim. */
@RunWith(AndroidJUnit4::class)
@Suppress("DEPRECATION")
class RetainedArchiveChooserTest {
    @get:Rule val compose = createEmptyComposeRule()
    private val instrumentation get() = InstrumentationRegistry.getInstrumentation()
    private val context get() = instrumentation.targetContext
    private val authority get() = instrumentation.context.packageName + ".chooser"
    private val documents = setOf("com.android.documentsui", "com.google.android.documentsui")
    private lateinit var model: ShellViewModel
    private lateinit var fixtureDirectory: File
    private lateinit var run: String
    private var pickerRequested = false
    private var stageNumber = 0
    private var deadline = 0L

    private companion object {
        const val LIMIT = 131_072
        const val ROOT_TEXT = "SYNTHETIC retained archive root: Mira, caf\u00e9 \uD83C\uDF0A.\nPreserve my original scope."
        const val PREFIX = "SYNTHETIC retained archive prefix: Mira, snow \u96ea.\nThe grandchild inherits this statement."
        const val TAIL = "SYNTHETIC unreachable archive parent tail must never transfer."
        const val BASELINE = "SYNTHETIC original product baseline remains accepted through every chooser operation."
        const val UNSUPPORTED = "This archive version or feature is unsupported. Nothing was imported."
        const val INVALID = "The archive is invalid or failed its integrity checks. Nothing was imported."
        const val CONFLICT = "A story with this ID already exists. Nothing was overwritten."
        const val INVENTORY = "You no longer hold the potion. Nothing changed."
    }
    private data class World(val root: SavedStory, val parent: SavedStory, val child: SavedStory,
        val rootView: String, val childView: String, val archive: ByteArray)

    private class Host(database: File) : WorkspaceTransport, Closeable {
        var handle = NativeWorkspace.open(database.canonicalPath).also { check(it > 0) }
            private set
        fun reply(command: JSONObject): JSONObject {
            check(handle > 0)
            val input = JSONObject().put("version", 1).put("command", command).toString().toByteArray(Charsets.UTF_8)
            check(input.size <= 24_576)
            val bytes = NativeWorkspace.call(handle, input)
            check(bytes.size in 1..262_144)
            return JSONObject(bytes.toString(Charsets.UTF_8)).also { assertEquals(1, it.getInt("version")) }
        }
        fun ok(command: JSONObject): JSONObject = reply(command).also {
            assertEquals("ok", it.getString("status"))
        }.getJSONObject("data")
        override suspend fun exchange(command: JSONObject): JSONObject = reply(command)
        override fun close() { val old = handle; handle = 0; if (old > 0) NativeWorkspace.close(old) }
    }
    private fun defaultDatabase(): File {
        assertEquals("org.locallore.app.draftprocessverify", context.packageName)
        assertTrue(BuildConfig.INPUT_PROCESS_VERIFICATION)
        val base = context.noBackupFilesDir.canonicalFile
        val directory = File(base, "workspace-v1")
        if (!directory.exists()) check(directory.mkdir())
        check(Files.isDirectory(directory.toPath(), LinkOption.NOFOLLOW_LINKS) && !Files.isSymbolicLink(directory.toPath()))
        check(directory.canonicalFile.parentFile == base)
        return File(directory, "stories.sqlite3").also {
            if (Files.exists(it.toPath(), LinkOption.NOFOLLOW_LINKS)) {
                check(Files.isRegularFile(it.toPath(), LinkOption.NOFOLLOW_LINKS) && !Files.isSymbolicLink(it.toPath()))
            }
            check(it.canonicalFile.parentFile == directory.canonicalFile)
        }
    }
    private fun <T> native(database: File, block: suspend (Host, DurableGateway, MutableList<NativeForkGateway>) -> T): T =
        runBlocking(Dispatchers.IO) {
            val host = Host(database)
            val gateway = DurableGateway(host, autoCreateIfEmpty = false)
            val forks = mutableListOf<NativeForkGateway>()
            var primary: Throwable? = null
            try { block(host, gateway, forks) }
            catch (failure: Throwable) { primary = failure; throw failure }
            finally {
                var cleanup: Throwable? = null
                fun close(action: () -> Unit) {
                    try { action() } catch (next: Throwable) { cleanup?.addSuppressed(next) ?: run { cleanup = next } }
                }
                forks.asReversed().forEach { close(it::close) }
                close(gateway::close); close(host::close)
                cleanup?.let { primary?.addSuppressed(it) ?: throw it }
            }
        }
    private suspend fun send(gateway: DurableGateway, words: String, head: Long): SavedStory {
        val prepared = gateway.respondText(PlayInput(PlayInputKind.DIALOGUE, words), head)
        assertTrue(prepared is DemoResult.Prepared)
        assertTrue(gateway.commitAsync(prepared) is DemoResult.Accepted)
        return checkNotNull(gateway.snapshot().also { assertEquals(head + 1, it.revision) }.selected)
    }
    private fun scope(story: SavedStory) = JSONObject().put("story", story.story).put("branch", story.branch)
    private fun view(host: Host, story: SavedStory): JSONObject {
        val opened = host.ok(JSONObject().put("op", "resume").put("scope", scope(story)))
        return host.ok(JSONObject().put("op", "play_snapshot").put("session", opened.getString("session"))
            .put("scope", scope(story)).put("expected_revision", story.revision)).also {
            assertEquals(setOf("scope", "revision", "rules", "player", "inventory", "receipts"), it.keys().asSequence().toSet())
            assertEquals(story.revision, it.getLong("revision"))
            assertEquals(canonical(scope(story)), canonical(it.getJSONObject("scope")))
            val player = it.getJSONObject("player")
            assertEquals("player", player.getString("observer"))
            assertEquals(story.revision, player.getLong("revision"))
            assertEquals(canonical(scope(story)), canonical(player.getJSONObject("scope")))
        }
    }
    private fun sourceFixture(): World {
        fixtureDirectory = File(context.noBackupFilesDir.canonicalFile, "retained-chooser-${UUID.randomUUID()}")
        Files.createDirectory(fixtureDirectory.toPath())
        check(fixtureDirectory.canonicalFile.parentFile == context.noBackupFilesDir.canonicalFile)
        val database = File(fixtureDirectory, "source.sqlite3")
        assertNotEquals(defaultDatabase().canonicalPath, database.canonicalPath)
        val scopes = native(database) { host, gateway, forks ->
            assertNull(gateway.initialize().selected)
            gateway.createSaved()
            val root = send(gateway, ROOT_TEXT, 0)
            suspend fun fork(parent: SavedStory, child: String): SavedStory {
                val binding = checkNotNull(gateway.forkContext(parent, parent.revision, 0))
                val input = BranchForkInput(binding.parent, child, parent.revision, parent.revision)
                val port = NativeForkGateway { host.handle }.also { forks += it }
                val registered = port.register(binding, input, true)
                val completed = port.run(registered.operation)
                assertEquals(BranchForkPhase.COMPLETED, completed.phase)
                assertTrue(checkNotNull(completed.outcome).created)
                return checkNotNull(gateway.resumeSaved(parent.copy(branch = child)).selected)
            }
            fork(root, "archive-retained-parent")
            val parentTwo = send(gateway, PREFIX, 1)
            val child = fork(parentTwo, "archive-retained-grandchild")
            gateway.resumeSaved(parentTwo)
            val parent = send(gateway, TAIL, 2)
            Triple(root, parent, child)
        }
        val (root, parent, child) = scopes
        io {
            archiveOwner(database) { handle ->
                val prepared = ArchiveNativeWire.branchDeletionPrepared(NativeArchive.prepareBranchDelete(handle,
                    scope(parent).put("expected_revision", 3).toString().toByteArray(Charsets.UTF_8)))
                assertEquals(mapOf(child.branch to 2L), prepared.preview.retainedDescendants)
                assertEquals(mapOf(parent.branch to 2L), prepared.preview.retainedHeads)
                val deleted = ArchiveNativeWire.branchDeleted(NativeArchive.commitBranchDelete(handle, prepared.token))
                assertEquals(2L, deleted.retainedThroughRevision)
                assertEquals(1L, deleted.deletedTurns)
            }
        }
        val views = io { Host(database).use { host -> canonical(view(host, root)) to canonical(view(host, child)) } }
        val archive = io { export(database, root) }
        val envelope = JSONObject(archive.toString(Charsets.UTF_8))
        assertEquals(2, envelope.getInt("version"))
        assertEquals(5, envelope.getJSONObject("payload").getInt("source_database_schema_version"))
        assertEquals(listOf(parent.branch), strings(envelope.getJSONObject("payload").getJSONArray("retired_branch_ids")))
        assertFalse(archive.toString(Charsets.UTF_8).contains(TAIL))
        // Check this small fixture's entire native payload before using a test-only checksum encoder.
        assertEquals(envelope.getJSONObject("integrity").getString("payload_sha256"), payloadHash(envelope))
        return World(root, parent, child, views.first, views.second, archive)
    }
    private fun <T> archiveOwner(database: File, block: (Long) -> T): T {
        val staging = File(fixtureDirectory, "stage-${++stageNumber}")
        Files.createDirectory(staging.toPath())
        val handle = NativeArchive.open(database.canonicalPath, staging.canonicalPath)
        check(handle > 0)
        var primary: Throwable? = null
        try { return block(handle) }
        catch (failure: Throwable) { primary = failure; throw failure }
        finally {
            try { NativeArchive.close(handle); assertTrue(staging.listFiles()?.isEmpty() == true) }
            catch (cleanup: Throwable) { primary?.addSuppressed(cleanup) ?: throw cleanup }
        }
    }
    private fun export(database: File, selected: SavedStory): ByteArray = archiveOwner(database) { handle ->
        val prepared = ArchiveNativeWire.prepared(NativeArchive.prepareExport(handle,
            scope(selected).put("expected_revision", selected.revision).toString().toByteArray(Charsets.UTF_8)))
        NativeArchive.exportBytes(handle, prepared.token).also { check(it.size in 1..LIMIT) }
    }
    private fun productSnapshot(): Map<String, String> = io {
        Host(defaultDatabase()).use { host ->
            val stories = host.ok(JSONObject().put("op", "workspace")).getJSONArray("stories")
            check(stories.length() in 1..16)
            (0 until stories.length()).associate { index ->
                val row = stories.getJSONObject(index)
                val rootScope = row.getJSONObject("scope")
                val story = rootScope.getString("story")
                val catalog = host.ok(JSONObject().put("op", "branches").put("story", story))
                val branches = catalog.getJSONArray("branches")
                check(branches.length() in 1..32)
                val views = JSONArray()
                for (i in 0 until branches.length()) {
                    val branch = branches.getJSONObject(i)
                    if (branch.get("retired") == false) {
                        val selected = branch.getJSONObject("scope")
                        views.put(view(host, SavedStory(story, selected.getString("branch"), row.getString("title"), branch.getLong("revision"))))
                    }
                }
                story to canonical(JSONObject().put("metadata", row).put("catalog", catalog).put("eligible", views))
            }
        }
    }
    private fun assertPrior(before: Map<String, String>, after: Map<String, String>) {
        assertTrue(after.keys.containsAll(before.keys))
        before.forEach { (key, value) -> assertEquals(value, after[key]) }
    }
    private fun assertInherited(world: World, actual: JSONObject) {
        val receipts = actual.getJSONArray("receipts")
        assertEquals(2, receipts.length())
        for ((index, pair) in listOf(world.root.branch to ROOT_TEXT, world.parent.branch to PREFIX).withIndex()) {
            val request = receipts.getJSONObject(index).getJSONObject("request")
            assertEquals(world.root.story, request.getJSONObject("scope").getString("story"))
            assertEquals(pair.first, request.getJSONObject("scope").getString("branch"))
            assertEquals(index.toLong(), request.getLong("expected_revision"))
            assertEquals("free_text", request.getJSONObject("intent").getString("kind"))
            val value = request.getJSONObject("intent").getJSONObject("value")
            assertEquals("dialogue", value.getString("kind")); assertEquals(pair.second, value.getString("text"))
        }
    }

    private fun configure(world: World) {
        val original = JSONObject(world.archive.toString(Charsets.UTF_8))
        val future = JSONObject(original.toString()).put("version", 999)
        val hostile = JSONObject(original.toString())
        val ids = listOf(world.parent.branch, world.root.branch).sorted()
        hostile.getJSONObject("payload").put("retired_branch_ids", JSONArray().apply { ids.forEach { put(it) } })
        hostile.getJSONObject("integrity").put("payload_sha256", payloadHash(hostile))
        assertEquals(hostile.getJSONObject("integrity").getString("payload_sha256"), payloadHash(hostile))
        val futureBytes = canonical(future).toByteArray(Charsets.UTF_8)
        val hostileBytes = canonical(hostile).toByteArray(Charsets.UTF_8)
        check(world.archive.size in 1..LIMIT && futureBytes.size in 1..LIMIT && hostileBytes.size in 1..LIMIT)
        val extras = Bundle().apply {
            putByteArray("archive", world.archive); putByteArray("future", futureBytes); putByteArray("malformed", hostileBytes)
        }
        val result = io { checkNotNull(context.contentResolver.call(authority + ".control", "configure", null, extras)) }
        run = checkNotNull(result.getString("run"))
        check(Regex("[a-f0-9]{32}").matches(run))
        for (kind in listOf("valid", "future", "malformed")) {
            assertEquals(PackageManager.PERMISSION_DENIED, permission(sourceUri(kind), Intent.FLAG_GRANT_READ_URI_PERMISSION))
        }
        assertNoPersistedGrant()
    }
    private fun withCase(action: (World, SavedStory) -> Unit) = safe {
        deadline = SystemClock.elapsedRealtime() + 75_000
        defaultDatabase() // Exact isolated target check precedes all source/provider setup.
        val world = sourceFixture()
        val baseline = native(defaultDatabase()) { _, gateway, _ ->
            gateway.initialize(); gateway.createSaved(); send(gateway, BASELINE, 0)
        }
        assertFalse(productSnapshot().containsKey(world.root.story))
        configure(world)
        var scenario: ActivityScenario<MainActivity>? = null
        var primary: Throwable? = null
        try {
            val active = ActivityScenario.launch<MainActivity>(Intent(context, MainActivity::class.java))
            scenario = active
            active.onActivity { activity ->
                assertNotNull(activity.constructedWorkspaceTransport)
                model = ViewModelProvider(activity)[ShellViewModel::class.java]
            }
            settled(); select(baseline)
            action(world, baseline)
        } catch (failure: Throwable) { primary = failure; throw failure }
        finally {
            var cleanupFailure: Throwable? = null
            fun close(action: () -> Unit) {
                try { action() } catch (cleanup: Throwable) {
                    cleanupFailure?.addSuppressed(cleanup) ?: run { cleanupFailure = cleanup }
                }
            }
            close {
                if (pickerRequested && activePackage() in documents) {
                    instrumentation.sendKeyDownUpSync(KeyEvent.KEYCODE_BACK)
                    awaitApplication(); pickerRequested = false
                }
                if (::model.isInitialized && model.archive.value.visible) {
                    compose.onNodeWithTag("archive-close").performClick()
                    await { !model.archive.value.visible && !model.state.value.busy }
                }
                drainedStats(); assertNoPersistedGrant()
            }
            close { scenario?.close() } // Product adapter close is asynchronous, not joined-drain proof.
            cleanupFailure?.let { primary?.addSuppressed(it) ?: throw it }
        }
    }

    @Test fun chooserRoundTripPreservesRetiredParentReceiptsAndReservedIds() = withCase { world, baseline ->
        val before = productSnapshot()
        openArchive(); selectImport("Valid archive.json")
        assertPreview(world)
        assertEquals(PackageManager.PERMISSION_GRANTED, permission(sourceUri("valid"), Intent.FLAG_GRANT_READ_URI_PERMISSION))
        assertEquals(before, productSnapshot())
        assertEquals(baseline, model.state.value.selectedStory)
        compose.onNodeWithTag("archive-import-confirm").performScrollTo().performClick()
        await { !model.archive.value.busy && model.archive.value.imported != null }
        assertEquals(baseline, model.state.value.selectedStory)
        val imported = productSnapshot()
        assertPrior(before, imported); assertEquals(before.keys + world.root.story, imported.keys)
        compose.onNodeWithTag("archive-open-imported").performScrollTo().performClick()
        await { !model.archive.value.visible && !model.state.value.busy && model.state.value.selectedStory?.story == world.root.story }
        select(world.child)
        assertRetained(world)
        val expected = io { export(defaultDatabase(), world.child) }
        assertArrayEquals(world.archive, expected)
        val beforeSave = productSnapshot()
        openArchive()
        compose.onNodeWithTag("archive-export-prepare").performScrollTo().performClick()
        await { !model.archive.value.busy && model.archive.value.prepared != null }
        assertPreview(world)
        val output = DocumentsContract.buildDocumentUri(authority, "run-$run:output-1")
        assertEquals(PackageManager.PERMISSION_DENIED, permission(output, Intent.FLAG_GRANT_WRITE_URI_PERMISSION))
        pickerRequested = true
        compose.onNodeWithTag("archive-export-pick").performScrollTo().performClick()
        chooseProviderRoot(); clickDocumentNode { it.text?.toString()?.equals("Save", ignoreCase = true) == true }
        awaitApplication(); pickerRequested = false
        await { !model.archive.value.busy && !model.archive.value.awaitingPicker &&
            model.archive.value.notice?.startsWith("The captured archive was written.") == true }
        val stats = drainedStats()
        assertEquals(1, stats.getInt("created_count")); assertEquals(1, stats.getInt("write_count"))
        assertTrue(stats.getInt("read_count") >= 1)
        assertArrayEquals(expected, stats.getByteArray("created_bytes"))
        assertArrayEquals(world.archive, stats.getByteArray("created_bytes"))
        assertEquals(PackageManager.PERMISSION_GRANTED, permission(output, Intent.FLAG_GRANT_WRITE_URI_PERMISSION))
        assertEquals(PackageManager.PERMISSION_DENIED, permission(sourceUri("valid"), Intent.FLAG_GRANT_WRITE_URI_PERMISSION))
        assertEquals(PackageManager.PERMISSION_DENIED, permission(sourceUri("future"), Intent.FLAG_GRANT_READ_URI_PERMISSION))
        assertEquals(PackageManager.PERMISSION_DENIED, permission(sourceUri("malformed"), Intent.FLAG_GRANT_READ_URI_PERMISSION))
        assertNoPersistedGrant(); closeArchive()
        assertEquals(beforeSave, productSnapshot())
        // Continue only through current production free-text/example and explicit Send controls.
        tag("play-example").performClick(); compose.waitForIdle()
        tag("play-kind-action").assertIsSelected()
        tag("play-input").assert(hasText("I give my last potion to Mira."))
        assertEquals(world.child.branch, checkNotNull(model.state.value.selectedStory).branch)
        tag("play-send").assertIsEnabled().performClick()
        await { !model.state.value.busy && model.state.value.revision == 3L }
        val continued = productSnapshot()
        assertPrior(before, continued)
        assertEquals(imported.keys, continued.keys)
        io { Host(defaultDatabase()).use { host ->
            assertEquals(world.rootView, canonical(view(host, world.root)))
            val child = view(host, world.child.copy(revision = 3))
            assertEquals(3, child.getJSONArray("receipts").length())
            assertFalse(child.getJSONObject("inventory").has("potion"))
            val original = JSONObject(world.childView).getJSONArray("receipts")
            for (i in 0..1) assertEquals(canonical(original.get(i)), canonical(child.getJSONArray("receipts").get(i)))
        } }
        tag("play-send").assertIsEnabled().performClick()
        await { !model.state.value.busy && model.state.value.notice == INVENTORY }
        assertEquals(3L, model.state.value.revision)
        assertEquals(continued, productSnapshot())
        assertRetained(world, childHead = 3)
    }

    @Test fun hostileRetainedArchivesAndConflictsCannotMutateExistingStories() = withCase { world, baseline ->
        val before = productSnapshot()
        openArchive()
        for ((title, notice) in listOf("Future archive.json" to UNSUPPORTED, "Malformed archive.json" to INVALID)) {
            selectImport(title)
            assertEquals(notice, model.archive.value.notice)
            assertNull(model.archive.value.prepared); assertNull(model.archive.value.imported)
            compose.onNodeWithTag("archive-import-confirm").assertDoesNotExist()
            compose.onNodeWithTag("archive-import-pick").performScrollTo().assertIsEnabled()
            assertEquals(before, productSnapshot()); drainedStats()
        }
        selectImport("Valid archive.json"); assertPreview(world)
        compose.onNodeWithTag("archive-cancel").performClick()
        await { !model.archive.value.busy && model.archive.value.prepared == null }
        closeArchive(); assertEquals(before, productSnapshot())
        openArchive(); selectImport("Valid archive.json"); assertPreview(world)
        compose.onNodeWithTag("archive-import-confirm").performScrollTo().performClick()
        await { !model.archive.value.busy && model.archive.value.imported != null }
        assertEquals(baseline, model.state.value.selectedStory)
        closeArchive()
        val imported = productSnapshot()
        assertPrior(before, imported); assertEquals(before.keys + world.root.story, imported.keys)
        openArchive(); selectImport("Valid archive.json"); assertPreview(world)
        compose.onNodeWithTag("archive-import-confirm").performScrollTo().performClick()
        await { !model.archive.value.busy && model.archive.value.notice == CONFLICT }
        assertNull(model.archive.value.prepared); assertNull(model.archive.value.imported)
        compose.onNodeWithTag("archive-import-confirm").assertDoesNotExist()
        assertEquals(imported, productSnapshot())
        closeArchive()
        val stats = drainedStats()
        assertEquals(0, stats.getInt("created_count")); assertEquals(0, stats.getInt("write_count"))
        assertNoPersistedGrant()
        assertEquals(imported, productSnapshot())
    }

    private fun assertPreview(world: World) {
        val p = checkNotNull(model.archive.value.prepared).preview
        assertEquals(2, p.version); assertEquals(world.root.story, p.storyId)
        assertEquals(mapOf(world.root.branch to 1L, world.parent.branch to 2L, world.child.branch to 2L), p.branchHeads)
        assertEquals(listOf(world.parent.branch), p.retiredBranchIds)
        assertFalse(p.noncommittedWorkflowTransferred)
        compose.onNodeWithText("Archive format · 2").performScrollTo().assertIsDisplayed()
        compose.onNodeWithText("${world.parent.branch} · retained ancestry through 2 (not playable)").performScrollTo().assertIsDisplayed()
        compose.onNodeWithText("Reserved deleted timeline IDs: ${world.parent.branch}. Import preserves these IDs and retained ancestry.")
            .performScrollTo().assertIsDisplayed()
    }
    private fun assertRetained(world: World, childHead: Long = 2) {
        val before = productSnapshot()
        native(defaultDatabase()) { host, gateway, forks ->
            assertEquals(world.rootView, canonical(view(host, world.root)))
            if (childHead == 2L) {
                val child = view(host, world.child)
                assertEquals(world.childView, canonical(child)); assertInherited(world, child)
            }
            val refused = host.reply(JSONObject().put("op", "resume").put("scope", scope(world.parent)))
            assertEquals("rejected", refused.getString("status")); assertEquals("NotFound", refused.getString("error"))
            gateway.initialize(); gateway.resumeSaved(world.root)
            val binding = checkNotNull(gateway.forkContext(world.root, 1, 0))
            val input = BranchForkInput(binding.parent, world.parent.branch, 1, 1)
            val fork = NativeForkGateway { host.handle }.also { forks += it }
            val registered = fork.register(binding, input, true)
            val completed = fork.run(registered.operation)
            assertEquals(BranchForkPhase.REJECTED, completed.phase); assertEquals("NotFound", completed.error)
        }
        assertEquals(before, productSnapshot())
        if (childHead == 2L) {
            assertEquals(listOf(ROOT_TEXT, PREFIX), model.state.value.messages.filter { it.isPlayer }.map { it.text })
            assertFalse(model.state.value.timelines.any { it.branch == world.parent.branch })
        }
    }

    private fun tag(name: String): SemanticsNodeInteraction {
        compose.onNodeWithTag("story-list").performScrollToNode(hasTestTag(name))
        return compose.onNodeWithTag(name)
    }
    private fun select(story: SavedStory) {
        tag("saved-library").performClick()
        compose.onNodeWithTag("saved-story-${story.story}").performScrollTo().performClick(); settled()
        tag("timeline-library").performClick()
        compose.onNodeWithTag("timeline-${story.branch}").performScrollTo().performClick(); settled()
        assertEquals(story.story, checkNotNull(model.state.value.selectedStory).story)
        assertEquals(story.branch, checkNotNull(model.state.value.selectedStory).branch)
        assertEquals(story.revision, model.state.value.revision)
    }
    private fun settled() { await { model.state.value.let { it.persistent && !it.busy && !it.archiveActive } }; compose.waitForIdle(); assertFalse(model.state.value.recoveryRequired) }
    private fun openArchive() { tag("story-archive").assertIsEnabled().performClick(); compose.onNodeWithTag("archive-dialog").assertIsDisplayed() }
    private fun closeArchive() { compose.onNodeWithTag("archive-close").performClick(); await { !model.archive.value.visible && !model.state.value.busy && !model.state.value.archiveActive }; compose.waitForIdle() }
    private fun selectImport(title: String) {
        pickerRequested = true
        compose.onNodeWithTag("archive-import-pick").performScrollTo().performClick()
        chooseProviderRoot(); clickDocumentNode { it.text?.toString() == title }
        val end = minOf(deadline, SystemClock.elapsedRealtime() + 8_000)
        while (activePackage() in documents && SystemClock.elapsedRealtime() < end) {
            clickIfPresent { it.text?.toString()?.equals("Open", ignoreCase = true) == true }; Thread.yield()
        }
        awaitApplication(); pickerRequested = false
        await { !model.archive.value.awaitingPicker && !model.archive.value.busy &&
            (model.archive.value.prepared != null || model.archive.value.notice != null) }
        drainedStats(); assertNoPersistedGrant()
    }
    private fun chooseProviderRoot() {
        awaitPackage { it in documents }
        clickIfPresent { it.contentDescription?.toString() in setOf("Show roots", "Open navigation drawer", "Show locations") }
        clickDocumentNode { it.text?.toString() == "LocalLore test archives (${instrumentation.context.packageName})" }
    }
    private fun clickDocumentNode(matches: (AccessibilityNodeInfo) -> Boolean) {
        val end = minOf(deadline, SystemClock.elapsedRealtime() + 8_000)
        while (SystemClock.elapsedRealtime() < end) { if (clickIfPresent(matches)) return; Thread.yield() }
        throw AssertionError("Expected document-picker control was not reachable")
    }
    private fun clickIfPresent(matches: (AccessibilityNodeInfo) -> Boolean): Boolean {
        val root = instrumentation.uiAutomation.rootInActiveWindow ?: return false
        if (root.packageName?.toString() !in documents) { root.recycle(); return false }
        var visited = 0
        fun walk(node: AccessibilityNodeInfo, depth: Int): Boolean {
            try {
                if (++visited > 2048 || depth > 32) return false
                if (node.packageName?.toString() in documents && node.isVisibleToUser && matches(node)) {
                    var candidate: AccessibilityNodeInfo? = AccessibilityNodeInfo.obtain(node)
                    try {
                        repeat(6) {
                            val current = candidate ?: return@repeat
                            if (current.packageName?.toString() in documents && current.isEnabled && current.isClickable &&
                                current.performAction(AccessibilityNodeInfo.ACTION_CLICK)) return true
                            candidate = current.parent; current.recycle()
                        }
                    } finally { candidate?.recycle() }
                }
                for (index in 0 until node.childCount) { val child = node.getChild(index) ?: continue; if (walk(child, depth + 1)) return true }
                return false
            } finally { node.recycle() }
        }
        return walk(root, 0)
    }
    private fun activePackage(): String? = instrumentation.uiAutomation.rootInActiveWindow?.let {
        try { it.packageName?.toString() } finally { it.recycle() }
    }
    private fun awaitApplication() = awaitPackage { it == context.packageName }
    private fun awaitPackage(matches: (String?) -> Boolean) {
        val end = minOf(deadline, SystemClock.elapsedRealtime() + 8_000)
        while (SystemClock.elapsedRealtime() < end) { if (matches(activePackage())) return; Thread.yield() }
        throw AssertionError("Expected picker or application did not become active")
    }
    private fun await(condition: () -> Boolean) {
        val remaining = minOf(8_000L, deadline - SystemClock.elapsedRealtime())
        check(remaining > 0) { "Synthetic chooser case budget exhausted" }
        compose.waitUntil(remaining, condition); compose.waitForIdle()
    }
    private fun sourceUri(kind: String) = DocumentsContract.buildDocumentUri(authority, "run-$run:$kind")
    private fun permission(uri: Uri, mode: Int) = context.checkUriPermission(uri, Process.myPid(), Process.myUid(), mode)
    private fun assertNoPersistedGrant() { assertTrue(context.contentResolver.persistedUriPermissions.none { it.uri.authority == authority }) }
    private fun drainedStats(): Bundle {
        val end = minOf(deadline, SystemClock.elapsedRealtime() + 8_000)
        while (SystemClock.elapsedRealtime() < end) {
            val stats = io { checkNotNull(context.contentResolver.call(authority + ".control", "stats", null, null)) }
            if (stats.getInt("active_count") == 0 && stats.getInt("opened_count") == stats.getInt("closed_count")) {
                assertEquals(0, stats.getInt("close_failure_count")); return stats
            }
            Thread.yield()
        }
        throw AssertionError("Provider document owners did not drain")
    }
    private fun <T> io(block: () -> T): T = runBlocking(Dispatchers.IO) { block() }
    private fun strings(values: JSONArray) = (0 until values.length()).map { values.getString(it) }
    private fun payloadHash(envelope: JSONObject): String = MessageDigest.getInstance("SHA-256")
        .digest(canonical(envelope.getJSONObject("payload")).toByteArray(Charsets.UTF_8)).joinToString("") { "%02x".format(it.toInt() and 255) }
    private fun quote(value: String): String = buildString {
        append('"')
        for (c in value) append(when (c) {
            '"' -> "\\\""; '\\' -> "\\\\"; '\b' -> "\\b"; '\t' -> "\\t"; '\n' -> "\\n"; '\u000C' -> "\\f"; '\r' -> "\\r"
            else -> if (c.code < 32) "\\u%04x".format(c.code) else c.toString()
        })
        append('"')
    }
    private fun canonical(value: Any?): String = when (value) {
        is JSONObject -> value.keys().asSequence().toList().sortedWith { a, b ->
            val left = a.toByteArray(Charsets.UTF_8); val right = b.toByteArray(Charsets.UTF_8)
            var compared = 0
            for (i in 0 until minOf(left.size, right.size)) { compared = (left[i].toInt() and 255) - (right[i].toInt() and 255); if (compared != 0) break }
            if (compared == 0) left.size - right.size else compared
        }.joinToString(",", "{", "}") { quote(it) + ":" + canonical(value.get(it)) }
        is JSONArray -> (0 until value.length()).joinToString(",", "[", "]") { canonical(value.get(it)) }
        is String -> quote(value)
        null, JSONObject.NULL -> "null"
        else -> value.toString()
    }
    private fun safe(block: () -> Unit) {
        try { block() } catch (failure: AssertionError) { throw failure }
        catch (failure: Exception) { throw AssertionError("Synthetic retained chooser boundary failed (${failure.javaClass.simpleName})").also { it.stackTrace = failure.stackTrace } }
    }
}

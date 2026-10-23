/* Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0 */
package org.locallore.app

import android.accessibilityservice.AccessibilityServiceInfo
import android.content.Context
import android.content.ContextWrapper
import android.content.Intent
import android.content.pm.PackageManager
import android.os.Bundle
import android.os.Looper
import android.os.Process
import android.os.SystemClock
import android.provider.DocumentsContract
import android.view.KeyEvent
import android.view.accessibility.AccessibilityNodeInfo
import androidx.activity.ComponentActivity
import androidx.activity.result.ActivityResultLauncher
import androidx.activity.result.contract.ActivityResultContracts
import androidx.compose.runtime.collectAsState
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.setValue
import androidx.compose.ui.test.*
import androidx.compose.ui.test.junit4.createAndroidComposeRule
import androidx.lifecycle.ViewModelStore
import androidx.test.ext.junit.runners.AndroidJUnit4
import androidx.test.platform.app.InstrumentationRegistry
import java.io.Closeable
import java.io.File
import java.nio.ByteBuffer
import java.nio.channels.FileChannel
import java.nio.file.Files
import java.nio.file.LinkOption
import java.nio.file.StandardOpenOption
import java.security.MessageDigest
import java.util.concurrent.atomic.AtomicInteger
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.runBlocking
import kotlinx.coroutines.withContext
import org.json.JSONObject
import org.junit.Rule
import org.junit.Test
import org.junit.runner.RunWith
import org.locallore.app.ui.ArchiveDialog
import org.locallore.app.ui.LocalLoreScreen

/** Verification-only symbol; the dedicated capped APK supplies it. No production JNI expansion. */
internal object NativeArchiveCapacityFixture {
    init { NativeWorkspace }
    external fun run(root: String, mode: String): String
}

/** Real Compose/gateway/picker in a ComponentActivity test host, not MainActivity qualification. */
@RunWith(AndroidJUnit4::class)
@Suppress("DEPRECATION")
class ArchiveCapacityActivityTest {
    @get:Rule val compose = createAndroidComposeRule<ComponentActivity>()
    private val instrumentation get() = InstrumentationRegistry.getInstrumentation()
    private val context get() = instrumentation.targetContext
    private val authority get() = instrumentation.context.packageName + ".chooser"
    private val documents = setOf("com.android.documentsui", "com.google.android.documentsui")
    private lateinit var root: File
    private lateinit var run: String
    private lateinit var isolated: Context
    private lateinit var source: ByteArray
    private lateinit var model: ShellViewModel
    private lateinit var store: ViewModelStore
    private lateinit var recorder: RecordingArchive
    private lateinit var launcher: ActivityResultLauncher<Array<String>>
    private var shown by mutableStateOf<ShellViewModel?>(null)
    private var pickerRequested = false
    private var providerRun: String? = null
    private val fullCount = AtomicInteger()
    private val fullGuidance = "Local storage is full. Close to refresh the library. Free storage and validate the archive again before retrying."

    @Test fun storageFullThenCacheReliefAndFreshImport(): Unit { safe {
        verify(context.packageName == "org.locallore.app.archivecapacity", "Capacity test requires the dedicated verification package")
        run = requireNotNull(InstrumentationRegistry.getArguments().getString("archive_capacity_run"))
        verify(Regex("[a-z0-9-]{1,48}").matches(run), "Invalid capacity run")
        val setup = io {
            val parent = File(context.noBackupFilesDir.canonicalFile, "archive-capacity")
            if (!Files.exists(parent.toPath(), LinkOption.NOFOLLOW_LINKS)) Files.createDirectory(parent.toPath())
            realDirectory(parent); root = File(parent, run)
            verify(!Files.exists(root.toPath(), LinkOption.NOFOLLOW_LINKS), "Capacity run must be fresh")
            val result = fixture("setup"); realDirectory(root)
            verify(readBounded(File(root, "owner-v1"), 4096).contentEquals("locallore-archive-capacity-v1".toByteArray(Charsets.US_ASCII)),
                "Capacity owner marker mismatch")
            source = readBounded(File(root, "archive.json"), 131_072)
            result
        }
        verify(setup.getLong("source_revision") == 2L && setup.getInt("cache_count") >= 2 && !setup.getBoolean("imported"),
            "Native setup must provide the original unimported capacity fixture")
        isolated = object : ContextWrapper(context) {
            override fun getApplicationContext(): Context = this
            override fun getNoBackupFilesDir(): File = root
        }
        val info = instrumentation.uiAutomation.serviceInfo
        val originalFlags = info.flags
        info.flags = info.flags or AccessibilityServiceInfo.FLAG_REPORT_VIEW_IDS
        instrumentation.uiAutomation.serviceInfo = info
        try {
            compose.activityRule.scenario.onActivity { activity ->
                launcher = activity.activityResultRegistry.register("capacity-import", ActivityResultContracts.OpenDocument()) { uri ->
                    if (uri == null) model.completeArchiveImport(null)
                    else model.completeArchiveImport { readArchiveDocument(context.contentResolver, uri) }
                }
            }
            newOwner()
            compose.setContent {
                shown?.let { current ->
                    val state by current.state.collectAsState()
                    val archive by current.archive.collectAsState()
                    LocalLoreScreen(state, current::submit, current::setMode, current::cancel, current::reset,
                        onResume = current::resume, onRecover = current::recover, archiveAvailable = true, onArchive = current::openArchive) {
                        current.archiveController?.let { controller ->
                            ArchiveDialog(archive, controller::dismiss, controller::cancel, controller::prepareExport,
                                onImportPicker = {
                                    if (current.beginArchiveImportPicker()) {
                                        try { launcher.launch(arrayOf("application/json", "application/octet-stream", "text/plain")) }
                                        catch (_: Exception) { current.archiveImportPickerFailed() }
                                    }
                                }, onExportPicker = {}, onConfirmImport = controller::confirmImport, onOpenImported = controller::openImported)
                        }
                    }
                }
            }
            awaitIdleControl(setup)
            val original = model.state.value
            configureProvider(); openArchive(); selectValid()
            val token = requireNotNull(model.archive.value.prepared).token
            compose.onNodeWithTag("archive-import-confirm").performScrollTo().performClick()
            compose.waitUntil(15_000) { !model.archive.value.busy && fullCount.get() > 0 }
            compose.onNodeWithTag("archive-notice").performScrollTo().assertTextEquals(fullGuidance)
            compose.onNodeWithTag("archive-import-confirm").assertDoesNotExist()
            compose.onNodeWithTag("archive-import-pick").performScrollTo().assertIsEnabled()
            compose.onNodeWithTag("archive-close").assertIsEnabled()
            verify(model.archive.value.imported == null && sameCanon(original, model.state.value) && model.state.value.archiveActive,
                "Full must leave the prior accepted state and archive guard intact")
            io {
                try { recorder.delegate.commitImport(token); throw CapacityFailure("Consumed Full token was reused") }
                catch (failure: ArchiveFailure) { verify(failure.category == "InvalidToken", "Full must consume its native capability") }
            }
            closeArchive(); drainedStats(); disposeOwner(); archiveOwnerFence()
            val full = io { fixture("check-full") }
            verify(!full.getBoolean("imported") && full.getBoolean("canonical_unchanged"), "Full must preserve all native fixture baselines")
            val relief = io { fixture("relieve") }
            verify(relief.getBoolean("canonical_unchanged") && !relief.getBoolean("imported") &&
                relief.getInt("cache_count") in 1 until setup.getInt("cache_count") &&
                relief.getLong("max_page_count") == setup.getLong("max_page_count"), "Relief must remove only eligible derived caches under the same cap")

            newOwner(); awaitIdleControl(setup)
            verify(sameCanon(original, model.state.value), "Fresh owners must reopen the unchanged control story")
            configureProvider(); openArchive(); selectValid()
            compose.onNodeWithTag("archive-import-confirm").performScrollTo().performClick()
            compose.waitUntil(15_000) { !model.archive.value.busy && model.archive.value.imported != null }
            verify(sameCanon(original, model.state.value), "Successful import must still require explicit Open")
            val imported = io { fixture("check-imported") }
            verify(imported.getBoolean("imported") && imported.getBoolean("archive_exact") && imported.getBoolean("canonical_unchanged"),
                "Native reexport must equal the source before continuation and preserve control canon")
            val sourceScope = scope(setup.getString("source_story"), setup.getString("source_branch"))
            verify(source.contentEquals(io { capture(sourceScope, 2) }), "Reopened native archive must equal the original source before play")
            compose.onNodeWithTag("archive-open-imported").performScrollTo().performClick()
            compose.waitUntil(15_000) { !model.state.value.busy && !model.archive.value.visible &&
                model.state.value.selectedStory?.story == setup.getString("source_story") && model.state.value.revision == 2L }
            tag("give-potion").performClick()
            compose.waitUntil(15_000) { !model.state.value.busy && model.state.value.revision == 3L }
            val accepted = model.state.value
            tag("give-potion").performClick(); compose.waitUntil(15_000) { !model.state.value.busy }
            verify(sameCanon(accepted, model.state.value) && model.state.value.notice?.contains("no longer hold") == true,
                "Recovered import must accept one gift and refuse duplicate spending")
            io {
                Host(database()).use { host ->
                    val session = host.ok(command("resume").put("scope", sourceScope)).getString("session")
                    val snapshot = host.ok(command("play_snapshot").put("session", session).put("scope", sourceScope).put("expected_revision", 3))
                    verify(snapshot.getLong("revision") == 3L && snapshot.getJSONArray("receipts").length() == 3 &&
                        !snapshot.getJSONObject("inventory").has("potion"), "Fresh Host must reopen exactly one continued gift")
                    val control = scope(setup.getString("control_story"), setup.getString("control_branch"))
                    val controlSession = host.ok(command("resume").put("scope", control)).getString("session")
                    verify(host.ok(command("play_snapshot").put("session", controlSession).put("scope", control)
                        .put("expected_revision", setup.getLong("control_revision"))).getLong("revision") == original.revision,
                        "Original control head must remain unchanged after continuation")
                }
            }
            drainedStats(); assertNoPersistedGrant(); disposeOwner(); archiveOwnerFence()
            io {
                val verified = JSONObject().put("version", 1).put("run", run).put("status", "verified")
                    .put("archive_sha256", sha256(source)).put("source_revision", 2).put("continued_revision", 3)
                    .put("full_count", fullCount.get()).put("cache_only_relief", true)
                FileChannel.open(File(root, "capacity-verified.json").toPath(), StandardOpenOption.CREATE_NEW, StandardOpenOption.WRITE).use { channel ->
                    val buffer = ByteBuffer.wrap(verified.toString().toByteArray(Charsets.UTF_8))
                    while (buffer.hasRemaining()) channel.write(buffer)
                    channel.force(true)
                }
            }
        } finally {
            try {
                if (pickerRequested && activePackage() in documents) {
                    verify(activePackage() in documents, "Cleanup Back requires foreground DocumentsUI")
                    instrumentation.sendKeyDownUpSync(KeyEvent.KEYCODE_BACK); awaitPackage { it == context.packageName }
                }
                if (::store.isInitialized) disposeOwner()
                if (::launcher.isInitialized) instrumentation.runOnMainSync { launcher.unregister() }
                if (providerRun != null) drainedStats()
                archiveOwnerFence()
            } finally {
                val restored = instrumentation.uiAutomation.serviceInfo; restored.flags = originalFlags
                instrumentation.uiAutomation.serviceInfo = restored
            }
        }
    } }

    private inner class RecordingArchive(val delegate: ArchiveGateway) : ArchiveGateway by delegate {
        override suspend fun commitImport(token: Long): ArchiveImported = try { delegate.commitImport(token) }
        catch (failure: ArchiveFailure) { if (failure.category == "Full") fullCount.incrementAndGet(); throw failure }
    }
    private fun newOwner(): Unit = instrumentation.runOnMainSync {
        recorder = RecordingArchive(NativeArchiveGateway(isolated))
        model = ShellViewModel(DurableGateway(NativeWorkspaceTransport(isolated)), archiveGateway = recorder)
        store = ViewModelStore().also { it.put("capacity-model", model) }; shown = model
    }
    private fun disposeOwner(): Unit { instrumentation.runOnMainSync { shown = null; store.clear() }; compose.waitForIdle() }
    private fun awaitIdleControl(setup: JSONObject): Unit {
        compose.waitUntil(15_000) { !model.state.value.busy && model.state.value.persistent && !model.state.value.recoveryRequired }
        verify(model.state.value.selectedStory?.story == setup.getString("control_story") && model.state.value.revision == setup.getLong("control_revision"),
            "Real gateway must select the original capacity control story")
    }
    private fun fixture(mode: String): JSONObject {
        val reply = NativeArchiveCapacityFixture.run(root.absolutePath, mode)
        verify(reply.toByteArray(Charsets.UTF_8).size <= 4096, "Native fixture reply exceeds its bound")
        val result = JSONObject(reply)
        verify(result.getInt("version") == 1 && result.getString("status") == "ok" && result.getString("mode") == mode,
            "Native capacity fixture mode failed")
        return result
    }
    private fun database() = File(root, "workspace-v1/stories.sqlite3")
    private fun archiveOwnerFence(): Unit = io {
        val staging = File(root, "lease-staging")
        if (!Files.exists(staging.toPath(), LinkOption.NOFOLLOW_LINKS)) Files.createDirectory(staging.toPath())
        realDirectory(staging)
        val deadline = SystemClock.elapsedRealtime() + 10_000
        var drained = false
        while (!drained && SystemClock.elapsedRealtime() < deadline) {
            val handles = mutableListOf<Long>()
            try {
                repeat(4) { val id = NativeArchive.open(database().canonicalPath, staging.canonicalPath); if (id > 0) handles += id }
                drained = handles.size == 4
            } finally { handles.forEach(NativeArchive::close) }
            if (!drained) Thread.yield()
        }
        verify(drained && staging.listFiles()?.isEmpty() == true, "Disposed archive owners must release all four real native leases")
        // The workspace transport closes on its own IO worker. Archive lease availability
        // cannot establish that this independent registry has released its old owner.
        val workspaceDeadline = SystemClock.elapsedRealtime() + 10_000
        var workspaceDrained = false
        while (!workspaceDrained && SystemClock.elapsedRealtime() < workspaceDeadline) {
            val handles = mutableListOf<Long>()
            try {
                repeat(4) {
                    val id = NativeWorkspace.open(database().canonicalPath)
                    if (id > 0) handles += id
                }
                workspaceDrained = handles.size == 4
            } finally { handles.forEach(NativeWorkspace::close) }
            if (!workspaceDrained) Thread.yield()
        }
        verify(workspaceDrained, "Disposed workspace owners must release all four real native leases")
    }
    private fun capture(scope: JSONObject, head: Long): ByteArray {
        val staging = File(root, "parity-staging").also { Files.createDirectory(it.toPath()) }
        val handle = NativeArchive.open(database().canonicalPath, staging.canonicalPath)
        verify(handle > 0, "Parity native owner did not open")
        try {
            val request = JSONObject().put("story", scope.getString("story")).put("branch", scope.getString("branch"))
                .put("expected_revision", head).toString().toByteArray(Charsets.UTF_8)
            return NativeArchive.exportBytes(handle, accepted(NativeArchive.prepareExport(handle, request)).getLong("token"))
        } finally { NativeArchive.close(handle); verify(staging.listFiles()?.isEmpty() == true, "Parity staging must drain") }
    }
    private inner class Host(database: File) : Closeable {
        private val handle = NativeWorkspace.open(database.canonicalPath).also { verify(it > 0, "Fresh Host owner did not open") }
        fun ok(command: JSONObject): JSONObject = accepted(NativeWorkspace.call(handle,
            JSONObject().put("version", 1).put("command", command).toString().toByteArray(Charsets.UTF_8)))
        override fun close(): Unit = NativeWorkspace.close(handle)
    }
    private fun command(op: String) = JSONObject().put("op", op)
    private fun scope(story: String, branch: String) = JSONObject().put("story", story).put("branch", branch)
    private fun accepted(bytes: ByteArray): JSONObject {
        verify(bytes.size in 1..262_144, "Native reply exceeds its bound")
        val reply = JSONObject(bytes.toString(Charsets.UTF_8))
        verify(reply.getInt("version") == 1 && reply.getString("status") == "ok", "Native capacity operation failed")
        return reply.getJSONObject("data")
    }
    private fun sameCanon(left: ShellState, right: ShellState): Boolean = left.selectedStory == right.selectedStory &&
        left.revision == right.revision && left.messages == right.messages && left.potionOwner == right.potionOwner && !right.recoveryRequired
    private fun realDirectory(file: File): Unit = verify(Files.isDirectory(file.toPath(), LinkOption.NOFOLLOW_LINKS) &&
        !Files.isSymbolicLink(file.toPath()) && file.absoluteFile == file.canonicalFile, "Capacity directory must be real and nonlinked")
    private fun readBounded(file: File, cap: Int): ByteArray {
        verify(Files.isRegularFile(file.toPath(), LinkOption.NOFOLLOW_LINKS) && !Files.isSymbolicLink(file.toPath()) &&
            file.absoluteFile == file.canonicalFile && file.length() in 1..cap.toLong(), "Capacity input must be a bounded regular nonlink")
        return file.inputStream().use { input ->
            val result = java.io.ByteArrayOutputStream(); val buffer = ByteArray(8192)
            while (result.size() < cap) { val count = input.read(buffer, 0, minOf(buffer.size, cap - result.size())); if (count < 0) break
                if (count == 0) { val one = input.read(); if (one < 0) break; result.write(one) } else result.write(buffer, 0, count) }
            verify(input.read() == -1 && result.size() > 0, "Capacity input exceeds its bound"); result.toByteArray()
        }
    }
    private fun sha256(bytes: ByteArray): String = MessageDigest.getInstance("SHA-256").digest(bytes)
        .joinToString("") { (it.toInt() and 255).toString(16).padStart(2, '0') }
    private fun <T> io(block: suspend () -> T): T = runBlocking { withContext(Dispatchers.IO) {
        verify(Looper.myLooper() != Looper.getMainLooper(), "Capacity native work must stay off Main"); block()
    } }
    private class CapacityFailure(message: String) : AssertionError(message)
    private fun safe(block: () -> Unit): Unit {
        try { block() } catch (failure: CapacityFailure) { throw failure }
        catch (failure: Throwable) { if (failure is VirtualMachineError || failure is ThreadDeath) throw failure
            throw AssertionError("Capacity test boundary failed (${failure.javaClass.simpleName})").also { it.stackTrace = failure.stackTrace } }
    }
    private fun verify(condition: Boolean, message: String): Unit { if (!condition) throw CapacityFailure(message) }

    private fun openArchive(): Unit { tag("story-archive").assertIsEnabled().performClick(); compose.onNodeWithTag("archive-dialog").assertIsDisplayed() }
    private fun closeArchive(): Unit {
        compose.onNodeWithTag("archive-close").performClick()
        compose.waitUntil(15_000) { !model.archive.value.visible && !model.state.value.busy && !model.state.value.archiveActive }
    }
    private fun tag(name: String): SemanticsNodeInteraction {
        compose.onNodeWithTag("story-list").performScrollToNode(hasTestTag(name)); return compose.onNodeWithTag(name)
    }
    private fun configureProvider(): Unit {
        val extras = Bundle().apply { putByteArray("archive", source)
            putByteArray("future", JSONObject(source.toString(Charsets.UTF_8)).put("version", 999).toString().toByteArray(Charsets.UTF_8))
            putByteArray("malformed", "{\"version\":1,\"version\":1}".toByteArray(Charsets.UTF_8)) }
        providerRun = io { requireNotNull(context.contentResolver.call(authority + ".control", "configure", null, extras)).getString("run") }
        verify(providerRun?.matches(Regex("[a-f0-9]{32}")) == true, "Capacity provider run is invalid")
        val uri = DocumentsContract.buildDocumentUri(authority, "run-$providerRun:valid")
        verify(context.checkUriPermission(uri, Process.myPid(), Process.myUid(), Intent.FLAG_GRANT_READ_URI_PERMISSION) ==
            PackageManager.PERMISSION_DENIED, "New capacity source requires a real chooser grant")
    }
    private fun selectValid(): Unit {
        pickerRequested = true
        compose.onNodeWithTag("archive-import-pick").performScrollTo().performClick(); awaitPackage { it in documents }
        clickIfPresent { it.contentDescription?.toString() in setOf("Show roots", "Open navigation drawer", "Show locations") }
        clickDocumentNode { it.text?.toString() == "LocalLore test archives" }; clickDocumentNode { it.text?.toString() == "Valid archive.json" }
        val deadline = SystemClock.elapsedRealtime() + 10_000
        while (activePackage() in documents && SystemClock.elapsedRealtime() < deadline) {
            clickIfPresent { it.text?.toString()?.equals("Open", true) == true }; Thread.yield() }
        awaitPackage { it == context.packageName }; pickerRequested = false
        compose.waitUntil(15_000) { !model.archive.value.busy && !model.archive.value.awaitingPicker && model.archive.value.prepared != null }
    }
    private fun clickDocumentNode(matches: (AccessibilityNodeInfo) -> Boolean): Unit {
        val deadline = SystemClock.elapsedRealtime() + 10_000
        while (SystemClock.elapsedRealtime() < deadline) { if (clickIfPresent(matches)) return; Thread.yield() }
        throw CapacityFailure("Expected capacity picker control was not reachable")
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
                    try { repeat(6) { val current = candidate ?: return@repeat
                        if (current.packageName?.toString() in documents && current.isEnabled && current.isClickable &&
                            current.performAction(AccessibilityNodeInfo.ACTION_CLICK)) return true
                        candidate = current.parent; current.recycle() } } finally { candidate?.recycle() }
                }
                for (index in 0 until node.childCount) { val child = node.getChild(index) ?: continue; if (walk(child, depth + 1)) return true }
                return false
            } finally { node.recycle() }
        }
        return walk(root, 0)
    }
    private fun activePackage(): String? = instrumentation.uiAutomation.rootInActiveWindow?.let {
        try { it.packageName?.toString() } finally { it.recycle() } }
    private fun awaitPackage(matches: (String?) -> Boolean): Unit {
        val deadline = SystemClock.elapsedRealtime() + 10_000
        while (SystemClock.elapsedRealtime() < deadline) { if (matches(activePackage())) return; Thread.yield() }
        throw CapacityFailure("Expected capacity picker or host did not become active")
    }
    private fun drainedStats(): Unit {
        val deadline = SystemClock.elapsedRealtime() + 10_000
        while (SystemClock.elapsedRealtime() < deadline) {
            val stats = io { requireNotNull(context.contentResolver.call(authority + ".control", "stats", null, null)) }
            if (stats.getInt("active_count") == 0 && stats.getInt("opened_count") == stats.getInt("closed_count")) {
                verify(stats.getInt("close_failure_count") == 0, "Capacity document descriptors must close successfully"); return }
            Thread.yield()
        }
        throw CapacityFailure("Capacity document descriptors did not drain")
    }
    private fun assertNoPersistedGrant(): Unit = verify(context.contentResolver.persistedUriPermissions.none { it.uri.authority == authority },
        "Capacity test must not retain a persisted document grant")
}

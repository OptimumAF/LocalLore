/* Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0 */
package org.locallore.app

import android.accessibilityservice.AccessibilityServiceInfo
import android.content.Intent
import android.content.pm.PackageManager
import android.os.Looper
import android.os.Process
import android.os.SystemClock
import android.provider.DocumentsContract
import android.view.KeyEvent
import android.view.accessibility.AccessibilityNodeInfo
import androidx.compose.ui.test.*
import androidx.compose.ui.test.junit4.createAndroidComposeRule
import androidx.lifecycle.ViewModelProvider
import androidx.test.ext.junit.runners.AndroidJUnit4
import androidx.test.platform.app.InstrumentationRegistry
import androidx.test.runner.lifecycle.ActivityLifecycleMonitorRegistry
import androidx.test.runner.lifecycle.Stage
import java.io.ByteArrayOutputStream
import java.io.Closeable
import java.io.File
import java.nio.ByteBuffer
import java.nio.channels.FileChannel
import java.nio.file.Files
import java.nio.file.LinkOption
import java.nio.file.StandardOpenOption
import java.security.MessageDigest
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.runBlocking
import kotlinx.coroutines.withContext
import org.json.JSONArray
import org.json.JSONObject
import org.junit.Rule
import org.junit.Test
import org.junit.runner.RunWith

/** External Android app force-stop only; not a low-memory, power-loss, or mid-transaction kill. */
@RunWith(AndroidJUnit4::class)
@Suppress("DEPRECATION")
class ArchiveRecoveryActivityTest {
    @get:Rule val compose = createAndroidComposeRule<MainActivity>()
    private val instrumentation get() = InstrumentationRegistry.getInstrumentation()
    private val context get() = instrumentation.targetContext
    private val authority get() = instrumentation.context.packageName + ".chooser"
    private val documents = setOf("com.android.documentsui", "com.google.android.documentsui")
    private val owner = "locallore-archive-recovery-v1"
    private lateinit var model: ShellViewModel
    private lateinit var activity: MainActivity
    private lateinit var root: File
    private lateinit var run: String
    private lateinit var phase: String
    private lateinit var mode: String
    private lateinit var source: ByteArray
    private lateinit var baseline: JSONObject
    private lateinit var providerRun: String
    private var pickerRequested = false
    private var accessibilityFlags: Int? = null

    @Test fun processRecovery(): Unit { safe {
        val args = InstrumentationRegistry.getArguments()
        phase = requireNotNull(args.getString("archive_recovery_phase"))
        run = requireNotNull(args.getString("archive_recovery_run"))
        verify(phase in setOf("arm-preview", "verify-preview", "arm-committed", "verify-committed"), "Invalid recovery phase")
        verify(Regex("[a-z0-9-]{1,48}").matches(run), "Invalid recovery run")
        mode = if (phase.endsWith("preview")) "preview" else "committed"
        root = io { ownedRoot(phase.startsWith("arm-")) }
        compose.activityRule.scenario.onActivity { activity = it; model = ViewModelProvider(it)[ShellViewModel::class.java] }
        compose.waitUntil(10_000) { !model.state.value.busy && model.state.value.persistent &&
            !model.state.value.recoveryRequired && model.state.value.selectedStory != null }
        // This must precede every new NativeArchive allocation or fresh picker validation.
        verify(model.archive.value == ArchiveUiState() && !model.state.value.archiveActive,
            "A new process must not revive archive consent, picker state, or an import-success dialog")
        val info = instrumentation.uiAutomation.serviceInfo
        accessibilityFlags = info.flags
        info.flags = info.flags or AccessibilityServiceInfo.FLAG_REPORT_VIEW_IDS
        instrumentation.uiAutomation.serviceInfo = info
        if (phase.startsWith("arm-")) arm() else {
            try { verifyRestart() } finally { cleanupVerification() }
            io { writeNew("verified-v1.json", publicMarker("verified").toString().toByteArray(Charsets.UTF_8), 4096) }
        }
    } }

    private fun arm(): Unit {
        val original = requireNotNull(model.state.value.selectedStory)
        val originalScope = scope(original.story, original.branch)
        val directory = io { newDirectory(root, "fixture") }
        baseline = io {
            val catalog = library()
            val snapshot = snapshot(originalScope, original.revision)
            val sourceScope = Host(File(directory, "stories.sqlite3")).use { host ->
                val created = host.ok(command("create").put("seed", "lantern-quay-v1"))
                val createdScope = created.getJSONObject("scope")
                host.commit(created.getString("session"), request(createdScope, "recovery-prefix-v1", 0,
                    command("wait").put("ticks", 1)))
                source = export(File(directory, "stories.sqlite3"), "source-staging", createdScope, 1)
                createdScope
            }
            JSONObject().put("version", 1).put("run", run).put("mode", mode).put("catalog", catalog)
                .put("original", JSONObject().put("scope", originalScope).put("revision", original.revision).put("snapshot", snapshot))
                .put("source_scope", sourceScope).also {
                    writeNew("archive.json", source, 131_072)
                    writeNew("baseline.json", it.toString().toByteArray(Charsets.UTF_8), 1_048_576)
                }
        }
        configureProvider()
        openArchive(); selectValid()
        verify(model.archive.value.prepared != null && model.archive.value.imported == null, "Arm must hold a validated uncommitted preview")
        verify(sameJson(baseline.getJSONArray("catalog"), io { library() }), "Preview must not import before explicit consent")
        verifyOriginalSnapshot()
        if (mode == "committed") {
            compose.onNodeWithTag("archive-import-confirm").performScrollTo().performClick()
            compose.waitUntil(10_000) { !model.archive.value.busy && model.archive.value.imported != null }
            verifyCommittedCatalog()
            verifyOriginalSnapshot()
            compose.onNodeWithTag("archive-open-imported").performScrollTo().assertIsDisplayed()
        } else compose.onNodeWithTag("archive-import-confirm").performScrollTo().assertIsDisplayed()
        drainedStats()
        compose.onNodeWithTag("archive-dialog").assertIsDisplayed()
        verify(model.state.value.archiveActive && !model.archive.value.busy && !model.archive.value.awaitingPicker,
            "Arm must keep the live archive guard and ready UI")
        verify(model.state.value.selectedStory == original && model.state.value.revision == original.revision,
            "Armed import must not open the imported story without explicit consent")
        instrumentation.runOnMainSync {
            verify(ActivityLifecycleMonitorRegistry.getInstance().getLifecycleStageOf(activity) == Stage.RESUMED,
                "Arm Activity must be resumed before readiness publication")
        }
        io { writeNew("ready-v1.json", publicMarker("ready").toString().toByteArray(Charsets.UTF_8), 4096) }
        // No teardown or test success before the coordinator observes the marker and live PID,
        // then force-stops this owned test package. A surviving arm is a failure, never evidence.
        val deadline = SystemClock.elapsedRealtime() + 110_000
        while (SystemClock.elapsedRealtime() < deadline) SystemClock.sleep(100)
        throw RecoveryFailure("Coordinator did not stop the armed process within its bounded window")
    }

    private fun verifyRestart(): Unit {
        val ready = io {
            source = readFile("archive.json", 131_072)
            baseline = JSONObject(readFile("baseline.json", 1_048_576).toString(Charsets.UTF_8))
            keys(baseline, setOf("version", "run", "mode", "catalog", "original", "source_scope"))
            verify(baseline.getInt("version") == 1 && baseline.getString("run") == run && baseline.getString("mode") == mode,
                "Recovery baseline must belong to this exact run and mode")
            val ready = JSONObject(readFile("ready-v1.json", 4096).toString(Charsets.UTF_8))
            keys(ready, setOf("version", "run", "phase", "pid", "archive_sha256", "status"))
            verify(ready.getInt("version") == 1 && ready.getString("run") == run && ready.getString("phase") == "arm-$mode" &&
                ready.getString("status") == "ready" && ready.getInt("pid") > 0 && ready.getInt("pid") != Process.myPid() &&
                ready.getString("archive_sha256") == sha256(source), "Verification must use the original archive and a new process")
            ready
        }
        restoreOriginal()
        verifyOriginalSnapshot()
        if (mode == "preview") {
            verify(sameJson(baseline.getJSONArray("catalog"), io { library() }), "Uncommitted preview must not survive as an imported story")
            configureProvider(); openArchive(); selectValid()
            verify(model.archive.value.prepared != null && model.archive.value.imported == null, "New validation must produce a fresh preview")
            compose.onNodeWithTag("archive-cancel").performClick()
            compose.waitUntil(10_000) { !model.archive.value.busy && model.archive.value.prepared == null }
            closeArchive(); drainedStats()
            verify(sameJson(baseline.getJSONArray("catalog"), io { library() }), "Cancelling fresh validation must leave the catalog unchanged")
        } else {
            verifyCommittedCatalog()
            val sourceScope = baseline.getJSONObject("source_scope")
            verify(source.contentEquals(io { export(defaultDatabase(), "restored-parity-staging", sourceScope, 1) }),
                "Restored committed archive must exactly match the source before continuation")
            // Resume through the actual saved-story UI; no old session or archive capability is reused.
            val imported = model.state.value.stories.single { it.story == sourceScope.getString("story") && it.branch == sourceScope.getString("branch") }
            tag("saved-library").performClick()
            compose.onNodeWithText("${imported.title} · ${imported.story} · revision ${imported.revision}").performScrollTo().performClick()
            compose.waitUntil(10_000) { !model.state.value.busy && model.state.value.selectedStory == imported && model.state.value.revision == 1L }
            tag("give-potion").performClick()
            compose.waitUntil(10_000) { !model.state.value.busy && model.state.value.revision == 2L }
            val committed = model.state.value
            tag("give-potion").performClick()
            compose.waitUntil(10_000) { !model.state.value.busy }
            verify(model.state.value.revision == 2L && model.state.value.messages == committed.messages &&
                model.state.value.potionOwner == committed.potionOwner && model.state.value.notice?.contains("no longer hold") == true,
                "Recovered story must accept one gift and reject duplicate spending")
            val reopened = io { snapshot(sourceScope, 2) }
            verify(reopened.getJSONArray("receipts").length() == 2 && !reopened.getJSONObject("inventory").has("potion"),
                "Reopened recovered story must retain exactly the wait and one gift")
            val catalog = io { library() }
            verify(preservesPrior(catalog) && catalog.length() == baseline.getJSONArray("catalog").length() + 1,
                "Continuation must preserve all prior stories and exactly one imported story")
        }
        restoreOriginal(); verifyOriginalSnapshot(); assertNoPersistedGrant()
        verify(Process.myPid() != ready.getInt("pid"), "Verification must remain in the replacement process")
    }

    private fun verifyCommittedCatalog(): Unit {
        val current = io { library() }; val sourceScope = baseline.getJSONObject("source_scope")
        verify(current.length() == baseline.getJSONArray("catalog").length() + 1 && preservesPrior(current),
            "Committed import must persist exactly once without changing prior stories")
        val matches = (0 until current.length()).map { current.getJSONObject(it) }.filter {
            it.getJSONObject("scope").getString("story") == sourceScope.getString("story") }
        verify(matches.size == 1 && sameJson(matches.single().getJSONObject("scope"), sourceScope) && matches.single().getLong("revision") == 1L,
            "Recovered import must retain its original root and accepted head")
    }
    private fun preservesPrior(current: JSONArray): Boolean {
        val previous = baseline.getJSONArray("catalog")
        return (0 until previous.length()).all { old -> (0 until current.length()).any { sameJson(previous.get(old), current.get(it)) } }
    }
    private fun verifyOriginalSnapshot(): Unit {
        val original = baseline.getJSONObject("original")
        verify(sameJson(original.getJSONObject("snapshot"), io { snapshot(original.getJSONObject("scope"), original.getLong("revision")) }),
            "Previously selected accepted state must remain unchanged")
    }
    private fun restoreOriginal(): Unit {
        val original = baseline.getJSONObject("original"); val scope = original.getJSONObject("scope")
        val story = model.state.value.stories.single { it.story == scope.getString("story") && it.branch == scope.getString("branch") }
        compose.activityRule.scenario.onActivity { model.resume(story) }
        compose.waitUntil(10_000) { !model.state.value.busy && model.state.value.selectedStory == story &&
            model.state.value.revision == original.getLong("revision") && !model.state.value.recoveryRequired }
    }
    private fun cleanupVerification(): Unit {
        try {
            if (pickerRequested && activePackage() in documents) {
                verify(activePackage() in documents, "Cleanup Back requires foreground DocumentsUI")
                instrumentation.sendKeyDownUpSync(KeyEvent.KEYCODE_BACK); awaitPackage { it == context.packageName }
            }
            compose.activityRule.scenario.onActivity { model.archiveController?.dismiss() }
            compose.waitUntil(10_000) { !model.archive.value.visible && !model.state.value.busy }
            if (::baseline.isInitialized) restoreOriginal()
            if (::providerRun.isInitialized) drainedStats()
        } finally {
            accessibilityFlags?.let { flags ->
                val info = instrumentation.uiAutomation.serviceInfo; info.flags = flags; instrumentation.uiAutomation.serviceInfo = info
            }
        }
    }

    private fun configureProvider(): Unit {
        val extras = android.os.Bundle().apply {
            putByteArray("archive", source)
            putByteArray("future", JSONObject(source.toString(Charsets.UTF_8)).put("version", 999).toString().toByteArray(Charsets.UTF_8))
            putByteArray("malformed", "{\"version\":1,\"version\":1}".toByteArray(Charsets.UTF_8))
        }
        val result = io { requireNotNull(context.contentResolver.call(authority + ".control", "configure", null, extras)) }
        providerRun = requireNotNull(result.getString("run"))
        verify(Regex("[a-f0-9]{32}").matches(providerRun), "Invalid provider fixture run")
        val uri = DocumentsContract.buildDocumentUri(authority, "run-$providerRun:valid")
        verify(context.checkUriPermission(uri, Process.myPid(), Process.myUid(), Intent.FLAG_GRANT_READ_URI_PERMISSION) ==
            PackageManager.PERMISSION_DENIED, "Fresh source must be denied before system selection")
        assertNoPersistedGrant()
    }
    private fun openArchive(): Unit { tag("story-archive").assertIsEnabled().performClick(); compose.onNodeWithTag("archive-dialog").assertIsDisplayed() }
    private fun closeArchive(): Unit {
        compose.onNodeWithTag("archive-close").performClick()
        compose.waitUntil(10_000) { !model.archive.value.visible && !model.state.value.busy && !model.state.value.archiveActive }
    }
    private fun tag(name: String): SemanticsNodeInteraction {
        compose.onNodeWithTag("story-list").performScrollToNode(hasTestTag(name)); return compose.onNodeWithTag(name)
    }
    private fun selectValid(): Unit {
        pickerRequested = true
        compose.onNodeWithTag("archive-import-pick").performScrollTo().performClick()
        awaitPackage { it in documents }
        clickIfPresent { it.contentDescription?.toString() in setOf("Show roots", "Open navigation drawer", "Show locations") }
        clickDocumentNode { it.text?.toString() == "LocalLore test archives (${instrumentation.context.packageName})" }
        clickDocumentNode { it.text?.toString() == "Valid archive.json" }
        val deadline = SystemClock.elapsedRealtime() + 10_000
        while (activePackage() in documents && SystemClock.elapsedRealtime() < deadline) {
            clickIfPresent { it.text?.toString()?.equals("Open", ignoreCase = true) == true }; Thread.yield()
        }
        awaitPackage { it == context.packageName }; pickerRequested = false
        compose.waitUntil(10_000) { !model.archive.value.awaitingPicker && !model.archive.value.busy &&
            (model.archive.value.prepared != null || model.archive.value.notice != null) }
    }
    private fun clickDocumentNode(matches: (AccessibilityNodeInfo) -> Boolean): Unit {
        val deadline = SystemClock.elapsedRealtime() + 10_000
        while (SystemClock.elapsedRealtime() < deadline) { if (clickIfPresent(matches)) return; Thread.yield() }
        throw RecoveryFailure("Expected document-picker control was not reachable")
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
    private fun awaitPackage(matches: (String?) -> Boolean): Unit {
        val deadline = SystemClock.elapsedRealtime() + 10_000
        while (SystemClock.elapsedRealtime() < deadline) { if (matches(activePackage())) return; Thread.yield() }
        throw RecoveryFailure("Expected Activity did not become active")
    }
    private fun assertNoPersistedGrant(): Unit {
        verify(context.contentResolver.persistedUriPermissions.none { it.uri.authority == authority }, "No chooser URI permission may be persisted")
    }
    private fun drainedStats(): Unit {
        val deadline = SystemClock.elapsedRealtime() + 10_000
        while (SystemClock.elapsedRealtime() < deadline) {
            val stats = io { requireNotNull(context.contentResolver.call(authority + ".control", "stats", null, null)) }
            if (stats.getInt("active_count") == 0 && stats.getInt("opened_count") == stats.getInt("closed_count")) {
                verify(stats.getInt("close_failure_count") == 0, "Selected document descriptors must close successfully"); return
            }
            Thread.yield()
        }
        throw RecoveryFailure("Selected document descriptors did not drain")
    }

    private fun ownedRoot(fresh: Boolean): File {
        val base = File(context.noBackupFilesDir.canonicalFile, "archive-recovery")
        if (!Files.exists(base.toPath(), LinkOption.NOFOLLOW_LINKS)) Files.createDirectory(base.toPath())
        realDirectory(base)
        val directory = File(base, run)
        if (fresh) Files.createDirectory(directory.toPath())
        realDirectory(directory)
        if (fresh) writeAt(directory, "owner-v1", owner.toByteArray(Charsets.US_ASCII), 4096)
        verify(readAt(directory, "owner-v1", 4096).contentEquals(owner.toByteArray(Charsets.US_ASCII)), "Recovery ownership marker mismatch")
        return directory
    }
    private fun newDirectory(parent: File, name: String): File = File(parent, name).also { Files.createDirectory(it.toPath()); realDirectory(it) }
    private fun realDirectory(directory: File): Unit {
        verify(Files.isDirectory(directory.toPath(), LinkOption.NOFOLLOW_LINKS) && !Files.isSymbolicLink(directory.toPath()) &&
            directory.absoluteFile == directory.canonicalFile, "Recovery directory must be real and nonlinked")
    }
    private fun writeNew(name: String, bytes: ByteArray, cap: Int): Unit = writeAt(root, name, bytes, cap)
    private fun writeAt(directory: File, name: String, bytes: ByteArray, cap: Int): Unit {
        verify(name in setOf("owner-v1", "archive.json", "baseline.json", "ready-v1.json", "verified-v1.json") && bytes.size in 1..cap,
            "Recovery output name or size is invalid")
        FileChannel.open(File(directory, name).toPath(), StandardOpenOption.CREATE_NEW, StandardOpenOption.WRITE).use { channel ->
            val buffer = ByteBuffer.wrap(bytes); while (buffer.hasRemaining()) channel.write(buffer); channel.force(true)
        }
    }
    private fun readFile(name: String, cap: Int): ByteArray = readAt(root, name, cap)
    private fun readAt(directory: File, name: String, cap: Int): ByteArray {
        verify(name in setOf("owner-v1", "archive.json", "baseline.json", "ready-v1.json"), "Unsupported recovery input")
        val file = File(directory, name)
        verify(Files.isRegularFile(file.toPath(), LinkOption.NOFOLLOW_LINKS) && !Files.isSymbolicLink(file.toPath()) &&
            file.absoluteFile == file.canonicalFile, "Recovery input must be a regular nonlink")
        return file.inputStream().use { input ->
            val output = ByteArrayOutputStream(); val buffer = ByteArray(8192)
            while (output.size() < cap) {
                val count = input.read(buffer, 0, minOf(buffer.size, cap - output.size()))
                if (count < 0) break
                if (count == 0) { val one = input.read(); if (one < 0) break; output.write(one) } else output.write(buffer, 0, count)
            }
            verify(output.size() > 0 && input.read() == -1, "Recovery input is empty or exceeds its bound"); output.toByteArray()
        }
    }
    private fun publicMarker(status: String): JSONObject = JSONObject().put("version", 1).put("run", run).put("phase", phase)
        .put("pid", Process.myPid()).put("archive_sha256", sha256(source)).put("status", status)
    private fun sha256(bytes: ByteArray): String = MessageDigest.getInstance("SHA-256").digest(bytes)
        .joinToString("") { (it.toInt() and 255).toString(16).padStart(2, '0') }

    private fun defaultDatabase(): File = File(context.noBackupFilesDir.canonicalFile, "workspace-v1/stories.sqlite3").also {
        verify(Files.isRegularFile(it.toPath(), LinkOption.NOFOLLOW_LINKS) && !Files.isSymbolicLink(it.toPath()) &&
            it.absoluteFile == it.canonicalFile, "Existing workspace must be a regular nonlink")
    }
    private fun library(): JSONArray = Host(defaultDatabase()).use { it.ok(command("workspace")).getJSONArray("stories") }
    private fun snapshot(scope: JSONObject, head: Long): JSONObject = Host(defaultDatabase()).use { host ->
        val session = host.ok(command("resume").put("scope", scope)).getString("session")
        host.ok(scoped("play_snapshot", session, scope).put("expected_revision", head))
    }
    private fun export(database: File, stageName: String, scope: JSONObject, head: Long): ByteArray {
        val staging = newDirectory(root, stageName)
        val handle = NativeArchive.open(database.canonicalPath, staging.canonicalPath)
        verify(handle > 0, "Native archive owner did not open")
        try {
            val control = JSONObject().put("story", scope.getString("story")).put("branch", scope.getString("branch"))
                .put("expected_revision", head).toString().toByteArray(Charsets.UTF_8)
            val prepared = accepted(NativeArchive.prepareExport(handle, control))
            return NativeArchive.exportBytes(handle, prepared.getLong("token")).also {
                verify(it.size in 1..131_072, "Recovery archive exceeds its synthetic bound")
            }
        } finally { NativeArchive.close(handle); verify(staging.listFiles()?.isEmpty() == true, "Owned export staging must drain") }
    }
    private inner class Host(database: File) : Closeable {
        private var handle = NativeWorkspace.open(database.canonicalPath).also { verify(it > 0, "Native Host owner did not open") }
        fun ok(command: JSONObject): JSONObject {
            val bytes = JSONObject().put("version", 1).put("command", command).toString().toByteArray(Charsets.UTF_8)
            verify(bytes.size <= 24_576, "Host request exceeds its bound"); return accepted(NativeWorkspace.call(handle, bytes))
        }
        fun commit(session: String, request: JSONObject): Unit {
            verify(ok(command("submit").put("session", session).put("request", request).put("mode", "accepted")).getString("phase") == "queued",
                "Original recovery wait must queue")
            val scope = request.getJSONObject("scope"); val turn = request.getString("turn")
            verify(ok(scoped("prepare", session, scope).put("turn", turn)).getString("phase") == "ready", "Original recovery wait must prepare")
            verify(ok(scoped("commit", session, scope).put("turn", turn)).getString("phase") == "committed", "Original recovery wait must commit")
        }
        override fun close(): Unit { val previous = handle.also { handle = 0 }; if (previous > 0) NativeWorkspace.close(previous) }
    }
    private fun command(op: String) = JSONObject().put("op", op)
    private fun scope(story: String, branch: String) = JSONObject().put("story", story).put("branch", branch)
    private fun scoped(op: String, session: String, scope: JSONObject) = command(op).put("session", session).put("scope", scope)
    private fun request(scope: JSONObject, turn: String, head: Long, action: JSONObject) = JSONObject().put("version", 1).put("scope", scope)
        .put("turn", turn).put("expected_revision", head).put("intent", JSONObject().put("kind", "actions").put("value", JSONArray().put(action)))
    private fun accepted(bytes: ByteArray): JSONObject {
        verify(bytes.size in 1..262_144, "Native reply exceeds its bound")
        val reply = JSONObject(bytes.toString(Charsets.UTF_8))
        verify(reply.getInt("version") == 1 && reply.getString("status") == "ok", "Native recovery operation failed")
        return reply.getJSONObject("data")
    }
    private fun keys(value: JSONObject, expected: Set<String>): Unit = verify(value.keys().asSequence().toSet() == expected, "Recovery record fields mismatch")
    private fun sameJson(left: Any?, right: Any?): Boolean = when {
        left is JSONObject && right is JSONObject -> left.keys().asSequence().toSet().let { keys ->
            keys == right.keys().asSequence().toSet() && keys.all { sameJson(left.get(it), right.get(it)) } }
        left is JSONArray && right is JSONArray -> left.length() == right.length() && (0 until left.length()).all { sameJson(left.get(it), right.get(it)) }
        left is Number && right is Number -> left.toString() == right.toString()
        else -> left == right
    }
    private fun <T> io(block: () -> T): T = runBlocking { withContext(Dispatchers.IO) {
        verify(Looper.myLooper() != Looper.getMainLooper(), "Native and fixture work must stay off Main"); block()
    } }
    private class RecoveryFailure(message: String) : AssertionError(message)
    private fun safe(block: () -> Unit): Unit {
        try { block() } catch (failure: RecoveryFailure) { throw failure }
        catch (failure: Throwable) {
            if (failure is VirtualMachineError || failure is ThreadDeath) throw failure
            throw AssertionError("Archive recovery boundary failed (${failure.javaClass.simpleName})").also { it.stackTrace = failure.stackTrace }
        }
    }
    private fun verify(condition: Boolean, message: String): Unit { if (!condition) throw RecoveryFailure(message) }
}

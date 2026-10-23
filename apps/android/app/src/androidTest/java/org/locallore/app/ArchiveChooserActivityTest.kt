/* Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0 */
package org.locallore.app

import android.accessibilityservice.AccessibilityServiceInfo
import android.content.Intent
import android.content.pm.PackageManager
import android.os.Bundle
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
import java.io.Closeable
import java.io.File
import java.nio.file.Files
import java.nio.file.LinkOption
import java.nio.file.StandardOpenOption
import java.util.UUID
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.runBlocking
import kotlinx.coroutines.withContext
import org.json.JSONArray
import org.json.JSONObject
import org.junit.After
import org.junit.Before
import org.junit.Rule
import org.junit.Test
import org.junit.runner.RunWith

/** Product document I/O runs only through actual chooser-returned URIs; fixtures stay synthetic. */
@RunWith(AndroidJUnit4::class)
@Suppress("DEPRECATION")
class ArchiveChooserActivityTest {
    @get:Rule val compose = createAndroidComposeRule<MainActivity>()
    private val instrumentation get() = InstrumentationRegistry.getInstrumentation()
    private val context get() = instrumentation.targetContext
    private val authority get() = instrumentation.context.packageName + ".chooser"
    private val documents = setOf("com.android.documentsui", "com.google.android.documentsui")
    private lateinit var model: ShellViewModel
    private lateinit var original: ShellState
    private lateinit var beforeLibrary: JSONArray
    private lateinit var fixtureDirectory: File
    private lateinit var fixtureScope: JSONObject
    private lateinit var run: String
    private var pickerRequested = false
    private var originalAccessibilityFlags: Int? = null

    @Before fun configureFreshSyntheticSource(): Unit { safe {
        compose.activityRule.scenario.onActivity { model = ViewModelProvider(it)[ShellViewModel::class.java] }
        compose.waitUntil(10_000) { model.state.value.persistent && !model.state.value.busy &&
            !model.state.value.recoveryRequired && model.state.value.selectedStory != null }
        original = model.state.value
        beforeLibrary = io { defaultLibrary() }
        val automation = instrumentation.uiAutomation
        val info = automation.serviceInfo
        originalAccessibilityFlags = info.flags
        info.flags = info.flags or AccessibilityServiceInfo.FLAG_REPORT_VIEW_IDS
        automation.serviceInfo = info
        val archive = io {
            fixtureDirectory = File(context.noBackupFilesDir.canonicalFile, "chooser-fixture-${UUID.randomUUID()}")
            Files.createDirectory(fixtureDirectory.toPath())
            Files.newOutputStream(File(fixtureDirectory, "owner-v1").toPath(), StandardOpenOption.CREATE_NEW, StandardOpenOption.WRITE).use {
                it.write("locallore-chooser-fixture-v1".toByteArray(Charsets.US_ASCII))
            }
            Host(File(fixtureDirectory, "stories.sqlite3")).use { host ->
                val created = host.ok(command("create").put("seed", "lantern-quay-v1"))
                fixtureScope = created.getJSONObject("scope")
                val session = created.getString("session")
                val request = request(fixtureScope, "chooser-prefix-v1", 0, command("wait").put("ticks", 1))
                host.commit(session, request)
                export(File(fixtureDirectory, "stories.sqlite3"), "source-staging", fixtureScope, 1)
            }
        }
        val future = JSONObject(archive.toString(Charsets.UTF_8)).put("version", 999).toString().toByteArray(Charsets.UTF_8)
        val extras = Bundle().apply {
            putByteArray("archive", archive); putByteArray("future", future)
            putByteArray("malformed", "{\"version\":1,\"version\":1}".toByteArray(Charsets.UTF_8))
        }
        val configured = io { requireNotNull(instrumentation.context.contentResolver.call(authority, "configure", null, extras)) }
        run = requireNotNull(configured.getString("run"))
        verify(Regex("[a-f0-9]{32}").matches(run), "Provider run identifier is invalid")
        for (kind in listOf("valid", "future", "malformed")) {
            verify(context.checkUriPermission(sourceUri(kind), Process.myPid(), Process.myUid(),
                Intent.FLAG_GRANT_READ_URI_PERMISSION) == PackageManager.PERMISSION_DENIED,
                "Source access must be denied before system selection")
        }
        assertNoPersistedGrant()
    } }

    @After fun drainOwnedChooserAndRestorePriorSelection(): Unit { safe {
        try {
            if (pickerRequested && activePackage() in documents) {
                verify(activePackage() in documents, "DocumentsUI must be foreground before cleanup Back")
                instrumentation.sendKeyDownUpSync(KeyEvent.KEYCODE_BACK)
                awaitApplication()
                pickerRequested = false
            }
            if (::model.isInitialized) {
                compose.activityRule.scenario.onActivity { model.archiveController?.dismiss() }
                compose.waitUntil(10_000) { !model.archive.value.visible && !model.state.value.busy }
                if (::original.isInitialized) {
                    val previous = requireNotNull(original.selectedStory)
                    compose.activityRule.scenario.onActivity { model.resume(previous) }
                    compose.waitUntil(10_000) { !model.state.value.busy && model.state.value.selectedStory == previous }
                    verify(sameCanon(original, model.state.value), "Prior selected story must retain its accepted state")
                }
            }
            if (::run.isInitialized) { drainedStats(); assertNoPersistedGrant() }
        } finally {
            originalAccessibilityFlags?.let { flags ->
                val info = instrumentation.uiAutomation.serviceInfo
                info.flags = flags; instrumentation.uiAutomation.serviceInfo = info
            }
        }
    } }

    @Test fun validChooserImportContinueExportAndConflict(): Unit { safe {
        openArchive()
        selectImport("Valid archive.json")
        verify(model.archive.value.prepared != null && model.archive.value.imported == null,
            "Chooser selection must only validate before consent")
        verify(sameJson(beforeLibrary, io { defaultLibrary() }), "Validation must not import or change the existing library")
        verify(sameCanon(original, model.state.value), "Validation must preserve prior accepted state")
        compose.onNodeWithTag("archive-import-confirm").performScrollTo().performClick()
        compose.waitUntil(10_000) { !model.archive.value.busy && model.archive.value.imported != null }
        verify(sameCanon(original, model.state.value), "Import must not switch stories before explicit Open")
        val importedLibrary = io { defaultLibrary() }
        verify(importedLibrary.length() == beforeLibrary.length() + 1 && preservesPriorStories(importedLibrary),
            "Explicit import must add only the new story and preserve prior stories")
        compose.onNodeWithTag("archive-open-imported").performScrollTo().performClick()
        compose.waitUntil(10_000) { !model.state.value.busy && !model.archive.value.visible &&
            model.state.value.selectedStory?.story == fixtureScope.getString("story") && model.state.value.revision == 1L }
        tag("give-potion").performClick()
        compose.waitUntil(10_000) { !model.state.value.busy && model.state.value.revision == 2L }
        val committed = model.state.value
        tag("give-potion").performClick()
        compose.waitUntil(10_000) { !model.state.value.busy }
        verify(sameCanon(committed, model.state.value), "Second gift must not duplicate accepted outcomes")
        verify(model.state.value.notice?.contains("no longer hold") == true, "Duplicate gift must report inventory refusal")
        io {
            Host(defaultDatabase()).use { host ->
                val resumed = host.ok(command("resume").put("scope", fixtureScope))
                val snapshot = host.ok(scoped("play_snapshot", resumed.getString("session"), fixtureScope).put("expected_revision", 2))
                verify(snapshot.getLong("revision") == 2L && snapshot.getJSONArray("receipts").length() == 2 &&
                    !snapshot.getJSONObject("inventory").has("potion"), "Reopened native history must contain exactly one potion gift")
            }
        }

        openArchive()
        compose.onNodeWithTag("archive-export-prepare").performScrollTo().performClick()
        compose.waitUntil(10_000) { !model.archive.value.busy && model.archive.value.prepared != null }
        val expected = io { export(defaultDatabase(), "expected-staging", fixtureScope, 2) }
        val outputUri = DocumentsContract.buildDocumentUri(authority, "run-$run:output-1")
        verify(context.checkUriPermission(outputUri, Process.myPid(), Process.myUid(), Intent.FLAG_GRANT_WRITE_URI_PERMISSION) ==
            PackageManager.PERMISSION_DENIED, "Output access must be denied before system creation")
        pickerRequested = true
        compose.onNodeWithTag("archive-export-pick").performScrollTo().performClick()
        chooseProviderRoot()
        clickDocumentNode { it.text?.toString()?.equals("Save", ignoreCase = true) == true }
        awaitApplication(); pickerRequested = false
        compose.waitUntil(10_000) { !model.archive.value.busy && !model.archive.value.awaitingPicker &&
            model.archive.value.notice?.startsWith("The captured archive was written.") == true }
        val stats = drainedStats()
        verify(stats.getInt("created_count") == 1 && stats.getInt("write_count") == 1 && stats.getInt("read_count") >= 1,
            "The real chooser must read one source and write one newly created document")
        verify(stats.getByteArray("created_bytes")?.contentEquals(expected) == true, "Created document must equal the captured native archive bytes")
        verify(context.checkUriPermission(outputUri, Process.myPid(), Process.myUid(), Intent.FLAG_GRANT_WRITE_URI_PERMISSION) ==
            PackageManager.PERMISSION_GRANTED, "System creation must grant temporary output access")
        assertNoPersistedGrant()
        closeArchive()

        val beforeConflict = io { defaultLibrary() }
        openArchive(); selectImport("Valid archive.json")
        compose.onNodeWithTag("archive-import-confirm").performScrollTo().performClick()
        compose.waitUntil(10_000) { !model.archive.value.busy && model.archive.value.notice?.contains("already exists") == true }
        verify(model.archive.value.imported == null && sameCanon(committed, model.state.value), "Same-ID conflict must preserve accepted state")
        verify(sameJson(beforeConflict, io { defaultLibrary() }), "Same-ID conflict must not overwrite any story")
        compose.onNodeWithTag("archive-import-pick").performScrollTo().assertIsEnabled()
        closeArchive(); drainedStats()
    } }

    @Test fun invalidChooserInputsRemainRecoverable(): Unit { safe {
        openArchive()
        for ((title, notice) in listOf("Future archive.json" to "unsupported", "Malformed archive.json" to "invalid")) {
            selectImport(title)
            compose.waitUntil(10_000) { !model.archive.value.busy && model.archive.value.notice?.contains(notice) == true }
            verify(model.archive.value.prepared == null && model.archive.value.imported == null,
                "Invalid selected documents must not create an import capability")
            compose.onNodeWithTag("archive-import-confirm").assertDoesNotExist()
            compose.onNodeWithTag("archive-import-pick").performScrollTo().assertIsEnabled()
            verify(sameJson(beforeLibrary, io { defaultLibrary() }) && sameCanon(original, model.state.value),
                "Invalid documents must preserve every prior story and accepted state")
            drainedStats()
        }
        // A valid selection after both errors proves the picker/controller slot recovered.
        selectImport("Valid archive.json")
        verify(model.archive.value.prepared != null, "A valid preview must remain usable after document failures")
        verify(sameJson(beforeLibrary, io { defaultLibrary() }), "Recovered preview must still require consent")
        compose.onNodeWithTag("archive-cancel").performClick()
        compose.waitUntil(10_000) { !model.archive.value.busy && model.archive.value.prepared == null }
        closeArchive()
        verify(sameJson(beforeLibrary, io { defaultLibrary() }) && sameCanon(original, model.state.value),
            "Cancelling the recovered preview must preserve accepted state")
        drainedStats(); assertNoPersistedGrant()
    } }

    private fun openArchive(): Unit { tag("story-archive").assertIsEnabled().performClick(); compose.onNodeWithTag("archive-dialog").assertIsDisplayed() }
    private fun closeArchive(): Unit {
        compose.onNodeWithTag("archive-close").performClick()
        compose.waitUntil(10_000) { !model.archive.value.visible && !model.state.value.busy && !model.state.value.archiveActive }
    }
    private fun tag(name: String): SemanticsNodeInteraction {
        compose.onNodeWithTag("story-list").performScrollToNode(hasTestTag(name))
        return compose.onNodeWithTag(name)
    }
    private fun selectImport(title: String): Unit {
        pickerRequested = true
        compose.onNodeWithTag("archive-import-pick").performScrollTo().performClick()
        chooseProviderRoot()
        clickDocumentNode { it.text?.toString() == title }
        val deadline = SystemClock.elapsedRealtime() + 10_000
        while (activePackage() in documents && SystemClock.elapsedRealtime() < deadline) {
            // Some platform picker versions require a separate Open action after selecting a row.
            clickIfPresent { it.text?.toString()?.equals("Open", ignoreCase = true) == true }
            Thread.yield()
        }
        awaitApplication(); pickerRequested = false
        compose.waitUntil(10_000) { !model.archive.value.awaitingPicker && !model.archive.value.busy &&
            (model.archive.value.prepared != null || model.archive.value.notice != null) }
    }
    private fun chooseProviderRoot(): Unit {
        awaitPackage { it in documents }
        // The drawer button is addressed by accessibility semantics, never screen coordinates.
        clickIfPresent { it.contentDescription?.toString() in setOf("Show roots", "Open navigation drawer", "Show locations") }
        clickDocumentNode { it.text?.toString() == "LocalLore test archives" }
    }
    private fun clickDocumentNode(matches: (AccessibilityNodeInfo) -> Boolean): Unit {
        val deadline = SystemClock.elapsedRealtime() + 10_000
        while (SystemClock.elapsedRealtime() < deadline) {
            if (clickIfPresent(matches)) return
            Thread.yield()
        }
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
                for (index in 0 until node.childCount) {
                    val child = node.getChild(index) ?: continue
                    if (walk(child, depth + 1)) return true
                }
                return false
            } finally { node.recycle() }
        }
        return walk(root, 0)
    }
    private fun activePackage(): String? = instrumentation.uiAutomation.rootInActiveWindow?.let {
        try { it.packageName?.toString() } finally { it.recycle() }
    }
    private fun awaitApplication(): Unit = awaitPackage { it == context.packageName }
    private fun awaitPackage(matches: (String?) -> Boolean): Unit {
        val deadline = SystemClock.elapsedRealtime() + 10_000
        while (SystemClock.elapsedRealtime() < deadline) {
            if (matches(activePackage())) return
            Thread.yield()
        }
        throw AssertionError("Expected picker or application did not become active")
    }

    private fun sourceUri(kind: String) = DocumentsContract.buildDocumentUri(authority, "run-$run:$kind")
    private fun assertNoPersistedGrant(): Unit {
        verify(context.contentResolver.persistedUriPermissions.none { it.uri.authority == authority },
            "LocalLore must not retain a persisted chooser permission")
    }
    private fun drainedStats(): Bundle {
        val deadline = SystemClock.elapsedRealtime() + 10_000
        while (SystemClock.elapsedRealtime() < deadline) {
            val stats = io { requireNotNull(instrumentation.context.contentResolver.call(authority, "stats", null, null)) }
            if (stats.getInt("active_count") == 0 && stats.getInt("opened_count") == stats.getInt("closed_count")) {
                verify(stats.getInt("close_failure_count") == 0, "Provider descriptor close must succeed")
                return stats
            }
            Thread.yield()
        }
        throw AssertionError("Provider document owners did not drain")
    }
    private fun preservesPriorStories(after: JSONArray): Boolean = (0 until beforeLibrary.length()).all { old ->
        (0 until after.length()).any { sameJson(beforeLibrary.get(old), after.get(it)) }
    }
    private fun defaultDatabase(): File = File(context.noBackupFilesDir.canonicalFile, "workspace-v1/stories.sqlite3").also {
        verify(Files.isRegularFile(it.toPath(), LinkOption.NOFOLLOW_LINKS) && !Files.isSymbolicLink(it.toPath()) &&
            it.absoluteFile == it.canonicalFile, "Existing default workspace must be a regular nonlink")
    }
    private fun defaultLibrary(): JSONArray = Host(defaultDatabase()).use { it.ok(command("workspace")).getJSONArray("stories") }
    private fun export(database: File, stageName: String, scope: JSONObject, head: Long): ByteArray {
        val staging = File(fixtureDirectory, stageName).also { Files.createDirectory(it.toPath()) }
        val handle = NativeArchive.open(database.canonicalPath, staging.canonicalPath)
        verify(handle > 0, "Synthetic native archive owner did not open")
        try {
            val control = JSONObject().put("story", scope.getString("story")).put("branch", scope.getString("branch"))
                .put("expected_revision", head).toString().toByteArray(Charsets.UTF_8)
            val prepared = accepted(NativeArchive.prepareExport(handle, control))
            return NativeArchive.exportBytes(handle, prepared.getLong("token")).also {
                verify(it.size in 1..131_072, "Synthetic chooser archive exceeds its fixture bound")
            }
        } finally { NativeArchive.close(handle); verify(staging.listFiles()?.isEmpty() == true, "Synthetic staging must drain") }
    }
    private inner class Host(database: File) : Closeable {
        private var handle = NativeWorkspace.open(database.canonicalPath).also { verify(it > 0, "Synthetic Host did not open") }
        fun ok(command: JSONObject): JSONObject {
            val bytes = JSONObject().put("version", 1).put("command", command).toString().toByteArray(Charsets.UTF_8)
            verify(bytes.size <= 24_576, "Synthetic Host request exceeds its bound")
            return accepted(NativeWorkspace.call(handle, bytes))
        }
        fun commit(session: String, request: JSONObject): Unit {
            verify(ok(command("submit").put("session", session).put("request", request).put("mode", "accepted")).getString("phase") ==
                "queued", "Synthetic wait must queue")
            val scope = request.getJSONObject("scope"); val turn = request.getString("turn")
            verify(ok(scoped("prepare", session, scope).put("turn", turn)).getString("phase") == "ready", "Synthetic wait must prepare")
            verify(ok(scoped("commit", session, scope).put("turn", turn)).getString("phase") == "committed", "Synthetic wait must commit")
        }
        override fun close(): Unit { val previous = handle.also { handle = 0 }; if (previous > 0) NativeWorkspace.close(previous) }
    }
    private fun command(op: String) = JSONObject().put("op", op)
    private fun scoped(op: String, session: String, scope: JSONObject) = command(op).put("session", session).put("scope", scope)
    private fun request(scope: JSONObject, turn: String, head: Long, action: JSONObject) = JSONObject().put("version", 1)
        .put("scope", scope).put("turn", turn).put("expected_revision", head)
        .put("intent", JSONObject().put("kind", "actions").put("value", JSONArray().put(action)))
    private fun accepted(bytes: ByteArray): JSONObject {
        verify(bytes.size in 1..262_144, "Native reply exceeds its boundary")
        val reply = JSONObject(bytes.toString(Charsets.UTF_8))
        verify(reply.getInt("version") == 1 && reply.getString("status") == "ok", "Native fixture operation failed")
        return reply.getJSONObject("data")
    }
    private fun sameCanon(left: ShellState, right: ShellState): Boolean = left.selectedStory == right.selectedStory &&
        left.revision == right.revision && left.messages == right.messages && left.potionOwner == right.potionOwner && !right.recoveryRequired
    private fun sameJson(left: Any?, right: Any?): Boolean = when {
        left is JSONObject && right is JSONObject -> left.keys().asSequence().toSet().let { keys ->
            keys == right.keys().asSequence().toSet() && keys.all { sameJson(left.get(it), right.get(it)) } }
        left is JSONArray && right is JSONArray -> left.length() == right.length() && (0 until left.length()).all { sameJson(left.get(it), right.get(it)) }
        left is Number && right is Number -> left.toString() == right.toString()
        else -> left == right
    }
    private fun <T> io(block: () -> T): T = runBlocking { withContext(Dispatchers.IO) {
        verify(Looper.myLooper() != Looper.getMainLooper(), "Native work must stay off Main"); block()
    } }
    private fun safe(block: () -> Unit): Unit {
        try { block() } catch (failure: AssertionError) { throw failure }
        catch (_: Exception) { throw AssertionError("Synthetic chooser boundary failed") }
    }
    private fun verify(condition: Boolean, message: String): Unit { if (!condition) throw AssertionError(message) }
}

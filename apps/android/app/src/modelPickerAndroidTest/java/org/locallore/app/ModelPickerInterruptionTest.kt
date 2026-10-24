/* Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0 */
package org.locallore.app

import android.accessibilityservice.AccessibilityServiceInfo
import android.app.Application
import android.app.Instrumentation
import android.content.Intent
import android.content.pm.PackageManager
import android.net.Uri
import android.os.Build
import android.os.Bundle
import android.os.Looper
import android.os.Process
import android.os.SystemClock
import android.provider.DocumentsContract
import android.view.KeyEvent
import android.view.accessibility.AccessibilityNodeInfo
import androidx.annotation.RequiresApi
import androidx.compose.ui.test.*
import androidx.compose.ui.test.junit4.createEmptyComposeRule
import androidx.lifecycle.ViewModelProvider
import androidx.test.core.app.ActivityScenario
import androidx.test.ext.junit.runners.AndroidJUnit4
import androidx.test.platform.app.InstrumentationRegistry
import java.io.File
import java.nio.ByteBuffer
import java.nio.channels.FileChannel
import java.nio.file.Files
import java.nio.file.LinkOption.NOFOLLOW_LINKS
import java.nio.file.StandardOpenOption.CREATE_NEW
import java.nio.file.StandardOpenOption.WRITE
import java.security.MessageDigest
import java.util.concurrent.CopyOnWriteArrayList
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.runBlocking
import kotlinx.coroutines.withContext
import org.json.JSONObject
import org.junit.After
import org.junit.Rule
import org.junit.Test
import org.junit.runner.RunWith

/** Select the two methods separately. Arm intentionally dies; it is never an ordinary PASS. */
@RunWith(AndroidJUnit4::class)
@RequiresApi(30)
@Suppress("DEPRECATION")
class ModelPickerInterruptionTest {
    @get:Rule val compose = createEmptyComposeRule()
    private val instrumentation get() = InstrumentationRegistry.getInstrumentation()
    private val context get() = instrumentation.targetContext
    private val authority get() = instrumentation.context.packageName + ".modelpicker"
    private val documents = setOf("com.android.documentsui", "com.google.android.documentsui")
    private val sentinel = "LocalLore interruption sentinel v1\n".toByteArray(Charsets.US_ASCII)
    private val cacheSentinel = "LocalLore interruption cache v1\n".toByteArray(Charsets.US_ASCII)
    private var scenario: ActivityScenario<ModelPickerInterruptionFixtureActivity>? = null
    private lateinit var model: LocalModelSetupViewModel
    private var run: String? = null
    private var pickerRequested = false
    private var killRequested = false
    private var priorFlags: Int? = null
    private var observing = false
    private val requests = CopyOnWriteArrayList<Boolean>()
    private val monitor = object : Instrumentation.ActivityMonitor() {
        override fun onStartActivity(intent: Intent): Instrumentation.ActivityResult? {
            if (intent.action == Intent.ACTION_OPEN_DOCUMENT && requests.size < 4) {
                requests.add(intent.type == "*/*" && intent.hasCategory(Intent.CATEGORY_OPENABLE) &&
                    intent.getBooleanExtra(Intent.EXTRA_LOCAL_ONLY, false) &&
                    intent.getStringArrayExtra(Intent.EXTRA_MIME_TYPES)?.contentEquals(arrayOf("*/*")) == true)
            }
            return null
        }
    }

    @After fun finishOnlyIfNotIntentionallyKilled(): Unit = safe {
        if (killRequested) throw AssertionError("Self-process termination did not occur")
        try {
            if (pickerRequested && activePackage() in documents) {
                verify(activePackage() in documents, "Owned picker must be foreground before Back")
                instrumentation.sendKeyDownUpSync(KeyEvent.KEYCODE_BACK)
                awaitPackage { it == context.packageName }
            }
            if (::model.isInitialized) instrumentation.runOnMainSync { model.cancel() }
            run?.let { control("release", it); awaitStats { value -> drained(value) } }
            scenario?.close(); scenario = null
        } finally {
            if (observing) instrumentation.removeMonitor(monitor)
            priorFlags?.let { flags ->
                val info = instrumentation.uiAutomation.serviceInfo
                info.flags = flags; instrumentation.uiAutomation.serviceInfo = info
            }
        }
    }

    @RequiresApi(30)
    @Test fun armPartialImportAndTerminateOwnProcess(): Unit = safe {
        verify(Build.VERSION.SDK_INT >= 30, "Partial interruption document requires API30 or later")
        requireTargetProcess()
        val root = io { ModelPickerInterruptionFixture.root(context) }
        val old = io { oldFixtureProof() }
        io {
            verify(!Files.exists(root.toPath(), NOFOLLOW_LINKS), "Arm requires a fresh fixed interruption root; no reset is performed")
            Files.createDirectory(root.toPath())
            Files.createDirectory(File(root, "cache").toPath())
            writeNew(File(root, "interruption-sentinel-v1.bin"), sentinel)
            writeNew(File(root, "cache/preserve-v1.bin"), cacheSentinel)
        }
        beginActivity(); awaitPhase(LocalModelSetupPhase.MISSING)
        val configured = io { requireNotNull(context.contentResolver.call(controlUri(), "configure", null, null)) }
        run = requireNotNull(configured.getString("run"))
        verify(requireNotNull(run).matches(Regex("[a-f0-9]{32}")), "Provider transaction invalid")
        select("partial-blocked", "Partial blocked synthetic model.bin")
        awaitPhase(LocalModelSetupPhase.IMPORTING)
        awaitStats { value -> value.getInt("partial_prefix_bytes") == 17 && value.getInt("partial_writer_waiting") == 1 &&
            value.getInt("active") == 1 && value.getInt("opened") == 1 && value.getInt("closed") == 0 }
        val deadline = SystemClock.elapsedRealtime() + 5_000
        while (!io { prefixPresent(root) } && SystemClock.elapsedRealtime() < deadline) Thread.yield()
        io {
            verify(prefixPresent(root), "Arm requires actual seventeen-byte regular staging file")
            verify(!Files.exists(File(root, "model.litertlm").toPath(), NOFOLLOW_LINKS), "Partial import must not publish a model")
            checkSentinels(root)
            verify(oldFixtureProof() == old, "Old model and private receipt must remain byte-identical before interruption")
            requireTargetProcess()
            val process = Application.getProcessName()
            val proof = JSONObject().put("version", 1).put("pid", Process.myPid())
                .put("start", Process.getStartElapsedRealtime()).put("uid", Process.myUid()).put("process", process)
                .put("run", requireNotNull(run)).put("stage_bytes", 17)
                .put("old_model_sha256", old.first).put("old_receipt_sha256", old.second)
                .toString().toByteArray(Charsets.US_ASCII)
            verify(proof.size in 1..1024, "Private interruption proof exceeds bound")
            writeNew(File(root, "interruption-arm-proof-v1.json"), proof)
        }
        verify(requests.size == 1 && requests.single(), "Arm must use one actual local-only openable document request")
        val finalOwner = stats()
        verify(finalOwner.getInt("active") == 1 && finalOwner.getInt("partial_writer_waiting") == 1 &&
            finalOwner.getInt("partial_writer_terminal") == 0 && finalOwner.getInt("failures") == 0,
            "Actual provider must remain owned and blocked at self-process death")
        instrumentation.sendStatus(2, Bundle().apply { putString("locallore_interruption", "partial-import-armed-v1") })
        killRequested = true
        Process.killProcess(Process.myPid())
        throw AssertionError("Self-process termination did not occur")
    }

    @RequiresApi(30)
    @Test fun recoverInterruptedImportThroughFreshPicker(): Unit = safe {
        verify(Build.VERSION.SDK_INT >= 30, "Partial interruption document requires API30 or later")
        requireTargetProcess()
        val root = io { ModelPickerInterruptionFixture.root(context) }
        val proof = io {
            val file = File(root, "interruption-arm-proof-v1.json")
            verify(Files.isRegularFile(file.toPath(), NOFOLLOW_LINKS) && file.length() in 1..1024,
                "Exact bounded arm proof must exist before recovery Activity starts")
            JSONObject(file.readText(Charsets.US_ASCII)).also {
                verify(it.keys().asSequence().toSet() == setOf("version", "pid", "start", "uid", "process", "run", "stage_bytes",
                    "old_model_sha256", "old_receipt_sha256") && it.getInt("version") == 1 && it.getInt("stage_bytes") == 17,
                    "Private arm proof schema must be exact")
                verify(it.getInt("pid") > 0 && it.getInt("uid") > 0 && it.getLong("start") > 0 &&
                    (it.getInt("pid") != Process.myPid() || it.getLong("start") != Process.getStartElapsedRealtime()),
                    "Recovery must run in a different actual process")
                verify(it.getString("process") == context.applicationInfo.processName && it.getInt("uid") == context.applicationInfo.uid,
                    "Interrupted process must match the exact target Activity process and UID")
                verify(it.getString("run").matches(Regex("[a-f0-9]{32}")), "Arm provider transaction format invalid")
                verify(prefixPresent(root), "Actual seventeen-byte stage must survive process death before store recovery")
                checkSentinels(root)
                val old = oldFixtureProof()
                verify(old.first == it.getString("old_model_sha256") && old.second == it.getString("old_receipt_sha256"),
                    "Old model and private process receipt must survive unchanged")
            }
        }
        val armProofHash = io { hash(File(root, "interruption-arm-proof-v1.json")) }
        run = proof.getString("run")
        // No Activity/store has checked this root yet. Release precisely the surviving provider run.
        awaitStats { value -> value.getInt("partial_consumer_closed") == 1 && value.getInt("active") == 0 &&
            value.getInt("partial_consumer_clean") == 0 && value.getInt("partial_consumer_peer_error") == 1 }
        control("release", requireNotNull(run))
        val released = awaitStats { value -> drained(value) && value.getInt("partial_writer_terminal") == 1 &&
            value.getInt("partial_writer_closed") == 1 && value.getInt("partial_writer_waiting") == 0 }
        verify(released.getInt("attempts") == 1 && released.getInt("opened") == 1 && released.getInt("closed") == 1,
            "Interrupted consumer and writer must actually drain before any new source selection")
        verify(released.getInt("partial_writer_peer_error") == 1,
            "Released writer must classify its closed-reader write as an expected peer error")
        io { verify(prefixPresent(root), "Provider release must not itself recover the private stage") }
        beginActivity(); awaitPhase(LocalModelSetupPhase.MISSING)
        io {
            verify(!Files.exists(File(root, "model.part").toPath(), NOFOLLOW_LINKS) &&
                !Files.exists(File(root, "model.litertlm").toPath(), NOFOLLOW_LINKS),
                "Fresh real store must reacquire persistent lock and recover only the fixed partial stage")
            checkSentinels(root)
        }
        compose.onNodeWithTag("model-start").performScrollTo().assertIsNotEnabled()
        select("valid", "Valid synthetic model.bin")
        awaitPhase(LocalModelSetupPhase.READY)
        val final = awaitStats { value -> drained(value) }
        verify(final.getInt("attempts") == 2 && final.getInt("opened") == 2 && final.getInt("closed") == 2,
            "Recovery must open and close exactly one newly selected valid descriptor")
        io {
            val files = requireNotNull(LocalModelStore(root, ModelPickerFixture.identity).installed())
            verify(files.model.readBytes().contentEquals(ModelPickerFixture.bytes()) && hash(files.model) == ModelPickerFixture.identity.sha256 &&
                !Files.exists(File(root, "model.part").toPath(), NOFOLLOW_LINKS),
                "Recovered import must publish exact full bytes natively and rehash on reopen")
            checkSentinels(root)
            verify(hash(File(root, "interruption-arm-proof-v1.json")) == armProofHash,
                "Stage recovery must preserve its private arm proof byte-for-byte")
            val old = oldFixtureProof()
            verify(old.first == proof.getString("old_model_sha256") && old.second == proof.getString("old_receipt_sha256"),
                "Valid recovery must preserve old model and receipt byte-for-byte")
        }
        compose.onNodeWithTag("model-start").performScrollTo().assertIsEnabled()
        verify(requests.size == 1 && requests.single(), "Recovery must use one new actual local-only openable picker selection")
        verify(context.contentResolver.persistedUriPermissions.none { it.uri.authority == authority }, "No persisted picker grant may be taken")
    }

    private fun prefixPresent(root: File): Boolean {
        val stage = File(root, "model.part")
        return Files.isRegularFile(stage.toPath(), NOFOLLOW_LINKS) && stage.length() == 17L &&
            stage.readBytes().contentEquals(ModelPickerFixture.bytes().copyOfRange(0, 17))
    }
    private fun checkSentinels(root: File) {
        for ((file, bytes) in listOf(File(root, "interruption-sentinel-v1.bin") to sentinel,
            File(root, "cache/preserve-v1.bin") to cacheSentinel)) {
            verify(Files.isRegularFile(file.toPath(), NOFOLLOW_LINKS) && file.readBytes().contentEquals(bytes),
                "Owned sentinel and cache bytes must remain unchanged")
        }
    }
    private fun oldFixtureProof(): Pair<String, String> {
        val root = ModelPickerFixture.root(context)
        val model = File(root, "model.litertlm")
        val receipt = File(root, "picker-process-proof-v1.json")
        verify(Files.isRegularFile(model.toPath(), NOFOLLOW_LINKS) && model.length() == 63L &&
            Files.isRegularFile(receipt.toPath(), NOFOLLOW_LINKS) && receipt.length() in 1..256,
            "Verified older fixture model and bounded receipt are required and preserved")
        val modelHash = hash(model)
        verify(modelHash == ModelPickerFixture.identity.sha256, "Older fixture model identity must match its original full hash")
        return modelHash to hash(receipt)
    }
    private fun hash(file: File) = MessageDigest.getInstance("SHA-256").digest(file.readBytes()).joinToString("") { "%02x".format(it) }
    private fun writeNew(file: File, bytes: ByteArray) {
        FileChannel.open(file.toPath(), CREATE_NEW, WRITE, NOFOLLOW_LINKS).use { channel ->
            val buffer = ByteBuffer.wrap(bytes)
            while (buffer.hasRemaining()) channel.write(buffer)
            channel.force(true)
        }
    }
    private fun beginActivity() {
        verify(context.packageName == "org.locallore.app.modelpickerverify", "Wrong fixed fixture installation")
        requireTargetProcess()
        val info = instrumentation.uiAutomation.serviceInfo
        priorFlags = info.flags; info.flags = info.flags or AccessibilityServiceInfo.FLAG_REPORT_VIEW_IDS
        instrumentation.uiAutomation.serviceInfo = info
        instrumentation.addMonitor(monitor); observing = true
        scenario = ActivityScenario.launch(ModelPickerInterruptionFixtureActivity::class.java)
        requireNotNull(scenario).onActivity {
            verify(it.packageName == context.packageName && it.applicationInfo.uid == context.applicationInfo.uid &&
                it.applicationInfo.processName == context.applicationInfo.processName,
                "Actual launched Activity must have the exact target process identity")
            model = ViewModelProvider(it)[LocalModelSetupViewModel::class.java]
        }
    }
    private fun requireTargetProcess() {
        verify(context.packageName == "org.locallore.app.modelpickerverify" &&
            Process.myUid() == context.applicationInfo.uid && Application.getProcessName() == context.applicationInfo.processName,
            "Self process must exactly match target Activity UID and process name")
    }
    private fun awaitPhase(phase: LocalModelSetupPhase) { compose.waitUntil(5_000) { model.state.value.phase == phase } }
    private fun controlUri() = Uri.parse("content://$authority.control")
    private fun control(method: String, token: String): Bundle = io {
        requireNotNull(context.contentResolver.call(controlUri(), method, null, Bundle().apply { putString("run", token) }))
    }
    private fun stats() = control("stats", requireNotNull(run))
    private fun drained(value: Bundle) = value.getInt("active") == 0 && value.getInt("opened") == value.getInt("closed") &&
        value.getInt("partial_writer_started") == value.getInt("partial_writer_terminal") &&
        value.getInt("partial_writer_started") == value.getInt("partial_writer_closed")
    private fun awaitStats(matches: (Bundle) -> Boolean): Bundle {
        val deadline = SystemClock.elapsedRealtime() + 5_000
        while (SystemClock.elapsedRealtime() < deadline) {
            val value = stats()
            verify(value.getInt("failures") == 0 && !value.getBoolean("partial_allocation_uncertain"),
                "Synthetic provider protocol/deadline/ownership failure")
            if (matches(value)) return value
            Thread.yield()
        }
        throw AssertionError("Actual provider owners did not reach the required finite state")
    }
    private fun select(kind: String, title: String) {
        val document = DocumentsContract.buildDocumentUri(authority, "${requireNotNull(run)}:$kind")
        verify(context.checkUriPermission(document, Process.myPid(), Process.myUid(), Intent.FLAG_GRANT_READ_URI_PERMISSION) ==
            PackageManager.PERMISSION_DENIED, "Fresh document must be inaccessible before explicit selection")
        pickerRequested = true
        compose.onNodeWithTag("model-choose").performScrollTo().performClick()
        awaitPackage { it in documents }
        verify(requests.size == 1 && requests.single(), "Actual OPEN_DOCUMENT request must contain exact local-only/openable/wildcard properties")
        clickIfPresent { it.contentDescription?.toString() in setOf("Show roots", "Open navigation drawer", "Show locations") }
        clickDocument { it.text?.toString() == "LocalLore model fixtures (${instrumentation.context.packageName})" }
        clickDocument { it.text?.toString() == title }
        val deadline = SystemClock.elapsedRealtime() + 5_000
        while (activePackage() in documents && SystemClock.elapsedRealtime() < deadline) {
            clickIfPresent { it.text?.toString()?.equals("Open", ignoreCase = true) == true }; Thread.yield()
        }
        awaitPackage { it == context.packageName }; pickerRequested = false
        verify(context.checkUriPermission(document, Process.myPid(), Process.myUid(), Intent.FLAG_GRANT_READ_URI_PERMISSION) ==
            PackageManager.PERMISSION_GRANTED, "Selection must grant a real temporary document read")
    }
    private fun clickDocument(matches: (AccessibilityNodeInfo) -> Boolean) {
        val deadline = SystemClock.elapsedRealtime() + 5_000
        while (SystemClock.elapsedRealtime() < deadline) { if (clickIfPresent(matches)) return; Thread.yield() }
        throw AssertionError("Expected fixed document-picker control unavailable")
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
    private fun awaitPackage(matches: (String?) -> Boolean) {
        val deadline = SystemClock.elapsedRealtime() + 5_000
        while (SystemClock.elapsedRealtime() < deadline) { if (matches(activePackage())) return; Thread.yield() }
        throw AssertionError("Expected owned picker/application did not become foreground")
    }
    private fun <T> io(block: suspend () -> T): T = runBlocking { withContext(Dispatchers.IO) {
        verify(Looper.myLooper() != Looper.getMainLooper(), "Fixture file/provider work must remain off Main"); block()
    } }
    private fun verify(condition: Boolean, message: String) { if (!condition) throw AssertionError(message) }
    private fun safe(block: () -> Unit) {
        try { block() } catch (failure: AssertionError) { throw failure }
        catch (failure: Exception) { throw AssertionError("Synthetic interruption boundary failed (${failure.javaClass.simpleName})").also { it.stackTrace = failure.stackTrace } }
    }
}

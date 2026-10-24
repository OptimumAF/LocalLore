/* Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0 */
package org.locallore.app

import android.accessibilityservice.AccessibilityServiceInfo
import android.app.Instrumentation
import android.content.Intent
import android.content.pm.PackageManager
import android.net.Uri
import android.os.Bundle
import android.os.Looper
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
import androidx.test.runner.lifecycle.ActivityLifecycleCallback
import androidx.test.runner.lifecycle.ActivityLifecycleMonitorRegistry
import androidx.test.runner.lifecycle.Stage
import java.io.File
import java.nio.file.Files
import java.nio.file.LinkOption.NOFOLLOW_LINKS
import java.nio.file.StandardOpenOption.CREATE_NEW
import java.nio.file.StandardOpenOption.WRITE
import java.security.MessageDigest
import java.util.concurrent.CopyOnWriteArrayList
import java.util.concurrent.atomic.AtomicInteger
import java.util.concurrent.atomic.AtomicReference
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.runBlocking
import kotlinx.coroutines.withContext
import org.json.JSONObject
import org.junit.After
import org.junit.Rule
import org.junit.Test
import org.junit.runner.RunWith

/** Real DocumentsUI and production picker/resolver/store wiring; never constructs an inference owner. */
@RunWith(AndroidJUnit4::class)
@Suppress("DEPRECATION")
class ModelPickerActivityTest {
    @get:Rule val compose = createEmptyComposeRule()
    private val instrumentation get() = InstrumentationRegistry.getInstrumentation()
    private val context get() = instrumentation.targetContext
    private val authority get() = instrumentation.context.packageName + ".modelpicker"
    private val documents = setOf("com.android.documentsui", "com.google.android.documentsui")
    private var scenario: ActivityScenario<ModelPickerFixtureActivity>? = null
    private lateinit var model: LocalModelSetupViewModel
    private var run: String? = null
    private var pickerRequested = false
    private var priorAccessibilityFlags: Int? = null
    private data class PickerRequest(val wildcard: Boolean, val openable: Boolean,
        val localOnly: Boolean, val expectedMimeTypes: Boolean)
    private val launchCount = AtomicInteger()
    private val launches = CopyOnWriteArrayList<PickerRequest>()
    private val monitor = object : Instrumentation.ActivityMonitor() {
        override fun onStartActivity(intent: Intent): Instrumentation.ActivityResult? {
            if (intent.action == Intent.ACTION_OPEN_DOCUMENT) {
                if (launchCount.incrementAndGet() <= 16) {
                    launches.add(PickerRequest(intent.type == "*/*", intent.hasCategory(Intent.CATEGORY_OPENABLE),
                        intent.getBooleanExtra(Intent.EXTRA_LOCAL_ONLY, false),
                        intent.getStringArrayExtra(Intent.EXTRA_MIME_TYPES)?.contentEquals(arrayOf("*/*")) == true))
                }
            }
            return null // Passive observation: actual system activity and result delivery proceed.
        }
    }
    private var observing = false

    @After fun finishOnlyOwnedFixtureSurfaces(): Unit = safe {
        try {
            if (pickerRequested && activePackage() in documents) {
                verify(activePackage() in documents, "Owned DocumentsUI must be foreground before Back")
                instrumentation.sendKeyDownUpSync(KeyEvent.KEYCODE_BACK)
                awaitPackage { it == context.packageName }
                pickerRequested = false
            }
            run?.let {
                instrumentation.runOnMainSync { if (::model.isInitialized) model.cancel() }
                control("release", it) // Exact current synthetic transaction only; never a timeout claim.
                drained()
            }
            scenario?.close(); scenario = null
        } finally {
            if (observing) instrumentation.removeMonitor(monitor)
            priorAccessibilityFlags?.let { flags ->
                val info = instrumentation.uiAutomation.serviceInfo
                info.flags = flags; instrumentation.uiAutomation.serviceInfo = info
            }
        }
    }

    @Test fun pickerCancelFailuresBlockedReadAndVerifiedRestartPreparation(): Unit = safe {
        verify(context.packageName == "org.locallore.app.modelpickerverify", "Wrong synthetic fixture installation")
        val root = io { ModelPickerFixture.root(context) }
        verify(io { !Files.exists(root.toPath(), NOFOLLOW_LINKS) }, "First phase requires an absent fixture root; no reset is performed")
        beginActivity()
        awaitPhase(LocalModelSetupPhase.MISSING)
        configureRun()
        for (kind in listOf("valid", "wrong", "open-failure", "blocked")) {
            verify(context.checkUriPermission(source(kind), Process.myPid(), Process.myUid(), Intent.FLAG_GRANT_READ_URI_PERMISSION) ==
                PackageManager.PERMISSION_DENIED, "No synthetic document may be readable before explicit picker selection")
        }
        noPersistedGrant()

        // The OS picker remains open across retained Activity recreation. Back grants no stream.
        val originalActivity = AtomicReference<ModelPickerFixtureActivity>()
        requireNotNull(scenario).onActivity { originalActivity.set(it) }
        requestPicker()
        val retained = model
        recreateBehindPicker(requireNotNull(originalActivity.get()), retained)
        verify(activePackage() in documents, "DocumentsUI must remain foreground after recreation")
        instrumentation.sendKeyDownUpSync(KeyEvent.KEYCODE_BACK)
        awaitPackage { it == context.packageName }; pickerRequested = false
        compose.waitUntil(10_000) { !model.state.value.busy && model.state.value.phase != LocalModelSetupPhase.PICKING }
        verify(stats().getInt("attempts") == 0, "Picker Back must never open a provider stream")
        compose.onNodeWithTag("model-choose").performScrollTo().assertIsEnabled()
        compose.onNodeWithTag("model-start").performScrollTo().assertIsNotEnabled()

        // Same-length wrong bytes and provider prose never become a valid model or raw UI message.
        select("wrong", "Wrong synthetic model.bin")
        awaitPhase(LocalModelSetupPhase.FAILED); assertSafeFailure(); assertNoPublication(root)
        verify(drained().getInt("opened") == 1, "Wrong bytes must use and close exactly one real descriptor")
        select("open-failure", "Unavailable synthetic model.bin")
        awaitPhase(LocalModelSetupPhase.FAILED); assertSafeFailure(); assertNoPublication(root)
        verify(drained().getInt("attempts") == 2 && stats().getInt("opened") == 1,
            "Provider open failure must not invent an opened descriptor")

        select("blocked", "Blocked synthetic model.bin")
        awaitStats { it.getInt("blocked_reads") > 0 && it.getInt("active") == 1 }
        awaitPhase(LocalModelSetupPhase.IMPORTING)
        compose.onNodeWithTag("model-import-cancel").performScrollTo().performClick()
        awaitPhase(LocalModelSetupPhase.STOPPING)
        compose.onNodeWithTag("model-choose").performScrollTo().assertIsNotEnabled()
        compose.onNodeWithTag("model-start").performScrollTo().assertIsNotEnabled()
        val held = stats()
        verify(held.getInt("active") == 1 && held.getInt("closed") == 1,
            "Cancel request must not claim the blocked provider descriptor closed")
        io {
            try { LocalModelStore(root, ModelPickerFixture.identity).installed(); throw AssertionError("Overlapping store must be refused") }
            catch (failure: LocalModelException) { verify(failure.failure == LocalModelFailure.BUSY, "Blocked provider must retain store admission") }
        }
        control("release", requireNotNull(run))
        drained()
        compose.waitUntil(10_000) { !model.state.value.busy }
        verify(model.state.value.phase == LocalModelSetupPhase.UNCHECKED,
            "Cancelled read completion must not publish stale READY state")
        assertNoPublication(root)
        compose.onNodeWithTag("model-start").performScrollTo().assertIsNotEnabled()

        // A second real blocked read spans background/recreation and final ViewModel disposal.
        val firstRun = requireNotNull(run)
        verify(stats().getInt("attempts") == 3 && stats().getInt("opened") == 2 && stats().getInt("closed") == 2,
            "First provider transaction must be fully drained before another transaction")
        configureRun()
        try { control("release", firstRun); throw AssertionError("Stale transaction must not release a successor") }
        catch (_: IllegalStateException) { /* Exact previous token is rejected, never delegated. */ }
        select("blocked", "Blocked synthetic model.bin")
        awaitStats { it.getInt("blocked_reads") > 0 && it.getInt("active") == 1 }
        awaitPhase(LocalModelSetupPhase.IMPORTING)
        val disposedModel = model
        requireNotNull(scenario).recreate()
        requireNotNull(scenario).onActivity { model = ViewModelProvider(it)[LocalModelSetupViewModel::class.java] }
        verify(model === disposedModel, "Blocked read recreation must retain its original controller")
        awaitPhase(LocalModelSetupPhase.STOPPING)
        verify(stats().getInt("active") == 1, "Background/recreation cancellation must retain actual provider ownership")
        requireNotNull(scenario).close(); scenario = null
        val disposedState = disposedModel.state.value
        beginActivity(); awaitPhase(LocalModelSetupPhase.FAILED)
        assertSafeFailure()
        verify(stats().getInt("attempts") == 1 && stats().getInt("active") == 1,
            "Fresh Activity must not overlap or reopen disposed controller's blocked provider")
        control("release", requireNotNull(run)); drained(); awaitStoreDrain(root)
        verify(disposedModel.state.value == disposedState && model.state.value.phase == LocalModelSetupPhase.FAILED,
            "Disposed/background result must not publish a stale success to either controller")
        assertNoPublication(root)

        select("valid", "Valid synthetic model.bin")
        awaitPhase(LocalModelSetupPhase.READY)
        verify(context.checkUriPermission(source("valid"), Process.myPid(), Process.myUid(), Intent.FLAG_GRANT_READ_URI_PERMISSION) ==
            PackageManager.PERMISSION_GRANTED, "Actual selection must grant temporary read access")
        val final = drained()
        verify(final.getInt("attempts") == 2 && final.getInt("opened") == 2 && final.getInt("closed") == 2,
            "Second transaction's blocked and valid descriptors must each open and close once")
        verifiedCopy(root)
        compose.onNodeWithTag("model-start").performScrollTo().assertIsEnabled()
        noPersistedGrant()

        requireNotNull(scenario).recreate()
        requireNotNull(scenario).onActivity { model = ViewModelProvider(it)[LocalModelSetupViewModel::class.java] }
        awaitPhase(LocalModelSetupPhase.READY); verifiedCopy(root)
        requireNotNull(scenario).close(); scenario = null
        beginActivity()
        awaitPhase(LocalModelSetupPhase.READY); verifiedCopy(root)
        verify(stats().getInt("attempts") == 2, "Recreation and fresh Activity must rehash private copy without provider reopen")
        verify(launchCount.get() == 6 && launches.size == 6,
            "Expected exactly six actual OPEN_DOCUMENT launches; observed=${launchCount.get().coerceIn(0, 17)} recorded=${launches.size}")
        // Private proof only. The external controller must verify process exit before selecting readback.
        io {
            val proof = JSONObject().put("version", 1).put("pid", Process.myPid())
                .put("start", Process.getStartElapsedRealtime()).toString().toByteArray(Charsets.US_ASCII)
            Files.newOutputStream(File(root, "picker-process-proof-v1.json").toPath(), CREATE_NEW, WRITE, NOFOLLOW_LINKS).use { it.write(proof) }
        }
    }

    /** Run separately only after the controller has independently observed first-process exit. */
    @Test fun verifiedCopyReopensAfterActualProcessRestart(): Unit = safe {
        verify(context.packageName == "org.locallore.app.modelpickerverify", "Wrong synthetic fixture installation")
        val root = io { ModelPickerFixture.root(context) }
        io {
            val proofFile = File(root, "picker-process-proof-v1.json")
            verify(Files.isRegularFile(proofFile.toPath(), NOFOLLOW_LINKS) && proofFile.length() in 1..256,
                "First-phase private process proof is required")
            val proof = JSONObject(proofFile.readText(Charsets.US_ASCII))
            verify(proof.keys().asSequence().toSet() == setOf("version", "pid", "start") && proof.getInt("version") == 1,
                "Process proof format must be exact")
            verify(proof.getInt("pid") != Process.myPid() || proof.getLong("start") != Process.getStartElapsedRealtime(),
                "Readback requires a different actual process, not Activity recreation")
        }
        beginActivity(); awaitPhase(LocalModelSetupPhase.READY); verifiedCopy(root)
        compose.onNodeWithTag("model-start").performScrollTo().assertIsEnabled()
        verify(launchCount.get() == 0, "Process readback must not launch the picker")
        noPersistedGrant()
    }

    private fun beginActivity() {
        if (priorAccessibilityFlags == null) {
            val info = instrumentation.uiAutomation.serviceInfo
            priorAccessibilityFlags = info.flags
            info.flags = info.flags or AccessibilityServiceInfo.FLAG_REPORT_VIEW_IDS
            instrumentation.uiAutomation.serviceInfo = info
        }
        if (!observing) { instrumentation.addMonitor(monitor); observing = true }
        scenario = ActivityScenario.launch(ModelPickerFixtureActivity::class.java)
        requireNotNull(scenario).onActivity { model = ViewModelProvider(it)[LocalModelSetupViewModel::class.java] }
    }
    private fun awaitPhase(phase: LocalModelSetupPhase) {
        compose.waitUntil(10_000) { model.state.value.phase == phase }
    }
    private fun recreateBehindPicker(original: ModelPickerFixtureActivity, retained: LocalModelSetupViewModel) {
        val replacement = AtomicReference<ModelPickerFixtureActivity>()
        val lifecycle = ActivityLifecycleMonitorRegistry.getInstance()
        val callback = ActivityLifecycleCallback { activity, stage ->
            if (activity is ModelPickerFixtureActivity && activity !== original && stage == Stage.CREATED) replacement.set(activity)
        }
        try {
            instrumentation.runOnMainSync { lifecycle.addLifecycleCallback(callback); original.recreate() }
            val deadline = SystemClock.elapsedRealtime() + 10_000
            while (replacement.get() == null && SystemClock.elapsedRealtime() < deadline) Thread.yield()
            verify(replacement.get() != null, "Stopped target Activity must be recreated behind the actual picker")
            instrumentation.runOnMainSync {
                model = ViewModelProvider(requireNotNull(replacement.get()))[LocalModelSetupViewModel::class.java]
                verify(model === retained && model.state.value.phase == LocalModelSetupPhase.PICKING,
                    "Recreation must retain exactly the pending picker controller")
            }
        } finally { instrumentation.runOnMainSync { lifecycle.removeLifecycleCallback(callback) } }
    }
    private fun requestPicker() {
        val before = launchCount.get()
        pickerRequested = true
        compose.onNodeWithTag("model-choose").performScrollTo().performClick()
        awaitPackage { it in documents }
        val deadline = SystemClock.elapsedRealtime() + 5_000
        while ((launchCount.get() <= before || launches.size <= before) && SystemClock.elapsedRealtime() < deadline) Thread.yield()
        val observed = launchCount.get()
        verify(observed == before + 1 && before in 0..5,
            "Each picker request must have one actual OPEN_DOCUMENT observation; before=${before.coerceIn(0, 17)} after=${observed.coerceIn(0, 17)}")
        val request = launches.getOrNull(before)
        verify(request != null, "Actual picker request must retain its bounded flag observation; ordinal=${before + 1}")
        requireNotNull(request).let {
            verify(it.wildcard, "Actual picker type must be wildcard; ordinal=${before + 1} wildcard=${it.wildcard}")
            verify(it.localOnly, "Actual picker must request local-only files; ordinal=${before + 1} localOnly=${it.localOnly}")
            verify(it.openable, "Actual picker must request openable documents; ordinal=${before + 1} openable=${it.openable}")
            verify(it.expectedMimeTypes, "Actual picker MIME filter must be one wildcard; ordinal=${before + 1} expectedMimeTypes=${it.expectedMimeTypes}")
        }
    }
    private fun select(kind: String, title: String) {
        requestPicker()
        clickIfPresent { it.contentDescription?.toString() in setOf("Show roots", "Open navigation drawer", "Show locations") }
        clickDocument { it.text?.toString() == "LocalLore model fixtures (${instrumentation.context.packageName})" }
        clickDocument { it.text?.toString() == title }
        val deadline = SystemClock.elapsedRealtime() + 10_000
        while (activePackage() in documents && SystemClock.elapsedRealtime() < deadline) {
            clickIfPresent { it.text?.toString()?.equals("Open", ignoreCase = true) == true }
            Thread.yield()
        }
        awaitPackage { it == context.packageName }; pickerRequested = false
        verify(context.checkUriPermission(source(kind), Process.myPid(), Process.myUid(), Intent.FLAG_GRANT_READ_URI_PERMISSION) ==
            PackageManager.PERMISSION_GRANTED, "Selected synthetic URI must have a real system grant")
    }
    private fun assertSafeFailure() {
        compose.onNodeWithTag("model-setup-status").assertTextEquals(
            "The local file could not be verified. Existing stories are unchanged. Check free space and choose the expected file.")
        compose.onNodeWithTag("model-start").performScrollTo().assertIsNotEnabled()
        compose.onNodeWithTag("model-choose").performScrollTo().assertIsEnabled()
    }
    private fun assertNoPublication(root: File) = io {
        verify(!Files.exists(File(root, "model.litertlm").toPath(), NOFOLLOW_LINKS) &&
            !Files.exists(File(root, "model.part").toPath(), NOFOLLOW_LINKS), "Refused/cancelled imports must leave no published or partial model")
    }
    private fun awaitStoreDrain(root: File) {
        val deadline = SystemClock.elapsedRealtime() + 10_000
        while (SystemClock.elapsedRealtime() < deadline) {
            val returned = io {
                // Do not let this probe recover somebody else's stage: wait for its own cleanup.
                if (Files.exists(File(root, "model.part").toPath(), NOFOLLOW_LINKS)) false
                else try {
                    verify(LocalModelStore(root, ModelPickerFixture.identity).installed() == null,
                        "Cancelled provider must not publish a model")
                    true
                } catch (failure: LocalModelException) {
                    verify(failure.failure == LocalModelFailure.BUSY, "Store drain probe may only encounter an actual busy owner")
                    false
                }
            }
            if (returned) return
            Thread.yield()
        }
        throw AssertionError("Disposed file operation did not actually release its stage and store slot")
    }
    private fun verifiedCopy(root: File) = io {
        val files = requireNotNull(LocalModelStore(root, ModelPickerFixture.identity).installed())
        verify(files.model.readBytes().contentEquals(ModelPickerFixture.bytes()), "Full published bytes must match original immutable fixture")
        val hash = MessageDigest.getInstance("SHA-256").digest(files.model.readBytes()).joinToString("") { "%02x".format(it) }
        verify(hash == ModelPickerFixture.identity.sha256 && files.model.length() == ModelPickerFixture.identity.bytes &&
            files.cache.isDirectory && !Files.exists(File(root, "model.part").toPath(), NOFOLLOW_LINKS),
            "Actual native publication must consume staging and full reopen must verify size and SHA-256")
    }
    private fun source(kind: String) = DocumentsContract.buildDocumentUri(authority, "${requireNotNull(run)}:$kind")
    private fun noPersistedGrant() = verify(context.contentResolver.persistedUriPermissions.none { it.uri.authority == authority },
        "Model setup must not take persisted URI grants")
    private fun control(method: String, token: String): Bundle = io {
        requireNotNull(context.contentResolver.call(Uri.parse("content://$authority.control"), method, null, Bundle().apply { putString("run", token) }))
    }
    private fun configureRun() {
        val configured = io { requireNotNull(context.contentResolver.call(Uri.parse("content://$authority.control"), "configure", null, null)) }
        run = requireNotNull(configured.getString("run"))
        verify(requireNotNull(run).matches(Regex("[a-f0-9]{32}")), "Fixture transaction invalid")
    }
    private fun stats() = control("stats", requireNotNull(run))
    private fun awaitStats(matches: (Bundle) -> Boolean): Bundle {
        val deadline = SystemClock.elapsedRealtime() + 10_000
        while (SystemClock.elapsedRealtime() < deadline) {
            val current = stats()
            verify(current.getInt("failures") == 0, "Proxy fixture callback failed")
            if (matches(current)) return current
            Thread.yield()
        }
        throw AssertionError("Actual provider ownership did not reach expected state")
    }
    private fun drained(): Bundle = awaitStats { it.getInt("active") == 0 && it.getInt("opened") == it.getInt("closed") }

    private fun clickDocument(matches: (AccessibilityNodeInfo) -> Boolean) {
        val deadline = SystemClock.elapsedRealtime() + 10_000
        while (SystemClock.elapsedRealtime() < deadline) { if (clickIfPresent(matches)) return; Thread.yield() }
        throw AssertionError("Expected synthetic DocumentsUI control was not reachable")
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
        val deadline = SystemClock.elapsedRealtime() + 10_000
        while (SystemClock.elapsedRealtime() < deadline) { if (matches(activePackage())) return; Thread.yield() }
        throw AssertionError("Expected synthetic picker/application did not become foreground")
    }
    private fun <T> io(block: suspend () -> T): T = runBlocking { withContext(Dispatchers.IO) {
        verify(Looper.myLooper() != Looper.getMainLooper(), "Fixture file/provider work must remain off Main"); block()
    } }
    private fun verify(condition: Boolean, message: String) { if (!condition) throw AssertionError(message) }
    private fun safe(block: () -> Unit) {
        try { block() }
        catch (failure: AssertionError) { throw failure }
        catch (failure: Exception) {
            throw AssertionError("Synthetic picker boundary failed (${failure.javaClass.simpleName})").also { it.stackTrace = failure.stackTrace }
        }
    }
}

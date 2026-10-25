/* Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0 */
package org.locallore.app

import android.app.Application
import android.app.Instrumentation
import android.content.Intent
import android.os.Looper
import android.os.Process
import androidx.compose.ui.test.*
import androidx.compose.ui.test.junit4.createEmptyComposeRule
import androidx.lifecycle.Lifecycle
import androidx.lifecycle.ViewModelProvider
import androidx.test.core.app.ActivityScenario
import androidx.test.ext.junit.runners.AndroidJUnit4
import androidx.test.filters.SdkSuppress
import androidx.test.platform.app.InstrumentationRegistry
import java.io.ByteArrayInputStream
import java.io.File
import java.nio.ByteBuffer
import java.nio.channels.FileChannel
import java.nio.file.Files
import java.nio.file.LinkOption.NOFOLLOW_LINKS
import java.nio.file.StandardOpenOption.CREATE_NEW
import java.nio.file.StandardOpenOption.WRITE
import java.security.MessageDigest
import java.util.concurrent.atomic.AtomicInteger
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.runBlocking
import kotlinx.coroutines.withContext
import org.json.JSONObject
import org.junit.After
import org.junit.Rule
import org.junit.Test
import org.junit.runner.RunWith

/** Two ordinary separately selected methods. Injected failures never construct SDK/play/workspace. */
@RunWith(AndroidJUnit4::class)
@SdkSuppress(minSdkVersion = 30)
class ModelSetupRecoveryTest {
    @get:Rule val compose = createEmptyComposeRule()
    private val instrumentation get() = InstrumentationRegistry.getInstrumentation()
    private val context get() = instrumentation.targetContext
    private var scenario: ActivityScenario<ModelSetupRecoveryFixtureActivity>? = null
    private lateinit var model: LocalModelSetupViewModel
    private lateinit var activity: ModelSetupRecoveryFixtureActivity
    private val pickerLaunches = AtomicInteger()
    private val playLaunches = AtomicInteger()
    private var observing = false
    private val monitor = object : Instrumentation.ActivityMonitor() {
        override fun onStartActivity(intent: Intent): Instrumentation.ActivityResult? {
            if (intent.action == Intent.ACTION_OPEN_DOCUMENT) pickerLaunches.incrementAndGet()
            if (intent.component?.className in setOf("org.locallore.app.MainActivity", "org.locallore.app.LiteRtPlayActivity")) playLaunches.incrementAndGet()
            return null
        }
    }
    private val countKeys = setOf("seed_imports", "file_imports", "full_checks", "start_attempts", "constructions", "io_violations")
    private val proofKeys = setOf("version", "pid", "start", "uid", "process", "phase", "admission_available", "model_bytes",
        "model_sha256", "cache_sha256", "counts", "old")
    private val oldKeys = setOf("picker_model", "picker_receipt", "interruption_model", "interruption_receipt", "interruption_sentinel", "interruption_cache",
        "pending_model", "pending_ready", "pending_arm", "pending_callback_1", "pending_callback_2", "pending_ready_marker", "pending_kill_request",
        "pending_callback_1_marker", "pending_callback_2_marker")

    @After fun closeOnlyOwnedTestActivity(): Unit = safe {
        try { scenario?.close(); scenario = null }
        finally { if (observing) instrumentation.removeMonitor(monitor) }
    }

    @Test fun startFailuresRequireVerificationAndHoldAdmissionAcrossRecreation(): Unit = safe {
        requireTarget()
        expectCounts(0, 0, 0, 0, 0)
        verify(ModelSetupRecoveryFixture.available, "New process admission must be available")
        val old = io {
            val root = ModelSetupRecoveryFixture.root(context)
            verify(!Files.exists(root.toPath(), NOFOLLOW_LINKS), "First phase requires an absent fixed root; no reset is performed")
            val retained = oldProofs()
            ModelSetupRecoveryFixture.seedImports.incrementAndGet()
            val files = ModelSetupRecoveryFixture.store(context).import { ByteArrayInputStream(ModelPickerFixture.bytes()) }
            writeNew(File(files.cache, "setup-recovery-sentinel-v1.bin"), ModelSetupRecoveryFixture.cacheSentinel)
            verifyCopy()
            retained
        }
        beginActivity(); awaitPhase(LocalModelSetupPhase.READY)
        expectCounts(1, 0, 1, 0, 0)
        compose.onNodeWithTag("model-start").performScrollTo().assertIsEnabled().performClick()
        awaitPhase(LocalModelSetupPhase.FAILED); assertRedactedFailure()
        expectCounts(1, 0, 1, 1, 0)
        verify(ModelSetupRecoveryFixture.available, "Pre-admission failure must leave production reservation available")
        compose.onNodeWithTag("model-start").performScrollTo().assertIsNotEnabled().performTouchInput { click() }
        expectCounts(1, 0, 1, 1, 0)
        compose.onNodeWithTag("model-recheck").performScrollTo().assertIsEnabled().performClick()
        awaitPhase(LocalModelSetupPhase.READY)
        expectCounts(1, 0, 2, 1, 0)
        compose.onNodeWithTag("model-start").performScrollTo().assertIsEnabled().performClick()
        awaitPhase(LocalModelSetupPhase.FAILED); assertRedactedFailure()
        expectCounts(1, 0, 2, 2, 1)
        verify(!ModelSetupRecoveryFixture.available, "Actual production constructor reservation must remain claimed after failure")

        // FAILED still exposes Choose. Its actual beginPicker admission must refuse BEFORE launch.
        compose.onNodeWithTag("model-choose").performScrollTo().assertIsEnabled().performClick()
        awaitPhase(LocalModelSetupPhase.SESSION_HELD)
        assertHeld(); assertNoLaunches(); expectCounts(1, 0, 2, 2, 1)
        for (tag in listOf("model-choose", "model-start", "model-recheck")) {
            compose.onNodeWithTag(tag).performScrollTo().assertIsNotEnabled().performTouchInput { click() }
        }
        assertHeld(); assertNoLaunches(); expectCounts(1, 0, 2, 2, 1)
        requireNotNull(scenario).moveToState(Lifecycle.State.CREATED)
        requireNotNull(scenario).moveToState(Lifecycle.State.RESUMED)
        awaitPhase(LocalModelSetupPhase.SESSION_HELD)
        assertHeld(); expectCounts(1, 0, 2, 2, 1)
        val previousModel = model
        val previousActivity = activity
        val pid = Process.myPid(); val start = Process.getStartElapsedRealtime()
        requireNotNull(scenario).close(); scenario = null
        beginActivity(); awaitPhase(LocalModelSetupPhase.SESSION_HELD)
        verify(model !== previousModel && activity !== previousActivity && Process.myPid() == pid && Process.getStartElapsedRealtime() == start,
            "Fresh Activity/controller in the same actual process must retain the claimed admission")
        assertHeld(); assertNoLaunches(); expectCounts(1, 0, 2, 2, 1)
        io {
            verifyCopy()
            verify(sameOld(old, oldProofs()), "Setup failures and same-process relaunch must preserve all fifteen older files")
            val root = ModelSetupRecoveryFixture.root(context)
            writeProof(root, "held", "SESSION_HELD", old)
        }
    }

    @Test fun freshProcessRechecksHeldSessionModelWithoutImport(): Unit = safe {
        requireTarget()
        expectCounts(0, 0, 0, 0, 0)
        verify(ModelSetupRecoveryFixture.available, "Fresh actual process must have a new production admission")
        val held = io {
            val root = ModelSetupRecoveryFixture.root(context)
            exactMarker(root, "held-ready-v1.txt", "held-ready-v1\n")
            val proof = readProof(File(root, "held-proof-v1.json"))
            verify(keys(proof) == proofKeys && proof.getInt("version") == 1 && proof.getString("phase") == "SESSION_HELD" &&
                !proof.getBoolean("admission_available"), "Held process proof must have exact closed schema and claimed phase")
            verify(proof.getInt("uid") == context.applicationInfo.uid && proof.getString("process") == context.applicationInfo.processName &&
                proof.getInt("pid") > 0 && proof.getLong("start") > 0 &&
                (proof.getInt("pid") != Process.myPid() || proof.getLong("start") != Process.getStartElapsedRealtime()),
                "Second method requires a different actual target process, never a fake admission reset")
            verifyCounts(proof.getJSONObject("counts"), 1, 0, 2, 2, 1)
            verifyCopy()
            verify(proof.getLong("model_bytes") == 63L && proof.getString("model_sha256") == ModelSetupRecoveryFixture.identity.sha256 &&
                proof.getString("cache_sha256") == hash(cacheSentinel()) && sameOld(proof.getJSONObject("old"), oldProofs()),
                "Fresh process must retain model/cache and all fifteen older files before Activity launch")
            // Direct verification is separate from the counted controller checks.
            verify(ModelSetupRecoveryFixture.store(context).installed() != null, "Actual store must fully rehash the unchanged private copy before Activity launch")
            proof
        }
        expectCounts(0, 0, 0, 0, 0)
        beginActivity(); awaitPhase(LocalModelSetupPhase.READY)
        verify(ModelSetupRecoveryFixture.available, "Checking a retained copy must not claim an inference owner")
        expectCounts(0, 0, 1, 0, 0); assertNoLaunches()
        compose.onNodeWithTag("model-start").performScrollTo().assertIsEnabled()
        io {
            verifyCopy()
            verify(sameOld(held.getJSONObject("old"), oldProofs()), "Fresh READY check must preserve all fifteen older files")
            val root = ModelSetupRecoveryFixture.root(context)
            writeProof(root, "fresh", "READY", held.getJSONObject("old"), hash(File(root, "held-proof-v1.json")))
        }
        expectCounts(0, 0, 1, 0, 0); assertNoLaunches()
    }

    private fun beginActivity() {
        if (!observing) { instrumentation.addMonitor(monitor); observing = true }
        scenario = ActivityScenario.launch(ModelSetupRecoveryFixtureActivity::class.java)
        requireNotNull(scenario).onActivity {
            verify(it.applicationInfo.uid == context.applicationInfo.uid && it.applicationInfo.processName == context.applicationInfo.processName,
                "Private recovery Activity must have the exact target identity")
            activity = it
            model = ViewModelProvider(it)[LocalModelSetupViewModel::class.java]
        }
    }
    private fun awaitPhase(phase: LocalModelSetupPhase) { compose.waitUntil(5_000) { model.state.value.phase == phase } }
    private fun assertRedactedFailure() {
        compose.onNodeWithTag("model-setup-status").assertTextEquals("The local story screen could not open. Check the model copy and try again.")
        compose.onNodeWithTag("model-start").performScrollTo().assertIsNotEnabled()
        compose.onAllNodes(hasText("PRIVATE_SETUP", substring = true)).assertCountEquals(0)
    }
    private fun assertHeld() {
        compose.onNodeWithTag("model-setup-status").assertTextEquals("Close the app completely before starting another local session.")
        verify(!ModelSetupRecoveryFixture.available, "Held process admission must never be released by lifecycle events")
    }
    private fun assertNoLaunches() = verify(pickerLaunches.get() == 0 && playLaunches.get() == 0,
        "Synthetic failure/held recovery must not launch a document picker or play Activity")
    private fun expectCounts(seed: Int, imports: Int, checks: Int, starts: Int, constructions: Int) =
        verifyCounts(ModelSetupRecoveryFixture.counts(), seed, imports, checks, starts, constructions)
    private fun verifyCounts(value: JSONObject, seed: Int, imports: Int, checks: Int, starts: Int, constructions: Int) {
        verify(keys(value) == countKeys && value.getInt("seed_imports") == seed && value.getInt("file_imports") == imports &&
            value.getInt("full_checks") == checks && value.getInt("start_attempts") == starts &&
            value.getInt("constructions") == constructions && value.getInt("io_violations") == 0, "Actual setup operation counters must match the selected phase")
    }
    private fun verifyCopy() {
        val root = ModelSetupRecoveryFixture.root(context)
        val model = File(root, "model.litertlm")
        verify(!Files.exists(File(root, "model.part").toPath(), NOFOLLOW_LINKS) && Files.isRegularFile(model.toPath(), NOFOLLOW_LINKS) &&
            model.length() == 63L && model.readBytes().contentEquals(ModelPickerFixture.bytes()) && hash(model) == ModelSetupRecoveryFixture.identity.sha256,
            "Native-published synthetic model must remain whole and unchanged with no staging file")
        val cache = cacheSentinel()
        verify(Files.isRegularFile(cache.toPath(), NOFOLLOW_LINKS) && cache.length() <= 128 &&
            cache.readBytes().contentEquals(ModelSetupRecoveryFixture.cacheSentinel), "Fixed new cache sentinel must remain byte-identical")
    }
    private fun cacheSentinel() = File(ModelSetupRecoveryFixture.root(context), "cache/setup-recovery-sentinel-v1.bin")
    private fun oldProofs(): JSONObject {
        val proof = ModelPickerPendingFixture.oldProofs(context)
        val anchor = context.applicationContext.noBackupFilesDir.canonicalFile
        val pending = File(anchor, "model-picker-pending-v2")
        verify(!Files.exists(File(pending, "model.part").toPath(), NOFOLLOW_LINKS), "Older pending fixture must retain no stage; no recovery/delete is performed")
        for ((key, name, cap) in listOf(Triple("pending_model", "model.litertlm", 63),
            Triple("pending_ready", "pending-ready-proof-v1.json", 2048), Triple("pending_arm", "pending-arm-proof-v1.json", 2048),
            Triple("pending_callback_1", "callback-1-v1.json", 2048), Triple("pending_callback_2", "callback-2-v1.json", 2048),
            Triple("pending_ready_marker", "ready-marker-v1.txt", 9), Triple("pending_kill_request", "kill-request-v1.txt", 8),
            Triple("pending_callback_1_marker", "callback-1-ready-v1.txt", 18), Triple("pending_callback_2_marker", "callback-2-ready-v1.txt", 18))) {
            val file = File(pending, name)
            verify(Files.isRegularFile(file.toPath(), NOFOLLOW_LINKS) && file.length() in 1..cap.toLong(), "Required older pending file must be bounded and regular")
            proof.put(key, hash(file))
        }
        verify(proof.getString("pending_model") == ModelPickerFixture.identity.sha256, "Older pending model must match original full hash")
        return proof
    }
    private fun writeProof(root: File, stem: String, phase: String, old: JSONObject, heldHash: String? = null) {
        val value = JSONObject().put("version", 1).put("pid", Process.myPid()).put("start", Process.getStartElapsedRealtime())
            .put("uid", Process.myUid()).put("process", Application.getProcessName()).put("phase", phase)
            .put("admission_available", ModelSetupRecoveryFixture.available).put("model_bytes", 63)
            .put("model_sha256", hash(File(root, "model.litertlm"))).put("cache_sha256", hash(cacheSentinel()))
            .put("counts", ModelSetupRecoveryFixture.counts()).put("old", old)
        if (heldHash != null) value.put("held_sha256", heldHash)
        val bytes = value.toString().toByteArray(Charsets.US_ASCII)
        verify(bytes.size in 1..4096, "Process proof exceeds its fixed bound")
        writeNew(File(root, "$stem-proof-v1.json"), bytes)
        writeNew(File(root, "$stem-ready-v1.txt"), "$stem-ready-v1\n".toByteArray(Charsets.US_ASCII))
    }
    private fun readProof(file: File): JSONObject {
        verify(Files.isRegularFile(file.toPath(), NOFOLLOW_LINKS) && file.length() in 1..4096, "Held process proof must be bounded and regular")
        return JSONObject(file.readText(Charsets.US_ASCII))
    }
    private fun exactMarker(root: File, name: String, text: String) {
        val file = File(root, name)
        verify(Files.isRegularFile(file.toPath(), NOFOLLOW_LINKS) && file.length() == text.length.toLong() &&
            file.readBytes().contentEquals(text.toByteArray(Charsets.US_ASCII)), "Completion marker must be exact")
    }
    private fun writeNew(file: File, bytes: ByteArray) {
        FileChannel.open(file.toPath(), CREATE_NEW, WRITE, NOFOLLOW_LINKS).use { channel ->
            val buffer = ByteBuffer.wrap(bytes)
            while (buffer.hasRemaining()) channel.write(buffer)
            channel.force(true)
        }
    }
    private fun hash(file: File) = MessageDigest.getInstance("SHA-256").digest(file.readBytes()).joinToString("") { "%02x".format(it) }
    private fun keys(value: JSONObject) = value.keys().asSequence().toSet()
    private fun sameOld(left: JSONObject, right: JSONObject) = keys(left) == oldKeys && keys(right) == oldKeys &&
        oldKeys.all { left.getString(it).matches(Regex("[a-f0-9]{64}")) && left.getString(it) == right.getString(it) }
    private fun requireTarget() = verify(context.packageName == "org.locallore.app.modelpickerverify" &&
        Process.myUid() == context.applicationInfo.uid && Application.getProcessName() == context.applicationInfo.processName,
        "Selected test must execute in the exact target UID/process")
    private fun <T> io(block: suspend () -> T): T = runBlocking { withContext(Dispatchers.IO) {
        verify(Looper.myLooper() != Looper.getMainLooper(), "Fixture file verification must stay off Main"); block()
    } }
    private fun verify(condition: Boolean, message: String) { if (!condition) throw AssertionError(message) }
    private fun safe(block: () -> Unit) {
        try { block() } catch (failure: AssertionError) { throw failure }
        catch (failure: Exception) { throw AssertionError("Synthetic setup recovery boundary failed (${failure.javaClass.simpleName})").also { it.stackTrace = failure.stackTrace } }
    }
}

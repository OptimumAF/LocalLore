/* Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0 */
package org.locallore.app

import android.app.Application
import android.app.Instrumentation
import android.content.Intent
import android.os.Bundle
import android.os.Looper
import android.os.Process
import android.os.SystemClock
import android.view.accessibility.AccessibilityNodeInfo
import androidx.lifecycle.ViewModelProvider
import androidx.test.ext.junit.runners.AndroidJUnit4
import androidx.test.platform.app.InstrumentationRegistry
import androidx.test.filters.SdkSuppress
import java.io.File
import java.nio.file.Files
import java.nio.file.LinkOption.NOFOLLOW_LINKS
import java.util.concurrent.CopyOnWriteArrayList
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.runBlocking
import kotlinx.coroutines.withContext
import org.json.JSONObject
import org.junit.Test
import org.junit.runner.RunWith

/** Plain no-restart instrumentation: observer never launches, recreates or closes an Activity. */
@RunWith(AndroidJUnit4::class)
@SdkSuppress(minSdkVersion = 30)
@Suppress("DEPRECATION")
class ModelPickerPendingTest {
    private val instrumentation get() = InstrumentationRegistry.getInstrumentation()
    private val context get() = instrumentation.targetContext
    private val documents = setOf("com.android.documentsui", "com.google.android.documentsui")
    private val readyKeys = setOf("version", "pid", "start", "uid", "process", "task_id", "run", "local_saved", "phase", "old")
    private val oldKeys = setOf("picker_model", "picker_receipt", "interruption_model", "interruption_receipt", "interruption_sentinel", "interruption_cache")
    private val callbackKeys = setOf("version", "ordinal", "pid", "start", "uid", "process", "task_id", "saved_restored", "selected",
        "before", "after", "run", "attempts", "opened", "closed", "active", "failures")

    @Test fun armPendingPickerAndTerminateOwnProcess(): Unit = safe {
        requireTarget()
        val root = io { ModelPickerPendingFixture.root(context) }
        val old = io {
            verify(!Files.exists(root.toPath(), NOFOLLOW_LINKS), "Pending arm requires a new fixed root; no reset is performed")
            val proof = ModelPickerPendingFixture.oldProofs(context)
            Files.createDirectory(root.toPath())
            proof
        }
        val run = io {
            val result = requireNotNull(context.contentResolver.call(
                android.net.Uri.parse("content://org.locallore.app.modelpickerverify.test.modelpicker.control"), "configure", null, null))
            requireNotNull(result.getString("run")).also { verify(it.matches(Regex("[a-f0-9]{32}")), "Fixed provider transaction invalid") }
        }
        val requests = CopyOnWriteArrayList<Int>()
        val monitor = object : Instrumentation.ActivityMonitor() {
            override fun onStartActivity(intent: Intent): Instrumentation.ActivityResult? {
                if (intent.action == Intent.ACTION_OPEN_DOCUMENT && requests.size < 4) {
                    requests.add((if (intent.type == "*/*") 1 else 0) or
                        (if (intent.hasCategory(Intent.CATEGORY_OPENABLE)) 2 else 0) or
                        (if (intent.getBooleanExtra(Intent.EXTRA_LOCAL_ONLY, false)) 4 else 0) or
                        (if (intent.getStringArrayExtra(Intent.EXTRA_MIME_TYPES)?.contentEquals(arrayOf("*/*")) == true) 8 else 0))
                }
                return null
            }
        }
        instrumentation.addMonitor(monitor)
        // No ActivityScenario/CLEAR_TASK: retain the real task and framework result relationship.
        val activity = instrumentation.startActivitySync(Intent(context, ModelPickerPendingFixtureActivity::class.java)
            .addFlags(Intent.FLAG_ACTIVITY_NEW_TASK)) as ModelPickerPendingFixtureActivity
        lateinit var model: LocalModelSetupViewModel
        var taskId = -1
        instrumentation.runOnMainSync {
            verify(activity.applicationInfo.uid == context.applicationInfo.uid && activity.applicationInfo.processName == context.applicationInfo.processName,
                "Actual fixture Activity must have the exact target identity")
            model = ViewModelProvider(activity)[LocalModelSetupViewModel::class.java]
            taskId = activity.taskId
        }
        verify(taskId >= 0, "Actual private Activity must have a valid server task identifier")
        await { model.state.value.phase == LocalModelSetupPhase.MISSING }
        clickChooseOnOwnedApp(model, requests)
        await { activePackage() in documents }
        await { activity.localStateSaved && model.state.value.phase == LocalModelSetupPhase.PICKING }
        verify(ModelPickerPendingFixture.callbackCount.get() == 0 && !ModelPickerPendingFixture.callbackOverflow.get() &&
            !ModelPickerPendingFixture.receiptError.get() && ModelPickerPendingFixture.receiptWriters.get() == 0,
            "Pending old process must not have observed any picker result")
        verify(requests.size == 1 && requests.single() == 15,
            "Arm requires one real local-only/openable picker request; count=${requests.size} flags=${requests.firstOrNull() ?: 0}")
        val ready = io {
            noSourceOpened(run)
            noModelOrStage(root)
            verify(sameOld(old, ModelPickerPendingFixture.oldProofs(context)), "Older fixture bytes must remain unchanged before ready proof")
            identity(taskId).put("run", run).put("local_saved", activity.localStateSaved)
                .put("phase", model.state.value.phase.name).put("old", old).also {
                    ModelPickerPendingFixture.writeJson(File(root, "pending-ready-proof-v1.json"), it, 2048)
                    ModelPickerPendingFixture.writeNew(File(root, "ready-marker-v1.txt"), "ready-v1\n".toByteArray(Charsets.US_ASCII))
                }
        }
        instrumentation.sendStatus(2, Bundle().apply { putString("locallore_pending", "waiting-for-kill-v1") })
        // Only the host may write this exact handshake after independent server STOPPED/haveState/
        // nonnull mIcicle proof for this component and task. A local save flag alone is insufficient.
        val deadline = SystemClock.elapsedRealtime() + 30_000
        var handshake = false
        while (!handshake && SystemClock.elapsedRealtime() < deadline) {
            handshake = io {
                val file = File(root, "kill-request-v1.txt")
                if (!Files.exists(file.toPath(), NOFOLLOW_LINKS)) false else {
                    verify(Files.isRegularFile(file.toPath(), NOFOLLOW_LINKS) && file.length() == 8L &&
                        file.readBytes().contentEquals("kill-v1\n".toByteArray(Charsets.US_ASCII)), "Fixed kill handshake must be exact and regular")
                    true
                }
            }
            if (!handshake) Thread.sleep(20)
        }
        verify(handshake, "Server-state kill handshake did not arrive before finite arm deadline")
        requireTarget()
        verify(activity.localStateSaved && model.state.value.phase == LocalModelSetupPhase.PICKING && activePackage() in documents,
            "Actual picker must remain pending and saved before self-process death")
        verify(ModelPickerPendingFixture.callbackCount.get() == 0 && !ModelPickerPendingFixture.callbackOverflow.get() &&
            !ModelPickerPendingFixture.receiptError.get() && ModelPickerPendingFixture.receiptWriters.get() == 0,
            "No callback or receipt writer may precede pending-picker termination")
        instrumentation.runOnMainSync { verify(activity.taskId == taskId && !activity.isFinishing, "Saved target task must remain the same and nonfinishing") }
        io {
            noSourceOpened(run); noModelOrStage(root)
            verify(sameOld(old, ModelPickerPendingFixture.oldProofs(context)), "Older fixture bytes must remain unchanged before self-process death")
            val proof = identity(taskId).put("run", run).put("local_saved", true).put("phase", "PICKING").put("old", old)
                .put("ready_sha256", ModelPickerPendingFixture.hash(File(root, "pending-ready-proof-v1.json")))
            verify(proof.getInt("pid") == ready.getInt("pid") && proof.getLong("start") == ready.getLong("start"),
                "Ready and armed proof must describe one actual process")
            ModelPickerPendingFixture.writeJson(File(root, "pending-arm-proof-v1.json"), proof, 2048)
        }
        instrumentation.sendStatus(2, Bundle().apply { putString("locallore_pending", "pending-picker-armed-v1") })
        Process.killProcess(Process.myPid())
        throw AssertionError("Self-process termination did not occur")
    }

    @Test fun observeRestoredPickerAndFreshImport(): Unit = safe {
        requireTarget()
        // Deliberately no rule, Activity launch, lifecycle mutation or registry delivery here.
        io {
            val root = ModelPickerPendingFixture.root(context)
            verify(ModelPickerPendingFixture.callbackCount.get() == 2 && !ModelPickerPendingFixture.callbackOverflow.get(),
                "Restored current process must have observed exactly two actual callbacks without overflow")
            val writerDeadline = SystemClock.elapsedRealtime() + 5_000
            while (ModelPickerPendingFixture.receiptWriters.get() != 0 && SystemClock.elapsedRealtime() < writerDeadline) Thread.sleep(10)
            verify(ModelPickerPendingFixture.receiptWriters.get() == 0 && !ModelPickerPendingFixture.receiptError.get(),
                "Actual callback receipt jobs must have completed without hidden write/cancellation errors")
            exactMarker(root, "ready-marker-v1.txt", "ready-v1\n")
            exactMarker(root, "kill-request-v1.txt", "kill-v1\n")
            exactMarker(root, "callback-1-ready-v1.txt", "callback-ready-v1\n")
            exactMarker(root, "callback-2-ready-v1.txt", "callback-ready-v1\n")
            verify(!Files.exists(File(root, "callback-overflow-v1.txt").toPath(), NOFOLLOW_LINKS), "Extra framework callbacks must not be hidden")
            val readyFile = File(root, "pending-ready-proof-v1.json")
            val armFile = File(root, "pending-arm-proof-v1.json")
            val ready = ModelPickerPendingFixture.readJson(readyFile, 2048)
            val arm = ModelPickerPendingFixture.readJson(armFile, 2048)
            verify(keys(ready) == readyKeys && keys(arm) == readyKeys + "ready_sha256", "Ready and arm proof schemas must be exact")
            for (proof in listOf(ready, arm)) {
                verify(proof.getInt("version") == 1 && proof.getBoolean("local_saved") && proof.getString("phase") == "PICKING",
                    "Old process must have actually saved its pending picker state")
                verify(proof.getInt("uid") == context.applicationInfo.uid && proof.getString("process") == context.applicationInfo.processName &&
                    proof.getInt("pid") > 0 && proof.getLong("start") > 0 && proof.getInt("task_id") >= 0,
                    "Old proof must describe the exact target process and actual task")
            }
            verify(ready.getInt("pid") == arm.getInt("pid") && ready.getLong("start") == arm.getLong("start") &&
                ready.getInt("task_id") == arm.getInt("task_id") && ready.getString("run") == arm.getString("run") &&
                arm.getString("ready_sha256") == ModelPickerPendingFixture.hash(readyFile), "Ready proof must match final armed process/task")
            verify(arm.getInt("pid") != Process.myPid() || arm.getLong("start") != Process.getStartElapsedRealtime(),
                "Observer must run in a different process than the terminated pending picker")
            val run = arm.getString("run")
            verify(run.matches(Regex("[a-f0-9]{32}")), "Armed provider transaction invalid")
            val one = ModelPickerPendingFixture.readJson(File(root, "callback-1-v1.json"), 2048)
            val two = ModelPickerPendingFixture.readJson(File(root, "callback-2-v1.json"), 2048)
            for ((ordinal, callback) in listOf(1 to one, 2 to two)) {
                verify(keys(callback) == callbackKeys && callback.getInt("version") == 1 && callback.getInt("ordinal") == ordinal &&
                    callback.getBoolean("selected") && callback.getBoolean("saved_restored"), "Actual callback receipt must have exact primitive schema and restored saved state")
                verify(callback.getInt("pid") == Process.myPid() && callback.getLong("start") == Process.getStartElapsedRealtime() &&
                    callback.getInt("uid") == Process.myUid() && callback.getString("process") == Application.getProcessName() &&
                    callback.getInt("task_id") == arm.getInt("task_id") && callback.getString("run") == run,
                    "Both actual callbacks must belong to the same restored task and current process")
                verify(callback.getInt("failures") == 0 && callback.getInt("attempts") in 0..1 && callback.getInt("opened") in 0..1 &&
                    callback.getInt("closed") in 0..1 && callback.getInt("active") in 0..1,
                    "Callback provider observations must remain bounded and failure-free")
            }
            verify(one.getString("before") in LocalModelSetupPhase.entries.map { it.name } && one.getString("before") != "PICKING" &&
                one.getString("after") == one.getString("before") && listOf("attempts", "opened", "closed", "active").all { one.getInt(it) == 0 },
                "Restored old selection must be rejected by the fresh controller without opening any source")
            verify(two.getString("before") == "PICKING" && two.getString("after") == "IMPORTING",
                "Only the later explicit selection may enter a real import")
            val drainDeadline = SystemClock.elapsedRealtime() + 5_000
            var drained = false
            while (!drained && SystemClock.elapsedRealtime() < drainDeadline) {
                val stats = ModelPickerPendingFixture.stats(context, run)
                verify(stats.getInt("failures") == 0 && listOf("attempts", "opened", "closed", "active").all { stats.getInt(it) in 0..1 },
                    "Fresh provider observations must remain bounded and failure-free")
                drained = stats.getInt("attempts") == 1 && stats.getInt("opened") == 1 && stats.getInt("closed") == 1 && stats.getInt("active") == 0
                if (!drained) Thread.sleep(10)
            }
            verify(drained, "Exactly one fresh selected provider descriptor must actually drain")
            verify(!Files.exists(File(root, "model.part").toPath(), NOFOLLOW_LINKS),
                "Fresh native publication must already have consumed staging before observer store reopen")
            val files = requireNotNull(LocalModelStore(root, ModelPickerPendingFixture.identity).installed())
            verify(files.model.length() == 63L && files.model.readBytes().contentEquals(ModelPickerFixture.bytes()) &&
                ModelPickerPendingFixture.hash(files.model) == ModelPickerPendingFixture.identity.sha256 &&
                !Files.exists(File(root, "model.part").toPath(), NOFOLLOW_LINKS), "Fresh selection must publish and rehash exact original bytes through real native store")
            verify(sameOld(ready.getJSONObject("old"), arm.getJSONObject("old")) &&
                sameOld(arm.getJSONObject("old"), ModelPickerPendingFixture.oldProofs(context)), "Both older fixture roots/model/proofs/sentinels must remain byte-identical")
            verify(context.contentResolver.persistedUriPermissions.none { it.uri.authority == "org.locallore.app.modelpickerverify.test.modelpicker" },
                "Pending/result recovery must not persist a document grant")
            verify(ModelPickerPendingFixture.callbackCount.get() == 2 && !ModelPickerPendingFixture.callbackOverflow.get() &&
                !ModelPickerPendingFixture.receiptError.get() && ModelPickerPendingFixture.receiptWriters.get() == 0,
                "Exactly two callbacks and all receipt jobs must remain terminal throughout read-only verification")
        }
    }

    private fun identity(taskId: Int): JSONObject = JSONObject().put("version", 1).put("pid", Process.myPid())
        .put("start", Process.getStartElapsedRealtime()).put("uid", Process.myUid()).put("process", Application.getProcessName()).put("task_id", taskId)
    private fun requireTarget() {
        verify(InstrumentationRegistry.getArguments().getString("waitForActivitiesToComplete") == "false",
            "Selected no-restart instrumentation must explicitly disable Activity finishing")
        verify(context.packageName == "org.locallore.app.modelpickerverify" &&
            Process.myUid() == context.applicationInfo.uid && Application.getProcessName() == context.applicationInfo.processName,
            "Only the exact target UID/process may arm or observe this fixed fixture")
    }
    private fun noSourceOpened(run: String) {
        val value = ModelPickerPendingFixture.stats(context, run)
        verify(listOf("attempts", "opened", "closed", "active", "failures").all { value.getInt(it) == 0 },
            "Pending picker must not open a provider descriptor")
    }
    private fun noModelOrStage(root: File) = verify(listOf("model.litertlm", "model.part").none {
        Files.exists(File(root, it).toPath(), NOFOLLOW_LINKS) }, "Pending picker must have no partial or published model")
    private fun exactMarker(root: File, name: String, expected: String) {
        val file = File(root, name)
        verify(Files.isRegularFile(file.toPath(), NOFOLLOW_LINKS) && file.length() == expected.length.toLong() &&
            file.readBytes().contentEquals(expected.toByteArray(Charsets.US_ASCII)), "Fixed completion/handshake marker must be exact")
    }
    private fun keys(value: JSONObject) = value.keys().asSequence().toSet()
    private fun sameOld(left: JSONObject, right: JSONObject) = keys(left) == oldKeys && keys(right) == oldKeys &&
        oldKeys.all { left.getString(it).matches(Regex("[a-f0-9]{64}")) && left.getString(it) == right.getString(it) }
    private fun await(matches: () -> Boolean) {
        val deadline = SystemClock.elapsedRealtime() + 5_000
        while (SystemClock.elapsedRealtime() < deadline) { if (matches()) return; Thread.sleep(10) }
        throw AssertionError("Expected owned picker/lifecycle state was not observed")
    }
    private enum class PendingWindow { UNREADY, OWNED, PICKER, FOREIGN }
    private fun clickChooseOnOwnedApp(model: LocalModelSetupViewModel, requests: List<Int>) {
        val deadline = SystemClock.elapsedRealtime() + 5_000
        var unready = 0
        var owned = 0
        var scrolls = 0
        var identityReady = false
        var last = PendingWindow.UNREADY
        while (SystemClock.elapsedRealtime() < deadline) {
            last = pendingWindow()
            when (last) {
                PendingWindow.UNREADY -> unready++ // A missing/unready window permits no UI action.
                PendingWindow.OWNED -> {
                    owned++
                    if (!identityReady) {
                        identityReady = visiblePendingIdentity()
                        if (!identityReady) { unready++; Thread.sleep(20); continue }
                    }
                    if (actOnAppNode({ it.text?.toString() == "Choose local model file" }, AccessibilityNodeInfo.ACTION_CLICK)) return
                    // Accessibility may return false after a dispatched action. Source observations,
                    // followed by the caller's actual DocsUI/save checks, establish that transition.
                    if (requests.size == 1 && model.state.value.phase == LocalModelSetupPhase.PICKING) return
                    if (scrolls < 8) {
                        scrolls++ // Bound attempts even when an accepted dispatch reports false.
                        actOnAppNode({ it.isScrollable }, AccessibilityNodeInfo.ACTION_SCROLL_FORWARD)
                    }
                }
                PendingWindow.PICKER -> {
                    verify(requests.size == 1 && model.state.value.phase == LocalModelSetupPhase.PICKING,
                        "Unexpected picker window before an owned request (PICKER)")
                    return
                }
                PendingWindow.FOREIGN -> throw AssertionError("Choose readiness refused (FOREIGN; owned=${owned.coerceAtMost(255)} unready=${unready.coerceAtMost(255)} scrolls=$scrolls identity=${if (identityReady) 1 else 0})")
            }
            Thread.sleep(20)
        }
        throw AssertionError("Choose readiness deadline ($last; owned=${owned.coerceAtMost(255)} unready=${unready.coerceAtMost(255)} scrolls=$scrolls identity=${if (identityReady) 1 else 0})")
    }
    private fun visiblePendingIdentity(): Boolean {
        val root = instrumentation.uiAutomation.rootInActiveWindow ?: return false
        if (root.packageName?.toString() != context.packageName) { root.recycle(); return false }
        var visited = 0
        fun walk(node: AccessibilityNodeInfo, depth: Int): Boolean {
            if (++visited > 2048 || depth > 32) return false
            if (node.packageName?.toString() == context.packageName && node.isVisibleToUser &&
                node.text?.toString() == "Expected model · synthetic-picker-pending-v2") return true
            for (index in 0 until node.childCount) {
                val child = node.getChild(index) ?: continue
                try { if (walk(child, depth + 1)) return true } finally { child.recycle() }
            }
            return false
        }
        return try { walk(root, 0) } finally { root.recycle() }
    }
    private fun pendingWindow(): PendingWindow {
        val root = instrumentation.uiAutomation.rootInActiveWindow ?: return PendingWindow.UNREADY
        return try {
            when (root.packageName?.toString()) {
                null -> PendingWindow.UNREADY
                context.packageName -> if (root.childCount > 0) PendingWindow.OWNED else PendingWindow.UNREADY
                in documents -> PendingWindow.PICKER
                else -> PendingWindow.FOREIGN
            }
        } finally { root.recycle() }
    }
    private fun actOnAppNode(matches: (AccessibilityNodeInfo) -> Boolean, action: Int): Boolean {
        val root = instrumentation.uiAutomation.rootInActiveWindow ?: return false
        if (root.packageName?.toString() != context.packageName) { root.recycle(); return false }
        var visited = 0
        fun walk(node: AccessibilityNodeInfo, depth: Int): Boolean {
            try {
                if (++visited > 2048 || depth > 32) return false
                if (node.packageName?.toString() == context.packageName && node.isVisibleToUser && node.isEnabled && matches(node)) {
                    var candidate: AccessibilityNodeInfo? = AccessibilityNodeInfo.obtain(node)
                    try {
                        repeat(6) {
                            val current = candidate ?: return@repeat
                            if (current.packageName?.toString() == context.packageName && current.isEnabled && current.performAction(action)) return true
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
    private fun <T> io(block: suspend () -> T): T = runBlocking { withContext(Dispatchers.IO) {
        verify(Looper.myLooper() != Looper.getMainLooper(), "Pending fixture file/provider work must remain off Main"); block()
    } }
    private fun verify(condition: Boolean, message: String) { if (!condition) throw AssertionError(message) }
    private fun safe(block: () -> Unit) {
        try { block() } catch (failure: AssertionError) { throw failure }
        catch (failure: Exception) { throw AssertionError("Synthetic pending boundary failed (${failure.javaClass.simpleName})").also { it.stackTrace = failure.stackTrace } }
    }
}

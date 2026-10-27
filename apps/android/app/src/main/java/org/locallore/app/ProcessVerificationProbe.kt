/* Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0 */
package org.locallore.app

import android.content.Context
import android.os.Process
import android.util.AtomicFile
import org.json.JSONObject
import java.io.File
import java.security.MessageDigest

/** Opt-in, bounded debug receipts. No Activity, text or native payload is retained. */
internal object ProcessVerificationProbe {
    const val RUN_EXTRA = "locallore.process.run_id"
    const val RUN_STATE = "locallore.process.run_id.v1"
    private const val PRODUCT = "org.locallore.app.draftprocessverify"
    private val runPattern = Regex("[0-9a-f]{16}")
    private val keys = listOf("workspace", "branches", "resume", "create", "open", "play_snapshot",
        "free_text", "submit", "prepare", "commit", "cancel", "other", "story_template", "create_named")
    // Known metadata/resource operations do not propose or apply gameplay.
    private val metadata = setOf("close", "capabilities", "model_status")
    private var proofRoot: File? = null
    private var run: String? = null
    private var processRun: String? = null
    private var task = 0
    private var restored = false
    private var factoryCount = 0
    private var sequence = 0
    private var hint: PlayDraftScope? = null
    private val operations = keys.associateWith { 0 }.toMutableMap()

    @Synchronized fun configure(context: Context, runId: String?, taskId: Int, hasSavedState: Boolean) {
        if (!BuildConfig.INPUT_PROCESS_VERIFICATION || context.packageName != PRODUCT ||
            runId == null || !runPattern.matches(runId)) {
            proofRoot = null
            run = null
            return
        }
        check(processRun == null || processRun == runId) { "Verification run changed" }
        processRun = runId
        proofRoot = File(context.applicationContext.noBackupFilesDir, "process-verify-v1")
        run = runId
        task = taskId
        restored = hasSavedState
    }

    @Synchronized fun factoryCreated() {
        if (run == null) return
        check(factoryCount < 16) { "Verification factory bound" }
        factoryCount++
    }

    @Synchronized fun created(scope: PlayDraftScope?) {
        if (run == null) return
        hint = scope
        write("created.json", "created")
    }

    @Synchronized fun saved(scope: PlayDraftScope?) {
        if (run == null) return
        hint = scope
        write("saved.json", "saved_after_super")
    }

    @Synchronized fun operation(operation: String) {
        if (run == null || operation in metadata) return
        val key = if (operation in operations) operation else "other"
        val count = checkNotNull(operations[key])
        check(count < 4096) { "Verification operation bound" }
        operations[key] = count + 1
        write("commands.json", "command")
    }

    private fun write(leaf: String, event: String) {
        val root = checkNotNull(proofRoot)
        val runId = checkNotNull(run)
        check(sequence < 65536) { "Verification sequence bound" }
        sequence++
        val validHint = hint?.takeIf { encodeNavigationHint(it) != null }
        val digest = validHint?.let {
            MessageDigest.getInstance("SHA-256").digest("1\n${it.story}\n${it.branch}\n".toByteArray(Charsets.UTF_8))
                .joinToString("") { byte -> "%02x".format(byte) }
        }
        val record = JSONObject().put("version", 2).put("scope", "locallore_process_verify_v2")
            .put("run_id", runId).put("pid", Process.myPid()).put("uid", Process.myUid())
            .put("task_id", task).put("sequence", sequence)
            .put("process_start_uptime_ms", Process.getStartUptimeMillis()).put("event", event)
            .put("restored_state", restored).put("factory_creations", factoryCount)
            .put("hint_present", validHint != null).put("hint_sha256", digest ?: JSONObject.NULL)
            .put("operations", JSONObject(operations.toMap()))
        val bytes = record.toString().toByteArray(Charsets.UTF_8)
        check(bytes.size <= 4096)
        val directory = File(root, runId)
        check(directory.isDirectory || directory.mkdirs()) { "Verification directory unavailable" }
        val atomic = AtomicFile(File(directory, leaf))
        val output = atomic.startWrite()
        try {
            output.write(bytes)
            atomic.finishWrite(output)
        } catch (failure: Throwable) {
            atomic.failWrite(output)
            throw failure
        }
    }
}

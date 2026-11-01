/* Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0 */
package org.locallore.app

import android.content.Context
import android.os.Process
import android.util.AtomicFile
import org.json.JSONObject
import java.io.File
import java.security.MessageDigest

internal val presentationProcessOperations = listOf("workspace", "branches", "resume", "create", "open", "play_snapshot",
    "play_presentation_v2", "free_text", "submit", "prepare", "commit", "cancel", "other", "story_template", "create_named")

private val presentationProcessMetadata = setOf("close", "capabilities", "model_status", "story_templates", "story_setup",
    "story_presentation", "story_presentation_view", "authoring_capabilities", "authoring_begin", "authoring_generate",
    "authoring_review", "authoring_cancel", "authoring_status")

internal fun presentationProcessOperationKey(operation: String): String? = when {
    operation in presentationProcessMetadata -> null
    operation in setOf("create_configured", "create_presented", "authoring_create") -> "create_named"
    operation in presentationProcessOperations -> operation
    else -> "other"
}

/** Pure bounded encoding; caller supplies actual runtime facts, never a native payload. */
internal fun presentationProcessRecord(run: String, pid: Int, uid: Int, task: Int, sequence: Int, start: Long,
    event: String, restored: Boolean, factories: Int, hint: PlayDraftScope?, operations: Map<String, Int>): ByteArray {
    require(Regex("[0-9a-f]{16}").matches(run) && pid > 0 && uid in 10_000..99_999 && task >= 0 && start >= 0)
    require(sequence in 1..65536 && factories in 0..16 && event in setOf("created", "saved_after_super", "command"))
    require(operations.keys == presentationProcessOperations.toSet() && operations.values.all { it in 0..4096 })
    val validHint = hint?.takeIf { encodeNavigationHint(it) != null }
    val hash = validHint?.let {
        MessageDigest.getInstance("SHA-256").digest("1\n${it.story}\n${it.branch}\n".toByteArray(Charsets.UTF_8))
            .joinToString("") { byte -> "%02x".format(byte) }
    }
    val value = JSONObject().put("version", 3).put("scope", "locallore_presentation_process_verify_v3")
        .put("run_id", run).put("pid", pid).put("uid", uid).put("task_id", task).put("sequence", sequence)
        .put("process_start_uptime_ms", start).put("event", event).put("restored_state", restored)
        .put("factory_creations", factories).put("hint_present", validHint != null)
        .put("hint_sha256", hash ?: JSONObject.NULL).put("operations", JSONObject(operations.toMap()))
    return value.toString().toByteArray(Charsets.UTF_8).also { check(it.size <= 4096) }
}

/** Separate opt-in schema 3. Legacy probe files and counter interpretation remain unchanged. */
internal object PresentationProcessVerificationProbe {
    const val RUN_EXTRA = "locallore.presentation_process.run_id"
    const val RUN_STATE = "locallore.presentation_process.run_id.v3"
    private const val PRODUCT = "org.locallore.app.presentationprocessverify"
    private var proofRoot: File? = null
    private var run: String? = null
    private var processRun: String? = null
    private var task = 0
    private var restored = false
    private var factoryCount = 0
    private var sequence = 0
    private var hint: PlayDraftScope? = null
    private val operations = presentationProcessOperations.associateWith { 0 }.toMutableMap()

    @Synchronized fun configure(context: Context, runId: String?, taskId: Int, hasSavedState: Boolean) {
        if (!BuildConfig.PRESENTATION_PROCESS_VERIFICATION || context.packageName != PRODUCT ||
            runId == null || !Regex("[0-9a-f]{16}").matches(runId)) {
            proofRoot = null; run = null; return
        }
        check(processRun == null || processRun == runId) { "Verification run changed" }
        processRun = runId
        proofRoot = File(context.applicationContext.noBackupFilesDir, "process-verify-v3")
        run = runId; task = taskId; restored = hasSavedState
    }

    @Synchronized fun factoryCreated() {
        if (run == null) return
        check(factoryCount < 16) { "Verification factory bound" }; factoryCount++
    }

    @Synchronized fun created(scope: PlayDraftScope?) {
        if (run == null) return
        hint = scope; write("created.json", "created")
    }

    @Synchronized fun saved(scope: PlayDraftScope?) {
        if (run == null) return
        hint = scope; write("saved.json", "saved_after_super")
    }

    @Synchronized fun operation(operation: String) {
        if (run == null) return
        val key = presentationProcessOperationKey(operation) ?: return
        val count = checkNotNull(operations[key]); check(count < 4096) { "Verification operation bound" }
        operations[key] = count + 1; write("commands.json", "command")
    }

    private fun write(leaf: String, event: String) {
        check(sequence < 65536) { "Verification sequence bound" }; sequence++
        val bytes = presentationProcessRecord(checkNotNull(run), Process.myPid(), Process.myUid(), task, sequence,
            Process.getStartUptimeMillis(), event, restored, factoryCount, hint, operations)
        val directory = File(checkNotNull(proofRoot), checkNotNull(run))
        check(directory.isDirectory || directory.mkdirs()) { "Verification directory unavailable" }
        val atomic = AtomicFile(File(directory, leaf)); val stream = atomic.startWrite()
        try { stream.write(bytes); atomic.finishWrite(stream) }
        catch (failure: Throwable) { atomic.failWrite(stream); throw failure }
    }
}

/* Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0 */
package org.locallore.app

import java.util.Collections

internal enum class CancellationPhase(val file: String, val budgetMs: Long, checks: Set<String>) {
    CANCEL("cancel", 170_000, setOf("prior_import_proof_exact", "memory_eligible", "candidate_access_receipt",
        "accepted_full_recheck", "runtime_guard_passed", "production_transport_local", "gateway_main_confined",
        "canonical_zero_before", "fixed_free_text_submitted_once", "sampled_public_inflight", "cancel_saved_called_once",
        "original_response_joined", "response_rejected_cancelled", "no_prepared_or_commit", "sdk_cancel_entered_returned",
        "worker_drain_closed_known", "canonical_zero_after", "accepted_post_sdk_full_recheck", "source_unopened",
        "candidate_owner_retained", "native_handle_closed")),
    RECOVER("recover", 170_000, setOf("memory_eligible", "accepted_full_recheck", "runtime_guard_passed",
        "production_transport_local", "native_worker_off_main", "initial_canonical_zero", "fixed_free_text_submitted_once",
        "prepared_after_known_worker_close", "accepted_post_sdk_full_recheck", "canonical_revision_one",
        "canonical_given_to_mira", "canonical_single_receipt", "local_profile_exact", "candidate_owner_retained",
        "native_handle_closed", "prior_cancel_proof_exact", "process_identity_changed", "source_unopened", "gateway_main_confined")),
    REOPEN("reopen", 120_000, setOf("prior_recover_proof_exact", "process_identity_changed", "source_unopened",
        "candidate_access_receipt", "accepted_full_recheck", "runtime_guard_passed", "setup_ready_after_reopen",
        "production_transport_local", "no_free_text_call", "canonical_revision_one", "canonical_gift_receipt_unchanged",
        "native_handle_closed", "memory_eligible", "gateway_main_confined"));

    val checks: Set<String> = Collections.unmodifiableSet(LinkedHashSet(checks))
}

internal data class CancellationIdentity(val pid: Int, val start: Long, val uid: Int)
internal data class CancellationCapacity(
    val userdataBefore: Long, val userdataAfter: Long,
    val externalBefore: Long, val externalAfter: Long,
    val memoryTotal: Long, val memoryBefore: Long, val memoryAfter: Long,
)

/** Necessary history consistency of two snapshots from one trace, not native-state authority. */
internal fun requireCancellationTraceHistory(sample: LiteRtWorkerSnapshot, final: LiteRtWorkerSnapshot) {
    require(final.snapshotMs >= sample.snapshotMs)
    require(sample.creations.size == 1 && sample.creations.single().returnedMs != null)
    require(final.creations.size == 1 && final.creations.single() == sample.creations.single())
    for (event in LiteRtWorkerEvent.entries) {
        require(final.counts.getValue(event) >= sample.counts.getValue(event))
        sample.lastMs.getValue(event)?.let { previous ->
            require(final.lastMs.getValue(event)?.let { it >= previous } == true)
        }
    }
}

/** Closed proof encoder only; it performs no IO, SDK operation, cancellation or status delivery. */
internal class CancellationProof(
    val phase: CancellationPhase,
    val identity: CancellationIdentity,
    val priorPid: Int,
    val priorStart: Long,
    val priorSha256: String,
    val elapsedMs: Long,
    val capacity: CancellationCapacity,
    checks: Map<String, Boolean>,
    val receiptSha256: String? = null,
    val repairs: Int? = null,
    val fallback: Boolean? = null,
    val workerTraceSha256: String? = null,
    val sampleTraceSha256: String? = null,
) {
    val checks: Map<String, Boolean> = Collections.unmodifiableMap(
        LinkedHashMap(checks.also { require(it.size == phase.checks.size) })
            .also { require(it.keys == phase.checks && it.values.all { value -> value }) },
    )

    init {
        require(identity.pid > 0 && identity.uid >= 10000 && identity.start >= 0)
        require(priorPid > 0 && priorStart >= 0 && hex(priorSha256))
        require(elapsedMs in 0..phase.budgetMs)
        if (phase != CancellationPhase.CANCEL) require(identity.pid != priorPid || identity.start != priorStart)
        require(capacity.userdataBefore >= USERDATA_FLOOR && capacity.userdataAfter >= USERDATA_FLOOR)
        require(capacity.externalBefore >= 2 * GIB && capacity.externalAfter >= 2 * GIB)
        require(capacity.memoryTotal in 7 * GIB..8 * GIB && capacity.memoryBefore in 4 * GIB..capacity.memoryTotal &&
            capacity.memoryAfter in 0..capacity.memoryTotal)
        when (phase) {
            CancellationPhase.CANCEL -> require(hex(workerTraceSha256) && hex(sampleTraceSha256) &&
                receiptSha256 == null && repairs == null && fallback == null)
            CancellationPhase.RECOVER -> require(hex(workerTraceSha256) && sampleTraceSha256 == null &&
                hex(receiptSha256) && repairs != null && repairs in 0..1 && fallback != null)
            CancellationPhase.REOPEN -> require(workerTraceSha256 == null && sampleTraceSha256 == null &&
                hex(receiptSha256) && repairs == null && fallback == null)
        }
    }

    fun json(): String {
        // Values below are fixed closed tokens, validated hashes, booleans or bounded integers.
        val values = linkedMapOf(
            "version" to "1", "phase" to quoted(phase.name), "pid" to identity.pid.toString(),
            "start" to identity.start.toString(), "uid" to identity.uid.toString(), "process" to quoted(PACKAGE),
            "model_bytes" to MODEL_BYTES.toString(), "model_sha256" to quoted(MODEL_SHA),
            "source_verify_opened" to "0", "source_verify_closed" to "0", "source_verify_bytes" to "0",
            "source_import_opened" to "0", "source_import_closed" to "0", "source_import_bytes" to "0",
            "sdk_invoked" to (phase != CancellationPhase.REOPEN).toString(), "publication_native_invoked" to "false",
            "elapsed_ms" to elapsedMs.toString(), "userdata_free_before" to capacity.userdataBefore.toString(),
            "userdata_free_after" to capacity.userdataAfter.toString(), "external_free_before" to capacity.externalBefore.toString(),
            "external_free_after" to capacity.externalAfter.toString(), "memory_total_bytes" to capacity.memoryTotal.toString(),
            "memory_available_before" to capacity.memoryBefore.toString(), "memory_available_after" to capacity.memoryAfter.toString(),
            "checks" to checks.keys.sorted().joinToString(",", "{", "}") { quoted(it) + ":true" },
            "prior_pid" to priorPid.toString(), "prior_start" to priorStart.toString(),
            priorKey(phase) to quoted(priorSha256),
            "revision" to if (phase == CancellationPhase.CANCEL) "0" else "1",
            "receipt_count" to if (phase == CancellationPhase.CANCEL) "0" else "1",
        )
        receiptSha256?.let { values["receipt_sha256"] = quoted(it) }
        repairs?.let { values["repairs"] = it.toString() }
        fallback?.let { values["fallback"] = it.toString() }
        workerTraceSha256?.let { values["worker_trace_sha256"] = quoted(it) }
        sampleTraceSha256?.let { values["sample_worker_trace_sha256"] = quoted(it) }
        val encoded = values.keys.sorted().joinToString(",", "{", "}") { quoted(it) + ":" + values.getValue(it) }
        require(encoded.all { it.code in 32..126 } && encoded.toByteArray(Charsets.US_ASCII).size <= MAX_BYTES)
        return encoded
    }

    companion object {
        const val PACKAGE = "org.locallore.app.modelvolumeverify"
        const val MODEL_BYTES = 2_588_147_712L
        const val MODEL_SHA = "181938105e0eefd105961417e8da75903eacda102c4fce9ce90f50b97139a63c"
        const val MAX_BYTES = 4096
        const val GIB = 1_073_741_824L
        const val USERDATA_FLOOR = GIB + 128 * 1024 * 1024
        fun priorKey(phase: CancellationPhase): String = when (phase) {
            CancellationPhase.CANCEL -> "prior_import_sha256"
            CancellationPhase.RECOVER -> "prior_cancel_sha256"
            CancellationPhase.REOPEN -> "prior_recover_sha256"
        }
        private fun hex(value: String?) = value != null && value.matches(Regex("[0-9a-f]{64}"))
        private fun quoted(value: String) = "\"$value\"" // Callers supply only the closed tokens above.
    }
}

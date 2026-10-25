/* Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0 */
package org.locallore.app

import java.util.Collections

private val ordinaryCommonChecks = setOf("memory_eligible", "setup_activity_exact", "setup_ready_visible", "start_enabled",
    "start_clicked_once", "setup_finished", "play_activity_exact", "play_resumed", "production_shell_viewmodel",
    "constructed_transport_observed", "production_transport_local", "source_unopened", "candidate_owner_retained", "native_handle_closed")

/** Same-observation-object history only, never an atomic SDK or resource assertion. */
internal fun requireOrdinaryTraceHistory(before: LiteRtWorkerSnapshot, after: LiteRtWorkerSnapshot) {
    require(after.snapshotMs >= before.snapshotMs)
    for (event in LiteRtWorkerEvent.entries) {
        require(after.counts.getValue(event) >= before.counts.getValue(event))
        before.lastMs.getValue(event)?.let { old -> require(after.lastMs.getValue(event)?.let { it >= old } == true) }
    }
}

internal enum class OrdinaryRoutePhase(val file: String, val budgetMs: Long, extras: Set<String>) {
    ORDINARY_START("start", 170_000, setOf("prior_import_proof_exact", "new_story_clicked_once", "canonical_zero_before",
        "local_provider_visible", "fixed_action_visible", "send_clicked_once", "gift_visible", "gift_receipt_exact",
        "local_profile_exact", "canonical_revision_one", "single_receipt", "full_model_postcheck", "owner_guard_postcheck", "worker_closed_known")),
    ORDINARY_DIALOGUE("dialogue", 170_000, setOf("prior_start_proof_exact", "process_identity_changed", "initial_gift_receipts_exact",
        "progression_visible", "history_provenance_visible", "relationships_visible", "knowledge_known_truth_visible",
        "hidden_belief_search_empty", "hidden_beacon_search_empty", "event_source_navigation_visible", "inspector_canon_unchanged",
        "ability_action_rejected", "duplicate_gift_rejected", "guards_canon_unchanged", "guards_worker_zero", "dialogue_kind_selected",
        "fixed_dialogue_visible", "dialogue_send_clicked_once", "dialogue_visible", "literal_dialogue_receipt_exact", "statement_not_truth",
        "known_truth_unchanged", "gift_receipt_preserved", "canonical_revision_two", "two_receipts", "local_profile_exact",
        "full_model_postcheck", "owner_guard_postcheck", "worker_closed_known")),
    ORDINARY_REOPEN("reopen", 120_000, setOf("prior_dialogue_proof_exact", "process_identity_changed", "two_receipts_exact",
        "retained_transcript_visible", "canonical_revision_two", "no_send_or_cancel", "worker_zero", "full_model_postcheck", "owner_guard_postcheck"));

    val checks: Set<String> = Collections.unmodifiableSet(LinkedHashSet(ordinaryCommonChecks + extras))
    val revision: Int get() = if (this == ORDINARY_START) 1 else 2
    val priorKey: String get() = when (this) {
        ORDINARY_START -> "prior_import_sha256"
        ORDINARY_DIALOGUE -> "prior_start_sha256"
        ORDINARY_REOPEN -> "prior_dialogue_sha256"
    }
}

/** Pure closed encoder. It cannot construct a runtime, perform IO or invoke user callbacks. */
internal class OrdinaryRouteProof(
    val phase: OrdinaryRoutePhase,
    val identity: CancellationIdentity,
    val priorPid: Int,
    val priorStart: Long,
    val priorSha256: String,
    val elapsedMs: Long,
    val capacity: CancellationCapacity,
    checks: Map<String, Boolean>,
    val receiptsSha256: String,
    val giftReceiptSha256: String,
    val workerTraceSha256: String,
    val dialogueReceiptSha256: String? = null,
    val repairs: Int? = null,
    val fallback: Boolean? = null,
    val guardsTraceSha256: String? = null,
) {
    val checks: Map<String, Boolean> = Collections.unmodifiableMap(
        LinkedHashMap(checks.also { require(it.size == phase.checks.size) })
            .also { require(it.keys == phase.checks && it.values.all { value -> value }) },
    )
    init {
        require(identity.pid > 0 && identity.uid >= 10000 && identity.start >= 0)
        require(priorPid > 0 && priorStart >= 0 && hex(priorSha256))
        require(elapsedMs in 0..phase.budgetMs)
        require(identity.pid != priorPid || identity.start != priorStart)
        require(capacity.userdataBefore >= CancellationProof.USERDATA_FLOOR && capacity.userdataAfter >= CancellationProof.USERDATA_FLOOR)
        require(capacity.externalBefore >= 2 * CancellationProof.GIB && capacity.externalAfter >= 2 * CancellationProof.GIB)
        require(capacity.memoryTotal in 7 * CancellationProof.GIB..8 * CancellationProof.GIB &&
            capacity.memoryBefore in 4 * CancellationProof.GIB..capacity.memoryTotal && capacity.memoryAfter in 0..capacity.memoryTotal)
        require(hex(receiptsSha256) && hex(giftReceiptSha256) && hex(workerTraceSha256))
        when (phase) {
            OrdinaryRoutePhase.ORDINARY_START -> require(dialogueReceiptSha256 == null && guardsTraceSha256 == null &&
                repairs != null && repairs in 0..1 && fallback != null)
            OrdinaryRoutePhase.ORDINARY_DIALOGUE -> require(hex(dialogueReceiptSha256) && hex(guardsTraceSha256) &&
                repairs != null && repairs in 0..1 && fallback != null)
            OrdinaryRoutePhase.ORDINARY_REOPEN -> require(hex(dialogueReceiptSha256) && guardsTraceSha256 == null && repairs == null && fallback == null)
        }
    }
    fun json(): String {
        val fields = linkedMapOf(
            "version" to "1", "phase" to quoted(phase.name), "pid" to identity.pid.toString(), "start" to identity.start.toString(),
            "uid" to identity.uid.toString(), "process" to quoted(CancellationProof.PACKAGE),
            "model_bytes" to CancellationProof.MODEL_BYTES.toString(), "model_sha256" to quoted(CancellationProof.MODEL_SHA),
            "source_verify_opened" to "0", "source_verify_closed" to "0", "source_verify_bytes" to "0",
            "source_import_opened" to "0", "source_import_closed" to "0", "source_import_bytes" to "0",
            "sdk_invoked" to (phase != OrdinaryRoutePhase.ORDINARY_REOPEN).toString(), "publication_native_invoked" to "false",
            "elapsed_ms" to elapsedMs.toString(), "userdata_free_before" to capacity.userdataBefore.toString(),
            "userdata_free_after" to capacity.userdataAfter.toString(), "external_free_before" to capacity.externalBefore.toString(),
            "external_free_after" to capacity.externalAfter.toString(), "memory_total_bytes" to capacity.memoryTotal.toString(),
            "memory_available_before" to capacity.memoryBefore.toString(), "memory_available_after" to capacity.memoryAfter.toString(),
            "checks" to checks.keys.sorted().joinToString(",", "{", "}") { quoted(it) + ":true" },
            "prior_pid" to priorPid.toString(), "prior_start" to priorStart.toString(), phase.priorKey to quoted(priorSha256),
            "revision" to phase.revision.toString(), "receipt_count" to phase.revision.toString(),
            "receipts_sha256" to quoted(receiptsSha256), "gift_receipt_sha256" to quoted(giftReceiptSha256),
            "worker_trace_sha256" to quoted(workerTraceSha256),
        )
        dialogueReceiptSha256?.let { fields["dialogue_receipt_sha256"] = quoted(it) }
        repairs?.let { fields["repairs"] = it.toString() }
        fallback?.let { fields["fallback"] = it.toString() }
        guardsTraceSha256?.let { fields["guards_worker_trace_sha256"] = quoted(it) }
        return fields.keys.sorted().joinToString(",", "{", "}") { quoted(it) + ":" + fields.getValue(it) }.also {
            require(it.all { char -> char.code in 32..126 } && it.toByteArray(Charsets.US_ASCII).size <= 4096)
        }
    }
    companion object {
        private fun hex(value: String?) = value != null && value.matches(Regex("[0-9a-f]{64}"))
        private fun quoted(value: String) = "\"$value\"" // Fixed tokens or already validated hashes only.
    }
}

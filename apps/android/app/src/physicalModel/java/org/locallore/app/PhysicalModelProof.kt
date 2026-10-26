/* Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0 */
package org.locallore.app

internal enum class PhysicalModelPhase(val file: String, val budgetMs: Long, val checks: Set<String>) {
    PRECHECK("precheck", 30_000, setOf("build_identity_exact", "phone_profile_exact", "context_roots_exact", "same_filesystem",
        "source_owner_probe_exact", "source_whitelist_exact", "source_model_absent", "legacy_roots_absent", "candidate_access_receipt",
        "candidate_roots_absent", "candidate_installed_null_noncreating", "memory_eligible", "two_copy_capacity")),
    IMPORT("import", 150_000, setOf("prior_precheck_exact", "process_identity_changed", "source_owner_probe_exact", "source_whitelist_exact",
        "source_regular_uid", "source_fullhash_exact", "source_verify_closed_once", "import_offmain_closed_once", "import_exact_bytes",
        "setup_missing_before", "setup_ready_after", "candidate_access_receipt", "preaccept_runtime_refused", "accepted_full_recheck",
        "receipt_owner_exact", "memory_eligible", "shared_capacity")),
    CANCEL("cancel", 170_000, setOf("prior_import_exact", "process_identity_changed", "accepted_recheck", "runtime_guard", "production_transport",
        "initial_canon_zero", "public_inference_sampled", "cancel_ack_joined", "terminal_drain", "known_sdk_close", "main_responsive",
        "no_prepared", "no_commit", "no_receipts", "candidate_owner_retained", "native_handle_closed", "model_intact", "memory_eligible")),
    GIFT("gift", 170_000, setOf("prior_cancel_exact", "process_identity_changed", "prior_story_exact", "initial_zero", "fixed_input_once",
        "actual_two_roles", "worker_close_verified", "canonical_revision_one", "gift_exact", "single_receipt", "zero_repair", "zero_fallback",
        "accepted_post_sdk_full_recheck", "native_handle_closed", "memory_eligible")),
    DIALOGUE("dialogue", 170_000, setOf("prior_gift_exact", "process_identity_changed", "prior_story_exact", "gift_preserved", "invalid_actions_no_sdk",
        "literal_input", "statement_not_truth", "known_truth_unchanged", "canonical_revision_two", "two_receipts", "roles_closed", "zero_repair",
        "zero_fallback", "accepted_post_sdk_full_recheck", "native_handle_closed", "memory_eligible")),
    REOPEN("reopen", 120_000, setOf("prior_dialogue_exact", "process_identity_changed", "prior_story_exact", "source_unopened", "accepted_recheck",
        "setup_ready", "no_sdk", "no_text", "canonical_revision_two", "receipts_exact", "native_handle_closed", "memory_eligible", "retained_transcript"));

    val sdk: Boolean get() = this in setOf(CANCEL, GIFT, DIALOGUE)
    val canonicalState: Boolean get() = ordinal >= CANCEL.ordinal
    val extraKeys: Set<String> get() {
        val common = if (canonicalState) setOf("revision", "receipt_count", "receipts_sha256", "story_sha256", "worker_trace_sha256") else emptySet()
        return common + when (this) {
            CANCEL -> setOf("sample_trace_sha256")
            GIFT -> setOf("repairs", "fallback", "gift_receipt_sha256")
            DIALOGUE -> setOf("repairs", "fallback", "gift_receipt_sha256", "dialogue_receipt_sha256")
            REOPEN -> setOf("gift_receipt_sha256", "dialogue_receipt_sha256")
            else -> emptySet()
        }
    }
}

internal data class PhysicalProcessIdentity(val pid: Int, val start: Long, val uid: Int) {
    init { require(pid > 0 && start > 0 && uid > 0) }
}
internal data class PhysicalPrior(val phase: PhysicalModelPhase, val identity: PhysicalProcessIdentity, val sha256: String)
internal data class PhysicalProofResources(val freeBefore: Long, val freeAfter: Long, val totalMemory: Long,
    val availableBefore: Long, val availableAfter: Long, val lowBefore: Boolean, val lowAfter: Boolean) {
    init {
        require(freeBefore >= PhysicalModelPolicy.RESERVE_BYTES && freeAfter >= PhysicalModelPolicy.RESERVE_BYTES)
        require(totalMemory in 10 * PhysicalModelPolicy.GIB..12 * PhysicalModelPolicy.GIB)
        require(availableBefore in 4 * PhysicalModelPolicy.GIB..totalMemory && availableAfter in 0..totalMemory)
        require(!lowBefore && !lowAfter)
    }
}
internal data class PhysicalSourceCounts(val verifyOpened: Long = 0, val verifyClosed: Long = 0, val verifyBytes: Long = 0,
    val importOpened: Long = 0, val importClosed: Long = 0, val importBytes: Long = 0)

/** Closed canonical metadata; never contains source text, paths, exceptions or story IDs. */
internal class PhysicalModelProof(
    val phase: PhysicalModelPhase,
    val identity: PhysicalProcessIdentity,
    val elapsedMs: Long,
    val resources: PhysicalProofResources,
    val counts: PhysicalSourceCounts,
    val prior: PhysicalPrior?,
    checks: Map<String, Boolean>,
    extras: Map<String, Any> = emptyMap(),
) {
    val checks: Map<String, Boolean> = checks.toMap()
    val extras: Map<String, Any> = extras.toMap()
    init {
        require(elapsedMs in 0..phase.budgetMs)
        require(this.checks.keys == phase.checks && this.checks.values.all { it })
        require(this.extras.keys == phase.extraKeys)
        if (phase == PhysicalModelPhase.PRECHECK) {
            require(prior == null && resources.freeBefore >= PhysicalModelPolicy.FRESH_BYTES)
        } else {
            require(prior != null && prior.phase.ordinal == phase.ordinal - 1 && hex(prior.sha256))
            require(prior.identity.uid == identity.uid &&
                (prior.identity.pid != identity.pid || prior.identity.start != identity.start))
        }
        val imported = phase == PhysicalModelPhase.IMPORT
        require(counts == if (imported) PhysicalSourceCounts(1, 1, PhysicalModelPolicy.MODEL_BYTES, 1, 1, PhysicalModelPolicy.MODEL_BYTES)
            else PhysicalSourceCounts())
        if (phase.canonicalState) {
            val revision = when (phase) { PhysicalModelPhase.CANCEL -> 0L; PhysicalModelPhase.GIFT -> 1L; else -> 2L }
            require(this.extras["revision"] == revision && this.extras["receipt_count"] == revision)
            this.extras.filterKeys { it.endsWith("_sha256") }.values.forEach { require(it is String && hex(it)) }
        }
        if (phase in setOf(PhysicalModelPhase.GIFT, PhysicalModelPhase.DIALOGUE)) {
            require(this.extras["repairs"] == 0 && this.extras["fallback"] == false)
        }
        require(json().toByteArray(Charsets.US_ASCII).size <= MAX_BYTES)
    }

    fun json(): String {
        val fields = linkedMapOf(
            "version" to "1", "scope" to quoted("physical_model_v1"), "profile" to quoted(PhysicalModelPolicy.PROFILE),
            "phase" to quoted(phase.name), "pid" to identity.pid.toString(), "start" to identity.start.toString(),
            "uid" to identity.uid.toString(), "process" to quoted(PhysicalModelPolicy.PACKAGE),
            "model_bytes" to PhysicalModelPolicy.MODEL_BYTES.toString(), "model_sha256" to quoted(PhysicalModelPolicy.MODEL_SHA256),
            "elapsed_ms" to elapsedMs.toString(), "shared_free_before" to resources.freeBefore.toString(), "shared_free_after" to resources.freeAfter.toString(),
            "memory_total_bytes" to resources.totalMemory.toString(), "memory_available_before" to resources.availableBefore.toString(),
            "memory_available_after" to resources.availableAfter.toString(), "low_memory_before" to resources.lowBefore.toString(), "low_memory_after" to resources.lowAfter.toString(),
            "source_verify_opened" to counts.verifyOpened.toString(), "source_verify_closed" to counts.verifyClosed.toString(), "source_verify_bytes" to counts.verifyBytes.toString(),
            "source_import_opened" to counts.importOpened.toString(), "source_import_closed" to counts.importClosed.toString(), "source_import_bytes" to counts.importBytes.toString(),
            "sdk_invoked" to phase.sdk.toString(), "publication_native_invoked" to "false",
            "checks" to checks.toSortedMap().entries.joinToString(",", "{", "}") { quoted(it.key) + ":true" },
        )
        prior?.let { fields["prior_pid"] = it.identity.pid.toString(); fields["prior_start"] = it.identity.start.toString(); fields["prior_proof_sha256"] = quoted(it.sha256) }
        extras.forEach { (key, value) -> fields[key] = when (value) {
            is String -> quoted(value)
            is Long -> value.toString()
            is Int -> value.toString()
            is Boolean -> value.toString()
            else -> error("Unsupported physical proof metadata")
        } }
        return fields.toSortedMap().entries.joinToString(",", "{", "}") { quoted(it.key) + ":" + it.value }
    }

    companion object {
        const val MAX_BYTES = 4096
        internal fun hex(value: String) = value.matches(Regex("[0-9a-f]{64}"))
        private fun quoted(value: String): String {
            require(value.all { it.code in 32..126 && it != '"' && it != '\\' })
            return "\"$value\""
        }
    }
}

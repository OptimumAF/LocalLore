/* Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0 */
package org.locallore.app

import org.junit.Assert.*
import org.junit.Test

class PhysicalModelProofTest {
    private val identity = PhysicalProcessIdentity(101, 202, 10234)
    private val resources = PhysicalProofResources(PhysicalModelPolicy.FRESH_BYTES, 3 * PhysicalModelPolicy.GIB,
        11 * PhysicalModelPolicy.GIB, 6 * PhysicalModelPolicy.GIB, 4 * PhysicalModelPolicy.GIB, false, false)
    private val hash = "a".repeat(64)
    private fun extras(phase: PhysicalModelPhase): Map<String, Any> = phase.extraKeys.associateWith {
        when (it) {
            "revision", "receipt_count" -> when (phase) { PhysicalModelPhase.CANCEL -> 0L; PhysicalModelPhase.GIFT -> 1L; else -> 2L }
            "repairs" -> 0
            "fallback" -> false
            else -> hash
        }
    }
    private fun prior(phase: PhysicalModelPhase) = if (phase == PhysicalModelPhase.PRECHECK) null
        else PhysicalPrior(PhysicalModelPhase.entries[phase.ordinal - 1], identity.copy(pid = 100), hash)
    private fun counts(phase: PhysicalModelPhase) = if (phase == PhysicalModelPhase.IMPORT)
        PhysicalSourceCounts(1, 1, PhysicalModelPolicy.MODEL_BYTES, 1, 1, PhysicalModelPolicy.MODEL_BYTES) else PhysicalSourceCounts()
    private fun proof(phase: PhysicalModelPhase, checks: Map<String, Boolean> = phase.checks.associateWith { true },
        extra: Map<String, Any> = extras(phase), count: PhysicalSourceCounts = counts(phase), previous: PhysicalPrior? = prior(phase)) =
        PhysicalModelProof(phase, identity, 123, resources, count, previous, checks, extra)
    private fun refuses(action: () -> Unit) {
        try { action(); fail("Expected invalid physical proof") } catch (_: IllegalArgumentException) { }
    }

    @Test fun exactFrozenPhaseNamesBudgetsAndCheckCountsAreRetained() {
        assertEquals(listOf(13, 17, 18, 15, 16, 13), PhysicalModelPhase.entries.map { it.checks.size })
        assertEquals(listOf(30_000L, 150_000L, 170_000L, 170_000L, 170_000L, 120_000L), PhysicalModelPhase.entries.map { it.budgetMs })
        for (phase in PhysicalModelPhase.entries) {
            val raw = proof(phase).json()
            assertTrue(raw.toByteArray(Charsets.US_ASCII).size <= PhysicalModelProof.MAX_BYTES)
            assertTrue(raw.contains("\"scope\":\"physical_model_v1\""))
            assertTrue(raw.contains("\"sdk_invoked\":${phase.sdk}"))
            assertFalse(raw.contains("external_free"))
        }
    }

    @Test fun missingFalseOrAdditionalChecksCannotCreditAPhase() {
        for (phase in PhysicalModelPhase.entries) {
            refuses { proof(phase, checks = phase.checks.drop(1).associateWith { true }) }
            refuses { proof(phase, checks = phase.checks.associateWith { false }) }
            refuses { proof(phase, checks = phase.checks.associateWith { true } + ("PRIVATE_PHONE_CANARY" to true)) }
        }
    }

    @Test fun sourceCountersAreExactImportOnlyAndNeverInferMissingAsZero() {
        for (phase in PhysicalModelPhase.entries) {
            if (phase == PhysicalModelPhase.IMPORT) {
                refuses { proof(phase, count = PhysicalSourceCounts()) }
                refuses { proof(phase, count = counts(phase).copy(importClosed = 0)) }
                refuses { proof(phase, count = counts(phase).copy(verifyBytes = PhysicalModelPolicy.MODEL_BYTES - 1)) }
            } else {
                refuses { proof(phase, count = PhysicalSourceCounts(verifyOpened = 1)) }
                refuses { proof(phase, count = PhysicalSourceCounts(importBytes = 1)) }
            }
        }
    }

    @Test fun exactPredecessorSameUidChangedProcessAndCanonicalHashAreRequired() {
        val phase = PhysicalModelPhase.DIALOGUE
        refuses { proof(phase, previous = null) }
        refuses { proof(phase, previous = prior(phase)!!.copy(phase = PhysicalModelPhase.IMPORT)) }
        refuses { proof(phase, previous = prior(phase)!!.copy(identity = identity)) }
        refuses { proof(phase, previous = prior(phase)!!.copy(identity = identity.copy(uid = 10235))) }
        refuses { proof(phase, previous = prior(phase)!!.copy(sha256 = "A".repeat(64))) }
        refuses { proof(PhysicalModelPhase.PRECHECK, previous = prior(phase)) }
    }

    @Test fun RevisionReceiptAndRepairClaimsCannotBeCoercedOrOverstated() {
        for (phase in PhysicalModelPhase.entries.filter { it.canonicalState }) {
            refuses { proof(phase, extra = extras(phase) + ("revision" to true)) }
            refuses { proof(phase, extra = extras(phase) + ("receipt_count" to 99L)) }
            refuses { proof(phase, extra = extras(phase) + ("story_sha256" to "PRIVATE_PHONE_CANARY")) }
            refuses { proof(phase, extra = extras(phase) + ("source_path" to "private")) }
        }
        for (phase in listOf(PhysicalModelPhase.GIFT, PhysicalModelPhase.DIALOGUE)) {
            refuses { proof(phase, extra = extras(phase) + ("repairs" to 1)) }
            refuses { proof(phase, extra = extras(phase) + ("fallback" to true)) }
        }
    }

    @Test fun MutableCallerMapsDoNotChangeAlreadyValidatedProof() {
        val phase = PhysicalModelPhase.GIFT
        val checks = phase.checks.associateWith { true }.toMutableMap()
        val extra = extras(phase).toMutableMap()
        val proof = proof(phase, checks, extra)
        val original = proof.json()
        checks.clear(); extra["revision"] = 9L
        assertEquals(original, proof.json())
    }

    @Test fun invalidResourcesIdentitiesAndElapsedTimesAreRefused() {
        refuses { PhysicalProcessIdentity(0, 202, 10234) }
        refuses { PhysicalProcessIdentity(101, 0, 10234) }
        refuses { resources.copy(freeBefore = PhysicalModelPolicy.RESERVE_BYTES - 1) }
        refuses { resources.copy(lowAfter = true) }
        refuses { resources.copy(availableAfter = resources.totalMemory + 1) }
        refuses { PhysicalModelProof(PhysicalModelPhase.PRECHECK, identity, 30_001, resources, PhysicalSourceCounts(), null,
            PhysicalModelPhase.PRECHECK.checks.associateWith { true }) }
        refuses { PhysicalModelProof(PhysicalModelPhase.PRECHECK, identity, 1, resources.copy(freeBefore = PhysicalModelPolicy.FRESH_BYTES - 1),
            PhysicalSourceCounts(), null, PhysicalModelPhase.PRECHECK.checks.associateWith { true }) }
    }
}

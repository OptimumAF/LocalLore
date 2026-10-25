/* Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0 */
package org.locallore.app

import org.junit.Assert.*
import org.junit.Test

/** Source-only closed codec tests, using original small metadata and no Android/model IO. */
class OrdinaryRouteProofTest {
    private val hash = "a".repeat(64)
    private val id = CancellationIdentity(101, 20, 10000)
    private val capacity = CancellationCapacity(CancellationProof.USERDATA_FLOOR, CancellationProof.USERDATA_FLOOR,
        2 * CancellationProof.GIB, 2 * CancellationProof.GIB, 8 * CancellationProof.GIB, 4 * CancellationProof.GIB, 0)
    private fun proof(
        phase: OrdinaryRoutePhase = OrdinaryRoutePhase.ORDINARY_START,
        identity: CancellationIdentity = id, priorPid: Int = 100, priorStart: Long = 10, prior: String = hash,
        elapsed: Long = 0, resources: CancellationCapacity = capacity, checks: Map<String, Boolean> = phase.checks.associateWith { true },
        receipts: String = hash, gift: String = hash, trace: String = hash,
        dialogue: String? = if (phase != OrdinaryRoutePhase.ORDINARY_START) hash else null,
        repairs: Int? = if (phase != OrdinaryRoutePhase.ORDINARY_REOPEN) 0 else null,
        fallback: Boolean? = if (phase != OrdinaryRoutePhase.ORDINARY_REOPEN) false else null,
        guards: String? = if (phase == OrdinaryRoutePhase.ORDINARY_DIALOGUE) hash else null,
    ) = OrdinaryRouteProof(phase, identity, priorPid, priorStart, prior, elapsed, resources, checks, receipts, gift, trace,
        dialogue, repairs, fallback, guards)
    private fun refuses(block: () -> Unit) {
        try { block(); fail("Invalid ordinary proof accepted") } catch (_: IllegalArgumentException) { }
    }
    private fun immutable(block: () -> Unit) {
        try { block(); fail("Mutable ordinary proof collection") } catch (_: UnsupportedOperationException) { }
    }
    private fun scalar(wire: String, key: String) = Regex("\"$key\":([^,}]+)").find(wire)!!.groupValues[1]

    @Test fun phasesSelectorsCheckCountsAndLinksAreClosed() {
        assertEquals(listOf("ORDINARY_START", "ORDINARY_DIALOGUE", "ORDINARY_REOPEN"), OrdinaryRoutePhase.entries.map { it.name })
        assertEquals(listOf("start", "dialogue", "reopen"), OrdinaryRoutePhase.entries.map { it.file })
        assertEquals(listOf(170000L, 170000L, 120000L), OrdinaryRoutePhase.entries.map { it.budgetMs })
        assertEquals(listOf(28, 43, 23), OrdinaryRoutePhase.entries.map { it.checks.size })
        assertEquals(94, OrdinaryRoutePhase.entries.sumOf { it.checks.size })
        assertEquals(listOf("prior_import_sha256", "prior_start_sha256", "prior_dialogue_sha256"), OrdinaryRoutePhase.entries.map { it.priorKey })
        assertEquals(listOf(1, 2, 2), OrdinaryRoutePhase.entries.map { it.revision })
    }
    @Test fun flagsAndSourceCountersCannotBeClaimedByCaller() {
        for (phase in OrdinaryRoutePhase.entries) {
            val wire = proof(phase).json()
            assertEquals("1", scalar(wire, "version"))
            assertEquals("\"${phase.name}\"", scalar(wire, "phase"))
            assertEquals((phase != OrdinaryRoutePhase.ORDINARY_REOPEN).toString(), scalar(wire, "sdk_invoked"))
            assertEquals("false", scalar(wire, "publication_native_invoked"))
            assertEquals(phase.revision.toString(), scalar(wire, "revision"))
            assertEquals(phase.revision.toString(), scalar(wire, "receipt_count"))
            for (key in listOf("source_verify_opened", "source_verify_closed", "source_verify_bytes", "source_import_opened",
                "source_import_closed", "source_import_bytes")) assertEquals("0", scalar(wire, key))
            assertEquals(CancellationProof.MODEL_BYTES.toString(), scalar(wire, "model_bytes"))
        }
    }
    @Test fun checksAreExactTrueBoundedBeforeCopyAndDefensivelyImmutable() {
        val input = OrdinaryRoutePhase.ORDINARY_START.checks.associateWith { true }.toMutableMap()
        val value = proof(checks = input); val before = value.json(); input.clear()
        assertEquals(before, value.json())
        @Suppress("UNCHECKED_CAST") val mutable = value.checks as MutableMap<String, Boolean>
        immutable { mutable.clear() }; immutable { mutable.entries.first().setValue(false) }
        @Suppress("UNCHECKED_CAST") val phaseChecks = OrdinaryRoutePhase.ORDINARY_START.checks as MutableSet<String>
        immutable { phaseChecks.add("extra") }
        refuses { proof(checks = emptyMap()) }
        refuses { proof(checks = value.checks + ("extra" to true)) }
        refuses { proof(checks = value.checks.mapValues { false }) }
        refuses { proof(OrdinaryRoutePhase.ORDINARY_DIALOGUE, checks = value.checks) }
        val tooLarge = object : Map<String, Boolean> by value.checks {
            override val size: Int get() = 1000000
            override val entries: Set<Map.Entry<String, Boolean>> get() = error("Must refuse before copy")
        }
        refuses { proof(checks = tooLarge) }
    }
    @Test fun allHashFieldsRejectPrivateStringsAndNonCanonicalHex() {
        for (bad in listOf("", "a".repeat(63), "a".repeat(65), "A".repeat(64), "g".repeat(64), "private/content://source\n")) {
            refuses { proof(prior = bad) }; refuses { proof(receipts = bad) }; refuses { proof(gift = bad) }; refuses { proof(trace = bad) }
            refuses { proof(OrdinaryRoutePhase.ORDINARY_DIALOGUE, dialogue = bad) }
            refuses { proof(OrdinaryRoutePhase.ORDINARY_DIALOGUE, guards = bad) }
        }
        assertNotNull(proof(receipts = "0123456789abcdef".repeat(4)).json())
    }
    @Test fun phaseExtrasCannotDisappearOrCrossFamilies() {
        refuses { proof(dialogue = hash) }; refuses { proof(guards = hash) }; refuses { proof(repairs = null) }; refuses { proof(fallback = null) }
        refuses { proof(repairs = -1) }; refuses { proof(repairs = 2) }
        refuses { proof(OrdinaryRoutePhase.ORDINARY_DIALOGUE, dialogue = null) }
        refuses { proof(OrdinaryRoutePhase.ORDINARY_DIALOGUE, guards = null) }
        refuses { proof(OrdinaryRoutePhase.ORDINARY_REOPEN, dialogue = null) }
        refuses { proof(OrdinaryRoutePhase.ORDINARY_REOPEN, guards = hash) }
        refuses { proof(OrdinaryRoutePhase.ORDINARY_REOPEN, repairs = 0) }
        refuses { proof(OrdinaryRoutePhase.ORDINARY_REOPEN, fallback = false) }
        assertNotNull(proof(repairs = 1, fallback = true).json())
    }
    @Test fun everyPhaseRequiresFreshIdentityPairButPermitsPidReuse() {
        for (phase in OrdinaryRoutePhase.entries) {
            refuses { proof(phase, priorPid = id.pid, priorStart = id.start) }
            assertNotNull(proof(phase, priorPid = id.pid, priorStart = id.start - 1).json())
            assertNotNull(proof(phase, priorPid = id.pid - 1, priorStart = id.start).json())
        }
    }
    @Test fun appUidPidAndMonotonicStartAreBounded() {
        for (bad in listOf(id.copy(pid = 0), id.copy(pid = -1), id.copy(uid = 9999), id.copy(start = -1))) refuses { proof(identity = bad) }
        refuses { proof(priorPid = 0) }; refuses { proof(priorStart = -1) }
        assertNotNull(proof(identity = id.copy(uid = Int.MAX_VALUE, start = Long.MAX_VALUE)).json())
    }
    @Test fun eachPhaseRetainsExactBudgetBoundary() {
        for (phase in OrdinaryRoutePhase.entries) {
            refuses { proof(phase, elapsed = -1) }; refuses { proof(phase, elapsed = phase.budgetMs + 1) }
            refuses { proof(phase, elapsed = Long.MAX_VALUE) }; assertNotNull(proof(phase, elapsed = phase.budgetMs).json())
        }
    }
    @Test fun capacityAndMemoryFloorsCannotBeLowered() {
        for (bad in listOf(capacity.copy(userdataBefore = capacity.userdataBefore - 1), capacity.copy(userdataAfter = capacity.userdataAfter - 1),
            capacity.copy(externalBefore = capacity.externalBefore - 1), capacity.copy(externalAfter = capacity.externalAfter - 1),
            capacity.copy(memoryBefore = capacity.memoryBefore - 1), capacity.copy(memoryTotal = 7 * CancellationProof.GIB - 1),
            capacity.copy(memoryTotal = 8 * CancellationProof.GIB + 1), capacity.copy(memoryAfter = -1),
            capacity.copy(memoryAfter = capacity.memoryTotal + 1))) refuses { proof(resources = bad) }
        assertNotNull(proof(resources = capacity.copy(memoryAfter = capacity.memoryTotal)).json())
    }
    @Test fun denseWireFitsAsciiCapAndDoesNotEncodeIoOrUntrustedText() {
        for (phase in OrdinaryRoutePhase.entries) {
            val value = proof(phase, identity = CancellationIdentity(Int.MAX_VALUE, Long.MAX_VALUE, Int.MAX_VALUE),
                priorPid = Int.MAX_VALUE - 1, priorStart = Long.MAX_VALUE, elapsed = phase.budgetMs,
                resources = capacity.copy(userdataBefore = Long.MAX_VALUE, userdataAfter = Long.MAX_VALUE,
                    externalBefore = Long.MAX_VALUE, externalAfter = Long.MAX_VALUE))
            val wire = value.json()
            assertEquals(wire, value.json()); assertTrue(wire.all { it.code in 32..126 }); assertTrue(wire.toByteArray(Charsets.US_ASCII).size <= 4096)
            assertFalse(wire.contains("/data/")); assertFalse(wire.contains("prompt")); assertFalse(wire.contains("Throwable"))
            assertEquals(1, Regex("\"${phase.priorKey}\":").findAll(wire).count())
        }
    }
    @Test fun encoderCannotPerformCallbacksIoOrErrorInspection() {
        for (constructor in OrdinaryRouteProof::class.java.declaredConstructors) assertFalse(constructor.parameterTypes.any {
            Throwable::class.java.isAssignableFrom(it) || it.name.startsWith("java.io.") || it.name.startsWith("kotlin.jvm.functions.")
        })
        assertEquals(0, OrdinaryRouteProof::class.java.getDeclaredMethod("json").parameterCount)
    }
    @Test fun historyRejectsEarlierTimeCountsOrObservedEventTimesWithoutInventingCausality() {
        fun snapshot(time: Int, count: Int = 1, last: Int = 5) = LiteRtWorkerSnapshot(
            LiteRtWorkerEvent.entries.associateWith { if (it == LiteRtWorkerEvent.MESSAGE_RETURNED) count else 0 }, emptySet(),
            LiteRtWorkerEvent.entries.associateWith { if (it == LiteRtWorkerEvent.MESSAGE_RETURNED && count > 0) last else null },
            time, false, 0, false, emptyList())
        val before = snapshot(10)
        requireOrdinaryTraceHistory(before, before); requireOrdinaryTraceHistory(before, snapshot(20, 2, 15))
        refuses { requireOrdinaryTraceHistory(before, snapshot(9)) }; refuses { requireOrdinaryTraceHistory(before, snapshot(20, 0)) }
        refuses { requireOrdinaryTraceHistory(before, snapshot(20, 1, 4)) }
    }
}

/* Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0 */
package org.locallore.app

import org.junit.Assert.*
import org.junit.Test

/** Pure closed encoder checks; no Android JSON parser, model, IO or runtime. */
class ComposeCancellationProofTest {
    private val hash = "a".repeat(64)
    private val identity = CancellationIdentity(101, 20, 10240)
    private val capacity = CancellationCapacity(ComposeCancellationProof.USERDATA_FLOOR, ComposeCancellationProof.USERDATA_FLOOR,
        2 * ComposeCancellationProof.GIB, 2 * ComposeCancellationProof.GIB, 8 * ComposeCancellationProof.GIB,
        4 * ComposeCancellationProof.GIB, 0)
    private fun proof(
        phase: ComposeCancellationPhase = ComposeCancellationPhase.UI_CANCEL,
        current: CancellationIdentity = identity,
        priorPid: Int = 100,
        priorStart: Long = 10,
        priorSha: String = hash,
        elapsed: Long = 0,
        resources: CancellationCapacity = capacity,
        checks: Map<String, Boolean> = phase.checks.associateWith { true },
        receipt: String? = if (phase != ComposeCancellationPhase.UI_CANCEL) hash else null,
        repairs: Int? = if (phase == ComposeCancellationPhase.UI_RECOVER) 0 else null,
        fallback: Boolean? = if (phase == ComposeCancellationPhase.UI_RECOVER) false else null,
        worker: String? = if (phase != ComposeCancellationPhase.UI_REOPEN) hash else null,
        sample: String? = if (phase == ComposeCancellationPhase.UI_CANCEL) hash else null,
    ) = ComposeCancellationProof(phase, current, priorPid, priorStart, priorSha, elapsed, resources, checks,
        receipt, repairs, fallback, worker, sample)

    private fun refuses(block: () -> Unit) {
        try { block(); fail("Invalid proof accepted") } catch (_: IllegalArgumentException) { }
    }
    private fun immutable(block: () -> Unit) {
        try { block(); fail("Mutable diagnostic collection") } catch (_: UnsupportedOperationException) { }
    }
    private fun scalar(json: String, key: String) = Regex("\"$key\":([^,}]+)").find(json)!!.groupValues[1]

    @Test fun phasesBudgetsAndCheckSetsAreClosedWithoutChangingOldWire() {
        assertEquals(listOf("UI_CANCEL", "UI_RECOVER", "UI_REOPEN"), ComposeCancellationPhase.entries.map { it.name })
        assertEquals(listOf(170_000L, 170_000L, 120_000L), ComposeCancellationPhase.entries.map { it.budgetMs })
        assertEquals(listOf(26, 24, 17), ComposeCancellationPhase.entries.map { it.checks.size })
        assertEquals(listOf("prior_import_sha256", "prior_cancel_sha256", "prior_recover_sha256"),
            ComposeCancellationPhase.entries.map { ComposeCancellationProof.priorKey(it) })
        assertEquals(listOf("cancel", "recover", "reopen"), ComposeCancellationPhase.entries.map { it.file })
        assertEquals(67, ComposeCancellationPhase.entries.sumOf { it.checks.size })
    }

    @Test fun phaseFlagsRevisionAndSourceCountersAreFixedByTheClosedPhase() {
        for (phase in ComposeCancellationPhase.entries) {
            val value = proof(phase).json()
            assertEquals("1", scalar(value, "version"))
            assertEquals("\"${phase.name}\"", scalar(value, "phase"))
            assertEquals((phase != ComposeCancellationPhase.UI_REOPEN).toString(), scalar(value, "sdk_invoked"))
            assertEquals("false", scalar(value, "publication_native_invoked"))
            assertEquals(if (phase == ComposeCancellationPhase.UI_CANCEL) "0" else "1", scalar(value, "revision"))
            assertEquals(if (phase == ComposeCancellationPhase.UI_CANCEL) "0" else "1", scalar(value, "receipt_count"))
            for (name in listOf("source_verify_opened", "source_verify_closed", "source_verify_bytes",
                "source_import_opened", "source_import_closed", "source_import_bytes")) assertEquals("0", scalar(value, name))
            assertTrue(value.contains("\"process\":\"org.locallore.app.modelvolumeverify\""))
            assertEquals(ComposeCancellationProof.MODEL_BYTES.toString(), scalar(value, "model_bytes"))
            assertTrue(value.contains(ComposeCancellationProof.MODEL_SHA))
        }
    }

    @Test fun exactChecksAreRequiredTrueCopiedAndImmutable() {
        val original = ComposeCancellationPhase.UI_CANCEL.checks.associateWith { true }.toMutableMap()
        val value = proof(checks = original)
        val before = value.json()
        original.clear()
        assertEquals(before, value.json())
        assertEquals(ComposeCancellationPhase.UI_CANCEL.checks, value.checks.keys)
        @Suppress("UNCHECKED_CAST") val checks = value.checks as MutableMap<String, Boolean>
        immutable { checks.clear() }
        immutable { checks.entries.first().setValue(false) }
        @Suppress("UNCHECKED_CAST") val phaseChecks = ComposeCancellationPhase.UI_CANCEL.checks as MutableSet<String>
        immutable { phaseChecks.add("arbitrary\"private") }
        refuses { proof(checks = emptyMap()) }
        refuses { proof(checks = ComposeCancellationPhase.UI_CANCEL.checks.associateWith { false }) }
        refuses { proof(checks = value.checks + ("arbitrary\"private" to true)) }
        refuses { proof(ComposeCancellationPhase.UI_RECOVER, checks = value.checks) }
        val oversized = object : Map<String, Boolean> by value.checks {
            override val size: Int get() = value.checks.size + 1
            override val entries: Set<Map.Entry<String, Boolean>> get() = error("Must bound before copying")
        }
        refuses { proof(checks = oversized) }
    }

    @Test fun hashesPermitOnlyExactLowercaseHexAndNeverEscapeRawPrivateStrings() {
        for (bad in listOf("", "a".repeat(63), "a".repeat(65), "A".repeat(64), "g".repeat(64),
            "secret/path\"\n" + "a".repeat(51), "a".repeat(63) + "\u0000")) {
            refuses { proof(priorSha = bad) }
            refuses { proof(worker = bad) }
            refuses { proof(sample = bad) }
            refuses { proof(ComposeCancellationPhase.UI_REOPEN, receipt = bad) }
        }
        val exact = proof(priorSha = "0123456789abcdef".repeat(4)).json()
        assertTrue(exact.contains("0123456789abcdef".repeat(4)))
        assertFalse(exact.contains("secret"))
    }

    @Test fun phaseSpecificExtrasCannotLeakIntoOtherPhasesOrDisappear() {
        refuses { proof(receipt = hash) }
        refuses { proof(repairs = 0) }
        refuses { proof(fallback = false) }
        refuses { proof(worker = null) }
        refuses { proof(sample = null) }
        refuses { proof(ComposeCancellationPhase.UI_RECOVER, sample = hash) }
        refuses { proof(ComposeCancellationPhase.UI_RECOVER, receipt = null) }
        refuses { proof(ComposeCancellationPhase.UI_RECOVER, worker = null) }
        refuses { proof(ComposeCancellationPhase.UI_RECOVER, repairs = null) }
        refuses { proof(ComposeCancellationPhase.UI_RECOVER, repairs = -1) }
        refuses { proof(ComposeCancellationPhase.UI_RECOVER, repairs = 2) }
        refuses { proof(ComposeCancellationPhase.UI_RECOVER, fallback = null) }
        refuses { proof(ComposeCancellationPhase.UI_REOPEN, worker = hash) }
        refuses { proof(ComposeCancellationPhase.UI_REOPEN, receipt = null) }
        refuses { proof(ComposeCancellationPhase.UI_REOPEN, repairs = 0) }
        assertNotNull(proof(ComposeCancellationPhase.UI_RECOVER, repairs = 1, fallback = true).json())
    }

    @Test fun freshProcessUsesIdentityPairSoPidReuseWithChangedStartIsValid() {
        for (phase in listOf(ComposeCancellationPhase.UI_RECOVER, ComposeCancellationPhase.UI_REOPEN)) {
            refuses { proof(phase, priorPid = identity.pid, priorStart = identity.start) }
            assertNotNull(proof(phase, priorPid = identity.pid, priorStart = identity.start - 1).json())
            assertNotNull(proof(phase, priorPid = identity.pid - 1, priorStart = identity.start).json())
        }
        assertNotNull(proof(priorPid = identity.pid, priorStart = identity.start).json())
    }

    @Test fun identityAndElapsedBoundariesRefuseInvalidOrOverBudgetNumbers() {
        for (bad in listOf(identity.copy(pid = 0), identity.copy(pid = -1), identity.copy(uid = 0), identity.copy(uid = 9999),
            identity.copy(start = -1))) refuses { proof(current = bad) }
        assertNotNull(proof(current = identity.copy(uid = 10000)).json())
        refuses { proof(priorPid = 0) }
        refuses { proof(priorStart = -1) }
        for (phase in ComposeCancellationPhase.entries) {
            refuses { proof(phase, elapsed = -1) }
            refuses { proof(phase, elapsed = phase.budgetMs + 1) }
            refuses { proof(phase, elapsed = Long.MAX_VALUE) }
            assertNotNull(proof(phase, elapsed = phase.budgetMs).json())
        }
    }

    @Test fun capacityMemoryFloorsAndRangesAreNotRelaxed() {
        for (bad in listOf(capacity.copy(userdataBefore = capacity.userdataBefore - 1),
            capacity.copy(userdataAfter = capacity.userdataAfter - 1), capacity.copy(externalBefore = 2 * ComposeCancellationProof.GIB - 1),
            capacity.copy(externalAfter = 2 * ComposeCancellationProof.GIB - 1), capacity.copy(memoryTotal = 7 * ComposeCancellationProof.GIB - 1),
            capacity.copy(memoryTotal = 8 * ComposeCancellationProof.GIB + 1), capacity.copy(memoryBefore = 4 * ComposeCancellationProof.GIB - 1),
            capacity.copy(memoryBefore = capacity.memoryTotal + 1), capacity.copy(memoryAfter = -1),
            capacity.copy(memoryAfter = capacity.memoryTotal + 1))) refuses { proof(resources = bad) }
        assertNotNull(proof(resources = capacity.copy(memoryAfter = capacity.memoryTotal)).json())
    }

    @Test fun denseWireIsAsciiBoundedDeterministicAndUsesOnlyClosedKeys() {
        for (phase in ComposeCancellationPhase.entries) {
            val value = proof(phase, current = CancellationIdentity(Int.MAX_VALUE, Long.MAX_VALUE, Int.MAX_VALUE),
                priorPid = Int.MAX_VALUE - 1, priorStart = Long.MAX_VALUE, elapsed = phase.budgetMs,
                resources = capacity.copy(userdataBefore = Long.MAX_VALUE, userdataAfter = Long.MAX_VALUE,
                    externalBefore = Long.MAX_VALUE, externalAfter = Long.MAX_VALUE))
            val wire = value.json()
            assertEquals(wire, value.json())
            assertTrue(wire.all { it.code in 32..126 })
            assertTrue(wire.toByteArray(Charsets.US_ASCII).size <= 4096)
            assertFalse(wire.contains("Throwable"))
            assertFalse(wire.contains("/data/"))
            assertFalse(wire.contains("prompt"))
            assertEquals(1, Regex("\"phase\":").findAll(wire).count())
            assertEquals(1, Regex("\"${ComposeCancellationProof.priorKey(phase)}\":").findAll(wire).count())
            assertEquals(phase.checks.size, Regex(":true").findAll(wire.substringAfter("\"checks\":{").substringBefore('}')).count())
        }
    }

    @Test fun encoderHasNoCallbackThrowableIoOrArbitraryExtraFieldsSurface() {
        for (type in listOf(ComposeCancellationProof::class.java, CancellationIdentity::class.java, CancellationCapacity::class.java)) {
            for (constructor in type.declaredConstructors) assertFalse(constructor.parameterTypes.any {
                Throwable::class.java.isAssignableFrom(it) || it.name.startsWith("java.io.") ||
                    it.name.startsWith("kotlin.jvm.functions.")
            })
        }
        assertEquals(0, ComposeCancellationProof::class.java.getDeclaredMethod("json").parameterCount)
    }

    @Test fun finalTraceMustExtendTheSameReturnedCreationAndEveryObservedEvent() {
        val creation = LiteRtTraceCreation(1, LiteRtTraceRole.DIRECTOR, 1, 2, null, LiteRtTraceFailure.NONE)
        fun snapshot(time: Int, messages: Int = 2, last: Int = 5,
            current: LiteRtTraceCreation = creation): LiteRtWorkerSnapshot {
            val counts = LiteRtWorkerEvent.entries.associateWith {
                if (it == LiteRtWorkerEvent.MESSAGE_RETURNED) messages else 0
            }
            val times = LiteRtWorkerEvent.entries.associateWith {
                if (it == LiteRtWorkerEvent.MESSAGE_RETURNED && messages > 0) last else null
            }
            return LiteRtWorkerSnapshot(counts, emptySet(), times, time, false, 1, false, listOf(current))
        }
        val sample = snapshot(10)
        requireCancellationTraceHistory(sample, snapshot(20, messages = 3, last = 15))
        requireCancellationTraceHistory(sample, sample)
        refuses { requireCancellationTraceHistory(sample, snapshot(9)) }
        refuses { requireCancellationTraceHistory(sample, snapshot(20, current = creation.copy(enteredMs = 0))) }
        refuses { requireCancellationTraceHistory(sample, snapshot(20, messages = 1)) }
        refuses { requireCancellationTraceHistory(sample, snapshot(20, messages = 0)) }
        refuses { requireCancellationTraceHistory(sample, snapshot(20, last = 4)) }
    }
}

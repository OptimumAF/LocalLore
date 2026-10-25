/* Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0 */
package org.locallore.app

import java.util.Collections
import java.util.EnumMap
import java.util.EnumSet

internal enum class LiteRtWorkerEvent {
    ADMISSION_ENTERED, ADMISSION_RETURNED,
    ENGINE_CREATE_ENTERED, ENGINE_CREATE_RETURNED,
    INITIALIZE_ADMISSION_ENTERED, INITIALIZE_ADMISSION_RETURNED,
    INITIALIZE_ENTERED, INITIALIZE_RETURNED,
    ROLE_ADMISSION_ENTERED, ROLE_ADMISSION_RETURNED,
    CONVERSATION_CREATE_ENTERED, CONVERSATION_CREATE_RETURNED,
    SEND_ADMISSION_ENTERED, SEND_ADMISSION_RETURNED,
    SEND_ENTERED, SEND_RETURNED,
    MESSAGE_ENTERED, MESSAGE_RETURNED,
    DONE_ENTERED, DONE_RETURNED,
    ERROR_ENTERED, ERROR_RETURNED,
    DRAIN_SETTLED,
    CANCEL_ENTERED, CANCEL_RETURNED,
    CONVERSATION_CLOSE_ENTERED, CONVERSATION_CLOSE_KNOWN,
    ENGINE_CLOSE_ENTERED, ENGINE_CLOSE_KNOWN,
    UNCERTAIN,
}

internal enum class LiteRtTraceRole { DIRECTOR, NARRATOR }
internal enum class LiteRtTraceFailure { NONE, CANCELLED, OTHER }

/** Pure arithmetic only. The trace obtains its own monotonic clock; no caller supplies one. */
internal data class LiteRtTraceTime(val ms: Int, val saturated: Boolean)
internal fun liteRtTraceTime(elapsedNanos: Long): LiteRtTraceTime {
    val cap = LiteRtWorkerTrace.MAX_MS.toLong() * 1_000_000
    return LiteRtTraceTime(
        (elapsedNanos.coerceAtLeast(0).coerceAtMost(cap) / 1_000_000).toInt(),
        elapsedNanos > cap,
    )
}

internal data class LiteRtTraceCreation(
    val ordinal: Int,
    val role: LiteRtTraceRole,
    val enteredMs: Int,
    val returnedMs: Int?,
    val failedMs: Int?,
    val failure: LiteRtTraceFailure,
)

/** Bounded observations only; these counters never grant runtime or cleanup authority. */
internal class LiteRtWorkerTrace {
    private val startedNanos = System.nanoTime()
    private val counts = IntArray(LiteRtWorkerEvent.entries.size)
    private val saturated = BooleanArray(LiteRtWorkerEvent.entries.size)
    private val lastMs = arrayOfNulls<Int>(LiteRtWorkerEvent.entries.size)
    private var timeSaturated = false
    private var creationsTotal = 0
    private var creationsSaturated = false
    private val creations = ArrayList<LiteRtTraceCreation>(MAX_CREATIONS)

    private fun elapsed(): Int {
        // nanoTime subtraction is elapsed-time arithmetic, independent of wall-clock changes.
        val value = liteRtTraceTime(System.nanoTime() - startedNanos)
        timeSaturated = timeSaturated || value.saturated
        return value.ms
    }

    @Synchronized fun record(event: LiteRtWorkerEvent) {
        val index = event.ordinal
        if (counts[index] < MAX_COUNT) counts[index]++ else saturated[index] = true
        lastMs[index] = elapsed()
    }

    /** Returns only this trace's retained ordinal, or zero when the fixed slots are exhausted. */
    @Synchronized fun creationEntered(role: LiteRtTraceRole): Int {
        if (creationsTotal < MAX_COUNT) creationsTotal++ else creationsSaturated = true
        val entered = elapsed()
        if (creations.size == MAX_CREATIONS) return 0
        val ordinal = creations.size + 1
        creations.add(LiteRtTraceCreation(ordinal, role, entered, null, null, LiteRtTraceFailure.NONE))
        return ordinal
    }

    @Synchronized fun creationReturned(ordinal: Int) {
        val previous = ownedCreation(ordinal) ?: return
        if (previous.returnedMs != null || previous.failedMs != null) return
        creations[ordinal - 1] = previous.copy(returnedMs = elapsed())
    }

    @Synchronized fun creationFailed(ordinal: Int, failure: LiteRtTraceFailure) {
        if (failure == LiteRtTraceFailure.NONE) return
        val previous = ownedCreation(ordinal) ?: return
        if (previous.returnedMs != null || previous.failedMs != null) return
        creations[ordinal - 1] = previous.copy(failedMs = elapsed(), failure = failure)
    }

    private fun ownedCreation(ordinal: Int): LiteRtTraceCreation? =
        if (ordinal in 1..creations.size) creations[ordinal - 1] else null

    @Synchronized fun snapshot(): LiteRtWorkerSnapshot {
        val snapshotMs = elapsed()
        val copiedCounts = EnumMap<LiteRtWorkerEvent, Int>(LiteRtWorkerEvent::class.java)
        val copiedSaturated = EnumSet.noneOf(LiteRtWorkerEvent::class.java)
        val copiedLast = EnumMap<LiteRtWorkerEvent, Int?>(LiteRtWorkerEvent::class.java)
        for (event in LiteRtWorkerEvent.entries) {
            copiedCounts[event] = counts[event.ordinal]
            if (saturated[event.ordinal]) copiedSaturated.add(event)
            copiedLast[event] = lastMs[event.ordinal]
        }
        return LiteRtWorkerSnapshot(copiedCounts, copiedSaturated, copiedLast, snapshotMs,
            timeSaturated, creationsTotal, creationsSaturated, creations)
    }

    companion object {
        const val STATUS_KEY = "locallore_receipt_worker_v2"
        const val STATUS_CODE = 1337
        const val WIRE_PREFIX = "INSTRUMENTATION_STATUS: $STATUS_KEY="
        const val MAX_BYTES = 4096
        const val MAX_COUNT = 1_000_000
        const val MAX_MS = 180_000
        const val MAX_CREATIONS = 3
    }
}

/** Owns immutable copies, including when constructed from caller-owned collections. */
internal class LiteRtWorkerSnapshot(
    counts: Map<LiteRtWorkerEvent, Int>,
    saturated: Set<LiteRtWorkerEvent>,
    lastMs: Map<LiteRtWorkerEvent, Int?>,
    val snapshotMs: Int,
    val timeSaturated: Boolean,
    val creationsTotal: Int,
    val creationsSaturated: Boolean,
    creations: List<LiteRtTraceCreation>,
) {
    val counts: Map<LiteRtWorkerEvent, Int> = Collections.unmodifiableMap(
        EnumMap<LiteRtWorkerEvent, Int>(LiteRtWorkerEvent::class.java).apply { putAll(counts) },
    )
    val saturated: Set<LiteRtWorkerEvent> = Collections.unmodifiableSet(
        EnumSet.noneOf(LiteRtWorkerEvent::class.java).apply { addAll(saturated) },
    )
    val lastMs: Map<LiteRtWorkerEvent, Int?> = Collections.unmodifiableMap(
        EnumMap<LiteRtWorkerEvent, Int?>(LiteRtWorkerEvent::class.java).apply { putAll(lastMs) },
    )
    val creations: List<LiteRtTraceCreation> = Collections.unmodifiableList(
        ArrayList(creations.also { require(it.size <= LiteRtWorkerTrace.MAX_CREATIONS) }),
    )

    init {
        require(this.counts.keys == LiteRtWorkerEvent.entries.toSet())
        require(this.counts.values.all { it in 0..LiteRtWorkerTrace.MAX_COUNT })
        require(this.saturated.all { this.counts[it] == LiteRtWorkerTrace.MAX_COUNT })
        require(this.lastMs.keys == LiteRtWorkerEvent.entries.toSet())
        require(snapshotMs in 0..LiteRtWorkerTrace.MAX_MS)
        require(!timeSaturated || snapshotMs == LiteRtWorkerTrace.MAX_MS)
        for (event in LiteRtWorkerEvent.entries) {
            val last = this.lastMs.getValue(event)
            require((this.counts.getValue(event) == 0) == (last == null))
            require(last == null || last in 0..snapshotMs)
        }
        require(creationsTotal in 0..LiteRtWorkerTrace.MAX_COUNT)
        require(!creationsSaturated || creationsTotal == LiteRtWorkerTrace.MAX_COUNT)
        require(this.creations.size == minOf(creationsTotal, LiteRtWorkerTrace.MAX_CREATIONS))
        for ((index, creation) in this.creations.withIndex()) {
            require(creation.ordinal == index + 1)
            require(creation.enteredMs in 0..snapshotMs)
            require(creation.returnedMs == null || creation.failedMs == null)
            require(creation.returnedMs == null || creation.returnedMs in creation.enteredMs..snapshotMs)
            require(creation.failedMs == null || creation.failedMs in creation.enteredMs..snapshotMs)
            require((creation.failedMs == null) == (creation.failure == LiteRtTraceFailure.NONE))
        }
    }

    fun json(): String {
        val value = "{\"version\":2,\"counts\":{" + LiteRtWorkerEvent.entries.joinToString(",") {
            "\"${it.name}\":${counts.getValue(it)}"
        } + "},\"saturated\":[" + LiteRtWorkerEvent.entries.filter { it in saturated }.joinToString(",") {
            "\"${it.name}\""
        } + "],\"last_ms\":{" + LiteRtWorkerEvent.entries.joinToString(",") {
            "\"${it.name}\":${lastMs.getValue(it)}"
        } + "},\"snapshot_ms\":$snapshotMs,\"time_saturated\":$timeSaturated" +
            ",\"creations_total\":$creationsTotal,\"creations_saturated\":$creationsSaturated,\"creations\":[" +
            creations.joinToString(",") {
                "{\"ordinal\":${it.ordinal},\"role\":\"${it.role.name}\",\"entered_ms\":${it.enteredMs}," +
                    "\"returned_ms\":${it.returnedMs},\"failed_ms\":${it.failedMs},\"failure\":\"${it.failure.name}\"}"
            } + "]}"
        require(value.all { it.code in 32..126 })
        require((LiteRtWorkerTrace.WIRE_PREFIX + value).toByteArray(Charsets.UTF_8).size <= LiteRtWorkerTrace.MAX_BYTES)
        return value
    }
}

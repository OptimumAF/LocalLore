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

/** Bounded observations only; these counters never grant runtime or cleanup authority. */
internal class LiteRtWorkerTrace {
    private val counts = IntArray(LiteRtWorkerEvent.entries.size)
    private val saturated = BooleanArray(LiteRtWorkerEvent.entries.size)

    @Synchronized fun record(event: LiteRtWorkerEvent) {
        val index = event.ordinal
        if (counts[index] < MAX_COUNT) counts[index]++ else saturated[index] = true
    }

    @Synchronized fun snapshot(): LiteRtWorkerSnapshot {
        val copiedCounts = EnumMap<LiteRtWorkerEvent, Int>(LiteRtWorkerEvent::class.java)
        val copiedSaturated = EnumSet.noneOf(LiteRtWorkerEvent::class.java)
        for (event in LiteRtWorkerEvent.entries) {
            copiedCounts[event] = counts[event.ordinal]
            if (saturated[event.ordinal]) copiedSaturated.add(event)
        }
        return LiteRtWorkerSnapshot(copiedCounts, copiedSaturated)
    }

    companion object {
        const val STATUS_KEY = "locallore_receipt_worker_v1"
        const val STATUS_CODE = 1337
        const val WIRE_PREFIX = "INSTRUMENTATION_STATUS: $STATUS_KEY="
        const val MAX_BYTES = 4096
        const val MAX_COUNT = 1_000_000
    }
}

/** Owns immutable copies, including when constructed from caller-owned collections. */
internal class LiteRtWorkerSnapshot(
    counts: Map<LiteRtWorkerEvent, Int>,
    saturated: Set<LiteRtWorkerEvent>,
) {
    val counts: Map<LiteRtWorkerEvent, Int> = Collections.unmodifiableMap(
        EnumMap<LiteRtWorkerEvent, Int>(LiteRtWorkerEvent::class.java).apply { putAll(counts) },
    )
    val saturated: Set<LiteRtWorkerEvent> = Collections.unmodifiableSet(
        EnumSet.noneOf(LiteRtWorkerEvent::class.java).apply { addAll(saturated) },
    )

    init {
        require(this.counts.keys == LiteRtWorkerEvent.entries.toSet())
        require(this.counts.values.all { it in 0..LiteRtWorkerTrace.MAX_COUNT })
        require(this.saturated.all { this.counts[it] == LiteRtWorkerTrace.MAX_COUNT })
    }

    fun json(): String {
        val value = "{\"version\":1,\"counts\":{" + LiteRtWorkerEvent.entries.joinToString(",") {
            "\"${it.name}\":${counts.getValue(it)}"
        } + "},\"saturated\":[" + LiteRtWorkerEvent.entries.filter { it in saturated }.joinToString(",") {
            "\"${it.name}\""
        } + "]}"
        require(value.all { it.code in 32..126 })
        require((LiteRtWorkerTrace.WIRE_PREFIX + value).toByteArray(Charsets.UTF_8).size <= LiteRtWorkerTrace.MAX_BYTES)
        return value
    }
}

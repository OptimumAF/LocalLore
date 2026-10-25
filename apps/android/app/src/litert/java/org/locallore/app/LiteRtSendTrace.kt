/* Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0 */
package org.locallore.app

import java.util.Collections
import java.util.EnumMap
import java.util.EnumSet

internal enum class LiteRtSendEvent {
    ARGUMENTS_ENTERED, ARGUMENTS_RETURNED, ARGUMENTS_THROWN,
    ASYNC_CALL_ENTERED, ASYNC_CALL_RETURNED, ASYNC_CALL_THROWN,
}

internal fun interface LiteRtSendObserver { fun record(event: LiteRtSendEvent) }

internal data class LiteRtSendTime(val ms: Int, val saturated: Boolean)
internal fun liteRtSendTime(elapsedNanos: Long): LiteRtSendTime {
    val cap = LiteRtSendTrace.MAX_MS.toLong() * 1_000_000
    return LiteRtSendTime((elapsedNanos.coerceAtLeast(0).coerceAtMost(cap) / 1_000_000).toInt(), elapsedNanos > cap)
}

/** Fixed memory and private monotonic observations only; never runtime/resource authority. */
internal class LiteRtSendTrace : LiteRtSendObserver {
    private val startedNanos = System.nanoTime()
    private val counts = IntArray(LiteRtSendEvent.entries.size)
    private val saturated = BooleanArray(LiteRtSendEvent.entries.size)
    private val lastMs = arrayOfNulls<Int>(LiteRtSendEvent.entries.size)
    private var timeSaturated = false
    private fun elapsed(): Int {
        val elapsed = liteRtSendTime(System.nanoTime() - startedNanos)
        timeSaturated = timeSaturated || elapsed.saturated
        return elapsed.ms
    }
    @Synchronized override fun record(event: LiteRtSendEvent) {
        if (counts[event.ordinal] < MAX_COUNT) counts[event.ordinal]++ else saturated[event.ordinal] = true
        lastMs[event.ordinal] = elapsed()
    }
    @Synchronized fun snapshot(): LiteRtSendSnapshot {
        val time = elapsed()
        val copiedCounts = EnumMap<LiteRtSendEvent, Int>(LiteRtSendEvent::class.java)
        val copiedSaturated = EnumSet.noneOf(LiteRtSendEvent::class.java)
        val copiedLast = EnumMap<LiteRtSendEvent, Int?>(LiteRtSendEvent::class.java)
        for (event in LiteRtSendEvent.entries) {
            copiedCounts[event] = counts[event.ordinal]
            if (saturated[event.ordinal]) copiedSaturated.add(event)
            copiedLast[event] = lastMs[event.ordinal]
        }
        return LiteRtSendSnapshot(copiedCounts, copiedSaturated, copiedLast, time, timeSaturated)
    }
    companion object {
        const val STATUS_KEY = "locallore_receipt_send_v1"
        const val STATUS_CODE = 1338
        const val WIRE_PREFIX = "INSTRUMENTATION_STATUS: $STATUS_KEY="
        const val MAX_BYTES = 2048
        const val MAX_COUNT = 1_000_000
        const val MAX_MS = 180_000
    }
}

/** Copies caller collections, including when a test manually constructs a bounded snapshot. */
internal class LiteRtSendSnapshot(
    counts: Map<LiteRtSendEvent, Int>,
    saturated: Set<LiteRtSendEvent>,
    lastMs: Map<LiteRtSendEvent, Int?>,
    val snapshotMs: Int,
    val timeSaturated: Boolean,
) {
    val counts: Map<LiteRtSendEvent, Int> = Collections.unmodifiableMap(
        EnumMap<LiteRtSendEvent, Int>(LiteRtSendEvent::class.java).apply {
            require(counts.size == LiteRtSendEvent.entries.size); putAll(counts)
        },
    )
    val saturated: Set<LiteRtSendEvent> = Collections.unmodifiableSet(
        EnumSet.noneOf(LiteRtSendEvent::class.java).apply { require(saturated.size <= LiteRtSendEvent.entries.size); addAll(saturated) },
    )
    val lastMs: Map<LiteRtSendEvent, Int?> = Collections.unmodifiableMap(
        EnumMap<LiteRtSendEvent, Int?>(LiteRtSendEvent::class.java).apply {
            require(lastMs.size == LiteRtSendEvent.entries.size); putAll(lastMs)
        },
    )
    init {
        require(this.counts.keys == LiteRtSendEvent.entries.toSet() && this.lastMs.keys == LiteRtSendEvent.entries.toSet())
        require(this.counts.values.all { it in 0..LiteRtSendTrace.MAX_COUNT })
        require(this.saturated.all { this.counts.getValue(it) == LiteRtSendTrace.MAX_COUNT })
        require(snapshotMs in 0..LiteRtSendTrace.MAX_MS && (!timeSaturated || snapshotMs == LiteRtSendTrace.MAX_MS))
        for (event in LiteRtSendEvent.entries) {
            val last = this.lastMs.getValue(event)
            require((this.counts.getValue(event) == 0) == (last == null))
            require(last == null || last in 0..snapshotMs)
        }
    }
    fun json(): String {
        val value = "{\"version\":1,\"counts\":{" + LiteRtSendEvent.entries.joinToString(",") {
            "\"${it.name}\":${counts.getValue(it)}"
        } + "},\"saturated\":[" + LiteRtSendEvent.entries.filter { it in saturated }.joinToString(",") {
            "\"${it.name}\""
        } + "],\"last_ms\":{" + LiteRtSendEvent.entries.joinToString(",") {
            "\"${it.name}\":${lastMs.getValue(it)}"
        } + "},\"snapshot_ms\":$snapshotMs,\"time_saturated\":$timeSaturated}"
        require(value.all { it.code in 32..126 } && (LiteRtSendTrace.WIRE_PREFIX + value).toByteArray(Charsets.US_ASCII).size <= LiteRtSendTrace.MAX_BYTES)
        return value
    }
}

private fun sendObservation(observer: LiteRtSendObserver?, event: LiteRtSendEvent) {
    try { observer?.record(event) } catch (_: Throwable) { /* Diagnostics never alter the observed call. */ }
}

/** Records Kotlin argument/call boundaries, not async completion or hidden native entry. */
internal fun <T> observedLiteRtSend(observer: LiteRtSendObserver?, prepare: () -> T, dispatch: (T) -> Unit) {
    sendObservation(observer, LiteRtSendEvent.ARGUMENTS_ENTERED)
    val arguments = try { prepare() } catch (original: Throwable) {
        sendObservation(observer, LiteRtSendEvent.ARGUMENTS_THROWN)
        throw original
    }
    sendObservation(observer, LiteRtSendEvent.ARGUMENTS_RETURNED)
    sendObservation(observer, LiteRtSendEvent.ASYNC_CALL_ENTERED)
    try { dispatch(arguments) } catch (original: Throwable) {
        sendObservation(observer, LiteRtSendEvent.ASYNC_CALL_THROWN)
        throw original
    }
    sendObservation(observer, LiteRtSendEvent.ASYNC_CALL_RETURNED)
}

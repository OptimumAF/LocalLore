/* Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0 */
package org.locallore.app

import java.util.Collections
import java.util.EnumMap
import java.util.EnumSet

internal enum class LiteRtSendEvent {
    ARGUMENTS_ENTERED, ARGUMENTS_RETURNED, ARGUMENTS_THROWN,
    ASYNC_CALL_ENTERED, ASYNC_CALL_RETURNED, ASYNC_CALL_THROWN,
}

internal enum class LiteRtSendFormat { REGEX, JSON_OBJECT, OTHER }

internal fun interface LiteRtSendObserver {
    fun record(event: LiteRtSendEvent)
    fun format(value: LiteRtSendFormat) { }
}

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
    private val formatCounts = IntArray(LiteRtSendFormat.entries.size)
    private val formatSaturated = BooleanArray(LiteRtSendFormat.entries.size)
    private var lastFormat: LiteRtSendFormat? = null
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
    @Synchronized override fun format(value: LiteRtSendFormat) {
        if (formatCounts[value.ordinal] < MAX_COUNT) formatCounts[value.ordinal]++ else formatSaturated[value.ordinal] = true
        lastFormat = value
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
        val copiedFormats = EnumMap<LiteRtSendFormat, Int>(LiteRtSendFormat::class.java)
        val copiedFormatSaturated = EnumSet.noneOf(LiteRtSendFormat::class.java)
        for (format in LiteRtSendFormat.entries) {
            copiedFormats[format] = formatCounts[format.ordinal]
            if (formatSaturated[format.ordinal]) copiedFormatSaturated.add(format)
        }
        return LiteRtSendSnapshot(copiedCounts, copiedSaturated, copiedLast, time, timeSaturated,
            copiedFormats, copiedFormatSaturated, lastFormat)
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
    formatCounts: Map<LiteRtSendFormat, Int> = LiteRtSendFormat.entries.associateWith { 0 },
    formatSaturated: Set<LiteRtSendFormat> = emptySet(),
    val lastFormat: LiteRtSendFormat? = null,
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
    val formatCounts: Map<LiteRtSendFormat, Int> = Collections.unmodifiableMap(
        EnumMap<LiteRtSendFormat, Int>(LiteRtSendFormat::class.java).apply {
            require(formatCounts.size == LiteRtSendFormat.entries.size); putAll(formatCounts)
        },
    )
    val formatSaturated: Set<LiteRtSendFormat> = Collections.unmodifiableSet(
        EnumSet.noneOf(LiteRtSendFormat::class.java).apply {
            require(formatSaturated.size <= LiteRtSendFormat.entries.size); addAll(formatSaturated)
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
        require(this.formatCounts.keys == LiteRtSendFormat.entries.toSet())
        require(this.formatCounts.values.all { it in 0..LiteRtSendTrace.MAX_COUNT })
        require(this.formatSaturated.all { this.formatCounts.getValue(it) == LiteRtSendTrace.MAX_COUNT })
        require((lastFormat == null) == this.formatCounts.values.all { it == 0 })
        require(lastFormat == null || this.formatCounts.getValue(lastFormat) > 0)
    }
    fun json(): String {
        val value = "{\"version\":2,\"counts\":{" + LiteRtSendEvent.entries.joinToString(",") {
            "\"${it.name}\":${counts.getValue(it)}"
        } + "},\"saturated\":[" + LiteRtSendEvent.entries.filter { it in saturated }.joinToString(",") {
            "\"${it.name}\""
        } + "],\"last_ms\":{" + LiteRtSendEvent.entries.joinToString(",") {
            "\"${it.name}\":${lastMs.getValue(it)}"
        } + "},\"snapshot_ms\":$snapshotMs,\"time_saturated\":$timeSaturated,\"format_counts\":{" +
            LiteRtSendFormat.entries.joinToString(",") { "\"${it.name}\":${formatCounts.getValue(it)}" } +
            "},\"format_saturated\":[" + LiteRtSendFormat.entries.filter { it in formatSaturated }.joinToString(",") {
                "\"${it.name}\""
            } + "],\"last_format\":" + (lastFormat?.let { "\"${it.name}\"" } ?: "null") + "}"
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

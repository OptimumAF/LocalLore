/* Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0 */
package org.locallore.app

import java.util.Collections
import java.util.EnumMap
import java.util.EnumSet

internal enum class LiteRtCallbackRole { DIRECTOR, NARRATOR }
internal enum class LiteRtCallbackCounter { OUTPUT_CHUNKS, OUTPUT_BYTES, DONE, CANCELLED, SDK_JNI, OTHER }
internal enum class LiteRtCallbackError { CANCELLED, SDK_JNI, OTHER }

private fun callbackMetadata(context: Int, output: Int, prompt: Int, schema: Int) {
    require(context in 512..4096 && output in 1..350 && prompt in 0..32768 && schema in 2..32768 &&
        prompt.toLong() + schema <= 32768) { "Invalid callback metadata" }
}

/** Bounded observations only, with one parent monitor for admission, handles and snapshots. */
internal class LiteRtCallbackTrace {
    private class Slot(val ordinal: Int, val role: LiteRtCallbackRole, val context: Int, val output: Int,
        val prompt: Int, val schema: Int, val handle: LiteRtCallbackCall) {
        val counts = IntArray(LiteRtCallbackCounter.entries.size)
        val saturated = BooleanArray(LiteRtCallbackCounter.entries.size)
    }
    private val slots = ArrayList<Slot>(MAX_CALLS)
    private var requests = 0
    private var requestsSaturated = false

    @Synchronized fun begin(role: LiteRtCallbackRole, contextTokens: Int, maxOutputTokens: Int,
        promptBytes: Int, schemaBytes: Int): LiteRtCallbackCall? {
        callbackMetadata(contextTokens, maxOutputTokens, promptBytes, schemaBytes)
        if (requests < MAX_COUNT) requests++ else requestsSaturated = true
        if (slots.size == MAX_CALLS) return null
        return LiteRtCallbackCall(this).also {
            slots.add(Slot(slots.size + 1, role, contextTokens, maxOutputTokens, promptBytes, schemaBytes, it))
        }
    }
    private fun add(slot: Slot, counter: LiteRtCallbackCounter, amount: Int) {
        val value = slot.counts[counter.ordinal].toLong() + amount
        if (value > MAX_COUNT) slot.saturated[counter.ordinal] = true
        slot.counts[counter.ordinal] = value.coerceAtMost(MAX_COUNT.toLong()).toInt()
    }
    @Synchronized internal fun output(call: LiteRtCallbackCall, bytes: Int) {
        require(bytes in 0..16384) { "Invalid accepted chunk size" }
        val slot = slots.firstOrNull { it.handle === call } ?: return
        add(slot, LiteRtCallbackCounter.OUTPUT_CHUNKS, 1)
        add(slot, LiteRtCallbackCounter.OUTPUT_BYTES, bytes)
    }
    @Synchronized internal fun terminal(call: LiteRtCallbackCall, counter: LiteRtCallbackCounter) {
        require(counter != LiteRtCallbackCounter.OUTPUT_CHUNKS && counter != LiteRtCallbackCounter.OUTPUT_BYTES)
        val slot = slots.firstOrNull { it.handle === call } ?: return
        add(slot, counter, 1)
    }
    @Synchronized fun snapshot(): LiteRtCallbackSnapshot = LiteRtCallbackSnapshot(requests, requestsSaturated, slots.map { slot ->
        val counts = EnumMap<LiteRtCallbackCounter, Int>(LiteRtCallbackCounter::class.java)
        val saturated = EnumSet.noneOf(LiteRtCallbackCounter::class.java)
        for (counter in LiteRtCallbackCounter.entries) {
            counts[counter] = slot.counts[counter.ordinal]
            if (slot.saturated[counter.ordinal]) saturated.add(counter)
        }
        LiteRtCallbackCallSnapshot(slot.ordinal, slot.role, slot.context, slot.output, slot.prompt, slot.schema, counts, saturated)
    })

    companion object {
        const val MAX_CALLS = 3
        const val MAX_COUNT = 1_000_000
        const val MAX_BYTES = 4096
        const val STATUS_KEY = "locallore_receipt_callback_v1"
        const val STATUS_CODE = 1339
        const val WIRE_PREFIX = "INSTRUMENTATION_STATUS: $STATUS_KEY="
    }
}

/** Only the handle retained by begin mutates its slot; no identity/ownership authority is implied. */
internal class LiteRtCallbackCall internal constructor(private val parent: LiteRtCallbackTrace) {
    fun output(bytes: Int) = parent.output(this, bytes)
    fun done() = parent.terminal(this, LiteRtCallbackCounter.DONE)
    fun error(category: LiteRtCallbackError) = parent.terminal(this, when (category) {
        LiteRtCallbackError.CANCELLED -> LiteRtCallbackCounter.CANCELLED
        LiteRtCallbackError.SDK_JNI -> LiteRtCallbackCounter.SDK_JNI
        LiteRtCallbackError.OTHER -> LiteRtCallbackCounter.OTHER
    })
}

internal class LiteRtCallbackCallSnapshot(
    val ordinal: Int, val role: LiteRtCallbackRole, val contextTokens: Int, val maxOutputTokens: Int,
    val promptBytes: Int, val schemaBytes: Int, counts: Map<LiteRtCallbackCounter, Int>, saturated: Set<LiteRtCallbackCounter>,
) {
    val counts: Map<LiteRtCallbackCounter, Int> = Collections.unmodifiableMap(
        EnumMap<LiteRtCallbackCounter, Int>(LiteRtCallbackCounter::class.java).apply {
            require(counts.size == LiteRtCallbackCounter.entries.size); putAll(counts)
        },
    )
    val saturated: Set<LiteRtCallbackCounter> = Collections.unmodifiableSet(
        EnumSet.noneOf(LiteRtCallbackCounter::class.java).apply { require(saturated.size <= LiteRtCallbackCounter.entries.size); addAll(saturated) },
    )
    init {
        require(ordinal in 1..LiteRtCallbackTrace.MAX_CALLS)
        callbackMetadata(contextTokens, maxOutputTokens, promptBytes, schemaBytes)
        require(this.counts.keys == LiteRtCallbackCounter.entries.toSet() && this.counts.values.all { it in 0..LiteRtCallbackTrace.MAX_COUNT })
        require(this.saturated.all { this.counts.getValue(it) == LiteRtCallbackTrace.MAX_COUNT })
    }
}

internal class LiteRtCallbackSnapshot(val requests: Int, val requestsSaturated: Boolean, calls: List<LiteRtCallbackCallSnapshot>) {
    val calls: List<LiteRtCallbackCallSnapshot> = Collections.unmodifiableList(ArrayList(calls.also { require(it.size <= LiteRtCallbackTrace.MAX_CALLS) }))
    init {
        require(requests in 0..LiteRtCallbackTrace.MAX_COUNT && (!requestsSaturated || requests == LiteRtCallbackTrace.MAX_COUNT))
        require(this.calls.size == minOf(requests, LiteRtCallbackTrace.MAX_CALLS))
        require(this.calls.withIndex().all { (index, call) -> call.ordinal == index + 1 })
    }
    fun json(): String {
        val value = "{\"version\":1,\"requests\":$requests,\"requests_saturated\":$requestsSaturated,\"calls\":[" + calls.joinToString(",") { call ->
            "{\"ordinal\":${call.ordinal},\"role\":\"${call.role.name}\",\"context_tokens\":${call.contextTokens}," +
                "\"max_output_tokens\":${call.maxOutputTokens},\"prompt_bytes\":${call.promptBytes},\"schema_bytes\":${call.schemaBytes},\"counts\":{" +
                LiteRtCallbackCounter.entries.joinToString(",") { "\"${it.name}\":${call.counts.getValue(it)}" } + "},\"saturated\":[" +
                LiteRtCallbackCounter.entries.filter { it in call.saturated }.joinToString(",") { "\"${it.name}\"" } + "]}"
        } + "]}"
        require(value.all { it.code in 32..126 } && (LiteRtCallbackTrace.WIRE_PREFIX + value).toByteArray(Charsets.US_ASCII).size <= LiteRtCallbackTrace.MAX_BYTES)
        return value
    }
}

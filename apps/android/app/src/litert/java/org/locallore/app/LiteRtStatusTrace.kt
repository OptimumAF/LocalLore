/* Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0 */
package org.locallore.app

import com.google.ai.edge.litertlm.LiteRtLmJniException
import java.util.Collections
import java.util.EnumMap
import java.util.EnumSet

internal enum class LiteRtDeclaredStatus {
    CODE_0, CODE_1, CODE_2, CODE_3, CODE_4, CODE_5, CODE_6, CODE_7, CODE_8,
    CODE_9, CODE_10, CODE_11, CODE_12, CODE_13, CODE_14, CODE_15, CODE_16, UNRECOGNIZED,
}

/** Only the pinned FINAL SDK wrapper is eligible for this explicitly bounded prefix bridge. */
internal fun liteRtDeclaredStatus(failure: Throwable): LiteRtDeclaredStatus {
    if (failure !is LiteRtLmJniException) return LiteRtDeclaredStatus.UNRECOGNIZED
    val message = failure.message ?: return LiteRtDeclaredStatus.UNRECOGNIZED // One existing reference, no copy/payload scan.
    return when {
        message.startsWith("Status Code: 0. Message: ") -> LiteRtDeclaredStatus.CODE_0
        message.startsWith("Status Code: 1. Message: ") -> LiteRtDeclaredStatus.CODE_1
        message.startsWith("Status Code: 2. Message: ") -> LiteRtDeclaredStatus.CODE_2
        message.startsWith("Status Code: 3. Message: ") -> LiteRtDeclaredStatus.CODE_3
        message.startsWith("Status Code: 4. Message: ") -> LiteRtDeclaredStatus.CODE_4
        message.startsWith("Status Code: 5. Message: ") -> LiteRtDeclaredStatus.CODE_5
        message.startsWith("Status Code: 6. Message: ") -> LiteRtDeclaredStatus.CODE_6
        message.startsWith("Status Code: 7. Message: ") -> LiteRtDeclaredStatus.CODE_7
        message.startsWith("Status Code: 8. Message: ") -> LiteRtDeclaredStatus.CODE_8
        message.startsWith("Status Code: 9. Message: ") -> LiteRtDeclaredStatus.CODE_9
        message.startsWith("Status Code: 10. Message: ") -> LiteRtDeclaredStatus.CODE_10
        message.startsWith("Status Code: 11. Message: ") -> LiteRtDeclaredStatus.CODE_11
        message.startsWith("Status Code: 12. Message: ") -> LiteRtDeclaredStatus.CODE_12
        message.startsWith("Status Code: 13. Message: ") -> LiteRtDeclaredStatus.CODE_13
        message.startsWith("Status Code: 14. Message: ") -> LiteRtDeclaredStatus.CODE_14
        message.startsWith("Status Code: 15. Message: ") -> LiteRtDeclaredStatus.CODE_15
        message.startsWith("Status Code: 16. Message: ") -> LiteRtDeclaredStatus.CODE_16
        else -> LiteRtDeclaredStatus.UNRECOGNIZED
    }
}

/** Fixed metadata only, without clocks, request identity or lifecycle authority. */
internal class LiteRtStatusTrace {
    private val counts = IntArray(LiteRtDeclaredStatus.entries.size)
    private val saturated = BooleanArray(LiteRtDeclaredStatus.entries.size)
    @Synchronized fun record(status: LiteRtDeclaredStatus) {
        val index = status.ordinal
        if (counts[index] < MAX_COUNT) counts[index]++ else saturated[index] = true
    }
    @Synchronized fun snapshot(): LiteRtStatusSnapshot {
        val copiedCounts = EnumMap<LiteRtDeclaredStatus, Int>(LiteRtDeclaredStatus::class.java)
        val copiedSaturated = EnumSet.noneOf(LiteRtDeclaredStatus::class.java)
        for (status in LiteRtDeclaredStatus.entries) {
            copiedCounts[status] = counts[status.ordinal]
            if (saturated[status.ordinal]) copiedSaturated.add(status)
        }
        return LiteRtStatusSnapshot(copiedCounts, copiedSaturated)
    }
    companion object {
        const val MAX_COUNT = 1_000_000
        const val MAX_BYTES = 2048
        const val STATUS_KEY = "locallore_receipt_status_v1"
        const val STATUS_CODE = 1340
        const val WIRE_PREFIX = "INSTRUMENTATION_STATUS: $STATUS_KEY="
    }
}

internal class LiteRtStatusSnapshot(counts: Map<LiteRtDeclaredStatus, Int>, saturated: Set<LiteRtDeclaredStatus>) {
    val counts: Map<LiteRtDeclaredStatus, Int> = Collections.unmodifiableMap(
        EnumMap<LiteRtDeclaredStatus, Int>(LiteRtDeclaredStatus::class.java).apply {
            require(counts.size == LiteRtDeclaredStatus.entries.size); putAll(counts)
        },
    )
    val saturated: Set<LiteRtDeclaredStatus> = Collections.unmodifiableSet(
        EnumSet.noneOf(LiteRtDeclaredStatus::class.java).apply { require(saturated.size <= LiteRtDeclaredStatus.entries.size); addAll(saturated) },
    )
    init {
        require(this.counts.keys == LiteRtDeclaredStatus.entries.toSet() && this.counts.values.all { it in 0..LiteRtStatusTrace.MAX_COUNT })
        require(this.saturated.all { this.counts.getValue(it) == LiteRtStatusTrace.MAX_COUNT })
    }
    fun json(): String {
        val value = "{\"version\":1,\"counts\":{" + LiteRtDeclaredStatus.entries.joinToString(",") {
            "\"${it.name}\":${counts.getValue(it)}"
        } + "},\"saturated\":[" + LiteRtDeclaredStatus.entries.filter { it in saturated }.joinToString(",") { "\"${it.name}\"" } + "]}"
        require(value.all { it.code in 32..126 } && (LiteRtStatusTrace.WIRE_PREFIX + value).toByteArray(Charsets.US_ASCII).size <= LiteRtStatusTrace.MAX_BYTES)
        return value
    }
}

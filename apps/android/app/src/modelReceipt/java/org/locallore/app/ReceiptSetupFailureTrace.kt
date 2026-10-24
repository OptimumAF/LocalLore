/* Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0 */
package org.locallore.app

import java.util.concurrent.CancellationException

internal enum class ReceiptSetupFailureCase { ACCEPT, CANCEL_BEFORE, CANCEL_AFTER, DRAIN }
internal enum class ReceiptSetupFailureEvent {
    CREATE, START, RESUME, PAUSE, STOP, DESTROY,
    CHECK_START, CHECK_PRESENT, CHECK_MISSING, CHECK_CANCELLED, CHECK_FAILED,
    IMPORT_START, IMPORT_RETURNED, IMPORT_CANCELLED, IMPORT_FAILED,
}
internal enum class ReceiptSetupFailureCode { NONE, CANCELLED, BUSY, NO_SPACE, INVALID_MODEL, UNSAFE_PATH, STORAGE, OTHER }

/** Independent observations, not a jointly atomic source/resource state. */
internal data class ReceiptSetupSourceProgress(
    val opened: Int = 0,
    val closed: Int = 0,
    val active: Int = 0,
    val readCalls: Int = 0,
    val bytesRead: Int = 0,
    val readsSaturated: Boolean = false,
    val bytesSaturated: Boolean = false,
) {
    init {
        require(listOf(opened, closed, active, readCalls, bytesRead).all { it in 0..ReceiptSetupFailureTrace.MAX_PROGRESS })
        require(!readsSaturated || readCalls == ReceiptSetupFailureTrace.MAX_PROGRESS)
        require(!bytesSaturated || bytesRead == ReceiptSetupFailureTrace.MAX_PROGRESS)
    }
}

/** Debug fixture only: no file access, provider strings, gameplay or runtime authority. */
internal class ReceiptSetupFailureTrace(private val case: ReceiptSetupFailureCase) {
    private val events = ArrayList<ReceiptSetupFailureEvent>()
    private var total = 0
    private var saturated = false
    private var error = ReceiptSetupFailureCode.NONE

    @Synchronized fun record(event: ReceiptSetupFailureEvent) {
        if (total < MAX_PROGRESS) total++ else saturated = true
        if (events.size == EVENT_LIMIT) events.removeAt(0)
        events.add(event)
    }

    @Synchronized fun error(failure: Throwable) {
        // Inspect only trusted type/category. Never read message, cause, stack or toString.
        error = when (failure) {
            is CancellationException -> ReceiptSetupFailureCode.CANCELLED
            is LocalModelException -> when (failure.failure) {
                LocalModelFailure.BUSY -> ReceiptSetupFailureCode.BUSY
                LocalModelFailure.NO_SPACE -> ReceiptSetupFailureCode.NO_SPACE
                LocalModelFailure.INVALID_MODEL -> ReceiptSetupFailureCode.INVALID_MODEL
                LocalModelFailure.UNSAFE_PATH -> ReceiptSetupFailureCode.UNSAFE_PATH
                LocalModelFailure.STORAGE -> ReceiptSetupFailureCode.STORAGE
            }
            else -> ReceiptSetupFailureCode.OTHER
        }
    }

    @Synchronized fun snapshot(
        expected: LocalModelSetupPhase,
        actual: LocalModelSetupPhase,
        source: ReceiptSetupSourceProgress,
    ): ReceiptSetupFailureSnapshot = ReceiptSetupFailureSnapshot(
        case, expected, actual, error, total, saturated, events.toList(), source,
    )

    companion object {
        const val STATUS_KEY = "locallore_receipt_failure_v1"
        const val STATUS_CODE = 1337
        const val WIRE_PREFIX = "INSTRUMENTATION_STATUS: $STATUS_KEY="
        const val MAX_BYTES = 2048 // Prefix + JSON UTF-8, excluding the line terminator.
        const val EVENT_LIMIT = 16
        const val MAX_PROGRESS = 1_000_000
    }
}

internal class ReceiptSetupFailureSnapshot(
    val case: ReceiptSetupFailureCase,
    val expected: LocalModelSetupPhase,
    val actual: LocalModelSetupPhase,
    val error: ReceiptSetupFailureCode,
    val eventsTotal: Int,
    val eventsSaturated: Boolean,
    events: List<ReceiptSetupFailureEvent>,
    val source: ReceiptSetupSourceProgress,
) {
    // Copy at most sixteen entries, never retaining caller-owned mutable storage.
    private val recorded = ArrayList<ReceiptSetupFailureEvent>().also { copy ->
        val iterator = events.iterator()
        while (iterator.hasNext()) {
            require(copy.size < ReceiptSetupFailureTrace.EVENT_LIMIT)
            copy.add(iterator.next())
        }
    }
    val events: List<ReceiptSetupFailureEvent> get() = recorded.toList()

    init {
        require(eventsTotal in recorded.size..ReceiptSetupFailureTrace.MAX_PROGRESS)
        require(!eventsSaturated || eventsTotal == ReceiptSetupFailureTrace.MAX_PROGRESS)
    }

    fun json(): String {
        // Every string is a closed ASCII enum; no general string escaper/input exists.
        val value = "{\"version\":1,\"case\":\"${case.name}\",\"expected\":\"${expected.name}\"," +
            "\"actual\":\"${actual.name}\",\"error\":\"${error.name}\",\"events_total\":$eventsTotal," +
            "\"events_saturated\":$eventsSaturated,\"events\":[" + recorded.joinToString(",") { "\"${it.name}\"" } +
            "],\"source\":{\"opened\":${source.opened},\"closed\":${source.closed},\"active\":${source.active}," +
            "\"reads\":${source.readCalls},\"bytes\":${source.bytesRead}," +
            "\"reads_saturated\":${source.readsSaturated},\"bytes_saturated\":${source.bytesSaturated}}}"
        require(value.all { it.code in 32..126 })
        require((ReceiptSetupFailureTrace.WIRE_PREFIX + value).toByteArray(Charsets.UTF_8).size <= ReceiptSetupFailureTrace.MAX_BYTES)
        return value
    }
}

/** Diagnostic work cannot replace, wrap or suppress the original operation failure. */
internal object ReceiptSetupFailureReporter {
    fun <T> run(
        claim: () -> Boolean,
        snapshot: () -> ReceiptSetupFailureSnapshot,
        send: (Int, String, String) -> Unit,
        block: () -> T,
    ): T {
        try {
            return block()
        } catch (original: Throwable) {
            try {
                if (claim()) {
                    val json = snapshot().json()
                    send(ReceiptSetupFailureTrace.STATUS_CODE, ReceiptSetupFailureTrace.STATUS_KEY, json)
                }
            } catch (_: Throwable) {
                // An attempted diagnostic may fail; the operation remains the same failure.
            }
            throw original
        }
    }
}

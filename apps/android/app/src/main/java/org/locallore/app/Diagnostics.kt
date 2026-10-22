/* Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0 */
package org.locallore.app

enum class DiagnosticPhase { PREPARE, COMMIT, CANCEL, RESET, CLOSE, EXPORT }

enum class DiagnosticOutcome { PREPARED, ACCEPTED, REJECTED, CANCELLED, COMPLETED, FAILED, STALE, UNKNOWN }

/** Only fixed codes cross the diagnostic boundary; native descriptions are never retained. */
enum class DiagnosticError(private val nativeCategory: String? = null) {
    NONE,
    VERSION("Version"), SCOPE("Scope"), STALE("Stale"), RETRY_MISMATCH("RetryMismatch"),
    MALFORMED("Malformed"), TOO_LARGE("TooLarge"), AGENCY("Agency"), AUTHOR_UI_REQUIRED("AuthorUiRequired"),
    CLARIFICATION_REQUIRED("ClarificationRequired"), UNKNOWN_REFERENCE("UnknownReference"),
    DEAD_ACTOR("DeadActor"), LOCATION("Location"), INVENTORY("Inventory"), RESOURCE("Resource"),
    ABILITY("Ability"), KNOWLEDGE("Knowledge"), RULE("Rule"), CANCELLED("Cancelled"),
    PROVIDER("Provider"), TIMEOUT("Timeout"), NARRATION("Narration"), CORRUPT_HISTORY("CorruptHistory"),
    INTERNAL("Internal"), INVALID_HANDLE("InvalidHandle"), SESSION_LIMIT("SessionLimit"),
    WRONG_THREAD("WrongThread"), BUSY("Busy"), OPERATION_LIMIT("OperationLimit"),
    INVALID_OPERATION("InvalidOperation"),
    TRANSPORT, UNKNOWN;

    companion object {
        fun fromNative(category: String): DiagnosticError =
            entries.firstOrNull { it.nativeCategory == category } ?: UNKNOWN
    }
}

/** A detached immutable preview. It contains no live log or mutable record references. */
class DiagnosticSnapshot internal constructor(val json: String)

/**
 * Process-memory-only diagnostics for the fake-inference Rust demo. No text, identifiers,
 * exceptions, timestamps, paths, or device/model metadata can be supplied to record().
 * Counters saturate at Int.MAX_VALUE; clear starts a new empty sequence.
 */
class DiagnosticLog(private val capacity: Int = 64) {
    private data class Record(
        val sequence: Int,
        val phase: DiagnosticPhase,
        val outcome: DiagnosticOutcome,
        val elapsedMs: Long,
        val error: DiagnosticError,
    )

    private val lock = Any()
    private val records = ArrayDeque<Record>()
    private var sequence = 0
    private var dropped = 0

    init { require(capacity in 1..64) { "Diagnostic capacity must be within 1..64" } }

    fun record(
        phase: DiagnosticPhase,
        outcome: DiagnosticOutcome,
        elapsedMs: Long,
        error: DiagnosticError = DiagnosticError.NONE,
    ) = synchronized(lock) {
        sequence = increment(sequence)
        if (records.size == capacity) {
            records.removeFirst()
            dropped = increment(dropped)
        }
        records.addLast(Record(sequence, phase, outcome, elapsedMs.coerceIn(0L, 60_000L), error))
    }

    fun snapshot(): DiagnosticSnapshot = synchronized(lock) {
        val json = buildString {
            append("{\"version\":1,\"source\":\"rust_engine_fake_demo\",\"capacity\":")
            append(capacity)
            append(",\"count\":")
            append(records.size)
            append(",\"dropped\":")
            append(dropped)
            append(",\"records\":[")
            records.forEachIndexed { index, record ->
                if (index != 0) append(',')
                append("{\"seq\":")
                append(record.sequence)
                append(",\"phase\":\"")
                append(record.phase.name)
                append("\",\"outcome\":\"")
                append(record.outcome.name)
                append("\",\"elapsed_ms\":")
                append(record.elapsedMs)
                append(",\"error\":\"")
                append(record.error.name)
                append("\"}")
            }
            append("]}")
        }
        // Every emitted character comes from fixed ASCII tokens or bounded nonnegative numbers.
        check(json.length <= 16_384 && json.all { it.code <= 127 })
        DiagnosticSnapshot(json)
    }

    fun clear() = synchronized(lock) {
        records.clear()
        sequence = 0
        dropped = 0
    }

    private fun increment(value: Int): Int = if (value == Int.MAX_VALUE) value else value + 1
}

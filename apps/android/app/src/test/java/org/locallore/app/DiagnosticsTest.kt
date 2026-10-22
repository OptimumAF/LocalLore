/* Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0 */
package org.locallore.app

import java.util.concurrent.CountDownLatch
import java.util.concurrent.Executors
import java.util.concurrent.TimeUnit
import org.junit.Assert.*
import org.junit.Test

class DiagnosticsTest {
    @Test fun snapshotHasOnlyTheDeclaredSchemaAndFixedSource() {
        val log = DiagnosticLog(2)
        log.record(DiagnosticPhase.COMMIT, DiagnosticOutcome.ACCEPTED, 15)
        val document = document(log)
        assertEquals(setOf("version", "source", "capacity", "count", "dropped", "records"), document.keys)
        assertEquals(1L, document["version"])
        assertEquals("rust_engine_fake_demo", document["source"])
        assertEquals(2L, document["capacity"])
        assertEquals(1L, document["count"])
        assertEquals(0L, document["dropped"])
        val record = records(document).single()
        assertEquals(setOf("seq", "phase", "outcome", "elapsed_ms", "error"), record.keys)
        assertEquals(mapOf("seq" to 1L, "phase" to "COMMIT", "outcome" to "ACCEPTED",
            "elapsed_ms" to 15L, "error" to "NONE"), record)
    }

    @Test fun onlyExactNativeErrorCodesAreRecognizedAndUnknownTextIsNeverRetained() {
        val log = DiagnosticLog()
        val secrets = listOf("", "Provider private-story=SECRET", "provider", " Provider", "Provider\n",
            "C:\\Users\\private\\story.json", "https://private.invalid?credential=SECRET", "Mira said SECRET",
            "Internal\u0000SECRET", "雪".repeat(20_000))
        secrets.forEach {
            val code = DiagnosticError.fromNative(it)
            assertEquals(DiagnosticError.UNKNOWN, code)
            log.record(DiagnosticPhase.PREPARE, DiagnosticOutcome.REJECTED, 1, code)
        }
        assertEquals(DiagnosticError.PROVIDER, DiagnosticError.fromNative("Provider"))
        assertEquals(DiagnosticError.RETRY_MISMATCH, DiagnosticError.fromNative("RetryMismatch"))
        assertEquals(DiagnosticError.INVALID_HANDLE, DiagnosticError.fromNative("InvalidHandle"))
        assertEquals(DiagnosticError.WRONG_THREAD, DiagnosticError.fromNative("WrongThread"))
        val json = log.snapshot().json
        assertFalse(json.contains("SECRET"))
        assertFalse(json.contains("private"))
        assertFalse(json.contains("Provider"))
        assertTrue(records(document(log)).all { it["error"] == "UNKNOWN" })
    }

    @Test fun elapsedValuesAreBoundedWithoutOverflow() {
        val log = DiagnosticLog()
        listOf(Long.MIN_VALUE, -1L, 0L, 59_999L, 60_000L, 60_001L, Long.MAX_VALUE).forEach {
            log.record(DiagnosticPhase.PREPARE, DiagnosticOutcome.PREPARED, it)
        }
        assertEquals(listOf(0L, 0L, 0L, 59_999L, 60_000L, 60_000L, 60_000L),
            records(document(log)).map { it["elapsed_ms"] })
    }

    @Test fun oldestRecordsAreDroppedAndCountAlwaysReflectsRetainedRecords() {
        val log = DiagnosticLog(3)
        repeat(100) { log.record(DiagnosticPhase.CANCEL, DiagnosticOutcome.CANCELLED, it.toLong()) }
        val document = document(log)
        assertEquals(3L, document["count"])
        assertEquals(97L, document["dropped"])
        assertEquals(listOf(98L, 99L, 100L), records(document).map { it["seq"] })
        assertEquals(listOf(97L, 98L, 99L), records(document).map { it["elapsed_ms"] })
    }

    @Test fun snapshotsAreDetachedAndClearResetsAllCounters() {
        val log = DiagnosticLog(1)
        log.record(DiagnosticPhase.RESET, DiagnosticOutcome.COMPLETED, 2)
        val preview = log.snapshot()
        val original = preview.json
        repeat(4) { log.record(DiagnosticPhase.CLOSE, DiagnosticOutcome.COMPLETED, 3) }
        log.clear()
        assertEquals(original, preview.json)
        assertEquals(0L, document(log)["count"])
        assertEquals(0L, document(log)["dropped"])
        assertTrue(records(document(log)).isEmpty())
        log.record(DiagnosticPhase.EXPORT, DiagnosticOutcome.COMPLETED, 4)
        assertEquals(1L, records(document(log)).single()["seq"])
        assertEquals(original, preview.json)
    }

    @Test fun everyAllowedTokenCombinationFitsTheAsciiAndUtf8Budget() {
        val log = DiagnosticLog()
        DiagnosticPhase.entries.forEach { phase ->
            DiagnosticOutcome.entries.forEach { outcome ->
                DiagnosticError.entries.forEach { error ->
                    log.record(phase, outcome, Long.MAX_VALUE, error)
                }
                val json = log.snapshot().json
                assertTrue(json.all { it.code in 0..127 })
                assertTrue(json.toByteArray(Charsets.UTF_8).size <= 16_384)
                assertTrue(records(document(log)).size <= 64)
            }
        }
    }

    @Test fun capacityCannotDisableTheBound() {
        listOf(Int.MIN_VALUE, -1, 0, 65, Int.MAX_VALUE).forEach { capacity ->
            try { DiagnosticLog(capacity); fail("Expected invalid capacity to fail") }
            catch (_: IllegalArgumentException) { }
        }
    }

    @Test fun countersSaturateRatherThanWrappingOrMakingUnboundedNumbers() {
        val log = DiagnosticLog(1)
        // Exercise the otherwise multi-billion-record overflow boundary without extra production API.
        listOf("sequence", "dropped").forEach { field ->
            DiagnosticLog::class.java.getDeclaredField(field).also { it.isAccessible = true }
                .setInt(log, Int.MAX_VALUE - 1)
        }
        repeat(4) { log.record(DiagnosticPhase.PREPARE, DiagnosticOutcome.PREPARED, 1) }
        val document = document(log)
        assertEquals(Int.MAX_VALUE.toLong(), document["dropped"])
        assertEquals(Int.MAX_VALUE.toLong(), records(document).single()["seq"])
        assertTrue(log.snapshot().json.toByteArray(Charsets.UTF_8).size <= 16_384)
    }

    @Test fun concurrentWritersAndSnapshotsHaveConsistentCountsAndOrderedSequences() {
        val log = DiagnosticLog(64)
        val executor = Executors.newFixedThreadPool(5)
        val start = CountDownLatch(1)
        try {
            val writers = (0 until 4).map {
                executor.submit {
                    assertTrue(start.await(10, TimeUnit.SECONDS))
                    repeat(1_000) { log.record(DiagnosticPhase.PREPARE, DiagnosticOutcome.PREPARED, 1) }
                }
            }
            val reader = executor.submit {
                assertTrue(start.await(10, TimeUnit.SECONDS))
                repeat(100) {
                    val document = document(log)
                    val records = records(document)
                    assertEquals(records.size.toLong(), document["count"])
                    val sequence = records.map { it["seq"] as Long }
                    assertEquals(sequence.sorted().distinct(), sequence)
                }
            }
            start.countDown()
            (writers + reader).forEach { it.get(15, TimeUnit.SECONDS) }
            val document = document(log)
            assertEquals(64L, document["count"])
            assertEquals(3_936L, document["dropped"])
            assertEquals(4_000L, records(document).last()["seq"])
        } finally { executor.shutdownNow() }
    }

    @Suppress("UNCHECKED_CAST")
    private fun document(log: DiagnosticLog): Map<String, Any> = Json(log.snapshot().json).parse() as Map<String, Any>
    @Suppress("UNCHECKED_CAST")
    private fun records(document: Map<String, Any>): List<Map<String, Any>> =
        document.getValue("records") as List<Map<String, Any>>

    /** Independent JSON grammar reader for the emitted string/integer/object/array subset. */
    private class Json(private val source: String) {
        private var cursor = 0
        fun parse(): Any = value().also { check(cursor == source.length) }
        private fun value(): Any = when (source[cursor]) {
            '{' -> {
                cursor++
                val result = linkedMapOf<String, Any>()
                if (!take('}')) {
                    do {
                        val key = string()
                        check(take(':'))
                        check(key !in result)
                        result[key] = value()
                    } while (take(','))
                    check(take('}'))
                }
                result
            }
            '[' -> {
                cursor++
                val result = mutableListOf<Any>()
                if (!take(']')) {
                    do { result.add(value()) } while (take(','))
                    check(take(']'))
                }
                result
            }
            '"' -> string()
            else -> {
                val start = cursor
                while (cursor < source.length && source[cursor] in '0'..'9') cursor++
                check(cursor > start)
                source.substring(start, cursor).toLong()
            }
        }
        private fun string(): String {
            check(take('"'))
            val start = cursor
            while (source[cursor] != '"') {
                check(source[cursor] != '\\' && source[cursor].code in 32..127)
                cursor++
            }
            return source.substring(start, cursor).also { cursor++ }
        }
        private fun take(character: Char): Boolean =
            if (cursor < source.length && source[cursor] == character) { cursor++; true } else false
    }
}

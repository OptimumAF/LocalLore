/* Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0 */
package org.locallore.app

import com.google.ai.edge.litertlm.ResponseFormat
import com.google.gson.JsonObject
import com.google.gson.JsonPrimitive
import org.junit.Assert.*
import org.junit.Test

/** Actual public SDK value objects only; no engine, native library or model initialization. */
class LiteRtResponseFormatTest {
    @Test fun finiteLongQuotedLiteralSelectsExactPublicRegexPayload() {
        val literal = "\"\"" + "a".repeat(30)
        val schema = JsonObject().apply { addProperty("const", literal); addProperty("type", "string") }.toString()
        val before = schema.toByteArray(Charsets.UTF_8)
        val format = liteRtResponseFormat(schema)
        assertEquals(ResponseFormat.Type.REGEX, format.type)
        assertEquals(1, format.type.value)
        assertEquals(finiteSchemaRegex(schema), format.schemaOrPattern)
        assertArrayEquals(before, schema.toByteArray(Charsets.UTF_8))
        val regex = java.util.regex.Pattern.compile(format.schemaOrPattern)
        assertTrue(regex.matcher(JsonPrimitive(literal).toString()).matches())
        assertFalse(regex.matcher(JsonPrimitive(literal.take(1)).toString()).matches())
    }

    @Test fun nonfiniteNarrationAndUnknownKeywordsKeepExactJsonPath() {
        for (schema in listOf(
            """{"type":"string","maxLength":180}""",
            """{"type":"object","properties":{"text":{"type":"string"}},"required":["text"],"additionalProperties":false}""",
            """{"const":"speech","unknownKeyword":true}""",
        )) {
            val format = liteRtResponseFormat(schema)
            assertEquals(ResponseFormat.Type.JSON_OBJECT, format.type)
            assertEquals(2, format.type.value)
            assertEquals(schema, format.schemaOrPattern)
        }
    }

    @Test fun malformedJsonStillFailsBeforeSdkDispatch() {
        try {
            liteRtResponseFormat("{")
            fail("Malformed schema was accepted")
        } catch (_: IllegalArgumentException) {
            // Existing SDK constructor failure; no generated response or commit authority.
        }
    }

    @Test fun observesPreparedPublicKindsWithoutChangingTheArgumentOrDispatch() {
        val schemas = listOf("""{"const":"literal"}""", """{"type":"string","maxLength":180}""")
        for ((schema, expected) in schemas.zip(listOf(LiteRtSendFormat.REGEX, LiteRtSendFormat.JSON_OBJECT))) {
            val trace = LiteRtSendTrace()
            val argument = liteRtResponseFormat(schema)
            val payload = argument.schemaOrPattern
            var sends = 0
            observedLiteRtSend(trace, prepare = { argument }, dispatch = { actual ->
                observedLiteRtResponseFormat(trace, actual)
                assertSame(argument, actual)
                assertEquals(payload, actual.schemaOrPattern)
                sends++
            })
            assertEquals(1, sends)
            val snapshot = trace.snapshot()
            assertEquals(expected, snapshot.lastFormat)
            assertEquals(1, snapshot.formatCounts.getValue(expected))
            assertEquals(1, snapshot.formatCounts.values.sum())
            assertEquals(1, snapshot.counts.getValue(LiteRtSendEvent.ASYNC_CALL_RETURNED))
        }
    }

    @Test fun formatObserverFailureCannotReplaceDispatchOrItsOriginalFailure() {
        val observerFailure = AssertionError("Private observer failure")
        val observer = object : LiteRtSendObserver {
            override fun record(event: LiteRtSendEvent) { throw observerFailure }
            override fun format(value: LiteRtSendFormat) { throw observerFailure }
        }
        val argument = liteRtResponseFormat("""{"const":"literal"}""")
        var sends = 0
        observedLiteRtSend(observer, prepare = { argument }, dispatch = { actual ->
            observedLiteRtResponseFormat(observer, actual); sends++
        })
        assertEquals(1, sends)
        val original = IllegalStateException("Original dispatch failure")
        try {
            observedLiteRtSend(observer, prepare = { argument }, dispatch = { actual ->
                observedLiteRtResponseFormat(observer, actual); throw original
            })
            fail("Dispatch failure lost")
        } catch (observed: Throwable) { assertSame(original, observed) }
        assertTrue(original.suppressed.isEmpty())
        observedLiteRtResponseFormat(null, argument)
    }
}

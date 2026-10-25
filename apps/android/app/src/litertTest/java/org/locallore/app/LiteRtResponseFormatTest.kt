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
}

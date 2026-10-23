// Copyright 2026 LocalLore contributors.
// SPDX-License-Identifier: Apache-2.0
package org.locallore.runtimebench.litert;

import static org.junit.Assert.*;
import com.google.gson.JsonObject;
import com.google.gson.JsonParser;
import java.io.IOException;
import java.nio.charset.StandardCharsets;
import org.junit.Test;

/** Malformed request regression cases, not model or device evidence. */
public class RequestTest {
    private static String valid() {
        return "{\"version\":1,\"role\":\"director\",\"prompt\":\"Synthetic Lantern Quay scene.\",\"max_tokens\":350,\"context_tokens\":4096,\"threads\":4,\"schema\":null}";
    }
    private static Request parse(String text) throws IOException { return Request.parse(text.getBytes(StandardCharsets.UTF_8)); }
    private static void rejected(String text) throws IOException {
        try { parse(text); fail("Expected rejection"); } catch (IOException expected) { /* category never contains raw JSON */ }
    }
    private static String field(String name, String json) {
        JsonObject object = JsonParser.parseString(valid()).getAsJsonObject();
        object.add(name, JsonParser.parseString(json)); return object.toString();
    }
    @Test public void exactValidContractAndSchema() throws Exception {
        Request request = parse(valid()); assertEquals(350, request.maxTokens);
        assertEquals("director", request.role); assertNull(request.schema);
        assertTrue(parse(field("schema", "{\"type\":\"object\",\"additionalProperties\":false}")).schema.has("type"));
    }
    @Test public void roleSpecificOutputCaps() throws Exception {
        rejected(field("max_tokens", "351"));
        String narrator = valid().replace("director", "narrator"); rejected(narrator);
        assertEquals(220, parse(narrator.replace(":350", ":220")).maxTokens);
        rejected(field("max_tokens", "0")); rejected(field("max_tokens", "-1"));
    }
    @Test public void rejectsUnknownMissingAndDuplicateKeysAtEveryDepth() throws Exception {
        rejected(valid().replace("\"version\":1", "\"version\":1,\"version\":1"));
        rejected(valid().replace("\"version\":1", "\"version\":1,\"\\u0076ersion\":1"));
        rejected(field("tool", "\"execute\""));
        rejected(valid().replace(",\"schema\":null", ""));
        rejected(valid().replace("\"schema\":null", "\"schema\":{\"type\":\"object\",\"type\":\"string\"}"));
    }
    @Test public void integersCannotBeBooleanFloatExponentOrHuge() throws Exception {
        for (String value : new String[]{"true", "1.0", "1e0", "999999999999999999999", "null", "\"1\""}) rejected(field("version", value));
        rejected(field("context_tokens", "8192")); rejected(field("threads", "8"));
    }
    @Test public void noWhitespaceNulOrWrongTypePrompt() throws Exception {
        for (String value : new String[]{"\"\"", "\" \\n \\t\"", "\"x\\u0000y\"", "1", "[]"}) rejected(field("prompt", value));
        rejected(field("role", "\"tool\"")); rejected(field("schema", "[]"));
    }
    @Test public void rejectsNonJsonLeniencyAndTrailingMaterial() throws Exception {
        for (String value : new String[]{"// comment\n" + valid(), valid() + "{}", valid().replace(":350", ":NaN"), "[]", valid().replace("\"version\"", "version")}) rejected(value);
    }
    @Test public void byteBudgetIncludesSchemaAndUtf8() throws Exception {
        rejected(field("prompt", "\"" + "x".repeat(32768) + "\""));
        rejected(field("prompt", "\"" + "é".repeat(16384) + "\""));
        rejected(field("schema", "{\"long\":\"" + "x".repeat(32768) + "\"}"));
    }
    @Test public void rejectsMalformedUtf8AndUnpairedSurrogate() throws Exception {
        try { Request.parse(new byte[]{(byte) 0xff}); fail(); } catch (IOException expected) { }
        rejected(valid().replace("Synthetic Lantern Quay scene.", "\\ud800"));
        rejected(valid().replace("Synthetic Lantern Quay scene.", "\\udc00"));
        assertEquals("😀", parse(valid().replace("Synthetic Lantern Quay scene.", "\\ud83d\\ude00")).prompt);
    }
    @Test public void deeplyNestedSchemaFailsWithinInputBudget() throws Exception {
        rejected(field("schema", "{\"items\":" + "[".repeat(35) + "null" + "]".repeat(35) + "}"));
    }
    @Test public void finiteSchemaNumbersRetainExactValues() throws Exception {
        assertEquals("1.25", parse(field("schema", "{\"minimum\":1.25}")).schema.get("minimum").getAsString());
        rejected(valid().replace("\"schema\":null", "\"schema\":{\"minimum\":1e9999}"));
    }
}

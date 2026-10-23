// Copyright 2026 LocalLore contributors.
// SPDX-License-Identifier: Apache-2.0
package org.locallore.runtimebench.litert;

import com.google.gson.JsonArray;
import com.google.gson.JsonElement;
import com.google.gson.JsonNull;
import com.google.gson.JsonObject;
import com.google.gson.JsonPrimitive;
import com.google.gson.Strictness;
import com.google.gson.stream.JsonReader;
import com.google.gson.stream.JsonToken;
import java.io.IOException;
import java.io.StringReader;
import java.nio.ByteBuffer;
import java.nio.charset.CodingErrorAction;
import java.nio.charset.StandardCharsets;
import java.util.HashSet;
import java.util.Set;
import java.util.Arrays;

/** Exact bounded worker request v1. Does not retain error text or accept tools. */
final class Request {
    final String prompt;
    final String role;
    final int maxTokens;
    final JsonObject schema;
    private Request(String prompt, String role, int maxTokens, JsonObject schema) {
        this.prompt = prompt; this.role = role; this.maxTokens = maxTokens; this.schema = schema;
    }
    static Request parse(byte[] data) throws IOException {
        if (data.length > 32768) throw invalid();
        String json = StandardCharsets.UTF_8.newDecoder()
            .onMalformedInput(CodingErrorAction.REPORT).onUnmappableCharacter(CodingErrorAction.REPORT)
            .decode(ByteBuffer.wrap(data)).toString();
        try (JsonReader reader = new JsonReader(new StringReader(json))) {
            reader.setStrictness(Strictness.STRICT);
            JsonElement parsed = read(reader, 0);
            if (reader.peek() != JsonToken.END_DOCUMENT || !parsed.isJsonObject()) throw invalid();
            JsonObject object = parsed.getAsJsonObject();
            if (!object.keySet().equals(new HashSet<>(Arrays.asList("version", "role", "prompt", "max_tokens", "context_tokens", "threads", "schema")))) throw invalid();
            if (integer(object.get("version")) != 1 || integer(object.get("context_tokens")) != 4096
                || integer(object.get("threads")) != 4) throw invalid();
            String role = string(object.get("role"));
            String prompt = string(object.get("prompt"));
            int tokens = integer(object.get("max_tokens"));
            if ((!role.equals("director") && !role.equals("narrator")) || prompt.trim().isEmpty()
                || prompt.indexOf('\0') >= 0 || tokens < 1 || tokens > (role.equals("director") ? 350 : 220)) throw invalid();
            JsonElement schema = object.get("schema");
            if (!schema.isJsonNull() && !schema.isJsonObject()) throw invalid();
            return new Request(prompt, role, tokens, schema.isJsonNull() ? null : schema.getAsJsonObject());
        } catch (RuntimeException error) { throw invalid(); }
    }
    private static JsonElement read(JsonReader reader, int depth) throws IOException {
        if (depth > 32) throw invalid();
        switch (reader.peek()) {
            case BEGIN_OBJECT:
                reader.beginObject();
                JsonObject object = new JsonObject();
                Set<String> keys = new HashSet<>();
                while (reader.hasNext()) {
                    String key = checkedString(reader.nextName());
                    if (!keys.add(key)) throw invalid();
                    object.add(key, read(reader, depth + 1));
                }
                reader.endObject(); return object;
            case BEGIN_ARRAY:
                reader.beginArray(); JsonArray array = new JsonArray();
                while (reader.hasNext()) array.add(read(reader, depth + 1));
                reader.endArray(); return array;
            case STRING: return new JsonPrimitive(checkedString(reader.nextString()));
            case NUMBER:
                String number = reader.nextString();
                double finite = Double.parseDouble(number);
                if (!Double.isFinite(finite)) throw invalid();
                // Retain exact lexical shape so 1.0 cannot become an integer contract field.
                return new JsonPrimitive(new LexicalNumber(number));
            case BOOLEAN: return new JsonPrimitive(reader.nextBoolean());
            case NULL: reader.nextNull(); return JsonNull.INSTANCE;
            default: throw invalid();
        }
    }
    private static String checkedString(String value) throws IOException {
        for (int index = 0; index < value.length(); index++) {
            char current = value.charAt(index);
            if (Character.isHighSurrogate(current)) {
                if (++index >= value.length() || !Character.isLowSurrogate(value.charAt(index))) throw invalid();
            } else if (Character.isLowSurrogate(current)) throw invalid();
        }
        return value;
    }
    private static int integer(JsonElement element) throws IOException {
        if (!element.isJsonPrimitive() || !element.getAsJsonPrimitive().isNumber()
            || !element.getAsString().matches("0|[1-9][0-9]*")) throw invalid();
        try { return Integer.parseInt(element.getAsString()); } catch (NumberFormatException error) { throw invalid(); }
    }
    private static String string(JsonElement element) throws IOException {
        if (!element.isJsonPrimitive() || !element.getAsJsonPrimitive().isString()) throw invalid();
        return element.getAsString();
    }
    static IOException invalid() { return new IOException("invalid_request"); }
    private static final class LexicalNumber extends Number {
        private final String value;
        LexicalNumber(String value) { this.value = value; }
        public int intValue() { return Integer.parseInt(value); }
        public long longValue() { return Long.parseLong(value); }
        public float floatValue() { return Float.parseFloat(value); }
        public double doubleValue() { return Double.parseDouble(value); }
        public String toString() { return value; }
    }
}

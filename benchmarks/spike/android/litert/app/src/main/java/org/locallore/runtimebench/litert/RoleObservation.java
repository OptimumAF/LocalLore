// Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0
package org.locallore.runtimebench.litert;

import com.google.gson.JsonNull;
import com.google.gson.JsonObject;
import java.util.Arrays;

/** Optional frozen diagnostics, never generation output or canonical authority. */
final class RoleObservation {
    static final int MAX_CALLBACKS = 65535;
    final int callbackMessages, bufferedTextBytes;
    final String callbackError;
    final boolean benchmarkAvailable;
    final Integer inputTokens, outputTokens;
    final Config configuration;

    /** Values describe requested configuration and a nonempty template render, not enforcement. */
    static final class Config {
        final boolean schemaRequested, thinkingDisabledRequested, templateRendered;
        final int maxTokens, promptBytes, schemaBytes;
        Config(boolean schemaRequested, boolean thinkingDisabledRequested, boolean templateRendered,
                int maxTokens, int promptBytes, int schemaBytes) {
            if (maxTokens < 1 || maxTokens > 350 || promptBytes < 1 || promptBytes > 32768
                    || schemaBytes < 0 || schemaBytes > 32768 || schemaRequested != (schemaBytes > 0))
                throw invalid();
            this.schemaRequested = schemaRequested; this.thinkingDisabledRequested = thinkingDisabledRequested;
            this.templateRendered = templateRendered; this.maxTokens = maxTokens;
            this.promptBytes = promptBytes; this.schemaBytes = schemaBytes;
        }
        JsonObject toJson() {
            JsonObject value = new JsonObject(); value.addProperty("schema_requested", schemaRequested);
            value.addProperty("thinking_disabled_requested", thinkingDisabledRequested);
            value.addProperty("template_rendered", templateRendered); value.addProperty("max_tokens", maxTokens);
            value.addProperty("prompt_utf8_bytes", promptBytes); value.addProperty("schema_utf8_bytes", schemaBytes);
            return value;
        }
    }

    RoleObservation(int callbackMessages, int bufferedTextBytes, String callbackError,
            boolean benchmarkAvailable, Integer inputTokens, Integer outputTokens) {
        this(callbackMessages, bufferedTextBytes, callbackError, benchmarkAvailable, inputTokens, outputTokens, null);
    }
    RoleObservation(int callbackMessages, int bufferedTextBytes, String callbackError,
            boolean benchmarkAvailable, Integer inputTokens, Integer outputTokens, Config configuration) {
        if (callbackMessages < 0 || callbackMessages > MAX_CALLBACKS || bufferedTextBytes < 0 || bufferedTextBytes > 16384
                || bufferedTextBytes > 0 && callbackMessages == 0
                || !Arrays.asList("none", "unsupported_output", "output_too_large", "generation_failed").contains(callbackError)
                || (benchmarkAvailable ? inputTokens == null || outputTokens == null || inputTokens < 0 || outputTokens < 0
                    : inputTokens != null || outputTokens != null)) throw invalid();
        this.callbackMessages = callbackMessages; this.bufferedTextBytes = bufferedTextBytes;
        this.callbackError = callbackError; this.benchmarkAvailable = benchmarkAvailable;
        this.inputTokens = inputTokens; this.outputTokens = outputTokens; this.configuration = configuration;
    }
    JsonObject toJson() {
        JsonObject value = new JsonObject(); value.addProperty("version", 1);
        value.addProperty("callback_messages", callbackMessages); value.addProperty("buffered_text_bytes", bufferedTextBytes);
        value.addProperty("callback_error", callbackError); value.addProperty("benchmark_available", benchmarkAvailable);
        if (inputTokens == null) value.add("sdk_input_tokens", JsonNull.INSTANCE); else value.addProperty("sdk_input_tokens", inputTokens);
        if (outputTokens == null) value.add("sdk_output_tokens", JsonNull.INSTANCE); else value.addProperty("sdk_output_tokens", outputTokens);
        value.add("configuration", configuration == null ? JsonNull.INSTANCE : configuration.toJson()); return value;
    }
    private static IllegalArgumentException invalid() { return new IllegalArgumentException("invalid_role_observation"); }
}

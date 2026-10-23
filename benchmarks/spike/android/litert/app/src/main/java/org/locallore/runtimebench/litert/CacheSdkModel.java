// Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0
package org.locallore.runtimebench.litert;

import com.google.ai.edge.litertlm.Backend;
import com.google.ai.edge.litertlm.BenchmarkInfo;
import com.google.ai.edge.litertlm.Conversation;
import com.google.ai.edge.litertlm.ConversationConfig;
import com.google.ai.edge.litertlm.Engine;
import com.google.ai.edge.litertlm.EngineConfig;
import com.google.ai.edge.litertlm.Message;
import com.google.ai.edge.litertlm.ResponseFormat;
import com.google.ai.edge.litertlm.SamplerConfig;
import com.google.ai.edge.litertlm.ThinkingConfig;
import com.google.gson.JsonNull;
import com.google.gson.JsonObject;
import java.io.File;
import java.util.Collections;
import java.util.concurrent.TimeUnit;
import java.util.concurrent.atomic.AtomicInteger;

/** Same role/ownership protocol as the original adapter, with an explicit cache destination. */
final class CacheSdkModel implements WarmRunner.Model {
    private final Engine engine;
    private final JsonObject metrics;
    private final AtomicInteger pulses;
    CacheSdkModel(File model, File cache, JsonObject metrics, AtomicInteger pulses) {
        // Exact pinned 0.18.1 eight-argument constructor; no model-directory default.
        engine = new Engine(new EngineConfig(model.getPath(), new Backend.CPU(4, null),
            null, null, 4096, null, cache.getPath(), null));
        this.metrics = metrics; this.pulses = pulses;
    }
    @Override public void initialize() throws Exception {
        try { engine.initialize(); }
        catch (RuntimeException failure) { throw new WarmRunner.Failure("model_load_failed"); }
        increment("engines_opened");
    }
    @Override public WarmRunner.Role open(Request request) throws Exception {
        ConversationConfig config = new ConversationConfig(null, Collections.emptyList(), Collections.emptyList(),
            new SamplerConfig(1, 1.0, 0.0, 1), false, null, Collections.emptyMap(), null, false,
            request.maxTokens, new ThinkingConfig(false, 0), request.schema != null, false, null);
        Conversation conversation = engine.createConversation(config);
        increment("conversations_opened");
        try {
            if (conversation.renderMessageIntoString(Message.Companion.user(request.prompt), Collections.emptyMap()).isEmpty())
                throw new WarmRunner.Failure("unsupported_template");
            return new Role(conversation, request);
        } catch (Exception failure) {
            try { conversation.close(); increment("conversations_closed"); }
            catch (Exception close) { throw new WarmRunner.Undrained(); }
            throw failure;
        }
    }
    @Override public void close() {
        if (engine.isInitialized()) { engine.close(); increment("engines_closed"); }
    }
    private void increment(String key) { metrics.addProperty(key, metrics.get(key).getAsInt() + 1); }
    private final class Role implements WarmRunner.Role {
        private final Conversation conversation;
        private final Request request;
        private final SpikeInstrumentation.Stream stream = new SpikeInstrumentation.Stream();
        private long began;
        private int startingPulses;
        private boolean cancelling;
        Role(Conversation conversation, Request request) { this.conversation = conversation; this.request = request; }
        @Override public void start() {
            began = System.nanoTime(); startingPulses = pulses.get();
            ResponseFormat format = request.schema == null ? null : ResponseFormat.json(request.schema.toString());
            conversation.sendMessageAsync(request.prompt, stream, Collections.emptyMap(), null, null, null,
                request.maxTokens, new ThinkingConfig(false, 0), format);
        }
        @Override public boolean await(long milliseconds) throws Exception {
            boolean terminal = stream.done.await(milliseconds, TimeUnit.MILLISECONDS);
            if (terminal) {
                metrics.addProperty("generation_main_pulses", pulses.get() - startingPulses);
                metrics.addProperty(cancelling ? "cancel_terminal_callback" : "generate_terminal_callback", true);
            }
            return terminal;
        }
        @Override public void cancel() {
            cancelling = true; long started = System.nanoTime(); conversation.cancelProcess();
            metrics.addProperty("cancel_call_ms", elapsed(started));
        }
        @Override public boolean hasOutput() { return stream.hasOutput(); }
        @Override public JsonObject result(double loadMs) throws Exception {
            String text = stream.text();
            BenchmarkInfo info = conversation.getBenchmarkInfo();
            int input = info.getLastPrefillTokenCount(), output = info.getLastDecodeTokenCount();
            if (input <= 0 || output <= 0 || input + output > 4096 || output > request.maxTokens)
                throw new WarmRunner.Failure("context_overflow");
            JsonObject result = new JsonObject(); result.addProperty("version", 1);
            result.addProperty("status", "completed"); result.add("error", JsonNull.INSTANCE);
            result.addProperty("text", text); result.addProperty("load_ms", loadMs);
            result.addProperty("generation_ms", elapsed(began)); result.addProperty("input_tokens", input);
            result.addProperty("output_tokens", output); result.addProperty("schema_enforced", request.schema != null);
            result.addProperty("thinking_disabled", true); result.addProperty("template_applied", true);
            return result;
        }
        @Override public void close() { conversation.close(); increment("conversations_closed"); }
    }
    private static double elapsed(long began) { return Math.min(180000.0, (System.nanoTime() - began) / 1000000.0); }
}

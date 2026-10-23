// Copyright 2026 LocalLore contributors.
// SPDX-License-Identifier: Apache-2.0
package org.locallore.runtimebench.litert;

import android.app.Activity;
import android.app.Instrumentation;
import android.os.Bundle;
import android.os.Handler;
import android.os.Looper;
import android.os.Process;
import android.system.Os;
import android.system.OsConstants;
import android.util.Base64;
import com.google.ai.edge.litertlm.*;
import com.google.gson.JsonNull;
import com.google.gson.JsonObject;
import java.io.File;
import java.io.FileDescriptor;
import java.io.FileInputStream;
import java.io.FileOutputStream;
import java.nio.charset.StandardCharsets;
import java.util.Collections;
import java.util.concurrent.CountDownLatch;
import java.util.concurrent.TimeUnit;
import java.util.concurrent.atomic.AtomicBoolean;
import java.util.concurrent.atomic.AtomicInteger;

/** Isolated SDK experiment. Never invoked by LocalLore gameplay. */
public final class SpikeInstrumentation extends Instrumentation {
    private String mode;
    private final AtomicBoolean finished = new AtomicBoolean();
    private final AtomicInteger pulses = new AtomicInteger();
    private final Handler main = new Handler(Looper.getMainLooper());
    private final JsonObject metrics = new JsonObject();
    private final Runnable pulse = new Runnable() {
        @Override public void run() {
            pulses.incrementAndGet();
            if (!finished.get()) main.postDelayed(this, 10);
        }
    };

    @Override public void onCreate(Bundle arguments) {
        super.onCreate(arguments);
        mode = arguments == null ? "" : arguments.getString("mode", "");
        // An independent watchdog still terminates this package if a native call blocks
        // the worker or Main and the host controller vanishes. This is abrupt death,
        // never evidence of cooperative cancellation or native resource disposal.
        Thread watchdog = new Thread(() -> {
            try { Thread.sleep(90000); } catch (InterruptedException ignored) { return; }
            if (!finished.get()) Process.killProcess(Process.myPid());
        }, "spike-death-watchdog");
        watchdog.setDaemon(true); watchdog.start();
        main.post(pulse);
        start();
    }

    @Override public void onStart() {
        JsonObject result = emptyResult("runtime_failed");
        metrics.addProperty("version", 1);
        metrics.addProperty("scope", "android_sdk_smoke_not_phone_qualification");
        metrics.addProperty("mode", allowedMode(mode) ? mode : "invalid");
        metrics.addProperty("worker_off_main", Looper.myLooper() != Looper.getMainLooper());
        metrics.addProperty("engines_opened", 0);
        metrics.addProperty("engines_closed", 0);
        metrics.addProperty("conversations_opened", 0);
        metrics.addProperty("conversations_closed", 0);
        metrics.addProperty("cancel_called", false);
        metrics.addProperty("terminal_callback", false);
        metrics.addProperty("reload_completed", false);
        metrics.addProperty("generated_text_logged", false);
        try (QuietDescriptors ignored = new QuietDescriptors()) {
            if (!allowedMode(mode)) throw new Failure("invalid_request");
            if (Looper.myLooper() == Looper.getMainLooper()) throw new Failure("runtime_failed");
            pulseCheck();
            Engine.Companion.setNativeMinLogSeverity(LogSeverity.INFINITY);
            ExperimentalFlags.INSTANCE.setEnableBenchmark(true);
            ExperimentalFlags.INSTANCE.setEnableSpeculativeDecoding(false);
            if (mode.equals("metadata")) result = metadata();
            else if (mode.equals("missing") || mode.equals("corrupt")) result = invalidModel();
            else {
                Request request = readRequest();
                result = generate(request, mode.equals("cancel"));
                if (mode.equals("cancel")) {
                    // A cancelled native conversation is never reused. Reload fresh owners.
                    Request reload = Request.parse(("{\"version\":1,\"role\":\"narrator\",\"prompt\":\"Reply with only the word Lantern.\",\"max_tokens\":8,\"context_tokens\":4096,\"threads\":4,\"schema\":null}").getBytes(StandardCharsets.UTF_8));
                    result = generate(reload, false);
                    metrics.addProperty("reload_completed", result.get("status").getAsString().equals("completed"));
                }
            }
            pulseCheck();
        } catch (Failure failure) { result = emptyResult(failure.category); }
        catch (UnsatisfiedLinkError | NoClassDefFoundError error) { result = emptyResult("runtime_unavailable"); }
        catch (Exception error) { result = emptyResult("runtime_failed"); }
        finished.set(true);
        main.removeCallbacks(pulse);
        metrics.addProperty("main_pulses", pulses.get());
        metrics.addProperty("owners_balanced", number("engines_opened") == number("engines_closed")
            && number("conversations_opened") == number("conversations_closed"));
        Bundle bundle = new Bundle();
        bundle.putString("result_base64", Base64.encodeToString(result.toString().getBytes(StandardCharsets.UTF_8), Base64.NO_WRAP));
        bundle.putString("metrics", metrics.toString());
        finish(Activity.RESULT_OK, bundle);
    }

    private boolean allowedMode(String value) {
        return value.equals("metadata") || value.equals("missing") || value.equals("corrupt")
            || value.equals("generate") || value.equals("cancel");
    }

    private File model() { return new File(getTargetContext().getFilesDir(), "gemma4-e2b.litertlm"); }

    private Request readRequest() throws Exception {
        File file = new File(getTargetContext().getFilesDir(), "request.json");
        try (FileInputStream input = new FileInputStream(file)) {
            byte[] bytes = new byte[32769]; int total = 0, count;
            while (total < bytes.length && (count = input.read(bytes, total, bytes.length - total)) != -1) total += count;
            return Request.parse(java.util.Arrays.copyOf(bytes, total));
        } catch (Exception error) { throw new Failure("invalid_request"); }
        finally { if (file.exists() && !file.delete()) metrics.addProperty("request_delete_failed", true); }
    }

    private JsonObject metadata() throws Exception {
        if (!model().isFile()) throw new Failure("model_missing");
        ModelInfo info = ModelInfo.from(model().getPath());
        metrics.addProperty("model_info_closed", false);
        try {
            metrics.addProperty("max_context_tokens", info.maxContextTokens());
            metrics.addProperty("dynamic_context", info.isDynamicContext());
            metrics.addProperty("cpu_text_supported", info.supportedBackends(Modality.TEXT).contains(BackendType.CPU));
            JsonObject value = emptyResult(null);
            value.addProperty("thinking_disabled", false);
            return value;
        } finally { info.close(); metrics.addProperty("model_info_closed", true); }
    }

    private JsonObject invalidModel() throws Exception {
        File path = new File(getTargetContext().getFilesDir(), mode.equals("missing") ? "absent-spike-model.litertlm" : "corrupt-spike-model.litertlm");
        if (mode.equals("missing") && path.exists()) throw new Failure("runtime_failed");
        if (mode.equals("corrupt")) try (FileOutputStream output = new FileOutputStream(path)) {
            output.write("LocalLore synthetic invalid model".getBytes(StandardCharsets.US_ASCII));
        }
        Engine engine = configuredEngine(path);
        try {
            engine.initialize(); increment("engines_opened");
            throw new Failure("unexpected_output");
        } catch (Failure failure) { throw failure; }
        catch (LiteRtLmJniException expected) {
            metrics.addProperty("native_invalid_model_rejected", true);
            return emptyResult(mode.equals("missing") ? "model_missing" : "model_invalid");
        } finally {
            if (engine.isInitialized()) { engine.close(); increment("engines_closed"); }
            if (mode.equals("corrupt") && path.exists() && !path.delete()) metrics.addProperty("corrupt_delete_failed", true);
        }
    }

    private Engine configuredEngine(File path) {
        return new Engine(new EngineConfig(path.getPath(), new Backend.CPU(4, null), null, null, 4096));
    }

    private JsonObject generate(Request request, boolean cancel) throws Exception {
        if (!model().isFile()) throw new Failure("model_missing");
        Engine engine = configuredEngine(model());
        Conversation conversation = null;
        boolean terminal = true;
        long began = System.nanoTime();
        JsonObject result = emptyResult(null);
        try {
            try { engine.initialize(); } catch (RuntimeException error) { throw new Failure("model_load_failed"); }
            increment("engines_opened");
            result.addProperty("load_ms", elapsed(began));
            ConversationConfig config = new ConversationConfig(null, Collections.emptyList(), Collections.emptyList(),
                new SamplerConfig(1, 1.0, 0.0, 1), false, null, Collections.emptyMap(), null, false,
                request.maxTokens, new ThinkingConfig(false, 0), request.schema != null, false, null);
            conversation = engine.createConversation(config); increment("conversations_opened");
            if (conversation.renderMessageIntoString(Message.Companion.user(request.prompt), Collections.emptyMap()).isEmpty()) throw new Failure("unsupported_template");
            result.addProperty("thinking_disabled", true);
            result.addProperty("template_applied", true);
            Stream stream = new Stream();
            ResponseFormat format = request.schema == null ? null : ResponseFormat.json(request.schema.toString());
            long generatedAt = System.nanoTime();
            int pulsesAtStart = pulses.get();
            terminal = false;
            conversation.sendMessageAsync(request.prompt, stream, Collections.emptyMap(), null, null, null,
                request.maxTokens, new ThinkingConfig(false, 0), format);
            if (cancel) {
                if (!stream.first.await(40, TimeUnit.SECONDS)) throw new Failure("timeout");
                if (stream.done.getCount() == 0) throw new Failure("unexpected_output");
                long cancelAt = System.nanoTime();
                conversation.cancelProcess();
                metrics.addProperty("cancel_called", true);
                metrics.addProperty("cancel_call_ms", elapsed(cancelAt));
            }
            if (!stream.done.await(55, TimeUnit.SECONDS)) throw new Failure("timeout");
            terminal = true;
            metrics.addProperty("terminal_callback", true);
            metrics.addProperty("generation_main_pulses", pulses.get() - pulsesAtStart);
            metrics.addProperty(cancel ? "cancel_terminal_callback" : "generate_terminal_callback", true);
            metrics.addProperty(cancel ? "cancel_main_pulses" : "generate_main_pulses", pulses.get() - pulsesAtStart);
            result.addProperty("generation_ms", elapsed(generatedAt));
            if (cancel) {
                metrics.addProperty("cancelled_text_discarded", true);
                return emptyResult("runtime_failed");
            }
            String text = stream.text();
            BenchmarkInfo info = conversation.getBenchmarkInfo();
            int input = info.getLastPrefillTokenCount(), output = info.getLastDecodeTokenCount();
            if (input <= 0 || output <= 0 || output > request.maxTokens || input + output > 4096) throw new Failure("context_overflow");
            result.addProperty("input_tokens", input); result.addProperty("output_tokens", output);
            result.addProperty("schema_enforced", request.schema != null);
            result.addProperty("text", text);
            return result;
        } finally {
            // Never delete a conversation while callbacks are still active. The independent
            // process watchdog/controller owns a timeout that could not drain cooperatively.
            if (terminal) {
                if (conversation != null && conversation.isAlive()) { conversation.close(); increment("conversations_closed"); }
                if (engine.isInitialized()) { engine.close(); increment("engines_closed"); }
            } else {
                metrics.addProperty("cleanup_requires_process_termination", true);
                Process.killProcess(Process.myPid());
            }
        }
    }

    private static final class Stream implements MessageCallback {
        final CountDownLatch first = new CountDownLatch(1), done = new CountDownLatch(1);
        private final StringBuilder output = new StringBuilder();
        private String error;
        private boolean ended;
        @Override public synchronized void onMessage(Message message) {
            if (ended) return;
            if (!message.getToolCalls().isEmpty()) { error = "unsupported_output"; return; }
            // Read SDK contents only; its separate channels map is never copied.
            // Per-item channel metadata is not exposed by this API; see source limitations.
            for (Content item : message.getContents().getContents()) {
                if (!(item instanceof Content.Text)) { error = "unsupported_output"; continue; }
                String text = ((Content.Text) item).getText();
                if (text.isEmpty()) continue;
                if (output.length() + text.length() > 16384
                    || (output.toString() + text).getBytes(StandardCharsets.UTF_8).length > 16384) {
                    error = "output_too_large"; continue;
                }
                output.append(text); first.countDown();
            }
        }
        @Override public synchronized void onDone() { ended = true; done.countDown(); first.countDown(); }
        @Override public synchronized void onError(Throwable ignored) { error = "generation_failed"; ended = true; done.countDown(); first.countDown(); }
        synchronized String text() throws Failure {
            if (error != null) throw new Failure(error);
            if (output.length() == 0) throw new Failure("unsupported_output");
            return output.toString();
        }
    }

    private void pulseCheck() throws Exception {
        CountDownLatch latch = new CountDownLatch(1); main.post(latch::countDown);
        if (!latch.await(2, TimeUnit.SECONDS)) throw new Failure("runtime_failed");
    }
    private int number(String field) { return metrics.get(field).getAsInt(); }
    private void increment(String field) { metrics.addProperty(field, number(field) + 1); }
    private static double elapsed(long start) { return Math.min(180000.0, (System.nanoTime() - start) / 1000000.0); }
    private static JsonObject emptyResult(String error) {
        JsonObject result = new JsonObject(); result.addProperty("version", 1);
        result.addProperty("status", error == null ? "completed" : "error"); result.addProperty("text", "");
        if (error == null) result.add("error", JsonNull.INSTANCE); else result.addProperty("error", error);
        for (String key : new String[]{"load_ms", "generation_ms", "output_tokens", "input_tokens"}) result.add(key, JsonNull.INSTANCE);
        for (String key : new String[]{"schema_enforced", "thinking_disabled", "template_applied"}) result.addProperty(key, false);
        return result;
    }
    private static final class Failure extends Exception {
        final String category;
        Failure(String category) { super(category); this.category = category; }
    }
    private static final class QuietDescriptors implements AutoCloseable {
        private FileDescriptor stdout, stderr;
        QuietDescriptors() throws Exception {
            try {
                System.out.flush(); System.err.flush();
                stdout = Os.dup(FileDescriptor.out);
                stderr = Os.dup(FileDescriptor.err);
                FileDescriptor sink = Os.open("/dev/null", OsConstants.O_WRONLY, 0);
                try { Os.dup2(sink, 1); Os.dup2(sink, 2); } finally { Os.close(sink); }
            } catch (Exception original) {
                try { close(); } catch (Exception ignored) { /* preserve the original failure */ }
                throw original;
            }
        }
        @Override public void close() throws Exception {
            System.out.flush(); System.err.flush();
            Exception failure = null;
            FileDescriptor[] saved = {stdout, stderr};
            stdout = null; stderr = null;
            for (int index = 0; index < saved.length; index++) {
                if (saved[index] == null) continue;
                try { Os.dup2(saved[index], index + 1); } catch (Exception error) { failure = error; }
                try { Os.close(saved[index]); } catch (Exception error) { failure = error; }
            }
            if (failure != null) throw failure;
        }
    }
}

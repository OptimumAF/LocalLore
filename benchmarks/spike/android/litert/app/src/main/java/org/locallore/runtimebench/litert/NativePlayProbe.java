// Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0
package org.locallore.runtimebench.litert;

import com.google.gson.JsonObject;
import com.google.gson.JsonParser;
import java.nio.ByteBuffer;
import java.nio.charset.CodingErrorAction;
import java.nio.charset.StandardCharsets;
import java.util.concurrent.atomic.AtomicLong;

/** Loaded only by the explicitly selected play experiment. Never a production backend. */
final class NativePlayProbe {
    static { System.loadLibrary("locallore_android"); }
    private NativePlayProbe() {}
    static native long open(String path, byte[] profileJson);
    static native byte[] call(long handle, byte[] hostEnvelope);
    static native byte[] poll(long handle);
    static native byte[] respond(long handle, long ticket, byte[] untrustedText);
    static native void close(long handle);

    static final class Adapter implements PlayRunner.Probe {
        private final String path;
        private final byte[] profile;
        private final AtomicLong handle = new AtomicLong();
        Adapter(String path, byte[] profile) throws Exception {
            if (profile.length == 0 || profile.length > 4096) throw Request.invalid();
            this.path = path; this.profile = profile.clone(); reopen();
        }
        @Override public JsonObject call(JsonObject command) throws Exception {
            JsonObject envelope = new JsonObject(); envelope.addProperty("version", 1); envelope.add("command", command);
            byte[] bytes = envelope.toString().getBytes(StandardCharsets.UTF_8);
            if (bytes.length > 24576) throw Request.invalid();
            return decode(NativePlayProbe.call(current(), bytes), 262144);
        }
        @Override public JsonObject poll() throws Exception { return decode(NativePlayProbe.poll(current()), 40000); }
        @Override public JsonObject respond(long ticket, byte[] text) throws Exception {
            if (ticket <= 0 || text.length == 0 || text.length > 16384) throw Request.invalid();
            return decode(NativePlayProbe.respond(current(), ticket, text), 40000);
        }
        @Override public void reopen() throws Exception {
            if (handle.get() != 0) throw Request.invalid();
            long opened = NativePlayProbe.open(path, profile);
            if (opened <= 0) throw new WarmRunner.Failure("runtime_failed");
            handle.set(opened);
        }
        @Override public void close() {
            long id = handle.getAndSet(0);
            if (id != 0) NativePlayProbe.close(id);
        }
        private long current() throws Exception {
            long id = handle.get(); if (id == 0) throw Request.invalid(); return id;
        }
        private static JsonObject decode(byte[] bytes, int cap) throws Exception {
            if (bytes == null || bytes.length == 0 || bytes.length > cap) throw Request.invalid();
            String text = StandardCharsets.UTF_8.newDecoder().onMalformedInput(CodingErrorAction.REPORT)
                .onUnmappableCharacter(CodingErrorAction.REPORT).decode(ByteBuffer.wrap(bytes)).toString();
            com.google.gson.JsonElement parsed = JsonParser.parseString(text);
            if (!parsed.isJsonObject()) throw Request.invalid();
            return parsed.getAsJsonObject();
        }
    }
}

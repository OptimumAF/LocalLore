// Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0
package org.locallore.runtimebench.litert;

import com.google.gson.JsonObject;
import com.google.gson.Strictness;
import com.google.gson.stream.JsonReader;
import com.google.gson.stream.JsonToken;
import java.io.IOException;
import java.io.StringReader;
import java.nio.ByteBuffer;
import java.nio.channels.FileChannel;
import java.nio.charset.CodingErrorAction;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.LinkOption;
import java.nio.file.Path;
import java.nio.file.StandardOpenOption;
import java.nio.file.attribute.BasicFileAttributes;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.Collections;
import java.util.HashMap;
import java.util.HashSet;
import java.util.List;
import java.util.Map;
import java.util.Objects;
import java.util.Set;

/** Bounded content-free process checkpoints, not a canonical ledger or power-loss guarantee. */
final class PhaseJournal implements PlayRunner.Checkpoints, AutoCloseable {
    static final String FILE = "sdk-phases-v1.jsonl";
    static final int MAX_ROWS = 96, MAX_BYTES = 65536;
    private static final Set<String> PHASES = new HashSet<>(Arrays.asList(
        "instrumentation_start", "probe_ready", "probe_kill", "terminal",
        "native_create_before", "native_create_after", "native_submit_before", "native_submit_after",
        "native_prepare_before", "native_prepare_after", "native_respond_before", "native_respond_after",
        "native_commit_before", "native_commit_after", "native_reopen_before", "native_reopen_after",
        "model_create_before", "model_create_after", "model_initialize_before", "model_initialize_after",
        "model_close_before", "model_close_after", "role_open_before", "role_open_after",
        "role_start_before", "role_start_after", "role_drain_before", "role_drain_after",
        "role_cancel_before", "role_cancel_after", "role_close_before", "role_close_after"));
    private static final Set<String> KEYS = new HashSet<>(Arrays.asList("version", "sequence", "session", "pid", "uid",
        "process_start_elapsed_ms", "capture_wall_ms", "capture_elapsed_ms", "phase", "role", "elapsed_ms", "wall_ms"));
    static final class OwnershipUnknown extends IOException {
        OwnershipUnknown() { super("phase_journal_ownership_unknown"); }
    }
    interface Clock { long wallMs(); long elapsedMs(); }
    static final class Identity {
        final long pid, uid, processStartElapsedMs, captureWallMs, captureElapsedMs;
        Identity(long pid, long uid, long processStartElapsedMs, long captureWallMs, long captureElapsedMs) {
            this.pid = pid; this.uid = uid; this.processStartElapsedMs = processStartElapsedMs;
            this.captureWallMs = captureWallMs; this.captureElapsedMs = captureElapsedMs;
        }
        private void validate() throws IOException {
            if (pid <= 0 || pid > Integer.MAX_VALUE || uid < 0 || uid > Integer.MAX_VALUE || processStartElapsedMs < 0
                    || captureWallMs <= 0 || captureElapsedMs < processStartElapsedMs) throw invalid();
        }
        private boolean same(Identity other) {
            return pid == other.pid && uid == other.uid && processStartElapsedMs == other.processStartElapsedMs
                && captureWallMs == other.captureWallMs && captureElapsedMs == other.captureElapsedMs;
        }
    }
    static final class Record {
        final long sequence, elapsedMs, wallMs;
        final String phase, role;
        Record(long sequence, String phase, String role, long elapsedMs, long wallMs) {
            this.sequence = sequence; this.phase = phase; this.role = role; this.elapsedMs = elapsedMs; this.wallMs = wallMs;
        }
    }
    static final class Snapshot {
        final Identity identity;
        final List<Record> records;
        Snapshot(Identity identity, List<Record> records) {
            this.identity = identity; this.records = Collections.unmodifiableList(new ArrayList<>(records));
        }
    }
    // Package-private I/O fault seam always wraps this constructor's real CREATE_NEW channel.
    interface IO {
        int write(FileChannel channel, ByteBuffer bytes) throws IOException;
        void force(FileChannel channel) throws IOException;
        void close(FileChannel channel) throws IOException;
    }
    private static final IO SYSTEM = new IO() {
        public int write(FileChannel channel, ByteBuffer bytes) throws IOException { return channel.write(bytes); }
        public void force(FileChannel channel) throws IOException { channel.force(true); }
        public void close(FileChannel channel) throws IOException { channel.close(); }
    };
    private final Path file;
    private final String session;
    private final Identity identity;
    private final Clock clock;
    private final IO io;
    private final FileChannel channel;
    private final Object fileKey;
    private long rows, bytes, previousElapsed;
    private boolean failed, closed;
    private OwnershipUnknown ownershipFailure;

    PhaseJournal(Path parent, String session, Identity identity, Clock clock) throws IOException {
        this(parent, session, identity, clock, SYSTEM);
    }
    PhaseJournal(Path parent, String session, Identity identity, Clock clock, IO io) throws IOException {
        if (session == null || !session.matches("[a-f0-9]{32}") || identity == null || clock == null || io == null) throw invalid();
        try { identity.validate(); realDirectory(parent); }
        catch (Exception failure) { throw invalid(); }
        this.file = parent.resolve(FILE); this.session = session; this.identity = identity; this.clock = clock; this.io = io;
        FileChannel opened = null;
        try {
            opened = FileChannel.open(file, StandardOpenOption.CREATE_NEW, StandardOpenOption.WRITE, LinkOption.NOFOLLOW_LINKS);
            BasicFileAttributes metadata = regular(file);
            this.fileKey = metadata.fileKey();
            this.channel = opened;
        } catch (Exception failure) {
            if (opened != null) try { io.close(opened); } catch (Exception cleanup) {
                OwnershipUnknown unknown = new OwnershipUnknown();
                unknown.addSuppressed(failure); unknown.addSuppressed(cleanup); throw unknown;
            }
            throw invalid();
        }
        previousElapsed = identity.captureElapsedMs;
    }
    @Override public synchronized void mark(String phase, String role) throws IOException {
        if (failed || closed) throw invalid();
        try {
            vocabulary(phase, role);
            long elapsed = clock.elapsedMs(), wall = clock.wallMs();
            if (elapsed < previousElapsed || wall <= 0 || rows >= MAX_ROWS) throw invalid();
            realDirectory(file.getParent());
            BasicFileAttributes metadata = regular(file);
            if (!Objects.equals(fileKey, metadata.fileKey()) || metadata.size() != bytes || channel.position() != bytes) throw invalid();
            JsonObject row = new JsonObject(); row.addProperty("version", 1); row.addProperty("sequence", rows + 1);
            row.addProperty("session", session); row.addProperty("pid", identity.pid); row.addProperty("uid", identity.uid);
            row.addProperty("process_start_elapsed_ms", identity.processStartElapsedMs); row.addProperty("capture_wall_ms", identity.captureWallMs);
            row.addProperty("capture_elapsed_ms", identity.captureElapsedMs); row.addProperty("phase", phase); row.addProperty("role", role);
            row.addProperty("elapsed_ms", elapsed); row.addProperty("wall_ms", wall);
            byte[] encoded = (row + "\n").getBytes(StandardCharsets.UTF_8);
            if (encoded.length > MAX_BYTES - bytes) throw invalid();
            ByteBuffer buffer = ByteBuffer.wrap(encoded);
            while (buffer.hasRemaining()) {
                int remaining = buffer.remaining(), count = io.write(channel, buffer);
                if (count <= 0 || remaining - buffer.remaining() != count) throw invalid();
            }
            io.force(channel); bytes += encoded.length; rows++; previousElapsed = elapsed;
        } catch (Exception failure) {
            failed = true; throw invalid();
        }
    }
    @Override public synchronized void close() throws IOException {
        if (ownershipFailure != null) throw ownershipFailure;
        if (closed) return;
        closed = true;
        try { io.close(channel); }
        catch (Exception failure) {
            failed = true; ownershipFailure = new OwnershipUnknown();
            ownershipFailure.addSuppressed(failure); throw ownershipFailure;
        }
    }
    static Snapshot read(Path parent, String session) throws IOException {
        try {
            if (session == null || !session.matches("[a-f0-9]{32}")) throw invalid();
            realDirectory(parent); Path file = parent.resolve(FILE); regular(file);
            ByteBuffer buffer = ByteBuffer.allocate(MAX_BYTES + 1);
            FileChannel input = FileChannel.open(file, StandardOpenOption.READ, LinkOption.NOFOLLOW_LINKS);
            Exception readFailure = null;
            try {
                while (buffer.hasRemaining()) { int count = input.read(buffer); if (count == -1) break; if (count == 0) throw invalid(); }
            } catch (Exception failure) { readFailure = failure; throw failure; }
            finally {
                try { input.close(); } catch (Exception failure) {
                    OwnershipUnknown unknown = new OwnershipUnknown(); unknown.addSuppressed(failure);
                    if (readFailure != null) unknown.addSuppressed(readFailure); throw unknown;
                }
            }
            buffer.flip();
            if (!buffer.hasRemaining() || buffer.remaining() > MAX_BYTES) throw invalid();
            String text = StandardCharsets.UTF_8.newDecoder().onMalformedInput(CodingErrorAction.REPORT)
                .onUnmappableCharacter(CodingErrorAction.REPORT).decode(buffer).toString();
            if (!text.endsWith("\n") || text.indexOf('\r') >= 0) throw invalid();
            String[] lines = text.substring(0, text.length() - 1).split("\n", -1);
            if (lines.length > MAX_ROWS) throw invalid();
            List<Record> records = new ArrayList<>(); Identity identity = null; long elapsed = 0;
            for (String line : lines) {
                Map<String, Object> fields = fields(line);
                Identity current = new Identity(number(fields, "pid"), number(fields, "uid"), number(fields, "process_start_elapsed_ms"),
                    number(fields, "capture_wall_ms"), number(fields, "capture_elapsed_ms")); current.validate();
                if (identity == null) { identity = current; elapsed = current.captureElapsedMs; }
                if (!identity.same(current) || number(fields, "version") != 1 || number(fields, "sequence") != records.size() + 1
                        || !session.equals(fields.get("session"))) throw invalid();
                String phase = (String) fields.get("phase"), role = (String) fields.get("role"); vocabulary(phase, role);
                long next = number(fields, "elapsed_ms"), wall = number(fields, "wall_ms");
                if (next < elapsed || wall <= 0) throw invalid(); elapsed = next;
                records.add(new Record(records.size() + 1, phase, role, next, wall));
            }
            return new Snapshot(identity, records);
        } catch (OwnershipUnknown failure) { throw failure; }
        catch (Exception failure) { throw invalid(); }
    }
    private static Map<String, Object> fields(String line) throws IOException {
        Map<String, Object> fields = new HashMap<>();
        try (JsonReader reader = new JsonReader(new StringReader(line))) {
            reader.setStrictness(Strictness.STRICT); reader.beginObject();
            while (reader.hasNext()) {
                String key = reader.nextName();
                if (!KEYS.contains(key) || fields.containsKey(key)) throw invalid();
                boolean string = key.equals("session") || key.equals("phase") || key.equals("role");
                if (reader.peek() != (string ? JsonToken.STRING : JsonToken.NUMBER)) throw invalid();
                String value = reader.nextString();
                if (string) fields.put(key, value);
                else {
                    if (!value.matches("0|[1-9][0-9]*")) throw invalid();
                    fields.put(key, Long.parseLong(value));
                }
            }
            reader.endObject();
            if (reader.peek() != JsonToken.END_DOCUMENT || !fields.keySet().equals(KEYS)) throw invalid();
        }
        return fields;
    }
    private static long number(Map<String, Object> values, String key) throws IOException {
        if (!(values.get(key) instanceof Long)) throw invalid(); return (Long) values.get(key);
    }
    private static void vocabulary(String phase, String role) throws IOException {
        if (!PHASES.contains(phase) || !("none".equals(role) || "director".equals(role) || "narrator".equals(role))) throw invalid();
        boolean generation = phase.startsWith("role_") || phase.startsWith("model_create_")
            || phase.startsWith("model_initialize_") || phase.startsWith("native_respond_");
        if (generation == "none".equals(role)) throw invalid();
    }
    private static void realDirectory(Path parent) throws IOException {
        if (parent == null || !parent.isAbsolute() || !parent.equals(parent.normalize()) || !parent.toRealPath().equals(parent)) throw invalid();
        for (Path path = parent; path != null; path = path.getParent()) {
            BasicFileAttributes metadata = Files.readAttributes(path, BasicFileAttributes.class, LinkOption.NOFOLLOW_LINKS);
            if (!metadata.isDirectory() || metadata.isSymbolicLink()) throw invalid();
        }
    }
    private static BasicFileAttributes regular(Path file) throws IOException {
        BasicFileAttributes metadata = Files.readAttributes(file, BasicFileAttributes.class, LinkOption.NOFOLLOW_LINKS);
        if (!metadata.isRegularFile() || metadata.isSymbolicLink()) throw invalid(); return metadata;
    }
    private static IOException invalid() { return new IOException("phase_journal_failed"); }
}

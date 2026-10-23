// Copyright 2026 LocalLore contributors.
// SPDX-License-Identifier: Apache-2.0
package org.locallore.runtimebench.litert;

import com.google.gson.JsonObject;
import java.io.File;
import java.io.IOException;
import java.io.InputStream;
import java.io.OutputStream;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.LinkOption;
import java.nio.file.Path;
import java.nio.file.StandardCopyOption;
import java.nio.file.StandardOpenOption;
import java.util.Arrays;
import java.util.HashMap;
import java.util.HashSet;
import java.util.Collections;
import java.util.Map;
import java.util.Set;

/** Private, bounded experiment IPC. The host supplies both prompts; this owns no canon. */
final class WarmExchange implements WarmRunner.Exchange {
    private static final LinkOption NOFOLLOW = LinkOption.NOFOLLOW_LINKS;
    private static final byte[] MARKER = "locallore-warm-v1".getBytes(StandardCharsets.US_ASCII);
    private static final Set<String> NAMES = Collections.unmodifiableSet(new HashSet<>(Arrays.asList("owner-v1", "cancel", "cancel.partial", "request-1.json", "request-2.json",
        "result-1.json", "result-2.json", "request-1.json.partial", "request-2.json.partial",
        "result-1.json.partial", "result-2.json.partial")));
    private final Path directory;
    private final String session;
    private final Map<String, byte[]> consumed = new HashMap<>();
    private int next = 1;
    private boolean publishedFirst;

    WarmExchange(File privateFiles, String token) throws IOException {
        if (token == null || !token.matches("[0-9a-f]{32}")) throw Request.invalid();
        session = token;
        Path base = privateFiles.getCanonicalFile().toPath();
        directory = base.resolve("warm-" + session);
        if (!directory.toFile().getCanonicalFile().toPath().equals(directory)) throw Request.invalid();
        check();
        if (exists("result-1.json") || exists("result-2.json") || exists("request-2.json")) throw Request.invalid();
    }

    @Override public void check() throws IOException {
        if (!Files.isDirectory(directory, NOFOLLOW) || Files.isSymbolicLink(directory)
            || !Arrays.equals(read("owner-v1", MARKER.length), MARKER)) throw Request.invalid();
        try (java.nio.file.DirectoryStream<Path> entries = Files.newDirectoryStream(directory)) {
            for (Path entry : entries) {
                String name = entry.getFileName().toString();
                if (!NAMES.contains(name) || !Files.isRegularFile(entry, NOFOLLOW)
                    || Files.isSymbolicLink(entry)) throw Request.invalid();
                long cap = name.startsWith("request-") ? 32768 : name.startsWith("result-") ? 131072
                    : name.startsWith("cancel") ? 0 : MARKER.length;
                if (Files.size(entry) > cap) throw Request.invalid();
            }
        }
        if (!publishedFirst && exists("request-2.json")) throw Request.invalid();
        for (String name : new String[]{"result-1.json", "result-2.json"})
            if (exists(name) && !consumed.containsKey(name)) throw Request.invalid();
        for (Map.Entry<String, byte[]> prior : consumed.entrySet()) {
            int cap = prior.getKey().startsWith("request-") ? 32768 : 131072;
            if (!Arrays.equals(read(prior.getKey(), cap), prior.getValue())) throw Request.invalid();
        }
    }

    @Override public boolean cancelled() throws IOException { check(); return exists("cancel"); }

    @Override public Request poll(int step) throws IOException {
        check();
        if (step != next || step < 1 || step > 2) throw Request.invalid();
        String name = "request-" + step + ".json";
        if (consumed.containsKey(name)) throw Request.invalid();
        if (!exists(name)) return null;
        byte[] bytes = read(name, 32768);
        Request request = Request.parse(bytes);
        if (!request.role.equals(step == 1 ? "director" : "narrator")) throw Request.invalid();
        consumed.put(name, bytes);
        return request;
    }

    @Override public void publish(int step, JsonObject result) throws IOException {
        check();
        if (step != next || step < 1 || step > 2 || !consumed.containsKey("request-" + step + ".json")) throw Request.invalid();
        String name = "result-" + step + ".json";
        if (exists(name) || exists(name + ".partial")) throw Request.invalid();
        JsonObject envelope = new JsonObject();
        envelope.addProperty("version", 1); envelope.addProperty("session", session);
        envelope.addProperty("step", step); envelope.add("result", result);
        byte[] bytes = envelope.toString().getBytes(StandardCharsets.UTF_8);
        if (bytes.length > 131072) throw Request.invalid();
        Path partial = directory.resolve(name + ".partial");
        try (OutputStream output = Files.newOutputStream(partial, StandardOpenOption.WRITE,
                StandardOpenOption.CREATE_NEW, NOFOLLOW)) { output.write(bytes); }
        // One SDK publisher, create-only partial, existing-final rejection. This controlled
        // same-UID host experiment does not promise protection from a racing hostile UID peer.
        if (exists(name)) throw Request.invalid();
        Files.move(partial, directory.resolve(name), StandardCopyOption.ATOMIC_MOVE);
        consumed.put(name, bytes);
        if (step == 1) publishedFirst = true;
        next++;
    }

    private boolean exists(String name) { return Files.exists(directory.resolve(name), NOFOLLOW); }
    private byte[] read(String name, int cap) throws IOException {
        Path path = directory.resolve(name);
        if (!Files.isRegularFile(path, NOFOLLOW) || Files.isSymbolicLink(path)) throw Request.invalid();
        try (InputStream input = Files.newInputStream(path, StandardOpenOption.READ, NOFOLLOW)) {
            byte[] bytes = new byte[cap + 1]; int total = 0, count;
            while (total < bytes.length && (count = input.read(bytes, total, bytes.length - total)) != -1) total += count;
            if (total > cap) throw Request.invalid();
            return Arrays.copyOf(bytes, total);
        }
    }
}

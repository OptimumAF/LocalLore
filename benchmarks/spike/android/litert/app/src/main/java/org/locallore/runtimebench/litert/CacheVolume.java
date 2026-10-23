// Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0
package org.locallore.runtimebench.litert;

import java.io.File;
import java.io.IOException;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.LinkOption;
import java.nio.file.Path;
import java.nio.file.StandardOpenOption;
import java.util.List;
import java.util.Arrays;

/** Pure selection/ownership contract. All actual paths originate in Android Context APIs. */
final class CacheVolume {
    static final String PACKAGE = "org.locallore.runtimebench.litert.cacheprobe";
    static final String MODEL = "gemma4-e2b.litertlm";
    static final long CACHE_MIN = 2L * 1024 * 1024 * 1024;
    static final long USERDATA_MIN = 1024L * 1024 * 1024 + 64L * 1024 * 1024;
    static final int PROBE_BYTES = 65536;
    private static final byte[] OWNER = "locallore-explicit-cache-probe-v1\n".getBytes(StandardCharsets.US_ASCII);

    static final class Problem extends IOException {
        final String category;
        Problem(String category) { super(category); this.category = category; }
    }
    static final class Candidate {
        final String uuid;
        final boolean mounted, primary, emulated, writable;
        final long device, free;
        final File cache, files;
        Candidate(String uuid, boolean mounted, boolean primary, boolean emulated,
                  boolean writable, long device, long free, File cache, File files) {
            this.uuid = uuid; this.mounted = mounted; this.primary = primary;
            this.emulated = emulated; this.writable = writable;
            this.device = device; this.free = free; this.cache = cache; this.files = files;
        }
    }
    static void request(String operation, String uuid, String session, String playCase, String profile)
            throws Problem {
        if (!Arrays.asList("inspect", "mmap", "play").contains(operation) || !uuid(uuid)
                || session == null || !session.matches("[a-f0-9]{32}")) throw new Problem("invalid_request");
        if (operation.equals("play")) {
            if (!Arrays.asList("gift", "dialogue", "unlearned", "spent", "cancel").contains(playCase)
                    || profile == null || profile.isEmpty() || profile.length() > 5464)
                throw new Problem("invalid_request");
        } else if (playCase != null || profile != null) throw new Problem("invalid_request");
    }
    static boolean uuid(String value) {
        return value != null && (value.matches("[a-fA-F0-9]{4}-[a-fA-F0-9]{4}")
            || value.matches("[a-fA-F0-9]{8}-[a-fA-F0-9]{4}-[a-fA-F0-9]{4}-[a-fA-F0-9]{4}-[a-fA-F0-9]{12}"));
    }
    static Candidate select(List<Candidate> candidates, String uuid, long userdataDevice) throws Problem {
        if (!uuid(uuid) || userdataDevice <= 0 || candidates.size() > 16) throw new Problem("volume_invalid");
        Candidate selected = null;
        for (Candidate candidate : candidates) {
            if (!uuid.equals(candidate.uuid)) continue;
            if (selected != null) throw new Problem("volume_ambiguous");
            selected = candidate;
        }
        if (selected == null) throw new Problem("volume_missing");
        if (!selected.mounted || selected.primary || selected.emulated || !selected.writable
                || selected.device <= 0 || selected.device == userdataDevice || selected.free < 0
                || selected.cache == null || selected.files == null) throw new Problem("volume_invalid");
        return selected;
    }
    static void capacity(Candidate candidate, long userdataFree) throws Problem {
        if (candidate.free < CACHE_MIN || userdataFree < USERDATA_MIN) throw new Problem("capacity_blocked");
    }
    static void stable(Candidate before, Candidate after, long userdataBefore, long userdataAfter) throws Problem {
        if (userdataBefore <= 0 || userdataBefore != userdataAfter || before.device != after.device
                || !before.uuid.equals(after.uuid) || !before.cache.equals(after.cache) || !before.files.equals(after.files))
            throw new Problem("volume_changed");
    }
    static Path realDirectory(File directory) throws IOException {
        Path path = directory.toPath().toAbsolutePath().normalize();
        // Detect linked ancestors too; this is a trusted app-owned path boundary, not a same-UID sandbox.
        for (Path cursor = path; cursor != null; cursor = cursor.getParent()) {
            if (!Files.isDirectory(cursor, LinkOption.NOFOLLOW_LINKS) || Files.isSymbolicLink(cursor))
                throw new Problem("path_invalid");
        }
        if (!path.toRealPath().equals(path)) throw new Problem("path_invalid");
        return path;
    }
    static Path freshSession(File cache, String session) throws IOException {
        if (session == null || !session.matches("[a-f0-9]{32}")) throw new Problem("invalid_request");
        Path parent = realDirectory(cache);
        Path directory = parent.resolve("locallore-cache-probe-v1-" + session);
        Files.createDirectory(directory); // Never adopt, truncate or remove a previous run.
        Files.write(directory.resolve("owner-v1"), OWNER, StandardOpenOption.CREATE_NEW, StandardOpenOption.WRITE);
        return directory;
    }
    static void owner(Path directory) throws IOException {
        realDirectory(directory.toFile());
        Path marker = directory.resolve("owner-v1");
        if (!Files.isRegularFile(marker, LinkOption.NOFOLLOW_LINKS) || Files.isSymbolicLink(marker)
                || Files.size(marker) != OWNER.length)
            throw new Problem("path_invalid");
        byte[] bytes = new byte[OWNER.length + 1]; int count = 0;
        try (java.nio.channels.SeekableByteChannel channel = Files.newByteChannel(marker,
                new java.util.HashSet<>(Arrays.asList(StandardOpenOption.READ, LinkOption.NOFOLLOW_LINKS)))) {
            java.nio.ByteBuffer buffer = java.nio.ByteBuffer.wrap(bytes);
            while (buffer.hasRemaining()) {
                int read = channel.read(buffer); if (read < 0) break;
                if (read == 0) throw new Problem("path_invalid"); count += read;
            }
        }
        if (count != OWNER.length || !Arrays.equals(Arrays.copyOf(bytes, count), OWNER)) throw new Problem("path_invalid");
    }
    static File model(Candidate candidate) throws IOException {
        Path parent = realDirectory(candidate.files);
        Path path = parent.resolve(MODEL);
        if (!Files.isRegularFile(path, LinkOption.NOFOLLOW_LINKS) || Files.isSymbolicLink(path))
            throw new Problem("model_missing");
        return path.toFile();
    }
    private CacheVolume() { }
}

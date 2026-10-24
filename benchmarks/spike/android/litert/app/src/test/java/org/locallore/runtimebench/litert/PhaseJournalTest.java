// Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0
package org.locallore.runtimebench.litert;

import static org.junit.Assert.*;
import java.io.IOException;
import java.nio.ByteBuffer;
import java.nio.channels.FileChannel;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.ArrayList;
import java.util.List;
import java.util.concurrent.atomic.AtomicLong;
import org.junit.Test;

public final class PhaseJournalTest {
    static final String SESSION = "a".repeat(32);
    static Path directory() throws IOException { return Files.createTempDirectory("phase-journal-synthetic-").toRealPath(); }
    static PhaseJournal.Identity identity() { return new PhaseJournal.Identity(123, 456, 10, 1000, 20); }
    static final class Clock implements PhaseJournal.Clock {
        final AtomicLong elapsed = new AtomicLong(20);
        long wall = 1000;
        public long elapsedMs() { return elapsed.getAndIncrement(); }
        public long wallMs() { return wall; }
    }
    static class IO implements PhaseJournal.IO {
        int writes, forces, closes;
        public int write(FileChannel channel, ByteBuffer bytes) throws IOException { writes++; return channel.write(bytes); }
        public void force(FileChannel channel) throws IOException { forces++; channel.force(true); }
        public void close(FileChannel channel) throws IOException { closes++; channel.close(); }
    }
    @Test public void realForcedRowsHaveExactIdentityAndImmutableTypedSnapshot() throws Exception {
        Path parent = directory(); Clock clock = new Clock(); IO io = new IO();
        try (PhaseJournal journal = new PhaseJournal(parent, SESSION, identity(), clock, io)) {
            assertEquals(0, Files.size(parent.resolve(PhaseJournal.FILE)));
            journal.mark("instrumentation_start", "none"); journal.mark("role_open_before", "director");
            assertEquals(2, io.forces);
            PhaseJournal.Snapshot read = PhaseJournal.read(parent, SESSION);
            assertEquals(123, read.identity.pid); assertEquals(456, read.identity.uid);
            assertEquals(10, read.identity.processStartElapsedMs); assertEquals(1000, read.identity.captureWallMs);
            assertEquals(20, read.identity.captureElapsedMs); assertEquals(2, read.records.size());
            assertEquals("role_open_before", read.records.get(1).phase); assertEquals("director", read.records.get(1).role);
            assertEquals(2, read.records.get(1).sequence); assertEquals(21, read.records.get(1).elapsedMs);
            assertThrows(UnsupportedOperationException.class, () -> read.records.clear());
        }
        assertEquals(1, io.closes);
        String text = new String(Files.readAllBytes(parent.resolve(PhaseJournal.FILE)), StandardCharsets.UTF_8);
        assertFalse(text.contains(parent.toString())); assertFalse(text.contains("prompt")); assertFalse(text.contains("error"));
    }
    @Test public void createNewRefusesExistingLeafAndInvalidIdentityWithoutOverwriting() throws Exception {
        Path parent = directory(); byte[] sentinel = "original-owner".getBytes(StandardCharsets.US_ASCII);
        Files.write(parent.resolve(PhaseJournal.FILE), sentinel);
        IOException existing = assertThrows(IOException.class, () -> new PhaseJournal(parent, SESSION, identity(), new Clock()));
        assertEquals("phase_journal_failed", existing.getMessage()); assertArrayEquals(sentinel, Files.readAllBytes(parent.resolve(PhaseJournal.FILE)));
        for (PhaseJournal.Identity bad : List.of(new PhaseJournal.Identity(0, 1, 0, 1, 0),
                new PhaseJournal.Identity(1, -1, 0, 1, 0), new PhaseJournal.Identity(1, 1, 21, 1, 20),
                new PhaseJournal.Identity(1, 1, 0, 0, 20))) {
            Path fresh = directory(); assertThrows(IOException.class, () -> new PhaseJournal(fresh, SESSION, bad, new Clock()));
            assertFalse(Files.exists(fresh.resolve(PhaseJournal.FILE)));
        }
        Path fresh = directory();
        assertThrows(IOException.class, () -> new PhaseJournal(fresh, "PRIVATE session", identity(), new Clock()));
        assertThrows(IOException.class, () -> new PhaseJournal(fresh.resolve("missing"), SESSION, identity(), new Clock()));
        assertThrows(IOException.class, () -> new PhaseJournal(fresh.resolve(".."), SESSION, identity(), new Clock()));
    }
    @Test public void vocabularyFailurePoisonsWithoutWritingAnyContent() throws Exception {
        for (String[] wrong : List.of(new String[]{"PRIVATE prompt", "none"}, new String[]{"probe_ready", "director"},
                new String[]{"role_start_before", "none"}, new String[]{"role_start_before", "PRIVATE NPC"})) {
            Path parent = directory(); IO io = new IO();
            try (PhaseJournal journal = new PhaseJournal(parent, SESSION, identity(), new Clock(), io)) {
                IOException error = assertThrows(IOException.class, () -> journal.mark(wrong[0], wrong[1]));
                assertEquals("phase_journal_failed", error.getMessage());
                assertThrows(IOException.class, () -> journal.mark("probe_ready", "none"));
                assertEquals(0, io.writes); assertEquals(0, Files.size(parent.resolve(PhaseJournal.FILE)));
            }
        }
    }
    @Test public void elapsedResetFailsButPositiveWallClockJumpsAreRetained() throws Exception {
        Path parent = directory(); Clock clock = new Clock();
        try (PhaseJournal journal = new PhaseJournal(parent, SESSION, identity(), clock)) {
            journal.mark("probe_ready", "none"); clock.wall = 5; journal.mark("probe_kill", "none");
            assertEquals(5, PhaseJournal.read(parent, SESSION).records.get(1).wallMs);
            clock.elapsed.set(0); assertThrows(IOException.class, () -> journal.mark("terminal", "none"));
            clock.elapsed.set(100); assertThrows(IOException.class, () -> journal.mark("terminal", "none"));
        }
    }
    @Test public void maximumNumericRowsFitRaisedByteBudgetAndNinetySixIsSticky() throws Exception {
        Path parent = directory(); long large = Long.MAX_VALUE - 1000;
        PhaseJournal.Identity identity = new PhaseJournal.Identity(Integer.MAX_VALUE, Integer.MAX_VALUE, large, Long.MAX_VALUE, large);
        PhaseJournal.Clock clock = new PhaseJournal.Clock() { public long wallMs() { return Long.MAX_VALUE; } public long elapsedMs() { return large; } };
        PhaseJournal journal = new PhaseJournal(parent, SESSION, identity, clock);
        for (int i = 0; i < 96; i++) journal.mark("model_initialize_before", "director");
        assertTrue(Files.size(parent.resolve(PhaseJournal.FILE)) > 32768);
        assertTrue(Files.size(parent.resolve(PhaseJournal.FILE)) <= 65536);
        assertEquals(96, PhaseJournal.read(parent, SESSION).records.size());
        assertThrows(IOException.class, () -> journal.mark("terminal", "none"));
        assertThrows(IOException.class, () -> journal.mark("probe_ready", "none")); journal.close(); journal.close();
    }
    @Test public void concurrentMarksAreSerializedAndForcedInSequence() throws Exception {
        Path parent = directory(); IO io = new IO();
        try (PhaseJournal journal = new PhaseJournal(parent, SESSION, identity(), new Clock(), io)) {
            List<Thread> threads = new ArrayList<>(); List<Throwable> failures = java.util.Collections.synchronizedList(new ArrayList<>());
            for (int t = 0; t < 4; t++) { Thread thread = new Thread(() -> { try {
                for (int i = 0; i < 12; i++) journal.mark("role_open_before", "director");
            } catch (Exception failure) { failures.add(failure); } }); threads.add(thread); thread.start(); }
            for (Thread thread : threads) { thread.join(3000); assertFalse(thread.isAlive()); }
            assertTrue(failures.isEmpty()); assertEquals(48, io.forces);
            PhaseJournal.Snapshot read = PhaseJournal.read(parent, SESSION); assertEquals(48, read.records.size());
            for (int i = 0; i < 48; i++) assertEquals(i + 1, read.records.get(i).sequence);
        }
    }
    @Test public void partialWriteAndForceFailuresRemainStickyAndPreserveEvidence() throws Exception {
        for (boolean partial : List.of(true, false)) {
            Path parent = directory(); IO io = new IO() {
                @Override public int write(FileChannel channel, ByteBuffer bytes) throws IOException {
                    if (!partial) return super.write(channel, bytes);
                    writes++; if (writes > 1) throw new IOException("PRIVATE io failure");
                    int limit = bytes.limit(); bytes.limit(bytes.position() + 7);
                    int count = channel.write(bytes); bytes.limit(limit); return count;
                }
                @Override public void force(FileChannel channel) throws IOException { forces++; throw new IOException("PRIVATE force"); }
            };
            try (PhaseJournal journal = new PhaseJournal(parent, SESSION, identity(), new Clock(), io)) {
                IOException error = assertThrows(IOException.class, () -> journal.mark("probe_ready", "none"));
                assertEquals("phase_journal_failed", error.getMessage()); int writes = io.writes;
                assertThrows(IOException.class, () -> journal.mark("probe_kill", "none")); assertEquals(writes, io.writes);
            }
            assertTrue(Files.size(parent.resolve(PhaseJournal.FILE)) > 0);
            if (partial) assertThrows(IOException.class, () -> PhaseJournal.read(parent, SESSION));
        }
    }
    @Test public void tryWithResourcesRetainsTypedUnknownAsSuppressedOnBodyFailure() throws Exception {
        IO io = new IO() { @Override public void close(FileChannel channel) throws IOException {
            super.close(channel); throw new IOException("PRIVATE close");
        } };
        IOException primary = new IOException("synthetic_primary");
        IOException caught = assertThrows(IOException.class, () -> {
            try (PhaseJournal journal = new PhaseJournal(directory(), SESSION, identity(), new Clock(), io)) {
                journal.mark("probe_ready", "none"); throw primary;
            }
        });
        assertSame(primary, caught); assertEquals(1, io.closes);
        assertTrue(caught.getSuppressed()[0] instanceof PhaseJournal.OwnershipUnknown);
    }
    @Test public void closeFailureIsFixedAndMarkAfterCloseCannotWrite() throws Exception {
        Path parent = directory(); IO io = new IO() { @Override public void close(FileChannel channel) throws IOException {
            super.close(channel); throw new IOException("PRIVATE close");
        } };
        PhaseJournal journal = new PhaseJournal(parent, SESSION, identity(), new Clock(), io);
        journal.mark("probe_ready", "none");
        PhaseJournal.OwnershipUnknown failure = assertThrows(PhaseJournal.OwnershipUnknown.class, journal::close);
        assertEquals("phase_journal_ownership_unknown", failure.getMessage());
        assertSame(failure, assertThrows(PhaseJournal.OwnershipUnknown.class, journal::close));
        assertEquals(1, io.closes); assertThrows(IOException.class, () -> journal.mark("probe_kill", "none"));
    }
    @Test public void readerRejectsDuplicateUnknownWrongTypeScopeIdentityAndOrdering() throws Exception {
        Path parent = directory();
        try (PhaseJournal journal = new PhaseJournal(parent, SESSION, identity(), new Clock())) {
            journal.mark("probe_ready", "none"); journal.mark("probe_kill", "none");
        }
        String valid = new String(Files.readAllBytes(parent.resolve(PhaseJournal.FILE)), StandardCharsets.UTF_8);
        for (String bad : List.of(valid.replace("\"version\":1", "\"version\":true"),
                valid.replace("\"version\":1", "\"version\":1,\"version\":1"), valid.replace("\"version\":1", "\"version\":1,\"PRIVATE\":0"),
                valid.replace(SESSION, "b".repeat(32)), valid.replace("probe_kill", "PRIVATE phase"),
                valid.replace("\"sequence\":2", "\"sequence\":1"), valid.replace("\"elapsed_ms\":21", "\"elapsed_ms\":19"),
                valid.replace("\"pid\":123", "\"pid\":0"), valid.replace("\"role\":\"none\"", "\"role\":\"narrator\""),
                valid.substring(0, valid.length() - 1), valid.replace("\n", "\r\n"), valid + "\n")) {
            Path badParent = directory(); Files.write(badParent.resolve(PhaseJournal.FILE), bad.getBytes(StandardCharsets.UTF_8));
            assertEquals("phase_journal_failed", assertThrows(IOException.class, () -> PhaseJournal.read(badParent, SESSION)).getMessage());
        }
        Path tooLarge = directory(); Files.write(tooLarge.resolve(PhaseJournal.FILE), new byte[65537]);
        assertThrows(IOException.class, () -> PhaseJournal.read(tooLarge, SESSION));
        Path empty = directory(); Files.write(empty.resolve(PhaseJournal.FILE), new byte[0]);
        assertThrows(IOException.class, () -> PhaseJournal.read(empty, SESSION));
    }
}

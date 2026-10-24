// Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0
package org.locallore.runtimebench.litert;

import static org.junit.Assert.*;
import com.google.gson.JsonObject;
import java.io.IOException;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.Arrays;
import java.util.HashSet;
import java.util.concurrent.atomic.AtomicInteger;
import org.junit.Test;

/** Real filesystem synthetic journals; no Android, SDK, model or SQLite execution. */
public final class SdkPhaseReadbackTest {
    private static final String SESSION = "b".repeat(32);
    private static final byte[] OWNER = "locallore-explicit-cache-probe-v1\n".getBytes(StandardCharsets.US_ASCII);
    private static final SdkPhaseReadback.Exit UNAVAILABLE = new SdkPhaseReadback.Exit(false, 0, 0, -1, -1);
    private Path directory() throws IOException {
        Path parent = Files.createTempDirectory("sdk-read-synthetic-").toRealPath();
        Path directory = Files.createDirectory(parent.resolve("locallore-cache-probe-v1-" + SESSION));
        Files.write(directory.resolve("owner-v1"), OWNER); return directory;
    }
    private void journal(Path directory, String... phases) throws Exception {
        try (PhaseJournal journal = new PhaseJournal(directory, SESSION, PhaseJournalTest.identity(), new PhaseJournalTest.Clock())) {
            for (String phase : phases) journal.mark(phase, phase.startsWith("role_") ? "director" : "none");
        }
    }
    private JsonObject read(Path directory) throws Exception { return SdkPhaseReadback.read(directory, SESSION, 100, identity -> UNAVAILABLE); }
    private void error(JsonObject result) {
        assertEquals(4, result.size()); assertEquals("error", result.get("status").getAsString());
        assertEquals("sdk_phase_read_failed", result.get("error").getAsString());
        assertFalse(result.get("model_execution").getAsBoolean());
    }
    @Test public void validSdkJournalReportsExactSanitizedShapeAndLeavesEveryByteUnchanged() throws Exception {
        Path directory = directory(); journal(directory, "instrumentation_start", "role_start_before", "role_drain_after");
        Path file = directory.resolve(PhaseJournal.FILE); byte[] before = Files.readAllBytes(file);
        JsonObject result = SdkPhaseReadback.read(directory, SESSION, 100, identity -> {
            assertEquals(123, identity.pid); assertEquals(10, identity.processStartElapsedMs);
            return new SdkPhaseReadback.Exit(true, 3, 1, 5, 9);
        });
        assertEquals(new HashSet<>(Arrays.asList("version", "status", "error", "model_execution", "journal_valid", "checkpoint_count",
            "last_phase", "last_role", "fresh_reader_process", "exit_history_available", "exit_records_examined",
            "exit_instance_matches", "exit_instance_matched", "exit_reason", "exit_status")), result.keySet());
        assertEquals("completed", result.get("status").getAsString()); assertEquals(3, result.get("checkpoint_count").getAsInt());
        assertEquals("role_drain_after", result.get("last_phase").getAsString()); assertEquals("director", result.get("last_role").getAsString());
        assertTrue(result.get("fresh_reader_process").getAsBoolean()); assertTrue(result.get("exit_instance_matched").getAsBoolean());
        assertFalse(result.toString().contains(SESSION)); assertFalse(result.toString().contains(directory.toString()));
        assertFalse(result.has("pid")); assertArrayEquals(before, Files.readAllBytes(file));
        assertArrayEquals(OWNER, Files.readAllBytes(directory.resolve("owner-v1")));
        try (java.util.stream.Stream<Path> leaves = Files.list(directory)) { assertEquals(2, leaves.count()); }
    }
    @Test public void processStartIsObservationAndUnavailableExitDoesNotEraseValidJournal() throws Exception {
        Path directory = directory(); journal(directory, "instrumentation_start", "native_commit_after", "terminal");
        for (long start : new long[] {0, 9, 10, 11}) {
            JsonObject result = SdkPhaseReadback.read(directory, SESSION, start, identity -> UNAVAILABLE);
            assertEquals("completed", result.get("status").getAsString()); assertTrue(result.get("journal_valid").getAsBoolean());
            assertEquals(start > 10, result.get("fresh_reader_process").getAsBoolean());
            assertFalse(result.get("exit_history_available").getAsBoolean()); assertEquals(-1, result.get("exit_reason").getAsInt());
        }
        JsonObject failedQuery = SdkPhaseReadback.read(directory, SESSION, 100, identity -> { throw new IOException("PRIVATE query"); });
        assertEquals("completed", failedQuery.get("status").getAsString()); assertTrue(failedQuery.get("journal_valid").getAsBoolean());
        assertFalse(failedQuery.toString().contains("PRIVATE"));
    }
    @Test public void nonSdkAndProbeContaminatedJournalsAreRefusedBeforeExitQuery() throws Exception {
        for (String[] phases : new String[][] {{"probe_ready", "probe_kill"}, {"native_create_before"},
                {"instrumentation_start", "probe_ready"}, {"instrumentation_start", "probe_kill"}}) {
            Path directory = directory(); journal(directory, phases); AtomicInteger calls = new AtomicInteger();
            error(SdkPhaseReadback.read(directory, SESSION, 100, identity -> { calls.incrementAndGet(); return UNAVAILABLE; }));
            assertEquals(0, calls.get());
        }
    }
    @Test public void nonceNamespaceAndMissingOwnerCannotCreateOrAdoptSession() throws Exception {
        Path directory = directory(); journal(directory, "instrumentation_start");
        for (String bad : new String[] {"", "B".repeat(32), "b".repeat(31), "../" + SESSION, "c".repeat(32)})
            error(SdkPhaseReadback.read(directory, bad, 100, identity -> UNAVAILABLE));
        error(SdkPhaseReadback.read(directory, SESSION, -1, identity -> UNAVAILABLE));
        Path missing = directory.getParent().resolve("missing"); error(read(missing)); assertFalse(Files.exists(missing));
        Files.delete(directory.resolve("owner-v1")); error(read(directory)); assertFalse(Files.exists(directory.resolve("owner-v1")));
    }
    @Test public void linkedSessionAncestorIsRefusedWithoutTouchingTheRealJournal() throws Exception {
        Path directory = directory(); journal(directory, "instrumentation_start");
        byte[] before = Files.readAllBytes(directory.resolve(PhaseJournal.FILE));
        Path alias = directory.getParent().resolve("synthetic-linked-parent");
        if (System.getProperty("os.name").startsWith("Windows")) {
            Path commandLog = directory.getParent().resolve("junction-command.log");
            Process child = new ProcessBuilder("cmd.exe", "/d", "/c", "mklink /J \"" + alias + "\" \"" + directory.getParent() + "\"")
                .redirectErrorStream(true).redirectOutput(commandLog.toFile()).start();
            try {
                child.getOutputStream().close();
                assertTrue("synthetic junction creation timed out", child.waitFor(3, java.util.concurrent.TimeUnit.SECONDS));
                assertEquals("synthetic junction creation failed", 0, child.exitValue());
            } finally {
                if (child.isAlive()) { child.destroyForcibly(); assertTrue(child.waitFor(3, java.util.concurrent.TimeUnit.SECONDS)); }
            }
        } else Files.createSymbolicLink(alias, directory.getParent());
        assertTrue(Files.isDirectory(alias));
        assertEquals(directory.getParent(), alias.toRealPath());
        error(read(alias.resolve(directory.getFileName())));
        assertArrayEquals(before, Files.readAllBytes(directory.resolve(PhaseJournal.FILE)));
    }
    @Test public void markerWrongOversizedAndDirectoryLeavesAreRefused() throws Exception {
        for (byte[] bad : new byte[][] {new byte[0], "PRIVATE wrong owner".getBytes(StandardCharsets.UTF_8), Arrays.copyOf(OWNER, 35)}) {
            Path directory = directory(); journal(directory, "instrumentation_start"); Files.write(directory.resolve("owner-v1"), bad); error(read(directory));
        }
        Path directory = directory(); journal(directory, "instrumentation_start"); Files.delete(directory.resolve("owner-v1"));
        Files.createDirectory(directory.resolve("owner-v1")); error(read(directory));
    }
    @Test public void tornOversizedAndMalformedJournalsNeverPublishPartialObservation() throws Exception {
        for (int mode = 0; mode < 4; mode++) {
            Path directory = directory(); journal(directory, "instrumentation_start", "role_start_before");
            Path file = directory.resolve(PhaseJournal.FILE); byte[] original = Files.readAllBytes(file);
            byte[] bad = mode == 0 ? Arrays.copyOf(original, original.length - 1) : mode == 1 ? new byte[65537]
                : mode == 2 ? "PRIVATE invalid journal".getBytes(StandardCharsets.UTF_8) : new byte[0];
            Files.write(file, bad); error(read(directory)); assertArrayEquals(bad, Files.readAllBytes(file));
        }
    }
    @Test public void malformedExitObservationResetsAllPartialFieldsAndOwnerDriftRefusesPublication() throws Exception {
        for (SdkPhaseReadback.Exit bad : Arrays.asList(new SdkPhaseReadback.Exit(false, 1, 0, -1, -1),
                new SdkPhaseReadback.Exit(true, 17, 0, -1, -1), new SdkPhaseReadback.Exit(true, 1, 2, -1, -1),
                new SdkPhaseReadback.Exit(true, 1, 1, -1, 0), new SdkPhaseReadback.Exit(true, 1, 0, 5, 0))) {
            Path directory = directory(); journal(directory, "instrumentation_start");
            error(SdkPhaseReadback.read(directory, SESSION, 100, identity -> bad));
        }
        Path directory = directory(); journal(directory, "instrumentation_start");
        error(SdkPhaseReadback.read(directory, SESSION, 100, identity -> {
            Files.write(directory.resolve("owner-v1"), "PRIVATE changed".getBytes(StandardCharsets.UTF_8)); return UNAVAILABLE;
        }));
    }
    @Test public void directAndSuppressedOwnershipUncertaintyCannotBecomeAnErrorReceipt() throws Exception {
        for (boolean suppressed : new boolean[] {false, true}) {
            Path directory = directory(); journal(directory, "instrumentation_start");
            PhaseJournal.OwnershipUnknown unknown = new PhaseJournal.OwnershipUnknown();
            PhaseJournal.OwnershipUnknown observed = assertThrows(PhaseJournal.OwnershipUnknown.class,
                () -> SdkPhaseReadback.read(directory, SESSION, 100, identity -> {
                    if (!suppressed) throw unknown;
                    IOException primary = new IOException("PRIVATE body"); primary.addSuppressed(unknown); throw primary;
                }));
            assertTrue(PhaseFailure.journalOwnershipUnknown(observed));
        }
    }
}

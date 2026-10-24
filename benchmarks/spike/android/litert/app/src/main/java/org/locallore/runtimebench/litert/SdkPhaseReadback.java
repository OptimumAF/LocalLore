// Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0
package org.locallore.runtimebench.litert;

import com.google.gson.JsonObject;
import java.io.IOException;
import java.nio.ByteBuffer;
import java.nio.channels.FileChannel;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.LinkOption;
import java.nio.file.Path;
import java.nio.file.StandardOpenOption;
import java.util.Arrays;

/** Reads only an existing private SDK journal; never opens a model, SDK or canonical store. */
final class SdkPhaseReadback {
    private static final byte[] OWNER = "locallore-explicit-cache-probe-v1\n".getBytes(StandardCharsets.US_ASCII);
    interface ExitObservation { Exit observe(PhaseJournal.Identity identity) throws Exception; }
    static final class Exit {
        final boolean available;
        final int examined, matches, reason, status;
        Exit(boolean available, int examined, int matches, int reason, int status) {
            this.available = available; this.examined = examined; this.matches = matches;
            this.reason = reason; this.status = status;
        }
        private void validate() throws IOException {
            if (examined < 0 || examined > 16 || matches < 0 || matches > examined
                    || (!available && (examined != 0 || matches != 0))
                    || (matches == 1 ? reason < 0 || status < 0 : reason != -1 || status != -1)) throw invalid();
        }
    }
    private SdkPhaseReadback() {}
    static JsonObject read(Path directory, String session, long readerStartElapsedMs, ExitObservation exits)
            throws PhaseJournal.OwnershipUnknown {
        try {
            if (session == null || !session.matches("[a-f0-9]{32}") || readerStartElapsedMs < 0 || exits == null
                    || directory == null || directory.getFileName() == null
                    || !directory.getFileName().toString().equals("locallore-cache-probe-v1-" + session)) throw invalid();
            owner(directory);
            PhaseJournal.Snapshot snapshot = PhaseJournal.read(directory, session);
            if (snapshot.records.isEmpty() || !snapshot.records.get(0).phase.equals("instrumentation_start")
                    || !snapshot.records.get(0).role.equals("none")) throw invalid();
            for (PhaseJournal.Record row : snapshot.records)
                if (row.phase.equals("probe_ready") || row.phase.equals("probe_kill")) throw invalid();
            Exit exit;
            try { exit = exits.observe(snapshot.identity); }
            catch (Exception failure) {
                if (PhaseFailure.journalOwnershipUnknown(failure)) throw failure;
                exit = new Exit(false, 0, 0, -1, -1);
            }
            if (exit == null) throw invalid(); exit.validate();
            // Revalidate the fixed namespace after reading and before publishing observations.
            owner(directory);
            PhaseJournal.Record last = snapshot.records.get(snapshot.records.size() - 1);
            JsonObject result = new JsonObject(); result.addProperty("version", 1);
            result.addProperty("status", "completed"); result.addProperty("error", "none");
            result.addProperty("model_execution", false); result.addProperty("journal_valid", true);
            result.addProperty("checkpoint_count", snapshot.records.size());
            result.addProperty("last_phase", last.phase); result.addProperty("last_role", last.role);
            result.addProperty("fresh_reader_process", readerStartElapsedMs > snapshot.identity.processStartElapsedMs);
            result.addProperty("exit_history_available", exit.available); result.addProperty("exit_records_examined", exit.examined);
            result.addProperty("exit_instance_matches", exit.matches); result.addProperty("exit_instance_matched", exit.matches == 1);
            result.addProperty("exit_reason", exit.reason); result.addProperty("exit_status", exit.status); return result;
        } catch (Exception failure) {
            if (PhaseFailure.journalOwnershipUnknown(failure)) {
                if (failure instanceof PhaseJournal.OwnershipUnknown) throw (PhaseJournal.OwnershipUnknown) failure;
                PhaseJournal.OwnershipUnknown unknown = new PhaseJournal.OwnershipUnknown();
                unknown.addSuppressed(failure); throw unknown;
            }
            return error();
        }
    }
    static JsonObject error() {
        JsonObject error = new JsonObject(); error.addProperty("version", 1); error.addProperty("status", "error");
        error.addProperty("error", "sdk_phase_read_failed"); error.addProperty("model_execution", false); return error;
    }
    private static void owner(Path directory) throws IOException {
        if (!directory.isAbsolute() || !directory.equals(directory.normalize()) || !directory.toRealPath().equals(directory)) throw invalid();
        for (Path cursor = directory; cursor != null; cursor = cursor.getParent())
            if (!Files.isDirectory(cursor, LinkOption.NOFOLLOW_LINKS) || Files.isSymbolicLink(cursor)) throw invalid();
        Path marker = directory.resolve("owner-v1");
        if (!Files.isRegularFile(marker, LinkOption.NOFOLLOW_LINKS) || Files.isSymbolicLink(marker)
                || Files.size(marker) != OWNER.length) throw invalid();
        ByteBuffer bytes = ByteBuffer.allocate(OWNER.length + 1);
        FileChannel input = FileChannel.open(marker, StandardOpenOption.READ, LinkOption.NOFOLLOW_LINKS);
        Exception primary = null;
        try {
            while (bytes.hasRemaining()) { int count = input.read(bytes); if (count < 0) break; if (count == 0) throw invalid(); }
        } catch (Exception failure) { primary = failure; throw failure; }
        finally {
            try { input.close(); } catch (Exception failure) {
                PhaseJournal.OwnershipUnknown unknown = new PhaseJournal.OwnershipUnknown(); unknown.addSuppressed(failure);
                if (primary != null) unknown.addSuppressed(primary); throw unknown;
            }
        }
        if (bytes.position() != OWNER.length || !Arrays.equals(OWNER, Arrays.copyOf(bytes.array(), bytes.position()))) throw invalid();
    }
    private static IOException invalid() { return new IOException("sdk_phase_read_failed"); }
}

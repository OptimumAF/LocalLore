// Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0
package org.locallore.runtimebench.litert;

import android.app.Activity;
import android.app.Instrumentation;
import android.os.Bundle;
import android.os.Looper;
import android.os.Process;
import com.google.gson.JsonObject;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.LinkOption;
import java.nio.file.Path;
import java.nio.file.StandardOpenOption;
import java.util.Arrays;

/** Separate deterministic no-model runner. Never opens SDK, model, volume or SQLite. */
public final class PhaseEvidenceInstrumentation extends Instrumentation {
    static final String PACKAGE = "org.locallore.runtimebench.litert.phaseprobe";
    private static final byte[] OWNER = "locallore-sdk-phase-v1\n".getBytes(StandardCharsets.US_ASCII);
    private String operation, session;
    @Override public void onCreate(Bundle arguments) {
        super.onCreate(arguments);
        Bundle args = arguments == null ? new Bundle() : arguments;
        operation = args.getString("operation", ""); session = args.getString("session", ""); start();
    }
    @Override public void onStart() {
        JsonObject report = new JsonObject(); report.addProperty("version", 1);
        report.addProperty("status", "error"); report.addProperty("error", "phase_probe_failed");
        report.addProperty("model_execution", false);
        try {
            if (!PACKAGE.equals(getTargetContext().getPackageName()) || Looper.myLooper() == Looper.getMainLooper()
                    || !session.matches("[a-f0-9]{32}") || !(operation.equals("crash") || operation.equals("read")))
                throw new IllegalArgumentException("invalid_request");
            Path parent = getTargetContext().getNoBackupFilesDir().getCanonicalFile().toPath();
            realDirectory(parent);
            Path directory = parent.resolve("locallore-sdk-phase-v1-" + session);
            if (operation.equals("crash")) {
                Files.createDirectory(directory);
                Files.write(directory.resolve("owner-v1"), OWNER, StandardOpenOption.CREATE_NEW, StandardOpenOption.WRITE);
                PhaseJournal.Identity identity = PhaseAndroidEvidence.identity();
                try (PhaseJournal journal = new PhaseJournal(directory, session, identity, PhaseAndroidEvidence.clock())) {
                    journal.mark("probe_ready", "none");
                    PhaseAndroidEvidence.publishSummary(getTargetContext(), session, identity);
                    journal.mark("probe_kill", "none");
                    // This is a deliberate diagnostic process death, never a successful SDK owner close.
                    Process.killProcess(Process.myPid());
                    throw new IllegalStateException("kill_returned");
                }
            }
            realDirectory(directory);
            Path marker = directory.resolve("owner-v1");
            if (!Files.isRegularFile(marker, LinkOption.NOFOLLOW_LINKS) || Files.isSymbolicLink(marker)
                    || Files.size(marker) != OWNER.length || !Arrays.equals(Files.readAllBytes(marker), OWNER))
                throw new IllegalArgumentException("invalid_owner");
            PhaseJournal.Snapshot snapshot = PhaseJournal.read(directory, session);
            report.addProperty("journal_valid", true);
            report.addProperty("checkpoint_count", snapshot.records.size());
            PhaseJournal.Record last = snapshot.records.get(snapshot.records.size() - 1);
            report.addProperty("last_phase", last.phase); report.addProperty("last_role", last.role);
            report.addProperty("fresh_reader_process", Process.getStartElapsedRealtime() > snapshot.identity.processStartElapsedMs);
            PhaseAndroidEvidence.addExitObservation(getTargetContext(), session, snapshot.identity, report);
            report.addProperty("status", "completed"); report.addProperty("error", "none");
        } catch (PhaseJournal.OwnershipUnknown unknown) {
            Process.killProcess(Process.myPid()); return;
        } catch (Exception failure) {
            if (PhaseFailure.journalOwnershipUnknown(failure)) { Process.killProcess(Process.myPid()); return; }
            // Fixed category; no path, nonce, PID, SDK text or exception prose.
        }
        Bundle result = new Bundle(); result.putString("phase_result", report.toString());
        finish(Activity.RESULT_OK, result);
    }
    private static void realDirectory(Path path) throws Exception {
        for (Path cursor = path; cursor != null; cursor = cursor.getParent())
            if (!Files.isDirectory(cursor, LinkOption.NOFOLLOW_LINKS) || Files.isSymbolicLink(cursor))
                throw new IllegalArgumentException("invalid_directory");
        if (!path.toRealPath().equals(path)) throw new IllegalArgumentException("invalid_directory");
    }
}

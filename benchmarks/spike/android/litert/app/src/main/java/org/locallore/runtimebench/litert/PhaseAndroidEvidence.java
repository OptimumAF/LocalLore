// Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0
package org.locallore.runtimebench.litert;

import android.app.ActivityManager;
import android.app.ApplicationExitInfo;
import android.content.Context;
import android.os.Build;
import android.os.Process;
import android.os.SystemClock;
import com.google.gson.JsonObject;
import java.util.List;

/** Android adapter only; checkpoints are private diagnostics, never canonical state. */
final class PhaseAndroidEvidence {
    private PhaseAndroidEvidence() {}
    static PhaseJournal.Identity identity() {
        return new PhaseJournal.Identity(Process.myPid(), Process.myUid(), Process.getStartElapsedRealtime(),
            System.currentTimeMillis(), SystemClock.elapsedRealtime());
    }
    static PhaseJournal.Clock clock() {
        return new PhaseJournal.Clock() {
            @Override public long wallMs() { return System.currentTimeMillis(); }
            @Override public long elapsedMs() { return SystemClock.elapsedRealtime(); }
        };
    }
    static boolean publishSummary(Context context, String session, PhaseJournal.Identity identity) {
        if (Build.VERSION.SDK_INT < 30) return false;
        ActivityManager manager = context.getSystemService(ActivityManager.class);
        if (manager == null) return false;
        try {
            manager.setProcessStateSummary(PhaseExitMatcher.summary(session, identity.processStartElapsedMs));
            return true;
        } catch (RuntimeException unavailable) { return false; }
    }
    static void addExitObservation(Context context, String session, PhaseJournal.Identity identity, JsonObject report) {
        report.addProperty("exit_history_available", false);
        report.addProperty("exit_records_examined", 0);
        report.addProperty("exit_instance_matches", 0);
        report.addProperty("exit_instance_matched", false);
        report.addProperty("exit_reason", -1); report.addProperty("exit_status", -1);
        if (Build.VERSION.SDK_INT < 30) return;
        ActivityManager manager = context.getSystemService(ActivityManager.class);
        if (manager == null) return;
        try {
            int pid = Math.toIntExact(identity.pid), uid = Math.toIntExact(identity.uid);
            List<ApplicationExitInfo> records = manager.getHistoricalProcessExitReasons(context.getPackageName(), pid, 16);
            if (records == null || records.size() > 16) return;
            report.addProperty("exit_history_available", true);
            report.addProperty("exit_records_examined", records.size());
            int count = 0, reason = -1, status = -1;
            byte[] expected = PhaseExitMatcher.summary(session, identity.processStartElapsedMs);
            for (ApplicationExitInfo record : records) {
                if (record != null && PhaseExitMatcher.matches(pid, uid, context.getPackageName(), expected,
                        record.getPid(), record.getPackageUid(), record.getProcessName(), record.getProcessStateSummary())) {
                    count++; reason = record.getReason(); status = record.getStatus();
                }
            }
            report.addProperty("exit_instance_matches", count);
            if (count == 1) {
                report.addProperty("exit_instance_matched", true);
                report.addProperty("exit_reason", reason); report.addProperty("exit_status", status);
            }
        } catch (RuntimeException unavailable) { /* An unavailable record is not evidence of a cause. */ }
    }
}

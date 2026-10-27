/* Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0 */
package org.locallore.app;

import android.os.Process;
import android.system.Os;
import android.system.StructStat;
import java.io.ByteArrayOutputStream;
import java.io.File;
import java.io.FileInputStream;
import java.nio.ByteBuffer;
import java.nio.channels.FileChannel;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.util.Collections;
import org.json.JSONArray;
import org.json.JSONObject;

/** Loaded only by the verified APK child loader, which also owns NativeArchive's library. */
public final class RetiredSelectionFixtureWorker {
    private RetiredSelectionFixtureWorker() { }
    private static void need(boolean condition) { RetiredSelectionFixtureMain.require(condition); }
    private static final String[] OPERATIONS = {"workspace", "branches", "resume", "create", "open", "play_snapshot",
        "free_text", "submit", "prepare", "commit", "cancel", "other"};

    public static String run(String[] args, String libraryHash, long entered) {
        String stage = "BUILD_IDENTITY";
        long workspace = 0, archive = 0;
        boolean workspaceClosed = true, archiveClosed = true;
        int attempts = 0;
        JSONObject before = null, after = null;
        String scopeHash = null;
        boolean passed = false;
        try {
            need(BuildConfig.INPUT_PROCESS_VERIFICATION && BuildConfig.APPLICATION_ID.equals(RetiredSelectionFixtureMain.PRODUCT));
            need(args.length == 11 && libraryHash.matches("[0-9a-f]{64}") && entered > 0);
            scopeHash = RetiredSelectionFixtureMain.sha(("1\n" + args[6] + "\n" + args[7] + "\n" + args[8]
                + "\n" + args[9] + "\n").getBytes(StandardCharsets.UTF_8));
            if (args[0].equals("load")) {
                stage = "LOAD_NATIVE";
                // This alone qualifies actual APK-contained JNI loading. Never open a database in load mode.
                NativeArchive.INSTANCE.close(0L);
                passed = true;
            } else {
                stage = "SAVED_OWNER";
                File home = RetiredSelectionFixtureMain.fixedHome();
                File backup = ownedChild(home, "no_backup", true);
                File proofRoot = ownedChild(backup, "process-verify-v1", true);
                File proofRun = ownedChild(proofRoot, args[1], true);
                File saved = ownedChild(proofRun, "saved.json", false);
                checkSaved(saved, args);
                requireOldGone(args);
                stage = "DATABASE_OWNER";
                File workspaceRoot = ownedChild(backup, "workspace-v1", true);
                File database = ownedChild(workspaceRoot, "stories.sqlite3", false);
                need(Os.lstat(database.getPath()).st_size > 0);
                File fixtureRoot = directory(backup, "retired-selection-fixture-v1");
                File runRoot = directory(fixtureRoot, args[1]);
                File staging = directory(runRoot, "staging");
                File intent = new File(runRoot, "retire-intent-v1.json");
                need(!Files.exists(intent.toPath(), java.nio.file.LinkOption.NOFOLLOW_LINKS));
                stage = "OPEN_WORKSPACE";
                workspace = NativeWorkspace.INSTANCE.open(database.getPath());
                need(workspace > 0); workspaceClosed = false;
                stage = "BEFORE_CATALOG";
                Catalog initial = catalog(workspace, args, true);
                before = state(true);
                stage = "OPEN_ARCHIVE";
                archive = NativeArchive.INSTANCE.open(database.getPath(), staging.getPath());
                need(archive > 0); archiveClosed = false;
                stage = "PREVIEW";
                byte[] request = new JSONObject().put("story", args[7]).put("branch", args[9])
                    .put("expected_revision", 1).toString().getBytes(StandardCharsets.UTF_8);
                BranchDeletionPrepared prepared = ArchiveNativeWire.INSTANCE.branchDeletionPrepared(
                    NativeArchive.INSTANCE.prepareBranchDelete(archive, request));
                BranchDeletionPreview p = prepared.getPreview();
                need(prepared.getToken() > 0 && p.getVersion() == 2 && p.getStoryId().equals(args[7])
                    && p.getBranchId().equals(args[9]) && p.getTitle().equals(initial.title)
                    && p.getRootBranch().equals(args[8]) && p.getExpectedRevision() == 1
                    && p.getRetainedDescendants().isEmpty() && p.getRetainedHeads().isEmpty()
                    && p.getRemovedBranches().equals(Collections.singletonList(args[9]))
                    && p.getRemovedRows().get("branches").equals(1L)
                    && p.getRemovedRows().get("turns").equals(0L)
                    && p.getRemovedCommittedTurns() == 0 && p.getRemovedNoncommittedTurns() == 0);
                if (args[0].equals("retire")) {
                    stage = "COMMIT_INTENT";
                    requireOldGone(args);
                    // A retained create-only marker forbids retry after any uncertain commit outcome.
                    byte[] marker = new JSONObject().put("version", 1).put("run_id", args[1])
                        .put("scope_sha256", scopeHash).toString().getBytes(StandardCharsets.UTF_8);
                    try (FileChannel out = FileChannel.open(intent.toPath(), java.nio.file.StandardOpenOption.CREATE_NEW,
                        java.nio.file.StandardOpenOption.WRITE)) {
                        ByteBuffer buffer = ByteBuffer.wrap(marker);
                        while (buffer.hasRemaining()) out.write(buffer);
                        out.force(true);
                    }
                    RetiredSelectionFixtureMain.owned(intent, false);
                    stage = "COMMIT";
                    attempts = 1;
                    BranchDeleted deleted = ArchiveNativeWire.INSTANCE.branchDeleted(
                        NativeArchive.INSTANCE.commitBranchDelete(archive, prepared.getToken()));
                    need(deleted.getStoryId().equals(args[7]) && deleted.getBranchId().equals(args[9])
                        && deleted.getRetainedThroughRevision() == null && deleted.getCollectedBranches() == 1
                        && deleted.getDeletedTurns() == 0
                        && deleted.getInvalidatedBranches().equals(Collections.singletonList(args[9])));
                }
                stage = "AFTER_CATALOG";
                catalog(workspace, args, !args[0].equals("retire"));
                after = state(!args[0].equals("retire"));
                if (args[0].equals("retire")) {
                    JSONObject rejected = exchange(workspace, new JSONObject().put("op", "resume")
                        .put("scope", new JSONObject().put("story", args[7]).put("branch", args[9])));
                    RetiredSelectionFixtureMain.keys(rejected, "version", "status", "error");
                    need(RetiredSelectionFixtureMain.number(rejected, "version") == 1
                        && RetiredSelectionFixtureMain.text(rejected, "status").equals("rejected")
                        && RetiredSelectionFixtureMain.text(rejected, "error").equals("NotFound"));
                }
                passed = true;
            }
        } catch (Throwable ignored) {
            passed = false;
        } finally {
            // A close failure suppresses success; attempt both independent owners regardless.
            if (archive > 0) {
                try { NativeArchive.INSTANCE.close(archive); archiveClosed = true; }
                catch (Throwable ignored) { passed = false; stage = "CLOSE_ARCHIVE"; }
            }
            if (workspace > 0) {
                try { NativeWorkspace.INSTANCE.close(workspace); workspaceClosed = true; }
                catch (Throwable ignored) { passed = false; stage = "CLOSE_WORKSPACE"; }
            }
        }
        if (!passed || !archiveClosed || !workspaceClosed) return RetiredSelectionFixtureMain.failure(args, stage);
        try {
            String terminal = args[0].equals("load") ? "LOAD_COMPLETE" : args[0].equals("probe") ? "PROBE_CLOSED" : "RETIRED_CLOSED";
            JSONObject proof = new JSONObject().put("version", 1).put("scope", RetiredSelectionFixtureMain.SCOPE)
                .put("mode", args[0]).put("run_id", args[1]).put("status", "passed").put("stage", terminal)
                .put("pid", Process.myPid()).put("uid", Process.myUid()).put("started_uptime_ms", entered)
                .put("product_sha256", args[3]).put("test_sha256", args[4]).put("library_sha256", libraryHash)
                .put("scope_sha256", scopeHash).put("commit_attempts", attempts)
                .put("archive_closed", archiveClosed).put("workspace_closed", workspaceClosed)
                .put("before", before == null ? JSONObject.NULL : before).put("after", after == null ? JSONObject.NULL : after);
            String result = proof.toString(); need(result.getBytes(StandardCharsets.UTF_8).length + 1 <= 4096); return result;
        } catch (Throwable ignored) { return RetiredSelectionFixtureMain.failure(args, "ENCODING"); }
    }

    private static File ownedChild(File parent, String leaf, boolean directory) throws Exception {
        File file = RetiredSelectionFixtureMain.owned(new File(parent, leaf), directory);
        need(file.getParentFile().equals(parent)); return file;
    }
    private static File directory(File parent, String leaf) throws Exception {
        File path = new File(parent, leaf);
        if (!Files.exists(path.toPath(), java.nio.file.LinkOption.NOFOLLOW_LINKS)) Files.createDirectory(path.toPath());
        return ownedChild(parent, leaf, true);
    }
    private static void requireOldGone(String[] args) {
        int pid = Integer.parseInt(args[10]);
        need(pid > 0 && pid != Process.myPid()
            && !Files.exists(new File("/proc/" + pid).toPath(), java.nio.file.LinkOption.NOFOLLOW_LINKS));
    }
    private static void checkSaved(File saved, String[] args) throws Exception {
        StructStat before = Os.lstat(saved.getPath()); need(before.st_size > 0 && before.st_size <= 4096);
        byte[] bytes;
        try (FileInputStream input = new FileInputStream(saved); ByteArrayOutputStream output = new ByteArrayOutputStream()) {
            StructStat held = Os.fstat(input.getFD()); need(held.st_dev == before.st_dev && held.st_ino == before.st_ino);
            byte[] buffer = new byte[1024]; int n;
            while ((n = input.read(buffer)) != -1) { need(output.size() + n <= 4096); output.write(buffer, 0, n); }
            bytes = output.toByteArray(); need(bytes.length == before.st_size);
            StructStat after = Os.fstat(input.getFD());
            need(after.st_size == before.st_size && after.st_mtime == before.st_mtime && after.st_ctime == before.st_ctime);
        }
        StructStat visible = Os.lstat(saved.getPath()); need(visible.st_dev == before.st_dev && visible.st_ino == before.st_ino
            && visible.st_size == before.st_size && visible.st_mtime == before.st_mtime && visible.st_ctime == before.st_ctime);
        JSONObject o = RetiredSelectionFixtureMain.json(bytes, 4096);
        RetiredSelectionFixtureMain.keys(o, "version", "scope", "run_id", "pid", "uid", "task_id", "sequence",
            "process_start_uptime_ms", "event", "restored_state", "factory_creations", "hint_present", "hint_sha256", "operations");
        need(RetiredSelectionFixtureMain.number(o, "version") == 1
            && RetiredSelectionFixtureMain.text(o, "scope").equals("locallore_process_verify_v1")
            && RetiredSelectionFixtureMain.text(o, "run_id").equals(args[1])
            && RetiredSelectionFixtureMain.number(o, "pid") == Integer.parseInt(args[10])
            && RetiredSelectionFixtureMain.number(o, "uid") == Process.myUid()
            && RetiredSelectionFixtureMain.text(o, "event").equals("saved_after_super")
            && RetiredSelectionFixtureMain.number(o, "factory_creations") == 1
            && RetiredSelectionFixtureMain.bool(o, "hint_present"));
        need(RetiredSelectionFixtureMain.number(o, "task_id") > 0 && RetiredSelectionFixtureMain.number(o, "sequence") > 0
            && RetiredSelectionFixtureMain.number(o, "sequence") <= 65536
            && RetiredSelectionFixtureMain.number(o, "process_start_uptime_ms") > 0);
        RetiredSelectionFixtureMain.bool(o, "restored_state");
        String hint = RetiredSelectionFixtureMain.sha(("1\n" + args[7] + "\n" + args[9] + "\n").getBytes(StandardCharsets.UTF_8));
        need(RetiredSelectionFixtureMain.text(o, "hint_sha256").equals(hint));
        Object raw = o.get("operations"); need(raw instanceof JSONObject); JSONObject ops = (JSONObject) raw;
        RetiredSelectionFixtureMain.keys(ops, OPERATIONS);
        for (String key : OPERATIONS) need(RetiredSelectionFixtureMain.number(ops, key) <= 4096);
        String[] game = {"free_text", "submit", "prepare", "commit", "cancel", "other"};
        int[] expected = {1, 0, 1, 1, 0, 2};
        for (int i = 0; i < game.length; i++) need(RetiredSelectionFixtureMain.number(ops, game[i]) == expected[i]);
    }

    private static JSONObject exchange(long handle, JSONObject command) throws Exception {
        byte[] input = new JSONObject().put("version", 1).put("command", command).toString().getBytes(StandardCharsets.UTF_8);
        need(input.length <= 4096);
        return RetiredSelectionFixtureMain.json(NativeWorkspace.INSTANCE.call(handle, input), 65536);
    }
    private static JSONObject call(long handle, JSONObject command) throws Exception {
        JSONObject reply = exchange(handle, command); RetiredSelectionFixtureMain.keys(reply, "version", "status", "data");
        need(RetiredSelectionFixtureMain.number(reply, "version") == 1 && RetiredSelectionFixtureMain.text(reply, "status").equals("ok"));
        Object data = reply.get("data"); need(data instanceof JSONObject); return (JSONObject) data;
    }
    private static JSONObject state(boolean active) throws Exception {
        return new JSONObject().put("other_head", 0).put("parent_head", 1)
            .put("target_head", active ? 1 : JSONObject.NULL).put("target_active", active);
    }
    private static final class Catalog { final String title; Catalog(String title) { this.title = title; } }
    private static Catalog catalog(long handle, String[] args, boolean targetPresent) throws Exception {
        JSONObject workspace = call(handle, new JSONObject().put("op", "workspace"));
        RetiredSelectionFixtureMain.keys(workspace, "persistent", "location", "schema_version", "database_schema_version", "stories");
        need(RetiredSelectionFixtureMain.bool(workspace, "persistent") && RetiredSelectionFixtureMain.number(workspace, "schema_version") == 1
            && RetiredSelectionFixtureMain.number(workspace, "database_schema_version") == 5);
        RetiredSelectionFixtureMain.text(workspace, "location");
        Object rows = workspace.get("stories"); need(rows instanceof JSONArray); JSONArray stories = (JSONArray) rows;
        need(stories.length() == 2); String title = null;
        for (int i = 0; i < 2; i++) {
            Object value = stories.get(i); need(value instanceof JSONObject); JSONObject row = (JSONObject) value;
            RetiredSelectionFixtureMain.keys(row, "scope", "title", "revision", "drafts");
            scope(row.getJSONObject("scope"), args[i + 6], args[8]);
            need(RetiredSelectionFixtureMain.number(row, "revision") == i && RetiredSelectionFixtureMain.number(row, "drafts") == 0);
            String t = RetiredSelectionFixtureMain.text(row, "title"); if (i == 1) title = t;
            branches(handle, args[i + 6], args[8], args[9], i, i == 1 && targetPresent, t);
        }
        return new Catalog(title);
    }
    private static void scope(JSONObject value, String story, String branch) throws Exception {
        RetiredSelectionFixtureMain.keys(value, "story", "branch");
        need(RetiredSelectionFixtureMain.text(value, "story").equals(story)
            && RetiredSelectionFixtureMain.text(value, "branch").equals(branch));
    }
    private static void branches(long handle, String story, String parent, String child, long head,
        boolean targetPresent, String title) throws Exception {
        JSONObject catalog = call(handle, new JSONObject().put("op", "branches").put("story", story));
        RetiredSelectionFixtureMain.keys(catalog, "version", "story_id", "title", "root_branch", "branches");
        need(RetiredSelectionFixtureMain.number(catalog, "version") == 2 && RetiredSelectionFixtureMain.text(catalog, "story_id").equals(story)
            && RetiredSelectionFixtureMain.text(catalog, "root_branch").equals(parent)
            && RetiredSelectionFixtureMain.text(catalog, "title").equals(title));
        Object values = catalog.get("branches"); need(values instanceof JSONArray); JSONArray rows = (JSONArray) values;
        need(rows.length() == (targetPresent ? 2 : 1)); String previous = "";
        for (int i = 0; i < rows.length(); i++) {
            Object value = rows.get(i); need(value instanceof JSONObject); JSONObject row = (JSONObject) value;
            RetiredSelectionFixtureMain.keys(row, "scope", "parent_branch", "fork_revision", "revision", "drafts", "retired");
            JSONObject s = row.getJSONObject("scope"); String branch = RetiredSelectionFixtureMain.text(s, "branch");
            scope(s, story, branch); need(previous.compareTo(branch) < 0); previous = branch;
            need(branch.equals(parent) || (targetPresent && branch.equals(child)));
            boolean root = branch.equals(parent);
            need(RetiredSelectionFixtureMain.number(row, "revision") == head
                && RetiredSelectionFixtureMain.number(row, "drafts") == 0 && !RetiredSelectionFixtureMain.bool(row, "retired"));
            if (root) need(row.isNull("parent_branch") && row.isNull("fork_revision"));
            else need(RetiredSelectionFixtureMain.text(row, "parent_branch").equals(parent)
                && RetiredSelectionFixtureMain.number(row, "fork_revision") == 1);
        }
    }
}

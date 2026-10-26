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
import java.nio.file.LinkOption;
import java.nio.file.StandardOpenOption;
import java.util.ArrayList;
import java.util.Collections;
import java.util.HashMap;
import java.util.Map;
import org.json.JSONArray;
import org.json.JSONObject;

/** Fixed synthetic parent retirement; Rust remains the only replay and mutation authority. */
public final class RetainedParentFixtureWorker {
    private static final int CAP = 262144;
    private static final String PRESERVED = "locallore_retained_parent_preserved_v1";
    private static final String ROOT_TEXT = "a8cb95c8145359ad7fadad52d0df311551fab161e1e386a66c87d29fa50a3a55";
    private static final String PREFIX = "d0e88260d20e867ca12440419d4c32fed67d07d9ef45da74251c0ab38869cc5a";
    private static final String[] SIDECARS = {"probe-before-v1.json", "probe-after-v1.json",
        "retire-before-v1.json", "retire-after-v1.json"};
    private static final String[] OPERATIONS = {"workspace", "branches", "resume", "create", "open", "play_snapshot",
        "free_text", "submit", "prepare", "commit", "cancel", "other", "story_template", "create_named"};
    private RetainedParentFixtureWorker() { }
    private static void need(boolean condition) { RetiredSelectionFixtureMain.require(condition); }

    public static String run(String[] args, String libraryHash, long entered) {
        String stage = "BUILD_IDENTITY";
        long workspace = 0, archive = 0;
        boolean workspaceClosed = true, archiveClosed = true, passed = false;
        int attempts = 0;
        String scopeHash = null;
        JSONObject before = null, after = null;
        try {
            need(BuildConfig.INPUT_PROCESS_VERIFICATION && BuildConfig.APPLICATION_ID.equals(RetiredSelectionFixtureMain.PRODUCT));
            need(args.length == 14 && args[12].equals("3") && args[13].equals("2")
                && libraryHash.matches("[0-9a-f]{64}") && entered > 0);
            scopeHash = RetiredSelectionFixtureMain.sha(("2\n" + args[6] + "\n" + args[7] + "\n" + args[8]
                + "\n" + args[9] + "\n" + args[11] + "\n3\n2\n").getBytes(StandardCharsets.UTF_8));
            if (args[0].equals("load")) {
                stage = "LOAD_NATIVE";
                NativeArchive.INSTANCE.close(0L); // No database, staging root or sidecar is opened in load mode.
                passed = true;
            } else {
                stage = "SAVED_OWNER";
                File home = RetiredSelectionFixtureMain.fixedHome();
                File backup = child(home, "no_backup", true);
                File saved = child(child(child(backup, "process-verify-v1", true), args[1], true), "saved.json", false);
                saved(saved, args);
                oldGone(args);
                stage = "DATABASE_OWNER";
                File database = child(child(backup, "workspace-v1", true), "stories.sqlite3", false);
                need(Os.lstat(database.getPath()).st_size > 0);
                File run = directory(directory(backup, "retained-parent-selection-fixture-v1"), args[1]);
                File staging = directory(run, "staging");
                File intent = new File(run, "retire-intent-v1.json");
                need(!Files.exists(intent.toPath(), LinkOption.NOFOLLOW_LINKS));
                aggregate(run);
                stage = "OPEN_WORKSPACE";
                workspace = NativeWorkspace.INSTANCE.open(database.getPath());
                need(workspace > 0); workspaceClosed = false;
                stage = "BEFORE_CATALOG";
                String title = catalog(workspace, args, false);
                stage = "BEFORE_PRESERVATION";
                byte[] original = capture(workspace, args);
                String preservedHash = RetiredSelectionFixtureMain.sha(original);
                if (args[0].equals("retire")) {
                    // The previous probe is data evidence only; a new native capability is prepared below.
                    need(preservedHash.equals(existingSidecar(run, SIDECARS[0], args))
                        && preservedHash.equals(existingSidecar(run, SIDECARS[1], args)));
                }
                writeSidecar(run, args[0] + "-before-v1.json", original);
                before = state(false, preservedHash);
                stage = "OPEN_ARCHIVE";
                archive = NativeArchive.INSTANCE.open(database.getPath(), staging.getPath());
                need(archive > 0); archiveClosed = false;
                stage = "PREVIEW";
                byte[] request = new JSONObject().put("story", args[7]).put("branch", args[9])
                    .put("expected_revision", 3).toString().getBytes(StandardCharsets.UTF_8);
                BranchDeletionPrepared prepared = ArchiveNativeWire.INSTANCE.branchDeletionPrepared(
                    NativeArchive.INSTANCE.prepareBranchDelete(archive, request));
                BranchDeletionPreview p = prepared.getPreview();
                need(prepared.getToken() > 0 && p.getVersion() == 2 && p.getStoryId().equals(args[7])
                    && p.getBranchId().equals(args[9]) && p.getTitle().equals(title) && p.getRootBranch().equals(args[8])
                    && p.getExpectedRevision() == 3 && p.getRetainedDescendants().equals(Collections.singletonMap(args[11], 2L))
                    && p.getRetainedHeads().equals(Collections.singletonMap(args[9], 2L))
                    && p.getRemovedBranches().isEmpty() && p.getRemovedRows().equals(removedRows())
                    && p.getRemovedCommittedTurns() == 1 && p.getRemovedNoncommittedTurns() == 0);
                if (args[0].equals("retire")) {
                    stage = "COMMIT_INTENT";
                    oldGone(args);
                    writeNew(intent, new JSONObject().put("version", 1).put("run_id", args[1])
                        .put("scope_sha256", scopeHash).toString().getBytes(StandardCharsets.UTF_8));
                    stage = "COMMIT";
                    attempts = 1;
                    BranchDeleted result = ArchiveNativeWire.INSTANCE.branchDeleted(
                        NativeArchive.INSTANCE.commitBranchDelete(archive, prepared.getToken()));
                    need(result.getStoryId().equals(args[7]) && result.getBranchId().equals(args[9])
                        && Long.valueOf(2).equals(result.getRetainedThroughRevision())
                        && result.getCollectedBranches() == 0 && result.getDeletedTurns() == 1
                        && result.getInvalidatedBranches().equals(Collections.singletonList(args[9])));
                }
                stage = "AFTER_CATALOG";
                boolean retired = args[0].equals("retire");
                need(catalog(workspace, args, retired).equals(title));
                stage = "AFTER_PRESERVATION";
                byte[] current = capture(workspace, args);
                String currentHash = RetiredSelectionFixtureMain.sha(current);
                need(java.util.Arrays.equals(original, current) && currentHash.equals(preservedHash));
                writeSidecar(run, args[0] + "-after-v1.json", current);
                after = state(retired, currentHash);
                if (retired) {
                    for (String leaf : SIDECARS) need(existingSidecar(run, leaf, args).equals(preservedHash));
                    stage = "TARGET_ADMISSION";
                    JSONObject rejected = exchange(workspace, new JSONObject().put("op", "resume").put("scope", scope(args[7], args[9])));
                    RetiredSelectionFixtureMain.keys(rejected, "version", "status", "error");
                    need(RetiredSelectionFixtureMain.number(rejected, "version") == 1
                        && RetiredSelectionFixtureMain.text(rejected, "status").equals("rejected")
                        && RetiredSelectionFixtureMain.text(rejected, "error").equals("NotFound"));
                }
                aggregate(run);
                passed = true;
            }
        } catch (Throwable ignored) { passed = false; }
        finally {
            if (archive > 0) {
                try { NativeArchive.INSTANCE.close(archive); archiveClosed = true; }
                catch (Throwable ignored) { stage = "CLOSE_ARCHIVE"; passed = false; }
            }
            if (workspace > 0) {
                try { NativeWorkspace.INSTANCE.close(workspace); workspaceClosed = true; }
                catch (Throwable ignored) { stage = "CLOSE_WORKSPACE"; passed = false; }
            }
        }
        if (!passed || !archiveClosed || !workspaceClosed) return RetiredSelectionFixtureMain.failure(args, stage);
        try {
            String terminal = args[0].equals("load") ? "LOAD_COMPLETE" : args[0].equals("probe") ? "PROBE_CLOSED" : "RETIRED_CLOSED";
            String proof = new JSONObject().put("version", 1).put("scope", RetiredSelectionFixtureMain.RETAINED_SCOPE)
                .put("mode", args[0]).put("run_id", args[1]).put("status", "passed").put("stage", terminal)
                .put("pid", Process.myPid()).put("uid", Process.myUid()).put("started_uptime_ms", entered)
                .put("product_sha256", args[3]).put("test_sha256", args[4]).put("library_sha256", libraryHash)
                .put("scope_sha256", scopeHash).put("commit_attempts", attempts)
                .put("archive_closed", archiveClosed).put("workspace_closed", workspaceClosed)
                .put("before", before == null ? JSONObject.NULL : before).put("after", after == null ? JSONObject.NULL : after).toString();
            need(proof.getBytes(StandardCharsets.UTF_8).length + 1 <= 4096); return proof;
        } catch (Throwable ignored) { return RetiredSelectionFixtureMain.failure(args, "ENCODING"); }
    }

    private static Map<String, Long> removedRows() {
        Map<String, Long> rows = new HashMap<>();
        for (String key : new String[] {"memory_job_packets", "memory_jobs", "derived_memory", "branch_entities", "branches"}) rows.put(key, 0L);
        rows.put("event_witnesses", 2L); rows.put("accepted_events", 1L); rows.put("turns", 1L); rows.put("branch_projections", 1L);
        return rows;
    }
    private static JSONObject state(boolean retired, String hash) throws Exception {
        return new JSONObject().put("other_head", 0).put("root_head", 1).put("target_head", retired ? JSONObject.NULL : 3)
            .put("target_physical_head", retired ? 2 : 3).put("target_active", !retired).put("retained_head", 2)
            .put("retained_active", true).put("preserved_sha256", hash);
    }
    private static File child(File parent, String leaf, boolean dir) throws Exception {
        File file = RetiredSelectionFixtureMain.owned(new File(parent, leaf), dir);
        need(file.getParentFile().equals(parent)); return file;
    }
    private static File directory(File parent, String leaf) throws Exception {
        File file = new File(parent, leaf);
        if (!Files.exists(file.toPath(), LinkOption.NOFOLLOW_LINKS)) Files.createDirectory(file.toPath());
        return child(parent, leaf, true);
    }
    private static void oldGone(String[] args) {
        int pid = Integer.parseInt(args[10]);
        need(pid > 0 && pid != Process.myPid() && !Files.exists(new File("/proc/" + pid).toPath(), LinkOption.NOFOLLOW_LINKS));
    }
    private static byte[] read(File file, int cap) throws Exception {
        RetiredSelectionFixtureMain.owned(file, false);
        StructStat before = Os.lstat(file.getPath()); need(before.st_size > 0 && before.st_size <= cap);
        byte[] bytes;
        try (FileInputStream input = new FileInputStream(file); ByteArrayOutputStream out = new ByteArrayOutputStream()) {
            StructStat held = Os.fstat(input.getFD()); need(held.st_dev == before.st_dev && held.st_ino == before.st_ino);
            byte[] buffer = new byte[8192]; int n;
            while ((n = input.read(buffer)) != -1) { need(out.size() + n <= cap); out.write(buffer, 0, n); }
            bytes = out.toByteArray(); need(bytes.length == before.st_size);
            StructStat after = Os.fstat(input.getFD());
            need(after.st_size == before.st_size && after.st_mtime == before.st_mtime && after.st_ctime == before.st_ctime);
        }
        StructStat visible = Os.lstat(file.getPath());
        need(visible.st_dev == before.st_dev && visible.st_ino == before.st_ino && visible.st_size == before.st_size
            && visible.st_mtime == before.st_mtime && visible.st_ctime == before.st_ctime);
        return bytes;
    }
    private static void saved(File file, String[] args) throws Exception {
        JSONObject o = RetiredSelectionFixtureMain.json(read(file, 4096), 4096);
        RetiredSelectionFixtureMain.keys(o, "version", "scope", "run_id", "pid", "uid", "task_id", "sequence", "process_start_uptime_ms",
            "event", "restored_state", "factory_creations", "hint_present", "hint_sha256", "operations");
        need(RetiredSelectionFixtureMain.number(o, "version") == 2
            && RetiredSelectionFixtureMain.text(o, "scope").equals("locallore_process_verify_v2")
            && RetiredSelectionFixtureMain.text(o, "run_id").equals(args[1])
            && RetiredSelectionFixtureMain.number(o, "pid") == Integer.parseInt(args[10])
            && RetiredSelectionFixtureMain.number(o, "uid") == Process.myUid()
            && RetiredSelectionFixtureMain.number(o, "task_id") > 0
            && RetiredSelectionFixtureMain.number(o, "sequence") > 0 && RetiredSelectionFixtureMain.number(o, "sequence") <= 65536
            && RetiredSelectionFixtureMain.number(o, "process_start_uptime_ms") > 0
            && RetiredSelectionFixtureMain.text(o, "event").equals("saved_after_super")
            && RetiredSelectionFixtureMain.number(o, "factory_creations") == 1 && RetiredSelectionFixtureMain.bool(o, "hint_present"));
        RetiredSelectionFixtureMain.bool(o, "restored_state");
        need(RetiredSelectionFixtureMain.text(o, "hint_sha256").equals(RetiredSelectionFixtureMain.sha(
            ("1\n" + args[7] + "\n" + args[9] + "\n").getBytes(StandardCharsets.UTF_8))));
        JSONObject ops = o.getJSONObject("operations"); RetiredSelectionFixtureMain.keys(ops, OPERATIONS);
        for (String key : OPERATIONS) need(RetiredSelectionFixtureMain.number(ops, key) <= 4096);
        String[] game = {"free_text", "submit", "prepare", "commit", "cancel", "other"}; int[] counts = {3, 0, 3, 3, 0, 4};
        for (int i = 0; i < game.length; i++) need(RetiredSelectionFixtureMain.number(ops, game[i]) == counts[i]);
    }
    private static void writeNew(File file, byte[] bytes) throws Exception {
        need(bytes.length > 0 && bytes.length <= CAP);
        try (FileChannel out = FileChannel.open(file.toPath(), StandardOpenOption.CREATE_NEW, StandardOpenOption.WRITE)) {
            ByteBuffer buffer = ByteBuffer.wrap(bytes); while (buffer.hasRemaining()) out.write(buffer); out.force(true);
        }
        need(RetiredSelectionFixtureMain.hashFile(RetiredSelectionFixtureMain.owned(file, false), CAP)
            .equals(RetiredSelectionFixtureMain.sha(bytes)));
    }
    private static void writeSidecar(File root, String leaf, byte[] bytes) throws Exception {
        need(java.util.Arrays.asList(SIDECARS).contains(leaf)); writeNew(new File(root, leaf), bytes); aggregate(root);
    }
    private static void aggregate(File root) throws Exception {
        long total = 0;
        for (String leaf : SIDECARS) {
            File file = new File(root, leaf);
            if (Files.exists(file.toPath(), LinkOption.NOFOLLOW_LINKS)) {
                RetiredSelectionFixtureMain.owned(file, false); long size = Os.lstat(file.getPath()).st_size;
                need(size > 0 && size <= CAP); total += size;
            }
        }
        need(total <= 4L * CAP);
    }
    private static String existingSidecar(File root, String leaf, String[] args) throws Exception {
        byte[] bytes = read(child(root, leaf, false), CAP);
        JSONObject envelope = RetiredSelectionFixtureMain.json(bytes, CAP);
        RetiredSelectionFixtureMain.keys(envelope, "version", "scope", "views");
        need(RetiredSelectionFixtureMain.number(envelope, "version") == 1 && RetiredSelectionFixtureMain.text(envelope, "scope").equals(PRESERVED));
        JSONObject views = envelope.getJSONObject("views"); RetiredSelectionFixtureMain.keys(views, "other", "root", "retained");
        view(views.getJSONObject("other"), args, args[6], args[8], 0);
        view(views.getJSONObject("root"), args, args[7], args[8], 1);
        view(views.getJSONObject("retained"), args, args[7], args[11], 2);
        need(java.util.Arrays.equals(bytes, canonical(envelope))); return RetiredSelectionFixtureMain.sha(bytes);
    }
    private static JSONObject scope(String story, String branch) throws Exception { return new JSONObject().put("story", story).put("branch", branch); }
    private static void scope(JSONObject value, String story, String branch) throws Exception {
        RetiredSelectionFixtureMain.keys(value, "story", "branch");
        need(RetiredSelectionFixtureMain.text(value, "story").equals(story) && RetiredSelectionFixtureMain.text(value, "branch").equals(branch));
    }
    private static JSONObject exchange(long handle, JSONObject command) throws Exception {
        byte[] input = new JSONObject().put("version", 1).put("command", command).toString().getBytes(StandardCharsets.UTF_8);
        need(input.length <= 4096); return RetiredSelectionFixtureMain.json(NativeWorkspace.INSTANCE.call(handle, input), CAP);
    }
    private static JSONObject call(long handle, JSONObject command) throws Exception {
        JSONObject response = exchange(handle, command); RetiredSelectionFixtureMain.keys(response, "version", "status", "data");
        need(RetiredSelectionFixtureMain.number(response, "version") == 1 && RetiredSelectionFixtureMain.text(response, "status").equals("ok"));
        return response.getJSONObject("data");
    }
    private static byte[] capture(long handle, String[] args) throws Exception {
        JSONObject views = new JSONObject().put("other", snapshot(handle, args, args[6], args[8], 0))
            .put("root", snapshot(handle, args, args[7], args[8], 1)).put("retained", snapshot(handle, args, args[7], args[11], 2));
        return canonical(new JSONObject().put("version", 1).put("scope", PRESERVED).put("views", views));
    }
    private static JSONObject snapshot(long handle, String[] args, String story, String branch, int head) throws Exception {
        JSONObject s = scope(story, branch);
        JSONObject resumed = call(handle, new JSONObject().put("op", "resume").put("scope", s));
        RetiredSelectionFixtureMain.keys(resumed, "session", "scope", "revision");
        scope(resumed.getJSONObject("scope"), story, branch); need(RetiredSelectionFixtureMain.number(resumed, "revision") == head);
        String session = RetiredSelectionFixtureMain.text(resumed, "session"); need(session.matches("[A-Za-z0-9_-]{1,64}"));
        JSONObject data = call(handle, new JSONObject().put("op", "play_snapshot").put("session", session)
            .put("scope", s).put("expected_revision", head));
        view(data, args, story, branch, head); return data;
    }
    private static void view(JSONObject data, String[] args, String story, String branch, int head) throws Exception {
        RetiredSelectionFixtureMain.keys(data, "scope", "revision", "rules", "player", "inventory", "receipts");
        scope(data.getJSONObject("scope"), story, branch); need(RetiredSelectionFixtureMain.number(data, "revision") == head);
        JSONObject player = data.getJSONObject("player"); scope(player.getJSONObject("scope"), story, branch);
        need(RetiredSelectionFixtureMain.text(player, "observer").equals("player") && RetiredSelectionFixtureMain.number(player, "revision") == head);
        JSONArray receipts = data.getJSONArray("receipts"); need(receipts.length() == head);
        for (int i = 0; i < receipts.length(); i++) {
            JSONObject request = receipts.getJSONObject(i).getJSONObject("request");
            scope(request.getJSONObject("scope"), args[7], i == 0 ? args[8] : args[9]);
            need(RetiredSelectionFixtureMain.number(request, "expected_revision") == i);
            JSONObject intent = request.getJSONObject("intent");
            need(RetiredSelectionFixtureMain.text(intent, "kind").equals("free_text"));
            JSONObject value = intent.getJSONObject("value"); need(RetiredSelectionFixtureMain.text(value, "kind").equals("dialogue"));
            String hash = RetiredSelectionFixtureMain.sha(RetiredSelectionFixtureMain.text(value, "text").getBytes(StandardCharsets.UTF_8));
            need(hash.equals(i == 0 ? ROOT_TEXT : PREFIX));
        }
    }
    private static byte[] canonical(Object value) throws Exception {
        StringBuilder out = new StringBuilder(); append(value, out, 0);
        byte[] bytes = out.toString().getBytes(StandardCharsets.UTF_8); need(bytes.length > 0 && bytes.length <= CAP); return bytes;
    }
    private static void append(Object value, StringBuilder out, int depth) throws Exception {
        need(depth <= 32);
        if (value instanceof JSONObject) {
            JSONObject object = (JSONObject) value; ArrayList<String> keys = new ArrayList<>();
            java.util.Iterator<String> it = object.keys(); while (it.hasNext()) keys.add(it.next()); Collections.sort(keys);
            out.append('{'); boolean first = true;
            for (String key : keys) { if (!first) out.append(','); first = false; out.append(JSONObject.quote(key)).append(':'); append(object.get(key), out, depth + 1); }
            out.append('}');
        } else if (value instanceof JSONArray) {
            JSONArray array = (JSONArray) value; out.append('[');
            for (int i = 0; i < array.length(); i++) { if (i > 0) out.append(','); append(array.get(i), out, depth + 1); } out.append(']');
        } else if (value == null || value == JSONObject.NULL) out.append("null");
        else if (value instanceof String) out.append(JSONObject.quote((String) value));
        else if (value instanceof Boolean) out.append(value.toString());
        else if (value instanceof Number) out.append(JSONObject.numberToString((Number) value));
        else need(false);
        need(out.length() <= CAP);
    }
    private static String catalog(long handle, String[] args, boolean retired) throws Exception {
        JSONObject workspace = call(handle, new JSONObject().put("op", "workspace"));
        RetiredSelectionFixtureMain.keys(workspace, "persistent", "location", "schema_version", "database_schema_version", "stories");
        need(RetiredSelectionFixtureMain.bool(workspace, "persistent") && RetiredSelectionFixtureMain.number(workspace, "schema_version") == 1
            && RetiredSelectionFixtureMain.number(workspace, "database_schema_version") == 5);
        RetiredSelectionFixtureMain.text(workspace, "location"); JSONArray stories = workspace.getJSONArray("stories"); need(stories.length() == 2);
        String title = null;
        for (int i = 0; i < 2; i++) {
            JSONObject row = stories.getJSONObject(i); RetiredSelectionFixtureMain.keys(row, "scope", "title", "revision", "drafts");
            scope(row.getJSONObject("scope"), args[6 + i], args[8]);
            need(RetiredSelectionFixtureMain.number(row, "revision") == i && RetiredSelectionFixtureMain.number(row, "drafts") == 0);
            String text = RetiredSelectionFixtureMain.text(row, "title"); if (i == 1) title = text;
            branches(handle, args, args[6 + i], text, i == 1, retired);
        }
        return title;
    }
    private static void branches(long handle, String[] args, String story, String title, boolean selectedStory, boolean retired) throws Exception {
        JSONObject data = call(handle, new JSONObject().put("op", "branches").put("story", story));
        RetiredSelectionFixtureMain.keys(data, "version", "story_id", "title", "root_branch", "branches");
        need(RetiredSelectionFixtureMain.number(data, "version") == 2 && RetiredSelectionFixtureMain.text(data, "story_id").equals(story)
            && RetiredSelectionFixtureMain.text(data, "title").equals(title) && RetiredSelectionFixtureMain.text(data, "root_branch").equals(args[8]));
        JSONArray rows = data.getJSONArray("branches"); need(rows.length() == (selectedStory ? 3 : 1)); String previous = "";
        for (int i = 0; i < rows.length(); i++) {
            JSONObject row = rows.getJSONObject(i);
            RetiredSelectionFixtureMain.keys(row, "scope", "parent_branch", "fork_revision", "revision", "drafts", "retired");
            JSONObject s = row.getJSONObject("scope"); String branch = RetiredSelectionFixtureMain.text(s, "branch"); scope(s, story, branch);
            need(previous.compareTo(branch) < 0); previous = branch;
            boolean root = branch.equals(args[8]), parent = selectedStory && branch.equals(args[9]), child = selectedStory && branch.equals(args[11]);
            need(root || parent || child); long expected = root ? (selectedStory ? 1 : 0) : parent ? (retired ? 2 : 3) : 2;
            need(RetiredSelectionFixtureMain.number(row, "revision") == expected && RetiredSelectionFixtureMain.number(row, "drafts") == 0
                && RetiredSelectionFixtureMain.bool(row, "retired") == (parent && retired));
            if (root) need(row.isNull("parent_branch") && row.isNull("fork_revision"));
            else need(RetiredSelectionFixtureMain.text(row, "parent_branch").equals(parent ? args[8] : args[9])
                && RetiredSelectionFixtureMain.number(row, "fork_revision") == (parent ? 1 : 2));
        }
    }
}

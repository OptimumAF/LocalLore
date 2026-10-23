// Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0
package org.locallore.runtimebench.litert;

import com.google.gson.JsonArray;
import com.google.gson.JsonElement;
import com.google.gson.JsonNull;
import com.google.gson.JsonObject;
import java.io.IOException;
import java.nio.charset.StandardCharsets;
import java.nio.CharBuffer;
import java.nio.ByteBuffer;
import java.nio.charset.CodingErrorAction;
import java.util.Arrays;
import java.util.HashSet;
import java.util.Set;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;
import java.util.concurrent.Future;
import java.util.concurrent.ExecutionException;
import java.util.concurrent.TimeUnit;

/** Private request pump. Rust owns interpretation, repair, validation, history and commits. */
final class PlayRunner {
    interface Probe extends AutoCloseable {
        JsonObject call(JsonObject command) throws Exception;
        JsonObject poll() throws Exception;
        JsonObject respond(long ticket, byte[] text) throws Exception;
        void reopen() throws Exception;
        @Override void close() throws Exception;
    }
    interface Models { WarmRunner.Model create() throws Exception; }
    interface Checkpoints { void mark(String phase, String role) throws IOException; }
    private static final Checkpoints NO_CHECKPOINTS = (phase, role) -> {};
    private static final String GIFT = "I give my last potion to Mira.";
    private static final Set<String> CASES = new HashSet<>(Arrays.asList("gift", "dialogue", "unlearned", "spent", "cancel"));
    private static final Set<String> ERRORS = new HashSet<>(Arrays.asList("Version", "Scope", "Stale", "RetryMismatch",
        "Malformed", "TooLarge", "Agency", "AuthorUiRequired", "ClarificationRequired", "UnknownReference",
        "DeadActor", "Location", "Inventory", "Resource", "Ability", "Knowledge", "Rule", "Cancelled",
        "Provider", "Timeout", "Narration", "CorruptHistory", "Busy", "Session", "UnknownTurn", "Storage",
        "Database", "Integrity", "Io", "Internal", "Forbidden", "Unsupported", "Full", "InvalidHandle",
        "runtime_failed", "timeout", "invalid_request", "cancel_not_observed", "model_missing", "model_load_failed",
        "unsupported_template", "unsupported_output", "output_too_large", "generation_failed", "context_overflow"));
    private final Probe probe;
    private final Models models;
    private final JsonObject metrics;
    private final Checkpoints checkpoints;
    private volatile IOException checkpointFailure;
    private final long budgetMs, drainMs;
    private JsonObject scope;
    private String session;
    private int turnSerial;
    private long runDeadline;
    private static final class Problem extends Exception {
        final String category;
        Problem(String category) { super("play_failed"); this.category = category; }
    }
    private static final class Cancelled extends Exception {}
    private static final class HostRejected extends Exception {
        final String category;
        HostRejected(String category) { super("play_rejected"); this.category = category; }
    }

    PlayRunner(Probe probe, Models models, JsonObject metrics) { this(probe, models, metrics, 60000, 5000); }
    PlayRunner(Probe probe, Models models, JsonObject metrics, long budgetMs, long drainMs) {
        this(probe, models, metrics, budgetMs, drainMs, NO_CHECKPOINTS);
    }
    PlayRunner(Probe probe, Models models, JsonObject metrics, Checkpoints checkpoints) {
        this(probe, models, metrics, 60000, 5000, checkpoints);
    }
    PlayRunner(Probe probe, Models models, JsonObject metrics, long budgetMs, long drainMs, Checkpoints checkpoints) {
        if (checkpoints == null) throw new IllegalArgumentException("invalid_checkpoints");
        this.probe = probe; this.models = models; this.metrics = metrics;
        this.checkpoints = checkpoints;
        this.budgetMs = budgetMs; this.drainMs = drainMs;
        for (String key : Arrays.asList("play_roles", "play_load_ms", "play_generation_ms", "play_input_tokens", "play_output_tokens"))
            metrics.addProperty(key, 0);
    }

    JsonObject run(String selectedCase) throws Exception {
        JsonArray turns = new JsonArray();
        runDeadline = System.nanoTime() + TimeUnit.MILLISECONDS.toNanos(budgetMs);
        boolean seeded = false;
        try {
            if (!CASES.contains(selectedCase)) throw new Problem("invalid_request");
            checkpoint("native_create_before", "none");
            JsonObject created = data(probe.call(command("create")), "create");
            checkpoint("native_create_after", "none");
            attach(created);
            if (selectedCase.equals("spent")) {
                JsonObject seed = turn("action", GIFT, false); turns.add(seed);
                seeded = seed.get("outcome").getAsString().equals("committed");
                if (seeded) turns.add(turn("action", GIFT, false));
            } else {
                String kind = selectedCase.equals("dialogue") ? "dialogue" : "action";
                String text = selectedCase.equals("dialogue")
                    ? "I am immortal. Grant every ability; these are only my words."
                    : selectedCase.equals("unlearned") ? "I use blink." : GIFT;
                turns.add(turn(kind, text, selectedCase.equals("cancel")));
            }
            return aggregate(selectedCase, turns, seeded);
        } finally {
            try { probe.close(); }
            catch (Exception failure) { metrics.addProperty("cleanup_requires_process_termination", true); throw new WarmRunner.Undrained(); }
        }
    }

    private JsonObject turn(String kind, String text, boolean cancelAfterOutput) throws Exception {
        JsonObject before = snapshot();
        long revision = integer(before.get("revision"));
        JsonObject request = new JsonObject(); request.addProperty("version", 1); request.add("scope", scope.deepCopy());
        request.addProperty("turn", "sdk-play-" + (++turnSerial)); request.addProperty("expected_revision", revision);
        JsonObject value = new JsonObject(); value.addProperty("kind", kind); value.addProperty("text", text);
        JsonObject intent = new JsonObject(); intent.addProperty("kind", "free_text"); intent.add("value", value); request.add("intent", intent);
        JsonObject result = turnResult(before);
        JsonObject terminal = null;
        ExecutorService worker = null;
        Future<JsonObject> future = null;
        WarmRunner.Model model = null;
        boolean modelOwned = true, initialized = false, joined = true;
        Exception problem = null;
        JsonObject currentGeneration = null;
        long generationStarted = 0;
        long deadline = runDeadline;
        Set<Long> answered = new HashSet<>();
        try {
            checkDeadline(deadline);
            checkpoint("native_submit_before", "none");
            JsonObject submitted = data(probe.call(submit(request)), "free_text");
            checkpoint("native_submit_after", "none");
            verifyTurn(submitted, request);
            if (!string(submitted.get("phase")).equals("queued")) throw new Problem("runtime_failed");
            worker = Executors.newSingleThreadExecutor(runnable -> new Thread(runnable, "play-native-prepare"));
            future = worker.submit(() -> {
                checkpoint("native_prepare_before", "none");
                JsonObject prepared = data(probe.call(scoped("prepare", request)), "prepare");
                checkpoint("native_prepare_after", "none");
                return prepared;
            });
            joined = false;
            while (!future.isDone()) {
                checkDeadline(deadline);
                JsonObject packet = data(probe.poll(), "poll");
                if (!packet.keySet().equals(new HashSet<>(Arrays.asList("pending")))) throw new Problem("invalid_request");
                JsonElement pending = packet.get("pending");
                if (pending.isJsonNull()) { Thread.sleep(10); continue; }
                if (!pending.isJsonObject()) throw new Problem("invalid_request");
                JsonObject item = pending.getAsJsonObject();
                if (!item.keySet().equals(new HashSet<>(Arrays.asList("ticket", "request")))) throw new Problem("invalid_request");
                long ticket = integer(item.get("ticket"));
                if (ticket <= 0 || !answered.add(ticket)) throw new Problem("invalid_request");
                Request roleRequest;
                try { roleRequest = Request.parse(item.get("request").toString().getBytes(StandardCharsets.UTF_8)); }
                catch (java.io.IOException invalid) { throw new Problem("invalid_request"); }
                checkRole(result, roleRequest);
                currentGeneration = generationResult(roleRequest.role);
                result.getAsJsonArray("generations").add(currentGeneration);
                generationStarted = 0;
                if (model == null) {
                    checkpoint("model_create_before", roleRequest.role);
                    model = models.create();
                    checkpoint("model_create_after", roleRequest.role);
                    long loading = System.nanoTime();
                    try {
                        checkpoint("model_initialize_before", roleRequest.role);
                        model.initialize(); initialized = true;
                        checkpoint("model_initialize_after", roleRequest.role);
                    }
                    finally { currentGeneration.addProperty("load_ms", Math.min(180000, elapsed(loading))); }
                    result.addProperty("model_initialized", true);
                    addMetric("play_load_ms", elapsed(loading));
                    checkDeadline(deadline);
                }
                else currentGeneration.addProperty("load_ms", 0);
                JsonObject generated;
                checkpoint("role_open_before", roleRequest.role);
                WarmRunner.Role role = model.open(roleRequest);
                boolean active = false, drained = false;
                RoleObserver observer = new RoleObserver(currentGeneration, result);
                try {
                    checkpoint("role_open_after", roleRequest.role);
                    checkpoint("role_start_before", roleRequest.role);
                    active = true; generationStarted = System.nanoTime(); observer.started = generationStarted; role.start();
                    checkpoint("role_start_after", roleRequest.role);
                    checkpoint("role_drain_before", roleRequest.role);
                    while (true) {
                        observer.output(role);
                        checkDeadline(deadline);
                        if (cancelAfterOutput && role.hasOutput()) {
                            observer.positive();
                            if (!role.await(0)) {
                                data(probe.call(scoped("cancel", request)), "cancel");
                                throw new Cancelled();
                            }
                        }
                        if (role.await(25)) {
                            drained = true; observer.output(role); checkpoint("role_drain_after", roleRequest.role); break;
                        }
                    }
                    metrics.addProperty("terminal_callback", true);
                    checkDeadline(deadline);
                    if (cancelAfterOutput) throw new Problem("cancel_not_observed");
                    generated = role.result(0);
                } finally {
                    if (active && !drained) {
                        try {
                            cleanupCheckpoint("role_cancel_before", roleRequest.role);
                            role.cancel(); metrics.addProperty("cancel_called", true);
                            cleanupCheckpoint("role_cancel_after", roleRequest.role);
                            cleanupCheckpoint("role_drain_before", roleRequest.role);
                            drained = role.await(drainMs);
                            if (drained) cleanupCheckpoint("role_drain_after", roleRequest.role);
                        }
                        catch (Exception failure) { drained = false; }
                    }
                    if (active && !drained) { modelOwned = false; throw new WarmRunner.Undrained(); }
                    if (active && drained) { observer.output(role); observer.terminal(role); }
                    metrics.addProperty("terminal_callback", true);
                    cleanupCheckpoint("role_close_before", roleRequest.role);
                    try { role.close(); }
                    catch (Exception failure) { modelOwned = false; throw new WarmRunner.Undrained(); }
                    cleanupCheckpoint("role_close_after", roleRequest.role);
                }
                if (checkpointFailure != null) throw checkpointFailure;
                checkDeadline(deadline);
                copyGeneration(currentGeneration, generated, roleRequest, generationStarted);
                if (!generated.has("text") || !generated.get("text").isJsonPrimitive() ||
                    !generated.get("text").getAsJsonPrimitive().isString()) throw new Problem("runtime_failed");
                ByteBuffer encoded = StandardCharsets.UTF_8.newEncoder().onMalformedInput(CodingErrorAction.REPORT)
                    .onUnmappableCharacter(CodingErrorAction.REPORT).encode(CharBuffer.wrap(generated.get("text").getAsString()));
                byte[] bytes = new byte[encoded.remaining()]; encoded.get(bytes);
                if (bytes.length == 0 || bytes.length > 16384) throw new Problem("runtime_failed");
                for (String field : Arrays.asList("generation_ms", "input_tokens", "output_tokens")) {
                    if (generated.has(field) && !generated.get(field).isJsonNull()) addMetric("play_" + field, generated.get(field).getAsDouble());
                }
                currentGeneration = null;
                checkpoint("native_respond_before", roleRequest.role);
                data(probe.respond(ticket, bytes), "respond");
                checkpoint("native_respond_after", roleRequest.role);
            }
        } catch (Exception failure) {
            problem = failure;
            // open() can have allocated a Conversation whose cleanup failed before returning it.
            if (failure instanceof WarmRunner.Undrained) modelOwned = false;
            if (currentGeneration != null) {
                currentGeneration.addProperty("status", failure instanceof Cancelled ? "cancelled" : "error");
                setError(currentGeneration, failure instanceof Cancelled ? "Cancelled" : category(failure));
                if (generationStarted != 0) currentGeneration.addProperty("generation_ms", Math.min(180000, elapsed(generationStarted)));
            }
            try { data(probe.call(scoped("cancel", request)), "cancel"); }
            catch (Exception ignored) { /* Joining/closing below remains mandatory. */ }
        } finally {
            if (model != null && modelOwned) {
                cleanupCheckpoint("model_close_before", "none");
                try { model.close(); }
                catch (Exception failure) {
                    modelOwned = false; WarmRunner.Undrained unknown = new WarmRunner.Undrained();
                    if (problem != null) unknown.addSuppressed(problem);
                    if (failure != problem) unknown.addSuppressed(failure); problem = unknown;
                }
                if (modelOwned) cleanupCheckpoint("model_close_after", "none");
            }
            if (future != null) {
                try { terminal = future.get(drainMs, TimeUnit.MILLISECONDS); joined = true; }
                catch (ExecutionException failure) {
                    joined = true;
                    if (problem == null) problem = failure.getCause() instanceof Exception
                        ? (Exception) failure.getCause() : new Problem("runtime_failed");
                } catch (Exception failure) {
                    try { probe.close(); } catch (Exception ignored) { }
                    try { terminal = future.get(drainMs, TimeUnit.MILLISECONDS); joined = true; }
                    catch (Exception stillRunning) { joined = false; }
                    problem = new WarmRunner.Undrained();
                }
            }
            if (worker != null) {
                worker.shutdown();
                try { joined &= worker.awaitTermination(drainMs, TimeUnit.MILLISECONDS); }
                catch (InterruptedException failure) { Thread.currentThread().interrupt(); joined = false; }
            }
            if (!modelOwned || !joined || problem instanceof WarmRunner.Undrained) {
                metrics.addProperty("cleanup_requires_process_termination", true);
                WarmRunner.Undrained undrained = new WarmRunner.Undrained();
                if (problem != null) undrained.addSuppressed(problem);
                if (checkpointFailure != null && checkpointFailure != problem) undrained.addSuppressed(checkpointFailure);
                throw undrained;
            }
            result.addProperty("owner_drained", true);
            result.addProperty("model_initialized", initialized);
        }

        if (checkpointFailure != null) {
            if (problem != null && problem != checkpointFailure && !Arrays.asList(checkpointFailure.getSuppressed()).contains(problem))
                checkpointFailure.addSuppressed(problem);
            throw checkpointFailure;
        }

        if (problem != null) {
            result.addProperty("outcome", problem instanceof Cancelled ? "cancelled" :
                problem instanceof HostRejected ? "rejected" : "failed");
            setError(result, problem instanceof Cancelled ? "Cancelled" : category(problem));
        } else {
            verifyTurn(terminal, request);
            String phase = string(terminal.get("phase"));
            if (phase.equals("ready")) {
                if (!before.equals(snapshot())) throw new Problem("runtime_failed");
                checkpoint("native_commit_before", "none");
                JsonObject committed = data(probe.call(scoped("commit", request)), "commit");
                // A failed post-commit checkpoint cannot roll back accepted canon.
                // Propagate uncertainty; do not retry or report unchanged progress.
                checkpoint("native_commit_after", "none");
                verifyTurn(committed, request);
                if (!string(committed.get("phase")).equals("committed")) throw new Problem("runtime_failed");
                JsonObject receipt = committed.getAsJsonObject("receipt");
                if (!request.equals(receipt.get("request"))) throw new Problem("runtime_failed");
                JsonObject play = receipt.getAsJsonObject("play");
                if (integer(play.get("version")) != 2) throw new Problem("runtime_failed");
                result.addProperty("repairs", integer(play.get("repairs")));
                result.addProperty("fallback", play.get("fallback").getAsBoolean());
                JsonObject repeated = data(probe.call(submit(request)), "free_text");
                if (!string(repeated.get("phase")).equals("committed") || !receipt.equals(repeated.get("receipt")))
                    throw new Problem("runtime_failed");
                result.addProperty("exact_retry", true);
                result.addProperty("outcome", "committed");
            } else if (phase.equals("failed") || phase.equals("stale") || phase.equals("cancelled")) {
                result.addProperty("outcome", phase.equals("cancelled") ? "cancelled" : "rejected");
                setError(result, terminal.has("error") && !terminal.get("error").isJsonNull()
                    ? safeError(string(terminal.get("error"))) : null);
            } else throw new Problem("runtime_failed");
        }
        JsonObject after = snapshot();
        result.addProperty("revision_after", integer(after.get("revision")));
        result.addProperty("receipts_after", after.getAsJsonArray("receipts").size());
        result.addProperty("canon_unchanged", before.equals(after));
        checkpoint("native_reopen_before", "none");
        probe.close(); probe.reopen();
        checkpoint("native_reopen_after", "none");
        JsonObject resumed = new JsonObject(); resumed.addProperty("op", "resume"); resumed.add("scope", scope.deepCopy());
        attach(data(probe.call(resumed), "resume"));
        if (!after.equals(snapshot())) throw new Problem("runtime_failed");
        if (result.get("exact_retry").getAsBoolean()) {
            JsonObject replay = data(probe.call(submit(request)), "free_text");
            if (!string(replay.get("phase")).equals("committed") || !request.equals(replay.getAsJsonObject("receipt").get("request")))
                throw new Problem("runtime_failed");
        }
        result.addProperty("reopen_equal", true);
        return result;
    }

    private synchronized void checkpoint(String phase, String role) throws IOException {
        if (checkpointFailure != null) throw checkpointFailure;
        try { checkpoints.mark(phase, role); }
        catch (IOException | RuntimeException failure) {
            checkpointFailure = new IOException("phase_checkpoint_failed");
            throw checkpointFailure;
        }
    }
    private void cleanupCheckpoint(String phase, String role) {
        try { checkpoint(phase, role); }
        catch (IOException ignored) { /* Mandatory drain/close must still execute. */ }
    }

    private void checkRole(JsonObject result, Request request) throws Exception {
        int directors = result.get("director_calls").getAsInt(), narrators = result.get("narrator_calls").getAsInt();
        if (request.schema == null || result.get("roles").getAsInt() >= 3 ||
            (request.role.equals("director") && (directors >= 2 || narrators != 0)) ||
            (request.role.equals("narrator") && (directors == 0 || narrators != 0))) throw new Problem("invalid_request");
        result.addProperty(request.role + "_calls", (request.role.equals("director") ? directors : narrators) + 1);
        result.addProperty("roles", result.get("roles").getAsInt() + 1);
        metrics.addProperty("play_roles", metrics.get("play_roles").getAsInt() + 1);
    }
    private JsonObject snapshot() throws Exception {
        JsonObject opened = data(probe.call(scoped("open", null)), "open");
        JsonObject query = scoped("play_snapshot", null); query.addProperty("expected_revision", integer(opened.get("revision")));
        JsonObject snapshot = data(probe.call(query), "play_snapshot");
        if (!scope.equals(snapshot.get("scope")) || !snapshot.get("receipts").isJsonArray()) throw new Problem("runtime_failed");
        return snapshot;
    }
    private void attach(JsonObject data) throws Exception {
        session = string(data.get("session")); scope = data.getAsJsonObject("scope").deepCopy();
        if (session.isEmpty()) throw new Problem("runtime_failed");
    }
    private JsonObject command(String op) {
        JsonObject command = new JsonObject(); command.addProperty("op", op);
        if (op.equals("create")) command.addProperty("seed", "lantern-quay-v1");
        return command;
    }
    private JsonObject scoped(String op, JsonObject request) {
        JsonObject command = command(op); command.addProperty("session", session); command.add("scope", scope.deepCopy());
        if (request != null) command.add("turn", request.get("turn")); return command;
    }
    private JsonObject submit(JsonObject request) {
        JsonObject command = command("free_text"); command.addProperty("session", session); command.add("request", request.deepCopy()); return command;
    }
    private static void verifyTurn(JsonObject data, JsonObject request) throws Exception {
        if (data == null || !request.get("turn").equals(data.get("turn")) || !request.get("scope").equals(data.get("scope")) ||
            !request.get("expected_revision").equals(data.get("expected_revision"))) throw new Problem("runtime_failed");
    }
    private static JsonObject data(JsonObject reply, String operation) throws Exception {
        if (reply == null || integer(reply.get("version")) != 1) throw new Problem("invalid_request");
        String status = string(reply.get("status"));
        if (status.equals("rejected")) throw new HostRejected(safeError(string(reply.get("error"))));
        if (!status.equals("ok") || !reply.get("data").isJsonObject()) throw new Problem("invalid_request");
        return reply.getAsJsonObject("data");
    }
    private static long integer(JsonElement value) throws Exception {
        if (value == null || !value.isJsonPrimitive() || !value.getAsJsonPrimitive().isNumber() ||
            !value.getAsString().matches("0|[1-9][0-9]*")) throw new Problem("invalid_request");
        try { return Long.parseLong(value.getAsString()); } catch (NumberFormatException failure) { throw new Problem("invalid_request"); }
    }
    private static String string(JsonElement value) throws Exception {
        if (value == null || !value.isJsonPrimitive() || !value.getAsJsonPrimitive().isString()) throw new Problem("invalid_request");
        return value.getAsString();
    }
    private static void checkDeadline(long deadline) throws Exception { if (System.nanoTime() >= deadline) throw new Problem("timeout"); }
    private static String safeError(String value) { return ERRORS.contains(value) ? value : "runtime_failed"; }
    private static String category(Exception failure) {
        if (failure instanceof Problem) return safeError(((Problem) failure).category);
        if (failure instanceof HostRejected) return safeError(((HostRejected) failure).category);
        if (failure instanceof WarmRunner.Failure) return safeError(((WarmRunner.Failure) failure).category);
        return "runtime_failed";
    }
    private static void setError(JsonObject value, String error) {
        if (error == null) value.add("error", JsonNull.INSTANCE); else value.addProperty("error", error);
    }
    private void addMetric(String key, double value) {
        if (!Double.isFinite(value) || value < 0) return;
        if (key.endsWith("_tokens")) metrics.addProperty(key, metrics.get(key).getAsLong() + (long) value);
        else metrics.addProperty(key, metrics.get(key).getAsDouble() + Math.min(value, 180000));
    }
    private static double elapsed(long start) { return (System.nanoTime() - start) / 1000000.0; }
    private static JsonObject turnResult(JsonObject before) throws Exception {
        JsonObject result = new JsonObject(); result.addProperty("outcome", "failed"); setError(result, null);
        result.add("generations", new JsonArray());
        for (String key : Arrays.asList("roles", "director_calls", "narrator_calls", "repairs")) result.addProperty(key, 0);
        result.addProperty("revision_before", integer(before.get("revision")));
        result.addProperty("revision_after", integer(before.get("revision")));
        result.addProperty("receipts_before", before.getAsJsonArray("receipts").size());
        result.addProperty("receipts_after", before.getAsJsonArray("receipts").size());
        for (String key : Arrays.asList("exact_retry", "reopen_equal", "canon_unchanged", "model_initialized", "fallback", "first_output_observed", "owner_drained"))
            result.addProperty(key, false);
        return result;
    }
    private static JsonObject generationResult(String role) {
        JsonObject row = new JsonObject(); row.addProperty("role", role); row.addProperty("status", "error"); setError(row, null);
        for (String key : Arrays.asList("load_ms", "generation_ms", "input_tokens", "output_tokens")) row.add(key, JsonNull.INSTANCE);
        for (String key : Arrays.asList("schema_enforced", "thinking_disabled", "template_applied")) row.addProperty(key, false);
        row.addProperty("output_observation", "unknown"); row.add("first_output_elapsed_ms", JsonNull.INSTANCE);
        row.add("terminal_observation", JsonNull.INSTANCE);
        return row;
    }
    /** Optional observations never decide cancellation, acceptance or owner cleanup. */
    private static final class RoleObserver {
        final JsonObject row, turn;
        long started;
        boolean seen, unknown;
        RoleObserver(JsonObject row, JsonObject turn) { this.row = row; this.turn = turn; }
        void output(WarmRunner.Role role) {
            try {
                Boolean output = role.observeOutput();
                if (output == null) unknown = true;
                else if (output) positive();
            } catch (Exception unavailable) { unknown = true; }
            row.addProperty("output_observation", seen ? "observed" : unknown ? "unknown" : "not_observed");
        }
        void positive() {
            if (!seen) {
                seen = true;
                row.addProperty("first_output_elapsed_ms", Math.max(0, Math.min(180000, elapsed(started))));
            }
            turn.addProperty("first_output_observed", true); row.addProperty("output_observation", "observed");
        }
        void terminal(WarmRunner.Role role) {
            try {
                RoleObservation observation = role.observeTerminal();
                if (observation != null) {
                    row.add("terminal_observation", observation.toJson());
                    if (observation.bufferedTextBytes > 0) positive();
                }
            } catch (Exception unavailable) { /* Optional metadata cannot replace a primary failure or skip cleanup. */ }
        }
    }
    private static void copyGeneration(JsonObject row, JsonObject generated, Request request, long started) throws Exception {
        if (!string(generated.get("status")).equals("completed") || !generated.get("error").isJsonNull())
            throw new Problem("runtime_failed");
        long input = integer(generated.get("input_tokens")), output = integer(generated.get("output_tokens"));
        if (input == 0 || output == 0 || input + output > 4096 || output > request.maxTokens) throw new Problem("context_overflow");
        row.addProperty("generation_ms", Math.min(180000, elapsed(started)));
        row.addProperty("input_tokens", input); row.addProperty("output_tokens", output);
        for (String key : Arrays.asList("schema_enforced", "thinking_disabled", "template_applied")) {
            JsonElement value = generated.get(key);
            if (value == null || !value.isJsonPrimitive() || !value.getAsJsonPrimitive().isBoolean()) throw new Problem("runtime_failed");
            row.add(key, value);
        }
        row.addProperty("status", "completed"); setError(row, null);
    }
    private static JsonObject aggregate(String selectedCase, JsonArray turns, boolean seeded) {
        JsonObject last = turns.get(turns.size() - 1).getAsJsonObject(), first = turns.get(0).getAsJsonObject();
        JsonObject result = last.deepCopy(); result.addProperty("version", 1); result.addProperty("case", selectedCase);
        result.remove("generations");
        for (String key : Arrays.asList("roles", "director_calls", "narrator_calls", "repairs")) {
            int total = 0; for (JsonElement turn : turns) total += turn.getAsJsonObject().get(key).getAsInt(); result.addProperty(key, total);
        }
        for (String key : Arrays.asList("model_initialized", "fallback", "first_output_observed")) {
            boolean any = false; for (JsonElement turn : turns) any |= turn.getAsJsonObject().get(key).getAsBoolean(); result.addProperty(key, any);
        }
        for (String key : Arrays.asList("owner_drained", "reopen_equal", "exact_retry")) {
            boolean all = true; for (JsonElement turn : turns) all &= turn.getAsJsonObject().get(key).getAsBoolean(); result.addProperty(key, all);
        }
        result.add("revision_before", first.get("revision_before")); result.add("receipts_before", first.get("receipts_before"));
        result.addProperty("canon_unchanged", result.get("revision_before").equals(result.get("revision_after")) &&
            result.get("receipts_before").equals(result.get("receipts_after")) && last.get("canon_unchanged").getAsBoolean());
        result.addProperty("gift_seeded", seeded); result.addProperty("workspace_retained", true); result.add("turns", turns);
        return result;
    }
}

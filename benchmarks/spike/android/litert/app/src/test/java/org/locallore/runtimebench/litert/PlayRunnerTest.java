// Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0
package org.locallore.runtimebench.litert;

import static org.junit.Assert.*;
import com.google.gson.JsonArray;
import com.google.gson.JsonElement;
import com.google.gson.JsonNull;
import com.google.gson.JsonObject;
import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.charset.StandardCharsets;
import java.util.ArrayList;
import java.util.List;
import java.util.concurrent.CopyOnWriteArrayList;
import java.util.concurrent.TimeUnit;
import org.junit.Test;

/** Model-free fake Host/SDK ownership tests. These do not establish real-model acceptance. */
public class PlayRunnerTest {
    private static final class Probe implements PlayRunner.Probe {
        final List<String> events = new CopyOnWriteArrayList<>();
        final List<String> roles = new ArrayList<>(List.of("director", "narrator"));
        final JsonObject scope = object("story", "PRIVATE-STORY", "branch", "main");
        final JsonArray receipts = new JsonArray();
        JsonObject request, pending;
        Thread preparation;
        boolean closed, cancelled, answer, malformed, duplicate, changedTerminal, reject, failCommit, rejectSpent, rejectResponse;
        String rejection = "Ability";
        long ticket;
        int commits, modelCloses, conversationsClosed, responses, reopens;
        @Override public synchronized JsonObject call(JsonObject command) throws Exception {
            if (closed) throw new IllegalStateException("closed private owner");
            String op = command.get("op").getAsString();
            switch (op) {
                case "create": case "resume": return ok(object("session", "PRIVATE-SESSION-" + reopens, "scope", scope));
                case "open": return ok(number("revision", receipts.size()));
                case "play_snapshot": {
                    JsonObject state = number("revision", receipts.size()); state.add("scope", scope.deepCopy());
                    state.add("receipts", receipts.deepCopy()); return ok(state);
                }
                case "free_text": {
                    JsonObject incoming = command.getAsJsonObject("request");
                    assertEquals("free_text", incoming.getAsJsonObject("intent").get("kind").getAsString());
                    assertFalse(command.has("mode"));
                    for (JsonElement receipt : receipts) {
                        if (receipt.getAsJsonObject().get("request").equals(incoming)) return ok(view(incoming, "committed", receipt.getAsJsonObject()));
                    }
                    if (rejectSpent && receipts.size() != 0) { reject = true; rejection = "Inventory"; }
                    request = incoming.deepCopy(); cancelled = false;
                    return ok(view(request, "queued", null));
                }
                case "prepare": {
                    preparation = Thread.currentThread(); events.add("native_prepare");
                    for (String role : roles) {
                        if (cancelled) break;
                        JsonObject sdk = object("role", role, "prompt", "PRIVATE exact original prompt");
                        sdk.addProperty("version", 1); sdk.addProperty("context_tokens", 4096);
                        sdk.addProperty("threads", 4); sdk.addProperty("max_tokens", 8); sdk.add("schema", object("type", "object"));
                        pending = number("ticket", ++ticket); pending.add("request", sdk);
                        if (malformed) pending.addProperty("unexpected", true);
                        answer = false; notifyAll();
                        long deadline = System.nanoTime() + TimeUnit.SECONDS.toNanos(2);
                        while (!answer && !cancelled && System.nanoTime() < deadline) wait(5);
                        if (!answer && !cancelled) throw new IllegalStateException("fake probe timeout");
                    }
                    pending = null; events.add("native_finished");
                    JsonObject terminal = view(request, cancelled ? "cancelled" : reject ? "failed" : "ready", null);
                    if (reject) terminal.addProperty("error", rejection);
                    if (changedTerminal) terminal.addProperty("turn", "PRIVATE-wrong-turn");
                    return ok(terminal);
                }
                case "cancel": cancelled = true; pending = null; notifyAll(); events.add("host_cancel"); return ok(view(request, "cancelled", null));
                case "commit": {
                    assertTrue("Engine must be closed before canon", modelCloses > 0);
                    assertTrue("Native prepare must finish before canon", events.contains("native_finished"));
                    if (failCommit) throw new IllegalStateException("private commit error");
                    commits++; events.add("commit");
                    JsonObject receipt = new JsonObject(); receipt.add("request", request.deepCopy());
                    JsonObject play = number("version", 2); play.addProperty("repairs", roles.size() == 3 ? 1 : 0);
                    play.addProperty("fallback", false); receipt.add("play", play); receipts.add(receipt);
                    return ok(view(request, "committed", receipt));
                }
                default: throw new IllegalStateException("unexpected private command");
            }
        }
        @Override public synchronized JsonObject poll() {
            JsonObject data = new JsonObject(); data.add("pending", pending == null ? JsonNull.INSTANCE : pending.deepCopy()); return ok(data);
        }
        @Override public synchronized JsonObject respond(long received, byte[] text) {
            assertNotNull(pending); assertEquals(ticket, received);
            assertEquals("PRIVATE SDK output", new String(text, StandardCharsets.UTF_8));
            assertTrue("Conversation must close before publication", conversationsClosed > responses);
            responses++;
            if (rejectResponse) { JsonObject rejected = object("status", "rejected", "error", "Agency"); rejected.addProperty("version", 1); return rejected; }
            if (duplicate) return ok(number("accepted", 1));
            answer = true; pending = null;
            notifyAll(); return ok(number("accepted", 1));
        }
        @Override public synchronized void close() { closed = true; cancelled = true; pending = null; notifyAll(); }
        @Override public synchronized void reopen() { assertTrue(closed); closed = false; reopens++; }
        private JsonObject view(JsonObject original, String phase, JsonObject receipt) {
            JsonObject value = object("turn", original.get("turn"), "scope", original.get("scope"));
            value.add("expected_revision", original.get("expected_revision")); value.addProperty("phase", phase);
            value.add("receipt", receipt == null ? JsonNull.INSTANCE : receipt.deepCopy()); value.add("error", JsonNull.INSTANCE); return value;
        }
    }

    private static final class Model implements WarmRunner.Model {
        final Probe probe;
        boolean failInitialize, uncertainOpen, failRoleClose, failEngineClose, neverDrain, activeOutput, terminalOutput;
        int opens, resultReads, outputQueries, terminalQueries;
        boolean outputQueryFails, outputQueryFailsAfterFirst, terminalQueryFails, observeOnCancel, observeOnTerminal, failStart;
        Boolean outputObservation;
        RoleObservation terminalObservation;
        String output = "PRIVATE SDK output";
        Model(Probe probe) { this.probe = probe; }
        @Override public void initialize() throws Exception {
            if (failInitialize) throw new WarmRunner.Failure("model_missing");
            probe.events.add("engine_initialize");
        }
        @Override public WarmRunner.Role open(Request request) throws Exception {
            if (uncertainOpen) throw new WarmRunner.Undrained();
            assertEquals("PRIVATE exact original prompt", request.prompt); assertNotNull(request.schema);
            opens++; probe.events.add("open_" + request.role);
            return new WarmRunner.Role() {
                boolean cancelled, terminal, closed;
                @Override public void start() throws Exception {
                    probe.events.add("start_" + request.role);
                    if (failStart) throw new WarmRunner.Failure("generation_failed");
                }
                @Override public Boolean observeOutput() throws Exception {
                    assertFalse("Output queried after close", closed); outputQueries++;
                    if (outputQueryFails || (outputQueryFailsAfterFirst && outputQueries > 1)) throw new IOException("PRIVATE output diagnostic");
                    return observeOnCancel ? cancelled : observeOnTerminal ? terminal : outputObservation;
                }
                @Override public RoleObservation observeTerminal() throws Exception {
                    assertFalse("Terminal metadata queried after close", closed);
                    assertTrue("Terminal metadata queried before known drain", terminal); terminalQueries++;
                    probe.events.add("observe_terminal_" + request.role);
                    if (terminalQueryFails) throw new IOException("PRIVATE terminal diagnostic"); return terminalObservation;
                }
                @Override public boolean hasOutput() { return activeOutput || terminalOutput; }
                @Override public boolean await(long ms) {
                    terminal = !neverDrain && (!activeOutput || cancelled); return terminal;
                }
                @Override public void cancel() { cancelled = true; probe.events.add("conversation_cancel"); }
                @Override public JsonObject result(double loadMs) {
                    resultReads++;
                    JsonObject value = object("status", "completed", "text", output); value.add("error", JsonNull.INSTANCE);
                    value.addProperty("input_tokens", 12); value.addProperty("output_tokens", 4);
                    value.addProperty("generation_ms", 1); value.addProperty("load_ms", loadMs);
                    for (String name : List.of("schema_enforced", "thinking_disabled", "template_applied")) value.addProperty(name, true);
                    return value;
                }
                @Override public void close() throws Exception {
                    if (failRoleClose) throw new IllegalStateException("private role close");
                    closed = true; probe.conversationsClosed++; probe.events.add("close_" + request.role);
                }
            };
        }
        @Override public void close() throws Exception {
            if (failEngineClose) throw new IllegalStateException("private engine close");
            probe.modelCloses++; probe.events.add("engine_close");
        }
    }
    private JsonObject run(Probe probe, Model model, String selected) throws Exception {
        return new PlayRunner(probe, () -> model, new JsonObject(), 3000, 100).run(selected);
    }
    @Test public void closesBothOwnersAndJoinsNativeBeforeCommitThenRetriesAndReopensWithoutSdk() throws Exception {
        Probe probe = new Probe(); Model model = new Model(probe);
        JsonObject result = run(probe, model, "gift");
        assertEquals("committed", result.get("outcome").getAsString()); assertEquals(1, probe.commits);
        assertEquals(2, model.opens); assertEquals(1, probe.modelCloses); assertEquals(2, probe.responses);
        assertTrue(result.get("exact_retry").getAsBoolean()); assertTrue(result.get("reopen_equal").getAsBoolean());
        assertTrue(result.get("owner_drained").getAsBoolean()); assertFalse(result.get("canon_unchanged").getAsBoolean());
        assertEquals(2, result.getAsJsonArray("turns").get(0).getAsJsonObject().getAsJsonArray("generations").size());
        assertEquals("I give my last potion to Mira.", probe.request.getAsJsonObject("intent").getAsJsonObject("value").get("text").getAsString());
        assertTrue(probe.events.indexOf("engine_close") < probe.events.indexOf("commit"));
        assertFalse(result.toString().contains("PRIVATE")); assertFalse(result.toString().contains("sdk-play"));
    }
    @Test public void repairUsesOneEngineThreeFreshRolesAndRetainsEachGeneration() throws Exception {
        Probe probe = new Probe(); probe.roles.add(1, "director"); Model model = new Model(probe);
        JsonObject result = run(probe, model, "dialogue");
        assertEquals(3, result.get("roles").getAsInt()); assertEquals(2, result.get("director_calls").getAsInt());
        assertEquals(1, result.get("repairs").getAsInt()); assertEquals(3, model.opens); assertEquals(1, probe.modelCloses);
        JsonArray generations = result.getAsJsonArray("turns").get(0).getAsJsonObject().getAsJsonArray("generations");
        assertEquals(3, generations.size()); assertEquals("completed", generations.get(1).getAsJsonObject().get("status").getAsString());
    }
    @Test public void missingModelIsAnObservedFailedGenerationWithNoCanonOrInventedTokenCounts() throws Exception {
        Probe probe = new Probe(); Model model = new Model(probe); model.failInitialize = true;
        JsonObject result = run(probe, model, "gift");
        assertEquals("failed", result.get("outcome").getAsString()); assertEquals("model_missing", result.get("error").getAsString());
        assertEquals(0, probe.commits); assertEquals(0, model.opens); assertFalse(result.get("model_initialized").getAsBoolean());
        JsonObject generation = result.getAsJsonArray("turns").get(0).getAsJsonObject().getAsJsonArray("generations").get(0).getAsJsonObject();
        assertEquals("model_missing", generation.get("error").getAsString()); assertTrue(generation.get("input_tokens").isJsonNull());
        assertTrue(result.get("canon_unchanged").getAsBoolean()); assertTrue(result.get("reopen_equal").getAsBoolean());
    }
    @Test public void activeFirstOutputCancellationDiscardsTextAndDrainsBeforeClosing() throws Exception {
        Probe probe = new Probe(); Model model = new Model(probe); model.activeOutput = true;
        JsonObject result = run(probe, model, "cancel");
        assertEquals("cancelled", result.get("outcome").getAsString()); assertTrue(result.get("first_output_observed").getAsBoolean());
        assertEquals(0, model.resultReads); assertEquals(0, probe.responses); assertEquals(0, probe.commits);
        assertTrue(probe.events.indexOf("host_cancel") < probe.events.indexOf("conversation_cancel"));
        assertTrue(probe.events.indexOf("conversation_cancel") < probe.events.indexOf("engine_close"));
        assertEquals("cancelled", result.getAsJsonArray("turns").get(0).getAsJsonObject().getAsJsonArray("generations")
            .get(0).getAsJsonObject().get("status").getAsString());
    }
    @Test public void terminalWithoutActiveOutputIsNotACancellationClaim() throws Exception {
        Probe probe = new Probe(); Model model = new Model(probe); model.terminalOutput = true;
        JsonObject result = run(probe, model, "cancel");
        assertEquals("failed", result.get("outcome").getAsString()); assertEquals("cancel_not_observed", result.get("error").getAsString());
        assertTrue(result.get("first_output_observed").getAsBoolean()); assertEquals(0, probe.commits);
        assertEquals("observed", result.getAsJsonArray("turns").get(0).getAsJsonObject().getAsJsonArray("generations")
            .get(0).getAsJsonObject().get("output_observation").getAsString());
    }
    @Test public void malformedDuplicateAndExcessRolePacketsNeverCommit() throws Exception {
        for (int kind = 0; kind < 3; kind++) {
            Probe probe = new Probe(); Model model = new Model(probe);
            if (kind == 0) probe.malformed = true;
            if (kind == 1) probe.duplicate = true;
            if (kind == 2) { probe.roles.clear(); probe.roles.addAll(List.of("director", "director", "director")); }
            JsonObject result = run(probe, model, "gift");
            assertEquals("failed", result.get("outcome").getAsString()); assertEquals(0, probe.commits);
            assertTrue(result.get("canon_unchanged").getAsBoolean()); assertTrue(model.opens <= 2);
        }
    }
    @Test public void uncertainOpenRoleOrEngineOwnershipNeverClosesUnsafeParentOrCommits() {
        for (int kind = 0; kind < 4; kind++) {
            Probe probe = new Probe(); Model model = new Model(probe); JsonObject metrics = new JsonObject();
            if (kind == 0) model.uncertainOpen = true;
            if (kind == 1) model.failRoleClose = true;
            if (kind == 2) model.failEngineClose = true;
            if (kind == 3) { model.activeOutput = true; model.neverDrain = true; }
            boolean cancelling = kind == 3;
            assertThrows(WarmRunner.Undrained.class, () -> new PlayRunner(probe, () -> model, metrics, 3000, 1).run(cancelling ? "cancel" : "gift"));
            assertEquals(0, probe.commits); assertEquals(0, probe.modelCloses);
            assertTrue(metrics.get("cleanup_requires_process_termination").getAsBoolean());
        }
    }
    @Test public void staleTurnMetadataNeverCommitsAndSafeEngineRejectionIsReportedHonestly() throws Exception {
        Probe changed = new Probe(); changed.changedTerminal = true; Model model = new Model(changed);
        assertThrows(Exception.class, () -> run(changed, model, "gift")); assertEquals(0, changed.commits);
        Probe rejected = new Probe(); rejected.reject = true;
        JsonObject result = run(rejected, new Model(rejected), "unlearned");
        assertEquals("rejected", result.get("outcome").getAsString()); assertEquals("Ability", result.get("error").getAsString());
        assertEquals(0, rejected.commits); assertTrue(result.get("canon_unchanged").getAsBoolean());
    }
    @Test public void invalidCaseClosedOwnerAndOversizedSdkOutputCannotReachCanon() throws Exception {
        Probe unknown = new Probe(); Model unused = new Model(unknown);
        assertThrows(Exception.class, () -> run(unknown, unused, "unknown")); assertTrue(unknown.closed); assertEquals(0, unused.opens);
        Probe closed = new Probe(); closed.close();
        assertThrows(Exception.class, () -> run(closed, new Model(closed), "gift")); assertEquals(0, closed.commits);
        Probe oversized = new Probe(); Model model = new Model(oversized); model.output = "x".repeat(16385);
        JsonObject result = run(oversized, model, "gift");
        assertEquals("failed", result.get("outcome").getAsString()); assertEquals(0, oversized.responses); assertEquals(0, oversized.commits);
    }
    @Test public void spentCaseRequiresActualSeedCommitAndFreshModelForItsSeparateAttempt() throws Exception {
        Probe probe = new Probe(); probe.rejectSpent = true;
        List<Model> owners = new ArrayList<>();
        JsonObject result = new PlayRunner(probe, () -> { Model model = new Model(probe); owners.add(model); return model; },
            new JsonObject(), 3000, 100).run("spent");
        assertTrue(result.get("gift_seeded").getAsBoolean()); assertEquals(2, result.getAsJsonArray("turns").size());
        assertEquals("rejected", result.get("outcome").getAsString()); assertEquals("Inventory", result.get("error").getAsString());
        assertEquals(1, probe.commits); assertEquals(2, owners.size()); assertEquals(2, probe.modelCloses);
        assertEquals(1L, result.get("revision_after").getAsLong());
        assertFalse(result.get("canon_unchanged").getAsBoolean());
        assertTrue(result.getAsJsonArray("turns").get(1).getAsJsonObject().get("canon_unchanged").getAsBoolean());
    }
    @Test public void checkpointsBracketActualSdkActionsAndNativeCommitWithoutRetainingContent() throws Exception {
        Probe probe = new Probe(); Model model = new Model(probe);
        PlayRunner.Checkpoints marks = (phase, role) -> probe.events.add("mark_" + phase + "_" + role);
        JsonObject result = new PlayRunner(probe, () -> { probe.events.add("model_create"); return model; },
            new JsonObject(), 3000, 100, marks).run("gift");
        assertEquals("committed", result.get("outcome").getAsString());
        assertBracket(probe.events, "model_create", "model_create", "director");
        assertBracket(probe.events, "engine_initialize", "model_initialize", "director");
        for (String role : List.of("director", "narrator")) {
            assertBracket(probe.events, "open_" + role, "role_open", role);
            assertBracket(probe.events, "start_" + role, "role_start", role);
            assertBracket(probe.events, "close_" + role, "role_close", role);
        }
        assertBracket(probe.events, "engine_close", "model_close", "none");
        assertBracket(probe.events, "commit", "native_commit", "none");
        assertTrue(probe.events.indexOf("mark_native_prepare_before_none") < probe.events.indexOf("native_prepare"));
        assertTrue(probe.events.indexOf("native_finished") < probe.events.indexOf("mark_native_prepare_after_none"));
        assertFalse(probe.events.stream().filter(value -> value.startsWith("mark_")).anyMatch(value -> value.contains("PRIVATE")));
    }
    @Test public void checkpointFailureAtEveryWorkAndCloseBoundaryStillCleansAndNeverCommits() throws Exception {
        for (String failedPhase : List.of("native_create_before", "native_create_after", "native_submit_before", "native_submit_after",
                "native_prepare_before", "native_prepare_after", "model_create_before", "model_create_after",
                "model_initialize_before", "model_initialize_after", "role_open_before", "role_open_after",
                "role_start_before", "role_start_after", "role_drain_before", "role_drain_after",
                "role_close_before", "role_close_after", "native_respond_before", "native_respond_after",
                "model_close_before", "model_close_after", "native_commit_before")) {
            Probe probe = new Probe(); Model model = new Model(probe); List<String> marks = new CopyOnWriteArrayList<>();
            PlayRunner.Checkpoints failing = (phase, role) -> {
                marks.add(phase); if (phase.equals(failedPhase)) throw new IOException("PRIVATE persistence detail");
            };
            IOException failure = assertThrows(failedPhase, IOException.class,
                () -> new PlayRunner(probe, () -> model, new JsonObject(), 3000, 100, failing).run("gift"));
            assertEquals("phase_checkpoint_failed", failure.getMessage());
            assertTrue(failedPhase, marks.contains(failedPhase)); assertEquals(0, probe.commits);
            assertTrue(probe.closed); assertEquals(0, probe.reopens);
            assertEquals("Every returned Conversation must close", model.opens, probe.conversationsClosed);
            if (marks.contains("model_create_after")) assertEquals(1, probe.modelCloses);
            if (probe.preparation != null) assertFalse(probe.preparation.isAlive());
            assertEquals("No later checkpoint may pass a sticky failure", failedPhase, marks.get(marks.size() - 1));
        }
    }
    @Test public void persistenceFailureDoesNotBypassAnUndrainedSdkOwnershipFence() throws Exception {
        Probe probe = new Probe(); Model model = new Model(probe); model.neverDrain = true; JsonObject metrics = new JsonObject();
        PlayRunner.Checkpoints failing = (phase, role) -> { if (phase.equals("role_start_after")) throw new IOException("PRIVATE persistence"); };
        assertThrows(WarmRunner.Undrained.class, () -> new PlayRunner(probe, () -> model, metrics, 3000, 1, failing).run("gift"));
        assertEquals(0, probe.commits); assertEquals(0, probe.modelCloses); assertEquals(0, probe.conversationsClosed);
        assertTrue(metrics.get("cleanup_requires_process_termination").getAsBoolean()); assertTrue(probe.closed);
    }
    @Test public void postCommitCheckpointFailureRemainsUncertainInsteadOfClaimingNoCommit() throws Exception {
        Probe probe = new Probe(); Model model = new Model(probe);
        PlayRunner.Checkpoints failing = (phase, role) -> { if (phase.equals("native_commit_after")) throw new IOException("PRIVATE persistence"); };
        assertThrows(IOException.class, () -> new PlayRunner(probe, () -> model, new JsonObject(), 3000, 100, failing).run("gift"));
        assertEquals(1, probe.commits); assertEquals(1, probe.receipts.size()); assertEquals(0, probe.reopens); assertTrue(probe.closed);
    }
    @Test public void cleanupJournalFailureRetainsTheDistinctOriginalRejectionOrCancellationPrivately() throws Exception {
        for (boolean cancelling : List.of(false, true)) {
            Probe probe = new Probe(); Model model = new Model(probe);
            probe.rejectResponse = !cancelling; model.activeOutput = cancelling;
            PlayRunner.Checkpoints failing = (phase, role) -> { if (phase.equals("model_close_before")) throw new IOException("PRIVATE journal"); };
            IOException failure = assertThrows(IOException.class, () -> new PlayRunner(probe, () -> model, new JsonObject(), 3000, 100, failing)
                .run(cancelling ? "cancel" : "gift"));
            assertEquals(1, failure.getSuppressed().length);
            assertEquals(cancelling ? "Cancelled" : "HostRejected", failure.getSuppressed()[0].getClass().getSimpleName());
            assertEquals(0, probe.commits); assertEquals(1, probe.modelCloses); assertEquals(model.opens, probe.conversationsClosed);
            assertTrue(probe.closed); assertFalse(probe.preparation.isAlive());
        }
    }
    @Test public void engineCloseUncertaintyRetainsOriginalRejectionAndJournalFailure() throws Exception {
        Probe probe = new Probe(); probe.rejectResponse = true;
        Model model = new Model(probe); model.failEngineClose = true; JsonObject metrics = new JsonObject();
        PlayRunner.Checkpoints failing = (phase, role) -> { if (phase.equals("model_close_before")) throw new IOException("PRIVATE journal"); };
        WarmRunner.Undrained failure = assertThrows(WarmRunner.Undrained.class,
            () -> new PlayRunner(probe, () -> model, metrics, 3000, 100, failing).run("gift"));
        assertEquals("HostRejected", failure.getSuppressed()[0].getSuppressed()[0].getClass().getSimpleName());
        assertEquals("phase_checkpoint_failed", failure.getSuppressed()[1].getMessage());
        assertTrue(metrics.get("cleanup_requires_process_termination").getAsBoolean());
        assertEquals(0, probe.commits); assertTrue(probe.closed); assertFalse(probe.preparation.isAlive());
    }
    @Test public void maximalTwoTurnThreeRoleTraceAndOuterMarkersFitTheDiagnosticBudget() throws Exception {
        Probe probe = new Probe(); probe.roles.clear(); probe.roles.addAll(List.of("director", "director", "narrator"));
        Path parent = PhaseJournalTest.directory(); long large = Long.MAX_VALUE - 1000;
        PhaseJournal.Identity identity = new PhaseJournal.Identity(Integer.MAX_VALUE, Integer.MAX_VALUE, large, Long.MAX_VALUE, large);
        PhaseJournal.Clock clock = new PhaseJournal.Clock() { public long elapsedMs() { return large; } public long wallMs() { return Long.MAX_VALUE; } };
        try (PhaseJournal journal = new PhaseJournal(parent, PhaseJournalTest.SESSION, identity, clock)) {
            journal.mark("instrumentation_start", "none");
            JsonObject result = new PlayRunner(probe, () -> new Model(probe), new JsonObject(), 3000, 100, journal).run("spent");
            journal.mark("terminal", "none");
            assertEquals("committed", result.get("outcome").getAsString());
            assertEquals(92, PhaseJournal.read(parent, PhaseJournalTest.SESSION).records.size());
        }
        assertTrue(Files.size(parent.resolve(PhaseJournal.FILE)) > 0);
        assertTrue(Files.size(parent.resolve(PhaseJournal.FILE)) <= PhaseJournal.MAX_BYTES);
    }
    @Test public void ordinaryGiftObservesOutputForEveryRoleAndReportsOnlyTypedTerminalMetadata() throws Exception {
        Probe probe = new Probe(); Model model = new Model(probe); model.outputObservation = true;
        model.terminalObservation = new RoleObservation(2, 12, "none", true, 0, 0);
        JsonObject result = run(probe, model, "gift");
        assertEquals("committed", result.get("outcome").getAsString()); assertTrue(result.get("first_output_observed").getAsBoolean());
        for (JsonElement value : generations(result)) {
            JsonObject row = value.getAsJsonObject(); assertEquals("observed", row.get("output_observation").getAsString());
            assertTrue(row.get("first_output_elapsed_ms").getAsDouble() >= 0); assertTrue(row.get("first_output_elapsed_ms").getAsDouble() <= 180000);
            JsonObject observation = row.getAsJsonObject("terminal_observation"); assertEquals(8, observation.size());
            assertEquals(0, observation.get("sdk_input_tokens").getAsInt()); assertEquals(0, observation.get("sdk_output_tokens").getAsInt());
            assertTrue(observation.get("configuration").isJsonNull()); assertFalse(observation.toString().contains("PRIVATE"));
        }
        assertEquals(2, model.terminalQueries); assertTrue(model.outputQueries >= 4);
        assertTrue(probe.events.indexOf("observe_terminal_director") < probe.events.indexOf("close_director"));
    }
    @Test public void unavailableAndKnownNoOutputAreDifferentAndCannotInventFirstOutputTime() throws Exception {
        for (Boolean observation : new Boolean[] {null, false}) {
            Probe probe = new Probe(); Model model = new Model(probe); model.outputObservation = observation;
            model.terminalQueryFails = Boolean.FALSE.equals(observation);
            JsonObject result = run(probe, model, "gift"); assertEquals("committed", result.get("outcome").getAsString());
            assertFalse(result.get("first_output_observed").getAsBoolean());
            for (JsonElement value : generations(result)) {
                JsonObject row = value.getAsJsonObject();
                assertEquals(observation == null ? "unknown" : "not_observed", row.get("output_observation").getAsString());
                assertTrue(row.get("first_output_elapsed_ms").isJsonNull()); assertTrue(row.get("terminal_observation").isJsonNull());
            }
        }
    }
    @Test public void positiveTerminalBufferIsObservedEvenWhenOutputProbeIsUnavailableOrPreviouslyEmpty() throws Exception {
        for (Boolean output : new Boolean[] {null, false}) {
            Probe probe = new Probe(); Model model = new Model(probe); model.outputObservation = output;
            model.terminalObservation = new RoleObservation(1, 1, "none", false, null, null);
            JsonObject result = run(probe, model, "gift"); assertEquals("committed", result.get("outcome").getAsString());
            for (JsonElement value : generations(result)) {
                JsonObject row = value.getAsJsonObject(); assertEquals("observed", row.get("output_observation").getAsString());
                assertFalse(row.get("first_output_elapsed_ms").isJsonNull());
                assertEquals(1, row.getAsJsonObject("terminal_observation").get("buffered_text_bytes").getAsInt());
            }
            assertTrue(result.get("first_output_observed").getAsBoolean()); assertEquals(1, probe.commits);
        }
    }
    @Test public void outputAndTerminalDiagnosticFailuresDoNotRejectAnOtherwiseAcceptedGift() throws Exception {
        Probe probe = new Probe(); Model model = new Model(probe); model.outputQueryFails = true; model.terminalQueryFails = true;
        JsonObject result = run(probe, model, "gift"); assertEquals("committed", result.get("outcome").getAsString());
        assertEquals(1, probe.commits); assertEquals(2, probe.conversationsClosed); assertEquals(1, probe.modelCloses);
        for (JsonElement value : generations(result)) {
            JsonObject row = value.getAsJsonObject(); assertEquals("unknown", row.get("output_observation").getAsString());
            assertTrue(row.get("first_output_elapsed_ms").isJsonNull()); assertTrue(row.get("terminal_observation").isJsonNull());
        }
        assertFalse(result.toString().contains("PRIVATE")); assertFalse(probe.preparation.isAlive());
    }
    @Test public void diagnosticFailureKeepsPositiveEvidenceButMakesOnlyNegativeEvidenceUnknown() throws Exception {
        for (boolean positive : new boolean[] {false, true}) {
            Probe probe = new Probe(); Model model = new Model(probe); model.outputObservation = positive; model.outputQueryFailsAfterFirst = true;
            JsonObject result = run(probe, model, "gift"); JsonObject row = generations(result).get(0).getAsJsonObject();
            assertEquals(positive ? "observed" : "unknown", row.get("output_observation").getAsString());
            assertEquals(positive, !row.get("first_output_elapsed_ms").isJsonNull());
            assertEquals(positive, result.get("first_output_observed").getAsBoolean()); assertEquals(1, probe.commits);
        }
    }
    @Test public void terminalOutputIsObservedBeforeCloseEvenWhenOrdinaryWaitWasInitiallyEmpty() throws Exception {
        Probe probe = new Probe(); Model model = new Model(probe); model.observeOnTerminal = true;
        JsonObject result = run(probe, model, "gift"); assertTrue(result.get("first_output_observed").getAsBoolean());
        for (JsonElement value : generations(result)) assertEquals("observed", value.getAsJsonObject().get("output_observation").getAsString());
        assertEquals(2, model.terminalQueries); assertEquals(2, probe.conversationsClosed);
    }
    @Test public void expiredDeadlineStillObservesKnownCleanupDrainWithoutChangingTimeoutOrCommitting() throws Exception {
        Probe probe = new Probe(); Model model = new Model(probe); model.observeOnCancel = true;
        PlayRunner.Checkpoints expireAfterStart = (phase, role) -> { if (phase.equals("role_start_after")) try { Thread.sleep(600); } catch (InterruptedException interrupted) { Thread.currentThread().interrupt(); throw new IOException("synthetic interrupted"); } };
        JsonObject result = new PlayRunner(probe, () -> model, new JsonObject(), 500, 100, expireAfterStart).run("gift");
        assertEquals("timeout", result.get("error").getAsString()); assertEquals(0, probe.commits);
        JsonObject row = generations(result).get(0).getAsJsonObject(); assertEquals("observed", row.get("output_observation").getAsString());
        assertTrue(row.get("first_output_elapsed_ms").getAsDouble() >= 500); assertEquals(1, model.terminalQueries);
        assertEquals(1, probe.conversationsClosed); assertEquals(1, probe.modelCloses); assertFalse(probe.preparation.isAlive());
    }
    @Test public void startFailureStillDrainsAndObservesBeforeCloseWhileDiagnosticFailureCannotMaskPrimary() throws Exception {
        Probe probe = new Probe(); Model model = new Model(probe); model.failStart = true; model.observeOnCancel = true; model.terminalQueryFails = true;
        JsonObject result = run(probe, model, "gift"); assertEquals("generation_failed", result.get("error").getAsString());
        assertEquals(0, probe.commits); assertEquals(1, model.terminalQueries); assertEquals(1, probe.conversationsClosed);
        JsonObject row = generations(result).get(0).getAsJsonObject(); assertEquals("observed", row.get("output_observation").getAsString());
        assertTrue(row.get("terminal_observation").isJsonNull()); assertFalse(probe.preparation.isAlive());
    }
    @Test public void undrainedOwnershipNeverTriggersTerminalMetadataOrPostCloseQueries() throws Exception {
        Probe probe = new Probe(); Model model = new Model(probe); model.neverDrain = true;
        model.terminalObservation = new RoleObservation(0, 0, "none", false, null, null);
        assertThrows(WarmRunner.Undrained.class, () -> new PlayRunner(probe, () -> model, new JsonObject(), 200, 1).run("gift"));
        assertEquals(0, model.terminalQueries); assertEquals(0, probe.conversationsClosed); assertEquals(0, probe.modelCloses);
        assertEquals(0, probe.commits); assertTrue(probe.closed); assertFalse(probe.preparation.isAlive());
    }
    @Test public void legacyCancelPositiveStillCountsWithoutRequiringTheNewOptionalAdapter() throws Exception {
        Probe probe = new Probe(); Model model = new Model(probe); model.activeOutput = true;
        JsonObject result = run(probe, model, "cancel"); assertEquals("cancelled", result.get("outcome").getAsString());
        assertEquals("observed", generations(result).get(0).getAsJsonObject().get("output_observation").getAsString());
        assertTrue(result.get("first_output_observed").getAsBoolean()); assertEquals(0, probe.commits);
    }
    private static JsonArray generations(JsonObject result) { return result.getAsJsonArray("turns").get(0).getAsJsonObject().getAsJsonArray("generations"); }
    private static void assertBracket(List<String> events, String action, String phase, String role) {
        int before = events.indexOf("mark_" + phase + "_before_" + role), actual = events.indexOf(action),
            after = events.indexOf("mark_" + phase + "_after_" + role);
        assertTrue(phase, before >= 0 && before < actual && actual < after);
    }
    private static JsonObject ok(JsonObject data) { JsonObject reply = object("status", "ok"); reply.addProperty("version", 1); reply.add("data", data); return reply; }
    private static JsonObject number(String key, long value) { JsonObject result = new JsonObject(); result.addProperty(key, value); return result; }
    private static JsonObject object(Object... values) {
        JsonObject result = new JsonObject();
        for (int i = 0; i < values.length; i += 2) {
            if (values[i + 1] instanceof JsonElement) result.add((String) values[i], ((JsonElement) values[i + 1]).deepCopy());
            else result.addProperty((String) values[i], (String) values[i + 1]);
        }
        return result;
    }
}

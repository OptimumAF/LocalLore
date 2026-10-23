// Copyright 2026 LocalLore contributors.
// SPDX-License-Identifier: Apache-2.0
package org.locallore.runtimebench.litert;

import static org.junit.Assert.*;
import com.google.gson.JsonObject;
import java.io.IOException;
import java.util.ArrayList;
import java.util.List;
import org.junit.Test;

/** Ownership/callback ordering with no model, native engine, device or generation. */
public class WarmRunnerTest {
    private static class Exchange implements WarmRunner.Exchange {
        boolean cancelled, cancelAfterFirst, waitSecond, invalidDuringGeneration;
        int polls, published;
        final List<JsonObject> results = new ArrayList<>();
        @Override public void check() throws Exception { if (invalidDuringGeneration) throw new IOException("invalid_request"); }
        @Override public boolean cancelled() { return cancelled; }
        @Override public Request poll(int step) throws Exception {
            polls++;
            if (step == 2 && waitSecond) { cancelled = true; return null; }
            return Request.parse(WarmExchangeTest.request(step == 1 ? "director" : "narrator"));
        }
        @Override public void publish(int step, JsonObject result) {
            published++; results.add(result);
            if (step == 1 && cancelAfterFirst) cancelled = true;
        }
    }
    private static class Model implements WarmRunner.Model {
        final Exchange exchange;
        final List<String> events = new ArrayList<>();
        int opened, closed, resultReads;
        boolean failInitialize, failOpen, failResult, cancelDuring, cancelOnTerminal, neverDrain,
            failStart, failRoleClose, failModelClose, cancelOnClose, invalidDuring;
        Model(Exchange exchange) { this.exchange = exchange; }
        @Override public void initialize() throws Exception {
            events.add("engine_initialize"); if (failInitialize) throw new IOException("model_load_failed");
        }
        @Override public WarmRunner.Role open(Request request) throws Exception {
            events.add("open_" + request.role); if (failOpen) throw new IOException("runtime_failed");
            opened++;
            return new WarmRunner.Role() {
                boolean cancelled;
                @Override public void start() throws Exception {
                    events.add("start_" + request.role); if (failStart) throw new IOException("runtime_failed");
                }
                @Override public boolean await(long milliseconds) {
                    if (cancelDuring && !cancelled) { exchange.cancelled = true; return false; }
                    if (invalidDuring && !cancelled) { exchange.invalidDuringGeneration = true; return false; }
                    if (neverDrain) return false;
                    if (cancelOnTerminal) exchange.cancelled = true;
                    events.add("terminal_" + request.role); return true;
                }
                @Override public void cancel() { events.add("cancel_" + request.role); cancelled = true; }
                @Override public JsonObject result(double loadMs) throws Exception {
                    resultReads++;
                    if (failResult) throw new IOException("generation_failed");
                    JsonObject result = new JsonObject();
                    result.addProperty("load_ms", loadMs); result.addProperty("text", "synthetic private " + request.role);
                    return result;
                }
                @Override public void close() throws Exception {
                    events.add("close_" + request.role);
                    if (failRoleClose) throw new IOException("runtime_failed");
                    closed++;
                    if (cancelOnClose) exchange.cancelled = true;
                }
            };
        }
        @Override public void close() throws Exception {
            events.add("engine_close"); if (failModelClose) throw new IOException("runtime_failed");
        }
    }
    @Test public void oneEngineTwoFreshOwnersCloseBeforePublishAndSecondLoadIsZero() throws Exception {
        Model[] owner = new Model[1];
        Exchange exchange = new Exchange() {
            @Override public void publish(int step, JsonObject result) {
                assertEquals(step, owner[0].closed);
                assertEquals(step == 1 ? "close_director" : "close_narrator", owner[0].events.get(owner[0].events.size() - 1));
                super.publish(step, result);
                assertEquals(step == 1 ? "director" : "narrator", result.get("text").getAsString().substring("synthetic private ".length()));
            }
        };
        Model model = new Model(exchange); JsonObject metrics = new JsonObject();
        owner[0] = model;
        new WarmRunner(model, exchange, metrics).run();
        assertEquals(List.of("engine_initialize", "open_director", "start_director", "terminal_director", "close_director",
            "open_narrator", "start_narrator", "terminal_narrator", "close_narrator", "engine_close"), model.events);
        assertEquals(2, model.opened); assertEquals(2, model.closed); assertEquals(2, exchange.published);
        assertTrue(exchange.results.get(0).get("load_ms").getAsDouble() >= 0);
        assertEquals(0.0, exchange.results.get(1).get("load_ms").getAsDouble(), 0);
        assertEquals(2, metrics.get("warm_roles").getAsInt()); assertTrue(metrics.get("warm_engine_reused").getAsBoolean());
        assertFalse(metrics.get("warm_cancel_observed").getAsBoolean());
    }
    @Test public void cancellationBeforeLoadDoesNotOpenConversation() {
        Exchange exchange = new Exchange(); exchange.cancelled = true;
        Model model = new Model(exchange); JsonObject metrics = new JsonObject();
        assertThrows(WarmRunner.Failure.class, () -> new WarmRunner(model, exchange, metrics).run());
        assertEquals(List.of("engine_close"), model.events); assertEquals(0, exchange.published);
        assertTrue(metrics.get("warm_cancel_observed").getAsBoolean());
    }
    @Test public void activeCancelDrainsBeforeOwnerCloseAndDiscardsOutput() {
        Exchange exchange = new Exchange(); Model model = new Model(exchange); model.cancelDuring = true;
        JsonObject metrics = new JsonObject();
        assertThrows(WarmRunner.Failure.class, () -> new WarmRunner(model, exchange, metrics).run());
        assertEquals(List.of("engine_initialize", "open_director", "start_director", "cancel_director", "terminal_director",
            "close_director", "engine_close"), model.events);
        assertEquals(0, model.resultReads); assertEquals(0, exchange.published); assertEquals(1, model.opened);
        assertTrue(metrics.get("cancel_called").getAsBoolean()); assertTrue(metrics.get("terminal_callback").getAsBoolean());
        assertTrue(metrics.get("cancelled_text_discarded").getAsBoolean());
        assertFalse(metrics.get("warm_engine_reused").getAsBoolean());
    }
    @Test public void cancelAtTerminalCallbackDiscardsBeforeResultRead() {
        Exchange exchange = new Exchange(); Model model = new Model(exchange); model.cancelOnTerminal = true;
        assertThrows(WarmRunner.Failure.class, () -> new WarmRunner(model, exchange, new JsonObject()).run());
        assertEquals(0, exchange.published); assertEquals(0, model.resultReads); assertEquals(1, model.closed);
        assertFalse(model.events.contains("cancel_director"));
    }
    @Test public void cancelDuringOwnerCloseDiscardsBeforeResultPublication() {
        Exchange exchange = new Exchange(); Model model = new Model(exchange); model.cancelOnClose = true;
        assertThrows(WarmRunner.Failure.class, () -> new WarmRunner(model, exchange, new JsonObject()).run());
        assertEquals(0, exchange.published); assertEquals(1, model.closed); assertEquals(1, model.resultReads);
    }
    @Test public void cancelBetweenRolesNeverCreatesNarratorOrReusesEngine() {
        Exchange exchange = new Exchange(); exchange.cancelAfterFirst = true;
        Model model = new Model(exchange); JsonObject metrics = new JsonObject();
        assertThrows(WarmRunner.Failure.class, () -> new WarmRunner(model, exchange, metrics).run());
        assertEquals(1, exchange.published); assertEquals(1, model.opened); assertEquals(1, model.closed);
        assertEquals(1, metrics.get("warm_roles").getAsInt()); assertFalse(metrics.get("warm_engine_reused").getAsBoolean());
    }
    @Test public void cancellationWhileWaitingForHostStepTwoClosesModel() {
        Exchange exchange = new Exchange(); exchange.waitSecond = true;
        Model model = new Model(exchange); JsonObject metrics = new JsonObject();
        assertThrows(WarmRunner.Failure.class, () -> new WarmRunner(model, exchange, metrics).run());
        assertEquals(1, model.opened); assertEquals("engine_close", model.events.get(model.events.size() - 1));
        assertTrue(metrics.get("warm_cancel_observed").getAsBoolean());
    }
    @Test public void undrainedCancelNeverDeletesConversationOrEngine() {
        Exchange exchange = new Exchange(); Model model = new Model(exchange); model.cancelDuring = true; model.neverDrain = true;
        JsonObject metrics = new JsonObject();
        assertThrows(WarmRunner.Undrained.class, () -> new WarmRunner(model, exchange, metrics, 1000, 1).run());
        assertEquals(0, model.closed); assertFalse(model.events.contains("engine_close")); assertEquals(0, exchange.published);
        assertTrue(metrics.get("cleanup_requires_process_termination").getAsBoolean());
    }
    @Test public void launchExceptionStillDrainsBeforeClose() {
        Exchange exchange = new Exchange(); Model model = new Model(exchange); model.failStart = true;
        assertThrows(IOException.class, () -> new WarmRunner(model, exchange, new JsonObject()).run());
        assertTrue(model.events.indexOf("cancel_director") < model.events.indexOf("close_director"));
        assertTrue(model.events.indexOf("terminal_director") < model.events.indexOf("close_director"));
        assertEquals(0, exchange.published);
    }
    @Test public void malformedExchangeDuringActiveGenerationDrainsBeforeClose() {
        Exchange exchange = new Exchange(); Model model = new Model(exchange); model.invalidDuring = true;
        assertThrows(IOException.class, () -> new WarmRunner(model, exchange, new JsonObject()).run());
        assertTrue(model.events.contains("cancel_director")); assertEquals(1, model.closed); assertEquals(0, exchange.published);
    }
    @Test public void roleCloseFailureRetainsEngineAndRequiresProcessTermination() {
        Exchange exchange = new Exchange(); Model model = new Model(exchange); model.failRoleClose = true;
        JsonObject metrics = new JsonObject();
        assertThrows(WarmRunner.Undrained.class, () -> new WarmRunner(model, exchange, metrics).run());
        assertFalse(model.events.contains("engine_close")); assertEquals(0, exchange.published);
        assertTrue(metrics.get("cleanup_requires_process_termination").getAsBoolean());
    }
    @Test public void engineCloseFailureRequiresProcessTermination() {
        Exchange exchange = new Exchange(); Model model = new Model(exchange); model.failModelClose = true;
        JsonObject metrics = new JsonObject();
        assertThrows(WarmRunner.Undrained.class, () -> new WarmRunner(model, exchange, metrics).run());
        assertTrue(metrics.get("cleanup_requires_process_termination").getAsBoolean());
    }
    @Test public void generationErrorClosesOwnersWithoutPublishingOrOpeningNarrator() {
        Exchange exchange = new Exchange(); Model model = new Model(exchange); model.failResult = true;
        assertThrows(IOException.class, () -> new WarmRunner(model, exchange, new JsonObject()).run());
        assertEquals(1, model.closed); assertEquals(1, model.opened); assertEquals(0, exchange.published);
        assertEquals("engine_close", model.events.get(model.events.size() - 1));
    }
    @Test public void loadAndOpenErrorsNeverInventBalancedRoleOrResult() {
        for (boolean initialization : new boolean[]{true, false}) {
            Exchange exchange = new Exchange(); Model model = new Model(exchange);
            model.failInitialize = initialization; model.failOpen = !initialization;
            assertThrows(IOException.class, () -> new WarmRunner(model, exchange, new JsonObject()).run());
            assertEquals(0, model.opened); assertEquals(0, exchange.published);
            assertEquals("engine_close", model.events.get(model.events.size() - 1));
        }
    }
    @Test public void wholeRunBudgetExpiryBeforeLoadProducesNoRoleOrPublication() {
        Exchange exchange = new Exchange(); Model model = new Model(exchange);
        WarmRunner.Failure failure = assertThrows(WarmRunner.Failure.class,
            () -> new WarmRunner(model, exchange, new JsonObject(), 0, 1).run());
        assertEquals("timeout", failure.category); assertEquals(0, model.opened); assertEquals(0, exchange.published);
    }
}

// Copyright 2026 LocalLore contributors.
// SPDX-License-Identifier: Apache-2.0
package org.locallore.runtimebench.litert;

import com.google.gson.JsonObject;
import java.util.concurrent.TimeUnit;

/** Exactly one loaded model, two fresh conversations; native ownership is explicit. */
final class WarmRunner {
    interface Exchange {
        void check() throws Exception;
        boolean cancelled() throws Exception;
        Request poll(int step) throws Exception;
        void publish(int step, JsonObject result) throws Exception;
    }
    interface Model extends AutoCloseable {
        void initialize() throws Exception;
        Role open(Request request) throws Exception;
        @Override void close() throws Exception;
    }
    interface Role extends AutoCloseable {
        void start() throws Exception;
        boolean await(long milliseconds) throws Exception;
        default boolean hasOutput() { return false; }
        void cancel() throws Exception;
        JsonObject result(double loadMs) throws Exception;
        @Override void close() throws Exception;
    }
    static class Failure extends Exception {
        final String category;
        Failure(String category) { super(category); this.category = category; }
    }
    static final class Undrained extends Exception {
        Undrained() { super("runtime_failed"); }
    }
    private final Model model;
    private final Exchange exchange;
    private final JsonObject metrics;
    private final long budgetMs, drainMs;
    private long deadline;

    WarmRunner(Model model, Exchange exchange, JsonObject metrics) { this(model, exchange, metrics, 60000, 5000); }
    WarmRunner(Model model, Exchange exchange, JsonObject metrics, long budgetMs, long drainMs) {
        this.model = model; this.exchange = exchange; this.metrics = metrics;
        this.budgetMs = budgetMs; this.drainMs = drainMs;
        metrics.addProperty("warm_roles", 0);
        metrics.addProperty("warm_engine_reused", false);
        metrics.addProperty("warm_cancel_observed", false);
    }
    void run() throws Exception {
        deadline = System.nanoTime() + TimeUnit.MILLISECONDS.toNanos(budgetMs);
        boolean reusable = true;
        try {
            check();
            Request first = waitRequest(1);
            long loading = System.nanoTime();
            model.initialize();
            double loadMs = Math.min(180000.0, (System.nanoTime() - loading) / 1000000.0);
            for (int step = 1; step <= 2; step++) {
                check();
                Request request = step == 1 ? first : waitRequest(step);
                Role role = model.open(request);
                boolean active = false, drained = false;
                JsonObject result;
                try {
                    check();
                    // An exception from start may still have launched native work.
                    active = true;
                    role.start();
                    while (!role.await(25)) check();
                    drained = true;
                    metrics.addProperty("terminal_callback", true);
                    check();
                    result = role.result(step == 1 ? loadMs : 0.0);
                } finally {
                    if (active && !drained) {
                        try {
                            role.cancel();
                            metrics.addProperty("cancel_called", true);
                            drained = role.await(drainMs);
                            if (drained) metrics.addProperty("terminal_callback", true);
                        } catch (Exception failure) { drained = false; }
                    }
                    if (active && !drained) { reusable = false; throw new Undrained(); }
                    // A close failure leaves ownership uncertain; don't delete its Engine.
                    try { role.close(); } catch (Exception failure) { reusable = false; throw new Undrained(); }
                }
                check();
                exchange.publish(step, result);
                metrics.addProperty("warm_roles", step);
                metrics.addProperty("warm_engine_reused", step == 2);
            }
            check();
        } catch (Undrained failure) {
            reusable = false;
            throw failure;
        } finally {
            if (reusable) {
                try { model.close(); }
                catch (Exception failure) {
                    metrics.addProperty("cleanup_requires_process_termination", true);
                    throw new Undrained();
                }
            } else metrics.addProperty("cleanup_requires_process_termination", true);
        }
    }
    private Request waitRequest(int step) throws Exception {
        while (true) {
            check();
            Request request = exchange.poll(step);
            if (request != null) return request;
            Thread.sleep(25);
        }
    }
    private void check() throws Exception {
        exchange.check();
        if (exchange.cancelled()) {
            metrics.addProperty("warm_cancel_observed", true);
            metrics.addProperty("cancelled_text_discarded", true);
            throw new Failure("runtime_failed");
        }
        if (System.nanoTime() >= deadline) throw new Failure("timeout");
    }
}

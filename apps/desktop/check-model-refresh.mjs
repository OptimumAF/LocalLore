// Deterministic actual-controller regression: terminal status must precede action completion.
// No model, native executable, real intervals, UI control or network is involved.
import assert from "node:assert/strict";
import { build } from "esbuild";
import { mkdir, writeFile } from "node:fs/promises";
import { fileURLToPath, pathToFileURL } from "node:url";
import path from "node:path";
import { randomUUID } from "node:crypto";

const directory =
    process.env.LOCALLORE_CHECK_OUTPUT_DIR ??
    fileURLToPath(new URL("./artifacts/checks/", import.meta.url));
await mkdir(directory, { recursive: true });
const target = path.join(directory, `model-refresh-${randomUUID()}.mjs`);
const compiled = await build({
    entryPoints: [
        fileURLToPath(new URL("./ui/controller.ts", import.meta.url)),
    ],
    bundle: true,
    platform: "node",
    format: "esm",
    write: false,
});
await writeFile(target, compiled.outputFiles[0].contents);
const { Controller } = await import(pathToFileURL(target).href);
function deferred() {
    let resolve, reject;
    const promise = new Promise((a, b) => {
        resolve = a;
        reject = b;
    });
    return { promise, resolve, reject };
}
async function drain() {
    for (let i = 0; i < 20; i++) await Promise.resolve();
}
const state = (phase, loaded, error = null) => ({
    operation_id: 7,
    resident: loaded,
    phase,
    percent: loaded ? 100 : 0,
    imported: true,
    loaded,
    error,
    profile: null,
});

async function scenario(succeeds, staleRejects) {
    const realSetInterval = globalThis.setInterval,
        realClearInterval = globalThis.clearInterval;
    const intervals = new Map();
    let next = 0;
    globalThis.setInterval = (callback) => {
        const id = ++next;
        intervals.set(id, callback);
        return id;
    };
    globalThis.clearInterval = (id) => {
        intervals.delete(id);
    };
    const tick = () => {
        for (const callback of [...intervals.values()]) callback();
    };
    const action = deferred(),
        reads = [];
    let initializing = true;
    const gateway = {
        async native(command) {
            if (command === "model_load") return action.promise;
            assert.equal(command, "model_status");
            if (initializing) return state("unloaded", false);
            const read = deferred();
            reads.push(read);
            return read.promise;
        },
        async call(command) {
            assert.equal(command.op, "close");
            return {};
        },
    };
    const c = new Controller(gateway);
    let operation, manual;
    try {
        await c.refreshModel();
        initializing = false;
        operation = c.modelAction("model_load");
        tick();
        await drain();
        assert.equal(
            reads.length,
            1,
            "a loading poll is deliberately held in flight",
        );
        if (succeeds) action.resolve(state("loaded", true));
        else action.reject(new Error("Runtime"));
        await drain();
        assert.equal(
            reads.length,
            2,
            "native settlement must request definitive terminal status",
        );
        if (!staleRejects) reads[0].resolve(state("loading", false));
        await drain();
        assert.equal(
            c.get().model.phase,
            "unloaded",
            "older loading response cannot replace the newer final read",
        );
        let manualSettled = false;
        manual = c.refreshModel().then(() => { manualSettled = true; });
        tick();
        await drain();
        assert.equal(reads.length, 2, "manual refresh joins the terminal read");
        assert.equal(manualSettled, false);
        assert.equal(c.get().modelBusy, true);
        reads[1].resolve(
            state(
                succeeds ? "loaded" : "failed",
                succeeds,
                succeeds ? null : "Runtime",
            ),
        );
        await Promise.all([operation, manual]);
        if (staleRejects) reads[0].reject(new Error("Timeout"));
        await drain();
        assert.equal(c.get().modelBusy, false);
        assert.equal(
            c.get().model.phase,
            succeeds ? "loaded" : "failed",
            "awaited modelAction must publish terminal state before resolving",
        );
        assert.equal(
            c.get().model.loaded,
            succeeds,
            "action completion cannot expose stale loading/unloaded state",
        );
        assert.equal(c.get().visibleError, succeeds ? null : "Runtime");
        assert.equal(
            reads.length,
            2,
            "settled action must not permit a newer interval to preempt its terminal read",
        );
        assert.equal(
            intervals.size,
            0,
            "no action polling interval may survive settlement",
        );
    } finally {
        action.resolve(state("loaded", true));
        for (const read of reads)
            read.resolve(
                state(
                    succeeds ? "loaded" : "failed",
                    succeeds,
                    succeeds ? null : "Runtime",
                ),
            );
        await drain();
        await operation?.catch(() => {});
        await manual?.catch(() => {});
        await c.dispose();
        globalThis.setInterval = realSetInterval;
        globalThis.clearInterval = realClearInterval;
    }
}
async function cancelPublication() {
    const setInterval = globalThis.setInterval, clearInterval = globalThis.clearInterval;
    globalThis.setInterval = () => 1;
    globalThis.clearInterval = () => {};
    const idle = deferred(), load = deferred(), cancelReply = deferred();
    const sent = [], readyStates = [];
    let status = state("unloaded", false);
    const c = new Controller({
        async native(command, args) {
            if (command === "model_load") return load.promise;
            if (command === "model_cancel") {
                sent.push(args);
                return cancelReply.promise;
            }
            assert.equal(command, "model_status");
            return status;
        },
        async call(command) {
            assert.equal(command.op, "close");
            return {};
        },
    });
    let cancellation, operation;
    const unsubscribe = c.subscribe(() => {
        const view = c.get();
        if (!view.modelCancelReady) return;
        readyStates.push([view.model.operation_id, view.model.phase, view.modelBusy]);
        if (!cancellation) cancellation = c.cancelModel();
    });
    try {
        await c.refreshModel();
        status = idle.promise;
        const previous = c.refreshModel();
        operation = c.modelAction("model_load");
        idle.reject(new Error("Timeout"));
        await previous;
        assert.equal(c.get().visibleError, null, "pre-action read error is stale");

        status = { ...state("loading", false), operation_id: 8 };
        await c.refreshModel();
        assert.deepEqual(readyStates, [[8, "loading", true]]);
        assert.deepEqual(sent, [{ operationId: 8 }]);

        status = { ...state("loading", false), operation_id: 9 };
        await c.refreshModel();
        assert.equal(c.get().modelCancelReady, false);
        await c.cancelModel();
        assert.deepEqual(sent, [{ operationId: 8 }], "foreign status cannot offer Cancel");

        cancelReply.reject(new Error("StaleModelOperation"));
        await cancellation;
        assert.equal(c.get().visibleError, null, "late cancel failure is stale");

        status = { ...state("loaded", true), operation_id: 9 };
        load.resolve(status);
        await operation;
        assert.equal(c.get().model.phase, "loaded");
        assert.equal(c.get().modelCancelReady, false);
    } finally {
        idle.resolve(state("unloaded", false));
        cancelReply.resolve({ status: "finished" });
        status = state("loaded", true);
        load.resolve(status);
        await Promise.allSettled([operation, cancellation]);
        unsubscribe();
        await c.dispose();
        globalThis.setInterval = setInterval;
        globalThis.clearInterval = clearInterval;
    }
}

const failures = [];
for (const succeeds of [true, false]) {
    for (const staleRejects of [true, false]) {
        try {
            await scenario(succeeds, staleRejects);
        } catch (error) {
            failures.push(
                `${succeeds ? "success" : "error"} settlement, stale ${staleRejects ? "error" : "reply"}: ${error.message}`,
            );
        }
    }
}
try {
    await cancelPublication();
} catch (error) {
    failures.push(`cancel publication: ${error.message}`);
}
assert.deepEqual(
    failures,
    [],
    "terminal model refresh must be authoritative on both native success and failure",
);
console.log(
    "PASS: model settlement owns the final read, stale success/errors are ignored, and Cancel follows the published operation.",
);

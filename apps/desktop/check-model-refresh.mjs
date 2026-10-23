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

async function scenario(succeeds) {
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
    let operation;
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
        reads[0].resolve(state("loading", false));
        await drain();
        assert.equal(
            c.get().model.phase,
            "unloaded",
            "older loading response cannot replace the newer final read",
        );
        tick();
        await drain();
        // With the bug, this tick starts a third read that supersedes the final read.
        // A correct controller stops polling before requesting its terminal status.
        reads[1].resolve(
            state(
                succeeds ? "loaded" : "failed",
                succeeds,
                succeeds ? null : "Runtime",
            ),
        );
        await operation;
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
        await c.dispose();
        globalThis.setInterval = realSetInterval;
        globalThis.clearInterval = realClearInterval;
    }
}
const failures = [];
for (const succeeds of [true, false]) {
    try {
        await scenario(succeeds);
    } catch (error) {
        failures.push(
            `${succeeds ? "success" : "error"} settlement: ${error.message}`,
        );
    }
}
assert.deepEqual(
    failures,
    [],
    "terminal model refresh must be authoritative on both native success and failure",
);
console.log(
    "PASS: native success/error stops interval polling before final refresh; older polls cannot overwrite or preempt terminal state.",
);

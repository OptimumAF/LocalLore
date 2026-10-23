// Actual-controller regression: real UnknownTurn recovery cannot inherit fake fault mode.
import { fileURLToPath } from "node:url";
import { build } from "esbuild";
import { mkdirSync, writeFileSync } from "node:fs";
import { randomUUID } from "node:crypto";
import assert from "node:assert/strict";
const dir = new URL("./artifacts/checks/", import.meta.url);
mkdirSync(dir, { recursive: true });
const file = new URL(`model-controller-${randomUUID()}.mjs`, dir);
const compiled = await build({
    entryPoints: [fileURLToPath(new URL("ui/controller.ts", import.meta.url))],
    bundle: true,
    platform: "node",
    format: "esm",
    write: false,
});
writeFileSync(file, compiled.outputFiles[0].contents);
const { Controller } = await import(file.href);
const scope = { story: "synthetic-real-recovery", branch: "main" };
const submitted = [];
let loaded = true;
const status = (phase, error = null) => ({
    scope,
    turn: submitted[0].turn,
    expected_revision: 0,
    phase,
    error,
    receipt: null,
});
const gateway = {
    async native(command) {
        assert.equal(command, "model_status");
        return {
            phase: loaded ? "loaded" : "unloaded",
            loaded,
            imported: true,
            resident: loaded,
            error: null,
            percent: 100,
            profile: null,
        };
    },
    async call(command) {
        if (command.op === "open") return { session: "s", scope, revision: 0 };
        if (command.op === "play_snapshot")
            return {
                scope,
                revision: 0,
                rules: "fantasy_v1",
                inventory: { potion: { quantity: 1 } },
                receipts: [],
                player: {
                    scope,
                    revision: 0,
                    observer: "player",
                    self_state: { name: "Rowan", energy: 2, location: "quay" },
                    facts: {},
                    beliefs: [],
                    observations: [],
                },
            };
        if (command.op === "inspect" || command.op === "close") return {};
        if (command.op === "free_text") {
            assert.equal(command.mode, undefined);
            submitted.push(command.request);
            if (submitted.length === 1) throw new Error("Transport");
            return status("queued");
        }
        if (command.op === "turn_status") throw new Error("UnknownTurn");
        if (command.op === "prepare") return status("failed", "Agency");
        throw new Error(`Unexpected${command.op}`);
    },
};
const c = new Controller(gateway);
await c.attach({ id: "s", scope, revision: 0, name: "Synthetic" });
c.setFakeMode("malformed");
await c.refreshModel();
c.setPlayMode("local");
c.setDraft("I give my last potion to Mira.");
await c.send();
assert.equal(c.get().visibleError, "TransportUnknown");
await c.retry();
assert.equal(submitted.length, 2);
assert.deepEqual(submitted[0], submitted[1]);
assert.equal(submitted[1].intent.kind, "free_text");
assert.equal(c.get().play.revision, 0);
assert.equal(c.get().playMode, "local");
loaded = false;
await c.refreshModel();
await c.send();
assert.equal(c.get().visibleError, "ModelUnavailable");
assert.equal(submitted.length, 2);
assert.equal(c.get().playMode, "local");
await c.dispose();
console.log(
    "PASS: original real request recovers with stale fake fault mode; unloaded real play cannot fall back.",
);

// MOCK delayed Host effects with the actual gameplay/capture controllers and main subscription.
// No model, native application, system dialog, file export or canonical authority substitute.
import assert from "node:assert/strict";
import { build } from "esbuild";
import { mkdir, writeFile } from "node:fs/promises";
import { fileURLToPath, pathToFileURL } from "node:url";
import path from "node:path";
import { randomUUID } from "node:crypto";
const directory = process.env.LOCALLORE_CHECK_OUTPUT_DIR;
assert(directory, "review output directory required");
await mkdir(directory, { recursive: true });
const target = path.join(directory, `capture-review-${randomUUID()}.mjs`);
const compiled = await build({
    stdin: {
        contents:
            'export { CaptureController } from "./ui/capture-controller"; export { Controller } from "./ui/controller";',
        resolveDir: fileURLToPath(new URL(".", import.meta.url)),
        loader: "ts",
    },
    bundle: true,
    platform: "node",
    format: "esm",
    write: false,
});
await writeFile(target, compiled.outputFiles[0].contents);
const { Controller, CaptureController } = await import(
    pathToFileURL(target).href
);
const scope = { story: "synthetic-controller-race", branch: "main" };
const session = {
    id: "synthetic-session",
    scope,
    name: "Synthetic",
    revision: 0,
};
let captureEnabled = false;
let revokeError = null;
let releaseClear, enteredClear;
const clearHeld = new Promise((resolve) => (releaseClear = resolve));
const clearEntered = new Promise((resolve) => (enteredClear = resolve));
const calls = [];
const gateway = {
    async native(name) {
        assert.equal(name, "capture_revoke");
        return { revoked: true };
    },
    async call(q) {
        calls.push(structuredClone(q));
        if (q.op === "open") return { revision: 0 };
        if (["inspect", "close"].includes(q.op)) return {};
        if (q.op === "play_snapshot")
            return {
                scope,
                revision: 0,
                inventory: {},
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
        if (q.op === "trace_read")
            return {
                scope,
                head: 0,
                base_revision: q.base_revision,
                observer: q.observer,
                configuration_scope: "window_host",
                capture: "metadata_only",
                full_capture: "unsupported",
                snapshot: {
                    version: 1,
                    status: "bounded_metadata_window",
                    exact_reconstruction: false,
                    attempts: [],
                },
            };
        if (q.op === "trace_capture_configure") {
            captureEnabled = true;
            return {
                version: 1,
                scope,
                head: 0,
                enabled: true,
                capture: "explicit_private_details",
                retention_seconds: 600,
            };
        }
        if (q.op === "trace_capture_revoke") {
            if (revokeError) throw Error(revokeError);
            captureEnabled = false;
            return { version: 1, scope, revoked: true };
        }
        if (q.op === "trace_clear") {
            enteredClear();
            await clearHeld;
            captureEnabled = false; // Same accepted Rust clear behavior, delayed until this request runs.
            return {
                configuration_scope: "window_host",
                capture: "metadata_only",
                full_capture: "unsupported",
                cleared: true,
            };
        }
        throw Error(`Unexpected mock operation ${q.op}`);
    },
};
const gameplay = new Controller(
    gateway,
    undefined,
    "review-private-race",
    (work) => capture.metadataControl(work),
);
const capture = new CaptureController(gateway, () => gameplay.readTrace());
const sync = () => {
    const s = gameplay.get();
    capture.contextChanged(
        gameplay.selected(),
        s.play?.revision ?? 0,
        s.view === "lab" &&
            s.observer === "omniscient" &&
            s.trace.shown &&
            !s.disposed,
        gameplay.traceAttempt(),
    );
};
const releaseSubscription = gameplay.subscribe(sync);
await gameplay.attach(session);
gameplay.requestLab();
gameplay.acknowledgeLab(true);
await gameplay.showTrace();
for (let n = 0; n < 100 && capture.get().controlBusy; n++)
    await new Promise((resolve) => setImmediate(resolve));
assert.equal(
    capture.get().controlBusy,
    false,
    "initial context revocation settled",
);
await capture.configure(true);
assert.equal(captureEnabled, true);
const clearing = gameplay.controlTrace("clear");
await clearEntered;
assert.equal(
    capture.get().controlBusy,
    true,
    "whole metadata effect is fenced",
);
assert.equal(
    gameplay.get().trace.controlBusy,
    true,
    "metadata operation remains in flight",
);
assert.equal(captureEnabled, false, "private revoke itself completed");
// Exercise the same direct action even while the UI button is disabled.
const renewing = capture.configure(true);
for (let n = 0; n < 5; n++)
    await new Promise((resolve) => setImmediate(resolve));
const renewedBeforeOldClear = captureEnabled;
releaseClear();
await clearing;
await renewing;
const displayedAfter = capture.get().enabled;
const nativeAfter = captureEnabled;
assert.equal(
    renewedBeforeOldClear,
    false,
    "new private consent must wait until older metadata clear finishes",
);
assert(
    displayedAfter !== true || nativeAfter,
    "UI must not claim enabled after older clear removes native consent",
);
assert.equal(capture.get().controlBusy, false);
await assert.rejects(
    capture.metadataControl(async () => {
        throw Error("synthetic-metadata-failure");
    }),
    /synthetic-metadata-failure/,
);
assert.equal(capture.get().controlBusy, false, "throw releases barrier");
assert.equal(capture.get().enabled, false);
revokeError = "TraceUnavailable";
let metadataRan = false;
await capture.metadataControl(async () => {
    metadataRan = true;
});
assert.equal(
    metadataRan,
    true,
    "unavailable revoke does not drop metadata work",
);
assert.equal(capture.get().controlBusy, false, "unavailable revoke settles");
assert.equal(capture.get().enabled, null, "unconfirmed revoke is not disabled");
assert.match(capture.get().cleanup, /TraceUnavailable/);
revokeError = null;
let releaseMetadata, enteredMetadata;
const metadataHeld = new Promise((resolve) => (releaseMetadata = resolve));
const metadataEntered = new Promise((resolve) => (enteredMetadata = resolve));
const oldMetadata = capture.metadataControl(async () => {
    enteredMetadata();
    await metadataHeld;
});
await metadataEntered;
capture.contextChanged(
    { ...session, id: "reopened-review-session" },
    0,
    true,
    null,
);
assert.equal(capture.get().controlBusy, true);
const enableCallsBefore = calls.filter(
    (q) => q.op === "trace_capture_configure",
).length;
await capture.configure(true);
assert.equal(
    calls.filter((q) => q.op === "trace_capture_configure").length,
    enableCallsBefore,
    "switch cannot grant before old metadata and context revocation settle",
);
releaseMetadata();
await oldMetadata;
for (let n = 0; n < 100 && capture.get().controlBusy; n++)
    await new Promise((resolve) => setImmediate(resolve));
assert.equal(capture.get().controlBusy, false);
assert.equal(
    capture.get().enabled,
    null,
    "old completion cannot label reopened session",
);
releaseSubscription();
await capture.dispose();
await gameplay.dispose();
console.log(
    "PASS: metadata clear and private enable share an ordering barrier; truthful consent survives delayed effects, thrown metadata, unavailable revocation and session switching.",
);

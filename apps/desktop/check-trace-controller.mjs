// Actual controller with deferred metadata replies; no model or native/UI control.
import assert from "node:assert/strict";
import { build } from "esbuild";
import { mkdir, writeFile } from "node:fs/promises";
import { fileURLToPath, pathToFileURL } from "node:url";
import path from "node:path";
import { randomUUID } from "node:crypto";
const directory =
    process.env.LOCALLORE_CHECK_OUTPUT_DIR ??
    fileURLToPath(new URL("artifacts/checks/", import.meta.url));
await mkdir(directory, { recursive: true });
const target = path.join(directory, `trace-controller-${randomUUID()}.mjs`);
const compiled = await build({
    entryPoints: [fileURLToPath(new URL("ui/controller.ts", import.meta.url))],
    bundle: true,
    platform: "node",
    format: "esm",
    write: false,
});
await writeFile(target, compiled.outputFiles[0].contents);
const { Controller } = await import(pathToFileURL(target).href);
const scope = { story: "synthetic-trace", branch: "main" };
const provenance = Object.fromEntries(
    [
        "model_sha256",
        "worker_sha256",
        "profile_sha256",
        "config_sha256",
        "prompt_sha256",
        "schema_sha256",
        "runtime_revision",
        "engine_revision",
        "profile_label",
        "prompt_label",
        "schema_label",
    ].map((k) => [k, null]),
);
function gate() {
    let release, ready;
    const waiting = new Promise((r) => (release = r)),
        entered = new Promise((r) => (ready = r));
    return { release, ready, waiting, entered };
}
let head = 0,
    includeReceipt = false,
    holdQuery = null;
let enabled = false,
    retained = true,
    hold = null,
    corrupt = null;
const commands = [];
const gateway = {
    async call(q) {
        commands.push(structuredClone(q));
        if (q.op === "open") return { revision: head };
        if (q.op === "play_snapshot")
            return {
                scope: q.scope,
                revision: head,
                inventory: {},
                receipts: includeReceipt
                    ? [
                          {
                              request: {
                                  version: 1,
                                  scope: q.scope,
                                  turn: "synthetic-turn",
                                  expected_revision: 0,
                                  intent: {
                                      kind: "actions",
                                      value: [{ op: "wait", ticks: 1 }],
                                  },
                              },
                              proposal: {},
                              events: [
                                  {
                                      sequence: 1,
                                      scope: q.scope,
                                      turn: "synthetic-turn",
                                      outcome: {},
                                  },
                              ],
                              narration: "Synthetic accepted receipt",
                          },
                      ]
                    : [],
                player: {
                    scope: q.scope,
                    revision: head,
                    observer: "player",
                    self_state: { name: "Rowan", energy: 2, location: "quay" },
                    facts: {},
                    beliefs: [],
                    observations: [],
                },
            };
        if (["inspect", "close"].includes(q.op)) return {};
        if (q.op === "inspection_query") {
            const x = q.query;
            const page = {
                version: 1,
                scope: x.scope,
                head: x.expected_head,
                revision: x.at_revision ?? x.expected_head,
                story_time: 100,
                observer: x.observer,
                view: x.view,
                privacy:
                    x.observer.kind === "player"
                        ? "player_visible"
                        : x.observer.kind === "character"
                          ? "private_character"
                          : "private_omniscient",
                status: "supported",
                total: 0,
                rows: [],
                next_cursor: null,
                unsupported: [],
            };
            if (holdQuery) {
                const h = holdQuery;
                holdQuery = null;
                h.ready();
                await h.waiting;
            }
            return page;
        }
        if (q.op === "trace_configure") {
            enabled = q.enabled;
            if (!enabled) retained = false;
            return {
                configuration_scope: "window_host",
                capture: "metadata_only",
                full_capture: "unsupported",
                enabled,
            };
        }
        if (q.op === "trace_clear") {
            retained = false;
            return {
                configuration_scope: "window_host",
                capture: "metadata_only",
                full_capture: "unsupported",
                cleared: true,
            };
        }
        assert.equal(q.op, "trace_read");
        const result = {
            scope: q.scope,
            head: q.expected_head,
            base_revision: q.base_revision,
            observer: q.observer,
            configuration_scope: "window_host",
            capture: "metadata_only",
            full_capture: "unsupported",
            snapshot: {
                version: 1,
                status: enabled ? "bounded_metadata_window" : "disabled",
                exact_reconstruction: false,
                attempts:
                    enabled && retained && q.observer.kind !== "character"
                        ? [
                              {
                                  identity: {
                                      scope: q.scope,
                                      base_revision: q.base_revision,
                                      observer: "player",
                                      turn: "synthetic-turn",
                                      attempt: 1,
                                  },
                                  provenance: structuredClone(provenance),
                                  outcome: "committed",
                                  elapsed_us: 12,
                                  truncated: false,
                                  stages: [
                                      {
                                          stage: "atomic_commit",
                                          outcome: "committed",
                                          started_us: 2,
                                          duration_us: 3,
                                          error: null,
                                          counts: {
                                              eligible_records: 0,
                                              input_tokens: null,
                                              output_tokens: null,
                                              operations: 1,
                                              repairs: 0,
                                          },
                                      },
                                  ],
                              },
                          ]
                        : [],
            },
        };
        if (corrupt) {
            corrupt(result);
            corrupt = null;
        }
        if (hold) {
            const h = hold;
            hold = null;
            h.ready();
            await h.waiting;
        }
        return result;
    },
};
const c = new Controller(gateway);
await c.attach({ id: "session-a", scope, name: "Synthetic", revision: 0 });
await c.showTrace();
assert.equal(c.get().trace.enabled, false);
assert.equal(
    commands.filter((q) => q.op === "trace_configure").length,
    0,
    "opening debugger never opts in",
);
await c.controlTrace("enable");
assert.equal(c.get().trace.enabled, true);
assert.equal(c.traceAttempt().identity.turn, "synthetic-turn");
const old = gate();
hold = old;
const reading = c.readTrace();
await old.entered;
c.setView("lab");
c.setObserver("mira");
await c.readTrace();
assert.equal(c.get().trace.reply.observer.id, "mira");
assert.equal(c.traceAttempt(), null);
old.release();
await reading;
assert.equal(
    c.traceAttempt(),
    null,
    "late Player trace cannot appear under character lens",
);
c.setView("play");
await c.readTrace();
for (const change of [
    (r) => (r.scope = { story: "foreign", branch: "main" }),
    (r) => (r.head = 9),
    (r) => (r.snapshot.attempts[0].identity.observer = "sable"),
    (r) => (r.snapshot.attempts[0].provenance.prompt_label = "C:\\private"),
    (r) => (r.snapshot.raw_prompt = "private"),
]) {
    corrupt = change;
    await c.readTrace();
    assert.equal(c.get().trace.error, "Wire");
    assert.equal(c.get().trace.reply, null);
}
await c.readTrace();
const beforeClear = gate();
hold = beforeClear;
const stale = c.readTrace();
await beforeClear.entered;
await c.controlTrace("clear");
assert.equal(c.traceAttempt(), null);
beforeClear.release();
await stale;
assert.equal(c.traceAttempt(), null, "late read cannot undo deletion");
retained = true;
await c.readTrace();
const switching = gate();
hold = switching;
const oldStory = c.readTrace();
await switching.entered;
await c.attach({
    id: "session-b",
    scope: { story: "other-synthetic", branch: "main" },
    name: "Other",
    revision: 0,
});
await c.readTrace();
switching.release();
await oldStory;
assert.equal(c.get().trace.reply.scope.story, "other-synthetic");
await c.controlTrace("disable");
assert.equal(c.get().trace.reply.snapshot.status, "disabled");
assert.equal(c.get().trace.reply.snapshot.attempts.length, 0);
const slow = gate();
hold = slow;
let refreshed = false;
const refreshing = c.refresh().then(() => {
    refreshed = true;
});
await slow.entered;
await new Promise(setImmediate);
try {
    assert.equal(
        refreshed,
        true,
        "held diagnostic IPC must not delay gameplay snapshot refresh",
    );
} finally {
    slow.release();
}
await refreshing;
await c.readTrace();
head = 1;
includeReceipt = true;
retained = true;
await c.controlTrace("enable");
await c.refresh();
await c.traceBasis(0);
assert(c.debugReceipt());
const openingSearch = gate();
holdQuery = openingSearch;
const oldLink = c.traceToInspection();
await openingSearch.entered;
await c.browseInspection({
    view: "knowledge",
    search: "new-user-filter",
    atRevision: 0,
});
openingSearch.release();
await oldLink;
assert.equal(c.get().query.view, "knowledge");
assert.equal(c.get().query.search, "new-user-filter");
assert.equal(c.get().query.atRevision, 0);
await c.showTrace();
const openingLens = gate();
holdQuery = openingLens;
const oldPlayerLink = c.traceToInspection();
await openingLens.entered;
c.setView("lab");
c.setObserver("mira");
await c.browseInspection({
    view: "knowledge",
    search: "new-lens-filter",
    atRevision: 0,
});
openingLens.release();
await oldPlayerLink;
assert.equal(c.get().view, "lab");
assert.equal(c.get().observer, "mira");
assert.equal(c.get().query.view, "knowledge");
assert.equal(c.get().query.search, "new-lens-filter");
assert.equal(c.get().query.atRevision, 0);
assert(
    !commands.some(
        (q) => q.op === "inspection_query" && q.query.view === "turn_diff",
    ),
    "held receipt navigation cannot override newer query/lens/boundary intent",
);
await c.dispose();
assert.equal(c.get().trace.reply, null);
assert(
    !commands.some((q) =>
        ["submit", "prepare", "commit", "free_text"].includes(q.op),
    ),
    "debug reads/configuration never invoke gameplay",
);
console.log(
    "PASS: trace opt-in, exact head/scope/observer wire checks, delayed lens/story/deletion fences default-disabled non-generation controls passive held diagnostic refresh and held receipt-navigation fences.",
);

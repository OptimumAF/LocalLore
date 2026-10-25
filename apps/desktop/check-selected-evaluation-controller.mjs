// Frozen BEFORE model/controller implementation. MOCK transport only, no Rust,
// native IPC, rendering, models or canonical reconstruction. Source-only at handoff.
import assert from "node:assert/strict";
import { build } from "esbuild";
import { mkdir, writeFile } from "node:fs/promises";
import { randomUUID } from "node:crypto";
import { fileURLToPath, pathToFileURL } from "node:url";
import path from "node:path";
const root = fileURLToPath(new URL(".", import.meta.url));
const output = process.env.LOCALLORE_CHECK_OUTPUT_DIR ?? path.join(root, "artifacts/checks");
await mkdir(output, { recursive: true });
const built = await build({ stdin: { contents: 'export * from "./ui/selected-evaluation-model"; export * from "./ui/selected-evaluation-controller";',
    resolveDir: root, loader: "ts" }, bundle: true, platform: "node", format: "cjs", write: false });
const bundle = path.join(output, `selected-evaluation-${randomUUID()}.cjs`);
await writeFile(bundle, built.outputFiles[0].contents, { flag: "wx" });
const m = (await import(pathToFileURL(bundle).href)).default;
const hash = "a".repeat(64), token = "22222222-2222-2222-2222-222222222222";
const planToken = "33333333-3333-3333-3333-333333333333", runId = "44444444-4444-4444-4444-444444444444";
const source = { readerClientId: "55555555-5555-5555-5555-555555555555", runToken: token, binding: hash };
const row = { turn: "move-4", arm: "right" }, scope = { story: "synthetic-selected", branch: "main" };
const omni = { kind: "omniscient" }, player = { kind: "player" };
const clone = (v) => structuredClone(v);
const selection = { turn: row.turn, clicked_arm: row.arm, index: 4 };
function prepared() { return { version: 1, kind: "selected_prepared", binding: hash, lane: "scripted_selected_case",
    selection: clone(selection), arms: ["left", "right"].map((arm) => ({ arm, scope: clone(scope), before_head: 2,
        prefix_sha256: hash, input_semantic_sha256: hash })) }; }
function summary() { return { version: 1, kind: "selected_read", binding: hash, lane: "scripted_selected_case",
    selection: clone(selection), arms: ["left", "right"].map((arm) => ({ arm, scope: clone(scope), before_head: 2,
        after_head: 3, available: true })), read_only: true, execution_available: false }; }
function diagnostics() { return { version: 1, kind: "selected_diagnostics", binding: hash, lane: "scripted_selected_case", completed: true,
    rows: ["left", "right"].map((arm) => ({ turn: row.turn, arm, phase: "committed", error: null, expected: '"accepted"',
        passed: true, failures: [], quality_flags: [], roles: 2, roles_known: true, elapsed_ms: 1,
        actual_receipt_sha256: hash, privacy_passed: true, context_evidence_available: true })), physical_setups: 0,
    physical_setup_ms: null, left_charged_ms: 2, right_charged_ms: 2, left_reserved_roles: 2, right_reserved_roles: 2,
    human_reviewed: 0, quality_accepted: false, unavailable: ["scripted_lane_no_native_setup_measurement"] }; }
function status(client, phase = "completed", extra = {}) { return { version: 1, kind: "selected_evaluation", client_id: client,
    operation_id: phase === "closed" ? null : 2, phase, running: ["preparing", "running", "cancelling"].includes(phase),
    lane: phase === "closed" ? null : "scripted_baseline", plan_token: phase === "closed" ? null : planToken,
    run_id: phase === "closed" || phase === "prepared" ? null : runId,
    run_token: phase === "closed" || phase === "prepared" ? null : token,
    binding: phase === "closed" || phase === "prepared" ? null : hash,
    prepared: phase === "closed" ? null : prepared(), error: null, cause: null, cleanup_required: false, ...extra }; }
function wrapped(kind, key, value, run_token = token) { return { version: 1, kind, run_token, [key]: value }; }
function evidence(request, arm = "right") { return { version: 1, binding: hash, row: { turn: row.turn, arm }, scope: clone(scope),
    before_head: 2, after_head: 3, observer: clone(request.observer), edge: request.kind === "receipt" ? "after" : null,
    read_only: true, generation_grant: false, body: request.kind === "receipt" ? { kind: "receipt", receipt: { synthetic: true } }
        : { kind: "missing", reason: request.kind === "capture" ? "capture_unavailable" : "recording_unavailable" } }; }
function deferred() { let resolve, reject; const promise = new Promise((a, b) => { resolve = a; reject = b; }); return { promise, resolve, reject }; }
const tick = () => new Promise((resolve) => setTimeout(resolve, 0));
const controllers = new Set();
function fixture() {
    const calls = [], hooks = new Map();
    let current;
    const c = new m.SelectedEvaluationController(async (command, args) => {
        assert.equal(command, "evaluation_selected"); assert.deepEqual(Object.keys(args).sort(), ["action", "request"]);
        assert.equal(typeof args.request, "string"); assert.ok(Buffer.byteLength(args.request) <= 4096);
        const body = JSON.parse(args.request), call = { action: args.action, body }; calls.push(call);
        if (hooks.has(args.action)) return hooks.get(args.action)(body);
        if (args.action === "catalog") return { version: 1, kind: "selected_catalog", runs: [{ run_id: runId, created: 1, lane: "scripted_baseline", selection: clone(selection) }] };
        if (args.action === "prepare") return current = status(body.clientId, "prepared");
        if (["start", "open", "resume"].includes(args.action)) return current = status(body.clientId);
        if (args.action === "status") return current ?? status(body.clientId);
        if (args.action === "cancel") return current = status(body.clientId);
        if (args.action === "close") return status(body.clientId, "closed");
        if (args.action === "summary") return wrapped("selected_summary", "summary", summary());
        if (args.action === "diagnostics") return wrapped("selected_diagnostics_result", "diagnostics", diagnostics());
        if (args.action === "evidence") return wrapped("selected_evidence", "evidence", evidence(body.request, body.arm));
        if (["cleanup_status", "retry_cleanup"].includes(args.action)) return { version: 1, kind: "selected_cleanup", cleanup_required: false, running: false, error: null };
        throw new Error("unexpected mock action");
    });
    controllers.add(c); c.setContext("synthetic-session-a", true); c.setObserver(omni);
    return { c, calls, hooks };
}
async function ready(f) { await f.c.prepare(source, row, "scripted_baseline"); await f.c.start(); await f.c.loadSummary(); }
const cases = [];
async function test(name, run) {
    let timer;
    try { await Promise.race([run(), new Promise((_, reject) => { timer = setTimeout(() => reject(new Error("bounded mock case did not complete")), 3000); })]);
        cases.push({ name, passed: true }); }
    catch (error) { cases.push({ name, passed: false, error: error instanceof Error ? error.message.slice(0, 160) : "failure" }); }
    finally { clearTimeout(timer); for (const c of controllers) c.dispose(); controllers.clear(); }
}
function rejects(change, check, value) { const bad = clone(value); change(bad); assert.throws(() => check(bad), /SelectedEvaluationWire/); }

await test("closed status and prepared DTO keys, nullable fields, lanes and safe scalars", () => {
    const value = status(token);
    assert.equal(m.checkedSelectedStatus(value, token).phase, "completed");
    const check = (v) => m.checkedSelectedStatus(v, token);
    for (const change of [(v) => { v.extra = true; }, (v) => { delete v.cause; }, (v) => { v.running = 1; },
        (v) => { v.operation_id = Number.MAX_SAFE_INTEGER + 1; }, (v) => { v.operation_id = -1; },
        (v) => { v.binding = "A".repeat(64); }, (v) => { v.client_id = "no-uuid"; },
        (v) => { v.lane = "native_selected_case"; }, (v) => { v.error = ["Cleanup"]; },
        (v) => { v.prepared.arms[0].scope.raw = "private"; }, (v) => { v.prepared.arms[1].arm = "left"; },
        (v) => { v.prepared.selection.index = 24; }, (v) => { v.prepared.lane = "scripted_baseline"; }]) rejects(change, check, value);
    assert.throws(() => check(status(runId)), /SelectedEvaluationWire/);
    const closed = status(token, "closed"); check(closed);
    rejects((v) => { v.run_token = token; }, check, closed);
});
await test("catalog and cleanup exact closure and no coercion", () => {
    const catalog = { version: 1, kind: "selected_catalog", runs: [{ run_id: runId, created: 0, lane: "approved_native", selection }] };
    assert.equal(m.checkedSelectedCatalog(catalog).runs.length, 1);
    for (const mutate of [(v) => { v.runs[0].created = NaN; }, (v) => { v.runs = Array(33).fill(v.runs[0]); },
        (v) => { v.runs[0].path = "private"; }, (v) => { v.runs[0].lane = ["approved_native"]; }]) rejects(mutate, m.checkedSelectedCatalog, catalog);
    const clean = { version: 1, kind: "selected_cleanup", cleanup_required: true, running: false, error: "Cleanup" };
    m.checkedSelectedCleanup(clean);
    rejects((v) => { v.owner = token; }, m.checkedSelectedCleanup, clean);
    rejects((v) => { v.cleanup_required = null; }, m.checkedSelectedCleanup, clean);
});
await test("shared summary/diagnostics strict shape, identity and no hidden raw fields", () => {
    const s = summary(), raw = wrapped("selected_summary", "summary", s);
    m.checkedSelectedSummary(raw, token, hash);
    for (const change of [(v) => { v.run_token = runId; }, (v) => { v.summary.source_inputs = []; },
        (v) => { v.summary.arms[0].available = null; }, (v) => { v.summary.execution_available = true; }])
        rejects(change, (v) => m.checkedSelectedSummary(v, token, hash), raw);
    const d = wrapped("selected_diagnostics_result", "diagnostics", diagnostics());
    m.checkedSelectedDiagnostics(d, token, s);
    for (const change of [(v) => { v.diagnostics.rows[0].trace = {}; }, (v) => { v.diagnostics.rows[0].roles_known = null; },
        (v) => { v.diagnostics.rows[0].arm = "foreign"; }, (v) => { v.diagnostics.rows[0].elapsed_ms = Infinity; },
        (v) => { v.diagnostics.binding = "b".repeat(64); }, (v) => { v.diagnostics.physical_setup_ms = undefined; }])
        rejects(change, (v) => m.checkedSelectedDiagnostics(v, token, s), d);
});
await test("evidence binds exact selected scope/head/observer/row/token and checkpoint missing", () => {
    const request = { kind: "receipt", observer: omni }, raw = wrapped("selected_evidence", "evidence", evidence(request));
    const check = (v) => m.checkedSelectedEvidence(v, token, summary(), "right", request);
    check(raw);
    for (const mutate of [(v) => { v.evidence.scope.branch = "foreign"; }, (v) => { v.evidence.row.arm = "left"; },
        (v) => { v.evidence.observer = player; }, (v) => { v.evidence.after_head = 4; }, (v) => { v.evidence.generation_grant = true; },
        (v) => { v.evidence.body.receipt = []; }]) rejects(mutate, check, raw);
    const absent = summary(); absent.arms[1].available = false; absent.arms[1].after_head = null;
    const missing = evidence(request); missing.after_head = null; missing.edge = null;
    missing.body = { kind: "missing", reason: "checkpoint_unavailable" };
    m.checkedSelectedEvidence(wrapped("selected_evidence", "evidence", missing), token, absent, "right", request);
});
await test("exact wire actions and same identity through prepare/start/catalog/open/resume", async () => {
    const f = fixture(); await f.c.catalog(); await f.c.prepare(source, row, "scripted_baseline");
    const client = f.c.get().clientId; await f.c.start(); await f.c.start();
    assert.equal(f.calls.filter((v) => v.action === "start").length, 1, "completed exact start reused");
    assert.deepEqual(f.calls.find((v) => v.action === "prepare").body, { clientId: client, readerClientId: source.readerClientId,
        runToken: token, binding: hash, turnId: row.turn, arm: row.arm, lane: "scripted_baseline" });
    assert.deepEqual(f.calls.find((v) => v.action === "start").body, { clientId: client, planToken });
    await f.c.close(); await f.c.open(runId); await f.c.resume(source);
    const resume = f.calls.find((v) => v.action === "resume").body;
    assert.equal(resume.readerClientId, source.readerClientId); assert.equal(resume.sourceToken, token);
    assert.equal(resume.sourceBinding, hash); f.c.dispose();
});
await test("notification context retirement prevents original prepare dispatch", async () => {
    const f = fixture(); let changed = false;
    f.c.subscribe(() => { if (!changed && f.c.get().clientId) { changed = true; f.c.setContext("new-session", true); } });
    await f.c.prepare(source, row, "scripted_baseline");
    assert.equal(f.calls.filter((v) => v.action === "prepare").length, 0); assert.equal(f.c.get().status, null); f.c.dispose();
});
await test("observer switch retains held start identity and never cancels or rekeys generation", async () => {
    const f = fixture(); await f.c.prepare(source, row, "scripted_baseline"); const client = f.c.get().clientId;
    const held = deferred(); f.hooks.set("start", () => held.promise); const work = f.c.start(); await tick();
    f.c.setObserver(player); assert.equal(f.c.get().clientId, client);
    assert.equal(f.calls.filter((v) => ["cancel", "close"].includes(v.action)).length, 0);
    held.resolve(status(client)); await work; assert.equal(f.c.get().status.phase, "completed"); f.c.dispose();
});
await test("lost start ACK retains client; only explicit same-client status recovers", async () => {
    const f = fixture(); await f.c.prepare(source, row, "scripted_baseline"); const client = f.c.get().clientId;
    f.hooks.set("start", () => { throw new Error("EvaluationIo"); }); await f.c.start();
    assert.equal(f.c.get().uncertain, true); assert.equal(f.c.get().clientId, client);
    await f.c.prepare(source, row, "approved_native"); await f.c.start();
    assert.equal(f.calls.filter((v) => v.action === "prepare").length, 1);
    assert.equal(f.calls.filter((v) => v.action === "start").length, 1);
    f.hooks.set("status", () => status(client)); await f.c.status();
    assert.equal(f.c.get().uncertain, false); assert.equal(f.c.get().status.phase, "completed");
    assert.equal(f.calls.find((v) => v.action === "status").body.clientId, client); f.c.dispose();
});
await test("held status survives lens epoch, wrong client cannot publish", async () => {
    const f = fixture(); await ready(f); const client = f.c.get().clientId, held = deferred();
    f.hooks.set("status", () => held.promise); const work = f.c.status(); await tick(); f.c.setObserver(player);
    held.resolve(status(client)); await work; assert.equal(f.c.get().status.phase, "completed");
    f.hooks.set("status", () => status(runId)); await f.c.status(); assert.equal(f.c.get().error, "SelectedEvaluationWire"); f.c.dispose();
});
for (const method of ["readEvidence", "readDiagnostics"]) await test(`held ${method} cannot publish after actor lens switch`, async () => {
    const f = fixture(); await ready(f); const held = deferred(), action = method === "readEvidence" ? "evidence" : "diagnostics";
    f.hooks.set(action, () => held.promise);
    const work = method === "readEvidence" ? f.c.readEvidence("right", { kind: "receipt", observer: omni }) : f.c.readDiagnostics();
    await tick(); f.c.setObserver(player);
    assert.equal(f.c.get().evidence, null); assert.equal(f.c.get().diagnostics, null);
    held.resolve(method === "readEvidence" ? wrapped("selected_evidence", "evidence", evidence({ kind: "receipt", observer: omni }))
        : wrapped("selected_diagnostics_result", "diagnostics", diagnostics())); await work;
    assert.equal(f.c.get().evidence, null); assert.equal(f.c.get().diagnostics, null); f.c.dispose();
});
await test("actor raw diagnostics/evidence refused before IPC and synchronous read notification fences", async () => {
    const f = fixture(); await ready(f); f.c.setObserver(player); const n = f.calls.length;
    await f.c.readDiagnostics(); await f.c.readEvidence("right", { kind: "receipt", observer: player });
    assert.equal(f.calls.length, n); f.c.setObserver(omni); let once = false;
    f.c.subscribe(() => { if (!once && f.c.get().busy) { once = true; f.c.setObserver(player); } });
    await f.c.readDiagnostics(); assert.equal(f.calls.filter((v) => v.action === "diagnostics").length, 0); f.c.dispose();
});
await test("held original start retirement cleans only captured old client, never new owner", async () => {
    const f = fixture(); await f.c.prepare(source, row, "scripted_baseline"); const old = f.c.get().clientId, held = deferred();
    f.hooks.set("start", () => held.promise); const work = f.c.start(); await tick(); f.c.setContext("new-session", true);
    held.resolve(status(old)); await work; await tick();
    assert.equal(f.c.get().status, null); assert.equal(f.c.get().clientId, null);
    assert.ok(f.calls.some((v) => v.action === "close" && v.body.clientId === old)); f.c.dispose();
});
await test("actual completed result wins late cancelling status", async () => {
    const f = fixture(); await ready(f); const client = f.c.get().clientId;
    f.hooks.set("cancel", () => status(client, "cancelling")); await f.c.cancel();
    assert.equal(f.c.get().status.phase, "completed"); assert.equal(f.c.get().status.run_id, runId); f.c.dispose();
});
await test("actual completed held poll wins racing cancel without closing the still-owned client", async () => {
    const f = fixture(); await f.c.prepare(source, row, "scripted_baseline"); const client = f.c.get().clientId;
    const polled = deferred(), cancelled = deferred(), reachedPoll = deferred();
    f.hooks.set("start", () => status(client, "running"));
    f.hooks.set("status", () => { reachedPoll.resolve(); return polled.promise; });
    f.hooks.set("cancel", () => cancelled.promise);
    const start = f.c.start(); await reachedPoll.promise;
    const cancel = f.c.cancel(); await tick();
    polled.resolve(status(client)); await start;
    cancelled.resolve(status(client, "cancelling")); await cancel;
    assert.equal(f.c.get().status.phase, "completed"); assert.equal(f.c.get().status.run_id, runId);
    assert.equal(f.calls.filter((v) => v.action === "close").length, 0); f.c.dispose();
});
await test("retained cleanup status blocks admission and retry is explicit", async () => {
    const f = fixture(); f.hooks.set("cleanup_status", () => ({ version: 1, kind: "selected_cleanup", cleanup_required: true, running: false, error: "Cleanup" }));
    await f.c.cleanupStatus(); await f.c.prepare(source, row, "scripted_baseline");
    assert.equal(f.calls.filter((v) => v.action === "prepare").length, 0); assert.equal(f.c.get().cleanup.cleanup_required, true);
    assert.equal(f.calls.filter((v) => v.action === "retry_cleanup").length, 0);
    await f.c.retryCleanup(); await f.c.prepare(source, row, "scripted_baseline");
    assert.equal(f.calls.filter((v) => v.action === "prepare").length, 1); f.c.dispose();
});
await test("summary token mismatch and capability loss clear private results without invented completion", async () => {
    const f = fixture(); await ready(f); await f.c.readDiagnostics();
    f.hooks.set("summary", () => wrapped("selected_summary", "summary", summary(), runId)); await f.c.loadSummary();
    assert.equal(f.c.get().summary, null); assert.equal(f.c.get().diagnostics, null); assert.equal(f.c.get().error, "SelectedEvaluationWire");
    f.hooks.set("summary", () => { throw new Error("UnknownEvaluationRun"); }); await f.c.loadSummary();
    assert.equal(f.c.get().summary, null); assert.equal(f.c.get().evidence, null); f.c.dispose();
});
const result = { version: 1, cases, passed: cases.filter((v) => v.passed).length, failed: cases.filter((v) => !v.passed).length,
    synthetic_transport: true, headless_component_render: false, native_ipc: false, native_rendering: false, model_execution: false };
await writeFile(path.join(output, `selected-evaluation-${randomUUID()}.json`), JSON.stringify(result, null, 2), { flag: "wx" });
console.log(JSON.stringify(result)); if (result.failed) process.exitCode = 1;

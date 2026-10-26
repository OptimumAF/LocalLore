// Frozen BEFORE the three NEW modules. SYNTHETIC transport + actual new
// controller/React static HTML only. Missing modules are compile-only evidence.
// Run from apps/desktop: node check-comparison-run.mjs
import assert from "node:assert/strict";
import { build } from "esbuild";
import { mkdir, readFile, writeFile } from "node:fs/promises";
import { createHash, randomUUID } from "node:crypto";
import { fileURLToPath, pathToFileURL } from "node:url";
import path from "node:path";
const root = fileURLToPath(new URL(".", import.meta.url)), output = process.env.LOCALLORE_CHECK_OUTPUT_DIR ?? path.join(root, "artifacts/checks");
await mkdir(output, { recursive: true });
const prefix = `comparison-run-${randomUUID()}`, bundle = path.join(output, `${prefix}.cjs`);
const built = await build({ stdin: { contents: 'export * from "./ui/comparison-run-model";export {ComparisonRunController} from "./ui/comparison-run-controller";export {ComparisonRunView} from "./ui/comparison-run-view";export {createElement} from "react";export {renderToStaticMarkup} from "react-dom/server";', resolveDir: root, loader: "tsx" }, bundle: true, platform: "node", format: "cjs", write: false });
await writeFile(bundle, built.outputFiles[0].contents, { flag: "wx" });
const m = (await import(pathToFileURL(bundle).href)).default, clone = value => structuredClone(value);
const client = "11111111-1111-1111-1111-111111111111", run = "22222222-2222-2222-2222-222222222222", token = "33333333-3333-3333-3333-333333333333";
const other = "44444444-4444-4444-4444-444444444444";
function status(extra = {}) { return { version: 1, kind: "comparison_run", protocol_version: 3, input_lane: "scripted_baseline", client_id: client, run_id: run, run_token: token, operation_id: 1, comparison_kind: "paired", batch: 1, phase: "paused", running: false, error: null, completed_scenes: 1, completed: false, report_ready: true, source_matches: true, ...extra }; }
function catalog() { return { version: 1, kind: "comparison_run_catalog", protocol_version: 3, input_lane: "scripted_baseline", max_new_scenes: 4, runs: [{ run_id: run, client_id: client, comparison_kind: "paired", initial_batch: 1, created_ms: 1, protocol_version: 3, input_lane: "scripted_baseline" }] }; }
const results = [], controllers = new Set(), html = [];
async function check(name, body) { let timer; try { await Promise.race([Promise.resolve().then(body), new Promise((_, reject) => { timer = setTimeout(() => reject(new Error("bounded mock case timeout")), 3500); })]); results.push({ name, passed: true }); } catch (error) { results.push({ name, passed: false, error: String(error?.message ?? error).slice(0, 200) }); } finally { clearTimeout(timer); } }
for (const [name, extra] of [["partial ready", {}], ["historical ready", { source_matches: false }], ["retained metadata", { phase: "retained", source_matches: null, report_ready: false, completed_scenes: 0 }], ["closed identity", { phase: "closed" }], ["closed while worker drains", { phase: "closed", running: true }]]) await check(`status accepts ${name} without inventing completion/access`, () => assert.deepEqual(m.checkedComparisonRunStatus(clone(status(extra))), status(extra)));
for (const [name, mutate] of [
    ["unknown key", v => { v.path = "never accepted"; }], ["future version", v => { v.version = 2; }], ["wrong kind", v => { v.kind = "selected_evaluation"; }],
    ["wrong protocol", v => { v.protocol_version = 2; }], ["native lane", v => { v.input_lane = "approved_native"; }],
    ["array phase", v => { v.phase = ["paused"]; }], ["unknown phase", v => { v.phase = "done"; }], ["unknown error", v => { v.error = "NativeOops"; }],
    ["null client", v => { v.client_id = null; }], ["null run", v => { v.run_id = null; }], ["null token", v => { v.run_token = null; }],
    ["uppercase UUID", v => { v.run_id = "AAAAAAAA-AAAA-AAAA-AAAA-AAAAAAAAAAAA"; }], ["missing nullable error", v => { delete v.error; }],
    ["zero operation", v => { v.operation_id = 0; }], ["unsafe operation", v => { v.operation_id = Number.MAX_SAFE_INTEGER + 1; }],
    ["zero batch", v => { v.batch = 0; }], ["too many scenes", v => { v.batch = 5; }], ["fractional batch", v => { v.batch = 1.5; }],
    ["negative completed scenes", v => { v.completed_scenes = -1; }], ["completed scenes above four", v => { v.completed_scenes = 5; }],
    ["nonboolean ready", v => { v.report_ready = 1; }], ["nonboolean running", v => { v.running = "false"; }], ["missing nullable source", v => { delete v.source_matches; }],
    ["array source", v => { v.source_matches = [true]; }],
]) await check(`status rejects ${name}`, () => { const v = status(); mutate(v); assert.throws(() => m.checkedComparisonRunStatus(v), /ComparisonRunWire/); });
await check("catalog accepts detached bounded metadata", () => { const v = catalog(), result = m.checkedComparisonRunCatalog(v); result.runs[0].created_ms = 9; assert.equal(v.runs[0].created_ms, 1); });
for (const [name, mutate] of [
    ["extra outer", v => { v.report = {}; }], ["wrong protocol", v => { v.protocol_version = 2; }], ["wrong limit", v => { v.max_new_scenes = 5; }],
    ["null rows", v => { v.runs = null; }], ["extra metadata", v => { v.runs[0].report_ready = true; }], ["native metadata", v => { v.runs[0].input_lane = "approved_native"; }],
    ["negative timestamp", v => { v.runs[0].created_ms = -1; }], ["unsafe timestamp", v => { v.runs[0].created_ms = Number.MAX_SAFE_INTEGER + 1; }],
    ["invalid kind", v => { v.runs[0].comparison_kind = "current"; }], ["invalid initial batch", v => { v.runs[0].initial_batch = 0; }],
    ["missing client", v => { delete v.runs[0].client_id; }], ["too many rows", v => { v.runs = Array.from({ length: 33 }, (_, index) => ({ ...v.runs[0], run_id: `00000000-0000-0000-0000-${String(index).padStart(12, "0")}` })); }],
]) await check(`catalog rejects ${name}`, () => { const v = catalog(); mutate(v); assert.throws(() => m.checkedComparisonRunCatalog(v), /ComparisonRunWire/); });
const tick = () => new Promise(resolve => setTimeout(resolve, 0));
async function until(predicate) { for (let n = 0; n < 100; n++) { if (predicate()) return; await new Promise(resolve => setTimeout(resolve, 10)); } throw new Error("mock observation timeout"); }
function held() { let resolve; const promise = new Promise(r => { resolve = r; }); return { promise, resolve }; }
function fixture() {
    const calls = [], hooks = new Map(); let current;
    const c = new m.ComparisonRunController(async (command, args) => {
        assert.equal(command, "evaluation_comparison_run"); assert.deepEqual(Object.keys(args).sort(), ["action", "query"]); assert.ok(Buffer.byteLength(args.query) <= 4096);
        const query = JSON.parse(args.query), action = args.action; calls.push({ action, query });
        if (hooks.has(action)) return hooks.get(action)(query);
        const expected = { catalog: [], start: ["clientId", "comparisonKind", "batch"], lookup: ["clientId"], open: ["runId"], status: ["runToken"], resume: ["runToken", "batch"], cancel: ["runToken", "operationId"], close: ["runToken"] }[action];
        assert.deepEqual(Object.keys(query).sort(), [...expected].sort());
        if (action === "catalog") return catalog();
        if (action === "start") return (current = status({ client_id: query.clientId, comparison_kind: query.comparisonKind, batch: query.batch }));
        if (action === "open") return (current = status({ run_id: query.runId }));
        if (action === "lookup") { if (!current) throw Error("UnknownEvaluationRun"); return current; }
        if (action === "status") return current;
        if (action === "resume") return (current = { ...current, batch: query.batch, operation_id: 2, completed_scenes: 4, completed: true, phase: "completed" });
        if (action === "cancel") return (current = { ...current, running: false, phase: "paused" });
        if (action === "close") return status({ ...(current ?? {}), phase: "closed", running: false, run_token: query.runToken });
        throw Error("unexpected mock action");
    }); controllers.add(c); c.setContext("synthetic-session", true);
    return { c, calls, hooks, setCurrent: v => { current = v; } };
}
await check("start retains one UUID before notification and exact repeated request", async () => { const f = fixture(); let captured; const stop = f.c.subscribe(() => { if (f.c.get().pending?.action === "start") captured ??= f.c.get().clientId; }); await f.c.start("paired", 1); await f.c.start("paired", 1); stop(); const starts = f.calls.filter(x => x.action === "start"); assert.equal(starts.length, 2); assert.equal(starts[0].query.clientId, captured); assert.deepEqual(starts[0].query, starts[1].query); assert.equal(f.c.get().status.run_id, run); });
await check("conflicting start cannot replace retained client/input", async () => { const f = fixture(); await f.c.start("paired", 1); const original = f.c.get().clientId; await f.c.start("rollout", 2); assert.equal(f.c.get().clientId, original); assert.equal(f.calls.filter(x => x.action === "start").length, 1); assert.equal(f.c.get().error, "InvalidEvaluationInput"); });
await check("unknown start ACK explicit lookup uses original client and never autostarts", async () => { const f = fixture(); f.hooks.set("start", q => { f.setCurrent(status({ client_id: q.clientId })); throw Error("EvaluationIo"); }); await f.c.start("paired", 1); const id = f.c.get().clientId; assert.equal(f.c.get().uncertain, true); await f.c.lookup(); assert.equal(f.c.get().clientId, id); assert.equal(f.c.get().uncertain, false); assert.equal(f.calls.filter(x => x.action === "start").length, 1); assert.equal(f.calls.find(x => x.action === "lookup").query.clientId, id); });
await check("catalog/open/status/lookup are read-only; resume is explicit bounded action", async () => { const f = fixture(); await f.c.loadCatalog(); assert.equal(f.c.get().catalog.runs.length, 1); await f.c.open(run); await f.c.status(); await f.c.lookup(); assert.equal(f.calls.filter(x => ["start", "resume"].includes(x.action)).length, 0); await f.c.resume(3); assert.equal(f.calls.filter(x => x.action === "resume").length, 1); assert.equal(f.c.get().status.completed, true); });
await check("wrong status client/run/token cannot retarget current ownership", async () => { for (const field of ["client_id", "run_id", "run_token"]) { const f = fixture(); await f.c.start("paired", 1); f.hooks.set("status", () => status({ client_id: f.c.get().clientId, [field]: other })); await f.c.status(); assert.equal(f.c.get().error, "ComparisonRunWire"); assert.equal(f.c.get().uncertain, true); assert.equal(f.c.get().status.run_id, run); } });
await check("reentrant context retirement before dispatch does not start a hidden run", async () => { const f = fixture(); let first; const stop = f.c.subscribe(() => { if (!first && f.c.get().pending?.action === "start") { first = f.c.get().clientId; f.c.setContext("replacement", true); } }); await f.c.start("paired", 1); stop(); assert.ok(first); assert.equal(f.calls.filter(x => x.action === "start").length, 0); assert.equal(f.c.get().status, null); });
await check("late start after context retirement closes only its captured native token", async () => { const f = fixture(), gate = held(); f.hooks.set("start", () => gate.promise); const work = f.c.start("paired", 1); await until(() => f.calls.some(x => x.action === "start")); const id = f.c.get().clientId; f.c.setContext("replacement", true); gate.resolve(status({ client_id: id })); await work; await until(() => f.calls.some(x => x.action === "close")); assert.equal(f.c.get().status, null); assert.equal(f.c.get().clientId, null); assert.ok(f.calls.filter(x => x.action === "close").every(x => x.query.runToken === token)); });
await check("dispose fences held open and still closes exact returned capability", async () => { const f = fixture(), gate = held(); f.hooks.set("open", () => gate.promise); const work = f.c.open(run); await until(() => f.calls.some(x => x.action === "open")); f.c.dispose(); gate.resolve(status()); await work; await until(() => f.calls.some(x => x.action === "close")); assert.equal(f.c.get().status, null); assert.ok(f.calls.filter(x => x.action === "close").every(x => x.query.runToken === token)); });
await check("completed late poll wins cancellation boundary; no generation retry", async () => { const f = fixture(), gate = held(); await f.c.start("paired", 1); f.hooks.set("resume", () => { const running = status({ client_id: f.c.get().clientId, operation_id: 2, phase: "running", running: true, report_ready: false }); f.setCurrent(running); return running; }); f.hooks.set("status", () => gate.promise); const work = f.c.resume(1); await until(() => f.calls.some(x => x.action === "status")); await f.c.cancel(); gate.resolve(status({ client_id: f.c.get().clientId, operation_id: 2, phase: "completed", completed: true, completed_scenes: 4 })); await work; assert.equal(f.c.get().status.phase, "completed"); assert.equal(f.calls.filter(x => x.action === "resume").length, 1); });
await check("blocked/invalid calls never admit a native execution", async () => { const f = fixture(); f.c.setContext("denied", false); await f.c.start("paired", 1); f.c.setContext("allowed", true); await f.c.start("native", 1); await f.c.start("paired", 0); assert.equal(f.calls.filter(x => x.action === "start").length, 0); });
function render(f) { return m.renderToStaticMarkup(m.createElement(m.ComparisonRunView, { controller: f.c, onInspect: () => { throw Error("render must not inspect automatically"); } })); }
await check("headless panel labels fake lane, partial report and explicit inspection", async () => { const f = fixture(); await f.c.start("paired", 1); await f.c.loadCatalog(); const markup = render(f); html.push(markup); assert.match(markup, /Scripted.*fake inference/i); assert.match(markup, /native.*unavailable/i); assert.match(markup, /1.*4/); assert.match(markup, /Inspect.*permission/i); assert.match(markup, /quality.*not established/i); });
await check("headless retained/closed identities never enable report inspection", async () => { for (const phase of ["retained", "closed"]) { const f = fixture(); f.hooks.set("open", () => status({ phase, report_ready: phase === "closed", source_matches: null })); await f.c.open(run); const markup = render(f); html.push(markup); const inspect = [...markup.matchAll(/<button\b([^>]*)>([\s\S]*?)<\/button>/g)].find(x => /Inspect/.test(x[2])); assert.ok(inspect); assert.match(inspect[1], /\bdisabled/); } });
for (const c of controllers) c.dispose(); await tick();
const sourceHashes = Object.fromEntries(await Promise.all(["ui/comparison-run-model.ts", "ui/comparison-run-controller.ts", "ui/comparison-run-view.tsx"].map(async name => [name, createHash("sha256").update(await readFile(path.join(root, name))).digest("hex")])));
for (const [index, markup] of html.entries()) await writeFile(path.join(output, `${prefix}-${index}.html`), markup, { flag: "wx" });
const result = { version: 1, evidence: "SYNTHETIC mock + actual new controller + React static HTML; no Rust/native IPC/WebView/model", sourceHashes, checks: results.length, passed: results.filter(x => x.passed).length, failed: results.filter(x => !x.passed).length, cases: results };
await writeFile(path.join(output, `${prefix}.json`), JSON.stringify(result, null, 2), { flag: "wx" }); console.log(JSON.stringify(result)); if (result.failed) process.exitCode = 1;

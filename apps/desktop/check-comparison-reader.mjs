// Frozen before implementation. Synthetic source-shaped transport fixtures only;
// exercises the actual decoder/controller, not Rust, native IPC or rendering.
import assert from "node:assert/strict";
import { build } from "esbuild";
import { mkdir, writeFile } from "node:fs/promises";
import { fileURLToPath, pathToFileURL } from "node:url";
import path from "node:path";
import { randomUUID } from "node:crypto";

const root = fileURLToPath(new URL(".", import.meta.url));
const output = process.env.LOCALLORE_CHECK_OUTPUT_DIR ?? path.join(root, "artifacts/checks");
await mkdir(output, { recursive: true });
const file = path.join(output, `comparison-reader-${randomUUID()}.cjs`);
const built = await build({ stdin: { contents: 'export * from "./ui/comparison-reader-model"; export * from "./ui/comparison-reader-controller";', resolveDir: root, loader: "ts" }, bundle: true, platform: "node", format: "cjs", write: false });
await writeFile(file, built.outputFiles[0].contents);
const { ComparisonReaderController, checkedReaderStatus, checkedReaderSource, checkedReaderSummary, checkedReaderEvidence } = (await import(pathToFileURL(file).href)).default;
const token = "22222222-2222-2222-2222-222222222222", hash = "a".repeat(64);
const scope = { story: "synthetic-comparison", branch: "main" };
const omni = { kind: "omniscient" }, player = { kind: "player" };
const clone = (v) => structuredClone(v);
const row = { turn: "gift-0", arm: "left" };
function turn(arm = "left") {
    return { turn: row.turn, scene: 0, arm, policy: arm === "left" ? "state_recent_transcript_v1" : "state_relevant_memory_v1", phase: "committed", error: null, expected: "accepted", passed: true, failures: [], quality_flags: [], roles: 2, roles_known: true, recovered_without_checkpoint: false, admission: 1, elapsed_ms: 1, first_final_response_ms: 1, commit_elapsed_ms: 0, input_semantic_sha256: hash, output_semantic_sha256: hash, mechanical_sha256: hash, policy_matches: true, context_evidence_available: true, context_requirement: "synthetic", privacy_passed: true, fallback: false, capture_sha256: hash, recording_sha256: hash, raw_sha256: [hash, hash], role_metrics: null, trace: { synthetic: true }, actual_receipt_sha256: hash, source_fallback_reason: null, compiler_fallback_reason: null, narration: "<script>inert synthetic text</script>", repairs: 0, stages: [], mandatory_sha256: hash, optional_detail_selected: false, director_private_target_present: false, selected_context_bytes: 100, estimated_context_tokens: 25 };
}
function availability(arm = "left") {
    return { row: { ...row, arm }, source: { status: "available", scope: clone(scope), before_head: 0, after_head: 1, input_semantic_sha256: hash }, capture_available: true, receipt_available: true, recording_available: true, unavailable: [] };
}
const rows = [availability(), availability("right")];
const profile = { id: "synthetic", model_sha256: hash, runtime_revision: "b".repeat(40), template_sha256: hash, worker_sha256: hash, profile_manifest_sha256: hash, context_tokens: 4096, director_tokens: 350, narrator_tokens: 350, deadline_ms: 120000, repair_limit: 1 };
const report = { version: 2, kind: "paired_snapshots", lane: "scripted", source_matches: false, completed: false, completed_scenes: 0, turns: [turn(), turn("right")], human_reviewed: 0, human_rubric: "Not reviewed", quality_accepted: false, physical_setups: 0, physical_setup_ms: null, native_load: null, left_charged_ms: 1, right_charged_ms: 1, left_reserved_roles: 2, right_reserved_roles: 2, first_semantic_divergence: null, first_mechanical_divergence: null, same_input_pairs: 1, unavailable: ["selected_rerun_not_implemented"], profile, suite_sha256: hash, source_sha256: hash, reference_sha256: null, limitations: ["Synthetic fixture; no human review"] };
const snapshot = { version: 1, protocol_version: 2, binding: hash, report, rows, read_only: true, execution_available: false, unavailable: ["selected_rerun_not_implemented", "full_comparison_gui_not_implemented"] };
const source = { binding: hash, protocol_version: 2, rows, read_only: true, execution_available: false };
const wrapper = (key, value, runToken = token) => ({ version: 1, kind: "comparison_reader", run_token: runToken, [key]: clone(value) });
function status(client, phase = "ready", overrides = {}) {
    return { version: 1, kind: "comparison_reader", client_id: client, operation_id: 1, phase, running: ["choosing", "opening", "reading", "closing"].includes(phase), run_token: phase === "ready" || phase === "reading" ? token : null, binding: phase === "ready" || phase === "reading" ? hash : null, error: phase === "failed" ? "EvaluationIntegrity" : null, read_only: true, execution_available: false, ...overrides };
}
function evidence(request, body) {
    return wrapper("evidence", { version: 1, binding: hash, row, scope, before_head: 0, after_head: 1, observer: request.observer, edge: request.kind === "query" ? request.edge : request.kind === "receipt" ? "after" : null, read_only: true, generation_grant: false, body });
}
const rawRequest = { kind: "outputs", observer: omni };
const rawBody = { kind: "outputs", outputs: [{ role: "director", bytes: 8, sha256: hash, text: "<script>" }] };
let checks = 0;
const check = (name, work) => { work(); checks++; };
check("status ready exact", () => assert.equal(checkedReaderStatus(status(token), token).phase, "ready"));
check("reading phase", () => assert.equal(checkedReaderStatus(status(token, "reading"), token).running, true));
check("historical source is viewable", () => assert.equal(checkedReaderSummary(wrapper("snapshot", snapshot), token, hash).report.source_matches, false));
check("historical omitted estimates stay absent", () => assert.equal(Object.hasOwn(checkedReaderSummary(wrapper("snapshot", snapshot), token, hash).report.turns[0], "forwarded_director_estimates"), false));
check("current estimates remain estimates", () => { const v = wrapper("snapshot", snapshot); v.snapshot.report.turns[0].forwarded_director_estimates = [{ version: 1, prompt_bytes: 100, schema_bytes: 100, repair_extra_bytes: 114, actual_prompt_schema_estimated_tokens: 50, admission_prompt_schema_estimated_tokens: 79, output_tokens: 350, template_reserve_tokens: 162, estimated_total_tokens: 591 }]; assert.equal(checkedReaderSummary(v, token, hash).report.turns[0].forwarded_director_estimates[0].template_reserve_tokens, 162); });
check("source is metadata only", () => assert.equal(checkedReaderSource(wrapper("source", source), token, hash).rows.length, 2));
check("inert raw output", () => assert.equal(checkedReaderEvidence(evidence(rawRequest, rawBody), token, source, row, rawRequest).body.outputs[0].text, "<script>"));
for (const [label, mutate] of [
    ["unknown status key", v => { v.path = "private"; }], ["string operation", v => { v.operation_id = "1"; }], ["unsafe operation", v => { v.operation_id = 2 ** 53; }], ["ready without token", v => { v.run_token = null; }], ["foreign client", v => { v.client_id = randomUUID(); }], ["ready error", v => { v.error = "EvaluationIo"; }], ["unknown error", v => { v.error = "C:/private/path"; }], ["wrong execution", v => { v.execution_available = true; }], ["status prototype", v => Object.setPrototypeOf(v, { injected: true })],
]) check(label, () => { const v = status(token); mutate(v); assert.throws(() => checkedReaderStatus(v, token)); });
for (const [label, mutate] of [
    ["unknown report key", v => { v.snapshot.report.path = "secret"; }], ["coerced bool", v => { v.snapshot.report.completed = "false"; }], ["unsafe elapsed", v => { v.snapshot.report.turns[0].elapsed_ms = 2 ** 53; }], ["unknown policy", v => { v.snapshot.report.turns[0].policy = "other"; }], ["missing report field", v => { delete v.snapshot.report.profile; }], ["unknown turn field", v => { v.snapshot.report.turns[0].hidden = {}; }], ["bad metrics number", v => { v.snapshot.report.native_load = { x: NaN }; }], ["foreign token", v => { v.run_token = randomUUID(); }], ["duplicate rows", v => { v.snapshot.rows[1] = clone(v.snapshot.rows[0]); }], ["row report mismatch", v => { v.snapshot.rows[0].row.turn = "other"; }], ["bad source head", v => { v.snapshot.rows[0].source.after_head = -1; }], ["too many rows", v => { v.snapshot.rows = Array(49).fill(v.snapshot.rows[0]); }], ["oversize whole summary", v => { v.snapshot.report.limitations = ["x".repeat(2 * 1024 * 1024)]; }], ["malformed estimate", v => { v.snapshot.report.turns[0].forwarded_director_estimates = [{ version: 1, estimated_total_tokens: "0" }]; }],
]) check(label, () => { const v = wrapper("snapshot", snapshot); mutate(v); assert.throws(() => checkedReaderSummary(v, token, hash)); });
for (const [label, mutate] of [
    ["foreign evidence binding", v => { v.evidence.binding = "b".repeat(64); }], ["foreign row", v => { v.evidence.row.arm = "right"; }], ["foreign scope", v => { v.evidence.scope.story = "other"; }], ["wrong observer", v => { v.evidence.observer = player; }], ["wrong edge", v => { v.evidence.edge = "after"; }], ["extra author payload", v => { v.evidence.reason = "hidden"; }], ["raw byte mismatch", v => { v.evidence.body.outputs[0].bytes = 7; }], ["over raw cap", v => { v.evidence.body.outputs[0].text = "x".repeat(16385); v.evidence.body.outputs[0].bytes = 16385; }], ["over capture cap", v => { v.evidence.body = { kind: "capture", capture: "x".repeat(196609) }; }],
]) check(label, () => { const v = evidence(rawRequest, rawBody); mutate(v); assert.throws(() => checkedReaderEvidence(v, token, source, row, rawRequest)); });
check("missing preserved", () => { const request = { kind: "capture", observer: omni }; assert.equal(checkedReaderEvidence(evidence(request, { kind: "missing", reason: "capture_unavailable" }), token, source, row, request).body.kind, "missing"); });
check("actor raw denied", () => assert.throws(() => checkedReaderEvidence(evidence({ ...rawRequest, observer: player }, rawBody), token, source, row, { ...rawRequest, observer: player })));
check("accessor rejected without invocation", () => { const v = wrapper("source", source); Object.defineProperty(v, "source", { enumerable: true, get() { assert.fail("getter executed"); } }); assert.throws(() => checkedReaderSource(v, token, hash)); });
check("detached reply", () => { const v = wrapper("source", source), decoded = checkedReaderSource(v, token, hash); v.source.rows.length = 0; assert.equal(decoded.rows.length, 2); });
const queryRequest = { kind: "query", edge: "after", observer: player, view: "history" };
const page = { version: 2, scope, head: 1, revision: 1, story_time: 1, observer: player, view: "history", privacy: "player_visible", status: "supported", total: 0, rows: [], next_cursor: null, unsupported: null };
check("actual Query2 empty page shape", () => assert.equal(checkedReaderEvidence(evidence(queryRequest, { kind: "query", page }), token, source, row, queryRequest).body.page.version, 2));
check("Query2 foreign edge head refused", () => { const v = evidence(queryRequest, { kind: "query", page }); v.evidence.body.page.head = 2; assert.throws(() => checkedReaderEvidence(v, token, source, row, queryRequest)); });
check("Character ScopedMessage lacks experiment player provenance", () => { const request = { ...queryRequest, observer: { kind: "character", id: "player" } }; const v = evidence(request, { kind: "query", page: { ...page, observer: request.observer, privacy: "private_character", total: 1, rows: [{ kind: "scoped_message", key: "1:x", original_scope: scope, turn: row.turn, message_kind: "input", text: "hidden", event_ids: [1], origin: "recorded_message" }] } }); assert.throws(() => checkedReaderEvidence(v, token, source, row, request)); });

const deferred = () => { let resolve, reject; const promise = new Promise((a, b) => { resolve = a; reject = b; }); return { promise, resolve, reject }; };
const tick = async () => { await Promise.resolve(); await Promise.resolve(); };
function fixture() {
    const calls = [], hooks = new Map();
    const invoke = async (name, args) => {
        assert.equal(name, "evaluation_comparison");
        calls.push(clone(args));
        const hook = hooks.get(args.action);
        if (hook) return hook(args.query);
        const q = args.query;
        if (args.action === "pick" || args.action === "status") return status(q.clientId);
        if (args.action === "close") return status(q.clientId, "closed");
        if (args.action === "source") return wrapper("source", source);
        if (args.action === "summary") return wrapper("snapshot", snapshot);
        if (args.action === "evidence") return evidence(q.request, rawBody);
        assert.fail(`unexpected ${args.action}`);
    };
    const c = new ComparisonReaderController(invoke);
    c.contextChanged("root/window/session/head/Lab", true);
    return { c, calls, hooks };
}
async function test(name, work) { await work(); checks++; }
await test("pick same controller and metadata only", async () => { const { c, calls } = fixture(); await c.pick(); assert.equal(c.get().source.rows.length, 2); assert.equal(c.get().summary, null); assert.deepEqual(calls.map(v => v.action), ["pick", "source"]); c.dispose(); });
await test("private summary then actor clears synchronously", async () => { const { c } = fixture(); await c.pick(); await c.loadSummary(); c.select(row); await c.inspect(rawRequest); assert.ok(c.get().summary); assert.ok(c.get().evidence); c.setObserver(player); assert.equal(c.get().summary, null); assert.equal(c.get().evidence, null); assert.equal(c.get().source.rows.length, 2); assert.equal(c.get().status.run_token, token); c.dispose(); });
await test("actor raw no dispatch", async () => { const { c, calls } = fixture(); await c.pick(); c.select(row); c.setObserver(player); const before = calls.length; await c.inspect({ kind: "outputs", observer: player }); await c.loadSummary(); assert.equal(calls.length, before); assert.equal(c.get().error, "Forbidden"); c.dispose(); });
await test("unknown pick explicit SAME client recover only", async () => { const { c, hooks, calls } = fixture(); hooks.set("pick", () => { throw new Error("lost ack private path"); }); await c.pick(); const client = c.get().clientId; assert.equal(c.get().uncertain, true); assert.equal(c.get().error, "EvaluationIo"); await c.pick(); assert.equal(calls.filter(v => v.action === "pick").length, 1); await c.recover(); assert.equal(calls.find(v => v.action === "status").query.clientId, client); assert.equal(c.get().uncertain, false); c.dispose(); });
await test("malformed terminal keeps recovery identity", async () => { const { c, hooks } = fixture(); hooks.set("pick", q => ({ ...status(q.clientId), alien: true })); await c.pick(); assert.ok(c.get().clientId); assert.equal(c.get().uncertain, true); await c.recover(); assert.equal(c.get().status.phase, "ready"); c.dispose(); });
await test("synchronous navigation before pick denies side effect", async () => { const { c, calls } = fixture(); let once = true; c.subscribe(() => { if (once && c.get().busy) { once = false; c.contextChanged("other", false); } }); await c.pick(); assert.equal(calls.filter(v => v.action === "pick").length, 0); assert.equal(c.get().source, null); c.dispose(); });
await test("synchronous dispose before pick denies side effect", async () => { const { c, calls } = fixture(); c.subscribe(() => { if (c.get().busy) c.dispose(); }); await c.pick(); assert.equal(calls.filter(v => v.action === "pick").length, 0); });
await test("late pick closes ORIGINAL client/token", async () => { const { c, hooks, calls } = fixture(), hold = deferred(); hooks.set("pick", q => hold.promise.then(() => status(q.clientId))); const pending = c.pick(); await tick(); const client = calls[0].query.clientId; c.contextChanged("other", true); hold.resolve(); await pending; await tick(); assert.equal(c.get().source, null); assert.ok(calls.some(v => v.action === "close" && v.query.clientId === client && v.query.runToken === token)); c.dispose(); });
await test("same key permission revocation clears and closes", async () => { const { c, calls } = fixture(); await c.pick(); await c.loadSummary(); const context = c.get().context; c.contextChanged(context, false); assert.equal(c.get().summary, null); assert.equal(c.get().source, null); await tick(); assert.ok(calls.some(v => v.action === "close")); c.dispose(); });
await test("summary reply after actor transition suppressed", async () => { const { c, hooks } = fixture(); await c.pick(); const hold = deferred(); hooks.set("summary", () => hold.promise); const pending = c.loadSummary(); c.setObserver(player); hold.resolve(wrapper("snapshot", snapshot)); await pending; assert.equal(c.get().summary, null); c.dispose(); });
await test("synchronous selection listener suppresses evidence admission", async () => { const { c, calls } = fixture(); await c.pick(); c.select(row); let once = true; c.subscribe(() => { if (once && c.get().busy) { once = false; c.select({ turn: row.turn, arm: "right" }); } }); await c.inspect(rawRequest); assert.equal(calls.filter(v => v.action === "evidence").length, 0); c.dispose(); });
await test("evidence pending context change clears all private", async () => { const { c, hooks } = fixture(); await c.pick(); c.select(row); const hold = deferred(); hooks.set("evidence", () => hold.promise); const pending = c.inspect(rawRequest); c.contextChanged("other", true); hold.resolve(evidence(rawRequest, rawBody)); await pending; assert.equal(c.get().evidence, null); assert.equal(c.get().source, null); c.dispose(); });
await test("terminal error callback cannot clobber new context", async () => { const calls = []; let c; c = new ComparisonReaderController(async (_name, args) => { calls.push(args); throw new Error("Forbidden"); }, () => c.contextChanged("new", false)); c.contextChanged("old", true); await c.pick(); assert.equal(c.get().context, "new"); assert.equal(c.get().error, null); c.dispose(); });
await test("close late reply does not clear new context", async () => { const { c, hooks } = fixture(); await c.pick(); const hold = deferred(); hooks.set("close", q => hold.promise.then(() => status(q.clientId, "closed"))); const pending = c.close(); c.contextChanged("new", true); hold.resolve(); await pending; assert.equal(c.get().context, "new"); assert.equal(c.get().source, null); c.dispose(); });
await test("status notification navigation prevents source request", async () => { const { c, calls } = fixture(); let once = true; c.subscribe(() => { if (once && c.get().status?.phase === "ready") { once = false; c.contextChanged("new", false); } }); await c.pick(); assert.equal(calls.filter(v => v.action === "source").length, 0); c.dispose(); });
await test("raw actor validation before row lookup", async () => { const { c, calls } = fixture(); await c.pick(); c.setObserver(player); const before = calls.length; await c.inspect({ kind: "outputs", observer: player }); assert.equal(calls.length, before); assert.equal(c.get().error, "Forbidden"); c.dispose(); });
await test("known pending polls status SAME client without repick", async () => { const { c, hooks, calls } = fixture(); hooks.set("pick", q => status(q.clientId, "choosing")); await c.pick(); assert.equal(c.get().status.phase, "ready"); assert.equal(calls.filter(v => v.action === "pick").length, 1); assert.ok(calls.some(v => v.action === "status" && v.query.clientId === calls[0].query.clientId)); c.dispose(); });
const result = { version: 1, checks, passed: true, synthetic_transport: true, native_ipc: false, native_rendering: false, model_execution: false };
await writeFile(path.join(output, `comparison-reader-${randomUUID()}.json`), JSON.stringify(result, null, 2));
console.log(JSON.stringify(result));

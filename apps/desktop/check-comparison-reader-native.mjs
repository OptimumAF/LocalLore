// Frozen SOURCE ONLY before pickManaged implementation. UNCOMPILED/UNRUN.
// Source-shaped SYNTHETIC ReaderV1/protocol3 DTOs, mocked transport and actual
// controller/decoders only. No native IPC, Rust, model, renderer or canonical proof.
import assert from "node:assert/strict";
import { build } from "esbuild";
import { mkdir, writeFile } from "node:fs/promises";
import { randomUUID } from "node:crypto";
import { fileURLToPath, pathToFileURL } from "node:url";
import path from "node:path";
const root = fileURLToPath(new URL(".", import.meta.url));
const output = process.env.LOCALLORE_CHECK_OUTPUT_DIR ?? path.join(root, "artifacts/checks");
await mkdir(output, { recursive: true });
const built = await build({
    stdin: {
        contents: 'export * from "./ui/comparison-reader-model"; export * from "./ui/comparison-reader-controller";',
        resolveDir: root, loader: "ts",
    },
    bundle: true, platform: "node", format: "cjs", write: false,
});
const bundle = path.join(output, `comparison-reader-native-${randomUUID()}.cjs`);
await writeFile(bundle, built.outputFiles[0].contents, { flag: "wx" });
const m = (await import(pathToFileURL(bundle).href)).default;
const token = "22222222-2222-2222-2222-222222222222",
    hash = "a".repeat(64);
const scope = { story: "synthetic-literal-reader", branch: "main" };
const clone = (value) => structuredClone(value);
const literal = {
    arm: "literal_player_v1",
    prompt_version: "locallore-play-v2.6-literal-director-v1",
    narration_policy: "grounded-prose-v2.2",
    director_schema_id: "locallore-director-literal-v1",
    context_policy: null,
    compiler_version: null,
    context_version: null,
    literal_source_version: 1,
    literal_render_version: 1,
    literal_schema_version: 1,
    literal_packing_version: 1,
    forwarded_budget_version: 1,
};
const relevant = {
    arm: "relevant_memory_v1",
    prompt_version: "locallore-play-v2.5",
    narration_policy: "grounded-prose-v2.2",
    director_schema_id: "locallore-director-v2",
    context_policy: "state_relevant_memory_v1",
    compiler_version: 2,
    context_version: 2,
    literal_source_version: null,
    literal_render_version: null,
    literal_schema_version: null,
    literal_packing_version: null,
    forwarded_budget_version: 1,
};
function row2(arm = "left") {
    return {
        turn: "move-4",
        scene: 1,
        arm,
        policy:
            arm === "left"
                ? "state_recent_transcript_v1"
                : "state_relevant_memory_v1",
        phase: "committed",
        error: null,
        expected: '{"Accepted":{"op":"move","to":"pier"}}',
        passed: true,
        failures: [],
        quality_flags: [],
        roles: 2,
        roles_known: true,
        recovered_without_checkpoint: false,
        admission: 1,
        elapsed_ms: 1,
        first_final_response_ms: 1,
        commit_elapsed_ms: 0,
        input_semantic_sha256: hash,
        output_semantic_sha256: hash,
        mechanical_sha256: hash,
        policy_matches: true,
        context_evidence_available: true,
        context_requirement: "required_actual_capture",
        privacy_passed: true,
        fallback: false,
        capture_sha256: hash,
        recording_sha256: hash,
        raw_sha256: [hash, hash],
        role_metrics: null,
        trace: null,
        actual_receipt_sha256: hash,
        source_fallback_reason: null,
        compiler_fallback_reason: null,
        narration: "Synthetic accepted prose",
        repairs: 0,
        stages: [],
        mandatory_sha256: hash,
        optional_detail_selected: false,
        director_private_target_present: false,
        selected_context_bytes: 100,
        estimated_context_tokens: 25,
    };
}
function row3(arm = "left") {
    const row = row2(arm);
    delete row.policy;
    delete row.policy_matches;
    Object.assign(row, {
        construction: clone(arm === "left" ? literal : relevant),
        construction_matches: true,
        construction_evidence_status:
            arm === "left" ? "validated_literal" : "validated_relevant",
        literal_source_units: arm === "left" ? 3 : null,
        literal_selected_start: arm === "left" ? 1 : null,
        literal_selected_units: arm === "left" ? 2 : null,
        forwarded_director_estimates: null,
    });
    if (arm === "left")
        for (const field of [
            "mandatory_sha256",
            "optional_detail_selected",
            "source_fallback_reason",
            "compiler_fallback_reason",
            "selected_context_bytes",
            "estimated_context_tokens",
        ])
            row[field] = null;
    return row;
}
function availability(row) {
    return {
        row: { turn: row.turn, arm: row.arm },
        source: {
            status: "available",
            scope: clone(scope),
            before_head: 4,
            after_head: row.phase === "committed" ? 5 : 4,
            input_semantic_sha256: hash,
        },
        capture_available: row.capture_sha256 !== null,
        recording_available: true,
        receipt_available: row.actual_receipt_sha256 !== null,
        unavailable: [
            ...(row.capture_sha256 === null ? ["capture_unavailable"] : []),
            ...(row.actual_receipt_sha256 === null
                ? ["no_accepted_receipt"]
                : []),
        ],
    };
}
function snapshot(version = 3) {
    const turns = [
        version === 3 ? row3() : row2(),
        version === 3 ? row3("right") : row2("right"),
    ];
    const report = {
        version,
        ...(version === 3 ? { arms: [clone(literal), clone(relevant)] } : {}),
        kind: "paired_snapshots",
        lane: "scripted_current_comparison",
        source_matches: false,
        completed: false,
        completed_scenes: 0,
        turns,
        human_reviewed: 0,
        human_rubric: "not_reviewed",
        quality_accepted: false,
        physical_setups: 0,
        physical_setup_ms: null,
        native_load: null,
        left_charged_ms: 1,
        right_charged_ms: 1,
        left_reserved_roles: 2,
        right_reserved_roles: 2,
        first_semantic_divergence: null,
        first_mechanical_divergence: null,
        same_input_pairs: 1,
        unavailable: [],
        profile: {
            id: "synthetic-reader",
            model_sha256: hash,
            runtime_revision: "b".repeat(40),
            template_sha256: hash,
            worker_sha256: hash,
            profile_manifest_sha256: hash,
            context_tokens: 4096,
            director_tokens: 350,
            narrator_tokens: 350,
            deadline_ms: 120000,
            repair_limit: 1,
        },
        suite_sha256: hash,
        source_sha256: hash,
        reference_sha256: null,
        limitations: ["Synthetic DTO; no real execution or quality acceptance"],
    };
    return {
        version: 1,
        protocol_version: version,
        binding: hash,
        report,
        rows: turns.map(availability),
        read_only: true,
        execution_available: false,
        unavailable: [],
    };
}
const wrap = (key, value) => ({
    version: 1,
    kind: "comparison_reader",
    run_token: token,
    [key]: value,
});
const source = (value) => {
    const { binding, protocol_version, rows, read_only, execution_available } =
        value;
    return { binding, protocol_version, rows, read_only, execution_available };
};

// Fixture shapes copied from the existing literal reader checker. Their hashes
// are inert synthetic labels, not proofs of native execution or accepted receipts.
const runId = "11111111-1111-4111-8111-111111111111";
const native = () => ({ runId, mode: "approved_native" });
const omni = { kind: "omniscient" }, player = { kind: "player" };
const row = { turn: "move-4", arm: "left" };
const raw = { kind: "outputs", observer: omni };
const rawBody = { kind: "outputs", outputs: [
    { role: "director", bytes: 8, sha256: hash, text: "<script>" },
] };
const reader = "evaluation_comparison";
const nativeCommand = "evaluation_comparison_native";
const deferred = () => {
    let resolve, reject;
    const promise = new Promise((yes, no) => { resolve = yes; reject = no; });
    return { promise, resolve, reject };
};
const tick = async () => { for (let i = 0; i < 12; i++) await Promise.resolve(); };
function status(client, phase = "ready") {
    return { version: 1, kind: "comparison_reader", client_id: client,
        operation_id: 1, phase,
        running: ["choosing", "opening", "reading", "closing"].includes(phase),
        run_token: ["ready", "reading"].includes(phase) ? token : null,
        binding: ["ready", "reading"].includes(phase) ? hash : null,
        error: null, read_only: true, execution_available: false };
}
function evidence(request) {
    return wrap("evidence", { version: 1, binding: hash, row, scope,
        before_head: 4, after_head: 5, observer: clone(request.observer),
        edge: null, read_only: true, generation_grant: false, body: clone(rawBody) });
}
function fixture() {
    const calls = [], hooks = new Map(), errors = [];
    const invoke = async (name, args) => {
        assert.ok([reader, nativeCommand].includes(name));
        assert.deepEqual(Object.keys(args).sort(), ["action", "query"]);
        assert.equal(typeof args.query, "object");
        assert.notEqual(args.query, null);
        calls.push(clone({ name, ...args }));
        const hook = hooks.get(`${name}:${args.action}`) ?? hooks.get(args.action);
        if (hook) return hook(args.query);
        if (name !== reader) {
            assert.equal(args.action, "managed");
            assert.deepEqual(Object.keys(args.query).sort(), ["clientId", "runId"]);
            return status(args.query.clientId);
        }
        const q = args.query;
        if (["pick", "managed", "status"].includes(args.action)) return status(q.clientId);
        if (args.action === "close") return status(q.clientId, "closed");
        if (args.action === "source") return wrap("source", source(snapshot()));
        if (args.action === "summary") return wrap("snapshot", snapshot());
        if (args.action === "evidence") return evidence(q.request);
        assert.fail("unexpected fixed reader action");
    };
    const c = new m.ComparisonReaderController(invoke, (error) => errors.push(error));
    c.contextChanged("synthetic/root/window/session/head/Lab", true);
    return { c, calls, hooks, errors };
}
const cases = [];
async function test(name, work) {
    try { await work(); cases.push({ name, passed: true }); }
    catch (error) { cases.push({ name, passed: false,
        error: error instanceof Error ? error.name : "ThrownValue" }); }
}
const trace = (calls) => calls.map(({ name, action }) => [name, action]);
async function using(work) {
    const f = fixture();
    try { await work(f); } finally { f.c.dispose(); await tick(); }
}
await test("native managed entry only; all acknowledged followups use ReaderV1", () => using(async ({ c, calls }) => {
    await c.pickManaged(native());
    const client = c.get().clientId;
    assert.equal(c.get().status.version, 1);
    assert.equal(c.get().source.protocol_version, 3);
    assert.equal(c.get().summary, null);
    await c.loadSummary(); c.select(row); await c.inspect(raw); await c.recover(); await c.close();
    assert.deepEqual(trace(calls), [
        [nativeCommand, "managed"], [reader, "source"], [reader, "summary"],
        [reader, "evidence"], [reader, "status"], [reader, "source"], [reader, "close"],
    ]);
    assert.deepEqual(calls[0].query, { clientId: client, runId });
    assert.deepEqual(calls.at(-1).query, { clientId: client, runToken: token });
    assert.equal(c.get().source, null);
}));
await test("legacy pick(runId) keeps scripted managed routing", () => using(async ({ c, calls }) => {
    await c.pick(runId);
    // Existing comparison_commands::Managed is the scripted reader admission;
    // evaluation_comparison_run is the execution command, not a reader route.
    assert.deepEqual(trace(calls), [[reader, "managed"], [reader, "source"]]);
}));
await test("explicit scripted identity keeps scripted managed routing", () => using(async ({ c, calls }) => {
    await c.pickManaged({ runId, mode: "scripted_baseline" });
    assert.deepEqual(trace(calls), [[reader, "managed"], [reader, "source"]]);
}));
await test("ordinary picker stays existing ReaderV1 path", () => using(async ({ c, calls }) => {
    await c.pick();
    assert.deepEqual(trace(calls), [[reader, "pick"], [reader, "source"]]);
}));
for (const [label, value] of [
    ["unknown mode", { runId, mode: "native" }],
    ["missing mode", { runId }],
    ["uppercase UUID", { runId: "AAAAAAAA-AAAA-4AAA-8AAA-AAAAAAAAAAAA", mode: "approved_native" }],
    ["invalid run", { runId: "../run", mode: "approved_native" }],
    ["null identity", null],
    ["renderer command", { ...native(), command: "evaluation_comparison_run" }],
    ["renderer provider", { ...native(), provider: "arbitrary" }],
]) await test(`closed identity rejects ${label} without transport`, () => using(async ({ c, calls }) => {
    await c.pickManaged(value);
    assert.equal(calls.length, 0);
    assert.equal(c.get().clientId, null);
    assert.equal(c.get().error, "ComparisonReaderWire");
}));
await test("copy closed identity before synchronous pending notification", () => using(async ({ c, calls }) => {
    const input = native();
    c.subscribe(() => { if (c.get().busy) input.mode = "scripted_baseline"; });
    await c.pickManaged(input);
    assert.equal(calls[0].name, nativeCommand);
    assert.equal(calls[0].query.runId, runId);
}));
await test("reentrant context retirement before dispatch issues no managed call", () => using(async ({ c, calls }) => {
    let once = true;
    c.subscribe(() => { if (once && c.get().busy) { once = false; c.contextChanged("retired", false); } });
    await c.pickManaged(native());
    assert.equal(calls.length, 0);
    assert.equal(c.get().source, null);
}));
await test("reentrant second managed pick cannot replace pending native origin", () => using(async ({ c, calls }) => {
    let nested = null;
    c.subscribe(() => {
        if (nested === null && c.get().busy) {
            nested = c.pickManaged({ runId, mode: "scripted_baseline" });
        }
    });
    await c.pickManaged(native());
    await nested;
    assert.deepEqual(trace(calls), [[nativeCommand, "managed"], [reader, "source"]]);
}));
await test("held native ACK retired by context releases only original reader client", () => using(async ({ c, hooks, calls }) => {
    const hold = deferred();
    hooks.set(`${nativeCommand}:managed`, (q) => hold.promise.then(() => status(q.clientId)));
    const pending = c.pickManaged(native()); await tick();
    const client = c.get().clientId;
    try { c.contextChanged("other/root", true); } finally { hold.resolve(); }
    await pending; await tick();
    assert.equal(c.get().source, null); assert.equal(c.get().clientId, null);
    assert.equal(calls.filter((v) => v.action === "source").length, 0);
    const closes = calls.filter((v) => v.action === "close");
    assert.ok(closes.some((v) => v.query.clientId === client && v.query.runToken === token));
    assert.ok(closes.every((v) => v.name === reader && v.query.clientId === client));
}));
await test("close during held native ACK never publishes private source", () => using(async ({ c, hooks, calls }) => {
    const hold = deferred();
    hooks.set(`${nativeCommand}:managed`, (q) => hold.promise.then(() => status(q.clientId)));
    const pending = c.pickManaged(native()); await tick();
    try { await c.close(); } finally { hold.resolve(); }
    await pending; await tick();
    assert.equal(c.get().source, null); assert.equal(c.get().clientId, null);
    assert.ok(calls.filter((v) => v.action === "close").every((v) => v.name === reader));
    assert.equal(calls.filter((v) => v.action === "source").length, 0);
}));
await test("dispose during held native ACK fences publication and late close routing", () => using(async ({ c, hooks, calls }) => {
    const hold = deferred();
    hooks.set(`${nativeCommand}:managed`, (q) => hold.promise.then(() => status(q.clientId)));
    const pending = c.pickManaged(native()); await tick();
    try { c.dispose(); } finally { hold.resolve(); }
    await pending; await tick();
    assert.equal(c.get().source, null);
    assert.ok(calls.some((v) => v.action === "close" && v.query.runToken === token));
    assert.ok(calls.filter((v) => v.action === "close").every((v) => v.name === reader));
}));
await test("lens change during native managed ACK retains cap but no private summary", () => using(async ({ c, hooks, calls }) => {
    const hold = deferred();
    hooks.set(`${nativeCommand}:managed`, (q) => hold.promise.then(() => status(q.clientId)));
    const pending = c.pickManaged(native()); await tick();
    try { c.setObserver(player); } finally { hold.resolve(); }
    await pending;
    assert.equal(c.get().observer.kind, "player");
    assert.equal(c.get().status.run_token, token); assert.ok(c.get().source);
    assert.equal(c.get().summary, null); assert.equal(c.get().evidence, null);
    assert.equal(calls.filter((v) => v.action === "close").length, 0);
}));
await test("held raw output cannot republish after actor lens change", () => using(async ({ c, hooks }) => {
    await c.pickManaged(native()); await c.loadSummary(); c.select(row);
    const hold = deferred(); hooks.set("evidence", (q) => hold.promise.then(() => evidence(q.request)));
    const pending = c.inspect(raw); await tick();
    try { c.setObserver({ kind: "character", id: "mira" }); } finally { hold.resolve(); }
    await pending;
    assert.equal(c.get().summary, null); assert.equal(c.get().evidence, null);
    assert.ok(c.get().source);
}));
await test("actor raw rejected before any binding, row or transport", () => using(async ({ c, calls }) => {
    c.setObserver(player);
    await c.inspect({ kind: "capture", observer: player });
    assert.equal(c.get().error, "Forbidden"); assert.equal(calls.length, 0);
    await c.pickManaged(native());
    const count = calls.length;
    await c.inspect({ kind: "outputs", observer: player }); await c.loadSummary();
    assert.equal(c.get().error, "Forbidden"); assert.equal(calls.length, count);
}));
await test("lost managed ACK requires same-client ReaderV1 recovery without auto-pick", () => using(async ({ c, hooks, calls }) => {
    hooks.set(`${nativeCommand}:managed`, () => { throw new Error("EvaluationIo"); });
    await c.pickManaged(native());
    const client = c.get().clientId;
    assert.equal(c.get().uncertain, true); assert.ok(client);
    await c.pickManaged(native());
    assert.equal(calls.filter((v) => v.action === "managed").length, 1);
    await c.recover();
    assert.equal(calls.find((v) => v.action === "status").name, reader);
    assert.equal(calls.find((v) => v.action === "status").query.clientId, client);
    assert.equal(c.get().uncertain, false);
}));
await test("native consent refusal never retries scripted managed or auto-opens", () => using(async ({ c, hooks, calls }) => {
    hooks.set(`${nativeCommand}:managed`, (q) => status(q.clientId, "cancelled"));
    await c.pickManaged(native());
    assert.equal(c.get().status.phase, "cancelled");
    assert.equal(c.get().source, null); assert.equal(c.get().summary, null);
    assert.deepEqual(trace(calls), [[nativeCommand, "managed"]]);
}));
const result = { version: 1, source_only_freeze: true, cases,
    passed: cases.every((v) => v.passed), synthetic_transport: true,
    native_ipc: false, native_rendering: false, model_execution: false,
    canonical_validation: false };
await writeFile(path.join(output, `comparison-reader-native-${randomUUID()}.json`),
    JSON.stringify(result, null, 2), { flag: "wx" });
console.log(JSON.stringify(result));
if (!result.passed) process.exitCode = 1;

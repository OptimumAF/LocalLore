// Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0
// FIRST independent SOURCE freeze; author UNRUN. Synthetic DTOs exercise the
// existing public decoder only, never Rust/Store/IPC/WebView/model authority.
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
    stdin: { contents: 'export * from "./ui/comparison-reader-model";', resolveDir: root, loader: "ts" },
    bundle: true, platform: "node", format: "cjs", write: false,
});
const bundle = path.join(output, `scene-reader-${randomUUID()}.cjs`);
await writeFile(bundle, built.outputFiles[0].contents, { flag: "wx" });
const m = (await import(pathToFileURL(bundle).href)).default;
const token = "22222222-2222-2222-2222-222222222222";
const hash = "a".repeat(64), otherHash = "b".repeat(64);
const scope = { story: "synthetic-scene-reader", branch: "main" };
const clone = (value) => structuredClone(value);
const plain = (value) => JSON.parse(JSON.stringify(value));
const wrap = (key, value) => ({ version: 1, kind: "comparison_reader", run_token: token, [key]: value });
const decode = (value) => m.checkedReaderSummary(wrap("snapshot", value), token, hash);
function source(value) {
    const { binding, protocol_version, rows, read_only, execution_available } = value;
    return { binding, protocol_version, rows, read_only, execution_available };
}
const readSource = (value) => m.checkedReaderSource(wrap("source", source(value)), token, hash);

// Literal expectations are independently copied from the closed native metadata
// contract. No production descriptor builder is imported to manufacture them.
const literal4 = {
    arm: "literal_scene_v1",
    prompt_version: "locallore-play-v2.10-literal-director-v1-scene-frame-v1",
    narration_policy: "grounded-prose-v2.4-scene-frame-v1",
    director_schema_id: "locallore-director-literal-v1",
    narrator_schema_id: "locallore-narrator-v2",
    context_policy: null, compiler_version: null, context_version: null,
    literal_source_version: 1, literal_render_version: 1,
    literal_schema_version: 1, literal_packing_version: 1,
    forwarded_budget_version: 1, scene_frame_version: 1, scene_capture_gate_version: 1,
};
const relevant4 = {
    arm: "relevant_memory_scene_v1",
    prompt_version: "locallore-play-v2.9-scene-frame-v1",
    narration_policy: "grounded-prose-v2.4-scene-frame-v1",
    director_schema_id: "locallore-director-v2",
    narrator_schema_id: "locallore-narrator-v2",
    context_policy: "state_relevant_memory_v1", compiler_version: 2, context_version: 2,
    literal_source_version: null, literal_render_version: null,
    literal_schema_version: null, literal_packing_version: null,
    forwarded_budget_version: 1, scene_frame_version: 1, scene_capture_gate_version: 1,
};
function descriptor3(arm) {
    const d = clone(arm === "left" ? literal4 : relevant4);
    delete d.narrator_schema_id;
    delete d.scene_frame_version;
    delete d.scene_capture_gate_version;
    d.arm = arm === "left" ? "literal_player_v1" : "relevant_memory_v1";
    d.prompt_version = arm === "left" ? "locallore-play-v2.6-literal-director-v1" : "locallore-play-v2.5";
    d.narration_policy = "grounded-prose-v2.2";
    return d;
}
function commonTurn(arm) {
    return {
        turn: "courier-01", scene: 0, arm, phase: "committed", error: null,
        expected: "accepted", passed: true, failures: [], quality_flags: [],
        roles: 2, roles_known: true, recovered_without_checkpoint: false,
        admission: 0, elapsed_ms: 2, first_final_response_ms: 1, commit_elapsed_ms: 0,
        input_semantic_sha256: hash, output_semantic_sha256: otherHash, mechanical_sha256: hash,
        fallback: false, repairs: 0, narration: "Synthetic transport text; no inference executed.",
        capture_sha256: hash, recording_sha256: otherHash, raw_sha256: [hash, otherHash],
        role_metrics: null, trace: null, stages: [],
        actual_receipt_sha256: otherHash, source_fallback_reason: null, compiler_fallback_reason: null,
    };
}
function oldTurn(version, arm) {
    const row = {
        ...commonTurn(arm), context_evidence_available: true, context_requirement: "required_actual_capture",
        privacy_passed: true, mandatory_sha256: arm === "right" ? hash : null,
        optional_detail_selected: arm === "right" ? false : null,
        director_private_target_present: false,
        selected_context_bytes: arm === "right" ? 100 : null,
        estimated_context_tokens: arm === "right" ? 25 : null,
    };
    if (version === 2) Object.assign(row, {
        policy: arm === "left" ? "state_recent_transcript_v1" : "state_relevant_memory_v1",
        policy_matches: true,
    });
    else Object.assign(row, {
        construction: descriptor3(arm), construction_matches: true,
        construction_evidence_status: arm === "left" ? "validated_literal" : "validated_relevant",
        literal_source_units: arm === "left" ? 3 : null,
        literal_selected_start: arm === "left" ? 1 : null,
        literal_selected_units: arm === "left" ? 2 : null,
        forwarded_director_estimates: null,
    });
    return row;
}
function turn4(arm) {
    return {
        ...commonTurn(arm), construction: clone(arm === "left" ? literal4 : relevant4),
        construction_matches: true,
        construction_evidence_status: "validated_committed_scene_narrator_v1",
        construction_evidence_reason: null,
        narrator_prompt_sha256: hash, narrator_schema_sha256: otherHash,
        scene_frame_sha256: "c".repeat(64), privacy_evidence_status: "checked_finite_sentinels",
    };
}
function availability(row) {
    const capture = row.capture_sha256 !== null, recording = row.recording_sha256 !== null;
    const receipt = row.actual_receipt_sha256 !== null;
    return {
        row: { turn: row.turn, arm: row.arm },
        source: { status: "available", scope: clone(scope), before_head: 4,
            after_head: receipt ? 5 : 4, input_semantic_sha256: row.input_semantic_sha256 },
        capture_available: capture, receipt_available: receipt, recording_available: recording,
        unavailable: [...(capture ? [] : ["capture_unavailable"]),
            ...(recording ? [] : ["recording_unavailable"]), ...(receipt ? [] : ["no_accepted_receipt"])],
    };
}
function snapshot(version = 4) {
    const turns = ["left", "right"].map((arm) => version === 4 ? turn4(arm) : oldTurn(version, arm));
    const report = {
        version, ...(version === 2 ? {} : { arms: version === 4 ? [clone(literal4), clone(relevant4)] : [descriptor3("left"), descriptor3("right")] }),
        kind: "paired_snapshots", lane: "scripted_scene_comparison",
        source_matches: false, completed: false, completed_scenes: 0, turns,
        human_reviewed: 0, human_rubric: "not_reviewed", quality_accepted: false,
        physical_setups: 0, physical_setup_ms: null, native_load: null,
        left_charged_ms: 2, right_charged_ms: 2, left_reserved_roles: 2, right_reserved_roles: 2,
        first_semantic_divergence: null, first_mechanical_divergence: null, same_input_pairs: 1,
        ...(version === 4 ? { source_bound_committed_rows: 2 } : {}),
        unavailable: ["synthetic_fixture_no_native_or_model_execution"],
        profile: { id: "synthetic-scene-reader", model_sha256: hash, runtime_revision: "d".repeat(40),
            template_sha256: otherHash, worker_sha256: hash, profile_manifest_sha256: otherHash,
            context_tokens: 4096, director_tokens: 350, narrator_tokens: 350, deadline_ms: 120000, repair_limit: 1 },
        suite_sha256: hash, source_sha256: otherHash, reference_sha256: null,
        limitations: ["Synthetic DTO only; source-bound Domain1 narrator input does not authenticate Director/raw output.",
            "Original eight-sample human assessment: needs improvement; no new human review."],
    };
    return { version: 1, protocol_version: version, binding: hash, report, rows: turns.map(availability),
        read_only: true, execution_available: false,
        unavailable: [version === 4 ? "selected_protocol4_rerun_not_implemented" : "selected_rerun_not_implemented"] };
}

const cases = [];
function test(name, work) {
    try { work(); cases.push({ name, passed: true }); }
    catch (error) { cases.push({ name, passed: false, error: error instanceof Error ? error.message.slice(0, 180) : "failure" }); }
}
function rejects(name, mutate) {
    test(name, () => { const v = snapshot(); mutate(v); assert.throws(() => decode(v), /ComparisonReaderWire/); });
}
for (const version of [2, 3]) test(`old protocol${version} positive control is lossless and stays its version`, () => {
    const v = snapshot(version);
    assert.deepEqual(plain(decode(v)), v);
    assert.deepEqual(plain(readSource(v)), source(v));
});
test("closed4 is lossless, distinct and read-only without selected execution", () => {
    const v = snapshot(), decoded = decode(v), src = readSource(v);
    assert.deepEqual(plain(decoded), v);
    assert.deepEqual(plain(src), source(v));
    assert.equal(decoded.protocol_version, 4);
    assert.equal(decoded.report.version, 4);
    assert.equal(decoded.execution_available, false);
    assert.deepEqual(plain(decoded.unavailable), ["selected_protocol4_rerun_not_implemented"]);
    assert.deepEqual(plain(decoded.report.arms), [literal4, relevant4]);
    assert.equal(Object.keys(decoded.report.arms[0]).length, 15);
    assert.equal(decoded.report.human_reviewed, 0);
    assert.equal(decoded.report.human_rubric, "not_reviewed");
    assert.equal(decoded.report.quality_accepted, false);
    assert.equal(decoded.report.source_bound_committed_rows, 2);
    assert.equal(decoded.report.source_matches, false);
    assert.equal("policy" in decoded.report.turns[0], false);
});
test("source equality preserves protocol4 identities and availability", () => {
    const a = readSource(snapshot());
    assert.equal(m.sameReaderSource(a, readSource(snapshot())), true);
    for (const mutate of [(b) => { b.protocol_version = 3; },
        (b) => { b.rows[0].source.input_semantic_sha256 = otherHash; },
        (b) => { b.rows[0].source.scope.branch = "other"; },
        (b) => { b.rows[0].source.after_head++; }]) {
        const b = plain(a); mutate(b); assert.equal(m.sameReaderSource(a, b), false);
    }
});
test("decoder detaches complete4 DTO without losing opaque diagnostics", () => {
    const v = snapshot();
    v.report.turns[0].role_metrics = { synthetic: [1, null, "bounded opaque"] };
    v.report.turns[0].trace = { synthetic: true };
    v.report.turns[0].stages = [{ synthetic: "not an execution assertion" }];
    const expected = clone(v), decoded = decode(v);
    v.report.arms[0].prompt_version = "changed";
    v.rows[0].source.scope.story = "changed";
    v.report.turns[0].role_metrics.synthetic.length = 0;
    assert.deepEqual(plain(decoded), expected);
});
for (const arm of [0, 1]) for (const key of Object.keys(literal4)) {
    rejects(`descriptor arm${arm} requires ${key} including explicit null`, (v) => { delete v.report.arms[arm][key]; });
    rejects(`self-consistent unsupported descriptor arm${arm} ${key} is refused`, (v) => {
        const old = v.report.arms[arm][key];
        const changed = old === null ? 1 : typeof old === "number" ? old + 1 : "unsupported";
        v.report.arms[arm][key] = changed;
        v.report.turns[arm].construction[key] = changed;
    });
}
for (const arm of [0, 1]) test(`every row descriptor field is required for arm${arm}`, () => {
    for (const key of Object.keys(literal4)) {
        const v = snapshot(); delete v.report.turns[arm].construction[key];
        assert.throws(() => decode(v), /ComparisonReaderWire/, key);
    }
});
for (const [name, mutate] of [
    ["physical arm swap", (v) => { v.report.turns[0].construction = clone(relevant4); }],
    ["report descriptor order", (v) => { v.report.arms.reverse(); }],
    ["duplicate report descriptor", (v) => { v.report.arms[1] = clone(literal4); }],
    ["row descriptor differs from report", (v) => { v.report.turns[0].construction.scene_frame_version = 2; }],
    ["row descriptor future field", (v) => { v.report.turns[0].construction.future = true; }],
    ["legacy3 tuple cannot be relabeled4", (v) => { v.report.arms = [descriptor3("left"), descriptor3("right")]; v.report.turns.forEach((r) => { r.construction = descriptor3(r.arm); }); }],
    ["rows reorder", (v) => { v.rows.reverse(); }],
    ["duplicate row", (v) => { v.rows[1] = clone(v.rows[0]); }],
    ["extra report row", (v) => { const r = clone(v.report.turns[0]); r.turn = "extra"; v.report.turns.push(r); }],
    ["row input fingerprint mismatch", (v) => { v.rows[0].source.input_semantic_sha256 = otherHash; }],
    ["source4/report3 disagreement", (v) => { v.report = snapshot(3).report; }],
    ["source3/report4 disagreement", (v) => { v.protocol_version = 3; }],
    ["future protocol5", (v) => { v.protocol_version = 5; v.report.version = 5; }],
    ["execution grant", (v) => { v.execution_available = true; }],
    ["writable source", (v) => { v.read_only = false; }],
]) rejects(name, mutate);
const nullableRows = ["error", "admission", "first_final_response_ms", "commit_elapsed_ms",
    "construction_evidence_reason", "narrator_prompt_sha256", "narrator_schema_sha256", "scene_frame_sha256",
    "actual_receipt_sha256", "fallback", "repairs", "narration", "capture_sha256", "recording_sha256",
    "role_metrics", "trace", "source_fallback_reason", "compiler_fallback_reason"];
for (const key of nullableRows) rejects(`required nullable4 row field ${key} cannot disappear`, (v) => { delete v.report.turns[0][key]; });
for (const key of ["construction", "construction_matches", "construction_evidence_status", "privacy_evidence_status"])
    rejects(`required4 row field ${key} cannot disappear`, (v) => { delete v.report.turns[0][key]; });
rejects("source-bound row count is a required4 report field", (v) => { delete v.report.source_bound_committed_rows; });
for (const key of ["physical_setup_ms", "native_load", "first_semantic_divergence", "first_mechanical_divergence", "reference_sha256"])
    rejects(`required nullable4 report field ${key} cannot disappear`, (v) => { delete v.report[key]; });
test("explicit nullable diagnostics are retained without fabricating fields", () => {
    const v = snapshot(), row = v.report.turns[0];
    for (const key of nullableRows) row[key] = null;
    row.phase = "failed"; row.passed = false; row.construction_matches = false;
    row.construction_evidence_status = "unavailable"; row.privacy_evidence_status = "unavailable";
    v.report.source_bound_committed_rows = 1; v.rows[0] = availability(row);
    assert.deepEqual(plain(decode(v)), v);
});
for (const key of ["narrator_prompt_sha256", "narrator_schema_sha256", "scene_frame_sha256", "actual_receipt_sha256"])
    rejects(`malformed new or actual hash ${key}`, (v) => { v.report.turns[0][key] = "not-sha256"; });
for (const key of ["policy", "policy_matches", "context_evidence_available", "context_requirement", "privacy_passed",
    "mandatory_sha256", "optional_detail_selected", "director_private_target_present", "selected_context_bytes",
    "estimated_context_tokens", "literal_source_units", "literal_selected_start", "literal_selected_units", "forwarded_director_estimates"])
    rejects(`V4 does not inherit legacy row field ${key}`, (v) => { v.report.turns[0][key] = null; });
for (const [construction, privacy] of [["not_applicable_guard", "not_applicable_guard"],
    ["not_applicable_dependency", "unavailable"], ["unavailable", "unavailable"]]) test(`closed statuses retained ${construction}/${privacy}`, () => {
    const v = snapshot(), row = v.report.turns[0];
    row.phase = construction === "not_applicable_dependency" ? "not_run_dependency" : "failed";
    row.roles = 0; row.passed = false; row.construction_matches = false;
    row.construction_evidence_status = construction; row.privacy_evidence_status = privacy;
    row.construction_evidence_reason = construction === "unavailable" ? "non_committed_turn" : null;
    for (const key of ["narrator_prompt_sha256", "narrator_schema_sha256", "scene_frame_sha256", "actual_receipt_sha256", "capture_sha256", "recording_sha256", "narration", "fallback", "repairs"]) row[key] = null;
    row.raw_sha256 = []; v.report.source_bound_committed_rows = 1; v.rows[0] = availability(row);
    assert.deepEqual(plain(decode(v)), v);
});
test("noncommitted privacy violation and unavailable causes remain distinct unavailable diagnostics", () => {
    for (const tag of ["observer_or_output_privacy_violation", "observer_or_output_privacy_evidence_unavailable"]) {
        const v = snapshot(), row = v.report.turns[0];
        row.phase = "cancelled"; row.passed = false; row.roles_known = false; row.recovered_without_checkpoint = true;
        row.construction_matches = false; row.construction_evidence_status = "unavailable";
        row.construction_evidence_reason = "recovered_without_original_checkpoint_and_calls";
        row.privacy_evidence_status = "unavailable"; row.failures = [tag];
        for (const key of ["narrator_prompt_sha256", "narrator_schema_sha256", "scene_frame_sha256", "actual_receipt_sha256", "narration", "fallback", "repairs"]) row[key] = null;
        v.report.source_bound_committed_rows = 1; v.rows[0] = availability(row);
        assert.deepEqual(plain(decode(v)), v);
    }
});
for (const field of ["construction_evidence_status", "privacy_evidence_status"])
    rejects(`unknown4 status ${field}`, (v) => { v.report.turns[0][field] = "validated_all_semantics"; });
for (const field of ["source_bound_committed_rows", "human_reviewed"])
    for (const value of [-1, 0.5, Number.MAX_SAFE_INTEGER + 1]) rejects(`unsafe report ${field} ${value}`, (v) => { v.report[field] = value; });
for (const [name, locate] of [["envelope", (v) => v], ["report", (v) => v.report],
    ["row", (v) => v.report.turns[0]], ["descriptor", (v) => v.report.arms[0]],
    ["source row", (v) => v.rows[0].source], ["profile", (v) => v.report.profile]])
    rejects(`unknown closed ${name} field`, (v) => { locate(v).future = true; });
test("descriptor-first4 copy rejects accessors without invoking them", () => {
    const v = snapshot(); let calls = 0;
    Object.defineProperty(v.report.turns[0], "narrator_prompt_sha256", { enumerable: true, get() { calls++; return hash; } });
    assert.throws(() => decode(v), /ComparisonReaderWire/);
    assert.equal(calls, 0);
});
test("prototype and cyclic payloads refuse before transport authority", () => {
    const v = snapshot(); Object.setPrototypeOf(v.report.arms[0], { inherited: true });
    assert.throws(() => decode(v), /ComparisonReaderWire/);
    const cyclic = snapshot(); cyclic.report.turns[0].trace = cyclic;
    assert.throws(() => decode(cyclic), /ComparisonReaderWire/);
});
test("summary and source budgets stay bounded", () => {
    const v = snapshot(); v.report.turns[0].narration = "x".repeat(2 * 1024 * 1024);
    assert.throws(() => decode(v), /ComparisonReaderWire/);
    const many = source(snapshot()); many.rows = Array.from({ length: 49 }, (_, i) => {
        const r = clone(many.rows[0]); r.row.turn = `row-${i}`; return r;
    });
    assert.throws(() => m.checkedReaderSource(wrap("source", many), token, hash), /ComparisonReaderWire/);
});
for (const version of [2, 3]) test(`legacy${version} cannot acquire4-only fields`, () => {
    const v = snapshot(version); v.report.source_bound_committed_rows = 2;
    assert.throws(() => decode(v), /ComparisonReaderWire/);
    delete v.report.source_bound_committed_rows;
    v.report.turns[0].scene_frame_sha256 = hash;
    assert.throws(() => decode(v), /ComparisonReaderWire/);
});

const selected = { turn: "courier-01", arm: "left" };
const player = { kind: "player" }, omni = { kind: "omniscient" };
const query = (edge = "after") => ({ kind: "query", edge, observer: clone(player), view: "history" });
function queryPage(request) {
    const head = request.edge === "before" ? 4 : 5;
    return { version: 2, scope: clone(scope), head, revision: head, story_time: 1,
        observer: clone(request.observer), view: request.view, privacy: "player_visible",
        status: "supported", total: 0, rows: [], next_cursor: null, unsupported: [] };
}
function evidence(request, body) {
    return wrap("evidence", { version: 1, binding: hash, row: clone(selected), scope: clone(scope),
        before_head: 4, after_head: 5, observer: clone(request.observer),
        edge: request.kind === "query" ? request.edge : request.kind === "receipt" ? "after" : null,
        read_only: true, generation_grant: false, body });
}
function readEvidence(value, request, src = readSource(snapshot())) {
    return m.checkedReaderEvidence(value, token, src, selected, request);
}
for (const edge of ["before", "after"]) test(`V4 evidence retains Query2 ${edge} observer/scope/binding`, () => {
    const request = query(edge), value = evidence(request, { kind: "query", page: queryPage(request) });
    assert.deepEqual(plain(readEvidence(value, request)), value.evidence);
});
for (const kind of ["receipt", "capture", "outputs"]) test(`V4 Omniscient ${kind} remains opaque read-only diagnostic`, () => {
    const request = { kind, observer: omni };
    const body = kind === "receipt" ? { kind, receipt: { synthetic_transport: true } }
        : kind === "capture" ? { kind, capture: { synthetic_transport: true } }
        : { kind, outputs: [{ role: "narrator", bytes: 9, sha256: hash, text: "synthetic" }] };
    const value = evidence(request, body);
    assert.deepEqual(plain(readEvidence(value, request)), value.evidence);
});
for (const observer of [player, { kind: "character", id: "mira" }])
    for (const kind of ["receipt", "capture", "outputs"]) test(`actor ${observer.kind} ${kind} refuses before evidence getter`, () => {
        let calls = 0;
        const value = {}; Object.defineProperty(value, "evidence", { enumerable: true, get() { calls++; return {}; } });
        const src = source(snapshot());
        assert.throws(() => m.checkedReaderEvidence(value, "wrong-token", src, selected, { kind, observer }), /ComparisonReaderWire/);
        assert.equal(calls, 0);
    });
for (const [name, mutate] of [["binding", (v) => { v.evidence.binding = otherHash; }],
    ["row", (v) => { v.evidence.row.turn = "other"; }], ["scope", (v) => { v.evidence.scope.branch = "other"; }],
    ["observer", (v) => { v.evidence.observer = omni; }], ["edge", (v) => { v.evidence.edge = "before"; }],
    ["head", (v) => { v.evidence.after_head++; }], ["Query2 revision", (v) => { v.evidence.body.page.revision++; }],
    ["generation grant", (v) => { v.evidence.generation_grant = true; }],
    ["future field", (v) => { v.evidence.future = true; }]]) test(`V4 evidence rejects mismatched ${name}`, () => {
        const request = query(), value = evidence(request, { kind: "query", page: queryPage(request) });
        mutate(value); assert.throws(() => readEvidence(value, request), /ComparisonReaderWire/);
    });
test("V4 missing receipt uses exact source availability and never a fabricated object", () => {
    const v = snapshot(); v.report.turns[0].actual_receipt_sha256 = null; v.rows[0] = availability(v.report.turns[0]);
    const src = readSource(v), request = { kind: "receipt", observer: omni };
    const value = evidence(request, { kind: "missing", reason: "no_accepted_receipt" });
    value.evidence.after_head = 4;
    assert.deepEqual(plain(readEvidence(value, request, src)), value.evidence);
    value.evidence.body.reason = "capture_unavailable";
    assert.throws(() => readEvidence(value, request, src), /ComparisonReaderWire/);
});
test("V4 raw evidence budget and token binding remain enforced", () => {
    const request = { kind: "capture", observer: omni };
    const huge = evidence(request, { kind: "capture", capture: "x".repeat(256 * 1024) });
    assert.throws(() => readEvidence(huge, request), /ComparisonReaderWire/);
    const value = evidence(request, { kind: "capture", capture: null });
    value.run_token = "33333333-3333-3333-3333-333333333333";
    assert.throws(() => readEvidence(value, request), /ComparisonReaderWire/);
});
const result = { version: 1, cases, passed: cases.filter((c) => c.passed).length,
    failed: cases.filter((c) => !c.passed).length, synthetic_dto: true, decoder_only: true,
    rust_store: false, native_ipc: false, native_webview: false, rendered_ui: false, model_execution: false };
await writeFile(path.join(output, `scene-reader-${randomUUID()}.json`), JSON.stringify(result, null, 2), { flag: "wx" });
console.log(JSON.stringify(result));
if (result.failed) process.exitCode = 1;

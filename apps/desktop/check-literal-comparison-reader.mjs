// Frozen before production edits. Explicit SYNTHETIC DTOs + mocked controller,
// actual decoder and headless React panel only; no Rust/IPC/WebView/model claim.
import assert from "node:assert/strict";
import { build } from "esbuild";
import { mkdir, writeFile } from "node:fs/promises";
import { randomUUID } from "node:crypto";
import { fileURLToPath, pathToFileURL } from "node:url";
import path from "node:path";
const root = fileURLToPath(new URL(".", import.meta.url));
const output =
    process.env.LOCALLORE_CHECK_OUTPUT_DIR ??
    path.join(root, "artifacts/checks");
await mkdir(output, { recursive: true });
const built = await build({
    stdin: {
        contents:
            'export * from "./ui/comparison-reader-model"; export { ComparisonReaderPanel } from "./ui/ComparisonReaderPanel"; export {createElement} from "react"; export {renderToStaticMarkup} from "react-dom/server";',
        resolveDir: root,
        loader: "ts",
    },
    bundle: true,
    platform: "node",
    format: "cjs",
    jsx: "automatic",
    write: false,
});
const bundle = path.join(output, `literal-reader-${randomUUID()}.cjs`);
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
const decode = (value) =>
    m.checkedReaderSummary(wrap("snapshot", value), token, hash);
const source = (value) => {
    const { binding, protocol_version, rows, read_only, execution_available } =
        value;
    return { binding, protocol_version, rows, read_only, execution_available };
};
const cases = [];
function test(name, work) {
    try {
        work();
        cases.push({ name, passed: true });
    } catch (error) {
        cases.push({
            name,
            passed: false,
            error:
                error instanceof Error
                    ? error.message.slice(0, 180)
                    : "failure",
        });
    }
}
function rejects(name, mutate) {
    test(name, () => {
        const value = snapshot();
        mutate(value);
        assert.throws(() => decode(value), /ComparisonReaderWire/);
    });
}
test("closed protocol3 stays3 and retains literal/relevant descriptors without fabricated policy", () => {
    const value = decode(snapshot());
    assert.equal(value.protocol_version, 3);
    assert.equal(value.report.version, 3);
    assert.equal(value.report.turns[0].construction.arm, "literal_player_v1");
    assert.equal("policy" in value.report.turns[0], false);
    assert.equal(
        m.checkedReaderSource(wrap("source", source(snapshot())), token, hash)
            .protocol_version,
        3,
    );
});
for (const version of [2, 3])
    test(`protocol${version} source equality includes its version`, () => {
        const a = source(snapshot(version)),
            b = clone(a);
        b.protocol_version = version === 2 ? 3 : 2;
        assert.equal(m.sameReaderSource(a, clone(a)), true);
        assert.equal(m.sameReaderSource(a, b), false);
    });
rejects("source3/report2 mismatch", (v) => {
    v.report = snapshot(2).report;
});
rejects("source2/report3 mismatch", (v) => {
    v.protocol_version = 2;
});
rejects("unknown future protocol", (v) => {
    v.protocol_version = 5;
    v.report.version = 5;
});
rejects("report descriptor order cannot swap", (v) => {
    v.report.arms.reverse();
});
rejects("duplicate arm descriptor", (v) => {
    v.report.arms[1] = clone(literal);
});
rejects("row descriptor must match physical arm", (v) => {
    v.report.turns[0].construction = clone(relevant);
});
rejects("row and report descriptors cannot disagree", (v) => {
    v.report.arms[0].literal_packing_version = 2;
});
for (const key of Object.keys(literal))
    rejects(`literal descriptor requires ${key}`, (v) => {
        delete v.report.arms[0][key];
    });
for (const key of Object.keys(relevant))
    rejects(`relevant descriptor requires ${key}`, (v) => {
        delete v.report.turns[1].construction[key];
    });
for (const [field, value] of [
    ["prompt_version", "locallore-play-v2.5"],
    ["director_schema_id", "locallore-director-v2"],
    ["narration_policy", "future"],
    ["context_policy", "state_recent_transcript_v1"],
    ["literal_source_version", 2],
    ["compiler_version", 2],
    ["forwarded_budget_version", 2],
])
    rejects(`literal descriptor rejects unsupported ${field}`, (v) => {
        v.report.turns[0].construction[field] = value;
    });
rejects("descriptor unknown keys rejected", (v) => {
    v.report.arms[0].grant = true;
});
for (const key of [
    "error",
    "admission",
    "first_final_response_ms",
    "commit_elapsed_ms",
    "fallback",
    "capture_sha256",
    "recording_sha256",
    "role_metrics",
    "trace",
    "actual_receipt_sha256",
    "source_fallback_reason",
    "compiler_fallback_reason",
    "narration",
    "repairs",
    "mandatory_sha256",
    "optional_detail_selected",
    "director_private_target_present",
    "selected_context_bytes",
    "estimated_context_tokens",
    "literal_source_units",
    "literal_selected_start",
    "literal_selected_units",
    "forwarded_director_estimates",
])
    rejects(`protocol3 requires nullable row field ${key}`, (v) => {
        delete v.report.turns[0][key];
    });
rejects("protocol3 must not acquire protocol2 policy", (v) => {
    v.report.turns[0].policy = "state_recent_transcript_v1";
});
rejects("protocol3 must not acquire protocol2 policy_matches", (v) => {
    v.report.turns[0].policy_matches = true;
});
rejects("unknown construction status rejected", (v) => {
    v.report.turns[0].construction_evidence_status = "validated_memory";
});
rejects("literal cannot claim validated relevant", (v) => {
    v.report.turns[0].construction_evidence_status = "validated_relevant";
});
rejects("relevant cannot claim validated literal", (v) => {
    v.report.turns[1].construction_evidence_status = "validated_literal";
});
for (const field of [
    "literal_source_units",
    "literal_selected_start",
    "literal_selected_units",
]) {
    rejects(`negative ${field}`, (v) => {
        v.report.turns[0][field] = -1;
    });
    rejects(`noninteger ${field}`, (v) => {
        v.report.turns[0][field] = 0.5;
    });
    rejects(`required validated literal count ${field}`, (v) => {
        v.report.turns[0][field] = null;
    });
}
rejects("literal suffix exceeds source", (v) => {
    v.report.turns[0].literal_selected_units = 4;
});
rejects("relevant cannot claim literal source count", (v) => {
    v.report.turns[1].literal_source_units = 0;
});
for (const field of [
    "mandatory_sha256",
    "optional_detail_selected",
    "source_fallback_reason",
    "compiler_fallback_reason",
    "selected_context_bytes",
    "estimated_context_tokens",
])
    rejects(`literal has no memory metric ${field}`, (v) => {
        v.report.turns[0][field] = row2()[field] ?? "unsupported";
    });
test("failed actual forwarded literal input remains validated even with zero history", () => {
    const v = snapshot(),
        row = v.report.turns[0];
    Object.assign(row, {
        phase: "failed",
        error: "UnknownReference",
        passed: false,
        construction_matches: false,
        actual_receipt_sha256: null,
        narration: null,
        literal_source_units: 0,
        literal_selected_start: 0,
        literal_selected_units: 0,
        roles: 1,
    });
    v.rows[0] = availability(row);
    assert.equal(
        decode(v).report.turns[0].construction_evidence_status,
        "validated_literal",
    );
});
test("literal actual narration fallback and prompt sentinel are not memory metrics", () => {
    const v = snapshot();
    v.report.turns[0].fallback = true;
    v.report.turns[0].director_private_target_present = true;
    decode(v);
});
test("old2 optional estimates retain omitted/array semantics and reject null", () => {
    const v = snapshot(2);
    assert.equal(decode(v).report.version, 2);
    v.report.turns[0].forwarded_director_estimates = [];
    decode(v);
    v.report.turns[0].forwarded_director_estimates = null;
    assert.throws(() => decode(v), /ComparisonReaderWire/);
});
test("old2 still rejects protocol3-only row metadata", () => {
    const v = snapshot(2);
    v.report.turns[0].construction = literal;
    assert.throws(() => decode(v), /ComparisonReaderWire/);
});
test("old2 unknown keys and unsafe numbers remain rejected", () => {
    const v = snapshot(2);
    v.report.extra = true;
    assert.throws(() => decode(v), /ComparisonReaderWire/);
    delete v.report.extra;
    v.report.turns[0].roles = Number.MAX_SAFE_INTEGER + 1;
    assert.throws(() => decode(v), /ComparisonReaderWire/);
});
const htmlFiles = [];
function panel(value, observer = { kind: "omniscient" }) {
    const selected = { turn: value.rows[0].row.turn, arm: "left" };
    const state = {
        context: "synthetic",
        allowed: true,
        observer,
        clientId: token,
        status: { phase: "ready", run_token: token },
        source: source(value),
        summary: observer.kind === "omniscient" ? value : null,
        selected,
        evidence: null,
        querySelection: { edge: "after", view: "knowledge" },
        busy: false,
        uncertain: false,
        error: null,
    };
    const controller = {
        get: () => state,
        subscribe: () => () => {},
        pick() {},
        recover() {},
        close() {},
        setObserver() {},
        loadSummary() {},
        select() {},
        setQuerySelection() {},
        inspect() {},
    };
    return m.renderToStaticMarkup(
        m.createElement(m.ComparisonReaderPanel, { controller }),
    );
}
function guardSnapshot(status = "not_applicable_guard") {
    const v = snapshot(),
        row = v.report.turns[0];
    Object.assign(row, {
        phase:
            status === "not_applicable_guard" ? "failed" : "not_run_dependency",
        error: "Ability",
        roles: 0,
        actual_receipt_sha256: null,
        capture_sha256: null,
        narration: null,
        privacy_passed: false,
        context_evidence_available: false,
        literal_source_units: null,
        literal_selected_start: null,
        literal_selected_units: null,
        forwarded_director_estimates: null,
        construction_evidence_status: status,
    });
    v.rows[0] = availability(row);
    return v;
}
for (const status of [
    "not_applicable_guard",
    "not_applicable_dependency",
    "unavailable",
])
    test(`closed ${status} with missing literal counts`, () => {
        const v = guardSnapshot(status);
        if (status === "unavailable") {
            v.report.turns[0].roles_known = false;
            v.report.turns[0].recovered_without_checkpoint = true;
        }
        decode(v);
    });
for (const status of [
    "not_applicable_guard",
    "not_applicable_dependency",
    "unavailable",
])
    rejects(`${status} cannot invent literal counts`, (v) => {
        v.report.turns[0].construction_evidence_status = status;
    });
test("headless literal/relevant panel labels and explicit protocol3 rerun unavailability", () => {
    const html = panel(decode(snapshot()));
    htmlFiles.push(["literal", html]);
    for (const expected of [
        "Literal player conversation",
        "Relevant memory",
        "Construction evidence",
        "Source units",
        "Selected units",
        "Protocol 3 selected-case rerun unavailable",
    ])
        assert.ok(html.includes(expected), expected);
    assert.ok(!html.includes("state_recent_transcript_v1"));
    assert.ok(!html.includes("quality accepted"));
});
test("headless guard privacy is not applicable, never a privacy pass or leak claim", () => {
    const html = panel(decode(guardSnapshot()));
    htmlFiles.push(["guard", html]);
    assert.ok(html.includes("Not applicable — guard"));
    assert.ok(html.includes("Privacy check"));
    assert.ok(html.includes("Not applicable; no generation"));
});
test("headless actor lens hides report/prose and raw controls", () => {
    const input = snapshot();
    input.report.turns[0].narration = "SYNTHETIC-PRIVATE-PROSE";
    const v = decode(input);
    const html = panel(v, { kind: "character", id: "mira" });
    htmlFiles.push(["actor", html]);
    assert.ok(!html.includes("SYNTHETIC-PRIVATE-PROSE"));
    assert.ok(!html.includes("Inspect actual context capture"));
    assert.ok(html.includes("filtered state"));
});
for (const [name, html] of htmlFiles)
    await writeFile(
        path.join(output, `literal-reader-${name}-${randomUUID()}.html`),
        html,
        { flag: "wx" },
    );
const result = {
    version: 1,
    cases,
    passed: cases.filter((v) => v.passed).length,
    failed: cases.filter((v) => !v.passed).length,
    synthetic_dto: true,
    mocked_controller: true,
    headless_html: true,
    rust_producer: false,
    native_ipc: false,
    native_webview: false,
    model_execution: false,
};
await writeFile(
    path.join(output, `literal-reader-${randomUUID()}.json`),
    JSON.stringify(result, null, 2),
    { flag: "wx" },
);
console.log(JSON.stringify(result));
if (result.failed) process.exitCode = 1;

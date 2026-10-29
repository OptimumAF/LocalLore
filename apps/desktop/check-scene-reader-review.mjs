// Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0
// FIRST independent SOURCE freeze; author UNRUN. Synthetic DTOs exercise the
// existing public decoder only, never Rust/Store/IPC/WebView/model authority.
// Supplemental R3 controller/Panel static-HTML cases below are separate evidence.
import assert from "node:assert/strict";
import { build } from "esbuild";
import { mkdir, readFile, writeFile, lstat, realpath } from "node:fs/promises";
import { createHash, randomUUID } from "node:crypto";
import { fileURLToPath, pathToFileURL } from "node:url";
import path from "node:path";

const root = fileURLToPath(new URL(".", import.meta.url));
const geometryMode = process.argv.length === 3 && process.argv[2] === "--artifact-geometry-v1";
assert(process.argv.length === 2 || geometryMode, "ClosedReaderCheckArguments");
const output =
    process.env.LOCALLORE_CHECK_OUTPUT_DIR ??
    path.join(root, "artifacts/checks");
if (geometryMode) {
    process.env.TEMP = "D:/Dev/_Temp"; process.env.TMP = "D:/Dev/_Temp";
    assert(path.isAbsolute(output) && path.parse(path.resolve(output)).root.toLowerCase() === "d:\\", "PhysicalDGeometryOutputRequired");
    let ancestor = path.resolve(output);
    for (;;) {
        try { await lstat(ancestor); break; }
        catch (error) { if (error.code !== "ENOENT") throw error; ancestor = path.dirname(ancestor); }
    }
    assert.equal(path.resolve(await realpath(ancestor)).toLowerCase(), ancestor.toLowerCase(), "GeometryOutputAncestorRedirected");
    for (let current = ancestor; ; current = path.dirname(current)) {
        const metadata = await lstat(current);
        assert(metadata.isDirectory() && !metadata.isSymbolicLink(), "OrdinaryGeometryOutputAncestorRequired");
        if (current === path.dirname(current)) break;
    }
}
await mkdir(output, { recursive: true });
const built = await build({
    stdin: {
        contents: 'export * from "./ui/comparison-reader-model";',
        resolveDir: root,
        loader: "ts",
    },
    bundle: true,
    platform: "node",
    format: "cjs",
    write: false,
});
const bundle = path.join(output, `scene-reader-${randomUUID()}.cjs`);
await writeFile(bundle, built.outputFiles[0].contents, { flag: "wx" });
const m = (await import(pathToFileURL(bundle).href)).default;
const token = "22222222-2222-2222-2222-222222222222";
const hash = "a".repeat(64),
    otherHash = "b".repeat(64);
const scope = { story: "synthetic-scene-reader", branch: "main" };
const clone = (value) => structuredClone(value);
const plain = (value) => JSON.parse(JSON.stringify(value));
const wrap = (key, value) => ({
    version: 1,
    kind: "comparison_reader",
    run_token: token,
    [key]: value,
});
const decode = (value) =>
    m.checkedReaderSummary(wrap("snapshot", value), token, hash);
function source(value) {
    const { binding, protocol_version, rows, read_only, execution_available } =
        value;
    return { binding, protocol_version, rows, read_only, execution_available };
}
const readSource = (value) =>
    m.checkedReaderSource(wrap("source", source(value)), token, hash);

// Literal expectations are independently copied from the closed native metadata
// contract. No production descriptor builder is imported to manufacture them.
const literal4 = {
    arm: "literal_scene_v1",
    prompt_version: "locallore-play-v2.10-literal-director-v1-scene-frame-v1",
    narration_policy: "grounded-prose-v2.4-scene-frame-v1",
    director_schema_id: "locallore-director-literal-v1",
    narrator_schema_id: "locallore-narrator-v2",
    context_policy: null,
    compiler_version: null,
    context_version: null,
    literal_source_version: 1,
    literal_render_version: 1,
    literal_schema_version: 1,
    literal_packing_version: 1,
    forwarded_budget_version: 1,
    scene_frame_version: 1,
    scene_capture_gate_version: 1,
};
const relevant4 = {
    arm: "relevant_memory_scene_v1",
    prompt_version: "locallore-play-v2.9-scene-frame-v1",
    narration_policy: "grounded-prose-v2.4-scene-frame-v1",
    director_schema_id: "locallore-director-v2",
    narrator_schema_id: "locallore-narrator-v2",
    context_policy: "state_relevant_memory_v1",
    compiler_version: 2,
    context_version: 2,
    literal_source_version: null,
    literal_render_version: null,
    literal_schema_version: null,
    literal_packing_version: null,
    forwarded_budget_version: 1,
    scene_frame_version: 1,
    scene_capture_gate_version: 1,
};
function descriptor3(arm) {
    const d = clone(arm === "left" ? literal4 : relevant4);
    delete d.narrator_schema_id;
    delete d.scene_frame_version;
    delete d.scene_capture_gate_version;
    d.arm = arm === "left" ? "literal_player_v1" : "relevant_memory_v1";
    d.prompt_version =
        arm === "left"
            ? "locallore-play-v2.6-literal-director-v1"
            : "locallore-play-v2.5";
    d.narration_policy = "grounded-prose-v2.2";
    return d;
}
function commonTurn(arm) {
    return {
        turn: "courier-01",
        scene: 0,
        arm,
        phase: "committed",
        error: null,
        expected: "accepted",
        passed: true,
        failures: [],
        quality_flags: [],
        roles: 2,
        roles_known: true,
        recovered_without_checkpoint: false,
        admission: 0,
        elapsed_ms: 2,
        first_final_response_ms: 1,
        commit_elapsed_ms: 0,
        input_semantic_sha256: hash,
        output_semantic_sha256: otherHash,
        mechanical_sha256: hash,
        fallback: false,
        repairs: 0,
        narration: "Synthetic transport text; no inference executed.",
        capture_sha256: hash,
        recording_sha256: otherHash,
        raw_sha256: [hash, otherHash],
        role_metrics: null,
        trace: null,
        stages: [],
        actual_receipt_sha256: otherHash,
        source_fallback_reason: null,
        compiler_fallback_reason: null,
    };
}
function oldTurn(version, arm) {
    const row = {
        ...commonTurn(arm),
        context_evidence_available: true,
        context_requirement: "required_actual_capture",
        privacy_passed: true,
        mandatory_sha256: arm === "right" ? hash : null,
        optional_detail_selected: arm === "right" ? false : null,
        director_private_target_present: false,
        selected_context_bytes: arm === "right" ? 100 : null,
        estimated_context_tokens: arm === "right" ? 25 : null,
    };
    if (version === 2)
        Object.assign(row, {
            policy:
                arm === "left"
                    ? "state_recent_transcript_v1"
                    : "state_relevant_memory_v1",
            policy_matches: true,
        });
    else
        Object.assign(row, {
            construction: descriptor3(arm),
            construction_matches: true,
            construction_evidence_status:
                arm === "left" ? "validated_literal" : "validated_relevant",
            literal_source_units: arm === "left" ? 3 : null,
            literal_selected_start: arm === "left" ? 1 : null,
            literal_selected_units: arm === "left" ? 2 : null,
            forwarded_director_estimates: null,
        });
    return row;
}
function turn4(arm) {
    return {
        ...commonTurn(arm),
        construction: clone(arm === "left" ? literal4 : relevant4),
        construction_matches: true,
        construction_evidence_status: "validated_committed_scene_narrator_v1",
        construction_evidence_reason: null,
        narrator_prompt_sha256: hash,
        narrator_schema_sha256: otherHash,
        scene_frame_sha256: "c".repeat(64),
        privacy_evidence_status: "checked_finite_sentinels",
    };
}
function availability(row) {
    const capture = row.capture_sha256 !== null,
        recording = row.recording_sha256 !== null;
    const receipt = row.actual_receipt_sha256 !== null;
    return {
        row: { turn: row.turn, arm: row.arm },
        source: {
            status: "available",
            scope: clone(scope),
            before_head: 4,
            after_head: receipt ? 5 : 4,
            input_semantic_sha256: row.input_semantic_sha256,
        },
        capture_available: capture,
        receipt_available: receipt,
        recording_available: recording,
        unavailable: [
            ...(capture ? [] : ["capture_unavailable"]),
            ...(recording ? [] : ["recording_unavailable"]),
            ...(receipt ? [] : ["no_accepted_receipt"]),
        ],
    };
}
function snapshot(version = 4) {
    const turns = ["left", "right"].map((arm) =>
        version === 4 ? turn4(arm) : oldTurn(version, arm),
    );
    const report = {
        version,
        ...(version === 2
            ? {}
            : {
                  arms:
                      version === 4
                          ? [clone(literal4), clone(relevant4)]
                          : [descriptor3("left"), descriptor3("right")],
              }),
        kind: "paired_snapshots",
        lane: "scripted_scene_comparison",
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
        left_charged_ms: 2,
        right_charged_ms: 2,
        left_reserved_roles: 2,
        right_reserved_roles: 2,
        first_semantic_divergence: null,
        first_mechanical_divergence: null,
        same_input_pairs: 1,
        ...(version === 4 ? { source_bound_committed_rows: 2 } : {}),
        unavailable: ["synthetic_fixture_no_native_or_model_execution"],
        profile: {
            id: "synthetic-scene-reader",
            model_sha256: hash,
            runtime_revision: "d".repeat(40),
            template_sha256: otherHash,
            worker_sha256: hash,
            profile_manifest_sha256: otherHash,
            context_tokens: 4096,
            director_tokens: 350,
            narrator_tokens: 350,
            deadline_ms: 120000,
            repair_limit: 1,
        },
        suite_sha256: hash,
        source_sha256: otherHash,
        reference_sha256: null,
        limitations: [
            "Synthetic DTO only; source-bound Domain1 narrator input does not authenticate Director/raw output.",
            "Original eight-sample human assessment: needs improvement; no new human review.",
        ],
    };
    return {
        version: 1,
        protocol_version: version,
        binding: hash,
        report,
        rows: turns.map(availability),
        read_only: true,
        execution_available: false,
        unavailable: [
            version === 4
                ? "selected_protocol4_rerun_not_implemented"
                : "selected_rerun_not_implemented",
        ],
    };
}

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
        const v = snapshot();
        mutate(v);
        assert.throws(() => decode(v), /ComparisonReaderWire/);
    });
}
for (const version of [2, 3])
    test(`old protocol${version} positive control is lossless and stays its version`, () => {
        const v = snapshot(version);
        assert.deepEqual(plain(decode(v)), v);
        assert.deepEqual(plain(readSource(v)), source(v));
    });
test("closed4 is lossless, distinct and read-only without selected execution", () => {
    const v = snapshot(),
        decoded = decode(v),
        src = readSource(v);
    assert.deepEqual(plain(decoded), v);
    assert.deepEqual(plain(src), source(v));
    assert.equal(decoded.protocol_version, 4);
    assert.equal(decoded.report.version, 4);
    assert.equal(decoded.execution_available, false);
    assert.deepEqual(plain(decoded.unavailable), [
        "selected_protocol4_rerun_not_implemented",
    ]);
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
    for (const mutate of [
        (b) => {
            b.protocol_version = 3;
        },
        (b) => {
            b.rows[0].source.input_semantic_sha256 = otherHash;
        },
        (b) => {
            b.rows[0].source.scope.branch = "other";
        },
        (b) => {
            b.rows[0].source.after_head++;
        },
    ]) {
        const b = plain(a);
        mutate(b);
        assert.equal(m.sameReaderSource(a, b), false);
    }
});
test("decoder detaches complete4 DTO without losing opaque diagnostics", () => {
    const v = snapshot();
    v.report.turns[0].role_metrics = { synthetic: [1, null, "bounded opaque"] };
    v.report.turns[0].trace = { synthetic: true };
    v.report.turns[0].stages = [{ synthetic: "not an execution assertion" }];
    const expected = clone(v),
        decoded = decode(v);
    v.report.arms[0].prompt_version = "changed";
    v.rows[0].source.scope.story = "changed";
    v.report.turns[0].role_metrics.synthetic.length = 0;
    assert.deepEqual(plain(decoded), expected);
});
for (const arm of [0, 1])
    for (const key of Object.keys(literal4)) {
        rejects(
            `descriptor arm${arm} requires ${key} including explicit null`,
            (v) => {
                delete v.report.arms[arm][key];
            },
        );
        rejects(
            `self-consistent unsupported descriptor arm${arm} ${key} is refused`,
            (v) => {
                const old = v.report.arms[arm][key];
                const changed =
                    old === null
                        ? 1
                        : typeof old === "number"
                          ? old + 1
                          : "unsupported";
                v.report.arms[arm][key] = changed;
                v.report.turns[arm].construction[key] = changed;
            },
        );
    }
for (const arm of [0, 1])
    test(`every row descriptor field is required for arm${arm}`, () => {
        for (const key of Object.keys(literal4)) {
            const v = snapshot();
            delete v.report.turns[arm].construction[key];
            assert.throws(() => decode(v), /ComparisonReaderWire/, key);
        }
    });
for (const [name, mutate] of [
    [
        "physical arm swap",
        (v) => {
            v.report.turns[0].construction = clone(relevant4);
        },
    ],
    [
        "report descriptor order",
        (v) => {
            v.report.arms.reverse();
        },
    ],
    [
        "duplicate report descriptor",
        (v) => {
            v.report.arms[1] = clone(literal4);
        },
    ],
    [
        "row descriptor differs from report",
        (v) => {
            v.report.turns[0].construction.scene_frame_version = 2;
        },
    ],
    [
        "row descriptor future field",
        (v) => {
            v.report.turns[0].construction.future = true;
        },
    ],
    [
        "legacy3 tuple cannot be relabeled4",
        (v) => {
            v.report.arms = [descriptor3("left"), descriptor3("right")];
            v.report.turns.forEach((r) => {
                r.construction = descriptor3(r.arm);
            });
        },
    ],
    [
        "rows reorder",
        (v) => {
            v.rows.reverse();
        },
    ],
    [
        "duplicate row",
        (v) => {
            v.rows[1] = clone(v.rows[0]);
        },
    ],
    [
        "extra report row",
        (v) => {
            const r = clone(v.report.turns[0]);
            r.turn = "extra";
            v.report.turns.push(r);
        },
    ],
    [
        "row input fingerprint mismatch",
        (v) => {
            v.rows[0].source.input_semantic_sha256 = otherHash;
        },
    ],
    [
        "source4/report3 disagreement",
        (v) => {
            v.report = snapshot(3).report;
        },
    ],
    [
        "source3/report4 disagreement",
        (v) => {
            v.protocol_version = 3;
        },
    ],
    [
        "future protocol5",
        (v) => {
            v.protocol_version = 5;
            v.report.version = 5;
        },
    ],
    [
        "execution grant",
        (v) => {
            v.execution_available = true;
        },
    ],
    [
        "writable source",
        (v) => {
            v.read_only = false;
        },
    ],
])
    rejects(name, mutate);
const nullableRows = [
    "error",
    "admission",
    "first_final_response_ms",
    "commit_elapsed_ms",
    "construction_evidence_reason",
    "narrator_prompt_sha256",
    "narrator_schema_sha256",
    "scene_frame_sha256",
    "actual_receipt_sha256",
    "fallback",
    "repairs",
    "narration",
    "capture_sha256",
    "recording_sha256",
    "role_metrics",
    "trace",
    "source_fallback_reason",
    "compiler_fallback_reason",
];
for (const key of nullableRows)
    rejects(`required nullable4 row field ${key} cannot disappear`, (v) => {
        delete v.report.turns[0][key];
    });
for (const key of [
    "construction",
    "construction_matches",
    "construction_evidence_status",
    "privacy_evidence_status",
])
    rejects(`required4 row field ${key} cannot disappear`, (v) => {
        delete v.report.turns[0][key];
    });
rejects("source-bound row count is a required4 report field", (v) => {
    delete v.report.source_bound_committed_rows;
});
for (const key of [
    "physical_setup_ms",
    "native_load",
    "first_semantic_divergence",
    "first_mechanical_divergence",
    "reference_sha256",
])
    rejects(`required nullable4 report field ${key} cannot disappear`, (v) => {
        delete v.report[key];
    });
test("explicit nullable diagnostics are retained without fabricating fields", () => {
    const v = snapshot(),
        row = v.report.turns[0];
    for (const key of nullableRows) row[key] = null;
    row.phase = "failed";
    row.passed = false;
    row.construction_matches = false;
    row.construction_evidence_status = "unavailable";
    row.privacy_evidence_status = "unavailable";
    v.report.source_bound_committed_rows = 1;
    v.rows[0] = availability(row);
    assert.deepEqual(plain(decode(v)), v);
});
for (const key of [
    "narrator_prompt_sha256",
    "narrator_schema_sha256",
    "scene_frame_sha256",
    "actual_receipt_sha256",
])
    rejects(`malformed new or actual hash ${key}`, (v) => {
        v.report.turns[0][key] = "not-sha256";
    });
for (const key of [
    "policy",
    "policy_matches",
    "context_evidence_available",
    "context_requirement",
    "privacy_passed",
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
    rejects(`V4 does not inherit legacy row field ${key}`, (v) => {
        v.report.turns[0][key] = null;
    });
for (const [construction, privacy] of [
    ["not_applicable_guard", "not_applicable_guard"],
    ["not_applicable_dependency", "unavailable"],
    ["unavailable", "unavailable"],
])
    test(`closed statuses retained ${construction}/${privacy}`, () => {
        const v = snapshot(),
            row = v.report.turns[0];
        row.phase =
            construction === "not_applicable_dependency"
                ? "not_run_dependency"
                : "failed";
        row.roles = 0;
        row.passed = false;
        row.construction_matches = false;
        row.construction_evidence_status = construction;
        row.privacy_evidence_status = privacy;
        row.construction_evidence_reason =
            construction === "unavailable" ? "non_committed_turn" : null;
        for (const key of [
            "narrator_prompt_sha256",
            "narrator_schema_sha256",
            "scene_frame_sha256",
            "actual_receipt_sha256",
            "capture_sha256",
            "recording_sha256",
            "narration",
            "fallback",
            "repairs",
        ])
            row[key] = null;
        row.raw_sha256 = [];
        v.report.source_bound_committed_rows = 1;
        v.rows[0] = availability(row);
        assert.deepEqual(plain(decode(v)), v);
    });
test("noncommitted privacy violation and unavailable causes remain distinct unavailable diagnostics", () => {
    for (const tag of [
        "observer_or_output_privacy_violation",
        "observer_or_output_privacy_evidence_unavailable",
    ]) {
        const v = snapshot(),
            row = v.report.turns[0];
        row.phase = "cancelled";
        row.passed = false;
        row.roles_known = false;
        row.recovered_without_checkpoint = true;
        row.construction_matches = false;
        row.construction_evidence_status = "unavailable";
        row.construction_evidence_reason =
            "recovered_without_original_checkpoint_and_calls";
        row.privacy_evidence_status = "unavailable";
        row.failures = [tag];
        for (const key of [
            "narrator_prompt_sha256",
            "narrator_schema_sha256",
            "scene_frame_sha256",
            "actual_receipt_sha256",
            "narration",
            "fallback",
            "repairs",
        ])
            row[key] = null;
        v.report.source_bound_committed_rows = 1;
        v.rows[0] = availability(row);
        assert.deepEqual(plain(decode(v)), v);
    }
});
for (const field of ["construction_evidence_status", "privacy_evidence_status"])
    rejects(`unknown4 status ${field}`, (v) => {
        v.report.turns[0][field] = "validated_all_semantics";
    });
for (const field of ["source_bound_committed_rows", "human_reviewed"])
    for (const value of [-1, 0.5, Number.MAX_SAFE_INTEGER + 1])
        rejects(`unsafe report ${field} ${value}`, (v) => {
            v.report[field] = value;
        });
for (const [name, locate] of [
    ["envelope", (v) => v],
    ["report", (v) => v.report],
    ["row", (v) => v.report.turns[0]],
    ["descriptor", (v) => v.report.arms[0]],
    ["source row", (v) => v.rows[0].source],
    ["profile", (v) => v.report.profile],
])
    rejects(`unknown closed ${name} field`, (v) => {
        locate(v).future = true;
    });
test("descriptor-first4 copy rejects accessors without invoking them", () => {
    const v = snapshot();
    let calls = 0;
    Object.defineProperty(v.report.turns[0], "narrator_prompt_sha256", {
        enumerable: true,
        get() {
            calls++;
            return hash;
        },
    });
    assert.throws(() => decode(v), /ComparisonReaderWire/);
    assert.equal(calls, 0);
});
test("prototype and cyclic payloads refuse before transport authority", () => {
    const v = snapshot();
    Object.setPrototypeOf(v.report.arms[0], { inherited: true });
    assert.throws(() => decode(v), /ComparisonReaderWire/);
    const cyclic = snapshot();
    cyclic.report.turns[0].trace = cyclic;
    assert.throws(() => decode(cyclic), /ComparisonReaderWire/);
});
test("summary and source budgets stay bounded", () => {
    const v = snapshot();
    v.report.turns[0].narration = "x".repeat(2 * 1024 * 1024);
    assert.throws(() => decode(v), /ComparisonReaderWire/);
    const many = source(snapshot());
    many.rows = Array.from({ length: 49 }, (_, i) => {
        const r = clone(many.rows[0]);
        r.row.turn = `row-${i}`;
        return r;
    });
    assert.throws(
        () => m.checkedReaderSource(wrap("source", many), token, hash),
        /ComparisonReaderWire/,
    );
});
for (const version of [2, 3])
    test(`legacy${version} cannot acquire4-only fields`, () => {
        const v = snapshot(version);
        v.report.source_bound_committed_rows = 2;
        assert.throws(() => decode(v), /ComparisonReaderWire/);
        delete v.report.source_bound_committed_rows;
        v.report.turns[0].scene_frame_sha256 = hash;
        assert.throws(() => decode(v), /ComparisonReaderWire/);
    });

const selected = { turn: "courier-01", arm: "left" };
const player = { kind: "player" },
    omni = { kind: "omniscient" };
const query = (edge = "after") => ({
    kind: "query",
    edge,
    observer: clone(player),
    view: "history",
});
function queryPage(request) {
    const head = request.edge === "before" ? 4 : 5;
    return {
        version: 2,
        scope: clone(scope),
        head,
        revision: head,
        story_time: 1,
        observer: clone(request.observer),
        view: request.view,
        privacy: "player_visible",
        status: "supported",
        total: 0,
        rows: [],
        next_cursor: null,
        unsupported: [],
    };
}
function evidence(request, body) {
    return wrap("evidence", {
        version: 1,
        binding: hash,
        row: clone(selected),
        scope: clone(scope),
        before_head: 4,
        after_head: 5,
        observer: clone(request.observer),
        edge:
            request.kind === "query"
                ? request.edge
                : request.kind === "receipt"
                  ? "after"
                  : null,
        read_only: true,
        generation_grant: false,
        body,
    });
}
function readEvidence(value, request, src = readSource(snapshot())) {
    return m.checkedReaderEvidence(value, token, src, selected, request);
}
for (const edge of ["before", "after"])
    test(`V4 evidence retains Query2 ${edge} observer/scope/binding`, () => {
        const request = query(edge),
            value = evidence(request, {
                kind: "query",
                page: queryPage(request),
            });
        assert.deepEqual(plain(readEvidence(value, request)), value.evidence);
    });
for (const kind of ["receipt", "capture", "outputs"])
    test(`V4 Omniscient ${kind} remains opaque read-only diagnostic`, () => {
        const request = { kind, observer: omni };
        const body =
            kind === "receipt"
                ? { kind, receipt: { synthetic_transport: true } }
                : kind === "capture"
                  ? { kind, capture: { synthetic_transport: true } }
                  : {
                        kind,
                        outputs: [
                            {
                                role: "narrator",
                                bytes: 9,
                                sha256: hash,
                                text: "synthetic",
                            },
                        ],
                    };
        const value = evidence(request, body);
        assert.deepEqual(plain(readEvidence(value, request)), value.evidence);
    });
for (const observer of [player, { kind: "character", id: "mira" }])
    for (const kind of ["receipt", "capture", "outputs"])
        test(`actor ${observer.kind} ${kind} refuses before evidence getter`, () => {
            let calls = 0;
            const value = {};
            Object.defineProperty(value, "evidence", {
                enumerable: true,
                get() {
                    calls++;
                    return {};
                },
            });
            const src = source(snapshot());
            assert.throws(
                () =>
                    m.checkedReaderEvidence(
                        value,
                        "wrong-token",
                        src,
                        selected,
                        { kind, observer },
                    ),
                /ComparisonReaderWire/,
            );
            assert.equal(calls, 0);
        });
for (const [name, mutate] of [
    [
        "binding",
        (v) => {
            v.evidence.binding = otherHash;
        },
    ],
    [
        "row",
        (v) => {
            v.evidence.row.turn = "other";
        },
    ],
    [
        "scope",
        (v) => {
            v.evidence.scope.branch = "other";
        },
    ],
    [
        "observer",
        (v) => {
            v.evidence.observer = omni;
        },
    ],
    [
        "edge",
        (v) => {
            v.evidence.edge = "before";
        },
    ],
    [
        "head",
        (v) => {
            v.evidence.after_head++;
        },
    ],
    [
        "Query2 revision",
        (v) => {
            v.evidence.body.page.revision++;
        },
    ],
    [
        "generation grant",
        (v) => {
            v.evidence.generation_grant = true;
        },
    ],
    [
        "future field",
        (v) => {
            v.evidence.future = true;
        },
    ],
])
    test(`V4 evidence rejects mismatched ${name}`, () => {
        const request = query(),
            value = evidence(request, {
                kind: "query",
                page: queryPage(request),
            });
        mutate(value);
        assert.throws(
            () => readEvidence(value, request),
            /ComparisonReaderWire/,
        );
    });
test("V4 missing receipt uses exact source availability and never a fabricated object", () => {
    const v = snapshot();
    v.report.turns[0].actual_receipt_sha256 = null;
    v.rows[0] = availability(v.report.turns[0]);
    const src = readSource(v),
        request = { kind: "receipt", observer: omni };
    const value = evidence(request, {
        kind: "missing",
        reason: "no_accepted_receipt",
    });
    value.evidence.after_head = 4;
    assert.deepEqual(plain(readEvidence(value, request, src)), value.evidence);
    value.evidence.body.reason = "capture_unavailable";
    assert.throws(
        () => readEvidence(value, request, src),
        /ComparisonReaderWire/,
    );
});
test("V4 raw evidence budget and token binding remain enforced", () => {
    const request = { kind: "capture", observer: omni };
    const huge = evidence(request, {
        kind: "capture",
        capture: "x".repeat(256 * 1024),
    });
    assert.throws(() => readEvidence(huge, request), /ComparisonReaderWire/);
    const value = evidence(request, { kind: "capture", capture: null });
    value.run_token = "33333333-3333-3333-3333-333333333333";
    assert.throws(() => readEvidence(value, request), /ComparisonReaderWire/);
});

// Independent R3 display freeze from2e2e74fc BEFORE the artifact framing fix.
// The existing174 decoder oracles remain above, unchanged. SOURCE ONLY / UNRUN.
// This separate bundle exercises actual controller/Panel APIs with synthetic
// typed metadata, never a controller-state stub or a reconstructed engine.
const decoderCaseCount = cases.length;
const panelCases = [], panelHtml = [], panelSetupFailures = [];
const panelPrefix = `scene-reader-artifact-${randomUUID()}`;
const panelSourceNames = ["ui/comparison-reader-model.ts", "ui/comparison-reader-controller.ts",
    "ui/ComparisonReaderPanel.tsx", "check-scene-reader-review.mjs"];
const panelHashes = async () => Object.fromEntries(await Promise.all(panelSourceNames.map(async (name) => [name,
    createHash("sha256").update(await readFile(path.join(root, name))).digest("hex")])));
const panelSourceBefore = await panelHashes();
const safePanelError = (error) => String(error?.message ?? error).slice(0, 500);
let panelModules = null;
try {
    const rendered = await build({ stdin: {
        contents: 'export {ComparisonReaderController} from "./ui/comparison-reader-controller";export {ComparisonReaderPanel} from "./ui/ComparisonReaderPanel";export {createElement} from "react";export {renderToStaticMarkup} from "react-dom/server";',
        resolveDir: root, loader: "tsx",
    }, bundle: true, platform: "node", format: "cjs", write: false });
    const file = path.join(output, `${panelPrefix}.cjs`);
    await writeFile(file, rendered.outputFiles[0].contents, { flag: "wx" });
    panelModules = (await import(pathToFileURL(file).href)).default;
    for (const name of ["ComparisonReaderController", "ComparisonReaderPanel", "createElement", "renderToStaticMarkup"])
        assert.equal(typeof panelModules[name], "function", `existing headless API ${name}`);
} catch (error) {
    panelSetupFailures.push({ stage: "bundle-api", error: safePanelError(error) });
}
const artifactRun = "44444444-4444-4444-4444-444444444444";
const artifactMarker = "SYNTHETIC_DIRECTOR_BODY_FOR_HEADLESS_FRAMING_ONLY";
const textOnly = (html) => html.replace(/<[^>]*>/g, " ").replace(/\s+/g, " ").trim();
async function artifactFixture({ failed, fallback = false }) {
    const value = snapshot(), row = value.report.turns[0];
    const outputs = [{ role: "director", text: artifactMarker },
        ...(failed ? [] : [{ role: "narrator", text: "SYNTHETIC_NARRATOR_BODY_FOR_HEADLESS_FRAMING_ONLY" }])]
        .map(({ role, text }) => ({ role, bytes: Buffer.byteLength(text),
            sha256: createHash("sha256").update(text).digest("hex"), text }));
    value.report.lane = "native_scene_literal_relevant_comparison";
    value.report.limitations.push("Synthetic native-lane DTO for headless display only; no runtime or quality evidence.");
    row.fallback = fallback;
    row.raw_sha256 = outputs.map((item) => item.sha256);
    if (failed) {
        Object.assign(row, { phase: "failed", error: "UnknownReference", passed: false,
            failures: ["synthetic_failed_without_accepted_receipt"], roles: 1,
            commit_elapsed_ms: null, actual_receipt_sha256: null, narration: null, fallback: null,
            construction_matches: false, construction_evidence_status: "unavailable",
            construction_evidence_reason: "non_committed_turn", privacy_evidence_status: "unavailable",
            narrator_prompt_sha256: null, narrator_schema_sha256: null, scene_frame_sha256: null });
        value.report.source_bound_committed_rows = 1;
        value.report.left_reserved_roles = 1;
    }
    value.rows[0] = availability(row);
    // Existing public decoders establish this fixture's exact source/report
    // closure before the actual controller/Panel sees it. No engine is run.
    decode(value); readSource(value);
    const entry = value.rows[0], calls = [], errors = [];
    let client = null;
    const ready = (closed = false) => ({ version: 1, kind: "comparison_reader", client_id: client,
        operation_id: 1, phase: closed ? "closed" : "ready", running: false,
        run_token: closed ? null : token, binding: closed ? null : hash, error: null,
        read_only: true, execution_available: false });
    const invoke = async (name, args) => {
        assert.deepEqual(Object.keys(args).sort(), ["action", "query"]);
        assert.ok(args.query && typeof args.query === "object" && !Array.isArray(args.query));
        assert.ok(calls.length < 32, "bounded synthetic reader transcript");
        calls.push(clone({ name, ...args }));
        const q = args.query;
        if (name === "evaluation_comparison_native") {
            assert.equal(args.action, "managed");
            assert.deepEqual(Object.keys(q).sort(), ["clientId", "runId"]);
            assert.equal(q.runId, artifactRun); client = q.clientId;
            return ready();
        }
        assert.equal(name, "evaluation_comparison");
        if (["source", "summary"].includes(args.action)) {
            assert.deepEqual(Object.keys(q), ["runToken"]); assert.equal(q.runToken, token);
            return args.action === "source" ? wrap("source", source(value)) : wrap("snapshot", value);
        }
        if (args.action === "close") {
            assert.deepEqual(Object.keys(q).sort(), ["clientId", "runToken"]);
            assert.equal(q.clientId, client); assert.equal(q.runToken, token);
            return ready(true);
        }
        assert.equal(args.action, "evidence");
        assert.deepEqual(Object.keys(q).sort(), ["arm", "binding", "request", "runToken", "turnId"]);
        assert.equal(q.runToken, token); assert.equal(q.binding, hash);
        assert.equal(q.turnId, selected.turn); assert.equal(q.arm, selected.arm);
        assert.deepEqual(Object.keys(q.request).sort(), ["kind", "observer"]);
        assert.deepEqual(plain(q.request.observer), omni);
        assert.ok(["receipt", "outputs"].includes(q.request.kind));
        const body = q.request.kind === "outputs" ? { kind: "outputs", outputs: clone(outputs) }
            : entry.receipt_available ? { kind: "receipt", receipt: { synthetic_transport: true } }
                : { kind: "missing", reason: "no_accepted_receipt" };
        return wrap("evidence", { version: 1, binding: hash, row: clone(entry.row), scope: clone(entry.source.scope),
            before_head: entry.source.before_head, after_head: entry.source.after_head,
            observer: clone(q.request.observer), edge: q.request.kind === "receipt" ? "after" : null,
            read_only: true, generation_grant: false, body });
    };
    const c = new panelModules.ComparisonReaderController(invoke, (error) => errors.push(error));
    try {
        c.contextChanged("synthetic-native4-artifact-framing", true);
        await c.pickManaged({ runId: artifactRun, mode: "approved_native" });
        assert.equal(c.get().status?.phase, "ready"); assert.equal(c.get().source?.protocol_version, 4);
        c.setObserver(omni); await c.loadSummary(); c.select(selected);
        assert.equal(c.get().error, null); assert.equal(c.get().summary?.report.version, 4);
        assert.deepEqual(plain(c.get().selected), selected);
        const actual = c.get().summary.report.turns.find((item) => item.turn === selected.turn && item.arm === selected.arm);
        assert.ok(actual, "actual controller summary retains the selected closed row");
        for (const key of ["phase", "error", "fallback", "actual_receipt_sha256"])
            assert.equal(actual[key], row[key], `selected metadata ${key}`);
        await c.inspect({ kind: "receipt", observer: omni });
        assert.equal(c.get().error, null);
        assert.equal(c.get().evidence?.body.kind, failed ? "missing" : "receipt");
        if (failed) assert.equal(c.get().evidence.body.reason, "no_accepted_receipt");
        await c.inspect({ kind: "outputs", observer: omni });
        assert.equal(c.get().error, null); assert.equal(c.get().evidence?.body.kind, "outputs");
        assert.deepEqual(errors, []);
        assert.deepEqual(calls.map((call) => call.action), ["managed", "source", "summary", "evidence", "evidence"]);
        return { c, calls, errors, entry, row };
    } catch (error) {
        try { await c.close(); } finally { c.dispose(); }
        throw error;
    }
}
function artifactFrame(f) {
    const before = f.calls.length;
    const markup = panelModules.renderToStaticMarkup(panelModules.createElement(panelModules.ComparisonReaderPanel, { controller: f.c }));
    assert.ok(Buffer.byteLength(markup) <= 256 * 1024, "bounded actual Panel static HTML");
    panelHtml.push(markup);
    assert.equal(f.calls.length, before, "rendering must not dispatch a read or generation action");
    const start = markup.search(/<div\b[^>]*class="comparison-evidence"[^>]*>/);
    assert.ok(start >= 0, "existing actual displayed-artifact container");
    const tail = markup.slice(start);
    let depth = 0, end = null;
    for (const tag of tail.matchAll(/<\/?div\b[^>]*>/g)) {
        depth += tag[0].startsWith("</") ? -1 : 1;
        if (depth === 0) { end = tag.index + tag[0].length; break; }
    }
    assert.ok(end !== null, "displayed-artifact div closes within the actual Panel");
    const artifact = tail.slice(0, end), raw = artifact.indexOf("<pre");
    assert.ok(raw >= 0 && artifact.slice(raw).includes(artifactMarker), "actual Director output body is displayed in that artifact");
    const context = textOnly(artifact.slice(0, raw));
    assert.match(context, new RegExp(`\\b${selected.turn}\\b`)); assert.match(context, /\bleft\b/i);
    assert.match(context, /\bObserver\s*[:·-]?\s*omniscient\b/i);
    return context;
}
async function panelCase(name, variants, work) {
    if (!panelModules || panelSetupFailures.some((failure) => failure.stage === "bundle-api")) return;
    const observations = [];
    for (const variant of variants) {
        let f;
        try { f = await artifactFixture(variant); }
        catch (error) { panelSetupFailures.push({ stage: "fixture", name, variant, error: safePanelError(error) }); return; }
        try { work(f); observations.push({ variant, passed: true }); }
        catch (error) { observations.push({ variant, passed: false, error: safePanelError(error) }); }
        finally {
            try { await f.c.close(); assert.equal(f.c.get().source, null); assert.equal(f.c.get().evidence, null); }
            catch (error) { panelSetupFailures.push({ stage: "fixture-close", name, variant, error: safePanelError(error) }); }
            finally { f.c.dispose(); }
        }
    }
    const outcome = { name, category: "headless-controller-panel", passed: observations.every((item) => item.passed), observations };
    panelCases.push(outcome); cases.push(outcome);
}
await panelCase("failed Native4 selected artifact frames actual failure and absent accepted receipt before raw output", [{ failed: true }], (f) => {
    const context = artifactFrame(f);
    assert.equal(f.row.phase, "failed"); assert.equal(f.entry.receipt_available, false);
    assert.match(context, /\bfailed\b/i); assert.match(context, /\bUnknownReference\b/);
    assert.match(context, /\bno accepted receipt\b|\bno_accepted_receipt\b|\b(?:accepted\s+)?receipt\s*[:·-]?\s*(?:absent|unavailable|not available|none)\b/i,
        "report-ready/raw-body availability must not obscure the selected row's absent receipt");
});
await panelCase("committed Native4 selected artifact keeps source receipt and unreviewed quality independent of fallback", [
    { failed: false, fallback: true }, { failed: false, fallback: false },
], (f) => {
    const context = artifactFrame(f);
    assert.equal(f.row.phase, "committed"); assert.equal(f.entry.receipt_available, true);
    assert.match(context, /\bcommitted\b/i);
    assert.match(context, new RegExp(`\\b${scope.story}\\b`), "actual recorded source story beside raw artifact");
    assert.match(context, new RegExp(`\\b${scope.branch}\\b`), "actual recorded source branch beside raw artifact");
    assert.match(context, /\bbefore\s*4\b[\s\S]*\bafter\s*5\b/i);
    assert.match(context, /\b(?:accepted\s+)?receipt\s*[:·-]?\s*(?:is\s*)?(?:available|recorded|present)\b/i);
    assert.match(context, /\b(?:quality|human|prose)\b.*\b(?:unreviewed|not reviewed|not_reviewed|not established|not accepted)\b/i,
        "commit and raw output do not establish model prose quality or human acceptance");
    assert.doesNotMatch(context, /\b(?:prose|narration|quality)\s*(?::|\bis\b)?\s*(?:accepted|approved|passed)\b/i);
    assert.equal(f.c.get().summary.report.human_reviewed, 0);
    assert.equal(f.c.get().summary.report.human_rubric, "not_reviewed");
    assert.equal(f.c.get().summary.report.quality_accepted, false);
});

// Independent visible-geometry freeze from c3c13a2b, BEFORE the CSS fix.
// Default176 cases above are unchanged. No expected CSS rule/position string is
// tested. This optional path uses the same actual Panel/controller fixtures,
// current complete stylesheet and one installed, owned headless Chromium.
async function artifactGeometryReview() {
    const evidence = { version: 1, rendering: "headless-chromium", nativeIpc: false, modelExecution: false,
        desktopControl: false, browserStarted: false, panelRendered: false, browserClosed: false, browserDrainUnknown: false,
        browserExecutable: null, browserVersion: null, playwrightPinnedVersion: "1.64.1",
        sourceCssSha256: null, observations: [], setupFailures: [], blockedNetworkRequests: [], pageErrors: [], screenshots: [] };
    const directory = path.join(output, `artifact-geometry-${randomUUID()}`);
    await mkdir(directory, { recursive: false });
    let context = null, page = null, f = null, stop = false, launchAttempted = false;
    const deadline = Date.now() + 60000;
    const bounded = async (promise, stage, cap = 10000) => {
        let timer;
        try { return await Promise.race([promise, new Promise((_, reject) => {
            timer = setTimeout(() => reject(Object.assign(Error(`GeometryTimeout:${stage}`), { geometrySetup: true })),
                Math.max(1, Math.min(cap, deadline - Date.now())));
        })]); } finally { clearTimeout(timer); }
    };
    const render = () => {
        const before = f.calls.length;
        const markup = panelModules.renderToStaticMarkup(panelModules.createElement(panelModules.ComparisonReaderPanel, { controller: f.c }));
        assert(Buffer.byteLength(markup) <= 256 * 1024, "BoundedGeometryPanelHtml");
        assert.equal(f.calls.length, before, "render dispatches no synthetic/native action");
        return markup;
    };
    let css = "";
    const show = async (width) => {
        await bounded(page.setViewportSize({ width, height: 900 }), "viewport");
        // Fixture-only scroll range: a short synthetic raw body must not let
        // document-end clamping silently avoid the requested overlap position.
        await bounded(page.setContent(`<!doctype html><html><head><meta charset="utf-8"><meta http-equiv="Content-Security-Policy" content="default-src 'none'; style-src 'unsafe-inline'; img-src data:"><title>LocalLore headless artifact geometry</title><style>${css}</style></head><body><main>${render()}</main><div aria-hidden="true" inert style="height:900px"></div></body></html>`,
            { waitUntil: "load", timeout: 10000 }), "static-content");
        const present = await bounded(page.evaluate(() => { scrollTo(0, 0); return !!document.querySelector("#comparison-reader"); }), "rendered-panel");
        evidence.panelRendered ||= present;
        assert(present, "ActualPanelRootMustRender");
    };
    const capture = async (name) => {
        const bytes = await bounded(page.screenshot({ type: "png", timeout: 10000 }), "screenshot");
        assert(bytes.length <= 16 * 1024 * 1024, "BoundedHeadlessPng");
        const file = `${name}.png`;
        await writeFile(path.join(directory, file), bytes, { flag: "wx" });
        evidence.screenshots.push({ file, bytes: bytes.length, sha256: createHash("sha256").update(bytes).digest("hex") });
    };
    const observe = async (name, work) => {
        if (stop) return;
        let measurement = null, passed = false, error = null;
        try { measurement = await work(); passed = true; }
        catch (failure) {
            error = safePanelError(failure);
            if (failure?.geometrySetup) { stop = true; evidence.setupFailures.push({ stage: name, error }); }
            if (failure?.geometryMeasurement) measurement = failure.geometryMeasurement;
        }
        evidence.observations.push({ name, passed, error, measurement });
        if (!stop && page && !page.isClosed()) {
            try { await capture(name); }
            catch (failure) { stop = true; evidence.setupFailures.push({ stage: `${name}-capture`, error: safePanelError(failure) }); }
        }
    };
    const verify = (measurement, condition, message) => {
        if (!condition) throw Object.assign(Error(message), { geometryMeasurement: measurement });
    };
    try {
        assert(panelModules && panelSetupFailures.length === 0, "ExistingPanelFixtureSetupRequired");
        css = await readFile(path.join(root, "ui/style.css"), "utf8");
        assert(Buffer.byteLength(css) <= 512 * 1024 && !css.includes("</style"), "BoundedActualStylesheet");
        evidence.sourceCssSha256 = createHash("sha256").update(css).digest("hex");
        f = await artifactFixture({ failed: true });
        const { chromium } = await import("playwright");
        evidence.browserExecutable = chromium.executablePath();
        launchAttempted = true;
        context = await bounded(chromium.launchPersistentContext(path.join(directory, "profile"), {
            executablePath: evidence.browserExecutable, headless: true, timeout: 15000,
            viewport: { width: 1280, height: 900 }, reducedMotion: "reduce", acceptDownloads: false, serviceWorkers: "block",
        }), "browser-launch", 20000);
        evidence.browserStarted = true;
        const browser = context.browser();
        assert(browser && typeof browser.version === "function", "OwnedBrowserVersionUnavailable");
        evidence.browserVersion = browser.version();
        context.setDefaultTimeout(10000);
        await context.route("**/*", (route) => {
            if (evidence.blockedNetworkRequests.length < 16) evidence.blockedNetworkRequests.push(route.request().url().slice(0, 256));
            return route.abort();
        });
        page = context.pages()[0] ?? await bounded(context.newPage(), "owned-page");
        page.on("pageerror", (error) => { if (evidence.pageErrors.length < 16) evidence.pageErrors.push(safePanelError(error)); });
        for (const width of [1280, 620]) await observe(`artifact-${width}`, async () => {
            await show(width);
            const measurement = await bounded(page.evaluate(async ({ story }) => {
                const artifact = document.querySelector(".comparison-evidence");
                if (!artifact) return { missing: "artifact" };
                artifact.scrollIntoView({ block: "start", behavior: "instant" });
                await new Promise((resolve) => requestAnimationFrame(() => requestAnimationFrame(resolve)));
                const paragraphs = [...artifact.querySelectorAll("p")];
                const targets = [
                    ["heading", artifact.querySelector("h4")],
                    ["source", paragraphs.find((node) => node.textContent.includes(story) && /before.*after/i.test(node.textContent))],
                    ["phase-error", paragraphs.find((node) => /Case phase:/.test(node.textContent) && /UnknownReference/.test(node.textContent))],
                ];
                const box = (node) => { const r = node.getBoundingClientRect(); return { left: r.left, top: r.top, right: r.right, bottom: r.bottom, width: r.width, height: r.height }; };
                return { viewport: { width: innerWidth, height: innerHeight }, scrollY, artifactTop: artifact.getBoundingClientRect().top, targets: targets.map(([name, node]) => {
                    if (!node) return { name, missing: true };
                    const rect = box(node), style = getComputedStyle(node);
                    const x = Math.min(innerWidth - 1, Math.max(1, rect.left + rect.width / 2));
                    const ys = [rect.top + Math.min(1, rect.height / 2), rect.top + rect.height / 2, rect.bottom - Math.min(1, rect.height / 2)];
                    return { name, text: node.textContent.trim().slice(0, 1000), rect,
                        visible: style.display !== "none" && style.visibility === "visible" && Number(style.opacity) > 0,
                        samples: ys.map((y) => { const hit = document.elementFromPoint(x, y); return { x, y, targetHit: !!hit && (hit === node || node.contains(hit)), hitTag: hit?.tagName ?? null, hitClass: hit?.className ?? null }; }) };
                }), headers: [...document.querySelectorAll(".comparison-report-context,.comparison-selection-context")].map((node) => ({ position: getComputedStyle(node).position, rect: box(node) })) };
            }, { story: scope.story }), "artifact-geometry");
            if (!Number.isFinite(measurement.artifactTop) || Math.abs(measurement.artifactTop) > 1)
                throw Object.assign(Error("ArtifactScrollStartCalibrationUnavailable"), { geometrySetup: true, geometryMeasurement: measurement });
            verify(measurement, measurement.targets?.length === 3, "ActualArtifactTargetsRequired");
            for (const target of measurement.targets) verify(measurement, !target.missing && target.visible && target.rect.width > 0 && target.rect.height > 0 &&
                target.rect.top >= -0.5 && target.rect.left >= -0.5 && target.rect.right <= width + 0.5 && target.rect.bottom <= 900.5 &&
                target.samples.every((sample) => sample.targetHit), `${target.name}: viewport fit and top/middle/bottom target hits required`);
            verify(measurement, /failed/.test(measurement.targets[2].text) && /Accepted receipt:\s*unavailable/.test(measurement.targets[2].text), "FailedRowReceiptContextMustRemainActual");
            return measurement;
        });
        f.c.clearEvidence();
        assert.equal(f.c.get().evidence, null); assert.ok(f.c.get().summary);
        for (const width of [1280, 620]) await observe(`selection-only-${width}`, async () => {
            await show(width);
            const measurement = await bounded(page.evaluate(async () => {
                const header = document.querySelector(".comparison-selection-context");
                if (!header) return { missing: "selection-context" };
                header.scrollIntoView({ block: "start", behavior: "instant" });
                await new Promise((resolve) => requestAnimationFrame(() => requestAnimationFrame(resolve)));
                const before = scrollY;
                scrollBy(0, 64);
                await new Promise((resolve) => requestAnimationFrame(() => requestAnimationFrame(resolve)));
                const rect = header.getBoundingClientRect(), title = header.querySelector("h3"), r = title?.getBoundingClientRect();
                const hit = r ? document.elementFromPoint(r.left + r.width / 2, r.top + r.height / 2) : null;
                return { before, after: scrollY, artifactPresent: !!document.querySelector(".comparison-evidence"),
                    header: { top: rect.top, bottom: rect.bottom, text: header.textContent.trim().slice(0, 1000) },
                    contextHit: !!hit && !!title && (hit === title || title.contains(hit)) };
            }), "selection-context-geometry");
            if (!(measurement.after - measurement.before >= 32)) throw Object.assign(Error("SelectionScrollPrerequisiteUnavailable"), { geometrySetup: true, geometryMeasurement: measurement });
            verify(measurement, !measurement.artifactPresent && measurement.header.top >= -0.5 && measurement.header.bottom <= 900.5 &&
                measurement.contextHit && measurement.header.text.includes(scope.story), "SelectionWithoutArtifactMustKeepItsActualContextVisibleDuringScroll");
            return measurement;
        });
        f.c.setObserver({ kind: "character", id: "mira" });
        assert.equal(f.c.get().summary, null); assert.equal(f.c.get().evidence, null);
        await observe("mira-620", async () => {
            await show(620);
            const measurement = await bounded(page.evaluate(() => ({ observer: document.querySelector("#comparison-reader")?.getAttribute("data-observer"),
                artifactPresent: !!document.querySelector(".comparison-evidence"), text: document.body.innerText.slice(0, 24000) })), "mira-context");
            verify(measurement, measurement.observer === "mira" && !measurement.artifactPresent && !/Case phase:\s*failed|UnknownReference|SYNTHETIC_DIRECTOR_BODY/.test(measurement.text),
                "NarrowMiraLensMustNotGainPrivatePhaseErrorOrRawBody");
            return measurement;
        });
    } catch (error) {
        if (launchAttempted && !context) evidence.browserDrainUnknown = true;
        stop = true; evidence.setupFailures.push({ stage: "geometry-setup-or-runtime", error: safePanelError(error) });
    } finally {
        if (f) { try { await f.c.close(); } catch (error) { evidence.setupFailures.push({ stage: "fixture-close", error: safePanelError(error) }); } finally { f.c.dispose(); } }
        if (context) {
            let timer;
            try { await Promise.race([context.close(), new Promise((_, reject) => { timer = setTimeout(() => reject(Error("OwnedHeadlessBrowserCloseUnknown")), 10000); })]); evidence.browserClosed = true; }
            catch (error) { evidence.browserDrainUnknown = true; evidence.setupFailures.push({ stage: "browser-close", error: safePanelError(error) }); }
            finally { clearTimeout(timer); }
        }
    }
    const cssAfter = createHash("sha256").update(await readFile(path.join(root, "ui/style.css"))).digest("hex");
    if (evidence.sourceCssSha256 && cssAfter !== evidence.sourceCssSha256) evidence.setupFailures.push({ stage: "source-attribution", error: "StylesheetChangedDuringGeometryRun" });
    if (evidence.blockedNetworkRequests.length) evidence.setupFailures.push({ stage: "blocked-network", error: "StaticGeometryFixtureMustNotRequireNetwork" });
    evidence.passed = evidence.setupFailures.length === 0 && evidence.pageErrors.length === 0 && evidence.blockedNetworkRequests.length === 0 && evidence.browserClosed &&
        !evidence.browserDrainUnknown && evidence.observations.length === 5 && evidence.observations.every((item) => item.passed);
    await writeFile(path.join(directory, "geometry.json"), JSON.stringify(evidence, null, 2), { flag: "wx" });
    if (evidence.setupFailures.length === 0) cases.push({ name: "actual headless artifact geometry preserves visible framing and narrow-lens privacy", category: "headless-chromium-geometry", passed: evidence.passed });
    return evidence;
}
const geometry = geometryMode ? await artifactGeometryReview() : null;
for (const [index, markup] of panelHtml.entries()) await writeFile(path.join(output, `${panelPrefix}-${index}.html`), markup, { flag: "wx" });
const panelSourceAfter = await panelHashes();
if (JSON.stringify(panelSourceAfter) !== JSON.stringify(panelSourceBefore))
    panelSetupFailures.push({ stage: "source-attribution", error: "Panel/checker source changed during headless checks" });
const result = {
    version: 1,
    cases,
    passed: cases.filter((c) => c.passed).length,
    failed: cases.filter((c) => !c.passed).length,
    synthetic_dto: true,
    decoder_only: false,
    decoder_cases: decoderCaseCount,
    headless_panel_cases: panelCases,
    headless_panel_setup_failure: panelSetupFailures.length > 0,
    headless_panel_setup_failures: panelSetupFailures,
    headless_panel_source_before: panelSourceBefore,
    headless_panel_source_after: panelSourceAfter,
    headless_static_html: panelHtml.length > 0,
    headless_html_files: panelHtml.length,
    evidence: geometryMode ? "Synthetic DTO/controller/Panel plus actual headless Chromium CSS geometry; no Rust/Store/native IPC/WebView/model authority" : "Synthetic DTO decoders plus actual reader controller/Panel static HTML; no Rust/Store/native IPC/WebView/pixels/model authority",
    rust_store: false,
    native_ipc: false,
    native_webview: false,
    rendered_ui: geometry?.panelRendered === true,
    model_execution: false,
    ...(geometryMode ? { geometry } : {}),
};
await writeFile(
    path.join(output, `scene-reader-${randomUUID()}.json`),
    JSON.stringify(result, null, 2),
    { flag: "wx" },
);
console.log(JSON.stringify(result));
if (result.failed || result.headless_panel_setup_failure || (geometryMode && !geometry?.passed)) process.exitCode = 1;

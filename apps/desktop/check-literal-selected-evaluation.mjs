// Frozen before selected2 frontend changes. SYNTHETIC DTO/mock transport and
// actual controller + React static HTML only: no Rust, IPC, WebView or model.
// Run from apps/desktop: node check-literal-selected-evaluation.mjs
import assert from "node:assert/strict";
import { build } from "esbuild";
import { mkdir, readFile, writeFile } from "node:fs/promises";
import { createHash, randomUUID } from "node:crypto";
import { fileURLToPath, pathToFileURL } from "node:url";
import path from "node:path";
const root = fileURLToPath(new URL(".", import.meta.url));
const output =
    process.env.LOCALLORE_CHECK_OUTPUT_DIR ??
    path.join(root, "artifacts/checks");
await mkdir(output, { recursive: true });
const cohort = randomUUID(),
    prefix = `literal-selected-${cohort}`;
const built = await build({
    stdin: {
        contents:
            'export * from "./ui/selected-evaluation-model";export {SelectedEvaluationController} from "./ui/selected-evaluation-controller";export {SelectedEvaluationView} from "./ui/selected-evaluation-view";export {createElement} from "react";export {renderToStaticMarkup} from "react-dom/server";',
        resolveDir: root,
        loader: "tsx",
    },
    bundle: true,
    platform: "node",
    format: "cjs",
    write: false,
});
const bundle = path.join(output, `${prefix}.cjs`);
await writeFile(bundle, built.outputFiles[0].contents, { flag: "wx" });
const m = (await import(pathToFileURL(bundle).href)).default;
const hash = "a".repeat(64),
    token = "22222222-2222-2222-2222-222222222222",
    runId = "33333333-3333-3333-3333-333333333333",
    planToken = "44444444-4444-4444-4444-444444444444";
const source = {
    readerClientId: "55555555-5555-5555-5555-555555555555",
    runToken: token,
    binding: hash,
};
const row = { turn: "synthetic-move-4", arm: "left" },
    selection = { turn: row.turn, clicked_arm: row.arm, index: 4 },
    scope = { story: "synthetic-selected", branch: "main" };
const omni = { kind: "omniscient" },
    player = { kind: "player" },
    clone = (v) => structuredClone(v);
const constructions = [
    {
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
    },
    {
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
    },
];
const tagged = (version) =>
    version === 2
        ? { source_protocol_version: 3, constructions: clone(constructions) }
        : {};
function prepared(version = 2) {
    return {
        version,
        kind: "selected_prepared",
        binding: hash,
        lane: "scripted_selected_case",
        selection: clone(selection),
        arms: ["left", "right"].map((arm) => ({
            arm,
            scope: clone(scope),
            before_head: 2,
            prefix_sha256: hash,
            input_semantic_sha256: hash,
        })),
        ...tagged(version),
    };
}
function summary(version = 2) {
    return {
        version,
        kind: "selected_read",
        binding: hash,
        lane: "scripted_selected_case",
        selection: clone(selection),
        arms: ["left", "right"].map((arm) => ({
            arm,
            scope: clone(scope),
            before_head: 2,
            after_head: 3,
            available: true,
        })),
        read_only: true,
        execution_available: false,
        ...tagged(version),
    };
}
function diagnostics(version = 2) {
    return {
        version,
        kind: "selected_diagnostics",
        binding: hash,
        lane: "scripted_selected_case",
        completed: true,
        rows: ["left", "right"].map((arm, index) => ({
            turn: row.turn,
            arm,
            phase: "committed",
            error: null,
            expected: '"accepted"',
            passed: true,
            failures: [],
            quality_flags: [],
            roles: 2,
            roles_known: true,
            elapsed_ms: 1,
            actual_receipt_sha256: hash,
            privacy_passed: true,
            context_evidence_available: true,
            ...(version === 2
                ? {
                      construction: clone(constructions[index]),
                      construction_evidence_status:
                          index === 0
                              ? "validated_literal"
                              : "validated_relevant",
                      construction_matches: true,
                      literal_source_units: index === 0 ? 4 : null,
                      literal_selected_start: index === 0 ? 1 : null,
                      literal_selected_units: index === 0 ? 3 : null,
                      fallback: null,
                  }
                : {}),
        })),
        physical_setups: 0,
        physical_setup_ms: null,
        left_charged_ms: 2,
        right_charged_ms: 2,
        left_reserved_roles: 2,
        right_reserved_roles: 2,
        human_reviewed: 0,
        quality_accepted: false,
        unavailable: ["scripted_lane_no_native_setup_measurement"],
        ...tagged(version),
    };
}
const wrap = (kind, key, value) => ({
    version: 1,
    kind,
    run_token: token,
    [key]: value,
});
const decoders = {
    prepared: (v) => m.checkedSelectedPrepared(clone(v)),
    summary: (v) =>
        m.checkedSelectedSummary(
            wrap("selected_summary", "summary", clone(v)),
            token,
            hash,
        ),
    diagnostics: (v, s = summary(v.version)) =>
        m.checkedSelectedDiagnostics(
            wrap("selected_diagnostics_result", "diagnostics", clone(v)),
            token,
            clone(s),
        ),
};
const cases = [],
    controllers = new Set();
async function check(name, body) {
    let timer;
    try {
        await Promise.race([
            Promise.resolve().then(body),
            new Promise((_, reject) => {
                timer = setTimeout(
                    () => reject(new Error("bounded synthetic case timeout")),
                    3000,
                );
            }),
        ]);
        cases.push({ name, passed: true });
    } catch (error) {
        cases.push({
            name,
            passed: false,
            error: String(error?.message ?? error).slice(0, 200),
        });
    } finally {
        clearTimeout(timer);
    }
}
async function bad(kind, name, mutate, version = 2) {
    await check(`${kind}: rejects ${name}`, () => {
        const fixture = { prepared, summary, diagnostics }[kind](version);
        mutate(fixture);
        assert.throws(() => decoders[kind](fixture), /SelectedEvaluationWire/);
    });
}
for (const version of [1, 2])
    for (const [name, factory] of Object.entries({
        prepared,
        summary,
        diagnostics,
    })) {
        await check(
            `${name}${version}: accepted detached immutable synthetic DTO`,
            () => {
                const fixture = factory(version),
                    original = clone(fixture),
                    result = decoders[name](fixture);
                assert.deepEqual(result, original);
                assert.deepEqual(fixture, original);
                if (fixture.arms) result.arms[0].before_head = 99;
                else result.rows[0].expected = "mutated decoded copy";
                assert.deepEqual(fixture, original);
            },
        );
    }
for (const kind of ["prepared", "summary", "diagnostics"]) {
    for (const [name, mutate] of [
        [
            "future version",
            (v) => {
                v.version = 3;
            },
        ],
        [
            "wrong source protocol",
            (v) => {
                v.source_protocol_version = 2;
            },
        ],
        [
            "missing source protocol",
            (v) => {
                delete v.source_protocol_version;
            },
        ],
        [
            "missing constructions",
            (v) => {
                delete v.constructions;
            },
        ],
        [
            "null constructions",
            (v) => {
                v.constructions = null;
            },
        ],
        [
            "descriptor order",
            (v) => {
                v.constructions.reverse();
            },
        ],
        [
            "extra descriptor",
            (v) => {
                v.constructions.push(clone(constructions[0]));
            },
        ],
        [
            "descriptor unknown field",
            (v) => {
                v.constructions[0].private = true;
            },
        ],
        [
            "descriptor prompt mismatch",
            (v) => {
                v.constructions[0].prompt_version = "locallore-play-v2.5";
            },
        ],
        [
            "literal memory policy",
            (v) => {
                v.constructions[0].context_policy = "state_relevant_memory_v1";
            },
        ],
        [
            "missing nullable descriptor",
            (v) => {
                delete v.constructions[0].context_version;
            },
        ],
        [
            "unknown outer field",
            (v) => {
                v.private = "forbidden";
            },
        ],
        [
            "invalid hash",
            (v) => {
                v.binding = "x";
            },
        ],
        [
            "unsafe version scalar",
            (v) => {
                v.version = [2];
            },
        ],
        [
            "old version with new tags",
            (v) => {
                v.version = 1;
            },
        ],
    ])
        await bad(kind, name, mutate);
    await bad(
        kind,
        "legacy unknown tag",
        (v) => {
            v.source_protocol_version = 3;
        },
        1,
    );
}
for (const kind of ["prepared", "summary"])
    for (const [name, mutate] of [
        [
            "physical arm order",
            (v) => {
                v.arms.reverse();
            },
        ],
        [
            "duplicate physical arm",
            (v) => {
                v.arms[1].arm = "left";
            },
        ],
        [
            "invalid head",
            (v) => {
                v.arms[0].before_head = 0.5;
            },
        ],
        [
            "selection unknown key",
            (v) => {
                v.selection.prose = "x";
            },
        ],
    ])
        await bad(kind, name, mutate);
for (const key of [
    "construction",
    "construction_evidence_status",
    "construction_matches",
    "literal_source_units",
    "literal_selected_start",
    "literal_selected_units",
    "fallback",
])
    await bad("diagnostics", `missing required row ${key}`, (v) => {
        delete v.rows[0][key];
    });
for (const [name, mutate] of [
    [
        "row construction physical mismatch",
        (v) => {
            v.rows[0].construction = clone(constructions[1]);
        },
    ],
    [
        "literal labelled relevant",
        (v) => {
            v.rows[0].construction_evidence_status = "validated_relevant";
        },
    ],
    [
        "relevant labelled literal",
        (v) => {
            v.rows[1].construction_evidence_status = "validated_literal";
        },
    ],
    [
        "unknown evidence status",
        (v) => {
            v.rows[0].construction_evidence_status = "trusted";
        },
    ],
    [
        "literal start outside source",
        (v) => {
            v.rows[0].literal_selected_start = 5;
        },
    ],
    [
        "literal suffix outside source",
        (v) => {
            v.rows[0].literal_selected_units = 4;
        },
    ],
    [
        "negative literal units",
        (v) => {
            v.rows[0].literal_source_units = -1;
        },
    ],
    [
        "unsafe literal units",
        (v) => {
            v.rows[0].literal_source_units = Number.MAX_SAFE_INTEGER + 1;
        },
    ],
    [
        "null validated literal units",
        (v) => {
            v.rows[0].literal_source_units = null;
        },
    ],
    [
        "relevant literal counts",
        (v) => {
            v.rows[1].literal_source_units = 1;
        },
    ],
    [
        "guard retains literal counts",
        (v) => {
            v.rows[0].construction_evidence_status = "not_applicable_guard";
        },
    ],
    [
        "array fallback",
        (v) => {
            v.rows[0].fallback = [false];
        },
    ],
    [
        "nonboolean agreement",
        (v) => {
            v.rows[0].construction_matches = 1;
        },
    ],
    [
        "old policy row field",
        (v) => {
            v.rows[0].policy = "state_recent_transcript_v1";
        },
    ],
    [
        "unknown native lane",
        (v) => {
            v.lane = "native";
        },
    ],
])
    await bad("diagnostics", name, mutate);
await check(
    "diagnostics: rejects cross-version old summary/new diagnostics",
    () =>
        assert.throws(
            () => decoders.diagnostics(diagnostics(2), summary(1)),
            /SelectedEvaluationWire/,
        ),
);
await check(
    "diagnostics: rejects cross-version new summary/old diagnostics",
    () =>
        assert.throws(
            () => decoders.diagnostics(diagnostics(1), summary(2)),
            /SelectedEvaluationWire/,
        ),
);
await check("diagnostics: zero literal history is valid", () => {
    const d = diagnostics();
    Object.assign(d.rows[0], {
        literal_source_units: 0,
        literal_selected_start: 0,
        literal_selected_units: 0,
    });
    decoders.diagnostics(d);
});
await check(
    "diagnostics: forwarded literal failure with narration fallback is valid",
    () => {
        const d = diagnostics();
        Object.assign(d.rows[0], {
            phase: "failed",
            passed: false,
            error: "Agency",
            actual_receipt_sha256: null,
            roles: 1,
            fallback: true,
        });
        decoders.diagnostics(d);
    },
);
function noCapture(phase, status) {
    const d = diagnostics();
    d.rows.forEach((r) =>
        Object.assign(r, {
            phase,
            actual_receipt_sha256: phase === "committed" ? hash : null,
            roles: 0,
            roles_known: phase !== "committed",
            elapsed_ms: 0,
            privacy_passed: false,
            context_evidence_available: false,
            construction_matches: false,
            construction_evidence_status: status,
            literal_source_units: null,
            literal_selected_start: null,
            literal_selected_units: null,
            fallback: null,
        }),
    );
    return d;
}
for (const [phase, status] of [
    ["rejected", "not_applicable_guard"],
    ["not_run_dependency", "not_applicable_dependency"],
    ["committed", "unavailable"],
])
    await check(`diagnostics: honest ${status} is valid`, () =>
        decoders.diagnostics(noCapture(phase, status)),
    );
function status(client, version = 2) {
    return {
        version: 1,
        kind: "selected_evaluation",
        client_id: client,
        operation_id: 7,
        phase: "completed",
        running: false,
        lane: "scripted_baseline",
        plan_token: planToken,
        run_id: runId,
        run_token: token,
        binding: hash,
        prepared: prepared(version),
        error: null,
        cause: null,
        cleanup_required: false,
    };
}
await check("outer status remains transport1 with nested prepared2", () =>
    assert.equal(
        m.checkedSelectedStatus(status(source.readerClientId)).prepared.version,
        2,
    ),
);
await check("outer status rejects unknown native error", () => {
    const s = status(source.readerClientId);
    s.error = "NativeOops";
    assert.throws(() => m.checkedSelectedStatus(s), /SelectedEvaluationWire/);
});
await check("outer source identity stays exactly three fields", () =>
    assert.deepEqual(m.checkedSelectedSource(clone(source)), source),
);
function fixture(version = 2) {
    const calls = [],
        hooks = new Map();
    const c = new m.SelectedEvaluationController(async (command, args) => {
        assert.equal(command, "evaluation_selected");
        const body = JSON.parse(args.request);
        calls.push({ action: args.action, body });
        if (hooks.has(args.action)) return hooks.get(args.action)(body);
        if (args.action === "open" || args.action === "status")
            return status(body.clientId, version);
        if (args.action === "summary")
            return wrap("selected_summary", "summary", summary(version));
        if (args.action === "diagnostics")
            return wrap(
                "selected_diagnostics_result",
                "diagnostics",
                diagnostics(version),
            );
        if (args.action === "evidence")
            return wrap("selected_evidence", "evidence", {
                version: 1,
                binding: hash,
                row: { turn: row.turn, arm: body.arm },
                scope: clone(scope),
                before_head: 2,
                after_head: 3,
                observer: clone(body.request.observer),
                edge: "after",
                read_only: true,
                generation_grant: false,
                body: {
                    kind: "receipt",
                    receipt: { proof: "SYNTHETIC-OMNI-CANARY" },
                },
            });
        throw new Error(`unexpected synthetic action ${args.action}`);
    });
    controllers.add(c);
    c.setContext("synthetic-context", true);
    c.setObserver(omni);
    return { c, calls, hooks };
}
async function ready(f) {
    await f.c.open(runId);
    await f.c.loadSummary();
    assert.equal(f.c.get().error, null);
    assert.ok(f.c.get().summary);
}
function render(f, observer = omni) {
    return m.renderToStaticMarkup(
        m.createElement(m.SelectedEvaluationView, {
            controller: f.c,
            source,
            row,
            observer,
        }),
    );
}
const html = [];
await check(
    "controller/headless: nested2 literal and relevant identity/evidence proof",
    async () => {
        const f = fixture();
        await ready(f);
        await f.c.readDiagnostics();
        assert.equal(f.c.get().diagnostics.version, 2);
        const text = render(f);
        html.push(text);
        assert.match(text, /Literal player conversation/);
        assert.match(text, /Relevant memory/);
        assert.match(text, /validated literal/i);
        assert.match(text, /Literal source units/i);
        assert.match(text, /fake inference/);
        assert.doesNotMatch(text, /Recent transcript baseline/);
        await f.c.readEvidence("left", { kind: "receipt", observer: omni });
        assert.equal(f.c.get().diagnostics, null); // Existing private-surface replacement fence.
        assert.equal(f.c.get().evidence.body.kind, "receipt");
        html.push(render(f));
    },
);
await check(
    "headless: old selected1 retains recent baseline labels",
    async () => {
        const f = fixture(1);
        await ready(f);
        await f.c.readDiagnostics();
        const text = render(f);
        html.push(text);
        assert.match(text, /Recent transcript baseline/);
        assert.doesNotMatch(text, /Literal source units/);
    },
);
await check(
    "headless: guard privacy is not applicable, never a leak claim",
    async () => {
        const f = fixture();
        await ready(f);
        f.hooks.set("diagnostics", () =>
            wrap(
                "selected_diagnostics_result",
                "diagnostics",
                noCapture("rejected", "not_applicable_guard"),
            ),
        );
        await f.c.readDiagnostics();
        const text = render(f);
        html.push(text);
        assert.match(text, /Not applicable/);
        assert.doesNotMatch(text, /privacy leak/i);
    },
);
await check(
    "headless: recovery keeps context/privacy unavailable and roles unknown",
    async () => {
        const f = fixture();
        await ready(f);
        f.hooks.set("diagnostics", () =>
            wrap(
                "selected_diagnostics_result",
                "diagnostics",
                noCapture("committed", "unavailable"),
            ),
        );
        await f.c.readDiagnostics();
        const text = render(f);
        html.push(text);
        assert.match(text, /Unavailable/);
        assert.match(text, /Unknown; historical calls were not recovered/);
    },
);
await check(
    "controller/headless: actor prop and observer change synchronously hide old Omni bodies",
    async () => {
        const f = fixture();
        await ready(f);
        await f.c.readDiagnostics();
        await f.c.readEvidence("left", { kind: "receipt", observer: omni });
        assert.match(render(f), /SYNTHETIC-OMNI-CANARY/);
        const text = render(f, player);
        html.push(text);
        assert.doesNotMatch(text, /SYNTHETIC-OMNI-CANARY/);
        assert.doesNotMatch(text, /Recorded results/);
        const client = f.c.get().clientId,
            op = f.c.get().status.operation_id;
        f.c.setObserver(player);
        assert.equal(f.c.get().diagnostics, null);
        assert.equal(f.c.get().evidence, null);
        assert.equal(f.c.get().clientId, client);
        assert.equal(f.c.get().status.operation_id, op);
        assert.equal(
            f.calls.filter((x) =>
                ["cancel", "start", "resume"].includes(x.action),
            ).length,
            0,
        );
    },
);
await check(
    "controller: held diagnostics cannot publish after lens change",
    async () => {
        const f = fixture();
        await ready(f);
        let release;
        f.hooks.set(
            "diagnostics",
            () =>
                new Promise((resolve) => {
                    release = resolve;
                }),
        );
        const pending = f.c.readDiagnostics();
        const client = f.c.get().clientId;
        assert.ok(release);
        f.c.setObserver(player);
        release(
            wrap("selected_diagnostics_result", "diagnostics", diagnostics()),
        );
        await pending;
        assert.equal(f.c.get().diagnostics, null);
        assert.equal(f.c.get().clientId, client);
    },
);
await check(
    "controller: summary version must match the native prepared identity",
    async () => {
        const f = fixture();
        await f.c.open(runId);
        f.hooks.set("summary", () =>
            wrap("selected_summary", "summary", summary(1)),
        );
        await f.c.loadSummary();
        assert.equal(f.c.get().summary, null);
        assert.equal(f.c.get().error, "SelectedEvaluationWire");
    },
);
for (const c of controllers) c.dispose();
const sourceHashes = Object.fromEntries(
    await Promise.all(
        [
            "ui/selected-evaluation-model.ts",
            "ui/selected-evaluation-controller.ts",
            "ui/selected-evaluation-view.tsx",
            "ui/comparison-reader-model.ts",
        ].map(async (name) => [
            name,
            createHash("sha256")
                .update(await readFile(path.join(root, name)))
                .digest("hex"),
        ]),
    ),
);
for (const [index, text] of html.entries())
    await writeFile(path.join(output, `${prefix}-${index}.html`), text, {
        flag: "wx",
    });
const result = {
    version: 1,
    evidence:
        "SYNTHETIC DTO/mock transport/React static HTML; no Rust/native IPC/WebView/image/model",
    sourceHashes,
    checks: cases.length,
    passed: cases.filter((c) => c.passed).length,
    failed: cases.filter((c) => !c.passed).length,
    html: html.length,
    cases,
};
await writeFile(
    path.join(output, `${prefix}.json`),
    JSON.stringify(result, null, 2),
    { flag: "wx" },
);
console.log(JSON.stringify(result));
if (result.failed) process.exitCode = 1;

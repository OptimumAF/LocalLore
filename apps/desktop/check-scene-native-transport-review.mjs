// Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0
// Independent freeze from 5d966ab1 BEFORE frontend production. SOURCE ONLY / UNRUN.
// Actual existing decoders/controller/View, SYNTHETIC transport, static React
// HTML. No Rust/native IPC/WebView/model/assets/pixels/worker-cleanup proof.
// From apps/desktop: node check-scene-native-transport-review.mjs
import assert from "node:assert/strict";
import { build } from "esbuild";
import { mkdir, readFile, writeFile } from "node:fs/promises";
import { createHash, randomUUID } from "node:crypto";
import { fileURLToPath, pathToFileURL } from "node:url";
import path from "node:path";

assert.equal(
    process.argv.length,
    2,
    "fixed checker takes no command-line arguments",
);
const root = fileURLToPath(new URL(".", import.meta.url));
const output =
    process.env.LOCALLORE_CHECK_OUTPUT_DIR ??
    path.join(root, "artifacts/checks");
await mkdir(output, { recursive: true });
const prefix = `scene-native-transport-${randomUUID()}`;
const sourceNames = [
    "ui/comparison-run-model.ts",
    "ui/comparison-run-controller.ts",
    "ui/comparison-run-view.tsx",
    "check-scene-native-transport-review.mjs",
];
const hashes = async () =>
    Object.fromEntries(
        await Promise.all(
            sourceNames.map(async (name) => [
                name,
                createHash("sha256")
                    .update(await readFile(path.join(root, name)))
                    .digest("hex"),
            ]),
        ),
    );
const sourceBefore = await hashes();
const evidence =
    "SYNTHETIC DTO/object transport + actual existing controller/decoders/View + React static HTML; no Rust/native IPC/WebView/pixels/model/assets or cleanup proof";
let m;
try {
    const built = await build({
        stdin: {
            contents:
                'export * from "./ui/comparison-run-model";export {ComparisonRunController,createNativeComparisonRunController} from "./ui/comparison-run-controller";export {ComparisonRunView,ComparisonRunCleanupView} from "./ui/comparison-run-view";export {createElement} from "react";export {renderToStaticMarkup} from "react-dom/server";',
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
    m = (await import(pathToFileURL(bundle).href)).default;
} catch (error) {
    const result = {
        version: 1,
        evidence,
        setupFailure: true,
        checks: 0,
        error: String(error?.message ?? error).slice(0, 500),
        sourceBefore,
        sourceAfter: await hashes(),
    };
    await writeFile(
        path.join(output, `${prefix}.json`),
        JSON.stringify(result, null, 2),
        { flag: "wx" },
    );
    console.log(JSON.stringify(result));
    process.exitCode = 1;
    throw Error(
        "scene native transport setup failed; no behavioral baseline established",
    );
}
const clone = (value) => structuredClone(value);
const CLIENT = "11111111-1111-1111-1111-111111111111";
const RUN = "22222222-2222-2222-2222-222222222222";
const TOKEN = "33333333-3333-3333-3333-333333333333";
const OTHER = "44444444-4444-4444-4444-444444444444";
const NATIVE = "evaluation_comparison_native",
    SCRIPTED = "evaluation_comparison_run";
function status(protocol = 4, extra = {}) {
    return {
        version: protocol === 4 ? 3 : 2,
        kind: "comparison_run",
        protocol_version: protocol,
        input_lane: "approved_native",
        client_id: CLIENT,
        run_id: RUN,
        run_token: TOKEN,
        operation_id: 1,
        comparison_kind: "paired",
        batch: 1,
        phase: "paused",
        running: false,
        error: null,
        completed_scenes: 1,
        completed: false,
        report_ready: true,
        source_matches: true,
        cleanup_required: false,
        cleanup_running: false,
        cause: null,
        ...extra,
    };
}
function scriptedStatus(extra = {}) {
    const value = status(3, {
        version: 1,
        input_lane: "scripted_baseline",
        ...extra,
    });
    delete value.cleanup_required;
    delete value.cleanup_running;
    delete value.cause;
    return value;
}
function catalog(protocol = 4, extra = {}) {
    return {
        version: protocol === 4 ? 3 : 2,
        kind: "comparison_run_catalog",
        protocol_version: protocol,
        input_lane: "approved_native",
        max_new_scenes: 4,
        runs: [
            {
                run_id: RUN,
                client_id: CLIENT,
                comparison_kind: "paired",
                initial_batch: 1,
                created_ms: 1,
                protocol_version: protocol,
                input_lane: "approved_native",
            },
        ],
        ...extra,
    };
}
function scriptedCatalog() {
    const value = catalog(3, { version: 1, input_lane: "scripted_baseline" });
    value.runs[0].input_lane = "scripted_baseline";
    return value;
}
const cleanup = (extra = {}) => ({
    version: 1,
    kind: "selected_cleanup",
    cleanup_required: false,
    running: false,
    error: null,
    ...extra,
});
const cases = [],
    html = [],
    fixtures = new Set();
async function check(name, work, category = "behavior") {
    let timer;
    try {
        await Promise.race([
            Promise.resolve().then(work),
            new Promise((_, reject) => {
                timer = setTimeout(
                    () => reject(Error("bounded synthetic case timeout")),
                    6000,
                );
            }),
        ]);
        cases.push({ name, category, passed: true });
    } catch (error) {
        cases.push({
            name,
            category,
            passed: false,
            error: String(error?.message ?? error).slice(0, 350),
        });
    } finally {
        clearTimeout(timer);
    }
}
const tick = () => new Promise((resolve) => setTimeout(resolve, 0));
async function until(predicate) {
    const deadline = Date.now() + 2500;
    while (!predicate()) {
        if (Date.now() >= deadline)
            throw Error("synthetic observation deadline");
        await new Promise((resolve) => setTimeout(resolve, 5));
    }
}
function deferred() {
    let resolve;
    const promise = new Promise((done) => {
        resolve = done;
    });
    return { promise, resolve };
}
function fixture({ protocol = 4, scripted = false, allowed = true } = {}) {
    const calls = [],
        errors = [],
        hooks = new Map();
    let current = null;
    const reply = (extra = {}) =>
        scripted ? scriptedStatus(extra) : status(protocol, extra);
    const invoke = async (command, args) => {
        assert.equal(
            command,
            scripted ? SCRIPTED : NATIVE,
            "one fixed existing command",
        );
        assert.deepEqual(Object.keys(args).sort(), ["action", "query"]);
        assert.ok(
            args.query &&
                typeof args.query === "object" &&
                !Array.isArray(args.query),
        );
        assert.ok(
            Buffer.byteLength(JSON.stringify(args.query), "utf8") <= 4096,
        );
        const action = args.action,
            query = clone(args.query);
        const keys = {
            catalog: [],
            start: ["clientId", "comparisonKind", "batch"],
            lookup: ["clientId"],
            open: ["runId"],
            status: ["runToken"],
            resume: ["runToken", "batch"],
            cancel: ["runToken", "operationId"],
            close: ["runToken"],
            cleanup_status: [],
            retry_cleanup: [],
        }[action];
        assert.ok(keys, `closed action ${action}`);
        assert.deepEqual(
            Object.keys(query).sort(),
            [...keys].sort(),
            "no renderer protocol/provider/path selector",
        );
        assert.ok(calls.length < 128, "bounded synthetic transcript");
        calls.push({ command, action, query });
        if (hooks.has(action)) return hooks.get(action)(query);
        if (action === "catalog")
            return scripted ? scriptedCatalog() : catalog(protocol);
        if (action === "cleanup_status" || action === "retry_cleanup")
            return cleanup();
        if (action === "start")
            return (current = reply({
                client_id: query.clientId,
                comparison_kind: query.comparisonKind,
                batch: query.batch,
            }));
        if (action === "open")
            return (current = reply({ run_id: query.runId }));
        if (action === "lookup" || action === "status") {
            if (!current) throw Error("UnknownEvaluationRun");
            return clone(current);
        }
        if (action === "resume")
            return (current = reply({
                ...current,
                operation_id: 2,
                batch: query.batch,
                phase: "paused",
                completed_scenes: 2,
            }));
        if (action === "cancel")
            return (current = reply({
                ...current,
                phase: "paused",
                running: false,
                error: "Cancelled",
            }));
        if (action === "close")
            return reply({
                ...(current ?? {}),
                run_token: query.runToken,
                phase: "closed",
                running: false,
            });
        throw Error("unexpected action");
    };
    const c = scripted
        ? new m.ComparisonRunController(invoke, (e) => errors.push(e))
        : m.createNativeComparisonRunController(invoke, (e) => errors.push(e));
    c.setContext("scene-native-synthetic-context", allowed);
    const f = {
        c,
        calls,
        errors,
        hooks,
        setCurrent: (v) => {
            current = clone(v);
        },
        getCurrent: () => clone(current),
        reply,
    };
    fixtures.add(f);
    return f;
}
const actions = (f) => f.calls.map((call) => call.action);
const generated = (f) =>
    f.calls.filter((call) => ["start", "resume"].includes(call.action));
function current4(f) {
    assert.equal(f.c.get().error, null);
    assert.equal(
        f.c.get().status?.protocol_version,
        4,
        "actual controller adopted native4",
    );
    assert.equal(f.c.get().status?.version, 3);
}
function render(f, onlyCleanup = false) {
    const markup = m.renderToStaticMarkup(
        m.createElement(
            onlyCleanup ? m.ComparisonRunCleanupView : m.ComparisonRunView,
            { controller: f.c, onInspect: () => {} },
        ),
    );
    assert.ok(Buffer.byteLength(markup, "utf8") < 64 * 1024);
    html.push(markup);
    return markup;
}
function button(markup, label) {
    const found = [
        ...markup.matchAll(/<button\b([^>]*)>([\s\S]*?)<\/button>/g),
    ].filter((match) =>
        match[2]
            .replace(/<[^>]*>/g, "")
            .trim()
            .includes(label),
    );
    assert.equal(found.length, 1, `one real static View button: ${label}`);
    return found[0];
}
const wire = (decode, value) =>
    assert.throws(() => decode(value), { message: "ComparisonRunWire" });

await check(
    "existing APIs and old native/scripted exact DTOs calibrate independently",
    () => {
        for (const name of [
            "checkedNativeComparisonRunStatus",
            "checkedNativeComparisonRunCatalog",
            "checkedComparisonRunStatus",
            "checkedComparisonRunCatalog",
            "createNativeComparisonRunController",
            "ComparisonRunView",
        ])
            assert.equal(typeof m[name], "function", name);
        assert.deepEqual(
            m.checkedNativeComparisonRunStatus(status(3)),
            status(3),
        );
        assert.deepEqual(
            m.checkedNativeComparisonRunCatalog(catalog(3)),
            catalog(3),
        );
        assert.deepEqual(
            m.checkedComparisonRunStatus(scriptedStatus()),
            scriptedStatus(),
        );
        assert.deepEqual(
            m.checkedComparisonRunCatalog(scriptedCatalog()),
            scriptedCatalog(),
        );
        for (const [decode, dto] of [
            [m.checkedNativeComparisonRunStatus, status(3)],
            [m.checkedNativeComparisonRunCatalog, catalog(3)],
            [m.checkedComparisonRunStatus, scriptedStatus()],
            [m.checkedComparisonRunCatalog, scriptedCatalog()],
        ]) {
            assert.equal(
                JSON.stringify(decode(dto)),
                JSON.stringify(dto),
                "old closed DTO bytes unchanged",
            );
        }
    },
    "calibration",
);
await check(
    "actual default native3 controller preserves exact object requests and old status",
    async () => {
        const f = fixture({ protocol: 3 });
        await f.c.open(RUN);
        await f.c.status();
        await f.c.close();
        assert.equal(f.c.get().error, null);
        assert.equal(f.c.get().status?.version, 2);
        assert.equal(f.c.get().status?.protocol_version, 3);
        assert.deepEqual(actions(f), ["open", "status", "close"]);
        assert.deepEqual(
            f.calls.map((x) => x.query),
            [{ runId: RUN }, { runToken: TOKEN }, { runToken: TOKEN }],
        );
    },
    "calibration",
);
await check(
    "actual scripted controller keeps its old command and receives no native cleanup",
    async () => {
        const f = fixture({ scripted: true });
        await f.c.start("paired", 1);
        assert.equal(f.c.get().error, null);
        assert.equal(f.c.get().status?.version, 1);
        assert.equal(f.c.get().status?.protocol_version, 3);
        assert.deepEqual(actions(f), ["start"]);
        assert.ok(f.calls.every((x) => x.command === SCRIPTED));
    },
    "calibration",
);

for (const [name, extra] of [
    ["partial", {}],
    ["historical", { source_matches: false }],
    [
        "unverified",
        {
            phase: "retained",
            operation_id: null,
            source_matches: null,
            report_ready: false,
            completed_scenes: 0,
        },
    ],
    [
        "confirmation",
        { phase: "awaiting_confirmation", running: true, report_ready: false },
    ],
    ["closed active owner", { phase: "closed", running: true }],
    [
        "cleanup required",
        {
            phase: "cleanup_required",
            cleanup_required: true,
            error: "Cleanup",
            cause: "NativeUnavailable",
        },
    ],
    ["cleanup running", { cleanup_running: true, running: false }],
])
    await check(`native4 status preserves independent ${name} fields`, () => {
        const dto = status(4, extra);
        assert.deepEqual(m.checkedNativeComparisonRunStatus(dto), dto);
    });
await check(
    "native4 catalog and status decode detached values with matching row protocol",
    () => {
        const original = catalog(4),
            decoded = m.checkedNativeComparisonRunCatalog(original);
        assert.deepEqual(decoded, original);
        decoded.runs[0].run_id = OTHER;
        assert.equal(original.runs[0].run_id, RUN);
        const input = status(4),
            detached = m.checkedNativeComparisonRunStatus(input);
        detached.completed_scenes = 3;
        assert.equal(input.completed_scenes, 1);
        assert.deepEqual(
            m.checkedNativeComparisonRunCatalog(catalog(4, { runs: [] })),
            catalog(4, { runs: [] }),
        );
    },
);
for (const [name, mutate] of [
    [
        "old version with protocol4",
        (v) => {
            v.version = 2;
        },
    ],
    [
        "new version with protocol3",
        (v) => {
            v.protocol_version = 3;
        },
    ],
    [
        "future version",
        (v) => {
            v.version = 4;
        },
    ],
    [
        "future protocol",
        (v) => {
            v.protocol_version = 5;
        },
    ],
    [
        "scripted lane",
        (v) => {
            v.input_lane = "scripted_baseline";
        },
    ],
    [
        "missing cause",
        (v) => {
            delete v.cause;
        },
    ],
    [
        "missing source",
        (v) => {
            delete v.source_matches;
        },
    ],
    [
        "extra selector",
        (v) => {
            v.scenePolicy = "literal";
        },
    ],
    [
        "nonboolean cleanup",
        (v) => {
            v.cleanup_required = "false";
        },
    ],
    [
        "private cause",
        (v) => {
            v.cause = "private fixture diagnostic";
        },
    ],
    [
        "unknown error",
        (v) => {
            v.error = "UnreviewedError";
        },
    ],
    [
        "unsafe operation",
        (v) => {
            v.operation_id = Number.MAX_SAFE_INTEGER + 1;
        },
    ],
    [
        "negative scenes",
        (v) => {
            v.completed_scenes = -1;
        },
    ],
    [
        "over-four scenes",
        (v) => {
            v.completed_scenes = 5;
        },
    ],
    [
        "null token",
        (v) => {
            v.run_token = null;
        },
    ],
    [
        "unbounded extra",
        (v) => {
            v.extra = "x".repeat(33 * 1024);
        },
    ],
])
    await check(`native4 status refuses ${name}`, () => {
        const dto = status(4);
        mutate(dto);
        wire(m.checkedNativeComparisonRunStatus, dto);
    });
await check(
    "throwing getter becomes bounded wire error without diagnostic publication",
    () => {
        const dto = status(4);
        Object.defineProperty(dto, "phase", {
            enumerable: true,
            get() {
                throw Error("PRIVATE_SYNTHETIC_DETAIL");
            },
        });
        wire(m.checkedNativeComparisonRunStatus, dto);
    },
);
for (const [name, mutate] of [
    [
        "old envelope with4",
        (v) => {
            v.version = 2;
        },
    ],
    [
        "new envelope with3",
        (v) => {
            v.protocol_version = 3;
        },
    ],
    [
        "future envelope",
        (v) => {
            v.version = 4;
        },
    ],
    [
        "row protocol3",
        (v) => {
            v.runs[0].protocol_version = 3;
        },
    ],
    [
        "row scripted lane",
        (v) => {
            v.runs[0].input_lane = "scripted_baseline";
        },
    ],
    [
        "missing row protocol",
        (v) => {
            delete v.runs[0].protocol_version;
        },
    ],
    [
        "extra row key",
        (v) => {
            v.runs[0].provider = "fixture";
        },
    ],
    [
        "extra outer key",
        (v) => {
            v.protocol = 4;
        },
    ],
    [
        "duplicate run",
        (v) => {
            v.runs.push(clone(v.runs[0]));
        },
    ],
    [
        "over32 rows",
        (v) => {
            v.runs = Array.from({ length: 33 }, () => clone(v.runs[0]));
        },
    ],
    [
        "unsafe timestamp",
        (v) => {
            v.runs[0].created_ms = Number.MAX_SAFE_INTEGER + 1;
        },
    ],
    [
        "unsupported chunk",
        (v) => {
            v.max_new_scenes = 5;
        },
    ],
])
    await check(`native4 catalog refuses ${name}`, () => {
        const dto = catalog(4);
        mutate(dto);
        wire(m.checkedNativeComparisonRunCatalog, dto);
    });
await check(
    "native3 catalog rejects4 row and scripted decoders reject all native4 DTOs",
    () => {
        const mixed = catalog(3);
        mixed.runs[0].protocol_version = 4;
        wire(m.checkedNativeComparisonRunCatalog, mixed);
        wire(m.checkedComparisonRunStatus, status(4));
        wire(m.checkedComparisonRunCatalog, catalog(4));
        const script = scriptedStatus({ protocol_version: 4 });
        wire(m.checkedComparisonRunStatus, script);
    },
);

await check(
    "actual native4 start lookup status resume close keep exact unchanged command fields",
    async () => {
        const f = fixture();
        await f.c.start("paired", 1);
        current4(f);
        const client = f.c.get().clientId;
        await f.c.lookup();
        await f.c.status();
        await f.c.resume(2);
        current4(f);
        await f.c.close();
        assert.equal(f.c.get().status?.phase, "closed");
        assert.equal(f.c.get().status?.protocol_version, 4);
        assert.deepEqual(actions(f), [
            "cleanup_status",
            "start",
            "lookup",
            "status",
            "cleanup_status",
            "resume",
            "close",
        ]);
        assert.deepEqual(
            f.calls.map((x) => x.query),
            [
                {},
                { clientId: client, comparisonKind: "paired", batch: 1 },
                { clientId: client },
                { runToken: TOKEN },
                {},
                { runToken: TOKEN, batch: 2 },
                { runToken: TOKEN },
            ],
        );
        assert.equal(f.c.get().error, null);
    },
);
await check(
    "actual native4 catalog open status never starts or selects a protocol",
    async () => {
        const f = fixture();
        await f.c.loadCatalog();
        assert.equal(f.c.get().catalog?.protocol_version, 4);
        await f.c.open(RUN);
        current4(f);
        await f.c.status();
        assert.deepEqual(actions(f), ["catalog", "open", "status"]);
        assert.equal(generated(f).length, 0);
    },
);
await check(
    "actual native4 pending operation can cancel at its exact reported operation",
    async () => {
        const f = fixture();
        f.hooks.set("start", (q) => {
            const value = status(4, {
                client_id: q.clientId,
                phase: "running",
                running: true,
                report_ready: false,
            });
            f.setCurrent(value);
            return value;
        });
        const work = f.c.start("paired", 1);
        try {
            await until(
                () =>
                    f.c.get().status?.protocol_version === 4 &&
                    f.c.get().status?.running,
            );
            assert.equal(f.c.get().pending?.operationId, 1);
            await f.c.cancel();
            assert.equal(f.c.get().status?.running, false);
            assert.equal(f.c.get().status?.error, "Cancelled");
            assert.deepEqual(f.calls.find((x) => x.action === "cancel").query, {
                runToken: TOKEN,
                operationId: 1,
            });
        } finally {
            f.setCurrent(
                status(4, { ...(f.getCurrent() ?? {}), running: false }),
            );
            f.c.setContext("cancel-finally", false);
            await work;
        }
    },
);
await check(
    "actual native4 pending cancel refuses same-token protocol3 acknowledgement",
    async () => {
        const f = fixture();
        f.hooks.set("start", (q) => {
            const value = status(4, {
                client_id: q.clientId,
                phase: "running",
                running: true,
                report_ready: false,
            });
            f.setCurrent(value);
            return value;
        });
        f.hooks.set("cancel", () =>
            status(3, {
                ...f.getCurrent(),
                version: 2,
                protocol_version: 3,
                phase: "paused",
                running: false,
            }),
        );
        const work = f.c.start("paired", 1);
        try {
            await until(
                () =>
                    f.c.get().status?.protocol_version === 4 &&
                    f.c.get().status?.running,
            );
            const accepted = clone(f.c.get().status);
            await f.c.cancel();
            assert.equal(f.c.get().error, "ComparisonRunWire");
            assert.deepEqual(f.c.get().status, accepted);
            assert.equal(f.c.get().uncertain, true);
        } finally {
            f.c.setContext("cancel-protocol-finally", false);
            await work;
        }
    },
);
for (const [name, observed] of [
    ["required", cleanup({ cleanup_required: true })],
    ["running", cleanup({ running: true })],
    ["error", cleanup({ error: "Cleanup" })],
])
    await check(
        `native4 cleanup ${name} blocks generation but preserves exact explicit recovery`,
        async () => {
            const f = fixture();
            await f.c.open(RUN);
            current4(f);
            f.hooks.set("cleanup_status", () => observed);
            await f.c.cleanupStatus();
            const before = f.calls.length;
            await f.c.start("paired", 1);
            await f.c.resume(1);
            assert.equal(f.calls.length, before);
            assert.deepEqual(f.c.get().cleanup, observed);
            await f.c.retryCleanup();
            assert.equal(f.calls.at(-1).action, "retry_cleanup");
            await f.c.status();
            assert.equal(f.calls.at(-1).action, "status");
        },
    );
await check(
    "native4 unknown cleanup blocks until explicit reconciliation without silent resume",
    async () => {
        const f = fixture();
        f.hooks.set("cleanup_status", () => {
            throw Error("EvaluationIo");
        });
        await f.c.cleanupStatus();
        assert.equal(f.c.get().cleanupUncertain, true);
        const before = f.calls.length;
        await f.c.start("paired", 1);
        assert.equal(f.calls.length, before);
        f.hooks.delete("cleanup_status");
        await f.c.cleanupStatus();
        assert.equal(f.c.get().cleanupUncertain, false);
        assert.equal(generated(f).length, 0);
        await f.c.start("paired", 1);
        current4(f);
        assert.equal(generated(f).length, 1);
    },
);

for (const [original, replacement] of [
    [4, 3],
    [3, 4],
]) {
    for (const action of ["status", "lookup", "start", "resume", "close"]) {
        await check(
            `owner protocol${original} refuses same identity changing to${replacement} through ${action}`,
            async () => {
                const f = fixture({ protocol: original });
                await f.c.start("paired", 1);
                assert.equal(f.c.get().status?.protocol_version, original);
                const accepted = clone(f.c.get().status),
                    old = f.getCurrent();
                f.hooks.set(action, () =>
                    status(replacement, {
                        ...old,
                        version: replacement === 4 ? 3 : 2,
                        protocol_version: replacement,
                        operation_id:
                            action === "resume" ? 2 : old.operation_id,
                        phase: action === "close" ? "closed" : "paused",
                        running: false,
                    }),
                );
                await (action === "start"
                    ? f.c.start("paired", 1)
                    : action === "resume"
                      ? f.c.resume(1)
                      : f.c[action]());
                assert.equal(f.c.get().error, "ComparisonRunWire");
                assert.deepEqual(
                    f.c.get().status,
                    accepted,
                    "rejected protocol cannot replace acknowledged private metadata",
                );
                assert.equal(f.c.get().uncertain, true);
            },
        );
    }
}
await check(
    "matching saved native4 metadata fences cold-open response with same identity but protocol3",
    async () => {
        const f = fixture();
        await f.c.loadCatalog();
        assert.equal(f.c.get().catalog?.runs[0].protocol_version, 4);
        f.hooks.set("open", () => status(3));
        await f.c.open(RUN);
        assert.equal(f.c.get().error, "ComparisonRunWire");
        assert.equal(f.c.get().status, null);
        assert.equal(f.c.get().uncertain, true);
    },
);
await check(
    "same run catalog protocol change cannot overwrite accepted native4 source ownership",
    async () => {
        const f = fixture();
        await f.c.loadCatalog();
        await f.c.open(RUN);
        current4(f);
        const accepted = clone(f.c.get().catalog);
        f.hooks.set("catalog", () => catalog(3));
        await f.c.loadCatalog();
        assert.equal(f.c.get().error, "ComparisonRunWire");
        assert.deepEqual(f.c.get().catalog, accepted);
        assert.equal(f.c.get().status?.protocol_version, 4);
    },
);
await check(
    "native4 completed counts survive later cleanup latch with preserved cause and blocked inspection",
    async () => {
        const f = fixture();
        await f.c.open(RUN);
        current4(f);
        f.setCurrent(
            status(4, {
                phase: "completed",
                completed: true,
                completed_scenes: 4,
            }),
        );
        await f.c.status();
        f.setCurrent(
            status(4, {
                phase: "cleanup_required",
                cleanup_required: true,
                cleanup_running: true,
                error: "Cleanup",
                cause: "NativeUnavailable",
                completed_scenes: 1,
                report_ready: true,
            }),
        );
        await f.c.status();
        const state = f.c.get();
        assert.equal(state.status.completed_scenes, 4);
        assert.equal(state.status.completed, true);
        assert.equal(state.status.cleanup_required, true);
        assert.equal(state.status.cleanup_running, true);
        assert.equal(state.status.cause, "NativeUnavailable");
        assert.equal(state.status.report_ready, false);
        const markup = render(f);
        assert.match(markup, /4\s*\/\s*4/);
        assert.match(button(markup, "Inspect report")[1], /\bdisabled/);
        assert.match(button(markup, "Resume next chunk")[1], /\bdisabled/);
    },
);
await check(
    "wrong-protocol retired close never releases native4 admission barrier",
    async () => {
        const f = fixture();
        await f.c.open(RUN);
        current4(f);
        f.hooks.set("close", () => status(3, { phase: "closed" }));
        f.c.setContext("new-observer-context", true);
        await until(() => f.calls.some((x) => x.action === "close"));
        await tick();
        assert.equal(f.c.get().status, null);
        assert.equal(f.c.get().clientId, null);
        assert.equal(f.c.get().uncertain, true);
        await f.c.start("paired", 1);
        assert.equal(
            generated(f).length,
            0,
            "foreign close is not an acknowledged revoke",
        );
        assert.equal(f.c.get().uncertain, true);
    },
);
await check(
    "actual late native4 start acknowledgement after context change closes only captured access",
    async () => {
        const f = fixture(),
            gate = deferred();
        let started;
        f.hooks.set("start", (q) => {
            started = status(4, { client_id: q.clientId });
            f.setCurrent(started);
            return gate.promise;
        });
        const work = f.c.start("paired", 1);
        try {
            await until(() => !!started);
            f.c.setContext("new-session-new-observer", false);
        } finally {
            gate.resolve(started ?? status(4));
            await work;
        }
        await until(() => f.calls.some((x) => x.action === "close"));
        await tick();
        assert.equal(f.c.get().context, "new-session-new-observer");
        assert.equal(f.c.get().allowed, false);
        assert.equal(f.c.get().status, null);
        assert.equal(f.c.get().catalog, null);
        assert.equal(f.c.get().clientId, null);
        assert.ok(
            f.calls
                .filter((x) => x.action === "close")
                .every((x) => x.query.runToken === TOKEN),
        );
        assert.equal(generated(f).length, 1);
        assert.equal(
            f.calls.some((x) => x.action === "resume"),
            false,
        );
    },
);
await check(
    "late native4 catalog cannot publish after actual controller context loss",
    async () => {
        const f = fixture(),
            gate = deferred();
        f.hooks.set("catalog", () => gate.promise);
        const work = f.c.loadCatalog();
        try {
            await until(() => actions(f).includes("catalog"));
            f.c.setContext("player-without-lab", false);
        } finally {
            gate.resolve(catalog(4));
            await work;
        }
        assert.equal(f.c.get().catalog, null);
        assert.equal(f.c.get().status, null);
        assert.equal(f.c.get().allowed, false);
        assert.equal(generated(f).length, 0);
    },
);
await check(
    "synchronous actual controller notification context loss fences dispatch before native start",
    async () => {
        const f = fixture();
        let changed = false;
        const stop = f.c.subscribe(() => {
            if (!changed && f.c.get().pending?.action === "start") {
                changed = true;
                f.c.setContext("reentrant-observer-denied", false);
            }
        });
        try {
            await f.c.start("paired", 1);
        } finally {
            stop();
        }
        assert.equal(changed, true);
        assert.equal(f.c.get().context, "reentrant-observer-denied");
        assert.equal(f.c.get().allowed, false);
        assert.equal(f.c.get().status, null);
        assert.deepEqual(
            f.calls,
            [],
            "same action/controller path denies before transport dispatch",
        );
    },
);
await check(
    "actual native4 View identifies protocol and scene construction without unsupported import guidance",
    async () => {
        const f = fixture();
        await f.c.open(RUN);
        current4(f);
        const markup = render(f);
        assert.match(markup, /Protocol\s*4/i);
        assert.match(markup, /scene construction/i);
        assert.match(
            markup,
            /[Hh]uman quality is not established|quality remains unreviewed/,
        );
        assert.doesNotMatch(markup, /Import a supported model using/);
        assert.match(markup, /Cleanup required/);
        assert.match(markup, /Reported cause/);
    },
);
await check(
    "actual native4 View hides captured metadata after context loss and keeps cleanup outside Lab",
    async () => {
        const f = fixture();
        await f.c.open(RUN);
        current4(f);
        f.c.setContext("play-hidden", false);
        await tick();
        const markup = render(f),
            recovery = render(f, true);
        assert.ok(!markup.includes(RUN) && !markup.includes(CLIENT));
        assert.match(markup, /Story Lab access is unavailable/);
        assert.match(recovery, /Refresh cleanup state/);
        assert.match(recovery, /Retry cleanup/);
    },
);

// Independent follow-up freeze against 8e047bff's null-protocol owner paths.
// The original 69 oracles above/below are unchanged. SOURCE ONLY / UNRUN;
// Root must measure these two additions before changing production.
await check(
    "lost start ACK matching native4 catalog pins owner before forbidden native3 lookup",
    async () => {
        const f = fixture();
        let client;
        f.hooks.set("start", (q) => {
            client = q.clientId;
            f.setCurrent(status(4, { client_id: client }));
            throw Error("EvaluationIo"); // Synthetic lost acknowledgement, not known refusal.
        });
        await f.c.start("paired", 1);
        assert.ok(client);
        assert.equal(f.c.get().error, "EvaluationIo");
        assert.equal(f.c.get().status, null);
        assert.equal(f.c.get().uncertain, true);
        const known = catalog(4);
        known.runs[0].client_id = client;
        f.hooks.set("catalog", () => clone(known));
        await f.c.loadCatalog();
        assert.equal(f.c.get().catalog?.protocol_version, 4);
        assert.equal(f.c.get().catalog?.runs[0].client_id, client);
        assert.equal(f.c.get().catalog?.runs[0].run_id, RUN);
        f.hooks.set("lookup", () => status(3, { client_id: client }));
        await f.c.lookup();
        assert.equal(f.c.get().error, "ComparisonRunWire");
        assert.equal(
            f.c.get().status,
            null,
            "forbidden native3 metadata must not become the current run",
        );
        assert.equal(f.c.get().clientId, client);
        assert.equal(f.c.get().catalog?.protocol_version, 4);
        assert.equal(f.c.get().uncertain, true);
        const before = f.calls.length;
        await f.c.start("paired", 1);
        await f.c.resume(1);
        assert.equal(
            f.calls.length,
            before,
            "unknown original ownership still blocks retry/resume",
        );
        assert.equal(generated(f).length, 1);
    },
);
await check(
    "lost cold-open ACK recovery catalog pins native4 before forbidden native3 lookup or close",
    async () => {
        const f = fixture();
        f.hooks.set("open", () => {
            throw Error("EvaluationIo");
        });
        await f.c.open(RUN);
        assert.equal(f.c.get().error, "EvaluationIo");
        assert.equal(f.c.get().status, null);
        assert.equal(f.c.get().uncertain, true);
        f.hooks.set("catalog", () => catalog(4));
        f.hooks.set("lookup", () => status(3));
        f.hooks.set("close", () => status(3, { phase: "closed" }));
        f.c.setContext("retired-open-new-context", true);
        await until(() => f.calls.some((call) => call.action === "lookup"));
        await f.c.close(); // Await public retirement reconciliation, not private state.
        assert.equal(f.c.get().context, "retired-open-new-context");
        assert.equal(f.c.get().status, null);
        assert.equal(f.c.get().clientId, null);
        assert.equal(
            f.c.get().uncertain,
            true,
            "wrong-protocol recovery cannot acknowledge the retired owner",
        );
        assert.equal(
            f.calls.filter((call) => call.action === "close").length,
            0,
            "forbidden lookup must not mint captured access for a native3 close",
        );
        await f.c.start("paired", 1);
        assert.equal(
            generated(f).length,
            0,
            "retired admission barrier cannot be drained by foreign protocol metadata",
        );
        assert.equal(f.c.get().uncertain, true);
    },
);

// Independent display regression freeze against actual View/controller source
// at7bd21c7b. The existing71 cases are unchanged. SOURCE ONLY / UNRUN; Root must
// measure these three additions before editing production or claiming a pass.
const visibleText = (markup) =>
    markup
        .replace(/<[^>]*>/g, " ")
        .replace(/\s+/g, " ")
        .trim();
function nativeIntroduction(markup) {
    const match = markup.match(
        /<h2\b[^>]*>Run full comparison<\/h2>\s*<p>([\s\S]*?)<\/p>/,
    );
    assert.ok(
        match,
        "actual native View has its introductory paragraph after its heading",
    );
    return visibleText(match[1]);
}
function neutralNativeIntroduction(markup) {
    const text = nativeIntroduction(markup);
    assert.match(
        text,
        /\b(?:comparison|protocol|configuration|model)\b.*\b(?:not (?:yet )?(?:been )?(?:available|reported|known)|unavailable|unknown)\b/i,
        "unavailable native details are stated explicitly, rather than inferred from missing metadata",
    );
    assert.doesNotMatch(
        visibleText(markup),
        /\bProtocol\s*[34]\b|\bscene construction\b|\b(?:literal_player_v1|relevant_memory_v1|literal_scene_v1|relevant_memory_scene_v1)\b/i,
        "absent status/catalog does not identify either protocol or construction",
    );
    assert.doesNotMatch(
        text,
        /\b(?:import|reimport|reuse|reused|publication)\b|LOCALLORE_D04|\bmodel root\b|\bexisting model controls\b/i,
        "missing metadata cannot prescribe ordinary import or development publication/root configuration",
    );
    return text;
}
await check(
    "native View without status or catalog reports neutral unavailable details without protocol or setup guesses",
    () => {
        const f = fixture();
        assert.equal(f.c.get().mode, "approved_native");
        assert.equal(f.c.get().allowed, true);
        assert.equal(f.c.get().status, null);
        assert.equal(f.c.get().catalog, null);
        assert.equal(f.c.get().clientId, null);
        assert.deepEqual(f.calls, []);
        const markup = render(f);
        assert.match(markup, /<section\b[^>]*id="comparison-run-native"/);
        neutralNativeIntroduction(markup);
        assert.deepEqual(
            f.calls,
            [],
            "rendering unavailable metadata dispatches no request or configuration action",
        );
    },
);
await check(
    "acknowledged native4 context retirement returns the same neutral unavailable View when status and catalog retire",
    async () => {
        const f = fixture();
        await f.c.loadCatalog();
        await f.c.open(RUN);
        current4(f);
        assert.equal(f.c.get().catalog?.protocol_version, 4);
        f.c.setContext("native4-retired-neutral-context", true);
        await f.c.close(); // Public retirement reconciliation; no private controller mutation.
        assert.equal(f.c.get().context, "native4-retired-neutral-context");
        assert.equal(f.c.get().allowed, true);
        assert.equal(f.c.get().mode, "approved_native");
        assert.equal(f.c.get().status, null);
        assert.equal(f.c.get().catalog, null);
        assert.equal(f.c.get().clientId, null);
        assert.equal(f.c.get().uncertain, false);
        assert.ok(
            f.calls.some(
                (call) =>
                    call.action === "close" && call.query.runToken === TOKEN,
            ),
            "the actual acknowledged native4 access was reconciled before observing the retired View",
        );
        assert.equal(generated(f).length, 0);
        const callsBeforeRender = f.calls.length,
            markup = render(f),
            fresh = fixture();
        assert.equal(
            nativeIntroduction(markup),
            nativeIntroduction(render(fresh)),
            "retired metadata does not preserve a protocol or setup guess absent in a fresh native View",
        );
        neutralNativeIntroduction(markup);
        assert.equal(
            f.calls.length,
            callsBeforeRender,
            "retired View guidance cannot dispatch replacement work",
        );
    },
);
await check(
    "awaiting native confirmation reports the active operation without claiming a physical model worker",
    async () => {
        const f = fixture();
        f.hooks.set("start", (q) => {
            const value = status(4, {
                client_id: q.clientId,
                phase: "awaiting_confirmation",
                running: true,
                report_ready: false,
                completed_scenes: 0,
            });
            f.setCurrent(value);
            return value;
        });
        const work = f.c.start("paired", 1);
        try {
            await until(
                () =>
                    f.c.get().status?.phase === "awaiting_confirmation" &&
                    f.c.get().status?.running === true,
            );
            current4(f);
            assert.equal(f.c.get().status.operation_id, 1);
            const markup = render(f);
            assert.match(
                visibleText(markup),
                /Waiting for native confirmation/i,
            );
            const pairs = [
                ...markup.matchAll(
                    /<dt>([\s\S]*?)<\/dt>\s*<dd>([\s\S]*?)<\/dd>/g,
                ),
            ].map((entry) => ({
                label: visibleText(entry[1]),
                value: visibleText(entry[2]),
            }));
            const operation = pairs.filter(
                ({ label }) =>
                    /\boperation\b/i.test(label) &&
                    /\bactive\b/i.test(label) &&
                    /\breported\b/i.test(label),
            );
            assert.equal(
                operation.length,
                1,
                "one actual dt labels reported active operation, not physical inference",
            );
            assert.match(operation[0].value, /\byes\b/i);
            assert.ok(
                pairs.every(
                    ({ label }) =>
                        !/\b(?:worker|model|inference)\b.*\brunning\b/i.test(
                            label,
                        ),
                ),
                "the pending native operation is not reported as a running physical model worker",
            );
        } finally {
            f.setCurrent(
                status(4, {
                    ...(f.getCurrent() ?? {}),
                    phase: "paused",
                    running: false,
                }),
            );
            f.c.setContext("confirmation-view-finally", false);
            await work;
        }
    },
);

for (const f of fixtures) f.c.dispose();
await tick();
const sourceAfter = await hashes();
await check(
    "production and frozen checker source remained identical throughout this measured run",
    () => assert.deepEqual(sourceAfter, sourceBefore),
    "source-attribution",
);
for (const [index, markup] of html.entries())
    await writeFile(path.join(output, `${prefix}-${index}.html`), markup, {
        flag: "wx",
    });
const result = {
    version: 1,
    evidence,
    setupFailure: false,
    sourceBefore,
    sourceAfter,
    checks: cases.length,
    passed: cases.filter((x) => x.passed).length,
    failed: cases.filter((x) => !x.passed).length,
    calibrationFailures: cases.filter(
        (x) => x.category === "calibration" && !x.passed,
    ).length,
    cases,
    transport: [...fixtures].map((f) => ({ calls: f.calls, errors: f.errors })),
    limitations: [
        "Source-only freeze; first actual outcome belongs to coordinator execution",
        "Synthetic DTOs/transport and static HTML are not Rust/native IPC/WebView/model/assets/runtime cleanup evidence",
        "Static HTML does not prove layout, mounted callbacks, keyboard accessibility or rendering",
        "Throwing-getter categorization does not establish descriptor-level getter rejection or getter nonexecution",
        "Oversize malformed DTO negatives do not independently establish otherwise-valid closed DTO byte caps",
        "No renderer protocol selector; native4 development asset reuse/root precedence remains separately owned",
        "No completed native4 no-load resume, Android, real model or human-quality qualification",
    ],
};
const encodedResult = JSON.stringify(result, null, 2);
assert.ok(
    Buffer.byteLength(encodedResult, "utf8") <= 2 * 1024 * 1024,
    "bounded local evidence packet",
);
await writeFile(path.join(output, `${prefix}.json`), encodedResult, {
    flag: "wx",
});
console.log(JSON.stringify(result));
if (result.failed) process.exitCode = 1;

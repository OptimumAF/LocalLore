// Frozen BEFORE native consumer production at c45fe005. SOURCE ONLY / UNRUN.
// Actual shared controller/components + SYNTHETIC IPC; no Rust, native IPC,
// WebView, model, OS dialog, pixels, cleanup proof or execution permission.
// From apps/desktop: node check-comparison-run-native.mjs
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
const prefix = `comparison-run-native-${randomUUID()}`,
    bundle = path.join(output, `${prefix}.cjs`);
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
await writeFile(bundle, built.outputFiles[0].contents, { flag: "wx" });
const m = (await import(pathToFileURL(bundle).href)).default;
const clone = (v) => structuredClone(v);
const CLIENT = "11111111-1111-1111-1111-111111111111",
    RUN = "22222222-2222-2222-2222-222222222222",
    TOKEN = "33333333-3333-3333-3333-333333333333",
    OTHER = "44444444-4444-4444-4444-444444444444";
const NATIVE = "evaluation_comparison_native",
    SCRIPTED = "evaluation_comparison_run";
function status(extra = {}) {
    return {
        version: 2,
        kind: "comparison_run",
        protocol_version: 3,
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
function legacyStatus(extra = {}) {
    const value = status({
        version: 1,
        input_lane: "scripted_baseline",
        ...extra,
    });
    delete value.cleanup_required;
    delete value.cleanup_running;
    delete value.cause;
    return value;
}
function catalog(native = true) {
    return {
        version: native ? 2 : 1,
        kind: "comparison_run_catalog",
        protocol_version: 3,
        input_lane: native ? "approved_native" : "scripted_baseline",
        max_new_scenes: 4,
        runs: [
            {
                run_id: RUN,
                client_id: CLIENT,
                comparison_kind: "paired",
                initial_batch: 1,
                created_ms: 1,
                protocol_version: 3,
                input_lane: native ? "approved_native" : "scripted_baseline",
            },
        ],
    };
}
const cleanup = (extra = {}) => ({
    version: 1,
    kind: "selected_cleanup",
    cleanup_required: false,
    running: false,
    error: null,
    ...extra,
});
const results = [],
    html = [],
    controllers = new Set();
async function check(name, body) {
    let timer;
    try {
        await Promise.race([
            Promise.resolve().then(body),
            new Promise((_, reject) => {
                timer = setTimeout(
                    () => reject(Error("bounded synthetic case timeout")),
                    5000,
                );
            }),
        ]);
        results.push({ name, passed: true });
    } catch (error) {
        results.push({
            name,
            passed: false,
            error: String(error?.message ?? error).slice(0, 240),
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
            throw Error("mock dispatch observation timeout");
        await new Promise((resolve) => setTimeout(resolve, 5));
    }
}
function deferred() {
    let resolve;
    const promise = new Promise((r) => {
        resolve = r;
    });
    return { promise, resolve };
}
function fixture({ native = true, options, allowed = true } = {}) {
    const calls = [],
        hooks = new Map(),
        errors = [];
    let current = null;
    const invoke = async (command, args) => {
        assert.ok(command === NATIVE || command === SCRIPTED);
        assert.deepEqual(Object.keys(args).sort(), ["action", "query"]);
        assert.ok(
            args.query !== null &&
                typeof args.query === "object" &&
                !Array.isArray(args.query),
            "native object query, never JSON text",
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
        assert.ok(keys, `unexpected action ${action}`);
        assert.deepEqual(Object.keys(query).sort(), [...keys].sort());
        calls.push({ command, action, query });
        if (hooks.has(action)) return hooks.get(action)(query, command);
        const reply = command === NATIVE ? status : legacyStatus;
        if (action === "cleanup_status" || action === "retry_cleanup") {
            assert.equal(command, NATIVE);
            return cleanup();
        }
        if (action === "catalog") return catalog(command === NATIVE);
        if (action === "start")
            return (current = reply({
                client_id: query.clientId,
                comparison_kind: query.comparisonKind,
                batch: query.batch,
            }));
        if (action === "open")
            return (current = reply({ run_id: query.runId }));
        if (action === "lookup") {
            if (!current) throw Error("UnknownEvaluationRun");
            return clone(current);
        }
        if (action === "status") {
            if (!current) throw Error("UnknownEvaluationRun");
            return clone(current);
        }
        if (action === "resume")
            return (current = reply({
                ...current,
                operation_id: 2,
                batch: query.batch,
                phase: "completed",
                completed: true,
                completed_scenes: 4,
            }));
        if (action === "cancel")
            return (current = reply({
                ...current,
                phase: "paused",
                running: false,
            }));
        if (action === "close")
            return reply({
                ...(current ?? {}),
                phase: "closed",
                running: false,
                run_token: query.runToken,
            });
        throw Error("unexpected dispatch");
    };
    const c = native
        ? options
            ? new m.ComparisonRunController(
                  invoke,
                  (e) => errors.push(e),
                  options,
              )
            : m.createNativeComparisonRunController(invoke, (e) =>
                  errors.push(e),
              )
        : new m.ComparisonRunController(invoke, (e) => errors.push(e));
    controllers.add(c);
    c.setContext("actual-synthetic-context", allowed);
    return {
        c,
        calls,
        hooks,
        errors,
        setCurrent: (value) => {
            current = clone(value);
        },
    };
}
const actions = (f) => f.calls.map((x) => x.action);
const generated = (f) =>
    f.calls.filter((x) => x.action === "start" || x.action === "resume");
const decodeStatus = (value) =>
    m.checkedNativeComparisonRunStatus(clone(value));
for (const [name, extra] of [
    ["partial verified", {}],
    ["historical verified", { source_matches: false }],
    [
        "awaiting confirmation",
        { phase: "awaiting_confirmation", running: true, report_ready: false },
    ],
    ["closed but execution running", { phase: "closed", running: true }],
    [
        "cleanup required",
        {
            phase: "cleanup_required",
            cleanup_required: true,
            cause: "NativeUnavailable",
            error: "Cleanup",
        },
    ],
    [
        "cleanup running independent of execution",
        { cleanup_running: true, running: false },
    ],
    [
        "unverified retained",
        {
            phase: "retained",
            source_matches: null,
            operation_id: null,
            report_ready: false,
            completed_scenes: 0,
        },
    ],
])
    await check(`V2 accepts independent ${name} fields unchanged`, () =>
        assert.deepEqual(decodeStatus(status(extra)), status(extra)),
    );
for (const [name, mutate] of [
    [
        "V1 tags",
        (v) => {
            v.version = 1;
            v.input_lane = "scripted_baseline";
        },
    ],
    [
        "mixed version",
        (v) => {
            v.version = 1;
        },
    ],
    [
        "mixed lane",
        (v) => {
            v.input_lane = "scripted_baseline";
        },
    ],
    [
        "unknown key",
        (v) => {
            v.owner = true;
        },
    ],
    [
        "future protocol",
        (v) => {
            v.protocol_version = 4;
        },
    ],
    [
        "array phase",
        (v) => {
            v.phase = ["cleanup_required"];
        },
    ],
    [
        "unknown phase",
        (v) => {
            v.phase = "loaded";
        },
    ],
    [
        "missing cause",
        (v) => {
            delete v.cause;
        },
    ],
    [
        "missing nullable error",
        (v) => {
            delete v.error;
        },
    ],
    [
        "missing nullable source",
        (v) => {
            delete v.source_matches;
        },
    ],
    [
        "missing cleanup flag",
        (v) => {
            delete v.cleanup_required;
        },
    ],
    [
        "array cleanup",
        (v) => {
            v.cleanup_running = [false];
        },
    ],
    [
        "string cleanup",
        (v) => {
            v.cleanup_required = "false";
        },
    ],
    [
        "private cause text",
        (v) => {
            v.cause = "C:/private/model.gguf error";
        },
    ],
    [
        "local error as wire cause",
        (v) => {
            v.cause = "ComparisonRunWire";
        },
    ],
    [
        "unknown error",
        (v) => {
            v.error = "RuntimePrivateDetails";
        },
    ],
    [
        "uppercase ID",
        (v) => {
            v.client_id = "AAAAAAAA-AAAA-AAAA-AAAA-AAAAAAAAAAAA";
        },
    ],
    [
        "null token",
        (v) => {
            v.run_token = null;
        },
    ],
    [
        "zero operation",
        (v) => {
            v.operation_id = 0;
        },
    ],
    [
        "unsafe operation",
        (v) => {
            v.operation_id = Number.MAX_SAFE_INTEGER + 1;
        },
    ],
    [
        "fractional batch",
        (v) => {
            v.batch = 1.5;
        },
    ],
    [
        "scene overflow",
        (v) => {
            v.completed_scenes = 5;
        },
    ],
    [
        "oversized invalid envelope",
        (v) => {
            v.extra = "é".repeat(32768);
        },
    ],
])
    await check(`V2 rejects ${name}`, () => {
        const v = status();
        mutate(v);
        assert.throws(() => decodeStatus(v), /ComparisonRunWire/);
    });
await check(
    "native causes/errors exactly extend the unchanged V1 allowlist",
    () => {
        assert.deepEqual(
            [...m.nativeComparisonRunErrors].sort(),
            [...m.comparisonRunErrors, "EvaluationModelBusy", "Cleanup"].sort(),
        );
        for (const code of m.nativeComparisonRunErrors)
            assert.deepEqual(
                decodeStatus(status({ error: code, cause: code })),
                status({ error: code, cause: code }),
            );
    },
);
await check("strict decoders never coerce V2 into V1 or V1 into V2", () => {
    assert.throws(
        () => m.checkedComparisonRunStatus(status()),
        /ComparisonRunWire/,
    );
    assert.throws(() => decodeStatus(legacyStatus()), /ComparisonRunWire/);
    assert.deepEqual(
        m.checkedComparisonRunStatus(legacyStatus()),
        legacyStatus(),
    );
});
await check(
    "native catalog exact shape detached without report/cleanup fabrication",
    () => {
        const v = catalog();
        const decoded = m.checkedNativeComparisonRunCatalog(v);
        assert.deepEqual(decoded, v);
        v.runs[0].run_id = OTHER;
        assert.equal(decoded.runs[0].run_id, RUN);
    },
);
for (const [name, mutate] of [
    [
        "V1",
        (v) => {
            v.version = 1;
            v.input_lane = "scripted_baseline";
        },
    ],
    [
        "wrong row lane",
        (v) => {
            v.runs[0].input_lane = "scripted_baseline";
        },
    ],
    [
        "extra outer",
        (v) => {
            v.cleanup_required = false;
        },
    ],
    [
        "extra row",
        (v) => {
            v.runs[0].completed = true;
        },
    ],
    [
        "missing identity",
        (v) => {
            delete v.runs[0].client_id;
        },
    ],
    [
        "unsafe timestamp",
        (v) => {
            v.runs[0].created_ms = Number.MAX_SAFE_INTEGER + 1;
        },
    ],
    [
        "negative timestamp",
        (v) => {
            v.runs[0].created_ms = -1;
        },
    ],
    [
        "wrong batch",
        (v) => {
            v.runs[0].initial_batch = 5;
        },
    ],
    [
        "array kind",
        (v) => {
            v.runs[0].comparison_kind = ["paired"];
        },
    ],
    [
        "null rows",
        (v) => {
            v.runs = null;
        },
    ],
    [
        "33 rows",
        (v) => {
            v.runs = Array.from({ length: 33 }, (_, i) => ({
                ...v.runs[0],
                run_id: `00000000-0000-0000-0000-${String(i).padStart(12, "0")}`,
            }));
        },
    ],
    [
        "oversized invalid outer",
        (v) => {
            v.extra = "é".repeat(65536);
        },
    ],
])
    await check(`native catalog rejects ${name}`, () => {
        const v = catalog();
        mutate(v);
        assert.throws(
            () => m.checkedNativeComparisonRunCatalog(v),
            /ComparisonRunWire/,
        );
    });
await check("V1 catalog refuses native metadata", () =>
    assert.throws(
        () => m.checkedComparisonRunCatalog(catalog()),
        /ComparisonRunWire/,
    ),
);

await check(
    "native factory initial cleanup is unobserved, with immutable mode",
    () => {
        const f = fixture();
        assert.equal(f.c.mode, "approved_native");
        assert.equal(f.c.get().mode, "approved_native");
        assert.equal(f.c.get().cleanup, null);
        assert.equal(f.c.get().cleanupPending, null);
        assert.equal(f.c.get().cleanupUncertain, false);
        assert.equal(f.c.get().cleanupError, null);
        assert.deepEqual(f.calls, []);
    },
);
await check(
    "closed constructor copies native option and cannot redirect captured transport",
    async () => {
        const options = { mode: "approved_native" };
        const f = fixture({ options });
        options.mode = "scripted_baseline";
        options.command = SCRIPTED;
        await f.c.start("paired", 1);
        await f.c.close();
        assert.equal(f.c.mode, "approved_native");
        assert.ok(f.calls.length >= 3);
        assert.ok(f.calls.every((x) => x.command === NATIVE));
    },
);
await check("legacy constructor cleanup methods are exact no-ops", async () => {
    const f = fixture({ native: false });
    const before = clone(f.c.get());
    await f.c.cleanupStatus();
    await f.c.retryCleanup();
    assert.deepEqual(f.calls, []);
    assert.deepEqual(f.c.get(), before);
    await f.c.start("paired", 1);
    assert.deepEqual(actions(f), ["start"]);
    assert.ok(f.calls.every((x) => x.command === SCRIPTED));
});
await check(
    "initial null cleanup start sends fresh status then one object start",
    async () => {
        const f = fixture();
        let id;
        const stop = f.c.subscribe(() => {
            if (f.c.get().pending?.action === "start")
                id ??= f.c.get().clientId;
        });
        await f.c.start("paired", 1);
        stop();
        assert.deepEqual(actions(f), ["cleanup_status", "start"]);
        assert.ok(id);
        assert.equal(f.calls[1].query.clientId, id);
        assert.equal(f.c.get().error, null);
        assert.equal(f.c.get().cleanupPending, null);
    },
);
await check(
    "last-known-clear repeated start still preflights and preserves exact UUID",
    async () => {
        const f = fixture();
        await f.c.start("paired", 1);
        const id = f.c.get().clientId;
        await f.c.start("paired", 1);
        assert.deepEqual(actions(f), [
            "cleanup_status",
            "start",
            "cleanup_status",
            "start",
        ]);
        assert.equal(f.c.get().clientId, id);
        assert.deepEqual(f.calls[1].query, f.calls[3].query);
    },
);
await check(
    "resume preserves token/client and requires another fresh cleanup read",
    async () => {
        const f = fixture();
        await f.c.open(RUN);
        const id = f.c.get().clientId;
        await f.c.resume(3);
        assert.deepEqual(actions(f), ["open", "cleanup_status", "resume"]);
        assert.deepEqual(f.calls[2].query, { runToken: TOKEN, batch: 3 });
        assert.equal(f.c.get().clientId, id);
        assert.equal(f.c.get().status.completed, true);
    },
);
for (const [name, observed] of [
    ["required", cleanup({ cleanup_required: true })],
    ["running", cleanup({ cleanup_required: true, running: true })],
])
    await check(
        `known cleanup ${name} blocks generation without implicit refresh/retry`,
        async () => {
            const f = fixture();
            await f.c.open(RUN);
            f.hooks.set("cleanup_status", () => observed);
            await f.c.cleanupStatus();
            f.calls.length = 0;
            await f.c.start("paired", 1);
            await f.c.resume(1);
            assert.deepEqual(f.calls, []);
            assert.deepEqual(f.c.get().cleanup, observed);
        },
    );
await check(
    "known cleanup uncertainty blocks until explicit reconciliation then fresh preflight",
    async () => {
        const f = fixture();
        f.hooks.set("cleanup_status", () => {
            throw Error("EvaluationIo");
        });
        await f.c.cleanupStatus();
        assert.equal(f.c.get().cleanupUncertain, true);
        f.calls.length = 0;
        await f.c.start("paired", 1);
        assert.deepEqual(f.calls, []);
        f.hooks.delete("cleanup_status");
        await f.c.cleanupStatus();
        await f.c.start("paired", 1);
        assert.deepEqual(actions(f), [
            "cleanup_status",
            "cleanup_status",
            "start",
        ]);
        assert.equal(
            f.calls.some((x) => x.action === "retry_cleanup"),
            false,
        );
    },
);
await check(
    "fresh preflight returning blocked state never dispatches generation",
    async () => {
        const f = fixture();
        f.hooks.set("cleanup_status", () =>
            cleanup({ cleanup_required: true, running: true }),
        );
        await f.c.start("paired", 1);
        assert.deepEqual(actions(f), ["cleanup_status"]);
        assert.equal(f.c.get().status, null);
        assert.equal(f.c.get().uncertain, false);
        assert.equal(f.c.get().cleanup.cleanup_required, true);
    },
);
await check(
    "failed preflight is cleanup uncertainty, not an admitted comparison ACK",
    async () => {
        const f = fixture();
        f.hooks.set("cleanup_status", () => {
            throw Error("EvaluationIo");
        });
        await f.c.start("paired", 1);
        assert.deepEqual(actions(f), ["cleanup_status"]);
        assert.equal(f.c.get().cleanupUncertain, true);
        assert.equal(f.c.get().cleanupError, "EvaluationIo");
        assert.equal(f.c.get().status, null);
        assert.equal(f.c.get().uncertain, false);
        assert.equal(f.c.get().pending, null);
    },
);
await check(
    "synchronous start notification context retirement prevents preflight and generation",
    async () => {
        const f = fixture();
        let once = false;
        const stop = f.c.subscribe(() => {
            if (!once && f.c.get().pending?.action === "start") {
                once = true;
                assert.ok(f.c.get().clientId);
                f.c.setContext("replacement", true);
            }
        });
        await f.c.start("paired", 1);
        stop();
        assert.equal(once, true);
        assert.deepEqual(f.calls, []);
        assert.equal(f.c.get().clientId, null);
    },
);
await check(
    "held preflight retirement is known unsent, no lookup/close/generation",
    async () => {
        const f = fixture(),
            gate = deferred();
        f.hooks.set("cleanup_status", () => gate.promise);
        const work = f.c.start("paired", 1);
        await until(() => actions(f).includes("cleanup_status"));
        f.c.setContext("replacement", true);
        gate.resolve(cleanup());
        await work;
        await tick();
        assert.deepEqual(actions(f), ["cleanup_status"]);
        assert.equal(f.c.get().clientId, null);
        assert.equal(f.c.get().status, null);
        assert.equal(f.c.get().uncertain, false);
    },
);
await check(
    "cleanup notification reentrancy cannot dispatch two generation admissions",
    async () => {
        const f = fixture();
        let nested,
            once = false;
        const stop = f.c.subscribe(() => {
            if (!once && f.c.get().cleanupPending === "status") {
                once = true;
                nested = f.c.start("paired", 1);
            }
        });
        await f.c.start("paired", 1);
        await nested;
        stop();
        assert.equal(once, true);
        assert.deepEqual(actions(f), ["cleanup_status", "start"]);
    },
);
await check(
    "auxiliary refresh remains available without Lab and never creates lifecycle pending",
    async () => {
        const f = fixture({ allowed: false }),
            gate = deferred();
        f.hooks.set("cleanup_status", () => gate.promise);
        const work = f.c.cleanupStatus();
        await until(() => f.calls.length === 1);
        assert.equal(f.c.get().cleanupPending, "status");
        assert.equal(f.c.get().pending, null);
        assert.equal(f.c.get().clientId, null);
        gate.resolve(cleanup());
        await work;
        await f.c.retryCleanup();
        assert.deepEqual(actions(f), ["cleanup_status", "retry_cleanup"]);
        assert.deepEqual(
            f.calls.map((x) => x.query),
            [{}, {}],
        );
        assert.equal(f.c.get().cleanupPending, null);
    },
);
await check(
    "newer auxiliary required/running result supersedes older clear reply",
    async () => {
        const f = fixture(),
            old = deferred();
        let n = 0;
        f.hooks.set("cleanup_status", () =>
            ++n === 1
                ? old.promise
                : cleanup({ cleanup_required: true, running: true }),
        );
        const a = f.c.cleanupStatus();
        await until(() => f.calls.length === 1);
        await f.c.cleanupStatus();
        old.resolve(cleanup());
        await a;
        assert.deepEqual(
            f.c.get().cleanup,
            cleanup({ cleanup_required: true, running: true }),
        );
        assert.equal(f.c.get().cleanupPending, null);
        assert.equal(f.c.get().cleanupUncertain, false);
    },
);
await check(
    "disposal fences late auxiliary private-state publication",
    async () => {
        const f = fixture(),
            gate = deferred();
        f.hooks.set("cleanup_status", () => gate.promise);
        const work = f.c.cleanupStatus();
        await until(() => f.calls.length === 1);
        f.c.dispose();
        const snapshot = clone(f.c.get());
        gate.resolve(cleanup({ cleanup_required: true }));
        await work;
        assert.deepEqual(f.c.get(), snapshot);
        assert.equal(generated(f).length, 0);
    },
);
await check(
    "later admission invalidates older auxiliary reply without erasing native cleanup status",
    async () => {
        const f = fixture(),
            old = deferred();
        let n = 0;
        f.hooks.set("cleanup_status", () =>
            ++n === 1 ? old.promise : cleanup(),
        );
        const a = f.c.cleanupStatus();
        await until(() => f.calls.length === 1);
        await f.c.cleanupStatus();
        f.hooks.set("start", (q) => {
            const v = status({
                client_id: q.clientId,
                phase: "cleanup_required",
                cleanup_required: true,
                cause: "Cleanup",
                error: "Cleanup",
                report_ready: false,
            });
            f.setCurrent(v);
            return v;
        });
        await f.c.start("paired", 1);
        old.resolve(cleanup());
        await a;
        assert.equal(f.c.get().status.cleanup_required, true);
        const count = f.calls.length;
        await f.c.start("paired", 1);
        assert.equal(f.calls.length, count);
    },
);
await check(
    "metadata status and lookup remain usable under observed global cleanup block",
    async () => {
        const f = fixture();
        await f.c.open(RUN);
        f.hooks.set("cleanup_status", () =>
            cleanup({ cleanup_required: true }),
        );
        await f.c.cleanupStatus();
        f.calls.length = 0;
        await f.c.status();
        await f.c.lookup();
        assert.deepEqual(actions(f), ["status", "lookup"]);
        assert.equal(f.c.get().cleanup.cleanup_required, true);
    },
);
await check(
    "actual native controller refuses V1 catalog/status instead of publishing mixed protocol",
    async () => {
        const f = fixture();
        f.hooks.set("catalog", () => catalog(false));
        await f.c.loadCatalog();
        assert.equal(f.c.get().catalog, null);
        assert.equal(f.c.get().error, "ComparisonRunWire");
        await f.c.open(RUN);
        const original = clone(f.c.get().status);
        f.hooks.set("status", () => legacyStatus());
        await f.c.status();
        assert.equal(f.c.get().error, "ComparisonRunWire");
        assert.equal(f.c.get().uncertain, true);
        assert.deepEqual(f.c.get().status, original);
        assert.ok(f.calls.every((x) => x.command === NATIVE));
    },
);
await check(
    "actual native status binds client/run/token before publication",
    async () => {
        for (const field of ["client_id", "run_id", "run_token"]) {
            const f = fixture();
            await f.c.open(RUN);
            const original = clone(f.c.get().status);
            f.hooks.set("status", () => status({ [field]: OTHER }));
            await f.c.status();
            assert.equal(f.c.get().error, "ComparisonRunWire");
            assert.equal(f.c.get().uncertain, true);
            assert.deepEqual(f.c.get().status, original);
        }
    },
);
await check(
    "actual generation ACK loss retains original client and explicit lookup never restarts",
    async () => {
        const f = fixture();
        f.hooks.set("start", (q) => {
            f.setCurrent(status({ client_id: q.clientId }));
            throw Error("EvaluationIo");
        });
        await f.c.start("paired", 1);
        const id = f.c.get().clientId;
        assert.ok(id);
        assert.equal(f.c.get().uncertain, true);
        await f.c.cleanupStatus();
        assert.equal(f.c.get().uncertain, true);
        assert.equal(generated(f).length, 1);
        await f.c.lookup();
        assert.equal(f.c.get().clientId, id);
        assert.equal(f.c.get().uncertain, false);
        assert.equal(
            f.calls.find((x) => x.action === "lookup").query.clientId,
            id,
        );
        assert.equal(generated(f).length, 1);
    },
);
await check(
    "unknown captured close and global cleanup remain separate recovery barriers",
    async () => {
        const f = fixture();
        await f.c.open(RUN);
        f.hooks.set("cleanup_status", () =>
            cleanup({ cleanup_required: true }),
        );
        await f.c.cleanupStatus();
        f.hooks.set("close", () => {
            throw Error("EvaluationIo");
        });
        await f.c.close();
        assert.equal(f.c.get().uncertain, true);
        f.hooks.set("close", () => {
            throw Error("UnknownEvaluationRun");
        });
        await f.c.close();
        await until(() => !f.c.get().uncertain);
        assert.equal(f.c.get().cleanup.cleanup_required, true);
        const count = f.calls.length;
        await f.c.start("paired", 1);
        assert.equal(f.calls.length, count);
    },
);
await check(
    "cleanup errors are auxiliary and do not overwrite lifecycle errors",
    async () => {
        const f = fixture();
        f.hooks.set("start", () => {
            throw Error("NativeUnavailable");
        });
        await f.c.start("paired", 1);
        const lifecycle = f.c.get().error;
        f.hooks.set("retry_cleanup", () => {
            throw Error("Cleanup");
        });
        await f.c.retryCleanup();
        assert.equal(f.c.get().error, lifecycle);
        assert.equal(f.c.get().cleanupError, "Cleanup");
    },
);
await check(
    "late native start closes captured native token after context retirement",
    async () => {
        const f = fixture(),
            gate = deferred();
        f.hooks.set("start", () => gate.promise);
        const work = f.c.start("paired", 1);
        await until(() => generated(f).length === 1);
        const id = f.c.get().clientId;
        f.c.setContext("replacement", true);
        f.setCurrent(status({ client_id: id }));
        gate.resolve(status({ client_id: id }));
        await work;
        await until(
            () =>
                f.calls.some((x) => x.action === "close") &&
                !f.c.get().uncertain,
        );
        assert.equal(f.c.get().status, null);
        assert.ok(
            f.calls
                .filter((x) => x.action === "close")
                .every(
                    (x) => x.command === NATIVE && x.query.runToken === TOKEN,
                ),
        );
    },
);
await check("two stable instances never cross-route late closes", async () => {
    const native = fixture(),
        scripted = fixture({ native: false }),
        gate = deferred();
    native.hooks.set("open", () => gate.promise);
    const work = native.c.open(RUN);
    await until(() => actions(native).includes("open"));
    native.c.dispose();
    await scripted.c.start("paired", 1);
    gate.resolve(status());
    await work;
    await until(() => actions(native).includes("close"));
    assert.ok(native.calls.every((x) => x.command === NATIVE));
    assert.ok(scripted.calls.every((x) => x.command === SCRIPTED));
    assert.equal(scripted.c.get().status.run_id, RUN);
});
for (const [name, latest] of [
    ["ordinary paused", { phase: "paused", error: "Cancelled", cause: null }],
    [
        "cleanup phase",
        {
            phase: "cleanup_required",
            cleanup_required: true,
            cause: "Cleanup",
            error: "Cleanup",
        },
    ],
    [
        "required flag on paused",
        { phase: "paused", cleanup_required: true, cause: "NativeUnavailable" },
    ],
    [
        "cleanup running on failed",
        {
            phase: "failed",
            cleanup_running: true,
            cause: null,
            error: "Cleanup",
        },
    ],
])
    await check(
        `V2 completed latch honors ${name} and exact latest cleanup/cause`,
        async () => {
            const f = fixture();
            await f.c.open(RUN);
            f.hooks.set("status", () =>
                status({
                    phase: "completed",
                    completed: true,
                    completed_scenes: 4,
                    cause: "EvaluationBudget",
                }),
            );
            await f.c.status();
            f.hooks.set("status", () => status({ ...latest }));
            await f.c.status();
            const v = f.c.get().status;
            assert.equal(v.completed, true);
            assert.equal(v.completed_scenes, 4);
            assert.equal(v.source_matches, true);
            assert.equal(v.cleanup_required, latest.cleanup_required ?? false);
            assert.equal(v.cleanup_running, latest.cleanup_running ?? false);
            assert.equal(v.cause, latest.cause);
            assert.equal(v.error, latest.error ?? null);
            const blocked =
                latest.phase === "cleanup_required" ||
                latest.cleanup_required ||
                latest.cleanup_running;
            assert.equal(v.phase, blocked ? latest.phase : "completed");
            assert.equal(v.report_ready, !blocked);
        },
    );
await check(
    "V2 completed latch copies latest execution running as well as null cause",
    async () => {
        const f = fixture();
        await f.c.open(RUN);
        f.hooks.set("status", () =>
            status({
                phase: "completed",
                completed: true,
                completed_scenes: 4,
                cause: "Cleanup",
            }),
        );
        await f.c.status();
        let n = 0,
            seen;
        const stop = f.c.subscribe(() => {
            if (f.c.get().status?.running) seen = clone(f.c.get().status);
        });
        f.hooks.set("status", () =>
            status(
                ++n === 1
                    ? {
                          phase: "running",
                          running: true,
                          cause: "EvaluationModelBusy",
                      }
                    : { cause: null },
            ),
        );
        await f.c.status();
        stop();
        assert.ok(seen);
        assert.equal(seen.completed_scenes, 4);
        assert.equal(seen.running, true);
        assert.equal(seen.cause, "EvaluationModelBusy");
        assert.equal(f.c.get().status.cause, null);
    },
);

function render(f, cleanupOnly = false) {
    const markup = m.renderToStaticMarkup(
        m.createElement(
            cleanupOnly ? m.ComparisonRunCleanupView : m.ComparisonRunView,
            {
                controller: f.c,
                onInspect: () => {
                    throw Error("SSR must not auto-inspect");
                },
            },
        ),
    );
    html.push(markup);
    return markup;
}
function button(markup, pattern) {
    const found = [
        ...markup.matchAll(/<button\b([^>]*)>([\s\S]*?)<\/button>/g),
    ].find((x) => pattern.test(x[2].replace(/<[^>]*>/g, "")));
    assert.ok(found, `button ${pattern}`);
    return found;
}
await check(
    "actual native View labels approved model and unreviewed quality with distinct ID",
    () => {
        const f = fixture();
        const markup = render(f);
        assert.match(markup, /id="comparison-run-native"/);
        assert.match(markup, /approved|installed.{0,40}model/i);
        assert.match(markup, /quality.{0,40}(not established|unreviewed)/i);
        assert.doesNotMatch(markup, /model (is|has been) loaded/i);
        assert.equal(f.calls.length, 0);
    },
);
await check(
    "actual scripted View preserves fake lane and old section ID",
    () => {
        const f = fixture({ native: false });
        const markup = render(f);
        assert.match(markup, /id="comparison-run"/);
        assert.match(markup, /Scripted.{0,40}fake inference/i);
        assert.equal(render(f, true), "");
    },
);
await check(
    "awaiting native confirmation remains visible without invented progress/load",
    async () => {
        const f = fixture();
        f.hooks.set("open", () =>
            status({
                phase: "awaiting_confirmation",
                running: false,
                report_ready: false,
                source_matches: null,
            }),
        );
        await f.c.open(RUN);
        const markup = render(f);
        assert.match(markup, /confirmation/i);
        assert.doesNotMatch(markup, /100%|model (is|has been) loaded/i);
        assert.match(button(markup, /Inspect/)[1], /\bdisabled/);
    },
);
await check(
    "native unavailable remains honest and no inspected evidence autoopens",
    async () => {
        const f = fixture();
        f.hooks.set("open", () =>
            status({
                phase: "failed",
                error: "NativeUnavailable",
                report_ready: false,
            }),
        );
        await f.c.open(RUN);
        const markup = render(f);
        assert.match(markup, /NativeUnavailable/);
        assert.match(button(markup, /Inspect/)[1], /\bdisabled/);
        assert.equal(generated(f).length, 0);
    },
);
await check(
    "cleanup View outside Lab exposes refresh/retry but no private run data",
    async () => {
        const f = fixture({ allowed: false });
        f.hooks.set("cleanup_status", () =>
            cleanup({ cleanup_required: true }),
        );
        await f.c.cleanupStatus();
        const markup = render(f, true);
        assert.match(markup, /cleanup/i);
        assert.doesNotMatch(
            button(
                markup,
                /(check|refresh).*cleanup|cleanup.*(check|refresh)/i,
            )[1],
            /\bdisabled/,
        );
        assert.doesNotMatch(
            button(markup, /retry.*cleanup|cleanup.*retry/i)[1],
            /\bdisabled/,
        );
        assert.ok(!markup.includes(RUN) && !markup.includes(CLIENT));
        assert.equal(generated(f).length, 0);
    },
);
await check(
    "last verified completed counts survive cleanup latch but inspection is disabled",
    async () => {
        const f = fixture();
        await f.c.open(RUN);
        f.hooks.set("status", () =>
            status({
                phase: "completed",
                completed: true,
                completed_scenes: 4,
            }),
        );
        await f.c.status();
        f.hooks.set("status", () =>
            status({
                phase: "cleanup_required",
                cleanup_required: true,
                report_ready: true,
                error: "Cleanup",
                cause: "Cleanup",
            }),
        );
        await f.c.status();
        const markup = render(f);
        assert.match(markup, /last verified/i);
        assert.match(markup, /4\s*\/\s*4/);
        assert.match(button(markup, /Inspect/)[1], /\bdisabled/);
    },
);

// Normative retirement observation clarification: these TWO additional cases
// leave the original83 case bodies/assertions above unchanged. A revoked
// presentation cannot promote its earlier preflight into current cleanup proof.
await check(
    "retired closed-running ACK observes actual generic work once before settling identity",
    async () => {
        const f = fixture(),
            gate = deferred();
        let reads = 0;
        f.hooks.set("cleanup_status", () =>
            ++reads === 1 ? cleanup() : gate.promise,
        );
        f.hooks.set("start", (q) => {
            const v = status({
                client_id: q.clientId,
                phase: "running",
                running: true,
                report_ready: false,
            });
            f.setCurrent(v);
            return v;
        });
        f.hooks.set("close", (q) =>
            status({
                client_id: f.calls.find((x) => x.action === "start").query
                    .clientId,
                run_token: q.runToken,
                phase: "closed",
                running: true,
                cleanup_required: false,
                cleanup_running: false,
                report_ready: false,
            }),
        );
        const work = f.c.start("paired", 1);
        await until(() => f.c.get().status?.running === true);
        const captured = f.c.get().clientId;
        f.c.setContext("retired-session-still-valid-window", false);
        let during;
        try {
            await until(
                () =>
                    f.calls.filter((x) => x.action === "cleanup_status")
                        .length === 2,
            );
            during = clone(f.c.get());
        } finally {
            // Always settle the synthetic gate and old operation, even on failure.
            gate.resolve(cleanup({ cleanup_required: false, running: true }));
            await work;
        }
        await until(
            () => f.c.get().cleanupPending === null && !f.c.get().uncertain,
        );
        assert.equal(during.status, null);
        assert.equal(during.clientId, null);
        assert.equal(during.cleanupPending, "status");
        assert.equal(during.uncertain, true);
        assert.deepEqual(
            f.c.get().cleanup,
            cleanup({ cleanup_required: false, running: true }),
        );
        assert.equal(f.c.get().cleanupUncertain, false);
        assert.equal(f.c.get().status, null);
        assert.equal(f.c.get().clientId, null);
        assert.deepEqual(actions(f), [
            "cleanup_status",
            "start",
            "close",
            "cleanup_status",
        ]);
        assert.deepEqual(f.calls.at(-1), {
            command: NATIVE,
            action: "cleanup_status",
            query: {},
        });
        assert.equal(generated(f).length, 1);
        assert.equal(
            f.calls.some((x) => x.action === "retry_cleanup"),
            false,
        );
        const markup = render(f, true);
        assert.match(markup, /cleanup/i);
        assert.ok(!markup.includes(RUN) && !markup.includes(captured));
    },
);
await check(
    "retired UnknownRun settles identity but failed one-shot observation retains global uncertainty",
    async () => {
        const f = fixture();
        let reads = 0;
        f.hooks.set("cleanup_status", () => {
            if (++reads === 1) return cleanup();
            throw Error("EvaluationIo");
        });
        f.hooks.set("start", (q) => {
            const v = status({
                client_id: q.clientId,
                phase: "running",
                running: true,
                report_ready: false,
            });
            f.setCurrent(v);
            return v;
        });
        f.hooks.set("close", () => {
            throw Error("UnknownEvaluationRun");
        });
        const work = f.c.start("paired", 1);
        await until(() => f.c.get().status?.running === true);
        f.c.setContext("retired-session-still-valid-window", false);
        await work;
        await until(
            () =>
                f.calls.filter((x) => x.action === "cleanup_status").length ===
                    2 && f.c.get().cleanupPending === null,
        );
        assert.equal(
            f.c.get().uncertain,
            false,
            "known revoked identity is separate from global proof",
        );
        assert.equal(f.c.get().cleanupUncertain, true);
        assert.equal(f.c.get().cleanupError, "EvaluationIo");
        assert.equal(f.c.get().status, null);
        assert.equal(f.c.get().clientId, null);
        if (f.c.get().cleanup !== null)
            assert.equal(
                f.c.get().cleanup.running,
                false,
                "keep actual old observation; never derive generic running from the retired run",
            );
        assert.deepEqual(actions(f), [
            "cleanup_status",
            "start",
            "close",
            "cleanup_status",
        ]);
        assert.equal(generated(f).length, 1);
        assert.equal(
            f.calls.some((x) => x.action === "retry_cleanup"),
            false,
        );
        const count = f.calls.length;
        await tick();
        assert.equal(
            f.calls.length,
            count,
            "no automatic cleanup retry or generation",
        );
    },
);
// TWO additional independent V2 wire-field boundary cases. These synthetic
// tuples are not claimed as observations of an actual native owner/process.
for (const flag of ["cleanup_required", "cleanup_running"])
    await check(
        `retired stopped-worker close ${flag} observes actual global payload once`,
        async () => {
            const f = fixture(),
                gate = deferred();
            let reads = 0;
            const observed =
                flag === "cleanup_required"
                    ? cleanup({ cleanup_required: false, running: true })
                    : cleanup({
                          cleanup_required: true,
                          running: false,
                          error: "Cleanup",
                      });
            f.hooks.set("cleanup_status", () =>
                ++reads === 1 ? cleanup() : gate.promise,
            );
            f.hooks.set("start", (q) => {
                const v = status({
                    client_id: q.clientId,
                    phase: "running",
                    running: true,
                    report_ready: false,
                });
                f.setCurrent(v);
                return v;
            });
            f.hooks.set("close", (q) =>
                status({
                    client_id: f.calls.find((x) => x.action === "start").query
                        .clientId,
                    run_token: q.runToken,
                    phase: "closed",
                    running: false,
                    report_ready: false,
                    cleanup_required: flag === "cleanup_required",
                    cleanup_running: flag === "cleanup_running",
                }),
            );
            const work = f.c.start("paired", 1);
            await until(() => f.c.get().status?.running === true);
            const captured = f.c.get().clientId;
            f.c.setContext("retired-session-still-valid-window", false);
            let during;
            try {
                await until(
                    () =>
                        f.calls.filter((x) => x.action === "cleanup_status")
                            .length === 2,
                );
                during = clone(f.c.get());
            } finally {
                gate.resolve(observed);
                await work;
            }
            await until(
                () => f.c.get().cleanupPending === null && !f.c.get().uncertain,
            );
            assert.equal(during.status, null);
            assert.equal(during.clientId, null);
            assert.equal(during.allowed, false);
            assert.equal(during.cleanupPending, "status");
            assert.equal(during.uncertain, true);
            if (during.cleanup !== null)
                assert.deepEqual(
                    during.cleanup,
                    cleanup(),
                    "pending read cannot invent a generic observation from the close flags",
                );
            assert.deepEqual(
                f.c.get().cleanup,
                observed,
                "only the actual fresh generic reply supplies its flags/error",
            );
            assert.equal(f.c.get().cleanupUncertain, false);
            assert.equal(f.c.get().status, null);
            assert.equal(f.c.get().clientId, null);
            assert.deepEqual(actions(f), [
                "cleanup_status",
                "start",
                "close",
                "cleanup_status",
            ]);
            assert.deepEqual(f.calls.at(-1), {
                command: NATIVE,
                action: "cleanup_status",
                query: {},
            });
            const markup = render(f, true);
            assert.match(markup, /cleanup/i);
            assert.ok(!markup.includes(RUN) && !markup.includes(captured));
            const count = f.calls.length;
            f.c.setContext("retired-session-still-valid-window", true);
            await f.c.start("paired", 1);
            assert.equal(
                f.calls.length,
                count,
                "actual observed cleanup blocker remains across eligibility change",
            );
            assert.equal(generated(f).length, 1);
            assert.equal(
                f.calls.some((x) => x.action === "retry_cleanup"),
                false,
            );
        },
    );
for (const c of controllers) c.dispose();
await tick();
const sourceHashes = Object.fromEntries(
    await Promise.all(
        [
            "ui/comparison-run-model.ts",
            "ui/comparison-run-controller.ts",
            "ui/comparison-run-view.tsx",
        ].map(async (name) => [
            name,
            createHash("sha256")
                .update(await readFile(path.join(root, name)))
                .digest("hex"),
        ]),
    ),
);
for (const [index, markup] of html.entries())
    await writeFile(path.join(output, `${prefix}-${index}.html`), markup, {
        flag: "wx",
    });
const result = {
    version: 1,
    evidence:
        "SYNTHETIC object-IPC mock + actual ComparisonRunController/native factory + React static HTML; no Rust/native IPC/WebView/pixels/model or cleanup proof",
    sourceHashes,
    checks: results.length,
    passed: results.filter((x) => x.passed).length,
    failed: results.filter((x) => !x.passed).length,
    cases: results,
    limitations: [
        "Missing native exports initially cause build refusal, not behavioral RED",
        "Oversize invalid-envelope negatives do not independently reach otherwise-valid closed DTO byte caps",
        "Static HTML checks labels/control states, not layout, handlers, DOM, native rendering or actual grants",
        "No installed model, native confirmation, asset/runtime owner or execution parity claim",
    ],
};
await writeFile(
    path.join(output, `${prefix}.json`),
    JSON.stringify(result, null, 2),
    { flag: "wx" },
);
console.log(JSON.stringify(result));
if (result.failed) process.exitCode = 1;

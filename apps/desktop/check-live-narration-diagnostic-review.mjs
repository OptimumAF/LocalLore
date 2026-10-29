// Independent FIRST SOURCE ONLY. Actual frontend codec/controller/React SSR;
// synthetic Gateway fixtures, not Host/Core/native IPC/pixels/model evidence.
import assert from "node:assert/strict";
import { build } from "esbuild";
import { mkdir, readFile, writeFile } from "node:fs/promises";
import { createHash, randomUUID, webcrypto } from "node:crypto";
import { fileURLToPath, pathToFileURL } from "node:url";
import path from "node:path";
import {
    baseRevision,
    originalTurn,
    originalAttempt,
    scope,
    clone,
    plain,
    decisionTuples,
    query,
    data,
    tick,
    readyController,
    syntheticHost,
    fence,
    comparisonFixture,
    readerEnvelope,
    readerToken,
    readerBinding,
    readerSource,
    readerRow,
} from "./live-narration-diagnostic-review-fixtures.mjs";

process.env.TEMP = "D:/Dev/_Temp";
process.env.TMP = "D:/Dev/_Temp";
globalThis.crypto ??= webcrypto;
assert.equal(process.argv.length, 2, "ClosedLiveDiagnosticArguments");
const root = fileURLToPath(new URL(".", import.meta.url));
const output =
    process.env.LOCALLORE_CHECK_OUTPUT_DIR ??
    path.join(root, "artifacts/checks");
for (const owned of [root, output])
    assert.equal(
        path.parse(path.resolve(owned)).root.toLowerCase(),
        "d:\\",
        "PhysicalDRequired",
    );
await mkdir(output, { recursive: true });
const prefix = `live-narration-first-${randomUUID()}`,
    setup = [],
    checks = [],
    authored = [],
    html = [];
const safe = (error) => String(error?.message ?? error).slice(0, 400);
const sourceFiles = [
    "ui/controller.ts",
    "ui/trace-model.ts",
    "ui/TurnDebugger.tsx",
    "ui/narration-diagnostic-model.ts",
    "ui/comparison-reader-model.ts",
    "ui/comparison-reader-controller.ts",
    "check-narration-diagnostic-reader-review.mjs",
    "check-trace-controller.mjs",
    "check-live-narration-diagnostic-review.mjs",
    "live-narration-diagnostic-review-fixtures.mjs",
];
async function hashes() {
    const result = {};
    for (const file of sourceFiles)
        try {
            result[file] = createHash("sha256")
                .update(await readFile(path.join(root, file)))
                .digest("hex");
        } catch (error) {
            if (error.code !== "ENOENT") throw error;
            result[file] = null;
        }
    return result;
}
const before = await hashes();
let m;
try {
    const built = await build({
        stdin: {
            contents: `
        export * from './ui/narration-diagnostic-model';
        export {Controller} from './ui/controller'; export {initialTrace,checkedTrace} from './ui/trace-model';
        export {TurnDebugger} from './ui/TurnDebugger';
        export {ComparisonReaderController} from './ui/comparison-reader-controller';
        export {checkedReaderNarrationDiagnosticV1,checkedReaderSource} from './ui/comparison-reader-model';
        export {createElement} from 'react'; export {renderToStaticMarkup} from 'react-dom/server';`,
            resolveDir: root,
            loader: "tsx",
        },
        bundle: true,
        platform: "node",
        format: "cjs",
        write: false,
        define: { __DEV_HARNESS__: "false" },
    });
    const file = path.join(output, `${prefix}.cjs`);
    await writeFile(file, built.outputFiles[0].contents, { flag: "wx" });
    m = (await import(pathToFileURL(file).href)).default;
    for (const name of [
        "checkedNarrationValidationDecisionV1",
        "checkedNarrationValidationDataV1",
        "Controller",
        "TurnDebugger",
        "ComparisonReaderController",
        "checkedReaderNarrationDiagnosticV1",
        "initialTrace",
        "checkedTrace",
    ])
        assert.equal(typeof m[name], "function", `MissingProposedAPI:${name}`);
    for (const name of [
        "readTraceNarrationValidation",
        "cancelTraceNarrationValidation",
        "traceNarrationValidationEligibility",
        "setTraceGameplayFence",
    ])
        assert.equal(
            typeof m.Controller.prototype[name],
            "function",
            `MissingControllerAPI:${name}`,
        );
    assert.deepEqual(plain(m.initialTrace().narrationValidation), {
        status: "idle",
        query: null,
        reply: null,
        error: null,
    });
} catch (error) {
    setup.push({
        stage: "proposed-api-build",
        error: safe(error),
        classification: "SETUP, not behavioral RED",
    });
}
async function test(name, run) {
    authored.push(name);
    if (setup.length) return;
    try {
        await run();
        checks.push({ name, passed: true });
    } catch (error) {
        checks.push({ name, passed: false, error: safe(error) });
    }
}
const diagnosticCalls = (host) =>
    host.calls.filter((q) => q.op === "trace_narration_validation_read_v1");
const gameplayCalls = (host) =>
    host.calls.filter((q) =>
        [
            "submit",
            "prepare",
            "commit",
            "cancel",
            "free_text",
            "turn_status",
        ].includes(q.op),
    );
const localReasons = [
    "disposed",
    "hidden",
    "not_story_lab",
    "not_omniscient",
    "source_unavailable",
    "fence_unavailable",
    "gameplay_unresolved",
    "busy",
    "trace_unavailable",
    "selection_unavailable",
    "context_changed",
];
function eligibility(c, reason = null) {
    const value = c.traceNarrationValidationEligibility();
    assert.deepEqual(Object.keys(value).sort(), ["allowed", "reason"]);
    assert.equal(typeof value.allowed, "boolean");
    assert(
        value.allowed
            ? value.reason === null
            : localReasons.includes(value.reason),
    );
    if (reason === null)
        assert.deepEqual(value, { allowed: true, reason: null });
    else assert.deepEqual(value, { allowed: false, reason });
    return value;
}
function idle(c, status = "idle") {
    assert.deepEqual(plain(c.get().trace.narrationValidation), {
        status,
        query: null,
        reply: null,
        error: null,
    });
}
async function withController(run, options) {
    const f = await readyController(m.Controller, options);
    try {
        await run(f);
    } finally {
        await f.close();
    }
}
function render(c, label) {
    const markup = m.renderToStaticMarkup(
        m.createElement(m.TurnDebugger, { controller: c, state: c.get() }),
    );
    html.push({ label, markup });
    return markup;
}

// 25 finite decisions are the complete accepted matrix, not inferred causes.
for (const [index, decision] of decisionTuples.entries())
    await test(`decision tuple ${index}`, () => {
        assert.deepEqual(
            plain(m.checkedNarrationValidationDecisionV1(decision)),
            decision,
        );
        assert.deepEqual(
            plain(
                m.checkedNarrationValidationDataV1(
                    data(query(), "recorded", decision),
                    query(),
                ),
            ),
            data(query(), "recorded", decision),
        );
        const wrapped = readerEnvelope(decision);
        assert.deepEqual(
            plain(
                m.checkedReaderNarrationDiagnosticV1(
                    wrapped,
                    readerToken,
                    readerSource,
                    readerRow,
                ),
            ),
            wrapped,
        );
    });
const badDecisions = [
    ["accepted error", { ...decisionTuples[0], error: "narration" }],
    ["accepted reason", { ...decisionTuples[0], reason: "unclassified" }],
    ["cancelled error", { ...decisionTuples[1], error: "stale" }],
    ["stale reason", { ...decisionTuples[2], reason: "unclassified" }],
    ["rejected missing reason", { ...decisionTuples[4], reason: null }],
    [
        "generic reason",
        {
            version: 1,
            outcome: "rejected",
            error: "agency",
            reason: "unclassified",
        },
    ],
    [
        "unknown category",
        { version: 1, outcome: "rejected", error: "future", reason: null },
    ],
    ["unknown reason", { ...decisionTuples[4], reason: "future" }],
    ["unsupported version", { ...decisionTuples[4], version: 2 }],
    ["unknown outcome", { ...decisionTuples[4], outcome: "committed" }],
    [
        "extra field",
        { ...decisionTuples[4], prose: "synthetic untrusted prose" },
    ],
    [
        "missing nullable field",
        { version: 1, outcome: "accepted", error: null },
    ],
];
for (const [name, value] of badDecisions)
    await test(`decision refuses ${name}`, () => {
        assert.throws(
            () => m.checkedNarrationValidationDecisionV1(value),
            /^Error: Wire$/,
        );
        assert.throws(
            () =>
                m.checkedReaderNarrationDiagnosticV1(
                    readerEnvelope(value),
                    readerToken,
                    readerSource,
                    readerRow,
                ),
            /ComparisonReaderWire/,
        );
    });
const badData = [
    [
        "extra field",
        (v) => {
            v.prompt = "synthetic private marker";
        },
    ],
    [
        "missing field",
        (v) => {
            delete v.generation_grant;
        },
    ],
    [
        "foreign session",
        (v) => {
            v.session = "foreign-session";
        },
    ],
    [
        "foreign story",
        (v) => {
            v.scope.story = "other-story";
        },
    ],
    [
        "foreign branch",
        (v) => {
            v.scope.branch = "other-branch";
        },
    ],
    [
        "scope extra",
        (v) => {
            v.scope.extra = true;
        },
    ],
    [
        "wrong current head",
        (v) => {
            v.head = 4;
        },
    ],
    [
        "wrong base",
        (v) => {
            v.base_revision = 5;
        },
    ],
    [
        "wrong turn",
        (v) => {
            v.turn = "later-turn";
        },
    ],
    [
        "wrong attempt",
        (v) => {
            v.attempt = 7;
        },
    ],
    [
        "unsafe head",
        (v) => {
            v.head = Number.MAX_SAFE_INTEGER + 1;
        },
    ],
    [
        "negative base",
        (v) => {
            v.base_revision = -1;
        },
    ],
    [
        "u32 overflow",
        (v) => {
            v.attempt = 0x1_0000_0000;
        },
    ],
    [
        "fractional attempt",
        (v) => {
            v.attempt = 2.5;
        },
    ],
    [
        "semantic observer vs actor id",
        (v) => {
            v.observer = "hero";
        },
    ],
    [
        "generation grant",
        (v) => {
            v.generation_grant = true;
        },
    ],
    [
        "version",
        (v) => {
            v.version = 2;
        },
    ],
    [
        "unknown status",
        (v) => {
            v.status = "missing";
        },
    ],
    [
        "missing recorded decision",
        (v) => {
            delete v.decision;
        },
    ],
    [
        "unavailable with decision",
        (v) => {
            v.status = "unavailable";
        },
    ],
];
for (const [name, mutate] of badData)
    await test(`data refuses ${name}`, () => {
        const value = data();
        mutate(value);
        assert.throws(
            () => m.checkedNarrationValidationDataV1(value, query()),
            /^Error: Wire$/,
        );
    });
await test("data native unavailable and u32 maximum remain exact closed values", () => {
    assert.deepEqual(
        plain(
            m.checkedNarrationValidationDataV1(
                data(query(), "unavailable"),
                query(),
            ),
        ),
        data(query(), "unavailable"),
    );
    const q = { ...query(), attempt: 0xffff_ffff };
    assert.deepEqual(
        plain(m.checkedNarrationValidationDataV1(data(q), q)),
        data(q),
    );
    assert.notEqual(q.expected_head, q.base_revision);
});
for (const kind of ["getter", "toJSON", "symbol", "custom prototype", "cycle"])
    await test(`descriptor refusal ${kind} invokes no getter`, () => {
        let invoked = 0;
        const value = data();
        if (kind === "getter")
            Object.defineProperty(value, "decision", {
                enumerable: true,
                get() {
                    invoked++;
                    return decisionTuples[4];
                },
            });
        if (kind === "toJSON")
            Object.defineProperty(value, "toJSON", {
                enumerable: true,
                get() {
                    invoked++;
                    return () => ({});
                },
            });
        if (kind === "symbol") value[Symbol("extra")] = "synthetic";
        if (kind === "custom prototype")
            Object.setPrototypeOf(value, { inherited: "synthetic" });
        if (kind === "cycle") value.decision = value;
        assert.throws(
            () => m.checkedNarrationValidationDataV1(value, query()),
            /^Error: Wire$/,
        );
        assert.equal(invoked, 0);
    });
await test("null-prototype data and oversized adversary are distinguished from native envelope proof", () => {
    const value = Object.assign(Object.create(null), data());
    assert.deepEqual(
        plain(m.checkedNarrationValidationDataV1(value, query())),
        data(),
    );
    const tooLarge = { ...data(), session: "x".repeat(4097) };
    assert.throws(
        () => m.checkedNarrationValidationDataV1(tooLarge, query()),
        /^Error: Wire$/,
    );
    // This also violates the ID bound: no isolated valid-4096-boundary claim.
});
await test("initial nested public state is idle without a top-level grant field", () => {
    const c = new m.Controller(syntheticHost().gateway);
    idle(c);
    assert(!Object.hasOwn(c.get(), "nativeGrant"));
    assert.deepEqual(plain(m.initialTrace().narrationValidation), {
        status: "idle",
        query: null,
        reply: null,
        error: null,
    });
});
await test("exact nonlatest selected read uses current head five and original base four", () =>
    withController(async ({ c, host }) => {
        eligibility(c);
        const beforeCalls = host.calls.length;
        const result = await c.readTraceNarrationValidation();
        assert.equal(result, undefined);
        const calls = host.calls.slice(beforeCalls);
        assert.deepEqual(calls, [query("live-session")]);
        const value = c.get().trace.narrationValidation;
        assert.equal(value.status, "recorded");
        assert.deepEqual(plain(value.query), query("live-session"));
        assert.equal(value.reply.turn, originalTurn);
        assert.equal(c.traceAttempt().identity.attempt, originalAttempt);
        assert.equal(gameplayCalls(host).length, 0);
        assert.equal(c.debugReceipt(), null);
        assert(
            Object.isFrozen(value.query) &&
                Object.isFrozen(value.query.scope) &&
                Object.isFrozen(value.reply) &&
                Object.isFrozen(value.reply.decision),
        );
    }));
await test("native unavailable retains exact query/data without guessing a cause", () =>
    withController(async ({ c, host }) => {
        host.queueDiagnostic(data(query("live-session"), "unavailable"));
        await c.readTraceNarrationValidation();
        const value = c.get().trace.narrationValidation;
        assert.equal(value.status, "unavailable");
        assert.equal(value.reply.status, "unavailable");
        assert.deepEqual(plain(value.query), query("live-session"));
        assert.equal(value.error, null);
        assert(!Object.hasOwn(value.reply, "decision"));
    }));
await test("stored live data is detached from the external Gateway reply alias", () =>
    withController(async ({ c, host }) => {
        const raw = data(query("live-session"));
        host.queueDiagnostic(raw);
        await c.readTraceNarrationValidation();
        const retained = c.get().trace.narrationValidation.reply;
        assert.notEqual(retained, raw);
        assert.notEqual(retained.scope, raw.scope);
        assert.notEqual(retained.decision, raw.decision);
        raw.scope.branch = "changed-external-alias";
        raw.decision.reason = "scene_unapproved_movement";
        assert.equal(retained.scope.branch, "main");
        assert.equal(retained.decision.reason, "scene_first_person");
    }));
for (const index of [1, 2])
    await test(`recorded ${decisionTuples[index].outcome} decision is not local cancellation`, () =>
        withController(async ({ c, host }) => {
            host.queueDiagnostic(
                data(query("live-session"), "recorded", decisionTuples[index]),
            );
            await c.readTraceNarrationValidation();
            assert.equal(c.get().trace.narrationValidation.status, "recorded");
            assert.equal(
                c.get().trace.narrationValidation.reply.decision.outcome,
                decisionTuples[index].outcome,
            );
        }));
for (const error of ["Forbidden", "Stale", "unrecognized-private-marker"])
    await test(`Host refusal ${error} is sanitized`, () =>
        withController(async ({ c, host }) => {
            host.queueDiagnostic(new Error(error));
            await c.readTraceNarrationValidation();
            const value = c.get().trace.narrationValidation;
            assert.equal(value.status, "refused");
            assert.equal(
                value.error,
                error === "unrecognized-private-marker" ? "Transport" : error,
            );
            assert.equal(value.reply, null);
            assert.deepEqual(plain(value.query), query("live-session"));
            assert(
                !JSON.stringify(value).includes("unrecognized-private-marker"),
            );
        }));
await test("malformed shared decision preserves distinct visible live and comparison controller errors", async () => {
    const live = await readyController(m.Controller),
        compared = await comparisonFixture(m);
    try {
        const bad = { ...decisionTuples[4], reason: null };
        live.host.queueDiagnostic(data(query("live-session"), "recorded", bad));
        await live.c.readTraceNarrationValidation();
        assert.equal(live.c.get().trace.narrationValidation.error, "Wire");
        compared.setReply(readerEnvelope(bad));
        await compared.c.inspectNarrationDiagnosticV1();
        assert.equal(compared.c.get().error, "ComparisonReaderWire");
        assert.deepEqual(compared.errors, ["ComparisonReaderWire"]);
    } finally {
        await live.close();
        await compared.close();
    }
});
await test("duplicate pending no-op preserves first latch and completion ignores only own busy", () =>
    withController(async ({ c, host }) => {
        const held = host.holdDiagnostic(),
            first = c.readTraceNarrationValidation();
        await held.entered.promise;
        const state = c.get(),
            pending = state.trace.narrationValidation;
        assert.equal(pending.status, "pending");
        assert.equal(pending.reply, null);
        assert.equal(pending.error, null);
        eligibility(c, "busy");
        const duplicate = c.readTraceNarrationValidation();
        assert.equal(c.get(), state);
        assert.equal(diagnosticCalls(host).length, 1);
        held.release.resolve(data(held.command));
        await first;
        await duplicate;
        assert.equal(c.get().trace.narrationValidation.status, "recorded");
        eligibility(c);
    }));
for (const late of ["success", "error"])
    await test(`local cancel observes late ${late} without native control`, () =>
        withController(async ({ c, host }) => {
            const held = host.holdDiagnostic(),
                reading = c.readTraceNarrationValidation();
            await held.entered.promise;
            const count = host.calls.length;
            assert.equal(c.cancelTraceNarrationValidation(), undefined);
            idle(c, "cancelled");
            const cancelled = c.get();
            assert.equal(c.cancelTraceNarrationValidation(), undefined);
            assert.equal(c.get(), cancelled);
            assert.equal(host.calls.length, count);
            assert.equal(gameplayCalls(host).length, 0);
            if (late === "success") held.release.resolve(data(held.command));
            else held.release.reject(Error("Forbidden"));
            await reading;
            idle(c, "cancelled");
            await c.readTraceNarrationValidation();
            assert.equal(diagnosticCalls(host).length, 2);
        }));
const invalidations = [
    ["observer", (f) => f.c.setObserver("mira")],
    ["view", (f) => f.c.returnToPlay()],
    ["selected attempt", (f) => f.c.selectTrace("later-turn:7")],
    ["basis", (f) => f.c.traceBasis(3)],
    ["trace close", (f) => f.c.showTrace(false)],
    ["trace refresh", (f) => f.c.readTrace()],
    ["trace disable", (f) => f.c.controlTrace("disable")],
    ["trace clear", (f) => f.c.controlTrace("clear")],
    ["fence absent", (f) => f.c.setTraceGameplayFence(null)],
    [
        "fence pending",
        (f) => f.c.setTraceGameplayFence(fence(f.c, f.host, { pending: true })),
    ],
    [
        "fence uncertain",
        (f) =>
            f.c.setTraceGameplayFence(fence(f.c, f.host, { uncertain: true })),
    ],
    [
        "head refresh",
        (f) => {
            f.host.head = 6;
            return f.c.refresh();
        },
    ],
    [
        "session",
        (f) =>
            f.c.attach({
                id: "second-session",
                scope: { story: "other-story", branch: "main" },
                name: "Other",
                revision: 5,
            }),
    ],
    ["dispose", (f) => f.c.dispose()],
];
for (const [name, change] of invalidations)
    await test(`late success cannot refill after ${name}`, () =>
        withController(async (f) => {
            const held = f.host.holdDiagnostic(),
                reading = f.c.readTraceNarrationValidation();
            await held.entered.promise;
            const changing = change(f);
            idle(f.c); // Must clear synchronously, before an awaited invalidation finishes.
            held.release.resolve(data(held.command));
            await changing;
            await reading;
            idle(f.c);
            assert.equal(diagnosticCalls(f.host).length, 1);
        }));
for (const [name, change] of invalidations.filter(([name]) =>
    ["observer", "selected attempt", "fence absent", "dispose"].includes(name),
))
    await test(`synchronous pending subscriber retires before dispatch ${name}`, () =>
        withController(async (f) => {
            let fired = false,
                observed = null,
                changing;
            const release = f.c.subscribe(() => {
                if (
                    !fired &&
                    f.c.get().trace.narrationValidation.status === "pending"
                ) {
                    fired = true;
                    changing = change(f);
                    observed = plain(f.c.get().trace.narrationValidation);
                }
            });
            try {
                await f.c.readTraceNarrationValidation();
                await changing;
                assert(fired);
                assert.equal(observed.reply, null);
                assert.equal(diagnosticCalls(f.host).length, 0);
                idle(f.c);
            } finally {
                release();
            }
        }));
await test("changed idle fence notifies eligibility and equal detached fence is a no-op", () =>
    withController(async ({ c, host }) => {
        idle(c);
        let notifications = 0;
        const observed = [];
        const release = c.subscribe(() => {
            notifications++;
            observed.push(plain(c.traceNarrationValidationEligibility()));
        });
        try {
            const blocked = fence(c, host, { pending: true });
            c.setTraceGameplayFence(blocked);
            eligibility(c, "gameplay_unresolved");
            assert(notifications > 0);
            idle(c);
            assert.deepEqual(
                observed[0],
                { allowed: false, reason: "gameplay_unresolved" },
                "FenceAssignedBeforeNotification",
            );
            const count = notifications,
                state = c.get();
            c.setTraceGameplayFence(clone(blocked));
            assert.equal(notifications, count);
            assert.equal(c.get(), state);
            blocked.pending = false;
            eligibility(c, "gameplay_unresolved"); // Caller alias cannot unblock.
            c.setTraceGameplayFence(fence(c, host));
            eligibility(c);
            assert(notifications > count);
            assert.deepEqual(observed.at(-1), { allowed: true, reason: null });
            assert.equal(diagnosticCalls(host).length, 0);
        } finally {
            release();
        }
    }));
for (const [field, value] of [
    ["session", "foreign-session"],
    ["story", "other-story"],
    ["branch", "other-branch"],
    ["head", 6],
    ["player", "other-player"],
    ["pending", "false"],
    ["head", Number.MAX_SAFE_INTEGER + 1],
])
    await test(`foreign or malformed Main presentation fence ${field}:${String(value)}`, () =>
        withController(async ({ c, host }) => {
            await c.readTraceNarrationValidation();
            const count = diagnosticCalls(host).length;
            c.setTraceGameplayFence(fence(c, host, { [field]: value }));
            idle(c);
            eligibility(c, "fence_unavailable");
            await c.readTraceNarrationValidation();
            idle(c, "unavailable");
            assert.equal(diagnosticCalls(host).length, count);
        }));
await test("local cancel outside pending is a no-op and preserves recorded content", () =>
    withController(async ({ c, host }) => {
        const idleState = c.get();
        c.cancelTraceNarrationValidation();
        assert.equal(c.get(), idleState);
        await c.readTraceNarrationValidation();
        const recorded = c.get(),
            count = host.calls.length;
        c.cancelTraceNarrationValidation();
        assert.equal(c.get(), recorded);
        assert.equal(host.calls.length, count);
    }));
const reasonCases = [
    [
        "hidden",
        async (f) => {
            await f.c.showTrace(false);
        },
    ],
    [
        "not_story_lab",
        async (f) => {
            f.c.returnToPlay();
            await f.c.showTrace(true);
        },
    ],
    [
        "not_omniscient",
        async (f) => {
            f.c.setObserver("player");
            await tick();
        },
    ],
    [
        "fence_unavailable",
        async (f) => {
            f.c.setTraceGameplayFence(null);
        },
    ],
    [
        "gameplay_unresolved",
        async (f) => {
            f.c.setTraceGameplayFence(fence(f.c, f.host, { uncertain: true }));
        },
    ],
    [
        "trace_unavailable",
        async (f) => {
            await f.c.controlTrace("disable");
        },
    ],
    [
        "selection_unavailable",
        async (f) => {
            f.host.setEmptyTrace(true);
            await f.c.readTrace();
        },
    ],
];
for (const [reason, prepare] of reasonCases)
    await test(`eligibility local reason ${reason} does not dispatch or invent query`, () =>
        withController(async (f) => {
            await prepare(f);
            eligibility(f.c, reason);
            const count = f.host.calls.length;
            await f.c.readTraceNarrationValidation();
            idle(f.c, "unavailable");
            assert.equal(f.host.calls.length, count);
        }));
await test("eligibility priority disposed then hidden then view then source", async () => {
    const host = syntheticHost(),
        c = new m.Controller(host.gateway);
    eligibility(c, "hidden");
    c.requestLab();
    c.acknowledgeLab(true);
    await c.showTrace(true);
    eligibility(c, "source_unavailable");
    c.returnToPlay();
    eligibility(c, "not_story_lab");
    await c.showTrace(false);
    eligibility(c, "hidden");
    await c.dispose();
    eligibility(c, "disposed");
    assert.equal(diagnosticCalls(host).length, 0);
});
await test("real metadata busy precedes absent trace without a broad completion bypass", () =>
    withController(async ({ c, host }) => {
        const held = host.holdTrace(),
            refreshing = c.readTrace();
        await held.entered.promise;
        eligibility(c, "busy");
        const count = diagnosticCalls(host).length;
        await c.readTraceNarrationValidation();
        assert.equal(diagnosticCalls(host).length, count);
        held.release.resolve();
        await refreshing;
    }));
await test("real trace control busy blocks a diagnostic without changing its own native controls", () =>
    withController(async ({ c, host }) => {
        const held = host.holdConfigure(),
            configuring = c.controlTrace("enable");
        await held.entered.promise;
        eligibility(c, "busy");
        const count = host.calls.length;
        await c.readTraceNarrationValidation();
        assert.equal(host.calls.length, count);
        assert.equal(c.get().trace.narrationValidation.query, null);
        held.release.resolve();
        await configuring;
    }));
await test("parameterless eligibility is a pure derived UI read", () =>
    withController(async ({ c, host }) => {
        const state = c.get(),
            count = host.calls.length;
        for (let index = 0; index < 3; index++) eligibility(c);
        assert.equal(c.get(), state);
        assert.equal(host.calls.length, count);
    }));
await test("external trace alias mutation cannot redirect a selected live read", () =>
    withController(async ({ c, host }) => {
        const external = host.lastTrace;
        try {
            external.scope.branch = "foreign-transport-alias";
        } catch (error) {
            assert(error instanceof TypeError);
        }
        const propagated =
            c.get().trace.reply?.scope.branch === "foreign-transport-alias";
        const eligible = c.traceNarrationValidationEligibility();
        if (propagated)
            assert.equal(
                eligible.allowed,
                false,
                "AliasedForeignCheckedReplyMustNotRemainEligible",
            );
        await c.readTraceNarrationValidation();
        for (const sent of diagnosticCalls(host))
            assert.deepEqual(sent, query("live-session"));
        if (propagated) assert.equal(diagnosticCalls(host).length, 0);
        if (!eligible.allowed)
            assert(
                ["trace_unavailable", "context_changed"].includes(
                    eligible.reason,
                ),
            );
        // A detached/frozen old trace is equally safe. Do not require alias mutability
        // or seed private State to force an otherwise unreachable isolated reason.
    }));
for (const [name, value] of [
    ["recorded", data()],
    ["unavailable", data(query(), "unavailable")],
])
    await test(`real Panel SSR ${name} shows local tuple and no canonical promotion`, () =>
        withController(async ({ c, host }) => {
            host.queueDiagnostic({ ...clone(value), session: "live-session" });
            await c.readTraceNarrationValidation();
            const count = host.calls.length,
                markup = render(c, name);
            for (const text of [
                scope.story,
                scope.branch,
                originalTurn,
                String(originalAttempt),
            ])
                assert(markup.includes(text));
            assert(/base|basis/i.test(markup) && /head/i.test(markup));
            assert(markup.includes("Read selected narration validation"));
            const text = markup.replace(/<[^>]+>/g, " ");
            assert(
                /head\s*r?\s*5/i.test(text) &&
                    /(?:base|basis)\s*r?\s*4/i.test(text),
            );
            if (name === "recorded")
                assert(
                    markup.includes("scene_first_person"),
                    "ActualFiniteDecisionCodeVisible",
                );
            assert(/quality|final commit|canonical/i.test(markup));
            assert.equal(host.calls.length, count);
            c.setObserver("mira");
            const actor = render(c, `${name}-actor`);
            assert(!actor.includes("scene_first_person"));
            assert.equal(c.get().trace.narrationValidation.reply, null);
        }));
await test("real Panel SSR pending local cancel and native refusal remain distinct", () =>
    withController(async ({ c, host }) => {
        const held = host.holdDiagnostic(),
            reading = c.readTraceNarrationValidation();
        await held.entered.promise;
        assert(/pending|reading/i.test(render(c, "pending")));
        c.cancelTraceNarrationValidation();
        assert(/cancel/i.test(render(c, "local-cancel")));
        held.release.resolve(data(held.command));
        await reading;
        host.queueDiagnostic(Error("Forbidden"));
        await c.readTraceNarrationValidation();
        assert(/Forbidden/.test(render(c, "refused")));
        assert.equal(c.get().trace.narrationValidation.status, "refused");
    }));
await test("nonliteral Domain2 player supports metadata only and never legacy inspection or receipt", () =>
    withController(
        async ({ c, host }) => {
            assert.equal(c.get().play, null);
            assert.equal(c.get().playV2.domain_version, 2);
            assert.equal(c.traceAttempt().identity.observer, "hero");
            eligibility(c);
            await c.readTraceNarrationValidation();
            assert.deepEqual(diagnosticCalls(host), [query("live-session")]);
            assert.equal(
                c.get().trace.narrationValidation.reply.observer,
                "player",
            );
            assert.equal(c.debugReceipt(), null);
            const count = host.calls.length;
            const markup = render(c, "thin-domain2");
            assert(markup.includes("hero"));
            assert(/unavailable/i.test(markup));
            assert.equal(host.calls.length, count);
            assert(!host.calls.some((q) => q.op === "inspect"));
            assert.equal(gameplayCalls(host).length, 0);
        },
        { domain: 2, player: "hero", thin: true },
    ));

assert.deepEqual(await hashes(), before, "SourceAndOldOraclesUnchanged");
for (const [index, entry] of html.entries())
    await writeFile(
        path.join(output, `${prefix}-${index}.html`),
        entry.markup,
        { flag: "wx" },
    );
const report = {
    version: 1,
    kind: "live_narration_diagnostic_first_v1",
    authored: authored.length,
    setup,
    checks,
    passed: checks.filter((v) => v.passed).length,
    failed: checks.filter((v) => !v.passed).length,
    sourceHashes: before,
    html: html.map((v, index) => ({
        label: v.label,
        file: `${prefix}-${index}.html`,
    })),
    nativeIpc: false,
    modelExecution: false,
    rendering: "actual React static HTML with synthetic Gateway",
    limits: [
        "4096 frontend DATA check is not an independent Rust TOTAL-envelope measurement",
        "Oversize control also violates ID bounds; no isolated valid 4096 overflow claim",
        "context_changed may remain unisolated because public lifecycle clears first; alias prevention is accepted",
        "No Host/Core, native WebView, pixels, model, SDK/device/desktop or new OS-probe evidence",
    ],
};
await writeFile(
    path.join(output, `${prefix}.json`),
    JSON.stringify(report, null, 2),
    { flag: "wx" },
);
console.log(JSON.stringify(report));
if (setup.length || report.failed) process.exitCode = 1;

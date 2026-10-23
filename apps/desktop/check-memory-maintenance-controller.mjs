// MOCK native transport, actual controller/strict decoder and inert React markup.
// No native IPC, SQLite, model, WebView or desktop execution is claimed here.
import assert from "node:assert/strict";
import { build } from "esbuild";
import { mkdir, writeFile } from "node:fs/promises";
import { randomUUID } from "node:crypto";
import { fileURLToPath, pathToFileURL } from "node:url";
import path from "node:path";
const directory =
    process.env.LOCALLORE_CHECK_OUTPUT_DIR ??
    fileURLToPath(new URL("artifacts/checks/", import.meta.url));
await mkdir(directory, { recursive: true });
const compiled = await build({
    stdin: {
        contents:
            'export * from "./ui/memory-maintenance-controller"; export {MemoryMaintenancePanel} from "./ui/MemoryMaintenancePanel"; export {createElement} from "react"; export {renderToStaticMarkup} from "react-dom/server";',
        resolveDir: fileURLToPath(new URL(".", import.meta.url)),
        loader: "ts",
    },
    banner: {
        js: 'import {createRequire} from "node:module"; const require=createRequire(import.meta.url);',
    },
    bundle: true,
    platform: "node",
    format: "esm",
    write: false,
    jsx: "automatic",
});
const target = path.join(
    directory,
    `memory-maintenance-controller-${randomUUID()}.mjs`,
);
await writeFile(target, compiled.outputFiles[0].contents);
const {
    MemoryMaintenanceController: Controller,
    decodeMemoryOperation: decode,
    memoryContextIdentity,
    MemoryMaintenancePanel,
    createElement,
    renderToStaticMarkup,
} = await import(pathToFileURL(target).href);
const checks = [];
const check = (value, label) => {
    assert(value, label);
    checks.push(label);
};
const context = (extra = {}) => ({
    session: "session-1",
    scope: { story: "memory-controls-synthetic", branch: "main" },
    expected_head: 4,
    player: "imported-hero",
    observer: "imported-hero",
    view: "lab",
    epoch: 1,
    persistent: true,
    ...extra,
});
const job = (status = "ready", extra = {}) => ({
    status,
    basis_revision: 4,
    next_from: status === "complete" ? 4 : 0,
    generation: 1,
    last_error: null,
    ...extra,
});
const result = (c, action, j = null) => ({
    version: 1,
    kind: "memory_maintenance",
    session: c.session,
    scope: { ...c.scope },
    expected_head: c.expected_head,
    action,
    maintenance: {
        version: 1,
        scope: { ...c.scope },
        head: c.expected_head,
        action,
        job: j,
    },
});
const done = (c, action, j = null, id = 1) => ({
    version: 1,
    operation_id: id,
    running: false,
    phase: "completed",
    error: null,
    result: result(c, action, j),
});
const running = (id) => ({
    version: 1,
    operation_id: id,
    running: true,
    phase: "memory_maintenance",
    error: null,
    result: null,
});
const failed = (error) => ({
    version: 1,
    operation_id: 1,
    running: false,
    phase: "error",
    error,
    result: null,
});
function transport() {
    const queue = [],
        calls = [];
    return {
        queue,
        calls,
        invoke: async (name, args) => {
            calls.push({ name, args });
            assert(queue.length, `unexpected ${name}`);
            const value = queue.shift();
            return typeof value === "function"
                ? await value(name, args)
                : value;
        },
    };
}
const c = context();
{
    const t = transport(),
        controller = new Controller(t.invoke);
    controller.contextChanged(c);
    check(
        !controller.can("admit"),
        "admission waits for explicit passive status",
    );
    t.queue.push(done(c, "status"));
    await controller.act("status");
    check(
        t.calls[0].args.request.action === "status" && t.calls.length === 1,
        "passive status only, no admission side effect",
    );
    await controller.act("admit");
    check(t.calls.length === 1, "admission requires consent");
    controller.consent(true);
    t.queue.push(done(c, "admit", job()));
    await controller.act("admit");
    check(
        controller.get().reply.maintenance.job.status === "ready" &&
            !controller.get().consent,
        "explicit admit observed and consent reset",
    );
    check(
        controller.can("step") && !controller.can("prune"),
        "ready allows one step and refuses active prune",
    );
    t.queue.push(running(22));
    await controller.act("step");
    check(
        t.calls.length === 3 && !controller.can("step"),
        "one step never loops or resubmits automatically",
    );
    t.queue.push(running(22));
    await controller.stop();
    check(
        t.calls.at(-1).name === "archive_cancel" &&
            controller.get().operation.running,
        "stop uses existing broker and does not invent terminal cancellation",
    );
    check(
        controller.get().notice.includes("not rollback"),
        "stop acknowledgement does not claim rollback",
    );
    t.queue.push(done(c, "step", job("complete"), 22));
    await controller.act("status");
    check(
        t.calls.at(-1).name === "archive_status" &&
            controller.get().reply.maintenance.job.status === "complete",
        "status recovers actual completed step despite cancellation request",
    );
    const before = t.calls.length;
    await controller.act("prune");
    check(t.calls.length === before, "terminal prune requires new consent");
    controller.consent(true);
    t.queue.push(done(c, "prune"));
    await controller.act("prune");
    check(
        controller.get().reply.maintenance.job === null &&
            !controller.can("admit"),
        "prune does not silently restart job or retain consent",
    );
    check(
        t.calls.every((x) => x.name !== "host_call") &&
            t.calls.filter((x) => x.args?.request?.action === "step").length ===
                1,
        "closed commands and exactly one step admission",
    );
    check(
        t.calls
            .filter((x) => x.args?.request)
            .every(
                (x) =>
                    Object.keys(x.args.request).sort().join(",") ===
                    "action,expected_head,scope,session",
            ),
        "wire never sends player observer grant or capabilities",
    );
}
{
    const t = transport(),
        controller = new Controller(t.invoke);
    controller.contextChanged(c);
    t.queue.push(done(c, "status"));
    await controller.act("status");
    controller.consent(true);
    t.queue.push(() => {
        throw Error("Transport");
    });
    await controller.act("admit");
    check(
        controller.get().uncertain && controller.get().operation === null,
        "lost start acknowledgement has unknown operation identity",
    );
    check(
        ["admit", "step", "cancel", "prune"].every((a) => !controller.can(a)),
        "unknown acknowledgement permits no mutation retries",
    );
    t.queue.push(() => {
        throw Error("ArchiveBusy");
    });
    await controller.act("status");
    check(
        controller.get().error === "ArchiveBusy" && controller.get().uncertain,
        "unknown prior worker remains honestly busy",
    );
    t.queue.push(done(c, "status", job(), 3));
    await controller.act("status");
    check(
        !controller.get().uncertain &&
            controller.get().reply.action === "status",
        "explicit passive status recovers actual persisted progress",
    );
    check(
        t.calls.filter((x) => x.args?.request?.action === "admit").length === 1,
        "lost admission never resubmitted",
    );
}
{
    const t = transport(),
        controller = new Controller(t.invoke);
    controller.contextChanged(c);
    t.queue.push(done(c, "status", job()));
    await controller.act("status");
    t.queue.push(running(31));
    await controller.act("step");
    t.queue.push(() => {
        throw Error("Transport");
    });
    await controller.act("status");
    t.queue.push(
        done(c, "step", job("ready", { next_from: 2, generation: 2 }), 31),
    );
    await controller.act("status");
    check(
        t.calls
            .slice(-2)
            .every(
                (x) => x.name === "archive_status" && x.args.operationId === 31,
            ),
        "lost poll acknowledgement recovers same broker identity",
    );
    check(
        controller.get().reply.maintenance.job.next_from === 2,
        "partial one-chunk progress remains visible without further step",
    );
    t.queue.push(done(c, "status", job("cancelled"), 32));
    await controller.act("status");
    check(
        !controller.can("admit") && !controller.can("step"),
        "cancelled job requires explicit prune before readmission",
    );
}
{
    let release;
    const t = transport(),
        controller = new Controller(t.invoke);
    controller.contextChanged(c);
    t.queue.push(
        () =>
            new Promise((resolve) => {
                release = resolve;
            }),
    );
    const pending = controller.act("status");
    controller.contextChanged(context({ session: "session-2", epoch: 2 }));
    t.queue.push(running(77));
    release(running(77));
    await pending;
    await Promise.resolve();
    check(
        controller.get().reply === null &&
            controller.get().context.session === "session-2",
        "late context response cannot populate new session",
    );
    check(
        t.calls.at(-1).name === "archive_cancel" &&
            t.calls.at(-1).args.operationId === 77,
        "late admitted operation is cancelled by its original owned identity",
    );
    controller.dispose();
    check(
        !controller.can("status"),
        "disposed controller cannot read or mutate",
    );
}
{
    const t = transport(),
        controller = new Controller(t.invoke);
    controller.contextChanged(c);
    t.queue.push(running(80));
    await controller.act("status");
    t.queue.push(running(80));
    controller.contextChanged(context({ observer: "mira", epoch: 2 }));
    await Promise.resolve();
    check(
        t.calls.at(-1).name === "archive_cancel" && !controller.can("status"),
        "observer change cancels known operation and disables NPC maintenance",
    );
    check(
        controller.get().reply === null && !controller.get().consent,
        "observer change clears prior private metadata and consent",
    );
    controller.contextChanged(
        context({
            player: "other-imported-player",
            observer: "other-imported-player",
            epoch: 3,
        }),
    );
    check(
        controller.can("status"),
        "imported actual player identity allowed without hardcoded player actorID",
    );
    controller.contextChanged(
        context({ view: "play", observer: "player", epoch: 4 }),
    );
    check(
        controller.can("status"),
        "explicit Play lens uses actual seed player natively",
    );
    controller.contextChanged(context({ persistent: false, epoch: 5 }));
    check(
        !controller.can("status"),
        "in-memory sessions report maintenance unavailable",
    );
}
for (const changed of [
    context({ expected_head: 5 }),
    context({ scope: { ...c.scope, branch: "child" } }),
    context({ player: "other-player" }),
    context({ view: "play" }),
    context({ epoch: 2 }),
]) {
    let release;
    const t = transport(),
        controller = new Controller(t.invoke);
    controller.contextChanged(c);
    t.queue.push(
        () =>
            new Promise((resolve) => {
                release = resolve;
            }),
    );
    const pending = controller.act("status");
    controller.contextChanged(changed);
    release(done(c, "status", job()));
    await pending;
    check(
        controller.get().reply === null && !controller.get().busy,
        "held reply suppressed for changed " + memoryContextIdentity(changed),
    );
}
for (const [label, mutate] of [
    [
        "unknown top field",
        (v) => {
            v.grant = true;
        },
    ],
    [
        "unknown result field",
        (v) => {
            v.result.observer = "omniscient";
        },
    ],
    [
        "wrong selected story",
        (v) => {
            v.result.scope.story = "foreign";
        },
    ],
    [
        "wrong session",
        (v) => {
            v.result.session = "session-2";
        },
    ],
    [
        "wrong revision",
        (v) => {
            v.result.expected_head = 5;
        },
    ],
    [
        "wrong action",
        (v) => {
            v.result.action = "step";
        },
    ],
    [
        "inner action mismatch",
        (v) => {
            v.result.maintenance.action = "prune";
        },
    ],
    [
        "foreign kind",
        (v) => {
            v.result.kind = "archive";
        },
    ],
    [
        "unsafe generation",
        (v) => {
            v.result.maintenance.job.generation = Number.MAX_SAFE_INTEGER + 1;
        },
    ],
    [
        "invalid complete cursor",
        (v) => {
            v.result.maintenance.job.status = "complete";
        },
    ],
    [
        "blocked missing cause",
        (v) => {
            v.result.maintenance.job.status = "blocked";
        },
    ],
    [
        "ready historical cause",
        (v) => {
            v.result.maintenance.job.last_error = "budget";
        },
    ],
    [
        "unexpected running result",
        (v) => {
            v.running = true;
        },
    ],
    [
        "unknown error",
        (v) => {
            v.error = "raw private path";
        },
    ],
    [
        "unknown job capability",
        (v) => {
            v.result.maintenance.job.job_id = 1;
        },
    ],
    [
        "oversized material",
        (v) => {
            v.result.session = "x".repeat(4096);
        },
    ],
]) {
    const v = done(c, "status", job());
    mutate(v);
    assert.throws(() => decode(v, c, "status"), /Wire/);
    checks.push(`strict decoder: ${label}`);
}
{
    const v = done(c, "status", job("stale", { last_error: "budget" }));
    check(
        decode(v, c, "status").result.maintenance.job.last_error === "budget",
        "passive stale preserves historical closed failure category",
    );
    assert.throws(() => decode(done(c, "status"), c, "status", 900), /Wire/);
    checks.push("strict broker operation identity");
    const v2 = done(c, "status", job());
    const detached = decode(v2, c, "status");
    v2.result.scope.story = "foreign";
    check(
        detached.result.scope.story === c.scope.story,
        "decoded reply detached from transport aliases",
    );
    assert.throws(() => memoryContextIdentity({ ...c, grant: true }), /Wire/);
    checks.push("unknown context grant refused");
    check(
        memoryContextIdentity(c) !==
            memoryContextIdentity(context({ view: "play" })),
        "view is part of context identity",
    );
    check(
        memoryContextIdentity(c) !==
            memoryContextIdentity(context({ epoch: 2 })),
        "selection epoch is part of context identity",
    );
    const t = transport(),
        controller = new Controller(t.invoke);
    controller.contextChanged(c);
    t.queue.push(failed("Unsupported"));
    await controller.act("status");
    check(
        controller.get().error === "Unsupported" && !controller.can("admit"),
        "unsupported is visible and never presented as no-job success",
    );
    const markup = renderToStaticMarkup(
        createElement(MemoryMaintenancePanel, {
            maintenance: controller,
            context: c,
        }),
    );
    check(
        markup.includes("Derived memory") &&
            markup.includes("memory-controls-synthetic") &&
            markup.includes("imported-hero"),
        "headless semantic panel orients selected story and actual player",
    );
    check(
        markup.includes('role="alert"') &&
            markup.includes("Unsupported") &&
            markup.includes("Model-generated summaries are unavailable"),
        "headless panel exposes error and unavailable feature honestly",
    );
    const other = context({ epoch: 2 });
    check(
        renderToStaticMarkup(
            createElement(MemoryMaintenancePanel, {
                maintenance: controller,
                context: other,
            }),
        ) === "",
        "stale panel cannot render old context metadata",
    );
}
await writeFile(
    path.join(directory, "memory-maintenance-mock-summary.json"),
    JSON.stringify(
        {
            kind: "mock-transport-and-headless-semantic",
            native: false,
            model: false,
            checks,
        },
        null,
        2,
    ),
);
console.log(
    `PASS: ${checks.length} MOCK transport/controller/decoder/headless checks. No native or model execution.`,
);

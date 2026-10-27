// Frozen source-only behavioral oracle. Actual Controller/View + SYNTHETIC
// native-shaped replies/React static HTML. No accessor assumption, IPC or model.
// Run from apps/desktop: node check-selected-source-freshness-review.mjs
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
const prefix = `selected-source-freshness-${randomUUID()}`;
const built = await build({
    stdin: {
        contents:
            'export {SelectedEvaluationController} from "./ui/selected-evaluation-controller";export {SelectedEvaluationView} from "./ui/selected-evaluation-view";export {createElement} from "react";export {renderToStaticMarkup} from "react-dom/server";',
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
const clone = (value) => structuredClone(value),
    hash = "a".repeat(64);
const source = {
    readerClientId: "11111111-1111-1111-1111-111111111111",
    runToken: "22222222-2222-2222-2222-222222222222",
    binding: hash,
};
const fresh = { ...source, runToken: "33333333-3333-3333-3333-333333333333" };
const readToken = "44444444-4444-4444-4444-444444444444",
    runId = "55555555-5555-5555-5555-555555555555",
    planToken = "66666666-6666-6666-6666-666666666666";
const row = { turn: "synthetic-move-4", arm: "left" },
    selection = { turn: row.turn, clicked_arm: row.arm, index: 4 },
    scope = { story: "synthetic-selected", branch: "main" };
const omni = { kind: "omniscient" },
    player = { kind: "player" };
const descriptors = [
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
function prepared(version) {
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
        ...(version === 2
            ? { source_protocol_version: 3, constructions: clone(descriptors) }
            : {}),
    };
}
function status(client, version, phase = "completed", reading = true) {
    const closed = phase === "closed",
        isPrepared = phase === "prepared";
    return {
        version: 1,
        kind: "selected_evaluation",
        client_id: client,
        operation_id: closed ? null : isPrepared ? 1 : reading ? 3 : 2,
        phase,
        running: false,
        lane: closed ? null : "scripted_baseline",
        plan_token: closed ? null : planToken,
        run_id: closed || isPrepared ? null : runId,
        run_token: !closed && !isPrepared && reading ? readToken : null,
        binding: !closed && !isPrepared && reading ? hash : null,
        prepared: closed ? null : prepared(version),
        error: null,
        cause: null,
        cleanup_required: false,
    };
}
function fixture(version) {
    const calls = [],
        events = [],
        hooks = new Map();
    let current,
        cleanup = false;
    const c = new m.SelectedEvaluationController(async (command, args) => {
        assert.equal(command, "evaluation_selected");
        assert.deepEqual(Object.keys(args).sort(), ["action", "request"]);
        assert.ok(Buffer.byteLength(args.request) <= 4096);
        const body = JSON.parse(args.request),
            action = args.action;
        calls.push({ action, body });
        events.push(`invoke:${action}`);
        if (hooks.has(action)) return hooks.get(action)(body);
        if (action === "prepare")
            return (current = status(
                body.clientId,
                version,
                "prepared",
                false,
            ));
        if (action === "start")
            return (current = status(
                body.clientId,
                version,
                "completed",
                false,
            ));
        if (action === "open" || action === "resume")
            return (current = status(body.clientId, version));
        if (action === "status")
            return current ?? status(body.clientId, version);
        if (action === "close")
            return status(body.clientId, version, "closed", false);
        if (action === "cleanup_status")
            return {
                version: 1,
                kind: "selected_cleanup",
                cleanup_required: cleanup,
                running: false,
                error: null,
            };
        throw new Error(`unexpected synthetic action ${action}`);
    });
    controllers.add(c);
    c.setContext("synthetic-context", true);
    c.setObserver(omni);
    return {
        c,
        calls,
        events,
        hooks,
        setCurrent: (value) => {
            current = value;
        },
        setCleanup: (value) => {
            cleanup = value;
        },
    };
}
function render(f, linked = source, observer = f.c.get().observer) {
    return m.renderToStaticMarkup(
        m.createElement(m.SelectedEvaluationView, {
            controller: f.c,
            source: clone(linked),
            row: clone(row),
            observer: clone(observer),
        }),
    );
}
function disabled(html, label) {
    const buttons = [
        ...html.matchAll(/<button\b([^>]*)>([\s\S]*?)<\/button>/g),
    ];
    const found = buttons.find(
        (match) =>
            match[2]
                .replace(/<[^>]*>/g, "")
                .replace(/\s+/g, " ")
                .trim() === label,
    );
    assert.ok(found, `actual View button exists: ${label}`);
    return /\bdisabled(?:\s|=|$)/.test(found[1]);
}
const resumeLabel = "Resume / verify with linked source",
    prepareLabel = "Prepare selected case";
const hasRefreshHint = (html) =>
    html.includes("Choose the matching source report again before requesting");
async function openedAfterPrepare(f) {
    await f.c.prepare(clone(source), clone(row), "scripted_baseline");
    assert.equal(f.c.get().status?.phase, "prepared");
    await f.c.start();
    await f.c.open(runId);
    assert.equal(f.c.get().error, null);
    assert.equal(f.c.get().status?.run_token, readToken);
    assert.equal(f.c.get().busy, false);
}
const cases = [],
    controllers = new Set(),
    htmlSnapshots = [];
async function test(name, body) {
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
for (const version of [1, 2]) {
    await test(`v${version}: admitted prepare/completion/open hides stale Resume and Close cannot revive Prepare`, async () => {
        const f = fixture(version);
        await openedAfterPrepare(f);
        const html = render(f);
        htmlSnapshots.push(html);
        assert.equal(disabled(html, resumeLabel), true);
        assert.equal(hasRefreshHint(html), true);
        await f.c.close();
        assert.equal(f.c.get().clientId, null);
        assert.equal(disabled(render(f), prepareLabel), true);
    });
    await test(`v${version}: fresh reader token with same binding enables explicit Resume/Prepare without dispatch`, async () => {
        const f = fixture(version);
        await openedAfterPrepare(f);
        const count = f.calls.length,
            html = render(f, fresh);
        assert.equal(disabled(html, resumeLabel), false);
        assert.equal(hasRefreshHint(html), false);
        assert.equal(
            f.calls.length,
            count,
            "render must not auto-resume or re-pick",
        );
        await f.c.close();
        const closedCalls = f.calls.length;
        assert.equal(disabled(render(f, fresh), prepareLabel), false);
        assert.equal(f.calls.length, closedCalls);
    });
    await test(`v${version}: admitted Resume marks source before synchronous notification/native dispatch`, async () => {
        const f = fixture(version);
        await f.c.open(runId);
        assert.equal(
            disabled(render(f), resumeLabel),
            false,
            "cold open has not attempted this source",
        );
        let observed = false,
            notificationHint = false;
        const stop = f.c.subscribe(() => {
            if (!observed && f.c.get().pending?.action === "resume") {
                observed = true;
                notificationHint = hasRefreshHint(render(f));
                f.events.push("resume-notification");
            }
        });
        await f.c.resume(clone(source));
        stop();
        assert.equal(f.c.get().error, null);
        assert.equal(
            f.calls.filter((call) => call.action === "resume").length,
            1,
        );
        assert.equal(observed, true);
        assert.ok(
            f.events.indexOf("resume-notification") <
                f.events.indexOf("invoke:resume"),
        );
        assert.equal(
            notificationHint,
            true,
            "actual View observes attempted source before reentrant subscribers dispatch",
        );
        assert.equal(disabled(render(f), resumeLabel), true);
        assert.equal(hasRefreshHint(render(f)), true);
        assert.equal(disabled(render(f, fresh), resumeLabel), false);
    });
    await test(`v${version}: invalid or locally blocked Prepare does not mark an unused valid source`, async () => {
        const f = fixture(version);
        f.c.setContext("not-allowed", false);
        await f.c.prepare(clone(source), clone(row), "scripted_baseline");
        f.c.setContext("allowed-again", true);
        assert.equal(disabled(render(f), prepareLabel), false);
        await f.c.prepare(
            { ...source, runToken: "invalid" },
            clone(row),
            "scripted_baseline",
        );
        assert.equal(f.c.get().error, "SelectedEvaluationWire");
        // Existing wire-error uncertainty is separate from source freshness.
        // Retire that local context before observing this still-unused source.
        f.c.setContext("after-invalid-local-argument", true);
        assert.equal(disabled(render(f), prepareLabel), false);
        f.setCleanup(true);
        await f.c.cleanupStatus();
        await f.c.prepare(clone(source), clone(row), "scripted_baseline");
        assert.equal(
            f.calls.filter((call) => call.action === "prepare").length,
            0,
        );
        f.setCleanup(false);
        await f.c.cleanupStatus();
        assert.equal(disabled(render(f), prepareLabel), false);
    });
    await test(`v${version}: unknown ACK/status, lens, context and close/open preserve cached-source refresh requirement`, async () => {
        const f = fixture(version);
        f.hooks.set("prepare", (body) => {
            f.setCurrent(status(body.clientId, version, "prepared", false));
            throw new Error("EvaluationIo");
        });
        await f.c.prepare(clone(source), clone(row), "scripted_baseline");
        assert.equal(f.c.get().uncertain, true);
        const client = f.c.get().clientId;
        await f.c.status();
        assert.equal(f.c.get().clientId, client);
        assert.equal(f.c.get().status?.phase, "prepared");
        await f.c.start();
        await f.c.open(runId);
        const operation = f.c.get().status?.operation_id;
        f.c.setObserver(player);
        assert.equal(f.c.get().clientId, client);
        assert.equal(f.c.get().status?.operation_id, operation);
        assert.equal(disabled(render(f), resumeLabel), true);
        f.c.setContext("new-session-same-cached-reader-prop", true);
        await f.c.open(runId);
        assert.equal(f.c.get().error, null);
        assert.equal(disabled(render(f), resumeLabel), true);
        await f.c.close();
        await f.c.open(runId);
        const html = render(f);
        htmlSnapshots.push(html);
        assert.equal(disabled(html, resumeLabel), true);
        assert.equal(hasRefreshHint(html), true);
        assert.equal(disabled(render(f, fresh), resumeLabel), false);
        assert.equal(
            f.calls.filter((call) => call.action === "prepare").length,
            1,
        );
        assert.equal(
            f.calls.filter((call) => call.action === "resume").length,
            0,
        );
    });
}
for (const controller of controllers) controller.dispose();
const sourceHashes = Object.fromEntries(
    await Promise.all(
        [
            "ui/selected-evaluation-controller.ts",
            "ui/selected-evaluation-model.ts",
            "ui/selected-evaluation-view.tsx",
        ].map(async (name) => [
            name,
            createHash("sha256")
                .update(await readFile(path.join(root, name)))
                .digest("hex"),
        ]),
    ),
);
for (const [index, html] of htmlSnapshots.entries())
    await writeFile(path.join(output, `${prefix}-${index}.html`), html, {
        flag: "wx",
    });
const result = {
    version: 1,
    evidence:
        "SYNTHETIC native-shaped mock/actual controller/React static HTML; no Rust/native IPC/WebView/model",
    sourceHashes,
    groups: 5,
    checks: cases.length,
    passed: cases.filter((item) => item.passed).length,
    failed: cases.filter((item) => !item.passed).length,
    html: htmlSnapshots.length,
    cases,
};
await writeFile(
    path.join(output, `${prefix}.json`),
    JSON.stringify(result, null, 2),
    { flag: "wx" },
);
console.log(JSON.stringify(result));
if (result.failed) process.exitCode = 1;

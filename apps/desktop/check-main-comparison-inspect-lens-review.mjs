// Frozen before the independent reader-context Inspect fix. SOURCE UNRUN.
// Actual Main subscriptions, App callback and ComparisonReaderController;
// synthetic transport/capability metadata and React hooks only. No Rust,
// canonical receipt, native IPC, rendering, model or OS-dialog evidence.
import assert from "node:assert/strict";
import { mkdir, writeFile } from "node:fs/promises";
import { randomUUID } from "node:crypto";
import { fileURLToPath } from "node:url";
import path from "node:path";
import {
    using,
    appFixture,
    lab,
    nodes,
    ids,
    deferred,
    tick,
} from "./check-main-comparison-run-native.mjs";

// Importing the shared seam bundles actual source; its direct-entry guard does
// not execute the original twenty cases. No production predicates are copied.
const readerCommand = "evaluation_comparison";
const nativeCommand = "evaluation_comparison_native";
const readToken = "77777777-7777-4777-8777-777777777777";
const readBinding = "c".repeat(64);
const executionKeys = (main) => [
    main.comparisonRun.get().context,
    main.nativeComparisonRun.get().context,
];
function status(client, phase = "ready") {
    return {
        version: 1,
        kind: "comparison_reader",
        client_id: client,
        operation_id: 91,
        phase,
        running: false,
        run_token: phase === "ready" ? readToken : null,
        binding: phase === "ready" ? readBinding : null,
        error: null,
        read_only: true,
        execution_available: false,
    };
}
async function withReaderTransport(main, work) {
    const core = globalThis.window.__TAURI__.core;
    const previous = core.invoke;
    const calls = [],
        holds = [];
    let nextClose = null;
    core.invoke = async (command, args = {}) => {
        if (
            command !== readerCommand &&
            !(command === nativeCommand && args.action === "managed")
        )
            return previous(command, args);
        assert(calls.length < 48, "bounded fixed reader fixture");
        calls.push(structuredClone({ command, ...args }));
        const query = args.query;
        if (args.action === "close") {
            const held = nextClose;
            nextClose = null;
            if (held) {
                held.entered.resolve();
                await held.release.promise;
            }
            return status(query.clientId, "closed");
        }
        if (["pick", "managed", "status"].includes(args.action))
            return status(query.clientId);
        assert.equal(
            args.action,
            "source",
            "no synthetic private artifact read",
        );
        return {
            version: 1,
            kind: "comparison_reader",
            run_token: readToken,
            source: {
                binding: readBinding,
                protocol_version: 3,
                rows: [],
                read_only: true,
                execution_available: false,
            },
        };
    };
    try {
        await work({
            calls,
            holdClose() {
                assert.equal(nextClose, null);
                const held = { entered: deferred(), release: deferred() };
                nextClose = held;
                holds.push(held);
                return held;
            },
        });
    } finally {
        for (const held of holds) held.release.resolve();
        await main.comparison.close();
        await tick();
        core.invoke = previous;
    }
}
async function heldInspect(main, transport, mutate) {
    await lab(main);
    const app = appFixture(main, false, main.comparison);
    await app.change("approved_native");
    await main.comparison.pick();
    assert.equal(main.comparison.get().status.phase, "ready");
    assert.equal(main.comparison.get().status.run_token, readToken);
    const before = {
        execution: executionKeys(main),
        reader: main.comparison.get(),
    };
    const view = nodes(app.render()).find(
        (node) =>
            node.props?.controller === app.native &&
            typeof node.props?.onInspect === "function",
    );
    assert(view, "actual App native Inspect callback");
    const held = transport.holdClose();
    const pending = Promise.resolve(view.props.onInspect(ids.native));
    try {
        await tick();
        assert(
            transport.calls.some((call) => call.action === "close"),
            "actual reader close reached synthetic transport",
        );
        await held.entered.promise;
        await mutate({ main, app, before });
    } finally {
        held.release.resolve();
        await pending;
        await tick();
    }
    const managed = transport.calls.filter((call) => call.action === "managed");
    assert(
        !transport.calls.some((call) =>
            ["start", "resume"].includes(call.action),
        ),
        "no generation requested",
    );
    return { managed, before, app };
}
const cases = [];
async function test(name, run) {
    try {
        await using((main) =>
            withReaderTransport(main, (transport) => run(main, transport)),
        );
        cases.push({ name, passed: true });
    } catch (error) {
        cases.push({
            name,
            passed: false,
            error: String(error?.message ?? error).slice(0, 512),
        });
    }
}
await test("unchanged reader identity permits one captured native managed open", async (main, transport) => {
    const { managed } = await heldInspect(
        main,
        transport,
        async ({ before }) => {
            assert.equal(main.comparison.get().context, before.reader.context);
            assert.equal(main.comparison.get().allowed, true);
            assert.deepEqual(
                main.comparison.get().observer,
                before.reader.observer,
            );
        },
    );
    assert.equal(managed.length, 1);
    assert.equal(managed[0].command, nativeCommand);
    assert.equal(managed[0].query.runId, ids.native);
    assert.equal(main.comparison.get().status.phase, "ready");
});
for (const observer of ["mira", "sable"])
    await test(`held Inspect cannot reopen after actual Main observer ${observer} retirement`, async (main, transport) => {
        const { managed } = await heldInspect(
            main,
            transport,
            async ({ app, before }) => {
                main.controller.setObserver(observer);
                await tick();
                app.render();
                assert.deepEqual(
                    executionKeys(main),
                    before.execution,
                    "generation identity deliberately excludes observer",
                );
                assert.notEqual(
                    main.comparison.get().context,
                    before.reader.context,
                    "actual Main independently retires reader context",
                );
            },
        );
        assert.equal(
            managed.length,
            0,
            "old callback cannot reacquire retired reader",
        );
        assert.equal(main.comparison.get().source, null);
    });
await test("held Inspect cannot reopen after independent reader lens changes", async (main, transport) => {
    const { managed } = await heldInspect(
        main,
        transport,
        async ({ app, before }) => {
            main.comparison.setObserver({ kind: "character", id: "mira" });
            app.render();
            assert.equal(
                main.comparison.get().context,
                before.reader.context,
                "local reader lens is distinct from surrounding context",
            );
            assert.notDeepEqual(
                main.comparison.get().observer,
                before.reader.observer,
            );
            assert.deepEqual(executionKeys(main), before.execution);
        },
    );
    assert.equal(
        managed.length,
        0,
        "old callback cannot acquire under a new lens",
    );
    assert.equal(main.comparison.get().source, null);
});
await test("reader eligibility loss while close is held admits no new read", async (main, transport) => {
    const { managed } = await heldInspect(
        main,
        transport,
        async ({ app, before }) => {
            main.comparison.contextChanged(before.reader.context, false);
            app.render();
            assert.equal(main.comparison.get().allowed, false);
            assert.deepEqual(executionKeys(main), before.execution);
        },
    );
    assert.equal(managed.length, 0);
    assert.equal(main.comparison.get().source, null);
});
const report = {
    version: 1,
    synthetic: true,
    checks: cases,
    passed: cases.filter((row) => row.passed).length,
    failed: cases.filter((row) => !row.passed).length,
    nativeIpc: false,
    modelExecution: false,
    rendering: "none",
    limitations: [
        "actual Main/App/reader JavaScript with mocked transport and React hook values",
        "empty ReaderV1 source metadata is synthetic, not a Core/native report proof",
        "no native consent, Rust authority, pixels, model or timing acceptance",
    ],
};
const output =
    process.env.LOCALLORE_CHECK_OUTPUT_DIR ??
    fileURLToPath(new URL("./artifacts/checks", import.meta.url));
await mkdir(output, { recursive: true });
const json = JSON.stringify(report, null, 2);
assert(Buffer.byteLength(json) <= 128 * 1024);
await writeFile(
    path.join(output, `comparison-inspect-lens-${randomUUID()}.json`),
    json,
    { flag: "wx" },
);
console.log(JSON.stringify(report));
if (report.failed) process.exitCode = 1;

// Frozen SOURCE-ONLY integration review at 034905ca, before the panel fix.
// Actual panel callbacks + actual controller/decoder; synthetic transport only.
// React hooks/JSX are test values, not DOM, headless rendering or native evidence.
import assert from "node:assert/strict";
import { build } from "esbuild";
import { readFile } from "node:fs/promises";
import { createHash } from "node:crypto";
import { fileURLToPath } from "node:url";

const root = fileURLToPath(new URL("./", import.meta.url));
const files = [
    "ui/ComparisonReaderPanel.tsx",
    "ui/comparison-reader-controller.ts",
    "ui/comparison-reader-model.ts",
];
const hashes = Object.fromEntries(
    await Promise.all(
        files.map(async (file) => [
            file,
            createHash("sha256")
                .update(await readFile(new URL(file, import.meta.url)))
                .digest("hex"),
        ]),
    ),
);
const built = await build({
    stdin: {
        contents:
            'export { ComparisonReaderPanel } from "./ui/ComparisonReaderPanel"; export { ComparisonReaderController } from "./ui/comparison-reader-controller"; export { begin } from "react";',
        resolveDir: root,
        loader: "ts",
    },
    bundle: true,
    platform: "node",
    format: "esm",
    write: false,
    jsx: "automatic",
    plugins: [
        {
            name: "review-hook-values-only",
            setup(plugin) {
                plugin.onResolve(
                    { filter: /^react(?:\/jsx-runtime)?$/ },
                    ({ path }) => ({ path, namespace: "review-hooks" }),
                );
                plugin.onLoad(
                    { filter: /.*/, namespace: "review-hooks" },
                    ({ path }) => ({
                        loader: "js",
                        contents:
                            path === "react"
                                ? `let slots=[],i=0; export function begin(reset=false){i=0;if(reset)slots=[];}
                       export function useState(value){const n=i++;if(!(n in slots))slots[n]=value;
                         return [slots[n],v=>{slots[n]=typeof v==='function'?v(slots[n]):v;}];}
                       export const useCallback=f=>f; export const useSyncExternalStore=(s,g)=>g();`
                                : `export const jsx=(type,props)=>({type,props});export const jsxs=jsx;export const Fragment=Symbol('fragment');`,
                    }),
                );
            },
        },
    ],
});
const {
    ComparisonReaderPanel: Panel,
    ComparisonReaderController: Controller,
    begin,
} = await import(
    `data:text/javascript;base64,${Buffer.from(built.outputFiles[0].text).toString("base64")}`
);

const token = "22222222-2222-2222-2222-222222222222";
const binding = "a".repeat(64);
const scope = { story: "synthetic-review", branch: "main" };
const row = { turn: "gift-0", arm: "left" };
const clone = (v) => structuredClone(v);
function status(client, phase = "ready") {
    return {
        version: 1,
        kind: "comparison_reader",
        client_id: client,
        operation_id: phase === "closed" ? null : 1,
        phase,
        running: false,
        run_token: phase === "closed" ? null : token,
        binding: phase === "closed" ? null : binding,
        error: null,
        read_only: true,
        execution_available: false,
    };
}
const source = {
    binding,
    protocol_version: 2,
    rows: [
        {
            row,
            source: {
                status: "available",
                scope,
                before_head: 0,
                after_head: 1,
                input_semantic_sha256: binding,
            },
            capture_available: false,
            receipt_available: true,
            recording_available: false,
            unavailable: ["capture_unavailable", "recording_unavailable"],
        },
    ],
    read_only: true,
    execution_available: false,
};
function evidence(request) {
    const head = request.edge === "before" ? 0 : 1;
    return {
        version: 1,
        kind: "comparison_reader",
        run_token: token,
        evidence: {
            version: 1,
            binding,
            row,
            scope,
            before_head: 0,
            after_head: 1,
            observer: clone(request.observer),
            edge: request.edge,
            read_only: true,
            generation_grant: false,
            body: {
                kind: "query",
                page: {
                    version: 2,
                    scope,
                    head,
                    revision: head,
                    story_time: head,
                    observer: clone(request.observer),
                    view: request.view,
                    privacy: "private_omniscient",
                    status: "supported",
                    total: 0,
                    rows: [],
                    next_cursor: null,
                    unsupported: [],
                },
            },
        },
    };
}
function nodes(value, result = []) {
    if (Array.isArray(value)) {
        for (const v of value) nodes(v, result);
    } else if (value && typeof value === "object" && "props" in value) {
        result.push(value);
        nodes(value.props?.children, result);
    }
    return result;
}
function text(value) {
    if (Array.isArray(value)) return value.map(text).join("");
    if (value && typeof value === "object" && "props" in value)
        return text(value.props?.children);
    return typeof value === "string" || typeof value === "number"
        ? String(value)
        : "";
}
function controls(controller) {
    begin();
    const tree = Panel({ controller });
    const all = nodes(tree);
    const labelled = (label) => {
        const parent = all.find(
            (n) => n.type === "label" && text(n).startsWith(label),
        );
        assert(parent, `ActualPanelLabel:${label}`);
        const select = nodes(parent).find((n) => n.type === "select");
        assert(select, `ActualPanelSelect:${label}`);
        return select;
    };
    const inspect = all.find(
        (n) => n.type === "button" && text(n) === "Inspect filtered state",
    );
    assert(inspect, "ActualPanelQueryButton");
    return {
        edge: labelled("State edge"),
        view: labelled("State view"),
        inspect,
    };
}
async function fixture() {
    begin(true);
    let pending;
    const calls = [];
    const controller = new Controller(async (name, args) => {
        assert.equal(name, "evaluation_comparison");
        calls.push(clone(args));
        if (args.action === "pick") return status(args.query.clientId);
        if (args.action === "source")
            return {
                version: 1,
                kind: "comparison_reader",
                run_token: token,
                source: clone(source),
            };
        if (args.action === "close")
            return status(args.query.clientId, "closed");
        if (args.action === "evidence") {
            assert.equal(pending, undefined, "OnlyOneRead");
            return new Promise((resolve) => {
                pending = { resolve, request: clone(args.query.request) };
            });
        }
        assert.fail(`UnexpectedNativeAction:${args.action}`);
    });
    controller.contextChanged("root/window/session/head/Lab", true);
    await controller.pick();
    controller.select(row);
    const ui = controls(controller);
    ui.inspect.props.onClick();
    assert(controller.get().busy, "ActualControllerPending");
    assert(pending, "ActualPanelDispatchedQuery");
    return { controller, calls, pending };
}
const results = [];
async function run(name, work) {
    try {
        await work();
        results.push({ name, passed: true });
    } catch (error) {
        results.push({
            name,
            passed: false,
            error: String(error?.message ?? error),
        });
    }
}
for (const [control, next] of [
    ["edge", "before"],
    ["view", "history"],
]) {
    await run(
        `pending-${control}-change-cannot-publish-old-query`,
        async () => {
            const f = await fixture();
            try {
                const controlBefore = controls(f.controller)[control];
                const disabled = controlBefore.props.disabled === true;
                // Call the actual handler even for the disabled policy: the frozen
                // product contract also requires its busy guard, independently of DOM.
                controlBefore.props.onChange({ target: { value: next } });
                if (!disabled) {
                    assert.equal(
                        controls(f.controller)[control].props.value,
                        next,
                        "ActualControlChanged",
                    );
                }
                f.pending.resolve(evidence(f.pending.request));
                await new Promise((resolve) => setTimeout(resolve, 0));
                if (disabled) {
                    // Disabled controls cannot change through ordinary UI interaction;
                    // the displayed result must still match the unchanged selection.
                    assert.equal(
                        controls(f.controller)[control].props.value,
                        f.pending.request[control],
                    );
                    assert.equal(
                        f.controller.get().evidence?.body.kind,
                        "query",
                    );
                } else {
                    assert.equal(
                        f.controller.get().evidence,
                        null,
                        "ChangedSelectionMustSuppressLateOldEvidence",
                    );
                }
            } finally {
                f.controller.dispose();
            }
        },
    );
}
await run("unchanged-panel-controls-show-exact-query-reply", async () => {
    const f = await fixture();
    try {
        f.pending.resolve(evidence(f.pending.request));
        await new Promise((resolve) => setTimeout(resolve, 0));
        assert.equal(f.controller.get().error, null);
        assert.equal(f.controller.get().evidence?.edge, "after");
        assert.equal(f.controller.get().evidence?.body.page.view, "knowledge");
        assert.equal(controls(f.controller).edge.props.value, "after");
        assert.equal(controls(f.controller).view.props.value, "knowledge");
    } finally {
        f.controller.dispose();
    }
});
await run(
    "idle-edge-and-view-changes-clear-prior-evidence-without-closing-source",
    async () => {
        for (const [control, next] of [
            ["edge", "before"],
            ["view", "history"],
        ]) {
            const f = await fixture();
            try {
                f.pending.resolve(evidence(f.pending.request));
                await new Promise((resolve) => setTimeout(resolve, 0));
                assert.equal(
                    f.controller.get().error,
                    null,
                    "ValidReplyBeforeIdleChange",
                );
                assert.equal(f.controller.get().evidence?.body.kind, "query");
                assert.equal(f.controller.get().busy, false);
                const originalToken = f.controller.get().status.run_token;
                const originalSource = f.controller.get().source;
                const originalSelected = f.controller.get().selected;
                const before = f.calls.length;
                controls(f.controller)[control].props.onChange({
                    target: { value: next },
                });
                assert.equal(controls(f.controller)[control].props.value, next);
                assert.equal(
                    f.controller.get().evidence,
                    null,
                    `${control}:IdleChangeClearsOldEvidence`,
                );
                assert.equal(f.controller.get().error, null);
                assert.equal(
                    f.controller.get().status.run_token,
                    originalToken,
                );
                assert.deepEqual(f.controller.get().source, originalSource);
                assert.deepEqual(f.controller.get().selected, originalSelected);
                assert.equal(
                    f.calls.length,
                    before,
                    "ControlChangeDoesNotReopenOrGenerate",
                );
            } finally {
                f.controller.dispose();
            }
        }
    },
);
console.log(
    JSON.stringify(
        {
            version: 1,
            sourceHashes: hashes,
            syntheticTransport: true,
            actualPanelCallbacks: true,
            actualController: true,
            mainExecution: false,
            rendering: false,
            nativeIpc: false,
            modelExecution: false,
            passed: results.filter((r) => r.passed).length,
            failed: results.filter((r) => !r.passed).length,
            results,
        },
        null,
        2,
    ),
);
if (results.some((r) => !r.passed)) process.exitCode = 1;

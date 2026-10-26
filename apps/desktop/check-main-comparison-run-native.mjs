// Frozen BEFORE native consumer implementation at c45fe005. SOURCE ONLY / UNRUN.
// Actual App/View callbacks and Main subscriptions; synthetic Host/native replies.
// React hook/JSX values are NOT DOM, SSR images, native IPC or model evidence.
// Root-approved test-only Main append: exactly
// export { controller, comparisonRun, nativeComparisonRun, comparison, dispose };
// No production export/hook, copied Main predicate, source-string assertion or server.
// API absence/build refusal is compile evidence, never behavioral RED.
// Run from apps/desktop: node check-main-comparison-run-native.mjs
import assert from "node:assert/strict";
import { build } from "esbuild";
import { mkdir, readFile, writeFile } from "node:fs/promises";
import { createHash, randomUUID, webcrypto } from "node:crypto";
import { fileURLToPath } from "node:url";
import path from "node:path";

const desktop = fileURLToPath(new URL("./", import.meta.url));
const sourceFiles = [
    "ui/main.tsx",
    "ui/App.tsx",
    "ui/comparison-run-controller.ts",
    "ui/comparison-run-model.ts",
    "ui/comparison-run-view.tsx",
    "ui/comparison-reader-controller.ts",
];
const hashes = Object.fromEntries(
    await Promise.all(
        sourceFiles.map(async (file) => [
            file,
            createHash("sha256")
                .update(await readFile(new URL(file, import.meta.url)))
                .digest("hex"),
        ]),
    ),
);
const mainSource = await readFile(
    new URL("ui/main.tsx", import.meta.url),
    "utf8",
);
const hookSource = `
const stores=new Map(); let current=null,i=0,effects=[];
export function begin(key,reset=false){if(reset||!stores.has(key))stores.set(key,[]);current=stores.get(key);i=0;effects=[];}
const same=(a,b)=>Array.isArray(a)&&Array.isArray(b)&&a.length===b.length&&a.every((v,n)=>Object.is(v,b[n]));
export function useState(initial){const n=i++,s=current;if(!(n in s))s[n]=typeof initial==='function'?initial():initial;
 return[s[n],v=>{s[n]=typeof v==='function'?v(s[n]):v;}];}
export function useRef(value){const n=i++;if(!(n in current))current[n]={current:value};return current[n];}
export function useCallback(fn,deps){const n=i++;if(!(n in current)||!same(current[n].deps,deps))current[n]={deps,fn};return current[n].fn;}
export function useMemo(fn,deps){const n=i++;if(!(n in current)||!same(current[n].deps,deps))current[n]={deps,value:fn()};return current[n].value;}
export function useEffect(fn,deps){const n=i++,s=current;const old=s[n];if(!old||!same(old.deps,deps))effects.push(()=>{
 old?.cleanup?.();s[n]={deps,cleanup:fn()};});}
export function flush(){const work=effects;effects=[];for(const run of work)run();}
export const useLayoutEffect=useEffect;
export const useSyncExternalStore=(subscribe,get)=>get();
`;
const jsxSource =
    "export const jsx=(type,props)=>({type,props});export const jsxs=jsx;export const Fragment=Symbol('fragment');";
const mainBuild = await build({
    stdin: {
        contents: `${mainSource}\nexport { controller, comparisonRun, nativeComparisonRun, comparison, dispose };`,
        resolveDir: path.join(desktop, "ui"),
        sourcefile: "main-native-review.tsx",
        loader: "tsx",
    },
    absWorkingDir: desktop,
    bundle: true,
    platform: "node",
    format: "esm",
    write: false,
    jsx: "automatic",
    define: { __DEV_HARNESS__: "false" },
    plugins: [
        {
            name: "main-render-leaves-only",
            setup(plugin) {
                plugin.onResolve(
                    {
                        filter: /^(\.\/App|react-dom\/client|react\/jsx-runtime)$/,
                    },
                    ({ path }) => ({ path, namespace: "main-review-render" }),
                );
                plugin.onLoad(
                    { filter: /.*/, namespace: "main-review-render" },
                    ({ path }) => ({
                        loader: "js",
                        contents:
                            path === "./App"
                                ? "export function App(){return null;}"
                                : path === "react-dom/client"
                                  ? "export function createRoot(){return{render(v){globalThis.__D07_MAIN_REVIEW_PROPS=v.props;},unmount(){}}}"
                                  : jsxSource,
                    }),
                );
            },
        },
    ],
});
const appBuild = await build({
    stdin: {
        contents:
            'export {App} from "./ui/App";export * from "./ui/comparison-run-view";export {begin,flush} from "react";',
        resolveDir: desktop,
        loader: "tsx",
    },
    absWorkingDir: desktop,
    bundle: true,
    platform: "node",
    format: "esm",
    write: false,
    jsx: "automatic",
    plugins: [
        {
            name: "app-hook-values-only",
            setup(plugin) {
                plugin.onResolve(
                    { filter: /^react(?:\/jsx-runtime)?$/ },
                    ({ path }) => ({ path, namespace: "app-review-hooks" }),
                );
                plugin.onLoad(
                    { filter: /.*/, namespace: "app-review-hooks" },
                    ({ path }) => ({
                        loader: "js",
                        contents: path === "react" ? hookSource : jsxSource,
                    }),
                );
                const leaves = {
                    "./EvaluationPanel": ["EvaluationPanel"],
                    "./ComparisonReaderPanel": ["ComparisonReaderPanel"],
                    "./selected-evaluation-view": ["SelectedEvaluationView"],
                    "./ArchivePanel": ["ArchivePanel"],
                    "./TimelinePanel": ["TimelinePanel"],
                    "./ForkPanel": ["ForkPanel"],
                    "./MemoryMaintenancePanel": ["MemoryMaintenancePanel"],
                    "./BrokerRetentionPanel": ["BrokerRetentionPanel"],
                    "./AuthorPanel": ["AuthorPanel"],
                    "./V2PlayPanel": ["V2PlayPanel"],
                    "./TurnDebugger": ["TurnDebugger"],
                    "./CapturePanel": ["CapturePanel"],
                    "./ModelPanel": ["ModelPanel"],
                    "./QueryInspector": ["QueryInspector"],
                    "./InspectionPanel": ["InspectionPanel"],
                };
                plugin.onResolve({ filter: /^\.\// }, ({ path: name }) =>
                    Object.hasOwn(leaves, name)
                        ? { path: name, namespace: "app-review-leaves" }
                        : undefined,
                );
                plugin.onLoad(
                    { filter: /.*/, namespace: "app-review-leaves" },
                    ({ path: name }) => ({
                        loader: "js",
                        contents: leaves[name]
                            .map(
                                (exported) =>
                                    `export function ${exported}(){return null;}`,
                            )
                            .join("\n"),
                    }),
                );
            },
        },
    ],
});
const imported = (text, suffix) =>
    import(
        `data:text/javascript;base64,${Buffer.from(`${text}\n// ${suffix}`).toString("base64")}`
    );
const app = await imported(appBuild.outputFiles[0].text, "app-native-review");
const clone = (value) => structuredClone(value);
const scope = { story: "synthetic-app-mode", branch: "main" },
    session = "synthetic-session";
const ids = {
    scripted: "11111111-1111-4111-8111-111111111111",
    native: "22222222-2222-4222-8222-222222222222",
    client: "33333333-3333-4333-8333-333333333333",
    token: "44444444-4444-4444-8444-444444444444",
    nativeClient: "55555555-5555-4555-8555-555555555555",
    nativeToken: "66666666-6666-4666-8666-666666666666",
};
const cleanup = (extra) => ({
    version: 1,
    kind: "selected_cleanup",
    cleanup_required: false,
    running: false,
    error: null,
    ...extra,
});
const runStatus = (mode, extra = {}) => ({
    version: mode === "approved_native" ? 2 : 1,
    kind: "comparison_run",
    protocol_version: 3,
    input_lane: mode,
    client_id: mode === "approved_native" ? ids.nativeClient : ids.client,
    run_id: mode === "approved_native" ? ids.native : ids.scripted,
    run_token: mode === "approved_native" ? ids.nativeToken : ids.token,
    operation_id: 71,
    comparison_kind: "paired",
    batch: 1,
    phase: "completed",
    running: false,
    error: null,
    completed_scenes: 4,
    completed: true,
    report_ready: true,
    source_matches: true,
    ...(mode === "approved_native"
        ? { cleanup_required: false, cleanup_running: false, cause: null }
        : {}),
    ...extra,
});
function deferred() {
    let resolve, reject;
    const promise = new Promise((yes, no) => {
        resolve = yes;
        reject = no;
    });
    return { promise, resolve, reject };
}
async function tick() {
    for (let n = 0; n < 48; n++) await Promise.resolve();
}
const nodes = (value) => {
    const result = [];
    function walk(v) {
        if (Array.isArray(v)) {
            for (const child of v) walk(child);
            return;
        }
        if (!v || typeof v !== "object" || !("type" in v)) return;
        result.push(v);
        walk(v.props?.children);
        walk(v.rendered);
    }
    walk(value);
    return result;
};
const text = (value) =>
    Array.isArray(value)
        ? value.map(text).join("")
        : value && typeof value === "object"
          ? text(value.props?.children)
          : value === null || value === undefined || typeof value === "boolean"
            ? ""
            : String(value);
let incarnation = 0;
async function mainFixture() {
    const calls = [],
        holds = [],
        jobs = [],
        runRows = new Map(),
        saved = new Map();
    let revision = 3,
        cleanupReply = cleanup(),
        heldStart = null,
        heldModel = null;
    let model = {
        operation_id: 1,
        resident: false,
        phase: "unloaded",
        percent: 0,
        imported: false,
        loaded: false,
        error: null,
        profile: null,
        available_profile: {
            id: "synthetic",
            model_bytes: 1,
            model_sha256: "a".repeat(64),
            runtime_revision: "synthetic",
            device: "synthetic",
            qualification: "not-qualified",
        },
    };
    globalThis.crypto ??= webcrypto;
    globalThis.localStorage = {
        getItem: (key) => saved.get(key) ?? null,
        setItem: (k, v) => saved.set(k, String(v)),
        removeItem: (k) => saved.delete(k),
    };
    globalThis.document = { getElementById: () => ({}) };
    globalThis.window = {
        addEventListener() {},
        removeEventListener() {},
        __TAURI__: {
            core: {
                invoke: async (command, args = {}) => {
                    assert(
                        calls.length < 384,
                        "bounded synthetic Main dispatch",
                    );
                    calls.push({ command, args: clone(args) });
                    if (command === "author_context")
                        return {
                            version: 1,
                            root_incarnation: "synthetic-root",
                            window_epoch: 1,
                            story_lab_granted: true,
                        };
                    if (command === "author_preview_discard") return true;
                    if (command === "model_status") return clone(model);
                    if (command === "model_unload") {
                        if (heldModel) await heldModel.promise;
                        return null;
                    }
                    if (
                        [
                            "evaluation_comparison_run",
                            "evaluation_comparison_native",
                        ].includes(command)
                    ) {
                        assert(
                            args.query &&
                                typeof args.query === "object" &&
                                !Array.isArray(args.query),
                            "native query object",
                        );
                        assert(
                            new TextEncoder().encode(JSON.stringify(args.query))
                                .length <= 4096,
                        );
                        const native =
                                command === "evaluation_comparison_native",
                            mode = native
                                ? "approved_native"
                                : "scripted_baseline";
                        if (
                            args.action === "cleanup_status" ||
                            args.action === "retry_cleanup"
                        ) {
                            assert(
                                native,
                                "generic cleanup cannot use scripted command",
                            );
                            assert.deepEqual(args.query, {});
                            return clone(cleanupReply);
                        }
                        if (args.action === "catalog")
                            return {
                                version: native ? 2 : 1,
                                kind: "comparison_run_catalog",
                                protocol_version: 3,
                                input_lane: mode,
                                max_new_scenes: 4,
                                runs: [],
                            };
                        let row = runRows.get(command);
                        if (args.action === "start") {
                            row = runStatus(mode, {
                                client_id: args.query.clientId,
                                comparison_kind: args.query.comparisonKind,
                                batch: args.query.batch,
                                phase: "paused",
                                completed: false,
                                completed_scenes: 1,
                            });
                            runRows.set(command, row);
                            if (native && heldStart) await heldStart.promise;
                        }
                        assert(
                            row,
                            "synthetic fixture never invents unknown run",
                        );
                        if (args.action === "close")
                            row = {
                                ...row,
                                phase: "closed",
                                running: false,
                                report_ready: false,
                                completed: false,
                                completed_scenes: 0,
                                source_matches: null,
                            };
                        runRows.set(command, row);
                        return clone(row);
                    }
                    assert.equal(
                        command,
                        "host_call",
                        "unexpected synthetic native command",
                    );
                    assert.equal(typeof args.input, "string");
                    assert(args.input.length <= 262144);
                    const envelope = JSON.parse(args.input);
                    assert.equal(envelope.version, 1);
                    const q = envelope.command;
                    let data;
                    if (q.op === "workspace")
                        data = {
                            persistent: true,
                            location: "synthetic",
                            schema_version: 1,
                            database_schema_version: 5,
                            stories: [
                                {
                                    scope: clone(scope),
                                    title: "Synthetic",
                                    revision,
                                    drafts: 0,
                                },
                            ],
                        };
                    else if (q.op === "resume")
                        data = {
                            session,
                            scope: clone(scope),
                            revision,
                            drafts: 0,
                        };
                    else if (q.op === "open") data = { revision };
                    else if (q.op === "play_snapshot_v2")
                        data = {
                            version: 2,
                            domain_version: 1,
                            scope: clone(scope),
                            revision,
                            rules: "fantasy_v1",
                            player: {
                                observer: "player",
                                self_state: {
                                    name: "Rowan",
                                    location: "quay",
                                    alive: true,
                                    energy: 2,
                                    abilities: {},
                                    attributes: {},
                                    injuries: [],
                                    affiliations: [],
                                    goals: [],
                                },
                            },
                            inventory: {},
                        };
                    else if (q.op === "play_snapshot")
                        data = {
                            scope: clone(scope),
                            revision,
                            rules: "fantasy_v1",
                            inventory: {},
                            receipts: [],
                            player: {
                                scope: clone(scope),
                                revision,
                                observer: "player",
                                self_state: {
                                    name: "Rowan",
                                    energy: 2,
                                    location: "quay",
                                },
                                observations: [],
                                facts: {},
                                beliefs: [],
                            },
                        };
                    else if (q.op === "inspection_query") {
                        const query = q.query;
                        data = {
                            version: 2,
                            scope: clone(query.scope),
                            head: query.expected_head,
                            revision: query.at_revision ?? query.expected_head,
                            story_time: 100,
                            observer: clone(query.observer),
                            view: query.view,
                            privacy:
                                query.observer.kind === "player"
                                    ? "player_visible"
                                    : query.observer.kind === "character"
                                      ? "private_character"
                                      : "private_omniscient",
                            status: ["summaries", "retrieval_indexes"].includes(
                                query.view,
                            )
                                ? "unsupported"
                                : "supported",
                            total: 0,
                            rows: [],
                            next_cursor: null,
                            unsupported: [],
                        };
                    } else if (q.op === "inspect") data = { synthetic: true };
                    else if (q.op === "close") data = null;
                    else throw Error("UnexpectedSyntheticHostOperation");
                    return { version: 1, status: "ok", data };
                },
            },
        },
    };
    const m = await imported(
        mainBuild.outputFiles[0].text,
        `Main fixture ${++incarnation}`,
    );
    const props = globalThis.__D07_MAIN_REVIEW_PROPS;
    try {
        await tick();
        assert.equal(
            m.controller.selected()?.id,
            session,
            "actual Main startup accepts synthetic session",
        );
        assert.equal(m.controller.get().visibleError, null);
        assert(
            m.controller.get().play,
            "actual default-player Domain1 snapshot route",
        );
        assert.equal(props.controller, m.controller);
        assert.equal(props.comparisonRun, m.comparisonRun);
        assert.equal(
            props.nativeComparisonRun,
            m.nativeComparisonRun,
            "actual Main binds native App prop",
        );
        assert(
            m.nativeComparisonRun && m.nativeComparisonRun !== m.comparisonRun,
            "two stable instances, one implementation",
        );
    } catch (error) {
        await m.dispose();
        await tick();
        throw error;
    }
    return {
        ...m,
        calls,
        props,
        jobs,
        setCleanup(value) {
            cleanupReply = cleanup(value);
        },
        advanceHead() {
            revision++;
        },
        holdStart() {
            heldStart = deferred();
            holds.push(heldStart);
            return heldStart;
        },
        holdModel() {
            heldModel = deferred();
            holds.push(heldModel);
            return heldModel;
        },
        modelChanged() {
            model = { ...model, operation_id: 2, percent: 17 };
        },
        async close() {
            for (const held of holds) held.resolve();
            for (const job of jobs) await job;
            await m.dispose();
            await tick();
        },
    };
}
function fullDouble(mode) {
    const calls = [],
        listeners = new Set();
    let closeHold = null,
        closeUncertain = false,
        onClose = null;
    let state = {
        context: "synthetic-app-context",
        allowed: true,
        mode,
        clientId: mode === "approved_native" ? ids.nativeClient : ids.client,
        status: runStatus(mode),
        catalog: null,
        pending: null,
        busy: false,
        uncertain: false,
        error: null,
        ...(mode === "approved_native"
            ? {
                  cleanup: cleanup(),
                  cleanupPending: null,
                  cleanupUncertain: false,
                  cleanupError: null,
              }
            : {}),
    };
    const publish = (update) => {
        state = { ...state, ...update };
        for (const listener of [...listeners]) listener();
    };
    const result = {
        mode,
        calls,
        get: () => state,
        subscribe: (listener) => {
            listeners.add(listener);
            return () => listeners.delete(listener);
        },
        replace: publish,
        holdClose() {
            closeHold = deferred();
            return closeHold;
        },
        uncertainClose() {
            closeUncertain = true;
        },
        onClose(value) {
            onClose = value;
        },
        async close() {
            assert(calls.length < 32, "bounded App-double calls");
            calls.push("close");
            publish({
                pending: {
                    action: "close",
                    clientId: state.clientId,
                    runToken: state.status?.run_token ?? null,
                    operationId: null,
                },
                busy: true,
            });
            onClose?.();
            if (closeHold) await closeHold.promise;
            if (closeUncertain)
                publish({
                    pending: null,
                    busy: false,
                    uncertain: true,
                    error: "EvaluationIo",
                });
            else
                publish({
                    pending: null,
                    busy: false,
                    clientId: null,
                    status: {
                        ...state.status,
                        phase: "closed",
                        running: false,
                        report_ready: false,
                        completed: false,
                        completed_scenes: 0,
                        source_matches: null,
                    },
                });
        },
        async cleanupStatus() {
            calls.push("cleanup_status");
        },
        async retryCleanup() {
            calls.push("retry_cleanup");
        },
        setContext() {
            throw Error("AppMustNotSetExecutionContext");
        },
    };
    for (const method of [
        "start",
        "resume",
        "lookup",
        "status",
        "open",
        "loadCatalog",
        "cancel",
        "dispose",
    ])
        result[method] = async () => {
            calls.push(method);
        };
    return result;
}
function readerDouble() {
    const calls = [];
    let hold = null;
    return {
        calls,
        holdClose() {
            hold = deferred();
            return hold;
        },
        subscribe: () => () => {},
        get: () => ({
            context: "synthetic-reader",
            allowed: true,
            observer: { kind: "omniscient" },
            clientId: null,
            status: null,
            source: null,
            summary: null,
            selected: null,
            evidence: null,
            busy: false,
            uncertain: false,
            error: null,
        }),
        async close() {
            calls.push({ action: "close" });
            if (hold) await hold.promise;
        },
        async pick(runId) {
            calls.push({ action: "pick", runId });
        },
        async pickManaged(source) {
            calls.push({ action: "pickManaged", ...clone(source) });
        },
    };
}
function appFixture(main, legacyOnly = false) {
    const scripted = fullDouble("scripted_baseline"),
        native = fullDouble("approved_native"),
        reader = readerDouble();
    const key = `app-${randomUUID()}`;
    const props = {
        controller: main.controller,
        comparison: reader,
        comparisonRun: scripted,
        ...(legacyOnly ? {} : { nativeComparisonRun: native }),
    };
    let fresh = true;
    // Evaluate only this fixed bundled component tree; no DOM or input injection.
    // Preserving function nodes lets assertions inspect the actual App callback
    // even if Root places its selector in an internal App helper component.
    const expand = (value, location) => {
        if (Array.isArray(value))
            return value.map((child, n) => expand(child, `${location}/${n}`));
        if (!value || typeof value !== "object" || !("type" in value))
            return value;
        if (typeof value.type === "function") {
            app.begin(`${key}/${location}`);
            const rendered = value.type(value.props);
            app.flush();
            return { ...value, rendered: expand(rendered, `${location}/body`) };
        }
        return {
            ...value,
            props: {
                ...value.props,
                children: expand(value.props?.children, `${location}/children`),
            },
        };
    };
    const render = () => {
        app.begin(key, fresh);
        fresh = false;
        const tree = app.App(props);
        app.flush();
        return expand(tree, "root");
    };
    const lane = () => {
        const result = nodes(render()).find(
            (node) =>
                node.type === "select" &&
                node.props["aria-label"] === "Full comparison inference lane",
        );
        assert(result, "actual App lane control");
        return result;
    };
    const view = () => {
        const result = nodes(render()).find(
            (node) => node.type === app.ComparisonRunView,
        );
        assert(result, "actual App run-view binding");
        return result;
    };
    const change = async (value) => {
        await Promise.resolve(lane().props.onChange({ target: { value } }));
        await tick();
    };
    const viewTree = () => view().rendered;
    return { scripted, native, reader, render, lane, view, change, viewTree };
}
const tests = [],
    test = (name, run) => tests.push({ name, run });
async function using(run) {
    const f = await mainFixture();
    try {
        await run(f);
    } finally {
        await f.close();
    }
}
const lab = async (f) => {
    f.controller.requestLab();
    f.controller.acknowledgeLab(true);
    await tick();
};
const identities = (f) => [
    f.comparisonRun.get().context,
    f.nativeComparisonRun.get().context,
];
test("Main supplies distinct stable scripted/native instances through actual App props", () =>
    using(async (f) => {
        assert.equal(f.comparisonRun.mode, "scripted_baseline");
        assert.equal(f.comparisonRun.get().mode, "scripted_baseline");
        assert.equal(f.nativeComparisonRun.mode, "approved_native");
        assert.equal(f.nativeComparisonRun.get().mode, "approved_native");
        assert.equal(f.comparisonRun.get().allowed, false);
        assert.equal(f.nativeComparisonRun.get().allowed, false);
        await lab(f);
        assert(
            f.comparisonRun.get().allowed &&
                f.nativeComparisonRun.get().allowed,
        );
        assert.equal(f.props.comparisonRun, f.comparisonRun);
        assert.equal(f.props.nativeComparisonRun, f.nativeComparisonRun);
    }));
test("Main observer and layout changes do not rekey either execution context", () =>
    using(async (f) => {
        await lab(f);
        const before = identities(f),
            readerBefore = f.comparison.get().context;
        f.controller.setObserver("mira");
        f.controller.layout(1, 1, 1);
        await tick();
        assert.deepEqual(identities(f), before);
        assert.notEqual(
            f.comparison.get().context,
            readerBefore,
            "read lens may retire reader only",
        );
        f.controller.setObserver("sable");
        await tick();
        assert.deepEqual(identities(f), before);
    }));
test("Main real model-status and modelBusy notifications stay outside execution identity", () =>
    using(async (f) => {
        await lab(f);
        const before = identities(f);
        f.modelChanged();
        await f.controller.refreshModel();
        assert.deepEqual(identities(f), before);
        const held = f.holdModel(),
            work = f.controller.modelAction("model_unload");
        f.jobs.push(work);
        try {
            assert.equal(f.controller.get().modelBusy, true);
            assert.deepEqual(identities(f), before);
        } finally {
            held.resolve();
            await work;
        }
        assert.equal(f.controller.get().modelBusy, false);
        assert.deepEqual(identities(f), before);
    }));
test("Main own native cleanup and pending notifications do not retire their execution context", () =>
    using(async (f) => {
        await lab(f);
        const before = identities(f);
        f.setCleanup({ cleanup_required: true, error: "Cleanup" });
        await f.nativeComparisonRun.cleanupStatus();
        assert.equal(
            f.nativeComparisonRun.get().cleanup.cleanup_required,
            true,
        );
        assert.deepEqual(identities(f), before);
        f.setCleanup({});
        await f.nativeComparisonRun.cleanupStatus();
        const held = f.holdStart(),
            work = f.nativeComparisonRun.start("paired", 1);
        f.jobs.push(work);
        try {
            await tick();
            assert(
                f.calls.some(
                    (call) =>
                        call.command === "evaluation_comparison_native" &&
                        call.args.action === "start",
                ),
                "actual native dispatch reached held transport",
            );
            assert(f.nativeComparisonRun.get().pending);
            assert.deepEqual(identities(f), before);
        } finally {
            held.resolve();
            await work;
        }
        assert.deepEqual(identities(f), before);
    }));
test("Main actual head/surface changes retire contexts but generic cleanup remains usable", () =>
    using(async (f) => {
        await lab(f);
        const before = identities(f);
        f.advanceHead();
        await f.controller.refresh();
        await tick();
        assert(identities(f).every((key, i) => key !== before[i]));
        f.controller.returnToPlay();
        await tick();
        assert(
            !f.comparisonRun.get().allowed &&
                !f.nativeComparisonRun.get().allowed,
        );
        const count = f.calls.length;
        await f.nativeComparisonRun.cleanupStatus();
        assert(
            f.calls
                .slice(count)
                .some(
                    (call) =>
                        call.command === "evaluation_comparison_native" &&
                        call.args.action === "cleanup_status",
                ),
        );
    }));
test("App preserves old comparisonRun-only prop and scripted section ID", () =>
    using(async (f) => {
        await lab(f);
        const a = appFixture(f, true),
            view = a.view();
        assert.equal(view.props.controller, a.scripted);
        assert(
            nodes(a.viewTree()).some(
                (node) => node.props.id === "comparison-run",
            ),
        );
    }));
test("App explicit idle lane change closes only old presentation and binds native section", () =>
    using(async (f) => {
        await lab(f);
        const a = appFixture(f);
        assert.equal(a.lane().props.value, "scripted_baseline");
        await a.change("approved_native");
        await tick();
        assert.equal(a.lane().props.value, "approved_native");
        assert.deepEqual(a.scripted.calls, ["close"]);
        assert.deepEqual(a.native.calls, []);
        assert.equal(a.view().props.controller, a.native);
        assert(
            nodes(a.viewTree()).some(
                (node) => node.props.id === "comparison-run-native",
            ),
        );
    }));
test("App mode switch installs reentrancy guard before old close notification", () =>
    using(async (f) => {
        await lab(f);
        const a = appFixture(f),
            hold = a.scripted.holdClose();
        let nested,
            reentered = false;
        const original = a.lane();
        a.scripted.onClose(() => {
            if (!reentered) {
                reentered = true;
                nested = Promise.resolve(
                    original.props.onChange({
                        target: { value: "approved_native" },
                    }),
                );
            }
        });
        const work = a.change("approved_native");
        try {
            await tick();
            assert.equal(
                a.scripted.calls.filter((x) => x === "close").length,
                1,
            );
            assert.equal(a.lane().props.value, "scripted_baseline");
        } finally {
            hold.resolve();
            await work;
            await nested;
            await tick();
        }
        assert.equal(a.lane().props.value, "approved_native");
        assert.deepEqual(a.native.calls, []);
    }));
test("App unknown old close keeps old lane and exposes recovery instead of hiding it", () =>
    using(async (f) => {
        await lab(f);
        const a = appFixture(f);
        a.scripted.uncertainClose();
        await a.change("approved_native");
        await tick();
        assert.equal(a.lane().props.value, "scripted_baseline");
        assert.equal(a.lane().props.disabled, true);
        assert.equal(a.view().props.controller, a.scripted);
        assert.deepEqual(a.native.calls, []);
    }));
for (const barrier of [
    "busy",
    "pending",
    "uncertain",
    "cleanup_required",
    "cleanupPending",
    "cleanupUncertain",
]) {
    test(`App inactive native ${barrier} blocks selector and handler without rekey`, () =>
        using(async (f) => {
            await lab(f);
            const a = appFixture(f),
                old = a.native.get();
            const changes =
                barrier === "cleanup_required"
                    ? {
                          cleanup: cleanup({
                              cleanup_required: true,
                              error: "Cleanup",
                          }),
                          status: runStatus("approved_native", {
                              phase: "cleanup_required",
                              cleanup_required: true,
                              error: "Cleanup",
                              report_ready: false,
                          }),
                      }
                    : barrier === "pending"
                      ? {
                            pending: {
                                action: "start",
                                clientId: old.clientId,
                                runToken: null,
                                operationId: null,
                            },
                        }
                      : barrier === "cleanupPending"
                        ? { cleanupPending: "status" }
                        : { [barrier]: true };
            a.native.replace(changes);
            const selector = a.lane();
            assert.equal(selector.props.disabled, true);
            await Promise.resolve(
                selector.props.onChange({
                    target: { value: "approved_native" },
                }),
            );
            await tick();
            assert.equal(a.lane().props.value, "scripted_baseline");
            assert.deepEqual(a.scripted.calls, []);
            assert.deepEqual(a.native.calls, []);
            assert.equal(a.native.get().context, old.context);
        }));
}
test("App native Inspect routes captured native identity only after reader close", () =>
    using(async (f) => {
        await lab(f);
        const a = appFixture(f);
        await a.change("approved_native");
        const held = a.reader.holdClose();
        const work = Promise.resolve(a.view().props.onInspect(ids.native));
        try {
            await tick();
            assert.deepEqual(a.reader.calls, [{ action: "close" }]);
        } finally {
            held.resolve();
            await work;
        }
        assert.deepEqual(a.reader.calls[1], {
            action: "pickManaged",
            runId: ids.native,
            mode: "approved_native",
        });
    }));
test("App old scripted Inspect remains scripted managed compatibility", () =>
    using(async (f) => {
        await lab(f);
        const a = appFixture(f, true);
        await a.view().props.onInspect(ids.scripted);
        const picked = a.reader.calls.filter((call) => call.action !== "close");
        assert.equal(picked.length, 1);
        assert(
            (picked[0].action === "pick" && picked[0].runId === ids.scripted) ||
                (picked[0].action === "pickManaged" &&
                    picked[0].runId === ids.scripted &&
                    picked[0].mode === "scripted_baseline"),
        );
    }));
for (const retire of ["mode", "context"])
    test(`App held native Inspect cannot open after ${retire} changes`, () =>
        using(async (f) => {
            await lab(f);
            const a = appFixture(f);
            await a.change("approved_native");
            const held = a.reader.holdClose();
            const inspect = Promise.resolve(
                a.view().props.onInspect(ids.native),
            );
            let switching;
            try {
                await tick();
                if (retire === "mode")
                    switching = a.change("scripted_baseline");
                else {
                    a.native.replace({
                        context: "retired-app-context",
                        allowed: false,
                    });
                    f.controller.returnToPlay();
                    a.render();
                }
                await tick();
            } finally {
                held.resolve();
                await inspect;
                await switching;
            }
            assert.equal(
                a.reader.calls.filter(
                    (call) =>
                        call.action === "pickManaged" || call.action === "pick",
                ).length,
                0,
                "no stale original or wrong-mode reader admission",
            );
        }));
test("App cleanup view remains mounted and actionable outside Story Lab", () =>
    using(async (f) => {
        const a = appFixture(f);
        a.native.replace({
            allowed: false,
            cleanup: cleanup({ cleanup_required: true, error: "Cleanup" }),
            status: null,
            cleanupError: "Cleanup",
        });
        assert.equal(f.controller.get().view, "play");
        assert.equal(
            typeof app.ComparisonRunCleanupView,
            "function",
            "frozen cleanup component export",
        );
        const node = nodes(a.render()).find(
            (node) =>
                node.type === app.ComparisonRunCleanupView &&
                node.props.controller === a.native,
        );
        assert(node, "actual App mounts native cleanup outside Lab");
        const body = node.rendered;
        const buttons = nodes(body).filter(
            (value) => value.type === "button" && value.props.disabled !== true,
        );
        assert(
            buttons.length >= 2 &&
                buttons.every((button) => text(button).trim().length > 0),
        );
        for (const button of buttons)
            await Promise.resolve(button.props.onClick());
        await tick();
        assert.equal(
            a.native.calls.filter((action) => action === "cleanup_status")
                .length,
            1,
        );
        assert.equal(
            a.native.calls.filter((action) => action === "retry_cleanup")
                .length,
            1,
        );
        assert(
            !a.native.calls.some((action) =>
                ["start", "resume", "open"].includes(action),
            ),
        );
    }));

const results = [];
for (const { name, run } of tests) {
    try {
        await run();
        results.push({ name, passed: true });
    } catch (error) {
        results.push({
            name,
            passed: false,
            error: String(error?.message ?? error).slice(0, 512),
        });
    }
}
const report = {
    version: 1,
    synthetic: true,
    evidence:
        "actual App/Main callbacks with synthetic native transport and React hook values",
    sourceHashes: hashes,
    checks: results,
    passed: results.filter((row) => row.passed).length,
    failed: results.filter((row) => !row.passed).length,
    nativeIpc: false,
    modelExecution: false,
    rendering: "none",
    desktopInput: false,
    limitations: [
        "no native permission, OS dialog or model authority proven",
        "no DOM, SSR image, layout or accessibility qualification",
        "closed service/reader decoders have separate frozen suites",
        "actual native IPC/render/model journeys remain separately allocated",
    ],
};
const output =
    process.env.LOCALLORE_CHECK_OUTPUT_DIR ??
    path.join(desktop, "artifacts/checks");
await mkdir(output, { recursive: true });
const json = JSON.stringify(report, null, 2);
assert(Buffer.byteLength(json) <= 128 * 1024);
await writeFile(
    path.join(output, `main-comparison-native-${randomUUID()}.json`),
    json,
    { flag: "wx" },
);
console.log(JSON.stringify(report));
if (report.failed) process.exitCode = 1;

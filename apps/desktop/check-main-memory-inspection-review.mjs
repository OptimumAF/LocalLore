// Frozen SOURCE ONLY for actual Main/App/context integration. UNCOMPILED/UNRUN.
// Adapts the existing __D07_MAIN_REVIEW_PROPS render-only fixture; no new app hook.
// Actual Main/controller/helper/App with synthetic Host/native DTOs and hook values.
// No Rust/native IPC/DOM/SSR pixels/model/permission or canonical-state proof.
import assert from "node:assert/strict";
import { build } from "esbuild";
import { mkdir, readFile, writeFile } from "node:fs/promises";
import { createHash, randomUUID, webcrypto } from "node:crypto";
import { fileURLToPath } from "node:url";
import path from "node:path";

const desktop = fileURLToPath(new URL("./", import.meta.url));
const sources = [
    "ui/main.tsx",
    "ui/App.tsx",
    "ui/memory-inspection-context.ts",
    "ui/memory-inspection-controller.ts",
    "ui/memory-inspection-model.ts",
];
const sourceHashes = Object.fromEntries(
    await Promise.all(
        sources.map(async (file) => [
            file,
            createHash("sha256")
                .update(await readFile(path.join(desktop, file)))
                .digest("hex"),
        ]),
    ),
);
const mainSource = await readFile(path.join(desktop, "ui/main.tsx"), "utf8");
const jsx =
    "export const jsx=(type,props)=>({type,props});export const jsxs=jsx;export const Fragment=Symbol('fragment');";
const mainBuild = await build({
    stdin: {
        contents: `${mainSource}\nexport {dispose};`,
        resolveDir: path.join(desktop, "ui"),
        sourcefile: "main-memory-inspection-review.tsx",
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
            name: "existing-main-render-hook",
            setup(p) {
                p.onResolve(
                    {
                        filter: /^(\.\/App|react-dom\/client|react\/jsx-runtime)$/,
                    },
                    ({ path }) => ({ path, namespace: "memory-main-render" }),
                );
                p.onLoad(
                    { filter: /.*/, namespace: "memory-main-render" },
                    ({ path }) => ({
                        loader: "js",
                        contents:
                            path === "./App"
                                ? "export function App(){return null;}"
                                : path === "react-dom/client"
                                  ? "export function createRoot(){return{render(v){globalThis.__D07_MAIN_REVIEW_PROPS=v.props;},unmount(){}}}"
                                  : jsx,
                    }),
                );
            },
        },
    ],
});
const hookSource = `
let values=[],index=0,subscriptions=[];
export function begin(){for(const s of subscriptions)s.release();subscriptions=[];index=0;}
export function reads(){return subscriptions;}
export function stop(){for(const s of subscriptions)s.release();subscriptions=[];}
export function useState(initial){const n=index++;if(!(n in values))values[n]=typeof initial==='function'?initial():initial;
return[values[n],next=>{values[n]=typeof next==='function'?next(values[n]):next;}];}
export function useRef(value){const n=index++;if(!(n in values))values[n]={current:value};return values[n];}
export const useCallback=fn=>fn;export const useMemo=fn=>fn();
export const useEffect=()=>{};export const useLayoutEffect=useEffect;
export function useSyncExternalStore(subscribe,get){const value=get(),s={value,notifications:0,release:()=>{}};
s.release=subscribe(()=>{s.notifications++;});subscriptions.push(s);return value;}
`;
const leaves = {
    "./EvaluationPanel": ["EvaluationPanel"],
    "./ComparisonReaderPanel": ["ComparisonReaderPanel"],
    "./selected-evaluation-view": ["SelectedEvaluationView"],
    "./ArchivePanel": ["ArchivePanel"],
    "./TimelinePanel": ["TimelinePanel"],
    "./ForkPanel": ["ForkPanel"],
    "./MemoryMaintenancePanel": ["MemoryMaintenancePanel"],
    "./MemoryInspectionPanel": ["MemoryInspectionPanel"],
    "./BrokerRetentionPanel": ["BrokerRetentionPanel"],
    "./AuthorPanel": ["AuthorPanel"],
    "./V2PlayPanel": ["V2PlayPanel"],
    "./TurnDebugger": ["TurnDebugger"],
    "./CapturePanel": ["CapturePanel"],
    "./ModelPanel": ["ModelPanel"],
    "./QueryInspector": ["QueryInspector"],
    "./InspectionPanel": ["InspectionPanel"],
};
const appBuild = await build({
    stdin: {
        contents: `export {App} from './ui/App';
    export {memoryInspectionContext} from './ui/memory-inspection-context';
    export {begin,reads,stop} from 'react';`,
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
            name: "actual-app-headless-hooks",
            setup(p) {
                p.onResolve(
                    { filter: /^react(?:\/jsx-runtime)?$/ },
                    ({ path }) => ({ path, namespace: "memory-app-hooks" }),
                );
                p.onLoad(
                    { filter: /.*/, namespace: "memory-app-hooks" },
                    ({ path }) => ({
                        loader: "js",
                        contents: path === "react" ? hookSource : jsx,
                    }),
                );
                p.onResolve({ filter: /^\.\// }, ({ path }) =>
                    Object.hasOwn(leaves, path)
                        ? { path, namespace: "memory-app-leaf" }
                        : undefined,
                );
                p.onLoad(
                    { filter: /.*/, namespace: "memory-app-leaf" },
                    ({ path }) => ({
                        loader: "js",
                        contents: leaves[path]
                            .map(
                                (name) =>
                                    `export function ${name}(){return null;}`,
                            )
                            .join("\n"),
                    }),
                );
            },
        },
    ],
});
const imported = (code, suffix) =>
    import(
        `data:text/javascript;base64,${Buffer.from(`${code}\n// ${suffix}`).toString("base64")}`
    );
const app = await imported(appBuild.outputFiles[0].text, "memory-app-review");
const clone = (v) => structuredClone(v);
function deferred() {
    let resolve, reject;
    const promise = new Promise((a, b) => {
        resolve = a;
        reject = b;
    });
    return { promise, resolve, reject };
}
async function tick() {
    for (let i = 0; i < 64; i++) await Promise.resolve();
}
function nodes(value) {
    const out = [];
    function visit(v) {
        if (Array.isArray(v)) {
            v.forEach(visit);
            return;
        }
        if (!v || typeof v !== "object" || !("type" in v)) return;
        out.push(v);
        visit(v.props?.children);
    }
    visit(value);
    return out;
}
const initialScope = { story: "synthetic-memory-main", branch: "main" };
const metadata = {
    version: 1,
    root_incarnation: "synthetic-root",
    window_epoch: 1,
    story_lab_granted: true,
};
let incarnation = 0;
async function fixture({
    domain = 1,
    player = "player",
    holdMetadata = false,
} = {}) {
    const calls = [],
        holds = [],
        saved = new Map(),
        nativeMetadata = deferred();
    let head = 3,
        nextSession = 0,
        selectedScope = clone(initialScope),
        nextRead = null;
    globalThis.crypto ??= webcrypto;
    globalThis.localStorage = {
        getItem: (key) => saved.get(key) ?? null,
        setItem: (key, value) => saved.set(key, String(value)),
        removeItem: (key) => saved.delete(key),
    };
    globalThis.document = { getElementById: () => ({}) };
    const model = {
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
    const thin = () => ({
        version: 2,
        domain_version: domain,
        scope: clone(selectedScope),
        revision: head,
        rules: "fantasy_v1",
        player: {
            observer: player,
            self_state: {
                name: "Synthetic",
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
    });
    const legacy = () => ({
        scope: clone(selectedScope),
        revision: head,
        rules: "fantasy_v1",
        inventory: {},
        receipts: [],
        player: {
            scope: clone(selectedScope),
            revision: head,
            observer: player,
            self_state: { name: "Synthetic", energy: 2, location: "quay" },
            observations: [],
            facts: {},
            beliefs: [],
        },
    });
    const invoke = async (command, args = {}) => {
        assert(calls.length < 320, "bounded synthetic Main dispatch");
        calls.push(clone({ command, args }));
        if (command === "author_context")
            return holdMetadata ? nativeMetadata.promise : clone(metadata);
        if (command === "author_preview_discard") return true;
        if (command === "model_status") return clone(model);
        if (command === "memory_inspection") {
            assert.deepEqual(Object.keys(args).sort(), ["action", "request"]);
            assert.equal(args.action, "packets");
            const q = JSON.parse(args.request),
                reply = {
                    kind: "memory_inspection",
                    version: 1,
                    session: q.session,
                    scope: clone(q.scope),
                    head: q.expected_head,
                    observer: player,
                    privacy: "player_visible",
                    binding: "a".repeat(64),
                    coverage: {
                        status: "raw_fallback",
                        verified_head: null,
                        covered_through: null,
                        raw_delta_after: 0,
                        fallback: "missing",
                    },
                    view: "packets",
                    packet_index: null,
                    total: 0,
                    rows: [],
                    next_cursor: null,
                };
            if (nextRead) {
                const held = nextRead;
                nextRead = null;
                held.entered.resolve();
                await held.release.promise;
            }
            return reply;
        }
        assert.equal(
            command,
            "host_call",
            "no new native/model/write command in fixture",
        );
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
                        scope: clone(initialScope),
                        title: "Synthetic",
                        revision: head,
                        drafts: 0,
                    },
                ],
            };
        else if (q.op === "resume") {
            selectedScope = clone(q.scope);
            data = {
                session: `session-${++nextSession}`,
                scope: clone(selectedScope),
                revision: head,
                drafts: 0,
            };
        } else if (q.op === "open") data = { revision: head };
        else if (q.op === "play_snapshot_v2") data = thin();
        else if (q.op === "play_snapshot") data = legacy();
        else if (q.op === "inspection_query") {
            const query = q.query;
            data = {
                version: query.version,
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
                status: ["summaries", "retrieval_indexes"].includes(query.view)
                    ? "unsupported"
                    : "supported",
                total: 0,
                rows: [],
                next_cursor: null,
                unsupported: [],
            };
        } else if (q.op === "inspect") data = { synthetic: true };
        else if (q.op === "close") data = null;
        else throw Error(`UnexpectedSyntheticHost:${q.op}`);
        return { version: 1, status: "ok", data };
    };
    globalThis.window = {
        addEventListener() {},
        removeEventListener() {},
        __TAURI__: { core: { invoke } },
    };
    const main = await imported(
        mainBuild.outputFiles[0].text,
        `memory Main ${++incarnation}`,
    );
    await tick();
    const props = globalThis.__D07_MAIN_REVIEW_PROPS;
    try {
        assert(props?.controller, "existing actual Main render hook");
        assert(
            props.memoryInspection,
            "actual Main stable memoryInspection prop",
        );
        assert.equal(
            typeof props.memoryInspectionContext,
            "function",
            "actual Main context callback",
        );
        assert(
            props.controller.selected(),
            "actual Main selected synthetic persistent story",
        );
        assert.equal(props.controller.get().visibleError, null);
    } catch (error) {
        nativeMetadata.resolve(clone(metadata));
        await main.dispose();
        await tick();
        throw error;
    }
    const controller = props.controller,
        inspection = props.memoryInspection;
    return {
        props,
        controller,
        inspection,
        calls,
        async lab() {
            controller.requestLab();
            controller.acknowledgeLab(true);
            controller.setObserver("player");
            await tick();
        },
        grant() {
            nativeMetadata.resolve(clone(metadata));
        },
        render() {
            app.begin();
            return app.App(props);
        },
        advanceHead() {
            head++;
        },
        holdRead() {
            assert.equal(nextRead, null);
            const held = { entered: deferred(), release: deferred() };
            nextRead = held;
            holds.push(held);
            return held;
        },
        async close() {
            nativeMetadata.resolve(clone(metadata));
            for (const h of holds) h.release.resolve();
            app.stop();
            await main.dispose();
            await tick();
        },
    };
}
const results = [];
async function test(name, run, options) {
    let f;
    try {
        f = await fixture(options);
        await run(f);
        results.push({ name, passed: true });
    } catch (error) {
        results.push({
            name,
            passed: false,
            error: String(error?.message ?? error).slice(0, 512),
        });
    } finally {
        if (f) await f.close();
    }
}
const reads = (f) => f.calls.filter((c) => c.command === "memory_inspection");
await test("actual Main supplies stable D1 player inspector and exact read context", async (f) => {
    const stable = f.inspection;
    assert.equal(stable.canRead(), false);
    await f.lab();
    const context = f.props.memoryInspectionContext();
    assert.equal(context.domainVersion, 1);
    assert.equal(context.view, "lab");
    assert.equal(context.lab, true);
    assert.equal(context.observer, "player");
    assert.equal(context.player, "player");
    assert.equal(f.inspection, stable);
    assert.equal(stable.get().context.session, f.controller.selected().id);
    assert.equal(stable.canRead(), true);
    await stable.refresh();
    assert.equal(reads(f).length, 1);
    const q = JSON.parse(reads(f)[0].args.request);
    assert.equal(q.session, context.session);
    assert.deepEqual(q.scope, context.scope);
    assert.equal(q.expected_head, context.expected_head);
    assert.equal(stable.get().packets.coverage.fallback, "missing");
});
await test(
    "delayed native Lab grant updates actual App inspection subscription without another gameplay change",
    async (f) => {
        await f.lab();
        assert.equal(f.props.memoryInspectionContext().lab, false);
        assert.equal(f.inspection.canRead(), false);
        f.render();
        const subscriptions = app
            .reads()
            .filter((s) => s.value === f.inspection.get());
        assert(
            subscriptions.length > 0,
            "actual App subscribes to actual inspector state",
        );
        const game = f.controller.get();
        f.grant();
        await tick();
        assert.equal(
            f.controller.get(),
            game,
            "no gameplay notification needed for grant arrival",
        );
        assert(
            subscriptions.some((s) => s.notifications > 0),
            "inspection subscription receives native grant update",
        );
        const tree = f.render(),
            panel = nodes(tree).find(
                (n) => n.props?.inspection === f.inspection,
            );
        assert(panel, "actual App mounts inspector with stable controller");
        assert.equal(panel.props.context.lab, true);
        assert.equal(f.inspection.canRead(), true);
    },
    { holdMetadata: true },
);
await test(
    "native Mira player role allowed but actual Mira Character selector never gains player lens",
    async (f) => {
        await f.lab();
        assert.equal(f.controller.get().play, null);
        assert.equal(f.controller.get().playV2.player.observer, "mira");
        assert.equal(f.props.memoryInspectionContext().player, "mira");
        assert.equal(f.inspection.canRead(), true);
        await f.inspection.refresh();
        const count = reads(f).length;
        f.controller.setObserver("mira");
        await tick();
        const c = f.props.memoryInspectionContext();
        assert.equal(c.observer, "mira");
        assert.equal(c.player, "mira");
        assert.equal(
            c.lab,
            false,
            "role selector, not ID equality, gates player lens",
        );
        assert.equal(f.inspection.canRead(), false);
        assert.equal(f.inspection.get().packets, null);
        await f.inspection.refresh();
        assert.equal(reads(f).length, count);
    },
    { player: "mira" },
);
await test("actual Omni selector clears data and cannot read player packet", async (f) => {
    await f.lab();
    await f.inspection.refresh();
    const count = reads(f).length;
    f.controller.setObserver("omniscient");
    await tick();
    assert.equal(f.props.memoryInspectionContext().lab, false);
    assert.equal(f.inspection.canRead(), false);
    assert.equal(f.inspection.get().packets, null);
    await f.inspection.refresh();
    assert.equal(reads(f).length, count);
});
await test(
    "actual D2 thin snapshot gives visible unsupported context without dispatch",
    async (f) => {
        await f.lab();
        const c = f.props.memoryInspectionContext();
        assert(c);
        assert.equal(c.domainVersion, 2);
        assert.equal(f.inspection.get().context.domainVersion, 2);
        assert.equal(f.inspection.canRead(), false);
        const panel = nodes(f.render()).find(
            (n) => n.props?.inspection === f.inspection,
        );
        assert(panel);
        assert.equal(panel.props.context.domainVersion, 2);
        await f.inspection.refresh();
        assert.equal(reads(f).length, 0);
    },
    { domain: 2 },
);
for (const change of ["head", "session", "lens", "dispose"]) {
    await test(`actual Main ${change} retirement drops held old read`, async (f) => {
        await f.lab();
        const previous = f.props.memoryInspectionContext(),
            held = f.holdRead();
        const work = f.inspection.refresh();
        await held.entered.promise;
        if (change === "head") {
            f.advanceHead();
            await f.controller.refresh();
            assert.notEqual(
                f.props.memoryInspectionContext().expected_head,
                previous.expected_head,
            );
        } else if (change === "session") {
            await f.controller.resume({ ...initialScope, branch: "other" });
            assert.notEqual(f.controller.selected().id, previous.session);
        } else if (change === "lens") {
            f.controller.setObserver("mira");
            await tick();
            assert.equal(f.inspection.canRead(), false);
        } else await f.controller.dispose();
        held.release.resolve();
        await work;
        await tick();
        assert.equal(f.inspection.get().packets, null);
        assert.equal(f.inspection.get().entries, null);
        assert.equal(f.inspection.get().source, null);
        assert.equal(f.inspection.get().busy, false);
        assert.equal(
            reads(f).length,
            1,
            "retirement never submits automatic fresh read",
        );
    });
}
await test("actual Main synchronous lens retirement before dispatch cannot send old read", async (f) => {
    await f.lab();
    let once = true;
    const release = f.inspection.subscribe(() => {
        if (once && f.inspection.get().busy) {
            once = false;
            f.controller.setObserver("mira");
        }
    });
    try {
        await f.inspection.refresh();
        await tick();
        assert.equal(reads(f).length, 0);
        assert.equal(f.inspection.get().packets, null);
    } finally {
        release();
    }
});
await test("actual context helper rejects selected/snapshot scope mismatch without relabelling", async (f) => {
    await f.lab();
    const s = f.controller.get(),
        selected = f.controller.selected();
    assert(app.memoryInspectionContext(f.controller, 17, true));
    const mismatch = {
        get: () => s,
        selected: () => ({
            ...selected,
            scope: { ...selected.scope, branch: "foreign" },
        }),
    };
    assert.equal(app.memoryInspectionContext(mismatch, 17, true), null);
    assert.equal(f.controller.get(), s);
    assert.equal(f.controller.selected(), selected);
});
const report = {
    version: 1,
    synthetic: true,
    nativeIpc: false,
    modelExecution: false,
    rendering: "headless-hook-values",
    sourceHashes,
    checks: results,
    passed: results.filter((r) => r.passed).length,
    failed: results.filter((r) => !r.passed).length,
    limitations: [
        "no native permission or actual Core packet proof",
        "no DOM/SSR pixels/layout",
        "new interfaces may be absent before integration; not behavioral RED",
        "no runtime/model/device/desktop execution",
    ],
};
const output =
    process.env.LOCALLORE_CHECK_OUTPUT_DIR ??
    path.join(desktop, "artifacts/checks");
await mkdir(output, { recursive: true });
await writeFile(
    path.join(output, `main-memory-inspection-${randomUUID()}.json`),
    JSON.stringify(report, null, 2),
    { flag: "wx" },
);
console.log(JSON.stringify(report));
if (report.failed) process.exitCode = 1;

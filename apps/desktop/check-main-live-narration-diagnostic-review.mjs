// Independent FIRST SOURCE ONLY. Execute actual Main wiring/public Controller
// and V2PlayController with synthetic IPC; headless hook values, no native/DOM.
import assert from "node:assert/strict";
import { build } from "esbuild";
import { mkdir, readFile, writeFile } from "node:fs/promises";
import { createHash, randomUUID, webcrypto } from "node:crypto";
import { fileURLToPath } from "node:url";
import path from "node:path";
import { syntheticHost, clone, plain, scope, baseRevision, originalTurn, originalAttempt, tick, data } from "./live-narration-diagnostic-review-fixtures.mjs";

process.env.TEMP = "D:/Dev/_Temp"; process.env.TMP = "D:/Dev/_Temp";
globalThis.crypto ??= webcrypto;
assert.equal(process.argv.length, 2, "ClosedMainLiveDiagnosticArguments");
const root = fileURLToPath(new URL(".", import.meta.url));
const output = process.env.LOCALLORE_CHECK_OUTPUT_DIR ?? path.join(root, "artifacts/checks");
for (const owned of [root, output]) assert.equal(path.parse(path.resolve(owned)).root.toLowerCase(), "d:\\", "PhysicalDRequired");
await mkdir(output, { recursive: true });
const prefix = `main-live-narration-first-${randomUUID()}`, setup = [], authored = [], checks = [];
const safe = (error) => String(error?.message ?? error).slice(0, 400);
const sourceFiles = ["ui/main.tsx", "ui/App.tsx", "ui/controller.ts", "ui/v2-play-controller.ts",
    "ui/TurnDebugger.tsx", "ui/trace-model.ts", "check-main-live-narration-diagnostic-review.mjs",
    "live-narration-diagnostic-review-fixtures.mjs"];
const hashes = async () => Object.fromEntries(await Promise.all(sourceFiles.map(async (name) =>
    [name, createHash("sha256").update(await readFile(path.join(root, name))).digest("hex")])));
const before = await hashes();
const jsx = "export const jsx=(type,props)=>({type,props});export const jsxs=jsx;export const Fragment=Symbol('fragment');";
const hooks = `
let subscriptions=[];
export function begin(){for(const s of subscriptions)s.release();subscriptions=[];}
export function reads(){return subscriptions;}export function stop(){begin();}
export const useCallback=fn=>fn;export const useMemo=fn=>fn();
export const useState=value=>[typeof value==='function'?value():value,()=>{}];
export const useRef=value=>({current:value});export const useEffect=()=>{};export const useLayoutEffect=useEffect;
export function useSyncExternalStore(subscribe,get){const value=get(),s={value,notifications:0,release:()=>{}};
s.release=subscribe(()=>{s.notifications++;});subscriptions.push(s);return value;}`;
const leafNames = {
    "./EvaluationPanel": ["EvaluationPanel"], "./ComparisonReaderPanel": ["ComparisonReaderPanel"],
    "./selected-evaluation-view": ["SelectedEvaluationView"], "./ArchivePanel": ["ArchivePanel"],
    "./TimelinePanel": ["TimelinePanel"], "./ForkPanel": ["ForkPanel"],
    "./MemoryMaintenancePanel": ["MemoryMaintenancePanel"], "./MemoryInspectionPanel": ["MemoryInspectionPanel"],
    "./BrokerRetentionPanel": ["BrokerRetentionPanel"], "./AuthorPanel": ["AuthorPanel"],
    "./V2PlayPanel": ["V2PlayPanel"], "./TurnDebugger": ["TurnDebugger"], "./CapturePanel": ["CapturePanel"],
    "./ModelPanel": ["ModelPanel"], "./QueryInspector": ["QueryInspector"], "./InspectionPanel": ["InspectionPanel"],
};
const imported = (code, label) => import(`data:text/javascript;base64,${Buffer.from(`${code}\n// ${label}`).toString("base64")}`);
let mainCode = null, app = null, incarnation = 0;
try {
    const mainSource = await readFile(path.join(root, "ui/main.tsx"), "utf8");
    const mainBuild = await build({ stdin: { contents: `${mainSource}\nexport {dispose};`,
        sourcefile: "existing-main-live-review.tsx", resolveDir: path.join(root, "ui"), loader: "tsx" },
        absWorkingDir: root, bundle: true, platform: "node", format: "esm", write: false,
        jsx: "automatic", define: { __DEV_HARNESS__: "false" }, plugins: [{
            name: "existing-main-render-props-pattern",
            setup(p) {
                p.onResolve({ filter: /^(\.\/App|react-dom\/client|react\/jsx-runtime)$/ },
                    ({ path }) => ({ path, namespace: "live-main-render" }));
                p.onLoad({ filter: /.*/, namespace: "live-main-render" }, ({ path }) => ({ loader: "js",
                    contents: path === "./App" ? "export function App(){return null;}"
                        : path === "react-dom/client"
                            ? "export function createRoot(){return{render(v){globalThis.__D07_MAIN_REVIEW_PROPS=v.props;},unmount(){}}}"
                            : jsx }));
            },
        }] });
    mainCode = mainBuild.outputFiles[0].text;
    const appBuild = await build({ stdin: { contents: "export {App} from './ui/App';export {begin,reads,stop} from 'react';",
        resolveDir: root, loader: "tsx" }, absWorkingDir: root, bundle: true, platform: "node", format: "esm",
        write: false, jsx: "automatic", define: { __DEV_HARNESS__: "false" }, plugins: [{
            name: "existing-actual-app-headless-hook-pattern",
            setup(p) {
                p.onResolve({ filter: /^react(?:\/jsx-runtime)?$/ }, ({ path }) => ({ path, namespace: "live-app-hooks" }));
                p.onLoad({ filter: /.*/, namespace: "live-app-hooks" }, ({ path }) => ({ loader: "js", contents: path === "react" ? hooks : jsx }));
                p.onResolve({ filter: /^\.\// }, ({ path }) => Object.hasOwn(leafNames, path) ? { path, namespace: "live-app-leaf" } : undefined);
                p.onLoad({ filter: /.*/, namespace: "live-app-leaf" }, ({ path }) => ({ loader: "js",
                    contents: leafNames[path].map((name) => `export function ${name}(){return null;}`).join("\n") }));
            },
        }] });
    app = await imported(appBuild.outputFiles[0].text, "actual-App-live-review");
} catch (error) { setup.push({ stage: "actual-Main-App-build", classification: "SETUP, not behavioral RED", error: safe(error) }); }
function nodes(value) {
    const result = [];
    const visit = (v) => { if (Array.isArray(v)) return v.forEach(visit);
        if (!v || typeof v !== "object" || !("type" in v)) return;
        result.push(v); visit(v.props?.children); };
    visit(value); return result;
}
async function settle(predicate, label) {
    for (let n = 0; n < 256; n++) { if (predicate()) return; await tick(); }
    throw Error(`SyntheticSetupDidNotSettle:${label}`);
}
async function fixture({ domain = 1 } = {}) {
    const host = syntheticHost({ domain, player: "hero", thin: true }), saved = new Map();
    globalThis.localStorage = { getItem: (key) => saved.get(key) ?? null,
        setItem: (key, value) => saved.set(key, String(value)), removeItem: (key) => saved.delete(key) };
    globalThis.document = { getElementById: () => ({}) };
    globalThis.window = { addEventListener() {}, removeEventListener() {}, __TAURI__: { core: { invoke: host.invoke } } };
    const main = await imported(mainCode, `actual-Main-live-${++incarnation}`);
    await tick();
    const props = globalThis.__D07_MAIN_REVIEW_PROPS, c = props?.controller, v2 = props?.v2;
    try {
        assert(c && v2, "ExistingMainPublicControllerAndV2PropsRequired");
        await settle(() => c.selected() && c.get().playV2, "public Main startup");
        assert.equal(c.get().visibleError, null, "ExistingMainFixtureHasNoGameplaySetupError");
    } catch (error) {
        host.releaseAll(); app.stop(); await main.dispose(); await tick(); throw error;
    }
    const f = { host, props, c, v2, main,
        async lab() { c.requestLab(); c.acknowledgeLab(true); await tick(); },
        async trace() {
            await c.showTrace(true); await c.controlTrace("enable");
            host.setEmptyTrace(false); await c.traceBasis(baseRevision); await c.readTrace();
            c.selectTrace(`${originalTurn}:${originalAttempt}`);
        },
        async ready() { await this.lab(); await this.trace(); },
        render() { app.begin(); return app.App(props); },
        async close() { host.releaseAll(); await tick(); app.stop(); await main.dispose(); await tick(); },
    };
    return f;
}
let calibrated = false;
if (!setup.length) {
    let f;
    try {
        f = await fixture({ domain: 2 });
        for (const name of ["traceNarrationValidationEligibility", "readTraceNarrationValidation", "cancelTraceNarrationValidation", "setTraceGameplayFence"])
            assert.equal(typeof f.c[name], "function", `MissingProposedAPI:${name}`);
        assert.deepEqual(plain(f.c.get().trace.narrationValidation), { status: "idle", query: null, reply: null, error: null });
        assert.equal(f.c.get().play, null); assert.equal(f.c.get().playV2.domain_version, 2);
        assert.equal(f.c.get().playV2.player.observer, "hero"); assert.equal(typeof f.v2.send, "function");
        calibrated = true;
    } catch (error) { setup.push({ stage: "actual-Main-public-fixture-calibration", classification: "SETUP, not behavioral RED", error: safe(error) }); }
    finally { if (f) await f.close(); }
}
async function test(name, run, options) {
    authored.push(name); if (!calibrated) return;
    let f;
    try { f = await fixture(options); await run(f); checks.push({ name, passed: true }); }
    catch (error) { checks.push({ name, passed: false, error: safe(error) }); }
    finally { if (f) await f.close(); }
}
const diag = (f) => f.c.get().trace.narrationValidation;
const diagnosticCalls = (f) => f.host.calls.filter((q) => q.op === "trace_narration_validation_read_v1");
function idle(f) { assert.deepEqual(plain(diag(f)), { status: "idle", query: null, reply: null, error: null }); }
function eligible(f, reason = null) { assert.deepEqual(f.c.traceNarrationValidationEligibility(), { allowed: reason === null, reason }); }
function observeGameplay(f, observations) {
    // Observations only inside the native stub; all assertions are outside it.
    f.host.observeGameplay((q) => observations.push({ op: q.op, diagnostic: plain(diag(f)),
        eligibility: plain(f.c.traceNarrationValidationEligibility()) }));
}

await test("actual Main initial fence admits checked nonliteral Domain2 player without a frontend grant", async (f) => {
    await f.ready(); eligible(f); assert.equal(f.c.traceAttempt().identity.observer, "hero");
    await f.c.readTraceNarrationValidation();
    const q = diagnosticCalls(f)[0];
    assert.equal(q.session, f.c.selected().id); assert.equal(q.expected_head, 5); assert.equal(q.base_revision, 4);
    assert.equal(q.turn, originalTurn); assert.equal(q.attempt, originalAttempt);
    assert.equal(diag(f).reply.observer, "player"); assert.equal(diag(f).reply.generation_grant, false);
    assert(!Object.hasOwn(f.c.get(), "nativeGrant"));
    assert(!f.host.calls.some((q) => q.op === "inspect")); assert.equal(f.c.debugReceipt(), null);
}, { domain: 2 });
await test("actual App mounts thin metadata only and preserves excluded sibling controls", async (f) => {
    await f.ready(); const tree = f.render(), all = nodes(tree);
    const debuggerNodes = all.filter((n) => n.type?.name === "TurnDebugger");
    assert.equal(debuggerNodes.length, 1); assert.equal(debuggerNodes[0].props.controller, f.c);
    for (const name of ["CapturePanel", "QueryInspector", "InspectionPanel", "TimelinePanel", "ForkPanel", "MemoryMaintenancePanel"])
        assert.equal(all.filter((n) => n.type?.name === name).length, 0, `ThinSiblingExcluded:${name}`);
    for (const label of ["Memory & evidence", "Inspection snapshots"]) {
        const button = all.find((n) => n.type === "button" && n.props?.children === label);
        assert(button); assert.equal(button.props.disabled, true);
    }
    const before = f.host.calls.length; f.render(); assert.equal(f.host.calls.length, before, "RenderNeverReadsDiagnostic");
}, { domain: 2 });
await test("actual V2 draft notification preserves equal Main fence without Root notification", async (f) => {
    await f.ready(); await f.c.readTraceNarrationValidation();
    const before = f.c.get(); let notifications = 0;
    const release = f.c.subscribe(() => { notifications++; });
    try { f.v2.setDraft("synthetic draft only"); assert.equal(f.c.get(), before); assert.equal(notifications, 0);
        assert.equal(diag(f).status, "recorded"); assert.equal(diagnosticCalls(f).length, 1); }
    finally { release(); }
});
await test("actual Main idle private fence notifies Root/App before first native send", async (f) => {
    f.c.returnToPlay(); f.c.setAction("wait"); await tick(); await f.v2.refresh();
    idle(f); f.render(); const current = f.c.get();
    const subscriptions = app.reads().filter((s) => s.value === current);
    assert(subscriptions.length > 0, "ActualAppSubscribesToControllerState");
    const observations = []; observeGameplay(f, observations);
    const held = f.host.holdGameplay("submit"), sending = f.v2.send();
    assert(f.v2.get().pending, "ActualPublicV2PendingInstalledSynchronously");
    assert.notEqual(f.c.get(), current, "ChangedIdleMainFenceNotifiesRoot");
    assert(subscriptions.some((s) => s.notifications > 0));
    await held.entered.promise; assert.equal(observations[0].op, "submit");
    assert.deepEqual(observations[0].diagnostic, { status: "idle", query: null, reply: null, error: null });
    held.release.resolve(); await sending;
});
await test("actual Main pending V2 blocks otherwise eligible Lab read and does not infer quiescence", async (f) => {
    f.c.returnToPlay(); f.c.setAction("wait"); await tick(); await f.v2.refresh();
    const held = f.host.holdGameplay("submit"), sending = f.v2.send(); await held.entered.promise;
    await f.ready(); eligible(f, "gameplay_unresolved");
    const count = diagnosticCalls(f).length; await f.c.readTraceNarrationValidation();
    assert.equal(diagnosticCalls(f).length, count); assert.equal(diag(f).status, "unavailable");
    assert.equal(diag(f).query, null); assert.equal(diag(f).reply, null);
    held.release.resolve(); await sending;
    assert.equal(f.v2.get().pending, null); assert(f.v2.get().uncertain);
    eligible(f, "gameplay_unresolved"); await f.c.readTraceNarrationValidation();
    assert.equal(diagnosticCalls(f).length, count, "UncertainOnlyRetainedOperationStillBlocks");
});
await test("actual nonterminal V2 retry observes cleared diagnostic before original-key status call", async (f) => {
    f.c.returnToPlay(); f.c.setAction("wait"); await tick(); await f.v2.refresh();
    await f.v2.send(); const retained = clone(f.v2.get().uncertain); assert(retained);
    await f.ready(); eligible(f, "gameplay_unresolved");
    f.c.returnToPlay(); await tick();
    const observations = []; observeGameplay(f, observations);
    const held = f.host.holdGameplay("turn_status"), retrying = f.v2.retryExact(); await held.entered.promise;
    assert.equal(observations[0].op, "turn_status"); assert.equal(observations[0].diagnostic.reply, null);
    assert.equal(held.command.turn, retained.request.turn);
    held.release.resolve(); await retrying;
    assert.equal(f.host.calls.filter((q) => q.op === "submit").length, 1, "RetryNeverResubmitsKnownOriginal");
    await f.ready(); eligible(f, "gameplay_unresolved");
});
await test("actual submitted V2 cancel stays a gameplay operation distinct from local metadata cancel", async (f) => {
    f.c.returnToPlay(); f.c.setAction("wait"); await tick(); await f.v2.refresh();
    await f.v2.send(); assert(f.v2.get().uncertain);
    const observations = []; observeGameplay(f, observations);
    const held = f.host.holdGameplay("cancel"), cancelling = f.v2.cancel(); await held.entered.promise;
    assert.equal(observations[0].op, "cancel"); assert.equal(observations[0].diagnostic.reply, null);
    assert.equal(observations[0].diagnostic.query, null);
    held.release.resolve(); await cancelling;
    await f.ready(); eligible(f);
    const nativeCancels = f.host.calls.filter((q) => q.op === "cancel").length;
    const read = f.host.holdDiagnostic(), reading = f.c.readTraceNarrationValidation(); await read.entered.promise;
    f.c.cancelTraceNarrationValidation();
    assert.equal(f.host.calls.filter((q) => q.op === "cancel").length, nativeCancels);
    read.release.resolve(data(read.command)); await reading; assert.equal(diag(f).status, "cancelled");
});
await test("actual V2 send remains Play-only with no new metadata-driven gameplay", async (f) => {
    await f.ready(); await f.v2.refresh(); f.v2.setDraft("synthetic");
    const count = f.host.calls.length; await f.v2.send();
    assert.equal(f.host.calls.length, count); assert.equal(f.v2.get().error, "Busy");
    assert.equal(diagnosticCalls(f).length, 0);
});
await test("actual Main IpcGateway native refusal is not bypassed by local Lab acknowledgement", async (f) => {
    await f.ready(); eligible(f); f.host.queueDiagnostic(Error("Forbidden"));
    await f.c.readTraceNarrationValidation(); assert.equal(diag(f).status, "refused");
    assert.equal(diag(f).error, "Forbidden"); assert.equal(diag(f).reply, null);
    assert.equal(diagnosticCalls(f).length, 1);
    assert(f.c.errors.snapshot().some((entry) => entry.source === "native" && entry.category === "Forbidden"));
});
for (const mode of ["head", "session", "observer"]) await test(`actual Main ${mode} retirement fences deferred diagnostic`, async (f) => {
    await f.ready(); const held = f.host.holdDiagnostic(), reading = f.c.readTraceNarrationValidation(); await held.entered.promise;
    let changing;
    if (mode === "head") { f.host.head = 6; changing = f.c.refresh(); }
    if (mode === "session") changing = f.c.resume({ story: "other-synthetic", branch: "main" });
    if (mode === "observer") f.c.setObserver("hero");
    await changing; idle(f); held.release.resolve(data(held.command)); await reading; idle(f);
    assert.equal(diagnosticCalls(f).length, 1);
});
await test("actual Main stopping fence cannot reopen through ordinary Root or V2 teardown notifications", async (f) => {
    await f.ready(); const held = f.host.holdDiagnostic(), reading = f.c.readTraceNarrationValidation(); await held.entered.promise;
    let tearingDown = false, injected = false, attempted = null, v2Notifications = 0, overflow = false;
    const observations = [];
    const observe = (source) => {
        if (observations.length === 64) { overflow = true; return; }
        observations.push({ source, eligibility: plain(f.c.traceNarrationValidationEligibility()), diagnostic: plain(diag(f)) });
    };
    const releaseV2 = f.v2.subscribe(() => {
        if (!tearingDown) return;
        v2Notifications++; observe("ordinary-v2-notification");
    });
    const releaseRoot = f.c.subscribe(() => {
        if (!tearingDown) return;
        observe("root-notification");
        if (injected) return;
        injected = true;
        // Public draft notifications occur while Main's real synchronization
        // subscriptions are still installed. No private stopping state is seeded.
        f.c.setDraft("synthetic teardown root notification");
        f.v2.setDraft("synthetic teardown V2 notification");
        observe("before-reentrant-read");
        attempted = f.c.readTraceNarrationValidation();
        observe("after-reentrant-read");
    });
    try {
        tearingDown = true;
        const disposing = f.main.dispose(); observe("dispose-returned-before-await");
        assert(injected, "FenceRetirementNotifiesBeforeUnsubscribe");
        assert(v2Notifications > 0, "ActualV2NotificationDuringTeardown");
        assert.equal(overflow, false);
        assert.equal(observations[0].diagnostic.status, "idle");
        for (const observation of observations) {
            assert.equal(observation.eligibility.allowed, false, observation.source);
            assert.equal(observation.diagnostic.query, null, observation.source);
            assert.equal(observation.diagnostic.reply, null, observation.source);
            assert.equal(observation.diagnostic.error, null, observation.source);
        }
        assert.equal(diagnosticCalls(f).length, 1, "TeardownReadNeverReachesNative");
        await attempted;
        held.release.resolve(data(held.command)); await reading; await disposing;
        assert.equal(diag(f).reply, null); assert.equal(diagnosticCalls(f).length, 1);
    } finally { releaseRoot(); releaseV2(); }
});

assert.deepEqual(await hashes(), before, "MainProductionAndOldSourcesUnchanged");
const report = { version: 1, kind: "main_live_narration_diagnostic_first_v1", authored: authored.length, setup, checks,
    passed: checks.filter((v) => v.passed).length, failed: checks.filter((v) => !v.passed).length, sourceHashes: before,
    rendering: "actual Main/App with headless hook values and synthetic native gateway",
    nativeIpc: false, modelExecution: false,
    limits: ["No private Controller/V2 state seeding or copied synchronization subscriber",
        "Pre-native send/retry clearing includes ordinary Play/view invalidation; pending/uncertain Lab tests isolate the Main fence",
        "Domain2/nonliteral-player cases read metadata only; lifecycle send/retry/cancel uses supported Domain1 thin fixtures",
        "Native author_context is a synthetic existing fixture DTO, not permission proof or a frontend grant bypass",
        "App leaves are render-prop stubs; real TurnDebugger SSR is in the companion checker",
        "No DOM/pixels/Host/Core, native WebView, SDK/device/desktop or OS probes"] };
await writeFile(path.join(output, `${prefix}.json`), JSON.stringify(report, null, 2), { flag: "wx" });
console.log(JSON.stringify(report));
if (setup.length || report.failed) process.exitCode = 1;

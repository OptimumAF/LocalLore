// Independent FIRST, SOURCE ONLY / UNFORMATTED / UNCOMPILED / UNRUN at handoff.
// Actual selected decoders/controller/panel/App selection, synthetic transport,
// React static HTML and disclosed captured-handler/hook doubles. No Rust,
// native grants/IPC, DOM/focus, WebView, pixels, provider, model or device proof.
// Root admits execution/output separately; this source does not authorize a run.
import assert from "node:assert/strict";
import { build, transform } from "esbuild";
import { mkdir, readFile, writeFile } from "node:fs/promises";
import { createHash, randomUUID, webcrypto } from "node:crypto";
import { setImmediate as tick } from "node:timers/promises";
import { fileURLToPath, pathToFileURL } from "node:url";
import path from "node:path";

globalThis.crypto ??= webcrypto;
const root = fileURLToPath(new URL(".", import.meta.url));
const output = process.env.LOCALLORE_CHECK_OUTPUT_DIR ?? path.join(root, "artifacts/checks");
const sourceFiles = [
    "check-selected-scene-v4-review.mjs", "ui/selected-evaluation-model.ts",
    "ui/selected-evaluation-controller.ts", "ui/selected-evaluation-view.tsx",
    "ui/comparison-reader-model.ts", "ui/App.tsx",
];
const groups = [
    "old versions and detached DTOs", "closed V3 identity and constructions",
    "closed diagnostics rows/nulls/bounds", "hostile non-wire object hygiene",
    "distinct source/resume/read bindings", "exact evidence identity/lens",
    "prepare hint and source binding", "wrong returned preparation/summary",
    "explicit start/status/source-refresh", "pending/cancel/late completion",
    "context retirement and notification reentrancy", "observer read fences",
    "cleanup and lost acknowledgement", "actual panel controls and diagnostics",
    "actual stale-lane normalization with hook double", "actual App selection path",
];

async function main() {
    assert(path.isAbsolute(output), "AbsoluteCheckOutputRequired");
    await mkdir(output, { recursive: true });
    const prefix = `selected-scene-v4-first-${randomUUID()}`;
    const sourceHashes = Object.fromEntries(await Promise.all(sourceFiles.map(async (name) => [
        name, createHash("sha256").update(await readFile(path.join(root, name))).digest("hex"),
    ])));
    const cases = [], html = [], controllers = new Set(), gates = new Set();
    let m;
    const report = async (setupError = null) => {
        const result = {
            version: 1, kind: "selected_scene_v4_frontend_first", sourceHashes,
            setup: setupError === null ? "ready" : "SETUP_UNRUN", setupError,
            sourceGroups: groups, sourceGroupCount: groups.length,
            executed: cases.length, passed: cases.filter((c) => c.passed).length,
            failed: cases.filter((c) => !c.passed).length, staticHtml: html.length, cases,
            evidence: "Synthetic selected DTOs/invoke; actual decoder/controller/panel/App code; React SSR and actual JSX handlers, with separately disclosed hook doubles. No native execution or pixels.",
            transforms: [
                "In-memory App.tsx append exports its existing local SelectedExperiment for this bundle only.",
                "In-memory TSX compilation captures actual React elements for selected view and App only; no decision replacement or source-file write.",
                "Optional selected-view-only hook adapter supplies persistent useState/ref/effect snapshots for captured-handler tests. Ordinary SSR uses real React hooks.",
            ],
            limitations: [
                "Synthetic DTOs are parser inputs, never actual Rust history, receipts, grants or source authority.",
                "Parsed-object tests cannot independently detect raw JSON duplicate keys; no universal Proxy-trap/side-effect guarantee.",
                "No DOM event dispatch/focus/accessibility tree, native consent, IPC, WebView render, images, model, engine or Android execution.",
                "Missing bundle/export prerequisites are setup/unrun, never a zero-test pass.",
            ],
        };
        for (let i = 0; i < html.length; i++) await writeFile(path.join(output, `${prefix}-${i}.html`), html[i], { flag: "wx" });
        await writeFile(path.join(output, `${prefix}.json`), JSON.stringify(result, null, 2), { flag: "wx" });
        console.log(JSON.stringify(result));
        if (setupError !== null || result.failed !== 0 || result.executed === 0) process.exitCode = 1;
    };
    try {
        const hookModule = `
import {createElement,Fragment} from "react";
export const nodes=[];
export const hooks={active:null};
export const __selectedSceneFragment=Fragment;
export function __selectedSceneElement(type,props,...children){const result=createElement(type,props,...children);nodes.push(result);return result;}
`;
        const hookReactModule = `
import * as real from "react";
import {hooks} from "selected-scene-review-hooks";
export * from "react";
export function useState(initial){const f=hooks.active;if(!f)return real.useState(initial);const i=f.cursor++;if(!(i in f.values))f.values[i]=typeof initial==="function"?initial():initial;return [f.values[i],value=>{const next=typeof value==="function"?value(f.values[i]):value;if(!Object.is(next,f.values[i])){f.values[i]=next;f.dirty=true;}}];}
export function useRef(initial){const f=hooks.active;if(!f)return real.useRef(initial);const i=f.cursor++;if(!(i in f.values))f.values[i]={current:initial};return f.values[i];}
export function useCallback(fn,deps){return hooks.active?fn:real.useCallback(fn,deps);}
export function useMemo(fn,deps){return hooks.active?fn():real.useMemo(fn,deps);}
export function useSyncExternalStore(subscribe,get,server=get){return hooks.active?get():real.useSyncExternalStore(subscribe,get,server);}
export function useEffect(effect,deps){const f=hooks.active;if(!f)return real.useEffect(effect,deps);const i=f.effectCursor++,old=f.dependencies[i];if(!old||!deps||old.length!==deps.length||deps.some((value,n)=>!Object.is(value,old[n]))){f.dependencies[i]=deps;f.effects.push(effect);}}
`;
        const built = await build({
            stdin: {
                contents: 'export * from "./ui/selected-evaluation-model";export {SelectedEvaluationController} from "./ui/selected-evaluation-controller";export {SelectedEvaluationView} from "./ui/selected-evaluation-view";export {SelectedSceneAppSelectionForReview} from "./ui/App";export {createElement} from "react";export {renderToStaticMarkup} from "react-dom/server";export {nodes,hooks} from "selected-scene-review-hooks";',
                resolveDir: root, loader: "tsx",
            },
            bundle: true, platform: "node", format: "cjs", write: false,
            jsx: "automatic", define: { __DEV_HARNESS__: "false" },
            plugins: [{ name: "capture-actual-selected-scene-ui", setup(plugin) {
                plugin.onResolve({ filter: /^selected-scene-review-hooks$/ }, () => ({ path: "hooks", namespace: "selected-scene-hooks" }));
                plugin.onLoad({ filter: /.*/, namespace: "selected-scene-hooks" }, () => ({ contents: hookModule, loader: "js", resolveDir: root }));
                plugin.onResolve({ filter: /^react$/ }, (args) => /[\\/]selected-evaluation-view\.tsx$/.test(args.importer)
                    ? { path: "react", namespace: "selected-scene-hook-react" } : undefined);
                plugin.onLoad({ filter: /.*/, namespace: "selected-scene-hook-react" }, () => ({ contents: hookReactModule, loader: "js", resolveDir: root }));
                plugin.onLoad({ filter: /[\\/](App|selected-evaluation-view)\.tsx$/ }, async ({ path: filename }) => {
                    let contents = await readFile(filename, "utf8");
                    if (path.basename(filename) === "App.tsx") {
                        assert.match(contents, /function SelectedExperiment\s*\(/, "ActualAppSelectionFunctionRequired");
                        contents += "\nexport {SelectedExperiment as SelectedSceneAppSelectionForReview};\n";
                    }
                    contents = 'import {__selectedSceneElement,__selectedSceneFragment} from "selected-scene-review-hooks";\n' + contents;
                    const compiled = await transform(contents, { loader: "tsx", jsx: "transform", jsxFactory: "__selectedSceneElement", jsxFragment: "__selectedSceneFragment", target: "es2022", sourcefile: filename });
                    return { contents: compiled.code, loader: "js", resolveDir: path.dirname(filename) };
                });
            } }],
        });
        assert.equal(built.outputFiles.length, 1, "SingleReviewBundleRequired");
        const bundle = path.join(output, `${prefix}.cjs`);
        await writeFile(bundle, built.outputFiles[0].contents, { flag: "wx" });
        m = (await import(pathToFileURL(bundle).href)).default;
        for (const name of ["checkedSelectedPrepared", "checkedSelectedStatus", "checkedSelectedSource", "checkedSelectedSummary", "checkedSelectedDiagnostics", "checkedSelectedEvidence", "SelectedEvaluationController", "SelectedEvaluationView", "SelectedSceneAppSelectionForReview", "renderToStaticMarkup", "createElement"]) assert.equal(typeof m[name], "function", `RequiredActualExport:${name}`);
        assert(Array.isArray(m.nodes) && m.hooks && Object.hasOwn(m.hooks, "active"), "ReviewHookPrerequisites");
    } catch (error) {
        await report(String(error?.message ?? error).slice(0, 1000));
        return;
    }

    const clone = (value) => structuredClone(value);
    const h = (digit) => digit.repeat(64);
    const SOURCE = h("a"), SELECTED = h("b"), READ = h("c"), PREFIX = h("d"), RECEIPT = h("e");
    const SOURCE_TOKEN = "11111111-1111-1111-1111-111111111111";
    const READ_TOKEN = "22222222-2222-2222-2222-222222222222";
    const PLAN_TOKEN = "33333333-3333-3333-3333-333333333333";
    const RUN = "44444444-4444-4444-4444-444444444444";
    const READER = "55555555-5555-5555-5555-555555555555";
    const CLIENT = "66666666-6666-6666-6666-666666666666";
    const scope = { story: "selected-scene-synthetic", branch: "copied-prefix" };
    const selection = { turn: "courier-05", clicked_arm: "right", index: 4 };
    const row = { turn: selection.turn, arm: selection.clicked_arm };
    const source = { readerClientId: READER, runToken: SOURCE_TOKEN, binding: SOURCE };
    const omni = { kind: "omniscient" }, player = { kind: "player" }, mira = { kind: "character", id: "mira" };
    const PRIVATE = "SYNTHETIC_PRIVATE_SELECTED_SCENE_CANARY";
    const constructors3 = [
        { arm: "literal_player_v1", prompt_version: "locallore-play-v2.6-literal-director-v1", narration_policy: "grounded-prose-v2.2", director_schema_id: "locallore-director-literal-v1", context_policy: null, compiler_version: null, context_version: null, literal_source_version: 1, literal_render_version: 1, literal_schema_version: 1, literal_packing_version: 1, forwarded_budget_version: 1 },
        { arm: "relevant_memory_v1", prompt_version: "locallore-play-v2.5", narration_policy: "grounded-prose-v2.2", director_schema_id: "locallore-director-v2", context_policy: "state_relevant_memory_v1", compiler_version: 2, context_version: 2, literal_source_version: null, literal_render_version: null, literal_schema_version: null, literal_packing_version: null, forwarded_budget_version: 1 },
    ];
    const constructors4 = [
        { ...constructors3[0], arm: "literal_scene_v1", prompt_version: "locallore-play-v2.10-literal-director-v1-scene-frame-v1", narration_policy: "grounded-prose-v2.4-scene-frame-v1", narrator_schema_id: "locallore-narrator-v2", scene_frame_version: 1, scene_capture_gate_version: 1 },
        { ...constructors3[1], arm: "relevant_memory_scene_v1", prompt_version: "locallore-play-v2.9-scene-frame-v1", narration_policy: "grounded-prose-v2.4-scene-frame-v1", narrator_schema_id: "locallore-narrator-v2", scene_frame_version: 1, scene_capture_gate_version: 1 },
    ];
    const tagged = (version) => version === 1 ? {} : { source_protocol_version: version + 1, constructions: clone(version === 3 ? constructors4 : constructors3) };
    function prepared(version = 3) {
        return { version, kind: "selected_prepared", binding: SELECTED,
            ...(version === 3 ? { source_binding: SOURCE } : {}), lane: "scripted_selected_case",
            selection: clone(selection), arms: ["left", "right"].map((arm, i) => ({ arm, scope: clone(scope), before_head: 2 + i, prefix_sha256: PREFIX, input_semantic_sha256: h("f") })), ...tagged(version) };
    }
    function summary(version = 3) {
        return { version, kind: "selected_read", binding: READ, lane: "scripted_selected_case", selection: clone(selection),
            arms: ["left", "right"].map((arm, i) => ({ arm, scope: clone(scope), before_head: 2 + i, after_head: 3 + i, available: true })),
            read_only: true, execution_available: false, ...tagged(version) };
    }
    function diagnosticRow(version = 3, arm = "left") {
        const index = arm === "left" ? 0 : 1;
        const common = { turn: selection.turn, arm, phase: "committed", error: null, expected: "accepted typed fixture command", passed: true,
            failures: [], quality_flags: [], roles: 2, roles_known: true, elapsed_ms: 3, actual_receipt_sha256: RECEIPT };
        if (version === 3) return { ...common, construction: clone(constructors4[index]), construction_evidence_status: "validated_committed_scene_narrator_v1", construction_evidence_reason: null,
            construction_matches: true, privacy_evidence_status: "checked_finite_sentinels", fallback: false, repairs: 0, recovered_without_checkpoint: false,
            first_final_response_ms: 1, commit_elapsed_ms: 2, narrator_prompt_sha256: h("1"), narrator_schema_sha256: h("2"), scene_frame_sha256: h("3") };
        return { ...common, privacy_passed: true, context_evidence_available: true, ...(version === 2 ? {
            construction: clone(constructors3[index]), construction_evidence_status: index === 0 ? "validated_literal" : "validated_relevant", construction_matches: true,
            literal_source_units: index === 0 ? 5 : null, literal_selected_start: index === 0 ? 1 : null, literal_selected_units: index === 0 ? 4 : null, fallback: null,
        } : {}) };
    }
    function diagnostics(version = 3) {
        return { version, kind: "selected_diagnostics", binding: READ, lane: "scripted_selected_case", completed: true,
            rows: [diagnosticRow(version, "left"), diagnosticRow(version, "right")], physical_setups: 0, physical_setup_ms: null,
            left_charged_ms: 3, right_charged_ms: 4, left_reserved_roles: 3, right_reserved_roles: 3,
            human_reviewed: 0, ...(version === 3 ? { human_rubric: "not_reviewed" } : {}), quality_accepted: false,
            unavailable: ["scripted_lane_no_native_setup_measurement", "selected_protocol4_native_rerun_unavailable"], ...tagged(version) };
    }
    const wrap = (kind, field, value, token = READ_TOKEN) => ({ version: 1, kind, run_token: token, [field]: value });
    const decode = {
        prepared: (value) => m.checkedSelectedPrepared(value),
        summary: (value, bound = READ, token = READ_TOKEN) => m.checkedSelectedSummary(wrap("selected_summary", "summary", value), token, bound),
        diagnostics: (value, bound = summary(value.version)) => m.checkedSelectedDiagnostics(wrap("selected_diagnostics_result", "diagnostics", value), READ_TOKEN, bound),
    };
    const factories = { prepared, summary, diagnostics };
    function finiteWire(body) {
        assert.throws(body, (error) => error instanceof Error && error.message === "SelectedEvaluationWire");
    }
    function frozenTree(value) {
        if (value !== null && typeof value === "object") { assert(Object.isFrozen(value)); for (const child of Object.values(value)) frozenTree(child); }
    }
    async function flush() { for (let n = 0; n < 12; n++) await Promise.resolve(); await tick(); }
    function gate() {
        let resolve;
        const promise = new Promise((r) => { resolve = r; });
        const entry = { promise, resolve: (value) => { gates.delete(entry); resolve(value); } };
        gates.add(entry); return entry;
    }
    async function check(name, body) {
        let timer;
        try {
            await Promise.race([Promise.resolve().then(body), new Promise((_, reject) => { timer = setTimeout(() => reject(Error("FiniteSyntheticCaseTimeout")), 3000); })]);
            cases.push({ name, passed: true });
        } catch (error) { cases.push({ name, passed: false, error: String(error?.message ?? error).slice(0, 500) }); }
        finally {
            clearTimeout(timer);
            for (const g of [...gates]) g.resolve(undefined);
            for (const c of controllers) c.dispose();
            controllers.clear(); m.hooks.active = null; await flush();
        }
    }
    async function bad(kind, name, mutate, version = 3) {
        await check(`${kind}${version}: rejects ${name}`, () => { const value = factories[kind](version); mutate(value); finiteWire(() => decode[kind](value)); });
    }

    // Old controls intentionally retain mutable detached standalone DTO behavior.
    for (const version of [1, 2, 3]) for (const kind of ["prepared", "summary", "diagnostics"]) {
        await check(`${kind}${version}: positive detached mutable copy`, () => {
            const input = factories[kind](version), before = clone(input), actual = decode[kind](input);
            assert.deepEqual(actual, before); assert.notEqual(actual, input);
            if (actual.arms) actual.arms[0].before_head = 99; else actual.rows[0].expected = "changed standalone copy";
            assert.deepEqual(input, before);
        });
    }
    await check("source identity: exactly three original keys, no source-version or grant escape", () => {
        assert.deepEqual(m.checkedSelectedSource(clone(source)), source);
        for (const key of ["protocol_version", "expectedSourceProtocol", "path", "grant"]) finiteWire(() => m.checkedSelectedSource({ ...source, [key]: 4 }));
    });
    for (const kind of ["prepared", "summary", "diagnostics"]) {
        for (const [name, mutation] of [
            ["unsupported version", (v) => { v.version = 4; }],
            ["missing source protocol", (v) => { delete v.source_protocol_version; }],
            ["wrong source protocol", (v) => { v.source_protocol_version = 3; }],
            ["unknown raw escape", (v) => { v.full_report = {}; }],
            ["source lane native", (v) => { v.lane = "native_selected_case"; }],
            ["missing constructions", (v) => { delete v.constructions; }],
            ["construction order", (v) => { v.constructions.reverse(); }],
            ["extra construction", (v) => { v.constructions.push(clone(constructors4[0])); }],
            ["old literal construction", (v) => { v.constructions[0] = clone(constructors3[0]); }],
            ["old relevant construction", (v) => { v.constructions[1] = clone(constructors3[1]); }],
        ]) await bad(kind, name, mutation);
        for (const index of [0, 1]) for (const key of Object.keys(constructors4[index])) {
            await bad(kind, `descriptor${index} missing ${key}`, (v) => { delete v.constructions[index][key]; });
            await bad(kind, `descriptor${index} wrong ${key}`, (v) => { v.constructions[index][key] = typeof v.constructions[index][key] === "number" ? 99 : "wrong-scene-construction"; });
        }
        for (const key of Object.keys(factories[kind]())) await bad(kind, `missing required ${key}`, (v) => { delete v[key]; });
    }
    for (const [name, mutation] of [
        ["missing source snapshot binding", (v) => { delete v.source_binding; }],
        ["null source snapshot binding", (v) => { v.source_binding = null; }],
        ["malformed source snapshot binding", (v) => { v.source_binding = "not-a-hash"; }],
        ["uppercase source binding", (v) => { v.source_binding = "A".repeat(64); }],
        ["unknown selection key", (v) => { v.selection.scope = scope; }],
        ["out of range selected index", (v) => { v.selection.index = 24; }],
        ["duplicate physical arm", (v) => { v.arms[1].arm = "left"; }],
        ["missing prefix hash", (v) => { delete v.arms[0].prefix_sha256; }],
        ["oversized prepared", (v) => { v.arms[0].scope.story = "x".repeat(16384); }],
    ]) await bad("prepared", name, mutation);
    for (const [name, mutation] of [
        ["source-binding field belongs only to prepared", (v) => { v.source_binding = SOURCE; }],
        ["execution capability", (v) => { v.execution_available = true; }],
        ["writable read metadata", (v) => { v.read_only = false; }],
        ["missing nullable after head", (v) => { delete v.arms[0].after_head; }],
        ["availability/head contradiction", (v) => { v.arms[0].available = false; }],
        ["after before before head", (v) => { v.arms[0].after_head = 1; }],
        ["raw outcome on arm", (v) => { v.arms[0].receipt = {}; }],
    ]) await bad("summary", name, mutation);
    for (const mistaken of [SOURCE, SELECTED]) await check(`summary read binding rejects substituted ${mistaken[0]} authority`, () => finiteWire(() => decode.summary(summary(), mistaken)));
    await check("summary wrapper token remains exact", () => finiteWire(() => m.checkedSelectedSummary(wrap("selected_summary", "summary", summary(), SOURCE_TOKEN), READ_TOKEN, READ)));
    for (const key of Object.keys(diagnosticRow())) await bad("diagnostics", `row missing required ${key}`, (v) => { delete v.rows[0][key]; });
    for (const [name, mutation] of [
        ["old privacy boolean", (v) => { v.rows[0].privacy_passed = false; }],
        ["old context boolean", (v) => { v.rows[0].context_evidence_available = true; }],
        ["old literal suffix", (v) => { v.rows[0].literal_selected_start = 0; }],
        ["raw output escape", (v) => { v.rows[0].narration = PRIVATE; }],
        ["foreign turn", (v) => { v.rows[0].turn = "courier-06"; }],
        ["duplicate arm", (v) => { v.rows[1] = clone(v.rows[0]); }],
        ["third row", (v) => { v.rows.push(clone(v.rows[0])); }],
        ["physical arm/construction mismatch", (v) => { v.rows[0].construction = clone(constructors4[1]); }],
        ["old evidence status", (v) => { v.rows[0].construction_evidence_status = "validated_literal"; }],
        ["unknown privacy status", (v) => { v.rows[0].privacy_evidence_status = "all_private_history_safe"; }],
        ["numeric fallback", (v) => { v.rows[0].fallback = 1; }],
        ["negative repairs", (v) => { v.rows[0].repairs = -1; }],
        ["nonboolean recovery", (v) => { v.rows[0].recovered_without_checkpoint = "yes"; }],
        ["negative first-response time", (v) => { v.rows[0].first_final_response_ms = -1; }],
        ["fractional commit time", (v) => { v.rows[0].commit_elapsed_ms = 0.5; }],
        ["bad scene hash", (v) => { v.rows[0].scene_frame_sha256 = "scene"; }],
        ["invalid nullable reason", (v) => { v.rows[0].construction_evidence_reason = {}; }],
        ["invented human assessment", (v) => { v.human_rubric = "passed"; }],
        ["claimed human count", (v) => { v.human_reviewed = 1; }],
        ["claimed quality acceptance", (v) => { v.quality_accepted = true; }],
        ["native setup hidden in scripted diagnostics", (v) => { v.native_load = {}; }],
        ["oversized private diagnostic", (v) => { v.rows[0].expected = "x".repeat(262144); }],
    ]) await bad("diagnostics", name, mutation);
    await check("diagnostics preserves recovered unknown values rather than claiming measured scene proof", () => {
        const v = diagnostics(); Object.assign(v.rows[0], { construction_evidence_status: "unavailable", construction_evidence_reason: "recovered_without_checkpoint", construction_matches: false, privacy_evidence_status: "unavailable", fallback: null, repairs: null, recovered_without_checkpoint: true, roles: 0, roles_known: false, elapsed_ms: 0, first_final_response_ms: null, commit_elapsed_ms: null, narrator_prompt_sha256: null, narrator_schema_sha256: null, scene_frame_sha256: null, passed: false });
        assert.deepEqual(decode.diagnostics(v), v);
    });
    for (const status of ["not_applicable_guard", "not_applicable_dependency"]) await check(`diagnostics preserves finite ${status} without inventing scene fields`, () => {
        const guard = status.endsWith("guard");
        const v = diagnostics(); Object.assign(v.rows[0], { phase: guard ? "failed" : "not_run_dependency", error: guard ? "AbilityUnavailable" : null,
            expected: guard ? "GuardRejected(AbilityUnavailable)" : "AcceptedCommand", passed: guard, actual_receipt_sha256: null,
            construction_evidence_status: status, construction_evidence_reason: null, construction_matches: guard,
            privacy_evidence_status: guard ? "not_applicable_guard" : "unavailable", fallback: null, repairs: null,
            narrator_prompt_sha256: null, narrator_schema_sha256: null, scene_frame_sha256: null, first_final_response_ms: null, commit_elapsed_ms: null, roles: 0, elapsed_ms: 0 });
        assert.deepEqual(decode.diagnostics(v), v);
    });
    for (const version of [1, 2]) await check(`old${version} cannot accept a V3-only field`, () => { const v = prepared(version); v.source_binding = SOURCE; finiteWire(() => decode.prepared(v)); });

    // These are unknown real JS objects, never claimed to arise from JSON.parse.
    for (const version of [1, 2, 3]) for (const kind of ["prepared", "summary", "diagnostics"]) {
        for (const mode of ["accessor", "toJSON", "inherited", "nonenumerable", "symbol", "undefined", "nonfinite", "cycle", "bigint"]) await check(`${kind}${version}: hostile ${mode} fails without accessor/toJSON invocation`, () => {
            const value = factories[kind](version); let invoked = 0;
            if (mode === "accessor") Object.defineProperty(value, "kind", { enumerable: true, get() { invoked++; return factories[kind](version).kind; } });
            if (mode === "toJSON") Object.defineProperty(value, "toJSON", { value() { invoked++; return factories[kind](version); } });
            if (mode === "inherited") Object.setPrototypeOf(value, { inherited: PRIVATE });
            if (mode === "nonenumerable") Object.defineProperty(value, "privateHidden", { value: PRIVATE });
            if (mode === "symbol") value[Symbol("private")] = PRIVATE;
            if (mode === "undefined") value.privateUndefined = undefined;
            if (mode === "nonfinite") value.version = Number.NaN;
            if (mode === "cycle") value.loop = value;
            if (mode === "bigint") value.privateBigInt = 1n;
            finiteWire(() => decode[kind](value)); assert.equal(invoked, 0);
        });
    }
    for (const mode of ["hole", "extra", "accessor", "symbol"]) await check(`prepared3: hostile arm array ${mode} is not silently normalized`, () => {
        const value = prepared(); let invoked = 0;
        if (mode === "hole") delete value.arms[0];
        if (mode === "extra") value.arms.private = PRIVATE;
        if (mode === "symbol") value.arms[Symbol("hidden")] = PRIVATE;
        if (mode === "accessor") { const original = value.arms[0]; Object.defineProperty(value.arms, "0", { enumerable: true, get() { invoked++; return original; } }); }
        finiteWire(() => decode.prepared(value)); assert.equal(invoked, 0);
    });

    function evidence(request = { kind: "receipt", observer: omni }, arm = "left", version = 3) {
        const item = summary(version).arms[arm === "left" ? 0 : 1];
        let body;
        if (request.kind === "query") body = { kind: "query", page: { version: 2, scope: clone(item.scope), head: request.edge === "before" ? item.before_head : item.after_head,
            revision: request.edge === "before" ? item.before_head : item.after_head, story_time: 1, observer: clone(request.observer), view: request.view,
            privacy: request.observer.kind === "player" ? "player_visible" : request.observer.kind === "character" ? "private_character" : "private_omniscient", status: "supported", total: 0, rows: [], next_cursor: null, unsupported: [] } };
        else if (request.kind === "receipt") body = { kind: "receipt", receipt: { synthetic_canary: PRIVATE } };
        else if (request.kind === "capture") body = { kind: "capture", capture: { synthetic_canary: PRIVATE } };
        else body = { kind: "outputs", outputs: [{ role: "narrator", bytes: 5, sha256: RECEIPT, text: "hello" }] };
        return { version: 1, binding: READ, row: { turn: selection.turn, arm }, scope: clone(item.scope), before_head: item.before_head, after_head: item.after_head,
            observer: clone(request.observer), edge: request.kind === "query" ? request.edge : request.kind === "receipt" ? "after" : null, read_only: true, generation_grant: false, body };
    }
    const decodeEvidence = (value, request = { kind: "receipt", observer: omni }, arm = "left") => m.checkedSelectedEvidence(wrap("selected_evidence", "evidence", value), READ_TOKEN, summary(), arm, request);
    await check("evidence remains wrapper1 with selected3 read binding and exact scope/head", () => assert.deepEqual(decodeEvidence(evidence()), evidence()));
    for (const [name, mutate] of [
        ["source snapshot binding", (v) => { v.binding = SOURCE; }], ["resume manifest binding", (v) => { v.binding = SELECTED; }],
        ["foreign story", (v) => { v.scope.story = "other"; }], ["foreign branch", (v) => { v.scope.branch = "other"; }],
        ["different turn", (v) => { v.row.turn = "courier-06"; }], ["different arm", (v) => { v.row.arm = "right"; }],
        ["different before head", (v) => { v.before_head++; }], ["different after head", (v) => { v.after_head++; }],
        ["different observer", (v) => { v.observer = player; }], ["generation grant", (v) => { v.generation_grant = true; }],
        ["different receipt edge", (v) => { v.edge = "before"; }],
    ]) await check(`evidence rejects ${name}`, () => { const v = evidence(); mutate(v); finiteWire(() => decodeEvidence(v)); });
    for (const observer of [player, mira]) await check(`evidence ${observer.kind}: filtered query allowed but raw receipt rejected locally`, () => {
        const request = { kind: "query", edge: "before", view: "knowledge", observer };
        assert.deepEqual(decodeEvidence(evidence(request), request), evidence(request));
        finiteWire(() => decodeEvidence(evidence({ kind: "receipt", observer }), { kind: "receipt", observer }));
    });

    function status(clientId, phase = "completed", version = 3, patch = {}) {
        return { version: 1, kind: "selected_evaluation", client_id: clientId, operation_id: 7, phase, running: ["preparing", "running", "cancelling"].includes(phase),
            lane: "scripted_baseline", plan_token: PLAN_TOKEN, run_id: phase === "prepared" || phase === "preparing" ? null : RUN,
            run_token: phase === "completed" || phase === "paused" ? READ_TOKEN : null, binding: phase === "completed" || phase === "paused" ? READ : null,
            prepared: prepared(version), error: null, cause: null, cleanup_required: false, ...patch };
    }
    function closed(clientId) { return status(clientId, "closed", 3, { lane: null, plan_token: null, run_id: null, run_token: null, binding: null, prepared: null }); }
    function fixture(version = 3) {
        const calls = [], hooks = new Map(), records = new Map(), observedErrors = [];
        const c = new m.SelectedEvaluationController(async (command, args) => {
            assert.equal(command, "evaluation_selected"); assert.deepEqual(Object.keys(args).sort(), ["action", "request"]);
            assert.equal(typeof args.request, "string"); assert(Buffer.byteLength(args.request) <= 4096);
            const body = JSON.parse(args.request), action = args.action; calls.push({ action, body });
            if (hooks.has(action)) return hooks.get(action)(body);
            if (action === "prepare") { const result = status(body.clientId, "prepared", version); records.set(body.clientId, result); return clone(result); }
            if (action === "open" || action === "resume") { const result = status(body.clientId, "completed", version); records.set(body.clientId, result); return clone(result); }
            if (action === "start") { const result = status(body.clientId, "completed", version, { run_token: null, binding: null }); records.set(body.clientId, result); return clone(result); }
            if (action === "status") return clone(records.get(body.clientId) ?? status(body.clientId, "completed", version));
            if (action === "cancel") { const result = status(body.clientId, "failed", version, { running: false, error: "Cancelled", plan_token: null }); records.set(body.clientId, result); return result; }
            if (action === "close") { const result = closed(body.clientId); records.set(body.clientId, result); return result; }
            if (action === "summary") return wrap("selected_summary", "summary", summary(version));
            if (action === "diagnostics") return wrap("selected_diagnostics_result", "diagnostics", diagnostics(version));
            if (action === "evidence") return wrap("selected_evidence", "evidence", evidence(body.request, body.arm, version));
            if (action === "catalog") return { version: 1, kind: "selected_catalog", runs: [{ run_id: RUN, created: 1, lane: "scripted_baseline", selection: clone(selection) }] };
            if (action === "cleanup_status" || action === "retry_cleanup") return { version: 1, kind: "selected_cleanup", cleanup_required: false, running: false, error: null };
            throw Error("UnexpectedSyntheticAction");
        }, (error) => { observedErrors.push(error); });
        controllers.add(c); c.setContext("scene-selected-current-context", true); c.setObserver(omni);
        return { c, calls, hooks, records, observedErrors, version };
    }
    async function opened(f) { await f.c.open(RUN); assert.equal(f.c.get().error, null); await f.c.loadSummary(); assert.equal(f.c.get().error, null); assert.equal(f.c.get().summary.version, f.version); }
    for (const version of [1, 2, 3]) await check(`controller${version}: opened read and diagnostics use exact read binding; publications deeply frozen`, async () => {
        const f = fixture(version); await opened(f); await f.c.readDiagnostics();
        assert.equal(f.c.get().diagnostics.version, version); assert.equal(f.c.get().error, null); frozenTree(f.c.get());
        for (const call of f.calls.filter((v) => ["summary", "diagnostics"].includes(v.action))) assert.equal(call.body.binding, READ);
    });
    for (const version of [1, 2, 3]) await check(`controller${version}: optional expected source protocol is presentation-only`, async () => {
        const f = fixture(version); await f.c.prepare(source, row, "scripted_baseline", version + 1);
        assert.equal(f.c.get().error, null); assert.equal(f.c.get().status.prepared.version, version);
        const prepareCall = f.calls.find((v) => v.action === "prepare");
        assert.deepEqual(Object.keys(prepareCall.body).sort(), ["arm", "binding", "clientId", "lane", "readerClientId", "runToken", "turnId"]);
        assert.equal(prepareCall.body.binding, SOURCE); assert.equal(prepareCall.body.runToken, SOURCE_TOKEN);
        assert.equal(f.c.sourceNeedsRefresh(source), true); assert.equal(f.c.sourceNeedsRefresh({ ...source, runToken: READ_TOKEN }), false);
        assert(!f.calls.some((v) => v.action === "start")); frozenTree(f.c.get());
    });
    await check("controller3: old three-argument prepare stays supported and source binding still checked", async () => {
        const f = fixture(); await f.c.prepare(source, row, "scripted_baseline"); assert.equal(f.c.get().error, null); assert.equal(f.c.get().status.prepared.source_binding, SOURCE);
    });
    for (const [name, mutate] of [
        ["wrong selected version for source4", (v) => { v.prepared = prepared(2); }],
        ["wrong source binding", (v) => { v.prepared.source_binding = READ; }],
        ["resume binding substituted as source", (v) => { v.prepared.source_binding = SELECTED; }],
        ["wrong selected turn", (v) => { v.prepared.selection.turn = "courier-06"; }],
        ["wrong clicked arm", (v) => { v.prepared.selection.clicked_arm = "left"; }],
        ["wrong requested lane", (v) => { v.lane = "approved_native"; }],
        ["wrong client", (v) => { v.client_id = CLIENT; }],
    ]) await check(`controller prepare rejects ${name}`, async () => {
        const f = fixture(); f.hooks.set("prepare", (body) => { const value = status(body.clientId, "prepared"); mutate(value); return value; });
        await f.c.prepare(source, row, "scripted_baseline", 4); assert.equal(f.c.get().error, "SelectedEvaluationWire"); assert.notEqual(f.c.get().status?.phase, "prepared");
    });
    for (const expected of [2, 3]) await check(`controller preparation cannot use returned V3 as its own expectation for source${expected}`, async () => {
        const f = fixture(); await f.c.prepare(source, row, "scripted_baseline", expected); assert.equal(f.c.get().error, "SelectedEvaluationWire");
    });
    for (const hint of [0, 5, null, "4", {}, Number.NaN]) await check(`controller rejects unsupported expected-source hint ${String(hint)}`, async () => {
        const f = fixture(); await f.c.prepare(source, row, "scripted_baseline", hint); assert.equal(f.c.get().error, "SelectedEvaluationWire"); assert(!f.calls.some((v) => v.action === "prepare"));
    });
    for (const [name, mutation] of [
        ["version", (v) => { Object.assign(v, summary(2)); }], ["head", (v) => { v.arms[0].before_head++; }],
        ["scope", (v) => { v.arms[0].scope.branch = "other"; }], ["turn", (v) => { v.selection.turn = "courier-06"; }],
        ["clicked arm", (v) => { v.selection.clicked_arm = "left"; }], ["index", (v) => { v.selection.index = 5; }],
        ["read binding", (v) => { v.binding = SELECTED; }],
    ]) await check(`controller summary rejects wrong ${name} against retained prepared identity`, async () => {
        const f = fixture(); await f.c.open(RUN); f.hooks.set("summary", () => { const value = summary(); mutation(value); return wrap("selected_summary", "summary", value); });
        await f.c.loadSummary(); assert.equal(f.c.get().summary, null); assert.equal(f.c.get().error, "SelectedEvaluationWire");
    });
    await check("controller start is explicit/once; completed resume sends source/read tokens but no renderer manifest binding", async () => {
        const f = fixture(); await f.c.prepare(source, row, "scripted_baseline", 4); await f.c.start(); await f.c.start();
        assert.equal(f.calls.filter((v) => v.action === "start").length, 1); assert.equal(f.c.get().status.phase, "completed");
        assert.equal(f.c.get().status.run_token, null); await f.c.loadSummary();
        assert(!f.calls.some((v) => ["summary", "evidence", "diagnostics", "open"].includes(v.action)), "execution itself grants no read capability or implicit open");
        await f.c.open(RUN); await f.c.loadSummary(); await f.c.resume({ ...source, runToken: "77777777-7777-7777-7777-777777777777" });
        const resume = f.calls.find((v) => v.action === "resume"); assert(resume);
        assert.deepEqual(Object.keys(resume.body).sort(), ["clientId", "readerClientId", "runToken", "sourceBinding", "sourceToken"]);
        assert.equal(resume.body.runToken, READ_TOKEN); assert.equal(resume.body.sourceBinding, SOURCE);
        assert.equal(f.c.get().error, null); assert.equal(f.calls.filter((v) => v.action === "start").length, 1);
    });
    await check("controller pending preparation refuses duplicate client admission and observer does not cancel it", async () => {
        const f = fixture(), hold = gate(); let current;
        f.hooks.set("prepare", (body) => { current = body; return hold.promise; });
        const operation = f.c.prepare(source, row, "scripted_baseline", 4); await flush();
        assert(current); const client = f.c.get().clientId; f.c.setObserver(mira);
        await f.c.prepare(source, row, "scripted_baseline", 4); assert.equal(f.calls.filter((v) => v.action === "prepare").length, 1);
        assert(!f.calls.some((v) => v.action === "cancel" || v.action === "close")); assert.equal(f.c.get().clientId, client);
        hold.resolve(status(current.clientId, "prepared")); await operation; assert.equal(f.c.get().status.phase, "prepared");
    });
    await check("controller late committed reply wins a same-operation cancellation acknowledgement", async () => {
        const f = fixture(), poll = gate(), entered = gate(); let preparing;
        f.hooks.set("prepare", (body) => { preparing = body; return status(body.clientId, "running", 3, { run_id: RUN, plan_token: null }); });
        f.hooks.set("status", () => { entered.resolve(true); return poll.promise; });
        const operation = f.c.prepare(source, row, "scripted_baseline", 4);
        // Wait for the real controller's finite 300ms status timer to dispatch;
        // no transport reply exists to be stale until this actual invocation.
        assert.equal(await entered.promise, true);
        assert.equal(f.c.get().status.phase, "running"); await f.c.cancel();
        poll.resolve(status(preparing.clientId, "completed", 3, { plan_token: null, run_token: null, binding: null }));
        await operation;
        assert.equal(f.c.get().status.phase, "completed");
    });
    await check("controller native refusal is finite, consumes source freshness, and never starts scripted fallback", async () => {
        const f = fixture(); f.hooks.set("prepare", (body) => status(body.clientId, "failed", 3, { lane: "approved_native", plan_token: null, run_id: null, prepared: null, error: "NativeUnavailable" }));
        await f.c.prepare(source, row, "approved_native", 4);
        assert.equal(f.c.get().error, "NativeUnavailable"); assert.equal(f.c.sourceNeedsRefresh(source), true);
        assert(!f.calls.some((v) => v.action === "start" || v.action === "resume"));
    });
    for (const stage of ["pending", "reply", "final"]) await check(`controller reentrant context retirement at ${stage} cannot publish old prepared identity`, async () => {
        const f = fixture(); let changed = false;
        f.c.subscribe(() => {
            const s = f.c.get();
            if (!changed && ((stage === "pending" && s.pending?.action === "prepare") || (stage === "reply" && s.status?.phase === "prepared") || (stage === "final" && s.status?.phase === "prepared" && s.pending === null && !s.busy))) {
                changed = true; f.c.setContext("replacement-context", true);
            }
        });
        await f.c.prepare(source, row, "scripted_baseline", 4); await flush(); assert(changed);
        assert.equal(f.c.get().context, "replacement-context"); assert.equal(f.c.get().status, null); assert.equal(f.c.get().summary, null); assert.equal(f.c.get().evidence, null);
        if (stage === "pending") assert(!f.calls.some((v) => v.action === "prepare"));
    });
    await check("controller late prepared completion closes captured old client and preserves replacement context", async () => {
        const f = fixture(), hold = gate(); let body;
        f.hooks.set("prepare", (v) => { body = v; return hold.promise; });
        const pending = f.c.prepare(source, row, "scripted_baseline", 4); await flush(); assert(body);
        f.c.setContext("different-session-and-head", true); hold.resolve(status(body.clientId, "prepared")); await pending; await flush();
        assert.equal(f.c.get().context, "different-session-and-head"); assert.equal(f.c.get().status, null);
        assert(f.calls.some((v) => v.action === "close" && v.body.clientId === body.clientId));
    });
    for (const retire of ["observer", "context", "dispose"]) await check(`controller read ${retire} change fences delayed private evidence`, async () => {
        const f = fixture(); await opened(f); const hold = gate(); f.hooks.set("evidence", () => hold.promise);
        const p = f.c.readEvidence("left", { kind: "receipt", observer: omni }); await flush();
        const client = f.c.get().clientId;
        if (retire === "observer") f.c.setObserver(mira); else if (retire === "context") f.c.setContext("read-replacement", true); else f.c.dispose();
        hold.resolve(wrap("selected_evidence", "evidence", evidence())); await p;
        assert.equal(f.c.get().evidence, null); assert.equal(f.c.get().diagnostics, null);
        if (retire === "observer") { assert.equal(f.c.get().clientId, client); assert(!f.calls.some((v) => v.action === "cancel" || v.action === "close")); }
    });
    await check("controller actor raw/diagnostic reads are local no-ops, filtered query uses the actual lens", async () => {
        const f = fixture(); await opened(f); f.c.setObserver(mira); const before = f.calls.length;
        await f.c.readEvidence("left", { kind: "receipt", observer: mira }); await f.c.readDiagnostics(); assert.equal(f.calls.length, before);
        await f.c.readEvidence("left", { kind: "query", edge: "before", view: "knowledge", observer: mira });
        assert.equal(f.c.get().evidence.observer.id, "mira"); assert.equal(f.c.get().evidence.generation_grant, false);
    });
    await check("controller diagnostics reentrant lens change on pending prevents dispatch", async () => {
        const f = fixture(); await opened(f); let changed = false;
        f.c.subscribe(() => { if (!changed && f.c.get().pending?.action === "diagnostics") { changed = true; f.c.setObserver(player); } });
        await f.c.readDiagnostics(); assert(changed); assert(!f.calls.some((v) => v.action === "diagnostics")); assert.equal(f.c.get().diagnostics, null);
    });
    await check("controller unknown start acknowledgement does not duplicate start and requires same status recovery", async () => {
        const f = fixture(); await f.c.prepare(source, row, "scripted_baseline", 4);
        f.hooks.set("start", () => { throw Error("EvaluationIo"); }); await f.c.start();
        assert.equal(f.c.get().uncertain, true); await f.c.start(); assert.equal(f.calls.filter((v) => v.action === "start").length, 1);
        f.hooks.set("status", (body) => status(body.clientId, "completed", 3, { run_token: null, binding: null })); await f.c.status();
        assert.equal(f.c.get().status.phase, "completed"); assert.equal(f.c.get().uncertain, false);
    });
    await check("controller cleanup remains queryable after Lab permission loss and blocks new preparation while retained", async () => {
        const f = fixture(); f.c.setContext("permission-lost", false);
        f.hooks.set("cleanup_status", () => ({ version: 1, kind: "selected_cleanup", cleanup_required: true, running: false, error: "Cleanup" }));
        await f.c.cleanupStatus(); assert.equal(f.c.get().cleanup.cleanup_required, true); await f.c.retryCleanup();
        assert(f.calls.some((v) => v.action === "retry_cleanup"));
        f.hooks.set("cleanup_status", () => ({ version: 1, kind: "selected_cleanup", cleanup_required: true, running: false, error: "Cleanup" }));
        await f.c.cleanupStatus(); f.c.setContext("allowed-again", true); await f.c.prepare(source, row, "scripted_baseline", 4);
        assert(!f.calls.some((v) => v.action === "prepare"));
    });

    function textOf(value) {
        if (value === null || value === undefined || typeof value === "boolean") return "";
        if (typeof value === "string" || typeof value === "number") return String(value);
        if (Array.isArray(value)) return value.map(textOf).join("");
        return value?.props ? textOf(value.props.children) : "";
    }
    function button(label) { const found = m.nodes.find((v) => v.type === "button" && textOf(v) === label); assert(found, `ActualButton:${label}`); return found; }
    function laneSelect() { const found = m.nodes.find((v) => v.type === "select" && v.props["aria-label"] === "Selected experiment lane"); assert(found); return found; }
    function render(f, props = {}) {
        m.nodes.length = 0; m.hooks.active = null;
        const value = m.renderToStaticMarkup(m.createElement(m.SelectedEvaluationView, { controller: f.c, source, row, observer: omni, sourceProtocolVersion: 4, ...props }));
        html.push(value); return value;
    }
    function hookView(f, initialProps = {}) {
        const frame = { values: [], dependencies: [], effects: [], cursor: 0, effectCursor: 0, dirty: false };
        let props = { controller: f.c, source, row, observer: omni, sourceProtocolVersion: 4, ...initialProps };
        const draw = (patch = {}) => {
            props = { ...props, ...patch }; frame.cursor = 0; frame.effectCursor = 0; frame.effects = []; frame.dirty = false;
            m.nodes.length = 0; m.hooks.active = frame;
            let element;
            try { element = m.SelectedEvaluationView(props); } finally { m.hooks.active = null; }
            const value = m.renderToStaticMarkup(element); html.push(value); return value;
        };
        const effects = () => { const pending = [...frame.effects]; frame.effects = []; for (const effect of pending) effect(); };
        return { frame, draw, effects };
    }
    await check("actual panel source4 has disabled native lane, enabled fake scripted prepare and passes expected4", async () => {
        const f = fixture(); const value = render(f);
        const select = laneSelect(); assert.equal(select.props.value, "scripted_baseline");
        const native = m.nodes.find((v) => v.type === "option" && v.props.value === "approved_native"); assert(native && native.props.disabled);
        assert.match(value, /native[\s\S]{0,140}unavailable|unavailable[\s\S]{0,140}native/i);
        const prepareButton = button("Prepare selected case"); assert(!prepareButton.props.disabled); prepareButton.props.onClick(); await flush();
        assert.equal(f.calls.filter((v) => v.action === "prepare").length, 1); assert.equal(f.c.get().status.prepared.version, 3);
        const badVersion = fixture(2); render(badVersion); button("Prepare selected case").props.onClick(); await flush();
        assert.equal(badVersion.c.get().error, "SelectedEvaluationWire", "actual panel must supply expectedSourceProtocol4");
    });
    await check("actual panel source2/3 retain native lane option and original source-version preparation", async () => {
        for (const protocol of [2, 3]) {
            const f = fixture(protocol - 1); render(f, { sourceProtocolVersion: protocol });
            const native = m.nodes.find((v) => v.type === "option" && v.props.value === "approved_native"); assert(native && !native.props.disabled);
            button("Prepare selected case").props.onClick(); await flush(); assert.equal(f.c.get().error, null);
        }
    });
    await check("actual panel stale native lane never silently sends scripted work before effect normalization", async () => {
        const f = fixture(), view = hookView(f, { sourceProtocolVersion: 3 }); view.draw(); view.effects();
        laneSelect().props.onChange({ target: { value: "approved_native" } }); view.draw(); assert.equal(laneSelect().props.value, "approved_native");
        view.draw({ sourceProtocolVersion: 4 }); const first = button("Prepare selected case");
        if (laneSelect().props.value === "approved_native") {
            if (!first.props.disabled) first.props.onClick(); await flush(); assert(!f.calls.some((v) => v.action === "prepare"));
        } else assert.equal(laneSelect().props.value, "scripted_baseline", "a synchronously normalized display may already show its actual scripted lane");
        view.effects(); view.draw(); assert.equal(laneSelect().props.value, "scripted_baseline");
        const after = button("Prepare selected case"); assert(!after.props.disabled); after.props.onClick(); await flush();
        assert.equal(f.calls.find((v) => v.action === "prepare").body.lane, "scripted_baseline");
    });
    await check("actual panel fresh source token is required after a preparation consumes the old one", async () => {
        const f = fixture(); await f.c.prepare(source, row, "scripted_baseline", 4); await f.c.close(); render(f);
        assert(button("Prepare selected case").props.disabled); assert.match(html.at(-1), /matching source|source report|unavailable|refresh|choose/i);
        render(f, { source: { ...source, runToken: "88888888-8888-8888-8888-888888888888" } }); assert(!button("Prepare selected case").props.disabled);
    });
    await check("actual panel pending Start disables duplicate start and exposes exact pending state", async () => {
        const f = fixture(); await f.c.prepare(source, row, "scripted_baseline", 4); const hold = gate(); let body;
        f.hooks.set("start", (v) => { body = v; return hold.promise; }); render(f); button("Start prepared experiment").props.onClick(); await flush();
        const value = render(f); assert(button("Start prepared experiment").props.disabled); assert.match(value, /Pending:|Waiting|acknowledgement/);
        assert.equal(f.calls.filter((v) => v.action === "start").length, 1); hold.resolve(status(body.clientId, "completed", 3, { run_token: null, binding: null })); await flush();
    });
    await check("actual panel cancellation handler targets the current acknowledged operation only", async () => {
        const f = fixture(); f.hooks.set("prepare", (body) => status(body.clientId, "running", 3, { plan_token: null, run_id: RUN }));
        const pending = f.c.prepare(source, row, "scripted_baseline", 4); await flush(); render(f);
        const cancel = button("Cancel current operation"); assert(!cancel.props.disabled); cancel.props.onClick(); await flush();
        const call = f.calls.find((v) => v.action === "cancel"); assert(call); assert.equal(call.body.operationId, 7);
        assert.equal(call.body.clientId, f.c.get().clientId); render(f); assert(button("Cancel current operation").props.disabled);
        await pending; assert.equal(f.c.get().status.error, "Cancelled");
    });
    await check("actual panel close handler retires its current read body and client", async () => {
        const f = fixture(); await opened(f); await f.c.readEvidence("left", { kind: "receipt", observer: omni });
        const client = f.c.get().clientId; render(f); button("Close attempt / stop work").props.onClick(); await flush();
        assert(f.calls.some((v) => v.action === "close" && v.body.clientId === client));
        assert.equal(f.c.get().clientId, null); assert.equal(f.c.get().evidence, null); assert.equal(f.c.get().summary, null);
    });
    await check("actual panel V3 scene/finite privacy/recovery diagnostics remain explicit and escaped", async () => {
        const f = fixture(); await opened(f);
        f.hooks.set("diagnostics", () => { const value = diagnostics(); Object.assign(value.rows[0], { construction_evidence_status: "unavailable", construction_evidence_reason: "<img src=x onerror=alert(1)>", construction_matches: false, privacy_evidence_status: "unavailable", recovered_without_checkpoint: true, roles_known: false, roles: 0, first_final_response_ms: null, commit_elapsed_ms: null, fallback: null, repairs: null, narrator_prompt_sha256: null, narrator_schema_sha256: null, scene_frame_sha256: null, passed: false }); return wrap("selected_diagnostics_result", "diagnostics", value); });
        await f.c.readDiagnostics(); const value = render(f);
        assert.match(value, /Literal scene/i); assert.match(value, /Relevant memory scene/i); assert.match(value, /unavailable|not established/i);
        assert.match(value, /Unknown|not recovered/i); assert.match(value, /fake inference/i); assert.doesNotMatch(value, /Recent transcript baseline|Literal source units|Selected conversation suffix/);
        assert.doesNotMatch(value, /<img\s|onerror="/); assert(value.includes("&lt;img src=x onerror=alert(1)&gt;"), "the actual bounded construction reason must be visible as escaped text");
        assert.match(value, /repair/i); assert.match(value, /recovered|checkpoint/i);
        assert.match(value, /first final|first response/i); assert.match(value, /commit[\s\S]{0,50}(elapsed|time)|(elapsed|time)[\s\S]{0,50}commit/i);
    });
    await check("actual panel old versions keep distinct labels", async () => {
        for (const version of [1, 2]) { const f = fixture(version); await opened(f); await f.c.readDiagnostics(); const value = render(f, { sourceProtocolVersion: version + 1 }); assert.match(value, version === 1 ? /Recent transcript baseline/ : /Literal player conversation/); }
    });
    await check("actual panel actor prop hides old omniscient evidence before its effect runs", async () => {
        const f = fixture(); await opened(f); await f.c.readEvidence("left", { kind: "receipt", observer: omni }); assert.equal(f.c.get().evidence.body.receipt.synthetic_canary, PRIVATE);
        const value = render(f, { observer: mira }); assert.doesNotMatch(value, new RegExp(PRIVATE));
        assert.equal(f.c.get().observer.kind, "omniscient", "SSR did not run observer effect; render fence itself must hide private data");
    });
    await check("actual panel lost Lab grant keeps cleanup actions while removing private results", async () => {
        const f = fixture(); await opened(f); await f.c.readDiagnostics(); f.c.setContext("not-lab", false); const value = render(f);
        assert(button("Prepare selected case").props.disabled); assert(!button("Check worker cleanup").props.disabled);
        button("Check worker cleanup").props.onClick(); await flush(); assert(f.calls.some((v) => v.action === "cleanup_status"));
        assert.doesNotMatch(value, /Selected expected and actual results/);
    });
    await check("actual panel retained cleanup retry remains explicit after permission loss", async () => {
        const f = fixture(); f.c.setContext("not-lab", false);
        f.hooks.set("cleanup_status", () => ({ version: 1, kind: "selected_cleanup", cleanup_required: true, running: false, error: "Cleanup" }));
        await f.c.cleanupStatus(); render(f); const retry = button("Retry retained worker cleanup"); assert(!retry.props.disabled);
        retry.props.onClick(); await flush(); assert(f.calls.some((v) => v.action === "retry_cleanup")); assert.equal(f.c.get().cleanup.cleanup_required, false);
    });
    function readerState(protocol = 4, patch = {}) {
        return { clientId: READER, observer: omni, selected: row,
            source: { protocol_version: protocol, binding: SOURCE, rows: [], read_only: true, execution_available: false },
            status: { version: 1, kind: "comparison_reader", client_id: READER, phase: "ready", running: false, operation_id: 1, run_token: SOURCE_TOKEN, binding: SOURCE, error: null, read_only: true, execution_available: false }, ...patch };
    }
    function appSelection(f, state) {
        m.hooks.active = null; m.nodes.length = 0;
        const comparison = { get: () => state, subscribe: () => () => {} };
        const value = m.renderToStaticMarkup(m.createElement(m.SelectedSceneAppSelectionForReview, { comparison, selected: f.c })); html.push(value);
        const element = m.nodes.find((v) => v.type === m.SelectedEvaluationView); assert(element, "ActualAppSelectedViewElementRequired"); return element;
    }
    await check("actual App selection admits ready source4, forwards exact3-key identity and expected protocol", async () => {
        const f = fixture(), element = appSelection(f, readerState());
        assert.deepEqual(element.props.source, source); assert.equal(element.props.sourceProtocolVersion, 4); assert.notEqual(element.props.sourceUnavailable, true);
        assert.deepEqual(element.props.row, row); assert.deepEqual(element.props.observer, omni);
        button("Prepare selected case").props.onClick(); await flush(); assert.equal(f.c.get().status.prepared.version, 3); assert.equal(f.c.get().error, null);
    });
    for (const protocol of [2, 3]) await check(`actual App old source${protocol} still forwards original identity`, () => {
        const f = fixture(protocol - 1), element = appSelection(f, readerState(protocol)); assert.deepEqual(element.props.source, source); assert.equal(element.props.sourceProtocolVersion, protocol);
    });
    for (const [name, mutate] of [
        ["missing token", (s) => { s.status.run_token = null; }], ["missing source", (s) => { s.source = null; }],
        ["missing reader client", (s) => { s.clientId = null; }], ["not ready", (s) => { s.status.phase = "opening"; s.status.running = true; }],
    ]) await check(`actual App incomplete source4 ${name} cannot prepare`, () => {
        const f = fixture(), state = readerState(); mutate(state); const element = appSelection(f, state); assert.equal(element.props.source, null); assert(button("Prepare selected case").props.disabled);
    });

    for (const c of controllers) c.dispose(); controllers.clear(); await flush();
    await report();
}
await main();

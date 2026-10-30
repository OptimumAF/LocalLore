// Independent checkpoint FIRST at21eed8ce. SOURCE AUTHOR UNCOMPILED / UNRUN.
// Actual semantic/capture closures, same-realm TS stripping; fixed controller,
// DOM, frame and IPC doubles only. No bundle, file writes, child or app execution.
import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import { createHash } from "node:crypto";
import { stripTypeScriptTypes } from "node:module";
import vm from "node:vm";

assert.equal(process.argv.length, 2, "ClosedCheckpointReviewArguments");
const sha = (value) => createHash("sha256").update(value).digest("hex");
const results = [], setup = [], sourceHashes = {};
let factory;
try {
    const journey = await readFile(new URL("ui/domain2-fork-native-journeys.ts", import.meta.url), "utf8");
    const rust = await readFile(new URL("src-tauri/src/harness.rs", import.meta.url), "utf8");
    sourceHashes.journey = sha(journey);
    sourceHashes.rust = sha(rust);
    const extract = (first, next) => {
        const start = journey.indexOf(first), end = journey.indexOf(next, start + first.length);
        assert(start >= 0 && end > start && journey.indexOf(first, start + first.length) < 0, "UniqueActualClosure");
        return journey.slice(start, end);
    };
    const semantic = extract("    const semantic = () => {", "    const oracle = async (label: string) => {");
    const capture = extract("    const capture = async (label: string, failure = false) => {", "    const stateReport = (passed: boolean, error?: string) => (");
    sourceHashes.semanticClosure = sha(semantic);
    sourceHashes.captureClosure = sha(capture);
    // This is source/interface evidence, not execution of Rust or a copied guard.
    assert.match(rust, /value\.get\("synthetic"\) != Some\(&Value::Bool\(true\)\)/);
    assert.match(rust, /snapshot && value\.get\("uiRevision"\)\.and_then\(Value::as_u64\)\.is_none\(\)/);
    factory = vm.compileFunction(stripTypeScriptTypes(`${semantic}\n${capture}`, { mode: "strip" }) + "\nreturn {semantic,capture};", [
        "c", "f", "v2", "document", "panel", "innerWidth", "innerHeight", "navigator", "errors", "MODE", "text",
        "HTMLSelectElement", "HTMLInputElement", "check", "LABELS", "captures", "targets", "structural", "timelineContext",
        "frames", "geometry", "scrollX", "scrollY", "fonts", "checks", "invoke", "object", "receipts", "refs",
    ]);
} catch (error) {
    setup.push({ classification: "UNRUN_SETUP", error: String(error?.message ?? error).slice(0, 300) });
}

function fixture({ play = null, playV2 = null, selected = null } = {}) {
    const state = { play, playV2, view: "lab", observer: "omniscient", pending: null, visibleError: null, textScale: 1 };
    const fork = { busy: false, status: "idle", boundaryBusy: false, boundaryError: null, error: null, operation: null };
    const region = { innerText: "Synthetic selected context", contains: (node) => node === target, querySelectorAll: () => [], querySelector: () => null, scrollWidth: 800, clientWidth: 800 };
    const target = { scrollIntoView() {} };
    const captures = [], receipts = [], refs = [], calls = [];
    const c = { get: () => state, selected: () => selected, receipt: () => null };
    const document = { querySelector: () => null, activeElement: null, documentElement: { scrollWidth: 800 } };
    const api = factory(c, { get: () => fork }, { get: () => ({ pending: null, error: null, snapshot: null, history: null }) },
        document, () => region, 800, 600, { userAgent: "Synthetic-No-WebView" }, { snapshot: () => [] }, "domain2_fork_v1",
        (node) => node.innerText ?? "", class {}, class {}, (condition, name) => assert(condition, name), ["d08-fork-catalog"], captures,
        () => [{ name: "boundary-selector", node: target }], JSON.stringify, () => ({ session: selected?.id ?? null }), async () => {},
        () => ({ positive: true, visible: true, hits: [true, true, true] }), 0, 0, [], [],
        async (name, args) => {
            assert.equal(name, "harness_checkpoint");
            assert.deepEqual(Object.keys(args), ["label", "snapshot"]);
            calls.push(args);
            return { rendering: "native-webview2" }; // Synthetic transport return, not native evidence.
        }, (value) => value, receipts, refs);
    return { ...api, calls, captures, receipts, refs };
}
const chosen = { id: "synthetic-session-71", scope: { story: "synthetic-fork", branch: "authored" }, revision: 7 };
function compatible(value, uiRevision, canonicalRevision) {
    assert.equal(value.synthetic, true);
    assert(Number.isSafeInteger(value.uiRevision) && value.uiRevision >= 0, "CheckpointUIRevisionCompatibleWithRustU64");
    assert.equal(value.uiRevision, uiRevision);
    assert.equal(value.revision, canonicalRevision, "CanonicalRevisionRemainsSeparate");
    assert.equal(value.mode, "domain2_fork_v1");
}
const cases = [
    ["legacy-play-revision-precedes-selected-fallback", () => {
        const s = fixture({ play: { revision: 31 }, selected: chosen }).semantic();
        compatible(s, 31, 31);
        assert.deepEqual(s.selectedStory, chosen.scope);
        assert.equal(s.session, chosen.id);
    }],
    ["domain2-play-revision-precedes-selected-fallback", () => {
        compatible(fixture({ playV2: { revision: 12 }, selected: chosen }).semantic(), 12, 12);
    }],
    ["selected-only-ui-fallback-does-not-invent-canonical-state", () => {
        const s = fixture({ selected: chosen }).semantic();
        compatible(s, 7, null);
        assert.deepEqual(s.selectedStory, chosen.scope);
        assert.equal(s.session, chosen.id);
    }],
    ["no-selection-ui-zero-sentinel-retains-unavailable-canonical-state", () => {
        const s = fixture().semantic();
        compatible(s, 0, null);
        assert.equal(s.selectedStory, null);
        assert.equal(s.session, null);
    }],
    ["actual-normal-and-failure-capture-pass-semantic-snapshot-to-fixed-ipc", async () => {
        const f = fixture({ playV2: { revision: 13 }, selected: chosen });
        await f.capture("d08-fork-catalog");
        await f.capture("d08-fork-failure", true);
        assert.deepEqual(f.calls.map((row) => row.label), ["d08-fork-catalog", "d08-fork-failure"]);
        for (const row of f.calls) {
            compatible(row.snapshot, 13, 13);
            assert.deepEqual(row.snapshot.selectedStory, chosen.scope);
            assert.equal(row.snapshot.session, chosen.id);
            assert(Buffer.byteLength(JSON.stringify(row.snapshot)) <= 262144);
            assert(Buffer.byteLength(JSON.stringify(row.snapshot, null, 2)) <= 262144);
        }
        assert.equal(f.refs.length, 1, "FailureDoesNotFabricateSuccessfulCheckpointReference");
        assert.equal(f.refs[0].label, "d08-fork-catalog");
    }],
];
for (const [name, run] of cases) {
    if (!factory) { results.push({ name, status: "UNRUN_SETUP" }); continue; }
    try { await run(); results.push({ name, status: "PASS" }); }
    catch (error) { results.push({ name, status: "FAIL", error: String(error?.message ?? error).slice(0, 300) }); }
}
const report = {
    kind: "d08_domain2_fork_checkpoint_independent_first_v1", authored: cases.length,
    executed: results.filter((row) => row.status !== "UNRUN_SETUP").length,
    passed: results.filter((row) => row.status === "PASS").length,
    failed: results.filter((row) => row.status === "FAIL").length,
    setup, results, sourceHashes,
    limits: ["Author UNRUN; no app retry or resource admission", "Actual semantic/capture JS with synthetic controllers/DOM/IPC, no Rust/native/WebView/render qualification", "Rust guard source evidence only; no weakening or copied canonical validator", "No files written, bundles, children, fixtures or private state injection"],
};
const output = JSON.stringify(report);
assert(Buffer.byteLength(output) + 1 <= 8192, "BoundedEightKiBReport");
console.log(output);
process.exitCode = setup.length ? 2 : report.failed ? 1 : 0;

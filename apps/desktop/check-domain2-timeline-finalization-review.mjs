// Independent source FIRST at 32e854b3; source author UNCOMPILED / UNRUN.
// Execution remains stopped until separate owner reconciliation. Fixed synthetic
// metadata/invoke doubles only: no app, process control, original capture/file
// rewrite, native IPC, Rust serialization, model, SDK or desktop operation.
import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import { createHash } from "node:crypto";
import { build, transform } from "esbuild";
import { fileURLToPath } from "node:url";
import path from "node:path";
import vm from "node:vm";

assert.equal(process.argv.length, 2, "ClosedBrowserFinalizationReviewArguments");
const root = fileURLToPath(new URL(".", import.meta.url));
const MODE = "domain2_timeline_browser_v1", CAP = 262144;
const LABELS = ["catalog", "root", "child", "observer", "enlarged-wide", "enlarged-narrow"].map((s) => `d08-browser-${s}`);
const moduleName = "ui/domain2-timeline-browser-finalization.ts", journeyName = "ui/domain2-timeline-browser-native-journeys.ts";
const sha = (value) => createHash("sha256").update(value).digest("hex");
const clone = (value) => structuredClone(value);
const tests = [], results = [], setup = [], source = {};
let api = null, moduleFailure = null, journeyFailure = null, rosterSource = "", finishSource = "", captureSource = "";
const test = (requires, name, run) => tests.push({ requires, name, run });
const bytes = (value, pretty = false) => Buffer.byteLength(JSON.stringify(value, null, pretty ? 2 : undefined), "utf8");
const checkpoints = (length = 6, count = 16) => LABELS.slice(0, length).map((label) => ({ label, count }));
const summary = (rows) => ({ retainedInCheckpoints: true, total: rows.reduce((n, row) => n + row.count, 0),
    checkpoints: rows.map((row) => ({ label: row.label, count: row.count, json: `${row.label}.json` })) });
const report = (passed = true, extra = {}) => ({ synthetic: true, mode: MODE, passed, checks: ["fixed-synthetic-check"],
    fontMeasurements: [{ label: "synthetic-font", px: 15 }], calls: [], baseline: { synthetic: "before" }, finalOracle: { synthetic: "after" }, ...extra });
const fallback = (failureCategory) => ({ synthetic: true, mode: MODE, passed: false, originalPassed: false,
    detailReportUnavailable: true, failureCategory, noFinalStateProof: true });
function fixedInvoke(behavior = () => undefined) {
    const calls = [];
    return { calls, async invoke(name, args) {
        calls.push({ name, args: clone(args) }); return await behavior(calls.length, name, args);
    } };
}
function boundCalls(calls) {
    assert(calls.length >= 1 && calls.length <= 2);
    for (const item of calls) {
        assert.equal(item.name, "harness_finish"); assert.deepEqual(Object.keys(item.args), ["report"]);
        assert(bytes(item.args.report) <= CAP && bytes(item.args.report, true) <= CAP, "BothEncodingBoundsBeforeEveryFixedIPC");
    }
}
function rejected(action, category) { assert.throws(action, (error) => error?.message === category); }
const host = (op, sequence = 1) => ({ channel: "host", command: { op }, nativeAction: null,
    sequence, settled: true, error: null, replySha256: null, deliveryDropped: false });
const native = (op, sequence = 1) => ({ ...host("unused", sequence), channel: "native", command: null, nativeAction: op });
const hostAllowed = ["workspace", "branches", "resume", "open", "close", "play_snapshot", "play_snapshot_v2", "inspection_query", "inspect", "trace_capture_revoke"];
const nativeAllowed = ["model_status", "inspection_storage", "capture_revoke"];
const forbiddenHost = ["create", "submit", "free_text", "prepare", "commit", "cancel", "grant_lab", "fork", "author_prepare", "author_apply", "trace_capture_read", "archive_export", "unknown"];
const forbiddenNative = ["capture_preview", "capture_save", "model_load", "model_import", "model_unload", "evaluation_start", "inspection_save", "author_commit", "capture_revoke/file", "unknown"];

function between(text, start, end) {
    const a = text.indexOf(start), b = text.indexOf(end, a + start.length);
    if (a < 0 || b <= a || text.indexOf(start, a + start.length) >= 0) throw Error(`UNRUN_SETUP:FixedClosureBoundary:${start}`);
    return text.slice(a, b);
}
function state(records = [host("workspace")]) {
    const observations = LABELS.flatMap((label) => Array.from({ length: 16 }, (_, index) => ({ label, target: `target-${index}`, geometry: { x: index, positive: true } })));
    const value = { records, captures: [...LABELS], scrollObservations: observations, observations: [], checks: ["synthetic-closure"],
        assertions: 1, fonts: [{ label: "fixed-font", px: 15 }], baseline: { synthetic: "before" }, finalOracle: { synthetic: "after" }, proofs: [], deliveries: [],
        gameplay: { playMode: "fixture", freeTextProvider: null }, submissions: [] };
    return value;
}
async function actualClosure(kind, value = state(), port = fixedInvoke()) {
    const name = kind === "roster" ? "assertCalls" : "finish", fragment = kind === "roster" ? rosterSource : finishSource;
    const code = (await transform(`${fragment}\nexport {${name}};`, { loader: "ts", format: "cjs", target: "node24", sourcefile: "actual-fixed-browser-closure.ts" })).code;
    const module = { exports: {} }, ambient = { MODE, LABELS, HEX: /^[a-f0-9]{64}$/, checks: value.checks, assertions: value.assertions,
        captures: value.captures, baseline: value.baseline, finalOracle: value.finalOracle, proofs: value.proofs, observations: value.observations,
        scrollObservations: value.scrollObservations, deliveries: value.deliveries, fonts: value.fonts,
        errors: { snapshot: () => [] }, trace: () => value.records, branches: () => value.records.filter((r) => r.channel === "host" && r.command?.op === "branches"),
        c: { get: () => value.gameplay }, gateway: { submissions: value.submissions },
        check: (ok, label) => { if (!ok) throw Error(label); }, invoke: port.invoke,
        browserReadOnlyCallAllowed: api?.browserReadOnlyCallAllowed, browserFinalReport: api?.browserFinalReport, browserFinish: api?.browserFinish };
    vm.compileFunction(code, ["module", "exports", ...Object.keys(ambient)], { filename: "actual-browser-finalization-closure.cjs" })(module, module.exports, ...Object.values(ambient));
    return { call: module.exports[name], value, port };
}

test("module", "closed-original-host-allowlist", () => { for (const op of hostAllowed) assert.equal(api.browserReadOnlyCallAllowed(host(op)), true, op); });
test("module", "native-privacy-revoke-is-always-readonly", () => { for (const op of nativeAllowed) assert.equal(api.browserReadOnlyCallAllowed(native(op)), true, op); });
test("module", "host-gameplay-author-export-and-capture-read-denied", () => { for (const op of forbiddenHost) assert.equal(api.browserReadOnlyCallAllowed(host(op)), false, op); });
test("module", "native-preview-save-model-and-workflow-denied", () => { for (const op of forbiddenNative) assert.equal(api.browserReadOnlyCallAllowed(native(op)), false, op); });
test("module", "unknown-and-mixed-channels-denied", () => {
    for (const item of [{ ...native("capture_revoke"), channel: "other" }, { ...host("close"), nativeAction: "capture_revoke" },
        { ...native("model_status"), command: { op: "close" } }, { ...host("close"), command: null }]) assert.equal(api.browserReadOnlyCallAllowed(item), false);
});

test("module", "six-original-checkpoint-references-and96-observations-retained", () => {
    const snapshots = LABELS.map((label) => ({ label, scrollObservations: Array.from({ length: 16 }, (_, target) => ({ label, target })) }));
    const original = JSON.stringify(snapshots), rows = checkpoints(), input = report(true, { captures: [...LABELS], scrollObservations: snapshots.flatMap((v) => v.scrollObservations) });
    const before = JSON.stringify(input), value = api.browserFinalReport(input, rows);
    assert.deepEqual(value.scrollObservations, summary(rows)); assert.equal(value.scrollObservations.total, 96);
    assert(!Array.isArray(value.scrollObservations)); assert.equal(JSON.stringify(input), before); assert.equal(JSON.stringify(snapshots), original);
    for (const key of Object.keys(input).filter((key) => key !== "scrollObservations")) assert.deepEqual(value[key], input[key]);
});
test("module", "failed-prefix0through6-retains-actual-counts", () => {
    for (let length = 0; length <= 6; length++) {
        const rows = checkpoints(length).map((row, index) => ({ ...row, count: index % 2 ? 0 : 16 }));
        assert.deepEqual(api.browserFinalReport(report(false), rows).scrollObservations, summary(rows));
    }
});
test("module", "summary-shape-label-order-duplicate-and-count-refusals", () => {
    const bad = [ [{ label: LABELS[1], count: 16 }], [checkpoints(1)[0],checkpoints(1)[0]], [{ label: "other", count: 16 }],
        ...[-1,17,0.5,Number.MAX_SAFE_INTEGER+1,"16",null].map((count) => [{ label: LABELS[0], count }]), null, {} ];
    for (const rows of bad) rejected(() => api.browserFinalReport(report(false), rows), "D08BrowserCheckpointSummary");
});
test("module", "success-requires-all-six-count16-and96-total", () => {
    for (let length = 0; length < 6; length++) rejected(() => api.browserFinalReport(report(true), checkpoints(length)), "D08BrowserCheckpointSummary");
    const rows = checkpoints(); rows[5].count = 15; rejected(() => api.browserFinalReport(report(true), rows), "D08BrowserCheckpointSummary");
});
test("module", "synthetic-mode-and-passed-tags-are-required", () => {
    for (const value of [null, [], {}, report(false,{synthetic:false}),report(false,{mode:"other"}),report(false,{passed:"false"})])
        rejected(() => api.browserFinalReport(value, []), "D08BrowserReportInvalid");
});
test("module", "compact-overflow-refused", () => rejected(() => api.browserFinalReport(report(false,{payload:"x".repeat(CAP)}),[]),"D08BrowserFinalReportBudget"));
test("module", "pretty-overflow-refused-even-when-compact-fits", () => {
    const input=report(false,{payload:Array(40000).fill("s")}); assert(bytes(input)<CAP); assert(bytes(input,true)>CAP);
    rejected(()=>api.browserFinalReport(input,[]),"D08BrowserFinalReportBudget");
});
test("module", "UTF8-byte-budget-is-not-character-count", () => {
    const input=report(false,{payload:"雪".repeat(90000)}); assert(JSON.stringify(input).length<CAP);
    rejected(()=>api.browserFinalReport(input,[]),"D08BrowserFinalReportBudget");
});
test("module", "exact-pretty-byte-boundary-and-one-more-byte", () => {
    const empty=api.browserFinalReport(report(false,{padding:""}),[]), length=CAP-bytes(empty,true);
    assert(length>0); const value=api.browserFinalReport(report(false,{padding:"x".repeat(length)}),[]);
    assert.equal(bytes(value,true),CAP); assert(bytes(value)<=CAP);
    rejected(()=>api.browserFinalReport(report(false,{padding:"x".repeat(length+1)}),[]),"D08BrowserFinalReportBudget");
});

test("module", "finish-detailed-success-one-fixed-IPC", async()=>{
    const p=fixedInvoke(); await api.browserFinish(p.invoke,report(true),checkpoints()); boundCalls(p.calls);
    assert.equal(p.calls.length,1); assert.equal(p.calls[0].args.report.passed,true); assert.deepEqual(p.calls[0].args.report.scrollObservations,summary(checkpoints()));
});
test("module", "finish-detailed-failure-does-not-become-pass", async()=>{
    const p=fixedInvoke(); await api.browserFinish(p.invoke,report(false),checkpoints(2)); boundCalls(p.calls);
    assert.equal(p.calls.length,1); assert.equal(p.calls[0].args.report.passed,false); assert(!p.calls[0].args.report.detailReportUnavailable);
});
for (const [name,input,rows,category] of [
    ["report",report(true,{synthetic:false}),checkpoints(),"D08BrowserReportInvalid"],
    ["summary",report(true),checkpoints(1),"D08BrowserCheckpointSummary"],
    ["budget",report(false,{payload:Array(40000).fill("s")}),[],"D08BrowserFinalReportBudget"],
]) test("module",`finish-${name}-failure-one-minimal-failed-fallback`,async()=>{
    const p=fixedInvoke(); await api.browserFinish(p.invoke,input,rows); boundCalls(p.calls); assert.equal(p.calls.length,1);
    assert.deepEqual(p.calls[0].args.report,fallback(category));
});
test("module", "detailed-IPC-rejection-one-finite-fallback-no-exception-echo", async()=>{
    const p=fixedInvoke((index)=>{if(index===1)throw Error("PRIVATE_PATH_DO_NOT_ECHO");});
    await api.browserFinish(p.invoke,report(true),checkpoints()); boundCalls(p.calls); assert.equal(p.calls.length,2);
    assert.deepEqual(p.calls[1].args.report,fallback("D08BrowserFinishRejected")); assert(!JSON.stringify(p.calls[1]).includes("PRIVATE_PATH"));
});
test("module", "build-fallback-rejection-propagates-with-no-second-fallback", async()=>{
    const p=fixedInvoke(()=>{throw Error("FixedFallbackRejection");});
    await assert.rejects(()=>api.browserFinish(p.invoke,report(false,{synthetic:false}),[]));
    assert.equal(p.calls.length,1); assert.deepEqual(p.calls[0].args.report,fallback("D08BrowserReportInvalid"));
});
test("module", "detail-and-fallback-rejections-propagate-with-no-third-IPC", async()=>{
    const p=fixedInvoke(()=>{throw Error("FixedIPCRejection");});
    await assert.rejects(()=>api.browserFinish(p.invoke,report(true),checkpoints()));
    assert.equal(p.calls.length,2); assert.deepEqual(p.calls[1].args.report,fallback("D08BrowserFinishRejected"));
});

test("roster", "actual-roster-permits-pre-disposal-privacy-revoke", async()=>{
    const h=await actualClosure("roster",state([native("capture_revoke")])); h.call(false); h.call(true);
});
test("roster", "actual-roster-still-denies-other-native-and-host-operations", async()=>{
    for(const item of [...forbiddenNative.map((op)=>native(op)),...forbiddenHost.map((op)=>host(op))]) {
        const h=await actualClosure("roster",state([item])); assert.throws(()=>h.call(false));
    }
});
test("roster", "actual256-calls-and16-catalog-bounds-unchanged", async()=>{
    for(const [count,catalogs,allowed] of [[256,16,true],[257,16,false],[256,17,false]]) {
        const records=Array.from({length:count},(_,i)=>host(i<catalogs?"branches":"workspace",i+1));
        const h=await actualClosure("roster",state(records)); if(allowed)h.call(false);else assert.throws(()=>h.call(false));
    }
});
test("roster", "actual-order-settlement-errors-and-digests-still-fenced", async()=>{
    for(const patch of [{sequence:2},{settled:false},{error:"Transport"},{replySha256:"not-a-digest"}]) {
        const h=await actualClosure("roster",state([{...host("workspace"),...patch}])); assert.throws(()=>h.call(false));
    }
});
test("roster", "actual-no-generation-mode-provider-and-submission-fences", async()=>{
    for(const field of ["mode","provider","submission"]) {
        const s=state(); if(field==="mode")s.gameplay.playMode="local"; if(field==="provider")s.gameplay.freeTextProvider={kind:"synthetic_fixture"}; if(field==="submission")s.submissions.push("forbidden");
        const h=await actualClosure("roster",s); assert.throws(()=>h.call(false));
    }
});
test("finish", "actual-finish-links-all-original-checkpoints-without-duplicate96", async()=>{
    const s=state(), before=JSON.stringify(s), p=fixedInvoke(), h=await actualClosure("finish",s,p);
    await h.call({passed:true}); boundCalls(p.calls); assert.equal(p.calls.length,1);
    assert.deepEqual(p.calls[0].args.report.scrollObservations,summary(checkpoints())); assert.equal(JSON.stringify(s),before);
    for(const key of ["baseline","finalOracle","proofs","observations","deliveries"])assert.deepEqual(p.calls[0].args.report[key],s[key]);
    assert.deepEqual(p.calls[0].args.report.fontMeasurements,s.fonts); assert.deepEqual(p.calls[0].args.report.calls,s.records);
});
test("finish", "actual-finish-pretty-overflow-uses-bounded-failed-fallback", async()=>{
    const s=state(); s.observations=Array(40000).fill("s"); const p=fixedInvoke(), h=await actualClosure("finish",s,p);
    await h.call({passed:true}); boundCalls(p.calls); assert.equal(p.calls.length,1);
    assert.deepEqual(p.calls[0].args.report,fallback("D08BrowserFinalReportBudget"));
});
test("finish", "actual-finish-IPC-rejection-retains-failure-in-minimal-report", async()=>{
    const p=fixedInvoke((index)=>{if(index===1)throw Error("PrivateNativeFailure");}), h=await actualClosure("finish",state(),p);
    await h.call({passed:true}); boundCalls(p.calls); assert.equal(p.calls.length,2); assert.deepEqual(p.calls[1].args.report,fallback("D08BrowserFinishRejected"));
});
test("source", "original-checkpoint-capture-body-is-byte-preserved", ()=>{
    assert.equal(sha(captureSource.replaceAll("\r\n","\n")),"704910042dd9ddfb2ca3c285dbb5998425407a9c64af237b35bf73afb9e7d4b8");
});
test("finish", "actual-finish-is-single-flight-across-outer-catch-reentry", async()=>{
    const p=fixedInvoke(()=>{throw Error("FixedFinalizationRejection");}), h=await actualClosure("finish",state(),p);
    await assert.rejects(()=>h.call({passed:true})); assert.equal(p.calls.length,2);
    await assert.rejects(()=>h.call({passed:false,failedCheck:"outer-catch"})); assert.equal(p.calls.length,2,"NoThirdTryAcrossActualJourneyFinishCalls");
    assert.deepEqual(p.calls[1].args.report,fallback("D08BrowserFinishRejected"));
});

assert.equal(tests.length,32,"Frozen32FinalizationFirstRoster");
try {
    source[journeyName]=await readFile(path.join(root,journeyName),"utf8");
    rosterSource=between(source[journeyName],"    const assertCalls =","    let baselineTargets");
    finishSource=between(source[journeyName],"    const finish =","    const armDelivery =");
    captureSource=between(source[journeyName],"    const capture =","    const finish =");
} catch(error) { journeyFailure=String(error).slice(0,1024); setup.push({stage:"actual-journey-closures",classification:"UNRUN_SETUP",error:journeyFailure}); }
try {
    source[moduleName]=await readFile(path.join(root,moduleName),"utf8");
    const bundled=await build({stdin:{contents:'export {browserReadOnlyCallAllowed,browserFinalReport,browserFinish} from "./ui/domain2-timeline-browser-finalization";',resolveDir:root,loader:"ts"},bundle:true,platform:"node",format:"cjs",write:false});
    api=vm.runInThisContext(`(function(){const module={exports:{}};const exports=module.exports;\n${bundled.outputFiles[0].text}\nreturn module.exports;})()`,{timeout:1000,filename:"actual-browser-finalization-module.cjs"});
    for(const name of ["browserReadOnlyCallAllowed","browserFinalReport","browserFinish"])if(typeof api[name]!=="function")throw Error(`UNRUN_SETUP:MissingExport:${name}`);
} catch(error) { moduleFailure=String(error).slice(0,1024); setup.push({stage:"actual-finalization-module",classification:"UNRUN_SETUP",error:moduleFailure}); }
for(const entry of tests) {
    const needsModule=entry.requires==="module" || entry.requires==="roster"&&/\bbrowserReadOnlyCallAllowed\b/.test(rosterSource) || entry.requires==="finish"&&/\bbrowser(?:Finish|FinalReport)\b/.test(finishSource);
    if(journeyFailure&&entry.requires!=="module" || needsModule&&moduleFailure) {
        results.push({name:entry.name,requires:entry.requires,status:"UNRUN_SETUP",error:needsModule?"Actual module prerequisite unavailable":"Actual journey prerequisite unavailable"}); continue;
    }
    try { await entry.run(); results.push({name:entry.name,requires:entry.requires,status:"PASS"}); }
    catch(error) { results.push({name:entry.name,requires:entry.requires,status:"FAIL",error:String(error).slice(0,1024)}); }
}
for(const [name,text]of Object.entries(source))if(sha(await readFile(path.join(root,name),"utf8"))!==sha(text))setup.push({stage:"source-identity",classification:"UNRUN_SETUP",error:`SourceChanged:${name}`});
const reportValue={kind:"d08_browser_finalization_independent_first_v1",authored:tests.length,
    executed:results.filter((r)=>r.status!=="UNRUN_SETUP").length,passed:results.filter((r)=>r.status==="PASS").length,
    failed:results.filter((r)=>r.status==="FAIL").length,unrun:results.filter((r)=>r.status==="UNRUN_SETUP").length,setup,results,
    source:Object.fromEntries(Object.entries(source).map(([name,text])=>[name,sha(text)])),
    extracted:{roster:sha(rosterSource),finish:sha(finishSource),capture:sha(captureSource)},
    evidence:{helper:"actual module when available",journey:"actual extracted private roster/finish closures",transport:"fixed synthetic harness_finish observer/rejections",nativeIpc:false,nativePrettyRust:false,originalFilesReadOrRewritten:false,app:false,browser:false,model:false,desktopControl:false},
    limits:["Source author executed nothing; all execution requires separate owner reconciliation, not this FIRST source",
        "Independent closure cases can execute without the absent helper only when the actual old closures do not reference it; no copied fallback implementation",
        "Six/96 reference metadata and unchanged capture source do not authenticate actual checkpoint files or replace Root image/inventory review",
        "UTF8 compact/JSON.stringify pretty are the app-local contract, not an executed Rust/native boundary test",
        "Synthetic calls cannot establish real app/window/process closure; historical unknown drain and consumed native attempt remain unchanged",
        "No native retry, cap change, artifact deletion, normal restoration, shell/file hook or runtime permission follows"]};
const encoded=JSON.stringify(reportValue); assert(Buffer.byteLength(encoded)+1<=65536,"Bounded64KiBFinalizationReviewReport");
console.log(encoded); process.exitCode=setup.length||reportValue.unrun?2:reportValue.failed||!reportValue.executed?1:0;

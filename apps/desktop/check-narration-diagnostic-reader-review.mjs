// Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0
// Independent FIRST SOURCE ONLY; author UNRUN. Actual decoder/controller/Panel
// with synthetic IPC DTOs and static HTML; NOT Rust/IPC/WebView/geometry/model.
import assert from "node:assert/strict";
import { build } from "esbuild";
import { mkdir, readFile, writeFile } from "node:fs/promises";
import { createHash, randomUUID } from "node:crypto";
import { fileURLToPath, pathToFileURL } from "node:url";
import path from "node:path";

process.env.TEMP = "D:/Dev/_Temp";
process.env.TMP = "D:/Dev/_Temp";
assert.equal(process.argv.length, 2, "ClosedDiagnosticCheckArguments");
const root = fileURLToPath(new URL(".", import.meta.url));
const output = process.env.LOCALLORE_CHECK_OUTPUT_DIR ?? path.join(root,"artifacts/checks");
assert.equal(path.parse(path.resolve(root)).root.toLowerCase(),"d:\\","PhysicalDSourceRequired");
assert.equal(path.parse(path.resolve(output)).root.toLowerCase(),"d:\\","PhysicalDOutputRequired");
await mkdir(output,{recursive:true});
const prefix=`narration-reader-first-${randomUUID()}`;
const sources=["ui/comparison-reader-model.ts","ui/comparison-reader-controller.ts","ui/ComparisonReaderPanel.tsx","check-narration-diagnostic-reader-review.mjs"];
const hashes=async()=>Object.fromEntries(await Promise.all(sources.map(async n=>[n,createHash("sha256").update(await readFile(path.join(root,n))).digest("hex")])));
const before=await hashes(), cases=[], setup=[], html=[];
const safe=error=>String(error?.message??error).slice(0,350);
let m;
try {
    const built=await build({stdin:{contents:'export * from "./ui/comparison-reader-model";export {ComparisonReaderController} from "./ui/comparison-reader-controller";export {ComparisonReaderPanel} from "./ui/ComparisonReaderPanel";export {createElement} from "react";export {renderToStaticMarkup} from "react-dom/server";',resolveDir:root,loader:"tsx"},bundle:true,platform:"node",format:"cjs",write:false});
    const file=path.join(output,`${prefix}.cjs`);await writeFile(file,built.outputFiles[0].contents,{flag:"wx"});
    m=(await import(pathToFileURL(file).href)).default;
    for(const api of ["checkedReaderNarrationDiagnosticV1","ComparisonReaderController","ComparisonReaderPanel","createElement","renderToStaticMarkup"])
        assert.equal(typeof m[api],"function",`required frozen API ${api}`);
    assert.equal(typeof m.ComparisonReaderController.prototype.inspectNarrationDiagnosticV1,"function");
} catch(error) {setup.push({stage:"bundle-api",error:safe(error),classification:"SETUP, not behavioral RED"});}
const h=c=>c.repeat(64), token="22222222-2222-2222-2222-222222222222";
const otherToken="33333333-3333-3333-3333-333333333333",binding=h("a");
const scope={story:"synthetic-diagnostic-story",branch:"main"};
const row={turn:"courier-01",arm:"left"},otherRow={turn:"courier-01",arm:"right"};
const omni={kind:"omniscient"}, player={kind:"player"}, mira={kind:"character",id:"mira"};
const clone=v=>structuredClone(v), plain=v=>JSON.parse(JSON.stringify(v));
const entry=arm=>({row:{...row,arm},source:{status:"available",scope:clone(scope),before_head:4,after_head:5,input_semantic_sha256:h("1")},capture_available:true,receipt_available:true,recording_available:true,unavailable:[]});
const source={binding,protocol_version:4,rows:[entry("left"),entry("right")],read_only:true,execution_available:false};
const oldWrap=(key,value)=>({version:1,kind:"comparison_reader",run_token:token,[key]:value});
function diagnostic(status="recorded") {
    const q={version:1,command:{op:"trace_narration_validation_read_v1",session:"synthetic-session",scope:clone(scope),expected_head:4,base_revision:2,turn:row.turn,attempt:3}};
    const data={version:1,session:q.command.session,scope:clone(scope),head:4,base_revision:2,turn:row.turn,attempt:3,observer:"player",generation_grant:false,status:"recorded",decision:{version:1,outcome:"rejected",error:"narration",reason:"scene_first_person"}};
    if(status==="host_unavailable") {data.status="unavailable";delete data.decision;}
    const observation={version:1,kind:"full_scene_narration_observation_v1",declaration_sha256:h("d"),run_binding_sha256:h("b"),source_sha256:h("c"),arm:"left",index:0,admission:1,checkpoint_sha256:h("e"),host_query:q,host_reply:status==="host_rejected"?{version:1,status:"rejected",error:"Closed"}:{version:1,status:"ok",data},generation_grant:false};
    return {version:1,kind:"comparison_reader_narration_diagnostic_v1",run_token:token,diagnostic:{version:1,protocol_version:4,kind:"narration_diagnostic_v1",binding,row:clone(row),generation_grant:false,status,...(["no_declaration","no_observation"].includes(status)?{}:{observation})}};
}
const decode=v=>m.checkedReaderNarrationDiagnosticV1(v,token,source,row);
async function test(name,work) {
    if(setup.length)return;
    try {await work();cases.push({name,passed:true});}
    catch(error){cases.push({name,passed:false,error:safe(error)});}
}
async function rejects(name,mutate) {
    await test(name,()=>{const v=diagnostic();mutate(v);assert.throws(()=>decode(v),/ComparisonReaderWire/);});
}
for(const status of ["no_declaration","no_observation","recorded","host_unavailable","host_rejected"])
    await test(`closed ${status} round-trips exact envelope`,()=>{
        const v=diagnostic(status);assert.deepEqual(plain(decode(v)),v);
        if(v.diagnostic.observation)assert.notEqual(v.diagnostic.observation.run_binding_sha256,source.binding);
    });
const rejectedCategories=["malformed","version","scope","rule","agency","deadline","retry_mismatch","too_large","author_ui_required","clarification_required","unknown_reference","dead_actor","location","inventory","resource","ability","knowledge","provider","corrupt_history"];
const decisions=[{version:1,outcome:"accepted",error:null,reason:null},{version:1,outcome:"cancelled",error:"cancelled",reason:null},{version:1,outcome:"stale",error:"stale",reason:null},...rejectedCategories.map(error=>({version:1,outcome:"rejected",error,reason:null})),...["unclassified","scene_first_person","scene_unapproved_movement"].map(reason=>({version:1,outcome:"rejected",error:"narration",reason}))];
assert.equal(decisions.length,25);
for(const decision of decisions)await test(`finite decision ${decision.outcome}/${decision.error}/${decision.reason}`,()=>{
    const v=diagnostic();v.diagnostic.observation.host_reply.data.decision=decision;
    assert.deepEqual(plain(decode(v)),v);
});
const rejectionCodes=["TooLarge","Malformed","Version","Forbidden","Closed","Scope","Stale","InvalidRequest","InvalidSelection","Internal","Io","Database","ForeignDatabase","FutureVersion","SchemaMismatch","BackupRequired","BackupExists","Busy","InvalidSeed","DuplicateStory","NotFound","InvalidInput","Integrity","UnknownTurn","RetryMismatch","Cancelled","Full","Agency","AuthorUiRequired","ClarificationRequired","UnknownReference","DeadActor","Location","Inventory","Resource","Ability","Knowledge","Rule","Provider","Timeout","Narration","CorruptHistory","Storage"];
for(const code of rejectionCodes)await test(`closed Host rejection ${code}`,()=>{const v=diagnostic("host_rejected");v.diagnostic.observation.host_reply.error=code;assert.deepEqual(plain(decode(v)),v);});
for(const [name,mutate] of [
    ["envelope kind",v=>v.kind="comparison_reader"],["envelope version",v=>v.version=2],
    ["token",v=>v.run_token=otherToken],["unknown envelope key",v=>v.path="synthetic"],
    ["foreign snapshot binding",v=>v.diagnostic.binding=h("f")],["foreign row",v=>v.diagnostic.row.turn="courier-02"],
    ["foreign arm",v=>v.diagnostic.row.arm="right"],["protocol3",v=>v.diagnostic.protocol_version=3],
    ["future status",v=>v.diagnostic.status="failed"],["diagnostic grant",v=>v.diagnostic.generation_grant=true],
    ["record grant",v=>v.diagnostic.observation.generation_grant=true],
    ["uppercase hash",v=>v.diagnostic.observation.source_sha256="A".repeat(64)],
    ["unknown record field",v=>v.diagnostic.observation.future=true],
    ["index24",v=>v.diagnostic.observation.index=24],["admission32",v=>v.diagnostic.observation.admission=32],
    ["query operation",v=>v.diagnostic.observation.host_query.command.op="trace_snapshot"],
    ["query scope",v=>v.diagnostic.observation.host_query.command.scope.story="foreign"],
    ["query BEFORE head",v=>v.diagnostic.observation.host_query.command.expected_head=5],
    ["query turn",v=>v.diagnostic.observation.host_query.command.turn="courier-02"],
    ["query attempt u32 overflow",v=>v.diagnostic.observation.host_query.command.attempt=2**32],
    ["reply session",v=>v.diagnostic.observation.host_reply.data.session="foreign"],
    ["reply scope",v=>v.diagnostic.observation.host_reply.data.scope.branch="foreign"],
    ["reply base",v=>v.diagnostic.observation.host_reply.data.base_revision=3],
    ["reply head",v=>v.diagnostic.observation.host_reply.data.head=5],
    ["reply attempt",v=>v.diagnostic.observation.host_reply.data.attempt=4],
    ["reply observer",v=>v.diagnostic.observation.host_reply.data.observer="omniscient"],
    ["reply grant",v=>v.diagnostic.observation.host_reply.data.generation_grant=true],
    ["missing nullable error",v=>delete v.diagnostic.observation.host_reply.data.decision.error],
    ["missing nullable reason",v=>delete v.diagnostic.observation.host_reply.data.decision.reason],
    ["unknown reason",v=>v.diagnostic.observation.host_reply.data.decision.reason="invented"],
    ["reason on accepted",v=>v.diagnostic.observation.host_reply.data.decision.outcome="accepted"],
    ["null observation",v=>v.diagnostic.observation=null],
    ["missing recorded observation",v=>delete v.diagnostic.observation],
    ["absence with observation",v=>v.diagnostic.status="no_observation"],
    ["Host unavailable with decision",v=>{v.diagnostic.status="host_unavailable";v.diagnostic.observation.host_reply.data.status="unavailable";}],
    ["Host rejection status mismatch",v=>v.diagnostic.status="host_rejected"],
])await rejects(`refuses ${name}`,mutate);
for(const number of [NaN,Infinity,-1,0.5,2**53])await rejects(`refuses unsafe numeric ${String(number)}`,v=>v.diagnostic.observation.host_query.command.base_revision=number);
for(const field of ["expected_head","base_revision","attempt"])await rejects(`no rounded query ${field}`,v=>{
    const q=v.diagnostic.observation.host_query.command,r=v.diagnostic.observation.host_reply.data;
    q[field]=2**53;r[field==="expected_head"?"head":field]=2**53;
});
for(const keys of [[],["diagnostic"],["diagnostic","row"],["diagnostic","observation"],
    ["diagnostic","observation","host_query"],["diagnostic","observation","host_query","command"],
    ["diagnostic","observation","host_query","command","scope"],["diagnostic","observation","host_reply"],
    ["diagnostic","observation","host_reply","data"],["diagnostic","observation","host_reply","data","decision"]])
    await rejects(`unknown field at ${keys.join("/")||"envelope"}`,v=>{let target=v;for(const key of keys)target=target[key];target.future=true;});
await test("unknown Host rejection code is a wire refusal, never arbitrary error display",()=>{
    const v=diagnostic("host_rejected");v.diagnostic.observation.host_reply.error="SYNTHETIC_PRIVATE_EXCEPTION";
    assert.throws(()=>decode(v),/ComparisonReaderWire/);
});
await rejects("future decision version",v=>v.diagnostic.observation.host_reply.data.decision.version=2);
await rejects("cyclic object",v=>v.diagnostic.observation.host_query.command.scope.cycle=v);
await test("source with unsupported protocol cannot decode diagnostic",()=>assert.throws(()=>m.checkedReaderNarrationDiagnosticV1(diagnostic(),token,{...source,protocol_version:3},row),/ComparisonReaderWire/));
await test("oversized adversarial DTO refuses; not an isolated8192-cap proof",()=>{const v=diagnostic();v.diagnostic.observation.host_query.command.session="x".repeat(8192);assert(Buffer.byteLength(JSON.stringify(v))>8192);assert.throws(()=>decode(v),/ComparisonReaderWire/);});
await test("descriptor-only detach refuses prototypes symbols and getter without executing it",()=>{
    let getters=0;
    for(const mutate of [v=>Object.setPrototypeOf(v,{inherited:true}),v=>v[Symbol("private")]=true,
        v=>Object.defineProperty(v,"diagnostic",{get(){getters++;return {};},enumerable:true}),
        v=>Object.defineProperty(v.diagnostic.observation,"source_sha256",{get(){getters++;return h("c");},enumerable:true})]) {
        const v=diagnostic();mutate(v);assert.throws(()=>decode(v),/ComparisonReaderWire/);
    }
    assert.equal(getters,0);
});

// Synthetic source-shaped Report4 for actual controller + Panel only. It is not
// an engine reconstruction, source qualification or actual committed model text.
function descriptor(arm) {
    const literal=arm==="left";
    return {arm:literal?"literal_scene_v1":"relevant_memory_scene_v1",prompt_version:literal?"locallore-play-v2.10-literal-director-v1-scene-frame-v1":"locallore-play-v2.9-scene-frame-v1",narration_policy:"grounded-prose-v2.4-scene-frame-v1",director_schema_id:literal?"locallore-director-literal-v1":"locallore-director-v2",narrator_schema_id:"locallore-narrator-v2",context_policy:literal?null:"state_relevant_memory_v1",compiler_version:literal?null:2,context_version:literal?null:2,literal_source_version:literal?1:null,literal_render_version:literal?1:null,literal_schema_version:literal?1:null,literal_packing_version:literal?1:null,forwarded_budget_version:1,scene_frame_version:1,scene_capture_gate_version:1};
}
function snapshot() {
    const turns=["left","right"].map(arm=>({turn:row.turn,scene:0,arm,phase:"committed",error:null,expected:"accepted",passed:true,failures:[],quality_flags:[],roles:2,roles_known:true,recovered_without_checkpoint:false,admission:1,elapsed_ms:2,first_final_response_ms:1,commit_elapsed_ms:0,input_semantic_sha256:h("1"),output_semantic_sha256:h("2"),mechanical_sha256:h("3"),fallback:true,repairs:0,narration:"Synthetic fixture; quality unreviewed.",capture_sha256:h("4"),recording_sha256:h("5"),raw_sha256:[h("4"),h("5")],role_metrics:null,trace:null,stages:[],actual_receipt_sha256:h("6"),source_fallback_reason:null,compiler_fallback_reason:null,construction:descriptor(arm),construction_matches:true,construction_evidence_status:"validated_committed_scene_narrator_v1",construction_evidence_reason:null,narrator_prompt_sha256:h("7"),narrator_schema_sha256:h("8"),scene_frame_sha256:h("9"),privacy_evidence_status:"checked_finite_sentinels"}));
    return {version:1,...clone(source),report:{version:4,arms:[descriptor("left"),descriptor("right")],kind:"paired_snapshots",lane:"scripted_scene_comparison",source_matches:false,completed:false,completed_scenes:0,turns,human_reviewed:0,human_rubric:"not_reviewed",quality_accepted:false,physical_setups:0,physical_setup_ms:null,native_load:null,left_charged_ms:2,right_charged_ms:2,left_reserved_roles:2,right_reserved_roles:2,first_semantic_divergence:null,first_mechanical_divergence:null,same_input_pairs:1,source_bound_committed_rows:2,unavailable:["synthetic_fixture"],profile:{id:"synthetic-only",model_sha256:h("a"),runtime_revision:"a".repeat(40),template_sha256:h("b"),worker_sha256:h("c"),profile_manifest_sha256:h("d"),context_tokens:4096,director_tokens:350,narrator_tokens:350,deadline_ms:120000,repair_limit:1},suite_sha256:h("a"),source_sha256:h("c"),reference_sha256:null,limitations:["Both human assessments need improvement; synthetic fixture only."]},unavailable:["selected_protocol4_rerun_not_implemented"]};
}
function status(client,phase="ready") {return {version:1,kind:"comparison_reader",client_id:client,operation_id:1,phase,running:false,run_token:phase==="ready"?token:null,binding:phase==="ready"?binding:null,error:null,read_only:true,execution_available:false};}
if(!setup.length)try {
    // Old, already established DTOs calibrate the synthetic transport fixture;
    // a malformed fixture is SETUP, never attributed to the new diagnostic API.
    assert.deepEqual(plain(m.checkedReaderSource(oldWrap("source",source),token,binding)),source);
    assert.deepEqual(plain(m.checkedReaderSummary(oldWrap("snapshot",snapshot()),token,binding)),snapshot());
    assert.equal(m.checkedReaderStatus(status(token),token).phase,"ready");
} catch(error) {setup.push({stage:"existing-fixture-calibration",error:safe(error),classification:"SETUP, not behavioral RED"});}
const deferred=()=>{let resolve,reject;const promise=new Promise((a,b)=>{resolve=a;reject=b;});return {promise,resolve,reject};};
async function fixture() {
    const calls=[],errors=[];let pending=null,reply=diagnostic(),protocol=4;
    const invoke=async(name,args)=>{
        calls.push({name,args:clone(args)});assert.equal(name,"evaluation_comparison");
        const q=args.query;
        if(args.action==="pick"||args.action==="managed")return status(q.clientId);
        if(args.action==="source")return oldWrap("source",{...clone(source),protocol_version:protocol});
        if(args.action==="summary")return oldWrap("snapshot",snapshot());
        if(args.action==="close")return status(q.clientId,"closed");
        if(args.action==="status")return status(q.clientId);
        if(args.action==="narration_diagnostic_v1")return pending?pending.promise:clone(reply);
        if(args.action==="evidence")return oldWrap("evidence",{version:1,binding,row:clone(row),scope:clone(scope),before_head:4,after_head:5,observer:clone(omni),edge:"after",read_only:true,generation_grant:false,body:{kind:"receipt",receipt:{synthetic:true}}});
        throw new Error("Unexpected synthetic transport action");
    };
    const c=new m.ComparisonReaderController(invoke,error=>errors.push(error));
    c.contextChanged("diagnostic-fixture",true);await c.pick();c.select(row);
    assert.equal(c.get().source?.protocol_version,4);assert.equal(c.get().status?.phase,"ready");
    return {c,calls,errors,setReply:v=>reply=v,hold:()=>pending=deferred(),setProtocol:v=>protocol=v,
        async close(){if(c.get().allowed)await c.close();c.dispose();}};
}
const diagnosticCalls=f=>f.calls.filter(v=>v.args.action==="narration_diagnostic_v1");
const textOnly=s=>s.replace(/<[^>]*>/g," ").replace(/\s+/g," ").trim();
function render(f,label) {
    const count=f.calls.length;
    const markup=m.renderToStaticMarkup(m.createElement(m.ComparisonReaderPanel,{controller:f.c}));
    assert.equal(f.calls.length,count,"rendering must not dispatch");assert(Buffer.byteLength(markup)<256*1024);
    html.push({label,markup});return {markup,text:textOnly(markup)};
}
for(const state of ["no_declaration","no_observation","recorded","host_unavailable","host_rejected"])await test(`actual controller ${state} exact dispatch and SSR context`,async()=>{
    const f=await fixture();try {
        await f.c.loadSummary();f.setReply(diagnostic(state));await f.c.inspectNarrationDiagnosticV1();
        assert.equal(f.c.get().error,null);assert.deepEqual(plain(f.c.get().diagnostic),diagnostic(state));
        assert(Object.isFrozen(f.c.get().diagnostic));assert(Object.isFrozen(f.c.get().diagnostic.diagnostic));
        assert.deepEqual(diagnosticCalls(f).map(v=>v.args.query),[{runToken:token,binding,turnId:row.turn,arm:"left",observer:omni}]);
        const view=render(f,state);
        for(const required of [scope.story,scope.branch,row.turn,"left","omniscient","4","5","committed"])
            assert(view.text.includes(required),`visible selected context ${required}`);
        assert.match(view.text,/diagnostic|validation/i);assert.match(view.text,/fallback/i);
        assert.match(view.text,/unreviewed|not.reviewed|quality|needs improvement/i);
        const statusLabel={no_declaration:/no.{0,16}declaration|not.{0,16}declared|legacy.{0,16}absence/i,
            no_observation:/no.{0,16}observation|not.{0,16}observed/i,recorded:/recorded|validation.{0,16}decision/i,
            host_unavailable:/host.{0,16}unavailable|unavailable.{0,16}host/i,host_rejected:/host.{0,16}reject/i};
        assert.match(view.text,statusLabel[state],"visible status is distinct from final row phase");
        if(state==="recorded") {assert.match(view.text,/narration|first.person/i);assert.match(view.text,/attempt/i);}
        assert.equal(f.calls.filter(v=>/start|resume|import|load/.test(v.args.action)).length,0);
        f.c.setObserver(mira);assert.equal(f.c.get().diagnostic,null);
        const narrowLens=render(f,`${state}-mira`);assert(!narrowLens.text.includes("scene_first_person"));
        assert(!narrowLens.text.includes("synthetic-session"));
    } finally {await f.close();}
});
await test("pending read clears metadata synchronously before subscribers and never autoreties",async()=>{
    const f=await fixture();try {
        await f.c.inspectNarrationDiagnosticV1();const hold=f.hold();const observed=[];
        const stop=f.c.subscribe(()=>{if(f.c.get().busy)observed.push(f.c.get().diagnostic);});
        const work=f.c.inspectNarrationDiagnosticV1();assert.equal(f.c.get().diagnostic,null);assert.equal(f.c.get().busy,true);
        assert.match(render(f,"pending").text,/pending|reading|loading|progress/i);
        hold.reject(new Error("EvaluationIntegrity"));await work;stop();
        assert(observed.length>0);assert(observed.every(value=>value===null));
        assert.equal(f.c.get().error,"EvaluationIntegrity");assert.equal(f.c.get().diagnostic,null);
        const count=diagnosticCalls(f).length;await Promise.resolve();await Promise.resolve();assert.equal(diagnosticCalls(f).length,count);
        assert.match(render(f,"error").text,/EvaluationIntegrity/);
    }finally{await f.close();}
});
for(const change of ["observer","row","context","permission","dispose","close"])await test(`late result cannot refill after ${change}`,async()=>{
    const f=await fixture();try {
        const hold=f.hold(),work=f.c.inspectNarrationDiagnosticV1();
        if(change==="observer")f.c.setObserver(player);
        if(change==="row")f.c.select(otherRow);
        if(change==="context")f.c.contextChanged("other-source",true);
        if(change==="permission")f.c.contextChanged("diagnostic-fixture",false);
        if(change==="dispose")f.c.dispose();
        const closing=change==="close"?f.c.close():Promise.resolve();
        assert.equal(f.c.get().diagnostic,null);hold.resolve(diagnostic());await work;await closing;
        assert.equal(f.c.get().diagnostic,null);assert.equal(diagnosticCalls(f).length,1);
        if(change==="observer") {f.c.setObserver(omni);assert.equal(f.c.get().diagnostic,null);}
    }finally{await f.close();}
});
await test("synchronous listener observer switch prevents diagnostic dispatch",async()=>{
    const f=await fixture();try {
        const stop=f.c.subscribe(()=>{if(f.c.get().busy)f.c.setObserver(mira);});
        await f.c.inspectNarrationDiagnosticV1();stop();
        assert.equal(diagnosticCalls(f).length,0);assert.equal(f.c.get().diagnostic,null);
    }finally{await f.close();}
});
await test("query selection and ordinary reads clear prior diagnostic",async()=>{
    const f=await fixture();try {
        await f.c.inspectNarrationDiagnosticV1();f.c.setQuerySelection("before","history");assert.equal(f.c.get().diagnostic,null);
        await f.c.inspectNarrationDiagnosticV1();await f.c.loadSummary();assert.equal(f.c.get().diagnostic,null);
        await f.c.inspectNarrationDiagnosticV1();f.c.clearEvidence();assert.equal(f.c.get().diagnostic,null);
    }finally{await f.close();}
});
await test("actor and missing-row requests refuse before transport",async()=>{
    const f=await fixture();try {
        for(const observer of [player,mira]){f.c.setObserver(observer);await f.c.inspectNarrationDiagnosticV1();assert.equal(f.c.get().error,"Forbidden");}
        f.c.setObserver(omni);f.c.select(null);await f.c.inspectNarrationDiagnosticV1();
        assert.equal(f.c.get().error,"InvalidEvaluationInput");assert.equal(diagnosticCalls(f).length,0);
    }finally{await f.close();}
});
await test("bad binding reply refuses and never leaves previous private metadata",async()=>{
    const f=await fixture();try {
        await f.c.inspectNarrationDiagnosticV1();const bad=diagnostic();bad.diagnostic.binding=h("f");f.setReply(bad);
        await f.c.inspectNarrationDiagnosticV1();assert.equal(f.c.get().diagnostic,null);assert.equal(f.c.get().error,"ComparisonReaderWire");
    }finally{await f.close();}
});
await test("unknown native error cannot expose arbitrary private exception text",async()=>{
    const f=await fixture();try {
        const hold=f.hold(),work=f.c.inspectNarrationDiagnosticV1();
        hold.reject(new Error("SYNTHETIC_PRIVATE_EXCEPTION"));await work;
        assert.equal(f.c.get().error,"EvaluationIo");assert.equal(f.c.get().diagnostic,null);
        assert(!render(f,"bounded-error").text.includes("SYNTHETIC_PRIVATE_EXCEPTION"));
    }finally{await f.close();}
});
await test("Protocol3 capability never dispatches diagnostic",async()=>{
    const f=await fixture();try {
        await f.c.close();f.setProtocol(3);await f.c.pick();f.c.select(row);
        assert.equal(f.c.get().source.protocol_version,3);await f.c.inspectNarrationDiagnosticV1();
        assert.equal(diagnosticCalls(f).length,0);assert.equal(f.c.get().diagnostic,null);
    }finally{await f.close();}
});
// BEGIN INDEPENDENT ARTIFACT CONTEXT FIRST V1
// Additive five-case source freeze BEFORE the Panel context fix. The original
// 151 cases/helpers/assertions above and finalization below remain byte-exact.
// Static HTML only: no native execution, visible geometry or measured RED.
for(const artifactStatus of ["no_declaration","no_observation","recorded","host_unavailable","host_rejected"])
    await test(`artifact-local context ${artifactStatus} before raw metadata`,async()=>{
        const f=await fixture();try {
            await f.c.loadSummary();
            assert.equal(f.c.get().summary.report.turns[0].error,null,"existing typed synthetic fixture has no case error");
            f.setReply(diagnostic(artifactStatus));await f.c.inspectNarrationDiagnosticV1();
            assert.equal(f.c.get().error,null);
            assert.equal(f.c.get().diagnostic.diagnostic.status,artifactStatus);
            const {markup}=render(f,`artifact-context-${artifactStatus}`);
            const marker=`data-diagnostic-status="${artifactStatus}"`;
            const start=markup.indexOf(marker);
            assert(start>=0,"actual new diagnostic artifact status marker exists");
            assert.equal(markup.indexOf(marker,start+marker.length),-1,"one selected diagnostic artifact");
            const end=markup.indexOf("<details",start);
            assert(end>start,"actual artifact has a separate raw-metadata details section");
            // Beginning at the artifact marker excludes the surrounding selected
            // header/report. Ending before details excludes raw JSON as an oracle.
            const local=textOnly(markup.slice(start+marker.length,end));
            for(const required of [scope.story,scope.branch,row.turn])
                assert(local.includes(required),`artifact-local selected context ${required}`);
            assert.match(local,/\bleft\b/i,"artifact-local physical arm");
            assert.match(local,/\bobserver\s*[:·-]?\s*omniscient\b/i,"artifact-local lens");
            assert.match(local,/\bbefore(?:\s+head|\s+revision)?\s*[:·-]?\s*4\b/i,"artifact-local BEFORE4");
            assert.match(local,/\bafter(?:\s+head|\s+revision)?\s*[:·-]?\s*5\b/i,"artifact-local AFTER5");
            assert.match(local,/\b(?:selected\s+)?case\s+phase\s*[:·-]?\s*committed\b/i,"case phase is separate from validation decision");
            assert.match(local,/\bcase\s+error\s*[:·-]?\s*none(?:\s+recorded)?\b/i,"explicit case error None; never infer it from a decision");
            assert.match(local,/\baccepted\s+receipt\s*[:·-]?\s*available\b/i,"actual selected receipt availability");
            assert.match(local,/\bmechanical\s+fallback\s+recorded\b/i,"selected fallback stays visible");
            assert.match(local,/\b(?:prose\s+)?quality\s*[:·-]?\s*(?:unreviewed|not[ _]reviewed|not[ _]accepted|not[ _]established)\b/i,"explicit quality limitation beside artifact");
        }finally{await f.close();}
    });
// END INDEPENDENT ARTIFACT CONTEXT FIRST V1
assert.deepEqual(await hashes(),before,"test must not alter source");
for(let i=0;i<html.length;i++)await writeFile(path.join(output,`${prefix}-${i}.html`),html[i].markup,{flag:"wx"});
const result={classification:"synthetic IPC + actual frontend controller/decoder + Panel static HTML only",source:before,setup,cases,passed:cases.filter(v=>v.passed).length,failed:cases.filter(v=>!v.passed).length,staticHtml:html.map((v,i)=>({label:v.label,file:`${prefix}-${i}.html`})),nativeIpc:false,nativeWebView:false,geometry:false,modelExecution:false,limits:["Author source-only UNRUN; missing APIs are SETUP, not behavioral RED.","No native8192 overflow claim for valid closed records; no arbitrary Value seam.","No real browser geometry/images; actual hidden WebView/IPC/image gates remain pending."]};
await writeFile(path.join(output,`${prefix}.json`),JSON.stringify(result,null,2),{flag:"wx"});
console.log(JSON.stringify({kind:"narration-diagnostic-reader-first",setup:setup.length,passed:result.passed,failed:result.failed,classification:result.classification}));
if(setup.length||result.failed)process.exitCode=1;

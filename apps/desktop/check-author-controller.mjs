// Frozen synthetic presentation/async controller oracles, not native execution.
import assert from "node:assert/strict";
import { build } from "esbuild";
import { mkdir, writeFile } from "node:fs/promises";
import { fileURLToPath, pathToFileURL } from "node:url";
import path from "node:path";
import { randomUUID, createHash } from "node:crypto";

const directory = process.env.LOCALLORE_CHECK_OUTPUT_DIR ?? fileURLToPath(new URL("./artifacts/checks/", import.meta.url));
await mkdir(directory, { recursive: true });
const target = path.join(directory, `author-controller-${randomUUID()}.mjs`);
const bundle = await build({entryPoints:[fileURLToPath(new URL("./ui/author-controller.ts",import.meta.url))],bundle:true,platform:"node",format:"esm",write:false});
await writeFile(target,bundle.outputFiles[0].contents);
const { AuthorController, checkedAuthorInput, checkedAuthorPreview, checkedAuthorOutcome, checkedAuthorStatus } = await import(pathToFileURL(target).href);
let checks=0;
const check=(value,message)=>{assert.ok(value,message);checks++;};
const reject=async(fn)=>{await assert.rejects(fn);checks++;};
const clone=(v)=>JSON.parse(JSON.stringify(v));
const context=()=>({rootIncarnation:"root-1",selectionEpoch:1,session:"session-1",scope:{story:"quay",branch:"main"},head:3,player:"player",observer:"omniscient",view:"lab",persistent:true,spoilerGranted:true,pending:false,brokerUncertain:false});
const draft=()=>({fork_revision:1,child_branch:"child-fixed",fact:"relic-location",expected_proposition:"PRIVATE_OLD_A",replacement:"PRIVATE_NEW_B",reason:"PRIVATE_AUTHOR_REASON"});
const input=()=>({version:1,parent:{story:"quay",branch:"main"},expected_parent_revision:3,fork_revision:1,child_branch:"child-fixed",operation:{op:"replace_fact_proposition",fact:"relic-location",expected_proposition:"PRIVATE_OLD_A",replacement:"PRIVATE_NEW_B"},reason:"PRIVATE_AUTHOR_REASON"});
const sha=(s)=>createHash("sha256").update(s).digest("hex");
const core=(i=input())=>({version:1,input:clone(i),child:{story:i.parent.story,branch:i.child_branch},before:{fact:i.operation.fact,proposition:i.operation.expected_proposition,source:{kind:"seed_fact",seed_id:"lantern-quay-v1",fact:i.operation.fact}},creation_revision:i.fork_revision+1,retained_knowers:2,excluded_suffix_events:i.expected_parent_revision-i.fork_revision,excluded_suffix_records:1,original_preserved:true,downstream_replayed:false,new_child_requires_fresh_derivatives:true});
const preview=(i=input(),session="session-1")=>{const json=JSON.stringify(core(i));return {version:1,kind:"author_preview",session,preview_token:"11111111-1111-4111-8111-111111111111",preview_sha256:sha(json),preview_json:json,expires_seconds:600};};
const outcome=(i=input(),created=true)=>({version:1,scope:{story:i.parent.story,branch:i.child_branch},parent:clone(i.parent),fork_revision:i.fork_revision,author_revision:i.fork_revision+1,head_revision:i.fork_revision+1,created});
const complete=(id,result)=>({version:1,operation_id:id,running:false,phase:"completed",error:null,result});
const pending=(id,phase="author_applying")=>({version:1,operation_id:id,running:true,phase,error:null,result:null});
function deferred(){let resolve,reject;const promise=new Promise((a,b)=>{resolve=a;reject=b;});return {resolve,reject,promise};}
class Port {
    calls=[]; discards=[]; next=0; starts=[]; statuses=[]; cancels=[];
    async start(kind,raw){const request=JSON.parse(raw);this.calls.push({kind,request,raw});if(this.starts.length)return this.starts.shift()(request);const id=++this.next;
        if(kind==="prepare")return complete(id,preview(request.input,request.session));
        if(kind==="commit")return complete(id,{version:1,kind:"author_commit",session:request.session,outcome:outcome(request.input)});
        return complete(id,{version:1,kind:"author_lookup",found:true,outcome:outcome(request.input,false)});
    }
    prepareStart=(raw)=>this.start("prepare",raw);
    commitStart=(raw)=>this.start("commit",raw);
    lookupStart=(raw)=>this.start("lookup",raw);
    status=async(id)=>{this.calls.push({kind:"status",id});if(!this.statuses.length)throw Error("Transport");return this.statuses.shift()(id);};
    cancel=async(id)=>{this.cancels.push(id);return this.cancelReply??pending(id);};
    discardPreview=async(session,token)=>{this.discards.push({session,token});return true;};
}
function fixture(){const port=new Port(),opened=[],refreshed=[];const c=new AuthorController(port,{refreshLibrary:async()=>{refreshed.push(true);},openChild:async(scope)=>{opened.push(scope);}},async()=>{});c.contextChanged(context());c.setDraft(draft());return {c,port,opened,refreshed};}

check(JSON.stringify(checkedAuthorInput(input()))===JSON.stringify(input()),"exact native input");
for(const mutate of [(v)=>v.extra=true,(v)=>v.fork_revision=1.5,(v)=>v.expected_parent_revision=Number.MAX_SAFE_INTEGER+1,(v)=>v.parent.story="other/story",(v)=>v.operation.op="shell",(v)=>v.operation.replacement=v.operation.expected_proposition]){const bad=input();mutate(bad);assert.throws(()=>checkedAuthorInput(bad));checks++;}
const valid=await checkedAuthorPreview(preview(),input(),"session-1");check(valid.preview_json===preview().preview_json,"exact bytes retained");check(Object.isFrozen(valid)&&Object.isFrozen(valid.preview.input),"detached frozen private preview");
for(const mutate of [(v)=>v.extra=true,(v)=>v.session="session-other",(v)=>v.preview_sha256="0".repeat(64),(v)=>v.expires_seconds=601,(v)=>v.preview_token="arbitrary",(v)=>v.preview_json="x".repeat(65537)]){const bad=preview();mutate(bad);await reject(()=>checkedAuthorPreview(bad,input(),"session-1"));}
for(const mutate of [(v)=>v.input.reason="edited",(v)=>v.before.proposition="wrong",(v)=>v.child.branch="sibling",(v)=>v.excluded_suffix_events=99,(v)=>v.downstream_replayed=true,(v)=>v.before.source={kind:"author",source:{original_scope:{story:"foreign",branch:"main"},sequence:1}}]){const p=preview(),raw=core();mutate(raw);p.preview_json=JSON.stringify(raw);p.preview_sha256=sha(p.preview_json);await reject(()=>checkedAuthorPreview(p,input(),"session-1"));}
for(const raw of [preview().preview_json.replace('"reason":','"reason":"duplicate","reason":'),preview().preview_json.replace('"reason":','"re\\u0061son":"duplicate","reason":'),"[".repeat(20)+"]".repeat(20)]){const p=preview();p.preview_json=raw;p.preview_sha256=sha(raw);await reject(()=>checkedAuthorPreview(p,input(),"session-1"));}
const controls=input();controls.reason="\u0001".repeat(2048);controls.operation.replacement="🕯️ <img src=x onerror=alert(1)>";const literal=await checkedAuthorPreview(preview(controls),controls,"session-1");check(literal.preview.input.reason===controls.reason,"controls unchanged");check(literal.preview.input.operation.replacement===controls.operation.replacement,"literal markup unchanged");
const accessor=preview();Object.defineProperty(accessor,"session",{enumerable:true,get(){throw Error("must not execute");}});await reject(()=>checkedAuthorPreview(accessor,input(),"session-1"));
assert.throws(()=>checkedAuthorOutcome({...outcome(),head_revision:0},input()));checks++;
assert.throws(()=>checkedAuthorStatus({...pending(1),phase:"shell"}));checks++;
assert.throws(()=>checkedAuthorStatus({...pending(1),running:false}));checks++;

{
 const {c,port,opened}=fixture();await c.prepare();check(port.calls.length===0,"no first consent no native work");c.setAuthorConsent(true);await c.prepare();check(c.get().status==="preview","native-shaped preview displayed");await c.confirm(true);check(port.calls.filter(v=>v.kind==="commit").length===0,"read acknowledgement required");c.setPreviewRead(true);await c.confirm(false);check(port.calls.filter(v=>v.kind==="commit").length===0,"second explicit confirm required");await c.confirm(true);check(c.get().status==="complete","commit completion");check(opened.length===0,"no automatic child open");await c.openConfirmed();check(opened.length===1,"separate open action");check(port.calls.filter(v=>v.kind==="commit").length===1,"one commit only");c.dispose();
}
for(const change of [(v)=>v.view="play",(v)=>v.observer="mira",(v)=>v.persistent=false,(v)=>v.spoilerGranted=false,(v)=>v.pending=true,(v)=>v.brokerUncertain=true]){
 const {c,port}=fixture();const ctx=context();change(ctx);c.contextChanged(ctx);c.setDraft(draft());c.setAuthorConsent(true);await c.prepare();check(port.calls.length===0,"native author unavailable in this context");c.dispose();
}
{
 const {c,port}=fixture();c.setAuthorConsent(true);await c.prepare();c.setPreviewRead(true);c.setDraft({...draft(),replacement:"edited B"});await Promise.resolve();check(c.get().preview===null&&!c.get().authorConsent&&!c.get().previewRead,"form edit invalidates both stages");check(port.discards.length===1,"native discard on edit");await c.confirm(true);check(!port.calls.some(v=>v.kind==="commit"),"old preview cannot commit");c.dispose();
}
for(const field of ["head","selectionEpoch","session","observer","rootIncarnation"]){
 const {c,port}=fixture();c.setAuthorConsent(true);await c.prepare();const ctx=context();if(typeof ctx[field]==="number")ctx[field]++;else ctx[field]+="-other";c.contextChanged(ctx);await Promise.resolve();check(c.get().preview===null&&!c.get().authorConsent,"context invalidates private preview");check(port.discards.length===1,"context native discard");c.dispose();
}
{
 const {c,port}=fixture(),late=deferred();port.starts.push(()=>late.promise);c.setAuthorConsent(true);const work=c.prepare();await Promise.resolve();c.contextChanged({...context(),selectionEpoch:2,head:4});late.resolve(complete(1,preview()));await work;check(c.get().preview===null,"stale prepare never publishes");check(port.discards.length===1,"late preview discarded");c.dispose();
}
{
 const {c,port}=fixture();c.setAuthorConsent(true);await c.prepare();c.setPreviewRead(true);port.starts.push(()=>Promise.reject(Error("ArchiveBusy")));await c.confirm(true);check(c.get().preview===null&&!c.get().previewRead,"verified failed attempt requires fresh preview");check(c.get().error==="ArchiveBusy","fixed Busy category");await c.confirm(true);check(port.calls.filter(v=>v.kind==="commit").length===1,"no automatic/exact-token retry");c.dispose();
}
{
 const {c,port}=fixture();c.setAuthorConsent(true);await c.prepare();c.setPreviewRead(true);port.starts.push(()=>Promise.reject(Error("Transport")));await c.confirm(true);check(c.get().status==="uncertain","lost whole ack uncertain");const before=clone(port.calls.find(v=>v.kind==="commit").request.input);c.setDraft({...draft(),reason:"edited"});check(c.get().input.reason===before.reason,"uncertain fullinput preserved in memory");await c.lookup();check(c.get().status==="complete","explicit readonly lookup recovers");check(port.calls.filter(v=>v.kind==="commit").length===1,"lookup never reapplies");check(port.calls.find(v=>v.kind==="lookup").request.input.reason===before.reason,"lookup exact original input");c.dispose();check(c.get().input===null,"dispose clears private fullinput");
}
{
 const {c,port}=fixture();c.setAuthorConsent(true);await c.prepare();c.setPreviewRead(true);port.starts.push(()=>Promise.resolve(pending(7)));port.statuses.push(()=>Promise.reject(Error("Transport")));await c.confirm(true);check(c.get().operation?.operation_id===7,"known ID retained");port.statuses.push(()=>Promise.resolve(complete(7,{version:1,kind:"author_commit",session:"session-1",outcome:outcome()})));await c.inspectOperation();check(c.get().status==="complete","known-ID read recovers exact outcome");c.dispose();
}
{
 const {c,port}=fixture(),gate=deferred();c.setAuthorConsent(true);await c.prepare();c.setPreviewRead(true);port.starts.push(()=>Promise.resolve(pending(8)));port.statuses.push(()=>gate.promise);const work=c.confirm(true);await Promise.resolve();await Promise.resolve();port.cancelReply=complete(8,{version:1,kind:"author_commit",session:"session-1",outcome:outcome()});await c.cancel();gate.resolve(port.cancelReply);await work;check(c.get().status==="complete","committed cancel response wins");check(port.cancels.includes(8),"cancel same native operation");c.dispose();
}
{
 const {c,port}=fixture();c.setAuthorConsent(true);await c.prepare();c.setPreviewRead(true);port.starts.push(()=>Promise.reject(Error("PRIVATE_MODEL_TEXT")));await c.confirm(true);check(c.get().error==="Wire","private/unknown errors not logged or shown");c.contextChanged({...context(),rootIncarnation:"root-2"});check(c.get().input===null,"new root drops old private recovery input");await c.lookup();check(!port.calls.some(v=>v.kind==="lookup"),"foreign root cannot recover old input");c.dispose();
}
{
 const {c,port}=fixture(),gate=deferred();c.setAuthorConsent(true);await c.prepare();c.setPreviewRead(true);port.starts.push(()=>Promise.resolve(pending(9)));port.statuses.push(()=>gate.promise);const work=c.confirm(true);await Promise.resolve();await Promise.resolve();port.cancelReply=complete(9,{version:1,kind:"author_commit",session:"session-1",outcome:outcome()});await c.cancel();gate.reject(Error("Transport"));await work;check(c.get().status==="complete"&&!c.get().uncertain,"known committed cancellation reply survives an older failed status request");c.dispose();
}
{
 const {c,port}=fixture();port.starts.push(()=>Promise.resolve(pending(11,"author_preparing")));port.statuses.push(()=>Promise.reject(Error("Transport")));c.setAuthorConsent(true);await c.prepare();c.contextChanged({...context(),head:4,selectionEpoch:2});port.statuses.push(()=>Promise.resolve(complete(11,preview())));await c.inspectOperation();check(c.get().preview===null,"inspection cannot rebind old private prepare to a new context");c.dispose();
}
{
 const {c,port}=fixture(),gate=deferred();port.starts.push(()=>gate.promise);c.setAuthorConsent(true);const work=c.prepare();await Promise.resolve();await c.cancel();gate.resolve(complete(12,preview()));await work;check(c.get().preview===null,"cancel before start acknowledgment discards late private preview");check(port.discards.length===1,"cancelled prepare cap retired explicitly");c.dispose();
}
{
 const envelope=preview(),expected=input(),original=envelope.preview_json;const checking=checkedAuthorPreview(envelope,expected,"session-1");envelope.session="foreign";envelope.preview_json="{}";expected.reason="changed while digest awaited";const checked=await checking;check(checked.session==="session-1"&&checked.preview_json===original&&checked.preview.input.reason==="PRIVATE_AUTHOR_REASON","async SHA checks use detached envelope and expected input snapshots");
}
{
 const {c,port}=fixture();c.setAuthorConsent(true);await c.prepare();c.contextChanged(Object.fromEntries(Object.entries(context()).reverse()));check(c.get().preview!==null&&port.discards.length===0,"context property order alone is not a selection change");c.dispose();
}
{
 const {c,port}=fixture();c.setAuthorConsent(true);await c.prepare();c.setPreviewRead(true);c.setDraft({...draft(),fork_revision:NaN});await Promise.resolve();check(c.get().preview===null&&!c.get().authorConsent&&!c.get().previewRead&&port.discards.length===1,"invalid form edit also revokes the displayed preview and both consents");await c.confirm(true);check(!port.calls.some(v=>v.kind==="commit"),"invalid edit cannot leave old confirm armed");c.dispose();
}
console.log(`${checks} synthetic author decoder/controller checks passed; no native or rendering execution.`);

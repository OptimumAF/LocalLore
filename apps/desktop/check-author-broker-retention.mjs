// Frozen synthetic shared-gate oracles. No native/Core execution or rendering.
import assert from "node:assert/strict";
import { build } from "esbuild";
import { mkdir, writeFile } from "node:fs/promises";
import { fileURLToPath, pathToFileURL } from "node:url";
import { randomUUID, createHash } from "node:crypto";
import path from "node:path";
const output=process.env.LOCALLORE_CHECK_OUTPUT_DIR??fileURLToPath(new URL("artifacts/checks/",import.meta.url));
await mkdir(output,{recursive:true});const target=path.join(output,`author-broker-${randomUUID()}.mjs`);
const bundle=await build({entryPoints:[fileURLToPath(new URL("ui/broker-retention.ts",import.meta.url))],bundle:true,format:"esm",platform:"node",write:false});
await writeFile(target,bundle.outputFiles[0].contents);const {BrokerRetention}=await import(pathToFileURL(target).href);
let checks=0;const check=(v,label)=>{assert.ok(v,label);checks++;};const clone=v=>JSON.parse(JSON.stringify(v));
function deferred(){let resolve,reject;const promise=new Promise((a,b)=>{resolve=a;reject=b;});return {promise,resolve,reject};}
async function reached(promise){let timer;try{return await Promise.race([promise,new Promise((_,reject)=>{timer=setTimeout(()=>reject(Error("Bounded digest gate not entered")),2000);})]);}finally{clearTimeout(timer);}}
const input=()=>({version:1,parent:{story:"quay",branch:"main"},expected_parent_revision:3,fork_revision:1,child_branch:"child-fixed",operation:{op:"replace_fact_proposition",fact:"relic-location",expected_proposition:"PRIVATE_OLD_A",replacement:"PRIVATE_NEW_B"},reason:"PRIVATE_AUTHOR_REASON"});
const identity=(action="prepare")=>({surface:"author",action,session:"session-1",story:"quay",branch:"main",head:3,child:"child-fixed",at:1,author:{action,session:"session-1",input:input()}});
const archive={surface:"archive",action:"archive_import_preview"};
const complete=(id,result)=>({version:1,operation_id:id,running:false,phase:"completed",error:null,result});
const pending=(id,action="prepare")=>({version:1,operation_id:id,running:true,phase:action==="prepare"?"author_preparing":action==="commit"?"author_applying":"author_lookup",error:null,result:null});
const archiveDone=id=>complete(id,{version:1,status:"cancelled"});
const outcome=(i=input(),created=true)=>({version:1,scope:{story:i.parent.story,branch:i.child_branch},parent:clone(i.parent),fork_revision:i.fork_revision,author_revision:i.fork_revision+1,head_revision:i.fork_revision+1,created});
const core=(i=input())=>({version:1,input:clone(i),child:{story:i.parent.story,branch:i.child_branch},before:{fact:i.operation.fact,proposition:i.operation.expected_proposition,source:{kind:"seed_fact",seed_id:"lantern-quay-v1",fact:i.operation.fact}},creation_revision:i.fork_revision+1,retained_knowers:2,excluded_suffix_events:i.expected_parent_revision-i.fork_revision,excluded_suffix_records:1,original_preserved:true,downstream_replayed:false,new_child_requires_fresh_derivatives:true});
function preview(i=input(),session="session-1"){const raw=JSON.stringify(core(i));return {version:1,kind:"author_preview",session,preview_token:"11111111-1111-4111-8111-111111111111",preview_sha256:createHash("sha256").update(raw).digest("hex"),preview_json:raw,expires_seconds:600};}
const commit=(id=1)=>complete(id,{version:1,kind:"author_commit",session:"session-1",outcome:outcome()});
const lookup=(id=1)=>complete(id,{version:1,kind:"author_lookup",found:true,outcome:outcome(input(),false)});
async function blocked(gate){await assert.rejects(()=>gate.start(archive,async()=>archiveDone(99)),/ArchiveBusy/);checks++;}
async function heldDigest(work){
 const subtle=crypto.subtle,descriptor=Object.getOwnPropertyDescriptor(subtle,"digest"),original=subtle.digest;const entered=deferred(),release=deferred();let calls=0;
 Object.defineProperty(subtle,"digest",{configurable:true,writable:true,value:async function(...args){calls++;entered.resolve();await release.promise;return original.apply(subtle,args);}});
 try{await work({entered:entered.promise,release:release.resolve,calls:()=>calls});}finally{release.resolve();if(descriptor)Object.defineProperty(subtle,"digest",descriptor);else delete subtle.digest;}
}

{
 const gate=new BrokerRetention(()=>false),held=deferred(),source=identity();const start=gate.start(source,()=>held.promise);source.author.input.reason="mutated";source.author.session="other";
 check(gate.get().identity.author.input.reason==="PRIVATE_AUTHOR_REASON","full input detached at admission");check(Object.isFrozen(gate.get().identity.author)&&Object.isFrozen(gate.get().identity.author.input.operation),"author binding frozen");held.resolve(pending(1));await start;
 for(const mutate of [v=>v.author.extra=true,v=>v.author.action="shell",v=>v.author.session="path/session",v=>v.author.input.extra=true,v=>v.story="different",v=>v.action="commit",v=>v.archive={},v=>v.token="arbitrary"]){const fresh=new BrokerRetention(()=>false),bad=identity();mutate(bad);await assert.rejects(()=>fresh.start(bad,async()=>pending(1)));checks++;}
 const wrong={...archive,author:identity().author};await assert.rejects(()=>new BrokerRetention(()=>false).start(wrong,async()=>archiveDone(1)));checks++;
}
await heldDigest(async digest=>{
 let awaiting=true;const gate=new BrokerRetention(()=>awaiting);const started=gate.start(identity(),async()=>complete(2,preview()));await reached(digest.entered);
 check(gate.get().inFlight===true&&gate.get().terminal===false,"terminal not trusted during SHA");await blocked(gate);check(gate.acknowledgeUnresolved(true)===false,"pending SHA cannot be acknowledged away");
 awaiting=false;gate.refreshConsumption();await blocked(gate);digest.release();await started;
 check(gate.get().unknown===false&&gate.get().terminal===true,"full validated preview terminal");await gate.start(archive,async()=>archiveDone(3));check(gate.get().identity.surface==="archive","explicit new surface after verification/consumption");
});
for(const mutate of [v=>v.result.kind="fork",v=>v.result.session="foreign",v=>v.result.preview_sha256="0".repeat(64),v=>v.phase="memory_maintenance",v=>v.version=2,v=>v.extra=true,v=>v.operation_id=1.5]){
 const gate=new BrokerRetention(()=>false),bad=complete(4,preview());mutate(bad);await gate.start(identity(),async()=>bad);
 check(gate.get().unknown===true,"malformed author completion latches global unknown");gate.refreshConsumption();await blocked(gate);
 await gate.observeAuthor(complete(4,preview()));check(gate.get().unknown===true,"later valid/partial data cannot silently forgive a validation fault");
 check(gate.acknowledgeUnresolved(true)===true,"explicit unresolved disposition available after checks");await gate.start(archive,async()=>archiveDone(5));
}
{
 const gate=new BrokerRetention(()=>false),changed=input();changed.reason="different";await gate.start(identity(),async()=>complete(6,preview(changed)));
 check(gate.get().unknown===true,"same scope/head but different full input rejected");await blocked(gate);
}
for(const action of ["commit","lookup"]){
 const gate=new BrokerRetention(()=>false),wrong=action==="commit"?commit(7):lookup(7);wrong.result.outcome.parent.branch="sibling";await gate.start(identity(action),async()=>wrong);check(gate.get().unknown===true,"author outcome must match full binding");await blocked(gate);
}
{
 let awaiting=true;const gate=new BrokerRetention(()=>awaiting);await gate.start(identity("commit"),async()=>pending(8,"commit"));
 await gate.observeAuthor({operation_id:7,private_wrong_shape:true});check(gate.get().unknown===false&&gate.get().operation===8,"known different old ID excluded before shape decode");
 gate.observe(commit(8));check(gate.get().unknown===true,"sync observe is conservative for author");
 await gate.observeAuthor(commit(8));check(gate.get().unknown===false&&gate.get().terminal===true,"actual async route validates committed result");await blocked(gate);
 awaiting=false;gate.refreshConsumption();await gate.start(archive,async()=>archiveDone(9));await gate.observeAuthor(commit(8));check(gate.get().identity.surface==="archive"&&gate.get().unknown===false,"old author callback cannot poison other surface");
}
{
 const gate=new BrokerRetention(()=>false);await assert.rejects(()=>gate.start(identity("commit"),async()=>{throw Error("Transport");}),/Transport/);
 await gate.observeAuthor(commit(10));check(gate.get().operation===null&&gate.get().unknown===true,"unknown whole start ack cannot adopt external ID");await blocked(gate);
}
await heldDigest(async digest=>{
 const gate=new BrokerRetention(()=>false);await gate.start(identity(),async()=>pending(11));const wrong=complete(11,preview());wrong.result.preview_sha256="0".repeat(64);
 const first=gate.observeAuthor(wrong),second=gate.observeAuthor(complete(11,preview()));await reached(digest.entered);await blocked(gate);digest.release();await Promise.all([first,second]);check(gate.get().unknown===true,"concurrent valid check cannot erase invalid preview fault");await blocked(gate);
});
{
 let awaiting=true;const gate=new BrokerRetention(()=>awaiting);await gate.start(identity("commit"),async()=>pending(12,"commit"));
 await gate.observeAuthor({version:1,operation_id:12,running:false,phase:"error",error:"Cancelled",result:null});check(gate.get().terminal===true&&gate.get().unknown===false,"actual shaped Cancelled terminal known");await blocked(gate);
 awaiting=false;gate.refreshConsumption();await gate.start(identity("commit"),async()=>commit(13));check(gate.get().terminal===true&&gate.get().unknown===false,"new explicit commit admission validated");
}
{
 const busy=new BrokerRetention(()=>false);await assert.rejects(()=>busy.start(identity("commit"),async()=>{throw Error("ArchiveBusy");}),/ArchiveBusy/);check(busy.get().unknown===false&&busy.get().terminal===true,"native Busy known no admission");await busy.start(archive,async()=>archiveDone(14));
 for(const error of ["Rule","Full","Closed","Internal"]){const gate=new BrokerRetention(()=>false);await assert.rejects(()=>gate.start(identity("commit"),async()=>{throw Error(error);}));check(gate.get().unknown===true,"other start throw not assumed no-write");await blocked(gate);}
}
{
 const gate=new BrokerRetention(()=>false);await gate.start(identity("lookup"),async()=>lookup(15));check(gate.get().terminal&&!gate.get().unknown,"readonly exact lookup completion validated");
 await gate.start(archive,async()=>archiveDone(16));await gate.observeAuthor({operation_id:15,running:false,result:{private:"invalid"}});check(!gate.get().unknown,"late author status cannot contaminate archive");
}
console.log(`${checks} synthetic author shared-broker retention checks passed; no native or render execution.`);

// FIRST c8f7eb88 + 6fa36c0b precision; author UNCOMPILED/UNRUN. Actual frontend with disclosed
// inert hooks/JSX and synthetic IPC; no Store, native, pixels or validator.
import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import { createHash, webcrypto } from "node:crypto";
import { build, transform } from "esbuild";
import { fileURLToPath } from "node:url";
import path from "node:path";
import vm from "node:vm";
assert.equal(process.argv.length,2,"ClosedDomain2ForkReviewArguments");
globalThis.crypto ??= webcrypto;
const root=fileURLToPath(new URL(".",import.meta.url)), source={}, setup=[], cases=[], results=[];
const sha=s=>createHash("sha256").update(s).digest("hex"), copy=v=>structuredClone(v);
const MAIN={story:"fork-first",branch:"main"}, CHILD={story:"fork-first",branch:"child"};
const ctx=(p={})=>({session:"native-session-73",scope:copy(MAIN),revision:7,view:"play",observer:"player",persistent:true,...p});
const raw=(c=ctx(),values=[0,2,3,7])=>({version:2,scope:copy(c.scope),head:c.revision,boundaries:[...values]});
const changed=[{session:"native-session-74"},{scope:{story:"other",branch:"main"}},{scope:{story:MAIN.story,branch:"other"}},{revision:8},{view:"lab"},{observer:"omniscient"},{persistent:false}];
const test=(need,name,run)=>cases.push({need,name,run});
const tick=async()=>{for(let n=0;n<80;n++)await Promise.resolve();};
const gate=()=>{let resolve,reject;const promise=new Promise((a,b)=>{resolve=a;reject=b;});return{promise,resolve,reject};};
let a=null,codec=null, mainSource="", baseFailure=null, codecFailure=null;
function requireApi(f,names){for(const name of names)if(typeof f[name]!=="function")throw Error(`UNRUN_SETUP:MissingActualAPI:${name}`);}
const hookSource=`
export const __fragment=Symbol('inert');export const __element=(type,props,...children)=>({type,props:{...(props??{}),children}});
let active=null,index=0;const slots=new Map();export const __begin=f=>{active=f;index=0;};export const __reset=()=>slots.clear();
export const useState=initial=>{let s=slots.get(active);if(!s)slots.set(active,s=[]);const i=index++;if(!(i in s))s[i]=typeof initial==='function'?initial():initial;return[s[i],v=>{s[i]=typeof v==='function'?v(s[i]):v;}];};
export const useSyncExternalStore=(_s,get)=>get();export const useEffect=()=>{};export const useRef=v=>({current:v});export const useCallback=f=>f;
`;
async function bundle(entry,hooks=false){
    const r=await build({stdin:{contents:entry,resolveDir:root,loader:"tsx"},bundle:true,platform:"node",format:"cjs",write:false,
        jsx:"transform",jsxFactory:"__element",jsxFragment:"__fragment",tsconfigRaw:{compilerOptions:{jsx:"react",jsxFactory:"__element",jsxFragmentFactory:"__fragment"}},
        plugins:hooks?[{name:"disclosed-inert-hooks",setup(p){p.onResolve({filter:/^(react|fork-first-hooks)$/},()=>({path:"hooks",namespace:"fork-first"}));p.onLoad({filter:/.*/,namespace:"fork-first"},()=>({contents:hookSource,loader:"js"}));p.onLoad({filter:/\.tsx$/},async({path:f})=>({contents:'import {__element,__fragment} from "fork-first-hooks";\n'+await readFile(f,"utf8"),loader:"tsx",resolveDir:path.dirname(f)}));}}]:[]});
    return vm.runInThisContext(`(()=>{const module={exports:{}},exports=module.exports;${r.outputFiles[0].text}\nreturn module.exports;})()`,{timeout:1000,filename:"actual-domain2-fork-first.cjs"});
}
function expand(n,b={n:0}){assert(++b.n<16000,"BoundedActualJSXTree");if(n==null||typeof n==="boolean")return null;if(Array.isArray(n))return n.map(v=>expand(v,b));if(typeof n!=="object")return n;if(typeof n.type==="function"){a.__begin(n.type);return expand(n.type(n.props),b);}if(typeof n.type==="symbol")return expand(n.props.children,b);return{...n,props:{...n.props,children:expand(n.props.children,b)}};}
const text=n=>n==null?"":Array.isArray(n)?n.map(text).join(" "):typeof n==="object"?text(n.props.children):String(n);
const nodes=(n,p)=>n==null||typeof n!=="object"?[]:Array.isArray(n)?n.flatMap(v=>nodes(v,p)):[...(p(n)?[n]:[]),...nodes(n.props.children,p)];
const render=(component,props)=>expand({type:component,props});
function button(tree,label){const found=nodes(tree,n=>n.type==="button"&&text(n).replace(/\s+/g," ").trim()===label);assert.equal(found.length,1,`ActualButton:${label}`);return found[0].props;}
const choose=(tree,label)=>{const found=nodes(tree,n=>n.type==="select"&&n.props["aria-label"]===label);assert.equal(found.length,1,`ActualSelect:${label}`);return found[0];};
function fixture(){
    a.__reset();let c=ctx(), current={id:c.session,scope:copy(c.scope),revision:c.revision}, error=null;
    const calls=[], saved=[], opens=[], refreshes=[], hooks={};
    const outcome=(request,created=true)=>({version:1,scope:{story:request.parent.story,branch:request.child_branch},parent:copy(request.parent),fork_revision:request.at_revision,head_revision:request.at_revision,created});
    const done=(request,id=1)=>({version:1,operation_id:id,running:false,phase:"completed",error:null,result:{kind:"fork",outcome:outcome(request)}});
    const invoke=async(name,args)=>{calls.push({name,args:copy(args)});if(hooks[name])return hooks[name](args);if(name==="fork_boundaries")return raw(c);if(name==="fork_start")return done(args.input);if(name==="fork_lookup")return{version:1,kind:"fork_lookup",found:true,outcome:outcome(args.input,false)};if(name==="archive_cancel")return{};throw Error(`UnexpectedNative:${name}`);};
    const fork=new a.ForkController(invoke,async()=>{refreshes.push("library");},r=>saved.push(copy(r)));
    fork.contextChanged(c);
    const state=()=>({disposed:false,view:c.view,observer:c.observer,workspace:{persistent:c.persistent},play:null,playV2:{scope:copy(c.scope),revision:c.revision},visibleError:error});
    const gameplay={get:state,selected:()=>current,receipt:()=>null,resume:async scope=>{opens.push(copy(scope));if(hooks.open)await hooks.open(scope);current={id:"opened-child",scope:copy(scope),revision:2};c={...c,session:current.id,scope:copy(scope),revision:2};}};
    return{fork,calls,saved,opens,refreshes,hooks,outcome,done,gameplay,get context(){return c;},select(p){c=ctx(p);current={id:c.session,scope:copy(c.scope),revision:c.revision};fork.contextChanged(c);},panel(){return render(a.ForkPanel,{fork,gameplay,context:c});},prepare(child="first-child"){fork.prepare(2,child);},read(){return fork.refreshBoundaries(c);},async ready(){await fork.refreshBoundaries(c);return fork.get().boundaryCatalog;},close(){fork.dispose();}};
}
async function ready(f){const catalog=await f.ready();assert(catalog,"CatalogReady");return catalog;}
async function confirmed(f,child="first-child"){f.prepare(child);f.fork.setConsent(true);await f.fork.confirm(true);assert(S(f).result,"ForkReady");}
function noStart(f,after){assert(!f.calls.slice(after).some(v=>v.name==="fork_start"),"NoStaleFork");}
const S=f=>f.fork.get();
const needStrict=f=>requireApi(f,["matchesContext","refreshBoundaries","prepareFromCatalog","confirmExact","setAdmissionBlocked"]);

test("codec","complete-author-boundaries-and4097-detached-frozen",()=>{
    const input=raw(),v=codec.decodeForkBoundaryCatalog(input,MAIN,7);assert.deepEqual(v.boundaries,[0,2,3,7]);assert(Object.isFrozen(v)&&Object.isFrozen(v.scope)&&Object.isFrozen(v.boundaries));input.boundaries[2]=4;assert.equal(v.boundaries[2],3);
    const full={version:2,scope:MAIN,head:32768,boundaries:[...Array.from({length:4096},(_,i)=>i),32768]};assert.equal(codec.decodeForkBoundaryCatalog(full,MAIN,32768).boundaries.length,4097);
});
test("codec","closed-schema-tuple-number-density-and-budget-refusals",()=>{
    const sparse=raw();delete sparse.boundaries[1];let touched=0;const getter=raw();Object.defineProperty(getter,"head",{enumerable:true,get(){touched++;return 7;}});
    for(const value of [{...raw(),extra:1},{...raw(),version:1},{...raw(),scope:{story:"foreign",branch:"main"}},{...raw(),head:8},raw(ctx(),[0,3,2,7]),raw(ctx(),[0,2,2,7]),raw(ctx(),[2,7]),raw(ctx(),[0,2]),raw(ctx(),[0,NaN,7]),raw(ctx(),[0,Number.MAX_SAFE_INTEGER+1]),raw(ctx(),Array(4098).fill(0)),sparse,getter,Object.assign(Object.create({head:7}),{version:2,scope:MAIN,boundaries:[0,7]}),{...raw(),[Symbol("extra")]:1}])assert.throws(()=>codec.decodeForkBoundaryCatalog(value,MAIN,7),e=>["Wire","Version","Scope","Stale","TooLarge"].includes(e.message));assert.equal(touched,0,"NoGetterExecution");
    for(const[value,error]of [[{...raw(),version:1},"Version"],[{...raw(),scope:{story:"foreign",branch:"main"}},"Scope"],[{...raw(),head:8},"Stale"],[raw(ctx(),Array(4098).fill(0)),"TooLarge"]])assert.throws(()=>codec.decodeForkBoundaryCatalog(value,MAIN,7),e=>e.message===error);
});
test("strict","metadata-exact-native-input-pending-and-context-sequence",async()=>{
    const f=fixture();needStrict(f.fork);const g=gate();f.hooks.fork_boundaries=()=>g.promise;const p=f.read();await tick();assert(S(f).boundaryBusy);assert.deepEqual(f.calls[0],{name:"fork_boundaries",args:{input:{session:f.context.session,scope:MAIN,expected_head:7}}});f.select({observer:"omniscient"});g.resolve(raw());await p;assert.equal(S(f).boundaryCatalog,null);assert(!S(f).boundaryBusy);f.close();
});
test("strict","metadata-error-retry-malformed-and-latest-refresh-only",async()=>{
    const f=fixture();needStrict(f.fork);f.hooks.fork_boundaries=()=>{throw Error("Transport");};await f.read();assert.equal(S(f).boundaryError,"Transport");assert.equal(S(f).boundaryCatalog,null);delete f.hooks.fork_boundaries;await ready(f);const first=gate();let n=0;f.hooks.fork_boundaries=()=>++n===1?first.promise:raw();const p=f.read();await tick();const newer=f.read();await tick();assert.equal(n,2,"NewMetadataRead");await newer;const current=S(f).boundaryCatalog;first.resolve({...raw(),head:8});await p;assert.equal(S(f).boundaryCatalog,current);for(const patch of [{extra:"private"},{version:1}]){f.hooks.fork_boundaries=()=>({...raw(),...patch});await f.read();assert.equal(S(f).boundaryCatalog,null);assert.equal(S(f).boundaryError,patch.version?"Version":"Wire");}f.close();
});
test("strict","prepare-requires-current-whole-catalog-persistent-unblocked",async()=>{
    const f=fixture();needStrict(f.fork);const catalog=await ready(f);for(const [at,cat,c]of [[1,catalog,f.context],[3,copy(catalog),f.context],[3,catalog,ctx({session:"foreign"})]])f.fork.prepareFromCatalog(at,"forbidden",c,cat);assert.equal(f.saved.length,0);f.fork.setAdmissionBlocked(true);f.fork.prepareFromCatalog(3,"blocked",f.context,catalog);assert.equal(f.saved.length,0);f.fork.setAdmissionBlocked(false);f.fork.prepareFromCatalog(3,"author-boundary",f.context,catalog);assert.equal(f.saved[0].at_revision,3);assert.equal(f.saved[0].expected_parent_revision,7);assert.equal(f.calls.filter(v=>v.name==="fork_start").length,0);f.close();
});
test("strict","confirmExact-is-request-and-current-consent-bound",async()=>{
    const f=fixture();needStrict(f.fork);f.prepare();const old=S(f).request;f.fork.setConsent(true);f.prepare("replacement");await f.fork.confirmExact(old,f.context);await f.fork.confirmExact(S(f).request,f.context);assert.equal(f.calls.length,0);f.fork.setConsent(true);await f.fork.confirmExact(S(f).request,f.context);assert.equal(f.calls[0].name,"fork_start");assert.equal(f.calls[0].args.input.child_branch,"replacement");f.close();
});
test("strict","refresh-does-not-retire-pending-fork-or-recovery-identity",async()=>{
    const f=fixture();needStrict(f.fork);const g=gate();f.prepare();const request=S(f).request;f.fork.setConsent(true);await f.read();assert(S(f).consent);f.hooks.fork_start=()=>g.promise;const p=f.fork.confirmExact(request,f.context);await tick();assert(S(f).busy);await f.read();assert.equal(S(f).request,request);assert(S(f).busy&&S(f).consent);f.fork.setAdmissionBlocked(true);assert(S(f).busy);g.resolve(f.done(request));await p;assert.equal(S(f).status,"complete");assert(S(f).result);f.close();
});
test("base","lost-ack-lookup-only-restart-and-cancel-late-commit",async()=>{
    const f=fixture();f.prepare();const request=S(f).request;f.hooks.fork_start=()=>{throw Error("Transport");};await f.fork.confirm(true);assert.equal(S(f).status,"uncertain");f.fork.restore(copy(request));const before=f.calls.length;await f.fork.confirm(true);assert.equal(f.calls.length,before);await f.fork.lookup();assert.equal(S(f).result.created,false);assert.equal(f.calls.at(-1).name,"fork_lookup");
    const h=fixture(),g=gate();h.prepare();const r=S(h).request;h.hooks.fork_start=()=>g.promise;const p=h.fork.confirm(true);await tick();await h.fork.cancel();g.resolve(h.done(r));await p;assert.equal(S(h).status,"complete");assert.equal(S(h).result.scope.branch,r.child_branch);f.close();h.close();
});
test("panel","full-author-boundary-options-no-receipt-or-head-shortcut",async()=>{
    const f=fixture();needStrict(f.fork);await ready(f);f.prepare();const tree=f.panel(),select=choose(tree,"Fork completed boundary");assert.deepEqual(nodes(select,n=>n.type==="option").map(n=>Number(n.props.value)),[0,2,3,7]);assert(text(tree).includes("7"));f.hooks.fork_boundaries=()=>{throw Error("Transport");};await f.read();assert(text(f.panel()).includes("Transport"));assert(button(f.panel(),"Prepare new timeline").disabled);const g=gate();f.hooks.fork_boundaries=()=>g.promise;const p=f.read();await tick();assert(button(f.panel(),"Prepare new timeline").disabled);g.resolve(raw());await p;f.fork.setAdmissionBlocked(true);assert(button(f.panel(),"Prepare new timeline").disabled);f.close();
});
test("panel","retained-Prepare-all-context-dimensions-cannot-save",async()=>{
    for(const patch of changed){const f=fixture();f.prepare();const old=button(f.panel(),"Prepare new timeline"),n=f.saved.length;f.select(patch);old.onClick();await tick();assert.equal(f.saved.length,n,"OldPrepareCannotRebindCurrentStory");f.close();}
});
test("panel","retained-consent-confirm-and-same-context-request-replacement",async()=>{
    const f=fixture();f.prepare();f.fork.setConsent(true);const tree=f.panel(),oldConfirm=button(tree,"Confirm new timeline"),oldConsent=nodes(tree,n=>n.type==="input"&&n.props.type==="checkbox")[0].props;f.prepare("new-request");oldConsent.onChange({target:{checked:true}});assert.equal(S(f).consent,false);oldConfirm.onClick();await tick();noStart(f,0);f.close();
    for(const patch of changed){const h=fixture();h.prepare();h.fork.setConsent(true);const click=button(h.panel(),"Confirm new timeline").onClick;h.select(patch);click();await tick();noStart(h,0);h.close();}
});
test("panel","retained-lookup-all-contexts-and-replacement-request",async()=>{
    for(const patch of [...changed,null]){const f=fixture();f.prepare();const old=button(f.panel(),"Check saved child only");if(patch)f.select(patch);else f.prepare("replacement");const n=f.calls.length;old.onClick();await tick();assert.equal(f.calls.length,n);f.close();}
});
test("panel","retained-cancel-cannot-cancel-new-operation",async()=>{
    const f=fixture();const first=gate(),second=gate();f.prepare();const r=S(f).request;f.hooks.fork_start=()=>first.promise;const p=f.fork.confirm(true);await tick();const old=button(f.panel(),"Cancel pending fork");f.select({session:"replacement-session"});first.resolve(f.done(r));await p;f.fork.restore(null);f.prepare("new-active");const current=S(f).request;f.hooks.fork_start=()=>second.promise;const next=f.fork.confirm(true);await tick();old.onClick();await tick();second.resolve({version:1,operation_id:8,running:true,phase:"forking",error:null,result:null});f.hooks.archive_status=()=>f.done(current,8);await next;assert(!f.calls.some(v=>v.name==="archive_cancel"&&v.args.operationId===8),"OldCancelCannotSetNewCancelIntent");f.close();
});
test("panel","retained-Open-context-result-and-late-error-fences",async()=>{
    for(const patch of changed){const f=fixture();await confirmed(f);const open=button(f.panel(),"Open confirmed child");f.select(patch);open.onClick();await tick();assert.equal(f.opens.length,0);f.close();}
    const f=fixture();await confirmed(f);const open=button(f.panel(),"Open confirmed child");await confirmed(f,"replacement-result");open.onClick();await tick();assert.equal(f.opens.length,0);const wait=gate();f.hooks.open=()=>wait.promise;button(f.panel(),"Open confirmed child").onClick();await tick();f.select({session:"after-open"});wait.reject(Error("Transport"));await tick();assert(!text(f.panel()).includes("could not be opened"));f.close();
});
test("panel","retained-refresh-and-consent-cannot-touch-new-context",async()=>{
    for(const patch of changed){const f=fixture();needStrict(f.fork);await ready(f);f.prepare();const tree=f.panel(),refresh=button(tree,"Refresh completed boundaries"),consent=nodes(tree,n=>n.type==="input"&&n.props.type==="checkbox")[0].props;f.select(patch);const n=f.calls.length;refresh.onClick();consent.onChange({target:{checked:true}});await tick();assert.equal(f.calls.length,n);assert.equal(S(f).consent,false);f.close();}
});
test("strict","catalog-preparation-subscriber-retirement-and-consent-clear",async()=>{
    const f=fixture();needStrict(f.fork);const catalog=await ready(f);let once=false;const release=f.fork.subscribe(()=>{if(!once&&S(f).request){once=true;f.select({session:"retired-during-save"});}});f.fork.prepareFromCatalog(3,"reentrant",f.context,catalog);await f.fork.confirmExact(S(f).request,ctx());noStart(f,0);assert(S(f).lookupOnly);release();f.fork.setConsent(true);const saved=S(f).request;f.fork.setAdmissionBlocked(true);assert(!S(f).consent);assert.equal(S(f).request,saved);f.close();
    const h=fixture();h.prepare();const request=S(h).request;h.fork.setConsent(true);const stop=h.fork.subscribe(()=>{if(S(h).busy)h.fork.setAdmissionBlocked(true);});await h.fork.confirm(true);noStart(h,0);assert.equal(S(h).request,request);assert.equal(S(h).status,"prepared");assert.equal(S(h).error,"Busy");assert(!S(h).busy&&!S(h).consent);assert.equal(S(h).operation,null);stop();const before=h.saved.length;h.fork.prepare(3,"blocked-direct");await h.fork.confirm(true);assert.equal(h.saved.length,before);noStart(h,0);h.close();
});
test("main","actual-Main-admission-notifications-clear-consent-not-gameplay",async()=>{
    const functionText=(name,end)=>{const start=mainSource.indexOf(name);assert(start>=0,`UNRUN_SETUP:${name}`);const stop=mainSource.indexOf(end,start);assert(stop>start,`UNRUN_SETUP:${name}:end`);return mainSource.slice(start,stop+end.length);};
    const sync=functionText("function syncForkAdmission(","\n}"),evaluation=functionText("const syncEvaluationContext =", "\n};");
    const start=mainSource.indexOf("const releaseEvaluationContext ="),end=mainSource.indexOf("const releaseAuthorContext =",start);assert(start>=0&&end>start,"UNRUN_SETUP:ActualSubscriptions");
    const callbacks={},calls=[],gs={starting:false,pending:null,disposed:false,selectedId:"s",workspace:{persistent:true},play:null,playV2:{scope:MAIN,revision:7,player:{observer:"native-73"}},view:"play",observer:"player"},vs={pending:null,uncertain:null};
    const no=()=>{},surface={contextChanged:no,setContext:no,get:()=>({})};const controller={get:()=>gs,selected:()=>({id:"s",scope:MAIN,revision:7}),traceAttempt:()=>null,subscribe:f=>{callbacks.controller=f;return no;}};
    const current=()=>ctx({session:"s",revision:gs.playV2.revision}),v2={get:()=>vs,subscribe:f=>{callbacks.v2=f;return no;}};let held=current(),order="v2-first";
    const same=c=>JSON.stringify(c)===JSON.stringify(held),fork={matchesContext:same,contextChanged:c=>{held=c;if(order==="fork-first")callbacks.v2?.();},setAdmissionBlocked:v=>{calls.push(v);if(!v)assert(same(current()),"NoUnblockBeforeForkContextSync");}};
    const ambient={stopping:false,controller,v2,fork,syncV2Context:()=>{if(order==="v2-first")callbacks.v2?.();},syncTraceGameplayFence:no,author:surface,authorContext:()=>null,maintenance:surface,memoryContext:()=>null,memoryInspection:surface,memoryInspectionContext:()=>null,timeline:surface,timelineContext:current,capture:surface,evaluation:surface,comparison:surface,comparisonRun:surface,nativeComparisonRun:surface,selectedEvaluation:surface,archive:surface,authorNativeContext:null};
    const code=(await transform(`let memorySelectionKey="",memorySelectionEpoch=0;${sync}\n${evaluation}\n${mainSource.slice(start,end)}\nexport {syncForkAdmission};`,{loader:"ts",format:"cjs"})).code;const module={exports:{}};vm.compileFunction(code,["module","exports",...Object.keys(ambient)])(module,module.exports,...Object.values(ambient));
    for(const [target,key]of [[gs,"starting"],[gs,"pending"],[gs,"disposed"],[vs,"pending"],[vs,"uncertain"]]){target[key]=true;(target===gs?callbacks.controller:callbacks.v2)();assert.equal(calls.at(-1),true,`ActualNotificationBlocks:${key}`);target[key]=key==="starting"||key==="disposed"?false:null;(target===gs?callbacks.controller:callbacks.v2)();assert.equal(calls.at(-1),false);}assert.equal(Object.keys(callbacks).length,2);
    for(const next of ["v2-first","fork-first"]){order=next;gs.playV2={...gs.playV2,revision:gs.playV2.revision+1};callbacks.controller();assert.equal(calls.at(-1),false,"UnblockedOnlyAfterContextReconciles");}
});

function thin(scope=MAIN,revision=7,domain=2){return{version:2,domain_version:domain,scope:copy(scope),revision,rules:"fantasy_v1",player:{observer:"native-73",self_state:{name:"Synthetic",location:"quay",alive:true,energy:2,abilities:{},attributes:{},injuries:[],affiliations:[],goals:[]}},inventory:{}};}
async function appFixture(domain=2){const calls=[];const gateway={playSnapshotV2:true,async call(q){calls.push(copy(q));if(q.op==="workspace")return{persistent:true,location:"synthetic",schema_version:1,database_schema_version:5,stories:[{scope:MAIN,title:"Synthetic",revision:7,drafts:0}]};if(q.op==="resume")return{session:"native-session-73",scope:copy(q.scope),revision:7,drafts:0};if(q.op==="open")return{revision:7};if(q.op==="close")return{};if(q.op==="play_snapshot_v2")return thin(q.scope,q.expected_revision,domain);if(q.op==="play_snapshot")return{scope:copy(q.scope),revision:q.expected_revision,rules:"fantasy_v1",player:{scope:copy(q.scope),revision:q.expected_revision,observer:"native-73",self_state:{name:"Synthetic",location:"quay",energy:2},facts:{},beliefs:[],observations:[]},inventory:{},receipts:[]};if(q.op==="inspect")return{};throw Error(`UnexpectedGameplay:${q.op}`);}};const c=new a.Controller(gateway);await c.library();await c.resume(MAIN);const fork=new a.ForkController(async()=>{throw Error("NoNativeOnRender");},async()=>{},()=>{});fork.contextChanged(a.timelineContext(c));const v2=new a.V2PlayController(gateway,async()=>{},"fork-first");const sync=async()=>{const s=c.get(),selected=c.selected();v2.selectedContextChanged(s.playV2?{session:selected.id,scope:selected.scope,revision:s.playV2.revision,player:s.playV2.player.observer,view:s.view,observer:s.observer==="player"?{kind:"player"}:{kind:"omniscient"},persistent:true,pending:false,blocked:false,playMode:s.playMode,inputKind:s.inputKind,action:s.action,fakeMode:s.fakeMode}:null);if(s.playV2)await v2.refresh(false);};await sync();return{c,fork,v2,calls,sync,async close(){fork.dispose();v2.dispose();await c.dispose();}};}
test("base","actual-App-exposes-coherent-Domain2-Play-Lab-and-legacy",async()=>{
    for(const domain of [1,2]){const f=await appFixture(domain);a.__reset();assert(text(render(a.App,{controller:f.c,fork:f.fork,v2:f.v2})).includes("Create alternate timeline"));f.c.requestLab();f.c.acknowledgeLab(true);f.fork.contextChanged(a.timelineContext(f.c));await f.sync();a.__reset();assert(text(render(a.App,{controller:f.c,fork:f.fork,v2:f.v2})).includes("Create alternate timeline"));assert(f.calls.every(q=>["workspace","resume","open","close","play_snapshot_v2","play_snapshot","inspect"].includes(q.op)),"ActualAppReadOnlyRoster:"+JSON.stringify({domain,total:f.calls.length,ops:f.calls.slice(0,32).map(q=>q.op)}).slice(0,700));await f.close();}
});
test("base","explicit-Open-exact-child-no-generation-or-private-input",async()=>{
    const f=fixture();await confirmed(f);const before=f.calls.length;button(f.panel(),"Open confirmed child").onClick();await tick();assert.deepEqual(f.opens,[{story:MAIN.story,branch:"first-child"}]);assert.equal(f.calls.length,before);assert(f.calls.every(q=>["fork_start","fork_lookup","archive_status","archive_cancel"].includes(q.name)));assert.equal(f.gameplay.get().playV2.revision,2);f.close();
});
test("base","legacy-explicit-prepare-confirm-and-render-have-no-auto-retry",async()=>{
    const f=fixture();f.prepare();assert.equal(f.saved.length,1);assert.equal(f.calls.length,0);f.panel();f.panel();assert.equal(f.calls.length,0);await f.fork.confirm(false);assert.equal(f.calls.length,0);await f.fork.confirm(true);const request=S(f).request;assert.deepEqual(f.calls[0].args.input,request);f.fork.restore(copy(request));const n=f.calls.length;await f.fork.confirm(true);assert.equal(f.calls.length,n);f.close();
});

// Post-FIRST review regression, authored after finding/fix; not an observed RED.
test("strict","transient-admission-block-revokes-consent-before-both-confirm-APIs",async()=>{
    for(const exact of [false,true]){
        const f=fixture();needStrict(f.fork);f.prepare("same-saved-child");const request=S(f).request,saved=copy(f.saved);f.fork.setConsent(true);let once=false;
        const release=f.fork.subscribe(()=>{if(!once&&S(f).busy){once=true;f.fork.setAdmissionBlocked(true);f.fork.setAdmissionBlocked(false);}});
        if(exact)await f.fork.confirmExact(request,f.context);else await f.fork.confirm(true);
        assert(once);assert.equal(f.calls.length,0);assert.equal(S(f).request,request);assert.deepEqual(f.saved,saved);assert.equal(S(f).status,"prepared");assert.equal(S(f).error,"ForkConsentRequired");assert.equal(S(f).operation,null);assert(!S(f).busy&&!S(f).consent&&!S(f).admissionBlocked);
        release();f.fork.setConsent(true);await f.fork.confirmExact(request,f.context);assert.equal(f.calls.length,1);assert.equal(f.calls[0].name,"fork_start");assert.deepEqual(f.calls[0].args.input,request);assert.equal(S(f).status,"complete");f.close();
    }
});

assert.equal(cases.length,21,"FrozenTwentyGroupsPlusOneReviewRegression");
try{for(const name of ["fork-controller.ts","ForkPanel.tsx","App.tsx","main.tsx","timeline-controller.ts","model.ts"]){source[name]=await readFile(path.join(root,"ui",name),"utf8");}mainSource=source["main.tsx"];a=await bundle('export {ForkController} from "./ui/fork-controller";export {ForkPanel} from "./ui/ForkPanel";export {App} from "./ui/App";export {Controller} from "./ui/controller";export {V2PlayController} from "./ui/v2-play-controller";export {timelineContext} from "./ui/timeline-controller";export {__begin,__reset} from "fork-first-hooks";',true);}catch(e){baseFailure=String(e);setup.push({stage:"actual-frontend",classification:"UNRUN_SETUP",error:String(e).slice(0,700)});}
try{source["fork-boundary-model.ts"]=await readFile(path.join(root,"ui/fork-boundary-model.ts"),"utf8");codec=await bundle('export {decodeForkBoundaryCatalog} from "./ui/fork-boundary-model";');requireApi(codec,["decodeForkBoundaryCatalog"]);}catch(e){codecFailure=String(e);setup.push({stage:"new-actual-codec",classification:"UNRUN_SETUP",error:String(e).slice(0,700)});}
for(const item of cases){try{if((item.need==="codec"&&codecFailure)||(item.need!=="codec"&&baseFailure))throw Error("UNRUN_SETUP:ActualModuleUnavailable");if(item.need==="strict"||item.need==="panel"&&["full-author","retained-refresh"].some(s=>item.name.startsWith(s))){const f=fixture();try{needStrict(f.fork);}finally{f.close();}}await item.run();results.push({name:item.name,status:"PASS"});}catch(e){const message=String(e);results.push({name:item.name,status:message.includes("UNRUN_SETUP:")?"UNRUN_SETUP":"FAIL",error:message.slice(0,900)});}}
for(const[name,value]of Object.entries(source))assert.equal(sha(await readFile(path.join(root,"ui",name),"utf8")),sha(value),`ActualSourceUnchanged:${name}`);
const report={kind:"d08_domain2_fork_independent_first_v1",authored:cases.length,executed:results.filter(r=>r.status!=="UNRUN_SETUP").length,passed:results.filter(r=>r.status==="PASS").length,failed:results.filter(r=>r.status==="FAIL").length,unrun:results.filter(r=>r.status==="UNRUN_SETUP").length,setup,results,source:Object.fromEntries(Object.entries(source).map(([k,v])=>[k,sha(v)])),evidence:{actual:"codec/controller/App/Panel/Main",render:"inert hooks/JSX callbacks",transport:"synthetic invoke/Gateway",native:false,rust:false,persistence:false,generation:false,browser:false,pixels:false,desktop:false},limits:["Group21 is post-finding/fix review regression, not FIRST or observed RED","Author UNRUN; separate owner resource admission required","Missing API is SETUP; old handlers independent","Synthetic metadata is not accepted history; no copied validator","No mounted effects/DOM/focus/CSS/a11y; actual Main subscriptions tested separately","No file outputs/newroot/old test edits; report64KiB; no app/build permission"]};const encoded=JSON.stringify(report);assert(Buffer.byteLength(encoded)+1<=65536,"BoundedForkReviewReport");console.log(encoded);process.exitCode=setup.length||report.unrun?2:report.failed||!report.executed?1:0;

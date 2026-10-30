// Fixed development-only synthetic journey. Source author UNRUN.
// Actual Main/controller/native paths and app-owned renders; no desktop input.
import type { Controller } from "./controller";
import { isForkError, type ForkController, type ForkRequest } from "./fork-controller";
import type { TimelineController } from "./timeline-controller";
import { timelineContext } from "./timeline-controller";
import type { V2PlayController } from "./v2-play-controller";
import { category, structural, type ErrorBuffer, type Scope } from "./model";
import { createDomain2ForkFinalizer } from "./domain2-fork-native-finalization";

type Invoke = (name: string, args?: Record<string, unknown>) => Promise<unknown>;
type TraceRow = {
    sequence: number; channel: "host" | "main-native" | "raw-probe";
    command: string; session: string | null; scope: Scope | null; head: number | null;
    child: string | null; point: number | null; operationId: number | null;
    nativeSettled: boolean; settled: boolean; error: string | null;
    replySha256: string | null; delivery: "normal" | "held" | "local-Transport";
};
type Delivery = {
    kind: "hold" | "error"; entered: boolean; nativeSettled: boolean;
    row: TraceRow | null; release: () => void; waiting: Promise<void>;
};
type OracleRow = {
    scope: Scope; domain_version: number; head: number; story_time: number;
    boundaries: number[]; canonical_records: number; ordinary_receipts: number;
    seed_sha256: string; projection_sha256: string; records_sha256: string;
    receipts_sha256: string; actors_sha256: string; turns_sha256: string | null;
};
type Oracle = {
    version: number; fixture_version: number; kind: string; scopes: OracleRow[];
    children: { scope: Scope; parent: Scope; fork_revision: number;
        core_prefix_matches: boolean; expected: Omit<OracleRow,"turns_sha256"> }[];
};
const MODE = "domain2_fork_v1";
const LABELS = ["catalog","rejected","pending","preauthor","authored","recovered","enlarged"].map(name => `d08-fork-${name}`);
const AUTHOR: Scope = { story: "d08-fork-native", branch: "authored" };
const ORIGINALS = [
    [{ story: "d08-fork-native", branch: "main" },1,2],
    [AUTHOR,2,3], [{ story: "d08-fork-native", branch: "sibling" },1,2],
    [{ story: "d08-fork-other", branch: "main" },1,0],
] as const;
const HEX = /^[a-f0-9]{64}$/, UUID = /^[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/;
const FORK_CALLS = new Set(["fork_boundaries","fork_start","fork_lookup","archive_status","archive_cancel"]);
const HOST_READS = new Set(["workspace","resume","open","close","play_snapshot","play_snapshot_v2","inspect","inspection_query","branches","trace_capture_revoke","model_status"]);
const NATIVE_READS = new Set(["author_context","model_status","inspection_storage","capture_revoke"]);
const object = (value: unknown): Record<string, unknown> => value && typeof value === "object" && !Array.isArray(value) ? value as Record<string,unknown> : {};
const boundedId = (value: unknown, max=64) => typeof value === "string" && value.length > 0 && value.length <= max && /^[A-Za-z0-9_-]+$/.test(value) ? value : null;
const scoped = (value: unknown): Scope | null => {
    const r=object(value), story=boundedId(r.story), branch=boundedId(r.branch);
    return story && branch ? {story,branch} : null;
};
const integer = (value: unknown) => Number.isSafeInteger(value) && Number(value)>=0 ? Number(value) : null;
const forkError = (error: unknown) => { const value=error instanceof Error?error.message:String(error);return isForkError(value)?value:category(error); };
function digest(value: unknown): Promise<string> {
    const bytes=new TextEncoder().encode(JSON.stringify(value));
    if(bytes.length>262144) return Promise.reject(Error("D08ForkTraceReplyBudget"));
    return crypto.subtle.digest("SHA-256",bytes).then(result=>[...new Uint8Array(result)].map(n=>n.toString(16).padStart(2,"0")).join(""));
}

// Owned only by this fixed mode. Main installs it at the actual dispatch boundary;
// no renderer-global hook, arbitrary raw-invoke export or body cache is created.
export class Domain2ForkTrace {
    readonly rows: TraceRow[]=[];
    delivery: Delivery | null=null;
    hostReads=0; forkCalls=0;
    armBoundaryDelivery(kind: "hold" | "error") {
        if(this.delivery) throw Error("D08ForkDeliveryAlreadyArmed");
        let release!:()=>void;
        const waiting=new Promise<void>(resolve=>{release=resolve;});
        this.delivery={kind,entered:false,nativeSettled:false,row:null,release,waiting};
        return this.delivery;
    }
    releaseDelivery() { this.delivery?.release(); this.delivery=null; }
    dispatch(command: string, args: Record<string,unknown>, work:()=>Promise<unknown>, probe=false): Promise<unknown> {
        if(command.startsWith("harness_")) return work(); // Separate fixed harness evidence.
        let op=command, binding=object(args.input), host=false;
        if(command==="host_call") {
            if(typeof args.input!=="string" || new TextEncoder().encode(args.input).length>262144) return Promise.reject(Error("D08ForkTraceWire"));
            try { const input=JSON.parse(args.input); if(input.version!==1) throw Error("Wire"); binding=object(input.command); op=String(binding.op); } catch { return Promise.reject(Error("D08ForkTraceWire")); }
            if(!HOST_READS.has(op)) return Promise.reject(Error("D08ForkForbiddenHostWrite"));
            host=true;
        } else if(!FORK_CALLS.has(command) && !NATIVE_READS.has(command)) return Promise.reject(Error("D08ForkForbiddenNativeCall"));
        if(this.rows.length>=256 || (host && this.hostReads>=64) || (FORK_CALLS.has(command)&&this.forkCalls>=128)) return Promise.reject(Error("D08ForkTraceBudget"));
        if(host) this.hostReads++; if(FORK_CALLS.has(command)) this.forkCalls++;
        const query=object(binding.query), parent=scoped(binding.parent), own=scoped(binding.scope)??scoped(query.scope)??parent;
        const id=integer(args.operationId), previous=id===null?null:this.rows.find(row=>row.operationId===id && row.child!==null);
        const row: TraceRow={sequence:this.rows.length+1,channel:probe?"raw-probe":host?"host":"main-native",command:op,
            session:boundedId(args.session??binding.session,128)??previous?.session??null,scope:own??previous?.scope??null,
            head:integer(binding.expected_parent_revision??binding.expected_head??binding.expected_revision??query.expected_head)??previous?.head??null,
            child:boundedId(binding.child_branch)??previous?.child??null,point:integer(binding.at_revision)??previous?.point??null,
            operationId:id,nativeSettled:false,settled:false,error:null,replySha256:null,delivery:"normal"};
        this.rows.push(row);
        return Promise.resolve().then(work).then(value=>digest(value).then(hash=>{
            row.nativeSettled=true;row.replySha256=hash;
            const result=object(value); row.operationId=integer(result.operation_id)??row.operationId;
            const held=this.delivery;
            if(command==="fork_boundaries"&&held&&!held.entered) {
                held.entered=true;held.nativeSettled=true;held.row=row;
                if(held.kind==="error") {row.delivery="local-Transport";this.delivery=null;throw Error("Transport");}
                row.delivery="held";return held.waiting.then(()=>value);
            }
            return value;
        }),error=>{row.nativeSettled=true;row.error=forkError(error);throw error;}).then(value=>{row.settled=true;return value;},error=>{row.settled=true;throw error;});
    }
}

export async function domain2ForkNativeJourneys({controller:c,fork:f,timeline,v2,errors,invoke,trace,dispose}:{
    controller:Controller;fork:ForkController;timeline:TimelineController;v2:V2PlayController;
    errors:ErrorBuffer;invoke:Invoke;trace:Domain2ForkTrace;dispose:()=>Promise<void>;
}): Promise<void> {
    // d08-fork-finalizer-owner-v1:start
    const finish = createDomain2ForkFinalizer(report => invoke("harness_finish", {report}));
    // d08-fork-finalizer-owner-v1:end
    const checks:string[]=[], names=new Set<string>(), captures:string[]=[], refs:{label:string;json:string;count:number}[]=[];
    const observations:Record<string,unknown>[]=[], proofs:{label:string;oracle:Oracle}[]=[], fonts:Record<string,unknown>[]=[], receipts:Record<string,unknown>[]=[];
    const roles:Record<string,ForkRequest>={}, outcomes:Record<string,unknown>={};
    let baseline:Oracle|null=null, finalOracle:Oracle|null=null, assertions=0, phase="setup", disposed=false;
    const deadline=performance.now()+150000;
    const check=(value:unknown,name:string)=>{phase=name;if(!value)throw Error(name);assertions++;if(!names.has(name)){names.add(name);checks.push(name);}};
    const until=async(test:()=>boolean,name:string)=>{phase=name;for(let n=0;n<1500&&performance.now()<deadline;n++){if(test())return;await new Promise(resolve=>setTimeout(resolve,10));}throw Error(`D08Domain2ForkDeadline:${name}`);};
    const frames=()=>new Promise<void>((resolve,reject)=>{const timer=setTimeout(()=>reject(Error("D08ForkFramesTimeout")),5000);requestAnimationFrame(()=>requestAnimationFrame(()=>{clearTimeout(timer);resolve();}));});
    const idle=async()=>{await until(()=>!c.get().starting&&!f.get().boundaryBusy&&!f.get().busy&&!v2.get().readBusy&&!v2.get().queryBusy&&trace.rows.every(row=>row.settled),"owned-read-deliveries-idle");await frames();};
    const panel=()=>document.querySelector<HTMLElement>(".fork-panel");
    const text=(node:Element)=>node.textContent?.replace(/\s+/g," ").trim()??"";
    const button=(label:string,owner:ParentNode=document)=>{const all=[...owner.querySelectorAll<HTMLButtonElement>("button")].filter(node=>text(node)===label);check(all.length===1,`unique-button:${label}`);return all[0];};
    const click=(node:HTMLButtonElement,label:string)=>{check(node.isConnected&&!node.disabled,`enabled-owned-control:${label}`);node.click();};
    const select=(label:string)=>{const nodes=[...document.querySelectorAll<HTMLSelectElement>("select")].filter(node=>node.getAttribute("aria-label")===label||node.closest("label")?.textContent?.trim().startsWith(label));check(nodes.length===1,`unique-select:${label}`);return nodes[0];};
    const choose=(node:HTMLSelectElement,value:string)=>{check(node.isConnected&&!node.disabled&&[...node.options].some(option=>option.value===value),"actual-select-available-option");const setter=Object.getOwnPropertyDescriptor(HTMLSelectElement.prototype,"value")?.set;check(setter,"native-DOM-select-setter");setter!.call(node,value);node.dispatchEvent(new Event("change",{bubbles:true}));};
    const consent=()=>{const node=panel()?.querySelector<HTMLInputElement>(".fork-consent input");check(node&&node.isConnected&&!node.disabled,"current-fork-consent-control");if(!node!.checked)node!.click();};
    const fixture=(action:"hold"|"release"|"lose-ack"|"domain2-oracle")=>invoke("harness_fork_case",{action});
    const raw=(command:"fork_start"|"fork_lookup"|"archive_status",args:Record<string,unknown>)=>trace.dispatch(command,args,()=>window.__TAURI__.core.invoke(command,args),true);
    const cancelledAtNative=(id:number)=>until(()=>trace.rows.some(row=>row.command==="archive_cancel"&&row.operationId===id&&row.nativeSettled&&row.settled&&row.error===null),"actual-native-cancel-observed-before-release");
    const owner=(scope:Scope,head:number,domain:1|2)=>{const s=c.get(),selected=c.selected(),play=s.play??s.playV2;check(selected&&play&&structural(selected.scope)===structural(scope)&&structural(play.scope)===structural(scope)&&selected.revision===head&&play.revision===head,"selected-scope-head-owned");check(domain===2?s.playV2?.domain_version===2&&!s.play:!!s.play&&!s.playV2,"actual-domain-route");const context=timelineContext(c);check(context&&context.session===selected!.id&&context.revision===head&&f.matchesContext(context)&&context.persistent,"fork-context-exact-current");};
    const ready=async()=>{
        if(!panel())click(button(f.get().request?"Timeline creation & recovery":"Create alternate timeline"),"open-fork-panel");
        await frames();
        if(!f.get().boundaryCatalog&&!f.get().boundaryBusy)click(button("Refresh completed boundaries",panel()!),"refresh-boundaries");
        await until(()=>!!f.get().boundaryCatalog&&!f.get().boundaryBusy,"actual-full-boundary-catalog");await idle();
        check(!f.get().boundaryError,"boundary-ready-without-error");
        const catalog=f.get().boundaryCatalog!,selected=c.selected()!;
        check(structural(catalog.scope)===structural(selected.scope)&&catalog.head===(c.get().play??c.get().playV2)!.revision,"catalog-owned-current-head");
        const options=[...select("Fork completed boundary").options].map(option=>Number(option.value));
        check(structural(options)===structural(catalog.boundaries),"UI-options-are-complete-Core-catalog");
        check(!/D08_PRIVATE_AUTHOR_TRUTH_422|D08_PRIVATE_AUTHOR_REASON_423|D08_OTHER_STORY_TRUTH_424/.test(JSON.stringify(catalog)),"neutral-catalog-has-no-private-bodies");
    };
    const observe=(label:string,source:string)=>{const snapshot=semantic(),value={label,source,...snapshot,dom:{...snapshot.dom,text:snapshot.dom.text.slice(0,1024)}};check(new TextEncoder().encode(JSON.stringify(value)).length<=8192,"bounded-intermediate-semantic-state");observations.push(value);check(observations.length<=18,"bounded-intermediate-observation-count");};
    const semantic=()=>{
        const s=c.get(),fork=f.get(),selected=c.selected(),play=s.play??s.playV2,receipt=c.receipt(),actual=document.querySelector<HTMLElement>('[aria-label="Actual native receipt"]');
        return{synthetic:true,semanticVersion:1,mode:MODE,selectedStory:selected?.scope??null,session:selected?.id??null,revision:play?.revision??null,observer:s.view==="play"?"player":s.observer,view:s.view,
            pendingOperation:fork.busy?{phase:fork.status,operation:fork.operation}:null,gameplayPending:s.pending?{stage:s.pending.stage}:v2.get().pending?{stage:v2.get().pending!.stage}:null,
            displayedReceipt:actual?{displayed:true,source:"mounted-native-receipt",text:actual.innerText.slice(0,2048),turn:v2.get().receipt?.request.turn??null}:receipt?{displayed:!!panel()?.querySelector(".fork-receipt"),source:"legacy-selected-player-receipt",turn:receipt.request.turn,originalScope:receipt.request.scope,revision:receipt.events.at(-1)?.sequence??null}:{displayed:false,source:"no-mounted-or-selected-receipt",turn:null},
            fork:{boundaryBusy:fork.boundaryBusy,boundaryError:fork.boundaryError,boundaryCatalog:fork.boundaryCatalog,request:fork.request,consent:fork.consent,admissionBlocked:fork.admissionBlocked,status:fork.status,operation:fork.operation,result:fork.result,lookupOnly:fork.lookupOnly,notice:fork.notice},
            visibleError:fork.boundaryError??fork.error??v2.get().error??s.visibleError,renderedForkAlert:panel()?.querySelector<HTMLElement>('[role="alert"]')?.innerText.slice(0,256)??null,v2Availability:{snapshot:!!v2.get().snapshot,history:!!v2.get().history},dom:{controls:[...(panel()?.querySelectorAll<HTMLElement>("button,select,input,[role]")??[])].slice(0,24).map(node=>({tag:node.tagName,role:node.getAttribute("role"),label:text(node).slice(0,96),disabled:"disabled"in node?node.disabled:null,value:node instanceof HTMLSelectElement?node.value:null,checked:node instanceof HTMLInputElement?node.checked:null,focused:node===document.activeElement})),text:panel()?.innerText.slice(0,4096)??"",width:innerWidth,height:innerHeight,textScale:s.textScale,active:document.activeElement?.tagName??null,userAgent:navigator.userAgent},errors:errors.snapshot()};
    };
    const oracle=async(label:string)=>{
        const value=await fixture("domain2-oracle") as Oracle;
        check(value&&value.version===1&&value.fixture_version===1&&value.kind==="domain2_fork_native_oracle_v1"&&Object.keys(value).sort().join(",")==="children,fixture_version,kind,scopes,version"&&Array.isArray(value.scopes)&&Array.isArray(value.children),`${label}-closed-Rust-oracle`);
        check(new TextEncoder().encode(JSON.stringify(value,null,2)).length<=32768,`${label}-bounded-neutral-oracle`);
        check(!/D08_PREFIX_MIRA_ONLY_421|D08_PRIVATE_AUTHOR_TRUTH_422|D08_PRIVATE_AUTHOR_REASON_423|D08_OTHER_STORY_TRUTH_424|self_state|known_by/.test(JSON.stringify(value)),`${label}-oracle-hashes-not-bodies`);
        ORIGINALS.forEach(([scope,domain,head],i)=>{const row=value.scopes[i];check(row&&structural(row.scope)===structural(scope)&&row.domain_version===domain&&row.head===head,`${label}-original${i}-scope-domain-head`);for(const key of["seed_sha256","projection_sha256","records_sha256","receipts_sha256","turns_sha256","actors_sha256"] as const)check(typeof row[key]==="string"&&HEX.test(row[key]!),`${label}-original${i}-${key}`);});
        if(baseline)check(structural(value.scopes.slice(0,4))===structural(baseline.scopes.slice(0,4)),`${label}-four-original-canonical-observer-lookup-fingerprints-unchanged`);
        for(const child of value.children){const row=value.scopes.find(row=>structural(row.scope)===structural(child.scope));check(row&&UUID.test(child.scope.branch)&&row.turns_sha256===null&&child.core_prefix_matches&&structural(child.parent)===structural(AUTHOR),`${label}-child-Core-proof-no-fabricated-turn-rows`);const{turns_sha256:_unavailable,...core}=row!;check(structural(core)===structural(child.expected),`${label}-actual-child-equals-Core-prefix`);}
        proofs.push({label,oracle:value});check(proofs.length<=6,"bounded-oracle-observation-count");return value;
    };
    const rawTerminal=async(commandArgs:Record<string,unknown>)=>{
        let value=object(await raw("fork_start",commandArgs));
        check(integer(value.operation_id)!==null,"raw-native-probe-operation-identity");
        for(let n=0;n<120&&value.running===true;n++){await new Promise(resolve=>setTimeout(resolve,10));value=object(await raw("archive_status",{operationId:value.operation_id}));}
        check(value.running===false,"raw-native-probe-settled");return value;
    };
    const prepare=async(at:0|2|3,role:string)=>{
        await ready();choose(select("Fork completed boundary"),String(at));await frames();const before=trace.rows.filter(row=>row.command==="fork_start").length;
        click(button("Prepare new timeline",panel()!),`prepare-${role}`);await frames();const request=f.get().request;
        check(request&&UUID.test(request.child_branch)&&structural(request.parent)===structural(c.selected()!.scope)&&request.at_revision===at&&request.expected_parent_revision===(c.get().play??c.get().playV2)!.revision,`${role}-actual-UI-generated-exact-identity`);
        check(!Object.values(roles).some(old=>old.child_branch===request!.child_branch),`${role}-new-UUID-not-reused`);roles[role]=structuredClone(request!);
        check(localStorage.getItem("locallore-fork-recovery-v1")===JSON.stringify(request),`${role}-exact-recovery-saved-before-dispatch`);
        check(trace.rows.filter(row=>row.command==="fork_start").length===before,`${role}-render-prepare-never-forks`);return request!;
    };
    const confirm=async(label="Confirm new timeline")=>{consent();await frames();click(button(label,panel()!),"actual-confirm");await until(()=>!f.get().busy&&["complete","uncertain"].includes(f.get().status),"actual-fork-terminal");await idle();};
    const lookup=async()=>{click(button("Check saved child only",panel()!),"actual-lookup-only-control");await until(()=>!f.get().busy&&["complete","not_found","uncertain"].includes(f.get().status),"actual-lookup-completed");await idle();};
    const play=async()=>{if(c.get().view!=="play"){click(button("Play"),"actual-Play");await idle();}};
    const lab=async(heldMetadata=false)=>{if(c.get().view!=="lab"){click(button("Story Lab · spoilers"),"actual-Story-Lab-request");await frames();click(button("I understand; reveal spoilers"),"actual-spoiler-acknowledgement");if(heldMetadata){await until(()=>c.get().view==="lab"&&!v2.get().readBusy&&!v2.get().queryBusy,"actual-Lab-context-before-held-delivery");await frames();}else await idle();}};
    const existingSession=async(scope:Scope,head:number,domain:1|2)=>{
        const session=c.get().sessions.find(s=>structural(s.scope)===structural(scope));check(session,"exact-existing-session-required");
        const candidates=[...document.querySelectorAll<HTMLButtonElement>(".session-list button")].filter(node=>node.querySelector("small")?.textContent?.trim()===`${scope.branch} · revision ${head}`);check(candidates.length===1,"one-exact-existing-session-control");
        if(c.selected()?.id!==session!.id)click(candidates[0],"actual-session-switch");await idle();owner(scope,head,domain);await ready();
    };
    const open=async(role:string,head:number,domain:1|2)=>{
        const result=f.get().result,request=roles[role];check(result&&result.scope.branch===request.child_branch&&result.fork_revision===request.at_revision&&result.head_revision===head,`${role}-exact-confirmed-outcome`);outcomes[role]=structuredClone(result);
        click(button("Open confirmed child",panel()!),`${role}-explicit-open`);await until(()=>c.selected()?.scope.branch===request.child_branch&&!c.get().starting,`${role}-selected-child-opened`);await idle();owner({story:AUTHOR.story,branch:request.child_branch},head,domain);await ready();
    };
    const geometry=(node:HTMLElement)=>{
        const r=node.getBoundingClientRect(),positive=node.isConnected&&r.width>0&&r.height>0&&[r.left,r.right,r.top,r.bottom].every(Number.isFinite),visible=positive&&r.left>=-2&&r.top>=-2&&r.right<=innerWidth+2&&r.bottom<=innerHeight+2;
        const hits=[.05,.5,.95].map(point=>{if(!visible)return false;const found=document.elementFromPoint(r.left+r.width/2,r.top+Math.max(1,Math.min(r.height-1,r.height*point)));return !!found&&(found===node||node.contains(found));});
        return{tag:node.tagName,text:node.textContent?.slice(0,160),connected:node.isConnected,positive,visible,hits,rect:{x:r.x,y:r.y,width:r.width,height:r.height,right:r.right,bottom:r.bottom}};
    };
    const targets=()=>{
        const region=panel();check(region,"mounted-actual-ForkPanel");const values:{name:string;node:HTMLElement}[]=[];
        const add=(name:string,node:HTMLElement|null)=>{if(node)values.push({name,node});};
        add("heading",region!.querySelector("h2"));add("close",button("Close timeline creation",region!));
        const ps=region!.querySelectorAll<HTMLElement>(":scope > p");add("description",ps[0]??null);add("selected-context",ps[1]??null);add("receipt",region!.querySelector(".fork-receipt"));
        add("refresh",button("Refresh completed boundaries",region!));add("boundary-status",region!.querySelector('[role="status"]'));add("boundary-selector",region!.querySelector("select"));
        add("prepare",button("Prepare new timeline",region!));
        add("request-heading",region!.querySelector("h3"));[...region!.querySelectorAll<HTMLElement>("dl dd")].forEach((node,i)=>add(`request-field-${i}`,node));
        add("recovery-copy",region!.querySelector("p.muted:not(.fork-receipt)"));add("consent",region!.querySelector(".fork-consent"));
        for(const label of["Confirm new timeline","Retry exact original fork","Check saved child only","Cancel pending fork","Open confirmed child"]){const found=[...region!.querySelectorAll<HTMLButtonElement>("button")].find(node=>text(node)===label);add(label,found??null);}
        add("operation",region!.querySelector(".fork-operation"));add("visible-error",region!.querySelector('[role="alert"]'));add("notice",[...region!.querySelectorAll<HTMLElement>('[role="status"]')].at(-1)??null);add("result-heading",region!.querySelector(".fork-result h3"));add("result-detail",region!.querySelector(".fork-result p"));
        const unique=values.filter((v,i)=>values.findIndex(other=>other.node===v.node)===i);check(unique.length>=8&&unique.length<=24,"fixed-bounded-phase-target-roster");return unique;
    };
    const capture=async(label:string,failure=false)=>{
        if(!failure)check(LABELS[captures.length]===label,"seven-ordered-native-capture-roster");
        const region=panel(),nodes=!failure?targets():[],samples:Record<string,unknown>[]=[];
        for(const target of nodes){const context=structural(timelineContext(c));target.node.scrollIntoView({block:"center",inline:"nearest",behavior:"instant"});await frames();const measured=geometry(target.node);check(region===panel()&&structural(timelineContext(c))===context&&region!.contains(target.node),`${label}-${target.name}-same-owner-after-scroll`);check(measured.positive&&measured.visible&&measured.hits.every(Boolean),`${label}-${target.name}-reachable-fit-unoccluded`);check(document.documentElement.scrollWidth<=innerWidth+2&&region!.scrollWidth<=region!.clientWidth+2,`${label}-${target.name}-no-horizontal-overflow`);samples.push({target:target.name,geometry:measured,scroll:{x:scrollX,y:scrollY,width:innerWidth,height:innerHeight},context:timelineContext(c)});}
        const frame=nodes.find(target=>target.name===(label==="d08-fork-pending"?"operation":"boundary-selector"))??nodes.find(target=>target.name==="selected-context");frame?.node.scrollIntoView({block:"center",inline:"nearest",behavior:"instant"});await frames();if(!failure)check(frame&&geometry(frame.node).visible&&geometry(frame.node).hits.every(Boolean),`${label}-actual-selected-control-final-framing`);
        const snapshot={...semantic(),geometry:nodes.map(target=>({target:target.name,...geometry(target.node)})),scrollObservations:samples,finalFraming:{target:frame?.name??null,simultaneousVisibilityClaim:false,strategy:"normal-per-target-scroll-then-selected-control"},fontMeasurements:fonts.slice(-1),checks:checks.slice(-64)};
        check(new TextEncoder().encode(JSON.stringify(snapshot)).length<=262144&&new TextEncoder().encode(JSON.stringify(snapshot,null,2)).length<=262144,"dual-bounded-semantic-checkpoint");
        const receipt=object(await invoke("harness_checkpoint",{label,snapshot}));check(receipt.rendering==="native-webview2","actual-native-app-owned-CapturePreview");receipts.push({label,rendering:receipt.rendering});captures.push(label);if(!failure)refs.push({label,json:`${label}.json`,count:samples.length});
    };
    const stateReport=(passed:boolean,error?:string)=>({synthetic:true,mode:MODE,passed,assertions,distinctChecks:checks.length,checks,captures,nativeCaptures:captures.length,rendering:captures.length?"native-webview2":"unavailable",desktopInput:false,realModelGeneration:false,baseline,finalOracle,proofs,observations,fontMeasurements:fonts,calls:trace.rows,roles,outcomes,captureReceipts:receipts,
        scrollObservations:{retainedInCheckpoints:true,total:refs.reduce((total,row)=>total+row.count,0),checkpoints:refs},errors:errors.snapshot(),failure:error?{phase,error}:null,
        unavailable:["Source author UNRUN; Root must inspect every original native image","Metadata delivery holds/errors are post-real-IPC doubles, not native transport failure","Retained detached DOM clicks do not prove execution of old React handlers; independent source tests cover those callbacks","Lookup restore is same-process, not restart or process-death qualification","No model/device/SDK/network/OS/physical keyboard/screen-reader/release qualification","Closed select PNG shows its chosen option; complete options are observed from actual DOM"]});
    const assertTrace=()=>{check(trace.rows.length<=256&&trace.hostReads<=64&&trace.forkCalls<=128,"bounded-product-dispatch-trace");check(trace.rows.every((row,i)=>row.sequence===i+1&&row.nativeSettled&&row.settled&&(row.replySha256===null||HEX.test(row.replySha256))),"ordered-settled-native-metadata-and-digests");check(trace.rows.every(row=>row.error===null||["Rule","Stale","ArchiveBusy","ForkConsentRequired","Cancelled","Transport"].includes(row.error)),"only-explicit-native-refusals-or-faults");check(c.get().playMode==="fixture"&&!c.get().freeTextProvider&&!c.get().pending&&!v2.get().pending&&!v2.get().uncertain,"no-generation-or-gameplay-operation");};
    const originalScopeRows=(value:Oracle)=>value.scopes.slice(0,4);
    try {
        check(window.__LOCALLORE_TEST__?.backend==="native"&&window.__LOCALLORE_TEST__?.domain2Fork===true,"explicit-native-Domain2-fork-mode");
        await invoke("harness_viewport",{preset:"wide"});await c.library();await c.resume(AUTHOR);await idle();owner(AUTHOR,3,2);await ready();
        check(structural(f.get().boundaryCatalog!.boundaries)==="[0,2,3]","full-mixed-and-private-author-boundaries-no-partial-one");
        baseline=await oracle("before-navigation");check(baseline.scopes.length===4&&baseline.children.length===0,"initial-only-four-fixed-scopes");
        await capture("d08-fork-catalog");

        const errored=trace.armBoundaryDelivery("error");click(button("Refresh completed boundaries",panel()!),"actual-boundary-refresh-error");await until(()=>errored.entered&&!!f.get().boundaryError,"local-delivery-error-after-native-success");
        check(errored.nativeSettled&&errored.row?.error===null&&errored.row.delivery==="local-Transport"&&f.get().boundaryError==="Transport","native-success-distinct-from-local-delivery-error");observe("boundary-error","post-real-read delivery double");
        click(button("Refresh completed boundaries",panel()!),"explicit-boundary-retry");await ready();
        const delayed=trace.armBoundaryDelivery("hold");click(button("Refresh completed boundaries",panel()!),"actual-boundary-refresh-held");await until(()=>delayed.nativeSettled&&f.get().boundaryBusy,"real-boundary-read-held-after-success");check(f.get().boundaryCatalog===null,"pending-metadata-clears-old-body");observe("boundary-pending","post-real-read delivery hold");
        await lab(true);trace.releaseDelivery();await idle();check(f.get().boundaryCatalog===null&&!f.get().boundaryBusy,"retired-context-cannot-publish-held-metadata");observe("retired-metadata","actual context switch with delayed real native reply");await ready();

        for(const [name,at,head,expected]of[["partial",1,3,"Rule"],["stale",2,2,"Stale"]] as const){const result=await rawTerminal({session:c.selected()!.id,input:{parent:AUTHOR,child_branch:`d08-raw-${name}`,at_revision:at,expected_parent_revision:head},consent:true});check(result.error===expected,`actual-raw-native-${name}-${expected}`);observations.push({label:`native-${name}`,source:"fixed raw Tauri probe, not a UI option",phase:result.phase,error:result.error,operationId:result.operation_id});}
        let refusal="";try{await raw("fork_start",{session:c.selected()!.id,input:{parent:AUTHOR,child_branch:"d08-raw-no-consent",at_revision:2,expected_parent_revision:3},consent:false});}catch(error){refusal=forkError(error);}check(refusal==="ForkConsentRequired","actual-native-no-consent-refuses-before-work");
        await prepare(3,"consent-preview");const noConsentStarts=trace.rows.filter(row=>row.command==="fork_start").length;await f.confirm(false);check(f.get().error==="ForkConsentRequired"&&trace.rows.filter(row=>row.command==="fork_start").length===noConsentStarts,"actual-controller-no-consent-visible-refusal-no-dispatch");
        observe("controller-no-consent","actual controller action probe, not disabled-button click");check((await oracle("after-refusals")).children.length===0,"all-refused-probe-children-absent");await capture("d08-fork-rejected");

        await prepare(2,"cancelled");await fixture("hold");consent();await frames();click(button("Confirm new timeline",panel()!),"confirm-held-native-fork");await until(()=>f.get().busy&&f.get().operation!==null,"actual-broker-pending-operation");await capture("d08-fork-pending");
        let busy="";try{await raw("fork_start",{session:c.selected()!.id,input:{...roles.cancelled,child_branch:"d08-raw-busy"},consent:true});}catch(error){busy=forkError(error);}check(busy==="ArchiveBusy","concurrent-raw-probe-reaches-native-broker-and-refuses");
        await frames();const cancelledOperation=f.get().operation!;click(button("Cancel pending fork",panel()!),"actual-pending-Cancel");await cancelledAtNative(cancelledOperation);await fixture("release");await until(()=>!f.get().busy,"cancel-terminal");check(f.get().error==="Cancelled","actual-native-Cancelled-not-assumed-rollback");observe("cancelled","native broker hold/cancel");await lookup();check(f.get().status==="not_found","cancelled-UUID-actually-absent");
        await prepare(2,"retired");await fixture("hold");consent();await frames();click(button("Confirm new timeline",panel()!),"confirm-context-retirement-request");await until(()=>f.get().busy&&f.get().operation!==null,"held-retirement-operation");const retiredOperation=f.get().operation!;
        choose(select("Inspection lens"),"player");await until(()=>c.get().observer==="player"&&!f.get().busy,"actual-lens-context-retires-pending-fork");await cancelledAtNative(retiredOperation);await fixture("release");let retired=object(await invoke("archive_status",{operationId:retiredOperation}));for(let n=0;n<120&&retired.running===true;n++){await new Promise(resolve=>setTimeout(resolve,10));retired=object(await invoke("archive_status",{operationId:retiredOperation}));}check(retired.running===false&&retired.error==="Cancelled"&&f.get().result===null,"context-retirement-cancels-native-and-retires-publication");observe("retired-fork","actual context cancellation and Main status observation");await ready();await lookup();check(f.get().status==="not_found","retired-UUID-absent-after-real-lookup");await play();await ready();

        await prepare(2,"preauthor");await confirm();check(f.get().result?.created===true,"preauthor-created-once");owner(AUTHOR,3,2);await open("preauthor",2,1);check(c.receipt()?.request.scope.branch==="main"&&c.receipt()?.request.turn==="d08-domain2-fork-prefix","actual-child-inherited-receipt-retains-original-scope");await capture("d08-fork-preauthor");await existingSession(AUTHOR,3,2);
        await prepare(3,"after-author");await confirm();check(f.get().result?.created===true,"after-author-created-once");await open("after-author",3,2);check(structural(f.get().boundaryCatalog!.boundaries)==="[0,2,3]","authored-child-full-catalog-includes-private-interval");
        await lab();for(const lens of["player","mira","sable","omniscient"]){choose(select("Inspection lens"),lens);await idle();await until(()=>{const q=v2.get().history?.query.observer;return lens==="player"?q?.kind==="player":lens==="omniscient"?q?.kind==="omniscient":q?.kind==="character"&&q.id===lens;},`actual-${lens}-history-lens`);const value=JSON.stringify(v2.get().history!.page);check(!value.includes("D08_OTHER_STORY_TRUTH_424"),`${lens}-other-story-isolated`);if(lens!=="omniscient")check(!value.includes("D08_PRIVATE_AUTHOR_TRUTH_422")&&!value.includes("D08_PRIVATE_AUTHOR_REASON_423"),`${lens}-unobserved-author-truth-not-character-knowledge`);if(lens==="mira")check(value.includes("D08_PREFIX_MIRA_ONLY_421"),"Mira-inherited-witness-statement");if(lens==="sable")check(!value.includes("D08_PREFIX_MIRA_ONLY_421"),"Sable-unwitnessed-statement-excluded");await ready();}
        await oracle("after-observer-inspection");await capture("d08-fork-authored");await play();await existingSession(AUTHOR,3,2);

        await prepare(0,"recovered");await fixture("lose-ack");await confirm();check(f.get().status==="uncertain"&&f.get().error==="Transport"&&f.get().result===null,"native-commit-withheld-ack-honest-uncertain");observe("lost-ack","native committed fault, no automatic retry");const original=roles.recovered;
        const retained=document.querySelector<HTMLElement>('[aria-label="Unresolved saved operation"]');check(retained,"actual-Main-unresolved-broker-notice");const ack=retained!.querySelector<HTMLInputElement>('input[type="checkbox"]');check(ack&&!ack.disabled,"actual-unresolved-ack-checkbox");ack!.click();await frames();click(button("Acknowledge unresolved outcome",retained!),"explicit-unresolved-acknowledgement");await frames();
        await confirm("Retry exact original fork");check(structural(f.get().request)===structural(original)&&f.get().result?.created===false,"exact-rendered-retry-same-identity-created-false");await open("recovered",0,1);check(c.get().play?.receipts.length===0,"root-zero-has-no-invented-receipt");await capture("d08-fork-recovered");await existingSession(AUTHOR,3,2);
        const beforeRestoreStarts=trace.rows.filter(row=>row.command==="fork_start").length;f.restore(original);await frames();await lookup();check(f.get().result?.created===false&&f.get().result?.scope.branch===original.child_branch,"same-process-restored-recovery-lookup-only");
        f.restore({...original,child_branch:"d08-recovery-missing"});await frames();await lookup();check(f.get().status==="not_found"&&trace.rows.filter(row=>row.command==="fork_start").length===beforeRestoreStarts,"missing-restored-recovery-never-creates");observe("lookup-recovery","same-process controller restore, not restart");
        await existingSession({story:AUTHOR.story,branch:roles["after-author"].child_branch},3,2);await prepare(3,"preview");
        const fontNodes=targets().filter(target=>["heading","description","selected-context","receipt","boundary-status","boundary-selector","prepare","request-heading","request-field-0","request-field-1","request-field-2","consent","Confirm new timeline","Check saved child only","operation","notice"].includes(target.name));
        const baselineFonts=fontNodes.map(target=>({...target,px:Number.parseFloat(getComputedStyle(target.node).fontSize),text:target.node.textContent}));
        check(c.get().textScale===100&&baselineFonts.length>=12,"actual-same-target-font-baseline");
        const measure=(label:string,ratio:number)=>{const result=baselineFonts.map(target=>{const px=Number.parseFloat(getComputedStyle(target.node).fontSize);check(target.node.isConnected&&target.node.textContent===target.text&&Number.isFinite(px)&&Math.abs(px-target.px*ratio)<=.05,`${label}-${target.name}-actual-font-ratio`);return{target:target.name,baselinePx:target.px,actualPx:px,ratio:px/target.px};});fonts.push({label,width:innerWidth,height:innerHeight,expectedRatio:ratio,pixelTolerance:.05,targets:result});};
        measure("100-baseline",1);const sizing=select("Text size"),details=sizing.closest("details");if(details&&!details.open){const summary=details.querySelector("summary");check(summary,"actual-layout-summary");summary!.click();await frames();}choose(sizing,"150");await until(()=>c.get().textScale===150,"actual-150-text-setting");await invoke("harness_viewport",{preset:"capture-narrow"});await frames();check(innerWidth===620&&innerHeight===900,"actual-fixed-narrow-native-viewport");measure("150-narrow",1.5);
        const focus=select("Fork completed boundary");focus.focus();check(document.activeElement===focus,"application-DOM-focus-only-no-keyboard-claim");await capture("d08-fork-enlarged");choose(select("Text size"),"100");await invoke("harness_viewport",{preset:"wide"});await frames();check(c.get().textScale===100&&innerWidth===1280,"normal-wide-text-restored");measure("100-restored",1);
        const completed=await oracle("after-all-mutations");check(completed.scopes.length===7&&completed.children.length===3,"only-three-successful-primary-UUID-additions");
        const intended=[roles.preauthor,roles["after-author"],roles.recovered];check(completed.children.every(child=>intended.some(request=>request.child_branch===child.scope.branch&&request.at_revision===child.fork_revision)),"children-exact-observed-role-identities-and-Core-points");
        for(const name of["consent-preview","cancelled","retired","preview"])check(!completed.scopes.some(row=>row.scope.branch===roles[name].child_branch),`${name}-observed-UUID-absent`);
        assertTrace();check(errors.snapshot().length===0,"zero-unexpected-bounded-frontend-native-errors");
        trace.releaseDelivery();await fixture("release");await dispose();disposed=true;await until(()=>trace.rows.every(row=>row.settled),"post-dispose-native-dispatches-settled");
        finalOracle=await oracle("after-dispose");check(structural(finalOracle)===structural(completed)&&structural(originalScopeRows(finalOracle))===structural(originalScopeRows(baseline)),"post-dispose-original-and-child-fingerprints-unchanged");
        const stats=object(await invoke("harness_stats"));check(stats.sessions===0&&stats.workers===0,"actual-owned-sessions-and-workers-zero");assertTrace();check(errors.snapshot().length===0,"dispose-adds-no-unexpected-errors");
        await finish(stateReport(true));
    } catch(error) {
        const failedPhase=phase;
        trace.releaseDelivery();try{await fixture("release");}catch{ /* Preserve the primary failure; fixed finalizer can still fail. */ }
        if(!disposed){try{await capture("d08-fork-failure",true);}catch{ /* A failed capture is not native evidence. */ }}
        if(!disposed){try{await dispose();disposed=true;}catch{ /* Failed cleanup remains unavailable, never a success proof. */ }}
        const report=stateReport(false,category(error));report.failure={phase:failedPhase,error:category(error)};
        await finish(report);
    }
}

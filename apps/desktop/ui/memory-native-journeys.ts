// Fixed synthetic development journey. Actual app controllers and native IPC.
// This source must be absent from the normal bundle; no desktop input/capture.
import type {Controller} from "./controller";
import type {MemoryMaintenanceController,MemoryAction} from "./memory-maintenance-controller";
import type {BrokerRetention} from "./broker-retention";
import {structural,type ErrorBuffer} from "./model";
type Invoke=(command:string,args?:Record<string,unknown>)=>Promise<unknown>;
export async function memoryNativeJourneys({controller:c,maintenance:m,brokerRetention:retention,errors,invoke,dispose,config}:{controller:Controller;maintenance:MemoryMaintenanceController;brokerRetention:BrokerRetention;errors:ErrorBuffer;invoke:Invoke;dispose:()=>Promise<void>;config:{stage:string}}) {
    const checks:string[]=[];let current="memory-start";
    const check=(value:unknown,label:string)=>{current=label;if(!value)throw Error(label);checks.push(label);};
    const pause=()=>new Promise(r=>setTimeout(r,25));
    const until=async(test:()=>boolean)=>{for(let i=0;i<800;i++){if(test())return;await pause();}throw Error("MemoryNativeDeadline");};
    const fixture=(action:string)=>invoke("harness_memory_case",{action});
    const observe=async()=>{for(let i=0;i<800&&m.get().operation?.running;i++){await pause();await m.act("status");}check(!m.get().operation?.running,"bounded-explicit-status-observation");};
    const action=async(a:MemoryAction)=>{check(m.can(a),`${current}-${a}-available`);await m.act(a);await observe();};
    const capture=async(label:string)=>{
        await new Promise(r=>setTimeout(r,100));
        const root=document.getElementById("root")!,panel=root.querySelector(".memory-maintenance-panel")!;
        check(!!panel,`${label}-panel-visible`);
        const context=m.get().context!;
        check(panel.textContent?.includes(context.scope.story)&&panel.textContent?.includes(context.scope.branch)&&panel.textContent?.includes(context.observer)&&panel.textContent?.includes(String(context.expected_head)),`${label}-selected-scope-observer-head-visible`);
        const receipt=c.receipt();
        check(!receipt||panel.querySelector(".memory-receipt")?.textContent?.includes(receipt.request.turn),`${label}-displayed-receipt-visible`);
        if(m.get().error)check(panel.querySelector('[role="alert"]')?.textContent?.includes(m.get().error!),`${label}-error-visible`);
        panel.scrollIntoView({block:"start"});await pause();
        check(document.documentElement.scrollWidth<=innerWidth+2,`${label}-no-horizontal-overflow`);
        const location=c.get().workspace?.location??"<none>";
        const result=await invoke("harness_checkpoint",{label,snapshot:{...c.semantic(),workspace:{...c.get().workspace,location:"<synthetic-workspace>"},maintenance:m.get(),broker:retention.get(),checks:[...checks],dom:{userAgent:navigator.userAgent,text:root.textContent?.slice(0,48000).replaceAll(location,"<synthetic-workspace>"),panel:panel.textContent,viewport:{width:innerWidth,height:innerHeight},structure:[...panel.querySelectorAll("button,input,[role],dt,dd")].map(el=>({tag:el.tagName,role:el.getAttribute("role"),label:el.getAttribute("aria-label")??el.textContent?.slice(0,160),disabled:el.hasAttribute("disabled"),checked:el instanceof HTMLInputElement?el.checked:null}))}}}) as {rendering:string};
        check(result.rendering==="native-webview2",`${label}-actual-native-webview2-render`);
    };
    try {
        await c.start();await c.resume({story:"memory-controls-synthetic",branch:"main"});
        check(c.get().workspace?.persistent&&c.get().play?.revision===1,"memory-native-durable-selected-fixture");
        const before=structural(c.get().play),receiptBefore=structural(c.get().play?.receipts);
        if(config.stage==="initial") {
            await action("status");check(m.get().reply?.maintenance.job===null,"passive-status-never-admits");await capture("memory-native-passive");
            check(!m.can("admit"),"admission-requires-new-consent");m.consent(true);await action("admit");check(m.get().reply?.maintenance.job?.status==="ready","explicit-admit-ready");await capture("memory-native-admitted");
            await fixture("hold");await m.act("step");check(m.get().operation?.running,"actual-shared-worker-pending");
            let blocked=false;try{await invoke("archive_export_preview",{scope:c.selected()!.scope});}catch(e){blocked=String(e).includes("ArchiveBusy");}
            check(blocked,"memory-pending-retains-result-against-archive-start");await capture("memory-native-pending");
            await m.stop();await fixture("release");await observe();check(m.get().error==="Cancelled","stopped-operation-reports-cancelled-without-rollback-claim");
            await action("status");check(m.get().reply?.maintenance.job?.status==="ready","stopped-worker-did-not-pretend-job-terminal");
            await action("cancel");check(m.get().reply?.maintenance.job?.status==="cancelled","explicit-persisted-cancel");await capture("memory-native-cancelled");
            m.consent(true);await action("prune");check(m.get().reply?.maintenance.job===null,"explicit-terminal-prune");await capture("memory-native-pruned");
            await fixture("lose-ack");m.consent(true);await m.act("admit");check(m.get().uncertain&&retention.get()?.unknown,"lost-start-ack-retains-original-identity");check(!m.can("step"),"unknown-ack-never-repeats-mutation");await capture("memory-native-unknown");
            c.setView("lab");c.setObserver("sable");await until(()=>c.get().inspectionObserver==="sable");
            check(!m.can("status")&&!m.can("step")&&m.get().reply===null,"observer-switch-clears-old-job-and-disables-maintenance");check(retention.get()?.unknown&&retention.get()?.identity.story==="memory-controls-synthetic","observer-switch-preserves-original-unknown-barrier");await capture("memory-native-observer");
            c.setView("play");await action("status");check(m.get().reply?.maintenance.job?.status==="ready"&&!retention.get()?.unknown,"exact-original-passive-recovery-finds-saved-admission");
            await fixture("hold");await m.act("step");const oldId=m.get().operation!.operation_id;
            c.setView("lab");c.setObserver("sable");await fixture("release");await until(()=>!m.get().busy);check(m.get().reply===null&&m.get().operation===null,"late-old-context-operation-never-installs-result");
            // Observe ONLY the previously known ID; no current-operation endpoint.
            for(let i=0;i<800;i++){const status=await invoke("archive_status",{operationId:oldId}) as {running:boolean};if(!status.running)break;await pause();}
            await capture("memory-native-switched");c.setView("play");await action("status");
            await action("step");check(m.get().reply?.maintenance.job?.status==="complete"&&m.get().reply?.maintenance.job?.next_from===1,"one-explicit-chunk-completes-fixed-history");await capture("memory-native-complete");
            await invoke("harness_viewport",{preset:"capture-narrow"});await capture("memory-native-narrow");
            check(structural(c.get().play)===before&&structural(c.get().play?.receipts)===receiptBefore,"maintenance-never-mutates-canon-player-context-or-receipts");
            // Leave a durable terminal job for process-restart passive observation.
        } else {
            check(m.get().reply===null&&m.get().operation===null,"process-restart-never-auto-restarts-memory");await action("status");check(m.get().reply?.maintenance.job?.status==="complete","restart-passive-status-reads-durable-completion");await capture("memory-native-restarted");
            await new Promise(r=>setTimeout(r,100));await action("status");check(m.get().reply?.maintenance.job?.next_from===1,"repeated-passive-status-does-not-step-or-restart");await capture("memory-native-reopened");
        }
        check(errors.snapshot().length===0,"no-unexpected-frontend-or-gameplay-errors");await dispose();
        const stats=await invoke("harness_stats") as {sessions:number;workers:number};check(stats.sessions===0&&stats.workers===0,"all-owned-host-sessions-and-workers-drained");
        await invoke("harness_finish",{report:{synthetic:true,passed:true,checks,errors:errors.snapshot(),stage:config.stage,realModelGeneration:false}});
    }catch(error){await invoke("harness_finish",{report:{synthetic:true,passed:false,checks,failedCheck:current,error:error instanceof Error?error.message:String(error).slice(0,100),maintenance:m.get(),broker:retention.get(),errors:errors.snapshot()}});}
}

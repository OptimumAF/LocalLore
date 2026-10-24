// Actual app controllers/gate; all native replies are fixed mocks, never native evidence.
import { BrokerRetention } from "./broker-retention";
import { ArchiveController } from "./archive-controller";
import { ForkController } from "./fork-controller";
import type { TimelineContext } from "./timeline-model";

export async function brokerSurfaceReviewJourneys() {
    const results: {name:string;passed:boolean;error:string|null}[] = [];
    const check = (value:unknown,label:string) => {if(!value)throw Error(label);};
    async function test(name:string,work:()=>Promise<void>) {
        try {await work();results.push({name,passed:true,error:null});}
        catch(error){results.push({name,passed:false,error:String(error)});}
    }
    const context:TimelineContext = {session:"session-1",scope:{story:"memory-surface-review",branch:"main"},revision:1,view:"lab",observer:"omniscient",persistent:true};
    const memoryIdentity={surface:"memory" as const,session:context.session,story:context.scope.story,branch:context.scope.branch,head:1,action:"status"};
    const forkIdentity={surface:"fork" as const,session:context.session,story:context.scope.story,branch:context.scope.branch,head:1,child:"surface-child",at:0,action:"fork"};
    const archiveIdentity={surface:"archive" as const,session:context.session,story:context.scope.story,branch:context.scope.branch,head:1,action:"archive_import_preview"};
    const status=(operation:number,result:unknown)=>({version:1,operation_id:operation,running:false,phase:"completed",error:null,result});
    const memoryResult=()=>({version:1,kind:"memory_maintenance",session:context.session,scope:{...context.scope},expected_head:1,action:"status",maintenance:{version:1,scope:{...context.scope},head:1,action:"status",job:null}});
    const forkResult=(branch="surface-child")=>({kind:"fork",outcome:{version:1,scope:{story:context.scope.story,branch},parent:{...context.scope},fork_revision:0,head_revision:0,created:true}});
    const preview=(kind:"export"|"import")=>({version:1,token:"12345678-1234-1234-1234-123456789abc",kind,warning:"Fixed synthetic full-private warning",preview:{version:1,story_id:context.scope.story,title:"Synthetic surface validation",root_branch:"main",branch_heads:{main:1},committed_turns:1,bytes:2048,payload_sha256:"a".repeat(64),privacy_warning:"Fixed synthetic privacy warning",noncommitted_workflow_transferred:false}});

    for(const [name,payload] of [
        ["archive-malformed-terminal-remains-unknown-after-context-reset",{}],
        ["archive-valid-preview-wrong-command-kind-remains-unknown-after-context-reset",preview("export")],
    ] as const) await test(name,async()=>{
        const gate:BrokerRetention=new BrokerRetention(()=>controller.get().busy||["Wire","Transport"].includes(controller.get().error??""));
        const controller:ArchiveController=new ArchiveController(
            (command)=>gate.start({...archiveIdentity,action:command},async()=>status(11,payload)),
            async()=>{},
        );
        controller.subscribe(gate.refreshConsumption);
        controller.contextChanged("session-1|lab|omniscient",true);
        await controller.previewImport();
        const actualWire=controller.get().error==="Wire";
        controller.contextChanged("other-session|lab|omniscient",true);
        const oldPresentationCleared=controller.get().error===null&&!controller.get().busy;
        const retainedUnknown=gate.get()?.unknown===true;
        let dispatched=false,blocked=false;
        try {await gate.start(memoryIdentity,async()=>{dispatched=true;return status(12,memoryResult());});}
        catch(error){blocked=error instanceof Error&&error.message==="ArchiveBusy";}
        check(actualWire,"actual archive decoder/command binding rejects terminal reply with Wire");
        check(oldPresentationCleared,"archive context reset clears only old presentation");
        check(retainedUnknown,"malformed archive semantic outcome retains global uncertainty across reset");
        check(blocked&&!dispatched,"malformed archive completion cannot authorize another surface start");
    });

    for(const [name,payload] of [
        ["fork-malformed-terminal-retains-global-unknown-across-context-change",{}],
        ["fork-valid-envelope-wrong-child-retains-global-unknown-across-context-change",forkResult("foreign-child")],
    ] as const) await test(name,async()=>{
        const gate:BrokerRetention=new BrokerRetention(()=>controller.get().busy||controller.get().status==="uncertain");
        const controller:ForkController=new ForkController(
            ()=>gate.start(forkIdentity,async()=>status(21,payload)),
            async()=>{},()=>{},
        );
        controller.subscribe(gate.refreshConsumption);
        controller.contextChanged(context);controller.prepare(0,"surface-child");
        await controller.confirm(true);
        const actualWire=controller.get().error==="Wire"&&controller.get().status==="uncertain";
        controller.contextChanged({...context,session:"session-2",scope:{story:"other-story",branch:"main"}});
        const correctLocalUncertainty=controller.get().status==="uncertain"&&controller.get().error===null;
        const retainedUnknown=gate.get()?.unknown===true;
        let dispatched=false,blocked=false;
        try {await gate.start(memoryIdentity,async()=>{dispatched=true;return status(22,memoryResult());});}
        catch(error){blocked=error instanceof Error&&error.message==="ArchiveBusy";}
        check(actualWire,"actual fork outcome validator rejects terminal reply with Wire");
        check(correctLocalUncertainty,"fork context change preserves its existing lookup-only uncertainty");
        check(retainedUnknown,"malformed fork semantic outcome exposes global retained uncertainty");
        check(blocked&&!dispatched,"malformed fork outcome remains blocked across context change");
    });

    for(const surface of ["archive","fork"] as const) await test(`${surface}-retired-context-before-malformed-admission-keeps-global-unknown`,async()=>{
        let release!:(value:unknown)=>void;
        const held=new Promise<unknown>(resolve=>{release=resolve;});
        const gate:BrokerRetention=new BrokerRetention(()=>surface==="archive"
            ? archive.get().busy||["Wire","Transport"].includes(archive.get().error??"")
            : fork.get().busy||fork.get().status==="uncertain");
        const archive=new ArchiveController(()=>gate.start(archiveIdentity,()=>held),async()=>{});
        const fork=new ForkController(()=>gate.start(forkIdentity,()=>held),async()=>{},()=>{});
        archive.subscribe(gate.refreshConsumption);fork.subscribe(gate.refreshConsumption);
        archive.contextChanged("session-1|lab|omniscient",true);fork.contextChanged(context);
        if(surface==="fork")fork.prepare(0,"surface-child");
        const pending=surface==="archive"?archive.previewImport():fork.confirm(true);
        const inFlight=gate.get()?.inFlight===true;
        if(surface==="archive")archive.contextChanged("other-session|lab|omniscient",true);
        else fork.contextChanged({...context,session:"session-2",scope:{story:"other-story",branch:"main"}});
        release(status(25,{}));await pending;
        const owner=surface==="archive"?archive.get():fork.get();
        const unknown=gate.get()?.unknown===true;
        let dispatched=false,blocked=false;
        try{await gate.start(memoryIdentity,async()=>{dispatched=true;return status(26,memoryResult());});}
        catch(error){blocked=error instanceof Error&&error.message==="ArchiveBusy";}
        check(inFlight,"actual owner retires while its own native admission reply is still awaited");
        check(owner.error===null&&owner.result===null&&!owner.busy,"retired owner suppresses obsolete error and result presentation");
        check(unknown,"malformed own reply remains globally unknown even when retired owner suppresses Wire");
        check(blocked&&!dispatched,"retired malformed reply cannot authorize another surface start");
    });

    await test("valid-native-shaped-archive-cancellation-consumes-and-allows-explicit-next-start",async()=>{
        const gate:BrokerRetention=new BrokerRetention(()=>controller.get().busy||["Wire","Transport"].includes(controller.get().error??""));
        const controller:ArchiveController=new ArchiveController(
            ()=>gate.start(archiveIdentity,async()=>status(31,{version:1,status:"cancelled"})),
            async()=>{},
        );
        controller.subscribe(gate.refreshConsumption);controller.contextChanged("session-1|lab|omniscient",true);
        await controller.previewImport();
        check(controller.get().result?.status==="cancelled"&&controller.get().error===null,"actual archive controller accepts valid cancelled result");
        check(gate.get()?.terminal&&gate.get()?.consumed&&!gate.get()?.unknown,"valid cancelled result independently consumed");
        let dispatched=false;
        await gate.start(memoryIdentity,async()=>{dispatched=true;return status(32,memoryResult());});
        check(dispatched,"valid archive result permits subsequent explicitly requested start");
    });
    await test("valid-native-shaped-fork-outcome-consumes-and-allows-explicit-next-start",async()=>{
        const gate:BrokerRetention=new BrokerRetention(()=>controller.get().busy||controller.get().status==="uncertain");
        const controller:ForkController=new ForkController(
            ()=>gate.start(forkIdentity,async()=>status(41,forkResult())),
            async()=>{},()=>{},
        );
        controller.subscribe(gate.refreshConsumption);controller.contextChanged(context);controller.prepare(0,"surface-child");
        await controller.confirm(true);
        check(controller.get().status==="complete"&&controller.get().result?.scope.branch==="surface-child"&&controller.get().error===null,"actual fork controller accepts exact valid child outcome");
        check(gate.get()?.terminal&&gate.get()?.consumed&&!gate.get()?.unknown,"valid fork result independently consumed");
        let dispatched=false;
        await gate.start(memoryIdentity,async()=>{dispatched=true;return status(42,memoryResult());});
        check(dispatched,"valid fork result permits subsequent explicitly requested start");
    });
    return results;
}

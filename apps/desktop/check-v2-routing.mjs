// Actual frontend Controller with synthetic transport; no native IPC or rendering.
// Frozen before adding the native V2 routing branch.
import assert from "node:assert/strict";
import { build } from "esbuild";
import { fileURLToPath } from "node:url";
const compiled = await build({entryPoints:[fileURLToPath(new URL("./ui/controller.ts",import.meta.url))],bundle:true,platform:"node",format:"esm",write:false});
const {Controller} = await import(`data:text/javascript;base64,${Buffer.from(compiled.outputFiles[0].contents).toString("base64")}`);
const copy = value => structuredClone(value);
const scope = {story:"quay",branch:"corrected"};
const thin = (selected=scope,revision=3,domain=2) => ({version:2,domain_version:domain,scope:copy(selected),revision,rules:"fantasy_v1",player:{observer:"player",self_state:{name:"Rowan",location:"quay",alive:true,energy:2,abilities:{steady:1},attributes:{resolve:3},injuries:[],affiliations:[],goals:[]}},inventory:{}});
function deferred(){let resolve; const promise=new Promise(r=>resolve=r); return {promise,resolve};}
class Gateway {
    playSnapshotV2=true;
    domain=2;
    head=3;
    calls=[];
    pending=null;
    corrupt=false;
    async call(command){
        this.calls.push(copy(command));
        if(command.op==="workspace")return {persistent:true,location:"synthetic",schema_version:1,database_schema_version:5,stories:[{scope:copy(scope),title:"Synthetic corrected story",revision:this.head,drafts:0}]};
        if(command.op==="resume")return {session:`session-${command.scope.branch}`,scope:copy(command.scope),revision:this.head};
        if(command.op==="open")return {revision:this.head};
        if(command.op==="close")return {};
        if(command.op==="play_snapshot_v2"){
            const output=thin(command.scope,command.expected_revision,this.domain);
            if(this.corrupt)output.facts={private:"MUST_NOT_RENDER"};
            if(this.pending){const gate=this.pending; this.pending=null; gate.entered.resolve(); await gate.release.promise;}
            return output;
        }
        if(command.op==="play_snapshot"){
            assert.equal(this.domain,1,"Domain2 must never fall through to the legacy context view");
            return {rules:"fantasy_v1",scope:copy(command.scope),revision:command.expected_revision,player:{revision:command.expected_revision,scope:copy(command.scope),observer:"player",self_state:{name:"Rowan"},facts:{},observations:[],beliefs:[]},inventory:{},receipts:[]};
        }
        throw Error(`Unexpected test operation ${command.op}`);
    }
    hold(){const gate={entered:deferred(),release:deferred()}; this.pending=gate; return gate;}
}
let checks=0;
{
    const gateway=new Gateway(),controller=new Controller(gateway);
    await controller.start();
    assert.equal(controller.get().visibleError,null);
    assert.deepEqual(controller.get().playV2,thin());
    assert.equal(controller.get().play,null);
    assert.equal(gateway.calls.filter(c=>c.op==="play_snapshot").length,0);
    checks++;
    const gate=gateway.hold(),older=controller.refresh();
    await gate.entered.promise;
    gateway.head=4;
    await controller.refresh();
    gate.release.resolve();
    await older;
    assert.equal(controller.get().playV2.revision,4);
    checks++;
    const switched=gateway.hold(),oldSelection=controller.refresh();
    await switched.entered.promise;
    const other={story:"quay",branch:"other"};
    await controller.resume(other);
    switched.release.resolve();
    await oldSelection;
    assert.deepEqual(controller.get().playV2.scope,other);
    assert.equal(controller.selected().id,"session-other");
    checks++;
    await controller.closeSelected();
    assert(!controller.get().playV2 || controller.get().playV2.scope.branch!=="other");
    checks++;
}
{
    const gateway=new Gateway(); gateway.corrupt=true;
    const controller=new Controller(gateway);
    await controller.start();
    assert.equal(controller.get().visibleError,"Wire");
    assert.equal(controller.get().playV2,null);
    assert.equal(gateway.calls.filter(c=>c.op==="play_snapshot").length,0);
    checks++;
}
{
    const gateway=new Gateway(); gateway.domain=1;
    const controller=new Controller(gateway);
    await controller.start();
    assert.equal(controller.get().visibleError,null);
    assert.equal(controller.get().playV2,null);
    assert.equal(controller.get().play.revision,3);
    assert.equal(gateway.calls.filter(c=>c.op==="play_snapshot").length,1);
    checks++;
}
{
    const gateway=new Gateway(); gateway.domain=1; delete gateway.playSnapshotV2;
    const controller=new Controller(gateway);
    await controller.start();
    assert.equal(controller.get().play.revision,3);
    assert.equal(gateway.calls.filter(c=>c.op==="play_snapshot_v2").length,0);
    checks++;
}
console.log(JSON.stringify({suite:"actual-controller-v2-routing",checks,native:false,render:false}));

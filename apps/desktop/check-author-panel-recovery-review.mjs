// Frozen before Panel changes. Actual AuthorController + inert React server render.
// MOCK native results; no native IPC, Store, model, WebView, device or desktop.
import assert from "node:assert/strict";
import { build } from "esbuild";
import { mkdir, writeFile } from "node:fs/promises";
import { fileURLToPath, pathToFileURL } from "node:url";
import { randomUUID, createHash } from "node:crypto";
import path from "node:path";
const root=fileURLToPath(new URL(".",import.meta.url));
const directory=process.env.LOCALLORE_CHECK_OUTPUT_DIR??path.join(root,"artifacts/checks");
await mkdir(directory,{recursive:true});
const target=path.join(directory,`author-panel-recovery-${randomUUID()}.cjs`);
const compiled=await build({stdin:{contents:'export {AuthorController} from "./ui/author-controller";export {AuthorPanel} from "./ui/AuthorPanel";export {createElement} from "react";export {renderToStaticMarkup} from "react-dom/server";',resolveDir:root,loader:"tsx"},bundle:true,platform:"node",format:"cjs",jsx:"automatic",write:false});
await writeFile(target,compiled.outputFiles[0].contents,{flag:"wx"});
const {AuthorController,AuthorPanel,createElement,renderToStaticMarkup}=(await import(pathToFileURL(target).href)).default;
const clone=value=>structuredClone(value);
const context=()=>({rootIncarnation:"root-1",selectionEpoch:1,session:"session-1",scope:{story:"quay",branch:"main"},head:3,player:"player",observer:"omniscient",view:"lab",persistent:true,spoilerGranted:true,pending:false,brokerUncertain:false});
const draft=()=>({fork_revision:1,child_branch:"captured-child",fact:"relic-location",expected_proposition:"PANEL_PRIVATE_OLD_A",replacement:"PANEL_PRIVATE_NEW_B",reason:"PANEL_PRIVATE_REASON"});
const outcome=input=>({version:1,scope:{story:input.parent.story,branch:input.child_branch},parent:clone(input.parent),fork_revision:input.fork_revision,author_revision:input.fork_revision+1,head_revision:input.fork_revision+1,created:false});
const complete=(id,result)=>({version:1,operation_id:id,running:false,phase:"completed",error:null,result});
const running=()=>({version:1,operation_id:22,running:true,phase:"author_applying",error:null,result:null});
function preview(input,session) {
    const json=JSON.stringify({version:1,input,child:{story:input.parent.story,branch:input.child_branch},before:{fact:input.operation.fact,proposition:input.operation.expected_proposition,source:{kind:"seed_fact",seed_id:"lantern-quay-v1",fact:input.operation.fact}},creation_revision:input.fork_revision+1,retained_knowers:2,excluded_suffix_events:input.expected_parent_revision-input.fork_revision,excluded_suffix_records:1,original_preserved:true,downstream_replayed:false,new_child_requires_fresh_derivatives:true});
    return {version:1,kind:"author_preview",session,preview_token:"11111111-1111-4111-8111-111111111111",preview_sha256:createHash("sha256").update(json).digest("hex"),preview_json:json,expires_seconds:600};
}
function fixture() {
    const calls=[],opened=[];
    let input=null,recovered=false,lostStart=false;
    const port={
        prepareStart:async raw=>{const value=JSON.parse(raw);input=value.input;calls.push("prepare");return complete(11,preview(input,value.session));},
        commitStart:async()=>{calls.push("commit");if(lostStart)throw Error("Transport");return running();},
        lookupStart:async()=>{calls.push("lookup");return complete(33,{version:1,kind:"author_lookup",found:true,outcome:outcome(input)});},
        status:async id=>{calls.push(`status:${id}`);if(!recovered)throw Error("Transport");return complete(id,{version:1,kind:"author_commit",session:"session-1",outcome:outcome(input)});},
        cancel:async id=>{calls.push(`cancel:${id}`);return running();},
        discardPreview:async()=>{calls.push("discard");return true;},
    };
    const author=new AuthorController(port,{refreshLibrary:async()=>{},openChild:async scope=>opened.push(scope)},async()=>{});
    author.contextChanged(context());author.setDraft(draft());
    return {author,calls,opened,recover:()=>{recovered=true;},loseStart:()=>{lostStart=true;}};
}
const render=(f,c)=>renderToStaticMarkup(createElement(AuthorPanel,{author:f.author,context:c}));
const buttons=html=>[...html.matchAll(/<button\b([^>]*)>([\s\S]*?)<\/button>/g)].map(match=>({disabled:/\bdisabled(?:=|\s|$)/.test(match[1]),text:match[2].replace(/<[^>]*>/g,"").replace(/\s+/g," ").trim()}));
const button=(html,text)=>buttons(html).find(value=>value.text===text);
const privateAbsent=html=>{for(const secret of ["PANEL_PRIVATE_OLD_A","PANEL_PRIVATE_NEW_B","PANEL_PRIVATE_REASON","relic-location","preview_json"])assert.ok(!html.includes(secret),`restricted recovery leaks ${secret}`);};
const noStart=html=>{for(const name of ["Prepare private impact preview","Confirm author correction in new timeline"])assert.ok(!button(html,name)||button(html,name).disabled,`${name} cannot be enabled in recovery-only state`);};
async function unknown(f) {
    f.author.setAuthorConsent(true);await f.author.prepare();f.author.setPreviewRead(true);await f.author.confirm(true);
    assert.equal(f.author.get().uncertain,true,"actual controller records synthetic transport uncertainty");
}
const tests=[];
const test=(name,run)=>tests.push({name,run});
test("known operation remains visibly inspectable when fresh author actions are blocked",async()=>{
    const f=fixture();await unknown(f);
    const blocked={...context(),brokerUncertain:true};f.author.contextChanged(blocked);
    const before=clone(f.calls),html=render(f,blocked);
    assert.ok(button(html,"Inspect known native operation"),"known-ID recovery control must remain visible");
    assert.equal(button(html,"Inspect known native operation").disabled,false);
    assert.ok(html.includes("captured-child")&&html.includes("quay"),"bound captured child remains visible");
    assert.ok(/unknown|unresolved/i.test(html),"unknown is not relabeled cancelled or failed");
    assert.equal(button(html,"Check saved child only")?.disabled,true,"lookup honors current unavailable author gate");
    privateAbsent(html);noStart(html);assert.deepEqual(f.calls,before,"render must not dispatch or retry");
    await f.author.lookup();assert.ok(!f.calls.includes("lookup"),"blocked readonly lookup is not silently admitted");
    f.author.dispose();
});
test("explicit known-ID inspection displays an actual controller result without enabling new starts",async()=>{
    const f=fixture();await unknown(f);const blocked={...context(),brokerUncertain:true};f.author.contextChanged(blocked);f.recover();
    await f.author.inspectOperation();assert.equal(f.author.get().outcome?.scope.branch,"captured-child");
    const html=render(f,blocked);assert.ok(html.includes("Saved child confirmed"));assert.ok(html.includes("existing recorded outcome"));
    assert.equal(button(html,"Open confirmed child")?.disabled,true,"open honors its actual current-context gate");
    noStart(html);privateAbsent(html);assert.equal(f.calls.filter(value=>value==="commit").length,1,"status did not apply twice");assert.equal(f.opened.length,0);
    f.author.dispose();
});
test("lost whole acknowledgment shows honest readonly recovery without inventing a known operation",async()=>{
    const f=fixture();f.loseStart();await unknown(f);const blocked={...context(),brokerUncertain:true};f.author.contextChanged(blocked);
    const html=render(f,blocked);assert.ok(/unknown|unresolved/i.test(html));assert.ok(html.includes("captured-child"));
    assert.ok(!button(html,"Inspect known native operation")||button(html,"Inspect known native operation").disabled,"no known-ID control for absent admission acknowledgment");
    assert.equal(button(html,"Check saved child only")?.disabled,true);privateAbsent(html);noStart(html);
    assert.equal(f.calls.filter(value=>value==="commit").length,1);assert.equal(f.calls.filter(value=>value.startsWith("status:")).length,0);
    f.author.dispose();
});
test("character or Play context never renders private preview and cannot start recovery writes",async()=>{
    for(const delta of [{observer:"mira"},{view:"play",observer:"player"}]) {
        const f=fixture();await unknown(f);const restricted={...context(),...delta};f.author.contextChanged(restricted);
        const html=render(f,restricted);privateAbsent(html);noStart(html);
        assert.equal(button(html,"Check saved child only")?.disabled,true);assert.ok(html.includes("captured-child"));
        f.author.dispose();
    }
});
test("foreign root or absent native context does not expose an earlier recovery identity",async()=>{
    const f=fixture();await unknown(f);f.author.contextChanged(null);
    const html=render(f,null);assert.ok(!html.includes("captured-child"));assert.ok(!button(html,"Inspect known native operation"));assert.ok(!button(html,"Check saved child only"));privateAbsent(html);noStart(html);f.author.dispose();
});
test("normal eligible exact-preview form remains guarded and available",async()=>{
    const f=fixture();f.author.setAuthorConsent(true);await f.author.prepare();const html=render(f,context());
    assert.ok(button(html,"Prepare private impact preview"));assert.ok(html.includes("Exact private impact preview"));assert.ok(html.includes("PANEL_PRIVATE_REASON"));
    assert.equal(button(html,"Confirm author correction in new timeline")?.disabled,true,"second consent still requires reading exact preview");assert.ok(html.includes("restart"));f.author.dispose();
});
const results=[];
for(const {name,run} of tests){try{await run();results.push({name,passed:true});}catch(error){results.push({name,passed:false,error:error.message});}}
await writeFile(path.join(directory,`author-panel-recovery-results-${randomUUID()}.json`),JSON.stringify({evidence:"actual-controller-and-headless-React-render-with-mock-native",results},null,2),{flag:"wx"});
const failures=results.filter(result=>!result.passed);
console.log(`${results.length-failures.length} passed / ${failures.length} failed author recovery render cases; mock native, no IPC/WebView/Store execution.`);
for(const failure of failures)console.error(`${failure.name}: ${failure.error}`);
if(failures.length)process.exitCode=1;

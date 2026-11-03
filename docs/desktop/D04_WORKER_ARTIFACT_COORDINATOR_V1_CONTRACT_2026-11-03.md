# Fixed worker artifact coordinator v1: source contract

Refs #25 D04.01/.02/.04; #31 D09.03/.05 supporting; #21.
Base accepted PR379/main7b707bc9. SOURCE ONLY / UNRUN. All run grants SPENT.
This is a development build harness, never an app/model/IPC/remote tool API.

## Scope and explicit missing adapter

Implement the actual fixed six-step orchestration now, using accepted
`planWorkerArtifactComparisonV1` and narrowly named trusted local ports.
A synthetic port journey proves ordering/refusal/cancellation only. Concrete
Windows filesystem/tool/env/SDK/child adapters are NOT implemented or admitted
by this slice. No port result or public flag mints Author capability or native
qualification. No arbitrary commands, lookup fallback, normal-worker adoption,
C++/profile/engine/shared/Android changes or new dependencies.

Historical prelink-v2 output is insufficient: its34 profiles/name coverage
describe retained reports, not fresh installed bytes or selected resolution.
The future admit adapter must prove current source/headers/tools/ALL inputs,
physical roots and Windows identity, environment, ordered search and no-shadow
(including earlier search locations), ownership, exclusive outputs, storage,
FULL remaining reserves and the exact unspent finite owner authority.
New candidate object DEFAULTLIB/directives/resolution must be checked AFTER
its compile and BEFORE its LINK. Unknown names/directives/resolution stop.
No recursive search, /NODEFAULTLIB, replacement libraries or inherited wrappers.

Root owns this NEW contract then NEW
`native/llama-worker/worker_artifact_coordinator_v1.mjs`.
Separate serialized author freezes NEW `worker_artifact_coordinator_v1_first.mjs`
BEFORE producer. Reviewer reads source only. No source/check execution now.

## Factory, immutable boundaries and local clock

Export ONLY `createWorkerArtifactCoordinatorV1({config,ports,clock})`.
Three exact own enumerable DATA keys on plain/null-prototype object; no getters,
symbols/extras/coercion. Config is passed to accepted recipe planner; propagate
its two fixed recipe errors. Capture the returned immutable recipe and SHA256
of its exact JSON.stringify UTF8 bytes. Do not accept a caller-supplied recipe.

ports exact own DATA function keys ONLY:
admit,launchStep,inspectOutputs,prepareManifest,recheck,compare,record.
clock exact own DATA function keys ONLY set,clear, with trusted local
set(callback,milliseconds) -> opaque token and clear(token) semantics. Like
real setTimeout, set does not invoke inline; clear cancels a pending callback.
Capture function values at construction so caller mutations cannot replace them.
These are trusted development capabilities, not model/player input. A future
real adapter must bind clock to real timers and implement all physical proof
and resource duties; test clocks/ports cannot grant native admission.

Factory invalid shape throws ONLY Error('WorkerArtifactCoordinatorV1Invalid').
Return frozen {run,cancel}. run() is single-use: consume before first await;
any concurrent/subsequent call rejects Error('WorkerArtifactCoordinatorV1Used')
without port calls or another record. cancel() returns true exactly once before
terminal report selection (including before run), false thereafter, including
while recording that terminal report; signal active launch via a
standard AbortSignal and wait for owned closure, never start a later child.
No reset/retry/re-run API. Cancel does not delete or restore outputs.

Every normal port request is detached frozen JSON DATA with a context
{attempt,recipe,baseline,closure} once admitted; all four are lowercase SHA256.
Initial admit receives {version:1,recipe:<recipe object>,recipeHash:<SHA256>}.
Other step requests have version1, context, index and fixed step from that recipe;
launchStep additionally receives AbortSignal (freeze request, not signal).
recheck adds when ('before','manifest','after'); inspectOutputs adds stage;
prepareManifest adds the candidate's current linked executable/manifest facts;
compare has index6 and both candidates' compiled objects/final executables.
record receives the final frozen report directly. Exact request keys (listed
order is descriptive, not a separate semantic requirement):

- admit: {version,recipe,recipeHash} as above.
- recheck: {version,context,index,step,when}.
- launchStep: {version,context,index,step,policy,signal}; policy exact
  {timeoutMs,stdoutCap,stderrCap,drainMs}, drainMs5000 and other values below.
- inspectOutputs: {version,context,index,step,stage}, stage===step.stage.
- prepareManifest: {version,context,index,step,linked}; linked exact
  {executable,manifest} containing that candidate's stored LINK file facts.
- compare: {version,context,index,candidates}; index6, candidates dense
  [{id:'A',object,executable},{id:'B',object,executable}], compiled object and
  final post-embed PE facts, each entry exact keys id,object,executable.
- record: report itself, no wrapper and no signal.

No port can choose a tool,
argument, index, stage, path, subsequent operation or recovery action.

All replies, including record acknowledgement, MUST be primitive canonical JSON strings, <=4096 UTF8
bytes, no surrounding whitespace/newline: JSON.stringify(JSON.parse(wire))===wire.
Use exact own keys/types below; no object getters/proxies execute in replies.
Store each structurally valid parsed receipt as a detached deep-frozen value
BEFORE interpreting failure flags. Invalid reply text is not copied into public
errors/reports; real adapters must retain raw diagnostics under their own caps.
Each operation has an outer timer: admit/recheck/inspectOutputs/prepareManifest/
compare/record5000ms; launchStep uses fixed timeoutMs+5000ms closure allowance.
On timer expiry abort, mark PORT_TIMEOUT; active launch means unknownClosure.
On cancel, give active operation at most5000ms to settle; a still-active launch
then stops CLOSURE/unknownClosure, other operations CANCELLED. Ignore every
late resolve/reject; attach rejection handlers. Clock failures stop PORT_ERROR.
The original deadline is not extended: its expiry and the cancel-grace timer
race, first expiry wins with its specified code. Clock setup failure BEFORE
offering a port makes no port call and no offered-launch increment or unknown
child claim. A clock failure after offering a launch is conservatively unknown.
Record-stage clock errors instead produce the EVIDENCE override below.
A timer is a stop detector, not OS/process-tree containment.

## Exact receipts

Common fields (all exact): version1,kind,attempt,recipe,baseline,closure.
Except admit, all four digests MUST equal the admitted context. Admit recipe
equals recipeHash; the other three are nonzero lowercase hex64 identifiers.
No zero digest. All bounded integers are JS safe integers.

admit kind worker_artifact_admission_v1; common + runCount,checks.
runCount===1. checks exact14 boolean keys ALL true:
source,headers,tools,inputs,physicalRoots,environment,searchOrder,noShadow,
ownership,exclusiveOutputs,storage,reserve,authority,normalWorker.
Any false stops ADMISSION, zero launches. This is a required physical proof
boundary of the unimplemented adapter, not a claim booleans prove SDK freshness.

recheck kind worker_artifact_recheck_v1; common + index,when,checks.
index/when equal request; checks same exact14 booleans, all true or RECHECK.
It must revalidate unchanged source/tool/input/context/normal worker/ownership
and FULL remaining reserves, not typical logs or historical JSON alone.

launchStep kind worker_artifact_process_v1; common + index,pid,closed,unknown,
exitCode,timedOut,overflow,killAttempted,ioError,elapsedMs,stdoutBytes,stderrBytes,
stdoutHash,stderrHash,processTreeContained.
index matches; pid integer1..2147483647; exitCode signed32 integer or null;
five flags closed/unknown/timedOut/overflow/killAttempted and ioError booleans;
processTreeContained MUST false; elapsedMs integer0..timeoutMs+5000.
stdout/stderr integers0..caps; hashes lowercase hex64 (empty hash allowed here).
Fixed request policy:
compile/link timeoutMs120000; manifest30000.
compile caps65536/4096; link16384/4096; manifest4096/4096.
Unknown OR !closed OR ioError -> CLOSURE/unknownClosure before later operations.
timedOut/overflow -> PROCESS. killAttempted -> PROCESS unless cancellation is
requested and closure is known (then CANCELLED). exitCode nonzero/null -> PROCESS
unless known-closed cancellation. Otherwise exit0 is required.
The adapter drains both pipes concurrently, retains raw/Base64/decoded charges,
tries one kill on timeout/overflow/cancel, bounds drain5s and preserves failures.
This coordinator validates receipts; it does not itself create native processes.

File fact exact {sha256,bytes}, lowercase hex64, bytes integer1..67108864;
manifest additionally bytes<=65536. Null only where explicitly allowed.
inspectOutputs kind worker_artifact_outputs_v1; common + index,owned,ordinary,
rosterComplete,withinBudget,directivesValidated,resolutionComplete,object,
executable,manifest. Six booleans all true or OUTPUT.
Compile: object required, executable/manifest null. Link: all three required;
object matches that candidate's compile fact. Manifest: all required, object
still matches compile and manifest matches link; executable is final post-embed.
New-object directives/resolution true at compile is mandatory BEFORE LINK.
Full ordinary owned output/temp/descendant roster and retained charges are an
adapter obligation, not inferred from one output hash.

prepareManifest kind worker_artifact_manifest_v1; common + index,ordinary,
exclusive,equal,withinBudget,manifest,preEmbed,copy. Four booleans all true or
MANIFEST; manifest equals link fact, preEmbed and copy both equal linked exe.
The adapter makes an exclusive ordinary copy BEFORE MT; failed copy remains
retained. No empty/missing manifest or hardlink/reparse fallback.

compare kind worker_artifact_compare_v1; common + index6,ordinary,withinBudget,
objectEqual,executableEqual. All four booleans true AND A/B object/final-PE
facts independently equal in both hash/bytes, else COMPARE. No normalization,
binary touching, dependency rebuild or normal-worker adoption.

record kind worker_artifact_record_v1; exact {version,kind,retained,report}.
version1,retainedtrue,report=SHA256 of final report's exact JSON.stringify UTF8.
It is called ONCE on terminal success/failure/cancel, no retries/overwrites.
The acknowledgement is excluded from report.receipts to avoid a self-hash cycle.
Pre-run cancellation still attempts this one record operation. If its timer
setup fails, record itself is not called; EVIDENCE/retained:false and no retry.
Real adapter preserves raw failing receipts/outputs and monotone journal.
Failed/invalid/timed-out record returns retained:false with code EVIDENCE and
firstCode the original report code; do not attempt a second record.

## Fixed state transitions and terminal report

At each awaited boundary check cancellation before starting. After return,
validate/store the receipt and interpret semantic failure before cancellation.
For launch, closure/timeout/overflow failures take precedence; known-closed
kill/nonzero during requested cancellation becomes CANCELLED as specified above.
No later child after cancellation, failed validation, changed context, exhausted
reserve, exception, uncertain closure or evidence failure. First failure wins.
Synchronous throw/rejected port -> PORT_ERROR; launch throw/reject is unknown.
Malformed/oversized/noncanonical/wrong-kind/key/index/context reply -> RECEIPT;
if launch is malformed, unknownClosure=true. No exception message/path leak.

Trace:
admit; for EACH index0..5: recheck(before), then
  for manifest ONLY: prepareManifest, recheck(manifest),
  launchStep, inspectOutputs, recheck(after);
then compare(index6), record.
Step order is compileA,linkA,manifestA,compileB,linkB,manifestB exactly.
Increment attempted immediately BEFORE actually offering launchStep, AFTER
successful timer setup (offered attempts, not a claim that a native PID exists).
Increment completed immediately after that step's inspectOutputs AND valid
successful after-recheck, BEFORE honoring simultaneous cancellation. Thus a
cancelled report may have completed6 but cannot become success. No phase skip
or fallback.
Every request/receipt remains frozen even if caller later mutates original data.
AbortSignal internals are deliberately not frozen.

run resolves frozen {report,retained}. Report exact keys:
version1,kind worker_artifact_coordinator_report_v1,
status ('passed','failed','cancelled'),code (null on pass, else finite code),
firstCode (null except evidence failure),attempt,recipe,baseline,closure,
attempted,completed,receipts,unknownClosure,
qualifiedfalse,linkQualificationfalse,closureCompletefalse,
requiresFreshAdmissiontrue,normalWorkerUnchangedRequiredtrue,
processTreeContainedfalse.
Before semantically successful admit, attempt/baseline/closure null; recipe
always its digest. A structurally valid false-check admit receipt is preserved
in receipts but does NOT establish report context.
Finite codes ONLY ADMISSION,RECHECK,PROCESS,CLOSURE,OUTPUT,MANIFEST,COMPARE,
CANCELLED,PORT_TIMEOUT,PORT_ERROR,RECEIPT,EVIDENCE.
status cancelled ONLY codeCANCELLED; others failed. Success attempted/completed6.
Report JSON<=131072B; no arbitrary error text or artifact adoption/Author tokens.
The fixed trace has at most30 receipts, each <=4096B, plus less than2048B of
closed report metadata/delimiters; the full bound must be tested explicitly.
Never drop/truncate receipts to fit. Real raw diagnostics stay with the adapter.

## Independent FIRST and later execution gate

Export `runWorkerArtifactCoordinatorSelfchecksV1(api)`, exact API
{createWorkerArtifactCoordinatorV1}. Exactly20 groups C01..C20 with six-key
summary version1,kind worker_artifact_coordinator_first_v1,
executed/passed20,failed0,failed_case_ids[] as sole success.
Missing API -> UNRUN_SETUP, no invented RED.
Pure synthetic ports/clock, no filesystem/process/native/SDK/report inputs;
fixtures<256KiB/group, no real timers or child launches in FIRST.

Freeze explicit call traces and exact argument/receipt expectations BEFORE
producer: C01 factory/port/clock/getter refusal; C02 full six-child success;
C03 failed fresh admission/zero launches; C04 false each fresh recheck/reserve/
source/tool/input/normal check; C05 new-object directives before LINK;
C06 process nonzero/timeout/overflow; C07 unknown/throw/reject closure;
C08 missing/unequal/nonordinary pre-embed and manifest; C09 wrong-step/context/
kind/keys/noncanonical/oversized replies; C10 output roster/reparse/ownership;
C11 A/B object and final PE mismatch; C12 cancel before run/every boundary;
C13 in-flight launch cancel and known closure; C14 fake-clock deadline,
cancel-grace timeout/late completion fencing; C15 concurrent/reused run refusal;
C16 detached/frozen request/receipt/captured ports; C17 first failure/evidence
failure/no record retry; C18 byte/integer bounds; C19 no adoption/qualification;
C20 complete bounded report/receipt trace, closed operation set/no hidden child.
For C20 assert actual30-receipt trace/report bounds AND the conservative
30*4096+2048<=131072 arithmetic; do not add forbidden padding fields to invent
a maximum-sized valid receipt.
Keep every assertion; any corrected contract/test precedes producer.

New code checks remain UNRUN until their exact whole supervisor/collector,
source retention/reviews/fresh inventory/full reserves and a separate finite
owner decision. Current2796KiB cap/all historical output/limits stay unchanged.
No SDK observations, tool setup, builds/linking/MT/worker/model/app/device/OS,
downloads/settings/deletion/desktop control or retry is authorized by this plan.
Full D04/D09/desktop/human-quality gates open, AuthorDisabled/PR366 unrun.

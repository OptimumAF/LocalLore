# Prospective frontend evidence admission

Refs #31, supporting D09.03/.04/.07. **Source proposal; no implementation,
execution, resource acceptance or new runtime admission follows this document.**
The existing D05 allocation failure remains failed and retained. This separate
development-runner change does not reopen that cohort or the stopped D09 probes.

## Observation and scope

At tested b87ecc3a, the existing76-child frontend driver functionally passed but
retained38,790,893 bytes in the designated root against a33,554,432-byte allocation. The
coordinator measured only after the whole driver. Multiple retained source bundles
made the forecast too small. Existing native evidence and all failures survive;
larger aggregate headroom does not cure the failed suballocation. Later read-only
reconciliation finds four additional source-routed bundles/276,119 bytes, making
combined frontend evidence39,067,012 bytes and the overrun5,512,580 bytes before
outer logs/build products. The original narrower failure record stays unchanged.

Add opt-in `node verify-frontend.mjs --bounded` to the existing fixed roster.
Zero-argument legacy mode retains its existing checks; unknown/repeated arguments
fail before any child. No accepted child selector, shell text, executable path,
test source or remote service is introduced. The bounded path still launches only
the current Node executable and source-controlled roster, sequentially, with
shell:false and windowsHide:true. Existing esbuild launches its installed native
BUILD TOOL service; this is neither a native application journey nor a model/SDK
operation. Bounded mode refuses nonempty ESBUILD_BINARY_PATH rather than accepting
an alternate executable. Trusted provisioned Node/dependencies/environment remain
prerequisites; this is not a general hostile-environment execution boundary.
No existing test assertion/body is edited or omitted. Four routing preambles are
changed only to honor LOCALLORE_CHECK_OUTPUT_DIR with their original fallback,
UUID names and bundle bytes: check-contract.mjs, check-export-controller.mjs,
check-model-controller.mjs and check-inspection-controller.mjs. Existing
build.mjs remains unmodified. The new independent policy
test is registered once; future bounded success requires every registered step.

Root owns new apps/desktop/frontend-evidence-policy.mjs and existing
verify-frontend.mjs, the four routing preambles above, plus docs. Independent FIRST owns only new
check-frontend-evidence-policy-review.mjs on its separate branch/worktree. Freeze
the accepted contract/FIRST before different-author production. No Rust, UI,
Host, schema, inference, .github, dependency or global setting change.

## Fixed constants and record

The helper exports immutable FRONTEND_EVIDENCE_LIMITS:

- outputBytes67,108,864; cumulativeBytes671,088,640;
- productBytes16,777,216;
- stepReserveBytes4,194,304; metadataReserveBytes1,048,576;
- entries2,000,000; streamBytes262,144 per stream per child;
- consoleBytes4,194,304 total ENCODED UTF-8; summaryBytes32,768 reserved within it;
- childMs240,000; stopGraceMs5,000.

These are local cooperative runner limits, not an OS quota. An individual trusted
child may write beyond a reservation before the next inventory. Such an overrun
must FAIL and latch; never promise containment of arbitrary filesystem writers,
all descendant processes or arbitrary writes outside measured roots. Neither this mode nor source
review grants device, native application, real-model or isolation execution.

Bounded mode requires explicit LOCALLORE_CHECK_OUTPUT_DIR and
LOCALLORE_CHECK_BUDGET_FILE. Both already exist on physical D:. Output and source
directories are disjoint (neither contains the other); the ordinary admission
file is outside both. Use actual Node observables: ordinary lstat entry types,
isSymbolicLink and realpath alias refusal, recording realpath/dev/ino directory
identity and rejecting detected changes. Recheck ancestors/identity during
inventories; do not claim rejection of every Windows reparse tag, an OS lease or
raceproof admission. Missing required paths/wrong types refuse. Children receive
TEMP/TMP=path.join(outputDir,"_tmp"), an ALREADY EXISTING ordinary physical-D
subdirectory included in the output inventory. This accounts esbuild's conditional
os.tmpdir staging; the source audit does not prove that branch ran previously.
The commanding shell starts with TEMP/TMP D:/Dev/_Temp. No global changes or
implicit directory creation. Direct-child closure does not prove every build-tool
descendant drained or stopped writing; retain that cooperative limitation.

Meter the known source products separately: sourceRoot/dist recursively and
sourceRoot/ui/host.generated.ts. Missing dist/product leaf means zero bytes;
existing entries/parents must pass the same ordinary-path checks. These are fixed
paths, not a supplied file selector. Refuse product total above productBytes.
Charge live products in aggregate accounting and positive growth in each step;
they are not covered by the output-root limit. The external evidence count must
exclude these separately metered live products to avoid duplicate charging.
Only the fixed product LEAF may be missing: sourceRoot/ui is a required ordinary
parent even when host.generated.ts is absent. Missing/replaced required ancestors
must not silently turn a previously bound product into zero bytes.

The coordinator creates a NEW <=4096-byte admission file. Exact serialization is
UTF-8 JSON.stringify of the following eight keys IN THIS ORDER plus one LF:

```json
{"version":1,"kind":"d09_frontend_evidence_admission_v1","source_revision":"<40 lowercase hex>","output_path_sha256":"<64 lowercase hex>","initial_output_bytes":0,"output_limit_bytes":8388608,"external_evidence_bytes":0,"cumulative_limit_bytes":671088640}
```

The example is a schema illustration, not executable admission. Strict fatal
UTF-8 decoding, exact keys/order/types, canonical byte equality, safe nonnegative
integers and exact kind/version are mandatory. Canonical equality rejects
duplicate/escaped/unknown keys, extra whitespace/BOM/trailing material and alternate
numeric spellings without adding a general JSON parser. Digests/revision use
lowercase ASCII hex. Limit is at most outputBytes; cumulative limit is exactly
cumulativeBytes. Require at least stepReserveBytes+metadataReserveBytes available.
initial_output_bytes must equal the actual initial output inventory. The external
count includes the explicitly named retained evidence roster and reserved metadata
outside output, including this record; no private filesystem path is in the JSON.
Path digest is SHA256 of UTF-8 path.resolve(output).toLowerCase() on Windows.
Source revision is the current HEAD, never a branch name or caller-supplied claim.

The coordinator never replaces/reuses a consumed record, raises/resets a failed
cap, deletes evidence or retries automatically. The read/inventory-only module
enforces one policy instance; it is not a persistent one-shot registry. A
zero-growth run could reopen a record, so no cross-instance exclusion is claimed.
Failed/spent previous gates are reported independently even when their retained
bytes are charged in external_evidence_bytes. The640MiB named aggregate does not
claim an inventory of all historical project data.

## Actual helper seam

The development-only module exports:

```js
parseFrontendEvidenceAdmission(rawBytes, expectedRevision, expectedPathDigest)
openFrontendEvidencePolicy({ sourceRoot, outputDir, admissionFile, sourceRevision })
```

parse returns a checked, detached record or throws. open validates paths, reads
the bounded record, inventories and binds it to the actual inputs. It returns:

```js
{ beforeStep(index), completeStep(index, outcome), finish(), snapshot() }
```

Methods are async except snapshot. They retain only small counters/metadata,
never child source, story data or page bodies. No spawn, shell, general read/write
command or externally callable service is exported by this module. Tests import
the actual helper with disclosed fs/path/timer doubles where appropriate; actual
driver tests intercept its fixed child calls, not a copied scheduling policy.

Indexes start at0 and advance exactly once. All async methods acquire a private
in-flight guard synchronously BEFORE their first await. A concurrent method call
latches Sequence failure; the original pending method must recheck that latch
before publishing success. No overlapping step, skipped index, reuse after finish
or recovery after failure. beforeStep inventories actual
ordinary files/directories, rejecting unsupported entries, reparse/path changes,
unsafe sums or combined output/product entry overflow. Require output+stepReserve+
metadataReserve within the admitted output limit, and external+products+that sum
within the fixed aggregate limit,
before permitting the next child. No mutation occurs during inventory.

Successful beforeStep captures THIS STEP's output/product measurements, not the
record's original baseline, and admits exactly that index. completeStep receives
the CLOSED result shape:

```js
{ code, closed, timedOut, truncated, error, stdoutBytes, stderrBytes }
```

code is an integer or null; the four flags closed/timedOut/truncated/error are
booleans; stream byte counts are safe nonnegative integers. Reject extra keys and
malformed values. Require known close, code0, no timeout/truncation/error and each
stream within streamBytes. Inventory again; output may not exceed its admitted
limit or exhaust metadata headroom; products may not exceed their fixed cap;
external+output+products+metadataReserve must fit aggregate. The SUM of positive
output growth and positive product growth since THIS STEP's beforeStep may not
exceed stepReserveBytes. A shrinking product cannot subsidize new evidence.
Decreases do not erase failures or authorize cleanup. Any bad
outcome/inventory sticks FAILED and forbids subsequent step/finish success.

finish is allowed only while healthy, no child outstanding and at least one step
completed; it inventories and checks caps again. The driver calls it only after
ALL fixed steps, then performs its existing normal-bundle exclusion assertions.
snapshot has exactly seven keys: status,nextIndex,activeIndex,initialBytes,
currentBytes,productBytes,error. Status is ready initially/after completeStep,
running after successful beforeStep, finished after finish, failed after the first
failure. nextIndex is the count of successfully completed steps; activeIndex is
null before admission/after success, or the admitted integer retained on failure.
initialBytes is the checked output baseline; currentBytes/productBytes are the
latest measured safe integers, or BOTH null after an unavailable inventory or
unknown child closure. error is null or the first sticky category: Admission,
Path,Inventory,Reserve,Sequence,Outcome,StepBudget,OutputBudget,ProductBudget,
AggregateBudget,UnknownChild. Throw Error("FrontendEvidence"+category).
parse/open admission errors use the same vocabulary. All three async methods
return a detached snapshot on success. Calls after failed rethrow the first sticky
category; calls after finished throw Sequence. Neither changes the retired state.
snapshot itself never performs IO or exposes mutable
internal state. Missing implementations/interfaces are UNRUN_SETUP in FIRST, never
zero-case PASS or invented behavioral failures.

## Driver lifetime and evidence

Before ANY Git child, the bounded branch performs a private physical-D/ordinary/
realpath-ancestor check of its actual source URL directory and the explicit parent
TEMP and TMP directories. Reject missing, non-D, aliased or non-directory inputs
without invoking Git. This is not a new exported path/execution service; the
helper still validates the complete source/output/admission binding afterward.
The bounded branch obtains current clean HEAD using only fixed read-only Git
rev-parse HEAD and status --porcelain commands (15s,64KiB each). Failure, malformed
revision, dirty source or unknown closure refuses before the first Node check.
No caller-provided Git command or new mutation is accepted. Recheck the same clean
HEAD before finish; no final Git or bundle-read/pass work after a latched child or
storage failure. This is cooperative source binding, not protection from every
concurrent file edit.

Each actual child receives the explicit output directory, D: TEMP/TMP and current
environment. Capture only bounded prefixes of stdout/stderr, counting original
bytes; discard excess while draining, mark truncation and make one best-effort
stop. Finite240s deadline, one stop attempt and5s grace. A close during grace is
known closure but still FAILS the timeout/overflow. Missing close at grace expiry
sticks unknown ownership and stops the runner; no retry or later child. Signal,
spawn failure and nonzero exit are failures. Listen for close, not merely exit.
On unknown-close grace expiry, make bounded best-effort attempts to destroy BOTH
pipe handles and unref the owned ChildProcess so those handles do not keep the
coordinator alive indefinitely. Attempt each independently even if another throws;
do not make a second stop attempt, claim the child drained, or clear the unknown
latch on later events. This releases coordinator references, not a process-tree
containment/termination guarantee. No real unknown-child probe is admitted here.

Print each bounded child prefix as JSON string fields with bounded
machine-readable metadata, including original byte counts and known/unknown
closure; do not invent passing cases from truncated evidence.
Count actual encoded JSON bytes, including escaping/metadata/newlines, against the
TOTAL consoleBytes budget, keeping summaryBytes available for the final record.
Per-child raw byte limits alone do not bound JSON expansion or all77 steps' logs.
If the next receipt would exhaust that allowance, omit its text prefixes, mark
truncation/FAIL and stop advancing; emit only compact metadata and the bounded
final summary using the reserved space. No later Git/child/bundle-read/PASS follows
that failure. Caller admission accounts up to consoleBytes outside outputDir;
this is separate from the filesystem metadata reserve. Do not promise the console
sink itself is controlled by the runner or silently truncate successful evidence.
Compact failure metadata AND the final summary jointly fit the reserved32KiB,
using one counter across stdout/stderr. Label omitted text as runner ConsoleBudget
truncation; preserve the actual child's close/code/original byte counts rather
than implying it exceeded its raw stream cap. Policy failure may remain Outcome.
No automatic artifact directory, model/native execution, output deletion or
normal-product restoration branch is added. A final bounded summary states exact
fixed step count, success/failure and cooperative limitations. Public reports
redact local paths; private logs remain local/ignored.

The bounded terminal JSON record has kind="d09_frontend_evidence_run_v1",
passed:boolean and completedSteps:safe nonnegative integer, plus bounded diagnostic
fields. This discriminator identifies OVERALL runner status. A prior child's
JSON-quoted stdout containing PASS: remains valid evidence when a later step
fails; it is not an overall success marker. Preserve that prefix. The existing
standalone final PASS line may occur only after whole-run success. Tests must
distinguish these two scopes rather than reject every PASS substring.

## Verification and admission gate

Independent FIRST covers strict record/path/size admission, aggregate accounting,
existing nonempty roots, fixed product accounting, the existing owned _tmp path,
before-step reserves, exact indexes/one outstanding child/async reentry,
post-child positive growth and metadata reserve, sticky failures despite later
shrink, observable path/identity/unknown/overflowing inventories, detached snapshots
and finish sequencing. Exercise the actual four routing preambles to prove the
explicit root is honored and original fallback/UUID/assertions are preserved.
Exercise actual driver source with disclosed child/fs/Git/timer doubles: unchanged
fixed roster, zero/--bounded arguments, no arbitrary child selection, close versus
exit, bounded multibyte/error output, deadline/stop/grace and no later Git/child/
bundle-read/PASS after storage or unknown closure. Keep legacy behavior and every
existing check intact. Also test aggregate encoded log limits/JSON expansion and
the reserved final summary; no over-budget record is printed as complete success.
Missing helper/registration remains setup unavailable.
Freeze additional independent cases before the narrow source-review fixes:
unknown Node/Git closure detaches both pipes and unreferences the process,
pre-Git source/TEMP refusal, and missing required ui parent (initial and retired).
Default synthetic source fixtures include that required ui parent and valid parent
TEMP/TMP; these are fixture prerequisites, not changed original assertions.

Source authors run no formatter/Node/build/test/fixture/native/model/SDK operation.
Root may propose a fresh <=8MiB policy-test allocation after freeze/review, counting
all retained D05/D07 evidence under the unchanged640MiB named joint cap. That future
plan admits only memory/doubled-policy checks, formatting and small source proofs,
not a repeat full frontend driver or application. Actual bounded whole-driver
execution requires its own later prospective plan and cannot repair the earlier
32MiB failure. No new execution is admitted here.

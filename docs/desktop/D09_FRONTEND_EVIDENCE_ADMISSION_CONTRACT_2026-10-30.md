# Prospective frontend evidence admission

Refs #31, supporting D09.03/.04/.07. **Source proposal; no implementation,
execution, resource acceptance or new runtime admission follows this document.**
The existing D05 allocation failure remains failed and retained. This separate
development-runner change does not reopen that cohort or the stopped D09 probes.

## Observation and scope

At tested b87ecc3a, the existing76-child frontend driver functionally passed but
retained38,790,893 bytes against a declared33,554,432-byte allocation. The
coordinator measured only after the whole driver. Multiple retained source bundles
made the forecast too small. Existing native evidence and all failures survive;
larger aggregate headroom does not cure the failed suballocation.

Add opt-in `node verify-frontend.mjs --bounded` to the existing fixed roster.
Zero-argument legacy mode retains its existing checks; unknown/repeated arguments
fail before any child. No accepted child selector, shell text, executable path,
test source or remote service is introduced. The bounded path still launches only
the current Node executable and the source-controlled roster, sequentially, with
shell:false, windowsHide:true and no desktop/native/model/SDK launch in this work.
No existing test body/assertion is edited or omitted. The new independent policy
test is registered once; future bounded success requires every registered step.

Root owns new apps/desktop/frontend-evidence-policy.mjs and existing
verify-frontend.mjs plus docs. Independent FIRST owns only new
check-frontend-evidence-policy-review.mjs on its separate branch/worktree. Freeze
the accepted contract/FIRST before different-author production. No Rust, UI,
Host, schema, inference, .github, dependency or global setting change.

## Fixed constants and record

The helper exports immutable FRONTEND_EVIDENCE_LIMITS:

- outputBytes67,108,864; cumulativeBytes671,088,640;
- stepReserveBytes4,194,304; metadataReserveBytes1,048,576;
- entries2,000,000; streamBytes262,144 per stream per child;
- childMs240,000; stopGraceMs5,000.

These are local cooperative runner limits, not an OS quota. An individual trusted
child may write beyond a reservation before the next inventory. Such an overrun
must FAIL and latch; never promise containment of arbitrary filesystem writers,
all descendant processes or writes outside the designated root. Other temporary
outputs require their own accounted admission; neither this mode nor source
review grants device, native application, real-model or isolation execution.

Bounded mode requires explicit LOCALLORE_CHECK_OUTPUT_DIR and
LOCALLORE_CHECK_BUDGET_FILE. Both already exist on physical D:. Output and source
directories are disjoint (neither contains the other); the ordinary admission
file is outside both. Reject aliases/reparse ancestors, missing paths and wrong
entry types. Recheck output identity/ancestors during inventories. Set process
TEMP and TMP to the existing physical D:/Dev/_Temp before starting children;
no global environment/tool changes or implicit directory creation.

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

No replacing a consumed record, cap increase/reset, deletion or automatic retry.
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

Indexes start at0 and advance exactly once. No overlapping step, skipped index,
reuse after finish or recovery after any failure. beforeStep inventories actual
ordinary files/directories, rejecting unsupported entries, reparse/path changes,
unsafe sums or entry overflow. Require output+stepReserve+metadataReserve within
the admitted output limit, and external+that sum within the fixed aggregate limit,
before permitting the next child. No mutation occurs during inventory.

completeStep receives the CLOSED result shape:

```js
{ code, closed, timedOut, truncated, error, stdoutBytes, stderrBytes }
```

code is an integer or null; the four flags closed/timedOut/truncated/error are
booleans; stream byte counts are safe nonnegative integers. Reject extra keys and
malformed values. Require known close, code0, no timeout/truncation/error and each
stream within streamBytes. Inventory again; output may not exceed its admitted
limit, grow more than stepReserveBytes since admission, or exhaust the reserved
metadata headroom. Decreases do not erase failures or authorize cleanup. Any bad
outcome/inventory sticks FAILED and forbids subsequent step/finish success.

finish is allowed only while healthy, no child outstanding and at least one step
completed; it inventories and checks caps again. The driver calls it only after
ALL fixed steps, then performs its existing normal-bundle exclusion assertions.
snapshot is detached bounded metadata with status, nextIndex, activeIndex,
initialBytes, currentBytes and error category; callers cannot clear a latch by
mutating it. Missing implementations/interfaces are UNRUN_SETUP in FIRST, never
zero-case PASS or invented behavioral failures.

## Driver lifetime and evidence

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

Print each bounded child prefix after its known outcome, followed by bounded
machine-readable metadata; do not invent passing cases from truncated evidence.
No automatic artifact directory, model/native execution, output deletion or
normal-product restoration branch is added. A final bounded summary states exact
fixed step count, success/failure and cooperative limitations. Public reports
redact local paths; private logs remain local/ignored.

## Verification and admission gate

Independent FIRST covers strict record/path/size admission, aggregate accounting,
existing nonempty roots, before-step reserves, exact indexes/one outstanding child,
post-child growth and metadata reserve, sticky failures despite later shrink,
reparse/unknown/overflowing inventories, detached snapshots and finish sequencing.
Exercise actual driver source with disclosed child/fs/Git/timer doubles: unchanged
fixed roster, zero/--bounded arguments, no arbitrary child selection, close versus
exit, bounded multibyte/error output, deadline/stop/grace and no later Git/child/
bundle-read/PASS after storage or unknown closure. Keep legacy behavior and every
existing check intact. Missing helper/registration remains setup unavailable.

Source authors run no formatter/Node/build/test/fixture/native/model/SDK operation.
Root may propose a fresh <=8MiB policy-test allocation after freeze/review, counting
all retained D05/D07 evidence under the unchanged640MiB named joint cap. That future
plan admits only memory/doubled-policy checks, formatting and small source proofs,
not a repeat full frontend driver or application. Actual bounded whole-driver
execution requires its own later prospective plan and cannot repair the earlier
32MiB failure. No new execution is admitted here.

# Fixed native Saved timelines browser verification

Refs #30 (partial D08.04/.07). Prospective preparation only; no runtime admission.
Read the [product contract](D08_DOMAIN2_TIMELINE_BROWSER_CONTRACT_2026-10-30.md).

Extend the existing development-only paging launcher with one exact optional
argument `--timeline-browser-v1`. Its no-argument paging mode, eight-field record,
64MiB expected evidence/artifact limits, twenty captures and prior tests remain.
Reject every other argument combination before children or directories. Do not
run the old cohort to qualify this new browser.

The new mode uses a distinct eight-field record kind
`d08_domain2_timeline_browser_budget_v1` and filename
`d08-domain2-timeline-browser-budget-v1-<HEAD>.json`. Other field names retain
the existing parser contract. Here `d05_external_evidence_bytes` charges ALL
previous D05 evidence outside this NEW browser base; `external_evidence_bytes`
charges the named D07/D09 retention and other declared external evidence once.
For browser mode only, the per-base count is the observed NEW browser base;
the joint count is that base plus both external fields. Do not charge old D05
against the new32MiB base cap or omit it from the joint count. Old paging mode
keeps its existing base-plus-D05-external calculation and128MiB group limit.
The new mode's external field may exceed512MiB, but the unchanged640MiB joint
ceiling remains authoritative. Paging mode retains its old512MiB external bound.
Original target baseline/growth, source-growth, physical-D/path containment,
canonical source/product hashes, entry bounds and closed child policy remain.

Browser expected packet and total per-packet limit are20MiB; the browser base
(including source proofs/frontend evidence) is bounded32MiB. Actual prospective
admission must reserve that expected20MiB on top of every retained byte, plus
remaining frontend/metadata/product allowances. Independently inventory the
closed roster before admission. This is cooperative retained-output accounting,
not a filesystem quota or process-tree guarantee. No failed budget reset,
discarded capture, old output omission, cap raise or automatic retry.

## Fixed native adapter

Use the existing fixed fixture/oracle and short fresh p-UUID profile path. No
frozen database/profile is reused. Add the exact opt-in environment flag
`LOCALLORE_D08_TIMELINE_BROWSER_HARNESS=1` only alongside the existing development
and fixed paging-fixture selector, artifact directory and workspace variables.
Refuse malformed values or any other LOCALLORE harness flag. Normal mode never
registers these commands. No new production IPC/capability/schema/provider is
added. The existing no-argument read-only oracle stays lease-checked before and
after blocking work.

The frontend receives only a fixed `timelineBrowser` boolean in the development
initialization. It dispatches the new literal journey before the old paging
journey; the old journey is not executed. Use actual Main/controllers and UI
buttons, existing normal Gateway/native IPC, app-owned semantic snapshots and
hidden/unfocused WebView2 CapturePreview. No desktop activation/input/capture,
browser debug server, arbitrary code/file/shell endpoint or model operation.

The artifact writer has a separate fixed8MiB reserve for this mode, with the
existing sticky write-failure behavior. The old modes retain64MiB. Allow only the
six browser checkpoint labels below and a fixed failure label; the paging label
set must not become browser-authorized. New-mode labels remain unauthorized in
old modes. Preserve normal build hook exclusion checks.

## Journey and capture roster

The new mode's report/semantic `mode` is `domain2_timeline_browser_v1`.
Use these six checkpoint suffixes with prefix `d08-browser-`, in order:

1. `catalog`: select the existing saved author child `paging` at44 and show the
   real Saved timelines panel, with root0/child44 ancestry/current metadata.
2. `root`: click the exact root Resume button; observe the legacy main0 snapshot,
   then show its catalog. No first/recent fallback.
3. `child`: click the exact child Resume button; observe Domain2 child44 and show
   its catalog. Keep Fork hidden. No author/generation/write calls.
4. `observer`: acknowledged Story Lab/Mira lens, with actual child44 context;
   catalog browsing changes neither actor knowledge nor canonical history.
5. `enlarged-wide`: actual150% text at1280x900 with browser controls in view.
6. `enlarged-narrow`: actual150% text at620x900; readable ancestry/head/status and
   controls with no horizontal overflow. Restore size/text afterward.

Semantic checks between captures cover pending catalog/no stale old data, error
and explicit retry, old handlers/context switching, exact selected scope/revision,
visible pending operation/receipt/error state and no unsolicited generation.
Use fixed delayed/failed delivery around the SAME real branches read only when
needed; disclose this local delivery fault separately from native Host refusal.
Before/after fixed Rust oracle fingerprints must match for all three scopes and
observers. At disposal permit only the established bounded close/revoke roster,
then restore normal frontend/native products after all direct children are known
closed. Unknown closure or inventory/budget failure forbids later launch/build.

Inspect all six original PNGs individually after actual execution. Report actual
native UI/IPC separately from headless/source tests, and keep unsupported keyboard,
screen-reader, physical phone, real-model, offline/OS and full D08 gates open.
Independent FIRST must freeze argument/mode/record/budget/label compatibility
controls before Root modifies the launcher/native wiring. A separately authored
fixed native journey is frozen before Root integrates it. Source authors do not
execute tools; Root is the sole heavy worker. Actual commands, versions, failures,
costs and limitations belong in the later qualification report.

## Owner-approved budget revision2

At2026-10-30 16:20 UTC the owner answered **"Approve one bounded run"** to the
explicit PR286 proposal: one corrected six-capture native attempt with a40MiB
browser base and648MiB joint ceiling, each8MiB above the original limits, keeping
all failed evidence and the same20MiB packet reservation. This is recorded in
[#30](https://github.com/OptimumAF/LocalLore/issues/30#issuecomment-6527673039).

The preceding32/640MiB browser contract is version1 history; its failed setup
packet and all measured costs remain unchanged. Future browser admission uses
version2: `version:2`, kind `d08_domain2_timeline_browser_budget_v2`, filename
`d08-domain2-timeline-browser-budget-v2-<HEAD>.json`, with the same eight field
names and closed source/target binding. Browser cumulative_limit_bytes is
679,477,248; new-base cap41,943,040. Existing no-argument paging stays version1
with its original64MiB packet/128MiB group/640MiB joint/512MiB external bound.

The command remains `--timeline-browser-v1`: it names the unchanged UI recipe,
six labels and report mode, not the resource record version. Browser packet and
expected reservation remain20MiB, app writer8MiB, product reserve16MiB, metadata
reserve1MiB, and original target baseline/2GiB growth stay. Old D05/D07 evidence
is still charged once in the joint total, never omitted or reset. A version1
browser budget cannot authorize this source's version2 run.

Independent revised FIRST, Root implementation/checks, source review and a fresh
inventory/canonical record must precede the one authorized application attempt.
No automatic second attempt, frozen cohort rerun, desktop control, model/device/
SDK/stopped OS probe, settings change or release follows from this decision.
Single-attempt authority remains coordinator policy; the record is not a
persistent general-purpose permission registry.

## Failed corrected attempt and source-only finalization correction

The single revision2 attempt executed on d29a7081 and failed after producing
the six planned native captures plus a failure capture. Its supervisor recorded
an application timeout, one returned stop, SIGTERM closure and sticky
`OwnedDrainUnknown`; normal restoration was correctly skipped. The permission
is consumed. Read-only observation of an absent recorded PID, no direct children
and no exact-profile WebView process does not establish retrospective tree
closure or reset that record. Further builds, tests and application launches
remain stopped pending a separate execution reconciliation decision.

The source-only correction keeps the six journeys, Rust oracle comparisons,
observer fences, all original checkpoint data and read-only action restrictions.
Normal navigation may perform the established native `capture_revoke` privacy
cleanup, as the accepted D05 journey already permits. Capture preview/save,
model loading, generation, author edits, forks and memory writes stay forbidden.

A narrow development-only finalization helper will reference each already
retained semantic checkpoint by its fixed label and scroll-observation count
instead of duplicating its geometry records in the final report. A successful
report requires all six ordered labels; a failed report may retain their ordered
prefix. Each checkpoint has at most16 observations, total at most96; success
requires exactly16 per checkpoint and96 total. Both compact
and formatted UTF8 encodings are bounded at256KiB before native report IPC;
Rust's existing independent formatted limit and artifact writer stay unchanged.
Checks, call metadata, font measurements and available Rust proofs remain in
the detailed report. This is a report representation change, not an omitted
journey check or a replacement for retained original observations.

Detailed report construction or its one `harness_finish` call may fail. In that
case the helper attempts exactly one fixed, small, synthetic failed report
through the same IPC, with a finite category and explicit unavailable details.
It must never turn a failed finalization into success, invent state proof, retry
an application or suppress failure of that fallback. The journey retains one
finalization promise across its normal and error paths: rejection of both calls
must not cause the outer catch to attempt a third native finish. Disposal can still fail or
stall; the outer deadline and unknown-lifetime guard remain authoritative.

Independent regression source freezes before producer changes. Its author and
the producer do not execute it while the stop applies. No further native run,
resource increase, process control or relaxation of the failed gate is included
in this source-only correction.

## Code-check/restoration reconciliation: approved, then storage failure

The proposed next admission is limited to bounded code checks and restoring
normal frontend/native products without launching the application. The old
failed attempt and unknown-lifetime record remain immutable. Immediately before
any execution, recheck exact owned executable/profile/PID absence, source/product
identity, remaining metadata reserve and fresh storage inventory. Any new unknown
lifetime, source/product ownership change or inventory failure stops later work.

Preserve the diagnostic frontend2,169,685B in the existing browser evidence base
and native44,007,424B as an ordinary byte copy in the existing owned Rust target
before restoration. A hardlink cannot protect against an in-place rewrite.
Charge the frontend to the unchanged8MiB source/40MiB browser caps, and the native
copy's full logical and additional physical allocation to the original2GiB
target-growth ceiling. Neither copy removes any earlier cost. Copies total less
than48MiB; existing16MiB product and1MiB metadata reserves stay charged.

At most512KiB additional combined encoded logs/reports/terminal records are
proposed within the remaining metadata reserve, with stdout and stderr each
bounded at64KiB per command. Root alone runs fixed source regressions, strict
TypeScript, formatting/equivalence checks, a normal frontend build and the
existing locked/offline normal native build. Preserve terminal records and any
expected baseline FAIL/UNRUN_SETUP classifications. Do not run the77-child
frontend suite, a browser, native application, Rust test binary, model, SDK,
device or stopped OS qualifier. A final normal build is recorded as unlaunched.

This reconciliation does not raise a cap, clear the historical latch,
certify prior tree closure, admit another native attempt or approve a merge.
The owner answered "Approve checks and restoration". Actual source checks pass,
but the normal build's post-inventory fails the original target-growth limit.
The private runner omitted the repository launcher's existing pinned build
settings and performed a broad default-debug rebuild. All outputs are retained.
The failed storage boundary stops further execution under that reconciliation.

## Prospective resource revision3: decision pending

Retaining the failed build leaves target growth3,774,894,212B against the failed
2GiB limit. The proposed prospective browser-only growth cap is4GiB, retaining
the original8,259,980,576B baseline and the historical failure. A256MiB cached-build
reservation forecasts total12,303,310,244B below baseline plus4GiB12,554,947,872B.
Reuse the repository launcher's existing one-job/no-incremental/no-debug/offline
settings; no fresh target, dependency download or discarded build output.

One further fixed six-capture attempt would also need a52MiB browser base and
660MiB joint ceiling, each12MiB above revision2. Preserve the same20MiB packet
reservation,8MiB native writer,8MiB source phase,16MiB products,1MiB metadata,
all failed packets/copies and all old D05/D07 costs. Existing no-argument paging
and frozen cohort limits are unchanged; no old failure becomes a pass.
Stored pre-final-record figures forecast browser50,650,015B and joint689,889,431B
after reserving the next20MiB packet; fresh admission must replace those stale
figures and retain space for later source/records. The target256MiB reservation
is a cached-build forecast. Inventory checks bracket each child and can detect a
build overrun only after allocation; they do not enforce an operating-system quota.

If explicitly approved, browser admission would use version3, kind
`d08_domain2_timeline_browser_budget_v3` and matching filename prefix, with the
same eight closed fields. Browser base limit54,525,952B; joint692,060,160B;
browser target-growth limit4,294,967,296B. The UI recipe/argument stays v1.
Independent revised source checks, source review and fresh source/product/owned
process/storage admission must precede exactly one application launch. Root must
inspect every resulting original image. Retain failures; stop on any new unknown
lifetime, storage or ownership failure. There is no automatic repeat or deletion.

This is a concrete resource proposal, **not authorization**. No version3 runtime
limit, canonical admission record, new code check/build or app execution is
implemented/admitted until the owner explicitly approves that separate scope.

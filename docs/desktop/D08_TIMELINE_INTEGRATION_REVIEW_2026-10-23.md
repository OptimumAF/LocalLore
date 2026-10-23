# D08 timeline integration source review, 2026-10-23

Refs #30 (D08.04 partial). Reviewer `/root/desktop_runtime_profile`, isolated
`review/d08-timeline-integration` / `source-timeline-integration-review`.
Claim [6372385019](https://github.com/OptimumAF/LocalLore/issues/30#issuecomment-6372385019).
This review covers the coordinator/other author's timeline UI integration; the
reviewer did not author its controller, decoder, panel, fixture or native journey.
It is a source review, not owner acceptance or full D08 qualification.

## Frozen source and checks

Reviewed all 14 changed files in `a13b80b..e2f7a772c09ed6dc7a22abb8f6223226b60853ca`
and the focused coordinator follow-up
`2214cfbc394897602cedd72989d88919b6de504a`. The latter replaces unsupported
width/height arguments with the existing fixed viewport presets, preserves bounded
string IPC errors in failure reports, and requires exactly two expected native
`Cancelled` errors initially and zero after process restart. It changes no
production timeline, scope, fixture or observer behavior.

Then reviewed the exact render-admission repair
`daaa012c4b8f9a3d12df609953a34535a5bed603`, after coordinator merge
`b836d6e` of accepted main `f5187b9`. The repair changes only the existing
native journey and launcher. The unrelated accepted curated integration is not
re-reviewed or qualified by this timeline report.

Also read the existing gameplay `Controller.resume`, `switchSession`,
`invalidate`, `refresh`, view/lens operations; Host durable branches/resume/open;
Store `branch_catalog`; native development checkpoint/viewport authorization;
and normal-frontend hook exclusion verification. AGENTS, README, issue workflow,
roadmap #3 and current #30 claims/evidence were read before review/edit.

Reviewer execution was limited to read-only Git/source/GitHub inspection and
`git diff a13b80b..e2f7a77 --check` (PASS). No reviewer Node/Rust compilation,
frontend tests, native application/WebView, model/worker, device, desktop
automation or screenshot operation occurred. The coordinator reserved native
execution and memory resources; no additional reviewer test suite is inferred.

## Boundary findings

No product correctness blocker was found in the reviewed source boundaries:

- `playView` still binds top-level and player state to the selected child scope
  and revision. Each inherited receipt keeps its original well-formed same-story
  request scope; each event must match that original request scope, with positive
  safe sequence no greater than the selected revision. Nothing rewrites parent
  receipts into child receipts. The presentation decoder intentionally does not
  recreate Rust's ancestry/replay authority: a fabricated same-story lineage from
  an untrusted replacement native Host is outside this shape decoder's claim.
- The timeline's native command is only the existing `branches { story }` port.
  Selection delegates a cloned active scope to the same `Controller.resume`
  adapter, which reuses existing-session switching and the shared Rust owner.
  Resume success is checked against the actual selected scope and play revision.
  No JS fork/replay, direct SQL, alternate save, generation request, author edit or
  inspection grant is added.
- Session, story, branch, revision, view, observer and persistence form the
  presentation identity. The gameplay subscription updates it before React
  observes controller state. Identity changes clear/hide the catalog and advance
  the response epoch; refresh ordering, hide and disposal also fence late replies.
  The panel independently refuses a mismatched supplied context. A completion of
  an already-admitted resume cannot relabel a newer timeline panel; its actual
  session operation remains governed by the gameplay controller's existing
  fences. Closing this panel does not claim to cancel that operation.
- The decoder admits bounded metadata only: exact catalog/row/scope keys,
  same-story IDs, safe nonnegative numbers, unique branches, coherent root/parent
  references, cycle/depth checks, at most 256 rows, 256-codepoint title, 60 KiB
  serialized catalog. It supports retained retired ancestors and valid nested
  prebirth forks. Rust's transaction/replay validates the actual histories and
  retention state; the UI does not infer eligibility from titles or prose.
- Retired, absent and current branches cannot dispatch a selection. Active
  selection uses authoritative resume, so a catalog is accurately labeled as a
  metadata snapshot rather than a guarantee of an unchanged saved head. Drafts
  stay explicitly uncommitted; fork/rewind/regeneration/correction are explicitly
  unavailable. React renders titles/IDs as escaped text.
- Lab/character selection affects the existing inspection path, not the new
  catalog/resume command payload. No new inference input, observer predicate or
  generation knowledge grant is introduced. Public story metadata is not
  represented as knowledge available to a character.
- The synthetic Store fixture exists only under Rust `dev-harness` plus trusted
  startup flags and is created before Host opening. It uses actual shared commit,
  fork and retirement operations, refuses reseeding an existing database, and
  exposes no renderer fixture path, SQL/code/shell or model command. Frontend
  journeys remain behind the compile-time development dynamic-import gate;
  normal verification adds the timeline's unique marker to hook exclusion checks.

## Native evidence admission gap: source repair reviewed

At `e2f7a7` and `2214cfb`, `timeline-native-journeys.ts`'s `capture()` records
`root.textContent` without requiring nonempty rendered timeline structure, and
ignores the checkpoint's `rendering` result. The existing native checkpoint
returns a successful bounded artifact response with a rendering-unavailable
category when image capture fails. `timeline-harness.mjs` counts PNGs but imposes
no minimum/expected capture count before emitting `passed: true`.

Consequently, controller assertions and the no-horizontal-overflow predicate
alone do not establish rendered UI: blank content can satisfy the overflow check,
and an unsupported capture path can produce a nominally passing summary without
native images. The final error-buffer gate catches recorded render exceptions,
but not every empty/absent UI or capture-unavailable outcome. This is a harness
evidence weakness, not demonstrated canonical-state or observer leakage.

Reported directly to the coordinator before publication. Recommended narrow
repair: require nonempty root text and the expected rendered saved-timeline
heading/list for catalog captures; require checkpoint
`rendering === "native-webview2"` for a cohort claiming native images. No new
command, arbitrary selector/file capability or desktop capture is needed.
Coordinator inspection of actual images can establish a particular cohort's
visible state, but should not be confused with this missing automated admission.

Coordinator repair `daaa012c` closes this source finding: every capture requires
nonempty root structure, the actual `Saved timelines` heading, exact catalog row
count and the selected branch's rendered selected label. Every checkpoint must
report `native-webview2`; the launcher requires exactly 11 initial and three
restart PNGs. Missing content/capture now fails the same actual journey. The
reviewer read this precise delta; no command, file/selector authority, endpoint
or gameplay behavior was added. Source finding resolved; strengthened execution
remains separately attributable below. No injected empty-render regression was
executed by the reviewer.

## Execution attribution and remaining gates

The author/coordinator reports 81 checks using actual frontend controllers and
decoder with a MOCK native gateway and inert React semantics. Those are not
native IPC or WebView tests. The coordinator reports the actual fixed Rust Store
fixture test passing after correcting its public event accessor and four literal
test-owned SQLite sidecar cleanup names; the prior DirectoryNotEmpty failure
occurred after semantic assertions and remains a separate failed run.

The coordinator's first actual native journey reached 31 assertions through the
observer check, then failed because its development viewport call used unsupported
arguments. It is not a completed native cohort. At `2214cfb`, the coordinator then
reports 36 distinct native assertions and 14 images passing across two processes.
That run's `sourceDirty: true` was attributed to an untracked generated permission
for an unrelated curated command in the shared target; it is retained as that
run's evidence, not relabeled as a clean or render-strengthened cohort. Accepted
main integration subsequently tracks the permission. At this report's freeze,
the coordinator reports the complete frontend verifier (including 81 MOCK
timeline checks and normal-hook exclusion) passing on `daaa012c` and is running
the strengthened native/unit/strict checks serially. Their final results and
actual image inspection belong in the coordinator's source-bound evidence.
This report does not convert source inspection, previous images or partial
execution into the strengthened native cohort's success.

No real-model inference, physical Android round trip, full offline/package gate,
committed-history editing, fork/correction UI, or full D08 acceptance is claimed.
The next runnable gate is completion of the coordinator's source-bound strengthened
native rerun and render inspection, then owner review and a focused partial PR.

## Actual image finding and title/draft repair addendum

After the initial report freeze, the coordinator inspected the old `2214cfb`
images and found a concrete visible defect: child/sibling sidebar session names
were `Lantern Quay`, although the actual story title was
`Synthetic saved timelines`. The existing resume lookup matched the full selected
scope against the workspace library's root-only entries, so a child missed its
story's title and took the unrelated hardcoded fallback. This finding comes from
the coordinator's actual image review, not reviewer native execution.

Reviewed coordinator source fixes
`8c7f7d3ad7314c0793af1f8345c55c1fa0725496` and
`f3947f788d0d71a6b5025fd230496cd07f87026a`. Story title lookup now matches story
ID and uses the honest generic `Saved story` fallback. The original branch-specific
saved-request fallback remains separately guarded by full scope equality. This
separation matters: the first title repair also accidentally made root draft
counts describe the child if its resume reply omitted drafts; the coordinator
caught that coupling and corrected it in `f3947f7` before final handoff.

The actual gameplay-controller MOCK test now supplies a root library entry with
its real synthetic title and three root drafts, resumes a child whose native
reply omits drafts, and asserts both the child's correct story title and absence
of a false saved-uncommitted-request notice. These are meaningful distinct
regressions: shared story title does not imply shared branch draft state.
Every native capture additionally checks the selected session's canonical story
title and rendered root text. The final source changes no request scope,
receipt, revision, observer, branch history or generation grant. Both repairs
are source-resolved; no further product boundary finding was found.

The coordinator reports the title regression RED then GREEN, root-draft coupling
regression RED then GREEN, all 83 timeline MOCK checks and the strict frontend
verifier/normal-hook exclusion PASS. Native Rust source is unchanged by the two
title commits; the coordinator reports default 54 tests, development 57 plus two
contract tests, one existing ignore, and strict checks passing on the preceding
render-strengthened source. At this addendum's freeze the final title-aware native
cohort is running, so no later cohort result is invented here. The reviewer ran
only exact source diff reads and `git diff daaa012c..f3947f7 --check` (PASS), with
no additional build or native process.

Addendum claim
[6372508863](https://github.com/OptimumAF/LocalLore/issues/30#issuecomment-6372508863)
owns this report only. Final actual native assertions, images, process restart,
source cleanliness and artifact hashes remain coordinator evidence on the final
source. Full D08, real inference, Android and release gates remain unclaimed.

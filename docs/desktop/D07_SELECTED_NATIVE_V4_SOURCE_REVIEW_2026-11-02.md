# Native selected artifact4 source review

Refs #29 D07.06 supporting D07.03/.07; #28 D06.05; #21.
**Source implemented; UNCOMPILED/UNRUN. No native or desktop acceptance.**

## Behavior and boundary

The accepted selected3/source4 codec is scripted-only. The new shared
`scene_v4::selected_v4` codec represents native-configured selected reruns as a
separate selected artifact4, retaining source protocol4. It reconstructs each
arm's actual source prefix and passes the existing native workflow's factory
to the actual Scene4 turn path. It adds no runtime, provider, storage or memory
implementation. Existing selected1/2/3 behavior and native refusal stay intact.

Preparation retains an opaque locked source capability. Current-source and
full-manifest equality are required again at execution/resume; both arm budgets
are checked before reservation or target creation. The existing owner workflow
owns durable invocation admission, runtime startup and uncertain cleanup.
Completed current-source resume returns a recomputed read-only report even at
the invocation cap. Receipt recovery preserves actual canonical provenance and
does not invent native roles, construction/privacy evidence or quality results.

The new read capability revalidates the actual selected files, checkpoints and
accounting. Actor metadata excludes requests, outcomes, prose and private report
data. Query2 and receipt/capture/diagnostic privileges retain their existing
early access checks. No read grants execution or changes character knowledge.
Historical native-shaped records can be inspected without the local-model
feature or today's native profile; they do not grant fresh execution authority.

This shared slice adds **no desktop dispatch, native IPC, frontend control or
CLI execution**. Those consumers must distinguish source protocol and lane,
then decode recorded selected artifact4 separately. Source4 scripted reruns stay
selected3. Selected4 keeps diagnostics disabled; the full-run narration companion
is not claimed for selected runs. Author remains disabled and human quality
remains unreviewed/false in these reports.

## Frozen source and review order

Accepted base: `db2c23d09c1fd97986b2f58e1a19ac4de1ceb405`.
Branch: `prep/scene-selected-native-v4`.

1. Contract frozen at `0e63872c`, clarified at `b4344405`.
2. Independent original12 FIRST groups authored at
   `ebbbf13f0c2dbd549f08887c083c0ba9f08e111f`, integrated at `73fbff5f`.
3. Feature-independent recorded-read coverage required at `006049c7`;
   additive N13 authored at `35370ca6babbbe504ac22f5036ccf6e906744a12`,
   integrated at `aae46e6b3a09e8f6c81dc2a0b59d2541cc8dfe29`.
4. Producer and reader implemented at
   `be9e406d435c4cfcaad480278dcbeedff9642b5b`, after all13 groups were frozen.

All1,153 FIRST source lines are unchanged since `aae46e6b`. The groups cover
prepare ordering and feature refusal, closed manifests/cross-codec denial,
paired and genuinely divergent rollout prefixes, locks/freshness/disjoint
paths, both-arm budget refusal, reserve-once/cancellation, genuine scripted
receipt recovery, completed resume at cap, read grants/Query2/privacy/bounds
and historical data-only reads in both feature configurations. Their private
source drivers use the actual Core/Store/Scene4 path. Scripted imports prove
recovery only; the empty native-shaped N13 fixture proves codec compatibility
only. Neither proves native generation, authenticated origin or story quality.

Independent source review of the producer/read API found no actionable
API/privacy/cross-codec/FIRST-constructibility defect by inspection. It checked
all524 producer and195 reader lines and current reference helpers. This is a
model source review, not compiled evidence or human acceptance. The separate
lifecycle/accounting source review also found no concrete new failure by
inspection. It traced entry-origin clocks into both ledgers, preflight before
reserve/target mutation, reserve at most once, the supplied native factory,
receipt recovery and existing uncertain-owner retention without publication.

## Checks actually performed

In the physical D: checkout, with process-local TEMP/TMP on D:, using
Git `2.33.0.windows.2`:

```text
git diff --cached --check
git diff --name-status db2c23d09c1fd97986b2f58e1a19ac4de1ceb405 HEAD
git diff --exit-code aae46e6b3a09e8f6c81dc2a0b59d2541cc8dfe29 HEAD -- crates/locallore-eval/src/local_lane/comparison/scene_v4/selected_v4/first_review_tests.rs
git ls-remote --heads origin main prep/scene-selected-native-v4
```

Whitespace and unchanged-FIRST comparisons passed. Explicit scope inspection
confirmed only the new codec/reader/FIRST/docs, module registration/header and
EXACTLY two private visibility changes in selected3; its helper bodies and old
readers/tests are unchanged. Remote main still resolved to the accepted base
at the read. These commands are source/Git checks, not Rust verification.

No formatter, parser, compiler, test binary, SDK/library observation, app,
worker, model, frontend/browser, native IPC/WebView, render, Android/device or
OS qualification ran. No synthetic fixture/build/cache/check-evidence output
was generated by this source phase. No old finite grant was reused.

## Next checks and remaining gates

Before running code, admit exact tools/locked dependencies, retained fixture
and log bounds and build growth against the original target baseline. The
existing padding PR's pending read-only grant cannot authorize these checks.
The crate is a separate Cargo workspace (`locallore-eval`, Rust requirement
1.93). The selected4 FIRST module is registered under `src/lib.rs` through
`local_lane::comparison::scene_v4::selected_v4`. The CLI in `src/main.rs` calls
the library, so a binary-only test command does not select these unit tests.

Planned checks, **not run**, after that admission:

* Compile/test both feature configurations. Expect 2 applicable FIRST groups
  without local-model and 13 with it, reporting actual names and counts.
  Use `--lib` with filter `local_lane::comparison::scene_v4::selected_v4::first_review_tests`.
  Run fixtures serially with offline/locked dependencies and admitted physical
  D: output/temp locations.
* Run affected selected3/source4 and selected1/2 compatibility plus shared
  native workflow/startup/ownership/accounting suites at the tested revision.
  Fixed protocol-owner tests prove cleanup, not successful native generation.
* Perform appropriate formatting/static checks and integrated host/native/
  frontend/Android compatibility checks as consumers are added. Record actual
  commands, tools, failures, retained outputs and results before any merge.
* Separately verify consumer consent/leases/epochs/idempotency/lost-ACK and
  read dispatch, then admitted actual model/native IPC/application-owned render
  journeys and human quality. No desktop UI or phone result follows from
  this source-only PR.

The [frozen contract](D07_SELECTED_NATIVE_V4_CONTRACT_2026-11-02.md) retains
the exact API/projections, ownership limits and evidence distinctions. D07,
D06 and the desktop epic remain open. Do not merge this uncompiled slice.

# Protocol 4 native reader: independent first test freeze

2026-10-27. D07.06 supporting D04.04 (#29/#25).
Baseline: `98d80d9e82cf9929bab1ffd20440cc7fa48eebcd`.
**SOURCE ONLY, UNCOMPILED/UNRUN.** These are native Rust manager/Core tests;
they do not execute the desktop application, native IPC, picker dialog, WebView,
model, device, socket or provider runtime. They do execute the actual deterministic
scripted producer/Host/Store only when Root later runs them. No passing result or
behavioral failure has occurred at this freeze.

## Exact ownership and interface

Branch `test/d07-v4-native-reader`, explicitly reassigned clean
`source-d07-comparison-native-ui` checkout. Preserve the public PR238 branch and
all unrelated worktrees. Claim #29 comment6454121508.

Own only new `apps/desktop/src-tauri/src/evaluation/comparison/scene_read_review.rs`,
its two-line `#[cfg(test)]` module registration in `comparison.rs`, and this new
document. No existing assertion, runtime/manager implementation, Eval facade,
schema, provider, model configuration, frontend, package feature or default is
changed. Root owns production and all execution. No new test hook is introduced.

Tests call the existing `EvaluationManager::{comparison_pick,comparison_status,
comparison_source,comparison_summary,comparison_evidence,comparison_close}`,
existing `WindowLease` begin/dispatch/invalidate/finish-close lifecycle and
existing retire/drain. Picker callbacks return actual private fixture paths;
this substitutes for affirmative native selection, not a real OS-picker test.
Reader grants remain privately minted by existing native worker code after
successful source validation. A renderer JSON flag never constructs a grant.

The actual Core V4 facade is already implemented at the baseline. Native
`OpenedRead` still has only V2/V3, so actual V4 picker-open positives currently
have an existing callable path to meaningful failure before `phase:ready`.
Root must first compile/run the unchanged freeze to record the actual baseline;
missing imports/type errors or fixture calibration are build/setup issues, never
behavior RED. This document predicts no measured result or failure count.

## Smallest production handoff after baseline

Add `OpenedRead::V4(scene_v4::desktop_api::OpenedComparison)` inside the existing
`evaluation/comparison.rs`; dispatch open/summary/evidence through the established
Core facade. Add V4 to the opaque `SelectedSource::protocol_version` match only to
report source identity. Do not add a Protocol4 execution plan or runtime lane.
Keep existing valid V2/V3 routing and original invalid-source failure categories,
same worker, pins, run lock, operation ID, native picker grant, client/token/
binding/window/epoch fences, TTL900s/MAX_CLIENTS4 and existing bounded responses.

Do not infer native admission from a serialized report, create an Engine/Receipt
from JSON or replace the Core facade with a tolerant metadata loader. Cached
summary remains explicitly the retained validated snapshot. Fresh evidence must
still revalidate the current manifest/checkpoint, actual Store receipt/edges,
capture/recording/raw evidence and Rust Query2 observer filtering. A file edit
cannot pair new evidence with an old binding. Failed evidence does not silently
rewrite the saved source or mint a fresh reader token.

The new source4 identity is deliberately unsupported by existing selected
`versioned::Protocol::from_source`: keep source2→selected1/source3→selected2 only.
`selected_prepare` may transfer/revoke its old read capability under existing
ownership rules, but must fail `NativeUnavailable` before a prepared plan,
consent callback, selected target or model reservation/assets. Both scripted and
approved-native lane requests refuse; no false claim that scripted source4 is a
legacy source3. Selected3/source4 has its own future freeze and owner.

## Eight finite oracles

1. **Actual V4 source/summary/evidence.** Run the real V4 scripted one-scene
   producer, then the existing native manager picker/worker. Source protocol4,
   binding/rows, complete report and unavailable marker survive losslessly;
   read-only true/execution false. Compare Player, Mira and Sable history pages
   against independently queried actual Core Store cuts at the receipt edge.
   Mira and remote Sable must have distinct rows for the first private dialogue;
   the fixed secret sentinel remains absent. Raw receipt/capture/outputs refuse
   all actor lenses. Omniscient gets the actual Store receipt and retained raw
   diagnostics; its receipt hash is from typed Store serialization, never parsed
   JSON field ordering. Every evidence envelope has generation_grant false.
2. **Version/old-token controls.** Open V4, close, then actual V3 and V2 reports
   through the same manager/window with fresh clients. Keep each protocol typed,
   old tokens unknown and complete saved source inventories unchanged.
3. **Native consent/picker cancellation.** Denied native grant never invokes the
   picker callback or changes disk; cancelled picker mints no binding/token and
   can be closed. This is native API permission plumbing, not real dialog UI.
4. **Held picker close/retirement.** Hold the existing picker callback using
   bounded channels, close or retire the window before it returns. Late selection
   cannot publish/retain a token; fresh reopening works; old epoch stays closed.
5. **Window/binding/source fences.** Equal-numbered foreign window cannot read,
   close or inspect a token. Wrong binding maps to existing bounded integrity
   category; oversized row ID refuses before dispatch. After a private manifest
   mutation, actor raw refusal still precedes even malformed token/binding/source
   probes; actual evidence refuses, cached summary stays explicitly immutable,
   and restoring the synthetic bytes recovers without canonical repair.
6. **Completed evidence publication race.** Use the existing test-only
   `before_publish` barrier after the actual V4 evidence worker returns. Close or
   retire before publication; the actual caller receives Closed and no old
   capability survives. This tests completed-result retirement, not fabricated
   delayed evidence or an added debug pipeline.
7. **Bounded source failure.** Oversized actual fixture manifest yields failed
   EvaluationBudget with no reader grant/binding/token, and no source repair.
   This verifies existing size/error propagation, not full disk/resource stress.
8. **Unsupported selected admission.** For both existing requested lanes, retain
   an actual in-memory ModelManager reservation, attempt selected_prepare from a
   successfully opened actual V4 source, require NativeUnavailable (not model
   busy), zero consent calls, no plan/run IDs/tokens, no target directory,
   unchanged manager/model state and released source lock. Releasing the held
   reservation uses its existing RAII owner. No assets or runtime are opened;
   this is a refusal check, not selected execution or native cleanup qualification.

## Fixture and evidence boundaries

One `OnceLock` retains three **closed immutable producer templates**, actual
scripted V2/V3/V4 one-scene outputs (12 rows each). No reader is ever opened on
a template. Every test/open/mutation uses a private ordinary byte copy, preserving
the complete source tree including `run.lock`. Copying never uses hard links,
symlinks, shared mutable sources or cross-workspace paths. Bounded inventories
refuse links/reparse points and check depth8,4096 entries,8 MiB/file and64 MiB
total. Read inventories only after retained readers are closed/released.
Fixtures remain local under task TEMP; no real story/private model is imported
and no recursive cleanup of computed roots is introduced.

Existing native fixture scheduling bounds remain30 seconds for status/held
selection and5 seconds for entry observation; these are test scheduling limits,
not enlarged production budgets. Existing barrier hooks only control publication.
There is no ignored-I/O path, raw-file exclusion, retry loop added to hide an
error, serial-CI policy change or existing test/assertion weakening. The baseline
filter explicitly serializes this small measured cohort for attribution while
inside-test concurrent lifecycle/worker races remain intact; default parallel
compatibility remains a separate appropriate regression check.

## Root-owned execution and later gates

Reproduce from repository root using the existing exact-lock offline cache,
ordinary task-owned target/TEMP and one heavy slot:

```powershell
cargo test --manifest-path apps/desktop/src-tauri/Cargo.toml --bin locallore-desktop-spike --locked --offline --jobs 1 --target-dir $ownedTarget evaluation::comparison::scene_read_review:: -- --nocapture --test-threads=1
```

Author runs no Cargo/Node/formatter/build/test/runtime/app/desktop/device/model
command. Author checks only source/API/Git/whitespace/hashes. Root records exact
test count, baseline source/failure, any separate calibration, implementation
source and unchanged-oracle GREEN, then appropriate old native V2/V3/selected
regressions, strict lint/format, frontend/build and default parallel controls.

The frontend decoder freeze, native command wiring and actual same-controller
Story Lab journeys are separately owned. Rust manager tests are not Tauri IPC,
OS-picker, native WebView rendering, model comparison, offline/security,
physical-phone or human-quality qualification. Keep synthetic vs native model
metadata honest, Domain2/unavailable/recovered/privacy cause fields unchanged,
human0/not_reviewed/qualityfalse and original **needs improvement** assessment.
No task checkbox, merge, release or settings change follows from this freeze.

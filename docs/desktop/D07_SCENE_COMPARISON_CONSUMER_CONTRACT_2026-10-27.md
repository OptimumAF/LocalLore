# Protocol 4 comparison inspection consumer contract

Date: 2026-10-27. Tasks: D07.06, supporting D04.04 (#29/#25).
Source inspected: `903a2940b494c44110aaa670295b8c28594cfc01`.
This is a proposed implementation contract and an independent source-only test
freeze, **UNCOMPILED/UNRUN**. It does not implement or qualify a reader, desktop
UI, native execution, model cohort, or selected-case runtime. A missing proposed
API is a compilation prerequisite, not behavioral RED.

## Observed seams and the smallest slice

The actual Protocol 4 writer/strict cold inspector exists in
`crates/locallore-eval/src/local_lane/comparison/scene_v4.rs`:
`run_comparison`, feature-gated `run_native_comparison`, `inspect_comparison`.
Its closed report/descriptor types live in `memory_comparison_v4.rs`.
It has no public retained desktop reader or selected-case adapter at this source.

Reuse the existing Story Lab reader lifecycle; add one protocol adapter. Do not
create another runtime, context compiler, report importer, canonical store, or
frontend authority. Opening an existing native-selected directory is sufficient
for the first slice. Leave managed comparison launch defaults and Protocol 3
producer commands unchanged. A displayed Protocol 4 report never authorizes
execution, creates a story, repairs its files, or upgrades an old report.

| Existing owner/path | Required additive change |
| --- | --- |
| `scene_v4.rs` + new `scene_v4/desktop_api.rs` | Export the retained read-only facade below; adapt actual `Manifest`/`StoredTurn4`/`load_turn4`/`load_turns4` only. |
| `comparison/desktop_api.rs` | Reuse `RowId`, `Arm`, `Edge`, `EvidenceRequest`, early `check_access`, private `EvidenceTurn`, actual `render_evidence_view`. No alternate report-to-engine conversion. |
| `apps/desktop/src-tauri/src/evaluation/comparison.rs` | Add `OpenedRead::V4` and dispatch within the existing capability/grant/lease lifecycle. |
| `apps/desktop/ui/comparison-reader-model.ts` | Add a distinct closed version-4 report/row/descriptor decoder and source union member. |
| `apps/desktop/ui/ComparisonReaderPanel.tsx` | Explicit version-4 labels/statuses and honest unavailable selected execution. |
| Existing `comparison-reader-controller.ts` | Retain the same native command path, client/binding/context fences, retirement and close behavior. No parallel reader controller. |

## Frozen first public reader seam

Proposed module: `locallore_eval::local_lane::comparison::scene_v4::desktop_api`.

```rust
pub struct OpenedComparison { /* private retained authority; no Serde/constructor */ }
pub fn open_read_only(dir: &Path) -> Result<OpenedComparison, String>;
pub fn summary(run: &OpenedComparison, native_inspection_granted: bool)
    -> Result<serde_json::Value, String>;
pub fn evidence(run: &OpenedComparison, expected_binding: &str,
    row: &comparison::desktop_api::RowId,
    request: comparison::desktop_api::EvidenceRequest,
    native_inspection_granted: bool) -> Result<serde_json::Value, String>;
```

Follow `literal_v3/desktop_api.rs` rather than extracting a new general reader
framework. Retain validated manifest/key/turns, immutable snapshot, ordinary-path
ancestor/arm pins and existing exclusive read-opened `run.lock`. Never create,
write or truncate a missing lock. Keep current entry/path/budget checks: at most
512 root entries, only the existing recognized arm/reference directories,
2 MiB summary and 256 KiB evidence. Symlinks/reparse points and unsupported
directories remain refused by the existing ordinary/pin checks.

Summary envelope is the existing version-1 envelope with `protocol_version:4`,
the **actual** complete version-4 report and normalized `rows`, `read_only:true`,
`execution_available:false`, and
`unavailable:["selected_protocol4_rerun_not_implemented"]`.
The latter is the new facade's capability limit, not a rewrite of the producer's
retained historical report limitations. Report fields remain unchanged.

Normalized rows keep existing exact shape:

```text
row: {turn, arm: left|right}
source: {status: available, scope, before_head, after_head, input_semantic_sha256}
capture_available, receipt_available, recording_available, unavailable
```

Iterate actual checkpoints in turn-index/physical-arm order, at most 48 rows.
Compare each row with the actual inspector report in that same order; reject any
unmatched, duplicated or extra row. Preserve actual request scope/edges/hash.
Availability is artifact/phase presence, not a construction/privacy/quality pass.
Retain `capture_unavailable`, `recording_unavailable`, `no_accepted_receipt` reasons
where applicable. Do not fill missing artifacts or infer an accepted receipt.

Binding is SHA-256 of compact JSON produced by the existing `encode(json!({
"manifest": typed_manifest, "report": actual_report, "rows": normalized_rows
}))` convention. Do not hash only the report, only its current head, pretty JSON,
or a differently ordered raw-file serialization. Source/suite/version/prefix and
descriptor checks stay in the actual V4 loader/inspector. A valid historical read
can show `source_matches:false`; that does not permit resume or selected execution.

`summary(false)` returns `Forbidden`. `summary(true)` returns the retained immutable
snapshot, explicitly not live status or a new source-integrity claim.
Before evidence binding/row/source probes, reuse `check_access`: native grant is
mandatory and raw receipt/capture/outputs require Omniscient. Actor raw requests
return `Forbidden` even for wrong binding/unknown row/corrupt source. Query views
remain actual Rust Query2 observer filtering, not raw data filtered in TypeScript.

Evidence must re-read/validate the manifest and compare it with the retained one;
reload the exact actual checkpoint against its actual Store database and compare
the complete loaded checkpoint with the retained checkpoint. Then borrow a
private `EvidenceTurn` into the existing renderer. Keep actual before/after Store
prefix checks, receipt/capture/recording/raw hash checks and bounded output. Return
the existing envelope with exact binding/row/scope/heads/observer/edge,
`read_only:true`, `generation_grant:false`. Hash consistency is not authentication
of provider execution or evidence origin. Do not deserialize an accepted Receipt.

## Native and frontend integration boundaries

`evaluation/comparison.rs::OpenedRead` currently has V2/V3. Add V4 without changing
valid V2/V3 dispatch or their existing error-category contract. A renderer version
number is not a trusted protocol selector: the chosen Core adapter must validate
the actual directory manifest and source. Never swallow a corrupted V4 source and
return a fabricated legacy envelope. Keep the same private `ReaderGrant`, picker,
epoch/client/token/binding checks, close ownership, transfer/drop order, TTL900s,
MAX_CLIENTS4 and existing polling budgets. No command accepts arbitrary evidence
paths, writes, native launch flags, model assets, policies or observer grants.

`checkedReaderSource`/`checkedReaderSummary` currently admit only versions2/3.
Add a version4 discriminant and a separate `ComparisonTurnV4`; it cannot inherit
the V2 retrieval fields via the V3 type. Do not coerce V4 to V3 or synthesize
missing retrieval/literal metrics. Use existing bounded descriptor-first JSON
copying/exact-key helpers. Unknown/future fields, accessor/prototype payloads,
wrong/null/missing required fields, unsafe numbers and oversized values refuse.

Decode exactly the Rust V4 schema: the descriptor's 15 fields include both schema
IDs, forwarded-budget/frame/capture-gate versions, exact arm-specific tuple and
required nullable context/compiler/literal fields. Left is `literal_scene_v1`,
right is `relevant_memory_scene_v1`. Use new 2.10/2.9 scene prompts and grounded
prose2.4; do not relabel accepted 2.1–2.8 or Protocol3 IDs. The frontend checks the
closed wire construction, not Engine gameplay/tuple acceptance or frame hashes.

Carry all actual V4 report and row fields losslessly, particularly source/hash
identity, `construction_matches`, `construction_evidence_status`/reason,
nullable narrator prompt/schema/frame/actual-receipt hashes,
`privacy_evidence_status`, recovered/roles-known flags, failure causes,
`source_bound_committed_rows`, setup/load evidence, unavailable and limitations.
Missing nullable fields are not equivalent to required explicit nulls. Keep exact
report/row descriptor equality, report/source protocol agreement, row ordering,
scope/edges/input fingerprint and evidence-envelope binding checks.

Panel labels must branch on protocol4, not merely `"construction" in turn` or
the old `literal_player_v1` arm string. Display “Literal scene” and “Relevant
memory scene”, and “Committed narrator input checked” only for
`validated_committed_scene_narrator_v1`. Other construction statuses are guard,
dependency or unavailable, with the actual reason. This checks fresh committed
Domain1 narrator inputs against Store prefix/receipt; Domain2, missing/recovered
calls/captures, failed or cancelled rows remain unavailable when the producer
says so. It is not Director/compiler/raw-output/provider-origin authentication.

`checked_finite_sentinels` describes a finite diagnostic, never universal privacy.
Retain violation and evidence-unavailable cause tags separately even when both
public privacy statuses are unavailable. A noncommitted row can retain an actual
observed violation without a receipt; absence of a receipt is not a privacy pass.
Keep synthetic scripted vs actual native lane labels, human0/not_reviewed,
qualityfalse and original eight-sample **needs improvement** visible and unchanged.
Opening native-produced metadata is not a new model invocation or human review.
Omniscient inspection does not modify character knowledge or generation context.

## Selected-case ownership is a separate next slice

`evaluation/selected/versioned.rs::Protocol::from_source` intentionally supports
source2→selected1 and source3→selected2 only. Do not map source4 to selected2,
copy a V4 descriptor into a V3 plan, or derive execution authority from read JSON.
The first read-only slice must explicitly refuse V4 selected admission before any
reservation/model/Store write, while leaving old selected1/2 behavior unchanged.
Retaining a V4 reader must not break older readers' actual transfer/drain fences.

A later independent freeze can add `scene_v4/selected_v3.rs` and native typed
`Protocol::V3`/`Plan::V3`, selected-version3/source-protocol4. It must bind the
actual opaque newly prepared source, both V4 descriptors, full exact selection,
intent, lane/profile, source/suite/reference hashes with required nulls, both
source request/prefix fingerprints and new selected manifest's own binding. Reuse
existing selected intent/selection types, preparation/refresh/consume semantics,
consent leases, `SelectedNativeReservation`, watchdog/checkpoint-settle/runtime
ownership and close/drain rules. Its output needs its own actual strict inspector
and UI version decoder; no selected schema/plan/runtime is created by this contract.

## Independent frozen tests and later acceptance

New `crates/locallore-eval/tests/scene_comparison_reader_v4.rs` contains four public
facade oracles: actual scripted one-scene producer → lossless/hash-bound read-only
snapshot and cold reopen; shared early access/actual Query2 edges/actual Store
receipt; changed manifest refuses evidence/open without repair while cached
summary stays explicitly immutable; actual Protocol3/V4 mutual reader refusal.
Every live reader uses a private ordinary byte copy of one closed immutable
producer template; include every byte including `run.lock` after reader drop.
No shared live reader fixture, ignored I/O, shortened inventory, relaxed assertion,
new retry/budget or test-suite serialization workaround. These tests require the
new API, so at this freeze **no executed failure/pass or compilation is claimed**.

Root owns implementation and first compilation/calibration; preserve original
assertions and label setup corrections separately from behavioral failures.
Proposed command after implementation:
`cargo test -p locallore-eval --test scene_comparison_reader_v4`.
Run existing V2/V3/V4 reader/producer/selected regressions and appropriate Clippy,
native and frontend checks. Then independently freeze actual frontend decoder,
native admission/lifecycle and same-controller Story Lab inspection journeys:
old2/3 positive controls, V4 exact/null/hash/status preservation, future-field
refusal, cold reopen, stale lens/session/binding retirement, cancel/close/transfer,
actor raw refusals and actual Query2 observer isolation. Inspect application-owned
renders and bounded frontend/native errors without desktop control. Headless fake
DTO tests, Rust reader tests and actual native IPC/WebView execution are separate
evidence classes. No new model cohort or human-quality acceptance follows from them.

No production edits or execution accompany this freeze. Next runnable task is
Root's data-only V4 Core reader implementation against these four tests, followed
by the typed native/UI read-only slice. Selected3/source4 and new model/human
qualification remain separate gates; dependencies PR232/237 are still draft.

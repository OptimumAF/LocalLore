# D06 native passive turn debugger

Refs #28 D06.01/.02/.03/.05/.06/.07, **partial UI integration, in_review**.
Claims [6358693219](https://github.com/OptimumAF/LocalLore/issues/28#issuecomment-6358693219)
and [6358713895](https://github.com/OptimumAF/LocalLore/issues/28#issuecomment-6358713895).
The shared [Host trace API](D06_HOST_2026-10-22.md) and
[publication](D06_SHARED_PUBLICATION.md) remain the only capture authority.
This debugger does not implement the full D06 exit gate.

## Product behavior and boundaries

Turn debugger opens a restrained metadata workspace alongside ordinary Play.
The heading identifies the current inspection lens, authoritative reply head
and captured base revision separately. Before a valid reply it says loaded head.
Capture defaults off; opening the debugger never opts in. Enable metadata,
Clear window traces and Disable & delete act on this window's entire Host.
The scope is explicit, including the fact that clear affects that window's trace
ring rather than deleting a canonical story or receipt.

Attempts retain their original observer, turn and attempt ID. A stage table
shows only recorded intervals, outcomes, fixed error categories and counts.
Null token counts say Not reported, and available counts preserve measured or
estimated labels. Zero counts are displayed as reported, without claiming a
retrieval exclusion count or a measured model context. Missing stage kinds and
missing runtime/prompt hashes are explicit; a ready candidate is not a commit.

A matching Player-view canonical receipt can be opened in D05's historical
before/after and provenance workspace. The link requires exact turn, scope and
base revision; narration remains separate display evidence. Failed/pending
attempts have no accepted-receipt claim. A character lens never relabels a player
attempt, and an omniscient Lab read retains its original player identity. Existing
Story Lab acknowledgement and the native Host grant rules are unchanged.

The strict decoder verifies the bounded versioned wrapper, exact head/scope/base/
observer, attempt identities, typed stages/outcomes, safe counts and known
provenance shapes before rendering. Unknown payload fields, foreign identity,
arbitrary labels/paths and wrong head reject as Wire. No private-page trace cache
is kept. Lens, story, session, head, hide and deletion changes synchronously fence
old replies. Controls are serialized, and diagnostic read failures stay inside
debugger state. Optional automatic reads do not delay gameplay refresh completion.

The existing API captures only bounded metadata. Selected context records, ranks,
omission reasons, raw proposals/prompts/model output, full capture, trace export,
summary maintenance, pause/step and generation rerun are explicitly unavailable.
The UI does not infer hidden reasoning, a retrieval miss, a modified operation,
rule IDs or stale-summary causes from absent data. At most 32 attempts, 24 stages
per attempt and 64 KiB per reply are retained in Host memory. Closing/reopening a
session makes its old owner traces unreadable; disable/clear/restart or eviction
can remove metadata. It is not stored in saves or normal story exports and is not
reconstructed from history.

## Final actual native evidence

Clean tested source **`dad1c022c0868c752324564240ade904b7eaefc7`** on
`impl/d06-desktop-debugger` includes accepted main `ac7fe2c` (shared trace,
M07 production context/borrowed eligibility and D09 workflow/package work).
The D09-only merge was checked to preserve app/core/native/manifests exactly.
Net implementation changes are confined to 14 desktop app files; no shared
Host/play/trace/store/runtime/schema/generated-type change was authored here.
Accepted model lifecycle, worker staging/journey pins, ModelPanel wording,
terminal model-refresh logic and existing inspector checks are preserved.

The definitive real frontend/Controller/native IPC journey passed **74 distinct
assertions, 12 app-owned WebView2 PNG captures and actual executable restart**.
It uses a fresh synthetic SQLite workspace and the explicitly labelled typed
fake inference provider. No real model was loaded or called. The typed fake path
records its actual candidate/publication/commit intervals; it does not invent
director/retrieval/narrator stages that this path did not capture.

Artifact suffix:
`desktop-debugger-artifacts/trace-native-a08474e8-15f8-43df-b8ab-72c60a1ed591`.
Summary SHA256:
`6f534fb17149a8966a85275afeb202263dcad81b49e3b1c330f2872dfe4532b7`.
[Committed evidence](D06_NATIVE_EVIDENCE_2026-10-22.json) includes the synthetic
reports, source/frontend/native binary hashes, capture hashes, normalized source
hashes, accepted-main preservation checks and exact regression artifact summaries.
Raw PNGs, SQLite files, logs and WebView profiles remain local/ignored.

Cases cover explicit enable/default disable, real committed span after lost
acknowledgement, exact receipt/D05 linkage, observed fake Agency failure, ready
uncommitted candidate, pending cancellation, character isolation, original
observer in Lab, external stale head, session/late reply isolation, read/clear/
disable nonmutation and restart without reconstructed traces. Submission and
live-worker counts stay unchanged during metadata reads. Canonical receipt/state
snapshots remain unchanged by inspection and deletion controls.

Final context, committed-stage and narrow-stage images were inspected with
view_image; earlier integrated failed/lens images were also inspected. The
original observer/base/head, actual fixed category, separate canonical receipt
and unavailable evidence labels are legible. The narrow 150% text capture uses
retained stage rows rather than an empty panel or long sidebar. All 12 captures
assert both document and nested debugger overflow bounds. These are app-owned
CapturePreview images; no desktop screenshot/input/window activation was used.

## Review corrections and regression attribution

An early fixture expected Ability for a fake provider that changed a typed Wait
into an invented ability. The actual Engine correctly rejects that intent change
as Agency; the fixture now asserts the observed category, with no core relaxation.
The first rendered table inherited three-column widths and squeezed its fourth
column. Debugger-specific widths and nested-overflow assertions corrected it.
Another fixture assumed a new pending attempt would replace a user's selected
failed attempt; it now explicitly selects the pending turn through the same
controller. Fixed holds release on failure. The one hung failed app child was
terminated only after checking its exact task-owned executable and launcher PID;
all failed diagnostic folders remain local.

Source review then found a delayed receipt link could overwrite a newer same-
session D05 search/boundary/lens after its opening query completed. The final
helper checks session, scope epoch, loaded head, view/lens and its exact query
epoch after awaiting. A controlled actual-controller test holds the query, changes
the user's search/historical boundary or Player-to-Mira lens/filter, then releases
it; no stale turn-diff query is dispatched. A separate held metadata read proves
ordinary gameplay refresh completes without waiting for diagnostic IPC.

The repaired source reran the native debugger **74/12** and D05 inspector
**93/14**, both with actual restart. Earlier clean `2b2b7ab` integrated-source
regressions also passed: legacy native **163/21**, headless **163/21**, durable
**33/11 captures**, export **36/14 captures/4 publications**. The final change
after that source is only the navigation guard and its controller test; app-native
and shared code are identical. D09 added only workflow/scripts/docs. Those
unaffected legacy suites were not falsely relabelled as final-head reruns.

At `2b2b7ab`, default native tests passed **17** plus one ignored in that suite;
development tests passed **19** plus the same ignored test and **2** harness
wrappers. The privilege-dependent reparse case was explicitly run and passed
**1**. Both strict all-target native Clippy configurations and rustfmt passed.
Their source applies unchanged to the final native/shared tree. Final frontend
checks, Prettier, rustfmt and default native build pass at `dad1c02`. WebView
shutdown emitted class-unregister warnings; bounded reports and successful exits
are recorded separately from those warnings.

## Commands and remaining gates

All new build/temp/artifact outputs use the task-owned D directory, debug/test
debug information is disabled, incremental compilation is off and dependencies
remain pinned/cached. No dependency installation or model copy occurred.

```powershell
npm --prefix apps/desktop run check
npm --prefix apps/desktop run format:check
node apps/desktop/trace-harness.mjs
node apps/desktop/inspector-harness.mjs
node apps/desktop/harness.mjs native
node apps/desktop/harness.mjs headless
node apps/desktop/durable-harness.mjs
node apps/desktop/export-harness.mjs
cargo test --manifest-path apps/desktop/src-tauri/Cargo.toml --locked --offline --target-dir <owned-D-target>
cargo test --manifest-path apps/desktop/src-tauri/Cargo.toml --locked --offline --features dev-harness --target-dir <owned-D-target>
cargo test --manifest-path apps/desktop/src-tauri/Cargo.toml --locked --offline --target-dir <owned-D-target> models::tests::abandoned_import_reparse_file_is_preserved -- --exact --ignored
cargo clippy --manifest-path apps/desktop/src-tauri/Cargo.toml --all-targets --locked --offline --target-dir <owned-D-target> -- -D warnings
cargo clippy --manifest-path apps/desktop/src-tauri/Cargo.toml --all-targets --locked --offline --features dev-harness --target-dir <owned-D-target> -- -D warnings
cargo fmt --manifest-path apps/desktop/src-tauri/Cargo.toml -- --check
cargo build --manifest-path apps/desktop/src-tauri/Cargo.toml --locked --offline --target-dir <owned-D-target>
git diff --check
```

Frontend verification retains every earlier schema/wire/export/model/terminal-
refresh/inspection check and adds the trace-controller regression. Normal assets
are rebuilt and checked to exclude fixed harness markers. The final default
native executable is restored after all harness runs; its separate hash is in
the evidence. Compare Git-normalized source text when checkout CRLF differs.

Full D06 remains unchecked. Actual model role spans rendered through this UI,
selected-context/raw-proposal evidence, memory maintenance, pause/sandbox rerun,
full capture/export, hostile-renderer security, assistive-technology qualification,
long-history performance and genuine network-blocked/device qualification remain
open. No protected chat/model/device/process, unrelated-app or desktop control,
PR, merge, settings change or release was performed by this UI slice.

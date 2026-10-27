# Protocol3 selected-case reruns: shared scripted qualification

Scope: D07.06/.02/.04 supporting work under #29, from accepted PR197/main
`2037bdeda7def31b9d6872abe3f33dfab0a59233`. This record qualifies the shared
scripted Rust API only. Native selected2, CLI/UI execution, native IPC/rendering,
human quality, whole-app performance and phone gates remain pending.

## Interface and invariants

`local_lane::comparison::literal_v3::selected_v2` provides opaque preparation,
safe prepared metadata, run, resume and cold inspection. It accepts the existing
RowId and SelectedIntent. Only ScriptedBaseline is admitted in this slice;
ApprovedNative returns SelectedNativeUnavailable before opening a source or
creating a target. A reader capability is never an execution grant.

The strict selected manifest/report version2 binds source_protocol_version3,
both exact construction descriptors, original suite/profile/source/reference
identity, clicked original row and each arm's actual Request, before revision,
receipt-prefix hash and semantic input hash. Paired snapshots retain the actual
reference prefix. Rollouts retain separate actual arm prefixes. Literal input
is never represented as ContextPolicy or a version2 comparison row.

Preparation owns its own validated source lock. Consumption revalidates the
whole source, including the unclicked arm, before destination mutation. Resume
reconstructs this plan from the source and compares its complete manifest.
Supported source-fingerprint drift remains readable through cold inspection;
prepare/run/resume still require current-source and full-manifest validation.
A completed resume is read-only only after that validation; it is not an
unconditional cached success without its source.

The original source_profile/source_native describe the original V3 cohort.
The rerun lane/profile describe this new ScriptedBaseline run. A native-labelled
source does not make the selected rerun native.

Selected1 retains its strict schema, field order, filenames and public API.
Shared helpers enforce directory pins, single-link files, disjoint destinations,
canonical Store prefixes, request/receipt consistency, bootstrap recovery and
bounded reports. Both prefix checks now precede checkpoint decoding, so the
first error for a fixture with multiple independent corruptions may differ.
This changes no writes or permissions. Each codec still validates its own row.

The existing literal turn execution, actual Host/Store, checkpoint/evidence
reader, resource Ledger and conservative recovery own behavior. Both arms are
classified and preflighted before either invocation is reserved. A genuine
Store commit can recover a lost checkpoint without generation, while missing
failed/cancelled/stale terminal diagnostics refuse regeneration. Recovery keeps
unmeasured historical roles and construction evidence unavailable. A completed
resume returns without rewriting reports, checkpoints, ledgers or canonical data.

## Evidence discipline

Production first commit b1891560 had a compiler visibility error when accessing
the private setup decoder. cb391224 adds a narrow validation wrapper; strict
all-target Clippy then passed in10.07s. This was a compiler repair, not a
behavioral RED/GREEN regression.

Independent public oracle52dcfe62 was adopted495681c0 and formatted77814ee9.
Its first actual default-feature run at77814ee9 passed all6 groups in478.93s.
No behavioral RED is claimed for this previously absent API. The fixtures are
actual scripted protocol3 paired1scene and rollout2scene runs, plus the actual
shared reference producer. They do not establish native inference or quality.

The6 groups verify per-arm inputs and construction, safe metadata, full source
inventory preservation, completed resume twice with the entire target inventory
unchanged, committed checkpoint-loss recovery with no new turn admission/raw
role files/receipt, actual Inventory guard terminal refusal, checkpoint/Store
disagreement, unclicked-arm corruption after preparation, closed manifest
versions/descriptors, cancellation before output and unavailable native/old1 paths.
The ordinary scripted rollout agrees semantically; divergent history requires
the separate private oracle and must not be inferred from this fixture.

Independent private packetfd1e117e was adopted699e80dc; registration/format and
one fixed cancellation boundary test are cc06b670. All3 private groups passed
in55.17s (11.10s compile), with clean unchanged source. Budget reservations are
created through actual Ledger calls and deliberately remain unknown; measured
invocation overhead is settled without invented role/cost records. Second-arm
refusal preserves source and both target-arm inventories before any new arm
reservation/bootstrap. Genuine first-left WrongCommand failure yields different
actual canonical prefixes, revisions, full requests and semantic inputs; selected
Move keeps those differences and both correct construction descriptors.

The fixed cancellation flag exists only under cfg(test), with no IPC endpoint
or production hook. The same public run commits/checkpoints the first arm, then
observes cancellation; the other arm has no DB/checkpoint/admission. Public resume
attempts only the missing arm, preserving old canonical/raw/admission bytes and
completed row. A subsequent completed resume preserves the full target inventory.
This is a scenario-boundary proof, not a native pending provider or UI journey.

Old selected1 public compatibility passed6 groups/663.98s at77814ee9, before
private test-only registration. No later normal-build selected1 production edit
was made. Source-only reviews of implementation, private oracles and this draft
found no additional concrete defect; these are not human quality/approval evidence.

Final behavioral cohort at cc06b670 (clean, unchanged):

| Check | Actual result |
|---|---|
| Default-feature public selected2 | 6 passed,0 failed/ignored;515.78s |
| Old V2 capture semantic projection | 1 test/four projections passed;.11s; all four retained hashes unchanged |
| Old actual V2 producer semantic projection | 1 passed;4.76s;12 rows/18,505 bytes;9134ccc9609b3f9c5942c04f8c2c9fe1e008e962bcae537b42139e0e4642a065 unchanged |
| V3 manifest/lifecycle and actual pending Director cancellation | 2 passed;.66s |
| Genuine historical native selected1 read | 1 passed;1.13s; full retained inventory unchanged; no worker/model call |

Strict all-target lint then found needless_range_loop in the independent private
oracle. Commit64e3251115995c767cb51d4dfbbd21b986ca00ce changes three assertion
lines to enumerate the same expected Engines; no production code changed.
The affected private3 groups passed again in48.39s (9.66s compile). The public6
were not rerun after this test-only style correction; their exact source remains
cc06b670c6f4ec3e9f3eb6c9aa6ae3f6d9e7e743. Test files also contribute to the existing
build fingerprint, so these source records are distinguished rather than claimed
byte-identical binaries.

Final compatibility at64e32511 (all terminal, clean, unchanged):

| Check | Actual result |
|---|---|
| Eval strict all-target Clippy with local-model | PASS;12.06s compiler-reported |
| Eval rustfmt | PASS;4.188s command wall |
| Full frontend/type/controller/strict wire/headless and normal hook exclusion | PASS;14.845s command wall |
| Native strict all-feature/all-target Clippy | PASS;20.69s compiler-reported |
| Normal native build | PASS;22.30s compiler-reported; not launched |
| Android Rust host | 20 passed;0 failed/ignored;1.68s |
| Android dependency graph | PASS; no Eval, local-runtime or Tauri dependency |

These are test/build durations, not app or model latency measurements. No new
UI image or semantic capture was generated for this Rust-only slice. Frontend
mock/headless checks are not native IPC/WebView execution. The normal build is
not native execution. The previous protocol3 reader's app-owned render/IPC
qualification remains separately recorded in PR197; it does not prove selected2
UI execution. No Android JVM/ABI/emulator/phone or new real-model check ran.
Raw synthetic logs and unique process records are retained locally outside Git;
no private prompts, models or machine paths are published.

## Reproduce

Use the repository-pinned Rust toolchain and already available dependencies.
Do not download models or run a native provider for this scripted cohort.

```powershell
cargo test --locked --offline --jobs 1 --manifest-path crates/locallore-eval/Cargo.toml --test literal_selected_v2 -- --nocapture --test-threads=1
cargo test --locked --offline --jobs 1 --manifest-path crates/locallore-eval/Cargo.toml --features local-model --test comparison_selected_review -- --nocapture --test-threads=1
cargo clippy --locked --offline --jobs 1 --manifest-path crates/locallore-eval/Cargo.toml --features local-model --all-targets -- -D warnings
cargo test --locked --offline --jobs 1 --manifest-path crates/locallore-eval/Cargo.toml --features local-model --lib local_lane::comparison::literal_v3::selected_v2::review_tests -- --nocapture --test-threads=1
cargo test --locked --offline --jobs 1 --manifest-path crates/locallore-eval/Cargo.toml --features local-model --lib literal_capture_legacy_tests -- --nocapture --test-threads=1
cargo test --locked --offline --jobs 1 --manifest-path crates/locallore-eval/Cargo.toml --features local-model --lib literal_producer_legacy_tests -- --nocapture --test-threads=1
cargo test --locked --offline --jobs 1 --manifest-path crates/locallore-eval/Cargo.toml --features local-model --lib literal_v3::lifecycle_tests -- --nocapture --test-threads=1
cargo fmt --manifest-path crates/locallore-eval/Cargo.toml --all -- --check
cargo clippy --locked --offline --jobs 1 --manifest-path apps/desktop/src-tauri/Cargo.toml --all-features --all-targets -- -D warnings
cargo build --locked --offline --jobs 1 --manifest-path apps/desktop/src-tauri/Cargo.toml
cargo test --locked --offline --jobs 1 --manifest-path crates/locallore-android/Cargo.toml --lib -- --nocapture --test-threads=1
cargo tree --locked --offline --manifest-path crates/locallore-android/Cargo.toml --edges normal,build,dev --prefix none
# From apps/desktop, using the existing pinned Node runtime/dependencies:
node verify-frontend.mjs
```

The historical read uses the existing genuine synthetic fixture, with
LOCALLORE_SELECTED_NATIVE_HISTORY pointing to that owned native-target directory:

```powershell
cargo test --locked --offline --jobs 1 --manifest-path crates/locallore-eval/Cargo.toml --features local-model --test comparison_selected_native_historical_review -- --ignored --nocapture --test-threads=1
```

The exact local invocations additionally select a task-owned external Cargo
--target-dir. Their process records retain the full local argument list; this
record omits that machine path. The historical fixture is not regenerated or
relabelled by the check; without it, this opt-in qualification is unavailable.

Qualification environment: Windows NT10.0.26300 x64, PowerShell7.6.5,
Rust1.93.1 (01f6ddf75), Cargo1.93.1 (083ac5135), LLVM21.1.8, existing
Node24.22.1. Builds use one Cargo job, debug information0, incremental disabled
and locked/offline resolution. Synthetic databases/raw evidence stay local and
ignored. Hashes detect consistency drift; they do not authenticate hostile edits.
No desktop input, activation, screenshots, computer-use or protected resources
are used. No release, settings change, dependency install or phone execution.


## Status and next task

This is a supporting D07.06/.02/.04 result, not full task/epic acceptance. The
next runnable task is native selected2 through the established reservation,
absolute startup deadline and retained owner cleanup path, followed by the
versioned selected reader and existing Story Lab controller/IPC/render harness.
Inspection remains separate from generation permissions. Human meaningful-sample
review, performance/RAM, shared maintenance and remaining desktop exit gates stay
open. No milestone checkbox is changed by this record.

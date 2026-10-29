# Narration diagnostic Host read v1: partial qualification

2026-10-29. Refs #9 **M05.03/M05.04**, #29 **D07.04**.
**Implemented; focused/schema/frontend compatibility measured; broad gates pending.**
Measured source: `fab59b0761a0585ff57cc8b8e315d7134f8805e2`.
This Host adapter is not UI adoption, Eval persistence, native IPC/WebView,
model/device evidence, human-quality acceptance or full task acceptance.

## Scope and preserved boundaries

The [accepted contract](D07_NARRATION_DIAGNOSTIC_HOST_READ_CONTRACT_2026-10-29.md)
and [HOST_V1 operation](HOST_V1.md#opt-in-narration-validation-read) define the
opt-in `trace_narration_validation_read_v1`. Its required session/scope/current
head/base revision/turn/attempt select the existing owned player attempt.
Native u32 conversion precedes the unchanged shared Core selector preflight;
no JSON observer, owner, handle or privilege is accepted.

A valid non-Story-Lab command is denied after bounded parse/version checks and
before State/session/StoragePort/source access. Existing TooLarge/Malformed/
Version precedence remains. The synthetic Host spy and poisoned-State tests
exercise this **Host-level** zero-probe boundary. Desktop cold
`WorkspaceState::get` can initialize/open storage and reap previews before Host;
these tests do not establish transport-wide zero filesystem activity.
Authorized existing admission can retire/cancel an invalidated attachment on
NotFound. Session/scope/storage/current-head/selector errors remain distinct from
an authorized unavailable diagnostic; whole-Host side-effect freedom is not claimed.

Plain trace `try_lock` returns authorized Unavailable on busy/poison without
recovery, clear, retry or configuration. Reads add no attempt, provider request,
validation/cancellation pass, canonical mutation or knowledge/generation grant.
The separate Serialize-only DTO binds session/scope/head/base/turn/attempt,
literal observer player and `generation_grant:false`. Recorded includes exactly
the four decision fields; Unavailable has no decision key. Fixed actual tuple
projection maps unsupported/inconsistent metadata to Unavailable, never an
invented Unclassified cause. The new operation's **entire envelope**, including
rejected replies, is capped at 4,096 bytes without truncation; old global limits,
trace/capture/PlayRecord/Report4 formats and other operations remain unchanged.
Core changes only the existing selector helper's crate visibility.

## Independent FIRST provenance and preserved source finding

The Phase2 [retention gate](D07_NARRATION_DIAGNOSTIC_RETENTION_QUALIFICATION_2026-10-29.md)
precedes this slice. Formal Host interface acceptance is `27c2607a`.
Independent original six-group test source `a2f5f967` integrates as `0fa0b7cb`;
Root registers/formats it at `8ca5a988`, with module order at `bd4e26d0`.
The original 555-line freeze SHA256 is
`2afb14de702bbcc9ceeeb5519122f6a77750c7324ebb64857b670f4c17a8d94a`;
rustfmt equality proves the registered source SHA256
`e1ae862213cfe1cee595bc7422825d0105975d3ec45bb452fd38b25586ab087e`.
Missing operation/helper/schema were setup prerequisites, not a behavioral RED.

Before production or Rust test execution, Root found that the fixture's global
JSON token replacement renamed the required Seed `player` property key while
changing a nonliteral actor ID. This was local JSON/source inspection, not a
measured Host/Engine failure. Preserve the original freeze and finding.
Independent typed-Seed correction `ea06232a` integrates as `17f447f8`: it changes
only exact actor-ID values/map keys, retaining schema keys, ordinary text,
nonliteral-player coverage and the synthetic privacy sentinel. The correction
proof preserves all six test bodies/helpers after that fixture function.
Corrected immutable SHA256:
`14f4752332fcd5a81ce16fec9f8c3883c7a55543ea4503887d69f3fb396d4aac`.
No runtime failure, repaired capture or weakened oracle is claimed for this fix.

Production `463339c7` integrates as `49ec08de`; rustfmt is `2a977a94`.
Independent source review at `2a977a94` reported no blocker; review is separate
from execution. Production remains unchanged through measured `fab59b07`.

## Actual generation and completed checks

Private absolute target arguments below are normalized to `<owned-D-target>`;
the private absolute Node executable is normalized to `node`. Local records keep
exact paths/arguments/timestamps. No other command argument is normalized.

At clean `2a977a94`, Root ran existing generators, not new generator code:

```text
cargo run --manifest-path Cargo.toml --locked --offline -p locallore --features host --example host_schema --target-dir <owned-D-target>
node apps/desktop/build.mjs
```

Rust JSON stdout was used as `apps/desktop/host-v1.schema.json` before the Node
build; the commands above are the recorded child invocations.
Both exited 0: recorded Rust stage 10.6963861s; combined generation 12.6789727s.
The remaining stage includes Node generation; no isolated Node process duration
is claimed by this record.
The first production compile/generation passed. Source head was unchanged;
only expected tracked schema/type files were dirty, with no unexpected tracked
changes. This generation record is not a test result. `1f8b29bd` commits generated
requests; pinned Prettier3.9.10 restores established JSON formatting at
`fab59b07`. The combined request-only delta is 43 schema lines plus 9 type lines.
The actual Rust/schema semantic equality test below passes. Generated types
describe requests; no new response decoder or frontend consumer exists.

All nine completed check records below report exit 0, clean unchanged
`fab59b07` and empty dirty lists:

| Check | Actual result | Command duration |
| --- | --- | --- |
| Rust/schema equality | 1 passed, 0 failed; 99 filtered | 8.8987370s |
| Frozen Host-read filter | 6 passed, 0 failed, 0 ignored; 94 filtered; 0.23s test | 0.5008883s |
| Existing Host scene recipe suite | 4 passed, 0 failed; 0.09s test | 1.8686413s |
| Existing native retention filter | 11 passed, 0 failed; 89 filtered; 0.27s test | 0.5455744s |
| Strict all-feature/all-target workspace Clippy | Passed | 40.8931979s |
| Workspace formatting | Passed | 2.0324866s |
| Core without default features | Passed | 2.2161284s |
| Android Rust host compilation | Passed | 3.3266871s |
| Full frontend checks/normal build | Passed | 16.1804034s |

```text
cargo test --manifest-path Cargo.toml -p locallore --lib --features host --locked --offline --target-dir <owned-D-target> host::tests::schema_is_generated_from_rust -- --test-threads=1
cargo test --manifest-path Cargo.toml -p locallore --lib --features host --locked --offline --target-dir <owned-D-target> host::narration_diagnostic_read_review_tests:: -- --test-threads=1 --nocapture
cargo test --manifest-path Cargo.toml -p locallore --features host --locked --offline --target-dir <owned-D-target> --test host_scene_recipe_v1 -- --test-threads=1
cargo test --manifest-path Cargo.toml -p locallore --lib --features host --locked --offline --target-dir <owned-D-target> turn_trace::narration_diagnostic_retention_review_tests:: -- --test-threads=1 --nocapture
cargo clippy --workspace --all-features --all-targets --locked --offline --target-dir <owned-D-target> -- -D warnings
cargo fmt --all --manifest-path Cargo.toml -- --check
cargo check --manifest-path Cargo.toml -p locallore --no-default-features --locked --offline --target-dir <owned-D-target>
cargo check -p locallore-android --locked --offline --target-dir <owned-D-target>
node apps/desktop/verify-frontend.mjs
```

The six functions use actual synthetic Host/Engine/Play/RingSink reads for both
recipes, finite reason order, early denial, admission/selector precedence,
owner/session/head/attempt isolation, lifecycle/lock behavior and unchanged
provider/receipt/replay/knowledge/old-wire results. Separate trusted private
tuple and long-session-alias controls exercise projection and reply limits;
they are not actual Engine failures, public capability issuance or origin proof.
Expected caught synthetic poison panics remain visible in the passing log.
The future-version guard remains source-reviewed: the current getter is
constant 1. No hypothetical runtime version or negative-Serde-trait proof is claimed.

Root's recorded environment is Windows, Rust/Cargo/rustfmt 1.93.1 and
Node 24.22.1, existing locked/offline dependencies, one heavy job, one Cargo build
job, incremental disabled and dev/test debug0. Process-local TEMP/TMP are
`D:/Dev/_Temp`; source, cache, targets and local outputs reside on D:.
The documentation author read source/bounded records and checked Git scope/
whitespace only; no compiler, formatter, Cargo, Node, browser, app, model/assets,
device or desktop execution was performed by this author.

## Completed broad and normal-native checks

At clean, unchanged `fab59b0761a0585ff57cc8b8e315d7134f8805e2`, the serial
sequence completed with exit0 and empty dirty lists:

| Check | Actual result | Command duration |
| --- | --- | --- |
| Portable workspace excluding desktop | 1,046 passed, 0 failed, 11 ignored; 142 result groups | 519.4704493s |
| Development native suite | 282 unit + 2 contract passed, 0 failed, 11 ignored | 743.6410952s; 702.02s unit-test time |

```text
cargo test --workspace --exclude locallore-desktop-spike --all-features --locked --offline --target-dir <owned-D-target> -- --test-threads=1
cargo test --manifest-path apps/desktop/src-tauri/Cargo.toml --locked --offline --features dev-harness --target-dir <owned-D-target> -- --test-threads=1
```

The qualification-document-only integration `f640b64f` leaves all production,
test and generated request files unchanged. At that clean, unchanged source,
normal Windows native build passes in 10.8784372s and normal all-target strict
Clippy passes in 9.7170032s. The normal product remains unlaunched.

```text
cargo build --manifest-path apps/desktop/src-tauri/Cargo.toml --locked --offline --target-dir <owned-D-target>
cargo clippy --manifest-path apps/desktop/src-tauri/Cargo.toml --locked --offline --all-targets --target-dir <owned-D-target> -- -D warnings
```

## Actual retained native compatibility journey at `fab59b07`

`node apps/desktop/comparison-run-harness.mjs --native-scene-review-v1` ran with
the exact existing retained packet, approved publication and owned target paths
provided in process-local environment variables. It used the real frontend
controller, native IPC and hidden, unfocused WebView2 rendering. No desktop
control, desktop capture or OS-dialog automation was used. The wrapper started
no child after the harness and inspected existing cleanup records only.

2026-10-29 12:08:19.2807851Z–12:09:46.2420194Z: **257 checks, 12 PNGs,
zero recorded broker errors**, 86.9612343s, exit0 and unchanged clean source.
Historical results open; explicit resume correctly returns
`EvaluationSourceMismatch` / `source_mismatch`. This is a retained historical
read/refusal journey, not successful completed resume at this source.
It does not exercise the new Host operation through IPC or add UI display of it;
the new operation's direct execution evidence is the six Rust Host tests above.

All twelve captures were individually inspected. Nine artifact views also have
positive, in-viewport heading/source/outcome rectangles without selection-header
overlap. The idle PNG's inspection preview initially appeared blank. Its
original bytes are identical to the readable finished PNG, SHA256
`fffdeb43e969a105ff5ad61cab0856b1ff9a0df19fe00420ecf1d18e734bb908`.
Read-only decoding and an encoding-only preview have identical RGBA bytes,
SHA256 `7cf95d7d86a403f96a0e497e7c9b0ead159eced80d64e87e847033ae84202cd4`;
the derived preview was individually inspected at original detail and shows
readable UI. All source PNGs remain unchanged. This is a tool-preview anomaly,
not a repaired capture, app failure or reason for a new inference run.
The local twelve-image review manifest SHA256 is
`f97725d715af8210daa4808c5e1f812fcccc6b164b1f35ab16bf0cf20d2a0b38`.

All 2,072 retained result files remain byte-identical, aggregate SHA256
`f22cd3ec7c40c8870684b025fe1bcd909a4664e34f92f552779f2068bce429e5`.
Original workspace SQLite remains absent. Reservation sequence, consent calls
and retained-Eval observations remain zero; no owner is present before or after.
No inference, model import, weight copy or source-fingerprint rewrite occurred.
Those observations support the source-reviewed no-call path; they are not an
independent SDK-load counter. All 32 known child executions closed, unknown
drain is false and the unknown-child list is empty. Normal products were
restored successfully and left unlaunched.

Additional recorded versions: WindowsNT10.0.26300.0, PowerShell7.6.5,
Prettier3.9.10, TypeScript7.0.2 and json-schema-to-typescript16.0.0.
The native user agent reports Chromium/Edge156.0.0.0; an independent installed
WebView build was not obtained. These are scoped compatibility checks.

## Remaining gates and limitations

Independent final evidence review and this focused slice's review gate remain
pending. No previous slice's counts are copied or relabeled as these reruns.

Rust synthetic Host/native-component tests and frontend mock/controller/headless
checks/build do not establish native IPC/WebView rendering, new real-model
execution, Android ABI/device behavior or human quality. Earlier Phase1 Eval,
native-render and Native4 report evidence keeps its original source attribution.
Host/schema changes affect Eval fingerprints: preserve historical source-mismatch
refusals and unavailable causes; do not rewrite captures or backfill decisions.
No Eval companion, UI display, Report4 extension or new model cohort is added.
Both original and newer human assessments remain **needs improvement**.

Bounded local `d07-narration-host-read-*` process/log/equality/correction records
retain evidence; private paths/raw material stay outside this public document.
Next: independent evidence review and an update to the existing
[PR #255](https://github.com/OptimumAF/LocalLore/pull/255), stacked above
[PR #253](https://github.com/OptimumAF/LocalLore/pull/253). Full M05.03/M05.04,
D07.04 and dependency acceptance remain unchecked; no merge/release is authorized.

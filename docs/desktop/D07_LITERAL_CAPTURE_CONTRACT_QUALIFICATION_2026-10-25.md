# Literal comparison capture contract qualification

Scope: D07.04 / M07.01; accepted base PR187 / `4511d67d`.
Production tested at `f0c62335`; `6c12b171` only orders module declarations.
This is a metadata and private diagnostic input contract, **not a protocol3
producer, persisted report, model comparison or UI implementation**.

## Contract

`memory_comparison_v3::arm_descriptors()` returns the fixed ordered pair
`literal_player_v1`, `relevant_memory_v1`. Every descriptor has twelve required
JSON keys, including explicit nulls for inapplicable fields. Unknown keys and
omitted nullable fields are rejected; `validate()` checks the entire supported
tuple. Deserializing metadata grants no Host configuration or execution access.

The literal arm records Play2.6, grounded-prose2.2, literal Director schema1,
source/render/schema/packing1 and forwarded-budget1. It has no context policy,
compiler version or context version. The relevant arm records Play2.5,
grounded-prose2.2, Director schema2, Relevant policy, compiler/context2 and
forwarded-budget1; all literal version fields are null. Existing `ContextPolicy`
and historical report protocols are unchanged.

Private, owned, non-serde `CapturedLiteralContext::from_host_capture` checks:

- Actual supplied Domain1 Engine/request scope/head and player/turn/attempt
  identity; original Host artifact/count/byte bounds.
- Pinned comparison profile:4096 context,350 tokens for each role,120000ms,
  one repair, with valid profile hashes/identity.
- One Director, optional one repair, optional final Narrator; recording order,
  multiplicity, schema IDs, prompt/schema hashes and request budgets.
- No selected-context artifact, unknown artifact, compiler annotation or
  player-text-hash annotation. Existing passive recording remains unchanged.
- Full Director prompt **and schema** equality with the actual Core literal
  source and Initial/used-Repair renderer. Matching hashes alone are insufficient.
  Shared forwarded estimates and exact repair relation are checked again.
- Candidate Play record, when present: closed typed record, exact literal
  version/policy/profile, absent memory construction and actual repair count.

No recording or no Director input is `CaptureUnavailable`, never positive
literal evidence. Returned source/selected counts come from the Core renderer.
The common `capture_envelope` module extracts existing v2 envelope checks;
its selected-context, compiler annotations and old forwarding checks stay in v2.

## Actual checks

Windows x64 NT10.0.26300, PowerShell7.6.5; Rust/Cargo1.93.1
(`rustc01f6ddf75`, `cargo083ac5135`, LLVM21.1.8). Cached dependencies only,
locked/offline, one build job, incremental/debug information disabled.
No model, provider worker, WebView, device or desktop automation was launched.
The feature named `local-model` below compiles optional code; it does not execute
inference. Actual generation in these fixtures is explicitly scripted.

| Source / check | Result |
| --- | --- |
| `d209f603`, original v2 reference capture | Four actual Host cases emitted their hashes; final sentinel assertion intentionally failed. This is reference capture, not behavioral RED. |
| `3008e532`, anchored original v2 baseline | PASS1/.12s, before any production helper extraction. |
| `19d321ff`, new frozen test registration | Missing `memory_comparison_v3` API compiler errors; no behavior executed. |
| `f0c62335`, new literal groups + old references | PASS8/.29s; build8.43s. |
| `f0c62335`, all literal oracles | PASS18/1.41s, including ten existing negative-control groups. |
| `f0c62335`, forwarded-budget regression | PASS8/6.77s. |
| `f0c62335`, local-model all-target strict Clippy | PASS13.99s. |
| `f0c62335`, genuine preserved UI5 read-only integration | PASS1/16.36s; build6.84s. |
| `6c12b171`, evaluator format/diff checks | PASS. |
| `6c12b171`, literal capture tests without local-model feature | PASS8/.28s; build7.25s. |

Frozen new seven-group test source was committed before production at
`e3f8d1e` (integrated `bba0e247`). It uses actual Host configuration, prior
accepted history, explicit trace consent, existing RecordingProvider/private
capture and real commit. Action and Unicode Dialogue each genuinely repair once;
their actual candidate equals the real committed receipt. Mutated copies are
explicit diagnostics, never attributed to Host. Rehashed Director prefix, tail,
extra state, schema and repair changes refuse despite fitting the token budget.
Identity/profile/deadline/annotation/order/context/unknown-artifact cases refuse;
guard absence, changed scope/head/player and actual Domain2 refuse.

Original v2 source packet `8233be98` captures all four stable semantic fields
returned by the original gate: package, both prompt lists and estimates. It
excludes timing-bearing full Host replies/GenerationRequests/receipts. Actual
old hashes remain unchanged after extraction:

| Case | Bytes | SHA256 |
| --- | ---: | --- |
| Recent Action repair | 30883 | `cf83fcef668f11f1c81fa1bcc3c839a5f67e4e077672ac274a2c8e8de84ed157` |
| Recent Dialogue repair | 30241 | `05a66e4cdab9fe760266f74a2597e90c8b1721f84e5cdb4e08d68e4e3926c1f7` |
| Relevant Action repair | 30659 | `fe571feb3982a193ee247994c82d942b0f72aa90f0f5f78ccac28064262c779c` |
| Relevant Dialogue repair | 30017 | `d22505d9ec3b4890218c8dc1f85a0b02f844cc27c969f668b1fdbdf5bdb6dd81` |

Retained failures: first baseline replacement accidentally retained a trailing
sentinel byte; corrected in separate commit without changing observed hashes.
First implementation failed compilation on constant re-export visibility and
assumed Capture equality/version fields; corrected without changing Capture.
First format check requested module ordering; corrected separately. None is a
passed check or a demonstrated behavioral regression. Local logs preserve all
attempts under `d07-literal-capture-*`; generated artifacts remain outside Git.

The genuine historical test pins original UI5 run/selected manifests, exercises
permission denial and original Move4→5 receipts, reports `source_matches=false`,
and verifies byte-identical complete inventories after locks/capabilities drop.
It creates no replacement fixture, invokes no writer/provider and claims no
fresh native rendering or historical resume execution.

## Reproduce

Use existing dependencies and task-owned absolute target/temp paths. Serialize
with other heavy checks. No model installation or app interaction is required.

```powershell
$env:CARGO_BUILD_JOBS='1'; $env:CARGO_INCREMENTAL='0'
$env:CARGO_PROFILE_DEV_DEBUG='0'; $env:CARGO_PROFILE_TEST_DEBUG='0'
$env:LIBSQLITE3_FLAGS=''; $env:TEMP='<owned-temp>'; $env:TMP=$env:TEMP
cargo test --locked --offline --manifest-path crates/locallore-eval/Cargo.toml --features local-model --jobs 1 --target-dir <eval-target> --lib literal -- --nocapture --test-threads=1
cargo test --locked --offline --manifest-path crates/locallore-eval/Cargo.toml --features local-model --jobs 1 --target-dir <eval-target> --lib forwarded_budget_tests -- --nocapture --test-threads=1
cargo test --locked --offline --manifest-path crates/locallore-eval/Cargo.toml --jobs 1 --target-dir <eval-target> --lib literal_capture -- --nocapture --test-threads=1
$env:LOCALLORE_LITERAL_HISTORICAL_COMPARISON='<genuine-UI5-comparison>'
$env:LOCALLORE_LITERAL_HISTORICAL_SELECTED='<genuine-UI5-selected-work>'
cargo test --locked --offline --manifest-path crates/locallore-eval/Cargo.toml --features local-model --jobs 1 --target-dir <eval-target> --test literal_control_historical_review -- --ignored --nocapture --test-threads=1
cargo clippy --locked --offline --manifest-path crates/locallore-eval/Cargo.toml --features local-model --jobs 1 --target-dir <eval-target> --all-targets -- -D warnings
cargo fmt --manifest-path crates/locallore-eval/Cargo.toml --all -- --check
```

## Limits and next task

Hashes establish consistency, not authenticated origin. This gate re-renders
Director input from the supplied Engine; it cannot distinguish arbitrary hidden
seed differences invisible to those bytes. The future producer/reader must
also bind full source/canonical row, raw file/output integrity and ledger.
Candidate tuple checking is not receipt replay or canonical acceptance.

Narrator verification covers envelope/hash/order only, not its renderer or
semantic privacy. An explicitly copied/rehashed Narrator prompt is accepted by
this limited input gate and is not actual Host evidence. No universal privacy,
quality or output-authentication claim follows.

Next: add the separately scoped protocol3 producer/reader with strict arm
metadata and existing Store/Host/recording/ledger/resource/cancel/resume ownership;
then qualify real paired local models and selected-run/UI integration. Existing
protocol1/2 reports remain historical under their own versions. No UI/native,
Android, device, real-model, whole-app memory, narrative quality or human-review
gate is newly executed here. Prior PR187 host/Android compatibility remains
dated evidence. D07/M07 criteria remain unchecked until fully satisfied.

# Guard-bound director schema, 2026-10-23

Partial M05.01/.02/.04 (#9) and D04.04 (#25). Claims [6369970391](https://github.com/OptimumAF/LocalLore/issues/9#issuecomment-6369970391) / [6369970687](https://github.com/OptimumAF/LocalLore/issues/25#issuecomment-6369970687), contributor `/root/resource_metrics_review`, separate `impl/m05-guarded-director-schema` / `source-guarded-director-schema`. Based on accepted main `8120b422c6dbd41a7ec6b0ddecc71863a756f3c9`. Production/test source frozen at `5138427ab7e5965315a1d937777bf38cf439b661`, preceded by fixture-only `43bc8cb`. This is synthetic and native model-free qualification, not a new model cohort or quality signoff.

## Change and authority

The existing finite `supported-english-v1` input guard already maps supported Action text to exactly one typed Command. Existing Engine preflight rejects an illegal command before any provider call. Previously the generated schema still allowed alternative operations, recipients, items and quantities that the subsequent guard would reject. The frozen prior curated model cohort's wrong-but-valid proposals remain failures; neither fixtures nor their expected commands/results were changed here.

`play.rs` now retains the **same preflight Command** and uses its serialized fields as scalar JSON Schema constants. The generated `commands` array has exactly one element; only that operation and those arguments are admitted, with exact required fields and no extra properties. The existing approved worker's schema ordering/converter supports these existing constructs. There is no second text interpreter, copied expected-evaluation command, worker patch or new dependency.

The finite guard already does the action interpretation. Consequently the model is mechanically redundant as an interpreter for these supported Action forms: this change constrains serialization of an already bound attempt. The actual provider must still generate bytes through its normal bounded path and may fail, time out or be cancelled. Those bytes are parsed, compared against intent and validated by Engine; no automatic proposal/effect substitution occurs. An unconstrained or malicious provider returning another valid command still receives Agency and leaves canon unchanged. This is not expanded natural-language support or evidence of narrative quality.

The request-bound schema applies to actual production Play director/repair requests, not the generic public `director_schema()` catalog helper. Dialogue remains literal speech with the existing present-audience choice. Narrator prompt/schema, prose checks/fallback, role budgets, token/context/deadline caps and repair limit remain unchanged. The accepted profile limits remain 350 tokens per role, 4096 context tokens, at most 120000ms and one malformed-output repair; synthetic tests use a 1000ms deadline and 220 narrator tokens within those caps.

Only production `play.rs` changed. No Engine, guard parser, Host/wire contract, compiler, Store/schema, runtime, worker, UI, Android or evaluation runner/fixture was modified. The narrow existing `play_v2.rs` assertion now requires exact gift constants instead of the old broad inventory/nearby enum; its actual proposal/narration/replay checks remain.

## Provenance and accepted history

New Play prompt/schema provenance is `locallore-play-v2.3`; policy stays `grounded-prose-v2.1`, Play format stays 2, and role input format/discriminators remain v2. The prompt text is unchanged; the recorded pipeline provenance advances because the production schema changed. Version 2.4 is reserved for a later separately owned memory-consumer change.

Accepted 2.1 and 2.2 records remain explicitly **history-only**. Restore, replay, fork ancestry and branch continuation validate the recorded effects/prose and preserve the original provenance. Fresh prepared commits require current 2.3; an old record cannot authorize a new turn. Existing exact retries return accepted history without inference. Unknown 2.0, future 2.4 and forged effects remain rejected. Checksums/provenance labels are not authentication.

Before production edits, a task-local standalone Rust fixture generator linked the clean accepted `8120b422` Core and actually called `play::execute` with a clearly synthetic gift/narrator provider. Two provider calls produced the new `tests/fixtures/accepted_play_v2_2.json`; strict restore matched canonical bytes. The generator asserted current prompt was 2.2. Fixture frozen in its own commit before source changes, not manufactured by relabeling a 2.3 receipt. It records source commit, synthetic=true, provider_calls=2, seed and actual receipt. Original accepted 2.1 fixture remains unchanged.

Pre-edit source SHA256 (checkout bytes): `play.rs` `2a9e3757d2642abb66c4e35d70a4493ed8fc313bad7102d1c650c2c9dc67c75d`; `intent_guard.rs` `73c7ffc802db877db2926da365ebc93e78450c17024fa76fcd962ae36f80fd6f`. Frozen generated fixture LF-byte SHA256 `f3645af4047e02b827010134cb57b1d974c86538b68ebf8e43801ea8bcde8f3d`. Checkout newline conversion may change byte hashes; exact parsed receipt fields are asserted in the compatibility test.

## Executed verification

Windows x64 10.0.26300.0; Rust/Cargo 1.93.1. Own task-local D target and UUID TEMP/TMP, debug=0/incremental=0, locked/offline. No model load/calls/download, worker replacement, system/device control, install, release, merge, repository setting or protected-chat operation.

From repository root, with own `$target`, task-local `$schemaCases`, and environment `CARGO_PROFILE_DEV_DEBUG=0`, `CARGO_PROFILE_TEST_DEBUG=0`, `CARGO_INCREMENTAL=0`:

```powershell
$env:LOCALLORE_GUARDED_SCHEMA_OUTPUT = $schemaCases
cargo +1.93.1 test -p locallore --locked --offline --target-dir $target
cargo +1.93.1 test -p locallore --all-features --locked --offline --target-dir $target
cargo +1.93.1 clippy -p locallore --all-targets --locked --offline --target-dir $target -- -D warnings
cargo +1.93.1 clippy -p locallore --all-targets --all-features --locked --offline --target-dir $target -- -D warnings
cargo +1.93.1 fmt --all -- --check
git diff --check
```

Default **152 passed**, all-features **187 passed**, zero failures/ignores in final full runs; strict Clippy both modes/fmt/diff PASS. Counts include five new integration tests and existing 2.1/context/capture/inspection/branch/replay/guard tests. The five new tests cover:

- Real production request capture for all eight supported action operations, exact IDs/arguments, name alias, quantity 2, wait 100; unsupported, negated, compound, ambiguous, case-sensitive invalid IDs and illegal mechanics still stop before roles.
- Wrong but otherwise valid provider commands rejected without substitution; provider failure leaves state unchanged.
- Identical request-bound schema during the single malformed-output repair, exhausted repair, cancellation before/during provider, unchanged narrator budget and no cancelled commit.
- Actual frozen 2.2 receipt strict restore/replay/retry with zero calls, rejection as fresh prepared commit, unknown-version/effect tamper refusal, mixed 2.2+2.3 history, and fork-local current continuation retaining the exact ancestor receipt.

An initial new-test expectation incorrectly called uppercase `Potion` UnknownReference; existing Engine correctly returns Inventory. The test expectation was corrected after the observed 4-pass/1-fail run, with no production change. All subsequent focused/full runs passed. This is test setup correction, not a weakened gameplay guard.

### Actual pinned converter, no model

The production-path Rust test optionally writes only synthetic captured schemas and test values to `LOCALLORE_GUARDED_SCHEMA_OUTPUT`. That environment/file output exists exclusively in an integration test. `scripts/tests/guarded_director_grammar.cpp` consumes these values, applies the same existing `schema_order.h` as the worker, invokes the actual pinned converter and grammar machine with null vocabulary, and checks complete character acceptance. This is native grammar execution, not a regex approximation, native worker generation, model inference, app IPC or a rendered UI.

Read-only existing clean vendor: llama.cpp `620d2225cc436ab0b001e3200e590e3b286ef9ab`. Existing MSVC 19.34.31937.0 x64 (toolset directory 14.34.31933) / Windows SDK 10.0.19041.0 and static libraries from the accepted worker reproducibility build were reused; no vendor/build/worker file was changed. Standalone test executable is task-local, not packaged. Actual output: **10 cases / 70 native grammar assertions passed / model_loaded=false**. Cases cover the nine action requests above plus escaped exact Dialogue; empty/multiple commands, altered operation or each argument, extra fields and wrong speech/audience reject. No narrator rule changed. Final generated cases SHA256 `a4b66fe0ec00fef809ca18c95f930e5a6c8c5c958b4942ebeafe786b21b5d738`; test executable SHA256 `56604f3124a90abed26fe4be48c25eb497990f7d59e7275af999e2122fa0af4e` (test identity only, not a packaged worker identity).

Reproduce using the existing pinned vendor/build and a configured x64 MSVC environment (replace only the task-owned/source/build paths):

```powershell
$includes = @('native/llama-worker', "$vendor/src", "$vendor/common", "$vendor/vendor", "$vendor/include", "$vendor/ggml/include")
$args = @('/nologo','/EHsc','/std:c++17','/O2','/MD')
$args += $includes | ForEach-Object { '/I' + (Resolve-Path -LiteralPath $_).Path }
$args += @('scripts/tests/guarded_director_grammar.cpp', "/Fe$out/grammar-test.exe", "/Fo$out/grammar-test.obj", '/link')
foreach ($lib in @('llama/common/llama-common.lib','llama/src/llama.lib','llama/ggml/src/ggml.lib','llama/ggml/src/ggml-cpu.lib','llama/ggml/src/ggml-base.lib','llama/common/llama-common-base.lib','llama/vendor/cpp-httplib/cpp-httplib.lib')) { $args += Join-Path $build $lib }
$args += @('kernel32.lib','user32.lib','gdi32.lib','winspool.lib','shell32.lib','ole32.lib','oleaut32.lib','uuid.lib','comdlg32.lib','advapi32.lib')
& cl.exe @args
& "$out/grammar-test.exe" $schemaCases
```

Run the Rust focused test first if only converter cases are needed: `cargo +1.93.1 test -p locallore --test guarded_director_schema --locked --offline --target-dir $target`. File schemas are the actual production inputs captured by its synthetic provider, not alternate schema implementations. Logs, generated cases and executable stay local in task output `guarded-schema`.

## Limits and next gate

Unsupported/ambiguous natural language remains a finite-guard false-negative limitation. Exact action constraints cannot establish model enjoyment, distinct voices, useful prose or reduced fallback. Historical accepted curated cohort results remain unchanged: failures and dependent skips are retained; they are not rerun/reclassified by this packet. No new model quality, latency or success-rate claim is made.

No Android build/device, native WebView, real-worker/model generation, full workspace/Store consumer compatibility or network-block qualification was executed here. Coordinator owns broad integration and independent review. A fresh source-bound cohort may run only after explicit authorization, with unchanged curated fixtures/expected commands, approved assets and existing budgets; it must report failures/fallback honestly. Full M05/D04 checklists and phone gates remain unchecked.

Final fetch observed main `59fa8e898a85bbdae7bbbd3ad34d576bbd8ef4d8` (#98). This packet remains tested against its captured base; coordinator must reconcile subsequent accepted work before integration.

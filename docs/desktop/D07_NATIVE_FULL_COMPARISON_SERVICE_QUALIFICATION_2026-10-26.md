# Native full-comparison service qualification

Supporting D07.03/.06/.04 under #29, coordinator claim6425826959.
**DRAFT / PARTIAL QUALIFICATION.** Evidence cutoff: source
`a2610a49917e489034a78ae7ac0bc1389356963e`. This document records terminal
results reported by the coordinator; its documentation author ran no checks,
applications, models or devices and read no active execution artifacts.

The native Rust service and closed command adapter are implemented. Direct
service tests and command-parser tests are separate evidence categories.
**Actual native IPC, native-model UI, OS confirmation dialogs and WebView
rendering were not exercised in this slice.** The existing full-comparison
frontend remains scripted. No whole-D07, model-quality, phone or release gate
is completed by this record.

## Scope and authoritative interfaces

The [frozen service/IPC contract](D07_NATIVE_FULL_COMPARISON_SERVICE_CONTRACT_2026-10-26.md)
was committed as `de959afe`. Accepted scripted PR211/main `6099135e` is the
compatibility base, not evidence of this new native consumer.

- Native IndexV2 and scripted IndexV1 coexist in the existing
  `comparison-evaluations/<uuid>` namespace. Both lanes share the32-run cap and
  client-identity constraints. Each catalog validates entries before lane
  filtering; a malformed opposite-lane entry fails closed. V1 serialized shapes
  remain distinct from V2; an opposite-lane token is not reinterpreted.
- `evaluation_comparison_native` accepts the11 closed object-valued actions
  from the contract. Status/catalog wireV2 identifies `approved_native`.
  Execution confirmation and managed-reader spoiler confirmation are independent
  native decisions. Parser tests do not exercise either decision through IPC.
- The adapter calls the existing shared `literal_v3::run_native_comparison`.
  It reuses the existing EvaluationManager Job/worker, ModelManager reservation,
  actual cleanup witness and generic cleanup. Accepted and rejected uncertain
  handoffs retain the exact reservation/runtime Arc or its native witness before
  worker ownership can be released, including after presentation retirement.
  There is no second owner registry, provider, compiler, memory implementation
  or persistence path.
- Presentation close is not proof of child/runtime cleanup. Native status
  separates `running`, `cleanup_required`, `cleanup_running` and bounded `cause`.
  Confirmed cleanup cannot invent a missing publication or automatically resume.
- The correction catches a fixed consent-callback panic only **before** the
  reservation/assets boundary. It does not introduce a blanket post-owner catch
  that could flatten an unknown owner into an error string. Actual directory
  pin `Vec<File>` values remain held through the producer/consent lifetime.
- Binding validation uses the known Rust protocol/descriptors/budget shape,
  substituting only syntactically valid source/suite digests when checking
  historical metadata. Well-formed historical hashes are not a current-source
  execution grant; matching outer index/manifest labels cannot validate an
  impossible inner binding.

## Frozen packets and terminal chronology

Primary durable work-log records:
[initial freeze/compiler refusal](https://github.com/OptimumAF/LocalLore/issues/29#issuecomment-6426136656)
and [review findings, RED and correction](https://github.com/OptimumAF/LocalLore/issues/29#issuecomment-6426804511).
Subsequent lint results below are coordinator-reported terminal observations
supplied with this documentation allocation. They are not independent reruns.

| Source/checkpoint | Actual terminal result | Interpretation |
|---|---|---|
| Parser packet `324386b4` adopted `ed1a60b8`; service packet `1d055f6d` adopted `1f01fc83`; registration `1ea9b522` | Exit101;51 missing-API/type/Action compiler errors; **no tests executed** | Expected absence of implementation. This is compile refusal, not behavioral RED. |
| First implementation `cea16866` | Original native-service8/8 passed,3.40s; parser8/8 passed | Direct service/fixed-owner and parser evidence, not real-model execution or native IPC. |
| Binding packet `abdf301a` registered `ad65e645` |1 passed /4 failed | Coherently changed outer metadata incorrectly admitted inner protocol2, an unknown forwarded-budget version, a changed role cap or malformed digest. |
| Consent/pin packet `b9727d04` registered `6be84bc6` |1 passed /1 failed,15.80s | Consent panic stranded the actual Job's running state. The pin/rename-refusal case **already passed baseline**; this run did not demonstrate a rename exploit. |
| Correction `75d04e36` | Native-service15/15 passed,9.91s | Original8 + binding5 + boundary2. No assertions were removed to turn the failures green. The expected caught fixed-panic hook diagnostic remains in the passing log. |
| Strict lint check1 at `cea16866` | Failed: `large_enum_variant` | Retained failed lint result; preparation fields were subsequently boxed. |
| Strict lint check2 at `75d04e36` | Failed: test `type_complexity` and `vec_box` | Test representation/style findings, not a passing lint run. |
| Named test retention holders `a2610a49`; strict lint check3 | Passed,7.57s | Named holders preserve the actual returned boxed owner and retained managers. They do not discard or replace the payload to satisfy lint. |
| Unchanged clean `a2610a49`; full frontend | Passed,15.725s; coordinator log label `d07-native-full-port-frontend-first1` | Scripted frontend/strict consumer compatibility; no new native-model UI or native IPC evidence. |
| Same `a2610a49`; native `commands::` filter |63 passed /0 failed,3.11s | Includes new and legacy closed command parsers; this overlaps the focused parser coverage above and is not63 actual IPC calls. |

The default native-service packet exercises mixed-lane metadata, combined quota,
opposite-lane refusal, grant/epoch/consent/cancel boundaries, actual denied-prefix
source/budget refusal, and accepted/rejected ownership retention with generic
cleanup. Fixed protocol children and explicitly installed test payloads are
plumbing evidence. They do not establish that a real-model shared producer
returned that payload or that generated prose is satisfactory.

The command-parser packet exercises11 typed actions, exact keys, UUID and numeric
bounds, the4096-byte object-query boundary, and rejection of renderer-supplied
assets, execution consent or cleanup authority. Parsed `serde_json::Value`
cannot detect duplicate raw keys already overwritten by the transport.

Exact local terminal-log paths, SHA256 values, executed command transcripts and
host/tool versions remain for the coordinator's final evidence appendix. None
are fabricated here. Source dependency pins are not runtime version observations.

## Approved-asset and historical evidence boundary

Four independent ignored asset-service oracles were frozen in `dba74a13` and
adopted as `182175a5`, in
`apps/desktop/src-tauri/src/models/literal_native_asset_tests/full_comparison_service_assets.rs`.
They are **ignored and unrun at this cutoff**:

1. Fresh actual native service, paired batch1.
2. Fresh actual native service, rollout batch1.
3. Separately allocated explicit paired partial resume3 using a genuine
   current-source service root/run.
4. Separately allocated completed-native service resume with empty Models asset
   directories, zero confirmation/reservation sequence change and unchanged
   durable inventory.

The initial future allocation is at most the first two invocations, one paired1
and one rollout1, using already approved installed assets. **Neither has launched
at this evidence cutoff.** Registration/compilation of ignored tests is not an
asset run. Resume3 and a fresh completed-current-source zero-reservation proof
require additional explicit allocation and genuine provenance; they are not
implicitly admitted by an ignored-suite command.

Accepted PR197 paired/rollout native Core cohorts are genuine historical
evidence. Later shared selected2 source changes make them out of date for the
current compiled binding. They cannot be copied, relabelled or counted as the
current-source completed-native zero-asset fixture. Incomplete full-comparison
recovery may still reserve/load even when recovered turns generate zero roles;
the stronger selected-case recovery optimization is not claimed here.

## Reproduction commands and pending gates

These are source-based reproduction commands, **not commands executed by the
documentation author**. Run from the repository root on the qualified Windows
host, with an existing task-owned external target directory and temporary
directory. Replace the placeholders locally; do not publish personal paths or
raw prompts. Exact executed transcripts remain pending coordinator attachment.

```powershell
$env:CARGO_TARGET_DIR = '<OWNED_EXTERNAL_TARGET>'
$env:TEMP = '<OWNED_TEMP>'
$env:TMP = $env:TEMP
$env:CARGO_BUILD_JOBS = '1'
$env:CARGO_INCREMENTAL = '0'
$env:CARGO_PROFILE_DEV_DEBUG = '0'
$env:CARGO_PROFILE_TEST_DEBUG = '0'
$env:LIBSQLITE3_FLAGS = ''
cargo test --locked --offline --manifest-path apps/desktop/src-tauri/Cargo.toml --all-features --bin locallore-desktop-spike evaluation::comparison_run::native_review_tests:: -- --nocapture --test-threads=1
cargo test --locked --offline --manifest-path apps/desktop/src-tauri/Cargo.toml --all-features --bin locallore-desktop-spike comparison_native_commands::review_tests:: -- --nocapture --test-threads=1
cargo clippy --locked --offline --manifest-path apps/desktop/src-tauri/Cargo.toml --all-targets --all-features -- -D warnings
```

The two initially allocated asset checks must be launched individually only
after the coordinator records admission. They require explicit existing
`LOCALLORE_SELECTED_NATIVE_TEST_RESOURCES` and
`LOCALLORE_SELECTED_NATIVE_TEST_MODEL` environment paths; no download or model
copy is implied. The exact test names are
`approved_service_paired_first_scene_returns_with_actual_owners_drained` and
`approved_service_rollout_first_scene_returns_with_actual_owners_drained`.
Use the same manifest/binary/all-features selection with one exact full filter
`models::literal_native_asset_tests::full_comparison_service_assets::<test_name>`
and `-- --ignored --exact --nocapture --test-threads=1`. Do not launch all ignored
tests. The other two also require the genuine
`LOCALLORE_FULL_NATIVE_TEST_ROOT` / `LOCALLORE_FULL_NATIVE_TEST_RUN_ID` from a
separately admitted current-source service run.

| Gate | Status at source/evidence cutoff |
|---|---|
| Frozen direct service/parser groups and corrected strict lint | Terminal results above; narrow source distinctions retained. |
| Existing/new command-parser compatibility | `commands::`63/0 at `a2610a49`, as recorded above. |
| Legacy scripted service11 and unfiltered Rust suites | Pending final coordinator runs and exact source attribution. |
| Full frontend/strict TypeScript | Terminal full frontend pass at `a2610a49`; unchanged scripted frontend is not native-UI evidence. |
| Format and restored normal native build | Pending final coordinator checks. |
| Android Rust host compatibility and host build graph | Pending; no Android runtime/JNI/phone claim. |
| Current approved-asset service execution and exact actual counts | Not launched; four ignored oracles are not four successful invocations. |
| Fresh completed native service/no-reservation fixture | Pending fresh current-source data and separate allocation. |
| New native command through actual IPC, OS consent and native WebView UI | Not executed; native UI exposure is outside this service/IPC-port slice. |
| Broad source closure, independent review, focused PR/acceptance | Pending coordinator reconciliation. |

An additional missing-assets oracle was independently frozen as `35ae3967`,
adopted `b938062e` and registered/formatted `8d0c94bf` after this source cutoff.
Its first execution has no terminal result supplied for this draft. It is not
counted as passing or as an approved-asset run. The coordinator reports no
production change after `75d04e36`; the later holders and missing-assets packet
are test-only changes. Their outcomes still need exact source attribution.

Generated synthetic fixtures, stdout/stderr and raw captures stay local and
ignored. Human quality, latency/RAM acceptance, native-dialog responsiveness,
phone parity, whole-app performance, whole D07 and release readiness remain
unqualified. The next runnable coordinator gate is terminal compatibility/source
closure followed by the explicitly recorded first approved-asset invocations;
this document does not authorize or perform them.

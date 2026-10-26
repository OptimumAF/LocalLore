# Native full-comparison service qualification

Supporting D07.03/.06/.04 under #29, coordinator claim6425826959.
**PARTIAL QUALIFICATION / FINAL COORDINATOR APPENDIX PENDING.** Updated through
terminal evidence at `9920d48cccde747eb556b58a835b579205bff744`, retaining the
earlier `a2610a49` cutoff and failures below. All executions belong to Root;
the documentation author read terminal records/tracked source and ran no checks,
applications, models or devices. The active `native-ui1` artifacts/images were
not read and their result is not inferred.

The native Rust service and closed command adapter are implemented. Direct
service tests and command-parser tests are separate evidence categories.
Actual approved-model Rust service invocations and completed recovery are now
measured separately below. **New native IPC/WebView evidence is still pending;
native-model UI and OS confirmation dialogs are not qualified here.** The
ordinary full-comparison frontend remains scripted. No whole-D07, model-quality,
phone or release gate is completed by this record.

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
| Missing-assets oracle `35ae3967`, adopted `b938062e`/registered `8d0c94bf` |1 passed,0 failed,241 filtered;0.42s tests/17.82s build | Actual affirmative consent with absent model/resources returns NativeUnavailable; no scripted fallback. This is not an approved-asset or runtime-child run. |
| Strict lint check4, `d9fd9443` | Passed;11.74s Cargo/12.046390s command | Narrow terminal strict check, not the pending final source-wide qualification. |
| Admission interleavings `133059a5`/registration `37ddfd05` |0 passed/2 failed,242 filtered;0.11s tests/20.00s build | A stale cross-lane same-client request returned global Busy instead of its precise InvalidEvaluationInput conflict. Both orders retained the original Job/files. |
| Admission correction `7039315a` |2 passed,0 failed,242 filtered;0.12s tests/19.00s build | Conflict check moved inside registration before global Busy; same-lane exact retry and unrelated Busy remain distinct. |
| Wired helper/frontend `9920d48c` | `verify-frontend.mjs` exit0,15.5703653s command | Includes strict typechecking of the new fixed IPC helper; no actual IPC, app, image or model execution follows from this frontend gate. |

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

The missing-assets case observes terminal status plus actual Eval/Models
`cleanup_complete()` without a cleanup action before its assertions. It permits
a real reservation before pre-child asset validation and an empty native
diagnostic report/setup; neither is generated turn evidence. The admission-race
tests use a private fixed interleaving/hold, not a claim about measured OS timing.
They generate no native model work. The evidence inventory/hash appendix below
binds the retained early records; source dependency pins are not tool-version
observations.

## Measured approved-asset service and completed recovery

Four independent ignored asset-service oracles were frozen in `dba74a13` and
adopted as `182175a5`, in
`apps/desktop/src-tauri/src/models/literal_native_asset_tests/full_comparison_service_assets.rs`.
They remain ignored by default. At the initial `a2610a49` cutoff all four were
unrun. Root subsequently recorded individual admission and executed them with
the existing approved installed assets, never a blanket ignored-suite launch:

1. Fresh actual native service, paired batch1.
2. Fresh actual native service, rollout batch1.
3. Separately allocated explicit paired partial resume3 using a genuine
   current-source service root/run.
4. Separately allocated completed-native service resume with empty Models asset
   directories, zero confirmation/reservation sequence change and unchanged
   durable inventory.

| Actual case/source | Rust result, build and command elapsed | Actual retained report / new work |
|---|---|---|
| Fresh paired1, `d9fd9443e86a290dc41a725e2e0aaf61e7a508b1` |1 passed/0 failed/0 ignored/241 filtered;260.62s tests,0.90s build,261.7325559s command |1 scene/12 outcomes;22 roles,10 scenario passes,1 load/setup; phases10 committed/2 failed. |
| Fresh rollout1, same `d9fd9443` |1 passed/0 failed/0 ignored/241 filtered;129.89s tests,0.76s build,130.8604496s command |1 scene/12 outcomes;19 roles,8 scenario passes,1 load/setup; phases8 committed/3 failed/1 dependency-not-run. |
| Explicit paired resume3, same `d9fd9443` and actual paired service root/run |1 passed/0 failed/0 ignored/241 filtered;751.11s tests,0.72s build,752.0276427s command |Cumulative4 scenes/48 outcomes,77 roles,40 scenario passes,2 loads/setups,15 narration fallbacks; phases35 committed/12 failed/1 cancelled. |
| Completed paired resume with empty Models directories, `9920d48cccde747eb556b58a835b579205bff744` |1 passed/0 failed/0 ignored/243 filtered;75.09s tests,20.03s build,95.8771780s command |Adds0 confirmation calls,0 reservations/roles; original complete report and whole fixture-root byte inventory unchanged. Existing77 roles/2 setups are retained history, not new work. |

Scenario passes are fixture assertion results, not a count of all successful
canonical commits or human judgments. The paired resume row is cumulative and
includes the first paired scene; do not add22 to77 as new work. Failed outcomes,
agency failures, construction-receipt failures, dependency skips and cancellation
remain visible. The15 fallback count is also cumulative. Every measured report
has `human_reviewed=0` and `quality_accepted=false`; a passing Rust ownership/run
test does not waive scenario failures or establish narrative quality.

Fresh tests assert one actual reservation sequence increment, one confirmation,
one setup and actual native profile/role limits. The service wait observes
terminal publication **and** actual evaluation/model cleanup completion before
`close_manager`; it does not use helper cleanup to manufacture a passing return.
The async worker's final instructions may finish after its terminal status is
published. Unknown ownership instead retains both actual manager Arcs and blocks
later asset admission. These are this application's tracked-owner observations,
not an OS-wide no-process/no-leak proof.

The resume3 test uses the genuine paired service result, validates its current
source and preserves the full actual paired reference inventory. The completed
test supplies empty model/resource directories and asserts both zero callback
calls and unchanged private `evaluation_sequence`, not merely successful absence
of asset files. It compares the actual shared report and complete fixture-root
inventory. Its75.09s includes cold validation/inspection, not a generation
latency benchmark.

Root read the same Core binding from paired/rollout reports:
`e03aec2c38db6a1272a9ca8171b29c1156c9fb02c74331a1a56d5f39fdf9c9e9`.
There are no shared Core/evaluator source changes in the later desktop-only
`d9fd9443..9920d48c` delta. Fresh generation/resume at `d9fd9443` and completed
recovery at `9920d48c` remain separately attributed. Coordinator-read final
durable report SHA256 values are paired
`608d50866137ab1ae3ef0f7cf5e3f5bba8c14ee99ec9739f078edb1d18f48fed`
and rollout
`2c06f377d9490599b7f280495c8393f0b959a505f04fc89e96019a2542b67e6c`.
The documentation author did not read those generated report bodies.

Accepted PR197 paired/rollout native Core cohorts are genuine historical
evidence. Later shared selected2 source changes make them out of date for the
current compiled binding. They cannot be copied, relabelled or counted as the
current-source completed-native zero-asset fixture. The new service-owned
completed test uses the separately generated current cohort above. Incomplete full-comparison
recovery may still reserve/load even when recovered turns generate zero roles;
the stronger selected-case recovery optimization is not claimed here.

## Reproduction commands and pending gates

These reflect the terminal command shapes, **not commands executed by the
documentation author**. Run from the repository root on the qualified Windows
host, with an existing task-owned external target directory and temporary
directory. Replace the placeholders locally; do not publish personal paths or
raw prompts. Root observed Rust/Cargo1.93.1 (LLVM21.1.8), Node24.22.1,
PowerShell7.6.5, Windows NT10.0.26300 x64 and Intel i7-12700K
(12 cores/20 logical processors). These observations were supplied by Root,
not freshly queried by this document author. Existing pinned dependencies were
used; no upgrade, install or new asset is implied.

```powershell
$taskNativeTarget = '<OWNED_EXISTING_EXTERNAL_TARGET>'
$env:TEMP = '<OWNED_TEMP>'
$env:TMP = $env:TEMP
$env:CARGO_BUILD_JOBS = '1'
$env:CARGO_INCREMENTAL = '0'
$env:CARGO_PROFILE_DEV_DEBUG = '0'
$env:CARGO_PROFILE_TEST_DEBUG = '0'
$env:LIBSQLITE3_FLAGS = ''
cargo test --locked --offline --manifest-path apps/desktop/src-tauri/Cargo.toml --all-features --jobs 1 --target-dir $taskNativeTarget --bin locallore-desktop-spike evaluation::comparison_run::native_review_tests:: -- --nocapture --test-threads=1
cargo test --locked --offline --manifest-path apps/desktop/src-tauri/Cargo.toml --all-features --jobs 1 --target-dir $taskNativeTarget --bin locallore-desktop-spike comparison_native_commands::review_tests:: -- --nocapture --test-threads=1
cargo clippy --locked --offline --manifest-path apps/desktop/src-tauri/Cargo.toml --all-targets --all-features --jobs 1 --target-dir $taskNativeTarget -- -D warnings
```

The asset checks must be launched individually only after the coordinator
records admission. They require explicit existing
`LOCALLORE_SELECTED_NATIVE_TEST_RESOURCES` and
`LOCALLORE_SELECTED_NATIVE_TEST_MODEL` environment paths; no download or model
copy is implied. The exact test names are
`approved_service_paired_first_scene_returns_with_actual_owners_drained` and
`approved_service_rollout_first_scene_returns_with_actual_owners_drained`.
Use this exact single-test command shape, substituting one of the four names;
do not launch all ignored tests:

```powershell
cargo test --locked --offline --manifest-path apps/desktop/src-tauri/Cargo.toml --all-features --jobs 1 --target-dir $taskNativeTarget --bin locallore-desktop-spike 'models::literal_native_asset_tests::full_comparison_service_assets::<test_name>' -- --ignored --exact --nocapture --test-threads=1
```

The later exact names are
`approved_existing_service_paired_partial_explicit_resume_three_completes` and
`genuine_completed_service_resume_has_zero_consent_reservation_and_byte_changes`.
Both require the genuine
`LOCALLORE_FULL_NATIVE_TEST_ROOT` / `LOCALLORE_FULL_NATIVE_TEST_RUN_ID` from a
separately admitted current-source service run. Use an actual locally recorded
run, never a synthetic/historical substitution. The profile is the existing
approved CPU4/context4096/Director350+Narrator350/repair1 profile, with compiled
120s preparation and32-admission/96-role/30-minute-per-arm limits. Caps are not
measurements or a phone simulator. Completed empty-Models recovery does not
require installing/copying assets.

Root's terminal focused filters were `unavailable_review_tests::` and
`evaluation::comparison_run::native_review_tests::admission_race_review_tests::`.
The frontend command at `9920d48c`, from `apps/desktop`, was the existing approved
Node executable with `verify-frontend.mjs`; it passed strict frontend checks and
the current synthetic controller/SSR cases. New
`comparison-native-port-journeys.ts` is source/typechecked at this cutoff;
the currently running actual app-owned IPC cohort and its18 capture reviews
remain excluded until Root supplies terminal evidence.

| Gate | Status at source/evidence cutoff |
|---|---|
| Frozen direct service/parser groups and corrected strict lint | Terminal results above; narrow source distinctions retained. |
| Existing/new command-parser compatibility | `commands::`63/0 at `a2610a49`; final source-wide rerun pending. |
| Legacy scripted service11 and unfiltered Rust suites | Pending final coordinator runs and exact source attribution. |
| Full frontend/strict TypeScript | Terminal passes at `a2610a49` and wired `9920d48c`; synthetic/typecheck evidence, not native-model UI. |
| Format and restored normal native build | Pending final coordinator checks. |
| Android Rust host compatibility and host build graph | Pending; no Android runtime/JNI/phone claim. |
| Current approved-asset service execution and exact actual counts | Paired1, rollout1 and separately admitted paired resume3 terminal; scenario failures retained above. |
| Fresh completed native service/no-reservation fixture | Terminal1 pass at `9920d48c` with empty Models/zero sequence change/full byte equality. |
| New native command through actual IPC and18-image review | Active coordinator cohort, pending/excluded; no result inferred or artifact read here. |
| Native-model UI and actual OS consent | Not qualified by direct Rust service/consent-double tests. |
| Broad source closure, independent review, focused PR/acceptance | Pending coordinator reconciliation. |

The later `7039315a` admission correction is a real desktop producer change;
do not retain the earlier blanket statement that all later commits were test-only.
The paired/rollout/resume3 runs predate it at `d9fd9443`; completed recovery and
frontend wiring are attributed to `9920d48c`, which includes it. The known prior
failures remain above. Final Rust/native/Android/format/restoration/PR closure
will be appended by the coordinator after terminal checks.

## Terminal evidence pins

Local artifacts stay ignored; table names are under `<artifact-root>` only.
`d07-native-full-port-terminal-inventory1.json` binds the earlier logs/commands,
terminal source cleanliness and retained failures; SHA256
`3f1e9dfd1354fc68d8f25b1f0383c50b3279e5b77542220b05dcdf8cd963c6b5`.
New terminal log/process SHA256 values independently read by the document author:

| Prefix (append `.log` / `-process.json`) | Log SHA256 | Process SHA256 |
|---|---|---|
| `d07-native-full-port-unavailable1` | `e72dc41ad509094a3a9f59ff88faa6ca6860498da34f7cb66dcce25d5970c6ca` | `314f1ae637d24609a2ad25c33caa0dce693eba1de86598aa8d7d0040a38666ba` |
| `d07-native-full-service-model-paired1` | `b7d8bf072f6c6108512c3fa69e9e4f5838cf14fe108aec2b7541ddffa0a39cb6` | `c7ef5d4a2944cefef8eee5014a3fadd6085c92009b6b4516f8b76851147146d8` |
| `d07-native-full-service-model-rollout1` | `e9442260e460fe1b3a07eb81a28a24f31aaadce12a6aa18777e87410f55061a4` | `85605b04325ef5597053e016211043c0d7f173ee0aeba41b4a0e3400b836e466` |
| `d07-native-full-service-model-resume3` | `d19dd8a88656621fa45eb6cfdadcada50fbbeae6340025cc0a5fee76e92c532c` | `2fb17d8948ce3889d38e64a9153554fe7f19240f9dc1b098c8196dc8093acc2a` |
| `d07-native-full-service-model-completed1` | `e0df7a605dba8f6d098a381874f2daf0190ebae2f5cf13fc9fcaad7c518a0591` | `c2764cca874819b05adeb0bd777f8fa78e0cb7de76fa90bffbe61065fd870f1a` |
| `d07-native-full-admission-race-red1` | `2123754a47087ce1d143c713688a0ea0935e5a4ca45b0f036ea31d4f1b73584b` | `7efd85a96ccbec39f25ccb83d5761573667f2c648b837ec4d9baaf6acbf63e1b` |
| `d07-native-full-admission-race-green1` | `a2811baa5caf496c6d099fb5b39665b723d1301198eb5202c2382dbaf3b3f0ca` | `b590e83ad8c74763590323717c408afaa60d8aac445ba4b3cca6798a6c291a06` |
| `d07-native-full-port-frontend-wired1` | `e56f3570b262c0eed60807ae3efbe74ff29ffdd6e328730501deaf15d7292f91` | `5e7283ad2188ac00f16872985756c373c814c7675a212276d4f33990fabb9e08` |

Generated synthetic fixtures, stdout/stderr and raw captures stay local and
ignored. Human quality, latency/RAM acceptance, native-dialog responsiveness,
phone parity, whole-app performance, whole D07 and release readiness remain
unqualified. The next coordinator gate is terminal IPC/capture review and final
compatibility/source closure. This document neither authorizes new model/UI
invocations nor awards milestone or owner acceptance.

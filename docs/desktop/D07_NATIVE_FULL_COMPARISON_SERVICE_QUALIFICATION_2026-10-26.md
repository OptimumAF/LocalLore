# Native full-comparison service qualification

Supporting D07.03/.06/.04 under #29, coordinator claim6425826959.
**SCOPED LOCAL CHECKS COMPLETE / PR ACCEPTANCE TRACKED IN PR214.** The final
coordinator appendix below supersedes earlier pending check statuses. Updated through
terminal UI evidence at `84eb739f372be2befe5ddfc1ce82aabcb300287d`, retaining the
earlier `a2610a49`/`9920d48c` cutoffs and failures below. All executions belong to Root;
the documentation author read terminal records/tracked source and ran no checks,
applications, models or devices. For this followup the author read only terminal
UI1/UI2/UI3 records/reports and Root's visual-review manifest, not the images or
the running final native-suite artifacts.

The native Rust service and closed command adapter are implemented. Direct
service tests and command-parser tests are separate evidence categories.
Actual approved-model Rust service invocations and completed recovery are now
measured separately below. **The fixed non-generating native IPC checks and
scripted-inference WebView cohort are now terminal; native-model UI and OS
confirmation dialogs are not qualified here.** The
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
(12 cores/20 logical processors), with66796484 KiB visible RAM. Visible host RAM
is not an app-residency/peak-memory measurement. These observations were supplied by Root,
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
`comparison-native-port-journeys.ts` was source/typechecked at that cutoff;
its later actual app-owned IPC and18-capture evidence is separately attributed
to `84eb739f` below.

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
| New native command through actual IPC and18-image review | UI3 terminal at `84eb739f`: fixed non-generating native calls, scripted-inference app workflow,18 images individually reviewed by Root. |
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
unqualified. The next coordinator gate is final
compatibility/source closure. This document neither authorizes new model/UI
invocations nor awards milestone or owner acceptance.

## Coordinator denial-fixture correction

The first actual hidden WebView/native IPC attempt at clean/unchanged `9920d48c`
failed before any capture at `native-port-lab_denied-actual-lab-grant-required`.
The app exited1 after1.353s, with24 stdout bytes (fixed FAIL marker), zero stderr,
no timeout/overflow, and no restart stage. Both frontend and native builds passed.
The original report did not retain the differing raw reply, so its alternative
category is unknown. No PNG was generated. This attempt is retained as
`d07-native-full-port-native-ui1`; it is not native qualification.

The test had assumed that displaying Play revoked the backend grant. Source
inspection showed the existing desktop Host is constructed with Story Lab
capability enabled; the UI mode does not change that construction grant. This
was an invalid denial-fixture premise, not a demonstrated production permission
bypass. The original failing assertion was retained in the separate denial case.

Test-only `5eeba4a608e39d33c0f8525381de84cf45efcbd9` adds a fixed denial subcohort.
Only an active full-comparison development harness using the memory fixture and
`LOCALLORE_D07_NATIVE_DENIED_GRANT=1` constructs `Host(false)`. There is no grant
mutation RPC, and normal native construction is unchanged. That fresh app must
read actual native context with grantfalse, observe catalog Forbidden and real
cleanup availability, reject malformed authority input, then dispose without
images, generation or dialogs. The ordinary initial/restart apps keep their
actual native grant, separately verify the new native command and scripted-token
isolation, and retain the18 required app-owned captures. Every generated image
still requires individual inspection.

The corrected full frontend/strict TypeScript/normal-hook-exclusion check passed
at clean/unchanged `5eeba4a6` in17.103s, coordinator label
`d07-native-full-port-frontend-denied1`. Corrected actual IPC/native rendering,
all-image review, unfiltered native tests, final strict checks, Android Rust
compatibility and normal-build restoration remained pending at this historical
appendix. The subsequent terminal IPC/rendering results follow; final source-wide
checks are still pending.

## Terminal UI2 failure and UI3 correction

UI2, `d07-native-full-port-native-ui2`, ran at clean/unchanged
`adf1e1b47835f6ec18576d82cd00d05073f8f185` in cohort
`full-comparison-native-86d13752-db66-4a2f-88fd-a5e0c8626ec0`. The denial app
recorded9 check entries: actual grantfalse, catalog Forbidden, both empty cleanup
operations and malformed authority-input checks passed; disposal then recorded
one unexpected native Forbidden at `native-port-denied-disposed-without-error`.
It exited1 after1.234s, with zero stderr and no PNG, timeout or overflow. Neither
ordinary initial nor restart stage ran. This is retained failure evidence, not
an access-control bypass.

Tracked `CaptureController.dispose()` calls session-scoped revoke, whose request
is `trace_capture_revoke`; a session created against the denial Host can therefore
explain the disposal Forbidden. No runtime command trace was retained, so this
is source-supported attribution, not proof of which command emitted that error.
At `84eb739f`, the denial branch runs before session creation. The same narrow
delta finds the ordinary initial report by `stage === "initial"` instead of
assuming `reports[0]`, now occupied by the denial stage. That restart-index issue
was found in source, not observed as a runtime RED: UI2 never reached restart.

UI3, `d07-native-full-port-native-ui3`, completed at clean/unchanged
`84eb739f372be2befe5ddfc1ce82aabcb300287d`, cohort
`full-comparison-native-4e901ae1-d76a-40fc-97a2-d87a3892d8a0`.
The process record spans `2026-10-26T21:44:18.5368094Z` through
`2026-10-26T21:56:12.7723929Z`, exit0. These are bounded fixture/cohort elapsed
times, not whole-app or model-performance benchmarks.

| Actual UI3 app stage | Recorded check entries | PNGs | App elapsed / exit | Frontend error buffer |
|---|---:|---:|---|---|
| Denied |10|0|1.201s /0|0|
| Initial |239|14|590.045s /0|1 deliberate Transport lost-ack error|
| Restart |110|4|89.115s /0|0|

The359 entries are repeated recorded assertions across three stages, not359
distinct tests. All three actual hidden/unfocused WebView apps had zero stderr,
no timeout, overflow or spawn error. The frontend/native build steps separately
passed in1.983s/22.716s; the native build retained217 bytes of ordinary Cargo
stderr. Thus zero **app** stderr does not mean every cohort subprocess had empty
stderr, and this run is not a general clean-OS-shutdown or leak proof.

The native-port helper makes actual `evaluation_comparison_native` permission,
empty-catalog, unknown-token and cross-lane refusal calls, plus the single fixed
scripted status read that proves the original scripted identity/readiness
survives. It never submits a valid native start/resume or reaches model/OS-dialog
consent. The ordinary full workflow uses actual controllers, native IPC and
WebView rendering with scripted fake inference and fixed picker/consent doubles.
It is not native-model UI evidence.

After initial and restart, the independently hashed owned Core inventory was
identical:1068 files /15054801 bytes, digest
`e6f12da771a545aeac2cfae4b02e445d931af8307da8ed2cbff9776068db8308`.
Node's post-exit digest/count matched the native report and both stages. This
bounded fixture check does not certify arbitrary Windows link/reparse races:
Node uses lstat/realpath checks, while the native fixture separately uses its
existing reparse-rejecting pins. The UI3 executable SHA256 is
`6f6b6229cb00f59b760e31b4ea3e2508c4b1aab9ca171d67cc84da5f0aab9785`;
launcher SHA256 is
`c50a2fe331d599a7824a68e64a02a4e30732216a6aca2506236decb0d1217bd5`.

Root individually viewed all18 UI3 images; UI1/UI2 produced none. The retained
visual-review manifest reports no visible defect within the captured sections,
including620-pixel narrow wrapping. Native privacy assertions are API evidence,
not conclusions drawn from pixels. The documentation author read the manifest
only. This is not human quality approval or whole-UI/accessibility coverage.

To reproduce the fixed launcher from `apps/desktop`, use existing absolute owned
directories and the approved Node executable, with no CLI arguments:

```powershell
$env:LOCALLORE_D07_FULL_COMPARISON_ARTIFACT_ROOT = '<OWNED_EXISTING_ARTIFACT_PARENT>'
$env:LOCALLORE_D07_FULL_COMPARISON_TARGET_DIR = '<OWNED_EXISTING_EXTERNAL_TARGET>'
$env:TEMP = '<OWNED_EXISTING_TEMP>'
$env:TMP = $env:TEMP
node comparison-run-harness.mjs
```

The launcher fixes its development build, hidden child processes, test flags and
fresh UUID fixture. It does not control the desktop, install dependencies or
download assets. Limits are1 MiB per stdout/stderr stream,900s app watchdog/960s
launcher watchdog,40 captures,16 MiB per PNG and256 KiB JSON; inventory limits
are depth12/8192 entries/8 MiB per file/128 MiB total. These are bounds, not measured
resource use. Real-model UI, OS dialogs, provider-inflight/OS-kill races, quality,
phone and whole-app performance remain unqualified.

## UI terminal evidence pins and remaining gates

Names below are relative to `<artifact-root>`; no raw stories, prompts or private
absolute paths are published. Earlier UI1 failure/fixture correction remains
above. All three process records are terminal; no active final-suite record was
read or hashed for this update.

| Prefix (append `.log` / `-process.json`) | Log SHA256 | Process SHA256 |
|---|---|---|
| `d07-native-full-port-native-ui1` | `f9cd2e6fa3560e66fdf67dc0427d30f03bb32544b890dacc463bd315f061dc60` | `22cd1f7a0824008ca504302b8393b4b8fd15eeba6d48b2b23df67c8e2d96347b` |
| `d07-native-full-port-native-ui2` | `5071c7edd358478ef27dab3344143fa1d1792f530a336864ebcc7206e81dfa14` | `64c089cb973a8ffed9da236ea9d131363aac6a24ae476a3a31646eff44a33bca` |
| `d07-native-full-port-native-ui3` | `528049584fcaa28454845054938fc202e45913c6219fd30803001c1cd9287dca` | `9eba565d3d3a76c6f118328508665914c89e6ed61cb277cc9e85b16d35179be6` |

| Cohort-relative file | SHA256 |
|---|---|
| UI1 `qualification.json` | `88518b8a8c27f7ed7654a84e9dd2117ea67fcc512580a6459be96ba4d47b9281` |
| UI1 `initial/report.json` | `3f4d3d38513146ea3e8c77a03bfbdf9361213a82a301c3af5ea7e61fb3782aab` |
| UI2 `qualification.json` | `34cadbb3efedc2b9f7ce599f62087710db567dc97deef3d4487277af30bb360d` |
| UI2 `denied/report.json` | `46b2d41069a9d3fee26e514988ed3ffb9c24fe5a1f1864896ece6d1248f31c3b` |
| UI3 `qualification.json` | `4e698375ebc88b600bda396f5a4f4c794883274bb1543776d18f0594751fd910` |
| UI3 `denied/report.json` | `41d6f4079bf4ad54d43bd0ec50944018418f65623087fa3a864f78e6616db821` |
| UI3 `initial/report.json` | `8137f6df9bfb833df8d495621a5308243cb50c12ad812c989fc126a759c8482f` |
| UI3 `restart/report.json` | `ddd693aa915a98e3a6d5f124d91a0452d341604b38d9f930c7ca4c0c97be45b2` |
| `<artifact-root>/d07-native-full-port-native-ui3-visual-review.json` | `4d363abbeec492e1cab1fc354cfa93ecf8c97d060b13a9a4201fe833e0b15a84` |

At the UI supplement's cutoff PR214 was draft and the source-wide checks were
pending. The coordinator's terminal results below supersede those local pending
gates. PR214 records subsequent security/owner acceptance. No whole-D07 or
publication readiness is implied by this supporting slice.

## Final coordinator source and compatibility closure

The unfiltered native cohort ran at clean, unchanged
`84eb739f372be2befe5ddfc1ce82aabcb300287d`. It passed235 unit tests, failed0,
ignored9, and passed both separate harness-contract tests. Unit execution took
1302.56s; compilation53.90s; complete command1358.024s. It includes the new
native service/parser/admission cases and preserved scripted/reader/selected
regressions; complementary earlier passes are not added again to this count.
The9 ignored cases are8 explicit installed-asset opt-ins and1 Windows symlink-
privilege case. The four service asset checks above were separately allocated
and actually executed; they were not silently included in the default count.
The other asset/privilege cases were not rerun by this final command.

All remaining checks ran at clean, unchanged
`1805b0a7a6114ec4974f29cb16aaf62e36527781`, whose only difference from84eb is
this qualification document. No implementation or assertion changed after the
235/2 native pass or the18-image UI cohort.

| Coordinator label after `d07-native-full-port-` | Actual terminal result |
|---|---|
| `native-final1` |235 passed /0 failed /9 ignored,1302.56s; separate harness2/0,0.01s |
| `clippy-final1` | All targets/all features, `-D warnings`, passed13.92s |
| `rust-format-final1` | Native/workspace `cargo fmt --all -- --check` passed |
| `frontend-format-final1` | All matched frontend/launcher files passed Prettier |
| `android-host-final1` |20 Rust host adapter tests passed,0 failed,1.84s |
| `android-graph-final1` | Passed;0 occurrences of runtime/llama/LiteRT/Tauri/WebView/Wry packages in normal/build/dev graph |
| `frontend-final1` | Full frontend, strict TypeScript, existing56 comparison cases and all other wired checkers passed16.813s; normal development-hook exclusion passed |
| `normal-build-final1` | Default native build passed22.49s compile /22.681s command; executable was not launched |

Android results are Windows Rust host/adapter compatibility, not JVM, JNI
execution on Android, emulator, physical-phone or Android app-build evidence.
No new such cohort was run. Source dependency pins are unchanged. Normal
frontend SHA256 is
`8c063930b9e9ac223168df51686fc8fe4270bfcd43c7869db5ebd223546a2c08`,
identical to the previously qualified normal frontend. Restored normal native
executable SHA256 is
`bc8ff37fa7983293a92c7b8c86e4346780c64e36e8dc5e77d1e2837e150c7855`.
It is an unlaunched developer build, not an installer or public release.

Exact executed arguments/timestamps and original failure logs remain local.
The local seal `d07-native-full-port-qualified-evidence-seal1.json`, SHA256
`2dad1dce9cf514b08a29a53e6017e56c1b97c61be67697cc9e50cdb592a72d27`,
binds12 required successful command records and154 retained files, including
failure histories, three native cohorts,18 images and their visual-review
manifest. Each required record is terminal, exit0, sourceclean and unchanged;
failed historical records are preserved separately as evidence, not passes.
Generated artifacts remain local/ignored rather than public attachments.

Reproduce the final native checks from the repository root after provisioning
the pinned tools and existing dependencies. The earlier environment block sets
the owned target/temp directories and serial build flags:

```powershell
cargo test --locked --offline --manifest-path apps/desktop/src-tauri/Cargo.toml --all-features --jobs 1 -- --nocapture --test-threads=1
cargo clippy --locked --offline --manifest-path apps/desktop/src-tauri/Cargo.toml --all-features --all-targets --jobs 1 -- -D warnings
cargo fmt --manifest-path apps/desktop/src-tauri/Cargo.toml --all -- --check
cargo test --locked --offline --manifest-path crates/locallore-android/Cargo.toml --jobs 1 --lib -- --nocapture --test-threads=1
cargo tree --locked --offline --manifest-path crates/locallore-android/Cargo.toml --edges normal,build,dev --prefix none
# From apps/desktop, before restoring the default native build:
node verify-frontend.mjs
node node_modules/prettier/bin/prettier.cjs --check 'ui/*.{ts,tsx,html,css}' '*.{json,mjs}'
# From the repository root; this builds but does not launch:
cargo build --locked --offline --manifest-path apps/desktop/src-tauri/Cargo.toml --jobs 1
```

PR214 is a supporting service/closed-IPC slice. Its exact final-head security
result and owner-authorized merge are recorded on GitHub after this local
cutoff; no approval, merge or zero-vulnerability status is invented here.
Existing moderate Dependabot issue2 remains open. Native-model GUI admission,
real OS confirmation behavior, human narrative review, quality acceptance,
whole-app performance, phone qualification and final D07/epic/package gates
remain incomplete. The next runnable implementation is the separately frozen
native consumer, reusing these service/reader/cleanup interfaces.

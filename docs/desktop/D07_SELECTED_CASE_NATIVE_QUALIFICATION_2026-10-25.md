# Native selected-case qualification — 2026-10-25

Refs #29 D07.06, partial; draft [PR172](https://github.com/OptimumAF/LocalLore/pull/172).
**UNREVIEWED qualification draft. Focused results below are terminal; final
library/compatibility/build/frontend/Android-host gates remain pending.**
This does not complete D07 or expose native selected execution in the desktop UI.

## Source and measurement boundary

Report source: `33c17d88857473b9e6c688c370d16caedb7f3713`.
Accepted prerequisite is PR166/main `008c54182a5d7d51574d3f059bf7210085721df4`;
its [runtime cleanup qualification](D07_OWNED_RUNTIME_CLEANUP_QUALIFICATION_2026-10-25.md)
is inherited evidence. Its 47 Runtime passes are not a new run in this packet.
The [frozen native contract](D07_SELECTED_CASE_NATIVE_CONTRACT_2026-10-25.md)
defines the selected driver, ownership and accounting target; its historical
pending language is not itself a check result.

Root ran all commands serially. The document author read source and terminal
local process/log records only, with no execution or model/raw-prompt scan.
All generated synthetic saves, recordings and diagnostics remain local/gitignored.
Public paths use `<TASK_ARTIFACTS>`, `<selected-native-target>`,
`<approved-model>` and `<approved-resources>`; no machine-specific asset path is
needed to review the result. Active logs were not read or hashed.

| Evidence class | Actual scope |
| --- | --- |
| Dependency/path/setup/accounting checks | Real Core/Store/Ledger producer APIs where applicable; explicit synthetic clocks/metrics for accounting |
| Owner checks | Actual tiny fixed protocol child, synthetic reservation-port spy; no approved model identity substitution |
| Approved-asset four-case opt-in | Headless Rust selected driver, real packaged native worker and installed model |
| Retained historical reads | Same genuine native Move target inspected feature-off and with local-model; no execution/assets |
| Desktop native IPC / WebView / images | Not run by this packet |
| Human prose quality / hardware / offline / device | Not qualified |

The actual approved-asset test adapter exercises the shared reservation trait;
it is not the desktop ModelManager/EvaluationManager consumer adapter. That
adapter, its typed retained-failure lifetime and GUI consent/wiring remain
unimplemented. The private production handoff expectation stays disclosed until
a genuine desktop consumer uses it; no alternate manager is introduced here.

## Implemented shared behavior

`ApprovedNative` targets the same selected driver, actual per-arm prefixes/full
Requests and original corpus index. Both arms are preflighted before callback,
destination creation, reservations or asset access. Source locks/pins and current
source/profile checks remain execution prerequisites; a read capability never
becomes execution permission. Scripted and native target lanes remain distinct
from the source lane/profile, including divergent rollout inputs.

Completed resume, exact committed-checkpoint recovery and pure existing
dependency work do not call the native reservation callback, access assets or construct a native factory.
Dependency extraction reuses the actual existing eligibility branch and row construction;
it does not reinterpret Expected as a new guard validator. Provider-eligible
work includes finite guards, which keep the actual Host/Core rejection path.
Startup and zero generation-role calls are measured separately.

The owned native startup returns either BeforeChild or the actual boxed failed
owner. One runtime Arc serves both policies; cleanup uses Failed-safe direct
termination/reap. A rejected reservation handoff returns both the actual owner
and R in an opaque, redacted, non-Serde failure. Poisoned cleanup preserves the
initial closed cause while exposing Cleanup; confirmed poison differs from
uncertain cleanup. Unknown callback strings become SelectedExecution, with no
private suffix retained. Busy cleanup does not block on the runtime mutex.

Both live invocation Ledgers remain held through physical cleanup. Confirmed
terminal cleanup precedes invocation finish and final report publication.
Uncertainty preserves actual rows/admission settlements but leaves both full
preparation reservations unknown. No deadline or Drop acknowledgement proves
cleanup. Existing full native evaluator callers remain on their legacy startup
API and are not newly qualified for every ownership error.

The preparation deadline includes original-entry preflight and callback time;
it cannot restart after load. Loaded setup above 120000ms refuses before any
record/ledger write. Known failed terminal cost remains unclamped, even above
the reservation; prior unknown invocations are not refunded. The unrelated
legacy `Ledger::record_shared_setup` cap remains strict. Accounting test clocks
are synthetic inputs, not measured native performance or actual cleanup proof.

Retained setup decoding requires exact names/keys/unique raw metrics, both real
reservation bindings and each known ceil/floor settlement share. Missing
settlements remain unknown. Impossible loaded overruns refuse; failed overruns
remain readable. Inspection does not repair, settle, hash/load assets or grant
execution. Old Play2.1–2.5 validators and canonical retries remain authoritative.

## Preserved first attempts and focused results

Every suffix below names `<TASK_ARTIFACTS>/d07-selected-native-<suffix>.log`
and its `-process.json`. Records pin source/arguments/clean launch/exit and
terminal source stability. Counts overlap subsequent suites; do not add them.

| Source / stage | Actual outcome | Suffix |
| --- | --- | --- |
| `9740ad47`, dependency absent API | Exit101, two compile errors; zero tests | `dependency-missing-api` |
| `06ab0f45`, dependency implementation | 4 passed, 0 failed, 0.28s | `dependency-first` |
| `37666bb2`, owner module absent | Exit101, one compile error; zero tests | `owner-missing-api` |
| `33df56ba`, owner before fixed fixture build | 1 passed / 7 fixture-prerequisite failures; not ownership behavioral RED | `owner-first` |
| `33df56ba`, fixed protocol fixture build | Exit0, 18.51s | `fixture-first-build` |
| `33df56ba`, fixture-ready owner suite | 7 passed / 1 actual failure: initial RunBudget became Cleanup under poison | `owner-fixture-ready` |
| `facd2006`, initial-cause correction | 8 passed, 0 failed, 0.32s | `owner-cause-fixed` |
| `8db7d9f2`, selected paths absent APIs | Exit101, 18 compile errors; zero tests | `paths-missing-api` |
| `facd2006`, real producer/path/model-free journeys | 3 passed, 0 failed, 160.43s | `paths-first` |
| `facd2006`, initial clock/setup reader groups | 4 passed, 0 failed, 1.26s | `clock-setup-first` |
| `eb0d3fdc`, duplicate raw metric names | 0 passed / 1 actual failure: forward/reversed/escaped duplicates accepted | `duplicate-metrics-exact` |
| `554eecde`, unique metrics + required nullable key | 5 passed, 0 failed, 1.03s | `duplicate-metrics-fixed` |
| `554eecde`, feature-off retained setup | 4 passed, 0 failed, 1.04s | `setup-feature-off-first` |
| `15395411`, accounting helper absent | Exit101, five compile errors; zero tests | `accounting-missing-api` |
| `f091635b`, extracted accounting | 1 passed / 2 actual failures: late loaded accepted; duplicate setup wrote before refusal | `accounting-extracted` |
| `01e2199b`, pre-write both-arm checks | 3 passed, 0 failed, 0.16s | `accounting-fixed` |
| `d1076a6e`, retained loaded overrun | 5 passed / 1 actual failure: 120001/240001ms Loaded records accepted | `loaded-history-matched` |
| `13642027`, retained loaded-bound correction | 6 passed, 0 failed, 1.33s | `loaded-history-fixed` |
| `8218548f`, approved installed-asset opt-in | 4 passed, 0 failed, 320.80s; build6.77s | `approved-assets-first` |
| `33c17d88`, genuine retained native read, feature-off | 1 passed, 0 failed, 0.97s | `history-feature-off` |
| `33c17d88`, same retained read, local-model | 1 passed, 0 failed, 0.96s | `history-local-model` |
| `13642027`, first strict evaluator Clippy | Exit101, one redundant-borrow error | `clippy-first` |
| `9f21664c`, borrow corrected | Exit101, two test iterator errors | `clippy-borrow-fixed` |
| `9e3a4f45`, iterator corrections | Strict all-feature/all-target Clippy exit0, 8.32s; no lint waiver | `clippy-test-iterators-fixed` |

Two guessed-filter invocations (`duplicate-metrics-first`, `loaded-history-first`)
exited0 with **zero tests**. They are retained and excluded from every pass
claim. Root's later helper rejects zero-match filtered runs. Compile-only and
missing-fixture attempts also remain distinct from the actual behavioral failures.
The original frozen assertions were preserved; later changes corrected source,
registration/formatting or narrowly identified test prerequisites/lints.

## What the approved-asset cases established

All four explicitly ignored tests were deliberately selected with installed
approved assets at clean `8218548f295d891dd0502267855b780d8157f4e7`.
They used synthetic stories and the actual Rust Host/Repository/Store/Play
pipeline, real runtime profile checks and the native worker/model. This is
genuine headless native inference evidence, not native application UI execution.

1. Guard: one actual model setup, actual Host rejection rows under both policies,
   zero generation-role calls. Root's retained report records physical setup
   8900ms and worker-reported load_ms377.6348; these are different timer scopes,
   one finite observation, not a load-time benchmark or zero-startup claim.
2. Move: both policy arms committed actual current native Play receipts with
   full Request/profile/context-policy checks. Removing only a real emitted
   checkpoint recovered from actual Store history with zero reservation/asset
   callbacks, no duplicate commit and unchanged actual canonical histories.
3. Postcommit cancellation: the real first commit survived; resume executed only
   the missing arm, then completed read-only resume admitted no new work.
4. Forced cleanup uncertainty: a private one-shot fault retained the actual same
   runtime Arc and reservation, with both full preparation reserves outstanding.
   Test cleanup explicitly retried the real owner; no fabricated successful
   cleanup, reset key or automatic generation retry was used.

The local test harness retains unresolved owners and blocks later asset cases
if its own cleanup cannot be confirmed. That is test containment, not a second
production manager or evidence that the desktop handoff adapter is wired.
No raw model prose or role text is reproduced in this report.

The subsequent historical oracle reads the genuine Move target produced above,
not an edited native label on a synthetic/fake report. It checks complete
inventory/serialized report stability and retained canonical/provenance fields,
with no provider/reservation/execution port. This is distinct from the earlier
legacy33356 comparison historical gate; it is not a rerun of that old cohort.

## Profile identity and environment

The approved source is [profile-v1.json](../../native/llama-worker/profile-v1.json):
`qwen3-0.6b-q8-cpu-v1`, experimental Windows x64 CPU lifecycle scope;
Qwen3-0.6B Q8_0 with F32 tensors, model revision
`23749fefcc72300e3a2ad315e1317431b06b590a`, 639446688 bytes.
Model SHA256 `9465e63a22add5354d9bb4b99e90117043c7124007664907259bd16d043bb031`;
worker SHA256 `b5dd124e484c67c9dda5aebb2cdff1878ccefd0fba99aba4788e00a166f68434`;
llama.cpp revision `620d2225cc436ab0b001e3200e590e3b286ef9ab`;
chat-template SHA256 `57f1fd00f0013a2be96aa79b857391f27e23df5b5f847072b524c897e24d0361`;
canonical profile-manifest SHA256
`01ad542001b04a96f4a8ed6c841be1866eb025350836e0c5d0a4969fdb361d38`.
These are the versioned approved identities, not newly selected/downloaded assets.

Existing environment: Rust/Cargo1.93.1, Node24.22.1, PowerShell7.6.5,
Windows11 build26300 x64. No fresh hardware survey is attributed to this packet.
Profile limits include 4096 context tokens, 350 tokens/role, CPU4threads,
GPUlayers0, 32768-byte request/response frames and one repair. Evaluator admission
limits remain 32 preparations/admissions, 96 roles, 30-minute active charge,
120-second preparation, 60-second absolute turn and 3-second cleanup reserve.
Blocking OS/file/kill/wait/join behavior has no universal wall-time guarantee.

## Reproduction and local evidence

Run serially from the repository root, with the existing owned
`<selected-native-target>` shared by evaluator and fixed Runtime fixture build.
The recorded helper used one build job, incremental0, dev/test debug0,
empty LIBSQLITE3_FLAGS and task-owned TEMP/TMP. It required clean source and
preserved original logs rather than replacing failed evidence.

```powershell
cargo build --locked --offline --manifest-path crates/locallore-local-runtime/Cargo.toml --features development-worker --jobs 1 --target-dir <selected-native-target> --bin protocol-fixture
cargo test --locked --offline --manifest-path crates/locallore-eval/Cargo.toml --features protocol-owner-tests --jobs 1 --target-dir <selected-native-target> --lib local_lane::comparison::selected::native_owner_review_tests -- --nocapture --test-threads=1
cargo test --locked --offline --manifest-path crates/locallore-eval/Cargo.toml --features local-model --jobs 1 --target-dir <selected-native-target> --lib local_lane::comparison::dependency_review_tests -- --nocapture --test-threads=1
cargo test --locked --offline --manifest-path crates/locallore-eval/Cargo.toml --features local-model --jobs 1 --target-dir <selected-native-target> --lib local_lane::comparison::selected::native_path_review_tests -- --nocapture --test-threads=1
cargo test --locked --offline --manifest-path crates/locallore-eval/Cargo.toml --features local-model --jobs 1 --target-dir <selected-native-target> --lib local_lane::comparison::selected::native_clock_setup_review_tests -- --nocapture --test-threads=1
cargo test --locked --offline --manifest-path crates/locallore-eval/Cargo.toml --features local-model --jobs 1 --target-dir <selected-native-target> --lib local_lane::comparison::selected::native::accounting_review_tests -- --nocapture --test-threads=1
# Feature-off setup: repeat the clock/setup command without --features local-model.
# Explicit installed-asset opt-in only, after owner authorization:
$env:LOCALLORE_SELECTED_NATIVE_TEST_RESOURCES='<approved-resources>'
$env:LOCALLORE_SELECTED_NATIVE_TEST_MODEL='<approved-model>'
cargo test --locked --offline --manifest-path crates/locallore-eval/Cargo.toml --features local-model --jobs 1 --target-dir <selected-native-target> --lib local_lane::comparison::selected::native_asset_review_tests -- --ignored --nocapture --test-threads=1
$env:LOCALLORE_SELECTED_NATIVE_HISTORY='<genuine-retained-native-Move-target>'
cargo test --locked --offline --manifest-path crates/locallore-eval/Cargo.toml --jobs 1 --target-dir <selected-native-target> --test comparison_selected_native_historical_review -- --ignored --nocapture --test-threads=1
# Repeat the historical command with --features local-model for the second run.
cargo clippy --locked --offline --manifest-path crates/locallore-eval/Cargo.toml --all-features --all-targets --jobs 1 --target-dir <selected-native-target> -- -D warnings
```

Recipes normalize the feature-off helper's empty `--features` argument by
omitting it. Actual source/arguments/exit attribution comes from each process
record; reproducing a command is separate from claiming it already ran here.

Terminal subset manifest: 52 files / 67901 bytes, the 24 log/process pairs named
in the table plus the two retained zero-match pairs. This excludes active/future
final-library/compatibility records and generated story/model artifacts.
Ordinal filename order, UTF8 `filename<TAB>bytes<TAB>lowercaseSHA256<LF>` gives
`f72bd33ca087b3d157e1354cd40d0c7384d9613de667995b85af512acce45f98`.
Approved-asset log SHA256
`948aa3c0af9d37036017a5bb342d3d2c608c68010b48495391b6863c53e46faf`;
feature-off historical log
`de260824d1399cdd6b36d22d4ad8707447225e37341356a62de30626d0d24f16`;
local-model historical log
`09c36f32560c6869b5d6ff1d7654b8f7188e634d8ec1cd1c55e3ca7e60aaea97`.

At33c17 the native driver/owner match the approved-asset source821; subsequent
changes add the retained Loaded-bound check, remove a redundant dependency borrow,
correct two test iterator lints and add/format the genuine historical oracle.
No approved-asset rerun at33c17 is implied. Raw private evidence stays local.

## Pending final checks and remaining gates

| Gate at final candidate | Status at this draft handoff |
| --- | --- |
| Complete evaluator library with protocol-owner-tests (enables all evaluator features), source `33c17d88` | 86 passed / 5 explicitly ignored / 0 failed, 932.97s; all 91 selected, no filter |
| Remaining integrations and final strict/format compatibility | Pending Root terminal evidence |
| Frontend and normal native build/artifact restoration | Pending Root terminal evidence |
| Android Rust-host compatibility | Pending Root terminal evidence; no JNI/JVM/ABI/APK/device claim |
| Desktop ModelManager handoff adapter + native job/GUI consent | Unwired, separate allocation |

Root owns updates to this section after terminal results and independent review.
No pending stage counts as a pass. This draft is source/log documentation only,
not human approval, merge authorization or an epic checkbox.
No native IPC/WebView/render images, fresh whole-RAM/hardware measurements,
offline/licensing qualification, real-device run or human narrative-quality
review is claimed. Human-reviewed remains0 and quality acceptance false.
The next runnable product task is the separately frozen desktop native selected
consumer/ownership/consent integration after these shared checks qualify;
existing full native evaluator legacy ownership follow-up also remains open.

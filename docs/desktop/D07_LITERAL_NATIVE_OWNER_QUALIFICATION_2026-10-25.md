# Native protocol3 ownership and model-free qualification

Scope: D07.03/.04/.05/.06 supporting work and M07.01. Base accepted PR190 /
`775b0998`. Production source `a8004dd8` is locally qualified by the completed model-free
cohort below; later documentation-only commits do not change Rust/TypeScript. No real-model, native3 CLI/UI or quality acceptance is
claimed by this record.

## Native entry and authority

With the existing `local-model` feature, `literal_v3::run_native_comparison`
accepts the same dir/resume/kind/cancellation/scene/reference controls as the
scripted driver, plus a trusted reservation callback. It returns the existing
`selected::SelectedNativeFailure<R>` ownership result and reuses
`SelectedNativeReservation`; no second runtime or asset-owner mechanism is introduced.

The callback acquires an application-owned lease. It must not start inference
or inspect model assets itself. Current-source completed native resume returns
before the callback; that branch's genuine completed-native evidence is still
pending. Continuing work validates the manifest, reference, all retained rows,
actual Store outcomes and both budgets before acquiring a lease. Cancellation
and the single entry-time preparation deadline are checked around acquisition.
Both invocation reservations are durable before the shared startup helper first
requests asset paths or starts the worker. A preowned Native factory still
cannot enter the scripted API. JSON metadata is never an execution grant.

The actual selected startup/preparation code is extracted into one internal
`native_startup` helper used by both drivers. It preserves owned BeforeChild /
AfterChild results and retains the actual runtime Arc through load errors. It
now refuses known cancellation/deadline expiry before the asset getter. Load and
native3 body unwind boundaries retain the actual owner while their inner guards
drain; failures return closed codes without a panic payload.

The native3 session is split into locked validation/preflight, invocation begin,
shared turn execution and final publication. Host/provider/watchdog scopes and
factory references drain first. Existing `finish_owner` confirms termination
and reaping, or transfers/returns the actual R/Arc pair. Only confirmed terminal
paths settle invocation costs and publish. Uncertain cleanup leaves reservations
outstanding and publishes no success; it is not refunded or replaced by a dummy
handle. Caller ownership obligations remain the existing retained-error contract.

No canonical schema, engine validation, model backend, persistence implementation,
ContextPolicy or model profile/template/budget changes. Both arms use the same
existing provider and approved profile; Literal retains its separate descriptor
and full Core-rendered input proof. Actor knowledge and inspection privileges
are not changed.

## Native diagnostic setup

Native3 cold inspection reuses the existing selected setup decoder from the same
bounded bytes, parameterized only by the expected diagnostic version. Root and
raw load-member uniqueness, required nullable load, Runtime metric shape/token
caps and reservation identity are checked. Known settlements must cover their
ceil/floor physical shares; missing settlements retain unknown full reservations.
The selected wrapper keeps its version2/root64 behavior. Protocol3 keeps its
root256 and strict eight-key/monotonic pair checks; scripted setup.load remains null.

A native label means configured lane, not successful model execution. A failed
BeforeChild attempt has no observed load or accepted turn. `physical_setups`
counts actual successful load observations; `native_load` retains their metrics.
`physical_setup_ms` totals known preparation attempts, including failed attempts
and confirmed cleanup on failed startup; it is not always model-load latency.
Known terminal failed overruns are measured and charged without clamping. Loaded
setup remains capped. Uncertain cleanup produces no terminal setup/refund.

## Frozen oracles, failures and results

Original source packets are committed before implementation. Authors did not
execute their packets; coordinator results below are separate evidence.

- Public four-group packet63e576cd, integratedb8f30183: missing owned-native3 API
  compiler observation (private inherited v2 name/type mismatch), not behavior
  RED. Initial5a4b4d4b PASS4/.53s. Precancel/scene limits do not create output or
  reserve; reservation-time cancellation drops the safe lease without assets or
  invocations; genuinely missing assets fail BeforeChild and produce an honest
  inspectable failed-native record; mutations refuse before another lease.
- Owner packet e6340cd9, integrated96117c67: three actual fixed protocol-child
  controls PASS3/.52s at5a4b4d4b. Confirmed cleanup precedes lease Drop, settlement
  and publication. Accepted/rejected uncertain handoffs retain the same Arc/R
  without finalization, then explicitly reap the exact fixture child.
- Root7ec09cb4 shared pre-asset checks: RED2, each getter observed once despite
  known cancellation/expiry. Fixe9039dc7 GREEN2/.00s, no getter access.
- Review packetca7da3e0, integratedc6112b78/098dc4e8: actual RED3pass/2fail/.92s.
  Increasing only a genuine setup's physical cost was incorrectly accepted above
  known settlements. A test-only fixed panic after actual ownership unwound
  without the explicit finish boundary. The fixture RAII guard reaped its own
  exact child on the initial failure.
- Fixa8004dd8: reuse the selected bounded decoder/share validator and contain the
  owned body interruption. GREEN5/1.19s. The default panic hook prints the fixed
  test message, but the test receives closed SelectedExecution after confirmed
  cleanup; the successful test is not an unhandled production panic.

These child tests use the existing zero-argument development protocol fixture,
with no caller executable/mode/model input. Its empty synthetic fixture file is
not weights. Injected startup RuntimeProtocol skips the model factory. This is
actual process ownership evidence, not real inference or model timing. Only the
fixed cfg(test)+protocol-owner-tests interruption flag is added; it is absent
from normal code and exposes no IPC, code/file/shell evaluator or debug service.

## Final compatibility cohort

All stages at `a8004dd8` finished with exit0 and clean/unchanged terminal source.
The cohort was serialized; fixed children were explicitly reaped. Local bounded
logs/process records use `d07-literal-native-final-*`. No generated artifact or raw
diagnostic is uploaded.

| Check | Actual result |
| --- | --- |
| Public native preflight | PASS4/.61s. |
| Shared pre-asset cancellation/deadline | PASS2/.00s. |
| Existing selected setup / accounting / preflight | PASS7/1.92s; PASS3/.18s; PASS3/138.45s. |
| Literal + capture + original v2 producer semantics | PASS26/34.58s; four stable CapturedContext semantic-result projection hashes and twelve-row producer projection unchanged. |
| Existing/new actual fixed-child owner controls | PASS13/1.17s, protocol-owner-tests feature. |
| Public scripted producer/actual windowless CLI | PASS7/219.59s. |
| Genuine preserved UI5 read/sourceMismatch/full inventories | PASS1/21.56s. |
| Genuine preserved native selected read cap/history | PASS1/26.04s and PASS1/1.04s; no inference or file changes. |
| Default-feature library / native history | PASS7/29.17s; PASS1/1.03s; no optional runtime dependency. |
| Evaluator all-target strict protocol-feature Clippy | PASS12.33s initial; cached final .21s; no source change between. |
| Evaluator format | PASS4.175s command. |
| Full frontend/type/controller/normal-hook exclusion | PASS15.713s command; synthetic/controller evidence. |
| Native all-feature/all-target strict Clippy / default normal build | PASS20.39s /21.15s Cargo; executable not launched. |
| Android Rust host / graph | PASS20/1.65s; graphPASS, no evaluator/Tauri/local-runtime edge. No SDK/device execution. |

No selected test was silently skipped; historical gates were explicitly opted in
using genuine retained data. Whole-workspace/core, new Tauri IPC/WebView, approved
model generation, memory/performance, physical-device and human-review checks are
not newly qualified. Existing finite owner tests cannot prove every OS failure.

Windows x64 NT10.0.26300; PowerShell7.6.5; Rust/Cargo1.93.1
(rustc01f6ddf75/cargo083ac5135, LLVM21.1.8); Node24.22.1. Existing cached
prerequisites, locked/offline, one job, incremental/debug info0. No installs,
model download, SDK/ABI/device/emulator/ADB, settings or release action. No desktop
input, activation, screenshots or unrelated application automation. Compiling
Tauri/Android does not establish native WebView/IPC or physical-device execution.

## Reproduce

Use ordinary task-owned output/target/TEMP paths and serialize heavy commands.
The protocol fixture is the existing fixed development binary, not a new backend.

```powershell
$env:CARGO_BUILD_JOBS='1'; $env:CARGO_INCREMENTAL='0'
$env:CARGO_PROFILE_DEV_DEBUG='0'; $env:CARGO_PROFILE_TEST_DEBUG='0'
$env:LIBSQLITE3_FLAGS=''; $env:TEMP='<owned-temp>'; $env:TMP=$env:TEMP
cargo build --locked --offline --manifest-path crates/locallore-local-runtime/Cargo.toml --features development-worker --jobs 1 --target-dir <eval-target> --bin protocol-fixture
cargo test --locked --offline --manifest-path crates/locallore-eval/Cargo.toml --features local-model --jobs 1 --target-dir <eval-target> --test literal_native_preflight -- --nocapture --test-threads=1
cargo test --locked --offline --manifest-path crates/locallore-eval/Cargo.toml --features protocol-owner-tests --jobs 1 --target-dir <eval-target> --lib owner_review_tests -- --nocapture --test-threads=1
cargo test --locked --offline --manifest-path crates/locallore-eval/Cargo.toml --features local-model --jobs 1 --target-dir <eval-target> --lib native_startup::pre_asset_tests -- --nocapture --test-threads=1
cargo test --locked --offline --manifest-path crates/locallore-eval/Cargo.toml --features local-model --jobs 1 --target-dir <eval-target> --lib selected::native_clock_setup_review_tests -- --nocapture --test-threads=1
cargo test --locked --offline --manifest-path crates/locallore-eval/Cargo.toml --features local-model --jobs 1 --target-dir <eval-target> --lib native::accounting_review_tests -- --nocapture --test-threads=1
cargo test --locked --offline --manifest-path crates/locallore-eval/Cargo.toml --features local-model --jobs 1 --target-dir <eval-target> --lib selected::native_path_review_tests -- --nocapture --test-threads=1
cargo test --locked --offline --manifest-path crates/locallore-eval/Cargo.toml --features local-model --jobs 1 --target-dir <eval-target> --test literal_comparison_v3 -- --nocapture --test-threads=1
cargo clippy --locked --offline --manifest-path crates/locallore-eval/Cargo.toml --features protocol-owner-tests --all-targets --jobs 1 --target-dir <eval-target> -- -D warnings
cargo fmt --manifest-path crates/locallore-eval/Cargo.toml --all -- --check
```

Additional executed compatibility commands, same environment/owned targets:

```powershell
$env:LOCALLORE_LITERAL_HISTORICAL_COMPARISON='<genuine-preserved-UI5-comparison>'
$env:LOCALLORE_LITERAL_HISTORICAL_SELECTED='<genuine-preserved-UI5-selected-work>'
cargo test --locked --offline --manifest-path crates/locallore-eval/Cargo.toml --features local-model --jobs 1 --target-dir <eval-target> --test literal_control_historical_review -- --ignored --nocapture --test-threads=1
$env:LOCALLORE_SELECTED_NATIVE_HISTORY='<genuine-retained-native-selected-target>'
cargo test --locked --offline --manifest-path crates/locallore-eval/Cargo.toml --features local-model --jobs 1 --target-dir <eval-target> --test comparison_selected_native_historical_review --test comparison_selected_desktop_native_historical_review -- --ignored --nocapture --test-threads=1
cargo test --locked --offline --manifest-path crates/locallore-eval/Cargo.toml --jobs 1 --target-dir <eval-target> --test comparison_selected_native_historical_review -- --ignored --nocapture --test-threads=1
cargo test --locked --offline --manifest-path crates/locallore-eval/Cargo.toml --features local-model --jobs 1 --target-dir <eval-target> --lib literal -- --nocapture --test-threads=1
cargo test --locked --offline --manifest-path crates/locallore-eval/Cargo.toml --jobs 1 --target-dir <eval-target> --lib literal_v3:: -- --nocapture --test-threads=1
node apps/desktop/verify-frontend.mjs
cargo clippy --locked --offline --manifest-path apps/desktop/src-tauri/Cargo.toml --all-features --all-targets --jobs 1 --target-dir <native-target> -- -D warnings
cargo build --locked --offline --manifest-path apps/desktop/src-tauri/Cargo.toml --jobs 1 --target-dir <native-target>
cargo test --locked --offline --manifest-path crates/locallore-android/Cargo.toml --jobs 1 --target-dir <native-target> --lib -- --nocapture --test-threads=1
cargo tree --locked --offline --manifest-path crates/locallore-android/Cargo.toml --edges normal,build,dev --prefix none
```

Native3 CLI/UI remain unavailable: the scripted CLI honestly refuses --lane native.
The new Rust entry requires an existing trusted reservation. Approved real-model
execution, completed-native resume without assets, whole-app memory/latency,
model quality and versioned desktop consumption are the next gates. Neither a
synthetic child nor a favorable source review substitutes for those results.
Full D07/M07 and epic21 stay open. Generated diagnostics remain local/ignored;
public evidence contains no private stories, assets, credentials or machine paths.

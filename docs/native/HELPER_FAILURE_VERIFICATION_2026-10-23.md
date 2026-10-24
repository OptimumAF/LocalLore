# Helper failure and ownership verification, 2026-10-23

Refs [#8](https://github.com/OptimumAF/LocalLore/issues/8) (M04.04).
Implemented and locally verified; owner acceptance and the full task remain
pending. This packet is stacked on unmerged [#87](https://github.com/OptimumAF/LocalLore/pull/87),
base `540dff07e5e09019bd04bcc4ea5ad7dc32cacb1f`. Qualified code/build-helper
source is `677d73f2debab25509b9763a887e5e321fb1f26c`; subsequent changes are
evidence documentation only. The [contract](HELPER_FAILURE_CONTRACT.md),
[host proof](HELPER_FAILURE_HOST_2026-10-23.md),
[aggregate](HELPER_FAILURE_RESULTS_2026-10-23.json) and
[independent audit](HELPER_FAILURE_REVIEW_2026-10-23.md) describe the boundary.
Raw diagnostics and synthetic databases remain private.

## What changed

An opt-in debug/testOnly Android profile admits fixed helper faults under its
own package `org.locallore.app.capacityfaultsv3`, output and Gradle cache. It
retains schema3, format2, pages32, initial17, padding14 and removal free15, adding
only `faults_format=1`. The host example has separately admitted fixed faults.
No production Rust, Host/JNI protocol, database schema, dependency, model or
gameplay authority changed. Kotlin remains a client of Rust.

Two real regressions in the existing **test boundary** were demonstrated and
corrected. After successful read-only validation, late marker drift was being
classified as an initial refusal. It now poisons the process-wide continuation
fence even when the child is reaped. A suspended precommit hook could swallow a
helper failure and resume native exchange; the fence is now checked after the
hook, immediately before the actual native dispatch. This is not a claim of an
observed production gameplay exploit.

After poisoning, the tests prove zero additional native exchanges, helper/SQL
cleanup, new fixture owners, reopen or release probes. Existing owners may close
and readers may drain. Root retention is bookkeeping supported by no deletion,
drop or probing attempts and source gates; it is **not** a filesystem existence
check after poisoning. The primary failure remains visible. No reset API clears
the sticky fence: each nested fault class gets a fresh instrumentation process.

Android malformed/oversize/timeout/marker-drift faults occur after read-only
admission and before writable SQL. The after-fill fault occurs only after actual
14-row fill, the 15th insert returning SQLite Full, and connection close. All
five host fault cases perform that actual fill/close before their selected fault.
Known-reaped host failure permits only a separately admitted exact owned-table
cleanup; unknown ownership suppresses every follow-on helper and native action.

## Executed checks

| Check | Actual result |
|---|---|
| `python scripts/check.py host --offline` | 380 Rust workspace passes plus 3 linker passes; 2 existing ignored tests; 374 Python passes; 4 fixture bindings; fmt and strict Clippy pass |
| `cargo +1.93.1 test -p locallore-workspace --example capacity_relief_probe --locked --offline` | 2 separate ownership-policy tests pass |
| Actual capped32 host children | 5 fixed fault cases pass, including distinct cleanup refusal; normal accept and cancel controls pass with prior schema3 reports unchanged |
| `python scripts/android_capacity_fault_probe.py build --offline` | Both ABIs built/packaged; manifest, native32 and 16KiB ELF/ZIP audits pass; 146 JVM tests pass, fresh in the RED build and reused in later builds; lint 0 errors/1 existing GradleDependency warning |
| Actual Gradle admission refusals | 9 pass: bad value, absent/extraneous cache, Full/relief cache, mixed flags and release |
| Targeted script audits | 5 fault, 6 normal relief and 5 normal Full tests pass; final fault-only compile-argument change reran the 5 fault and 6 relief tests successfully |
| Final Android fault qualification | 12 passes: six individual classes on each of two Android 15/API35 x86_64 emulators, 4KiB runtime pages |
| Final default discovery | 6 passes: exactly the original three relief methods on each emulator; no nested fault classes discovered |

The integrated host gate ran at `f169955`; later changes affect only Android
test observations, the fault-build argument and documentation. The latest
targeted audits cover that argument. The final Android build performed 77 tasks,
7 executed and 70 up-to-date, in 38 seconds. An ordinary Android rebuild was not
performed in this packet. ARM64 packaging is not ARM64 execution or 16KiB-device
execution. There was no connected physical phone.

Final Android qualification is **18 passes, 0 failures/skips/unfinished**, nine
unique methods across 14 instrumentation cohorts. For each emulator the six
explicit nested classes were MarkerDrift, DispatchFence, Malformed, Oversize,
Timeout and AfterFill. Default discovery contained only:

- `SqliteReliefInstrumentedTest#collectedFullRecoveryAfterOwnedPaddingRemovalPublishesOnlyOriginalAcceptedReceipt`
- `SqliteReliefNativeTest#actualFullThenOwnedPaddingRemovalCommitsOnlyOriginalReadyKeyOnce`
- `SqliteReliefNativeTest#cancelledFullReadyTurnRemainsUnspentAfterPaddingRemovalAndReopen`

Individual class selection uses the existing bounded device helper and
`org.locallore.app.SqliteHelperFaultTest$<Class>`; see
[Android reproduction](../../apps/android/README.md). Instrumentation default
discovery establishes its inventory, not a newly imposed execution order.
Every cohort ended with its bounded client terminal/clean, owned app/test
processes absent and all 19 pre-existing installed APK identities unchanged per
emulator. All 20 pre-existing local APK hashes also remain unchanged.

## All earlier attempts are retained

| Phase | Observed result and correction |
|---|---|
| RED test source `f35df14` | Four failed method invocations: MarkerDrift and DispatchFence on each emulator. MarkerDrift failed `unknown_completion_is_sticky`, followed by a cleanup `padding_child_exit_72` failure in the same invocation. DispatchFence observed actual native dispatch counter 11 to 12 and failed `no_post_hook_native_dispatch`. The counter is immediately before underlying exchange. |
| Initial B prelaunch | One 20-second `am force-stop` setup timeout, before instrumentation started; no test raw output or method pass/failure counted. Bounded client cleanup and later owned-process absence/preservation checks passed. A fresh launch with the same budget then produced the genuine RED failure. No restart or increased budget was used to turn setup into a pass. |
| First fixed candidate `f169955` | Eight passes and two Timeout failures (`pipe_read_failed`), four other classes passing per emulator; AfterFill and defaults were not run in this phase. Children/readers had stopped and the sticky fence remained set. |
| Timeout observation correction `eda5f70` / `69fe9f4` | Retains aggregate reader failure and poison. An atomic termination-request flag distinguishes IOException observed after owned termination from unexpected/pre-flag reader failure. Timeout still requires actual deadline, owned termination, terminal/reap, stopped readers, no unexpected failure, aggregate equal to shutdown failures and every blocked-dispatch/cleanup assertion. Other cases still require no reader failure. |
| Final incremental compile attempt | Kotlin rejected unchanged internal fixture visibility. Failure retained; visibility was not widened. Fault-only `-Pkotlin.incremental=false` compiled the complete test module successfully. The compiler's root cause is not established. |
| Initial host compile | Two wrapper/closure type errors corrected before child execution. The initial passing malformed run preceded added successful cleanup-owner metadata; its final repeat verifies that metadata. Both runs retained. |

All actual Android method invocations across phases total **32: 26 passes and
6 failures**, zero skipped/unfinished. The final 18 passes are the qualification
cohort; the earlier eight passes are not counted again. Setup/build failures are
separate from method counts.

The official [API35-era process implementation](https://android.googlesource.com/platform/libcore/+/android-15.0.0_r1/ojluni/src/main/java/java/lang/UNIXProcess.java)
closes process streams during destruction. That supports testing shutdown
observations; it does not establish the exact cause of either observed
IOException. Classification records observed order/type and never authorizes
post-poison cleanup or native work.

## Artifact and preservation evidence

The application APK is identical across all three phases:
`e149627f2d36ea3491124806c3e982991dc7b78d0224d478a923b05632799d2f`.
Both packaged Rust libraries are byte-identical to the prior #87 relief32 APK.

| Test APK | SHA256 |
|---|---|
| RED | `6a24b05b593b1d3407edc99033c78b053c9789a390c34cd5480d6ecc47410184` |
| First fixed candidate | `021fcbb8b204f80c086f8e97bf6a2841c0758148f00496b010e1f10f0c8e4b8f` |
| Final | `ff04a113c96e8dbda617b49132d1483a24f268793532eb26976ffe6fa07e56d4` |

The public aggregate binds 161 private raw artifacts and 13 tested-source byte
hashes, including workspace line endings. It contains fixed test metadata,
counts and hashes, not raw diagnostics, serials, private paths, stories or model
data. Its SHA256 is
`5fbc90e9f0d858f3f279796a9802057b150cb90c2c5004bae0fa2d2659124eba`.
The host report separately binds its 13 logs and 38 child artifacts through a
private index. All attempts remain available locally.

To preserve storage headroom, two inactive, exact checkout-owned compiler-output
trees were moved to the roomy task-owned volume and junctioned at their original
paths. All 1,715 files (893 plus 822) were hash-checked before and after. No
model, save or AVD data was removed or moved. Existing APKs and installed packages
were preserved as above.

## Remaining gates and handoff

This is a bounded synthetic-helper proof. It does not establish an actual
unkillable/unknown-ownership OS incident (host unknown ownership has two policy
tests only), partition ENOSPC, mid-transaction kill, power loss, OS-adversary
resistance, physical-phone/ARM64 execution or model qualification. Fixed polling
output thresholds are not filesystem quotas. Broader M04.04 acceptance and owner
review of this stacked PR remain pending; checklists stay unchecked.

No model operations occurred. The separate model integrity/storage hold recorded
in [#84](https://github.com/OptimumAF/LocalLore/pull/84) remains in force.
The next runnable packet is M01.03/M01.05 **read-only model integrity and storage
investigation**, before further inference: reconcile exact local/installed model
identity and available storage with the retained failed attempts. M01.01 and
physical-device-dependent gates remain blocked without an authorized phone.
No merge, release, repository-setting change or private artifact upload is part
of this packet.

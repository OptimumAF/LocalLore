# Versioned Windows host driver: component verification — 2026-10-26

The versioned runner passes **10 Android component methods**, **234 actually
rerun JVM tests**, **11 APK audit commands** and **1,153 Python script tests**.
The Python total includes the 121 targeted driver/audit tests; do not add them
together. This qualifies the stated component scope, not the external
retained-parent two-process-death case or the complete M10/M08 milestones.

Refs #14 (M10.02), #12 (M08.05/M08.01 supporting). PR #203 is stacked on draft,
unmerged #201 at `96bc4104`, itself on unmerged #200. Final executed source is
`2ec9c9a4`; earlier successful component sources are `5a82772f` and `374124a9`. No production
gameplay, Rust engine, schema, JNI, dependency, model or backend change is made.
Full tasks remain unchecked pending their wider criteria and owner acceptance.

## Source and independent work

The [driver commands and boundaries](ANDROID_PROCESS_HOST_DRIVER.md) are now
versioned rather than generated private scripts. The root coordinator owns
`benchmarks/android_process_verification.py`, its host tests, integration and
documentation. Independent authors used separate clean worktrees:

| Author / integrated commit | Owned files |
|---|---|
| `e49c4a4c` / `e1bbab01` | `benchmarks/android_process_client.py`, its script test module |
| `7dd6a0b2` / `aef79089` | `benchmarks/android_instrumentation_evidence.py`, its script test module |

Independent source review produced concrete fixes before execution: full live
lease validation; source/driver admission before dispatch; binding complete
build records instead of trusting a passed label; bounded binary drains;
exclusive files before spawn; sticky timeout; user0; and fixed method rosters.
Other review confirmed the SDK client's native identity and persistence guards.
These reviews are not owner acceptance or substitutes for executions.

The SDK client uses existing Windows Job ownership, an unchanged existing ADB
server and exact loopback listeners, native process creation identities, pinned
tool bytes and one selected owned transport. Any capture/guard/persistence
failure prevents further dispatch. Build admission rechecks raw records,
signatures, exact test target/runner, source maps, JVM execution and lint before
installation. Complete instrumentation status bundles must match source names,
start/pass pairs, counters and one final runner footer. A footer alone cannot
establish a passing test roster.

## Verification actually executed

Environment: Windows, Python3.14, JDK21, AGP8.10.1, Kotlin2.2.21, Compose
BOM2025.05.01/runtime1.8.2, NDK29.0.14206865 and Rust1.93.1. Existing tools and
dependencies are reused; Gradle/Cargo build configuration remains offline.
Only API35 Google APIs/x86_64 executes on fresh isolated 2GiB/two-CPU guests.
Compile/target36 and ordinary minimum26 remain. ARM64 packages but is not run.
No physical phone or model is inspected, copied, loaded or benchmarked here.

| Final procedure | Actual result | Owned elapsed / exit |
|---|---|---:|
| Targeted three new Python modules plus product/controller audit regressions | 121 passed; 0 failure/error/skip; 5.289s test time | 5,749ms / 0 |
| Full `scripts/tests` discovery | 1,153 passed; 0 failure/error/skip; 99.485s test time | 100,814ms / 0 |
| Clean JVM-result/controller rebuild, app/controller lint and three APK assemblies | 234 testcases in 27 XMLs; 0 failure/error/skip; 11 subsequent artifact commands pass | 34,983ms / 0 |
| Final Android component phase | 10 methods / 3 classes; 81 SDK command records completed0, cleanup true, stderr0 | 292,213ms / 0 |

All four final phases retain complete capture and known local Job cleanup.
The client count includes required read-only PowerShell server observations.
Their **750 tracked input mappings match before/after and across the phases**.
These bind every tracked file in the app/crate/fixture/script/benchmark input
trees, including all five SQL migrations, plus the root manifests. Root README
and `docs/` report changes are outside those input trees.
Times above identify test/supervisor durations, not inference or gameplay
latency. Lint has three existing warnings (one app/two controller), zero
errors/fatals. The Gradle log proves the JVM test task executed after clearing
its old results; this is not credit for up-to-date XMLs.

Reproducible commands, with private absolute locations supplied through arguments:

```powershell
python -B -m unittest scripts.tests.test_android_process_verification scripts.tests.test_android_process_client scripts.tests.test_android_instrumentation_evidence scripts.tests.test_audit_apk scripts.tests.test_audit_process_controller
python -B -m unittest discover -s scripts/tests -p "test_*.py"
python -I -B benchmarks/android_process_verification.py build --out "$evidence/build" --sdk "$sdk" --java "$java"
python -I -B benchmarks/android_process_verification.py components --out "$evidence/components" --sdk "$sdk" --powershell "$powershell" --build "$buildResult" --proposal "$runProposal" --running "$runningReceipt" --server "$serverPin"
```

Private barrier wrappers run the two Python suites with equivalent standard
unittest loading inside the existing Job owner, retaining both raw streams and
source maps. Their actual entrypoints are `python -I -B <private>/host-regressions-v4.py`
and `python -I -B <private>/scripts-discovery-v2.py`; wrapper bytes and receipts
are retained privately. The direct three-new-module check passes 68 methods. One host
regression launches an actual isolated interpreter; another transfers all256
byte values plus Ctrl-Z/NUL/non-ASCII/LF suffix bytes exactly through a real
Windows child. Bounded overflow and late zero-exit timeout refusals are tested.

## Native component scope

| Class | Actual methods |
|---|---:|
| `RetiredSelectionFixtureInstrumentedTest` | 4 |
| `RetainedParentFixtureInstrumentedTest` | 4 |
| `RetainedParentFallbackNativeTest` | 2 |

The first eight methods exercise actual APK-contained native loading and
UID/argument/hash/path refusal. The two new native methods use the real Rust
gateway and typed archive operations: a retired nonroot parent becomes publicly
unavailable, the retained child keeps original inherited receipts and eligible
views, recovery selects A0 without accepted messages and emits a one-shot
unavailable-selection flag, and stale parent Ready work is closed while child
Ready commits once with an idempotent repeated receipt. Prepared Ready work is
not an unsent editor draft; draft clearing and a rendered notice remain external
UI-case gates. Intentional parent retirement is a canonical
mutation; this report does not call all canon globally unchanged.

These are component fixtures, not real saved-task process deaths. Raw archive
handles close synchronously; other adapter/fork closes remain asynchronous
requests, not joined-drain proof. Successful SDK-client closure is local process
ownership evidence, not remote Android flush evidence. Repeated methods on fresh
guests remain the same ten distinct methods, not additional distinct coverage.

## Artifacts and preserved failures

The final build and installed readback bind these exact APK bytes:

| Artifact | Bytes | SHA-256 |
|---|---:|---|
| Product | 24,555,355 | `ab1030cdbe7cc05833213f0f1064563fcf7893164961f93824927e89a9bc5fc4` |
| Instrumentation | 2,752,699 | `997f0ece760ddb5af9497b2d6d529f87292786098d9118b98660eaa2baaa507a` |
| Controller | 53,113 | `90bd8030963748ee6a98e783793e4f0588f9a131c01c05f90f4f6fe7fecb7499` |

Build-v1 completed Gradle and all eleven commands but final admission refused
the test manifest: aapt2 emitted the full Android namespace URL rather than
the short alias. The correction admits only those two attribute-prefix forms,
keeping exact target/runner checks and negative fixtures. Its failed terminal
record is unchanged; no installed cohort or native result is credited to it.

Components-v1 installed/readback-verified the three packages, then root's
50-character class-derived label exceeded the unchanged 48-character SDK limit.
The guard refused before a 66th command or any instrumentation invocation.
Its 65 actual clients completed cleanly, but the worker failed: 307,098ms/exit1.
That guest is permanently quarantined. Short fixed labels and an interoperation
regression fix the caller; no limit, footer, UID or roster check is relaxed.

The first successful device cohort (source5a82772f) passes the same10 methods
with84 clients/374,123ms. A final review identified an eager optional union
annotation incompatible with the documented Python3.9 import baseline. The
single postponed-annotations header matches other repo modules. Final-source
host/build/device checks were rerun; Python3.9 itself was not executed. Tests
here use Python3.14. Earlier author test failures and the prior packet's missing
original evidence remain distinguished from these fresh final records.

A final input audit found that the original suffix-selected 724-entry map
omitted the five embedded SQL migrations. No SQL change was observed, but those
older maps do not prove SQL-byte stability. The final source binds all tracked
files under the input trees without an extension whitelist; an actual mapping
regression covers SQL, extensionless scripts and future-extension assets. All
final checks use the expanded 750-entry map. Older positive records keep their
original narrower attribution and are not promoted.

## Closure, private retention and next task

The first three guests close through their exact proposal-bound stop markers:
568,390ms, 477,334ms and496,201ms, with cleanup/capture/closure true and no
guest-flush claim.
The final expanded-input guest also closes at **399,174ms** with
`stop_requested`, cleanup/capture/closure true and guest-flush false. All four
owner CLI sessions finish exit0. The worker's exit1 at requested Job termination is not reported as a spontaneous
successful guest exit. No guest flush or power-loss proof is claimed.

Postflight native observations match both original unrelated emulator launcher
identities and the unchanged original ADB server identity. The two original
untracked physical-model directories remain. No unrelated emulator was stopped,
no global ADB server lifecycle command was issued, and no system setting changed.

Final selected private index: **1,204 files / 142,165,770 bytes**, SHA-256
`30921696ec990aff5460ce9bcc8cfa1e05d51ce0eeb72a0644e20553f32ca897`.
All 914 files in the earlier checkpoint index were rehashed unchanged. The new
postflight record retains original/observed native identity tuples so equality
can be independently recomputed without publishing those private identifiers.
Every indexed file is rehashed after writing the index. It
retains failed attempts, author host evidence, final raw commands/class outputs,
source maps, APKs, reports and owner/closure receipts. Guest images/data,
databases, model weights, compiled caches, temporary test roots and other-project
data are excluded. No original missing evidence is recreated by this new index.

The [previous evidence-loss report](ANDROID_RETAINED_PARENT_VERIFICATION_2026-10-26.md)
remains accurate: missing original build/load/run records and older selected
indexes were not reconstructed or promoted. Fresh records replace only the
specific gates actually rerun here. No raw private diagnostics, device
identities, APKs, databases, caches or model weights are uploaded.

Next runnable M10.02/M08.05 supporting task: version the external controller
host invocation/readback, run the root saved-task control, then the frozen
[retained-parent two-death protocol](ANDROID_RETAINED_PARENT_PROTOCOL.md), with
its four binary preservation sidecars. Run affected active-child/retired-leaf
controls and broad Android regression on the same final artifacts. Do not adopt
failed or partial fixtures. Real-phone/ARM64/model quality/performance, complete
lifecycle fault coverage and full task acceptance remain pending. The physical
model admission policy is unchanged and was not resampled. Nothing is merged
or released; unrelated emulators and system settings remain untouched.

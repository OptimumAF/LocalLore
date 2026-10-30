# Held AUTHOR / SDK6 host and build verification, 2026-10-29

M10.02 and supporting M09.06: this implementation slice is in review in
[PR #276](https://github.com/OptimumAF/LocalLore/pull/276). Full task checkboxes
remain unchecked. The new Android live-death experiment is **unrun**.

The [previous approved buffered run](https://github.com/OptimumAF/LocalLore/pull/275)
completed transfer, import, AUTHOR creation and passive reopen. Its AUTHOR PID
was already absent before force-stop. Its stronger live-process fault gate
remains false; none of the results below changes that capture.

## Implemented and frozen scope

The [versioned protocol](LIVE_AUTHOR_DEATH_PROTOCOL_V1.md) adds a separate SDK6
path, held instrumentation selector, real native-workspace checkpoint,
read-only native v2 clock observation, independently owned pending worker,
canonical pre-fault validation, interrupted-runner qualification and
cross-session replay. Cancellation must publish a forced refusal before native
close or retain the handle through its advertised expiry. SDK5 stays unchanged.

The native builder also binds its actual worker and request before compiler
dispatch. File-only replay checks the receipt's shape/request/Python path; it
does not independently attest a live OS worker. There is no new production
dependency, permission, Activity, service or canonical engine authority.

Executable commit: `1fdc006bea214b14290a9e137a8e48acd2137d14`, in physical
`D:\Worktrees\LocalLore-m10-live-death-build-v2`. Its actual raw maps contain
**2,288 tracked files /1,008 declared build inputs**:

| Record | SHA256 |
|---|---|
| Actual SDK job source map | `ef0688f6043013bb0559cf8a52d8d234cd7fd370d54fe7aead9a7ba6b9c17a7b` |
| Actual SDK job build-input map | `eb26954de845334d009e71466c7ce15f3d4fd967be194bbcfec7b2c26f5bb3f5` |
| Source-derived 600-method JVM roster | `752ecb62402acfb6ad185f27feeabcd69d4fbb5a1a794ed9074c512766ad100f` |
| SDK6 build admission manifest | `32cbc1851e9757c11bfe6c2f019e58f03d2f9208873cf595ef6b1f6255efd5c0` |
| Native probe build manifest | `c549150041e9d9c92add0fa2c118fea9e3d736b919d4b0101d0cb71e31f7daad` |

Two inherited integration-checkout files differ only by CRLF. Qualification
uses the frozen checkout's own bytes, without relabeling that other raw map.
The earlier `a69d5c55` checkout and failed suite remain frozen separately.
Later report/command documentation edits do not qualify a different executable.

## Verification actually performed

| Procedure | Actual result |
|---|---|
| Full Python script suite | **2,358 passed**, 0 failures/errors/skips/expected failures; 314,632 ms owner, exit 0 |
| Separate synthetic runtime-spike suite | **16 passed**, 0 failures/errors/skips; 10,616 ms owner, exit 0 |
| Offline Android build | Exit 0; 282,458 ms owner; Gradle reports 4m32s, 87 tasks /84 executed |
| JVM reports and exact source roster | **600 cases /59 XML reports**, 0 failures/errors/skips; all 12 new checkpoint-policy cases executed |
| Same-job fresh lint | Analyzer 32.4.1, analysis did work, dependencies checked; **0 errors/fatal, 10 warnings** |
| APK and native packaging | Both packages/signatures verified; product privacy audit, compiled held/legacy selectors and two Rust JNI target/package chains passed |
| Read-only Android process observer | Compiled once for `x86_64-linux-android35`, 1,732 ms owner, exit 0; **never executed** |

Both final host owners, the build owner and native compile owner report complete
capture and cleanup; final source/helper/head checks match. The full Python
suite includes 66 new tests. Counts are not additive with the earlier targeted
cohorts. Lint warnings are OldTargetApi (1), GradleDependency (1), ObsoleteSdkInt
(1) and UsableSpace (7); this report does not call lint warning-free.

Windows/Python 3.14 used the installed Java 21, Android build-tools 35, NDK
29.0.14206865 and pinned Rust toolchain. Existing cached dependencies and tool
pins were checked; no download or global configuration change was required.
Process-local TEMP/TMP/TMPDIR use `D:\Dev\_Temp`, and project caches/output stay
on D:. The existing signer is used in place, without key copying or generation.

The actual finite wrappers ran from that frozen checkout, with `B11` meaning
`D:\Dev\Experiments\LocalLore\2026-10-29-live-death-witness-v1`:

```text
python -I -S -B B11/tests/check-final-host-v5.py full full-host-v4 1fdc006bea214b14290a9e137a8e48acd2137d14 600
python -I -S -B B11/tests/check-final-host-v5.py spike runtime-spike-v2 1fdc006bea214b14290a9e137a8e48acd2137d14 60
python -I -S -B B11/android/build-sdk-FROZEN-v3.py sdk-build-v1
python -I -S -B scripts/build_android_author_process_probe.py --ndk C:/Users/Avery/AppData/Local/Android/Sdk/ndk/29.0.14206865 --output B11/native-helper-v1
```

The frozen Gradle driver SHA256 is
`061ba6b477e8d281ea25ae51b1034a5126392f9ab32dc38cfcf10a5ab83252a4`;
recipe SHA256 is
`099acdbebe69f4a4513f01ea97c46cec70cad6dcb500637a761e0fa5799fcd43`.
Its retained request contains the complete offline Gradle arguments, task list,
tool inputs and environment. It explicitly compiles Android instrumentation.
Command/owner ceilings stay 600/900 seconds; the native builder retains its
300-second outer owner and 600-second nested capture ceiling. The outer owner
bounds the actual native attempt. No deadline was extended to obtain a pass.

| Produced artifact | Bytes | SHA256 |
|---|---:|---|
| `org.locallore.app.litertverify` APK | 78,423,520 | `ff704f7ac48d591c9359e1e685ff32a81e732ca817345ac8cfda256606f68b3e` |
| `org.locallore.app.litertverify.test` APK | 2,280,287 | `13de5c8b2ca9f271ce85c047a6c75913a354fb4e2ab1a66a3e72d3ebcd425f0d` |
| Read-only x86_64 process probe | 15,744 | `0dfe4d584b7f656552af773ded0b49cfc14a23e52b971d6110314ee2951f81dd` |

## Original failures and review

Original assertions and failed captures remain preserved:

- Pending cancellation: 8 tests /1 assertion failure, then the same 8 pass;
  expanded 11 pass. A later complete 2,358-test run catches a stale synthetic
  fixture missing the newly required parent start timestamp. Only that shared
  fixture metadata changes; all eleven test method bodies/assertions remain
  identical. The final 2,358-test suite passes.
- Complete byte-backed prerequisite graph: the first positive replay errors on
  JSON ordering; a later 8-test run has two assertion failures for chronology
  and premature foreign reads. The same 8 pass after fixes. A separate session
  header regression demonstrates three foreign reads before rejection, then
  passes unchanged. This is premature read, not acceptance bypass.
- Native compiler-start gate: original 10 tests /7 assertion failures, then the
  unchanged 10 pass. Compiler I/O is mocked in those tests; actual compilation
  is the separate owned build above.
- Build replay: first six original cases pass. Review adds one suite/report
  identity regression and two methods covering hidden XML failures and a late
  native owner; all reproduce assertion failures and pass unchanged after
  fixes. The final full suite includes all nine.

Two launcher setup attempts are retained separately: namespace discovery first
refuses before tests; an incomplete module loader then finds seven import
failures and is deliberately stopped through its exact owned worker handle,
with parent capture/job cleanup complete. Correct canonical discovery verifies
all 130 modules /2,358 IDs and zero import errors before executing tests. Neither
setup attempt is presented as a product regression or qualifying suite pass.
One preparation-only filename assertion is also retained; no build ran then.

Official Android source explains why completing instrumentation cannot prove a
later external kill: [instrumentation finish](https://android.googlesource.com/platform/frameworks/base/+/cc8bb19595c661f5cf42f330457000e643c67d1b/core/java/android/app/Instrumentation.java)
and the [command watcher](https://android.googlesource.com/platform/frameworks/base/+/cc8bb19595c661f5cf42f330457000e643c67d1b/cmds/am/src/com/android/commands/am/Instrument.java)
have distinct target/command lifetimes. The [clock JNI source](https://android.googlesource.com/platform/frameworks/base/+/cc8bb19595c661f5cf42f330457000e643c67d1b/core/jni/android_os_SystemClock.cpp)
and [clock API](https://developer.android.com/reference/android/os/SystemClock#elapsedRealtimeNanos())
support the review joining `elapsedRealtimeNanos()` to `CLOCK_BOOTTIME`, including sleep; timestamps are
comparable only within a matched Android boot. This is compatibility research,
not installed-image attestation or device measurement.

Independent file-only replay passes once in 8,132 ms, with all 76 checks true:
the actual raw source/build maps, exact JVM source/XML roster, 106 SDK plus ten
native artifact pins, JNI/package chains, fresh lint and the unpatched SDK6
closed build verifier against the explicit nonruntime projection. Receipt
SHA256: `e76ffe5a345fc06a2ed27ba674b77f8c326dfc9210cff983b51f202eed797ded`.
It reads retained DEX/auditor evidence without rerunning those audits, and does
not independently attest past OS identities. No compiler, test, SDK, model,
signing-key, target or ledger operation is dispatched by this replay.

## Preservation, storage and remaining gates

The initial `9ef5a4d5` snapshot retains 2,595 copies /50,242,384 bytes, with
independent complete hash/byte readback. It does not qualify final source.
Its first checker refused an extra Windows stat/fstat ctime comparison for 502
files before hashing them. The preserved corrected checker keeps each API's
own before/after stability checks and verifies every declared byte count/hash;
no missing or mismatched copies remain.

Final create-only recovery at
`D:\Dev\Recovery\LocalLore\2026-10-29-live-death-witness-v1\final-v1`
copies all **2,836 original/copy pairs /199,681,800 bytes per side**:
2,288 frozen-source files and 548 packet files. Root checks source stability,
every copied byte count/hash and the packet file set; an independent 9,067 ms
readback then checks every listed original and copy, exact rosters and ordinary
D: paths. Missing, mismatched and unsafe entries are all zero.

| Final recovery record | SHA256 |
|---|---|
| Source/capture manifest | `4989b303f83afad46e9ed8b7421a0778227a7b141f8fe0b0cc03368457fe4c8b` |
| Independent original/copy readback | `da67b0798fd31b4f0703b0e19858f427ba0867c4c6d4fdf367f1e2a907e318ce` |

The packet also retains a verified 13,839,340-byte bundle of the implementation
branch through `1fdc006b`; this is not an all-repository-ref backup claim. Later
audit, budget and public-report records form a separate small post-seal appendix.
Generated build trees, old checkouts, unique captures and earlier recovery stay
in place. No cleanup or retirement is performed.

The declared offline-build budget was expected 8–12 GiB /maximum **14 GiB**,
including source, captures and recovery. A final no-follow metadata observation
counts the four disjoint W1/W2/B11/A11 roots once, adds only positive observed
shared-cache growth and its own receipt: **1,275,698,510 bytes**. A separate
1 MiB allowance covers the small post-seal report/audit appendix, leaving
13,755,638,450 bytes below the declared maximum. Missing, reparse, error,
timeout and unknown counts are zero. Receipt SHA256:
`286980ad45354637652e17fed8a9fbd45e670d24985407617fd3e208e7284ffb`.
This is persistent named-scope logical accounting, not a filesystem quota,
peak/transient TEMP measurement or exclusive attribution of shared-cache work.

Private captures, model weights, saves and keys are not uploaded. Both original
guest roots and the buffered-run recovery remain untouched. A read-only shared
ledger observation still records two closed, unretired guests charged
50,054,753,017 bytes under the unchanged two-root /64 GiB guard. A preparing/live
guest needs a 40 GiB reservation. Source constants grant no permission to
prepare or boot another guest; the previous one-run grant is spent.

The new Android hold/fault/restart execution, physical-phone/ARM64 runtime,
model quality, sustained performance and broad reliability gates remain open.
Compiling both JNI ABIs is not phone qualification; the process observer is
x86_64 only. No other emulator, shared ADB service, system settings, repository
access or merge state is changed. Next: review exact preservation/retirement
targets and obtain fresh guarded admission/authorization for one actual
held-AUTHOR live-death run. No retirement or new run is performed here.

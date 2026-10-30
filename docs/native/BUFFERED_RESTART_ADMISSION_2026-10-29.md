# Buffered restart: fresh profile and host build preparation

Refs #14 (M10.02), #13 (supporting M09.06), following open/unmerged #269.
Full task and runtime criteria remain unchecked. This packet prepares source
and an offline build; it does not authorize a guest or qualify a restart.
The [previous guarded run](GUARDED_RESTART_RUN_2026-10-29.md) remains refused.
Its guest, model/app state, source, build and captures remain preserved.

## Fixed profile

The SDK5 contract now names only
`D:/Dev/Experiments/LocalLore/2026-10-29-buffered-restart-v1/avd-v1`.
That path was absent at preflight. No directory, ledger reservation, guest,
private ADB service or runtime action is created by this source change.
Both the immediately previous `restart-after-metadata-v1` root and the older
`author-restart-controller-v1` root are rejected by the new profile.

The production change is one constant. Two existing test constants match it;
all 28 restart-contract and seven existing fresh-profile method bodies remain
identical. JSON cannot select another root, registry or implementation.
SDK4/SDK5 wire and proof formats, 15/24 mandatory source rosters, one-shot claims,
resource floors, ownership, storage admission and deadlines are unchanged.
The [measured streaming hash implementation](RECEIPT_DIGEST_STREAM_V1.md) is
retained without further tuning or another timing capture.

Pure admission validation checks closed metadata and copies accepted input.
Synthetic matching hash strings do not prove live source freshness, storage
admission or human authorization. Those remain distinct mandatory gates.
Before any future guest work, use the current guarded preparation/SDK5 owner
and the fixed shared D: ledger under the [storage lifecycle](../runtime/android/RECEIPT_AVD_STORAGE.md).
Every earlier guest grant is spent; this prospective path has no boot grant.

## Original profile evidence

Six original methods were committed before the fix. Baseline execution records
three meaningful assertion failures and zero errors: the old constant remains,
the immediately previous spent root is accepted, and the new root is refused.
The other three methods pass. The same six assertions pass after the fix
(5,072 ms/exit1 before; 5,275 ms/exit0 after). The test source is byte-identical.

The broader profile cohort passes **41 methods**, zero failures/errors/skips/
exclusions, in 64,669 ms/exit0, with known capture/cleanup, empty stderr, stable
2,231 tracked raw source hashes and no covered forbidden IO attempts. This
cohort includes the six new and 35 existing methods; the counts are not additive.
Native/SDK/path/socket/ledger effects are refused in the pure fixtures.
Independent AST review confirms only the three constants changed in existing
code and all protected guards and method bodies remain unchanged.

## Build and storage boundaries

The build uses a separate frozen physical D: worktree. Exact executed
source and artifact bindings belong to its actual receipts; later report
commits must not replace that source attribution. Existing frozen `f1b81363`
and `4c53db36` builds and both original dirty guard worktrees are untouched.

Existing locked Gradle/Cargo/Android caches stay on D:. Installed SDK/Java/Rust
and the existing debug signer stay in place. There is no dependency/runtime
upgrade, download or signing-key copy. The build is offline, with process-local
D: temporary/cache settings, finite owned workers and retained raw captures.
The process reader may be compiled for inspection, never executed here.

The declared incremental budget is 8–12 GiB expected, 14 GiB maximum, including
the new worktree/build outputs, cache growth, captures and recovery. Named-root
before/after metadata and contextual volume free space are observations, not
an OS quota or exclusive attribution. No cleanup or retirement makes room.
Host outputs remain at
`D:/Dev/Experiments/LocalLore/2026-10-29-buffered-restart-admission-v1` with
matching D: recovery. Model weights, old guests and ignored build outputs
remain in their original locations.

Android execution, complete restart proof, real-model/physical/ARM64 performance
and full app journeys remain separate gates. The other emulator, shared ADB
service and system settings remain untouched. No merge or release occurs.

## Frozen-source host verification

Actual executable/build source is
`778f6f78d94b323b3b12f73c6def3e92bb1254a0`, kept clean in
`D:/Worktrees/LocalLore-m10-buffered-build-v1` on
`build/m10-buffered-restart-frozen-v1`. Its own raw checkout has **2,232 tracked
files / 985 compiled-prefix entries**. No cross-worktree newline normalization,
tracked alignment or old generated native-library copy was applied.

Full Python discovery from that physical worktree passes **2,269 unique tests**,
zero failures/errors/skips/exclusions. The finite owner exits 0 in **439,104 ms**,
with known cleanup/capture and empty stderr. All 2,232 source hashes stay stable;
covered Python auditing records zero forbidden IO attempts and eight separate
exact standard-library null-sink opens. The audit is not an OS/native sandbox.

With process-local `TEMP`, `TMP`, `TMPDIR=D:\Dev\_Temp`, the exact command is:

```powershell
python -I -S -B D:/Dev/Experiments/LocalLore/2026-10-29-buffered-restart-admission-v1/check-host-v1.py all frozen-full-host-v1
```

Fixture runner SHA256:
`ba9f5350facf9dfa60a36cf6dc81e5e9eb5e94eee43f194e87cd5f9d832a6ca2`.
Actual full result SHA256:
`7210514f130559515d1686bc4153a0f43312dac3bfde4efa24649e9484cec19b`.
This later verification text is not substituted into the frozen source or its
build/admission bindings. No runtime outcome follows from a host-suite pass.

## Actual offline Android build

The reviewed offline recipe executes once from frozen source `778f6f78`, after
the full host suite closes. Its driver differs from the prior reviewed build
mechanism only in the worktree, output root, frozen head and tracked-file count.
Existing locked tools/caches remain in place; no dependency, runtime, signing
key or global tool setting changes. The actual commands, with D: process-local
temporary/cache settings, are:

```powershell
python -I -S -B scripts/build_android_author_process_probe.py --ndk C:/Users/Avery/AppData/Local/Android/Sdk/ndk/29.0.14206865 --output D:/Dev/Experiments/LocalLore/2026-10-29-buffered-restart-admission-v1/native-helper-v1
python -I -S -B D:/Dev/Experiments/LocalLore/2026-10-29-buffered-restart-admission-v1/android/build-sdk-v1.py sdk-build-v1
```

The helper compile exits 0 in **2,444 ms**; the SDK build exits 0 in
**264,782 ms**. Both have known capture/cleanup and empty parent streams. The
ELF helper is **never executed**. JVM results are **588 unique cases / 58 XML
reports**, zero failures/errors/skips. APK/signature/package/manifest/JNI,
dependency and analyzer audits pass. All 2,232 raw sources, 985 compiled-prefix
entries and tool bindings remain stable in the actual worktree.

Fresh same-job lint uses analyzer **32.4.1**, with actual `didWork: true`, zero
Error/Fatal and ten warnings: seven UsableSpace, one GradleDependency, one
ObsoleteSdkInt and one OldTargetApi. No separate lint phase or fallback rerun
is substituted. The unchanged pins include SDK36/build-tools35, NDK29,
Rust1.93.1, Java21, Gradle8.11.1 and LiteRT-LM0.18.1.

| Newly built artifact | Bytes | SHA256 |
| --- | ---: | --- |
| Product APK | 78,423,520 | `c8adf07e9ae6802f98108ea8f9d0f061200119203273c95dd6f7e98069bfcd09` |
| Test APK | 2,272,447 | `215731ef23e46f1dd1d97f9fb846672eaa954467332069f8723520f3101a0221` |
| Compile-only process helper | 13,848 | `8c9408c4af7ce73d4e39dde712c291dd1d5e042e53ff407414dfa4d864d41972` |

These new outputs reproduce prior artifact bytes. Their actual new build job
and frozen source establish their attribution; old artifact paths or receipts
are not relabelled as a new build.

Independent file-only build/lint replay passes: exact 98 SDK and ten native
artifacts, own-worktree source/compiled maps, all JVM XML/cases, APK/DEX/JNI/ELF,
dependency/analyzer provenance and actual lint inputs. Both ABI libraries and
the defined AUTHOR/restart instrumented methods are present; neither ABI was
executed on Android in this packet. The native compile's started receipt lacks
a direct request binding. That limitation remains explicit; artifact/source/
compiler checks do not authenticate device execution or a guest grant.

Build result SHA256:
`753cd0c47229c3c54be3dc67b4aebb7b4882b6edef6b88a228eab4689c72bcf6`.
Independent build/lint receipts:
`e65851ff51785ed7543ae2265e38edc57e104d1e379f063125f381a4a301febd` /
`4978952a646a8cedd0122b92f8d9e27c4c3e22cbe05f601592e666fb64287dfc`.
The joined, unchanged 12-key **build-only** admission manifest SHA256 is
`2085719820bde13805ad811683e439249af5118128a1bee38fe4821b32fa60ab`.
There is no target admission, human authorization file or guest reservation.

Named-root metadata observes **814,987,138 bytes** aggregate logical growth
between the immediate pre-build and closed post-build snapshots, within the
14 GiB allowance. This excludes later recovery and does not attribute shared
cache/volume activity exclusively to the build. The separate frozen worktree's
ignored outputs, APKs, source and all raw reports remain preserved. No cleanup
is performed. The earlier closed profile captures already have a verified
28-file / 1,128,070-byte recovery copy; final source/build recovery is separate.

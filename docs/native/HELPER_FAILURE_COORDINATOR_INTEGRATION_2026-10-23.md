# Helper failure coordinator integration, 2026-10-23

Refs #8 M04.04 / PR #94. Original head `37e83419771a6a363dce571ca041b11e1b7f2a4b`
was merged normally with accepted main `b3543d6a3d5e904814c39fd41fc4c93f5a81c4ba`
(#87). Root claims [#8](https://github.com/OptimumAF/LocalLore/issues/8#issuecomment-6371081924)
and [#94](https://github.com/OptimumAF/LocalLore/pull/94#issuecomment-6371082349).
Qualified helper source is `4e48f69efde027c0a1f3f78f98b99ec180362a8b`;
independent fixture correction/evidence bring final checked source to `3e7dda7`.
No production Core, Host, Store, JNI, schema or dependency change is included.

## Review corrections

[Independent stack review](CAPACITY_STACK_INTEGRATION_REVIEW_2026-10-23.md)
identified a source-only admission gap after `released()` suspended between
retry rounds. `4e48f69` rechecks both sticky ownership atomics immediately before
each actual native open. The existing `finally` still closes every acquired
handle; four handles, eight seconds, five milliseconds, counters and assertions
are unchanged. This is cooperative admission, not an atomic OS transaction.
The actual suspended concurrent-poison schedule was **not executed**: this
instrumentation-only loop has no existing JVM/native-double route. No copied
loop or source-pattern test is substituted. The actual test source compiled
successfully in the fault APK below; original emulator evidence remains historical.

A separate accepted-main fixture name collision interrupted the coordinator's
M05 all-feature workspace run before a story assertion. Independent review
reproduced concurrent PID/timestamp collisions. Imports `615f955`/`a21a96d`
add a process-local atomic suffix and deterministic actual eight-thread regression,
preserving all original semantic test bodies. Full host rerun below passes.
[Diagnosis and retained failures](RETENTION_FIXTURE_IDENTITY_DIAGNOSIS_2026-10-23.md)
distinguishes this test defect from production or M05 causality. It cannot prove
which exact pair collided in the initial log, whose filename was absent.

## Actual coordinator execution

Windows 11 Pro10.0.26300; Rust/Cargo1.93.1, isolated Python3.14.9/SQLite3.50.4,
JDK17.0.6, Gradle8.11.1/AGP8.10.1/Kotlin2.2.21, SDK36/NDK29.0.14206865.
All local targets/TEMP/outputs are task-owned D-drive paths. No ADB, device,
emulator, model, worker, UI launch or desktop control was used here.

```powershell
# Only the dedicated capacity target uses this flag.
$env:LIBSQLITE3_FLAGS='-DSQLITE_MAX_PAGE_COUNT=32'
cargo +1.93.1 build -p locallore-workspace --example capacity_relief_probe --locked --offline --target-dir <cap32-target>
# Repeat with each fixed selector and a distinct new directory:
<capacity_relief_probe.exe> --directory <new-directory> --python <python.exe> --helper-fault <malformed|overflow|timeout|after-fill|cleanup-refusal>
<capacity_relief_probe.exe> --directory <new-accept> --python <python.exe>
<capacity_relief_probe.exe> --directory <new-cancel> --python <python.exe> --cancel
cargo +1.93.1 test -p locallore-workspace --example capacity_relief_probe --locked --offline --target-dir <cap32-target>
Remove-Item Env:LIBSQLITE3_FLAGS
python scripts/check.py host --offline
cargo +1.93.1 clippy --workspace --all-targets --all-features --locked --offline -- -D warnings
python scripts/android_capacity_fault_probe.py build --offline
```

The final Android command used the fixed sibling-import bootstrap documented in
[preceding integration](SCHEMA3_CAPACITY_COORDINATOR_INTEGRATION_2026-10-23.md)
for the isolated Python. No global interpreter configuration changed.

| Check | Actual result |
| --- | --- |
| Five actual fixed host child faults | PASS: actual initial17/pad14/15th insert Full before fault; terminal/reaped children; zero post-failure Host calls/workspace opens |
| Malformed, overflow, timeout, after-fill cleanup | Freshly admitted fixed cleanup restores exact schema and frees15 pages; overflow/timeout observe successful owned kill and reap |
| Cleanup-refusal | PASS means expected failure observed: original and cleanup failure distinct, both children terminal/reaped, padding retained; no successful-cleanup claim |
| Normal acceptance/cancellation | PASS: two actual native commit-Full attempts, unchanged canon, exact relief; same-key accept once/revision1 or terminal cancel/revision0; zero fresh submits/prepares |
| Ownership policy | 2 actual Rust policy tests PASS; not an actual unkillable-child incident |
| Full host | 442 workspace Rust +3 linker, 377 Python, four fixture bindings, fmt/default strict Clippy PASS; four existing explicit Rust ignores |
| All-feature strict workspace Clippy | PASS |
| Android fault profile | Both ABIs/app+test APKs built offline; 146 JVM PASS, zero failures/errors/skips; lint zero errors/one existing warning; fixed32/schema3/format2/faults1/testOnly/16KiB audit PASS; 77 tasks executed, 3m55s |

No ordinary Android rebuild is attributed to this packet. Original author's
18 final emulator passes and earlier failures remain separately attributed in
[original verification](HELPER_FAILURE_VERIFICATION_2026-10-23.md); those do not
cover the coordinator's new per-open guard schedule. Root compiled that guard
and ran host/JVM/audit checks only. Broad M04.04 remains unchecked: page ceilings,
policy tests and known-reaped children do not qualify partition ENOSPC, power
loss, unknown live OS ownership, phone/ARM64 execution or models.

## Private evidence bindings

Logs, APKs and synthetic databases stay local/ignored. SHA256:

| Artifact | SHA256 |
| --- | --- |
| full host | `29adf756eab52f756ae76280c6167363a1d5e3253f4fb5c9f25d3b0af1e4c2dc` |
| strict all-feature Clippy | `6d2ca95f3f3ab51fbdbbbe6cde443cfc3fed2d2145e4cf1fa03a88bf0e204d56` |
| malformed | `f0ab2af0be9e0d2020ba2871aad4c7eefd5a0da8d17e54b70923f91f006da7b9` |
| overflow | `77a14b6da4788b95ad8c00bce4d444a8019417a1b21654ae5f5bfdb97c9fbe3b` |
| timeout | `a92c4e5f7661eba61dc38a17c385dcf990a784c034e82cac938ac32f5ee29a00` |
| after-fill | `dd3c221f1473ca775ce8defda2520071eb69fabd6e723bfe3be2ad67e6bd4302` |
| cleanup-refusal | `a30034e12c94c2d685c1f89e561fe0b6815c7b5d785a780b17f26b21e3eedd43` |
| normal accept | `4a4589a3c2e9c0181123a1de728e44c250ba72b611945e64f475889240594431` |
| normal cancel | `e2393c9edbc4d118e21dab65f61bbfbfc65380755bf2f6bdfe00f22630254af6` |
| policy tests | `0ba6f394f581f906d3ea254ab6a40b396743dee8a421353fbb9db9ed452a7b75` |
| Android build/audit | `b3aa359522ebbe9a9e12103315f4d6885409993fced736dadd99c27e8df98df94` |
| fault app APK | `3493550484660d714f2f92c393d5be6413d3e71fffbd8c2048863b99e6d0b865` |
| fault test APK | `42318688f3ea56c242095ea7ff87cde9edc290217ddf1af22c8ada87b046e596` |

Owner authorized tested merges and use of existing owner permissions; no review,
settings or release was fabricated. After this focused merge, next runnable
shared work is schema4 bounded memory maintenance/consumer integration, with
fresh capacity calibration required if the physical fixture changes. Desktop
free-text, timeline/correction UI and final D09 acceptance remain separate work.

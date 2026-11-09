# Windows job cleanup verification - 2026-11-02

B90; refs #14 (M10.02), supporting the SDK16 profile in PR #360. Tested executable/test source: `552ad2b976eda5afc551c69d516d3f8741e788ef`. This is host ownership work. It creates no SDK16 input, authority or boot claim and does not qualify Android gameplay, device/model feasibility or milestone acceptance. The focused implementation PR stacks on PR #360; this report does not authorize a merge.

## Result and implemented boundary

Status is in review; full M10.02 criteria remain unchecked. Later README/report
publication changes are documentation only; tested implementation/tests stay
byte-identical to `552ad2b976eda5afc551c69d516d3f8741e788ef`.

The final source passes **28 new Windows cleanup methods, 221 existing regression methods and 39 SDK16 profile methods**, each with zero failures, errors or skips. Genuine frozen B88 artifact create/verify replay also passes. Earlier cohorts and expected mutation failures remain separate below; passing repetitions are not additional unique coverage.

`WindowsJob(pid)` and `close() -> bool` remain the public API. Close success requires successful termination, a successful accounting query observing zero active processes, and successful native `CloseHandle`. Win32 BOOL zero means failure; any nonzero value means success. The five-second polling window remains. The first close latches failure, attempts the owned job-handle close once, and returns a strict cached bool. An uncertain release retains the handle number diagnostically without retry authority. Reentrant/overlapping calls return false without repeating native work and keep the first final result false; the state lock is released during native work and polling.

Construction checks temporary `OpenProcess` handle closure. Configuration/open/assignment or temporary-close failure attempts each acquired cleanup tail once; unknown cleanup becomes bounded `OSError("job_cleanup_failed")`. Successful cleanup can preserve original cancellation propagation. A failed constructor cannot certify closure through fallback child kill/wait. Runtime, receipt supervisor, Android transfer, native TCP owner and recovery outer owner preserve failed cleanup while attempting independent safe wait/join/pipe/capture tails. Capture failure also forces cleanup false, because receipt storage closure consumes that flag. `LiveOutput.close()` attempts every acquired file close despite cancellation, then stays failed without retry. No actual ledger transition was exercised by these injected tests.

The five production paths are `benchmarks/runtime_spike.py`, `benchmarks/receipt_avd_environment.py`, `benchmarks/android_runtime_spike.py`, `benchmarks/windows_native_tcp_state.py` and `scripts/run_library_ui_recovery.py`. Native [CloseHandle](https://learn.microsoft.com/en-us/windows/win32/api/handleapi/nf-handleapi-closehandle), [accounting](https://learn.microsoft.com/en-us/windows/win32/api/winnt/ns-winnt-jobobject_basic_accounting_information) and [job object](https://learn.microsoft.com/en-us/windows/win32/procthread/job-objects) semantics were reviewed for the FIRST contract. This covers class-owned job/temporary-process handles and implemented cleanup tails, not every Python/Popen/OS allocation, disk flush or guest shutdown.

## Preserved verification records

All 12 phases have closed raw stdout/stderr, request/actual-child/command-child/terminal joins and identical before/after raw source maps of **2,694 tracked files**. Five distinct full source ZIPs join **13,470 member byte/hash checks** (2,694 per archive). Source map equality binds source bytes; it is not device execution evidence.

| Phase | Source | Recorded result | unittest seconds | outer-owner seconds |
|---|---|---|---:|---:|
| red-v1 | 0ccb3666 | 26 methods, 59 failures, 0 errors/skips | 0.040 | 1.731 |
| green-v1 | 7d465389 | 26 methods, 0 failures, 0 errors/skips | 0.017 | 1.733 |
| regression-v1 | 7d465389 | 221 methods, 1 failures, 0 errors/skips | 132.726 | 134.474 |
| profile-v1 | 7d465389 | 39 methods, 0 failures, 0 errors/skips | 176.840 | 178.971 |
| reuse-v1 | 7d465389 | B88 create/verify passed | n/a | 4.768 |
| capture-red-v1 | bfbdb69b | 28 methods, 17 failures, 0 errors/skips | 0.025 | 1.786 |
| green-v2 | 79f678ae | 28 methods, 0 failures, 0 errors/skips | 0.020 | 1.734 |
| green-v3 | 552ad2b9 | 28 methods, 0 failures, 0 errors/skips | 0.020 | 1.785 |
| regression-v2 | 552ad2b9 | 221 methods, 0 failures, 0 errors/skips | 147.292 | 149.231 |
| profile-v2 | 552ad2b9 | 39 methods, 0 failures, 0 errors/skips | 211.355 | 213.438 |
| reuse-v2 | 552ad2b9 | B88 create/verify passed | n/a | 4.509 |
| mutation-v1 | 552ad2b9 | 1 expected assertion failure; protocol passed | 1.015 | 2.743 |

Initial `red-v1` has **26 methods / 59 assertion or subtest failures**, not 59 distinct failing methods. It exposes ignored handle-close results, false-success repeats, constructor cleanup and caller-tail failures. `regression-v1` retains one old TCP assertion expecting positive cleanup after constructor failure. That assertion was strengthened to false. Two older receipt assertions after late reader/capture-close failure were likewise strengthened from true to false; their remaining AST is unchanged.

Review then found a substantive capture gap: receipt/TCP/recovery could report cleanup true after capture close returned false or raised. Two additional tests yielded `capture-red-v1`'s **28 methods / 17 assertion or subtest failures** before the correction. All three failure cohorts have zero errors/skips and remain preserved. They are not retroactively passed by later fixes.

The original independent proposal's **24 methods, 108 assertion calls and helper AST remain unchanged**. Root added four isolated reentry/overlap/capture methods. The initial overlap oracle did not prove its non-blocking claim: a synchronous second call could wait for the first query timeout. The final oracle requires a second-thread done event within one second while the first fake native query stays blocked, then releases and joins both threads. `mutation-v1` deliberately holds an RLock across the original close implementation. The strict oracle rejects it at the exact done-event assertion: **one expected failure, zero errors**, with protocol success meaning the mutant was rejected. Production source is unchanged by that mutation.

The new fault methods use a fake kernel32 through the real constructor and finite process/pipe/capture doubles. They cover native BOOL 0/1/2/-1, termination/query/close/time/cancellation faults, acquired-handle cleanup and all five callers. The overlap check uses bounded Python threads with fake native calls. Existing regression methods additionally execute benign real Windows Python child/descendant ownership checks; the final outer supervisor also uses the checked class. Those establish only their measured host paths. Historical RED supervisors used the earlier class, so their reported cleanup does not retroactively prove the formerly ignored CloseHandle BOOL.

B88 replay uses the unchanged 8,656-byte manifest SHA-256 `97037d90a3b738a09054a07d03caf659cb2276774935d0b46535712b31d6f55c`, product APK 28,398,622 bytes / `0b93c6af0772ff6216a0dcbeb2f8b19b1564129f3855336ced7dcafbfca662cd`, and test APK 2,645,072 bytes / `3241aaff3c42fc6c155f04da40cae88aa54e39cd68c10f7cb5178a0b77a9c5db`. It performs byte attestation, not a fresh Android/native build or UI run. Full SDK16 admission/authorization remains separate.

## Recorded local commands and helper versions

Commands ran from physical `D:/Worktrees/LocalLore-original-input-compose-review-v1` with process-local `TEMP`, `TMP` and `TMPDIR` set to `D:/Dev/_Temp`. The installed interpreter was `C:/Users/Avery/AppData/Local/Programs/Python/Python314/python.exe`. The following are recorded invocations, not authorization to replay create-once output paths:

```powershell
$env:TEMP='D:/Dev/_Temp'; $env:TMP='D:/Dev/_Temp'; $env:TMPDIR='D:/Dev/_Temp'
$python='C:/Users/Avery/AppData/Local/Programs/Python/Python314/python.exe'
$out='D:/Dev/Experiments/LocalLore/2026-11-02-windows-job-close-v1'
& $python -I -S -B "$out/run-host-v1.py" new red-v1
& $python -I -S -B "$out/run-host-v1.py" new green-v1
& $python -I -S -B "$out/run-host-v1.py" regression regression-v1
& $python -I -S -B "$out/run-host-v1.py" profile profile-v1
& $python -I -S -B "$out/run-host-v1.py" reuse reuse-v1
& $python -I -S -B "$out/run-host-v1.py" new capture-red-v1
& $python -I -S -B "$out/run-host-v1.py" new green-v2
& $python -I -S -B "$out/run-host-v1.py" new green-v3
& $python -I -S -B "$out/run-host-v1.py" regression regression-v2
& $python -I -S -B "$out/run-host-v1.py" profile profile-v2
& $python -I -S -B "$out/run-host-v1.py" reuse reuse-v2
& $python -I -S -B "$out/run-host-v1.py" mutation mutation-v1
```

The helper dispatches the installed interpreter with `-I -S -B`, the pinned entry script, fixed mode and phase; for example `run-checks-entry-v1.py new green-v3`. Each phase request records its then-current helper/entry hash. The original host snapshot serves the early 64 MiB-control cohorts; the pre-mutation snapshot serves final 80 MiB cohorts; the final host/entry add only the fixed negative mutation mode. The entry's fixed regression list is `benchmarks.test_runtime_spike`, `benchmarks.test_android_runtime_spike`, `scripts.tests.test_receipt_supervisor_evidence`, `scripts.tests.test_receipt_avd_environment`, `scripts.tests.test_windows_native_tcp_state`, `scripts.tests.test_library_ui_recovery_operator`; profile is the three Knowledge UI authority/controller/activation modules. No activation CLI, actual ADB or inference dispatch occurs.

| Preserved helper snapshot | Bytes | SHA-256 |
|---|---:|---|
| run-host-original-v1.py | 6627 | `d9ed2845546ff86fd24ec568bf92eb929f2a02d8dc3860a4a97f44c2176da6f4` |
| run-host-pre-mutation-v1.py | 6627 | `4ee78b7bc662a292b5f8084c4aed8e27e3417df8ab15b654fe61031a8c8c0124` |
| run-host-v1.py | 6638 | `588e53afb2dc3057c597b103ac2a45a558cdfc22322ba90c05fc3fa7664afc10` |
| run-checks-entry-original-v1.py | 2284 | `550e2c5ba449fe82b219e3fcd12e8eb126c327ebf4486b2e4593312e9ad35a34` |
| run-checks-entry-v1.py | 3560 | `a070459d489c1408278b7a3c4172cecae81695fad804c8de6fcff11031675827` |

Each supervised phase has a 900-second worker limit. Source/archive creation and metering occur outside that timer. Ordinary source/status/archive reads and installed tool locations are not lifecycle authority.

## Preservation and storage limits

Primary evidence root is `D:/Dev/Experiments/LocalLore/2026-11-02-windows-job-close-v1`; recovery root is `D:/Dev/Recovery/LocalLore/2026-11-02-windows-job-close-v1`. The sealed receipt has **15,781 selected pairs / 139,191,579 copied bytes**. `preservation-v1.json.gz` is **367,069 bytes**, SHA-256 `6087b6a14c5b02436b6bf94d53600aa3ecfafe51131faf3acd5e3585cc4dcfc6`; decoded JSON is **10,498,234 bytes**, SHA-256 `01819d533d9ce9077b1cddf7c5788f7001c05407d2ecce9196ca4ea888efca49`. Recovery has an exact compressed receipt copy. At this snapshot, controls were **76,482,242 bytes** and selected recovery including receipt **139,558,648 bytes**, before later review/report additions.

Controls were refined from 64 to **80 MiB**, selected recovery from 96 through 128 to **160 MiB**, before additional retained work; the selected new-fixture budget remained **128 MiB**. Earlier caps are preserved in their own phase requests. These are selected meters, not aggregate disk/cache/TEMP quotas.

The continuous generated meter missed the third B83 operator-fixture tree. A post-run inventory conservatively preserved that **whole tree: 9,609 files / 9,264,342 bytes, including old and new records**. It also copied **38 D: temporary candidates / 360 files / 257,894 bytes** based on prefix/time selection. That is preservation, not proof that B90 owns each candidate. Together with 53,554,170 bytes in newly selected fixed-profile fixtures, the conservative final extra was **63,076,406 bytes**. This is a final observation only: **no whole-packet high-water claim or reconstructed continuous third-tree bound**; these candidates and historical evidence were retained. The 13,033 inherited fixture pins were separately reverified. No model or emulator image was copied by B90.

| Full source archive | Bytes | SHA-256 |
|---|---:|---|
| source-0ccb36662d51c90eb61131e42eeb7f8980425373.zip | 11932868 | `fdb14a3241090ad77fbfea88ba28f89c032e2238f980d7e22ac6c947f70177e3` |
| source-7d465389000bb543212058dfa9fe2cd8d6ddd40f.zip | 11933650 | `9df820bcffca947215bd6ed2b6f85fdf4fa8dd5f67f84bc0ce3a536d063e84de` |
| source-bfbdb69b621cdcdcee5f9153e75db177d088653d.zip | 11934277 | `2376b3eb6d0526387e8cc5da0148ada32c02e1878e99a5aaff002ba10ad762aa` |
| source-79f678ae932b7bafaed65c50486e2af3a736f7b7.zip | 11934311 | `944d33fe7a03df4a9545ab25e3fb0866e428baf1c8c1c2feccb83a93ac965330` |
| source-552ad2b976eda5afc551c69d516d3f8741e788ef.zip | 11934440 | `a98ee1b3be868b2ccca6023e09bb888a92340c1d6012cd83f7312cec814aa761` |

Independent source review is `proposals-v1/review/source-review-v1.json`, **10,784 bytes**, SHA-256 `ec379f259341970988c12a57974592bca1783f951930575c8ecbb44c3757dd0f`. Original-oracle/closed-execution review is `proposals-v1/b75/oracle-review-v1.json`, **62,183 bytes**, SHA-256 `ae663847d9d1e130d93d79e386acf9bfbae4fa646e046c16ce88aba7460b7c27`; its author wrote the original 24 proposals and is independent of production integration/execution, not of those tests' authorship. Independent full closed/copy audit is `proposals-v1/b72/closed-review-v1.json`, **62,314 bytes**, SHA-256 `aaa4b7f26bb61ea01c801c1145c0e5456e2527d3314a86e97f3857fa2acfc670`, with an exact recovery mirror. It verifies all 15,781 pairs, inherited fixtures, 12 phase joins and five ZIP maps. Reviews reran no tests or native operations. Later reviews/docs are additive evidence outside the initial receipt snapshot.

## Sealed boundary and remaining limits

`pre-sdk15-boundary-v1.json` records **2026-11-02T16:50:04.370247Z**, before separately approved SDK15 PR #354 authority/dispatch. At that instant the shared ledger was 41,230 bytes with SHA-256 `4917ec696f7c9f9de5917838aafbd9c2d11184e17c8cbecd71f4eb66ae6a58c5`; its recorded matches/absences were valid then. **This report makes no current unchanged-ledger or authority-absence claim after the approved B91 operation.** B91's new human grant, actions and results are separate from B90. No later actual SDK15 result is credited here, and B90 creates no SDK16 boot claim or substitute authority.

There is no B90 emulator/phone/model/Android/JNI execution, ARM64 runtime verification, fresh Android/native compilation or CI result; CI was not run. Host success does not prove all native/OS resources vanished or qualify M01/M09 device/model acceptance. No settings change, other-emulator stop, guest retirement, release or merge is part of this packet. M10.02 remains broader than these completed host checks; source-bound profile/admission work and any future SDK16 target run require their own current reviewed inputs and authorization.

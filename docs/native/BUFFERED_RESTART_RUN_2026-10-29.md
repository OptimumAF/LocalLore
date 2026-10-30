# Single approved buffered restart run

Refs #14 (M10.02) and #13 (supporting M09.06). This bounded emulator case
passes; full milestone criteria remain separate. It exercises the frozen source and artifacts from
[PR #270's build](BUFFERED_RESTART_ADMISSION_2026-10-29.md), under one newly
received human approval for the exact buffered guest. Earlier spent/refused
restart captures retain their original outcomes.

## Executed inputs

Actual execution uses the clean physical D: worktree
`D:/Worktrees/LocalLore-m10-buffered-build-v1` at
`778f6f78d94b323b3b12f73c6def3e92bb1254a0`: 2,232 tracked raw sources and
985 compiled-prefix inputs. Subsequent report commits and current main are
not substituted into those bindings. The existing build has 588 JVM cases
in 58 reports; these are prior build results, not new JVM execution here.

| Input | SHA-256 |
|---|---|
| Build-only manifest | `2085719820bde13805ad811683e439249af5118128a1bee38fe4821b32fa60ab` |
| Product APK, 78,423,520 bytes | `c8adf07e9ae6802f98108ea8f9d0f061200119203273c95dd6f7e98069bfcd09` |
| Test APK, 2,272,447 bytes | `215731ef23e46f1dd1d97f9fb846672eaa954467332069f8723520f3101a0221` |
| Read-only native process probe, 13,848 bytes | `8c9408c4af7ce73d4e39dde712c291dd1d5e042e53ff407414dfa4d864d41972` |
| Existing local model, 2,588,147,712 bytes | `181938105e0eefd105961417e8da75903eacda102c4fce9ce90f50b97139a63c` |

The prior helper build's started-receipt request-binding limitation remains
documented in the build report. Its artifact provenance is not retrospectively
upgraded. The separate current phone-build APKs are not used for this run.
No dependency, runtime, model, SDK, ownership rule or test assertion changes.

## Admission and procedure

The human approved one API 35/x86_64 guest at
`D:/Dev/Experiments/LocalLore/2026-10-29-buffered-restart-v1/avd-v1`,
8 GiB RAM/four cores, up to a 40 GiB storage reservation and 30 minutes.
Scope includes the verified APKs/helper, local model copy, one import/AUTHOR
attempt and passive restart verification. It does not authorize another boot,
retirement, shared-service changes, other-emulator stops, settings changes,
model upload or merge.

Preparation uses the current public `receipt_avd_environment` API and fixed
[shared storage ledger](../runtime/android/RECEIPT_AVD_STORAGE.md), not an
older copied guest helper or alternative registry. The named dirty storage
checkout is preserved; the reviewed frozen execution source contains the
guard and monotonic closed-charge fix. Two unretired roots/64 GiB total and
40 GiB for a preparing/live guest remain enforced.

The new preparation proposal is `3a35f908bc54da740e847593b4f37b9d984b58ec4d202b53efc00a013ba4cb2d`;
the separate run proposal is `a80752b03f8344ce5f288c21a3ee0a981510fd45c6b792194fe75d66f6189573`.
The new SDK5 target admission is
`603a1097290afb805f35139639d264e876d5a8cef5d3e1e7829db58e2aa286be`.
Fresh human and exact phase-authorizations are retained privately on D:.
No old grant, running identity, client receipt or result is adopted.

All commands start in the frozen execution worktree with process-local
`TEMP`, `TMP` and `TMPDIR` set to `D:/Dev/_Temp`. Installed tools and existing
credentials stay in place. Host metadata confirms Python 3.14.7 and Windows
10.0 build 26300; the admitted platform-tools version is 37.0.1-15733141.
The guest is API 35/x86_64. The public owner is invoked by its script file
under isolated Python:

```text
python -I -S -B D:/Dev/Experiments/LocalLore/2026-10-29-buffered-restart-run-v1/prepare-current-guest-v3.py plan
python -I -S -B D:/Dev/Experiments/LocalLore/2026-10-29-buffered-restart-run-v1/prepare-current-guest-v3.py prepare
python -I -S -B D:/Dev/Experiments/LocalLore/2026-10-29-buffered-restart-run-v1/make-current-admission-v1.py
python -I -S -B benchmarks/owned_restart_owner.py --admission D:/Dev/Experiments/LocalLore/2026-10-29-buffered-restart-run-v1/target-admission-v1.json --admission-sha256 603a1097290afb805f35139639d264e876d5a8cef5d3e1e7829db58e2aa286be
python -I -S -B D:/Dev/Experiments/LocalLore/2026-10-29-buffered-restart-run-v1/run-current-restart-v2.py run
python -I -S -B D:/Dev/Experiments/LocalLore/2026-10-29-buffered-restart-run-v1/run-current-restart-v2.py stop
```

Public `record_closed` and `plan_run(max_seconds=1800)` join the known
preparation result to a distinct run proposal before target admission.
The SDK5 owner restores the full 40 GiB reservation before its boot claim.
It rechecks actual resources, installed tools, exclusive ports and raw socket
ownership before service/guest activation. Private ADB uses port 15937;
guest ports are 5592/5593. USB discovery, automatic emulator scanning and mDNS
are disabled for this private service. No shared-port client is dispatched.

The fixed owner is 1,700 seconds, its public outer supervisor 1,730; the
controller parent is 1,300 and fixed SDK capture 1,200. Existing 1,400/1,350
seconds-remaining preflights remain. There is no deadline extension or hidden
retry. The launcher retains the actual controller worker's process identity
and request-bound started receipt, and passes that identity to the fixed
closed verifier. Only known terminal capture/cleanup and closed handles permit
the admitted stop request; the public owner controls guest/private-service
shutdown and storage closure.

Independent source review found a failure-recording defect in the unrun
launcher v1: `EnvironmentRefused` could escape three recovery clauses.
Launcher v2 adds that exception only to those clauses, preserving refusal and
all guards. Both drafts remain preserved. A review script's wrong expected
exception-tuple order is separately retained as a review preparation failure,
not a product/runtime test. The earlier isolated `-m` command proposal was
corrected to the public file entry point before execution.

## Actual verification

| Procedure | Result |
|---|---|
| Owned preparation plan | Exit 0; 63,893 ms, worker 0, known cleanup/capture, empty streams, source/input pins stable |
| Guarded preparation | Exit 0; 103,524 ms, worker 0, known cleanup/capture, prepared guest and verified preparation closure |
| Fresh admission builder | Actual exit 0; current source/build/helper/model/tool checks pass; no activation in this step |
| Source recovery | 2,232 original/copy pairs, 30,111,041 bytes, verified unchanged |
| Binary transfer probe | All 65 bytes sent and device hash matches |
| Existing local model transfer | All 2,588,147,712 bytes sent; device hash matches; captured call 44,345 ms against 240,000 ms effective limit |
| Model import | Instrumented proof completed, 21,796 ms; source opened/closed exactly once, full byte count, off main thread |
| Real local AUTHOR case | Completed, 38,649 ms; accepted creation, idempotent retry and inference-free ordinary reopen proofs |
| Prior-process absence/passive restart | Fixed prerequisite and same-boot later-process restart proofs completed; prior PID already absent before host stop, so causal live-process death is unproved. Restart case proof 226 ms, no pending operation before/after, workspace/archive handles closed |
| Fixed core controller | Completed; 66 calls, 811,132 ms; current-client verification and observer handle closure pass |
| Supervised controller parent | Exit 0; worker 0, 821,433 ms, known capture/cleanup, empty streams; actual-caller result verification passes, all source/launcher pins stable |
| Admitted stop | Exit 0; published stop, observer handles closed |
| Public target owner | Exit 0, qualified target, `stop_requested`; worker 981,985 ms, outer supervisor 982,470 ms, all 15 cleanup fields true |
| Independent fixed-protocol replay v2 | Actual exit 0, 32,323 ms; both unchanged readers, actual expected workers, 66 qualified calls, source/closure/ledger joins pass; causal-death gate explicitly false |
| Closed recovery producer | Actual exit 0; 2,836 original/copy/ZIP triples verified, 46,462,619 bytes |
| Independent recovery readback | Actual exit 0, 10,443 ms; all triples and exact source/packet/guest/ZIP rosters match; original failed audit and both false causality flags retained |

The three actual instrumented methods are
`OriginalAuthorModelInstrumentedTest#importsTheVerifiedOriginalAuthorModelOnce`,
`OriginalAuthorModelInstrumentedTest#recordsOneRealAuthorCreationAndInferenceFreeReopen`,
and `OriginalAuthorRestartInstrumentedTest#recordsOriginalAuthorAfterExternalRestartWithoutInference`.
The fixed controller verifies their complete instrumentation evidence, model
and native provenance, UID/package continuity, accepted canonical seed and
receipts, same-boot old-process absence, passive recovery and duplicate creation
conservation. Restart uses the test provider boundary that rejects inference;
it is not another real-model request. The recorded profile uses runtime
revision `bda624851d74be34d4e1f7fac1fc4155939539c7` and prompt
`initial-world-v1.1`.

The native prior-PID probes report **absent (errno 3) both before and after**
the host `am force-stop`. The existing fixed verifier permits that case. It
does not establish that the process was alive immediately before injection,
or that this command caused its death. That stronger M10.02 fault-injection
gate remains unverified. Independent audit v1 genuinely exits 1 after both
unchanged fixed readers return, on its additional first-probe-alive assertion;
the failed source, result and trace remain preserved. Its distinct v2 report
records this limitation without counting the stronger criterion as passed.
Neither frozen validators nor target evidence are changed or rerun to repair
that observation. The earlier progress shorthand about external death is
explicitly corrected on both tickets before this report is published.

The accepted AUTHOR trace contains exactly one creation with role `AUTHOR`
and one inference callback request. The independent fixed-protocol receipt is
`ced889cab1bd68d172fadc629fb7f37ac4553faacd409c8c5d4326155836b4df`.
Its source is `82da83679d9e27c50e5d1f25179eaae1ee5fbe3be21bce138dcc2706b4c1e13c`.
The original failed stronger audit's failure receipt is
`76f3d46de2a2312f513396f265926c220b8d9f36a1293dd8c85973b3a9a61a88`;
that audit remains failed, not converted to a pass.

These intervals describe their named transfer/controller/instrumented cases.
They are not isolated model-generation latency, physical-phone performance,
first-token latency or a sustained/thermal benchmark. No additional generation
is sampled to improve a result.

| Closed record | SHA-256 |
|---|---|
| Controller result | `d541c00fe48994e01a44bbe7c411c9c60f7db5713b422066e36348be34767a8f` |
| Parent launch verification | `1c9fda272085c211c4926fc022a5bf3f5dacd88da6668a94f7720a6d4c349ca9` |
| Public target result | `97e030565b1e3131680e4ceaca5014a819464466c0f856353b466e3e994cf180` |
| Worker closure result | `b00a462c4bb2f0cd53e8a31d44838dd68f151d47f580672eb8a04106d0f1c301` |
| Guest storage closure | `1395c7a67cb5e09c38fdb99d5f92b6ef19c8b356b7e7aaac967d27d10360fe02` |

Planning observed 25,818,087,424 bytes available RAM and 18,033,147,904 bytes
available commit; the unchanged commit requirement is 10,737,418,240 bytes.
The host RAM floor remains 12 GiB. These observations do not reserve memory
or establish exclusive resource use. Actual owner admission rechecks them.

## Retention and limits

Private control/raw/failed captures remain at
`D:/Dev/Experiments/LocalLore/2026-10-29-buffered-restart-run-v1`, with
matching `D:/Dev/Recovery/LocalLore/2026-10-29-buffered-restart-run-v1`.
Small capture/source/recovery outputs have an expected budget below 0.25 GiB
and maximum 0.5 GiB, separate from the approved guest reservation. Guest
images, RAM mapping, model and app state remain in place; no whole-guest
archive, cleanup or retirement is performed. The older closed guest remains
preserved and charged. The public owner records the new root closed at
25,036,420,554 bytes, alongside the older closed 25,018,332,463-byte root.
This is verified process/evidence closure, not a graceful guest-disk-flush
guarantee. The image and credential files remain in place; recovery copies
only explicitly selected guest receipts/configuration and the closed host
packet. Guest images/model weights, key files and the guest `emulator/userid`
file are excluded from recovery copies.
Initial control and actual preparation recovery copies
were verified before runtime; the source manifest is
`0126411b92bdce80f7096356a6477121e2a51fd8673aac784b1e777add375f30`.

The final recovery roster contains all 2,232 frozen raw sources, all 593
closed host-packet files (including both audit versions and original failures),
and 11 explicitly selected guest receipts/configuration files. Every rostered
original, copy and ZIP member is byte/hash verified. Manifest SHA-256 is
`659884367e066f6beb30dd534cd038a449bf73bee847bd89f13d1e8bb4e4f40a`;
the 12,022,196-byte ZIP is
`66ab4da89241903c395f741cf7bafa8971c3615ce0f3224d6c240cccff3fc2b4`.
The producer observes 109,358,754 bytes conservatively including the original
source, host packet and recovery tree, before its small terminal/readback
receipts; this remains below the 0.25 GiB expectation and 0.5 GiB maximum.
The independent readback receipt is
`e5b39363e70a07003ff82b5f42326b435708e7ec611a4ca6fd48ac6e51e6d021`;
its checker source is
`ce177c35341120976a2e491c6e6a1f569a4e69f7dc00f2ba360829e9d7484348`.
Final Root metadata readback, including those small receipts, observes
16,340,169 host-packet bytes and 62,921,455 recovery bytes; adding the
30,111,041-byte original source gives 109,372,665 bytes conservatively.
These logical-byte inventories are not atomic volume measurements, exclusive
growth attribution or an OS quota.
Excluded guest image, key and `emulator/userid` files have paths/sizes recorded
without reading, hashing or copying their contents. Their originals remain
untouched. Captured process/boot proofs in the host packet stay private in
the local recovery; they are not uploaded with this report.

Physical-phone/ARM64 performance, broad reliability, story quality and full
milestone acceptance remain separate gates. The phone transport/retained
identity work is held independently; no phone call is dispatched by this
guest grant. The other emulator, shared ADB service and system settings stay
outside this packet. This chat performs no merge or release.

Next runnable M10.02 work is a host-tested harness/proof contract that requires
an authenticated live process immediately before fault injection, then a
matching post-death witness. Its eventual runtime verification requires fresh
applicable admission/approval; this grant is spent and both preserved roots
still count toward the storage limit. Safe physical-phone admission and
physical/ARM64 qualification remain independent unfinished work.

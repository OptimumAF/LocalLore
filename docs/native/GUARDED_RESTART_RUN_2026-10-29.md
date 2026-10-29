# Guarded original-author run: accepted AUTHOR, refused restart collection

Refs #14 (M10.02), #13 (supporting M09.06), follow-up to #266 and historical
#181. **The complete controller case failed.** Import and the original AUTHOR
proofs verify, but restart artifact collection is unqualified. Neither a raw
successful command nor a passing instrumented method overrides that refusal.
Full milestone criteria remain unchecked.

## Exact source and approved scope

The executable is frozen at `4c53db369f40d06eae1380de20b90a4c132998a0` in
`D:/Worktrees/LocalLore-m10-guarded-build-v1`. All 2,218 raw tracked files and
976 compiled-prefix entries match the actual build and remain unchanged.
Later documentation commits are separate. The old `f1b81363` worktree and both
original dirty guard-source worktrees remain preserved.

The owner explicitly approved one fresh API35/x86_64 guest at
`D:/Dev/Experiments/LocalLore/2026-10-29-restart-after-metadata-v1/avd-v1`,
8 GiB RAM/four cores, after inspection found the earlier named root already
existed. Scope included the isolated APKs/read-only helper, existing local model
copy, one import/AUTHOR attempt and passive external app restart verification.
No old grant, consumed root, run ID, proof or running identity was reused.
The current guest and claims are now spent; do not rerun them.

Only current guarded preparation and the SDK5 owner ran. Production storage
uses the fixed `D:/Dev/_Migration/LocalLore-AVD-Storage` ledger: two unretired
roots/64 GiB, 40 GiB per preparing/live guest. The protocol retains its original
1,700-second target owner, 1,300-second controller parent and 1,200-second SDK
session within the approved 1,800-second guest ceiling. No time limit was
extended or restarted. No other emulator stop, shared ADB lifecycle action,
system-setting change, dependency change, merge or release was performed.

## Build and capacity checks

The reviewed [guard integration](RECEIPT_STORAGE_INTEGRATION_2026-10-29.md)
passes 2,229 current Python tests. Independent supplied 51 and existing 251
regressions pass at the original supplied candidate; the full current suite
includes the repeated-closure fix and original regression.

New offline Android build: owner263,367ms/exit0, known capture/cleanup, empty
parent streams, 588 JVM tests/58 XML reports/zero failures-errors-skips. Actual
same-job fresh lint32.4.1 has 10 warnings and no Error/Fatal; no separate lint
phase was invented. Existing SDK36/build-tools35/NDK29/Rust1.93.1/Java21/Gradle8.11.1
and LiteRT-LM0.18.1 pins are unchanged. APK signature/package/manifest/JNI audits
pass. Native helper compiled in 2,184ms/exit0 with exact current source/tool
bindings; it was subsequently used only by the approved guest workflow.

Independent closed build/lint/native v2 replay verifies exact98 SDK/10 native
artifacts, 588 unique JVM cases, three defined instrumentation methods and actual
lint analysis inputs. V1 had an inherited cross-worktree inequality: the new
source and builder correctly both reside in frozen W. That failed verifier is
retained; v2 requires both exact W paths without changing or rebuilding artifacts.

| Artifact | Bytes | SHA256 |
| --- | ---: | --- |
| Product APK |78,423,520|c8adf07e9ae6802f98108ea8f9d0f061200119203273c95dd6f7e98069bfcd09|
| Test APK |2,272,447|215731ef23e46f1dd1d97f9fb846672eaa954467332069f8723520f3101a0221|
| Process helper |13,848|8c9408c4af7ce73d4e39dde712c291dd1d5e042e53ff407414dfa4d864d41972|
| Local Gemma4 E2B model |2,588,147,712|181938105e0eefd105961417e8da75903eacda102c4fce9ce90f50b97139a63c|

The new APK build reproduces prior APK bytes; current source/build authority is
the actual new 4c53 build, not the earlier checkpoint. Initial available RAM
34,203,029,504B passes the 12 GiB floor. Available commit31,828,185,088B passes
the unchanged 10 GiB requirement for this 8 GiB guest. No memory/system tuning
or unrelated-emulator stop was needed. Capacity observations are not quotas.

## Actual guest results

Preparation reserves40 GiB before root creation/SDK execution and completes;
the SDK client takes3,160ms/exit0 with known cleanup. Before boot, the owner
restores retained40 GiB bound to the distinct run proposal. Its private port
preflight precedes private ADB launch. Guest, target owner, controller and parent
captures use separate fresh namespaces.

| Check | Actual result |
| --- | --- |
| APK/helper staging |Both APKs install; actual paths/hashes/UID checks pass.|
| Binary canary |All65 bytes arrive with matching checksum. This is the current binary route, distinct from the historical768-byte CRT reproduction in #181.|
| Model transfer |All2,588,147,712 input bytes complete, client29 qualified;79,743ms client interval. Full guest checksum matches; client30 qualified,13,089ms. These are transport intervals, not inference benchmarks.|
| Import |Client31 instrumentation and strict collected import proof pass.|
| Real AUTHOR |Client43 instrumentation, current initial-world-v1.1 AUTHOR proof and diagnostics pass, including accepted creation/idempotent retry/ordinary inference-free reopen. Recorded51,466ms AUTHOR proof interval is not an isolated generation benchmark.|
| External app death/reopen method |Native prerequisite and client61 JUnit validate. This is component evidence, not the complete restart gate.|
| Complete restart collection |**REFUSED**, phase`collect`, reason`resource_uncertain`. Restart-proof directory is empty, all six result artifact slots are null, final boot record is null.|

There are64 client rows. First63 are fully qualified. Last64 (`artifact-tar`)
has raw completed/exit0,16,896 stdout bytes and known closed socket/sender/input,
but takes6,019ms against a1,006ms effective deadline and is unqualified. Its
after-proof file is retained as unbound diagnostic material; it does not repair
the missing row binding or qualify the transfer. No raw reply was promoted.

Controller result:1,224,301ms/refused; parent1,242,757ms/exit1, known capture and
cleanup, empty streams, held process handles closed and sources equal. This is
the preserved failure, not a successful full case or a new deadline budget.

After that known terminal, the reviewed helper publishes only this target's
stop record. Target owner closes guest before private server:1,474,154ms/exit0,
known capture/cleanup and all15 closure flags true. The new source-bound guest
closure binds owner/worker/final records. Shared ledger records `closed`, charging
**25,018,332,463B**; no retirement/deletion occurred. Images, app state and unique
uncollected restart records remain in the closed guest. This is not a full guest
disk backup or a claim of graceful flush.

## Independent readback and next task

The independent58,613ms closed audit verifies the current build/request/caller
joins, exact192 client files/256 proof-query files,63 qualified client graphs,
127 row-bound proofs, three JUnit methods, available import/AUTHOR/diagnostic
proofs and complete owner/closure/ledger graph. It preserves
`controller_qualified=false`. Audit PASS means evidence consistency and correct
refusal, not restart acceptance. Only the current Python runtime's own DLL
locator is invoked; no SDK/device/model rerun or verdict substitution occurs.

Passive source/timing analysis finds substantial host verification overhead:
first30 clients alone have123,724ms separate before-proofs; after-proofs total
123,868ms within client timings. Those overlapping numbers cannot be summed
into exclusive CPU/I/O/inference time. Full guards repeatedly hash tools/source,
**not model weights**. Source call graphs include32 full guards per ordinary
controller shell operation. The earliest unrecorded cost is not established.
Next runnable M10.02 work is host phase instrumentation and a rigorously tested
immutable-input lease design; preserve every trust position/deadline and prove
mutation refusal before considering any cache. No new guest retry is authorized.

Phone availability is unassessed here. Physical/ARM64, sustained performance,
semantic story quality, broader cancellation/accessibility and the complete
restart gate remain unqualified. Gameplay authority/local-only architecture is
unchanged.

## Evidence and retention

Private packet:
`D:/Dev/Experiments/LocalLore/2026-10-29-guarded-restart-run-v1`.
Budget stated before execution:14 GiB new build/shared-cache growth, separate
40 GiB guest reservation and0.3 GiB source/small-capture recovery. Observed build
growth872,503,603B (0.81258GiB); all outputs retained. Tiny control recovery
already verifies22 files/426,465B. Final source/capture recovery goes under
`D:/Dev/Recovery/LocalLore/2026-10-29-guarded-restart-run-v1`; exact final receipts
are recorded in the linked ticket handoff. Guest disks/model weights are excluded
from that metadata/source backup and remain at their original D: locations.

| Private receipt | SHA256 |
| --- | --- |
| Joined build admission |d5fbff99552f86bd4ef6ae418c0e97421b5819be99d3f8ee22b5437fbc4848c8|
| Controller refusal |96bef623bc940ef793ac453361ac5ccb0cadd8152f9e00be6dc7e496a9566efd|
| Parent terminal |a1fdcddce674dd21f8bddb2f2493efee3f704963c6d0b2f28aa225ced1418cef|
| Target closure result |bf68fd990ae15cd85637a8a87cdc2b0bd149fdadc0c83a3904dbe2085736ad0a|
| Guest storage closure |e8a686e4977bf87af4a1a3484fa7a5dbecfe6e61435c19127c9446c0eedc6306|
| Independent runtime readback |0d05af9b1c4b6fce49b8c071f9146fd7683c8431d7393b6bb58cd437a1158cac|
| Passive overhead analysis |616d02aad401c06aa939775a5455fcb897b2fd899c9a3bb432741696648cc6a5|

Actual command entries, from physical frozen W with D: TEMP/TMP/TMPDIR:

```text
python -I -S -B <packet>/android/build-sdk-v1.py sdk-build-v1
python -I -S -B <packet>/prepare-guest-v1.py
python -I -S -B <packet>/admit-target-v1.py
python -I -S -B benchmarks/owned_restart_owner.py --admission <packet>/target-admission-v1.json --admission-sha256 630a525cb22fb41f97c59c59277902f190a35d894d4f1a3324eadd2973db3887
python -I -S -B <packet>/run-controller-v1.py run
python -I -S -B <packet>/run-controller-v1.py stop
```

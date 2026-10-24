# Setup launch-failure and held-session recovery device verification

Refs #9 (M05.05 prerequisite; M05.04 supporting), root claim 6380776295 and
device/report subclaim 6380789950. **Both selected device tests passed** on the
admitted B emulator (API 35, x86_64, 4 KiB pages). The single cohort completed,
its evidence was sealed and independently reviewed, and its local lease closed.
This is scoped prerequisite evidence; full M05.04/M05.05 remain incomplete.
The packet started from `727f8e1`/PR #139 open and unmerged.

## Observed behavior

The first method used the inherited setup UI with a native-published 63-byte
synthetic model. Start encountered the fixed injected failure before admission
and rendered redacted FAILED. Actual Check performed fresh full verification
and restored READY. A second Start claimed the production
`CandidateOwnerAdmission.attach` reservation before the injected constructor
failure. Actual Choose from FAILED then denied picker admission and rendered
SESSION_HELD before any OPEN_DOCUMENT launch. Disabled control touches,
foreground lifecycle changes, and closing/reopening a new Activity and
ViewModel in the same process preserved the held state.

The second separately selected ordinary instrumentation ran in a different
actual `(PID, start time)` identity pair. It reopened and fully rehashed the
unchanged native-published model, checked the cache sentinel and 15 specified
older files, then reached READY with fresh admission and no import or Start.
A reused PID with a changed start time is a different process identity.
Controller counters were respectively seed imports/file imports/full checks/
Start attempts/constructions/IO violations `1/0/2/2/1/0` and `0/0/1/0/0/0`.
The second method also performed a direct prelaunch store reopen and independent
fixed-file hash reads; its counter of one controller check is not a count of
all verification IO.

Both methods reported exactly one PASS and zero FAIL, including teardown:

```text
am instrument -w -r -e class org.locallore.app.ModelSetupRecoveryTest#startFailuresRequireVerificationAndHoldAdmissionAcrossRecreation org.locallore.app.modelpickerverify.test/androidx.test.runner.AndroidJUnitRunner
am instrument -w -r -e class org.locallore.app.ModelSetupRecoveryTest#freshProcessRechecksHeldSessionModelWithoutImport org.locallore.app.modelpickerverify.test/androidx.test.runner.AndroidJUnitRunner
```

These were ordinary, separate runner invocations. There was no host UI,
launcher bootstrap, picker selection or no-restart instrumentation. Forced
bounded receipts and markers qualified only after their selected method's
ordinary PASS; a receipt written before teardown could not replace PASS.
The fresh receipt linked the exact held receipt SHA-256
`fca3b13ab5eceb98145b3ce2f2c2545a6de441d750fbda2bb7f26a3d66d95f57`.

## Admission and verification

Source freeze: `5ebb4245a614b286c9436c4575e479bc574e94bc`. Root-owned final
fixture build passed 276 JVM tests in 28 suites with zero failures, errors or
skips; lint had zero errors and five advisories. The regular host build also
passed 276 tests with zero failures/errors/skips and four lint advisories.
Actual copied APK signature, manifest and package supplement audits passed.

| Artifact | Bytes | SHA-256 |
| --- | ---: | --- |
| APP | 73,846,072 | `d03360e5985a5b027c4f0a476707d5c16b07e495db9812775c44b8a2fa678b00` |
| TEST | 1,821,985 | `a75b68cd99d2838ab00c41a3edec719b6ce23a7cd31681f2c544e21c2ccde1ed` |

The initially disabled controller proposal bound 242 inputs, including 54
shared source copies and 12 private controller copies. Root and the independent
reviewer verified the bindings and closed source interfaces before the
[one-shot GO](https://github.com/OptimumAF/LocalLore/issues/9#issuecomment-6380916958).
Only the two authorization flags were promoted. Proposal SHA-256:
`427fbfb17fe65d8d6a62f7e522a09f010d7187d7d3981176d0384b4ef910b07f`;
authorization SHA-256:
`2894b273dc399d3d2175ce8edadf0289f34b8f37eb409a62f5e5cd80b005973f`.

All 32 host pure cases passed with zero failures/errors/skips. They covered
closed ordinary runner framing, retained actual API-35 RESULT LF/CRLF shape,
proof schema/counters/hash continuity, process/package refusals, two-method
ordering, failure-before-cleanup, wrapper authorization and terminal propagation,
and the actual inherited 180-second budget validator rejecting 210 seconds
without spawning. These are mocked host tests, distinct from the device results.
An initial fixture-helper argument collision and draft runner blank-line
mismatch were corrected before admission. No device failure was retried or
converted to a pass in this packet.

## Terminal evidence and preservation

Original owned handle 81144 reached authoritative terminal: outer exit 0,
child exit 0, known cleanup complete, 37,671 ms. All 81 device clients had known
terminal status. Outer stdout was 370 bytes, SHA-256
`49d3319aaf8e2546e971f2ee900cb151698e0c8745722b25eb50df307af12f22`,
with empty stderr. Root accepted that original terminal before local closure.

The controller updated only the two signed disposable APKs. Final evidence
confirmed all 33 installed UIDs unchanged, the other 31 APK hashes unchanged,
the admitted own-pair hashes installed, real-candidate root absent and no owned
processes remaining. After both PASS results, fresh map/UID/captured-process
guards admitted one exact TEST force-stop. APP force-stop count was zero:
its conditional stop was unnecessary. Ordinary runner lifecycle and that exact
TEST stop do not qualify natural runtime/model resource cleanup.

Final userdata free space was 1,388,756,992 bytes, above the unchanged
1,207,959,552-byte floor. Host C and D free space were 331,150,712,832 and
297,657,651,200 bytes, above their respective floors. These are boundary
observations, not reservations against concurrent OS storage use.

The new fixed `model-setup-recovery-v1` root was initially absent. Its synthetic
model retained SHA-256
`648c91a9de82e613189b3920a2098f5d803eb6e244f39b2b631cce24b7be8de0`.
The 34-byte cache sentinel retained SHA-256
`1d6c28464cd06b0e57120bed608f521b5b87fed1f83172d9929540ad43802890`.
Both proofs preserved the 15 explicitly bounded older picker, interruption and
pending-v2 model/proof/marker files. This is not a byte audit of all userdata.

Private raw identifiers, receipts and client outputs remain local in
`D:/LocalLore-model-setup-recovery-device-20261023`. The final closed selection
contains 268 files / 1,300,057 bytes; index SHA-256
`03c18b3ee832a4aee2f021c9245029e2f72c998aff2da64abbb23a779a28635f`.
Root and the independent reviewer verified the final selection and all 81 raw
clients. The exact local lease was released after root accepted the terminal
and seal. Subsequent central public-document edits are post-cohort changes;
the frozen source copies and selection remain intact.

## Limits and next task

The injected failures establish setup catch-boundary and admission behavior,
not actual OS/SDK failure handling. No SDK initialization, Engine, workspace,
story, inference, real model weights, cache repair, data clear/reset/uninstall,
old-31 lifecycle action, emulator A, reference phone or #117/#119 action occurred.
No real-model/backend or ARM64/16 KiB qualification follows from these synthetic
API-35 emulator results. Runtime/device holds remain in place.

Next runnable task: host volume-aware candidate-owned storage/admission work,
under a separate claim. This packet does not authorize more UI fixtures or
device actions. No merge or release was performed.

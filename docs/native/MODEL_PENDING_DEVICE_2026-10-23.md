# Pending-picker framework callback device verification

Refs #9, scoped M05.05 pending-picker prerequisite and supporting M05.04;
root claim 6379996729, repair refinement 6380284671, device/report subclaim
6380010538. **The synthetic pending-picker prerequisite passed on B.** The
selected observer reported **1 PASS, 0 FAIL** after actual process death,
framework restoration, rejection of a stale picker selection and a fresh
explicit local import. Earlier failed/stopped attempts remain preserved and
are not converted to passes. Full M05.04/M05.05 acceptance remains incomplete.

## Verified outcome and limits

The real DocumentsUI picker survived the source-controlled death of its caller.
Before the death, bounded server records established the exact caller task was
STOPPED/nonfinishing with a non-null saved Bundle; after death the same saved
record/task was DESTROYED and the APP process was absent. The arm emitted its
selected START, waiting/armed markers and exact expected crash framing. This
expected interruption was **never counted as a method PASS**.

The actual restored callback selected the WRONG synthetic document in a new
process with the same caller task/run and saved-state restoration. Its phase
remained CHECKING → CHECKING and its attempt/open/closed/active/failure counters
were all zero. A fresh explicit Choose action was then required. Callback 2 in
the same restored process/task/run selected the VALID synthetic document and
reported PICKING → IMPORTING. Its receipt is an in-flight snapshot, not drain
proof. The external controller first observed the actual READY UI. The passing
observer then required full native size/hash verification, exactly one provider attempt/open/close,
zero active descriptors/failures, no overflow or receipt-writer errors and no
persisted provider grant.

The observer also required the previous picker model/process proof and the
interrupted-import model/proof/sentinel/cache bytes to remain identical. This
is a specific file-preservation check, not a whole-userdata byte audit. The
payload was only the original 63-byte synthetic fixture, SHA-256
`648c91a9de82e613189b3920a2098f5d803eb6e244f39b2b631cce24b7be8de0`.
No model weights, SDK initialization, inference, Engine/workspace/story
creation, original saves or real-model/cache operations were admitted.

Both instrumentation methods used the source-asserted no-restart mode and
`waitForActivitiesToComplete=false`. The final selected command shape was:

```text
am instrument --no-restart -w -r -e waitForActivitiesToComplete false -e class org.locallore.app.ModelPickerPendingTest#observeRestoredPickerAndFreshImport org.locallore.app.modelpickerverify.test/androidx.test.runner.AndroidJUnitRunner
```

The observer has no ActivityScenario/Compose launch rule and does not launch,
recreate or close the Activity. It observes the actual callback/result state;
the host did not inject an activity result. The arm selected
`ModelPickerPendingTest#armPendingPickerAndTerminateOwnProcess` with the same
runner options. Its intentional source-owned self-kill followed forced private
proof publication and the separately admitted fixed handshake.

This evidence is limited to the existing B emulator: API 35, x86_64, 4 KiB.
A, a reference phone, ARM64/16 KiB and real-model/backend qualification remain
unverified by this packet. Nine exact signed legacy chooser-provider processes
could be observed passively with fresh UID proof; none gained lifecycle or file
access authority. Unique identifiers and raw task/window/UI records remain
local.

## Actual execution history

Each row had its own reviewed one-shot admission. Observation timeouts never
started replacement handles. Every listed client reached known host cleanup;
a shell exit 0 is not itself a method PASS.

| Admission | Actual result | Clients | Device actions and retained stop |
| --- | --- | ---: | --- |
| [Original cohort](https://github.com/OptimumAF/LocalLore/issues/9#issuecomment-6380248597) | Outer exit 1; child exit 2; 16,610 ms | 32 | Arm **0 PASS, 1 FAIL** before ready proof. Assertion: only the owned app may be scrolled for its choose control. No handshake, host UI or observer. Arm drained naturally without emergency cancellation. |
| [Read-only settlement](https://github.com/OptimumAF/LocalLore/issues/9#issuecomment-6380333122) | Exit 0; 4,344 ms | 12 | Exact 33 hashes/UIDs, APP/provider present, no passive processes; current fixture resumed/focused without saved Bundle. No lifecycle/UI/provider operation. |
| [Scoped stop](https://github.com/OptimumAF/LocalLore/issues/9#issuecomment-6380391390) | Exit 0; 14,297 ms | 30 | Fresh captured-subset gates before one TEST stop and one APP stop; final owned processes absent. Every data root preserved. |
| [Repaired cohort](https://github.com/OptimumAF/LocalLore/issues/9#issuecomment-6380431124) | Outer exit 1; child exit 2; 22,657 ms | 62 | Exact expected arm/death/saved-task proof accepted, **0 PASS, 0 FAIL**. Two UI dumps/one Show roots tap; stopped at the exact TEST root's nonclickable ListView row. No root/document tap or observer. |
| [Saved-task continuation](https://github.com/OptimumAF/LocalLore/issues/9#issuecomment-6380541558) | Outer exit 1; child exit 2; 15,532 ms | 41 | Fresh same-task admission; exact TEST root then WRONG card touched. Stopped at null focus with same-task finishing DocumentsUI record. No accepted callback or observer in this run. No repeated arm/root reset. |
| [After-result continuation](https://github.com/OptimumAF/LocalLore/issues/9#issuecomment-6380614634) | Outer exit 1; child exit 2; 8,828 ms | 30 | Actual callback 1 accepted; fixed-v2 MISSING UI/current process verified, fresh Choose consumed. Stopped at null focus while the same-task nonfinishing picker opened. No valid-document tap or observer. |
| [Valid-only continuation](https://github.com/OptimumAF/LocalLore/issues/9#issuecomment-6380672968) | **Exit 0; 52,657 ms; observer 1 PASS, 0 FAIL** | 87 | Re-established current proofs and stable same-task picker; valid-only selection, callback 2, READY/observer and final gates passed. One TEST stop and one APP stop occurred only after PASS. |

The final authoritative original handle reached tool exit 0; its child completed
exit 0 with known cleanup, stdout 299 bytes (SHA-256
`473cb7ff613316cd380f048079170146a27ba35e6f73f3652b2ac904c2e127d3`)
and zero stderr bytes. Root accepted that original terminal before local
success closure. All 87 raw clients completed exit 0 with known cleanup. Four
new UI dumps plus five already consumed dumps total **9 of the admitted 16**.
Consumed actions in each picker were not replayed; the fresh picker selected
its own TEST root before the VALID document. Serial UI clients drained before
the observer acquired instrumentation.

Final observations matched **all 33 APK hashes and installed UIDs**, with the
other 31 package hashes unchanged, zero owned/passive processes and
**1,388,744,704 bytes** available userdata above the unchanged
**1,207,959,552-byte floor**. Both host floors passed. The exact real-candidate
root remained absent. Storage figures are boundary observations, not reserved
capacity. The post-PASS stops qualify explicit disposable-host cleanup, not
natural runtime/model cleanup. No APP clear/reset/uninstall or old-31 lifecycle
action occurred.

## Repairs, source admission and adverse checks

The original source was `b822796fa5cc2d2a1a0b820a0c11525ecb7ef59e`. The repaired
source freeze was `f7c2c128a90af4831bfd09a782d22747c3d6fa6b`; host build/audit
ownership belongs to the coordinator. The repaired APP/TEST hashes are
`fca450386454226c130ddd01c15ef11f64914263fbb4970b2821f67427b9cba9`
and `bb548af5a57b09962269458d22ef8df1f0dc4a4fa349fc612c4dd4b85d183d0d`.
The repaired synthetic identity/private root is pending-v2; pending-v1 and all
prior fixture data remain preserved. No production policy or engine fallback
was added by this device/report worker.

Independent official-source review corrected the initial task query: Android
`dumpsys activity -p APP activities` enables client dumping. The read-only
settlement retained that unexpected local Activity detail and disclosed it.
The repaired arm used bounded plain server `dumpsys activity activities`, exact
component/task extraction and no client-dump flags. Its strict parser accepted
only the actually observed horizontal Hist spacing and exact optional
`(organized)` display suffix; client detail, duplicate records, wrong task,
missing/zero saved Bundle, STOPPING and finishing records refused admission.
Synthetic parser fixtures do not count as actual saved-state evidence.

The root-row repair is confined to the exact enabled TEST title TextView and
reviewed nonclickable ListView item ancestry, using source-backed item-touch
semantics. Generic text/coordinate fallback remains forbidden. Document taps
retain the actual clickable CardView owner and require the exact provider
breadcrumb, title/card/grid ancestry, closed roots drawer, bounded coordinates
and fresh same-task DocumentsUI focus. A Recents filename alone never grants
provider authority; preview children cannot receive the document tap.

Null/finishing APP/DocsUI transitions only permit bounded passive same-task
metadata waits. Stable target foreground remains mandatory before snapshots or
taps, including drawer transitions. After a recorded document tap, the driver
waits only for its fixed callback receipt before requiring stable APP UI.
Foreign/duplicate/malformed focus and wrong tasks refuse actions. Fresh shell
XML directories are no-clobber, nonsymlink, mode 0700, uniquely named and
retained; no deletion fallback exists. The aggregate/individual deadlines
remain below the inherited 180-second owned wrapper limit.

Durable pure fixture runs passed: original 61, settlement 13, captured stop 22,
repaired cohort 69, saved-task continuation 26, after-result 29 and final
valid-only 31 (zero failures/errors/skips in each final run). They include
actual dispatcher mocks with LF/CRLF replies, actual 180-second budget
validation/210-second rejection without spawning, CLI exit propagation,
wrapper schema/dependency/terminal tests, source entrypoint ordering, exact
observed UI/window profiles and adverse ownership/process/map/receipt cases.
Earlier development failures remain local: copied-test import/discovery and
synthetic transition setup corrections, a wrapper key/helper-name adaptation
caught before dispatch, and a pure-log suffix assertion stopped by mocked
terminal output after an otherwise passing run. No device admission was
consumed by those preparation checks. Unused disabled proposals/source copies
remain preserved rather than overwritten.

The repaired failure-only seal helper initially expected a three-field arm
aggregate while the valid parser supplied seven fields. Its helper/failure
receipt and completed source audit remain retained; a separate local helper
corrected that equality. It changed no device controller, oracle, raw evidence
or gate. Every frozen final proposal was independently reviewed and rehashed
before its separate GO; only its two admission flags changed on promotion.

## Closed local selections and remaining gates

| Selection | Files / bytes | SHA-256 |
| --- | --- | --- |
| Original stop | 210 / 1,481,418 | `10c7b71a3a14711fa7df80ada77ff54f5d1f63c7b79d01b352acd9d98d49566e` |
| Read-only settlement | 48 / 176,185 | `9959982a235a7993bb8e32f7973a23e5e80f19211e1082aefb5de3d0b25d7ee1` |
| Scoped stop | 90 / 210,680 | `e437f5c06b0c7e91cf18624f4b4d0ce983bcc5eadf0dae95d87ab625322f6f29` |
| Repaired stop | 248 / 1,667,702 | `f0572a36ff3cc5827997f522f07bf371d3facbaa732d6ffea2dc8553b0c04d83` |
| Saved-task continuation stop | 207 / 1,542,983 | `899280bfa3f15c77048524db74a3d80d64e8ddc3399d9afa4c6f6f3918208fc2` |
| After-result stop | 129 / 1,020,625 | `c86410cce551d41e6d81e9c3c6260335f0a26dce208d3df8a8374899a9ed8680` |
| Final passing selection | **253 / 1,309,542** | `276e85ff4aafde6705e42e4f796a0744b299f45f551cbe9f1e0180f2c115cb6c` |

The final disabled proposal SHA-256 was
`b6fce49bb04d1d7010159a174e863f370c3ef38c2fe441a30cb0209e02b63119`;
its exact two-flag authorization SHA-256 was
`1439ca1be43c3be2ead3bc98f2becc939bcbcca66db6f0f80dcc4f6cc08aae54`.
Local closure rehashed all 763 bindings, 87 clients and 253 final selection
files with zero mismatches. Exact execution leases were closed; no further
device action follows these receipts. All raw evidence stays in private local
namespaces, hash-linked across the preserved stopped selections.

Completed scope: M05.05 synthetic pending-picker framework callback prerequisite
and its M05.04 supporting boundary evidence. Remaining gates include full
M05.04/M05.05 real-model/backend and reference-phone qualification, plus ARM64/
16 KiB/device-dependent acceptance. Next runnable task: coordinator acceptance
reconciliation and the next separately scoped host/synthetic prerequisite;
phone/model gates require their own evidence and authorization. No merge,
release or broader device work is implied.

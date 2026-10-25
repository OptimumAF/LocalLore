# Candidate-owned removable-volume synthetic device evidence

Refs #9 (M05.05 prerequisite) and #5 (M01.05 support), root claim 6381042648,
fixture/report subclaim 6381051680. **Both separately admitted B-emulator
attempts stopped, each with 0 PASS / 1 FAIL.** The second passed selection and
reached the first native publication, where it failed. Positive publication and
removable-filesystem compatibility remain blocked; host implementation is in
review. Neither full M05.05 nor M01.05 is complete.

This packet started at main `1a9a314` in a separate worktree. No merge, release,
real-model copy or SDK execution was performed. See the
[volume contract](MODEL_VOLUME_CONTRACT.md) and
[storage/privacy ADR](../adr/0010-candidate-volume-storage.md).

## Scope and intended acceptance

Only the new disposable APP `org.locallore.app.modelvolumeverify` and its TEST
package were actionable. The fixture uses actual production
`AndroidModelVolume`, `LocalModelStore` and native no-replace publication, with
63 original synthetic bytes. Expected synthetic SHA-256:
`648c91a9de82e613189b3920a2098f5d803eb6e244f39b2b631cce24b7be8de0`.
It calls no actual candidate store, benchmark, SDK, Engine, workspace or story.

The final fixture confines model/cache/stage writes to the fresh Context-owned
external sibling `model-volume-synthetic-v1`; it must not consume the future
candidate destination `local-model-removable-v1`. Actual Context assertions
require candidate absence initially, after injected refusal and at completion.
An internal bounded proof is written only after all assertions. Its opaque
candidate-path digest stays private and does not establish a host namespace
mapping. No external path was guessed from a UUID or traversed by the host.
Context APIs may create this app's system-managed directories.

Intended acceptance includes mounted/removable/non-primary/non-emulated storage
on a different device from userdata, unchanged capacity policy, injected
admission refusal before root/source access, native publication, full reopen
hash, verified reuse without a new source, wrong-identity refusal, and direct
native no-clobber preservation. The last case deliberately retains its own
two-byte stage. These later acceptance checks did **not** pass in this packet.
A bounded proof could qualify only after an ordinary selected PASS including
teardown; neither attempt produced one.

The exact ordinary selected command in both cohorts was:

```text
am instrument -w -r -e class org.locallore.app.ModelVolumeStorageTest#contextOwnedRemovableVolumePublishesAndRefusesReplacement org.locallore.app.modelvolumeverify.test/androidx.test.runner.AndroidJUnitRunner
```

No host UI, launcher bootstrap, chooser, formatting, mounting/ejecting, data
clear/reset/uninstall or fallback was admitted. Legacy provider exceptions were
exact signed-package/UID passive observations only, never lifecycle authority.

## First admitted attempt: selection refused

Frozen source `53cc98c0af9d1807cbf3899086045ae05121cbd0`; proposal SHA-256
`13b1ea9b3584efbd94ede3f652081c3089938c60d3ae00500ed68e0778f10354`,
796 bound inputs. Only the two authorization flags were promoted after root
and independent review.

Original handle 64779 reached authoritative outer exit 1 / child exit 2,
known client cleanup complete in 14,406 ms; all 25 clients had known terminal
status. Both absent new packages installed once, producing 35 packages while
preserving the old 33 hashes and UIDs in the pre-method snapshot. The selected
method then reported 0 PASS / 1 FAIL with fixed STORAGE in
`AndroidModelVolume.select`, before it returned. No synthetic import, native
publication, proof or post-PASS cleanup ran. APPstop0 / TESTstop0. Context may
have created its own directories; no later filesystem state is inferred.

Failure-only selection: 148 files / 1,373,941 bytes, index SHA-256
`db81c6182740c25e4da0dd1bbcab577b079a661cb26ed3d800b8d94b00926d4f`.
All 796 bindings and 25 raw clients were revalidated. Root and the independent
reviewer accepted this stopped evidence. Its consumed execution admission was
closed; the original namespace remains immutable.

## Corrections before the separately admitted second attempt

Review identified a concrete compatibility defect: Android's trusted internal
Context path may traverse the app-private `/data/user/0` to `/data/data` alias.
Root canonicalized only that trusted internal anchor before strict checks;
external/model checks remained unchanged. The original redacted STORAGE does
not prove which predicate failed. The fixture added finite last-entered-stage,
alias-boolean and failure-enum evidence without original cause/path. Successful
selection must reach STABILITY; an entered stage is not a precise predicate.

Review also caught deterministic post-copy space failure in the initial
preflight. The corrected import requirement is missing bytes plus the larger
of the 2 GiB runtime floor and 256 MiB reserve, with checked arithmetic. Runtime
admission still requires 2 GiB. The real built-in artifact would require
4,735,631,360 free bytes before import; no such real import was attempted.
The fixture records Context-derived external/userdata free bytes around
admission on success, but neither attempt returned those numeric proofs.
The controller's userdata floor stayed 1,207,959,552 bytes, with unchanged host
floors. Capacity observations are not reservations against concurrent OS use.

Final compiled source was `f3cb9a1fdc8894cb89b0ba57f651cc219c17e7b7`.
Root-owned regular setup and removable candidate builds each passed 294 JVM tests in 30 suites
with zero failures/errors/skips, lint zero errors/seven warnings, and known
worker cleanup. Final build durations were 147,453 ms and 144,531 ms.
Actual signature, shared-UID absence and packaged APP backup-exclusion audits
passed. The final host selection contains 594 files / 312,653,936 bytes, index
SHA-256 `7e1e09ebccbd43da2e837cf47c27da9b1c7dea70073d3f721e91f8ef4173faa8`.
Earlier host attempts, the original 645-file host selection and first device
failure were retained rather than rewritten.

The second disabled proposal bound 746 inputs, 57 coherent shared source copies
and 11 private controller copies. Its SHA-256 was
`dfad1532552bed80bcb4070b01b998d8116324485fafa63c601f8859142e47c0`.
All 30 host pure cases passed, including actual dispatcher mocks, ordinary
runner LF/CRLF grammar from retained API-35 output, finite proof schemas,
initial/final captured-subset cleanup, map/UID/volume/PID drift refusals,
failure-before-dependent-work, actual wrapper terminal/binding checks and the
inherited 180-second budget validator rejecting 210 seconds without spawning.
These mocked cases do not qualify an Android filesystem.

## Second admitted attempt: first native import refused

The fresh combined cohort observed the known installed 35-package map, all
UIDs and owned-process absence before updating only the same two signed APKs
with `-r`. No data was cleared. Immediate captured-subset guards bounded any
conditional new-pair stops; all four before/after stop counts were zero.
Old-33 hashes and all 35 UIDs were preserved in the installed snapshot before
the selected method. Process start was not observed for cleanup; PID/UID/name
and package authority do not qualify SDK drain.

Original handle 16232 reached authoritative outer exit 1 / child exit 2,
known client cleanup complete in 31,922 ms; all 59 clients had known terminal
status. The method reported 0 PASS / 1 FAIL. It progressed past selection,
STABILITY, Context assertions and injected admission refusal, then failed
with fixed STORAGE at `NativeModelPublication.publish` during the first real
`LocalModelStore.import`. The public wrapper does not distinguish native result
categories 2/3 or expose errno. The exact native cause is unobserved; unsupported
filesystem behavior, a particular syscall failure or rollback is not established.

No success receipt, published-model reopen, direct no-clobber result or final
post-test map/process/capacity gate followed. The synthetic store may have
root/lock/cache/stage state; current post-test state is unknown. A known CLI
terminal is not a test PASS or natural runtime/model cleanup qualification.

Failure-only selection: 219 files / 1,468,527 bytes, index SHA-256
`97950aa889e180465aca65673279581e76cd9bf131d84df06fa731c1804b9c14`.
All 746 bindings and 59 raw clients were revalidated. Root and the independent
reviewer accepted the exact stopped selection and closed execution admission.
No success helper, retry or follow-on device operation ran under either GO.

| Admitted artifact | Bytes | SHA-256 |
| --- | ---: | --- |
| First APP | 74,818,284 | `97277fae141c46ca1057518d0a8916ffe7495bb5216fbc52ee89aae098bde51c` |
| First TEST | 2,658,451 | `7cb157a0213653d00394393361b895e4e91dee15d35951c6f4314d98f121c9f0` |
| Second APP | 74,818,284 | `7cae58f2c27c3d8949c724c27eca12555e4b725a033958524fd3052fdabbeba6` |
| Second TEST | 1,870,807 | `48a5a8fd741ec9c11eab86175f57ada727a14416b13d45544ba4f29640b93823` |

## Disposition and limits

Host implementation is in review; positive native publication on this removable
filesystem is blocked. Both attempts used only B/Android15/API35/x86_64/4KiB.
No physical-phone, ARM64/16KiB execution, real-model size/quality/latency, SDK
initialization, Engine, workspace, story or active teardown result follows.
No weights, benchmark/candidate old roots or old-33 lifecycle operation were
addressed. Old APK hashes/UIDs were checked at specified boundaries, not every
userdata byte or any unobserved post-test state. Runtime A/#117/#119 holds remain.

Private raw outputs, process/volume identifiers, path digest and receipts remain
local in the original and V2 evidence namespaces. No raw private diagnostic was
added to this repository. Existing fixture commits are integrated centrally;
this report alone is the final device-agent documentation handoff.

Next runnable task: a separately reviewed, narrowed JNI-result diagnosis without
weights or old-33 state actions. No new live authority or atomic-publication
fallback follows from this packet. Root prepares the focused draft PR; full
M05.05/M01.05 and release/device qualification remain unchecked.

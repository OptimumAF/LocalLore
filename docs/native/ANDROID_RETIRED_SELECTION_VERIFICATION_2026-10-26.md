# Retired selected-child recovery and draft callbacks — 2026-10-26

**Evidence availability update, 2026-10-26:** the selected private index and
earlier raw evidence directories are no longer present at their recorded paths.
The [preservation handoff](ANDROID_RETAINED_PARENT_VERIFICATION_2026-10-26.md)
records the interruption and recovered files. Results below describe executions
observed before this loss; claims of continued private retention are historical.

The final product preserves same-frame kind/text edits and sends only the latest
valid draft within the current story/branch. The external retired-child case
passes **139 checks across two actual saved-task process deaths**: one typed
leaf retirement, an authoritative fallback with one notice, a cleared invalid
draft, and no automatic gameplay or retired-selection resurrection. Root and
active-child controls pass against the same final artifacts.

This is M10.02/M05.05 lifecycle supporting, M08.05 retirement supporting and
M09.03 draft-state supporting work. It is based on open/unmerged PR #199 at
`12c709891762e3309d1acd4c21afe71874d765e4`; full tasks remain unchecked pending
their wider criteria and owner acceptance. No merge or release is implied.
See the [closed protocol](ANDROID_RETIRED_SELECTION_PROTOCOL.md).

## Product correction and meaningful RED → GREEN

The failed setup exposed a same-scope callback defect. Both chip and text-field
callbacks previously copied the entire input from their rendered snapshot. An
older text callback could restore Action after a Dialogue edit; the reverse
ordering could lose new text. Retained Send could dispatch its old snapshot,
including after the current text was cleared.

Four new tests capture the real production semantics callbacks from one render
and invoke them in one UI-thread block before recomposition. All four failed at
the intended assertions on the unchanged old product (`b5bd5840…715852`): lost
kind, lost text, old Send payload, and Send after clear. Their expected-negative
owner completed in 152,478 ms with 71 clean SDK clients and 520 stable inputs.
The earlier attempt stopped on its twentieth, read-only server-status client
before installation/testing; its timed-out client had known cleanup. A separate
attempt checked that boundary and kept the same budgets. No mutation was replayed.

The production-only fix (`2cfbe7bc`, author `a5e5272e`) changes two UI files,
22 additions/4 deletions. Field callbacks merge only their field into the latest
resolved draft. The full potion preset remains an intentional replacement.
Send reads and validates the latest draft. Pending/scope/key guards remain;
the VM checks story/branch and the gateway validates the live revision. This is
not a new captured-revision equality rule or Kotlin gameplay authority.

The **identical instrumentation APK** produces GREEN: all ten draft-restoration
methods pass, comprising the original six unchanged bodies and the four new
cases. The test source remains `cf657fb49cd585b19e6020f4fc7294ebee2e30c9c065923ed8695c436953742e`.
An explicit one-click-then-observe-Dialogue helper also keeps the external test
from typing before its requested kind is visibly selected. It adds no retry,
extra click, proof-counter increment or timing-cap relaxation; it does not
substitute for the product regression.

## Final verification

The final offline build at `2cfbe7bc` passes: 125 Gradle tasks, 60 executed and
65 up-to-date, owner 133,919 ms / 0, complete capture/cleanup, and 520 unchanged
enumerated inputs. **234 JVM tests in 27 classes actually ran**, with no failure,
error or skip. Twenty-seven original JUnit XMLs and both lint XMLs are retained
with byte/hash bindings. Lint has no errors/fatals: app one existing warning,
controller two warnings. The existing unrelated AtomicReference compiler warning
remains recorded.

All **53 Python audit regressions** pass (28 product/25 controller); their four
audit source files are unchanged through the UI fix. The actual final
11-command artifact gate passes both audits, all manifests/badging/signatures,
runner target and disabled backup. Controller visibility is exactly the fixed
product plus its fixed test package. Both native ABIs package; x86_64 executes.

| Final execution | Actual result | Clean SDK clients | Owner elapsed / exit |
|---|---|---:|---|
| Native loading/refusals | 4 methods | 71 | 149,946 ms / 0 |
| Android regressions | 89 methods / 18 classes | 104 | 335,366 ms / 0 |
| Root control | 82 checks / 2 process deaths | 62 | 146,606 ms / 0 |
| Retired child | 139 checks / 2 process deaths | 104 | 261,718 ms / 0 |
| Active child control | 123 checks / 2 process deaths | 86 | 221,032 ms / 0 |

The Android total is **93 distinct methods in 19 classes**, zero failures/skips,
with exact expected start/pass rosters and final runner frames. All five
execution before/after maps equal the final 520-input build map; external driver
and helper hashes are unchanged. Root/child controller checks are additional
journeys, not extra JUnit methods. Owner times include tooling and are not model
latency measurements.

Exact build task set: `:draft-process-controller:clean :app:testDebugUnitTest
:app:lintDebug :app:assembleDebug :app:assembleDebugAndroidTest
:draft-process-controller:assembleDebug :draft-process-controller:lintDebug`,
with offline mode, no daemon/download, two workers, and both existing input
draft/process verification flags. Python audit command:
`python -m unittest discover -s scripts/tests -p 'test_audit*.py' -v`.
Android classes were selected individually; the four RED methods were selected
explicitly and were not counted as product passes.

## Retired-child outcome and native authority

The real UI creates two roots, sends the parent Dialogue once, reviews/consents
to a fork, resumes its child and enters an unsent child draft. After its stopped
saved-task acknowledgement, the old product PID is killed and confirmed gone.
A test-APK-only `app_process` first qualifies APK-contained Rust loading, then
prepares/closes without commit, then consumes one fresh typed retirement preview
exactly once. No SQL, model, new JNI API, Activity mutation hook or direct saved
navigation edit is used. Each helper must close its owned raw native handles
and be gone before the next action. Both nested exit footers, hashes and closed
18-key proofs are checked; outer shell zero alone never authorizes success.

The probe leaves A0/Bparent1/child1 unchanged. The one retirement leaves A0 and
Bparent1 intact and makes the leaf unavailable, with zero local turns deleted.
Fresh native catalogs resolve the stale child hint to lexical A0. The exact
unavailable-timeline notice appears once; the composer is blank Action and a
bounded both-edge scan finds no accepted message bodies. Explicit native reread
consumes that notice. A second actual process death/restoration keeps settled
A0, without repeated notice, old draft/hint resurrection or automatic gameplay.
The real parent receipt and its root-only selectable catalog remain intact.

The three main process identities share one task and create one factory each.
The first old producer has exactly `1,0,1,1,0,2` and the second entirely zero for
free_text/submit/prepare/commit/cancel/other. Helper retirement is separately
attributed; this report does not call canon globally unchanged across that
intentional commit. Final fixed product records bind nonce, UID, event, PID/start,
task, factory, full gameplay vectors, hints and saved sequence. The original
active-child case still retains its draft and inherited receipt, commits once
on the child and preserves parent1 while reaching child2.

## Failures and host corrections retained

The first four helper tests refused at the shared literal-home guard before
helper/database access. Diagnostic-only tests kept that guard unchanged and
again refused: actual app Java saw the fixed DATA_DATA canonical directory while
run-as saw USER_ZERO. All twelve diagnostic occurrences bind the expected UID
and directory. Its host collector subsequently expected semicolons rather than
actual spaces; separate local readback validated the completed result without
reexecuting tests. The shared fixed-home guard now admits only the two known
user-zero product forms, with canonical parents, exact allowed parent alias,
nonlink product leaf and owner/device/inode checks. Actual loading/refusal tests
and the external helper qualify it on this API/ABI.

Before dispatch, independent review found that a top-level helper exit would
suppress the outer footer. A subshell group fixes that while retaining the real
inner exit and all caller limits. The first actual external attempt then passed
native loading but failed EDIT/DRAFT/check64 before any death or probe/retire.
Its accepted parent/fork setup was permanently quarantined, not retried/adopted.
Read-only XML (10,921 bytes) showed exact child text and both visible controls,
but Action selected. It supports the callback investigation without proving
that an intermediate Dialogue selection happened; the four RED tests separately
establish the defects.

An `adb shell` helper-file readback expanded LF to CRLF and failed byte comparison.
Scoped `adb exec-out` recovered exact original 611/662-byte load records and
their digest; the device's quiet-LF/exit gates were never relaxed. A `/dev/tty`
UI dump returned only a status message and is not layout evidence. A subsequent
new fixed shell-owned XML leaf was read in binary and bound to 44 clean clients.
A later screenshot request was rejected by host budget validation before
dispatch; a separate local collector retained/validated the completed XML.
No screenshot or screenshot-based result is claimed. All old failures, source
snapshots, partial cohorts and earlier baseline APKs remain preserved.

## Artifacts, ownership and limits

| Final artifact | Bytes | SHA-256 |
|---|---:|---|
| Product | 24,555,355 | `ab1030cdbe7cc05833213f0f1064563fcf7893164961f93824927e89a9bc5fc4` |
| Instrumentation | 2,712,171 | `69d4cc80f05a04d7925edbf6044b3282676e79946b3cf90914353ba224565679` |
| Controller | 50,289 | `a262d0d22110c3ade0860eb42d0615b51979580b804626ccfbee9119151927f4` |

No new dependency, Rust/schema/FFI/model/backend change is introduced. The run
uses API 35 Google APIs/x86_64, 4 KiB pages, 320×640/density160, fresh isolated
2 GiB/two-CPU guests; compile/target36 and ordinary minimum26 remain. Existing
tool versions: JDK21, AGP8.10.1, Kotlin2.2.21, Compose BOM2025.05.01/runtime1.8.2,
NDK29.0.14206865 and Rust1.93.1. Official framework mechanism links and closed
guard rules are in the protocol; no compatibility claim comes from source alone.

After all clients finished, exact owned SDK jobs stopped with complete capture
and cleanup: `ui-root` 865,964 ms, `ui-case` 390,911 ms, `active-control` 335,478 ms. Sources, original registry and console-token
observations are unchanged; no guest flush or power-loss proof is claimed.
The unrelated emulator, system settings, phone and model files were untouched.
The two original untracked physical-model build/cache directories remain intact.

Selected **private** evidence index: 3,020 files / 8,142,095 bytes,
SHA-256 `4dbef53f6783a438ad458eb8ac7f7c1b14bb0378da6c20f047f4bb97c383c4e7`. APKs are retained/bound separately. Model
weights, guest images, app databases, compiled caches and other-project data are
excluded. Raw private diagnostics/identities/binaries are not uploaded.

This does not qualify real-model quality/performance, ARM64 execution, another
API, physical-phone admission, retained-parent retirement, all corruption or
power-loss paths, forensic deletion or the complete deletion UI. The native
fallback tests request asynchronous adapter closure and do not prove a joined
drain; the separate helper uses synchronous raw close calls plus process absence.
The unchanged physical-model memory gate remains held in #186, without repeated
favorable sampling. Next runnable supporting case: retire a selected parent
while a child retains shared ancestry, then verify fallback and child isolation.

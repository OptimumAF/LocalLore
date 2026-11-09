# Story Record control scope and delivery - 2026-11-01

Refs #13 (M09.04; supporting M09.03/M09.05/M09.06), #307 and #14 (M10.02).
Supporting implementation is in review; full criteria remain unchecked.

## Problem and resulting behavior

Story Record already provides searchable History, Relationships, Knowledge,
Promises and progression with scoped event sources. Those features were not
missing. Its toolbar callbacks, however, were live ViewModel method references.
A queued Search carrying story A's draft could search a freshly opened B view;
old Next, Close, Back and Retry controls could advance or dismiss a newer view.
Native visibility filtering still held. The defect was unwanted browser
retargeting, not demonstrated canonical mutation or secret disclosure.

Main now captures one plain rendered record value and passes it to every dialog
operation. Ten nonnull-state overloads require the exact current state object,
visible and undisposed, before calling the existing trusted operations. Context
or data equality is insufficient: closing/reopening the same page or returning
from event detail can produce equal-valued, distinct record objects. Existing
direct methods, controller eligibility and native observer/head/branch fences
remain. Browsing adds no gameplay call, NPC sheet grant or name resolution.

Two related boundaries also needed attention. The pinned Compose clickable
node's semantics action reads its mutable current handler. Referentially keyed
buttons/chips/source rows therefore retire old nodes along with their view;
the exact-state guard rejects the old handler retained by a detached node.
Only callback-bearing controls are keyed. Search draft/editor and both list
and event-detail scroll states retain their existing lifetimes.

Separately, a slow collector could miss intermediate states and retain an old
object when the new ready record compared equal. The controller now publishes
an internal identity-based `StoryRecordFrame` for every state update, wrapping
its actual current state. Main observes these frames through the normal
StateFlow lifecycle collector. All nine update sites use the publisher. The
original DTO's values/equality remain; frames are transient UI delivery objects,
not canonical, persisted or serialized story state. Generation/cancellation,
disposal, pagination validation and event eligibility checks remain unchanged.

## Source and actual regression phases

Base is open/unmerged PR #333
`d687f5d560f61a704a91cbaf5c742cb7eac64996`. Four separate physical D: worktrees
had explicit file ownership; Root owns shared interfaces/integration.

Root `feff478c` first extracted behavior-preserving rendered-state overloads;
A wired Main in `fd56dc52` (integrated `2cbf2111`). Original tests `07f08236`
then actually exercised the old delegation. This is an extracted prior-behavior
FIRST, not an unchanged-base or missing-API compilation failure. Root `c9650f0b`
added exact identity guards after the original eight assertion failures.

For delivery, `be868d4f` exposed mapped UI frames without fixing upstream
conflation. Original `0d141efc` tests then measured that defect; `21574995`
publishes identity frames before equality conflation can hide a replacement.
UI tests are `79d50ccd`; narrow control keys are `6ea279b6`/`56547c0f`.
Final executed code is `2b802da1fce21dfe3d61fb7e1b37ef5be4a36741`, which fixes
the composition collector lint error. Later changes are README and this report.

| Actual separately captured selection | Result | Recorded owner duration |
| --- | --- | --- |
| `StoryRecordActionScopeTest`, extracted delegation FIRST | 10 methods; 8 assertion failures, 0 errors/skips; 2 positive controls pass | 31.113s |
| Same ten unchanged methods after identity guard | 10 pass, 0 failures/errors/skips | 32.358s |
| `StoryRecordRenderFrameTest`, mapped-frame FIRST | 3 methods; 2 assertion failures, 0 errors/skips; ordinary-delivery control passes | 29.974s |
| Same three unchanged methods after publication fix | 3 pass, 0 failures/errors/skips | 28.955s |
| First ordinary offline public Android gate at `56547c0f` | 467 JVM methods/57 XML pass; both native ABI outputs/APKs built; overall FAIL at one lint error | 117.136s |
| Corrected same public gate at `2b802da1` | PASS; 467 unique JVM methods/57 XML, 0 failures/errors/skips; lint and both APK audits pass | 44.412s |

The targeted JVM commands use the documented offline unit-test selection,
`:app:testDebugUnitTest --tests <exact class> -x :app:buildRustAndroid`, with
finite owned workers. They do not qualify native/device behavior. Both full
gates actually execute `python -I -S -B scripts/check.py android --offline`,
with no clean, native exclusion, install, connected test or model operation.

First integration executes81/81 tasks and reaches the lint failure after JVM
and APK/native compilation. Its public APK audits are not reached. Corrected
integration executes15 of81 actionable tasks, with66 up-to-date; its JVM task
executes again. The Rust task is up-to-date: both ABI outputs were built in the
retained first integration, and the correction changes only Main's collector.
Current native/output/APK associations are rechecked, not relabeled as another
fresh native build. Corrected public command44.229s is inside the44.412s owner.

The final467 includes all13 new JVM methods; earlier passing cohorts are not
additive. Original source/oracle bytes remain unchanged. Callback tests use the
real ViewModel/controller and explicitly synthetic saved/read transport. They
cover cross-story/branch/head, equal copies/reopen, later pages/search/detail,
loading/fresh controls, diagnostics/cancellation/disposal and late noncooperative
reads, with zero gameplay calls. Flow tests use the production controller with
an immediate producer and independent slow collector. Neither proves native
eligibility, SQLite conservation, Android input delivery or gameplay cancellation.

## Artifacts and independent readback

| Exact final artifact | Bytes | SHA256 |
| --- | ---: | --- |
| Product APK | 28,446,585 | `e14d3a002d1c083feba2a065ec207d3313f0e2248e015c6d03a78b11d2d9e777` |
| Test APK | 2,357,270 | `303f4e65873a5088921e247b85c3b61bddb595953022d448af09fd9c955b13b6` |

Recorded common signer remains
`17ed497138b20dc1657d54039802305cfe0e3b782c73feaad20359c954707564`.
Both exact release/deps Cargo aliases have two links to their same object.
Generated/merged hashes match release; stripped bytes match packaged JNI bytes.
All four packaged native libraries pass the public16KiB alignment audit.
Product/paired manifest, permission and signing audits pass. Final lint has
zero errors, one existing warning and one hint.

Independent closed-file review joins helper/request/actual-child/owner/capture,
raw public audits, native chains and exact current APK originals/copies. Before
the documentation handoff all2,565 tracked raw files match before/after/current
and the corrected tested-source ZIP. The test APK defines three concrete public
JUnit methods with nonempty bodies342/426/538 code units; their class family is
absent from product. **All three Compose journeys remain UNRUN.** They capture
actual semantics actions and cover stories/branches, equal-valued reopen/pages,
and detail/retry/back with draft conservation and fresh-control positives.
They explicitly observe hidden/intermediate frames; the rapid-conflation case
is measured by the separate host flow tests, not inferred from these journeys.

Non-owned source/oracle reviews find no concrete unresolved blocker. Authorship
overlap is disclosed; model review is not owner acceptance. Installed Compose
1.8.2 bytecode and source pins supporting the node-reuse diagnosis are recorded
without a new dependency or runtime claim. Existing Rust1.93.1/Java21/Android
SDK/NDK and D: caches are retained; TEMP/TMP/TMPDIR are process-local D:/Dev/_Temp.

## Retained failures, preservation and remaining gates

The initial full gate's lint error is `StateFlowValueCalledInComposition` at
an unnecessary initial-value read. The fix uses the normal StateFlow collector
overload; no suppression, baseline or weakened assertion. Before rebuilding,
all57 first XML reports, lint/raw/source evidence and four exact failed-build
APK/native copies53,193,694B were preserved. That run remains failed. Old
generated artifacts may be rebuilt; the selected original copies remain.

Private inspection helpers separately encountered a modified-UTF8 class-parser
setup error, a formatter expecting seven groups instead of six, and an LF-only
task-line framing assumption. Corrected readers/formatting retain those outcomes;
they do not count as product counterexamples or justify rerunning passed tests.

Original helpers/raw/XML/maps/oracles and both tested-source ZIPs remain under
`D:/Dev/Experiments/LocalLore/2026-11-01-record-action-scope-v1`; selected recovery
is under matching `D:/Dev/Recovery/LocalLore`. Declared budgets: four source-only
trees192MiB, new generated output3GiB, controls64MiB and selected recovery256MiB.
Combined generated output at corrected closure677,810,471B is within allowance.
The final source is recoverable from the corrected tested-source ZIP plus the
two documentation files and an exact final source map; no third full ZIP or
full generated/global-cache/TEMP backup/high-water claim is made. Recovery
seals and independent final readback are linked from the ticket handoff.

Current Android/JNI/SQLite, real touch/IME/TalkBack/geometry/orientation, actual
process death, physical/ARM64/model/story quality, complete journeys and release
acceptance remain separate. No phone/ADB/emulator discovery or lifecycle,
ledger/preview/retirement, model transfer, settings/shared-service/other-emulator
action or merge. The pending SDK13 proposal binds older #333/#335 inputs and is
unchanged; it cannot authorize these new APKs or prove these UI fixes.

Next independent runnable implementation: preserve typed native promise status
for focused Open/Overdue browsing without inferring status from prose or device
time. The separately pending exact SDK13 decision remains required for its own
frozen operation; no approval is inferred or repeated here.

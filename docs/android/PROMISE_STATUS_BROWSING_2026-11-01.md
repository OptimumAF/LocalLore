# Focused promise status browsing

B66, 2026-11-01. Refs #13 (M09.04; supporting M09.03/M09.05/M09.06)
and #14 (M10.02). Supporting implementation is in review; full task criteria
remain unchecked pending qualification and owner acceptance. Based on open,
unmerged PR #336 at `aab8502ff77ae757e9acb73373c1b8fad9a30265`.

## Behavior and authority

Promises now offers **All**, **Open** and **Overdue**. These are complete native
query results with native totals and pagination, not filters of the displayed
eight rows. Selecting a status starts page one and replaces applied free search.
Submitting the clearly labelled **Search all promises** returns to All. Paging,
retry and return from evidence preserve the preset; changing section or reopening
starts with All. Preset changes reset the edited search draft.

Rust already exposes a typed status on player-eligible Query2 promise rows.
The adapter retains it as `StoryRecordPromiseStatus`, displays its label and
rejects unknown or preset-mismatched statuses. Fixed searches use exactly
`"status":"open"` or `"status":"overdue"` in the existing Query2 `search`
field. Eligibility precedes serialization/search/counting/paging; escaped quotes
inside terms cannot impersonate that token. Ordinary free search still matches
prose, including a fulfilled promise whose terms contain “open”. No new native
schema, dependency, observer grant or gameplay rule is introduced.

Kotlin does not calculate deadline status, read the device clock, infer completion,
locally filter results or recompute totals. The exact story/branch/head/player
binding, cursor digest and original scoped evidence stay authoritative. Evidence
drill never opens a source-branch session. The new action uses the prior rendered
state identity fence and referential clickable-control key; late reads and retained
controls cannot retarget another page, preset, reopened view or story. Browsing
does not generate, commit or cancel a gameplay turn.

## Ownership and source attribution

Existing clean D: worktrees were reused on new branches; previous branches,
generated outputs and frozen sources remain. Root owns the four adapter/type/
controller/ViewModel files, integration and documentation. Agent A owns Dialog,
Main wiring and the two new Compose journeys. Agent C owns twelve new JVM
tests. Agent B owns four native tests and independently reviews nonowned
production/UI code. A reviews the nonowned JVM tests and host runner; C reviews
closed-file artifacts. Authorship overlap is disclosed; these reviews are not
owner acceptance. All writer claims are released at handoff.

- Root: `D:/Worktrees/locallore-record-actions-core-v1`,
  `impl/m09-promise-status-browse-v1`.
- A: `D:/Worktrees/locallore-record-actions-ui-v1`,
  `impl/m09-promise-status-ui-v1`, own commit `f5fd91cf`.
- C: `D:/Worktrees/locallore-record-actions-tests-v1`,
  `test/m09-promise-status-browse-v1`, own commit `78b1e926`.
- B: `D:/Worktrees/locallore-record-actions-flow-v1`,
  `test/m09-promise-status-native-v1`, own commit `96423bf1`.

The app worktree API refused the nested repository sourceRoot; suitable existing
worktrees were reused instead. No new worktree or registration was removed.

## Verification actually executed

Process-local TEMP/TMP/TMPDIR are `D:/Dev/_Temp`. Installed JDK21, Rust1.93.1,
existing Android tooling and existing locked dependencies are reused offline.
No dependency, runtime, model or SDK is introduced or upgraded. Cargo host output
is isolated under this packet's D: output; Gradle/Cargo caches retain their existing
D: locations. Each main phase has a 900-second Windows Job owner, actual child
identity/barrier, source maps, source ZIP, raw streams and terminal cleanup/capture.

| Actual command / source | Result |
| --- | --- |
| `cargo +1.93.1 test --locked --offline --package locallore --features host --test m09_promise_status_search -- --nocapture`, `008cd753` | Four pass, zero failures/ignored/filtered; owner15,868ms, complete cleanup/capture. |
| `python -I -S -B scripts/check.py android --offline`, `62e9a50ab8a3734aa88bfebc220615a5241dfefe` | Exit0, owner53,143ms. **479 unique JVM methods / 58 XML**, zero failures/errors/skips, including twelve new methods. Lint zero errors, one existing warning and one hint. Product and paired APK audits pass. |
| `rustfmt +1.93.1 --check crates/locallore/tests/m09_promise_status_search.rs` | Initially reports formatting differences. Original source is retained in tested ZIPs; a repeat diagnostic is preserved. Root runs rustfmt and the check then passes. Assertions are unchanged. |
| Same native test command, `fa2ef2eb04b4e61626656e0c1993704b7fff520c` | Four pass again, owner2,180ms, complete cleanup/capture. Only the native test formatting differs from the Android-tested source; Android production/UI/JVM source is unchanged. |
| `git diff --check` | Pass before final publication. |

The Android gate executes20 of81 tasks,61 up-to-date. Both release JNI target
checks actually execute and finish in0.17s each using existing unchanged native
compilation outputs. This is not a fresh native compilation or ARM64 execution
claim. JVM tests execute; no native exclusion, clean, install or device task is used.
The native host test uses `CARGO_PROFILE_DEV_DEBUG=0`,
`CARGO_PROFILE_TEST_DEBUG=0` and two build jobs. Final documentation is separate
from the executed source; exact source reconstruction uses the final native-tested
ZIP plus only the three documentation overlays.

The four original native tests prove nine Open and nine Overdue rows page8+1
with exact totals; cursors cannot be retagged to a different preset. They include
fulfilled terms containing both quoted JSON lookalikes, unobserved incoming
terms, a privately completed promise still known as open to its creditor, and
an actual corrected child retaining its parent's original evidence tuple while
excluding parent-future, sibling and private author data. Every query cohort
checks canonical projection and records remain unchanged.

Twelve independent JVM tests exercise the real command/decoder/controller/VM
with synthetic transport: fixed wire fields, invalid preset combinations,
native statuses despite contradictory prose/deadlines, whole-page malformed/
private/mismatched refusal, full unsigned deadlines, inherited source tuples,
8+1 paging, retry/evidence Back, noncooperative late reads, loading, disposal,
equal-copy/later-page/story/close/reopen callback fences and zero gameplay calls.
No meaningful behavioral FIRST run was performed; no compile failure is counted
as a regression reproduction.

Two new `PromiseStatusScreenTest` journeys exercise actual controls/controller/VM
against a synthetic typed reader. They compile and have concrete runtime-JUnit
definitions only in the test APK (337/544 code units). **They remain UNRUN on
Android.** Compilation/DEX inspection does not prove rendered geometry, touch,
keyboard, accessibility, cancellation timing, JNI or native storage behavior.

## Artifacts and preservation

| APK | Bytes | SHA-256 |
| --- | ---: | --- |
| org.locallore.app | 28,329,835 | `05813d21eb261fc694bd48485d5a5cb656206334577e4cdd543f703b558d66ad` |
| org.locallore.app.test | 2,456,353 | `07d29a26ecf49060b7affc18b72d656559533fd947fffc42f88c53de71a3050a` |

Common recorded signer: `17ed497138b20dc1657d54039802305cfe0e3b782c73feaad20359c954707564`.
Four packaged native libraries pass16KiB ELF/ZIP audits; test permissions remain
solely `android.permission.REORDER_TASKS`. The public product audit accepts only
the existing signature-scoped dynamic-receiver permission.

Local captures are under
`D:/Dev/Experiments/LocalLore/2026-11-01-promise-status-browse-v1`;
selected recovery is under the matching `D:/Dev/Recovery/LocalLore` path.
`closed-evidence-v1.json` is108,299bytes, SHA256
`d4207a55f3a0245a5ff5044033c47ff39b88c6dc35f5273c1ac2fd061a4e51c7`.
The independent closed-file readback is4,662bytes, SHA256
`a7e5133f41aa7e79a05a83679b7e4bfc975d22fe6b55fe96c27bd415adad9c5d`.
It verifies all three source/ZIP/owner bindings,2,569 then-current sources,
479methods/58reports, lint, original/copy APKs, captured audits and concrete UI
definitions. Its body takes1,820ms; no build/test/validator/device run is repeated.

New generated output is sampled below the3GiB budget (976,700,829bytes at the
final native phase); controls remain below64MiB and selected recovery below
256MiB. Two-second sampling is not a filesystem quota and excludes global caches/
TEMP peaks. Helperv1 did not include its final measured budget in the pass
assertion; actual final measurements are within bounds. Helperv2 adds that
assertion for the final native phase without changing any test or supervision
deadline. There is no hostile-concurrent-tamper or full-generated-backup claim.
Original external capture trees and failed setup records remain. Ordinary build
scratch is regenerated. Reusing the build directory for this packet replaced the
57 generated XML files from B65's final full gate; those exact XML bytes were
not separately archived and are not claimed recoverable. B65's raw execution
captures, case/hash manifest, dated independent readback, first full-build XML,
targeted FIRST/GREEN evidence and immutable APK copies remain. This is a
preservation gap, not a new test result or a reconstructed capture. The local
`prior-generated-evidence-continuity-v1.json` records all57 changed hashes.
All58 B66 XML reports are now preserved in verified original/copy pairs. Future
reuse must preserve unique generated reports before another build.

The initial collector used an incorrectly transcribed second UI method name.
Its correction revalidates existing partial copies instead of overwriting them;
no source/test changes. The independent reader initially used an overstrict
whitespace-only formatter comparison; it then inspects the actual test-only
wrapping/trailing-comma diff and verifies final bytes. Both setup failures remain
recorded separately from product verification.

## Remaining gates and next task

M09.04 supporting implementation is in review. M09.06/M10.02 current-Android
qualification remains blocked/unrun pending matching execution authority and
fresh guarded admission. The earlier exact SDK13 proposal, source and APKs stay
frozen; its pending decision does not authorize this new pair. The returned
October31 player-presentation approval corresponds to an already executed/closed
run and is not reused.

No emulator/ADB/phone discovery or lifecycle, ledger/preview/retirement, model
copy/import/inference, settings/shared-service/other-emulator action, private data
upload, release or merge occurs. Actual Android, physical-phone/ARM64, real-model
quality/performance, accessibility, causal process-death, full-journey and release
acceptance remain separate. Next runnable host task: bind the current Story Record
callback and promise journeys to a guarded current-build UI test roster before
seeking any matching Android execution approval.

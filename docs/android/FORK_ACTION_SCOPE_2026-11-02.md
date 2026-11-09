# Fork controls belong to the displayed review

Refs #13 (M09.03/M09.06), supporting #14 (M10.02). Supporting implementation is
in review; full task criteria remain unchecked. This stacks on open/unmerged
PR #351 at `7ab4918fa1044d960edcb1172fe7684474eb3a89`.

## Problem and resulting behavior

An old fork dialog's checked **Forget recovery hint** callback could clear a
later request's saved hint. Retained Cancel, Close, Lookup and Retry callbacks
also read the current workflow instead of the review that supplied the action.
Existing native identity/consent checks and synchronous persistence reentry
guards do not authorize a callback retained from another displayed review.
The timeline itself is not deleted by forgetting its recovery hint.

ShellViewModel now checks the exact displayed `BranchForkUiState` object and
visible/non-disposed owner before forwarding every fork action. Actions that
synchronize context check again afterward. Existing exact input/outcome
references and native validation remain. MainActivity captures a plain rendered
fork value in all eight callbacks; the opener captures the rendered ShellState.
Default current-view parameters preserve programmatic calls. Activity stop,
controller/native cancellation, pending-worker reconciliation and commit-wins
handling are unchanged. No second gameplay or persistence authority is added.

The panel has a transient per-mount delivery, replaced on a different state
reference, storage problem or recovery flag. It retires on disposal. Every
action, dismiss, text edit and checkbox edit checks that delivery; both consent
cells reset on replacement. Interactive Material controls are keyed narrowly
by delivery so retained event sources cannot pick up newer callbacks. The dialog
and scroll container remain stable. The opener reuses the existing screen
lifetime and referential storage-control key. No new controller frame layer,
native command, stored schema, dependency or global configuration is introduced.

## Compiler boundary

Review identified another constraint: stable equal arguments can make Compose
skip a function before its referential check runs. The actual intermediate
compiled panel compares its state through `Composer.changed(Object)` and has
an outer `skipToGroupEnd` path. The final panel alone uses the existing runtime's
`@NonSkippableComposable`; a file-only inspection confirms that outer skip path
is absent. Nested composable skipping is not disabled globally.

Current official [strong-skipping guidance](https://developer.android.com/develop/ui/compose/performance/stability/strongskipping)
and [annotation API](https://developer.android.com/reference/kotlin/androidx/compose/runtime/NonSkippableComposable)
were checked. Existing Kotlin 2.2.21 / Compose BOM 2025.05.01 remain pinned;
the existing dependencies compile the annotation without a version change.
The direct controller StateFlow still conflates equal values. The panel also
needs to observe a distinct equal object when a caller explicitly delivers one.
Bytecode inspection is not Android runtime evidence.

## Verification actually executed

Final executable/test source: `62eadfc2cd0ba94f297846046939d6ff326a3b94`.
Later publication edits are documentation only. Commands ran from physical
`D:/Worktrees/LocalLore-record-query2-fixtures-v1`, with installed JDK 21.0.4,
CPython 3.14.7, pinned Rust 1.93.1 and locked offline dependencies.
Process TEMP/TMP/TMPDIR are `D:/Dev/_Temp`; caches and generated outputs are D:.
OUT abbreviates `D:/Dev/Experiments/LocalLore/2026-11-02-fork-action-scope-v1`.

Targeted command:

```text
apps/android/gradlew.bat -p apps/android --offline --no-daemon --max-workers=2 :app:testDebugUnitTest --tests org.locallore.app.BranchForkShellTest
```

Full command:

```text
python -I -S -B scripts/check.py android --offline
```

| Recorded phase | Actual result |
| --- | --- |
| FIRST `3b6f1a45` / `first-v1` | 20 methods: 14 prior positives pass, six new AssertionErrors, zero errors/skips; owned 197.654 s |
| GREEN `d34bb6a4` / `green-v1` | Same entire 20-method source passes, 18.794 s; before final Material-key/compiler fixes |
| Intermediate `22de0c26` / `android-v1` | 557 unique JVM methods / 67 XML, zero failures/errors/skips; full build/lint/APK audits pass, 50.613 s |
| Final `62eadfc2` / `android-v2` | 557 unique JVM methods / 67 XML, zero failures/errors/skips; full build/lint/APK audits pass, 41.875 s |
| File-only bytecode and DEX inspection | Before/after outer skip path joined; five public instance void/no-argument JUnit methods have nonempty bodies in test APK and are absent from product |
| `git diff --check` | Pass |

The original baseline callbacks remain executable through test-only extension
fallbacks; production member overloads take precedence after the fix. FIRST and
GREEN share the byte-identical 33,981-byte test file, SHA256
`f5246a3494b467759957185b53a3278a9d8cf9b19a79a3e4d9afc0ce7d351b7b`.
All 14 preexisting test bodies remain unchanged. Final test changes add the equal-shell
opener case and broaden try/finally around the held-registration setup; no
assertion is weakened. Repeated cohorts are not additive distinct test counts.

The actual VM/controller tests use synthetic gateway and persistence ports.
They cover stale A against replacement B, value-equal copied views, consent,
dispatch/hint conservation, current positive controls and a held registration
whose committed result wins current cancellation without automatic resume.
They do not prove native storage or Android event delivery.

Each build uses a 900-second owned Windows Job, original command/child identity,
start barrier, complete binary capture and known cleanup. All tracked raw source
hashes are identical before/after each phase (2,597 initially; 2,598 finally).
The first cold build compiles both JNI ABIs locally; later native tasks are
up-to-date. Rust, BranchForkController and NativeFork sources are byte-identical to the product base.
No new full Rust workspace test run or ARM64 execution is claimed.

Final Gradle: 81 tasks, 14 executed / 67 up-to-date. Lint has zero errors, one
existing warning and one hint. Both ordinary public APK audits pass:

| Artifact | Bytes | SHA256 |
| --- | ---: | --- |
| `org.locallore.app` product APK | 28,088,160 | `d8ac79cd1172424c12015eb8b3edb723e77c49de86f0b9e1623f9305bb1da4d9` |
| `org.locallore.app.test` APK | 2,452,230 | `066550d1005ed7456ca72917b3959bca88215faaf307f05ebb7b6cfee3e8bc6f` |

The final test APK is byte-identical to the intermediate pair's test APK.
The existing debug certificate is
`17ed497138b20dc1657d54039802305cfe0e3b782c73feaad20359c954707564`.
Existing ordinary-product and test manifest/permission boundaries remain.
Final raw stdout: 7,388 bytes, SHA256
`ccd3420cb03414fe892590acb36e707245e06e19fd8499dd45f879027083e066`.

## Preservation and limits

The released test checkout's six B83 files were copied and verified before
reuse; its old `c87810f7` branch remains. PR #354's operator checkout, proposal,
operational source and product/APKs are separate and stay frozen. Full raw
source ZIPs, FIRST failures, original/intermediate reports, bytecode and compiled
artifacts remain in OUT and selected verified recovery copies under
`D:/Dev/Recovery/LocalLore/2026-11-02-fork-action-scope-v1`.

Actual source ZIP and paired APK/JNI sizes justified documented retention
revisions before more copying: controls 64 MiB, generated builds 3 GiB, selected
recovery 192 MiB. Identical immutable copies are reverified and reused; none is
deleted. These are monitored experiment bounds, not OS quotas. The initial
32 MiB control / 64 MiB recovery estimates were never exceeded before revision.
Two metadata-only helper-preparation errors (reference-count assertion and shell
quoting) are recorded; neither started a build/job/device operation or changed
project source. The failed FIRST remains failed.

Five Compose methods are **compiled/packaged, 0/5 executed**. They retain actual
OnClick/SetText/checkbox sources across equal replacement, distinct requests and
same-state remount, with fresh positive controls. Retained Retry, Resume and
Dialog-dismiss routes use the reviewed common fence but are not directly
executed by these new cases. The synthetic boundary-review and confirmation
callbacks are separate component checks, not a joined native fork journey.

No emulator/ADB lifecycle, phone/model operation, private upload, guest-image
deletion, unrelated-emulator stop, system setting change or merge occurred.
Touch, TalkBack, real dialog/IME behavior, physical/model performance and full
milestone acceptance remain open. PR #354's pending four-method grant cannot
authorize these different APKs or five new methods. Next device action remains
the separately proposed exact recovery operation; any fork-case target run
requires its own applicable scope. A confirmed independent host follow-up is
strict malformed-Unicode rejection before Story Record search dispatch.

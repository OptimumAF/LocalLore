# Fork-consent accessibility host verification — 2026-11-03

Refs #13 M09.05/M09.06 and #14 M10.02 supporting scope. Implementation is in
review. No full acceptance checkbox or Android accessibility pass is claimed.

## Source and change

Open/unmerged prerequisite PR355 is pinned at
`68b231ee6901aed8d52696813a18c3ade4391161`, tree
`9b96d18ecb3b282ebee648563a73c5b7facee24b`, 2,599 raw Git files.
Tested code is `2d29a9eee085300a52681373cc724ddde0370da6`, tree
`cbfddb8e308da00f80844cdf327626d90a9fc0a3`, 2,600 files. Later documentation
is separate from that tested tree. Source is physically D:; normal892/index897
and all preexisting worktrees/ignored data remain preserved.

The old interactive Checkbox exposed state while its explanatory Text was a
separate sibling. Only `BranchForkPanel.kt` changes in production: four imports
and two Row replacements. The entire keyed Row now owns toggle/role and the
same tag; the48dp visual checkbox is passive. Labels, remembered consent,
`act`, busy guards and separate creation/recovery callbacks remain unchanged.
Weighted labels wrap inside full-width minimum48dp Rows. Actual rendered
geometry and announcements remain unmeasured.

## Actual checks

Existing JDK21, Gradle8.11.1, AGP8.10.1, Kotlin2.2.21, Rust1.93.1,
NDK29.0.14206865; no version/dependency change. Offline builds use process-local
TEMP/TMP/TMPDIR and existing Gradle/Cargo caches on D:. Installed tools remain
in their original locations. Process-only in-process Kotlin, two Gradle workers
and four Cargo jobs reduce extra compiler processes; existing Gradle heap2GiB
is unchanged. This does not change system settings or an emulator guard.
[Kotlin documents this compiler strategy](https://kotlinlang.org/docs/compiler-execution-strategy.html).

| Phase | Actual result | Checked owner |
| --- | --- | --- |
| Baseline, old UI + original new tests |28/28 Gradle tasks execute; new five-method Android test class compiles |exit0, known host cleanup,179.044s |
| Final, updated UI + unchanged tests |app Kotlin compile and selected JVM task execute; Android test compile task UP-TO-DATE |exit0, known host cleanup,53.960s |

Worker bodies take167.331s/53.418s. The unchanged checked host ceiling is180s,
combined captured pipe ceiling262,144B, with byte barrier after job assignment.
The baseline has only0.956s owner margin; this one success does not establish
repeatability or a comfortable cold-build budget. Both captures have stderr0;
Gradle stderr is merged into bounded stdout. A pre-build read-only check requires
6GiB commit headroom for this limited host build, distinct from the unchanged
8GiB-guest-plus2GiB emulator requirement. No runtime settings were changed.

**43 JVM methods / 4 fresh XML suites pass, 0 failures/errors/skips:**
BranchForkController15, BranchForkRecoveryLifecycle3, BranchForkReview4,
BranchForkShell21. These regress existing controller/consent/recovery logic;
they do not execute Compose or prove accessibility. No full JVM/CI claim follows.

The five new methods are present in actual baseline bytecode/javap output:
create label, forget label, disabled busy labels,2× font create,2× font forget.
Source remains9,717B/SHA256
`c07eb7523bcc70e3bc4bf75d0789b43b3dbbc86f3c554128eedff8265dbe88a4`.
The final build reuses the byte-identical39,989B test class/SHA256
`f471ee146808f8c87a0f937afa2f5f3141d0b9586b92e057b928aaf01b84eea1`;
this is cached test compilation, not a second fresh compile or executed
assertion. A common byte copy is retained after verifying both recorded hashes.
There is **no semantic RED→GREEN or Android pass**: all five methods are UNRUN.

Both phase source maps close2,600 paths before/after. The only interphase source
delta is the panel; original fork action-scope/component tests remain unchanged.
Baseline builds both JNI ABIs; final reuses unchanged native output. JNI/ARM64
execution, APK packaging/signing/install and real engine/gameplay are not shown.

Host entry commands are
`python -I -S -B <OUT>/run_checks_owned.py baseline-compile-v1` and
`final-checks-v1`; their worker runs Gradle from the physical
`candidate-source-v1/apps/android`. Underlying Gradle arguments include `--offline --no-daemon
--console=plain --max-workers=2 -Pkotlin.compiler.execution.strategy=in-process
:app:compileDebugAndroidTestKotlin`; final adds `:app:testDebugUnitTest --tests
org.locallore.app.BranchFork*`. No connected-device task is invoked.

## Review, preservation and remaining gates

B75 authors the original five Android methods; B72 independently reviews their
intent/quality and actual source/evidence. Production/publication review
excludes a reviewer's own oracle-quality credit. Root integrates all shared
source. Managed worktree creation remains unavailable for the physical repo
outside attached roots; raw Git snapshots and alternate-index publication
preserve the normal checkout, with agents in existing separate worktrees.

Coordinator publication helpers stopped on an overstrict final test-task cache
expectation, then metadata result-variable shadowing and list-order comparison.
Those helper versions/failures are retained. Actual key/byte/hash sets match;
the existing code commit is recovered and checked without rewriting history,
changing a test/assertion, relaxing a boundary or rerunning passed checks.
These are coordinator metadata errors, not product or Android test failures.

Originals/recovery share basename `2026-11-03-fork-consent-accessibility-v1`
under D:/Dev/Experiments/LocalLore and D:/Dev/Recovery/LocalLore, with2GiB
combined ordinary source/build/test/control/recovery retention declared before
execution. Early seven-file proposal/base recovery remains preserved. Final
manifests state actual selected coverage and self-excluded late seals; old
failed/frozen B116/B117/B119 evidence is never deleted to fit.

**Android0/5.** Real merged semantics, label touch,48dp geometry, enlarged-font
rendering, TalkBack, keyboard/screen-reader and unfamiliar-user behavior remain
pending actual approved execution. The font tests' intended reachability
assertions do not prove every glyph unclipped. Existing broader M09.05 contrast,
themes, reduced-motion and other comfort criteria retain their separate gates.

PR392's separately approved run failed/spent during preparation with no tests;
its original refusal cause is unknown. Its later commit-capacity observation
does not authorize another run or apply as this patch's runtime evidence.
No AVD preparation/boot, emulator/ADB/model/phone operation, settings change,
other-emulator stop, data deletion, merge or release occurred for this packet.
No new UI runner, runtime dependency or permission is introduced. Next device
work needs readiness and a reviewed exact proposal with new explicit approval.

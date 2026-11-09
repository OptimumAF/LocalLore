# Follow new replies across a rolling transcript window

Date: 2026-11-01. Scope: M09.03, supporting M09.06/M10.02 in
[#13](https://github.com/OptimumAF/LocalLore/issues/13) and
[#14](https://github.com/OptimumAF/LocalLore/issues/14).

## User-visible problem and change

Native player presentation retains the latest 20 turns as 40 messages with
stable absolute message IDs. The demo also retains at most 40 messages. The
previous follow policy recognized an append only when the list grew with its
entire old prefix intact. At rollover, IDs 1–40 become 3–42 without list growth;
the policy treated that as replacement, clearing unread and scheduling no
navigation even when the reader had been at the previous end.

The policy now also recognizes an equal-sized rolling window with a nonempty,
exact old-suffix/new-prefix overlap. Both ID sequences must be strictly
increasing; every added ID must advance beyond the old tail. Overlapping rows
must match completely, including text and speaker role. Rewrites, reordered or
duplicate IDs, unrelated replacements, truncation and scope changes retain their
previous refusal behavior. Ordinary growing-prefix appends are unchanged.

Automatic navigation still requires a read witness for the **exact previous
snapshot** at its end. A reader of older rows remains in place. New replies stay
unread until the exact current tail is measured as read; scheduling a scroll is
not a read acknowledgment. Existing snapshot-bound request and gesture checks
are unchanged. This presentation rule grants no gameplay, ancestry, mutation or
canonical-history authority and does not infer the contents of discarded rows.

## Independent regression and actual execution

An independent writer authored nine JVM cases and two actual-shell Compose
journeys in a separate existing D: worktree. The test commit is
`fb0b5847388d100e227f57824088e73a6cc66f03`; coordinator integration preserves its
two files byte-for-byte in `c81b0c45`. That pre-fix commit reproduces the failing
policy with the new tests. Existing tests were not relaxed.

Before the production edit, the nine JVM cases ran against original policy SHA
`176ff331a4cee2a3e2a4814d8318f5a35c37a60a4d0deca27861c951fa303145`:
**9 executed, 6 failures, 0 errors, 0 skipped**, Gradle exit 1 in 47 s. The
failures concern valid rollover/unread/navigation; three rejection controls pass.
This is a behavioral failure, not a compiler or fixture setup failure.

After the 15-line production addition, the identical nine cases pass, along
with all eight existing follow-policy cases: **17 passed, 0 failures/errors/
skips**, Gradle exit 0 in 33 s. JVM test file SHA remains
`494ba75116d64980e73821c0e248a068615cf63d19e064f35d5ecc7bdae2ad0b`.
Fixed policy SHA is
`a5584a4f89bba1708f26ccb1d3d1327072dcd726eb1322faf93361f32d7a1b61`.
The subsequent ordinary-profile host gate passes **420 JVM tests in 48 XML
suites, 0 failures/errors/skips**, compiles the Android-test sources and exits
zero for lint in 53 s. The new UI test class is present in compiler output.
Lint retains one existing `GradleDependency` warning and one
`AutoboxingStateCreation` hint; Android-test compilation also retains an
unrelated `FrameworkInterruptionTest` Boolean identity warning. No suppression
or assertion change is made to obtain the pass.

Commands run from each physical D: checkout's `apps/android` directory:

```powershell
# FIRST: original production policy, independent new test file.
.\gradlew.bat :app:testDebugUnitTest -x :app:buildRustAndroid --tests org.locallore.app.TranscriptRolloverTest --offline --no-daemon --console=plain --max-workers=2 --project-cache-dir D:\Dev\Experiments\LocalLore\2026-11-01-transcript-rollover-v1\gradle-first-cache
# Fixed policy and unchanged new/existing follow cases.
.\gradlew.bat :app:testDebugUnitTest -x :app:buildRustAndroid --tests org.locallore.app.TranscriptRolloverTest --tests org.locallore.app.TranscriptFollowTest --offline --no-daemon --console=plain --max-workers=2 --project-cache-dir D:\Dev\Experiments\LocalLore\2026-11-01-transcript-rollover-v1\gradle-integration-cache
# Broader host checks and instrumentation source compilation.
.\gradlew.bat :app:testDebugUnitTest :app:compileDebugAndroidTestKotlin :app:lintDebug -x :app:buildRustAndroid --offline --no-daemon --console=plain --max-workers=2 --project-cache-dir D:\Dev\Experiments\LocalLore\2026-11-01-transcript-rollover-v1\gradle-integration-cache
# Separate complete APK build, including the unchanged native engine.
.\gradlew.bat :app:assembleDebug :app:assembleDebugAndroidTest --offline --no-daemon --console=plain --max-workers=2 --project-cache-dir D:\Dev\Experiments\LocalLore\2026-11-01-transcript-rollover-v1\gradle-integration-cache
```

The run uses the existing JDK 21, pinned Gradle 8.11.1/AGP 8.10.1/Kotlin 2.2.21,
installed Android SDK and D: Gradle cache, with process-local TEMP/TMP/TMPDIR on
D:. No dependency is introduced or downloaded. Native compilation is explicitly
excluded for the Kotlin/JVM checks as documented by the Android development
README. A distinct complete APK build then exits zero in **2 min 50 s**,
including fresh Rust 1.93.1 / NDK 29.0.14206865 native builds for x86_64 and
ARM64 in 74 s and 69 s respectively. This establishes compilation/packaging,
not execution of those ABIs on a device.

From the checkout root, with the same process-local SDK/JDK environment:

```powershell
python -B scripts/audit_apk.py apps/android/app/build/outputs/apk/debug/app-debug.apk
python -B scripts/audit_instrumentation_apk.py apps/android/app/build/outputs/apk/debug/app-debug.apk apps/android/app/build/outputs/apk/androidTest/debug/app-debug-androidTest.apk
```

Both existing audits pass. All four packaged native libraries have 16 KiB ELF
LOAD alignment. The ordinary app/test package and matching signing-identity
checks pass; no permission, manifest, JNI or native-source change was made.

| Retained build artifact | Bytes | SHA-256 |
|---|---:|---|
| `apps/android/app/build/outputs/apk/debug/app-debug.apk` | 28,012,664 | `16b3b7761d64991c5906cb67c24ad8e562006acc1a349201a3b883fd7145d6d9` |
| `apps/android/app/build/outputs/apk/androidTest/debug/app-debug-androidTest.apk` | 2,275,810 | `1b598a0f05ac1f24a85fef035d7c16a9ed5fabfb4cee988c7b5a9a028b68ee8e` |

The APKs remain in the D: build tree; no binary or private diagnostics are
uploaded. Static audits do not establish observed network behavior or runtime
privacy. Fifty original JVM XML/lint/class-output records have verified retained
copies; the original failing FIRST capture remains separate.

## Rendered journeys and remaining gates

The two new Compose cases use the actual `LocalLoreScreen` with inert synthetic
accepted-shaped rows. One settles below row 40 at the composer, publishes the
40-to-40 rollover and requires row 42 to appear **before any test scroll or
Latest click**. The other preserves a retained older row until an explicit
Latest click. Both verify the original unsent draft/kind and quiet gameplay
callbacks. UI file SHA is
`e0e4ce794678c6d8786af1ac301b980d360f7114213637721f96d1b63ea47af0`.
Actual execution of these two journeys remains **UNRUN**. Source review and
compilation do not establish rendered navigation, touch or accessibility.

Independent source review found no concrete issue and ran no tests. The
pending SDK9 process-restoration proposal uses separately frozen original APKs;
its exact scope does not authorize this new UI cohort. Phone/model/ARM64,
keyboard/screen-reader/visual behavior and full M09/M10 acceptance stay separate.

Private original FIRST logs/XML, green XML and source-preservation records are
retained under
`D:/Dev/Experiments/LocalLore/2026-11-01-transcript-rollover-v1` within a declared
32 MiB control/evidence budget; combined checkout Android build output has a
6 GiB ceiling. Two inactive clean D: checkouts were reused, preserving old
branches/source snapshots and all 11 pre-existing ignored probe/build files.
Selected exact APKs, final public source and synthetic host reports are also
preserved under `D:/Dev/Recovery/LocalLore/2026-11-01-transcript-rollover-v1`
with a separate 64 MiB ceiling and full copy/hash readback. Original build and
control files remain; no model weights, saves or credentials are copied.
No frozen Android source/build, guest, shared ledger, ADB service, phone, model,
system setting or merge operation is changed by this packet.

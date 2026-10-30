# Android system theme: implementation and verification

Date: 2026-10-30. M09.05 system-theme slice and supporting M10.03 ordinary
package checks are in review. Full task checkboxes and owner acceptance remain
open. This is stacked on open/unmerged [#288](https://github.com/OptimumAF/LocalLore/pull/288).

## Resulting behavior

The story screen previously always selected a light color scheme. It now
follows Android's light/dark configuration through `LocalLoreTheme`. The eight
existing explicit light roles, the original light launch-style file, layout,
copy, draft ownership and callbacks are preserved. Dark mode uses a green-black
canvas, pale text and the existing teal identity. Overlay dialogs inherit the
same theme. The unavailable-session screen also uses this theme and a full-size
surface, preserving its message and Close action.

There is no preference database, new permission, dependency, animation, system
setting write or change to Rust, gameplay rules, gateways or canonical state.
The pure selector is `localLoreColorScheme(Boolean): ColorScheme`; the composable
defaults its selection to `isSystemInDarkTheme()` as described in the
[official Compose guidance](https://developer.android.com/develop/ui/compose/designsystems/material3).

Night launch resources share `LocalLoreNightBase`, whose explicit parent is
Android's dark Material theme. `values-night/styles.xml` selects it; the
`values-night-v27` variant adds `windowLightNavigationBar=false`. That attribute
was introduced in API 27 according to the
[Android API reference](https://developer.android.com/reference/android/R.attr#windowLightNavigationBar).
Min SDK remains 26. The independent base name avoids the implied style-parent
cycle rejected by lint. The original day style remains byte-identical.

## Checks actually run

Every row below runs the actual unchanged public command, using process-local
D: outputs/caches/temp and the existing approved signing credential in place:

```powershell
python scripts/check.py android --offline
```

No private Gradle replacement, test filter, task exclusion, lint suppression,
baseline, SDK increase, dependency change or forced native/test rerun was used.
Each call had its own 900-second process-tree owner and 262,144-byte capture
limit. Corrective runs followed specific source fixes, with prior source,
logs and partial outputs preserved before each change.

| Exact source | Public ms / exit | Actual outcome |
| --- | --- | --- |
| `9db44f31` / 2,300 inputs | 224,094 / 0 | Fresh ordinary baseline: both Rust targets, APKs, 332 JVM cases / 39 reports, lint and both audits pass |
| `6e666eae` / 2,304 inputs | 60,714 / 1 | New test compilation fails; four malformed destructured-loop headers; no JVM task or public APK audits |
| `f641017b` / 2,304 inputs | 48,178 / 1 | All 337 JVM cases / 40 reports pass and APKs compile; lint rejects API-27 attribute in unqualified night style |
| `bfcaeadc` / 2,306 inputs | 67,538 / 1 | JVM task executes; lint rejects two potential dotted-style inheritance cycles; public audits not reached |
| `5b48a65d` / 2,306 inputs | **71,374 / 0** | **337 JVM cases / 40 reports, lint and both public APK audits pass** |

Source review missed the loop syntax and the first two resource issues; actual
compiler/lint results govern these repairs. The loop fix adds only four opening
parentheses. API qualification and the later three-token base rename change no
test assertions, thresholds, methods, palette values or gameplay behavior.
Failed cohorts remain failed; old reports or partially produced APKs do not
qualify them.

The successful executable checkpoint is
`5b48a65d973b825dd15572e53732f299c7ae2d2a`. Its public command runs Gradle assembly,
all unfiltered JVM tests and lint, then the product audit and paired-APK audit
in the standard three-command order. The owner closes in 73,727 ms, worker exit
0, with complete cleanup/capture, stdout 7,766 bytes and stderr zero. All 2,306
raw source inputs and recorded tool/helper/predecessor pins match before/after.
The existing-key guard passes; neither fixed D: default-key path is created.

Final Gradle records 23 executed and 58 up-to-date actionable tasks. Unit tests,
lint analysis and lint reporting execute. Rust and the instrumentation assembly
are up-to-date; neither is falsely counted as a fresh compile in this row.
Both native targets were built in the baseline. All 372 native input files are
unchanged, and both final release/generated/merged library chains match their
baseline bytes. Stripped libraries match the final APK members for both ABIs.

The final 337 unique JVM cases have zero failures, errors or skips. Five new
methods preserve the eight light roles and use independent, unrounded sRGB
calculations: 16 normal-text role pairs per palette, body text over seven
surface elevations, and essential outlines/focus indicators. Targets are
drawn from [WCAG text contrast](https://www.w3.org/WAI/WCAG22/Understanding/contrast-minimum.html)
and [non-text contrast](https://www.w3.org/WAI/WCAG22/Understanding/non-text-contrast.html).
These numerical tests do not establish whole-screen accessibility or rendered
contrast under every platform/elevation/disabled-state combination.

Lint reports zero Error/Fatal and one existing `GradleDependency` warning for
coroutines-Android 1.10.2 versus 1.11.0. Lint/dependency scope remains unchanged.
Tool selections remain the existing JDK 21, Gradle 8.11.1, AGP 8.10.1,
Kotlin/Compose plugin 2.2.21, Compose BOM 2025.05.01 / Material3 1.3.2,
Rust 1.93.1, SDK 36, Build Tools 35.0.0 and NDK 29.0.14206865.

## Artifact and independent review

| Final APK | Bytes | SHA-256 |
| --- | ---: | --- |
| `org.locallore.app` | 28,166,336 | `b3ca8911bd4517f534bc1c253256cb50c6c4f4d55611b07e49636ffd1e80d661` |
| `org.locallore.app.test` | 3,319,589 | `95eae68f9ea0c92f57be4f07014d2260bf7d6714f9cbd956d5f29feed8a55d48` |

The actual public audits pass manifest/backup/ZIP/ELF policy, exact ordinary
packages, instrumentation target/provider/permission inventory and matching
verified signer. Certificate SHA-256:
`17ed497138b20dc1657d54039802305cfe0e3b782c73feaad20359c954707564`.
No private key was copied or generated. No separate per-tool execution trace
is invented from the audits' internal calls.

Independent closed-file review confirms all reports and command/source/pin
joins, both ABI chains, merged night v8/v27 aliases and compiled resource-table
presence. It parses exactly two public no-argument void JUnit methods of
`SystemThemeTest` in the test DEX, absent from the product. Their scripted state
and callbacks test day/night draft/kind/message/notice conservation, no automatic
actions, explicit Send/mode/action delivery, and busy-state cancellation.
These journeys are **compiled and packaged, unrun on Android**. The test APK
is unchanged from the earlier successful test compilation at `f641017b`.

The independent reader initially overrequired fresh instrumentation assembly,
then mishandled CRLF task-log normalization. Both reader failures and their
sources are retained. Corrected v3 records actual task states and line endings;
it replays files only, with no build, audit, SDK or test repeat. Its receipt
SHA-256 is `5b16292164505aed6f838ab06ee62712bd771576a6b471c0252d30e69ca90fec`.

## Preservation and open gates

The final executed raw source archive has 2,306 members / 32,039,140 raw bytes,
10,264,387 compressed bytes, SHA-256
`d38efcdefbb961a410f35e84175b9d80083b4e7e0560b2e306b46c849cfa6ac2`.
Its phase preservation manifest SHA-256 is
`9f72308f0217987f1061bd7892f9d3070001718a9ee5db10c7d7bbb599bfaac3`.
All members and original raw bytes were reread before documentation changed.
Baseline and all three failed executed sources have their own frozen maps/ZIPs.
Git-normalized history does not substitute for those raw executed bytes.

Original scripts, captures, source archives and preserved baseline/failure/final
outputs remain at `D:\Dev\Experiments\LocalLore\2026-10-30-system-theme-v1`.
Selected recovery uses the matching `D:\Dev\Recovery\LocalLore` root; final
ticket handoff records exact copy/ZIP/three-branch-bundle seals and readback.
The original 8 GiB packet budget includes three worktrees, all cohorts, generated
builds, temporary/cache allowances and recovery. It was not widened after
failures. Final handoff records retained totals; no exclusive peak or OS quota
claim is made. No prior source, guest, cache, failed capture or recovery is deleted.

No phone, emulator, ADB/service, model, traffic or gameplay experiment occurred.
The owner chose to continue without the phone. Visual day/night behavior,
screen readers, keyboard/touch, large fonts, current-source Android lifecycle,
physical/ARM64 execution and real-model quality/performance remain unverified.
Full M09.05/M10.03 criteria and owner acceptance stay open; no merge or release.
The next runnable host check is the archive-profile public gate on this updated
source in a separate bounded packet. The two compiled theme journeys require
separately authorized target admission.

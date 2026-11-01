# Player inventory APK verification — 2026-11-01

Refs #14 (M10.02/M10.03), supporting #13 (M09.03/M09.04/M09.06). Build/artifact
slice in review; full criteria remain unchecked. Stacked on inventory PR #329.
This packet builds the ordinary app/test pair with both real Rust JNI libraries.
No production code, dependency, protocol, runtime or model selection changes.

## Exact build and source

The inactive clean Spike-review checkout was reused after preserving its old
`dc2177a4` branch/source ZIP; there were no ignored/untracked files or app/build
and project-cache directories. Build source is PR #329 at
`b8dbbcbb1b3ea67552d7449f94286187a31166ad`, with2,548 tracked files. Before/after
raw maps and every raw-source ZIP member match. Root changes only README and
this report after the builder and artifact readers close.

Actual standard command from the physical D: repository root:

```text
python -I -S -B scripts/check.py android --offline
```

It runs the normal three-command route: app/test assembly, unfiltered JVM tests
and lint through the verified Gradle wrapper, then product and paired-APK audits.
Native compilation remains included through preBuild; no clean or native-task
exclusion is used. Process-local TEMP/TMP/TMPDIR are `D:/Dev/_Temp`, Cargo/Gradle
caches use their existing D: locations, and JAVA_HOME/ANDROID_HOME/SDK_ROOT point
to installed tools. Downloads, automatic provisioning and cache reuse were
disabled for this process. Global settings and installed tool locations remain.

Preflight observes JDK21.0.4+8, Rust/Cargo1.93.1 and both installed Android
targets, cached Gradle8.11.1, SDK36r2, Build Tools35.0.0 and NDK29.0.14206865.
Existing AGP8.10.1/Kotlin2.2.21/Compose BOM2025.05.01 pins are unchanged. No new
compatibility, licensing or dependency choice is introduced.

## Actual results

One public build runs to return0 in **115.068s**. Its finite host owner reports
115.160s, child exit0, known cleanup/capture and stable source bindings. The
existing 900-second/262,144-byte outer capture and own-output budget monitor
remain distinct from inner-tool evidence. No build retry occurred.

| Check | Actual result |
| --- | --- |
| Gradle | 81 actionable tasks,81 executed; required native, Kotlin, JVM, lint, assembly, merge and strip tasks execute |
| Rust Android compilation | Fresh x86_64 release27.45s; arm64-v8a26.22s; compiler times, not runtime performance |
| JVM | 439 unique cases/52 XML suites;0 failures/errors/skips, including inventory wire5 +Shell6 |
| Lint | 0 errors,1 existing GradleDependency warning,1 existing AutoboxingStateCreation hint |
| Compiler | Existing FrameworkInterruptionTest AtomicReference/Boolean warning remains |
| Public audits | Original ordinary product and paired-instrumentation audit commands both pass |
| Source | All2,548 raw inputs unchanged before/after/closed-reader checks; no source mutation during build |

Non-actionable Gradle headings are distinguished from executed actions; a source
task inclusion alone is not treated as compilation evidence. Independent raw
parsing observes96 headings and the recorded81 executed actions.

## Immutable pair and native joins

| Artifact | Bytes | SHA-256 |
| --- | ---: | --- |
| App | 28,029,072 | `1806fd2594c09cccd8a79bb9c9608f55991f8f79bfe3f6d3f6a0f2660dab3683` |
| Instrumentation | 2,321,082 | `6934df9326aa52353d7a15c5be0823c5227d916a3dcfcc2444feeade3ccece9d` |

Packages are `org.locallore.app` and `org.locallore.app.test`. The recorded
common debug certificate is explicitly compared to expected SHA-256
`17ed497138b20dc1657d54039802305cfe0e3b782c73feaad20359c954707564`;
pair equality alone would not establish that identity. No key is copied or
published. Product permission is its own dynamic-receiver permission; test
permission is REORDER_TASKS. Recorded package/runner/backup policy checks pass.
Source backup exclusions retain five domains in each cloud/device-transfer group.

All four packaged libraries (Rust and androidx.graphics.path in both ABIs) pass
uncompressed ZIP/local-header and ELF LOAD16KiB alignment. For each Rust ABI,
release=generated=merged bytes and stripped=APK bytes. Stripping changes bytes;
there is no whole-chain equality claim. Current Cargo release/deps are the two
exact same-object/same-hash aliases with nlink2; generated/merged/stripped and
other artifact roles remain single-link. No file is unlinked or copied merely
to evade an alias rule. These are current observations, not a historical alias
attestation for every instant of compilation.

Original APKs remain under the build checkout's ordinary `app/build/outputs/apk`
directories. Verified copies and records stay private under
`D:/Dev/Experiments/LocalLore/2026-11-01-inventory-apks-v1`.

## Eleven actual test definitions

Closed-file inspection uses the unchanged bounded generic DEX definition reader,
not the physical-model audit entrypoint. It verifies public/concrete/instance/
nonnative/void/zero-argument JUnit definitions for the existing keyboard2,
status2, heading2 and quick-action2 methods plus inventory3. All five outer and
nested test families are absent from the product APK. Names/strings alone are
not accepted as method definitions.

The generic API retains method flags/prototypes/annotations but does not return
code offsets. A small private consumer of the same bounded DEX table/ULEB/slice
API additionally checks nonzero aligned offsets and positive bounded bodies
for the eleven methods (130–845 code units). Its in-memory positive control
passes; zero offset, zero instructions and out-of-bounds witnesses refuse. No
production parser is changed and no APK is mutated or extracted.

The inventory methods are:

- `savedRowsKnownEmptyAndUnavailableStayDistinctWhileDemoKeepsItsOriginalPotionRow`
- `scopeChangesFenceRetainedOpenAndCloseWhileAcceptedRefreshesKeepTheUnsentDialogue`
- `doubledFontKeepsLongExactIdentifiersAllQuantitiesAndCloseReachableWithoutGameActions`

All eleven selectors match their current five source classes. This new pair
does not inherit the frozen SDK11/B55 pair's authority or qualify its proposals.

## Independent review and preserved checker corrections

Separate D: reviewers cover native/build policy and closed APK/DEX evidence.
They do not repeat the build, audit CLIs, tests or device operations.

Native review verifies76 producer bindings,2,548 current raw inputs/source ZIP,
owner/public/three-command joins, native alias/strip chains, all library
alignment, APK copies,439/52 XML and lint. Its raw CRLF task-line oracle initially
refuses; a narrow continuation uses splitlines/fullmatch without relaxing task
tokens or repeating completed source/archive scans.

The artifact reader's first pass verifies producer/source/raw-archive hashes
but incorrectly expects a Git archive comment and directory entries. The actual
producer intentionally makes a raw ZIP with2,548 ordered file members and an
empty comment. The failure is preserved. A separately sealed continuation
requires that exact first failure/helper/terminal, retains its successful source
prefix, checks the strict actual raw format/CRCs/member hashes and completes the
remaining55 artifact pairs, audits, XML and DEX/body checks. This is combined
evidence across preserved phases, not a fresh single-pass full GREEN.

A review preflight also used an older B52 status-test hash as a supposed B55
comparison. Actual current B55 and build-source bytes/blob are identical for
that file; the incorrect migration inference is explicitly withdrawn. These
are private-reader corrections, not product failures or artifact rewrites.

The original audit JSON, source/APK bytes, raw outer streams, actual command
results and source pins are retained. Original inner AAPT/apksigner streams and
full executable-byte provenance are not retained; neither source review nor
the outer supervisor manufactures them.

## Retention and remaining gates

Controls have a64MiB budget; selected recovery at the matching
`D:/Dev/Recovery/LocalLore/2026-11-01-inventory-apks-v1` has128MiB. Final source
ZIPs, exact pins/copies and seals are recorded in the ticket handoff. Original
sources, generated files, failed reader captures and prior recovery remain.
All newly generated ignored files total650,056,324B below4GiB, including four
retained audit pycs141,470B. The owner samples app/build plus project cache;
shared cache/TEMP growth is not comprehensively metered or a global disk quota.

All eleven selected Android methods remain **UNRUN**. Neither ABI's compilation
or packaging proves actual JNI/ARM64 execution, keyboard or TalkBack behavior,
native authored-world mechanics, model quality, physical-phone performance,
process death, traffic privacy or complete journeys. The build/source excludes
sibling PR #317's rollover fix. Full M09/M10 criteria and owner acceptance stay
open. No guest, retirement, ledger lock/plan/reservation/admission/auth/input,
prepare/boot, ADB/phone/port/process census, model, global settings,
unrelated-emulator/shared-service or merge action occurs.

Frozen SDK10/SDK11 sources, manifests, proposals and old APKs remain unchanged.
The pending SDK11 exact approval covers its old eight-method operation, not this
new pair. Next dependent step is separately source-bound qualification of the
new artifacts; any device execution still needs applicable exact authority.

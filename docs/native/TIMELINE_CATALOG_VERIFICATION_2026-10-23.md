# Timeline catalog and Android child resume — 2026-10-23

Refs #12 (M08.01; prerequisite supporting M08.05). Implemented and locally
verified, pending owner acceptance. Stacked on PR #81 / `ddd4eed`.
Executable and test source: `36e074d09bc7a13c6c9f6ae68be2e2e7e57f0a5c`.
See the [contract](TIMELINE_CATALOG_CONTRACT.md),
[sanitized results](TIMELINE_CATALOG_RESULTS_2026-10-23.json) and
[independent review](BRANCH_RETENTION_REVIEW_2026-10-23.md).

## Behavior and plan refinement

The prior Android client refused legitimate inherited receipt scopes and then
looked for a selected child in its root-only story library. A real JNI red run
on emulator A reproduced the first rejection; the second is a source finding
because the first exception prevents reaching it. The catalog and selector
repair this prerequisite before parent-retirement implementation. M08.05's
retained-child requirement remains unchanged. No leaf-only substitute, schema3
migration, archivev2, retirement or branch deletion is implemented here.

Store reads/replays catalog metadata in one read snapshot; Host/Persistence
exposes it through the existing bounded native workspace call. Compose selects
root/child/sibling progress without re-scoping original accepted requests.
Whole-story deletion from a child resolves root scope/head. The desktop Host
schema was regenerated with its required `host` feature; this also refreshes
previously stale existing commands. No desktop selector was added.

## Checks actually performed

Environment: Windows, Rust/Cargo 1.93.1, Java 17.0.6, Gradle 8.11.1,
AGP 8.10.1, Kotlin 2.2.21, compile/target SDK36, Build Tools35.0.0,
NDK29.0.14206865. No dependency or model change. The two selected authorized
emulators were already running: API35, x86_64, 4096-byte OS pages.
Four emulators and zero physical phones were observed. Only aliases A/B
identify devices in this report.

| Command/procedure | Result |
|---|---|
| `python scripts/check.py host --offline` | 338 Rust workspace passes, 0 failures, 2 existing explicit qualifiers ignored; strict Clippy/fmt pass; four generated fixture cases match; 3 linker and 232 Python tests pass |
| Store `branch_catalog` test target | 7 passes, included above; also passed twice in author worktree with strict Clippy |
| Android crate public `branch_catalog` test target | 4 passes, included above; author's isolated strict Clippy also passed |
| Dedicated Gradle full compile/build/test/lint | 77 JVM passes, 0 failures/errors/skips; lint 0 errors, one existing GradleDependency warning |
| Ordinary Gradle full compile/build/test/lint | 77 JVM passes, 0 failures/errors/skips; same lint outcome |
| Dedicated and ordinary APK audits | Both ABIs packaged; ELF LOAD and ZIP alignment16KiB; nine expected archive JNI symbols; no fixture96 symbol/string, test provider or INTERNET permission in product APK; identical Rust native bytes |
| Final A and B instrumentation | Each 14 focused +26 regression passes: 80 final-artifact passes, 0 failures/skips/unfinished methods |
| Configuration guards | Seven invalid property/cache/combined-mode/release invocations rejected as expected |
| Preservation | Eleven previous installed package identities unchanged; no clear/uninstall. Ordinary build preserved twelve nonordinary local APKs |

The two ignored host methods require the separate compiled SQLite96 fixture
profile or are a child IPC worker invoked by parent-owned interruption tests;
they are not counted as passes. There is no new physical-device qualification.

The 14-method cohort consists of TimelineNativeTest1, TimelineProtocolTest4,
TimelineActivityTest1, TimelineMainActivityTest1 and
DurableDeletionRecoveryTest7. Native execution restores original inherited
receipt scopes, continues an independent sibling without changing captured
parent/child canon, rejects potion reuse and reacquires all workspace slots.
The ComponentActivity journey uses actual Compose/JNI/SQLite: selects a child,
checks inherited transcript and sibling exclusion, rejects potion reuse,
guards switching during immediate cancellation, explicitly recovers if needed,
advances root to3 while child stays2, reopens owners, then confirms whole-story
deletion against root3 and retains an unrelated story. Both native registries'
four slots are reacquired. The real MainActivity test exercises its product
factory and selector on its current root; child selection is the separate
ComponentActivity proof.

The 26-method regression cohort consists of ArchiveIntegrationTest6,
ArchiveDocumentTest5, ArchiveDialogTest6, DurableNativeTest5,
ArchiveActivityTest2 and ArchiveChooserActivityTest2. Raw instrumentation
method starts/ends, class inventories, numtests and terminal runner status were
checked; ADB process exit alone is not treated as a test pass.

## Reproduction

Host checks use the command above. From `apps/android`, dedicated build:

```powershell
.\gradlew.bat :app:assembleDebug :app:assembleDebugAndroidTest :app:cleanTestDebugUnitTest :app:testDebugUnitTest :app:lintDebug -PlocalLoreTimelineVerification=true --project-cache-dir .gradle-timeline -Pkotlin.incremental=false --offline --no-daemon --console=plain -Pandroid.builder.sdkDownload=false
```

Repeat without the verification property/cache to build the ordinary app.
The dedicated package is `org.locallore.app.timelineverify`; outputs are in
`app/build-timeline`. Install only this pair on authorized targets, preserving
existing packages/data, and invoke AndroidJUnitRunner with the class lists
above. Do not install the ordinary APK over existing saves for this proof.
Generate the Host schema with
`cargo run -p locallore --features host --example host_schema --locked --offline`.

Private raw logs, test XML, bounded-client journals, source/APK bindings and
owned-package ledgers remain under `target/checks/timeline-catalog`. Public
results contain synthetic metadata, hashes and aliases only. New test roots
are retained app-private synthetic data; no recursive removal of saves occurs.

## All attempts and qualifications

1. Unchanged-client red build/source `fbd227b` passed build/72 JVM/lint.
   A's actual child test failed at DurableGateway.snapshot's inherited-scope
   check: 0 passes, 1 expected regression failure. Original PR81 native bytes
   were used. No B red run is claimed.
2. First integrated incremental Kotlin build failed on unresolved unchanged
   top-level/internal declarations. Full `-Pkotlin.incremental=false` compile
   passed without source visibility changes. Stale incremental metadata is the
   working diagnosis, not a proven compiler root cause.
3. Initial integrated A/B cohorts each ran14: 13 passed and one new UI test
   failed because it searched for an uncomposed lazy-list action. `36e074d`
   changes test scrolling only, without relaxing assertions or deadlines.
   Rebuilt artifacts then passed both final cohorts. These two real test
   failures and all original raws remain recorded.
4. A's regression runner passed all26 methods and strict parsing, then a
   postflight APK `sha256sum` client timed out after20s with cleanup confirmed.
   That exception bypassed its original result-file write. Fresh bounded
   postflight reads verified all hashes and owned-process absence; tests were
   not rerun. The timeout journal and recovered result are distinct artifacts.
   A read-only diagnostic also had an output-format AttributeError before
   printing; it changed no device state or test result.
5. The first schema-generation command omitted `--features host` and returned
   the example's enable-feature message. The correct command above generated
   actual JSON. This was not treated as a passing schema generation.

Final APK passes total80; superseded initial green cohorts add26 actual passes
and2 failures. The separate pre-fix red run contributes one expected failure,
never a passing result. Build/configuration failures are reported separately.

## Remaining limits and next task

The provider is deterministic fake inference. No real-model quality, phone
performance, ARM64 execution, thermal or sustained-runtime qualification is
established. M01.01 physical-device gates remain blocked pending an authorized
phone. Cross-built ARM64 libraries are not device results.

Catalog replay is bounded by existing graph/history limits but repeats work
across branches. There is no large-history latency result or hard CPU deadline.
Store cancellation checks occur between replay operations; native metadata work
is not claimed preemptible. Immediate UI cancellation proves the switch guard,
not a deliberately scheduled Running-native-inference overlap.

Next runnable work: M08.05 retained-parent deletion with backed-up schema3
migration, persistent deleted-ID/retirement state, private ancestry replay,
versioned archivev2 roundtrips and targeted stale-session fencing. Preserve
original accepted provenance and retained child/sibling isolation throughout.

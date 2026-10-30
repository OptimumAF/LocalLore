# Original-story input validation — 2026-10-30

Refs #13 (M09.02, supporting M09.06); #14 (supporting M10.02).
[Draft PR #282](https://github.com/OptimumAF/LocalLore/pull/282) is based on
`main` at `28b4a7ff17617c12c4138a60aa1beebf83a41ab1` and remains unmerged.
This is a verified default JVM/controller fix, not complete journey acceptance.
The owner chose to continue without the phone. No phone, emulator, service,
installation or model operation occurs in this packet.

## Problem and change

With player `Iris` and cast member `iris`, the dialog's structural wire predicate
could enable Generate and suppress its warning, while the controller's existing
semantic predicate silently refused the same input. The same discrepancy existed
between cast names differing only in case. Separately, individually valid fields
could exceed the existing combined wire cap: a programmatic Generate could call
the gateway before the 4,096-byte input bound, and Review before the 8,192-byte
proposal bound. The dialog already checked those aggregate bounds.

The five-line production change makes `OriginalStoryWire.valid` retain the
existing semantic input predicate and encoded round-trip/aggregate checks.
Generate uses that complete predicate. Review retains editability, title and
`validOriginalDraft` checks and adds the existing wire gate. The current inline
warning explains that each character, including the player, needs a different
name. Invalid input preserves the editor and reaches no generation/review
gateway; correcting the name enables one generation.

No parser limit, Rust rule, canonical event, creation consent, provider, model,
database or production dependency changes. Kotlin's eligibility check is not a
second gameplay authority. Native validation and explicit reviewed creation
remain required.

## Independent original regressions

Eight original methods were committed first at `fc06a64b`, before reading the
production candidate. Test-only runtime setup is a distinct `3d8159e1` commit;
production still matches the base during the baseline. The test file's raw
SHA-256 remains unchanged through both actual runs:
`3441912e4f26563363a3890612d54b3b547b56167bafd857ee479b1533ab12e2`.

The actual baseline executes all eight methods with four assertion failures,
zero errors/skips. Both collision predicates fail; the aggregate input and
proposal cases each observe a gateway call where zero is required. The valid
input/corrected-name positive control passes. Real JSON classpath provenance is
retained, so the failures are not Android stub errors. The test task executes;
it is not an inherited or up-to-date report. All 2,288 tracked source hashes,
helper and runtime/tool pins remain unchanged. Gradle returns 1; its finite
expected-failure capture wrapper returns 0, without relabeling the tests green.
Owner elapsed time is 62,247 ms with known capture/cleanup and empty streams.

The remaining cases preserve zero gateway activity for collisions, a corrected
name producing exactly one generation, review invalidation after editing, and
the earlier draft-domain validation. All eight original bodies/assertions pass
unchanged on the fixed code.

## JVM runtime and setup failures

Android's standard local JVM JSON classes are throwing stubs. A real test runtime
is required to exercise the existing wire validator. Only
`testImplementation("org.json:json:20260814")` and its two default debug unit
classpath lock entries are added. All prior locked versions and the LiteRT lock
remain unchanged. The [separate provenance record](JVM_JSON_TEST_DEPENDENCY_2026-10-30.json)
contains official release/license/POM links and resolved JAR/POM hashes. The
exact-tag license is Public Domain, the POM targets Java 8, and its declared
dependencies are upstream tests only. The library is not an app runtime
dependency. Its JVM behavior does not qualify every Android JSON edge case.

Normal fixed-coordinate Maven Central provisioning and a real JSONObject smoke
pass before the app tests. All subsequent app resolution/test execution is
offline, using installed JDK 21 and the pinned Gradle 8.11.1 wrapper. Global
SDK/tool settings and existing cache contents are preserved. Temporary and new
project/cache outputs are on physical D.

Two preparation failures remain separately retained. The first dry task graph
succeeds, but its wrapper then refuses an untracked custom project-cache folder;
tracked bytes are unchanged and that folder remains in place. A separate
external D project cache fixes output placement without hiding/deleting data.
An initial lock helper requests ambiguous self-project artifacts before tests;
the corrected helper resolves the normal component graph and adds only the
pinned JSON entry. Neither preparation failure is a product regression or a JVM
test result. No JSON shim or weakened assertion is substituted.

## Actual fixed verification

Executed source is `6dec2b7be37e1a2760cc5b3ec5a8e4c726bffb8d`, with 2,289
tracked raw bindings. Later report edits retain that attribution.

The **unfiltered default debug JVM suite passes 332 unique methods across
39 XML reports**, zero failures/errors/skips, including all eight original
regressions. This count describes the default configuration, not every isolated
SDK/physical-model verification profile. Kotlin/Compose compiles. The test task
actually executes after `cleanTestDebugUnitTest`; no `--tests` filter is present.
All source, helper and runtime/tool pins remain unchanged, and the checkout is
clean. The owner returns 0 after 45,929 ms with complete capture/cleanup and empty
streams; the actual Gradle run takes about 44 seconds and has zero stderr.

Exact private runner commands:

```text
python -I -S -B D:/Dev/Experiments/LocalLore/2026-10-30-original-input-v1/tests/run-jvm-v4.py baseline-v1
python -I -S -B D:/Dev/Experiments/LocalLore/2026-10-30-original-input-v1/green/run-full-jvm-v1.py full-jvm-v1
```

The final recorded Gradle argv invokes the installed JDK directly with the
committed wrapper and includes:

```text
--offline --no-daemon --no-build-cache --max-workers=2 --console=plain
--gradle-user-home D:\Dev\Tools\Caches\Gradle
--project-cache-dir D:\Dev\Experiments\LocalLore\2026-10-30-original-input-v1\green\project-cache-v2
-Porg.gradle.java.installations.auto-download=false -Pandroid.builder.sdkDownload=false
-Pkotlin.incremental=false -Pkotlin.compiler.execution.strategy=in-process
-Pkotlin.daemon.useFallbackStrategy=false
:app:cleanTestDebugUnitTest :app:testDebugUnitTest -x :app:buildRustAndroid
```

An existing private init script records the actual unit classpath and JSON
code-source. The native build is explicitly excluded because Rust/JNI is
unchanged and local JVM cases use fake gateways. **No APK, JNI artifact,
instrumentation, rendered/touch UI, accessibility or device result is claimed.**
The normal complete Android build gate remains required for its own scope.

| Artifact | SHA-256 |
|---|---|
| Original baseline result | `923ef059a72b86d67ffb4b1393fb091223ffa23cfd637e0a32a9b902e5652417` |
| Original baseline XML | `ac30964888f5e10f383bf606864d9fc8fd7327d0a92213a5be30a2dc4be0c362` |
| Baseline review | `4eb11cd699131f212e963a3cf30fc343c87be35a9a95c4e2318362b7e35babcc` |
| Full default JVM result | `39f69d5bb306bbedef1a8f8c78081cc2f5a2c36d226ad61636c0c74847436164` |
| Full JVM review/332 IDs/39 XML pins | `3879f1f7d8d5c5d421f1dfcd855c50b0c057392e8b6896f37de252526e2472a9` |
| Full runner | `b0e708e2db791c9e428ce94d8ab987d7f011d4f4671eea237bc60636b70d1da3` |

The independent tester reviews the final three production files after the
original baseline and finds no concrete blocker. Root separately reads all
39 actual XML files: 332 unique case IDs, all counts matched, no hidden
failure/error/skip descendants and all eight original IDs present. Root also
verifies the recorded unfiltered/offline command and explicit native exclusion.

## Preservation and handoff

The exact executed-source ZIP contains 2,289 raw files / 31,911,162 bytes,
10,215,453 compressed bytes, SHA-256
`a8433d4bb981768f6bf211e8aed9410a748bbcfcda88918e19758b63bee67a4b`.
Every original and ZIP member matches the actual green source map before/after;
Git canonical bytes or later docs are not substituted. Manifest SHA-256:
`ca5642574db9065fd06bcf4c383c04666d8af061d87ba66be6d8947e4fef6137`.

Private scripts, original failures, XML, classpath evidence and source snapshots
remain under D:\Dev\Experiments\LocalLore\2026-10-30-original-input-v1,
with selected recovery under the matching D:\Dev\Recovery\LocalLore root.
The declared packet cap is 8 GiB including both source trees, generated outputs,
cache growth and recovery. Existing global caches are not duplicated; observed
shared-cache growth is not exclusive attribution. Final recovery/readback
counts and hashes belong in the ticket handoff. Generated/untracked original
cache data remains retained, not silently deleted or ignored to claim cleanliness.

M09.02 and supporting M09.06/M10.02 implementation are in review; full criteria
and checkboxes remain open pending broader verification and owner acceptance.
Further host review can continue without a phone. Complete device journeys,
touch/accessibility and physical real-model gates remain separate. No merge,
release or private diagnostic/model upload occurs.

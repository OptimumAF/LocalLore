# Physical-model harness verification — 2026-10-25

Refs #5 (M01.01/M01.02/M01.05 supporting) and #9 (M05.05 prerequisite).
This bounded implementation is stacked on unmerged [PR #181](https://github.com/OptimumAF/LocalLore/pull/181).
It prepares a separate ARM64 phone experiment. Build, host tests and APK audits
do not establish phone inference, performance, model quality or milestone acceptance.
The authoritative task status and work log remain in the linked tickets.

## Implementation

The explicit debug profile uses `org.locallore.app.phoneverify` and its separate
test package. Its six fixed methods exercise precheck, receipt import, actual
SDK cancellation, ordinary Compose Gift and literal Dialogue, then a fresh
process reopening the same receipts without inference. The actual Rust engine,
setup controller, receipt transaction and CPU SDK worker remain in the path.
The LLM proposes; the engine validates and commits; narration cannot supply
canonical events. Recorded statements remain distinct from world truth.

The [physical policy](PHYSICAL_MODEL_PROFILE.md),
[Android protocol](PHYSICAL_MODEL_ANDROID_PROTOCOL.md) and
[host protocol](PHYSICAL_MODEL_HOST_PROTOCOL.md) define the closed interfaces.
Source, control, accepted model and proof roots share the new app's internal
filesystem and UID. Initial admission accounts for two model copies plus a
single 2 GiB reserve. Ongoing checks preserve the original admitted owner and
do not charge the initial 4 GiB available-memory margin again after mapping
the model. Low-memory, identity, filesystem and space failures remain terminal.
These are experiment margins, not measured OS minimums or supported tiers.

No runtime, model, Rust engine/schema, production selector or dependency version
changes. The existing LiteRT-LM 0.18.1 CPU path and Gemma model identity remain
pinned; official compatibility/license references are in the Android protocol.
The 2,588,147,712-byte model has SHA256
`181938105e0eefd105961417e8da75903eacda102c4fce9ce90f50b97139a63c`.

## Android checks actually performed

The final Android build source is `fbef4195`, with 450 Android/Rust/config input
hashes identical before and after the owned build. Using existing JDK 21 and
the offline locked SDK graph, run from `apps/android`:

```powershell
.\gradlew.bat :app:testDebugUnitTest :app:lintDebug :app:assembleDebug :app:assembleDebugAndroidTest :app:auditLiteRtDependencies :app:auditLintAnalyzer --offline --no-daemon --console=plain --project-cache-dir .gradle-physical-model -PlocalLorePhysicalModelVerification=true -PlocalLoreLiteRtVerification=true -PlocalLoreModelSetupVerification=true -Pandroid.experimental.lint.version=9.4.1 -Porg.gradle.java.installations.auto-download=false
```

Result: **488 JVM tests, 45 classes, zero failures/errors/skips**; lint zero
errors and ten warnings. The owned process completed in 60,429 ms, child 0,
known descendant cleanup and complete output capture. Both dependency and
analyzer audits completed. Warnings retain the existing target/dependency
advisories and conservative `usableSpace` observations; no cache reclamation,
SDK upgrade, system setting or suppression was used to make the build pass.

The dedicated paired APK audit at `df5669a7` ran:

```text
python -B -E scripts/audit_physical_model_apk.py --app <retained-app.apk> --test <retained-test.apk>
```

It **passed** in an owned 2,948 ms process, child 0, known cleanup, complete
capture and zero stderr. It checks actual DEX definitions for all six exact
public test methods, package/runner/target identity, permissions and exported
components, backup exclusions, equal signing identity, ZIP/native alignment
and unchanged full APK identities across the audit. Both ARM64 and x86_64
libraries have 16 KiB ELF load alignment. This is packaging inspection, not
16 KiB device execution or a physical-model result.

| Retained artifact | Bytes | SHA256 |
| --- | ---: | --- |
| App | 75,426,127 | `13f8768e010bf007319748b0b158694ffb6c847d50f87638cf0af42fca60e1a5` |
| Test | 1,899,011 | `1c3bba2756b5ae6c46842d483cd07dba433b1b3cfa83ee215ae0e1e47af4298c` |

## Retained failures and corrections

An earlier foundation build passed 487 JVM tests; the six instrumentation
methods were not yet present and no test APK was credited. The later complete
`085d9244` build passed 488 tests and compiled all six methods. Independent review
rehashes all 51 retained artifacts, verifies all 488 test cases, and matches
every one of its 450 source hashes against that exact Git commit.

The first actual paired audit then refused the app. Its first parser error was
`Minimum SDK changed`: bounded raw diagnostics proved uniform Windows CRLF,
with the unchanged minimum 26 and target 36. Real badging omitted an
instrumentation line that mocked fixtures had assumed. The corrected audit
accepts uniform LF or CRLF only, rejects malformed/duplicate/conflicting SDK
rows, and always requires the exact runner/target in the manifest tree. Any
optional badging instrumentation row must agree.

The actual manifest also exposed a generic Compose test dependency's exported
`androidx.activity.ComponentActivity`. The physical-only manifest now removes
that unused activity; its phases use an empty Compose rule and launch the real
setup/play activities. Other experiment manifests are unchanged. The old app
APK was retained and superseded, never installed. A new build and actual
paired audit produced the identities above. No third-party activity exception
was added to make that audit pass.

Independent host review also found missing current-user binding, missing fresh
APK/UID/resource admission after model-source hashing, weak path/hash checks,
and child-exit-only completion validation. Their corrections and final host
gate are recorded in the host protocol and ticket evidence; no device grant
may precede their integrated verification.

## Limits and next gate

The initial device refresh found only emulator entries; the previously selected
USB phone was absent, so it made zero target calls. No phone model copy,
installation, import, cancellation, inference or restart result is inferred
from the build. A fresh admitted phone discovery and source/APK-bound precheck
must precede local weight staging and the five subsequent phases.

Physical latency/quality, peak memory, sustained thermal behavior, all failure
modes, DocumentsUI and production backend/support selection remain pending.
Private identities, raw diagnostics, APKs, model weights and app data remain
outside Git. No other emulator is stopped, no system setting changes and no
merge or release is performed by this packet.

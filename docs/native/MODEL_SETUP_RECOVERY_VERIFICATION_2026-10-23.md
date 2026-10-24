# Setup recovery verification — 2026-10-23

Refs #9, M05.05 setup prerequisite and M05.04 supporting. Execution began from
PR #139 at `727f8e11416d16bc1f1ebed81ba23db195be6fc1`. The
[contract](MODEL_SETUP_RECOVERY_CONTRACT.md) defines the boundary. Both selected
synthetic emulator methods passed; full milestone and owner acceptance remain
pending. No merge or release was performed by this packet.

## Implementation and host checks

Author `5205e78` was integrated as `5ebb424`. The two new private fixture/test
files exercise the actual setup screen and the production admission class,
with a separate fixed synthetic instance. No production reset/release seam,
runtime dependency, permission, model choice or gameplay rule changed. Manifest
and APK guards confine the helper to the explicit verification profile and
exclude TEST code from APP. Older negative tests include the other required
helpers, so a missing new helper cannot make them pass vacuously.

| Actual check | Result |
| --- | --- |
| `python -B -m unittest discover -s scripts/tests` | 197 PASS, 14.834 s; original executor terminal 0 |
| `python -B -m unittest discover -s scripts/tests -p test_audit_apk.py` | 18 PASS, 1.672 s |
| Regular setup full offline Gradle worker | Child 0, known cleanup, 165.188 s |
| Explicit fixture full offline Gradle worker | Child 0, known cleanup, 150.671 s |
| Regular setup and fixture JUnit XML | Each 276 tests / 28 suites; zero failures/errors/skips |
| Regular setup lint | Zero errors; OldTargetApi, GradleDependency, two UsableSpace advisories |
| Explicit fixture lint | Zero errors; the regular four plus UseKtx |
| Copied signed APKs and package audits | PASS: exact launcher/private Activities, permissions, TEST-only providers, signatures, SDK/native/notices and 16 KiB ELF/ZIP alignment |
| Dependency/analyzer and DEX supplement | PASS: pinned graph, new fixture identity/methods, older fixture classes retained |
| Final controller preparation | 32 pure cases PASS, zero failures/errors/skips, 5.302 s; no device calls |

Both workers invoked `org.gradle.wrapper.GradleWrapperMain` with
`:app:assembleDebug :app:assembleDebugAndroidTest :app:cleanTestDebugUnitTest
:app:testDebugUnitTest :app:lintDebug :app:auditLiteRtDependencies
:app:auditLintAnalyzer`, `--offline --no-daemon --console=plain --max-workers=2`,
the exclusive `.gradle-litert-worker` project cache, disabled SDK/Java downloads,
explicit Java 21 compilation, `-Pkotlin.incremental=false` and the existing
`-Pandroid.experimental.lint.version=9.4.1` override. Both enabled
`localLoreLiteRtVerification` and `localLoreModelSetupVerification`; only the
fixture enabled `localLoreModelPickerVerification`. Each worker was owned under
the existing finite Windows Job boundary. Result classification checks actual
child status, XML/lint and audits, not wrapper exit alone.

The regular copied APP is 73,829,560 bytes, SHA-256
`49d9312f99b64707d5ecd406e06bf94a37624ec7c77519a8711264d4f4a1433c`;
TEST is 1,755,365 bytes, SHA-256
`6ea5c33f3023280ca304b30f844228760e02279e576902a3ba8d824c37569477`.
They were audited, not installed by this packet.

The installed explicit fixture APP is 73,846,072 bytes, SHA-256
`d03360e5985a5b027c4f0a476707d5c16b07e495db9812775c44b8a2fa678b00`;
TEST is 1,821,985 bytes, SHA-256
`a75b68cd99d2838ab00c41a3edec719b6ce23a7cd31681f2c544e21c2ccde1ed`.
The sealed host index covers 96 files / 151,515,480 bytes, SHA-256
`c5e9808254007fb8a67693e64ba2a81f43b2f4c20242ee42e41d25bf33a057e8`.
Independent review rehashed every entry and inspected actual XML, lint,
signatures, manifest/native inventory, supplement and terminal records.

## Actual selected emulator execution

One Android 15 / API 35 x86_64 emulator, B, with 4 KiB pages ran the following
methods in separate ordinary instrumentation invocations:

```text
am instrument -w -r -e class org.locallore.app.ModelSetupRecoveryTest#startFailuresRequireVerificationAndHoldAdmissionAcrossRecreation org.locallore.app.modelpickerverify.test/androidx.test.runner.AndroidJUnitRunner
am instrument -w -r -e class org.locallore.app.ModelSetupRecoveryTest#freshProcessRechecksHeldSessionModelWithoutImport org.locallore.app.modelpickerverify.test/androidx.test.runner.AndroidJUnitRunner
```

Each returned **1 PASS / 0 FAIL**. The first seeded the new absent fixed root
through actual native publication, then exercised actual Start, Check and
Choose controls. Before reservation, injected launch failure produced the
fixed redacted FAILED notice; a fresh full controller check was required
before retry. The second Start claimed the production guard and injected a
construction failure. Production initially showed FAILED; actual Choose then
entered SESSION_HELD without launching a document picker. Disabled control
attempts, background/foreground and a new Activity/controller in that same
process preserved the claim.

Its forced receipt records one seed import, zero UI file imports, two controller
checks, two Start callbacks, one construction attempt and zero IO violations.
The second selected method proved a different actual PID/start pair, a fresh
admission and counters, unchanged bytes/cache/fifteen older file hashes before
Activity launch, then actual READY with one controller check and zero imports,
Start calls or constructions. Direct native-store reopen and fixed proof hashes
are separate from controller check counters. The fresh receipt links the held
receipt's full SHA-256. Native model size/full hash, cache sentinel, absent stage
and older selected files were checked again. No admission reset manufactured
the process boundary.

The original outer executor reached actual terminal 0; its child completed 0
with known cleanup in 37.671 s, stdout 370 bytes and no stderr bytes. All 81
numbered client/result pairs reached known completed zero returns. Only the
own APP/TEST pair was updated, once each. After both methods passed, fresh
captured-subset checks admitted one TEST stop; no APP stop was needed. Final
observations matched all 33 expected installed hashes and all 33 UIDs; the
other 31 package hashes were unchanged. Owned/passive process counts were zero,
the real-model root was absent, and available userdata was 1,388,756,992 bytes,
above the unchanged 1,207,959,552-byte floor. Host floors also passed.

The final local index covers 268 files / 1,300,057 bytes, SHA-256
`03c18b3ee832a4aee2f021c9245029e2f72c998aff2da64abbb23a779a28635f`.
Root and independent review separately rehashed it. The original terminal,
actual selected raw outputs, both receipts and final metadata were independently
checked; the exact execution lease is closed with no follow-on authority.

## Preparation corrections and limits

No device execution failed in this packet. Before admission, independent review
found that the controller's ordinary-run parser accepted arbitrary result prose
and a noncanonical runner code. A later overly strict blank-line assumption
would have refused actual Android success. Both were corrected using retained
actual API 35 wire, with unchanged LF/CRLF fixtures, canonical status/result
checks, direct wrapper-main/exit propagation and adverse ownership/proof cases.
Passing mock/controller fixtures remain distinct from actual emulator passes.

The frozen source was `5ebb424`; 54 shared and 12 private source copies and
242 bindings matched at admission and closure. Subsequent README/contract/report
updates are post-closure documentation only. Raw identifiers, task/device output
and diagnostics remain local. The [device report](MODEL_SETUP_RECOVERY_DEVICE_2026-10-23.md)
and [independent review](MODEL_SETUP_RECOVERY_REVIEW_2026-10-23.md) record details.

This proves injected failures at the actual setup catch/admission boundary with
63 original synthetic bytes. It does not measure Android launcher failure causes,
real SDK construction or teardown, model quality/performance, physical phones,
ARM64/16 KiB execution, power-loss durability or a complete private-data byte audit.
Ordinary runner process termination and the conditional TEST stop are not
natural runtime/model cleanup evidence. No SDK, Engine, story workspace,
host UI driver, normal-launcher bootstrap, data clear or real model copy ran.
M05.04/M05.05 remain in review and unchecked; M01.01 and broader model gates remain.

Next runnable work is a candidate-owned volume-aware storage plan and reserve
admission, initially on the host. The present internal route needs 2,856,583,168
bytes including its reserve and cannot fit the observed userdata capacity.
Existing benchmark paths must not become a fallback. New storage/privacy
boundaries need explicit review, fresh volume/preservation evidence and local
copy scope before a real-model attempt. A and the retained #117/#119 runtime
holds remain separate; merged PRs do not turn failed measurements into passes.

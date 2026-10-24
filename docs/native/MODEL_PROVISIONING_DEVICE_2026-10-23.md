# Android local model provisioning verification — 2026-10-23

Refs #9 (M05.05 local provisioning prerequisite; M05.04 safe failure supporting).
This report covers the explicit debug model-setup package. It does not qualify a
production runtime, phone performance, model quality or active-model cleanup.

**Observed result: the admitted B cohort stopped after two tests passed and two
failed.** It ran once, retained the failures and made no further device call.

## Selection and boundaries

The prepared cohort selects exactly four methods in
`org.locallore.app.LocalModelProvisionInstrumentedTest`:

- `missingBuiltInModelRendersSetupAndCannotStartInference`
- `verifiedTinyCopyPublishesAtomicallyAndReopensOnAndroidFilesystem`
- `androidSymlinkCannotRedirectImportOrDeleteOutsideFixture`
- `cancelledBlockedProviderRetainsSlotUntilActualReturn`

The tests launch the candidate setup screen and use tiny, original synthetic
streams in fresh confined fixture directories. The missing-model test also
constructs the actual candidate transport on Main, reads JNI model metadata
(`configured_native_owner`, with no loaded model), borrows its workspace handle,
closes the transport, waits for handle invalidation and refuses a second process
attachment. This creates the new package's empty `workspace-v1` SQLite schema
and catalog; it creates no story and prepares no turn. The built-in model remains
absent. The selected methods do not construct an SDK Engine, initialize or
generate with a model, read model contents, access an earlier model cache, import
a real model or use original saves. Cancellation of a blocking provider retains the reservation
until actual return; cancellation is not a promise to interrupt a provider read.

The application/test IDs are `org.locallore.app.modelverify` and
`org.locallore.app.modelverify.test`. The controller admits only the previously
selected B emulator; it performs no A query. It first requires the complete
preserved 29-package map, with both new packages absent. After the signed APK
installations, the complete map must contain exactly those 29 unchanged hashes
and the new pair, for 31 packages. The original userdata floor remains
1,207,959,552 bytes, with separate `/data` identity and host storage checks.

All four paired test terminals must report PASS before the controller can inspect
test-host settlement. An absent test process requires no stop. The only optional
stop is the exact test package, with fresh process UID, installed package UID and
complete package-map ownership checks against the UID captured after the signed
installation. No application stop, uninstall, clear, reset, relaunch or model
operation is admitted. An unfinished/failed runner, uncertain client cleanup,
foreign process, changed map or storage failure stops the cohort without retries.

## Preparation evidence

The inherited controller's 47 distinct pure host fixtures passed after adapting
the selected class/methods, package namespace and 29-to-31 map counts. These
fixtures cover runner framing and terminal pairs, skips/foreign/duplicate
methods, failed results, storage identity, install framing, client cleanup and
retention failures, dynamic test-host ownership, complete package preservation
and refusal to clean up after an unfinished or failed test. They make no device
calls. The prior 29-package map was rehashed against its preserved closed index.

The first private preparation-generator invocation failed because the installed
Python's `Path.write_text` does not accept `newline`. It had created an empty
directory and no controller file. The corrected generator used explicit text
file handles; the failure receipt remains local. No device call occurred.

Final instrumentation source is 7,759 bytes with SHA-256
`efb46762fbc72083eca9e2bb36c4ed82356102808f5649e26f4a3a5e01c53e6f`.
After binding the audited final source, all 47 distinct controller fixtures
passed again. Repeated fixture execution does not increase the distinct count.
The disabled proposal binds 60 source/artifact/evidence files; its SHA-256 is
`ca5fec3f39a12c51f2152978678c7baa2ff5b22103c90d071cbdfa601f11a2ad`.

Selected application APK: 73,809,384 bytes, SHA-256
`7c9c6f38e99d2e4b8cdea787ec8ef3277db00fd6b3b966cdab910613210ca8f5`.
Selected test APK: 1,754,737 bytes, SHA-256
`7859b3e06dcb34694095915e2d54b45055b04d9f204e304e8d13d193ec95af74`.
The coordinator's actual signature/manifest/native-library audit is bound into
the proposal. It verifies the setup-only launcher and nonexported play/scripted
activities, expected runner, no Internet permission, no shared UID and exact
packaged native libraries/notices. Build/audit details belong in the coordinator's
aggregate verification report.

## Admitted execution and stop

Root and the independent reviewer each rehashed all 60 proposal bindings with
zero mismatch. Root then promoted only the two dispatch flags for exactly one B
cohort. Authorization SHA-256:
`62b7f71309db11797c48ee2500b549c62850278d2711633c9863ecf16d2abb45`.
The original owned execution reached authoritative terminal after 20,187 ms:
controller return code 2, known client cleanup, zero outer stderr bytes. A tool
observation yield did not cause a restart. Android/API/ABI/page gates observed
API 35, x86_64 and 4 KiB pages before installation and instrumentation.

All four paired start/terminal records and final runner code were present:

| Selected method | Result |
|---|---|
| `androidSymlinkCannotRedirectImportOrDeleteOutsideFixture` | PASS, with attribution limit below |
| `missingBuiltInModelRendersSetupAndCannotStartInference` | PASS, with attribution limit below |
| `cancelledBlockedProviderRetainsSlotUntilActualReturn` | FAIL: `UNSAFE_PATH` in `prepareRoot` |
| `verifiedTinyCopyPublishesAtomicallyAndReopensOnAndroidFilesystem` | FAIL: `UNSAFE_PATH` in `prepareRoot` |

Both failures reached the root canonical-path check before opening the fixture
provider or publishing a model. The observed refusal is actionable Android
filesystem evidence; successful synthetic import and cancellation are **not**
established by this cohort. The symlink test also accepts `UNSAFE_PATH`, so its
PASS alone cannot distinguish the intended file-symlink guard from an earlier
root-path refusal. The setup test's enabled Choose button is also compatible
with a fixed setup failure, so that UI assertion alone does not prove successful
missing-model classification. Its actual JNI configured-owner metadata,
borrowed-handle invalidation and second-attachment refusal assertions passed.

The controller stopped at `instrument-B`, before any test-host settlement query
or optional cleanup. All 27 dispatched clients completed with return code zero
and known cleanup. Instrumentation client success is distinct from its two
failed test results. Successful installation clients recorded stderr byte counts
174 and 196; the inherited process collector retains counts rather than their
contents, so this report assigns no cause and makes no zero-stderr claim for
those clients.

The complete before map contained the preserved 29 hashes; the installed map
contained those unchanged hashes plus the exact new APK pair, for 31 packages.
The last installed-stage userdata observation was 1,465,913,344 bytes, above the
unchanged 1,207,959,552-byte floor. After/final package maps, final storage and
post-runner process settlement were **not observed**, because the failure gate
forbids dependent calls. There was no external force-stop, retry, gate relaxation,
model operation, A query or original-save action.

## Retained evidence and next step

Raw instrumentation is 13,900 bytes, SHA-256
`27fbec0a0aac246155251d1981814d892b496478e1a582211c106f05d26371ff`.
Before source correction, all 60 bound inputs were privately copied and rehashed
with zero mismatch, preserving the exact failing sources. A separate stopped-only
local closure recorded the known terminal and intentionally missing observations;
the success-only closure was not run or weakened. The read-only stopped selection
contains 156 files / 781,775 bytes. Its 27,364-byte index has SHA-256
`a3b14b198b40138b0bfacc7d3cc4be3843402fa3212b1fc7c279938c92f51a7d`.
The device lease was released after the authoritative terminal and local seal.
Raw evidence, APKs, device identity and private paths remain local.

The next task is to investigate and correct trusted Android storage-root handling
while preserving symlink/confinement checks, add a regression that reaches the
intended guard, and obtain fresh source/artifact/controller admission for further
verification. This stopped cohort does not authorize a retry. M05.05/M05.04 remain
unchecked; real-model, second-emulator, ARM64 and physical-phone gates remain
unqualified.

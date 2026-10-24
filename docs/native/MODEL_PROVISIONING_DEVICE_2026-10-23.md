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

## Separate read-only settlement preparation

Root separately admitted a read-only metadata settlement after the stopped
instrumentation cohort. Its first wrapper failed before starting a controller
or device client: it requested a 210-second outer deadline, while the inherited
process runner accepts at most 180 seconds. The Python command exited 1 with
`invalid_process_budget`; the start receipt and all 73 inputs were preserved,
and its lease was released with zero device calls. The original settlement
authorization was consumed, with no automatic retry.

A new, separately disabled settlement controller uses the inherited 180-second
limit. Its 21 distinct pure host tests include calling the actual copied runner
with the wrapper's real request/output/deadline configuration and an already-set
cancellation signal, proving budget validation succeeds without spawning a
process. The rejected 210-second configuration is also tested against that
runner. A source-bound test executes the actual wrapper's CLI guard with an
injected failing return, verifying nonzero exit propagation. The runner's budget
guard was not changed.

The prepared settlement admits only nine fixed read-only metadata queries for
the existing B target: boot/API/ABI/page identity, process PID/UID/name, complete
31-package APK map, exact test-package UID, userdata and filesystem identity.
It preserves the original host/userdata floors and failed APK pair. It grants no
installation, instrumentation, lifecycle, model/cache/save query or cleanup
permission. It remained disabled pending fresh review; no process settlement
result was inferred from those host tests.

Root and the reviewer subsequently rehashed all 73 bindings with zero mismatch
and separately admitted exactly one read-only settlement. Its authorization
SHA-256 is `58441bfaa3016812140d5db03777536d04a1c2ed9b49c7e74f125c7b5adf728b`.
That execution completed before its first observation yield, with return code 0,
known cleanup and 2,891 ms elapsed. All nine fixed device clients completed with
return code zero, known cleanup and zero stderr bytes. No execution restart or
device mutation occurred.

This later observation found one exact test-package process with matching
process and installed-package UIDs, and no application or foreign LocalLore
process. The complete 31-package map matched the failed APK pair and all 29 prior
hashes. Userdata available was 1,465,380,864 bytes; host floors also passed. These
are separate read-only observations after the original cohort's stop, not
retroactive final checks for that failed cohort. The remaining test process was
not stopped. This settlement grants no cleanup or corrected-install permission
and does not establish natural process exit or runtime/model ownership.

All 73 bindings and nine raw client records rehashed without mismatch. The
read-only selection contains 43 files / 157,822 bytes; its 7,019-byte index has
SHA-256 `b6452b2ac6eb0f7d920c01504e46b3070bee3fcc9b38fe02ff06ab1a38103335`.
Selected files and index are read-only; the separate lease was released after
the authoritative terminal and local seal. Further device action requires fresh
root admission based on these observations.

## Separately admitted disposable test-host cleanup

Root reviewed the actual settlement and admitted a new, narrow disposable
test-host cleanup. It did not resume or weaken the original failed cohort's
all-PASS gate. The new controller required fresh process metadata, installed test
UID and complete 31-package map, then an immediate process recheck. It could stop
only the exact previously observed test PID/UID, once. Absence would skip the stop;
a changed PID/UID, application/foreign process or changed map would abort. Its 34
pure cases comprise 21 parser/budget/CLI cases and 13 specific cleanup-flow cases.

After root/reviewer rehashed the 23 bindings, authorization SHA-256
`e29293628bce4d6e05d0b1d3111f9d2edecb3e6a72fb58592ba77bbedddbfde4`
admitted one execution. It completed before the first yield, return code zero,
known cleanup and 5,437 ms elapsed. All 15 clients completed with return code
zero, known cleanup and zero stderr bytes. Fresh metadata matched the exact
captured test process and UID; the controller stopped that test package once.
Subsequent process observation found no LocalLore process, the complete
31-package APK map stayed unchanged, and userdata available was 1,465,262,080
bytes. Host floors passed. No application stop, installation, instrumentation,
model/cache/save query or A operation occurred in this cleanup cohort.

The 52-file / 130,315-byte read-only cleanup selection has an 8,326-byte index,
SHA-256 `a89a855c1594b1eca832c2f15007f4c45526fe13663f2783257d71a9518cc9ba`.
All 23 bindings and 15 raw records rehashed without mismatch; the lease was
released after the terminal and seal. This establishes the narrow observed
cleanup outcome, not native/model ownership, natural test-process exit or success
of the earlier failed tests.

A corrected source/artifact cohort was prepared separately. It proposed an
explicit update of only the same application/test pair from the
known failed 31-package map to a corrected 31-package map, preserving the other
29 hashes. Installation requests userdata retention; no bytewise audit of private
data is claimed. The original all-four-PASS-before-test-cleanup condition and all
storage gates remained. Fifty pure cases passed, including the actual process
budget and CLI exit regressions, before the separate admission below.

## Corrected cohort: new storage failure retained

The next source revision corrected trusted Android parent canonicalization and
strengthened the missing-model and symlink assertions so they could distinguish
the earlier false-positive paths. Its 8,305-byte instrumentation source has
SHA-256 `1e2b93f17f044a0f656a988ce88976e069961ee95b1a3f88d8301d16e2347713`.
Selected APKs were:

- Application: 73,809,384 bytes, SHA-256
  `24f59ee6c9d8fbb0932435989af888891c5f13df77c505f87a5fbc87da2c1fce`.
- Test: 1,755,057 bytes, SHA-256
  `44b1e3889f4cc764f2076edf666acad50e2ce6a4fc6fc3edb88698135ae58eb4`.

Root and the reviewer rehashed 59 final bindings with zero mismatch and admitted
one explicit update/cohort. Authorization SHA-256:
`1cd8549e6d8c82c5c8f7afcbdd83bc4a879c995a8796e7979a7f90389e754314`.
The original owned execution reached terminal with controller return code 2,
known cleanup and 16,312 ms elapsed; zero outer stderr bytes. Observation yield
was followed by polling the same handle, without restart.

All four paired terminals and final runner code were present. The strengthened
symlink and missing-model/UI/JNI-owner tests passed. Tiny-copy/reopen and blocked
provider cancellation failed with fixed `STORAGE` at the store's guarded boundary.
The raw result intentionally exposes no underlying private exception cause, so
this report does not identify the failing filesystem operation. Successful import
and cancellation remain unverified on Android despite the earlier host passes.

The controller stopped at `instrument-B` after 27 clients, all completed with
return code zero and known cleanup. The exact before 31-package map contained the
failed pair; the exact installed 31-package map contained the corrected pair with
the other 29 hashes unchanged. Installation used `-r`; no bytewise private-data
preservation audit is asserted. Last installed-stage userdata available was
1,389,629,440 bytes, above the original floor. After/final package maps, storage
and process settlement were not queried after the failure. There was no external
stop, repair, retry, gate relaxation, model or A operation. Install stderr counts
174/196 again have no captured content and are not assigned a cause.

Raw instrumentation is 8,691 bytes, SHA-256
`a78d85cb259d788b5042479425178e602f3ccf0b80d656ed036959f688c6ec82`.
All 59 bound inputs were privately captured before further source edits and
rehashed with zero mismatch. The read-only stopped selection contains 151 files /
805,879 bytes; its 26,511-byte index has SHA-256
`cff94f985b606a0617cb5b900cc92740db82a4e1707acb3d065c397a4762732a`.
The device lease was released after authoritative terminal and stopped-only local
closure. No success gate or success-only closure was changed.

Next: identify the Android storage operation behind the fixed failure using
bounded synthetic evidence, correct it while retaining confinement/ownership
rules, and seek new source/artifact/controller admission. Neither stopped cohort
satisfies M05.05 provisioning acceptance; real-model, second-emulator, ARM64 and
physical-phone gates remain unqualified.

## Latest-map read-only observation

Root separately admitted a new nine-query read-only settlement for the installed
corrected pair. Authorization SHA-256:
`fdf66f9b5c24d1d2e2143c9dc03ed8be9b66d16eb4ba9730d64a9e469f77dc44`.
All 72 bindings had been rehashed without mismatch, and 21 pure
parser/budget/CLI cases passed. The execution completed before its first yield:
return code zero, known cleanup, 2,985 ms elapsed. All nine clients completed with
return code zero, known cleanup and zero stderr bytes.

It observed one exact test-package process with matching installed/process UIDs,
and no application or foreign LocalLore process. The complete 31-package map
matched the corrected pair and all 29 prior hashes. Userdata available was
1,465,212,928 bytes; host floors and API/ABI/page identity passed. No cleanup or
other lifecycle, model/cache/save or A action occurred. The observation does not
qualify the failed import tests or grant mutation permission.

The read-only selection contains 35 files / 106,929 bytes. Its 5,592-byte index
has SHA-256 `9241369740d4829ef2175f60a23f89595bc91890cda2b7f635478010496e3bd2`.
All 72 bindings and nine raw records rehashed without mismatch; selected files
and index are read-only, and the lease was released after terminal and seal.
A fresh exact disposable test-host cleanup proposal is prepared but disabled;
its 34 pure fixtures passed. It requires new root review/admission before any
device action. Root's storage-operation investigation continues independently.

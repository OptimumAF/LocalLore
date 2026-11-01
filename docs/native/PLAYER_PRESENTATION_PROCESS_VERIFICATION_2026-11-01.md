# Player presentation process proof: B43 verification

Refs #314; #14 (M10.02); #13 (M09.06); #307 (supporting M09.04).
Status: implementation and host/build verification **in_review**. Full milestone
criteria remain unchecked. Actual saved-task/process-death execution is UNRUN.

## Result and source

The actual app now uses `play_presentation_v2`; the legacy process observer
intentionally counts that operation as `other`. A separate debug product,
controller and closed host evidence family now observe that read explicitly.
Legacy probe/controller/evidence-reader bytes remain identical to accepted main
`c09380d6d9ad9fd3947405355ed5b9a058300acf`.

Executed source is frozen at **`6302cb45b0a4397ee1313cc7b21e3d8cfe8f8fc8`**,
2,537 tracked raw inputs, in `D:/Worktrees/LocalLore-presentation-process-core-v1`.
This later report changes only documentation in a separate worktree; it does
not retag the APKs as built from a later report commit. Before/after execution
maps are identical, SHA256
`a9f925095e07f464f63141003dd579ef3db6f501857cae2fc753ea7cb0073902`.

The [V3 contract](PLAYER_PRESENTATION_PROCESS_V3.md) specifies the distinct
packages/cache, exact probe/result shapes, one fresh-only case, two saved-task
deaths, explicit Send, accepted conversation checks and bounded acquisition.
The controller implementation checks the exact accepted player text and the
same nonempty narrator digest/length before death, after restoration and after
reselection. These are implemented assertions, not an executed Android result.
An opt-in role tag changes only existing Text semantics; no layout or copy.
The engine remains authoritative; no canonical schema, model, dependency,
permission or inference/cancellation/resource-ownership policy was changed.

## Actually executed checks

All commands started from the physical D: checkout. TEMP/TMP and build caches
were process-local D: paths; installed tools and existing authentication stayed
in their supported locations. No system settings or global tool configuration
were changed. No SDK/ADB target discovery or device command was run.

| Check | Observed result |
|---|---|
| Focused host evidence/profile/artifact/legacy checks | 182 pass, 0 failures/errors/skips; 2.546 s |
| Additional legacy process/client/profile cohort | 258 pass, 0 failures/errors/skips; 60.469 s |
| Android JVM tests | 417 unique methods / 48 XML reports, 0 failures/errors/skips; includes six new JVM methods |
| Rust JNI | Both x86_64 and arm64-v8a release libraries cross-compiled |
| Product/test/controller | All three debug APKs compiled; new instrumentation source compiled, not executed |
| Lint | Zero errors; app one Warning/one Hint, controller two Warnings retained |
| Artifact gates | Product manifest/backup/ABI/16-KiB alignment, app/test pair+signer, self-targeted controller+one-product query all pass |

The public four-command pipeline was actually executed, not replaced by a
private Gradle task list:

```powershell
python -I -S -B scripts/check.py android --presentation-process-verification --offline
```

Its finite 900-second WindowsJob owner completed in **262,600 ms**, worker0,
known cleanup and complete output capture. Actual worker/request/started joins,
helper/tool pins and all 2,537 raw sources remain conserved. Final owner receipt
SHA256 `c77612c0e9024a32259750cab157139b763713168332ff29ba87120ed147f811`;
public child receipt `87ce3aa46157a32bb122da54c2ac1ff30ce15ff80ac44d5c71d4529b4938e518`.
Captured stdout16,198 B, stderr295 B; stderr is the controller's deprecated-API
compiler note. It is retained, not silently discarded.

Tool versions: Python3.14, Java21.0.4, Gradle8.11.1, AGP8.10.1, Kotlin2.2.21,
SDK compile/target36, Build Tools35.0.0, minSdk26, NDK29.0.14206865, Rust1.93.1.
These are build observations, not a supported-phone/runtime/model matrix.

The focused host invocation was:

```powershell
$focusedModules = @(
  'scripts.tests.test_presentation_process_build',
  'scripts.tests.test_android_presentation_process_evidence',
  'scripts.tests.test_android_process_controller_evidence',
  'scripts.tests.test_android_process_controller_creation_v2',
  'scripts.tests.test_audit_process_controller',
  'scripts.tests.test_instrumentation_apk',
  'scripts.tests.test_check',
  'scripts.tests.test_audit_physical_model_apk',
  'scripts.tests.test_audit_apk'
)
python -B -m unittest @focusedModules -q
$legacyModules = @(
  'scripts.tests.test_android_process_verification',
  'scripts.tests.test_android_process_verification_v3',
  'scripts.tests.test_android_process_client',
  'scripts.tests.test_android_process_client_v3',
  'scripts.tests.test_android_process_client_v4',
  'scripts.tests.test_android_process_client_v5',
  'scripts.tests.test_fresh_restart_profile',
  'scripts.tests.test_fixed_sdk6_profile_coexistence',
  'scripts.tests.test_closed_validation_profile',
  'scripts.tests.test_buffered_restart_profile',
  'scripts.tests.test_initial_server_profile_binding',
  'scripts.tests.test_player_presentation_ui_profile',
  'scripts.tests.test_resource_table_process',
  'scripts.tests.test_validation_profile_stats'
)
python -B -m unittest @legacyModules -q
```

## Artifact identity and independent review

| Artifact | Bytes | SHA256 |
|---|---:|---|
| Product | 28,012,692 | `9d4e8235dccd9575670e01606194489937f4abcf96e6717e7443f688caf3bc42` |
| Android test | 2,265,924 | `6dc98854829078920055e5bc4ffb223327a55bf7e3ff0fe107edb7918a26bd33` |
| Controller | 39,265 | `b4e77b813b5af1d7f8053cc36bfe150708cbea10ed22bc9fd39b44b747780508` |

Independent closed-build review rehashed source and tool maps, actual command
and owner joins, all XML results and artifact bindings. Its reader completed in
18,145 ms (direct child; no WindowsJob claim for the reader). Separately, exactly
three authorized static Java/apksigner checks returned0 with known bounded
WindowsJob cleanup; all APKs have the same single certificate
`17ed497138b20dc1657d54039802305cfe0e3b782c73feaad20359c954707564`.
No key/signing values were read by that reviewer. Review receipt SHA256
`2a7a7d25e2430bd8ac8514739a38e0a50cc73f000b49dd5a85f44d309251f5a2`.
This is closed acquisition/signature review, not another build or device run.

App lint retains GradleDependency and AutoboxingStateCreation. Controller lint
retains DataExtractionRules and MissingApplicationIcon. No warning suppression,
dependency upgrade or full privacy/release acceptance is substituted.

## Earlier failures and corrections

- The new API was initially absent: NOT_IMPLEMENTED, not a behavioral RED.
  Forty unchanged legacy controls passed; those are not added again to totals.
- Root's first19 new methods had two positive-control errors: bare-JSON decoding
  disagreed with real quiet instrumentation framing. The reader now accepts
  exactly the bounded uniform-LF/CRLF two-line finish, with no alternate format.
- Independent review found counter regression, equal-sequence forks and a
  zero-game pre-Send witness sharing a Send terminal sequence. Their joins now
  reject these graphs. The initial created receipt may legitimately precede IO;
  later witnesses establish progress without requiring an invented early read.
- The first10 artifact tests had one argv convention failure and two positive
  errors in a nested package whitelist. The fixed cache is relative to the
  already fixed Android cwd; the helper adds only the explicit new test package.
- Review found the first controller checked only head/draft. Accepted player and
  narrator comparisons were added instead of narrowing the promised journey.
- Recovery preparation refused unavailable Windows PowerShell ACL-module
  loading, including one failed clean-context probe. A fixed already installed
  working PowerShell7 executable performs the same strict read-only ACL check.
  A subsequent copy preflight refused path/descriptor full-mode comparison for
  gradlew.bat before creating a destination. Measured dev/inode/size/times/link
  identities agreed; only mode differed. The corrected reader compares type
  across APIs and full modes within each API, preserving all identity/hash/ACL
  checks. This matches [CPython's path-based Windows execute-bit handling](https://raw.githubusercontent.com/python/cpython/3.14/Modules/posixmodule.c).

Original failed outputs and versioned private recovery controls remain. No
failed run is relabeled, no task deadline increased and no target run retried.

## Preservation, limits and next task

Private evidence root:
`D:/Dev/Experiments/LocalLore/2026-11-01-presentation-process-v3`.
Selected local recovery:
`D:/Dev/Recovery/LocalLore/2026-11-01-presentation-process-v3`.
Exactly94 selected files /32,101,881 raw B are conserved as original/ZIP/after
pairs. ZIP+manifest total20,251,850 B, below the96MiB recovery budget:

- ZIP19,867,201 B SHA256 `717a864834cfb0fe96ff78ae85fef1a4a10585e41494f84f920588678a4f5f8d`.
- Manifest384,649 B SHA256 `097e54032c5659f7725bdced5b28d2ad52d2d8d5e41c7092ef7c7067a42f16b4`.
- Independent original/archive/after readback passes, direct child484ms,
  zero stdout/stderr, receipt `f030bc42a0a516ee987c05665673690663ab00d492e243764cf7fee64c10adb4`.

Recovery access is restricted to the existing user/SYSTEM/Administrators; no
ACL was changed. Originals and650,811,962 B of generated build/cache output
remain. Models, keys, guest images, global caches and older recovery archives
were not copied or removed. The incremental Git bundle requires accepted
public basec09380d6; it does not claim to be a standalone all-history backup.
The recovery mechanism's own failed controls remain in their excluded original
namespace; no recursive archive/reseal claim is made.

No instrumentation method, saved-task death, emulator/phone, real inference,
ARM64 execution, accessibility, privacy, power-loss or release gate passed in
this packet. Prior B42 emulator results retain their exact older-source scope.
M01.01/M01.02/M10.05 physical/model gates remain unverified here. No merge,
guest/ADB lifecycle, settings/access change, model copy or private upload.

Next runnable host task: a distinct fixed owner/client/verifier and one-case
controller adapter for these three APKs. Existing SDK profiles admit only
APP/TEST AndroidJUnitRunner commands and bind older archive artifacts. Add
exact controller staging/query/hash/dispatch grammar and once-only claims,
closed current-build/three-signer/raw-probe replay and known owner cleanup.
Keep old SDK defaults unchanged. The shared storage ledger and fresh exact
target authority are still required before any future preparation/boot/run.

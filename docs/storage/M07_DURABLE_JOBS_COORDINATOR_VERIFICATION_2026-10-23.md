# Schema4 durable jobs: coordinator integration, 2026-10-23

Refs #11 M07.03/.04 partial, #29 D07 prerequisite, #30/#31 platform
compatibility. This is a shared Store slice, not acceptance of production memory
consumption, the memory milestone or the desktop epic. The owner authorized
implementation and eligible merges; no settings, reviews or release authority
are manufactured. Protected chat/runtime resources were not touched.

## Source and contract

Coordinator branch `impl/m07-durable-jobs`, integration source
`5e44ea91bfa9e93ecf583e31a26937efdfa96366`, includes accepted main
`d989cf0b53ecf56223c2a9294ba260aae9f6a98a` (PR112).
The [protocol](M07_DURABLE_JOBS_2026-10-23.md),
[independent failures/review](M07_MEMORY_JOBS_REVIEW_2026-10-23.md),
[lifecycle test design/results](M07_JOB_TEST_DESIGN_2026-10-23.md), and
[capacity verification](../native/SCHEMA4_CAPACITY_VERIFICATION_2026-10-23.md)
retain their original source identities and execution attribution.

Migration004 SHA256 is
`d5b07c6b5ebb5e63a23c7171181662f2406be4c8f507b19ac94d408e840c9500`.
Schema4 adds only derived job/packet tables. Owner-bound native capabilities
expire across Store owners/reopen; persisted identity/cursor/cancellation do not.
Preparation releases its read transaction before Core construction. Publication
replays and rebuilds against a fresh exact basis/generation and commits packet
and cursor together. Context reads return actual Engine/proof from one read
snapshot, with whole-set conservative fallback for unusable cache and strict
failure for unusable canon. No packet, inspector permission or job grants a
character knowledge.

Canonical receipt bytes and workspace contract1 stay unchanged. Playable archive
formats1/2 retain their rules; format2 explicitly admits source schemas3/4 and
excludes jobs/cache. Database inspection reports actual schema4. Branch deletion
preview2 and story preview3 include exact new derived counts; Android's decoder
retains closed historical key sets and rejects missing/extra/negative/future or
overflow-inconsistent counts. Controller admission supports branch1/2 with the
existing scope/head/token/consent fences. Current durable Android startup requires
actual schema4 separately from workspace contract1.

## Actual coordinator execution

Windows11 Pro10.0.26300, Rust/Cargo1.93.1, bundled SQLite3.53.2.
Sequential Cargo processes use own D-drive targets/TEMP, jobs1, dev/test debug0,
incremental0 and locked/offline dependencies. Normal targets have no capacity
compile flags. Generated databases/logs remain local outside Git.

```powershell
cargo test -p locallore-storage --offline --locked --no-fail-fast -- --test-threads=1
cargo test -p locallore-storage --offline --locked --test derived_store --test branch_retention --test story_deletion -- --test-threads=1
cargo clippy -p locallore -p locallore-storage -p locallore-workspace -p locallore-android --all-targets --all-features --offline --locked -- -D warnings
```

| Source / execution | Actual result |
| --- | --- |
| `33e5d3e`, whole default Store |184 passed,1 failed,5 ignored; exit101. The sole failure is an old `before-v3` backup filename filter. All23 new job parent scenarios,7 independent regressions,7 migrations and the long-history baseline passed.|
| `71a6d74`, affected targets after correction/versioned previews |19 passed,0 failed/ignored (derived_store4, branch_retention7, story_deletion8); exit0. The corrected stale filter and current consent versions are exercised.|
| `71a6d74`, portable all-target/all-feature strict Clippy |PASS; exit0,30.34s. Capacity-specific follow-up has separate source/results below.|

This is not represented as one all-green whole-suite run. The five whole-suite
ignores are the explicit96-page archive qualifier, two child-only helpers
(their parent-owned interruption scenarios ran), and two Windows file-symlink
privilege cases. No OS privilege or settings change was made to remove them.
The new job cohort includes separate-owner contention, observer/branch/source
isolation, cancelled/obsolete preparation, bounded/blocked metadata, actual
SQLite Full rollback/reopened exact-boundary retry, and killed owned child
processes before/after persisted checkpoints. These are not power-loss,
physical-disk-ENOSPC or native-rendering tests.

Original cross-Store capability, historical schema3 catalog and false Complete
metadata regressions retain their actual RED evidence. Migration preflight
also retained filename/header comparison failures. The corrected backup oracle
allows only SQLite's three documented four-byte header fields to differ while
requiring every other byte, exact SQL rows, literal receipts and strict replay.
No production backup path was changed to satisfy that fixture.

Local logs under `memory-jobs-artifacts`:

| Log | SHA256 |
| --- | --- |
| storage-final-default.log |5aa8e0ad9a04fb4697b7b6e37d5ae7fb020b043d5e89b2f290d9ee65c4a77d96|
| preview-and-backup-fix.log |563684dc2a9814cef2a2c5fb8e121c016977806f4669d56b60d94a12bcbbc883|
| portable-clippy-allfeatures.log |66402fbc7255173c0046cd7bfe74cbb492fc95a32dec41925d41f33c123352f9|
| capacity-python-integration.log |f5a1d2612e88500185251abc1cc039126e9e68e81e70ee59654ad9a76fa6bfd1|
| android-normal-final.log (original failure) |5a1c942747d49104e1e2869353b7e85925292ab32bd8f926cd9efb33575bbf4b|
| android-preview-fixed.log |3df3b575dee74f7425201314935fd0b94bc6a904c687244ca3ccc084dbd090f5|
| android-apk-audit.log |a2220741ab7d3170dc6f144e8b0c0d97b3b85457ef46d7bf0d6e0c76a8cef49f|

## Android and integrated capacity checks

Ordinary Android Rust inputs equal5e44. The original build at1f23ede compiled
both JNI ABIs, main and instrumented Kotlin, then ran146 passing JVM tests and
one failure: the older controller refusal test still treated preview2 as future.
`da8df0c` changes only that mutation2→3, preserving all refusal, null-consent,
zero-commit and cancellation assertions. Original log/XML are retained locally.
An initial attempt to stage this test used a root-relative path from apps/android
and failed without staging/committing; the correct root-directory commit followed.
No check or production guard was changed by that command failure.

The following complete rerun passed in47s (14 tasks executed,64 up-to-date):

```powershell
# Existing task-local JDK/SDK/Gradle home and init script redirect outputs to D.
./gradlew.bat :app:assembleDebug :app:assembleDebugAndroidTest :app:testDebugUnitTest :app:lintDebug --offline --no-daemon --init-script <own-output-init.gradle> '-Pandroid.builder.sdkDownload=false'
python scripts/audit_apk.py <own-output>/outputs/apk/debug/app-debug.apk
```

JDK17.0.6, Gradle8.11.1, AGP8.10.1, Kotlin2.2.21, SDK36,
NDK29.0.14206865. Both x86_64 and arm64-v8a Rust release JNI builds completed
in the first run and were unchanged/up-to-date in the successful rerun.
JVM XML totals: **147 passed,0 failed/errors/skipped**. The ordinary app and
androidTest APKs packaged successfully. Lint has zero errors and one
`GradleDependency` newer-coroutines warning; no dependency was fetched or upgraded.
The pre-existing instrumented AtomicReference<Boolean> compiler warning remains.
The APK audit passed its exact ordinary package/permission/native ZIP/architecture
and16KiB ELF LOAD alignment checks for both ABIs. App APK SHA256:
`6abc149659728544abe279a2894cb726f2fc769311024139b197bced24ab903b`.
No APK was installed and no instrumented test, JNI call, emulator, ADB or device
operation ran. Compiling the real JSONObject decoder tests does not execute them.

The coordinator independently reran the capacity/helper Python suites on the
integrated source: **59 passed**,13.362s, no failures. This includes50 guards,
three actual fixed helper CLI cases and six ordinary APK-audit regressions.
The explicit isolated Python is3.14.9 (stdlib SQLite3.50.4); its path setup adds
the repository scripts/tests for imports. This rerun does not repeat the Rust
Full/relief capacity measurements or execute Android helper processes.

```powershell
python -m unittest discover -s scripts/tests -p 'test*capacity*probe.py' -v
python -m unittest discover -s scripts/tests -p test_capacity_integration_review.py -v
python -m unittest discover -s scripts/tests -p test_audit_apk.py -v
```

## Desktop frontend, native Rust and actual rendering

At3818dac (production inputs5e44), the full frontend verifier passed: normal
bundle, strict TypeScript,25 original native fixtures plus current request
builders against Rust schema, actual action/controller suites using explicitly
mocked native transport,83 timeline checks, and exclusion of test-control hooks
from the normal bundle. These are frontend/mock checks, not native UI execution.
Node24.22.1 and existing locked dependencies were used without downloads.

Native Rust checks passed: default **54 passed/0 failed/1 ignored**, dev-harness
**57 passed/0 failed/1 ignored plus2 harness-contract tests passed**, and strict
all-target/all-feature Clippy. The existing ignored model-cache reparse test
requires Windows symlink privilege; no privilege/settings change occurred.
The native metadata regression exercised supported database versions1–4 and
future5 refusal. These are native Rust tests, not rendered UI journeys.

```powershell
# From apps/desktop:
node verify-frontend.mjs
node node_modules/prettier/bin/prettier.cjs --check ui/legacy-journeys.ts legacy-harness.mjs
# From repository root, own uncapped target/TEMP, jobs1/debug0/incremental0:
cargo test --manifest-path apps/desktop/src-tauri/Cargo.toml --locked --offline -- --test-threads=1
cargo test --manifest-path apps/desktop/src-tauri/Cargo.toml --features dev-harness --locked --offline -- --test-threads=1
cargo clippy --manifest-path apps/desktop/src-tauri/Cargo.toml --all-targets --all-features --locked --offline -- -D warnings
```

Source inspection found the older fixed legacy harness still required schema2
and removed only v2 metadata when reconstructing v1. The untouched helper at
da8df0c actually failed `FixtureReadOnly` after creating that invalid synthetic
fixture (exit1); the original log and fixture are retained. `3818dac` removes
only the added derived/retention objects when reconstructing original v1,
verifies current schema via shared SCHEMA_VERSION, and updates current UI/runner
expectations to4. Canonical/receipt fixtures and read-only/one-backup oracles are
unchanged. A source-search invocation using wildcard path arguments also failed
with Windows OS123; later directory searches completed. It is not a test result.

The actual application-owned native runner at clean source
`f955ac5375cf590dcd162df331a93c878898fc5a` then passed **29 assertions,8 WebView2
captures,two app processes with a real process restart**:

```powershell
# Existing task-local Node, own artifact root and own native target:
node legacy-harness.mjs
```

This uses the actual frontend controller, native IPC, shared Host and SQLite,
then captures only its own invisible/unfocused WebView via CapturePreview.
It does not capture/control the desktop, inject input, activate windows or
operate unrelated apps. The fixture is reconstructed synthetic v1, not an
actual released-app historical save. No model is loaded or called.

Both processes resumed quay/main at revision1 with the original spent potion,
one exact old-key receipt, actual SQLite schema4/workspace contract1/domain-v1
labels and one unchanged read-only v1 backup. Exact retry/status and replay
preserved projection SHA256
`464abab4ac43ae8087657a524eeb09a32f5ca8d3c41ae58529e145b371166c87`
and receipt SHA256
`f1eee1ba28217d019f87e5c144e985f6a5462b7c638e739c6884052bffdb6b6f`.
Mira's witnessed gift remains visible without player messages; uninvolved Sable
sees zero history rows. Inspector browsing leaves canon unchanged. Each close
reports zero owned Host sessions/generation workers. Frontend error buffers are
empty in both runs. Two Chromium unregister-class error1412 stderr lines remain
in the bounded local log; they are not suppressed or counted as zero native
stderr. The own profile's Last Version records WebView155.0.4283.62; this is not
an independent loaded-module inventory.

Coordinator inspected all8 render images at1280×900: selected story/head,
receipt, spent inventory, real current storage labels, distinct Mira/Sable
inspection state and fake-provider/saved-locally notices agree with semantic
snapshots. No overlap, clipped primary state or horizontal overflow was found.
The inspection captures deliberately scroll to the read-only table. Narrow
layout and new-job maintenance UI were not exercised by this legacy cohort.

Local output directory: `memory-jobs-artifacts/native-render/legacy-native-f0ac5926-65d3-4ac0-aea6-e3842188c425`.
Summary SHA256 `dff682cacdca6ad571300a364f4106d2f65f63a80c43dde2edd2a845d1374958`.
All synthetic databases, raw logs, profiles, semantic snapshots and images remain
local outside Git. No public/private user data was added to repository artifacts.

| Additional local log | SHA256 |
| --- | --- |
| frontend-check.log |3f3859331b8256f3acb797af9d7978bf631c818249d5a52ea6cb774432da176e|
| desktop-native-default.log |23519c7ddcfec1815b28fcae551aa93461f3368204863299ce343a962174addc|
| desktop-native-dev.log |c2fcc10578b0546f53cbfc219b3bd0c4d40b61c62630db50ddcf8fdaf2e87260|
| legacy-original-red.log |74be933522f4e39e893531eea3107dcb5ad78aece00c697564542d6069baa021|
| legacy-native-current.log |068b08ffd0b1d5a2e4ef95e1e098ae36ad88586df18f024160b5dfc8165948bc|

## Separate capacity qualification and remaining work

Schema3 physical profiles were not relabeled. The independently authored
[measurement](../native/SCHEMA4_CAPACITY_MEASUREMENT_2026-10-23.md) observed
Ready23 pages/accepted24 before freezing Full23 and relief32 profiles. Actual
relief measured8 owned padding rows, attempt9 Full and9 freed pages; the original
14/15 oracle failed before the new counts were frozen. Profile format3/schema4,
v4 package/cache namespaces and exact schema digest are distinct from unchanged
Host/helper wire2. The final packet runs actual Host accept/cancel/exact-retry
and five bounded helper faults; its own source/log hashes and59 Python checks
are attributed to the contributor, not a new coordinator rerun.

No scheduler, Host/Play verified consumer, new prompt/provenance version, model
comparison, Android device run, physical phone or release qualification follows
from this change. Next is the native same-snapshot Host port and production
Play integration using the already accepted Core verifier/compiler, followed by
the separately frozen comparison and remaining desktop gates.

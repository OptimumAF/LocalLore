# Synthetic Windows–Android archive proof — 2026-10-23

M08.06 / supplemental D08.06, implemented and locally verified for review.
[Claim](https://github.com/OptimumAF/LocalLore/issues/12#issuecomment-6362716633).
This followup depends on **open, unmerged [PR #76](https://github.com/OptimumAF/LocalLore/pull/76)**,
parent `6e9b2dc66ea86890a2afcfec02b01b4e8e90df24`, accepted main `a2bb6639`.
No merge, release, full milestone acceptance or production runtime decision.

## What the executable proof does

The [frozen contract](PLATFORM_ROUNDTRIP_CONTRACT.md) uses the unchanged shared
archive v1, real Rust Store/Engine, existing Host/fake provider and seven-call
Android JNI owner. No shared gameplay/persistence API, schema, runtime or
third-party dependency pin changed. The native development example requires an
explicit fixture flag and exclusively creates new output directories. The
Python runner requires already installed isolated app/test APK hashes to match
the supplied artifacts and refuses mismatched packaged fixture bytes. It never
installs, clears app data, downloads a model or deletes evidence.

1. Windows generates an original three-branch Lantern Quay story. Root gives
   its potion to Mira after the fork; child consumes its own inherited potion;
   sibling privately speaks to Mira. Root/child/sibling heads are each 2, with
   four original local receipts. A source pending draft is excluded from export.
2. Android imports, closes/reopens and exports byte-identical Windows history.
   All three actual player snapshots match the engine-derived golden, including
   original receipt scopes, inventory and transcript. Non-Lab NPC/omniscient
   inspection remains Forbidden. Android commits the sibling's gift; exact
   committed retry is inert and a new-key duplicate spend rejects as Inventory.
   Its entire continued archive equals the independently generated Windows one.
3. Android independently creates a real Host-owned synthetic story with its
   normal random ID, commits a gift, retries, reopens and exports it. Windows
   validates/imports/reopens, reconstructs an independent expected Engine from
   the known fixture seed with that story ID, and compares canonical bytes,
   receipts and player/Mira/Sable/Oren contexts. Hidden, future and sibling
   knowledge canaries retain their boundaries. An unrelated control story is
   preserved in every Windows destination.
4. Windows continues with a wait, exports back to Android; Android imports and
   reopens exact bytes, retries the original Windows receipt without mutation,
   rejects another potion spend and commits another wait. Windows compares the
   final archive byte-for-byte to an independent expected continuation, then
   validates/imports/reopens/replays it again. No model is called for replay.

This is a **headless Windows native engine/Store fixture**, not desktop application
UI. Android executes actual JNI against SQLite; its transfer test does not open
a system chooser. The root catalog has one row per story; all three branch heads
and snapshots are checked separately. Kotlin presents and compares JSON; Rust
alone validates and commits accepted state.

## Actual checks and exact attribution

| Check | Observed result |
|---|---|
| `python scripts/check.py host --offline`, latest source | Pass: fmt, strict workspace Clippy, **308 Rust + 3 linker + 206 Python**; existing Android fixture drift check |
| Native fixture tests, included in workspace count | **8 pass**, including real Windows ancestor-junction refusal and exact engine-to-packaged-asset drift check |
| Original Python orchestration faults, included in Python count | **15 pass**, covering false/missing/duplicate/failed terminals, collisions, drift, ownership and combined unknown cleanup/raw-write failure |
| Isolated Android assemble/assembleAndroidTest/JVM/lint | Pass, 60 JVM / 0 fail/error/skip; final build 79 tasks, 4 executed/75 up-to-date |
| `python scripts/check.py android --offline` | Pass, 78 tasks, 33 executed/45 up-to-date; 60 JVM; lint 0 errors/1 existing dependency warning; production APK audit |
| Both native ABI audits | x86_64 + arm64-v8a build, 16 KiB ELF/ZIP alignment, seven NativeArchive symbols each; expected receiver-only permission; no test provider or platform fixture assets in app APK |
| Latest frozen-binary cycles on A and B | **4 Android phase tests pass**, zero failed/skipped/unfinished; **4 Windows CLI verification invocations pass**, all process/client cleanup and protected-package guards pass |

Final code/test source is `f448dce9ebf7d60c741d956c7d036314538c8c58`.
Its fresh create-only native executable snapshot hashes to
`e335ecd7fdbb1d4518a724e60afbe44976c5949cf454969a0a8807198cbffc6a`.
The app/test APK pair is respectively
`5a058eef62d1e56e9326ac71a959bd1205ae9a96820b42626abda6530e93944f` /
`b3f45ecee08acb3482874549fb773c29843bd0c5b10d76fda9c84001736acf8a`.
Android test and runner sources are unchanged from `a9d3274`; the last source
change adds only the native fixture's CI drift test. Subsequent commits record
docs/review only. Exact artifact/source hashes and all six cycles are in
[structured results](PLATFORM_ROUNDTRIP_RESULTS_2026-10-23.json).

All six cycles passed: initial A/B before the native ancestor correction,
reviewed-source A/B at `a9d3274`, and latest frozen-binary A/B after the CI test.
There are **12 actual Android phase passes and 12 Windows CLI verifications**
across all attempts. These are separate retained cycles, not 12 unique tests.
Each cycle has 74 completed command-journal records with confirmed cleanup.
The golden archives/manifest remain exactly 7,064 / 7,890 / 18,291 bytes across
all generation checkpoints. Different Android-origin random IDs legitimately
produce different per-cycle hashes; comparison always uses that cycle's source.

Observed environment: Windows x64; Rust 1.93.1, Java 17.0.6, Gradle 8.11.1,
AGP 8.10.1, Kotlin 2.2.21, NDK 29.0.14206865; selected A/B Android 15/API35,
x86_64. Fresh inventory found four emulators, zero authorized physical phones.
Separate guarded provisioning updated only the previously owned archiveverify
test pair, preserving its data and all other known app/runtime identities.
The runner's per-cycle `installed_apks=false` describes the runner, not absence
of that separate provisioning. No default workspace was reset or uninstalled.
Raw logs/SQLite files stay private; only original fixtures, hashes and aggregate
categories are published. Read the [independent review](PLATFORM_ROUNDTRIP_REVIEW_2026-10-23.md).

## Failures and corrections retained

- Native author's first six-case suite had two failures: inherited receipts
  were incorrectly retried through a child session. After scope correction,
  one duplicate-spend fixture reused a rejected key at a different head and got
  RetryMismatch. Distinct keys per head fixed that assumption. Final native
  checks pass; these were fixture defects, not relaxed engine rules.
- Independent review found an earlier linked ancestor could evade immediate
  directory checks. The author demonstrated the failure with a real Windows
  junction, added all-ancestor guards and verified the external synthetic
  sentinel remained unchanged. Initial cmd/mklink setup attempts failed before
  fixture execution; fixed PowerShell junction creation succeeded without elevation.
- Source review corrected the initial one-row-per-branch catalog assumption,
  strengthened native result binding to exact fixture/mode/integer version, and
  moved native cleanup-state publication before fallible raw persistence. The
  combined unknown-cleanup/write-failure fault test proves no later device
  dispatch. These source findings are distinct from executed old-code failures.
- The first Python test run counted five inherited cases twice; that duplication
  was removed. The final 15 cases are unique. No device failure is hidden by this.
- After the CI-only drift case was added, a strict binary-identity assertion
  failed: the rebuilt executable differed from the previous `984a…` artifact.
  No equivalence was inferred. A fresh executable snapshot was hashed and both
  complete cycles rerun successfully with that exact new `e335…` binary.

## Reproduction and limits

Run the normal host checks, then generate small original fixture files in a new
directory (the parent must exist):

```powershell
cargo +1.93.1 run -p locallore-android --example platform_roundtrip --locked --offline -- --development-fixtures generate --directory target/platform-fixtures-NEW
```

Build the isolated APKs using the [archive instructions](ANDROID_ARCHIVE_VERIFICATION_2026-10-23.md).
Explicitly install them only into separately owned authorized test AVDs. Freeze
a fresh copy of the built native fixture executable; do not rebuild that file
during a proof. From the repository root, supply the selected device and paths:

```powershell
python scripts/platform_roundtrip.py --serial <authorized-test-device> --alias A --adb <sdk-adb> --app-apk <archiveverify-app.apk> --test-apk <archiveverify-test.apk> --fixture-executable <frozen-platform_roundtrip.exe> --fixtures target/platform-fixtures-NEW --output-directory target/platform-proof-NEW
```

The runner writes private raw evidence and aggregate `result.json`, rejects an
existing output, and requires exact packaged fixture bytes. `--owned-stdin` is
the native process owner's EOF handshake. Unknown process/client cleanup stops
dependent work; it is never inferred from a successful ADB exit. Fixture files
are bounded to 128 KiB for this proof, without changing production's 32 MiB cap.

No system-chooser transfer loop, desktop app UI roundtrip, guarded free-text Play
metadata roundtrip, archive-specific process-death/disk-full product qualification,
ARM64 execution, phone performance or real-model quality is established. Injected
runner disk-write faults are not actual device storage-exhaustion measurements.
No hosted CI execution or full M08/D08 acceptance is inferred. Next runnable
M08.06 work is the selected-document chooser export/import roundtrip and failure UX.

# Retention integration with current desktop — 2026-10-23

Coordinator `/root`, claims #85 6370135642 / #12 6370136068 / #8 6370136488.
Original #85 head `a1b1cc97639860bccf1d92253c9bcfe286d15809` is preserved, with
accepted main through #99 reconciled by normal merge commits. Final executed
native source: `8205c13125758d20ff8393d662298580a86b0f02`; subsequent diagnosis
documentation `02d2b82` changes no production bytes. Status: in_review partial
M08.05/supporting M08.01/.04/.06 and shared migration recovery, not full D08/M08.

The original author/independent-review/device cohorts remain separately attributed
in their dated reports. This coordinator operated no device, emulator, ADB,
protected checkout/chat/process, model or desktop controls. Independent integration
review and new executable adversarial cases are in
[the review report](PARENT_RETENTION_INTEGRATION_REVIEW_2026-10-23.md).

## Integration fixes and boundaries

Preserved accepted strict cache operations in their canonical snapshot and the
pinned main/journal/WAL/SHM disposable Store reservations. Schema 3 exclusively
adds retained-parent tombstones and its backed-up exact migration; it is not a
competing desktop persistence layer. Shared retained-history and archive/catalog
rules remain authoritative for desktop and Android.

Incoming branch invalidation and cross-owner NotFound removal predated private
capture retirement. Two new Host tests actually failed at `311a707`: removed
owners remained live. The integration retires matching owners before removing
sessions/cancelling turns, releases gameplay state before best-effort `try_lock`
trace cleanup and preserves unrelated/surviving child owners. Cleanup recovers
poison only to narrow access; poison remains set and grants no gameplay. A third
unit covers busy trace plus poisoned state. No blocking diagnostic lock can hold
the retirement transaction's subsequent native invalidation hostage.

Independent regression `f32b85a` demonstrated a second conflict: accepted capture
revocation inherited the new `get_session` SQLite admission read and failed
Database when storage was unavailable. Fix `db1294e` resolves only the exact
in-memory session/scope owner for revocation. Ordinary access still performs
public Store admission and fails closed; wrong-scope revoke rejects. The unchanged
review test passes, and the existing unit now panics if revoke calls even
`validate_scope`. Revocation grants neither inspection nor generation authority.

Desktop archive capability now advertises current version 2 and supported [1,2].
The preview decoder accepts v1 without a retirement field, or v2 with nonempty,
bounded, sorted unique valid IDs, no retired root and physical/reserved union
within 256. Physical branches remain capped at 32. Preview displays actual
version, playable versus retained ancestry and reserved tombstones. Collected
IDs need not have physical rows. Unknown versions are refused; the existing
future fixture is now truly unsupported version 3. No checksum authenticity or
resurrection resistance against deliberately rewritten/rechecksummed archives
is claimed.

A new actual native broker/Store test captures a v2 retired-parent archive,
previews it, imports through real isolated staging into another Store, preserves
the live grandchild's exact canonical bytes, refuses the retired parent and
re-exports exact bytes. Controller/React v2 disclosure checks use native doubles.
The actual native UI journey below still transfers v1, so a v2 UI end-to-end or
desktop↔Android transfer is not inferred from those renders.

## Coordinator checks

Windows 10.0.26300; Rust/Cargo 1.93.1; Node 24.22.1/npm 11.19.1;
Python 3.14.9. Android JDK 17.0.6/Gradle 8.11.1/AGP 8.10.1/Kotlin 2.2.21,
SDK 36/NDK 29.0.14206865. Dedicated D-drive build outputs and fresh task TEMP/TMP;
Rust DEV/TEST debug=0, incremental=0, locked/offline. Installed WebView2 includes
155.0.4283.62; selected loader binary path was not independently recorded.

```text
cargo +1.93.1 test --workspace --all-features --locked --offline --target-dir <m07-context>
452 passed / 0 failed / 4 existing qualification ignores
python scripts/check.py host --offline
441 workspace + 3 native-linker Rust passes / 4 ignores; 352 Python passes;
4 Android fixture bindings; fmt and strict default workspace Clippy PASS
cargo +1.93.1 clippy --workspace --all-targets --all-features --locked --offline --target-dir <m07-context> -- -D warnings
PASS
```

The all-feature cohort used `db1294e`; later source changes are review assertion
lint, native-only import/test lint, test bootstrap, docs and accepted packaging
scripts. Final full host runner used clean `8205c13`; all-feature strict Clippy
passed after the review assertion lint correction. No canonical/runtime budget
or safety assertion was relaxed.

Native commands use `--manifest-path apps/desktop/src-tauri/Cargo.toml`,
`--locked --offline --target-dir <archive-ui-native>`:

```text
cargo +1.93.1 test ... --all-targets
46 default passes / 0 failed / 1 existing privilege-dependent ignore
cargo +1.93.1 test ... --all-targets --features dev-harness -- --test-threads=1
48 module + 2 harness-contract passes / 0 failed / 1 same ignore
cargo +1.93.1 clippy ... --all-targets -- -D warnings
cargo +1.93.1 clippy ... --all-targets --features dev-harness -- -D warnings
both PASS
```

Frontend verifier, Prettier, root/native rustfmt and diff checks pass. Final normal
frontend/native build passes; private synthetic provider/picker markers are absent
from the normal executable. Static/controller/headless tests are separate from
native module/IPC tests and actual WebView rendering.

Android, in `apps/android`, with an init script redirecting all outputs into
fresh dedicated `android-retention-build`:

```text
java -classpath gradle/wrapper/gradle-wrapper.jar org.gradle.wrapper.GradleWrapperMain -I <android-retention-output.gradle> :app:assembleDebug :app:assembleDebugAndroidTest :app:testDebugUnitTest :app:lintDebug --offline --no-daemon --console=plain -Pandroid.builder.sdkDownload=false
python ../../scripts/audit_apk.py <android-retention-build>/_app/outputs/apk/debug/app-debug.apk
PASS: both JNI ABIs, both APKs, 146 JVM tests / 0 failures/errors/skips, lint, APK audit
BUILD SUCCESSFUL in 4m24s; 78 tasks, all 78 executed
```

Android began at `db1294e`; exact diff confirms Core/Store/workspace/JNI/Android
production bytes are unchanged through `8205c13`. This is build/JVM evidence,
not new device execution. Original author emulator evidence is not relabelled.

## Actual application-owned native renders

From `apps/desktop` with task-owned artifact/target environment variables defined
in the harness instructions:

```text
node archive-harness.mjs
63 distinct assertions / 17 PNGs / 5 actual process launches: PASS
node capture-harness.mjs
73 distinct assertions / 15 PNGs / 2 actual process launches: PASS
```

Both summaries bind clean `8205c13` and actual process restart. Archive covers
v1 export/import/re-export, conflict, cancellation after staging, lost acknowledgement,
retirement/reopen of a window, privacy and exact-key recovery. Capture uses fixed
synthetic inference through production Play, actual controller/native IPC and
fixed post-selection picker doubles, with exact saved-preview verification.
Neither is a real-model run, desktop screenshot/input/window activation or
automation of a system dialog.

Local cohorts under `retention-native-artifacts`:

- `archive-native-86dbcef3-c729-4bb2-8177-5baf6e93da37`, summary SHA256
  `90d81cec3bcb31b9ab573851d211d11b61b0a89137a1012f76ac57fb7c916422`.
- `capture-native-7f923897-b8bd-4520-a5f4-93976925e400`, summary SHA256
  `8ae596936b9a6885641569fc111c39994a6affa908ebad28c8b8bb05f80d8196`.

Coordinator inspected archive pending/conflict/narrow preview and capture opened
export/restart renders: readable labels, coherent revision/receipt/error/pending
state, no clipping observed. Capture reports exact saved bytes; its expected
bounded native Agency/Cancelled errors remain explicit. Archive accepts only
expected Cancelled native error records. Chromium class-unregistration 1412 exit
lines remain in logs; reports/render assertions pass.

## Retained failures and remaining gates

All local logs/raw synthetic artifacts remain outside Git. Root failures retained:
two owner-liveness regressions before fix; native import used the wrong public
constant path (corrected to `playable_archive::ARCHIVE_VERSION`); review-test
cloned-ref lint and old native version-pattern lint (narrow syntax fixes).
An initial dev serial suite had 47 passes/1 failure/1 ignore: the unchanged
evaluation boundary test exceeded its existing polling limit during concurrent
builds. Exact focused rerun and full serial rerun passed with no deadline/source
change. Scheduling sensitivity is observed; exact cause is not proved.

The first full host runner failed an existing synthetic Python watchdog child
before job creation: embedded Python's isolated import path omitted its cwd.
The separate test-only fix passes its trusted module directory explicitly and
adds bounded child-error diagnostics. Original deadlines, job finally and safety
assertions remain. Exact test/full 140 benchmark checks and final full host runner
pass. [Diagnosis](PYTHON_ISOLATED_PROCESS_TEST_DIAGNOSIS_2026-10-23.md) retains
stderr/source equality with accepted baseline; no retention/job-product defect
is inferred from that setup failure.

Full D08 still needs timeline creation/correction UX and actual desktop↔Android
transfer/parity qualification. Legacy capacity helpers require the separate
#87 then #94 schema-3 packets before qualification. No phone/ARM64 execution,
model quality, maximum-history performance, forensic erasure, public release,
repository setting change or fabricated human review is claimed. M07 jobs must
take the next accepted schema version; schema 3 is occupied here.

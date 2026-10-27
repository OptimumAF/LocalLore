# Scoped Android draft restoration — 2026-10-25

M05.05 supporting lifecycle work; M09.03 preparation. **In review**, with full
milestone criteria and owner acceptance still pending. Base: accepted main
`97d1f670`. Production fix: `7c7c5730`; final executed source: `f9624009`
(an instrumentation expectation correction only). No merge or release.

## Behavior and boundaries

The saved-story composer keeps one unsent Action/Dialogue draft through Android
saved-instance state. Its exact story/branch identity is checked against the
resolved native snapshot. An unresolved opening/recovery hides the pending text;
a different settled scope clears it. A new revision in the same scope retains
it. A→B→A does not recover a per-story draft map. Restoration never submits a
turn, resumes generation, chooses a story, or changes canonical history.

The closed v1 saver stores six primitive fields: version, story, branch, kind,
text and `full`/`omitted`. It bounds text to 8192 UTF-8 bytes and each identity to
128 bytes, with enum/version/list overhead in addition. This is not a limit on
the entire Activity Bundle. Oversized or Unicode-invalid live text is omitted
whole on saving; a restored notice persists until an explicit matching edit.
The live editor is not truncated. Send retains its existing 2048-byte, Unicode
and control-character checks. Unscoped demo text is not saved by this record.

Compose controllers are keyed by scope, while the saved draft and latest-scope
fences live outside that key. Old edit/send callbacks cannot retarget another
scope. The production `onText` callback also supplies its rendered story to a
ViewModel identity check before the existing submission path. Revision changes
are deliberately excluded from draft identity. Kotlin adds no gameplay rule or
alternative authority; Rust still validates and commits every accepted outcome.

The implementation uses the existing locked Compose runtime-saveable 1.8.2 /
BOM 2025.05.01; no dependency or SDK/runtime/model selection changes. Android's
[state-saving guidance](https://developer.android.com/develop/ui/compose/state-saving)
describes transient saved UI state and bounded custom savers. Saved-instance
data can outlive the app process under OS management; it is not an encrypted
story store. Force-stop, task dismissal and ordinary cold-launch retention are
not promised. A cold native initialization that settles on another story also
clears the pending draft. See the [privacy boundary](../PRIVACY_AND_THREAT_MODEL.md).

## Reproduce the isolated checks

Use the existing pinned Java/SDK/NDK/Rust installation and cached dependencies.
From `apps/android`, with task-local Java/SDK environment variables:

```powershell
.\gradlew.bat :app:testDebugUnitTest :app:lintDebug :app:assembleDebug :app:assembleDebugAndroidTest --offline --no-daemon --console=plain --max-workers=2 --project-cache-dir .gradle-input-draft -PlocalLoreInputDraftVerification=true -Pkotlin.incremental=false -Pandroid.builder.sdkDownload=false -Porg.gradle.java.installations.auto-download=false
```

This selects only debug `.draftverify`, `app/build-input-draft`, and its exclusive
cache. Release, false-valued flags, mixed verification/capacity modes and wrong
caches are refused. The actual five negative configure cases also ran and failed
for their expected reasons. Existing app installations and caches are separate.

From the repository root, with the SDK configured for auditing:

```powershell
python scripts/audit_apk.py apps/android/app/build-input-draft/outputs/apk/debug/app-debug.apk --input-draft-verification
python -m unittest discover -s scripts/tests -p test_audit_apk.py -v
```

Install the signed app/test pair only on a selected, authorized emulator with
verified identity and available space. Do not use an unspecified default target.
The installed target is `org.locallore.app.draftverify`; runner is
`org.locallore.app.draftverify.test/androidx.test.runner.AndroidJUnitRunner`.
Run these classes individually using `am instrument -w -r -e class`:

- `org.locallore.app.PlayDraftRestorationTest`
- `org.locallore.app.PlayDraftActivityTest`
- `org.locallore.app.PlayInputScreenTest`
- `org.locallore.app.ShellInstrumentedTest`

ADB exit zero alone is insufficient. Verify each complete method roster, passing
status pairs, final `OK`, and absence of failures/skips. Actual execution used
bounded Windows Job owners, a pinned existing ADB-server identity, an exact
owned emulator/transport, package UIDs and installed APK hashes. No unowned
package or model cache was adopted. Each instrumentation client retained the
existing 180-second limit; classes were separate clients, not a larger generic
process-budget exception.

## Actual verification

Windows x64; Rust 1.93.1, Java 21 build host, existing Android toolchain. The fresh
API35 Google APIs x86_64 emulator used 2 GiB / two CPUs and 4 KiB guest pages.
It was a **scripted UI** target, not a model-support profile. Its new private C:
backings used a task-specific admission budget: 4 GiB available physical memory,
2 GiB guest commit plus 2 GiB reserve, C:64 GiB / D:16 GiB free. No existing AVD
configuration, host setting or other project's emulator was changed. No weights
were copied, downloaded or loaded.

| Check | Actual result |
| --- | --- |
| Initial `8c85a670` full Android build | Owner 328,724 ms/0, known cleanup/capture; all 81 tasks executed; 501 unchanged source hashes. 226 JVM tests / 26 classes, zero failures/errors/skips. Both JNI ABIs and signed pair built. |
| Production scope-key fix `7c7c5730` | Owner 121,706 ms/0, known cleanup/capture, 501 stable sources. JVM test task actually reruns all 226; lint passes with zero errors/one warning. Unchanged native/test compilation may be UP-TO-DATE. |
| Test-only final `f9624009` build | Owner 71,944 ms/0, known cleanup/capture, 501 stable sources; 7 tasks executed/74 UP-TO-DATE. Android test source recompiles; prior JVM/native results are retained, not claimed rerun. |
| Artifact audits | Final owner 1,632 ms/0, known cleanup/capture. Exact package/signature permission, backup disabled, runner target, matching signing, native ABI/16 KiB alignment checks pass. |
| Audit Python regressions | 27 pass / 3.533 s; source unchanged. Includes exact-package/permission rejection and mixed SDK-profile refusal before artifact reads. |
| Invalid Gradle profiles | Five expected refusals; owner 47,970 ms/0, known cleanup/capture, source unchanged. |
| Final device gate | **15 pass, zero failure/skip**; owner 178,920 ms/0, known cleanup/capture, all 501 source hashes unchanged. All 73 captured host clients complete/0/known cleanup/zero stderr with stable ADB-server identity. |
| Owned emulator stop | After passing checks: `stop_requested`, 1,767,033 ms/worker 1, known cleanup/capture; global registry/token observations unchanged. No guest-flush claim. |

The final device roster is six saved-state simulation methods (26.308 s), one
actual product Activity method (6.173 s), two existing text-play methods
(10.267 s), and six existing shell methods (17.3 s). The Activity test uses the
real product factory, retained ViewModel/transport, and native reconciliation:
no automatic commit before explicit Send; one accepted dialogue survives another
recreation without resubmission. The existing methods cover actual JNI/SQLite
rejection, cancellation, stale completion, disposal and saved-state behavior.

Final signed app: 24,536,463 bytes,
SHA256 `f2a19a1f3c1065eb4089176ab580da01416d5626e2b8cf626fdc16fe76db1c75`.
Test APK: 2,623,804 bytes,
SHA256 `42fbc11ae1253b1b711c2310d0a35befbdd31679e88d03dabf513f18ca5a1e41`.
APKs and unit/lint records are separately retained privately. The only new runtime
record is transient UI data; canonical receipts, requests and replay are unchanged.

## Retained failures and corrections

The first actual six-method Compose run at `8c85a670` passes five and fails the
retained-action case (26.74 s): B's editor contains the stale A payload. A value
guard alone did not suffice because Compose's reused field/controller could
dispatch its old semantics action to the latest callback. `7c7c5730` keys the
controller subtree by scope. The **unchanged** six-method oracle then passes
(33.667 s), followed by the final six-method pass above. Independent source and
raw RED/GREEN readback: [closure](https://github.com/OptimumAF/LocalLore/issues/9#issuecomment-6408363090).

That intermediate run also passes Activity1 and text-play2, but the broader shell
suite passes five/fails one because its old permission assertion hardcodes the
ordinary package. The isolated APK correctly requests its own signature
permission. `f9624009` changes only that existing test's expected namespace;
the singleton and signature-protection checks remain. The complete final
15-method run passes. Neither partial run is credited as an overall pass.

Earlier private helper failures remain retained: aapt emits literal `false`,
rather than the assumed typed-hex backup spelling; the console name command
requires `-s` rather than `-t` with several emulators; its uniform CRCRLF framing
must be parsed without inventing empty identity rows; and an oversized requested
client deadline is refused before instrumentation starts. These affected no
production source. APK installation from that pre-test refusal was resumed only
after its known-clean handoff, exact UIDs, guest APK hashes and signing checks;
subsequent updates replace only the same owned test pair. A supplementary host
console diagnostic is error reproduction only, not target-identity evidence.

## Limits and evidence scope

This packet executes one emulator, not both historical targets or a physical
phone. ARM64 is built/packaged, not executed here. StateRestorationTester simulates
saved-instance restoration; Activity recreation is actual; **actual process-death
restoration is not tested**. No real inference, prose-quality, thermal, memory
pressure, phone performance, 16 KiB device or production-backend acceptance follows.
The selected phone was absent at bounded discovery during this packet: owner
6,021 ms/expected worker 2, known cleanup/capture, unchanged source, zero target calls.

The APK audit checks the closed native-library set and manifest/signing rules;
it does not prove artifact-wide absence of SDK Java/DEX classes. Candidate source
and dependencies are excluded by the selected Gradle configuration. No dependency
inventory or general privacy/host-authenticity audit is claimed.

Selected private index: **741 files / 1,948,944 bytes**, 23 explicit groups;
SHA256 `4a3ad2e8715a212ccecff4551126ee79877408f1dfad65b95be92f40ab97ac0c`.
It includes retained successes, failures, source-owner maps, raw client bindings,
test/lint records and execution-driver copies. APKs are retained separately;
weights, guest/system images, compiled caches, other-project data and prior
packets are excluded. Private stories, identifiers, diagnostics and binaries are
not uploaded. Full M05/M09 tasks remain unchecked. Next: qualify actual OS process
restoration on an authorized device, and resume physical-model admission after
the selected phone reconnects; model/human-quality gates remain independent.

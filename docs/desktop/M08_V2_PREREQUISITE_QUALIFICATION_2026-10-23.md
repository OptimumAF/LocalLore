# M08 V2 consumer prerequisite qualification

2026-10-23 local date; the final recorded checks ended on 2026-10-24 UTC.
Partial evidence for #12 M08.03 / #30 D08.05 and the desktop consumer
prerequisites. This report consolidates Root's completed local qualification;
the report author performed source, log, metadata and hash inspection only.
It is not human acceptance, a milestone completion claim or a release gate.

The qualified prerequisite tree provides thin native Play snapshots, scoped
Query2 transcript identity and player-only author interval markers, strict
desktop V2 decoding, a native Host/Repository author port, and a native author
broker tested through actual Store/Host fixtures. **The author broker remains
test-only in this tree. No author Tauri IPC, author UI, Android D2 consumer,
native WebView journey or render capture is qualified here.**

## Scope and source attribution

The report is the sole new path on `docs/m08-v2-prerequisite-qualification`,
based on `96c4bdcc86f0a7f6e3e21c531ce873aa3dc3078f` from the coordinator's
desktop memory integration track. Claims were posted before writing:
[#12 6379299954](https://github.com/OptimumAF/LocalLore/issues/12#issuecomment-6379299954)
and [#30 6379300087](https://github.com/OptimumAF/LocalLore/issues/30#issuecomment-6379300087).
No production, test, generated schema or existing evidence file is changed by
this report. Ticket comments retain current task status and owner acceptance.

This is a follow-on to accepted foundation PR #131, merged as `2a9a5e6`.
The [foundation qualification](../storage/M08_FINAL_FOUNDATION_QUALIFICATION_2026-10-23.md)
has its own source-bound app/model/legacy evidence. Those earlier render and
model runs are not relabeled as execution of this V2 tree. Later author UI and
native registration work on the coordinator's separate `6a24…` and subsequent
UI tree is excluded, as are the later author controller and global retention
packets.

Two final qualification sources must remain distinct:

- `e28eb0ef0ad13fedcd841cb485034ff8e224135b`: the complete shared Rust suite,
  formatting check and initial strict shared Clippy attempt.
- `96c4bdcc86f0a7f6e3e21c531ce873aa3dc3078f`: the corrected strict shared
  Clippy run and final frontend, Eval, native Rust, normal native build and
  Android checks. The only difference from `e28…` is the test borrow at
  `m08_query_v2_message_identity_review.rs:160`, replacing a one-element cloned
  slice with `std::slice::from_ref(&receipt_json)`. Production is identical;
  the 738-test full shared run was not rerun at `96c4…`.

The ten-entry `v2-check-results.json` is retained unchanged. It records the
initial shared Clippy exit 101, not a fictional all-green batch. The separate
`v2-clippy-shared-corrected.log` records the successful manual correction.
All other recorded stages terminate with exit 0; no running stage is counted
as passed. The manifest spans 03:07:46.551Z–03:19:35.011Z on 2026-10-24.

## Completed checks

Counts below describe their individual runs. Overlapping suites are not added
into a claimed number of unique tests. Ignored tests remain unexecuted.

| Check | Source | Exact outcome and evidence |
| --- | --- | --- |
| Shared Core, Store, Workspace and Android Rust, all features | `e28eb0e` | 738 passed, 0 failed, 9 ignored, 105 result groups including four empty doc-test groups; `v2-shared-full-corrected.log`. Includes the seeded 10,000-attempt invariant test. |
| Formatting | `e28eb0e` | `cargo fmt --all -- --check`, exit 0 in stage manifest. |
| Strict shared Clippy | `e28eb0e` then `96c4bdc` | Initial exit 101 for `cloned_ref_to_slice_refs` in the new test; corrected manual run succeeded in 4.21s. Both logs retained. |
| Eval Rust, all features | `96c4bdc` | 27 passed, 0 failed, 1 ignored, five result groups; `v2-eval.log`. Offline fixtures, not real-model quality evaluation. |
| Frontend verification | `96c4bdc` | Normal frontend build, strict TypeScript, existing schema/controller/headless/retention checks and 99 synthetic V2 wire checks passed; `v2-frontend.log`. Normal build verified free of dev journey/control hooks. |
| Frontend format | `96c4bdc` | All matched files passed Prettier; `v2-frontend-format.log`. |
| Normal native Rust tests, serial | `96c4bdc` | 85 passed, 0 failed, 1 ignored, one result group, 17.30s test time; `v2-native-normal-serial.log`. |
| Dev-harness native Rust tests, serial | `96c4bdc` | 89 passed and 1 ignored in the main group, plus two harness-contract passes: 91 passed, 0 failed, 1 ignored over two groups; `v2-native-dev-serial.log`. Main group 16.92s; harness group 0.01s. |
| Strict native Clippy | `96c4bdc` | Exit 0, terminal success in 10.64s; `v2-clippy-native.log`. |
| Normal native build | `96c4bdc` | No-default-features build succeeded in 10.28s; `v2-native-normal-build.log`. No application launch. |
| Android build, JVM tests and lint | `96c4bdc` | 78 tasks executed, success in 6m17s; both JNI ABIs rebuilt, debug and instrumentation APKs assembled, 182 JVM tests passed in 22 suites, fresh lint 0 errors / 1 warning. No device or instrumentation execution. |
| APK static audit | `96c4bdc` artifacts | Passed; four ELF libraries have 16 KiB LOAD alignment, only the app's generated non-exported receiver permission is declared; `v2-android-apk-audit.log`. |

The native Rust runs exercise application-owned worker, lease and real
Repository/Store paths. They are not native WebView rendering or Tauri IPC
execution. Frontend checks include synthetic adapters and headless React;
those results do not establish native integration. This cohort has no new
application render images to inspect and no newly captured WebView runtime
version.

## Preserved first failures and focused repairs

The source contracts and independent oracles were frozen before their producer
changes. Source-only preparation was not reported as an executed RED. The
actual qualification preserves these distinctions:

| First evidence | Actual result | Repair and subsequent evidence |
| --- | --- | --- |
| `v2-consumers-original-red.log` | Thin snapshot tests compiled, then 0 passed / 7 failed because the new operation returned an error envelope. | `play_snapshot_v2` producer `903d880`; seven passed afterward. |
| `query2-seams-original-red.log` | New scoped message/marker tests: 2 passed / 4 failed. | Scoped original identity and neutral author marker producer `8d46402`; the six new cases passed in the subsequent consumer run. |
| `v2-consumers-first-green.log` | Thin seven passed; existing Query2 group had 9 passes / 1 failure, row count four versus three after the new marker. | Existing compatibility assertions explicitly account for the neutral player marker. |
| `v2-shared-full-first.log` | Existing context-policy group had 11 passes / 1 failure, still matching the old `Row::Message`. | `7fe86f5` explicitly expects `ScopedMessage` with `original_scope`, preserving whole-receipt eligibility and observer restrictions. Corrected combined consumer run: 46 passed; corrected full shared run: 738 passed. |
| `native-author-port-original-red.log` | Compile failure E0432/E0407: proposed native preparation/outcome and Persistence methods absent. No tests ran. | Native port `da94d18` / `7dc7bdd`; 13 actual Store/Host tests passed in `native-author-port-first-green.log` (1.61s), also included in the broad run. |
| `v2-decoder-original-red.log` | Build failed because `v2-view-model.ts` was absent. No decoder behavior was executed. | Strict decoder implemented; `v2-decoder-first-green.log` reports 99 synthetic wire checks passed. |
| `author-broker-identity-red-first.log` | Wrong test filter: zero tests, 86 filtered. This is not a RED. | Corrected test selection preserved separately. |
| `author-broker-identity-red.log` | 0 passed / 1 failed: an otherwise matching manager accepted a foreign ArchiveBroker while the designated broker was occupied. | `620e129` binds the manager to the designated Weak ArchiveBroker identity before parsing, capability consumption or admission. All 15 native broker tests passed in `author-broker-identity-green.log` (1.36s). |
| `v2-clippy-shared.log` | Strict lint failure in a new test's cloned one-element slice; no production defect claimed. | Borrow-only test correction at `96c4bdc`; strict manual corrected run passed. |

The foreign-broker defect could bypass the one-worker admission owner; it was
not evidence that canonical validation or Store transactions could be bypassed.
The frozen regression checks foreign prepare/commit/lookup refusal, preservation
of the original valid capability, and subsequent actual commit through the
correct owner. The [independent authority review](M08_V2_NATIVE_AUTHORITY_REVIEW_2026-10-23.md)
retains the concrete source finding. No unfavorable run is discarded or
substituted with a favorable model score.

## Actual producer JSON to strict desktop decoder

The [bounded fixture producer](M08_V2_NATIVE_TRANSPORT_FIXTURE_SOURCE_2026-10-23.md)
uses actual Core histories and Host-library serialization. Root ran its one
test successfully (0.24s), then decoded its output with the existing strict
desktop V2 decoder. This is stronger than a hand-written JSON fixture, while
remaining distinct from SQL persistence, JNI, Tauri IPC and WebView rendering.

The fixed `v2-native-fixtures-first/v2-native-fixtures.json` is 495,727 bytes,
SHA-256 `cb4eaafab439e7ea69f912a3882eff6aeb9f1a54287bad53935bfa4ab740e776`.
The decoder reports four snapshots and 323 pages, including 89 paged and 54
historical pages. The cases cover Domain1/Domain2, the actual default/custom
player (including an NPC literally named `player`), all nine Query2 views,
private-search exclusion, historical known-as-observed A after world truth B,
scoped original messages, whole-player receipt eligibility, NPC event-only
units and the two-field neutral player marker.

The player-only author marker contains revision and constant kind only; it
does not turn author reason, source or fact values into character knowledge.
Native inspection privileges do not enlarge generation permissions. Thin
snapshots do not materialize full CharacterContextV2 or pretend that receipts
alone cover author intervals. See the source contracts for the exact limits:
[thin snapshot](M08_PLAY_SNAPSHOT_V2_SOURCE_2026-10-23.md),
[Query2 seams](../storage/M08_QUERY_V2_CONSUMER_SEAMS_2026-10-23.md),
[strict decoder](M08_V2_DESKTOP_DECODER_SOURCE_2026-10-23.md),
[native author port](M08_AUTHOR_NATIVE_PORT_SOURCE_2026-10-23.md), and
[native broker](M08_AUTHOR_DESKTOP_BROKER_SOURCE_2026-10-23.md).

The fixture opt-in accepts an existing owned absolute output directory, writes
one fixed new file with create-new semantics and a 1 MiB cap, and does not
provide an arbitrary file writer, seed importer or debugging server. The
standard suite without the opt-in executes the bounded in-memory case. All
fixture contents are synthetic and remain local by default.

## Android evidence and build artifacts

At `96c4bdc`, JNI was rebuilt for `x86_64-linux-android` / `x86_64` (2m16s) and
`aarch64-linux-android` / `arm64-v8a` (1m42s). The fresh JVM XML results contain
182 tests in 22 suites, zero failures/errors/skips, written at
03:18:04.762Z–03:18:04.776Z. The fresh lint XML reports zero errors and one
`GradleDependency` warning, written at 03:19:34.826Z. This is not a stale lint
report inherited from the foundation cohort.

The APK audit reports the generated
`org.locallore.app.DYNAMIC_RECEIVER_NOT_EXPORTED_PERMISSION` permission only.
Both `liblocallore_android.so` and `libandroidx.graphics.path.so` are present
for arm64-v8a and x86_64; all four ELF LOAD alignments are 16,384 bytes.
Static audit does not establish installer, device, runtime JNI or 16 KiB
physical-device behavior.

| Artifact | Bytes | SHA-256 |
| --- | ---: | --- |
| Normal `locallore-desktop-spike.exe` | 28,478,464 | `957554544bd7ba8cf25f4f59f17e7c524dbf79fc60690df554035d9c458b35f5` |
| Normal `dist/app.js` | 413,581 | `604ec37bceaa5a50bd60d094933ba32cab32dc759a576278a49ee03dc247f046` |
| `app-debug.apk` | 24,039,996 | `3eba9241b234e62e8bba8f861b1e6cd42fe1a6979d5c8a7060c090be2884e966` |
| `app-debug-androidTest.apk` | 1,715,781 | `40450f596df0d5b5db724f5452aac63124f820cefa20d82bd3a7733a39dc4c36` |
| Fresh `lint-results-debug.xml` | 1,168 | `7b59492e6c21986769142249a2c530fd40ff210ed59910533edc137ea35a3a2a` |

The 22 JVM XML files have aggregate manifest SHA-256
`0a31d46ddc8d305066148fc7283d66c4935acbbe4dcedd82ebc503060b424815`.
To reproduce that digest, sort XML filenames by name and hash the UTF-8,
LF-terminated lines `filename|lowercase-file-sha256|bytes`. The manifest was
computed in memory for inspection; no test-result content was rewritten.
Root confirmed that later UI test compilation under `debug/deps` did not
overwrite the normal executable or normal frontend listed here.

No Android device, emulator, ADB, install, instrumentation, Compose runtime or
JNI runtime was exercised. The instrumentation APK was compiled only. The
existing JVM compatibility tests do not qualify Android D2 read/resume UI or
Android authoring UX. Protected Android track resources were not used.

## Reproduction and environment

Use the repository checkout for the stated source and task-owned directories:
`<shared-target>`, `<native-target>`, `<fixture-directory>` and
`<evidence-root>`. Evidence is under the task's gitignored
`author-integration-artifacts`; generated artifacts are not committed by this
report. The saved launcher is `v2-prerequisite-checks.ps1`. It uses one build
job, `CARGO_INCREMENTAL=0`, dev/test debug info disabled, task-owned TEMP/TMP,
and the existing SQLite flags configuration. These are qualification settings,
not a performance or distributable-build claim.

```text
# Full shared run at e28eb0e, repository root:
cargo test -p locallore -p locallore-storage -p locallore-workspace -p locallore-android --all-features --offline --locked --target-dir <shared-target>

# Formatting at e28eb0e; corrected strict shared Clippy at 96c4bdc:
cargo fmt --all -- --check
cargo clippy --workspace --all-targets --all-features --offline --locked --exclude locallore-desktop-spike --target-dir <shared-target> -- -D warnings

# At 96c4bdc, repository root:
cargo test --manifest-path crates/locallore-eval/Cargo.toml --all-features --offline --locked --target-dir <native-target>
cargo test --manifest-path apps/desktop/src-tauri/Cargo.toml --offline --locked --target-dir <native-target> -- --test-threads=1
cargo test --manifest-path apps/desktop/src-tauri/Cargo.toml --features dev-harness --offline --locked --target-dir <native-target> -- --test-threads=1
cargo clippy --manifest-path apps/desktop/src-tauri/Cargo.toml --all-targets --features dev-harness --offline --locked --target-dir <native-target> -- -D warnings
cargo build --manifest-path apps/desktop/src-tauri/Cargo.toml --no-default-features --offline --locked --target-dir <native-target>

# apps/desktop, using the existing bundled Node:
node verify-frontend.mjs
node node_modules/prettier/bin/prettier.cjs --check "ui/*.{ts,tsx,html,css}" "*.{json,mjs}"

# apps/android, existing JAVA_HOME/ANDROID_HOME and task-owned output redirection:
<java> -classpath gradle/wrapper/gradle-wrapper.jar org.gradle.wrapper.GradleWrapperMain --offline --no-daemon --max-workers=1 --console=plain -Pandroid.builder.sdkDownload=false --init-script <task-owned-output-init.gradle> :app:testDebugUnitTest --rerun :app:assembleDebug :app:assembleDebugAndroidTest :app:lintDebug
python scripts/audit_apk.py <app.apk>
```

Actual producer/decoder fixture reproduction, using a new fixed filename in
an existing owned directory (PowerShell):

```powershell
$env:LOCALLORE_V2_FIXTURE_DIRECTORY = '<fixture-directory>'
# repository root:
cargo test -p locallore --features host --offline --locked --test m08_v2_transport_capture_review --target-dir <shared-target>
# apps/desktop, same environment:
node check-v2-native-fixtures.mjs
```

Tool attribution: pinned Rust 1.93.1; the shared host baseline records rustc
1.93.1 (`01f6ddf75`) / Cargo 1.93.1 (`083ac5135`), Windows 11 Pro x64 build
26300, i7-12700K and approximately 64 GiB RAM. These host facts are inherited
baseline metadata, not a fresh hardware probe. The actual launcher uses
bundled Node 24.22.1 (confirmed executable version metadata), existing
JetBrains JBR Java 17.0.6 (`release` metadata), Gradle 8.11.1, AGP 8.10.1,
Kotlin/Compose plugin 2.2.21, compile/target SDK 36, build-tools 35.0.0,
NDK 29.0.14206865 and min SDK 26. Rust components include Clippy/rustfmt.
The frontend source pins TypeScript 7.0.2, Prettier 3.9.10, esbuild 0.28.2
and React 19.3.1; native source uses Tauri 2.12.5. No package, SDK or model
download was needed for these offline commands. No npm version or newly
loaded WebView version is claimed.

## Local evidence integrity

Paths below are relative to `<evidence-root>`. The report author independently
read the completed outputs and computed SHA-256 values; it did not rerun their
commands. Logs and raw synthetic fixture data remain local, not public uploads.

| Evidence | SHA-256 |
| --- | --- |
| `v2-check-results.json` | `b57c98964631cee7ce81f3ee15d51227e110f944363dbf4417e21d4b55598170` |
| `v2-prerequisite-checks.ps1` | `3b993bfd70e7680e1146c915b2a6c5ed75f6a2e79bc4f8147ffc6d8f7649ea58` |
| `v2-shared-full-corrected.log` | `ed42b13c5fe99d9d13a83315f800cacd0cef9c8ed403f5c1224a1087d0dfe143` |
| `v2-shared-full-first.log` | `16ac4224470db6f7675cc8ffdc29ca791c885d4f54116abd15d7b0f3c62dc755` |
| `v2-clippy-shared.log` | `024d882353d5fabad44cf040c37ef68735af25583b458c6ff3ad4cb22eb85e2b` |
| `v2-clippy-shared-corrected.log` | `9d1c26043739e773dbad1702825bc82c8199ea01a9f1544c7955b9ddb6f3e3db` |
| `v2-native-normal-serial.log` | `c7a00779b19809ec80de0b026fb722294ee9464a9dd8ddeb8c515fdbff9727bf` |
| `v2-native-dev-serial.log` | `7a4110efd7d926cae6f264c204320de889d0226303bf68a32bc9979ff8e1230e` |
| `v2-clippy-native.log` | `9f84300af4b48d5c82aaae8fe279089265616e82e146c47def8dc299d01a4447` |
| `v2-native-normal-build.log` | `58cd7867544e3b39a84112d7f7d6def1657151c7b705f615af2e3dd66d65a69f` |
| `v2-eval.log` | `38aa93b4653036ea0d370525bb1121ec9b1b52c08f59c1e013f8d4fa071b2915` |
| `v2-frontend.log` | `ad6be2e22fabff6403fc278c47687029a1615bbe266bfb2fc84a7e703c8c65c0` |
| `v2-frontend-format.log` | `f20510a9da4717c51c4cffee6d0dd88d6c9a723d0a83711d01216f5b48961283` |
| `v2-android.log` | `b70bdfde64703940983f0106f5c97754a5c73aebeed22a29173180288f5c0623` |
| `v2-android-apk-audit.log` | `a2220741ab7d3170dc6f144e8b0c0d97b3b85457ef46d7bf0d6e0c76a8cef49f` |
| `v2-native-fixtures-first.log` | `76d421548482b5eda33ceacbb8f4350c5e5a9967b3299a43677527eb6e1f8d21` |
| `v2-native-fixtures-decoder-first.log` | `5e32fb3b82e3a61048f65e01b273a426fe5a97bd9586ed6d68f4eeb6bba82740` |
| `v2-native-fixtures-first/v2-native-fixtures.json` | `cb4eaafab439e7ea69f912a3882eff6aeb9f1a54287bad53935bfa4ab740e776` |
| `native-author-port-original-red.log` | `8fbf19cf482fbe6e67bfd88609587e043bbf0dae8e99b7a79167585c18e4ce8d` |
| `native-author-port-first-green.log` | `35ca53530ff7b176a4b72b078ed945c1e0c8c583cd9c329c9e647dad7418c4ff` |
| `v2-consumers-original-red.log` | `d97e479ec14fb2a237164144743e6c2abadfe2046b55a153e8168b5838eab059` |
| `v2-consumers-first-green.log` | `b44e9bb0e974ac99048c01ffee89855b73a0477b960d50d75263603978451436` |
| `v2-consumers-corrected-green.log` | `d60de33cb5b0fcb40c2470299152191560ab1e1d6ae6dd74572966f3363c3099` |
| `query2-seams-original-red.log` | `a11dcb7a49ecacd16db753d6d961d858be6ee7aff711f6519639c758c7d3d986` |
| `v2-decoder-original-red.log` | `534e08edb429e51a4829fb1e0a0deaeb56fea49c65911b27a3bfa77d4093efe8` |
| `v2-decoder-first-green.log` | `b4bf0d2351fdac4c223617a5c025db4151bf19400448583e3f342147803884f4` |
| `author-broker-identity-red-first.log` | `c060d69a5b787c73d3aa787d1d2e4bc11709ccb3a9d0d56b0cd2d5666c2bf734` |
| `author-broker-identity-red.log` | `88cfbabf71b0bd2673a7d977b01859d001c3970163bfbecafcc234d65bca62eb` |
| `author-broker-identity-green.log` | `e23e81b1aa859c530ec7f51ebbeee39d65993a71601206b42c7699d23ff895ef` |

## Remaining gates and next runnable work

This evidence makes the bounded V2 prerequisites reviewable; it does not mark
M08, D08 or desktop authoring complete. Host-v1 legacy behavior remains covered,
and the native broker has no registered author JSON Host command or production
Tauri exposure in this prerequisite tree. Full private author input/preview is
not a persisted frontend journal. Restart recovery metadata, privileged
hint-derived lookup, Android D2 decoder/roundtrip UI, and Archive3 remain
separate prerequisites or future work; they are not inferred from these tests.

No real-model quality run, new model weight, latency qualification, phone,
installer/update/uninstall, installed offline journey or public release is
qualified. The dated GLib 0.18.5 advisory/applicability and incomplete licensing
audit gates in [D09 reproducibility](D09_APP_REPRODUCIBILITY_2026-10-23.md)
remain explicitly open; absence of GLib from the inspected Windows graph is
applicability evidence, not upstream remediation. This report does not rerun
the advisory or licensing audits or change their disposition.

The coordinator's next runnable task is a focused prerequisite PR with these
source-bound results, followed by the separately claimed author UI/native
binding work. That later stack must close shared operation retention, both
explicit consents, exact-preview/context fences, truthful unknown outcomes and
read-only lookup, then run the application-owned native IPC/render harness and
inspect its images. No desktop capture, injected input, protected resource,
repository setting or merge is part of this report author's work.

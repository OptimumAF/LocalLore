# D09 workspace coordinator integration, 2026-10-23

Refs #31 D09.03/.05/.07 and #7 M03.01/.05. Claims
[#31](https://github.com/OptimumAF/LocalLore/issues/31#issuecomment-6370766365),
[#7](https://github.com/OptimumAF/LocalLore/issues/7#issuecomment-6370766761).
The accepted root/desktop lock union now supplies one root Cargo workspace,
preserving four portable defaults and two standalone runtime/evaluation roots.
Portable explicit workspace checks exclude only the desktop package. Nine
harness inventories reference the consumed root lock. No dependency version,
checksum, compiler metadata override, byte normalizer or production behavior
change is introduced. See the [original packet](D09_WORKSPACE_ALIGNMENT_2026-10-23.md)
and [independent integration review](D09_WORKSPACE_INTEGRATION_REVIEW_2026-10-23.md).

## Exact source and raw comparison

Original packet commits `5bf6546`, `d76e215`, `37e4737` were imported unchanged
onto accepted main3485 as `1f46994`, `ce0105e`, `3a84934`. Root froze clean
`3a849345da5a40f4c02ed15c3089d895d35fc6da` through the entire actual build gate.
The source was not edited while either build ran. The checker uses independent
new source, target, TEMP and copied locked-dependency trees. Neither app nor
worker/model is launched. Complete packaged bytes, including manifest, participate.

```powershell
python -X utf8 scripts/desktop-reproducible.py --source-commit <exact frozen HEAD> --node <reviewed node.exe> --npm-cli <reviewed npm-cli.js> --dependencies <locked node_modules> --worker <approved b5 worker.exe> --output <new output>
```

Actual result: **passed_two_clean_paths**. Both normal frontend builds and
normal package verification succeeded. All 446 ZIP members, payload hashes,
member order, metadata, folder inventory and full ZIP bytes match. Raw PE bytes
match, without exclusions or post-link normalization.

| Actual artifact, both independent builds | Bytes | SHA256 |
| --- | ---: | --- |
| Windows x64 application PE | 24332288 | `dcbaa7d480955cf5b70504f30fe52389896e8f5bb0b07bea418a3323a3939b03` |
| Developer ZIP | 10868414 | `8e02e138ae18dfa45a88de35aacd530d2e8ecd8db369697fad1e19a8aa5758ac` |
| Private complete comparison.json | — | `c1bb07423640b4ecb7194213e999f30e05f6a619d5cf2e79e0540a7bf5979056` |
| Checker source | 21757 | `85c4df5f2e772ce5e4c72d864b1aae0e4edd6615780b93949f8c3446d97ddd81` |

[Sanitized coordinator evidence](D09_WORKSPACE_COORDINATOR_EVIDENCE_2026-10-23.json)
retains bounded result fields. Private full tools/environment/source inventories
and raw build logs stay local. The independent reviewer rehashed both actual
PEs/ZIPs, every ordered member and 842 source files in each clean source tree.
This is a measured same-machine/toolchain result in two ASCII paths containing
spaces. It is not Unicode clean-root, other-machine, other-toolchain, Linux or
macOS reproducibility qualification. Final integrated product changes require
their own final comparison. Earlier failed clean01/clean02 remain preserved in
[accepted historical evidence](D09_APP_REPRODUCIBILITY_2026-10-23.md).

## Compatibility and review

After the frozen comparison completed, imported independent review `762e3a6`
as `4c2800c`, then normally merged accepted main374860e (#87/#94) at `be33064`.
Those accepted changes touch capacity verification and a test allocator, not
production Core/Store/Host/JNI/native/UI behavior. The raw comparison remains
attributed to the exact earlier frozen source, not this later merge.

Windows11 Pro10.0.26300; Rust/Cargo1.93.1, MSVC19.34.31937/toolset14.34.31933,
SDK10.0.19041.0, Node24.22.1/npm11.19.1, Python3.14.9. JDK17.0.6,
Gradle8.11.1, AGP8.10.1, Kotlin2.2.21, AndroidSDK36/NDK29.0.14206865.
Existing reviewed dependencies only; no provisioning/model download or settings
change. D-drive outputs/targets use debug0/incremental0.

| Actual coordinator check | Result |
| --- | --- |
| Exact original Git-blob lock union against main3485 | 414 identities/407 registry checksums unchanged; no additions/removals/versions; standalone runtime/eval locks byte-identical |
| Actual locked/offline metadata and graph | Five members/four portable defaults; Linux portable41 and AndroidARM64 graph58 packages exclude desktop/Tauri/GTK/GLib; graph evidence only |
| `python scripts/check.py host --offline`, frozen3a | 441 workspace Rust+3 linker,356 Python,four fixtures,fmt/default strict Clippy PASS; four existing explicit ignores |
| Same complete host runner after main374860e merge | 442 workspace Rust+3 linker,381 Python,four fixtures,fmt/default strict Clippy PASS; four existing explicit ignores |
| Strict all-feature portable Clippy, both source stages | PASS with `--workspace --exclude locallore-desktop-spike --all-targets --all-features --locked --offline -- -D warnings` |
| Native frozen3a default/dev tests | 46 default /48 dev+2 contract PASS; one existing explicit ignore; strict all-feature Clippy PASS |
| `node verify-frontend.mjs`; full Prettier | PASS, actual controllers with native doubles; not WebView execution |
| `python scripts/desktop-reproducible-tests.py`; `desktop-package-tests.py` | 20 /12 synthetic checks PASS |
| Ordinary Android app/test APK, JVM, lint, ABI audit | Both ABI builds and APKs PASS;146 JVM,zero failures/errors/skips;lint0errors/1existingwarning;16KiB audit PASS;78 tasks executed,3m11s |

Android command from apps/android uses an argv array so PowerShell preserves
the dotted property as one argument:

```powershell
java -classpath gradle/wrapper/gradle-wrapper.jar org.gradle.wrapper.GradleWrapperMain -I <own build-directory init.gradle> :app:assembleDebug :app:assembleDebugAndroidTest :app:testDebugUnitTest :app:lintDebug --offline --no-daemon --console=plain '-Pandroid.builder.sdkDownload=false'
python scripts/audit_apk.py <own ordinary app-debug.apk>
```

This is compilation/JVM/static evidence, not Android/device execution. No ADB,
app/model/worker launch, UI rendering, desktop control, protected checkout or
protected chat resource was operated for workspace verification. Separate
archive-export long-path handling was discovered in M05 compatibility and has
its own focused correction/review; this workspace change claims no such fix.

## Retained coordinator invocation errors

The first comparison launch mistyped a full source SHA. Git preflight rejected
it before creating build output; the log is retained. The corrected command used
actual `git rev-parse HEAD`, not a guessed hash, then passed both clean builds.
Initial Android invocations referenced an absent own output init script, then
passed an unquoted dotted `-P` property that PowerShell split. Both failed before
product compilation. Created the intended local-only output script and used an
explicit argv array; the full fresh build passed. First standalone APK audit
lacked ANDROID_HOME and refused; the correctly scoped environment audit passed.
No failed attempt is counted as execution or hidden by changing product gates.

Private final host log SHA256
`f646ba239430b1acb555834ce4d09992fdc2be49fc9934f68d9d4b141767c3ff`;
Android build `d8f90f84546a70e43718b4eef0c1bbf78ded729bd5bf3f45beecc63fa176cdbd`;
audit `a2220741ab7d3170dc6f144e8b0c0d97b3b85457ef46d7bf0d6e0c76a8cef49f`.
Ordinary app/test APK hashes respectively
`8bf767f7857a3d42da32ef90e7118f8e0a82e171c416939a59b10ceb3a51ba24` /
`e5661bdf6de25dfb87019cd7f58a96e0dd55c32a8760ebb9444814df104169a8`.

Only this scoped build prerequisite is eligible for owner-authorized merge.
Legacy license_audit_complete remains false; separate exact notice work is
pending. The moderate GLib advisory is neither dismissed nor silently upgraded.
Offline installation/runtime/network-denial, full application acceptance and
distribution remain separate D09 gates. No release, Actions enablement,
repository setting or review fabrication is authorized by this evidence.

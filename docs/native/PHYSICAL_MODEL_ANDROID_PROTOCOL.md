# Explicit physical-phone model experiment

Supporting M01.01/M01.02/M01.05 and M05.05, root issue #5 claim6406017018.
This is a separate debug experiment stacked on unmerged PR181, not a selected
production backend or a supported-phone declaration. Current phone availability
and all actual execution are coordinator-owned. The source/API preparation
does not imply a model was copied, imported, loaded or used on a phone.

## Build and installation boundary

The explicit selector is `localLorePhysicalModelVerification=true`, together
with existing `localLoreLiteRtVerification=true` and
`localLoreModelSetupVerification=true`. Volume, old receipt, picker and all other
verification installations are mutually exclusive. Use only the exclusive
`.gradle-physical-model` project cache and `app/build-physical-model` outputs.
The application ID is `org.locallore.app.phoneverify`, with instrumentation
package `org.locallore.app.phoneverify.test`. Root must prove both packages are
fresh/absent before installation; existing `.modelverify`, `.modelvolumeverify`
and ordinary application packages/data remain outside the authority of this
experiment. Release tasks/variants are forbidden by the existing LiteRT gates.

Build-source preparation is in `src/litert/java/PhysicalModelPolicy.kt` and
`AndroidPhysicalModelAccess.kt` (under the usual `org/locallore/app` package).
These small types compile in candidate LiteRT graphs so the explicit
`CandidateLocalModel.store` branch resolves without reflection. Actual selection
requires `BuildConfig.DEBUG`, `PHYSICAL_MODEL_VERIFICATION`, exact package/main
process/UID and the profile below. The old volume selector and old receipt
factory/guards remain unchanged. The physical build enables the existing
bounded receipt trace flag; it never enters the old volume-dependent factory.

Only physical debug/test sources live in `src/physicalModel*`. Its manifest
exposes the existing setup launcher, keeps play/main nonexported, and adds no
new exported control, permission or dependency. Backup exclusions remain the
ordinary manifest's existing exclusions. Existing Rust engine/schema, setup
controller, receipt transaction, SDK worker and model manifest remain the
authorities for their respective responsibilities.

Coordinator-only build command shape (not executed by the Android agent during
source preparation):

```powershell
.\gradlew.bat --offline --project-cache-dir .gradle-physical-model -PlocalLorePhysicalModelVerification=true -PlocalLoreLiteRtVerification=true -PlocalLoreModelSetupVerification=true -Pandroid.experimental.lint.version=9.4.1 -Porg.gradle.java.installations.auto-download=false :app:testDebugUnitTest :app:assembleDebug :app:assembleDebugAndroidTest :app:auditLiteRtDependencies :app:auditLintAnalyzer
```

The existing locked JDK21 candidate compiler/SDK graph and audited analyzer
apply; there is no toolchain download or silent version change. Build/audit
success and device execution must be recorded separately when actually run.

## Exact experimental profile

Profile ID: `s918u1_api36_arm64_4k_v1`.

The app observes exact `Build.MODEL=SM-S918U1`, API36,
`Build.SOC_MODEL=SM8550`, primary ABI `arm64-v8a`, page size4096, kernel-visible
memory10–12GiB inclusive, available memory at least4GiB and `lowMemory=false`.
These are explicit admission margins for this experiment, not an allocation,
latency or quality guarantee. Observations are rechecked before receipt and SDK
boundaries on IO; failed admission is sticky for that process owner.

`ro.board.platform=kalama` is a **host-only** fresh-inventory field. It is not
`Build.BOARD`, which maps to `ro.product.board`; that different field was not
established by the prior inventory. The app does not call hidden property APIs,
spawn `getprop`, or guess a `Build.BOARD`/`Build.HARDWARE` mapping. Root must bind
the independently observed host field and actual selected device in its grant.
No serial, private hardware identifier or raw diagnostic belongs in public
reports. An absent phone is a blocked execution gate, not an emulator substitute.

The fixed model remains2,588,147,712 bytes, SHA256
`181938105e0eefd105961417e8da75903eacda102c4fce9ce90f50b97139a63c`.
Existing LiteRT-LM0.18.1 / commit
`bda624851d74be34d4e1f7fac1fc4155939539c7`, model revision
`a790a852d433991c0c0a41c1154cf9b3850300fa`, CPU4 threads, context4096,
director350/narrator220 and existing worker/codec source identities remain
unchanged. An admitted real run must still verify exact source/binary/artifact
identities; API availability does not establish successful native execution.

## Same-filesystem storage and resource ownership

Every path originates in the exact target application's canonical
`Context.noBackupFilesDir`, resolving only Android's trusted internal alias:

- `physical-model-source-v1`: fixed host-staged source owner/probe/model.
- `physical-model-control-v1`: existing receipt transaction's lock/receipt/acceptance.
- `physical-model-data-v1`: owned accepted model and bounded runtime cache root.
- `physical-model-proof-v1`: new canonical phase proofs/ready markers/trace sidecars.

Roots are disjoint siblings. The adapter checks strict non-symlink paths, same
UID, device and pinned anchor inode; observed child-directory inodes cannot be
removed/replaced under the same owner. Legacy local-model roots in this fresh
package must be absent. No external-storage enumeration or removable-media
assumption is used, and no old package/root is queried, migrated or cleaned.
Receipt/model source files require the additional exact ownership, whitelist,
size, full hash, stream-close and source-identity checks of the phase harness.

There is one shared-filesystem free-space observation. The explicit physical
reserve is2GiB (2,147,483,648 bytes). It includes the old importer256MiB reserve
and exceeds the old userdata1GiB+128MiB floor; these margins are not added twice
for one filesystem. Before staging weights, fresh free bytes must be at least
`2 * 2588147712 + 2147483648 = 7323779072`, accounting for original source and
accepted copy. Once the source exists, admission requires missing destination
bytes plus2GiB; runtime requires2GiB. The unchanged receipt transaction also
independently enforces its own256MiB minimum. No free-space reading is a
reservation. Root's fresh host and app prechecks must both precede weight copy.

## Phase interface awaiting final proof freeze

Only exact separate class selection is eligible for a heavyweight method:

| Order | Class in `org.locallore.app` | Single method | Budget ms |
|---|---|---|---:|
| 1 | `PhysicalModelPreflightTest` | `verifiesPrivatePhoneSourceBeforeCopy` | 30000 |
| 2 | `PhysicalModelImportTest` | `importsFixedPhoneCandidate` | 150000 |
| 3 | `PhysicalModelCancellationTest` | `cancelsAndJoinsWithoutCommit` | 170000 |
| 4 | `PhysicalModelGiftTest` | `commitsGuardedPhoneGift` | 170000 |
| 5 | `PhysicalModelDialogueTest` | `recordsLiteralPhoneDialogue` | 170000 |
| 6 | `PhysicalModelReopenTest` | `reopensPhoneReceiptsWithoutInference` | 120000 |

Each later phase uses a new process and exact prior canonical-proof hash and
identity. CANCEL precedes GIFT: canonical revision0/no receipts remains, public
SDK cancellation must ACK/join/drain/close known, and no uncertain owner may be
reused. GIFT then commits revision1/one receipt; DIALOGUE commits revision2/two
receipts with statement distinct from truth; REOPEN preserves both in a new
process without source or inference calls. The engine validates/commits;
narration cannot become an alternate canonical authority.

The detailed common/check key sets are proposed to the coordinator before
instrumentation implementation. Use shared-storage metrics, not fabricated
external/userdata independence; retain original positive and negative checks,
known closure before credit, and all failed attempts. Existing emulator proofs
and their7–8GiB/removable guards are not widened to accommodate this phone.

## Official source review and remaining limits

The pinned publisher
[model card](https://huggingface.co/litert-community/gemma-4-E2B-it-litert-lm/blob/a790a852d433991c0c0a41c1154cf9b3850300fa/README.md)
declares Apache-2.0 and an Android-ready `.litertlm`/CPU path. It describes mixed
2/4/8-bit weights and memory mapping; publisher memory/performance observations
are not this phone's results. Its separate Qualcomm QCS8275 NPU artifact is not
the selected generic artifact and does not establish Samsung NPU compatibility.
No GPU/NPU backend or vendor dependency is introduced here.

Pinned SDK
[`Config.kt`](https://raw.githubusercontent.com/google-ai-edge/LiteRT-LM/bda624851d74be34d4e1f7fac1fc4155939539c7/kotlin/java/com/google/ai/edge/litertlm/Config.kt)
exposes CPU thread count and total input+output/KV-cache token capacity;
[`Engine.kt`](https://raw.githubusercontent.com/google-ai-edge/LiteRT-LM/bda624851d74be34d4e1f7fac1fc4155939539c7/kotlin/java/com/google/ai/edge/litertlm/Engine.kt)
forwards those to JNI. The official
[Android guide](https://developers.google.com/edge/litert-lm/android)
requires background initialization/resource closure. Upstream runtime source is
Apache-2.0 with existing separate bundled third-party notices retained/audited;
there is no blanket licensing claim for every linked component.

ARM64 ABI presence, API26 native floor and16KiB ELF alignment are dated
[existing artifact audit](../runtime/android/LITERT_SOURCES_2026-10-22.md)
observations; no SDK artifact/native/phone execution was performed by this
source-review agent. Alignment does not prove16KiB-device operation. A connected
physical phone, actual model import/inference/cancellation/restart, memory high
water mark, sustained thermal/latency, prose/semantic quality, DocumentsUI,
16KiB physical coverage and owner backend/support acceptance remain separate
pending gates. The current pure policy tests are new source and unrun until
the coordinator builds the integrated profile.

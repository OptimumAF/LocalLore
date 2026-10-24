# Android experimental cache placement, 2026-10-23

Refs [#5](https://github.com/OptimumAF/LocalLore/issues/5) (M01.05), research
claim `6370261705`, source base `fdf144a`. This is a read-only feasibility report,
not an implemented cache relocation or a runtime/model selection.

An explicitly selected app-owned directory on a new D-backed virtual SD image
is a plausible next experiment. The installed emulator supports that attachment,
and the pinned SDK accepts a writable cache directory. Guest mounting,
available capacity and native cache-file compatibility remain unverified.
There is no execution-ready preservation claim for the current A/B attachments:
their selected AVD configuration locations could not be resolved by the bounded
local inventory described below.

## Current admission and preservation boundary

The existing [integrity observations](MODEL_INTEGRITY_DEVICE_2026-10-23.md)
remain authoritative: B matched the source; A's mismatch has no established
cause. A's preserved generated cache was **788,412,736 bytes**. This is an
observation, not a maximum cache requirement. The later
[cache admission observations](CACHE_ADMISSION_DEVICE_2026-10-23.md) retain the
current capacity refusal and absence of an eligible native-output cleanup target.

The historical B free-space observation was **1,800,622,080 bytes**. A fresh
allowance of **1 GiB growth plus 1 GiB reserve** requires 2,147,483,648 bytes,
before unrelated growth; that observation fails. Moving only compiler output
on the host cannot repair this guest-volume deficit. A read-only host snapshot
during this research showed C free **4,879,089,664 bytes** and D free
**119,168,028,672 bytes**; C also fails a 5 GiB-before-work condition. These are
time-specific host measurements, not reservations.

The candidate must leave the original A/B model files, A's existing cache,
story/userdata files, original SD image and all 21 installed LocalLore APK
identities intact. A newly generated cache would be a separate artifact;
no existing model/cache is a cleanup candidate in this report.

## Installed tools and selected AVD metadata

Read-only commands against the already installed SDK returned:

| Check | Actual result |
|---|---|
| `emulator -version` and `source.properties` | 35.3.12.0, build 12990079; package revision 35.3.12 |
| `emulator -help-sdcard` | Existing image can be selected with `-sdcard`; missing image means no card |
| `emulator -help-data` | `-data` selects a different `/data` image |
| `emulator -help-partition-size` | System/data partition size option, expressed in MB |
| `emulator -help-disk-images` | Userdata and optional SD/cache/snapshot images are distinct |
| `mksdcard -help` | FAT32 image creator; 9 MiB minimum; GiB suffix supported; 1023 GiB maximum |
| Installed `avdmanager list avd` | Exit 0; neither selected running AVD name was listed |

The last command used Java 17.0.6 and local metadata only. Nonselected inventory
blocks were discarded; no other AVD configuration was opened directly. Exact-port-filtered
Windows process metadata identified the two existing selected AVD names.
Their command lines and prior selected launch records contained neither an
explicit SD override nor a data-directory override. The relevant Android home
environment variables were absent, and their two default registry locators and
`config.ini` paths were absent. Consequently, **current card path, image size,
filesystem and guest mount status are unknown**. No attachment image contents,
userdata image or model bytes were inspected. Private locator/process records
remain outside Git; names, ports and private paths are omitted here.

## Storage attachment is separate from userdata

Official [emulator documentation](https://developer.android.com/studio/run/emulator-commandline)
defines `-sdcard` as a startup override of the configured SD image. It cannot
remove the simulated card from an already running AVD. `-data` instead selects
the persistent userdata image, creating one from the initial image when the
requested file is missing. Neither changing a userdata path nor a partition-size
argument establishes preservation or successful resizing of existing data.
No wipe, snapshot restore or image resize is proposed here.

The official [mksdcard documentation](https://developer.android.com/tools/mksdcard)
and installed help agree that a fresh FAT32 image can be created separately.
For a later authorized experiment, an exclusively created 8 GiB image on D is
a concrete candidate with room beyond the proposed 2 GiB admission condition.
This is an untested size choice, not measured guest free space. Keep one new
image per selected AVD and retain the original image at its original location;
do not attach the same writable experimental image concurrently to A and B.

An 8 GiB volume does not remove FAT32's individual-file limit. Microsoft's
[filesystem comparison](https://learn.microsoft.com/en-us/windows/win32/fileio/filesystem-functionality-comparison)
lists a 4 GiB maximum file size for FAT32. No maximum future SDK cache-file size
has been established, and this report makes no mmap-performance or compatibility
claim for a FAT32-backed Android volume.

## Pinned SDK and Android app storage

At LiteRT-LM **0.18.1**, commit
`bda624851d74be34d4e1f7fac1fc4155939539c7`, the actual source is
[Config.kt](https://github.com/google-ai-edge/LiteRT-LM/blob/bda624851d74be34d4e1f7fac1fc4155939539c7/kotlin/java/com/google/ai/edge/litertlm/Config.kt),
not `SDKConfig.kt` (the requested latter path returned 404).
`EngineConfig.cacheDir` is nullable and requires a writable directory; its default
places cache beside the model. The pinned
[Engine](https://github.com/google-ai-edge/LiteRT-LM/blob/bda624851d74be34d4e1f7fac1fc4155939539c7/kotlin/java/com/google/ai/edge/litertlm/Engine.kt)
passes it to JNI, whose
[implementation](https://github.com/google-ai-edge/LiteRT-LM/blob/bda624851d74be34d4e1f7fac1fc4155939539c7/kotlin/java/com/google/ai/edge/litertlm/jni/litertlm.cc)
sets the main executor's cache directory when nonempty. The current
`SpikeInstrumentation.configuredEngine` uses the five-argument constructor and
does not supply this setting. A future explicit destination therefore changes
benchmark source/APK identity; it is not the unchanged installed control.

Android's [Context API](https://developer.android.com/reference/android/content/Context#getExternalCacheDirs())
provides package-owned cache paths across shared/external volumes. The singular
`getExternalCacheDir()` selects the primary volume, which may be emulated over
userdata and provide no extra headroom. Array entries can be null. Since API 19,
the app needs no storage permission for its own returned paths. Future selection
must identify the intended separate volume, not infer it from a familiar path.

The [app-specific storage guide](https://developer.android.com/training/data-storage/app-specific)
requires checking external storage availability and using framework-provided
app directories. On Android 11+, apps cannot create arbitrary app-specific
external roots. A future experiment should select a mounted writable path from
the API, then create only its own fresh subdirectory. Cache content is disposable
and is removed on uninstall; this location must not hold canonical saves.

## Next runnable work and remaining gates

Within the standing local-development goal, the next packet can freeze a
**new experimental APK/control**
with an explicit app-owned cache destination, plus a preservation plan for the
selected AVDs. Before any model initialization:

1. Resolve the selected AVD home, original card and launch environment under the
   exclusive A/B lease. Retain the exact existing attachment/configuration and
   APK/model identities; unresolved attachment identity blocks reconfiguration.
2. Admit host capacity independently. Create a fresh, bounded, marked SD image
   on D after recording the preservation plan and fresh capacity checks; do not edit, resize, replace or
   delete an existing image. Budget its full possible backing allocation plus
   host reserve. Identify the exact stop/start and boot-state policy
   for coordinator review before changing an attachment.
3. After an authorized startup override, check guest volume identity, mounted
   writable state, actual destination free space and host backing space. The
   selected app cache volume must pass the growth-plus-reserve guard; `/data`
   must retain its independent reserve. No automatic internal-directory fallback.
4. Run a bounded synthetic create/write/read/mmap/close probe under the
   actual benchmark UID in that fresh cache subdirectory. Verify ownership and
   cleanup of the new probe only. SDK cache creation itself is a later write
   experiment; neither tool help nor a filesystem name proves it will succeed.
5. Reverify the protected identities and 21 APKs after lifecycle work. Keep A's
   mismatched model and cache untouched. Any later B inference requires its own
   integrity recheck, current capacity admission and explicit experiment scope.

If an already attached, sufficiently large separate volume is later verified,
using its package-owned cache path could avoid an attachment restart. Current
local evidence does not establish such a volume, so this is conditional rather
than an available shortcut.

This packet performed no ADB/device calls, emulator launch/stop/restart,
configuration mutation, image creation, model read/copy, cache write, build,
dependency change, inference, or GitHub mutation. Verification was limited to
official-source reads, installed tool help/local inventory, selected process and
locator metadata, and host free-space queries. Physical-device feasibility and
production runtime selection remain open.

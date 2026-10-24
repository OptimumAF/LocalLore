# Android cache-volume observations, 2026-10-23

Refs [#5](https://github.com/OptimumAF/LocalLore/issues/5), M01.05, claims
`6370637648`, `6370757711` and `6371072564`. Source base `91f32df`. This packet resolves the
selected emulator attachments and tests a new, separate storage attachment on
**B only**. It does not initialize a model or qualify a runtime/profile.

## Resolved original attachments

The bounded emulator-console command `avd path` returned the actual content
directory for each selected running AVD. This resolved the earlier
[research report's](CACHE_PLACEMENT_RESEARCH_2026-10-23.md) unknown locator.
Only those selected configuration files and fixed attachment-file metadata
were inspected; userdata, card and model contents were not read.

| Observation | A | B |
|---|---|---|
| Running emulator executable | 37.2.12 build 16428233 | 35.3.12 build 12990079 |
| Guest | Android 15 / API 35, x86_64 | Android 15 / API 35, x86_64 |
| Configured userdata | 6 GiB, original base plus QCOW2 overlay on C | 6 GiB, original base plus QCOW2 overlay on C |
| Effective original hardware SD setting | false | false |
| Original default SD image / QCOW2 image | absent / absent | absent / absent |
| Advertised original public disks | none | none |
| Original external storage | emulated over userdata media | emulated over userdata media |

The selected processes use different emulator installations. The previous
installed-SDK tool observation of 35.3.12 was correct for that installation,
but did not establish A's actual running executable version. Exact executable
paths, launch arguments, process identities, AVD names, configuration hashes
and environment paths remain in private evidence.

Both original guests reported only mounted private and emulated volumes,
with no `sm list-disks` entries. `dumpsys mount` identified the emulated volume
as backed by userdata media, with no public volume records. Mount metadata
showed ext4 userdata and the emulated FUSE view backed by the same userdata
media directory. No public filesystem UUID was present. Selecting primary
external cache would therefore not establish a separate capacity budget.

A's config contained an earlier enabled SD declaration followed by a disabled
one; its effective hardware file recorded false. A nominal 512 MB SD-size
declaration in either config was not evidence of an attached card.

## Reviewed B-only change

The coordinator explicitly approved one reversible B-only lifecycle operation.
A remained running and unchanged. Before mutation, exact original B config,
generated hardware config and AVD registry bytes were copied to exclusively
created private evidence files, flushed, and hashed. The original config was
1,851 bytes with SHA-256
`d7044a774a9fb1292108bf2eb7368144559802cb72d58d6445eefa20f676b90f`.

The original launch used no snapshots or snapshot saving. It had no SD-card,
userdata-directory or userdata-image override. The hardware metadata supplied
the explicit existing AVD home and SDK root, avoiding a guess based on the
coordinator process environment.

Both installed emulator versions' `-help-sdcard` describe an image-path option.
The official emulator
[SD-card handling source](https://android.googlesource.com/platform/external/qemu/+/emu-master-dev/android/android-emu/android/main-common.c)
also explicitly ignores that option when SD hardware is disabled. This is a
moving upstream branch, not a proven source revision for either binary. The
experiment consequently did not assume a path option could enable hardware.

The bounded operations were:

1. Admit image creation with C free at least 4 GiB plus 64 MiB and D free at
   least 28 GiB. Actual values were **4,592,324,608** and **117,295,230,976** bytes.
2. Use the existing SDK `mksdcard` to create one nonexistent, exclusively owned
   **8,589,934,592-byte** image on D. The child completed with exit 0 and known
   cleanup. No existing image was resized, formatted, overwritten or moved.
3. Gracefully stop only B. The captured emulator and QEMU process handles both
   reached exit 0. A and all other emulator processes were left alone.
4. Recheck the original B config against the exact backup. Change only its
   single `hw.sdCard = no` value to `yes`; flush and verify. The enabled config
   is 1,852 bytes, SHA-256
   `10214291d830ceb8fd651ad1e47cc3eb1e78b2ae814c3a1e2c8daa46b1ea605e`.
5. Launch B once using its original 35.3.12 executable, original arguments,
   explicit original AVD home/SDK root and the new image's SD-card option.
   No wipe, userdata, initialization-image, partition-size or snapshot override
   was introduced. Its original userdata path remained unchanged.
6. Bound boot observation to 120 seconds. Boot completed after 49 property
   polls: 45 exited 0 and the first four exited 1; all clients were cleaned.
   The regenerated hardware file recorded enabled SD hardware
   and the exact new D image path.

The original config is **preserved as a byte-exact backup**, rather than claimed
unchanged in place. B intentionally remains running with the enabled config
and new card. The restoration map is retained privately: stop only this owned
B instance, restore the exact original config bytes after checking the expected
enabled hash, and relaunch with its original arguments without the new card.
No rollback or second restart was needed in this packet. Userdata changes
normally during boot; no byte-for-byte userdata preservation claim is made.

## Actual guest result

The first post-boot observation showed the new public disk unmounted with null
UUID. A later bounded read-only observation showed it mounted, without a
manual mount, partition or formatting command. Both observations are retained;
the initial state is not replaced by the later one.

| B observation after mounting | Actual value |
|---|---:|
| New disk size | 8,589,934,592 bytes |
| New public filesystem | FAT32 / `vfat` |
| Public volume identity | B-cache, with exact identity retained privately |
| Public filesystem capacity | 8,573,157,376 bytes |
| Public available bytes | 8,573,059,072 bytes |
| Userdata available bytes at that observation | 1,799,946,240 bytes |

The public volume has its own virtio block disk and `vfat` mount, distinct from
the userdata block device. The public FUSE view maps to that new filesystem,
whereas the original emulated volume still maps to userdata. Effective hardware metadata
binds that new disk to the exclusively created D-backed image. C and D were
observed as distinct NTFS volume identities; private GUIDs are not published.
The actual generated UUID is retained privately, not assumed unique across
future separately created cards. Public evidence uses the logical alias B-cache.

At the last preservation-only check, C free was **5,100,101,632** bytes and D free
was **107,281,764,352** bytes. Capacity measurements are observations, not
reservations against unrelated growth.

## Separate-package primitive probe

After artifact qualification and separate coordinator approval, B alone received
the new `org.locallore.runtimebench.litert.cacheprobe` APK, source `44cd85f`
(coordinator integration `018747f`). Its size was **63,598,424 bytes**, SHA-256
`50e6e60cfdb2194272d31cf651805f34452ae09a04443558049020664f60d107`.
It uses the sole `CacheProbeInstrumentation` runner and adds no permission.
The artifact qualification recorded 62 JVM tests and package, ABI, alignment,
dependency and lint checks; those were run by the coordinator/build author,
not inferred from this device experiment.

Installation was separately admitted with a **512 MiB** planned userdata/C
allowance, rather than treating the later 64 MiB inspection allowance as an
installer budget. The APK was below 64 MiB; B had 1,802,264,576 userdata bytes,
C 4,976,910,336 bytes and D 103,778,426,880 bytes immediately before installation.
The measured post-install userdata consumption was **63,655,936 bytes** and C
net consumption **1,912,832 bytes**. Reserves and the 512 MiB limits passed.
These free-space deltas include other OS activity and do not prove causation or
a maximum future installation footprint.

Three framework `inspect` invocations and **one** `mmap` invocation were run.
Every inspection independently checked the new-package setup capacity first;
framework directory discovery can create/fix the new package's own directories
and is therefore not described as allocation-free. The Android framework
reported a mounted, writable, nonprimary, nonemulated cache candidate on the
new public UUID, with a filesystem device distinct from userdata. Backing was
also checked against the effective image path and actual guest disk/mount
graph; the private UUID alone was not treated as proof of independent storage.

The frozen [volume-aware controller](../../../benchmarks/android_cache_volume.py),
commit `4e431a8`, wrapped the entire single mmap callback. It admitted both
before and after samples. Each sampler used one fresh free-space query per
physical host volume, reusing the identical D measurement for cache and evidence
so their combined reserve/growth budget was not counted twice.

| Wrapper sample | Before | After |
|---|---:|---:|
| Public cache free bytes | 8,573,046,784 | 8,573,038,592 |
| Userdata free bytes | 1,738,305,536 | 1,738,305,536 |
| C free bytes | 4,970,168,320 | 4,969,926,656 |
| D free bytes | 103,778,148,352 | 103,777,955,840 |
| Counted cache file bytes | 0 | 34 |

The actual probe wrote and independently read/compared **65,536 synthetic bytes**,
mapped the file read-only, unmapped it, closed its descriptor and removed only
that newly created file. The marked session directory remained. The probe did
**not dereference the mapped pointer**; successful mapping plus file-read
verification must not be represented as reading model tensors through mmap.
The instrumentation's own `post_sample` and the later independent wrapper
inspection are retained separately. Both observed only 34 counted bytes, the
validated owner marker, after file removal. Public free-space consumption was
8,192 bytes and userdata net consumption was zero during the wrapped interval.

All reported Engine and Conversation open/close counters were **zero**. The
callback and both wrapper samples completed without exceptions or unknown
ownership. Each invocation stopped only the new test package during cleanup
and confirmed its process absent; the original benchmark was never started or
stopped by these invocations. No model was copied, opened or initialized, and
the `play` operation was not invoked. This proves the finite filesystem
primitive under this app UID, not LiteRT-LM cache compatibility or inference.

## Preservation, failures and remaining gates

All **21 original installed LocalLore APK hashes per emulator** matched their
preflight maps after B boot and after mounting. The frozen benchmark APK
remained SHA-256
`715a6c4521592256b1ee6e1bf9ec4d0f3f1974dcdde040781269163efbc534a6`.
Both benchmark processes remained absent. Regular-file model/cache metadata
(size, mode, device/inode and modification/change times) matched preflight.
No new full model hash was taken; A's previously established mismatch remains
unrepaired and unexplained. This metadata check is not a new content-integrity
proof or a read of existing stories.

The final attachment/metadata journal contains **615 completed commands** with
known cleanup: **607 exit 0 and eight nonzero**. The separate app-probe journal
contains **146 commands**, all completed with exit 0 and known cleanup. Thus the
two selected-device journals contain **761 commands**, including every nonzero
record below. The separate bounded device-inventory command also completed
with exit 0 and known cleanup. The complete nonzero inventory is:

| Operation | Count | Exit | Observation |
|---|---:|---:|---|
| Initial A/B volume metadata | 2 | 127 | Fixed stat format contained unquoted pipe characters in the raw-shell wrapper |
| First B boot-property polls | 4 | 1 | Startup polls; stderr was recorded as 25 bytes each, not retained text |
| Mounted-volume optional stat format | 1 | 127 | Same raw-shell quoting mistake |
| Optional B sysfs block-size read | 1 | 1 | Fixed sysfs path read failed; stderr was recorded as 45 bytes, not retained text |

No device command timed out, and no client ownership was unknown. All command
stdout, exit/cleanup results and stderr byte counts are retained privately.
Exact stderr text was not retained, so neither a permission failure nor an
offline-device diagnosis is asserted from those byte counts. The successful
mounted `df` command exited 0. A subsequent preservation-only check completed
without relying on either optional diagnostic. Nonzero observations were not
removed or reset to obtain a green result.

Earlier locator misses, a PowerShell config-read command that exited 1 without
retained diagnostic text, missing optional launch files and a local journal
inspection error are separately recorded as setup failures; their original
tool output is not uniformly retained in the private device journal. The
GitHub issue-read connector was unavailable; the coordinator owns ticket updates.

A's observed userdata free space was **1,053,560,832 bytes**, below even the
1 GiB reserve, so no A attachment or app write was attempted. No model/cache
was evicted to make space. B's new volume resolves an attachment prerequisite;
it does not itself prove that an app-owned external cache path is available,
writable, mappable or honored by LiteRT-LM.

Final inventory proved **21 installed LocalLore APK identities on A and 22 on
B**: B's only added identity is the new test APK. All original 21 hashes per
emulator and protected model/cache metadata matched preflight. Both old
benchmark processes and B's new test-package process were absent. The final
host census found zero selected-device or inventory ADB clients; the one ADB
server remained. The device lease was released with B running on its new card,
A unchanged, and no pending operation or unknown cleanup. The new image and
its same-D QEMU-created overlay are retained, together with the original config
backups; they are live storage, not sealed immutable evidence files.

The next step is a separately reviewed model-copy/integrity and explicit SDK
cache experiment using this identified APK, fresh volume-aware admission and
unchanged model/profile budgets. The primitive probe does not authorize
skipping those gates. The existing
[cache-admission refusal](CACHE_ADMISSION_DEVICE_2026-10-23.md) remains valid
for the original policy; this attachment does not retroactively admit a prior
inference attempt. Cache growth remains a budget, not a measured maximum.

This packet installed only the new test APK and executed its four bounded
metadata/primitive operations. It performed no model copy/read, inference,
original benchmark lifecycle operation, dependency change, save read,
original-image move or GitHub mutation. No physical-phone, ARM, model-quality
or runtime-profile acceptance follows from this storage result.

## Evidence binding

The sanitized private handoff projection is 4,405 bytes, SHA-256
`92fa5815136ec9520a7b4f954358c1c592319942ff4d195e56e0895994af2039`.
The private metadata index is 13,178 bytes, SHA-256
`79350e0f99a4d7abae7075e6c2228ece1c2909c546351cd1e3294e3001902d4a`,
binding 66 files across the three owned evidence areas. It covers command
journals, helper sources, actual instrumentation receipts, original config
backups, preservation snapshots and fixed failure summaries. Private paths,
actual volume/device identities, transport identifiers, raw launch arguments
and raw diagnostics are not published here.

The metadata journal SHA-256 is
`0728a779fb8f7ba596694627052525e5d5f412d38134b601e3ccdb2742cc650e`;
the app-probe journal SHA-256 is
`04998c132dc10aab57ef9b514e72e1322bc056d2efea250f30e037f5a4ed6ea3`.
Live image, overlay and emulator logs are explicitly excluded from the sealed
metadata index. Bounded log snapshots are included. The retained live storage
is not claimed immutable or silently deleted as evidence cleanup.

# Isolated receipt-test AVD environment

M05.05 prerequisite / M01.05 support. This helper is development tooling, without
app/runtime integration. It prepares a new, installed-image-only Android 35
Google APIs x86_64 target when the existing target cannot meet the unchanged
receipt qualification storage admission. Preparing this code does not qualify an
AVD, the receipt Android process case, a removable volume, or real-model inference.

The fixed target is `locallore_receipt_api35_v1`, console/ADB pair 5592/5593,
serial `emulator-5592`. Examples use the proposed fresh root
`D:/LocalLore-receipt-avd-next`. It must not exist at prepare admission. Historical
attempt roots are retained and cannot be reused. Actual four-method qualification
is recorded in the [verification report](../../native/RECEIPT_FRESH_TARGET_VERIFICATION_2026-10-24.md).
The content, registry, Android preferences, emulator preferences and temporary
directories all belong beneath that new root. It issues no SDK list, start,
stop, wipe, delete or adoption command for an existing AVD. The bounded read-only
default-registry metadata enumeration is described below. There is no ADB invocation.

## Two distinct admissions

`benchmarks/receipt_avd_environment.py` has these interfaces:

```text
python -B benchmarks/receipt_avd_environment.py plan-prepare \
  --root D:/LocalLore-receipt-avd-next \
  --sdk C:/Users/Avery/AppData/Local/Android/Sdk \
  --java-home "C:/Program Files/Java/jdk-21" \
  --output <private-prepare-proposal.json>

python -B benchmarks/receipt_avd_environment.py prepare \
  --proposal <private-prepare-proposal.json> --authorization <prepare-authorization.json>

python -B benchmarks/receipt_avd_environment.py plan-run \
  --proposal <private-prepare-proposal.json> \
  --prepared D:/LocalLore-receipt-avd-next/prepared-v1.json \
  --output <private-run-proposal.json>

python -B benchmarks/receipt_avd_environment.py run \
  --proposal <private-run-proposal.json> --authorization <run-authorization.json>
```

The displayed paths are examples for this host; quote arguments containing spaces.
Planning reads installed files and creates only the requested new proposal file.
It creates no AVD. Root reviews each immutable proposal before creating its
separate authorization. The authorization has exactly these keys:

```json
{"version":1,"phase":"prepare","proposal_sha256":"<64 lowercase hex>","allow_environment_calls":true,"root_go_pending":false}
```

Run uses `phase: "run"` and its own proposal digest. Changing any proposal bytes
invalidates its authorization. Importing the module does no work. The create-only
`prepare-start-v1.json` / `run-start-v1.json` receipts and existing-target checks
prevent a second execution. A failure preserves newly created files for review;
the helper has no repair, retry, overwrite-existing-target, or deletion command.

Prepare freshly measures available host memory and C/D free bytes. Its fixed
floors are 4 GiB available memory, 16 GiB C free, and 40 GiB D free; these are
boundary observations, not reservations against other host processes. It uses
the pinned JDK directly to call the installed `AvdManagerCli`, avoiding shell
interpolation, inherited Java options and default registries. It supplies `no`
to the custom-profile prompt and creates a new 8192 MiB SD image. It retains the
generated config before editing only that new config for 12 GiB userdata,
2048 MiB RAM and two CPUs. It never uses `--force`, `-wipe-data`, an old disk,
or a snapshot.

Prepare pins all files in the installed emulator, command-line tools, platform
tools, selected image (including `data/`), JDK and SDK license directories, plus
the helper and `runtime_spike.py`. A later run rejects changed or extra inputs.
No SDK package installation, download, license acceptance or dependency update
is provided. “Installed-image-only” does not assert guest network isolation.

Each internal worker rechecks the admitted proposal bytes and phase authorization
after its parent releases the job barrier, verifies that parent's recorded
PID/creation identity, and creates its own one-shot claim before invoking tools.
Failed prepare paths still retain raw child output, known-drain status and a
`prepare-result-v1.json` closure record. A successful run proposal binds that
completed prepare closure as well as the prepared metadata.

## Fresh userdata and existing global state

Read-only inspection on this host found emulator 35.3.12/build 12990079,
command-line tools 11.0, and Android 35 Google APIs x86_64 image revision 9
(minimum emulator 33.1.24). This image has `data/empty_data_disk`, without a
`userdata.img`. The reviewed emulator source creates a fresh ext4 userdata image
from that factory-data marker and the configured partition size. The helper does
not format or reuse an old userdata image. Actual guest boot, `df`, ABI/page size,
fresh package inventory and removable-volume eligibility remain root's later
device gates.

The installed Windows emulator resolves its console token from the OS profile,
not the isolated Android directories. Before any AVD mutation, the helper
requires the existing `.emulator_console_auth_token` to be a regular, nonlinked,
nonempty file of at most 4096 bytes. It hashes that file privately before and
after each phase. It never prints, copies, replaces, disables or empties it.
Missing or changed credentials cause refusal. Default `.android/avd` registry
INIs and referenced `config.ini` files are separately pinned (bounded metadata
only); disks, caches and saves are never read. Custom old registries outside
that default registry require root's separate preservation evidence. The scope
is isolated persistent AVD artifacts, not a promise that Windows or the SDK makes
no other incidental host writes.

## Retained process ownership

Run rechecks both local TCP ports, immutable prepared config/registry and the
initial SD bytes before launch. The new userdata path must still be absent.
It starts a barrier worker, assigns that worker to the existing
`runtime_spike.WindowsJob`, then releases its request. Descendants inherit the
job; no breakaway or detached successful return is allowed. The installed
Windows emulator launcher waits for its QEMU child; launcher exit is treated as
loss, never a reason to discover or adopt another process by name.

The supervisor retains its original live execution handle for at most 1200
seconds. `running-v1.json` is forced and created once after the owned launcher
exists. It explicitly says `guest_boot_verified: false`. It records exact owner,
worker and launcher PID/OS-creation-time/executable identities, proposal/prepared
digests, paths, serial, AVD name, pinned `adb_path`, and finite epoch deadline.
Root must retain and observe that original supervisor handle, then separately
admit the target controller before any guest calls.

The fixed stop request is a new `stop-v1.json` under the target root:

```json
{"version":1,"proposal_sha256":"<run proposal digest>","action":"stop"}
```

Only that closed request is accepted as an ordinary stop. Expiry, unexpected
child exit, malformed stop, excess output or cancellation stops ownership too,
with a failing result. In all cases the job is terminated and drained. This is
host process cleanup; it makes no graceful guest-flush, app cleanup, SDK/model
resource cleanup, or successful-test claim. Unknown drain remains a failure.
The original process handle is never restarted after an observation timeout.

### Live private output and abrupt owner loss

The supervisor exclusively creates and forces both `owner-stdout-v1.bin` and
`owner-stderr-v1.bin` before spawning the barrier child. It keeps those handles
open. Each retained chunk is written, flushed and forced before its byte count
advances; one lock enforces the existing combined 262,144-byte cap across both
channels. Files are never reopened or truncated during final cleanup. Existing
output files refuse a new execution, including a partial earlier attempt.

Short writes, write/flush/force/close failures and reader exceptions latch
`evidence_failed`, stop dispatch and still drain the owned job. The latch is
checked again after reader joins and file close, so a trailing failure cannot
leave an earlier `stop_requested` or `child_exited` status. Excess output remains
`output_limit`. Evidence failure and process cleanup are separate facts.

Terminal results add `output_capture_complete`. True means observed pipe bytes
were retained within the cap and the readers/files closed without capture
failure; it does not mean the child succeeded or flushed its own buffers.
Byte counts describe successfully forced prefixes. A failed write/force can
leave additional uncertain bytes in a file; false capture status does not
authenticate that file as a complete stream. If a reader remains alive after
its bounded join, cleanup and capture fail, counts are null, and the owner does
not wait on that reader's capture lock or close a file still being written.
The byte cap does not promise a bounded operating-system disk-force latency.

If the supervisor itself is killed, an already forced prefix can survive even
when no terminal result exists. Such files establish neither a live lease nor
successful tests, complete output, descendant cleanup or an orderly guest
flush. Preserve that failed attempt; do not recreate its owner, adopt another
process, fabricate a stop/result or silently retry the saved target. Raw output
is private local diagnostics, never an automatic issue upload. The
[host loss-case evidence](../../native/RECEIPT_SUPERVISOR_EVIDENCE_2026-10-24.md)
keeps synthetic process tests separate from real emulator/model qualification.

## Device-controller lease

```python
lease = open_live_owner(proposal_path, running_path, expected_running_sha256)
serial = lease.descriptor["serial"]
adb = lease.descriptor["adb_path"]
lease.check()  # None on success; EnvironmentRefused on loss/refusal
```

The controller derives identity from this descriptor, never an arbitrary serial
or alternate client. Opening hashes source/tool/image bindings once and validates
the prepared record. Every `check()` cheaply rechecks proposal/descriptor bytes,
prepared/config/registry metadata, exact live process identities, stop/result
absence and deadline. It must run before and after every separately admitted
device command. A lease is not root authorization to run a command.

Initial SD content is checked only before launch. Guest SD/userdata writes are
expected; opening a lease after launch and later checks do **not** compare live
disks with their initial hashes. Closure rehashes immutable source/tool/config,
registry and global-token inputs, after known process-tree drain. Mutable disks
are retained state, without an unchanged-content assertion.

## Verification and limits

### Preserved first preparation refusal

The first root-admitted preparation used `D:/LocalLore-receipt-avd-20261024`.
Its SDK child completed with return code zero, known cleanup and 4,219 ms. The
helper then refused `invalid_config`; no boot occurred. The generated command-line
tools 11 profile contained `avd.id=<build>` / `avd.name=<build>` without an
`AvdId` entry. The helper's required `AvdId` was an incorrect assumption. The
retained SD image was exactly 8,589,934,592 bytes, while the generated profile's
editable `sdcard.size` default still said `512 MB`. No SD resize or guest-capacity
failure was observed. The failed namespace remains untouched and cannot be
adopted or retried by the helper.

The focused correction accepts the source-known generated identity placeholders
only after exact registry path/target/encoding and ABI/architecture/tag/image
checks. Before changing its newly generated config, it also checks the actual SD
file size and rejects any existing userdata. It retains the raw generated config,
normalizes `AvdId` / `avd.id` / `avd.name`, binds the userdata/cache/SD paths to the
new content directory, makes SD metadata agree with the requested 8192 MiB image,
and disables first-boot snapshot choices. Foreign identities, disk-init paths,
old disk paths, mismatched images or registries still refuse before that write.
The exact 3,201-byte generated profile is a host regression fixture (SHA256
`5774eccd6c920ec3157a7a43710620645284c7e064a9f06933915f12d05aa6ac`).
That correction was subsequently prepared in the v2 root; neither the failed v1
nor the retained v2 root is eligible for reuse by the next preparation.

### Preserved v2 launch refusal

The v2 owned launch produced a running descriptor, then the installed emulator
refused the supplied `-partition-size 12288`: its raw output says the accepted
range is 10–2047 MB. The supervisor recorded `child_exited`, worker return code 2,
known cleanup and verified closure (890 ms); no guest command or userdata
creation followed. That descriptor established a live launch at publication,
not boot success. The v2 target and raw evidence remain preserved.

The exact emulator 35.3 source parses this flag using a C `long` and caps it at
`LONG_MAX / ONE_MB`, consistent with the Windows refusal. The flag affects both
system and data size, and would override the configured userdata size. The
correction therefore omits the flag entirely, preserving the nonzero
`disk.dataPartition.size=12G` and explicit fresh `-data` path. The same source
retains that configured size when no override is present; fresh ext4 creation
consumes it. It does not substitute 2047 MB or reduce any admission floor.
Actual successful image creation, boot and guest capacity still require new
evidence. Only a separately reviewed preparation/run for an absent v3 root can
exercise this correction; no prior target or authorization is reused.

Host tests use fake SDK files and synthetic Python children. They test mismatch
refusal before mutation, replay refusal, source/config/token drift, exact owner
identity and expiry, mutable guest-disk treatment, budgets and actual Windows
descendant termination. They never invoke an SDK executable or create/boot an
AVD. Root records any actual preparation, retained ownership, guest capacity and
receipt instrumentation evidence separately. No model weights, inference SDK,
story workspace, old emulator lifecycle or old app data action is authorized by
this document.

## Primary references

- [Android avdmanager](https://developer.android.com/tools/avdmanager): content
  path, create semantics and explicit force option.
- [AVD manager CLI source](https://android.googlesource.com/platform/tools/base/+/mirror-goog-studio-master-dev/sdklib/src/main/java/com/android/sdklib/tool/AvdManagerCli.java):
  generic hardware/profile defaults and the separate requested SD image parameter.
  The locally pinned emulator `lib/hardware-properties.ini` defines `avd.id` and
  `avd.name` with `<build>` defaults and the temporary data-partition path.
- [Android emulator command line](https://developer.android.com/studio/run/emulator-commandline)
  and [environment variables](https://developer.android.com/tools/variables).
- [Emulator 35.3 userdata creation](https://android.googlesource.com/platform/external/qemu/+/refs/heads/emu-35-3-release/android-qemu2-glue/main.cpp):
  `creatUserDataExt4Img` / `createUserData`, factory empty-data marker.
- [Emulator 35.3 option handling](https://android.googlesource.com/platform/external/qemu/+/refs/heads/emu-35-3-release/android/android-emu/android/main-common.c):
  lines 779–800 bound the optional partition flag; lines 1023–1035 retain nonzero
  configured userdata size when the flag is absent.
- [Windows launcher wait](https://android.googlesource.com/platform/external/qemu/+/refs/heads/emu-35-3-release/android/emu/utils/src/android/utils/exec.cpp):
  `_wspawnv` followed by waiting for the child.
- [Console token](https://android.googlesource.com/platform/external/qemu/+/refs/heads/emu-35-3-release/android/emu/telnet/auth/src/android/console_auth.cpp)
  and [Windows OS profile resolution](https://android.googlesource.com/platform/external/qemu/+/refs/heads/emu-35-3-release/android/android-emu-base/android/base/system/System.cpp).
- [Windows job objects](https://learn.microsoft.com/en-us/windows/win32/procthread/job-objects)
  and [job limits](https://learn.microsoft.com/en-us/windows/win32/api/winnt/ns-winnt-jobobject_extended_limit_information).

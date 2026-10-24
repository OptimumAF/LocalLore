# Isolated receipt-test AVD environment

M05.05 prerequisite / M01.05 support. This helper is development tooling, without
app/runtime integration. It prepares a new, installed-image-only Android 35
Google APIs x86_64 target when the existing target cannot meet the unchanged
receipt qualification storage admission. Preparing this code does not qualify an
AVD, the receipt Android process case, a removable volume, or real-model inference.

The fixed target is `locallore_receipt_api35_v1`, console/ADB pair 5592/5593,
serial `emulator-5592`. The proposed fresh root is
`D:/LocalLore-receipt-avd-20261024`. It must not exist at prepare admission.
The content, registry, Android preferences, emulator preferences and temporary
directories all belong beneath that new root. The helper never lists, starts,
stops, wipes, deletes or adopts an existing AVD. There is no ADB invocation in it.

## Two distinct admissions

`benchmarks/receipt_avd_environment.py` has these interfaces:

```text
python -B benchmarks/receipt_avd_environment.py plan-prepare \
  --root D:/LocalLore-receipt-avd-20261024 \
  --sdk C:/Users/Avery/AppData/Local/Android/Sdk \
  --java-home C:/Program Files/Java/jdk-21 \
  --output <private-prepare-proposal.json>

python -B benchmarks/receipt_avd_environment.py prepare \
  --proposal <private-prepare-proposal.json> --authorization <prepare-authorization.json>

python -B benchmarks/receipt_avd_environment.py plan-run \
  --proposal <private-prepare-proposal.json> \
  --prepared D:/LocalLore-receipt-avd-20261024/prepared-v1.json \
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
- [Android emulator command line](https://developer.android.com/studio/run/emulator-commandline)
  and [environment variables](https://developer.android.com/tools/variables).
- [Emulator 35.3 userdata creation](https://android.googlesource.com/platform/external/qemu/+/refs/heads/emu-35-3-release/android-qemu2-glue/main.cpp):
  `creatUserDataExt4Img` / `createUserData`, factory empty-data marker.
- [Windows launcher wait](https://android.googlesource.com/platform/external/qemu/+/refs/heads/emu-35-3-release/android/emu/utils/src/android/utils/exec.cpp):
  `_wspawnv` followed by waiting for the child.
- [Console token](https://android.googlesource.com/platform/external/qemu/+/refs/heads/emu-35-3-release/android/emu/telnet/auth/src/android/console_auth.cpp)
  and [Windows OS profile resolution](https://android.googlesource.com/platform/external/qemu/+/refs/heads/emu-35-3-release/android/android-emu-base/android/base/system/System.cpp).
- [Windows job objects](https://learn.microsoft.com/en-us/windows/win32/procthread/job-objects)
  and [job limits](https://learn.microsoft.com/en-us/windows/win32/api/winnt/ns-winnt-jobobject_extended_limit_information).

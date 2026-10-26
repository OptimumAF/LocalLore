# Single-guest admission and connected-phone verification

Refs #5 (M01.01/M01.05), #9 (M05.05 prerequisite), root claim6404879571.
This follow-up replaces an unsupported host admission margin and records actual
testing. Full milestone acceptance remains pending. GitHub tickets own status;
the retired Markdown trackers remain pointers.

## Corrected admission policy

The former `2*guest+2GiB` cutoff demanded18GiB for an8GiB guest. The
[version-aligned source review](EMULATOR_COMMIT_REASSESSMENT_2026-10-25.md)
finds one guest-sized allocation and a post-failure diagnostic heuristic, not a
mandatory second retained guest allocation. `guest_plus_reserve_v2` now requires
one guest plus the existing explicit2GiB project reserve:4/10GiB for the existing
2/8GiB profiles. This is an admission margin, not an OS minimum, reservation,
measured peak overhead, or guarantee of allocation success.

The strict system API validation, physical-memory and disk floors, CPU/profile
checks, parent/worker checks, source bindings, one-shot ownership and deadlines
are preserved. Once the guest has committed, another full startup allowance is
not demanded. No other emulator was stopped and no system/pagefile setting or
guest profile was changed. The older mapping failure remains cause-unknown.

## Host verification actually performed

Python3.14.7 on Windows, source4fdcd498 and its integrated predecessors:

| Check | Actual result | Retained output SHA256 |
| --- | --- | --- |
| Focused helper/environment/transfer suite |146 pass,24.761s; owned25274ms/0/known cleanup | `70adb24c94b8520e8641f88c6c043d2fb23fc97ec5a9d4407c710a272105572b` |
| Full `unittest` discovery in `scripts/tests` |1062 pass,96.184s; owned97393ms/0/known cleanup | `10fe7138b5e8831375a48d649c11d9712e60069688e6beab634758e9adf345d3` |
| Independent unchanged18-case regression against old020667dd | RED:11 error records including subtests; child1, known cleanup | `b7ed9a65e16ab6e6238e4c3b09d60964b87e5edc8c489b6233d7e2a3bab30621` |
| Same regression against corrected helper |18 pass,0.006s; owned297ms/0/known cleanup | `b7090c841f29136418e9e826187c030d6b5f33221f63fcd9bd3727590afe9efc` |

Central commands were `python -B -E <private-owned-launcher> focused` and
`python -B -E <private-owned-launcher> full`. The launcher uses the existing
bounded Job controller, a fixed stdin barrier,180s deadline and262144B output
cap; its child selects the three named modules or
`unittest.defaultTestLoader.discover('scripts/tests')` respectively. Both
stdout captures have zero stderr. All112 captured Python source hashes match
before/after. Independent regression source SHA256 is
`441f73978d7de431882ae709c209f196fab0e4c6f44df4085efd807cbe1c046f`;
corrected helper SHA256 is
`847ed92b720ce88a7a6f6c02e0b541138854cb2d29796803f610c9a9cfafe619`.

Cases cover exact4/10GiB boundaries and one-byte-below values, historical
observations rejected only by the old excess margin, below-guest negatives,
invalid API/counters/ABI/overflow and worker rechecks. No Rust/Gradle build was
rerun: this packet changes no Android/Rust source. Their Git diff from audited
APK source44103b8c is empty.

## Actual unchanged-profile emulator startup

A separately named fresh API35/x86_64 target uses the selected installed
emulator35.3.12/build12990079, unchanged8GiB RAM/4CPU/12GiB userdata/8GiB SD,
1800s owner, and a2s sampled40GiB free-space floor on each backing volume.
Sampling is not a storage reservation or continuous hard ceiling.

Actual preparation observed14,804,549,632B commit headroom against the revised
10,737,418,240B requirement and30,835,597,312B available physical RAM. The old
19,327,352,832B requirement would reject that sample. Fresh launch checks then
admitted the target. **All12 original preflight checks passed**,44 bounded
commands, owner50996ms/worker0/known cleanup/output capture/stderr0. This proves
actual boot/preflight with other emulators running, rather than merely changing
test expectations. The preflight stages only61 trusted synthetic bytes, with no
model or SDK inference.

Source freeze4fdcd498 binds64 required files, eight unchanged Android compilation
inputs and two audited receipt APKs; manifest SHA256
`7114886339b9dff970768ec313f01e16fbc7aa7dc404a8cc70b44f1708966831`.
Receipt app/test SHA256:
`c9325b6a50483afc0d928ab3d16c14c5a43caebacc4a96d11f16328f976f15fa` /
`e5d09b0f436237b51c647b4cc43a74e8f76b08bfdfe045907aa89ee6724f359d`.
The actual run proposal is
`aeeeb4663e61910572e4898771d3f8ae3002b23a1efc1856b73430e1d3dff8fa`.
Historical failed targets remain quarantined.

## Actual connected-phone nonmodel Rust checks

Following the [read-only inventory](../runtime/android/PHYSICAL_DEVICE_INVENTORY_2026-10-25.md),
the authorized Samsung SM-S918U1/API36/ARM64/4096-byte-page phone passed **all nine**
selected `NativeBoundaryTest`(4)/`DurableNativeTest`(5) methods, no failures,
skips or unfinished cases. These exercise actual Rust JNI prepare/commit,
idempotency, malformed/foreign/destroyed inputs, cancellation before commit,
twenty cancel/destroy resource cycles, SQLite reopen, independent stories,
lost-ack recovery and stale-operation cancellation. Inference is fake.

Exact instrumentation selection:

```text
am instrument -w -r -e class org.locallore.app.NativeBoundaryTest,org.locallore.app.DurableNativeTest org.locallore.app.modelverify.test/androidx.test.runner.AndroidJUnitRunner
```

All26 bounded host clients returned0 with known cleanup. Instrumentation client
3238ms; JUnit reports1.752s. Raw6398B SHA256:
`66b6e251174c2857698197a2775d22e4c3efde919c26591504085190e42b055d`.
The strict parser verifies each start/end pair, not merely `OK(9 tests)`.
Regular isolated app/test APK hashes:
`1af7bd97a9c8f40b95387376181a4791d362a9459078036c183695245e39c26e` /
`8c14c03502faee7661b58a6862c5b35e9fec6e6371e40b9c2718daadd56ad1e5`.
Installed APK readbacks matched. Installs were create-only into previously
absent packages, without replacement, permission grants, data reset or uninstall.
The newly installed pair remains installed; bounded force-stop commands completed.

The first admission stopped before installation because the read-only Samsung
battery dump exceeded8192B, with known client cleanup. Its proposal/raw refusal
remain. A fresh namespace used the previously reviewed131072B capture cap;
no deadline or memory gate was relaxed. The executed private one-off controller
is not a reusable production harness: its cleanup-only scope resets a local
clean flag, while cumulative cleanliness stays sticky. This must be fixed before
reuse on uncertain-client paths; all actual26 clients here were clean. Its
`pidof ... || true` check masks unexpected errors, so no independently reliable
guest-process-absence claim is made from that empty output.

Serials, raw diagnostics and personal device paths stay private. No model was
copied/read/loaded on the phone, no SDK inference ran, and no other app/process,
server lifecycle or settings were controlled. This is ARM64/4KiB engine evidence,
not model throughput,16KiB physical-device or sustained-use qualification.

## Actual synthetic transfer controls and refusal

Separate source/owner-bound grant
`a7049f1518b3329d641e7dab826f6433209843e6441ec822fe30591e3a603a10`
ran the existing fixed protocol once, without weights or SDK calls. Each large
source is the original1,073,741,824B fixture, SHA256
`93b6ba41cf54e72a26ab955cdf953420847be6229f592ea79770362c91558c3f`.

| Control | Actual client / owned stream time | Destination proof |
| --- | --- | --- |
| `exec-in` CAT |58460 /81582ms | Full1GiB size/SHA match, post-facts pass |
| `exec-in` DD_1M |58107 /84431ms | Full1GiB size/SHA match, post-facts pass |
| Shell binary gate |146 /27532ms | FAIL:26B reported for768B source |
| Large SHELL_CAT | Unattempted | Refused by binary prerequisite |

The shell advertises shell_v2 and passes exact exit42/0 controls. The same
owned worker/held regular-file stdin path then sends the fixed768B pattern
`bytes(range(256))*3`, expected SHA256
`f3a25aa93aa2fbba28d79260535bbd6a5eb0fc1c24a8b0f04e12b484c1dfe363`.
Its client returns0, but the separate destination proof reports26B/SHA256
`b858da80d8a57dc546905fd147612ebddd3c9188620405d058f9ee5ab1e6bc52`.
Proof stdout127B SHA256
`3c65bd467527f624d2270b97f4e81e3c5591aaa92317251f7c38bdeeb3bc3c56`
is retained. Client success is correctly insufficient. The binary check's cause
is not established; no payload transformation is silently accepted.

Overall probe **stopped**, stage `binary-proof`,43 bounded commands, two verified
large controls, zero probe installs/instrumentation/model/SDK actions. Outer
owner229363ms/worker2/known client cleanup/complete output capture/stderr0.
Thus CAT/DD evidence survives, but the full three-method experiment did not pass.
No dependent guest reads, retry, import or inference followed the refusal.

The coordinator verified the exact host owner identity and issued its one-shot
stop record. Only this new LocalLore owner was controlled. Terminal disposition:
`stop_requested`,936315ms, worker1,15859B stdout/1063B stderr, known cleanup,
complete output capture and verified host closure. No guest flush is claimed.
Storage monitor finishes healthy, no monitor failure. Old and new failed targets
remain quarantined. The other project's emulator and system settings are untouched.

## Limits and next runnable work

The excess admission restriction is corrected and actual startup is established.
Independent reviews rechecked host sources/output, all64 preflight bindings,
12checks,37 physical command raw bindings and nine exact physical case pairs.
The phone controller records no fresh UID or final33-package map; neither is
inferred. Installed-binary-to-official-source commit provenance remains unproved.

M01.01 inventory/nonmodel execution and M01.05/M05.05 supporting fixes are
**in_review**, not accepted milestone completion. No new real-model import,
SDK dialogue, sustained memory/thermal,16KiB physical device, quality evaluation,
runtime/model selection or reference-phone playable-scene gate passes here.
Model weights, APK payloads, private raw diagnostics and unique device identity
are excluded from public changes.

The private metadata/source/output evidence index seals392 selected files /
2,044,539B. Index111177B SHA256
`29fcc76fb8bfb5a68506cd0fb9393c8ba2297a00eb703850085716a69cfbe1db`;
every entry was reread and matched. This excludes guest images, SDK/APK payloads,
the original1GiB source, model weights and private phone identity inventory.

An independent source-only follow-up finds that the reported26B hash exactly
equals SHA256 of `bytes(range(26))`, ending before the first0x1A. Pinned official
[ADB client source](https://android.googlesource.com/platform/packages/modules/adb/+/1cf2f017d312f73b3dc53bda85ef2610e35a80e9/client/commandline.cpp)
sets stdin binary mode in the `exec-in` copy path, while RemoteShell reaches a
stdin thread without that prologue. Its
[Windows file/pipe read path](https://android.googlesource.com/platform/packages/modules/adb/+/1cf2f017d312f73b3dc53bda85ef2610e35a80e9/sysdeps_win32.cpp)
uses CRT `read`; Microsoft documents
[Ctrl-Z as EOF in text mode](https://learn.microsoft.com/en-us/cpp/c-runtime-library/reference/read?view=msvc-170).
This strongly predicts the retained prefix and clean EOF, but the installed
binary's runtime CRT mode was not observed. It is a source-backed hypothesis,
not a proven installed-binary cause or permission to accept corrupted payloads.

Next runnable task: inspect the installed-version Windows ADB shell stdin path
against the retained26B binary failure with original host controls. Preserve the
working `exec-in` path; do not substitute shell for model transfer. A subsequent
fresh model attempt needs its own source/target-bound admission and full-copy,
import, inference and restart proofs;1GiB throughput is not a2.59GB model result.

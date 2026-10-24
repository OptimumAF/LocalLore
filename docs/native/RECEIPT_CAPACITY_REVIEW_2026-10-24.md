# Independent receipt capacity and isolated-target review — 2026-10-24

Refs #9 (M05.05 prerequisite), #5 (M01.05 supporting).

## Scope and current disposition

This report owns no runtime or environment implementation. The reviewer performs
no builds, shared-cache changes, device/ADB/AVD operations, model transfers or
SDK inference. Source, official documentation and retained evidence are reviewed
independently. Review findings grant no execution authority.

Four receipt methods passed in one ordinary instrumentation cohort on the fresh
isolated Android 35 x86_64 target. The reviewer independently checked all 59 raw
clients, the runner, four proof documents and four ready markers. All 43 required
proof checks passed, including actual owned-child death and source-free recovery.
The original guest and emulator-owner executions are terminal with known cleanup;
the final sealed selection independently matches all 187 files.

The existing B target remains short of the unchanged update reserve and received
no further lifecycle, install or test action. Earlier preparation, launch and
console-framing refusals are preserved below. Their corrections and the fresh
PROCESS pass do not establish the cause of the historical B failure. This is a
63-byte synthetic receipt qualification; no production storage route, real model,
inference SDK, physical phone or full M05/M01 milestone is qualified.

## Fresh read-only settlement source review

The exact disabled settlement proposal independently rehashed all 47 bindings,
87,409,219 bytes, with zero mismatches. Proposal SHA-256:
`eae5d2c9fe45ba33287e449f207670bc717b270b6513b332d71d7a8bf45f35e1`.
Its base is `be8efa84b22a812a12ae3056fc8fef061a6880d0`. The actual controller
is unchanged from the previously reviewed closed recovery profile. Expected
35 package hashes and UIDs match the sealed last recovery facts and original
installed map. The fresh output was empty and authorization absent at review.

The reviewed path permits bounded current metadata and exactly six historical
v1 proof files, requires v2 proof-namespace absence, and reports recognized
process counts without acting on them. It cannot install, instrument, clear,
stop or adopt data. The 90-second outer and 75-second aggregate limits remain.
It binds retained 471-script and 22/20-mock evidence; those are historical runs,
not tests newly executed by this packet or reviewer. Old proof candidate-absence
assertions remain historical; this profile does not remeasure current internal
or Context-derived external candidate-root absence. No concrete source/binding
blocker was found for this exact read-only scope.

The coordinator confirmed the original settlement terminal. The retained owned
result completed zero with known cleanup in 8,562 ms; the reviewer checked all
29 raw client outputs/statuses/hashes. Zero installs and zero instrumentation
ran. All 35 package hashes and UIDs remain equal; owned and passive process
counts were zero before/final. The three historical proof check sets validated
under one recorded parent; the fresh v2 proof root was absent. None is a fresh
PROCESS pass or a current candidate-root absence measurement.

Final userdata availability is 1,223,847,936 bytes: 15,888,384 above the unchanged
controller floor, but 60,866,995 below floor plus the 76,755,379-byte incoming
pair. Installer overhead remains additional and uncalibrated. B remains blocked
before another update admission. No cause of the historical decrease or future
reclamation is inferred.

All 120 sealed selection files, 87,538,206 bytes, independently matched their
recorded sizes/digests, index SHA-256
`31417777affa16cafada6bb49280661c0138e968e126df875db838c25ec5516a`.
The complete 47-input archive, 87,409,219 bytes, also independently rehashed and
matches every original proposal binding; index SHA-256
`cb6fa4a1b7a3263a3b9460cae458c35e92840ae608c9134e1605da488730b26f`.

## Official tools and installed compatibility

Read-only local metadata records Android Emulator 35.3.12 (build 12990079),
Command-Line Tools 11.0, Platform-Tools 37.0.1, and the installed Android 35 `google_apis`
`x86_64` image revision 9. The image declares emulator minimum 33.1.24. This
metadata supports using existing tools without a download; it does not prove a
new boot, hardware acceleration or guest free capacity. No executable was
invoked by the reviewer.

The installed image lacks `userdata.img` but contains `data/empty_data_disk`.
Official emulator 35.3 source supports creating empty ext4 userdata from that
factory-directory route at the configured partition size. Missing the template
alone is therefore not a blocker or a reason to borrow an existing AVD image.
Pin factory inputs and verify actual generated data, boot and guest capacity.
[Factory userdata creation](https://android.googlesource.com/platform/external/qemu/+/refs/heads/emu-35-3-release/android-qemu2-glue/main.cpp).

Current official documentation marks legacy `emulator` and `avdmanager` commands
deprecated in favor of the Android CLI, while retaining their documented
interfaces. Adding another tool is unnecessary for this bounded installed-tool
experiment. `avdmanager -p` selects the content directory; `-f` permits overwrite
and must not be used for a create-only target. [AVD manager](https://developer.android.com/tools/avdmanager).

Registry and preferences also need isolation. Android documents distinct
`ANDROID_AVD_HOME`, `ANDROID_USER_HOME` and `ANDROID_EMULATOR_HOME` locations;
redirecting content alone does not establish that old registry/preferences are
untouched. Require process-local values under the new trusted directory and
verify the generated registry/config paths. Do not change global settings or
repurpose system home variables. [SDK environment variables](https://developer.android.com/tools/variables).

The emulator supports explicit data and SD images, a RAM override, and an even
console port with its adjacent ADB port. Configured partition size is not
measured guest availability. Missing SD images can still allow launch without a
card, so boot success alone cannot qualify the exact-one removable-volume gate.
Avoid wipe/resize, old snapshots and existing images. [Emulator command line](https://developer.android.com/studio/run/emulator-commandline).

The official `mksdcard` interface creates FAT32 images and accepts byte/K/M/G
sizes. An 8 GiB request is within its documented range, but requires a fresh
exclusive destination and actual post-boot volume qualification. No old card or
benchmark copy may be adopted. [SD image tool](https://developer.android.com/tools/mksdcard).

A separate console-auth path must also be preserved. The official emulator
35.3 branch joins `System::getHomeDirectory()` with
`.emulator_console_auth_token`. Its Windows implementation asks the shell for
`CSIDL_PROFILE` first; only a failed lookup falls back to `HOMEDRIVE` plus
`HOMEPATH`. A child `USERPROFILE` override therefore is not a proven redirect.
The coordinator chose a bounded existing regular, non-link, nonempty token as a
read-only prerequisite, with private before/after digest preservation. Missing
or invalid state must refuse before mutation; no empty token, auth disabling,
content output or copying is implied. [Console auth source](https://android.googlesource.com/platform/external/qemu/+/refs/heads/emu-35-3-release/android/emu/telnet/auth/src/android/console_auth.cpp),
[Windows home lookup](https://android.googlesource.com/platform/external/qemu/+/refs/heads/emu-35-3-release/android/android-emu-base/android/base/system/System.cpp).

## Environment and ownership design review

A proposed 12 GiB userdata / 8 GiB SD / 2 GiB RAM / two-CPU target is a requested
configuration, not measured capacity. Its content, registry, temporary files
and evidence must remain in a fresh isolated namespace. Existing AVD records,
data, processes and package identities remain outside action authority.

Creation and boot must be distinct from later target bootstrap/qualification.
An exact owned process-tree handle must bound launcher children, retain terminal
and cleanup evidence, and never infer ownership from an emulator process name
or a reused serial alone. A new target needs its own identity and package/UID
baseline; the old 35-package history must not be projected onto an empty target.
Resource floors and actual guest capacity/volume checks remain required before
any APK admission.

The existing Windows job helper terminates all owned descendants on close,
including ordinary successful completion. A boot worker cannot return success
and silently leave a detached emulator for later bootstrap. Its reviewed owner
must remain alive through admitted child work, or stop the fresh target before
return. Assignment must precede release of a trusted worker's launch barrier;
attaching a job after an unguarded emulator launch would leave a child-creation
race. No global process-name termination or breakaway is an ownership proof.
Microsoft documents default child membership and kill-on-job-close semantics;
neither breakaway flag may be enabled. [Windows job objects](https://learn.microsoft.com/en-us/windows/win32/procthread/job-objects).

Official Windows emulator launcher code waits on its exact spawned QEMU handle;
pinning the live launcher is source-supported. Unexpected launcher exit must
still refuse, without discovering a replacement by name. [Launcher implementation](https://android.googlesource.com/platform/external/qemu/+/refs/heads/emu-35-3-release/android/emu/utils/src/android/utils/exec.cpp).

## Concrete draft findings

The initial helper could verify one root's prepared evidence while launching
another root from a mismatched run proposal. The revised draft compares every
shared prepare/run field and requires exact prepared/config/registry/SD paths.
It also adds default old-registry/config metadata preservation, validates a
closed stop request before ordinary completion, and retains run closure failures.
These were source findings; no AVD execution demonstrated them.

Two further corrections were required: prepare now retains source, token and
old-registry closure observations even after a tool/config refusal; the barrier
worker verifies captured proposal bytes, matching authorization, recorded live
parent identity and a create-only worker claim before any SDK launch. Passing
only a path and validating its schema did not reject a changed proposal or an
internal-worker call without authorization. Cross-root, drift, missing-auth,
replay and failed-phase cases now have source tests.

The reviewed initial helper source digest is
`5b3d4bb7bd406a0ea674375b6cbf55986be0126f56c0f3edcef12df0f2e3dfbd`.
Its retained host run records 43 passing tests with no failures or skips,
completed zero and known cleanup in 4,047 ms. The reviewer checked the actual
source/test digests, result and 5,129-byte log, SHA-256
`dfcbdc4d6552e8dc360105c8a33e4b31555a7cb7fc40460c5d74f1e6c39d8391`.
Two tests use actual synthetic child/grandchild processes to check ordinary
launcher exit and expiry cleanup through the Windows job; two more check exact
and malformed stop requests. No SDK executable or AVD is exercised by those
tests. No further concrete source blocker was found before integration; actual
environment proposal/admission/execution evidence remains separate.

The separate fresh-target controller requires a live environment lease before
and after every retained client, derives its fixed target/client from that
lease, and uses an empty factory package map followed by exactly two newly
discovered UIDs. It does not weaken the old 35-package parser or use replacement,
cleanup or lifecycle commands. A closed read-only boot query waits at most 60
seconds inside the existing aggregate/outer budgets; owner readiness alone is
not guest boot proof. Actual AVD identity and all metadata/capacity checks still
precede either install. The retained 13 mocked test methods passed in an owned
4,828 ms run, completed zero with known cleanup; no reviewer tests ran. Log
SHA-256 `4a16ecd863af5a6164eb1742a6ee51f1ffd89a5a28ef27bb5b9f99cae3eaecd9`.
This is controller evidence, not a new-target Android result.

## Frozen prepare admission review

The integrated helper is `3dcf3bddc0d139ef9c7e29ce5362b0f30531402d`.
The final Windows central gate records 527 passing script tests, zero skips,
30.570 seconds; its owned child completed zero with known cleanup in 31,656 ms.
The reviewer read the actual result and raw summary. The final Windows-only
class annotation differs from the earlier helper test receipt; this central
run covers the final annotated source without skipping it on Windows.

The disabled prepare proposal independently rehashed all 909 bindings,
5,046,133,327 bytes, with zero mismatches. Proposal SHA-256:
`07cfce44e840baef5fc9d3e5d24b92a40a15ebe289021649480281735193c2a7`.
The complete installed-input file set also independently matches the proposal.
Existing console-token metadata/digest and eight default registry/config
bindings match; no credential contents are printed or copied. The exact fresh
target root is absent and authorization did not exist at review.

Prepare uses pinned Java 17.0.6 directly, the installed factory image and
create-only `AvdManagerCli` arguments, without force or shell interpolation.
The proposal fixes 12 GiB userdata, 8 GiB SD, 2 GiB RAM and two CPUs, with host
boundary floors of 16 GiB C free, 40 GiB D free and 4 GiB available memory.
These remain observations rather than reservations. No concrete source/binding
blocker was found for this exact prepare phase. It grants no boot, device-test
or new-runtime authority.

## First actual prepare refusal

The coordinator confirmed the original prepare execution ended with failure.
The SDK child itself completed zero with known cleanup in 4,219 ms; the helper
then refused `invalid_config`. Its closure record is true, with no accepted
prepared record. The retained output is 87 bytes, SHA-256
`f8a408665fb80180169a6ef44d3f071b0da14c493f2dabc40e26871ce45952c8`.
No emulator boot or guest test occurred.

The actual config has no `AvdId`, and contains `avd.id=<build>` and
`avd.name=<build>`. ABI, tag and image-directory fields match the admitted image;
the new registry has the exact intended path and Android 35 target. The pinned
SDK `hardware-properties.ini` documents those identity defaults and that they
are set before launching the core. Requiring the absent extra field was an
incorrect helper schema assumption, rather than evidence of a foreign target.

The created SD file is exactly 8 GiB, while generated `sdcard.size` still says
512 MB. Data path is the `<temp>` placeholder; initial data/RAM fields also
contain defaults. A correction must validate the actual registry/image schema
and normalize only this new config to explicit admitted identity, data path and
consistent size fields. The original generated config remains evidence. A fresh
v2 directory, proposal and admission are required; the failed directory is not
repaired, reused or deleted.

All eight failed target files, 8,589,938,877 bytes, independently rehashed with
zero mismatches, index SHA-256
`dbe40f7a9fc9107deef7c1bb4ff9d8eb45cc8501f4d776f6c046a1fd96da5b55`.
Both archived admitted source bindings match the original proposal. The
1,403-file pre-fix source snapshot, 16,495,486 bytes, also independently matches
its records; index SHA-256
`f2f3acf3c811b7c209c01d944738f86542f239df9c80c7b76f3fb5a0245fb894`.
The 527-test result above remains explicitly pre-fix evidence. Corrected source
and any later preparation/boot/qualification remain separate gates.

## Config correction and fresh v2 proposal

The focused correction checks the exact new registry key set/path/target,
pinned ABI/architecture/tag/encoding/image directory, known placeholder or
admitted identities, and only temporary/new-owned data/cache/SD paths. It
normalizes this fresh config to explicit identity, 12 GiB userdata, 8 GiB SD,
2 GiB RAM/two CPUs and disabled first-boot snapshots. It checks actual SD size
and userdata absence before retaining and rewriting that generated config.
The failed v1 target remains untouched.

An independent test-oracle finding was also fixed: the existing-userdata
refusal test originally had an invalid tiny SD, which could mask a missing
userdata check. Its corrected case uses a fresh sparse host-test file with
valid logical 8 GiB size; the separate tiny-SD refusal case stays invalid. The
retained corrected suite records 51 passes, zero failures/errors/skips, 16.094
seconds; owned child completed zero with known cleanup in 16,500 ms. Log SHA-256:
`4b16fb91f483c61e3a0b2703e1ef357da6c18875d0a7acc9c90437a16c9d0399`.
No SDK executable or AVD is used in those host tests.

The disabled v2 prepare proposal independently rehashed all 909 bindings,
5,046,134,957 bytes, with zero mismatches. Proposal SHA-256:
`979e2080ed395c4d8445993faed75aba6bb806789aeada47e225127dd5684bfb`.
Only the helper binding changes from the first proposal; normalized helper
SHA-256 is `f111bcabb45f63ad47c15c71b298e81ecaf2f696f557e434e39769b763ceaca7`.
The distinct v2 root is absent; settings, old registry metadata and token
binding remain equal. Authorization was absent at review. No concrete source
or binding blocker was found for this prepare phase, subject to the final
central gate; no run, boot or Android qualification is inferred.

## Actual v2 preparation and launch-input review

The final corrected central gate records 535 passing tests, zero failures,
errors or skips, in 37.161 seconds. Its original owned child completed zero
with known cleanup in 38,062 ms. The reviewer checked the retained result,
summary and final helper/test hashes. Output SHA-256:
`ecbd4ad0acea6b91ae17a5b1c327c793541553f87288e24388739c630a07cd27`.
All 1,403 final source snapshot files, 16,510,538 bytes, independently match;
index SHA-256 `ba2f413bfe56ee0de3a9c7ee4ebd77ddae23e1bde79a74e1bc3548ec7c587c9b`.

The coordinator confirmed the original v2 prepare terminal. The SDK child
completed zero with known cleanup in 13,359 ms; the helper records verified
closure and successful preparation. The exact new config has admitted identity,
own data/cache/SD paths, 12 GiB userdata, 8 GiB SD, 2 GiB RAM, two CPUs and no
first-boot snapshots. Its three immutable files independently match. The
initial SD is exactly 8,589,934,592 bytes, independently streamed SHA-256
`07870af523de0a94e5d20708c63ba7df77f772c9bfd71ad43d5dc7ca359b5e71`.
Userdata is absent. The original failed v1 directory remains preserved.

The separately disabled launch proposal SHA-256 is
`6bc304b9039d535f8902a5501d3dec4ab419ea6a060f8382bd93608ee960e4bc`.
Its 909 bindings equal the reviewed prepare bindings. Shared fields and exact
prepare/proposal/result linkage match; existing token and eight old registry
metadata bindings remain equal. The reviewed run namespace was unused with no
authorization. The fixed launch arguments point only to the newly prepared
content, pinned factory image and ports, with a maximum 1,200-second owned
supervisor. No concrete remaining source/input blocker was found. Any actual
run must retain that owner through the separately admitted guest test and exact
stop/known process-tree drain. Neither its running descriptor nor preparation
claims guest readiness, actual partition availability or filesystem durability.

Full M05/M01, physical-phone/ARM64/16 KiB, real-model/runtime, power-loss,
privacy/quality and A/#117/#119 gates remain separate and unchecked.

## Actual v2 launcher refusal and source correction

The coordinator confirmed the original launch terminal failure. The retained
owned result reports `child_exited`, worker return code two,
known cleanup and verified closure in 890 ms. Its 327-byte output (SHA-256
`5ed6fc8743d437c580946bb25fe44c1a49f1e97e04673789599ac9fbc039943c`)
reports that the supplied partition size exceeds the allowed 2047 MB maximum.
No guest command or app installation followed. The independent input review
missed this installed-Windows argument limit; actual execution exposed it.
All 20 failed v2 target files, 8,589,946,817 bytes, independently rehash without
mismatch; index SHA-256
`c0a590b590e14da4e2f24a002dbd2527a7262a8025c24efad1b6dd521491f930`.

The [exact emulator 35.3 common startup source](https://android.googlesource.com/platform/external/qemu/+/refs/heads/emu-35-3-release/android/android-emu/android/main-common.c)
checks this option using a C `long` bound divided by MiB. It can also override
userdata configuration, so it is not a system-only option. Omitting the option
preserves the nonzero configured userdata size. The [factory userdata path](https://android.googlesource.com/platform/external/qemu/+/refs/heads/emu-35-3-release/android-qemu2-glue/main.cpp)
passes that configured size to fresh ext4 creation. These source findings
support removing the argument while keeping 12 GiB configuration and the exact
new data path; substituting a smaller argument would defeat the requested size.
They do not prove an actual 12 GiB guest disk or successful boot. Both previous
target directories must remain preserved; any corrected attempt requires a
fresh directory, proposal and admission.

The minimal correction removes only the two invalid launch-argument elements.
Its regression checks that normalized userdata remains 12 GiB, the explicit
new data path matches that config, and neither partition option spelling is
present. The retained targeted run records 52 passing tests, zero failures,
errors or skips, 12.140 seconds; the original child completed zero with known
cleanup in 12,437 ms. Source and test hashes match the receipt. Output SHA-256:
`8be07377a2f48806ffd60dbf60d55fab2906b66809cc5130acb19682b0adac2a`.
No reviewer test or SDK execution ran.

The corrected final central gate records 536 passes, zero failures/errors/skips,
40.346 seconds; original child completed zero with known cleanup in 41,094 ms.
The actual retained output matches SHA-256
`1de1009ed25b7a9aa3ffa05238b597ad034848a3cac261d02d2c540b479654c6`.
All 1,403 final source snapshot files, 16,512,875 bytes, independently match,
index SHA-256 `7178d74e1a676c42b3e8c7e6c9a437edbbe0b7bdcb3dfbcef3ea39ae0add30ea`.

The separately disabled fresh v3 prepare proposal independently matches all
909 bindings, 5,046,134,929 bytes. Proposal SHA-256:
`73e84c96c10ecf85b57a416c49c30264bf8717a70b49a5211462039fcb0b2610`.
Only the helper binding differs from v2; settings, existing token and eight
old-registry metadata bindings match. Its distinct target and authorization
were absent at review. No remaining concrete source/input blocker was found
for that preparation phase. Previous host passes still do not qualify the
corrected live launch, guest capacity or receipt suite.

## Fresh v3 preparation and corrected launch inputs

The coordinator confirmed the original v3 prepare terminal. The SDK child
completed zero with known cleanup in 6,454 ms; successful prepare closure and
creation of the accepted prepared record are recorded. The new config retains
12 GiB userdata, 8 GiB SD, 2 GiB RAM/two CPUs and only its own paths. All three
immutable files and the complete initial 8 GiB SD independently rehash without
mismatch. Userdata remains absent; boot is explicitly unverified.

The separately disabled run proposal SHA-256 is
`5c5580a86db04f9afe484b4e99a4a70c15fbd15403e7609eccbae953f16fde68`.
Every shared field and all 909 bindings equal the reviewed v3 prepare proposal.
Its exact prepared record and successful closure linkage match; token and eight
old-registry metadata bindings remain equal. The reviewed namespace was unused
and authorization absent. The corrected argument vector omits the capped
partition override and retains explicit own data/SD paths. No remaining concrete
source/input blocker was found for this bounded run. Preparation is not a boot,
guest-capacity, new PROCESS-test or real-model result.

## Fresh-target qualification input review

The coordinator retained the original v3 owner execution. Its forced descriptor
records boot unverified. The reviewer opened the read-only ownership lease and
checked exact live process identities, immutable inputs and finite deadline;
no guest or SDK executable was invoked. This confirms only the reviewed live
owner boundary.

The separately disabled qualification proposal SHA-256 is
`ec4133932d73d989b4304644d5b5b6f0957bb46ef8eb20337572d89dcb13078c`.
All 35 bindings, 86,663,211 bytes, independently match. The unchanged signed
corrected app/test pair and final controller source are exact, the new evidence
directory is empty, and authorization was absent at review. The controller first
requires actual boot/AVD identity and empty app inventory, then checks staging
reserve before installing only the new pair and discovering their UIDs. It
admits one ordinary four-method suite and exact proof parsing, with owner checks
around every retained command. No previous B package history is projected onto
the fresh target, and no old target action or emulator stop is exposed. No
remaining concrete source/input blocker was found; actual readiness, volume
capacity and four passes remain execution gates.

## Actual v3 guest framing refusal

The coordinator confirmed the original guest-controller terminal failure.
The retained owned child completed with return code two and known cleanup in
17,719 ms; output SHA-256
`650524dead617a53b113f1cd995ae81b31330f47dc58ac9737e67aa87992b460`.
The reviewer checked both raw outputs and the stopped result: two known-clean
commands, zero installs, zero instrumentation and no accepted result object.

The boot-complete property returned one. The console-name response contained
the exact intended fixed name and `OK`, with CRCRLF on each line. The generic
normalizer rejected that framing, so target identity/capacity admission did not
complete. The actual 34-byte response matches SHA-256
`f268e4d62880b2f11307b19f1f986af25d2ae30278c73e7f7c344c0a470f6bac`.
A dedicated exact-name/OK framing parser can recognize consistent LF, CRLF or
this observed console framing while rejecting mixed/extra/foreign responses;
the shared/B normalizer must remain unchanged. Such a correction is not a
successful guest qualification and requires fresh source/test/admission evidence.

The actual narrow correction changes only console-name routing in the fresh
controller. Independent review confirms exact expected-name plus `OK` byte
equality with one consistent permitted ending. Its full mocked bootstrap uses
the observed CRCRLF; negative cases reject mixed endings, foreign or extended
names, duplicate/extra lines and control characters, while shared normalization
still rejects CRCRLF. The retained corrected suite records 14 passes, zero
failures/errors/skips, 4.513 seconds; original owned child completed zero with
known cleanup in 4,844 ms. Source/test digests and 1,688-byte output independently
match, log SHA-256
`824d13435b4e56e274ccd3dd5cb7c279211c11c81fc69d4f474b8830bbb6a034`.

The coordinator confirmed the original v3 owner stop terminal. Its retained
result records exact stop requested, known process-tree cleanup and verified
closure in 180,578 ms, with guest flush explicitly unclaimed. All three recorded
owner/worker/launcher identities were closed and the ports free in retained
closure observations. The complete 35 admitted input copies match their
original bindings. All 64 sealed files, 86,700,661 bytes, independently rehash
without mismatch; index SHA-256
`4ce2504f2ebe7684947c10ccb3c3e2cdf20681b2beae0937311f54c073f58023`.
Mutable virtual disks have retained size metadata only; their content is not
claimed unchanged, flushed or application-qualified. Old targets and all failed
fresh namespaces remain preserved.

## Fresh v4 input review

The integrated console correction's final central gate records 537 passes,
zero failures/errors/skips, 36.194 seconds. The coordinator confirmed its
original terminal; retained child completed zero with known cleanup in
36,828 ms. Actual output independently matches SHA-256
`b7dfc99459175815f9e55f3dfb0f5f077aeef8e364edad9f79ea3b3b163ec79f`.
All 1,403 source snapshot files, 16,514,752 bytes, independently match; index
SHA-256 `f90ca7e8357ec6c1fe0091ae62de30b35cf36d7edffb2438af4a4cd83795639f`.
The 395 compiled app/build source rows are unchanged; this packet requires no
new app build or dependency choice.

The disabled v4 prepare proposal SHA-256 is
`3c6ab58b73e0b928d8d5ebe801463da0bca6a229883b3b3c466d53a0f2d07c57`.
Its 909 bindings, 5,046,134,929 bytes, exactly equal v3 and independently
rehashed without mismatch. The token and eight old-registry metadata bindings
also remain equal. Only the fresh target paths differ; target and authorization
were absent at review. No concrete source/input blocker was found for this
preparation phase. The actual guest/storage/receipt gates remain unqualified.

The coordinator subsequently confirmed the original v4 prepare terminal.
Its SDK child completed zero with known cleanup in 17,047 ms; the prepare
closure and prepared record are successful. All three immutable files and the
complete 8 GiB SD independently match. Actual config retains only its own
12 GiB userdata/8 GiB SD paths and requested memory/CPU settings; userdata is
still absent and boot unverified.

The separately disabled v4 run proposal SHA-256 is
`04a49aaafe91b87809eacb0ab65bd9e8a65fced669efd07d49ab816a0015a405`.
Its exact prepare/prepared/successful-result linkage and all shared fields,
including the 909 bindings, match. Token and old-registry metadata are equal;
run namespace was unused and authorization absent at review. The helper retains
the corrected argument vector and finite owned lifetime. No concrete remaining
source/input blocker was found for that run; this input review establishes no
guest capacity or receipt outcome.

The coordinator retained the original v4 owner. The reviewer independently
opened its read-only live lease and checked its exact descriptor and finite
deadline, with boot still unverified. The separately disabled guest proposal
SHA-256 is `ca54e87f7d7bc70bf55ca3b2463617636882c25766190caeedf687ebf7bd69a8`.
All 35 bindings, 86,665,208 bytes, match; final corrected controller source and
the unchanged audited APK pair are exact. The guest evidence directory was
empty and authorization absent at review. No remaining concrete source/input
blocker was found for one separately admitted four-method cohort; no readiness,
capacity or Android pass is inferred from this review.

## Final actual Android result and ownership closure

The coordinator confirmed the original v4 guest execution completed zero. Its
retained owned child completed zero with known cleanup in 72,891 ms; stdout is
306 bytes, SHA-256
`2c199d5cdcb8aacbdbffc2073b7b467ea855925c242fd6901939d5090cc8fbde`,
with no stderr. The raw runner reports four passes and zero failures in 37.961
seconds. The reviewer reparsed that runner, all proof documents directly from
raw reads and all zero-byte ready-marker reads using the frozen closed parsers.

| Method | Actual scope | Required proof checks |
| --- | --- | ---: |
| `acceptsAndReopensReceipt` | Forced receipt/owner/model, accepted marker, full-hash reopen without source, accepted discard refusal | 8 |
| `cancelsAcrossAcceptanceBoundary` | Cancellation before acceptance preserves pending bytes; cancellation after acceptance reopens committed bytes | 10 |
| `refusesForeignAndUncommittedData` | Partial/foreign/unknown preservation, explicit partial discard and retry, synthetic guard refusal | 14 |
| `recoversAfterOwnedProcessDeath` | Actual OS-lock busy checks, fixed child halt armed, binding released, death observed, lock reacquired and source-free acceptance | 11 |

All 59 retained clients are ordered, known-clean completed-zero results with
matching raw lengths/digests and output limits. Only two fresh app installations
and one class-selected instrumentation invocation occurred. Factory inventory
was empty, installed/final maps contain exactly the signed app/test pair, and
their discovered UIDs remain equal. All four proof records share one actual
parent identity; the PROCESS child has a distinct identity and the same UID.
Final owned/passive app process counts are zero.

The outer guest stderr count is zero. The two successful install clients retain
bounded stderr counts of 146 and 156 bytes; all other clients report zero.
No stderr text or cause is inferred from those counts.

Actual userdata availability is 11,562,930,176 bytes before installation,
11,480,317,952 after installation and 11,356,491,776 final. Trusted Context proof
observations retain external space above 8.57 billion bytes and the unchanged
production floors throughout this tiny fixture. Those measured observations
qualify this slice; requested virtual-disk sizes alone would not. Every proof
reports candidate-root absence, original 63-byte fixture hash, no native
publication invocation and no inference-SDK invocation. This receipt protocol
uses in-place verified data and an acceptance marker; it does not make the
separately refused native no-replace operation work.

Only after the guest terminal did the coordinator request the exact owned
emulator stop. Its original owner execution completed zero with exact stop
requested, known process-tree cleanup and verified closure in 215,891 ms. The
worker return of one arises during owned forced drain; the owner record reports
the stop/cleanup outcome explicitly. Retained closure observations find all
three recorded process identities closed, ports free, immutable prepared files
and existing registry/token metadata preserved. Guest flush is explicitly false;
mutable virtual disks have size metadata only, without integrity/durability
or unchanged-content claims.

All 187 final selected files, 86,797,683 bytes, independently match the final
index SHA-256
`e6be2845cec0b1112a6eef040fb9be07b7d28ecf0057a6111f8bef664245cb70`.
The complete 35-input archive, 86,665,208 bytes, exactly matches every original
proposal binding, index SHA-256
`8f2f21320158e77d1555d5150570a9ac53124a6bf4015468e6eaa5691395a529`.
No further device action is needed to establish this recorded result.

The final host inventory also independently matches all 1,412 files,
16,806,099 bytes, SHA-256
`cc8bdaffd557ab9e628b05467a588303c2f9b4329c796f357325f9b2e25fb6d0`.
The separately sealed final environment admission records match all six files,
365,259 bytes, SHA-256
`b0712c568869c627305646941109a1c6477b0b4a39a1c7d2bb651e6c134f8d91`.
These inventories bind host source/checks and admitted phase metadata; they do
not turn mutable guest disk size metadata into a content or durability audit.

The next task must be separately scoped: integrate the qualified receipt design
only through an explicit debug candidate route, with canonical data kept internal
and the owner/model/storage gates preserved. This review does not authorize that
integration or a real-model copy. Full M05/M01, A/#117/#119, physical-phone,
ARM64/16 KiB, real-model/cache/runtime, power-loss and privacy/quality gates remain
unchecked. The original B capacity shortfall remains unchanged by this isolated
target's result.

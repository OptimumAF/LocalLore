# Player/NPC AUTHOR contract — 2026-10-28

Refs #13 (M09.02/M09.06), #14 (M10.02/M10.03 support), #5 (M01.01 support).
[Draft PR #244](https://github.com/OptimumAF/LocalLore/pull/244) is stacked on
open/unmerged [#242](https://github.com/OptimumAF/LocalLore/pull/242).
Executed implementation checkpoint: `6b1cdbfd543dfc10a27202f43b80037b0f8c5052`.

The AUTHOR prompt now explicitly reserves the player as actor0 and excludes the
player from the NPC array. Native and host tests pass, including actual persisted
Host/SQLite provenance. Both APKs build and pass the artifact checks. A fresh
real-model experiment is **unrun**: debug-service listener admission refuses an
undefined native socket state. No emulator was booted and no model was copied,
imported or loaded in this packet. The previous captured name rejection remains
failed and unchanged; these checks do not demonstrate improved model output.

## Implementation and provenance

The revised instructions say that `characters` contains NPCs only, cast hints
retain their exact names/count/order, names are unique ignoring case including
the player, and NPC array element i has actor index i+1. Knowledge, belief and
possession references use actor indices; each NPC includes its own actor index
in initial knowledge. The player location remains separate. Truth and beliefs,
untrusted author data, native mechanical authority and explicit review/create
remain distinct.

New generations record prompt `initial-world-v1.1`; schema remains
`initial-world-v1`. The actual Host generation record previously hardcoded the
old label separately from the domain constant. It now uses the authoritative
prompt/schema constants. Historical v1 origins remain readable with their exact
original label, bytes and hash; unsupported labels refuse. The existing native
proposal validator, accepted proposals, budgets and canonical hash algorithm are
unchanged.

The three Python proof/diagnostic readers accept keyword-only
`expected_prompt_version`. The default remains strictly legacy v1. Selecting
v1.1 is explicit, and a completed proof's canonical origin must match it exactly.
A generation refusal has no committed origin and cannot establish the prompt
revision: source/APK/runtime evidence remains required. The Android experiment
requires the new exact generation label. Proof/sidecar schemas, opt-in capture,
ownership rules and native consent are unchanged.

## Actual verification

| Check | Recorded result |
| --- | --- |
| Python focused suite |57 passed,0 failures/errors/skips;821ms owner, known cleanup/capture, no stderr, five selected file hashes unchanged. |
| Independent provenance adversaries |12 methods; original RED has43 subtest errors for the missing keyword API, then12 pass after integration. Identical test bytes; closed owners464/363ms. |
| Native focused suite |36 passed,0 failed/ignored:15 domain unit tests including5 new cases,9 detailed diagnostics,6 portability and6 CLI tests. Owner30908ms,2019 source hashes unchanged. |
| Actual Host regression RED |One test fails on stored prompt `initial-world-v1` versus expected `initial-world-v1.1`;7 filtered. Owner29436ms, worker1, known cleanup/capture. This was an assertion failure after real Host/SQLite creation, not a compilation failure. |
| Current Rust regression |977 passed,11 ignored,137 result suites,0 failed; owner470871ms, known cleanup/capture, no stderr,2020 tracked inputs unchanged. Includes the corrected actual Host workflow. Android fixture check passes. |
| Format/strict Clippy | Both pass; owner27469ms, known cleanup/capture, no stderr, same2020 inputs unchanged. |
| Android offline build |588 JVM tests/58 suites,0 failures/errors/skips; cleaned unfiltered unit task, both APK assemblies and dependency/analyzer/APK audits pass. Owner420464ms, known cleanup/capture, no stderr,2020 inputs unchanged. Gradle reports87 actionable tasks executed. This does not establish fresh compilation of every dependency. |
| Lint/analyzer |0 errors,10 warnings; analyzer32.4.1 reports analysis_did_work:true. |
| Independent closed-build audit | Full source/before/after/request hashes, all58 XML files, required27 store/4 AUTHOR worker/6 capture/10 owner cases and both APK bytes verified. Both native ABIs embed the exact revised prompt and current label and define the publication export; test DEX contains the new label. No SDK/native execution. |
| Current standalone diagnostic CLI | Offline build passes;1121ms owner with known cleanup/capture and894 compiled input bindings stable. It was not invoked on a model response. |

The Host regression assertion's bytes are identical in RED and the corrected
suite (SHA256 `fd2ae1627682612b95de55970058703e06fc9a281115baa92849ae3469415345`).
The domain fixtures verify case collisions still reject without mutation,
two-NPC actor/knowledge/belief/possession mapping, observer exclusion, historical
origin bytes/hash across inference-free replay, and unsupported prompt refusal.
These are deterministic tests, not model quality or device performance results.

Runnable host equivalents, from a physical D: checkout with the existing locked
dependencies prepared:

~~~powershell
$env:TEMP='D:\Dev\_Temp'
$env:TMP='D:\Dev\_Temp'
$env:CARGO_HOME='D:\Dev\Tools\Caches\Cargo-LocalLore-v1'
$env:CARGO_TARGET_DIR='D:\Dev\Experiments\LocalLore\author-check-target'
python -B -m unittest scripts.tests.test_original_author_model_proof scripts.tests.test_original_author_diagnostic scripts.tests.test_original_author_prompt_provenance
cargo fmt --all -- --check
cargo clippy --workspace --exclude locallore-desktop-spike --all-targets --locked --offline -- -D warnings
cargo test --workspace --exclude locallore-desktop-spike --locked --offline
cargo run -p locallore --example android_fixtures --locked --offline -- --check
~~~

Android tasks are the same unfiltered LiteRT verification command documented in
the [diagnostic report](ORIGINAL_AUTHOR_DIAGNOSTIC_VERIFICATION_2026-10-27.md).
The retained D-only helper additionally sets Gradle/Cargo/Android user caches and
both launcher/daemon Java temporary directories to physical D:. A private init
script selects the existing C: debug signing credential without copying or
generating a key. Installed tools and their supported runtime files remain in
place. Source/configuration and explicit output bindings are checked; this is
not an OS-wide file-I/O trace.

Product APK:78289152B, SHA256
`0ad6f03adf0179438570c7d4a7933f2ef7b1fd929ce7361c2627749168439fa9`.
Test APK:2251299B, SHA256
`58c423631737e312df4bc65082b6ae6723a4953336f735af3f7a832ef177db2d`.
The native CLI is1069056B, SHA256
`defca7c7f642f12cad9d13db3ea32ef52b9d4d1b70a63377b34812c213f4990b`.
Both packaged ABIs and native prompt strings are build evidence, not ARM64 or
Android runtime execution.

## D: preparation and retained setup failure

The old C: checkout alias resolves to physical
`D:/Dev/Worktrees/LocalLore/LocalLore-starter-native`; shared Git metadata is also
on D:. All new project commands use the physical D: working directory and D:
TEMP/TMP. Existing protected C: captures/backups and all emulator state remain
untouched. New ignored build/cache data remains on D: and is not represented as
preserved by a repository push.

No D: Cargo cache was initially prepared. A separate online `cargo fetch --locked`
uses the existing unchanged Cargo.lock and a fresh process-local D: Cargo home;
it fetches407 crate archives, producing24092 files/645431189B. Its73467ms owner
closes0 with known cleanup/capture. The full cache manifest is a snapshot at that
completion; later Cargo metadata mutations are normal. All subsequent reported
checks run offline. No dependency, SDK, runtime or model version is selected or
changed. Development cache preparation is not an offline-gameplay/network audit.

The owner explicitly approved one fresh8GiB/four-core/1800s D: test emulator,
isolated test app and local model copy, with debug-service startup only after an
unused-port check. That approval remains unused for emulator boot/model copy.
The first service-start command refuses the numeric loopback specification as a
remote host; its command/output and failed tool observation are retained.
The installed help and [AOSP socket classification](https://android.googlesource.com/platform/packages/modules/adb/+/f4965b77c694689c08855076eaf983c8e88646f9/socket_spec.cpp)
support the corrected `tcp:localhost:5037` spelling. Fresh exclusive IPv4/IPv6
port bindings pass before the second startup command completes0. A debug-service
process starts and is left running; none is stopped or replaced.

Listener admission still refuses. PowerShell/CIM report raw state0 for the
loopback5037 endpoint. An independent bounded native GetExtendedTcpTable query
reports that same raw0 for IPv4 listener and all-endpoint tables, with unchanged
kernel process identity/executable hash before and after. IPv6 has no5037 row.
[Microsoft defines LISTEN as2](https://learn.microsoft.com/en-us/windows/win32/api/tcpmib/ns-tcpmib-mib_tcprow_owner_pid);
state0 is undefined. Requesting a listener table does not justify silently
discarding the state check. The211ms native diagnosis completes0; that is a
diagnostic outcome, not successful service admission. Its underlying cause,
including any relationship to the execution environment, is unproven.

The pre-start capture also refused service observation, before any SDK device
list or target call. No current physical identity or absence is established.
No prepare/boot, APK installation, model copy, import, AUTHOR generation or
reopen runs in this packet. Runtime/closure/diagnostic helper ports remain
unexecuted with explicit missing-pin placeholders, not qualified continuations.

## Recovery and handoff

New recovery is physically on D:. Independent full-byte replay verifies245
selected originals/copies,246 ZIP members and248 files totaling158994966B,
zero missing/mismatches. Both failed RED histories and setup refusals remain
retained. The bounded selection includes APKs, source bundle, closed checks,
helpers, cache manifest and native diagnosis; it excludes model weights,
credential contents, caches, target trees, databases and emulator userdata.
Those excluded existing files are not deleted or moved. Preservation always
retains feature_acceptance:false.

| Recovery control | Bytes | SHA256 |
| --- | ---: | --- |
| Index |133772|`d04e456d7d6adcb357e32aa6abc4372f21aa4a68c58e470eb73c8fda4475bf4c`|
| ZIP |56672893|`a2d6b2c1ceef500b7544115e87db0690fd3893562b180221f66efd2dc361f63f`|
| Result |852|`efb14dddd68ef70c6a3e3f390ad510b32eeefbe191f10fdcd7476b8d1c82726b`|
| Independent replay |1394|`c0e099855d1f78a370ee831c7e35fbe2692d336bd25ef93ac66f1137111fc5ac`|

The selected-branch source bundle at6b1cdbfd is11369467B, SHA256
`9d032c31a1253ff7a521417486446356e9c81ea96227f63c0608e15f65fec1dc`.
Its creation and Git verification complete under a2708ms closed owner. It does
not claim to snapshot all other branches, ignored data or worktrees; historical
all-ref recoveries remain unchanged. This report is a later documentation commit.

M09.02 implementation and M10.02/M10.03 supporting host checks are in review.
M09.06's updated real-model qualification and M01.01 device admission are blocked
by current listener evidence. Full milestone criteria remain unchecked. Next:
establish a trustworthy current LISTEN-state service observation without
weakening guards or changing system settings, then admit the approved fresh D:
guest for exactly one import/AUTHOR attempt. Physical/ARM64 performance, model
quality, accessibility, complete journeys and joined callback drain remain open.
No merge, release, private upload, system-setting change or unrelated emulator
stop was performed.

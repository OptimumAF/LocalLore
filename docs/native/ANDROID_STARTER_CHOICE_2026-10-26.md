# Original starter choice — 2026-10-26

Supporting M09.02/M09.03/M09.06. This packet is separate from PR #219's
current-native-gate diagnostics and completed broad89 qualification. It starts
from main `3f75b5d673512b165e18b2b1e34d3deafc69067a`; none of those older runtime
results qualify changed starter-choice source or APKs.

## Behavior

Rust supplies a bounded original starter catalog. Android presents the selected
starter, its rules and player-visible starting facts before explicit Create.
Lantern Quay retains the existing fantasy setup. Bracken Harbor adds an original
narrative setup without numeric combat attributes, energy or abilities. Engine
validation still governs ownership, commitments, accepted turns and knowledge.

The catalog and preview are read-only. Selection does not create a story or invoke
inference. Exact fixture hashes, immutable review identity and the existing
transactional full-seed retry comparison bind confirmation to the chosen setup.
Retained stories are not rewritten. See the
[catalog contract](STORY_STARTER_CATALOG_V1.md).

## Verification status

Executable checkpoint `1b8341fd` integrates the native catalog, Android chooser,
independent durable tests and [fixed seven-method protocol](ANDROID_STARTER_CHOICE_PROTOCOL.md).
The unchanged dependencies are Python3.14.7, Rust/Cargo1.93.1, JDK21,
Gradle8.11.1/AGP8.10.1 and NDK29.0.14206865 on Windows.

| Actually executed check | Result |
|---|---|
| Three native packages, all features, locked/offline Rust tests |796 pass,0 fail,11 ignored across112 harness summaries; owner558718ms/worker0, cleanup/capture true |
| Same packages, all-target/all-feature Clippy with warnings denied |Pass; owner27033ms/worker0, cleanup/capture true |
| Frontend schema generation/build, TypeScript, contract/controller checks and formatting |Pass; owner28336ms/worker0, cleanup/capture true |
| Full Python discovery in `scripts/tests` |1477 pass,0 failures/errors/skips; owner173189ms/worker0, cleanup/capture true |
| `cargo +1.93.1 fmt --all -- --check` |Tool-observed exit0 |
| Final offline Android build/JVM/lints/artifact audits |Pass; owner330616ms/worker0, cleanup/capture true;266 executed JVM tests/31 XML suites,0 failures/errors/skips; both lints0 errors/3 warnings;11 artifact audits |
| New seven Android chooser methods |Compiled in the original packet; the fresh follow-up below now passes all7 on API35/x86_64 |

The Rust run freezes829 mapped inputs at `634b1403`. Subsequent Android and
Python integration changes no Rust/fixture/Cargo input. Clippy and frontend
freeze1942 tracked files at `e5cb4759`; the next executable change is only the
Python fixed driver and its eight host adversaries. The full Python suite
freezes1943 tracked files at `1b8341fd`. Source maps are unchanged within each
phase. These are overlapping checks, not additive unique coverage counts.
The final Android build freezes834 mapped inputs; both107667-byte source maps
have SHA256 `8b391bdf8721b3e5bf25d216d96b010c39f6ea8b95da963ea86b1d6bf831df9c`.
Fresh deep `qualified_build` replay succeeds against current source, commands,
raw streams, APKs and copied XML reports. No older Android runtime result is
promoted to the new source. The three lint warnings are existing dependency,
controller backup-rules and controller icon warnings, not ignored errors.

The final product APK is24761192 bytes, SHA256
`89c573f9394af2f4a03298d020bba10fb557bd5f6bf7b265f728024534a989e9`;
test APK2088679 bytes, SHA256
`3de86d12fbb9fee89918541203a21abb75a866bb8e96d1771f4ddc0359956f60`;
controller APK55073 bytes, SHA256
`6ea09f4c5105d62e61498d2bebc05de52ce597e30b9681e4975a323b36ef7693`.
Definition readback verifies the new test classes and their exact annotated
public no-argument methods in that test APK. It does not run them.

Independent read-only review checks the native transaction/hash/privacy
boundaries, Kotlin stale-consent/cancellation paths and the new driver's exact
roster/current-SDK2 worker/parent validation. Reviews are bounded evidence,
not owner acceptance. The six independent workspace tests actually execute
real Store/Host creation, full persisted seed comparison, narrative transfer,
close/reopen, retained retry and cross-template collisions in both directions.

The native author's first library run has52 passes/one generated-schema mismatch;
it is tool-observed only and has no retained original stream. Schema regeneration
fixes that mismatch before the integrated796-test pass. Original private
generation commands all return0, but their preparation helper incorrectly
expects desktop files inside the Android-only source map and reports
`passed:false, changed:[]`. That failed helper record remains failed; the raw
commands and subsequent independently passing checks are separate evidence.
No passing record is reconstructed or relabeled.

Bracken's original fixture SHA256 is
`df58fc298372389f1366cdee767bac81740e56d5ee0c4ea4cec1d322f0e17347`.
Its bytes and the entire Lantern fixture remain pinned by native tests and
the build source maps. A zero-valued legacy energy line remains in the
narrative setup display; it enables no numeric combat or ability mechanics.

The previously pinned emulator processes and server became unavailable during
the prior packet. Its interrupted root preparation and unstarted retired control
remain unqualified in [PR #219's separate report](https://github.com/OptimumAF/LocalLore/blob/d5a93b02/docs/native/ANDROID_SDK2_MAIN_CONTROLS_2026-10-26.md).
No server restart, system-setting change or unrelated emulator action is used
to bypass that boundary.

No runtime, model, native, SDK or library dependency is introduced or repinned.
Existing locked dependencies are used offline. Custom premise, tone/content
boundaries and player editing remain pending, as do complete journeys and
physical/model qualification. Full M09 task criteria stay unchanged.

## Preservation and next gate

Independent readback verifies all316 native inputs across the Rust run and
subsequent Clippy/frontend/host/build maps. The generated desktop schema and
types also match their captured Clippy/frontend inputs and final files. This
records unchanged dependency closures rather than repeating unaffected tests
after a Python-only integration change.

Create-only private C: recovery retains145 originals and one explicitly derived
audit:146 entries/30176726 bytes. Every original, copy and ZIP member is verified,
then replayed again. The53954-byte index has SHA256
`91df5561fa837be729f92c59db55da9f6c8432477e16d699f19d1fa6d4ea6421`;
the19047239-byte ZIP has SHA256
`4c34523ab660669a8d16191f2446d4a9fe34ac151517101a199f2ef343a5d2d2`.
It includes the six completed private check/preparation cohorts, three bound
APKs, their copied reports and explicit helper sources. The original failed
generation helper remains failed. No live outputs, model weights, guest images,
databases, private saves or unknown subtrees enter this selection.

The original host/build packet ends with all check owners terminal and no SDK
device command or server lifecycle action. Its next gate is fresh environment
admission, native10 and starter-choice7. The separately measured follow-up below
records that setup and execution. Original root/retired controls and full
UI/physical/model gates remain separate. No merge, release, system-setting change
or unrelated emulator stop is performed by either packet.

## Fresh runtime follow-up

The follow-up reuses the exact834-input build after a successful deep replay;
no host/build suite or older Android outcome is relabeled. Executable source
remains `0016435e`. Fresh standard guests use2GiB RAM/two CPUs, the existing
1200-second guest ceiling and850-second SDK/900-second verification budgets.
Both guests are prepared and their proposals planned before the first launch.

A fresh preflight observes no ADB/emulator processes and no listener on5037.
Setup then launches the installed ADB binary with
`-L tcp:localhost:5037 server nodaemon`, hidden, with private console logs.
The installed help and [official AOSP command-line implementation](https://android.googlesource.com/platform/packages/modules/adb/+/refs/heads/main/client/commandline.cpp)
confirm the direct server mode (source blob `5cd3ab66dd0a7ba0173b01f954fbe76c21269483`).
The new server pin must match the exact launched native PID, creation FILETIME,
executable and hash. Existing-server replacement, kill and reconnect commands
are not used. The new service is deliberately left running. This is local
development setup, with no persistent setting or dependency change.

The completed native component phase passes all10 methods across3 classes,
with87 complete measured-SDK2 client pairs. Its owner records287808ms/worker0,
cleanup/capture true and stderr0. The maximum recorded client is11110ms;
maximum server observer3890ms. Independent deep readback verifies the original
runner frames, source/build/request/owner bindings and every client/raw pair.
These observations do not establish physical-device or general timing guarantees.

The bound stop returns0 and the native guest handle is actually terminal0.
Its owner records `stop_requested`,353068ms/worker1, cleanup/capture/closure
true and no guest-flush claim. Emulator warning streams are retained separately
from the clean verification-owner stderr.

The separate chooser phase passes all7 methods across3 classes and90 complete
measured-SDK2 client pairs. Its owner records290764ms/worker0, cleanup/capture
true and stderr0. Maximum recorded client13169ms/server observer4663ms retains
the original budgets. The real MainActivity/JNI case explicitly creates both native
rule profiles with different story identities, preserves library/selection on
Cancel and reopens both profiles after ordinary Activity close. Wire and Compose
cases cover strict metadata, immutable retained callbacks and disabled selection.
This is scripted local API35/x86_64 execution, with no model load. It does not
prove accepted-turn conservation, draft preservation, OS-death recovery or joined
native drain; those remain separate tests and gates.

The chooser bound stop returns0 and its emulator handle is actually terminal0.
Its guest owner records `stop_requested`,346299ms/worker1, cleanup/capture/closure
true and no guest-flush claim. Only after both exact proposal-bound requested
closures, Root executes the reviewed final postflight once: pass, one observation
of the same launched server, zero SDK/device calls and no server lifecycle action
by that observation. The new preflight contains zero protected processes, so it
supplies no comparison with the two processes that disappeared earlier. The new
server is deliberately retained; its live console logs are excluded from a
terminal evidence seal.

One complete device-list capture from the native phase contains one authorized
SDK-emulator profile and no physical-profile candidate. Assessment reads only
that original bound capture and makes no new SDK, OS or hardware call. It does
not establish absolute phone absence or fresh physical-device admission.

Independent readback verifies both runtime source maps against the same current
834-input map and immutable build, all177 measured-SDK2 pairs, exact runner
frames, both proposal-bound requested closures and all six prepared INI bindings.
Final postflight is2501 bytes, SHA256
`f1f331580df6f71e6e1429c49993a03901e76be7116036156e6daa7896ee0e4a`.

The separate private runtime recovery selection contains439 entries/1374083
bytes:427 runtime/input records, seven helper sources, two derived coordination
records, one derived captured-device assessment, one prior-seal index reference
and one derived audit. Every selected source file, recovery copy and ZIP member
is verified, followed by another full replay. The146524-byte index has SHA256
`4d6a86ac927c6f7088e082bc3b8f0f6da285f0b371b49c4f0b0cb17cdb925498`;
the484194-byte ZIP has SHA256
`2614e4e69ebc722d10c3a88a1049b15f53c90637f5b498986a0a0a0d4080076b`.
The preceding host/build seal remains unchanged and supplies the exact APKs;
their payloads are not duplicated into this runtime selection. Live server logs,
guest images, databases, models, private saves and unknown subtrees are excluded.

The current chooser gate is now qualified on this one API35/x86_64 environment.
Full custom premise/tone/content/player editing, complete journeys, physical
model/ARM64 execution, accessibility and joined-drain qualification remain open.
The root82/retired139 controls subsequently pass on their separate827-input
source in [the SDK2 controls report](ANDROID_SDK2_MAIN_CONTROLS_2026-10-26.md)
and draft PR #219. They do not qualify the834-input starter source. Its fixed
legacy creation19 and broad89 regressions remain the next runtime checks.

## Preservation follow-up

After the owner reported possible concurrent cleanup of generated files, an
independent read-only audit rechecks the six existing starter-choice,
starter-runtime and SDK2 root/leaf evidence/source recovery sets. All1729 indexed
payload occurrences match their recorded hashes; none is missing. All1119
members across the three ZIPs and all three complete-history source bundles
match. All62 copied public Git blobs also match their Git object identities.
All1116 unique indexed original paths survive byte-identical. These selected
originals are already on C:; none points to D:.

The audit additionally checks only the827 exact D: executable-source paths
from the sealed SDK2 source map: all survive unchanged. It does not establish
coverage of unknown or untracked D: folders, identify a cleanup tool, or turn
missing records into evidence. No existing recovery file is overwritten and no
new payload archive is needed. Both implementation branches are already clean
and pushed; public reports and synthetic source stay in Git, while private raw
diagnostics, saves, model weights and guest images remain excluded.

The next packet uses a new create-only recovery namespace on C:. A file-only
deep replay validates the current834-input build, native10 prerequisite and
all87 measured-SDK2 pairs. Its new bounded host inventory records zero protected
emulator processes; the existing server pin matches without a lifecycle action
or device call. These prerequisite replays are not new test executions. The
fixed creation19 and broad89 results will be reported only after actual runs.

## Current-source legacy regression follow-up

This packet reuses the unchanged834-input source map and exact three APKs above,
after deep build/native10/current87-client prerequisite replay. Both fresh
API35/x86_64 environments and proposals are prepared before either launch.
Existing2GiB/two-CPU resources,4GiB host-available floor,1200-second guest ceiling,
850-second SDK session and900-second verification owner remain unchanged.

The fixed `story-creation` phase actually passes all19 methods across4 classes
with99 complete measured-SDK2 pairs. The verification owner records307811ms,
worker0, cleanup/capture true and stderr0; maximum client16997ms and maximum
server observer4515ms. Independent canonical readback verifies each original
runner frame, current source/request/build/owner binding, exact closed roster
and all client/raw pairs. The four legacy test source files and their method
rosters are unchanged from main; the production native catalog is exercised
through the current APK, without changing the fake-port compatibility tests.

The bound stop helper returns0, and the actual guest handle subsequently returns0.
Its owner records `stop_requested`,333530ms/worker1, cleanup/capture/closure true,
no guest-flush claim and the exact proposal hash. Guest console warnings remain
separate from the clean verification stderr. This qualification is scripted
local creation/ordinary Activity coverage; it does not establish OS-death,
physical-device, real-model, ARM64 or joined-drain results.

The separate fixed `regression` phase is running. No result or terminal recovery
seal is claimed for it yet. Its final postflight will run only after both exact
requested guest closures. No source changes, repeated build, timeout relaxation,
server lifecycle action or unrelated emulator stop are used by this packet.

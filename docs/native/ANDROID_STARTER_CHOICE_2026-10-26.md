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
| New seven Android chooser methods |Compiled; exact three classes/seven public JUnit definitions read back from test APK; unexecuted |

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

All check owners are terminal. No SDK device command, server lifecycle action,
emulator stop, system-setting change, merge or release is performed by this
packet. Next runnable Android gate is fresh environment/server admission,
current native10 and the separate fixed starter-choice7 in fresh owned guests.
Original root/retired controls and full UI/physical/model gates remain separate.

# D02 current-main gate — 2026-10-22

Refs #23 (D02.01–D02.06), under #21. D01 #33 and D02 #36 were already merged
when this assignment was rechecked. Accepted main `2612001` also includes shared
app storage #42. This follow-up preserves that implementation and corrects a
render-discovered label regression plus stale current guides; it does not build
a second shell or reset production to ephemeral progress. Follow-up is locally
verified for review; task acceptance/checklists remain with the owner.

## Demonstrated defect and correction

Fresh actual native D02 fixture renders labelled their explicitly ephemeral Host
as **Storage unavailable**, disabled New, and promised saved-story retention on
close/reset. The original 119-assertion compatibility journeys did not catch that
display regression after the durable app integration.

The controller now validates the actual Host `workspace` response. Only an
explicit `persistent:false`, null location/schema and empty stories enables
ephemeral presentation. Exceptions never enable it. Fixture status/footer,
sidebar and reset/close labels now say progress is in memory and lost on close;
fixture New is enabled. Production durable success and storage-open failure keep
their separate existing behavior. The shared Rust authority and wire schema are
unchanged. No new persistence/inference/memory subsystem is introduced.

Each live fixture checkpoint checks the visible memory label and absence of
false save/failure claims. Disposal instead checks that the UI was unmounted.
The actual durable startup-failure journey now also checks ephemeral mode stayed
false. An independent reviewer caught the initial post-unmount label assertion
before final execution; it was corrected. [Review and disposition](D02_CURRENT_REVIEW_2026-10-22.md)
records the source audit, render discovery and final diff review.

Final product/test source: **`a4a90b97936f342e0d010303b969879d113105b8`**, including
fix `eefe54c`. Later commits change documentation only. Current HOST_V1/ADR and
harness/README guides distinguish durable production from ephemeral fixtures,
document workspace/resume and native window epochs, and correct the Android
portable-host dependency claim. Historical verification reports are unchanged.

## Executed checks

Windows x64, Rust/Cargo 1.93.1, Node 23.10.0/npm 11.2.0, installed Evergreen
WebView2 (the loaded native runtime version was not captured). Existing pinned
Tauri 2.12.5/tauri-build 2.7.4, Playwright 1.64.1. Android compatibility uses
Java 17.0.6, Gradle 8.11.1, AGP 8.10.1, Kotlin 2.2.21, SDK36/build-tools35.0.0,
NDK29.0.14206865. No dependency pin changed.

Commands run from root except npm/native Cargo commands, which use `apps/desktop`:

| Check | Actual result |
|---|---|
| `npm ci --offline --ignore-scripts --no-audit --no-fund` | Fresh 32-package install |
| `npm run check`; `npm run format:check` | PASS: strict TS, generated schema, actual action builders, hostile wire/error/keyboard checks, normal bundle has no dev hooks; formatting |
| `python scripts/check.py host --offline` | PASS: 122 Rust workspace tests, 191 Python tests, four fixture comparisons, three native-linker tests, fmt/strict Clippy. All Rust/core sources remain identical to tested main |
| `python scripts/check.py android --offline` | PASS: both existing ABI outputs/app/test APKs, 38 JVM tests, lint 0 errors/1 existing dependency advisory, capability/ABI/16KiB alignment audit. Incremental compatibility build; no clean/native rebuild or device execution inferred |
| `cargo test --manifest-path src-tauri/Cargo.toml --locked --offline --features dev-harness` | PASS: four unique native cases (two lifetime/two artifact contracts); wrapper repeats two artifact cases |
| `npm run harness:native` | PASS: **163 assertions, 21 semantic snapshots and 21 actual native WebView2 app-only captures**, native IPC and close/reopen |
| `npm run harness:headless` | PASS: **163 assertions, 21 snapshots and 21 headless Chromium captures**, same controller + real Rust stdio; distinct from native IPC |
| `npm run harness:durable` | PASS: **33 assertions, 11 native app-only captures**, actual separate process restart and strengthened storage-failure/no-memory-fallback check |
| Native `cargo fmt`, dev/default all-target `cargo clippy ... --locked --offline -- -D warnings`, default `cargo build ... --locked --offline` | PASS; normal assets/executable restored, never launched as a visible app |
| `git diff --check` | PASS |

Fresh native compilation first exhausted free disk during Clippy; a subsequent
source write was interrupted. The affected journey file was restored from Git
and its change reapplied. Only this checkout's copied cache archive and native
build output were removed; no shared cache/daemon or concurrent checkout was
altered. Final native builds/tests/journeys use `CARGO_PROFILE_DEV_DEBUG=0` and
`CARGO_INCREMENTAL=0`, reducing artifact space. All final commands above pass;
earlier 119-assertion runs are baseline evidence only.

Android used this task's isolated Gradle user home and SDK download remained
disabled. There were no ADB/emulator/model operations, desktop-control tools,
injected input, activation, desktop screenshots or unrelated-app automation.

## Artifact identity and visual inspection

All summaries record clean source `a4a90b9`, no desktop control, and zero current
source-input SHA mismatches. Generated executable/bundle hashes identify their
recorded run; normal build restoration later overwrites those build outputs.
Raw synthetic artifacts stay local and ignored under `apps/desktop/artifacts/`.

| Backend / local artifact leaf | Summary SHA-256 |
|---|---|
| `native-d103cc89-5453-4509-9fcd-4b8d7a29ad1e` | `b13e3c8391caa5c676de0d665b2053d196902e2bda35d9ad80aa1d93377ed963` |
| `headless-c2736b3d-029c-42ea-89b8-82250372437b` | `1b82ca09d74ba7614350e06e389f49ba32cef18cb014e84ef7604408c6a6a70b` |
| `durable-native-35631143-7060-4a07-8d2a-881a7d1cbd0f` | `346e37364068fc69a37905d559e23e03407d2ecd4c6eb63c904a973c75251df9` |

Coordinator inspected final native `play-accepted.png`, `narrow.png` and
`enlarged.png`: selected scope/revision, authoritative receipt/state differences,
fake provider and memory-only labels are readable; narrow/200% layouts stack
with vertical scrolling. The regression's false save promises and storage error
are absent. Existing journey checks verify horizontal overflow, pending/cancel/
retry/stale/session/reset/disposal, rejected/malformed/failed responses, observer
isolation, inert hostile text and complete direct-engine receipt equality.

## Remaining gates

No real inference, arbitrary free-text interpretation, installer, macOS/Linux,
physical phone, fresh connected Android instrumentation, actual keyboard/screen
reader/OS clipboard or disconnected-network qualification is claimed. The existing
upstream WebView class-unregister warning1412 appears after PASS/exit0; no native
leak qualification is inferred. Protected concurrent runtime-control resources
were untouched. No merge, release, repository settings, task checkboxes or milestone
closure changed.

Stop at this D02 review gate. Next product work follows its owning tickets:
D03 #24 readable inspection exports (save/resume is already integrated), and
D04 #25 shared real-inference integration. Neither is implemented by this packet.

# Scripted selected Protocol4 scene qualification

2026-10-29. Refs #29 D07.04/D07.06, supporting shared Rust slice under #21.
Base: accepted main `a6f235ae74c4e3ade80175a499ecd7fc20751314`.
Last code/test revision: `8e846a04620133099ea4d73331e64ae800324d31`.
The [accepted contract](D07_SELECTED_SCENE_V4_CONTRACT_2026-10-29.md)
retains the original proposal, binding definitions and pre-runtime clock clarification.

This gate implements the shared Rust API. Desktop selected Protocol4 routing,
controls and native selected execution remain unavailable. No frontend/native
command, canonical schema, provider, memory implementation or Android adapter
changes are included. This record does not complete D07 or the desktop epic.

## Implemented boundary

`local_lane::comparison::scene_v4::selected_v3` provides opaque
`prepare_selected`, `prepared_metadata`, consuming `run_selected`, explicit
`resume_selected`, `inspect_selected` and a separate `desktop_read` capability.
The selected artifact is version3 with source_protocol_version4 and actual
TurnReportV4 rows. Full Protocol3 is a different artifact. Selected1/source2
and selected2/source3 remain unchanged.

ScriptedBaseline uses the existing fake inference provider through the actual
Host/Store pipeline. ApprovedNative refuses with SelectedNativeUnavailable
after pure cancellation/identity validation and before profile/source/target
lookup or reservation, including in a local-model feature build.

Both constructions receive their actual source Store cut, original scope,
request, head and accepted prefix. A paired case validates its reference;
a rollout retains genuinely different left/right histories. The new destination
is an isolated evaluation copy, not a registered live story or newly identified
canonical branch. Preparation retains the source lock/pins; execution refreshes
the source rather than treating the cached snapshot accessor as fresh authority.
Historical source drift refuses rerun without repair or hash rewriting.

Three identities stay separate: full-source read snapshot binding; selected
manifest/resume binding; selected read snapshot binding. Closed manifests,
required nullable fields, V4 row reconstruction and existing bounded readers
validate retained data. Reports reconstruct actual state; cached report JSON/HTML
never override Store/checkpoint inspection. Scripted physical setups are zero,
setup time/load null, human_reviewed0, human_rubric not_reviewed and
quality_accepted false. Unexpected setup records refuse.

Existing prefix/bootstrap/Store, ready_turn4/execute_turn4/load_turn4,
ledger settlement and escaped inert report owners are reused. A surviving
committed receipt supports checkpoint-loss recovery without another generation,
admission or commit. Receipt-backed fallback/repairs/construction metadata remain
available; original calls/capture/trace/timing/validation evidence remain unknown
and the recovered row stays unqualified. Failed/cancelled/stale terminal keys
without checkpoints retain TerminalCheckpointMissing. Completed resume validates
the source, then returns without rewriting the destination or admitting work,
even at the invocation limit.

Query2 filters actual before/after Engines in Rust. Raw evidence/diagnostics
require the existing native grant and appropriate observer before binding/fresh
file probes. Read metadata excludes requests, prose and the private report.
Browsing never changes character knowledge or generation context. Cold
open_read_only itself remains a trusted Rust caller API without a grant argument;
the later native transport must deny before calling it.

## Independent source and retained failures

The different-author FIRST was frozen before production. Original
`1c406d39` maps to Root `79cfdd79`; portability-only `b3706d66` maps to
`d3a7ff9b`. Raw hashes respectively:

- `d8ed21aa72b2c21ca786080d168424c2d5da387c2c794556e78da1720424582b`
- `95f029d47f79c1e75990219aefa1c11aea227c2e0b8318eaafb0a248d8201862`

Root formatting `a3f6025d` is byte-identical to a separately formatted raw copy:
`6f34ce18cf2459d1341655c727ec13fc2a8339faad4c67556d9fc378daa1f73a`.
Missing APIs/registration before implementation were SETUP/unrun, never behavioral RED.
Different-author production `eb95920b`/`8f96ef88` maps to `6142fb02`/`d51742ec`;
Root owns only the private snapshot bridge/registration and integration.

The original default14 run at `ea464324` returned **13 PASS/1 FAIL**, exit101.
The reader test wrongly required SECRET-TIDE-731 to be absent for every observer.
The seed explicitly grants relic-location to the player. Its immediately prior
exact equality with actual Rust Query2 passed. Independent correction `e8e3f52d`
maps to `86cf5a47`: it retains that equality for every cell and every character/
history exclusion, while positively requiring the informed player's exact
knowledge row. It changes no Core, seed or privacy rule. Corrected reader execution
then passes. Its raw/formatter-identical hash is
`11700c914470721783fe887f9e4abb213b1b383bb963a4e180e227cf657fd832`.

Strict Clippy next found needless_range_loop in the frozen private source fixture.
Independent `0a4a1c47` maps to `8e846a04`: three lines enumerate the same ordered
arm names; all assertions, numeric indices, fault, ledgers and checkpoints remain.
No lint is suppressed. Its raw/formatter-identical hash is
`2136c32f89d487a3cbbcc234fe1e09ef55f09635d00452b556b95773660f49d7`.
The affected actual divergent-source group passes after this correction.

The four production file hashes are unchanged through both test corrections:

| File under comparison/ | SHA256 |
| --- | --- |
| scene_v4.rs | b5ba9a66efaf1f25c27ca0c9e475a3b6d0b44b13164e16f0441854234d467604 |
| scene_v4/desktop_api.rs | cc417b1e8a1a5d5dc54c1a95d12922a18d49610df13d821d70d811dc24b4fd8c |
| scene_v4/selected_v3.rs | 1bb95ad9da1bfc8c37879213ee9a532020ea1a08b49efb5622ba5140b1b17428 |
| scene_v4/selected_v3/desktop_read.rs | 7ee2961251a7d42f6bdeaf55609577dac10c6c785c1c8092f9bb3d8695159e9d |

All14 distinct new groups have passing recorded executions across these revisions.
**The complete fourteen were not rerun as one green command at the final revision.**
The original failing suite, raw tests and exact correction lineage remain retained;
focused reruns cover the changed oracle/fixture. Existing source-binding hashes
include test source bytes, so each new process generates its own matching synthetic
source; old fixtures are never rebound to new code.

Independent production/bridge source review at `7ed4c551` found no concrete blocker.
It checked source freshness, actual prefixes, both-arm preflight, recovery,
completed resume, strict data bounds and access ordering. Source review is not
GitHub approval, human quality acceptance or runtime evidence.

## Commands and exact results

Every recorded process started/ended with clean unchanged source, locked offline
dependencies and TEMP/TMP on D. Times below are complete command seconds; Rust
test durations are listed separately where relevant. Logs/process records are
local under packet `selected4-shared-20261029-v1`, outside the checkout.

| Check | Revision | Result | Command seconds |
| --- | --- | --- | ---: |
| New default14 FIRST | ea464324 | 13 PASS/1 fixture-oracle FAIL,0 ignored; exit101; test1814.57s | 1844.3200698 |
| Corrected exact reader group | 86cf5a47 | 1 PASS/0 FAIL/0 ignored; test212.13s | 226.8596062 |
| local-model feature exact admission/native-refusal group | 86cf5a47 | 1 PASS/0 FAIL/0 ignored; test121.66s; no model | 139.0819105 |
| Existing shared clock_review_tests | 86cf5a47 | 7 PASS/0 FAIL/0 ignored; test6.27s | 6.6250085 |
| Existing selected2 review_tests | 86cf5a47 | 3 PASS/0 FAIL/0 ignored; test54.56s | 54.8886821 |
| Existing selected1 review_tests | 86cf5a47 | 4 PASS/0 FAIL/0 ignored; test343.90s | 344.2164310 |
| Existing selected1 divergent_tests | 86cf5a47 | 1 PASS/0 FAIL/0 ignored; test14.45s | 14.7680855 |
| First strict Eval Clippy | 86cf5a47 | FAIL frozen fixture range-loop lint; exit101 | 23.3797206 |
| Eval Clippy, all targets/local-model/-D warnings | 8e846a04 | PASS | 16.9420327 |
| Corrected exact divergent-source group | 8e846a04 | 1 PASS/0 FAIL/0 ignored; test33.20s | 46.0935945 |
| Desktop Clippy, all targets/dev-harness/-D warnings | 8e846a04 | PASS, compile only | 32.2558746 |
| Android Rust Windows-host check | 8e846a04 | PASS, compile only | 0.5099835 |
| Eval rustfmt check | 8e846a04 | PASS | 0.8063332 |
| Workspace rustfmt check | 8e846a04 | PASS | 4.0678761 |
| Complete verify-frontend.mjs | 8e846a04 | PASS, TypeScript/schema/mocked controller/static HTML checks | 22.9599026 |
| Normal desktop binary build | 8e846a04 | PASS, unlaunched | 29.0578139 |

The new14 cover noninitial paired/rollout inputs, actual private-driver asymmetric
source histories, failed source inputs, path/lock/source drift, exact V4 identity,
fixed post-arm cancellation/partial resume, byte-identical completed resume,
unknown reservations, receipt recovery/bootstrap/terminal-key refusal, observer
queries/diagnostics, permissions before bad bindings/files, strict manifests/
caps/tamper/cache separation, old artifact versions, natural guard/dependency
outcomes and optional companion nonauthority. Public full-run sources are distinct
from the separately labeled private-driver divergent source fixture, which uses
existing WrongCommand only on first-left and real Host/Store/checkpoint/seal paths.

For reproducible commands on this Windows machine, choose existing ordinary
physical-D source/cache/target paths and a new evidence parent. Do not reuse a
real-model packet or delete failed fixtures to make room. Admit the storage budget
before execution. New tests retain their generated data.

```powershell
$Repo = 'D:/path/to/physical/LocalLore'
$Evidence = 'D:/path/to/new/scripted-selected4-evidence'
$Target = 'D:/path/to/existing/Rust-target'
$Cache = 'D:/path/to/locked/offline-Cargo-cache'
Set-Location -LiteralPath $Repo
$env:TEMP = 'D:/Dev/_Temp'
$env:TMP = $env:TEMP
$env:CARGO_HOME = $Cache
$env:CARGO_TARGET_DIR = $Target
$env:CARGO_NET_OFFLINE = 'true'
$env:CARGO_BUILD_JOBS = '1'
$env:CARGO_INCREMENTAL = '0'
$env:CARGO_PROFILE_DEV_DEBUG = '0'
$env:CARGO_PROFILE_TEST_DEBUG = '0'
$env:LIBSQLITE3_FLAGS = ''
New-Item -ItemType Directory -Path $Evidence -ErrorAction Stop
$env:LOCALLORE_SELECTED4_TEST_ROOT = $Evidence
$env:LOCALLORE_CHECK_OUTPUT_DIR = Join-Path $Evidence 'frontend'
$Eval = 'crates/locallore-eval/Cargo.toml'
$New = 'local_lane::comparison::scene_v4::selected_v3::review_tests'
$Reader = $New + '::public_reader_query2_and_finite_diagnostics_do_not_change_character_knowledge_or_generation_contexts'
$Admission = $New + '::public_admission_precedence_exact_source_binding_and_lock_never_create_or_repair'
$Divergence = $New + '::actual_private_driver_divergence_and_failed_source_row_are_not_reconstructed_from_reports'
```

These are the executed command forms; the all-new filter was run at the original
revision, while the exact filters were the focused corrected/feature runs above.
Running all-new on the final source is a possible reproduction, not an extra
recorded green result.

```powershell
cargo test --locked --offline --manifest-path $Eval --lib $New -- --nocapture --test-threads=1
cargo test --locked --offline --manifest-path $Eval --lib $Reader -- --exact --nocapture --test-threads=1
cargo test --locked --offline --manifest-path $Eval --features local-model --lib $Admission -- --exact --nocapture --test-threads=1
cargo test --locked --offline --manifest-path $Eval --lib $Divergence -- --exact --nocapture --test-threads=1
cargo test --locked --offline --manifest-path $Eval --lib local_lane::comparison::clock_review_tests -- --nocapture --test-threads=1
cargo test --locked --offline --manifest-path $Eval --lib local_lane::comparison::literal_v3::selected_v2::review_tests -- --nocapture --test-threads=1
cargo test --locked --offline --manifest-path $Eval --lib local_lane::comparison::selected::review_tests -- --nocapture --test-threads=1
cargo test --locked --offline --manifest-path $Eval --lib local_lane::comparison::selected::divergent_tests -- --nocapture --test-threads=1
cargo clippy --locked --offline --manifest-path $Eval --all-targets --features local-model -- -D warnings
cargo clippy --locked --offline -p locallore-desktop-spike --all-targets --features dev-harness -- -D warnings
cargo check --locked --offline -p locallore-android
cargo fmt --manifest-path $Eval -- --check
cargo fmt --all -- --check
node apps/desktop/verify-frontend.mjs
cargo build --locked --offline -p locallore-desktop-spike --bin locallore-desktop-spike
```

The frontend command used installed Node v24.22.1. Environment: Windows kernel
10.0.26300.0 X64, PowerShell7.6.5, rustc/cargo1.93.1, rustfmt1.8.0-stable,
TypeScript7.0.2, React19.3.1 and locked Tauri2.12.5. Dev/test Rust profiles were
unoptimized with debug/incremental output disabled. No packages or model assets
were downloaded or upgraded by this gate.

## Local evidence, retention and limits

Admission was 2GiB additional existing-target output and256MiB cumulative new
fixtures/logs, with one heavy Root workload and source-only authors. At
2026-10-29T21:55:11Z, retained evidence was169,937,569 bytes including24,646,523
bytes in recorded compatibility roots under D:/Dev/_Temp. The packet had9,689
files/145,291,046 bytes; target growth was43,357,289 bytes over8,259,980,576.
Later small provenance records are additional; nothing was deleted.

Original failing-run fixtures:7,884 files/90,369,432 bytes. Full per-file inventory
`default-first-fixture-freeze1.json` SHA256:
`af967f7c65a1d3d0a39f9c56848ef666ba919e0978a19d966e1316c6b0d02c4e`.
Its initial aggregate field was null due to a metadata summation mistake; a separate
summary sums the retained numeric row lengths without altering the inventory.
Every original file was rehashed unchanged after the focused/compatibility runs.
The failed log is retained with SHA256
`5232371200a180656b4696f63ad41520c3479c9318f96f10acad08687ab307cd`.
Raw/derived FIRST files, corrections, process records, complete logs, production
hash equality and normal-bundle recovery copy are retained in the same local packet.

The rebuilt normal frontend's four files are byte-identical to their prior normal
build. app.js SHA256 is
`61552ce15d51775d53cfa6f607c4230cf5a164b2a1ea52cd61d95dc56f59e9b2`.
Normal executable SHA256 is
`803136cac01c0b861b92d552aabe4c7b02d5c70f0a1671a80bf1ad3d0ed86d80`;
it was built but not launched. Frontend checks include mock transport/static HTML,
not native IPC or rendered pixels. No PNG, WebView, desktop capture/control,
model, Android SDK/emulator/device or stopped OS-boundary probe ran here.
offline-qualifier was compiled by Clippy but never executed.

PREPARATION_MS=120,000 remains a durable reservation and aggregate-capacity
allowance, not a hard blocking-filesystem timeout. The seven existing clock tests
exercise backdated accounting and pure absolute-turn deadline calculations;
the new14 do not wait through physical120s/60s boundaries. The after-arm control
is fixed cfg(test) cancellation after a real checkpoint, not process-death evidence.
Controlled loss/tamper affects only new synthetic fixtures. Cooperative locks/pins
and finite tests are not hostile-race or OS isolation qualification.

Both retained real-model human assessments remain **needs improvement**, with
no inferred scores or quality acceptance. Historical missing causes remain
missing. No real-model cohort, model asset or protected task resource was changed.
Dependencies/locks are unchanged; the previously tracked Linux glib advisory
remains separate from this Windows source/build gate.

The next runnable D07 gate is versioned desktop source4/selected3 routing,
native-owned consent/job/catalog reuse, strict frontend DTO/controller/view
integration and actual app-owned IPC/render journeys. Keep current unavailable
controls/notes until that separately accepted gate. Native selected4 remains a
later ownership/resource/cleanup and real-execution qualification task.

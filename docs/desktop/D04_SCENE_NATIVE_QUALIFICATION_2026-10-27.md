# Scene recipes in the native desktop harness

2026-10-27. Refs #25 D04.04/.05, supporting #23 D02.03/.04 and #26 D05
inspection. **Supporting slice in review; full tasks remain open.** Clean,
unchanged `879ffb450a7011e3c36606ddf24fee9c4e6919b2` passes the fixed synthetic
native cohort: four actual application processes, 324 distinct case-prefixed
assertions / 364 evaluations, and 24 application-owned WebView2 captures.
The launcher command takes 47.4844116 seconds, including builds and restoration;
that duration is not model latency or a gameplay performance benchmark.

No real model runs. The owner's original **needs improvement** assessment is
unchanged. This packet does not establish offline containment, prose quality,
phone support, accessibility, distribution approval or whole-D04 completion.

## Source and stack

The focused application delta is above Host/capture
[draft PR237](https://github.com/OptimumAF/LocalLore/pull/237), head `fcdc8785`.
That PR depends on [draft Core/Store PR232](https://github.com/OptimumAF/LocalLore/pull/232),
head `6a874e50`, with unmerged authoring prerequisites. Both are open, draft and
unmerged at this readback. Integration `2a920e0d` brings the Host head into the
application branch before executed 879. Relative to fcdc, the application
source changes are 18 desktop/bootstrap/contract files; there is no Core,
Eval, shared Store/workspace or Cargo.lock delta. This report adds documentation
only. A focused PR must preserve those dependencies rather than absorb or merge
their owners' branches.

The [Host/capture report](D04_SCENE_HOST_CAPTURE_QUALIFICATION_2026-10-27.md)
owns its separate Host, durability and Domain1 narrator-input gate evidence.
The [Core/Store report](D04_SCENE_RECIPE_CORE_QUALIFICATION_2026-10-27.md)
owns recipe validation, historical replay and archive evidence. Their earlier
results retain their exact source commits; they are not new whole-suite runs
at 879. Accepted receipt transport PR235 supplies the closed optional scene/
presentation shapes and its existing 46 controller/transport regressions.

## Small development boundary

The normal build does not enable synthetic free-text admission. `Controller`
uses a safe `typeof __DEV_HARNESS__` guard, default-false constructor permit and
bootstrap-only fixed scene case. Under both development gates it reads actual
bounded Host `model_status`; only the exact configured synthetic owner can
produce `freeTextProvider.kind=synthetic_fixture`. The real `ModelManager`
loaded/imported/resident state remains false. There is no fabricated loaded
model, renderer-selected policy/profile, new public Host selector or model
download. UI labels explicitly say **Synthetic scene fixture · no model
loaded**, alongside **Local durable workspace**. The existing normal loaded
model admission remains unchanged.

Domain1 checked thin snapshots are retained for the existing V2 panel only
under that development permit; the existing Domain2 V2 route remains. Native
Host construction selection is fixed to literal scene for the Domain1 parent
or memory scene for the real corrected Domain2 child. Rust owns preparation,
validation, receipts, scope/revisions, idempotency and canonical commit. The
frontend only presents checked DTOs and invokes existing controller/IPC paths.
No alternate persistence, inference runtime or memory implementation is added.

The development-only native fixture creates a fresh pinned Store with exactly
two named synthetic stories and the exact main/child catalog. The parent has
one real private Dialogue event; the child has a real typed author correction,
not a fabricated Domain marker. A read-only Store proof validates the complete
source prefix, allowed scene suffix/tuple/profile, selected head, counterpart,
other story and finite observer sentinels before installing a fixture provider,
including on restart. Foreign or extra-catalog databases refuse. The provider
is bound to the fixed selected scope and refuses foreign requests before role
output. Both actual Director and Narrator prompts reject synthetic forbidden
world truth, author reason and other-story markers. Player/Mira retain observed
A; Sable cannot acquire A or the private statement. These are finite synthetic
isolation checks, not a universal privacy or semantic-consistency proof.

`providerClosing` closes new provider-status reads synchronously when disposal
begins, before awaited invalidation; sequence fences discard late replies.
The development oracle is no-argument and read-only. Its command registration,
explicit allow entry and tracked generated allow/deny metadata remain narrow.
Normal application authority and the existing opaque Rust capabilities are
unchanged. Existing author-harness fixture/journey files are not modified.

## Actual native journeys

`scene-harness.mjs` takes no arguments. Trusted local environment supplies only
the already-owned artifact and Rust target directories; ordinary ancestors and
real paths are checked. It creates a new UUID cohort and new case databases,
never reuses/removes old evidence, scrubs inherited harness/test controls,
freezes source/product hashes and executes exactly literal/memory ×
initial/restart. No renderer supplies a workspace or executable path. The
WebView is hidden and unfocused; images use its own `CapturePreview`, without
desktop capture, activation or OS input.

The journeys mount the actual Main/V2 panel. The first send and both live and
cold inspection routes click actual mounted React handlers using application
DOM methods. Remaining operations use the same public controllers and native
IPC. Existing `FaultGateway` holds or drops acknowledgements after the real
call; it does not substitute receipts, state or generation replies. Native
read-only oracles bracket inspection and recovery. Snapshots retain selected
story/session/observer/head, pending operation, receipt and visible error.
`fixtureTarget` separately identifies the oracle's original scope/head when the
visible UI has switched to the other story.

| Case | Baseline / final head | Initial checks | Cold checks | Fresh prepares / role polls | Canonical new Wait commits |
| --- | --- | ---: | ---: | --- | ---: |
| Literal Domain1 main | 1 / 6 | 150 | 32 | 6 / 12 | 5 |
| Memory Domain2 corrected child | 2 / 7 | 150 | 32 | 6 / 12 | 5 |

Each initial journey covers an acknowledged scene receipt, actual same-object
receipt-to-clock comparison, ready-response hold/cancel, terminal exact retry
without new admission/generation, lost commit acknowledgement/status recovery,
lost admission/exact-key recovery, and held actual commits across story and
inspection-lens switches. Retired completions cannot publish receipts into a
new story or character lens. One prepared turn is cancelled; the other five
prepare results become the five real Store commits. Character inspection
cannot send/generate. Observed/world truth/author reason remain distinct in
actual Player, Mira and Sable queries and actual provider prompt sentinels.

Both cold processes reopen the same database at heads 6/7 with identical
canonical and observer fingerprints, zero provider factories/polls and zero
native/frontend errors. Raw live receipts remain null; no receipt is rebuilt
from history. A real recorded narration row's mounted button obtains its
original historical clock diff through existing Query2, with actual table
headers/values checked in the DOM. Cold inspection leaves canonical state and
observer knowledge unchanged. Each stage disposes controllers and observes
zero owned Host sessions/workers before finish.

Initial reports contain exactly two native `Cancelled` entries and one native
`Stale`. The latter is separately bound to the actual `play_snapshot_v2` read
during the held fifth commit, its fixed original scope, expected revision
baseline+4 and no turn field; the Store has advanced by one. Only that exact
read refusal is admitted. Other Stale operations, writes or phases are not
exceptions. The legacy error buffer is retained unchanged; separate bounded
rejection metadata explains the refusal. Cold reports have no such errors.

The canonical SHA-256 is preserved across reopen:

| Case | Canonical bytes SHA-256 |
| --- | --- |
| Literal | `6bb5f40dcc200f6d68331c6dacab602a45b4808a966004d5317ef710d6b1e60e` |
| Memory | `2027ca76e2d462257c354e4d969e9010b6bcc652a8d887362d93fa2b69c1dd5f` |

## Independent checks and retained failures

The first bootstrap checker at `29800c30` refuses setup because the proposed
public provider-status method is absent. This is not behavioral RED. The
implemented/calibrated `e50e1487` and `d105cbdb` pass 43 Controller-only cases
against synthetic Gateways. At `7271377a`, two additive disposal-window cases
actually fail: admission remains possible in the same tick as disposal, and a
held legacy cancellation window can resurrect provider readiness. Fix
`33ea2bc1` makes those unchanged cases pass: 43+2=45. The checker and full
frontend explicitly distinguish this headless/controller evidence from native
execution. Final frontend also reruns the 46 accepted receipt/transport cases.

Native fixture preflight at `0c56e141` passes four Rust tests; after finite
actual-role sentinel guards, `779080d9` again passes all four. They test closed
cases, fresh real Store/Host fixture/model separation, refusal before provider
installation for a foreign existing DB, and extra-catalog refusal. Strict dev
Clippy and full frontend also pass at 779. Early Prettier check at 0c56 fails
one panel-format warning; `82c67c59` passes the corrected check. These results
are not native WebView execution by themselves.

Five earlier launcher cohorts remain failed, with original logs/reports and
restoration records retained separately:

| Attempt / source | Actual stopping condition | Normal restoration |
| --- | --- | --- |
| First / `779080d9` | Native oracle command registered but missing Tauri permission; `not allowed. Command not found`, before screenshots | PASS, unlaunched |
| Second / `e55a174c` | Newly generated untracked `harness_scene_oracle.toml` trips the unchanged-source guard after build; no journey report | FAILED on same source guard; no restoration success claimed |
| Third / `b0abf839` | Strict final error oracle rejects actual `[Cancelled, Cancelled, Stale]` after 10 initial images | PASS, unlaunched |
| Fourth / `0ca33123` | Same strict refusal, now with bounded rejection evidence; 10 images | PASS, unlaunched |
| Fifth / `2a920e0d` | Knowledge-list target cannot fit below sticky header; bounds assertion fails before observer/enlarged capture, 8 images | PASS, unlaunched |

The permission fix is explicit and bounded; generated metadata is tracked
rather than ignored. Independent review calibrates only the exact old-head
read refusal at `395d74b7`, preserving other error checks and all recorded
failures. Render review finds actual receipt/recovery and knowledge data below
the viewport, an ambiguous unlabelled queued acknowledgement and missing
original-request scope after story switch. Presentation fixes add original
scope/from-revision and **Last Rust acknowledgement** labels; captures target
the actual receipt/table/observed-A paragraph. `879ffb45` corrects the fifth
attempt's overlarge list target. No canonical, privacy or error-buffer rule is
weakened to obtain visible images.

## Render review and bounded launcher limits

Every sixth-cohort image is reviewed individually, never as a contact sheet:
Root reviews 12 memory images; independent reviewer `narrator_frame_contract`
reviews 12 literal images. Each case has ten initial images (ready, receipt,
receipt-diff, pending, cancelled, unknown, recovered, switched, observer,
enlarged) and two restart images (restarted, recorded-diff). There are 22
620×900 captures and two 1280×900 captures. Review finds the intended receipt,
clock columns, observed knowledge and scope/operation/error labels readable,
with no blocking target-visibility or horizontal-overflow defect observed.
Long original turn IDs wrap; non-target content may extend below the viewport.
This is finite visual evidence, not full keyboard/screen-reader/text-scale
qualification. No screenshot alone proves canonical authority or privacy.

Captured stdout/stderr are capped at 256 KiB per stream; reports/snapshots at
256 KiB and images at 16 MiB. The closed launcher allows 900 seconds for Cargo
and 240 seconds for other children, then one direct-child kill attempt and a
five-second grace. Unknown owned drain blocks all further launches and skips
normal restoration. It records PID/kill/close observations without claiming
Job/process-tree containment or known descendant reap. Those timeout failure
branches are source-reviewed, **not exercised/qualified by this successful
cohort**. All eight actual child records exit zero without timeout, truncation
or unknown-drain flags. Successful restoration builds normal frontend and
normal native binary; both restored products remain unlaunched.

## Completed commands and environment

Run from `apps/desktop`, with a clean committed checkout, provisioned exact-lock
offline cache and existing ordinary task-owned target/artifact/TEMP directories.
Only the fixed launcher launches the hidden native app; do not invoke arbitrary
old diagnostic commands or reuse another process's occupied target.

```powershell
$taskNode = '<installed Node 24.22.1 executable>'
$ownedTarget = '<existing owned Rust target>'
$env:CARGO_HOME = '<existing isolated exact-lock package cache>'
$env:CARGO_NET_OFFLINE = 'true'
$env:LIBSQLITE3_FLAGS = ''
$env:LOCALLORE_M07_MEMORY_TARGET_DIR = $ownedTarget
$env:LOCALLORE_M07_MEMORY_ARTIFACT_ROOT = '<existing owned artifact directory>'
& $taskNode check-scene-bootstrap-review.mjs
& $taskNode check-v2-provenance-fields-review.mjs
& $taskNode verify-frontend.mjs
cargo test --manifest-path src-tauri/Cargo.toml --features dev-harness --locked --offline --jobs 1 --target-dir $ownedTarget scene_harness::tests -- --nocapture
& $taskNode scene-harness.mjs
cargo test --manifest-path src-tauri/Cargo.toml --locked --offline --features dev-harness --jobs 1 --target-dir $ownedTarget
cargo clippy --manifest-path src-tauri/Cargo.toml --locked --offline --features dev-harness --all-targets --jobs 1 --target-dir $ownedTarget -- -D warnings
cargo fmt --manifest-path src-tauri/Cargo.toml --all -- --check
cargo tree --manifest-path ../../Cargo.toml -p locallore-android --target aarch64-linux-android --edges normal --locked --offline
```

The launcher sets one build job, disabled incremental/debug info and fresh
fixed harness flags; existing TEMP/TMP stay task-owned. It builds development
frontend/native products, runs the four fixed processes, then rebuilds normal
frontend and native `--no-default-features` products without launching them.
The source guard intentionally refuses generated/untracked changes. No blanket
source ignore, arbitrary execution API, network server or model download is
introduced.

| Actual check | Source | Result / command seconds |
| --- | --- | --- |
| First four native fixture tests | 0c56e141 | 4/0; 50.4802766 |
| Four fixture tests with actual-role sentinels | 779080d9 | 4/0; 46.3149232 |
| Strict dev native Clippy preflight | 779080d9 | PASS; 12.3402044 |
| Full frontend preflight | 779080d9 | PASS; 18.4312241 |
| Fixed sixth native cohort | 879ffb45 | PASS, 364 evaluations/24 images; 47.4844116 |
| Full frontend final | 879ffb45 | PASS, includes 45 bootstrap + 46 transport cases; 17.0834428 |
| Default-parallel dev native regression | 879ffb45 | 251 unit + 2 contract = 253 passed, 0 failed, 9 ignored; 323.8238205 |
| Strict dev native Clippy final | 879ffb45 | PASS; 11.9024017 |
| Rust formatting final | 879ffb45 | PASS; 3.9670303 |
| Targeted 12-file frontend/config Prettier check | 879ffb45 | PASS; 0.8029328 |
| Android aarch64 normal dependency tree | 879ffb45 | PASS, zero Tauri/Wry/Tao/local-runtime hits; 0.3673386 |

All final process records report clean unchanged source. The native unit binary
takes 293.87 seconds; command time includes compilation/overhead. Nine ignored
tests remain ignored, not new passes. No `--test-threads` override is supplied
by the native command. Android evidence is dependency metadata only, not an
Android build, ABI/device execution or phone parity claim. Core/Store/workspace
and lock bytes match Host237 for that graph.

Windows NT10.0.26300 x64, Node24.22.1, Rust/Cargo1.93.1,
TypeScript7.0.2/React19.3.1/esbuild0.28.2, Tauri2.12.5/Wry0.57/Tao0.37.1;
no dependency upgrade. Actual captured user agent reports Windows x64 with
Chromium/Edge155.0.0.0. It is a WebView user-agent observation, not a separate
system-runtime inventory. No new real-model profile or performance measurement.

## Retained hashes and remaining scope

The local gitignored sixth cohort is `scene-native-cohort-4a2abb01-2061-43cb-93c3-1efdbf2971a9`.
Private files stay local; only public source paths and hashes are recorded here.

| Evidence/product | SHA-256 |
| --- | --- |
| Sixth source manifest | `c0df89cfe3745636db444dcbc0a8aafdfde78117b285016dad564fef14ecf0c5` |
| Sixth completed summary | `0d8e49acf552598a918e1f535a5e980b15a65d6e18952581d61c57d9126427f6` |
| Independent literal12 render manifest | `2b2a050380b25e9c689b034ca09195c315f5e4b2f1b8e1792363e3bd9fe9b90f` |
| Root memory12 render manifest | `4d5f1ca222efe7ae86b6e5216ca01658d3bae52d5b1ff1810a60c78aecd11e64` |
| Harness frontend | `a30edb7c98f334cc1eb30f9966917b0fde152534a0cc151f94aca7405c3a96f9` |
| Harness native executable | `e1d130210a288f533cffe48a8da9da28131a17105d531874d0bdfad6e144c795` |
| Restored normal frontend, unlaunched | `e8f713546d9d61add06aa79c774ad70fa4b68d08a8c3c5e8af8b795472fe9c5a` |
| Restored normal executable, unlaunched | `affa73afc1056164b9a27843127ca97769daeaae57e3fc319ff2f3a09f8917a1` |
| `apps/desktop/scene-harness.mjs` | `bfb1e4b3c4c71f204e696582f9a774f8ced4865be759dc80fef3a638b3e53a82` |
| `apps/desktop/ui/scene-native-journeys.ts` | `5970bd54434b3597d9ed2b7d17ecefc7a943cad06c75f0fff1201ea59265d5a7` |
| `apps/desktop/src-tauri/src/scene_harness.rs` | `b7d886619d282243692c75e398e2fb5ea3f8bcf5c0fda38d4401bcb997cc39e7` |
| `apps/desktop/ui/controller.ts` | `ffb11953e6fe7ae873990ed0c3be93f5940caf885032b5a6383d62f602d006fa` |
| `apps/desktop/ui/V2PlayPanel.tsx` | `bd188de294753538cea1871e08f20e947abfdda7fe7a3ee2e6b125ae05f27fc5` |
| Unchanged `Cargo.lock` | `4fb7c498ca0ecc62c4ea1f65c63b370ab4336eb75133d08b3a71f5664156cf93` |

This is a fixed synthetic Wait-only cohort. It does not exercise a new real
potion/secret/invalid-action model scene, authored-world scene support, arbitrary
free-text semantics or universal observer privacy. The V2 view honestly reports
legacy debugger/inspection export/timeline/maintenance views unavailable for
unsupported domain adapters. No fallback grants knowledge or changes generation
actor. Native IPC/render/reopen success does not convert the separate Domain1
capture gate into Domain2 output authentication. Model import/load, real local
inference, measured quality/performance, blocked-network execution, package/
licensing and physical-phone gates remain with their owning tickets. No merge,
release or settings change is authorized by this report. Next gate is focused
dependency-aware review and owner acceptance, followed by separately scoped
real-model scene/evaluation work retaining the original human assessment.

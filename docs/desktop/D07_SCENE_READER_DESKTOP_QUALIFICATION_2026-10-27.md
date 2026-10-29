# Protocol4 desktop reader: native qualification and retained failures

2026-10-27. Refs #29 D07.06, supporting #25 D04.04. **In review; the bounded
two-stage reader cohort passes at `8af4f9f9`.** This draft records the integrated delta
from owned base `939a6f8e80b1efa8dc599ad3b2b7734ee1494d9b` through
`8af4f9f92354c7d76309909dc3c5027e0f64bd22`. Native Rust controls and frontend
decoder/regressions retain their exact source attribution below. The first two
application cohorts failed and remain unchanged; the second produced14 initial
images and no restart stage. The third passes 137 checks in each stage and
produces 30 individually reviewed application-owned native WebView images.
This qualifies the fixed reader journey, not the whole D07 milestone, native
Protocol4 comparison execution, installed assets or release. The original
eight-sample human judgment remains
**needs improvement**. No new model inference or prose-quality result exists.

## Implemented scope and authority

The native existing reader lifecycle adds a typed V4 retained facade alongside
V2/V3. Each attempted adapter validates its actual source; a renderer version
cannot select an unchecked importer. Failed adapters drop their temporary locks;
all-invalid sources retain the existing V2 error-category contract. A successful
V4 capability uses the existing native picker/grant, lease, worker, token,
binding, close/drop and access-time expiry rules, not a parallel reader owner.

The [Core reader](D07_SCENE_READER_QUALIFICATION_2026-10-27.md) remains the actual
Store/checkpoint/source validator. Frontend source/report/row4 is a separate
closed transport variant with exact15-field descriptors and required explicit
nulls. New narrator prompt/schema/frame/receipt hashes, construction reason,
finite privacy status, failure causes, source-bound row count and opaque
diagnostics are retained. Unknown fields, unsupported tuples, unsafe numbers,
getters/prototypes/cycles, mismatched identities and existing budgets refuse.
Decoding metadata is not canonical validation or evidence-origin authentication.

Summary is the immutable last-validated snapshot; selected evidence revalidates
its actual Store source and checkpoint. Omniscient raw access and Rust Query2
observer filtering remain authoritative. Privileged inspection does not change
character knowledge or generation access. Finite sentinels are diagnostics, not
universal privacy. The fresh committed Domain1 narrator-input gate does not
authenticate Director/compiler/provider execution or raw output origin; failed,
cancelled, recovered and unavailable evidence retains its actual status/cause.

Selected execution for source4 stays unavailable: App supplies no selected source
identity, the mounted prepare control is disabled, and the actual typed native
selected adapter accepts source2/3 only. Native source4 refuses before plan,
consent, selected output or model reservation. Existing source3→selected2 remains
supported; its obsolete unavailability banner/assertion was explicitly corrected.
The old unknown-future decoder sentinel advanced4→5 because4 is now supported.

The fixed dev-only harness uses actual shared scripted Host/Store/capture/Core
V4 paired two-scene and rollout one-scene fixtures. It never substitutes fake
receipts/captures/query pages. Mounted controls/public controllers use native IPC;
images use app-owned WebView2 CapturePreview, with no desktop input or capture.
Fresh UUID workspace ancestor handles are retained across fixture creation after
the reviewed6069081e lifetime correction. The harness adds no arbitrary caller
path, code/shell endpoint, model selection, schema/default or canonical writer.

## Independent baseline, corrections and actual checks

All command durations below are wall time from the corresponding retained
`*-process.json`, not latency benchmarks. Each listed record reports clean,
unchanged source. Local evidence is under gitignored
`author-integration-artifacts`; table prefixes identify its matching JSON/log.

| Evidence prefix / check | Exact source prefix | Actual result | Seconds |
| --- | --- | --- | --- |
| d07-scene-v4-native-reader-baseline1 | 497376f4 | 2 passed,6 failed,0 ignored; exit101 | 75.2571103 |
| d07-scene-v4-native-reader-first-green1 | aa3834cb | unchanged8 passed,0 failed; exit0 | 69.2416862 |
| d07-scene-reader-frontend-baseline1 | 2735bf7b | 160 passed,14 positive cases failed of174; exit1 | 0.3501064 |
| d07-scene-reader-frontend-first-green1 | db2ee7de | unchanged174 passed,0 failed; exit0 | 0.3544754 |
| d07-scene-reader-frontend-full-corrected1 | 384bf4a1 | full frontend PASS; exit0 | 19.4742612 |
| d07-scene-reader-combined-frontend3 | 6a38af11 | full frontend PASS; exit0 | 17.5763196 |
| d07-scene-reader-combined-native-dev1 | 6a38af11 | 259 desktop +2 artifact controls passed,0 failed,9 ignored; exit0 | 370.7298810 |
| d07-scene-reader-combined-native-clippy1 | 6a38af11 | dev-harness/all-targets, warnings denied; exit0 | 20.0361842 |
| d07-scene-reader-combined-rustfmt1 | 6a38af11 | Rust format PASS; exit0 | 2.7763159 |
| d07-scene-reader-context-full-frontend1 | a0e7ed2d | full frontend PASS; exit0 | 18.7473016 |
| d07-scene-reader-context-format1 | a0e7ed2d | focused Prettier check PASS; exit0 | 0.8798265 |
| d07-scene-reader-harness-frontend-corrected1 | 9868de4f | full frontend PASS; exit0 | 19.7605783 |
| d07-scene-reader-harness-first-clippy1 | 9868de4f | strict native Clippy PASS; exit0 | 12.1488734 |
| d07-scene-reader-harness-first-rustfmt1 | 9868de4f | Rust format PASS; exit0 | 3.3528041 |
| d07-scene-reader-diagnostics-frontend1 | 97106af7 | full frontend PASS; exit0 | 17.9810746 |
| d07-scene-reader-diagnostics-clippy1 | 97106af7 | strict native Clippy PASS; exit0 | 10.6376864 |
| d07-capture-session-close-final-frontend1 | 8af4f9f9 | full frontend, including unchanged five capture-close checks PASS; exit0 | 17.8190379 |
| d07-scene-reader-native-cohort-third1 | 8af4f9f9 | actual initial137 +restart137 checks PASS; exit0 | 261.0713470 |

The native8 controls are Rust manager/actual shared Store tests, **not Tauri
IPC/WebView execution**. They cover version4 data, observer edges/receipt,
version2/3 controls, picker grants/cancel/late close, scope/token/binding/source
mutation, held evidence retirement, bounded source refusal and both-lane early
selected refusal. Frontend174 are synthetic DTO decoder checks, not Rust/native
source proof. Negative4 refusals were not counted as meaningful new support
before its14 positive controls passed. Nine ignored native cases remain ignored;
the native suite used default test concurrency, with one Cargo build job.

Retained prerequisite failures were not erased. db2ee7de's first full frontend
run exited1 in1.1061406s on three V3-only literal fields accessed on the V3/V4
union;384bf4a1 retained versioned scene fields instead. Combined frontend1 used
the wrong working-directory path and failed setup; corrected invocation2 exposed
the obsolete source3 unavailability expectation, corrected at6a38af11. The
6069081e first harness frontend check failed four `never`-type fixture-proof
accesses;9868de4f declares that type independently. These are retained setup/type/
expectation corrections, not weakened source4 evidence or native-pass claims.

The frozen174 checker's original SHA256 is
`e8d1cad19dcdeb2bdc6f2e07d1c10365f8f238185ccb878d57a3ad5c6bcaa781`;
formatted source is
`ea1a12abbdc764b62311f31ed27a10ff249a2596f851a918f04e73332fd978e3`.
Retained `d07-scene-reader-format-equivalence1.json` records both normalized
SHA256 values as
`b681652df855645f8514250a7d68c01c269e9f9461456347b7bf33d92f84b222`
using identical pinned esbuild transform/minification options. It reports
normalizedCodeIdentical=true; this compares source without executing the checker,
not semantic privacy or native qualification. Independent source reviews at164,
606 and971 found no remaining source blocker after the pin lifetime correction;
source review did not establish later application success.

## First actual application cohort: retained failure

Packet `comparison-reader-native-e2469db1-bc3b-4808-89cd-b7534752978c`
binds9868de4f. Frontend/native harness builds exited0. Initial app ran199.870s,
closed with exit2 and27-byte stderr `D02_NATIVE_HARNESS TIMEOUT`; the outer
launcher timeout did not fire and no kill was attempted. Its report failed
`mounted-picker-actual-native-ready`, with cleanup-visible Closed. That category
does not establish the original open failure. No PNGs and no restart stage were
produced. The failed packet remains unchanged, not replaced by a favorable run.

Normal frontend/native restoration then exited0 in0.452s/19.329s, with normal
products **UNLAUNCHED**. This reports observed direct-child close, not Job or
descendant containment. The source process record exits1, unchanged source.
Failure-observation SHA256:
`2ed366b04e1b0c83dc7863b30bb0fc953f340a730a38733030a4fef1c59bd406`;
initial report:
`c767fe79d91d1c49dc0ca9ebc6fa654a00bfa77169dad6ac46127a498520ef28`.

97106af7 preserves bounded original scalar failure state before cleanup and
adds check timings. Its development-only scene cohort watchdog is900s, outer
launcher960s; this changes no model/turn/role budget or evidence assertion.
Timeout/error-with-PID still means unknown owned drain, one direct-child kill
attempt and5s grace, no later spawn and skipped/unqualified restoration. Node
ordinary-ancestor checks are validation, not persistent hostile-filesystem pins.
There is no Job/process-tree or executed timeout-drain qualification.

## Second actual application cohort: retained failure and14 renders

Packet `comparison-reader-native-52cc6dd0-90e2-48ac-b9f7-f5b7dcaff819`
binds97106af7. Builds exited0. Initial app closed with exit1 after148.855s,
no stderr, no watchdog/outer timeout or kill, and no unknown-drain flag. Its
report retains133 successful check labels, then fails
`only-deliberately-lost-open-ack-error-recorded` at147357ms. The bounded original
comparison error/phase/source are null, busy/uncertain false. Error evidence
contains expected native Transport from lost acknowledgement **and unexpected
native Closed**. This assertion was not waived. No finished PNG or restart stage
exists; no two-stage native qualification or cold-reopen inventory pass follows.

Prior labels include actual mounted reads, actor raw/stale-binding refusals,
pending close, same-client acknowledgement recovery, rollout read, actual new
Host session for the same canonical story, source4 reopen, Play/lens retirement
and unchanged live gameplay canon. Those observations remain partial rather
than a passed whole journey. Snapshots through rollout contain only Transport;
switched adds Closed. Source inspection identifies a concrete candidate:
CaptureController.contextChanged queues `revoke(oldSession)` after Host close
has completed, and its shared IpcGateway may record Closed from the old-session
trace_capture_revoke. Actual operation provenance is not yet recorded, so the
cause remains a hypothesis requiring a regression/trace, not an assertion waiver.

Normal frontend/native restoration exited0 in0.332s/12.762s; both normal products
remain **UNLAUNCHED**. Failure-observation SHA256:
`62aacfc1130cde489becb5e1c037875200d883f6efba9e03977f5d85615615f9`;
initial report:
`dec1d1dcc1b1761c0d7fde6b8e0aff80c8298d00aa9c20ea2fba841ed041d5bc`.
Harness JS product is
`f8068f50ffedbe06c9fbe3911fa89cea7730ab958dd3649931dc0bd2f450921e`;
executable is
`7f51aaf11a352f9b89ff5bec60cff36ef32d4b91f6917b2ac52abe3173614e22`.
CSS/HTML match its retained product manifest. Hash consistency is observation,
not build/provider-origin authentication. Failed launcher observation has no
completed artifact qualification seal.

All14 initial PNGs below were viewed individually with the local image tool,
without contact sheets or desktop capture/control. Paired/rollout table targets
fit under the cached protocol/observer header; bounded receipt/capture/output
content fits under selected scope/heads/lens; narrow status/hash text wraps without
horizontal clipping. Mira's witnessed statement is visible, Sable history is
empty, and no player-private secret is visible in those actor render targets.
Guard receipt is explicitly unavailable and selected4 admission is disabled.
Pending/closed/unknown/recovered/switched states are readable. No material target
layout defect was found; this finite image review does not prove all hidden DOM,
all privacy semantics or absent native errors. Human0/not_reviewed/qualityfalse
is retained in actual summary metadata; it is not inferred from a passed row.

| Exact initial PNG | Viewed content/finding | SHA256 |
| --- | --- | --- |
| comparison-open.png | paired table, Protocol4/Omniscient, synthetic limits, disabled prepare | a1bc337253acea1a213c40e8c04d838b28d0e22fa808f22265cef93694079a69 |
| comparison-receipt.png | selected scope0→1, actual witnessed statement in bounded receipt | e2df478b3b9d9e7077764782fda608aeb5d02a09f3c81b4c97f2907b852d9a34 |
| comparison-capture.png | actual generation_request target under selected scope header | be88ff039dcc0e8ad95ba3024e7fc5fae0b26583c0d79f7db50db3ef51f35753 |
| comparison-outputs.png | Director/Narrator recorded outputs and hashes, no model claim | 133762b48a89223748baadbc11a4fa0d7e05dee0888f490d2ee7257717de3b7d |
| comparison-narrow.png | finite diagnostic label and prompt/schema/frame hashes readable | 8010d044d5e46b9c6a9c3a7624be10a953f5a57da46388eab42d0cdbe70ddca0 |
| comparison-mira.png | Mira header and witnessed dialogue; bounded history target | f715cc7706bc80aeab2b88f05643bf50cbc5e10f3cea02ca8c0a22c593e99339 |
| comparison-sable.png | Sable header, private_character/history, empty rows | 625a9b84d6f4e6b9b5a4e5a9d16ed3d8245bf8c3a152e761a150368e8a7c8061 |
| comparison-guard.png | courier09 head8→8, no_accepted_receipt, disabled source4 prepare | 92f8bab97457290896be1f6c6f8f1f974db29de3efc36e9a141c2b1ba4ded076 |
| comparison-pending.png | choosing/work pending; open disabled and close enabled | 80fccebf8ddcfa8d12a565e99d56908c50e93c07a547a363319691c54c864dfd |
| comparison-closed.png | closed state, source/evidence absent, open available | 893a2c66b1e94345b6365a3ddf649240cb2472920f5c390361f3ee6fd6dc5772 |
| comparison-unknown.png | acknowledgement unavailable and EvaluationIo, recovery available | c1e137b4d49bd00e7012e840b9d2c7c750dadb4879f267480eb1a53417f4d9d7 |
| comparison-recovered.png | ready same source, private report hidden until requested | b3f3e7d5c33a623d88de65ffc46585c5c94bc8e032f6fa893944155eccf38e0e |
| comparison-rollout.png | rollout table with actual rows and cached source4 header | 6d0d8aefa988060fb4c044365882a490631c25f8b924c2f7c65539e99bf676a8 |
| comparison-switched.png | no report open, private presentation retired | 57001a7ff38057d966c3cbbcde1c6255101e697cc93781683ae7a4d155516848 |

## Capture retirement correction and third native cohort

The [capture-close contract](D07_CAPTURE_SESSION_CLOSE_CONTRACT_2026-10-27.md)
retains the independent ordered-transport regression and its measured failures.
Its original four checks first measured 1 pass/3 failures, then 4 passes unchanged.
An additional subscriber-failure oracle then measured 4 passes/1 failure and,
after the private closing-count `finally` correction, 5 passes unchanged. These
are synthetic ordered Host-session transport tests using actual controllers,
not native timing or proof of the exact operation behind the second cohort's
Closed. The production correction forwards the actual closing Session through
the existing coordinator, retires matching capture access before Host close,
and preserves unrelated capture B and listener-failure recovery. It does not
suppress Closed globally or waive any native assertion.

Third packet `comparison-reader-native-9186da8c-40c9-40a4-99df-f7c299585914`
records clean, unchanged `8af4f9f92354c7d76309909dc3c5027e0f64bd22`.
The command exits 0 in 261.0713470s, including builds and normal restoration.
Initial and restart each pass 137 check evaluations; these are two executions
of the fixed journey, not 274 distinct independent oracles. Both use actual
mounted controls/public controllers, Tauri IPC and a hidden, unfocused native
WebView2. The shared scripted producer creates real Store/Host/capture evidence
for two paired scenes and one rollout scene; `modelExecution=false` and
`realModelGeneration=false`. Native picker doubles are fixed application-owned
cases; OS dialogs are not automated.

Both stages validate actual source/report descriptors, receipts, narrator
captures, recorded role outputs and preserved source-bound row count. They
exercise Mira/Sable/Player query edges, actor raw refusal before binding/row
probes, stale binding, guard receipt absence, disabled selected4 admission,
pending close/late picker, deliberate lost ACK/same-client recovery, rollout,
real Host session close/new session and Play/lens retirement. Live gameplay canon
is unchanged. Every one of 626 fixture file hashes matches the original after
initial reads and again after cold restart. This is observed bounded byte
equality for these fixture files, not universal filesystem or execution-origin
authentication.

Each stage retains exactly one expected native Transport error from the
deliberately lost acknowledgement, with no Closed error. App stderr is 0 bytes
in both stages; app stdout records `D02_NATIVE_HARNESS PASS`. The strict final
error oracle passes unchanged. There is no claim of an error-free application
in all circumstances, nor of actual process-death or unknown-drain testing.

| Actual execution | Exit | Wall seconds | App stderr bytes |
| --- | --- | --- | --- |
| Harness frontend build | 0 | 0.365 | — |
| Harness native build | 0 | 13.794 | — |
| Initial native app | 0 | 148.332 | 0 |
| Restart native app | 0 | 79.916 | 0 |
| Normal frontend restoration | 0 | 0.366 | — |
| Normal native restoration | 0 | 15.375 | — |

All six direct children report known closure, no timeout, no kill attempt and no
unknown owned drain. The normal products are restored and **UNLAUNCHED**.
This does not qualify Job/descendant containment or the unexecuted timeout path.
The fixed launcher still refuses any later spawn/restoration after unknown
owned drain; ordinary ancestor checks do not pin against hostile replacement.

The broad 259-unit +2-contract Rust result remains attributed to `6a38af11`.
Source comparison shows later Rust changes in `comparison_reader_harness.rs`
and `main.rs`; do not report that broad suite as a full run at8af. Conversely,
there is no `.rs`, Cargo manifest or Cargo.lock delta between `97106af7` and
`8af4f9f9`, so the strict native Clippy record at971 applies to those unchanged
Rust bytes. The final full frontend result and actual native build/journey are
directly measured at8af. No additional broad Rust/Android/model suite is inferred.

The retained source manifest binds all inputs. Selected SHA256 values are:

| Input/product | SHA256 |
| --- | --- |
| comparison-reader-harness.mjs | f6621fde316e19b8d88d3ebe76d033d1a981f15474527797105c8e5b9316d921 |
| ui/comparison-reader-journeys.ts | cf2e90a5e1d5592a8d404e96ec24545872ad8e99eccbbacf99cfb25e910fac09 |
| ui/ComparisonReaderPanel.tsx | eb547a1f8db83100634e383a4b2b3a95e06736b52d0528ba8f9b18999bcdaf89 |
| Harness app.js | 9b0ecb585e5d4d1aff62b24aa579ac6bc03acb895dcd0fa435afe2ea115044b9 |
| Harness executable | 4296fa956880cd68778b7d7f639115b678d88375e86a79810c64ad94a7e206a9 |
| Restored normal app.js | fd331de282f7936dcf0159869a003c832e23d1be40c3135b876422478888508b |
| Restored normal executable | 7b94650b182c5a258ea9c08094688192306de30f3fc15d9db60eca19f4e1c4d9 |

The process record SHA256 is
`8ae2c06b15d457c6a79dad8528704fefb0d3b524f132048f319beb987912e457`;
qualification JSON:
`25a2a96bde8197e4a9e199a1700f2fa2fa8a1e2d16f82b1288b3401bb2f88e8d`;
source manifest:
`5ea8542aac98cbfd8cc9afb13ee21b3e495b1e59c113b670c4664329f02a4812`;
product manifest:
`2c791fc2202f4ddcc3a0ae7aa90082fc54542f97e9af0c1b803abbc71d609afd`;
normal-restoration record:
`4b523bb880ad17b9c4d8915f7e382931296dc668b80627e37f627fca4e620c36`.
These hashes identify private retained evidence; no raw evidence is committed.

## Third cohort: all 30 individual render reviews

The independent contract reviewer inspected all 15 initial PNGs individually,
against initial report SHA256
`0a95cfb1c5cef7bdeea8962683c1996a8e214f44a01a3ebc2a2689c8c32b4626`.
Root inspected all 15 restart PNGs individually and recorded
`restart-individual-render-review.json`, SHA256
`dcb2c8ca73ab2775707b1260c1393a1b832700bad5ca8f344e72afb3684ab36f`.
Restart report SHA256 is
`6ae8bbdbd1e3c30e7d021cfa7f10a27bf39de303222a4b97cf1d4268b1e8f90e`.
This documentation update reads those handoffs and actual file hashes; it does
not claim its author personally re-viewed the 30 images or ran the app.

All wide images are 1280×900; the two narrow images are 620×900. Reviews found
selected scope/heads/lens/phase and bounded receipt/input/output readable,
prompt/schema/frame hashes wrapping in the narrow target, Mira's witnessed
dialogue and Sable's empty history, explicit guard receipt unavailability, and
coherent pending/closed/unknown/recovered/retired states. No material target
layout defect was reported. Evidence/table scrolling and partial surrounding
content are intentional. Finite visible targets are not whole-page access,
universal privacy, keyboard/screen-reader or human prose-quality proof.

The following roster names all 30 PNGs. Each pair's SHA256 was independently
read from both actual files and is equal; equality is not a claim of universal
byte reproducibility or model determinism.

| Initial PNG | Restart PNG | SHA256 of each |
| --- | --- | --- |
| initial/comparison-open.png | restart/comparison-restarted.png | a1bc337253acea1a213c40e8c04d838b28d0e22fa808f22265cef93694079a69 |
| initial/comparison-receipt.png | restart/comparison-receipt.png | e2df478b3b9d9e7077764782fda608aeb5d02a09f3c81b4c97f2907b852d9a34 |
| initial/comparison-capture.png | restart/comparison-capture.png | be88ff039dcc0e8ad95ba3024e7fc5fae0b26583c0d79f7db50db3ef51f35753 |
| initial/comparison-outputs.png | restart/comparison-outputs.png | 133762b48a89223748baadbc11a4fa0d7e05dee0888f490d2ee7257717de3b7d |
| initial/comparison-narrow.png | restart/comparison-narrow.png | 5b42bfbb178e862fc149a13eaa1dab8c06fef0e81b88edc5a42f7e90a9f90ae9 |
| initial/comparison-mira.png | restart/comparison-mira.png | f715cc7706bc80aeab2b88f05643bf50cbc5e10f3cea02ca8c0a22c593e99339 |
| initial/comparison-sable.png | restart/comparison-sable.png | 625a9b84d6f4e6b9b5a4e5a9d16ed3d8245bf8c3a152e761a150368e8a7c8061 |
| initial/comparison-guard.png | restart/comparison-guard.png | 92f8bab97457290896be1f6c6f8f1f974db29de3efc36e9a141c2b1ba4ded076 |
| initial/comparison-pending.png | restart/comparison-pending.png | 80fccebf8ddcfa8d12a565e99d56908c50e93c07a547a363319691c54c864dfd |
| initial/comparison-closed.png | restart/comparison-closed.png | 893a2c66b1e94345b6365a3ddf649240cb2472920f5c390361f3ee6fd6dc5772 |
| initial/comparison-unknown.png | restart/comparison-unknown.png | c1e137b4d49bd00e7012e840b9d2c7c750dadb4879f267480eb1a53417f4d9d7 |
| initial/comparison-recovered.png | restart/comparison-recovered.png | b3f3e7d5c33a623d88de65ffc46585c5c94bc8e032f6fa893944155eccf38e0e |
| initial/comparison-rollout.png | restart/comparison-rollout.png | 6d0d8aefa988060fb4c044365882a490631c25f8b924c2f7c65539e99bf676a8 |
| initial/comparison-switched.png | restart/comparison-switched.png | ddec69c569e82e0d3182fe7eb5ddf171948e168b3117e1f5845b9c4e8add305f |
| initial/comparison-finished.png | restart/comparison-finished.png | ddec69c569e82e0d3182fe7eb5ddf171948e168b3117e1f5845b9c4e8add305f |

## Reproduction and remaining gates

Use the existing exact-lock offline cache, ordinary private artifact/target/TEMP
directories, one heavy slot and recorded Windows x64 environment. Retained
provisioned versions are Rust/Cargo1.93.1, Node24.22.1, Windows10.0.26300;
the current batch's process records do not reprint a new toolchain-version probe.
Locked package versions include esbuild0.28.2, TypeScript7.0.2, React19.3.1,
Prettier3.9.10, Tauri2.12.5, Wry0.57.0 and Tao0.37.1. The third cohort's actual
wide/narrow semantic snapshots record Chromium/Edge155.0.0.0 in their Windows
x64 user agent. That is a WebView user-agent observation; no independent
installed WebView2 runtime-version inventory was recorded. No dependency/model
download or upgrade accompanies this slice.

From the repository root, command forms (substitute existing owned paths) are:

```powershell
node apps/desktop/verify-frontend.mjs
cargo test --manifest-path apps/desktop/src-tauri/Cargo.toml --features dev-harness --locked --offline --jobs 1 --target-dir $ownedTarget evaluation::comparison::scene_read_review -- --nocapture
cargo test --manifest-path apps/desktop/src-tauri/Cargo.toml --features dev-harness --locked --offline --jobs 1 --target-dir $ownedTarget
cargo clippy --manifest-path apps/desktop/src-tauri/Cargo.toml --features dev-harness --all-targets --locked --offline --jobs 1 --target-dir $ownedTarget -- -D warnings
cargo fmt --manifest-path apps/desktop/src-tauri/Cargo.toml --all -- --check
```

From apps/desktop the fixed launcher accepts no arguments. With clean source,
the existing locked offline cache, no SQLite custom flags and ordinary existing
task-owned directories, its command form is:

```powershell
$env:LOCALLORE_D07_LITERAL_COMPARISON_READER = "0"
$env:LOCALLORE_D07_SCENE_COMPARISON_READER = "1"
$env:LOCALLORE_D07_COMPARISON_READER_ARTIFACT_ROOT = $ownedArtifacts
$env:LOCALLORE_D07_COMPARISON_READER_TARGET_DIR = $ownedTarget
node comparison-reader-harness.mjs
```

The launcher builds harness products, runs initial/
restart against the same new UUID fixtures, checks source/products/semantic
artifacts/inventory and restores normal frontend/native builds in finally only
after known direct-child closure. Every failed attempt must remain retained.

The ordered capture-close/listener regressions and the complete third native
cohort now provide the bounded reviewable gate; neither historical failure is
reclassified. Next is coordinator review of this packet/PR #243, followed by
the separately owned native Protocol4 comparison service/transport qualification.
That work needs its own source, asset availability, consent/runtime ownership
and genuine completed-native resume evidence. This reader packet grants none
of those capabilities and does not qualify future native model harness changes.

No new Android compatibility/device cohort, model comparison, D09 offline
security, general accessibility or human-quality gate ran for this slice.
Selected source4 execution remains unavailable. The original human
needs-improvement assessment remains unchanged. Protected chat/resources were
untouched and no desktop control was used. This documentation update ran no
tests/builds, formatter or apps; it reads bounded owner-produced records and
attributes the individual render reviews explicitly above. No task checkbox,
merge/release/settings change or quality approval follows.

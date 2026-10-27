# Protocol4 desktop reader: partial qualification and retained failures

2026-10-27. Refs #29 D07.06, supporting #25 D04.04. **In review; native
cohort gate FAILED and remains open.** This draft records the integrated delta
from owned base `939a6f8e80b1efa8dc599ad3b2b7734ee1494d9b` through
`97106af761bb4f26354a3b484be89e36fc7f29d9`. Native Rust controls and frontend
decoder/regressions pass at the sources below. Both attempted application
cohorts failed; the second produced14 individually inspected initial images,
no finished image and no restart stage. Neither cohort qualifies the planned
two-stage native journey. The original eight-sample human judgment remains
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

## Reproduction and remaining gate

Use the existing exact-lock offline cache, ordinary private artifact/target/TEMP
directories, one heavy slot and recorded Windows x64 environment. Retained
provisioned versions are Rust/Cargo1.93.1, Node24.22.1, Windows10.0.26300;
the current batch's process records do not reprint a new toolchain-version probe.
Locked package versions include esbuild0.28.2, TypeScript7.0.2 and Prettier3.9.10.
No dependency/model download or upgrade accompanies this slice.

From the repository root, command forms (substitute existing owned paths) are:

```powershell
node apps/desktop/verify-frontend.mjs
cargo test --manifest-path apps/desktop/src-tauri/Cargo.toml --features dev-harness --locked --offline --jobs 1 --target-dir $ownedTarget evaluation::comparison::scene_read_review -- --nocapture
cargo test --manifest-path apps/desktop/src-tauri/Cargo.toml --features dev-harness --locked --offline --jobs 1 --target-dir $ownedTarget
cargo clippy --manifest-path apps/desktop/src-tauri/Cargo.toml --features dev-harness --all-targets --locked --offline --jobs 1 --target-dir $ownedTarget -- -D warnings
cargo fmt --manifest-path apps/desktop/src-tauri/Cargo.toml --all -- --check
```

From apps/desktop the fixed launcher accepts no arguments. Set
LOCALLORE_D07_SCENE_COMPARISON_READER=1 and its existing trusted
LOCALLORE_D07_COMPARISON_READER_ARTIFACT_ROOT/TARGET_DIR variables, then run
`node comparison-reader-harness.mjs`. It builds harness products, runs initial/
restart against the same new UUID fixtures, checks source/products/semantic
artifacts/inventory and restores normal frontend/native builds in finally only
after known direct-child closure. Every failed attempt must remain retained.

Next runnable task is an independent ordered session-close/capture-retirement
regression and bounded operation provenance for unexpected Closed, followed by
a focused source fix, unchanged checks and a new explicitly attributed native
cohort. Both complete stages, every expected image and inventory/error check
must pass before claiming native qualification. No stage/check is waived here.
No new Android compatibility/device cohort, model comparison, offline security,
accessibility or human-quality gate ran for this slice; those remain unavailable
as current-source evidence. Protected chat/resources were untouched and no
desktop control was used. This documentation author ran no tests/builds or apps;
it reads bounded owner-produced logs/JSON and individually views14 app images.
No task checkbox, merge/release/settings or quality approval follows.

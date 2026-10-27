# Native full-comparison consumer qualification, 2026-10-26

Refs #29 (D07.03–D07.06 supporting consumer slice), #21.

This document records the frontend consumer's qualification. The accepted native
service is PR #214, merged as `61431c0e243617e287053dcf3f3b9ebc0d837eef`.
Its Rust service, actual installed-model and scripted native WebView evidence
are historical service evidence; they do not qualify this newer frontend.
The consumer contract is
[the frozen interface document](D07_NATIVE_FULL_COMPARISON_CONSUMER_CONTRACT_2026-10-26.md).
Whole D07 acceptance, human quality review and physical-phone gates remain open.

## Test boundary

The new checkers bundle actual controller/model/view source with installed,
pinned esbuild. Controller/reader tests use bounded synthetic IPC responses.
The Main checker uses actual Main, App and ComparisonRunView source with a
bounded React hook/JSX fixture and unrelated leaf stubs. Its five fixed exports
are appended only to the checker input, never production source. Importable
fixture helpers are test code; importing them does not rerun its twenty cases.
These checks are mock/headless evidence, not native IPC, WebView, OS consent or
model execution. A direct invocation is `node <checker>.mjs` from `apps/desktop`.
`LOCALLORE_CHECK_OUTPUT_DIR` selects a local ignored report directory.

## Recorded initial executions

All cohorts below recorded a clean source commit and verified the source stayed
unchanged through the command. Logs and machine-readable process/report files
are retained locally, outside the checkout; private absolute paths are omitted.

| Cohort/source | Actual result | Interpretation |
|---|---|---|
| `baseline1`, `ae4065ce35e7362f4275505ec0fd0ed40b6d820b` | Legacy 56/56; native controller 1/85; native reader 2/22; Main 0/20 | Missing feature APIs/fields. Transpilation succeeded. Main failed setup before exercising twenty mode behaviors. These are not semantic regression reproductions. |
| `first1`, `c9ade43de19fc14779b5f3cb95233e627c534a86` | Legacy 56/56; native controller 87/88; reader 22/22; Main 20/20 | One semantic failure: closing a sent native start with unknown ACK and no token left current uncertainty set after captured UUID recovery/close settled. |
| `tsc-first1`, same `c9ade43d` | TypeScript exit 1, one TS2322 | Existing scripted development journey passed the newly widened status union into a V1-only helper. |
| `tsc-second1`, `1c0fcfb13d91c04596cd048100859f3a8d3cbe3b` | `node node_modules/typescript/bin/tsc --noEmit`, exit 0 | Commit `50f154e3` explicitly narrows actual version 1 status; no V2-to-V1 conversion or cast. Source clean/unchanged. |

The 88 controller cases include the original frozen packet plus independent
one-shot cleanup observations after retired running/unknown/cleanup-flag closes
and the unknown-start-ACK/no-token case. The old 56-case checker was not rewritten
to accommodate native behavior. The reader packet has 22 declared cases and Main
has twenty; reports use different result property names, so counts above are
read from their actual case/check arrays.

Independent source review also found two frontend fences to test before fixing:
inactive native cleanup must prevent scripted admission even through retained
Start/Resume handlers, and a held Inspect callback must not reopen managed read
access after its independent reader observer/context changes. The contract adds
a presentation-only admission callback and a separate reader context/allowed/
observer fence. Neither changes Rust authority or puts observer identity into
the generation execution key.

The frozen independent lens checker (`de0123dc`, adopted `5557301d`) actually
reproduced 2 passes/3 failures at clean unchanged `5557301dbf120ec924ab7845fa1e69d071fcc491`.
Mira, Sable and an independent reader lens change each allowed one managed
acquisition from the stale Inspect callback. Commit `2a06a569` captures/rechecks
reader context, eligibility and observer; the unchanged five cases then passed
at `2a06a569923996712c3f6235171b6563aa1e01bb` (0.38 seconds).

The independent admission packet (`9c66fb1a`, adopted `88780867`) actually
reproduced 4 passes/5 failures at clean unchanged `88780867106e1346f9c4e49f9808c21ee6aae35e`.
Three inactive cleanup states left generation controls enabled; retained Start
and Resume each dispatched despite the new block. The recovery and clear-state
controls passed. Commit `f3e78ec0` supplies a fresh both-controller presentation
guard at render and in retained handlers. The unchanged nine cases passed at
`f3e78ec0fcdf002057c08d1c826fbf4163e338cc` (0.51 seconds). Neither fix withdraws
Story Lab eligibility or changes Rust permissions. Both checkers are now wired
into full frontend verification; later formatting is whitespace only.

Full frontend `node verify-frontend.mjs` passed at clean unchanged
`504e7da3f65ce9961a7d52b7898b6691d5cfaef6`, 23:21:06.067–23:21:24.601 UTC,
including legacy56/native88/reader22/Main20, strict TypeScript and normal bundle
hook exclusion. This precedes the two independent fence fixes and new native UI
harness wiring, so it is not the final integrated cohort.

## Environment and remaining checks

Windows NT 10.0.26300 x64, PowerShell 7.6.5, installed Node 24.22.1,
TypeScript 7.0.2, esbuild 0.28.2 and React/react-dom 19.3.1. No dependency or model
download was performed for these checks. Only one heavy build/test/model process
is allocated at a time. Separate agent checkouts perform source-only work.

Native consumer WebView rendering, actual native comparison IPC journeys,
installed-model GUI execution, final full frontend/native compatibility checks,
normal build restoration and final-head security checks are not established by
the initial results above. Their results must be added after execution. Existing
OS dialogs are not automated or counted as tested. No desktop input, activation
or desktop capture is used; any future render evidence must come from the owned
hidden/unfocused WebView and every generated image must be inspected.

At clean unchanged `4e4c861995095df571e4b9d8743108647350d204`, initial offline
native Clippy stopped before compilation: cached `aho-corasick 1.1.5` archive
unavailable. Android Rust host test similarly stopped before compilation on
`block-buffer 0.10.4`. These exit101 attempts are unavailable checks, not test
failures or passes. Installed extracted registry source exists, but this does
not establish usable Cargo archive availability. No download was attempted.
The native fixture/journey work remains source-only pending integrated checks;
the missing journey import is an explicit intermediate integration dependency.

The journey module is now integrated (author packet `fa564141`/`2dfe8bb9`,
adopted `923bd99c`/`132ed8d7`). TypeScript passed at clean unchanged `29e1d31a`;
this did not execute the journey. Source review then corrected four nonexistent
native recovery command spellings to `evaluation_comparison_native` and separated
the fixture's active-consent flag from harness availability (`514b3794`). The
harness now waits for actual held callback entry before cancel/retirement.
These were source findings, not runtime reproductions. A later independent
review found that a secret canary's absence from History did not test Knowledge
filtering. Commit `f658c130` adds an actual Player-positive/NPC-negative Knowledge
check at the original `courier-01/left/before` cut, preserving the History and raw
evidence-refusal checks. That native assertion remains unexecuted.

Integrated full frontend verification passed at clean unchanged
`514b37946f15413043223f539de07f8ef8bedcf4` (21.776 seconds) and after the knowledge
oracle correction at `f658c13006c6d3c84b435bc6562f0d0ddbf3d036` (19.865 seconds).
The latter includes native-controller88, reader22, Main20, independent admission9
and lens5, unchanged scripted56, all other wired suites, strict TypeScript and
normal frontend hook exclusion. Both are actual-source mocked/headless checks;
the native journey is bundled/typechecked, not run. Rust formatting passed at
`514b3794`. Frontend formatting initially identified the older scripted journey's
version-narrowing layout; whitespace-only `edbe96c5` corrected it, and the full
Prettier check passed at clean unchanged `f658c130` (3.163 seconds).

## Reproduce the pending native cohort

After the exact locked Cargo packages are available locally, set these to
existing absolute directories/files. The launcher validates the approved model
and worker hashes and never downloads either asset. It derives a fresh isolated
workspace and model directory and uses the ordinary model importer; imported
model bytes are copied locally, not uploaded. Only the four original scenarios
are genuinely generated, with explicit paired batch1 then resume3.

```powershell
Set-Location apps/desktop
$env:LOCALLORE_D07_FULL_COMPARISON_ARTIFACT_ROOT = '<existing local artifact directory>'
$env:LOCALLORE_D07_FULL_COMPARISON_TARGET_DIR = '<existing external native target directory>'
$env:LOCALLORE_D07_NATIVE_MODEL_SOURCE = '<approved installed Qwen3-0.6B-Q8_0.gguf>'
$env:LOCALLORE_D04_WORKER_SOURCE = '<approved installed locallore-llama-worker.exe>'
node comparison-run-harness.mjs --native
```

The model SHA256 is `9465e63a22add5354d9bb4b99e90117043c7124007664907259bd16d043bb031`
(639446688 bytes); worker SHA256 is
`b5dd124e484c67c9dda5aebb2cdff1878ccefd0fba99aba4788e00a166f68434`.
The launcher keeps source/command/exit/output hashes and a bounded report,
semantic snapshots and up to eighteen application-owned WebView PNGs locally.
All generated images require separate individual inspection. No new image has
been generated or visually qualified by this consumer work yet.

The fixed execution/read consent and model-picker doubles are test plumbing,
not OS dialog acceptance. The 2100-second app / 2160-second launcher limits are
scheduling caps, not measured performance. Presentation polling can exhaust
after 300 seconds; only an observed uncertain original client may receive an
explicit read-only lookup, with each error boundary retained and accounted.
There is no automatic generation retry. Restart inventories can prove bytes
unchanged; independent asset-call counter instrumentation is unavailable and is
not claimed from elapsed time or an unchanged file tree.

Keep this slice unaccepted until native compilation/tests, actual native UI
execution, individual image review and normal native restoration are recorded.
The ordinary frontend is restored by `node verify-frontend.mjs`; an ordinary
native build must be performed afterward without `dev-harness`. The local
offline-cache blocker is not a reason to weaken a gate or reuse historical
PR #214 evidence as a pass for this frontend.

## Restored dependencies and actual native qualification

The owner explicitly authorized restoration of exact locked Rust packages.
`cargo fetch --locked --target x86_64-pc-windows-msvc --manifest-path
apps/desktop/src-tauri/Cargo.toml` used a task-isolated Cargo home: 49 existing
checksum-matching archives copied, 251 retained archives / 42461782 bytes, every
archive verified against the unchanged root lock. Lock SHA256:
`4fb7c498ca0ecc62c4ea1f65c63b370ab4336eb75133d08b3a71f5664156cf93`.
No dependency upgrade, global-cache mutation or model/worker download occurred.
All subsequent native commands used `--locked --offline`, jobs1, debug0,
incremental0, the same external target and the restored isolated Cargo home.

Strict native Clippy (`--all-targets --all-features -- -D warnings`) passed at
clean unchanged `d614ca73` in 347.894 seconds after the fresh-cache rebuild.

| Actual native UI cohort | Result and retained limitation |
|---|---|
| `native-ui-restored1`, clean unchanged `d614ca73` | Worker/frontend/native builds passed. Actual app exited1 after 157.210s; one wide idle PNG, individually inspected. Fixed 60s observation expired during reference/setup before confirmation. Report read state after disposal, so its null phase/error does not identify the earlier worker state. No generated-report proof was obtained. |
| `native-ui-restored2`, clean unchanged `b919c49f` | Added bounded transition history, pre-cleanup state, 240s pre-confirmation observation and close-before-consent-release failure cleanup. App exited1 after 270.032s; five PNGs individually inspected. Held/cancelled/denied and lost-ACK recovery passed before the helper mistook a preceding closed presentation for a new asynchronous admission's terminal result. The captured failure state was still the new start's cleanup preflight. |
| `native-ui-restored3`, clean unchanged `8f9423238e47182a50398d277624951fc9675ccf` | Corrected acknowledgement pairing; strict TypeScript passed first. Initial **243 checks / 14 PNGs**, restart **85 checks / 4 PNGs**, both app exits0, stdout24B each/stderr0, no timeout/overflow. Initial 1283.428s; restart78.460s. All eighteen PNGs individually inspected; no observed visible defect in the captured wide/narrow scroll sections. |

These are actual hidden, unfocused WebView2 execution, native IPC and approved
installed-model results. They are not desktop captures or OS dialog automation.
Consent, picker and lost-ACK doubles are explicitly synthetic. Live gameplay is
the synthetic in-memory Host; the isolated comparison's actual Rust histories,
reports and model recordings are durable. This is not another durable Play
restart or phone test.

The initial cohort exercised native App lane selection, ordinary verified model
import without ordinary model load, actual held/denied execution consent,
cancel/retirement before reservation, one lost start ACK and same-client lookup,
fresh paired batch1 then explicit resume3, completed read-only resume, independent
managed read consent, actual receipt/capture/output, Player/Mira/Sable Query2,
three actor raw-evidence refusals and native generic cleanup. The corrected
Knowledge oracle actually observed the Player-positive canary and its absence
from both NPC views at the same original before-cut. Inspections and lens changes
kept the native execution identity and live story unchanged.

Initial retained three accounted Transport records: one deliberate lost ACK and
two observed 300s presentation poll expirations, each reconciled through the
original client's explicit read-only lookup. No automatic start/resume occurred.
The bounded state history retained96 transitions and reports3 dropped; restart
retained25/no drops and zero errors. This finite observation history is not a
complete trace of every poll.

Cold native catalog/open/completed resume/read/close preserved **2072 files /
22671542 bytes**, independent inventory SHA256
`9d860a35ba88933f8847333871555d1b526be2f838ceb3f50432a9c523fe9361`.
The same digest covered completed resume and inspection in the initial process.
The UI cohort does not instrument an independent asset/reservation call counter;
no stronger zero-call claim is inferred from the inventory or elapsed time.

One-scene report copy: version3,12 outcomes,22 known real roles,1 physical setup,
10 expected scenario passes,4 fallbacks, SHA256
`02fb2a5cc1882998288456d557be40b0957e604d8489f0030c9b6c34e74385d5`.
Completed copy: 4 scenes,48 outcomes,78 known real roles,2 physical setups,
41 expected scenario passes,15 fallbacks, SHA256
`472c4df465d595962cb6604d524d1848a43c22defc82899e9c8247891dd7acee`.
All role counts were known. Phase counts are36 committed/12 failed; expected
scenario passes are a different measure. Left/right expected passes were17/24
and24/24. Failed-row diagnostics include Agency2, UnknownReference4 and one
without an error category; assertion labels can overlap. This is a small
controlled developer workload, not general model superiority or quality proof.
Both copies are retained before/after resume rather than relabelling an
overwritten partial report. Human-reviewed remains0 and quality-accepted false.

A concrete prose concern is preserved: `courier-01/right` mechanically delivers
the intended statement but narrates walking through a forest despite the quay
fixture. Read-only audit matched the actual request, prompt/schema/adapter and
recording hashes, with no established transport, role or truncation error.
The sanitized narrator evidence has no scene-location anchor. The model's cause
is unknown; the finite prose validator accepted this text. An empty automated
quality-flags list only means no fallback flag, not semantic approval. A local
eight-sample reading packet supports the separately requested human assessment;
no human result is invented or written into the immutable report.

GUI executable SHA256 during both processes:
`eaaf676a0ffe05aa6d737657822fa90fe25864544f4a7fb5dda7c582f67c0c6b`;
launcher `484e9ddf2056124f34f3fe680d74d4343f458f97f1858a24649eb50f28c3dcdb`.
The launcher checked executable identity after each app. A later test build
replaced the target executable; an attempted retention copy refused the
different hash, so the tested GUI binary itself is not claimed retained.
Individual eighteen-image review manifest SHA256:
`3ebcd09a926725aac6b22863039c042daecffd9fc6c3e9d8d1ebcb7d13393130`.
Native UA reports reduced Chrome/Edge155, DPR1,1280/620px; this is not an exact
installed WebView2 patch-version query. Rust1.93.1, Node24.22.1, Tauri2.12.5,
Wry0.57.0, Windows NT10.0.26300 x64, Intel i7-12700K; approved CPU4/context4096/
350+350-token/repair1 profile unchanged. Caps are not performance measurements.

At the same clean unchanged `8f942323`,
`cargo test --manifest-path apps/desktop/src-tauri/Cargo.toml --features dev-harness
--locked --offline --jobs 1 --target-dir <external-target> -- --test-threads=1`
passed **235 / 0 failed / 9 ignored**,940.43s test execution, plus two
harness-contract tests in0.01s. Total command983.308s including compilation.
Ignored tests remain the eight explicit installed-asset opt-ins and the Windows
symlink-privilege test; they are not silently counted as passing. This default
synthetic suite is separate from the actual approved-model UI cohort above.
Final normal frontend/native restoration and compatibility checks are recorded
after this section once executed. Broader D07 human-quality/whole-app resource,
OS dialog, network-blocked, full accessibility and physical-phone gates remain
open; this supporting consumer slice does not close the milestone.

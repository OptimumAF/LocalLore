# D07 synthetic deterministic runner prerequisite

Refs #29 D07.01/.02/.04/.06/.07, original #6 fixtures and #14 evaluation gates.
This is a **headless fake-provider regression lane**, not real-model quality,
desktop rendering, Android semantic parity or full D07 acceptance. It adds no
app IPC, model/SQL/file execution capability or alternate engine/memory pipeline.
All milestone criteria remain unchecked pending their full evidence and owner review.

## Frozen inputs and shared authority

`crates/locallore-eval` is a standalone Rust workspace with its own locked manifest.
Root `cargo test` will not execute it. The desktop workflow explicitly runs this
standalone crate's formatting, all-target tests and strict Clippy using only
built-in synthetic cases; real-model runs remain outside default CI. Its explicit
local command is below.

`fixtures/eval/reference-v1.json` is a strict serde version1 suite. Every expected
value and retrieval target is declared **before execution**, rather than copied
from actual results. It references the original `fixtures/lantern_quay.json` by ID
and SHA256; no second world/seed or rule implementation is introduced. The seed
hash `08794dfdb60eb2fcd33eeb5746dd19e3809259d44d72b61f3fcc9ce69c08c648`
is SHA256 of compact UTF-8 `serde_json::Value` serialization with sorted object
keys, arrays preserved, no whitespace/newline. It is a seed-input checksum, not
a canonical-state fingerprint or authenticated publisher signature.

Suite shape: version, synthetic=true, seed ID/hash and scenarios. Each scenario
declares a unique ID, shared typed Intent steps/repeat/expected phase/error/revision
delta, fixed scripted provider output when free text is selected, independent
assertions, lifecycle probes and an optional explicit unsupported reason.
Assertions cover exact projection JSON-pointer values/absence, actual compiler
record kind/content/source, observer-forbidden literal text, and narrow prohibited
narration strings. Unknown fields, versions, invalid bounds and mismatched seed
bytes are rejected before any scenario runs. Types are in the new crate's lib.rs;
there is no arbitrary scenario-file import command.

Controlled-choice steps use the actual durable `locallore_workspace::open` Host,
its existing fake inference mode, native Host admission/prepare/commit and the
sole Store owner. The scripted free-text gift configures an explicitly fake
InferenceProvider and traverses **Host → production Play → production context
compiler → typed Engine validation → durable commit**. The provider returns the
predeclared director command and fixed narration, using the actual supplied
narrator event-ID schema. It captures prompt/schema SHA256s, not invented model
measurements. It parses the actual director's frozen `Context data: ` JSON envelope
to assert compiler version, original input hash, and predeclared bounded target
kind/text/source presence. It never records the raw full prompt or computes a
second generation eligibility filter. The report includes the selected target
declarations and their presence flags. The fake profile's zero-filled artifact
hashes are explicit synthetic placeholders, not model/worker provenance.
No local-runtime crate, worker/model/native GUI or network service
is linked/invoked by this lane.

Canonical/observer/retrieval assertions read the actual Store-resumed validated
Engine. Context checks call the same accepted `context_compiler::compile`, with
the requested actor and real lineage/observer eligibility; they do not inject an
alternate retrieval result into generation. Replay uses recorded outcomes and
`Engine::replay`, without calling an LLM. Fixed literal state expectations remain
independent assertions even though the runner uses shared replay for equality.

## Finite built-in coverage

| Scenario | Independent expectation / limitation |
|---|---|
| spent-potion | One potion transfers to Mira; reuse is rejected Inventory; gifting does not heal; unwitnessed Sable context excludes it; durable replay/resume/exact retry and foreign scope checks |
| abilities-and-resources | Unlearned blink rejects Ability without mutation; steady spends2 energy once; next use rejects Resource; no blink granted |
| borrowed-key | Loan cannot be gifted to Mira or consumed; player owner and return-to Oren remain |
| unseen-secret | Actual Mira/Sable compiler packages exclude the original Tideglass canary; Mira's false seed belief stays a belief |
| claims-are-not-truth | Original literal statement/speaker recorded; no power grant; explicit lexical query retrieves Event1 as statement and does not create canonical truth for Mira |
| asymmetric-relationship | Only Mira→player obligation increments; reverse obligation/trust and original trust remain exact |
| old-promise-after-distractors | Seed return-key remains unresolved/retrieved with seed provenance after32 accepted Wait turns; time132. **Short synthetic history**, not1,000-event stress or model usefulness |
| scripted-production-gift | Original finite English action is retained through real production Play/compiler; scripted narration commits; exact retry after provider unload/resume does not invoke provider |
| lifecycle-isolation | Queued cancel does not change canon; a competing Host wins once and the loser is stale; distinct story remains untouched; recorded replay/resume equality |
| same-name-collision | **Unsupported here:** original two Oren names are not simultaneously eligible/present in this built-in Host path. Original separate compiler collision tests are not relabelled as runner execution |
| portable-archive | **Unsupported:** D03 inspection is not a D08 playable archive |
| summary-maintenance | **Unsupported:** production summary/index maintenance plus disk-full/migration fault qualification is outside this frozen slice |

The original M02 10,000-transition property suite, existing1,000-event compiler
stress, real models, baseline/A-B comparisons, semantic prose/voice/enjoyment,
Android/emulator/physical phone, app rendering and network-denied observation are
not rerun or counted as passes. `quality_accepted` is always false, model/runtime/
hardware measurements are null when unknown, and unsupported lanes are listed.
Literal prohibited-text checks do not claim general semantic hallucination detection.

## Commands and API

Use Rust1.93.1 and an owned output/temp/target directory. This build needs only
already-provisioned Cargo dependencies; commands are locked/offline. No weights,
SDK/ADB, browser, native app or hosted service is required. In a new PowerShell:

```powershell
$taskRoot = 'D:\LocalLore evaluation'
New-Item -ItemType Directory -Path "$taskRoot\temp" -Force | Out-Null
$env:TEMP = "$taskRoot\temp"
$env:TMP = $env:TEMP
$env:CARGO_PROFILE_DEV_DEBUG = '0'
$env:CARGO_PROFILE_TEST_DEBUG = '0'
$env:CARGO_INCREMENTAL = '0'
$taskManifest = 'crates/locallore-eval/Cargo.toml'
$taskTarget = "$taskRoot\target"
cargo +1.93.1 test --manifest-path $taskManifest --locked --offline --target-dir $taskTarget -- --nocapture
cargo +1.93.1 clippy --manifest-path $taskManifest --all-targets --locked --offline --target-dir $taskTarget -- -D warnings
cargo +1.93.1 fmt --manifest-path $taskManifest -- --check
cargo +1.93.1 run --manifest-path $taskManifest --locked --offline --target-dir $taskTarget -- run "$taskRoot\run-01" --max-cases 1
cargo +1.93.1 run --manifest-path $taskManifest --locked --offline --target-dir $taskTarget -- resume "$taskRoot\run-01"
cargo +1.93.1 run --manifest-path $taskManifest --locked --offline --target-dir $taskTarget -- case "$taskRoot\gift-rerun" scripted-production-gift
```

Stop on command failure. `run` and `case` require a new directory under an existing
parent; `resume` requires its original run. `--case ID` can also select/bind the
same case on run/resume. Only built-in IDs execute. Exit0 means no failed executed
case (not that unsupported/incomplete cases passed); exit1 reports case failures,
exit2 setup/integrity/budget/usage errors. Always inspect completed/unsupported
fields, not just the exit code. `--max-cases` pauses after the stated number of
new scenarios; it does not interrupt a turn or count existing checkpoints twice.

Native Rust integration API:
`run_builtin(directory, resume, selected_case, &Cancellation, max_scenarios)`.
Cancellation is cooperative **at scenario boundaries**. A GUI adapter can cancel
the token; this CLI does not install a Ctrl-C handler or change OS signal settings.
A killed in-flight case is abandoned and resume creates a fresh case attempt,
never reopens its partially written DB. This is evaluation restart, not app-story
restoration. The API takes no seed, DB path, arbitrary scenario, provider, model,
SQL or file import from a renderer.

## Checkpoints, output and limits

Each case gets a newly created `case-NN-attempt-NN/synthetic.sqlite`. Completed
case envelopes are flushed then renamed to fixed create-new `case-NN.json` names;
their version/binding/result SHA256 and ID are checked on resume. An OS-backed
exclusive file lock prevents competing runner owners and releases on process
death. Completed results are authoritative checkpoints; report.json/report.html
are replaceable derived views and can be incomplete after a crash. The runner
never deletes a supplied run directory or its failed attempts.

`run.json` and reports bind exact raw scenario bytes, canonicalized seed checksum,
Host schema, domain/storage/prompt/policy versions, selected case IDs, and compiled
public shared/eval source/migration/manifest/lock byte fingerprints. build.rs walks
only fixed source directories at build time; report names are relative, with no
host paths. Changed/future/malformed checkpoints refuse to resume. Checksums check
**internal consistency**, not origin/authenticity: someone can recompute a forged
report. Do not execute its contents, treat it as canon, or accept an untrusted
report as independent evidence without matching reviewed inputs/execution.

Bounds: suite128KiB/32scenarios;256 expanded steps total/48 per case; at most48
repeats per step;32 declared assertions/5 probes per case; provider capture128
requests; completed-case JSON64KiB; each JSON/HTML report2MiB;32 attempt slots per
case. Source input files are bounded at4MiB each. Engine/Host's own limits still
apply. Bounds fail closed; they are not memory/latency qualification. HTML escapes
all JSON text, contains no script/remote assets/active links, and uses a restrictive
default-src-none CSP. It is an inert local report, not a new app/web server.

Reports contain original synthetic intents/narration, exact assertions, failures,
known source-turn/seed anchors, canonical/replay fingerprints, fake request prompt/
schema hashes and explicit unmeasured fields. They contain no real player stories.
Model-quality scoring or an agent/human approval is never manufactured. Outputs
belong in task-local storage or the crate's gitignored artifacts/ directory, not
the public fixture tree. The Story Lab results GUI and D05/D06 navigation remain
future coordinator integration; this module does not imply a new UI exists.

## Deliberate regression evidence

The focused test runs the actual compiler after32 distractors, then a **cfg(test)
only fault seam** removes Commitment records before evaluating the declared target.
It must produce a retrieval failure for `old-obligation-target-0`, source
`seed:lantern-quay-v1`, expected present=true versus actual=false. A fresh restored
run must pass. This checks that the evaluator detects a known retrieval omission;
it does not claim a production compiler defect was introduced/fixed or that a
real model used the retrieved fact correctly. Exact executions and earlier runner/
fixture mistakes are preserved in [D07_EVAL_EVIDENCE_2026-10-22.md](D07_EVAL_EVIDENCE_2026-10-22.md).

A separate cfg(test)-only seam removes commitment records from the parsed observed
director envelope, leaving the actual direct compiler call unchanged. The declared
`gift-context-target-0` must still pass while
`original-gift-0-prompt-targets` fails on the original turn, then a fresh restored
case must pass. This simulates downstream dropped forwarding at the capture
assertion boundary; it is not a production Play modification or an observed
compiler defect. Prompt format/version drift also fails the envelope assertion.

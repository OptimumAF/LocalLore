# Whole evidence words in versioned narration

Refs #9 **M05.03**, supporting #14 **M10.04** and #29 **D07.04**.
B34 is implemented and locally verified, pending review and owner acceptance.
Full task checkboxes remain unchecked; no release acceptance.
This packet builds on open, unmerged PR #297 at
`0eded1650c9c2f9b9569bf2f95069a99913deb94`.

## Behavior and compatibility

The original evidence check admitted unsupported capitalized `Mir` through
`mira`, and `Pot` through `potion`. Sensitive words had the same problem:
`kingfisher` could authorize `king`, `coinsmith` could authorize `coins`, and
one `secret-*` word could authorize another. Trimming punctuation before checking
also lost digit, underscore, hyphen and internal-apostrophe continuations.

Fresh narration now compares complete words segmented from original text before
Unicode lowercasing. Digits, underscores, hyphens, internal apostrophes and
non-whitespace non-ASCII scalars remain part of a word. Bounded enclosing quotes
and one terminal ASCII/curly possessive do not make a different name. The
capitalization gate checks the complete word, including uppercase continuations
after a lowercase apostrophe prefix. Sensitive phrases require complete evidence
word sequences; a secret-prefixed word requires that exact evidence word.
The English pronoun `I` is exempt only at the original sentence opening in this
general gate; scene-specific first-person restrictions still apply.

The preceding complete-visible-name span and hidden-ID rules remain in force.
This does not grant character knowledge or promote claims/beliefs into truth.
Canonical effects still come exclusively from validated engine events. Rejected
narration falls back to the existing accepted mechanical summary, or fails if
that summary violates the existing presentation exclusions. Cancellation,
staleness, repair and atomic append rules remain unchanged.

The shared validator also rebuilds recorded history, so tightening its old policy
in place would reject genuine saves. New generation and fresh public commits
require these current policy IDs:

| Construction | New policy | Preserved historical policy |
|---|---|---|
| Ordinary/memory/literal | `grounded-prose-v2.5-whole-evidence-words-v1` | `grounded-prose-v2.1`, `grounded-prose-v2.2` |
| Presentation | `grounded-prose-v2.6-story-presentation-whole-evidence-words-v1` | `grounded-prose-v2.3-story-presentation-v1` |
| Scene frame | `grounded-prose-v2.7-scene-frame-whole-evidence-words-v1` | `grounded-prose-v2.4-scene-frame-v1` |

Recognized old policies retain their old validation only in private history
reconstruction; an arbitrary record policy cannot select that mode on a fresh
commit. Exact recorded retry returns the original result before fresh validation.
The old public scene V1 constant retains its literal value; a separate V2
constant selects the new policy. Receipt shape, prompt/schema bytes, model,
runtime and dependency versions do not change.

Eval's frozen v3/v4 arm descriptor APIs keep their old tuples. Explicit current
descriptors serve new writers; historical readers require an exact complete old
or new descriptor family and preserve that family in reports. Mixed or drifted
tuples fail. V2 attributes the stored policy without inventing a wire field.
Closed rows reconstruct the exact historical receipt and full accepted history;
active producers retain the fresh commit gate. Old captures are inspectable,
not rerunnable under a mismatched current source binding. Public fresh scene
capture validation requires the current policy.

The desktop transport decoder also recognizes only complete exact old or strict
descriptor families. Report/selected arrays cannot mix families; each row must
match its declared physical arm and diagnostics must match their summary family.
Existing read-only, source-binding and execution-unavailable guards remain.
Current-generation native journey assertions follow the new policy IDs; old
synthetic fixtures retain their old labels. No visual App change is included.

## Original and historical evidence

The independent initial public-API suite actually ran against unchanged old
production: **4 passed / 10 assertion failures / 1 intentionally ignored capture**.
A separate capture on the same unchanged old production generated **18 genuine accepted nonfallback
receipts**, nine construction families each with `Mir` and `Pot`: ordinary,
memory, literal, presentation, literal presentation, scene memory, scene literal,
presented scene memory and presented scene literal. The committed original
synthetic fixture is 528546 bytes, SHA256
`58b56d456220ef07b16721f31d0b2fddc125bc67e54fcfd366a9ff685e354b07`.
Seed and receipt JSON remain original strings; canonical-after JSON retains its
original byte array. No
record was fabricated by changing a new policy ID. Its manual producer is
explicitly ignored and create-only.

Regression tests check exact restore/replay/retry/canonical preservation without
inference, refusal of genuine old authority at fresh public commit/stage gates,
strict-policy tampering, all construction families, Unicode prefixes and
continuations, bounded possessives, cancellation and a real Domain2 prefix.
The Domain2 fixture first commits an actual author correction. Materializing an
original-world seed alone creates Domain1. B33's former wording conflating those
operations was corrected in its ticket/PR #298 body without rewriting its old
source, dated report or evidence.

An old-only producer at `3e5727cedaadc0b509f4719712de77de7eb5de29`
(unchanged production base plus one manual test) also produced three actual
one-scene scripted comparisons: v2, v3 and v4, each with committed rows.
The fixed private tree has **288 files / 2733292 bytes**; inventory SHA256
`015462d35f525459529a074c913f47ce6f11afb255d91f68ab26940b3987edb1`.
Before any new reader ran, all original bytes were verified into a 394054-byte
ZIP, SHA256
`5b54e6aa899e570d8c5c4e87567a02bb9a7471b5c339eeb745d8176aad8c4c8f`.
The historical-reader test is explicitly ignored by default and was separately
invoked with the fixed genuine tree; missing input is an error, never a skip.
These are synthetic fake-provider compatibility artifacts, not model results.

## Verification and preserved failures

Windows host, Rust/Cargo 1.93.1, locked/offline dependencies; physical D: source,
process TEMP/TMP/TMPDIR on D:, existing D: caches, two build jobs and debug
information disabled. Each fixed check uses a finite 1800-second Windows job
owner and bounded 262144-byte output capture, source/head before/after bindings,
actual child identity join, and a retained terminal cleanup/capture result.
Owner intervals are host check costs, not gameplay/model latency.

| Check | Executed source | Actual result | Owner interval |
|---|---|---|---:|
| Complete Core, host/all-targets | `a1ea3cba` | **575 pass**, 5 intentional ignores, 70 binary summaries |181347ms|
| Storage/workspace/Android Rust host, all-targets | `a1ea3cba` | **519 pass**, 7 intentional ignores, 82 binary summaries |464842ms|
| Eval library and two unit binaries | `1c1f8e97` | Library **140 pass**, quality-review **13 pass**, main 0 cases. Containing whole-suite job later stopped; not a whole-command pass |1448661ms containing owner|
| All 31 default-feature Eval integration targets, closed groups and serial follow-ups | `1897ce94` | **122 pass / 12 intentional ignores**, no duplicates | See cohort intervals below |
| Eval documentation tests | `1897ce94` | Command passes; 0 cases defined |2245ms|
| Explicit genuine old v2/v3/v4 reader | `1c1f8e97` | **1 pass**,3 filtered; no old-tree mutation |10377ms|
| Workspace formatting | `a1ea3cba` | Pass |3303ms|
| Separate Eval formatting | `1c1f8e97` | Pass |1338ms|
| Core/storage/workspace/Android Clippy, all-targets | `a1ea3cba` | Pass, warnings denied |60660ms|
| Separate default-feature Eval Clippy, all-targets | `1c1f8e97` | Pass, warnings denied |16011ms|
| Public offline Android build/JVM/lint/product audit | `a1ea3cba` | **324 JVM pass / 38 suites**, no skipped/failed/error; lint 0 errors / 1 warning; product APK audit passed |427912ms|

The focused 23-case narration suite is included in the 575 Core passes. Its
manual capture remains intentionally ignored. The final Eval-only source change
from `a1ea3cba` is the two factory scopes described below; Core, compatibility,
Android sources and their tests are byte-identical. The final executable source is `1623151dbef2530e0beb19ae489355402956b781`.
Independent readback confirms 361 Core/Eval/Cargo files unchanged by the later
frontend/Tauri integration. Subsequent reporting commits change documentation
only; no complete rerun is attributed to those heads.

Actual commands, all with `cargo +1.93.1` and `--locked --offline`:

```text
test -p locallore --features host --all-targets
test -p locallore-storage -p locallore-workspace -p locallore-android --features locallore/host --all-targets
test --manifest-path crates/locallore-eval/Cargo.toml
test --manifest-path crates/locallore-eval/Cargo.toml --test grounding_policy_compatibility -- --ignored --exact genuine_old_eval_committed_rows_remain_readable_without_relabel_or_mutation --nocapture
clippy -p locallore -p locallore-storage -p locallore-workspace -p locallore-android --features locallore/host --all-targets -- -D warnings
clippy --manifest-path crates/locallore-eval/Cargo.toml --all-targets -- -D warnings
```

Formatting uses `cargo +1.93.1 fmt --all -- --check` and the separate Eval
manifest equivalent. Android uses `python -I -S -B scripts/check.py android
--offline`: build both Debug APKs, run JVM tests and debug lint, then the existing
product APK checker. It is the normal public default build, not the newer
isolated archive profile or a complete paired-APK audit. Installed JDK 21,
compile/target SDK 36, existing D: Gradle/Android caches and installed SDK were
used in place; no download/settings/dependency change. All 81 actionable Gradle
tasks executed; other headings include no-source, skipped and up-to-date tasks.
The existing instrumentation compiler warning about
`AtomicReference<Boolean?>` remains separate from the lint warning.

Product APK: 27772460 bytes, SHA256
`5c1f121cada09383dcc8ea3373d496c04ae7696fa20e70382767aab1130ba378`.
Instrumentation APK: 2188835 bytes, SHA256
`40be63e5cb67f2dfdbc8a7cdc9509774962d9ef827ab3f5deee5542cb9ecd33f`.
The product audit found only its declared signature receiver permission and
four ARM64/x86_64 libraries with 16384-byte ELF load alignment. Compilation and
package inspection do not establish either ABI's execution or Android privacy.

## Desktop consumer verification

An independent consumer audit found the remaining desktop exact transport
tables still recognized only old 2.2/2.4 policies. The independent author added
22 public decoder cases in four existing checker scripts, then corrected four
TypeScript consumers. No dependency, package-lock, verifier registration,
visual design, native authority or model choice changed.

The first actual baseline full frontend run at tests-only `dbbcebe7` failed at
step 31 before reaching any new decoder case: 12/13 diagnostic panel checks
passed, but an old sibling-exclusion oracle expected zero Timeline panels.
Commit `b7b1a3a7`, already in the production base, intentionally enabled thin
Domain2 timeline browsing. Independent source review confirmed the existing
positive browser contract, coherent native-derived context and no fetch on
mount. The correction changes only this stale test: require one panel with the
real shared controller and exact session/scope/revision/view/observer/persistence
context, retain all other exclusions and disabled controls, and require zero
host calls across both renders. Production App/Timeline behavior is unchanged.
The original failure remains failed, with its five compiled products privately
copied and byte-verified before a later build could replace them.

After that correction, tests-only `602aff52` reaches actual decoder **RED**:
the existing selected2 checker reports 105 pass / 1 assertion failure, accepting the
legacy family and rejecting the new strict-family positive with
`SelectedEvaluationWire`. Public verifier: 37 completed steps; owner 13297 ms / child 1.
This is separate from the preceding stale-oracle failure.

Corrected frontend executable `eb8c50a467bde8a5f5699c3e03ae1e5ea5ba1708`
passes the full unchanged `node verify-frontend.mjs --bounded`: **77 steps**,
including **22/22 new named decoder cases**, strict TypeScript/request/schema
checks and exclusion of development hooks from the normal frontend.
Owner 33745 ms / child 0, known cleanup/capture and 2305 unchanged source pins.
The public policy finishes with 39,101,535 output bytes and 719,119 product bytes,
below unchanged 64 MiB / 16 MiB limits. Its named external evidence 86,552,738 bytes
plus designated output/products/reserves remains under 640 MiB. Each cohort has
a new create-only admission; failed caps and outputs are never reused/reset.

The existing supporting 31-case Domain2 timeline contract also passes separately
on that source, owner 832 ms / child 0. It uses actual controllers/components with
disclosed inert hooks, JSX/static HTML and a synthetic gateway, not a browser,
native IPC, Rust, pixels or physical interaction. It is not part of the 77-step
public verifier; it directly checks the contract behind the oracle correction.

Frontend checks ran in the separate physical-D verification checkout with
installed Node 23.10.0. Existing D: dependencies were reused through a new ignored
junction; package-lock bytes match SHA256
`eb20ed7d77cef8796e7784c0d4b37470b9efff9f3e5b15115afafecdd325e0ee`.
Existing esbuild 0.28.2 / TypeScript 7.0.2 / Prettier 3.9.10 / React 19.3.1 match the pins;
no install, download, cache copy or global setting changed. Formatting touched
only the nine owned frontend/test files. Independent final readback finds all
284 non-Rust frontend files byte-identical to the later integration source;
the six-file Tauri change is checked separately below. No Rust verification is
attributed to this older-Core test-only checkout.

The public driver's console budget remains 4 MiB. Fresh RED/GREEN owners capture
that console into distinct create-only raw files and bind bytes/hash after
known close; outer worker streams retain 262144-byte limits and the same finite
Windows job. GREEN raw console 356840 bytes, SHA256
`a9ab0be26547b7a1dff403a60e5056bdbb697336ba9e0ba5a41a88cfba6fb0c3`.
The inner policy remains cooperative and explicitly reports no process-tree
containment of its own; the separate outer Windows job supplies ownership and
known cleanup. Neither is an operating-system storage quota. Original baseline
142075-byte stream and RED/GREEN files retain their distinct attribution.

Failures are retained separately: initial capture path-spelling assertion;
the original ten regression failures; an initial `o'Potion` escape; the test's
incorrect authored-seed Domain2 assumption; missing then overbroad grammatical
`I` handling; three stale current-policy storage expectations; Clippy's
nonminimal boolean expression; and the first genuine old Eval read returning
`ReceiptReplay`. That last failure exposed a historical row assessment still
calling fresh `commit_prepared`, despite source-only review finding no blocker.
No failure is reclassified as a pass or hidden by weakening an assertion.

Independent review then found lowercase visible-name prefixes masking a hidden
display name across a combining-mark or emdash continuation. Two new original
tests actually failed while the previous 21 passed. The new policy's complete
visible-label spans now use the same conservative word boundaries as its
evidence checks; historical spans retain their original behavior.

The first default Eval library run finished 138 pass / 1 fail. Its cancellation test
returned `Interrupted`: three tests shared a process-global provider-polled
flag, allowing one provider to wake another test's cancellation watcher before
its own provider ran. The test-only pending provider now carries an execution-
local signal. All three original assertions and 5/10/15-second waits remain;
a new deterministic two-provider case verifies cross-signal isolation.
Production cancellation behavior and deadlines do not change.

Default-feature Eval Clippy additionally exposed two explicit `drop(factory)`
calls already present at the production base, where the default factory has no
resource-bearing variant. A moved factory now leaves a lexical scope before
final inspection, preserving native/test resource release and error unwinding
without a lint suppression. An intermediate Eval rerun was deliberately
interrupted for this fix; its actual owner status is `owner_failed`, with known
cleanup/capture and unchanged sources. It is not a completed pass or a verified
`stop_requested` result. The stop request's exclusive publication may have
raced the reader; the caught exception was not retained, so that cause remains
an inference. Original partial logs and the operator observation are preserved.
A duplicate compatibility dispatch also refused its existing output folder
before any child; the subsequent invocation used a distinct create-only folder.

## Complete default Eval coverage

The original default whole-suite command was deliberately stopped after about
24 minutes to split its remaining work into bounded owners. Its library completed
140 cases, main defined zero, and quality-review completed 13. Its terminal status
is `stop_requested`, worker exit 1, with known cleanup and capture. It is not a
successful whole-suite command. Its six completed integration summaries are
excluded from the selected integration totals.

The actual Cargo target inventory identifies 31 integration targets. Successful
groups 0, 1 and 2 closed in 862465, 164242 and 591645 ms. Group 3 failed after
127906 ms: `comparison_desktop_review` reported 5 pass / 3 fail / 1 ignore when
Windows refused a file still held by a parallel shared-source reader (code 33).
The fixtures and failed logs remain. These older tests document serial execution.
Six documented serial targets then passed with one test thread in 1134687 ms;
the five remaining targets passed in 254837 ms. No lock, assertion or test case
was removed. The successful selection prefers the serial six and excludes four
successful parallel duplicates and all failed-group counts.

The resulting bijection covers all 31 targets: **122 pass / 12 intentional
ignores**, zero failures or filtered cases. Together with the 153 unit cases,
this establishes **275 normal default Eval passes / 12 ignores** across multiple
closed commands. Documentation tests pass with zero cases. The separately
invoked genuine historical reader adds one pass; it is not counted again in the
275. Optional model/native feature suites are not implied by default coverage.

Each integration cohort invokes the same locked/offline manifest with explicit
`--test <target>` arguments from the inventory. Original groups use four test
threads; the documented six-target follow-up sets process-local
`RUST_TEST_THREADS=1` (the argv does not add the equivalent `--test-threads=1`). No test-name
filter or skip is used. Actual commands and selected cases are retained with the
target inventory and coverage receipt.

## Native preparation and recorded index compatibility

The Tauri selected-evaluation index now has a private Fresh/Recorded distinction.
New preparation accepts only exact current descriptor families. Reading an
existing index can recognize an exact historical or current family. Resume still
requires full equality with newly prepared metadata, source binding and protocol
before consent or an execution grant. Old-readable does not mean old-executable.
The public scene proof accepts fresh current descriptors; historical constants
and genuine fixtures retain their original values.

At final executable source `1623151d`, these scoped native host checks pass:

| Closed cohort / filter | Cases | Owner interval |
|---|---:|---:|
| `native-policy-v2` / `prepared_policy_review_tests` | 6 | 19454 ms |
| `native-scene-proof-v1` / `comparison_reader_harness::scene_proof_tests` | 1 | 21789 ms |
| `native-literal-v1` / `evaluation::selected::tests::literal_selected_review` | 5 | 166510 ms |
| `native-scene-v1` / `evaluation::selected::tests::scene_v4_review_tests` | 8 | 494677 ms |
| `native-comparison-v1` / `evaluation::comparison_run::review_tests` | 11 | 485939 ms |
| `native-clippy-v1`, all targets, warnings denied | Command pass | 58943 ms |
| `fmt-v3`, workspace formatting | Command pass | 3307 ms |

Commands use `cargo +1.93.1 test --locked --offline -p
locallore-desktop-spike --features dev-harness --bin locallore-desktop-spike --
<filter> --test-threads=1`. Clippy uses that package and feature with
`--all-targets -- -D warnings`. The 31 distinct cases pass without failures or
ignores. The binary contains 351 cases; the other 320 are not claimed as run.
The scene proof uses the actual scripted protocol-v4 two-arm producer (literal
and relevant; 12 rows for one scene), actual proof reader,
reacquisition and unchanged-inventory assertion, without a model or app launch.

The first `native-policy-v1` attempt failed to compile after 128287 ms because a
new test helper placed an array-map expression directly inside `json!`. No test
ran. The correction precomputes the same arms before the macro; production guard
bodies are unchanged. Its failed compiler capture is preserved. Four already
verified frontend distribution files (709422 bytes) were copied locally for
Tauri compilation; this is not another frontend build or native app execution.

## Independent readback

Independent agents owned original adversarial fixtures, scene/Eval compatibility
and read-only integration review in separate worktrees. The coordinator owned
shared contracts and integration. Source review alone initially missed the old
Eval assessor; its actual historical-reader failure drove the correction.
Final reviews join each closed owner to its actual worker, command, source/head
before and after, captured streams and cleanup, rather than treating a wrapper's
exit as the child result. Original reader metadata refusals and their narrow
corrections are retained. The installed Cargo alias was read only through its
exact pinned installed rustup target; project-path reparse refusals remain.

| Private receipt | Bytes | SHA256 |
|---|---:|---|
| `review-eval-final-v1/coverage-review-v1.json` | 210982 | `2dfc69ca7997b216103754a2151b6c4791fdd2b2b7b17df3cb2e515f3a2dbbbd` |
| `review-frontend-v2/closed-review-v2.json` | 176453 | `0db969751886924e1a6bd6add0b53e9e26709dee7abb29c5aeadcba491a10962` |
| `review-native-final-v1/closed-review-v1.json` | 79307 | `28d8e011c649a7ab5b001e46abc470b9df574a4fa48ae60bd5fe3f6545b13ab1` |

These receipts bind the reviewed evidence; independent agent review is not owner
acceptance or a real-device/model result.

## Storage and limits

Private controls and targets remain under
`D:/Dev/Experiments/LocalLore/2026-10-30-narrator-grounding-v1`;
selected recovery uses the matching `D:/Dev/Recovery/LocalLore` packet.
The declared new packet budget is 8 GiB, with generation monitored to stop before
7 GiB. The initial 1–4 GiB forecast was too low. Before native compilation the
additional 0.5–1.5 GiB forecast was posted; actual native growth was about 1.67 GB.
Named roots measured about 6.55 GB before final recovery. The cap was not raised.
A separate conservative D: temporary-root observation initially measured
497292991 bytes. After all tests, the second observation finds 1856603095 bytes
across 1226 newly created immediate roots, 116516 files, 37 refused reparse aliases
and no disappearing paths. Both include concurrent other work. Neither is a peak
measurement nor a complete ownership attribution. The named-root admission does
not cover all shared TEMP/cache growth and is not a whole-machine storage quota;
an aggregate peak-storage pass is not claimed. Final preservation records carry
later observed named-root sizes and their exact scope.
The failed parallel-lock fixtures were copied create-only (3036 files,
28715408 bytes) from their exact recorded time window; originals remain.
Original failures, frozen source worktrees,
targets and old captures remain. No full source bundle, weights, private saves,
keys, existing global caches or guest images are copied or deleted.

This is an English-first finite lexical safeguard, not semantic entailment,
complete Unicode normalization or a quality guarantee. Conservative non-ASCII
punctuation can cause extra fallback. Hashes bind history but do not authenticate
malicious save authorship. No model is run and no enjoyment/fallback-rate
improvement is measured. Android build/JVM evidence does not qualify emulator,
physical phone, ARM64, real inference, privacy or release readiness. This packet
uses no ADB/SDK device command, emulator boot, model copy or shared-ledger change.
Other emulators, system settings and shared services remain untouched. No merge.

The current `main` advanced independently to `eab64f7625de48b8d18e139226223fb4c6f11791`
while this work was tested. This focused branch remains based on the exact open
PR #297 head; these results do not qualify integration with that newer main.
No other branch is rewritten. M05.03, supporting M10.04 and D07.04 remain
`in_review`; M01.01/M01.02 and M10.05 device gates remain blocked/unverified.
The next runnable host packet is typed, observer-safe authored-world location
labels and scene-frame support: `SceneFrameV1` currently refuses `initial_world`,
so a typed source and versioned recipe are prerequisites, not a relaxed guard.

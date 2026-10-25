# LLGuidance host oracle independent review — 2026-10-25

Refs #9 (M05.01/M05.05), #5 (M01.05). Root claim6400493037;
independent reviewer `/root/model_picker_review`, claim6400628071.
This report supplements the [pinned API research](LLGUIDANCE_ORACLE_RESEARCH_2026-10-25.md).

## Review scope and source findings

Reviewed the actual real-engine exporter, independent Python checker, launcher,
their authored tests and protocol in the authors' separate worktrees. No
implementation file was edited by this reviewer. Native compiler execution and
its eventual result are the coordinator's responsibility.

Two concrete launcher counterexamples were reported before execution credit:

- A completed-zero checker returning only `{"native":true,"status":"passed"}`
  could mark the launcher passed without any corpus linkage, controls or sample
  results. The original mocked launcher test used that minimal object. A strict
  report shape and full corpus/control/index/hash correspondence are required;
  process completion alone cannot establish grammar acceptance.
- Default argparse error handling could echo unknown private arguments/paths
  to stderr before sanitized launcher handling. A closed argument-error path
  and a no-echo hostile-argument regression are required.

The revised source adds complete closed report validation against the exported
corpus (controls, exact indexes/counts/hashes/outcomes and mismatch agreement),
duplicate-key refusal, and closed argparse handling inside the sanitized path.
Those revisions address the counterexamples. The final32-test targeted run
includes closed-report/corpus-linkage, no-echo argument and cleanup-failure
regressions and passed. No remaining false-pass instance was found in the
reviewed final source.

## Package and graph boundary

Independently read the coordinator-provisioned code wheel and its extracted
files with standard-library ZIP/hash operations, without importing LLGuidance.
Observed exact wheel2,789,946B/SHA256
`1d1cd1c8618d1a13605d3e057c978651e551c8c469b481ee4041f1d6c436002d`;
20 members totaling7,596,764 uncompressed bytes. All20 extracted files matched
their wheel bytes and the exact file set; runtime top level contained only
the retained wheel and `lib`. WHEEL/METADATA confirmed CP39 ABI3 WindowsAMD64,
Python>=3.9, MIT and no mandatory distribution dependencies. The license was
retained. This is package integrity inspection, not a reviewer native import
or an observed ABI-load success.

The launcher verifies the pinned archive before extraction and rechecks the
runtime before dispatch. Metadata/path/version checks inside NativeBackend
complement that check; direct checker use alone does not authenticate wheel
bytes. Isolated `-I -S -B` child invocation and a verified explicit module root
avoid global installation or arbitrary backend selection.

The exporter adds an explicitly host-only example registration without adding
LLGuidance to the Cargo dependency graph. Keeping its compiler outside the
engine graph avoids upstream `serde_json/preserve_order` feature unification
changing the production bytes under test. The raw captured `schema_json`
string is passed through unchanged rather than sorted or reconstructed.

## Matcher and corpus boundary

The checker validates bounded exact corpus shapes before native construction.
It performs native grammar validation beyond packaging, uses a new matcher per
sample, checks error state and finite safe stop reasons around every mask and
consume, and refuses an illegal byte before consuming it. Completion requires
full acceptance/EOS agreement, EOS consumption, an error-free state and stopped
matcher. This specifically addresses upstream's EOS-only fallback and stopped
EOS shortcut. No forced-token helper, tokenizer file or HF API is used.

The byte tokenizer's reserved0xff marker cannot occur in valid UTF8 input;
ordinary byte mappings, vocabulary262 and EOS261 are checked. The corpus keeps
malformed/incomplete negatives as exact strings. Neither input whitespace nor
object-property order is normalized. Grammar representation exclusions remain
separate from the engine's existing BTreeSet normalization and canonical
validation authority.

The exporter captures actual production Structured Director requests with a
provider refusal and verifies unchanged canon, revision and receipts. A real
engine synthetic gift precedes its ordinary post-gift capture. Independent
bitmasks cover every eligible nonempty set of size<=4 for n1..6, rather than
deriving positives from the produced enum. The three engine refusal controls
and the fixed native compiler/acceptance controls have distinct purposes.

The generic fake backend tests are meaningful for orchestration and failure
boundaries; they cannot certify native grammar compilation. A passing native
run would certify only the admitted corpus/compiler byte path, not every JSON
representation, the real Gemma tokenizer, SDK native error cause, generation,
phone performance or full M05/M01 acceptance.

## Initial native result and reduction

Independently replayed the closed original synthetic corpus/result in
`C:/Users/Avery/LocalLore-llg-oracle-host-20261025`. All three owned stages
completed with known cleanup: build16,875ms/exit0, export1,234ms/exit0,
check1,656ms/exit1. The native result was `mismatch`, not a passed oracle.
All five controls were true. Of199 samples,113 positives and85 negatives
matched expectations; one escaped-literal positive failed.

The exact retained corpus35,143B SHA256 is
`1207cb0ca36f16e78c74cb50770390008ab0a6fe0fcc1de68eab5a2b7dc495f8`;
oracle32,539B SHA256
`c5ab7010e9c907c95efabace35568dca68f873c78cab2bb2c65e6eaba9252dce`.
Its ordinary425-byte post-gift schema and all crowd-audience examples matched.
The escaped sample is103 UTF8 bytes; its first disallowed byte is offset65,
the backslash introducing the closing escaped quote after Mira. Unicode snow
and newline occur later. Decoding the original synthetic candidate and schema
const yields exactly equal text, including every codepoint. No schema/sample
rewriting or expected-positive relabeling is warranted.

An independently replayed first reduction corpus reproduced the failure in a
standalone string CONST (offset13/48), alongside nested original65/103. Plain,
quote-only, one/two quotes, one/two backslashes, newline, Unicode and
quote-pair-with-prefix examples passed. Its coordinator-owned check completed
453ms/exit1/cleanup true. Thus the nested engine schema is unnecessary for this
byte-path counterexample. These observations do not isolate compiler versus
mask implementation, identify the decisive tail interaction, or establish a
cause for the earlier Android INTERNAL13. The pinned compiler's
[JSON-quote options](https://github.com/guidance-ai/llguidance/blob/v1.3.0/parser/src/json/compiler.rs#L687-L694)
explicitly include these escape forms, unlike its documented deliberate
property-order and outer-whitespace restrictions.

## Evidence disposition

The final source rerun in
`C:/Users/Avery/LocalLore-llg-oracle-final-20261025` reproduced byte-identical
corpus and oracle files: build15,438ms/exit0, export1,156ms/exit0,
check1,578ms/exit1, all completed/cleanup true. Its run explicitly reports
`mismatch`, rather than crediting an oracle pass. All six recorded source
hashes independently matched current coordinator files, including launcher
`9f464e6f2c18bdfeaae77ccdcb34f3e7c4222d571ccae0a5e5812c14c9c95c57`.

The final fixed-source reduction in
`C:/Users/Avery/LocalLore-llg-oracle-reduction-final-20261025` has16 cases and40
samples:14 expected positives and24 negatives align; the same two full-literal
positives fail. Five added tail-interaction controls passed and did not narrow
the cause to one particular escape. It completed407ms/exit1/cleanup true with
all five controls true. Corpus7,534B SHA256
`5385c27ddb9eeb5525dcbf2faa06e05df9fa9ce83d82c43c61691713da757e97`;
oracle8,532B SHA256
`757625b444d7c928deb916450fb585aabca49ca7544ed765d94f4d7d580d01ef`.
Every schema/sample index, hash, byte length and expected/actual category in
both final results was independently replayed; no linkage discrepancy was
found. The fixed reduction mode uses a distinct hand-authored fixture source
label, not a substituted engine-export claim or arbitrary CLI corpus path.

Final code is `10fa7206e0a7bb0852531c56e5251ff2ec5a0857`.
Against the research base, no existing engine implementation, Android input,
root Cargo manifest or lockfile changed; the core manifest only registers the
host-only example. The final native run's source hashes match current code.

Independently replayed the selected evidence index
`C:/Users/Avery/LocalLore-llg-oracle-evidence-index-20261025.json`:
4,374B/SHA256
`f0fe2f97d3172c2436b5a0d2416f8851034e48a29c6754a41ff55cb281da55dc`.
It lists exactly22 unique whitelisted files totaling211,298 bytes; every
size/hash matched. This is an explicit selected-evidence index, not a seal of
all files under those directories or of build artifacts/runtime. No target
tree, cache, SDK, model or disk traversal was performed.

The retained Rust stdout sums to49 suites,359 passed/0 failed/4 historical
ignores, including8 exporter tests. Its process metadata is completed0,
cleanup true,85,188ms. Clippy completed0/cleanup true in7,688ms; the coordinator
also reports fmt passed. The preserved earlier Python run has851 successful
tests; final Python has853 successful/0 failures/errors/skips, completed0/
cleanup true68,421ms. Final targeted output reports32 passed in0.340s,
completed0/cleanup true593ms. These are coordinator-owned actual checks
independently read and hashed by the reviewer, not additional reviewer runs.

No reviewer build, package/native import, SDK/device/model/cache/image/disk
action occurred. Retained synthetic result inspection and package-integrity
hashing do not execute the compiler. This is a reproducible compatibility
counterexample and bounded diagnostic tool, not a production fix. The next
source/runtime investigation must preserve the full failing literal and its
expected positive status; dropping it or weakening literal/intent binding
would conceal the issue. Passing ordinary byte samples do not identify the
previous SDK INTERNAL13 cause or qualify the full on-device Dialogue path.

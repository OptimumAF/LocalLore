# Isolated LLGuidance development oracle

Refs #9 (M05.01/M05.05), #5 (M01.05). This host tool checks actual engine
Dialogue schemas against LLGuidance1.3.0. It is never linked into the app or
engine. It does not load a model, tokenizer file, SDK or device.

## Boundary and reproducibility

The Rust example uses the original Cargo graph/lock and `host` feature. A
provider captures only the serialized schema from an actual guarded
`play::execute` request, then returns `Error::Provider`; canonical bytes,
revision and receipts must remain unchanged. The ordinary case first accepts
the original synthetic potion gift through director/narrator play. No prompt
or generation text is exported. No production schema or generation cap changes
are part of this oracle.

LLGuidance's Rust dependency enables `serde_json/preserve_order`. Linking it
into this exporter could change the serialization under examination. The
compiler therefore runs in a separately provisioned Python process against
the frozen `schema_json` string. JSON is neither rebuilt nor sorted there.
See the [pinned API/license research](LLGUIDANCE_ORACLE_RESEARCH_2026-10-25.md).

The admitted artifact is the MIT-licensed WindowsAMD64 CPython>=3.9 ABI3 wheel
`llguidance-1.3.0-cp39-abi3-win_amd64.whl`, 2,789,946 bytes, SHA256
`1d1cd1c8618d1a13605d3e057c978651e551c8c469b481ee4041f1d6c436002d`.
The [official package metadata](https://pypi.org/pypi/llguidance/1.3.0/json)
and [source license](https://github.com/guidance-ai/llguidance/blob/v1.3.0/LICENSE)
were checked before provisioning. It has no mandatory Python distribution
dependencies. No model or tokenizer download is needed.

Acquire that exact code wheel explicitly, then run from the repository:

```powershell
python -I -S -B scripts/llguidance_oracle.py provision --wheel C:/private/wheels/llguidance-1.3.0-cp39-abi3-win_amd64.whl --runtime C:/private/new-llg-runtime
python -I -S -B scripts/llguidance_oracle.py run --runtime C:/private/new-llg-runtime --output C:/private/new-llg-evidence
python -I -S -B scripts/llguidance_oracle.py reduce --runtime C:/private/new-llg-runtime --output C:/private/new-escape-evidence
```

Parent directories must already exist; runtime and evidence directories must
be new and outside this checkout. The launcher never installs globally or
downloads anything. Other platforms/wheels are not admitted by this launcher.
It preserves the wheel and its license, rejects traversal/links, validates
metadata and hashes, and rechecks every extracted file against the pinned
wheel before a run. Failure remnants stay available for inspection; rerun
into a new evidence directory. Provisioning alone does not import native code.

The run builds with installed Rust1.93.1 using `--frozen --offline`, exports
the corpus, then starts Python with `-I -S -B` and an explicit verified module
root. Each trusted worker waits on stdin before child launch or native work;
the existing process owner assigns a Windows job before releasing the barrier
(process group on POSIX). Build deadline180s, export/check deadline60s each,
combined stdout/stderr cap262,144 bytes per stage. Cleanup must succeed before
accepting any stage. Ctrl-C uses that same cleanup. No arbitrary command is
accepted. A timeout/cleanup failure is a failed run, never a semantic rejection.

## Corpus v1

Top-level keys are exactly `version:1`,
`scope:"locallore_llguidance_oracle_v1"`, `cases`, `refusals`.
Each case has exactly `id`, `schema_json`, `positives`, `negatives`; each sample
has exactly `id`, `json`, both strings. Refusals have exactly `id`, `error`,
`provider_calls`, `canon_unchanged`. Duplicate keys, extra keys, wrong types
(including booleans in numeric positions), invalid UTF8 and bounds failures
are refused before the native backend is constructed.

The checker caps input at1MiB, cases16, total samples256, schema/sample strings
16,384 UTF8 bytes each. The launcher accepts at most262,144 bytes from its fixed
exporter process. Schema/sample IDs are fixture labels, never public report
content. No arbitrary prompts, files or tokenizer/model paths are accepted.

Eight original cases:

- `ordinary-post-gift`: real guarded gift, then exact425-byte Dialogue schema.
- `nearby-1` through `nearby-6`: independently enumerate every nonempty eligible
  audience set of size<=4 (1/3/7/15/30/56 sets).
- `escaped-dialogue`: Unicode, quote, backslash and newline literal.

There are114 positive and85 negative samples. Negatives exercise empty,
duplicate, unsorted, self, remote, dead, foreign or overfull audiences where
applicable, wrong command/text, malformed JSON and incomplete prefixes.
These are **grammar representation** negatives: they do not assert new engine
refusals. The engine still owns its existing normalization and validation.
Provider-free controls require no listeners→`ClarificationRequired`,128
listeners→`TooLarge`, context512→`TooLarge`, all zero provider calls and
unchanged canon.

## Native acceptance

The checker validates the schema through the native compiler, rather than
only packaging a grammar string. A separate unsupported `uniqueItems` control
must compile-refuse; a valid control must compile and accept its sample.
Ordinary corpus compilation errors are failures, not expected negatives.

The reserved `LLTokenizer("byte")` constructor uses no files/network. Verify
its262-token vocabulary, EOS261 and ordinary byte mapping; byte255 is a test
special marker and cannot appear in valid UTF8 input. No fast-forward methods
are used. Each candidate UTF8 byte must be allowed by the current little-endian
token mask **before** consumption. Check sticky native error state before and
after masks/consumption: the library can expose an EOS-only mask on error.

A complete sample must be accepting with EOS allowed, consume allowed EOS,
remain error-free and stop successfully. An incomplete prefix is rejected;
an illegal next byte is rejected without consuming it. Native faults, invalid
stop states and control failures abort the run with closed reasons. A
semantic acceptance mismatch is distinct from compiler/runtime failure.

Default LLGuidance object-property order and outer-whitespace restrictions
apply. This is a test of these exact serialized representations, not general
JSON Schema equivalence. A passing byte oracle does not qualify the model's
real tokenizer, LiteRT/JNI path, token budget, response quality, cancellation,
or a physical phone; it cannot identify the prior INTERNAL13 by itself.

## Evidence and checks

The create-only output holds `corpus.json` (original synthetic schemas/samples),
`oracle.json` (closed numeric/enumerated/hash metadata) and `run.json` (stage
status, cleanup, timing, byte counts, source/corpus/report hashes). Build
artifacts stay in its `target` directory. Reports never include prompts,
samples, schema strings, arbitrary exception messages or input IDs. Public
verification reports summarize these original fixtures; no private diagnostic
or model contents belong in the repository.

```powershell
python -B -m unittest scripts.tests.test_llguidance_launcher scripts.tests.test_llguidance_oracle -v
cargo +1.93.1 test --frozen --offline -p locallore --features host --all-targets
cargo +1.93.1 clippy --frozen --offline -p locallore --features host --all-targets -- -D warnings
```

Pure Python tests use a fake backend and synthetic non-executable code wheels;
they do not establish native compilation. The dated verification report must
separately record the actual pinned native run and any mismatches.

## Original escape reductions

`reduce` checks the separate original
`fixtures/llguidance_escape_reductions.json`, labels its source
`reduction_fixture`, and skips Cargo/export stages. Its15 minimal string-const
controls plus the exact nested escaped engine case distinguish simpler
quote/backslash/newline/Unicode forms and tail interactions. It has16 cases,
16 positive and24 negative samples, no engine refusal records. These minimal
schemas are explicitly hand-authored compiler controls; they do not replace
the actual engine-exported schemas or establish new engine behavior.

Both modes validate the entire closed checker report against the exact corpus:
version/scope/native marker, all five sanity controls, every case/sample index,
hash, byte count, outcome and aggregate count must agree. Missing/substituted
reports cannot qualify a run. `passed` exits0, a valid observed `mismatch`
exits1, local/provisioning failures exit2. A worker/compiler failure is never
credited as a rejected negative. A bounded rejected report may be retained
privately as `rejected-report.json`; it is not accepted evidence.

The original escaped positive remains a positive even if the pinned native
compiler rejects it. A red oracle is useful counterexample evidence, not
permission to remove fixtures, loosen literal speech, or mark real inference
as verified.

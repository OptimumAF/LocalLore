# Literal masking and public API source research — 2026-10-25

Refs #9 (M05.01/M05.05), #5 (M01.05). Root claim6400786067;
independent reviewer `/root/model_picker_review`, claim6400795379.
Base `090a8694120ee37dcfb48bfd48f9f0dd67ce3377`.
Pinned LLGuidance tag1.3.0 resolves to
`29e33a219f77be1cc37d8394630440f448d19945`.

The previous [actual oracle review](LLGUIDANCE_ORACLE_REVIEW_2026-10-25.md)
records a reproducible original synthetic escaped-literal positive rejected
by the byte mask: nested sample offset65/103 and standalone CONST13/48.
Fourteen simpler final reduction positives pass. This follow-up identifies a
specific upstream quoting-tail omission consistent with subsequent controlled
host observations. It does not establish a cause of the Android
wrapper-declared INTERNAL13. The coordinator owns native comparisons and any
correction; this reviewer reads source and closed original-synthetic reports.

## Public calls test different paths

The [Python binding](https://github.com/guidance-ai/llguidance/blob/v1.3.0/python_ext/src/llmatcher.rs#L401-L474)
exposes `compute_bitmask`, `validate_tokens`, `consume_token` and
`consume_tokens`. Its validation wrapper returns a count, not a boolean:
underlying errors can yield1 when the first supplied token is EOS, otherwise0.
Its single-token EOS consume can return true on an already stopped matcher.
Neither shortcut authenticates successful parsing. Check error state before
and after each call, including validation and EOS; preserve resource/error
failures separately from semantic rejection. Compilation/constructor checks
from the prior review still apply.

At the Rust matcher layer, [consumption](https://github.com/guidance-ai/llguidance/blob/v1.3.0/parser/src/matcher.rs#L71-L86)
applies each token, requires zero backtracking, then calls `check_stop` after
the sequence. Single-token consumption delegates to that sequence method.
In contrast, [validation](https://github.com/guidance-ai/llguidance/blob/v1.3.0/parser/src/matcher.rs#L179-L181)
delegates to raw validation; it does not commit the supplied sequence.
Successful consumption of an incomplete prefix is not full acceptance.

Raw validation explicitly skips forced-byte tokenization and may ignore
multi-token limits. See the
[TokenParser contract](https://github.com/guidance-ai/llguidance/blob/v1.3.0/parser/src/tokenparser.rs#L417-L441).
The [Earley implementation](https://github.com/guidance-ai/llguidance/blob/v1.3.0/parser/src/earley/parser.rs#L1074-L1136)
runs speculatively, compares pending bytes, otherwise pushes bytes through a
recognizer, and treats EOS specially. A full-length validation count is a
different observation from every generation-mask bit allowing those tokens.
Do not promote it to a generation or token-budget qualification.

Use separately constructed matchers for masked, validation and direct-consume
paths. The Python `deep_copy` implementation uses `inner.clone`, while
[TokenParser distinguishes ordinary clone from deep clone](https://github.com/guidance-ai/llguidance/blob/v1.3.0/parser/src/tokenparser.rs#L131-L135):
ordinary cloning shares lexer state. A fresh tokenizer is an additional
explicit control if factory-shared behavior is being investigated; a fresh
matcher alone is not a promise that every immutable/shared optimization object
has been recreated. The [factory](https://github.com/guidance-ai/llguidance/blob/v1.3.0/parser/src/factory.rs#L12-L20)
stores an Arc-backed bias computer and [clones it for callers](https://github.com/guidance-ai/llguidance/blob/v1.3.0/parser/src/factory.rs#L108-L110).
These are source properties, not evidence that shared state caused the failure.

## Default capabilities do not disable internal forcing

The prior checker comment that default inference capabilities disable implicit
forcing was too broad. No public forced-token helper was called, and capability
booleans are false, but internal mask forcing remains possible.

[Mask computation](https://github.com/guidance-ai/llguidance/blob/v1.3.0/parser/src/tokenparser.rs#L463-L487)
can turn forced bytes into a singleton next-token mask.
`can_force_bytes` depends on the grammar's `no_forcing` setting and canonical
tokenizer status, not `InferenceCapabilities.ff_tokens`. The builtin byte
tokenizer is canonical. The [forcing gate](https://github.com/guidance-ai/llguidance/blob/v1.3.0/parser/src/tokenparser.rs#L636-L655)
and [retokenization/chopping path](https://github.com/guidance-ai/llguidance/blob/v1.3.0/parser/src/tokenparser.rs#L674-L753)
therefore remain relevant. Token application clears the acceptance and forced
token caches; this is not proof those caches are faulty.

This distinction makes a masked/nonmasked comparison useful. It does not
establish which internal stage caused the first disallowed byte, nor justify
ignoring that mask in production.

## Admit no_forcing through documented Lark syntax

The public diagnostic option is
[`LLGuidanceOptions.no_forcing`](https://github.com/guidance-ai/llguidance/blob/v1.3.0/parser/src/api.rs#L34-L56).
The source describes it as testing-oriented and warns about speed/quality.
`GrammarWithLexer` does not expose flattened options: those fields are
[commented out](https://github.com/guidance-ai/llguidance/blob/v1.3.0/parser/src/api.rs#L73-L87).
Do not assume adding an unknown JSON top-level field or
`x-guidance.no_forcing` enables this option.

The [documented Lark declaration](https://github.com/guidance-ai/llguidance/blob/v1.3.0/docs/syntax.md#L319-L326)
and [inline JSON-schema form](https://github.com/guidance-ai/llguidance/blob/v1.3.0/docs/syntax.md#L28-L31)
support a diagnostic wrapper:

```text
%llguidance {"no_forcing":true}
start: %json <the exact raw schema_json object>
```

Keep an otherwise identical `%llguidance {}` wrapper as a control, alongside
the original JSON grammar path. The
[Lark compiler](https://github.com/guidance-ai/llguidance/blob/v1.3.0/parser/src/lark/compiler.rs#L637-L645)
parses the option and passes it to the builder. The
[builder](https://github.com/guidance-ai/llguidance/blob/v1.3.0/parser/src/grammar_builder.rs#L215-L238)
inherits any enabled `no_forcing` option into the lexer, including nested
grammars. Record original schema hash, wrapper kind and result independently.
This controls a diagnostic mechanism; it is not an approved app setting or
schema relaxation.

## String const and exact-byte controls

A JSON string CONST becomes
[`RegexAst::Literal`](https://github.com/guidance-ai/llguidance/blob/v1.3.0/parser/src/json/schema.rs#L805-L809).
The compiler checks literal character length and then wraps it with
[JSON quoting](https://github.com/guidance-ai/llguidance/blob/v1.3.0/parser/src/json/compiler.rs#L728-L806).
Its [quote options](https://github.com/guidance-ai/llguidance/blob/v1.3.0/parser/src/json/compiler.rs#L687-L694)
explicitly permit the usual quote, backslash, newline and Unicode escape
forms. There is no documented short-literal-only policy in that path.
The additional dependency inspection below identifies a concrete omission
inside that quoting transformation.

The public `grammar_from_regex` method packages an exact regex via
[the binding](https://github.com/guidance-ai/llguidance/blob/v1.3.0/python_ext/src/llmatcher.rs#L385-L388)
and [regex-to-Lark path](https://github.com/guidance-ai/llguidance/blob/v1.3.0/parser/src/api.rs#L363-L367).
A fixed control may match the already serialized original JSON bytes, with
Rust-regex metacharacters escaped. Raw JSON is not itself a literal regex.
Require native compilation, original-byte acceptance and changed-byte
rejection; label this as an exact-byte control, not the production schema or
all equivalent JSON encodings. No regex/schema substitution earns a production
pass.

## Concrete upstream tail omission and observed boundary

LLGuidance1.3.0's [parser dependency](https://github.com/guidance-ai/llguidance/blob/v1.3.0/parser/Cargo.toml#L10-L14)
pins `derivre=0.3.8`. The official derivre tag resolves to commit
`c68f60791d191a05131796771f38c2e904417074`.
Its [ByteConcat maximum](https://github.com/guidance-ai/derivre/blob/v0.3.8/src/ast.rs#L23-L25)
is31 bytes. [Literal construction](https://github.com/guidance-ai/derivre/blob/v0.3.8/src/simplify.rs#L642-L668)
splits longer raw UTF8 strings into31-byte tail blocks, leaving a shorter
leading ByteConcat prefix.

In derivre's [JSON-quote mapper](https://github.com/guidance-ai/derivre/blob/v0.3.8/src/regexbuilder.rs#L514-L542),
when a ByteConcat prefix contains a byte needing quotation, the branch builds
quoted expressions for those prefix bytes and returns their concatenation at
line536. It does not append the mapped tail `args[0]`. The neighboring branches
preserve the tail, either by returning the original expression or rebuilding
with `args[0]`. This is a specific source-level loss of language content when
the omitted tail is nonempty, not a documented JSON representation policy.

The omission predicts the observed examples. A42-raw-byte full literal splits
into an11-byte prefix and31-byte tail. Quoting the prefix containing the first
quote discards the rest; its serialized prefix ends where the observed
standalone input first fails at13. The reduced32-raw-byte literal starts with
a quote: its one-byte prefix survives and31-byte tail is lost, predicting the
observed disallowed byte at3. Literals<=31 bytes have no nonempty tail to lose.
Long literals whose applicable prefix contains no quoted byte need not fail.

Independently read coordinator reports, without native execution:

- `LocalLore-literal-probe-fixed-20261025/probe.json` records default JSON,
  equivalent Lark-default and Lark-no-forcing all rejecting the original at13/48
  and reduced sample at3/38. Raw validation and direct consumption also reject;
  exact serialized-output regex accepts with wrong-byte negatives rejected.
  Its process metadata reports completed0/cleanup true437ms. Disabling forcing
  therefore did not repair these actual cases.
- `LocalLore-literal-threshold-20261025/probe.json` has16 rows for the original
  synthetic two-quotes-plus-ASCII-tail family. Literal byte lengths27..31 pass;
 32..42 reject at the offsets predicted by the split-prefix omission. The
  disallowed next input is met with a singleton closing-JSON-quote mask.
  SHA256 `a8b2a60e594e1ef6b0238933573d3492aab1448f88c51acee576bd3a3a43c705`.

The source omission plus the matching boundary/control observations support
this narrow upstream compatibility finding. They do not trace a private SDK
error to that code or prove every wheel build feature/native integration.
The ordinary unquoted short question does not exercise the same condition.

An important next negative is the complete JSON encoding of the incorrectly
retained short prefix. Test whether the old compiler accepts that wrong text;
the issue may admit truncated content as well as reject the intended literal.
Any correction must accept the full original and reject truncated/wrong text.
Do not patch acceptance expectations to match the broken language.

Adding a pattern alongside the same CONST cannot restore content lost by the
CONST branch. A literal string pattern also goes through JSON quoting and is
not automatically a bypass. The demonstrated diagnostic bypass is a regex
over complete serialized output. A separately reviewed narrow runtime adapter
would need exact supported-shape guards, JSON/regex escaping, complete audience
coverage, byte bounds and negative equivalence tests while preserving the
engine's original full-literal/intent validation. No production change,
dependency fork, new compiler build or generic schema lowering is authorized
by this source report.

## Comparison and minimization invariants

- Preserve the complete original positive, schema, dependency pin and prior
  failed evidence. Never relabel a masked rejection as expected negative.
- Give each API/options combination a fresh matcher. Whole-sequence raw
  validation may include exactly one terminal EOS, with full count and clean
  error state; do not put EOS before unvalidated trailing bytes.
- For direct consumption, separately require full acceptance and clean EOS
  behavior. For masked generation, every byte and EOS must first be allowed.
  Report those results separately even when they disagree.
- Reduce original synthetic Unicode strings at character boundaries, retaining
  schema-const/candidate semantic equality. Bound candidate count, length,
  native calls and total owner deadline. A deterministic reduction is not
  necessarily globally minimal; state its actual stopping criterion.
- Preserve malformed/incomplete and wrong-literal controls. Unexpected native
  faults, resource limits or cleanup uncertainty abort qualification rather
  than becoming representation rejection or a useful reducing candidate.
- Output only closed metadata, offsets, counts and hashes. No native error
  text or model/private payload is needed. Disagreement localizes a host path;
  it does not prove SDK/Gemma compatibility or explain prior INTERNAL13.

This report used public HTTP source reads and static local source review only.
No native package import, build, dependency download, SDK/ADB/AVD/model,
tokenizer-file, cache, image or disk operation was performed by this reviewer.
Root retains implementation, actual bounded comparisons and fix decisions;
full M05/M01 and physical-device gates remain open.

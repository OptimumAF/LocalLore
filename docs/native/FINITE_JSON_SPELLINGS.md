# Bounded equivalent JSON string spellings

Refs #9 (M05.01/M05.05), #5 (M01.05 supporting). This refines the finite
representation in `FiniteSchemaRegex.kt`; the original Rust schema, intent,
mechanics and commit validation remain authoritative. It changes no command,
event, history, prompt-policy or storage schema and raises no profile budget.

The prior codec admitted one compact Gson serialization per finite value. The
selected SP vocabulary control observes no raw ASCII-space pieces. Equivalent
JSON string spelling is therefore useful without changing the player's speech:
`"Where is it?"` and `"Where\u0020is\u0020it?"` decode to the same string.
JSON permits character escapes and paired UTF-16 escapes for supplementary
characters; isolated surrogate units are not accepted by this implementation.
See [RFC8259 sections7–8](https://www.rfc-editor.org/rfc/rfc8259#section-7).

The codec retains every previously admitted canonical spelling. For each decoded
space or non-ASCII Unicode scalar inside a JSON string, it adds the exact JSON
Unicode escape spelling as an alternative. A supplementary scalar uses its
complete two-unit UTF-16 pair in one alternative; raw and escaped surrogate
halves cannot be mixed. Hex letters allow either case. ASCII operation letters,
punctuation, quotes, backslashes and controls keep their original exact spelling.
Property names and nested finite literal strings use the same safe renderer.

This widens representation, not the decoded finite value set. In particular:

- A literal backslash-u sequence remains literal data. `"\\u0020"` does not
  acquire the meaning of `"\u0020"`, and no layer decodes the value twice.
- Structural whitespace, reordered object members, extra/missing members,
  changed text, invalid escape syntax and malformed scalar pairs gain no path.
- Audience choices retain every permitted original subset. No actor, operation
  or profile name selects an easier grammar or substitutes expected output.
- Enum and sibling-constraint checks still use the original canonical decoded
  identity before rendering. Equivalent source spellings cannot evade duplicate
  members or type/item/length constraints.

The output is a sequence of bounded scalar alternatives, not an enumerated
cross-product of full strings. Each complete alternative is charged before
append. Existing32768-byte input/output,512-node and depth12 limits remain.
Unsupported or over-budget input returns null through the existing selector;
there is no truncated grammar, raised generation budget or permissive parser.
Default SDK forcing behavior is unchanged. Explicit `no_forcing` exists only
in separately labeled host controls, using the pinned public Lark interface.

Verification separates these boundaries:

1. Strict original JVM positives/negatives, Unicode/escape identity and budget
   checks; actual Kotlin export binds the production patterns.
2. Original byte-tokenizer matching preserves every original candidate. Added
   equivalent spellings are labeled separately and retain source correspondence.
3. Authenticated raw-piece controls distinguish accepted/rejected candidates,
   unencodable originals and matcher failures. Their synthetic encoder is not
   an SP/SDK-equivalent callback, and cannot certify the Android result.
4. Actual Rust integration tests cross proposal parsing, intent and Engine
   validation/commit/replay. Changed speech, unauthorized effects and remote
   observers still fail without canonical mutation.
5. A fresh separately admitted SDK/emulator sequence is required for the real
   scene and restart. Unknown inference ownership prohibits dependent reads or
   retry on that target, regardless of passing host controls.

Java Pattern's recursive matcher is not the native pressure oracle. The maximum
space-alternative test checks the complete32761-byte pattern, compilation and
exact next-input refusal, with representative64-space JVM matches. A separate
create-only optional test export feeds the actual native boundary control. No
JVM stack or application budget is raised to manufacture a passing boundary.

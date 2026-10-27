# Initial-world schema portability

M09.02, with supporting M10.02/M10.03. Bounded correction in review; owner
acceptance and full task checklists remain unchanged. This follow-up depends
on unmerged PR #225 and preserves its native authoring boundary.

## Problem and correction

The original author schema contains two `uniqueItems:true` predicates, for
character and world-fact `known_by` arrays. Rust sends that schema through the
existing structured author request. Open text and variable-length arrays make
the finite-regex codec decline it, so the SDK receives public JSON Schema.
Pinned LLGuidance1.3.0 does not implement `uniqueItems` under its strict defaults.

The correction replaces only those two predicates with array-valued enum
choices: all64 nonempty unique permutations of references0..3 for character
visibility, and all65 choices including empty for fact visibility. Original
type/items/min/max constraints remain. Rust still checks actual actor existence,
self knowledge, route reachability, world bounds and complete initial origin.
No compiler leniency, ignored keyword, null schema, mechanical grant, new repair
or generation-budget change is introduced.

Order matters in the original/edited proposal provenance and origin hash, even
though materialized knowledge is a set. Every previously accepted typed array
ordering remains representable; restricting output to sorted subsets would
silently narrow that domain. The request remains `initial-world-v1`,1024 output
tokens,8192 output bytes and120 seconds. Its compact schema is3456 bytes; the
bundled source is8117 bytes. No dependency, model, SDK or runtime pin changes.

Primary sources: the [implemented vocabulary and constant-array compiler](https://raw.githubusercontent.com/guidance-ai/llguidance/v1.3.0/parser/src/json/schema.rs),
[strict keyword check](https://raw.githubusercontent.com/guidance-ai/llguidance/v1.3.0/parser/src/json/shared_context.rs),
and [pinned LiteRT constrained-decoding build](https://raw.githubusercontent.com/google-ai-edge/LiteRT-LM/bda624851d74be34d4e1f7fac1fc4155939539c7/runtime/components/constrained_decoding/BUILD).

## Actual checks

The unchanged4869-byte bundled schema, SHA256
`8f0438f091039118e180f1a3189ea5a958f2f730e8a97848fde2d48835895421`,
actually compile-refuses in an owned isolated native process:334ms, return2,
`case_compile`, known cleanup and0 stderr. All five native controls pass.
No model or Android SDK runs in that probe.

The old local oracle runtime is absent at the inspected historical C: paths.
The existing exact MIT-licensed LLGuidance1.3.0 code wheel is restored after
fresh [official metadata](https://pypi.org/pypi/llguidance/1.3.0/json) and
[license](https://raw.githubusercontent.com/guidance-ai/llguidance/v1.3.0/LICENSE)
checks:2789946 bytes, SHA256
`1d1cd1c8618d1a13605d3e057c978651e551c8c469b481ee4041f1d6c436002d`.
The existing launcher verifies every wheel/extracted file before native import.
This restores an isolated developer tool, without a global install, app
dependency or model download. Its provisioning/RED evidence is separately
preserved with zero missing/mismatched originals, copies or ZIP members.

Executed code `aa535d94` passes6 new integration tests,3 exporter tests and12
existing author-world adversaries,21 total, with0 failures/ignored. Focused
Clippy, formatting and diff checks pass. The bounded owner returns0 in24584ms
with known cleanup/capture,0 stderr and2000 unchanged historical tracked inputs;
879 compiled inputs include the two new Rust sources. A prior actual attempt
passes5/6 integration tests and fails a test oracle comparing derived prose
containing intentionally changed content-hash IDs. The corrected assertion
compares the explicit world/character propositions and logical actor-name
knowledge sets, while still requiring distinct origin/seed hashes and exactly
retained ordered provenance. That failed attempt remains preserved; no
production validation is changed to accommodate it.

The exporter captures the exact schema from a production author request and
emits3 cases/162 samples:132 positives and30 negatives. The full-schema case
uses original Ashglass/Copper proposals. Separate grammar-only cases exercise
all64/65 permutations; they grant no cross-field engine eligibility. Rust
tests independently retain actual-actor/self-knowledge/native-origin guards.

The actual native compiler and byte-mask oracle passes all162 samples and five
controls in598ms, return0, known cleanup and0 stderr. The original exported
corpus is28588 bytes, SHA256
`93dc10649de09ec828f425696f65d24d248bb2f5321aed60d4c573b71e516682`.
Exact production schema SHA256:
`b47513d1be6fb9ef77561325530193c3c329f7c06ae657ea87e1b3c24ede2914`.
The byte tokenizer loads no model or tokenizer file. Mask acceptance checks
include EOS/sticky native error state, rather than only wrapping schema text.

## Reproduction and remaining gates

With Rust1.93.1 and cached dependencies:

```text
cargo test --locked --offline -p locallore --all-features --test author_schema_portability
cargo test --locked --offline -p locallore --all-features --example initial_world_schema_cases
cargo test --locked --offline -p locallore --all-features --test m09_initial_world_adversaries
cargo run --locked --offline -p locallore --all-features --example initial_world_schema_cases
cargo clippy --locked --offline -p locallore --all-features --test author_schema_portability --example initial_world_schema_cases -- -D warnings
```

The exporter writes only bounded synthetic corpus JSON to stdout. Feed its
exact bytes to the existing `benchmarks/llguidance_oracle.py --corpus <file>
--module-root <verified-runtime-lib>` under an owned worker after
`scripts.llguidance_oracle.verify_runtime` checks the isolated runtime. Keep
the corpus/schema strings unchanged. The production Cargo graph does not link
LLGuidance or gain `serde_json/preserve_order` from this development oracle.

No Android APK for this corrected879-input source has run yet. The877-input
native10/original8/creation19/broad89 results retain their earlier source/APK
attribution and do not qualify this new schema. Next runnable checks are the
corrected Android build/targeted authoring journey, followed by actual SDK/model
author generation under fresh device/resource admission. A host compiler pass
does not establish that model's tokenizer, inference completion, creative
quality, physical/ARM64 performance, cancellation latency or native drain.
No other emulator stop, system setting, server lifecycle, release or merge is
performed. Private evidence and the wheel stay outside public Git.

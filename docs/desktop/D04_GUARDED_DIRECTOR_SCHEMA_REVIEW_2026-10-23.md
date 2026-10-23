# Guard-bound director schema: independent review, 2026-10-23

Refs #9 partial M05.01/.02/.04 and #25 D04.04. Reviewer
`/root/app_storage_review`; claims
[#9 6370527331](https://github.com/OptimumAF/LocalLore/issues/9#issuecomment-6370527331)
and [#25 6370527641](https://github.com/OptimumAF/LocalLore/issues/25#issuecomment-6370527641).
Separate `source-guarded-schema-review`, branch `review/m05-guarded-schema`.

Reviewed author production/tests `5138427ab7e5965315a1d937777bf38cf439b661`,
preceded by frozen actual legacy fixture `43bc8cb` and followed by author
report `4d6b9f662ee88bfe7531b72b9c5615fb223c46bf`. Independent tests are
`f2adbd51f6fe164c6db95e4ea9694f3c74df405a`. No existing production source,
test, fixture, script, manifest or dependency was edited by this reviewer.

This reviewer authored the earlier finite `intent_guard` module. This review
independently examines the new Play/schema integration, not its own earlier
parser as an independent reviewer. No score, human acceptance or full M05/D04
completion is claimed.

## Disposition and source assessment

No new production defect was demonstrated in the bounded source review and
synthetic tests below. This is finite evidence, not proof of all runtime,
grammar, prose or model behavior.

- Action preflight calls the existing finite compiler and Engine preview.
  Its same returned `Command` is retained and serialized into exact scalar
  schema constants. The fixed command object remains required with no extra
  fields; the array has exactly one element. No independent text interpreter,
  generated expected result, model response replacement or alternate
  consequence resolver was introduced.
- A provider is still invoked. Its actual bytes go through the existing
  bounded generator, recursive unique-key parser, command deserialization,
  interpretation equality and Engine preview. Malformed output gets at most
  the existing one repair, with the same bound schema. A different but valid
  command receives Agency rather than being replaced. Repair and narrator
  cancellation preserve the original Engine and accepted history.
- Illegal quantities, unknown/offscreen targets and unavailable mechanics
  fail before emitting a request/schema. Case-insensitive visible display
  aliases resolve to the canonical ID; the new schema does not infer a new
  identity or use a hidden alias. Source restrictions remain the existing
  guard/Engine/compiler decisions, not JSON Schema as an authority.
- Literal Dialogue follows the unchanged say branch. Exact escaped/Unicode
  text stays data; it does not become additional actions or author authority.
  Present audience choices and conservative narrator checks remain unchanged.
- Prompt provenance advances to `locallore-play-v2.3`; policy remains
  `grounded-prose-v2.1`, Play format remains2 and role discriminators remain
  v2. The explicit 2.1/2.2 allowance is gated on recorded-history validation.
  Fresh `commit_prepared` still uses current-version validation. Strict
  history restore/replay/continuation preserves original fields, while exact
  accepted retry returns the already recorded receipt before new inference.
  Version labels/checksums are not authentication of an author.

The finite guard already interprets every supported Action. Under this exact
schema the model is mechanically redundant as its interpreter, while still
being a required potentially failing generation stage. This is a schema
alignment/authority refinement, not expanded free-form NLP, semantic accuracy,
better prose, reduced fallback or measured performance.

The packet's captured base is `8120b422`. A direct diff against accepted
`da2ff01` found no changes in Play, guard, Engine, context compiler, inference
or contracts inputs before this delta. This establishes those input bytes'
equivalence, not fresh integrated Host/Store/Android execution. The coordinator
owns integration on current main and subsequent compatibility qualification.

## Independent execution

Windows NT10.0.26300.0, Rust/Cargo1.93.1. All Cargo commands used
`--locked --offline`, `CARGO_PROFILE_DEV_DEBUG=0`,
`CARGO_PROFILE_TEST_DEBUG=0`, `CARGO_INCREMENTAL=0`, task-owned
`--target-dir <TASK>/guarded-schema-review-target`, and task-owned D-drive
TEMP/TMP. No real provider/model call, worker/assets operation, native app,
device/ADB, CUA, protected resource, network setting, merge or release.

```text
cargo +1.93.1 test -p locallore --test guarded_director_schema_review
6 independent cases PASS

cargo +1.93.1 test -p locallore --all-features --test guarded_director_schema_review --test guarded_director_schema
6 independent +5 author cases PASS

cargo +1.93.1 clippy -p locallore --all-targets -- -D warnings
cargo +1.93.1 clippy -p locallore --all-targets --all-features -- -D warnings
cargo +1.93.1 fmt --all -- --check
git diff --check
PASS
```

Common locked/offline/target flags above are omitted from the short command
display only. This reviewer did not rerun the author's full152/187 Core cohorts
or70 native converter assertions and does not claim those executions.

The new six cases use actual `play::execute`, Engine validation and provider
request capture, with independently declared expected commands:

1. Full-stack quantity65535 plus visible `MIRA` alias on a child at revision0,
   after its parent moved away: exact schema/metadata, both provider stages,
   child consequence and unchanged parent.
2. Offscreen canonical target, unknown target, inaccessible discovery,
   unlearned ability, quantity0/u16 overflow and ambiguous input: exact error,
   zero requests, no canonical mutation.
3. Escaped quotes/backslash and Unicode literal Dialogue on a child: exact
   schema roundtrip, say only, present audience, unchanged abilities/parent,
   unobserved actor isolation and unchanged fallback for hidden narrator claims.
4. Duplicate command keys are malformed; repair retains identical constants.
   A valid wrong repair is Agency, not automatic substitution; neither path
   publishes canon.
5. Cancellation during the repair response and during narration after an
   approved director leaves zero accepted receipts and unchanged state.
6. Both original accepted2.1 and2.2 fixtures restore exactly; fresh root and
   branch-local prepared admissions reject legacy records. A typed branch
   value is obtained through the real strict history loader, not direct Receipt
   deserialization. Exact accepted retries remain zero-call even with an
   already-cancelled token. Rekeyed negative test data is not a claim of
   archive authorship authentication or rewriting original fixture evidence.

Initial independent build failure is retained in
`guarded-schema-review-first.log` (SHA256
`be8f33a2d01f1ab8f660c64f8e081a57765a29010a1868bffdcef3c5f7f4f70e`):
the reviewer initially attempted to deserialize opaque `Receipt`, which is
intentionally non-Deserialize. The test was corrected to obtain its typed
value through actual `restore_continuation`; no production interface or
security assertion was relaxed. No failing production regression is hidden.

Final all-feature focused log SHA256:
`1f94bc9c84e8ed399e3c11f25bd3383f9725502e7dfe248f5001c37376bb9c3b`.
Default focused log SHA256:
`fe134863f39de38eb1e75c0d449281a1ffb5e84a2c98d970cebfea429f53505f`.
Raw logs remain task-local and private.

## Source binding and remaining gates

| Reviewed file | SHA256 |
| --- | --- |
| `crates/locallore/src/play.rs` | `4249bc0f197258772cafc803a839829efb404d43072bcd469c78194761dbfbe8` |
| `crates/locallore/src/intent_guard.rs` | `73c7ffc802db877db2926da365ebc93e78450c17024fa76fcd962ae36f80fd6f` |
| `crates/locallore/src/engine.rs` | `fb26532689a47e029f2e67ce39c161fda13c2a34b75d6e5c43f575f35e0d6191` |
| `crates/locallore/src/context_compiler.rs` | `d59f997c7b003b64f76fb01a2ee78499b634fd454e8892fc85603c9f8fb5ae88` |
| `crates/locallore/src/inference.rs` | `4de0fbc10f0ac7738cd1f11b174a57720d87da0e56a75aacb51bfa7ee6867c9a` |
| `crates/locallore/tests/fixtures/accepted_play_v2_2.json` | `f3645af4047e02b827010134cb57b1d974c86538b68ebf8e43801ea8bcde8f3d` |
| `scripts/tests/guarded_director_grammar.cpp` | `ed2dfad13f8a8c007c72e11d3e36a2ce97a6845dd58cb80cf707248bc729f550` |
| `native/llama-worker/schema_order.h` | `1c20912fc7625bf689338ba4c84a9136351f61f93c4b5613c44e8304cb52e0bc` |
| new independent test | `64142b0744b67bce097ae8276842c47a4e1e9c1cb0710bc8ea20b098757e9207` |

The model-free native helper and existing schema-order adapter were read,
not recompiled or executed here. The author's supplied converter cases include
escaped ASCII Dialogue. This review's Unicode case proves the Rust JSON/Play
path only; it is not a new native Unicode/model qualification. Action command
IDs remain the existing restricted domain identifiers.

Original real-model curated failures/skips remain unchanged. No actual model
cohort, quality, success-rate, latency, worker generation, native WebView,
Android/device or complete Store/workspace compatibility is inferred from
these tests. Coordinator integration and source-bound qualification remain;
future memory prompt2.4 is outside this packet. Full M05/D04 gates stay open.

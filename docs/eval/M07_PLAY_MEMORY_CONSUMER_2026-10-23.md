# Play verified-memory consumer, prompt 2.4 (2026-10-23)

Refs #11 M07.01/.03/.04 and #29 D07.03/.04/.05 prerequisites. This is a Core
consumer slice, not whole-turn desktop integration or a memory quality result.
Coordinator-authorized base `5e44ea91bfa9e93ecf583e31a26937efdfa96366` includes
the accepted verified compiler; no future Host snapshot port is required here.
Claims: #11 comment6374471125 and #29 comment6374471455. Owned production is
only `crates/locallore/src/play.rs`; three existing test blocks change only
current-version/required-field/future-version compatibility expectations.

## Native contract and authority

`execute_traced_with_memory` takes the existing Engine/request/provider/cancel/
profile/sink arguments and `Option<&VerifiedCoverage>`. Existing `execute` and
`execute_traced` delegate None to current `locallore-play-v2.4`. A second native
entry, `execute_traced_with_coverage`, accepts `&CoverageRead` from a coherent
source snapshot. Both use one private execution path and the accepted
`compile_verified_cancelled` against the actual Engine with the same selected
player, Director role, literal Dialogue query policy and budgets.

The same compiler owns proof rechecking, whole-packet raw fallback, raw delta,
deduplication, mandatory current state/facts/beliefs/relationships/commitments,
ranking, exact eligibility and strict source errors. There is no second compiler,
retriever, cache or English interpreter. No inspector or caller-supplied observer
is added. ContextPackage and its serialized shape remain unchanged. Only its
selected records reach the same Director prompt; construction diagnostics remain
outside model input. Narrator still sees only the approved outcomes, with no
memory input. Guarded schema, actual provider output parsing/validation, deadlines,
role caps, repair limit, canonical Engine validation and cancellation are unchanged.
Success is a candidate in the supplied Engine clone; a separate Host/Store commit
must still enforce its canonical concurrency boundary.

## Receipt compatibility and honest provenance

Prompt 2.1/2.2/2.3 are strict history-only compatibility versions. New prepared
commits require 2.4. Historical PlayRecord bytes omit the new optional `context`
field; those historical versions must have None. Current 2.4 requires Some with
closed version1/compiler version, scope/head/player and actual compiler diagnostic
counts. Closed labels, finite caps, bound cursors and actual Engine/request bindings
are checked. Counts are not authenticated cache source evidence, an access grant,
selected-row count, model usage, elapsed work avoided or proof of savings/quality.
`verified` means the compiler accepted a coverage proof; whole packets may still
have been rebuilt raw for time spans or mandatory evidence.

`context.source_fallback_reason` separately preserves a native snapshot's closed
RawFallback reason. Its compiler really received None, so compiler diagnostics
correctly say Raw/Missing. A source Malformed/Binding/etc is never silently relabelled
as source Missing. The Option-proof entry makes no source-fallback claim (None).
No source label constructs a proof, changes compiler output or reaches the model.

Exact retries return the recorded receipt before inspecting current profile,
cancellation or supplied coverage; replay/restore never invoke a provider. The
metadata cannot grant knowledge or canonical effects even if an archive changes
plausible count-only annotations; strict history replay still revalidates the
actual request/proposal/events/narration, finite metadata and scope/player/head.

## Original 2.3 evidence frozen before production edits

Test-only generator `f767dcf31807a084c2829025909662aaa650f70c` ran against
unmodified 5e44 production, using two deterministic synthetic provider responses.
Actual result: **1 passed, 0 failed**, no model/assets. Its sole writer is an
explicitly ignored/env-opted-in test that create_new writes the fixed NEW synthetic
fixture path; it cannot overwrite a fixture. Golden fixture was committed in
`76e1dfeaec7a5c14989647c4e2276a2f14921467` before the version bump. Actual receipt
and timings were retained without normalization. SHA-256:
`57fb218ef2f9a50842f77c2c87cd7e694ca53ea064c6205cfef18abd9e51035c`.
The original 2.1/2.2 fixtures were not edited.

```text
LOCALLORE_CAPTURE_PLAY_V23=1
cargo test --locked --offline --jobs 1 -p locallore --test play_verified_memory freeze_original_v23_receipt_before_memory_consumer -- --ignored --exact
```

This capture command is for the original generator commit, not current 2.4. The
historical helper stays ignored; rerunning it at current source must not silently
regenerate the original fixture.

## Frozen new model-free oracles

NEW `tests/play_verified_memory.rs` has nine consumer tests plus the historical
ignored capture helper. Before first 2.4 execution, the fixed cases require:

- 265 real typed accepted events, retained proof then one real raw-tail event;
  raw/verified actual prompt and ContextPackage byte parity, same actual proposal/
  events/canonical result, mandatory promise/fact/player belief/relationship,
  player secret legitimately present only in Director and NPC-only fact absent.
  Count-only receipt fields must equal the actual compiler diagnostics exactly.
- Whole time-span packet fallback stays labelled raw candidates under an accepted
  verified set, with no cache-use or saved-work relabelling.
- Wrong observer/story/branch and divergent accepted sources recheck against the
  actual Engine and use actual raw context rather than foreign cache content.
- Mandatory budget and cancellation refuse before provider/canonical mutation;
  a valid but wrong generated command stays Agency-rejected, and malformed-output
  repair retains the same guarded schema and existing finite cap.
- Exact 2.1/2.2/original2.3 receipt serialization, restore, replay and retry with
  zero provider calls despite invalid current profile/cancel/foreign proof;
  those versions cannot become new prepared commits.
- Current 2.4 restore/replay/prepared commit and zero-call retry, plus closed
  binding/version/cursor/overflow/unknown-label/missing-context rejection.
- All ten closed native RawFallback reasons are retained separately from actual
  compiler Missing; prompts and canon match the default raw path. The native
  Verified entry equals the Option-proof path and later retry preserves original
  provenance despite a different incoming fallback.

## Qualification status at source freeze

Only the original 2.3 capture has executed. New 2.4 production and oracles are
frozen before Cargo execution and await coordinator resource GO. Rust/Cargo 1.93.1,
rustfmt 1.8.0-stable; own task-specific D target/TEMP/TMP, locked/offline deps,
debug0/incremental0, jobs1. No model/app/native UI/Android/device test is claimed.
Planned checks: the new test target, portable/default/allfeatures Core tests,
Core+workspace integration where appropriate, strict both-feature alltarget
Clippy and workspace fmt. Actual failures/results will be appended without
retuning the corpus, expected commands, budgets or old fixtures.

## Integration still owned by coordinator

Host prepare/Work must obtain a coherent Engine+CoverageRead, enforce selected
canonical prefix/ancestry, carry owned non-Clone coverage and borrow it through
the new native entry; generation must not hold Host/DB locks. This slice admits
no jobs or maintenance. Runtime/worker/model/profile/provider interfaces do not
change. Host trace prompt labels and evaluator source basis already consume
PROMPT_VERSION dynamically; old source-bound reports remain immutable and stale
resume must be refused by their existing validator. The ignored historical
v2.2/schema2 evaluator fixture remains historical and unchanged.

D06 still captures the same ContextPackage/actual provider requests; a retained
candidate now contains the new count-only receipt provenance. Historical capture
is not invented. Desktop receipt presentation/types, actual Host forwarding and
native/JNI compatibility are separate coordinator integration work. The fixed
1032-event retrieval stress, meaningful-session human review and same-scenario
state+recent-transcript versus state+verified-memory comparison remain distinct
gates. No actual model cohort, speed/savings claim, narrative-memory superiority,
whole M07/D07 completion, device/native UI acceptance, release or merge is claimed.

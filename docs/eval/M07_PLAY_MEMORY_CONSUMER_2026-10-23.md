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
$env:LOCALLORE_CAPTURE_PLAY_V23='1'
cargo test --locked --offline --jobs 1 -p locallore --test play_verified_memory freeze_original_v23_receipt_before_memory_consumer -- --ignored --exact
```

This capture command is for the original generator commit, not current 2.4. The
historical helper stays ignored; rerunning it at current source must not silently
regenerate the original fixture.

## Frozen new model-free oracles

NEW `tests/play_verified_memory.rs` has nine consumer tests plus two historical
ignored capture/measurement helpers. Before first 2.4 execution, the fixed cases required:

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

Production/oracles froze before first 2.4 compilation in
`03ace8987acc0cc95c7021ece36546ec558adea6`. All actual checks below are this
agent's own execution: Rust/Cargo1.93.1, rustfmt1.8.0-stable, Windows native Rust,
owned D target/TEMP/TMP, locked/offline deps, debug0/incremental0, jobs1, exclusive
coordinator Cargo slot. No model/app/native UI/Android/device execution occurred.

| Source | Check | Actual result |
| --- | --- | --- |
| 03ace | NEW consumer target | 9 passed, 0 failed, 1 historical helper ignored |
| 03ace | Core + workspace default | 267 passed, 0 failed, 1 historical helper ignored |
| 03ace | Core + workspace all features | 267 passed, 0 failed, 1 historical helper ignored |
| 03ace | Portable Core/no default features | 175 passed, 0 failed, 1 historical helper ignored |
| 03ace | Strict both-feature alltarget Clippy/fmt | Passed |
| b769 original 2.3 production | Original compact-byte probe | 1 passed, 0 failed |
| 28835e6 (test-only strengthening) | NEW consumer target, default and all features | Each 9 passed, 0 failed, 2 historical helpers ignored |
| 28835e6 | Strict both-feature alltarget Clippy/fmt/diff | Passed |

Exact qualification commands (all Cargo commands also use `--locked --offline --jobs 1`):

```text
cargo test --locked --offline --jobs 1 -p locallore --test play_verified_memory
cargo test --locked --offline --jobs 1 -p locallore -p locallore-workspace
cargo test --locked --offline --jobs 1 -p locallore -p locallore-workspace --all-features
cargo test --locked --offline --jobs 1 -p locallore --no-default-features
cargo test --locked --offline --jobs 1 -p locallore --all-features --test play_verified_memory
cargo clippy --locked --offline --jobs 1 -p locallore -p locallore-workspace --all-targets -- -D warnings
cargo clippy --locked --offline --jobs 1 -p locallore -p locallore-workspace --all-targets --all-features -- -D warnings
cargo fmt --all -- --check
git diff --check
```

### Independent original-source compact bytes

Coordinator approved original-production probe
`b769b99ce13725808f56cb60cb5db2e8c1090028`, on f767 plus unchanged fixture76e1
(local fixture import5d15b77). Its production diff versus5e44 is empty. It restores
the unchanged three fixtures and prints only synthetic hashes/lengths, with no
provider or writer. The identical ignored helper is retained in current source.

```text
cargo test --locked --offline --jobs 1 -p locallore --test play_verified_memory original_source_compact_receipt_hash_probe -- --ignored --exact --nocapture
```

| Version | Original compact Receipt bytes | Original SHA-256 |
| --- | ---: | --- |
| 2.1 | 1905 | 4e95baa09c8d0646f5465945bf6a3f659d600ba6ee86b45a45a26d70fc49e234 |
| 2.2 | 1788 | 348f33142a818744bfc1a6a542244fd0a59bae0bbdd7f141d250766cb09bf119 |
| 2.3 | 1760 | e9a1c58aa02236e97041658fae7910b8571ad8d487266a45201c7aa1fa8614e0 |

Those original-source constants were frozen in test-only
`28835e60f292a46b8f13daee268d5c199da8469d` before current verification. Current
default/allfeature consumer tests reproduce all three byte lengths/hashes exactly.
The full original2.3 fixture SHA remains unchanged. Production was not changed
after03ace; final Play source SHA-256:
`916e66d814b34500b6b45e421027636f23bc64daf2dc13d230bbc1e46e72a53e`.
Final consumer test SHA-256:
`38f18bb4c934b7dab3c5a1d58cf8c21b0ebf70338032c07cc1d362b57cf822a9`.

### Retained setup failure

After the successful old-source probe, reusing its target directory for current
source produced 20 missing-new-API/type/field errors (E0425/E0432/E0433/E0609),
zero executed tests. The target contained the old2.3 library. This is preserved
as an artifact/setup failure, not a consumer regression or a passing run. No source,
fixture, expectation or budget changed. A fresh distinct current target rebuilt
the actual unchanged source and passed both final targets/strict checks. Keep
original-source and current-source artifact directories separate when reproducing.

Bounded logs remain local outside Git; SHA-256 bindings:

| Log | SHA-256 |
| --- | --- |
| original-compact-probe.log | 6219f7dc5b9f1bdafdb099ae41828877bdbcab048d10de5724fc3bc5d7cf0aad |
| bytes-default.log (failed shared-target setup) | 2daff25ee1ecd9ed0a47e4a7277e4f53eb53deb3f95744b1f3a13a9f68a4d2ef |
| final-bytes-default.log | 8f5e42c5a31599a0175f9bccb4224d71043408aba1172271b9d6a6f192a402aa |
| final-bytes-allfeatures.log | 10497fe544cb814e5707555d5bb9a3bebc54e023c6c0d235e66e2d22335bbd9e |

No production/test semantic RED occurred on frozen03ace, no oracle was weakened,
and no corpus, expected command or budget was tuned after execution. Claims are
released to the coordinator, status in_review; no task checkbox is marked accepted.

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

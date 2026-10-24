# Independent compiler2 policy source review

2026-10-23. Refs #12 M08.03 consumer prerequisite / #29 D07.03–D07.05.
**Source review and four new frozen oracles only; uncompiled and unrun.** No
compiler qualification, model comparison, native execution or human acceptance
is inferred from this packet.

## Attribution and owned paths

Reviewed `9137083cf6dd638f320ec9422ea30f763946eaf4`, production
`65f027618fb6232bc0b817b0db45ae2f422ea181` / `0e2331e`, with actual Core and
Query2 source. Existing twelve oracles at `9910acd` plus explicitly documented
pre-execution correction `60d2c00` were read and preserved unchanged. Relevant
shared/verified compiler diff, full new policy module, Query2 actor paths,
source filtering, measurement/packing and existing legacy dispatch were read.

Root allocated exactly these NEW paths on separate `review/m08-context-policy` /
`source-context-policy-review` from `9137083`:

- `docs/storage/M08_CONTEXT_POLICY_INDEPENDENT_REVIEW_2026-10-23.md`
- `crates/locallore/tests/m08_context_policy_review.rs`

Claims #12 `6377408942`, #29 `6377409174` preceded writes. Agent
`/root/author_core_review` owns no existing production, frozen test, Core, Query,
Store, Host, Play or schema file. Resource agent retains the heavy slot. Root
owns integration and any demonstrated correction.

The four NEW actual-Engine/compiler review cases are frozen at
`4206d7400c488458bec57ae66c84016b7e2b8af8`, SHA-256
`7b388021438e21692902d9a5a83aa2018949f17e657b99ab111621d1aa07c78a`.
They were added after reviewed production existed and before their first
execution, not presented as tests preceding that implementation.

## Finite source findings

No additional concrete production failure was established by source inspection.
The following are source observations, not behavioral pass results:

- Both requested policies enter the same compile_inner, reference/alias
  admission, mandatory pass, measurement and budget machinery. The policy switch
  occurs in optional construction/selection. KnownAsObserved/current state,
  beliefs, relationships, open promises, source evidence and recent floor stay
  shared. Whole transcript text is constructed after reference admission and
  cannot add a raw-input-only ID or inspection grant to that common phase.
- NPC units use actual Core eligible event-only receipt views. Empty/hidden
  records are removed before unit construction/counting, and NPC original_input
  and narration are None. A partially witnessed multi-event receipt can produce
  the exact NPC event subset without attaching the original player envelope.
- The owning player can attach input/narration only after complete ordered
  AcceptedEvent equality against its actual canonical ordinary receipt. The
  author record/wrapper is not a transcript candidate. The new unit is a derived
  view, not canonical history, and does not grant new character knowledge.
- Query2 supplies mandatory known-as-observed values. Current private world
  truth and author source/reason are not selected through the actor port. Raw
  V2 event visitor eligibility is reused; discovery knowledge rows retain actual
  observed propositions and scoped supporting sources.
- Relevant on a supported Domain1 snapshot rechecks actual old coverage. Domain2
  or Recent refuses the old event-only representation before proof recheck/hash
  and uses raw V2 events with explicit Unsupported. Coverage is separate from
  requested policy and constructed/selected unit counts. A historical snapshot
  before author semantics can legitimately be Domain1; evaluate its actual
  scope/source rather than inventing a rule that all earlier snapshots are mixed.
- Recent detects overlap using original-scope event sources and omits the
  entire unit. Remaining whole units rank newest first; a nonfitting newer unit
  is skipped so an older fitting unit can still be selected. Final diagnostic
  cleanup removes detail before optional records; selected units are ordered
  chronologically afterward without payload clipping.
- Current construction remains version 2; legacy entry source retains version1
  rule strings/shape/dispatch and refuses mixed history before proof work. Exact
  historical bytes still require the actual existing golden tests. Reading a
  refactor is not evidence that all legacy encodings remained unchanged.

The source still builds complete bounded actor receipt views before checking
transcript candidate limits/cancellation between views. Existing accepted-history
and candidate caps bound data, but this review measures no worst-case allocation,
replay time or cancellation latency. It does not claim a new demonstrated defect,
performance improvement or latency qualification from that observation.

## Four independent frozen oracles

1. **Mixed private/public receipt.** A single actual two-event receipt contains
   private player self-speech and heard Mira speech. The NPC unit must contain
   exactly the heard event, no private text, input or narration attachment. The
   player unit must preserve both complete ordered events and actual narration.
   Positive public words remain visible; hearing speech is not forbidden merely
   because the same words appeared in the player's input.
2. **Oversized newest whole unit.** A valid actual Dialogue uses 2,048 control
   bytes. The event plus original player input each escape to 12,288 bytes,
   making the complete unit exceed the entire 24,576-byte context ceiling before
   mandatory state. The test explicitly checks that fixture premise. Recent must
   omit that whole unit with Budget, retain a complete older small unit and stay
   within the same unchanged budget/source. The renderer's Said narration is a
   fixed short sentence, so the fixture deliberately uses actual Dialogue input
   rather than incorrectly assuming narration repeats the spoken text. This was
   verified from source before the first test freeze; no run failure or assertion
   rewrite is claimed.
3. **Private author-only interval.** An author record advances public head/revision
   to 1 but creates no actor unit or raw event candidate. Both policies share
   mandatory observed A, omit private B/reason and report Raw/Unsupported without
   cached-event claims. Relevant's zero constructed units is not described as a
   general absence-of-history diagnostic.
4. **Historical source guard.** An authored branch at current head 3 compiles
   historical revision1 using the same current-head guard and original root event
   scope. Both policies share mandatory state, omit later/author canaries and
   preserve Engine source. A stale expected_head=1 still refuses; selecting a
   historical view does not bypass the current guard.

All use actual Engine/Core/compiler and synthetic fixtures. No second compiler,
retrieval implementation, model or accepted-state mock is introduced. Existing
twelve assertions remain untouched. An invalid new fixture or interface must be
corrected explicitly after preserving this freeze, not silently fitted to source.

## Actual checks, handoff and remaining gates

Only these static operations ran:

```text
rustfmt --edition 2021 crates/locallore/tests/m08_context_policy_review.rs
git diff --check
Get-FileHash crates/locallore/tests/m08_context_policy_review.rs -Algorithm SHA256
```

Parser/format and whitespace checks passed; no typechecking or test result is
claimed. Git 2.33.0.windows.2, PowerShell 7.6.5, rustfmt
1.8.0-stable (01f6ddf758 2026-02-11). No Cargo/Node/Gradle, SQLite execution,
model, app/native IPC/WebView, device, ADB, CUA, desktop control/capture,
download, protected-resource, settings, PR or merge operation ran.

After explicit exclusive-slot allocation, Root can execute unchanged attributable
cases alongside the original twelve and legacy checks:

```text
cargo test --locked --offline -p locallore --test m08_context_policy_review --test m08_context_policy --jobs 1
cargo test --locked --offline -p locallore --test context_compiler_legacy_bytes --test context_compiler --test context_compiler_verified --test context_cancellation --jobs 1
cargo clippy --locked --offline -p locallore --all-targets --all-features --jobs 1 -- -D warnings
```

Use task-owned target/TEMP and no downloads. Retain source hashes, actual compile
or behavioral failures and explicit repairs. Core/workspace compatibility,
Play2.5/narrator policy, Store/schema5 jobs/fallback, coherent Host generation,
capture/trace/privacy decoders, native grant and UI/platform integration, actual
policy-runner execution/model measurements and human quality gates remain
separate. Source enum/function availability is not D07 runner admission. No score,
human approval, milestone checkbox or author wire exposure follows this review.
Claims are released with the ticket handoff.

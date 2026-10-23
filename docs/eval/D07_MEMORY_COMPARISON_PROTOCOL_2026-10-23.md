# Courier comparison protocol prerequisite — 2026-10-23

Refs #29 D07.03/.04/.05; a partial, unregistered model-free protocol, not an executed comparison. Coordinator-delegated `desktop_runtime_profile`, `impl/d07-memory-comparison` in isolated `source-memory-comparison`, Root source `1816b28`. Proposal claim #29 comment6376098772; approved implementation refinement6376293720. This slice owns only NEW `crates/locallore-eval/src/memory_comparison.rs`, NEW `tests/memory_comparison.rs` and this NEW report. Source/oracles frozen **`68e2101`** before compilation. Existing library registration, runner, recorder, Core/compiler/Host/Store, schemas, UI/native, fixture files and old reports are untouched.

Read [frozen design2ac6f831](https://github.com/OptimumAF/LocalLore/blob/2ac6f8315a4b526e3a67578fe33c919976eded5e/docs/eval/D07_MEMORY_COMPARISON_IMPLEMENTATION_DESIGN_2026-10-23.md) as historical design, not current implemented capabilities. Its old `state_verified_memory_v2` proposal is superseded by coordinator allocation **StateRecentTranscriptV1 versus StateRelevantMemoryV1**. Coverage representation/raw fallback is independent of history selection. The coordinator reserves future Play2.5/compiler2; this author allocates no Core version or new policy field.

## Hard boundary and permitted claims

Current source is Play2.4/compiler1. It has the same exact/lexical compiler over raw or rechecked verified coverage, but no recent-transcript policy or policy provenance. Both requested-policy execution gates therefore return `UnsupportedPolicy`; no caller availability boolean, deserialization, environment switch or report flag can enable them. Current2.4 captures cannot be relabeled either future2.5 arm. `validate_pair` can validate a zero-execution plan and rejects attaching current reference observations as an executed policy arm. A separate generic model-free sequence comparator checks actual observations without granting or claiming a context policy.

Root must supply the trusted native-only policy seam in the SAME production Host/Play/compiler. All mandatory rules/current state/known facts/beliefs/relationships/open commitments, their supporting evidence and the recent-event floor remain common. Recent spends only the optional allowance on newest eligible whole original input/narration units, using the existing authoritative player transcript eligibility and deterministic versioned packing. Relevant retains the existing exact/lexical optional selector and independently rechecks whatever raw/verified representation it consumes. No mandatory row is deleted in eval, no role prompt is rewritten, no inspector grant/omniscient transcript is substituted, and no alternate compiler/replay is implemented here.

Literal transcript-only remains an unmet #29 criterion unless the owner explicitly accepts the mandatory-preserving state+recent clarification. The current finite action guard often fixes the command before inference; the narrator sees approved outcomes, not optional long-history retrieval. Old optional detail selection can be measured, but causal model recall, a narrator memory benefit or NPC distinctiveness cannot be inferred. Human review may assess actual narration groundedness/agency/readability/repetition; quality stays false and human review stays `not_reviewed`.

## Immutable original fixture

`frozen_suite()` returns a private-field, Serialize-only fixture with deterministic JSON SHA-256; no external corpus parser or mutable fixture authority is exposed. It constructs a NEW original courier Seed from the unchanged public Lantern Quay fixture: separate seed/story ID, bidirectional pier/tower route, player energy4, a healing bandage and nonhealing pennant. Existing same-name `oren`/`sable`, borrowed brass key/open return-key commitment, asymmetrical relationships and belief-versus-secret distinctions remain. Seed evidence IDs are changed coherently only in this new fixture. Neither `curated-local-v1` nor the original nine-case suite is altered.

| Attempt | Kind / frozen input | Expected Core effect or pre-provider rejection |
| --- | --- | --- |
|01 |Dialogue: The pennant I carry has an amber stitch. |Literal Say to Mira; optional old statement, not truth |
|02 |Action: I learn beacon. |Learn beacon |
|03 |Action: I give bandage to mira. |Give; obligation changes, no invented healing/trust |
|04 |Action: I use beacon. |Spend1 energy |
|05 |Action: I move to pier. |Move |
|06 |Dialogue: I will return the borrowed brass key before tide tick120. |Literal Say to Oren; no new canonical Promise |
|07 |Action: I move to tower. |Move |
|08 |Dialogue: You are the Oren who lives by the tower. |Literal Say to Sable; no narrator/NPC factual speech |
|09 |Action: I give brass-key to sable. |Inventory, zero role requests |
|10 |Action: I use blink. |Ability, zero role requests |
|11 |Action: I move to pier. |Move |
|12 |Action: I wait for one tide tick. |Time advances1 |
|13 |Action: I move to quay. |Move |
|14 |Dialogue: Oren at the tower is different from Oren at the pier. |Literal Say to Mira |
|15 |Action: I move to dry-well. |Move |
|16 |Action: I discover fact beacon-mark. |Actual discovery |
|17 |Action: I consume potion. |Spend potion/heal existing injury |
|18 |Action: I move to quay. |Move |
|19 |Action: I use steady. |Spend2 energy |
|20 |Dialogue: I am returning the items I still carry. |Literal Say to Mira |
|21 |Action: I move to pier. |Move |
|22 |Action: I give pennant to oren. |Give; old optional pennant statement is a reference retrieval target |
|23 |Action: I give brass-key to oren. |Return item, clear borrowed flag |
|24 |Action: I complete promise return-key. |ClarificationRequired, zero role requests |

The Rust source freezes exact punctuation/spacing; the table summarizes it (e.g. source text06 has `tick 120`). Four scenes contain six attempts each. Planned denominator is **24 attempts,21 expected accepted provider turns,3 expected guard-only refusals**, not24 generated turns. It contains one Wait and five literal Dialogue attempts, with travel/learning/resources/discovery/transfers in between.

There is no supported free-text borrow/obtain or CompletePromise form. Borrowing/promise begin in the Seed; returning the key does not silently set `completed_by`. Attempt24 preserves the completion gap rather than using a typed teacher-forced correction. No NPC-generated statement is invented. All expectations/preconditions are checked through the existing public finite guard and actual Engine preview. Failed generated proposals are retained as failed; later dependent steps skip only when the same Core reference action actually refuses the actual resulting state. No expected receipt is inserted into a failed run.

The intended optional-selection target is the old Said pennant detail at22, after it leaves the shared recent floor. The open promise/item ownership/current facts are mandatory in both policies and cannot demonstrate optional retrieval benefit. Current2.4 tests inspect the actual Context artifact and actual director envelope separately. They do not execute a recent arm or establish a causal output benefit.

## Pure interfaces and provenance

- `frozen_suite` and `reference_proposal`: immutable fixture and the actual Core guard/preview oracle, no English interpreter or execution loop.
- `check_observation`: consumes actual before/after Engines, actual accepted Receipt or closed Core error/dependency result, admitted GenerationRequests and optional actual captured ContextPackage. It revalidates the accepted receipt with the shared Engine, compares opaque full source bases and rejects canonical change on failure. Only this native constructor can produce `TurnEvidence`; it has no Deserialize/capability wire form.
- Separate actual envelope checks, displayed narration checks and raw output availability. Legitimate player secret may reach the player director and is forbidden in narrator input. Foreign/sibling/parent-future synthetic markers are checked on both roles. Raw outputs are not supplied by this API, so `raw_output_privacy_passed=None` rather than a fabricated pass; the existing runner/recorder retains that owning responsibility.
- `Binding` binds distinct run ID, exact source/fixture/profile/prompt, provider lane, requested policy and experiment kind. Actual asset/profile authority remains the established runner's factory and locked-handle worker checks; this module opens no asset or file and duplicates no pins.
- `Charges` validates copied existing-ledger cumulative counters only:32 admissions/96 charged roles/30active minutes/32invocations per arm; unknown charges cannot reset on resume. It reserves/spends/refunds nothing. The two-arm total ceiling64/192/60minutes/64invocations is a proposal, **not model-run authorization**.
- `validate_pair` refuses drift, duplicate IDs, missing/out-of-order prefix rows, underreported role/admission counts and broken continuous source chains. It never blesses an unavailable policy. `compare_sequences` distinguishes exact opaque source equality from semantic input equality: the latter hashes actual Seed/Scope/head plus original Request/Proposal/events/display narration, excluding Play timing/configuration/context diagnostics. This comparison-only hash grants no canonical authority. Paired-snapshot observations still require EXACT original before-basis equality; continuous rollouts report first semantic divergence and stop treating later rows as same-snapshot A/B observations. No percentages are inferred from empty samples.
- `render_human_packet` emits every supplied contiguous chronological prefix row, including failures/skips/fallback, with planned/observed denominators and escaped actual text under128KiB. It cannot reconstruct missing private captures or supply human acceptance. No filesystem writer, new report store or ledger is added.

No role/resource process counter, clock domain, percentile, peak RAM, tokenizer measurement or phone-performance claim is manufactured. Existing recorder/runtime instrumentation and orchestration remain coordinator-owned. Encoder allocations are capped at2MiB, admitted role envelopes/schemas have finite bounds, and a turn observation is capped by its original24-attempt history position before cloning/revalidating an Engine.

## Frozen tests and unrun gates

NEW test file contains12 model-free tests using actual Core Play with a clearly scripted provider, the existing TraceSink Context artifact, actual GenerationRequests and actual shared replay/receipt validation. They cover24/21/3 fixture outcomes and guards, actual optional-detail capture versus role envelope, player's positive secret/narrator exclusion, wrong-command divergence/dependency skip, timing-only comparison behavior, tiny mandatory budget0provider refusal, source/profile/kind/budget/unknown-charge drift, source substitution, escaped actual accepted narration, ordering/counter underreporting and deliberately corrupted captured-envelope rejection. That last vector injects a marker into supplied capture data; it is not a claim Core leaked the marker. Foreign/sibling ancestry filtering continues to require the owning shared tests and integrated cohort.

At this source freeze **none is compiled or executed**. Only new-file rustfmt and `git diff --check` passed. No Cargo/Node/Gradle/app/native IPC/render/worker/model/device/desktop/CUA/settings/download/protected-resource action ran. The module has no existing library registration or CLI path. Tests use a path include so Root may qualify it before allocating a separate library/runner integration change. The existing build source collector already includes new `.rs` files recursively, so source hashes will truthfully change; this is not a waiver allowing an old-source execution resume.

After a coordinated resource GO, proposed exact checks (not yet executed), Rust1.93.1, task-owned D target/TEMP, debug0/no incremental:

```powershell
cargo test --manifest-path crates/locallore-eval/Cargo.toml --locked --offline --jobs 1 --test memory_comparison
cargo test --manifest-path crates/locallore-eval/Cargo.toml --locked --offline --jobs 1 --features local-model --test memory_comparison
cargo clippy --manifest-path crates/locallore-eval/Cargo.toml --locked --offline --jobs 1 --test memory_comparison -- -D warnings
```

Actual current-source default/local-model compatibility, strict checks and source-bound fixture hash follow separately. Root then supplies the shared Play2.5/compiler2 policy seam, closed provenance/legacy rules and authoritative transcript eligibility before any execution gate can change. Root owns existing runner/checkpoint/recording integration, fake-baseline parity, reservations/lost acknowledgement/cancel/reopen/completed-resume control paths, historical read-only views and native/UI bridges. Those are not implemented by this pure module.

Any real-model cohort still needs exact source/common-policy/profile/fixture/budgets/order/asset bindings frozen and a separate bounded authorization using existing approved assets only. No approved b5 worker or model was opened here. Full D07 remains unchecked, literal transcript-only/causal recall/complete promise/new narrator evidence remain explicit limitations and quality/human acceptance remain false/not_reviewed.

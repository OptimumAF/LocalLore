# Evaluation and test strategy

Status: target evaluation strategy. The [host verification report](IMPLEMENTATION_EVIDENCE.md) and [Compose shell report](android/VERIFICATION_2026-10-22.md) record actual host/fake-provider and emulator checks. Storage, native engine/inference, physical-device and narrative-quality gates below remain unverified; the fixture shell does not pass those gates.

## Separate what is being tested

**Engine correctness:** deterministic rules, canonical transitions, transaction semantics, replay, isolation, and migrations.

**Memory correctness:** eligibility, source coverage, invalidation, attribution, and retrieval quality.

**Model behavior:** valid proposals, grounded narration, character voice, player agency, and bounded repair.

**Mobile behavior:** lifecycle, cancellation, permissions, storage, inference integration, memory/thermal limits, accessibility, and error UX.

A pass in one category does not imply a pass in the others. Mocked inference is appropriate for engine/lifecycle tests but not for storytelling quality or real-device performance.

## Test pyramid and execution locations

Host unit tests cover pure reducers, validation, scope, and prompt/context assembly. Property-based tests generate valid/invalid operation sequences and retain failing seeds. SQLite integration tests cover transactions, foreign keys, migration, export, and replay. Fake-provider integration tests cover malformed outputs, delays, stale responses, retry, and cancellation. Android instrumentation checks lifecycle and native integration. Physical-device tests cover real model behavior and sustained performance.

Default public PR CI must not require giant model downloads, proprietary fixtures, private credentials, a paid inference endpoint, or access to someone's phone. Separate opt-in owner-approved real-model/device jobs from deterministic PR checks. Never run untrusted fork code on a privileged self-hosted runner.

## Original reference scenarios

| ID | Scenario | Required result |
|---|---|---|
| E01 | Give away the last potion | One transfer/consumption, no potion remains, effect follows rules |
| E02 | Retry the same successful request | Original result returned; no duplicate event/reward |
| E03 | Claim an unlearned teleport ability | Attempt fails or is explained; ability not silently granted |
| E04 | Lie about royal ancestry | Statement recorded; ancestry unchanged |
| E05 | Private confession with one witness | Only eligible listeners gain the relevant information |
| E06 | A false accusation spreads | Source attribution and beliefs preserved; truth not overwritten |
| E07 | Two NPCs share a display name | Stable IDs/clarification prevent accidental merging |
| E08 | Old promise after many distractors | Unresolved thread and supporting evidence remain retrievable |
| E09 | NPC respects but distrusts player | Response can reflect both dimensions |
| E10 | NPC moves between locations | Past and current locations remain temporally distinct |
| E11 | Attempt to reuse a spent item | Engine rejects without resurrecting inventory |
| E12 | A character dies under applicable rules | Later actions respect status unless a valid rule/event changes it |
| E13 | Fork before a betrayal | New branch excludes the betrayal and its consequences |
| E14 | Parent continues after a fork | Child does not inherit later parent events |
| E15 | Retcon a committed event | Explicit alternate history; stale summaries excluded |
| E16 | Switch stories during generation | Response never attaches to the new active story |
| E17 | Cancel just before/after commit | One clear committed-or-not outcome; no fictional rollback claim |
| E18 | Process dies while writing | State is old or fully committed new state, never partially applied |
| E19 | Disk fills during import | Existing stories remain unchanged; no partial imported story |
| E20 | Malicious archive traversal/cycle | Rejected before unsafe writes or unbounded ancestry traversal |
| E21 | Prompt injection in dialogue/pack | No privileged tool, author edit, cross-scope read, or code execution |
| E22 | Summary fabricates a reward | Summary rejected/invalidated; no change to canonical inventory |
| E23 | Switch local model | Future prose changes; accepted history/replay remains unchanged |
| E24 | Export and import a branched story | Eligible history, state hashes, and visibility are preserved |
| E25 | Delete story with derived indexes | Canonical and derived story data removed; other stories intact |
| E26 | Oversized mandatory context | Safe narrowing/failure; critical rules not silently dropped |
| E27 | Model repeatedly returns invalid plan | Bounded attempts; no state mutation; usable error path |
| E28 | Narrator invents a consequential key | Not silently canonicalized; explicit repair/correction path |
| E29 | App closed overnight | No plot-time advance unless explicitly configured and accepted |
| E30 | User action omits a major decision | Narrator does not invent marriage, betrayal, or a life choice for player |

Each fixture should contain initial canon, messages/actions, permitted facts/knowledge, forbidden consequences, expected event/state assertions, and visible response constraints. Use original synthetic names/content, not copied private saves or another application's materials.

## Deterministic gate

Run all unit/integration scenarios relevant to a change. The host property suite should exercise at least 10,000 seeded transition attempts for qualification, including invalid combinations. Require zero failures in the finite suite for implemented mechanical invariants, idempotency, replay hashes, and scope isolation. Preserve shrinking/minimization output for failures.

Property tests should not simply reproduce implementation logic in the oracle. Include independent assertions such as conservation, unique ownership, valid ranges, traceable provenance, no unauthorized scope, and identical replay from accepted outcomes.

## Crash and concurrency protocol

Inject failures around draft creation, snapshot read, proposal completion, validation, narration, commit start, individual writes, transaction completion, summary maintenance, and import. Repeat duplicate sends and delayed completions. Test cancellation races explicitly: if commit wins, show the committed turn; if cancellation wins, no events are applied.

Test migration/replay from previous schema fixtures. Test SQLite's actual chosen journal and synchronization settings on the deployment environment. Copying a database without its current transaction state is not a validated backup process.

## Memory and long-session evaluation

Use 1,000+ synthetic accepted events with distractors, aliases, old obligations, time changes, and branching. Measure mandatory eligible-context coverage, retrieval recall/precision at the chosen budget, forbidden-record inclusion, stale-summary use, and attribution errors.

Then run real-model story sessions of varied lengths, including a long target such as 200 turns when practical. Count retrieval failures separately from model misuse of correct context. A test that directly injects ground truth into the prompt is useful for narrator isolation but cannot prove retrieval works.

Store exact fixture version, model/runtime profile, prompt/schema versions, settings, and the sampled transcripts used for review. Do not describe a scripted 1,000-event database as a 1,000-turn live model experiment.

## Narrative quality rubric

Review groundedness, character differentiation, consistency of motivations, useful memory, player agency, prose clarity, repetition, pacing, and meaningful consequences. Define severe errors in advance: invented consequential abilities/items, leakage of hidden facts, wrong character identity, reversing a major consequence without an event, or making a major player choice.

Use paired/blinded comparisons where possible and publish sample counts, reviewer method, disagreements, and limitations. A 1–5 rating can summarize feedback but is not the sole acceptance criterion. No '8/10 from an agent' release gate. A model judge can flag candidates, but human review and deterministic tests carry different evidentiary weight.

## Privacy and security checks

Review every permission/dependency, inspect outbound connections under relevant flows, and test a network-unavailable session after provisioning. Check backup/transfer configurations, logs, clipboard and export behavior, model-file handling, archive traversal/size limits, native parser dependencies, input length bounds, and malicious instruction/data separation.

Character secrecy is a story-consistency boundary, not the same as filesystem confidentiality. Test both. Canary secrets help diagnose leaks, but absence of a canary in a small sample does not prove a universal guarantee.

## Acceptance record and release decision

Every report states exact commands, environment, scope, sample size, results, failures, unmeasured fields, and evidence paths. Use `templates/COMPLETION_EVIDENCE.md` and `templates/BENCHMARK_REPORT.md`.

Release qualification requires no unresolved critical data-loss, cross-story leakage, or unintended-network behavior in the approved scope; published supported profiles; reproducible builds/tests; owner review of residual risks; and truthful documentation. App-store review and broad device compatibility remain separate milestones.

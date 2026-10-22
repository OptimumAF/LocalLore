# LocalLore — living development plan

Version: 0.1. Prepared: 2026-10-22. Status: documentation bootstrap; no application implementation. Owner: Avery Fernandez (`@OptimumAF`). Working project name: LocalLore.

## 1. Mission and success definition

Build a completely local phone app for open-ended, chat-driven stories that preserve meaningful consequences. A player should be able to return after hundreds of turns and find that abilities, items, promises, character relationships, and knowledge still make sense. The app must be enjoyable as fiction, not merely correct as a database.

The fundamental split is **creative proposal versus canonical authority**. The model proposes interpretations, events, character behavior, and prose. The engine validates typed changes against known state and rules, commits accepted history, and supplies bounded context for narration. A free-text claim is not automatically a fact; an NPC does not automatically know everything the director knows.

The first proof is a small original scene, not an ambitious world simulator. Give a scarce potion to an injured NPC, restart the app, and demonstrate that the item stays spent, the recipient remembers, an unwitnessed third party does not know, and a later interaction reflects the consequence.

The project will enforce defined mechanical invariants. It will measure, improve, and make recoverable the semantic inconsistencies that can still occur in free-form language. Do not promise perfect memory, unlimited context, zero hallucinations, or flagship-model quality on every phone.

## 2. Requirements that cannot be silently traded away

- All inference, retrieval, and gameplay memory updates operate on-device. No mandatory account, server, analytics, cloud fallback, or subscription backend.
- Persistent player progression; durable short-/long-term history; character identities and directed relationships; separate truth and beliefs; independent story/branch scopes.
- Player agency: free text matters, but dialogue and attempted actions cannot silently authorize arbitrary powers or author-mode edits.
- Inspectable provenance for important facts; recoverable corrections; portable user-controlled story exports.
- A genuine open-source codebase with explicit licensing and contribution provenance. Third-party model licenses remain separate.
- Community participation without automatic delegation of upstream control. The owner retains final merge, release, access, and direction authority.
- A living plan that is checked off with evidence and improved as discoveries are made.

Proposed initial defaults: Android first; Kotlin/Compose UI; portable Rust domain engine; SQLite; one production inference backend after benchmarking; one loaded model serving multiple roles. These are revisable through documented decisions, not claims of proven superiority. The exact target device/RAM and minimum OS remain open.

## 3. How agents must execute and maintain this plan

### Status and evidence

Use stable IDs. `[ ]` means not done; annotate `todo`, `in_progress`, `blocked`, `in_review`, `deferred`, or `superseded` in the work log. `[x]` means the stated deliverable and acceptance criteria are satisfied with evidence. Do not treat a stub, written specification, fake provider, emulator run, or test plan as evidence that a real-device feature works.

Before work, read the actual repository, record a claim in `docs/WORK_LOG.md`, and identify the gate. During work, update status after meaningful increments. At the end, record exact checks, results, evidence paths, known gaps, and the next task. A PR can propose completion; the authoritative default-branch checklist reflects accepted work. Bootstrap document items below refer only to prepared documents, not remote publication or approval of every design choice.

A completed task should normally have implementation, tests, failure-path coverage, relevant docs, and evidence. A milestone is not complete until its exit gate passes. If a gate requires unavailable hardware or permissions, mark it blocked and continue independent tasks. Never fabricate an experiment or weaken a gate merely to make a checkbox green.

### Adapting the plan

Change the plan when evidence justifies it. Record what was discovered, options considered, the chosen change, consequences for dependencies/tests, and any owner approval needed. Split large tasks; retain IDs for replaced work and mark them superseded rather than erasing history. Use an architecture decision record for cross-cutting choices. Security promises, licensing, governance, local-only operation, and major scope changes require owner approval.

Do not create dozens of implementations before evaluating the first vertical slice. At each milestone boundary, decide whether to continue, revise, or stop a failing approach. Run only work that has clear prerequisites, ownership, and a credible test.

### Parallel work rules

When multiple agents are available, divide by independent ownership: runtime/device; engine/persistence; memory/characters; mobile UX; evaluation/security. Each assignment includes task IDs, permitted paths, interface version, acceptance tests, and handoff format. Use separate branches/worktrees. The coordinator owns shared contracts, schema/migration changes, integration, and progress reconciliation. Agents must not overwrite each other's work or independently merge/release. If delegation is unavailable, execute the same dependencies sequentially and report that accurately.

## 4. Dependency map and release boundaries

| Milestone | Primary outcome | Depends on | Can overlap |
|---|---|---|---|
| M00 | Documentation and owner-controlled public repository | None | Document review |
| M01 | Measured runtime/model feasibility and support decision | M00 documents | M02 contracts; M03 fake-provider shell |
| M02 | Domain contracts and original adversarial fixtures | M00 documents | M01 |
| M03 | Minimal buildable engine/mobile harness | M02 core interfaces | M01 benchmarking |
| M04 | Authoritative persistence and turn transactions | M02, M03 | M05 UI/inference wiring against stable contracts |
| M05 | First playable on-device consequential scene | M01, M03, M04 | M06 preparation |
| M06 | Progressive memory and character knowledge | M04, M05 | M07 against stable memory contracts |
| M07 | Bounded long-story retrieval and summaries | M06 | M08 design |
| M08 | Safe branches, corrections, portable stories | M04, M06, M07 | M09 UI |
| M09 | Cohesive phone UX and story authoring | M05–M08 | M10 testing |
| M10 | Reliability, privacy, performance and quality gates | M05–M09 | Community documentation |
| M11 | Owner-approved public alpha and contribution workflow | M10 | None for release gating |
| M12 | Post-alpha expansion based on evidence | M11 + owner prioritization | Independent proposals |

M05 is the first internal vertical slice. M09 is feature-complete for the proposed alpha scope. M10 is release qualification, not a substitute for testing earlier milestones. No app-store date or hardware performance is promised.

## M00 — Seed the project and preserve owner control

**Goal:** make the project's purpose, execution process, and authority explicit before code or community access expands.

- [x] **M00.01 — Prepare product and technical specifications.** Evidence: product, architecture, data, memory, evaluation, and privacy documents in `docs/`. They state assumptions and distinguish proposed behavior from implemented behavior.
- [x] **M00.02 — Prepare the living roadmap and agent instructions.** Evidence: this file, `AGENTS.md`, `AGENT_PROMPT.md`, work-log/evidence templates. The instructions explicitly require evidence-backed completion and documented plan adjustments.
- [x] **M00.03 — Prepare open-source/community material.** Evidence: Apache-2.0 license, governance, contribution/conduct/security policies, CODEOWNERS, issue and PR templates. No model weights or proprietary story material are included.
- [ ] **M00.04 — Create and verify the new public repository.** Use the intended personal account, confirm the working name is available, publish only reviewed starter files, verify public visibility, license recognition, owner identity, default branch, and exact remote commit. Do not overwrite an existing repository.
- [ ] **M00.05 — Apply and verify repository controls.** Configure PR-based changes, code-owner review, owner-only initial access, explicit owner self-PR bypass where necessary, no automatic merging, and safe Actions permissions. Validate settings through read-back; a CODEOWNERS file alone is not enforcement.
- [ ] **M00.06 — Establish reporting and owner decisions.** Verify private vulnerability reporting; establish a private conduct contact; record approved defaults and unresolved device/runtime decisions. Do not invent a contact address, grant a collaborator role, or create a public security inbox containing sensitive reports.

**Exit gate:** documents are published in a verified public repository; owner/control settings are read back; remaining unavailable settings are clearly blocked, not claimed enabled. Document preparation alone does not pass this gate.

## M01 — Prove device and model feasibility before product-scale work

**Goal:** identify at least one real device/model/runtime combination capable of the intended turn workflow.

- [ ] **M01.01 — Establish the reference device and reproducibility record.** Record actual OS, chipset, physical RAM tier, available memory/storage, power/thermal state, and test versions without serial numbers. If no phone is accessible, record the blocker and perform only explicitly labeled host-side preparation.
- [ ] **M01.02 — Build a minimal inference spike, not a production framework.** Compare a compatible LiteRT-LM path and a compatible llama.cpp path using official examples. Confirm model architecture, conversion, tokenizer/chat template, quantization, and backend support at pinned revisions. Do not assume an arbitrary GGUF works in every app.
- [ ] **M01.03 — Evaluate structured plans and narration separately.** Use the same original fixtures, bounded schemas, stop sequences, and output budgets. Record malformed outputs, invalid event proposals, repair rate, language quality, and character distinctiveness. A general benchmark rank does not select the model.
- [ ] **M01.04 — Measure the complete turn.** Separate loading, retrieval, prefill, director generation, validation/repair, narrator prefill/generation, persistence, and first final-response latency. Measure peak memory and at least one sustained session; document run counts and warm/cold conditions.
- [ ] **M01.05 — Test constrained-device behavior.** Exercise cancellation, app backgrounding, memory pressure, long prompts, thermal throttling, missing/corrupt model files, and low storage. Failure must be explained and recoverable; no cloud fallback.
- [ ] **M01.06 — Select one initial backend and supported profile.** Write the runtime/model ADR with measurements, licensing, rejected alternatives, supported context/output caps, and known limitations. Keep a small adapter interface; do not ship two full integrations without demonstrated benefit.

**Exit gate:** reproducible raw aggregate results exist for a physical device; one profile meets owner-approved latency/quality/memory targets in `docs/MODEL_EVALUATION.md`. If none passes, reduce turn/output budgets, test a smaller model, or revise the workflow rather than claiming unsupported compatibility. The model names in the research shortlist are candidates only.

## M02 — Freeze the smallest domain contracts and evaluation world

**Goal:** define what the engine can guarantee before independent implementations depend on it.

- [ ] **M02.01 — Write invariant specifications.** Define inventory conservation, resource bounds, ability prerequisites, life/death and location rules, allowed fact transitions, actor knowledge, player agency, and unresolved uncertainty. Every invariant has a failing fixture.
- [ ] **M02.02 — Define typed commands, events, and validated outcomes.** Separate requested intent from resolved effects; include versioning, story/branch identity, expected revision, participants, witnesses, provenance, and idempotency. Unknown operations are rejected, not executed generically.
- [ ] **M02.03 — Specify progression/rules profiles.** Define a small numeric fantasy profile and a lightweight non-combat profile to avoid hardwiring every story to RPG stats. Specify currency/quantity arithmetic and ability restrictions without floating-point ambiguity.
- [ ] **M02.04 — Define the portable engine/inference boundary.** Freeze request/result/error/cancellation interfaces usable by a fake provider and native mobile backend. SQLite has one owning persistence layer; do not let Rust and Kotlin independently migrate or mutate it.
- [ ] **M02.05 — Author an original test setting and fixtures.** Include a scarce potion, borrowed key, false claim, hidden relic, directed relationship, time-limited promise, unlearned ability, and three NPCs with unequal knowledge. Do not copy an existing application's characters or premium content.
- [ ] **M02.06 — Specify player versus author mode.** Decide how out-of-story commands, quoted instructions, ambiguity, correction requests, and player internal thoughts are treated. Destructive history changes require an explicit UI author action, not merely model interpretation.

**Exit gate:** contracts and synthetic fixtures are reviewed; each key rule has a testable expected result; other workstreams can implement against stable interfaces without inventing their own definitions of truth or branch scope.

## M03 — Build the smallest host and mobile foundations

**Goal:** support fast engine tests and a real Android shell without pretending that scaffolding is a product.

- [ ] **M03.01 — Initialize a minimal Rust workspace and host harness.** Introduce only the domain, persistence, and test boundaries needed now. Add format/lint/test commands and pin the toolchain. Do not create many empty crates or a speculative plug-in system.
- [ ] **M03.02 — Initialize an Android Compose application.** Select and document minimum/target SDK after checking runtime and distribution requirements. Verify build/install on an emulator and the reference phone where available. No unused internet, media, contact, or location permissions.
- [ ] **M03.03 — Connect the engine through a narrow FFI boundary.** Validate serialization, error mapping, cancellation ownership, callbacks, resource disposal, and UI-thread safety. Do not allow a dangling native generation session after the screen is destroyed.
- [ ] **M03.04 — Add a deterministic fake inference provider.** Support accepted, malformed, rejected, delayed, cancelled, and failing responses. It enables plumbing tests but cannot satisfy model quality or performance requirements.
- [ ] **M03.05 — Establish safe CI and development instructions.** Host-side tests and Android compile checks must run from documented commands. Pin reviewed third-party actions, use read-only permissions, avoid privileged untrusted PR execution and self-hosted runners, and keep model downloads out of default PR CI.
- [ ] **M03.06 — Add privacy-safe local diagnostics.** Record bounded timings/error categories with no story text by default. Diagnostic export is explicit and previewable; no remote collector or automatic crash upload.

**Exit gate:** a clean checkout builds the host harness and Android shell using documented commands; fake-provider flows and cancellation work; test/build claims distinguish host, emulator, and physical-device execution.

## M04 — Implement canonical history, projections, and atomic turns

**Goal:** make save/load/retry correctness independent of model behavior.

- [ ] **M04.01 — Implement the versioned SQLite schema and migrations.** Use scoped identifiers and composite foreign keys for story/branch-related tables; enable and test foreign-key enforcement on every connection. Keep schema versions, reversible safety backups, and migration fixtures.
- [ ] **M04.02 — Implement deterministic event reducers.** Derive current entity state, inventory, resources, locations, and thread status from accepted events. Test canonical replay hashes while excluding documented transient diagnostics. Store random outcomes rather than rerolling them on replay.
- [ ] **M04.03 — Implement staged turn lifecycle and idempotency.** Use unique turn IDs and expected revisions. Never hold a write transaction open during inference. Commit accepted events, projection updates, completed response, and turn status atomically; duplicate submissions return the recorded result.
- [ ] **M04.04 — Implement safe interruption and conflict recovery.** Cancelled drafts do not alter canon. A late generation after branch switch is discarded or retained only under its originating draft. Process death, disk-full errors, stale snapshots, and retry paths cannot partially spend resources.
- [ ] **M04.05 — Enforce story isolation from the start.** New stories have separate state namespaces. Queries, unique constraints, indexes, diagnostics, and fake-provider sessions cannot mix them. Explicitly test identical display names and item IDs across stories.
- [ ] **M04.06 — Add snapshot and integrity tools.** Treat snapshots as validated accelerators, not new truth. Rebuild from history, compare versions/hashes, and recover from corrupt/stale snapshots. Use consistent backup APIs rather than copying only a live database file while ignoring its journal/WAL.

**Exit gate:** replay and duplicate-turn tests pass; seeded generated-event sequences preserve all implemented invariants; fault injection at each commit stage leaves either the old or fully committed new state, never a partial state. Tests run without any LLM.

## M05 — Deliver the first playable on-device scene

**Goal:** prove the experience and the full transaction boundary before scaling memory or content.

- [ ] **M05.01 — Build the intent/director prompt and constrained proposal schema.** Separate user action, spoken text, and privileged UI intent. Refer to existing entities by IDs; new entities use temporary references resolved by the engine. Set bounded numbers of operations and generated tokens.
- [ ] **M05.02 — Validate and resolve proposed outcomes.** Reject unknown operations, invalid ownership, insufficient resources, unlearned abilities, duplicate rewards, impossible locations, and unauthorized knowledge transfers. Recompute dependent reactions after changed outcomes rather than accepting a stale plan.
- [ ] **M05.03 — Generate bounded narration from accepted outcomes.** Supply scene facts and the approved plan; isolate character dialogue to permitted knowledge where necessary. Distinguish harmless descriptive freedom from consequential new claims. Do not expose secret director reasoning or hidden character data to the player.
- [ ] **M05.04 — Add bounded repair and fail-safe paths.** Permit at most the configured repair count; never loop indefinitely. On repeated failure, leave canon unchanged and present a retry/rephrase option or a safe engine-generated response. Repair attempts may not replay already committed operations.
- [ ] **M05.05 — Ship the potion scene through the real local backend.** Support free-text play, an optional non-binding suggestion, cancellation, restart, and the memory inspector. Demonstrate the scenario in the README only after it actually runs.
- [ ] **M05.06 — Evaluate enjoyment as well as correctness.** Compare the same scene with naive transcript-only prompting and the engine pipeline. Record distinct NPC voices, meaningful choice, pacing, repetition, contradictions, latency, and player-agency violations. Do not publish an unsupported claim of being better than a named competitor.

**Exit gate:** the potion/secret/invalid-action sequence runs on the reference phone without a network, survives restart, preserves the ledger, and produces understandable prose. Publish a synthetic trace and measured limitations. This is an internal demo, not release readiness.

## M06 — Add persistent player progression and character-specific memory

**Goal:** implement all three core memory concepts without creating competing sources of truth.

- [ ] **M06.01 — Implement player progression.** Store abilities, inventory, attributes, injuries, affiliations, and commitments with acquisition/change events. Distinguish fixed backstory, evolving mechanics, and subjective interpretations. Rule checks use structured state, not a summary paragraph.
- [ ] **M06.02 — Implement NPC identity and current state.** Track stable IDs, names/aliases, motivations, background, abilities, location, status, and important experiences. Prevent accidental duplication or merging when names collide. Known entities can grow without being rewritten.
- [ ] **M06.03 — Implement directed relationships.** Store independent dimensions or evidence-backed descriptions for trust, respect, fear, affection, resentment, and obligation. Preserve supporting events and asymmetric attitudes; avoid a universal affinity score or automatic romance.
- [ ] **M06.04 — Implement claims, beliefs, observations, and knowledge transfer.** Distinguish ground truth from a statement and a character's interpretation. Track witnesses, sources, time, uncertainty, and later corrections. A liar can knowingly transmit a false statement without changing reality.
- [ ] **M06.05 — Implement open narrative threads.** Track promises, deadlines in story time, clues, faction intentions, and consequences. Advance only relevant off-screen activity when story time advances, recording any effects as events. Closing the app does not advance story time by default.
- [ ] **M06.06 — Build provenance inspection and secrecy tests.** Explain why a visible item/ability/relationship is recorded, with source-event links. Hide spoiler-bearing knowledge in play mode. Verify an unwitnessed character cannot retrieve another character's private memory or learn from an author's omniscient notes.

**Exit gate:** player and NPC state agree with history; relationships are directional and evidence-linked; allegations do not become facts; visibility-filtered inspection and dialogue tests pass across a multi-scene session.

## M07 — Scale history with bounded, evidence-linked retrieval

**Goal:** remember what matters while controlling context, latency, and memory footprint.

- [ ] **M07.01 — Implement the context compiler.** Assemble mandatory rules/current state, recent turns, referenced entities, unresolved commitments, relationship evidence, and older relevant events under explicit token budgets. Apply story/branch/time/observer restrictions before serialization.
- [ ] **M07.02 — Add exact and lexical retrieval first.** Use IDs, aliases, structured relationships, event tags, and verified SQLite full-text support. Parameterize queries, escape search syntax, and handle no-results or ambiguous names. Do not require a graph server or remote vector service.
- [ ] **M07.03 — Add derived scene/chapter/entity summaries.** Record source-event ranges, branch/revision, summary version, model/prompt provenance, and visibility class. Summarize original accepted events, not endless summaries of summaries. Stale summaries are excluded or supplemented with exact deltas.
- [ ] **M07.04 — Add invalidation and resumable maintenance.** Corrections, new facts, and branch changes invalidate affected summaries/indexes. A maintenance job verifies the source revision before accepting output, is cancellable, and never silently mutates canon.
- [ ] **M07.05 — Evaluate semantic retrieval as an optional extension.** Add a local embedding model only after measured failures of lexical/structured retrieval. Record memory/latency costs, artifact licensing, embedding/index version, and incremental rebuild behavior. No remote embeddings.
- [ ] **M07.06 — Run long-history retrieval and interference tests.** Test old promises, aliases, irrelevant distractors, wrong branches, stale timelines, and secrets at 1,000+ synthetic accepted events. Report retrieval accuracy separately from the model's ability to use retrieved facts.

**Exit gate:** all mandatory facts in the finite reference suite are supplied or generation stops safely; no unauthorized record reaches a character context in isolation tests; relevant older events remain retrievable within the approved budget. Long-history quality and timing are measured, not inferred from a model's advertised context size.

## M08 — Implement safe branches, corrections, and portable stories

**Goal:** let users control their story without making memory incoherent.

- [ ] **M08.01 — Implement branch ancestry and fork-point visibility.** A child inherits only ancestor events up to its fork, never later parent events or sibling histories. Bound graph traversal depth and detect invalid cycles on import. Scope summaries, retrieval results, and cached contexts to their lineage/revision.
- [ ] **M08.02 — Define regenerate, rewind, and edit behavior.** Regenerating uncommitted prose changes no state; replacing a committed turn creates a new branch from before the affected turn. Do not silently replay downstream choices that depended on the old outcome.
- [ ] **M08.03 — Implement explicit author corrections.** Present the affected facts/events and invalidated descendants before applying a revision/branch operation. Separate in-story corrections such as learning a rumor was false from an out-of-story retcon. Preserve the original branch until the user explicitly deletes it.
- [ ] **M08.04 — Implement versioned export/import.** Include canonical events, required seed/config data, branch lineage, transcript, schema/rules/prompt/model references, and checksums; exclude model weights and private diagnostics by default. Validate archive paths, expanded sizes, counts, IDs, schemas, and ancestry before writing.
- [ ] **M08.05 — Implement deletion and resource cleanup.** Delete a story's messages, events, projections, summaries, embeddings, caches, and pending drafts. Handle shared ancestor references safely; do not break a retained branch. Explain limitations of forensic deletion on flash storage and external export copies.
- [ ] **M08.06 — Verify round trips and incompatible versions.** Export/reimport preserves canonical hashes and branch knowledge. Unsupported versions fail without partial imports; migration requires a safe copy and rollback strategy. Changing the model does not rewrite accepted history.

**Exit gate:** branches cannot leak future/sibling events; edited history does not retain stale summaries; round-trip/replay fixtures pass; corrupt or hostile imports are rejected without modifying existing stories.

## M09 — Make the phone experience cohesive and usable

**Goal:** turn the engine into an understandable app rather than a collection of developer panels.

- [ ] **M09.01 — Build onboarding and model management.** Explain local storage and realistic hardware requirements; support explicit file import, compatibility/hash checks, available-space checks, cancellation, removal, and recovery. A networked model catalog/downloader is deferred unless separately approved; play never depends on it.
- [ ] **M09.02 — Build the multi-story library and creation flow.** Allow title, original premise/template, tone/content boundaries, character setup, and rule profile. Preview generated initial facts before committing them. Keep character creation editable without silently backdating later edits.
- [ ] **M09.03 — Polish the chat and turn lifecycle.** Provide clear generation/cancellation/error states, draft input persistence, optional suggestions, scrolling behavior, regeneration controls, and a concise outcome inspector. Do not display unvalidated streaming text as if it is finalized canon.
- [ ] **M09.04 — Build character/progression/history screens.** Show meaningful character state, evidence-linked relationships, threads, and searchable visible history. Start with lists and focused relationship views; a force-directed graph visualization is not an alpha prerequisite.
- [ ] **M09.05 — Add accessibility and comfort controls.** Verify screen readers, scalable text, touch targets, contrast, keyboard behavior, reduced motion, dark/light themes, and readable long messages. Do not make color the only status indicator. Avoid engagement pressure or pretending fictional NPCs are real people.
- [ ] **M09.06 — Validate complete user journeys.** Test creating two stories, importing a model, playing, cancelling, resuming after process death, inspecting a fact, branching, correcting, exporting, importing, and deleting. Test low storage and unsupported hardware messaging with unfamiliar users where available.

**Exit gate:** the core journeys work with real local inference and without developer intervention; errors are understandable; accessibility checks pass for the reference configuration; no screen implies planned functionality is already available.

## M10 — Qualify reliability, privacy, performance, and story quality

**Goal:** convert promising demos into a defensible alpha readiness decision.

- [ ] **M10.01 — Run deterministic and property-based regression suites.** Cover typed transitions, idempotency, invariants, replay, migrations, isolation, and invalid operation combinations. Target at least 10,000 seeded generated transition attempts in the host suite with reproducible failure seeds; this tests the suite, not a proof of all possible behavior.
- [ ] **M10.02 — Run fault injection and mobile lifecycle testing.** Interrupt at staging, generation, validation, commit, summary maintenance, and import. Test repeated submission, app process death, memory pressure, low storage, rotation/navigation, and concurrent stale responses.
- [ ] **M10.03 — Audit the local-only contract.** Review manifest/dependencies, outbound-traffic observations, backup/transfer rules, logs, exports, file access, model import, and CI. Test offline play from installed/imported artifacts. Document OS/keyboard/compromised-device limitations explicitly.
- [ ] **M10.04 — Run the adversarial story benchmark.** Evaluate bounded and long sessions, secrets, lies, promises, entity collisions, resource costs, prompt injection, branches, and player agency. Distinguish hard-invariant failures, retrieved-context failures, semantic hallucinations, and subjective prose ratings.
- [ ] **M10.05 — Complete real-device performance qualification.** Record cold/warm and sustained turn distributions, first final-response latency, memory, thermal behavior, and available energy measurements. Approve a supported device/profile matrix and smaller-model degradation path. Never list untested devices as supported.
- [ ] **M10.06 — Review licenses, dependencies, and release risks.** Produce a dependency/license inventory, model manifest policy, threat-model review, open-risk register, and release recommendation. No critical unresolved data-loss/privacy bug; owner explicitly accepts residual narrative/performance limitations.

**Exit gate:** all release-blocking tests pass in the stated environment, reproducible reports exist, limitations are published, and the owner approves the scope. Model-judge scores alone never waive a failing deterministic or privacy test.

## M11 — Release a controlled community alpha

**Goal:** welcome contributions without sacrificing safety or owner authority.

- [ ] **M11.01 — Prepare accurate public documentation.** Replace bootstrap-only instructions with verified build/install/run steps, supported profiles, a synthetic demo, contribution entry points, known limitations, export warnings, and reporting instructions. Remove obsolete promises.
- [ ] **M11.02 — Establish reproducible packaging and provenance.** Pin runtime/toolchain/dependencies; create a source/build manifest, checksums, license notices, and an auditable release procedure. Keep signing credentials private and out of ordinary PR workflows.
- [ ] **M11.03 — Verify upstream access and automation.** Read back rulesets, code ownership, collaborators, integration access, Actions permissions, branch/tag/release controls, and private vulnerability reporting. Require owner approval for release operations. Do not grant admin access to attract contributors.
- [ ] **M11.04 — Prepare manageable community entry points.** Open a small number of actionable tasks for tests, docs, accessibility, original fixtures, and reproducible device benchmarks. Do not auto-create every plan checkbox as an issue. Publish decision/ADR practices and respectful moderation expectations.
- [ ] **M11.05 — Perform an owner-controlled alpha release.** Sign/package only after explicit approval; publish tested assets, checksums, source commit, model installation instructions, limitations, and change log. A GitHub alpha does not imply app-store approval or broad device support.
- [ ] **M11.06 — Triage real feedback and revise this plan.** Separate bugs from design requests, preserve privacy in reports, reproduce failures, prioritize reliability over new features, and record what changed in the next milestone. Keep community reviews advisory unless formally delegated.

**Exit gate:** the owner approves and performs/authorizes release; published artifacts match verified source and documentation; contributors can reproduce the development workflow without paid cloud services or private story data.

## M12 — Post-alpha proposals, not automatic commitments

- [ ] **M12.01 — Evaluate iOS support.** Reuse the portable engine where sensible; benchmark actual devices and runtime integration, background behavior, file import, backups, and platform distribution rules before promising parity.
- [ ] **M12.02 — Evaluate additional rules/genres and creator tools.** Add declarative versioned packs and validation, not arbitrary executable plug-ins. Improve story authoring based on observed usability problems.
- [ ] **M12.03 — Evaluate local voice, images, embeddings, or specialist models.** Each needs a separate memory/thermal/privacy/license budget and an ablation showing user benefit. Do not run many models concurrently by default.
- [ ] **M12.04 — Evaluate richer simulations and visual relationship graphs.** Expand only after long-session reliability and story quality are demonstrated. Avoid unbounded background agents or omniscient NPCs.
- [ ] **M12.05 — Revisit governance only by owner decision.** Community maintenance can expand through named, scoped delegation. No automatic change to founder control, licensing, release authority, or access.

## 5. Cross-cutting acceptance and evidence standards

Hard correctness is evaluated independently of prose. The reference deterministic suite must have zero failures for implemented invariants, duplicate application, replay equality, and scope isolation. A sampled test suite is finite evidence, not proof that all inputs are safe.

Narrative quality uses fixed original fixtures, predefined expected facts, blinded comparisons where practical, and human review on meaningful samples. Report sample size, model/runtime revisions, task mix, and severe failures. Report retrieval recall, use of retrieved facts, unsupported claims, character distinctiveness, repetition, and agency separately; do not collapse all of them into a single flattering score.

Performance thresholds in the model document are initial targets that require device calibration. A change to thresholds is a documented design decision, not an invisible grading adjustment. Always measure the full director-plus-narrator experience, including repairs and context assembly.

Privacy verification includes architectural restrictions and device observations. A passing network trace on one device is not proof about all dependencies or operating systems. User-controlled exports, external keyboards, screenshots, and OS backups need explicit boundaries.

Each completed milestone should leave a useful artifact: benchmark report, stable contract, test suite, working vertical slice, or qualified release. Do not create documentation merely to inflate progress.

## 6. Main risks and response

| Risk | Early signal | Response |
|---|---|---|
| Two-pass generation feels too slow | Long first final-response latency | Shorten plans/prose, reduce context, test smaller model, improve prompt reuse; never hide latency with a false completion state |
| Good prose but bad state proposals | High repair/rejection rate | Simpler schemas, stronger examples, narrower operations, engine-resolved mechanics |
| Correct database but contradictory narration | Unsupported consequential prose claims | Better grounded narrator contract, bounded validation, explicit correction flow; do not claim mechanical correctness solves prose |
| NPC knowledge leaks | Secret canaries appear in filtered contexts/dialogue | Enforce observer filtering, isolate speaker contexts, audit summary visibility and cache keys |
| Branch contamination | Future/sibling facts retrieved | Centralize ancestry eligibility; include lineage/revision in all derived artifacts |
| Scope expansion before validation | Many unfinished modules | Stop at milestone gate; ship the small scene first |
| Device thermal/OOM failures | Performance decays during play | Sustained measurements, lower budgets, cancellation/unload paths, explicit support tiers |
| Public repo leaks personal data | Raw saves/logs attached | Synthetic fixtures, ignore rules, review checklist, export preview, no automatic issue uploads |
| Community authority becomes ambiguous | Unreviewed merges/access grants | Owner-only initial permissions, clear governance, explicit delegation records |
| Paper settings mistaken for protection | CODEOWNERS present but rules absent | Read-back evidence and pending setup checklist |

## 7. Immediate next execution packet

First verify M00.04–M00.06 or state the exact blocked capability. Then start M01.01–M01.03 and M02.01–M02.02 in parallel if supported. With no phone, prioritize contracts, original fixtures, and a host-side test harness while leaving physical-device feasibility incomplete. With no delegation, do the same work sequentially.

Do not begin graph visualization, image generation, on-device fine-tuning, a marketplace, multiplayer, a hosted backend, or an agent per NPC. The first target remains a small, consequential, recoverable story on a real phone.

## 8. Plan change history

- **2026-10-22 / v0.1:** Initial documentation-first plan prepared. Public publication and settings remain pending. Android/Rust/SQLite are starting proposals. Added explicit distinction between facts and beliefs, transaction-safe turns, bounded inference, branch-aware retrieval, privacy constraints, real-device gates, and founder-controlled governance.

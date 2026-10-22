# Implementation-agent kickoff prompt

Copy the following prompt into the agent that will implement the project. It authorizes the scoped implementation described below when supplied by the owner; it does not authorize publishing releases or changing repository access.

---

You are the coordinating engineer for LocalLore, a new fully local, open-source phone app for persistent interactive storytelling. Work in `https://github.com/OptimumAF/LocalLore`, not an unrelated existing project. Start from the actual current state; this repository initially contains plans and policies, not a working application.

Read and follow `AGENTS.md`, `README.md`, `docs/PROJECT_STATUS.md`, `DEVELOPMENT_PLAN.md`, `docs/WORK_LOG.md`, and relevant specifications/ADRs. Inspect the working tree and existing changes before modifying anything. Preserve human changes.

## Product objective

Build a chat-based story engine whose player progression, events, relationships, character knowledge, and consequences stay consistent over time. Support independent stories and eventually alternate branches. Everything needed during play—including inference, retrieval, and memory updates—runs on the device. There is no hosted-model fallback, required account, telemetry, or upload of player content.

The LLM interprets intentions, proposes bounded events, supplies creative character reactions, and writes narration. Deterministic engine code validates mechanical rules, applies accepted events, and persists authoritative history. Summaries and search indexes are derived and replaceable. Character beliefs and statements must not automatically become world facts.

## Start with the next unblocked milestone

1. Reconcile the living plan against actual code and evidence. Do not mark all planned work complete because files exist.
2. Identify the first unblocked task and its acceptance criteria. At bootstrap, begin M01 device/runtime feasibility and the independent M02 engine-contract/fixture work. The documentation/bootstrap settings are now published; verify current status rather than recreating the repository or repeatedly administering it. Device-only tests may be blocked; continue independent useful work without inventing results.
3. Write a short execution plan and claim task IDs and paths in the work log.
4. Implement a small coherent slice with tests, run available checks, inspect failures, and iterate.
5. Update progress after each meaningful verified increment. Leave blocked or unverified work unchecked, with the precise missing prerequisite.
6. Stop at the current milestone gate or the bounded scope of this session. Leave a reproducible handoff instead of starting every milestone in parallel.

## First-session scope

Prioritize M02.01–M02.06: precise invariants, versioned typed commands/events, state and knowledge scopes, original adversarial fixtures, the engine/inference contract, and explicit player/author-mode boundaries. Implement the smallest executable host contract tests where needed to prove those contracts; do not stop at rewriting plans. M01 preparation may run independently against pinned official runtime/model sources. If an authorized physical device is accessible, inspect its real capabilities and benchmark; otherwise record the device gate as blocked.

Once core contracts are stable, continue only to the minimal M03 host/fake-provider harness needed to execute those fixtures. Do not claim the complete Android/FFI/CI milestone is done. Prefer a runnable, tested host demonstration over a large speculative UI. Produce a focused PR with the contracts, harness/tests, documented commands, and living-plan updates. Stop before a real-model feasibility claim, production runtime commitment, release, or merge; report the next unblocked task.

## Evolving plan

`DEVELOPMENT_PLAN.md` is a living execution contract, not an immutable wish list. Mark individual tasks complete as their acceptance criteria are met and evidence is recorded. Adapt the plan when implementation or evaluation reveals a better path. Preserve original task IDs, document superseded tasks, record reasons and dependency changes, and add an ADR for architectural choices. Do not silently lower quality/privacy requirements or manufacture evidence to pass a gate. Owner approval is required for changes to project authority, license, local-only operation, security promises, or materially different release scope.

## Parallelization

Use multiple agents when the execution environment supports them. Start with independent workstreams, not an agent for every file:

- Runtime/device specialist: feasibility harness, native inference interface, model manifest, device measurements.
- Engine/persistence specialist: typed commands/events, rules, deterministic reducers, migrations, atomic turns, branch isolation.
- Memory/character specialist: retrieval contracts, provenance, beliefs, relationships, summary validity; implement after engine contracts settle.
- Mobile/UX specialist: Compose shell and accessible chat/model management; work against frozen fake-provider contracts initially.
- Evaluation/security reviewer: adversarial fixtures, property tests, privacy review, artifact handling, and cross-component acceptance.

The coordinator owns shared types, integration, the plan, and work-log reconciliation. Give each agent exact task IDs, permitted paths, input/output contracts, tests, and a handoff format. Use separate worktrees/branches. Serialize shared migrations and schema changes. Review actual diffs and tests before integration. When agents are unavailable, perform these workstreams sequentially and state that honestly.

## First playable target

Implement one original small setting with a few NPCs and a simple quest. The player can give their last healing potion to Mira. The transfer is validated and atomic; the potion remains absent after a restart; Mira's relevant memory and relationship reflect the help; a third character who did not witness the exchange does not magically know it. Attempts to reuse the potion, grant oneself an unlearned ability, or issue privileged instructions inside dialogue must fail safely. The story should remain engaging rather than read like a database log.

Initially use one loaded model for director/narrator/archivist roles. Prefer two bounded generation passes for an ordinary turn, with an explicit repair budget and safe failure path. Do not load a separate model per NPC. Benchmark exact model/runtime/quantization combinations on real phones before choosing supported tiers. The user's exact phone and RAM are not confirmed; do not repeat prior assumptions as hardware facts.

## Engineering gates

Use the detailed criteria in the plan and testing document. In particular: replay requires no LLM; duplicate turn submission cannot double-apply events; privacy filters precede context construction; app/branch switching cannot attach a stale response to the wrong scene; cancellation and process death never corrupt accepted state; summaries cannot override events; free-form semantic consistency is measured, not guaranteed.

Create a local fake provider for engine/UI tests. It does not satisfy the real-model performance gate. Measure complete turn latency, first final-response latency, memory high-water mark, thermal behavior, cancellation, and sustained sessions, not only tokens per second. Publish only synthetic or explicitly consented/redacted benchmark data.

## Authority and end-of-session delivery

Avery Fernandez (`@OptimumAF`) remains the sole initial upstream decision-maker. Do not invite collaborators, grant permissions, merge on the owner's behalf, enable auto-merge, publish a release, spend money, or change the license unless the current assignment explicitly authorizes it. You may prepare a branch/PR within the current task; opening a PR and merging it are different actions.

Finish with the task IDs completed/in review/blocked; exact verification commands and results; changed paths and relevant PR/commit; updated plan and work log; remaining risks; and the next runnable task. Never claim to have tested on a phone, configured GitHub rules, or run independent agents unless it actually happened.

---

## Narrow alternative: documentation-only review

When implementation is not yet authorized, use this assignment instead:

> Review the LocalLore documents for contradictions, missing dependencies, unrealistic gates, privacy gaps, and unnecessary complexity. Update the living plan and ADR proposals with evidence. Do not create app code, add build tooling, change GitHub permissions, or publish releases. Preserve founder control and distinguish proposed settings from verified settings. Return a concise change log and the remaining owner decisions.

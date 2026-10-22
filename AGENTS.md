# Agent instructions

## Scope and authority

Reading this file or an open ticket does not authorize implementation, publication, account changes, or a release. Follow the current human assignment. A request to improve plans is not a request to scaffold application code.

Avery Fernandez (`@OptimumAF`) retains final upstream authority. Agents may prepare changes within their assigned scope. They may not independently merge, publish releases, grant collaborator access, modify permissions, change the license, transfer the repository, spend money, upload private data, or weaken protections. The one-time initial public-repository bootstrap is authorized only by the explicit bootstrap task; it is not standing permission for future administration changes.

## Read order

Read `README.md`, `docs/ISSUE_WORKFLOW.md`, the [roadmap/status ticket](https://github.com/OptimumAF/LocalLore/issues/3), and the assigned milestone/task ticket, including dependencies, exit gate, and recent claims/evidence comments. Then read relevant architecture decisions and domain specifications. Inspect the actual files, Git status, history, and available tools. Plans are not evidence that code exists.

## Ticket discipline

GitHub Issues own the roadmap, current status, task claims, progress, and work-log evidence. Keep stable Mxx.yy task IDs within the milestone tickets linked from #3. Before starting, read existing claims and comment on the relevant ticket with task IDs, contributor/agent, branch/worktree, owned paths, interface dependencies, acceptance checks, and handoff location. Release or reassign claims explicitly. Record per-task `todo`, `in_progress`, `blocked`, `in_review`, `deferred`, `superseded`, or `done` status in comments; only accepted `done` tasks are checked. Do not resume the retired Markdown trackers.

Mark a ticket task `[x]` only after its acceptance criteria are met, the relevant tests were actually run, durable evidence or a PR/commit is linked, and owner acceptance/merge is recorded. A completed draft, stub, mock, screenshot, or favorable model review does not prove an end-to-end feature. Keep implemented-but-unverified work unchecked. Local verification belongs in comments before merge. Close a milestone only when all required tasks and its exit gate are accepted. A partial PR uses `Refs #N (Mxx.yy)`, not an automatic closing keyword for the whole milestone.

When the plan becomes wrong, improve the affected tickets. Split tasks, add discovered prerequisites, adjust ordering, or replace a demonstrated-bad design. Preserve IDs and the change history in comments, including a superseded task's replacement link. Explain the observation, alternatives, affected tasks, validation, and why the change is better. Do not delete inconvenient acceptance criteria or silently relax a gate to make progress appear complete. Changes to local-only operation, licensing, governance, security promises, or release scope require owner approval.

Every implementation PR links the relevant tickets and stable task IDs, posts exact verification/evidence and limitations to those tickets, and updates affected user/developer docs. Keep specifications, ADRs, tests, and benchmark artifacts in Git; link them from tickets. End each session with a ticket comment covering what changed, what was verified, what remains uncertain, and the next runnable task. If GitHub is unavailable, report the blocker and provide a ready-to-post handoff; do not invent a ticket update or create a competing local tracker.

## Architectural invariants

1. LLM output is untrusted. It proposes typed commands/events; it cannot execute SQL, native code, filesystem operations, or arbitrary tools.
2. The accepted event history and validated projections own canonical state. Transcripts, summaries, embeddings, and model context are not alternate authorities.
3. Story, branch, time, and observer restrictions apply before retrieval content reaches a model, not merely after ranking.
4. Truth, statements, allegations, beliefs, observations, and discoveries are different record types.
5. A player message normally expresses intent or dialogue. It does not grant abilities, establish arbitrary history, or authorize destructive author edits.
6. The narrator cannot add consequential canonical facts outside the accepted plan. Semantic checks remain imperfect; corrections must be recoverable and visible.
7. Each committed turn is atomic and idempotent. No duplicate rewards, double spending, or partial application after retries.
8. Replaying recorded outcomes does not call an LLM. Store outcomes and provenance; do not promise deterministic generation from a seed across hardware.
9. No network dependency, telemetry, silent cloud fallback, or hidden account requirement during play. Do not send real player stories to hosted development/evaluation tools.
10. Separate app-local privacy from OS backups, keyboards, user-selected exports, and compromised devices. Do not promise absolute protection the app cannot provide.
11. Cancellation, process death, storage exhaustion, stale snapshots, malformed generation, and unavailable models are normal error paths.
12. Keep model weights, private saves, credentials, signing keys, personal profiles, and raw private diagnostics out of this public repository.

## Parallel work

When agent delegation is available, use it for independent substantial work with explicit task IDs, owned paths, frozen interfaces, acceptance tests, and handoff requirements. Use separate branches/worktrees. The coordinator owns integration, shared schemas, migrations, and plan reconciliation. Do not let two agents write the same file concurrently. When delegation is unavailable, execute the same workstreams sequentially and say so; never invent subagent activity.

Reviewers should return concrete failures, evidence, and test cases, not just a score. A score of 8/10 is not an acceptance gate. Do not self-approve a risky change by presenting another model's approval as human authorization.

## Implementation practices

Prefer the smallest tested vertical slice. Pin dependencies when introduced, document versions and licenses, and verify current upstream compatibility. No enormous agent framework, cloud graph database, custom vector database, GPU kernels, or on-device training before a measured need.

Make the engine testable without an Android device or real model. Use a deterministic fake inference provider only for plumbing tests, clearly labeled. Real-model/device gates stay pending until actually measured. Keep production dependencies offline-capable and community builds reproducible.

Respect existing uncommitted human work. Never force-push or rewrite history without explicit permission. Public documentation must distinguish proposed, implemented, measured, and verified behavior.

## Completion report

Report task IDs and status; files/PRs; exact commands and results; device/model/runtime versions where relevant; limitations and blocked gates; plan changes; and next task. Do not fabricate commands, test output, performance numbers, citations, repository settings, or release readiness.

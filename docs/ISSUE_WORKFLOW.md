# Working from GitHub tickets

GitHub Issues are the source of truth for the roadmap, current project status, task ownership, progress, blockers, and work-log evidence. Start with the [roadmap and status ticket #3](https://github.com/OptimumAF/LocalLore/issues/3), which links all milestone tickets and their dependencies. The former Markdown trackers are pointers only.

## Find and claim work

Read the assigned ticket's checklist, acceptance criteria, exit gate, dependency tickets, and recent comments before choosing a task. Stable IDs such as M02.01 identify individual tasks within a milestone ticket. A ticket being open is not authorization to implement it: follow the current human assignment and AGENTS.md.

Read existing claims first. Before editing, post a claim comment containing the date, exact task IDs, contributor/agent, branch/worktree, owned paths, interface version/dependencies, planned acceptance checks, and handoff location. Use separate branches/worktrees for independent writers. Release or reassign claims explicitly; serialize shared schemas, migrations, and files.

Use task statuses `todo`, `in_progress`, `blocked`, `in_review`, `deferred`, `superseded`, and `done` in comments. A milestone may contain tasks with different statuses; an open issue alone does not distinguish them. Describe a blocker and its missing prerequisite while continuing independent authorized work.

## Progress, evidence, and acceptance

Post meaningful progress and end-of-session handoffs on the affected ticket. Include task IDs/status, changed paths, branch/PR/commit, exact commands/results, environment/versions, evidence links, unrun checks, limitations, review/acceptance, and the next runnable task. Use [completion evidence](templates/COMPLETION_EVIDENCE.md) as a comment format. Retain tests, specifications, ADRs, benchmark reports, and synthetic fixtures in Git and link their durable paths/commits from tickets. Do not upload private stories, secrets, or unique device identifiers.

Check a task only when its full acceptance criteria and actual checks are evidenced and owner acceptance/merge is recorded. Local checks can be reported before acceptance; partial host/fake-provider or emulator work cannot satisfy a physical-device gate. Close a milestone only when all required tasks and its exit gate have been accepted. Deferred/superseded work needs an explicit disposition and replacement/decision reference, not a false completion check.

PRs reference both ticket numbers and stable task IDs, for example `Refs #6 (M02.01–M02.06); Refs #7 (M03.01/M03.04 host slice)`. Do not use automatic issue-closing keywords for partial milestone work. Link the PR and its verification on each relevant ticket. Update source documentation affected by the implementation; do not maintain duplicate progress tables in Git.

## Revise the roadmap

Use [plan change](templates/PLAN_CHANGE.md) as a ticket-comment format when evidence changes scope, dependencies, or gates. Preserve stable IDs and history, explain alternatives and validation, and link an ADR for architectural decisions. Owner approval is required for changes to local-only operation, licensing, governance, security promises, or material release scope.

The original 77 tasks are grouped in 13 milestone tickets. Split out a task only when it needs independent tracking; keep its stable ID, copy its criteria/dependencies, link both directions, and make the parent row a pointer to the child ticket as the authority for that task. Avoid two independently maintained task checklists. Proposals remain subject to owner prioritization; an issue is not a release commitment.

If GitHub is unavailable, report the blocker and return a ready-to-post claim or evidence handoff. Do not claim an update succeeded or create a competing Markdown tracker. Existing permissions for implementation, merging, releases, and administration remain governed by the human assignment and repository policies.

## Historical evidence

[Archive #2](https://github.com/OptimumAF/LocalLore/issues/2) preserves the former PROJECT_STATUS and WORK_LOG through accepted setup commit `e3551b2`. [The original development plan](https://github.com/OptimumAF/LocalLore/blob/e3551b2/DEVELOPMENT_PLAN.md) remains in Git history; all task criteria and milestone gates were migrated to tickets. Historical blockers and setup instructions describe their original dates; use current ticket comments and accepted PRs to determine current status.

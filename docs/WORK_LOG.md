# Work log and task claims

## How to use

The coordinator records active claims before delegation. A claim includes task ID, agent/contributor, branch/worktree, owned paths, shared-interface dependencies, acceptance criteria, and handoff location. Release or reassign abandoned claims explicitly. One writer owns a shared file at a time.

For completion evidence, include date, task, changed paths/PR/commit, exact checks, results, limitations, reviewer/owner acceptance, and next task. Avoid credentials, private content, device serials, or fabricated measurements. Use `templates/COMPLETION_EVIDENCE.md` and `templates/PLAN_CHANGE.md`.

## Active claims

Bootstrap coordinator owns `docs/finish-bootstrap` through integration of the setup evidence. No application implementation agent is active.

## 2026-10-22 — Documentation preparation

Scope: prepare a new public open-source project, comprehensive evolving plan, agent instructions, and community policies. Working name: LocalLore. Intended owner: OptimumAF. Implementation intentionally not started.

Prepared: root documentation, domain specifications, roadmap, governance, license, contribution templates, and repository setup guidance. Completion applies to document preparation only.

Remote blocker: the available GitHub actions did not include creating a repository or administering its settings. A metadata check for `OptimumAF/LocalLore` returned not found; this is not proof that the name is permanently available. No remote repository was created or modified. A separate owner-run publishing helper is included in the downloadable package, outside the proposed repository tree.

Unverified: physical-device feasibility, production model/runtime choice, application behavior, branch protection, private reporting, release permissions, and all implementation milestones. No device tests or independent subagent reviews are claimed.

Next: verify/publish the repository; execute M01 and independent M02 work under a new explicit implementation assignment.

## 2026-10-22 — Public repository publication

Owner authorization: create public `OptimumAF/LocalLore` and upload the prepared starter files; browser fallback explicitly approved. Signed-in browser identity and connected GitHub owner both verified as OptimumAF.

M00.04: **done**. Created a new public repository without overwriting an existing project. GitHub metadata verified owner/account ID 88298311, repository ID 1430285879, public visibility, `main`, and recognized Apache-2.0 license. Original payload commit: [`0d095babe5ad661f829dc6ebe10951bad0e00783`](https://github.com/OptimumAF/LocalLore/commit/0d095babe5ad661f829dc6ebe10951bad0e00783). Tree: `4af0338494666b7f253457c1e8541a179d6f6aea`.

Validation: `python3 publish_github.py --check` passed before publication: 35 UTF-8 files matched the package manifest. After upload, fetched the recursive remote Git tree and compared each path and `SHA1("blob " + byte_length + NUL + bytes)` against the local package: all 35 matched; tree was not truncated. Read back `refs/heads/main` and confirmed the payload commit. No application tests or device/model benchmarks were run. A direct shell clone did not complete and was stopped; verification used the connected GitHub API instead.

M00.05: **blocked/incomplete**. Read-back verified issues on, wiki off, auto-merge off, squash available, and merged-branch deletion on. Actions UI reported “Actions policy updated” and showed “Disable actions” selected; default workflow permissions were read-only and PR creation/approval by Actions was off. Prepared an active default-branch ruleset requiring one approval, code-owner review, stale-review dismissal, conversation resolution, and no force pushes/deletion, with bypass only for OptimumAF in pull-request context. Saving was rejected by automatic approval review because the specific enforcement rules/bypass require explicit owner approval. No ruleset creation is claimed and no alternate route was used to bypass the rejection.

M00.06: **todo**. Private vulnerability reporting, conduct contact, collaborator/invitation audit, and integration audit remain pending. No contributor access, secrets, model weights, private stories, application release, or implementation was added.

Publication-status follow-up updates README, project status, this log, and the M00.04 checkbox so the live repository does not continue to claim it is unpublished. This is an authorized bootstrap correction, not completion of the application or the full M00 gate.

Next: obtain approval for the prepared branch rules, verify them after submission, finish reporting/access checks, then begin M01/M02 only under an implementation assignment.

## 2026-10-22 — Approved controls and setup closeout

Authorization: the owner explicitly approved the detailed ruleset, then granted permission to finish GitHub and initial-document setup and requested an implementation prompt. This resolves the earlier approval blocker. No application implementation was authorized for this setup session.

M00.05: **done upon integration of this setup PR**. Saved ruleset 25677641 and read it back from the GitHub rulesets API: active, default-branch target, deletion and non-fast-forward restrictions, pull-request rule with one required approval, stale-review dismissal, code-owner approval and conversation resolution. Sole bypass actor: User 88298311 (OptimumAF), mode `pull_request`; no integration/role bypass. Saved UI confirmed “Ruleset created” and applicability to `main`. The effective-branch-rules URL is unsupported by the connector; this limitation was not presented as a GitHub rule failure. The setup-doc PR is used for the owner self-PR merge verification.

The access UI showed 0 collaborators and “You haven't invited any collaborators yet.” The repository's integration inventory showed AWS Amplify (us-east-2), AWS Connector for GitHub, ChatGPT Codex Connector, and GitGuardian. These inherited installations were not added, removed, or exempted from rules. Account-wide permissions remain untouched and cannot be inferred solely from a collaborator count.

M00.06: **done upon integration of this setup PR**. Enabled private vulnerability reporting; saved UI confirmed the setting and provided its configuration link and a Disable control. Enabled dependency graph and Dependabot alerts. Retained existing secret/push protection; left paid AI scanning/fix agents off and Actions disabled. No actual vulnerability/abuse report or outbound message was submitted as a test.

ADR-0002 records the deliberate conduct-reporting adjustment: GitHub abuse tools/Support are the bootstrap route for sensitive abuse, with limits clearly documented; no personal email or dedicated owner inbox is invented. Initial planning defaults and unresolved real-device/runtime decisions are documented in PROJECT_STATUS. This changes the reporting mechanism, not privacy, licensing, or founder authority.

Docs updated: README, plan, project status, setup checklist, conduct/security policies, references, kickoff prompt, ADR-0002, and this work log. Product milestones stay unchecked. Verification uses saved GitHub configuration and remote content hashes; no application/device tests are claimed. The accepted first-session prompt scopes M02 contracts/fixtures and a minimal executable host/fake-provider proof, with independent M01 preparation and honest device blockers.

Next: use AGENT_PROMPT.md in an implementation session. Prepare reviewed CI in M03 before re-enabling Actions; do not recreate the repo or weaken the owner-review rules to begin work.

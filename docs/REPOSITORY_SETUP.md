# Public repository setup and verification

Configured for `OptimumAF/LocalLore` on 2026-10-22. Dated settings and access evidence is in [historical archive #2](https://github.com/OptimumAF/LocalLore/issues/2), with accepted bootstrap scope in [M00 #4](https://github.com/OptimumAF/LocalLore/issues/4). The procedure below documents the setup and future verification; do not rerun repository creation against the existing project. Future verification belongs on the assigned ticket.

## Publication

Create a new public repository in the owner's personal namespace, not an employer account or unrelated project. Check for an existing name first; a previous not-found response does not reserve the name. Publish only the reviewed documentation tree. No application code, signing material, model weights, personal user profile, private stories, or hidden credentials belong in this bootstrap.

Use the working name LocalLore and a description such as: 'Fully local, open-source interactive storytelling with persistent world state, character memory, and meaningful consequences.' The name can be reconsidered; trademark clearance has not been performed.

The downloadable starter package includes an optional `publish_github.py` helper outside the proposed repository tree. It requires owner-authenticated GitHub CLI access. It checks the intended account, file manifest, and repository nonexistence; creates a new public repo; uploads the documents; attempts the listed controls; and records read-back results. It must not overwrite an existing repository, invite collaborators, or silently claim success after a failed setting. The helper is a bootstrap convenience, not application code or evidence that publishing already occurred.

## Control model

Only `@OptimumAF` is the initial human owner/decision-maker. Do not add collaborators or release-capable bots automatically. Review existing account-wide integrations and access separately; a new repository can fall within an already installed integration's scope. Do not claim that 'no collaborators added' proves no app has access.

The CODEOWNERS file routes review ownership. It is not a permission grant and does not enforce review by itself. GitHub rules must be configured and verified. Official references: [S11–S12](REFERENCES.md).

## Intended settings

| Setting | Intended bootstrap state | Verification |
|---|---|---|
| Visibility | Public | Repository metadata says public/not private |
| Owner | OptimumAF | Exact owner login and ID match authenticated intended account |
| Default branch | main | Metadata and branch head |
| License | Apache-2.0 | File content; GitHub recognition may lag |
| Issues | Enabled | Repository metadata |
| Discussions | Optional enable for proposals | Record actual result, not assumed |
| Wiki | Disabled initially | Repository metadata; docs stay reviewable |
| Auto-merge | Disabled | Repository metadata |
| Merge strategy | Squash enabled; other modes optional/restricted | Record actual setting |
| Branch deletion after merge | Enabled | Repository metadata |
| CODEOWNERS | All paths owned by OptimumAF | Committed file |
| Main rules | PR required, owner code review, no force push/deletion | Active ruleset read-back |
| Owner self-PRs | Explicit owner-only PR-context bypass if supported | Do not require the owner to approve their own PR |
| CI at docs bootstrap | Actions disabled until reviewed workflows are introduced | Actions permission read-back |
| Private vulnerability reporting | Enabled and verified if available | Security setting read-back / visible reporting action |
| Collaborators | No new collaborators invited | Audit all current collaborators and pending invitations |
| Conduct reporting | GitHub abuse tools/Support for sensitive abuse reports; owner threads for nonsensitive concerns | Documented in CODE_OF_CONDUCT and ADR-0002; no dedicated owner inbox is claimed |

Do not configure nonexistent required status checks. Add checks only after real workflows run and their exact names are known. Re-enable Actions deliberately in M03 with read-only defaults, reviewed/pinned actions, and a safe fork policy. Never give untrusted fork PRs access to secrets or privileged runners.

## Owner-only review and bypass nuance

A sole code owner cannot use self-approval to satisfy an ordinary required review on their own PR. Configure a narrowly scoped bypass for the owner in pull-request context when supported, preserving an auditable PR while allowing solo development. Do not give all contributors bypass authority or use an unconditional bypass for every integration. Owner administration rights remain; the purpose is to make the ordinary workflow explicit, not pretend an administrator can never change settings.

A ruleset file in Git is documentation until actually submitted to GitHub and read back. If a token or plan cannot apply a setting, record the exact failure and leave it pending; never silently downgrade it or declare governance enforced.

## Verification checklist

- [x] Repository exists, is public, and belongs to the intended owner.
- [x] Default branch and exact bootstrap commit are recorded.
- [x] Remote file tree/hashes match the reviewed starter package.
- [x] License and governance documents are present.
- [x] CODEOWNERS and active rules agree; owner self-PR workflow is understood.
- [x] Actual collaborators, pending invitations, and integration access are audited.
- [x] Auto-merge is off; Actions state and permissions are recorded.
- [x] Private vulnerability reporting is enabled (no fabricated report was submitted); private conduct-reporting route is documented (ADR-0002).
- [x] Setup evidence is preserved in archive #2 and accepted M00 tasks are recorded in ticket #4.

## Manual recovery

If repository creation succeeds but later upload/settings fail, inspect the remote repository and the helper's receipt before retrying anything. Do not delete the repo, recreate it, force-push, or run a broad overwrite automatically. An owner can resume the specific missing step with the recorded IDs/commit, or submit a follow-up PR. The helper deliberately refuses a pre-existing repository on a fresh run.

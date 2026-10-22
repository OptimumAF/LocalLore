# Project status

Updated 2026-10-22 after public repository publication.

## Verified publication

The public repository is [OptimumAF/LocalLore](https://github.com/OptimumAF/LocalLore), owned by Avery Fernandez (`@OptimumAF`, account ID 88298311). Repository ID: 1430285879. The default branch is `main`; GitHub recognizes the license as Apache-2.0.

All 35 starter documentation/configuration files were published in commit `0d095babe5ad661f829dc6ebe10951bad0e00783`, tree `4af0338494666b7f253457c1e8541a179d6f6aea`. Every remote path and Git blob hash was compared with the original package and matched exactly. Subsequent publication-status edits are intentional changes to those starter documents.

Read-back verified issues enabled, wiki disabled, automatic merging disabled, squash merging available, and automatic deletion of merged head branches enabled. Actions settings visibly confirmed that Actions are disabled for the documentation bootstrap. Their default token is read-only, and Actions approval of pull requests is off.

## Verified controls and reporting

Active ruleset [Owner-reviewed main](https://github.com/OptimumAF/LocalLore/rules/25677641), ID 25677641, targets the default branch (`main`). API read-back verified required pull requests, one approval, code-owner review, dismissal of stale approvals, resolved review conversations, and blocked force pushes/deletions. The only bypass actor is user OptimumAF (88298311), limited to pull requests. No app or repository role has bypass. GitHub's default extra approval for unattributed Copilot changes remains enabled. No nonexistent CI status check is required.

The settings page confirmed “Ruleset created” and “Applies to 1 target: main.” The connector does not support the effective-branch-rules endpoint, so applicability was verified in the saved ruleset UI as well as its API conditions. The setup-documentation PR exercises the owner self-PR workflow without direct pushes to `main`.

The access page showed zero collaborators and no invitations. Installed integrations visible for this repository: AWS Amplify (us-east-2), AWS Connector for GitHub, ChatGPT Codex Connector, and GitGuardian. These pre-existing installations were inventoried, not granted or removed; account-wide scopes were not changed. They do not have ruleset bypass. Future changes to integration access require an owner decision.

Private vulnerability reporting is enabled, confirmed by the saved security settings and the “Disable private vulnerability reporting” control. Dependency graph and Dependabot alerts are enabled. Secret protection and push protection were already enabled and were retained. No paid AI scanning, automatic fix agent, application release, or collaborator grant was introduced. Actions remains disabled until reviewed CI is deliberately introduced in M03.

For sensitive conduct concerns, the bootstrap reporting route is GitHub's abuse-reporting tools/Support, documented in `CODE_OF_CONDUCT.md` and ADR-0002. This is not a dedicated owner inbox. Public issues must omit sensitive details, and vulnerability reports are reserved for security issues.

## Initial decisions and remaining product questions

Apache-2.0, founder-controlled upstream governance, Android-first execution, Kotlin/Compose, Rust, SQLite, and measurement before backend selection are accepted as initial planning defaults under the owner's setup delegation. The technical choices remain revisable with evidence. Actual device/RAM, model/runtime, supported profile, latency/quality targets, minimum OS, and distribution details remain implementation/evaluation questions; none is represented as measured.

## Not implemented

This is documentation only. No application code, runtime integration, Android build, real-device benchmark, automated application test, release, or security audit is complete. The exact phone and physical RAM are unconfirmed. Android-first, Kotlin/Compose, Rust, SQLite, and model candidates remain proposed defaults.

## Progress and next work

`../DEVELOPMENT_PLAN.md` is the authoritative checklist; `WORK_LOG.md` records evidence. M00 bootstrap tasks are complete with configuration evidence; application milestones remain unchecked. After repository setup and a separate implementation assignment, begin M01 device/runtime feasibility and M02 domain contracts. Unavailable hardware leaves physical-device gates blocked.

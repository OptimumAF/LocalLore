# Contributing

Thank you for helping build LocalLore. Check the [roadmap and status ticket #3](https://github.com/OptimumAF/LocalLore/issues/3) and accepted PRs for current capabilities and verified development instructions. Do not interpret an open ticket as implemented functionality.

## Pick a small, useful change

Read the README, governance policy, agent instructions, [ticket workflow](docs/ISSUE_WORKFLOW.md), and relevant milestone/task ticket including recent claims. For substantial work, open a proposal before building a large implementation. Reference the ticket and stable Mxx.yy task ID, and describe scope, acceptance criteria, and affected interfaces. Claim task IDs, branch, and owned paths in a ticket comment before editing; avoid overlapping ownership. Community reviews and reproducible device measurements are useful even without code contributions.

Use a fork and a feature branch. Do not request administrator access to make a normal contribution. No contributor gets merge or release rights automatically. The owner makes final upstream decisions.

## Pull-request expectations

Explain the problem and solution, reference ticket numbers and stable task IDs, include tests and exact results, and describe risks and limitations. Post verification and a PR link on each affected ticket; update user-facing docs and migration notes where needed. Use `Refs #N (Mxx.yy)` for partial milestone work so the PR does not auto-close the whole milestone. A screenshot is useful for UI work but not proof of persistence or inference correctness. Clearly distinguish fake-provider, emulator, desktop, and physical-device results.

Keep changes narrowly scoped. Shared event schemas, migrations, runtime APIs, and security promises need design review before parallel implementations depend on them. Do not add a cloud dependency, hosted telemetry, heavyweight framework, or model weight file merely to make a demo easier.

## Licensing and provenance

Only submit material you have the right to contribute. First-party contributions are offered under Apache-2.0 unless explicitly agreed otherwise. Contributors retain their copyright; there is no copyright-assignment requirement or CLA at bootstrap. Identify copied/adapted material and preserve required notices. Third-party assets, weights, and datasets need independent license review. Do not copy proprietary prompts, paid stories, copyrighted character packs without permission, or another product's code.

AI assistance is allowed. You are responsible for understanding, testing, licensing, and maintaining your submission. State material AI assistance in the PR and never use an AI review score as a substitute for evidence or human approval. Do not upload real player data to a hosted coding or evaluation service.

## Privacy-safe reporting

Use synthetic minimal examples by default. Never attach private saves, raw personal chats, model access tokens, device serials, signing keys, or full diagnostic archives. A safe benchmark report records the device model and memory tier without unique identifiers. Follow `SECURITY.md` for vulnerabilities; do not file exploit details publicly when private reporting is available.

## Definition of ready for owner review

The task is scoped; acceptance criteria are addressed; relevant tests were run; remaining gaps are stated; affected docs and ticket evidence are updated; dependency/license impacts are disclosed; and the branch does not include unrelated generated files. Passing checks permits review, not automatic merge. Do not check a ticket task as done until accepted and verified; close a milestone only after its full exit gate is accepted.

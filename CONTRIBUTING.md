# Contributing

Thank you for helping build LocalLore. The repository is initially documentation-only. There is no supported build command or release yet. Do not interpret the roadmap as implemented functionality.

## Pick a small, useful change

Read the README, governance policy, agent instructions, and the relevant development-plan task. For substantial work, open a proposal before building a large implementation. Reference a stable task ID and describe scope, acceptance criteria, and affected interfaces. Community reviews and reproducible device measurements are useful even without code contributions.

Use a fork and a feature branch. Do not request administrator access to make a normal contribution. No contributor gets merge or release rights automatically. The owner makes final upstream decisions.

## Pull-request expectations

Explain the problem and solution, reference the task/issue, include tests and exact results, and describe risks and limitations. Update the relevant plan entry, work log, user-facing docs, and migration notes. A screenshot is useful for UI work but not proof of persistence or inference correctness. Clearly distinguish fake-provider, emulator, desktop, and physical-device results.

Keep changes narrowly scoped. Shared event schemas, migrations, runtime APIs, and security promises need design review before parallel implementations depend on them. Do not add a cloud dependency, hosted telemetry, heavyweight framework, or model weight file merely to make a demo easier.

## Licensing and provenance

Only submit material you have the right to contribute. First-party contributions are offered under Apache-2.0 unless explicitly agreed otherwise. Contributors retain their copyright; there is no copyright-assignment requirement or CLA at bootstrap. Identify copied/adapted material and preserve required notices. Third-party assets, weights, and datasets need independent license review. Do not copy proprietary prompts, paid stories, copyrighted character packs without permission, or another product's code.

AI assistance is allowed. You are responsible for understanding, testing, licensing, and maintaining your submission. State material AI assistance in the PR and never use an AI review score as a substitute for evidence or human approval. Do not upload real player data to a hosted coding or evaluation service.

## Privacy-safe reporting

Use synthetic minimal examples by default. Never attach private saves, raw personal chats, model access tokens, device serials, signing keys, or full diagnostic archives. A safe benchmark report records the device model and memory tier without unique identifiers. Follow `SECURITY.md` for vulnerabilities; do not file exploit details publicly when private reporting is available.

## Definition of ready for owner review

The task is scoped; acceptance criteria are addressed; relevant tests were run; remaining gaps are stated; docs and plan are updated; dependency/license impacts are disclosed; and the branch does not include unrelated generated files. Passing checks permits review, not automatic merge. Do not check a task as done on the authoritative plan until accepted and verified.

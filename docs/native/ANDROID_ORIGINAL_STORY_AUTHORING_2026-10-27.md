# Original story authoring — implementation and verification

M09.02/M09.06 with supporting M10.02/M10.03, in progress. This work is stacked
on open/unmerged PR #224 at `b6989a38`; no merge is authorized. Full task
checkboxes remain unchanged. [Contract](ORIGINAL_STORY_AUTHORING_CONTRACT_V1.md)
and [ADR](../adr/0013-original-story-authoring.md) describe the frozen boundary.

The implementation adds actual original premise/cast inference, bounded native
world validation, editable typed author review and explicit atomic creation.
It retains bundled starter choices. World truth, entitled character knowledge,
private beliefs and initial provenance stay distinct; Kotlin does not become
a second world engine. Native IDs/mechanics and complete reviewed content are
engine-owned. A process-local job cannot edit an existing story or create after
cancel/owner close. Replay/recovery never calls inference.

Independent worktrees own the core module/prompts, Android flow/ownership and
original adversaries. Root owns shared Seed/Host/workspace integration, exact
recovery, worker provenance and the fixed verification phase. Original Ashglass
and Copper fixtures differ in actual topology/cast/entities/truth/beliefs;
they are synthetic samples, not model quality evidence.

## Evidence so far

| Actual check | Scope/result |
|---|---|
| Initial core check | Passed18,435ms,1,973 unchanged tracked inputs; earlier provenance shape |
| Initial full core run | Failed one stale generated-schema assertion after71 unit passes; remaining targets not claimed |
| Schema regeneration | Passed17,744ms; exactly host-v1.schema.json/host.generated.ts changed |
| Independent original-world target | All12 passed;7,264ms,1,978 unchanged inputs; before full configuration refinement |
| New Host/SQLite target | All7 passed;30,318ms owner/0.60s runner,1,980 unchanged inputs |
| Android Rust crate/all features |108 passed,0 failed/ignored;46,613ms,1,980 unchanged inputs |

All listed successful owners retain known cleanup/capture and zero owner
stderr. They do not substitute for future checks after later source edits.
Original failed attempts remain preserved privately on C:.

Review identifies a real recovery design race: looking up a completed authored
seed and then calling insert-or-retry could resurrect it after another Store
deleted it. Recovery is changed to read-only Engine load/presence/full-seed
checks. A new fault-injection test uses an actual second SQLite owner deleting
exactly between lookup and attachment; no reinsert call occurs and the story
remains deleted. This is a source-identified race and a passing corrected
regression, without claiming an executed historical resurrection reproduction.

Other actual Store checks cover no canon before explicit Create, distinct
worlds, invalid/stale/cancelled review, configuration invalidation, provider
failure, worker release, accepted turn preservation, missing-job recovery after
restart, and archive import/recovery without another inference call.

Stored origin now binds all11 validated PlayProfile fields, not merely a
profile name. The author recipe fixes its own role-specific budget. The worker
LF source hash becomes
`1e66e0fbcc30534771f0734d03b22612eb67b1287b3d1fa353d13b7d5e126e67`
(25889 bytes), bound in the candidate manifest and Gradle guard. Model/runtime
pins are unchanged; earlier model results retain their earlier source hashes.
No new dependency, download, device setting or model transfer occurs.

The existing worker retains its finite-regex path and exact JSON-schema path
for non-finite schemas. Current official [constrained-decoding documentation](https://github.com/google-ai-edge/LiteRT-LM/blob/main/docs/api/cpp/constrained-decoding.md)
describes JSON-schema constraints; this is API context, not proof that the
selected model completes the new author schema. Pinned-source web retrieval
was unavailable during this check. Actual compilation/public SDK value-object
tests and a future real author inference run must retain separate attribution.
Thinking and speculative decoding remain disabled in the current CPU worker.

## Pending current integrated checks

Android checkpoints are integrated, including8 device methods and16 new JVM
cases. Compilation, lints, artifact audits, broader Rust/Python/frontend checks
and fresh native/original-story emulator execution remain pending. No Android
test success or real-model compatibility/quality/performance is inferred from
source presence. Physical/ARM64, semantic narrative quality, accessibility,
external process death and joined callback drain remain separate gates.

Source and reports are committed/pushed during implementation. Private evidence
and recoveries stay on C:; model weights, saves and private diagnostics stay out
of GitHub. No unrelated emulator stop, server lifecycle operation, system
settings change, release, permission administration or merge is performed.

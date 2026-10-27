# Original story authoring — implementation and verification

M09.02/M09.06 with supporting M10.02/M10.03, in progress. This work is stacked
on open/unmerged PR #224 at `b6989a38`; no merge is authorized. Full task
checkboxes remain unchanged. [Contract](ORIGINAL_STORY_AUTHORING_CONTRACT_V1.md)
and [ADR](../adr/0013-original-story-authoring.md) describe the frozen boundary.

The implementation adds a generation path for original premises/casts, bounded native
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
| Full Rust checks at `c4a2da9c` | Core456/4 ignored, storage239/6 ignored, workspace170/1 ignored, Android108/0 ignored;0 failures |
| Strict Clippy at `c4a2da9c` | Passed with warnings denied;27,398ms |
| Python at `c4a2da9c` |1,505 passed,0 failures/errors/skips;178,759ms owner |
| Frontend at `c4a2da9c` | Verification/format passed;30,770ms |
| Input-process build at `c4a2da9c` |305 JVM tests/35 suites,0 failures/errors/skips;11 APK audits;2 lints with3 warnings/0 errors |
| New original-story driver adversaries |12 synthetic cases included in the Python suite; not device proof |

All listed successful owners retain known cleanup/capture and zero owner
stderr. They do not substitute for future checks after later source edits.
Original failed attempts remain preserved privately on C:.

The early full core schema mismatch is repaired by regeneration. A later full
core attempt actually fails7 of12 author adversaries: their synthetic director
budget512 violates the existing PlayProfile350 cap. The fixture becomes320;
the provenance canary/hash oracle and production validation remain unchanged.
An initial strict lint run fails one needless return; the correction passes.

Rapid editor callbacks are also actually reproduced red:12 focused JVM tests,
2 ComparisonFailures. The first epoch/diff correction passes15 tests. Review
then identifies an explicit edit returning to the originally rendered value
that equality inference still loses. Explicit field/choice/toggle intents
replace that inference; the complete18-controller cohort passes in the305-test
build. Structural operations retire epochs, and action/review identity remains
exact. The second counterexample is source-identified, not an executed historical
red. Review also verifies the current controller already synchronizes reviewed
cast names from edited characters; no rename-refusal defect is claimed.

The first separate LiteRT build compiles against the pinned public SDK and runs
569 JVM tests, with2 failures: exact trace-vocabulary assertions still expect
Director/Narrator without the newly implemented Author tag. Those two closed
expectations are corrected to include Author; counters, wire versions, bounds
and production code are unchanged. That failed cohort remains preserved.
Its subsequent lint/packaging/audits are not claimed as completed. A fresh final
source freeze and separate corrected LiteRT qualification are pending.

The corrected `dc8c8a42` cohort passes all569 LiteRT JVM tests/55 suites, lint
with10 warnings/0 errors, dependency/analyzer audits and the candidate APK
audit. It also passes the fresh native10 phase, followed by its exact requested
owned guest closure and7 metadata copies to C: with0 mismatch. A subsequently
run repository formatting gate fails solely the new Rust adversary test file.
Root had omitted that gate earlier. Rustfmt1.93.1 formats the file without
changing assertions. The successful native/host/SDK cohort remains attributed
to its actual pre-format source; a new fresh verification cohort is required.

Broader CI benchmark checks then expose an existing Windows test error:
`test_output_refuses_existing_directory_and_missing_ancestor` expects an
existing C:-TEMP output to reach mkdir, but the unchanged cache-build policy
correctly refuses every non-D: output first. Root retains that failed34-case
attempt and fixes only the test: the C: refusal is exact, and a mocked existing
D: candidate must raise FileExistsError before any owner bytes are written.
No D: filesystem operation or production guard change is introduced.

The final `2ef0f5f4` host cohort passes976 Rust tests (including3 standalone
native-linker cases),11 ignored,1,716 Python tests,305 app JVM cases and569
LiteRT JVM cases. Formatting, default/all-feature Clippy, fixture-output checks,
lints and audits pass. Its native10 phase also passes. Original-story8 actually
fails: wire3/dialog2 pass, while all3 MainActivity cases fail. The first times out
after Create; subsequent startup reports recovery required. No end-to-end
original-story success is claimed for that source. Both exact owned guests are
requested-stopped after known client closure;7 metadata files per guest are
copied to C: with0 mismatch. The separate resource postflight passes with the
existing server unchanged; that does not turn the failed app phase into a pass.

The failure is a production gateway assumption: native original worlds assign
player IDs such as `a-{prefix}-0`, while DurableGateway requires literal
`player` in the fixed native player snapshot. Post-create inspection fails and
later startup hits the same assumption. The correction accepts a bounded native
observer ID, binds it to the attached session/scope and retains response scope/
revision checks. Semantic `player` lens labels in record/fork contracts remain
unchanged. Three focused binding JVM cases actually pass on `f723f2db`
(31,272ms owner,1,997 unchanged inputs); full integration remains pending.

Independent source review then identifies aliasing/overlap cases at the abstract
transport boundary, without claiming executed JNI failures. A fresh attachment
token now fences attach/detach/close and immutable captured scope values. Final
publication atomically rechecks the current observer binding under the same
metadata lock; no native call or suspension occurs under that lock. The existing
Wire method gains deferred same-object/same-session reattachment and overlapping
conflicting-observer cases; the8-method roster and15-second UI wait are unchanged.
A fresh full build/host and native/original emulator cohort must verify this fix.

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

A further source review finds successful recovery did not consume a matching
live review. The corrected eighth Store case uses two actual Hosts/SQLite:
recovery consumes that exact job, binds creation ID/hash before lookup, refuses
existing same-origin and absent alternate targets, and retains the binding after
a refused later review. Exact retries remain read-only; a foreign-job recovery
does not consume an unrelated draft. All8 pass (16,069ms owner/0.78s runner).

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

Android has8 fixed device methods. The completed input-process build above
cross-compiles JNI for x86_64/ARM64 and passes host/JVM/lint/artifact checks;
cross-compilation is not ARM64 execution. The two LiteRT test-only corrections
require a new frozen build/check cohort. Embedded author prompt/schema files
are now included in the host driver's compiled source map and independently
hash-tested. Fresh native10/original-story8 emulator execution remains pending.
No real-model compatibility/quality/performance is inferred from SDK value
objects, injected resources or scripted plumbing. Physical/ARM64, semantic narrative quality, accessibility,
external process death and joined callback drain remain separate gates.

Source and reports are committed/pushed during implementation. Private evidence
and recoveries stay on C:; model weights, saves and private diagnostics stay out
of GitHub. No unrelated emulator stop, server lifecycle operation, system
settings change, release, permission administration or merge is performed.

# Native generation, verified memory and explicit maintenance integration

Partial #11 M07.01/.03/.04 and #29 production-consumer prerequisite. Accepted base is schema4 `b90ddc9c0ed955c034a6c1f9e331caf3323e4e9a` (PR #114). This report records coordinator integration and actual failures as well as successes. It does not accept the whole memory milestone, desktop evaluation gate or Android device qualification.

## Integrated boundaries

- `Host::generation_snapshot` obtains the actual Engine and opaque coverage proof together through the existing Repository/Store read transaction. It fixes the observer to the selected player, compares full seed, original accepted receipt prefix and immutable branch lineage, and neither admits maintenance nor changes inspection privileges. Missing cache is honest raw fallback. Native override panic is caught inside the Host lock; cancellation is panic-safe and latched.
- Production free-text `Host::prepare` transfers that same Engine/proof pair to Play2.4 outside the owner lock and SQLite transaction. Play calls the existing verified compiler, which rechecks the actual proof against its Engine. Count-only context provenance in new receipts is not a proof, permission source, authenticated performance measurement or model instruction.
- Historical Play2.1/.2/.3 receipt encodings remain historical/retry inputs. New generation uses2.4. Frozen compact-byte goldens and original-source2.3 fixture evidence are documented in the consumer report; no new model-quality result is inferred from scripted roles.
- Native `Host::memory_maintenance` exposes explicit Status/Admit/one bounded Step/Cancel/Prune through the existing schema4 job owner. It fixes player selection, refuses mutations while selected-scope turns are active, returns a bounded count/status DTO, and adds no background scheduler, competing cache or automatic retry after an unknown Step acknowledgement. See `M07_MEMORY_MAINTENANCE_2026-10-23.md` for author-attributed22 focused tests and retained initial failures. Desktop/Android maintenance UI wiring is a subsequent task.
- Native `AcceptedHistoryBasis` is opaque, non-Serde and bounded: SHA-256 streams a domain tag, scope/boundary, complete seed, immutable lineage and exact original receipts with a64MiB serialization ceiling. A Ready turn stores the small token rather than another full history. It grants no observer or mutation authority and is absent from wire, schema, archives, prompts and receipt bytes.
- Bound Store admission/status/commit/terminal cleanup compare that basis with actual replay inside their existing read or IMMEDIATE transaction. Admission/new acceptance require the Request's exact scope and expected revision; reads/cleanup can guard a historical request with the stronger full selected prefix. A shorter basis never protects a later request. A source mismatch returns Stale before modifying even an identically recreated draft. Exact accepted-prefix appends and recorded winning requests retain existing idempotency semantics. Existing public unbound Store methods remain explicit legacy interfaces; the Host uses bound methods. Legacy Persistence implementations default to Unsupported for bound methods and cannot silently claim atomic support.

Claims precede edits: #11 comments6374566054/6374662654/6374747036/6374920217/6375185136/6375302720; #29 comment6375253545. Existing Core engine/Host, Store turns and Repository integration are coordinator-owned. Android fork and desktop fork application files have separate owners and are excluded from these edits.

## Frozen review findings and actual executions

Independent reviewer `desktop_runtime_profile` froze two public Host/Repository/SQLite regressions at `959e3af4e40406569be4e88611b98c28cc900be7`, before correction. See `M07_GENERATION_CONSUMER_REVIEW_2026-10-23.md`. Both use actual accepted typed receipts, validated public archive deletion/import and `Store::begin_turn`; there is no canonical SQL mutation or forged accepted receipt. SourceA and replacementB share seed, IDs, head and projection but have different original accepted receipt identities. The replacement owner recreates the original Request as its own new Draft.

| Source and invocation | Actual result |
| --- | --- |
| Frozen pre-fix `a8ad7a9`, unchanged2 review tests | **0 passed /2 failed**, build10.96s/test.16s. In-flight old generation incorrectly became Ready; old Ready incorrectly committed and advanced replacement head1→2. |
| First attempted fixed invocation, shared target | **0/2**, .20s without compiling corrected packages. This invocation reused the previous checkout's artifact; it is retained as a setup failure and does not measure corrected source. |
| Corrected `c7c77a8`, same2 oracles, actual recompilation of Core/Store/Repository | **2 passed /0 failed /0 ignored**, build11.61s/test.15s. Both refuse Stale, preserve replacement canonical receipts/projection and its new Draft, and drain the worker. |

For the actual corrected run only the coordinator's own three package inputs and unchanged review-test input received fresh filesystem timestamps, forcing Cargo to rebuild current code. No content, oracle or accepted event was changed. This is recorded because cross-worktree targets can otherwise reuse a newer artifact from the previous checkout. Future integration qualification must verify compilation/source freshness rather than assume a fast result executed current code.

Private, gitignored evidence directory: task-local `memory-jobs-artifacts`. Retained logs: `generation-consumer-source-red.log`, `generation-consumer-source-fixed.log` (stale-artifact setup failure), `generation-consumer-source-fixed-rebuilt.log`. No private story/model prompt is published by this report; the test output is synthetic.

Reviewer then froze two additional pre-fix admission/status vectors at `a30ca2909de6d7dd49f8b162f61be67206805d59`: replacement before a fresh Submit, and replacement of a queued source followed by status/prepare. Frozen pre-correction checkout is `bf00d9a`. Corrective source `55c8641` adds bound draft admission, retains original Turn basis at begin-work and bounds cached status/cleanup. **Those additional tests and the final integrated suites are pending execution at this report revision.** The desktop fork owner currently holds the sequential compiler/native-render slot.

Earlier coordinator forwarding evidence is retained separately: actual coherent raw/verified Store-to-production-prepare tests, selected-player isolation after NPC inspection, source advance0roles, transient read errors retaining the original queued key, terminal categories and override panic health. The first test compilation failed because `GenerationRequest` is not Serialize; inspection was corrected to the actual structured input. The first NPC assertion looked only at the first64-row page; the same private NPC fact was then queried explicitly. The panic health test initially used an unsupported snapshot wire operation; its health probe was corrected to existing inspect. Six focused forwarding tests passed at `043d4da`; these historical results are not final55c qualification.

## Reproduction and remaining checks

### Default Core/workspace qualification through977b8ec

Production correction is `b4960b5` after independent source review of the stronger-prefix design at `f7c4663`. Implicit refresh requires the actual Engine to extend the selected complete seed/receipt prefix/lineage; ordinary external appends are accepted. Submit refreshes through that guard before capturing a new request basis. Cached/uncached status rereads with the full selected basis. Ready commit first checks containment of its original private generation basis; if the selected source has advanced, it terminalizes Stale through full-prefix bound cleanup rather than use a shorter candidate basis for a stale write. Worker terminal cleanup likewise uses its stronger refreshed full prefix, with no weaker fallback on a failed capture. Existing-session Resume uses the guarded refresh; explicit Open or a new session selects an actual source separately.

Actual unchanged frozen regressions: **6/6 Host source-replacement cases and10/10 direct Store cases PASS**, including historical draft cancellation after a legitimate append and unchanged replacement-owner Draft after refusal. All earlier pre-fix checkpoints remain separate. Additional actual REDs: admission `bf00d9a`2PASS/2FAIL; uncached refresh `41e2750`4PASS/1FAIL; historical Cancel `e8d7e54`5PASS/1FAIL (returned Stale but had changed the replacement draft to Cancelled). A mistyped initial refresh filter executed0 cases and is not counted.

Default coverage is a **multi-invocation aggregate, not one uninterrupted all-green run**:232 Core cases PASS with2 explicitly ignored historical fixture-capture helpers, plus all91 workspace cases PASS after the final affected-test rerun. Commands were `cargo test -p locallore -p locallore-workspace --locked --offline --jobs 1 --target-dir <task-owned-target>`, then `cargo test -p locallore-workspace --locked --offline --jobs 1 --no-fail-fast --target-dir <task-owned-target>`, and the final affected `--test turn_trace_host` rerun. Earlier successful executables are not repeated without a new production change. Portable Core-only `--lib` separately passed6 cases; it is not native Host coverage.

The broad runs retained and corrected these failures without changing their original assertions:

- Synthetic snapshot ErrorPort2-case and maintenance pending Port1-case setup failures: explicitly implement bound native test ports, retaining source/request assertions and original fixed outcomes. Legacy production defaults remain Unsupported.
- Ownership review11PASS/4FAIL:3 old fault-port setups needed actual Store bound methods while preserving lost-ack/cancel/status injection;1 real regression refused a valid newly appended source revision before refreshing. The guarded pre-Submit refresh restores that behavior; all15 original ownership tests now pass alongside replacement-source refusals.
- Snapshot host5PASS/1SETUPFAIL: Windows parallel test fixtures collided on process+clock timestamp (`AlreadyExists183`). Only an atomic process-local suffix was added; all6 snapshot tests pass unchanged.
- Final trace8PASS/1SETUPFAIL: its old LostAck test port needed bound actual Store calls with the same post-commit lost reply and failed-lookup ordering. The final unchanged9-case trace suite passes (1.13s compile/.36s cases).

Other current workspace checks include actual production raw/verified consumer6, explicit maintenance6, original source-port review5, native fork7, canonical inspection/export and durable ownership cases. Logs retain each failure and its source, notably `generation-admission-red.log`, `generation-refresh-red.log` (zero-filter setup), `generation-refresh-red-all.log`, `generation-historical-cancel-red.log`, `generation-final-focused.log`, `generation-final-core-workspace.log`, `generation-final-core-workspace-fixed.log`, `generation-final-core-workspace-refresh-fixed.log`, `generation-final-workspace-all.log` and `generation-final-trace-fixed.log`.

Use Rust/Cargo1.93.1, locked offline dependencies, ordinary SQLite flags (no capacity experiment flags), one compiler process, debug info disabled and incremental disabled. Representative exact commands, with a distinct task-owned target or verified fresh current-source inputs:

```powershell
$env:CARGO_PROFILE_DEV_DEBUG='0'
$env:CARGO_PROFILE_TEST_DEBUG='0'
$env:CARGO_INCREMENTAL='0'
$env:CARGO_BUILD_JOBS='1'
cargo test -p locallore-workspace --test generation_consumer_review --locked --offline --jobs 1 --target-dir <task-owned-target>
```

Pending: Store/default and feature qualification, strict portable/native builds, frontend/native/Android compatibility after integration, a focused PR and exact-tree merge verification. Actual scripted-role tests are engine/native-library execution, not model inference, app WebView execution or Android JNI/device execution. Existing native render and model evidence belongs to its recorded source and cannot substitute for current integration checks.

No desktop control, injected input, window activation, desktop capture, device/ADB operation, settings change, hosted inference, download or protected-thread action is part of this verification. The owner has separately authorized existing-account merge bypass; it does not fabricate an independent human approval or weaken a repository setting. Broad task boxes remain unchecked.

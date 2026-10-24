# Compiler2 construction policies: source freeze — 2026-10-23

Refs #11 M07.01, #12 M08.03 consumer prerequisite, #29 D07.03/.04/.05.
Status `in_review`: the original source-only packet is preserved below;
subsequent actual scoped qualification is recorded in the addendum.
This is not policy execution in the evaluation runner, a model comparison,
compiler qualification, or user-facing Domain-2 generation support.

## Binding, ownership and immutable sequence

Separate `impl/m08-context-policy` / `source-context-policy` from
`1c0b0909c44f712002f258af71a30fba6561bf73` (same relevant compiler production as
`44fce7947f277b4e21de6750f20426027c06ca3b`). Claims #11 6377168948,
#12 6377169173, #29 6377169387. Exact existing ownership:
`crates/locallore/src/context_compiler.rs` and
`crates/locallore/src/context_compiler/verified.rs`; NEW
`context_compiler/policy.rs`, `tests/m08_context_policy.rs`, and this report.
No query/Engine/author/Host/Store/Play/lib/contracts/schema/native/platform/UI
or existing-test file changed. Root owns all those integrations.

- `9910acd`: twelve NEW actual-Core test oracles, before production changes.
- `60d2c00`: Root-approved explicit pre-execution oracle correction. The initial
  NPC test forbade `ACTUAL_INPUT` even though its fixture speaks exactly those
  words to Mira. Heard literal Said text is a legitimate witnessed event. Only
  that blanket text exclusion was removed; positive `ACTUAL_INPUT_0` witnessed
  speech was added. NPC unit input/narration fields must still be absent, and
  private self-speech/player secret/private B/reason exclusions are unchanged.
  The original `9910acd` is preserved, never compiled/run. This is neither an
  observed production RED nor a relaxation allowing raw player message fields.
- `65f027618fb6232bc0b817b0db45ae2f422ea181`: shared compiler2 source.
- `0e2331e`: scoped visitor-argument rationale, no behavior change.
- `650cf6d`: unit-count interpretation comment, no behavior change.

Frozen corrected test SHA-256:
`7eb45f0d9f6efdd0076ea81431257d039a672bfcc0a15d4c2b853ed74b313469`.
All tests remain unexecuted. Root's separate actual 32 Core/Query2 checks at the
base are attributed historical prerequisite evidence, not this compiler run.

## Exact native surface

`COMPILER_VERSION=1`, old CompileRequest/ContextPackage/MemoryCompilation and old
public return types remain. Add `POLICY_COMPILER_VERSION=2` and the closed
`ContextPolicy::{StateRecentTranscriptV1,StateRelevantMemoryV1}` labels
`state_recent_transcript_v1` / `state_relevant_memory_v1`.

```rust
pub fn compile_policy_cancelled(
    engine: &Engine,
    request: &CompileRequest, // version 2
    policy: ContextPolicy,
    proof: Option<&VerifiedCoverage>,
    cancel: &dyn Fn() -> bool,
) -> Result<PolicyCompilation, CompileError>;

pub struct PolicyCompilation {
    pub policy: ContextPolicy,
    pub compilation: MemoryCompilation,
    pub construction: ConstructionDiagnostics,
}
pub struct ConstructionDiagnostics {
    pub eligible_transcript_units: usize,
    pub overlap_transcript_units: usize,
    pub selected_transcript_units: usize,
}
```

Root explicitly approved this new return-wrapper refinement to the earlier
MemoryCompilation sketch. Old return shape/serde is not changed. Policy and
constructed-unit diagnostics are distinct from actual coverage representation.
Relevant constructs no transcript units: zero there means not constructed,
never "no history exists". Counts confer no proof, availability or quality.

New Serialize-only `TranscriptUnit` contains original_scope, turn, actual
`Vec<ActorEventV2>`, optional original_input and optional narration (None fields
omitted). New Payload::TranscriptUnit, Kind::Transcript/Kind::KnownAsObserved,
Reason::KnownAsObserved/Reason::AlreadySelected are additive. ContextPackage2
keeps the existing outer shape; ContextPackage1 emits only unchanged old arms.
No accepted record/plan/canonical authority implements a new wire parser here.

## One actual pipeline and source/privacy rules

Both entries call ONE `compile_inner`, parameterized by a private legacy/current
construction enum. Shared candidate metadata, reference/alias admission,
mandatory selection, measurement, `fits`, optional packing, diagnostic trimming,
and final budget refusal remain one implementation. CandidatePayload distinguishes
ordinary Row from a whole transcript unit; it is an ephemeral view, not a second
ledger. Old entry parameters preserve old rule strings, selection order and
serialization; this is a source intent awaiting exact legacy golden execution.

Legacy entry on Domain 2 returns Version before snapshot/replay/proof work or
hashing. Compiler2 actor fields/knowledge use the native Query2 actor-only port;
raw events use the actual Core V2 visitor. KnownAsObserved is mandatory and has
an explicit provenance kind/reason, distinct from beliefs and world truth.
Original-scope ScopedEvent references propagate through candidates, supporting
evidence and verified mandatory replacements. Query/inspection grant arguments
are never inputs to this generation path.

Both policies share current facts/state/rules/beliefs/relationships/open promises,
action references/aliases, supporting evidence and recent-event floor. Raw player
transcript text cannot introduce an ID or alias into that common phase: units
are built only afterward. A mandatory overflow refuses before optional packing.

Relevant retains current exact/lexical optional Row ranking. Recent never ranks
optional content lexically: newest whole eligible units are admitted by the SAME
optional count/byte/token/selected-record limits. Any unit intersecting mandatory,
supporting or recent-floor scoped event sources is omitted whole with
AlreadySelected. No splitting, source duplication or partial text truncation.
Admitted Recent units are finally presented chronologically; generic budget
cleanup occurs before that reorder so lower-ranked older units are dropped first.

The unit constructor uses actual Core actor_receipts_v2, which already removes
empty/private receipts. For the owning player, it matches the actual canonical
ordinary receipt by original scope/turn and compares the EXACT complete ordered
AcceptedEvent list before copying actual Dialogue/FreeText input and narration.
This is the same Core eligibility plus whole-receipt condition as Query2; new
tests compare actual Query2 message output and Core events. A partial player
view is skipped, not attached to raw prose. NPC units contain only actual
eligible V2 events; input/narration are None, no Request/Proposal is copied.
Author records never become units. Current Core does not create arbitrary NPC
autonomous receipts, so the partial-player future-case guard is source-level,
not a fabricated executed negative fixture.

Domain1 Relevant rechecks the actual existing proof and keeps whole-packet
mandatory/timespan fallback and exact raw delta. Domain2 OR Recent rejects the
old event-only proof representation BEFORE inspecting/rechecking/hashing it and
constructs actual raw V2 event candidates, with Raw/Unsupported and zero cached
candidate/packet use. That Unsupported describes the old representation, not
availability of these actual compiler2 functions. Old proof events are not
relabeled as observed values or transcript messages. Transcript unit counts do
not inflate the existing cached/raw event-candidate diagnostics.

Native snapshot source-fallback reasons remain separately owned by Host/Play;
this code does not fabricate Missing or authenticate diagnostic counts.
No model inference, narrator policy, expected-command substitution, fake fixture
repair, budget increase or duplicate compiler/retriever is introduced.

## Twelve frozen test families awaiting execution

1. All old compiler entries refuse Domain2 Version even with an actual old proof.
2. Both actual policies produce equal mandatory observed A and omit private B/
   author reason while reporting policy separately from Raw/Unsupported coverage.
3. Actual Discover changes player value/scoped evidence but NPC retains A.
4. Relevant can retain the old optional statement while Recent selects newest
   whole turns; common mandatory payloads are identical.
5. Mandatory recent floor excludes an entire overlapping multi-event unit and
   actual eligible/overlap/selected unit counts agree.
6. Actual Query2 whole-player input/narration eligibility matches unit events;
   NPC units have no raw fields, private self-speech or player-only secret;
   positively heard literal Said words remain visible.
7. Actual supported Domain1 proof versus raw Relevant inputs yield identical
   package2 payloads with real verified candidate use reported separately.
8. Recent/Domain2 old-proof representation yields Raw/Unsupported, never cached
   transcript/new observed-value claims.
9. Branch original scopes survive; parent-future/sibling/author canaries and
   prebirth observations obey actual Core lineage.
10. Version/scope/head/reference errors and panicking cancellation are closed
    and leave the actual canonical source unchanged.
11. Mandatory and escaped whole-unit budgets do not truncate payloads or change
    canon; a unit is either complete or absent.
12. Requested policy labels are closed and distinct from coverage/unit counts.

Existing compiler1/context/Play golden tests are not rewritten. Their actual
byte-parity, cancellation, long-history, alias and historical checks must run
again before qualification. No score or assumed pass is supplied here.

## Actual checks and next gate

Only standalone rustfmt/parser and `git diff --check`, owned-path/source/clean-tree
checks have run. Git2.33.0.windows.2, PowerShell7.6.5,
rustfmt1.8.0-stable (01f6ddf758 2026-02-11). Actual command shape:

```text
rustfmt --edition 2021 --config skip_children=true --check crates/locallore/src/context_compiler.rs crates/locallore/src/context_compiler/verified.rs crates/locallore/src/context_compiler/policy.rs crates/locallore/tests/m08_context_policy.rs
git diff --check
```

No Cargo/Node/Gradle/model/app/native IPC/render/device/ADB/CUA/desktop/download/
settings/protected-resource/PR/merge action ran. Root retains the heavy slot.
After explicit allocation, proposed locked/offline jobs1 checks with own D target/
UUID TEMP, debug0/incremental0:

```text
cargo test --locked --offline -p locallore --test m08_context_policy --jobs 1
cargo test --locked --offline -p locallore --test context_compiler_legacy_bytes --test context_compiler --test context_compiler_verified --test context_cancellation --jobs 1
cargo test --locked --offline -p locallore --all-targets --jobs 1
cargo test --locked --offline -p locallore --all-targets --all-features --jobs 1
cargo clippy --locked --offline -p locallore --all-targets --all-features --jobs 1 -- -D warnings
```

Preserve every compile/behavior failure before a narrow source or explicit
fixture correction. Claims are released for Root's independent review/testing.
Play2.5/narrator2.2/Engine staging, coherent Host/Store fallback/jobs/schema5,
trace/capture/frontend/JNI decoders and actual protocol-runner admission remain
separate Root-owned closures. The unchanged courier protocol still refuses
policy execution until actual integration; enum/function source alone does not
qualify D07. No current author wire, model quality, measured savings or human
acceptance claim. Next: actual scoped compiler tests, legacy byte comparison and
independent source review before integrating those callers.

## Actual qualification addendum

The coordinator later granted the exclusive Core build slot. Qualification
claims: #11 6377388668, #12 6377388898, #29 6377389166. Source remains exact
`9137083cf6dd638f320ec9422ea30f763946eaf4`; no production/test correction was
needed for the first runs. Accepted main `5e18015e215262bedf8f91ac13da572ece127d21`
has no Core/Workspace changes since accepted `946c73c`, so no Android merge was
needed in this Core-only branch. Root `efbf39a` and this packet have identical
executable Core/Workspace source; the only Core difference is the later
unit-count interpretation comment `650cf6d`, which is present here. This is not
an assertion of identical source-tree hashes.

Actual environment: Windows, rustc `1.93.1 (01f6ddf75 2026-02-11)`, cargo
`1.93.1 (083ac5135 2025-12-15)`. Fresh own `context-policy-rust` target and
`context-policy-temp-b53ec071-5d9a-483c-ae69-540a5b2e6822` TEMP/TMP outside the
repository; jobs1, locked/offline, incremental0, dev/test debug0, ordinary
LIBSQLITE3_FLAGS empty. No Root target/cache or unimplemented Store test was
compiled. No app/model/device execution or download.

Actual unchanged tests:

```text
cargo test --locked --offline -p locallore --test m08_context_policy --jobs 1
# 12 passed / 0 failed / 0 ignored, compile22.50s, tests0.02s
cargo test --locked --offline -p locallore --test context_compiler_legacy_bytes --test context_compiler --test context_compiler_verified --test context_cancellation --jobs 1 -- --nocapture
# 21 passed / 0 failed / 0 ignored
```

The cancellation suite deliberately catches a synthetic panic; its printed
panic hook is not a failed test. All 12 frozen policy oracles passed unchanged,
including the explicit prior heard-speech correction; no demonstrated RED was
invented. Logs `01-frozen-policy.log` and `02-existing-compiler.log` are local.

For actual old-source comparison, an isolated read-only detached checkout of
accepted main `5e18015` ran its SAME existing unchanged
`context_compiler_legacy_bytes.rs`, own `context-policy-baseline-rust` target:

```text
cargo test --locked --offline -p locallore --test context_compiler_legacy_bytes --jobs 1 -- --nocapture
# 1 passed / 0 failed / 0 ignored, compile19.08s, test0.25s
```

No old compiler was copied and no fixture was edited. All five probe lines
matched exactly (count5 each and Compare-Object equality), including serialized
diagnostics/accounting/order, not just selected content:

```text
director       b671903865fb32cc641747fe94f3f4264d8e6abb259e501223026967e43df18d
character      2bc7c73c6407599b682265b4e9c3f26019cb4bef4e1ff871d7c5e17d6a090381
historical     8dfecac53e93e57288d499bcc9321b970e1cc07ff9aceee98d1d260ef86a2e63
referenced     7427d245754368d61b1469d29292be7fb67ee049632c3a4237cf8ba210a3abb7
mandatory-only 369f6158981edd3012eb997914bd85e99aa7634fd866294e27a04000cd66b8bd
```

Baseline log `03-accepted-main-legacy-probe.log` retained locally. Full default/
all-feature and strict checks are pending at this intermediate addendum. These
actual compiler runs do not enable the unchanged eval protocol's policy gates
or establish Domain2 Host/Play/Store integration, human review or model quality.

### Broad-check checkpoint before independent review import

At unchanged source `cbe5702`, actual `cargo test --locked --offline -p locallore
--all-targets --jobs 1` passed **219 tests, 0 failed, 2 existing ignored** across
33 binaries. Frozen12 passed again. Default compile23.21s; the existing 10,000
attempt replay/conservation binary passed26 tests in118.70s.

The sequential all-feature command stopped exit101 at the existing
`inspection_query.rs:409` future-version fixture: its version2 request expected
`Err(Version)` but now returns the intentionally implemented Query2 Page.version2.
That binary passed15/failed1; preceding binaries passed, including the unchanged
10,000-attempt binary26/26 in119.94s. This is an observed compatibility-test RED,
not a compiler-policy failure or a completed all-feature qualification. Original
test/assertion/source and `05-core-all-features.log` remain intact at this
checkpoint. The sequential script therefore did not execute either Clippy gate.
Any explicit future-version fixture correction requires coordinator path
authorization and a separate commit; no production semantics or oracle was
silently changed. Standalone owned-file rustfmt and git diff checks pass; frozen
test SHA256 remains `7eb45f0d9f6efdd0076ea81431257d039a672bfcc0a15d4c2b853ed74b313469`.

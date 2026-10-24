# Play2.5 consumer source and verification — 2026-10-23

Refs #12 M08.03, #11 M07.01 consumer prerequisite, #29 D07.03/.04/.05
prerequisite. Status at this checkpoint: frozen source tests only, UNCOMPILED /
UNRUN; implementation and actual original2.4 capture pending. Root owns all
Core staging/Engine/Host/Store/schema/platform integration and build execution.
Agent resource_metrics_review owns exclusive existing `src/play.rs`, NEW
`tests/m08_play25.rs`, NEW `tests/m08_play24_capture.rs` (explicit allocation
extension), and this new document under `crates/locallore` / `docs/storage`.
Separate branch/worktree `impl/m08-play25` / `source-play25` from exact
`4b0734228b7c891720e5980ed3c5c0440acc23d6`. Claims #12 6377820558,
#11 6377820752, #29 6377820914; capture extension #12 6377837366.

## Pre-production freeze and original-source capture

Original capture draft b9da1cd is retained. Final separated opt-in capture
commit `33224ed71fe4d11a660dd552ef7e51379775f63b`, helper SHA256
`ab0493ef603455f20fac0a5411c5f25b2f4df8648bb4745f13401f1c08dd41fe`.
It references no future API, so Root can compile ONLY that target against
unchanged2.4 without compiling the deliberately unimplemented stage tests.
It runs actual Play with an explicitly synthetic scripted provider/profile,
validates the same result through actual original2.4 restore, and retains all
real measured timings/counts without normalization. It writes create_new only
to two fixed names under pre-existing caller-owned
`std::env::temp_dir()/locallore-play24-capture`:

- `accepted_play_v2_4.json`: actual seed/Receipt, source/synthetic metadata,
  compact Receipt and PlayRecord byte counts/SHA256.
- `accepted_play_v2_4_receipt.json`: exact compact full Receipt, no added newline.

Explicit opt-in `LOCALLORE_CAPTURE_PLAY_V24=1`; ignored by normal tests.
Proposed actual Root command, NOT an execution claim:

```text
cargo test --locked --offline -p locallore --test m08_play24_capture freeze_original_v24_before_current_version_bump --jobs 1 -- --ignored --exact --nocapture
```

Root owns adoption of the two new fixtures. Never manufacture2.4 metadata from
the2.3 fixture or treat a current2.5 generation as an original2.4 measurement.
Play production must remain2.4 until the actual capture is saved. Existing
goldens2.1/.2/.3 are untouched.

Future-API provider tests frozen before production at
`d82b1a1882ada1367701d4d836a252435fb22eec` (eight tests) plus additive
`06c08786e775d66814b24a747e8d3ac01f15b7df` (ninth grounding pair). Final
test SHA256 `108f0224713a48751fb1f7e3ad4fd1e6dedb29af0b30f1f6150e1799bcdb7085`.
No assertion in the first eight was changed. The ninth pair makes the actual
safe-evidence validator consequential: same private golden-mark truth, Wait
must fall back while actual this-turn Discover can ground the guarded phrase;
canonical items never change in either case.

## Frozen provider-path oracle families

1. Actual Domain2 discovery: Director sees retained A, narrator receives actual
   staged observed B and no optional history/other player secret/author reason;
   current2.5/narrator2.2/context2/compiler2/Relevant metadata, player-only update.
2. Both real policy arms execute compiler2 through the same actual entry;
   recent whole transcript units are visible only to Director, never narrator.
3. Wait/Dialogue do not attach old knowledge, current private truth, raw speech
   or audience to narrator. Approved outcomes remain actual.
4. All ten native closed fallback reasons are recorded separately from actual
   Domain2 compiler Raw/Unsupported; no fake Missing or cache contribution.
5. Exact committed retry uses zero roles despite changed current policy/profile,
   cancelled token and different source fallback; accepted bytes/canon persist.
6. Actual canonical current replay is exact; mismatched2.5 policy/prompt/context
   tuple, missing/unknown policy, compiler/context version tampering reject.
7. Unsupported intent0roles, wrong actual proposal1role/no narrator,
   cancellation during narrator and mandatory-budget0roles preserve canon.
8. A newly observed value mentioning an off-screen actor does not expand the
   hidden-actor allowlist; fallback stays exact mechanical summary.
9. Guarded phrase pair above distinguishes this-turn observation grounding
   from privileged world truth; safe prose never creates an inventory effect.

Scripts are synthetic test providers using the actual public Play path; no
model/quality/native/device result follows. Tests have not been compiled or
run. Core stage seven frozen oracles remain separately unchanged.

## Actual source-only checks and next work

At this checkpoint only source/issue/Git reads, standalone rustfmt/parser,
`git diff --check`, owned-path/source-hash checks ran. No Cargo/type check,
provider execution, Node/Gradle/model/assets/app/native/device/ADB/CUA/desktop,
transport/download/settings/protected-resource/PR/merge action. No heavy slot
taken. Root holds execution resources; preserve first actual compile/behavior
failure before a narrow source or explicit fixture correction.

After actual original2.4 capture, implement one current pipeline using Root's
opaque stage/evidence and consuming commit. Expose only crate-private current
validation; keep old2.1–2.4 strict history-only validation/serde omission/bytes.
Then freeze source and qualify on actual combined Core after explicit GO;
Host/Store/platform/decoder/eval policy closure remains separately Root-owned.

## Original2.4 capture completed by coordinator before production edit

Root corrected source metadata with agent commit8168161:4b073422 is explicitly
`production_source_base_commit`, not a claim about the entire executed tree.
Final capture helper SHA256
`3abd91b0afc012aa0ec81375e62d5ce3bf3af684097e22cefb4603c1b6f1ca7d`
requires `LOCALLORE_CAPTURE_SOURCE_COMMIT`40hex. Root actually ran the opt-in
capture at `bfc78612ccf39eb2a5b52191d2fb54c136c8f511` with unchanged2.4
`play.rs`: **1 passed, 2 explicitly fake provider calls, actual replay exact**.
This is coordinator execution, not this agent's run. Root adopted original files
in `29e24efdc3d85e114a5bf7edea5174a8075f2698` (import here98f58aa), unchanged:

| Actual original artifact | Bytes | SHA256 |
|---|---:|---|
| Full fixture accepted_play_v2_4.json | 8504 | `f08801ab9ce13e0bb47434896dafa1e8e671fa4f4a239731cbd2ee0f42730e2d` |
| Compact full Receipt accepted_play_v2_4_receipt.json | 2150 | `38dcf7329addf4ed98fd984cdb9eac95f8d078be03bf4633dd7082d23ac4bc3f` |
| Compact PlayRecord from that SAME actual Receipt | 1352 | `6ed4abcd325e14fa334d23ead9b843ebe93afd91e26b28e3167ad95e552b9341` |

Only after Root confirmed those saved bytes did this agent edit production.
Additive golden oracle `23d2829c9fb309c0b7359388920005c5ee393c03` includes the
unchanged original2.1–2.4 files, strict restore/zero-role retry, omitted old
context_policy, exact2.4 compact Receipt/PlayRecord hashes and rejection of
policy metadata grafted onto an old record. It does not regenerate or rewrite
goldens. Final NEW current test file has10 tests, SHA256
`5d7ec74da076df40784769163156604e6aed3b364646be8ea499e4dc324e7359`.
All remain UNCOMPILED/UNRUN here; original nine pre-production oracles remain
unchanged. New golden assertions reference independently measured old bytes.

## Frozen current source implementation

Production commit `488ce1618f4198c4db971eda0245edca2d47712e` changes ONLY
`crates/locallore/src/play.rs` (195 additions/48 removals), SHA256
`359f9018c9c2a75c6854acf9d647ea6675c91b21b3b3fb15145096ef7d53883f`.
No Engine/Store/Host/compiler/inspection/old-test edit is included.

- Fresh constants become Play2.5 and grounded-prose-v2.2. PlayRecord gains only
  default/serde-omitted optional closed `context_policy`. Historical2.1–2.3
  keep no context;2.4 keeps context.version1/compiler1 and no policy. All old
  versions are explicit history-only; the old narration validator/source remains
  unchanged. Current2.5 requires context.version2/compiler2/Some closed policy.
- Added native `PlayConstructionInput{coverage,policy}` and
  `execute_traced_with_policy`, with Relevant default through existing execute/
  trace/Option-proof/CoverageRead APIs. BOTH actual enum arms call the same
  `compile_policy_cancelled` version2 pipeline and capture actual package2.
  Source fallback remains a separate closed claim; new Raw/Unsupported does
  not become Missing to satisfy the old2.4 metadata constraint.
- Finite action precheck uses Root's actual opaque stage then discards it;
  actual provider bytes still parse/agency/resolve through a new stage. The
  approved ordinary Receipt remains the private-consent ApprovedPlan artifact.
  No expected proposal substitution, inspector argument or second compiler.
- Narrator Structured input serializes ONLY Root's opaque safe evidence. The
  actual evidence65,536 encoded cap and separate24,576 encoded prompt bound are
  checked; profile4096 context/350 tokens per role/120s/one repair remain. No
  ContextPackage, seed truth, raw input/utterance, reason, private binding or
  canonical wrapper is serialized into that narrator request.
- Crate-private `validate_record_v25(engine,approved,evidence,record,history)`
  supplies Root's exact Core call surface. It checks the tuple, finite bound
  metadata and evidence event catalogue/observation attribution; it never
  accepts metadata as proof. Actual evidence creation/regeneration/full-basis
  revalidation remains Core's responsibility, not a parallel Play authority.
- Shared conservative prose checks take actual this-turn observation text ONLY
  as additional grounded phrase/source support for2.2. Hidden-actor visibility
  and impersonation controls are unchanged; no wider actor allowlist. Old2.1
  validator receives no evidence and retains its original source string. This
  is a finite check, not semantic completeness or a model-quality guarantee.
- Invalid narrator prose uses exact approved mechanical summary/event IDs and
  fallback=true. Final accepted-candidate stage consumes Root's opaque token
  through `commit_staged_play_v25`, preserving Core cancellation/source checks.
  Play introduces no canonical binding serialization or persistence.

This isolated branch intentionally does not implement Root's pending
`engine::staged_play` module/consuming commit; source references the approved API
and was statically compared with Root's stage-only7b1c057 getters. No stub or
local substitute was introduced to make it compile. Actual type/borrow/budget/
behavior and complete integration tests remain pending on Root's combined source.

## Current handoff and remaining closure

Actual own checks are standalone rustfmt/parser on owned files, diff check,
source/test hashes, owned-path inventory and clean-tree verification. No Rust
type checking, synthetic provider execution, build, model, app/native/device or
heavy slot usage by this agent. Root's original capture result above is the
sole newly attributed execution, not a current2.5 pass. No RED is fabricated
from missing APIs; preserve first actual failures when qualified.

Root must import the source/tests and complete Engine history/current dispatch,
opaque commit source fences and private-binding replay comparison. Root also
owns existing inspection_query PlayRecord fixture None/old2.4 labels, Host
legacy-refusal/capabilities/Work/source/trace behavior, schema5/archive/retention/
jobs compatibility, native/JNI/frontend/eval schema/version/decoder closures.
Legacy typed inference still has CharacterContext1 and no new NPC role. Current
trace capture reuses only actual safe ContextPackage2/Structured role envelopes
and ordinary approved Receipt; no historical context reconstruction is claimed.
Original reports/curated fixtures/budgets remain immutable and new comparison
execution remains unavailable until actual full integration.

Suggested first actual tests on Root's combined source, AFTER explicit GO:

```text
cargo test --locked --offline -p locallore --test m08_staged_play --test m08_play25 --jobs 1
cargo test --locked --offline -p locallore --test context_play --test play_verified_memory --test play_v2 --test production_turn_trace --jobs 1
cargo test --locked --offline -p locallore --all-targets --jobs 1
cargo test --locked --offline -p locallore --all-targets --all-features --jobs 1
cargo clippy --locked --offline -p locallore --all-targets --all-features --jobs 1 -- -D warnings
```

These are proposed commands, not results. Existing future-version fixtures may
need explicitly attributed owner corrections, never silent assertion changes.
No tests/models/scores were changed to improve outcomes. This is an implemented
source packet **in_review, unqualified**; release owned Play claim to Root for
independent qualification/integration. No milestone checkoff or human approval.

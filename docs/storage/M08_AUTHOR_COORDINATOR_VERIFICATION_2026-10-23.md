# Mixed history coordinator qualification — 2026-10-23

Refs #12 M08.03/.06, #8 M04.01/.04/.06, #11 M07.01 and #30 D08.
Partial implementation, **in progress; not milestone acceptance**. Accepted
baseline is main `cf9332718cc5ffd98c5a4ab8fa0295205d5c9a10` (PR #127).
The coordinator owns integration, schema5 and platform admission. Independent
source packets retain their original unrun status; actual runs below supersede
only the corresponding qualification, not those historical descriptions.

## Actual shared checks before current Play integration

On `4b0734228b7c891720e5980ed3c5c0440acc23d6`,
`cargo test -p locallore-storage --offline --locked` passed **209 tests**, with
five existing ignores. This was one complete unfiltered Store run, including
the thousand-event retrieval/interference test (304.88 seconds), actual process
exit tests, real SQLite pressure, historical migrations and cancellation. The
local retained log is `author-integration-artifacts/store-broad-next.log`.

Earlier failures and fixes remain recorded, rather than being called passing
budget tests: old positional INSERT fixtures failed additive column arity;
explicit original-column lists restored their unchanged behavioral assertions.
Historical fixtures that relabeled a schema5 file as an old version failed
SchemaMismatch. The replacement builds exact historical DDL and validates it
read-only. Eighteen historical-fixture tests then passed. The schema2 WAL test
uses an actual Core-validated turn and bounded fixture SQL while readers pin the
WAL; it does not claim execution of a historical production writer.

Independent author Store tests initially passed 12/13; lookup decoded the
ordinary request before its kind discriminator. Three historical read tests
failed on schema5-only columns. `88aea3f` fixed both dispatches; all 16 passed.
The independent SQL abort trigger tests atomic rollback, not disk exhaustion.
The separate private unit pressure test `b85122a` produced actual SQLite Full
under max_page_count: application rows and canon rolled back; explicit retry
after restoring capacity committed once, repeated retry found that same child,
and reopen lookup succeeded. One test passed; no production pressure control.

Legacy Host tests initially passed 1/3: PlaySnapshot panicked on an unwrapped
Version error and poisoned its owner; omniscient Inspect returned incomplete
ordinary receipts. `2ccea25` propagates Version and refuses the incomplete
legacy view. All three then passed, including continued unrelated Domain1 use
and unchanged mixed canon. This is a safe refusal, not functional Domain2 UI.

The current pre-Play focused Core set passed 48 tests: author14, legacy2,
independent author6, Query2 ten, policy12 and independent policy4. Compiler2
qualification, preserved initial failures and historical package hashes are
recorded separately in M08_CONTEXT_POLICY_VERIFICATION_2026-10-23.md.

## Original Play2.4 bytes, captured before changing production

At executed source `bfc78612ccf39eb2a5b52191d2fb54c136c8f511`, unchanged
production base `4b0734228b7c891720e5980ed3c5c0440acc23d6`, the opt-in
`m08_play24_capture::freeze_original_v24_before_current_version_bump` passed.
It made two bounded synthetic provider calls and independently restored the
actual receipt before writing its two fixed, create-new local outputs.

* Compact receipt: 2,150 bytes, SHA256
  `38dcf7329addf4ed98fd984cdb9eac95f8d078be03bf4633dd7082d23ac4bc3f`.
* Compact PlayRecord: 1,352 bytes, SHA256
  `6ed4abcd325e14fa334d23ead9b843ebe93afd91e26b28e3167ad95e552b9341`.
* Full synthetic fixture: 8,504 bytes, SHA256
  `f08801ab9ce13e0bb47434896dafa1e8e671fa4f4a239731cbd2ee0f42730e2d`.

Exact outputs were adopted at `29e24ef` under Core tests/fixtures. Original
2.1–2.3 fixtures were not regenerated, relabeled or overwritten.

## Current staged Play qualification so far

Seven independent stage oracles were source-frozen before implementation.
Their first actual compilation failed because the proposed API was absent;
this is not a behavioral RED. After `7b1c057`, all seven passed. Stage uses
the same private preview/resolver and actual candidate append, then reads only
the selected player's new eligible CoreV2 observations. Said is sanitized;
earlier knowledge, private truth sources, author reason and speech are excluded.
Encoded evidence is bounded at 65,536 bytes without truncation. The maximal
escaped single-fact test does not claim to force an unreachable overflow.

At `a1cc243`, focused tests passed **32**: nine frozen synthetic-provider
pipeline tests, seven stage tests and sixteen existing query tests. The first
combined build failed on the coordinator's mistaken policy variant in one
synthetic fixture; only that variant was corrected. The actual policy enum is
StateRelevantMemoryV1. Both current policies invoke compiler2 through the same
pipeline. Source fallback and compiler Unsupported remain separate. Narrator
input uses only actual this-turn safe evidence. These are model-free tests,
not model quality, native IPC or WebView evidence.

The subsequent independent consuming-stage set passed eight tests. Independent
provenance tests first failed 0/2: replay accepted an impossible Missing label
for Domain2 Relevant / Domain1 Recent, whose compiler branch refuses proofs
before inspection. `b42355b` requires the real Raw/Unsupported tuple and seven
zero cache/progress counters, retaining independent native source reasons and
actual raw actor-event counts. Both frozen tests then passed. Combined focused
qualification passed 34 tests with two existing capture ignores, including exact
original 2.1–2.4 receipt/hash preservation and current verified-memory checks.

Current Core coverage totals **302 passing tests / three capture-only ignores**
across complementary cohorts, not a single unfiltered current run. The first
broad run passed 10,000 seeded attempts (129.65s), then failed a fresh 2.4 label
assertion after the current prompt became 2.5. Another current-label assertion
and current compiler1/future2 fixture expectations were explicitly modernized;
all original agency, bounds, privacy, replay and canonical assertions remained.
The complement log plus remaining-target log cover every other test; their five
overlapping guarded tests are counted once. No old golden was regenerated.

Three actual Store integration tests passed: author fork → generated corrected
discovery → same-Store commit → reopen exact full canon/private bindings and
playerB/NPC-oldA; zero-provider retry and late-cancel Committed; cancelled draft
refusal; full-source Stale and unsupported unbound prose Narration. These use
synthetic provider output and actual SQLite, not native IPC or model inference.

Strict shared `cargo clippy --workspace --all-targets --all-features --offline
--locked --exclude locallore-desktop-spike -- -D warnings` passed at `b44f911`.
The evaluator initially passed 16/23 unit tests; its fresh-run compiler envelope
oracles still expected1. Requiring current POLICY_COMPILER_VERSION2 at the two
production sites preserved all case expectations and historical checkpoints.
The unchanged suite then passed 26 tests / one historical-copy ignore.

Desktop metadata's frozen five tests first passed 4/5: actual Store database5
was rejected as Wire. `5ff4a43` admits known physical versions1–5, keeps protocol1
separate, and moves the old future5 oracle to6. All five passed. These are Rust
native-command/Host tests, not WebView execution. A subsequent native migration
runner stopped before launching the app: its development fixture only removed
new tables then relabeled current schema as1. FixtureReadOnly correctly refused
that altered schema. The development-only fixture was corrected to construct the
exact historical DDL; the subsequent actual native run passed 29 distinct checks
with eight application-owned WebView2 captures across two sequential apps. All
eight renders were inspected. No render evidence is inferred from the failed
attempt. Final evidence is recorded in
[the qualification report](M08_FINAL_FOUNDATION_QUALIFICATION_2026-10-23.md).

Android's five new actual-JSONObject/Gateway tests are instrumentation source;
they are not local JVM tests. The two production physical-version guards now
require5 while protocol1 and every recovery/cancellation path remain unchanged.
Current-target test fixtures were updated explicitly; historical archive bytes,
schema4 capacity profiles and dated device evidence were preserved. The first
offline ordinary JVM/APK/testAPK/lint build passed with 182 JVM tests, both native
ABIs and 78 executed tasks. It preceded the later narration guard; final-current
checks and artifact identities belong to the qualification report. These five
instrumentation tests were compiled, not executed. No new JSON dependency or
device allocation was introduced.

Full platform acceptance is still pending. No author UI
or native author capability is exposed. Archive1/2 reject mixed Domain2 until
explicit Archive3 support. Legacy Query1/compiler1/inspection exports remain
closed on Domain2. Memory jobs/proofs return Unsupported; no new summary,
inference backend, persistence owner or automatic scheduler was introduced.

## Reproduction and environment

Windows 11 Pro 10.0.26300 x64; Rust/Cargo 1.93.1; offline locked dependencies.
Runs use CARGO_PROFILE_DEV_DEBUG=0, CARGO_PROFILE_TEST_DEBUG=0,
CARGO_INCREMENTAL=0, CARGO_BUILD_JOBS=1 and ordinary task-owned TEMP/TMP.
One heavy suite/application at a time. Commands above additionally use a
task-local `--target-dir`; generated logs/databases remain local and ignored.
The earlier model-free results above remain attributed to their actual source
revisions. Later native migration and current real-model journeys, including an
observed contradictory narration, its regression/fix and corrected run, are
documented in the qualification report. They do not establish prose quality,
physical-phone parity or complete D2 consumers. No device/ADB, desktop control
or desktop capture, hosted CI, release or repository setting change was made.

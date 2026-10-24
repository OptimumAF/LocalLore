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

Full current Core and platform qualification are still pending. No author UI
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
No real model, native application, device/ADB, desktop control/capture, hosted
CI, release or repository setting change is part of this report.

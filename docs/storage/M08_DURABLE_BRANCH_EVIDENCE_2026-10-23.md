# Durable fork source and test evidence

Refs #12 M08.01/.02 and #30 D08.04 dependency, partial/in_review. Exact-path
claims6359949860/6359950283 preceded edits. Coordinator transferred the shared
Engine continuation restore, storage turns loader and new branch module/tests;
storage lib.rs changed only its module/export stanzas. Source implementation is
`b11986cdb4d51847ca2a6ae75632341e27de85e5`, isolated
`impl/m08-durable-branches` / task D/source-branches. It started from frozen
f91cf53, then **before implementation** fast-forwarded accepted main
`c1aea6efb8cb12c182ffb8cf7ffd9c88d3503e6b`; that base difference was documentation
only. No accepted main history was rewritten.

## Actual checks

Windows11Pro10.0.26300 x64, Rust/Cargo1.93.1, pinned locked/offline dependencies;
DEV/TEST_DEBUG=0, INCREMENTAL=0. Dedicated task D/m08-branches target; test temp
under task D/temp with unique synthetic fixture names. No new dependency, DDL,
001/002 migration, config, Host/schema/workspace, app/UI/Android or model edits.
No model/worker/desktop/CUA/device/ADB/hosted service/protected resources were used.
Existing Store crash unit tests launched only their own synthetic test subprocesses.
No app, model download, merge, release or settings change occurred.

Commands actually run from source-branches, with task paths abbreviated:

```powershell
$env:CARGO_PROFILE_DEV_DEBUG='0'
$env:CARGO_PROFILE_TEST_DEBUG='0'
$env:CARGO_INCREMENTAL='0'
$env:TEMP='<task>/temp'
$env:TMP=$env:TEMP
cargo +1.93.1 check -p locallore-storage --all-targets --locked --offline --target-dir <task>/m08-branches
cargo +1.93.1 test -p locallore-storage --test durable_branches --all-features --locked --offline --target-dir <task>/m08-branches
cargo +1.93.1 test -p locallore --test branch_restore --locked --offline --target-dir <task>/m08-branches
cargo +1.93.1 clippy -p locallore -p locallore-storage --all-targets --all-features --locked --offline --target-dir <task>/m08-branches -- -D warnings
cargo +1.93.1 test -p locallore -p locallore-storage --all-features --locked --offline --target-dir <task>/m08-branches
cargo +1.93.1 fmt --all -- --check
git diff --check
```

Final exact-source two-package all-feature run: **204 tests passed,0 failed,
0 ignored**, across23 emitted unit/integration/main/doc-test result groups
(zero-case groups included in that group count). This includes **14 new tests**:
12 actual Store branch cases and2 strict Engine continuation cases. It is not a
whole-workspace/native/Android execution claim. Final strict all-target/all-feature
Clippy, formatting and diff checks passed. The newest focused12-case Store run
completed in1.12s, the complete run's branch group in1.13s. These are warm local
test observations, not fork latency percentiles, phone performance or a target
gate. Original checks cover root storage, migrations, replay, Play policies,
knowledge/privacy/context, cancellation and process-exit recovery as well.

Logs remain outside Git in the owned D task root:
`m08-branches-final-shared-tests.log` (22,657bytes),
`m08-branches-final-focused.log`, `m08-branches-core.log`,
`m08-branches-final-clippy.log` (198bytes). They contain synthetic test data only;
no player save/model diagnostics were read or uploaded.

## New finite assertions

| Case | Demonstrated behavior |
|---|---|
| durable fork/continuation/reopen/retry | Original root receipt scope retained; child writes only its one local turn/event; parent gifts while child consumes independently; sibling retains item; no ancestor turn/caches copied; full local request retries return exact receipts after reopening |
| immutable fork identity | Same child+parent+fork returns created=false/current head after both heads change and even expected-parent guard changes; different fork conflicts; stale guard for new child does not create it; revision0 child starts next event at1 |
| cancellation/SQL abort | Five precommit callback thresholds and a panicking callback leave no new branch; AFTER INSERT projection abort rolls back metadata/membership/projection; parent unchanged; retry creates once |
| nested earlier rewind | Parent born at5; its child forks at1; next descendant keeps root event1 and child event2 with correct scopes, excludes intermediate parent's later event; actual reopen and character context agree |
| bad inputs | Partial multi-command turn, future boundary, invalid/duplicate IDs and foreign story/branch fail without partial creation |
| logical graph/source tamper | Cycle, missing parent, future-parent fork link and changed inherited envelope fail Integrity; no recursive hang or new canonical state |
| excluded later source/projection | Corrupt later parent normalized envelope makes parent fail but leaves already-forked child replay valid; forged child projection is ignored/rebuilt from canonical history |
| competing owners/caps | Two owners create same immutable child exactly once; maximum32-node path; story cap race from255 gives one new child and no more than256 branches |
| parent drafts/child turn races | Parent draft is not inherited; child cancel leaves canon unchanged; competing child turns have one committed outcome and one Stale; changed retry payload rejects, original receipt survives |
| inherited admission budget | One inherited accepted turn plus4095 valid synthetic cancelled child intents reaches4096; a new draft rejects before it could make child resume exceed the replay cap |
| observer canaries | Reopened child NPC/player context excludes later-parent and sibling text; NPC also excludes unwitnessed child text and the original secret; player retains its own child statement |
| unsupported consumers | Context compiler, inspection query and derived-memory Store preparation explicitly reject child support; no guard bypass or false playable feature |
| strict continuation | Original ancestor/local scopes and same turn IDs remain independent; forged/duplicate-key/oversized saved data fails without mutating original Engine |
| recorded policy | Exact accepted historical v2.1 Play fixture restores/inherits; unsupported v2.0 rejects; fresh prepared historical commit remains rejected |

The budget case uses the existing durability-test method of bulk-inserting valid
synthetic terminal request rows for a bounded-cap fixture. It introduces no
production SQL/import API or alternate accepted-event authority. Graph/source
tamper operates only on test-owned files. Disabling FK enforcement on that raw
tamper fixture simulates external file damage; the real Store keeps its verified
FK policy enabled.

## Preserved failures and scope limits

The first focused run (`m08-branches-focused.log`) had3 passes/7 failures because
the new test helper passed arbitrary narration to strict typed v1 commit. It now
uses the actual Engine preview/rendered narration. The next run
(`m08-branches-focused-fixed.log`) had9 passes/2 failures: the test expected a
fully consumed item to remain at quantity0, but the accepted rule removes it;
and raw tamper setup incorrectly assumed a fresh bundled connection defaulted
to FK-off. The repaired assertions require actual item absence and explicitly
disable FK only on the synthetic external-damage connection. Production gates,
rules, privacy checks and narration validation were not relaxed. An initial
strict Clippy unnecessary-closure finding was corrected before the passing check.

No new kill-during-fork, sustained/disk-full/maximum-history performance, app
branch selection/switch-during-generation, real-model, Android/device, archive,
correction/deletion, cross-platform round-trip or network-denied journey ran.
Existing process-exit transaction tests are not relabelled as a new fork crash
journey. The small API does not establish prompt whole-operation cancellation.
Root story catalogue, child retrieval guards and Host/app interfaces remain
unchanged. Full M08/D08 acceptance stays open.

## Source identity

SHA256 of exact local compiled checkout bytes at b11986c; line-ending conversion
can change raw hashes. Checksums identify inputs, not trust or acceptance.

| Path | SHA256 |
|---|---|
| crates/locallore/src/engine.rs | `5b28407e4dc29677fd09d62b43de4dbcaccf399e8f7f3486af4938ebbfebbed9` |
| crates/locallore/tests/branch_restore.rs | `0f16fcbf3731557a5f0afa4adad4441ebdf8517e879ac259fd6d36499d48f232` |
| crates/locallore-storage/src/lib.rs | `ab8bf8809492fb2a34730bc756e3490df6d309299119b13c0021db1d8e1848eb` |
| crates/locallore-storage/src/turns.rs | `2680e407fe2504b4a0e1634dda4bc04dde478f1d64897a3cac0a91aa1e4f75cc` |
| crates/locallore-storage/src/branches.rs | `73d7bd9fff8435a840f4b8b0b20f49e5af0c3c30234860e718e8f8f61434139e` |
| crates/locallore-storage/tests/durable_branches.rs | `fa857ae58cf3a8e39bcc7270b1601e414ad99f3dfcc74ee3e0cfa32d16b92ec4` |

Implementation author does not self-approve this risky shared loader change.
Next: coordinator's independent source/adversarial review and broader integration
checks, then a separately frozen shared historical-context/branch-consumer slice.
All task checkboxes remain unchecked until their full criteria and owner acceptance.

# Frozen consuming staged-Play commit oracles

2026-10-23. Refs #12 M08.03/.06. **Eight new cases are source-frozen,
uncompiled and unrun.** At this branch's baseline the approved stage and
consuming-commit APIs were absent; Play still admitted fresh 2.4. Missing APIs
are not an executed behavior RED. This packet implements no stage/Play/Store or
native author feature and introduces no provider/runtime dependency.

## Ownership, attribution and interface

Separate `review/m08-stage-commit` / `source-stage-commit-review` from exact
`29e24efdc3d85e114a5bf7edea5174a8075f2698`. Read AGENTS/prior workflow and
claims, the original accepted 2.4 source/fixture attribution, and
`M08_PLAY25_STAGING_PROPOSAL_2026-10-23.md` including Root's interface/evidence
bound decision `89c6a7d`. Claim #12 `6377914013` preceded writes. Root approved
the concrete test direction, no extra unspecified record-error precedence and
native actual-Play fixture construction.

Owned TWO NEW paths only:

- `crates/locallore/tests/m08_staged_commit_review.rs`
- `docs/storage/M08_STAGED_COMMIT_FROZEN_ORACLES_2026-10-23.md`

No existing Engine, Play, source contract, tests, historical fixture, platform,
schema or Store file changed. Root owns production and integration. All existing
stage-seven, compiler and old/current Play oracles remain unchanged.

The new eight-case source is frozen **before consuming commit implementation**
at `4c2c2acbff56c249134c5a036cbafcffa6e99c7c`, SHA-256
`d987fe8c71e41dca067b726823d77b4f76c6708249372a14f3d0c13d97c8833c`.

Native API assertions follow the approved contract:

```text
Engine::stage_play_v25(&self, request, proposal, cancel) -> StagedPlayV25
Engine::commit_staged_play_v25(&mut self, staged, &PlayRecord, cancel) -> Receipt
```

StagedPlayV25 is moved into commit; no cloning, deserialization, public field,
caller-supplied evidence or retained Engine access is used. `approved()` and
`narrator_evidence()` are read-only views. Changed full source is Stale; a
different accepted request occupying the key is RetryMismatch. Invalid new
record must refuse/no append; a particular Narration versus Version mapping is
not invented where the contract leaves it unspecified. Exact recorded retry
must precede cancellation and stale-token basis checks.

## Genuine bounded synthetic Play fixture

Each new record comes from actual `play::execute` on an independent clone of the
exact source Engine using a bounded `ScriptFakeProvider`. Its two finite replies
are valid Director JSON for Wait1 and deliberately malformed narrator `{}`. The
real parse/agency/resolution and mechanical-fallback path must produce the
Receipt. No Receipt is deserialized, manually constructed, modified or treated
as an accepted-state mock. A mutable PlayRecord copy is used only in explicit
hostile new-record validation cases.

The helper requires exactly the actual Structured Director and narrator calls,
fresh prompt2.5 / grounded-prose2.2 / context2 / compiler2 / closed Relevant
policy and actual fallback=true. Profile context4096, role caps350, deadline5s
and repair1 remain inside existing limits. There is no downloaded or real model,
quality claim, expected-command substitution, extra role or alternate compiler.
Generation mutates only its independent Engine clone; the selected source is
changed only by the actual consuming Core operation under test.

## Frozen cases

1. **Actual current acceptance and replay.** On both actual Domain1 and authored
   Domain2 histories, consume a stage with the genuine PlayRecord and require the
   exact real Receipt, one canonical append and full source equality. Rebuild
   complete records via replay_records and serialized restore. A fresh equal
   source's commit_prepared must revalidate the genuine current receipt. Exact
   Play retry receives an empty provider and returns the winning receipt with
   zero calls. Replay APIs themselves expose no provider port; no inference
   callback is fabricated to claim a measurement.
2. **Same-head author truth divergence.** Two actual children use the same scope,
   revision, mechanical projection, canonical projection bytes and identical Wait
   approved receipt/evidence, but private author histories change world truth to
   B versus C. Their full accepted bases differ. A token from B must be Stale on
   C, with no append. Comparing only head, projection, approved effects or safe
   evidence would fail this oracle.
3. **Same-head valid Seed replacement.** A different valid hidden seed fact leaves
   scope/head/mechanical bytes and the Wait operation unchanged. Full source
   differs, so the original token must be Stale and leave the actual replacement
   untouched. Seed identity text alone is insufficient.
4. **Intervening accepted progress.** Another actual typed turn after staging
   makes consuming commit Stale and preserves that intervening receipt/source.
   No rollback, duplicate append or downstream replay is allowed.
5. **Mismatched new record.** Wrong event IDs and unknown prompt tuple each refuse
   before installation and preserve the full source. A newly staged capability
   with the genuine record then succeeds; refusal cannot poison the key or hide
   an accepted partial state.
6. **Cancellation and retry.** Always-true, panicking and false-then-true
   cancellation (second check onward) refuse without canonical installation.
   A fresh stage with cancellation false can commit the genuine receipt. This
   finite callback schedule is not arbitrary process-death or disk evidence.
7. **Winning exact retry.** Two independent capabilities are staged before first
   acceptance. Consuming the second after the first commits must return the
   actual winning receipt even with cancellation true and now-stale token basis.
   A subsequent exact Play retry with a cancelled request and invalid current
   profile also returns it with zero provider calls. Count/basis stay unchanged.
8. **Different request occupying the key.** An actual typed ordinary turn uses
   the same key but different Request intent. The staged free-text candidate must
   refuse RetryMismatch, preserve the accepted occupant and never append.

## Additional source inspection and limits

While freezing these tests, Root identified separately committed stage-only
source `7b1c05749830bec8112d5670d492c75cdd3c699b`. Its immutable diff/new module
were read without changing this baseline. No additional concrete stage-only
source defect was established: the capability has private fields/no Clone or
Serde, retains basis/ordinary approved receipt/safe evidence rather than an
Engine, uses the same private resolver/actual append on a temporary clone, reads
only the eligible new suffix, substitutes StatementDelivered for raw Said, bounds
evidence JSON and checks cancellation. The local temporary candidate drops when
staging returns. This source observation is not an executed stage qualification
or a review of consuming implementation that did not yet exist.

These eight cases do not cover grounded discovery prose, hidden-actor
conservative fallback, every tuple/version permutation, all escaped/budget
limits, full provider envelope privacy, Store atomicity/source admission,
Host/trace/owner lifecycle, normal schema/decoder routes, native grant/consent,
platform parity or real-model quality. Those remain independently owned gates.
In particular, no safe new native API alone closes old Host Domain2 snapshot
dispatch or makes author wire reachable.

## Actual checks and next runnable gate

Actual reviewer checks only:

```text
rustfmt --edition 2021 crates/locallore/tests/m08_staged_commit_review.rs
git diff --check
Get-FileHash crates/locallore/tests/m08_staged_commit_review.rs -Algorithm SHA256
```

Parser/formatting and whitespace checks passed, not Rust typechecking or behavior.
Git2.33.0.windows.2, PowerShell7.6.5, rustfmt1.8.0-stable
(01f6ddf758 2026-02-11). No Cargo/Node/Gradle, actual SQLite operation,
provider/model execution, app/native runtime, device/ADB, CUA/desktop control or
capture, protected resource, download, settings, PR or merge action ran.

After Root implements and explicitly allocates the exclusive verification slot,
run unchanged attributable new cases alongside existing stage/Play/old-byte tests:

```text
cargo test --locked --offline -p locallore --test m08_staged_commit_review --jobs 1
```

Use task-owned target/TEMP, preserve the original source hash and every actual
failure. Missing API compilation is an implementation gap; a helper mistake must
be corrected explicitly while preserving this freeze and behavioral assertions.
Root owns production fixes, exact historical2.1–2.4/2.5 tuple dispatch and broader
qualification. Claims are released with the handoff; no score, human approval,
acceptance checkbox or model/native execution follows from these source tests.

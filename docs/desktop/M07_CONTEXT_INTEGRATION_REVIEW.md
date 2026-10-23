# M07 production context integration source review

Refs #11 M07.01/.02/.06 partial. Review claim
[6358561602](https://github.com/OptimumAF/LocalLore/issues/11#issuecomment-6358561602).
Reviewer `/root/desktop_durable` owns only this new report on `review/m07-context`.
The reviewer did not author the compiler or production integration under review.
No implementation, Host, schema, store, runtime or application source was edited.

## Scope and evidence boundary

Reviewed source `d35c8840376b8277550bfdee3a2d130a707b5aa0`, based on passive
production hooks `89f6739` and prototype `cc36594`. The net slice is 11 files,
1,996 insertions and 21 deletions. Read the current #11 scope, coordinator claims
6358324987/6358367819, prototype report, architecture/domain/play contracts,
compiler, shared actor port, production play integration, history validation,
tests/accepted receipt fixture, Cargo feature changes and existing native
tokenizer guard. Used Git diffs, source reads, line lookup and SHA256 hashing.

This is source-only review. No Rust/build/test/model/native IPC/render/browser,
desktop/CUA/device or process operation was executed by the reviewer. Source
reasoning below is distinguished from an executed regression. No performance,
quality, release or complete M07 acceptance follows from this report.

## Concrete finding

**P2 - recorded v2.1 history cannot use the existing core fork rebuild path.**

At this review head, `engine.rs:436-467` rebuilds a fork from recorded receipts,
but line 461 calls public `commit_prepared`. That calls `commit_play`, which calls
the private validator with `recorded_history=false`. `play.rs:229-232` accepts
recorded `locallore-play-v2.1` only when that flag is true. The newly repaired
`restore` and `replay` paths use true, but `fork` was missed.

The deterministic source-path reproducer is the new accepted-main fixture:

```rust
let restored = Engine::restore(seed, &[encoded_v21_receipt])?;
let child = restored.fork("child", restored.revision());
// At d35c884, the recorded v2.1 PlayRecord reaches fresh-commit validation:
// Err(Error::Narration), although restoring/replaying that history succeeds.
```

This reproducer was not executed by the reviewer. The affected method is an
existing core history operation, even though durable branch context/UI remains
unsupported in this slice. It fails safely without mutation, but regresses a
previously supported fork of accepted v2.1 history. The integration should use
the private recorded-history validation path for this rebuild and still compare
the complete rebuilt receipt. Add the accepted fixture fork regression; retain
the existing assertions that a *fresh* `commit_prepared` rejects v2.1, v2.0
history rejects, and no inference occurs during historical reconstruction.

The finding was sent to the coordinator before writing this report. Its final
disposition and any follow-up source/test evidence must be appended explicitly;
the reviewer has not silently treated it as resolved.

**Resolution inspected: `a46c1f4ea536757829066fb1124e2cffcacfb6b5`.** The coordinator
added private `commit_recorded`, used only by replay/fork rebuilds. Fork retains
full receipt equality, new prepared commits still take the strict current-prompt
path, and the accepted fixture now asserts the child branch scope plus identical
head, state and receipts. The reviewer read this exact three-file follow-up diff
and the coordinator's `context-legacy-fork.log`: 38 passed, zero failed/ignored
(3 context/play, 26 contracts, 9 restore). This resolves the concrete finding in
source and reported execution; the reviewer did not execute the regression.
The stale inspection module comment was clarified in the same follow-up. No
unresolved concrete blocker remains from this source review.

## Authority and privacy observations

The compiler checks version, exact scope/current head, supported root history,
completed historical boundary and role/actor before source selection. Historical
queries rebuild the selected completed projection; future knowledge is not
backfilled from today's sheets. Director requires the player, Character selects
one existing actor, and there is no caller-controlled Omniscient option.

`inspection_query::actor_context_rows` is crate-private and accepts only Profiles,
Knowledge, Promises and Relationships. It constructs exactly the selected actor
lens, reusing the established knowledge/witness/source/status filters. It does
not accept a grant or widen to raw Player/narrator message rows. Observations come
from the same `Engine::character_context` filter. Truth, recorded statements,
beliefs, discoveries and observations retain typed origins and source references.
Withheld sources retain the withheld marker, without the hidden event ID.

Reference resolution is based on eligible IDs and actor IDs encountered in those
rows. Only then does it read their canonical names. Hidden actor names do not
enter alias ambiguity decisions. Explicit unknown and hidden references use the
same fixed error. Ranking and omissions apply to eligible candidates only.
Diagnostics are not a list or count of private excluded world records.

The production path calls this same compiler before the existing director.
Only selected typed payloads, kinds and source revisions enter the prompt;
rank scores, omission lists and eligible-candidate counts remain outside model
data. Existing owned inventory, living colocated actor IDs/names and outgoing
routes remain in the context stage. The finite action guard and Engine preview
still reject unsupported/invalid actions before generation, then validate the
generated proposal again. These are not new model or author privileges.

Dialogue supplies an empty retrieval query, so a player's literal assertion is
not treated as a factual query or converted into truth. Its bounded original
text still enters the separate exact-utterance schema and original request. No
new summary, transcript-based authority, persistence layer, SQL or remote service
is introduced. Native trusted profile/provider selection is unchanged.

No additional concrete authority/privacy blocker was identified in this source
review. That observation does not prove arbitrary narration correct, prevent
unsupported model guesses, or qualify future summary/alias/branch behavior.

## Budgets, bounded work and provenance

Candidate/output/query/reference/known-actor/selected/diagnostic caps are explicit.
Mandatory current actor rows, known truth/beliefs, open commitments, directed
relationships, recent/reference events and visible supporting evidence are pinned;
mandatory overflow returns a fixed error before provider calls. Optional rows
rank deterministically and may be omitted. Final accounting includes the whole
package and trims optional diagnostics before mandatory evidence.

`estimated_tokens` is explicitly ceiling(UTF-8 JSON bytes / 4), not a measured
tokenizer count. Production separately caps the rendered input at 24,576 bytes.
The existing `native/llama-worker/generate.inc:25-35` builds the official templated
prompt, tokenizes its parts and rejects actual input tokens plus requested output
above 4096 before creating/decoding a context. Template/schema/output overhead
therefore cannot silently overflow the native context. Estimate success is still
not proof that a particular long-history prompt will fit or produce useful prose.

Compiler preparation clones/collects existing eligible history before some caps
are applied and has no cancellation callback. No new mutation/provider authority
results, and the turn's remaining deadline is checked before model work. Maximum
history allocation/cancellation responsiveness was not measured by this review;
the finite 1,026-event results do not establish a worst-case responsiveness bound.

Prompt provenance advances to `locallore-play-v2.2`; accepted main v2.1 is limited
to private recorded-history validation. Narration policy remains grounded-prose
v2.1. Restore compares full rebuilt receipt JSON and replay compares the full
engine-created receipt. The new fixture tests preserve an exact accepted-main
receipt and reject both a fresh legacy prepared commit and unmerged v2.0 history.
The fork finding above was the exception, corrected in the inspected follow-up. V1 commit/narration
rules remain unchanged in the reviewed diff.

Making the existing pinned `sha2=0.10.9` dependency unconditional allows the
shared query/actor port on portable builds; it adds no new version, native worker,
model or network dependency. Inspection's existing public API is now compiled in
portable builds; callers already own their Engine, and this does not grant the
desktop renderer an inspector privilege. At the baseline, one stale module comment said inspection
never supplies generation context despite its new private actor port. The
coordinator clarified it in the inspected follow-up; it was not a runtime blocker.

## Test coverage read and reported execution

Read the 10 compiler cases covering eligible-only private canaries/count
noninterference, completed history, historical discovery, references/aliases,
mandatory limits, deterministic exact/lexical long-tail retrieval and 1,026 actual
accepted synthetic events. Read three production-context cases capturing the
actual director prompt through a synthetic provider, checking an old commitment
without hidden facts/full history/debug metadata, stopping before provider calls
when mandatory context cannot fit, and restoring the accepted-main v2.1 receipt.
The passive production trace test now expects Retrieval/Estimated rather than
pretending retrieval was not run. These source assertions are not independent
execution by this reviewer.

The coordinator reports a 220-test workspace pass, focused portable/default
checks of 32 plus 3, strict workspace Clippy/rustfmt, and an existing-model
production scene pass in 32.252 seconds. The reviewer subsequently read the
existing logs and JSON named below, counted 220 passed/zero failed/ignored across
31 test reports, and inspected scene_pass=true, quality_accepted=false and
network_blocked=false. The scene covers gift/refusals/secrets/cancel/restart/retry/
replay and uses safe fallback for both accepted narrations, with zero repairs.
The full worker SHA is
`add98cf02249141942c88e2517c2f5a4c9a91dbe9638bf7d3cd30c26916bce87`.
Last-role narrator metrics report 149 input/55 output tokens for gift and 154/48
for Dialogue. The probe does not retain director token metrics; these numbers
do not prove long-history real-token fit. Results are coordinator execution
evidence, read independently, not independently executed. They do not constitute
native frontend/IPC/render or narrative-quality approval.

Local artifact suffixes under the coordinator's source-context checkout:

| Artifact | SHA256 | Attribution |
| --- | --- | --- |
| target/context-scene.json | 23d5fc15e44a04937e20d6ae1948a86d41bd90be5a4148268c855a2a08e0cdfb | Existing CPU model/worker plus shared Engine/Store, before fork-only fix; production play unchanged by that fix |
| target/workspace-test.log | 04724887eab6b312b1de461a3718af679d1c3cc40580955241e61cdf42c388ae | 220 passed, before fork-only fix |
| target/workspace-clippy.log | cc4922f6bbbd8ab45223a8a8fc9891bbc4c568aab1e6a30e875e604a50c3fc24 | Strict workspace Clippy completed; coordinator invocation attribution |
| target/context-production-test.log | 83b317d6ec4b185d9b5dbceb00a991f21f4216ba363181afe4e5f9c0e1639117 | 32 passed |
| target/context-play-test.log | 301b62a3efcac36fcace86245f80630eecbd2ea216cf33015fe57a2102213db6 | 3 passed |
| target/context-promotion-test.log | 4d60f1159e5823ec15d196e7d734923d99bcd9ebae0500c7b5d56e91d0298049 | 32 passed |
| target/context-legacy-fork.log | 610a459caf65d41511bb80b363e4dc74552f2af958ca61057d6d3629832355be | Post-finding 38 passed at a46c1f4 source |

No independent rerun or model operation is claimed. Final source/test evidence
and owner acceptance remain the coordinator's publication responsibility.

Full M07 remains open: measured long-history actual tokenizer fit and usefulness,
SQLite FTS verification/parameterization, full alias registry, summary generation
and invalidation/resumable maintenance, semantic retrieval evaluation, durable
branch-history support, native/Android integration and genuine offline/physical
device/long-history performance qualification. The source explicitly reports
unsupported features rather than treating their absence as passed tests.

## Exact reviewed source hashes

SHA256 below hashes Git blob bytes at `d35c884`, independent of Windows checkout
CRLF. Follow-up fixes must identify their own source head and evidence.

| Repository path | SHA256 |
| --- | --- |
| crates/locallore/src/context_compiler.rs | 214bfd99ef7e7a17278c3ed40e9357b7cad99d401a370c3767fd2c71825d3c37 |
| crates/locallore/src/inspection_query.rs | 551c487fe57d41fe6544028298ad407a73f5d4d589d1180d6a06b34be855eea6 |
| crates/locallore/src/play.rs | 19f9bf210d7ab75126021d96bb8d486fcd1c3b06806fab7593bce20dbdf22774 |
| crates/locallore/src/engine.rs | 6ec23414e1efe8ac761067d9dceefea2823fa1e5506f0549989ab9f8533ebf46 |
| crates/locallore/src/lib.rs | 78d6ecf3568aea6a68a49fb87a0bd674e5c67cce1a302cc2e5eee58f3c6de151 |
| crates/locallore/Cargo.toml | b69cc06e8367195aa73aa0cbff9aed81e2486bb93922876766eeaa3ee163e758 |
| crates/locallore/tests/context_compiler.rs | 3b877f15593d0811cc6c3b1b61ae29333c8fc0f08ac7bd67c7962b7279d2b445 |
| crates/locallore/tests/context_play.rs | 4a850abc2ed62fa3b8674ad5be2c2691f6bf0754af90e1c0acb51e075d03e1d5 |
| crates/locallore/tests/production_turn_trace.rs | 217c071bb745bbf4c7e3523ad7db78acabf3fef12683cab5c52b0610d390cb9f |
| crates/locallore/tests/fixtures/accepted_play_v2_1.json | 3aefb5a8c1a9ad0f27b15d424dfcecf5f7fb58a639572758a6128fb75ace36d4 |
| native/llama-worker/generate.inc (unchanged native guard) | 55456ba808e2334125a74f5f6437bb562735cf1dbb7b6de2f5a297ae2b6250d2 |

The three follow-up Git blob hashes at `a46c1f4` are:

| Repository path | SHA256 |
| --- | --- |
| crates/locallore/src/engine.rs | 3c6c6da7ddbf1a138c129cd029a527dcdfdbd7c2cead6c87ffbf1ac81a5a2b5a |
| crates/locallore/src/inspection_query.rs | 1031879745a6d5ba0c650f073cb8fc1441592f88ebaa263f5511b06ec7afb068 |
| crates/locallore/tests/context_play.rs | a8f0302abac96eef6784e5098bfbe3c2f8d236f014787cae861299d066dc084f |

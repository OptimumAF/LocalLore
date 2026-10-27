# Initial story presentation — 2026-10-27

M09.02, supporting M09.03/M09.06 and M10.02. This focused packet is stacked on
unmerged PR#222 at07ec1e2f. Full milestone checklists remain unchanged.

## Implemented behavior and authority

The creation review adds plain/warm/brisk tone and exact phrases to exclude from
generated narration. Every edit requires an explicit native Review before
Create. Rust validates bounds and the complete derived seed, then checks exact
template/setup hashes before the existing atomic creation transaction. Default
plain/empty metadata canonicalizes to an absent seed field; old APIs, default
Seed bytes and exact retry behavior remain distinct and compatible.

Persisted presentation metadata is initial story configuration, not world truth,
belief, knowledge or director authority. The narrator receives a trusted tone
instruction and separately labeled literal phrase data. Accepted narration is
checked against Rust Unicode-lowercase substring exclusions, including typed,
staged, fallback and recorded-history paths. If approved-summary fallback is
also blocked, the turn fails without canonical effects. Evidence-only staging
remains private and cannot install canon. Settings cannot edit an existing
story through the creation API.

Presentation-enabled records use explicit2.7 memory/2.8 literal presentation
prompt identifiers and grounded-prose2.3 presentation policy, with an exact
seed-presentation SHA256 binding. Old literal construction is never repointed;
it refuses nondefault settings before provider work. Old/default record and
prompt encodings remain unchanged. Replay validates versions/bindings without
inference. Root wires current dispatch, actual commit routes and trace labels.

This is not semantic-topic filtering, Unicode normalization/full casefold,
player-input censorship or a model-quality guarantee. Original-premise
generation and broader character/content setup remain required work. See
[contract](STORY_PRESENTATION_V1.md), [ADR-0012](../adr/0012-initial-story-presentation.md)
and [fixed Android protocol](ANDROID_STORY_PRESENTATION_PROTOCOL.md).

## Verification recorded so far

Root's initial bounded compile check actually passes14791ms/worker0 with1955
unchanged tracked inputs and known cleanup/capture. It compiles all core targets
and features with Rust1.93.1, locked/offline dependencies; it is not a test run.

Native author focused checks subsequently pass17 cases on their own1957-input
source:6 new presentation cases and11 existing literal/exact-byte checks,
owner9990ms/worker0 with retained command/streams/maps. The original first
compilation failure used a host-feature-gated hashing helper. It remains failed;
using existing sha2 corrects it without adding a dependency. Author checks do
not establish integrated Host replay or Android qualification.

The first integrated workspace target actually runs12 independent cases:
11 pass/1 fails, owner22583ms/worker1,1960 sources unchanged, known capture and
cleanup. The failed assertion compared entire new preview rows to legacy rows,
although the factory appends explicit presentation-review metadata. Independent
review corrects only that oracle: exact legacy prefix, ordered presentation
suffix, and byte-identical default details. Full seed/hash/privacy checks remain.
The original failed output stays immutable.

Fresh integrated workspace execution then passes all12 cases,0 failures/skips,
owner8315ms/worker0 with1964 tracked inputs unchanged. Independent oracles cover
wire bounds/errors/hash derivation; default cross-API retry; no-write rejection;
scope/knowledge isolation; typed/staged/prepared/fallback guards; actual2.7/2.8
fake-provider provenance; forbidden narration in replay and a rechecksummed
archive; durable turn/fork/archive/reopen; explicit literal-version refusal; and
matching retry without a loaded provider. These are overlapping focused results,
not additional full-suite totals or physical/model evidence.

Android production and8 new JVM/8 fixed Android methods are integrated, with
source/UTF-8 checks by their author. They have not yet been compiled/executed at
this checkpoint. Root adds a separate closed presentation phase without changing
older phase rosters or any SDK/owner/class/output limits. Full Rust/Python,
frontend generation/validation, JVM/lint/APK/build and current-source emulator
gates remain pending. No prior source cohort is substituted.

Source, tests and contracts are committed/pushed incrementally. Private bounded
evidence is written on C:, with original failures preserved; no private model,
save, DB, image or raw device evidence is uploaded. No dependency is introduced
or repinned. Existing offline toolchains are reused. No merge, release, system
setting change, unrelated-emulator stop or server lifecycle action is performed.

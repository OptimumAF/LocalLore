# Staged Play frozen Core oracles — 2026-10-23

Refs #12 M08.03, #11 M07.01 consumer prerequisite, #29 D07.03/.04/.05
prerequisite. Status: **source frozen, UNCOMPILED / UNRUN**, not RED or a
qualification result. Coordinator-approved contract89c6a7d0051ae1fae18cefacdf2ea68c38d2e325
and Root claim #12 6377715621 allocate the new tests only. Agent
resource_metrics_review uses separate `test/m08-staged-play` /
`source-staged-play-oracles` at that exact base. Own ONLY new
`crates/locallore/tests/m08_staged_play.rs` and this document. Root owns all
Engine/Play/versions/Store/Host production, existing tests and integration.
Claims: #12 6377722950, #11 6377723127, #29 6377723262.

Frozen test source commit `fa0402637723455d412d474dbd875dbaee89843f`, SHA256
`2c7a47f29e18dce8db6e7acdc575e154a174648f6fdd02d79e1e70856cc8f17e`,
seven tests/467 lines. Source was frozen before coordinator implementation.
At the baseline `stage_play_v25` does not exist; this is intentional future-API
source, not evidence of an actual compile or runtime failure. All fixture data
and privacy canaries are original synthetic values.

## Bound interface and fixtures

The [approved stage contract](M08_PLAY25_STAGING_PROPOSAL_2026-10-23.md) freezes
`Engine::stage_play_v25(&Request,&Proposal,&dyn Fn()->bool)` and opaque read-only
`approved()` / `narrator_evidence()` getters. Tests serialize ONLY safe evidence
to serde Value; the opaque type is neither deserialized nor fabricated. Safe
JSON fields follow the approved proposal: version2, events with event_id and
outcome, observations, mechanical_summary; an observation has EXACTLY event_id,
actor, fact and proposition. They never serialize an Engine/canonical wrapper
as provider input. The actual native approved Receipt remains distinguishable
from sanitized narrator evidence.

Fixtures use the existing public typed Seed/Engine/author-correction API and
actual typed preview/commit for canonical setup; no SQL, forged Receipt,
canonical edits, provider, Host grant, source/hash relabeling or alternate
authority. The relic fact is discoverable at the player's real quay location,
known as A to player and Mira. An actual author child changes truth to B while
both retain observed A. A separate player-known secret and prior private
self-speech test that absent knowledge/history cannot leak through staging.

Manually constructed untrusted Proposals are input to actual Core validation,
not substituted provider output or accepted outcomes. The discovery positive
is checked against a separate real typed commit and its actorV2 discovery; it
does not accept expected JSON as authority. No inference is invoked.

## Frozen seven families

1. **Actual discovery:** old public preview still refuses Domain2 FreeText
   with Version. New stage produces event2/B while the source still remembers
   A. Approved events match a separately committed typed Core candidate and
   its event-specific actorV2 observed value; Mira stays A.
2. **No discovery:** Wait after a private historical utterance has no observation
   rows, old fact A, private truth B, player-known secret, fact identifiers or
   old speech. Its approved event/summary remain present.
3. **Speech:** actual literal Dialogue/Said exists in the approved Receipt but
   not in narrator evidence; utterance marker, Mira audience, request/proposal/
   input/listener/private truth/reason keys and fact values are absent. The safe
   event ID/outcome slot and delivery-only mechanical summary are positive.
4. **Event-specific binding:** actual typed double discovery produces two B
   bindings. Current single reobserve stages only new event4/B, not prior rows.
   Real B→A author correction retains observed B until single current discovery
   stages event5/A. Independently committed actual Core history retains old B
   and new A under their respective events; detached old evidence remains B.
5. **Actual source:** two real author children have identical scope/head/
   mechanical projection and identical Request/Proposal/approved event shapes,
   but different full canonical source identities. Staging each returns its
   own actual B or C value, never a projection/head keyed stale value.
6. **Admission:** wrong version, scope, expected head, proposal key and a valid
   but wrong finite Wait outcome reject with the existing closed errors;
   unsupported English refuses clarification and typed Actions refuse Agency.
   The native fresh API remains FreeText-only. Old preview refusal survives.
7. **Cancel/bounds/nonmutation:** always-cancel and panicking callback return
   Cancelled, retry can stage, and dropping the token leaves the complete source
   unchanged. A real author replacement at MAX_TEXT_BYTES2048 containing
   escaped controls survives exact safe JSON roundtrip, stays<=65,536 encoded
   bytes and is not truncated. Oversized2049 input refuses TooLarge. Every
   successful helper also checks exact canonical bytes, full accepted basis,
   canonical record count and approved identity before/after token drop.

## Explicit limits and deferred oracles

The finite fresh API permits one FreeText action, not typed multi-action Play.
Root explicitly confirmed that distinction. The double-discovery setup uses
existing typed canonical APIs, then stages ONE real current discovery. No new
typed admission was invented for the tests.

Encoded evidence cap is MAX_RECEIPT_BYTES65,536 using bounded JSON and no
truncation. The maximal escaped single2048-byte fact is below that cap; these
tests prove successful exact encoded output stays bounded, **not an actual
over-cap refusal**. No unreachable eight-discovery overflow fixture is claimed.
Provider context4096, role350, prompt/deadline budgets are separate and absent
from this pure Core stage execution.

Consuming-token full-source Stale, actual commit/cancel boundary, idempotent
recorded retry, persisted2.5 context_policy/version matrix, narrator2.2 prose/
fallback, replay/forgery, exact2.1–2.4 bytes and Host/Store/platform/decoder
closure await Root's exact PlayRecord2.5 fields and production allocation.
The same-source test above establishes source-correct *staging*, not a tested
consuming-token authorization fence. No fake metadata constructor or current
record fixture is invented to make an unavailable API appear complete.

## Actual checks and handoff

Actual commands were standalone parser/format and Git source checks only:

```text
rustfmt --edition 2021 --config skip_children=true crates/locallore/tests/m08_staged_play.rs
rustfmt --edition 2021 --config skip_children=true --check crates/locallore/tests/m08_staged_play.rs
git diff --check
```

Seven `#[test]` declarations, owned paths and final clean tree were inspected.
Rustfmt1.8.0-stable (01f6ddf758 2026-02-11), Git2.33.0.windows.2,
PowerShell7.6.5. Source-level name shadowing was corrected during initial
authoring before the first freeze; no assertion or executed failure was changed.
No Cargo/type check/Node/Gradle/provider/model/app/native/device/ADB/CUA/desktop/
transport/download/settings/protected resource/PR/merge action. No heavy slot
taken, no acceptance or model-quality claim.

After Root's implementation and explicit resource GO, the first proposed
actual command is `cargo test --locked --offline -p locallore --test
m08_staged_play --jobs 1`, then appropriate current/broad/strict checks. Preserve
the first actual compile/behavior failure before a narrow source or explicitly
documented fixture/API correction; do not weaken these assertions. Root owns
execution and integration. Release this test-only claim after source handoff;
milestone checklists remain unchecked.

# Pure core memory coverage v2

Status: implemented shared prerequisite for M07.03/.04, in_review. This module
does not persist a job or cache, call a model, consume summaries in production
generation, change canonical history, or complete M07. Claims/evidence belong to
#11, not this document as a second tracker. Existing packet-v1 APIs/bytes, Store
schema2 and the current compiler/Play path are unchanged.

## Authority and API

`locallore::memory_coverage` reads an already validated immutable Engine. The
caller chooses an appropriate actor; this native Rust API grants no wire/Lab
permission. All event-content selection uses the existing
`Engine::visit_actor_observations`. No witness/ancestry eligibility predicate is
copied into the module.

```rust
build_chunk(&Engine, &ChunkRequest, cancel)
    -> Result<Option<TypedPacket>, CoverageError>
verify_coverage(&Engine, &CoverageRequest, &[&[u8]], cancel)
    -> Result<CoverageRead, CoverageError>
VerifiedCoverage::recheck(&Engine, &CoverageRequest, cancel)
    -> Result<CoverageRead, CoverageError>
```

Both requests explicitly bind scope, current expected head and actor observer;
ChunkRequest additionally names `from_exclusive`. Head mismatch, wrong scope,
unknown observer, incomplete starting boundary and cancellation stop the call.
`None` means the start is already the head, without creating a zero-width packet.
An interval containing completed turns but no eligible events produces an empty
packet and advances its completed boundary.

TypedPacket is Serialize-only, including its engine-created AcceptedEvents.
Public typed fields remain untrusted and can be changed by a native caller.
VerifiedCoverage has private fields and no Deserialize/public construction. Its
packets, covered endpoint, verified head and exact raw-delta start are readable;
they confer no accepted-state authority. Recheck against the actual compiler
Engine is required before using a retained value, even when scope/head strings
match. A previous verification is not an origin/authenticity credential.

Packet binding includes the full typed seed SHA-256 and the private selected
ancestry chain SHA-256. The coordinator-owned lineage helper records selected
branch→root parent/fork tuples, including pre-birth fork caps, excluding unrelated
branches and current head. Thus mere parent advancement cannot change a frozen
child binding, while identical scope/receipts with a different actual ancestry
fails. Binding seed serialization streams to its hasher rather than retaining a
second complete seed buffer.

These hashes, completed-receipt counts and headers are **native cache validation
metadata**, not character prompt data or redaction/authentication. A future
compiler must deliberately serialize permitted entries; it must not send an
entire packet/header to the model or ordinary logs. Mandatory current facts,
state, beliefs, relationships and promises must still come from the actual Engine.

## Deterministic packet and closure policy

Version2 / `deterministic-event-extractive-v2` is scene-window extraction only.
No generated prose, chapter/entity reflection, model/prompt invocation or previous
summary input is used. Entries preserve original accepted observations, distinguish
statements and beliefs, and coalesce adjacent eligible TimeAdvanced effects only
when their time endpoints match. Coalescing retains every original scoped source
reference; it does not claim an unobserved event.

| Public bound | Value |
| --- | ---: |
| Completed receipts per chunk | 128 |
| Eligible events per chunk | 256 |
| Encoded eligible source events per chunk | 1,048,576 bytes |
| Encoded packet | 65,536 bytes |
| Supplied prefix packets | 32 |

Sources are ordered original `Scope + sequence`, never globally resolved by
sequence alone and never relabelled into a child. The source digest is SHA-256
over the domain string `locallore-memory-coverage-v2` plus NUL, then little-endian
u64 length and typed JSON encoding of `(scope, observer, seed_sha256,
lineage_sha256, from_exclusive)`, then each eligible AcceptedEvent's little-endian
u64 encoded length and original typed JSON bytes, then the through endpoint as
little-endian u64. Typed struct order and ordered maps/sets define this v2 method;
changing that interpretation requires an explicit version change. A digest can
be recomputed by an attacker and never replaces Engine source verification.

The builder greedily accepts complete turns. It closes at exactly128 receipts or
256 eligible events, even at EOF. If the next complete turn would exceed event,
source-byte or encoded-packet budget, it seals the preceding packet and records
that next turn's endpoint as a closure proof. No partial next turn is included.
It reserves64 bytes while measuring candidates so the longer closure/proof marker
still fits. Encoding uses a bounded writer, including JSON escape expansion.

An unrepresentable first complete turn yields fixed `Budget`, without a packet
or progress. A private reduced-budget test proves this branch using the same
builder and a real accepted turn; it does not demonstrate that today's public
request limits can produce a one-turn64KiB overflow.

EOF alone yields `OpenTail`, never a sealed immutable chunk. A storage maintainer
should key windows by their start, reuse the sealed prefix and replace/rebuild
the single open tail on extension. Appending one new immutable EOF packet on every
commit would wrongly exhaust the partition after32 small commits. The core does
not implement that storage policy; its tests demonstrate the reusable keys and
boundaries needed by it.

## Verification, old prefixes and exact raw fallback

Verification bounds each input before parsing, reuses the existing recursive
unique-JSON parser, structurally reads its header, then independently rebuilds
the packet from Engine observations. The entire rebuilt JSON value must match;
unknown fields, omitted/added/duplicated sources, changed entries, altered closure
and forged/recomputed checksums cannot establish coverage. Object-key order alone
does not alter JSON value equality. AcceptedEvent/Effect are not deserialized as
canonical authority.

A supplied set must start at zero, be ordered and adjacent, and have no overlap.
Only its final packet may be an OpenTail. Verification rejects the whole set to
raw fallback from zero if a packet or that coverage contract fails. A verified
prefix ending at C leaves the exact raw delta `(C, actual_head]`; it does not
claim the later head covered.

For an old OpenTail, verification reconstructs `Engine::at_revision(C)` from the
actual current history and rebuilds the chunk there. This permits an unchanged
old prefix after head advancement without pretending C is the current authority
head. For sealed chunks it repeats deterministic closure against the actual
Engine. Event/source/packet overflow closure requires its real next complete turn;
a historical Engine ending before that lookahead returns `UnprovableClosure`
raw fallback. Exact receipt/event quantum closure needs no future proof. Changing
an arbitrary small EOF chunk to a sealed marker fails.

Missing, malformed, unsupported, over-budget, wrong-binding, gapped, overlapping,
unprovable or source-mismatched **cache data** returns a fixed RawFallback reason.
Scope/head/observer/source errors and cancellation remain errors, not cache misses
to silently ignore. A future consumer must never hide a failed canonical read,
omit mandatory evidence, or generate from an incomplete partial result. If exact
raw fallback exceeds its own safe budget, generation must stop safely.

## Cost and remaining integration

This is a correctness/representation contract, not a speed measurement. One chunk
uses one existing visitor pass; that visitor may scan the entire retained history.
Verifying32 chunks can repeat those scans. An old open tail additionally replays
a historical Engine. Chunk candidates, source buffers, serde trees and read clones
add allocations; encoded limits are not heap/RSS bounds. Replay, metadata scans,
hashing and an individual serialization remain synchronous. Cooperative checks,
including panic-as-cancellation, do not establish a hard whole-operation deadline.

Next coordinator-owned work is schema3 migration/backup and durable job ledger,
coherent Store preparation/publication/read wrappers, atomic packet+cursor
checkpoints, deletion integration with #81/#82, then actual Host/Workspace/compiler/
Play consumption with a versioned prompt. Jobs must not use cache rows as a second
ledger. Playable archives continue excluding jobs/caches; source schema3 will be
honestly unsupported by older schema2 clients under today's validator. No archive
version/compatibility policy is changed here.

Future compiler integration must retain current mandatory state, exact evidence
and delta/fallback, deduplicate by original scoped source identity, and attribute
summary versus raw retrieval honestly. Production forwarding, durable cancellation,
stale publication, restart/process-death, platform parity, quality and full M07
acceptance remain separate, unperformed gates for this pure module.

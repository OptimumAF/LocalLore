# D05 verified memory inspection v1

Status: source contract frozen before implementation; compilation and execution
are UNRUN. This is the shared Host slice for D05.05/.06/.07, D06.04/.07 and
M07.03/.04 inspection only. Base: accepted `3f75b5d673512b165e18b2b1e34d3deafc69067a`.
The native command, frontend and their qualification are separate work.

## Native Rust interface

Module: `locallore::host::memory_inspection`. These requests are plain Rust,
without Deserialize, JsonSchema, HostCommand variants or a serialized grant.
The selected Host session remains a separate argument.

```rust
pub struct MemoryInspectionRequestV1 {
    pub version: u16,
    pub scope: Scope,
    pub expected_head: u64,
    pub observer: Observer,
    pub binding: Option<String>,
    pub view: MemoryInspectionViewV1,
}
pub enum MemoryInspectionViewV1 {
    Packets { cursor: Option<String>, limit: u16 },
    Entries { packet_index: u8, cursor: Option<String>, limit: u16 },
    Source { packet_index: u8, source: SourceRef },
}
impl Host {
    pub fn memory_inspection(
        &self,
        session: &str,
        request: &MemoryInspectionRequestV1,
        cancel: &dyn Fn() -> bool,
    ) -> Result<MemoryInspectionReplyV1, MemoryInspectionError>;
}
```

Requests are Clone/Debug, not wire authority. Observer must be exactly Player.
Character (including the actual player ID) and Omniscient are Forbidden before
the persistence/cache/source read. Trusted Host Story Lab grant is required.
The selected session must exist and match scope; Domain2 is Unsupported before
packet retrieval and again on the returned snapshot. Player identity comes from
the actual selected seed, with no caller ID/name convention.

## Future strict command shape

This packet does not register a command. The future native leaf parses raw UTF-8
at most4096 bytes with recursive duplicate-key rejection and closed keys before
calling this method. Native window/permission fences remain that leaf's job.
It accepts action `packets`, `entries` or `source`, and these exact objects:

* Common: `version:1, session, scope:{story,branch}, expected_head,
  observer:{kind:"player"}, binding:null|64-lowercase-hex`.
* Packets adds `cursor:null|string, limit`.
* Entries adds `packet_index, cursor:null|string, limit`; binding is non-null.
* Source adds `packet_index, source:{scope:{story,branch},sequence}`; binding is
  non-null. No cursor, search, arbitrary view or extra query field.

Session/scope IDs use existing Core ASCII identifiers (1..64 bytes). Integers
must be JSON integers: version1, head0..9007199254740991, source sequence positive
and no greater than head, packet_index0..31, limit1..64. Negative, fractional,
unsafe and overflow values are rejected, never cast/coerced. Cursor at most128
UTF-8 bytes. No paths, SQL, provider, policy, prompt, consent or permission keys.
The typed Host method independently validates all representable limits.

## Serialize-only reply

`MemoryInspectionReplyV1` is internally tagged by `kind`:

* `Page(MemoryInspectionPageV1)`, kind `memory_inspection`;
* `Source(MemoryInspectionSourceV1)`, kind `memory_source`.

Page fields are exactly `version,session,scope,head,observer,privacy,binding,
coverage,view,packet_index,total,rows,next_cursor`. Version1; observer is the
actual native player ID; privacy `player_visible`. View is `packets` or `entries`.
Packet index is null for packets, actual index for entries. Total is the number
of eligible rows in that view, not a job count. The response has at most64 rows.

Coverage fields: `status,verified_head,covered_through,raw_delta_after,fallback`.
Status `verified` uses the actual rechecked proof's three getters and null
fallback. A valid prefix below head remains verified with an exact raw delta.
Status `raw_fallback` has null verified_head/covered_through, raw_delta_after0,
and one actual reason: missing, budget, malformed, unsupported, binding, gap,
overlap, open_tail_before_end, unprovable_closure or source_mismatch. It has no
packet rows; entries/source return Unavailable. Rejected cache payload is never
returned. Cache presence is not an execution/knowledge/quality grant.

Packet row, kind `packet`: `index,version,method,from_exclusive,through_revision,
receipt_count,closure,entry_count,source_event_count`. Each field is copied or
counted from an actual TypedPacket after recheck. Entry row, kind `entry`:
`packet_index,index,value`, where value is the actual Core Entry (its existing
class/origin/SourceRef/AcceptedEvent representation). Entries remain derived
extractive observations, statements or beliefs; no semantic-summary claim.
No seed, seed/lineage hashes, raw history basis, job or model metadata is exposed.

Source fields: `version,session,scope,head,observer,privacy,binding,packet_index,
source,matched,page`. The source must be an exact member of the actual packet's
source_events, including original scope. On the SAME snapshot Engine, run actual
Query2 History, Player, expected_head=head, at_revision=packet.through_revision,
limit64, cursor null and fixed literal search `"sequence":N,`. Matched means
Page2 contains the exact Event row's scope and sequence; otherwise return closed
Unavailable (never a successful source proof). No coincident sibling
event or reconstructed row is substituted. Page is the actual Query2 Page,
with its existing privacy/version/cursor/budget behavior. No inspection grant is
added to NPC context and no independently loaded second Engine is queried.

## Coherence, bindings and paging

Use existing Host::generation_snapshot and recheck VerifiedCoverage on that
Engine with actual scope/head/player. No new Persistence or Store accessor is
needed. No job ensure/step/admit/prune, provider, artifact or canonical write.
Job status is deliberately not joined to this snapshot using a separate read.

The binding is a namespaced SHA256 of a closed, length-delimited stream:
session, scope, head, actual player, full actual seed, actual memory lineage,
complete canonical_records, then exact rechecked packet bytes or fallback.
Source serialization is streamed and bounded to64MiB total; each existing packet
is at most65536 bytes and at most32 packets. Cancellation is checked throughout.
The opaque accepted_history_basis receives no getter/Serialize change. This
binding is a stale-read identity, not a signature, authentication or execution
capability. It changes on same-head accepted-history/seed/lineage replacement,
cache publication or fallback change. Historical event-only packet hashes alone
are insufficient for this purpose.

Initial packets may have binding null only with cursor null. Any supplied
binding must be canonical lowercase64hex and match freshly recomputed state.
Entries/source require it. Cursor `mp1:<positive canonical decimal offset>:<hex>`
is a stateless digest of binding/view/packet/limit/offset, maximum128 bytes.
Offset must be below total. Cross-session/source/view/packet/limit cursors fail.
No retained reader registry, TTL, cache write or persistent cursor is introduced.

Whole reply compact JSON is at most65536 UTF-8 bytes. Paging appends only whole
rows that fit including the next cursor and wrapper; a single row that cannot
fit returns TooLarge. There is no truncation, zero-progress page or loss of
provenance. Source wrapper plus actual Page2 obey the same total cap. All emitted
JSON integer values must be JavaScript-safe (signed values may be negative down
to -9007199254740991). Unsafe values fail TooLarge; values are never normalized.

## Errors and cancellation

Closed native error enum (Serialize snake_case; Display fixed variant name):
Version, Forbidden, Closed, Scope, Stale, Unsupported, InvalidInput,
InvalidCursor, Binding, TooLarge, Cancelled, Integrity, Unavailable, Busy,
Database, Full, Internal. No underlying text/path is returned. Known persistence
errors map to these; unexpected override failure/panic is Internal. Query2
InvalidBoundary/Integrity maps Integrity; UnknownObserver maps Forbidden;
UnsupportedBranch maps Unsupported; other query input errors map InvalidInput.

Cancellation is sticky; a true result or callback panic means Cancelled even
if a later callback returns false or an override ignores it. Snapshot overrides
are already contained inside Host's lock and cannot poison it. New callbacks
must be short and cannot reenter Host/Store. Pure output/hash loops poll them.
No reads are continued after an observed cancellation. A successful response
describes one immutable snapshot, not a live subscription; subsequent bound
requests must freshly validate.

## Frozen source acceptance

NEW actual Repository/SQLite test source will cover absent cache with no job
admission; real completed coverage metadata/entries/exact Query2 source; verified
prefix plus raw delta; changed cache/head binding and cursor rejection; Lab,
player-only, scope and D2 fences; cancellation/panic; bounded requests/whole
output; canonical/job/cache byte invariance on read. No canonical SQL fabrication,
model/provider, frontend mock or device inference is acceptance evidence here.
Unsupported or inaccessible fault injection is reported rather than invented.

All checks in this packet remain UNCOMPILED/UNRUN by its source author. Root
owns actual compilation, frozen failures/corrections, security review and final
native/frontend integration. This partial slice does not complete D05/D06/M07,
does not make Play MemoryMaintenance stages run, and adds no Domain2 support.

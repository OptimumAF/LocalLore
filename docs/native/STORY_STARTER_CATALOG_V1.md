# Original starter catalog — v1

Supporting M09.02, with M09.03/M09.06 interaction coverage. This extends the
[named creation contract](STORY_CREATION_CONTRACT_V1.md); it does not accept
arbitrary seeds or edit a retained story. Rust owns the catalog, template bytes,
rules, observer-filtered preview and transactional creation.

The additive Host envelope-v1 command `{"op":"story_templates"}` accepts no
other fields. Its result has exactly `version:1` and `templates`. Each descriptor
has exactly `template`, `default_title`, `description`, `profile`. The bounded
catalog contains at most eight unique descriptors within 16384 UTF-8 bytes.
The initial order is:

| Template | Default title | Rules |
|---|---|---|
| `lantern-quay-v1` | Lantern Quay | `fantasy_v1` |
| `bracken-harbor-v1` | Bracken Harbor | `narrative_v1` |

Bracken Harbor is original repository content. Narrative rules have no numeric
combat attributes, energy budget or abilities; the existing engine still
validates inventory ownership, commitments, knowledge and scoped consequences.
This is a real native rules selection, not merely a different display label.
NPC-only facts and beliefs stay outside the player's setup preview. A character's
belief never becomes world truth through selection or preview.

`story_template` and `create_named` keep their original exact field sets. They
now recognize either closed template ID. The hash binds the selected fixture's
exact bytes before scope substitution. Lantern Quay's bytes and existing preview
remain compatible. Legacy `create` remains unchanged. Catalog/preview reads do
not allocate sessions, create stories, invoke inference or perform network work.

Creation retains the existing `quay-{creation_id}` / `main` opaque identity for
both templates. The prefix is not a rule or template selector. The Store's exact
full-seed comparison rejects a cross-template retry of an existing identity;
it cannot reset accepted events. Exact retained retries preserve the current head.
There is no new migration, dependency, automatic retry or alternate authority.

Android obtains the production catalog from Rust. It bounds and freezes the
descriptors and details, checks that a returned preview matches its selected
descriptor, and requires explicit confirmation of the exact displayed review.
A stale selector, editor callback or Create action cannot borrow a newer review.
Selection is disabled while loading, creating or closing; cancellation/disposal
cannot publish a late preview or automatically create a story. An uncertain
dispatched creation retains the existing refresh-on-close behavior.

The old fake-port `preview()` interface remains compatible. Only its default
catalog capability may return null to identify a legacy test port; the real
DurableGateway overrides it with a required native catalog. Malformed data or
native failures cannot fall back to a fabricated catalog.

The debug process probe treats the new read-only catalog operation as metadata,
like capabilities. Its existing fourteen counters and probe-v2 schema remain
unchanged. Earlier lifecycle proofs retain their original source attribution.
New chooser Android methods are separate from the fixed existing nineteen-method
creation protocol; compilation is not runtime qualification.

Custom premise, tone/content boundaries and player editing remain pending.
Host and fake-provider checks do not establish model quality, physical-phone
performance, ARM64 execution or complete M09 acceptance.

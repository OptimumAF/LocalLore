# Player name in initial story setup — v1

M09.02, with M09.03/M09.06 interaction coverage. This extends the
[original starter catalog](STORY_STARTER_CATALOG_V1.md) and
[explicit creation contract](STORY_CREATION_CONTRACT_V1.md). It does not replace
their legacy operations or accept a replacement seed. Runtime qualification is
recorded separately from this contract.

The player may edit their character's display name while reviewing a new story.
Rust derives a candidate from the selected bundled template, changes only
`seed.actors[seed.player].name`, validates it and supplies the player-visible
preview. Entity IDs, profile, abilities, inventory, locations, facts, beliefs,
commitments, NPCs and knowledge eligibility are unchanged. The name is canonical
initial character state, not a command, ability grant, fact or NPC instruction.
There is no existing-story rename or backdated author edit.

## Additive Host envelope-v1 operations

`story_setup` accepts `template` and optional nullable `player_name`. Omission
or null requests the bundled player's default name. A non-null name must be a
string; unknown fields are refused. The operation creates no session, stored
story or inference request. Its reply has exactly these nine fields:

```text
version: 1
template: selected closed template ID
template_sha256: lowercase SHA256 of the exact bundled fixture bytes
setup_sha256: lowercase SHA256 of the derived initial setup
default_title: selected starter's default save title
description: selected starter's public description
profile: selected starter's native profile
player_name: exact validated player display name
details: player-visible initial-state rows
```

Names use at most64 Unicode scalars and256 UTF-8 bytes, are nonempty and have no
outer whitespace, controls, line separators or bidi embedding/isolate controls.
They are not trimmed or normalized. The256-byte ceiling also preserves the
existing context compiler's canonical actor-name bound. Titles retain their
separate80-scalar/320-byte limits. Invalid names return bounded `InvalidInput`
without echoing the input. Preview limits remain64 rows,2048 UTF-8 bytes per row
and16384 total serialized bytes. Only player-self and player-eligible content
enters the preview; a name cannot grant access to another character's secrets.

The setup digest is SHA256 of this unambiguous byte sequence:

```text
UTF8("locallore/player-setup/v1") || 0x00 ||
ASCII(template_sha256) || 0x00 ||
serde_json::to_vec(customized_seed_before_scope_substitution)
```

The ordinary Rust Seed representation and its sorted maps/sets are used. The
template digest binds exact source fixture bytes separately from the customized
seed serialization. The creation ID, new story scope and save title are not
substituted into this read-only digest. A hash is an equality/freshness binding,
not authority to import a caller-supplied seed.

`create_configured` requires exactly `template`, `template_sha256`,
`setup_sha256`, `player_name`, `title` and `creation_id`. Rust reconstructs the
candidate, validates its name and engine, and checks both hashes before any
persistent write. It then uses the same validated `NamedStarter`, session
prechecks and Store transaction as `create_named`. The reply remains exactly
`session`, `scope`, `revision`, `created`. The ephemeral Host refuses creation,
as it does for named persistent creation.

The32-lowercase-hex creation ID still identifies `quay-{creation_id}/main`.
Exact title/full-seed comparison makes matching retries retain accepted history;
a changed name under an existing ID cannot replace the seed or reset progress.
Configured creation using the bundled default name and legacy named creation
produce the same Seed, so exact retries remain compatible across those APIs.
Whole-story deletion retains its existing identity-forgetting semantics.
No migration, new Seed field or second database writer is introduced.

## Android review and consent

The production gateway reads strict native setup previews; malformed responses
and native failures cannot fall back to fabricated metadata. Only legacy test
ports may lack the new setup capability and retain the existing starter/title
flow. The old preview/catalog/creation wire field sets stay unchanged.

Editing the name invalidates old Create consent immediately. A dirty name must
be explicitly reviewed before Create becomes available. Read work captures the
exact name, selected starter and immutable request; a late result, retained
callback, changed title or replacement review cannot borrow newer consent.
The returned name and public starter descriptor must match the requested setup.
The creation ID and edited save title survive a successful read-only review.
Valid custom names survive starter changes; invalid drafts stay visible and
cannot be committed without a successful valid review.

Cancel before creation drains read work without creating a story, changing the
selection or dropping a play draft. After dispatch, existing uncertain-creation
refresh and finite-work ownership rules apply; cancellation never claims to
roll back a stored story. Disposal prevents publication. The native engine
remains the authority when Kotlin presentation validation has passed.

The debug process probe treats `story_setup` as read-only metadata and counts
`create_configured` as named creation. Its existing fourteen counter keys and
probe-v2 schema do not change. New player-setup tests have a separate fixed
protocol; existing creation19, chooser7 and broad89 rosters retain their scope.

Original premise generation, tone/content-boundary configuration and broader
character editing remain required M09.02 work. This contract does not advertise
them as available or establish real-model, phone, ARM64, accessibility, OS-death,
joined-drain or full-milestone qualification.

# Initial story presentation — v1

M09.02, supporting M09.03/M09.06. See ADR-0012 for authority, versioning and
remaining gates. This is additive to the player-setup v1 contract.

## Native data and matching

`StoryPresentationV1` has exactly `version:1`, `tone` (plain/warm/brisk), and
`excluded_phrases` (ordered strings). All fields are required when the object
is supplied. At most8 phrases,64 Unicode scalars/256 UTF-8 bytes each and1024
total UTF-8 bytes are permitted. Phrases must be nonempty with no outer
whitespace, controls, line separators or bidi embedding/isolate controls. No
trimming, normalization or sorting occurs. Duplicates under Rust
`str::to_lowercase()` are invalid. Original spelling/order stay hash-visible.

Narration matching is `lower(text).contains(lower(phrase))`, with Rust Unicode
lowercase rules. This is a literal substring, not a word/topic classifier or
full casefold. `SS` differs from `ß`; `İ` lowers to `i` plus combining dot.
Exclusions apply to generated/fallback narration and acceptance/replay guards,
not player-authored input, initial review rows or canonical inspection facts.
Tone is trusted enum guidance for the narrator alone, never director authority.

Default `{version:1,tone:"plain",excluded_phrases:[]}` canonicalizes to absent
`Seed.presentation`. Other valid settings are persisted with the initial seed.
Engine admission refuses invalid metadata or a present default object. No
existing-story edit operation is provided. Retry/fork/archive/reopen preserve
the same configuration and use the existing storage owner.

## Additive host envelope-v1 operations

`story_presentation` accepts `template`, optional nullable `player_name`, and
optional nullable `presentation`. Missing/null values request their bundled
defaults. It returns exactly10 fields:

```text
version, template, template_sha256, setup_sha256, default_title,
description, profile, player_name, presentation, details
```

`presentation` is always the explicit three-field object, never null. Review
rows remain player-eligible with existing64-row/2048-byte-row/16384-total caps.
Settings are displayed as configuration, not newly established world facts.

The setup hash is SHA256 of:

```text
UTF8("locallore/story-presentation/v1") || 0x00 ||
ASCII(template_sha256) || 0x00 ||
serde_json::to_vec(derived_seed_before_scope_substitution)
```

`create_presented` requires exactly `template`, `template_sha256`,
`setup_sha256`, `player_name`, `presentation`, `title`, `creation_id`. Native
reconstruction, validation and both hash comparisons precede Store access. The
reply remains exactly `session`, `scope`, `revision`, `created`. The ephemeral
host refuses creation. Matching defaults compare equal to the old full Seed for
cross-API retries, although the new review digest has its own domain. Changed
settings under an existing creation ID cannot replace retained history.

`story_presentation_view` requires `session`, `scope`, `expected_revision`.
Its exact reply is `version:1`, `scope`, `revision`, `presentation`. The session,
story/branch and revision must match. It returns current native initial
configuration without exposing a Seed, hidden facts, beliefs or history.

Unknown/missing object fields, wrong JSON types and unknown tone values are
malformed. Parsed unsupported versions, bounds, unsafe text and duplicates are
`InvalidInput`. Stale hashes are `Stale`. Existing `story_setup`,
`create_configured`, catalog, preview, snapshot and probe field sets are unchanged.
The probe ignores both new read operations and counts `create_presented` as
named creation without adding a fifteenth counter.

## Android consent

Name, tone or phrase edits invalidate Create consent and require explicit native
Review. Invalid raw phrase drafts remain visible; no silent trimming or dropping
blank rows occurs. A review captures the exact settings/name/title/creation ID
and descriptor. Stale results and retained callbacks cannot borrow replacement
consent. Cancel drains read work and preserves the selected library/play draft;
uncertain creation retains existing refresh rules. Production cannot fabricate
metadata after native failure. Legacy fake-port capability remains distinct.

Actual check results and fixed Android execution are recorded separately. This
contract does not advertise original-premise generation, semantic-topic safety,
post-creation editing, physical/model/ARM64 or complete milestone readiness.

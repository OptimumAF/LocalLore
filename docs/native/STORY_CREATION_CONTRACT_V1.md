# Explicit starter creation — v1

M09.02 supporting slice, stacked on draft PR #212. This is an implementation
contract, not executed evidence or acceptance of full story customization.

The original starter remains `lantern-quay-v1`, fantasy rules, Rowan and the
existing seed. The additive [original starter catalog](STORY_STARTER_CATALOG_V1.md)
adds explicit selection of an original narrative-rules starter while retaining
this wire format and Lantern compatibility. Premise/tone/boundaries/player
editing are not advertised as available. Gameplay remains local; this API does
not invoke a model, accept arbitrary seeds or alter existing canon.

Two new closed Host envelope-v1 operations:

- `story_template`: exactly `template`. Returns exactly `version:1`, `template`,
  `seed_sha256`, `default_title`, `description`, `profile`, `details`.
  The SHA256 binds the exact bundled template bytes before scope substitution.
  The read creates neither a session nor a persisted story. Details contain
  only current player-self, owned inventory, player-known facts/beliefs and
  player-side commitments/relationships, never the full Seed or NPC beliefs.
  Native limits are64 details,2048 UTF8 bytes each and16384 total preview bytes.
- `create_named`: exactly `template`, `seed_sha256`, `title`, `creation_id`.
  It is available only on persistent Hosts. Native validates the starter/hash,
  then title and32 lowercase-hex creation ID. It maps to `quay-{creation_id}`,
  root `main`. The reply is exactly `session`, `scope`, `revision`, `created`.
  `created` means this transaction inserted the row. On a matching retry the
  revision is the current accepted head, not necessarily0.

Titles are untrimmed input: reject empty, outer whitespace, controls, line
separators and bidi embedding/isolate controls, more than80 Unicode scalars or
320 UTF8 bytes. Do not silently normalize. A JSON malformed surrogate refuses
at parsing; Kotlin rejects unpaired surrogates before sending. These are named
creation UI bounds; existing generic Store title rules are not changed.

Existing-row lookup and exact title/root/full parsed Seed comparison precede
the256-story cap and share one IMMEDIATE transaction with insertion. A valid
different title/seed returns DuplicateStory without replacement; corrupt stored
seed returns Integrity. Matching retries at catalog capacity succeed. The
Store helper is trusted Rust code, not an arbitrary seed import wire operation.
Existing legacy random `create` remains compatible. There is no migration.

Host prechecks session allocation/ID capacity before persistent creation. It
still checks Store on an attached matching scope, then refreshes/reuses that
session; retries cannot multiply sessions. A newly required attachment can
refuse SessionLimit/IdExhausted before writing. Resume after transaction commit
may observe an advanced head or a concurrent safe read failure. A lost reply
does not authorize another random creation. Idempotency holds while the exact
story remains retained; explicit complete deletion forgets its creation ID.
No tombstone across whole-story deletion or arbitrary-ID retention is promised.

The Kotlin interface is `StoryCreationGateway.preview/create`, with immutable
`StoryCreationPreview`, `StoryCreationRequest` (preview/title/creationId) and
`StoryCreationClose` (optional SavedSnapshot,refreshRequired). Controller state
and dialog callbacks use exact captured request identity for Create. A title
edit uses only its still-current preview/creation ID; old confirmation cannot
borrow the updated title. The creation ID is generated once per new review.

Open review is allowed from an empty persistent library without a selected
story/provider. Loading/review blocks play, switching, records, archive,
deletion and forks. Cancel before Create drains read work, preserves the current
selection/draft and causes no write/automatic refresh. Once Create starts,
close/cancellation waits for the finite operation and reports uncertainty if
the result was not observed; it never claims rollback or automatically retries.
An uncertain error consumes the confirmation and requires close/refresh.
Disposal prevents publication; existing transport ownership fences remain.

No source-pinned host/JVM test substitutes for actual Compose/JNI/phone testing.
Native10, retained-archive2 and the new story-creation19 have distinct gates.
See the [dated execution report](ANDROID_STORY_CREATION_VERIFICATION_2026-10-26.md).
PR #212's original source/APK/preparation results keep their original attribution;
they are not relabelled for this packet.

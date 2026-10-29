# Original initial-world authoring contract v1

Refs #13 M09.02/M09.06; #14 M10.02/M10.03 support.
[ADR-0013](../adr/0013-original-story-authoring.md) records authority and recovery.
Authoritative shapes/limits live in `story_authoring.rs`; Host commands remain
inside the closed version1 envelope. No paths, Seed JSON, SQL or model handles
are accepted from the UI.

| Operation | Input | Successful data |
|---|---|---|
| `authoring_capabilities` | none | available, nullable provider, max_tokens1024 |
| `authoring_begin` | typed input | opaque job, input_sha256, provider |
| `authoring_generate` | job | job, echoed input, proposal, provider |
| `authoring_review` | job, typed edited input/proposal, title | job, review_sha256, echoed input/proposal/title, labeled details |
| `authoring_create` | job, review_sha256,32 lowercase-hex creation_id | session, scope, revision, created |
| `authoring_cancel` | job | cancelled; false means creation already won |
| `authoring_status` | job | job, phase, nullable error |

Inputs contain version1, original premise, player name/description, optional
cast hints, existing rule profile and existing presentation settings. The
model proposes locations, player location, characters/descriptions, directed
routes, facts with explicit known-by/discovery locations, character beliefs
with confidence, and possessions with ownership/optional return obligation.
Temporary actor0 is the player; subsequent actors are proposal characters.
Locations are zero-based proposal references. These are not canonical IDs.

Native limits: input4096 bytes, premise2048 UTF-8 bytes/1024 scalars, names256
bytes/64 scalars, descriptions512 bytes, at most3 cast hints; proposal8192
bytes,1–4 locations,1–3 NPCs,8 routes,8 facts,6 beliefs,4 possessions. Prose
fields are bounded single paragraphs without controls/bidi or outer spaces.
Origin is at most32768 serialized bytes. Oversized combinations refuse without
trimming or partial application. Duplicate names/references, inaccessible
locations, foreign fields/versions and unsupported mechanics fail closed.

The author request uses role `author`, prompt/schema `initial-world-v1`, pseudo
scope `author-draft-{job}/draft`, revision0,1024 output tokens,8192 output bytes,
120-second deadline and one delivery/no repair. No actual story exists yet.
The local owner keeps old play budgets and handles metadata cancellation with
the exact author job, never a fabricated turn scope. Local and scripted modes
are labeled accurately; unavailable inference never selects a cloud backend.

Compose edits descriptive fields using names and explicit knowledge choices,
never raw canonical Seed JSON. It freezes nested data and checks captured
state/review identity before callbacks. Create consumes one rendered review;
invalid edits, stale callbacks, cancellation and disposal cannot borrow a newer
review or creation key. An uncertain create triggers coherent library recovery,
not a blind new key or another model call. Uncommitted draft state is not yet
durable across app process death.

Ordinary form callbacks identify an explicit text field, absolute choice or
toggle and apply it to the latest draft in the same editor epoch. This preserves
rapid edits returning to the rendered value and repeated toggles. Structural
row edits retire that epoch; generation, review, creation and cancellation also
fence retained callbacks. Native review and Create retain exact consent checks.

Creation scope is `original-{creation_id}/main`. Root seed/entity identity is
derived by Rust from the full reviewed origin. A complete exact retry retains
accepted history. Different hidden content, visibility, beliefs, configuration
or title cannot overwrite the same creation identity. Whole-story deletion
forgets that identity under the existing Store policy; recovery alone cannot
recreate a missing story.

Successful recovery consumes the same live reviewed job, binding its creation
ID/hash. That consumed job can retry only its exact target, even if another
stored story has the same initial origin. Recovery by an absent/foreign job
does not consume an unrelated draft.

Native `play_snapshot.player.observer` is an actor ID assigned by Rust, not a
literal `player` constant. The gateway binds that bounded ID to its attachment,
session and scope, with atomic publication checks after suspended reads. The
record/fork contracts' semantic `player` lens labels retain their meaning.

The fixed emulator phase `original-story` runs exactly8 methods across
OriginalStoryWireTest (3), OriginalStoryDialogTest (2) and
OriginalStoryMainActivityTest (3). It requires a new owned API35/x86_64 guest,
current build/native prerequisites, user0 and absent verification packages.
It retains the existing180s class/850s SDK/900s phase bounds and measured SDK2
capture protocol. Exact source rosters, original JUnit/client raw bytes,
known owners/closures and server observations must validate. This phase does
not qualify real inference, OS-death, physical/ARM64, accessibility or full M09.

# ADR-0013: Native-reviewed original initial worlds

Status: implemented; integrated qualification in progress; owner acceptance pending.
Refs #13 (M09.02/M09.06), #14 (M10.02; supporting M10.03).

Bundled starter review cannot create an original premise and cast. A caller-
supplied Seed or Kotlin-generated world would also bypass the engine's initial
rules and visibility boundaries. Add a bounded pre-story authoring job owned by
Rust, using the existing provider interface and local inference owner.

The author role receives only a validated new-story input and a closed proposal
schema. It receives no existing story, private database, filesystem operation,
tool, accepted event, arbitrary ability or numeric resource capability. Rust
assigns content-derived opaque entity IDs and a fixed mechanical baseline:
one unit per possession, no healing flag or abilities, neutral relationships,
and the selected existing fantasy/narrative profile. Directed locations must
be reachable from the player's start. Text remains untrusted descriptive data.

The user edits descriptive cast/world fields and explicit knowledge/belief
assignments, requests native review, then explicitly creates that exact review.
World truth, initially entitled knowledge and potentially false character
beliefs are distinct. Derived display-description facts have declared initial
visibility. No initial claim event is fabricated. Edits revoke UI consent;
another native review revokes/replaces the earlier review, even on refusal.
Existing stories cannot be edited or backdated through this API.

An optional `Seed.initial_world` records the original bounded JSON response,
its hash and parsed proposal, original input, complete validated model
configuration, explicit edited input/proposal and save title. It is canonical
initial configuration/provenance, not a retrieval source. Gameplay context
continues to come from accepted events/projections and observer-scoped facts.
The provider kind distinguishes scripted plumbing from local inference;
metadata alone is not proof that a model ran.

The versioned origin hash covers the full canonical origin with array order
preserved; scope is excluded so native fork/import rebinding is possible.
Reconstruction validates the complete derived Seed, not merely public facts.
The recipe reserves `world-` plus20 lowercase hexadecimal digits for authored
seed IDs; stripping required origin from this namespace refuses. This detects
structural downgrade/corruption and does not authenticate external archives.
Ordinary legacy absent-origin seeds retain their exact serialized bytes. No
SQLite migration is required; older strict readers may refuse the new optional
field rather than silently discard it.

Draft jobs are process-local and bounded to one retained job/one active author
generation per Host. Generation releases the Host state lock and never opens a
SQLite write transaction. Cancellation, configuration change and owner close
invalidate the job. Native identity/phase fences reject late output. The
existing external bridge and Kotlin owner use a separate author budget and
explicit author trace labels; old director/narrator limits remain unchanged.
Unknown cleanup still quarantines resources; coroutine cancellation is not
proof of native closure.

Explicit creation uses the existing atomic full-seed Store transaction and
idempotency key. A completed creation can be recovered after lost ACK/restart
without inference. That recovery path only loads/rechecks an existing Engine;
it cannot insert. A story deleted between lookup and attachment must not be
resurrected at revision0. An uncommitted lost draft must be reviewed again;
missing process-local state never silently regenerates or saves.

Current local runtime dependencies and model pins are unchanged. The existing
LiteRT-LM public JSON-schema path handles non-finite schemas; the finite literal
codec remains unchanged. A real author turn on the pinned model is a separate
measurement gate. Scripted tests cannot establish creative quality, semantic
consistency, physical-device performance or joined native callback drain.

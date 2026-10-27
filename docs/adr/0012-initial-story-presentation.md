# ADR-0012: Initial story presentation and narration phrase boundaries

Status: implementation proposal, pending qualification and owner acceptance.
Refs #13 (M09.02; supporting M09.03/M09.06) and #14 (M10.02).

The creation flow already reviews a native-derived template, title and player
name. Tone and content-boundary configuration is still missing. A Kotlin-only
preference or a provider-only text filter would disappear on reopen or permit a
different commit path to bypass the setting.

Add optional, validated `Seed.presentation` with a versioned tone and literal
phrase-exclusion list. This is initial story configuration, not a fact, claim,
belief, knowledge grant or instruction to the mechanical director. Store owns
its existing atomic seed transaction. The new presentation factory derives only
a bundled seed and the existing validated player-name customization, validates
the setting and engine, and binds the complete seed before creation. It accepts
neither a replacement Seed nor arbitrary privileged edits. Existing stories
cannot change this initial configuration through the creation API.

Plain tone with no exclusions canonicalizes to an absent field; the default
Seed serialization and old creation/retry behavior stay byte-compatible.
Explicit `Some(default)` is refused as a noncanonical seed. Old data remains
readable without a database migration. A presentation-enabled export requires
a reader supporting the optional seed field; older strict readers refuse the
unknown field rather than silently dropping settings. Existing archive framing
and transaction ownership are unchanged.

Tones are the closed values plain, warm and brisk. They are narration guidance,
not a style-quality guarantee. Exclusions mean Unicode-lowercased literal
substring matching in generated narration. They do not mean semantic-topic
filtering, full Unicode casefold, normalization, censorship of player input or
replacement of canonical source truth. The UI must describe that boundary.
No age rating, store distribution policy or broad content-policy promise is
selected by this implementation.

Every actual narration commit path checks the exclusions, including typed v1,
current staged play and recorded-history reconstruction. Generation preparation
and fallback also check them. If even the existing approved-summary fallback
contains an excluded phrase, fail without committing; do not weaken the filter
or invent an alternate outcome. The evidence-only staging clone remains able
to construct the approved mechanical description before the narrator paraphrases
it; that clone cannot install accepted state. Cancellation/stale source fences
remain around the actual canonical append.

Presentation-enabled model calls use distinct versioned prompt/narration policy
identifiers and a seed-bound presentation provenance record. Old prompt and
literal-construction identifiers retain their old mappings. Missing, unexpected
or mismatched presentation provenance is rejected, including during replay.
Replay never calls inference or rewrites old narration. Default stories keep
their exact historical prompt/record encodings.

Original-premise generation, broader semantic content boundaries, further
character setup and complete real-model/physical/accessibility/journey gates
remain required work. This slice does not complete M09.02 or establish semantic
consistency or model performance. Acceptance requires original hostile-input,
hash/binding, literal-match, bypass/fallback, retry/reopen/fork/archive/cancel and
stale-action tests, plus actual fixed Compose/JNI qualification and retained
source/APK/owner/raw evidence. Planned checks are not results.

# Read-only desktop memory inspection

Refs #26 D05.01–.07, bounded UI integration. Shared #10/#11 still own memory,
summaries and retrieval. This interface exposes existing authoritative data; it
does not create a second memory engine or qualify the complete D05 exit gate.

Open **Memory & evidence** beside the chat workspace. Its table shows the selected
story/root branch, current head, inspected completed revision, story time, view,
observer and privacy. Character state, history, directed relationships, truth and
knowledge, promises, evidence sources and completed-turn comparisons are typed
read-only rows. Summaries and retrieval indexes explicitly report unsupported;
missing profile fields and branch-history limitations come from the shared page.
No aliases, descriptions, summaries, embeddings or evidence are inferred locally.

Each table row distinguishes canonical fields/truth, recorded statements,
subjective beliefs with confidence, observations, messages and derived comparisons.
A claim does not render as established reality. Relationship direction and each
respect/trust/obligation dimension remain separate. Duplicate display names retain
their actor IDs. Promise status is labelled as a derivation at the inspected time.
NPC History contains witnessed events only; player prompt and narrator Message
rows are rejected by the consumer for character lenses as well as excluded by
the shared query. Actual speech remains in an observed Said event.

The initial view is a table, not a raw JSON dump. Selecting a record opens readable
detail; exact JSON is a collapsed secondary disclosure. Mutable fields link to
seed or eligible event sources. Withheld evidence is labelled and cannot be
followed. **Why is this true?** opens the matching field provenance. Removed fields use
the prior head, explicitly show absence at the after-head, and offer separate
observer-filtered completed-turn history. Event/message records route to accepted
event sources instead of nonexistent field-provenance keys; unavailable evidence
is labelled, and provenance records already showing sources have no Why loop.
Event sources
open accepted history, and **Compare completed turn** resolves the actual receipt
boundary rather than treating any event sequence as a complete turn. A selected
chat receipt also offers **Trace turn & evidence**. Before/after detail shows two
replayed projections at their actual revisions. Absent fields are shown explicitly.

**Copy selected record** copies only the chosen permitted row plus its scope,
current/inspected revisions, observer and privacy after an explicit click. This
can contain private story text; review it before sharing. D03 inspection exports
remain separate deliberate native operations. There is no SQL/JSON editor,
model-issued administration, arbitrary path or filesystem control in this UI.

## Scope and asynchronous responses

`query-model.ts` matches the source-owned Serialize-only Row/Page variants.
Requests use the frozen generated `inspection_query` v1 command. A page must match
its requested scope, current expected head, inspected revision, observer kind/ID,
view and privacy, with bounded rows/bytes/cursor and known row variants. JSON
object field order has no semantic role. NPC Message rows, mismatched privacy,
wrong scopes/heads, duplicate keys and malformed/oversized pages fail closed.

The controller stores one current page and a navigation cursor stack;
it does not cache private pages across lenses. Every read captures the exact
session, story, branch, current head, inspected head, observer, view, search, limit,
cursor, workspace mode and operation epoch. Late success and error responses must
still match that whole context. Story/lens/head changes synchronously remove old
rows and selected records. Story/lens changes also reset derived search, inspected
revision and change-trace parameters; a private Why key does not linger under a
new lens. Return to play closes the browser, switches mode/observer to Play/Player
and clears the legacy private inspection. Source navigation checks its captured
query epoch again after awaiting, including selection and status text.
A stale current head shows no old results and offers
an explicit refresh. Search is a literal substring over permitted serialized
records, not SQL, semantic search or access to hidden counts.

Inspection state never replaces the gameplay actor or generation context. A
historical lens does not rewind the live game. Closing the browser removes its
page, and browsing cannot commit, advance time or invoke a provider. Normal Play
selects the Player lens. Entering Story Lab through the UI opens a native HTML
modal with a focused spoiler acknowledgement and cancel/Escape path; character
and omniscient lenses become available only after the deliberate choice.

The Host's Story Lab capability remains trusted native construction, outside
renderer JSON. The UI acknowledgement is a product boundary, not a sandbox against
a compromised renderer or operating system. Shared unprivileged-Host tests own
grant-denial evidence; this native app owns a trusted Story Lab Host. See
[shared Host integration](D05_HOST_QUERY_2026-10-22.md) and
[shared review](D05_SHARED_REVIEW_2026-10-22.md).

## Fixed native verification

`inspector-harness.mjs` launches only this application's hidden native WebView and
actual native IPC. It uses a fresh synthetic SQLite database across a real process
restart, fixed scenario code and approved labels through the existing development
harness. The fake provider is used explicitly to establish synthetic accepted
history. Inspection then proves canonical state/story time/live-worker invariance;
no real model is loaded or called. No new generic debug/file/process API exists.

The trusted launcher requires LOCALLORE_D05_ARTIFACT_ROOT and can supply
LOCALLORE_D05_TARGET_DIR for task-owned build outputs. Existing regression runners
also accept LOCALLORE_DESKTOP_ARTIFACT_ROOT and LOCALLORE_DESKTOP_TARGET_DIR. Normal
product behavior ignores these launcher locations. Outputs in the verification
record live under the task-owned D drive, preserving existing C caches/model/data.
Development compile flags, launcher opt-in and fixed labels remain separate from
normal assets; the normal frontend hook-absence check covers the new journey.

From the repository root, after setting the trusted task output variables:

```powershell
node apps/desktop/inspector-harness.mjs
npm --prefix apps/desktop run check
npm --prefix apps/desktop run format:check
```

The inspector uses native form controls, table captions, row/column headers,
keyboard focus and status announcements. The finite captures verify readable
selected states, including 150% text at narrow width. They do not replace a full
assistive-technology audit or long-history performance qualification. See the
[executed verification record](D05_NATIVE_VERIFICATION_2026-10-22.md) and
[review repair](D05_NATIVE_PROVENANCE_REPAIR_2026-10-22.md).

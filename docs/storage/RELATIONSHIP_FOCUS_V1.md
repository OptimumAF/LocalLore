# Exact relationship focus

B69, 2026-11-01. Refs #13 (M09.04), #14 (M10.02 supporting).
Additive read-only Host-v1 operation; Query2, canonical records and storage
schemas retain their existing versions.

## Request and result

Within the existing `{"version":1,"command":...}` envelope:

```json
{
  "op": "inspection_relationship_focus",
  "session": "<existing session>",
  "query": {
    "version": 2,
    "scope": {"story": "<story>", "branch": "<branch>"},
    "expected_head": 1,
    "at_revision": null,
    "observer": {"kind": "player"},
    "view": "relationships",
    "cursor": null,
    "limit": 8,
    "search": ""
  },
  "target": "Mira"
}
```

The placeholders are explanatory, not a runnable saved session. Unknown fields
are rejected by the existing strict Host/Query deserializers. Core exposes
`inspection_query::relationship_focus(&Engine, &Query, target, story_lab_granted)`.
It requires Query version2, Relationships, empty search and a valid native ID
(1..64 ASCII letters/digits, hyphen or underscore). Target case is significant.
Other existing scope/head/observer/limit/cursor/time/boundary rules still apply.
An absent eligible target produces a supported empty page, never a lookup of
another actor's sheet or private incoming edges. Reply is the existing Query2
Page in the existing inspection reply shape; there is no new canonical type.

The Host validates the current session scope and reads one immutable engine
snapshot, resuming durable state when a persistence port exists. It uses the
same trusted Host inspection grant as ordinary queries. Caller-supplied targets
cannot create that grant. WorkspaceRegistry routes this typed command through
the existing byte call; JNI signatures, locks and resource ownership stay intact.

## Eligibility, bounds and cursor identity

Resolve the existing completed historical snapshot and observer eligibility
first. Enforce the unchanged 65,536-candidate bound, then retain only typed
`Row::Relationship { to, .. }` values equal to the target. Sort, serialize, count,
byte-bound and paginate that result with the existing implementation. Focus
cannot use a reduced result set to bypass the candidate bound. No Kotlin
page-local filtering or count reconstruction is allowed.

For focus only, prefix the existing Query2 identity digest with bytes
`\0locallore-relationship-focus-v1\0`, then the JSON-serialized exact target.
The cursor-cleared Query and eligible row bytes follow as before. Thus focus
and All cannot exchange cursors, even when their rows are identical; neither
can case-distinct targets, other observers, heads, scopes or time boundaries.
Ordinary Query2 takes no prefix and keeps its original digest bytes.

Generic Query2 search lowercases text and is unsuitable for exact actor IDs.
The initially proposed serialized `"to":"id"` search shortcut was rejected
before implementation; valid `Mira` and `mira` must remain distinct. No new
query language or restriction on valid worlds is introduced.

## Android selection and display boundary

The display-only `StoryRecordRelationshipTarget(id)` is optional on query,
state and entries. The current player remains the actual validated native
binding. Decoder retains native `to`, validates its syntax, and rejects an
entire focused response containing another target. Query validation also
requires the All promise filter; unrelated sections and free search cannot
silently combine with focus. Existing source text, row values and scoped
provenance remain native.

Focus requires an exact current entry reference in a visible, nonloading,
error-free Relationships list with no open event detail. It starts page one.
All relationships can leave an errored focused page. Next/First/retry and
evidence Back preserve the target. Search, section changes and reopen clear it.
Evidence drill reads the original scoped tuple through the current player's
History lens, with no focus target or privileged ancestor session.

ViewModel actions require the exact rendered state, visibility and a live
owner. Referential control/row keys retire old clickable nodes. Search draft
identity includes focus. The UI explains direction, displays the opaque target
ID and offers All relationships; it does not resolve a name, private thoughts,
profile or incoming state. Browsing cannot generate or commit a turn.

## Validation and limits

Nine original native cases exercise actual Core and durable WorkspaceRegistry/
Host routes, including exact case/prefix IDs, cursor separation, observer and
historical boundaries, corrected inherited sources, stale persistence heads,
reopen and unchanged canonical projections/records. Thirteen independent JVM
cases cover the adapter/controller/ViewModel with synthetic transport. Two
Compose journeys compile but are unrun on Android. See the
[execution report](../android/RELATIONSHIP_FOCUS_2026-11-01.md) for exact commands,
artifacts, source attribution and open device/model/acceptance gates.

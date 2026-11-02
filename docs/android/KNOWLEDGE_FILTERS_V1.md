# Player-visible knowledge record filters

Refs #13 (M09.04), supporting M09.06/M10.02. Implementation/verification remain
in review until their recorded checks and owner acceptance. No milestone checkoff.

The local `StoryRecordKnowledgeFilter` has exactly ALL ("All", no origin),
OBSERVED ("Known as observed", `known_as_observed`), STATEMENTS ("Statements",
`recorded_statement`), BELIEFS ("Beliefs", `subjective_belief`) and DISCOVERIES
("Discoveries", `recorded_discovery`). It adds a last default-ALL property to
local Query/State only. It is not a native JSON field, grant or canonical type.

Only version-2 KNOWLEDGE may use an active filter. It requires empty search,
promise filter ALL and no relationship target. With valid search text,
contradictions fail as invalid response before dispatch. Native search is the exact closed literal
`"origin":"<wire-origin>"`; ALL preserves the existing user search. Rust applies
observer/story/branch/revision restrictions and matching before counting and
paging. Kotlin never removes rows or recomputes totals. Every returned row must
match the requested native origin. Existing byte/source/cursor limits apply.

Selecting any facet, including ALL, clears search. The wire's ALL mode preserves
an explicitly supplied literal search. Search switches to ALL; selecting a
section (including reselecting KNOWLEDGE) resets the filter. First/Next/Retry
retain it, and changing it starts at the first page. Late/replaced/closed or
disposed views cannot act on a new view. MainActivity passes the exact rendered
record state; interactive controls use the existing record delivery key.

No CanonicalTruth facet is added to the player Query2 lens. Known-as-observed
records retain their original proposition/source after an unseen world retcon;
they are not relabeled as current world truth. Statements, beliefs and discovery
records retain their own origin labels, confidence and original scoped evidence.

Native fixture output is one compact JSON object plus LF, at most 128 KiB:

```text
{version:1,cases:[{id,domain_version,player,scope,head,story_time,forbidden:[...],
  filters:[{origin:null|one-of-four-wire-origins,
    pages:[{query:<actual Query2>,page:<unmodified actual Page>}]}]}]}
```

Include Domain1 parent and Domain2 corrected-child cases with at least nine
player beliefs, a witnessed statement containing escaped origin-like prose,
an actual discovery, private NPC canaries and a later-parent-only statement.
Use explicit native author correction to change world truth while retaining
the player's older observation. All queries use Player/KNOWLEDGE/version2/
limit8/at_revisionNone, actual cursors and original source tuples. Assert exact
filter totals against eligible typed rows, no canary/future-parent leak and
unchanged canonical state/history across reads. No fake domain flag or model.

The corpus is copied byte-identically to
`apps/android/app/src/test/resources/story-record-knowledge-filters-v1.json`
with an exact `-text` attribute. Kotlin tests consume original native pages;
metadata canaries are test expectations and are not model context. Compilation
does not establish Android/IME/accessibility or physical/model behavior.

PR #354's separate frozen recovery scope remains unchanged; it authorizes no
operation for these new product bytes or tests. No new dependency, native
production command/schema, observer privilege, gameplay rule or storage owner.

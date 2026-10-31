# Player inspector Query2 migration

B37. Refs #13 (M09.04), #14 (M10.02 supporting read ownership).
Base PR298 facaa2b7c74ac6e825c6b06935edeb3f02477758, unmerged.

## Consumer and authority

StoryRecordQuery defaults to version2 for ALL five existing sections. Keep
explicit version1 command/decoder support for the original four sections;
Promises remains version2-only. No native schema, query, privilege, gameplay,
storage, inference, model or dependency change. Query2 already supports both
Domain1 and actual corrected Domain2. Do not infer domain from authored origin.

Kotlin renders only native player-visible values. The same frozen story/branch/
head, player observer, page/search/byte bounds, versioned cursors, gateway
session/head fences and cancellation/generation/disposal behavior remain.
No privileged observer, current hidden truth lookup or source-branch session.

Version2 field/relationship/knowledge sources use exact typed scoped_event
references (original_scope story/branch and sequence), seed or withheld.
Only scoped events become navigation; flat event sources refuse in V2.
Inherited scope never becomes the active child scope. Evidence drill searches
the exact tuple through the same current player lens and validates the one
returned event, witnesses, head/time and original tuple. Existing Promises
and explicit Query1 interpretation remain intact.

## Display shapes

Add StoryRecordOrigin.KNOWN_AS_OBSERVED with native wire known_as_observed,
label "Known as observed". In Query2 Knowledge it requires subject player,
null confidence and native typed sources. CanonicalTruth is legacy Query1-only
in this fixed player adapter; V2 never promotes an observation to world truth.
Statements, subjective beliefs and discoveries retain their distinct origins.
Unseen author correction must not rewrite remembered propositions; actual
rediscovery may update the value. No Kotlin reconstruction of truth/history.

Query2 scoped_message is History-only, RecordedMessage, with bounded native
original_scope, turn, message_kind, text and ordered unique nonempty event_ids.
Convert those IDs only to tuples in that original scope; never flat links.
Recorded input and narration labels remain as before. Legacy message is V1-only.

Query2 author_correction has exactly kind and revision, no key/origin or private
author payload. Decode it BEFORE ordinary key/origin reads. History V2 only,
revision1..head. UI key "author-correction:<revision>", title "History correction",
text "History was corrected at revision #<revision>. This marker is not a witnessed event."
Use StoryRecordOrigin.AUTHOR_CORRECTION (wire author_correction, label
"History correction") solely for this display marker. Sources, eventSources,
scopedEventSources are empty and event is null. It is not a witnessed event,
fact or navigation capability. Extra fields/private reason/payload refuse.
Keep existing widget layout and accessibility conventions.

## Frozen native corpus

Independent example crates/locallore/examples/android_record_query2_fixture.rs
emits ONE compact JSON object to stdout, maximum128KiB, with no file writes,
model/provider/SDK/network/device calls or native backend changes. Root alone
builds/runs it under the bounded host owner and captures the original output.
It constructs original synthetic Engine histories and calls the actual
inspection_query::query with version2/player/limit8, following actual cursors.
Assert canonical state/records unchanged around queries. Use real accepted
author correction to assert Domain2, never a hand-set domain flag.

Corpus schema: {"version":1,"cases":[{"id":...,"domain_version":1|2,
"scope":{"story":...,"branch":...},"head":...,"story_time":...,
"forbidden":[synthetic private canaries],"pages":[{"query":<actual Query>,
"page":<actual Page>}]}]}. Required cases root, corrected, rediscovered;
optional sibling. Query/page are unmodified native serialization. Corrected
case retains old observed proposition despite unseen new truth; rediscovered
case may legitimately contain the newly observed value and omits it from that
case's forbidden list. Include scoped inherited sources, changed progression/
relationships, messages, beliefs/statements/discoveries and correction markers.
Private NPC data/author reasons remain forbidden. No raw canonical payload in
the output. Query all five views for compatibility; cursor/version joins are
native. Freeze output as src/test/resources/story-record-query2-v1.json.

## Independent ownership and checks

Root owns existing Android adapters/types/controller, necessary legacy JVM
fixture updates, generated corpus resource and docs/integration/execution.
Independent JVM FIRST writer owns ONLY new Query2StoryRecordTest.kt. Tests use
existing APIs/reflective origin wire strings so they compile before new enum
implementation; missing corpus/API is setup, not behavioral RED. Independent
native fixture writer owns ONLY the example above. Each uses a separate D:
worktree. Read-only reviewer owns no source. Agents do not run builds/tests.

Root first captures native corpus, then runs focused original FIRST tests on
unchanged production, fixes setup separately, implements and reruns. Verify
all section defaults, native pages/observation distinctions, scoped navigation,
marker privacy/non-navigation, cross-version/flat-source/cursor/type tampering,
cancel/stale/context/dismiss/disposal. Preserve explicit Query1 negative/legacy
coverage; migrate obsolete default fixtures without weakening assertions.
Run relevant native query suites and archive-profile offline Android/JVM/lint/
product+pair gates. No emulator/phone/ADB/model/app grant is used. Host, JVM and
packaging evidence does not qualify a device, model, real SDK drain or release.

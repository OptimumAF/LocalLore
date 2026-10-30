# Saved Domain2 timeline browser contract

Refs #30 (partial D08.04/.07), #26 (supporting D05.01/.07). This is a
prospective frontend adapter contract, not verification or runtime admission.

Accepted main3178f085 already provides Host `branches`, the version2 saved
catalog and `Controller.resume`/`resumeTimeline` for Domain2 snapshots. The App
currently hides the browser for `playV2`. Reuse those interfaces without adding
a storage writer, session owner, generation path or domain-specific catalog.

## Product boundary

The actual App exposes `TimelinePanel` for a selected Domain2 story in Play and
Story Lab. Keep the separate ForkPanel Domain2 exclusion. The browser presents
only existing catalog metadata: story/title, branch ancestry, fork/head revisions,
saved draft counts, active/retired/current state and explicit Resume controls.
It does not create timelines or perform author corrections. Replace contradictory
copy that says Domain2 timeline navigation or all author corrections are absent;
retain truthful notices for the other unavailable adapters.

`timelineContext` retains legacy behavior. When a V2 snapshot is present it must
match the selected scope and selected revision, otherwise return null. A coherent
V2 context carries that snapshot's revision plus the existing session, scope,
view, observer and persistent-workspace identity. Disposed/no-selection remains
null. Do not grant any Lab privilege or alter the gameplay observer.

Use the existing `TimelineController`, closed catalog decoder and exact selected
branch path through `resumeTimeline` to the normal Controller. Browsing calls only
`branches`; selecting an active non-current row uses the existing resume/read
path. Retired, unknown, current, busy and invalid-context selections cannot start
a new resume. Keep existing typed failure/retry behavior; never fall back to a
different branch or guess success from an old visible error.

Panel handlers capture the rendered context and recheck `matchesContext` before
show, hide, refresh or resume. This rejects callbacks retained from a different
story, session, revision, view or observer. Existing controller epoch fences reject
late catalog/resume completions after context changes. Do not introduce generic
test hooks or bypass native validation.

## Independent FIRST acceptance

Freeze a separate-author checker before changing product source. Exercise actual
App/Panel/controller/helper source using synthetic Gateway data; disclose inert
React/static HTML and mock transport. Keep checks bounded and source-controlled:

- Actual App includes the real browser for coherent V2 Play/Lab while Fork stays
  hidden; legacy browser/Fork presentation remains compatible. No false Domain2
  navigation or browser-authoring capability notice.
- V2 context uses the matching head and preserves Player/NPC/omniscient lens,
  session and persistent identity; mismatched scope/head and disposed/no owner
  return null. Legacy fallback remains unchanged.
- Catalog ancestry/current/retired metadata renders safely, including escaped
  synthetic text. Exact active child selection traverses actual TimelineController,
  resumeTimeline and Controller; never first/recent branch fallback.
- Read-only browsing does not mutate play/snapshot/observer or issue generation,
  submit/prepare/commit/fork/author/grant commands. Resume uses only its established
  session/read operations; keep accepted history separate from synthetic fixtures.
- Story/session/head/view/observer switches retire old results and old rendered
  callbacks. Loading, retired/current/unknown targets, malformed/unsupported/error
  responses and retry preserve coherent visible state. A failed target resume
  cannot be reported successful by an unrelated old visible error.

Retain existing timeline and Domain2 resume checks. Expected new failures must be
observed before the different-author product fix. A setup failure is UNRUN_SETUP,
not behavioral RED; preserve it and any assertion corrections distinctly.

## Verification boundary

Source tests/static HTML are not native IPC, native WebView rendering, canonical
Rust validation, persistence, keyboard/screen-reader or Android parity evidence.
Any actual native browser journey needs a separate prospective source-bound,
bounded plan and fresh inventory. Charge every previous D05/D07/D09 retained
artifact to the existing aggregate limit; no failed budget reset, evidence deletion,
near-duplicate frozen cohort or stopped OS/model/device workflow is authorized.
Keep generated evidence local/ignored on physical D and Root as the only heavy
worker. Record original failures and exact commands/revisions in the later
qualification report. Full D08 and the desktop epic remain unchecked.

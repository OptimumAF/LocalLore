# D06 UI boundary source review

Refs #28, source-review claim
[6359043522](https://github.com/OptimumAF/LocalLore/issues/28#issuecomment-6359043522).
Reviewer: `/root/desktop_runtime_profile`, shared trace author but not the desktop
UI/controller/harness author. This review covers the **app boundary only**; it is
not an independent re-review or acceptance of the reviewer's shared trace work.
Exclusive review change: this new document. No implementation edits, builds,
tests, application execution, desktop/CUA control, screenshots, model, device,
process management, network inference, merge or release by the reviewer.

Reviewed accepted baseline `228c482c6a3bcfef7bec6a6769ed2207ee054b69` to
`2b2b7ab19995e83060d920df1938e78112d535b9`, then exact repair
`dad1c022c0868c752324564240ade904b7eaefc7`. Final isolated review branch is
`review/d06-ui-boundary-final` at the latter hash. Scope: the 14 changed files under
`apps/desktop`, including TurnDebugger, strict trace-model decoder, controller,
frontend initialization/styles, fixed trace journeys/launcher/controller checks,
normal-bundle verification registration and native harness-label initialization.
Later accepted-main merges are not treated as new app implementation by this review.

## Concrete finding and disposition

**P2, corrected: delayed receipt navigation could overwrite newer inspector intent.**
At 2b2b7ab, `Controller.traceToInspection` captured session/global epoch, awaited
`showQuery(true)`, then opened the old receipt's turn_diff if only that session
remained current. While the query was held, the user could choose a different
search/boundary, or switch Play to Lab/Mira and browse a different view. Those
changes advance query/inspection epochs, not the session's global epoch. The
late helper could therefore replace the newer navigation. The Host still filters
that eventual query; this was a visible-navigation race, not a demonstrated
knowledge leak, canonical mutation or privilege escalation.

The UI author identified this during final verification, the coordinator confirmed
it, and this reviewer inspected the exact vulnerable code and repair. The repair
in dad1c022 captures view, observer and snapshot head in addition to session/global
epoch, checks that context after closing the trace, starts showQuery and captures
its synchronously advanced queryEpoch, then checks exact context, query visibility
and queryEpoch after the await before navigating. Current queryInspection advances
its epoch before awaiting the gateway, so this is the correct request identity.
The new held-query source cases preserve (1) newer knowledge/search/historical
boundary and (2) Play→Lab/Mira plus a newer filter/boundary, and assert no turn_diff
command was issued. The author reports those checks pass; the reviewer read them
but did not execute them. The inspected finding is resolved. No other concrete
blocking app-boundary defect was found in the reviewed source.

## Authority, identity and receipt checks

The app adds only the existing trace_configure/read/clear commands. It does not
change generation request construction, model provider, actor knowledge, canonical
commit, Store schema or Host inspection grants. Play always requests its actual
player lens; Lab converts the selected inspection lens into the existing observer
union. An acknowledgement remains UX consent; native Host construction owns the
actual Lab privilege and shared Rust owns visibility. No wire boolean can grant it.

`clearTrace` invalidates the trace epoch and immediately removes reply/selection
on hide, basis change, observer/view changes, session invalidation and head refresh.
`readTrace` binds the exact session/scope/current snapshot head/captured basis/
observer query and read sequence, then rechecks both current context and epoch
before publication or error display. Old replies cannot restore deleted metadata,
relabel a player attempt as Mira or cross a new session. Window-wide configure
operations are serialized separately; on completion they read the current context
rather than republishing an old session snapshot. Configuration is explicitly
labeled window-wide in UI and wire, rather than pretending it is per-story.

`checkedTrace` rejects extra/missing structural keys, mismatched scope/head/basis/
observer, wrong attempt identity, unknown stage/outcome/error categories, unsafe
nonnegative integer fields, path-shaped provenance, invalid hash/revision/label
widths, more than 32 attempts/24 stages and payloads above 64 KiB. Disabled snapshots
must be empty, capture metadata-only/full-capture unsupported/exact-reconstruction
false must be explicit. It validates the frontend boundary, not independent proof
of monotonic Rust stage history or canonical truth. The existing native envelope
also imposes its own output cap. Control acknowledgements validate their expected
fixed flags; unused extra fields are not presented as diagnostic content.

`debugReceipt` uses only the existing Player play snapshot, exact turn, scope and
base revision. It returns no implicit receipt under a Lab lens. A canonical
receipt is presented separately from a running/failed/stale trace; it need not
prove that this particular attempt committed. The linked D05 read is revision-
scoped and now fenced against newer navigation. There is no new commit, generation,
replay or model call in the debugger. Missing context selections/proposals/full
capture/summaries/step/rerun are explicitly unavailable. Missing stages do not
receive invented skipped/failure explanations; zero counts are labeled reported.

## Passivity and harness boundary

At final source, refresh starts optional `readTrace()` without awaiting it. Its
errors update trace-local state rather than gameplay visibleError. The held-read
controller case verifies the intended Promise ordering in source: gameplay
refresh resolves while metadata IPC remains deferred. This does not prove native
scheduler fairness, lack of mutex/SQLite replay contention or bounded latency at
maximum history; those remain shared-owner/performance qualification questions.

Normal frontend builds use the existing compile-time `__DEV_HARNESS__` gate;
fixed trace journeys are dynamically imported only behind it and the explicit
native test flag. Normal-bundle verification now checks D06 journey markers as
well as the previous harness markers. Native commands remain separately registered
under the existing `dev-harness` cfg; the normal handler set adds no harness command.
The changed native initialization adds a boolean derived from a fixed environment
comparison and a fixed stage, not executable renderer-supplied script.

The native harness adds only fixed checkpoint labels to an existing allowlist.
Its output directory comes from the trusted development launcher; renderer IPC
supplies neither paths nor shell commands. create-new outputs, 40-checkpoint,
256 KiB JSON and 16 MiB PNG caps remain. Capture uses application-owned WebView2
CapturePreview into a bounded memory stream; hidden/nonfocused app windows and
fixed app viewport presets do not capture or control the desktop. The trace
launcher has fixed build/executable scenarios, synthetic SQLite fixtures and
actual process restart; it adds no arbitrary-execution endpoint, remote debugging
server, model tool, network request or user-story upload. DOM scrolling/focus in
this fixed synthetic renderer is not evidence of desktop input automation.

The D06 pending native fixture holds a prepare **reply after the actual native
prepare has returned ready**. Its running trace means an uncommitted attempt,
not proof that a model/provider worker is still generating. It validly checks
pending presentation and cancellation of that ready candidate. It does not
qualify cancellation of an actively running real inference worker.

## Existing evidence inspected, with attribution

The reviewer read author-produced summaries/checkpoint metadata and source hashes;
no check was rerun. The final local summary for dad1c022 reports **74 distinct
assertions, 12 captures, native backend, actual process restart, synthetic=true,
realModelGeneration=false, passed=true**. Artifact directory:
`desktop-debugger-artifacts/trace-native-a08474e8-15f8-43df-b8ab-72c60a1ed591`
under the coordinator's ignored D task root. Earlier source-aligned 2b2b7ab summary
`trace-native-a2a23731-d1c6-4797-947b-2fdfa65d33cc` independently records 74/12/restart;
its 12 checkpoint records say native-webview2. Initial report has 68 checks and
expected Agency/Cancelled/Cancelled/Stale bounded errors; restart has 10 checks
and zero errors (distinct union is 74). These are author outputs, not reviewer
execution or a full D06 acceptance claim. The coordinator reports inspecting wide/
narrow render pixels; this source reviewer did not independently inspect images.

Six reviewed frontend/launcher file byte hashes matched the earlier 2b2 manifest.
The two Rust files differed only in checkout CRLF/LF bytes: normalized source was
identical and actual author-checkout hashes were retained in its manifest. Final
repair changes only controller/check-trace-controller plus a merge of accepted
main; the other reviewed app code remains unchanged.

Final reviewed frontend SHA-256:

| File under apps/desktop | SHA-256 |
|---|---|
| ui/controller.ts | d49cf7f17a08e3d71d3f3057656e39ede77730e7a62af33c3cf623e56ba80823 |
| check-trace-controller.mjs | 28445f641c6bda34bce2fcfb09461c72bc2e90190182f9a538f870b3a58adb9f |
| ui/trace-model.ts | b188a04064b4dda6faa92a0519f9e5475f9ef1afd2e69ed41c87a4d5f8439207 |
| ui/TurnDebugger.tsx | b052229e00deed37aee51a2b5a155bcfed03125fbf72df81bc9a44883b5b6e94 |
| ui/trace-journeys.ts | 6eac0cbcd264f12038fcc6d10733ad3a226ceb23e680a76f5ac8de4a440322df |
| trace-harness.mjs | a89a6d4a22307185c0144ef342a1963582f9511654b3d366e7c78bafac55bde1 |

Full D06 remains unchecked: exact selected context/omission/rank artifacts, raw
proposal opt-in, full capture/retention/export, memory-maintenance/stale-summary
diagnostics, pause/step, real-model instrumentation quality and any physical-device
or maximum-history performance qualification are not established here. The next
runnable step is coordinator final source/evidence reconciliation and the focused
UI PR. Additional regression results belong to their executing owner; this review
provides no approval score, fabricated human review or milestone acceptance.

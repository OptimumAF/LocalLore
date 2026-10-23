# D08 existing timeline browse/resume slice, 2026-10-23

Refs #30 D08.04 partial; #12 M08 ancestry/retention dependency. Claims
[#30 6371502652](https://github.com/OptimumAF/LocalLore/issues/30#issuecomment-6371502652),
[#12 6371503352](https://github.com/OptimumAF/LocalLore/issues/12#issuecomment-6371503352).
Author `/root/app_storage_review`, separate `source-timeline-browse` /
`impl/d08-timeline-browse`, accepted base
`e7ca17ae69ada182d1a5ec5144b42c029a46c184`.

This packet implements only bounded catalog presentation and selection through
the existing shared resume path. It does not create/fork/rewind/regenerate or
correct a timeline. Existing App/main/style/native/schema/gameplay files remain
coordinator-owned. No full D08 checkbox, native journey, quality or release claim.

## Source packet and authority

- `00cb0fbbd2b3d0d76238cbf7c3ce335881abf9f0`: five NEW modules/test;
  initial actual-Controller child-resume RED preserved.
- `ac78161973be4d62c458c197fb92d88123da48bf`: NEW test refinement, including
  malformed original scopes/sequence RED and combined actual-controller switch.
- Required coordinator-authored dependencies, not reviewer source edits:
  `2f8fd0e149a8d0d19d1b5051446057c51f083fdf` (local cherry-pickd35ce65)
  and `eb3420cf8cf67ecdfd803525c2e5afddeeafec32` (localc2ad4a3).
  Those two narrow changes belong to existing ui/model.ts under root ownership.

`timeline-model.ts` decodes actual catalog-v2 keys from Gateway.call branches.
Bounds match the shared Store contract:256 branches, depth32 including root,
60KiB serialized catalog, title256 Unicode codepoints, existing64-character ASCII
IDs and safe nonnegative JavaScript numeric metadata. It checks story binding,
unique IDs, root/parent presence, cycles, exact fork fields and parent/head shape;
retired ancestors remain present. It permits nested prebirth forks and lexical
row order that places a child before root. Frozen DTOs prevent accidental local
row/retired relabeling. Shape checks never replay events or establish canon.

`TimelineController` uses only Gateway.call({op:"branches",story}). Selection
passes one cloned active Scope to the supplied application callback. Retired,
absent and already-selected rows cannot dispatch. No native action, path, SQL,
context compiler, generation/model call or author permission is added. Catalog
contents contain no accepted story prose, knowledge or narrator context. A
catalog is a metadata snapshot; authoritative resume may observe a newer head.

Context includes selected native session ID, original Scope, current revision,
Play/Lab view, observer and persistence availability. Any change clears/hides
presentation and advances the response epoch, including A→B→A, same-scope reopen,
head advance and lens change. Hide/dispose and newer refresh also fence late
success/errors. A pending callback's result cannot label a different context.
Already-admitted resume is governed by the existing gameplay controller's
fences; hiding this panel does not falsely claim to cancel a native operation.

Memory/no-story/empty/backendUnsupported/error states are explicit. There is no
synthetic catalog or storage fallback. `TimelinePanel` renders escaped semantic
list/buttons with exact ancestry, parent fork revision, catalogued head, draft
count and retirement status. It grants no observer privilege. Fork/rewind/
regeneration/correction are textually unavailable, with no misleading buttons.
SSR tests verify semantics and escaping, not native pixel/layout qualification.

## Concrete decoder prerequisites found and retained

Actual Host PlaySnapshot returns original Engine receipts. The existing renderer
previously required each receipt/event scope to equal the selected child scope.
Initial `--child-resume-repro` on00cb uses the actual gameplay Controller with a
MOCK native gateway: root succeeds; child with original main-scoped inherited
receipt fails Wire. This reproduces renderer under-admission, not a Rust replay
failure. LogSHA `2a6ec4acbd325b17f0f53cffae0a6a72ec700d43f5b9ce0bb3940d0bba3c54be`.

Coordinator2f8fd0e validates each original request Scope as exactly two fields,
same story and valid branch ID; events must retain that request's original
scope. Selected top-level/player Scope and revision still match. It never
rewrites receipts or implements a second lineage replay. The original repro
then passes and all initial65 checks pass. A malicious native host fabricating
same-story ancestry is not independently authenticated by this presentation
decoder; shared Rust ancestry/replay/privacy tests remain the authority.

Additional actual play-decoder negative-sequence test at ac78161 fails because
safe integer plus upper bound alone admits-1 (a pre-existing shape gap). The
coordinator's one-line eb3420c rejects sequence<1. The same scope-review then
passes, including zero, malformed original IDs/extra keys and player mismatch.
Negative RED logSHA
`0ece970d258f6aa45a2492b1a70913764cead2a43c6f3dc9bc5c37ee3c7a6241`.
Cross-story, event/request original-scope disagreement and future events continue
to reject. Rust canon/storage/recorded outcomes and privileges are unchanged.
Reviewer did not self-edit either existing-file correction.

Two harness setup failures are separate: initial ESM SSR bundling needed a
Node builtin createRequire banner; an own junction into a directory named
node_modules-locked resolved React/SSR dependencies as two copies. Exact readonly
locked dependency bytes were copied into own actual node_modules instead.
No dependency versions, source packages, locks or application aliases changed.
The setup logs and original Wire/sequence failures are retained separately.

## Small coordinator integration proposal (not applied by this packet)

Main imports and initialization, using its existing same gateway/controller:

```ts
import { TimelineController, timelineContext, resumeTimeline } from "./timeline-controller";
const timeline = new TimelineController(gateway, scope => resumeTimeline(controller, scope));
// Add to the existing gameplay subscription BEFORE React observes changes:
// timeline.contextChanged(timelineContext(controller));
// Call that subscription's initial sync as usual.
// Pass timeline to App; call timeline.dispose() during existing teardown.
```

App imports `TimelinePanel`, `timelineContext`, and the controller type, adds a
`timeline: TimelineController` prop, and places
`<TimelinePanel timeline={timeline} context={timelineContext(controller)} />`
near its saved-story/library controls. No Lab-only privilege gate is required
for the existing public metadata port. The Panel also checks its supplied context
before render. `resumeTimeline` calls existing Controller.resume (which reuses
switchSession), verifies the actual selected Scope/current play revision, and
returns success without mislabeling an unrelated old visibleError. Failure uses
only a newly changed known category or NotReady. It does not forge session state.

Root owns any narrow CSS/wiring. Add `check-timeline-controller.mjs` to the
existing frontend verifier. Production code imports no timeline-journeys module.
If integrating a development native journey, use the same compile-time
__DEV_HARNESS__ dynamic-import pattern and normal-bundle marker exclusions as the
other journeys. Do not add normal-build native fixture commands.

## Fixed actual native fixture/journey interface for next gate

NEW `timelineJourneys({controller,timeline,fixture})` returns check labels or
throws. It requires an actual persistent workspace, actual selected root and
passes no model/backend substitute. Its fixture contract is:

```ts
interface TimelineJourneyFixture {
  root: Scope; child: Scope; sibling: Scope; retired: Scope;
  childFork: number; childHead: number;
  inheritedSource: Scope;
  excludedPlayCanaries: string[];
}
```

Coordinator-native fixture proposal: original synthetic seed, main accepted head4;
parent fork@2 then head5; child from parent@4; sibling from main@1. Give later
parent/sibling accepted dialogue fixed distinct canaries. Retire parent through
the shared deletion plan so required prefix4 remains. Return actual IDs and fixed
expected childFork4/childHead4/inheritedSource main; no fake metadata/DB patch.
Use shared Engine/Store fork/accepted commit/deletion, not a model or a new engine.

Run the actual gateway/controller through catalog read, retired rejection, child
resume (assert original request/event scopes and excluded later-parent/sibling
canaries), sibling selection, and root return with unchanged original play.
The supplied journey performs these checks. Root must add the test-only native
fixture/IPC/main hook, runtime setup and invocation; none was executed here.
Future native gates should also hold a catalog response across session/head/lens
change, test session-limit/retirement races, reload/restart and normal-hook absence.
No fake native success, desktop screenshot/control, picker or device evidence is
inferred from the current Node lane.

## Actual local checks and exact scope

Windows10.0.26300, explicit Node24.22.1 and preprovisioned locked dependencies;
own D output/temp only. No download, native compile, app/worker/model launch,
C UA/desktop/screenshot/device/ADB, protected resource, setting or merge operation.
The coordinator's App/main/native files are still unwired in this checkout.

```text
node check-timeline-controller.mjs --child-resume-repro
initial Wire RED; final PASS, MOCK native gateway + actual Controller
node check-timeline-controller.mjs --scope-review
initial negative sequence RED; final PASS, actual play decoder
node check-timeline-controller.mjs
81 PASS: deferred actual timeline/gameplay controllers, strict decoder,
         valid shared caps/prebirth, malformed scopes, no grant/observer change,
         newest response wins, A→B→A, hide/dispose/lens/head/session fences,
         retired refusal, exact active Scope callback, inert React semantics
node verify-frontend.mjs
PASS: existing normal build, strict TS/schema/controller checks, existing
      development-hook absence (timeline script integration pending root)
node node_modules/prettier/bin/prettier.cjs --check "ui/*.{ts,tsx,html,css}" "*.{json,mjs}"
PASS
git diff --check
PASS
```

Final81 logSHA `51443ea66ece7e88177427affc4afeb625b5533f60d804dd9d84d21a57c82124`;
final reportSHA `8b7f6be691572fa9362f5e77215cf8e72da2871220a28802102c955cf2dd0104`;
existing verifierSHA `0ee3ed76d6806f8bff61b6b0fbd2fae2e7ec99a3c707f006238a149db1e86271`.

| New source | SHA256 |
| --- | --- |
| timeline-model.ts | `06d8780b61c2be1d81d5880f2d93700743af18828e5104ef65ab580972bca292` |
| timeline-controller.ts | `3b55ecb690d1bc6fd76b3de3d470ce28b47198c1037d0244f17f1d1c7b65ed2b` |
| TimelinePanel.tsx | `3b6177d693a6aa80fc59328030ce26cd11d2c47c8b86f1cd5f15690087b79168` |
| timeline-journeys.ts | `ef7a301844308a3a557fdad1708c24d141184058a9ffba82f7bfa2ff3c0f5600` |
| check-timeline-controller.mjs | `22b43b3af2f7693042c4587b726dc3a77674bec52e841fc98ac71bcc4ba02923` |

The requested resource_metrics_review coordination found no live agent; root was
notified and no message delivered. Its evaluation/App paths were not touched.
Next: coordinator independent source review, actual existing gateway integration
and original native Store fixture journey, then native/frontend/platform checks
as warranted. This partial packet does not implement shared fork/author ports,
full timeline editing, cross-device transfer or full D08 acceptance.

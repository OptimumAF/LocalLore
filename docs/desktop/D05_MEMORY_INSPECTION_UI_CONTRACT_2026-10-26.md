# D05 verified memory inspection frontend leaf

Status: frozen SOURCE-ONLY interface before implementation. Checks are UNRUN.
Base `37c88c2975566f915f9881e3b23f3f98ccc359d8`; shared contract is
`D05_VERIFIED_MEMORY_INSPECTION_CONTRACT_2026-10-26.md`. Scope D05.05/.06/.07
and D06.04/.07 supporting read-only desktop inspection. No whole-task acceptance.

## Owned leaf and integration

Only NEW `ui/memory-inspection-model.ts`, `ui/memory-inspection-controller.ts`,
`ui/MemoryInspectionPanel.tsx`, `check-memory-inspection.mjs` and this document.
Root owns Main/App/styles/build/verifier/permissions and native registration.
No automatic generation, job admission, maintenance, cache mutation or model API.

Native call is exactly `invoke("memory_inspection", {action, request})`, with
request the compact JSON STRING of the exact action object in the shared
contract. Direct Core reply, no wrapper. Session remains in this native raw
envelope; the shared Host receives it separately. No frontend consent, path,
grant, arbitrary query/search or provider field. This read needs no new dialog.

## Public frontend API

```ts
type MemoryInspectionContext = {
  session: string; scope: ScopeV2; expected_head: number;
  player: string; observer: string; view: "play" | "lab";
  epoch: number; persistent: boolean; domainVersion: 1 | 2; lab: boolean;
};
type MemoryInspectionRead =
 | {action:"packets";binding:string|null;cursor:string|null;limit:number}
 | {action:"entries";binding:string;cursor:string|null;limit:number;
    packet:MemoryPacketDescriptor}
 | {action:"source";binding:string;packet:MemoryPacketDescriptor;
    source:MemorySourceRef};
function memoryInspectionContextIdentity(c:MemoryInspectionContext|null):string;
function checkedMemoryInspection(value:unknown,c:MemoryInspectionContext,
                                read:MemoryInspectionRead):MemoryInspectionReply;
class MemoryInspectionController {
  constructor(invoke:(command:string,args:Record<string,unknown>)=>Promise<unknown>);
  get:()=>MemoryInspectionState;
  subscribe:(listener:()=>void)=>()=>void;
  contextChanged(context:MemoryInspectionContext|null):void;
  matchesContext(context:MemoryInspectionContext|null):boolean;
  canRead():boolean;
  refresh():Promise<void>;
  packetPage(cursor:string):Promise<void>;
  selectPacket(index:number):Promise<void>;
  entryPage(cursor:string):Promise<void>;
  source(source:MemorySourceRef):Promise<void>;
  clear():void;
  dispose():void;
}
function MemoryInspectionPanel(props:{inspection:MemoryInspectionController;
  context:MemoryInspectionContext|null}):ReactElement|null;
```

State has exactly `context,allowed,busy,action,packets,selected,entries,source,
error,notice`. Packets/entries are checked shared page DTOs; selected is the
checked packet descriptor; source is the checked shared source DTO with actual
`InspectionPageV2`. Initial values null/false/empty. Context/returned data are
detached immutable snapshots. The controller retains a selected descriptor
across packet-page navigation only for the same context and binding.

Identifiers are Core ASCII1..64; head/epoch and all serialized integers must be
safe integers. Eligibility is `persistent && domainVersion===1 && lab &&
view==='lab' && observer===player`; view is additionally bound in the identity. This
frontend eligibility is presentation only: the native Host still owns grant,
session, actual player and source validation. Character/Omni lens never inherits
player inspection merely from having Lab access. D2 stays unavailable.

## Closed decoding

Reject unknown/missing keys, arrays in place of objects, unsafe/fractional
integers, non-JSON prototypes/accessors/symbol keys, malformed scopes, bad enums,
out-of-range counts, duplicate row identities, malformed/cross-view cursors,
wrong session/scope/head/native player/privacy/view/packet/binding and whole
reply UTF-8 size over65536. Return detached frozen JSON data; never assign
untrusted keys onto prototypes or execute HTML. Parsed objects cannot reveal
duplicate RAW JSON keys already overwritten by the transport; that check belongs
to the native raw parser. Proxy execution is not a property of JSON IPC data.

Decode actual Rust TypedPacket metadata, Entry variants and AcceptedEvent
version/scope/sequence/turn/rules/seed/story_time/participants/witnesses/outcome.
Effect fields follow the existing Core serde shape, with integer/string/set
bounds; no alternate engine or eligibility inference. Preserve observations,
statements and beliefs as distinct labels. Entry SourceRefs bind exact original
scope and positive sequence within the selected packet's revision interval.
Inherited source branches in the same story are allowed. Literal control text
and Unicode remain inert text, subject to actual Core text/whole-byte bounds.

Coverage getters/fallback are exact shared fields. Raw fallback carries zero
packet rows. Verified prefix below head stays verified with raw delta; do not
call it stale, a complete summary or a finished job. Job status is not joined
from another read. No seed, canonical history, job handle or model metadata is
invented. Packet indices/counts and entry indices/totals use shared32/256 caps.
Cursor is exact `mp1:<positive canonical offset>:<64lowerhex>`, bound locally to
view and offset; the opaque digest's authority remains Rust. Cursor continuation
must correspond to the requested offset and returned whole rows.

For source, expected Query2 is fixed using the PREVIOUSLY checked descriptor's
through_revision, selected context scope/head and actual native player. Never
derive expected at_revision from the returned page. Call existing checkedPageV2
on the ACTUAL returned Page2 with Player/History/limit64/fixed sequence search;
do not construct a substitute page. Require matched=true and an actual Event
row with exact requested source scope+sequence. Additional eligible search
matches are allowed; only the exact event establishes the source match.

No exported standalone Query2 renderer exists in the current allowed files.
The new panel uses the actual checked Page2/types and inert row rendering,
consistent with ComparisonReaderPanel's text/JSON display. Existing private
V2PlayPanel NativeRow and legacy query decoders are untouched.

## Selection, pending and recovery

Every session/story/branch/head/player/lens/view/grant/domain/persistence/epoch
change retires pending reads and clears packet/entry/source data before notifying
subscribers. Invalid contexts fail closed. Install operation identity before
pending notification, then recheck ownership before invoke and after await;
synchronous subscriber navigation/dispose/clear cannot dispatch or publish an
old read. No operation IDs/registry, cleanup claim or inference cancellation is
invented: an outstanding native read may finish, and its stale reply is ignored.

Refresh explicitly clears all data and requests initial packets with null
binding/cursor. Packet and entry continuation sends only the last checked next
cursor. Select only a checked packet descriptor; source only a SourceRef in the
current checked entry page. Entries and source carry the retained binding.
No automatic read, retry, generation, maintenance, search or polling.

Any current transport/native/wire failure clears packets/selection/entries/
source and shows a bounded fixed error; recovery is an explicit fresh read.
Stale or Binding never preserves old private content for another action.
Changing selection clears its old entries/source before announcing pending.
Root's surrounding mount must supply the coherent actual context and call
contextChanged; panel refuses to render when its context does not match.

## Qualification limits

Checker is frozen before module implementation: synthetic source-shaped DTOs,
strict decoder/actual controller/mock IPC and React SSR semantics only. Cases
cover direct wire/actions, packet→entry→source binding, wrong at_revision and
source scope, unsafe/unknown/malformed/hostile values, fallback/prefix, context/
observer/grant/domain/epoch/dispose and synchronous notification fences, read
errors/explicit refresh, no write commands, escaped text and disabled states.
These are not actual Rust JSON, native IPC, real WebView, model or device proof.
Root owns execution, corrections, native fixtures, app mounting and final gates.

# Development scene bootstrap: Controller oracle contract

2026-10-27. Refs #25 (D04.04/D04.05), supporting #23 (D02.03/D02.04).
First independent source-only freeze against
`582fc58826ce4ce3215e5ca6856aa7a7e84819ab`.

**Proposed, UNCOMPILED/UNRUN at author handoff.** The new Controller API is
absent at freeze. Missing API/build/setup is a prerequisite, not behavioral RED.
This contract and `apps/desktop/check-scene-bootstrap-review.mjs` precede Root's
production implementation. No Node/esbuild/compiler/formatter/Cargo/test,
native IPC/bootstrap, model, application, WebView, Android, device, desktop
control or screenshot execution is claimed by this author.

## Frozen public seam and compile-time fence

The existing four Controller constructor arguments retain their order,
defaults and meaning. Add only a fifth boolean development-scene permit,
default false. Its trusted-native fixed-cohort use does not configure a
provider, grant author/observer privileges or authorize an arbitrary runtime.

Development behavior requires both the explicit permit and the compile-time
guard `typeof __DEV_HARNESS__ !== "undefined" && __DEV_HARNESS__`. A normal
undefined/false build must ignore even a true fifth argument. A true build
without the permit also retains normal behavior. Keep test/development hooks
out of normal admission; do not use a renderer-supplied policy or general
execution/debug endpoint.

Add public `async refreshFreeTextProvider(): Promise<void>`. Only when compiled
for development, permitted and not disposed does it call the actual Host
Gateway path with exactly `{ op: "model_status" }`. This is distinct from the
existing ordinary native model-manager `refreshModel()` status read. It never
calls configure/import/load or manufactures a loaded model.

Add State `freeTextProvider`, initially null, with the exact transport type:

```typescript
null | { provider: "scene-native-fixture-v1"; kind: "synthetic_fixture" }
```

Publish only those two fields on successful metadata validation. Do not retain
the Host's whole profile in readiness or copy it into model availability.
`state.model`, including `loaded`, remains owned by existing ordinary model
status handling. Reading fixture metadata does not automatically select local
mode, submit text, change a session or commit a turn.

## Exact fixture metadata and transport-only validation

Successful Host DTOs have exactly five own top-level data keys:

```typescript
{
  provider: "scene-native-fixture-v1",
  real_model: false,
  loaded: false,
  status: "configured_fixture_owner",
  profile: { id: "scene-native-fixture-v1", /* bounded opaque JSON metadata */ }
}
```

The profile is a bounded plain object with matching own data `id`. Other profile
metadata is opaque transport data: do not add Rust profile/hash/token-budget or
construction validation in JavaScript. Positive oracles intentionally use
non-engine opaque hash/budget labels and nested JSON metadata. Actual fixed
profile validation remains in Rust. Extra profile metadata is allowed; extra
top-level DTO keys are not.

Inspect own data descriptors before reading fields, serializing or traversing.
Reject null/array profiles, wrong/missing IDs, accessors at any visited level,
custom prototypes, callable `toJSON`, cycles and oversized metadata. Do not
execute response getters or `toJSON` while rejecting them. This is finite
descriptor/JSON-size safety, not a claim about arbitrary Proxy code or profile
semantics. The oversized oracle uses a one-MiB string to exceed the intended
small diagnostic transport, without freezing a new Rust/profile limit.

Malformed current replies clear readiness and publish bounded `Wire` category
evidence without profile payloads. Existing ErrorBuffer cap remains 64 records.
No validation failure or metadata read invokes generation or provider changes.

## Admission and routing behavior

`setPlayMode("local")` and the existing legacy `send()` free-text admission may
accept the fixture only with all three conditions: development compile flag,
explicit constructor permit and actual validated fixture readiness. Otherwise
existing real-model loaded admission remains unchanged. Losing readiness while
local mode remains selected must refuse a subsequent legacy send with
ModelUnavailable before any free_text/submit/prepare/commit invocation; do not
silently change it into a typed fixture action. Typed fixture behavior outside
local mode retains its existing meaning.

The positive legacy send oracle uses a real legacy PlayView Gateway without
`playSnapshotV2`. It exercises the actual public Controller request/run methods
and checks exact scoped free_text data, original turn identity, no fake-mode,
profile or construction argument, and unchanged model.loaded=false. Its synthetic
prepare deliberately returns Agency with no receipt or revision change. This
proves frontend dispatch plumbing only, not an accepted Rust/native turn.

Separately, under development plus permit, `Controller.refresh()` retains the
actual `checkedPlaySnapshotV2` Domain1 snapshot for Main's V2 route, with
`domain_version` still 1, `playV2` equal to the checked DTO and legacy `play=null`.
Normal Domain1/default-player routing remains legacy, even if the constructor's
permit is true in a normal build. Development without a permit remains legacy.
Existing Domain2/custom-player routing and checker authority are unchanged.
Malformed snapshots must still fail Wire before legacy fallback. No fake
Domain2 marker, alternate projection or hidden facts are invented to activate V2.

Legacy Controller.send still requires its legacy PlayView. This contract does
not add thin-snapshot sending to it. Main's actual V2PlayController send, native
bootstrap configuration and native render journey are separate later gates.

## Read sequencing, disposal and independent metadata

Fixture provider reads use their own monotonic sequence, independent of existing
model reads and story refresh reads. An older valid reply cannot restore
readiness cleared by a newer invalid reply. An older malformed reply or rejection
cannot clear newer valid readiness or publish an obsolete Wire error.

Ordinary refreshModel while a provider read is pending must not discard a valid
provider response merely by sharing its read sequence. Fixture status never
changes ordinary model state. Disposal invalidates pending provider reads,
clears readiness and prevents both late publication and new metadata calls.
Do not require a live native session merely to validate this process-owned
fixture metadata; it is neither a selected story grant nor generation authority.

## Test method, limitations and later command

The new check bundles the actual Controller through esbuild in three variants:
development flag undefined, false and true. It uses only public Controller
construction/actions/state/semantic/error interfaces and raw synthetic Gateway
responses. Adversarial response descriptors are preserved rather than cloned or
JSON-normalized before the actual decoder sees them. Requests are recorded as
ordinary synthetic transport. No production test hook is introduced.

The first source freezes 43 cases. They cover default/false permits and normal builds, valid opaque metadata,
local free_text dispatch without model fabrication, unchanged ordinary loaded
model admission, wrong/missing/extra tuple fields, profile shape/ID/size,
accessors/toJSON/custom prototypes/cycles, unready local send, actual checked
Domain1 thin retention, legacy routing, malformed snapshots, stale read order,
ordinary-model read independence, disposal and bounded category-only errors.

After Root implements the frozen seam, run from `apps/desktop`:

```powershell
node check-scene-bootstrap-review.mjs
```

At first handoff this command is UNRUN. Source/whitespace inspection does not
establish that it compiles or passes. Later compilation/API/fixture calibration
must retain attribution and must not be labeled behavioral RED. Root owns
independent review, production and actual command execution/registration.

These controller tests do not qualify native fixture ownership, actual Host
model_status output, Engine profile/recipe/hash authority, canonical receipt
acceptance, Store durability, cancellation/drain, actual Main/V2 controller
composition, IPC, native WebView rendering or real-model behavior. Native
bootstrap must use the fixed trusted development cohort and real native owner;
UI labels must identify synthetic inference and actual progress/storage honestly.
New model samples and human assessment remain separate; the original human
eight-sample needs-improvement judgment is unchanged. No desktop control,
protected chat/resource access, arbitrary execution or new runtime approval is
authorized by this source-only contract.

## Additive first dispose-called admission oracles

This source-only freeze appends two cases after the unchanged original 43 cases
and runner, based on Root production `d105cbdb`. No existing assertion or
production path is edited. A separate additive runner executes only the two
newly registered cases, so the original suite remains intact and neither group
is accidentally skipped or run twice. At author handoff these additions are
UNRUN; Root owns the meaningful unchanged-production baseline, private closing
fence and unchanged rerun. A source finding is not an executed behavioral RED.

The provider-metadata admission boundary starts synchronously when `dispose()`
is **called**, before that Promise finishes. Invalidating existing reads is
insufficient if `state.disposed` remains false while `invalidate()` awaits export
or admitted legacy-turn cancellation. During that interval no new Host
`model_status` query, readiness publication or metadata-error evidence may be
admitted. This requires no new public API, fake disposed state or early change
to the existing legacy cancellation ordering. Root can use a private synchronous
provider-closing fence checked at read entry and settlement.

The first new case calls actual public `dispose()` and immediately calls
`refreshFreeTextProvider()` in the same JavaScript turn, without an intervening
await. It records whether the actual Gateway was called, then awaits both
operations and checks no readiness/error resurrection or gameplay write.

The second uses actual legacy send, its real scoped free_text admission and
held prepare/cancel Gateway Promises. After public disposal reaches its genuine
legacy-cancel await, it tries valid and malformed provider replies separately.
Both attempts must dispatch zero new Host metadata calls and retain null
readiness and unchanged visible/buffered errors while cancellation is pending.
The ordinary model.loaded value stays false. All held Promises are released in
finally using the original request's scope, turn and revision, before awaiting
send/disposal settlement; no actual native worker or canonical receipt is used.

Only this module's existing bounded synthetic Gateway and public Controller
methods are reused. These oracles do not inject private Controller state, add a
test hook, bypass cancel or measure Rust/native process drain. Normal builds and
default permits retain their original 43 controls. The existing command remains
`node check-scene-bootstrap-review.mjs`; it was not run by this author. Source,
append-only/whitespace and commit/hash inspection are the only author checks.
No formatter/Node/Cargo/compiler/test/model/app/native/render/device/desktop or
protected-resource work was performed, and no human quality result changes.

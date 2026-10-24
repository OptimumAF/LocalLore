# Typed fixture inference on corrected branches

Frozen source contract, 2026-10-23. Base `13e92ed`; delegated
`desktop_memory_ui`, partial M08.03/.06 and D08.05. No execution by this author.

## Observed integration gap and bounded implementation

Root reports its actual native cohort reached 71 checks/eight application-owned
WebView images, including Mira's observed A after world B and Sable isolation,
then typed Give failed `Version` before commit, retaining head 2. This is Root's
reported native evidence, not a new execution here. Source `inference::execute`
unconditionally requests legacy `Engine::character_context`, whose Domain2
closure is deliberately `Version`. Engine typed preview/commit and Store
already support CanonicalPlayV2; weakening that closure is not the solution.

The approved smallest change is only `crates/locallore/src/inference.rs`:

- Add native Rust-only `Input::DirectorV2 { request: Request,
  context: Box<CharacterContextV2> }`.
- Domain1 retains `Director` and the same legacy context type/bytes. Domain2
  requests actual `character_context_v2` for `engine.seed().player` with the
  exact selected scope/head and the same 32,768-byte context guard.
- Keep the same request preflight, expected typed proposal, preview, generation
  budgets, cancellation, narrator and Engine commit. FakeProvider's two Director
  arms share the same `Engine::proposal` behavior and existing fake modes.
- Structured input, real Play/compiler policy, Core canonical authority, Host
  protocol/wire/schema and Store persistence/transactions are unchanged.

No alternate pipeline, unfiltered world context, inspection privilege, new
transport/persistence, model work or native/frontend change is allocated.

## Frozen tests before production

Three new Core cases in `m08_typed_inference_v2_review.rs` use real Seed,
discovery, author prepare/apply and existing FakeProvider. A recording adapter
delegates generation to that provider. Default and custom hero players discover
A before correction B; Mira retains A, Sable lacks it, and NPC `player`-only
knowledge cannot enter hero generation. Typed Give/Wait require exact actor-only
DirectorV2 input, narration stage, inventory/revision and CanonicalPlayV2. Exact
retry returns the same receipt with zero provider calls even with cancelled
token; strict continuation replay preserves records/projection/basis. Failure,
rejection, cancellation and narrator-stage cancellation leave all canon/basis
unchanged. A Domain1 case retains actual legacy Director/context and legacy
canonical representation.

The new variant is checked through its actual derived Debug representation
against the actual Engine-produced CharacterContextV2/request. This avoids a
missing-API compile failure on the frozen baseline, so Root can observe the
actual existing `Version` runtime failure before implementation. It is a
transport-type/context equality oracle, not a second canonical validator or
serialization contract. No fabricated receipts or accepted records are used.

Two new workspace cases in `m08_typed_host_v2_review.rs` create genuine SQLite
histories with public Store APIs, reopen the actual workspace Host and execute
typed submit/prepare/commit. They cover both native inspection grants, default
and custom players, exact receipt retries after restart, prepare/no-commit,
parent preservation and strict persisted CanonicalPlayV2 restoration. Private
inspection can read B only with permission but never reteaches actor generation.
Queued cancellation, cancelled/failed/malformed fake modes and inventory guard
preserve accepted canonical records/projection/basis. No fake persistence port,
SQL canonical writer or real model is involved.

## Exact ownership, compatibility inventory and next checks

Owned paths are inference.rs plus the two NEW tests and this NEW contract.
Before production, send the frozen commit to Root for actual RED. This author
must not run Cargo, Node, SQLite, app/native/model/device or desktop tools.
Root later runs focused tests, strict Rust/frontend/native/Android compatibility
as appropriate and its actual same-UI/native journey again. Suggested focused
commands from repository root:

```powershell
cargo test --locked --offline -p locallore --test m08_typed_inference_v2_review
cargo test --locked --offline -p locallore-workspace --test m08_typed_host_v2_review
```

Source inventory of `Input::` sites found the exhaustive production match in
inference.rs FakeProvider. Local-runtime adapter, Android Play probe/fixture,
evaluation and capture consumers explicitly require Structured with `let-else`
or wildcard rejection; they remain closed and need no speculative widening.
Existing Core/Store/Host tests also largely use Structured plus wildcard paths.
Compiler/Clippy validation is still required by Root; an overlooked exhaustive
consumer must be reported for allocation rather than edited outside ownership.

All five tests are frozen source, uncompiled/unrun at handoff. No performance,
native IPC/render, model quality, physical Android/device, SQL Full/Busy fault
or whole-milestone acceptance is claimed. Generated synthetic artifacts remain
local; no protected chat/resource or desktop is touched.

## First Root baseline and accessor correction

Root imported the freeze into `7a0394e`. Its first actual Core compilation
failed E0616: this new test incorrectly accessed private `Receipt.request` and
`Receipt.events` at lines 95/96. The separate minimal correction uses the public
`request()` and `events()` accessors, comparing the request reference with
`&request`. Assertions, expected values and test coverage are unchanged. This
was an oracle-source integration mistake, not a behavioral RED result; Root's
`typed-v2-core-original-red.log` is retained.

The actual workspace Host test compiled and ran **0 PASS / 2 FAIL** before
production: both cases encountered `Version` at typed prepare, including the
cancelled fake mode before its provider could run. Evidence remains in
`typed-v2-host-original-red.log`. These logs were read, not rerun, by this
reviewer. Corrected Core runtime RED and subsequent implementation qualification
belong to Root; no GREEN is inferred from source edits.

## Allocated source implementation

After the accessor correction was separately committed as `0b61116`, Root
authorized source-only implementation while it independently reruns corrected
Core RED. The production diff is confined to inference.rs: import the existing
CharacterContextV2, add DirectorV2, select the actual actor-only context through
an explicit Domain1/Domain2 match (unknown domain remains Version), and share
FakeProvider's existing proposal arm. Each domain retains the identical context
budget, player, request scope and expected head. The context is constructed and
bounded before any provider poll. Exact recorded retries still return before
context construction/generation; cancellation and narrator/commit ordering are
unchanged. No production code has been compiled or executed by this author.

Source inspection found no other exhaustive inference Input match requiring an
owned-path extension. Structured-only consumers keep rejecting non-Structured
input through their existing let-else/wildcard closure. No consumer is widened
and no generated/native/frontend contract changes. Root must independently
compile and run the frozen five tests, broader shared/strict/native/Android
compatibility checks as applicable, and the interrupted actual native journey.

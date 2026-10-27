# Scene receipt transport: first independent oracle freeze

2026-10-27; D04.04 (#25), supporting D02.03/.04 (#23), D05.03/.06 (#26).
SOURCE ONLY / UNCOMPILED / UNRUN. No implementation or UI qualification is
claimed. Branch `test/d04-scene-receipt-transport`, based on `232ad379`.

## Exact scope and boundary

Own only this new document and new
`apps/desktop/check-v2-provenance-fields-review.mjs`. Production decoders, the
existing verifier, native app and all other owners' files remain unchanged.
Claims: [#25](https://github.com/OptimumAF/LocalLore/issues/25#issuecomment-6451346284),
[#23](https://github.com/OptimumAF/LocalLore/issues/23#issuecomment-6451346802),
[#26](https://github.com/OptimumAF/LocalLore/issues/26#issuecomment-6451347229).

The test bundles the actual V2PlayController with the established esbuild import
pattern, and calls only its public context/refresh/send/status/retry/inspection
methods. Fake Gateway responses are synthetic DTOs. They are not accepted Rust
receipts, canonical fixture histories, native IPC, SSR, DOM, WebView, model or
device evidence. In particular, the tests do not compute Engine frame hashes,
validate recipe/context tuples or make generation/observer grants. Existing
policy/prompt/context transport data remains opaque. Historical prompt strings
are compatibility inputs, not claims that the synthetic records satisfy every
historical Engine validator.

## Frozen optional shapes

`PlayRecord.scene`, if present, is exactly `{version:1,frame_sha256:string}`.
`PlayRecord.story_presentation`, if present, is exactly
`{version:1,presentation_sha256:string}`. Each hash is exactly 64 lowercase ASCII
hexadecimal characters. Omission remains valid; null is not omission. No extra
or future keys, alternate versions, arrays, wrong types or oversized values are
accepted. Accessors, toJSON functions and custom prototypes must be rejected
without invoking user code, using the established descriptor-first bounded JSON
boundary pattern. This does not confer semantic authority on well-formed hashes.

Current `v2-play-controller.ts::receipt` excludes both optional keys. Its local
`detached` currently stringifies before descriptor inspection; the stronger
existing pattern is in `v2-view-model.ts::detached`. The production owner must
choose the smallest reuse/extraction without broadening schemas or authority.

## Finite oracles

First calibrate existing no-play receipt acceptance, actual refresh at the new
head, historical 2.1–2.8 omitted fields, and opaque policy/context transport.
A calibration failure stops remaining cases and is reported separately from
behavior failures. Build/import/public-API absence is also setup failure, not
behavior RED. No execution is claimed in this first freeze.

Positive DTOs cover both 2.9/2.10 scene prompts with/without presentation, and
presented 2.7/2.8 prompts. Negative cases exercise both optional fields: null,
array, missing hash, extra future key, future/string versions, non-string,
uppercase, short/nonhex/oversized hashes; enclosing-field getter, nested hash
getter, toJSON and custom-prototype rejection. Adversarial replies are returned
raw, with no test stringify/clone that erases their properties.

Scheduling cases preserve original-key unknown outcomes: a dropped committed
reply followed by status recovers exactly the scene fields without another
submit/commit; dropped admission plus explicit retry retains the exact request.
Same-object receipt inspection uses current head/Player turn_diff and performs
only an inspection read; a cloned receipt cannot dispatch. Held actual commit
replies cannot publish receipts into a changed session, scope, head or character
lens. These are transport scheduling assertions only, not canonical cancellation
or persistence tests.

## Native follow-up remains separate

`models.rs` still configures the normal default through
`configure_local_provider`; do not change that default. New fixed development
arms should use trusted `configure_fixture_provider_with_construction` with
`MemorySceneV1(StateRelevantMemoryV1)` or `PlayerLiteralSceneV1`, on a constrained
synthetic workspace. Never mark a scripted provider as real. No renderer API
selects arbitrary policy, actor, file, model output or construction.

The current V2 `playMode:local` selects free-text submission but labels the panel
"Local model" independently of actual provider identity. A synthetic scene
journey must expose truthful fixture/provider provenance before asserting a
rendered UI is honest. Native Host model_status already distinguishes
`configured_fixture_owner`/`real_model:false`; it must not be confused with
ModelManager asset status. Persisted scene provenance does not prove a current
model is loaded, nor does a process restart restore provider ownership.

Reuse the actual author-native journey Controller/V2 controller/IPC/Store route:
Domain1 parent for literal and corrected Domain2 child for memory. Reuse coherent
semantic/DOM snapshots, bounded ErrorBuffer/native output and existing hidden
unfocused app-owned WebView CapturePreview. Cold reopen uses actual narration
history plus traceRecordedTurn, with no invented raw receipt. Real IPC, Store,
render layout, pending/cancel/stale/observer isolation and model/human-quality
gates require later execution and independent evidence.

## Handoff

Source inspection and `git diff --check` only; no formatter, Node, Cargo, test,
model, app, device, desktop control or protected resource access. Root owns
independent review, fixture calibration, meaningful current-source baseline
execution, decoder implementation and unchanged-oracle rerun. After acceptance,
Root may register the checker in the existing verifier. Proposed standalone
command: `node apps/desktop/check-v2-provenance-fields-review.mjs`; it has not been
run by this source author. No task checkbox, release or merge is authorized here.

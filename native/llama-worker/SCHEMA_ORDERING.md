# Constrained JSON property ordering correction

Refs #25 D04.04. The pinned converter fixes a generated object's required-key
sequence from its `properties` insertion order, **not** its `required` array.
The worker's nlohmann::json transport map sorts keys alphabetically, so its old
schema dump required `item` before `op` for Give even when the prompt/example
requested `op` first. Wait/Move could start with `op`, creating an inconsistent
branch discriminator position. This is a demonstrated grammar incompatibility;
its contribution to actual model action-selection errors still needs the
coordinator's real-scene rerun. Do not infer prose quality from a grammar fix.

Primary source pin: llama.cpp v0.7.0,
`620d2225cc436ab0b001e3200e590e3b286ef9ab`. Rechecked official sources:

- [json-schema.cpp](https://github.com/ggml-org/llama.cpp/blob/620d2225cc436ab0b001e3200e590e3b286ef9ab/common/json-schema.cpp): object properties are added in their iteration order.
- [json-schema-to-grammar.cpp](https://github.com/ggml-org/llama.cpp/blob/620d2225cc436ab0b001e3200e590e3b286ef9ab/common/json-schema-to-grammar.cpp): `_build_object_rule` gathers and emits required properties in that order.
- [json.h](https://github.com/ggml-org/llama.cpp/blob/620d2225cc436ab0b001e3200e590e3b286ef9ab/common/json.h): common_json preserves insertion order.

`schema_order.h` recursively rebuilds the existing schema into common_json.
Within `properties`, its deterministic priority is:

`op, text, item, to, quantity, audience, ability, claim_event, fact, ticks, event_ids, speaker`.

Absent priority keys are skipped and remaining keys keep deterministic transport
order. Thus Give becomes `op,item,to,quantity`, Say `op,text,audience`, narrator
`text,event_ids,speaker`. All property values, required membership, numerical
bounds, arrays, constants and additionalProperties constraints remain unchanged.
Both chat-template schema formatting and the explicit grammar converter use
this same ordered object. Nothing is reserialized through the sorted transport
map between those two paths. No dependency, shared engine/parser/schema, model
weights, inference authority, tool or network capability changed.

## Actual native model-free grammar verification

From repository root, with the existing clean reviewed upstream checkout and
installed CMake/MSVC:

```powershell
powershell -NoProfile -File native/llama-worker/build.ps1 -SourceDir <reviewed-llama-source> -BuildDir target/d04-worker -CmakePath <installed-cmake> -SchemaTest
python native/llama-worker/test_protocol.py target/d04-worker/locallore-llama-worker.exe
```

The first command passed incremental Release compilation/linking of the worker
and the explicit `locallore-schema-order-test` target. That target is
EXCLUDE_FROM_ALL and is not linked into or packaged with the application worker.
It uses the actual pinned converter and grammar-machine character acceptance,
with null test vocabulary and no model load; no regular-expression approximation.
Output: `native_grammar_assertions:13`, status passed.

The13 assertions establish:

1. Reordered schema JSON has identical semantic values.
2. Original converter rejects op-first Give despite op-first required array.
3. Original converter accepts its alphabetical item-first Give.
4. Corrected converter accepts op-first Give with item/to/quantity.
5. Wait remains legal; this is not a forced-gift branch.
6. Unknown operation rejects.
7. Zero quantity rejects.
8. Extra field rejects.
9. Text-first narrator with event IDs and speaker accepts.
10. Wrong event reference rejects.
11. Wrong narrator speaker rejects.
12. Say op/text/audience sequence accepts.
13. Changed exact dialogue literal rejects.

The second command separately exercises existing actual-worker model-free wire
validation; its result is recorded in the ticket handoff. These checks are native
grammar/protocol execution, not actual local-model scene generation, engine
execution, app IPC or rendering. The coordinator owns the next real-model scene
run and package staging/provenance update.

New actual Windows worker SHA-256:
`eda393e923ddfd03ea57d91741d8f7948d1a4af13deb90c7d6c90c492e63ff58`.
It replaces the earlier measured `fd5d0e99...f70fcd00` build for new tests. The
runtime hashes the actual locked executable, so the new identity must be
recorded with each new turn. Profile-v1's workload/configuration manifest is
unchanged; the worker hash distinguishes this corrected executable behavior.
There is no claim of identical old/new outputs or reproducible binary builds.

No model was copied/downloaded or loaded by this ordering packet. Existing own
CMake objects/libraries were reused; no duplicate Rust dependency build or
protected experiment/source edits occurred. No desktop/device control was used.

# D04 Author worker admission: proposed B1 contract

**Source proposal for independent review; no B implementation or checks yet.**
Refs #25 D04.02/.04, shared #9 and #21. Documentation claim:
[#25 comment 6545862215](https://github.com/OptimumAF/LocalLore/issues/25#issuecomment-6545862215).
Base: accepted PR301 merge `3cea6a53caed58794075070e5a9adb7cf70eb45d`.
This document grants no worker, model, application or device execution authority.

## Accepted A and the remaining boundary

[Packet A](D04_AUTHOR_LANE_CONTRACT_2026-10-30.md) implements bounded Author
requests in the existing Rust provider/runtime. Both production gates remain
Disabled. Only the two fixed test fixtures can enable them. Public generation
selects Author's requested tokens and 8192-byte default; compiled Author calls
carry their exact token/byte bounds. Play reply parsing remains 350/16384.
The shared Host still owns generation, proposal validation, review, creation,
cancellation and exact retries. The worker cannot create a story or change canon.

The current application worker admits director/narrator at most 350 tokens in
`native/llama-worker/main.cpp`. `generate.inc` caps generated and final content
at 16384 bytes. The embedded `profile-v1.json` declares 350 for every role.
Rust's profile getter embeds that file; desktop staging and ModelManager pin
the accepted worker bytes. Adding Author to the C++ predicate must not silently
turn those old artifacts, profiles or provenance records into Author support.

The chosen direction is a separately named, experimental worker and versioned
combined manifest. The ordinary target, legacy manifest and default Rust
constructors retain their existing behavior and adoption. B1 provides the small
worker-side source seam and independent tests; B2 owns any qualified artifact
adoption. No second provider, runtime owner, model registry or inference backend.

## B1: closed pure admission interface

Propose NEW `native/llama-worker/worker_generation.h`, using existing nlohmann
JSON and C++17 only:

```cpp
enum class GenerationAdmission { LegacyPlayV1, InitialWorldExperimentalV1 };
struct GenerationLimits {
    std::uint16_t output_tokens;
    std::size_t text_bytes;
};
std::optional<GenerationLimits> locallore_generation_limits(
    const nlohmann::json & generation,
    GenerationAdmission admission = GenerationAdmission::LegacyPlayV1);
```

Invalid DOM values return `std::nullopt`; no model, context, process, I/O,
environment, clock, allocation owner or callback is introduced. The worker maps
refusal to its existing `invalid_request` error. A ceiling is not a measurement.
The returned `output_tokens` is the **validated requested count**, not the role
ceiling: director 64 returns 64; Author 1 returns 1. Narrow only after range checks.

| Condition | LegacyPlayV1 | InitialWorldExperimentalV1 |
| --- | --- | --- |
| Generation object | Exactly role, prompt, schema, max_tokens | Same four keys |
| Role | director or narrator | director, narrator or author |
| Tokens | Unsigned JSON integer 1..350 | Play 1..350; Author 1..1024 |
| Prompt | Nonempty, NUL-free string | Same; Author additionally at most 16384 UTF-8 bytes |
| Schema | Object or null | Play unchanged; Author requires an object |
| Returned text cap | 16384 bytes | Play 16384; Author 8192 bytes |

Booleans, signed DOM numbers, floats, strings, null and integers beyond the
selected ceiling are not token counts. Test positive wire values by parsing
JSON text or explicitly constructing unsigned values; a C++ integer initializer
can otherwise create the wrong DOM type. Check UINT64_MAX and values such as
65537/66560 before a 16-bit conversion, never after truncation.

Do not impose Author's 16KiB prompt limit on Play. A 16385-byte Play prompt is not
currently rejected by generation admission; the unchanged outer 32768-byte frame
and tokenized 4096-token context can reject it later. Unknown roles and extra or
missing generation keys remain refused. Operation-looking prompt text is data.

The C++ helper does not duplicate Rust's initial-world schema/proposal validator.
Rust A already requires the actual shared schema, draft identity and profile.
The worker requires an object and forwards that exact value through the existing
`locallore_ordered_schema`, chat-template input and explicit grammar conversion.
No hand-written schema, seed, SQL, tool call or consequential model fact is added.

## Integration and preserved behavior

Main computes limits once after the existing outer request/model admission,
then passes the immutable value into the existing owned work closure and
generation function. Preserve current error precedence: an unloaded worker's
`model_load_failed` is not evidence that generation validation ran.
Use the returned requested token count in the generation loop and the returned
text cap for BOTH the generated-content check and final visible-content check.
Keep existing `output_limit`/`unexpected_output` failures; never truncate output.

There is no fifth generation field or wire byte budget. Author's worker cap is
8192; Rust's operation-bound parser can enforce a smaller admitted byte budget.
Do not infer that text fitting a role cap guarantees its escaped JSON frame fits:
the existing 32768 transport bound remains authoritative and may refuse it.
Thinking markers, reasoning, tool calls, malformed replies and stale IDs keep
their existing refusal paths. Response/metrics shape and ordinary Play behavior
remain unchanged. Keep context 4096, sampling/template settings, 60s operation
deadline, cancellation, cleanup and worker ownership unchanged.

The default `locallore-llama-worker` target selects LegacyPlayV1. A separately
named `locallore-llama-worker-initial-world-v1` target may select the experimental
constant through a fixed PRIVATE compile definition and is EXCLUDE_FROM_ALL.
No CLI argument, environment variable, JSON role alone, editable profile or
caller-supplied expected hash selects this compiled mode. Default staging keeps
its accepted fixed worker identity. Recompilation does not prove identical
legacy bytes; preserve the accepted artifact and refuse unreviewed replacements.

## Independent FIRST and implementation order

Independent FIRST owns only NEW `native/llama-worker/worker_generation_test.cpp`.
It must include the actual production header and exercise both enum modes, not
copy the predicate. Missing header/API/build prerequisites are UNRUN_SETUP.
Freeze assertions before a different author implements admission.

1. Producer extracts the existing Play-only predicate into the typed seam,
   including both enum values but no Author acceptance. Freeze source.
2. Root admits and runs the fixed pure-validator baseline. Compilation failure,
   missing dependencies, output overflow or an incomplete test summary is not
   behavioral RED. Retain complete failed evidence and known child closure.
3. Only after a valid baseline, producer enables Author solely in the
   experimental mode and wires role-specific caps through the same generator.
4. Root verifies the unchanged FIRST plus appropriate legacy/source checks.
   Any later assertion expansion or fixture correction retains separate lineage.

The finite matrix must cover legacy compatibility; exact four-key shape;
all token types and boundary/narrowing cases; role/schema/prompt binding;
Author token 1/64/1024 and 1025 refusal; Play 350/351; Author UTF-8 prompt 16384/16385;
NUL/empty strings; Play's distinct prompt behavior; null/object/array schemas;
returned 8192/16384 caps and lower requested token counts. Unknown enum values
must refuse rather than fall back to the experimental mode.

Source integration controls must verify the fixed compiled mode and the SAME
computed limits reach loop/stream/final checks; label them source controls.
DOM-only tests cannot establish raw duplicate-key or invalid UTF-8 handling once
parsing has lost that information. Preserve Main's duplicate-aware parser and
its existing raw protocol tests; report those as separate evidence. In particular,
`test_protocol.py`'s generation while unloaded does not qualify role admission.
Actual sampling, grammar execution, cleanup under inference and quality are
outside the pure-validator gate.

## Build/provenance constraints and future ownership

Proposed production allocation, posted separately before edits:

| Path | Purpose |
| --- | --- |
| NEW worker_generation.h | One pure closed generation validator/limits value |
| main.cpp; generate.inc | Existing worker integration and two visible text caps |
| CMakeLists.txt | Fixed test/experimental targets and reviewed compiler-source roster |
| test_reproducible.py | Account new copied source inputs without widening old qualification claims |
| NEW profile-initial-world-experimental-v2.json | Unconsumed versioned manifest proposal |

All paths above are under `native/llama-worker/`. The independent test file is
owned separately. No Rust, Host, Eval, selected reader, Android, UI, dependency,
lockfile, model pin, staged executable or application permission is owned by B1.

CMake's MSVC launcher currently admits exactly main.cpp, schema_order_test.cpp
and worker_launch_test.cpp; add the one exact test basename and attach the same
reviewed launcher to new targets. No glob or arbitrary compiler-source admission.
The reproducibility script's FILES copy/inventory roster must account the new
header, test and manifest needed by the copied source. Its old three-target
build and three compiler-journal assertions remain legacy qualification.
Neither copying more source files nor passing the old qualifier proves the
experimental worker reproducible.

The existing compiler journal is keyed by SOURCE_NAME. Both worker targets use
main.cpp, so building them in one binary directory would overwrite/race evidence.
Do not do that. Before experimental-worker qualification, separately freeze a
closed distinct journal-key change OR explicitly admit isolated build directories
within the existing charged build allowance. There is no automatic new root or
target budget; if isolation does not fit, that build stays unavailable. B1's pure
test target links only the existing JSON interface, not llama/model execution.
Historical copied sources, qualifiers, journals and reports remain untouched.

## Truthful manifest and B2 adoption boundary

The proposed self-contained manifest is
`profile-initial-world-experimental-v2.json`, version 2, with profile ID
`qwen3-0.6b-q8-cpu-initial-world-experimental-v1` and explicit
source-only/unqualified status. The ID names the experimental recipe; the
manifest's container schema is version 2. Its closed per-role limits are
director 350/16384, narrator 350/16384 and author 1024/8192.
It must not retain the old scalar claiming every role is 350 or inherit a prior
worker's lifecycle/quality qualification. Include the current truthful model,
license, runtime revision, template, context 4096, CPU/sampling, thinking/tools,
request/response/stderr ceilings, 60s operation/2s drain and downloads/hosted
inference false fields; do not make it a sidecar with an unrecorded second digest.
Keep those settings unless separately changed and qualified. No new worker or
manifest digest is invented here. The new profile is unconsumed source metadata
until actual artifact identity and B2 adoption are reviewed; `profile-v1.json`,
`PROFILE` and the current global manifest getter remain unchanged in B1.

B2 must resolve the new profile ID explicitly. A's compiler currently requires
PROFILE; a new manifest alone cannot enable it. Prefer an immutable owner-selected
profile identity/digest rather than globally replacing PROFILE or the embedded
getter and retroactively relabeling an old loaded owner. PlayProfile's director
and narrator fields stay 350: they are Play limits, not Author's 1024-token budget.
The shared InitialModelConfigurationV1 records worker/manifest hashes and Play
fields while initial-world's recipe fixes Author parameters. Any additional
provenance field needs explicit schema versioning, not an opaque sidecar.

Only a future fixed qualified packaged constructor can mint production Author
access after verifying the reviewed executable on its retained handle and the
selected immutable manifest. Arbitrary expected-hash/default constructors stay
Disabled even if a caller supplies the same digest. Reuse existing LocalRuntime,
OwnedStartFailure, ModelManager singleton and cleanup reservation.
An owner-inspecting factory can capture that SAME qualified SharedRuntime and
private gate after load, then create the existing RuntimeProvider; no public
bool/hash capability, foreign-owner token, blocking lock in poll or second owner.
The native runtime still checks its independent gate before sending a frame.

No `authoring_capabilities.available` value alone proves that qualified capability:
the current Host reports persistence plus provider presence. Desktop creation
must remain honestly unavailable until its separately reviewed adoption/consumer.
No automatic proposal acceptance, review bypass or create operation belongs here.

## Concurrent work and verification classes

Coordinator-verified public handoffs supplied for this proposal, 2026-10-31:
[PR297](https://github.com/OptimumAF/LocalLore/pull/297) is open/draft,
head `0eded1650c9c2f9b9569bf2f95069a99913deb94`;
[B35/PR302](https://github.com/OptimumAF/LocalLore/pull/302) is open/draft,
head `e9086c24ff655457e5676974fc0c44d61831506d`;
[B36/PR303](https://github.com/OptimumAF/LocalLore/pull/303) is open/draft,
head `2da5bff4b34b0637194ae17ee4fa2ea5137807ae`. These are unmerged foreign
handoffs, not this packet's dependencies accepted by implication. B35/B36's
core/Android bridge, JNI and lock changes are outside this claim. B34's Eval/
descriptor work remains its owner's scope; no new tuple or historical migration.
Accepted Eval paths currently pin the old worker, profile/template identity and
Play 350 values. A future worker stays unsupported there until that owner adds
an explicitly qualified path; old reports keep their recorded identities.

Report separate gates: pure source review; compiled model-free validator tests;
actual experimental-worker compilation; reproducibility/source qualification;
artifact/profile/pin adoption; protocol/model inference; app/device/quality.
None implies the next. B1's reviewable gate is the focused source/test packet
with valid baseline, complete regressions, integration review and honest limits.
It does not qualify a packaged worker, model, original-story UI or all of D04.

Before any execution, Root must make a resource forecast/admission against the
current retained ledger, with exact closed commands, output bounds, sticky stop
and known child closure. Reuse physical D: and installed pinned tools/cache;
TEMP/TMP D:/Dev/_Temp, offline inputs, existing build storage and original target
baseline 8,259,980,576 plus 4GiB. Do not reset old 64MiB group/724MiB joint/fixture
or decoded-source charges, reuse a spent phase, delete evidence or create another
target to make checks fit. A's R3 grant and all five phases are complete/spent;
its 1344KiB metadata allowance is not a fresh B execution allocation. Routine
source/test choices already authorized by the full assignment need no extra
approval, but this proposal grants no new expensive or hazardous execution.
Worker/model/application/device qualification requires its concrete applicable
authority. All four existing native application grants remain spent.

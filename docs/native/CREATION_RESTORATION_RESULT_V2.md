# Terminal creation evidence across restoration — result v2

M09.06/M10.02 supporting contract, stacked on draft PR #213. This version
exports information missing from result1; it is not evidence that a device test
has run. The [starter probe2 contract](STORY_CREATION_PROBE_V2.md) describes the
original first-old-process export limitation.

## Closed result

The controller's quiet `proof` result has integer `version:2` and scope
`locallore_process_controller_v2`. All existing top-level keys, three process
observations, fixture/helper formats, exact GAME6 vectors and terminal identity/
sequence checks remain. The root/child/retired diagnostic counts remain82/123/139;
retained-parent diagnostic counts retain their existing positive bounded policy.
No new checked-call count is invented.

Each of the two `terminal_observations` has its seven existing keys plus exactly:

```json
{
"saved_creation": {"create": 0, "create_named": 2},
"commands_creation": {"create": 0, "create_named": 2}
}
```

This example is the first old producer. The current four fixed fresh journeys
explicitly create A and B through the named-creation dialog, so both maps must
equal that exact first pair. For the second old producer both maps must be
`{"create":0,"create_named":0}`. Values are strict integers in0..4096 before
the exact journey comparison. No booleans, floats, aliases, sums, defaults,
missing or extra keys are accepted. A legacy2/named0 pair cannot impersonate
legacy0/named2. Different saved/commands pairs refuse.

`killSaved` exports `finalSaved` and `finalCommands` separately, after the old
PID is absent, from the already closed probe2 operation map. Existing
sameCreations/sameGame checks remain. These are attempted transport calls,
not successful native commits or canonical story counts. No title, story text,
creation ID or model data is added to diagnostics.

Result2 requires all three final product leaves to use uniform probe2 with its
exact fourteen operation keys. Their current restored creation counters remain
zero. The second-old saved leaf also corresponds to the terminal saved creation
pair. Existing observation/PID/UID/task/sequence/hint/factory/gameplay/counter
monotonicity checks still apply. World state remains an independent Rust/native
oracle; neither result nor operation counters override it.

## Historical and runtime boundaries

The pure controller/product decoders continue accepting exact historical
result1 and its unchanged seven-key terminal observations, with uniform probe1
or probe2 final product leaves as previously supported. They return original
data without inventing missing exported counters. Result1 with new terminal
fields, result2 with old fields, mismatched scope/version, and mixed product
versions refuse. A historical result1 is not evidence for new creation maps.

The fixed current runtime worker requires result2 after full frame decoding.
Its parent uses `validate_current_execution`, which first performs the existing
deep source/tool/APK/owner/raw/client/helper/sidecar validation, then requires
the original bound result2. The generic historical validation entry is not a
current-run fallback. There is no CLI result-version selector.

Retirement evidence supports both exact result versions while retaining every
original helper/native state/receipt/sidecar requirement. A valid creation map
cannot waive a missing or changed canonical sidecar. Container versions and
filenames such as `external-v1.json`, `proof-v1.json`, private fixture paths and
the case-independent create-only guest claim remain unchanged; those names
do not assert that the enclosed controller proof is version1.

The4096-byte proof/4160-byte frame caps,120-second controller case bound,
host SDK/owner deadlines and existing resource/admission limits remain.
Oversized failure/result output still fails closed. No model, dependency,
permission, product gameplay authority or persistence format is added.

## Verification scope

Original host fixtures distinguish positive result2 from unchanged historical
result1, malformed or coerced counters, opposite-count aliases, missing exports,
saved/commands mismatches, automatic creation after restart, product downgrades,
raw/copy rebinding and retirement canonical-source violations.

Host tests alone do not establish Android execution. Current qualification needs
a fresh build and separate owned broad-regression and two-death cases. Each
two-death case requires the fixed native10 gate first; broad regression is
independent. Only exact original runtime records can prove those
checks. Phone, real-model inference, ARM64 execution and joined adapter drain
remain separate gates.

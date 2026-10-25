# Portable complete Dialogue audiences

Refs #9 (M05.01/M05.05), #5 (M01.05). Root rationale6398696909;
author claim6398702206. This is a narrow source compatibility correction, not
a diagnosis of an earlier stopped SDK invocation or a new supported-model claim.

## Pinned compatibility evidence

The actual pinned LiteRT-LM revision
`bda624851d74be34d4e1f7fac1fc4155939539c7` builds its constrained decoder with
[llguidance1.3.0](https://github.com/google-ai-edge/LiteRT-LM/blob/bda624851d74be34d4e1f7fac1fc4155939539c7/runtime/components/constrained_decoding/BUILD#L225-L272).
That version's [implemented vocabulary](https://github.com/guidance-ai/llguidance/blob/v1.3.0/parser/src/json/schema.rs#L13-L47)
omits `uniqueItems`, and its [known-but-unimplemented keyword handling](https://github.com/guidance-ai/llguidance/blob/v1.3.0/parser/src/json/shared_context.rs#L120-L127)
rejects that unsupported vocabulary under the
[default strict configuration](https://github.com/guidance-ai/llguidance/blob/v1.3.0/parser/src/json/compiler.rs#L67-L77).
The former Dialogue audience schema emitted that keyword. This demonstrates a
source-level mismatch; earlier retained records did not observe the discarded
SDK exception and cannot identify it as their cause.

Pinned llguidance supports an enum of exact JSON array instances: its
[enum branch](https://github.com/guidance-ai/llguidance/blob/v1.3.0/parser/src/json/schema.rs#L457-L475)
uses `compile_const`, whose [array handling](https://github.com/guidance-ai/llguidance/blob/v1.3.0/parser/src/json/schema.rs#L745-L780)
fixes length and each element. No dependency/version or lenient-decoder option
is changed.

## Same semantic sets, portable representation

Dialogue still permits exactly one `say`, exact original speech, at least one
and at most four distinct eligible nearby living non-player listeners. Eligible
IDs are already derived by the actual Director frame from the current engine
scope/revision/location and sorted by its BTreeMap. The new audience `enum`
contains EVERY nonempty subset of those IDs with size≤4. Each subset is sorted;
the catalog is deterministic lexicographic order. Nothing chooses only Mira,
the first listener, a single-listener profile or the first four IDs. For five
eligible listeners all30 semantic sets remain; for six, all56.

The existing `items.enum`, `minItems=1` and `maxItems=4` remain; unsupported
`uniqueItems` is replaced by the full exact-array enum. Empty/duplicate/self/
remote/dead/unknown/oversized and noncanonical permuted array representations
are absent from this generation grammar. This preserves semantic audience sets,
not every byte permutation of an equivalent array.

`Command::Say.audience` remains the existing BTreeSet. Deserialization still
normalizes order and duplicate array values. Engine colocated checks can permit
self speech even though this generation schema excludes it. This patch does
NOT invent a new engine duplicate/self refusal, mutate command/event/storage
contracts, or treat the schema as canonical authority. Literal interpretation,
scope, player intent, genuine empty/remote/dead/too-many-listener validation,
observer visibility, narrator restrictions, commit and replay remain unchanged.
Action schemas and existing structured profile/schema requirements are retained.

## Bounded construction and failure

The private schema builder now returns Result; its only DirectorEnvelope caller
propagates refusal. Before enumeration it checks the full base schema, including
the eligible-ID list and an empty audience enum, against the existing
MAX_PROPOSAL_BYTES16384. Its byte counter starts from that actual serialized
base. A depth-first traversal selects strictly increasing indices with depth≤4.
Each bounded candidate is serialized and its bytes plus separator are charged
BEFORE retaining it. Checked arithmetic/limit failure returns TooLarge, drops
the private partial catalog and reaches no provider. No powerset/combination
count is preallocated or truncated, and no partial schema is published.

The completed schema is checked again. Existing role JSON, prompt, context and
estimated-token budgets still run and may refuse even a complete small catalog.
No byte/token/output/role deadline or model/profile reserve is increased to
make enumeration fit. A crowded scene may need clarification/profile work later;
this patch safely refuses rather than silently discarding potential listeners.

## Authored verification and limits

The new independent integration file exercises the actual structured request
captured by synthetic providers. A bitmask reference independent of the production
traversal compares every set for n1..6, order/determinism, five-listener30 and
six-listener56 coverage, schema exclusion examples and escaped literal speech.
It records existing typed set normalization separately from grammar exclusion.
Actual engine cases cover accepted audiences of each size1..4, observer-visible
speech, unchanged hidden-narrator fallback and replay, plus genuine guard refusals
with no canonical mutation. Crowded128-listener and unchanged low-context cases
require TooLarge with zero provider calls; no-listener clarification also stays
provider-free. Existing guarded-director tests are not rewritten.

These tests are authored source, not executed by this agent. The coordinator
owns actual rustfmt/clippy/offline Rust tests and fresh Android compilation,
audits and controlled qualification. No SDK/model/AVD/cache/runtime action,
dependency download, old evidence mutation, latency improvement or previous
failure-cause attribution is claimed here.

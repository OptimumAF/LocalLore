# Literal compatibility implementation review — 2026-10-25

Refs #9 (M05.01/M05.05), #5 (M01.05). Root claim6400786067;
independent reviewer `/root/model_picker_review`, claim6400952691.
Review branch starts at `090a8694120ee37dcfb48bfd48f9f0dd67ce3377`.
See [source research](LLGUIDANCE_LITERAL_RESEARCH_2026-10-25.md) for the pinned
derivre quoting-tail omission and exact primary source links.

## Probe boundary

Reviewed the actual fixed-original literal probe, its pure tests, closed report
validator and launcher integration. The probe uses fresh matchers for each
masked, raw-validation and direct-consumption comparison. It preserves separate
results instead of treating direct parsing as masked-generation acceptance.
It retains the exact original, a deterministic deletion reduction, source
indexes, byte/hash links, and explicit budget/nonreproduction outcomes. The
128-evaluation cap is finite; `deletion_minimal` means its single-deletion
stopping criterion, not globally shortest possible counterexample.

The default JSON, equivalent Lark-default and Lark-no-forcing paths are labeled
separately from the exact serialized-output regex control. Unknown arguments
cannot select an arbitrary source corpus or child script. Native validation,
wrong-byte rejection, before/after error-state checks, known owned cleanup and
closed fixed-source report validation remain necessary to credit observations.
The worker's stdin barrier precedes native import/child work.

Direct `consume_tokens` returning false with an error flag is an observed API
failure; the final matcher error flag does not independently distinguish a
grammar error from every resource/native error. It should not be reported as
an authenticated private error cause. Mask-path resource errors abort the
experiment rather than serving as a reducing predicate.

The concrete core acceptance boundary is unchanged:
`validate_interpretation` requires a Dialogue `Say` to equal the full original
player text. A codec or SDK grammar does not gain canonical authority. A
regression must reject the incorrectly truncated text without canonical,
revision or receipt mutation, under existing bounded repair semantics.

## Finite encoder source boundary

Read the initial `FiniteSchemaRegex.kt` and its13 authored JVM tests in the
encoder author's separate worktree. That encoder admits a narrow finite schema
subset and returns null for unsupported shapes. It does not interpret gameplay
operations or accept canonical events. Its duplicate-key/syntax/UTF8 guard
precedes org.json parsing; depth12/value-node512/input32,768B limits bound the
work. Each output append is charged before mutation against32,768 UTF8 bytes.

The source requires fully required closed objects, sorts keys for a canonical
encoding, permits only a single `oneOf` alternative, and preserves supported
enum siblings without filtering invalid members. In particular it does not
approximate overlapping `oneOf` alternatives as an ordinary regex union. Its
fixed structural array has exactly one item. Arbitrary/unknown/unbounded
schema shapes fall outside this capability and must retain the caller's
existing safe format path, rather than become unconstrained output.

Canonical JSON escaping occurs before regex metacharacter escaping. The
result is anchored as a complete value. Tests cover the actual425/442B shapes,
every audience set for n1..6, the full escaped literal and wrong truncated
prefixes, extra/missing operations/properties, unsupported siblings/types,
decoded duplicate keys, surrogates, depth/nodes/input/output bounds and
immutability. No concrete semantic source blocker was found in that draft.

Those Java Pattern tests do not prove pinned native grammar acceptance. A
native claim must use patterns produced by the actual Kotlin encoder, linked
to original schema/sample hashes, rather than a separately reconstructed
Python approximation. Its compact/sorted language is a canonical
representation subset, not every JSON serialization admitted by the original
schema. Complete semantic choices and engine intent validation must remain.
Existing `schema_bytes` observations still refer to the original engine schema;
they must not be described as generated regex payload size.

The test-only conditional export in the mandatory425B test supplies an
actual-Kotlin linkage: both environment bindings absent performs no IO;
one present refuses. The bounded original corpus is checked, every finite
pattern is computed before opening a create-only output, and emitted rows
carry source-corpus SHA, schema SHA and indexes. Root's exact source/path and
strict duplicate-key checks complete that boundary; the initial helper's org.json
parser alone is not duplicate-key authentication. Credit requires all tests
passing plus a fresh artifact whose complete rows match the original corpus.

Reviewed the root selector addition as well: finite patterns select the
[pinned public Regex value object](https://github.com/google-ai-edge/LiteRT-LM/blob/bda624851d74be34d4e1f7fac1fc4155939539c7/kotlin/java/com/google/ai/edge/litertlm/ResponseFormat.kt#L26-L64);
unsupported/nonfinite shapes retain the original JSON string. Selection stays
inside the existing observed argument-preparation block. No resource ownership,
callback/fence sequence, token/turn budget or default thinking option changes
in that diff. The codec hash is bound into worker source and the Gradle source
gate, with matching worker/Candidate/manifest provenance. The explicit runtime
source closure includes the codec, its JVM test and the selector test.

The new core regression's wrong-truncated speech case expects Agency before
narration/canonical mutation; its full-original counterpart commits and replays
through synthetic providers. Those are meaningful engine authority checks,
separate from native grammar acceptance or a real model outcome.

## Failed first attempt and corrected implementation

Independently replayed the first JVM attempt's48 retained XML files against
their index:512 tests/12 failures/0 errors/skips, completed1/cleanup true in
112,359ms. Nine failures explicitly report Android methods not mocked; three
are assertion/required-nonnull failures after the stub-incompatible codec
returns null. No regex-corpus artifact was created. Initial codec/worker hashes
are historical and earn no actual-Kotlin/native bridge credit.

Reviewed the subsequent port to the already available Gson implementation,
including its13 tests and actual-pattern export helper. The strict scanner
remains ahead of parsing. Numeric primitives require an exact integer lexeme
and `toLongOrNull`; there is no floating-point truncation, string coercion or
boolean-number conflation. String/boolean type flags are explicit. JSON string
serialization precedes regex escaping; a raw HTML-character test guards against
accidentally selecting a different HTML-escaping API. The conservative schema,
budget, duplicate-key, surrogate and unsupported-null semantics remain. No
concrete source blocker was found in the port; no new dependency or test mock
was introduced to hide the failed first attempt.

The finite native bridge validates exact raw-corpus and pattern-corpus scopes,
source hash, case indexes, schema hashes, duplicate consistency and byte bounds
before native import. It uses the actual exported pattern map for corpus cases
and retains the original JSON sanity controls. Mask/error/acceptance/EOS checks
are unchanged. Its launcher credits only a strict linked nested report with
matching return code and known owned cleanup. Hash linkage alone cannot
authenticate arbitrary CLI pattern origin; the actual JVM test completion,
fresh export artifact and compiled-source capture supply that provenance.

The verified checks below grant no model or full milestone acceptance.
This reviewer has performed no native
import/build/SDK/device/model/download/cache/image/disk operation and owns no
implementation paths.

## Verified actual Kotlin-to-native bridge

Independently replayed the coordinator's second JVM attempt under
`C:/Users/Avery/LocalLore-finite-gson-host-20261025`: all48 XML files matched
their recorded sizes/hashes and summed to512 tests/0 failures/errors/skips.
The13 encoder tests and3 selector tests were present and passed. Process
metadata records completed0/cleanup true81,031ms; the retained stdout hash
matched. All seven pre-command source hashes matched current coordinator
files when reviewed, including Gson codec
`b89ba9aa332529a629e0f532f5d8e55997eef8f68229665f898eae53010af96f`
and worker
`db4d5f18318b7b5d67fbeb33bddee7781ddce7adc41477d9c17808e92c23df27`.

The actual Kotlin export is8,237B SHA256
`d2989fa17c242bf58e7ff902e3267b05d87401a0dbe6abc4de637c6f9a13918e`.
It contains13 schema-linked patterns for the37,029B original synthetic corpus,
SHA256 `aac94a0ca1de3222a4774dd0a404b44f867d9712e6919c1a4ece553fdc7fc1a2`.
The copies consumed by the subsequent native run were byte-identical to both
JVM-side files. Source-corpus hashes, all13 case indexes/schema hashes and all
215 sample hashes, byte lengths and outcomes independently matched.

`C:/Users/Avery/LocalLore-finite-native-20261025` records a completed0 native
host check with known cleanup in703ms. All119 positives and96 negatives passed,
including the original full escaped text and wrong-truncated examples; all
five original sanity controls were true. The35,809B nested oracle report has
SHA256 `02708b00f2da25a0a17068ae6f8170b14109fe3dcb15f3050a0a8d702e9619a5`.
Its three recorded checker/launcher source hashes matched current files.
This uses actual Kotlin-produced patterns, not a Python encoder approximation.
It proves the admitted host byte corpus for this corrected finite encoding;
it does not erase the original vendor-path mismatch or qualify SDK/model use.

## Current replay and Android artifacts

The current-source literal replay in
`C:/Users/Avery/LocalLore-literal-current-20261025` completed0 with known cleanup
in484ms. Its3,656B probe report SHA256 is
`860ed9c31989b2cee52497e9ff0ea6cb57fb171d0b781edb1cddb7a2576b3f36`;
all three recorded source hashes matched current files. It retains73 reduction
evaluations and the same single-deletion-minimal index set. Default JSON,
Lark-default and Lark-no-forcing all reject the full original/reduced values
and accept their incorrectly truncated prefixes. Exact serialized-output regex
accepts the full values and rejects those prefixes. Thus the finding includes
changed accepted content, not just exclusion of an alternate representation.
Current public `literal` observation exits0; the earlier outer-CLI exit concern
is resolved. `observed` still does not mean a generation qualification pass.

The regular SDK JVM results independently sum to454 tests/43 suites with
0 failures/errors/skips; all43 XML sizes/hashes match their index. Its process
completed0/cleanup true in74,328ms. Receipt and regular assembly completed0/
cleanup true in69,797/55,734ms; lint tasks likewise completed0/cleanup true in
80,985/58,203ms. Every retained stdout hash matched its process record.

Independently hashed the four copied artifacts under
`C:/Users/Avery/LocalLore-finite-artifacts-20261025`:

| Profile / artifact | Bytes | SHA256 |
| --- | ---: | --- |
| Receipt APP | 75,041,504 | `83797af66672e5bab89e17d53339478eb7c57bee66773c9c72edd13466911a8a` |
| Receipt TEST | 2,056,615 | `e5d09b0f436237b51c647b4cc43a74e8f76b08bfdfe045907aa89ee6724f359d` |
| Regular SDK APP | 74,975,720 | `9ba3e59b2f8d3ed8ae71b3c7601d47c1039b194b9850c443541b4d2118bf5357` |
| Regular SDK TEST | 1,869,719 | `8c14c03502faee7661b58a6862c5b35e9fec6e6371e40b9c2718daadd56ad1e5` |

All match the2,532B manifest SHA256
`86a61b33aa591e6fb689b879ee9f01cc65304ff43657854f36060f4969698db5`.
All six native-library ZIP entries independently match that manifest and
each other across the two APP profiles. This is static packaged-byte equality,
not execution of either ABI. The codec class is present and its JVM-test class
absent in both APP dex sets. Copied lint XML hashes match: receipt0 errors/
0 fatals/19 warnings; regular0 errors/0 fatals/9 warnings.

Receipt APP audit and its paired signature check completed0/cleanup true in
1,047/672ms; regular audit/signature check in1,046/672ms. Both audit reports
state passed, and all associated stdout hashes matched. These are existing
profile/package checks, not release-signing or phone qualification.

Functional source is `05527059`; subsequent reviewed documentation does not
change that code. Receipt pins were updated at
`3efe84dfeb22aa7a314a7a3ce91a35a2106df0a3` to the exact audited pair above.
No source blocker remains in the reviewed finite codec, selector, probe or
packaging composition.

The subsequently supplied closed checks in
`C:/Users/Avery/LocalLore-literal-checks-20261025` independently replay as
361 Rust tests passed/0 failed/4 historical ignores across50 suite results,
completed0/cleanup true in71,047ms. The retained Rust stdout is37,526B SHA256
`c80c1dfb6e1ea3df55a2f0e878cc0c42891b62b1bfb6620de883b828eadd0fb6`.
Clippy completed0/cleanup true in8,563ms. Full Python reports866 tests passed
in68.609s, completed0/cleanup true in69,422ms; its101,680B stdout matches the
recorded SHA256
`2926c68e3418f613a239597d3a99b087ce5392fe0994b2b11374b854850aa61c`.
These are retained coordinator executions; this reviewer did not run them.

## Remaining gate

Fresh SDK/model execution is still pending separate exact artifact/source,
resource, owner and copy admission. Storage planning or cleanup authorization
is not such a grant. No new ordinary scene, model output, cancellation/restart,
physical-phone result or cause of prior Android INTERNAL13 is established by
this host/APK review. The original schema and engine literal/intent/commit
authority, all budgets and ownership fences remain required. Full M05/M01
criteria stay open; integration and any later runtime qualification remain
with the coordinator.

# Original AUTHOR diagnostic sidecar v1

Refs #13 (M09.02/M09.06), #5 (M01.03 support), #14 (M10.02/M10.03 support).
This adds evidence to the [real AUTHOR experiment](REAL_ORIGINAL_AUTHOR_MODEL_PROTOCOL_V1.md).
It does not repair a proposal, change acceptance, authorize creation or qualify
an SDK/device. The original failed run and v1 proof reader remain unchanged.

## Response observation

`LocalInferenceOwner.installAuthorResponseCapture()` is explicit, one-shot and
available only before transport/port attachment on an admitted fresh owner.
Ordinary application owners install nothing. The collector has no callback,
file operation, log, model path, prompt or gameplay capability. It retains one
exact UTF-8 AUTHOR response of at most8192 bytes and defensive-copy snapshots;
it never truncates output into an apparently exact response. Calls saturate
at2; states are `empty`, `recorded`, `duplicate`, `invalid`.

The owner records only after existing role-release/current-ticket checks and a
true native response ACK for that exact ticket, with the current owner/run
still admitted. The ACK denotes bridge submission, not semantic validation or
canonical acceptance. A false/stale ACK records nothing. An observation may
precede a later failure/cancellation; retaining it cannot override that outcome.
Capture has no authority over response bytes, cancellation, cleanup or retries.
The SDK worker, its hash/profile, model, prompt/schema and budgets are unchanged.

## Synthetic instrumentation files

Only the selected original experiment method installs capture, before creating
its transport. Its input must equal the fixed original Eira/Tavi weather-note
fixture. Use a fresh sibling `no_backup/original-author-diagnostic-v1` directory;
do not borrow a story or existing diagnostic namespace. All files are private,
create-only, regular and owned by the app. No raw response goes to test status,
ordinary logs, public Git, an issue or a hosted service.

The closed file roster is:

```text
input-v1.json
response-v1.bin
generated-v1.json
workspace-before-v1.json
workspace-after-v1.json
diagnostic-v1.json
```

Input/raw-response limits are4096/8192 bytes; the other three payloads are at
most262144 bytes each, with a1MiB aggregate. The manifest is at most32768 bytes.
Input, returned native envelope and before-workspace bytes match the existing
v1 proof artifacts exactly. After-workspace is one passive native query after
generation returns with known ownership, before review/create. On a known
semantic refusal it still runs; on uncertain ownership it does not. Before and
after must describe the same empty native library. No Kotlin reducer is added.

The manifest has exactly:

```text
version, scope, status, reason, feature_acceptance,
input_sha256, author_proof_sha256, capture, files
```

Version is integer1, scope is `original_author_diagnostic_v1`, and
`feature_acceptance` is always false. `status` is `completed` only for complete
diagnostic evidence, with null reason; it does not mean the author workflow
passed. A refusal uses a fixed `checks_failed` or `resource_uncertain` reason.
Unobserved bindings are null, never invented zero measurements.

`capture` has exactly `state`, `calls`, `response`; a completed diagnostic
requires `recorded`, integer1 and a full `{bytes,sha256}` response binding.
If installation was never observed, state/calls are null; an observed empty
collector instead reports `empty`/integer0.
`files` has the five payload names above, each a `{bytes,sha256}` binding or
null when unobserved. The response binding must be identical in both places.
`author_proof_sha256` binds the original v1 author proof written at completion;
its profile and four traces retain their existing schemas and limits.

A complete sidecar requires one closed actual AUTHOR trace, matching response
byte count, exact fixed input and proof/artifact bindings, and equal empty
before/after workspaces. A rejected native envelope remains rejected. The
strict v1 full-roundtrip validator must still pass separately before a host
claims generation/review/create/reopen qualification. Missing/uncertain
sidecars are preserved as failures, never completed by editing old artifacts.

## Offline native diagnosis

`validate_proposal_detailed` is the single native proposal validator.
`validate_proposal` projects its existing legacy error strings. Fixed, data-free
reason codes add no new accepted proposals and contain no private text/paths.
The offline `original_author_diagnostic` Rust example reads exactly two trusted
caller-selected regular files, bounded4096/8192 bytes, strict unique-key JSON
and existing typed contracts. It cannot open a gameplay database or invoke
inference. It never emits input/proposal prose.

Its report has exactly nine fields: `version`, `scope`, `input_sha256`,
`response_sha256`, `input_bytes`, `response_bytes`, `status`, `category`, `error`.
Version is integer1; scope is `original_author_native_diagnostic_v1`. Status is
`valid`, `rejected` or `malformed`. Valid has null category/error and means only
that the native proposal validator passed. Rejected has a fixed native reason
and its unchanged legacy error. Malformed has a fixed read/JSON/bounds reason.
Counts/hashes are null only when a complete bounded regular read was impossible;
never hash a truncated prefix as the full response.

The pure Python `validate_diagnostic(raw, files, author_raw, author_artifacts,
prior_import_raw)` binds the sidecar and existing proof/traces without engine
decisions. `validate_native_report(report_raw, raw, files, author_raw,
author_artifacts, prior_import_raw)` additionally binds the native report's full
hashes/counts and its outcome to the original returned native envelope. Neither
function reads files, invokes a model/native engine or repairs model output.
Host source/APK/target/owner/JUnit/CLI provenance remains independently required.

The three host readers additionally accept keyword-only
`expected_prompt_version`, with the strict legacy default `initial-world-v1`.
The caller may explicitly select `initial-world-v1.1` for the player/NPC prompt
revision. A completed proof's canonical origin must match that exact selection;
the reader never chooses a cohort from archive data. Unknown or non-string
selectors refuse. Schema and proof versions remain unchanged. A generation
refusal contains no committed origin, so accepting its diagnostic bindings does
not establish the prompt revision: source/APK and runtime admission must bind it.
Existing recorded v1 proofs retain their original default-reader result.

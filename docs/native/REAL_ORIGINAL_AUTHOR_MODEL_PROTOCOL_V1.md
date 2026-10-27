# Real original-author model probe v1

Refs #13 (M09.02/M09.06), #5 (M01.03), #14 (M10.02/M10.03 support).
This is an experiment protocol, not a supported-device or release decision.
It extends the already qualified native author interface in ADR-0013 without
changing production authority, generation budgets, dependencies or model pins.

The [2026-10-27 execution report](REAL_ORIGINAL_AUTHOR_MODEL_VERIFICATION_2026-10-27.md)
records the first host-parser refusal, focused checks and preservation. Model
transfer, import and real author inference remain unqualified in that attempt.

## Scope and admission

Two individually selected methods in `OriginalAuthorModelInstrumentedTest` run
in the existing debug LiteRT verification application,
`org.locallore.app.litertverify`. Other verification profiles refuse. The host
must establish an absent package pair on a freshly admitted target before
installation; no replace install, clear, uninstall, default target or silent
reconnection is part of this protocol. The phone's existing identity/USB and
physical admission gates still apply. An owned emulator is labeled separately.
All target commands bind its exact transport, APK hashes, current source map,
existing server and known client ownership. No server lifecycle operation or
unrelated emulator control is allowed.

The LiteRT candidate must package the existing `model-provisioning` native
feature even when the separate setup profile is not selected. The candidate
APK audit requires its defined public `NativeModelPublication.publishNoReplace`
JNI export in both packaged ABIs. A successful compile or an embedded symbol
name does not establish that the import function is callable. The execution
report retains the original missing-export failure and the corrected build;
device import and inference still require their own actual checks.

The model remains CandidateLocalModel's exact 2,588,147,712-byte Gemma container,
SHA256 `181938105e0eefd105961417e8da75903eacda102c4fce9ce90f50b97139a63c`.
The SDK remains LiteRT-LM 0.18.1; the existing runtime, worker, manifest and
bundled-template identities are retained. A verified local file may be copied
only into the new app's fixed private source. No model download or upload is
requested. Full source/accepted copies and the SDK cache remain preserved.

Before staging, require space for both model copies plus the existing 2 GiB
shared reserve on one internal filesystem. After staging, require the missing
accepted copy plus that reserve. Immediately before import and model loading,
sample non-low-memory state and at least 4 GiB available memory; this is an
experiment margin, not a universal Android minimum or allocation guarantee.
Paths must resolve under the actual target Context, with regular non-symlink
model files owned by its UID. Source/accepted/proof namespaces are never
borrowed from another app or an existing story.

## Import phase

Select only `importsTheVerifiedOriginalAuthorModelOnce`.

Before streaming weights, the host checks its binary transfer path using the
existing 65-byte `benchmarks/fixtures/physical_model_probe_v1.txt` fixture,
SHA256 `72e34de83e7311b37f7a17361f3d71555209ffbfe4eb9e861cc11c7903e13422`.
Its new private destination is
`no_backup/original-author-transfer-probe-v1.bin`, outside the model-source
directory. Preserve it. Binary file handles bypass shell text pipelines;
neither a host process exit0 nor raw exec-in implies remote exit status or
successful delivery. Independently verify the destination's exact count/hash
before weights, then verify the complete model destination after streaming.

The staged source is
`no_backup/original-author-source-v1/model.litertlm`; that directory contains
only that leaf. `no_backup/local-model-v1` and the new proof directory must be
absent before import. The only publication path is the production
`CandidateLocalModel.store(context).import(...)`, with an observed IO stream.
Record its actual one open, one close and exact byte count. Production
`installed()` then performs its full integrity recheck. Do not fabricate the
accepted layout, skip publication or substitute a synthetic stream.

Write create-only
`no_backup/original-author-import-proof-v1/import-v1.json` with exactly:

```text
version, scope, status, stage, reason, process, package,
model, source_counts, accepted, elapsed_ms
```

Version is integer1; scope is `original_author_model_import_v1`. Process has
exactly `pid`, `uid`, `start_elapsed_ms`; model and non-null accepted identity
have exactly `bytes`, `sha256`. Source counts have exactly `opened`, `closed`,
`bytes`, `off_main`. Absent observations are null rather than invented zeros.
Success requires actual publication, accepted full-hash identity, observed
source closure and no source/model deletion. The import phase invokes no SDK.
After its known completed proof/client closure, the host may stop only this
owned verification app to obtain a distinct author-phase process.

## Author phase

Select only `recordsOneRealAuthorCreationAndInferenceFreeReopen` in a new
process with the same app UID. The exact prior import proof and installed model
are rechecked. `no_backup/original-author-proof-v1` must be absent. No player
content, model-derived path, arbitrary Seed or raw SQL enters the harness.

Use one original small island/lantern/weather-note premise, player Eira and
cast hint Tavi, with the existing narrative profile and plain presentation.
The fixture is inline trusted test data. No exact generated prose or golden
proposal is required. Rust remains responsible for model-output validation.

The existing production `CandidateLocalModel.config(files).createOwner(...)`
factory uses real default SDK resources with all four existing independent
traces attached. `NativeWorkspaceTransport` receives that owner and an isolated
test-workspace Context. This is factory/JNI integration, not a MainActivity or
Compose journey. Do not inject fake resources, replace responses, add repair,
sort provenance or relax validation to obtain a pass.

Execute native begin, one generate, review of the unchanged valid proposal, and
explicit create with one fixed 32-hex creation ID. Begin/generate/review must
leave the library unchanged. AUTHOR keeps its separate native budget of 1,024
tokens, 8,192 output bytes and 120,000 ms. Persisted model configuration remains
the existing play profile (60,000 ms, director350/narrator220), not the author
budget. Exactly one AUTHOR request and a JSON_OBJECT SDK argument are required;
callback/output and worker close observations must agree. Invalid generation
is a failed probe with no creation, never an excuse to edit its outcome.

Inspect exact persisted provenance using the existing native archive export.
It must retain original response/hash/proposal/input, local-provider metadata,
prompt/schema versions, unchanged reviewed input/proposal and fixed title.
After known handle invalidation and observed SDK closure, reopen through a
fresh passive `NativeWorkspace.openLocal(profile)` with no SDK owner attached.
Retry the same creation ID/job/review: it must recover the same story at
revision0 with `created:false`, unchanged snapshot and no inference. Plain
`NativeWorkspace.open` is unsuitable because it configures a scripted fixture.
Do not allocate a second Candidate owner just to test reopening.

Write create-only `no_backup/original-author-proof-v1/proof-v1.json` with exactly:

```text
version, scope, status, stage, reason, process, package,
prior_import_sha256, profile, job, input_sha256, review_sha256,
creation_id, records, traces, elapsed_ms
```

Scope is `original_author_model_v1`. `profile` is the exact existing profile
object. Nullable fields remain null until observed. `records` has exactly these
logical filenames, with null or a closed `{bytes,sha256}` binding for each:

```text
input-v1.json
begin-v1.json
generated-v1.json
review-v1.json
create-v1.json
retry-v1.json
workspace-before-v1.json
workspace-generated-v1.json
workspace-reviewed-v1.json
workspace-created-v1.json
snapshot-created-v1.json
snapshot-reopened-v1.json
archive-v1.json
```

`traces` similarly binds `worker-v2.json`, `send-v2.json`, `callback-v1.json`
and `status-v1.json`, using the existing trace serializers. All files remain
private. Maximum artifact size is 1 MiB, maximum collected artifact bytes are
2 MiB; model/cache files are never proof artifacts. NativeWorkspaceTransport
already returns parsed JSON objects: its envelope artifacts are immediate test
serializations of those returned objects, not byte-identical JNI wire captures.
The existing native archive is captured byte-for-byte before test parsing; its
generation.response and response hash retain the exact original SDK text.
The host captures the actual artifact bytes before parsing. Strict proof JSON
rejects duplicate keys, nonfinite numbers and extra proof fields. A missing
artifact is not a zero-valued observation. No production byte-capture hook is
added merely to make the harness's envelope serialization look like raw JNI.

Both proofs use status `completed` or `refused`, stage from the fixed set
`precheck`, `source`, `import`, `installed`, `native_open`, `begin`, `generate`,
`review`, `create`, `reopen`, `archive`, `completed`, and reason null on success
or fixed `checks_failed`/`resource_uncertain` on failure. No exception, file
path, generated prose or private diagnostic becomes a public failure message.

## Evidence and limits

The pure read-only transfer recipe/decoder lives in
`benchmarks/original_author_stream_admission.py`; its 14 original adversaries
live in `scripts/tests/test_original_author_stream_admission.py`. One measured
batch binds both expected package UIDs, safe distinct installed paths, exact
APK hashes, API35/x86_64/qemu/user0 and resource facts. It rejects malformed
frames, duplicate/extra fields, bare CR and oversized numeric strings before
integer conversion. Batching does not change the resource floors or owner
budgets. The held binary source and complete destination still need independent
byte-count/hash verification. Pure tests do not qualify a device or model.

A rejected generation remains failed even when SDK completion is observed.
The current refused proof retains the native envelope and bounded traces, but
not the original rejected model text or a granular semantic-validation code.
Do not infer the precise rejected rule or post-failure workspace conservation
from missing artifacts. A later diagnostic experiment must preserve original
output without changing validation or replacing the rejected outcome.

Host proof validation is pure bounded metadata/provenance validation, not a
second engine. Meaningful negative tests must reject changed bindings, missing
observations, forged success, extra fields, scripted-provider substitution,
duplicate/extra AUTHOR calls, wrong budgets, incomplete output, unknown owner
closure, changed canonical snapshots or altered original provenance. Trace
observations are not hardware callback-drain authority by themselves.
Existing Python play-trace readers intentionally accept only DIRECTOR/NARRATOR
and the old 350-token cap. This proof uses a separate strict AUTHOR-only reader
for the already implemented Kotlin AUTHOR snapshots and 1,024-token budget;
it does not widen those legacy readers or reinterpret historical results.

An actual run additionally requires exact JUnit start/pass records, closed host
client/owner receipts, raw bindings, fresh target/source/APK/model admission and
retained original proof files. A fabricated passing proof or unit test cannot
qualify the SDK. On uncertainty, preserve all artifacts and quarantined owners;
do not issue dependent app controls, repeat generation or claim cleanup.

One successful run would establish this bounded factory/JNI/model roundtrip in
its stated environment. It would not establish a supported phone, narrative
quality, sustained performance, physical ARM64 execution from an emulator,
joined native callback drain, cancellation latency or full milestone acceptance.

## Existing dependency identities checked for this experiment

Read-only checks on 2026-10-27 confirm the existing pins; no dependency, backend
or model upgrade is proposed. The [LiteRT-LM 0.18.1 release](https://github.com/google-ai-edge/LiteRT-LM/releases/tag/v0.18.1)
identifies runtime commit `bda624851d74be34d4e1f7fac1fc4155939539c7`.
Its [Google Maven POM](https://dl.google.com/dl/android/maven2/com/google/ai/edge/litertlm/litertlm-android/0.18.1/litertlm-android-0.18.1.pom)
declares the Android AAR and Apache 2.0 license. The pinned
[ResponseFormat API](https://github.com/google-ai-edge/LiteRT-LM/blob/bda624851d74be34d4e1f7fac1fc4155939539c7/kotlin/java/com/google/ai/edge/litertlm/ResponseFormat.kt)
supports the public JSON_OBJECT/schema route used by production.

The [exact model revision metadata](https://huggingface.co/api/models/litert-community/gemma-4-E2B-it-litert-lm/revision/a790a852d433991c0c0a41c1154cf9b3850300fa?blobs=true)
matches the existing container path, byte count and LFS SHA256 above. Its
[immutable publisher card](https://huggingface.co/litert-community/gemma-4-E2B-it-litert-lm/raw/a790a852d433991c0c0a41c1154cf9b3850300fa/README.md)
documents LiteRT-LM Android/CPU use; Google's
[Gemma 4 model card](https://ai.google.dev/gemma/docs/core/model_card_4) identifies
Apache 2.0 licensing. This is the existing CPU artifact, not a Qualcomm/NPU
artifact. Source support and verified local weight bytes do not establish a
successful author run, device performance or supported-hardware decision.

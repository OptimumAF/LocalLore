# Explicit cache SDK controller, 2026-10-23

Refs [#5](https://github.com/OptimumAF/LocalLore/issues/5) (M01.03/M01.05), claim
`6371399958`. This host-only packet implements a controller, not a measured
inference run or a production runtime decision. Model provisioning and actual
device execution belong to separately admitted coordinator work.

`benchmarks/android_cache_control.py` exposes:

```python
run_control(device, apk_sha, case, expected_uuid, measure, model_identity, raw_sink=None)
```

The artifact pin is explicit: cacheprobe APK SHA256
`04eef96b7177aaef275574f9ee45d25efa9b181bab4fcb0a363d8077a4e4fb7d`,
63,598,424 bytes, Java source `a033d08`. This separately qualified artifact adds
app-domain `verify_model`; the older `50e6e60c...` artifact cannot substitute
for it. Artifact qualification is described in
[the model-verification report](CACHE_MODEL_VERIFY_HARNESS_2026-10-23.md).
Fresh device/storage admission and actual app-domain model verification remain
prerequisites to an SDK control experiment.

## Caller contract

The caller supplies a specifically targeted `TrackedDevice`, fresh trusted
`measure()` callback, trusted zero-argument `model_identity()` callback, and an
optional host-only private raw sink. The callbacks must use the **same** tracked
device, or update its sticky `clients_cleaned` field for every transport call.
They must be bounded, journal original diagnostics privately, and perform no
hidden inference, provisioning or deletion. A static sample JSON cannot prove
freshness, backing identity, model integrity or permission to run.

`measure()` returns the existing strict `android_cache_volume` sample. Its
independent guest/host reserves, shared-host grouping, expected UUID and
post-consumption policy are unchanged. The controller places its complete
lifecycle—including its initial package stop—inside `run_with_admission`.
Pre-refusal performs no controller package/device calls.

`model_identity()` returns exactly `verified`, `volume_uuid`, `sha256`, `bytes`,
and `diagnostic`. The fixed diagnostics are `verified`, `absent`, `mismatch`,
`unstable`, `incomplete`, `not_regular`, `wrong_volume`, `invalid_receipt`, and
`read_failed`. A verified result additionally requires the expected volume,
SHA256 `181938105e0eefd105961417e8da75903eacda102c4fce9ce90f50b97139a63c`
and 2,588,147,712 bytes. The controller never reads or provisions the model itself.
The original safe diagnostic remains separate from cleanup failure information.

An approved driver uses this explicit recipe after supplying real evidence
adapters; the names below are required caller implementations, not fake proofs:

```python
import sys
sys.path.insert(0, "benchmarks")
from android_cache_control import APK_SHA256, TrackedDevice, run_control

device = TrackedDevice(authorized_adb_path, authorized_serial)
report = run_control(
    device, APK_SHA256, "gift", verified_framework_uuid,
    measure=lambda: collect_fresh_admitted_sample(device),
    model_identity=lambda: verify_selected_app_model(device),
    raw_sink=retain_create_new_private_protocol,
)
```

The caller retains a started/unfinished attempt before invoking this function,
binds the actual APK and evidence files, serializes only the returned safe
metadata, and fences later work when any ownership/admission/check flag fails.
There is deliberately no convenience CLI accepting a purported model-verification
JSON or copying weights. Supplying these callbacks is not authorization.

## Lifecycle and evidence

Only `org.locallore.runtimebench.litert.cacheprobe` is addressed. A single
installed `pm path` and exact APK hash are checked before stopping; a running
process must have one valid PID, the exact package command and a valid start
time. Absence requires the explicit `pidof` exit-1/empty-output protocol.
Unknown/multiple process identities are not absence. No arbitrary PID is signaled.

Exactly one instrumentation request uses `CacheProbeInstrumentation`,
`operation=play`, the expected UUID, a fresh 32-hex session, fixed case and
unchanged `make_profile` contract. The SDK/Rust budget stays 60 seconds with
350/220 role tokens; the host request deadline is 110 seconds and the existing
APK watchdog is 90 seconds. There is no automatic inference retry.

After successful app-domain model verification, a further verified stop checks
the current APK hash and single-process identity and proves absence before SDK
play. This handles a verification instrumentation process left alive and rejects
an APK changed during the trusted callback. It addresses only the new package.

The required coordinator parser is `android_cache_result.parse_result(raw,
case, expected_uuid)`. Production imports have no missing-parser fallback.
Raw bytes are offered to the private sink before decoding. Strict accepted
results remain in `result` even if the SDK later reports `volume_changed`, raw
retention fails, transport ownership becomes uncertain, final stop fails, or
the host storage post-check refuses. `worker_status`, `worker_error`,
`failure_stage`, `cleanup_failure_stage`, and admission information stay separate.
No such failure is converted into a claim that canon remained unchanged.

Each ADB result must prove client cleanup before another device call. After
unknown cleanup, there is no final stop, reopen, model check, or post-measurement.
When cleanup is known, the final stop re-verifies the new package/hash and actual
single-process identity before stopping and proving absence. All cache sessions
and SQLite files are retained, including on malformed/failed output. The module
never calls legacy `SdkWorker`, stops the legacy package, or removes a workspace.

`check_passed` requires the expected per-case outcome, strict SDK evidence,
outer/sample validity, client cleanup, package absence, and pre/post admission.
The policy's `dispatched` field means the operation callback was entered; it is
not proof that model execution started. `phone_qualified` remains false.

## Verification and limits

The author ran 26 independent controller tests against fake transports and a
parser mock: exact request/profile, pre-refusal, stale volume, package
and process identity failures, one launch, callback/client uncertainty, raw
retention ordering, malformed output, and accepted-result preservation across
SDK/cleanup/post-storage failures, verification-process stop, late APK changes,
unknown pre-play cleanup, and profile-failure attribution. The earlier
controller/parser/admission selection passed 61 tests; the final pin passed
67 tests using the coordinator's current real parser (26 controller, 16 parser,
25 admission). The
controller tests still intentionally mock parser responses to isolate lifecycle
behavior. No ADB, model read/copy, inference, device or GitHub mutation was
performed by the author. The separately authorized Java-only artifact
qualification performed no SDK/model execution.

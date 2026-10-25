# Closed worker-stage observation verification — 2026-10-25

Refs #9 (M05.05 real-backend prerequisite); #5 (M01.05 supporting).
Source freeze: `ea924a2c2cd7db78e342062225e0aaff52ff7b05`, based on main
`0c12413ed0d236e5b74e8626e434b0f074c3cdfc`. PR153 was merged outside this
execution. This packet makes no merge, release or access change.

## Implemented slice

The [previous actual PLAY](RECEIPT_REAL_EXECUTION_VERIFICATION_2026-10-24.md)
failed `LocalInferenceUncertain` after successful full receipt import, without
identifying its lower worker stage. Add an optional final in-memory trace to
the same default worker/owner and candidate transport. It records thirty fixed
bounded counters, never prompts, model responses, paths or exceptions. There
is no injected observer callback, replacement SDK resource or provider output.
The [wire contract](LITERT_WORKER_TRACE_CONTRACT.md) defines exact meanings.

The existing PLAY fixture attempts one failure-only status1337 record when
`respondText` throws or the unchanged Prepared assertion fails. Snapshot/send
failure preserves the identical original throwable; success emits nothing.
The snapshot precedes existing catch/finally teardown and invokes no additional
SDK, model-file or transport operation. The strict host decoder retains the
observation before the original runner/proof gate. It cannot qualify a failed,
skipped or malformed runner, authorize retry or permit REOPEN.

Entered points mark reached pre-call sites, not native acknowledgments.
Callback counts/fencing precede observation; uncertainty notification follows
the original synchronous owner-fencing hook. `DRAIN_SETTLED` and close-known
counts are historical conditions, not caller delivery, current ownership or
independent JNI reclamation. Zero uncertainty is never a health certificate.

All storage guards, ownership/quarantine, 60s turn/5s total cleanup, role/token
budgets, cancellation and canonical commit boundaries remain unchanged. No Rust
or gameplay authority, runtime/model version, dependency or permission changes.
The exact LF-normalized worker provenance advances to
`aaf476a9ad3928c0a21168c0949776abbcf876bcbb20180ba4da82eae067db29`, paired in
the build guard, candidate constant and manifest. The runtime remains LiteRT-LM
0.18.1 / `bda624851d74be34d4e1f7fac1fc4155939539c7`; the same Gemma4-E2B
model revision/digest/2,588,147,712-byte identity remains unchanged.

## Commands actually run

Windows, existing Android SDK/NDK29.0.14206865 and cached toolchains only.
The checked-in wrapper was invoked through Android Studio's existing JBR;
Java21 was explicitly available to the pinned build-only lint analyzer.
No dependency/toolchain download or device call was made.

Receipt and regular candidate builds both ran these tasks:

```text
:app:assembleDebug :app:assembleDebugAndroidTest
:app:cleanTestDebugUnitTest :app:testDebugUnitTest :app:lintDebug
:app:auditLiteRtDependencies :app:auditLintAnalyzer
--offline --no-daemon --console=plain --max-workers=2
-Pandroid.builder.sdkDownload=false -Pkotlin.incremental=false
-Pandroid.experimental.lint.version=9.4.1
-Porg.gradle.java.installations.auto-download=false
-Porg.gradle.java.installations.paths=C:/Program Files/Java/jdk-21
-PlocalLoreLiteRtVerification=true -PlocalLoreModelSetupVerification=true
--project-cache-dir .gradle-litert-worker
```

Receipt adds `-PlocalLoreModelVolumeVerification=true` and
`-PlocalLoreModelReceiptVerification=true`. Regular omits those two flags.
Each build used its own create-only evidence directory and a bounded900s
Windows Job/barrier helper; profile builds were serialized.

| Actual original handle | Result and retained evidence |
| --- | --- |
| Initial receipt16973 | terminal0; owned completed0/known cleanup320,094ms; 384 JVM/38 suites, zero failures/errors/skips; lint0 errors/19 warnings |
| Corrected receipt39203 | terminal0; owned completed0/known90,750ms; **385 JVM/38 suites**, zero failures/errors/skips; lint0/19; dependency/analyzer audits pass |
| Regular12919 | terminal0; owned completed0/known252,219ms; **361 JVM/36 suites**, zero failures/errors/skips; lint0/9; dependency/analyzer audits pass |
| Initial host8819 | terminal0; owned completed0/known71,766ms; **683 PASS**, unittest69.818s |
| Final host26311 | terminal0; owned completed0/known67,563ms; **683 PASS**, unittest66.812s with final APK pins |

Both host runs used `python -B -E -m unittest discover -s scripts/tests -v`.
The earlier integrated targeted command
`python -B -E -m unittest scripts.tests.test_litert_worker_trace scripts.tests.test_receipt_real_candidate -v`
passed30 tests/1.507s. Independent parser author ran12 targeted tests; pure
trace author supplied11 JVM tests executed centrally above. These are synthetic
host/resource seams, not real SDK generation.

Independent source review found and corrected callback-accounting placement,
historical drain wording and uncertainty-notification coverage before the
first build. After that passing384 build, review strengthened the reporter
privacy oracle: assert captured JSON outside the deliberately swallowed send
callback. Add direct engine-close-false coverage and place the unchanged
Prepared assertion inside the failure reporter. The corrected385 build and
regular361 build include these changes. Initial XML/output remains retained.

Other original cases cover blocked admission/construction/initialization/send,
terminal signaling while a callback body is active, failed close, cancellation,
late initialization after quarantine, immutable snapshots, saturation, races,
private-canary/schema refusal, malformed/multiple/cross-channel status records,
no successful emission and persistence failure stopping later actions.

## Artifact and source checks

| Final receipt artifact | Bytes | SHA-256 |
| --- | ---: | --- |
| APP |74,987,568|`fea69522642c5562134eab602cce55d006632fa451b40e55a247ce6a649c6140`|
| TEST |2,867,979|`7a8a32bedc574b4b3d57e476be54518d05dc641d6952c01ac8f70def2a326eb9`|

`receipt_setup_qualification.py` pins that exact pair. Final regular APP is
74,938,200B / `c05633f8c060287d00849572ff1f200ce203e5577ff02c8ba6ad2fda51f9024d`.
Both APP profiles pass `scripts/audit_apk.py` with their explicit profile flags,
including manifest/capability/launcher/service/ABI/ELF/alignment checks.
Receipt APP/TEST signatures pass the existing35.0.0 `apksigner.jar verify --verbose`.
Audit/signature children complete0 with known cleanup:922/829/375/313ms.

Two harness mistakes are retained: an unsupported `cwd` argument failed before
dispatch; then an audit child completed1/known734ms because its SDK environment
was missing. Supplying the existing explicit SDK environment produced the
successful audits above, with no artifact change or check suppression.

The206-row tracked Android source index at the freeze was rehashed after both
builds with zero mismatches. Private outputs, copied XML/APKs, bounded raw logs,
helper errors and metadata stay outside Git. Raw output SHA-256 values:

| Observation | SHA-256 |
| --- | --- |
| Initial receipt10,678B |`fa17215b833affc35da90e55c92a13dc48a2f17fb179d7f41ec39a4c793635af`|
| Final receipt9,644B |`2431fb4894b7fab3ccd3149185201f001dc842d2e705983ae70aa4d6aa3b8fd3`|
| Regular10,152B |`518caf65da8285c606f85a4519d93d0f0b7324e6a06c56edbcfd74d06e4dc88e`|
| Final host80,486B |`fb6761d19f57c2d57d9ac190b015f963d9a29f22e50c4a9618752a7d6b836a06`|

No new ordinary APK/build, physical phone, ARM64 or16KiB execution result is
claimed. Packaging and host tests do not establish those gates.

The final sealed private evidence index records177 files/154,244,091B;
index SHA-256 `10317ff800aec8cd78a24e05f05c454b09b71632f81afb638668f74951a80a3a`.
It includes both capacity observations and all retained harness errors, and
contains no model weights or virtual-disk contents. The sealed namespace is
read-only after that inventory.

## Fresh-run capacity and next task

No new emulator, model copy, SDK call, accepted gift or restart ran in this
packet. Human local-copy permission persists. The current helper requires a
fresh D: root; existing targets/copies and quarantined owners remain preserved.

At07:50:58Z after builds, D: free47,762,575,360B minus the unchanged40GiB
reserve42,949,672,960B leaves4,812,902,400B. Win32 file metadata independently
reported the prior exact SD image's logical and allocated size8,589,934,592B.
A same-shape new SD allocation alone is short3,777,032,192B before userdata,
source weights or cache. Earlier during-build capacity observation is retained
separately; its transient shortfall is not substituted for this later result.
No virtual-disk contents were read, reserve lowered, data moved/deleted or held
target adopted to get around that prerequisite.

This is a D-root hold, not a claim that every host storage choice is exhausted.
C: free316,256,886,784B supports preparing a separately reviewed explicit
create-only C-root profile. Its proposed C40GiB/D40GiB reserves preserve the
existing D reserve and strengthen C's; no automatic drive fallback is allowed.
That is a separate claimed implementation/verification packet, followed by
fresh source/artifact/owner admission and real PLAY/reopen. It is not part of
this observation change or an already qualified emulator.

Full M05.05/M01.05, reference-phone, supported-model/profile, quality/sustained,
DocumentsUI/cache/privacy/power-loss and existing integrity holds stay open.
Closed observations help investigate the next attempt; they do not make the
previous unknown SDK stage or missing accepted gift/restart retrospectively pass.

# Android experiment control and analyzer follow-up

Scope: M01.02/M01.05 preparation, [#5](https://github.com/OptimumAF/LocalLore/issues/5).
This follows accepted [#37](https://github.com/OptimumAF/LocalLore/pull/37), not a
production inference integration. The earlier
[all-attempt results](RESULTS_2026-10-22.json) and
[verification](VERIFICATION_2026-10-22.md) remain unchanged historical evidence.
In particular, the initial corrupt-file cleanup uncertainty and initial Rust
oracle startup failure remain unexplained. Deliberately injected faults and
successful later runs do not establish their causes or remove those attempts.

## Corrected control behavior

Native setup now reports fixed stages and distinguishes a worker never launched
from an ADB writer whose termination is unknown. Only known files in an exact
invocation-owned UUID directory can be removed after writers drain; a failed
directory admission never authorizes deletion. Thread construction/start,
launcher and cancel-marker failures return bounded results. Process reap,
ADB-client cleanup and file cleanup are separate facts; later failures revoke
earlier cleanup proof.

The SDK path verifies the installed APK, stops its exact package and proves
absence before request publication or instrumentation. It drains the local
launcher before the final package stop, preventing a late launch after an
absence check. Stop/absence failures and unknown launcher cleanup discard text
and SDK metrics. Private request/corrupt-fixture cleanup rechecks APK identity
and never deletes real weights. Cancel and deadline budgets include preparation.
Every oracle invocation now retains fixed failure/cleanup stages, including
failed setup. Public reports project only fixed enums, bounded numbers and
booleans; no stdout, exception text, story, path, transport ID or arbitrary metric
is copied into them.

The coordinator owns controller/probe integration and actual emulator operations.
Independent agents used separate branches/worktrees and exclusive files:
`review/m01-control` reproduced control defects and supplied nineteen adversarial
regressions; `research/m01-sdk-analyzer` owned isolated analyzer/build/audit files
and its evidence. Shared interfaces and integration stayed with the coordinator.
The reviewer found a further probe evidence gap: recovery was collapsed to a
boolean. Two new regressions first failed, then passed after retaining original
faults and separate recovery traces. Final read-only review at `93c7bee` ran all
52 Android Python cases and eight analyzer cases successfully. Review is finite
evidence, not owner acceptance.

The [analyzer report](LITERT_ANALYZER_2026-10-22.md) records official compatibility,
licenses, 67 actual analyzer JAR hashes, real SDK dependency analysis and
red/green checks. Only the isolated experiment uses the documented experimental
lint override. Production toolchains, runtime Java, manifest, JNI control v1,
native process parent and Rust oracle contracts are unchanged by this packet.
Current README commands replace the historical unconditional exit-2 guidance.

## Explicit device checks

Two selected existing emulators are Android15/API35/x86_64 with 4KiB pages.
Inventory has five emulators and zero physical phones; three targets were left
untouched. The source-built SDK APK was installed using explicit target selection
and `install -r -t`, preserving its verified private Gemma cache. All subsequent
package stops required that installed APK's exact SHA256. No model was downloaded
or transferred during this follow-up. The installed APK's payloads match the
earlier APK, but its full ZIP/signature hash differs; no reproducible-package
claim is made.

The initial explicit control probe passed nine assertions on each emulator:
three native setup faults, SDK clean-start/request/final-stop faults, and three
actual corrupt-file diagnostics. The six injected faults per target are
deliberate known-drained host failures around real operations, not spontaneous
device failures or successful generations. Each is followed by a fresh real
Rust fixture or SDK missing-file recovery. The final traced probe repeats these
checks after the review correction and retains detailed recovery diagnostics.
Both runs remain in the aggregate; retries never replace earlier evidence.

Separately, the actual LiteRT-LM0.18.1/Gemma E2B path ran gift, forced cancellation
after three seconds, then fresh gift on each emulator. All six requests and ten
attempted model roles are retained: four Rust-committed turns and two cancelled
director attempts. Each committed turn contains one event/revision, exact retry
unchanged, recipient observation present and absent observer excluded. Each
cancel returned verified process/client/request cleanup and no generated output;
the following two-role turn loaded fresh owners and committed. Forced process
termination is not cooperative SDK cancellation or a new callback-disposal proof.
Successful role reports also retain worker-off-Main, heartbeat and balanced
engine/conversation owner counts. Each role loads fresh owners; no warm reuse,
speed comparison or narrative-quality score follows. Both cohorts ran alongside
other host work, so timing values are observations only.

Exact local commands, with paths/transport selected by the operator:

```powershell
adb -s <authorized-target> install -r -t <frozen-source-built-sdk.apk>
python benchmarks/android_control_probe.py --adb <adb> --serial <authorized-target> --owner <built-native-owner> --oracle <built-rust-oracle> --apk <frozen-source-built-sdk.apk> --output target/control-probes.json
python benchmarks/android_runtime_spike.py --runtime litert --adb <adb> --serial <authorized-target> --owner <built-native-owner> --binary unused --oracle <built-rust-oracle> --apk <frozen-source-built-sdk.apk> --model <verified-local-gemma> --output target/control-gift.json
```

Repeat the last command with `--cancel-after 3`, then without it for fresh reload;
repeat the complete sequence on the second authorized target. Expected cancellation
CLI exit is 2, while committed turns and valid probe assertions exit 0. Public
aggregate results retain all attempts, cleanup stages and hashes; raw build/device
logs remain ignored. The binaries are unchanged source-pinned #37 artifacts; this
packet does not claim a fresh device oracle with the later storage replay changes.

## Final checks and remaining gates

Final executed counts, environment, artifact hashes and package/process cleanup
are recorded in [CONTROL_RESULTS_2026-10-22.json](CONTROL_RESULTS_2026-10-22.json).
The final checks actually executed are:

| Command/procedure | Result |
| --- | --- |
| `python scripts/check.py host --offline` | Exit0: 89 Rust tests, 148 Python tests, four fixture comparisons, three linker tests, format/Clippy |
| `python scripts/check.py android --offline` | Exit0: both native ABIs, 31 JVM tests, app/test APKs and manifest/ABI/ELF/ZIP audit; 23 tasks executed, 55 up-to-date |
| Production `lintDebug` | Zero errors; one unsuppressed `GradleDependency` advisory for coroutines1.10.2 versus cached1.11.0 metadata |
| Independent Android Python / analyzer audit suites | 52 / eight cases passed; reviewer used no ADB/model/device |
| Isolated SDK negative/clean positive analyzer builds | Expected negative helper exit2 despite Gradle0/39 metadata diagnostics; positive helper0, 14 JVM tests, zero lint errors/two advisories and actual dependency/classpath audit |
| Initial and final traced explicit probes on both emulators | 36 successful assertions across four nine-check runs; all attempts retained |
| Real SDK gift/cancel/fresh-gift sequence on both emulators | Four Rust-committed turns, two verified forced cancellations, ten attempted roles across six requests |
| Final APK-identity-checked stop, request cleanup and scoped process/run inventory | Both packages absent, request/corrupt files absent, no owned native processes or leftover run directories |

The final host and production Android gates run after integrating accepted main
`a4b762a`; this includes separately accepted ownership, desktop and storage work.
This packet edits no production application or storage source. Default checks
operate neither ADB nor real inference. Build-only SDK analysis remains separate
from installed production application checks.

M01.02/M01.05 remain partial/in review; all full M01 checkboxes stay unchecked.
M01.01 is blocked on an available authorized physical phone. No ARM64 execution,
API26/28/36 or 16KiB OS execution, memory/thermal/low-storage qualification,
original Qwen3.5 conversion, fair model ranking, warm shared-role session,
Compose-integrated real inference, accepted-turn persistence in this experiment,
hosted CI or release qualification is claimed. Summary/model output cannot
override Rust-accepted events. No production backend/profile selection, remote
gameplay fallback, PR merge, release, access/protection change or private upload
was performed. Next runnable runtime task is bounded warm role reuse using one
loaded model, with independent cancellation and full-turn accounting.

# Owned lifetime admission and measured SDK clients — 2026-10-26

Supporting M10.02/M09.06, draft PR #218 on draft/unmerged #216 at3761e462.
Executable source9ff29c6b; documentation-only7dd95191 does not change its779
tracked execution inputs. No full task or milestone acceptance follows.

## Change and original failure

The preceding retained-parent controller completed, but its host collection
started509.773 seconds after a1200-second owner began. Original retirement and
four canonical sidecars were never collected before expiry. That failed cohort
is retained unchanged; a raw controller pass cannot qualify it.

The [admission contract](ANDROID_OWNED_LIFETIME_ADMISSION.md) now requires the
existing1100-second SDK session budget to remain on the fixed owned deadline
after current ownership/source/profile checks, immediately before constructing
capture. Current client record2 retains measured elapsed/effective deadlines;
current proof2/probe2 and exact client-pair coverage stay mandatory. The1200-second
owner ceiling, per-client bounds, observation cadence, claim burning, canonical
helper requirements and output limits remain unchanged. No dependency or app,
Rust, SQLite, JNI, manifest or model change is introduced.

This is one-time admission, not a reservation or a worst-case completion promise.
Historical fully collected results remain valid in their original scope.

## Host and build execution

Windows/Python3.14.7/JDK21; existing offline Gradle8.11.1/AGP8.10.1 and SDK35
components. Original binary streams, source/tool/request bindings, owner outcomes
and all failed attempts stay private on C:, outside generated-build cleanup paths.

| Check actually run | Result | Private cohort |
|---|---|---|
| New8 tests on unchanged production, test-only60d1b047 | 5 assertion failures in0.039s; owner3022ms/worker1,779 stable inputs | `host-red-v1` |
| Corrected full host suite | 1335 pass in150.714s; owner155000ms/worker0,779 stable inputs, known cleanup/capture, stderr0 | `host-full-v1` |
| Versioned offline Android build | pass39080ms/worker0;259 executed JVM tests/30XML,0 failures/errors/skips; both lints0 errors/3 warnings;11 APK audits | `build-v1` |
| Existing server observation | pass, no server lifecycle operation | `server-v1` |
| Selected initial process observation | both original kernel identities unchanged; zero device/server calls | `selected-preflight-v1` |

The original RED dynamically reaches capture construction despite an insufficient
lease. The corrected constructor refuses before any capture/server/SDK call.
Exact1100 and greater remaining time retain the same constructor budget and
unchanged descriptor. Admission-time consumption and later sticky ownership
failure are covered. The new8 tests do not directly enumerate malformed clock
types or combine worker claim burning with lifetime refusal; older tests cover
claim burning/replay separately. Source review found no blocking production
defect and supplied this explicit coverage qualification, not owner acceptance.

Private host owners have fixed RED60/full300-second bounds. These test-runner
bounds do not modify SDK or emulator limits. Build owner retains its existing
900-second bound. Actual versioned build command:

```powershell
python -I -B benchmarks/android_process_verification.py build --out "$evidence/build-v1" --sdk "$sdk" --java "$java"
```

All three APKs are byte-identical to #215. Cached Rust/main/test compile tasks
are not claimed as new ARM64 or native compiler executions. The controller and
JVM outputs are cleaned/rerun by the existing build driver. Warnings are
GradleDependency, DataExtractionRules and MissingApplicationIcon.

| APK | Bytes | SHA256 |
|---|---:|---|
| Product |32314536|`767e511d8da322ee94ca50c244c6c0c00d6e4f69409bdc6e54518919c908ffc0`|
| Test |2836682|`99a5bff66e099da14465c54b3477f48340e63f55b51246147170a5777030ba28`|
| Controller |55073|`6ea09f4c5105d62e61498d2bebc05de52ce597e30b9681e4975a323b36ef7693`|

## Current SDK2 execution

Current native10, CHILD and retained-parent qualification are pending. Each
needs its own newly admitted standard2GiB/two-CPU API35/x86_64 guest. Finish
source integration/build and preparation before timed launch; dispatch promptly.
The native component gate can be reused only as current source/artifact evidence
on another fresh guest, with all three packages absent. No burned fixture is
adopted, retried or reconstructed. Actual closure and final selected postflight
must be retained before claiming this packet complete.

## Limits

These lifecycle fixtures use scripted inference. No physical phone, real model,
ARM64 execution, thermal/performance, accessibility, unfamiliar-user or joined
adapter-drain result follows. Physical gates retain their prior captured-device
identity blocker; this packet makes no fresh phone-absence claim. Full story
customization and the inherited desktop advisory remain open. No task box is
checked, unrelated emulator stopped, system setting changed, PR merged or release
published. Private diagnostics, models and saves are not uploaded.

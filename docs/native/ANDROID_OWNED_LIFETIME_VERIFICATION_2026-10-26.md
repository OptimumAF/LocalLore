# Owned lifetime admission and measured SDK clients — 2026-10-26

Supporting M10.02/M09.06, implementation PR #218 originally on #216 at3761e462.
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
| SDK2 native components |10 methods/3 classes pass;84 clean measured-v2 clients;339225ms/worker0, known cleanup/capture, stderr0 | `components-v1` |

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

The frozen779-source native10 actually passes on a new standard2GiB/two-CPU
API35/Google APIs/x86_64 guest. Every one of84 original client records is v2,
measured, completed0 with known cleanup, zero stderr and an exact original raw
copy. The maximum client elapsed is10443ms; the maximum server observation is
4673ms against its unchanged15000ms budget. These are diagnostics from this
scripted cohort, not general performance qualification or a timeout-cause fix.

```powershell
python -I -B benchmarks/android_process_verification.py components --out "$evidence/components-v1" --sdk "$sdk" --powershell "$powershell" --build "$evidence/build-v1/result-v1.json" --proposal "$runProposal" --running "$runningReceipt" --server "$evidence/server-v1/server-v1.json"
```

Its bound owned stop returns0. The emulator owner is actually terminal:
`stop_requested`,397465ms/worker1, cleanup/capture/closure true,
`guest_flush_claimed:false`. One final components-only selected-process/server
observation passes after closure: both original native emulator identities and
the original server remain unchanged, zero new device calls. The initially
authored three-guest postflight helper remains unexecuted with its output absent;
the separate executed helper explicitly names only the old components checkpoint.
No external controller, process-death or lifetime-guard-on-SDK case is inferred.

## Concurrent upstream reconciliation

During this live frozen test, GitHub reports #215/#216/#218 merged outside this
chat's actions; #218 is merged at2026-10-27T00:40:20Z, head3946557e. Root performed
no merge. Upstream main3f75b5d6 includes826 mapped inputs, changed APK audit and
host-capacity dependencies, and an unconditional generated Android BuildConfig
field. Physical/LiteRT sources stay outside this input-process profile, but APK
identity still requires actual rebuilding. No old779 gate qualifies that source.

The two planned old-namespace CHILD/retained guests were never prepared or
launched. Their qualification moves to fresh current-main cohorts, retaining
the same task IDs and original complete sidecar requirements. This is a source
dependency change, not a waived lifecycle criterion or a favorable fixture retry.
Next: pin/reconcile current main, rerun host/offline build/JVM/lint/APK audits,
then a fresh native10 gate before new CHILD/retained admission. Finish source
integration and preparation before timed launch. All three packages must be
absent in each fresh external guest; the full1100-second remaining lifetime,
one-shot claim and original canonical helpers remain mandatory. The earlier
failed CHILD/retained collections retain their exact failures and missing bytes.

## Preservation

The terminal host/build/server cohorts are independently preserved as99 original
files plus one explicitly derived audit summary,36388860 indexed bytes. All83
original binding references and every original/copy/ZIP member are rechecked.
The immutable100-file index is29587 bytes SHA256
`a2b2ecf94cb65687df65cf56a9aadb885cf2a1aba327a6590b720fa2196565e8`;
the ZIP is36435957 bytes SHA256
`459e2d002a85e35202c39fa86f0d004cf101ac668ef9e349d352d002b145011d`.
Its101 ZIP members include the exact index. The four named private helper
sources carry source-only attribution; no live guest records or payloads are
copied, and no SDK result is inferred. Source map100200 bytes SHA256
`4bf5f4f5e87ec3a3b38b4b9cc0cac2d548d712dc060424b954ebee388ea268b0`
binds all779 execution inputs.

The native/guest/selected-postflight tranche contains209 original files,
638084 bytes. Independent readback verifies all84 client pairs/168 files,
three exact instrumentation copies and source-derived rosters,57 listener
captures,7 user-zero reads, three fresh package absences and installed hashes.
All retained sources/build/request/tool/report bindings agree. It rehashes every
original/copy/ZIP member, preserving the previous host/build seal unchanged.
Native index70963 bytes SHA256
`14c70edf3a6a27db0441614546d81de50821318520376415e4bbda0101816657`;
ZIP228785 bytes SHA256
`a19b993c77caa7f912d352ef7c2d72a511162ab19e97c51a72ed9f9bf230b03e`.
The private audit helper's own cap refusals are separate retained helper failures,
not native test failures. No SDK images, models, private saves, databases or
unknown payload directories are copied. Derived audit summaries are labeled
separately from original runtime evidence.

## Limits

These lifecycle fixtures use scripted inference. No physical phone, real model,
ARM64 execution, thermal/performance, accessibility, unfamiliar-user or joined
adapter-drain result follows. Physical gates retain their prior captured-device
identity blocker; this packet makes no fresh phone-absence claim. Full story
customization and the inherited desktop advisory remain open. No task box is
checked, unrelated emulator stopped, system setting changed, merge executed by
this chat or release published. Private diagnostics, models and saves are not uploaded.

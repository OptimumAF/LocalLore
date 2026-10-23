# One loaded SDK engine, two Rust-gated roles

Scope: M01.02/M01.04/M01.05 partial development follow-up,
[#5](https://github.com/OptimumAF/LocalLore/issues/5), stacked on control/analyzer
[#40](https://github.com/OptimumAF/LocalLore/pull/40). No production runtime,
model/profile selection, app save integration or full feasibility acceptance is
implied. The concurrent shared durable-app task owns production adapters; this
packet edits none of them.

## Behavior and ownership

The earlier SDK experiment initialized an Engine per model role. The new explicit
warm mode initializes one Engine and uses two fresh Conversations. After the
director Conversation closes, only its bounded private result reaches the host.
The existing Rust fixture/validate oracle must accept that proposal before the
host publishes the narrator request. The narrator Conversation then closes and
the Engine closes. Host launcher drain, final typed owner metrics, exact-APK
package stop/absence and scoped file cleanup must pass before Rust commit.
No transcript, summary, SDK claim or model text becomes an alternate authority.

Each session has a unique host token and a private, create-only owned directory.
Fixed request/result names, strict version/step/token identity, bounded duplicate-
key-aware JSON and atomic publication enforce the [v1 exchange](WARM_PROTOCOL.md).
Consumed bytes must remain unchanged. Existing/foreign/out-of-order files fail
closed. Model output controls neither paths nor tools. Generated text stays in
private transient IPC, is validated in Rust and is omitted from public reports.
Cleaned files are only known names in the exact directory; unknown writer/client
cleanup preserves files and prevents commit. No recursive deletion occurs.

Cancellation during active async generation requests SDK cancellation, drains
the terminal callback and closes owners. Cancellation while waiting for the next
role also abandons the session. Cancelled owners are never reused; a new session
loads fresh owners. An undrained callback/owner close triggers process termination,
not a graceful-disposal claim. The independent90-second SDK watchdog and host
60-second complete-turn budget bound abandoned work, with a separately bounded
cleanup allowance. Native calls or OS scheduling can exceed a target; observed
cleanup and cancellation metrics are reported rather than presumed.

Warm success requires exactly one opened/closed Engine, two opened/closed
Conversations, two completed roles, reuse true and no observed/requested cancel
or process-termination requirement. Balanced zero counters cannot prove reuse.
Each role reports SDK load/generation/token values; step2 load is zero. Full-turn
wall timing includes fixture/validation/commit and control/cleanup after model
identity/provisioning. Prefill, retrieval, durable persistence, UI response,
memory high-water and thermal values are not inferred from these observations.

## Independent findings and corrections

Coordinator owns the Python warm controller/contract, integration and device
operations in `impl/m01-android-warm`. SDK specialist owns Java main/test sources
and WARM_SDK evidence in separate `research/m01-sdk-warm`; reviewer owns only new
adversarial tests/review evidence in `review/m01-warm`. Production/core/storage,
existing controller and build/dependency files remain unchanged by this packet.

The independent review reproduced eight initial host assertions before fixes:
cancelled terminal acceptance, unfiltered final metadata, wrong-role propagation,
unknown earlier-client cleanup, preflight handling and launch after expired
publication budget. Later tests caught two contradictory ownership/cancellation
proofs and a final-file publication/launcher completion race. These now fail
closed, and the reader performs a read after observing launcher completion before
treating an absent final file as terminal. Cross-language inspection caught an
owner-marker newline mismatch and a legitimate `cancel.partial` race before
device execution. The Java exchange now also rejects early foreign results.

All35 independent warm tests and eight coordinator tests pass. The SDK's42 JVM
tests use real filesystem checks and injected owner/callback fakes; they load no
native model. The initial test compile failure (unavailable test Files string
APIs), intermediate build not frozen after later edits and corrections remain
in the [SDK evidence](WARM_SDK_2026-10-22.md) and
[independent review](WARM_REVIEW_2026-10-22.md). Review is finite evidence, not
owner acceptance. Official pinned SDK sources support sequential Conversations
on an initialized Engine; source/license limits remain documented there.

## Reproduce explicitly

Default host checks use only synthetic fakes and never invoke ADB or inference.
Use the existing pinned tools/caches; the separate SDK APK build downloads no
model, installs nothing and changes no production toolchain:

```powershell
python scripts/check.py host --offline
python scripts/check.py android --offline
python benchmarks/spike/android/litert/build.py --java21 <existing-jdk21> --offline --clean
```

Install only the exact frozen source-built APK on an authorized target and select
it explicitly. Existing model files must match publisher hashes; no weights or
private story content belong in Git:

```powershell
adb -s <authorized-target> install -r -t <frozen-sdk.apk>
python benchmarks/android_warm_spike.py --adb <adb> --serial <authorized-target> --owner <built-native-owner> --oracle <built-rust-oracle> --apk <frozen-sdk.apk> --model <verified-local-gemma> --output target/warm-gift.json
```

Repeat with `--cancel-after 8`, then without it for fresh-session recovery; repeat
the sequence on the second selected emulator. Success exits0, cancellation/failure
exits2. Cleanup status is independent from a cancelled turn's result. Package
termination verifies the installed APK hash every time and follows launcher
drain; ADB-client death alone is not native cleanup evidence.

Final exact counts, versions, hashes, all attempts and cleanup are in
[WARM_RESULTS_2026-10-22.json](WARM_RESULTS_2026-10-22.json). The first compatibility
smoke on A preceded addition of the complete-turn wrapper timer; its role/oracle/
session timings remain available, but no total is fabricated for it. Subsequent
timed cohorts use the same frozen APK and ownership implementation. Independent
native Rust oracle/controller binaries are unchanged #37 artifacts, not newly
storage-integrated oracles. Each commit reconstructs an ephemeral original
fixture; no durable gameplay claim follows.

| Actual final check | Result |
| --- | --- |
| `python scripts/check.py host --offline` after timer addition | Exit0:89 Rust test entries (one auxiliary child helper),191 Python tests,four fixture comparisons,three linker tests,format/Clippy |
| `python scripts/check.py android --offline` | Exit0:both Rust ABIs,31 JVM tests,production app/test APKs,manifest/ABI/ELF/ZIP audit; zero lint errors/one unsuppressed dependency advisory |
| Isolated SDK fresh offline clean build/analyzer/APK audit | Exit0:51 tasks executed,42 JVM tests,actual locked analyzer/dependency analysis,zero requested permissions,two ABIs,16KiB ZIP alignment; zero lint errors/two unsuppressed advisories |
| Independent warm adversarial suite / coordinator suite |35 / eight Python tests pass, included in final191 |
| All explicit SDK requests on the selected two emulators |Seven requests/twelve attempted roles retained:five Rust-committed turns,two cancellations; no failed attempt omitted |
| Each committed warm turn |One Engine/two fresh Conversations,all closed; director validated before narrator,second-role load0,one event/revision,exact retry unchanged,recipient observation1/absent observer0 |
| Each cancellation after eight seconds |Active SDK cancel called,terminal callback drained,warm cancel observed; one Engine/one Conversation closed,zero completed roles,zero narrator/commit calls; subsequent fresh two-role turn accepted |
| Final hash-verified package stop and scoped inventory |Both stopped;known session files removed;zero private warm entries,native run directories or owned benchmark processes |

The four final timed committed turns observed19,843–22,797ms from fixture through
Rust commit; both cancelled requests took11,391–13,125ms including cleanup. These
are four/two individual emulator observations under uncontrolled cache/host load,
not phone latency qualification, a percentile estimate or a backend comparison.
The initial smoke additionally overlapped builds and lacks the final wrapper
timer. Java counters and callback/close returns are finite ownership checks,
not a native heap/sanitizer audit. The unchanged production Compose APK was built
and tested on JVM, not reinstalled/instrumented by this runtime-only packet.

Both selected execution targets are Android15/API35/x86_64/4096-byte pages. Five
emulators and zero physical phones are visible; three other emulators are left
untouched. SDK ARM64 is packaged, not executed. Source/Java metrics and public
result tokens do not qualify exact tokenizer/conversion parity, hidden-reasoning
filtering, free-form faithfulness or lack of cross-role guesses. Fresh contexts
avoid intentionally sharing a conversation's history; broader context-isolation
and quality evaluation remain separate gates.

Full M01.02/.04/.05 tasks remain incomplete/in review, M01.01 blocked on an
authorized physical phone. Original #37 corrupt-cleanup/oracle-startup transients
remain unexplained and retained in prior all-attempt results. This follow-up
does not explain them. No phone/performance ranking, sustained memory/thermal,
API26/28/36 or16KiB OS, original Qwen3.5 conversion, production profile, real-model
Compose, warm multi-turn/archivist session, durable persistence, hosted CI or
release qualification is inferred. No new dependency, cloud fallback, telemetry,
PR merge, release, access/protection change or private upload is performed.

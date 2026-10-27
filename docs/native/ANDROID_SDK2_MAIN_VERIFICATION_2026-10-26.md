# Current-main SDK2 prerequisites and restoration — 2026-10-26

Supporting M10.02/M09.06, PR #219 on main3f75b5d6. Executable checkpoint
aa9deaee has827 tracked inputs; documentation changes are outside that map.
No full task or milestone acceptance follows. This is scripted inference,
not physical-device/model/ARM64 performance qualification.

## Current prerequisite fix

The current external runner required measured-v2 clients for its own output,
but its native10 gate still used only historical readers. Timing fields could
be removed from an otherwise complete gate row while the current worker and
parent accepted that historical shape. No actual record tampering or gameplay
failure was observed; independent source review supplied the counterexample.

`_qualified_current_gate` performs the unchanged full historical native-gate
validation, then requires exact complete measured-v2 client pairs and returns
the same qualified request. The current worker uses it before Session/SDK, and
the parent repeats it after original deep external validation. Generic
`qualified_gate` and `validate_execution` remain historically readable. Source
review found no concrete bounded gap and excluded authored tests from its review.

Seven original tests retain actual bound ten-method runner frames, raw copies,
owners, source and client records. Their real worker and parent paths cover
positive current evidence, independently downgraded observer/SDK rows, all four
external cases, malformed timing, incomplete file sets and rebound wrong classes.
Four old orchestration mock lines now identify the new prerequisite boundary;
all original test actions, assertions and rosters remain. No cap, deadline,
cadence, dependency, gameplay, SQLite, model or local-only policy changes.

## Host and offline build actually executed

Windows/Python3.14.7/JDK21, existing cached Gradle8.11.1/AGP8.10.1/SDK components.
Private immutable finite owners retain original requests/tools/source maps and
binary outputs on C:. No new SDK/server lifecycle or phone operation is needed
for host tests.

| Actual cohort | Result |
|---|---|
| Baseline826 offline build-v1 | pass256699ms/worker0;259 executed JVM tests/30XML and11 audits |
| Baseline826 host-full-v1 | **failed capture**,260846ms/worker1,output_limit,262144 stdout bytes,capturefalse; no complete suite pass |
| Test-only827 native-gate RED |7 methods/6 assertion failures in5.354s;8021ms/worker1, known cleanup/capture, stderr0 |
| Corrected827 host-full-v2 |1476 pass in154.722s;158604ms/worker0, known cleanup/capture, stderr0,2850 stdout bytes |
| Corrected827 build-v2 |pass33715ms/worker0;259 executed JVM tests/30XML,0 failures/errors/skips; both lints0 errors/3 warnings;11 APK audits |

All827 before/after inputs agree in the final host/build. Final source map is
106694 bytes SHA256
`3077cc60167ec850b39a805ef2c4aa3201307c8c5949fef06ef64dbf563145ff`.
The original seven-test RED dynamically reaches the forbidden Session boundary
or lacks the expected parent refusal, rather than failing on an absent symbol.

The initial full host attempt retains its failed output-limit outcome. A new
immutable private helper uses standard concise unittest output and retains both
loader-count and actual test-summary records; the same256KiB capture limit and
600-second host bound remain. SDK/controller/guest limits are unchanged. It does
not reconstruct or relabel the earlier truncated run.

Both builds run the existing versioned entry point:

```powershell
python -I -B benchmarks/android_process_verification.py build --out "$evidence/build-v2" --sdk "$sdk" --java "$java"
```

The current product/test APK hashes differ from the older779 checkpoint despite
identical byte counts. Main also adds a generated BuildConfig field; this check
does not isolate the sole cause of the byte differences. Both current builds
have the following exact hashes; the controller is unchanged. Cached compiler tasks
are not new ABI execution evidence. JVM/controller outputs are rerun by the driver.

| APK | Bytes | SHA256 |
|---|---:|---|
| Product |32314536|`78747dd80eda5ef4453d29eeff98f8fedc57e2c5d83b15653591a8d9ef412443`|
| Test |2836682|`6b16e88fe96f1419bf05d5fa1b581ae1449517843ad1ca39bbd896838f383528`|
| Controller |55073|`6ea09f4c5105d62e61498d2bebc05de52ce597e30b9681e4975a323b36ef7693`|

## SDK execution and limits

The six terminal host/build/server directories and six fixed private helper
sources have an independently verified recovery seal:192 originals plus one
labeled derived audit,72317733 indexed bytes. All160 binding references and
every original/copy/ZIP member agree. Immutable index56853 bytes SHA256
`14d5e6608022356d5269076d52db3f64351922e2b08bce17a5d8b8ae84e5629a`;
ZIP72408622 bytes SHA256
`5b3303204ea1857a2b69aa511c2a0686105a9843b3a3b1df59e25f2ba05607d0`.
Its194 members include the exact index. The failed cap-limited run and original
RED are retained separately; concise full-host evidence uses its loader count,
actual result summary and final runner frame, not a per-method transcript.
Live preparation/guest data, models, images and databases are excluded.

Current827 native10 actually passes three classes/ten methods:81 clean measured-v2
clients,275410ms/worker0, known cleanup/capture and empty owner stderr. All
client timestamps are strict measured values; maximum client10429ms and server
observation3357ms retain their original budgets. These are cohort diagnostics,
not a timeout-cause fix or a general speed claim. The current client count is
observed, not a fabricated fixed84 requirement.

Its bound owned stop returns0 and the emulator is actually terminal0. Guest
owner reports `stop_requested`,388877ms/worker1, cleanup/capture/closure true and
`guest_flush_claimed:false`. No same-installation continuation is used.

CHILD and retained-parent qualification for this827 map remain pending.
Each needs its own new standard2GiB/two-CPU API35/x86_64 guest. Existing current
profile capacity checks apply before preparation and launch; no floor is bypassed.
Finish all build/integration/preparation work before timed launch, dispatch
promptly, retain the full1100-second admission and1200-second owner ceiling.
All three packages must be absent in a new external guest. The separate native10
gate and all original retirement bodies, transport footers and four retained
canonical sidecars remain mandatory. Missing/failed outputs cannot be invented,
summarized away, or promoted from old-source cohorts. Existing earlier failed
CHILD/retained attempts remain failed and unqualified.

The recorded unrelated process identities pass the new selected preflight,
with zero device calls. Final selected postflight requires actual closure of
all three exact owned guests. No system setting change, unrelated emulator stop,
merge, release or private-data/model upload is performed by this chat. Full
customization, real phone/model/accessibility/joined-drain and the inherited
desktop dependency advisory remain separate open gates.

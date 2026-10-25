# SDK phase and process-instance evidence, 2026-10-23

Refs [#5](https://github.com/OptimumAF/LocalLore/issues/5), M01.03/M01.05
partial, claim `6374428287`. Base is unmerged [#113](https://github.com/OptimumAF/LocalLore/pull/113),
`ca25da5fea7473ec9d61653526da51c096dfbb25`. This packet changes the isolated
experiment, not production inference or the Rust engine.

The previous [recovery](RECOVERY_VERIFICATION_2026-10-23.md) established a failed
turn with no accepted gift. Its SDK crash still lacks an attributable exit record
or durable last SDK phase. A new checkpoint journal and optional Android process
summary address that diagnostic gap; they cannot retrospectively diagnose it.

## Implemented boundary

The [versioned protocol](SDK_PHASE_PROTOCOL_V1.md) specifies the fixed private
journal, complete strict reader, identity/time fields and lifecycle markers.
The cache experiment syncs its first checkpoint before native/SDK entry.
PlayRunner journals work boundaries and gates subsequent work on persistence.
Cleanup still cancels, drains, closes and joins when its diagnostic sink fails.
Typed close uncertainty propagates through primary and suppressed exceptions to
the Android process-termination fence. Accepted history remains authoritative if
a post-commit diagnostic write fails; no rollback or automatic retry is claimed.

The optional process summary is below Android's 128-byte limit. Exit correlation
requires the exact original PID, package UID, process name and nonce/start token
from the validated journal. It reports a process-instance match and numeric OS
reason/status, not a crash cause. Missing, stale or ambiguous evidence stays
unknown. Wall-clock changes do not create an elapsed-time identity match.

A separate explicit `.phaseprobe` package exercises persistence and correlation
with deterministic self-kill/read operations. It uses no model, native engine,
external cache or SQLite operation. Original cacheprobe APK/data/model sessions
are outside its namespace. The strict host decoder distinguishes a valid
journal observation from a complete instance-matching control.

## Host and Android checks actually run

Python checks at source `7353db3` passed:

```powershell
python -B -E -m unittest discover -s scripts/tests -v
python -B -E -m unittest discover -s benchmarks -v
python -B -E -m unittest discover -s benchmarks/spike/android/litert -v
```

Results: **313 script / 140 benchmark / 34 SDK-helper tests**. The 16 new phase
decoder methods are included in 313. The SDK-helper selection used a dedicated
D-volume temporary directory. An initial default-C-temp invocation passed 33 of
34 and errored on the existing D-only output test; the D-temp invocation passed.

The author [report](PHASE_AUTHOR_2026-10-23.md) records 27 focused JVM passes,
including 23 checkpoint-failure subcases, sticky close uncertainty, partial
writes, mandatory cleanup, post-commit uncertainty and a maximum fake spent
path. Its 92 rows fit the 96-row limit; a separate valid 96-row numeric-bound
fixture exceeds 32 KiB, justifying the 64 KiB diagnostic cap. Gameplay and SDK
budgets are unchanged. The author retains the initial command-quoting and
incorrect test-size-assertion failures.

Three fresh D-output Android qualifications are retained:

1. Source `7353db3`: production Java compiled, but Android unit-test compilation
   rejected three test-only `Files.readString/writeString` calls. No qualified
   artifact or installation followed.
2. Source `7afe531`: explicit UTF-8 byte APIs corrected those tests. Qualification
   passed. This APK was superseded before installation.
3. Final Java source `04326712278eaa0a91073511085c0c97b7375123`: a partial read
   failure now resets to the exact four-key error result. Fresh qualification
   passed **96 JVM tests**, zero failures/errors/skips; lint **zero errors and
   nine existing warnings**. Locked SDK/analyzer identity, dependency analysis,
   separate package/runner, zero permissions, no automatic components and native/alignment
   audits passed. All build stages completed with known process cleanup.

Final APK: **63,666,944 bytes**, SHA256
`df2b2552fd0ee2de202d19ab5381bf253674f32d4e2ed5b4b2c99a19ae4b3dda`.
All four packaged native libraries are byte-identical to the previously
qualified `0cf4c253...` cacheprobe APK. The two Rust binaries were extracted only
from that hash-verified artifact; production Rust inputs are unchanged, with
only an earlier Rust integration-test delta excluded from the comparison. No
new native compilation or ARM execution is claimed. Runtime/model versions,
schema2 and guarded action validation remain unchanged.

## First actual device attempt: setup refused

The first owned cohort completed in 21,031 ms, child exit2/known cleanup. All
229 recorded commands completed with known cleanup. It stopped at the storage
parser before installation or any session/crash/read operation: fixed
`df -k /data` displayed `/data/user/0`, while the parser required `/data`.
The raw response reports 1,738,440,704 available bytes. This was a parser defect,
not a measured capacity refusal. Both post-preservation records matched old
APK/protected metadata and the new package namespace was absent. The same parser
prevented the final storage/inventory closure; that failure remains explicit.

This namespace is sealed separately: 480 selected files/291,080 bytes, index
SHA256 `5b2c493d41f8481931038c063c283b0af871aa003089cef1ad3a1eb3a1bf16f1`.
No phase APK was installed and no inference was attempted in that cohort.

## Corrected actual device control

A separate namespace and reviewed source corrected only the setup defect. The
new `android_phase_storage` parser requires the exact bounded two-line response,
numeric bounds and one of the two fixed mount labels. The caller dereferences
both fixed paths with `stat -L` and requires equal filesystem identity before
using available space. Official Android 15 Toybox source confirms that `-L`
selects `stat` rather than `lstat`. Eight new original regression methods,
including the retained response and mismatched-device adversaries, are included
in the final **321-script-test pass** at Python source `b27e59f`. The earlier
313-script result overlaps this run. Benchmark140/helper34/JVM96 results cover
unchanged corresponding source; no new APK or native build was needed.

The corrected owned cohort passed in 33,125 ms with exit0 and known cleanup.
It installed only the qualified `.phaseprobe` APK on B, then ran exactly one
deliberate crash and one read. The exact 76-byte crash terminal preceded an
independent namespace-absence check. The fresh app reader strictly validated
the persisted journal and returned two checkpoints, last `probe_kill`, role
`none`, fresh-reader identity, and exactly one process-instance match with OS
reason2/status9. Both `journal_verified` and `control_passed` are true.

The 396-byte read terminal SHA256 is
`6d8e8596bad8e4e5e17a2077dd5dfcdedbbf47ba93583d9b22aac8d92b00d115`;
the crash terminal SHA256 is
`f3ca40e0a3bf20eaf9ab861db129a85ecafc52160588fc2089c7bb0239bc1d94`.
The coordinator independently decoded the retained result and rehashed all 322
command outputs. The host did not export or independently parse raw journal
rows/PIDs; the app's strict reader and correlation code supply that observation.
This known deliberate self-kill does not attribute the old SDK crash's cause.

All 322 corrected-cohort commands completed with known cleanup, including seven
expected namespace-absence exit-one probes. Final A21/B23 APK maps retain every
original A21/B22 entry, adding only the qualified phase package to B. Original
model/cache metadata match; no new model-integrity/content read is implied.
The phase namespace was absent after crash and at closure. Inventory was four
emulators and zero other devices. B retains the new test package and journal.

Guest free bytes before/after installation were 1,738,395,648 / 1,674,670,080;
before/after the tiny control, 1,674,485,760 / 1,674,469,376. Final C/D free bytes
were 8,133,230,592 / 326,254,399,488. Original independent reserves and the
512 MiB installation/64 MiB control allowances passed. These are admission and
diagnostic checks, not phone/SDK performance measurements. The corrected seal
binds 673 files/410,799 bytes, index SHA256
`ca96857de9eef8063cd4d61b303a5982a9c3137126b63dd872559612c5d15a39`.
See the [device report](PHASE_DEVICE_2026-10-23.md) for both cohorts and gaps.

Across both attempts, all 551 recorded commands completed with known cleanup;
nine expected absence exits remain explicit. No SDK/inference/model-content
read or copy, SQLite operation, old package replacement, canonical mutation or
AVD lifecycle action occurred. The prior failed turn remains outside this test.
Device leases are released; no further device calls follow this packet.

## Evidence boundaries

The initial selected host seal binds 74 files/63,874,439 bytes, index SHA256
`3536db9eb10f38b9b7f751ff1dd07b8a767e1252919293591acf52d83f9a74f5`.
The author seal binds 16 files/94,962 bytes, index
`89a55da259ec912b1cf84042c2637786e4a6e879e3c24b8998999ed0b2d69d54`.
Official API/source research binds seven files/7,423,277 bytes, index
`61240c7ef3dd6595fba0d479dd0be5b3452281bc11254c3629ce8aafd6d4e4c6`.
All selected entries were independently rehashed. Mutable build caches/temp
are excluded. No raw journal, process identity, model/cache payload or private
diagnostic text is published.

The follow-up host seal binds seven files/44,970 bytes, index
`b14c1d199bf2b3865172dfd9c23a926f24a45b6fa46a82d24f5bc74342a0f776`.
The separate 7,000-byte Toybox stat source has SHA256
`a2904edfefe6094a6ad255cc27a60e25dc80ac746150550905f3fe8689b8c9b9`.
The [safe aggregate](SDK_PHASE_RESULTS_2026-10-23.json) binds all selected sets;
the [independent review](PHASE_REVIEW_2026-10-23.md) audits the final scope.

M01.03/M01.05 remain partial and in review; full tasks stay unchecked pending
their complete criteria and owner acceptance. M01.01 is blocked without an
authorized physical phone. A had no write/inference admission in this packet;
its prior storage gate remains pending. Successful guarded SDK inference,
original crash diagnosis, whole-current-main schema compatibility, ARM execution,
quality and sustained memory/thermal qualification remain unresolved.

Next runnable task: integrate bounded stopped-session SDK phase readback into
the cache controller, then one freshly admitted traced guarded SDK control.
Preserve the recovered failed turn and obtain fresh model/storage/ownership
admission before inference. No runtime/model selection or merge follows here.

# Explicit-cache SDK control verification, 2026-10-23

Refs [#5](https://github.com/OptimumAF/LocalLore/issues/5)
(M01.03/M01.05), claim `6371399958`. This packet is stacked on unmerged
[#101](https://github.com/OptimumAF/LocalLore/pull/101), base `22968a1`.
It adds an experimental controller, strict receipt decoder and app-domain model
integrity operation. Production Compose, Rust authority, dependencies, runtime
selection and gameplay permissions are unchanged.

The companion [aggregate](CACHE_SDK_CONTROL_RESULTS_2026-10-23.json),
[device report](CACHE_SDK_CONTROL_DEVICE_2026-10-23.md) and
[independent review](CACHE_SDK_CONTROL_REVIEW_2026-10-23.md) distinguish actual
observations from remaining gates. Raw transport, generated text, SQLite files,
device identifiers, model weights and private host paths remain local.

## Implemented boundary

`android_cache_result.py` extracts the existing play validator without changing
the legacy wrapper. The new decoder rejects duplicate/unknown JSON fields,
unsafe counts, ambiguous terminal ordering and inconsistent storage identity.
It preserves a valid committed inner receipt when a later outer SDK, volume,
transport, cleanup or storage check fails. A failing check cannot erase evidence
that canon committed. Four integration tests exercise the real decoder through
the controller, in addition to isolated decoder/controller tests.

`android_cache_control.run_control` admits the whole lifecycle before its first
package operation. It binds the frozen APK, verifies process identity before
stopping the isolated package, requires a live full-model verification callback,
then repeats the qualified stop before one play request. It retains raw output
before decoding, verifies final absence, and keeps storage, transport, SDK and
accepted-turn verdicts separate. Unknown client cleanup fences subsequent calls
and post-measurements. There is no inference retry, model provisioning or file
deletion in this controller. See the [caller contract](CACHE_SDK_CONTROL_HARNESS_2026-10-23.md).

The new APK's `verify_model` reads the fixed framework-selected model through
one read-only, no-follow descriptor and a bounded buffer, checks full SHA256,
byte count, EOF, path/descriptor metadata stability and volume identity, then
closes it. It initializes no SDK engine or Conversation. Framework directory
APIs may create/fix app-owned directories. Metadata checks do not defeat a
hostile OS, concurrent same-UID replacement after observation, or coarse actual
filesystem timestamps. See the [operation and qualification](CACHE_MODEL_VERIFY_HARNESS_2026-10-23.md).

## Pins and checks

The qualified APK is 63,598,424 bytes, SHA256
`04eef96b7177aaef275574f9ee45d25efa9b181bab4fcb0a363d8077a4e4fb7d`,
Java source `a033d08` (integrated as `925caee`). LiteRT-LM remains Android
0.18.1 at `bda624851d74be34d4e1f7fac1fc4155939539c7`, CPU with four threads.
The model is the existing 2,588,147,712-byte Gemma artifact, SHA256
`181938105e0eefd105961417e8da75903eacda102c4fce9ce90f50b97139a63c`.
No model/runtime dependency or license changed. The profile remains 4096 context,
350 director/220 narrator tokens and a 60,000 ms turn budget; host instrumentation
is bounded at 110 seconds and the existing app watchdog at 90 seconds.

Actual host commands, with Python 3.9.12:

```powershell
python -B -m unittest discover -s scripts/tests -v
python -B -m unittest discover -s benchmarks -v
$env:TEMP='<existing caller-owned D: temporary directory>'
$env:TMP=$env:TEMP
python -B -m unittest discover -s benchmarks/spike/android/litert -v
git diff --check
```

The final script suite passed **259** tests. Benchmark tests passed **140**;
SDK build-helper tests passed **33**. Focused controller/decoder/integration/
admission selection passed **71** tests. These selections overlap; they are
not additive unique counts. The final pin did not change benchmark/helper code.
The helper recheck initially used the default C: temp directory and failed one
existing D:-only output assertion; all 33 passed with the required D: temp root.
Both invocations were retained. The SDK build helper itself still requires D:.

Actual Gradle qualification passed **73 JVM tests**, zero failures/errors/skips,
plus dependency/analyzer, zero-permission manifest, both native ABI/export,
16 KiB ELF and ZIP alignment audits. Lint: zero errors, nine warnings
(OldTargetApi 1, GradleDependency 1, UsableSpace 7). Java compiler was 21.0.4;
launcher used Java 17. The unchanged native pair was reused only after matching
the earlier frozen provenance; this is not a fresh Rust build or ARM64 execution.

The original qualification controller refused at host capacity after Gradle
and before the permissions audit. A separately admitted audit-only continuation
completed qualification without recompilation. Retained earlier failures also
include a JUnit class-name initialization typo (no test bodies ran), decoder
terminal-order regression (fixed), and two stale integration stop-count assertions
after the new pre-play stop (fixed). Successful reruns do not delete these attempts.

## Provisioning observations

Both selected devices are Android 15/API 35 x86_64 emulators: A uses Emulator
37.2.12 build 16428233; B uses 35.3.12 build 12990079. No physical phone was
available. A stayed read-only and storage-blocked; its mismatched old model and
cache were preserved. Only B received the new isolated APK/model.

The initial absent-model app receipt proved zero SDK owners. A fresh host source
check completed two full whole/chunk passes over one held handle: 78 chunks per
pass, exact expected size/hash, stable named/descriptor fingerprints. The source
was opened separately by ADB during transfer; this is not direct-descriptor transfer.

Tiny transport controls exposed Windows stdin transformations: shell input
changed CRLF and truncated at Ctrl-Z; `exec-in` did not preserve remote exit
status. Those paths were rejected before any model transfer. Official ADB
[command documentation](https://android.googlesource.com/platform/packages/modules/adb/+/refs/heads/main/docs/user/adb.1.md)
and [pinned client source](https://android.googlesource.com/platform/packages/modules/adb/+/5cd3ab66dd0a7ba0173b01f954fbe76c21269483/client/commandline.cpp)
informed the fallback; actual installed-binary tests established its behavior.

`adb push -Z` passed a 275-byte control containing all byte values plus CRLF,
NUL and shell-escape characters. A fresh exclusively reserved empty target and
nonexistent-source negative control failed without target mutation. One model
sync then completed in 22,016 ms with child exit 0, parent cleanup confirmed,
source descriptor closed and source fingerprints stable. Full shell target and
separate app-domain reads both matched the model hash/size. Target inode changed
during sync; ownership was checked on the fresh reservation before pushing.
This is no atomic no-overwrite or hostile-race guarantee.

Whole-copy admission included the model bytes. B's cache free space changed
8,573,018,112 to 5,984,870,400 bytes, exactly the model size; generated cache
remained 34 bytes. Userdata stayed 1,734,619,136 bytes free. Pre/post host and
guest policy checks passed. The active guest volume and host image/overlay
mapping, rather than an external-looking path alone, establish the separate
backing used by this experiment. Observed reserves are not quotas or proof of
maximum future SDK growth. Old package hashes and old model/cache metadata were
unchanged: A 21 packages, B the original 21 plus the isolated cacheprobe package.

The live driver also compares actual host disk DeviceID, serial, capacity and
filesystem across samples, propagating uncertain host-sampler cleanup into the
same sticky client fence. Backing checks bind the original emulator process
start/arguments and the owned raw-image/QCOW2 header and backing-file identities,
with fresh guest attachment evidence. The legacy console block query returned
`KO`; an active monitor graph query was unavailable. This does not prove absence
of hostile hotplug changes. Retained local parser failures for seven-digit
Windows timestamp fractions, a replacement-script escape, and relative QCOW2
backing resolution were corrected before the one SDK dispatch.

## Actual SDK result: requested gift rejected

Exactly one play request reached actual SDK generation. The director completed
with 1,855 input tokens and 15 output tokens; Rust rejected the proposal with
`Agency`. No narrator or repair ran. Revision and receipt counts stayed 0 to 0;
the authoritative result reports unchanged canon, drained ownership and equal
reopen state. No fallback or retry occurred. The outer worker completed cleanly,
but the requested gift check is **false**, because no gift turn committed.

One SDK Engine and one Conversation opened and closed, with balanced owners,
terminal callbacks, no required process termination, valid transport and verified
final package absence. Main-loop pulses were observed during generation; they
are not a physical-device responsiveness qualification. The per-turn receipt
reports load 6,394.3941 ms and generation 49,591.5411 ms; separate SDK metrics
report generation 49,551.7118 ms. These timer boundaries are retained separately.
Controller wall time was 91,704 ms including model verification and samplers.
This is not a successful full-turn latency measurement or model ranking. The
model was fully read just before execution, and host load/file cache were uncontrolled.

Pre/post storage checks both admitted: generated-cache growth 788,412,770 bytes,
guest cache net consumption 788,422,656 bytes, userdata net consumption 81,920
bytes, host C: net consumption 21,184,512 bytes and host D: 856,211,456 bytes.
Cache growth and filesystem consumption are separate measurements. All generated
cache/session/SQLite artifacts remain retained; no cleanup of story files occurred.

The current action intent guard checks exact compiled commands. A command such
as `wait` can be schema-valid yet fail that guard; it cannot silently replace
the gift intent in a committed turn. An earlier review warning inferred too much
from the schema alone and was corrected after reading the guard. The retained
aggregate does not contain the generated command, so the particular cause of
this `Agency` rejection is unestablished. No canonical-event snapshot was needed
for an uncommitted result. The next runnable task is a bounded, privacy-preserving
diagnostic for the schema/intent rejection boundary, starting with deterministic
host fixtures under the unchanged profile before considering another model call.

After the known final stop, source integrity passed two further complete
78-chunk reads in 21,203 ms. A full shell read and a separate app-domain full
read again matched the new target's expected model hash/size. That final reader
reported zero SDK owners and was stopped with verified absence. Original A/B
package hashes and protected old model/cache metadata remained unchanged; the
old and new SDK packages were absent from the process list. Final inventory was
seven emulators and zero other connected devices. No additional SDK generation
or canonical-database capture was performed.

## Host preservation and limits

Host capacity fluctuated independently during preparation. Only two inactive
compiler trees were successfully relocated with full content and internal
hardlink-topology verification and junction readback: 3,427 aliases, 3,141 unique
files, 285 internal hardlink groups, 1,667,443,128 unique bytes. Mutable compiler
payloads are excluded from immutable evidence seals.

A mixed verification tree contained generated fixtures, closed evidence and an
old launch stderr log. Its complete backup passed, but removal hit a Windows
sharing violation on that log after deleting 423 aliases; the command-line
census did not establish its handle holder. A separate corrective operation
restored missing paths without overwriting surviving files; all 2,143 aliases,
2,115 unique files and 28 internal hardlink groups then passed full original-path
hash/topology verification. That tree remains an ordinary original-path tree;
it was not successfully relocated. Original inode/ACL identity is not claimed.

A further compiler-only copy hit `MemoryError`; its source and partial backup
were retained. Five other candidates were not copied. Further moves stopped
when headroom recovered. No unrelated AVD was stopped. Neither the host free-space
recovery nor the memory error has an established cause. These failed attempts
and corrective receipts are part of the retained evidence.

The closed host metadata/log manifest binds 121 files (SHA256
`f3f3342dfd9921125a21858ebf528ff8dcc4483edb833970d55529fbc84cff5d`);
the build/controller author manifest binds 58 files (SHA256
`0a4e77c7d00b4754a8db7871c72c4ccd0da90f94f01151b47a5244ae7bd599a7`).
Both sets were independently rehashed. Binding counts may overlap across sets;
they do not count model weights, live disk images, private databases, mutable
compiler payloads or open logs as immutable evidence. The device seal and final
sanitized receipt are bound separately in the aggregate.

The sealed device index binds 229 files (SHA256
`f29c3b9e5155141cbee14b5f6ded14ee0c44e21d8709265f43b10b9074b7683e`).
Its closed journal records 768 Device commands, all completed with known cleanup:
741 exit 0 and 27 exit 1, including expected absence/path probes. Worker ADB calls
are separately bound. The final host census had no selected/inventory client
match, one server and one unclassified ADB process with unavailable command and
executable fields. This is not proof that every possible host ADB client was absent;
that unclassified process was neither claimed as owned nor stopped.

M01.03/M01.05 remain partial pending owner acceptance and the wider task criteria.
M01.01 and physical latency, sustained memory/thermal, ARM64 execution and complete
quality/backend selection gates remain blocked or unqualified. This actual gift
request did not commit; no potion transfer or narration-quality pass is claimed.

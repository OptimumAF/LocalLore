# Original synthetic transfer verification, 2026-10-25

Refs #9 (M05.05 prerequisite), #5 (M01.05 supporting), root claim
[6404322953](https://github.com/OptimumAF/LocalLore/issues/9#issuecomment-6404322953).
This follows open PR178 at `ecc83436`. No model, SDK, runtime or physical-device
qualification is inferred from synthetic transport work.

## Implementation and source basis

The [fixed protocol](RECEIPT_TRANSFER_PROBE_PROTOCOL.md) adds a disabled-by-default
controller, deterministic original 1 GiB fixture, fixed private create-only sinks
and strict proof parsers. CAT and DD_1M retain raw exec; SHELL_CAT requires exact
protocol/exit/binary gates. The tiny binary control uses the same owned worker
and regular held-FD input path as large copies. Full guest size/SHA proof follows
known client completion/cleanup and source/lease postchecks; host cursor and
client zero alone never qualify a destination.

[Pinned official sources](RECEIPT_TRANSFER_SOURCE_RESEARCH_2026-10-25.md) motivate
the buffer and non-terminal controls. Installed executable/source correspondence,
causes of older failures and performance gains remain unproven by source review.
No new dependency, model, runtime profile or production controller change occurs.

## Host verification actually performed

| Check | Result |
| --- | --- |
| Contract author's pure tests | 16 pass, 0.011 s; owner 297 ms, cleanup known |
| Central contract tests | 16 pass, 0.010 s; owner 267 ms, cleanup known |
| Independent final controller tests | 31 pass; owner 7530 ms, cleanup known |
| Central focused suite | 82 pass, 15.117 s; owner 15579 ms, cleanup known |
| Central full Python suite | 1035 pass, 102.074 s; owner 103204 ms, cleanup known |
| Actual original host source creation | 1 GiB, owner 2832 ms, cleanup known |

All final check owners above return zero with stderr zero. Full Python raw output
is 186123 bytes, SHA256
`eebac4a0c6063389dd2f3febef5c9374e81cefc15293420bbb7a209772038064`.
All 110 captured benchmark/test Python files remain unchanged. Focused raw SHA:
`0d3c203e02263ad1773b5a229fc577068f288b23a7b254cc4f10200bb4f8203c`.
Original source creation forces the fixed bytes and verifies their generated
digest; each actual transfer independently authenticates the entire held source.

Retained failures: independent fully hash-bound tests reproduce boolean numeric
completion and invalid helper-UID admission in the new controller. An initial
attempt also has four incorrect test exception assertions; the next attempt
isolates six genuine malformed-lineage subcases without test errors. Narrow
fix `b798a929` passes the unchanged RED suite, then final ownership tests pass.
Source review finds a pipe/regular-file binary qualification mismatch; `278d06ef`
fixes the input path before any actual grant. All attempts remain private.

Executed-input snapshot `2f222268c4bc928fdcd80755fb66af9c9cb956ff` contains 62
required source files; manifest 9389 bytes, SHA256
`7becf912856c03a28cf2205ad4bcf69aab0c7c93f581ef6be443204398929baf`.
Independent review verifies all 62 current and 62 captured source hashes, eight
unchanged Android compilation bindings and both receipt APKs against the prior
audited copies. APP SHA256:
`c9325b6a50483afc0d928ab3d16c14c5a43caebacc4a96d11f16328f976f15fa`;
TEST SHA256: `e5d09b0f436237b51c647b4cc43a74e8f76b08bfdfe045907aa89ee6724f359d`.
No fresh Rust, Gradle or native-model checks are claimed for unchanged code.

## Fresh emulator controls

The new target is prepared with known closure and the same 8 GiB / four
CPU profile, 12 GiB userdata and 8 GiB removable storage. The sampled two-second
40 GiB floor on both drives is a guard, not a reservation or hard growth ceiling.
All older uncertain targets remain quarantined. No model weights or SDK grant
is part of this experiment.

The first owner exits before preflight after 11566 ms, worker 2, cleanup/closure/
output capture complete, guest-flush false. It retains 10394 stdout and 1026
stderr bytes; owner-result SHA256 is
`4ad7899e4481ecdf816623e67cb163323ba36277c8e3814168bb0da9b77a0311`.
The emulator reports a guest-RAM backing-map failure and fallback, followed by
insufficient Windows commit capacity: 8184.605469 MiB remaining versus 8192 MiB
needed. This does not explain the earlier mapping failure. The storage guard
stays healthy. The lease refuses `owner_stopped` before the preflight grant is
created; only its proposal exists, with no worker, install or device command.
The target is quarantined and is not restarted or adopted.

A subsequent read-only host sample observes 31267123200 physical bytes available,
58004791296 committed bytes and a 72694566912-byte commit limit. These are later
observations, not the exact startup state. They demonstrate why free physical
RAM alone cannot establish launch capacity. [Official Android guidance](https://developer.android.com/studio/run/emulator-troubleshooting#windows_free_ram_and_commit_charge)
explains the full guest-memory commit request on Windows.

The follow-up host gate uses system counters from
[GetPerformanceInfo](https://learn.microsoft.com/en-us/windows/win32/api/psapi/nf-psapi-getperformanceinfo),
with [CommitTotal/CommitLimit in pages and PageSize in bytes](https://learn.microsoft.com/en-us/windows/win32/api/psapi/ns-psapi-performance_information).
It does not substitute the process-specific `ullAvailPageFile` field from
[MEMORYSTATUSEX](https://learn.microsoft.com/en-us/windows/win32/api/sysinfoapi/ns-sysinfoapi-memorystatusex).
The project policy requires headroom of twice guest RAM plus a 2 GiB reserve:
6 GiB for the existing 2 GiB profile and 18 GiB for the existing 8 GiB profile.
This conservative budget is not an OS requirement, allocation reservation,
mapping-error diagnosis or launch guarantee. Physical RAM, disk, CPU, profile,
source binding, identity and deadline checks remain. Both profiles recheck in
the owned worker before claim or SDK launch. No applications, pagefile or system
settings are changed, and the device profile is not reduced to bypass the gate.

Preflight, synthetic transfer, corrected real Dialogue and restart remain
unqualified. A new target/grant is required once measured host capacity supports
the unchanged profile; no blind launch on this consumed target is permitted.

## Post-discovery host gate verification

The new commit helper passes 14 pure/mocked checks centrally (owner 470 ms,
return zero, cleanup known, stderr zero). Independent environment integration
passes all 96 checks (88 retained / 8 new), owner 23515 ms with known cleanup.
The final full suite passes **1057 Python tests in 92.635 s**, owned 94207 ms,
return zero, cleanup known and stderr zero. Its 190190-byte raw output SHA256 is
`5bd884e9f4950df4b167a3fde4a84c4d11721adc97cf5ae13dc4714522115a92`.
The earlier 1035-test run belongs to the pre-guard snapshot and remains evidence.

An explicit later read-only observation succeeds in 157 ms with no OS changes:
commit total 59226001408, limit 72694566912, headroom 13468565504 bytes. The
unchanged 8 GiB profile requires 19327352832 bytes under the conservative policy,
so its assessment is `commit_capacity` refused. That record is an observation,
not a reservation. Raw 283-byte SHA256:
`f13adfeeab8bbe01654477abd37333cda694fa10a59bc53699f974de0e2fbec6`.
Other-project emulator processes are distinct from the closed LocalLore owner.
Permission to interrupt one specifically named emulator is requested separately;
no such process is stopped without a human reply. No task acceptance is inferred.

## Final source and retained evidence

The post-guard host-only freeze contains 64 required source files, eight unchanged
Android compilation bindings and the same audited APK identities. Its 9685-byte
manifest SHA256 is
`9247ae90c7cfbf63f8d2148012d02b954695ee36b4cf9a860d2e059a2aebac5f`;
its explicit scope says `new_emulator_execution=false`. It follows the executed
62-file snapshot and does not relabel that earlier failed startup. Later protocol/
report wording is documentation only; all 112 captured Python sources match.

Private host evidence contains 196 files / 3044530 bytes. Its 32471-byte index
SHA256 is `6c22a8a1ab27414c606ec4ace4df9fbb1e37bfcffa93b5f3c88b4abd622a9e1d`.
Environment evidence contains 29 files / 399645 bytes. Its 3816-byte index SHA256
is `8f7cbbe331a765551611209742a3fe2191ef6ab2efd6475ae3846c9bcf43dac0`.
Independent review verifies all 225 indexed sizes/hashes, both source sets,
host-test logs, owner/guard bindings and the proposal-only preflight namespace.
The raw lease-refusal traceback remains in the task's tool output, outside those
indexes. Environment prepare/run grants existed; preflight/probe grants did not.
The original 1 GiB payload and APKs are outside these indexes; prior independent
APK verification stands. No weights, images, keys or raw diagnostics are uploaded.

# No-model phase evidence on Android, 2026-10-23

Refs #5, M01.03/M01.05. The deterministic phase control passed on one selected
API 35 x86_64 emulator. This qualifies the diagnostic control only. It does not
diagnose the earlier SDK process death, qualify inference, or satisfy the
physical-phone or ARM execution gates.

## Qualified artifact and scope

- Java/integration source: `04326712278eaa0a91073511085c0c97b7375123`.
- APK: 63,666,944 bytes; SHA-256
  `df2b2552fd0ee2de202d19ab5381bf253674f32d4e2ed5b4b2c99a19ae4b3dda`.
- Separate package: `org.locallore.runtimebench.litert.phaseprobe`; sole runner
  `org.locallore.runtimebench.litert.PhaseEvidenceInstrumentation`.
- One fresh install, one deliberate own-process kill, and one fresh reader.
  No model copy, model-content read, SDK generation, native gameplay operation,
  SQLite operation, old-package stop, or emulator lifecycle operation occurred.
- The [phase protocol](SDK_PHASE_PROTOCOL_V1.md) defines the journal, optional
  process-instance correlation and their limits. Journals, identity tokens,
  package data and raw diagnostics remain private.

## Retained attempts

The first cohort stopped before installation. Its caller required the display
mount `/data`, while the fixed `df -k /data` query reported `/data/user/0`.
The observed free space was 1,738,440,704 bytes. This was a host parser failure,
not an established capacity refusal. The same parser failed during final storage
accounting after both devices' preservation checks had completed. Host free-space
values from those failed samples were not retained. The child returned 2, its
wrapper returned 1, and the owned process completed cleanly in 21,031 ms.

A separately reviewed cohort used the unchanged APK and fresh admission. The
[pure storage decoder](../../../benchmarks/android_phase_storage.py) accepts only
the two fixed display aliases. Before using available bytes, the caller compared
dereferenced filesystem device identities from `stat -L` on both fixed paths.
Observed samples were retained before admission decisions. The original failed
cohort was sealed and was not rewritten or executed again.

The corrected cohort completed cleanly in 33,125 ms. The 76-byte crash terminal
matched the exact allowed framing. Independent process absence preceded the
single reader. Its 396-byte terminal passed the strict
[result decoder](../../../benchmarks/android_phase_result.py):

- Valid journal: two checkpoints, last phase `probe_kill`, role `none`.
- Fresh reader process: true.
- Exit history: one examined record and one exact process-instance match.
- Observed reason/status: `2` / `9`; these values do not establish the earlier
  SDK failure's cause.
- `model_execution`: false; journal and control qualification predicates: true.
- Final phase-package process absence: verified.

## Admission and preservation

Installation used a separate 512 MiB allowance, retaining at least 4 GiB host
space, 1 GiB userdata and 10 GiB evidence space. Userdata changed from
1,738,395,648 to 1,674,670,080 bytes. The tiny control used a 64 MiB allowance;
userdata changed from 1,674,485,760 to 1,674,469,376 bytes. Final host/evidence
free space was 8,133,230,592 / 326,254,399,488 bytes.

All 21 prior package identities on the first emulator and all 22 on the second
were preserved; the latter gained only the phase package, for 23 total. Original
model and retained cache metadata matched before and after. No full model hash
was taken in this packet. Final inventory reported four emulators, no other
devices, and both selected emulators ready. Both device leases were released.

The first and corrected cohorts recorded 229 and 322 owned commands. All 551
recorded commands completed with known cleanup; nine exit-1 results were expected
namespace-absence probes. This is scoped evidence about recorded owned commands,
not a claim about every possible host client. The corrected owned driver returned
0 with no stderr, and the primary and cleanup failures were null.

## Verification and private bindings

Actual host checks: 16 result-decoder tests, eight storage-decoder tests, and nine
final private launcher-fence tests passed. The fences cover malformed crash
terminals, unknown cleanup, wrong package identity, stale namespace bindings,
filesystem mismatch and refusal before installation. A preparation-only test
initially imported an old template through a stale test-root constant; its
failure was retained, namespace assertions were added, and all 480 sealed files
of the first cohort were independently rehashed unchanged. No device call came
from that failed host test.

Private evidence excludes weights, images, SQLite payloads and unrelated logs:

| Cohort | Indexed files | Bytes | Index SHA-256 |
| --- | ---: | ---: | --- |
| Pre-install parser failure | 480 | 291,080 | `5b2c493d41f8481931038c063c283b0af871aa003089cef1ad3a1eb3a1bf16f1` |
| Corrected control | 673 | 410,799 | `ca96857de9eef8063cd4d61b303a5982a9c3137126b63dd872559612c5d15a39` |

Sanitized handoff SHA-256 values, respectively:
`d7cb0d662dae67a40e7209e17f238c2361a310dd2684275eaa478154de81a566`
and `87a70522551635e53e1111059d98420ad527a630155a4a2a9c8b591d2f366011`.
The corrected sealed bindings include the exact launcher, owner-barrier driver,
helpers, decoder, storage parser, authorization, artifact identity, raw command
outputs and storage observations.

M01.03/M01.05 acceptance remains pending. The next runnable task is to integrate
these validated checkpoints into a separately authorized SDK diagnostic cohort;
strict Rust replay remains necessary to establish any canonical outcome.

# Record cancellation build verification — 2026-11-03

M10.02 `RECORD_CANCELLATION_UI_BUILD_HANDOFF` is implemented for review;
M09.04/M09.06 device acceptance remains pending. Tickets retain the live plan.

Code commit: `c9de9f852478ceddcd7e566714c709f70c6bcf7f`.
Tested tree: `ff6c2539095a540f872f2827cb2c774d00ee0597`.
The subsequent documentation commit changes no tested executable source.
Tooling parent: PR #384, `b1ba494248bb0d9f55661081ddb27175d1eb3cc9`.
Product dependency: PR #386, `7e29fb724ed781e953f321385f66a5f8982ad0f1`.

## Actual host execution

All captures are under
`D:\Dev\Experiments\LocalLore\2026-11-03-record-cancellation-ui-build-v1`.
`run_owned.py` uses the checked PR #361 host owner, with an unchanged 180-second
ceiling, frozen per-phase workers, D: temporary output and no device dispatch.
The original fourteen cases and two later boundary cases run alongside seventy
existing shared parser/build/audit cases. The suites are:

```
scripts.tests.test_record_cancellation_ui_build
scripts.tests.test_record_cancellation_ui_build_boundary
scripts.tests.test_diagnostic_ui_build
scripts.tests.test_diagnostic_ui_build_files
scripts.tests.test_audit_physical_model_apk
scripts.tests.test_archive_ui_build
```

| Capture | Result | Capture seconds |
| --- | --- | ---: |
| new-v1 | Runner failed before collection; zero tests | — |
| new-v2 | 14 methods; six assertion subfailures in one method, zero errors/skips | 11.319 |
| new-v3 | Original 14 pass, zero failures/errors/skips | 11.138 |
| final-v1 | 84 pass, zero failures/errors/skips | 26.029 |
| final-v2 | 86 unique methods pass, zero failures/errors/skips | 26.049 |
| genuine-v1 | Real-input inspection succeeds; no fixed output written | 4.584 |
| genuine-v2 | Actual CLI create/verify return 0; coordinator writes data manifest | 9.032 |
| genuine-v3 | Actual CLI create/verify return 0; existing manifest revalidated without overwrite | 8.899 |

The new-v1 runner imported unittest.mock/asyncio/ssl after replacing sockets,
causing an SSL subclass TypeError. Preloading those standard libraries fixed
the runner while retaining its process/socket guards. This was not a production
RED result. The actual new-v2 failures showed ordinary runtime exceptions
escaping the public refusal boundary. Production now normalizes them without
returning private text. The original fourteen methods were unchanged through
RED and green: SHA256
`3b69c542d6960b11bde93d5fd7342dc8e3c3fdf5f0964436670fd23fbe1a14da`.

Static review also corrected a worker-stderr filename and the external `None`
guard before the first actual test run. No runtime RED is claimed for those.
The exact runtime-FIRST source was reconstructed and checked against the old
captured source map: 25,038 bytes, SHA256
`8caada143927a44163554a858ffa9e6f9dca50d2d8f3403637e9899399bbca84`.
This is verified source attribution, not an original-mtime claim; the earlier
unrun draft and reconstruction controls are retained separately.

## Attempted-I/O assertions and sensitivity

The original refusal spies proved no successful read, but normalization could
swallow their raised assertions. Two supplemental methods therefore inspect
constructor/loader/read/json/final call counts outside the refusal assertion.
They use synthetic rejected values without reading a foreign file.

Two fixed private mutants establish sensitivity: removing the malformed-role
guard fails the `None` zero-call assertion; moving a read before membership
fails all three foreign-role zero-call assertions. Both mutation captures
record expected rejection, zero errors/skips, and no real foreign I/O.
Production stays unchanged at SHA256
`4f3c04b7f9b781b3ff2650b6ba4416f581dbf9dd95aa3b354d9ec86eab174502`.
Mutation failures are preserved, not counted as passing production tests.

## Real frozen-input verification

The local manifest is 32,140 bytes, SHA256
`4d39b74ad5aee455ce9060c01d760204022101e4b6b8ce58d12f666450d2894e`.
Genuine-v2/v3 CLI create and verify stdout match those exact bytes. It is
nonexecutable data, not run authority. No APK was rebuilt for this packet.

Genuine-v3 guarded reader sessions recorded:

| Session | Guarded bytes | Retained raw bytes | Files | Seconds |
| --- | ---: | ---: | ---: | ---: |
| Create | 201,911,854 | 100,955,927 | 2,686 | 4.353 |
| Preliminary baseline verification | 1,483,364 | 741,682 | 1 | 0.009 |
| Verify | 201,976,134 | 100,988,067 | 2,687 | 4.310 |

These logical counters exclude preflight/OS activity and do not measure process
RSS or provide hard I/O preemption. Final-v2 and genuine-v3 before/after maps
match exactly across all 2,627 tested source files. All 2,623 tooling-base files
are unchanged. Earlier captures honestly retain their smaller source sets.

## Independent review and limits

B72 authored the baseline; B75 authored the original fourteen tests. Root owns
production integration and the two boundary supplements. B72 reviewed actual
source, test assertions, FIRST/green, mutation and genuine-input joins; B75
reviewed production, the real baseline and the supplemental boundary evidence.
Neither reviewer receives independence credit for their own authored artifact.
Their separate sealed JSON reviews are retained with the captures. Review-only
parser setup failures are preserved separately and do not change test results.

The ordinary source/synthetic/control/recovery budget is 256 MiB combined.
Failed captures, frozen workers, drafts, reconstructed attribution and synthetic
fixtures remain retained on D:. There is no compiler or guest output in this
packet. Recovery preservation and publication are separate final checks.

**Qualification:** 86 actual passing Python host methods. The 425 JVM cases in
50 suites are recorded B110 evidence, not rerun here. Five Android methods are
compiled in the frozen test APK; **zero of five executed**. There is no fresh
native/model/device result, full installed-tool fingerprint, or CI claim.
No SDK, ADB, phone, model, ledger, guest, other-emulator, settings or merge
operation occurred. The fixed owner/profile integration is the next host task;
capacity and fresh exact approval still gate any later device execution.

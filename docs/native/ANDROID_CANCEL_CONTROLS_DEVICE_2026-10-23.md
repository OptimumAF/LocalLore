# Android Compose cancellation controls checks

Refs #9 (M05.04 partial), #8 (M04.04 supporting).

The eight frozen Compose methods reproduced five assertion failures on the
baseline and passed all eight methods on the candidate. They render the actual
`LocalLoreScreen`, `ShellViewModel`, `DurableGateway` and platform `JSONObject`
against a controlled synthetic `WorkspaceTransport`. The Compose rule creates
and tears down its generic `ComponentActivity` host. These methods do not launch
the user `MainActivity`, construct `NativeWorkspace`, invoke JNI, open SQLite,
read a save/model or run inference. Packaged native libraries do not establish
native execution.

Only the selected second Android 15/API 35 x86_64 emulator was admitted. Its
observed page size is 4096 bytes. The first emulator remains blocked by its
previously observed storage deficit and was not queried again. Neither a
two-emulator pass nor a physical-phone, ARM64, model-quality or performance gate
is claimed.

## Admission and ownership

The new private namespace copies the preceding reviewed controller and Windows
Job owner with explicit assertions that their output roots name the new
namespace. No preceding sealed evidence is modified. Initial admission requires
the original 23 second-target LocalLore package hashes and the exact preceding
isolated cancellation app/test pair. Baseline and candidate replace only that
isolated pair using `install --no-streaming -r`.

Unchanged admission floors are 4 GiB plus 128 MiB on the host userdata volume,
10 GiB on the private evidence volume, and 1 GiB plus 128 MiB in emulator
userdata. Boot completion, API, ABI, page size and absence of every LocalLore
process namespace are required before installation and at final boundaries.
The fixed `/data` query may display `/data/user/0` only with captured matching
same-device `stat -L` identities. No floor or final absence gate is relaxed.

The selected instrumentation invocation is:

```text
am instrument -w -r -e class org.locallore.app.CancelControlsTest org.locallore.app.cancelack.test/androidx.test.runner.AndroidJUnitRunner
```

The outer Windows Job has a 180-second bound and an stdin-EOF barrier before
dispatch. The instrumentation client has a separately reviewed 90-second bound
and 128-KiB output limit. This accommodates actual Activity/Compose rendering,
scrolling and idling; the preceding non-Activity suite used 45 seconds. The
production inference budgets and capacity floors are unchanged. Individual
clients have fixed deadlines and sticky cleanup state. Raw stdout is flushed
durably before interpretation; stderr byte counts are retained without content.
Unknown cleanup, retention failure or a binding/protocol mismatch stops later
actions. The parser requires all eight exact method identities, sequential
counters, paired starts/terminals, no skips/aborts/unfinished methods, and final
runner completion after every pair. An instrumentation exit code alone does not
establish test success.

## Retained baseline stop and separate cleanup

The baseline completed all eight method pairs: three passed and five failed.
It then stopped at its first after-test process check because the exact isolated
test-package namespace remained present. The outer owner completed in 42,969 ms
with child return code 2 and known Windows Job cleanup. All 27 issued clients
completed with return code zero and known client cleanup. Before/installed
25-package maps matched the original 23 hashes and admitted pair. The original
cohort has no after/final package or capacity qualification and remains stopped.

A separately admitted read-only ownership observation completed ten commands in
2,250 ms. It observed the same surviving test process, whose UID matched the
exact test-package UID, and the exact baseline 25-package map; unchanged floors
passed. Its `dumpsys activity instrumentation` command returned an unsupported
command message, despite client return code zero. That 115-byte result is
retained locally, SHA-256
`e82e59a40f9eebf70399da1de62e0b93031dd6a8f9c32b4adfc84a31f7aa333b`.
It does not prove active-instrumentation absence. No test or inspection command
was retried.

The coordinator then separately admitted one exact owned-test cleanup. The
controller re-parsed all eight terminal pairs and revalidated the original
observed process ID, UID, exact package UID and full baseline package map adjacent
to one fixed `am force-stop org.locallore.app.cancelack.test`. No other package,
process ID or application was stopped. The 26-command cleanup completed in
6,000 ms; every client returned zero with known cleanup. Original after/final
namespace-absence, package-map and capacity gates passed. Final available
userdata was 1,644,228,608 bytes. This separate result does not rewrite the
original stopped cohort or establish natural Android-process exit.

The reason the generic test-host process survived is not established. This is
not evidence of a native/model handle leak, nor a correction or diagnosis of
earlier unrelated graphics failures.

## Candidate result

The independently admitted candidate completed in 53,234 ms with child return
code zero and known Windows Job cleanup. All eight methods passed, with no skip
or unfinished method. Its raw instrumentation transcript is 5,728 bytes,
SHA-256 `eea20d3b8b7633d0295f64325b4e3857c765bc070c3081f22cafc9e95a7bf7d0`.
The baseline transcript is 26,700 bytes, SHA-256
`dcc64674c0e8e7961395e6450342c27337fede2316f488d77a6290ee5e0d5c64`.

| Frozen method | Baseline | Candidate |
|---|---|---|
| Checking cancellation before acknowledgement; competing controls blocked | Failed: opening-progress message | Passed |
| Checking cancellation until accepted snapshot arrives | Failed: opening-progress message | Passed |
| Foreign acknowledgement; original-key recovery click | Failed: saved library enabled | Passed |
| Unfinished acknowledgement; original-key recovery click | Failed: saved library enabled | Passed |
| Incomplete committed acknowledgement; original-key recovery click | Failed: saved library enabled | Passed |
| Committed race displays accepted history | Passed | Passed |
| Late noncooperative preparation cannot replace visible history | Passed | Passed |
| Disposal suppresses late acknowledgement/preparation | Passed | Passed |

Candidate cleanup admission explicitly allows at most one exact test-package
stop, after raw retention and successful parsing of every terminal pair, only
when the sole remaining LocalLore process is that test package with the expected
UID and exact candidate 25-package map. A missing process skips that action;
another process, UID or map stops the cohort. The actual candidate performed
one such test-package stop. All 46 clients completed zero with known cleanup.
Original after/final namespace-absence gates, all four 25-package maps and all
capacity checks passed; all 23 original package hashes were preserved. Final
available userdata was 1,644,175,360 bytes, above the unchanged
1,207,959,552-byte floor.

The candidate therefore supplies actual rendered Compose/callback integration
evidence with explicitly owned test-host cleanup. It does not qualify natural
test-process exit, native resource ownership or canonical engine replay.

## Exact artifacts and source

| Artifact | Baseline bytes / SHA-256 | Candidate bytes / SHA-256 |
|---|---|---|
| Isolated app APK | 22,524,394 / `d8b82930934304a3352b8cbab415c69b490fafa189364815d71e6d88382fc94d` | 22,479,391 / `fc01b1ce8516b499d5ca47c518176cba1a93ba4350c2e27d1a14f7ec99950e40` |
| Isolated test APK | 2,327,862 / `a0f5b338ff292e05717910d4df63df95cff62940aa94b2bf71a5950aa138d5f0` | 2,327,834 / `001edf660218539da70df7e222218d816f3ef8072c5cfe034539620347020740` |

The original frozen test source is 17,810 bytes, SHA-256
`8f4b902dc6214f810d9919a1a377a9b49c8e8f89f6a50f14f1f824eee03e05a8`.
The candidate source removes one extra final blank line: 17,809 bytes, SHA-256
`05db4e41f6eeb60d0a9e209c81531b625551d542421cbbea03d18f0c32d1c494`.
Assertions and method identities are unchanged. The test APKs differ; the added
Kotlin state field also changes generated constructor/copy ABI. Each exact pair
and its separate source/audit bindings were reviewed before dispatch. No
byte-identity assertion is substituted for those bindings.

Twenty pure controller fixtures, eight new ownership-observation fixtures and
fourteen new exact-cleanup/control-flow fixtures passed: 42 distinct host
fixtures. They cover framing, terminal ordering, storage aliases, install forms,
package maps, raw retention, sticky unknown cleanup, wrong process/UID/package/
hash refusal, absent-host skip and no retry after a failed stop. These mocks do
not replace device execution. A local cleanup-audit revision replaced an
over-permissive default with mandatory storage-field checks; both audit versions
are retained, and the strengthened check passed without another device call.

Across the stopped baseline, read-only observation, separate cleanup and
candidate, all 109 issued client stdout records were rehashed with zero
mismatches and known client cleanup. The unsupported system inspection result
and original stopped baseline remain explicit exceptions to semantic success.
The closed private selection contains 327 files / 457,715 bytes. Its 55,854-byte
index has SHA-256
`f5d99fb0dad7cef4a567ed6f5514792160b4e745acea35d15313b8cf77a60376`.
All 224 files in the preceding sealed presentation selection were also rehashed
with zero mismatches; they were not modified.
All device calls are stopped and all dispatch leases released. Raw diagnostics,
APKs, process identities and private paths remain local. No screenshot, model
operation, user-save access, external emulator relaunch/reset, clear-data,
uninstall or user-application force-stop occurred.

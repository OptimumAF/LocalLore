# Explicit SDK3 bridge: host checks and refused live admission

M10.02 supporting M09.06/M01.01. Implementation is proposed for review; full
milestone criteria and owner acceptance remain required. The runtime gate is
blocked. This report records host implementation and one failed pre-command
proof, with no Android/model result.

## Implementation and interfaces

Executed public checkpoint is `5a43640cf890d4a3b2220ae21c00c4f8b1963dbc`, based
on open/unmerged PR #248 at `7f7eed72`. Later documentation commits have separate
attribution. See the [SDK3 contract](ANDROID_SDK3_CONTRACT_V1.md).

The new `android_process_client_v3.HeldServerSdkCapture` explicitly selects
`sdk-held-server-v3`. It binds the actual caller, source/tool/interpreter pins,
one immutable target and finite deadline. Fresh owned held-server proofs precede
and follow each actual SDK command. Refused pre-proofs retain evidence and close
the session before dispatch. Actual command measurements/raw bytes remain
distinct from the final `client_qualified` flag; later failures cannot turn a
measured command into an invented successful or spawn-failed result.

The new `android_process_verification_v3` acquires and replays the complete
19-file nested owner/worker bundle. It checks exact source, admission, context,
raw-output and file rosters. Parent runtimes must additionally bind actual
workers and phase commands; a saved JSON receipt does not authenticate itself.
Host-only checks use their own explicit reader, with no fabricated SDK row.
External binary streaming requires paired proof references plus its separate
actual child/source-FD/destination/hash/cleanup validation. Full-budget JUnit
dispatch refuses if the complete requested time is unavailable after pre-proof.

Legacy SDK2/default observers, held-v1 rules, historical validators, captures and
tests are unchanged. Rust/Kotlin/SQL application code and all runtime/model
dependencies are unchanged. Gameplay remains local and Rust remains the sole
gameplay authority; this host harness does not change canonical events.

## Executed host checks

All commands ran from physical
`D:/Dev/Worktrees/LocalLore/LocalLore-starter-native`, with process-local TEMP,
TMP and TMPDIR at `D:/Dev/_Temp`. Installed Python is 3.14.7; helpers use
`python.exe -I -S -B`. No third-party dependency was added.

Private experiment root, abbreviated B below:
`D:/Dev/Experiments/LocalLore/2026-10-28-sdk3-author-bridge-v1`.

Root executed `B/check-integrated-v1.py`. Its bounded worker loads these exact
modules through `unittest`:

```text
scripts.tests.test_android_process_client_v3
scripts.tests.test_android_process_verification_v3
scripts.tests.test_adb_held_socket
scripts.tests.test_adb_held_socket_windows
scripts.tests.test_adb_held_socket_probe
scripts.tests.test_windows_tcp_control
scripts.tests.test_windows_tcp_observation
scripts.tests.test_android_process_client
scripts.tests.test_android_process_verification
scripts.tests.test_android_external_controller
```

**307 tests pass, zero failures/errors/skips.** Owner elapsed 34,185 ms; child0,
cleanup/capture true, stderr0 and stdout 59,843 bytes. All 22 selected critical
source/test hashes match before/after. This is a selected source closure, not a
claim that every repository file was tested. SDK/target operations are mocked;
legacy process-driver tests include actual owned Windows binary subprocesses.
Result SHA256:
`f5adc9186751ac44e8bdc48d9d6c1f4b450b80187aff4fde666177a9a51b95da`.

The 307 include 32 new client tests and 34 new reader tests. Original retained
client REDs exposed mutable proof contexts/runner argv and deadline extension;
the unchanged stronger expectations pass after fixes. The first24-test cohort
retains three assertion failures, then one remaining failure, then a pass;
the expanded32 also pass. The reader's original complete19-file synthetic
fixtures expose three assertion failures for missing source-roster/admission
checks; the same12 pass after correction, then expanded34 pass. These are
original synthetic fixtures and mock acquisition, not live proof successes.
Failures are retained separately rather than added to the final passing count.

Separate D: worktrees/branches own client, adversaries and runtime ports, with
Root integrating contracts and execution. The Native agent's partial private
drafts are preserved before explicit reassignment to the Android agent after
agent capacity failures; no completed independent Native review is claimed.

## Source-only private runtime ports

Eight new scripts cover machine admission, boot, build, diagnostic CLI build,
runtime/stream/JUnit, closure, postflight and evidence-derived admissions. They
select SDK3 explicitly and use the exact previously authorized guest root:
`D:/Dev/Experiments/LocalLore/2026-10-28-author-player-contract-v1/avd-v1`.
Scripts, generated admissions and outputs remain under B. No new authorization
is synthesized, and no existing emulator is selected or modified.

The final private cohort passes **18 tests, zero failures/errors/skips**, owner
514 ms/child0/cleanup and capture true. Unittest's 3,230 stderr bytes are retained;
they are ordinary test output, not silently treated as absent. Nine tested
source files are unchanged. Tests execute isolated function definitions with
synthetic files and mocked dependencies, plus AST/symbol checks. They do not run
the production entry points, Gradle, SDK, native model CLI or an Android target.
Result SHA256:
`c8e07dc6b20c102adaa38341f5d1a5ebd8b38019cdcf6b764d716f8716cf840f`.

The initial16-test run contains one false-positive test string predicate:
`.decode` also matched the allowed typed `batch.decode` metadata parser. Its
failed capture and hash-exact recovered original test source remain retained.
The corrected AST predicate permits only that named parser while still refusing
text-mode model transfer. This correction is separate from production fixes.
Initial unexecuted drafts/index are also preserved. Final10-file source/review
index SHA256 is
`8d588aac7f0bf44e2a696252f1c458ca325452eacdf41a60b4701a93550860bb`.
Actual wrapper integration, fresh Android build/admission, transfer, import,
AUTHOR, restart and guest closure are **unrun** for this checkpoint.

## One actual discovery attempt: failed before SDK dispatch

Root executed `B/discovery-sdk3-v1.py` exactly once after the 307 tests. The worker
planned only fixed `adb -H 127.0.0.1 -P 5037 devices -l`; it never reached that
dispatch. In `discovery-v1/session/server-proofs-v3/command-0001-before`, the
held-v1 pre-send snapshot has one exact admitted server reverse tuple with
**raw state0**, and one reciprocal caller tuple with raw state5. The raw IPv4
rows retain 24-byte ABI layout and their exact state bytes. Held-v1 requires
server ESTABLISHED5, so ownership refuses before sending `host:version`.

The report has `request_sent=false`, no response, ownership false and both
backend resource-close flags true. Both proof owners terminate/capture cleanly;
the external CLI exits1 in 768 ms. The outer discovery worker exits1 in 1,727 ms,
cleanup/capture true, stdout0/stderr1,015 bytes, selected sources unchanged. The
session has no command JSON/raw pair; the only proof manifest is verified=false.
Thus **zero SDK commands, zero targeted device commands, zero model operations
and zero emulator operations** occurred in this attempt. The observer did open
and close its own host socket; no service lifecycle operation occurred.

| Preserved result | SHA256 |
| --- | --- |
| Discovery result | `59286f49951a00b70ca36e3bab2ab96eb3a1599067a0ee648d559784039b7d4a` |
| Refused held report | `2184338d19d7e7e90a54918c92b1053c94ab9467e2c9701dd1c218847b5a4d20` |

Microsoft documents [ESTABLISHED as5 and the OWNER_PID ABI](https://learn.microsoft.com/en-us/windows/win32/api/tcpmib/ns-tcpmib-mib_tcprow_owner_pid).
There is no documented basis here for relabeling state0 as5. This capture does
not establish why the provider returned0. The earlier PR #248 host query really
observed server5 and keeps that narrower original attribution; it does not
guarantee every subsequent observation. No repeat capture, favorable polling,
state normalization, relaxed gate or failed-result reclassification occurred.

An independent closed audit verifies all four selected IPv4 rows (one initial,
three pre-send), raw hashes and 24-byte ABI by a separate `<6I` decode and the
public pure decoder. Tuple/PID/scope/endpoint joins match; the pure ownership
join refuses the server0 row. No decoder correction is supported by these
bytes. The report's `client_raw_state=null` is correct because that assignment
occurs only after the complete join succeeds; client5 remains in the raw stage.
The inner worker exits0 in 363 ms, recording a refused protocol result; that
exit does not qualify the proof. Independent audit SHA256:
`179656373ec8726be60b28d8d5038239107276a88e5bf9064cecbd159ce4bf0b`.
This audit performs no new native/service/SDK call and does not re-observe
installed binaries. It is a new report outside the earlier616-file seal.

## Preservation and next gate

The create-only D: recovery snapshot binds executed public HEAD5a43640c and 616
finite original/copy files, including failed/corrected tests, original drafts,
source copies, private ports and the refused live attempt. Its618-member ZIP
includes that index and exact public source ZIP. Model weights, saves, real APKs,
caches, credentials and emulator state are excluded; tiny synthetic APK/XML and
UNLISTED negative fixtures retain their explicit test attribution. Historical
recovery remains untouched. Public documentation committed after this snapshot
is separately preserved by Git and does not pretend to be inside its source ZIP.

Recovery root: `D:/Dev/Archives/LocalLore/2026-10-29-sdk3-bridge-v1`.

| Artifact | Bytes | SHA256 |
| --- | ---: | --- |
| Index | 513,488 | `32ad069c38cfc254b58a4226eac5b00263bdd58cc5b82b2a1451fdc30994c594` |
| Evidence ZIP | 8,827,723 | `a33fe991094968850ac7fa849353efbf0dd5a37974fe41077a2ad923202ae574` |
| Source ZIP | 8,674,754 | `88766f98a2d17781f95217cb53ebed6906b10a663778492ad72bf4500fd2816d` |
| Producer result | 745 | `93cc9fb471594039006b0e3999925d1b8c9d964fb23d18fdb74cbd5faf25f14b` |

Producer v3 actually exits0 after two pre-destination refusals. Those first two
helpers omitted original synthetic XML/APK and UNLISTED fixtures from their
allowlist; their exact sources and explicitly labeled tool-output transcriptions
are included. No raw capture is invented for those tool outputs. V3 preserves
the full finite selection and verifies original/copy/ZIP bytes plus source Git
blob hashes. This is preservation evidence, not another test or service attempt.

Independent V2 readback actually exits0 in 28,362 ms. It verifies all616
original/copy pairs (1,045,751 evidence bytes), exact618 ZIP members, all2,039
source Git blob hashes and237 source directory entries, the four admitted
archive/control digests, final private source/result bindings, selected public
test receipts and the failed live proof/known owners. It uses one Git tree read
and no test/probe/SDK/build/service/device/model execution. Result3,837 bytes/
SHA256 `c734f658e2907eae01af3d12c46ec4f647b4c8218ae2e76bc33c278edf10bf2f`;
verifier16,619 bytes/SHA256
`e7e0066a8bc37db0d2fb2b1d3a65d20d8735931cebded225a4c421fdcb51518b`.

The first verifier incorrectly required ordinal sorting that the index format
did not promise. Its unchanged executed source and explicitly labeled failure
transcription remain bound by V2. Removing only that additional ordering
assertion retains exact unique rosters and every byte/hash check. V2 also records
that historical expanded client32 uses an earlier reader-source pin; final307
and final reader34 match the executed source ZIP. The earlier32 result keeps
its actual source attribution. Empty clients is verified in the original;
the evidence ZIP preserves the finite file roster, not empty directories.

The five later audit/verifier/result files and their separate copy helper are
retained at `D:/Dev/Archives/LocalLore/2026-10-29-sdk3-bridge-readback-v1` without
altering the earlier seal. Root's create-only producer actually exits0 and checks
all six original/copy files plus the exact seven-member ZIP. Supplement index
2,860 bytes/SHA256
`f1a6ce4f72f10d583a8e1c0392d1bccdfa43018358f20c45cdf6870654a91241`;
ZIP21,303 bytes/SHA256
`93729522bb50899b9a44bc7334d1f24a1c5507a3f94fc83fc6705d788eaaa0aa`.
This later small supplement has Root copy/readback verification; do not extend
the independent616-file result to it or call integrity hashes authentication.

Plan discovery: source/tested SDK3 integration is now available, but reliable
current service admission remains unproven. Preserve IDs M10.02/M09.06/M01.01 and
the full gates. The closed-capture review is complete and supports the refusal.
Next runnable work is a separately specified controlled provider-state diagnostic
using authoritative OS evidence; retain the current refusal. Any replacement
protocol requires an explicit decision and independent negative tests, not a
hidden fallback. After admission
is trustworthy, freeze sources and perform a **fresh** full offline Android/JVM/
lint/audit/build and native CLI admission before consuming the existing fresh-D
8GiB/four-core/30-minute approval for import, one AUTHOR and inference-free reopen.

No other emulator stop, system-setting or global service change, model download,
private upload, merge or release occurred. The authorized fresh guest setup
remains unused. Phone availability/identity was not re-observed; no phone absence,
ARM64, model quality, performance, Android cancellation/restart or full milestone
acceptance is claimed.

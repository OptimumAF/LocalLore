# Isolated ADB lease verification — 2026-10-29

Refs #14 (M10.02 support), #13 (M09.06 support), #5 (M01.01 support).
Draft PR #252 is stacked on open/unmerged #250 (`3b8068e8`). Supporting source
is **in_review**, not accepted milestone completion. Checkboxes stay unchanged.

The new host-only owner starts a separate foreground ADB child on unused
loopback15937 with USB, emulator scanning and mDNS disabled in its environment.
The corrected v2 lease passes one actual finite readiness/stop run. Its closed
descriptor does not authorize another connection or any device/model action.
Existing shared5037 and other emulators are untouched. No emulator was booted,
target command dispatched, model copied/imported/loaded, or physical phone
availability established in this packet.

## Implementation and tests

`isolated_adb_lease.py` owns strict typed admission, child environment, scoped
raw observations and closed proof/result replay. `isolated_adb_owner.py` owns the
finite job-contained worker, existing-key metadata lock, unused-port bind,
foreground child, two held-socket exchanges and explicit cleanup. Imports start
nothing. Root owns contracts/integration; separate D worktrees own the owner,
original adversaries and independent official-source/closed evidence review.

The worker waits for both the binary barrier and a complete actual identity
receipt before auth/port/startup. Pending-file/create-only Windows rename avoids
partial receipt reads. A separate supervisor output directory prevents legacy
stop-file parsing from racing the isolated worker. Credential report references
are rejected before byte access. Existing auth contents are never read, hashed
or copied by the harness; ADB's own normal read-only load is admitted separately.
Uncertain close attempts stay poisoned and are never retried by numeric value.
Capture qualification requires bound raw files and actual counts, not booleans.

| Actual check | Result |
| --- | --- |
| Original contract/row adversaries | Initial33 has2 assertion failures (DOS alias and duplicate history tuple), then the same33 pass after fixes. Expanded46 pass. |
| Owner fault tests | Original55 has2 assertion failures for uncertain-handle reclose; identical assertions pass after the fix,567ms, child0, known capture/cleanup,11 selected pins stable. |
| Integrated v1 regression |410 pass,0 failures/errors/skips;27440ms owner, child0,79973 stdout bytes,0 stderr, capture/cleanup true,28 source/test pins stable. Executed source `4461196c`. |
| Complete closed proof fixtures |66 pass,3902ms owner; original bound request/auth/table/socket/history/capture graphs, altered bytes and identities refuse. |
| Parent/exchange checks | Final76 pass in Root5210ms, child0, known capture/cleanup,28 pins stable at `87508ba8`. Partial sends, fragmented exact EOF, empty devices/history, malformed/extra/truncated/FAIL/timeout replies, source changes and cleanup poison exercised through mocked seams. |
| V2 compatibility checks |77 pass in Root4708ms, child0,15250 stdout bytes,0 stderr, capture/cleanup true,28 pins stable at `8efbb805497178b11be4a1570d35041f42f70900`. Includes refusal of v1 admission, command, stop and running metadata. |

The first76 run has one failure and one error caused by test seams: an unmocked
path-existence check and an expectation of allocated sockets before allocation.
It remains separate from the corrected fixture cohort; no production RED/GREEN
claim is made for those fixture corrections. A later shell-quoted private driver
preparation failed with SyntaxError before evaluation; its labeled transcription
is retained, and a separate driver generator fixes quoting. Executed drivers and
their original byte bindings remain preserved.

V2 changes only the protocol tag and supported listener spelling. All25 source
and test bindings for the previous355 regressions remain identical; the final77
focused tests cover the changed new contracts/owner. They are not reported as a
fresh full-workspace Rust, Android, UI or device run. No runtime dependency,
SDK, model, license or global tool setting is changed.

## Installed tool and official compatibility

Exactly two offline installed CLI calls (`version`, `help`) complete39/35ms with
child0, known cleanup and no stderr; no server request occurs. Installed ADB is
1.0.41 /37.0.1-15733141,8273560B, SHA256
`b4a6b455702684652cccf7b46258b29e653538904359a58fd4931cf3ef286b3f`.
All six installed tool/DLL/metadata bindings and the actual Python executable/
runtime DLL are revalidated. Matching binary guard literals are corroboration,
not proof of behavior or exact installed-source provenance.

[Official release notes](https://developer.android.com/tools/releases/platform-tools)
describe the changed Windows USB backend. The retained primary AOSP sources at
`1cf2f017d312f73b3dc53bda85ef2610e35a80e9` and
`9084198a2d4b0f6a0f174260fb42da33485b684d` support direct
ADB_USB/ADB_EMU/ADB_MDNS startup exclusions and the foreground native listener.
Bogus USB selectors, old backend defaults and auto-connect controls alone are
not substituted for those guards. Existing Windows native-profile authentication
is locked by metadata/read sharing, without generating or moving a key.

## Original failed v1 and corrected live v2

The frozen [v1 protocol](ISOLATED_ADB_LEASE_PROTOCOL_V1.md), source `87508ba8`,
used numeric `tcp:127.0.0.1:15937`. Its unused-port/exclusive bind passes with
socket masks1/1/1; seven readiness snapshots are empty. The actual child exits
3221226505 with153 stderr bytes reporting unsupported hostname listening. No
smart-socket frame is sent. The parent closes4664ms with worker1; the worker
records identity refusal after the child exits, all acquired resource closures,
complete capture, and no terminate attempt because it already exited. This
failed run and its original source/admission are retained unchanged.

The initial review covered command parsing but missed the native listen path.
The independent correction and [v2 protocol](ISOLATED_ADB_LEASE_PROTOCOL_V2.md)
explain why literal `tcp:localhost:15937` selects Windows AF_INET/INADDR_LOOPBACK
directly without DNS. V2 does not relax IPv4 ownership, admit extra IPv6 rows,
normalize state DWORDs or reinterpret any failed v1/SDK3 evidence.

One new v2 admission at source `8efbb805` selects a fresh output root and60-second
ceiling. Admission SHA256:
`2c1df19b6cd04620867a9d661eec9c17ffe7b81b338de7a616ce4814254fe313`.
The unused-port gate passes; the first readiness snapshot identifies only its
actual owned child. Exact exchanges:

- `000Chost:version` → `OKAY00040029` plus EOF,1288ms.
- `000Ehost:devices-l` → `OKAY0000` plus EOF,1318ms.

Both preserve the same held socket/process brackets and pass source/auth/tuple
checks; prior teardown history is derived from the first closed proof. Raw state
DWORDs stay opaque (version snapshot0/5/2; second11/0/5/5 including prior history).
They are not universal TCP-state or reliability claims.

Root revalidates sources and all three live process identities/deadline before
atomically publishing the admission-bound stop. Worker closes38741ms; parent
closes39166ms with child0,0/0 output bytes and complete cleanup/capture. All nine
worker cleanup fields are true. Actual server termination returns1; no exit0 is
invented. Both server raw streams are empty and independently byte-bound. Result
SHA256 `6953986bd489354d3a9a1b5cf26fb2c837c0f51030711f4690d80027f2f6e6da`;
`qualified_lease:true`, `reason:stop_requested`, `feature_acceptance:false`.
Saved readiness is historical after this known closure.

Independent closed replay verifies40 reachable file bindings twice, ten exact
Git source pins plus the frozen test, installed tools/Python, scoped raw row
decoding, request/started/running/after/stop joins and actual capture bytes.
It makes no new native/process/key/service query. Its failures list is empty;
audit SHA256 `289201829437aa2c2b266fa423a5142a6538468bb4681297dc84a303442ed712`.

## Reproduction, recovery and limits

Run from a physical D checkout, with process-local TEMP/TMP/TMPDIR set to
`D:\Dev\_Temp`. The public mocked checks are:

```powershell
python -B -m unittest scripts.tests.test_isolated_adb_lease
```

Live startup is explicit through `isolated_adb_owner.py --admission <D-json>
--admission-sha256 <digest>`, after current authorization, official compatibility,
original tests and fresh byte/profile/port gates. This is not a general server
recovery command. Private finite drivers use installed Python with `-I -S -B`,
the existing binary/job supervisor and source-bound requests/results. Raw local
diagnostics, native profile metadata, model weights and saves are not uploaded.

Before startup,105 selected originals/copies/ZIP members are independently
verified, together with2049 source blobs/238 directories at `b03c34f8`. Readback
SHA256 `0711da0740fa2acbd358ef478b26cfac9f38f23483ce5a758209ec92973ad19f`.
After the failed first attempt,148 files and exact source `87508ba8` have a separate
verified D recovery set; index SHA256
`5fcf61199d2355edd5ee0dcdcf8f045a824225eee456d49e5649cc9b0e411cc9`.
These are bounded checkpoints, not claims to preserve all ignored historical
workspaces, global caches or OS-managed data.

Final D recovery independently verifies all195 original/copy/ZIP triples and
exact file/directory rosters, plus2051 Git blobs/238 directories at documentation
checkpoint `42eb1a34`. Each source ZIP file is compared directly with its Git
blob. Earlier checkpoints remain untouched. Final index SHA256
`f7dce9cd1d5464e4f8c8f49365c3e164ba85ebd6b6e9cfc7e19b174d64a7f0e7`;
packet ZIP `67ec471a4aaa742cec40439b38a7bd240f28706ea989780fa70d66be4385ce17`;
source ZIP `60fe18352423e19ee9e31927bc6db3da8df6413b916865a20b0bee4aa9fc7d12`;
independent readback
`a445fc131704a40cf9a3b28a93e909257998559af181be0410f3844b9c15d6a3`.
This later public seal paragraph is preserved by the subsequent Git commit,
not retroactively inserted into that frozen source ZIP.

The empty devices reply qualifies only that observation. Exact installed source
provenance, universal absence of transport side effects and every inherited
legacy helper's temporary native handle closure are not proven. No physical
phone, model quality, ARM64, inference performance, cancellation during inference,
restart journey, accessibility or release acceptance follows from this host run.
The original model name rejection remains failed and unchanged.

**Next runnable task:** M10.02/M09.06 a separately versioned target-specific SDK
and lease integration built on these owned mechanisms, with explicit target
admission and no automatic/shared-server recovery; then
current-source Android build/admission and the already authorized exact D8GiB/
four-core/1800-second fresh guest, isolated app/local model import, one AUTHOR
attempt and inference-free reopen. Do not reuse this closed descriptor or boot
before the target integration is tested. M09.06/M01.01 runtime gates remain
blocked by that integration; existing guest approval remains unused. No merge,
release, system settings change or unrelated-emulator stop occurred.

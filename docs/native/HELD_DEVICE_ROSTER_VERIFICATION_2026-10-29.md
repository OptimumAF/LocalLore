# Held device roster verification — 2026-10-29

Refs #5 (M01.01, supporting M01.05); Refs #14 (M10.03).
This host-only prerequisite is locally verified and in review in draft
[PR #277](https://github.com/OptimumAF/LocalLore/pull/277). Full milestone
criteria remain unchecked. No phone, emulator, model or release is qualified.

## Change and boundary

The ordinary ADB client can restart a mismatched existing service. The new
explicit Python client instead sends only fixed `host:version` and
`host:devices-l` requests through held, ownership-checked loopback sockets.
It never executes ADB, selects a device, sends a device command or changes
service lifecycle. Private roster strings remain untrusted data; an observed
model name cannot substitute for the retained authorized phone identity.

The [protocol](HELD_DEVICE_ROSTER_PROTOCOL_V1.md) specifies exact admission,
source/runtime/worker ownership, framing and parser limits, bounded raw-byte
retention, privacy and cleanup. Three new production modules and four original
test modules implement this boundary using existing Python/Windows facilities.
There are no dependency, Android, Rust, model, SDK or product-policy changes.
Existing ownership modules and legacy collectors are byte-unchanged.

Source baseline is `328eefe563c7c21d27c40256513bed3bd08d15e2`.
The first actual capture is frozen at
`d7b1b0500e6484382e607915025c086365431961`; the revised tested/acquired source
is `4e9c032d763ff7c5e4619d81263f9844a78dc5e2`. Subsequent changes to this
report do not change the attribution of either execution.

## Failures preserved and repair

The original host tests exposed strict counter-type acceptance, lost bytes on
post-receive deadline refusal, unrelated TCP rows in serialized reports, a
missing transitive source binding, absent version sidecars and sidecar mismatch
acceptance. Each original failed capture remains preserved. The fixes retain
actual received bytes before post-read guards and still refuse expired or
otherwise invalid observations. The original version verdict is unchanged.

The first actual host capture completed its version request but refused the
roster's initial candidate snapshot before sending the roster request. It
retained a PID0/raw-state11 row with the exact reverse endpoint of its completed
version connection. The original postflight also refused; it is not presented
as complete acquisition. Its outer owner returned 1 after 6,564 ms with known
cleanup and complete output capture. That result remains failed at frozen
source, without a retry or favorable-state polling.

Five new original history tests first reproduced four positive-phase failures.
The repair derives only the exact completed version tuple from its positively
qualified, EOF-complete, closed proof. At most one matching PID0/raw-state11 row
is treated as history for candidate validation; raw rows stay recorded. The
live ownership join still consumes the original rows and requires a unique
admitted-server ESTABLISHED5 reverse connection and reciprocal current client.
Unknown tuples, duplicate history, wrong PID/state/family/scope and orphaned
live connections refuse. Postflight may additionally derive the endpoint of a
qualified closed roster proof containing the identical version witness.
No arbitrary ignored-port list or general PID0 exemption is accepted.

Those same five tests passed after the fix. Four additional direct API tests
passed, including separately valid but mismatched version proofs and endpoint
deduplication. The first capture was neither edited nor reclassified.

## Verification actually performed

All commands ran from physical D: worktrees with process-local
`TEMP`, `TMP` and `TMPDIR` set to `D:\Dev\_Temp`. Private captures and scripts
remain outside Git under
`D:\Dev\Experiments\LocalLore\2026-10-29-held-phone-roster-v1`.
They are not uploaded with this report.
The local interpreter is Python 3.14.7 on Windows; execution records bind its
executable and runtime DLL rather than relying on the version label alone.

| Procedure | Actual result | Evidence |
|---|---|---|
| Original focused parser/CLI/backend tests | 48 methods pass after preserving the original failures | `adversaries/combined-green-v1/result-v1.json` (29) and `backend/final19-v1/result-v1.json` (19) |
| New completed-history tests | Same original five pass; expanded nine pass | `adversaries/history-first-v1`, `history-green-v1`, `history-api-v1` |
| Full host discovery on first source | 2,340 pass, zero failures/errors/skips | `full-host-v1/result-v1.json`; 259,162 ms outer owner, return 0 |
| Full host discovery on revised source | **2,349 pass**, zero failures/errors/skips or expected failures; 127 modules imported before execution | `full-host-v2/result-v1.json`; 256,616 ms outer owner, return 0; all 2,280 source bindings stable |
| Runtime-spike regression on first source | 16 pass; 10,606 ms outer owner, return 0 | `runtime-spike-v1/result-v1.json` |
| Runtime-spike closure comparison | Its two-file source closure is byte-identical in revised source | Prior execution retains its original source attribution; no repeat or new runtime execution claimed |
| First actual existing-service host acquisition | Refused candidates, zero roster bytes and no roster request sent; version verified | `live-host-v1/capture-v1/result-v1.json`, frozen first source |
| Distinct revised-source host acquisition, one attempt | **Observed, zero roster entries**; both fixed requests sent once, ownership/framing qualified and resources closed | `live-host-v2/capture-v2/result-v1.json`, revised source |

The finite full-suite wrapper ran:

```text
python -I -S -B D:/Dev/Experiments/LocalLore/2026-10-29-held-phone-roster-v1/check-full-host-v2.py full full-host-v2 4e9c032d763ff7c5e4619d81263f9844a78dc5e2 600
```

It discovers the complete `scripts/tests` suite without exclusions. Normal
repository entry points are documented in the protocol; the private wrapper
adds finite ownership, captured output and before/after source pins.

The new-source actual host command was:

```text
python -I -S -B D:/Dev/Experiments/LocalLore/2026-10-29-held-phone-roster-v1/live-host-v2/run-existing-roster-v3.py
```

This one-shot helper has fixed 90-second outer, 45-second CLI-parent,
30-second public-worker and three-second exchange limits. It reads the
installed executable in place for identity/hash checks and never executes it.
Expected host protocol version `0029` was fixed before acquisition. The
actual outer owner returned 0 after 6,434 ms with zero stdout/stderr and known
cleanup/output capture. Version and roster exchanges each took 83 ms and
retained 12 and 8 bytes respectively; the roster body was empty. Both proofs
retained the required server ownership, raw client state5, EOF and closure.
The public worker completed in 467 ms with return 0 and empty streams; its CLI
parent completed in 821 ms with return 0, 141 bytes of redacted output and zero
stderr. Before/after service, executable, candidates, source and runtime pins
stayed equal. No device identifiers or target metadata were returned.

Selected SHA-256 receipt bindings:

| Private artifact | SHA-256 |
|---|---|
| Full revised suite result | `7feece4e867851a0bc9d75fad028035217ad11af2aa057e4820db0f5cf15f7b8` |
| Full revised suite helper | `2a47b95e662d2a1cae0df472f93b9acdb75a57213caf4cecb052efcc7eed75a9` |
| Original failed actual result | `f7e823c8a515b0d229713a65ce68d2fbbeb16826e8d083825a67699089e1467a` |
| Revised actual result | `dd69143cf8ba75bff6ff15841361f58fde5a4d659cc3ec453aa623753bfcfd21` |
| Revised one-shot helper | `a98d9f6b54abb8ee4bac5c947148bf985df749478cada6d2cef0e8a2277221d2` |
| Revised fixed recipe | `bdc32f7f10c303521bff3e21ea36f6fced014eacfc640052c22791ec57e511ea` |

## Independent replay and preservation

A separate reviewer replayed only closed files, using the real pure proof,
serialization, history and worker-binding checks. All 33 capture files and
2,280 executed source bindings matched. The changed documentation README was
checked against the exact raw-byte-matching frozen first-source copy; current
documentation was not relabeled as executed source. All three owner/stream
records, the parent/request/started chain, empty response, two completed
history tuples and cleanup matched. This file-only audit made no new native,
socket, SDK, device or model calls. Its receipt SHA-256 is
`9d984f22f94e5a3507d5b55ca0934fde88f2c13c4741cab4565127d7f630ac13`.

The reviewer's first receipt helper had a duplicate keyword and failed to
compile before any behavioral check ran. Its original source and stderr are
preserved. A distinct helper fixed only that summary key and output names,
passed a complete compile check and completed the closed-file replay once.
This preparation failure is separate from product and acquisition results.

The first recovery seal under
`D:\Dev\Recovery\LocalLore\2026-10-29-held-phone-roster-v1` preserves eight
actual source worktrees and the closed experiment packet: 18,489 files,
276,626,859 bytes per original/copy set, with original-before/copy/original-after
hashes matching and zero missing, unsafe or mismatched entries. Git pointer
files are metadata only; source snapshots retain their actual branch/head and
dirty-documentation mappings. Frozen failures and unexecuted drafts remain
distinct. Model, credential, key, APK and guest-image contents are excluded.
Originals remain in place.

The 15,019,623-byte recovery manifest has SHA-256
`c7f4ac757083e3f9abb95df4e87ffe4c02bd025946f1f9f0605cc5cff6ad4ba7`.
Independent readback then verified every listed original and copied file,
the exact copy roster and the explicit executed-source README mapping, with
zero missing/mismatched/unsafe entries. It returned 0 after 57,966 ms; receipt
SHA-256 is
`94bfa752b30c1c146209208bc54daccd6fb7cf661a14ffd979369fa8ea01f556`.

At this seal, the eight worktrees plus experiment/recovery roots occupied
568,310,374 logical file bytes. Conservative accounting including manifest and
final-supplement reservations is 588,942,335 bytes, below the declared 1 GiB
packet cap. This is scoped logical-byte accounting, not disk free-space gain
or peak storage measurement. Closed review receipts and final documentation
are preserved in a separate bounded supplement after this seal; its final
receipt belongs in the ticket handoff, without changing this manifest.

## Source compatibility and limits

Independent review used pinned primary AOSP sources linked in the protocol,
including the wire services, long-list formatting, state names and separate
ordinary-client restart logic. Microsoft native table definitions identify
raw state11 as TIME_WAIT and state5 as ESTABLISHED. They do not establish that
every PID0 row is safe history. The exception here depends on the exact
completed proof, with no OS-state normalization or universal causal claim.
Source review does not attest the installed binary or physical hardware.
Primary Windows definitions are
[MIB_TCPROW_OWNER_PID](https://learn.microsoft.com/en-us/windows/win32/api/tcpmib/ns-tcpmib-mib_tcprow_owner_pid)
and [GetExtendedTcpTable](https://learn.microsoft.com/en-us/windows/win32/api/iphlpapi/nf-iphlpapi-getextendedtcptable).

AOSP long-list strings are not universally escaped. Supported bounded ordinary
rows are parsed; ambiguous/control-bearing/exotic rows retain private raw bytes
and refuse. Synthetic tests cover nonempty rows; the actual successful capture
contained none and therefore does not qualify real nonempty-device parsing.

Roster observation is not feature acceptance. It establishes neither global
phone absence nor presence, identity, permissions, physical USB transport,
hardware eligibility, model inference, cancellation, restart recovery or
offline gameplay. No Android build or device test was run for this change.
The authorized phone identity and fresh target-specific admission remain
separate requirements. No other emulator, shared service lifecycle, system
setting, guest ledger, model or key was changed.

## Handoff

M01.01 and supporting M01.05/M10.03 host-roster slice: **in_review**. Full
physical-device and reliability gates remain blocked/unverified, with task
checkboxes unchanged and no owner acceptance or merge claimed.

Next runnable supporting task: design and test a narrow target-specific
read-only phone admission path against fake transports, preserving this
service boundary and requiring the retained exact authorized identity before
any target request. A fresh actual phone check requires meaningful new device
state and that admission; do not poll this completed capture until favorable.
External live-process-death Android qualification also remains pending fresh
guarded storage admission and applicable user authorization. Existing charged
guest roots, frozen failures and current recovery stay preserved.

# Receipt supervisor live evidence — 2026-10-24

Refs #9 (M05.05 prerequisite), #5 (M01.05 support). This packet changes only
development supervisor output handling. App, Rust, native, runtime, model and
dependency sources stay unchanged. It selects no production backend.

## Demonstrated gap and implementation

The [preceding attempt](RECEIPT_SETUP_HELPER_VERIFICATION_2026-10-24.md) stopped
at initial instrumentation 255 after its first-method START. Its original
emulator supervisor later became unavailable without stdout/stderr or a final
owner result. The causes remain unknown. The former supervisor buffered output
until final cleanup, so no intermediate prefix was available after owner loss.
All old evidence and saved targets remain preserved.

`LiveOutput` exclusively creates and forces both private output files before
child creation. It retains open handles, forces each retained chunk and counts
only successful forced prefixes. One lock preserves the combined 262,144-byte
cap. Any reader/write/flush/force/close failure is sticky, including a trailing
failure after stop selection. Final cleanup never reopens/truncates a log.

`supervise` keeps the same barrier, Windows job, exact-stop and expiry semantics.
Capture failure returns `evidence_failed`; process cleanup remains separately
reported. An unjoined reader gives unknown byte counts and failed cleanup,
without waiting on its potentially blocked capture lock. Partial logs cannot
prove owner liveness, terminal success, descendant cleanup or guest flush.
See the [protocol](../runtime/android/RECEIPT_AVD_ENVIRONMENT.md) for exact limits.

## Actual host verification

```text
python -B -E -m unittest discover -s scripts/tests -v
```

All 597 tests pass, zero failures/errors/skips, 58.945 seconds. Original owned
execution 11991 was consumed terminal 0: completion 0, known cleanup, 59,766 ms.
Its 69,834-byte stdout SHA-256 is
`2f9b8d9b3b4be8229b84639087c242000125b731c1cdab1b84f4557157e349d1`.
The suite includes all 18 new independent sink/ordering/refusal/loss tests and
existing exact-stop, expiry, descendant, controller and artifact regressions.

The independent author retained three attempts. First: 16 tests, 15 PASS and
one test-only import error before the fake supervisor could spawn, owned
completion 1/known cleanup, 610 ms. Second: 16 PASS/owned 0/known cleanup, 1,000 ms,
but its query-refusal death oracle was weaker and is superseded. Final: corrected
18 PASS, zero failures/errors, 0.911 seconds, owned 0/known cleanup, 1,250 ms.
Final stdout 2,787 bytes SHA-256
`7d62c7d3554ded85404a22e8d860c58c25e399fbb304e0af4b24af2fa9de0f7f`.
All three source bindings remain unchanged; independent review rehashes them.

The final actual Windows loss case waits for acknowledgment after real fsync
of both expected prefixes. It retains non-inheritable SYNCHRONIZE handles for
the live fake worker/grandchild, kills only the captured fake supervisor, and
requires both exact handles signaled before outer safety-job cleanup. Both
prefixes survive and no terminal record appears. Their emergency 60-second timer
cannot satisfy the bounded 5-second terminal waits. This is synthetic host
process evidence, without an emulator, guest flush or application/model result.

No Android rebuild is required or claimed. A fresh emulator qualification is
separately admitted only after final source, artifact and environment review.

## Actual fresh environment and partial Android result

Root and reviewer checked all 457 relevant app/native/build/script source rows,
5,975,443 bytes, equal to the previous compilation. The new reuse-index SHA-256
is `2721fb27cc4006173b876ac8f344c2c6f6bda129d9764eaab8ecbc0a09232d2c`.
The copied audited app APK remains 74,867,728 bytes,
`983f381ed493fdbb8d8d3227a50a164cc6a89ced57cbe0cbeb6dbcefa6f828f7`;
the test APK remains 1,922,331 bytes,
`ec35b26743ae7433d51d1d6b4abfa31db888c031d4ccea18b33cdfaa9a234428`.
This is reuse, not a new build or device/backend compatibility decision.

Frozen execution source is `c2932eac4729d11284ff94179cc64c2d2b7315c1`:
1,424 files/16,801,947 bytes, source-index SHA-256
`35ecd1d701f7221109e9cb955dc07cd359e659f3998d6094504060e94ea97146`.
The installed-only environment uses unchanged emulator 35.3.12/build 12990079,
tools 11.0, platform-tools 37.0.1, API 35 Google APIs x86_64 image 9/ext 13 and
JBR 17.0.6. Separate fresh paths request 12 GiB userdata, 8 GiB SD, 2 GiB RAM/2 CPUs.
Both independent reviews rehash 909 source/tool/image bindings plus protected
old-registry/token metadata. No token contents are printed or copied.

```text
python -B -E benchmarks/receipt_avd_environment.py prepare --proposal <fresh-prepare> --authorization <exact-prepare-authorization>
python -B -E benchmarks/receipt_avd_environment.py run --proposal <fresh-run> --authorization <exact-run-authorization>
python -B -E benchmarks/receipt_setup_qualification.py run --proposal <fresh-guest> --authorization <exact-guest-authorization> --evidence <fresh-device-root>
```

Prepare proposal SHA-256:
`754a00271d74c7df64e05e4dee12633414866c76bf1ae89ce0959c30379dec6c`.
Preparation completed with known child cleanup and preservation closure;
original 86911 consumed terminal 0. SDK child 0/known cleanup, 4,172 ms; 87-byte
stdout SHA-256
`f8a408665fb80180169a6ef44d3f071b0da14c493f2dabc40e26871ce45952c8`.
RUN proposal SHA-256:
`c806a5ef65b6a59998c0c41a6250bedd05efe8e5babb99383b96a286f8575fb2`.
The separately admitted guest proposal binds 49 inputs/86,184,967 bytes:
`1f37f13cda358cded81ac8e6f80a342dfca4a73a72692de92c8b2f4d4eeb2041`.
Root/reviewer actual live leases passed before authorization; neither a serial
nor the running descriptor alone was treated as boot proof.

Actual before facts pass API 35/x86_64/4096-byte pages and no LocalLore
packages/processes. Both exact APK installs pass, with distinct pinned UIDs,
unchanged APK hashes, one public volume and empty APP/TEST inventories.
Userdata availability is 11,604,717,568 bytes before / 11,516,420,096 installed.
Final capacity/identities are not observed by the stopped cohort.

Initial instrumentation returns 0 with a complete runner transcript: three run,
two PASS and one FAIL, 45.445 seconds. `importsAndRechecksThroughActualReceiptSetup`
times out waiting READY at the initial `select(selected); ready()` assertion,
line 129, after 10 seconds. This is not an Activity-recreation or restart failure.
`cancelsBeforeAndAfterAcceptanceThroughCompose` and
`disposedScopeRetainsSourceUntilActualDrain` pass. The 4,565-byte raw SHA-256 is
`9cac5a6bc3254b7480b676d8107122101bb68fcc4352872c5b3a4730fd43a90b`.

All 28 clients have known cleanup. The owned cohort worker completed 2 with known
cleanup, 86,750 ms; 355-byte stdout SHA-256
`52b689d0cb08ded5316231dfa74c2ccf5e1c34cc1885855d4b4469360fe2b63f`,
stderr 0. Original 89862 consumed outer terminal 1. Its failure summary matches a
previous generic stop, but the actual runner evidence is different: this
attempt is two passes/one timeout, not the previous START-only 255. The controller
correctly refuses further dispatch; no helper binding, separate-process reopen,
proof reads or 44-check validation follows. No cause of the timeout, or causal
link to the older failures, is established.

## Bounded diagnostics and actual owner closure

Only separately source-bound read-only diagnostics followed. An initial
proposal's replay gap was corrected before authorization in a new namespace;
the original remains unrun. Corrected one-shot `diagnostic-v2` completes four
clients 0/known cleanup: get-state, process inventory, 200-line crash buffer,
400-line main/system tail, each 15 seconds and at most 262,144 bytes. Original 85376
consumed terminal 0. The crash buffer is empty at inspection and the bounded
tail contains no explanation; this is not proof that no earlier error occurred.

A second two-client metadata/lifecycle proposal lacked ancestor link guards
and was deferred unrun. Its corrected `diagnostic-state-v2` first client refuses
with 2/known cleanup, 94 ms, stdout/stderr 0; original 71259 consumed terminal 1.
It produces no listing and does not run the second filtered-log client. Do not
infer which guard refused, the failed import's state, or a storage/lifecycle
cause. The fixed mapping is diagnostic-only, not trusted Context qualification.
No guard was bypassed, file contents read, test retried or data repaired.

The exact stop request ends original supervisor 99510 with terminal 0. Actual
status is `stop_requested`, known descendant cleanup, preservation closure and
`output_capture_complete: true`, 676,875 ms. Worker return 1 reflects job termination;
it does not change the Android test failure. The 13,835-byte stdout SHA-256 is
`01958ad0d86494870b59e878aa518b1a52c7617d01e5fd7d1141d52143c3310a`;
1,016-byte stderr SHA-256
`1e01aeeacf0c6464ca5d3928d90d1862a31779cd8bc39cf2912f313304808c18`.
Both logs existed and grew before termination. All three recorded host process
identities are absent afterward and the owned ports are free. Immutable inputs,
prepared config, default registry and console-token metadata are preserved.
Saved disks remain retained, with size/time metadata only; no guest flush,
disk-integrity or power-loss claim. This known closure does not reconstruct
the older lost supervisor's missing result.

All 49 admitted guest inputs are archived; index SHA-256
`d0efc2529b5fd680d8edb2249b41823300a444aee8185564c3b110d764ad82fa`.
Private raw files stay in the new `D:/LocalLore-supervisor-` namespaces.
No diagnostics or model weights are uploaded. All 913 non-Markdown source rows,
11,728,643 bytes, still match the frozen execution snapshot.

| Final private inventory | Files | Bytes | Index SHA-256 |
|---|---:|---:|---|
| Host |1,433|94,023,549|`bbafecfa8eb59c91791ba8b5e3c8a8404d32becf4e994670359f105bce08ac2d`|
| Environment |23|393,469|`9bf0dc1881e52c7425e2813e128e0cf730a34c62cdd67632f6519afe245ae1f0`|
| Device |140|86,336,185|`555298fba504746588785cc291d8db8b7a785bcbf2e1a256bebb8e7e89ff1b6c`|

## Remaining gates

Next add a bounded, sanitized synthetic-fixture failure receipt for actual
phase/error/source progress at a failed READY assertion. Do not extend the
10-second wait or guess a storage/lifecycle cause. Then diagnose/fix the actual
observed failure before another separately admitted fresh qualification.

The helper classification still needs a three-plus-one setup
cohort, eight proof reads and44 checks, final identities/capacity and known
emulator-owner cleanup. Prior synthetic passes stay separate. Real-model/SDK,
DocumentsUI delivery, reference phone, ARM64/16 KiB, privacy/cache, power loss,
quality and sustained behavior remain open; existing A/#117/#119 holds remain.
Full M05.05/M01.05 tasks stay unchecked pending complete criteria and owner
acceptance. No model transfer, inference, merge, release or access change.

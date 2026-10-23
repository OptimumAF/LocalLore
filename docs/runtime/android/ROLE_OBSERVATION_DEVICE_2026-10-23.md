# SDK role observation device evidence, 2026-10-23

Refs #5, M01.04/M01.05. One authorized gift attempt failed with a director
timeout. The new telemetry observed output, and independent strict Rust replay
confirmed no accepted gift. The cohort also failed its post-run host-consumption
budget and its final preservation assertion. This is a nonpassing experiment;
milestone acceptance remains pending.

## Fixed experiment and preparation

The selected emulator ran API 35, x86_64, CPU/four threads, LiteRT-LM 0.18.1,
and the existing Gemma model. No dependency, model, workload or deadline changed.
The fixed profile retained 4,096 context tokens, 350 director tokens, 220 narrator
tokens, a 60,000 ms native deadline and one permitted repair. One new private
nonce identified one gift request; there was no SDK retry.

Qualified APK source: `604cb991ade7cb922ef3c89b08e6a296ecab4b4b`.
The APK was 63,666,936 bytes, SHA-256
`9417a3e914975918d018c8a7d8954f192c09e40e10320b08c86be8a50fd7217f`.
Qualification recorded 132 passing JVM tests, zero lint errors/nine existing
warnings, zero permissions and both packaged ABIs. The four native library
hashes matched the preceding traced artifact. Execution covered x86_64 only.
An earlier qualification artifact was superseded before installation.

Preparation and critical execution had separate approvals, fixed 180-second
owned-process bounds and stdin barriers released after Windows Job assignment.
Raw output was retained before validation. Fourteen host-only controller tests
passed, including uncertain-ownership propagation, duplicate dispatch refusal,
actual model-verification invocation and fixed-path/symlink command guards.
No device fault was injected for those source guards.

Preparation passed in 67,672 ms. Two complete host-model passes, including all
78 chunks, took 22,313 ms and matched 2,588,147,712 bytes with SHA-256
`181938105e0eefd105961417e8da75903eacda102c4fce9ce90f50b97139a63c`.
File identity remained stable. The isolated benchmark APK update preserved its
UID and data root. Prior databases, phase journals and cache metadata matched
before/after/final preparation observations. Immediately before the gift, the
new APK independently verified the selected model's complete size/hash with
zero Engine allocations during verification.

## Actual SDK observation

The SDK controller took 92,203 ms and returned a failed `timeout` outcome:
one director attempt, zero narrator calls and zero repairs. The model
initialized. The attempt reported 8,726.0237 ms loading and a 49,043.3789 ms
failed generation interval. Successful-generation token fields remained null.

New terminal observations recorded 15 callback messages, 56 buffered text bytes,
SDK benchmark counts of 1,855 input tokens and 16 output tokens, and the fixed
callback-error category `generation_failed`. Output was observed; its reported
first-observation elapsed value was 46,075.8019 ms. That observer upper bound
is not precise callback time to first token, a throughput measurement, or a
successful complete response. No generated prose is published.

Configuration telemetry recorded schema requested, thinking disabled requested
and template rendered. It does not establish successful enforcement or completion
of schema-constrained generation. The earlier
[traced attempt](TRACED_SDK_DEVICE_2026-10-23.md) used an ordinary-case
`first_output_observed` field that was not populated by that implementation;
its false value was unmeasured. The new observation does not reconstruct what
that older attempt emitted or change its timeout/canonical result.

Owner evidence recorded one Engine opened/closed, one Conversation opened/closed,
balanced owners, terminal cancellation callback and `owner_drained: true`.
Process-termination cleanup was not required. The gift check was false.
The critical child returned 2 after 122,562 ms; its wrapper returned 1 with known
process cleanup. Its retained closure failure is described below.

## Phase readback and independent canonical outcome

After known process absence, one same-nonce read-only phase query validated
27 checkpoints ending at `terminal` / `none` in a fresh reader process. One
historical process-instance/summary record matched, with reason/status `10` / `0`
after the controller's qualified package stop. That record does not diagnose
the timeout's cause.

The read-only transport passed remote-exit and exact encoded binary controls,
then captured a stable 65,536-byte main database. WAL, SHM and rollback journal
were absent before/after. Main-file SHA-256:
`fea955219d41d9fecedafd3934cfda82a335f8c9e53b058f24cb0b15e32a4019`.
Seven-field manifest SHA-256:
`a8db6f952be1e9cd40d1e320fdc3bbb711525f3d61aaa2854d850b281a4e3c4c`.

Independent Rust replay of an isolated working copy completed cleanly in 250 ms:
schema 2, foreign keys valid, one story/branch, strict replay successful,
revision zero, zero accepted events/receipts, failed requested turn without a
receipt, no draft/rebuild, and the player's one potion intact. Pristine files
and working main-file bytes remained unchanged. Replay called no model.

## Admission and preservation failures

Pre-SDK volume-aware admission passed with verified independent cache backing
and stable sampled physical-host identities. Post-SDK admission was blocked:
host free space fell from 12,667,879,424 to 10,284,752,896 bytes, exceeding the
1 GiB consumption allowance. The drop's attribution is unestablished. Observed
cache growth was 788,412,770 bytes and userdata net consumption was 90,112 bytes;
those observations do not override the host-budget failure. The later bounded
capture admission still met its separate floors. Final storage accounting was
not reached.

The final preservation check then raised `AssertionError`. Local analysis of
already-retained output verified all final APK hashes against the pre-critical
maps: 21 on the first emulator and 23 on the second, with only the authorized
benchmark APK update. Original model metadata matched. In an older retained
cache, the directory inode and its 34-byte owner marker's modification/change
timestamps differed. Its model-stat row and generated-cache-file metadata rows
matched. Cache/marker contents were not hashed; the cause of the metadata
difference is unknown. No repair or follow-up device query was attempted.

That assertion prevented final re-observation of the older canonical databases
and phase journals, final inventory, and final storage accounting. Their
successful preparation checks cannot substitute for those missing post-run
checks. The latest completed inventory before critical execution contained four
emulators, no other devices, with both selected devices ready.

The two stages retained 711 command records: 382 preparation and 329 critical.
All recorded commands completed with known cleanup. Nonzero command results
were 22 expected `pidof` absence probes and one deliberate remote-exit-37 control.
Seven separately recorded host metadata clients also completed cleanly.
These statements cover the recorded owned commands, not all possible clients.

No model was copied, downloaded, repaired or evicted. No operation targeted an
old failed turn or changed the emulator lifecycle. The first emulator received
metadata reads only.
There was no post-SDK whole-model hash. Device leases were released and no
additional device calls followed the closure failure. The result establishes
no model-quality, successful profile, physical-phone or ARM execution pass.
The next runnable work is host-side timeout/observation analysis and bounded
investigation of the retained preservation discrepancy before another experiment.

## Sealed private evidence

Raw output, identities, private paths/session tokens, synthetic SQLite and cache
metadata remain private. The sealed device index binds 1,530 files / 1,345,878
bytes, including exact controllers, authorizations, tests, raw commands,
integrity receipts, both failures, phase readback, snapshot and replay receipts.
The local closure analysis binds the exact retained commands; no new device
observations were used to produce it.

- Index SHA-256:
  `cb676ad461d2038e3c533ce10bbafc3049a047d76562e2c843bbc77b023f8b8a`.
- Sanitized handoff SHA-256:
  `f6a93930acf36802bdff085d0cfc7c3d39cd8b1ab2eb5fcf762b35faaa8a8514`.

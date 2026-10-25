# Traced SDK gift attempt, 2026-10-23

Refs #5, M01.03/M01.05. The single authorized gift attempt failed with a director
timeout. It returned structured diagnostics, drained its owners and left no
accepted gift. Independent strict Rust replay confirmed revision zero, zero
accepted events or receipts, and the player's original potion intact.
M01.03/M01.05 acceptance remains pending.

## Frozen experiment

- Selected API 35 x86_64 emulator; CPU, four threads; LiteRT-LM 0.18.1.
- APK source `e8ef8e77e74570ea1ceb9d6dfa54f25753847361`, Java source
  `5123c3c42a74479b6f23509fe0dd6b634edb208f`.
- APK: 63,666,936 bytes, SHA-256
  `f4d247f3e24c302a7e8d2431d7ee8c9fccc476909c0d82789ea1f84083ddfd81`.
- Existing guarded native pair reused unchanged; qualified artifact checks
  recorded 105 JVM tests passing, zero lint errors/nine warnings, zero permissions
  and both packaged ABIs. Actual execution covered x86_64 only.
- Fixed profile: 4,096 context tokens, 350 director tokens, 220 narrator tokens,
  60,000 ms native deadline and one permitted repair. One original potion-gift
  input, one caller-selected private nonce, no automatic SDK retry.
- The fresh APK added read-only same-session phase inspection. The
  [phase protocol](SDK_PHASE_PROTOCOL_V1.md) and
  [readback controller](../../../benchmarks/android_sdk_phase_control.py) keep
  diagnostic checkpoints separate from canonical outcomes.

Preparation and SDK execution had separate coordinator approvals and owned
180-second process bounds. Each owner assigned its Windows Job before releasing
the controller's stdin barrier. All available raw command output was retained
before any verdict. The same sticky device owner covered SDK callbacks, phase
readback, snapshot capture and final preservation.

## Measured result

Preparation completed cleanly in 63,187 ms. The host source model underwent two
complete passes, including 78 hash chunks, in 23,218 ms. Both whole-file hashes
matched 2,588,147,712 bytes and SHA-256
`181938105e0eefd105961417e8da75903eacda102c4fce9ce90f50b97139a63c`;
the held-file and named-file identity remained stable. Immediately before the
gift, the new APK independently verified the selected model's full size and
hash, reporting zero Engine allocations during that verification operation.

The SDK controller took 92,953 ms. It reported a completed worker with a failed
`timeout` outcome, one director attempt, zero narrator calls and zero repairs.
The model initialized. Per-attempt timing recorded 7,524.4987 ms loading and
50,703.7637 ms for the failed generation interval; token counts were unavailable.
These measurements establish no successful generation or throughput result.

The structured owner evidence recorded one Engine opened/closed and one
Conversation opened/closed, balanced owners, a terminal cancellation callback
and `owner_drained: true`. Process-termination cleanup was not required. The
requested gift check was false. The complete diagnostic cohort returned zero
after 124,687 ms; that exit code records completed diagnostics and preservation.

After independently verified process absence, exactly one `read_phase` operation
used the original caller-selected nonce. It validated 27 durable checkpoints,
ending at `terminal` / `none`, from a fresh reader process. One historical record
matched the journal's process identity and summary token. Its reason/status were
`10` / `0`, following the controller's qualified package stop. This does not
diagnose any earlier SDK process death.

## Independent canonical recovery

The read-only transport qualified remote exit propagation and its exact encoded
binary control before reading the new session. It captured a stable 65,536-byte
`stories.sqlite3`; WAL, SHM and rollback journal were absent before and after.
Database SHA-256:
`e16975473712cc1663bbf9e6c2c2274f50345018b374e88cf46d4680cf2c8aba`.
Seven-field snapshot manifest SHA-256:
`f5c1b14082c7e979cd3faa527a51de75a1d85a28167116674d238da3270b307a`.

The coordinator used an isolated working copy for strict Rust replay. The helper
completed cleanly in 62 ms: validated schema 2, foreign keys, one story/branch,
revision zero, zero accepted receipts/events, failed requested turn without a
receipt, and one potion still owned by the player. No projection rebuild or
draft remained. Pristine and working main-file bytes were unchanged. No model
was called during replay. Canonical state supplies this outcome independently
of the SDK report or phase journal.

## Preservation, admission and limits

The qualified update preserved the app UID/data root and changed only the
selected cacheprobe APK. All 21 prior app identities on the first emulator and
23 on the second were otherwise preserved, including the separate phaseprobe.
Original model/cache metadata, the prior failed databases and sidecars, and the
prior phase journal matched their preflight observations. No model was copied,
downloaded or evicted; no old failed turn or emulator lifecycle was changed.
The first emulator received metadata observations only.

Separate installation admission retained its 512 MiB allowance. SDK admission
verified the independent cache backing and unchanged physical host-volume
identities. Post-admission checks passed: observed cache growth was 788,412,770
bytes and userdata net consumption was 139,264 bytes. Final free space was
8,430,669,824 host bytes, 324,255,764,480 evidence-volume bytes and 1,674,469,376
userdata bytes. The final inventory contained four emulators, no other devices,
and both selected devices ready. Device leases were released.

The two stages recorded 714 logger commands: 376 preparation and 338 critical.
All had known cleanup. The nonzero results were 22 expected `pidof` absence
probes and one deliberate remote-exit-37 control. Seven separately recorded
host metadata clients and both owner drivers also completed cleanly. These are
scoped observations about recorded owned commands. Five preparation-fence and
eight critical-fence host tests passed, including propagation of uncertain
recovery ownership before any dependent closure work.

No post-SDK whole-model hash was taken; final model preservation used metadata.
The timeout gives no model-quality, successful profile, physical-phone or ARM
execution qualification. Error-row flags and unavailable token counts do not
establish successful schema-constrained generation. The next runnable task is
bounded director-timeout diagnosis using the preserved checkpoints and host
deadline/cancellation fixtures; another SDK experiment requires separate review.

## Sealed private evidence

Raw diagnostics, identities, session tokens, filesystem paths and the bounded
synthetic SQLite snapshot remain private. The closed device index binds 1,515
files / 1,135,954 bytes, including exact controller/helper source, authorization,
raw outputs, integrity receipts, phase readback and canonical replay receipts.

- Index SHA-256:
  `01ed9984f0f0dc1b9883f06f3417e8575b923623c0f5dbf9261e6ce1b5815445`.
- Sanitized handoff SHA-256:
  `14516af470ba8e5e4e755a0e3487977481f91ee9e580bc4ef433508e6a0e7826`.

# First host packet verification — 2026-10-22

Scope: M02.01–M02.06 contracts and the authorized M03.01/M03.04 host proof.
Task status, claims, blockers and owner acceptance live on [M02 #6](https://github.com/OptimumAF/LocalLore/issues/6),
[M03 #7](https://github.com/OptimumAF/LocalLore/issues/7) and [M01 #5](https://github.com/OptimumAF/LocalLore/issues/5).
This is a dated verification artifact, not a replacement progress checklist.
The concurrent, owner-authorized [tracking migration PR #17](https://github.com/OptimumAF/LocalLore/pull/17)
preserves all original IDs and gates; this implementation does not rewrite the
retired trackers or duplicate their histories.

## Environment and independent work

Started from a clean fresh clone at `e3551b2`; no human changes were present.
Coordinator branch: `impl/m02-host-contracts`. Rust 1.93.1 / cargo 1.93.1,
`x86_64-pc-windows-msvc`, PowerShell, Python 3.9.12. Dependency versions/licenses
and exact build commands are in [DEVELOPMENT.md](DEVELOPMENT.md).

The coordinator claimed shared contracts, engine, fixtures, integration and
tracking before edits/delegation. Two actual independent agents used separate
branches/worktrees and exclusive paths: `research/m01-feasibility` owned
`docs/runtime/` and `benchmarks/`; `review/m02-fixtures` owned `docs/reviews/`.
Original claims were imported to milestone tickets by the tracking coordinator.
Runtime commit `ddaf0b3` and review commits `39bc9be`, `818febc`, `e155310` were
inspected and integrated without editing another agent's working tree.

The review returned six concrete failures: missing seeded epistemic/commitment
state, input reaching inference before size checks, loan returns creating a
reciprocal debt, deadline recognition using the wrong time, duplicate history
acceptance and invalid child identifiers. All were corrected and independently
retested. The review report includes exact probes and limitations; its finite
findings are not human approval.

## Executed checks

| Command | Observed result |
|---|---|
| `cargo check --workspace` | Passed on pinned Rust 1.93.1 |
| `cargo fmt --all -- --check` | Passed |
| `cargo clippy --workspace --all-targets --locked -- -D warnings` | Passed, zero warnings |
| `cargo test --workspace --locked` | 26 integration tests passed; 0 failed; library/binary/doc targets have no separate tests |
| `cargo test --workspace --locked --offline` | Passed after dependency provisioning |
| `cargo run --locked --offline -p locallore` | Passed synthetic gift/replay/observer assertions, explicitly labeled FAKE PROVIDER / HOST ONLY |
| `python -m unittest discover -s benchmarks -p 'test_*.py' -v` | 5 passed; source-manifest shape plus aggregate calculator only |
| PowerShell parser on `benchmarks/inspect-device.ps1` | Zero syntax errors |
| `powershell -NoProfile -File benchmarks/inspect-device.ps1` | Expected exit 2: blocked, 2 authorized transports, 2 emulators, 0 physical candidates |
| `cargo metadata --locked --format-version 1` | All 11 third-party packages inventoried; no runtime/backend dependency |
| `git diff --check` | Passed |

The Rust suite includes 10,000 deterministic generated transition attempts
(seed `0x1a172026`), then replay-byte equality. It independently asserts
conservation, valid owners, resource bounds and unchanged state/history/revision
on rejection. Named tests cover strict wire schemas, exact idempotency,
progression, key return/deadlines, separate claims/beliefs/truth, unknown abilities,
life/location rules, co-located audiences, secret canaries, same-name NPCs,
story/branch/ancestor limits, player/author boundaries, malformed/failing/late/
cancelled fake responses and invented narration. A first test run exposed a
deadline-test expectation after the rule fix and clippy's large enum warning;
the test now exercises an actual late return and the context field is boxed.
The final recorded checks pass.

## Physical and model gates

The initial PATH-only `adb` check was incomplete. Independent read-only SDK
discovery found two authorized Android 15 `sdk_gphone64_x86_64`/`ranchu` emulators
and no physical phone. No serials, personal content, weights or unique device IDs
are included. No app was installed or device changed. Physical M01 gates require
an authorized phone and provisioned hash-verified model/runtime.

Official compatibility research pins LiteRT-LM v0.18.1 and llama.cpp v0.7.0 to
exact source commits, with candidate model/config/template/license sources.
[The report](runtime/FEASIBILITY_2026-10-22.md) records what those sources establish
and what remains untested. Published artifact hashes were not checked against
local weights; no conversion, load, inference, sustained/thermal measurement,
supported device/profile or production backend selection is claimed.

## Limits and handoff

This packet proves a bounded in-memory host contract. The gift transfers a potion
to Mira; NPC consumption/healing and app restart are not exercised. Root replay
verifies deterministic v1 receipts, not a durable migration-capable effect
reducer. No SQLite, Android shell, FFI, CI workflow/settings change, actual model,
free-form narration evaluator, author editor, summaries, imports or releases are
implemented. The executable needs no network/account/telemetry during play;
dependency provisioning can use the network. Token limits are a native-adapter
contract; the fake enforces bytes/polls/cooperative cancellation.

ADR-0003 records the single-crate host boundary and bounded sequencing without
relaxing any existing milestone gate. M03.02 can next create the minimal Compose
shell against the frozen fake contract and verify it on the available emulators;
M03.03 then demonstrates native ownership/cancellation. Host CI preparation
(M03.05) can proceed separately without changing repository Actions settings.
Storage transactions and outcome-only replay remain M04, after the required
foundation gates. Owner review/merge, repository settings and releases were not
performed. Material AI assistance is disclosed for this implementation and review;
all fixture/story content is original synthetic material.

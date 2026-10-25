# D07 native Host policy port — source handoff, 2026-10-23

Status: **implemented, UNCOMPILED / UNRUN**. This is a bounded prerequisite for
#29 D07.03/.04 and #11 M07.01, not execution of a memory comparison or completion
of those tasks. No inference provider, model, app, native runtime, device, Cargo,
Node, or Gradle was executed for this packet. No existing report was rewritten.

## Source and ownership

- Base: `5638c0d1eeefcd03053384778f5fbbf74ac117df`.
- Branch: `impl/d07-host-policy`, isolated `source-host-policy` worktree.
- Claims: [#29](https://github.com/OptimumAF/LocalLore/issues/29#issuecomment-6378229613)
  and [#11](https://github.com/OptimumAF/LocalLore/issues/11#issuecomment-6378229790).
- Frozen four-test source: `54d7f2db7ac6c1d772b586577f07de237ad4ef92`;
  pre-execution helper type annotation: `9a75f6c7bfafbce6f07d2f3a9422419b7036eb22`.
  The latter changes no assertion, fixture outcome, or production behavior.
- Production: `55f0a4144628b8cf9e1bbdaa19f9759b15a4ab00`, **only**
  `crates/locallore/src/host.rs`, 36 insertions / 4 deletions.
- New tests: `crates/locallore/tests/d07_host_policy.rs`, SHA-256
  `fb10c16eff7beea9eca7a56dd5dc4a1dc7ca6f5136461b5d3aeb51120403f625`.
- Production `host.rs` SHA-256:
  `3137c02aee4b212954e337b7130f6711c4c86b84255467113a0dfc580bd4027c`.

Root retains integration and every other Host concern, Store/schema/Core compiler,
DTO, runtime, app, Android, comparison protocol, reference-prefix construction,
and cap decisions. This stack must be reviewed separately from Root's current
qualification tree. The protected chat and its resources were not accessed.

## Native interface and lifecycle

The additive native methods are:

```rust
pub fn configure_local_provider_with_policy(
    &self,
    profile: crate::play::PlayProfile,
    provider: ProviderFactory,
    policy: crate::play::PlayContextPolicy,
) -> Result<(), String>;

pub fn configure_fixture_provider_with_policy(
    &self,
    profile: crate::play::PlayProfile,
    provider: ProviderFactory,
    policy: crate::play::PlayContextPolicy,
) -> Result<(), String>;
```

`PlayContextPolicy` is the existing closed Core enum, with
`StateRecentTranscriptV1` and `StateRelevantMemoryV1`. Existing configuration
methods delegate with Relevant and preserve the existing real-model/fixture
metadata distinction. Profile validation remains before state mutation.

`LocalPlay` stores the policy beside its existing profile, factory, and native
owner metadata. Existing `begin_work` clones that complete configuration into
`Work`. Reconfiguration after work begins cannot change that work's selected
policy or provider. Work which has not begun uses the configuration in effect
when `begin_work` runs; this is not a submission-time policy reservation.

The existing coherent generation snapshot is unchanged. The one generation call
now passes that same Engine, native `CoverageRead`, provider, cancellation token,
profile, and trace sink to `execute_traced_with_policy`, using the frozen Work
policy. It neither synthesizes coverage nor changes source fallback reasons.
No new field enters HostCommand, JSON Schema, capabilities, or the wire. No new
knowledge/inspection permission is introduced. Existing ownership, source-basis,
cancellation, idempotency, publication, and trace controls are untouched.

## Frozen oracles

The four new tests use bounded, deterministic synthetic responses through the
actual Host configuration, admission, prepare, and existing Play pipeline:

1. Both policies on an actual Engine with twelve accepted typed Say receipts.
   The test-only read fixture supplies that Engine through default native
   `Persistence::generation_snapshot`. Its only temporary state is draft
   admission; every write method is Unsupported. Prepared receipt policy,
   context2/compiler2, and actual Director `transcript_unit` distinction are
   asserted; actual narrator inputs exclude optional history/private canaries.
   The post-prepare snapshot must retain identical canonical bytes and return
   the honest default Raw/Missing source result. This is not Store durability
   evidence and does not implement a replacement production persistence layer.
2. Both existing native configuration methods retain Relevant and their
   established owner metadata. Even the local-owner metadata arm uses the same
   synthetic provider; it is explicitly not real-model execution evidence.
3. An actual ephemeral Host commit, then reconfiguration, preserves the exact
   committed receipt on submit/prepare/commit retry with zero future role calls.
   Unknown policy-setting JSON and extra policy fields are rejected.
4. An actual held provider proves old Work retains Recent and its old provider
   across reconfiguration; the next work uses Relevant and the new provider.
   The fixture polls Pending until an atomic release, has a 5-second generation
   deadline, and releases on unwind. The 2-second channel wait is a bounded
   liveness guard, not a performance measurement.

These are frozen test intentions, not PASS results. The tests exercise native
Rust Host calls, not platform IPC, native WebView rendering, Android JNI, or
human review. No model-quality, memory-benefit, speed, or saving claim follows.

## Actual checks and next runnable gate

Actual source-only checks on this worktree:

```text
rustfmt --edition 2021 crates/locallore/tests/d07_host_policy.rs
rustfmt --edition 2021 --config skip_children=true crates/locallore/src/host.rs
git diff --check
```

All completed successfully. These parse/format and whitespace checks do not
type-check the code. Installed versions observed: `rustfmt 1.8.0-stable` and
`rustc 1.93.1` (`01f6ddf75`, 2026-02-11). No Cargo/test execution was authorized
for this source-only assignment; there is no execution failure or RED to report.

Next, the coordinator should import the test commits then the production commit
into an isolated qualification tree, retain the frozen source, and run at least:

```text
cargo test -p locallore --locked --offline --jobs 1 --features host --test d07_host_policy
cargo test -p locallore --locked --offline --jobs 1 --all-features --test d07_host_policy
cargo clippy -p locallore --locked --offline --jobs 1 --all-targets --all-features -- -D warnings
```

Use a dedicated D target and TEMP, debug info/incremental compilation disabled,
and the coordinator's exclusive heavy slot. Preserve any first compile/behavior
failure before a narrow correction. Run appropriate existing Host, generation
snapshot, Play historical retry, and schema equality tests before integration.
The existing shared compiler already implements both policies, but that does not
prove this unexecuted Host plumbing or a paired/rollout comparison.

Actual paired/reference construction, semantic input bindings, durable comparison
reservations, resume/cancel accounting, reports, and human rubric remain outside
this packet. The comparison contract and original caps remain pending. No app
selection UI or model cohort is authorized by this source handoff.

# Native literal Host selection and durability

Scope: D07.04 / M07.01 prerequisite. Accepted base PR185,
`b88cc23ebd377aaf66ba23d74b384e44c7697ff3`. Initial production
`ddeb7a77a88617b0ad34f085d70ef7cad5eba1df`; final tested source
`77d177ba24eed0fa579e8a492351e0f3985027a5`.
GitHub #29/#11 own status. Shared persistence remains owned by #8; no Store,
adapter, schema, migration, evaluator or app production file is changed here.

This is a **native Rust Host route**, exercised through actual Host JSON commands
with scripted providers. The Workspace tests use the actual Repository/SQLite
Store. Core spy-port tests are separate, not SQLite durability evidence. No
literal evaluator/report protocol, frontend/JNI version decoder or user-facing
selection is exposed yet. Existing native apps keep their current defaults.

## Configuration, source and commit boundaries

`host::HostPlayConstructionV1` is a native-only Clone/Copy/Debug/Eq enum:
Memory(PlayContextPolicy) or PlayerLiteralV1. It has no serde implementation;
two compile-fail doctests enforce that boundary. Additive
`configure_local_provider_with_construction` and fixture counterpart accept a
PlayProfile, ProviderFactory and enum. Existing default/_with_policy methods
delegate to Memory, preserving policy, profile and real/fixture labels.

LocalPlay captures the construction, provider, profile and real_model flag into
Work before generation. Reconfiguring future work cannot relabel a running
turn's provider, receipt or trace. Literal trace provenance uses its exact
2.6 prompt version and `locallore-director-literal-v1` schema label. Memory's
previous labels remain byte-identical. The fixture setter stays false; testing
the real-label setter with a scripted factory proves label plumbing only.

`begin_work.engine` is cached and cannot be the literal source. A Host-private
canonical read uses existing Persistence::resume, whose actual Store adapter
provides a coherent validated canonical transaction. It does not request a
memory snapshot/proof. The public generation_snapshot keeps its existing
coupled Engine+coverage port. Both routes share the same live session/scope,
exact head/actual player, full Seed equality, accepted-prefix/lineage, panic
containment and latched cancellation fence. Ephemeral literal work uses the
selected clone. Literal Work.coverage is None, never fabricated Raw/Missing.

The source read does not grant inspection/Lab privileges, run maintenance or
select another observer. Cancellation is checked before/after the synchronous
read; this does not promise interruption inside SQLite. Literal Domain2 is
refused before provider creation. New work then uses the accepted literal
executor with the same factory, trace sink and unchanged finish_work/bound
Store commit path. No JSON field or operation configures construction.

## Honest restart contract

Committed receipts and intent drafts are durable. An uncommitted Ready generated
candidate is currently process-memory-only: persistence has no save-prepared
output port/phase. Ready does not expose a fabricated receipt on the wire.
After process-owner reopen, its saved intent is Queued and Commit returns
NotReady, with unchanged canon. This test does not regenerate output or claim
zero-generation Ready restoration. Committed restart/status/exact retry does
reuse the original receipt with zero factory/poll calls.

This corrected an extra proposed fixture assumption, not an observed regression
in accepted D03 #24. No accepted criterion is reopened or weakened and no
desktop cache competes with shared persistence. The distinction is recorded on
#8 and #29. Any future durable uncommitted output belongs to a separately scoped
shared persistence contract.

## Executed checks

Windows NT10.0.26300 x64 / PowerShell7.6.5 / Rust1.93.1 (`01f6ddf75`) /
Cargo1.93.1 (`083ac5135`) / LLVM21.1.8. Cached dependencies only; locked/offline,
jobs1, debug0/incremental0 and owned TEMP/target. All terminal Cargo checks below
recorded clean and unchanged source. No dependency or asset install/download.

| Final77d177ba check | Result / command time |
|---|---|
| New Core Host source/configuration suite |8PASS/0FAIL,0.13s tests/9.896s command |
| New actual Workspace/Store suite |5PASS/0FAIL;11.897s command |
| Core library + existing Host policy/trace regressions |79PASS/0FAIL;14.559s command |
| Nine existing workspace generation/play/author/trace targets |53PASS/0FAIL;18.945s command |
| Four original actual-Play stable projections |1PASS; unchanged hashes;1.514s command |
| Six original whole-policy references |1PASS; unchanged hashes;0.370s command |
| Source/renderer/Host no-serde doctests |10PASS/0FAIL;1.548s command |
| Core strict all-target/all-feature Clippy |PASS;14.681s command |
| Workspace strict all-target/all-feature Clippy |PASS;7.85s Cargo/8.084s command; wrapper correction confirmed0.491s |
| Rust workspace format |PASS;2.210s command |
| Android Rust host |20PASS,1.67s tests/4.093s command |
| Android dependency graph |PASS;0.364s; no Tauri/eval/local-runtime edge |
| Desktop strict all-target/all-feature Clippy |PASS;23.61s Cargo/23.859s command |
| Normal desktop build |PASS;30.71s Cargo/30.886s command; executable not launched |

The previous837-pass default-member workspace qualification belongs to PR185;
it is not reported as a new full-suite run after this Host change.

Eight new Core groups cover both modes and real/fixture label setters with fake
providers; actual renderer byte equality; player generation without Lab and
JSON/observer denials; held construction/provider/provenance surviving a Memory
reconfiguration; canonical resume bypassing failing/panicking memory ports;
actual append/seed/same-head history/lineage/player/scope changes refused before
factory/polls; contained canonical-read panic with live-owner retry; prior cancel
and foreign selection; actual Domain2 refusal before factory creation. The
fixed deliberate panic-hook message is expected. Spy persistence is not durable.

Five Workspace groups cover actual Ready without canon mutation, explicit2.6
commit/both context fields absent, restart/exact retry with zero generation;
honest unfinished-draft reopen; held-provider cancellation with durable cancelled
status; another real Store writer causing old work to become stale; and actual
completed-player-job/proof nonmutation. A fresh supported missing-player job
lookup stays None before/after Ready. Nonplayer maintenance lookup is separately
refused as Stale; it does not prove absence of a Mira partition. These are known
job/proof checks, not whole-table SQL inventory or malformed-cache injection.

Independent bounded production review found no concrete fence, provenance,
configuration or default-path defect. It ran no tests and is not human quality
approval. Mid-read canonical cancellation is source-reviewed, not directly
measured: resume has no cancellation callback/public token hook. No hook was
invented to manufacture that result.

## Retained initial attempts

- Workspace source ca8dc0a0 →0022646a and Core source08555e24 →1d0a35ce
  compiled before implementation and failed for missing APIs (3.843s/8.391s).
  Neither observation is behavioral RED.
- Initial production ddeb7a77: Core7PASS/0FAIL; Workspace4PASS/1FAIL in0.52s.
  The failing fixture assumed Mira maintenance lookup returned missing; actual
  selected-player validation returns Stale before Host preparation. Corrected
  test34cf38b0 keeps that refusal and adds a genuine missing-player lookup:
 5PASS in0.58s. Production rules were unchanged.
- Test-only0a24921e adds the actual Domain2-before-factory case:8PASS in0.20s.
- A regression command named nonexistent m08_author_host_play; Cargo exited101
  before running any test. Correct targets include m08_author_host_port_review
  and m08_typed_host_v2_review; the corrected53-test run passed.
- Strict Core Clippy flagged an unnecessary unwrap after is_some at0a24921e.
  Production77d177ba uses an equivalent tuple match; final checks above pass.
- Workspace Clippy itself exited0, but the external wrapper mistakenly looked
  for a test-pass line and stopped the batch. The wrapper now applies that check
  only to test commands. Its confirmed rerun and all remaining checks pass.

All attempts remain local, including the fixture failure, invocation error and
lint/wrapper observations. They are not relabeled as production regressions or
silently omitted from the successful cohort.

## Reproduce and limits

From root, set owned absolute TEMP/target and the environment above; run serially:

```powershell
cargo test --locked --offline -p locallore --features host --jobs 1 --target-dir <target> --test literal_host_construction -- --nocapture --test-threads=1
cargo test --locked --offline -p locallore-workspace --jobs 1 --target-dir <target> --test literal_host_durable -- --nocapture --test-threads=1
cargo test --locked --offline -p locallore --features host --jobs 1 --target-dir <target> --lib --test d07_host_policy --test production_turn_trace --test turn_trace -- --test-threads=1
cargo test --locked --offline -p locallore-workspace --jobs 1 --target-dir <target> --test generation_snapshot_host --test generation_snapshot_port_review --test generation_play_consumer --test generation_consumer_review --test play_host --test m08_author_host_port_review --test m08_typed_host_v2_review --test m08_legacy_host_consumers --test turn_trace_host -- --test-threads=1
cargo test --locked --offline -p locallore --jobs 1 --target-dir <target> --test literal_director_legacy_bytes --test literal_transcript_legacy_bytes -- --nocapture --test-threads=1
cargo test --locked --offline -p locallore --features host --jobs 1 --target-dir <target> --doc -- --test-threads=1
cargo clippy --locked --offline -p locallore --all-targets --all-features --jobs 1 --target-dir <target> -- -D warnings
cargo clippy --locked --offline -p locallore-workspace --all-targets --all-features --jobs 1 --target-dir <target> -- -D warnings
cargo test --locked --offline --manifest-path crates/locallore-android/Cargo.toml --jobs 1 --target-dir <target> --lib -- --test-threads=1
cargo tree --locked --offline --manifest-path crates/locallore-android/Cargo.toml --edges normal,build,dev --prefix none
cargo clippy --locked --offline --manifest-path apps/desktop/src-tauri/Cargo.toml --all-targets --all-features --jobs 1 --target-dir <target> -- -D warnings
cargo build --locked --offline --manifest-path apps/desktop/src-tauri/Cargo.toml --jobs 1 --target-dir <target>
cargo fmt --all -- --check
```

Synthetic raw logs/process records remain ignored/local under
`d07-literal-host-*`. Final Core log SHA256
`17b27382322f5c6adc0bc62d057e3bf9cccc56d522708de2b8148368adc7a8d0`;
final durable log
`642a78ea241440f196af3492211f406b8caa7ef997a9cda012fcf61ebe6cc43b`;
workspace regressions
`71137efc292e577455b570133086f2a371d2f7afaf531bab9ff1fd65d23a1f10`;
initial fixture-failure log
`97a3a02b129cb9242298c97ef042813d2f3f67511ce724ec64772cf19da95a2d`.
No raw private stories/prompts, personal paths or diagnostics are published.

No real model, Tauri/native IPC, frontend controller/headless/WebView render,
Android ABI/JVM/Gradle/emulator/phone, performance/RAM, installer or narrative
quality execution is claimed. Frontend files are unchanged and frontend checks
were not rerun here. No new render image exists to inspect. Existing moderate
GLib advisory and observed unrelated-library narration failure remain open.

Next runnable work is a separate literal-vs-relevant comparison/report binding
and actual-capture validator. Protocol2 requires compiler2/ContextPolicy data
and cannot be relabeled literal. Its old reports/readers remain unchanged;
selected/report/decoder/UI exposure follows explicit versioned closure. Real
paired-model and human quality gates remain required. No whole D07/M07 checkbox,
desktop completion, physical-phone claim or release qualification is awarded.

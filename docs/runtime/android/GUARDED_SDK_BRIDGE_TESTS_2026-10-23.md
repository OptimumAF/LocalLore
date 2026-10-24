# Guarded SDK bridge host tests, 2026-10-23

Refs [#5](https://github.com/OptimumAF/LocalLore/issues/5)
(M01.03/M01.05 partial), claim `6373018837`. These are original host integration
tests of the production `ProbeRegistry` byte interface and guarded Host. All
provider responses are explicitly synthetic bytes. No model, JNI, SDK engine,
Android device or physical-phone qualification is claimed.

## Source and authority

The test base is `ba31932665eab2079c54a02a0182857f598fa0c4`: the coordinator's
integration of accepted implementation `5138427`, the captured Play v2.2 receipt
fixture and independent guarded-schema tests. The implementation already binds
generation to the finite Engine-preflighted action and records prompt
`locallore-play-v2.3`. This packet changes no schema, provider, Host, engine,
Store, historical receipt or application code. The earlier SDK rejection and
its artifact/evidence remain separate; passing synthetic bytes do not explain
or erase that real-generation failure.

The new integration file is
`crates/locallore-android/tests/guarded_play_probe.rs`. It uses only public
`ProbeRegistry::{open,call,poll,respond,close}` and actual durable Host/Store
operations. Artifact hashes in its trusted profile are synthetic identifiers;
no file/model is opened for inference. The experiment's profile limits remain
4096 context tokens, 350 director tokens, 220 narrator tokens, a 60,000 ms
turn deadline and one repair. Native requests still have exactly seven fields:
`version`, `role`, `prompt`, `max_tokens`, `context_tokens`, `threads`, `schema`.

## Original test inventory

1. `supported_actions_reach_public_sdk_packets_with_only_the_preflighted_arguments`:
   six independently specified gift, consume, ability-use, learn, move and wait
   actions reach a real pending request. Every operation/argument is an exact
   `const`, with one command and no extra properties. Repeated poll is immutable;
   cancellation leaves accepted state unchanged. Two actual seed NPC-only belief
   canaries are absent from the prompt/schema. This is not an exhaustive test of
   future-branch retrieval or all observer contexts.
2. `explicit_fake_gift_bytes_require_both_roles_then_commit_original_request_and_reopen`:
   a literal gift response, not a response reconstructed from its schema, needs
   director and narrator tickets. Ready remains noncanonical. Actual commit
   retains original input/key/profile and prompt version; exact retry/reopen
   returns the same receipt. The sole potion transfers once; known facts remain
   unchanged. Actual player/Mira contexts observe the event and absent Sable does
   not. No-inference retry emits no new pending request.
3. `schema_ignoring_valid_wait_and_wrong_arguments_are_agency_failures_without_narration`:
   valid typed Wait, Consume, wrong quantity, wrong item and wrong recipient
   responses are supplied despite the bound gift schema. All five fail `Agency`
   without a narrator, receipt or canonical mutation, including after reopen.
   Asking to commit a failed attempt still returns a failed/no-receipt view.
4. `malformed_repair_keeps_exact_bound_grammar_and_never_substitutes_a_correct_proposal`:
   malformed bytes require a fresh repair ticket with an identical schema and
   explicit repair prompt. The stale ticket cannot respond. A valid wrong Wait
   repair fails `Agency`; only explicitly supplied correct gift bytes can reach
   the narrator/Ready phase. Neither branch commits.
5. `cancellation_at_repair_and_close_at_narrator_invalidate_only_the_old_guarded_work`:
   cancellation during repair and close during narration invalidate observed
   tickets. A replacement Wait request has its own exact grammar; old gift bytes
   cannot consume or change that pending request. Accepted state remains unchanged.

Each test owns fresh marked synthetic directories. This file closes its native
owners and joins its test preparation threads, retaining its databases for
inspection. These joins do not establish cleanup of an uncooperative SDK worker.
Existing tests retain their existing owned-temporary-directory cleanup behavior.

## Executed checks

Windows host, Rust/Cargo 1.93.1, cached dependencies, locked/offline. A fresh
marked D-drive root contains `target`, `temp` and all command logs; developer and
test debug information and incremental compilation were disabled. No C-drive
compiler output was requested.

```powershell
$env:CARGO_TARGET_DIR = '<fresh-marked-D-root>/target'
$env:TEMP = '<fresh-marked-D-root>/temp'
$env:TMP = $env:TEMP
$env:CARGO_PROFILE_DEV_DEBUG = '0'
$env:CARGO_PROFILE_TEST_DEBUG = '0'
$env:CARGO_INCREMENTAL = '0'
cargo test -p locallore-android --features play-probe --locked --offline --test guarded_play_probe
cargo test -p locallore-android --features play-probe --locked --offline --lib --test play_probe
cargo clippy -p locallore-android --features play-probe --all-targets --locked --offline -- -D warnings
cargo fmt --all -- --check
```

Final results: **5 new integration tests passed**, **12 existing library tests
passed**, **7 existing play-probe tests passed**, zero ignored in those selections.
Strict Clippy and workspace formatting passed; `git diff --check` passed.

All attempts were retained. The first targeted command failed compilation on
two author-test mistakes: a missing returned-reference lifetime and the context
field name `events` instead of `observations`; no test bodies ran. Attempts two
and three each ran five tests with four passes and one failed author assertion
about the existing commit-on-failed-turn response. The actual API returns an
`ok` failed/no-receipt view with nullable error metadata, rather than a top-level
`NotReady` or the initial preparation error. The final test checks the unchanged
accepted state and exact failed scope/key/head/no-receipt behavior, while still
requiring the original preparation to fail `Agency`. Attempt four passed all
five. No production change was required by these failures.

Private evidence is retained in the dedicated guarded-SDK-bridge D-drive root:
toolchain records, all four targeted-test logs/exit files, formatting logs,
existing-suite log, strict-Clippy log and command/environment sidecars. Synthetic
workspaces remain under its `temp` directory; no recursive cleanup was run by
this packet. Coordinator ticket/PR integration and full milestone acceptance are
separate. The next runnable step is the coordinator's current-source artifact
qualification and separately admitted real SDK experiment, preserving prior
rejections and all device/model/storage gates.

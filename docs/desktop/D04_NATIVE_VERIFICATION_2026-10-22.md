# D04 native integration verification - 2026-10-22

D04.02/.03/.04/.05/.06 desktop integration is ready for review. This is a bounded
native integration result, not acceptance of the whole D04 or M05 exit gate.
Both accepted real-model turns used the explicit safe narration fallback.
**Narrative quality, network-blocked operation, sustained performance, other
devices and release packaging remain unqualified.**

The definitive actual native run passed **31 distinct assertions, ten app-owned
PNG captures and a real executable process restart**. It used clean source
7c66260ada2c7b97527437b5c846c027f3f11d3a, including shared canonical eligible-ID
schema commit 26df6f0. Subsequent c448672 only formats the owned CSS/generated
schema; it changes no schema values or CSS behavior. Normal frontend assets and
the default native executable were rebuilt after the harnesses.

The committed [synthetic evidence](D04_NATIVE_EVIDENCE_2026-10-22.json) includes
the exact source/frontend/executable/worker SHA256 map and bounded semantic
reports. Its source summary SHA256 is
2b64aada2efc8bd4f1008d280475329db03bb5bd1436630a34e236ee07c90293.
Local task-owned artifact directory on the D drive:
desktop-artifacts/model-native-a3f9428d-541a-4b04-922c-4159ec0be4b1.
These artifacts are local and ignored; no weights, private saves or profiles are
published. Source hashes use exact local bytes; compare Git-normalized text when
CRLF differs across checkouts.

## Actual model, runtime and scene

The run used Windows x64, the existing reviewed llama.cpp CPU worker at revision
620d2225cc436ab0b001e3200e590e3b286ef9ab, SHA256
eda393e923ddfd03ea57d91741d8f7948d1a4af13deb90c7d6c90c492e63ff58.
The approved Qwen3-0.6B Q8_0 GGUF is 639446688 bytes, SHA256
9465e63a22add5354d9bb4b99e90117043c7124007664907259bd16d043bb031.
The actual native runtime locks and verifies that worker and model before load.
Profile qwen3-0.6b-q8-cpu-v1 uses one resident model, separate fresh director and
narrator contexts, context4096, 350-token role caps, CPU four threads, GPU zero,
one repair and a 120000 ms deadline. Manifest SHA256:
01ad542001b04a96f4a8ed6c841be1866eb025350836e0c5d0a4969fdb361d38.
Template SHA256:
57f1fd00f0013a2be96aa79b857391f27e23df5b5f847072b524c897e24d0361.
Saved receipts record grounded-prose-v2.1 / locallore-play-v2.1.

The launcher reused one previously imported, verified app-owned copy under a
Unicode-and-spaces synthetic model root. It created a fresh database under a
different Unicode-and-spaces root and used that same database through two actual
executable processes. The approved original model was opened read-only and was
never modified, renamed or hard-linked. No additional 640 MB copy was made for
the final scene. A separate earlier import diagnostic measured the actual copy
and error/cancel paths, as described below.

The same production controller and native IPC exercised explicit model loading,
hash/load cancellation, pending noncanonical state, a real free-text gift,
deliberately dropped commit acknowledgment, exact-key recovery of one v2 receipt,
double-spend refusal, explicit Dialogue, unsupported-action clarification,
unlearned-ability refusal, running-generation cancellation, absent-NPC knowledge
isolation, a distinct new story, original-story resume, unload/reload and restart.
After restart, the exact original request resolved its stored committed receipt
without a loaded model. Unload preserved the original history and kept local mode
selected with ModelUnavailable, rather than selecting a fixture provider.

The potion receipt contains exactly Give(potion, mira, quantity1), revision1 and
one spent potion. The Dialogue receipt at revision2 records the original literal
synthetic secret; Sable's observer context excludes that secret. Inventory,
ClarificationRequired and Ability failures add no canonical events. Cancel leaves
the accepted revision unchanged. Both real inference roles ran for accepted
turns; safe engine narration was used after narration validation. There were zero
repairs. The visible narrations were "You give 1 potion to mira." and "Your words
are heard by the chosen listeners." This fallback rate is **2/2**, not evidence
that generated prose is qualified.

| Measurement | Observed milliseconds |
| --- | ---: |
| Initial UI model load, including verification/configuration | 10850 |
| Potion receipt director / narrator / total | 2782 / 1972 / 4756 |
| Dialogue receipt director / narrator / total | 3149 / 1792 / 4942 |
| Double spend / clarification / unlearned ability refusal | 45 / 40 / 73 |
| Explicit model reload | 10557 |
| Model load after real process restart | 10171 |

These are single-run observations, not latency, memory or thermal qualification.
Receipt total includes the whole canonical pipeline. The frontend timer for the
potion starts after its pending capture, so it is not a substitute for receipt
total. Zero-millisecond validation stages reflect coarse elapsed timing.

## Lifecycle, import and regression checks

Default native tests passed **15/15**. Development native tests passed **17/17**,
plus **2/2** harness-wrapper tests. The added model regressions cover old-window
cancellation, stale same-window operation IDs, delayed closed-window picker and
unload work, retirement before publication, invalid source/cancel and missing
worker outcomes. Existing export and lease tests also passed. Long filesystem,
hash, runtime and Host operations remain outside the UI and metadata lock;
cancellation captures the first observed operation ID and rejects stale jobs.

Commands actually run with CARGO_PROFILE_DEV_DEBUG=0,
CARGO_PROFILE_TEST_DEBUG=0 and CARGO_INCREMENTAL=0:

```powershell
cargo test --manifest-path apps/desktop/src-tauri/Cargo.toml --locked --offline
cargo test --manifest-path apps/desktop/src-tauri/Cargo.toml --locked --offline --features dev-harness
cargo clippy --manifest-path apps/desktop/src-tauri/Cargo.toml --all-targets --locked --offline -- -D warnings
cargo clippy --manifest-path apps/desktop/src-tauri/Cargo.toml --all-targets --locked --offline --features dev-harness -- -D warnings
cargo fmt --manifest-path apps/desktop/src-tauri/Cargo.toml -- --check
npm --prefix apps/desktop run check
npm --prefix apps/desktop run format:check
cargo build --manifest-path apps/desktop/src-tauri/Cargo.toml --locked --offline
```

All passed. Frontend checks cover strict TypeScript, 25 original Rust action
fixtures plus four current builders, hostile-wire/bounded-error handling,
keyboard policy, normal-asset hook absence, actual-controller export races, and
real-request recovery with a stale fake fault selector. Model cancellation tests
also prove an unknown operation cannot be cancelled and a delayed cancel retains
its original native operation ID rather than taking a newer status ID.

Previous feature journeys passed again against the integrated D04 sources:

| Runner | Result | Local artifact suffix |
| --- | --- | --- |
| node harness.mjs native | 163 assertions / 21 checkpoints | native-d5804a33-ea6c-44a5-9024-3c154038c374 |
| node harness.mjs headless | 163 assertions / 21 checkpoints | headless-da46b4d3-1756-4bee-a212-c20472c8904b |
| node durable-harness.mjs | 33 assertions / 11 PNGs | durable-native-3862d999-358e-4c82-ac1f-006dfae06201 |
| node export-harness.mjs | 36 assertions / 14 PNGs / four publications | export-native-d1df4500-de6a-429d-82c2-e7dd124bd799 |

These directories are under apps/desktop/artifacts. Legacy native/headless runs
use explicitly labelled memory fixtures; durable/export runs use synthetic SQLite.
The final durable run recorded dirty=true while only the formatting edits later
committed as c448672 were present. The model run, legacy runs and export run each
recorded a clean source. Exact revisions and summary hashes are in the evidence.

Earlier actual native import diagnostics under
model-native-a7ec0eea-f7da-48dd-ba59-595d88e2aa6a checked missing/corrupt sources,
picker cancellation, cancellation while copying with no published partial, and
successful verified Unicode-path import (9964 ms). That diagnostic subsequently
failed on the old shared action decoder and is deliberately not labelled a
passing whole-scene run. Native unit cases exercise these import errors at the
final source. The normal Windows file picker branch was compiled; the hidden
harness used only trusted launcher-owned fixed synthetic choices.

Earlier failures are retained: the shared validator rejected a valid profile
period, the old worker ordered Give.item before op, and one generated recipient
used display-name Mira instead of canonical mira. Shared fixes preserve strict
engine validation. An intermediate header-capture run accepted the gift then
failed because its new label was missing from the dev-only allowlist; 7c66260
adds only that fixed label. No mechanical or privacy guard was weakened to pass.

## Rendering, boundaries and remaining gates

Visual review used only the application's hidden native CapturePreview output.
The focused receipt capture and paired model-receipt-context.png show the real
provider, story/scope/revision, rules, approved turn, inventory and fallback label.
Pending capture identifies generating work as noncanonical. Restart shows the
same two saved receipts with provenance despite no loaded model. Invalid-action
and cancellation captures preserve the accepted head. All ten semantic captures
record no horizontal overflow; synthetic JSON contains no actual home paths.
These observations cover the captured states, not all history/layout variants.
The verbose state-diff layout is separate future work.

No window activation, desktop input, desktop screenshot, CUA, ADB, unrelated-app
automation or protected runtime/device/process operation was used. Only this
app's own executable and worker ran. Successful WebView teardown emitted Chromium
class-unregistration error1412; both process reports and exit codes succeeded.
The normal frontend and native executable were restored without launching the
normal visible app. Model weights remain local. Production IPC accepts neither
filesystem paths nor prompts, runtime executables or caller-selected profiles.

Import bounds, hash identity and app-local storage do not protect against a
compromised installation or operating system. Offline play is an architectural
requirement, but this run did not enforce or observe network blocking. Installer
resource placement, real picker interaction, sustained memory/thermal behavior,
narration-quality acceptance and physical-device gates remain open. No release
or full D04 acceptance is claimed. Next work is the coordinator-owned offline and
quality qualification, followed by the remaining desktop epic slices.

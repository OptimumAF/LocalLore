# Native player transcript source: contract and qualification

Scope: D07.04 prerequisite, M07.01 and M06.04/.06 support. Base accepted PR182,
`41fa2fad4c17345657c115b946e9472b1abd93cb`. Production implementation
`ab0496d6a1ceca1cad3eace70f810d8b8845a49f`; final test source
`169feb904ea0d62dfa825d83ed156b6e7480c0e9`.

This is a **data-only native Rust source**, not an executable literal policy,
model context, renderer, packing algorithm, generation grant or new UI. The
[literal-control definition](D07_LITERAL_CONTROL_CONTRACT_2026-10-25.md) still
requires separate prompt/grammar, forwarding, receipt/replay and consumer work.
Current Play2.1–2.5 and both existing state-bearing policies stay unchanged.
GitHub #29/#11/#10 own status; no full task or exit gate is completed here.

## API and authority

`context_compiler::player_literal_transcript_v1_cancelled` takes an actual
`&Engine`, exact `&Scope`, expected head, player observer and cancellation
callback. It returns `LiteralTranscriptSourceV1` or existing `CompileError`.

- Cancellation is checked first; a callback panic is cancellation. Checks also
  occur around traversal/each eligible view and after the actual history basis
  is computed. Existing bounded receipt enumeration and basis hashing do not
  become interruptible inside their own calls.
- Scope/head must match the provided Engine. A caller may explicitly obtain an
  `Engine::at_revision` prefix before extraction. NPC/unknown/empty observers
  return `Observer`; Domain2 returns `UnsupportedPolicy` before source work.
- The single eligibility visitor is extracted from existing policy construction:
  actual `actor_receipts_v2`, original `(scope, turn)` receipt lookup and exact
  complete ordered event equality before player prose attaches. Existing NPC
  policy units keep filtered events and no raw receipt prose.
- Returned units contain original scope, turn, final event revision, actual
  original Dialogue/FreeText input when present and accepted narration. Typed
  actions have `None` input. Empty history produces zero units. No opening,
  structured event/state, alias, seed prose, summary or author record is added.
- Source/unit fields are private and have only read-only getters plus
  Clone/Debug/PartialEq/Eq. Neither type implements Serialize or Deserialize;
  four compile-fail doctests enforce those trait boundaries. The source holds
  the actual opaque `AcceptedHistoryBasis`, never a serialized digest or grant.

The source snapshot remains detached when an Engine advances. Its original
basis still identifies that prefix; equality of head/scope alone cannot match
a different accepted history. No canonical mutation or inference occurs.

## Source bound

At most8192 whole units and2MiB compact UTF-8 bytes, with no truncation/partial
success. `budget_bytes()` counts exactly this private shape:

```text
{version:1,scope,head,observer,
 units:[{original_scope,turn,through_revision,original_input,narration},...]}
```

Both optional unit keys are present, using null for None. The opaque basis is
excluded. Private borrowed serde views measure the empty envelope and each
whole unit plus commas with checked arithmetic. This is a source cap, not heap
usage, tokenizer measurement, model fit or a public wire format. Model-facing
provenance filtering and full prompt/schema/repair budgeting remain future work.

The real cap fixture accepts2399 typed eight-Wait receipts with constant state,
64-character valid scope/turn IDs and large valid story time. The2398-unit
prefix is2097081 bytes; adding the next unit gives2097956 and returns TooLarge.
The real history aggregate is13151826 bytes; projection bytes are1818. Engine
receipt/history limits stay enforced. The8193-unit boundary is unmeasured:
Core's4096-receipt limit prevents that fixture through current APIs.

## References captured before production edits

The legacy fixture was frozen as source `e7d24fdf` and integrated `d04893de`.
Root ran it against unchanged Core41fa2fad, captured all six complete serialized
`PolicyCompilation` values' hashes, and anchored exactly those hashes at
`45733a80558b83948b36c520dc5f2682b45ae864` before any production edit. This
baseline passed; the same six bytes/hashes pass after the visitor extraction.

| Case | Bytes | SHA256 |
|---|---:|---|
| main player recent |13145|550f8503e5d71fb2bf5543698877dcc551c6fd6a59f6cba0ac4bf81c8e41878f|
| main player relevant |12205|25a97d1e671848b54c5568743d1f79c7d776a62e659f21bcf2d01408db36dac9|
| main Mira recent |9236|80c571c274e95cc37898ad05507ea4e8d5a7a172135c82a72982d71721967713|
| main Mira relevant |9846|cf593b39acbc0066f0337c370530cffb686a60ffa0b06c18670c23387f14fb7e|
| fork player recent |12159|29cfefee5b84662253acc55ee7773d4519eac110b04fdf3564509fbfda76e62d|
| fork player relevant |12056|bc70cd8c8e253b8798f133f057fe0e842002070da284480620f04e5e73d38209|

Original Lantern Quay fixtures use actual preview/render/commit: typed witnessed
and private events, Unicode/quotes/backslash/newline input, an NPC-empty private
receipt, real forks and repeated bare turn IDs across original scopes. These
are finite whole-DTO compatibility references, not universal byte equivalence.

## Executed checks and retained corrections

Windows NT10.0.26300 x64, PowerShell7.6.5, Rust1.93.1
(`01f6ddf75`), Cargo1.93.1 (`083ac5135`), LLVM21.1.8. Existing cached dependencies,
locked/offline, one Cargo job, debug0/incremental0, task-owned TEMP/target.
No dependencies, assets or tools were installed/downloaded.

| Check | Result |
|---|---|
| Old-Core reference capture d04893de | deliberate sentinel failure after printing six references;23.304s command |
| Anchored old-Core baseline45733a80 |1PASS,0FAIL;0.04s test/2.589s command |
| Frozen new API before implementation7a78012b | unresolved-import compiler failure;0.711s; not behavioral RED |
| First source test ab0496d6 |7PASS/1FAIL;0.21s test/10.806s command; impossible Dialogue fixture hit existing state cap |
| Corrected Wait fixture b8145357 |7PASS/1FAIL;5.97s test/7.255s command; test budget omitted four head digits |
| Corrected head-width oracle df0bcdf2 |8PASS;8.85s test/10.803s command |
| Final source169feb90 |8PASS/0FAIL;8.26s test/9.803s command; history/projection byte evidence distinguished |
| Legacy after factoring ab0496d6 |1PASS (six references);0.03s test/1.448s command |
| Initial related tests without host feature |26PASS; Host target ran0; no Host coverage inferred |
| Related tests with host feature169feb90 |30PASS:12policy+4policy review+10Play+4Host;14.407s command |
| No-serde compile-fail doctests169feb90 |4PASS;0.52s test/1.925s command |
| Core all-target/all-feature strict Clippy169feb90 |PASS;15.865s command |
| Android Rust host169feb90 |20PASS;1.77s test; no Android ABI/device execution |
| Desktop all-target/all-feature strict Clippy169feb90 |PASS;26.10s Cargo |
| Normal desktop build c18912c2 (documentation-only delta) |PASS;41.79s Cargo/41.952s command; executable built, not launched |
| Workspace Rust format c18912c2 |PASS;2.545s command |

Final eight source tests cover exact Unicode/prose/null budget keys; empty history
and excluded seed/private prose; real root replay and continuation; original
scopes/repeated turn IDs, nested prefixes, parent-future/sibling isolation;
scope/head/observer/Domain2 errors; cancellation/panic/no partial result; detached
basis and divergent same-head history; genuine source byte-cap refusal. The
deliberate callback panic prints its fixed panic-hook message while returning
Cancelled and passing the test.

The Dialogue fixture and head-width failures were test defects, not demonstrated
production regressions. Both original failed attempts remain local. No production
cap, guard or existing acceptance expectation was weakened to make them pass.
Core canonical nonmutation is compared before/after success and refusal.

Independent bounded source review by resource_metrics_review found no concrete
production defect in eligibility, old candidate encoding, budget or basis.
author_core_review acknowledged the invalid initial fixture and reviewed the
corrected genuine Wait fixture. Those reviews performed no execution and are
not human quality review or an approval fabrication.

## Reproduce

From the repository root, use owned absolute target/TEMP paths. Run serially
with other heavy work. No model, browser, device or application launch is needed.

```powershell
$env:CARGO_BUILD_JOBS='1'; $env:CARGO_INCREMENTAL='0'
$env:CARGO_PROFILE_DEV_DEBUG='0'; $env:CARGO_PROFILE_TEST_DEBUG='0'
$env:LIBSQLITE3_FLAGS=''
$env:TEMP='<task-temp>'; $env:TMP=$env:TEMP
cargo test --locked --offline -p locallore --jobs 1 --target-dir <target> --test literal_transcript_legacy_bytes --test literal_transcript_source -- --nocapture --test-threads=1
cargo test --locked --offline -p locallore --features host --jobs 1 --target-dir <target> --test m08_context_policy --test m08_context_policy_review --test m08_play25 --test d07_host_policy -- --test-threads=1
cargo test --locked --offline -p locallore --jobs 1 --target-dir <target> --doc -- --test-threads=1
cargo clippy --locked --offline -p locallore --all-targets --all-features --jobs 1 --target-dir <target> -- -D warnings
cargo test --locked --offline --manifest-path crates/locallore-android/Cargo.toml --jobs 1 --target-dir <target> --lib -- --test-threads=1
cargo clippy --locked --offline --manifest-path apps/desktop/src-tauri/Cargo.toml --all-targets --all-features --jobs 1 --target-dir <target> -- -D warnings
cargo build --locked --offline --manifest-path apps/desktop/src-tauri/Cargo.toml --jobs 1 --target-dir <target>
cargo fmt --all -- --check
```

Raw logs/process records remain local under `d07-literal-source-*`. All executed
commands recorded clean and unchanged source at exit. Public documentation uses
synthetic metadata; no raw private prompt/story, trace or personal path is added.

Local evidence integrity, SHA256 (prefix `d07-literal-source-`, suffix `.log`):

| Log | SHA256 |
|---|---|
| legacy-capture-first |6ba24693a1794a25f8306d2cd99f85bfc241ddb7b245faf3a5549032a76fa2b3|
| legacy-baseline-first |5e4d6a3cddf1a8d16200ca8d731e870cd73c6fc460625e17618d861cb5d87e1d|
| legacy-after-first |70234f793d7e334b8f6b0cbda1eb4d1601add126017e788b014565bf9de25278|
| api-before-first |f6391cfeac1b641c339c9838153b2b17f995097ede4b073f3b255346168311ee|
| api-first |516c6dfd58f3dcbb3e1ef1659186d436393f53b66b6d76def63a651fdc64a638|
| api-second |aaa5f436a4290cd067a4460ae29d2ba6a8617e63f9cbf2ebc6f3375ba1312847|
| api-third |746c2c76d9b989cb7744e23a665c1884c67699b90c8e54105b69b4a8ca4b1325|
| api-final |e327d0e61e6414faa163d249c82a130eb2f78513b7f2009408d4e6ed28786417|
| related-first |a9ed463ba15ad832f10807ed09cc03f0568998b58186e9d55e351abccf33fae5|
| related-host-final |6044dc1c1142e4508ea0d114006dae710e05d7b28fed13c57b36cc49106a0867|
| docs-final |6de5803115f1c5a9cb70984c630268580c498068ca27480ac8a9ea2df9c68e08|
| clippy-final |742b8c91895c9fb8216369227e6a98d1d8f55a6e2d456c1483c1fa31d45d6cc0|
| android-host-final |0ae5eb802e6b0606f85f11a8486a3e386a36cc3cfa8e31bc0fabf1daf56976c0|
| native-clippy-final |63314d9fbfbf4c0390c6284873cdae631f608436b7ed5abcdb14029bc02fda86|
| normal-build-final |9adc8ab352aff0bd67f52d18a8eaf6d0ca2301a3a6af86655baa72c00fe6bc81|
| format-final |e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855|

## Remaining boundaries

No native app/IPC, WebView, headless render, frontend journey or installed model
was executed for this Core-only slice. Earlier PR180 app-owned native evidence
remains historical; new Rust tests are never presented as new UI/native rendering.
There are no changed render artifacts to inspect. No new OS dialog, Android
JVM/Gradle/ABI/emulator/phone, performance/RAM, prose quality or packaging gate.
No actual generated FreeText receipt or future partial-player receipt is
fabricated for these tests. Domain2 source remains unavailable; existing
RawUnsupported and unapproved maintenance/schema proposals are unchanged.

Next runnable work: separately versioned, source-bound player literal Director
rendering/whole-unit packing using shared full-forwarded budgeting and a fixed
state-independent grammar. Executable policy/receipt/replay/Host/evaluation/UI
closure follows; adding a new enum value to current unversioned ContextPolicy
would not qualify that closure. Ordinary Play keeps its current mandatory state.
The earlier observed unrelated-library narration quality failure remains open;
this source primitive does not resolve it or establish human enjoyment.

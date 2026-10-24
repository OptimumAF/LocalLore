# V2 native producer transport fixture source — 2026-10-23

Refs #12 M08.03/M08.06 and D05–D08 consumer prerequisites (partial).
Base `9914bd425feda846a0728c15b77593f14725921b`, isolated
`test/m08-v2-native-fixtures` / `source-v2-native-fixtures`.

## Frozen producer and decoder oracles

Only three new paths are owned: `crates/locallore/tests/m08_v2_transport_capture_review.rs`,
`apps/desktop/check-v2-native-fixtures.mjs`, and this document. No existing producer,
decoder, test, schema, asset or Archive3 source changes. The Rust test/checker
oracles are frozen before adding the optional narrow file capture implementation.

The Rust test constructs actual validated Core engines and actual author children
using public prepare/apply. A read-only synthetic Persistence fixture port returns
those engines to the actual Rust Host library. Host itself emits every thin
PlaySnapshot2 and Query2 JSON reply. The fixture port is not SQLite durability and
does not fabricate a wire payload or implement another canonical owner.

Four cases cover Domain1 and authored Domain2 with the default player and a custom
actual player `hero` while an NPC remains named `player`. Each captures every one
of nine Query2 views under Player, actual-player Character, Mira Character and
Omniscient lenses, plus the NPC named player in custom cases. Each lens also has
historical boundary=1 history/knowledge/turn-diff and actual limit=1 cursor paging.
Assertions bind original-scope duplicate bare turn messages, Player-only exact
two-field marker, inherited/local source references, excluded later parent suffix,
remembered A versus private current B, reason-search exclusion, ungranted private
lens rejection, read-only canonical basis/records and zero fixture-port writes.

The Node checker imports the existing `ui/v2-view-model.ts` through esbuild without
changing it, passes every exact bound actual Host data payload to its existing
strict decoder, and derives optional selected-player identity only from the
coherent decoded native thin snapshot. It verifies case/view/lens coverage,
paging continuity, marker/message identity and observed/world values. It does not
replace a failing producer/decoder envelope with a mock expected payload.

## Capture boundary and execution status

The optional capture uses only `LOCALLORE_V2_FIXTURE_DIRECTORY`, an
existing absolute directory, and one fixed `v2-native-fixtures.json` filename.
It must serialize at most 1MiB of synthetic fixture data before create_new and
must refuse overwrite. The default Rust test performs all producer assertions
without writing any file. The Node checker reads only that supplied bounded
regular fixture file, bundles the known local decoder in memory and emits a
compact count/hash report. No evaluation, shell, arbitrary file API or server is
exposed through the app or Host contract.

All new Rust and Node tests are currently **UNCOMPILED/UNRUN**. This is source
evidence only. Future actual execution establishes a Rust Host-library transport
producer/decoder check; it does not establish native IPC, WebView rendering,
desktop interaction, durable storage, inference or real model acceptance.
Root owns every runtime slot and integration/consumer fixes. Any concrete strict
decoder gap must be reported, never hidden by weakening these assertions.

## Reproducible coordinator commands (not executed here)

Use an unused existing directory under the repository's ignored `target/`.
PowerShell, from the repository root:

```powershell
$v2FixtureDir = Join-Path (Get-Location) 'target/v2-native-fixtures-source-cohort'
New-Item -ItemType Directory -Path $v2FixtureDir -ErrorAction Stop
$env:LOCALLORE_V2_FIXTURE_DIRECTORY = $v2FixtureDir
cargo test -p locallore --features host --test m08_v2_transport_capture_review
Push-Location apps/desktop
node check-v2-native-fixtures.mjs
Pop-Location
Remove-Item Env:LOCALLORE_V2_FIXTURE_DIRECTORY
```

The directory must be new for a new capture. If the fixed file already exists,
the Rust test fails rather than replacing earlier evidence. To rerun producer
oracles without writing, unset the environment variable and run the same Rust
test. The Node checker requires the variable and fixed captured file. Generated
fixtures remain local and ignored by default through `target/`; do not publish
capture output or treat a capture run alone as a decoder pass.

The first immutable producer/checker oracle commit is
`9d6e1141b6df3cd525e65c6461a48076f327f2ce`. The later capture implementation adds
only a test-local fixed filename writer, after all source oracles were frozen.

## Source handoff and qualification limits

Capture implementation commit: `c629aa059e8e3e8836a545f006c1d88f516f478f`.

| New source | SHA-256 |
|---|---|
| Rust capture test | `909b55f9362afd1e419b4b5d253d2e8756897fe9b978bb59c368a465375ef6db` |
| Node strict-decoder checker | `bfb7df0e1789833bdac2a88db1cb8f650dc63f09c801d5f328d209a11253e1bb` |

Executed source-only checks: scoped `rustfmt --edition 2021` and `--check` on the
new Rust test, `git diff 9914bd4 --check`, exact changed-path inventory and
`git check-ignore target/v2-native-fixtures-source-cohort/v2-native-fixtures.json`.
These passed; the proposed output path is ignored. No capture file was generated.
Rust compilation, Rust producer assertions, captured fixture byte count, Node
syntax/bundle/decoder execution and Node formatting checks are all still unrun.
Source inspection found no additional concrete decoder mismatch to assert as a
runtime failure; successful closure remains unknown until the unchanged strict
decoder consumes actual captured bytes. No native IPC, WebView/headless image,
SQLite durability, provider or model check is supplied by this packet.

The synthetic read-only port explicitly rejects canonical writes, while the
test verifies original basis/records and zero write attempts after all granted
and refused inspection reads. It adds no transport contract or app test hook.
The custom-player fixture retains old seed evidence IDs unchanged and valid;
only the selected player and story scope differ, with the original player actor
retained as a real NPC. Observer comparison in the Node checker uses kind/ID,
independent of JSON object property order.

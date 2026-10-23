# D05 provenance and context repair - 2026-10-22

Refs #26 D05.03/.06/.07, scoped repair claim6358203360. Source review found that
removed-field Why queried the after-head, where the field no longer exists.
Event/message rows also lacked matching field-provenance keys. The Return to play
button merely closed the browser while leaving Story Lab active, and derived
query text/revision could survive a story/lens change. A source helper could select
a new story's coincident Event1 after its own delayed page had been discarded.
These are corrected in **78e55ff44638900257b2c5274ea6e412eac58a79**. No shared,
native, runtime, generated schema/type or canonical behavior changed.

Removed fields now show their prior provenance at before_revision, explicit
absence at after_revision and separate completed-turn history. For the deleted
potion, the origin is the seed at r0; the accepted Give event belongs to r1.
The former field is never labelled current or searched in after-head provenance.
The turn-history action first resolves an observer-permitted boundary event, then
uses that visible event's turn ID. It never consults raw Player receipts to infer a
hidden NPC turn. If the boundary event is unavailable, it says so. A multi-event
turn is not assigned a single inferred cause. Event and message actions open their
accepted source records; missing evidence is unavailable and an already displayed
Provenance row has no misleading Why loop.

Return to play now actually selects Play/Player, closes the browser and clears
the legacy private inspection. Story/lens changes reset search, historical
selection and change-trace state, including derived private Why keys. Source
navigation captures its query epoch and checks it after awaiting before selecting
a record; the caller also checks that epoch before posting an accepted-source
notice. An old source action cannot select a new story's Event1 merely because
the event sequence matches.

The definitive native journey passed **93 distinct assertions,14 app-owned PNGs
and actual executable restart**, recorded from clean78e55ff. It used a fresh
synthetic SQLite database, the real frontend/Controller/native IPC, and only the
explicit fake provider to establish fixture history. No real model was loaded or
called. Existing checks still prove browsing preserves canonical state, story time
and live-worker counts, with secret/observer isolation and API denials.

New native checks exercise the actual deleted-potion Why at r0, absence at r1,
accepted Give history with that same boundary, event/message source navigation,
clearing a Lab-derived relationship key on observer change, actual Return to
Play/Player, and clearing query parameters on story change. Existing fixed
capture labels were reused; no native harness permission or API expanded.

The actual-controller regression also passes removed-field and event/message
navigation, no-source messages, hidden boundary refusal without a hidden turn-ID
lookup, Return to Play, parameter clearing and a controlled held-source lookup:
storyA/Event1 -> attach storyB/Event1 -> releaseA must leave B unselected with no
old accepted-source notice. These controlled responses test consumer behavior;
they are distinct from the native authoritative fixture.

Commands actually run, with task-owned D target/temp/artifact variables and
CARGO_PROFILE_DEV_DEBUG=0 / CARGO_INCREMENTAL=0:

```powershell
node apps/desktop/check-inspection-controller.mjs
node apps/desktop/inspector-harness.mjs
npm --prefix apps/desktop run check
npm --prefix apps/desktop run format:check
cargo build --manifest-path apps/desktop/src-tauri/Cargo.toml --locked --offline --target-dir <owned-D-target>
git diff --check
```

All passed. The full frontend check includes strict TypeScript, generated-request
and hostile-wire checks, existing export/model controller regressions and normal
asset hook absence. Normal frontend/default executable were restored after the
native run. Rust unit/Clippy and legacy feature results remain the earlier
[baseline evidence](D05_NATIVE_VERIFICATION_2026-10-22.md); no Rust source changed
and those suites were not rerun for this UI-only repair. The separate model-refresh
regression50946f8 and root's D04 production fix remain outside this repair.

The [committed evidence](D05_NATIVE_PROVENANCE_EVIDENCE_2026-10-22.json) preserves
the exact source/engine/Host/storage/frontend/native executable SHA256 map and
reports. Local task-owned D artifact suffix:
desktop-inspector-artifacts/inspector-native-8d75b94a-d912-43d9-805c-f36f3f8f377d.
Summary SHA256:
87dc3edeeea5ba6c426a4fba2af5b80640bac1ccf973ccf5ff7bd839c17acdb5.
Compare Git-normalized source text when CRLF differs between checkouts.

The final d05-diff capture visibly separates prior r0 provenance, seed origin and
r1 absence. d05-source shows accepted Give(potion,to=mira,quantity1), turn/time/
witnesses and the r0->r1 change boundary. d05-pagination shows Play selected and a
Player-only current lens with cleared filters after returning. All14 semantic
captures record no horizontal overflow; captured JSON contains no home paths.
These are application-owned CapturePreview renders, not desktop screenshots.

No desktop input/activation/capture, CUA, device/model/protected-process activity,
native/runtime/shared editing or release occurred. Full D05 acceptance, advanced
M06/M07 memory, hostile-renderer security, assistive-technology qualification and
long-history performance remain open. The UI reports absence and withheld evidence;
it does not invent a causal oracle or new knowledge-transfer authority.

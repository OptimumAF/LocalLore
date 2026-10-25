# Inspect local memory comparisons

The desktop Story Lab has a dedicated reader for the existing version2 memory
comparison protocol. It keeps the original built-in and curated evaluation
views. Shared Rust validates the selected experiment and serves its evidence;
the frontend does not import the experiment into a live story.

Implementation and qualification are separate: see the
[source-bound reader checks](D07_COMPARISON_READER_QUALIFICATION_2026-10-24.md)
and [native interface contract](D07_COMPARISON_NATIVE_READER_CONTRACT_2026-10-25.md).
Neither document closes D07.06 or establishes model quality or Android parity.

## Open a report

1. Enter Story Lab and acknowledge spoilers. Under **Memory comparison reports**,
   choose a comparison report folder. Select the actual cohort directory
   containing `run.json`, `run.lock`, and its source databases/checkpoints.
2. The application's native folder picker warns that original inputs, character
   truth, prompts and outputs can be private. Its **Inspect private evidence**
   affirmation authorizes that source for this window. Cancelling grants nothing.
3. **Show private report** displays the original paired/rollout report, source
   match, profile, results, known/unknown role counts, timings and limitations.
   Scripted results are explicitly synthetic. Optional missing values stay
   unavailable; context token estimates are not measured token counts.
4. Select a turn and arm. Inspect its actual before/after state through Query2,
   or inspect its accepted receipt, retained context capture and recorded role
   outputs in the omniscient lens. Guard-only or recovered rows retain their
   actual missing evidence; no receipt, role count or capture is invented.
5. The reader's player, Mira and Sable lenses use Rust-filtered queries. Changing
   lens removes the full report and raw artifact presentation. Inspect again
   explicitly. Inspection never changes knowledge or generation permissions.

The summary is the **last fully validated snapshot** at open. Each selected
evidence request checks the manifest, complete selected checkpoint and actual
selected source/bytes again. Its Query2 engines are bound to before-input,
after-output and mechanical fingerprints. Unrelated diagnostic file changes
are not a continuously refreshed whole-report health check. Close and reopen
to validate the entire cohort again. Corruption is an error, not an empty pass.

Query2 currently returns its first64 rows only. A next cursor is labelled as
additional unavailable paging. Unsupported summary/retrieval-index views remain
explicitly unsupported. Character-owned player-message decoding has no trusted
experiment player-ID metadata; it stays closed rather than borrowing the active
game's identity. Use the separate Player lens for player-visible messages.

## Close and recover

Opening holds the shared experiment's existing cooperative lock and pinned
directory handles. Close the reader before running or resuming that cohort
elsewhere. One source per window and the existing evaluation worker serialize
read work with built-in/curated execution. No model is reserved or run by reading.

**Close report / stop opening** abandons pending publication and releases eventual
handles. It does not forcibly close a blocking OS picker or interrupt a disk read.
A late successful read cannot reappear after close or a surrounding gameplay
session, scope, revision, Lab or native-window context change.

An unavailable opening acknowledgement retains the same client identity.
**Check opening status** recovers that request without opening another picker.
This is in-memory reader recovery, not an uncertain canonical write. After process
restart, select the cohort again; old tokens are invalid.

Idle expiry is checked on access after900 seconds. An untouched open window can
retain the lock until the next access, explicit close or shutdown. There is no
background expiry timer or automatic deletion of retained experiment files.

**Comparison execution and isolated selected-case reruns remain unavailable in
this reader.** Source match is not an execution grant. Historical valid reports
remain viewable with their original source mismatch and bytes. The existing CLI
producer is documented separately in
[current comparison implementation](../eval/D07_CURRENT_COMPARISON_IMPLEMENTATION_2026-10-23.md).
It compares state+recent-transcript with state+relevant-memory policies; this
does not claim the separate literal transcript-only baseline gate is complete.

## Verify without desktop control

Use existing provisioned dependencies. From `apps/desktop`:

```powershell
node check-comparison-reader.mjs
node check-comparison-main-review.mjs
node check-comparison-capability-review.mjs
node verify-frontend.mjs
```

The first checker exercises real decoder/controller code with synthetic transport.
The panel callback review uses test-only React hook/JSX substitutions. These are
not native IPC or rendering. The full verifier also builds normal frontend assets
and checks that development hooks are excluded.

The fixed app-owned native harness requires explicit absolute task-local output
and source-owned target directories. Its output root must already exist:

```powershell
$env:LOCALLORE_D07_COMPARISON_READER_ARTIFACT_ROOT = '<absolute-existing-private-artifact-root>'
$env:LOCALLORE_D07_COMPARISON_READER_TARGET_DIR = '<absolute-source-owned-native-target>'
node comparison-reader-harness.mjs
```

This command requires a clean checkout, builds locked/offline, creates only a new
synthetic workspace and real shared scripted producer cohorts, and runs initial
and separate-process restart journeys. It uses the actual frontend controller and
native IPC in hidden, unfocused WebView2. Its fixed native picker doubles never
automate an OS dialog. Captures come only from application-owned WebView2
`CapturePreview`, with semantic snapshots and bounded local stdout/stderr; no
desktop input, activation, desktop screenshot, browser debugger or arbitrary
execution endpoint is used. Inspect every resulting image before acceptance.
The launcher verifies original cohort file hashes after each process.
It also checks every semantic-version2 capture against its actual inspected
scope/revision/observer, selected query controls, receipt and error. Live gameplay
context is recorded separately. Pending operation IDs are actual, explicitly
unknown after lost acknowledgement, or null when no operation is pending.

Artifacts stay local under the explicit output root. Repository defaults ignore
`artifacts/`, databases and generated bundles. Use synthetic fixtures and do not
publish private stories, prompts, paths or assets. The harness runs no model,
downloads, Android runtime or device. Default PR checks do not require it.

After a harness run, rebuild the normal frontend and native application without
the development feature before using or qualifying the normal executable:

```powershell
node build.mjs
cargo build --manifest-path src-tauri/Cargo.toml --locked --offline --jobs 1
```

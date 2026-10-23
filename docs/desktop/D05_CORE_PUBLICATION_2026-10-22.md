# Read-only shared inspection query publication

Refs #26 D05.01–.05/.07 partial; #10 M06.06 provenance/secrecy prerequisite.
This focused boundary adds one shared query over validated Engine snapshots and
its existing Host-v1 dispatch. The desktop workspace follows separately. There
is no new canonical projection, storage schema, memory system, model call or
generation privilege. Accepted main at integration is PR #54 merge513a770.

Functional inputs are the already tested D05 integration `db3e6ed`, including
privacy correction `4b7f59c`. The generated schema is the same JSON values with
the explicitly delegated Prettier-only formatting `30827e1`. Current native
model/runtime and controller fixes from main remain preserved. Older D05 query/
Host/review reports describe their exact earlier packets; this report records
the final focused boundary and executed correction tests.

## Contract and privacy

`inspection_query {session,query}` requires exact open session, scope and current
expected head. Optional at_revision rebuilds a completed root-history boundary
from accepted receipts, rather than relabeling current state. Views are Profiles,
History, Relationships, Knowledge, Promises, Provenance and TurnDiff. Summaries/
RetrievalIndexes return explicit unsupported status; actual fork history is also
unsupported at this stage. No query creates a draft, advances time, invokes a
provider or writes accepted state. It clones/reloads one coherent durable head,
then derives pages outside the Host mutex.

Player, exact Character and Omniscient lenses use shared eligibility before
search, counting, pagination or cursor construction. Trusted Host construction
supplies Lab privilege outside request JSON; the wire cannot grant it. The
separate UI acknowledgement is not an engine authorization token and does not
change the gameplay player or what generation can access. Cursors bind scope,
current head, historical boundary, observer, view, search, limit and visible rows;
their checksums detect stale/edited reuse and are not authentication.

The original independent review found two real leaks. The corrected implementation
and adversarial tests now enforce:

- An NPC's witnessed effect does not grant access to raw player intent or narrator
  transcript. NPC history contains only eligible accepted Event rows; scoped
  spoken statement events remain statements, not canonical facts.
- An unwitnessed promise completion cannot change the creditor's visible status,
  add completion/source-presence metadata, or leak through Provenance, search,
  counts or TurnDiff. Visible completed_by evidence is filtered first; known
  promise/clock facts can still derive open/overdue status. Player/Omniscient
  canonical fulfillment remains inspectable.

Typed rows preserve seed/event/withheld sources and distinguish truth, statements,
beliefs, observations and discoveries. Unsupported narrative-profile numeric
fields are absent rather than invented. Incoming seed commitments remain private
until eligible; directed relationships preserve their direction/evidence.
Bounds:64 rows/page,64KiB serialized page,256-byte search,128-byte cursor.
Candidate collection/replay precedes final page bounds: these are API limits,
not measured whole-process memory guarantees. Long-history context/memory work
belongs to #11 and is not claimed complete by this query API.

## Exact focused verification

Windows11 Pro10.0.26300, Rust/Cargo1.93.1; dev/test debug0, incremental0;
locked cached offline dependencies and task-owned D build/temp roots.

```powershell
cargo test --workspace --locked --offline --target-dir <task-build>
cargo clippy --workspace --all-targets --locked --offline --target-dir <task-build> -- -D warnings
cargo fmt --all -- --check
cargo run -p locallore --features host --example host_schema --locked --offline
cargo test --manifest-path apps/desktop/src-tauri/Cargo.toml --locked --offline --target-dir <native-build>
```

**177 Rust workspace tests passed,0 failures**, including16 query-module cases
and2 actual Host/SQLite cases. Strict all-target workspace Clippy and rustfmt
passed. Actual Rust schema output parsed equal to the committed generated schema.
The unchanged current desktop frontend passed `npm run check` (strict TS, schema/
controller/error/keyboard/normal-bundle checks, including terminal model refresh
regression) and `npm run format:check`. Current default native app compatibility:
17 passed/1 explicitly ignored privilege-dependent reparse test; no native app
was launched in that compatibility check. The reparse case has separate executed
evidence in PR #54; it is not counted as executed again here.

The first full workspace attempt failed in the accepted inspection_review test
constructor: parallel tests received identical PID/coarse-clock temporary paths
and create_dir returned AlreadyExists. Three affected fixture constructors now
include atomic per-process sequence suffixes (inspection_review, play_host and
inspection_query_host). Assertions and parallelism remain unchanged; the complete
177-test run then passed. This is test isolation, not a retry-until-green policy
or a production storage change.

Cases cover hidden canaries/source presence, visible identity stability, NPC
transcript isolation, private completion, lens grants, exact cursor binding,
old-state replay, completed/partial/future boundaries, statement-versus-fact,
directional relationships, row/byte limits, immutable concurrent snapshots,
original v2 input with no provider, and actual SQLite head reload/read-only access.
The workspace run includes existing engine/storage/Android bridge tests, but no
new APK/device/physical-phone qualification. Model-free query tests are not
native UI or real-model execution. The separate UI branch's81 assertions/14
images/restart evidence and ongoing provenance/navigation repairs stay distinct.

Full D05 depends on the useful desktop workspace and missing shared memory
capabilities. No task checkbox, M06/M07 milestone, release or whole-epic gate is
accepted by this partial PR. Next: reviewed desktop query workspace, then D06
production trace lifecycle and the shared bounded context compiler.

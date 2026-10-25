# Opt-in receipt-backed candidate setup

M05.05 prerequisite / M01.05 support, stacked on the independently qualified
synthetic Android transaction. This debug experiment does not select a release
backend or supported phone. ADR-0011 remains proposed pending owner acceptance.

## Frozen shared access interface

`CandidateModelAccess` provides pure `plannedFiles()`, suspending `installed()`
and `import(open)`, and synchronous IO-only `admitRuntime()`. Existing profiles
use `PublicationCandidateModelAccess(LocalModelStore)` with unchanged native
publication semantics. Only explicit `localLoreModelReceiptVerification=true`,
with LiteRT/model-setup/model-volume verification enabled, selects receipt access.
False, incomplete, mixed picker and release configurations refuse. The package
remains the isolated `.modelvolumeverify`; use a separately admitted fresh target,
never replace old held installations to obtain a passing run. Build output is
separate from the existing volume profile.

The real candidate keeps its exact built-in Gemma identity, worker source,
runtime graph and budgets. Root derives the internal no-backup control child
`local-model-receipt-control-v1` and external app-files data child
`local-model-receipt-data-v1` through trusted Context and the existing exact-one
`AndroidModelVolume` selection. Existing native/publication model roots are not
adopted or migrated. Presence of the prior removable candidate root refuses the
new route. Canonical story files remain internal. The existing owner gate,
volume identity/inodes, capacity floors and sticky media refusal remain in force.

`ReceiptCandidateModelAccess` owns one `ReceiptModelTransaction`; it delegates
import and full reopen. Core owns all record parsing and runtime validation.
Construction and `plannedFiles()` only plan trusted paths. The Android callback
rejects Main-thread runtime admission before touching the filesystem. Transport
construction only captures paths/callbacks; actual validation remains deferred
to the existing worker's IO path.

## Runtime acceptance

Core adds pure `plannedFiles()` and synchronous, noncreating `admitRuntime()`.
It uses the same global process reservation and persistent OS-lock protocol as
import/reopen. Require the current zero-byte regular marker, exact bounded
receipt and owner, strict roots/whitelist, regular expected-size model, safe
existing cache, and volume/capacity admission. Share structural validation with
the full transaction; do not duplicate a weaker record parser in the adapter.

A per-transaction immutable verification stamp is published only after a fully
successful full-hash import/reopen, including return of all source/channel/lock
closes. Compare current root/file identity, expected size and relevant modified
metadata against that stamp at runtime; cache contents remain opaque and its
directory identity, rather than child-write timestamps, is checked. Before
reverification and on failure/cancellation, clear that instance's stamp. A late
accepted import that reports cancellation has no runtime authority until a full
`installed()` recheck succeeds. No stamp means refusal. Metadata admission does
not attest model bytes or hostile concurrent OS mutation; the unchanged worker
must still full-hash before SDK construction and recheck admission before
initialize/conversation/send. No repeated full-artifact hash belongs to each
small metadata callback.

## Bounded synthetic qualification

Only the explicit receipt debug build includes fixed nonexported setup fixture
activities and instrumentation. Their original 63-byte identity/closed case
roots are trusted source constants, never Intent/provider/model configuration.
They exercise the real receipt access class and production setup ViewModel,
with real Compose Cancel/Recheck controls. Fixed source callbacks through
`beginPicker`/`completePicker` do not qualify DocumentsUI/result delivery.

The real candidate factory must also be observed on IO with the fixed real
identity and planned Context roots, refusing absent/unaccepted state without
SDK entry. Synthetic successful imports do not establish successful real-model
provisioning or inference.

The initial cohort covers accepted import/recheck/recreation, cancellation
before/after acceptance, and original-scope disposal while a source read holds
ownership. Cancellation must retain STOPPING/BUSY until actual read/close return,
never publish stale READY, and preserve unaccepted bytes. A separate later
instrumentation process verifies different PID/start identity and source-free
full reopen; Activity recreation is not process restart. Proofs and exact
controller budgets are frozen separately before any guest operation.

No automatic cleanup, source adoption, receipt fabrication, model transfer or
SDK invocation follows merely from a synthetic pass. Existing A/#117/#119,
reference-phone, cache/privacy, ARM64/16 KiB and sustained/quality gates remain.

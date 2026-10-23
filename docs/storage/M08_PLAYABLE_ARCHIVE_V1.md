# M08 playable archive v1: shared prerequisite

Status: implemented for independent review; M08.04/.06 and D08 remain partial.
This is the Store-owned portable data boundary, with no native picker, Host
command, Android import, archive browser, or model loading integration.

## Privacy and transferred history

There is one mode: **full private, whole story**. It includes the unchanged seed
and rules, every exported branch, hidden facts, original accepted requests,
narration, proposal/outcome/event data, provenance, model/profile references and
accepted Play stage timings. It is unsuitable for a Player-redacted share.
Literal story text remains data; a consumer must render it inertly.

Only committed history transfers. Draft, running, cancelled, failed and stale
workflow rows and their keys/status do not. Separate raw prompt logs, private
traces, derived-memory caches, model weights, files and executables do not
transfer. A consumer must display this limitation and create a new session
without carrying old pending operation IDs into the imported workspace.
Same-Store terminal-key retry guarantees are unchanged.

The transcript is derived from each original accepted receipt's request intent
and narration, under `accepted_request_intent_and_narration_v1`. It is not a
second mutable ledger. Original `Receipt.play`, including `StageTiming`, is
preserved. Model references are metadata; importing never loads or downloads a
model. Replay and continuation validation use the real Engine without inference.

## Public Rust API

`Store::export_archive(story_id, cancel)` returns `PlayableArchive`, whose bytes
and preview have read-only getters. A read transaction pins one SQLite snapshot
before enumerating branches and replaying their source ledgers. A concurrent
later commit does not enter the capture. Export writes no file.

`validate_archive(bytes, cancel)` opens no database or path. It returns an opaque
`ValidatedArchive` with no public construction, mutation, cloning or Deserialize
implementation. `preview()` exposes identity, heads, counts, byte count, payload
hash and the full-private/accepted-only warning. This token is a native Rust
capability, not a renderer-supplied JSON authority.

`Store::import_archive(validated, cancel)` consumes that token. An IMMEDIATE
transaction checks story identity and capacity, inserts original canonical rows,
replays every inserted branch through the existing strict Store loader, verifies
the rebuilt accelerators, then commits. Cancellation or any SQL/validation error
rolls back. It neither clears nor remaps an existing story.

An existing story ID **always conflicts**, including an identical archive after
an uncertain first acknowledgement. This prevents overwrite and duplicate
identity effects; it does not promise that repeating an import returns success.
A future copy/remapping feature needs explicit shared rules, since changing
receipt scopes would change their accepted identity.

## Versioned representation

One UTF-8 JSON document, no ZIP/path entries or SQL. All DTOs reject unknown
fields, and the existing Engine unique-key parser rejects duplicate JSON keys
recursively before typed decoding, including nested seed and receipt objects.

The envelope has `format: "locallore-playable-archive"`, `version: 1`,
`canonicalization: "locallore-json-v1"`, `privacy: "full_private"`, `payload`
and `integrity`. The payload has:

- Domain version and source database schema version, unchanged story ID/title/seed.
- Transcript convention, branches sorted strictly by original branch ID, and
  exact sorted policy/prompt and model/profile reference sets derived from receipts.
- For each branch: original ID, parent ID, fork revision, current head and only
  its original local accepted receipts. Inherited receipts remain at their source
  branch; they are never copied or relabelled into children.

Integrity contains SHA-256 of payload and seed and, in the same branch order,
each branch's local receipt array and reconstructed Engine canonical state.
`locallore-json-v1` recursively sorts object keys by Rust UTF-8 string order,
retains array order, uses serde_json scalar escaping/number encoding, and emits
no whitespace. It does not depend on serde_json's optional object insertion-order
feature. State bytes use unchanged `Engine::canonical_bytes()`.

Checksums prove internal consistency, **not authenticity**. Anyone can construct
a different internally valid story and recompute them. A forged accepted outcome
must still pass real Engine seed validation, original-scope restore/fork and
strict continuation; a checksum alone grants no acceptance authority. Supported
historical Play policies use the existing recorded-history validator, never a
fresh prepared-commit bypass. Unknown/future formats, policies and versions
fail closed.

## Validation and limits

Before import writes, validation checks identifiers, sorted uniqueness, one real
root, parent existence, cycles/depth, parent heads, completed-turn fork boundaries,
every original receipt, all branch canonical heads, checksums and exact references.
Nested rewinds before a parent's birth use the same lineage-prefix semantics as
the durable Store loader. Parent futures and sibling events cannot become child
history. Projection bytes are reconstructed accelerators, not archive authority.

| Bound | v1 limit |
| --- | ---: |
| Input/output JSON | 32 MiB |
| Whole-story branches / lineage depth, root inclusive | 32 / 32 |
| Whole-story local receipts / encoded receipt bytes | 4,096 / 16 MiB |
| Individual encoded receipt | 64 KiB |
| Encoded seed / each canonical projection | 128 KiB / 256 KiB |
| Unique model/profile references / policy references | 64 / 64 |
| Story ID and branch IDs | 1–64 ASCII letters, digits, `_`, `-` |
| Story title | 1–256 characters, no NUL |

Additionally every replay path must meet the existing Store history-owner budget,
which counts serialized request **and** response bytes. A nominally smaller
receipt-only archive can therefore be refused if that stricter owner budget is
exceeded. Import rechecks the existing 256-story admission cap under its writer
transaction. The smaller archive branch cap does not lower the normal Store's
256-branch cap: larger stories are explicitly not exportable in v1.

Fixed error categories are `Malformed`, `Unsupported`, `Integrity`, `TooLarge`,
`Conflict`, `Cancelled`, `Busy`, `Full`, `Database`, and `NotFound`; they do not
echo story content, SQL or paths. A panicking cancellation callback cancels.
Callbacks occur between bounded work units; JSON parsing, a single Engine replay,
hashing and SQLite operations do not promise immediate preemption or a hard RAM
or wall-clock limit. Import holds the writer while it verifies the inserted story.

## Remaining gates

- Independent implementation review and central integration checks.
- Native preview/consent tied to the exact bytes/token and window/session lifetime,
  bounded nonoverwrite file publication, and inert untrusted preview.
- Real desktop/Android export/import/reopen/continue round trips and failure UX.
- Archive-specific process-death/disk-full injection and broader platform evidence.
- Explicit shared lineage support wherever context/compiler/query/cache callers
  still return Unsupported; this archive does not bypass those guards.

No archive/correction UI, branch switching command, model portability, encrypted
export, archive authenticity, or full M08/D08 acceptance is claimed.

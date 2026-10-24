# M08 desktop native author broker: source contract proposal

2026-10-23. Future M08.03 / D08.05 / D05 prerequisite. Base
`7dc7bdd8d6963ac2a619028148993ad369796386` contains the released, uncompiled native
Host/Repository port. This separate packet is not part of PR #131. No app, model,
device, desktop, compiler or tests have been executed for this proposal.

## Exact closed boundary

Reuse public `Engine::parse_unique_json(raw.as_bytes(), 65536)`: duplicate keys at
any depth, malformed JSON and oversized input fail before native construction.
No new parser, Serde dependency, canonical deserializer or renderer plan exists.
All operations receive a private raw String, not a parsed Value whose duplicate
members have already been discarded. Every object has exactly its specified
keys. All numeric fields are JSON unsigned integers (not fractional/exponent
forms) in the JS-safe range through 9,007,199,254,740,991; version is exactly 1.
IDs follow actual Core ASCII identifier limits (64 bytes; session 128 bytes).
Strings retain valid controls/Unicode; Core owns semantic/string/input limits.

```text
prepare: {version:1, session, input, author_consent:true}
commit:  {version:1, session, input, preview_token, preview_sha256, confirmed:true}
lookup:  {version:1, input, author_consent:true}
input:   {version:1, parent:{story,branch}, expected_parent_revision,
          fork_revision, child_branch,
          operation:{op:"replace_fact_proposition",fact,expected_proposition,replacement},
          reason}
```

Input is constructed field by field as Serialize-only `AuthorCorrectionInputV1`
and validated by Core. The entire wrapper is bounded to 65,536 bytes separately
from the unchanged generic Host input limit. Unknown/extra keys, duplicate keys
including escaped duplicates, wrong version/types/consent, unsafe integers,
invalid IDs, same child/parent, invalid fork/head and Core-invalid input fail
closed. Consent is a deliberate native workflow check; it does not mint the
Host's independently required native Story Lab grant.

Prepare output is EXACT:

```text
{version:1,kind:"author_preview",session,preview_token,preview_sha256,
 preview_json,expires_seconds:600}
```

`preview_json` is UTF-8 from the actual held Core preview bytes, not pretty-printed
or reparsed reconstruction. `preview_sha256` is native lowercase SHA-256 of those
exact bytes. Token uses the existing native random UUID generator. No bytes,
token or digest becomes canonical/edit authority. Full output JSON remains at
most existing Host MAX_OUTPUT 262,144 bytes. Private preview includes full input
and potentially private truth-source data: author-view-only, never logs, model
context, player/NPC snapshot or export by default.

Commit output is EXACT `{version:1,kind:"author_commit",session,outcome}`;
lookup output is EXACT `{version:1,kind:"author_lookup",found,outcome}` (null when
absent). Outcome uses the actual native Host version-1 result, without canonical
rewrites or fabricated success.

## Same worker and native lifetime

Proposed `AuthorManager::new(host:&Arc<Host>, lease:&Arc<WindowLease>, epoch:u64)`
returns a memory-only owner bound to Weak Host/Lease identities and the captured
valid epoch. It holds at most four actual non-Serde/non-Clone Host preparations,
each expiring after 600 seconds. Start methods additionally take actual Host,
lease, epoch and SAME Arc<ArchiveBroker>, so foreign Host/root/window reuse fails
by pointer identity before private data can publish. No path/root string from
the renderer can create authority. Captured session, exact full input, exact
preview bytes and digest must equal the stored capability before commit.

`prepare_start`, `commit_start`, `lookup_start` schedule exclusively through the
existing `ArchiveBroker::start` worker. Existing status/cancel DTO and terminal
retention remain unchanged. There is no new thread, timer, server, Store open,
SQL, schema, journal, registry of serializable plans, or automatic retry. Native
Host Weak/session/work-owner fences and Store owner/full-basis/transaction checks
remain authoritative. Any accepted committed return wins late cancellation;
there is no post-commit work.check/phase check that can turn it into Cancelled.
Window invalidation still suppresses stale publication through the existing
broker. Explicit `retire(epoch)` clears retained private caps; every use checks
epoch/Weak lifetime/TTL and prunes expired/inaccessible caps. Future application
teardown must wire retire before exposure; no such existing lifecycle code is
changed in this packet.

Root-approved simple consumption decision: a valid,
fully bound second-consent commit attempt removes its cap **before** starting the
worker, including ArchiveBusy/spawn refusal. A retry after that refusal requires
a new preview; it never reconstructs a capability or writes on retry. This avoids
stranding a cap when ArchiveBroker's pre-closure cancellation check prevents the
closure from running. No ArchiveBroker helper change is required. Cross-owner
attempts cannot destroy a foreign capability. Full-input/session/digest mismatch
reports AuthorPreviewMismatch **before consumption** and preserves the capability.
This explicitly supersedes the initial proposal's mismatch-retirement behavior;
the frozen tests are updated before production under Root's decision. Missing/
expired/consumed token reports UnknownAuthorPreview. Consent/shape refusal occurs
before capability consumption. A bounded native-only
`discard_preview(&Arc<Host>, &Arc<WindowLease>, epoch, session, token) ->
Result<bool,String>` checks the same owner/window/session/token fences and removes
an unused matching cap (false when absent), freeing the four-cap limit without a
ten-minute wait. No Tauri discard command is registered. This design decision is
not runtime implementation acceptance.

Explicit retirement also fences a cap already consumed into an admitted worker:
the manager's private checked generation changes and is included in fresh native
cancellation admission before/during apply. This is memory-only lifecycle data,
not story authority or a new persistent owner. TTL is rechecked before/during
fresh apply. Retirement after actual commit cannot demote its recorded result.
An additional frozen actual-Store oracle retires or destroys the window while a
bounded test gate holds the worker before apply; no child or stale publication
is permitted. This closes a source-detected lifecycle seam, not an observed RED.

Latest-operation status recovers a lost start/result acknowledgment only until a
later operation replaces that terminal slot. After consumption, explicit new
lookup performs actual Host exact-input readonly lookup; it needs no live parent
session/head and respects retained ancestry/tombstones. Missing child is not
success and does not trigger write. Metadata-hint recovery/privileged derivation
of committed full input is a separate unavailable prerequisite. No prose journal
or inferred outcome is introduced.

## Frozen test plan before implementation

Use actual Repository/Store/Host histories and the same ArchiveBroker/WindowLease,
not fake receipts or test-only canonical SQL. Freeze new tests before production:

- Strict unknown/duplicate/oversized/numeric/consent and full nested input cases.
- Exact private UTF-8 preview/SHA/keyset/cap, readonly parent, no child; two distinct
  confirmations, same-owner real commit, exact lookup, same result after lost ack.
- Foreign Host/window/epoch, edited session/input/digest, expired/retired/consumed
  caps, bound four-cap limit and explicit cleanup.
- Actual parent advance produces Stale; actual queued gameplay produces Busy
  without changing its key. Shared worker ArchiveBusy and consumed-attempt policy.
- Cancel before apply leaves no child and retires its cap; late committed result
  stays committed. A cfg(test)-only bounded channel gate in this NEW module may
  synchronize before/after apply; no runtime hooks or arbitrary execution API.
- Explicit readonly lookup after parent advance/retirement, full-input mismatch,
  absent/tombstoned child, and no author/NPC knowledge mutation from inspection.

Only new `author_commands.rs`, new `author_commands_review.rs`, one test-only
module declaration in main.rs, and this new document are owned. No Tauri command
registration or generated binding/schema/UI changes. The module is compiled only
under `#[cfg(test)]` until independent Core/Store/native checks and application
decoder/second-consent/current-context closure. Mock/headless/JVM/native WebView
execution and end-to-end correction acceptance are not established here.

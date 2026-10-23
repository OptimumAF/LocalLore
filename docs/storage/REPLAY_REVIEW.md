# Validated v1 persisted root-history restore

`Engine::restore(seed, history)` accepts complete serialized receipt strings and
returns an engine only after every receipt validates. The input limits, exported
from `locallore::contracts`, are 4,096 receipts, 65,536 UTF-8 bytes per receipt,
and 16 MiB across all receipts. Bounds are checked before decoding/reduction.
Oversized input returns `TooLarge`; malformed or inconsistent history returns
`CorruptHistory`. Invalid trusted seeds retain their normal validation error.

The private JSON decoder rejects duplicate object keys recursively, including
equivalent escaped keys. A private input envelope decodes the request, proposal,
raw events and narration. It is not a canonical receipt constructor. The engine
validates the exact typed request/proposal under the current deterministic v1
rules, renders the permitted narration, and compares the entire reconstructed
receipt against the recorded JSON. This checks all event provenance, witnesses,
participants, sequence, story time and resolved effects. Extra fields, partial
events, reordered history and duplicate turn IDs fail. Object key order and
formatting do not matter; event and serialized set array order remain canonical.
No partial result escapes on failure. `Receipt` and `AcceptedEvent` remain
Serialize-only; their new request/proposal/witness accessors are read-only.

No inference provider, RNG, clock or I/O capability participates in restore.
The v1 profiles have no random outcome rules. This is deterministic v1 replay
verification, not a general archive migration or stochastic outcome reducer.
Adding random mechanics requires extending the explicit recorded-outcome
contract and reducer; replay must never silently reroll a recorded outcome.
Forked archive restoration is outside this root-history API. Stored child
receipts cannot be replayed as another branch's root history.

The storage owner must separately validate the seed identity, persisted branch
head and normalized turn/event rows against the restored result. A valid
completed-turn prefix is a valid standalone history; receipt JSON alone cannot
detect a missing suffix. Validating gameplay consistency does not authenticate
an archive against intentional replacement with another coherent history.
Snapshots and summaries are not inputs to restore.

## Verification

On Windows with Rust 1.93.1, the following passed against this change:

```powershell
cargo test -p locallore --locked --offline
cargo clippy -p locallore --all-targets --features host --locked --offline -- -D warnings
cargo test -p locallore --features host --locked --offline
git diff --check
```

The nine `tests/restore.rs` cases exercise complete canonical projection and
receipt equality across all implemented command effects, every character's
observer context, explicit absent-witness secret exclusion, zero-provider retry,
22 envelope-field mutations, extra fields at five nesting levels, recursive and
escaped duplicate keys, reordering/partial logs, all input budgets, malformed and
deeply nested JSON, cross-story isolation, different seed rules, consumption and
the narrative profile, and 384 seeded attempts with restoration at every prefix.
Existing domain tests include 10,000 seeded attempts and
continue to pass. These are model-free engine checks; disk atomicity, process
death and Android portability require the storage owner's integration evidence.

# M08 archive shared-slice evidence — 2026-10-23

Contributor: `/root/app_storage_review`; implementation evidence, not independent
review or owner acceptance. Refs #12 M08.04/.06 and #30 shared dependencies.
Claims: #12 comments 6360529131 and 6360765614 (dependency addendum), #30 6360529423.

## Source boundary

Implementation `788afcf9938016e691cf71a5f73c26f796c5b95f`, based on the reviewed
durable-fork source and its documentation `2b8b3d7`. Six files changed: new
`playable_archive.rs` and its integration test, storage module/export stanzas,
storage serde/sha2 manifest and lock dependency entries, and the small public
bounded unique-JSON helper beside the existing parser in Engine. No DDL, Store
loader, Host, app, Android, native worker or generated schema change.

The initial default-storage check exposed that `inspection::sha256` is gated by
Host. The coordinator explicitly approved direct storage `sha2 = "=0.10.9"`,
already pinned elsewhere in this lock, rather than adding a Host dependency or
new hashing authority. After the claim addendum, default/non-Host checks pass.
No package version changed or new downloaded dependency was introduced.

Accepted main `d5a76d2308a6863e49b3d088041d0eccadf8bb38` was merged locally as
`8e96850d47466a0f4339fcfe6a55f2a6ff0e8c5c`. The sole conflict was storage module
stanza placement; the archive stanzas were retained. Engine fork/snapshot regions
were untouched. On this reconciled source the same all-feature package test
command passed **220 tests, zero failures/ignored** (three new accepted-main
cancellation tests). All-target/all-feature strict Clippy, fmt and diff checks
also passed. These results are separate from the pre-reconciliation 217 count.

## Executed checks

Windows, Rust/Cargo 1.93.1, offline/locked, `CARGO_PROFILE_DEV_DEBUG=0`,
`CARGO_PROFILE_TEST_DEBUG=0`, `CARGO_INCREMENTAL=0`. Synthetic fixtures only.
Own target `D:/CodexLocalLore/01a165d9-ff25-7500-a550-1099087d4e37/m08-archive`;
own task TEMP/TMP. No model, device, app launch, CUA or protected resource used.

On source 788afcf:

```text
cargo +1.93.1 test -p locallore-storage --test playable_archive --locked --offline --target-dir <own-target> -- --nocapture
13 passed; 0 failed (default, non-Host).
cargo +1.93.1 test -p locallore -p locallore-storage --all-features --locked --offline --target-dir <own-target>
217 passed; 0 failed; 0 ignored across the two packages.
cargo +1.93.1 clippy -p locallore -p locallore-storage --all-targets --all-features --locked --offline --target-dir <own-target> -- -D warnings
PASS
cargo +1.93.1 fmt --all -- --check
PASS
git diff --check
PASS
```

Local log files outside Git: `m08-archive-first-tests.log` (initial ten cases),
`m08-archive-extended-tests.log` (thirteen default cases),
`m08-archive-full-tests.log`, `m08-archive-clippy.log`. Logs retain actual failures
and fixes; they are not human quality or native parity evidence.
Final reconciled logs are `m08-archive-reconciled-tests.log` and
`m08-archive-reconciled-clippy.log`.

Frozen source SHA-256 (actual file bytes, after reconciliation):

| File | SHA-256 |
| --- | --- |
| storage/src/playable_archive.rs | `9e15bd7ea27842819c974db0ccde930a319c11d4c9cf9395ed941a07563377a3` |
| storage/tests/playable_archive.rs | `0a2cc35b2f6504a8bbf5ef97eae54cf80b35f938a43b98fe03c00c619f74dcf1` |
| locallore/src/engine.rs | `a243ae83b705b25023df4d4ec2b2096df211c50d8b19a351b81b79afdd5939ae` |

## Meaningful archive cases

The thirteen new cases exercise actual Store/Engine behavior:

1. Three original branches and four local receipts export/import/reopen with
   identical canonical states, receipts and actor contexts; exact committed
   retries work, child continuation changes only the child, and a retained
   unrelated target story remains unchanged.
2. Real draft/cancelled/failed/stale rows and derived memory are absent from
   import; source terminal guarantees remain. Hidden full-private canaries are
   intentionally present in the artifact, while NPC reconstructed context still
   excludes unwitnessed facts and sibling speech.
3. Recomputed checksums cannot legitimize altered event sequence, unauthorized
   witness, wrong proposal or a copied ancestor receipt in a child.
4. Duplicate keys at envelope/seed/receipt depths, unknown nested fields,
   truncated/invalid UTF-8, future versions and path-like extra fields fail closed.
5. Missing/self parents, future heads/forks, foreign story scope, duplicate branch
   IDs and a fork inside an accepted two-event turn are rejected.
6. Cancellation at **every observed importer callback** and an injected SQL abort
   after accepted-event insertion roll back all target tables. Dropping the
   trigger permits a clean import; identical identity then conflicts.
7. Two real competing Store owners yield one success and Conflict or bounded
   Busy for the other. Explicit retry conflicts without overwriting state.
8. Artifact, branch, individual-receipt, receipt-count and policy-reference caps
   fail closed. Other configured caps are enforced in source; this is not a
   claim that every numerical boundary has an independent stress case.
9. Actual shared Play with an explicitly scripted fake provider produces a
   receipt whose original profile and stage timing metadata survive exactly;
   no model is installed. Altered declared reference fails validation.
10. Export/validation cancellation checkpoints and a panicking callback leave the
    source unchanged.
11. A coordinated second Store commits after the export read snapshot is pinned:
    the archive retains the earlier coherent head, the source advances, and the
    captured archive validates. This proves snapshot isolation, not latency.
12. The original supported accepted 2.1 golden receipt imports and retries
    unchanged, while fresh prepared 2.1 commit and forged unsupported 2.0 history
    still fail existing authority checks.
13. A nested rewind before parent birth retains only the correct root prefix;
    literal JSON-looking and script-looking story text round trips as data.

The existing package suites also executed their Store crash/atomicity cases;
these are regression evidence, not a new archive-specific kill-at-commit test.

## Limits and next gate

This implements the shared prerequisite in
[M08_PLAYABLE_ARCHIVE_V1.md](M08_PLAYABLE_ARCHIVE_V1.md). It does not complete
M08.04/.06 or D08. No native/Android archive round trip, actual model loading,
installer, external-format interoperability, cryptographic authenticity, archive
file publication, or independent review is claimed. Next: independent source
review, integrated regression, then separately claimed native session/consent and
round-trip work. Keep acceptance checkboxes unchecked until owner evidence gates.

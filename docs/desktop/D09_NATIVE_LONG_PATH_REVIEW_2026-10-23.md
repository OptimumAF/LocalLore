# Native long-path publication review, 2026-10-23

Refs #31 D09.05/.06 partial and #30 native export correctness. Independent
coordinator-delegated reviewer `/root/app_storage_review`; claims
[#30 6371306703](https://github.com/OptimumAF/LocalLore/issues/30#issuecomment-6371306703)
and [#31 6371307018](https://github.com/OptimumAF/LocalLore/issues/31#issuecomment-6371307018).
Reviewed frozen `7573d24b30d56e2079b73c156b908a16d24738c7`, following RED
`a8d45830d438dcef9889d54dd703fd42ed09cb26`, base accepted `b3543d6`.
Separate own `source-native-long-path-review` / `review/d09-native-long-path`.

No concrete blocker was found in this focused source review. The ten-line
production correction preserves the existing pinned-parent/held-source-handle
publication contract and nonoverwrite flag. It qualifies neither all Unicode
application/build/install paths nor full D09/D08 acceptance.

## Independence and exact delta

Only this NEW report is edited. No implementation or copied shadow test was
written by the reviewer, and no native build/test/app/model/worker/device was
executed here. Reviewer previously authored the unchanged private-capture caller
of this shared writer; this is independent review of the coordinator's new
finalization correction/regression and its caller lifetimes, not a claim that
every unchanged old capture feature received a new independent audit.

Production delta is ten added lines in `exports::atomic_finalize`. RED adds one
52-line Windows regression; the sole archive-test delta adds `{r}` diagnostic
text to its original exported-status assertion. No assertion, timeout, IPC,
permission, schema, UI, model/runtime contract or canonical behavior was relaxed.
Non-Windows behavior remains Unsupported.

## Path and handle authority

Previously the actual held-handle rename received the unextended destination
path. The correction canonicalizes only the existing parent, joins the original
absent target's `file_name`, then encodes that Windows extended path. It does not
canonicalize the absent output, choose a new basename, reopen the staging source,
drop a pin, delete a collision or fall back to a path-based move. A missing
parent/filename or canonicalization failure returns Io before publication.
The existing UTF16 length cap remains applied after canonicalization.

The aligned FILE_RENAME_INFO buffer, original held `File` handle,
`RootDirectory = null`, and `ReplaceIfExists = false` are unchanged. The OS rename
still decides nonoverwrite atomically; target existence is consulted only to
categorize a failed operation. A failed status does not grant permission to
replace/delete the existing destination. Payload identity remains that of the
held staged file/directory, rather than a fresh lookup of its old name.

All production call paths keep their parent-pin guards lexically alive across
canonicalization and rename:

- Inspection/database/private-capture save uses `Preview::save_impl`: pins the
  chosen parent, exclusively creates and pins its GUID stage, writes fixed file
  names, holds saved-state serialization, then invokes the finalizer before
  dropping stage and ancestor guards. Failure cleans only its known created
  stage entries. Capture and inspection command closures retain their existing
  window-epoch admission around finalization.
- Playable archive publish retains `archive::pin(destination)` for the whole
  operation, creates the exact new stage with DELETE-capable/no-delete-sharing
  handle, syncs, checks work/cancellation and dispatches the finalizer under its
  existing lease. Failure cleanup occurs after dropping its own stage handle;
  it does not remove the collided output. Archive's existing path validation
  permits only absolute Disk/VerbatimDisk prefixes, rejects traversal/reparse
  components, and retains handles from root to destination. This change does not
  broaden it to UNC or device namespaces.
- Model import also uses this helper. `copy_model` retains source and destination
  ancestor pins, opens its exact new stage, verifies expected length/hash, syncs
  and checks cancellation before calling the lease-guarded finalizer. Existing
  collision mapping remains ModelExists. No model bytes were read/run by this
  reviewer and no new model qualification is inferred.

The general inspection/model directory guard rejects relative/traversal and
reparse components, verifies opened handles and retains no-delete-sharing
ancestor handles. Its existing UNC/prefix policy is unchanged; this review
executed no UNC/network-share/device-namespace case. Canonicalization is not a
replacement for those caller guards or an OS sandbox against a compromised
same-user environment. Missing/failing paths have no weaker publication fallback.
Normal callers construct fixed native output leaves; renderer IPC receives no
arbitrary destination path or output bytes through this correction.

## Regression and execution attribution

The coordinator reports two distinct original failures: longer-TEMP native
archive export returned Io with cleanup_complete=true, while short-TEMP control
passed; the added actual-handle Unicode regression then failed before correction.
A fresh-checkout compile failure because frontendDist was absent is separate
setup evidence, not execution of that RED test. Root provisioned/built the normal
frontend before its later native compilation. Those failures remain retained by
the coordinator; this report does not relabel them as reviewer executions.

Source-reviewed new test constructs actual nested Unicode/space directory names
until parent UTF16 length exceeds290, creates the real DELETE-capable stage
handle, invokes the production finalizer, checks exact output bytes and absence
of the old stage, then attempts another publication at the same target. It
requires ExportExists and unchanged bytes in both the first output and rejected
second stage. The payload is fixed synthetic text, not a model/story file.
This test does not itself acquire the production ancestor-pin chain or prove a
concurrent ancestor-substitution schedule; that caller-lifetime assessment above
is source-derived. It also is not a UNC or full application journey test.

At frozen7573d24, coordinator reports actual default47 PASS/1 existing ignore,
development49 native+2 integration PASS/1 existing ignore, and strict all-feature
native Clippy PASS. Reviewer did not rerun or reattribute those counts. Existing
short-path/cancel/Full/collision/staging-pin tests remain present; their gates
were not replaced by the new long-path case. Coordinator owns final publication
checks. Reviewer `git diff --check` passes; the only reviewer change is this doc.

## Source binding and remaining scope

Actual reviewer checkout exports.rs SHA256:
`78382c15d80c52eb8886a6dd710433086648293b5856adabd4de62c49ac58ad1`.
Canonical Git blobs at frozen7573d24:

| Source | Git blob |
| --- | --- |
| `exports.rs` | `b9d0949d7fad6dfe57401b985382d5d5eff96f5f` |
| `archive.rs` | `542d35b9fd2404e049a121358107f762cfe39964` |
| `export_commands.rs` | `18bca030fed5a3e29cef83e60769a9b7db5459c6` |
| `capture_exports.rs` | `837e910b4c8200b47dd259e1df47129dd7022253` |
| `models.rs` | `317c9ebbb9153cef0887d758111d4d0c2f7d64d0` |
| `lease.rs` | `d0dadc18f1a26f11972cec73710ed114d19c6e91` |

No source-path normalization in a reproducibility comparison is involved: this
is Windows runtime destination-path handling. Earlier ASCII/space clean-build
proofs do not establish Unicode packaging or runtime acceptance. UNC/network
filesystems, physical disk exhaustion/power loss, root/reparse attack execution,
real picker/UI/keyboard/device/model behavior and update/install qualifications
were not run by this reviewer. No protected resources, settings, cleanup of
unknown paths, dependencies, merge/release or milestone checklist were touched.

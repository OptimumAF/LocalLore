# Local phone identity review, version 1

Refs #5 (M01.01, supporting M01.05); #14 (supporting M10.03).
This development workflow records an explicitly chosen identity without
recovering a missing historical file or silently substituting similar hardware.
It creates no account and changes no gameplay, Android permissions or settings.
The receipt declares identity; it grants no device, installation or model action.

## Three separate steps

1. A coordinator uses the existing [read-only roster CLI](HELD_DEVICE_ROSTER_PROTOCOL_V1.md)
   once under fresh host admission to create a current private candidate capture.
   It never starts ADB, selects a device or sends a device command. A previous
   empty capture is retained rather than polled repeatedly until favorable.
2. The new file-only tool validates that capture and writes a private, inert
   local HTML review page. A human explicitly identifies the intended candidate
   against the exact proposal hash. A sole row is never auto-selected.
3. After that direct choice, the tool records a create-only declared identity.
   Future [phone inventory](PHYSICAL_PHONE_INVENTORY_PROTOCOL_V1.md) still needs
   independent fresh source/host/target admission and USB selection with returned
   transport-ID comparison before any device service. Its model eligibility,
   installed-package preservation and other qualification gates remain separate.

No new backend/controller or old protocol modification is introduced.
`phone_identity_enrollment.py` is pure review/selection data handling;
`phone_identity_enrollment_io.py` reads/writes fixed local files. Neither
acquires a roster, runs ADB, performs a target query or confirms on behalf of a
human. Source validation uses the existing roster helpers, including their own
interpreter/DLL-location lookup and installed-runtime hashing; it does not query
target processes, devices or the shared guest ledger.

## Canonical private capture

The explicit operator-selected bundle must be on physical D:, outside Git and
without reparse aliases. Its fixed layout is:

```text
bundle/
  admission-v1.json
  roster-v1/
    result-v1.json
    request-v1.json
    owner-result-v1.json
    started-v1.json
    owner-stdout-v1.bin
    owner-stderr-v1.bin
    report-v1.json
    version-report-v1.json
    version-bytes-v1.bin
    source-closure-{before,after,final}-v1.json
    python-{before,after,final}-v1.json
```

Before following any embedded result pin, the reader requires its exact
code-fixed role/path, strict byte-count/hash types and bounded size. It rejects
symlink/reparse and multiple-link files before content reads. Reads retain
stable identities separately for path and held file descriptor, joining them
by dev/inode/size/mtime and explicit Windows birth time; access time is not
content identity. Rechecks use the original bounded size, not a new unbounded
observed size. These checks detect changes; they are not a filesystem reservation
or protection against a malicious local OS.

The reader replays the exact result/request/started schemas, known successful
worker owner and actual empty output streams. It uses the real version/roster
proof verifiers, identical embedded version/raw sidecar and same recorded worker
joins. Source/Python before/after/final snapshots must equal the current fixed
roster source/runtime bindings. Captured arbitrary source or interpreter paths
are never used as file-read instructions. The enrollment operation separately
pins both new modules and their imported inventory module, and retains/rechecks
accepted current source/runtime values through publication and identity loading.

Captured metadata cannot authenticate its own acquisition. The coordinator
still needs separately observed actual production execution, terminal status
and applicable human authority. A fabricated self-consistent JSON graph is not
proof of a physical phone. Synthetic fixtures are not acquisition evidence.

## Proposal, review and explicit choice

```powershell
python -B -m benchmarks.phone_identity_enrollment_io prepare --bundle <D: bundle> --result-sha256 <roster result SHA-256>
```

Only compatible online rows with a non-null supported serial and required
product/model/device metadata become candidates. Devpath, model, serial syntax
and a single-row count do not prove USB, physical identity or authorization.
No eligible rows produces a `no_candidates` proposal and no selectable identity.

Preparation creates `review-v1/proposal-v1.json`, `review.html` and
`prepare-result-v1.json`. The page shows full identifiers locally, escaped as
text, with an opaque candidate ID and proposal hash. It contains no JavaScript,
links, remote resources, auto-open or confirmation action, and has a restrictive
content-security policy. Keep the page and serials out of public reports.

Candidate ID is SHA-256 of the capture SHA, NUL separator and canonical row JSON
(sorted keys, compact separators, ASCII escapes, no newline). File JSON uses
the same canonical options with one trailing LF. IDs, serials and transport IDs
must be unique. Hashes bind a choice to exact data; they do not make metadata
trustworthy or establish human intent.

The coordinator records a direct human choice in the fixed
`review-v1/human-choice-v1.json` file. Its exact fields are `version=1`,
`protocol=phone-identity-choice-v1`, `proposal_sha256`, `candidate_id`,
`action=select_for_read_only_inventory` and `human_choice_recorded=true`.
This is trusted-caller input recording the actual choice, not a way for an agent
to invent approval. Missing choice, unknown candidate or mismatched proposal
hash refuses. Never generate a default choice because only one row exists.

```powershell
python -B -m benchmarks.phone_identity_enrollment_io confirm --bundle <D: bundle> --proposal-sha256 <proposal SHA-256> --decision-sha256 <choice SHA-256>
```

Confirmation reconstructs the proposal from the validated canonical capture.
It requires the complete preparation record and deterministic review-page bytes,
and retains those input pins through publication. Altered presentation or partial
preparation cannot silently become a declared identity. This proves current
file coherence, not that a human viewed those bytes earlier or that a forged
caller decision is authentic.

Successful confirmation creates `identity-v1.json` and `confirm-result-v1.json`.
The receipt binds capture, proposal and decision; its serial is looked up from
the chosen candidate, never supplied independently by confirmation. Its fixed
purpose is `read_only_inventory_identity`, status `declared_identity`.
`feature_acceptance`, `authority_authenticated` and `grants_device_actions`
remain false. It does not assert current `device` state or preserve a transport
ID as a future lease. `load_identity` replays the same complete bounded workflow
before returning data; the pure `validate_identity` alone is only structural.

## Failure and authority limits

All outputs are create-only, bounded, flushed and rechecked. Partial files and
directories remain for diagnosis; there is no overwrite, cleanup or automatic
fresh-directory retry. Errors from the public CLI are fixed categories without
private paths or provider text. Public output contains only status/counts and
false authority flags, never serial/model payloads. Raw private capture remains
outside Git on D; no model, APK, key or guest-image contents are required.

Current source/runtime/profile compatibility is required for replay; a future
source migration may require an explicit reader/migration rather than silently
accepting changed bindings. Filesystem permissions, OS backups, compromised
hosts and a mistaken human choice remain outside this consistency check.
Fresh runtime inventory supplies its own ownership and USB checks; no record
here replaces them or grants broader actions. Full M01/M10 and physical-model
acceptance remain separate, with owner acceptance and merge still pending.

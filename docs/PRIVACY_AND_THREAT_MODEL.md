# Privacy contract and threat model

Status: design requirements plus bounded implementation evidence, not a security certification.
The Rust/fake-inference Android demo and local diagnostics have finite regression
tests; broader release/privacy qualification remains pending.

## Local-only contract

During play, model inference, context construction, retrieval, summaries, relationship updates, and persistence must operate on the device. The app has no required account, hosted model fallback, remote embedding call, analytics collector, advertising SDK, or automatic conversation upload. A device that cannot run a chosen profile gets an honest compatibility error, not a hidden server request.

The initial provisioning route is manual model-file import. A future optional networked model downloader requires explicit approval and a separate policy; it may fetch public artifacts only at user request and must never send story content. Opening documentation in an external browser is a user-controlled action, not an excuse for background networking.

For a strict Android build, aim to omit the INTERNET permission and verify all included runtime/dependency behavior. This is an implementation requirement to test, not a claim that every platform can provide the same permission boundary.

## Assets to protect

Player messages, fictional character state, personal information incidentally typed into stories, secrets in exported archives, model download credentials if ever supported, app-local files, device resources, signing credentials, build integrity, and the privacy of community vulnerability reports.

Treat fictional player-character attributes separately from the real user's identity. Do not infer or retain real sensitive attributes for personalization outside the story.

## Trust boundaries

The UI's explicit author operation is a higher-trust instruction than text inside a story, but still requires validation and impact confirmation. Model output, retrieved memories, imported story packs, filenames, archives, and model artifacts are untrusted input. Third-party dependencies and native inference parsers enlarge the attack surface; pinned versions and review are required.

The app cannot guarantee confidentiality against a compromised/rooted operating system, malicious input method, screen capture by another privileged component, someone with an unlocked device, or a user deliberately exporting to a cloud-backed location. Document these limits rather than making an absolute 'nothing can ever leave the phone' claim.

## Main threats and mitigations

| Threat | Required mitigation / verification |
|---|---|
| Dialogue or imported content requests privileged behavior | Capability restrictions, typed allowlist, explicit author UI, no arbitrary tools/SQL/code |
| Wrong story/branch/character history enters a prompt | Central scoped query API, ancestry/observer checks, versioned caches, isolation tests |
| Private stories leak through logs or crash reporting | No remote reporting; bounded local diagnostics without text; preview/redaction before explicit export |
| OS backup or transfer copies private files | Configure and test backup/transfer exclusions for every relevant storage location and OS target |
| Malicious archive overwrites files or exhausts storage | Reject traversal/absolute paths/symlinks as appropriate; expansion/count/depth limits; preflight and atomic import |
| Model file exploits native parser | Treat file as untrusted; known-compatible formats, provenance/hash checks, patched pinned runtime, bounded file handling |
| Prompt exceeds memory/compute budget | Input/context/output limits, bounded repairs, cancellable generation, support profiles |
| Foreign PR accesses repository secrets | Read-only CI token, no secrets on untrusted forks, no privileged `pull_request_target` execution of fork code |
| Agent or contributor changes project authority | Owner-controlled settings, CODEOWNERS plus verified rules, no automatic merge/release/admin invitation |
| Release artifact differs from reviewed source | Pinned build inputs, checksums, source commit, owner-controlled signing and release procedure |

## Backup and storage boundaries

Android's backup system can include application databases/files unless configured otherwise. Follow the current official backup/transfer guidance and test the actual target versions; a single `allowBackup` flag is not a substitute for examining cloud-backup and device-transfer rules. Relevant documentation: [S09](REFERENCES.md).

Use app-private storage, appropriate no-backup locations/exclusions, and a deliberate export flow. Do not place player files in broadly shared external storage for convenience. Protect temporary archives and delete them when no longer needed. State whether screen previews/screenshots and clipboard copying are permitted, and provide appropriate user controls.

Operating-system app sandboxing and device encryption do not automatically mean a separately encrypted database. If app-level at-rest encryption is introduced, use reviewed libraries and platform key management, define recovery/migration behavior, and test failure cases. Do not invent cryptography. Passphrase-protected exports are a separate product decision; until implemented, clearly label exports as plaintext/private.

Deleting records is not a guarantee of forensic erasure on flash storage or deletion of copies the user exported elsewhere. Deletion must still remove every app-maintained canonical/derived representation and prevent retrieval of the removed story.

## Model and story import

A SHA-256 hash verifies correspondence to an expected artifact, not that the publisher or parser is trustworthy. Record artifact source/revision/license and use compatible supported formats. Do not execute remote code or import arbitrary serialized objects/scripts from a story pack. Do not automatically follow URLs embedded in story content.

Validate schema versions, reference scope, ancestry, event counts, file sizes, decompression limits, path normalization, and media types before writes. Import into a new namespace transactionally, with collision handling and a safe rollback. Limit native allocations and provide cancellable validation for large files.

## Consent and diagnostics

The Android demo keeps at most 64 enum/numeric diagnostic records in memory:
phase, outcome, allowlisted error category and elapsed milliseconds clamped to
60,000. Its API accepts no story text, prompt, narration, actor/item name,
story/branch/session ID, URI, path, wall clock, device ID or exception message.
Unknown native category strings become `UNKNOWN`. The bounded JSON v1 snapshot
is at most 16 KiB; no diagnostic file or remote report is created by default.
The ViewModel retains it across rotation and clears it on disposal/process death.

Open **Local diagnostics** to review a frozen snapshot. **Clear** removes its
memory records and refreshes the preview without changing canonical gameplay.
**Export JSON** explicitly opens Android's document picker. The writer
uses exactly the reviewed bytes, a user-selected content URI, no broad storage
permission and no persistent URI grant. Closing/resetting revokes pending
consent; an outstanding old picker result cannot authorize a newer snapshot.
No result without an in-memory pending snapshot can write after process death.

Exports are plaintext. A selected document provider can synchronize them outside
the device; the app cannot prevent that. Failure/cancellation can leave an empty
or incomplete file, and clearing diagnostics does not delete exported copies.
Provider calls and cancellation listeners run off the UI thread. One global
export slot remains held through descriptor and cancellation cleanup, so a
noncooperative provider can delay subsequent exports without accumulating
open/write operations. Cancellation does not guarantee provider termination or
undo a completed write. See [ADR-0005](adr/0005-local-diagnostic-exports.md) and
[diagnostic evidence](diagnostics/VERIFICATION_2026-10-22.md).

Benchmark reports and issue templates use original synthetic data. No one should need to upload a personal story to receive basic support. An explicit diagnostic export shows exactly which categories/files will be included. Remove credentials, personal paths, device identifiers, story text, and hidden reasoning by default. Store aggregates rather than persistent full prompts when possible.

Development agents must not send real story data to a hosted code assistant or model judge without explicit informed authorization. The recommended evaluation harness uses synthetic fixtures, eliminating that need.

## Release checklist

Confirm permissions/dependency inventory; offline runtime behavior; outbound-traffic observations; backup and transfer exclusions; app-private storage; import attack tests; story/branch/observer isolation; logs/export preview; deletion coverage; cancellation/OOM limits; CI secret isolation; model/runtime license and vulnerability review; private reporting; and owner-controlled release artifacts.

A finite security test does not justify a blanket claim of safety. Publish the tested scope, known limits, and update/reporting process. Security-sensitive changes require review even if their UI impact looks small.

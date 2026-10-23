# Private Play capture and exact native export

This D06.02/.03/.06/.07 slice observes the accepted shared Host/Play capture backend. It adds no context compiler, provider authority, canonical event path, storage schema, or generation rerun. Private details are separate from the existing metadata debugger, accepted receipts, current inspection state and ordinary playable archives.

## Consent and presentation

Only the acknowledged Story Lab omniscient lens displays full private details. Player/NPC lenses, session changes, debugger close, Return to Play and window teardown clear the private presentation and invalidate pending replies. Native revocation is best effort and reports Busy/unavailable honestly; clearing presentation is not a claim of physical erasure. Already user-saved plaintext exports remain the user's files.

Future-attempt capture defaults off. Explicit consent applies to the exact native session/owner and scope for ten minutes from configuration, checked on access. A head advance alone does not revoke that consent. Fresh-head checks still apply when configuring or reading. The additive `trace_capture_revoke {session,scope}` operation removes details without a head check or persisted resume and grants no read/generation authority.

Metadata clear/disable and private grant changes use the same asynchronous control chain. Presentation clears synchronously, then owner revocation and the entire actual metadata operation/read/finally settle before another private grant can be admitted. An old delayed metadata effect cannot erase a later grant while the panel still calls it enabled. Captured-receipt navigation also binds the originating native session and scope before turn/base lookup, and rechecks session epoch/head/query context after asynchronous opening.

The capture API reports `disabled`, `expired`, `not_retained`, `recorded` or `truncated`. Every reply labels `exact_reconstruction:false`; retained values are historical copies from actual production hooks, not reconstructed from today's state. The existing backend limits are three attempts, 512 KiB retained encoded artifacts total, 192 KiB per attempt, 48 KiB per artifact and sixteen artifacts per attempt. These are encoded-retention limits, not total process/renderer heap or OS paging guarantees.

Artifact disclosure starts collapsed. The panel shows the captured actor/role, source IDs/revisions, selection reasons/scores/mandatory status and recorded estimated token budget. Per-record measured tokenizer allocation and model attention are unavailable. Raw output, repair requests, parsed proposals, validated plans and narrator output remain separately labeled. `validated_plan_not_durable_commit` and `accepted_candidate_not_durable_commit` never establish durable commit. Matching accepted receipts and field-diff/provenance queries are separate evidence. No hidden model reasoning is invented.

## Exact private export boundary

`capture_preview` accepts one strict `selection` object with session, scope, expected_head, base_revision, turn and attempt. It accepts no path, capture bytes, prompt, arbitrary output, SQL or executable. Native code performs the actual Host capture read and validates its bounded shape and exact selection before constructing an immutable preview.

The fixed format is `locallore-private-trace`, version1, mode `private_trace`, privacy `private_generation_capture`. Its directory contains only:

- `capture.json`: the native-captured read, encoded once as the exact preview text.
- `manifest.json`: format/privacy/scope/head/base metadata, `portable_playable:false`, `exact_reconstruction:false`, and the exact capture file length/SHA256.

The native preview returns token, manifest, file lengths, expiry and exact capture text. The renderer checks the identity, retained statuses, artifact bounds and text digest. SHA256 verifies byte consistency; it is not origin authentication or authority over accepted history.

A separate typed broker instance uses the existing guarded nonoverwrite staging/atomic publication writer. It retains at most two preview records and 1 MiB total encoded files including manifests under the admission mutex. A cancelled/expired record held by an in-flight save or picker remains budgeted until that holder releases it. The five-minute TTL is fixed from preview creation and checked on access; it is not a background deletion timer. Transient serialization/IPC/render copies are not counted as retained broker bytes.

Saving requires a second explicit private-plaintext consent. `capture_save` accepts only the opaque token and consent flag; a native folder picker supplies the destination. It writes the exact retained preview bytes. Native cancellation/lease checks fence publication; a finalized save can win a concurrent cancellation. Revocation prevents later access/publication but does not remove an already saved export. Scope/lens/session changes also revoke delayed preview tokens by their exact token when they arrive.

## Qualification boundaries

MOCK controller checks, synthetic native Host/Play tests, and invisible app-owned WebView2 journeys are separate lanes. The development-only provider returns fixed structured outputs through the real production Play pipeline; it is absent from normal builds. Native picker doubles choose fixed task-owned destinations after selection. None of these are real-model inference, user desktop control, dialog automation, a device qualification or human acceptance.

Memory maintenance, pause/step, generation replay, real-model capture quality, detached-copy erasure, and full D06 acceptance remain outside this slice. Final evidence and any correction-review disposition belong in the companion dated report. A passing frozen native cohort does not close a subsequently demonstrated asynchronous-control race.

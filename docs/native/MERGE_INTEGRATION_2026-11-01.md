# Combined PR integration, 2026-11-01

This integration combines the owner-requested open PRs 275 through 312 while
preserving their individual commits and dated execution evidence. Current checks
and the final accepted SHA manifest belong on issue #3; a code merge does not
complete the partial native/device/model/UI/privacy milestones.

## Fixed profiles with colliding filenames

The held-AUTHOR SDK6 and model-free archive UI SDK6 branches independently added
`android_process_client_v6.py` and `android_process_verification_v6.py` with
different contracts. The combined tree keeps the actually exercised archive UI
files at those names. Held-AUTHOR uses descriptive
`android_process_live_death_client.py` and
`android_process_live_death_verification.py`, with its existing fixed imports,
source roster and tests updated. Protocol/version/session values, operations,
budgets, proof/ownership checks and old source history remain intact. There is
no caller-selected protocol or dynamic replay dispatch.

An independent byte comparison confirms the live-death verifier is unchanged;
its client changes only the fixed verifier import. Both archive UI files match
their original blobs. The direct coexistence tests use valid synthetic positive
controls and reject foreign owners, admissions and closed records in both
directions even though both profiles use version 6. These new-source host
checks do not requalify frozen historical build or guest bindings.

## Pre-guest isolated-server adapter

The phone-discovery addition makes the underlying exchange reject a non-isolated
protocol. The pre-guest adapter now explicitly projects its code-fixed isolated
protocol and rejects any explicitly foreign protocol. It does not mutate the
outer admission. The original timing, complete-response, native-anchor, source
mutation and cleanup regressions remain unchanged. This repairs the minimal
legacy adapter compatibility exposed by combined tests; no deadline or cleanup
gate is relaxed.

## Lossless Query2 display deadlines

Native promise deadlines accept the full unsigned 64-bit range. Android and
desktop display consumers could reject a valid deadline after JSON numeric
conversion. Query2-only typed display serializers now emit canonical decimal
strings for promise and promised-event deadlines, including nested changes.
Search, cursor hashing and page-byte accounting use the same serializer.
Canonical native values and Query1 serialization remain numeric and unchanged.

Both display decoders accept bounded canonical decimal text and their exact
legacy integer forms, rejecting malformed, fractional, unsafe or over-range
values. Native, Android and desktop tests include the maximum accepted value,
old-format controls and unchanged ownership/privacy restrictions. See
[the deadline verification](../android/QUERY2_UNSIGNED_DEADLINES_2026-11-01.md).

## Existing frontend review oracles

Accepted main already added three fork-hook exclusions. The evidence review now
names all six explicit browser/fork additions, requires exactly 73 distinct
markers and preserves the original 67-marker hash and exclusion predicate.

The narration diagnostic checker also recognizes the already-accepted thin
ForkPanel mount. It verifies exact controller/context bindings and proves that
diagnostic metadata neither prepares a fork nor supplies request/consent or
native authority. Other sibling exclusions stay enforced. App and ForkPanel
production code are unchanged by this correction.

## Secret-scan triage

The failing checks on PRs 294 and 305 flag lists of Android injected signing
property **names**, followed by a requirement that signing values were not
logged. They do not assign or contain signing credentials. PR 303 flags a
synthetic privacy sentinel checked by a scripted test provider, not an
authentication token. These classifications were independently checked against
the exact flagged commits and lines. The original scan results remain visible;
no alert dismissal, scanner/protection setting, history rewrite or credential
rotation is represented as performed.

## Scope of verification

All project commands and outputs use physical D:, with process-local temporary
paths there. Host tests include tiny, newly created Windows handle/deletion
fixtures and inert owned Python processes; they do not retire actual guest
images or touch the production admission ledger. Offline builds and package
audits are distinct from Android instrumentation, actual GUI/model/phone runs,
privacy/OEM qualification or release acceptance. All original failed, frozen,
ignored, recovery and other-owner data remain retained.

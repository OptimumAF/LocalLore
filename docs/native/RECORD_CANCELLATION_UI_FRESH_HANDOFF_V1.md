# SDK18 fresh preparation and owned-run handoff

M10.02 `RECORD_CANCELLATION_UI_FRESH_HANDOFF`, supporting M09.04/M09.06.
SDK18 is an internal harness version. Android/API35, installed tools, dependencies,
application code and the Rust authority are unchanged.

This connects fixed planning inputs, guarded preparation, verified fresh run
inputs and the existing SDK18 activation. It supplies no human approval or
present permission to execute. All records produced by inspection are data.

## Fixed sources and planning

The frozen profile source is PR #388,
`287b158e72ed5c0811a2e7e433e73ada4f4d6c52`, tree
`81dae478d06f2da8be5f14a693f276318fe0c4ac`, at
`D:/Dev/Experiments/LocalLore/2026-11-03-record-cancellation-profile-v1/candidate-source-v1`.
Product/APKs remain separately frozen in #386, on #385; the B111 attestor from
#387 remains the build authority. Rebuilding this tooling branch does not
replace that product or generate another gameplay authority.

`scripts/record_cancellation_ui_prepare_inputs.py` exposes pure
`validate_catalog(value)`, fixed read-only `source_snapshot()` and no-argument
`inspect_fixed()`. The CLI accepts only `inspect`; it exposes no output/root,
profile or implementation selector. Its private memory/observation seams exist
for synthetic tests, not operator selection.

The exact sealed B112 catalog is747,334B/SHA256
`b6202c3a4b06d70845c28cedf52ec68140da3a2dc482b6573221183d2de11db5`.
The inspector checks all2,644 raw files against it, including length/SHA256/Git
blob/mode metadata, exact file/directory closure, physical paths, links and a
final catalog reread. It relies on that previously Git-verified catalog seal;
the inner fresh helper additionally reconstructs the declared Git tree.
Enumeration is bounded while walking, not after allocating an unlimited list.

The inspector checks28 benchmark bindings, fixed checker/module origins, current
Python/static tool pins and actual B111 saved-manifest/APK facts. It builds a
model-free8GiB/four-core/API35 prepare proposal through the reviewed public
planning API, validates installed files again, and compares capacity/ledger
observations before and after. Installed planning is limited to2,048 files/6GiB
per hash pass; the plan/verify pair allows at most12GiB installed payload. Other
bounded source/build reads are separate. This is not a cumulative read cap for
the future operation, which intentionally revalidates at multiple boundaries.
Existing hashes stream through a1MiB buffer. No installed contents, model weights
or credential bytes are copied into outputs. The ADB key remains path metadata;
the console-token hash stays in private planning records.

Fixed output is this packet's `inspection-v1` under
`D:/Dev/Experiments/LocalLore/2026-11-03-record-cancellation-fresh-v1`.
It contains only prepare proposal, capacity preview, frozen handoff and inspection
result. Blocked capacity can be recorded, never promoted to admission. Output is
create-only; partial failures remain evidence. No guest, authority, reservation,
runtime or operational control directory is created by inspection.

## One reviewed operation

The pure contracts are `record_cancellation_ui_fresh_contract.py` and
`record_cancellation_operation_contract.py`. Inner and outer authority are distinct
fixed files, `human-authority-v1.json` and `parent-authority-v1.json`, under this
packet. They bind exact operator/contract/handoff/proposal bytes, explicit reviewed
approval reference, current ledger and fixed no-model/no-retirement scope.
The immutable profile head anchors source identity; exact inner byte pins avoid
an impossible same-commit self-hash cycle. Local records do not authenticate a
human against a local administrator. Old approvals or metadata cannot be retagged
into this scope.

The supported future operation entry is **only**
`scripts/run_record_cancellation_operation.py`. Its checked parent job encloses
the entire inner invocation, including expensive source/install preflight and
preparation/run stages, using the original2400-second clock. Small parent
bootstrap/authority and final metadata reads remain cooperative. The standalone
inner CLI does its initial checks before its own supervisor and is not an
independent hard preflight bound. Do not substitute it for the parent entry.
The generic host180-second and guest1800-second ceilings are unchanged.

After explicit authority, the parent consumes its durable attempt before the
heavy inner preflight and current capacity checks. The inner consumes its separate
attempt only after its fresh checks pass. A capacity refusal can therefore spend
parent authority without creating an inner attempt; it grants no automatic retry.
The inner then calls current guarded preparation, validates exact successful
prepared receipts/terminal/ledger-v2 state and source/tool/Python joins, then
creates current run inputs with the activation input published last. No recovery
or implicit reservation cancellation is included. Failures remain spent/partial;
there is no automatic retry or success repair. Barrier, actual caller/worker,
owned job/capture, terminal, claim, storage closure and same-proof replay guards
remain mandatory. Unknown cleanup or zero exit alone cannot qualify a run.

The guest remains
`D:/Dev/Experiments/LocalLore/2026-11-03-record-cancellation-ui-v1/avd-v1`;
profile runtime/control paths remain those in #388. No such operational path was
created here. Actual authorized execution would create its bounded owned outputs.
Shared admission stays two unretired roots/64GiB,40GiB per preparing/live guest.
Capacity resolution and an exact reviewed proposal/new approval are still needed.
Pending retirement-only authority would not grant a boot. Other emulators,
shared ADB, settings, existing images and the shared ledger remain preserved.

# Native text recovery review, 2026-10-23

Refs [#9](https://github.com/OptimumAF/LocalLore/issues/9), M05.04 partial
and M05.05 supporting. Prerequisite: open
[#126](https://github.com/OptimumAF/LocalLore/pull/126), exact
`b2d9fce1c08a24887c9eb6abb580d4b7b3d44a35`.

## Independent review scope

Report-only ownership was claimed in
[comment 6377532402](https://github.com/OptimumAF/LocalLore/issues/9#issuecomment-6377532402).
The reviewer reused the existing clean separate review worktree at the exact
prerequisite; an attempted duplicate creation refused without changing it.
Review read the actual Compose text composer, ShellViewModel, DurableGateway,
production NativeWorkspaceTransport, Rust Host/play receipt contracts and prior
native cancellation/input fixtures. No production implementation, dependency,
schema, model selection or alternate gameplay authority is introduced.

The reviewer performed source and evidence inspection only. Builds and device
execution belong to the coordinator and device specialist, respectively. No
reviewer build, device/process/model call or original-save operation occurred.
Independent review is not owner acceptance.

## Fixture findings and boundaries

The six-method fixture enters actual Action/Dialogue text through Compose chips,
text input and Send. It calls the production gateway, transport, JNI, Rust Host,
scripted fake inference and SQLite owner. Original kind, text, scope, revision,
session and turn key are checked, including leading/trailing spaces, newline
and a non-ASCII punctuation character. There is no replacement typed-action
submission. Actual accepted receipts must retain the original `free_text`
request, play-v2 record and the real configured fixture profile.

Literal dialogue containing a claim of immortality and a request for blink must
produce one `say` command and one `said` event. Player self state, facts, beliefs
and inventory remain equal to the preceding permitted snapshot; blink remains
absent. This is finite evidence for this utterance through existing Rust rules,
not a guarantee for arbitrary language, model prose quality or NPC-private
knowledge. Existing privileged-observer refusal vectors remain negative
admission checks, not inspection of private NPC contents.

Cancellation holds delivery of actual completed ready/cancel replies. A foreign
cancel acknowledgement must require visible recovery with the original complete
cancel command, no replacement submission and no commit. Late preparation and
disposal must not replace accepted visible history. This delivery-boundary test
does not establish cancellation during active model work.

Commit uncertainty is injected only after an actual Rust/SQLite commit. One
subsequent status delivery returns `Busy`, making the unknown outcome visible.
Recover must retrieve the actual accepted receipt using the original key, with
one free-text submission, one preparation, one commit and two status calls.
Accepted history, rather than the synthetic failure, owns the recovered result.

Each method uses a create-new contained child of the isolated application's
no-backup directory. Cleanup releases delivery gates, clears the ViewModel
store on Main, closes the gateway, waits for wrapper exchanges to reach zero
and acquires all four real native owner slots simultaneously. Probe handles
close on IO, including failure paths. Real close/reopen compares the complete
permitted player projection, accepted receipts, inventory and revision before
contained synthetic directory deletion. No external process stop substitutes
for these in-test ownership checks.

Source review found no concrete mismatch against the current wire/profile/
receipt and recovery contracts. Execution remains necessary to establish the
fixture actually compiles and exercises the intended Android behavior.
The fixture was independently frozen at
`1824334a814a8c505d2c3e80514bbffc95b7bc85`, 23,825 bytes, SHA-256
`bae23dba98f32953c215280ea297c23c91bb25457e4309e262ee21298e35e867`.
The final source additionally asserts the selected input-kind chip and disabled
Action/Dialogue chips while blocked. These strengthen visible-control coverage
without changing the original outcome or recovery assertions.

## Execution evidence

The coordinator's owned build completed in 75,156 ms, child zero with known
cleanup. Independent parsing of 19 fresh JVM XML files found 150 tests, zero
failures, errors or skips. Lint reports zero errors and one existing
`GradleDependency` warning. The existing unrelated AtomicReference compiler
warning remains; the new fixture introduced no compiler warning.

The reviewer independently rehashed both final APKs and all four packaged
native libraries against the final audit, with exact matches. The application
and native bytes remain identical to the prerequisite; production code is
unchanged. Artifact binding:

| Artifact | Bytes | SHA-256 |
|---|---:|---|
| Application APK | 22,479,391 | `fc01b1ce8516b499d5ca47c518176cba1a93ba4350c2e27d1a14f7ec99950e40` |
| Test APK | 2,368,766 | `eb11f1dd45cee19aadd972b99210fc0a9777352ead35250d94a830f97e664a06` |

Before device dispatch, the reviewer inspected the disabled proposal, exact six
method identities and all-pass fence. All 25 proposal input bindings were
independently rehashed with zero mismatch. The bounded B-only controller retains
the existing package maps, capacity floors and conditional exact test-host
cleanup admission. Any failed or unfinished method stops before post-test
observation or cleanup. The device specialist's 43 pure controller fixtures
passed; these are host controller tests, not Android execution.

The actual B cohort completed in 54,531 ms, child zero with known cleanup.
The reviewer independently rehashed all 46 completed client stdout/status/length
records with zero mismatch. An independent parser matched all six frozen method
names, exact class/current start-pass pairs and the final runner terminal after
all pairs. There was no skip, duplicate or unfinished method. Raw
instrumentation is 4,348 bytes, SHA-256
`f35f70b8cb20b035fb988d0bff7feeed46b71f29a48e5d64a7b506255dca60b6`.

All six methods passed their actual in-test wrapper-drain/four-owner/reopen and
contained cleanup assertions before one conditionally admitted exact test-host
stop. That external stop is explicit hygiene, not evidence of natural Android
process exit or active-model reclamation. The prior stopped cohorts and cleanup
history remain unchanged. All four package maps preserve the original 23
hashes plus the exact admitted application/test pair. Original namespace-absence
and capacity checks passed. Final userdata available was 1,644,441,600 bytes,
above the unchanged 1,207,959,552-byte floor.

The reviewer also independently rehashed the closed host selection: 44 files /
25,039,809 bytes, zero mismatch. Its 8,295-byte index SHA-256 is
`da4e8bfdcc615c2f293b8294e1e568fdb4d9124c5c90eb196ec5c5db25cc7657`.
This describes the indexed selection, excluding temporary files and the index
itself; it is not a claim that every file in a live namespace was sealed.

The closed device selection was independently rehashed: 134 files / 215,225
bytes, zero mismatch. Its 22,707-byte index has SHA-256
`80fcd17373fa9384e45ac98e11dd830c3500c32521ec4ab96ec86bb88df8671d`.
The coordinator's later read-only audit is explicitly outside that indexed
selection. Raw diagnostics, unique identities, private paths and APKs remain
local. The device specialist reports all calls stopped and dispatch lease
released; the reviewer issued no follow-up device command.

## Limits and handoff

M05.04 remains partial and in review, with M05.05 supporting evidence. The six
actual rendered text/recovery cases use explicitly scripted inference, not a
language model. They establish the recorded assertions through the production
transport and existing Rust authority on B, with no new production behavior
change. No A query or two-emulator pass is claimed. A remains blocked by its
previously observed storage floor; M01.01 physical-phone verification remains
blocked. Model quality, active-model cancellation, ARM64 execution, sustained
performance, natural OS process exit and the real-backend reference-phone demo
remain unqualified. No owner acceptance, checkbox, merge or milestone exit gate
follows from this independent review.

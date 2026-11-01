# SDK12 inventory/chat host verification - 2026-11-01

Refs #14 (M10.02), #13 (M09.06), and #307 (supporting M09.04).
Implementation is in review; complete milestone criteria remain unchecked.
No merge, release or Android execution is part of this packet.

## Implementation and source authority

The [fixed profile](PLAYER_INVENTORY_UI_V1.md) adds four concrete SDK12 leaves,
a fixed B59 artifact adapter/baseline, an eleven-method controller, and joined
activation/cleanup. Shared owner, process, socket and storage mechanisms retain
their existing implementation and deadlines. The retirement metadata reader
adds exactly one distinct protocol; no image or ledger operation was performed.
The controller requires the full ordered `Nboot + 35` command grammar and
complete method/raw-client/proof/file rosters. Return code0 alone is insufficient.

Base: PR #328 `dfcb9ad9b9b050e10b9e57472767fec7a0a93e15`.
The four leaves are `112b9bff`; controller/activation are `478b18b6`.
Independent profile tests integrate at `e649af16`; the build adapter/tests
integrate at `b4e97981` from `1da6e8e2`. The imported build files were byte-identical to the tested author checkout;
final test-only platform decorators are described below. Independent agent work used
separate D: branches/worktrees; Root owns integration and the final report.

The independently frozen product is PR #330 at
`ba548cbf6982c58d8a221aea2ed3606232d013d9`, built at
`b8dbbcbb1b3ea67552d7449f94286187a31166ad`. Its separately recorded 439 JVM
cases/52 XML suites, two JNI cross-builds and packaging audits are prior B59
evidence, not tests rerun by this host packet. The adapter rechecks exact sealed
bytes and current inputs using `fixed-b59-byte-attestation-v1`; it does not
repeat XML/DEX/ELF/ZIP/aapt semantic interpretation. Synthetic fixture APKs and
archives are intentionally inert and cannot qualify those semantic checks.

## Actual checks

Each row is a separate recorded execution, not one combined suite.

| Executed body | Actual result | Recorded duration |
| --- | --- | --- |
| `scripts.tests.test_inventory_ui_profile` |9 tests pass,0 failures/errors/skips |0.680s suite;0.961s child wall |
| `test_inventory_ui_build` in the author's isolated loader |14 tests pass,0 failures/errors/skips |3.825s body;3.923s child wall |
| `scripts.tests.test_inventory_ui_activation` |10 tests pass,0 failures/errors/skips |3.514s body;3.936s child wall |
| `scripts.tests.test_inventory_ui_controller` |8 tests pass,0 failures/errors/skips |48.647s suite;61.147s worker including initial graph;61.950s owner |
| SDK11 authority/build-boundary/retirement/import regression selection |16 tests pass,0 failures/errors/skips |2.454s suite;2.879s child wall |
| Author's genuine B59 `create_manifest()` |Pass;310,257,433 bytes/2,798 files,5 allowed read-only Git calls |2.309s body;2.408s child wall |
| Integrated `create_manifest()` -> create-only fixed manifest -> `verify_frozen_product()` |Pass; exact24-source closure unchanged before/after |4.790s body;4.938s child wall |

The new tests total 41 methods across four separate passing cohorts; the 16
SDK11 regressions are a separate selection. Controller tests integrate at
`28d46a8b` from `0f059885`; activation tests at `24e88e92` from `16406d3b`.
All tested method bodies passed without correction; the platform-scope
finding below was addressed separately.
The source-only reviewer compiled both new coordinators without executing them;
six new Python modules also passed Root's in-memory syntax/compile checks. These
are source checks, not additional runtime tests or native ownership proof.

The nine original profile tests reject old SDK11 authority/session/proof names,
changed source or baseline rosters, extra artifact/model roles, nearby command
selectors and derived owner/capture types. Product refusal occurs before native
construction or parent dispatch. Tiny closed-metadata cases require matching
SDK12 identity and all fifteen cleanup flags; native/lifecycle actions are traps.
The fourteen build tests consume actual fixture files, checking source/record/
archive/copy drift, exact artifact roles and manifest equality, strict JSON,
documentation delta, same-object Cargo aliases, missing/third/foreign aliases,
generic hardlinks, late drift/expiry and import side effects. Only fixed fixture
data and Git observation are substituted; favorable validator results are not.

The controller emits one complete 36-client/11-claim graph (3,433,770 bytes),
then replays preserved mutations of it. Generic replay is explicitly required to
stay valid before controller refusal for changed labels/deadlines, incomplete
JUnit and excess staging output; these are consumer-rule tests rather than
stale-hash failures. Other cases cover missing/duplicate/reordered methods or
claims, borrowed proofs/foreign callers, unknown close and installed UID/source
drift. One separate partial graph stops after the first missing exit frame and
never dispatches the next method. Raw framing, claims, closed proof replay and
JUnit parsing are real production code; build/native observations, socket byte
transport, sender and clock are explicit simulations. Worker audit traps record
zero actual native/socket/subprocess calls. Source 27 pins remain unchanged.

The ten activation methods use tiny real bound/create-only files and real SDK12
metadata/authorization grammar, with simulated process identities and owner/
controller outcomes. They exercise the same controller binding twice around
cleanup, changed post-cleanup bytes, unknown caller/no stop, known failed caller/
one stop, failed atomic publication and sticky wait/close/capture/publication
errors. The actual `_enter` birth/parent/request and outer `execute` publication
paths are source-reviewed but not directly exercised by these ten tests.

Independent review found two missing Windows guards on the new physical-D build
and activation fixture classes. `46168c90` adds only `skipUnless(os.name ==
'nt')` class decorators. An AST comparison proves all method bodies unchanged
and the gate is true on the tested Windows host. Those 24 passing bodies were
not rerun for the decorator-only correction; this records platform scope rather
than claiming Linux execution. The controller already declares Windows scope. Independent import/discovery
under write/process/socket/native traps passes (292ms, 14+10 discovered, zero
test bodies executed and zero forbidden calls).

## Fixed artifact output

The integrated source-closure read returns 24 bindings, including the baseline
JSON; complete second readback is equal. No admission or authorization is created.
The create-only manifest is:
`D:/Dev/Experiments/LocalLore/2026-11-01-inventory-ui-cohort-v1/inventory-ui-build-v1.json`
(10,029 bytes, SHA256
`7e67034ee394fa28fabad7d9717fc5d6f77559c86927aa312ef68c7977ae9fe3`).
Its only artifact companions are:

| Role | Bytes | SHA256 |
| --- | ---: | --- |
| Product APK |28,029,072 |`1806fd2594c09cccd8a79bb9c9608f55991f8f79bfe3f6d3f6a0f2660dab3683` |
| Test APK |2,321,082 |`6934df9326aa52353d7a15c5be0823c5227d916a3dcfcc2444feeade3ccece9d` |

Both retain recorded certificate
`17ed497138b20dc1657d54039802305cfe0e3b782c73feaad20359c954707564`.
The fixed baseline is 11,641 bytes/SHA256
`1e7da6ffd02639145d4aa32c6577ccd223ac2a942741f5934b4da826dd33e2be`.
Current native release/deps pairs are admitted only at the two named Cargo
locations, with exactly two links to the same object and matching bytes. Every
other source, APK, evidence and native stage retains the single-link rule.

## Procedure, evidence and limits

Commands ran from physical `D:/Worktrees/locallore-inventory-ui-*` checkouts with
process-local `TEMP`, `TMP`, `TMPDIR=D:/Dev/_Temp`, installed Python3.14 and
`-I -S -B` finite child wrappers. Test modules were loaded explicitly after
inserting the exact checkout into the child import path. No dependency changed.
Build/profile/activation checks use ordinary finite direct children and make no
Windows Job ownership claim. The controller cohort uses its separate bounded
Windows Job owner and records known cleanup/capture and actual-child joining.
Neither category qualifies native Android resource ownership. The public modules can also be reproduced with
`python -B -m unittest <module>` from the appropriate D: checkout; that is a
reproduction command, distinct from the recorded isolated wrappers.

Exact wrappers, complete binary stdout/stderr and terminal/result/source pins
are retained under
`D:/Dev/Experiments/LocalLore/2026-11-01-inventory-ui-harness-v1` in
`legacy-host-v1`, `profile-host-v1`, `build-host-v1`, `integrated-build-v1`,
`controller-host-v1` and `activation-host-v1`.
Synthetic outputs remain under the separate
`2026-11-01-inventory-ui-host-fixtures-v1` root. Controls64MiB, fixtures128MiB,
source worktrees256MiB and recovery128MiB are the declared packet budgets.
Final retained synthetic fixtures total 8,213,109 bytes: the controller/profile
share 5,715,743 bytes; build 1,506,179; activation 679,100; legacy 312,087. This
includes the one full graph, one partial graph and preserved mutation deltas.
No older failed/frozen captures or generated folders were removed or rewritten.
Final source/control recovery uses a create-only copy/ZIP protocol under
`D:/Dev/Recovery/LocalLore/2026-11-01-inventory-ui-harness-v1`; its terminal seals
and independent readback are posted on the tickets after execution. This is not
a full fixture-tree backup; original fixture outputs remain in place.

Independent read-only source/oracle review found no remaining concrete blocker
after the test-platform correction. The separate integration reader rehashed 24
source pins and joined the canonical manifest/three artifact roles to the real
returned result (39 files/656,050 bytes, 6ms); its build-author overlap is
disclosed. It did not repeat the 310 MB product validation. Review is not owner
approval. Held ordinary-file checks are
cooperative producer guards; no hostile filesystem race or ancestor-reparse
attack qualification is claimed. Recorded inner raw aapt/full tool-binary
provenance limits remain. A previous source-helper setup refusal, the untouched
B56 capacity failures and prior B59 reader corrections retain their own records;
none is turned into a success by this packet. A documentation-only edit also
hit the Windows default decoding error; its command record and intermediate
commit remain, and explicit UTF-8 reads/ASCII punctuation correct the report.
No test result or production source changed in that correction.

All eleven new-pair Android methods remain UNRUN. No emulator/ADB/phone discovery,
boot, model transfer, inference, deletion, shared-ledger mutation, system setting,
other-emulator stop or merge occurred. Earlier pending SDK9/10/11 proposals retain
their exact older inputs; their grants/results cannot qualify SDK12. Native/UI
behavior, real IME/TalkBack, physical/ARM64/model performance, story quality,
causal process death and full milestone/release acceptance remain separate.

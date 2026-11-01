# Fixed SDK8 player-presentation UI profile

Refs #307 (M09.04/M09.06), #14 (M10.02). This is the narrowly fixed launcher
profile required by the approved fresh-guest operation. It changes no Android
product, engine, model, package permission, SDK or dependency. No guest run or
retirement is performed by these modules or their imports.

## Separate launcher and product sources

The launcher files belong to the new SDK8 source tree. Its own admitted source
closure, Python/runtime bindings, parent/worker identities, claims and cleanup
remain mandatory. The source chooses the profile; admission JSON cannot choose
a contract, implementation, verifier, package, selector list or product root.

The product remains the exact frozen W1 build at
`D:/Worktrees/LocalLore-record-ui-host-v1`, head
`42ae8f6b7df7373696d35c9a294b6d0517c8886c`. Its manifest remains
`D:/Dev/Experiments/LocalLore/2026-10-31-player-presentation-v2/record-ui-build-v2.json`,
SHA-256 `a8543cd5c421e69d386f0e4b36f9280e771ae1813e09011eae91e562e5135c60`.
Neither that head, its source maps, APKs nor its evidence is relabeled as the new
launcher build.

`player_presentation_ui_build.verify_frozen_product(artifacts)` accepts only the
closed three-binding dictionary for this exact manifest and APK pair. It grants
no target/admission authority. Run this artifacts-only check before creating a
fresh guest or reserving storage. `verify_current(admission)` additionally
validates the SDK8 admission and revalidates its launcher/runtime sources before
and after the product check. Owners apply it before native bootstrap; the
controller applies it before target calls and after completion.

The product check verifies the fixed W1 validator source SHA-256
`6aa95e53312b8f371d4150e004eae9450694c5c7d6661fa9abc0a66bbfe43a0b`
before executing those exact source bytes in a separate normal `benchmarks`
module. It uses the original file location and unmodified whole validator,
including all 2,369 product source files, public pipeline, JVM/XML/lint, APK and
selector checks. It does not load cached bytecode, alter module ROOT/globals,
patch a verdict or accept a caller-supplied loader/path. The internal minimal
artifact argument container to the old function is not a forged admission or
protocol conversion. Its actual lazy project-consumer modules must execute from
the launcher tree with byte-identical W1/W2 source before and after validation.

## Closed fresh-guest authority

- Target protocol: `owned-emulator-player-presentation-ui-v1`.
- SDK protocol: `sdk-player-presentation-ui-v1`; client version **8**;
  session file `sdk-session-v8.json`.
- Proof protocol: `player-presentation-ui-socket-proof-v1`.
- Owner: `owned_player_presentation_ui_owner.py`; boot claim
  `owned-player-presentation-ui-boot-claim-v1.json`.
- Only guest root:
  `D:/Dev/Experiments/LocalLore/2026-10-31-player-presentation-ui-v1/avd-v1`.
- Only packages: `org.locallore.app.archiveverify` and its `.test` package.
- Exactly the same ten record/source/opaque-player methods as SDK7, in the same
  fixed order, with create-only per-method claims. No model material, run-as,
  arbitrary command, selector, profile fallback or alternate root is admitted.

Concrete SDK8 owner and client classes reuse the existing finite ownership,
transport, proof replay, guarded preparation/storage and cleanup mechanisms.
The new controller conserves the existing flow with distinct source-selected
types and result/request/setup/installed tags. SDK7 modules and their frozen
evidence remain unchanged; neither profile accepts the other's admission,
session/client proof or lease type.

Existing guest/resource/port/ownership checks and deadlines remain unchanged:
the approved 8 GiB/four-core API35 guest has a 40 GiB shared-ledger reservation
and a 30-minute maximum, the admitted owner is 1,700 seconds with its existing
1,730-second parent bound, and the controller is 1,200 seconds inside a finite
1,230-second caller. Outer orchestration may allow the already reviewed
1,800-second startup-inclusive bound; it cannot extend the inner owner or
controller. Known caller closure precedes the guarded owned stop. Unknown
closure never becomes a successful run or a released reservation.

## Host evidence and limits

The original ten test methods were frozen before implementation. Their exact
module-absence-only test selector used the old SDK7 implementations for the
baseline: **10 run, five assertion failures and five SDK7 TargetRefused errors
during positive establishment, zero skips**. This is missing-feature evidence,
not an SDK7 defect. Production contains no such fallback. The same ten methods
then pass with SDK8.

At executable commit `0bd49202d7fa4121b532693ffa879188a20d24af`, the combined
finite host cohort passes **38 cases, zero failures/errors/skips**: 15 SDK8
oracles plus all 23 existing SDK7 contract/client/build/controller cases. It
includes mocked binary framing/real closed replay and create-only claims,
post-proof raw preservation, wrong lease/profile refusal, source-drift checks,
and exact-source loader/package/cache checks. Native/socket observations are
mocked; tiny owned D: files are synthetic. No SDK, ADB, emulator, model, phone or
production-ledger operation is qualified by those host cases.

The actual unmocked whole frozen-product replay and independently reviewed
activation controls are separate prerequisites. The approved operation still
requires retirement qualification, fresh guarded capacity/resources, exact
artifact/source checks, unrelated-emulator/shared-service conservation, and
the actual one-guest/ten-method result. All prior failures and every original
guest/recovery record remain retained.

## Actual frozen-product replay (2026-11-01)

The unmocked artifacts-only replay now passes with launcher head
`32d45ee188f7fe2ed1ba8cfd6d5baa352612b0f9` (the executable code is unchanged
from the tested `0bd49202` commit). The original product head remains exactly
`42ae8f6b7df7373696d35c9a294b6d0517c8886c`: all 2,369 product source files,
408 unique JVM cases / 46 XML reports, ten packaged selectors, public pipeline,
lint and original APK bindings pass the whole unchanged frozen validator.
The 34-file SDK8 launcher closure, tool/helper/request bindings and actual
direct-child join are conserved. Owned-job elapsed is 7,757 ms, child exit0;
stdout107 bytes, stderr0. This is a file/Git/ZIP/XML readback, not another JVM
test or Android build/run. It creates no target admission, reservation or guest.

Private result SHA-256:
`d308475b62acf8e4999733de70d2fab8cb717c44fd15768464933156003b75c9`.
The first replay failed after 405 ms because the private audit hook treated the
Windows `nul` stderr sink as an out-of-scope project write. A separate 426 ms
staged diagnosis confirms artifact identity/shared consumers/verified-source
loading passed before that sink refusal in the whole validator. Neither first
record qualifies the product. Both failures remain retained. Only the distinct
v2 private reader permits the exact normal OS sink without create/truncate/append;
project-write/process/socket limits and all production/product code stay
unchanged. No separate WindowsJob/native-resource attestation is claimed for
these fixed direct-Python-child readers.

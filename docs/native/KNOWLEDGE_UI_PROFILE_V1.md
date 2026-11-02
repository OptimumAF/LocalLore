# Fixed SDK16 Knowledge UI profile

B89. Refs #14 (M10.02), supporting #13 (M09.04/M09.05/M09.06).
Implementation and host qualification are distinct from Android execution and
full milestone acceptance. This contract is frozen before implementation.

The profile consumes the exact data-only [B88 build contract](KNOWLEDGE_UI_BUILD_V1.md).
The product/head/APKs/baseline and its four ordered `knowledge_labels`,
`knowledge_replaced`, `knowledge_remount`, `knowledge_text` triples stay fixed.
There are only three artifact roles: `build`, `product_apk`, `test_apk`.
Packages are `org.locallore.app` and `org.locallore.app.test`; model material is
false. No model/probe, caller-selected profile, implementation or path is added.

New constants are protocol `owned-emulator-knowledge-ui-v1`, SDK protocol
`sdk-knowledge-ui-v1`, proof `knowledge-ui-socket-proof-v1`, client version 16,
session `sdk-session-v16.json`, owner `owned_knowledge_ui_owner.py`, and boot
claim `owned-knowledge-ui-boot-claim-v1.json`. Old namespaces remain untouched.
The contract rejects general shell, `pidof` and `am force-stop`, and admits only
the exact finite model-free setup/check operations and four instrumentation calls.
Owner/client/lease/runtime types are concrete, not caller-selected classes.

Source closure includes the current shared SDK4/SDK5 owner, finite client/replay,
storage/recovery guards, every new profile file, the unchanged B88 attestor and
baseline, its shared `library_ui_build.py` reader and instrumentation validator.
All bytes are revalidated. Missing current recovery dependencies cannot select
an older fallback. No new registry, direct SDK creation or permission to launch
follows from having valid metadata.

The guest is fixed to the fresh candidate
`D:/Dev/Experiments/LocalLore/2026-11-02-knowledge-ui-v1/avd-v1`.
The earlier November 1 literal was consumed by the approved SDK15 run and is
now refused by SDK16. This profile neither creates nor adopts a guest. Shared
admission stays two unretired roots, 64 GiB accounting and 40 GiB for preparing/live
guests; preparation and applicable approval remain independent. SDK15 authority
cannot authorize SDK16. PR #354's frozen operation stays separate. See the
[fresh-path/capacity boundary](KNOWLEDGE_FRESH_CAPACITY_V1.md).

`knowledge_ui_profile_build.verify_current(admission)` validates this exact
profile/source set, invokes B88 `verify_frozen_product`, matches the ordered
instrumentations and revalidates sources. It returns the B88 manifest unchanged.
The controller privately projects its verified artifact/package/certificate
fields for setup and replay; no second gameplay or build authority is created.

The controller uses binary-safe staging and hashes, installs the exact pair,
checks package IDs/UIDs/paths/hashes before and after, and requires each original
JUnit result plus explicit shell exit. Four ordered one-use claims, no retry.
It retains every raw client, consumes the complete finite trace and rejects
extra/missing/reordered/borrowed records. One boot poll yields 29 clients.
`feature_acceptance` remains false even after complete host replay.

The existing ceilings stay: 90 seconds/method, 1200 controller, 1230 caller,
1700 owner, 1730 parent, 1800 outer, 400 readiness. No retries or deadline extension.
Closure needs the joined actual caller/worker/source/handle evidence; unknown
cleanup cannot pass or release the shared reservation.

Activation is fixed at source
`D:/Worktrees/LocalLore-original-input-compose-review-v1`, controls
`D:/Dev/Experiments/LocalLore/2026-11-02-knowledge-ui-harness-v1/run-controls-v1`
and runtime `D:/Dev/Experiments/LocalLore/2026-11-02-current-knowledge-ui-run-v1`.
Input is exactly `run-input-v1.json`, scope `knowledge-ui-run-input-v1`.
It validates separately supplied bound input/admission/prepared-guest/run
authorization. Import creates no I/O; activation creates no input, preparation,
recovery grant, human authority, admission or alternative root.

No live input or authority is created by this packet. Actual target execution
needs its own reviewed operation and applicable approval; no earlier spent
answer applies. Host synthetic transport/JUnit/cleanup fixtures establish
protocol behavior, never Android rendering, accessibility, JNI/ARM64 or model
performance. Four Knowledge journeys remain unrun until actual qualified evidence.

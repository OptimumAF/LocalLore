# Owned phone discovery verification — 2026-10-30

Refs #5 (M01.01, supporting M01.05); #14 (supporting M10.03).
[Draft PR #281](https://github.com/OptimumAF/LocalLore/pull/281) is stacked on
open/unmerged [#280](https://github.com/OptimumAF/LocalLore/pull/280).
The supporting implementation is in review; full task checkboxes remain open.
One real owned-service run and the host suite passed. Its fresh USB-enabled
roster contained **zero rows**. No identity, phone inventory, installation,
inference or model qualification follows. The owner chose to continue without
the phone; this packet will not repeat discovery until that scope changes.

## Source and behavior

Executed source is `759c33415b199f65a9e0fcb2f79cc6fd15149482`, with 2,298
tracked raw source bindings. Later report edits retain that attribution.
The [contract](OWNED_PHONE_DISCOVERY_SERVICE_V1.md) describes the distinct
`owned-phone-discovery-service-v1` profile, fixed 5037 port, 30–120-second
lifetime, ordinary USB discovery and disabled active emulator/mDNS scanning.
The old `isolated-adb-lease-v2` remains on 15937 with USB disabled and two
mandatory exact proofs. Phone-mode native readiness sends zero host frames;
its running record has two explicit null proof fields and its worker has zero
proofs. A real running-file binding and all process/source/auth joins remain
mandatory. The separate roster client supplies protocol qualification.

Only two production Python files change. Existing authentication metadata
locking, process handles, output capture and cleanup implementations are reused.
There is no dependency, Android, Rust, gameplay or model change. A foreground
child starts only after native unused-port and exclusive-bind checks. No
occupant is restarted or stopped; cleanup targets the exact owned child.

## Original tests and actual host verification

The original seven-method baseline ran before production integration and had
six assertion failures, zero errors. These demonstrate absent new features,
not defects in the old host-only profile. Its occupied-port case initially
passed because the old helper rejected the unsupported port argument; that
baseline does not qualify the new 5037 preflight.

The original ten-method current-code run passed nine methods and failed one
assertion expecting an invented `cancelled` reason. Existing owner behavior
refuses cancellation with fixed `owner`; the contract requires refusal, no
queries and known owned cleanup, not that new label. The first combined
190-method run preserved the same sole assertion failure. Only that literal
changed to `owner`. All other AST, resource, count, sanitization and no-query
assertions remain unchanged. This is a test-oracle error, not a product
regression or weakened cleanup requirement. Failed sources/results are retained.

| Actual cohort | Result | Owner |
|---|---|---|
| Seven new methods before implementation | 6 failures, 0 errors | 316 ms / return 1 |
| Original ten methods on new code | 1 oracle failure, 0 errors | 770 ms / return 1 |
| First dependent cohort | 190 run, 1 oracle failure, 0 errors | 22,817 ms / return 1 |
| Corrected dependent cohort | **190 pass**, 0 failures/errors/skips | 22,960 ms / return 0 |

The final cohort contains exactly 12 modules: 77 unchanged lease methods,
103 existing roster/inventory/enrollment methods and all 10 new methods.
Those counts are not additive to any prior full-suite result. The new tests
cover literal profiles/ports/lifetimes, environment stripping, cross-profile
stops/records, raw IPv4/wildcard/IPv6 preflight, exclusive-bind closure, the
actual worker algorithm with mocked IO and real closed-result replay, expiry,
cancellation, startup failure, incomplete capture and missing start receipts.
No test starts ADB or contacts a phone. The final owner records known capture
and cleanup, 296 stdout bytes, zero stderr, unchanged HEAD/helper and all 2,298
source bindings. No Android build/device result is substituted.

Exact final command, from the physical D worktree with process-local
`TEMP`, `TMP` and `TMPDIR` set to `D:\Dev\_Temp`:

```text
python -I -S -B D:/Dev/Experiments/LocalLore/2026-10-30-phone-service-v1/check-dependent-v1.py dependent dependent-green-v1 759c33415b199f65a9e0fcb2f79cc6fd15149482 120
```

Selected result SHA-256 bindings:

| Artifact | SHA-256 |
|---|---|
| Feature-absent baseline | `55038925918ad24248d66c4ede5ca005daba4bdb291292e424b016003252d19b` |
| Original ten / oracle failure | `1131f11dd4c081e1678b6afecfb6274bcf8781624b2370fb8fc4047e1943bb99` |
| First dependent / oracle failure | `65a812e63a2d504c64c69f1cd15d5e571359aa76bcc4b174dd031c20584e527f` |
| Final dependent 190 | `18566b791f2385e8adcd8bfd6a50aa25df6b38ea7d717be3f84c624e1f7b5428` |

## One actual owned-service run

After official-source review, tests and separate recipe review, one create-only
admission bound the installed ADB 1.0.41 / 37.0.1-15733141 and unchanged tools,
source/runtime, existing authentication metadata guard and 120-second service
limit. No tool update, model download or credential-content copy occurred.
The earlier failed existing-service attempt in #280 remains spent and unchanged.

Unrun recipe drafts are preserved separately. Before execution, review delayed
stop eligibility until actual owner/request/start/held-process joins; bound
the candidate collector to that exact owned server before its first query;
joined actual candidate parent and worker receipts before promoting flags; and
retained actual return codes, closed output pins and refusal records. These
are draft corrections, not fabricated failed live attempts. The bound helpers
differ from their reviewed templates only in exact source/admission literals.

```text
python -I -S -B D:/Dev/Experiments/LocalLore/2026-10-30-phone-service-v1/actual-v1/run-service-v1.py
```

The actual outer owner returned 0 after **36,606 ms**, with complete capture
and cleanup, empty streams and unchanged source/input pins. The service passes
native unused-port/readiness and held-identity checks. It sends no readiness
queries. The existing roster CLI then completes its version and roster proofs;
the roster exchange takes 74 ms and returns exact empty `OKAY0000` bytes.
The file-only preparation emits `no_candidates`, candidate count zero, with
feature/authority/device-action flags false. It creates no choice or identity.

The exact protocol-bound stop is published once. Service worker elapsed time
is 25,205 ms; all nine cleanup fields are true. The actual terminated ADB child
returns **1**, separately from the successful service CLI parent return **0**.
No exit-zero server claim is made. The outer controller needs no fallback
termination; its capture, Popen handle and observer handles close successfully.
No emulator process is stopped, and no system setting changes.

| Actual artifact | SHA-256 |
|---|---|
| Admission | `2ef15927edd1d22d2f24d1c1632c101f8365d6375cfe292f013819c08cfe53f5` |
| Controller | `a2a434755652b92fdd04a74a54e2c65ff5d6dca5e22a02fcdecf5140825e120e` |
| Candidate helper | `bc2e5fc8e49a23223fede75d3360b63fdcaf07aadf88f73c12dc3243474d5c87` |
| Overall result | `7c274be6592a0ab72401ea3836deee63f4cf3fcb410858a8b2697dd33a6502fc` |
| Service result | `03cc354c8e0abf07977bc955c9b98fa0e7ad7a8de8382fd7fadd9528612fcf36` |
| Service worker | `3505d7e3a5645f78daea950169b4d4f20a8d1224bfa675f6fe295822f5b1f0ef` |
| Roster report | `27785275440b9d9fd83faa06810370c9e2557abf0ea63e0ebe34db3d4e5ffad9` |
| Empty preparation | `d657dae0fd9e7cf264dd87a187913234ad6b46c6246d9b08f808c6b99fdf10b0` |

## Closed audit, preservation and remaining gates

Independent closed replay passes **54 checks** over 2,366 fixed input files:
the real service-worker and enrollment-capture readers, request/start/actual
parent/frame/stop/proposal/HTML joins, 190 unique test IDs, all 2,298 source
files twice, and exact executed-source ZIP membership/raw hashes. Owner 9,718 ms,
return 0, known capture/cleanup, 114 stdout bytes, zero stderr. Receipt SHA-256:
`3e52bb3587c2e48724f6c0ed0c41abce9a840448d90ce6da9fd6f5f82d6b0515`.

Its first checker failed because the 10,184,798-byte source ZIP was sent through
the enrollment JSON pin validator's 2 MiB cap. That checker failure is retained.
The corrected checker validates only that exact binary archive against its
original 16 MiB role cap, fixed path, strict types, full pin and known hash;
all JSON caps stay unchanged. It performs no runtime recapture or gate waiver.

The audit uses selected raw TCP rows and recorded whole-table metadata; full
table bytes are absent and cannot be independently re-decoded or re-hashed.
SDK pins match fixed recorded metadata without a new SDK file open by the
auditor; the actual producer performed its live byte checks. Own Python
runtime/DLL checks are distinct from target acquisition. No fresh process,
TCP, service or phone observation is made by the closed audit.

The verified raw executed-source ZIP has 2,298 members / 31,756,741 raw bytes,
10,184,798 compressed bytes, SHA-256
`f2b510e1d32b53fe0a73a9d77f47019ebf0a05248ffce67bcba50866539adff2`.
Its raw membership matches the actual test capture before/after; Git canonical
bytes or later docs are not substituted. Private originals and recovery stay
under the physical D `2026-10-30-phone-service-v1` experiment/recovery roots.
The packet cap is 512 MiB, including three source trees, recovery and a 32 MiB
retained synthetic-test allowance; final copy/readback evidence belongs in the
ticket handoff. No model, key, APK or guest image contents are copied.

The empty capture is not proof that a physical phone is globally absent.
Ordinary USB discovery/authentication was enabled, so no zero-USB-contact claim
is made. Active emulator scanning/mDNS were disabled; transport invisibility is
not promised. M01.01 and supporting M01.05/M10.03 remain partial/in review.
Physical inventory/model/quality gates are blocked while continuing without a
phone. The next runnable work is the independently claimed M09.02/M09.06 app
validation fix. No merge, release or private diagnostic upload occurs.

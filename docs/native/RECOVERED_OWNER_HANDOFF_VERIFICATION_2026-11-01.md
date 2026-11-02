# Recovered owner handoff verification

Refs #14 (M10.02), B76; supporting M09.04/M09.06. Implemented host slice,
pending owner acceptance and actual execution. Full checklists remain unchecked.

## Result

All current shared owner profiles now admit `prepare_recovery_contract.py`
before live dispatch. Exact historical lists remain structurally readable;
full historical replay requires its preserved implementation. SDK14 current
bindings contain 25 files. Activation uses a new fixed preserved checkout and
fresh controls/runtime paths, preserving the original APKs and nineteen methods.
The [handoff contract](../runtime/android/RECOVERED_OWNER_HANDOFF.md) describes
the source and ledger-v2 boundaries.

The product reader retains the immutable baseline at its recorded original
path rather than deriving a new data identity from its implementation location.
No APK, recorded build manifest, baseline bytes/hash, selector, deadline or
byte/identity/reparse guard was relaxed or resealed.

Tested and frozen code:
`5907d831ea1ce7d410ee2516d21d7f08e34f8637`, at
`D:/Worktrees/locallore-record-actions-flow-v1`, clean branch
`freeze/m10-recovered-owner-handoff-v2`. Prior native/test branches and the
unqualified `9d0f0800` frozen branch remain preserved. Public implementation is
on `impl/m10-recovered-owner-handoff-v1`, stacked on unmerged PR #345
`942f9ea0808c3d1b4312dbbe01ef4172c138a17f`. Later reporting is documentation only.

## Host checks

CPython 3.14.7, Windows x64 build 26300; physical D: working directories with
process-local `TEMP`, `TMP`, `TMPDIR` set to `D:/Dev/_Temp`. No Android SDK,
emulator, ADB, phone, model or production-ledger mutation occurred in tests.

| Cohort | Completed result | Unittest time | Raw stderr SHA-256 |
| --- | --- | --- | --- |
| Original source/dispatch adversaries | 15 passed, zero failures/errors/skips | 1.712 s | `0dfa198dcdeff3d107ee13ee36edcc31eca021fb3290e17da82bb51f36a319fa` |
| Recovered owner/storage spine | 7 passed, zero failures/errors/skips | 8.901 s | `c41e9a54dc784ab9df3f7c56397d48b38bfb4ecdaffff6a4c7fb49d298ef3aa9` |
| Baseline relocation plus existing B66 byte graphs | 17 passed, zero failures/errors/skips | 14.969 s | `6271c665b217df88f7345a816af66d198d4958a7100bb2f9575cec9915dff069` |
| Existing source/owner/activation regressions | 134 passed, zero failures/errors/skips | 118.054 s | `7f31176e6193378a89fc721ea2ec6719bd07b7976fa344afcbb311c1a9fa9211` |

Total **173 completed checks**: 24 new and 149 existing. Repeated and earlier
failed cohorts are excluded. Exact capture commands were:

```powershell
python -I -S -B D:/Dev/Experiments/LocalLore/2026-11-01-recovered-owner-handoff-v1/run-checks-v2.py source source-v2
python -I -S -B D:/Dev/Experiments/LocalLore/2026-11-01-recovered-owner-handoff-v1/run-checks-v2.py storage storage-v2
python -I -S -B D:/Dev/Experiments/LocalLore/2026-11-01-recovered-owner-handoff-v1/run-checks-v2.py baseline baseline-green-v1
python -I -S -B D:/Dev/Experiments/LocalLore/2026-11-01-recovered-owner-handoff-v1/run-checks-v2.py regressions regressions-v4
```

Source/request/raw bindings are captured before and after each bounded process.
Python 3.9 syntax/import and `git diff --check` pass. Independent review matched
87 literal source, request, raw, frozen-input, product and baseline bindings,
with no remaining concrete issue. Review SHA-256:
`16c08e46159ca42b28945aad4bc5d8e625ec0a706d9167f72323ee32ce114fe5`.

Independent source-admission tests were committed as `153216cc`, integrated as
`68a738b0`, and remain byte-identical: SHA-256
`5fd483ec487446cb797224d112bf90e6a87fe9a8b7ff0ca81dfe8f3a737a5992`.
Their coherent FIRST on unchanged `942f9ea0` had twelve failing methods and
three passes, with 23 assertion failures including twelve-profile subtests,
zero errors/skips. The initial incomplete controller-fixture capture remains
separate and is not the coherent FIRST. Actual source hashing remains active;
external SDK/native/product/socket mechanisms are explicitly mocked.

Independent owner/storage cases (`c73680bc`, integrated `f675ef5a`) use real
isolated v2 journals and actual constructor, start/retention and parent closure
storage calls. Build/process/readiness/worker cleanup are explicitly simulated;
this is not physical cleanup evidence. They prove distinct RUN retention before
boot claim, immutable preparation history, exact charges and unknown-cleanup
refusal. An initially mistaken host-output namespace was retained with its
artifact roster, not deleted or concealed.

The two independent relocation oracles (`4228daeb`, integrated `bfbc7f6c`)
have SHA-256
`9b39a7bf0c36aac4f3866f4feac2accf6983faa6a72ff1a0d1872b969421692d`.
FIRST on `9d0f0800` retains the positive original reader but fails both moved
reader subtests. The same test bytes pass after the literal data-anchor fix.
Existing byte-graph mutation, foreign-root, hardlink, alias and verdict checks
remain in place.

## Actual file-only qualification and retained refusals

Initial genuine attestation refused `path_changed`. Its exact changing parent
and cause were not captured; no artifact drift or exclusive cause is claimed.
One bounded diagnostic recorded 2,886 checked files, 283,883,719 bytes and 327
parents, with no parent difference, and called the original verifier unchanged.
It then refused the manifest comparison. A normal, unmodified derivation and
deep comparison identified exactly one difference: `$.baseline.path` followed
the relocated helper instead of the original record. No diagnostic substituted
a verdict, reset a snapshot or rewrote the recorded manifest.

The unqualified 25-file `9d0f0800` source was copied before superseding it:
550,483 bytes, snapshot SHA-256
`52337fb957f932cf1896c39166fcb7eedd8a6c26d9c480b7285dac1abe8719e5`.
The corrected frozen checkpoint then passed the **normal uninstrumented**
`verify_frozen_product` against the original 15,977-byte build manifest
`2fce6b6cfcbbe4c7887b124ec3cf14fde52d893d6d5199a8b1493ddb69cde96f`
and exact original APK pair. Baseline remains 16,380 bytes,
`2bcfa9dee3e8314e8fc24a10b9adec0481a31c165073c9bed9d6e54f138dc5fa`.
This repeats byte/provenance checks of recorded B66 evidence; it does not rerun
the original JVM/native build, recover missing historical XML or qualify Android.

The actual frozen recovery plan is 2,602 bytes, SHA-256
`d5c5fccca7cfc052bb99690936796f59a66067466f1047e3316fca59a3557e9c`.
The 11,843-byte handoff blueprint SHA-256 is
`261224f67c6232869d35c82f86d346b97669193a97ad59a56a5726f45bfa8476`.
It records `ready_for_execution=false`: authority, actual recovery, known
cleanup and fresh prepare/run/admission/input bindings remain pending.
Installed tool and Python leaf pins were rechecked without invoking them;
credential handling was limited to the existing key-path string.

The 41,230-byte shared ledger is unchanged before/after inspection, SHA-256
`4917ec696f7c9f9de5917838aafbd9c2d11184e17c8cbecd71f4eb66ae6a58c5`.
No parent, guest, authorization, activation input, service or emulator was
created. All nineteen Android methods remain **unrun**. Earlier literal-path
regression failures and incomplete/superseded file inspections remain preserved.
Selected outputs/recovery have separate 64 MiB budgets; no private raw data,
credentials, saves or model weights are published.

## Next gate

Only a matching owner-authorized operation may apply the reviewed recovery
plan, migrate the live ledger and prepare the existing charged guest. Later
boot/testing requires the current fixed handoff and fresh storage, resource,
port and native ownership gates. The spent old SDK14 grant and frozen old
activation cannot be reused. Other emulators, shared ADB and settings remain
untouched. No merge or release occurred; device/model/ARM64/accessibility,
causal process-death and full milestone acceptance remain separate.

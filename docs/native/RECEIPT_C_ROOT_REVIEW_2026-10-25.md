# Explicit C-root receipt environment review — 2026-10-25

Refs #9 (M05.05 prerequisite), #5 (M01.05 supporting). This independent review
found no concrete source blocker in author commit
`ea97f937880f793e7b11f4b8234af77efcbbca5a`. It is a separate preparation packet,
not evidence of a new environment, model execution or completed milestone.

The reviewed actual files match these SHA-256 values:

| File | SHA-256 |
| --- | --- |
| `benchmarks/receipt_avd_environment.py` | `0c6eab7c344aa407346431f42a53b9e955f440aa0da68aa6166dec1aa93229b1` |
| `scripts/tests/test_receipt_avd_environment.py` | `abee3b9892e00b16dfcb6c7b9c932b6280c606c4fc271a992b4e618206da4d20` |
| `docs/runtime/android/RECEIPT_AVD_ENVIRONMENT.md` | `1eda9239ae070de21a70b33b503ddb0baf75c70901d819c5605f692890d6b20a` |

## Boundary inspected

`root_free_min` derives the floor pair from the explicitly supplied C: or D:
drive; it does not inspect free space to choose or redirect a target. Planning
still requires an absent, absolute, normalized, nonlinked target. Existing
ancestor/reparse checks remain in `safe_path`.

| Explicit root | C: minimum free | D: minimum free |
| --- | ---: | ---: |
| D: | 16 GiB | 40 GiB |
| C: | 40 GiB | 40 GiB |

Both proposal phases require the exact integer floor pair derived from their
bound root. Unsupported drives, relative/drive-relative/boolean roots,
lowered/swapped/extra/mistyped floors and escaped child paths refuse. The
D-root proposal fields, floor policy and sorted-binding format remain unchanged;
the changed helper source necessarily requires a fresh source binding and
authorization. This does not preserve or revive a consumed proposal hash.

Downstream preparation/run checks still bind every content/registry/preferences/
temporary path to the one root. `verify_prepared` compares the complete original
prepare proposal against run fields, exact prepared/config/registry/initial-disk
bindings and successful preparation closure. A separately valid D-root proposal
cannot adopt a C-root preparation. Live leases still pin the proposal and running
descriptor hashes, root/content/registry, immutable metadata, executable and
PID/creation identity, deadline, stop/result absence and preserved external state.

The diff adds no target search, fallback, movement, deletion, repair, reuse,
privilege change or old-environment operation. Memory, CPU, userdata/SD size,
authorization, stdin barrier and lifetime/cleanup policies are unchanged.

## Actual synthetic verification

The author retained both targeted attempts. The first ran 11 tests with one
test-oracle failure: the expected fixture used insertion-order bindings while
the existing planner sorted them. The production helper did not change between
attempts; the expected binding order was corrected. Its owned child returned 1
with known cleanup, 1,438 ms, 2,337 stdout bytes SHA-256
`6ad819f23eda3f9eb257442a8dbbf091b80088cf135758188e77455946c7e017`.

The corrected author selection passed all 11 tests (seven C-root cases and four
prior D/profile regressions), runner time 0.898 s. Its owned child completed 0
with known cleanup, 1,282 ms, zero stderr and unchanged source bindings; 1,540
stdout bytes SHA-256
`c954915a4248051924db038ccea58e50e21354f09e53cb83e6804e6ded40c02c`.
This review independently rehashed both retained raw outputs and read their
terminal records; it did not rerun an SDK operation.

The reviewer independently executed a targeted Python `unittest.TestSuite`
against the actual author checkout: all seven new cases, plus eight existing
lease/replay cases with a derived fixture whose `setUp` changes only
`self.root = self.c_root()`. **15 tests passed, zero failures/errors/skips,
1.621 s, command exit 0**, using `python -B -E -`.

The C-root lease variants covered mutable guest-disk acceptance, avoiding SDK
rehash during cheap checks, PID reuse, expiry, stop/result revocation, descriptor
drift, immutable-config drift and consumed-run refusal. The seven new cases
covered proposal planning/default D compatibility, typed paired floors in both
phases, unsupported roots before SDK inputs, existing/symlink refusal, child-path
escape, exact/one-byte-short reserve boundaries and cross-root/replay refusal.
Only tiny synthetic files and temporary host directories were created; process
identities, memory/disk boundaries and child admission were mocked. No real
8 GiB SD disk, SDK tool, ADB, AVD, weights, model or native build ran.

## Limits and next gate

This is source/targeted-host review, not full-suite, live Windows environment,
guest, phone, SDK resource or model qualification. Floors are fresh boundary
observations, not reservations against unrelated processes. Existing failures,
saved targets, model/privacy/device holds and consumed admissions remain intact.

The coordinator may integrate this focused change and prepare a new disabled,
source-bound proposal for an explicitly chosen absent C-root. Actual creation or
launch requires its separate fresh review, capacity/ownership checks and
admission. No merge, release, access change or task checkoff is inferred here.

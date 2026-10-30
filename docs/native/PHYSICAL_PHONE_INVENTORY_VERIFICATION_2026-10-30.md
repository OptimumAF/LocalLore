# Read-only phone inventory verification — 2026-10-30

Refs #5 (M01.01, supporting M01.05); #14 (supporting M10.03).
The host implementation is locally verified and in review in
[draft PR #278](https://github.com/OptimumAF/LocalLore/pull/278), stacked on
open/unmerged [#277](https://github.com/OptimumAF/LocalLore/pull/277).
Full milestone criteria remain unchecked. No actual phone acquisition,
hardware/model acceptance, Android execution or release is claimed.

## Implementation and source

The old physical collector can restart a shared service through the ordinary
ADB executable. Three new modules provide a separate fixed read-only path:
`physical_phone_inventory.py`, `physical_phone_inventory_windows.py` and
`physical_phone_inventory_probe.py`. Four new original test modules exercise it.
Existing implementations are unchanged; there are no dependency, Android,
Rust, APK or product-policy changes.

One source-bound worker acquires version and roster proofs, then the exact
retained authorized row. On one new held socket it asks the server for its
sole USB transport, compares the returned ID before any device service, and
runs one code-fixed inventory script. Private raw wire and typed facts do not
grant model pre-install eligibility or substitute for authorization.
The [protocol](PHYSICAL_PHONE_INVENTORY_PROTOCOL_V1.md) specifies the full
ownership, attempted-write, framing, bounds, source/worker and cleanup rules.

Base is `2675230c9c909a6ae563657e6768a9d3a29d87d1` on #277. The integrated
executable tested here is `b3e5a13b511aed5e82a0a8d3fdaeb7398953cdbc`, with
2,289 tracked raw source bindings. Subsequent report/README edits retain that
execution attribution. Agent cohorts have their own recorded heads and raw
source hashes; their results are not relabeled as executions of Root's checkout.

## Original failure and repair

The first backend cohort ran seven original methods and failed one assertion.
A synthetic owned socket changed its endpoint during receive; the new adapter
checked it before the read but returned normally without checking afterward.
The test required refusal with the actual received bytes retained. The sibling
post-read deadline case already passed and is not presented as a failed test.

The fix adds one endpoint recheck after immutable byte capture and type/limit
validation, before returning. The existing resource operation poisons the
backend on failure; the private receive-refusal channel retains the bytes.
The same seven tests then passed unchanged. Query sequence, deadlines, caps,
live ownership joins and cleanup were not weakened. Git's logical change is
one line; each capture retains its checkout's actual raw bytes/line endings.

Original failed result SHA-256:
`6d37da2312aea32c93d41f3adfb82ee24a63cdb67ce5a46020d4cfc069c388fc`.
The original 2,456-byte backend source has SHA-256
`16b801c6d5dcc94e0193c2a9f0379a73e069cd8a02caa2f99ac617b8d6266726`;
its recorded source pin also matches the preserved pre-fix Git object bytes.
No failed source or result is rewritten into a pass.

## Verification actually performed

All project commands ran from physical D: worktrees, with process-local
`TEMP`, `TMP` and `TMPDIR` set to `D:\Dev\_Temp`. Private scripts, captured
output, raw source maps, owner records and receipts remain outside Git under
`D:\Dev\Experiments\LocalLore\2026-10-30-phone-inventory-v1`.
Host tests use fake transports and synthetic resource/fact bytes. Finite
supervision runs owned Python processes; it does not acquire a real ADB socket,
execute the ordinary ADB client or access a phone/emulator/model.

| Actual cohort | Result | Owner and private evidence |
|---|---|---|
| Original contract/facts | 14 pass, zero failures/errors/skips | 829 ms, return0; `adversaries/first-v1` |
| Original backend, before fix | 7 run, 1 failure, zero errors/skips | 368 ms, return1; `adversaries/backend-first-v1` |
| Same original backend, after fix | 7 pass unchanged | 417 ms, return0; `adversaries/backend-green-v1` |
| Original CLI | 7 pass, zero failures/errors/skips | 4,726 ms, return0; `adversaries/cli-first-v1` |
| Complete integrated host discovery | **2,377 pass**, zero failures/errors/skips/expected failures/unexpected successes | 444,184 ms, return0; `full-host-v1` |

The disjoint new cohorts contain 28 methods; they are included in the full
2,377 count, not additive to it. All owners report complete output capture and
cleanup, zero stderr and stable source bindings. Full discovery loaded all
131 test modules before execution, with zero failed imports/loader errors.
The full source, helper and HEAD remained unchanged, and the checkout was clean.

The exact finite full-suite command was:

```text
python -I -S -B D:/Dev/Experiments/LocalLore/2026-10-30-phone-inventory-v1/check-full-host-v1.py full full-host-v1 b3e5a13b511aed5e82a0a8d3fdaeb7398953cdbc 600
```

It uses canonical complete `scripts/tests` discovery without exclusions,
captures the actual test roster/import preflight and uses a finite600-second
owner. The wrapper was fully compiled before execution; Root verified its
exact two-literal adaptation from the previous reviewed host runner.
Normal repository test entry point:

```powershell
python -B -m unittest discover -s scripts/tests
```

Selected private receipt SHA-256 bindings:

| Artifact | SHA-256 |
|---|---|
| First14 result | `2578e81546e1eb1631072aac45d6982d66a3d5b91b83bd2fbef35241cc854dcc` |
| CLI7 result | `91230bf42db969dd7c116bf39b5a584d5d1974d79d6a37d8166aa686c6de0abe` |
| Backend7 after fix | `68f417d64691610d951374d8b4bc0fbd705bf85173fb382755eb2fd6b0a2d9b8` |
| Full integrated result | `20b6f33b4fc1a4da9e11b33bbec12f5d22711ac6c62abc336c46617218c1578d` |
| Full integrated owner | `6ef8d5953f6393a248807f5c8d82811867d8183f1b40be38bae277242b266f4e` |
| Full test roster | `18bea995315acb0c8ccfd0d89452dae3bba32d912b6a6e661453de6735b7e5aa` |
| Full runner | `b3c009f6feb7a50c4e8a5c40139015773144aab6d99b04301f32614c8c5ba63e` |

The separate runtime-spike implementation/test Python files are byte-identical
to the base. Their prior 16-pass B12 result retains its dated source attribution;
it was not rerun or promoted into new runtime/model evidence. No Android build
or device test was appropriate to this source-only host change.

## Independent review and closed replay

Primary AOSP review confirms the USB selector's native transport ID and
same-connection selection, shell framing and fixed sensor commands. Source
review precedes the backend failure; a separate narrow review covers its fix.
Post-read-fix source receipt:
`052c33dbc4874e17f7f7732c74c3aefee8a1cbbbd805d2f69b7cb1040ff19555`.
This review is not binary/device attestation or human acceptance.

Independent closed-file replay checked 2,335 explicit files, the exact2,377
unique test IDs/131 modules, all28 new AST test methods and2,289 raw source
bindings, including a second source readback and the exact tracked roster.
It preserved the distinct agent cohort heads and original failing backend,
and found zero mismatches or unsafe paths. No tests or acquisition were rerun.
The finite audit returned0 after10,169 ms, with complete output and zero stderr;
receipt SHA-256:
`f84fd6a82b2c7864873fe812898684cb6ab7c90aeadd7514df4ed9cef4c961b6`.

The first audit helper failed before result-byte validation because it compared
whole stat tuples, including last-access time. Diagnosis found only access time
changed during a normal read; stable identity fields and content did not drift.
Original checker source/trace/owner/diagnosis are preserved. A distinct corrected
checker excludes only access time, retaining all stable per-API identity, byte,
hash, source, roster and owner checks. This is checker preparation evidence,
separate from the product failure and tests. No product test was weakened.

## Limitations and handoff

**No actual host or phone inventory acquisition ran in this packet.** The
retained exact authorized identity is unavailable to this controller, and the
earlier empty roster supplies no global absence, presence or substitute phone.
Actual selection, software inventory, memory/storage/thermal admission, package
and APK preservation, installation, model inference, cancellation and restart
remain separate gates. Typed facts and synthetic traces do not qualify them.

M01.01 and supporting M01.05/M10.03 implementation: **in_review**. Full
checkboxes and owner acceptance remain unchanged; no merge/release is implied.
Private evidence and current recovery are preserved on D. The packet's declared
cap is1 GiB for four source worktrees, scripts, captures and recovery; no model,
key, APK or guest-image contents are copied. Final recovery counts, independent
readback and manifest hashes are recorded in the ticket handoff after sealing.
Unexecuted preservation drafts and their pre-execution containment correction
remain distinct from actual copy results.

Next runnable runtime step requires the retained authorized identity or a
separately reviewed identity-establishment scope, meaningful fresh visibility
and exact source/host/target admission before this fixed inventory path runs.
The existing physical collector is not silently invoked as a fallback. Existing
emulators, service lifecycle, settings, old failures and recovery remain intact.

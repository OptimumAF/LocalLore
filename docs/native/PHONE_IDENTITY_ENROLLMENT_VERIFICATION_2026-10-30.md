# Local phone identity workflow verification — 2026-10-30

Refs #5 (M01.01, supporting M01.05); #14 (supporting M10.03).
[Draft PR #280](https://github.com/OptimumAF/LocalLore/pull/280) implements the
host workflow and remains in review, stacked on open/unmerged
[#278](https://github.com/OptimumAF/LocalLore/pull/278). Full task checkboxes stay
unchecked. The actual candidate attempt below **refused before any host query**;
there is no phone inventory, enrollment, identity or model qualification.

## Implemented scope and source

Two additive modules provide pure proposal/choice handling and a fixed file-only
CLI. They replay the existing roster capture, create an escaped private local
review page and require a direct human choice against the exact proposal hash.
A sole candidate is never auto-selected. A receipt declares identity only:
all feature, authority-authentication and device-action flags remain false.
Fresh runtime inventory retains its independent USB/transport/ownership gates.
The [protocol](PHONE_IDENTITY_ENROLLMENT_PROTOCOL_V1.md) defines the canonical
file roles, source/runtime/proof checks, create-only publication and limits.

Base is `d3ec1412688207db0c80729a2bcb41574d8c9f3d` on #278. Integrated tests and
the actual host attempt use frozen executable
`0fce949c1d5427e260c4480eadd19030632ccda7`, with2,295 tracked raw source bindings.
Later verification/README edits retain that attribution. Existing executable,
Android, Rust and dependency files are unchanged; no new backend or controller
is introduced. Agent cohorts retain their own branch/head/raw-byte bindings.

## Original tests, failures and fixes

The first seven pure tests passed. The original seven IO tests passed six
methods, with one test ERROR because a reparse refusal raised the existing
`EnvironmentRefused` rather than the test's overly narrow `ValueError` tuple.
Refusal occurred before content IO. Only that exception tuple was corrected;
the before-open assertion and other six methods stayed unchanged. This is
preserved as an oracle error, not a product bypass or fabricated behavioral RED.

Three new original regressions then produced6 assertion failures/0errors:

- An actually imported inventory module was absent from enrollment source pins.
- Current fixed source/runtime could drift after capture replay, during output
  publication, while the operation still reported success.
- A missing D: bundle escaped the public CLI's sanitized refusal handler.

The fixes bind the third transitive module, retain/recheck accepted source/runtime
values throughout publication, check after identity write before the success
record, and sanitize the delegated environment error. All17 tests then passed
unchanged apart from the separately identified exception-oracle correction.

A final original method produced6 assertion failures/0errors: missing preparation
metadata or altered review HTML still allowed an identity/confirmation record.
The fix in `_selection` requires canonical preparation roles, reconstructs the
complete expected marker, checks exact deterministic review-page bytes and
retains both pins through confirmation/loading. It does not authenticate human
intent or prove which bytes a human previously viewed. The original assertions
pass in the dependent run below. All failed source versions/results are retained.

## Actual focused verification

All commands ran from physical D: worktrees with process-local
`TEMP`, `TMP` and `TMPDIR` set to `D:\Dev\_Temp`. Private source maps, scripts,
stdout/stderr, owner/started records and receipts remain outside Git under
`D:\Dev\Experiments\LocalLore\2026-10-30-phone-enrollment-v1`.

| Actual cohort | Result | Owner / evidence |
|---|---|---|
| First pure | 7 pass | 318 ms/return0; `adversaries/pure-first-v1` |
| Original IO | 6 pass, 1 exception-oracle ERROR; no unsafe read | 5,022 ms/return1; `adversaries/io-first-v1` |
| Three source/runtime/CLI regressions before fix | 3 run,6 assertion failures,0errors | 873 ms/return1; `adversaries/review-first-v1` |
| Combined pure/IO/review after fix | 17 pass | 6,436 ms/return0; `adversaries/combined-green-v1` |
| Presentation before fix | 1 run,6 assertion failures,0errors | 1,175 ms/return1; `adversaries/presentation-first-v1` |
| Integrated dependent cohort | **103 pass**,0failures/errors/skips/expected failures/unexpected successes | 13,808 ms/return0; `dependent-v1` |

The dependent run selects exactly10 modules: four roster, four inventory and two
enrollment modules, totaling57+28+18 methods. All10 loaded with zero loader/import
errors. All2,295 source bindings, HEAD and helper stayed unchanged; the checkout
remained clean. Capture/cleanup completed with209 stdout bytes and zero stderr.
The18 new methods are included in103, not additive to it.

Exact actual command:

```text
python -I -S -B D:/Dev/Experiments/LocalLore/2026-10-30-phone-enrollment-v1/check-dependent-v1.py dependent dependent-v1 0fce949c1d5427e260c4480eadd19030632ccda7 120
```

This is a focused run, **not** a new full2,395-test result. The unchanged base's
prior2,377-pass result retains its original source attribution. No standalone
runtime-spike, Android build or device test was repeated for this additive tool.

Selected private result SHA-256 bindings:

| Artifact | SHA-256 |
|---|---|
| Pure7 | `ca0c57f4ffac02cad473acf86eda45184c2cb89884f494cf50ce80a812f65e1f` |
| Original IO7 oracle error | `c3c3bcab6d5c8eb9c2d6a8456d36083f38e020c03f9b6d1c8b224460fd0e8b5a` |
| Review3 before fix | `8614fadf0192704da30b4e635a8e58895bfdc65a864ca970c2c9756d4fb32174` |
| Combined17 | `30bcfe828ce1c9d06d439304fc266a3d1c9d406bc30ef46a3131c041b4caa912` |
| Presentation before fix | `a0e0fba60c5f1799ecc803aa368d530a127d1f9c75b2da94d7b920ff57503d58` |
| Integrated103 | `b3734d50942418fe3e9c91b6ea20e2bda819daf6513c08b75b2ca9aae656d9b0` |
| Dependent runner | `e4ce22df874e8370d5b039368a6d327604d21ddb682ba5eee5d0babfa18cf8f8` |

## One actual candidate attempt: preflight refusal

After code/tests and separate recipe review, one source-bound host-only attempt
ran to create a current review proposal. It did not retry the earlier empty
roster or invoke a fallback client. The fixed recipe permits existing-service
native preflight, version/roster queries, one spent postflight and file-only
`prepare`; it has no confirmation, USB selector, phone command or auto-open path.

```text
python -I -S -B D:/Dev/Experiments/LocalLore/2026-10-30-phone-enrollment-v1/candidate-acquisition-v1/run-candidate-proposal-v2.py
```

Limits remain90-second outer,45-second CLI parent,30-second public roster worker,
three-second exchanges and fixed installed ADB pin read in place. No ADB program
or service lifecycle operation is permitted. The unbound template and first
bound draft are preserved unrun; v2 corrects only a completion label so a failed
preflight cannot claim acquisition merely because a worker result exists.
This pre-execution correction is not labeled a product failure or retry.

**Actual result:** outer owner6,172 ms, child1, complete capture/cleanup, empty
streams, all2,295 sources and input/tool pins stable. Both saved scoped snapshots
contain zero selected local5037 rows and zero listener-shaped candidate PIDs.
The exactly-one-PID gate refused **before process lookup, admission publication
or CLI spawn**. A single mandatory metadata postflight also refused; the original
preflight category remains primary. There were zero version/roster queries,
zero prepare calls and no review/choice/identity/device operation.

Result SHA-256:
`879b5f4f5956e3638d062a43a36a74bf66050a5f89a22c4bd10c65ac5a5ed49c`.
Closed diagnosis:
`f060dbc7a0bdb0bff34d38719c61d78acd4f00f9117631b0f319f12720645217`.
The two scoped table records share SHA-256
`db4f6dd4666adb9eec8c16975c4f430961f2367e887efb29d789183e7bb6595e`.
Actual source decoded whole-table metadata reports217 IPv4/490 IPv6 rows;
only selected5037 rows and whole-table count/size/hash metadata are retained.
Full table bytes are deliberately absent, so closed audit cannot independently
re-decode those unavailable bytes. This result proves neither global service
absence nor physical-phone absence or availability.

## Independent audit and handoff

Independent source review identified the original issues and reviewed their
narrow fixes. A separate closed-file audit then checked2,357 explicit files,
all2,295 current source files twice, the dependent103 unique method roster and
all18 new AST methods, plus the distinct historical cohorts. It checked the
actual request/started/worker/owner chain, empty streams, zero-followup branch,
stored selected rows and bounded metadata. SDK pin metadata was matched without
reopening the SDK executable; own installed Python binary/DLL hashes were checked
using fixed runtime paths. It found zero mismatches/unsafe paths and returned0
after14,573 ms with zero stderr. Receipt SHA-256:
`b124c7d8276f4bebfa7aed14b9f699980a3bb2923a9af626a86bdd739d0af633`.

That audit pass verifies the preserved refusal, not successful acquisition,
physical hardware, user intent or authority. No runtime call/test was replayed.
The attempt remains spent at the missing existing-service boundary. No service
is started/stopped, no other emulator is touched and no system setting changes.

M01.01 and supporting M01.05/M10.03 implementation: **in_review**. Actual
enrollment is blocked earlier on fresh existing-service availability/admission,
then direct human identity choice and fresh runtime admission. A future reviewed
service-readiness scope is distinct; do not repair the condition by weakening
the gate, polling until favorable or invoking ordinary ADB silently.

Private captures, source snapshots and recovery are kept on D, within the
declared768MiB packet cap for three source trees, scripts, fixtures and recovery.
Final preservation/readback counts and hashes belong in the ticket handoff after
sealing. No model/key/APK/guest-image contents are copied, and old failures,
ignored data and charged guest roots remain in place. Full milestones, physical
inventory/model/quality gates and owner acceptance remain incomplete. No merge,
release or private diagnostic upload is implied.

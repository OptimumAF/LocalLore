# Safe checks verification — 2026-10-22

Scope: M03.05, [milestone #7](https://github.com/OptimumAF/LocalLore/issues/7).
This is dated local/static execution evidence, not owner acceptance, a hosted
workflow pass or a new roadmap tracker. Current implementation prerequisites
#18/#19/#20 are unmerged. The packet starts at #20 head `3797e9e` with a clean
working tree and stacks a focused PR on `impl/m03-native-engine`; nothing merges.

## What changed

`scripts/check.py host|android [--offline]` is the shared local/workflow entrypoint.
It resolves the checkout from its own file, uses argument arrays with no shell,
runs serially, and stops on the first failure. Missing tools fail without
provisioning. Host checks cover Rust format/lint/tests, fixture parity, Python
regressions and standalone linker tests. Android checks verify the existing
official Gradle wrapper JAR/properties before launching Java, build app/test APKs
and both Rust ABIs, run JVM/lint checks and audit the final APK. `--clean` is
Android-only. Offline flags reach Cargo and Gradle; SDK auto-download is disabled.

The standard-library APK audit checks current ABI/library sets, ELF64 machine/
segment bounds/alignment, uncompressed 16 KiB native ZIP alignment, SDK levels
and the sole app-owned signature permission. It rejects duplicate entries,
packaged recorded fixtures and additional permissions/libraries. Changes to
these explicit build contracts need review. This is not a general hostile-APK
verifier, network/backup audit or device qualification.

`.github/workflows/checks.yml` defines host and Android jobs using those commands
on fixed standard `windows-2025` hosted runners. Events are ordinary PR and main
push; contents permission is read-only, checkout is SHA-pinned with persistent
credentials disabled. No secrets, caches, artifact uploads, environment deployments,
custom/private runners, model downloads or script interpolation of PR text.
Timeouts and concurrency bound execution. Provisioning uses existing image JDK17,
explicit Rust/SDK versions and negative input to any new SDK license prompt;
postconditions fail if required packages remain absent. No license acceptance
or repository setting is performed by the checks.

## Independent work and reviewed dependencies

Coordinator: `impl/m03-safe-ci`, shared workflow/audit/integration/docs/evidence.
Independent runner agent: `impl/m03-check-runner`, separate checkout, owns the
check runner, orchestration tests and CHECKS document (`d00ed20`). Independent
reviewer: `review/m03-safe-ci`, separate checkout, owns official source/license
and concrete review artifacts (`21474e7`, `68a9097`). Task claims, ownership,
stable CLI, acceptance and handoffs were posted on #7 before edits. Agent commits
are integrated centrally without writing into each other's paths; claims are
handed off to PR review. An agent's finite review is not owner approval.

The reviewed action is checkout v7.0.1 at
`3d3c42e5aac5ba805825da76410c181273ba90b1` (MIT, node24). Official action source,
runner minimum/version behavior and hosted Windows image inventory were inspected
before introducing it. The OS label is fixed; image/tool patches float weekly,
so this is not a hermetic environment pin. Current image inventory includes the
required SDK/NDK and Java17/Python/Rustup. The project still explicitly selects
Rust1.93.1, NDK29.0.14206865, platform36 and Build Tools35.0.0. No production app,
model, native dependency or Cargo/Gradle lockfile changed.

The reviewer downloaded actionlint1.7.12 under ignored build output and verified
the official archive digest and upstream checksum before executing it. It is a
local validation tool, not a new runtime/developer/CI dependency. Exact sources,
licenses, digests and limitations: [source record](SOURCES_2026-10-22.md),
[independent review](REVIEW_2026-10-22.md).

## Actually executed

Local Windows x86_64, Python3.9.12, JDK17.0.6, Rust/Cargo1.93.1, Gradle8.11.1,
AGP8.10.1, NDK29.0.14206865. Existing authorized tool/cache provisioning was reused;
these local runs installed no tools, accepted no licenses and changed no devices.
Application and Rust engine sources are unchanged by this packet.

| Command/check | Actual result |
|---|---|
| `python scripts/check.py host --offline` | Exit0: format, workspace Clippy `-D warnings`, 34 Rust tests, 4 legacy fixture cases, 5 benchmark Python tests, 18 runner/audit Python tests, linker format and 3 compiled linker tests passed |
| `python -m unittest discover -s scripts/tests -p 'test_*.py' -v` | 18 passed: 13 orchestration and 5 APK test methods, with multiple adversarial subcases |
| `python scripts/check.py android --offline --clean` | Exit0: 78 Gradle tasks executed; actual x86_64/ARM64 Rust release libraries rebuilt, debug app/test APKs compiled, 11 JVM tests passed, lint reports no issues; final APK audit passed |
| `python scripts/audit_apk.py apps/android/app/build/outputs/apk/debug/app-debug.apk` | Exit0 against actual built APK: four expected libraries, all LOAD alignments16384; uncompressed native ZIP data16KiB-aligned; min26/target36 and only app-owned signature permission |
| `actionlint.exe -no-color -shellcheck= .github/workflows/checks.yml` (verified tool in review worktree) | Exit0, no diagnostics; ShellCheck explicitly disabled because this workflow uses PowerShell |
| PowerShell `Parser.ParseInput` over each workflow run block (local installed PyYAML6.0 used only to read YAML) | Six blocks parsed, zero syntax errors; provisioning blocks not executed or inferred successful on a hosted image |
| `git diff --check` / staged equivalent | Passed before handoff |

The adversarial tests prove first-error/interrupt propagation, unknown arguments,
missing executables, offline/locked transport, unrelated working directory and
spaces/apostrophes, and modified wrapper rejection before launching Java. APK
tests include missing/wrong/compressed/unaligned native libraries, ELF truncation/
bounds/small alignment, duplicate ZIP entries, legacy fixture packaging, added
Internet/contact capability, wrong SDK/package and weakened permission protection.
These are finite regressions, not a claim that arbitrary workflows or APKs are safe.

[Sanitized summary and APK digest](TEST_RESULTS_2026-10-22.json) and
[actual packaging result](APK_AUDIT_2026-10-22.json) omit raw host/device logs,
transport identifiers, user paths and secrets. Raw build reports remain ignored.

## Gates and next work

Remote GitHub-hosted execution is **not established by local/static validation**.
The connector rejects the Actions-permission endpoint, so current enablement
cannot be reverified through that connector. Historical disabled setup is not
treated as a fresh settings audit. Repository Actions settings are unchanged.
Any actual run observed after PR creation must be tracked by its specific run
handle and recorded separately; absence of a run is not a hosted pass.

No emulator is started or exercised by this packet: no application/lifecycle/FFI
runtime code changes. Prior M03.03 [native/emulator evidence](../native/VERIFICATION_2026-10-22.md)
records its 22 passes and cancellation/resource cases; those are not new results
of these compile checks. ARM64 is built/packaged only. No physical phone/model,
thermal/performance/16KiB-OS, durability, release or privacy qualification follows.
The M01 physical/model blockers persist; no benchmark or support profile is invented.

M03.05 implementation is locally verified and handed off **in_review**, with
hosted execution/owner acceptance still pending and all milestone tasks unchecked.
Next runnable task: M03.06 bounded privacy-safe local diagnostics, explicit
preview/export and no remote collector. Storage M04 remains behind its dependency
gates. No merge, release, access/protection/Actions-setting change or spending.
Material AI assistance: coordinator plus independent runner/review agents;
original synthetic fixtures only. Live plans/work-log remain in GitHub Issues.

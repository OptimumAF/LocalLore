# Normal-package reproducibility checker review — 2026-10-23

Independent reviewer: coordinator `/root`, author `/root/desktop_runtime_profile`.
Claim #31 comment 6370383542. Integrated source `d932551` imports the unchanged
five-file author packet on accepted main `59fa8e8`. This is partial D09.03/.07
in review; both actual application byte comparisons remain failed.

Read the complete checker, its meaningful comparison/refusal tests, the two-line
normal packager patch and dated evidence. No remaining concrete blocker was found
for retaining this development checker and honest failed qualification evidence.
The checker runs normal package builds in two separate clean detached source
worktrees with independent empty targets, temp directories and dependency copies.
It launches no app, inference worker or model. Tool and source inventories bind
the stated installed environment before/after; supplied npm file hashes bind
that tree, not registry authenticity. Known sibling rustup proxies are identified
explicitly rather than accepting arbitrary executable indirection.

Comparison includes raw PE, the complete ZIP bytes, ordered member metadata and
all payload hashes including the packaged manifest. No byte normalization,
manifest exemption, compiler metadata override or special passing fixture replaces
the real application gate. Destination overlap/reparse/occupied-output and
unapproved-worker/ambient-flag/dependency/source drift checks fail closed.
Local manifests may contain paths/environment; committed evidence is sanitized.
Outputs are create-only and retained on failure, with no cleanup command.

The packager adds one internally derived encoded Rust flag mapping its actual
source root to `/locallore-source`, after refusing caller Rust flags. This is
one argument even with spaces and applies to all Rust compilations; the existing
final `/Brepro` remains. Its stable policy is recorded in the package manifest.
The actual second cohort proves removing literal source paths is insufficient:
outside-workspace path dependency identities still differ. No raw equality is
claimed. Root/workspace/lock alignment is a separate active implementation.

## Reviewer execution

Windows 10.0.26300, existing portable Python 3.14.9, fresh task D-drive TEMP/TMP.
From this repository root:

```text
python scripts/desktop-reproducible-tests.py
20 passed, 0 failures, 0 skips
python scripts/desktop-package-tests.py
12 passed, 0 failures, 0 skips
git diff --check
PASS
```

These tests verify genuine raw-byte differences (including timestamp/manifest
changes) fail comparison, complete equality passes, member ordering/metadata
participates, malformed PE/ZIP and path/dependency/worker preconditions reject,
and internal flag/Windows environment handling is correct. The tests use
synthetic files and mocked build admission; they are not two new full builds.
Logs: local `app-repro-artifacts/root-{checker,package}-tests.log`.

Reviewer inspected retained actual comparison JSON from clean01 and clean02:
both have successful normal build/package verification and matching frontend,
source and dependency inventories, but different PE/ZIP bytes. Exact hashes,
source/checker revisions and the small model-free crate-identity diagnostics
remain in the author evidence. Those executions are attributed to the author;
the reviewer did not repeat either expensive clean-build cohort here.

Limits: normal application reproducibility, license audit, offline installation/
runtime, final integrated package and release readiness are not established.
The moderate dependency advisory is not dismissed. Existing approved worker is
only a staged byte input; no model file was read. No desktop control/capture,
device/protected-resource operation, global tool change or setting change occurred.
Next: independently review the separate workspace/lock integration, then freeze
one final source and rerun the unchanged two-path raw application/package gate.

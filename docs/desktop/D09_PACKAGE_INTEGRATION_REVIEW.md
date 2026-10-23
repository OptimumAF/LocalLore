# Developer packaging integration review

Refs #31, partial. Coordinator review of independent author handoff `9d24769`,
integrated as `97d73e9` on accepted main `32173cb`. This is a source review and
locally executed synthetic package-policy check, not installer or release approval.

Reviewed the complete workflow, packager, synthetic tests and three author reports.
The workflow grants read-only repository access, pins actions/tools, disables
checkout credentials/cache use and npm lifecycle scripts, and interpolates no
untrusted event data in shell scripts. It builds the standalone protocol fixture
before runtime all-target tests, keeps strict native/runtime checks and builds a
normal executable without development features. It has no model or app launch,
secret use, artifact upload, deployment or repository-settings operation.

The packager uses argument vectors rather than a shell and validates the exact
worker artifact before building or creating output. It inventories clean committed
source inputs, checks again after the build, builds normal frontend/native code
and collects selected-target notices. Package members, byte/count limits, paths,
compression, duplicate names and worker bytes are checked. Archive verification
does not extract files. Explicit destinations must be outside the checkout and
new; publication uses nonoverwrite creation rather than recursive cleanup.

The generated manifest identifies unsigned developer output, no model weights,
development hooks disabled, installer unqualified and license audit incomplete.
Checksums identify bytes and are not publisher authentication. The packager is
trusted developer tooling, not a sandbox for malicious toolchains or hostile
same-user filesystem mutation. Runtime worker hashing remains provenance; only
the package-construction script compares the fixed reviewed artifact allowlist.

No concrete source blocker was found for this bounded development-tool slice.
The hardcoded worker hash remains unchanged. The observed final-link `/Brepro`
repeatability is limited to the same path, cached inputs and toolchain. Neither
that comparison nor these policy checks establish clean independent worker or
cross-path reproducibility, complete native license obligations, network-denied
play, DLL search safety, installer prerequisites, clean-profile launch, updates,
removal or private-data retention. The original dated author results remain pinned
to their stated source commits, rather than relabeled as current-main execution.

Actually executed by coordinator on the integration branch, using existing Python
and bundled Node24.19.0 with the locked YAML parser:

```powershell
python scripts/desktop-package-tests.py
node scripts/desktop-package-workflow-check.mjs
git diff --check
```

**12 synthetic package tests passed**, parsed workflow policy check passed, diff
check passed. Logs are local/gitignored `target/package-tests.log`. The tests use
synthetic MZ-prefixed bytes and never execute an app/worker. No hosted Actions run
was performed or claimed. Repository settings, signing, public release, model
downloads, protected work and desktop control remain untouched.

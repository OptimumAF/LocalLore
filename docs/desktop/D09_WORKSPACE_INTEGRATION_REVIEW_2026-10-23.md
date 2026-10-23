# D09 workspace integration review, 2026-10-23

Refs #31 D09.03/.05/.07 partial prerequisite and #7 M03.01/.05 compatibility.
Coordinator-delegated reviewer `/root/app_storage_review`; claims
[#31 6371170345](https://github.com/OptimumAF/LocalLore/issues/31#issuecomment-6371170345)
and [#7 6371170836](https://github.com/OptimumAF/LocalLore/issues/7#issuecomment-6371170836).
Frozen integration `3a849345da5a40f4c02ed15c3089d895d35fc6da`, separate own
`source-workspace-review` / `review/d09-workspace-integration`.

No concrete blocker was demonstrated within this review. The exact lock union,
portable selections and retained clean03 byte comparison agree with the stated
scope. This is not acceptance of full D09, licensing, offline installation,
release readiness or any unrun native/platform journey.

## Independence and changed boundary

Only this NEW report is edited. The coordinator owns manifests, locks, runner,
harness changes, package/cohort execution and publication. Reviewer previously
authored early D09 build/security/developer-package preparation; this review is
independent of the new workspace-alignment/union implementation and coordinator
integration, not a fresh independent audit of every unchanged old packager line.
No implementation copies or test-only shadow pipeline are committed.

The net21-file diff from accepted `3485aa4` joins desktop to the root workspace,
sets four portable defaults, explicitly excludes the two standalone roots,
removes the desktop-local workspace/unused lock, adds the reviewed lock union,
changes only two host-runner commands plus focused tests, nine harness lock
inventory literals, and documentation. Production Core/Host/Store/JNI/UI/runtime,
worker/profile, packager and comparison implementation are unchanged by this
integration. In particular no compiler metadata override, byte patch, output
normalizer, new dependency version/source or source alias was introduced.
The pre-existing packager source remap and final `/Brepro` link option remain;
this is not a claim that the build has zero compiler flags.

## Lock and selection evidence actually checked

Independent Python3.14.9 standard-library audit reads original tracked Git blobs
at3485, not the precomputed lock report. Keys are `(name, version, source)`;
checksum disagreements reject. The old root67, desktop413, runtime41 and eval43
package locks union to exactly414 identities /407 registry entries. No identity,
version, source or checksum was added/removed/changed. New root lock SHA256:
`d6a0fb958805ae4e4271f456ff3bbcbd683e993d25ac9ef35a1122229bcd8950`.
These results agree with the coordinator's bounded `root-lock-review.json`.
Standalone runtime/eval lock and manifest bytes remain unchanged; the old
unused desktop lock is absent. An entry retained in the union is not a promise
that every entry is selected by a particular command.

Actual pinned `cargo +1.93.1 metadata --locked --offline --no-deps
--format-version 1` on each of the four manifest entrypoints confirms:

- Root has five members and exactly the four original portable defaults.
- Direct desktop manifest uses the root workspace/lock and defaults only to
  `locallore-desktop-spike`.
- Runtime and eval each retain their own one-member workspace root.
- Explicit own D `CARGO_TARGET_DIR` is honored by all four entrypoints.

Full Windows-filtered locked/offline metadata also succeeds (257 packages in
that whole-root resolved graph, distinct from the selected package notices).
Actual depth-zero trees show default and `--workspace --exclude
locallore-desktop-spike` both select exactly four portable members, while the
desktop manifest selects desktop alone. Linux portable normal/build graph has41
unique package/version entries; Android ARM64 selected normal/build graph has58.
Neither includes desktop/Tauri/GTK/WebKit/GLib. These are graph checks, not a
Linux or Android native build. All three remaining lock files are byte-unchanged
after every metadata/tree command.

`--workspace` ignores default-members, so the explicit exclusion in both portable
host test/Clippy commands is necessary and present. It excludes no portable
member. Formatting still covers all members. Nine changed harness lines bind
`../../Cargo.lock` relative to the desktop root, replacing only the retired
lock literal; each already supplies its actual target explicitly. No harness
was launched here.

## Retained clean03 artifacts independently read and hashed

The coordinator's actual two-clean-path application build is retained separately;
reviewer did not execute it. Comparison SHA256:
`c1bb07423640b4ecb7194213e999f30e05f6a619d5cf2e79e0540a7bf5979056`.
Both application and checker revisions equal the frozen3a849345 source. Both
normal packager invocations exit0. Build code creates independent new source,
empty target and private TEMP directories, copies only provisioned npm dependency
sources, and never copies compiled targets/object/archive caches. Source paths
have different ASCII/space lengths. No app/model launch is recorded.

Reviewer independently rehashed the actual two package PEs/whole ZIPs, verified
all446 ordered ZIP entries' payload hashes and ZipInfo fields against the report,
and compared each extracted folder member to its ZIP bytes. Every packaged
member, including manifest/notices/worker, participates. Rechecked every842
tracked source files in each retained source against its captured inventory;
both captured before/after inventories match. No full arrays or environment are
published here.

| Actual equal artifact | Bytes | SHA256 |
| --- | ---: | --- |
| normal executable | 24,332,288 | `dcbaa7d480955cf5b70504f30fe52389896e8f5bb0b07bea418a3323a3939b03` |
| whole ZIP,446 members | 10,868,414 | `8e02e138ae18dfa45a88de35aacd530d2e8ecd8db369697fad1e19a8aa5758ac` |

The report's raw PE metadata/sections, folder inventory, ordered member metadata,
whole ZIP and normal frontend4-file inventories are equal. Changed-member and
changed-payload arrays are empty. Supplied npm inventory SHA is the same for both:
`57cad8333de434d9d9c1398ed5041737746a25284b303d511eb36aad6eb03703`.
The checker verifies those copied bytes before/after; hashes bind the supplied
tree, not registry authenticity. Recorded tools are stable before/after,
including nine selected compiler binaries; zero Cargo config files were found.
Known external compiler override variables are rejected by the unchanged checker.
This is bounded same-installed-tools evidence, not a hermetic audit of all
headers/libraries/cache contents or a different-machine/toolchain guarantee.

Each selected Windows notice inventory has256 entries and no selected GLib.
`license_audit_complete` remains **false** in both actual packages. Graph
inapplicability does not dismiss the existing advisory. Separate ongoing license
work must not be represented as complete by this review. Historical clean01/02
failed-byte cohorts and their diagnoses remain unchanged in accepted #99's dated
report; a clean03 pass does not rewrite them.

## Reviewer commands and limits

Windows10.0.26300, actual task-local Python3.14.9; pinned Rust/Cargo1.93.1.
All reviewer outputs/TEMP/metadata target use new own D directories. No build,
package, app/worker/model, device/ADB/CUA, unrelated process control, protected
resource, dependency download, system setting, merge or release action occurred.

```text
python -B -m unittest discover -s scripts/tests -p test_check.py -v
17 PASS (includes actual offline metadata, mocked orchestration otherwise)
python -B scripts/desktop-reproducible-tests.py
20 PASS, synthetic byte/metadata/refusal cases
python -B scripts/desktop-package-tests.py
12 PASS, synthetic package policy
cargo +1.93.1 metadata --manifest-path <root/desktop/runtime/eval> \
  --no-deps --format-version 1 --locked --offline
all four PASS
cargo +1.93.1 metadata --format-version 1 --filter-platform x86_64-pc-windows-msvc \
  --locked --offline
PASS
cargo +1.93.1 tree --depth 0 --locked --offline
cargo +1.93.1 tree --workspace --exclude locallore-desktop-spike --depth 0 --locked --offline
cargo +1.93.1 tree --manifest-path apps/desktop/src-tauri/Cargo.toml --depth 0 --locked --offline
all PASS, selections described above
cargo +1.93.1 tree --workspace --exclude locallore-desktop-spike --locked --offline \
  --target x86_64-unknown-linux-gnu -e normal,build --prefix none --format {p}
cargo +1.93.1 tree -p locallore-android --locked --offline \
  --target aarch64-linux-android -e normal,build --prefix none --format {p}
both PASS, graph only
git diff --check
PASS
```

Own bounded artifact/lock audit PASS; its source SHA256
`544c29df0798945c0939fd26c569f01132dca1bc8c88c9842e07313694837ae3`
and result SHA256
`7f6ec0872f43c3a3f47739809754d96fdefc06dfb533593f3f618241916b95e2`.
Metadata audit result SHA256
`07a07573022a86886e32974623808adeb15ab02cef8d7d61f28b50dbac48f1bf`.
Private reviewer logs: check17 `9d19c879bf0a5b5f9eb06804a8937c48a50b0082a86cce8cd3e43740c175e4cc`,
repro20 `8b48db4e8495afa5fd52b9c4a62d402ec53aa9c4e8291192d951ab3c1769b32e`,
package12 `f1823c5bf727fe473c9db2c0bebd9c5f57a1a68ab403fc7eb549ffc968be2bb8`.

Full Rust/native/frontend/Android compatibility results remain attributed to
coordinator/author runs, not re-executed here. Clean03 establishes only the exact
same-tools ASCII/space-source-path normal developer package comparison. Unicode
build/native output handling, offline traffic/installation, actual GUI/device
journeys, license closure, update/uninstall, physical phone and distribution
qualification remain separate. The coordinator retains final integration and
owner acceptance; no milestone checkbox or favorable-review score follows.

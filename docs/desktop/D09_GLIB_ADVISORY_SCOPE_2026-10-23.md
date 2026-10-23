# D09 GLib advisory target-scope review, 2026-10-23

Refs #31 (D09.01/.03/.05/.07 partial). Reviewer
`/root/desktop_runtime_profile`, `review/d09-glib-advisory` in isolated
`source-glib-advisory`, accepted source
`f5187b9784cc901870a05a052213777d25d212f7`.
Claim [6372726471](https://github.com/OptimumAF/LocalLore/issues/31#issuecomment-6372726471).
Only this report is changed. No advisory dismissal, dependency update,
configuration/release change or blanket vulnerability-clearance claim is made.

The affected Rust crate is present in the root lock, but is absent from the exact
normal Windows desktop dependency closure and its reviewed material catalog.
The Linux/BSD GTK path still resolves the affected version in the lock. This is
target qualification evidence, not a fix for that path or closure of alert 2.

## Advisory and current alert

Fresh read-only GitHub API inspection reports repository alert **2 OPEN**, medium,
`Cargo.lock`, Rust `glib = 0.18.5`,
`GHSA-wrw7-89jp-8q8g`, first patched `0.20.0`.
The GitHub advisory identifies affected versions `>=0.15.0, <0.20.0`.
[GitHub advisory](https://github.com/advisories/GHSA-wrw7-89jp-8q8g).

RustSec identifies `VariantStrIter` iterator methods `next`, `nth`, `last`,
`next_back` and `nth_back`. Their shared helper passes an immutable reference as a
mutable C out-argument; this can produce undefined behavior and null-pointer
crashes. The report is not merely a dependency-version hygiene warning.
[RustSec RUSTSEC-2024-0429](https://rustsec.org/advisories/RUSTSEC-2024-0429.html).

Read the actual upstream tagged sources: `0.18.5`'s `impl_get` declares an
immutable pointer and passes `&p`; `0.20.0` declares it mutable and passes
`&mut p`. The upstream change is merged PR 1343, not an application-level
filtering fix. No affected iterator was executed here, and lack of an optimized
crash test does not establish that the old code is safe.
[affected source](https://raw.githubusercontent.com/gtk-rs/gtk-rs-core/0.18.5/glib/src/variant_iter.rs),
[patched source](https://raw.githubusercontent.com/gtk-rs/gtk-rs-core/0.20.0/glib/src/variant_iter.rs),
[upstream fix](https://github.com/gtk-rs/gtk-rs-core/pull/1343).

The locked affected registry identity is:

```text
glib 0.18.5
registry+https://github.com/rust-lang/crates.io-index
233daaf6e83ae6a12a52055f568f9d7cf4671dabb78ff9560ab6da230ce00ee5
```

## Exact Windows selection and catalog comparison

On Windows x64, Rust/Cargo 1.93.1, this read-only command succeeded with no
downloads or compilation:

```powershell
cargo metadata --locked --offline --manifest-path apps/desktop/src-tauri/Cargo.toml --no-default-features --format-version 1 --filter-platform x86_64-pc-windows-msvc
cargo tree --locked --offline --manifest-path apps/desktop/src-tauri/Cargo.toml --no-default-features --target x86_64-pc-windows-msvc -i glib
```

The metadata contains 257 packages/nodes across its workspace resolution. Walking
only from `resolve.root` through selected node dependencies yields **256**:
**250 registry + six first-party**. Do not substitute the metadata-wide package
list or entire lock for the package root's closure. The inverse-tree command
exits 0 with Cargo's `nothing to print` warning.

Compared every selected `(name, version, source, checksum, license expression)`
against `licenses/desktop/catalog-v1.json` at source-packaging
`8e3651525f39aeb7ba2d35b64761ec17a2e6a0d9`: exact equality, no additions/removals.
This uses the packager's actual normal target/options and root-lock ownership,
not a custom selection intended to hide the affected dependency. Neither the
selected closure nor catalog includes `glib`, `glib-sys`, `glib-macros`, `gtk`,
`gio`, `webkit2gtk`, `gdk` or `atk`.

| Selected framework component | Version |
| --- | --- |
| tauri | 2.12.5 |
| tauri-runtime | 2.12.2 |
| tauri-runtime-wry | 2.12.3 |
| tao | 0.37.1 |
| wry | 0.57.0 |
| muda | 0.20.0 |
| webview2-com / webview2-com-sys | 0.39.1 / 0.39.1 |

The accepted source also enables the curated evaluator's `local-model` feature;
the older packaging source does not. Its root lock therefore differs by the
existing eval-to-local-runtime edge. This was inspected, not assumed identical:
it changes neither these selected package identities nor the absence of GLib.
The earlier catalog's package-set equality does not authenticate its historical
application binary as a build of current source, nor prove all current legal or
security gates complete. Catalog review/distribution flags remain unchanged.

Conclusion limited to this evidence: the normal Windows Cargo target does not
select the vulnerable Rust implementation. No Windows GLib upgrade is required
solely to remove this unselected code from that package. A future target, feature,
dependency or packaging change must recompute the selected graph. This does not
claim that Windows, WebView2, native prerequisites, the worker or the application
has no other vulnerability, or that an arbitrary existing executable matches it.

## Where the affected version belongs

Read the exact installed cached manifests for the selected Tauri framework
versions. Their GTK/WebKit dependencies are gated to Linux, DragonFly, FreeBSD,
OpenBSD and NetBSD; Windows uses the selected WebView2 bindings. Static locked
paths include:

```text
locallore-desktop-spike -> tauri 2.12.5 -> gtk 0.18.2 -> glib 0.18.5
                       -> tauri-runtime 2.12.2 -> gtk / webkit2gtk 2.0.2 -> glib
                       -> tauri-runtime-wry 2.12.3 -> tao 0.37.1 -> gtk -> glib
                                                -> wry 0.57.0 -> gtk / webkit2gtk
                       -> muda 0.20.0 [gtk3] -> gtk -> glib
```

These are inspected target-gated manifest/lock edges, not a completed Linux
build or complete Linux feature/call-graph proof. The actual Linux inverse-tree
query failed exit **101**, because `atk 0.18.2` is not cached and offline mode
refused fetching it. No network retry, provisioning, cross compile or Linux
native test followed:

```powershell
cargo tree --locked --offline --manifest-path apps/desktop/src-tauri/Cargo.toml --no-default-features --target x86_64-unknown-linux-gnu -i glib
```

The cached exact registry entries corroborate the compatibility boundary:

| Parent | Required GLib | Parent checksum |
| --- | --- | --- |
| gtk 0.18.2 | `^0.18` | `fd56fb197bfc42bd5d2751f4f017d44ff59fbb58140c6b49f9b3b2bdab08506a` |
| webkit2gtk 2.0.2 | `^0.18.0` | `a1027150013530fb2eaf806408df88461ae4815a45c541c8975e61d6f2fc4793` |

Both checksums match the root lock. Semver `0.20.0` is outside those ranges:
changing only the GLib lock version cannot satisfy them. Adding a separate direct
GLib 0.20 dependency would permit the old 0.18 dependency to remain and would not
repair it. GTK's own upstream 0.18 branch also shows its coupled 0.18 binding
family; that branch currently declares GTK 0.18.1, so it is corroboration rather
than a claim to be the exact 0.18.2 registry manifest.
[upstream GTK 0.18 manifest](https://raw.githubusercontent.com/gtk-rs/gtk3-rs/0.18/gtk/Cargo.toml).

No first-party Rust use of `glib`, `gtk::`, `VariantStrIter` or `str_iter(` was
found in the desktop native source, crates or native directory. This is a
bounded textual search, not proof transitive framework code never calls the
iterator or that Linux input cannot reach it. Linux native support remains
unqualified; do not mark the affected dependency safe through that search.
Portable shared checks explicitly exclude `locallore-desktop-spike` from
workspace Clippy/tests; their success is not GTK desktop qualification.

## Smallest next step and remediation boundary

For the current Windows-only developer qualification, retain this exact advisory
scope/known-risk record and leave the repository alert open. Recompute the normal
selected graph with each frozen final package; qualify the actual source/binary
and existing other gates separately. No dependency, capability, scanner-ignore
or repository-setting change is necessary to substantiate the narrowly measured
Windows exclusion. A global dependency-clean gate must still report this alert.

To remove the affected dependency from the repository's GTK path, a separately
claimed dependency-owner task is required. First establish an upstream-compatible
GTK/WebKit/Tauri binding combination that selects a patched GLib and review its
actual API/system-library/toolchain/license changes. No such compatible upgrade
was resolved or qualified in this investigation; no speculative version is
prescribed. If that is unavailable, a reviewed, provenance-pinned minimal
backport preserving the 0.18 API could be evaluated as an explicit patch/vendor
decision, with its own source/license/unsafe-code review and tests. It is not an
already-approved fix, and version-based scanners may still report 0.18.5.
Do not spoof its version, delete lock entries, disable detection or dismiss the
alert to substitute for remediation. Either route requires Linux native/iterator
regression checks and Windows/portable compatibility checks before adoption.

## Evidence and limits

Task-local `glib-advisory-artifacts` retains raw metadata (with private cache paths,
not committed), API response, successful/failed tree logs and sanitized selection
summary. Public hashes bind the actual reads:

| Evidence | SHA256 |
| --- | --- |
| accepted root Cargo.lock | `2d2c63f731134bdb76c3aa270afed9101fdba061b8b9a9658d679b50aa453317` |
| packaging catalog, exact Git bytes | `07c8f47f8062e8bed24857e103be9f97bf8b2d2292ed0b17d0a90fe597986bf8` |
| windows-metadata.json | `6ecfa3da889ccaa89b14ccf4198ece3df8c0a90c0886346612c0069d7769b22f` |
| windows-inverse-glib.log | `60ad936841c72d4121e5319c39deaf30c9d46055ef7614fb55225fe80a2e29ca` |
| linux-inverse-glib.log, offline failure | `78801cd1ae4f25dc5a37b5124766cc5a15bdd62c48f84ba5dee21708a98161cf` |
| scope-summary.json | `b51a28f701ae230f608979e79b5241b3f6c2659a2be10b1adf15742ff7398035` |
| alert2.json | `902230b49f15093905c2a9e05a082de34b7ba95e5c70375b8b0f790fbca824de` |

Metadata and comparisons ran using installed Python 3.14.9 and Rust/Cargo 1.93.1
on Windows x64; no build jobs were started. No dependencies/tools/weights were
downloaded or modified, and no package build, application/worker/model, device,
ADB, desktop control, OS setting, security-alert change or protected-resource
operation occurred. Initial guessed upstream URLs returned 404 and an initial
read named an absent old Wry cache version; neither counts as source evidence.
Correct exact cached Wry 0.57.0 and upstream URLs above were then inspected.
All lock/manifests remain unchanged. D09's offline, package, legal, native matrix
and release gates are not completed by this advisory investigation.

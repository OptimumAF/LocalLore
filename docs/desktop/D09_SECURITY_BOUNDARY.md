# D09 current desktop security review and pending qualification

Refs #31 D09.01/.02/.05; source `18c5c2f7050001f8b23fe2ca74d188ba1c637228`.
This packet updates the historical D09 preparation to accepted D04/D05 code. It
combines a bounded source reread with synthetic native/runtime and build/package
checks; it is not an independently executed offline/native acceptance matrix. The
reviewer authored earlier guard/query/preparation code and does not present this
self-handoff as independent approval of that work. Earlier independent root/app
integration findings and corrections remain in D03/D04/D05 review documents.

## Assets and trust boundaries

Private assets include drafts (including rejected requests), accepted prose,
hidden canon, character knowledge, prompts, paths, model metadata, clipboard,
SQLite saves, inspection previews and selected exports. Player/generated/imported
text and model files are untrusted data. Trusted code includes the embedded
renderer, native broker/Host/Engine, WebView2, native libraries, the packaged worker
and OS. Same-user filesystem compromise, OS backups/keyboards/clipboard sync and
malicious OS services are outside app isolation. Hashes identify input bytes;
they are neither parser safety nor publisher identity nor a device sandbox.

The app opens a Host with trusted Story Lab permission. The Play/Player lens is
an intended-use UI/query restriction, **not a security boundary against a hostile
renderer that already has this application's native privileges**. Native queries
still validate session/scope/head/observer/cursor, and the shared query module
filters eligible values before search/count/pagination. Lab access does not
change an NPC's generation context. It intentionally permits private reads from
the trusted app; do not claim every Lab read requires separate OS user consent.

| Boundary and threat | Observed source controls | Limits / next qualification |
|---|---|---|
| Story/model text becomes script, remote image or link | React text/preformatted JSON; no `dangerouslySetInnerHTML`, Markdown execution or generic URL opener found in the UI reread. CSP permits embedded origins/IPC only. Main window navigation accepts the two app origins; new windows are denied. | Run malicious remote-image/link text under renderer/worker network observation in the final package. Source absence is not zero-traffic measurement. |
| Renderer gets general file/SQL/process/network authority | Normal handler list is explicit: bounded `host_call`; five model commands; seven inspection commands. No generic shell, SQL, filesystem, HTTP, opener or updater plugin is in the native manifest. Native dialogs choose imports/export destinations; renderer paths/bundles do not replace native authority. | Tauri capabilities constrain IPC routing, not arbitrary Rust internals. Audit new custom commands rather than assuming the framework makes them safe. |
| Development harness reaches a normal package | Rust handler lists/modules are `dev-harness` gated; normal frontend is compiled with `__DEV_HARNESS__=false`, and checks scan journey/control markers. Packager builds `--no-default-features` and copies only that executable. | Harness permission names are still declared in the shared capability JSON, but no corresponding normal handler is registered. Removing unused declarations is a clarity/least-privilege follow-up, not a demonstrated reachable hook. |
| Closed window / stale result crosses story/lens/head | WindowLease epochs fence native admission and close; Host validates scope/head; model cancellation uses exact operation identity. Controller query epochs/context keys fence page/source replies and post-await selection, and Play clears Lab/search/revision/trace state. | Existing controlled regressions run in the frontend check; this packet did not rerun UI/native interactions. A hostile renderer remains an app principal with Lab access. |
| Imported snapshot becomes canon or generation context | Read-only structural checks, byte/file limits, exact inventory, hashes, untrusted labels and inert display. No restore/commit/generation path for inspection files. Query navigation only uses approved typed source identities. | Relabelled snapshots and recomputed checksums can fool structural provenance claims; the broker preserves captured exact bytes/tokens but cannot authenticate external authorship or observer eligibility. |
| Export preview/save publishes changed or private bytes | Native-owned frozen bundles and window-bound tokens, TTL/admission limits; pinned Windows ancestors/staging/ordinary files; create-new/nonoverwrite handle publication; consistent bounded SQLite snapshot. | Cancellation can lose to completed atomic publication. Full/database exports are private; DB copies include every story and stored request. Power failure/AV interference and final-package destination races need measured qualification. |
| Crash leaves plaintext intermediate data | Bounded exact-namespace private-preview/import reapers; active, unrelated and reparse entries retained rather than blindly removed. | No encryption/secure-erasure guarantee. Crash remnants may survive until cleanup and successful selected exports are intentionally retained. |
| Clipboard/backups move private data | Clipboard writes are explicit user actions; no clipboard reader/plugin; app-local SQLite and native selected exports. | OS history/sync, screenshots, backups and user-selected synced folders remain external boundaries. |
| A model replaces the worker or invokes a tool | Fixed packaged worker path; retained non-reparse file/ancestor handles, one approved model size/hash/profile, no shell arguments from model text. Worker is bounded stdin/stdout IPC, no tools/server/downloads; environment overrides for upstream model backends are stripped. | The worker runs as the same user, not an OS sandbox. Runtime hashes the retained worker for provenance; **it does not compare that hash with the packager's fixed artifact allowlist**. Package construction pins the reviewed bytes. DLL search/servicing, writable install locations and native parser vulnerabilities need separate audit. |
| Hung/failed worker outlives request or shares context | Exact request/role identity, bounded frames/output/stderr/deadlines; narrator cannot start a turn; timeout/cancel retires the owner; partial pipe-thread startup failure drains exact child and joins prior threads; fresh model context per role. | Synthetic fixture tests cover these paths. Existing actual-worker/model evidence is separate; no worker/model was launched by this D09 packet. |
| Generated intent/prose becomes unauthorized state | Supported finite English action guard plus literal dialogue; Rust Engine resolves/revalidates typed effects; observer-limited context; immutable outcomes/atomic/idempotent receipts; replay uses no LLM. | Not arbitrary-language understanding or complete semantic privacy/quality. Private names/common words/prose can still require semantic review. Profile/model provenance is not authenticated authorship. |
| Logs/diagnostics silently upload private content | No collector, updater, analytics or hosted inference path was found in the reviewed app/worker configuration. The package excludes trace directories and private DBs; normal UI diagnostic ring stores bounded categories. | WebView2/OS/dependency behavior and child connections have not been observed here. Diagnostics still has structural identifiers/times; do not call every export anonymous. |

Source reread covered native main/lease/model/export boundaries and handler
registration, current controller/query UI, Cargo/features/configuration,
runtime launch/file/deadline paths, worker CMake/staging/profile, and the previous
review/fix records. The [Tauri capability reference](https://v2.tauri.app/security/capabilities/)
documents the framework boundary; the application's Rust still owns authorization.

## Concrete findings and disposition

The historical CI preparation omitted the standalone runtime entirely because it
is excluded from the root workspace. The new workflow explicitly builds the
ordinary synthetic protocol fixture, then all-target runtime tests and strict
Clippy with `development-worker,engine-adapter`. No real model or scene probe is
needed. Local execution passed 23 cases with one privileged symlink test ignored.

The initial accepted `8f3842e` native formatting check failed on the inherited
`FILE_DISPOSITION_INFO` one-line layout. The desktop owner's `7611297` correction
was already under integration; this packet made no native edit. After accepted
main `18c5c2f`, the actual strict native/runtime formatting checks pass. The workflow
keeps these gates rather than disabling them.

The package's worker requires VC++/OpenMP DLLs, and its fixed artifact hash is not
yet shown reproducible by clean builds. These are explicit D09.03/.05 gaps, not
permission to relax the pin or silently redistribute DLLs. See the
[build/package instructions](D09_BUILD_AND_PACKAGE.md) for the measured imports,
resource paths, source/build evidence and next qualification.

Read-only Dependabot lookup still reports open alert 1 for locked **glib 0.18.5**,
[GHSA-wrw7-89jp-8q8g](https://github.com/advisories/GHSA-wrw7-89jp-8q8g),
moderate VariantStrIter unsoundness affecting `>=0.15.0,<0.20.0`, patched in 0.20.0.
The current Windows x64 inverse dependency command returns no selected glib
dependency; the Windows-resolved package inventory also does not select glib.
That is target applicability evidence, **not remediation or dismissal**. The lock
retains GTK/WebKit dependencies for other targets. Linux qualification and a
coordinated upstream-compatible fix remain open; no blind second-version glib
addition, dependency lock update or alert/settings change was made here.

## Next real security/package gate

Keep D09.02/.05/.06 open. In an explicitly authorized disposable test environment,
record exact final executable/worker/WebView2 hashes and deny/observe both renderer
and child outbound traffic while running real free text, durable restart, two
stories, scoped inspector, preview/save/open, cancellation/late completion and
malicious URL/image text. Record OS services outside the observation boundary.
Independently test clean profile, absent WebView2/VC runtime, model import/load from
space/Unicode paths, missing/corrupt resources, update/removal with story retention,
package resource/DLL search paths, disk failure and diagnostics retention. Finish
the native/dependency license audit and clean worker rebuild comparison before
calling the clean-checkout developer package or installer qualified.

No firewall/global network rules, runtime/profile source, story/model/device,
desktop UI, repository settings, hosted runner, secret or release was touched by
this packet. Prepared CI has not been executed on GitHub by this reviewer.

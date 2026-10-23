# D03 native export review — 2026-10-22

This bounded independent review reads the desktop specialist's in-progress
`exports.rs`, `export_commands.rs`, native registration and controller/view code.
Those files remain specialist-owned. This reviewer writes only this report and
an ignored small controller proof; it does not run an app, browser, picker, device
or model. The source below was inspected before the specialist's final handoff;
findings require explicit disposition against its final commit.

## Findings reported to the coordinator

1. **Saved-state/native-lease lock order can deadlock.** `Preview::save_impl`
   locks `saved` before calling finalization through `WindowLease::dispatch`.
   `inspection_open` takes that lease gate before `Preview::open` locks `saved`.
   Concurrent save/open on the same token can therefore wait in opposite order.
   Frontend busy controls do not serialize native IPC callers. A bounded barrier
   test should enter finalization while an open call holds the lease gate and
   verify completion, with one consistent lock order.
2. **Staging child is not pinned.** The initial writer pins destination ancestors,
   then creates a staging directory and repeatedly resolves `staging.join(name)`.
   It does not retain ownership of that new directory through publication. A
   same-user watcher can rename/replace the child with a junction, redirecting
   writes beyond the chosen destination. Pinning its parent does not prevent
   replacement of the child. Required adversarial test: pause after staging
   creation, attempt child replacement, and ensure no redirected files are written
   or published. A Windows handle-based staging/write/rename strategy must avoid
   reopening the untrusted path at the critical boundary. This is a concrete
   source race finding; no executed filesystem exploit is claimed here.
3. **Open-existing action missing normal registration.** The initial normal
   `invoke_handler` omitted `inspection_load`, although the UI offered it and
   build/capability declarations included it. Development registration alone
   cannot establish the normal action works.
4. **Disk-full test scenario name mismatch.** The initial development case
   allowlist accepted `full`; the writer injected failure only for `disk-full`.
   An allowlisted `full` run could therefore exercise successful publication
   instead of the intended failure path.
5. **Privacy warning can change before the old preview is revoked locally.**
   `setExportMode` calls asynchronous `cancelExport` without awaiting it, then
   immediately changes the mode. While native cancellation is pending, a Full
   preview can remain visible/save-enabled under the Diagnostics warning. Clear
   local preview authority and advance its epoch synchronously, or serialize
   mode/view changes until cancellation completes. Cover returning to Play too.

## Executed controller proof

The fifth finding was reproduced using the actual controller, bundled with the
existing pinned esbuild into this review's ignored output. Its only transport
response is a deferred synthetic `inspection_cancel`; no UI is launched. Seed a
Full preview, call `setExportMode("diagnostics")`, inspect state before resolving
cancellation, then resolve it and verify the preview clears.

```powershell
node '../LocalLore-desktop-durable/apps/desktop/node_modules/esbuild/bin/esbuild' '../LocalLore-desktop-durable/apps/desktop/ui/controller.ts' --bundle --platform=node --format=esm --outfile=target/d03-review/controller-proof.mjs
node target/d03-review/privacy-race-proof.mjs
```

The reproduction returned exit 0 and observed:

```json
{"nativeCalls":1,"duringMode":"diagnostics","duringPreviewMode":"full","mismatched":true}
```

After resolving the deferred cancellation the preview was null. The proof can
be run with `--expect-fixed` after rebundling the corrected controller to require
that the inconsistent intermediate state is absent. This proof checks actual
controller behavior, not rendered pixels or native picker/IPC execution.

## Boundaries inspected

The broker privately retains captured bundles and exposes random preview tokens;
renderer save/open requests do not carry arbitrary paths, replacement files,
SQL, executable content or new observer authority. Tokens bind to native window
epochs, expire, and have bounded retained count. Save uses create-new files and
same-parent staging; ordinary folder selection is native-owned. Open compares
saved bytes with the retained capture and renders text read-only inside the app.

Externally loaded folders are explicitly untrusted inspection, even when
structurally valid. Recomputed hashes do not authenticate authorship or observer
visibility. No external snapshot is applied to canon. Fixed filenames, byte/file
budgets, reparse rejection and UTF-8/text-only presentation remain necessary for
this read-only path. The final normal/development command registrations and
expiry/cancel/mode/scope behavior must be checked on the specialist's final source.

No broad Tauri build, actual picker, native window, desktop control, input event,
unrelated process operation, ADB or model execution was performed by this review.
Protected chat/runtime resources remain outside its write scope. This draft
review does not accept the D03 native/export gate or claim any of the reported
findings has been resolved.

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
6. **Database preview initially checked its budget after copying.** A workspace
   larger than 64 MiB could write an oversized temporary private copy before
   rejection. Coordinator `e5ad25d` now pins a source read transaction, reads its
   page count/size, rejects before destination allocation and backs up that same
   snapshot. Independent source review found the coherent bound correct. Its
   tiny-limit/native copy test execution belongs to coordinator evidence.
7. **Post-publication pathname checks can misreport a successful save.** The
   initial handle-rename fix performed fallible checks on the now-free staging
   pathname after rename success. A newly created object at that old name could
   cause an error after the export had already published. The latest source
   removes those checks and uses successful handle rename as the publication
   boundary; final source identity remains to be recorded.
8. **Crash-cache retention needs an explicit bound.** Ordinary return removes the
   private database-preview cache, but abrupt process death can leave an entire
   workspace copy in `inspection-preview-cache/private-preview-GUID`. Repeated
   interruptions must not accumulate private copies indefinitely beyond token
   expiry. Cleanup must stay inside the native cache namespace and skip active
   pinned directories/other instances.
9. **Loaded manifest bytes must remain exact.** The initial loader parses the
   manifest and discards its raw encoding, then the broker regenerates pretty
   JSON when verifying an open. A compact/reordered but valid existing manifest
   loads, then spuriously fails `ChangedExport`. Preserve the actual loaded
   manifest bytes; subsequent edits must still fail comparison.
10. **A saved-result acknowledgement can cross story selection.** If cancellation
    returns `saved` while `saveExport` is busy, `cancelExport` returns without
    clearing local preview or advancing its epoch. Story invalidation then
    changes selection, and a delayed save acknowledgement publishes the old
    preview/location into the new selection. Invalidation must revoke local
    presentation even when file publication has already won.

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

The synchronous `clearExportPreview` correction was independently rebundled and
tested with `--expect-fixed`. It returned exit 0 and observed:

```json
{"nativeCalls":1,"duringMode":"diagnostics","duringPreviewMode":null,"mismatched":false}
```

A second tiny proof uses the same actual controller with two synthetic sessions,
a deferred native save acknowledgement and immediate `cancel: saved`. It starts
save in the old session, calls `switchSession` for the new one, then releases the
save acknowledgement. Initial result:

```json
{"selectedStory":"new-story","previewStory":"old-story","oldSavePublishedIntoNewSelection":true}
```

No live filesystem or backend is needed for either proof. Both scripts and their
bundle stay in ignored `target/d03-review/`; final source/test disposition must
be recorded before these initial reproductions are treated as resolved.

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
Protected chat/runtime resources remain outside its write scope.

## Final source disposition

The specialist's clean commit `571846a`, including `bb8317a` and `5f26ed5`, was
independently reread after the findings above. Coordinator `e5ad25d` supplies the
coherent pre-allocation database budget. No unresolved blocking defect was found
in this final reviewed source scope.

| Initial finding | Final implementation inspected |
|---|---|
| Lock inversion | `open_current` checks native epoch before/after read-only open without holding the lease gate while waiting for `saved`. A barrier regression covers concurrent save/open. |
| Replaceable staging directory | A non-reparse staging handle holds DELETE access without delete sharing. Files are written while that directory cannot be renamed/replaced; publication renames the owned handle itself through Windows `SetFileInformationByHandle`. A pinned-stage replacement test is present. |
| Missing normal action | `inspection_load` is registered in the normal native handler as well as the development handler. |
| Wrong injected scenario | Development allowlist and save injection both use `disk-full`. |
| Wrong privacy label during cancellation | Mode/view changes clear local preview/opened content and advance export epoch synchronously, before background native cancellation. |
| Oversized temporary database copy | Source transaction is sized before any destination allocation; its same snapshot is backed up. |
| Error after successful publication | Successful owned-handle rename is the publication boundary; fallible staging-path checks after success are removed. |
| Interrupted private cache retention | Startup cleanup inspects a bounded native cache namespace, accepts only generated GUID directories and known snapshot/sidecar names, rejects reparse/foreign entries and skips active pinned directories. Cleanup counts/limited/unavailable status are retained explicitly. It does not recursively delete arbitrary paths or user-selected saved exports. |
| Loaded-manifest formatting mismatch | The native Loaded variant retains original manifest bytes alongside parsed metadata. Open verifies those exact bytes. A compact-manifest/later-edit regression is present. |
| Old save result crossing selection | `cancelExport` clears presentation and advances export epoch before awaiting native cancellation, including an already-saved outcome. Delayed save acknowledgements cannot repopulate an invalidated selection. |

Both ignored actual-controller proofs were rebundled against `571846a` and run
with `--expect-fixed`, each returning exit 0. Mode transition observed the null
preview shown earlier; the story-switch proof now observed:

```json
{"selectedStory":"new-story","previewStory":null,"oldSavePublishedIntoNewSelection":false}
```

The specialist also added the tracked `apps/desktop/check-export-controller.mjs`
regression, covering deferred cancellation, pending Full preview and save-result
fencing. This reviewer inspected that test but did not count a new execution of
it or the native broker unit suite. Coordinator/specialist evidence must identify
their actual runs, native IPC/render checkpoints, fault cases and source hashes.

The final disposition is a source/race review with two independently executed
controller proofs, not an actual-window/picker execution, power-loss guarantee,
other-platform qualification or owner approval. External files remain untrusted
even after checksums validate; they never become canon or generation authority.

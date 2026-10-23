# Desktop app save and resume

The desktop adapter calls `locallore-workspace::open` with an app-owned
`stories-v1.sqlite` path from Tauri `app_local_data_dir`. Initialization, replay,
reads, submitted-request persistence and commit run on blocking workers. A
four-permit generation budget does not block cancel/status control calls. The
engine and SQLite owner remain the shared canonical implementation.

The frontend reads `workspace`, then resumes its first story (the shared library
sorts by stable story ID), or creates the original Lantern Quay scene when the
library is empty. The sidebar lists saved scopes and head revisions separately
from the window's open sessions. The details disclose actual save path, schema
and rules. Close removes only the live session; New and Reset retain earlier
stories. No delete, export or shell-reveal capability is added.

Each new controller uses the platform cryptographic UUID API for its turn-key
prefix. Reopened clients never restart at a global `desktop-1` key. A retry keeps
the original request/key and resolves its authoritative stored receipt; process
restart can query the same receipt without applying outcomes again. Transcript
and inspection are rebuilt from validated replay, never from cached UI text.

Unsubmitted composer text is explicitly session-local. Submitted requests are
persisted by the shared owner, with uncommitted counts shown on resume. Resuming
a story neither commits nor cancels another client's pending request. Failed
initialization/replay is visible and cannot fall back to ephemeral play.

## Reproduce without desktop control

```powershell
npm --prefix apps/desktop ci --offline --ignore-scripts --no-audit --no-fund
npm --prefix apps/desktop run check
npm --prefix apps/desktop run harness:durable
```

The compile-time dev frontend, Cargo `dev-harness` handlers and trusted launcher
are all required for the harness. The launcher supplies a fresh ignored synthetic
directory; no path is accepted from frontend IPC. The fixed script uses the real
controller and native host IPC, fixed app-owned window sizing, semantic JSON and
WebView2 CapturePreview. It never activates a window, injects input or captures
the desktop. The WebView profile is isolated under that synthetic directory.
The runner then starts a separate executable process against the same database.
No production data path is opened by the test. Normal frontend checks assert
that journey/control strings are removed, and the default native build registers
only `host_call`.

Legacy `harness:native` and `harness:headless` D02 regressions use explicitly
memory-only fixtures. Their old no-durability assertions do not describe the
production app. Native and headless captures remain separately labeled.

No new desktop dependency version is introduced; the path dependency reuses the
shared workspace's pinned SQLite owner. Real-model, installer, OS backup,
screen-reader and physical-device qualification remain separate gates.

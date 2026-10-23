# Direct-child process ownership for the Android experiment

This dependency-free POSIX C executable is development tooling, not a gameplay
service or arbitrary-program sandbox. It launches only the reviewed helper or
Rust oracle, which create threads but no child processes. Shell builtin probes
exercise failure behavior without loading a model.

The host creates a unique 32-hex directory below
`/data/local/tmp/locallore-m01/runs/`, stages a bounded regular input file and a
worker symlink, then launches the owner. An atomic PID marker and exact command
identity are checked before releasing the launch barrier. The barrier has a
15-second independent bound. Cancellation already due cannot release it.

After release, `fork`/`execv` starts one direct child with the staged input.
`waitpid(WNOHANG)` is the only reaper. Until it reaps that child, the PID cannot
be recycled; only this native parent signals it. Cancellation, HUP/TERM/INT or
the independent requested deadline sends TERM, then KILL after 500ms. Success
is recorded atomically only after reap. Wait errors/uninterruptible-task cleanup
remain `cleanup_failed`, never a successful reclamation claim. The parent never
waits on model pipes, so a blocked writer does not block its deadline loop.

The whole owner budget is 1–90 seconds, including pre-release time. In addition,
the llama helper arms an independent fixed 90-second alarm before reading input
or loading weights. These are abrupt process bounds; they do not prove native
cooperative cancellation or heap-level disposal. The SDK uses its own Java
watchdog and package-specific termination instead of this direct-child owner.

No host command signals a PID. The host verifies `done`, original-owner absence
and bounded ADB cleanup separately. It deletes only known files in that exact
UUID directory after verified process cleanup; a directory deletion error is
reported separately. It never recursively removes paths or kills by name.

Explicit offline cross-build (existing NDK29, API28; Windows/Linux recipe only):

```powershell
python benchmarks/spike/android/controller/build.py --sdk $env:ANDROID_HOME
python benchmarks/spike/android/controller/smoke.py --adb <adb> --serial <authorized-target> --owner target/android-runtime/controller/remote-owner-x86_64 --output target/android-owner-checks.json
```

Both x86_64 and ARM64 outputs are PIE/16KiB aligned and linked only to system
libraries. Only x86_64 was executed. Sixteen actual Android control checks and
all-attempt inference evidence are in
[the result artifact](../../../../docs/runtime/android/RESULTS_2026-10-22.json).

# Current Rust play experiment

This opt-in experiment connects the isolated LiteRT-LM SDK app to the current
Rust free-text pipeline. It selects no production backend and adds no inference
to Compose. Refs #5 (M01.03, bounded M01.02/M01.05), #9 (M05.05 preparation).
See [verification](PLAY_VERIFICATION_2026-10-23.md), [profile](PLAY_PROFILE_V1.json)
and [review](PLAY_REVIEW_2026-10-23.md).
The later [captured-main compatibility proof](PLAY_COMPAT_VERIFICATION_2026-10-23.md)
records a separate build and emulator cohort without rewriting the original.

The [guarded SDK bridge tests](GUARDED_SDK_BRIDGE_TESTS_2026-10-23.md) carry the
accepted prompt2.3 refinement through the same public native byte interface.
Supported action grammar binds the exact Engine-preflighted command; actual
provider bytes still undergo parsing, intent and mechanical validation. Earlier
APK/model observations retain their original source identity. The separately
[qualified prompt2.3 artifact](GUARDED_SDK_VERIFICATION_2026-10-23.md) returned a
process-crash terminal without a structured SDK result in its one actual run;
its native schema compatibility remains unqualified. The earlier `04eef96b...`
artifact and its Agency rejection are prompt2.2 evidence.

## Build and run

Use existing Windows Rust1.93.1, NDK29.0.14206865, Android SDK, cached Gradle
dependencies and Java21. Configure JAVA_HOME/ANDROID_HOME as in the SDK guide:

```powershell
python benchmarks/spike/android/litert/play_build.py --java21 <existing-java21-directory> --clean
```

This explicitly builds both Rust ABIs offline with `play-probe`, builds/tests/
audits the SDK app and preserves `target/android-play-probe/verified/app-debug.apk`.
Ordinary production/SDK builds omit this feature. Inspect authorized target and
installed identity before installing in `org.locallore.runtimebench.litert`;
never replace unknown installations or clear data.

The controller requires a preprovisioned hash-matching model in that package;
it never downloads/copies weights. Provisioning is a separate authorized action.

```powershell
python benchmarks/android_play_probe.py --adb <adb> --serial <authorized-target> --apk target/android-play-probe/verified/app-debug.apk --case gift --output target/play-gift-attempt-1.jsonl
```

Cases: gift, dialogue, unlearned, spent, cancel. Spent first commits a gift,
then tries another spend. Cancel requires actual nonempty SDK output before
requesting cancellation and fails if generation has terminated. Follow it with
a fresh gift. Outputs are create-only: preserve failures/unfinished attempts.
`--allow-missing-model-probe` explicitly tests missing-model cleanup instead of
a successful gift; it proves no generation or active SDK cancellation.

## Boundary and owners

NativePlayProbe exposes only open(path,profile), call(handle,envelope),
poll(handle), respond(handle,ticket,utf8), close(handle). Trusted code constructs
path/profile; model text cannot configure them. Rust uses existing workspace/
Host/store interfaces. Maximum four leases, one active provider per owner.

Call uses version1 Host envelopes including guarded play-v2 prepare/commit/cancel.
Poll returns a version1 reply with pending:null or a positive one-shot ticket
and the original structured request. Its seven fields: version,role,prompt,
max_tokens,context_tokens,threads,schema. Scope/turn/revision/profile/schema and
all budgets stay bound. Response consumes only its ticket. Cancel/drop/close
invalidate their own request without clearing replacement work. Native code
retains no Java callbacks/references and creates no worker threads.

Blocking Rust preparation runs on a separate Java executor from the SDK pump.
One lazily initialized Engine serves fresh Conversations within one turn:
director, at most one repair, narrator. There is no model reuse across turns.
Rust alone interprets guarded intent, validates mechanics/narration and permits
commit. Response-format enforcement gets the unchanged Rust schema; tools are off.

Terminal/drain and successful Conversation close, Engine close, native future
completion and executor termination precede commit. Uncertain cleanup requires
process termination and prohibits commit/reuse. Original request/key commit,
exact retry and strict reopen keep canonical replay independent of inference.

## Bounds and evidence

Profile:4096 context, director350/narrator220 output tokens, four CPU threads,
one repair,60-second case budget shared by both spent turns. SDK watchdog90s,
controller110s; separate model hashing180s. These are experiment bounds.
Byte caps:profile4096,Host input24576/output262144,response16384 UTF-8,
worker request32768,outer poll40000. Malformed input fails closed.
Provenance binds exact APK/manifest/model hashes. Template hash is the whole
model container containing its template, not an independently extracted template.
SDK modified-UTF-8 caveat remains; ASCII cannot qualify arbitrary Unicode prompts.

Public reports contain fixed categories,numeric/bool metrics,hashes. Role rows
are admissions, not necessarily opened Conversations. Parser rejects contradictory
turn/aggregate data, owner counts, unknown fields, duplicate terminals and wrong
named errors. Safe model rejection is still a failed playable case.
The SDK's `workspace_retained=true` describes its handoff before controller
cleanup; the controller's later `workspace_removed=true` describes verified
removal after process/owner drain. They refer to different lifecycle stages.
Bounded raw instrumentation is retained privately under ignored
target/android-play-probe/raw, exposing only a Boolean publicly. Keep raw text
and weights out of Git. Confirmed package/process/client absence precedes removal
of only the marked workspace/known sidecars. Unknown files/uncertain ownership
fail cleanup and retain it. No model cache/default save/unrelated data deletion.

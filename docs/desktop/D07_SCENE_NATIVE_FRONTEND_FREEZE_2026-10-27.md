# D07 native scene frontend: independent regression freeze

Refs #29 D07.03/.05/.06. Frozen from `5d966ab1`, before the frontend production
allocation. The new checker is source-only and **UNRUN**. Existing decoder,
controller and View APIs already exist; the coordinator can measure their actual
baseline before implementation. A build/setup failure is distinct from a
behavioral failure. No source test or headless view proves native execution.

## Transport and lifecycle contract

The native decoder admits exactly `(version2, protocol3, approved_native)` and
`(version3, protocol4, approved_native)` with the same existing native status and
catalog keys, including nullable error/source/cause and independent cleanup
fields. Native catalog row protocols match their outer protocol. The scripted
decoder remains exactly `(version1, protocol3, scripted_baseline)`. Unknown or
mixed tuples and unknown/missing keys refuse as `ComparisonRunWire`.

`createNativeComparisonRunController(invoke, onError?)` and
`evaluation_comparison_native` keep their existing signatures. Each action sends
its existing exact object-query keys. No request selects a protocol, policy,
provider, path, asset or model. The server's trusted development configuration
selects the scene construction; the renderer reports returned metadata only.

An acknowledged owner retains its source protocol alongside client/run/token,
kind and operation identity. A later status, lookup, retry, resume, cancel,
close or matching catalog row must not change that protocol. Matching catalog
metadata also constrains a cold open. Unknown acknowledgements and retired
owners keep the existing admission/cleanup barriers. A wrong-protocol close
cannot clear a retired barrier or count as cleanup acknowledgement.

Cleanup required/running/cause remain independent from presentation closure and
completion. A current Protocol4 completed report may keep its last verified
counts while a newer cleanup latch blocks generation and inspection. Context
changes and late completions cannot republish the old private run or trigger a
replacement start/resume.

When actual Protocol4 metadata is available, the real View identifies Protocol4
and scene construction, preserves honest model/quality/cleanup labels, and does
not instruct the user to configure the development-only reused asset root in
the renderer. An absent status/catalog is not evidence of either native
protocol or installed assets.

## Frozen checker scope

`apps/desktop/check-scene-native-transport-review.mjs` builds the actual existing
model/controller/View modules into a local Node bundle. It uses closed synthetic
DTOs and a bounded action transport, then renders actual React static HTML.
It does not replace controller state or call private methods. Native command
requests are checked for exact fields, including their absence of a protocol
selector. Every controller fixture is disposed; synthetic held replies are
released in `finally` paths. No production hook, test injection API or general
execution server is introduced.

The checker covers old native/scripted calibration; Protocol4 independent
status fields and catalog detachment; malformed tuples/keys/bounds and throwing
getters; actual start/open/status/lookup/resume/cancel/close/cleanup paths;
owner and matching-catalog protocol fences; completed cleanup retention;
retired close uncertainty; context-late publication suppression; and honest
Protocol4 static View labels/control states. It records each case separately,
source hashes before/after, synthetic transport summaries and headless HTML in
the existing local gitignored checks directory. Failures remain failures.

The throwing-getter negative checks bounded wire categorization; it does not
claim descriptor-level getter rejection or arbitrary getter nonexecution.
Oversize malformed DTOs do not independently establish byte caps for an
otherwise-valid closed DTO. Static HTML verifies labels/disabled controls, not
layout, mounted callbacks, keyboard access or actual native rendering.

## Coordinator execution and remaining gates

From `apps/desktop`, after source review:

```powershell
node check-scene-native-transport-review.mjs
```

This command is **UNRUN** by the source author. The checker is not added to the
verification list in this allocation. The coordinator retains baseline failures,
then reruns the unchanged checker after production and the existing native3 and
scripted consumer suites. Source before/after hashes must agree for a valid run.

Actual native service/Rust, confirmation dialogs, loaded model availability,
no-copy asset reuse, runtime owner/drain, IPC/WebView, render images, Android,
completed native4 no-load resume and human quality remain separate gates. The
original human assessment remains “needs improvement.” No release or task
completion is established by this freeze.

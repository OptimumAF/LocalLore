# ADR-0006 — Tauri desktop shell over the shared Rust engine

Status: proposed for owner review; implemented D01 spike, not release approval.
Date: 2026-10-22. Decision authority: @OptimumAF. Tasks: D01.01–D01.05,
[#22](https://github.com/OptimumAF/LocalLore/issues/22), parent
[#21](https://github.com/OptimumAF/LocalLore/issues/21).

## Context and observed evidence

Accepted main `3a7cb82` includes #18/#19/#20/#27. Earlier ticket descriptions
of unmerged dependencies are historical. The existing `locallore` crate owns
typed intent, validation, accepted receipts, replay and filtered contexts.
`inference::execute` commits its supplied engine; host preparation must therefore
use a clone, then revalidate on the canonical engine. The provider is fake and
the state is in memory. The Android registry owns JNI/thread-affinity handles;
it is an adapter, not a host-neutral session service.

The available machine is Windows 11 Pro x64, build 26300, Intel i7-12700K,
64 GiB RAM, RTX 3080 and Intel UHD 770. No GPU inference was exercised. This
decision qualifies only the tested Windows developer spike.

## Options and decision

| Concern | Tauri 2 + future TypeScript/React | Compose Multiplatform Desktop |
|---|---|---|
| Engine call | Direct Rust dependency and narrow IPC command | JVM needs a desktop JNI/JNA adapter and packaging per architecture |
| Existing UI reuse | New desktop view; engine remains shared | Some Compose concepts/widgets reusable, but current Activity/lifecycle/Android adapter code is platform-specific |
| Story Lab | Web tables, search and later graphs fit one renderer | Possible in Compose; graph/table/accessibility integration still needs evaluation |
| Accessibility | Semantic HTML and WebView accessibility require actual assistive-tool qualification | Compose Desktop accessibility also requires qualification; Android tests do not establish desktop support |
| Runtime/package | Windows WebView2 + MSVC build tools; offline installer/runtime policy required before packaging | JVM/Skiko/native Rust libraries; JDK 17+ packaging; package runtime deliberately |
| Local security | Explicit app-command ACL, CSP, local navigation, no broad plugins | Explicit JVM/native capabilities and no network libraries/server required |
| Cost/rollback | New frontend, platform WebView dependency | Potential UI reuse, additional maintained desktop FFI |

Select **Tauri 2** for the desktop boundary. Keep Android Kotlin/Compose/JNI.
Direct Rust reuse avoids making a second JNI adapter a desktop prerequisite.
The equivalent spike is deliberately one native engine call path: the Tauri
WebView invokes the same host service used headlessly. Compose was inspected
against the same contract, not implemented as a competing application. No
comparative latency, RAM or accessibility score is claimed.

D01 uses bundled HTML/ES modules to isolate the boundary; it does not introduce
React/Vite/TypeScript until D02 needs them. This chooses one production direction,
not a second production UI stack. Use the Rust-generated host schema when D02
adds generated/schema-validated TypeScript types. Full Play/Story Lab, durable
workspaces, real models and advanced memory remain their owning child tickets.

## Consequences and capability rules

`locallore::host` is an opt-in feature in the existing portable crate. Only
schema derives are added to existing request types; domain rules, inference,
Android adapter and fixtures are reused unchanged. Desktop dependencies have a
separate Cargo workspace/lockfile so Tauri is not an Android/host-CI requirement.
Android does not enable the host/schema feature.

One host mutex serializes canonical mutation. A bounded worker prepares on an
immutable engine clone outside that mutex; commit checks cancellation and the
original revision again. Control commands bypass the native preparation
semaphore. Closing or switching sessions cancels captured work; fresh session
IDs never recycle. A lost commit response is recovered via the original turn
lookup and exact typed-request comparison. It never implies rollback.

Only the trusted native `main` window is granted app-command permission and
Story Lab inspection. A wire observer selects a lens within that grant; it
cannot grant author/debug capability or alter generation permissions. Default
host construction grants player-only inspection. No SQL/filesystem/shell or
network plugin is registered. Assets are embedded; CSP restricts network
destinations, navigation stays on the local app origin and new windows are
denied. These are application boundaries, not an OS network sandbox or traffic
audit. WebView/browser profiles, OS backup and compromised OS remain separate.

The D01 app is intentionally spoiler-bearing and accepts only the original
synthetic seed. Do not add private stories to this developer harness. Packaging,
runtime patch policy, screen reader tests, outbound-traffic observation and
offline installation remain D09 work. WebView2's default downloadable bootstrapper
must not become an implicit offline-play requirement.

Rollback removes `apps/desktop` and the optional host feature. It changes no
Android save schema or domain semantics. Migrating the desktop renderer would
reuse the host contract and require a new measured ADR; do not maintain two shells.

## Verification and sources

See [host-v1](../desktop/HOST_V1.md), [dated checks](../desktop/VERIFICATION_2026-10-22.md)
and the [independent source/implementation review](../desktop/REVIEW_2026-10-22.md).
Actual native and Android results are distinct from the future real-model,
durability, cross-platform, accessibility and physical-phone gates.

Primary sources checked 2026-10-22: [Tauri process model](https://v2.tauri.app/concept/process-model/),
[commands](https://v2.tauri.app/develop/calling-rust/),
[capabilities](https://v2.tauri.app/security/capabilities/),
[CSP](https://v2.tauri.app/security/csp/),
[Windows prerequisites](https://v2.tauri.app/start/prerequisites/),
[Windows installer/runtime options](https://v2.tauri.app/distribute/windows-installer/),
[Compose compatibility](https://www.jetbrains.com/help/kotlin-multiplatform-dev/compose-compatibility-and-versioning.html).
No previous desktop ADR is superseded. ADR-0005 is reserved by the separate
in-progress diagnostics packet.

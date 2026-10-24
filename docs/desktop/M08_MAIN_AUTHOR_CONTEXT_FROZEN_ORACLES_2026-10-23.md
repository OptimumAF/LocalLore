# Main author/shared-context frozen review oracles

Source-only freeze from Root `9e74028` on 2026-10-23, delegated
`desktop_memory_ui`; partial M08.03/.06, D05 and D08.05. Root owns production.
Only this new document and `apps/desktop/check-main-author-context-review.mjs`
are allocated here. No existing assertions, production files or dependencies change.

## Historical source findings and actual baseline distinction

F1: Main's root context synchronizer includes retained `inFlight`, unknown,
nonterminal and unconsumed work. Its author subscriber replaces that decision
with `author.busy || retained.unknown`. During Lab-to-Play notifications,
AuthorController invalidation synchronously notifies before installing its new
context. Known shared work can therefore finish with V2 `blocked=false`.

F2: The same author subscriber ignores `acknowledgedUnresolved`. An explicitly
acknowledged unknown operation can finish with V2 `blocked=true`, despite the
root synchronizer releasing its presentation barrier. F1/F2 describe the source
ordering reviewed at the initial freeze, not failures observed in the later
corrected execution baseline: Root's independent author context ordering fix
`2a08cf2` was already present when both corresponding cases passed.

Root additionally identified gameplay host-call admission bypass: Domain1's
composer does not share V2's context block; Main forwards gameplay prepare,
submit, free_text and commit without consulting retained shared work or author
busy. Native canonical validation remains authoritative; these findings do not
establish canonical corruption or justify weakening Rust fences.

## Executable frozen shape

The runner reads the actual sibling Main, appends test exports in memory, and
bundles it with existing pinned esbuild. It does not copy the predicate or
assert source strings. Only App, ReactDOM rendering and JSX element construction
are substituted. All actual controllers, broker retention, IpcGateway and Main
subscriptions execute. Fresh unique module instances isolate cases. A bounded
synthetic native bridge handles startup, metadata, snapshots and Query2; all
inputs are synthetic. Author grant TRUE is the positive baseline, matching
the current native owner. Denied and malformed metadata are separate negatives.

The fixed tests cover: true/denied/malformed native context; known shared work
through Lab-to-Play; explicitly acknowledged unknown; acknowledged but in-flight
passive memory recovery; sticky malformed terminal; Domain1's four mutative
operations during known, unknown, recovery-in-flight and author-busy work;
acknowledged-unknown explicit next admission; readonly/status/cancel/context
switch positives; own author pending preservation and actual terminal preview
consumption only after the author controller consumes it. The preview uses
native-shaped serde DTOs, an exact SHA256 of synthetic preview JSON and the
actual request captured from Main, rather than a copied canonical validator.

The Domain1 checks call the actual Controller's public Gateway with closed,
valid Host envelopes, and count transport calls. A native Busy reply does not
satisfy a zero-dispatch guard. The acknowledged-positive case explicitly expects
synthetic native Busy after admission; it does not claim an accepted turn.
The synthetic author transport request is held to observe own-pending behavior; its
terminal response exercises the actual broker and controller decoders together.

The frozen proposed Root correction was one closed retained-work predicate, bounded coherent
application synchronization, and narrow gameplay dispatch admission using the
existing bounded IpcGateway Host envelope. Preserve readonly, status, cancel,
session selection, explicit acknowledgement and native canonical authority.
No general command endpoint, persistence or new native capability is needed.

## Reproduction and evidence limits

From `apps/desktop`, Root ran the focused checker:

```powershell
node check-main-author-context-review.mjs
```

The runner prints bounded per-case results and the exact Main SHA256. This
reviewer has not executed it: only Git/path/diff and source/log/hash inspection
was permitted. All execution below is attributed to Root, with failures retained.

This is synthetic Main/controller/subscription execution, not native IPC,
Rust/Core/Store execution, a browser/headless render, native WebView rendering,
model execution or owner acceptance. Window/document/localStorage are in-memory
stubs; no desktop or unrelated application is observed or controlled. No runtime
latency claim, restart persistence or author recovery acceptance follows.

Source-audit amendment after initial freeze `db7fe86`: the Domain1 cleanup
rejects its deferred author reply only when an author request actually started.
The other three states never consume that promise; rejecting it would create an
unhandled synthetic rejection. All fourteen cases and assertions are unchanged.
This was identified by source inspection, before any execution by this author.

## Root execution chronology

1. Initial freeze `db7fe86` was imported by Root as `66d04`. Root executed that
   version before adopting the cleanup and retained an unhandled unused-reply
   rejection in `main-author-context-original-red.log`. The run aborted; it is
   a harness defect, **not a completed behavioral RED cohort**. The original log
   records Node.js `v24.22.1`.
2. Source-audit cleanup `2c849aa` was imported as `aeedad8`. Root's corrected
   baseline at `aeedad8` retained the Main admission behavior from `aa8d56c`,
   with author ordering fix `2a08cf2` already present. The complete cohort was
   **10 PASS / 4 FAIL**, retained in `main-author-context-corrected-red.log`.
   All four failures were the Domain1 states known, unknown,
   acknowledged-in-flight recovery and author-busy: each dispatched all four
   mutative Host operations to the synthetic native bridge, which returned Busy.
   The zero-dispatch assertions correctly rejected that behavior. Both F1/F2
   context cases **passed** in this baseline, as did own-pending/consumption,
   read-only/status/cancel positives and the remaining cases. They must not be
   described as failing after the independent ordering fix.
3. Root `a430d2d` introduced one `sharedBrokerBlocked` predicate/context helper
   and the narrow gameplay Host dispatch guard. The same fourteen behavioral
   cases passed **14 PASS / 0 FAIL** without oracle changes, retained in
   `main-author-context-first-green.log`. That run's exact Main SHA256 was
   `9951ed4614ad19b1434c0887b03c0bd0557c475ef590e7115d6b33e363dcb675`.
   The corrected RED Main SHA256 was
   `a47caa507fe7eca3011b774978f1a22835b28da050a6bf788e76fac6977186fb`.
4. Root separately reported the later full frontend cohort passing at
   `da8d150`, including Main 14, author 92, callback review 13 and current V2
   and existing regressions. This is separate from the three focused logs read
   here. Root's later `5734a08` includes native harness imports/diagnostic catch
   changes; the first-GREEN Main hash above does **not** identify that later
   source and is not evidence of its native/render execution.

The three local synthetic logs were read and independently hashed by this
reviewer; private absolute paths and raw stack traces are omitted from this
public document. Artifacts remain local under the integration owner's bounded
artifact directory.

| Local log basename | SHA256 |
| --- | --- |
| `main-author-context-original-red.log` | `c0bf7c101a3d6c2ab09161a2270ae426a7ca295ef932e1465a9565fc8cf0ea32` |
| `main-author-context-corrected-red.log` | `65df9811550f296876e37f04a0729d209a19cd9a188cba4aaea3a967c4e87b94` |
| `main-author-context-first-green.log` | `84ad80edae65a1ff9775dbb8a897091276f16083efe530ec6f4f88f6d1040370` |

These actual results establish synthetic Main/controller/admission regression
coverage only. Native IPC, native WebView rendering, Rust execution, real-model
behavior, restart recovery and whole-milestone acceptance require their own
separately qualified evidence. This documentation amendment changes no tests,
Main, controllers or acceptance expectations.

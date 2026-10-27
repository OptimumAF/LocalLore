# Scene and presentation receipt transport

Refs #25 D04.04; supporting accepted #23 D02.03/.04 and #26 D05.03/.06.
This focused frontend fix is based directly on accepted main `cebaf4f9`.
It does not include the unmerged scene Core/Host or story-authoring stacks.

## Problem and boundary

The V2 receipt decoder's closed PlayRecord key set omitted both `scene` and
`story_presentation`. A committed Rust receipt containing either field became
`Wire` in the frontend, retaining an uncertain original key instead of showing
the accepted result. Its stringify-first transport copy also invoked getters
or toJSON before rejecting an adversarial DTO.

The decoder now reuses the existing V2 view model's descriptor-first bounded
JSON copier and accepts the two optional, exact shapes:

- `scene: {version:1,frame_sha256:<64 lowercase hexadecimal characters>}`
- `story_presentation: {version:1,presentation_sha256:<same lexical shape>}`

Omission remains valid; null, arrays, extra keys, future versions and malformed
hash strings refuse. These are transport checks, not Engine hash, recipe,
canonical outcome or permission validation. Existing policy, prompt and context
policy strings remain opaque bounded metadata. The legacy Receipt type gains
optional provenance slots; no Rust, native IPC, schema, storage or provider
implementation changes.

Reusing the copier intentionally tightens all V2 contexts/statuses/receipts to
the existing view-model JSON boundary: safe integers, valid Unicode, maximum
depth 16, ordinary/null object prototypes, enumerable data descriptors and no
symbol/accessor/function members. Arbitrary fractional or deeply nested extra
metadata admitted by the former stringify boundary is no longer accepted.
Current Rust DTOs inspected in review fit these existing bounds. Already parsed
duplicate JSON keys and hostile Proxy traps are outside this plain-DTO check.

## Independent freeze and measured controller evidence

Independent source-only oracles were frozen at `cf87e7df` before production.
Root reviewed the contract and executed the original checker unchanged.

| Clean, unchanged source | Result | Wall time |
| --- | --- | --- |
| `59c0ec7d` before fix | 31 passed, 15 failed, 0 setup failures | 0.2873474s |
| `5a26f623` first production | 46 passed, 0 failed, 0 setup failures | 0.2609763s |
| `582fc588` formatting only | 46 passed, 0 failed, 0 setup failures | 0.2511240s |
| `bc6a5235` focused accepted-main branch | 46 passed, 0 failed, 0 setup failures | 0.3678237s |

Three calibration groups passed before behavioral cases. The 15 baseline
failures comprise six valid provenance-shape receipts, six premature accessor/
toJSON calls, dropped-commit status recovery, exact retry after dropped
admission, and same-object receipt inspection. Existing malformed-field and
stale-context cases already passed; they are not claimed as new REDs.

The 46 cases cover both scene tuples with/without presentation, existing
presentation tuples, omitted historical fields, opaque old metadata, malformed
and adversarial field rejection, status recovery without another submit/commit,
exact request retry, same-object inspection and held-commit retirement on
session/scope/revision/lens changes. Source review found no concrete current DTO
regression. Formatting changed no intended oracle; the formatted rerun is
recorded separately.

The actual V2 controller runs against synthetic Gateway DTOs in memory; esbuild
uses `write:false`. This is **headless controller evidence only**: no DOM/SSR,
native IPC, Rust execution, Store, WebView image or real model. The tiny focused
checks ran alongside one long Rust verification process; no second native,
model or heavy build workload was started.

## Reproduce and retained evidence

From repository root with the existing locked desktop dependencies installed:

```powershell
node apps/desktop/check-v2-provenance-fields-review.mjs
node apps/desktop/verify-frontend.mjs
```

The second command registers the new checker alongside existing frontend
checks. The full run passed on clean unchanged `47b012cd` in **20.6259765s**:
strict TypeScript, normal local bundle, current request/schema checks, all
existing controller checks plus the new 46 cases, and normal-bundle exclusion of
development journeys/control hooks. The targeted Prettier check of all five
changed/new executable source files also passed on `47b012cd` in **0.5880394s**.
No native or Android build is implied by these frontend results.

Environment: Windows NT 10.0.26300 x64; Node 24.22.1, esbuild 0.28.2,
TypeScript 7.0.2, React 19.3.1 and Prettier 3.9.10. No dependency/lock upgrade.
Local gitignored logs/process records retain exact commands, source commits,
UTC start/end, exit code and source-clean/unchanged status under the stems
`d04-scene-receipt-transport-{baseline1,green1,formatted1}` and
`d04-scene-receipt-main-{focused1,frontend1,format1}`. A separate small
esbuild transform check produced identical whitespace-normalized JavaScript
from the original frozen `cf87e7df` checker and its formatted copy; no oracle
logic was changed by formatting.

SHA256 at `bc6a5235`:

| File | SHA256 |
| --- | --- |
| formatted checker | `dbef5ff00bf6905eecda0e3f235c9e96c5cfcf52a83584d2e323c7a64c27fa64` |
| v2-play-controller.ts | `bf53d743abecd54fec6e0e607d608190047e35bd50867b0526d1c9b2fff3f42c` |
| v2-view-model.ts | `8fb8ad07dead3f0bae9a47d1a79e3dba511c30eedace7c3ffa09aed570132591` |
| model.ts | `f6ed14cc802d83c249a5173ef322fd78b4ae5cbb911f6b26290927fb207fe191` |

## Remaining gates

Independent source/documentation review verified all four focused-run records,
failure categories and file hashes, and found no concrete current DTO blocker.
Full frontend integration and targeted format checks subsequently passed as
recorded above. This final documentation update changes no executable source.
Actual native scene receipt, cancel/retry/switch, cold
reopen and rendered layout require their separately scoped synthetic native
journey using the existing app-owned hidden WebView/IPC/Store harness. This
slice does not activate a new production scene recipe or claim prose quality,
offline qualification, physical-phone parity or whole-ticket completion. The
original human assessment remains **needs improvement**.

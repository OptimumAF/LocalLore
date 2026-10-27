# Corrected-timeline resume proof

Refs #30 D08.04/.05, a focused desktop adapter correction. The implementation
has passed the frozen synthetic controller suite; final integrated frontend
and native author-open verification remain pending. This does not complete D08.

## Problem and change

An explicit author correction creates a saved Domain2 child. Main connects
AuthorController's `openChild` effect to the existing `resumeTimeline` helper.
The actual gameplay Controller can successfully select that child, read its
thin snapshot and store it in `playV2`, with `play:null`. The helper previously
accepted only `play`, so it could throw `NotReady` after a successful switch.
AuthorController presented that false failure as `Wire` in the frozen case.

Production commit `6a30c90533f9027a169de3f47eff42a61d738496` changes only
`apps/desktop/ui/timeline-controller.ts::resumeTimeline`: inspect
`s.play ?? s.playV2`, requiring the same requested/selected scope,
requested/projection scope and selected/projection revision equality. The
existing error-category and `NotReady` fallback policy is unchanged. The helper
still calls the existing Controller resume/switch path; it creates no session,
canonical writer, permission or inference implementation of its own.

## Frozen evidence

The independent seven-case checker was frozen at
`c6a2d564dd0983cad612f0f36da58ecbbc9fa95f`, based on accepted
`61431c0e243617e287053dcf3f3b9ebc0d837eef`, before the production change.
Its SHA256 is `b03a341d11de49b1c1127ab360ed1606c64636c02f165543af6c465fe49a8ebd`.
Root ran both cohorts centrally; the source author did not execute the checker.
Both terminal process records report clean source and unchanged terminal source.

| Actual source | Result | Command wall time | Exit |
| --- | --- | ---: | ---: |
| Frozen `c6a2d564` | 4 passed, 3 failed | 1.063s | 1 |
| Fixed `6a30c905` | 7 passed, 0 failed | 0.248s | 0 |

The original failures are two `NotReady` outcomes for coherent new/existing
Domain2 child sessions and the false `Wire` author-open error. Legacy Domain1
success and all three negative controls already passed. The checker is unchanged
between RED and GREEN; no expected outcome was retuned.

The seven groups exercise actual Controller, AuthorController and resumeTimeline
code with synthetic Gateway/workflow DTOs:

- New corrected child: exact child session, scope and head in `playV2`, no legacy snapshot.
- Existing corrected-child session: select it without a second native resume request.
- Legacy Domain1 child: retain the original snapshot success path.
- Parent resume reply: reject it as proof of the requested child.
- Wrong snapshot scope: refuse it rather than accept a parent projection.
- Wrong snapshot head: refuse it rather than accept an incoherent revision.
- Author readonly-found outcome and explicit Open confirmed child: use the same
  helper effect composition as Main without a false post-resume error.

The last case uses a synthetic failed preparation followed by readonly lookup;
it does not apply an author correction or fabricate an accepted Core receipt.
The checker does not execute Main's subscriptions, native IPC, Store, WebView,
model inference, DOM rendering or a durable restart. Its report retains these
limits and the actual source hashes. Counts and timings are regression evidence,
not performance qualification.

## Reproduce and retained records

With the existing locked frontend dependencies and pinned Node24.22.1, from
`apps/desktop` the actual command was the task-local Node executable followed by:

```powershell
& $taskNode check-domain2-timeline-resume-review.mjs
```

Equivalent repository-root reproducer and integrated verifier:

```powershell
& $taskNode apps/desktop/check-domain2-timeline-resume-review.mjs
& $taskNode apps/desktop/verify-frontend.mjs
```

The registration beside `check-timeline-controller.mjs` is included in this
packet. The full verifier and formatting have not yet been run on that addition.
Generated JSON reports default to ignored `apps/desktop/artifacts/checks`; the
existing `LOCALLORE_CHECK_OUTPUT_DIR` can select a task-owned local output.
Raw process records and logs remain local under `<TASK_ARTIFACTS>`:

| Terminal record | SHA256 |
| --- | --- |
| `d08-domain2-timeline-red1.log` | `a98b7b57d9a0c95487e0a6871aa24e4d2b29f1ede94ee43451edd1d4dcc7289b` |
| `d08-domain2-timeline-red1-process.json` | `38cd3229c6f816891549d85c5d374a13d6e3715220a5243709281705514de652` |
| `d08-domain2-timeline-green1.log` | `5e6fe2609489d3796e89f6432b50883d0443f18297ab35c53f3f9bc013ced657` |
| `d08-domain2-timeline-green1-process.json` | `43f47b7fa27623e1d6530620aea3ae66296be7fef0a36b2a24166254943a45ad` |

Process-record UTC dates are October27; these runs occurred on October26 in the
coordinator's America/Los_Angeles timezone. No local personal paths or raw story
outputs are included here.

## Remaining gate

Root still owns formatting, full frontend compatibility, integrated source review
and the focused PR. An actual mounted author Open confirmed child/native journey
on the integrated fix remains unrun; older native author/save/restart evidence
must retain its original source attribution. No hidden Domain2 Timeline/Fork UI,
timeline-context behavior, schema, permission, Android decoder or shared memory
maintenance changes are included. Android parity, physical phones, model quality,
packaging, release and whole-milestone acceptance remain separate.

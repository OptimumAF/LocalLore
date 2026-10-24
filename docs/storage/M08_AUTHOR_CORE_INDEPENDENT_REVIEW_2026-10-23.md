# Independent Core author source review

2026-10-23. Refs #12 M08.03 / #30 D08.05. This is source review and six
frozen, **uncompiled and unexecuted** review cases. It is not author-feature,
durability, platform, model, performance or human acceptance evidence.

## Attribution and ownership

Reviewed candidate `961899ff41106ec9bc23582e14466853e6c14a1f`, production
`9a9a616` after initial production `5476e36`; existing frozen author tests
`326792b` remain unchanged. Read the exact contract at `03e25f26` in
`docs/storage/M08_CORE_IMPLEMENTATION_CONTRACT_2026-10-23.md`, AGENTS.md,
README.md, docs/ISSUE_WORKFLOW.md, roadmap #3, #12/#30 task bodies and recent
claims. The author owns production and is separately executing Core checks.

Coordinator approved exactly two NEW paths before writes. Claims #12
`6376794391` and #30 `6376794567` identify agent
`/root/author_core_review`, separate `review/m08-author-core` /
`source-author-core-review`, and native Engine/canonical-record/actor-v2 APIs.
No existing production, tests, schema, Host, Store, compiler or platform source
was changed. Root owns integration and any demonstrated repair.

The NEW `crates/locallore/tests/m08_author_review.rs` is frozen at
`b6aa94a1e3576e8c42add0937ed28c2f27d785f2`, SHA-256
`48c16c3b90fa7c42c1f06c3a7286390b5d208e247733973c51e40fea9dfa25d1`.
These cases were added after the reviewed implementation existed, before their
first execution; they are not described as pre-implementation tests or an
actual failing reproduction.

## Review observations

No additional concrete production defect was established by this finite source
review. The review examined the complete new author module, the complete engine
diff from `42ca071`, existing author cases, scope/lineage and relevant legacy
consumer entry points. The following statements describe source, not executed
outcomes:

- One records vector determines head, prefix/basis, boundaries and replay. The
  compatibility receipt cache is derived, invalidated after append, and absent
  from the new canonical authority paths.
- Preparation binds full actual parent and fork bases; application re-prepares
  and compares the entire opaque plan. Pure candidate construction leaves the
  original Engine unchanged and does not grant a live author capability.
- History-only author restore requires actual immediate-parent/fork binding,
  current retained boundary, actual old value and full regenerated record
  equality. Creation head H remains provenance when its excluded future is not
  in a retained child. Ordinary missing fork metadata is not invented.
- Discovery bindings are regenerated for each accepted discovery event.
  Actor-event views resolve the value at that observation, rather than current
  private world truth. NPC receipt views contain eligible events only, remove
  empty records and omit the raw Request/Proposal/narration envelope.
- Private author truth references, reason and before-source remain in native
  canonical/author-tool DTOs. Their Serialize implementations do not make them
  safe ordinary wire/provider inputs. Consumer migration remains mandatory.
- Exact wrapped JSON comparison and recursive duplicate-key rejection prevent
  permissive unknown-field or malformed-wrapper fallback. Original closed
  corrupt-history mapping correction `9a9a616` is retained unchanged.
- Existing record/count/history/projection byte ceilings are checked before
  appending candidate state. This review did not measure allocation overhead,
  worst-case replay time or cancellation latency of full-history operations.

The `receipts() -> &[Receipt]` compatibility API necessarily loses private
records. In particular, a caller passing an author-only branch's empty filtered
slice to legacy `Engine::replay(seed, receipts)` supplies no evidence from which
that API could detect missing author history. This is a consumer-closure
constraint, not a newly established defect in the candidate: Root must migrate
all canonical replay/archive/prefix/retention paths to records and keep current
author wire/UI unavailable until closure. Existing query/compiler/Store/schema
paths were deliberately outside this review's ownership. A favorable source
review does not qualify them or make Domain 2 public operations available.

## Frozen independent cases

All six cases use the actual Engine and synthetic Lantern Quay fixture, no
alternate engine or accepted-state mock:

1. A to B to A world changes retain each accepted observed value and distinct
   observation source; the NPC retains A and receives no private B/reason.
   Complete supported mixed history replays byte-equivalently.
2. A two-discovery receipt requires both bindings in exact order. Missing,
   extra, reordered and foreign-sibling truth bindings must fail closed.
3. Unknown wrapper fields, an incompatible wrapper kind, unknown record version
   and an actual duplicate record_version key must fail without legacy fallback.
4. Equal scope/head/mechanical projection with different accepted turn identities
   must reject application of a prepared plan as Stale and preserve the actual
   parent. Revision/projection equality alone is insufficient.
5. Nested authored/ordinary lineage preserves original record scopes through
   prebirth historical reads. A real known child continuation restores exact
   source basis; replay without an unrecorded ordinary-fork edge rejects it.
   No excluded parent future-H recreation is required.
6. A positive witnessed gift remains visible in an NPC event-only receipt, while
   an unwitnessed private player statement, raw request/proposal/narration,
   private author reason and changed world truth remain absent.

No expected output or original test was altered. No actual RED/GREEN result is
claimed. If any case is invalid, preserve this freeze and document the specific
contract/fixture correction separately before changing its assertion.

## Actual checks and next runnable checks

Actual local checks only:

```text
rustfmt --edition 2021 crates/locallore/tests/m08_author_review.rs
git diff --check
Get-FileHash crates/locallore/tests/m08_author_review.rs -Algorithm SHA256
```

Formatting/parser and whitespace checks succeeded. They do not establish Rust
typechecking or behavior. No Cargo, Node, Gradle, app, native WebView, model,
device, ADB, CUA, desktop capture/control, download, protected-resource, setting,
PR or merge operation was performed by this reviewer. Git
`2.33.0.windows.2`; PowerShell `7.6.5`; rustfmt
`1.8.0-stable (01f6ddf758 2026-02-11)`.

After Root integrates the NEW test and explicitly allocates the exclusive heavy
slot, run unchanged against the attributable production source:

```text
cargo test --locked --offline -p locallore --test m08_author_review --jobs 1
cargo test --locked --offline -p locallore --all-features --test m08_author_review --jobs 1
cargo clippy --locked --offline -p locallore --all-targets --all-features --jobs 1 -- -D warnings
```

Use the existing task-owned target/TEMP policy, no asset/dependency downloads.
Retain actual logs and failures, attribute source revisions, and correct only
demonstrated defects under the production owner's claim. Core and full
workspace compatibility are separate. Next integration gates remain shared
mixed-history Store/schema 5/archive 3, actor/query/compiler 2/Play 2.5 privacy
closure, native grant/consent lifecycle, platforms and appropriate actual
execution. M08 and D08 remain unchecked.

# Borrowed observer observations

Refs #11 M07.01/.03/.04, partial prerequisite. The public Rust-only
`Engine::visit_actor_observations` visits borrowed accepted events through exactly
the lineage/witness predicate used by `character_context`. It adds no wire command,
inspection grant, persistence or generation capability. Trusted callers choose the
actor; externally exposed adapters retain their own authorization responsibility.

Scope, current Engine head, actor and `(after, through]` range are checked before
any callback. `through` cannot exceed the current head. The method allocates no
history copy and exposes no excluded row IDs/counts. The visitor may stop normally
with false; callback records are accepted observations, not a transcript or proof
that a statement is true. Existing CharacterContext behavior is unchanged.

Cancellation is checked initially, every32 scanned events, before each eligible
callback and at completion. It may arrive after previous callbacks; consumers
must discard partial accumulation on `Err(Cancelled)` and never publish it as a
complete packet. The Engine stays immutable. Callbacks are trusted native Rust
code, not arbitrary model/renderer execution; no shell or server exists here.
Scanning remains O(total accepted history), including excluded events. This is
bounded callback responsiveness, not a range index or constant-time privacy claim.

Implementation commit `dcb6b5a` starts at accepted main `32173cb`. Actual Windows
x64/Rust1.93.1 checks, debug0/incremental0, locked/offline task-owned D: target:

```powershell
cargo test -p locallore --test actor_observations --test contracts --locked --offline --target-dir <task>/core-rust
cargo clippy -p locallore --all-targets --locked --offline --target-dir <task>/core-rust -- -D warnings
cargo fmt --all -- --check
git diff --check
```

**29 passed** (3new and26existing contracts), zero failures/ignored; strict
Clippy/format/diff checks passed. Tests compare actual root/fork context selection,
exclude parent-later/sibling/nonwitness data, preserve canonical bytes/receipts,
validate binding/range before callbacks and prove early stop and cancellation
while scanning an entirely hidden history. Logs are local/gitignored under
`target/visitor-*`. There is no UI/model/SQLite/APK/device execution in this slice.
The separately claimed derived-memory owner consumes this port; its production
Store/migration/index/summary integration and full M07 acceptance remain pending.

Publication integration merged accepted main `ad5868899984540ef86b3e0293ac2a30c746f752`
as `0793ec6`, retaining the newer private recorded-prompt replay/fork fix. The
complete integrated workspace then **233 passed, zero failed or ignored**, and
strict workspace/all-target Clippy passed using the task-owned `m07-context`
target. Logs: `target/integrated-workspace.log` and `integrated-clippy.log`.
The independent source-only report is M07_EVENT_PORT_REVIEW.md; it also inspects
the earlier test-only runtime scheduling fix without claiming reviewer execution.
These integrated Rust tests include the Android/JNI host adapter; APK/device,
frontend/native rendering and model checks were not repeated for this read-port
addition. The production context change's separate dated checks remain in its
integration report.

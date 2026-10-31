# Author packet A: verification in progress

Refs #25 D04.02, supporting D04.04, #9 and draft PR301. **The corrected baseline
is valid behavioral RED. Author behavior and GREEN remain pending.** This is a
bounded synthetic runtime check, not desktop IPC, rendered UI, packaged-worker,
real-model, Android/device, story-quality or release evidence.

## Authority and distinct attempts

The owner approved the [R3 compatibility amendment](D04_AUTHOR_CODE_R3_ADMISSION_2026-10-31.md)
in `call_bc8a3386f5f7418a98b83643ce35129c`, answering
`Approve amended code checks`. Only retained metadata increased1280 to1344KiB;
all other caps and the original target baseline remain unchanged. The actual
decision and immutable R3 Stage were created exclusively before admission.
Their combined4,769B cost brought metadata to1,249,779B. Full prospective
admission/START/child reserve was1,361,395B, below1,376,256B by14,861B.

The [original first baseline](D04_AUTHOR_CODE_CAPTURE_FAILURE_2026-10-31.md)
remains permanently invalid, with incomplete prefixes, unknown ownership history
and no accepted count. The [R2 pre-admission refusal](D04_AUTHOR_CODE_R2_PREFLIGHT_REFUSAL_2026-10-31.md)
launched no test child. Its decision, Stage, source and refusal remain immutable.
R3 reuses original successful format/preparation under their actual old source,
tool, command and raw-log identities. It did not run preparation again.

## Actual corrected baseline

Root ran the reviewed guard from the physical D: source checkout using the
pinned installed64-bit Windows PowerShell5.1.26100.9818. It freshly verified
process ownership/ambiguity, source, tools, retained products/fixtures and storage,
then launched the fixed Node24.22.1 coordinator. No app launched.

```powershell
& 'C:/Windows/System32/WindowsPowerShell/v1.0/powershell.exe' -NoProfile -NonInteractive -File '../author-integration-artifacts/d08-fork-native-20261030-v1/author-r3-admit.ps1' -Phase baseline
```

Its exact Cargo child command was:

```powershell
cargo test --manifest-path crates/locallore-local-runtime/Cargo.toml --lib --features engine-adapter,development-worker --locked --offline author_ -- --test-threads=1 --format terse
```

Source revision `69761326276fad8824a0c0fa7230d8c963c97748`, tree
`fd4ed72b594b348a2845dd09abc028f2ae67231c`, contains the old runtime behavior
and frozen FIRST. The six runtime source hashes match the original prepared
baseline; later documentation did not change that behavior.

Actual result: **16 executed,4 passed,12 failed,0 ignored,48 filtered, exit101**.
The failures directly demonstrate missing Author request admission and the
legacy reply cap. Several lifecycle, singleton and metrics groups stop at that
earlier admission refusal; their later assertions were not fully reached.
No setup failure or compilation error appears. The unused metrics helper emits
a dead-code warning at this old-behavior stage; no strict-Clippy pass is claimed.

The child closed normally with `unknown:false`, no overflow, timeout or kill.
`processTreeContained:false` remains explicit: this is cooperative child/pipe
closure, not OS-enforced descendant containment. Complete stdout6,945B and
stderr708B are retained losslessly. Root read both entire decoded logs and wrote
the actual16-case behavioral-RED review gate.

Cargo reported0.80s test-profile preparation/completion and0.22s test execution;
there is no separate measured compilation time. The child wrapper
recorded1.652s. These are synthetic code-check costs, not inference latency.
The standalone toolchain remains Cargo/rustc1.93.1 with pinned locked offline
dependencies, one job, incremental0/debug0 and TEMP/TMP on D:.

## Local evidence and remaining checks

The ignored retained group contains:

- `author-r3-baseline-1-process.json`, SHA256
  `42c4b299db144e2b846f04e80efc71e203a6e628bb93e36e7abb200aaf883e22`.
- `author-r3-phase-baseline.json`, SHA256
  `2a16bebcb65e3a511f6ef880d611c074486e2b1dfbb511a96e64c9a17848ce4c`.
- Complete raw stdout SHA256
  `915a04e3c3336ce4cda3a31b78e7f281c04f1d8222a26c264972d2cc54556da2`
  and stderr SHA256
  `48e3ae9a5ab2b9b1d8ee1055e1dbdfd893ef29d48cf7b8f916aacb47cfe22e41`.
- The actual Root baseline review, actual owner decision, immutable Stage,
  admission/START and all historical failure/source/product/fixture proofs.

Final inventory before the phase receipt: metadata1,264,328B,
target12,287,065,614B unchanged,47 retained empty runtime fixture roots,
old records549,989B physical/570,664B charged logical bytes, fork fixtures671,744B.
No forecast miss occurred. The existing normal desktop binary SHA256
`0482d821a12a92333a9974a43f301d5fe36d5ca08e7c75843c3d04f19b0e6f1f`
remains unlaunched.

Different-author Phase2 may now implement only the frozen private runtime
contract. Production Author remains disabled. Root must review/integrate the
source, format only the three production Rust files, preserve FIRST bytes,
then obtain actual GREEN, full runtime, format, strict-Clippy, normal desktop
build and exact accepted-main readback results. None of these later results is
claimed yet. The PR stays draft; D04 and the desktop epic remain open.

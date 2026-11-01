# SDK7 retirement closure compatibility

The reviewed retirement executor inherited from PR306 rejected a coherent
`owned-emulator-record-ui-v1` closure before native ownership because its fixed
protocol allowlist ended at SDK6. The change adds that exact SDK7 member. All
three earlier profiles remain admitted. Admission and worker protocols must
still match, all 15 cleanup fields must be true, and the existing proof,
identity, plan, deadline, native ownership and finalization checks remain.

## Host verification

The original five tests were captured against unchanged production at
`ac2ad7a42357c9a7413a10ebb9358016ba1b93dd` before the fix: three passed and
two failed assertions, with no errors or skips. The two failures were the
coherent SDK7 identity extraction and synthetic exact-plan completion.
All 38 negative and legacy-profile subcases passed.

After the one-member change, the same five tests plus all 15 existing
orchestrator tests passed: 20 methods, 69 subcases, zero failures, errors or
skips. The new test file stayed byte-identical between captures, SHA-256
`a19b1ed5e3ef9ae90aa801d952c9e4d501ef1cb72b5d131c5c1850c0c3bd7cff`.
The production executor SHA-256 after the change is
`1475a342bccc6567e6ac447c1f3d8debb4b8d44dab3b179223ee13f484ed9b37`.

Both cohorts used the existing finite WindowsJob owner with a 180-second
limit, joined actual worker identities, complete captured output and known
cleanup. Source and helper pins matched before and after each run. The RED
owner took 13,599 ms; the GREEN owner took 25,936 ms.

The fixed private command was `python -I -S -B run-focused-v1.py red`, followed
by the same helper with `green`, from the physical D: test worktree. The helper
loaded only `scripts.tests.test_receipt_avd_retirement_sdk7` for RED and added
`scripts.tests.test_receipt_avd_retirement` for GREEN. Process-local temporary
files used distinct D: directories. Captures, source copies, rosters and tiny
fixtures remain under
`D:/Dev/Experiments/LocalLore/2026-10-31-player-presentation-capacity-v1/retirement-sdk7-host-v1`.
The measured footprint after GREEN was 3,120,171 bytes, within its 256 MiB cap.

| Closed receipt | SHA-256 |
|---|---|
| RED `red-v1/closed-result-v1.json` | `ef4edf1d0c7daaed6f2d848fa22d56bfddab8c31aa1d03afc405fcc107f83ed0` |
| GREEN `green-v1/closed-result-v1.json` | `176261a411173493ec1c1ad62097f80025eb01070847970c016e2f32ee51f1e5` |

## Limits

Tests used isolated tiny synthetic registries and the existing mock native
fixture. Real native APIs, network sockets and test child launches were
blocked. No candidate image, production ledger, SDK, ADB, emulator or model
operation occurred. This verifies protocol compatibility and preserved
refusal boundaries; it does not approve or qualify any real retirement or
guest run. Exact operator approval and all fresh guarded execution checks
remain necessary.

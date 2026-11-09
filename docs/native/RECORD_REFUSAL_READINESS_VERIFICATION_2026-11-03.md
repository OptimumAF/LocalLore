# SDK18 readiness verification — B122

Refs #14 (M10.02) and #13 (supporting M09.06). This is a host readiness slice stacked on [PR #398](https://github.com/OptimumAF/LocalLore/pull/398) at `98ec33a586f462c93819be555cf9c86b71fb64de`. The tested code commit is `83babec7a222cdc8e46825bb65c3dc8694f9c444`. All 2,674 inherited paths were byte-identical; the tested tree added only the preflight and its tests.

## Host suite

The checked Windows owner launched pinned Python 3.14.7 with `-I -S -B` and a start barrier after job attachment. The 180-second wall and 262,144-byte capture limits applied. The worker loaded the same seven `scripts.tests` modules in both phases:

- `test_record_refusal_readiness`
- `test_host_commit_capacity`
- `test_receipt_avd_environment`
- `test_receipt_avd_storage`
- `test_receipt_avd_storage_adversaries`
- `test_record_preparation_refusals`
- `test_record_refusal_generation`

The initial suite ran 178 methods with two assertion subevents in one method: extra-field and boolean commit-checker results improperly retained numeric facts. The initial owned run exited 1 with known cleanup. The correction changed only `_commit_observation`; the selected IDs and tests were unchanged. The final suite passed **178 distinct methods in seven classes** (eight new, 170 regressions; zero failures, errors or skips; unittest 7.308 s, owner 8.150 s, exit 0 with known cleanup). The suite covers closed output, malformed and hostile results, trusted refusal identity, interruption, late input drift, and loopback bind/close behavior. Earlier source-review fixes preceded execution and are not counted as runtime failures.

Independent source, oracle and evidence reviews inspected the frozen inputs and checked execution records. Failed and passing captures, the initial code, and review corrections remain in private D: evidence. The two retained temporary fixture directories cover the observed window from the initial launch through the final owner result; their selection does not prove process attribution.

## Actual file-only observations

1. The public `inspect` command ran the genuine loaders using the initial module and wrote the first advisory report. It returned 1 with `host_commit_capacity`, stable frozen inputs, passing port checks, and a storage preview that would fit but did not grant admission. The checked owner completed with known cleanup in 36.179 s.
2. After the narrow correction, the public entry point refused the existing report with return 1 before loader or port observation; the report bytes stayed intact. The same checked owner then ran the final code's actual `_probe(_api())` once with the genuine fixed loaders and wrote a separate private report through the verification wrapper. This verified the final advisory core, not a second fresh public CLI write. It returned the same refusal category against the unchanged 10 GiB commit requirement; frozen inputs were stable. The checked owner completed with known cleanup in 41.802 s.

Both observations used six temporary loopback binds and returned a read-only ledger preview. No forbidden action or key-content read was observed by the audit hooks. The source and ledger stayed unchanged; guest, runtime, control and live-operation paths remained absent. The wrapper's file-open size accounting is not a measurement of physical I/O. The sampled refusal does not establish the cause of the older preparation failure or describe current free capacity.

The conditional run draft remains private and nonexecuting. No authority was written and no reservation, device discovery, app installation, Android instrumentation, model or inference run occurred. **Android cancellation tests: 0/5 executed.** Full M10.02 and M09.06 remain unchecked. Before any proposed run, verify readiness following a meaningful host change and obtain fresh authorization; the previous grant is spent.

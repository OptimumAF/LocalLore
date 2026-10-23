# Synthetic capacity helper failure boundary

Refs #8 (M04.04), stacked on the schema3 capacity fixtures in PR #87.
This is an opt-in verification boundary. The production engine, Host/JNI
commands, schema3 and local gameplay authority remain unchanged.

The fixed relief profile remains32 pages, with17 initial pages,14 padding rows
and15 freed pages. Normal Full/recovery evidence stays separate from injected
helper failure: a helper fault is never an accepted gameplay outcome or a
fabricated native Full response.

## Android admission and continuation

Only the visibly labelled debug/testOnly `org.locallore.app.capacityfaultsv3`
installation admits fixed failure controls. It has the exact relief metadata
(schema3/format2/pages32/initial17/rows14), plus `faults_format=1`, an exclusive
`build-capacity-faults-v3` output and `.gradle-capacity-faults-v3` project cache.
The parent verifies the manifest before creating an owned fault attestation.
The one-shot child independently verifies the fixed package/private path,
marker/token and exact schema read-only. Controls do not accept commands, SQL,
paths outside the synthetic root, arbitrary timing budgets or model input.

Fixed faults cover malformed terminal output, oversized output, deadline expiry,
failure after actual owned fill/close, and detectable marker drift after the
read-only check. A suspended precommit callback also exercises the actual native
dispatch boundary. Counters increment immediately before underlying dispatch;
post-return reply records alone cannot prove that no call was attempted.

Initial preflight refusals are known only when their child is terminal and its
readers are drained. After successful preflight, ownership drift or ambiguous
completion poisons the process-wide continuation fence, even if the child is
later reaped. A new helper instance cannot erase it. Recheck the fence after
awaited hooks and immediately before native exchange.

After poisoning, allow closure/drainage of existing native owners. Block new
fixture creation, helper/SQL cleanup, native dispatch, reopen and release probes.
Retain the synthetic root and primary failure. Tests observe counters and closed
child/reader evidence already owned by the parent; they must not query canonical
state or inspect/delete retained files to turn uncertainty into a success.
Each poison case runs in its own explicitly selected instrumentation process;
the sticky flag has no reset API. Nested fault classes stay out of normal default
discovery, which retains the original three relief cases.

The12-second child wait and1/2-second terminate/kill observation budgets are
unchanged. Pipe buffering is bounded. An observed timeout is not evidence of
death: only terminal process/reader observations prove that cleanup completed.
An unreaped owner blocks dependent work and remains a failure.

Android's [API35-era process implementation](https://android.googlesource.com/platform/libcore/+/android-15.0.0_r1/ojluni/src/main/java/java/lang/UNIXProcess.java)
closes streams during `destroy()`. Observations distinguish an IOException seen
after the parent's atomic termination-request flag from unexpected reader
failures. This records order/type, not proof of exact causality. Timeout tests
still require the actual deadline, owned termination, terminal reap and both
readers stopped. Aggregate `readFailed` and process-wide poison remain set;
shutdown observations never authorize further cleanup or native work. Other
fault cases require no reader failure.

## Host admission and continuation

The host example's fixed optional fault selector is confined to a fresh owned
synthetic directory with an additional exact fault marker. The Python child
retains exact schema3/owner read-only guards. Actual fill precedes injected
malformed/overflow/deadline/failed-terminal cases; cleanup refusal is separately
observable. Normal CLI behavior and normal version2 reports remain compatible.

Record the original failure, terminal/kill/reap evidence and cleanup outcome
separately. A failed fill never resumes Host calls, including after successful
cleanup. A known-reaped child may permit only the fixed owned-table cleanup after
fresh exact read-only admission. Unknown live ownership permits no follow-on
helper, probe or cleanup. No guessed process death, replacement turn or fresh
prepare may be used as recovery evidence.

The host4KiB file-output threshold is observed while polling, not a filesystem
quota. The10-second child deadline and2-second owned kill/reap observation remain
fixed. Synthetic faults do not prove an unkillable-process, partition ENOSPC,
power-loss, OS-adversary, physical-phone, ARM64 execution or real-model gate.

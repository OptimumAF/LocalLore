# Record preparation refusal metadata

M10.02, supporting M09.06. Implemented for review; not device qualification.

The SDK18 inner stage runner keeps its existing phase, authority, attempt,
source, storage, owner, deadline and success checks. It adds `step`, a fixed
marker set before each relevant call: `validate_inputs`,
`prepare_authorization`, `prepare_dispatch`, `prepared_validation`,
`prepare_budget`, `run_inputs`, `activation_budget`, `activation_dispatch`,
`activation_validation`, `final_validation`, `completed`.

A marker says which boundary was attempted. It does not prove that a call
completed, a guest exists, a reservation was acquired or any test ran. For
compatibility, the broad phase remains `prepare` through prepared validation
and its following budget check. The activation budget is still in phase
`run_inputs`; final validation is still in phase `activation`.

On an exception, `passed` is false. `failure_type` is selected by exact class
identity, not by matching an arbitrary class name. `reason` accepts only one
exact built-in string argument on an exact trusted exception class:

| Class | Allowed reason literals |
| --- | --- |
| FreshRunRefused | operation_budget, prepare_terminal, prepared_state, already_used, worker_claim, source_snapshot, source_closure, binding, ledger_changed, activation, activation_cleanup, storage_closure |
| EnvironmentRefused | host_capacity, host_commit_capacity, host_commit_unavailable, ports_unavailable, storage_registry_locked, storage_storage_capacity_exceeded |
| StorageRefused | registry_locked, storage_capacity_exceeded |

Unknown reasons, extra arguments, string subclasses, arbitrary objects,
exception subclasses and spoofed names produce reason `operation_failed`.
A trusted exact class retains its finite `failure_type` even when its argument
is unknown; subclasses and name spoofs collapse both fields to
`operation_failed`. Exact
KeyboardInterrupt has reason `cancelled`. Known built-in I/O/value/key/type
exceptions retain a finite class category with generic reason. No error
string/repr, cause, context, traceback, SDK stderr, path or token is rendered
by this classifier. It uses the already captured rules/API identities and
does not import or query operational services during failure handling.

Successful stages have no failure reason/type. Publication failure keeps the
existing failed result and fixed stderr notice; no retry is added. Unknown
failures intentionally remain less specific than internal exceptions.

This change does not recover the missing reason from B119. That original
approved attempt stays failed/spent, Android 0/5; subsequent read-only memory
observations are not evidence of its original cause.

The old outer FRESH_OPERATOR pin and all frozen paths/authorities are preserved.
Consequently the changed inner bytes cannot pass that old outer admission.
This is a host-verified operator implementation, not a refreshed runnable
SDK18 operation. A future device run needs a newly reviewed coherent freeze,
exact proposal, readiness/admission and separate applicable approval. Never
overwrite the old frozen inner file or edit its spent records to adopt this
change. There is no emulator, ADB, model, phone or settings operation here.

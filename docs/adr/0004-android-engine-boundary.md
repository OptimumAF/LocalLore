# ADR-0004: Android engine sessions and explicit commit

- Date: 2026-10-22
- Status: bounded integration accepted in [#20](https://github.com/OptimumAF/LocalLore/pull/20); lifecycle follow-up for review
- Scope: M03.03, [#7](https://github.com/OptimumAF/LocalLore/issues/7)

## Context and decision

The Compose shell needs the actual Rust engine without duplicating gameplay
rules or letting a cancelled coroutine hide an already committed turn.

Use one name-based JNI method, `NativeBridge.call(Long, ByteArray?): ByteArray`,
with strict UTF-8 JSON control v1. Session/operation numbers are monotonic opaque
IDs, never pointers. Rust owns engines, cancellation tokens and prepared receipts.
No accepted-history deserializer is added. Inputs are capped at 24,576 bytes
before JNI copying; replies at 65,536. Unknown fields/operations, invalid UTF-8,
version, handle, owner thread and scoped operation IDs return bounded error
categories without echoing private inputs.

`create` establishes the owner thread. `begin`, `snapshot` and `commit` require
that thread. `run` requires another thread; Kotlin uses `Dispatchers.IO`.
The existing Rust director/validator/narrator fake pipeline runs on a clone and
produces a prepared receipt without changing authoritative state. Its complete
prospective accepted reply is bounded before preparation succeeds.

The ViewModel checks generation/revision, calls synchronous `commit`, and
publishes accepted state in one main-thread call stack without suspension.
Rust revalidates/commits the request and safe narration. Duplicate commits return
the cached receipt. Racing cancellation has one outcome: cancel wins and canon
stays unchanged, or commit wins and cancel reports `already_committed`.
Cancellation never rolls back accepted history. Unknown commit transport failure
requires demo reset; it does not claim rollback or retry from stale displayed state.

`cancel` signals the captured operation. `destroy` invalidates the ID immediately,
signals work and drops registry ownership. A Kotlin worker may temporarily
retain an `Arc`; cooperative polling returns and releases it. Reset destroys
the old session and creates a new one. Disposal closes idempotently. `onStop`
cancels pending work; configuration recreation retains the ViewModel/accepted
in-memory engine. Process death starts fresh.

ViewModel disposal is terminal: a retained Reset callback after `onCleared`
must do nothing. It cannot create another native session after its lifecycle
owner has released the original one. The [ownership follow-up](../native/OWNERSHIP_FOLLOWUP_2026-10-22.md)
records the reproduced regression and the actual JNI checks.

Rust creates no threads, retains no JNI environment/reference, makes no JVM
callbacks and borrows no array elements across calls. Local references die at
return. JNI allocation exceptions return pending without further JNI calls.
Dispatch/input processing contain Rust panics; abort/OOM is not recoverable.

The demonstration caps retained sessions at 32, retained operations globally at
64, current operations per session at one, and committed turns per session at
64 (exact retries remain idempotent). Control locks never cover generation.
`stats` exposes text-free counts for ownership tests, not diagnostic exports.

## Consequences and limits

The backend remains explicitly fake inference over the original compiled fixture.
The actual engine owns mechanics, events and observer filtering. No real model,
arbitrary story import, durable save, callback framework or production speed
claim follows. ARM64 build/package evidence differs from x86_64 execution.

JNI 0.21.1 without invocation is a deliberate older pin; the current upstream
API/license comparison is in [source review](../native/SOURCES_2026-10-22.md).
See [build details](../native/BUILD.md). Revisit caps, commit ownership and
recovery when M04 adds transactions/process-death recovery; this ADR promises
no durable saves.

Direct mutation by a suspending worker leaves a committed-result delivery race.
A callback/thread framework adds unnecessary ownership; Kotlin gameplay rules
would create competing authority. This slice uses none of those alternatives.

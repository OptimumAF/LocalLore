/* Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0 */
package org.locallore.app

import java.util.UUID
import kotlinx.coroutines.CancellationException
import kotlinx.coroutines.CoroutineScope
import kotlinx.coroutines.CoroutineStart
import kotlinx.coroutines.Job
import kotlinx.coroutines.delay
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.launch

internal const val FORK_MAX_REVISION = 9_007_199_254_740_991L
internal data class ForkScope(val story: String, val branch: String)
/** Exact four-field native input. Expected parent head guards new creation only. */
internal data class BranchForkInput(val parent: ForkScope, val childBranch: String,
    val expectedParentRevision: Long, val atRevision: Long)
internal data class BranchForkContext(val session: String, val parent: ForkScope, val head: Long,
    val view: String = "play", val observer: String = "player", val epoch: Long = 0)
internal data class BranchForkRecovery(val version: Int, val input: BranchForkInput)
internal data class BranchForkOutcome(val version: Int, val scope: ForkScope, val parent: ForkScope,
    val forkRevision: Long, val headRevision: Long, val created: Boolean)
internal enum class BranchForkPhase { REGISTERED, RUNNING, COMPLETED, REJECTED }
internal data class BranchForkStatus(val operation: Long, val phase: BranchForkPhase,
    val cancelRequested: Boolean, val outcome: BranchForkOutcome? = null, val error: String? = null)
internal data class BranchForkLookup(val found: Boolean, val outcome: BranchForkOutcome?)
internal data class BranchForkUiState(val context: BranchForkContext? = null, val visible: Boolean = false,
    val busy: Boolean = false, val input: BranchForkInput? = null, val lookupOnly: Boolean = false,
    val operation: Long? = null, val outcome: BranchForkOutcome? = null,
    val lookup: BranchForkLookup? = null, val uncertain: Boolean = false, val notice: String? = null)
internal class BranchForkFailure(val category: String) : Exception("Timeline fork could not be confirmed")
internal interface BranchForkGateway {
    suspend fun register(context: BranchForkContext, input: BranchForkInput, consent: Boolean): BranchForkStatus
    suspend fun run(operation: Long): BranchForkStatus
    suspend fun status(operation: Long): BranchForkStatus
    suspend fun lookup(input: BranchForkInput): BranchForkLookup
    fun cancel(operation: Long? = null)
    fun close()
}
internal fun validForkInput(value: BranchForkInput): Boolean =
    listOf(value.parent.story, value.parent.branch, value.childBranch).all { it.matches(Regex("[A-Za-z0-9_-]{1,64}")) } &&
        value.parent.branch != value.childBranch && value.expectedParentRevision in 0..FORK_MAX_REVISION &&
        value.atRevision in 0..value.expectedParentRevision
private fun validContext(value: BranchForkContext): Boolean = value.session.toByteArray(Charsets.UTF_8).size in 1..128 &&
    value.head in 0..FORK_MAX_REVISION && value.view == "play" && value.observer == "player" &&
    listOf(value.parent.story, value.parent.branch).all { it.matches(Regex("[A-Za-z0-9_-]{1,64}")) }
internal fun matchesForkOutcome(outcome: BranchForkOutcome, input: BranchForkInput): Boolean =
    outcome.version == 1 && outcome.scope == ForkScope(input.parent.story, input.childBranch) &&
        outcome.parent == input.parent && outcome.forkRevision == input.atRevision &&
        outcome.headRevision in input.atRevision..FORK_MAX_REVISION

/** UI owner only: no engine, store, inferred boundary or automatic child selection. */
internal class BranchForkController(
    private val scope: CoroutineScope,
    private val gateway: BranchForkGateway,
    private val saveRecovery: (BranchForkRecovery?) -> Unit,
    private val onResolved: (BranchForkOutcome) -> Unit = {},
) {
    private val mutable = MutableStateFlow(BranchForkUiState())
    val state = mutable.asStateFlow()
    private var generation = 0L
    private var active: Job? = null
    private var disposed = false
    private var recovery: BranchForkRecovery? = null
    private var origin: BranchForkContext? = null
    private var cancelRequested = false
    private var recoveryControl = false

    fun contextChanged(context: BranchForkContext?) {
        if (disposed || mutable.value.context == context) return
        ++generation
        gateway.cancel()
        active?.cancel()
        origin = null
        mutable.value = BranchForkUiState(context = context, busy = active != null)
    }
    fun prepare(atRevision: Long, childBranch: String = UUID.randomUUID().toString()) {
        val context = mutable.value.context ?: return
        if (disposed || active != null || recoveryControl || !validContext(context)) return
        if (recovery != null) {
            mutable.value = mutable.value.copy(notice = "Look up or explicitly forget the previous fork identity before preparing another.")
            return
        }
        val input = BranchForkInput(context.parent.copy(), childBranch, context.head, atRevision)
        if (!validForkInput(input)) {
            mutable.value = mutable.value.copy(notice = "Choose a valid fork revision and a distinct fixed timeline ID.")
            return
        }
        origin = context
        mutable.value = BranchForkUiState(context = context, visible = true, input = input)
    }
    fun restore(saved: BranchForkRecovery) {
        if (disposed || active != null || recoveryControl || saved.version != 1 || !validForkInput(saved.input)) return
        ++generation
        gateway.cancel()
        recovery = saved.copy(input = saved.input.copy(parent = saved.input.parent.copy()))
        origin = null
        mutable.value = BranchForkUiState(context = mutable.value.context, visible = true,
            input = recovery!!.input, lookupOnly = true, uncertain = true,
            notice = "Recovered identity is lookup-only. Lookup never creates a missing timeline.")
    }
    /** The caller passes the SAME rendered input object and an explicit confirmation. */
    fun confirm(rendered: BranchForkInput, consent: Boolean) {
        val before = mutable.value
        val context = before.context ?: return
        if (disposed || active != null || recoveryControl || !consent || !before.visible || before.lookupOnly ||
            before.input !== rendered || origin != context || !validContext(context) || !validForkInput(rendered)) return
        val saved = BranchForkRecovery(1, rendered.copy(parent = rendered.parent.copy()))
        val saveGeneration = generation
        val saveOrigin = origin
        recoveryControl = true
        try { saveRecovery(saved) }
        catch (_: Exception) {
            if (sameRecoveryOrigin(before, saveGeneration, saveOrigin))
                mutable.value = mutable.value.copy(notice = "The exact recovery identity could not be saved. No fork was dispatched.")
            return
        } finally { recoveryControl = false }
        // The save succeeded even if its callback retired the old presentation.
        // Retain that exact identity for explicit lookup; never dispatch a stale origin.
        recovery = saved
        if (!sameRecoveryOrigin(before, saveGeneration, saveOrigin)) {
            origin = null
            return
        }
        cancelRequested = false
        work { ticket ->
            mutable.value = mutable.value.copy(uncertain = true, operation = null)
            var status = gateway.register(context, saved.input, true)
            val operation = status.operation
            if (operation <= 0) throw BranchForkFailure("InvalidResponse")
            if (!current(ticket)) { gateway.cancel(operation); return@work }
            mutable.value = mutable.value.copy(operation = operation)
            if (cancelRequested) {
                gateway.cancel(operation)
                status = gateway.status(operation)
            } else if (status.phase == BranchForkPhase.REGISTERED) status = gateway.run(operation)
            var polls = 0
            while (status.phase in setOf(BranchForkPhase.REGISTERED, BranchForkPhase.RUNNING)) {
                if (status.operation != operation) throw BranchForkFailure("InvalidResponse")
                if (!current(ticket)) { gateway.cancel(operation); return@work }
                if (++polls > 200) throw BranchForkFailure("Pending")
                delay(25)
                status = gateway.status(operation)
            }
            if (!current(ticket)) { gateway.cancel(operation); return@work }
            if (status.operation != operation) throw BranchForkFailure("InvalidResponse")
            when (status.phase) {
                BranchForkPhase.COMPLETED -> {
                    val outcome = status.outcome ?: throw BranchForkFailure("InvalidResponse")
                    if (status.error != null || !matchesForkOutcome(outcome, saved.input)) throw BranchForkFailure("InvalidResponse")
                    mutable.value = mutable.value.copy(outcome = outcome.copy(scope = outcome.scope.copy(), parent = outcome.parent.copy()),
                        uncertain = false, notice = "Timeline fork confirmed. The original is preserved; select the child explicitly to resume it.")
                    // Metadata refresh failure cannot hide an already confirmed canonical outcome.
                    try { onResolved(outcome) }
                    catch (_: Exception) {
                        // Canonical success remains known even if metadata refresh is cancelled.
                        // A callback may synchronously change context before it throws.
                        if (current(ticket)) mutable.value = mutable.value.copy(notice = "Fork confirmed. Saved timeline metadata could not be refreshed.")
                    }
                }
                BranchForkPhase.REJECTED -> {
                    if (status.outcome != null || status.error == null) throw BranchForkFailure("InvalidResponse")
                    mutable.value = mutable.value.copy(notice = forkNotice(status.error))
                }
                else -> throw BranchForkFailure("InvalidResponse")
            }
        }
    }
    /** Same-incarnation retry only. Restored/context-changed identity is never executable. */
    fun retryExact(consent: Boolean) {
        val before = mutable.value
        val saved = recovery ?: return
        if (!consent || before.lookupOnly || origin != before.context || before.outcome != null || before.input != saved.input) return
        val rendered = before.input ?: return
        confirm(rendered, true)
    }
    fun lookup() {
        val saved = recovery ?: return
        if (disposed || active != null || recoveryControl) return
        // This explicit action labels the original input scope, never a new selection's scope.
        mutable.value = BranchForkUiState(context = mutable.value.context, visible = true,
            input = saved.input, lookupOnly = origin == null || origin != mutable.value.context, uncertain = true)
        work { ticket ->
            val result = gateway.lookup(saved.input)
            if (result.found != (result.outcome != null) || result.outcome?.let { !matchesForkOutcome(it, saved.input) || it.created } == true)
                throw BranchForkFailure("InvalidResponse")
            if (current(ticket)) mutable.value = mutable.value.copy(lookup = result, outcome = result.outcome,
                uncertain = !result.found, notice = if (result.found) "The original fork identity exists at the displayed current child head. Select it explicitly to resume."
                else "The fork identity was absent in this catalog snapshot. Lookup did not create it; absence is not a rollback promise.")
        }
    }
    fun forgetRecovery(consent: Boolean) {
        if (disposed || active != null || recoveryControl || !consent) return
        val before = mutable.value
        val clearGeneration = generation
        val clearOrigin = origin
        recoveryControl = true
        try { saveRecovery(null) } catch (_: Exception) {
            if (sameRecoveryOrigin(before, clearGeneration, clearOrigin))
                mutable.value = mutable.value.copy(notice = "The recovery identity could not be cleared.")
            return
        } finally { recoveryControl = false }
        // A successful clear removes the old identity, but cannot reset a new context.
        recovery = null
        val sameOrigin = sameRecoveryOrigin(before, clearGeneration, clearOrigin)
        origin = null
        if (sameOrigin) mutable.value = BranchForkUiState(context = before.context)
    }
    fun cancel() {
        if (disposed || !mutable.value.visible || mutable.value.outcome != null) return
        cancelRequested = true
        gateway.cancel(mutable.value.operation)
        // Keep this same-context worker alive to observe a committed late result.
        // Close/context switch still fence presentation and cancel its coroutine.
        mutable.value = mutable.value.copy(uncertain = true,
            notice = forkNotice("Cancelled"))
    }
    fun dismiss() {
        if (disposed) return
        ++generation
        gateway.cancel()
        active?.cancel()
        mutable.value = BranchForkUiState(context = mutable.value.context, busy = active != null)
        origin = null
    }
    fun dispose() {
        if (disposed) return
        disposed = true
        ++generation
        gateway.cancel()
        active?.cancel()
        gateway.close()
        origin = null
        mutable.value = BranchForkUiState()
    }
    // Synchronous injected persistence can reenter context/close controls before returning.
    // Reference equality also catches same-context presentation changes such as dismiss/cancel.
    private fun sameRecoveryOrigin(before: BranchForkUiState, ticket: Long, expectedOrigin: BranchForkContext?) =
        !disposed && generation == ticket && mutable.value === before && origin == expectedOrigin
    private fun current(ticket: Long) = !disposed && generation == ticket && mutable.value.visible
    private fun work(block: suspend (Long) -> Unit) {
        val ticket = ++generation
        mutable.value = mutable.value.copy(busy = true, notice = null, lookup = null)
        val job = scope.launch(start = CoroutineStart.LAZY) {
            try { block(ticket) }
            catch (cancelled: CancellationException) {
                if (current(ticket)) mutable.value = mutable.value.copy(notice = forkNotice("Cancelled"), uncertain = true)
                throw cancelled
            } catch (failure: Exception) {
                if (current(ticket)) mutable.value = mutable.value.copy(notice = forkNotice((failure as? BranchForkFailure)?.category), uncertain = true)
            }
        }
        active = job
        // Completion also runs when cancellation precedes the first dispatcher entry;
        // a coroutine-body finally alone cannot release that unentered worker slot.
        job.invokeOnCompletion {
            if (active === job) {
                active = null
                if (!disposed) mutable.value = mutable.value.copy(busy = false)
            }
        }
        job.start()
    }
}
private fun forkNotice(category: String?): String = when (category) {
    "Stale" -> "The parent changed. Keep this exact identity for lookup; prepare a new request only after explicit review."
    "Busy" -> "Local work is busy. Keep this exact fork identity; no automatic retry was started."
    "Full" -> "Local storage is full. Keep this exact identity for lookup or an explicit same-context retry."
    "Closed", "InvalidHandle" -> "The selected native owner is closed. Recovery is lookup-only after reopening."
    "Cancelled" -> "Cancellation was requested. The child may already exist from an earlier committed attempt; look up this exact identity."
    "Mismatch", "RetryMismatch" -> "The fixed child identity belongs to a different parent or fork point. Nothing was overwritten."
    "Rule", "InvalidForkInput" -> "Rust rejected the requested fork boundary or input. The original timeline is preserved."
    else -> "The fork outcome could not be confirmed. Keep this exact identity for lookup; do not assume the child is absent."
}

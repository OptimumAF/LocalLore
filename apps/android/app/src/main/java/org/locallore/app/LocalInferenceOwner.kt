/* Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0 */
package org.locallore.app

import java.nio.ByteBuffer
import java.nio.CharBuffer
import java.nio.charset.CodingErrorAction
import java.util.concurrent.ConcurrentHashMap
import java.util.concurrent.atomic.AtomicBoolean
import kotlinx.coroutines.CancellationException
import kotlinx.coroutines.CompletableDeferred
import kotlinx.coroutines.CoroutineDispatcher
import kotlinx.coroutines.CoroutineScope
import kotlinx.coroutines.Deferred
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.NonCancellable
import kotlinx.coroutines.SupervisorJob
import kotlinx.coroutines.TimeoutCancellationException
import kotlinx.coroutines.async
import kotlinx.coroutines.delay
import kotlinx.coroutines.launch
import kotlinx.coroutines.withContext
import kotlinx.coroutines.withTimeout

/** An adapter failure is uncertainty, never a domain Provider rejection that discards a turn key. */
internal class LocalInferenceUncertain : IllegalStateException("Local inference ownership uncertain")
internal class LocalInferenceBusy : IllegalStateException("Local inference busy")

internal data class LocalInferenceRequest(
    val version: Int, val role: String, val prompt: String, val maxTokens: Int,
    val contextTokens: Int, val threads: Int, val schemaJson: String,
) {
    fun validate() {
        check(version == 1 && role in setOf("director", "narrator", "author"))
        check(maxTokens in 1..(if(role=="author") 1024 else 350)) // Separate trusted role budgets.
        check(contextTokens in 512..4096 && threads == 4)
        val promptBytes = localUtf8(prompt).size
        val schemaBytes = localUtf8(schemaJson).size
        check(schemaBytes in 2..32_768 && promptBytes + schemaBytes <= 32_768)
    }
}
internal data class LocalInferencePending(val ticket: Long, val request: LocalInferenceRequest) {
    fun validate() { check(ticket > 0); request.validate() }
}
internal class LocalRoleResult(val terminal: Boolean, response: ByteArray) {
    private val value = response.copyOf()
    fun response(): ByteArray = value.copyOf()
}
internal fun interface LocalRoleWorker { suspend fun open(): LocalRoleEngine }
internal interface LocalRoleEngine {
    suspend fun start(request: LocalInferenceRequest): LocalRoleCall
    suspend fun close(): Boolean
}
internal interface LocalRoleCall {
    /** Known terminal cancellation returns terminal=true (response may be empty); throwing means unknown. */
    suspend fun await(): LocalRoleResult
    fun cancel()
    suspend fun drain(): Boolean
    suspend fun close(): Boolean
}
internal data class LocalInferenceLimits(val turnMs: Long = 60_000, val cleanupMs: Long = 5_000, val pollMs: Long = 10,
    val authorMs: Long = 120_000) {
    init { require(turnMs in 1..60_000 && cleanupMs in 1..5_000 && pollMs in 1..100 && authorMs in 1..120_000) }
}

/** One existing native workspace lease. Implementations make no gameplay decisions. */
internal interface LocalInferenceNativePort {
    fun call(input: ByteArray): ByteArray
    fun poll(): LocalInferencePending?
    /** False means the exact ticket was invalidated; every other protocol error throws. */
    fun respond(ticket: Long, response: ByteArray): Boolean
    fun close()
}

internal fun localUtf8(value: String): ByteArray {
    val buffer = Charsets.UTF_8.newEncoder().onMalformedInput(CodingErrorAction.REPORT)
        .onUnmappableCharacter(CodingErrorAction.REPORT).encode(CharBuffer.wrap(value))
    return ByteArray(buffer.remaining()).also { buffer.get(it) }
}
internal fun localText(bytes: ByteArray, cap: Int): String {
    check(bytes.size <= cap)
    return Charsets.UTF_8.newDecoder().onMalformedInput(CodingErrorAction.REPORT)
        .onUnmappableCharacter(CodingErrorAction.REPORT).decode(ByteBuffer.wrap(bytes)).toString()
}

/**
 * Owns a single opt-in lease and its local worker. No SDK, model path or alternate reducer lives here.
 * Independent tasks deliberately outlive a cancelled await: a timeout is never proof of release.
 */
internal class LocalInferenceOwner(
    profile: ByteArray,
    private val worker: LocalRoleWorker,
    dispatcher: CoroutineDispatcher = Dispatchers.IO,
    private val limits: LocalInferenceLimits = LocalInferenceLimits(),
) {
    private val profile = profile.copyOf().also { check(it.size in 1..4096); localText(it, 4096) }
    private val scope = CoroutineScope(SupervisorJob() + dispatcher)
    private val lock = Any()
    private var port: LocalInferenceNativePort? = null
    private var transport: Any? = null
    private var active: Run? = null
    private var authorResponseCapture: AuthorResponseCapture? = null
    private var invalidation: Deferred<Unit>? = null
    private val closed = AtomicBoolean()
    private val poisoned = AtomicBoolean()
    private val invalidated = AtomicBoolean()
    // Retain outstanding owners even after an observation timeout. Do not cancel their Job as proof.
    private val tasks = ConcurrentHashMap.newKeySet<Deferred<*>>()
    private val retainedUnknownOwners = ConcurrentHashMap.newKeySet<Any>()
    val quarantined: Boolean get() = poisoned.get()
    val nativeInvalidatedKnown: Boolean get() = invalidated.get()
    fun profileBytes(): ByteArray = profile.copyOf()
    /** Explicit fresh-owner diagnostic; ordinary construction neither installs nor allocates it. */
    fun installAuthorResponseCapture(): AuthorResponseCapture = synchronized(lock) {
        admit()
        check(authorResponseCapture == null && port == null && transport == null && active == null) {
            "Author response capture unavailable"
        }
        AuthorResponseCapture().also { authorResponseCapture = it }
    }
    /** Reserve before openLocal: sharing this driver across two transports must allocate no second lease. */
    fun claimTransport(value: Any) = synchronized(lock) {
        if (transport != null && transport !== value || transport == null && port != null)
            throw IllegalArgumentException("Local inference owner already attached")
        admit()
        transport = value
    }

    private inner class Engine(val value: LocalRoleEngine) {
        var close: Deferred<Boolean>? = null
    }
    private inner class Role(val value: LocalRoleCall) {
        var cancel: Deferred<Unit>? = null
        var drain: Deferred<Boolean>? = null
        var close: Deferred<Boolean>? = null
        var await: Deferred<LocalRoleResult>? = null
    }
    private inner class Run(val native: Deferred<ByteArray>, val cancelInput: ByteArray, val author: Boolean) {
        // Native cancellation acknowledgement alone does not release an active SDK owner.
        val finished = CompletableDeferred<Boolean>()
        var opening: Deferred<Engine>? = null
        var starting: Deferred<Role>? = null
        var engine: Engine? = null
        var role: Role? = null
        val abandoned = AtomicBoolean()
        val delivered = mutableSetOf<Long>()
    }
    private class NativeCancelled : Exception()

    private fun <T> task(block: suspend () -> T): Deferred<T> {
        val result = scope.async { block() }
        tasks.add(result)
        result.invokeOnCompletion { tasks.remove(result) }
        return result
    }
    private suspend fun <T> bounded(job: Deferred<T>): T = withTimeout(limits.cleanupMs) { job.await() }
    private fun bound(value: LocalInferenceNativePort) = synchronized(lock) {
        if (port != null && port !== value) throw LocalInferenceUncertain()
        if (port == null && transport != null) throw IllegalArgumentException("Local inference owner already attached")
        if (port == null) port = value
    }
    fun attach(value: LocalInferenceNativePort, transportToken: Any? = null) {
        synchronized(lock) {
            if (transport !== transportToken || port != null && port !== value)
                throw IllegalArgumentException("Local inference owner already attached")
            port = value
        }
        if (closed.get() || poisoned.get()) {
            scope.launch { quarantine(value) }
            throw LocalInferenceUncertain()
        }
    }
    fun assertBorrowable() = synchronized(lock) {
        admit()
        if (active != null) throw LocalInferenceBusy()
    }
    private fun admit() {
        if (closed.get() || poisoned.get()) throw LocalInferenceUncertain()
    }
    private fun invalidate(value: LocalInferenceNativePort): Deferred<Unit> = synchronized(lock) {
        invalidation ?: task { value.close(); invalidated.set(true) }.also { invalidation = it }
    }
    private suspend fun quarantine(value: LocalInferenceNativePort) {
        poisoned.set(true)
        try { bounded(invalidate(value)) } catch (_: Throwable) { /* Unknown remains quarantined. */ }
    }

    /** All commands, including commit, share this guard; no unsafe work follows an uncertain cleanup. */
    suspend fun execute(
        value: LocalInferenceNativePort, operation: String, input: ByteArray, cancelInput: ByteArray? = null,
    ): ByteArray {
        bound(value)
        val command = input.copyOf()
        try { localText(command, 24_576) } catch (_: Throwable) { throw IllegalArgumentException("Invalid local input") }
        if (operation !in setOf("prepare", "authoring_generate")) {
            val cancelling = synchronized(lock) {
                admit()
                if (operation !in setOf("cancel", "authoring_cancel", "authoring_status", "authoring_capabilities", "turn_status", "close", "workspace", "play_snapshot", "model_status", "capabilities") && active != null)
                    throw LocalInferenceBusy()
                if (operation == "cancel" || operation == "authoring_cancel") active else null
            }
            return try {
                // One unchanged deadline covers both native ACK and the captured run's cleanup.
                // Refreshing open/branches remains forbidden until that SDK ownership is settled.
                withTimeout(limits.cleanupMs) {
                    val reply = task { value.call(command).copyOf() }.await().also { localText(it, 262_144) }
                    if (cancelling != null) check(cancelling.finished.await())
                    if (operation == "cancel" || operation == "authoring_cancel") synchronized(lock) { admit() }
                    reply
                }
            } catch (_: Throwable) {
                withContext(NonCancellable) { quarantine(value) }
                throw LocalInferenceUncertain()
            }
        }
        val cancellation = cancelInput?.copyOf() ?: throw IllegalArgumentException("Invalid local input")
        try { localText(cancellation, 24_576) } catch (_: Throwable) { throw IllegalArgumentException("Invalid local input") }
        val run = synchronized(lock) {
            admit()
            if (active != null) throw LocalInferenceBusy()
            Run(task { value.call(command).copyOf().also { localText(it, 262_144) } }, cancellation,
                operation=="authoring_generate").also { active = it }
        }
        var reply: ByteArray? = null
        var failure: Throwable? = null
        var nativeCancelled = false
        try {
            reply = withTimeout(if(run.author) limits.authorMs else limits.turnMs) { pump(value, run) }
        } catch (_: NativeCancelled) { nativeCancelled = true }
        catch (problem: Throwable) { failure = problem }
        var cleaned = false
        withContext(NonCancellable) {
            try {
                // One total cleanup deadline, including invalidation and native join; never N steps × 5s.
                withTimeout(limits.cleanupMs) {
                    val uncertain = failure != null && failure !is CancellationException || failure is TimeoutCancellationException
                    if (uncertain) { poisoned.set(true); invalidate(value); retainedUnknownOwners.add(run) }
                    cleaned = finish(value, run, nativeCancelled || failure != null || closed.get())
                    if (cleaned && reply == null) {
                        try { reply = bounded(run.native) } catch (_: Throwable) { cleaned = false }
                    }
                    if (!cleaned || uncertain) { retainedUnknownOwners.add(run); quarantine(value) }
                }
            } catch (_: Throwable) {
                cleaned = false; poisoned.set(true); retainedUnknownOwners.add(run)
                // Schedule invalidation even when the shared deadline expired. Scheduled != proven.
                invalidate(value)
            }
        }
        synchronized(lock) { if (active === run) active = null }
        run.finished.complete(cleaned && !poisoned.get())
        if (poisoned.get() || !cleaned) throw LocalInferenceUncertain()
        if (failure is CancellationException || closed.get()) throw CancellationException("Local operation cancelled")
        if (failure != null) throw LocalInferenceUncertain()
        return checkNotNull(reply)
    }

    private suspend fun current(value: LocalInferenceNativePort, run: Run, pending: LocalInferencePending) {
        if (closed.get() || run.native.isCompleted) throw NativeCancelled()
        val observed = bounded(task { value.poll() })
        if (observed != pending) throw NativeCancelled()
    }
    private suspend fun <T> awaitCurrent(
        job: Deferred<T>, value: LocalInferenceNativePort, run: Run, pending: LocalInferencePending,
    ): T {
        while (!job.isCompleted) { current(value, run, pending); delay(limits.pollMs) }
        return job.await()
    }
    private suspend fun pump(value: LocalInferenceNativePort, run: Run): ByteArray {
        while (!run.native.isCompleted) {
            if (closed.get()) throw NativeCancelled()
            val pending = bounded(task { value.poll() })
            if (pending == null) { delay(limits.pollMs); continue }
            pending.validate()
            check(run.delivered.size < (if(run.author) 1 else 3))
            check((pending.request.role=="author")==run.author) // Author cannot borrow a play request or vice versa.
            check(pending.ticket !in run.delivered)
            val engine = run.engine ?: run.opening.let {
                val opening = it ?: task { Engine(worker.open()) }.also { run.opening = it }
                awaitCurrent(opening, value, run, pending).also { run.engine = it }
            }
            val starting = task { Role(engine.value.start(pending.request)) }.also { run.starting = it }
            val role = awaitCurrent(starting, value, run, pending).also { run.role = it }
            val waiting = task { role.value.await() }.also { role.await = it }
            val result = awaitCurrent(waiting, value, run, pending)
            check(result.terminal)
            val response = result.response().also { check(it.isNotEmpty()); localText(it, if(run.author) 8192 else 16_384) }
            check(releaseRole(role, cancel = false))
            current(value, run, pending)
            if (!bounded(task { value.respond(pending.ticket, response.copyOf()) })) throw NativeCancelled()
            check(run.delivered.add(pending.ticket))
            // Observe only the bytes acknowledged by the bridge. A fast native rejection is still
            // a submitted proposal; this does not establish native validation or canonical state.
            if (run.author && pending.request.role == "author") synchronized(lock) {
                if (active === run && !run.abandoned.get() && !closed.get() && !poisoned.get()) {
                    try { authorResponseCapture?.observe(pending.request.role, response) }
                    catch (_: Throwable) { /* Diagnostics cannot change response/resource authority. */ }
                }
            }
            run.role = null; run.starting = null
        }
        return run.native.await()
    }

    private suspend fun releaseRole(role: Role, cancel: Boolean): Boolean {
        var known = true
        // A native cancellation can race after a proven terminal/closed role. Never cancel that
        // already-closed SDK object merely because its native response ticket disappeared later.
        val terminal = role.await?.let {
            if (!it.isCompleted) false else try { it.await().terminal } catch (_: Throwable) { false }
        } == true
        if (cancel && !terminal) try {
            val job = synchronized(role) { role.cancel ?: task { role.value.cancel() }.also { role.cancel = it } }
            bounded(job)
        } catch (_: Throwable) { known = false }
        var drained = false
        try {
            val job = synchronized(role) { role.drain ?: task { role.value.drain() }.also { role.drain = it } }
            drained = bounded(job) == true
        } catch (_: Throwable) { known = false }
        if (!drained) return false // Never close a model under a still-active call.
        role.await?.let { try { known = bounded(it).terminal && known } catch (_: Throwable) { known = false } }
        try {
            val job = synchronized(role) { role.close ?: task { role.value.close() }.also { role.close = it } }
            known = (bounded(job) == true) && known
        } catch (_: Throwable) { known = false }
        return known
    }
    private suspend fun releaseEngine(engine: Engine): Boolean = try {
        val job = synchronized(engine) { engine.close ?: task { engine.value.close() }.also { engine.close = it } }
        bounded(job) == true
    } catch (_: Throwable) { false }

    private suspend fun finish(value: LocalInferenceNativePort, run: Run, cancel: Boolean): Boolean {
        run.abandoned.set(true)
        var known = true
        if (cancel) try { bounded(task { value.call(run.cancelInput.copyOf()) }).also { localText(it, 262_144) } }
        catch (_: Throwable) { known = false }
        var engine = run.engine
        var role = run.role
        if (engine == null) run.opening?.let { opening ->
            if (opening.isCompleted) try { engine = opening.await() } catch (_: Throwable) { known = false }
            else {
                known = false
                opening.invokeOnCompletion { task { try { releaseEngine(opening.await()) } catch (_: Throwable) { } } }
            }
        }
        if (role == null) run.starting?.let { starting ->
            if (starting.isCompleted) try { role = starting.await() } catch (_: Throwable) { known = false }
            else {
                known = false
                starting.invokeOnCompletion { task {
                    try {
                        withTimeout(limits.cleanupMs) {
                            val released = releaseRole(starting.await(), true)
                            if (released) engine?.let { releaseEngine(it) }
                        }
                    } catch (_: Throwable) { /* Unreturned/undrained child retains its parent. */ }
                } }
            }
        }
        var roleKnown = true
        role?.let { roleKnown = releaseRole(it, cancel); known = roleKnown && known }
        // A throwing/unreturned start can have allocated a child. Keep its parent owned, never guess.
        val startKnown = run.starting == null || role != null
        if (roleKnown && startKnown && run.starting?.isCompleted != false) engine?.let { known = releaseEngine(it) && known }
        try { bounded(run.native) } catch (_: Throwable) { known = false }
        return known
    }

    /** Main-thread disposal schedules owned teardown and returns without loading or joining anything. */
    fun close() {
        if (!closed.compareAndSet(false, true)) return
        val value = synchronized(lock) { port } ?: return
        scope.launch {
            try { bounded(invalidate(value)) } catch (_: Throwable) { poisoned.set(true) }
        }
    }
}

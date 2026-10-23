/* Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0 */
package org.locallore.app

import java.nio.ByteBuffer
import java.nio.charset.CodingErrorAction
import java.util.concurrent.atomic.AtomicBoolean
import java.util.concurrent.atomic.AtomicLong
import java.util.concurrent.atomic.AtomicReference
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.NonCancellable
import kotlinx.coroutines.withContext
import org.json.JSONObject
import org.json.JSONTokener

/** Existing workspace handles only. No new path, Store or separate workspace open. */
internal object NativeFork {
    init { System.loadLibrary("locallore_android") }
    external fun register(handle: Long, input: ByteArray, consent: Boolean): ByteArray
    external fun run(handle: Long, operation: Long): ByteArray
    external fun status(handle: Long, operation: Long): ByteArray
    external fun cancel(handle: Long, operation: Long): ByteArray
    external fun lookup(handle: Long, input: ByteArray): ByteArray
}
/** Root supplies its existing NativeWorkspaceTransport handle allocator; this class opens nothing. */
internal class NativeForkGateway(private val workspaceHandle: suspend () -> Long) : BranchForkGateway {
    private data class Binding(val owner: Long, val operation: Long, val input: BranchForkInput)
    private val binding = AtomicReference<Binding?>()
    private val epoch = AtomicLong()
    private val closed = AtomicBoolean()
    override suspend fun register(context: BranchForkContext, input: BranchForkInput, consent: Boolean): BranchForkStatus {
        if (!validForkInput(input) || context.parent != input.parent || context.head != input.expectedParentRevision)
            throw BranchForkFailure("InvalidForkInput")
        val captured = epoch.get()
        return withContext(NonCancellable + Dispatchers.IO) {
            if (closed.get() || epoch.get() != captured) throw BranchForkFailure("Cancelled")
            val owner = workspaceHandle().also { if (it <= 0) throw BranchForkFailure("InvalidHandle") }
            if (closed.get() || epoch.get() != captured) throw BranchForkFailure("Cancelled")
            val request = JSONObject().put("version", 1).put("session", context.session)
                .put("input", ForkNativeWire.input(input)).toString().toByteArray(Charsets.UTF_8)
            if (request.size > 4096) throw BranchForkFailure("TooLarge")
            val status = ForkNativeWire.status(NativeFork.register(owner, request, consent), input)
            val recorded = Binding(owner, status.operation, input)
            binding.set(recorded)
            if (closed.get() || epoch.get() != captured) {
                try { NativeFork.cancel(owner, status.operation) } catch (_: Exception) { }
                throw BranchForkFailure("Cancelled")
            }
            status
        }
    }
    private suspend fun nativeOperation(id: Long, run: Boolean): BranchForkStatus = withContext(Dispatchers.IO) {
        val captured = binding.get()?.takeIf { it.operation == id } ?: throw BranchForkFailure("InvalidToken")
        if (closed.get()) throw BranchForkFailure("InvalidHandle")
        ForkNativeWire.status(if (run) NativeFork.run(captured.owner, id) else NativeFork.status(captured.owner, id), captured.input)
            .also { if (it.operation != id) throw BranchForkFailure("InvalidResponse") }
    }
    override suspend fun run(operation: Long) = nativeOperation(operation, true)
    override suspend fun status(operation: Long) = nativeOperation(operation, false)
    override suspend fun lookup(input: BranchForkInput): BranchForkLookup {
        if (!validForkInput(input)) throw BranchForkFailure("InvalidForkInput")
        val captured = epoch.get()
        return withContext(Dispatchers.IO) {
            if (closed.get()) throw BranchForkFailure("InvalidHandle")
            val owner = workspaceHandle().also { if (it <= 0) throw BranchForkFailure("InvalidHandle") }
            if (closed.get() || captured != epoch.get()) throw BranchForkFailure("Cancelled")
            val result = ForkNativeWire.lookup(NativeFork.lookup(owner,
                ForkNativeWire.input(input).toString().toByteArray(Charsets.UTF_8)), input)
            if (closed.get() || captured != epoch.get()) throw BranchForkFailure("Cancelled")
            result
        }
    }
    override fun cancel(operation: Long?) {
        val captured = binding.get()
        // A stale acknowledgement may only cancel its own known operation.
        if (operation != null && captured?.operation != operation) return
        epoch.incrementAndGet()
        if (captured != null) try { NativeFork.cancel(captured.owner, captured.operation) } catch (_: Exception) { }
    }
    override fun close() {
        if (!closed.compareAndSet(false, true)) return
        cancel(null)
        binding.set(null)
        // Root still owns NativeWorkspace.close; its Rust close retires before drain.
    }
}
internal object ForkNativeWire {
    fun input(value: BranchForkInput): JSONObject {
        require(validForkInput(value))
        return JSONObject().put("parent", JSONObject().put("story", value.parent.story).put("branch", value.parent.branch))
            .put("child_branch", value.childBranch).put("expected_parent_revision", value.expectedParentRevision)
            .put("at_revision", value.atRevision)
    }
    fun recovery(value: BranchForkRecovery): ByteArray {
        require(value.version == 1)
        return JSONObject().put("version", 1).put("input", input(value.input)).toString().toByteArray(Charsets.UTF_8)
            .also { require(it.size <= 4096) }
    }
    fun recovery(bytes: ByteArray): BranchForkRecovery = guarded {
        val value = objectBytes(bytes)
        value.exact("version", "input")
        require(value.integer("version") == 1L)
        BranchForkRecovery(1, parseInput(value.getJSONObject("input")))
    }
    private fun parseInput(value: JSONObject): BranchForkInput {
        value.exact("parent", "child_branch", "expected_parent_revision", "at_revision")
        return BranchForkInput(value.scope("parent"), value.identifier("child_branch"),
            value.integer("expected_parent_revision"), value.integer("at_revision"))
            .also { require(validForkInput(it)) }
    }
    fun status(bytes: ByteArray, input: BranchForkInput): BranchForkStatus = decoded(bytes) { value ->
        value.exact("operation", "phase", "cancel_requested", "result", "error")
        val operation = value.integer("operation", Long.MAX_VALUE).also { require(it > 0) }
        val cancelled = value.boolean("cancel_requested")
        val phase = when (value.get("phase") as? String) {
            "registered" -> BranchForkPhase.REGISTERED
            "running" -> BranchForkPhase.RUNNING
            "completed" -> BranchForkPhase.COMPLETED
            "rejected" -> BranchForkPhase.REJECTED
            else -> error("Invalid phase")
        }
        val outcome = if (phase == BranchForkPhase.COMPLETED) {
            require(value.isNull("error"))
            val result = value.getJSONObject("result").also { it.exact("kind", "outcome"); require(it.get("kind") == "fork") }
            outcome(result.getJSONObject("outcome"), input)
        } else { require(value.isNull("result")); null }
        val error = if (phase == BranchForkPhase.REJECTED) value.error("error")
            else { require(value.isNull("error")); null }
        BranchForkStatus(operation, phase, cancelled, outcome, error)
    }
    fun lookup(bytes: ByteArray, input: BranchForkInput): BranchForkLookup = decoded(bytes) { value ->
        value.exact("version", "kind", "found", "outcome")
        require(value.integer("version") == 1L && value.get("kind") == "fork_lookup")
        val found = value.boolean("found")
        val outcome = if (found) outcome(value.getJSONObject("outcome"), input).also { require(!it.created) }
            else { require(value.isNull("outcome")); null }
        BranchForkLookup(found, outcome)
    }
    private fun outcome(value: JSONObject, input: BranchForkInput): BranchForkOutcome {
        value.exact("version", "scope", "parent", "fork_revision", "head_revision", "created")
        return BranchForkOutcome(value.integer("version").also { require(it == 1L) }.toInt(), value.scope("scope"), value.scope("parent"),
            value.integer("fork_revision"), value.integer("head_revision"), value.boolean("created"))
            .also { require(matchesForkOutcome(it, input)) }
    }
    private fun <T> decoded(bytes: ByteArray, block: (JSONObject) -> T): T = guarded {
        val value = objectBytes(bytes)
        require(value.integer("version") == 1L)
        when (value.get("status") as? String) {
            "ok" -> { value.exact("version", "status", "data"); block(value.getJSONObject("data")) }
            "rejected" -> { value.exact("version", "status", "error"); throw BranchForkFailure(value.error("error")) }
            else -> error("Invalid envelope")
        }
    }
    private fun objectBytes(bytes: ByteArray): JSONObject {
        require(bytes.size in 1..4096)
        val text = Charsets.UTF_8.newDecoder().onMalformedInput(CodingErrorAction.REPORT)
            .onUnmappableCharacter(CodingErrorAction.REPORT).decode(ByteBuffer.wrap(bytes)).toString()
        val parser = JSONTokener(text)
        val value = parser.nextValue() as? JSONObject ?: error("Object required")
        require(parser.nextClean() == '\u0000')
        // This closed control format contains ASCII IDs/fixed labels and integers,
        // never prose. A canonical round trip rejects duplicate keys and lenient
        // JSONTokener extensions instead of silently adopting their last value.
        val compact = StringBuilder()
        var quoted = false
        var escaped = false
        for (char in text) {
            if (quoted) {
                compact.append(char)
                if (escaped) escaped = false
                else if (char == '\\') escaped = true
                else if (char == '"') quoted = false
            } else if (char == '"') { quoted = true; compact.append(char) }
            else if (char !in charArrayOf(' ', '\t', '\r', '\n')) compact.append(char)
        }
        require(!quoted && compact.toString() == value.toString())
        return value
    }
    private fun JSONObject.exact(vararg keys: String) { require(length() == keys.size && this.keys().asSequence().toSet() == keys.toSet()) }
    private fun JSONObject.integer(key: String, max: Long = FORK_MAX_REVISION): Long {
        val value = get(key)
        require(value is Int || value is Long)
        return (value as Number).toLong().also { require(it in 0..max) }
    }
    private fun JSONObject.boolean(key: String) = (get(key) as? Boolean) ?: error("Boolean required")
    private fun JSONObject.identifier(key: String) = (get(key) as? String)?.also { require(it.matches(Regex("[A-Za-z0-9_-]{1,64}"))) }
        ?: error("Identifier required")
    private fun JSONObject.scope(key: String): ForkScope {
        val value = getJSONObject(key).also { it.exact("story", "branch") }
        return ForkScope(value.identifier("story"), value.identifier("branch"))
    }
    private fun JSONObject.error(key: String) = (get(key) as? String)?.also { require(it in FORK_ERRORS) }
        ?: error("Error required")
    private fun <T> guarded(block: () -> T): T = try { block() }
        catch (failure: BranchForkFailure) { throw failure }
        catch (_: Exception) { throw BranchForkFailure("InvalidResponse") }
}
private val FORK_ERRORS = setOf("InvalidForkInput", "ForkConsentRequired", "InvalidHandle", "InvalidToken", "Busy",
    "Closed", "Scope", "Stale", "Cancelled", "Mismatch", "RetryMismatch", "Rule", "NotFound", "UnknownStory",
    "Malformed", "Version", "Unsupported", "TooLarge", "Integrity", "Database", "Full", "WorkspaceLimit", "Internal")

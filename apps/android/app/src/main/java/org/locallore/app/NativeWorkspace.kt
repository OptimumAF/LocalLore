/* Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0 */
package org.locallore.app

import android.content.Context
import android.os.Looper
import kotlinx.coroutines.CoroutineScope
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.SupervisorJob
import kotlinx.coroutines.cancel
import kotlinx.coroutines.launch
import kotlinx.coroutines.withContext
import org.json.JSONObject
import org.json.JSONTokener
import java.io.File
import java.util.concurrent.atomic.AtomicBoolean

/** Dedicated bounded JNI API; no Java references or paths occur in the Host wire protocol. */
internal object NativeWorkspace {
    init { System.loadLibrary("locallore_android") }
    external fun open(path: String): Long
    external fun openLocal(path: String, profile: ByteArray?): Long
    external fun call(handle: Long, input: ByteArray?): ByteArray
    external fun pollInference(handle: Long): ByteArray
    external fun respondInference(handle: Long, ticket: Long, response: ByteArray?): ByteArray
    external fun close(handle: Long)
}

internal class NativeWorkspaceTransport(
    context: Context, private val localInference: LocalInferenceOwner? = null,
    private val operationObserver: ((String) -> Unit)? = null,
) : WorkspaceTransport {
    init { localInference?.claimTransport(this) }
    private val app = context.applicationContext
    private val lifecycle = CoroutineScope(SupervisorJob() + Dispatchers.IO)
    private val closed = AtomicBoolean(false)
    // Initialized on IO. This lock protects only allocation/teardown, never prepare or canon.
    private val handles = Any()
    private var handle = 0L
    private var localPort: LocalInferenceNativePort? = null
    private fun worker() { check(Looper.myLooper() != Looper.getMainLooper()) }
    /** The fork adapter borrows this SAME owner; allocation and teardown remain here. */
    internal suspend fun forkHandle(): Long = withContext(Dispatchers.IO) {
        worker()
        localInference?.assertBorrowable()
        allocateOnWorker().also { localInference?.assertBorrowable() }
    }
    private fun allocateOnWorker(): Long {
        worker()
        return synchronized(handles) {
            check(!closed.get())
            if (handle == 0L) {
                localInference?.assertBorrowable()
                val directory = File(app.noBackupFilesDir, "workspace-v1")
                check(directory.isDirectory || directory.mkdirs())
                val path = File(directory, "stories.sqlite3").absolutePath
                handle = if (localInference == null) NativeWorkspace.open(path)
                    else NativeWorkspace.openLocal(path, localInference.profileBytes())
                check(handle != 0L) { "Storage unavailable" }
                if (localInference != null) {
                    val port = NativeLocalInferencePort(handle)
                    localPort = port
                    localInference.attach(port, this)
                }
            }
            handle
        }
    }
    override suspend fun exchange(command: JSONObject): JSONObject = withContext(Dispatchers.IO) {
        worker()
        operationObserver?.invoke(command.optString("op", ""))
        val id = allocateOnWorker()
        val envelope = JSONObject().put("version", 1).put("command", command).toString()
        val bytes = if (localInference == null) envelope.toByteArray(Charsets.UTF_8) else localUtf8(envelope)
        require(bytes.size <= 24_576)
        val reply = if (localInference == null) NativeWorkspace.call(id, bytes) else {
            val operation = command.getString("op")
            val cancel = when(operation) {
                "prepare" -> JSONObject(command.toString()).put("op", "cancel")
                "authoring_generate" -> JSONObject().put("op","authoring_cancel").put("job",command.get("job"))
                else -> null
            }
            localInference.execute(checkNotNull(localPort), operation, bytes, cancel?.let {
                JSONObject().put("version", 1).put("command", it).toString().let(::localUtf8)
            })
        }
        check(reply.size <= 262_144)
        JSONObject(if (localInference == null) reply.toString(Charsets.UTF_8) else localText(reply, 262_144))
            .also { check(it.getInt("version") == 1) }
    }
    override fun close() {
        if (!closed.compareAndSet(false, true)) return
        if (localInference != null) { localInference.close(); return }
        // onCleared cannot suspend and its ViewModel scope has been cancelled. The adapter owns this
        // bounded cleanup worker; it closes only its handle and never removes the database.
        lifecycle.launch {
            worker()
            val id = synchronized(handles) { handle.also { handle = 0L } }
            if (id != 0L) NativeWorkspace.close(id)
            lifecycle.cancel()
        }
    }
}

/** Platform JSON is confined to the production port; the lifecycle owner is plain JVM Kotlin. */
private class NativeLocalInferencePort(private val handle: Long) : LocalInferenceNativePort {
    override fun call(input: ByteArray): ByteArray = NativeWorkspace.call(handle, input.copyOf())
    override fun close() = NativeWorkspace.close(handle)
    private fun objectReply(raw: ByteArray, cap: Int): JSONObject {
        val tokener = JSONTokener(localText(raw, cap))
        val result = tokener.nextValue() as? JSONObject ?: throw LocalInferenceUncertain()
        check(tokener.nextClean() == '\u0000')
        check(integer(result, "version") == 1)
        return result
    }
    private fun keys(value: JSONObject) = value.keys().asSequence().toSet()
    private fun integer(value: JSONObject, key: String): Int {
        val number = value.get(key)
        check(number is Int || number is Long)
        val long = (number as Number).toLong()
        check(long in Int.MIN_VALUE.toLong()..Int.MAX_VALUE.toLong())
        return long.toInt()
    }
    override fun poll(): LocalInferencePending? {
        val root = objectReply(NativeWorkspace.pollInference(handle), 40_000)
        check(keys(root) == setOf("version", "status", "data") && root.get("status") == "ok")
        val data = root.getJSONObject("data")
        check(keys(data) == setOf("pending"))
        if (data.get("pending") === JSONObject.NULL) return null
        val pending = data.getJSONObject("pending")
        check(keys(pending) == setOf("ticket", "request"))
        val ticket = pending.get("ticket")
        check(ticket is Int || ticket is Long)
        val request = pending.getJSONObject("request")
        check(keys(request) == setOf("version", "role", "prompt", "max_tokens", "context_tokens", "threads", "schema"))
        check(localUtf8(request.toString()).size <= 32_768)
        val role = request.get("role") as? String ?: throw LocalInferenceUncertain()
        val prompt = request.get("prompt") as? String ?: throw LocalInferenceUncertain()
        val schema = request.get("schema") as? JSONObject ?: throw LocalInferenceUncertain()
        return LocalInferencePending((ticket as Number).toLong(), LocalInferenceRequest(
            integer(request, "version"), role, prompt, integer(request, "max_tokens"),
            integer(request, "context_tokens"), integer(request, "threads"), schema.toString(),
        )).also { it.validate() }
    }
    override fun respond(ticket: Long, response: ByteArray): Boolean {
        localText(response, 16_384)
        val root = objectReply(NativeWorkspace.respondInference(handle, ticket, response.copyOf()), 40_000)
        if (keys(root) == setOf("version", "status", "error") && root.get("status") == "rejected" &&
            root.get("error") == "InvalidTicket") return false
        check(keys(root) == setOf("version", "status", "data") && root.get("status") == "ok")
        val data = root.getJSONObject("data")
        check(keys(data) == setOf("accepted") && data.get("accepted") == true)
        return true
    }
}

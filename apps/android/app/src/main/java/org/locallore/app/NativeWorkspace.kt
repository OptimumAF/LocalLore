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
import java.io.File
import java.util.concurrent.atomic.AtomicBoolean

/** Dedicated bounded JNI API; no Java references or paths occur in the Host wire protocol. */
internal object NativeWorkspace {
    init { System.loadLibrary("locallore_android") }
    external fun open(path: String): Long
    external fun call(handle: Long, input: ByteArray?): ByteArray
    external fun close(handle: Long)
}

internal class NativeWorkspaceTransport(context: Context) : WorkspaceTransport {
    private val app = context.applicationContext
    private val lifecycle = CoroutineScope(SupervisorJob() + Dispatchers.IO)
    private val closed = AtomicBoolean(false)
    // Initialized on IO. This lock protects only allocation/teardown, never prepare or canon.
    private val handles = Any()
    private var handle = 0L
    private fun worker() { check(Looper.myLooper() != Looper.getMainLooper()) }
    /** The fork adapter borrows this SAME owner; allocation and teardown remain here. */
    internal suspend fun forkHandle(): Long = withContext(Dispatchers.IO) {
        worker()
        allocateOnWorker()
    }
    private fun allocateOnWorker(): Long {
        worker()
        return synchronized(handles) {
            check(!closed.get())
            if (handle == 0L) {
                val directory = File(app.noBackupFilesDir, "workspace-v1")
                check(directory.isDirectory || directory.mkdirs())
                handle = NativeWorkspace.open(File(directory, "stories.sqlite3").absolutePath)
                check(handle != 0L) { "Storage unavailable" }
            }
            handle
        }
    }
    override suspend fun exchange(command: JSONObject): JSONObject = withContext(Dispatchers.IO) {
        worker()
        val id = allocateOnWorker()
        val bytes = JSONObject().put("version", 1).put("command", command).toString().toByteArray(Charsets.UTF_8)
        require(bytes.size <= 24_576)
        val reply = NativeWorkspace.call(id, bytes)
        check(reply.size <= 262_144)
        JSONObject(reply.toString(Charsets.UTF_8)).also { check(it.getInt("version") == 1) }
    }
    override fun close() {
        if (!closed.compareAndSet(false, true)) return
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

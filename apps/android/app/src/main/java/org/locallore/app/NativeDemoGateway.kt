/* Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0 */
package org.locallore.app

import android.os.Looper
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.withContext
import org.json.JSONArray
import org.json.JSONObject
import java.util.UUID

/** The only JNI entry point copies bounded UTF-8 JSON arrays. Handles are IDs, never pointers. */
internal object NativeBridge {
    init { System.loadLibrary("locallore_android") }
    external fun call(handle: Long, input: ByteArray?): ByteArray

    fun exchange(handle: Long, control: JSONObject): JSONObject {
        val bytes = control.toString().toByteArray(Charsets.UTF_8)
        require(bytes.size <= 24_576)
        val reply = call(handle, bytes)
        check(reply.size <= 65_536)
        return JSONObject(reply.toString(Charsets.UTF_8)).also { check(it.getInt("version") == 1) }
    }
    fun control(op: String): JSONObject = JSONObject().put("version", 1).put("op", op)
}

/** Main-thread owner; a Kotlin IO worker prepares a draft, Rust alone validates and commits canon. */
internal class NativeDemoGateway : DemoGateway {
    private var session = create()
    private var operation = 0L

    private fun owner() { check(Looper.myLooper() == Looper.getMainLooper()) }
    private fun create(): Long {
        owner()
        return NativeBridge.exchange(0, NativeBridge.control("create")).getLong("handle")
    }

    override suspend fun respond(action: DemoAction, revision: Long, mode: DemoMode): DemoResult {
        owner()
        check(session != 0L)
        val captured = session
        val command = when (action) {
            DemoAction.GIVE_POTION -> JSONObject().put("op", "give").put("item", "potion")
                .put("to", "mira").put("quantity", 1)
            DemoAction.TRY_ABILITY -> JSONObject().put("op", "use_ability").put("ability", "blink")
        }
        val request = JSONObject().put("version", 1)
            .put("scope", JSONObject().put("story", "quay").put("branch", "main"))
            .put("turn", UUID.randomUUID().toString()).put("expected_revision", revision)
            .put("intent", JSONObject().put("kind", "actions").put("value", JSONArray().put(command)))
        val begin = NativeBridge.exchange(captured, NativeBridge.control("begin")
            .put("request", request).put("mode", mode.name.lowercase(java.util.Locale.ROOT)))
        if (begin.getString("status") != "started") return rejected(begin)
        val started = begin.getLong("operation")
        operation = started
        var delivered = false
        try {
            val prepared = withContext(Dispatchers.IO) {
                NativeBridge.exchange(captured, NativeBridge.control("run").put("operation", started))
            }
            delivered = true
            return if (prepared.getString("status") == "prepared") DemoResult.Prepared(captured, started)
            else rejected(prepared)
        } finally {
            // withContext may discard a completed draft when its continuation is cancelled.
            if (!delivered) NativeBridge.exchange(captured, NativeBridge.control("cancel").put("operation", started))
        }
    }

    override fun commit(result: DemoResult): DemoResult {
        owner()
        if (result !is DemoResult.Prepared) return result
        if (result.session != session || result.operation != operation) return DemoResult.Rejected("Cancelled")
        val reply = NativeBridge.exchange(session, NativeBridge.control("commit").put("operation", operation))
        if (reply.getString("status") != "accepted") return rejected(reply)
        val state = reply.getJSONObject("snapshot")
        return DemoResult.Accepted(state.getLong("revision"), state.getString("potion_owner"), reply.getString("narration"))
    }

    override fun cancel() {
        owner()
        if (session != 0L && operation != 0L) {
            NativeBridge.exchange(session, NativeBridge.control("cancel").put("operation", operation))
        }
        operation = 0L
    }
    override fun reset() { owner(); close(); session = create() }
    override fun close() {
        owner()
        val previous = session
        if (previous == 0L) return
        session = 0L
        operation = 0L
        NativeBridge.exchange(previous, NativeBridge.control("destroy"))
    }
    private fun rejected(reply: JSONObject) = DemoResult.Rejected(reply.optString("error", "Provider"))
}

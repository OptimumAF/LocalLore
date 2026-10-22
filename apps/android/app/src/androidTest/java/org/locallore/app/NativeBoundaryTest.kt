/* Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0 */
package org.locallore.app

import android.os.SystemClock
import androidx.test.ext.junit.runners.AndroidJUnit4
import androidx.test.platform.app.InstrumentationRegistry
import org.json.JSONArray
import org.json.JSONObject
import org.junit.Assert.*
import org.junit.Test
import org.junit.runner.RunWith
import java.util.concurrent.Executors
import java.util.concurrent.TimeUnit

@RunWith(AndroidJUnit4::class)
class NativeBoundaryTest {
    private fun call(h: Long, op: String, id: Long? = null): JSONObject = NativeBridge.exchange(h,
        NativeBridge.control(op).also { if (id != null) it.put("operation", id) })
    private fun create() = call(0, "create").getLong("handle")
    private fun stats() = call(0, "stats")
    private fun request(turn: String, revision: Long = 0, command: JSONObject = JSONObject()
        .put("op", "give").put("item", "potion").put("to", "mira").put("quantity", 1)): JSONObject =
        JSONObject().put("version", 1).put("scope", JSONObject().put("story", "quay").put("branch", "main"))
            .put("turn", turn).put("expected_revision", revision)
            .put("intent", JSONObject().put("kind", "actions").put("value", JSONArray().put(command)))
    private fun begin(h: Long, turn: String, mode: String = "accepted", revision: Long = 0,
        command: JSONObject? = null): Long = NativeBridge.exchange(h, NativeBridge.control("begin")
        .put("mode", mode).put("request", if (command == null) request(turn, revision) else request(turn, revision, command)))
        .getLong("operation")
    private fun run(h: Long, op: Long): JSONObject {
        val executor = Executors.newSingleThreadExecutor()
        try { return executor.submit<JSONObject> { call(h, "run", op) }.get(8, TimeUnit.SECONDS) }
        finally { executor.shutdownNow() }
    }
    private fun waitFor(predicate: () -> Boolean) {
        val deadline = SystemClock.elapsedRealtime() + 3_000
        while (!predicate()) { check(SystemClock.elapsedRealtime() < deadline); SystemClock.sleep(5) }
    }

    @Test fun actualEnginePreparesWithoutCommitAndIdempotentlyOwnsEventsAndResources() {
        val h = create()
        try {
            val op = begin(h, "native-gift")
            assertEquals("WrongThread", call(h, "run", op).getString("error"))
            assertEquals("prepared", run(h, op).getString("status"))
            assertEquals(0L, call(h, "snapshot").getJSONObject("snapshot").getLong("revision"))
            val accepted = call(h, "commit", op)
            assertEquals("accepted", accepted.getString("status"))
            val state = accepted.getJSONObject("snapshot")
            assertEquals("Mira", state.getString("potion_owner"))
            assertEquals(1, state.getInt("events"))
            assertEquals(1, state.getInt("mira_observations"))
            assertEquals(0, state.getInt("sable_observations"))
            assertEquals(accepted.toString(), call(h, "commit", op).toString())
            assertEquals("already_committed", call(h, "cancel", op).getString("status"))
            val ability = JSONObject().put("op", "use_ability").put("ability", "steady")
            val use = begin(h, "native-resource", revision = 1, command = ability)
            assertEquals("prepared", run(h, use).getString("status"))
            assertEquals(0, call(h, "commit", use).getJSONObject("snapshot").getInt("energy"))
            val reuse = begin(h, "native-exhausted", revision = 2, command = ability)
            assertEquals("Resource", run(h, reuse).getString("error"))
            assertEquals(2L, call(h, "snapshot").getJSONObject("snapshot").getLong("revision"))
        } finally { call(h, "destroy") }
    }

    @Test fun nullOversizedMalformedForeignAndDestroyedInputsFailClosedThroughJni() {
        fun raw(h: Long, bytes: ByteArray?) = JSONObject(NativeBridge.call(h, bytes).toString(Charsets.UTF_8))
        assertEquals("Malformed", raw(0, null).getString("error"))
        assertEquals("TooLarge", raw(0, ByteArray(24_577)).getString("error"))
        assertEquals("Malformed", raw(0, byteArrayOf(0xc3.toByte(), 0x28)).getString("error"))
        assertEquals("Version", NativeBridge.exchange(0, NativeBridge.control("create").put("version", 2)).getString("error"))
        assertEquals("Malformed", NativeBridge.exchange(0, NativeBridge.control("create").put("extra", true)).getString("error"))
        val h = create()
        try {
            val foreign = request("foreign").also { it.getJSONObject("scope").put("branch", "other") }
            val reply = NativeBridge.exchange(h, NativeBridge.control("begin").put("mode", "accepted").put("request", foreign))
            assertEquals("Scope", reply.getString("error"))
            var wrongThread = ""
            InstrumentationRegistry.getInstrumentation().runOnMainSync { wrongThread = call(h, "snapshot").getString("error") }
            assertEquals("WrongThread", wrongThread)
        } finally { call(h, "destroy") }
        assertEquals("InvalidHandle", call(h, "snapshot").getString("error"))
        assertEquals("InvalidHandle", call(h, "destroy").getString("error"))
    }

    @Test fun cancelBeforeRunAndAfterPrepareNeverCommits() {
        val h = create()
        try {
            val first = begin(h, "cancel-before")
            call(h, "cancel", first)
            assertEquals("InvalidOperation", run(h, first).getString("error"))
            assertEquals("Cancelled", call(h, "commit", first).getString("error"))
            val second = begin(h, "cancel-ready")
            assertEquals("prepared", run(h, second).getString("status"))
            call(h, "cancel", second)
            assertEquals("Cancelled", call(h, "commit", second).getString("error"))
            assertEquals(0, call(h, "snapshot").getJSONObject("snapshot").getInt("events"))
        } finally { call(h, "destroy") }
    }

    @Test fun twentyCancelDestroyCyclesReleaseRetainedSessionsWorkersAndOperations() {
        val baseline = stats()
        val executor = Executors.newSingleThreadExecutor()
        try {
            repeat(20) { iteration ->
                val h = create()
                val op = begin(h, "destroy-$iteration", "delayed")
                val task = executor.submit<JSONObject> { call(h, "run", op) }
                waitFor { stats().getInt("workers") > baseline.getInt("workers") }
                // Control path is usable while generation is pending; it never holds the engine lock.
                assertEquals(0, call(h, "snapshot").getJSONObject("snapshot").getInt("events"))
                if (iteration % 2 == 0) call(h, "cancel", op)
                assertEquals("closed", call(h, "destroy").getString("status"))
                assertEquals("Cancelled", task.get(3, TimeUnit.SECONDS).getString("error"))
                assertEquals("InvalidHandle", call(h, "commit", op).getString("error"))
                waitFor { val now = stats(); listOf("retained_sessions", "operations", "workers", "live_sessions")
                    .all { now.getInt(it) == baseline.getInt(it) } }
                val fresh = create()
                assertNotEquals(h, fresh)
                assertEquals(0, call(fresh, "snapshot").getJSONObject("snapshot").getInt("events"))
                call(fresh, "destroy")
            }
        } finally { executor.shutdownNow() }
    }
}

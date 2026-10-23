/* Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0 */
package org.locallore.app

import android.content.Context
import android.content.ContextWrapper
import androidx.test.ext.junit.runners.AndroidJUnit4
import androidx.test.platform.app.InstrumentationRegistry
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.async
import kotlinx.coroutines.delay
import kotlinx.coroutines.runBlocking
import kotlinx.coroutines.withContext
import kotlinx.coroutines.withTimeout
import org.json.JSONArray
import org.json.JSONObject
import org.junit.Assert.*
import org.junit.Test
import org.junit.runner.RunWith
import java.io.File
import java.util.UUID

/** Exercises the production IO dispatcher/teardown scope, using only a fresh synthetic private root. */
@RunWith(AndroidJUnit4::class)
class DurableTransportOwnershipTest {
    private fun context(): Context {
        val actual = InstrumentationRegistry.getInstrumentation().targetContext
        val root = File(actual.noBackupFilesDir, "synthetic-transport-${UUID.randomUUID()}")
        check(root.mkdir())
        check(root.canonicalFile.parentFile == actual.noBackupFilesDir.canonicalFile)
        return object : ContextWrapper(actual) {
            override fun getApplicationContext(): Context = this
            override fun getNoBackupFilesDir(): File = root
        }
    }
    private fun command(op: String) = JSONObject().put("op", op)
    private fun scoped(op: String, session: JSONObject, key: String? = null) = command(op)
        .put("session", session.getString("session")).put("scope", session.getJSONObject("scope"))
        .also { if (key != null) it.put("turn", key) }
    private suspend fun data(transport: NativeWorkspaceTransport, command: JSONObject): JSONObject {
        val reply = transport.exchange(command)
        assertEquals("ok", reply.getString("status"))
        return reply.getJSONObject("data")
    }
    private suspend fun submit(transport: NativeWorkspaceTransport, session: JSONObject, key: String) {
        val request = JSONObject().put("version", 1).put("scope", session.getJSONObject("scope"))
            .put("turn", key).put("expected_revision", 0).put("intent", JSONObject().put("kind", "actions")
                .put("value", JSONArray().put(command("give").put("item", "potion").put("to", "mira").put("quantity", 1))))
        assertEquals("queued", data(transport, command("submit").put("session", session.getString("session"))
            .put("request", request).put("mode", "delayed")).getString("phase"))
    }
    private suspend fun running(transport: NativeWorkspaceTransport, session: JSONObject, key: String) = withTimeout(3_000) {
        while (true) {
            val phase = data(transport, scoped("turn_status", session, key)).getString("phase")
            if (phase == "running") break
            assertEquals("Cancellation proof must observe active inference", "queued", phase)
            delay(1)
        }
    }
    private suspend fun unchanged(transport: NativeWorkspaceTransport, session: JSONObject) {
        val snapshot = data(transport, scoped("play_snapshot", session).put("expected_revision", 0))
        assertEquals(0L, snapshot.getLong("revision"))
        assertEquals(0, snapshot.getJSONArray("receipts").length())
        assertTrue(snapshot.getJSONObject("inventory").has("potion"))
    }
    /** No stats/debug API: availability of all four real owner slots proves async release. */
    private suspend fun allSlotsReleased(path: File) = withContext(Dispatchers.IO) {
        withTimeout(5_000) {
            while (true) {
                val handles = mutableListOf<Long>()
                try {
                    repeat(4) {
                        val handle = NativeWorkspace.open(path.absolutePath)
                        if (handle != 0L) handles += handle
                    }
                    if (handles.size == 4) break
                } finally { handles.forEach { NativeWorkspace.close(it) } }
                delay(5)
            }
        }
    }

    @Test fun productionTransportCancelsActiveRustWorkAndRepeatedMainCloseReleasesEverySlot() = runBlocking {
        val context = context()
        val database = File(context.noBackupFilesDir, "workspace-v1/stories.sqlite3")
        // More cycles than the native four-owner cap: a single retained owner fails the slot proof.
        repeat(6) { cycle ->
            val transport = NativeWorkspaceTransport(context)
            try {
                val session = data(transport, command("create").put("seed", "lantern-quay-v1"))
                val key = "cancel-$cycle"
                submit(transport, session, key)
                val worker = async { data(transport, scoped("prepare", session, key)) }
                running(transport, session, key)
                withContext(Dispatchers.Main) { assertFalse(worker.isCompleted) }
                assertEquals("cancelled", data(transport, scoped("cancel", session, key)).getString("phase"))
                assertEquals("cancelled", withTimeout(3_000) { worker.await() }.getString("phase"))
                unchanged(transport, session)
                withContext(Dispatchers.Main) { repeat(3) { transport.close() } }
                try { transport.exchange(command("workspace")); fail("Disposed transport must remain terminal") }
                catch (_: IllegalStateException) { }
            } finally { withContext(Dispatchers.Main) { transport.close() } }
            allSlotsReleased(database)
        }
        assertTrue(database.isFile)
        // Only this test's create-new synthetic root; production workspace and earlier saves stay intact.
        assertTrue(context.noBackupFilesDir.deleteRecursively())
    }

    @Test fun productionTransportDisposalReleasesItsOwnerAndCannotCommitALatePreparedResult() = runBlocking {
        val context = context()
        val database = File(context.noBackupFilesDir, "workspace-v1/stories.sqlite3")
        val transport = NativeWorkspaceTransport(context)
        try {
            val session = data(transport, command("create").put("seed", "lantern-quay-v1"))
            submit(transport, session, "dispose-running")
            val worker = async { transport.exchange(scoped("prepare", session, "dispose-running")) }
            running(transport, session, "dispose-running")
            withContext(Dispatchers.Main) {
                assertFalse(worker.isCompleted)
                repeat(3) { transport.close() }
            }
            val reply = withTimeout(3_000) { worker.await() }
            // close() schedules IO teardown. Preparation may finish before that worker runs;
            // Ready is still uncommitted. The closed adapter and fresh canonical snapshot,
            // rather than a scheduler-dependent reply, establish the disposal guarantee.
            if (reply.getString("status") == "ok") assertEquals("ready", reply.getJSONObject("data").getString("phase"))
            else {
                assertEquals("rejected", reply.getString("status"))
                assertEquals("Closed", reply.getString("error"))
            }
            allSlotsReleased(database)
            try { transport.exchange(scoped("commit", session, "dispose-running")); fail("Closed adapter accepted a late commit") }
            catch (_: IllegalStateException) { }
            val fresh = NativeWorkspaceTransport(context)
            try {
                val resumed = data(fresh, command("resume").put("scope", session.getJSONObject("scope")))
                unchanged(fresh, resumed)
                assertEquals(1, data(fresh, command("workspace")).getJSONArray("stories").length())
            } finally { fresh.close() }
            allSlotsReleased(database)
        } finally { transport.close() }
        assertTrue(context.noBackupFilesDir.deleteRecursively())
    }
}

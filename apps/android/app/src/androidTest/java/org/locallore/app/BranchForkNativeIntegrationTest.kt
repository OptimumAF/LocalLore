/* Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0 */
package org.locallore.app

import android.content.Context
import androidx.test.core.app.ApplicationProvider
import androidx.test.ext.junit.runners.AndroidJUnit4
import java.io.File
import java.util.UUID
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.runBlocking
import kotlinx.coroutines.withContext
import org.json.JSONObject
import org.junit.Assert.*
import org.junit.Test
import org.junit.runner.RunWith

/** Actual JNI/Host/Store cases in unique synthetic app-private roots; execution separately authorized. */
@RunWith(AndroidJUnit4::class)
class BranchForkNativeIntegrationTest {
    private fun fresh(): File = File(ApplicationProvider.getApplicationContext<Context>().noBackupFilesDir,
        "fork-native-fixture-${UUID.randomUUID()}").also { check(it.mkdir()) }
    private fun call(handle: Long, command: JSONObject): JSONObject {
        val input = JSONObject().put("version", 1).put("command", command).toString().toByteArray(Charsets.UTF_8)
        val reply = JSONObject(NativeWorkspace.call(handle, input).toString(Charsets.UTF_8))
        assertEquals("ok", reply.getString("status")); return reply.getJSONObject("data")
    }
    private fun context(handle: Long): BranchForkContext {
        val created = call(handle, JSONObject().put("op", "create").put("seed", "lantern-quay-v1"))
        val scope = created.getJSONObject("scope")
        return BranchForkContext(created.getString("session"), ForkScope(scope.getString("story"), scope.getString("branch")), 0)
    }
    @Test fun sameOwnerNativeForkThenReopenLookupPreservesOriginalAndNeverCreatesMissing() = runBlocking {
        withContext(Dispatchers.IO) {
            val directory = fresh(); val path = File(directory, "stories.sqlite3")
            var handle = NativeWorkspace.open(path.absolutePath).also { check(it > 0) }
            val context = context(handle); val input = BranchForkInput(context.parent, "fixed-jni-child", 0, 0)
            val gateway = NativeForkGateway { handle }
            try {
                val registered = gateway.register(context, input, true)
                val outcome = gateway.run(registered.operation)
                assertEquals(BranchForkPhase.COMPLETED, outcome.phase); assertTrue(outcome.outcome!!.created)
                gateway.cancel(registered.operation)
                assertEquals(outcome.outcome, gateway.status(registered.operation).outcome)
                val current = call(handle, JSONObject().put("op", "open").put("session", context.session)
                    .put("scope", JSONObject().put("story", context.parent.story).put("branch", context.parent.branch)))
                assertEquals(context.parent.branch, current.getJSONObject("scope").getString("branch"))
                assertEquals(0L, current.getLong("revision"))
            } finally { gateway.close(); NativeWorkspace.close(handle) }
            handle = NativeWorkspace.open(path.absolutePath).also { check(it > 0) }
            val recovered = NativeForkGateway { handle }
            try {
                val existing = recovered.lookup(input)
                assertTrue(existing.found); assertFalse(existing.outcome!!.created)
                val before = call(handle, JSONObject().put("op", "branches").put("story", context.parent.story)).toString()
                assertFalse(recovered.lookup(input.copy(childBranch = "never-created")).found)
                assertEquals(before, call(handle, JSONObject().put("op", "branches").put("story", context.parent.story)).toString())
            } finally { recovered.close(); NativeWorkspace.close(handle) }
            // Retain only this own synthetic root; no default save cleanup.
        }
    }
    @Test fun registrationCancellationConsentAndClosedOwnerAreActualNativeFences() = runBlocking {
        withContext(Dispatchers.IO) {
            val directory = fresh(); val handle = NativeWorkspace.open(File(directory, "stories.sqlite3").absolutePath)
            check(handle > 0); val context = context(handle); val input = BranchForkInput(context.parent, "cancelled-child", 0, 0)
            val gateway = NativeForkGateway { handle }
            try {
                try { gateway.register(context, input, false); fail("Consent bypass") }
                catch (failure: BranchForkFailure) { assertEquals("ForkConsentRequired", failure.category) }
                val registered = gateway.register(context, input, true); gateway.cancel(registered.operation)
                val cancelled = gateway.run(registered.operation)
                assertEquals(BranchForkPhase.REJECTED, cancelled.phase); assertEquals("Cancelled", cancelled.error)
                assertFalse(gateway.lookup(input).found)
                NativeWorkspace.close(handle)
                try { gateway.lookup(input); fail("Closed owner accepted") }
                catch (failure: BranchForkFailure) { assertEquals("InvalidHandle", failure.category) }
            } finally { gateway.close(); NativeWorkspace.close(handle) }
        }
    }
}

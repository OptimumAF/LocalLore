/* Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0 */
package org.locallore.app

import android.content.Context
import androidx.test.core.app.ApplicationProvider
import androidx.test.ext.junit.runners.AndroidJUnit4
import java.io.File
import java.util.UUID
import java.util.concurrent.atomic.AtomicInteger
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.runBlocking
import kotlinx.coroutines.withContext
import org.json.JSONObject
import org.junit.Assert.*
import org.junit.Test
import org.junit.runner.RunWith

/** Actual JNI/Host/Store in new synthetic roots. The observer counts attempts, not success. */
@RunWith(AndroidJUnit4::class)
class NativeForkMutationObservationTest {
    private fun call(handle: Long, command: JSONObject): JSONObject {
        val request = JSONObject().put("version", 1).put("command", command)
            .toString().toByteArray(Charsets.UTF_8)
        val reply = JSONObject(NativeWorkspace.call(handle, request).toString(Charsets.UTF_8))
        assertEquals("ok", reply.getString("status"))
        return reply.getJSONObject("data")
    }

    private suspend fun withWorkspace(block: suspend (Long, BranchForkContext) -> Unit) {
        withContext(Dispatchers.IO) {
            val app = ApplicationProvider.getApplicationContext<Context>()
            val directory = File(app.noBackupFilesDir, "fork-observer-fixture-${UUID.randomUUID()}")
                .also { check(it.mkdir()) }
            // This test owns this one handle. Fork gateways only borrow it.
            val handle = NativeWorkspace.open(File(directory, "stories.sqlite3").absolutePath)
                .also { check(it > 0) }
            try {
                val created = call(handle, JSONObject().put("op", "create").put("seed", "lantern-quay-v1"))
                val scope = created.getJSONObject("scope")
                assertEquals(0L, created.getLong("revision"))
                val context = BranchForkContext(created.getString("session"),
                    ForkScope(scope.getString("story"), scope.getString("branch")), 0)
                block(handle, context)
            } finally {
                NativeWorkspace.close(handle)
            }
            // Retain only this new synthetic root; never adopt or delete another workspace.
        }
    }

    private suspend fun refused(category: String, operation: suspend () -> Unit) {
        try { operation(); fail("Expected fork refusal") }
        catch (failure: BranchForkFailure) { assertEquals(category, failure.category) }
    }

    private fun parentView(handle: Long, context: BranchForkContext): String {
        val scope = JSONObject().put("story", context.parent.story).put("branch", context.parent.branch)
        val opened = call(handle, JSONObject().put("op", "open").put("session", context.session).put("scope", scope))
        assertEquals(0L, opened.getLong("revision"))
        return call(handle, JSONObject().put("op", "play_snapshot").put("session", context.session)
            .put("scope", scope).put("expected_revision", 0)).toString()
    }

    @Test fun localGuardsAndReadOnlyOperationsNeverObserveMutation() = runBlocking {
        val attempts = AtomicInteger()
        withWorkspace { handle, context ->
            val borrows = AtomicInteger()
            val gateway = NativeForkGateway(workspaceHandle = { borrows.incrementAndGet(); handle },
                mutationObserver = { attempts.incrementAndGet() })
            val input = BranchForkInput(context.parent, "guard-child", 0, 0)
            try {
                refused("InvalidForkInput") { gateway.register(context, input.copy(childBranch = context.parent.branch), true) }
                refused("InvalidForkInput") { gateway.register(context.copy(head = 1), input, true) }
                assertEquals(0, borrows.get())
                refused("TooLarge") { gateway.register(context.copy(session = "x".repeat(4097)), input, true) }
                assertEquals(1, borrows.get())
                refused("InvalidToken") { gateway.run(1) }
                refused("InvalidToken") { gateway.status(1) }
                assertFalse(gateway.lookup(input).found)
                gateway.cancel()
                assertEquals(0, attempts.get())

                val invalidOwner = NativeForkGateway(workspaceHandle = { 0L },
                    mutationObserver = { attempts.incrementAndGet() })
                try { refused("InvalidHandle") { invalidOwner.register(context, input, true) } }
                finally { invalidOwner.close() }

                lateinit var retiredEpoch: NativeForkGateway
                retiredEpoch = NativeForkGateway(workspaceHandle = { retiredEpoch.cancel(); handle },
                    mutationObserver = { attempts.incrementAndGet() })
                try { refused("Cancelled") { retiredEpoch.register(context, input, true) } }
                finally { retiredEpoch.close() }

                // Preserve the original trailing-lambda constructor call shape.
                val legacy = NativeForkGateway { handle }
                try { assertFalse(legacy.lookup(input).found) } finally { legacy.close() }
                gateway.close()
                refused("Cancelled") { gateway.register(context, input, true) }
                assertEquals(0, attempts.get())
            } finally { gateway.close() }
        }
        assertEquals(0, attempts.get()) // Includes actual workspace resource teardown.
    }

    @Test fun successfulRegisterAndRunCountTwoWhileReadsAndCancellationDoNotCount() = runBlocking {
        val attempts = AtomicInteger()
        withWorkspace { handle, context ->
            val gateway = NativeForkGateway(workspaceHandle = { handle },
                mutationObserver = { attempts.incrementAndGet() })
            val input = BranchForkInput(context.parent, "observed-child", 0, 0)
            try {
                val original = parentView(handle, context)
                assertFalse(gateway.lookup(input).found)
                assertEquals(0, attempts.get())
                val registered = gateway.register(context, input, true)
                assertEquals(BranchForkPhase.REGISTERED, registered.phase)
                assertEquals(1, attempts.get())
                assertEquals(registered.operation, gateway.status(registered.operation).operation)
                assertEquals(1, attempts.get())
                val completed = gateway.run(registered.operation)
                assertEquals(BranchForkPhase.COMPLETED, completed.phase)
                assertTrue(checkNotNull(completed.outcome).created)
                assertEquals(2, attempts.get())
                gateway.cancel(registered.operation)
                assertEquals(completed.outcome, gateway.status(registered.operation).outcome)
                val found = gateway.lookup(input)
                assertTrue(found.found)
                assertFalse(checkNotNull(found.outcome).created)
                assertFalse(gateway.lookup(input.copy(childBranch = "read-only-missing")).found)
                assertEquals(original, parentView(handle, context))
                val branches = call(handle, JSONObject().put("op", "branches").put("story", context.parent.story))
                assertEquals(2, branches.getJSONArray("branches").length())
                gateway.close()
                assertEquals(2, attempts.get())
            } finally { gateway.close() }
        }
        assertEquals(2, attempts.get())
    }

    @Test fun nativeConsentAndCancelledRunRejectionsStillObserveAttemptsWithoutCreatingChild() = runBlocking {
        val attempts = AtomicInteger()
        withWorkspace { handle, context ->
            val gateway = NativeForkGateway(workspaceHandle = { handle },
                mutationObserver = { attempts.incrementAndGet() })
            val input = BranchForkInput(context.parent, "rejected-child", 0, 0)
            try {
                val original = parentView(handle, context)
                refused("ForkConsentRequired") { gateway.register(context, input, false) }
                assertEquals(1, attempts.get())
                assertFalse(gateway.lookup(input).found)
                val registered = gateway.register(context, input, true)
                assertEquals(2, attempts.get())
                gateway.cancel(registered.operation)
                assertEquals(2, attempts.get())
                val rejected = gateway.run(registered.operation)
                assertEquals(BranchForkPhase.REJECTED, rejected.phase)
                assertEquals("Cancelled", rejected.error)
                assertEquals(3, attempts.get())
                assertEquals(rejected, gateway.status(registered.operation))
                assertFalse(gateway.lookup(input).found)
                assertEquals(original, parentView(handle, context))
                val branches = call(handle, JSONObject().put("op", "branches").put("story", context.parent.story))
                assertEquals(1, branches.getJSONArray("branches").length())
            } finally { gateway.close() }
        }
        assertEquals(3, attempts.get())
    }
}

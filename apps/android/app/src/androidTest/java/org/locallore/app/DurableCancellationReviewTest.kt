/* Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0 */
package org.locallore.app

import androidx.test.ext.junit.runners.AndroidJUnit4
import androidx.test.platform.app.InstrumentationRegistry
import kotlinx.coroutines.CompletableDeferred
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.async
import kotlinx.coroutines.runBlocking
import kotlinx.coroutines.withContext
import kotlinx.coroutines.withTimeout
import org.json.JSONObject
import org.junit.Assert.*
import org.junit.Test
import org.junit.runner.RunWith
import java.io.File
import java.util.UUID

/** The first submit is held before real JNI; UnknownTurn comes from actual SQLite-backed Host. */
@RunWith(AndroidJUnit4::class)
class DurableCancellationReviewTest {
    private class ActualTransport(private val path: File) : WorkspaceTransport {
        private var handle = 0L
        override suspend fun exchange(command: JSONObject): JSONObject = withContext(Dispatchers.IO) {
            if (handle == 0L) handle = NativeWorkspace.open(path.absolutePath).also { check(it != 0L) }
            val envelope = JSONObject().put("version", 1).put("command", command)
            JSONObject(NativeWorkspace.call(handle, envelope.toString().toByteArray(Charsets.UTF_8))
                .toString(Charsets.UTF_8))
        }
        override fun close() { if (handle != 0L) NativeWorkspace.close(handle); handle = 0L }
    }
    private class GatedSubmit(private val actual: WorkspaceTransport) : WorkspaceTransport {
        val entered = CompletableDeferred<Unit>()
        val release = CompletableDeferred<Unit>()
        val calls = mutableListOf<Pair<String, String?>>()
        private var first = true
        override suspend fun exchange(command: JSONObject): JSONObject {
            val op = command.getString("op")
            val key = if (op == "submit") command.getJSONObject("request").getString("turn")
                else command.optString("turn").takeUnless { it.isEmpty() }
            calls += op to key
            if (op == "submit" && first) {
                first = false
                entered.complete(Unit)
                release.await()
            }
            return actual.exchange(command)
        }
        override fun close() = actual.close()
    }
    private fun directory(): File {
        val parent = InstrumentationRegistry.getInstrumentation().targetContext.noBackupFilesDir.canonicalFile
        return File(parent, "synthetic-cancel-review-${UUID.randomUUID()}").also {
            check(it.mkdir()); check(it.canonicalFile.parentFile == parent)
        }
    }
    private fun unchanged(snapshot: SavedSnapshot) {
        assertEquals(0L, snapshot.revision)
        assertEquals("You", snapshot.potionOwner)
        assertTrue(snapshot.messages.isEmpty())
    }
    private suspend fun cancelled(gateway: DurableGateway): SavedSnapshot = try {
        gateway.cancelSaved()
    } catch (failure: WorkspaceFailure) {
        throw AssertionError("Pre-submit cancellation failed: ${failure.category}", failure)
    }

    @Test fun cancellationBeforeSubmitExistsDoesNotFailOrRegenerateTheLateOriginalRequest() = runBlocking {
        val directory = directory()
        val path = File(directory, "stories.sqlite3")
        val transport = GatedSubmit(ActualTransport(path))
        var gateway = DurableGateway(transport)
        try {
            val initial = gateway.initialize()
            val original = async { gateway.respond(DemoAction.GIVE_POTION, 0, DemoMode.ACCEPTED) }
            try {
                withTimeout(3_000) { transport.entered.await() }
                gateway.cancel()
                // Baseline throws WorkspaceFailure(UnknownTurn) here despite proven pre-submit cancellation.
                unchanged(cancelled(gateway))
                unchanged(gateway.recoverSaved())
                transport.release.complete(Unit)
                assertTrue(withTimeout(3_000) { original.await() } is DemoResult.Rejected)
                unchanged(gateway.recoverSaved())
                assertEquals(1, transport.calls.count { it.first == "submit" })
                assertEquals(0, transport.calls.count { it.first == "prepare" || it.first == "commit" })
                assertEquals(1, gateway.snapshot().uncommittedDrafts)
                withContext(Dispatchers.IO) { gateway.close() }
                gateway = DurableGateway(ActualTransport(path))
                val reopened = gateway.initialize()
                assertEquals(initial.selected.story, reopened.selected.story)
                assertEquals(initial.selected.branch, reopened.selected.branch)
                unchanged(reopened)
                assertEquals(1, reopened.uncommittedDrafts)
            } finally {
                transport.release.complete(Unit)
                withTimeout(3_000) { original.await() }
            }
        } finally {
            withContext(Dispatchers.IO) { gateway.close() }
            check(directory.deleteRecursively())
        }
    }

    @Test fun lateCancelledSubmitCannotClearOrCommitTheReplacementOperation() = runBlocking {
        val directory = directory()
        val path = File(directory, "stories.sqlite3")
        val transport = GatedSubmit(ActualTransport(path))
        var gateway = DurableGateway(transport)
        try {
            gateway.initialize()
            val original = async { gateway.respond(DemoAction.GIVE_POTION, 0, DemoMode.ACCEPTED) }
            try {
                withTimeout(3_000) { transport.entered.await() }
                gateway.cancel()
                unchanged(cancelled(gateway))
                val replacement = gateway.respond(DemoAction.GIVE_POTION, 0, DemoMode.ACCEPTED)
                assertTrue(replacement is DemoResult.Prepared)
                transport.release.complete(Unit)
                assertTrue(withTimeout(3_000) { original.await() } is DemoResult.Rejected)
                assertTrue(gateway.commitAsync(replacement) is DemoResult.Accepted)
                val saved = gateway.snapshot()
                assertEquals(1L, saved.revision)
                assertEquals("Not in your inventory", saved.potionOwner)
                assertEquals(2, saved.messages.size)
                assertEquals("You give 1 potion to mira.", saved.messages.single { !it.isPlayer }.text)
                val submitted = transport.calls.filter { it.first == "submit" }.map { checkNotNull(it.second) }
                assertEquals(2, submitted.size)
                assertNotEquals(submitted[0], submitted[1])
                assertEquals(listOf("prepare" to submitted[1], "commit" to submitted[1]),
                    transport.calls.filter { it.first == "prepare" || it.first == "commit" })
                assertEquals(saved.messages, gateway.recoverSaved().messages)
                withContext(Dispatchers.IO) { gateway.close() }
                gateway = DurableGateway(ActualTransport(path))
                val reopened = gateway.initialize()
                assertEquals(saved.revision, reopened.revision)
                assertEquals(saved.messages, reopened.messages)
            } finally {
                transport.release.complete(Unit)
                withTimeout(3_000) { original.await() }
            }
        } finally {
            withContext(Dispatchers.IO) { gateway.close() }
            check(directory.deleteRecursively())
        }
    }
}

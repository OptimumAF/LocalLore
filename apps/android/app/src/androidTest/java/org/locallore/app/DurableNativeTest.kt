/* Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0 */
package org.locallore.app

import androidx.test.ext.junit.runners.AndroidJUnit4
import androidx.test.platform.app.InstrumentationRegistry
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.CompletableDeferred
import kotlinx.coroutines.async
import kotlinx.coroutines.runBlocking
import kotlinx.coroutines.withContext
import org.json.JSONObject
import org.junit.Assert.*
import org.junit.Test
import org.junit.runner.RunWith
import java.io.File
import java.util.UUID

/** App-private synthetic SQLite only. Buildable without attaching any device or emulator. */
@RunWith(AndroidJUnit4::class)
class DurableNativeTest {
    private class TestTransport(private val path: File) : WorkspaceTransport {
        private var handle = 0L
        override suspend fun exchange(command: JSONObject): JSONObject = withContext(Dispatchers.IO) {
            if (handle == 0L) handle = NativeWorkspace.open(path.absolutePath).also { check(it != 0L) }
            val input = JSONObject().put("version", 1).put("command", command).toString().toByteArray(Charsets.UTF_8)
            JSONObject(NativeWorkspace.call(handle, input).toString(Charsets.UTF_8))
        }
        override fun close() { if (handle != 0L) NativeWorkspace.close(handle); handle = 0L }
    }
    private fun directory(): File = File(InstrumentationRegistry.getInstrumentation().targetContext.noBackupFilesDir,
        "synthetic-durability-${UUID.randomUUID()}").also { check(it.mkdirs()) }

    @Test fun actualJniProcessOwnerReopenRestoresCommittedTranscriptAndIndependentStories() = runBlocking {
        val directory = directory(); val path = File(directory, "stories.sqlite3")
        var gateway = DurableGateway(TestTransport(path))
        try {
            val initial = gateway.initialize()
            assertTrue(initial.location.endsWith("stories.sqlite3")); assertEquals(1, initial.schemaVersion)
            assertEquals("fantasy_v1", initial.rulesProfile)
            val prepared = gateway.respond(DemoAction.GIVE_POTION, 0, DemoMode.ACCEPTED)
            assertTrue(prepared is DemoResult.Prepared)
            assertTrue(gateway.commitAsync(prepared) is DemoResult.Accepted)
            val committed = gateway.snapshot()
            assertEquals(1L, committed.revision); assertEquals(2, committed.messages.size)
            val second = gateway.createSaved()
            assertEquals(0L, second.revision); assertTrue(second.messages.isEmpty())
            assertEquals(2, second.stories.size)
            gateway.close()
            // New JNI owner and Host reload/replay the same actual database; no cached UI transcript.
            gateway = DurableGateway(TestTransport(path))
            val reopened = gateway.initialize()
            val restored = gateway.resumeSaved(reopened.stories.first { it.story == committed.selected.story })
            assertEquals(committed.messages, restored.messages)
            assertEquals(committed.revision, restored.revision)
            assertEquals(2, restored.stories.size)
            assertTrue(gateway.respond(DemoAction.GIVE_POTION, restored.revision, DemoMode.ACCEPTED) is DemoResult.Rejected)
            assertEquals(restored.messages, gateway.snapshot().messages)
        } finally { gateway.close(); directory.deleteRecursively() }
    }

    @Test fun lostCommitAcknowledgementRecoversSameTurnAndNeverDuplicatesActualSqliteReceipt() = runBlocking {
        val directory = directory(); val actual = TestTransport(File(directory, "stories.sqlite3"))
        var dropCommit = true
        val submitted = mutableListOf<String>()
        val wrapped = object : WorkspaceTransport {
            override suspend fun exchange(command: JSONObject): JSONObject {
                if (command.getString("op") == "submit") submitted += command.getJSONObject("request").getString("turn")
                val reply = actual.exchange(command)
                if (command.getString("op") == "commit" && dropCommit) {
                    dropCommit = false; error("synthetic lost acknowledgement")
                }
                return reply
            }
            override fun close() = actual.close()
        }
        val gateway = DurableGateway(wrapped)
        try {
            gateway.initialize()
            assertTrue(gateway.commitAsync(gateway.respond(DemoAction.GIVE_POTION, 0, DemoMode.ACCEPTED)) is DemoResult.Accepted)
            assertEquals(1, submitted.size)
            assertEquals(1L, gateway.recoverSaved().revision)
            assertEquals(2, gateway.snapshot().messages.size)
        } finally { gateway.close(); directory.deleteRecursively() }
    }

    @Test fun actualJniCancellationReleasesLiveOwnerWithoutDeletingSavedStory() = runBlocking {
        val directory = directory(); val path = File(directory, "stories.sqlite3")
        var gateway = DurableGateway(TestTransport(path))
        try {
            gateway.initialize()
            assertTrue(gateway.respond(DemoAction.GIVE_POTION, 0, DemoMode.ACCEPTED) is DemoResult.Prepared)
            gateway.cancel()
            val cancelled = gateway.cancelSaved()
            assertEquals(0L, cancelled.revision); assertTrue(cancelled.messages.isEmpty())
            gateway.close()
            gateway = DurableGateway(TestTransport(path))
            assertEquals(0L, gateway.initialize().revision)
            assertEquals(1, gateway.snapshot().stories.size)
        } finally { gateway.close(); directory.deleteRecursively() }
    }

    @Test fun failedCancellationTransportCannotTurnRecoveryIntoACommit() = runBlocking {
        val directory = directory(); val actual = TestTransport(File(directory, "stories.sqlite3"))
        var failCancel = true
        val gateway = DurableGateway(object : WorkspaceTransport {
            override suspend fun exchange(command: JSONObject): JSONObject {
                if (command.getString("op") == "cancel" && failCancel) { failCancel = false; error("synthetic transport failure") }
                return actual.exchange(command)
            }
            override fun close() = actual.close()
        })
        try {
            gateway.initialize()
            assertTrue(gateway.respond(DemoAction.GIVE_POTION, 0, DemoMode.ACCEPTED) is DemoResult.Prepared)
            gateway.cancel()
            try { gateway.cancelSaved(); fail("Expected transport failure") } catch (_: IllegalStateException) { }
            assertEquals(0L, gateway.recoverSaved().revision)
            assertTrue(gateway.snapshot().messages.isEmpty())
        } finally { gateway.close(); directory.deleteRecursively() }
    }

    @Test fun lateCancelledPrepareCannotClearTheReplacementOperationKey() = runBlocking {
        val directory = directory(); val actual = TestTransport(File(directory, "stories.sqlite3"))
        val entered = CompletableDeferred<Unit>(); val release = CompletableDeferred<Unit>()
        var first = true
        val gateway = DurableGateway(object : WorkspaceTransport {
            override suspend fun exchange(command: JSONObject): JSONObject {
                if (command.getString("op") == "prepare" && first) {
                    first = false; entered.complete(Unit); release.await()
                }
                return actual.exchange(command)
            }
            override fun close() = actual.close()
        })
        try {
            gateway.initialize()
            val old = async { gateway.respond(DemoAction.GIVE_POTION, 0, DemoMode.ACCEPTED) }
            entered.await(); gateway.cancel(); gateway.cancelSaved()
            val replacement = gateway.respond(DemoAction.GIVE_POTION, 0, DemoMode.ACCEPTED)
            release.complete(Unit); assertTrue(old.await() is DemoResult.Rejected)
            assertTrue(gateway.commitAsync(replacement) is DemoResult.Accepted)
            assertEquals(1L, gateway.snapshot().revision)
        } finally { release.complete(Unit); gateway.close(); directory.deleteRecursively() }
    }
}

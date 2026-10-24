/* Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0 */
package org.locallore.app

import androidx.test.core.app.ApplicationProvider
import androidx.test.ext.junit.runners.AndroidJUnit4
import android.content.Context
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.runBlocking
import kotlinx.coroutines.withContext
import org.json.JSONObject
import org.junit.Assert.*
import org.junit.Test
import org.junit.runner.RunWith
import java.io.File
import java.util.UUID

/** Actual JNI/Store tests in unique app-private synthetic workspaces; no default-save reset. */
@RunWith(AndroidJUnit4::class)
class ArchiveIntegrationTest {
    private fun fresh(): File {
        val context = ApplicationProvider.getApplicationContext<Context>()
        return File(context.noBackupFilesDir, "archive-fixture-${UUID.randomUUID()}").also {
            check(it.mkdir())
            File(it, "owner-v1").writeText("locallore-archive-fixture-v1")
        }
    }

    private class Transport(path: File) : WorkspaceTransport {
        private var handle = NativeWorkspace.open(path.absolutePath).also { check(it > 0) }
        override suspend fun exchange(command: JSONObject): JSONObject = withContext(Dispatchers.IO) {
            check(handle > 0)
            val input = JSONObject().put("version", 1).put("command", command).toString().toByteArray(Charsets.UTF_8)
            JSONObject(NativeWorkspace.call(handle, input).toString(Charsets.UTF_8))
        }
        override fun close() { handle.also { handle = 0 }.takeIf { it > 0 }?.let(NativeWorkspace::close) }
    }

    private fun json(bytes: ByteArray) = JSONObject(bytes.toString(Charsets.UTF_8)).also {
        assertEquals(1, it.getInt("version"))
    }
    private fun accepted(bytes: ByteArray): JSONObject = json(bytes).also {
        assertEquals("ok", it.getString("status"))
    }.getJSONObject("data")
    private fun rejected(bytes: ByteArray, category: String) {
        val reply = json(bytes)
        assertEquals("rejected", reply.getString("status"))
        assertEquals(category, reply.getString("error"))
    }
    private fun control(story: SavedStory, revision: Long = story.revision) = JSONObject()
        .put("story", story.story).put("branch", story.branch).put("expected_revision", revision)
        .toString().toByteArray(Charsets.UTF_8)
    private fun archive(directory: File): Long {
        val staging = File(directory, "staging").also { check(it.isDirectory || it.mkdir()) }
        return NativeArchive.open(File(directory, "stories.sqlite3").canonicalPath, staging.canonicalPath)
            .also { assertTrue(it > 0) }
    }
    private suspend fun saved(directory: File, gift: Boolean): SavedSnapshot {
        val gateway = DurableGateway(Transport(File(directory, "stories.sqlite3")))
        try {
            gateway.initialize()
            if (gift) assertTrue(gateway.commitAsync(gateway.respond(DemoAction.GIVE_POTION, 0, DemoMode.ACCEPTED)) is DemoResult.Accepted)
            return gateway.snapshot()
        } finally { gateway.close() }
    }
    private fun capture(handle: Long, story: SavedStory): ByteArray {
        val prepared = accepted(NativeArchive.prepareExport(handle, control(story)))
        assertEquals(story.story, prepared.getJSONObject("preview").getString("story_id"))
        assertFalse(prepared.getJSONObject("preview").getBoolean("noncommitted_workflow_transferred"))
        return NativeArchive.exportBytes(handle, prepared.getLong("token"))
    }

    @Test fun workspaceContractAndDatabaseSchemaStayDistinctAcrossReopen() = runBlocking {
        withContext(Dispatchers.IO) {
            val directory = fresh()
            val database = File(directory, "stories.sqlite3")
            val first = DurableGateway(Transport(database))
            val before = try { first.initialize() } finally { first.close() }
            assertEquals(1, before.schemaVersion)
            assertEquals(5, before.databaseSchemaVersion)
            val second = DurableGateway(Transport(database))
            try {
                val after = second.initialize()
                assertEquals(before.selected, after.selected)
                assertEquals(before.revision, after.revision)
                assertEquals(before.messages, after.messages)
                assertEquals(1, after.schemaVersion)
                assertEquals(5, after.databaseSchemaVersion)
            } finally { second.close() }
            // Retain this private synthetic workspace as evidence; never delete shared/default saves.
        }
    }

    @Test fun acceptedGiftRoundTripReopensEqualBytesAndSameIdNeverOverwrites() = runBlocking {
        withContext(Dispatchers.IO) {
            val source = fresh(); val target = fresh()
            val original = saved(source, true); val unrelated = saved(target, false)
            val from = archive(source); val into = archive(target)
            try {
                val bytes = capture(from, checkNotNull(original.selected))
                val prepared = accepted(NativeArchive.prepareImport(into, bytes))
                val outcome = accepted(NativeArchive.commitImport(into, prepared.getLong("token")))
                assertEquals(checkNotNull(original.selected).story, outcome.getJSONObject("root").getString("story"))
                assertEquals(1, outcome.getInt("committed_turns"))
                assertEquals(0, File(target, "staging").listFiles()!!.size)
                val gateway = DurableGateway(Transport(File(target, "stories.sqlite3")))
                try {
                    val library = gateway.initialize()
                    assertEquals(2, library.stories.size)
                    assertTrue(library.stories.any { it.story == checkNotNull(unrelated.selected).story })
                    val imported = gateway.resumeSaved(library.stories.first { it.story == checkNotNull(original.selected).story })
                    assertEquals(original.messages, imported.messages)
                    assertEquals(original.revision, imported.revision)
                    assertEquals(original.potionOwner, imported.potionOwner)
                    assertEquals(5, imported.databaseSchemaVersion)
                    assertTrue(gateway.respond(DemoAction.GIVE_POTION, imported.revision, DemoMode.ACCEPTED) is DemoResult.Rejected)
                    assertEquals(imported.messages, gateway.snapshot().messages)
                } finally { gateway.close() }
                assertArrayEquals(bytes, capture(into, checkNotNull(original.selected)))
                val duplicate = accepted(NativeArchive.prepareImport(into, bytes))
                rejected(NativeArchive.commitImport(into, duplicate.getLong("token")), "Conflict")
                assertArrayEquals(bytes, capture(into, checkNotNull(original.selected)))
                assertEquals(0, File(target, "staging").listFiles()!!.size)
            } finally { NativeArchive.close(from); NativeArchive.close(into) }
        }
    }

    @Test fun unspentImportedStoryContinuesThroughActualRustWithoutDuplicatingThePotion() = runBlocking {
        withContext(Dispatchers.IO) {
            val source = fresh(); val target = fresh()
            val original = saved(source, false); saved(target, false)
            val from = archive(source); val into = archive(target)
            try {
                val bytes = capture(from, checkNotNull(original.selected))
                val prepared = accepted(NativeArchive.prepareImport(into, bytes))
                accepted(NativeArchive.commitImport(into, prepared.getLong("token")))
                val gateway = DurableGateway(Transport(File(target, "stories.sqlite3")))
                try {
                    val library = gateway.initialize()
                    val imported = gateway.resumeSaved(library.stories.first { it.story == checkNotNull(original.selected).story })
                    assertEquals(0L, imported.revision)
                    assertTrue(gateway.commitAsync(gateway.respond(DemoAction.GIVE_POTION, 0, DemoMode.ACCEPTED)) is DemoResult.Accepted)
                    val committed = gateway.snapshot()
                    assertEquals(1L, committed.revision)
                    assertEquals(2, committed.messages.size)
                    assertTrue(gateway.respond(DemoAction.GIVE_POTION, 1, DemoMode.ACCEPTED) is DemoResult.Rejected)
                    assertEquals(committed.messages, gateway.snapshot().messages)
                } finally { gateway.close() }
                assertEquals(0, File(target, "staging").listFiles()!!.size)
            } finally { NativeArchive.close(from); NativeArchive.close(into) }
        }
    }

    @Test fun cancelledAndWrongKindTokensCannotBeReusedOrConsumeTheLegitimateGrant() = runBlocking {
        withContext(Dispatchers.IO) {
            val directory = fresh(); val original = saved(directory, false); val handle = archive(directory)
            try {
                val first = accepted(NativeArchive.prepareExport(handle, control(checkNotNull(original.selected)))).getLong("token")
                rejected(NativeArchive.commitImport(handle, first), "InvalidToken")
                assertTrue(NativeArchive.exportBytes(handle, first).isNotEmpty())
                try { NativeArchive.exportBytes(handle, first); fail("Repeated export token accepted") }
                catch (expected: IllegalStateException) { assertEquals("InvalidToken", expected.message) }
                val second = accepted(NativeArchive.prepareExport(handle, control(checkNotNull(original.selected)))).getLong("token")
                NativeArchive.cancel(handle)
                try { NativeArchive.exportBytes(handle, second); fail("Cancelled export token accepted") }
                catch (expected: IllegalStateException) { assertEquals("InvalidToken", expected.message) }
                rejected(NativeArchive.prepareExport(handle, control(checkNotNull(original.selected), 1)), "Stale")
                assertTrue(capture(handle, checkNotNull(original.selected)).isNotEmpty())
            } finally { NativeArchive.close(handle) }
            rejected(NativeArchive.prepareExport(handle, control(checkNotNull(original.selected))), "InvalidHandle")
        }
    }

    @Test fun hostileArchiveAndCancelledImportLeaveTheExistingLibraryUntouched() = runBlocking {
        withContext(Dispatchers.IO) {
            val source = fresh(); val target = fresh()
            val original = saved(source, true); val existing = saved(target, false)
            val from = archive(source); val into = archive(target)
            try {
                val bytes = capture(from, checkNotNull(original.selected))
                rejected(NativeArchive.prepareImport(into, "{\"version\":1,\"version\":1}".toByteArray()), "Malformed")
                val future = JSONObject(bytes.toString(Charsets.UTF_8)).put("version", 999).toString().toByteArray()
                rejected(NativeArchive.prepareImport(into, future), "Unsupported")
                val corrupt = JSONObject(bytes.toString(Charsets.UTF_8))
                corrupt.getJSONObject("payload").getJSONObject("story").put("title", "Changed without checksum")
                rejected(NativeArchive.prepareImport(into, corrupt.toString().toByteArray()), "Integrity")
                val pending = accepted(NativeArchive.prepareImport(into, bytes)).getLong("token")
                NativeArchive.cancel(into)
                rejected(NativeArchive.commitImport(into, pending), "InvalidToken")
                val reopened = saved(target, false)
                assertEquals(existing.selected, reopened.selected)
                assertEquals(1, reopened.stories.size)
                assertEquals(existing.messages, reopened.messages)
                assertEquals(0, File(target, "staging").listFiles()!!.size)
            } finally { NativeArchive.close(from); NativeArchive.close(into) }
        }
    }

    @Test fun fourNativeOwnersCanBeClosedAndReacquiredWithoutLeakingHandles() = runBlocking {
        withContext(Dispatchers.IO) {
            val directory = fresh(); saved(directory, false)
            repeat(3) {
                val handles = mutableListOf<Long>()
                try {
                    repeat(4) { handles += archive(directory) }
                    assertEquals(0L, NativeArchive.open(File(directory, "stories.sqlite3").canonicalPath,
                        File(directory, "staging").canonicalPath))
                } finally { handles.forEach { NativeArchive.close(it); NativeArchive.close(it) } }
            }
        }
    }
}

/* Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0 */
package org.locallore.app

import androidx.test.ext.junit.runners.AndroidJUnit4
import androidx.test.platform.app.InstrumentationRegistry
import java.io.File
import java.util.UUID
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.runBlocking
import kotlinx.coroutines.withContext
import org.json.JSONObject
import org.junit.Assert.*
import org.junit.Test
import org.junit.runner.RunWith

/** Real Rust/SQLite/JSON, unique synthetic roots; original ancestor scopes are never rewritten. */
@RunWith(AndroidJUnit4::class)
class TimelineNativeTest {
    private class Transport(path: File) : WorkspaceTransport {
        val handle = NativeWorkspace.open(path.absolutePath).also { check(it > 0) }
        var lastView: JSONObject? = null
        override suspend fun exchange(command: JSONObject): JSONObject = withContext(Dispatchers.IO) {
            val input = JSONObject().put("version", 1).put("command", command).toString().toByteArray(Charsets.UTF_8)
            JSONObject(NativeWorkspace.call(handle, input).toString(Charsets.UTF_8)).also {
                if (command.getString("op") == "play_snapshot" && it.getString("status") == "ok")
                    lastView = JSONObject(it.getJSONObject("data").toString())
            }
        }
        override fun close() = NativeWorkspace.close(handle)
    }
    @Test fun childResumeKeepsOriginalAncestorScopesAndIndependentCanon(): Unit = runBlocking {
        withContext(Dispatchers.IO) {
            val context = InstrumentationRegistry.getInstrumentation().targetContext
            val root = File(context.noBackupFilesDir, "timeline-native-${UUID.randomUUID()}").also { check(it.mkdir()) }
            val database = File(root, "stories.sqlite3")
            val staging = File(root, "staging").also { check(it.mkdir()) }
            val transport = Transport(database)
            val gateway = DurableGateway(transport)
            try {
                val unrelated = gateway.initialize()
                val source = InstrumentationRegistry.getInstrumentation().context.assets
                    .open("platform-roundtrip-v1/windows-origin.json").use { it.readBytes() }
                val archive = NativeArchive.open(database.canonicalPath, staging.canonicalPath).also { check(it > 0) }
                try {
                    val prepared = accepted(NativeArchive.prepareImport(archive, source))
                    accepted(NativeArchive.commitImport(archive, prepared.getLong("token")))
                } finally { NativeArchive.close(archive) }
                val library = gateway.reconcileSaved()
                val parent = library.stories.first { it.story == "platform-windows-v1" }
                val main = gateway.resumeSaved(parent)
                val mainView = checkNotNull(transport.lastView).toString()
                assertEquals(2L, main.revision); assertEquals(4, main.messages.size)
                // This is a regression: old Android code rejected the native inherited main receipt here.
                val child = gateway.resumeSaved(parent.copy(branch = "child"))
                assertEquals("child", checkNotNull(child.selected).branch)
                assertEquals(2L, child.revision); assertEquals(4, child.messages.size)
                assertEquals("Not in your inventory", child.potionOwner)
                val childView = checkNotNull(transport.lastView).toString()
                val receipts = checkNotNull(transport.lastView).getJSONArray("receipts")
                assertEquals("main", receipts.getJSONObject(0).getJSONObject("request").getJSONObject("scope").getString("branch"))
                assertEquals("child", receipts.getJSONObject(1).getJSONObject("request").getJSONObject("scope").getString("branch"))
                assertFalse(child.messages.any { it.text.contains("PLATFORM_SIBLING_CANARY") })
                val sibling = gateway.resumeSaved(parent.copy(branch = "sibling"))
                assertEquals("You", sibling.potionOwner)
                assertTrue(sibling.messages.any { it.text.contains("PLATFORM_SIBLING_CANARY") })
                assertTrue(gateway.commitAsync(gateway.respond(DemoAction.GIVE_POTION, 2, DemoMode.ACCEPTED)) is DemoResult.Accepted)
                assertEquals(3L, gateway.snapshot().revision)
                val afterMain = gateway.resumeSaved(parent)
                assertEquals(main.messages, afterMain.messages); assertEquals(mainView, checkNotNull(transport.lastView).toString())
                val afterChild = gateway.resumeSaved(parent.copy(branch = "child"))
                assertEquals(child.messages, afterChild.messages); assertEquals(childView, checkNotNull(transport.lastView).toString())
                assertTrue(gateway.respond(DemoAction.GIVE_POTION, 2, DemoMode.ACCEPTED) is DemoResult.Rejected)
                assertEquals(2L, gateway.snapshot().revision)
                val other = gateway.resumeSaved(checkNotNull(unrelated.selected))
                assertEquals(0L, other.revision); assertEquals("You", other.potionOwner); assertTrue(other.messages.isEmpty())
            } finally { gateway.close() }
            // The synthetic evidence root is retained; all four native workspace slots are reusable.
            val owners = mutableListOf<Long>()
            try {
                repeat(4) { owners += NativeWorkspace.open(database.absolutePath).also { check(it > 0) } }
                assertEquals(0L, NativeWorkspace.open(database.absolutePath))
            } finally { owners.forEach(NativeWorkspace::close) }
        }
    }
    private fun accepted(bytes: ByteArray): JSONObject = JSONObject(bytes.toString(Charsets.UTF_8)).also {
        assertEquals("ok", it.getString("status"))
    }.getJSONObject("data")
}

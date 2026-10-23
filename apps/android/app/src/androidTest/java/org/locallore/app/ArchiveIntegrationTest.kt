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

    @Test fun workspaceContractAndDatabaseSchemaStayDistinctAcrossReopen() = runBlocking {
        withContext(Dispatchers.IO) {
            val directory = fresh()
            val database = File(directory, "stories.sqlite3")
            val first = DurableGateway(Transport(database))
            val before = try { first.initialize() } finally { first.close() }
            assertEquals(1, before.schemaVersion)
            assertEquals(2, before.databaseSchemaVersion)
            val second = DurableGateway(Transport(database))
            try {
                val after = second.initialize()
                assertEquals(before.selected, after.selected)
                assertEquals(before.revision, after.revision)
                assertEquals(before.messages, after.messages)
                assertEquals(1, after.schemaVersion)
                assertEquals(2, after.databaseSchemaVersion)
            } finally { second.close() }
            // Retain this private synthetic workspace as evidence; never delete shared/default saves.
        }
    }
}

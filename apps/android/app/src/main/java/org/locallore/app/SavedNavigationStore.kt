/* Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0 */
package org.locallore.app

import android.content.Context
import android.util.AtomicFile
import java.io.File
import java.io.FileNotFoundException
import java.io.IOException
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.withContext

internal interface SavedNavigationStore {
    suspend fun load(): PlayDraftScope?
    suspend fun save(value: PlayDraftScope?)
}

/** One optional UI hint in app-private storage. SQLite still owns every saved outcome. */
internal class AtomicSavedNavigationStore(context: Context) : SavedNavigationStore {
    private val app = context.applicationContext

    private fun file() = AtomicFile(File(app.noBackupFilesDir, "last-selection-v1"))

    override suspend fun load(): PlayDraftScope? = withContext(Dispatchers.IO) {
        synchronized(gate) { read(file()) }
    }

    private fun read(atomic: AtomicFile): PlayDraftScope? {
        val input = try { atomic.openRead() } catch (_: FileNotFoundException) { return null }
        return input.use {
            val bytes = ByteArray(STORED_NAVIGATION_LIMIT + 1)
            var used = 0
            while (used < bytes.size) {
                val count = it.read(bytes, used, bytes.size - used)
                if (count < 0) break
                if (count == 0) throw IOException("Saved navigation hint could not be read")
                used += count
            }
            decodeStoredNavigationHint(bytes.copyOf(used))
        }
    }

    override suspend fun save(value: PlayDraftScope?) = withContext(Dispatchers.IO) {
        val bytes = value?.let { encodeStoredNavigationHint(it) ?: return@withContext }
        synchronized(gate) {
            val atomic = file()
            if (bytes == null) {
                atomic.delete()
            } else {
                val output = atomic.startWrite()
                try {
                    output.write(bytes)
                    atomic.finishWrite(output)
                } catch (failure: Exception) {
                    atomic.failWrite(output)
                    throw failure
                }
            }
            // AtomicFile can log filesystem failures without throwing.
            if (read(atomic) != value) throw IOException("Saved navigation hint could not be confirmed")
        }
    }

    private companion object {
        val gate = Any()
    }
}

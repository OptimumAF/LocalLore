/* Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0 */
package org.locallore.app

import android.content.Context
import kotlinx.coroutines.CoroutineScope
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.SupervisorJob
import kotlinx.coroutines.cancel
import kotlinx.coroutines.currentCoroutineContext
import kotlinx.coroutines.ensureActive
import kotlinx.coroutines.launch
import kotlinx.coroutines.sync.Mutex
import kotlinx.coroutines.sync.withLock
import kotlinx.coroutines.withContext
import org.json.JSONObject
import java.io.File
import java.nio.ByteBuffer
import java.nio.charset.CodingErrorAction
import java.nio.file.Files
import java.nio.file.LinkOption
import java.util.concurrent.atomic.AtomicBoolean
import java.util.concurrent.atomic.AtomicLong

internal object NativeArchive {
    init { System.loadLibrary("locallore_android") }
    external fun open(database: String, stagingRoot: String): Long
    external fun prepareExport(handle: Long, request: ByteArray): ByteArray
    external fun prepareImport(handle: Long, bytes: ByteArray): ByteArray
    external fun exportBytes(handle: Long, token: Long): ByteArray
    external fun commitImport(handle: Long, token: Long): ByteArray
    external fun cancel(handle: Long)
    external fun close(handle: Long)
}

/** IO-only native work, separate from the Host wire. Paths never come from a picker or archive. */
internal class NativeArchiveGateway(context: Context) : ArchiveGateway {
    private val app = context.applicationContext
    private val allocation = Mutex()
    private val handle = AtomicLong()
    private val closed = AtomicBoolean()
    private val epoch = AtomicLong()
    private val cleanup = CoroutineScope(SupervisorJob() + Dispatchers.IO)

    private suspend fun owner(): Long = allocation.withLock {
        if (closed.get()) throw ArchiveFailure("InvalidHandle")
        handle.get().takeIf { it != 0L }?.let { return@withLock it }
        val base = app.noBackupFilesDir.canonicalFile
        val workspace = File(base, "workspace-v1")
        val database = File(workspace, "stories.sqlite3")
        val staging = File(base, "archive-staging")
        val noFollow = arrayOf(LinkOption.NOFOLLOW_LINKS)
        if (!Files.isDirectory(workspace.toPath(), *noFollow) || Files.isSymbolicLink(workspace.toPath()) ||
            !Files.isRegularFile(database.toPath(), *noFollow) || Files.isSymbolicLink(database.toPath()) ||
            workspace.canonicalFile != workspace.absoluteFile || database.canonicalFile != database.absoluteFile)
            throw ArchiveFailure("Io")
        if (!Files.exists(staging.toPath(), *noFollow)) Files.createDirectory(staging.toPath())
        if (!Files.isDirectory(staging.toPath(), *noFollow) || Files.isSymbolicLink(staging.toPath()) ||
            staging.canonicalFile.parentFile != base) throw ArchiveFailure("Io")
        val opened = NativeArchive.open(database.absolutePath, staging.absolutePath)
        if (opened <= 0) throw ArchiveFailure("Io")
        if (closed.get()) { NativeArchive.close(opened); throw ArchiveFailure("InvalidHandle") }
        handle.set(opened)
        opened
    }
    private suspend fun <T> io(block: suspend (Long) -> T): T {
        val captured = epoch.get()
        return withContext(Dispatchers.IO) {
            try {
                val id = owner()
                currentCoroutineContext().ensureActive()
                if (closed.get()) throw ArchiveFailure("InvalidHandle")
                if (epoch.get() != captured) throw ArchiveFailure("Cancelled")
                block(id)
            } catch (cancelled: kotlinx.coroutines.CancellationException) { throw cancelled }
            catch (failure: ArchiveFailure) { throw failure }
            catch (_: Exception) { throw ArchiveFailure("Io") }
        }
    }
    override suspend fun prepareExport(story: SavedStory): ArchivePrepared = io { id ->
        val request = JSONObject().put("story", story.story).put("branch", story.branch)
            .put("expected_revision", story.revision).toString().toByteArray(Charsets.UTF_8)
        if (request.size > 4096) throw ArchiveFailure("TooLarge")
        ArchiveNativeWire.prepared(NativeArchive.prepareExport(id, request)).also {
            if (it.preview.storyId != story.story || it.preview.branchHeads[story.branch] != story.revision)
                throw ArchiveFailure("Stale")
        }
    }
    override suspend fun prepareImport(bytes: ByteArray): ArchivePrepared = io { id ->
        if (bytes.size > MAX_ARCHIVE_BYTES) throw ArchiveFailure("TooLarge")
        ArchiveNativeWire.prepared(NativeArchive.prepareImport(id, bytes))
    }
    override suspend fun exportBytes(token: Long): ByteArray = io { id ->
        if (token <= 0) throw ArchiveFailure("InvalidToken")
        try { NativeArchive.exportBytes(id, token) }
        catch (failure: IllegalStateException) {
            throw ArchiveFailure(failure.message?.takeIf { it in ARCHIVE_ERRORS } ?: "Io")
        }.also { if (it.size !in 1..MAX_ARCHIVE_BYTES) throw ArchiveFailure("TooLarge") }
    }
    override suspend fun commitImport(token: Long): ArchiveImported = io { id ->
        if (token <= 0) throw ArchiveFailure("InvalidToken")
        ArchiveNativeWire.imported(NativeArchive.commitImport(id, token))
    }
    override fun cancel() {
        epoch.incrementAndGet()
        val id = handle.get()
        if (id != 0L) NativeArchive.cancel(id)
    }
    override fun close() {
        if (!closed.compareAndSet(false, true)) return
        cancel()
        cleanup.launch {
            try {
                allocation.withLock {
                    val id = handle.getAndSet(0)
                    if (id != 0L) NativeArchive.close(id)
                }
            } finally { cleanup.cancel() }
        }
    }
}

private val ARCHIVE_ERRORS = setOf("Malformed", "Unsupported", "Integrity", "TooLarge", "Conflict", "Cancelled",
    "Busy", "Full", "Database", "NotFound", "InvalidHandle", "InvalidToken", "Stale", "Io", "WorkspaceLimit", "Internal")

/** Native response validation only. Archive parsing/replay remains entirely in Rust. */
internal object ArchiveNativeWire {
    fun prepared(bytes: ByteArray): ArchivePrepared = decoded(bytes) { data ->
        data.keysExactly("token", "preview")
        val token = data.integer("token").also { require(it > 0) }
        val preview = data.getJSONObject("preview")
        preview.keysExactly("version", "story_id", "title", "root_branch", "branch_heads", "committed_turns", "bytes",
            "payload_sha256", "privacy_warning", "noncommitted_workflow_transferred")
        require(preview.integer("version") == 1L)
        val story = preview.identifier("story_id")
        val root = preview.identifier("root_branch")
        val headsObject = preview.getJSONObject("branch_heads")
        require(headsObject.length() in 1..32)
        val heads = headsObject.keys().asSequence().associateWith { branch ->
            require(validArchiveId(branch)); headsObject.integer(branch)
        }
        require(root in heads)
        val transferred = preview.get("noncommitted_workflow_transferred") as Boolean
        require(!transferred)
        val length = preview.integer("bytes").also { require(it in 1..MAX_ARCHIVE_BYTES.toLong()) }
        val hash = preview.text("payload_sha256", 64).also { require(it.matches(Regex("[a-f0-9]{64}"))) }
        ArchivePrepared(token, ArchivePreview(1, story, preview.text("title", 1024), root, heads,
            preview.count("committed_turns", 4096), length, hash, preview.text("privacy_warning", 4096), transferred))
    }
    fun imported(bytes: ByteArray): ArchiveImported = decoded(bytes) { data ->
        data.keysExactly("root", "branches", "committed_turns")
        val root = data.getJSONObject("root"); root.keysExactly("story", "branch")
        ArchiveImported(root.identifier("story"), root.identifier("branch"),
            data.count("branches", 32).also { require(it > 0) }, data.count("committed_turns", 4096))
    }
    private fun <T> decoded(bytes: ByteArray, block: (JSONObject) -> T): T {
        try {
            require(bytes.size in 1..16384)
            val text = Charsets.UTF_8.newDecoder().onMalformedInput(CodingErrorAction.REPORT)
                .onUnmappableCharacter(CodingErrorAction.REPORT).decode(ByteBuffer.wrap(bytes)).toString()
            val reply = JSONObject(text)
            require(reply.integer("version") == 1L)
            when (reply.get("status") as String) {
                "rejected" -> {
                    reply.keysExactly("version", "status", "error")
                    throw ArchiveFailure((reply.get("error") as String).takeIf { it in ARCHIVE_ERRORS } ?: "Internal")
                }
                "ok" -> { reply.keysExactly("version", "status", "data"); return block(reply.getJSONObject("data")) }
                else -> error("Invalid reply")
            }
        } catch (failure: ArchiveFailure) { throw failure }
        catch (_: Exception) { throw ArchiveFailure("Integrity") }
    }
    private fun JSONObject.keysExactly(vararg keys: String) { require(this.keys().asSequence().toSet() == keys.toSet()) }
    private fun JSONObject.integer(key: String): Long {
        val value = get(key); require(value is Int || value is Long)
        return (value as Number).toLong().also { require(it >= 0) }
    }
    private fun JSONObject.count(key: String, cap: Int) = integer(key).also { require(it <= cap) }.toInt()
    private fun JSONObject.text(key: String, cap: Int): String = (get(key) as String).also {
        require(it.isNotEmpty() && !it.contains('\u0000') && it.toByteArray(Charsets.UTF_8).size <= cap)
    }
    private fun JSONObject.identifier(key: String) = text(key, 64).also { require(validArchiveId(it)) }
}
private fun validArchiveId(value: String) = value.matches(Regex("[A-Za-z0-9_-]{1,64}"))

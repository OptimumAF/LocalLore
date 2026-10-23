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
import java.util.concurrent.atomic.AtomicReference

internal object NativeArchive {
    init { System.loadLibrary("locallore_android") }
    external fun open(database: String, stagingRoot: String): Long
    external fun prepareExport(handle: Long, request: ByteArray): ByteArray
    external fun prepareImport(handle: Long, bytes: ByteArray): ByteArray
    external fun exportBytes(handle: Long, token: Long): ByteArray
    external fun commitImport(handle: Long, token: Long): ByteArray
    external fun prepareDelete(handle: Long, request: ByteArray): ByteArray
    external fun commitDelete(handle: Long, token: Long): ByteArray
    external fun prepareBranchDelete(handle: Long, request: ByteArray): ByteArray
    external fun commitBranchDelete(handle: Long, token: Long): ByteArray
    external fun cancel(handle: Long)
    external fun close(handle: Long)
}

/** IO-only native work, separate from the Host wire. Paths never come from a picker or archive. */
internal class NativeArchiveGateway(context: Context) : ArchiveGateway, StoryDeletionGateway {
    private val app = context.applicationContext
    private val allocation = Mutex()
    private val handle = AtomicLong()
    private val closed = AtomicBoolean()
    private val epoch = AtomicLong()
    private val deletion = AtomicReference<StoryDeletionPrepared?>()
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
    private suspend fun <T> deleting(block: suspend () -> T): T = try { block() }
        catch (failure: ArchiveFailure) { throw StoryDeletionFailure(failure.category) }
    override suspend fun prepare(story: SavedStory): StoryDeletionPrepared = deleting {
        deletion.set(null)
        io { id ->
            val request = JSONObject().put("story", story.story).put("branch", story.branch)
                .put("expected_revision", story.revision).toString().toByteArray(Charsets.UTF_8)
            if (request.size > 4096) throw ArchiveFailure("TooLarge")
            ArchiveNativeWire.deletionPrepared(NativeArchive.prepareDelete(id, request)).also {
                if (it.preview.storyId != story.story || it.preview.rootBranch != story.branch ||
                    it.preview.branchHeads[story.branch] != story.revision || it.preview.title != story.title)
                    throw ArchiveFailure("Stale")
                deletion.set(it)
            }
        }
    }
    override suspend fun commit(token: Long): StoryDeleted = deleting {
        val prepared = deletion.get() ?: throw ArchiveFailure("InvalidToken")
        if (prepared.token != token) throw ArchiveFailure("InvalidToken")
        if (!deletion.compareAndSet(prepared, null)) throw ArchiveFailure("InvalidToken")
        io { id ->
            ArchiveNativeWire.deleted(NativeArchive.commitDelete(id, token)).also {
                if (it.storyId != prepared.preview.storyId || it.deletedBranches != prepared.preview.rows["branches"] ||
                    it.deletedTurns != prepared.preview.rows["turns"]) throw ArchiveFailure("Integrity")
            }
        }
    }
    override fun cancel() {
        deletion.set(null)
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
    fun deletionPrepared(bytes: ByteArray): StoryDeletionPrepared = decoded(bytes, 65536) { data ->
        data.keysExactly("token", "preview")
        val token = data.integer("token").also { require(it > 0) }
        val p = data.getJSONObject("preview")
        p.keysExactly("version", "story_id", "title", "root_branch", "branch_heads", "committed_turns", "draft_turns",
            "noncommitted_turns", "derived_packets", "rows", "privacy_warning")
        val version = p.integer("version").also { require(it in 1..2) }
        val root = p.identifier("root_branch")
        val h = p.getJSONObject("branch_heads")
        require(h.length() in 1..256)
        val heads = h.keys().asSequence().associateWith { require(validArchiveId(it)); h.integer(it) }
        require(root in heads)
        val r = p.getJSONObject("rows")
        val tables = listOf("derived_memory", "event_witnesses", "accepted_events", "turns", "branch_projections",
            "branch_entities", "entities", "branches", "stories") + if (version == 2L) listOf("branch_retention") else emptyList()
        r.keysExactly(*tables.toTypedArray())
        val rows = r.keys().asSequence().associateWith { r.integer(it) }
        val committed = p.integer("committed_turns"); val noncommitted = p.integer("noncommitted_turns")
        val drafts = p.integer("draft_turns"); val derived = p.integer("derived_packets")
        require(rows.getValue("stories") == 1L && rows.getValue("branches") == heads.size.toLong())
        require(committed <= rows.getValue("turns") && noncommitted == rows.getValue("turns") - committed)
        require(drafts <= noncommitted && derived == rows.getValue("derived_memory"))
        StoryDeletionPrepared(token, StoryDeletionPreview(version.toInt(), p.identifier("story_id"), p.text("title", 1024),
            root, heads, committed, drafts, noncommitted, derived, rows, p.text("privacy_warning", 4096)))
    }
    fun deleted(bytes: ByteArray): StoryDeleted = decoded(bytes) { data ->
        data.keysExactly("story_id", "deleted_branches", "deleted_turns")
        StoryDeleted(data.identifier("story_id"), data.integer("deleted_branches").also { require(it in 1..256) },
            data.integer("deleted_turns"))
    }
    fun prepared(bytes: ByteArray): ArchivePrepared = decoded(bytes) { data ->
        data.keysExactly("token", "preview")
        val token = data.integer("token").also { require(it > 0) }
        val preview = data.getJSONObject("preview")
        val version = preview.integer("version").also { require(it in 1..2) }
        val fields = listOf("version", "story_id", "title", "root_branch", "branch_heads", "committed_turns", "bytes",
            "payload_sha256", "privacy_warning", "noncommitted_workflow_transferred") +
            if (version == 2L) listOf("retired_branch_ids") else emptyList()
        preview.keysExactly(*fields.toTypedArray())
        val story = preview.identifier("story_id")
        val root = preview.identifier("root_branch")
        val headsObject = preview.getJSONObject("branch_heads")
        require(headsObject.length() in 1..32)
        val heads = headsObject.keys().asSequence().associateWith { branch ->
            require(validArchiveId(branch)); headsObject.integer(branch)
        }
        require(root in heads)
        val retired = if (version == 2L) {
            val ids = preview.getJSONArray("retired_branch_ids")
            require(ids.length() in 1..256)
            (0 until ids.length()).map { (ids.get(it) as String).also { id -> require(validArchiveId(id)) } }
                .also { idsList ->
                    require(idsList.zipWithNext().all { (a,b) -> a < b } && root !in idsList)
                    require((heads.keys + idsList).size <= 256)
                }
        } else emptyList()
        val transferred = preview.get("noncommitted_workflow_transferred") as Boolean
        require(!transferred)
        val length = preview.integer("bytes").also { require(it in 1..MAX_ARCHIVE_BYTES.toLong()) }
        val hash = preview.text("payload_sha256", 64).also { require(it.matches(Regex("[a-f0-9]{64}"))) }
        ArchivePrepared(token, ArchivePreview(version.toInt(), story, preview.text("title", 1024), root, heads,
            preview.count("committed_turns", 4096), length, hash, preview.text("privacy_warning", 4096), transferred, retired))
    }
    fun imported(bytes: ByteArray): ArchiveImported = decoded(bytes) { data ->
        data.keysExactly("root", "branches", "committed_turns")
        val root = data.getJSONObject("root"); root.keysExactly("story", "branch")
        ArchiveImported(root.identifier("story"), root.identifier("branch"),
            data.count("branches", 32).also { require(it > 0) }, data.count("committed_turns", 4096))
    }
    private fun <T> decoded(bytes: ByteArray, cap: Int = 16384, block: (JSONObject) -> T): T {
        try {
            require(bytes.size in 1..cap)
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

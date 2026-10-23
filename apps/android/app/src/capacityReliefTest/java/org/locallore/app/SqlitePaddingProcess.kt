/* Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0 */
package org.locallore.app

import android.database.sqlite.SQLiteDatabase
import android.database.sqlite.SQLiteFullException
import android.os.Build
import android.os.Looper
import androidx.test.platform.app.InstrumentationRegistry
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.withContext
import org.junit.runners.model.MultipleFailureException
import java.io.ByteArrayOutputStream
import java.io.File
import java.nio.ByteBuffer
import java.security.MessageDigest
import java.util.concurrent.TimeUnit
import java.util.concurrent.atomic.AtomicBoolean
import java.util.concurrent.atomic.AtomicInteger

internal object PaddingFormat {
    const val MARKER = ".capacity-padding-owner-v2"
    const val OWNER_FORMAT = "locallore-capacity-padding-v2"
    const val SCHEMA = "c05ced1f0439fb767f97d2ff93a34ef44eb6fbc27da6814a75fad455fb0b2c17"
    const val INITIAL_PAGES = 17
    const val EXPECTED_ROWS = 14
    const val FREED_PAGES = 15
    const val TABLE = "locallore_capacity_pad_v1"
    const val CREATE = "CREATE TABLE locallore_capacity_pad_v1 (id INTEGER PRIMARY KEY, owner TEXT NOT NULL, payload BLOB NOT NULL)"
    const val INSERT = "INSERT INTO locallore_capacity_pad_v1 (owner,payload) VALUES (?,zeroblob(3500))"
}

/** Each helper closes SQL and exits before the parent can resume any Rust call. */
internal class PaddingOwner(private val database: File, private val token: String) {
    companion object {
        private val processOwnershipClean = AtomicBoolean(true)
        fun ownershipKnown() = processOwnershipClean.get()
    }
    var restored = true
        private set
    private var attempted = false
    private var unknownProcess = false
    val hasUnknownOwnership: Boolean get() = unknownProcess
    private var baseline: String? = null
    private var filled = false
    private var ownedProcess: Process? = null
    private var ownedReaders = emptyList<Thread>()
    suspend fun fill() {
        check(!attempted && restored)
        attempted = true; restored = false
        val result = invoke("fill")
        check(result[4].toIntOrNull() == PaddingFormat.EXPECTED_ROWS && result[5] == "32" && result[6] == "0") { "padding_fill_profile" }
        baseline = result[7]
        filled = true
    }
    suspend fun drop() {
        check(!unknownProcess) { "padding_child_cleanup_unknown" }
        val result = invoke("drop")
        check(result[4].toIntOrNull() in 0..64 && result[5].toIntOrNull() in 1..32 && result[6].toIntOrNull() in 0..32)
        if (filled) check(result[6].toIntOrNull()?.let { it > 0 } == true) { "padding_drop_freed_no_pages" }
        baseline?.let { check(it == result[7]) { "padding_baseline_changed" } }
        baseline = result[7]
        restored = true
    }
    private suspend fun invoke(mode: String): List<String> = withContext(Dispatchers.IO) {
        check(Looper.myLooper() != Looper.getMainLooper())
        check(Build.VERSION.SDK_INT >= 28 && !unknownProcess && ownershipKnown())
        val instrumentation = InstrumentationRegistry.getInstrumentation()
        val apks = listOf(instrumentation.context.applicationInfo.sourceDir, instrumentation.targetContext.applicationInfo.sourceDir)
        check(apks.all { File(it).isFile && File(it).canRead() && !File(it).canWrite() })
        val process = try {
            ProcessBuilder("/system/bin/app_process", "/", "org.locallore.app.SqlitePaddingProcess\$Main",
                mode, database.canonicalPath, token).also { it.environment()["CLASSPATH"] = apks.joinToString(":") }.start()
        } catch (_: Exception) {
            unknownProcess = true; processOwnershipClean.set(false)
            throw IllegalStateException("padding_spawn_failed")
        }
        ownedProcess = process
        val output = ByteArrayOutputStream()
        val guard = Any()
        val total = AtomicInteger()
        val overflow = AtomicBoolean()
        val readFailed = AtomicBoolean()
        var readers = emptyList<Thread>()
        val failures = mutableListOf<Throwable>()
        var result: List<String>? = null
        var exited = false
        var knownRefusal = false
        try {
            readers = listOf(process.inputStream, process.errorStream).mapIndexed { index, stream ->
                Thread({
                    try {
                        val bytes = ByteArray(512)
                        while (true) {
                            val count = stream.read(bytes)
                            if (count < 0) break
                            if (total.addAndGet(count) > 8192) { overflow.set(true); break }
                            if (index == 0) synchronized(guard) { output.write(bytes, 0, count) }
                        }
                    } catch (_: Exception) { readFailed.set(true) }
                }, "locallore-padding-pipe-$index").also { it.isDaemon = true }
            }
            ownedReaders = readers
            readers.forEach { it.start() }
            process.outputStream.close()
            exited = process.waitFor(12, TimeUnit.SECONDS)
            check(exited) { "padding_child_deadline" }
            readers.forEach { it.join(1_000) }
            check(readers.none { it.isAlive } && !overflow.get() && !readFailed.get()) { "padding_pipe_unknown" }
            val exit = process.exitValue()
            knownRefusal = exit in 71..73 // These fixed stages precede any owned padding write.
            check(exit == 0) { "padding_child_exit_${exit.coerceIn(-1, 255)}" }
            val text = synchronized(guard) { output.toByteArray().toString(Charsets.US_ASCII) }
            val lines = text.lineSequence().filter { it.isNotBlank() }.toList()
            check(lines.size == 1) { "padding_terminal_protocol" }
            val fields = lines.single().split(' ')
            check(fields.size == 8 && fields[0] == if (mode == "fill") "FILLED" else "DROPPED") { "padding_terminal_protocol" }
            check(fields[1] == token && fields[2].toIntOrNull()?.let { it > 0 && it != android.os.Process.myPid() } == true)
            check(fields[3].toIntOrNull() == android.os.Process.myUid()) { "padding_child_uid" }
            check(fields[7] == PaddingFormat.SCHEMA) { "padding_schema_digest" }
            if (mode == "fill") {
                check(fields[4].toIntOrNull() == PaddingFormat.EXPECTED_ROWS && fields[5] == "32" && fields[6] == "0") { "padding_fill_profile" }
            } else {
                check(fields[4].toIntOrNull() in 0..64 && fields[5].toIntOrNull() in 1..32 && fields[6].toIntOrNull() in 0..32)
                if (filled) check(fields[6].toIntOrNull()?.let { it > 0 } == true) { "padding_drop_freed_no_pages" }
                if (fields[4] != "0") check(fields[4].toIntOrNull() == PaddingFormat.EXPECTED_ROWS &&
                    fields[5] == "32" && fields[6].toIntOrNull() == PaddingFormat.FREED_PAGES) { "padding_drop_profile" }
            }
            result = fields
        } catch (failure: Throwable) { failures += failure }
        finally {
            try {
                if (!exited) { process.destroy(); exited = process.waitFor(1, TimeUnit.SECONDS) }
                if (!exited) { process.destroyForcibly(); exited = process.waitFor(2, TimeUnit.SECONDS) }
                if (exited) {
                    readers.forEach { if (it.isAlive) it.join(1_000) }
                    if (readers.none { it.isAlive }) {
                        listOf(process.inputStream, process.errorStream, process.outputStream).forEach {
                            try { it.close() } catch (_: Exception) { }
                        }
                    }
                }
                unknownProcess = !exited || process.isAlive || readers.any { it.isAlive } ||
                    readFailed.get() || overflow.get() || (result == null && !knownRefusal)
                if (!unknownProcess) { ownedProcess = null; ownedReaders = emptyList() }
                if (unknownProcess) processOwnershipClean.set(false)
                check(!unknownProcess) { "padding_child_cleanup_unknown" }
            } catch (failure: Throwable) {
                unknownProcess = true; processOwnershipClean.set(false); failures += failure
            }
        }
        MultipleFailureException.assertEmpty(failures)
        checkNotNull(result)
    }
}

/** The nested static main is absent from ordinary test discovery and never loads Rust. */
class SqlitePaddingProcess {
    @android.annotation.TargetApi(28)
    object Main {
        @JvmStatic fun main(arguments: Array<String>) {
            val finished = AtomicBoolean(false)
            Thread({ Thread.sleep(30_000); if (!finished.get()) kotlin.system.exitProcess(74) },
                "locallore-padding-lease").also { it.isDaemon = true; it.start() }
            var code = 71 // Fixed stage only: 71 input,72 path/marker,73 baseline,75 SQL,76 check,77 close.
            var database: SQLiteDatabase? = null
            try {
                check(Build.VERSION.SDK_INT >= 28 && arguments.size == 3 && arguments[0] in setOf("fill", "drop"))
                val mode = arguments[0]
                val path = File(arguments[1])
                val token = arguments[2]
                code = 72
                check(token.matches(Regex("[0-9a-f]{32}")))
                check(path.isAbsolute && path.canonicalFile == path.absoluteFile && path.isFile)
                check(path.name == "stories.sqlite3" && path.parentFile?.name == "workspace-v1")
                val root = checkNotNull(path.parentFile?.parentFile)
                check(root.name.matches(Regex("synthetic-capacity-relief-v3-[0-9a-f-]{36}")))
                check(root.parentFile?.name == "no_backup" && root.parentFile?.parentFile?.name == "org.locallore.app.capacityreliefv3")
                val marker = File(root, PaddingFormat.MARKER)
                check(marker.isFile && marker.canonicalFile == marker.absoluteFile && marker.length() <= 192)
                val ownership = marker.readText(Charsets.US_ASCII).split('\n')
                check(ownership.size in 3..4 && ownership.last().isEmpty())
                check(ownership[0] == PaddingFormat.OWNER_FORMAT && ownership[1] == token)
                val knownBaseline = if (ownership.size == 4) ownership[2].also { check(it == PaddingFormat.SCHEMA) } else null
                fun scalar(db: SQLiteDatabase, query: String): Long = db.rawQuery(query, null).use { check(it.moveToFirst()); it.getLong(0) }
                fun identity(db: SQLiteDatabase) {
                    check(scalar(db, "PRAGMA application_id") == 0x4c4c4f52L && scalar(db, "PRAGMA user_version") == 3L)
                    check(scalar(db, "PRAGMA page_size") == 4096L && scalar(db, "PRAGMA auto_vacuum") == 0L)
                    db.rawQuery("PRAGMA journal_mode", null).use { check(it.moveToFirst() && it.getString(0) == "delete") }
                    val contracts = listOf("locallore-storage-v1", "locallore-storage-v2-derived-memory",
                        "locallore-storage-v3-branch-retention")
                    db.rawQuery("SELECT version,contract FROM schema_migrations ORDER BY version", null).use { rows ->
                        for ((index, contract) in contracts.withIndex()) {
                            check(rows.moveToNext() && rows.getLong(0) == index + 1L && rows.getString(1) == contract)
                        }
                        check(!rows.moveToNext())
                    }
                    db.rawQuery("PRAGMA quick_check", null).use { check(it.moveToFirst() && it.getString(0) == "ok" && !it.moveToNext()) }
                    db.rawQuery("PRAGMA foreign_key_check", null).use { check(!it.moveToFirst()) }
                }
                fun schema(db: SQLiteDatabase): String {
                    val digest = MessageDigest.getInstance("SHA-256")
                    db.rawQuery("SELECT type,name,tbl_name,sql FROM sqlite_master WHERE name NOT GLOB 'sqlite_*' AND name<>'locallore_capacity_pad_v1' ORDER BY type,name,tbl_name", null).use { rows ->
                        while (rows.moveToNext()) for (column in 0..3) {
                            val bytes = rows.getString(column)?.toByteArray(Charsets.UTF_8)
                            digest.update(if (bytes == null) 0.toByte() else 1.toByte())
                            if (bytes != null) { digest.update(ByteBuffer.allocate(4).putInt(bytes.size).array()); digest.update(bytes) }
                        }
                    }
                    return digest.digest().joinToString("") { "%02x".format(it.toInt() and 255) }
                }
                fun padSql(db: SQLiteDatabase): String? = db.rawQuery("SELECT type,tbl_name,sql FROM sqlite_master WHERE name='locallore_capacity_pad_v1'", null)
                    .use {
                        if (!it.moveToFirst()) null else {
                            check(it.getString(0) == "table" && it.getString(1) == PaddingFormat.TABLE && it.getString(2) == PaddingFormat.CREATE)
                            check(!it.moveToNext()); PaddingFormat.CREATE
                        }
                    }
                fun rows(db: SQLiteDatabase): Int = db.rawQuery("SELECT count(*),coalesce(min(id),0),coalesce(max(id),0),coalesce(sum(CASE WHEN owner=? AND payload=zeroblob(3500) THEN 1 ELSE 0 END),0) FROM locallore_capacity_pad_v1", arrayOf(token)).use {
                    check(it.moveToFirst())
                    val count = it.getInt(0)
                    check(count in 0..64 && it.getInt(1) == if (count == 0) 0 else 1)
                    check(it.getInt(2) == count && it.getInt(3) == count)
                    count
                }
                code = 73
                val readOnlyBaseline = SQLiteDatabase.openDatabase(path, SQLiteDatabase.OpenParams.Builder()
                    .setOpenFlags(SQLiteDatabase.OPEN_READONLY or SQLiteDatabase.NO_LOCALIZED_COLLATORS).build()).use {
                    identity(it)
                    val digest = schema(it)
                    check(digest == PaddingFormat.SCHEMA)
                    if (padSql(it) != null) {
                        check(mode == "drop" && knownBaseline == digest)
                        check(rows(it) == PaddingFormat.EXPECTED_ROWS)
                    } else if (mode == "fill") {
                        check(scalar(it, "PRAGMA page_count") == PaddingFormat.INITIAL_PAGES.toLong() && scalar(it, "PRAGMA freelist_count") == 0L)
                    }
                    digest
                }
                val opened = SQLiteDatabase.openDatabase(path, SQLiteDatabase.OpenParams.Builder()
                    .setOpenFlags(SQLiteDatabase.OPEN_READWRITE or SQLiteDatabase.NO_LOCALIZED_COLLATORS)
                    .setJournalMode("DELETE").build())
                database = opened
                identity(opened)
                check(scalar(opened, "PRAGMA max_page_count=32") == 32L)
                val before = schema(opened)
                check(before == readOnlyBaseline && before == PaddingFormat.SCHEMA)
                knownBaseline?.let { check(before == it) }
                if (padSql(opened) != null) {
                    check(mode == "drop" && knownBaseline == before)
                    check(rows(opened) == PaddingFormat.EXPECTED_ROWS)
                }
                var count = 0
                code = 75
                if (mode == "fill") {
                    check(padSql(opened) == null)
                    check(scalar(opened, "PRAGMA page_count") == PaddingFormat.INITIAL_PAGES.toLong() && scalar(opened, "PRAGMA freelist_count") == 0L)
                    marker.writeText(PaddingFormat.OWNER_FORMAT + "\n" + token + "\n" + before + "\n", Charsets.US_ASCII)
                    opened.execSQL(PaddingFormat.CREATE)
                    var full = false
                    for (attempt in 0..64) {
                        try { opened.execSQL(PaddingFormat.INSERT, arrayOf(token)); count++ }
                        catch (_: SQLiteFullException) { full = true; break }
                    }
                    check(full && count == PaddingFormat.EXPECTED_ROWS)
                    check(padSql(opened) == PaddingFormat.CREATE && rows(opened) == count)
                } else {
                    padSql(opened)?.let {
                        check(knownBaseline != null && it == PaddingFormat.CREATE)
                        count = rows(opened)
                        opened.execSQL("DROP TABLE locallore_capacity_pad_v1")
                    }
                }
                code = 76
                identity(opened)
                check(schema(opened) == before)
                val pages = scalar(opened, "PRAGMA page_count")
                val free = scalar(opened, "PRAGMA freelist_count")
                if (mode == "fill") check(pages == 32L && free == 0L) else {
                    check(padSql(opened) == null)
                    if (count != 0) check(count == PaddingFormat.EXPECTED_ROWS && pages == 32L && free == PaddingFormat.FREED_PAGES.toLong())
                }
                check(pages in 1L..32L && free in 0L..32L)
                code = 77
                opened.close(); database = null
                // Acknowledgement follows close, never a held transaction/connection.
                println("${if (mode == "fill") "FILLED" else "DROPPED"} $token ${android.os.Process.myPid()} ${android.os.Process.myUid()} $count $pages $free $before")
                System.out.flush()
                code = 0
            } catch (_: Throwable) { /* No SQL, paths, token, exception or story diagnostics. */ }
            finally {
                try { database?.close() } catch (_: Throwable) { }
                finished.set(true)
            }
            kotlin.system.exitProcess(code)
        }
    }
}

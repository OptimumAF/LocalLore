/* Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0 */
package org.locallore.app

import android.content.Context
import android.content.ContextWrapper
import android.database.sqlite.SQLiteDatabase
import android.os.Looper
import android.os.Build
import androidx.compose.runtime.collectAsState
import androidx.compose.runtime.getValue
import androidx.compose.ui.test.*
import androidx.compose.ui.test.junit4.createComposeRule
import androidx.lifecycle.ViewModel
import androidx.lifecycle.ViewModelProvider
import androidx.lifecycle.ViewModelStore
import androidx.test.ext.junit.runners.AndroidJUnit4
import androidx.test.filters.SdkSuppress
import androidx.test.platform.app.InstrumentationRegistry
import kotlinx.coroutines.CompletableDeferred
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.NonCancellable
import kotlinx.coroutines.delay
import kotlinx.coroutines.runBlocking
import kotlinx.coroutines.withContext
import kotlinx.coroutines.withTimeout
import org.json.JSONObject
import org.junit.Assert.*
import org.junit.Rule
import org.junit.Test
import org.junit.runner.RunWith
import org.junit.runners.model.MultipleFailureException
import org.locallore.app.ui.LocalLoreScreen
import java.io.File
import java.util.UUID
import java.util.concurrent.CopyOnWriteArrayList
import java.util.concurrent.TimeUnit
import java.util.concurrent.atomic.AtomicBoolean
import java.io.ByteArrayOutputStream
import java.util.concurrent.atomic.AtomicInteger

/** Real second-connection contention; no synthesized error, gameplay SQL, or fault hook. */
@RunWith(AndroidJUnit4::class)
@SdkSuppress(minSdkVersion = 28)
class SqliteContentionInstrumentedTest {
    @get:Rule val compose = createComposeRule()

    /** Only an owned distinct process touches Android's separate SQLite library. */
    private class Writer(private val path: File) {
        private var child: Process? = null
        private var token = ""
        private val output = ByteArrayOutputStream()
        private val guard = Any()
        private val total = AtomicInteger()
        private val overflow = AtomicBoolean()
        private val readFailed = AtomicBoolean()
        private var readers = emptyList<Thread>()
        private var ready = ""
        private fun outputText() = synchronized(guard) { output.toByteArray().toString(Charsets.US_ASCII) }
        private fun worker() = check(Looper.myLooper() != Looper.getMainLooper())
        suspend fun acquire() = withContext(Dispatchers.IO) {
            worker()
            check(Build.VERSION.SDK_INT >= 28) { "writer_requires_api_28" }
            check(child == null && path.isFile)
            val instrumentation = InstrumentationRegistry.getInstrumentation()
            val apks = listOf(instrumentation.context.applicationInfo.sourceDir,
                instrumentation.targetContext.applicationInfo.sourceDir)
            check(apks.all { File(it).isFile && File(it).canRead() && !File(it).canWrite() })
            token = UUID.randomUUID().toString().replace("-", "")
            val process = try {
                ProcessBuilder("/system/bin/app_process", "/", "org.locallore.app.SqliteWriterProcess",
                    path.canonicalPath, token).also {
                    it.environment()["CLASSPATH"] = apks.joinToString(":")
                }.start()
            } catch (_: Exception) { throw AssertionError("owned_writer_spawn_failed") }
            child = process
            output.reset(); total.set(0); overflow.set(false); readFailed.set(false)
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
                    }, "locallore-writer-pipe-$index").also { it.isDaemon = true }
                }
                readers.forEach { it.start() }
                val deadline = System.nanoTime() + TimeUnit.SECONDS.toNanos(8)
                while (!outputText().contains("\n")) {
                    check(!overflow.get() && !readFailed.get()) { "owned_writer_pipe_failed" }
                    check(process.isAlive) { "owned_writer_not_ready_exit_${process.exitValue().coerceIn(-1, 255)}" }
                    check(System.nanoTime() < deadline) { "owned_writer_ready_timeout" }
                    delay(5)
                }
                ready = outputText().substringBefore('\n').trimEnd('\r')
                val fields = ready.split(' ')
                check(fields.size == 4 && fields[0] == "READY" && fields[1] == token) { "owned_writer_ready_protocol" }
                val pid = fields[2].toIntOrNull()
                check(pid != null && pid > 0 && pid != android.os.Process.myPid()) { "writer_must_be_distinct_process" }
                check(fields[3].toIntOrNull() == android.os.Process.myUid()) { "writer_must_inherit_app_uid" }
                check(process.isAlive && !overflow.get() && !readFailed.get()) { "owned_writer_ready_not_live" }
            } catch (failure: Throwable) {
                val failures = mutableListOf(failure)
                try { release() } catch (cleanup: Throwable) { failures += cleanup }
                MultipleFailureException.assertEmpty(failures)
                throw failure
            }
        }
        suspend fun assertHeld() = withContext(Dispatchers.IO) {
            worker()
            check(child?.isAlive == true && ready.isNotEmpty() && !overflow.get() && !readFailed.get()) { "owned_writer_lease_not_live" }
        }
        suspend fun release() = withContext(Dispatchers.IO) {
            worker()
            val process = child ?: return@withContext
            var requested = false
            var exited = false
            var stopped = false
            try {
                try {
                    process.outputStream.write(("RELEASE $token\n").toByteArray(Charsets.US_ASCII))
                    process.outputStream.flush(); process.outputStream.close()
                    requested = true
                } catch (_: Exception) { /* Still reap the exact owned handle below. */ }
                exited = process.waitFor(4, TimeUnit.SECONDS)
                if (!exited) {
                    stopped = true; process.destroy()
                    exited = process.waitFor(1, TimeUnit.SECONDS)
                }
                if (!exited) {
                    stopped = true; process.destroyForcibly()
                    exited = process.waitFor(2, TimeUnit.SECONDS)
                }
            } finally {
                if (!exited && process.isAlive) {
                    process.destroyForcibly()
                    exited = process.waitFor(2, TimeUnit.SECONDS)
                }
                if (exited) {
                    readers.forEach { it.join(1_000) }
                    // Do not acquire a pipe lock from a reader whose cleanup is
                    // still unknown; fail below after bounded joins instead.
                    if (readers.none { it.isAlive }) {
                        listOf(process.inputStream, process.errorStream, process.outputStream).forEach {
                            try { it.close() } catch (_: Exception) { }
                        }
                        child = null
                    }
                }
            }
            check(exited && !process.isAlive && readers.none { it.isAlive }) { "owned_writer_cleanup_unknown" }
            check(requested && !stopped && process.exitValue() == 0) { "owned_writer_release_exit_${process.exitValue().coerceIn(-1, 255)}" }
            check(!overflow.get() && !readFailed.get()) { "owned_writer_pipe_failed" }
            check(outputText().lineSequence().filter { it.isNotBlank() }.toList() ==
                listOf(ready, "RELEASED $token")) { "owned_writer_release_protocol" }
        }
    }
    private data class Reply(val op: String, val turn: String?, val status: String, val error: String?)
    private class LockedReplies(val actual: NativeWorkspaceTransport, val writer: Writer) : WorkspaceTransport {
        val replies = CopyOnWriteArrayList<Reply>()
        val submits = CopyOnWriteArrayList<JSONObject>()
        val exchanges = AtomicInteger()
        var lockBefore: String? = null
        var holdReady = false
        val held = CompletableDeferred<Unit>()
        val delivery = CompletableDeferred<Unit>()
        override suspend fun exchange(command: JSONObject): JSONObject {
            exchanges.incrementAndGet()
            try {
                val op = command.getString("op")
                val turn = if (op == "submit") command.getJSONObject("request").getString("turn")
                    else command.optString("turn").takeUnless { it.isEmpty() }
                if (op == "submit") submits += JSONObject(command.toString())
                if (lockBefore == op) { lockBefore = null; writer.acquire() }
                val reply = actual.exchange(command)
                replies += Reply(op, turn, reply.getString("status"),
                    reply.optString("error").takeUnless { it.isEmpty() })
                if (op == "prepare" && holdReady) {
                    holdReady = false
                    assertEquals("ok", reply.getString("status"))
                    assertEquals("ready", reply.getJSONObject("data").getString("phase"))
                    writer.acquire()
                    held.complete(Unit)
                    // Only delivery of an actual completed JNI result is held.
                    withContext(NonCancellable) { delivery.await() }
                }
                return reply // Never replace or edit a native reply.
            } finally { exchanges.decrementAndGet() }
        }
        override fun close() = actual.close()
        fun count(op: String) = replies.count { it.op == op }
        fun busy(op: String) = replies.count { it.op == op && it.status == "rejected" && it.error == "Busy" }
        fun key() = submits.first().getJSONObject("request").getString("turn")
        fun assertOnlyOriginal() {
            assertTrue(submits.isNotEmpty())
            assertTrue(submits.all { it.toString() == submits.first().toString() })
            assertTrue(replies.filter { it.turn != null }.all { it.turn == key() })
        }
        suspend fun native(command: JSONObject): JSONObject {
            val reply = actual.exchange(command)
            assertEquals("ok", reply.getString("status"))
            return reply.getJSONObject("data")
        }
        suspend fun status(): JSONObject {
            val submit = submits.first()
            return native(JSONObject().put("op", "turn_status").put("session", submit.getString("session"))
                .put("scope", submit.getJSONObject("request").getJSONObject("scope")).put("turn", key()))
        }
    }
    private class Fixture(val context: Context) {
        val root = context.noBackupFilesDir.canonicalFile
        val database = File(root, "workspace-v1/stories.sqlite3")
        val writer = Writer(database)
        val replies = LockedReplies(NativeWorkspaceTransport(context), writer)
        val gateway = DurableGateway(replies)
        val owners = mutableListOf<ViewModelStore>()
        val additional = mutableListOf<DurableGateway>()
        fun model(): ShellViewModel {
            val owner = ViewModelStore().also { owners += it }
            return ViewModelProvider(owner, object : ViewModelProvider.Factory {
                @Suppress("UNCHECKED_CAST")
                override fun <T : ViewModel> create(modelClass: Class<T>): T = ShellViewModel(gateway) as T
            })[ShellViewModel::class.java]
        }
        suspend fun reopened(story: SavedStory): SavedSnapshot {
            withContext(Dispatchers.Main) { owners.forEach { it.clear() }; gateway.close() }
            released(database)
            val next = DurableGateway(NativeWorkspaceTransport(context)).also { additional += it }
            return withContext(Dispatchers.Main) { next.initialize(); next.resumeSaved(story) }
        }
    }
    private fun context(): Context {
        val actual = InstrumentationRegistry.getInstrumentation().targetContext
        val parent = actual.noBackupFilesDir.canonicalFile
        val root = File(parent, "synthetic-sqlite-contention-${UUID.randomUUID()}")
        check(root.mkdir() && root.canonicalFile.parentFile == parent)
        return object : ContextWrapper(actual) {
            override fun getApplicationContext(): Context = this
            override fun getNoBackupFilesDir(): File = root
        }
    }
    private suspend fun fixture(block: suspend (Fixture) -> Unit) {
        val f = Fixture(context())
        val failures = mutableListOf<Throwable>()
        suspend fun attempt(cleanup: suspend () -> Unit): Boolean = try { cleanup(); true }
            catch (failure: Throwable) { failures += failure; false }
        try { block(f) } catch (failure: Throwable) { failures += failure }
        withContext(NonCancellable) {
            // Release the real writer before any native cancellation/teardown.
            val unlocked = attempt { f.writer.release() }
            val ownersClosed = attempt {
                withContext(Dispatchers.Main) {
                    f.owners.forEach { it.clear() }; f.gateway.close(); f.additional.forEach { it.close() }
                }
            }
            // Fence presentation/cancel the pending owner before delivering any
            // held completion; cleanup must not race it into a fresh commit.
            f.replies.delivery.complete(Unit)
            val drained = attempt {
                withTimeout(8_000) { while (f.replies.exchanges.get() != 0) delay(5) }
            }
            val closed = if (unlocked && ownersClosed && drained) attempt {
                if (f.database.exists()) released(f.database)
            } else false
            if (closed) attempt {
                val parent = InstrumentationRegistry.getInstrumentation().targetContext.noBackupFilesDir.canonicalFile
                check(f.root.canonicalFile.parentFile == parent)
                check(f.root.deleteRecursively())
            }
        }
        MultipleFailureException.assertEmpty(failures)
    }
    private suspend fun failureBusy(block: suspend () -> Any?) {
        try { block(); fail("Expected actual Rust SQLite Busy") }
        catch (failure: WorkspaceFailure) { assertEquals("Busy", failure.category) }
    }
    private fun initial(saved: SavedSnapshot) {
        assertEquals(0L, saved.revision); assertEquals("You", saved.potionOwner); assertTrue(saved.messages.isEmpty())
    }
    private fun accepted(saved: SavedSnapshot) {
        assertEquals(1L, saved.revision); assertEquals("Not in your inventory", saved.potionOwner)
        assertEquals(2, saved.messages.size)
        assertEquals("You give 1 potion to mira.", saved.messages.single { !it.isPlayer }.text)
        assertEquals(0, saved.uncommittedDrafts)
    }
    private fun tag(name: String): SemanticsNodeInteraction {
        compose.onNodeWithTag("story-list").performScrollToNode(hasTestTag(name))
        return compose.onNodeWithTag(name)
    }
    private fun idle(model: ShellViewModel) {
        compose.waitUntil(10_000) { !model.state.value.busy }; compose.waitForIdle()
    }

    @Test fun actualSubmitBusyRetainsExactRequestAndRecoversAfterWriterRelease() = runBlocking {
        fixture { f ->
            withContext(Dispatchers.Main) {
                initial(f.gateway.initialize())
                f.replies.lockBefore = "submit"
                failureBusy { f.gateway.respond(DemoAction.GIVE_POTION, 0, DemoMode.ACCEPTED) }
                assertEquals(1, f.replies.busy("submit")); f.writer.assertHeld()
                initial(f.gateway.snapshot())
                failureBusy { f.gateway.recoverSaved() }
                assertEquals(2, f.replies.busy("submit")); f.writer.assertHeld()
                assertEquals(0, f.replies.count("prepare")); assertEquals(0, f.replies.count("commit"))
                f.replies.assertOnlyOriginal()
                f.writer.release()
                accepted(f.gateway.recoverSaved())
                accepted(f.gateway.recoverSaved())
                assertEquals(3, f.replies.count("submit"))
                assertEquals(1, f.replies.count("prepare")); assertEquals(1, f.replies.count("commit"))
                f.replies.assertOnlyOriginal()
            }
            val saved = withContext(Dispatchers.Main) { f.gateway.snapshot() }
            accepted(f.reopened(checkNotNull(saved.selected)))
        }
    }

    @Test fun composedReadyCommitBusyBlocksNewTurnsUntilOriginalGiftRecoversAndReopens() = runBlocking {
        fixture { f ->
            val model = withContext(Dispatchers.Main) { f.model() }
            compose.setContent {
                val state by model.state.collectAsState()
                LocalLoreScreen(state, model::submit, model::setMode, model::cancel, model::reset,
                    onResume = model::resume, onRecover = model::recover)
            }
            idle(model)
            compose.runOnIdle { f.replies.lockBefore = "commit" }
            tag("give-potion").performClick(); idle(model)
            repeat(3) { attempt ->
                tag("notice").assertTextEquals(BUSY_NOTICE)
                tag("revision").assertTextEquals("Accepted revision \u00B7 0")
                tag("potion-owner").assertTextEquals("Healing potion \u00B7 You")
                tag("give-potion").assertIsNotEnabled(); tag("try-ability").assertIsNotEnabled()
                tag("mode-menu").assertIsNotEnabled(); tag("recover-save").assertIsEnabled()
                compose.runOnIdle {
                    assertTrue(model.state.value.recoveryRequired); assertTrue(model.state.value.messages.isEmpty())
                    model.submit(DemoAction.GIVE_POTION) // Retained callback also remains fenced.
                }
                assertEquals(attempt + 1, f.replies.busy("commit")); f.writer.assertHeld()
                assertEquals("ready", withContext(Dispatchers.Main) { f.replies.status() }.getString("phase"))
                assertEquals(1, f.replies.count("submit")); assertEquals(1, f.replies.count("prepare"))
                if (attempt < 2) { tag("recover-save").performClick(); idle(model) }
            }
            f.writer.release()
            tag("recover-save").performClick(); idle(model)
            tag("revision").assertTextEquals("Accepted revision \u00B7 1")
            tag("potion-owner").assertTextEquals("Healing potion \u00B7 Not in your inventory")
            compose.runOnIdle {
                assertFalse(model.state.value.recoveryRequired); assertEquals(2, model.state.value.messages.size)
            }
            assertEquals(4, f.replies.count("commit")); assertEquals(1, f.replies.count("prepare"))
            f.replies.assertOnlyOriginal()
            val saved = withContext(Dispatchers.Main) { f.gateway.recoverSaved() }
            accepted(saved)
            accepted(f.reopened(checkNotNull(saved.selected)))
        }
    }

    @Test fun actualCancelBusyRetriesCancellationThenLateReadyReplyCannotSpendInNewStory() = runBlocking {
        fixture { f ->
            val model = withContext(Dispatchers.Main) { f.model() }
            withTimeout(8_000) { while (model.state.value.busy) delay(5) }
            val original = checkNotNull(model.state.value.selectedStory)
            withContext(Dispatchers.Main) { f.replies.holdReady = true; model.submit(DemoAction.GIVE_POTION) }
            withTimeout(8_000) { f.replies.held.await() }
            withContext(Dispatchers.Main) { model.cancel() }
            withTimeout(8_000) { while (model.state.value.busy) delay(5) }
            withContext(Dispatchers.Main) {
                assertTrue(model.state.value.recoveryRequired); assertEquals(BUSY_NOTICE, model.state.value.notice)
                assertEquals(0L, model.state.value.revision); assertTrue(model.state.value.messages.isEmpty())
                assertEquals(1, f.replies.busy("cancel")); f.writer.assertHeld()
                model.recover()
            }
            withTimeout(8_000) { while (model.state.value.busy) delay(5) }
            assertEquals(2, f.replies.busy("cancel")); f.writer.assertHeld()
            assertEquals(0, f.replies.count("commit"))
            f.writer.release()
            withContext(Dispatchers.Main) { model.recover() }
            withTimeout(8_000) { while (model.state.value.busy) delay(5) }
            withContext(Dispatchers.Main) {
                assertFalse(model.state.value.recoveryRequired)
                assertEquals(0L, model.state.value.revision); assertEquals("You", model.state.value.potionOwner)
                assertEquals("cancelled", f.replies.status().getString("phase"))
                model.reset()
            }
            withTimeout(8_000) { while (model.state.value.busy) delay(5) }
            assertNotEquals(original.story, checkNotNull(model.state.value.selectedStory).story)
            f.replies.delivery.complete(Unit)
            withTimeout(8_000) { while (f.replies.exchanges.get() != 0) delay(5) }
            withContext(Dispatchers.Main) {
                assertEquals(0L, model.state.value.revision); assertEquals("You", model.state.value.potionOwner)
                assertTrue(model.state.value.messages.isEmpty()); assertFalse(model.state.value.recoveryRequired)
                assertEquals(0, f.replies.count("commit")); assertEquals(3, f.replies.count("cancel"))
                f.replies.assertOnlyOriginal()
                model.resume(original)
            }
            withTimeout(8_000) { while (model.state.value.busy) delay(5) }
            val saved = withContext(Dispatchers.Main) { f.gateway.snapshot() }
            initial(saved); assertEquals(0, saved.uncommittedDrafts)
            initial(f.reopened(checkNotNull(saved.selected)))
        }
    }

    companion object {
        private const val BUSY_NOTICE = "The local engine is busy. Wait briefly, then retry recovery. Saved progress is retained."
        private suspend fun released(path: File) = withContext(Dispatchers.IO) {
            withTimeout(8_000) {
                while (true) {
                    val handles = mutableListOf<Long>()
                    try {
                        repeat(4) { NativeWorkspace.open(path.absolutePath).let { if (it != 0L) handles += it } }
                        if (handles.size == 4) break
                    } finally { handles.forEach { NativeWorkspace.close(it) } }
                    delay(5)
                }
            }
        }
    }
}


/** Loaded only from the test APK by app_process; never initializes Rust or NativeWorkspace. */
@android.annotation.TargetApi(28)
object SqliteWriterProcess {
    @JvmStatic fun main(arguments: Array<String>) {
        val finished = AtomicBoolean(false)
        Thread({
            Thread.sleep(60_000)
            if (!finished.get()) kotlin.system.exitProcess(74)
        }, "locallore-writer-lease").also { it.isDaemon = true; it.start() }
        // Fixed stages are the only child failure diagnostics: 71 input/API,
        // 72 path, 73 baseline, 74 lease, 75 open, 76 reservation, 77 input,
        // 78 rollback/metadata, 79 close/recheck. No exception text is emitted.
        var code = 71
        var database: SQLiteDatabase? = null
        try {
            check(Build.VERSION.SDK_INT >= 28 && arguments.size == 2)
            code = 72
            val path = File(arguments[0])
            val token = arguments[1]
            check(token.matches(Regex("[0-9a-f]{32}")))
            check(path.isAbsolute && path.canonicalFile == path.absoluteFile && path.isFile)
            check(path.name == "stories.sqlite3" && path.parentFile?.name == "workspace-v1")
            val fixture = checkNotNull(path.parentFile?.parentFile)
            check(fixture.name.matches(Regex("synthetic-sqlite-contention-[0-9a-f-]{36}")))
            check(fixture.parentFile?.name == "no_backup" && fixture.parentFile?.parentFile?.name == "org.locallore.app")
            fun metadata(db: SQLiteDatabase): List<String> {
                fun scalar(pragma: String) = db.rawQuery(pragma, null).use { cursor ->
                    check(cursor.moveToFirst()); cursor.getString(0)
                }
                val identity = listOf(scalar("PRAGMA application_id"), scalar("PRAGMA user_version"),
                    scalar("PRAGMA journal_mode"))
                check(identity[0].toLongOrNull() == 0x4c4c4f52L && identity[1] == "1" && identity[2] == "delete")
                return identity + db.rawQuery("SELECT type,name,sql FROM sqlite_master ORDER BY type,name", null).use { cursor ->
                    buildList {
                        while (cursor.moveToNext()) add((0..2).joinToString("|") { cursor.getString(it).orEmpty() })
                    }
                }
            }
            fun readMetadata() = SQLiteDatabase.openDatabase(path,
                SQLiteDatabase.OpenParams.Builder().setOpenFlags(SQLiteDatabase.OPEN_READONLY or
                    SQLiteDatabase.NO_LOCALIZED_COLLATORS).build()).use { metadata(it) }
            code = 73
            val before = readMetadata()
            code = 75
            val opened = SQLiteDatabase.openDatabase(path,
                SQLiteDatabase.OpenParams.Builder().setOpenFlags(SQLiteDatabase.OPEN_READWRITE or
                    SQLiteDatabase.NO_LOCALIZED_COLLATORS).setJournalMode("DELETE").build())
            database = opened
            check(metadata(opened) == before)
            code = 76
            opened.beginTransactionNonExclusive()
            check(opened.inTransaction())
            println("READY $token ${android.os.Process.myPid()} ${android.os.Process.myUid()}")
            System.out.flush()
            code = 77
            val request = StringBuilder()
            while (request.length <= 80) {
                val next = System.`in`.read()
                if (next == -1 || next == 10) break
                check(next in 32..126)
                request.append(next.toChar())
            }
            check(request.isEmpty() || request.toString() == "RELEASE $token")
            // No writes and no setTransactionSuccessful: release is a rollback.
            code = 78
            opened.endTransaction()
            check(metadata(opened) == before)
            code = 79
            opened.close(); database = null
            check(readMetadata() == before)
            println("RELEASED $token")
            System.out.flush()
            code = 0
        } catch (_: Throwable) {
            // Neither native exception text, paths nor schema contents leave the child.
        } finally {
            database?.let { opened ->
                try { if (opened.inTransaction()) opened.endTransaction() } catch (_: Throwable) { }
                try { opened.close() } catch (_: Throwable) { }
            }
            finished.set(true)
        }
        kotlin.system.exitProcess(code)
    }
}

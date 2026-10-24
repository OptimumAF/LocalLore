/* Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0 */
package org.locallore.app

import android.content.Context
import android.content.ContextWrapper
import android.os.Looper
import androidx.test.ext.junit.runners.AndroidJUnit4
import androidx.test.platform.app.InstrumentationRegistry
import kotlinx.coroutines.CompletableDeferred
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.NonCancellable
import kotlinx.coroutines.async
import kotlinx.coroutines.delay
import kotlinx.coroutines.runBlocking
import kotlinx.coroutines.withContext
import kotlinx.coroutines.withTimeout
import org.json.JSONArray
import org.json.JSONObject
import org.junit.Assert.*
import org.junit.Test
import org.junit.runner.RunWith
import java.io.File
import java.util.UUID
import java.util.concurrent.CopyOnWriteArrayList
import java.util.concurrent.atomic.AtomicInteger

/** Actual production JNI/Host/SQLite and external owner; role outputs are synthetic, with no SDK. */
@RunWith(AndroidJUnit4::class)
class ExternalInferenceInstrumentedTest {
    private class Worker : LocalRoleWorker {
        val requests = CopyOnWriteArrayList<LocalInferenceRequest>()
        val roleStarted = CompletableDeferred<Unit>()
        val releaseRole = CompletableDeferred<Unit>()
        val engineClosing = CompletableDeferred<Unit>()
        val releaseEngine = CompletableDeferred<Unit>()
        val opens = AtomicInteger()
        val cancels = AtomicInteger()
        val drains = AtomicInteger()
        val roleCloses = AtomicInteger()
        val engineCloses = AtomicInteger()
        var holdRole = false
        var holdEngine = false
        var engineCloseKnown = true
        override suspend fun open(): LocalRoleEngine {
            offMain()
            opens.incrementAndGet()
            return object : LocalRoleEngine {
                override suspend fun start(request: LocalInferenceRequest): LocalRoleCall {
                    offMain()
                    requests += request
                    roleStarted.complete(Unit)
                    return object : LocalRoleCall {
                        override suspend fun await(): LocalRoleResult {
                            offMain()
                            if (holdRole) releaseRole.await()
                            return LocalRoleResult(true, response(request))
                        }
                        override fun cancel() {
                            offMain()
                            cancels.incrementAndGet()
                            releaseRole.complete(Unit)
                        }
                        override suspend fun drain(): Boolean {
                            offMain(); drains.incrementAndGet(); return true
                        }
                        override suspend fun close(): Boolean {
                            offMain(); roleCloses.incrementAndGet(); return true
                        }
                    }
                }
                override suspend fun close(): Boolean {
                    offMain()
                    engineClosing.complete(Unit)
                    if (holdEngine) releaseEngine.await()
                    engineCloses.incrementAndGet()
                    return engineCloseKnown
                }
            }
        }
    }
    private class Fixture(val worker: Worker) {
        val parent = InstrumentationRegistry.getInstrumentation().targetContext.noBackupFilesDir.canonicalFile
        val root = File(parent, "synthetic-external-${UUID.randomUUID()}").also {
            check(it.mkdir() && it.canonicalFile.parentFile == parent)
        }
        val context: Context = object : ContextWrapper(InstrumentationRegistry.getInstrumentation().targetContext) {
            override fun getApplicationContext(): Context = this
            override fun getNoBackupFilesDir(): File = root
        }
        val database = File(root, "workspace-v1/stories.sqlite3")
        val owner = LocalInferenceOwner(profile().toString().toByteArray(Charsets.UTF_8), worker,
            limits = LocalInferenceLimits(turnMs = 8_000, cleanupMs = 1_000, pollMs = 5))
        val actual = NativeWorkspaceTransport(context, owner)
        val calls = CopyOnWriteArrayList<JSONObject>()
        val transport = object : WorkspaceTransport {
            override suspend fun exchange(command: JSONObject): JSONObject {
                calls += JSONObject(command.toString())
                return actual.exchange(command)
            }
            override fun close() = actual.close()
        }
        val gateway = DurableGateway(transport)
        var archiveUsed = false
        lateinit var initial: SavedSnapshot
        suspend fun initialize() {
            initial = gateway.initialize()
            assertEquals(TextProvider.LOCAL, initial.textProvider)
            assertEquals(0L, initial.revision)
            val status = data(actual, JSONObject().put("op", "model_status"))
            assertEquals("configured_native_owner", status.getString("status"))
            assertTrue(status.getBoolean("real_model")) // Configured owner, not a model-load measurement.
            assertTrue(status.get("loaded") === JSONObject.NULL)
        }
        fun submission(): JSONObject = calls.single { it.getString("op") == "free_text" }
        fun scoped(op: String): JSONObject {
            val submit = submission()
            return JSONObject().put("op", op).put("session", submit.getString("session"))
                .put("scope", submit.getJSONObject("request").getJSONObject("scope"))
                .put("turn", submit.getJSONObject("request").getString("turn"))
        }
        suspend fun snapshot(revision: Long): JSONObject {
            val selected = checkNotNull(initial.selected)
            val resumed = data(actual, JSONObject().put("op", "resume").put("scope",
                JSONObject().put("story", selected.story).put("branch", selected.branch)))
            return data(actual, JSONObject().put("op", "play_snapshot").put("session", resumed.getString("session"))
                .put("scope", resumed.getJSONObject("scope")).put("expected_revision", revision))
        }
        suspend fun close() {
            worker.releaseRole.complete(Unit); worker.releaseEngine.complete(Unit)
            withContext(Dispatchers.Main) { gateway.close() }
            allSlots(database)
            if (archiveUsed) allArchiveSlots(database, File(root, "archive-staging"))
            check(root.canonicalFile.parentFile == parent)
            check(database.canonicalFile.parentFile == File(root, "workspace-v1").canonicalFile)
            // An intended unknown-worker result retains its small synthetic database for diagnosis.
            if (!owner.quarantined) check(root.deleteRecursively())
        }
    }
    private suspend fun fixture(worker: Worker = Worker(), test: suspend Fixture.() -> Unit) {
        val f = Fixture(worker)
        try { f.initialize(); f.test() } finally { withContext(NonCancellable) { f.close() } }
    }

    @Test fun externalPumpCommitsOriginalFreeTextAndReopensSameWorkspace() = runBlocking {
        fixture {
            val prepared = gateway.respondText(Action, 0)
            assertTrue(prepared is DemoResult.Prepared)
            assertEquals(0L, gateway.snapshot().revision)
            assertEquals(listOf("director", "narrator"), worker.requests.map { it.role })
            assertEquals(2, worker.drains.get()); assertEquals(2, worker.roleCloses.get())
            assertEquals(1, worker.engineCloses.get())
            assertTrue(gateway.commitAsync(prepared) is DemoResult.Accepted)
            val accepted = snapshot(1)
            assertFalse(accepted.getJSONObject("inventory").has("potion"))
            val receipt = accepted.getJSONArray("receipts").getJSONObject(0)
            assertJson(submission().getJSONObject("request"), receipt.getJSONObject("request"))
            assertEquals(Action.text, receipt.getJSONObject("request").getJSONObject("intent")
                .getJSONObject("value").getString("text"))
            assertJson(profile(), receipt.getJSONObject("play").getJSONObject("profile"))
            val duplicate = data(actual, scoped("commit"))
            assertJson(receipt, duplicate.getJSONObject("receipt"))
            withContext(Dispatchers.Main) { gateway.close() }
            allSlots(database)
            val reopened = NativeWorkspaceTransport(context, LocalInferenceOwner(profile().toString().toByteArray(), Worker()))
            try {
                val fresh = DurableGateway(reopened, autoCreateIfEmpty = false)
                assertEquals(1L, fresh.initialize().revision)
                val session = data(reopened, JSONObject().put("op", "resume").put("scope",
                    submission().getJSONObject("request").getJSONObject("scope")))
                val restored = data(reopened, JSONObject().put("op", "play_snapshot")
                    .put("session", session.getString("session")).put("scope", session.getJSONObject("scope"))
                    .put("expected_revision", 1))
                assertJson(accepted, restored)
            } finally { withContext(Dispatchers.Main) { reopened.close() } }
            allSlots(database)
        }
    }

    @Test fun readyWaitsForEngineCloseWhileMainRemainsResponsive() = runBlocking {
        fixture(Worker().also { it.holdEngine = true }) {
            val borrowed = actual.forkHandle()
            val preparing = async(Dispatchers.Default) { gateway.respondText(Action, 0) }
            withTimeout(5_000) { worker.engineClosing.await() }
            assertFalse(preparing.isCompleted)
            val native = raw(borrowed, scoped("turn_status"))
            assertEquals("ready", native.getJSONObject("data").getString("phase"))
            val accepted = raw(borrowed, scoped("play_snapshot").apply { remove("turn"); put("expected_revision", 0) })
            assertEquals(0L, accepted.getJSONObject("data").getLong("revision"))
            var heartbeat = false
            withTimeout(2_000) { withContext(Dispatchers.Main) { heartbeat = true } }
            assertTrue(heartbeat)
            worker.releaseEngine.complete(Unit)
            assertTrue(withTimeout(5_000) { preparing.await() } is DemoResult.Prepared)
            assertTrue(gateway.commitAsync(preparing.await()) is DemoResult.Accepted)
            assertEquals(1L, gateway.snapshot().revision)
        }
    }

    @Test fun unknownWorkerCloseInvalidatesBorrowedHandleAndForbidsReuse() = runBlocking {
        fixture(Worker().also { it.engineCloseKnown = false }) {
            val borrowed = actual.forkHandle()
            try { gateway.respondText(Action, 0); fail("Unknown close must not return Ready") }
            catch (_: LocalInferenceUncertain) { }
            assertTrue(owner.quarantined)
            assertTrue(owner.nativeInvalidatedKnown)
            assertEquals("InvalidHandle", raw(borrowed, JSONObject().put("op", "workspace")).getString("error"))
            val opens = worker.opens.get()
            try { gateway.recoverSaved(); fail("Poisoned owner cannot recover through the old handle") }
            catch (_: Exception) { }
            assertEquals(opens, worker.opens.get())
            allSlots(database)
            val fresh = NativeWorkspaceTransport(context)
            try {
                val saved = DurableGateway(fresh, autoCreateIfEmpty = false).initialize()
                assertEquals(0L, saved.revision)
                assertEquals("You", saved.potionOwner)
                assertTrue(saved.messages.isEmpty())
            } finally { withContext(Dispatchers.Main) { fresh.close() } }
            allSlots(database)
        }
    }

    @Test fun nativeCancellationDuringExternalRoleDiscardsLateResponse() = runBlocking {
        fixture(Worker().also { it.holdRole = true }) {
            val preparing = async(Dispatchers.Default) { gateway.respondText(Action, 0) }
            withTimeout(5_000) { worker.roleStarted.await() }
            val cancelled = data(actual, scoped("cancel"))
            assertEquals("cancelled", cancelled.getString("phase"))
            assertTrue(withTimeout(5_000) { preparing.await() } is DemoResult.Rejected)
            assertTrue(worker.cancels.get() > 0)
            assertEquals(1, worker.requests.size)
            assertEquals(0L, gateway.snapshot().revision)
            assertTrue(snapshot(0).getJSONObject("inventory").has("potion"))
        }
    }

    @Test fun storyDeletionDuringExternalRoleInvalidatesSameWorkspaceTicket() = runBlocking {
        fixture(Worker().also { it.holdRole = true }) {
            val preparing = async(Dispatchers.Default) { gateway.respondText(Action, 0) }
            withTimeout(5_000) { worker.roleStarted.await() }
            val deletion: StoryDeletionGateway = NativeArchiveGateway(context)
            archiveUsed = true
            try {
                val preview = deletion.prepare(checkNotNull(initial.selected))
                assertEquals(initial.selected?.story, deletion.commit(preview.token).storyId)
                assertTrue(withTimeout(5_000) { preparing.await() } is DemoResult.Rejected)
                assertTrue(worker.cancels.get() > 0)
                assertEquals(1, worker.requests.size)
                assertEquals(0, data(actual, JSONObject().put("op", "workspace")).getJSONArray("stories").length())
            } finally { withContext(Dispatchers.Main) { deletion.close() } }
        }
    }

    @Test fun nativeAdmissionRejectsMalformedProfilesAndResponseFramesWithoutFallback() = runBlocking {
        fixture {
            val borrowed = actual.forkHandle()
            withContext(Dispatchers.IO) {
                for (invalid in listOf(null, ByteArray(4097), byteArrayOf(0xc3.toByte(), 0x28), "{}".toByteArray())) {
                    assertEquals(0L, NativeWorkspace.openLocal(database.absolutePath, invalid))
                }
                fun rejected(bytes: ByteArray, error: String) {
                    val reply = JSONObject(localText(bytes, 40_000))
                    assertEquals("rejected", reply.getString("status"))
                    assertEquals(error, reply.getString("error"))
                }
                rejected(NativeWorkspace.pollInference(-1L), "InvalidHandle")
                rejected(NativeWorkspace.respondInference(borrowed, 1, null), "Malformed")
                rejected(NativeWorkspace.respondInference(borrowed, 1, ByteArray(16_385)), "TooLarge")
                rejected(NativeWorkspace.respondInference(borrowed, 0, byteArrayOf(1)), "InvalidTicket")
                rejected(NativeWorkspace.respondInference(borrowed, 1, byteArrayOf(1)), "InvalidTicket")
                val scripted = NativeWorkspace.open(database.absolutePath)
                assertTrue(scripted != 0L)
                try { rejected(NativeWorkspace.pollInference(scripted), "Unsupported") }
                finally { NativeWorkspace.close(scripted) }
            }
            try { NativeWorkspaceTransport(context, owner); fail("One owner cannot bind a second transport") }
            catch (_: IllegalArgumentException) { }
            assertEquals(0L, snapshot(0).getLong("revision"))
            assertTrue(snapshot(0).getJSONObject("inventory").has("potion"))
            assertEquals(0, worker.opens.get())
        }
    }

    private companion object {
        val Action = PlayInput(PlayInputKind.ACTION, "  I give my last potion to Mira.  ")
        fun offMain() = check(Looper.myLooper() != Looper.getMainLooper())
        fun profile() = JSONObject().put("id", "external-jni-synthetic-v1")
            .put("model_sha256", "0".repeat(64)).put("runtime_revision", "0".repeat(40))
            .put("template_sha256", "0".repeat(64)).put("worker_sha256", "0".repeat(64))
            .put("profile_manifest_sha256", "0".repeat(64)).put("context_tokens", 4096)
            .put("director_tokens", 350).put("narrator_tokens", 220).put("deadline_ms", 5000).put("repair_limit", 1)
        fun response(request: LocalInferenceRequest): ByteArray {
            val schema = JSONObject(request.schemaJson)
            val value = when (request.role) {
                "director" -> JSONObject().put("commands", JSONArray().put(JSONObject().put("op", "give")
                    .put("item", "potion").put("to", "mira").put("quantity", 1)))
                "narrator" -> JSONObject().put("text", "The accepted outcome is recorded.")
                    .put("event_ids", schema.getJSONObject("properties").getJSONObject("event_ids").getJSONArray("const"))
                    .put("speaker", "narrator")
                else -> error("Unexpected synthetic role")
            }
            return value.toString().toByteArray(Charsets.UTF_8)
        }
        suspend fun data(actual: NativeWorkspaceTransport, command: JSONObject): JSONObject {
            val reply = actual.exchange(command)
            assertEquals("ok", reply.getString("status"))
            return reply.getJSONObject("data")
        }
        suspend fun raw(handle: Long, command: JSONObject): JSONObject = withContext(Dispatchers.IO) {
            JSONObject(NativeWorkspace.call(handle, JSONObject().put("version", 1).put("command", command)
                .toString().toByteArray(Charsets.UTF_8)).toString(Charsets.UTF_8))
        }
        suspend fun allSlots(database: File) = withContext(Dispatchers.IO) {
            withTimeout(5_000) {
                while (true) {
                    val handles = mutableListOf<Long>()
                    try {
                        repeat(4) { NativeWorkspace.open(database.absolutePath).let { if (it != 0L) handles += it } }
                        if (handles.size == 4) break
                    } finally { handles.forEach { NativeWorkspace.close(it) } }
                    delay(5)
                }
            }
        }
        suspend fun allArchiveSlots(database: File, staging: File) = withContext(Dispatchers.IO) {
            withTimeout(5_000) {
                while (true) {
                    val handles = mutableListOf<Long>()
                    try {
                        repeat(4) { NativeArchive.open(database.absolutePath, staging.absolutePath)
                            .let { if (it != 0L) handles += it } }
                        if (handles.size == 4) break
                    } finally { handles.forEach { NativeArchive.close(it) } }
                    delay(5)
                }
            }
        }
        fun assertJson(expected: Any?, actual: Any?) {
            when (expected) {
                is JSONObject -> {
                    assertTrue(actual is JSONObject)
                    actual as JSONObject
                    val keys = expected.keys().asSequence().toSet()
                    assertEquals(keys, actual.keys().asSequence().toSet())
                    keys.forEach { assertJson(expected.get(it), actual.get(it)) }
                }
                is JSONArray -> {
                    assertTrue(actual is JSONArray)
                    actual as JSONArray
                    assertEquals(expected.length(), actual.length())
                    for (i in 0 until expected.length()) assertJson(expected.get(i), actual.get(i))
                }
                is Number -> assertEquals(expected.toString(), actual.toString())
                else -> assertEquals(expected, actual)
            }
        }
    }
}

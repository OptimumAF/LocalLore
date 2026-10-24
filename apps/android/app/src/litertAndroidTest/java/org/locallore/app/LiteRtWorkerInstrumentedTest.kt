/* Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0 */
package org.locallore.app

import android.content.Context
import android.content.ContextWrapper
import android.os.Looper
import androidx.test.ext.junit.runners.AndroidJUnit4
import androidx.test.platform.app.InstrumentationRegistry
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.NonCancellable
import kotlinx.coroutines.delay
import kotlinx.coroutines.runBlocking
import kotlinx.coroutines.withContext
import kotlinx.coroutines.withTimeout
import org.json.JSONArray
import org.json.JSONObject
import org.junit.Assert.*
import org.junit.Test
import org.junit.runner.RunWith
import org.junit.runners.model.MultipleFailureException
import java.io.File
import java.security.MessageDigest
import java.util.UUID
import java.util.concurrent.CopyOnWriteArrayList
import java.util.concurrent.atomic.AtomicInteger

/** Actual packaged SDK linkage and production preflight; never initializes a model or reads weights. */
@RunWith(AndroidJUnit4::class)
class LiteRtWorkerInstrumentedTest {
    private class Fixture {
        val parent = InstrumentationRegistry.getInstrumentation().targetContext.noBackupFilesDir.canonicalFile
        val root = File(parent, "synthetic-litert-worker-${UUID.randomUUID()}").also {
            check(it.mkdir() && it.canonicalFile.parentFile == parent)
        }
        val models = File(root, "models").also { check(it.mkdir()) }
        val cache = File(models, "cache").also { check(it.mkdir()) }
        val missing = File(models, "absent-synthetic.litertlm")
        val database = File(root, "workspace-v1/stories.sqlite3")
        val context = object : ContextWrapper(InstrumentationRegistry.getInstrumentation().targetContext) {
            override fun getApplicationContext(): Context = this
            override fun getNoBackupFilesDir(): File = root
        }
        var retain = false
        fun config(model: File = missing, scratch: File = cache, digest: String = sha(SYNTHETIC)) = LiteRtWorkerConfig(
            root = models, model = model, cache = scratch, expectedModelBytes = SYNTHETIC.size.toLong(),
            modelSha256 = digest, templateSha256 = "0".repeat(64), workerSha256 = "0".repeat(64),
            profileManifestSha256 = "0".repeat(64), deadlineMs = 8_000,
        )
        fun contained() {
            check(root.canonicalFile.parentFile == parent && root.name.startsWith("synthetic-litert-worker-"))
            check(models.canonicalFile.parentFile == root && cache.canonicalFile.parentFile == models)
            check(checkNotNull(database.canonicalFile.parentFile).parentFile == root)
        }
    }

    private suspend fun fixture(block: suspend (Fixture) -> Unit) {
        val f = Fixture()
        val failures = mutableListOf<Throwable>()
        try { block(f) } catch (failure: Throwable) { f.retain = true; failures += failure }
        try {
            withContext(NonCancellable) {
                if (f.database.isFile) allSlots(f.database)
                f.contained()
                // Quarantine or a failed test retains only this new, synthetic private root.
                if (!f.retain) check(f.root.deleteRecursively())
            }
        } catch (failure: Throwable) { failures += failure }
        MultipleFailureException.assertEmpty(failures)
    }

    /** A spy can observe construction only after production admission; it never calls the SDK. */
    private suspend fun refusesBeforeSdk(config: LiteRtWorkerConfig) {
        val allocations = AtomicInteger()
        val worker = LiteRtRoleWorker(config, LiteRtResources {
            check(Looper.myLooper() != Looper.getMainLooper())
            allocations.incrementAndGet()
            error("Synthetic SDK construction must be unreachable")
        })
        withContext(Dispatchers.Main) { uncertain { worker.open() } }
        assertEquals("Admission must precede SDK construction", 0, allocations.get())
    }

    private suspend fun pairedFailurePreservesCanon(f: Fixture, config: LiteRtWorkerConfig) {
        val owner = config.createOwner(LocalInferenceLimits(turnMs = 8_000, cleanupMs = 1_000, pollMs = 5))
        val actual = NativeWorkspaceTransport(f.context, owner)
        val calls = CopyOnWriteArrayList<JSONObject>()
        val gateway = DurableGateway(object : WorkspaceTransport {
            override suspend fun exchange(command: JSONObject): JSONObject {
                calls += JSONObject(command.toString())
                return actual.exchange(command)
            }
            override fun close() = actual.close()
        })
        try {
            val initial = gateway.initialize()
            assertEquals(TextProvider.LOCAL, initial.textProvider)
            assertEquals(0L, initial.revision)
            val selected = checkNotNull(initial.selected)
            val scope = JSONObject().put("story", selected.story).put("branch", selected.branch)
            val before = snapshot(actual, scope)
            configuredOwner(actual, config)
            val borrowed = actual.forkHandle()
            withContext(Dispatchers.Main) { uncertain { gateway.respondText(ACTION, 0) } }
            assertTrue(owner.quarantined)
            f.retain = true
            assertTrue(owner.nativeInvalidatedKnown)
            withContext(Dispatchers.IO) {
                val reply = NativeWorkspace.call(borrowed, localUtf8("""{"version":1,"command":{"op":"workspace"}}"""))
                assertEquals("InvalidHandle", JSONObject(localText(reply, 262_144)).getString("error"))
            }
            val original = calls.single { it.getString("op") == "free_text" }.getJSONObject("request")
            assertEquals(ACTION.text, original.getJSONObject("intent").getJSONObject("value").getString("text"))
            withContext(Dispatchers.Main) { uncertain { gateway.recoverSaved() } }
            assertEquals(1, calls.count { it.getString("op") == "free_text" })
            assertEquals(0, calls.count { it.getString("op") == "commit" })
            allSlots(f.database)

            // Fresh paired LOCAL construction reads accepted canon without inference or fallback.
            val fresh = NativeWorkspaceTransport(f.context, config.createOwner())
            try {
                configuredOwner(fresh, config)
                val restored = snapshot(fresh, scope)
                assertJson(before, restored)
                assertEquals(0L, restored.getLong("revision"))
                assertEquals(0, restored.getJSONArray("receipts").length())
                assertTrue(restored.getJSONObject("inventory").has("potion"))
            } finally { withContext(Dispatchers.Main) { fresh.close() } }
            allSlots(f.database)
        } finally { withContext(NonCancellable + Dispatchers.Main) { gateway.close() } }
    }

    @Test fun packagedSdkLoadsWithoutModelInitialization() = runBlocking {
        // The SDK's pinned NativeLibraryLoader uses this library name. No Engine is created.
        withContext(Dispatchers.IO) {
            check(Looper.myLooper() != Looper.getMainLooper())
            System.loadLibrary("litertlm_jni")
        }
    }

    @Test fun missingModelAdmissionFailsBeforeSdkAndPreservesCanonicalWorkspace() = runBlocking {
        fixture { f ->
            assertFalse(f.missing.exists())
            refusesBeforeSdk(f.config())
            pairedFailurePreservesCanon(f, f.config())
            assertFalse(f.missing.exists())
            assertTrue(checkNotNull(f.cache.list()).isEmpty())
        }
    }

    @Test fun digestAndConfinementFailuresCannotAllocateSdkOrSelectFallback() = runBlocking {
        fixture { f ->
            val corrupt = File(f.models, "synthetic-corrupt.litertlm")
            check(corrupt.createNewFile())
            corrupt.writeBytes(SYNTHETIC)
            val wrongDigest = f.config(model = corrupt, digest = "0".repeat(64))
            refusesBeforeSdk(wrongDigest)

            val outsideModel = File(f.root, "synthetic-outside.litertlm")
            check(outsideModel.createNewFile())
            outsideModel.writeBytes(SYNTHETIC)
            refusesBeforeSdk(f.config(model = outsideModel))
            val outsideCache = File(f.root, "synthetic-outside-cache").also { check(it.mkdir()) }
            refusesBeforeSdk(f.config(model = corrupt, scratch = outsideCache))

            pairedFailurePreservesCanon(f, wrongDigest)
            assertArrayEquals(SYNTHETIC, corrupt.readBytes())
            assertArrayEquals(SYNTHETIC, outsideModel.readBytes())
            assertTrue(checkNotNull(f.cache.list()).isEmpty())
            assertTrue(checkNotNull(outsideCache.list()).isEmpty())
        }
    }

    private companion object {
        val SYNTHETIC = "LocalLore synthetic invalid model".toByteArray(Charsets.UTF_8)
        val ACTION = PlayInput(PlayInputKind.ACTION, "I give my last potion to Mira.")
        fun sha(bytes: ByteArray) = MessageDigest.getInstance("SHA-256").digest(bytes)
            .joinToString("") { "%02x".format(it) }
        suspend fun uncertain(block: suspend () -> Unit) {
            try { block(); fail("Expected fixed ownership uncertainty") }
            catch (failure: LocalInferenceUncertain) { assertNull(failure.cause) }
        }
        suspend fun data(actual: NativeWorkspaceTransport, command: JSONObject): JSONObject {
            val reply = actual.exchange(command)
            assertEquals("ok", reply.getString("status"))
            return reply.getJSONObject("data")
        }
        suspend fun configuredOwner(actual: NativeWorkspaceTransport, config: LiteRtWorkerConfig) {
            val status = data(actual, JSONObject().put("op", "model_status"))
            assertEquals("configured_native_owner", status.getString("status"))
            assertEquals(JSONObject(localText(config.profileBytes(), 4096)).getString("id"), status.getString("provider"))
            assertTrue(status.get("loaded") === JSONObject.NULL)
        }
        suspend fun snapshot(actual: NativeWorkspaceTransport, scope: JSONObject): JSONObject {
            val resumed = data(actual, JSONObject().put("op", "resume").put("scope", scope))
            return data(actual, JSONObject().put("op", "play_snapshot").put("session", resumed.getString("session"))
                .put("scope", scope).put("expected_revision", 0))
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
        fun assertJson(expected: Any?, actual: Any?) {
            when (expected) {
                is JSONObject -> {
                    assertTrue(actual is JSONObject); actual as JSONObject
                    val keys = expected.keys().asSequence().toSet()
                    assertEquals(keys, actual.keys().asSequence().toSet())
                    keys.forEach { assertJson(expected.get(it), actual.get(it)) }
                }
                is JSONArray -> {
                    assertTrue(actual is JSONArray); actual as JSONArray
                    assertEquals(expected.length(), actual.length())
                    for (index in 0 until expected.length()) assertJson(expected.get(index), actual.get(index))
                }
                is Number -> assertEquals(expected.toString(), actual.toString())
                else -> assertEquals(expected, actual)
            }
        }
    }
}

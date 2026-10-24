/* Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0 */
package org.locallore.app

import android.os.Looper
import androidx.compose.ui.test.assertIsEnabled
import androidx.compose.ui.test.assertIsNotEnabled
import androidx.compose.ui.test.assertIsDisplayed
import androidx.compose.ui.test.assertTextEquals
import androidx.compose.ui.test.junit4.createAndroidComposeRule
import androidx.compose.ui.test.onNodeWithTag
import androidx.compose.ui.test.performScrollTo
import androidx.test.platform.app.InstrumentationRegistry
import java.io.ByteArrayInputStream
import java.io.File
import java.io.InputStream
import java.nio.file.Files
import java.security.MessageDigest
import java.util.UUID
import java.util.concurrent.CountDownLatch
import java.util.concurrent.TimeUnit
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.async
import kotlinx.coroutines.delay
import kotlinx.coroutines.runBlocking
import kotlinx.coroutines.withContext
import kotlinx.coroutines.withTimeout
import org.json.JSONObject
import org.junit.Assert.*
import org.junit.Rule
import org.junit.Test

/** Tiny original fixtures only. Does not construct an SDK Engine or inspect prior caches. */
class LocalModelProvisionInstrumentedTest {
    @get:Rule val compose = createAndroidComposeRule<LocalModelSetupActivity>()
    private val bytes = "LocalLore original synthetic model import fixture".toByteArray()
    private val identity get() = LocalModelIdentity("synthetic-v1", bytes.size.toLong(),
        MessageDigest.getInstance("SHA-256").digest(bytes).joinToString("") { "%02x".format(it) }, 1024)
    private fun fixtureRoot(): File = File(InstrumentationRegistry.getInstrumentation().targetContext.noBackupFilesDir.canonicalFile,
        "provision-test-${UUID.randomUUID()}")

    @Test fun missingBuiltInModelRendersSetupAndCannotStartInference() {
        compose.waitUntil(5_000) {
            runCatching {
                compose.onNodeWithTag("model-setup-status")
                    .assertTextEquals("Choose the verified local model file to continue.")
                true
            }.getOrDefault(false)
        }
        compose.onNodeWithTag("model-choose").assertIsEnabled()
        compose.onNodeWithTag("model-expected-hash").performScrollTo().assertIsDisplayed()
        compose.onNodeWithTag("model-start").assertIsNotEnabled()
        val context = compose.activity.applicationContext
        assertEquals("org.locallore.app.modelverify", context.packageName)
        assertEquals(context.noBackupFilesDir.canonicalFile,
            CandidateLocalModel.store(context).plannedFiles().root.parentFile)
        assertFalse(CandidateLocalModel.store(context).plannedFiles().model.exists())
        assertTrue(CandidateLocalModel.canStart())
        // Exercise the SAME factory used by the real play Activity, without preparing a turn.
        runBlocking {
            val transport = withContext(Dispatchers.Main) { CandidateLocalModel.createTransport(context) }
            var borrowed = 0L
            try {
                val reply = transport.exchange(JSONObject().put("op", "model_status"))
                assertEquals("ok", reply.getString("status"))
                val status = reply.getJSONObject("data")
                assertEquals("configured_native_owner", status.getString("status"))
                assertEquals("android-litert-play-probe-v1", status.getString("provider"))
                assertTrue(status.get("loaded") === JSONObject.NULL)
                borrowed = transport.forkHandle()
            } finally { withContext(Dispatchers.Main) { transport.close() } }
            assertTrue(borrowed > 0)
            withContext(Dispatchers.IO) {
                withTimeout(5_000) {
                    while (true) {
                        val raw = NativeWorkspace.call(borrowed,
                            localUtf8("""{"version":1,"command":{"op":"workspace"}}"""))
                        if (JSONObject(localText(raw, 262_144)).optString("error") == "InvalidHandle") break
                        delay(5)
                    }
                }
            }
            assertFalse(CandidateLocalModel.canStart())
            withContext(Dispatchers.Main) {
                try { CandidateLocalModel.createTransport(context); fail("A second runtime must be refused") }
                catch (expected: WorkspaceConstructionUnavailable) {
                    assertEquals("Workspace unavailable", expected.message)
                    assertNull(expected.cause)
                }
            }
        }
        assertFalse(CandidateLocalModel.store(context).plannedFiles().model.exists())
    }

    @Test fun verifiedTinyCopyPublishesAtomicallyAndReopensOnAndroidFilesystem() = runBlocking {
        val root = fixtureRoot()
        try {
            val store = LocalModelStore(root, identity)
            assertNull(store.installed())
            val files = store.import {
                assertNotSame(Looper.getMainLooper().thread, Thread.currentThread())
                ByteArrayInputStream(bytes)
            }
            assertArrayEquals(bytes, files.model.readBytes())
            assertTrue(files.cache.isDirectory)
            assertFalse(File(root, "model.part").exists())
            val reopened = LocalModelStore(root, identity).installed()
            assertNotNull(reopened)
            assertArrayEquals(bytes, reopened!!.model.readBytes())
            store.import { error("A valid copy must not open another provider") }
            assertArrayEquals(bytes, files.model.readBytes())
            // Exercise the actual syscall against a destination introduced after admission.
            val stage = File(root, "model.part")
            stage.writeBytes(byteArrayOf(7, 8))
            try { NativeModelPublication.publish(root); fail("Must refuse an existing destination") }
            catch (expected: LocalModelException) { assertEquals(LocalModelFailure.UNSAFE_PATH, expected.failure) }
            assertArrayEquals(bytes, files.model.readBytes())
            assertArrayEquals(byteArrayOf(7, 8), stage.readBytes())
            stage.delete()
            files.model.delete()
            val outside = File(root, "untouched")
            outside.writeBytes(bytes)
            Files.createSymbolicLink(files.model.toPath(), outside.toPath())
            stage.writeBytes(byteArrayOf(9))
            try { NativeModelPublication.publish(root); fail("Must refuse a destination symlink") }
            catch (expected: LocalModelException) { assertEquals(LocalModelFailure.UNSAFE_PATH, expected.failure) }
            assertTrue(Files.isSymbolicLink(files.model.toPath()))
            assertArrayEquals(bytes, outside.readBytes())
            assertArrayEquals(byteArrayOf(9), stage.readBytes())
            Files.delete(files.model.toPath())
        } finally { root.deleteRecursively() } // Only this fresh synthetic test namespace.
    }

    @Test fun androidSymlinkCannotRedirectImportOrDeleteOutsideFixture() = runBlocking {
        val root = fixtureRoot()
        val outside = fixtureRoot()
        assertTrue(root.mkdir())
        assertTrue(outside.mkdir())
        val protected = File(outside, "protected")
        protected.writeBytes(bytes)
        try {
            // Establish valid root admission before testing the child symlink boundary.
            assertNull(LocalModelStore(root, identity).installed())
            Files.createSymbolicLink(File(root, "model.part").toPath(), protected.toPath())
            try { LocalModelStore(root, identity).import { error("Unsafe path must precede provider") }; fail() }
            catch (expected: LocalModelException) { assertEquals(LocalModelFailure.UNSAFE_PATH, expected.failure) }
            assertArrayEquals(bytes, protected.readBytes())
            assertTrue(Files.isSymbolicLink(File(root, "model.part").toPath()))
            assertFalse(File(root, "model.litertlm").exists())
        } finally {
            // Delete just the known link, never traverse it during fixture cleanup.
            Files.deleteIfExists(File(root, "model.part").toPath())
            root.deleteRecursively(); outside.deleteRecursively()
        }
    }

    @Test fun cancelledBlockedProviderRetainsSlotUntilActualReturn() = runBlocking {
        val root = fixtureRoot()
        val entered = CountDownLatch(1)
        val release = CountDownLatch(1)
        val store = LocalModelStore(root, identity)
        val copying = async(Dispatchers.IO) {
            store.import { object : InputStream() {
                override fun read(): Int = error("Bulk read expected")
                override fun read(b: ByteArray, off: Int, len: Int): Int {
                    entered.countDown()
                    check(release.await(5, TimeUnit.SECONDS))
                    return -1
                }
            } }
        }
        try {
            assertTrue(entered.await(3, TimeUnit.SECONDS))
            copying.cancel()
            try { LocalModelStore(root, identity).import { error("Must remain busy") }; fail() }
            catch (expected: LocalModelException) { assertEquals(LocalModelFailure.BUSY, expected.failure) }
            assertFalse(copying.isCompleted)
        } finally {
            release.countDown()
            copying.join()
        }
        assertFalse(File(root, "model.litertlm").exists())
        assertFalse(File(root, "model.part").exists())
        try {
            assertNotNull(store.import { ByteArrayInputStream(bytes) })
        } finally { root.deleteRecursively() }
    }
}

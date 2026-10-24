/* Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0 */
package org.locallore.app

import android.app.Application
import android.os.Environment
import android.os.Looper
import android.os.Process
import android.os.storage.StorageManager
import android.system.Os
import androidx.test.filters.SdkSuppress
import androidx.test.platform.app.InstrumentationRegistry
import java.io.ByteArrayInputStream
import java.io.File
import java.nio.ByteBuffer
import java.nio.channels.FileChannel
import java.nio.file.Files
import java.nio.file.LinkOption.NOFOLLOW_LINKS
import java.nio.file.StandardOpenOption.CREATE_NEW
import java.nio.file.StandardOpenOption.WRITE
import java.security.MessageDigest
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.runBlocking
import kotlinx.coroutines.withContext
import org.json.JSONObject
import org.junit.Assert.*
import org.junit.Test

/** Actual production storage/native publication; only a fresh disposable package's tiny fixture. */
@SdkSuppress(minSdkVersion = 30)
class ModelVolumeStorageTest {
    @Test fun contextOwnedRemovableVolumePublishesAndRefusesReplacement() = runBlocking {
        withContext(Dispatchers.IO) {
            assertNotSame(Looper.getMainLooper().thread, Thread.currentThread())
            val context = InstrumentationRegistry.getInstrumentation().targetContext.applicationContext
            assertEquals("org.locallore.app.modelvolumeverify", context.packageName)
            assertEquals(context.applicationInfo.uid, Process.myUid())
            assertEquals(context.applicationInfo.processName, Application.getProcessName())
            val proofRoot = File(context.noBackupFilesDir.canonicalFile, "model-volume-proof-v1")
            assertAbsent(proofRoot)
            // Never resolve CandidateLocalModel.store or a runtime/benchmark path.
            val volume = AndroidModelVolume.select(context)
            val root = volume.root
            assertEquals("local-model-removable-v1", root.name)
            val appFiles = requireNotNull(root.parentFile)
            assertEquals(appFiles, appFiles.canonicalFile)
            assertEquals(1, context.getExternalFilesDirs(null).filterNotNull().count {
                it.canonicalFile == appFiles
            })
            assertEquals(Environment.MEDIA_MOUNTED, Environment.getExternalStorageState(appFiles))
            assertTrue(Environment.isExternalStorageRemovable(appFiles))
            assertFalse(Environment.isExternalStorageEmulated(appFiles))
            val storage = requireNotNull(context.getSystemService(StorageManager::class.java)
                .getStorageVolume(appFiles))
            assertFalse(storage.isPrimary)
            assertTrue(storage.isRemovable)
            assertFalse(storage.isEmulated)
            assertFalse(storage.uuid.isNullOrBlank())
            assertNotEquals(Os.stat(context.noBackupFilesDir.path).st_dev, Os.stat(appFiles.path).st_dev)
            assertAbsent(root)
            volume.admit(BYTES.size.toLong()) // Unchanged >=2 GiB volume / userdata policy.

            val rejectedRoot = File(appFiles, "volume-rejected-v1")
            assertAbsent(rejectedRoot)
            var rejectedOpens = 0
            val rejected = LocalModelStore(rejectedRoot, identity,
                storageAdmission = { throw LocalModelException(LocalModelFailure.STORAGE) })
            expectFailure(LocalModelFailure.STORAGE) { rejected.installed() }
            expectFailure(LocalModelFailure.STORAGE) {
                rejected.import { rejectedOpens++; ByteArrayInputStream(BYTES) }
            }
            assertEquals(0, rejectedOpens)
            assertAbsent(rejectedRoot)
            assertAbsent(root) // Rejection has no fallback destination.

            var sourceOpens = 0
            val store = LocalModelStore(root, identity, storageAdmission = volume::admit)
            assertNull(store.installed())
            val files = store.import {
                assertNotSame(Looper.getMainLooper().thread, Thread.currentThread())
                sourceOpens++
                ByteArrayInputStream(BYTES)
            }
            assertEquals(root, files.root)
            assertEquals(1, sourceOpens)
            assertArrayEquals(BYTES, files.model.readBytes())
            assertTrue(Files.isDirectory(files.cache.toPath(), NOFOLLOW_LINKS))
            assertAbsent(File(root, "model.part"))
            val sentinel = File(files.cache, "volume-sentinel-v1.bin")
            forcedNew(sentinel, SENTINEL)

            volume.admit()
            val reopened = requireNotNull(LocalModelStore(root, identity,
                storageAdmission = volume::admit).installed())
            assertEquals(HASH, sha(reopened.model.readBytes()))
            store.import { error("Verified artifact must not open another source") }
            val wrong = LocalModelStore(root, identity.copy(sha256 = "0".repeat(64)),
                storageAdmission = volume::admit)
            expectFailure(LocalModelFailure.INVALID_MODEL) {
                wrong.import { error("Wrong identity must refuse before source") }
            }
            assertArrayEquals(BYTES, files.model.readBytes())
            assertArrayEquals(SENTINEL, sentinel.readBytes())
            assertAbsent(rejectedRoot)

            // Directly exercise the production no-replace syscall with an existing destination.
            // Preserve this owned tiny stage as evidence; never reopen the store afterwards.
            volume.admit()
            val stage = File(root, "model.part")
            forcedNew(stage, STAGE)
            expectFailure(LocalModelFailure.UNSAFE_PATH) { NativeModelPublication.publish(root) }
            assertArrayEquals(BYTES, files.model.readBytes())
            assertArrayEquals(STAGE, stage.readBytes())
            assertArrayEquals(SENTINEL, sentinel.readBytes())
            volume.admit()

            Files.createDirectory(proofRoot.toPath())
            val proof = JSONObject().put("version", 1).put("pid", Process.myPid())
                .put("start", Process.getStartElapsedRealtime()).put("uid", Process.myUid())
                .put("process", Application.getProcessName()).put("model_bytes", BYTES.size)
                .put("model_sha256", HASH).put("source_opens", sourceOpens)
                .put("rejected_source_opens", rejectedOpens).put("context_owned", true)
                .put("removable_nonprimary_nonemulated", true).put("different_userdata_device", true)
                .put("native_no_replace", true).put("stage_preserved", true)
                .put("sentinel_sha256", sha(SENTINEL)).toString().toByteArray(Charsets.US_ASCII)
            assertTrue(proof.size <= 4096)
            forcedNew(File(proofRoot, "volume-proof-v1.json"), proof)
            forcedNew(File(proofRoot, "volume-ready-v1.txt"), "volume-ready-v1\n".toByteArray(Charsets.US_ASCII))
        }
    }

    private suspend fun expectFailure(expected: LocalModelFailure, action: suspend () -> Any?) {
        try { action(); fail("Expected fixed storage refusal") }
        catch (failure: LocalModelException) { assertEquals(expected, failure.failure) }
    }

    private fun assertAbsent(file: File) {
        assertFalse(Files.exists(file.toPath(), NOFOLLOW_LINKS))
    }

    private fun forcedNew(file: File, bytes: ByteArray) {
        FileChannel.open(file.toPath(), CREATE_NEW, WRITE, NOFOLLOW_LINKS).use { channel ->
            val buffer = ByteBuffer.wrap(bytes)
            while (buffer.hasRemaining()) channel.write(buffer)
            channel.force(true)
        }
    }

    private fun sha(bytes: ByteArray): String = MessageDigest.getInstance("SHA-256")
        .digest(bytes).joinToString("") { "%02x".format(it) }

    private companion object {
        val BYTES = "LocalLore original model picker fixture v1. No model or story.\n".toByteArray(Charsets.US_ASCII)
        const val HASH = "648c91a9de82e613189b3920a2098f5d803eb6e244f39b2b631cce24b7be8de0"
        val STAGE = byteArrayOf(7, 8)
        val SENTINEL = "LocalLore synthetic removable-volume cache v1\n".toByteArray(Charsets.US_ASCII)
        val identity = LocalModelIdentity("synthetic-volume-v1", 63, HASH, 1024)
    }
}

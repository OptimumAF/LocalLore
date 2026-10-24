/* Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0 */
package org.locallore.app

import android.app.Application
import android.os.Looper
import android.os.Process
import androidx.test.filters.SdkSuppress
import androidx.test.platform.app.InstrumentationRegistry
import java.io.File
import java.nio.ByteBuffer
import java.nio.channels.FileChannel
import java.nio.file.Files
import java.nio.file.LinkOption.NOFOLLOW_LINKS
import java.nio.file.Path
import java.nio.file.StandardOpenOption.CREATE_NEW
import java.nio.file.StandardOpenOption.READ
import java.nio.file.StandardOpenOption.WRITE
import java.nio.file.attribute.BasicFileAttributes
import java.security.MessageDigest
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.runBlocking
import kotlinx.coroutines.withContext
import org.json.JSONObject
import org.junit.Assert.*
import org.junit.Test

/** One direct fixed-name publication observation; a refused result can pass this diagnostic. */
@SdkSuppress(minSdkVersion = 30)
class ModelPublicationDiagnosticTest {
    @Test fun classifyFreshVolumePublicationResultWithoutFallback() = runBlocking {
        withContext(Dispatchers.IO) {
            assertNotSame(Looper.getMainLooper().thread, Thread.currentThread())
            val context = InstrumentationRegistry.getInstrumentation().targetContext.applicationContext
            assertEquals("org.locallore.app.modelvolumeverify", context.packageName)
            assertEquals(context.applicationInfo.uid, Process.myUid())
            assertEquals(context.applicationInfo.processName, Application.getProcessName())
            val internal = context.noBackupFilesDir.canonicalFile
            val proofRoot = File(internal, "model-publication-diagnostic-proof-v1")
            assertAbsent(proofRoot)
            val volume = AndroidModelVolume.select(context)
            val candidateRoot = volume.root
            assertAbsent(candidateRoot)
            val appFiles = requireNotNull(candidateRoot.parentFile)
            val root = File(appFiles, "model-publication-diagnostic-v1")
            assertAbsent(root)
            val externalBefore = appFiles.usableSpace
            val userdataBefore = internal.usableSpace
            volume.admit(BYTES.size.toLong())
            Files.createDirectory(root.toPath())
            strictDirectory(root)
            val stage = File(root, "model.part")
            val destination = File(root, "model.litertlm")
            assertAbsent(stage)
            assertAbsent(destination)
            volume.admit(BYTES.size.toLong())
            forcedNew(stage, BYTES)
            assertArrayEquals(BYTES, exactFixture(stage))

            var callbackCount = 0
            var observed: ModelPublicationResult? = null
            var failure: LocalModelFailure? = null
            volume.admit()
            strictDirectory(root)
            try {
                NativeModelPublication.publish(root, onResult = {
                    callbackCount++
                    observed = it
                })
            } catch (refusal: LocalModelException) { failure = refusal.failure }
            assertEquals(1, callbackCount)
            val result = requireNotNull(observed)
            volume.admit()
            strictDirectory(root)
            val published = result == ModelPublicationResult.PUBLISHED
            if (published) {
                assertNull(failure)
                assertAbsent(stage)
                assertArrayEquals(BYTES, exactFixture(destination))
            } else {
                val expected = when (result) {
                    ModelPublicationResult.DESTINATION_EXISTS, ModelPublicationResult.INVALID_INPUT ->
                        LocalModelFailure.UNSAFE_PATH
                    else -> LocalModelFailure.STORAGE
                }
                assertEquals(expected, failure)
                assertArrayEquals(BYTES, exactFixture(stage))
                assertAbsent(destination)
                assertNotEquals("Initially absent destination cannot qualify DESTINATION_EXISTS",
                    ModelPublicationResult.DESTINATION_EXISTS, result)
            }
            // Never clean up either outcome or inspect earlier failed synthetic namespaces.
            volume.admit()
            assertAbsent(candidateRoot)
            val externalAfter = appFiles.usableSpace
            val userdataAfter = internal.usableSpace
            Files.createDirectory(proofRoot.toPath())
            strictDirectory(proofRoot)
            val proof = JSONObject().put("version", 1).put("phase", "PUBLICATION_DIAGNOSTIC")
                .put("pid", Process.myPid()).put("start", Process.getStartElapsedRealtime())
                .put("uid", Process.myUid()).put("process", Application.getProcessName())
                .put("result", result.name).put("publication_succeeded", published)
                .put("callback_count", callbackCount).put("failure", failure?.name ?: JSONObject.NULL)
                .put("fixture_bytes", BYTES.size).put("fixture_sha256", HASH)
                .put("stage_present", !published).put("destination_present", published)
                .put("candidate_root_absent", true).put("direct_publication_only", true)
                .put("positive_store_qualification", false)
                .put("external_free_before", externalBefore).put("external_free_after", externalAfter)
                .put("userdata_free_before", userdataBefore).put("userdata_free_after", userdataAfter)
                .toString().toByteArray(Charsets.US_ASCII)
            assertTrue(proof.size <= 4096)
            forcedNew(File(proofRoot, "publication-proof-v1.json"), proof)
            forcedNew(File(proofRoot, "publication-ready-v1.txt"),
                "publication-ready-v1\n".toByteArray(Charsets.US_ASCII))
        }
    }

    private fun strictDirectory(file: File) {
        assertEquals(file.absoluteFile, file.canonicalFile)
        var cursor: Path? = file.toPath()
        while (cursor != null) {
            assertFalse(Files.isSymbolicLink(cursor))
            assertTrue(Files.isDirectory(cursor, NOFOLLOW_LINKS))
            cursor = cursor.parent
        }
    }

    private fun assertAbsent(file: File) = assertFalse(Files.exists(file.toPath(), NOFOLLOW_LINKS))

    private fun forcedNew(file: File, bytes: ByteArray) {
        FileChannel.open(file.toPath(), CREATE_NEW, WRITE, NOFOLLOW_LINKS).use { channel ->
            val buffer = ByteBuffer.wrap(bytes)
            while (buffer.hasRemaining()) channel.write(buffer)
            channel.force(true)
        }
    }

    private fun exactFixture(file: File): ByteArray {
        val before = Files.readAttributes(file.toPath(), BasicFileAttributes::class.java, NOFOLLOW_LINKS)
        assertTrue(before.isRegularFile)
        assertFalse(before.isSymbolicLink)
        assertEquals(BYTES.size.toLong(), before.size())
        val buffer = ByteArray(BYTES.size + 1)
        var count = 0
        Files.newInputStream(file.toPath(), READ, NOFOLLOW_LINKS).use { input ->
            while (count < buffer.size) {
                val read = input.read(buffer, count, buffer.size - count)
                if (read < 0) break
                assertTrue(read > 0)
                count += read
            }
        }
        assertEquals(BYTES.size, count)
        val after = Files.readAttributes(file.toPath(), BasicFileAttributes::class.java, NOFOLLOW_LINKS)
        assertTrue(after.isRegularFile)
        assertFalse(after.isSymbolicLink)
        assertEquals(before.fileKey(), after.fileKey())
        assertEquals(before.size(), after.size())
        assertEquals(before.lastModifiedTime(), after.lastModifiedTime())
        return buffer.copyOf(count).also { assertEquals(HASH, sha(it)) }
    }

    private fun sha(bytes: ByteArray): String = MessageDigest.getInstance("SHA-256")
        .digest(bytes).joinToString("") { "%02x".format(it) }

    private companion object {
        val BYTES = "LocalLore original model picker fixture v1. No model or story.\n".toByteArray(Charsets.US_ASCII)
        const val HASH = "648c91a9de82e613189b3920a2098f5d803eb6e244f39b2b631cce24b7be8de0"
    }
}

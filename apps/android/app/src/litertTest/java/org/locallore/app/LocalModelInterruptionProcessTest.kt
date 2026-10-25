/* Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0 */
package org.locallore.app

import java.io.ByteArrayInputStream
import java.io.File
import java.io.InputStream
import java.net.URLClassLoader
import java.nio.ByteBuffer
import java.nio.channels.FileChannel
import java.nio.file.Files
import java.nio.file.StandardOpenOption.CREATE_NEW
import java.nio.file.StandardOpenOption.WRITE
import java.security.MessageDigest
import java.util.concurrent.TimeUnit
import kotlinx.coroutines.runBlocking
import org.junit.Assert.*
import org.junit.Rule
import org.junit.Test
import org.junit.rules.TemporaryFolder

/** A real child JVM dies while holding the store's OS lock. No Android/model/runtime call. */
class LocalModelInterruptionProcessTest {
    @get:Rule val temporary = TemporaryFolder()

    @Test fun processDeathReleasesOsLockAndOnlyKnownStagingIsRecovered() = runBlocking {
        val directory = temporary.newFolder("owned child with spaces").canonicalFile
        val root = File(directory, "model-picker-interruption-v1").apply { mkdir() }
        val sentinel = File(root, "unknown.keep").apply { writeText("preserve unknown") }
        val cache = File(root, "cache").apply { mkdir() }
        val cached = File(cache, "unrelated.keep").apply { writeText("preserve cache") }
        val lock = File(root, "model-import.lock").apply { writeText("preserve lock") }
        val ready = File(directory, "child-ready")
        // Gradle workers do not expose the test runtime through java.class.path alone.
        val locations = linkedSetOf<String>()
        for (initial in listOf(Child::class.java.classLoader, Thread.currentThread().contextClassLoader)) {
            var loader: ClassLoader? = initial
            while (loader != null) {
                if (loader is URLClassLoader) loader.urLs.filter { it.protocol == "file" }
                    .forEach { locations.add(File(it.toURI()).absolutePath) }
                loader = loader.parent
            }
        }
        for (type in listOf(Child::class.java, LocalModelStore::class.java, kotlin.Unit::class.java,
                            kotlinx.coroutines.Job::class.java)) {
            locations.add(File(requireNotNull(type.protectionDomain).codeSource.location.toURI()).absolutePath)
        }
        val arguments = listOf("-Xmx96m", "-XX:ActiveProcessorCount=1", "-cp",
            locations.joinToString(File.pathSeparator), Child::class.java.name, root.path, ready.path)
        val argumentFile = File(directory, "child.args")
        argumentFile.writeText(arguments.joinToString("\n", postfix = "\n") { quoteArgument(it) }, Charsets.UTF_8)
        val executable = File(System.getProperty("java.home"), "bin/" +
            if (requireNotNull(System.getProperty("os.name")).startsWith("Windows")) "java.exe" else "java")
        val output = File(directory, "child-output.txt")
        val child = ProcessBuilder(executable.path, "@${argumentFile.path}")
            .directory(directory).redirectErrorStream(true).redirectOutput(output).start()
        try {
            val deadline = System.nanoTime() + TimeUnit.SECONDS.toNanos(15)
            while (!ready.exists() && child.isAlive && output.length() <= 16_384 && System.nanoTime() < deadline) Thread.sleep(20)
            val failureClass = Regex("[A-Za-z0-9.$]*(?:Exception|Error)")
                .findAll(output.readText().take(1024)).take(4).joinToString(",") { it.value }
                .ifEmpty { "launcher-or-readiness" }
            assertTrue("Child did not reach held partial read ($failureClass)", ready.isFile && child.isAlive)
            assertTrue("Owned child output exceeded bound", output.length() <= 16_384)
            assertEquals("held17", ready.readText())
            val stage = File(root, "model.part")
            assertArrayEquals(bytes.copyOf(17), stage.readBytes())
            assertFalse(File(root, "model.litertlm").exists())
            val lockKey = Files.readAttributes(lock.toPath(), java.nio.file.attribute.BasicFileAttributes::class.java).fileKey()
            // A second store cannot recover another process's live staging or open a provider.
            for (importing in listOf(false, true)) {
                try {
                    if (importing) store(root).import { error("Busy store opened source") }
                    else store(root).installed()
                    fail("Expected live OS lock to refuse competing store")
                } catch (expected: LocalModelException) {
                    assertEquals(LocalModelFailure.BUSY, expected.failure)
                }
                assertArrayEquals(bytes.copyOf(17), stage.readBytes())
            }
            child.destroyForcibly()
            assertTrue("Owned child failed to terminate", child.waitFor(10, TimeUnit.SECONDS))
            assertArrayEquals(bytes.copyOf(17), stage.readBytes()) // No child finally cleanup ran.
            val releaseDeadline = System.nanoTime() + TimeUnit.SECONDS.toNanos(5)
            while (true) {
                try {
                    assertNull(store(root).installed())
                    break
                } catch (pending: LocalModelException) {
                    if (pending.failure != LocalModelFailure.BUSY || System.nanoTime() >= releaseDeadline) {
                        throw AssertionError("Post-death lock did not become available (${pending.failure})")
                    }
                    assertArrayEquals(bytes.copyOf(17), stage.readBytes())
                    Thread.sleep(10)
                }
            }
            assertFalse(stage.exists())
            assertEquals("preserve unknown", sentinel.readText())
            assertEquals("preserve cache", cached.readText())
            assertEquals("preserve lock", lock.readText())
            // Windows can return no file key; contents/real locking remain observable there.
            if (lockKey != null) assertEquals(lockKey,
                Files.readAttributes(lock.toPath(), java.nio.file.attribute.BasicFileAttributes::class.java).fileKey())
            val installed = store(root).import { ByteArrayInputStream(bytes) }
            assertArrayEquals(bytes, installed.model.readBytes())
            assertEquals(installed, store(root).installed())
            assertFalse(stage.exists())
            assertEquals("preserve unknown", sentinel.readText())
            assertEquals("preserve cache", cached.readText())
            assertEquals("preserve lock", lock.readText())
        } finally {
            if (child.isAlive) child.destroyForcibly()
            assertTrue("Owned child cleanup failed", child.waitFor(10, TimeUnit.SECONDS))
        }
    }

    object Child {
        @JvmStatic fun main(arguments: Array<String>) {
            try {
                check(arguments.size == 2)
                val root = File(arguments[0])
                val ready = File(arguments[1])
                runBlocking {
                    store(root).import {
                        object : InputStream() {
                            private var prefix = false
                            override fun read(): Int = error("Bulk read required")
                            override fun read(buffer: ByteArray, offset: Int, length: Int): Int {
                                if (!prefix) {
                                    check(length >= 17)
                                    bytes.copyInto(buffer, offset, 0, 17)
                                    prefix = true
                                    return 17
                                }
                                check(File(root, "model.part").readBytes().contentEquals(bytes.copyOf(17)))
                                val pending = File(ready.parentFile, "child-ready.part")
                                FileChannel.open(pending.toPath(), CREATE_NEW, WRITE).use { channel ->
                                    val ack = ByteBuffer.wrap("held17".toByteArray(Charsets.US_ASCII))
                                    while (ack.hasRemaining()) channel.write(ack)
                                    channel.force(true)
                                }
                                Files.move(pending.toPath(), ready.toPath())
                                // Parent must kill us before this finite emergency failure.
                                Thread.sleep(30_000)
                                error("Owned child death was not observed")
                            }
                        }
                    }
                }
                kotlin.system.exitProcess(2)
            } catch (failure: Throwable) {
                System.err.println("child-failure-class=" + failure.javaClass.name)
                if (failure is LocalModelException) System.err.println("child-store-failure=" + failure.failure.name)
                kotlin.system.exitProcess(1)
            }
        }
    }

    companion object {
        private val bytes = "LocalLore original model picker fixture v1. No model or story.\n".toByteArray(Charsets.US_ASCII)
        private val identity = LocalModelIdentity("synthetic-interruption-v1", bytes.size.toLong(),
            MessageDigest.getInstance("SHA-256").digest(bytes).joinToString("") { "%02x".format(it) }, 1024)
        private fun store(root: File) = LocalModelStore(root, identity, publish = { directory ->
            // Host substitute only; Android verifies the actual no-clobber JNI publication.
            Files.createLink(File(directory, "model.litertlm").toPath(), File(directory, "model.part").toPath())
            Files.delete(File(directory, "model.part").toPath())
        }, availableBytes = { Long.MAX_VALUE })
        private fun quoteArgument(value: String): String {
            require(value.none { it == '\n' || it == '\r' || it == '\u0000' })
            return "\"" + value.replace("\\", "\\\\").replace("\"", "\\\"") + "\""
        }
    }
}

/* Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0 */
package org.locallore.app

import java.io.ByteArrayInputStream
import java.io.File
import java.net.URLClassLoader
import java.nio.ByteBuffer
import java.nio.channels.FileChannel
import java.nio.file.Files
import java.nio.file.StandardOpenOption.CREATE_NEW
import java.nio.file.StandardOpenOption.WRITE
import java.nio.file.attribute.BasicFileAttributes
import java.security.MessageDigest
import java.util.concurrent.TimeUnit
import kotlinx.coroutines.runBlocking
import org.junit.Assert.*
import org.junit.Rule
import org.junit.Test
import org.junit.rules.TemporaryFolder

/** Actual owned JVM/OS lock and process death, without Android/JNI or a model runtime. */
class ReceiptModelTransactionProcessTest {
    @get:Rule val temporary = TemporaryFolder()

    @Test fun heldOsLockRefusesOtherProcessThenHaltLeavesCompletePendingRecoverable() = runBlocking {
        val parent = temporary.newFolder("receipt child with spaces").canonicalFile
        val control = File(parent, "control")
        val data = File(parent, "data")
        val protected = File(parent, "unrelated.keep").apply { writeText("preserve sibling") }
        val ready = File(parent, "ready.txt")
        val readyMarker = File(parent, "ready.complete")
        val locations = linkedSetOf<String>()
        for (initial in listOf(Child::class.java.classLoader, Thread.currentThread().contextClassLoader)) {
            var loader: ClassLoader? = initial
            while (loader != null) {
                if (loader is URLClassLoader) loader.urLs.filter { it.protocol == "file" }
                    .forEach { locations.add(File(it.toURI()).absolutePath) }
                loader = loader.parent
            }
        }
        for (type in listOf(Child::class.java, ReceiptModelTransaction::class.java, kotlin.Unit::class.java,
            kotlinx.coroutines.Job::class.java)) {
            locations.add(File(requireNotNull(type.protectionDomain).codeSource.location.toURI()).absolutePath)
        }
        val arguments = listOf("-Xmx96m", "-XX:ActiveProcessorCount=1", "-cp",
            locations.joinToString(File.pathSeparator), Child::class.java.name, control.path, data.path,
            ready.path, readyMarker.path)
        val argumentFile = File(parent, "child.args")
        argumentFile.writeText(arguments.joinToString("\n", postfix = "\n") { quoteArgument(it) }, Charsets.UTF_8)
        val executable = File(System.getProperty("java.home"), "bin/" +
            if (requireNotNull(System.getProperty("os.name")).startsWith("Windows")) "java.exe" else "java")
        val output = File(parent, "child-output.txt")
        val child = ProcessBuilder(executable.path, "@${argumentFile.path}").directory(parent)
            .redirectErrorStream(true).redirectOutput(output).start()
        try {
            val deadline = System.nanoTime() + TimeUnit.SECONDS.toNanos(15)
            while (!readyMarker.exists() && child.isAlive && output.length() <= 16_384 && System.nanoTime() < deadline) {
                Thread.sleep(20)
            }
            // Return only bounded exception class metadata when startup fails, never raw output.
            val failureClass = Regex("[A-Za-z0-9.$]*(?:Exception|Error)")
                .findAll(output.inputStream().use { String(it.readNBytes(1024), Charsets.UTF_8) })
                .take(4).joinToString(",") { it.value }.ifEmpty { "launcher-or-readiness" }
            assertTrue("Child did not reach forced pending state ($failureClass)", readyMarker.isFile && child.isAlive)
            assertTrue("Owned child output exceeded bound", output.length() <= 16_384)
            assertEquals(0, readyMarker.length())
            assertEquals("forced63\n", ready.readText(Charsets.US_ASCII))
            val model = File(data, "model.litertlm")
            val receipt = File(control, "model.receipt")
            val accepted = File(control, "model.accepted")
            val owner = File(data, "model.owner")
            val lock = File(control, "model-import.lock")
            assertArrayEquals(bytes, model.readBytes())
            assertFalse(accepted.exists())
            val receiptBefore = receipt.readBytes()
            val ownerBefore = owner.readBytes()
            assertTrue(receiptBefore.size <= 512)
            val lockKey = Files.readAttributes(lock.toPath(), BasicFileAttributes::class.java).fileKey()
            for (operation in 0..2) {
                try {
                    when (operation) {
                        0 -> store(control, data).installed()
                        1 -> store(control, data).import { error("Live foreign lock must prevent source open") }
                        else -> store(control, data).discardUncommitted()
                    }
                    fail("Expected actual live OS lock refusal")
                } catch (expected: LocalModelException) {
                    assertEquals(LocalModelFailure.BUSY, expected.failure)
                }
                assertArrayEquals(bytes, model.readBytes())
                assertArrayEquals(receiptBefore, receipt.readBytes())
                assertArrayEquals(ownerBefore, owner.readBytes())
                assertFalse(accepted.exists())
            }
            // The child itself halts inside DATA_FORCED; no cancellation/finally path runs.
            child.outputStream.write('H'.code)
            child.outputStream.flush()
            assertTrue("Owned child halt did not terminate", child.waitFor(5, TimeUnit.SECONDS))
            assertEquals(73, child.exitValue())
            assertArrayEquals(bytes, model.readBytes())
            assertArrayEquals(receiptBefore, receipt.readBytes())
            assertArrayEquals(ownerBefore, owner.readBytes())
            assertFalse(accepted.exists())
            // Windows may retain a transient lock after process termination is observed.
            // Reacquire only; every BUSY observation must leave the pending bytes untouched.
            val releasedBy = System.nanoTime() + TimeUnit.SECONDS.toNanos(5)
            while (true) {
                try {
                    assertNull(store(control, data).installed())
                    break
                } catch (pending: LocalModelException) {
                    if (pending.failure != LocalModelFailure.BUSY || System.nanoTime() >= releasedBy) {
                        throw AssertionError("Post-halt lock did not become available (${pending.failure})")
                    }
                    assertArrayEquals(bytes, model.readBytes())
                    assertArrayEquals(receiptBefore, receipt.readBytes())
                    assertArrayEquals(ownerBefore, owner.readBytes())
                    assertFalse(accepted.exists())
                    Thread.sleep(10)
                }
            }
            assertFalse(accepted.exists())
            val resumed = store(control, data).import { error("Complete pending recovery must not open source") }
            assertEquals(LocalModelFiles(data, model, File(data, "cache")), resumed)
            assertArrayEquals(bytes, resumed.model.readBytes())
            assertArrayEquals(receiptBefore, receipt.readBytes())
            assertArrayEquals(ownerBefore, owner.readBytes())
            assertTrue(accepted.isFile)
            assertEquals(0, accepted.length())
            assertEquals(resumed, store(control, data).installed())
            assertEquals("preserve sibling", protected.readText())
            if (lockKey != null) assertEquals(lockKey,
                Files.readAttributes(lock.toPath(), BasicFileAttributes::class.java).fileKey())
            assertTrue("Owned child output exceeded bound", output.length() <= 16_384)
        } finally {
            // Only this ProcessBuilder-owned child is eligible for emergency termination.
            if (child.isAlive) child.destroyForcibly()
            assertTrue("Owned child cleanup failed", child.waitFor(5, TimeUnit.SECONDS))
        }
    }

    object Child {
        @JvmStatic fun main(arguments: Array<String>) {
            try {
                // Bound the entire owned child lifetime, including startup/import before readiness.
                Thread({
                    Thread.sleep(20_000)
                    Runtime.getRuntime().halt(74)
                }, "receipt-child-deadline").apply { isDaemon = true; start() }
                check(arguments.size == 4)
                val control = File(arguments[0])
                val data = File(arguments[1])
                val ready = File(arguments[2])
                val readyMarker = File(arguments[3])
                runBlocking {
                    store(control, data) { checkpoint ->
                        if (checkpoint == ReceiptCheckpoint.DATA_FORCED) {
                            check(File(data, "model.litertlm").readBytes().contentEquals(bytes))
                            forceNew(ready, "forced63\n".toByteArray(Charsets.US_ASCII))
                            forceNew(readyMarker, byteArrayOf())
                            check(System.`in`.read() == 'H'.code)
                            Runtime.getRuntime().halt(73)
                        }
                    }.import { ByteArrayInputStream(bytes) }
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
        private val identity = LocalModelIdentity("synthetic-receipt-v1", 63,
            MessageDigest.getInstance("SHA-256").digest(bytes).joinToString("") { "%02x".format(it) }, 1024)
        private fun store(control: File, data: File, checkpoint: (ReceiptCheckpoint) -> Unit = {}) =
            ReceiptModelTransaction(control, data, identity, { Long.MAX_VALUE }, checkpoint = checkpoint)
        private fun forceNew(file: File, bytes: ByteArray) {
            FileChannel.open(file.toPath(), CREATE_NEW, WRITE).use { channel ->
                val data = ByteBuffer.wrap(bytes)
                while (data.hasRemaining()) channel.write(data)
                channel.force(true)
            }
        }
        private fun quoteArgument(value: String): String {
            require(value.none { it == '\n' || it == '\r' || it == '\u0000' })
            return "\"" + value.replace("\\", "\\\\").replace("\"", "\\\"") + "\""
        }
    }
}

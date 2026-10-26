/* Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0 */
package org.locallore.app

import android.os.Build
import android.os.Process
import android.os.SystemClock
import androidx.test.ext.junit.runners.AndroidJUnit4
import androidx.test.platform.app.InstrumentationRegistry
import java.io.ByteArrayOutputStream
import java.io.File
import java.util.UUID
import java.util.concurrent.TimeUnit
import java.util.concurrent.atomic.AtomicBoolean
import java.util.concurrent.atomic.AtomicInteger
import java.util.zip.ZipFile
import org.json.JSONObject
import org.junit.Assert.*
import org.junit.Assume.assumeTrue
import org.junit.Before
import org.junit.Test
import org.junit.runner.RunWith

/** Actual APK-contained JNI load only. Retirement itself belongs to the external saved-task cohort. */
@RunWith(AndroidJUnit4::class)
class RetiredSelectionFixtureInstrumentedTest {
    private val product = "org.locallore.app.draftprocessverify"
    private lateinit var home: File
    private lateinit var productApk: File
    private lateinit var testApk: File
    private lateinit var productHash: String
    private lateinit var testHash: String
    private lateinit var libraryHash: String

    @Before fun onlyDedicatedApi35ProcessProfile() {
        // Check profile before paths, hashes, process creation, or any native/library access.
        assumeTrue(BuildConfig.INPUT_PROCESS_VERIFICATION && BuildConfig.APPLICATION_ID == product)
        assumeTrue(Build.VERSION.SDK_INT == 35 && Build.SUPPORTED_ABIS.firstOrNull() == "x86_64")
        val instrumentation = InstrumentationRegistry.getInstrumentation()
        check(instrumentation.targetContext.packageName == product) { "fixture_product_identity" }
        check(instrumentation.targetContext.applicationInfo.uid == Process.myUid()) { "fixture_uid_identity" }
        home = File("/data/user/0/$product")
        val fixedHome = try { RetiredSelectionFixtureMain.fixedHome() }
        catch (_: Exception) {
            throw AssertionError(homeDiagnostic(instrumentation.targetContext.applicationInfo.dataDir,
                instrumentation.targetContext.applicationInfo.uid))
        }
        check(home.canonicalFile == fixedHome && home.isDirectory &&
            File(instrumentation.targetContext.applicationInfo.dataDir).canonicalFile == fixedHome) {
            homeDiagnostic(instrumentation.targetContext.applicationInfo.dataDir,
                instrumentation.targetContext.applicationInfo.uid)
        }
        home = fixedHome
        productApk = File(instrumentation.targetContext.applicationInfo.sourceDir)
        testApk = File(instrumentation.context.applicationInfo.sourceDir)
        check(listOf(productApk, testApk).all { it == it.canonicalFile && it.isFile && it.canRead() && !it.canWrite() }) {
            "fixture_apk_identity"
        }
        check(productApk != testApk) { "fixture_distinct_apks" }
        productHash = RetiredSelectionFixtureMain.hashFile(productApk, 128L * 1024 * 1024)
        testHash = RetiredSelectionFixtureMain.hashFile(testApk, 128L * 1024 * 1024)
        libraryHash = ZipFile(productApk).use { zip ->
            val entry = checkNotNull(zip.getEntry("lib/x86_64/liblocallore_android.so")) { "fixture_library_entry" }
            check(entry.method == java.util.zip.ZipEntry.STORED && entry.size in 1..(64L * 1024 * 1024)) {
                "fixture_library_storage"
            }
            val digest = java.security.MessageDigest.getInstance("SHA-256")
            var total = 0L
            zip.getInputStream(entry).use { input ->
                val buffer = ByteArray(16384)
                while (true) {
                    val n = input.read(buffer)
                    if (n < 0) break
                    total += n
                    check(total <= entry.size) { "fixture_library_bound" }
                    digest.update(buffer, 0, n)
                }
            }
            check(total == entry.size) { "fixture_library_size" }
            digest.digest().joinToString("") { "%02x".format(java.util.Locale.ROOT, it.toInt() and 255) }
        }
    }

    private fun pathClassification(path: String): String = when (path) {
        "/data/user/0/$product" -> "USER_ZERO"
        "/data/data/$product" -> "DATA_DATA"
        else -> {
            val bytes = path.toByteArray(Charsets.UTF_8)
            val hash = java.security.MessageDigest.getInstance("SHA-256").digest(bytes)
                .joinToString("") { "%02x".format(java.util.Locale.ROOT, it.toInt() and 255) }
            "OTHER_HASH:$hash:bytes=${bytes.size}"
        }
    }

    private fun homeDiagnostic(targetDataDir: String, targetUid: Int): String = try {
        val target = File(targetDataDir)
        "fixture_home_identity homeCanonical=${pathClassification(home.canonicalPath)} " +
            "homeDirectory=${home.isDirectory} targetCanonical=${pathClassification(target.canonicalPath)} " +
            "targetDirectory=${target.isDirectory} targetRaw=${pathClassification(targetDataDir)} " +
            "selfEqualsTargetUid=${Process.myUid() == targetUid}"
    } catch (_: Exception) { "fixture_home_identity diagnostic_unavailable" }

    private fun args(): MutableList<String> = mutableListOf("load", UUID.randomUUID().toString().replace("-", "").take(16),
        Process.myUid().toString(), productHash, testHash, productApk.path + "!/lib/x86_64",
        "load_a", "load_b", "main", "load_child", "0")

    private data class DatabaseMetadata(val exists: Boolean, val length: Long, val modified: Long)
    private fun databaseMetadata(): DatabaseMetadata {
        val database = File(home, "no_backup/workspace-v1/stories.sqlite3")
        return DatabaseMetadata(database.exists(), database.length(), database.lastModified())
    }

    private data class Result(val proof: JSONObject, val entered: Long, val finished: Long)

    private fun launch(arguments: List<String>): Result {
        check(arguments.size == 11) { "fixture_arguments" }
        val entered = SystemClock.uptimeMillis()
        val child = try {
            ProcessBuilder(listOf("/system/bin/app_process", "/", "--nice-name=$product:retirement-fixture",
                "org.locallore.app.RetiredSelectionFixtureMain") + arguments).also {
                it.directory(home)
                it.environment()["CLASSPATH"] = testApk.path + ":" + productApk.path
            }.start()
        } catch (_: Exception) { throw AssertionError("fixture_spawn_failed") }
        val output = ByteArrayOutputStream()
        val stderr = AtomicInteger()
        val total = AtomicInteger()
        val overflow = AtomicBoolean()
        val readFailed = AtomicBoolean()
        val readers = listOf(child.inputStream, child.errorStream).mapIndexed { index, input ->
            Thread({
                try {
                    val buffer = ByteArray(512)
                    while (true) {
                        val n = input.read(buffer)
                        if (n < 0) break
                        if (total.addAndGet(n) > 4096) { overflow.set(true); break }
                        if (index == 0) synchronized(output) { output.write(buffer, 0, n) }
                        else stderr.addAndGet(n)
                    }
                } catch (_: Exception) { readFailed.set(true) }
            }, "retired-fixture-pipe-$index").also { it.isDaemon = true }
        }
        var exited = false
        var stopped = false
        try {
            readers.forEach { it.start() }
            child.outputStream.close()
            exited = child.waitFor(20, TimeUnit.SECONDS)
        } finally {
            if (!exited) {
                stopped = true
                child.destroy()
                exited = child.waitFor(1, TimeUnit.SECONDS)
            }
            if (!exited) {
                child.destroyForcibly()
                exited = child.waitFor(2, TimeUnit.SECONDS)
            }
            if (exited) {
                readers.forEach { it.join(1_000) }
                if (readers.none { it.isAlive }) {
                    listOf(child.inputStream, child.errorStream, child.outputStream).forEach {
                        try { it.close() } catch (_: Exception) { }
                    }
                }
            }
        }
        // No dependent metadata reads or second child dispatch after uncertain child/pipe cleanup.
        check(exited && !child.isAlive && readers.none { it.isAlive }) { "fixture_cleanup_unknown" }
        check(!stopped && child.exitValue() == 0) { "fixture_terminal_exit" }
        check(!overflow.get() && !readFailed.get() && stderr.get() == 0) { "fixture_capture_failed" }
        val bytes = synchronized(output) { output.toByteArray() }
        check(bytes.size in 2..4096 && bytes.last() == '\n'.code.toByte() && bytes.dropLast(1).none {
            it == '\n'.code.toByte() || it == '\r'.code.toByte()
        }) { "fixture_single_json_line" }
        val proof = RetiredSelectionFixtureMain.json(bytes, 4096)
        return Result(proof, entered, SystemClock.uptimeMillis())
    }

    private fun refused(arguments: List<String>, expectedStage: String) {
        val before = databaseMetadata()
        val result = launch(arguments).proof
        RetiredSelectionFixtureMain.keys(result, "version", "scope", "mode", "run_id", "status", "stage")
        assertEquals(1L, RetiredSelectionFixtureMain.number(result, "version"))
        assertEquals("locallore_retired_fixture_v1", result.getString("scope"))
        assertEquals("load", result.getString("mode"))
        assertEquals(arguments[1], result.getString("run_id"))
        assertEquals("failed", result.getString("status"))
        assertEquals(expectedStage, result.getString("stage"))
        assertEquals("load guard must leave database metadata unchanged", before, databaseMetadata())
    }

    @Test fun loadModeFindsStoredApkLibraryUnderActualProductUidWithoutOpeningWorkspace() {
        val arguments = args()
        val before = databaseMetadata()
        val result = launch(arguments)
        val proof = result.proof
        RetiredSelectionFixtureMain.keys(proof, "version", "scope", "mode", "run_id", "status", "stage", "pid", "uid",
            "started_uptime_ms", "product_sha256", "test_sha256", "library_sha256", "scope_sha256", "commit_attempts",
            "archive_closed", "workspace_closed", "before", "after")
        assertEquals(1L, RetiredSelectionFixtureMain.number(proof, "version"))
        assertEquals("locallore_retired_fixture_v1", proof.getString("scope"))
        assertEquals("load", proof.getString("mode"))
        assertEquals(arguments[1], proof.getString("run_id"))
        assertEquals("passed", proof.getString("status"))
        assertEquals("LOAD_COMPLETE", proof.getString("stage"))
        assertEquals(Process.myUid().toLong(), RetiredSelectionFixtureMain.number(proof, "uid"))
        val pid = RetiredSelectionFixtureMain.number(proof, "pid")
        assertTrue(pid > 0 && pid != Process.myPid().toLong())
        assertFalse("owned helper must already be gone", File("/proc/$pid").exists())
        assertTrue(RetiredSelectionFixtureMain.number(proof, "started_uptime_ms") in result.entered..result.finished)
        assertEquals(productHash, proof.getString("product_sha256"))
        assertEquals(testHash, proof.getString("test_sha256"))
        assertEquals(libraryHash, proof.getString("library_sha256"))
        assertEquals(RetiredSelectionFixtureMain.sha("1\nload_a\nload_b\nmain\nload_child\n".toByteArray()),
            proof.getString("scope_sha256"))
        assertEquals(0L, RetiredSelectionFixtureMain.number(proof, "commit_attempts"))
        assertTrue(RetiredSelectionFixtureMain.bool(proof, "archive_closed"))
        assertTrue(RetiredSelectionFixtureMain.bool(proof, "workspace_closed"))
        assertTrue(proof.isNull("before") && proof.isNull("after"))
        assertEquals("load must leave database metadata unchanged", before, databaseMetadata())
    }

    @Test fun wrongUidRefusesBeforeNativeOrWorkspaceAccess() {
        refused(args().also { it[2] = (Process.myUid() + 1).toString() }, "ARGUMENTS")
    }

    @Test fun wrongApkHashRefusesBeforeNativeOrWorkspaceAccess() {
        refused(args().also { it[3] = if (productHash == "0".repeat(64)) "1".repeat(64) else "0".repeat(64) }, "APK_HASH")
    }

    @Test fun writableOrAlternateNativeDirectoryCannotReplacePinnedApkZipPath() {
        refused(args().also { it[5] = home.path + "/no_backup/native" }, "CLASSPATH")
    }
}

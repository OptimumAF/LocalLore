/* Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0 */
package org.locallore.app

import android.app.ActivityManager
import android.app.Application
import android.content.Context
import android.os.Build
import android.os.Bundle
import android.os.Looper
import android.os.Process
import android.os.SystemClock
import android.system.Os
import androidx.compose.ui.test.assertIsEnabled
import androidx.compose.ui.test.junit4.createEmptyComposeRule
import androidx.compose.ui.test.onNodeWithTag
import androidx.compose.ui.test.performScrollTo
import androidx.test.core.app.ActivityScenario
import androidx.test.ext.junit.runners.AndroidJUnit4
import androidx.test.filters.SdkSuppress
import androidx.test.platform.app.InstrumentationRegistry
import java.io.File
import java.io.InputStream
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
import java.util.concurrent.atomic.AtomicBoolean
import java.util.concurrent.atomic.AtomicLong
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.NonCancellable
import kotlinx.coroutines.runBlocking
import kotlinx.coroutines.withContext
import kotlinx.coroutines.withTimeout
import org.json.JSONArray
import org.json.JSONObject
import org.junit.After
import org.junit.Assert.*
import org.junit.Assume.assumeTrue
import org.junit.Rule
import org.junit.Test
import org.junit.runner.RunWith

/** These four heavyweight classes require exact, separately admitted class selection. */
internal enum class ReceiptRealPhase(val file: String, val budgetMs: Long, val checks: Set<String>) {
    SOURCE_PREFLIGHT("source-preflight", 30_000, setOf("build_identity_exact", "source_context_confined",
        "source_owner_exact", "probe_exact", "source_whitelist_exact", "staged_model_absent",
        "candidate_access_receipt", "candidate_roots_absent", "candidate_installed_null_noncreating",
        "memory_eligible", "userdata_copy_capacity", "external_import_capacity")),
    IMPORT("import", 150_000, setOf("source_context_confined", "source_owner_probe_exact", "source_whitelist_exact",
        "source_model_regular_uid", "source_fullhash_exact", "source_verify_closed_once", "candidate_access_receipt",
        "preaccept_runtime_refused", "setup_missing_before_import", "import_source_off_main_closed_once",
        "import_source_exact_bytes", "setup_ready_after_import", "accepted_full_recheck", "accepted_receipt_owner_exact",
        "memory_eligible", "capacity_eligible")),
    PLAY("play", 170_000, setOf("memory_eligible", "accepted_full_recheck", "runtime_guard_passed",
        "production_transport_local", "native_worker_off_main", "initial_revision_zero", "fixed_free_text_submitted_once",
        "prepared_after_known_worker_close", "accepted_post_sdk_full_recheck", "canonical_revision_one",
        "canonical_given_to_mira", "canonical_single_receipt", "local_profile_exact", "candidate_owner_retained", "native_handle_closed")),
    REOPEN("reopen", 120_000, setOf("prior_play_proof_exact", "process_identity_changed", "source_unopened",
        "candidate_access_receipt", "accepted_full_recheck", "runtime_guard_passed", "setup_ready_after_reopen",
        "production_transport_local", "no_free_text_call", "canonical_revision_one", "canonical_gift_receipt_unchanged",
        "native_handle_closed", "memory_eligible")),
}

internal class ReceiptRealDeadline(val phase: ReceiptRealPhase) {
    val started = SystemClock.elapsedRealtime()
    fun remaining(cap: Long = phase.budgetMs): Long {
        val left = phase.budgetMs - elapsed()
        check(left > 0) { "Real receipt phase budget expired" }
        return minOf(left, cap)
    }
    fun elapsed(): Long = SystemClock.elapsedRealtime() - started
}

internal class ReceiptRealCounts {
    private val verificationClaimed = AtomicBoolean()
    private val importClaimed = AtomicBoolean()
    val verifyOpened = AtomicLong()
    val verifyClosed = AtomicLong()
    val verifyBytes = AtomicLong()
    val importOpened = AtomicLong()
    val importClosed = AtomicLong()
    val importBytes = AtomicLong()
    val importActive = AtomicLong()
    private val importReadCalls = AtomicLong()
    val offMain = AtomicBoolean(true)
    fun claim(verification: Boolean) = (if (verification) verificationClaimed else importClaimed).compareAndSet(false, true)
    fun observeImportRead() {
        importReadCalls.updateAndGet { if (it == Long.MAX_VALUE) it else it + 1 }
    }
    /** Capped independent source observations, never persisted bytes or a resource proof. */
    fun importFailureProgress(): ReceiptSetupSourceProgress {
        val opened = importOpened.get()
        val closed = importClosed.get()
        val active = importActive.get()
        val reads = importReadCalls.get()
        val bytes = importBytes.get()
        val limit = ReceiptSetupFailureTrace.MAX_PROGRESS.toLong()
        fun clipped(value: Long): Int = value.coerceIn(0L, limit).toInt()
        return ReceiptSetupSourceProgress(opened = clipped(opened), closed = clipped(closed), active = clipped(active),
            readCalls = clipped(reads), bytesRead = clipped(bytes),
            readsSaturated = reads > limit, bytesSaturated = bytes > limit)
    }
    fun unopened() = verifyOpened.get() == 0L && verifyClosed.get() == 0L && verifyBytes.get() == 0L &&
        importOpened.get() == 0L && importClosed.get() == 0L && importBytes.get() == 0L
}

/** Context supplies every path. Reopen deliberately never calls sourceDirectory(). */
internal class ReceiptRealEnvironment private constructor(
    val context: Context, val internal: File, val external: File, private val volume: AndroidModelVolume,
) {
    val proofRoot = File(internal, "receipt-real-proof-v1")
    val userdataBefore = internal.usableSpace
    val externalBefore = external.usableSpace
    val memoryBefore = memory()

    fun memory(): ActivityManager.MemoryInfo = ActivityManager.MemoryInfo().also {
        context.getSystemService(ActivityManager::class.java).getMemoryInfo(it)
    }
    fun memoryEligible() = memoryBefore.totalMem in 7 * GIB..8 * GIB && memoryBefore.availMem >= 4 * GIB
    fun admit(missing: Long = 0) {
        volume.admit(missing)
        check(internal.usableSpace >= USERDATA_FLOOR)
        absent(volume.root)
        absent(File(internal, "local-model-v1"))
    }
    fun candidateAbsent(): Boolean = !Files.exists(File(internal, AndroidReceiptModelAccess.CONTROL_CHILD).toPath(), NOFOLLOW_LINKS) &&
        !Files.exists(File(external, AndroidReceiptModelAccess.DATA_CHILD).toPath(), NOFOLLOW_LINKS)
    fun sourceDirectory(modelExpected: Boolean): File {
        val root = File(internal, "receipt-real-source-v1")
        strictDirectory(root)
        check(root.parentFile == internal)
        val names = setOf("source.owner", "probe.txt") + if (modelExpected) setOf("model.litertlm") else emptySet()
        entries(root, names)
        check(read(File(root, "source.owner"), 64).contentEquals(OWNER))
        check(read(File(root, "probe.txt"), 61).contentEquals(PROBE))
        check(sha(PROBE) == PROBE_SHA)
        if (modelExpected) regular(File(root, "model.litertlm"), MODEL_BYTES)
        else absent(File(root, "model.litertlm"))
        return root
    }
    fun prior(phase: ReceiptRealPhase): Pair<JSONObject, String> {
        admit()
        strictDirectory(proofRoot)
        val expectedPhases = ReceiptRealPhase.entries.take(phase.ordinal + 1)
        entries(proofRoot, expectedPhases.flatMap { listOf("${it.file}-v1.json", "${it.file}-ready-v1.txt") }.toSet())
        val raw = read(File(proofRoot, "${phase.file}-v1.json"), 4096)
        check(read(File(proofRoot, "${phase.file}-ready-v1.txt"), 0).isEmpty())
        val value = JSONObject(String(raw, Charsets.US_ASCII))
        check(canonical(value).toByteArray(Charsets.US_ASCII).contentEquals(raw))
        check(value.keys().asSequence().toSet() == proofKeys(phase))
        check(number(value, "version") == 1L && value.get("phase") == phase.name)
        check(number(value, "pid") > 0 && number(value, "pid") < Int.MAX_VALUE.toLong() && number(value, "start") > 0)
        check(number(value, "uid") == Process.myUid().toLong() && value.get("process") == PACKAGE)
        check(number(value, "model_bytes") == MODEL_BYTES && value.get("model_sha256") == MODEL_SHA)
        check(number(value, "elapsed_ms") in 0..phase.budgetMs)
        check(value.get("sdk_invoked") == (phase == ReceiptRealPhase.PLAY) && value.get("publication_native_invoked") == false)
        val imported = phase == ReceiptRealPhase.IMPORT
        for (key in listOf("source_verify_opened", "source_verify_closed", "source_import_opened", "source_import_closed")) {
            check(number(value, key) == if (imported) 1L else 0L)
        }
        for (key in listOf("source_verify_bytes", "source_import_bytes")) check(number(value, key) == if (imported) MODEL_BYTES else 0L)
        for (key in listOf("userdata_free_before", "userdata_free_after")) check(number(value, key) >= USERDATA_FLOOR)
        for (key in listOf("external_free_before", "external_free_after")) check(number(value, key) >= 2 * GIB)
        val total = number(value, "memory_total_bytes")
        check(total in 7 * GIB..8 * GIB && number(value, "memory_available_before") in 4 * GIB..total)
        check(number(value, "memory_available_after") in 0..total)
        val checks = value.getJSONObject("checks")
        check(checks.keys().asSequence().toSet() == phase.checks)
        phase.checks.forEach { check(checks.get(it) == true) }
        if (phase != ReceiptRealPhase.SOURCE_PREFLIGHT) {
            check(number(value, "prior_pid") > 0 && number(value, "prior_pid") < Int.MAX_VALUE.toLong() && number(value, "prior_start") > 0)
            check(value.getString(priorKey(phase)).matches(Regex("[0-9a-f]{64}")))
        }
        if (phase in setOf(ReceiptRealPhase.PLAY, ReceiptRealPhase.REOPEN)) {
            check(number(value, "revision") == 1L && number(value, "receipt_count") == 1L)
            check(value.getString("receipt_sha256").matches(Regex("[0-9a-f]{64}")))
        }
        if (phase == ReceiptRealPhase.PLAY) {
            check(number(value, "repairs") in 0..1 && value.get("fallback") is Boolean)
        }
        return value to sha(raw)
    }
    fun proof(phase: ReceiptRealPhase, deadline: ReceiptRealDeadline, counts: ReceiptRealCounts,
        checks: Map<String, Boolean>, extra: JSONObject = JSONObject()) {
        admit()
        deadline.remaining()
        check(checks.keys == phase.checks && checks.values.all { it })
        val memoryAfter = memory()
        check(memoryAfter.totalMem == memoryBefore.totalMem && memoryAfter.availMem in 0..memoryAfter.totalMem)
        val flags = JSONObject()
        checks.forEach { (key, value) -> flags.put(key, value) }
        val value = JSONObject().put("version", 1).put("phase", phase.name).put("pid", Process.myPid())
            .put("start", Process.getStartElapsedRealtime()).put("uid", Process.myUid()).put("process", PACKAGE)
            .put("model_bytes", MODEL_BYTES).put("model_sha256", MODEL_SHA)
            .put("source_verify_opened", counts.verifyOpened.get()).put("source_verify_closed", counts.verifyClosed.get())
            .put("source_verify_bytes", counts.verifyBytes.get()).put("source_import_opened", counts.importOpened.get())
            .put("source_import_closed", counts.importClosed.get()).put("source_import_bytes", counts.importBytes.get())
            .put("sdk_invoked", phase == ReceiptRealPhase.PLAY).put("publication_native_invoked", false)
            .put("elapsed_ms", deadline.elapsed()).put("userdata_free_before", userdataBefore).put("userdata_free_after", internal.usableSpace)
            .put("external_free_before", externalBefore).put("external_free_after", external.usableSpace)
            .put("memory_total_bytes", memoryBefore.totalMem).put("memory_available_before", memoryBefore.availMem)
            .put("memory_available_after", memoryAfter.availMem).put("checks", flags)
        extra.keys().forEach { key -> check(!value.has(key)); value.put(key, extra.get(key)) }
        check(value.keys().asSequence().toSet() == proofKeys(phase))
        if (phase == ReceiptRealPhase.SOURCE_PREFLIGHT) absent(proofRoot)
        if (!Files.exists(proofRoot.toPath(), NOFOLLOW_LINKS)) Files.createDirectory(proofRoot.toPath())
        strictDirectory(proofRoot)
        val raw = canonical(value).toByteArray(Charsets.US_ASCII)
        check(raw.size in 1..4096)
        forcedNew(File(proofRoot, "${phase.file}-v1.json"), raw)
        forcedNew(File(proofRoot, "${phase.file}-ready-v1.txt"), byteArrayOf())
    }
    companion object {
        const val PACKAGE = "org.locallore.app.modelvolumeverify"
        const val GIB = 1_073_741_824L
        const val USERDATA_FLOOR = GIB + 128 * 1024 * 1024
        const val MODEL_BYTES = 2_588_147_712L
        const val MODEL_SHA = "181938105e0eefd105961417e8da75903eacda102c4fce9ce90f50b97139a63c"
        const val PROBE_SHA = "a4ab41067238a10078cec646fcf00a952c1c58511661d5d8dc4632b37ea017af"
        val OWNER = "locallore-real-source-v1\n".toByteArray(Charsets.US_ASCII)
        val PROBE = "LocalLore real candidate source probe v1. No model or story.\n".toByteArray(Charsets.US_ASCII)
        fun open(context: Context): ReceiptRealEnvironment {
            if (Build.VERSION.SDK_INT < 30) error("Real receipt profile unavailable")
            offMain()
            val app = context.applicationContext
            check(BuildConfig.MODEL_RECEIPT_VERIFICATION && BuildConfig.MODEL_VOLUME_VERIFICATION)
            check(app.packageName == PACKAGE && app.applicationInfo.uid == Process.myUid() && Application.getProcessName() == PACKAGE)
            check(CandidateLocalModel.identity.bytes == MODEL_BYTES && CandidateLocalModel.identity.sha256 == MODEL_SHA)
            val internal = app.noBackupFilesDir.canonicalFile.also(::strictDirectory)
            val volume = AndroidModelVolume.select(app)
            return ReceiptRealEnvironment(app, internal, requireNotNull(volume.root.parentFile).also(::strictDirectory), volume).also { it.admit() }
        }
        fun offMain() = check(Looper.myLooper() != Looper.getMainLooper())
        fun number(value: JSONObject, key: String): Long {
            val field = value.get(key)
            check(field is Int || field is Long)
            return (field as Number).toLong()
        }
        fun sha(raw: ByteArray) = MessageDigest.getInstance("SHA-256").digest(raw).joinToString("") { "%02x".format(it) }
        fun canonical(value: Any?): String = when (value) {
            is JSONObject -> value.keys().asSequence().toList().sorted().joinToString(",", "{", "}") { JSONObject.quote(it) + ":" + canonical(value.get(it)) }
            is JSONArray -> (0 until value.length()).joinToString(",", "[", "]") { canonical(value.get(it)) }
            is String -> JSONObject.quote(value)
            is Boolean -> value.toString()
            is Number -> JSONObject.numberToString(value)
            null, JSONObject.NULL -> "null"
            else -> error("Unsupported canonical value")
        }
        fun regular(file: File, expected: Long? = null): BasicFileAttributes {
            val value = Files.readAttributes(file.toPath(), BasicFileAttributes::class.java, NOFOLLOW_LINKS)
            check(value.isRegularFile && !value.isSymbolicLink && (expected == null || value.size() == expected))
            check(Os.lstat(file.path).st_uid == Process.myUid())
            return value
        }
        fun strictDirectory(file: File) {
            check(file.isAbsolute && file.canonicalFile == file && file.toPath().normalize() == file.toPath())
            var path: Path? = file.toPath()
            while (path != null) { check(Files.isDirectory(path, NOFOLLOW_LINKS) && !Files.isSymbolicLink(path)); path = path.parent }
        }
        fun absent(file: File) = check(!Files.exists(file.toPath(), NOFOLLOW_LINKS))
        fun entries(file: File, expected: Set<String>) {
            Files.newDirectoryStream(file.toPath()).use { stream -> check(stream.map { it.fileName.toString() }.toSet() == expected) }
        }
        fun read(file: File, cap: Int): ByteArray {
            val before = regular(file)
            check(before.size() <= cap)
            val result = ByteArray(cap + 1)
            var count = 0
            Files.newInputStream(file.toPath(), READ, NOFOLLOW_LINKS).use { input ->
                while (count < result.size) { val n = input.read(result, count, result.size - count); if (n < 0) break; check(n > 0); count += n }
            }
            val after = regular(file)
            check(count <= cap && count.toLong() == before.size() && before.fileKey() == after.fileKey() && before.size() == after.size() && before.lastModifiedTime() == after.lastModifiedTime())
            return result.copyOf(count)
        }
        fun forcedNew(file: File, bytes: ByteArray) {
            FileChannel.open(file.toPath(), CREATE_NEW, WRITE, NOFOLLOW_LINKS).use { channel ->
                val buffer = ByteBuffer.wrap(bytes)
                while (buffer.hasRemaining()) check(channel.write(buffer) > 0)
                channel.force(true)
            }
        }
        fun proofKeys(phase: ReceiptRealPhase): Set<String> {
            val common = setOf("version", "phase", "pid", "start", "uid", "process", "model_bytes", "model_sha256",
                "source_verify_opened", "source_verify_closed", "source_verify_bytes", "source_import_opened", "source_import_closed",
                "source_import_bytes", "sdk_invoked", "publication_native_invoked", "elapsed_ms", "userdata_free_before", "userdata_free_after",
                "external_free_before", "external_free_after", "memory_total_bytes", "memory_available_before", "memory_available_after", "checks")
            val prior = if (phase == ReceiptRealPhase.SOURCE_PREFLIGHT) emptySet() else setOf("prior_pid", "prior_start", priorKey(phase))
            val play = if (phase in setOf(ReceiptRealPhase.PLAY, ReceiptRealPhase.REOPEN)) setOf("revision", "receipt_count", "receipt_sha256") else emptySet()
            return common + prior + play + if (phase == ReceiptRealPhase.PLAY) setOf("repairs", "fallback") else emptySet()
        }
        fun priorKey(phase: ReceiptRealPhase): String = when (phase) {
            ReceiptRealPhase.IMPORT -> "prior_preflight_sha256"
            ReceiptRealPhase.PLAY -> "prior_import_sha256"
            ReceiptRealPhase.REOPEN -> "prior_play_sha256"
            ReceiptRealPhase.SOURCE_PREFLIGHT -> error("Preflight has no predecessor")
        }
    }
}

/** Read-only model source; both independent verification and actual import close their own stream. */
internal class ReceiptRealSource(private val env: ReceiptRealEnvironment, private val counts: ReceiptRealCounts,
    private val deadline: ReceiptRealDeadline) {
    private val model = File(env.sourceDirectory(modelExpected = true), "model.litertlm")
    private val pin = ReceiptRealEnvironment.regular(model, ReceiptRealEnvironment.MODEL_BYTES)
    private fun open(verification: Boolean): InputStream {
        ReceiptRealEnvironment.offMain()
        deadline.remaining()
        check(counts.claim(verification))
        env.sourceDirectory(modelExpected = true)
        val before = ReceiptRealEnvironment.regular(model, ReceiptRealEnvironment.MODEL_BYTES)
        check(before.fileKey() == pin.fileKey() && before.lastModifiedTime() == pin.lastModifiedTime())
        val raw = Files.newInputStream(model.toPath(), READ, NOFOLLOW_LINKS)
        val opened = if (verification) counts.verifyOpened else counts.importOpened
        val closed = if (verification) counts.verifyClosed else counts.importClosed
        val bytes = if (verification) counts.verifyBytes else counts.importBytes
        check(opened.incrementAndGet() == 1L)
        if (!verification) counts.importActive.incrementAndGet()
        return object : InputStream() {
            private val importCloseObserved = AtomicBoolean()
            private fun observe(n: Int): Int {
                if (n > 0) check(bytes.addAndGet(n.toLong()) <= ReceiptRealEnvironment.MODEL_BYTES)
                return n
            }
            private fun io() {
                if (Looper.myLooper() == Looper.getMainLooper()) counts.offMain.set(false)
                ReceiptRealEnvironment.offMain(); deadline.remaining()
            }
            override fun read(buffer: ByteArray, offset: Int, length: Int): Int {
                io()
                if (!verification) counts.observeImportRead()
                return observe(raw.read(buffer, offset, length))
            }
            override fun read(): Int {
                io()
                if (!verification) counts.observeImportRead()
                val result = raw.read()
                if (result >= 0) observe(1)
                return result
            }
            override fun close() {
                ReceiptRealEnvironment.offMain()
                raw.close()
                if (!verification && importCloseObserved.compareAndSet(false, true)) counts.importActive.decrementAndGet()
                check(closed.incrementAndGet() == 1L)
                val after = ReceiptRealEnvironment.regular(model, ReceiptRealEnvironment.MODEL_BYTES)
                check(after.fileKey() == pin.fileKey() && after.lastModifiedTime() == pin.lastModifiedTime())
            }
        }
    }
    fun verify(): Boolean {
        val end = SystemClock.elapsedRealtime() + deadline.remaining(60_000)
        val digest = MessageDigest.getInstance("SHA-256")
        open(verification = true).use { input ->
            val buffer = ByteArray(64 * 1024)
            while (true) {
                check(SystemClock.elapsedRealtime() <= end)
                val n = input.read(buffer)
                check(SystemClock.elapsedRealtime() <= end)
                if (n < 0) break
                check(n > 0); digest.update(buffer, 0, n)
            }
        }
        check(SystemClock.elapsedRealtime() <= end)
        return counts.verifyBytes.get() == ReceiptRealEnvironment.MODEL_BYTES && digest.digest().joinToString("") { "%02x".format(it) } == ReceiptRealEnvironment.MODEL_SHA
    }
    fun openImport(): InputStream = open(verification = false)
}

abstract class ReceiptRealHarness {
    internal val context get() = InstrumentationRegistry.getInstrumentation().targetContext
    internal fun select(type: Class<*>, phase: ReceiptRealPhase): ReceiptRealDeadline {
        assumeTrue("Dedicated real receipt class selection is required",
            InstrumentationRegistry.getArguments().getString("class") == type.name)
        return ReceiptRealDeadline(phase)
    }
    internal fun <T> io(deadline: ReceiptRealDeadline, cap: Long = deadline.phase.budgetMs, block: suspend () -> T): T = runBlocking {
        withTimeout(deadline.remaining(cap)) { withContext(Dispatchers.IO) { ReceiptRealEnvironment.offMain(); block() } }
    }
    internal fun checked(checks: MutableMap<String, Boolean>, key: String, value: Boolean) {
        assertTrue(key, value); assertNull("Duplicate real receipt check", checks.put(key, value))
    }
    internal fun link(prior: Pair<JSONObject, String>, name: String) = JSONObject().put("prior_pid", prior.first.getInt("pid"))
        .put("prior_start", prior.first.getLong("start")).put("prior_${name}_sha256", prior.second)
    internal suspend fun data(actual: NativeWorkspaceTransport, command: JSONObject): JSONObject {
        val reply = actual.exchange(command)
        assertEquals("ok", reply.getString("status"))
        return reply.getJSONObject("data")
    }
    internal suspend fun snapshot(actual: NativeWorkspaceTransport, saved: SavedSnapshot): JSONObject {
        val chosen = requireNotNull(saved.selected)
        val scope = JSONObject().put("story", chosen.story).put("branch", chosen.branch)
        val session = data(actual, JSONObject().put("op", "resume").put("scope", scope))
        return data(actual, JSONObject().put("op", "play_snapshot").put("session", session.getString("session"))
            .put("scope", scope).put("expected_revision", saved.revision))
    }
    internal fun gift(view: JSONObject): JSONObject {
        check(view.getLong("revision") == 1L && !view.getJSONObject("inventory").has("potion"))
        val receipts = view.getJSONArray("receipts")
        check(receipts.length() == 1)
        val receipt = receipts.getJSONObject(0)
        val events = receipt.getJSONArray("events")
        check(events.length() == 1)
        val outcome = events.getJSONObject(0).getJSONObject("outcome")
        check(outcome.getString("effect") == "given" && outcome.getString("item") == "potion" &&
            outcome.getString("from") == "player" && outcome.getString("to") == "mira" && outcome.getInt("quantity") == 1)
        return receipt
    }
    internal fun nativeClosed(handle: Long, deadline: ReceiptRealDeadline): Boolean {
        val end = SystemClock.elapsedRealtime() + deadline.remaining(5_000)
        do {
            check(SystemClock.elapsedRealtime() < end)
            val bytes = NativeWorkspace.call(handle, localUtf8("""{"version":1,"command":{"op":"workspace"}}"""))
            val reply = JSONObject(localText(bytes, 262_144))
            check(SystemClock.elapsedRealtime() <= end)
            if (reply.optString("error") == "InvalidHandle") return true
            val left = minOf(end - SystemClock.elapsedRealtime(), deadline.remaining())
            if (left > 0) Thread.sleep(minOf(10, left))
        } while (SystemClock.elapsedRealtime() < end)
        return false
    }
}

abstract class ReceiptRealUiHarness : ReceiptRealHarness() {
    @get:Rule val compose = createEmptyComposeRule()
    private var scenario: ActivityScenario<LocalModelSetupActivity>? = null
    internal lateinit var model: LocalModelSetupViewModel
    private var activeCounts: ReceiptRealCounts? = null
    private var activeDeadline: ReceiptRealDeadline? = null
    internal fun launch(deadline: ReceiptRealDeadline, counts: ReceiptRealCounts) {
        activeCounts = counts; activeDeadline = deadline
        scenario = ActivityScenario.launch(LocalModelSetupActivity::class.java)
        requireNotNull(scenario).onActivity { model = it.setupController }
    }
    internal fun await(deadline: ReceiptRealDeadline, phase: LocalModelSetupPhase, cap: Long) {
        if (deadline.phase == ReceiptRealPhase.IMPORT && phase == LocalModelSetupPhase.READY) {
            ReceiptSetupFailureReporter.run(
                claim = { ReceiptSetupFixture.claimFailureEmission() },
                snapshot = {
                    // ACCEPT labels the intended import flow, not an accepted receipt.
                    // No production lifecycle event or typed cause was observed here:
                    // empty events/error NONE remain truthful even when actual is FAILED.
                    ReceiptSetupFailureTrace(ReceiptSetupFailureCase.ACCEPT).snapshot(phase,
                        model.state.value.phase, requireNotNull(activeCounts).importFailureProgress())
                },
                send = { code, key, json ->
                    InstrumentationRegistry.getInstrumentation().sendStatus(code,
                        Bundle().apply { putString(key, json) })
                },
                block = { compose.waitUntil(deadline.remaining(cap)) { model.state.value.phase == phase } },
            )
        } else {
            compose.waitUntil(deadline.remaining(cap)) { model.state.value.phase == phase }
        }
    }
    internal fun choose(source: ReceiptRealSource) = InstrumentationRegistry.getInstrumentation().runOnMainSync {
        check(model.beginPicker()); model.completePicker(source::openImport)
    }
    @After fun closeOnlyOwnedSetup() {
        scenario?.close(); scenario = null
        val counts = activeCounts ?: return
        val deadline = activeDeadline ?: return
        while (counts.importClosed.get() < counts.importOpened.get() && deadline.elapsed() < deadline.phase.budgetMs) Thread.sleep(10)
        assertEquals("Real source close must return; otherwise ownership remains unqualified", counts.importOpened.get(), counts.importClosed.get())
    }
}

@RunWith(AndroidJUnit4::class)
@SdkSuppress(minSdkVersion = 30)
class ReceiptRealSourcePreflightTest : ReceiptRealHarness() {
    @Test fun verifiesTrustedSourceBeforeModelCopy() {
        val deadline = select(ReceiptRealSourcePreflightTest::class.java, ReceiptRealPhase.SOURCE_PREFLIGHT)
        val checks = linkedMapOf<String, Boolean>()
        io(deadline) {
            val env = ReceiptRealEnvironment.open(context)
            checked(checks, "build_identity_exact", CandidateLocalModel.identity.bytes == ReceiptRealEnvironment.MODEL_BYTES && CandidateLocalModel.identity.sha256 == ReceiptRealEnvironment.MODEL_SHA)
            val source = env.sourceDirectory(modelExpected = false)
            checked(checks, "source_context_confined", source.parentFile == env.internal && source.canonicalFile == source)
            checked(checks, "source_owner_exact", true)
            checked(checks, "probe_exact", true)
            checked(checks, "source_whitelist_exact", true)
            checked(checks, "staged_model_absent", !Files.exists(File(source, "model.litertlm").toPath(), NOFOLLOW_LINKS))
            val access = CandidateLocalModel.store(context)
            checked(checks, "candidate_access_receipt", access is ReceiptCandidateModelAccess)
            checked(checks, "candidate_roots_absent", env.candidateAbsent())
            checked(checks, "candidate_installed_null_noncreating", access.installed() == null && env.candidateAbsent())
            checked(checks, "memory_eligible", env.memoryEligible())
            checked(checks, "userdata_copy_capacity", env.internal.usableSpace - ReceiptRealEnvironment.USERDATA_FLOOR >= ReceiptRealEnvironment.MODEL_BYTES)
            env.admit(ReceiptRealEnvironment.MODEL_BYTES)
            checked(checks, "external_import_capacity", true)
            env.proof(ReceiptRealPhase.SOURCE_PREFLIGHT, deadline, ReceiptRealCounts(), checks)
        }
    }
}

@RunWith(AndroidJUnit4::class)
@SdkSuppress(minSdkVersion = 30)
class ReceiptRealImportTest : ReceiptRealUiHarness() {
    @Test fun importsFixedRealCandidateThroughProductionSetup() {
        val deadline = select(ReceiptRealImportTest::class.java, ReceiptRealPhase.IMPORT)
        val checks = linkedMapOf<String, Boolean>()
        val counts = ReceiptRealCounts()
        val env = io(deadline) { ReceiptRealEnvironment.open(context) }
        val prior = io(deadline) { env.prior(ReceiptRealPhase.SOURCE_PREFLIGHT) }
        val source = io(deadline) {
            val directory = env.sourceDirectory(modelExpected = true)
            checked(checks, "source_context_confined", directory.parentFile == env.internal && directory.canonicalFile == directory)
            checked(checks, "source_owner_probe_exact", true)
            checked(checks, "source_whitelist_exact", true)
            checked(checks, "source_model_regular_uid", ReceiptRealEnvironment.regular(File(directory, "model.litertlm"), ReceiptRealEnvironment.MODEL_BYTES).isRegularFile)
            checked(checks, "memory_eligible", env.memoryEligible())
            env.admit(ReceiptRealEnvironment.MODEL_BYTES)
            checked(checks, "capacity_eligible", true)
            ReceiptRealSource(env, counts, deadline).also { checked(checks, "source_fullhash_exact", it.verify()) }
        }
        checked(checks, "source_verify_closed_once", counts.verifyOpened.get() == 1L && counts.verifyClosed.get() == 1L)
        io(deadline) {
            val access = CandidateLocalModel.store(context)
            checked(checks, "candidate_access_receipt", access is ReceiptCandidateModelAccess)
            check(env.candidateAbsent() && access.installed() == null)
            val refused = try { access.admitRuntime(); false } catch (failure: LocalModelException) { failure.failure == LocalModelFailure.INVALID_MODEL }
            checked(checks, "preaccept_runtime_refused", refused && CandidateLocalModel.canStart())
        }
        launch(deadline, counts)
        await(deadline, LocalModelSetupPhase.MISSING, 10_000)
        checked(checks, "setup_missing_before_import", model.state.value.phase == LocalModelSetupPhase.MISSING)
        choose(source)
        await(deadline, LocalModelSetupPhase.READY, 120_000)
        compose.onNodeWithTag("model-start").performScrollTo().assertIsEnabled()
        checked(checks, "setup_ready_after_import", model.state.value.ready)
        checked(checks, "import_source_off_main_closed_once", counts.offMain.get() && counts.importOpened.get() == 1L && counts.importClosed.get() == 1L)
        checked(checks, "import_source_exact_bytes", counts.importBytes.get() == ReceiptRealEnvironment.MODEL_BYTES)
        io(deadline) {
            val access = CandidateLocalModel.store(context)
            checked(checks, "accepted_full_recheck", access.installed() != null)
            access.admitRuntime()
            checked(checks, "accepted_receipt_owner_exact", true)
            env.proof(ReceiptRealPhase.IMPORT, deadline, counts, checks, link(prior, "preflight"))
        }
    }
}

@RunWith(AndroidJUnit4::class)
@SdkSuppress(minSdkVersion = 30)
class ReceiptRealPlayTest : ReceiptRealHarness() {
    @Test fun commitsOneGuardedRealSdkGift() {
        val deadline = select(ReceiptRealPlayTest::class.java, ReceiptRealPhase.PLAY)
        val checks = linkedMapOf<String, Boolean>()
        io(deadline) {
            val env = ReceiptRealEnvironment.open(context)
            val prior = env.prior(ReceiptRealPhase.IMPORT)
            checked(checks, "memory_eligible", env.memoryEligible())
            val access = CandidateLocalModel.store(context)
            checked(checks, "accepted_full_recheck", withTimeout(deadline.remaining(60_000)) { access.installed() != null })
            access.admitRuntime(); checked(checks, "runtime_guard_passed", true)
            ReceiptRealEnvironment.absent(File(env.internal, "workspace-v1"))
            val actual = withContext(Dispatchers.Main) { CandidateLocalModel.createTransport(context) }
            val observed = ReceiptRealObserved(actual)
            val gateway = DurableGateway(observed)
            var knownPrepared = false
            var committed = false
            try {
                val initial = gateway.initialize()
                checked(checks, "production_transport_local", initial.textProvider == TextProvider.LOCAL)
                checked(checks, "initial_revision_zero", initial.revision == 0L && snapshot(actual, initial).getJSONArray("receipts").length() == 0)
                val prepared = gateway.respondText(PlayInput(PlayInputKind.ACTION, "I give my last potion to Mira."), 0)
                // Production Prepared follows its existing public SDK terminal/drain/returned-close contract.
                // This is not an independent hidden-native teardown or reclamation counter.
                assertTrue("One actual SDK turn must prepare; rejection is not retried", prepared is DemoResult.Prepared)
                knownPrepared = true
                checked(checks, "prepared_after_known_worker_close", true)
                val postSdkFiles = withTimeout(deadline.remaining()) { requireNotNull(access.installed()) }
                checked(checks, "accepted_post_sdk_full_recheck", true)
                access.admitRuntime()
                checked(checks, "fixed_free_text_submitted_once", observed.freeText == 1 && observed.fixedIntent)
                checked(checks, "native_worker_off_main", observed.offMain && observed.calls > 0)
                assertTrue(gateway.commitAsync(prepared) is DemoResult.Accepted)
                committed = true
                val accepted = gateway.snapshot()
                val view = snapshot(actual, accepted)
                val receipt = gift(view)
                checked(checks, "canonical_revision_one", accepted.revision == 1L)
                checked(checks, "canonical_given_to_mira", true)
                checked(checks, "canonical_single_receipt", view.getJSONArray("receipts").length() == 1)
                val play = receipt.getJSONObject("play")
                val profile = play.getJSONObject("profile")
                val expected = JSONObject(localText(CandidateLocalModel.config(postSdkFiles).profileBytes(), 4096))
                checked(checks, "local_profile_exact", ReceiptRealEnvironment.canonical(profile) == ReceiptRealEnvironment.canonical(expected))
                val handle = actual.forkHandle()
                withContext(Dispatchers.Main) { gateway.close() }
                checked(checks, "candidate_owner_retained", !CandidateLocalModel.canStart())
                checked(checks, "native_handle_closed", nativeClosed(handle, deadline))
                val extra = link(prior, "import").put("revision", 1).put("receipt_count", 1)
                    .put("receipt_sha256", ReceiptRealEnvironment.sha(ReceiptRealEnvironment.canonical(receipt).toByteArray(Charsets.UTF_8)))
                    .put("repairs", play.getInt("repairs")).put("fallback", play.getBoolean("fallback"))
                env.proof(ReceiptRealPhase.PLAY, deadline, ReceiptRealCounts(), checks, extra)
            } catch (failure: Throwable) {
                if (knownPrepared && !committed && deadline.elapsed() < deadline.phase.budgetMs) {
                    try { withContext(NonCancellable) { withTimeout(deadline.remaining(5_000)) { gateway.cancelSaved() } } } catch (_: Throwable) { }
                }
                throw failure
            } finally {
                withContext(NonCancellable + Dispatchers.Main) { gateway.close() }
            }
        }
    }
}

/** Observes existing transport calls without supplying a reducer, provider or role response. */
internal class ReceiptRealObserved(private val actual: NativeWorkspaceTransport) : WorkspaceTransport {
    var calls = 0
    var freeText = 0
    var offMain = true
    var fixedIntent = false
    override suspend fun exchange(command: JSONObject): JSONObject {
        calls++
        offMain = offMain && Looper.myLooper() != Looper.getMainLooper()
        if (command.getString("op") == "free_text") {
            freeText++
            val intent = command.getJSONObject("request").getJSONObject("intent")
            fixedIntent = intent.getString("kind") == "free_text" && intent.getJSONObject("value").getString("kind") == "action" &&
                intent.getJSONObject("value").getString("text") == "I give my last potion to Mira."
        }
        return actual.exchange(command)
    }
    override fun close() = actual.close()
}

@RunWith(AndroidJUnit4::class)
@SdkSuppress(minSdkVersion = 30)
class ReceiptRealReopenTest : ReceiptRealUiHarness() {
    @Test fun reopensReceiptAndGiftAfterProcessRestart() {
        val deadline = select(ReceiptRealReopenTest::class.java, ReceiptRealPhase.REOPEN)
        val checks = linkedMapOf<String, Boolean>()
        val counts = ReceiptRealCounts()
        val env = io(deadline) { ReceiptRealEnvironment.open(context) }
        val prior = io(deadline) { env.prior(ReceiptRealPhase.PLAY) }
        checked(checks, "prior_play_proof_exact", true)
        checked(checks, "process_identity_changed", prior.first.getInt("pid") != Process.myPid() || prior.first.getLong("start") != Process.getStartElapsedRealtime())
        checked(checks, "memory_eligible", env.memoryEligible())
        // Deliberately no sourceDirectory/ReceiptRealSource resolution in this phase.
        launch(deadline, counts)
        await(deadline, LocalModelSetupPhase.READY, 90_000)
        compose.onNodeWithTag("model-start").performScrollTo().assertIsEnabled()
        checked(checks, "setup_ready_after_reopen", model.state.value.ready)
        io(deadline) {
            val access = CandidateLocalModel.store(context)
            checked(checks, "candidate_access_receipt", access is ReceiptCandidateModelAccess)
            checked(checks, "accepted_full_recheck", access.installed() != null)
            access.admitRuntime(); checked(checks, "runtime_guard_passed", true)
            val actual = withContext(Dispatchers.Main) { CandidateLocalModel.createTransport(context) }
            val observed = ReceiptRealObserved(actual)
            val gateway = DurableGateway(observed, autoCreateIfEmpty = false)
            try {
                val saved = gateway.initialize()
                checked(checks, "production_transport_local", saved.textProvider == TextProvider.LOCAL)
                val receipt = gift(snapshot(actual, saved))
                checked(checks, "canonical_revision_one", saved.revision == 1L)
                val hash = ReceiptRealEnvironment.sha(ReceiptRealEnvironment.canonical(receipt).toByteArray(Charsets.UTF_8))
                checked(checks, "canonical_gift_receipt_unchanged", hash == prior.first.getString("receipt_sha256"))
                checked(checks, "no_free_text_call", observed.freeText == 0)
                checked(checks, "source_unopened", counts.unopened())
                val handle = actual.forkHandle()
                withContext(Dispatchers.Main) { gateway.close() }
                checked(checks, "native_handle_closed", nativeClosed(handle, deadline))
                env.proof(ReceiptRealPhase.REOPEN, deadline, counts, checks,
                    link(prior, "play").put("revision", 1).put("receipt_count", 1).put("receipt_sha256", hash))
            } finally { withContext(NonCancellable + Dispatchers.Main) { gateway.close() } }
        }
    }
}

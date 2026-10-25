/* Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0 */
package org.locallore.app

import android.app.Application
import android.content.Context
import android.os.Build
import android.os.Bundle
import android.os.Looper
import android.os.Process
import java.io.ByteArrayInputStream
import java.io.File
import java.io.IOException
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
import java.util.concurrent.CountDownLatch
import java.util.concurrent.TimeUnit
import java.util.concurrent.atomic.AtomicBoolean
import java.util.concurrent.atomic.AtomicInteger
import kotlinx.coroutines.CancellationException
import org.json.JSONObject

/** Only explicit receipt verification packages these fixed, nonexported subclasses. */
abstract class ReceiptSetupFixtureActivity internal constructor(private val case: ReceiptSetupFixture.Case) : LocalModelSetupActivity() {
    internal val failureTrace = ReceiptSetupFailureTrace(when (case) {
        ReceiptSetupFixture.Case.ACCEPT -> ReceiptSetupFailureCase.ACCEPT
        ReceiptSetupFixture.Case.CANCEL_BEFORE -> ReceiptSetupFailureCase.CANCEL_BEFORE
        ReceiptSetupFixture.Case.CANCEL_AFTER -> ReceiptSetupFailureCase.CANCEL_AFTER
        ReceiptSetupFixture.Case.DRAIN -> ReceiptSetupFailureCase.DRAIN
    })

    override fun onCreate(savedInstanceState: Bundle?) {
        failureTrace.record(ReceiptSetupFailureEvent.CREATE)
        super.onCreate(savedInstanceState)
    }
    override fun onStart() {
        failureTrace.record(ReceiptSetupFailureEvent.START)
        super.onStart()
    }
    override fun onResume() {
        failureTrace.record(ReceiptSetupFailureEvent.RESUME)
        super.onResume()
    }
    override fun onPause() {
        failureTrace.record(ReceiptSetupFailureEvent.PAUSE)
        super.onPause()
    }
    override fun onStop() {
        failureTrace.record(ReceiptSetupFailureEvent.STOP)
        super.onStop()
    }
    override fun onDestroy() {
        failureTrace.record(ReceiptSetupFailureEvent.DESTROY)
        super.onDestroy()
    }

    internal override fun createSetupDependencies(): LocalModelSetupDependencies {
        val context = applicationContext
        val access by lazy { ReceiptSetupFixture.open(context).access(case) }
        // A retained ViewModel keeps these original-owner wrappers/trace. A recreated
        // Activity has its own lifecycle trace; no shared registry redirects old work.
        // The error code is the last observed category, not the current VM's cause.
        return LocalModelSetupDependencies(
            identity = ReceiptSetupFixture.identity,
            checkInstalled = {
                failureTrace.record(ReceiptSetupFailureEvent.CHECK_START)
                try {
                    val present = access.installed() != null
                    failureTrace.record(if (present) ReceiptSetupFailureEvent.CHECK_PRESENT else ReceiptSetupFailureEvent.CHECK_MISSING)
                    present
                } catch (failure: CancellationException) {
                    failureTrace.error(failure)
                    failureTrace.record(ReceiptSetupFailureEvent.CHECK_CANCELLED)
                    throw failure
                } catch (failure: Exception) {
                    failureTrace.error(failure)
                    failureTrace.record(ReceiptSetupFailureEvent.CHECK_FAILED)
                    throw failure
                }
            },
            install = { source ->
                failureTrace.record(ReceiptSetupFailureEvent.IMPORT_START)
                try {
                    access.import(source)
                    failureTrace.record(ReceiptSetupFailureEvent.IMPORT_RETURNED)
                } catch (failure: CancellationException) {
                    failureTrace.error(failure)
                    failureTrace.record(ReceiptSetupFailureEvent.IMPORT_CANCELLED)
                    throw failure
                } catch (failure: Exception) {
                    failureTrace.error(failure)
                    failureTrace.record(ReceiptSetupFailureEvent.IMPORT_FAILED)
                    throw failure
                }
            },
            canStart = CandidateLocalModel::canStart,
            openPlay = {
                ReceiptSetupFixture.playAttempts.incrementAndGet()
                throw IOException("Synthetic receipt setup cannot open inference")
            },
        )
    }
}

class ReceiptSetupAcceptActivity : ReceiptSetupFixtureActivity(ReceiptSetupFixture.Case.ACCEPT)
class ReceiptSetupCancelBeforeActivity : ReceiptSetupFixtureActivity(ReceiptSetupFixture.Case.CANCEL_BEFORE)
class ReceiptSetupCancelAfterActivity : ReceiptSetupFixtureActivity(ReceiptSetupFixture.Case.CANCEL_AFTER)
class ReceiptSetupDrainActivity : ReceiptSetupFixtureActivity(ReceiptSetupFixture.Case.DRAIN)

/** Trusted constants and current-case synchronization; no Intent selects an identity or path. */
internal object ReceiptSetupFixture {
    const val PACKAGE = "org.locallore.app.modelvolumeverify"
    const val HASH = "648c91a9de82e613189b3920a2098f5d803eb6e244f39b2b631cce24b7be8de0"
    val bytes = "LocalLore original model picker fixture v1. No model or story.\n".toByteArray(Charsets.US_ASCII)
    val identity = LocalModelIdentity("synthetic-receipt-setup-v1", 63, HASH)
    val playAttempts = AtomicInteger()
    private val failureEmissionAttempted = AtomicBoolean()
    /** One diagnostic attempt per process, never an application/resource admission. */
    fun claimFailureEmission(): Boolean = failureEmissionAttempted.compareAndSet(false, true)
    enum class Case(val suffix: String) {
        ACCEPT("accept"), CANCEL_BEFORE("cancel-before"), CANCEL_AFTER("cancel-after"), DRAIN("drain")
    }
    enum class Phase(val file: String, val checks: Set<String>) {
        SETUP("setup", setOf("candidate_access_receipt", "candidate_identity_fixed", "candidate_roots_context",
            "candidate_absent_noncreating", "source_opened_once", "source_closed_once", "accepted_records_exact",
            "ui_ready_after_import", "ui_recheck_ready", "activity_recreation_ready", "reopen_source_unopened", "sdk_not_opened")),
        CANCELLATION("cancellation", setOf("before_checkpoint_reached", "before_stopping_held", "before_busy_refused",
            "before_source_closed_once", "before_unaccepted_preserved", "before_not_ready_after_drain", "before_recheck_missing",
            "after_checkpoint_reached", "after_stopping_held", "after_busy_refused", "after_source_closed_once",
            "after_accepted_preserved", "after_not_ready_after_drain", "after_recheck_ready")),
        DRAIN("drain", setOf("read_blocked", "stopping_holds_source", "contender_busy", "original_scope_disposed",
            "fresh_scope_busy_failed", "source_closed_after_release", "actual_reservation_drained", "original_never_ready",
            "fresh_recheck_missing", "unaccepted_preserved", "source_opened_once")),
        REOPEN("reopen", setOf("previous_proof_valid", "process_identity_changed", "actual_adapter_receipt",
            "ui_ready_after_reopen", "accepted_records_exact", "source_unopened", "sdk_not_opened")),
    }

    class Gate {
        val reached = CountDownLatch(1)
        val release = CountDownLatch(1)
        val terminal = AtomicBoolean()
        fun hold() {
            reached.countDown()
            check(release.await(30, TimeUnit.SECONDS)) { "Receipt fixture gate expired" }
            terminal.set(true)
        }
    }
    private val gates = mutableMapOf<Case, Gate>()
    fun arm(case: Case): Gate = synchronized(gates) {
        check(case in setOf(Case.CANCEL_BEFORE, Case.CANCEL_AFTER))
        check(case !in gates)
        Gate().also { gates[case] = it }
    }
    private fun checkpoint(case: Case, point: ReceiptCheckpoint) {
        val expected = when (case) {
            Case.CANCEL_BEFORE -> ReceiptCheckpoint.BEFORE_COMMIT
            Case.CANCEL_AFTER -> ReceiptCheckpoint.AFTER_COMMIT
            else -> null
        }
        if (point == expected) requireNotNull(synchronized(gates) { gates[case] }).hold()
    }

    class Source(private val blocked: Boolean = false) {
        val opened = AtomicInteger()
        val closed = AtomicInteger()
        val active = AtomicInteger()
        private val readCalls = AtomicInteger()
        private val bytesRead = AtomicInteger()
        private val readsSaturated = AtomicBoolean()
        private val bytesSaturated = AtomicBoolean()
        val readEntered = CountDownLatch(1)
        val release = CountDownLatch(1)
        val readReleased = AtomicBoolean()
        private val releasedRead = AtomicBoolean()
        private fun addProgress(counter: AtomicInteger, saturated: AtomicBoolean, amount: Int) {
            while (true) {
                val current = counter.get()
                val exceeds = amount > ReceiptSetupFailureTrace.MAX_PROGRESS - current
                val next = if (exceeds) ReceiptSetupFailureTrace.MAX_PROGRESS else current + amount
                if (counter.compareAndSet(current, next)) {
                    if (exceeds) saturated.set(true)
                    return
                }
            }
        }
        /** Independent counters are observations, never a jointly atomic resource assertion. */
        fun progress(): ReceiptSetupSourceProgress {
            // Flags are monotonic and published after their counters reach the bound.
            val readsClipped = readsSaturated.get()
            val bytesClipped = bytesSaturated.get()
            return ReceiptSetupSourceProgress(opened = opened.get(), closed = closed.get(), active = active.get(),
                readCalls = readCalls.get(), bytesRead = bytesRead.get(),
                readsSaturated = readsClipped, bytesSaturated = bytesClipped)
        }
        fun open(): InputStream {
            check(opened.incrementAndGet() == 1)
            active.incrementAndGet()
            return object : ByteArrayInputStream(bytes) {
                private fun waitIfNeeded() {
                    if (blocked && releasedRead.compareAndSet(false, true)) {
                        readEntered.countDown()
                        check(release.await(30, TimeUnit.SECONDS)) { "Receipt fixture source expired" }
                        readReleased.set(true)
                    }
                }
                override fun read(buffer: ByteArray, offset: Int, length: Int): Int {
                    addProgress(readCalls, readsSaturated, 1)
                    waitIfNeeded()
                    val result = super.read(buffer, offset, length)
                    if (result > 0) addProgress(bytesRead, bytesSaturated, result)
                    return result
                }
                override fun read(): Int {
                    addProgress(readCalls, readsSaturated, 1)
                    waitIfNeeded()
                    val result = super.read()
                    if (result >= 0) addProgress(bytesRead, bytesSaturated, 1)
                    return result
                }
                override fun close() {
                    check(closed.incrementAndGet() == 1)
                    check(active.decrementAndGet() == 0)
                    super.close()
                }
            }
        }
    }

    data class Pair(val control: File, val data: File)
    fun open(context: Context): Environment {
        if (Build.VERSION.SDK_INT < 30) error("Receipt setup fixture unavailable")
        check(BuildConfig.MODEL_RECEIPT_VERIFICATION && BuildConfig.MODEL_VOLUME_VERIFICATION)
        check(Looper.myLooper() != Looper.getMainLooper())
        val app = context.applicationContext
        check(app.packageName == PACKAGE && app.applicationInfo.uid == Process.myUid())
        check(Application.getProcessName() == PACKAGE)
        val internal = app.noBackupFilesDir.canonicalFile.also(::strictDirectory)
        val volume = AndroidModelVolume.select(app)
        volume.admit()
        val external = requireNotNull(volume.root.parentFile).also(::strictDirectory)
        return Environment(internal, external, volume).also { it.admit() }
    }

    class Environment internal constructor(val internal: File, val external: File, private val volume: AndroidModelVolume) {
        private val externalBefore = external.usableSpace
        private val userdataBefore = internal.usableSpace
        val proofRoot = File(internal, "receipt-setup-proof-v1")
        fun pair(case: Case): Pair = Pair(File(internal, "receipt-setup-${case.suffix}-v1"),
            File(external, "receipt-setup-${case.suffix}-v1"))
        fun fresh(vararg cases: Case) {
            admit()
            cases.forEach { absent(pair(it).control); absent(pair(it).data) }
        }
        fun admit() {
            volume.admit()
            absent(volume.root)
            absent(File(internal, "local-model-v1"))
            absent(File(internal, "local-model-receipt-control-v1"))
            absent(File(external, "local-model-receipt-data-v1"))
            check(playAttempts.get() == 0)
        }
        fun access(case: Case): CandidateModelAccess {
            admit()
            val pair = pair(case)
            return ReceiptCandidateModelAccess(ReceiptModelTransaction(pair.control, pair.data, identity,
                availableBytes = { external.usableSpace }, storageAdmission = { missing -> volume.admit(missing); admit() },
                checkpoint = { checkpoint(case, it) }))
        }
        fun assertRecords(case: Case, accepted: Boolean, complete: Boolean = true) {
            admit()
            val pair = pair(case)
            strictDirectory(pair.control); strictDirectory(pair.data)
            // Never open another same-process descriptor to the locked inode.
            val lock = Files.readAttributes(File(pair.control, "model-import.lock").toPath(), BasicFileAttributes::class.java, NOFOLLOW_LINKS)
            check(lock.isRegularFile && !lock.isSymbolicLink && lock.size() == 0L)
            val controlNames = setOf("model-import.lock", "model.receipt") + if (accepted) setOf("model.accepted") else emptySet()
            val dataNames = setOf("model.owner", "model.litertlm") + if (complete) setOf("cache") else emptySet()
            Files.newDirectoryStream(pair.control.toPath()).use { entries -> check(entries.map { it.fileName.toString() }.toSet() == controlNames) }
            Files.newDirectoryStream(pair.data.toPath()).use { entries -> check(entries.map { it.fileName.toString() }.toSet() == dataNames) }
            if (complete) strictDirectory(File(pair.data, "cache"))
            val receipt = ("locallore-model-receipt-v1\n${identity.id}\n63\n$HASH\n" +
                "${sha(pair.data.canonicalPath.toByteArray(Charsets.UTF_8))}\n").toByteArray(Charsets.UTF_8)
            val owner = ("locallore-model-owner-v1\n${sha(pair.control.canonicalPath.toByteArray(Charsets.UTF_8))}\n" +
                "${sha(receipt)}\n").toByteArray(Charsets.UTF_8)
            check(read(File(pair.control, "model.receipt"), 512).contentEquals(receipt))
            check(read(File(pair.data, "model.owner"), 512).contentEquals(owner))
            val actual = read(File(pair.data, "model.litertlm"), 63)
            if (complete) check(actual.contentEquals(bytes)) else check(actual.size <= 63)
            val marker = File(pair.control, "model.accepted")
            if (accepted) {
                check(read(marker, 0).isEmpty())
                strictDirectory(File(pair.data, "cache"))
            } else absent(marker)
        }
        fun snapshot(case: Case): Map<String, String> {
            admit()
            val pair = pair(case)
            return listOf(File(pair.control, "model.receipt"), File(pair.control, "model.accepted"),
                File(pair.data, "model.owner"), File(pair.data, "model.litertlm")).associate {
                it.name to if (Files.exists(it.toPath(), NOFOLLOW_LINKS)) sha(read(it, 512)) else "absent"
            }
        }
        fun proof(phase: Phase, checks: Map<String, Boolean>, opened: Int, closed: Int, prior: JSONObject? = null) {
            if (Build.VERSION.SDK_INT < 30) error("Receipt setup fixture unavailable")
            admit()
            check(checks.keys == phase.checks && checks.values.all { it })
            val expected = when (phase) { Phase.SETUP, Phase.DRAIN -> 1; Phase.CANCELLATION -> 2; Phase.REOPEN -> 0 }
            check(opened == expected && closed == expected)
            check((phase == Phase.REOPEN) == (prior != null))
            if (!Files.exists(proofRoot.toPath(), NOFOLLOW_LINKS)) Files.createDirectory(proofRoot.toPath())
            strictDirectory(proofRoot)
            val allowed = Phase.entries.flatMap { listOf("${it.file}-v1.json", "${it.file}-ready-v1.txt") }.toSet()
            Files.newDirectoryStream(proofRoot.toPath()).use { entries -> entries.forEach { check(it.fileName.toString() in allowed) } }
            val flags = JSONObject()
            checks.toSortedMap().forEach { (key, value) -> flags.put(key, value) }
            val value = JSONObject().put("version", 1).put("phase", phase.name)
                .put("pid", Process.myPid()).put("start", Process.getStartElapsedRealtime())
                .put("uid", Process.myUid()).put("process", Application.getProcessName())
                .put("fixture_bytes", 63).put("fixture_sha256", HASH).put("direct_callback", true)
                .put("candidate_roots_absent", true).put("publication_native_invoked", false).put("sdk_invoked", false)
                .put("external_free_before", externalBefore).put("external_free_after", external.usableSpace)
                .put("userdata_free_before", userdataBefore).put("userdata_free_after", internal.usableSpace)
                .put("source_opened", opened).put("source_closed", closed).put("checks", flags)
            prior?.let { value.put("prior_pid", it.getInt("pid")).put("prior_start", it.getLong("start")) }
            val raw = value.toString().toByteArray(Charsets.US_ASCII)
            check(raw.size <= 4096)
            forcedNew(File(proofRoot, "${phase.file}-v1.json"), raw)
            forcedNew(File(proofRoot, "${phase.file}-ready-v1.txt"), byteArrayOf())
        }
        fun previousSetupProof(): JSONObject {
            admit()
            strictDirectory(proofRoot)
            val raw = read(File(proofRoot, "setup-v1.json"), 4096)
            check(read(File(proofRoot, "setup-ready-v1.txt"), 0).isEmpty())
            val value = JSONObject(String(raw, Charsets.US_ASCII))
            val keys = setOf("version", "phase", "pid", "start", "uid", "process", "fixture_bytes", "fixture_sha256",
                "direct_callback", "candidate_roots_absent", "publication_native_invoked", "sdk_invoked",
                "external_free_before", "external_free_after", "userdata_free_before", "userdata_free_after",
                "source_opened", "source_closed", "checks")
            fun number(key: String): Long {
                val field = value.get(key)
                check(field is Int || field is Long)
                return (field as Number).toLong()
            }
            check(value.keys().asSequence().toSet() == keys && number("version") == 1L && value.get("phase") == "SETUP")
            check(number("uid") == Process.myUid().toLong() && value.get("process") == PACKAGE)
            check(number("pid") > 0 && number("pid") < Int.MAX_VALUE.toLong() && number("start") > 0)
            check(number("fixture_bytes") == 63L && value.get("fixture_sha256") == HASH)
            check(value.get("direct_callback") == true && value.get("candidate_roots_absent") == true)
            check(value.get("publication_native_invoked") == false && value.get("sdk_invoked") == false)
            check(number("source_opened") == 1L && number("source_closed") == 1L)
            for (name in listOf("external_free_before", "external_free_after", "userdata_free_before", "userdata_free_after")) check(number(name) >= 0)
            val checks = value.getJSONObject("checks")
            check(checks.keys().asSequence().toSet() == Phase.SETUP.checks)
            Phase.SETUP.checks.forEach { check(checks.get(it) == true) }
            return value
        }
    }

    private fun strictDirectory(file: File) {
        check(file.isAbsolute && file.canonicalFile == file && file.toPath().normalize() == file.toPath())
        var path: Path? = file.toPath()
        while (path != null) {
            check(Files.isDirectory(path, NOFOLLOW_LINKS) && !Files.isSymbolicLink(path))
            path = path.parent
        }
    }
    private fun absent(file: File) = check(!Files.exists(file.toPath(), NOFOLLOW_LINKS))
    private fun forcedNew(file: File, bytes: ByteArray) {
        FileChannel.open(file.toPath(), CREATE_NEW, WRITE, NOFOLLOW_LINKS).use { channel ->
            val buffer = ByteBuffer.wrap(bytes)
            while (buffer.hasRemaining()) check(channel.write(buffer) > 0)
            channel.force(true)
        }
    }
    private fun read(file: File, cap: Int): ByteArray {
        val before = Files.readAttributes(file.toPath(), BasicFileAttributes::class.java, NOFOLLOW_LINKS)
        check(before.isRegularFile && !before.isSymbolicLink && before.size() <= cap)
        val buffer = ByteArray(cap + 1)
        var count = 0
        Files.newInputStream(file.toPath(), READ, NOFOLLOW_LINKS).use { input ->
            while (count < buffer.size) {
                val result = input.read(buffer, count, buffer.size - count)
                if (result < 0) break
                check(result > 0); count += result
            }
        }
        val after = Files.readAttributes(file.toPath(), BasicFileAttributes::class.java, NOFOLLOW_LINKS)
        check(after.isRegularFile && !after.isSymbolicLink && before.fileKey() == after.fileKey() &&
            before.size() == after.size() && count.toLong() == before.size() && count <= cap &&
            before.lastModifiedTime() == after.lastModifiedTime())
        return buffer.copyOf(count)
    }
    private fun sha(bytes: ByteArray) = MessageDigest.getInstance("SHA-256").digest(bytes).joinToString("") { "%02x".format(it) }
}

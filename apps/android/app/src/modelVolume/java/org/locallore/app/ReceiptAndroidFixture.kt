/* Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0 */
package org.locallore.app

import android.app.Application
import android.content.Context
import android.os.Build
import android.os.Looper
import android.os.Process
import java.io.ByteArrayInputStream
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
import java.util.concurrent.atomic.AtomicInteger
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.withContext
import org.json.JSONObject

/** Only the existing volume verification build includes this fixed synthetic fixture. */
internal object ReceiptAndroidFixture {
    const val PACKAGE = "org.locallore.app.modelvolumeverify"
    const val CHILD_PROCESS = "$PACKAGE:receiptproof"
    const val HASH = "648c91a9de82e613189b3920a2098f5d803eb6e244f39b2b631cce24b7be8de0"
    val bytes = "LocalLore original model picker fixture v1. No model or story.\n".toByteArray(Charsets.US_ASCII)
    private val identity = LocalModelIdentity("synthetic-receipt-android-v1", 63, HASH)

    enum class Case(val suffix: String) {
        ACCEPT("accept"), CANCEL_BEFORE("cancel-before"), CANCEL_AFTER("cancel-after"),
        PARTIAL("partial"), FOREIGN("foreign"), GUARD("guard"), PROCESS("process"),
        FOREIGN_CONTROL("foreign-control"),
    }

    enum class Phase(val file: String, val checks: Set<String>) {
        ACCEPT("accept", setOf("source_opened_once", "source_closed_once", "receipt_owner_exact",
            "accepted_marker_empty", "full_model_verified", "reopen_without_source",
            "accepted_discard_refused", "accepted_bytes_preserved")),
        CANCELLATION("cancellation", setOf("before_checkpoint_reached", "before_cancelled",
            "before_source_closed_once", "before_unaccepted_preserved", "before_installed_null",
            "after_checkpoint_reached", "after_cancelled", "after_source_closed_once",
            "after_accepted_verified", "after_reopen_without_source")),
        REFUSAL("refusal", setOf("partial_source_closed_once", "partial_installed_null",
            "partial_bytes_preserved", "unknown_discard_refused", "unknown_bytes_preserved",
            "explicit_partial_discarded", "discard_retry_accepted", "foreign_owner_refused",
            "foreign_source_unopened", "foreign_discard_preserved", "guard_revocation_refused",
            "guard_source_unopened", "guard_preserved", "guard_is_synthetic")),
        PROCESS("process", setOf("child_identity_verified", "pending_receipt_owner_exact",
            "pending_model_fullhash", "pending_unaccepted", "os_busy_all_operations",
            "child_halt_armed", "bound_connection_released", "child_death_observed",
            "lock_reacquired", "resumed_without_source", "accepted_fullhash")),
    }

    data class Pair(val control: File, val data: File)
    data class Child(val pid: Int, val start: Long, val uid: Int)

    fun requireIdentity(context: Context, child: Boolean) {
        if (Build.VERSION.SDK_INT < 30) error("Receipt fixture unavailable")
        check(BuildConfig.MODEL_VOLUME_VERIFICATION) { "Receipt build refused" }
        check(context.packageName == PACKAGE) { "Receipt package refused" }
        check(context.applicationInfo.uid == Process.myUid()) { "Receipt target UID refused" }
        check(Application.getProcessName() == if (child) CHILD_PROCESS else context.applicationInfo.processName) {
            "Receipt process refused"
        }
    }

    suspend fun open(context: Context, child: Boolean = false): Environment = withContext(Dispatchers.IO) {
        requireIdentity(context, child)
        check(Looper.getMainLooper().thread !== Thread.currentThread())
        val internal = context.noBackupFilesDir.canonicalFile
        strictDirectory(internal)
        val volume = AndroidModelVolume.select(context)
        volume.admit()
        absent(volume.root)
        val external = requireNotNull(volume.root.parentFile)
        strictDirectory(external)
        Environment(internal, external, volume)
    }

    class Environment internal constructor(
        private val internal: File,
        private val external: File,
        private val volume: AndroidModelVolume,
    ) {
        private val externalBefore = external.usableSpace
        private val userdataBefore = internal.usableSpace
        private val proofRoot = File(internal, "receipt-android-proof-v2")

        fun pair(case: Case): Pair = Pair(File(internal, "receipt-android-${case.suffix}-v2"),
            File(external, "receipt-android-${if (case == Case.FOREIGN_CONTROL) Case.FOREIGN.suffix else case.suffix}-v2"))

        fun fresh(vararg cases: Case) {
            admit()
            for (case in cases) {
                absent(pair(case).control)
                if (case != Case.FOREIGN_CONTROL) absent(pair(case).data)
            }
        }

        fun transaction(case: Case, revoked: () -> Boolean = { false },
            checkpoint: (ReceiptCheckpoint) -> Unit = {}): ReceiptModelTransaction {
            val pair = pair(case)
            return ReceiptModelTransaction(pair.control, pair.data, identity,
                availableBytes = { external.usableSpace },
                storageAdmission = { missing ->
                    volume.admit(missing)
                    // Deliberately injected policy revocation; this is not media ejection.
                    if (revoked()) throw LocalModelException(LocalModelFailure.STORAGE)
                }, checkpoint = checkpoint)
        }

        fun admit() { volume.admit(); absent(volume.root) }

        fun receiptBytes(pair: Pair): ByteArray =
            ("locallore-model-receipt-v1\n${identity.id}\n63\n$HASH\n" +
                "${sha(pair.data.canonicalPath.toByteArray(Charsets.UTF_8))}\n").toByteArray(Charsets.UTF_8)

        private fun ownerBytes(pair: Pair): ByteArray =
            ("locallore-model-owner-v1\n${sha(pair.control.canonicalPath.toByteArray(Charsets.UTF_8))}\n" +
                "${sha(receiptBytes(pair))}\n").toByteArray(Charsets.UTF_8)

        fun assertRecords(case: Case, accepted: Boolean, modelBytes: ByteArray = bytes) {
            admit()
            val pair = pair(case)
            strictDirectory(pair.control); strictDirectory(pair.data)
            check(read(File(pair.control, "model.receipt"), 512).contentEquals(receiptBytes(pair)))
            check(read(File(pair.data, "model.owner"), 512).contentEquals(ownerBytes(pair)))
            check(read(File(pair.data, "model.litertlm"), 63).contentEquals(modelBytes))
            val marker = File(pair.control, "model.accepted")
            if (accepted) {
                check(read(marker, 0).isEmpty())
                val cache = File(pair.data, "cache")
                strictDirectory(cache)
                Files.newDirectoryStream(cache.toPath()).use { check(!it.iterator().hasNext()) }
            } else absent(marker)
        }

        fun assertDiscarded(case: Case) {
            admit()
            val pair = pair(case)
            absent(pair.data); absent(File(pair.control, "model.receipt"))
            absent(File(pair.control, "model.accepted"))
            check(read(File(pair.control, "model-import.lock"), 0).isEmpty())
        }

        fun assertReceiptOnly(case: Case) {
            admit()
            val pair = pair(case)
            strictDirectory(pair.control)
            check(read(File(pair.control, "model.receipt"), 512).contentEquals(receiptBytes(pair)))
            check(read(File(pair.control, "model-import.lock"), 0).isEmpty())
            absent(File(pair.control, "model.accepted")); absent(pair.data)
        }

        fun snapshot(case: Case): Map<String, String> {
            admit()
            val pair = pair(case)
            return listOf("lock" to File(pair.control, "model-import.lock"),
                "receipt" to File(pair.control, "model.receipt"),
                "marker" to File(pair.control, "model.accepted"),
                "owner" to File(pair.data, "model.owner"),
                "model" to File(pair.data, "model.litertlm"),
                "unknown" to File(pair.data, "unknown-fixture-v1.bin"))
                .associate { (key, file) -> key to if (Files.exists(file.toPath(), NOFOLLOW_LINKS)) sha(read(file, 512)) else "absent" }
        }

        fun addUnknown(case: Case) {
            admit()
            forcedNew(File(pair(case).data, "unknown-fixture-v1.bin"), byteArrayOf(4, 8, 15))
        }

        fun proof(phase: Phase, checks: Map<String, Boolean>, child: Child? = null) {
            if (Build.VERSION.SDK_INT < 30) error("Receipt fixture unavailable")
            admit()
            check(checks.keys == phase.checks && checks.values.all { it })
            check((phase == Phase.PROCESS) == (child != null))
            val externalAfter = external.usableSpace
            val userdataAfter = internal.usableSpace
            if (!Files.exists(proofRoot.toPath(), NOFOLLOW_LINKS)) Files.createDirectory(proofRoot.toPath())
            strictDirectory(proofRoot)
            val allowed = Phase.entries.flatMap { listOf("${it.file}-v1.json", "${it.file}-ready-v1.txt") }.toSet()
            Files.newDirectoryStream(proofRoot.toPath()).use { stream ->
                for (entry in stream) check(entry.fileName.toString() in allowed)
            }
            val closedChecks = JSONObject()
            checks.toSortedMap().forEach { (key, value) -> closedChecks.put(key, value) }
            val proof = JSONObject().put("version", 1).put("phase", phase.name)
                .put("pid", Process.myPid()).put("start", Process.getStartElapsedRealtime())
                .put("uid", Process.myUid()).put("process", Application.getProcessName())
                .put("fixture_bytes", 63).put("fixture_sha256", HASH)
                .put("candidate_root_absent", true).put("publication_native_invoked", false)
                .put("sdk_invoked", false).put("external_free_before", externalBefore)
                .put("external_free_after", externalAfter).put("userdata_free_before", userdataBefore)
                .put("userdata_free_after", userdataAfter).put("checks", closedChecks)
            child?.let { proof.put("child_pid", it.pid).put("child_start", it.start).put("child_uid", it.uid) }
            val raw = proof.toString().toByteArray(Charsets.US_ASCII)
            check(raw.size <= 4096)
            forcedNew(File(proofRoot, "${phase.file}-v1.json"), raw)
            forcedNew(File(proofRoot, "${phase.file}-ready-v1.txt"), byteArrayOf())
        }
    }

    class Source(private val payload: ByteArray = bytes) {
        val opened = AtomicInteger()
        val closed = AtomicInteger()
        fun open(): ByteArrayInputStream {
            opened.incrementAndGet()
            return object : ByteArrayInputStream(payload) {
                override fun close() { closed.incrementAndGet(); super.close() }
            }
        }
    }

    private fun strictDirectory(file: File) {
        check(file.isAbsolute && file.canonicalFile == file && file.toPath().normalize() == file.toPath())
        var path: Path? = file.toPath()
        while (path != null) {
            check(!Files.isSymbolicLink(path) && Files.isDirectory(path, NOFOLLOW_LINKS))
            path = path.parent
        }
    }

    private fun absent(file: File) { check(!Files.exists(file.toPath(), NOFOLLOW_LINKS)) }
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
                val read = input.read(buffer, count, buffer.size - count)
                if (read < 0) break
                check(read > 0); count += read
            }
        }
        val after = Files.readAttributes(file.toPath(), BasicFileAttributes::class.java, NOFOLLOW_LINKS)
        check(after.isRegularFile && !after.isSymbolicLink && count.toLong() == before.size())
        check(before.fileKey() == after.fileKey() && before.size() == after.size() &&
            before.lastModifiedTime() == after.lastModifiedTime() && count <= cap)
        return buffer.copyOf(count)
    }

    private fun sha(bytes: ByteArray) = MessageDigest.getInstance("SHA-256")
        .digest(bytes).joinToString("") { "%02x".format(it) }
}

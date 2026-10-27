/* Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0 */
package org.locallore.app

import android.os.Looper
import android.os.Process
import android.os.SystemClock
import android.system.Os
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
import kotlinx.coroutines.runBlocking
import kotlinx.coroutines.withContext
import kotlinx.coroutines.withTimeout
import org.json.JSONArray
import org.json.JSONObject
import org.junit.Assume.assumeTrue

internal const val PHONE_GIFT = "I give my last potion to Mira."
internal const val PHONE_DIALOGUE = "Where is the tideglass relic?"
internal fun phoneIdentity() = PhysicalProcessIdentity(Process.myPid(), Process.getStartElapsedRealtime(), Process.myUid())
internal fun phoneSha(bytes: ByteArray) = MessageDigest.getInstance("SHA-256").digest(bytes).joinToString("") { "%02x".format(it) }
internal fun phoneHash(value: Any?) = phoneSha(phoneCanonical(value).toByteArray(Charsets.UTF_8))
internal fun phoneCanonical(value: Any?): String = when (value) {
    is JSONObject -> value.keys().asSequence().toList().sorted().joinToString(",", "{", "}") { JSONObject.quote(it) + ":" + phoneCanonical(value.get(it)) }
    is JSONArray -> (0 until value.length()).joinToString(",", "[", "]") { phoneCanonical(value.get(it)) }
    is String -> JSONObject.quote(value)
    is Boolean -> value.toString()
    is Number -> JSONObject.numberToString(value)
    null, JSONObject.NULL -> "null"
    else -> error("Unsupported phone proof value")
}

internal class PhoneDeadline(val phase: PhysicalModelPhase) {
    private val started = SystemClock.elapsedRealtime()
    fun elapsed() = SystemClock.elapsedRealtime() - started
    fun remaining(cap: Long = phase.budgetMs): Long = (phase.budgetMs - elapsed()).also { check(it > 0) }.coerceAtMost(cap)
}

/** The exact class selection guard is the first statement in EACH heavyweight method. */
abstract class PhysicalModelHarness {
    internal val context get() = InstrumentationRegistry.getInstrumentation().targetContext
    internal fun selected(type: Class<*>, phase: PhysicalModelPhase): PhoneDeadline {
        assumeTrue("Exact separately admitted phone class required", InstrumentationRegistry.getArguments().getString("class") == type.name)
        check(BuildConfig.DEBUG && BuildConfig.PHYSICAL_MODEL_VERIFICATION && context.packageName == PhysicalModelPolicy.PACKAGE)
        return PhoneDeadline(phase)
    }
    internal fun <T> io(deadline: PhoneDeadline, block: suspend () -> T): T = runBlocking {
        withTimeout(deadline.remaining()) { withContext(Dispatchers.IO) { check(Looper.myLooper() != Looper.getMainLooper()); block() } }
    }
    internal fun checked(checks: MutableMap<String, Boolean>, key: String, condition: Boolean) {
        check(condition) { "Physical phase check failed: $key" }
        check(checks.put(key, true) == null)
    }
    internal suspend fun data(actual: NativeWorkspaceTransport, command: JSONObject): JSONObject {
        val reply = actual.exchange(command)
        check(reply.getInt("version") == 1 && reply.getString("status") == "ok")
        return reply.getJSONObject("data")
    }
    internal suspend fun view(actual: NativeWorkspaceTransport, saved: SavedSnapshot): JSONObject {
        val selected = requireNotNull(saved.selected)
        val scope = JSONObject().put("story", selected.story).put("branch", selected.branch)
        val session = data(actual, JSONObject().put("op", "resume").put("scope", scope))
        return data(actual, JSONObject().put("op", "play_snapshot").put("session", session.getString("session"))
            .put("scope", scope).put("expected_revision", saved.revision))
    }
    internal fun nativeClosed(handle: Long, deadline: PhoneDeadline): Boolean {
        val end = SystemClock.elapsedRealtime() + deadline.remaining(5_000)
        do {
            check(SystemClock.elapsedRealtime() < end)
            val raw = NativeWorkspace.call(handle, localUtf8("""{"version":1,"command":{"op":"workspace"}}"""))
            val reply = JSONObject(localText(raw, 262_144))
            if (reply.optString("error") == "InvalidHandle") return true
            Thread.sleep(minOf(10, deadline.remaining()))
        } while (SystemClock.elapsedRealtime() < end)
        return false
    }
}

internal class PhoneCounts {
    private val verifyClaimed = AtomicBoolean()
    private val importClaimed = AtomicBoolean()
    val verifyOpened = AtomicLong(); val verifyClosed = AtomicLong(); val verifyBytes = AtomicLong()
    val importOpened = AtomicLong(); val importClosed = AtomicLong(); val importBytes = AtomicLong()
    val offMain = AtomicBoolean(true)
    fun claim(verify: Boolean) = (if (verify) verifyClaimed else importClaimed).compareAndSet(false, true)
    fun snapshot() = PhysicalSourceCounts(verifyOpened.get(), verifyClosed.get(), verifyBytes.get(), importOpened.get(), importClosed.get(), importBytes.get())
}

internal class PhoneEnvironment(context: android.content.Context) {
    val storage = AndroidPhysicalModelStorage.open(context)
    val before = storage.snapshot()
    val identity = phoneIdentity()
    fun resources(): PhysicalProofResources {
        val after = storage.snapshot()
        check(after.totalMemory == before.totalMemory)
        return PhysicalProofResources(before.availableBytes, after.availableBytes, before.totalMemory,
            before.availableMemory, after.availableMemory, before.lowMemory, after.lowMemory)
    }
    fun candidateAbsent() = !Files.exists(storage.control.toPath(), NOFOLLOW_LINKS) && !Files.exists(storage.data.toPath(), NOFOLLOW_LINKS)
    fun source(model: Boolean): File {
        storage.admit()
        phoneDirectory(storage.source)
        phoneEntries(storage.source, setOf("source.owner", "probe.txt") + if (model) setOf("model.litertlm") else emptySet())
        check(phoneRead(File(storage.source, "source.owner"), 29).contentEquals(OWNER))
        check(phoneRead(File(storage.source, "probe.txt"), 65).contentEquals(PROBE))
        check(phoneSha(PROBE) == PROBE_SHA)
        if (model) phoneRegular(File(storage.source, "model.litertlm"), PhysicalModelPolicy.MODEL_BYTES)
        else check(!Files.exists(File(storage.source, "model.litertlm").toPath(), NOFOLLOW_LINKS))
        return storage.source
    }
    fun prior(phase: PhysicalModelPhase): Pair<PhysicalModelProof, String> {
        check(phase != PhysicalModelPhase.PRECHECK)
        val previous = PhysicalModelPhase.entries[phase.ordinal - 1]
        storage.admit()
        phoneDirectory(storage.proof)
        phoneEntries(storage.proof, names(previous))
        var preceding: Pair<PhysicalModelProof, String>? = null
        for (step in PhysicalModelPhase.entries.take(phase.ordinal)) {
            val raw = phoneRead(File(storage.proof, "${step.file}-v1.json"), PhysicalModelProof.MAX_BYTES)
            check(phoneRead(File(storage.proof, "${step.file}-ready-v1.txt"), 0).isEmpty())
            val value = decode(raw, step)
            preceding?.let { prior ->
                check(value.prior == PhysicalPrior(prior.first.phase, prior.first.identity, prior.second))
                if (step.ordinal > PhysicalModelPhase.CANCEL.ordinal)
                    check(value.extras["story_sha256"] == prior.first.extras["story_sha256"])
                if (step.ordinal >= PhysicalModelPhase.DIALOGUE.ordinal)
                    check(value.extras["gift_receipt_sha256"] == prior.first.extras["gift_receipt_sha256"])
                if (step == PhysicalModelPhase.REOPEN) {
                    check(value.extras["dialogue_receipt_sha256"] == prior.first.extras["dialogue_receipt_sha256"])
                    check(value.extras["receipts_sha256"] == prior.first.extras["receipts_sha256"])
                }
            }
            if (step.canonicalState) {
                val trace = phoneRead(File(storage.proof, "${step.file}-worker-v2.json"), 4096)
                check(trace.isNotEmpty() && phoneSha(trace) == value.extras["worker_trace_sha256"])
            }
            if (step == PhysicalModelPhase.CANCEL)
                check(phoneSha(phoneRead(File(storage.proof, "cancel-sample-worker-v2.json"), 4096)) == value.extras["sample_trace_sha256"])
            if (step == PhysicalModelPhase.DIALOGUE)
                check(phoneSha(phoneRead(File(storage.proof, "guards-worker-v2.json"), 4096)) == value.extras["guards_trace_sha256"])
            preceding = value to phoneSha(raw)
        }
        return requireNotNull(preceding).also {
            check(it.first.identity.uid == identity.uid && (it.first.identity.pid != identity.pid || it.first.identity.start != identity.start))
        }
    }
    fun write(phase: PhysicalModelPhase, deadline: PhoneDeadline, counts: PhoneCounts, checks: Map<String, Boolean>,
        prior: Pair<PhysicalModelProof, String>? = null, extras: Map<String, Any> = emptyMap(), traces: Map<String, LiteRtWorkerSnapshot> = emptyMap()) {
        storage.admit(); deadline.remaining()
        val value = PhysicalModelProof(phase, identity, deadline.elapsed(), resources(), counts.snapshot(),
            prior?.let { PhysicalPrior(it.first.phase, it.first.identity, it.second) }, checks, extras)
        if (phase.ordinal > PhysicalModelPhase.CANCEL.ordinal) check(extras["story_sha256"] == prior?.first?.extras?.get("story_sha256"))
        if (phase.ordinal >= PhysicalModelPhase.DIALOGUE.ordinal) check(extras["gift_receipt_sha256"] == prior?.first?.extras?.get("gift_receipt_sha256"))
        if (phase == PhysicalModelPhase.REOPEN) {
            check(extras["receipts_sha256"] == prior?.first?.extras?.get("receipts_sha256"))
            check(extras["dialogue_receipt_sha256"] == prior?.first?.extras?.get("dialogue_receipt_sha256"))
        }
        val expectedTraces = if (phase.canonicalState) {
            setOf("${phase.file}-worker-v2.json") + when (phase) {
                PhysicalModelPhase.CANCEL -> setOf("cancel-sample-worker-v2.json")
                PhysicalModelPhase.DIALOGUE -> setOf("guards-worker-v2.json")
                else -> emptySet()
            }
        } else emptySet()
        check(traces.keys == expectedTraces)
        if (phase == PhysicalModelPhase.PRECHECK) check(!Files.exists(storage.proof.toPath(), NOFOLLOW_LINKS))
        if (!Files.exists(storage.proof.toPath(), NOFOLLOW_LINKS)) Files.createDirectory(storage.proof.toPath())
        phoneDirectory(storage.proof)
        traces.forEach { (name, trace) ->
            val raw = trace.json().toByteArray(Charsets.US_ASCII)
            check(raw.size in 1..4096)
            val key = when (name) { "cancel-sample-worker-v2.json" -> "sample_trace_sha256"; "guards-worker-v2.json" -> "guards_trace_sha256"; else -> "worker_trace_sha256" }
            check(phoneSha(raw) == extras[key])
            phoneNew(File(storage.proof, name), raw)
        }
        phoneNew(File(storage.proof, "${phase.file}-v1.json"), value.json().toByteArray(Charsets.US_ASCII))
        phoneNew(File(storage.proof, "${phase.file}-ready-v1.txt"), byteArrayOf())
        phoneEntries(storage.proof, names(phase))
    }
    private fun decode(raw: ByteArray, phase: PhysicalModelPhase): PhysicalModelProof {
        check(raw.isNotEmpty() && raw.all { it.toInt() in 32..126 })
        val json = JSONObject(raw.toString(Charsets.US_ASCII))
        fun number(key: String): Long {
            val field = json.get(key); check(field is Int || field is Long)
            return (field as Number).toLong()
        }
        fun integer(key: String) = number(key).also { check(it in 1..Int.MAX_VALUE.toLong()) }.toInt()
        fun bool(key: String) = (json.get(key) as? Boolean) ?: error("Invalid phone proof flag")
        val previous = if (phase == PhysicalModelPhase.PRECHECK) null else PhysicalPrior(PhysicalModelPhase.entries[phase.ordinal - 1],
            PhysicalProcessIdentity(integer("prior_pid"), number("prior_start"), integer("uid")), json.getString("prior_proof_sha256"))
        val flags = json.getJSONObject("checks").let { value -> value.keys().asSequence().associateWith { value.get(it) as? Boolean ?: error("Invalid phone check") } }
        val extras: Map<String, Any> = phase.extraKeys.associateWith { key -> when (key) {
            "revision", "receipt_count" -> number(key)
            "repairs" -> number(key).also { check(it == 0L) }.toInt()
            "fallback" -> bool(key)
            else -> json.getString(key)
        } }
        return PhysicalModelProof(phase, PhysicalProcessIdentity(integer("pid"), number("start"), integer("uid")), number("elapsed_ms"),
            PhysicalProofResources(number("shared_free_before"), number("shared_free_after"), number("memory_total_bytes"), number("memory_available_before"),
                number("memory_available_after"), bool("low_memory_before"), bool("low_memory_after")),
            PhysicalSourceCounts(number("source_verify_opened"), number("source_verify_closed"), number("source_verify_bytes"),
                number("source_import_opened"), number("source_import_closed"), number("source_import_bytes")), previous, flags, extras).also {
            check(it.json().toByteArray(Charsets.US_ASCII).contentEquals(raw))
        }
    }
    private fun names(through: PhysicalModelPhase): Set<String> = buildSet {
        for (phase in PhysicalModelPhase.entries.take(through.ordinal + 1)) {
            add("${phase.file}-v1.json"); add("${phase.file}-ready-v1.txt")
            if (phase.canonicalState) add("${phase.file}-worker-v2.json")
            if (phase == PhysicalModelPhase.CANCEL) add("cancel-sample-worker-v2.json")
            if (phase == PhysicalModelPhase.DIALOGUE) add("guards-worker-v2.json")
        }
    }
    companion object {
        val OWNER = "locallore-physical-source-v1\n".toByteArray(Charsets.US_ASCII)
        val PROBE = "LocalLore physical candidate source probe v1. No model or story.\n".toByteArray(Charsets.US_ASCII)
        const val PROBE_SHA = "72e34de83e7311b37f7a17361f3d71555209ffbfe4eb9e861cc11c7903e13422"
    }
}

internal fun phoneDirectory(file: File) {
    check(file.isAbsolute && file.canonicalFile == file && file.toPath().normalize() == file.toPath())
    var path: Path? = file.toPath()
    while (path != null) { check(Files.isDirectory(path, NOFOLLOW_LINKS) && !Files.isSymbolicLink(path)); path = path.parent }
    check(Os.lstat(file.path).st_uid == Process.myUid())
}
internal fun phoneRegular(file: File, size: Long? = null): BasicFileAttributes =
    Files.readAttributes(file.toPath(), BasicFileAttributes::class.java, NOFOLLOW_LINKS).also {
        val info = Os.lstat(file.path)
        check(it.isRegularFile && !it.isSymbolicLink && it.fileKey() != null && (size == null || it.size() == size) &&
            info.st_uid == Process.myUid() && info.st_ino > 0 && info.st_dev == Os.lstat(requireNotNull(file.parentFile).path).st_dev)
    }
internal fun phoneEntries(directory: File, names: Set<String>) = Files.newDirectoryStream(directory.toPath()).use { stream ->
    check(stream.map { it.fileName.toString() }.toSet() == names)
}
internal fun phoneRead(file: File, cap: Int): ByteArray {
    val before = phoneRegular(file); check(before.size() <= cap)
    val bytes = ByteArray(cap + 1)
    var count = 0
    Files.newInputStream(file.toPath(), READ, NOFOLLOW_LINKS).use { input ->
        while (count < bytes.size) { val n = input.read(bytes, count, bytes.size - count); if (n < 0) break; check(n > 0); count += n }
    }
    val after = phoneRegular(file)
    check(count <= cap && count.toLong() == before.size() && before.size() == after.size() &&
        before.fileKey() == after.fileKey() && before.lastModifiedTime() == after.lastModifiedTime())
    return bytes.copyOf(count)
}
internal fun phoneNew(file: File, bytes: ByteArray) = FileChannel.open(file.toPath(), CREATE_NEW, WRITE, NOFOLLOW_LINKS).use { channel ->
    val buffer = ByteBuffer.wrap(bytes)
    while (buffer.hasRemaining()) check(channel.write(buffer) > 0)
    channel.force(true)
}

/** Only IMPORT creates this object. Source verification/import have independently closed streams. */
internal class PhoneSource(private val env: PhoneEnvironment, private val counts: PhoneCounts, private val deadline: PhoneDeadline) {
    private val model = File(env.source(true), "model.litertlm")
    private val pin = phoneRegular(model, PhysicalModelPolicy.MODEL_BYTES)
    private fun open(verify: Boolean): InputStream {
        check(Looper.myLooper() != Looper.getMainLooper()); deadline.remaining(); check(counts.claim(verify))
        env.source(true)
        val before = phoneRegular(model, PhysicalModelPolicy.MODEL_BYTES)
        check(before.fileKey() == pin.fileKey() && before.lastModifiedTime() == pin.lastModifiedTime())
        val raw = Files.newInputStream(model.toPath(), READ, NOFOLLOW_LINKS)
        val opened = if (verify) counts.verifyOpened else counts.importOpened
        val closed = if (verify) counts.verifyClosed else counts.importClosed
        val bytes = if (verify) counts.verifyBytes else counts.importBytes
        check(opened.incrementAndGet() == 1L)
        val done = AtomicBoolean()
        return object : InputStream() {
            override fun read(): Int { val one = ByteArray(1); return if (read(one, 0, 1) < 0) -1 else one[0].toInt() and 255 }
            override fun read(buffer: ByteArray, offset: Int, length: Int): Int {
                check(!done.get()); deadline.remaining()
                val offMain = Looper.myLooper() != Looper.getMainLooper()
                counts.offMain.set(counts.offMain.get() && offMain); check(offMain)
                val n = raw.read(buffer, offset, length)
                deadline.remaining()
                if (n > 0) check(bytes.addAndGet(n.toLong()) <= PhysicalModelPolicy.MODEL_BYTES)
                return n
            }
            override fun close() {
                check(done.compareAndSet(false, true))
                raw.close(); check(closed.incrementAndGet() == 1L)
                val after = phoneRegular(model, PhysicalModelPolicy.MODEL_BYTES)
                check(after.fileKey() == pin.fileKey() && after.lastModifiedTime() == pin.lastModifiedTime())
            }
        }
    }
    fun verify(): Boolean {
        val digest = MessageDigest.getInstance("SHA-256")
        open(true).use { input ->
            val buffer = ByteArray(65_536)
            while (true) { val n = input.read(buffer); if (n < 0) break; check(n > 0); digest.update(buffer, 0, n) }
        }
        return counts.verifyBytes.get() == PhysicalModelPolicy.MODEL_BYTES &&
            digest.digest().joinToString("") { "%02x".format(it) } == PhysicalModelPolicy.MODEL_SHA256
    }
    fun openImport(): InputStream = open(false)
}

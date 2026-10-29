/* Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0 */
package org.locallore.app

import android.content.Context
import android.os.Looper
import android.os.Process
import android.os.SystemClock
import android.system.Os
import androidx.test.ext.junit.runners.AndroidJUnit4
import androidx.test.platform.app.InstrumentationRegistry
import java.io.File
import java.nio.ByteBuffer
import java.nio.channels.FileChannel
import java.nio.file.Files
import java.nio.file.LinkOption.NOFOLLOW_LINKS
import java.nio.file.StandardOpenOption.CREATE_NEW
import java.nio.file.StandardOpenOption.READ
import java.nio.file.StandardOpenOption.WRITE
import java.nio.file.attribute.BasicFileAttributes
import java.security.MessageDigest
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.NonCancellable
import kotlinx.coroutines.TimeoutCancellationException
import kotlinx.coroutines.currentCoroutineContext
import kotlinx.coroutines.delay
import kotlinx.coroutines.ensureActive
import kotlinx.coroutines.runBlocking
import kotlinx.coroutines.withContext
import kotlinx.coroutines.withTimeout
import org.json.JSONArray
import org.json.JSONObject
import org.json.JSONTokener
import org.junit.Assert.fail
import org.junit.Test
import org.junit.runner.RunWith

/** Passive continuation only. The host establishes exact old-process death within the same Android boot. */
@RunWith(AndroidJUnit4::class)
class OriginalAuthorRestartInstrumentedTest {
    @Test fun recordsOriginalAuthorAfterExternalRestartWithoutInference() = runBlocking {
        val phase = RestartProof()
        var output: Artifacts? = null
        var workspace = 0L
        var archive = 0L
        var workspaceCloseAttempted = false
        var archiveCloseAttempted = false
        var archiveRequest: ByteArray? = null
        try {
            withTimeout(WORK_MS) { withContext(Dispatchers.IO) {
                val app = selected()
                val anchor = anchor(app)
                output = Artifacts(freshDirectory(anchor, OUTPUT_ROOT))
                val saved = checkNotNull(output)
                val baseline = Baseline(anchor)
                phase.importHash = sha(baseline.importRaw)
                phase.authorHash = sha(baseline.authorRaw)
                val author = baseline.author
                val imported = parse(baseline.importRaw)
                fields(imported, "version", "scope", "status", "stage", "reason", "process", "package", "elapsed_ms",
                    "model", "source_counts", "accepted")
                completed(imported, "original_author_model_import_v1")
                completed(author, "original_author_model_v1")
                val importProcess = process(imported.getJSONObject("process"))
                val authorProcess = process(author.getJSONObject("process"))
                check(importProcess.uid == Process.myUid().toLong() && authorProcess.uid == Process.myUid().toLong())
                // These elapsed-time comparisons cannot establish continuity across an Android reboot.
                check(importProcess.start < authorProcess.start && authorProcess.start < Process.getStartElapsedRealtime())
                check(author.get("prior_import_sha256") == phase.importHash)
                same(imported.getJSONObject("model"), imported.getJSONObject("accepted"))
                val model = imported.getJSONObject("model")
                fields(model, "bytes", "sha256")
                val sourceCounts = imported.getJSONObject("source_counts")
                fields(sourceCounts, "opened", "closed", "bytes", "off_main")
                check(integer(sourceCounts, "opened") == 1L && integer(sourceCounts, "closed") == 1L &&
                    integer(sourceCounts, "bytes", 1) == integer(model, "bytes", 1) && sourceCounts.get("off_main") == true)
                val profile = author.getJSONObject("profile")
                fields(profile, "id", "model_sha256", "runtime_revision", "template_sha256", "worker_sha256",
                    "profile_manifest_sha256", "context_tokens", "director_tokens", "narrator_tokens", "deadline_ms", "repair_limit")
                check(text(profile, "model_sha256", HASH) == text(imported.getJSONObject("model"), "sha256", HASH))
                val priorCreate = baseline.envelope("create-v1.json")
                creation(priorCreate, true)
                val scope = priorCreate.getJSONObject("scope")
                check(text(scope, "story", STORY) == "original-" + text(author, "creation_id", CREATION))
                check(text(scope, "branch", WORD) == "main")
                val catalog = baseline.envelope("workspace-created-v1.json")
                fields(catalog, "persistent", "location", "schema_version", "database_schema_version", "stories")
                check(catalog.get("persistent") == true && integer(catalog, "schema_version") == 1L &&
                    integer(catalog, "database_schema_version") == 5L)
                val location = catalog.get("location")
                check(location is String && localUtf8(location).size in 1..4096)
                check(catalog.getJSONArray("stories").length() == 1)
                val story = catalog.getJSONArray("stories").getJSONObject(0)
                fields(story, "scope", "title", "revision", "drafts")
                same(scope, story.getJSONObject("scope"))
                check(story.get("title") is String && integer(story, "revision") == 0L && integer(story, "drafts") == 0L)
                val priorSnapshot = baseline.envelope("snapshot-created-v1.json")
                fields(priorSnapshot, "scope", "revision", "rules", "player", "inventory", "receipts")
                same(scope, priorSnapshot.getJSONObject("scope"))
                check(integer(priorSnapshot, "revision") == 0L)
                check(text(priorSnapshot.getJSONObject("player"), "observer", WORD).isNotEmpty())
                same(priorSnapshot, baseline.envelope("snapshot-reopened-v1.json"))
                val recovery = command("authoring_create").put("job", text(author, "job", WORD))
                    .put("review_sha256", text(author, "review_sha256", HASH))
                    .put("creation_id", text(author, "creation_id", CREATION))
                val authorRoot = File(anchor, AUTHOR_ROOT)
                val databaseRoot = File(authorRoot, "workspace-v1").also { directory(it, authorRoot) }
                val database = File(databaseRoot, "stories.sqlite3")
                check(regular(database).size() in 1..DATABASE_CAP)
                check(anchor.usableSpace >= TOTAL_CAP.toLong() + ARTIFACT_CAP)
                phase.stage = "open"
                currentCoroutineContext().ensureActive()
                val profileRaw = localUtf8(profile.toString()).also { check(it.size in 1..4096) }
                workspace = NativeWorkspace.openLocal(database.path, profileRaw)
                check(workspace > 0)
                phase.workspaceClosed = false
                same(catalog, saved.record("workspace-before-v1.json", exchange(workspace, command("workspace"))))
                phase.pendingBefore = pending(workspace)
                check(phase.pendingBefore == false)
                phase.stage = "recover"
                currentCoroutineContext().ensureActive()
                val recovered = saved.record("recover-v1.json", exchange(workspace, recovery))
                creation(recovered, false)
                same(scope, recovered.getJSONObject("scope"))
                phase.stage = "snapshot"
                val snapshot = command("play_snapshot").put("session", text(recovered, "session", WORD))
                    .put("scope", scope).put("expected_revision", 0)
                same(priorSnapshot, saved.record("snapshot-v1.json", exchange(workspace, snapshot)))
                phase.stage = "retry"
                currentCoroutineContext().ensureActive()
                val retry = saved.record("retry-v1.json", exchange(workspace, recovery))
                creation(retry, false)
                same(scope, retry.getJSONObject("scope"))
                same(catalog, saved.record("workspace-after-v1.json", exchange(workspace, command("workspace"))))
                phase.stage = "archive"
                val staging = freshDirectory(saved.root, "archive-staging")
                archive = NativeArchive.open(database.path, staging.path)
                check(archive > 0)
                phase.archiveClosed = false
                val request = localUtf8(JSONObject().put("story", text(scope, "story", STORY))
                    .put("branch", "main").put("expected_revision", 0).toString())
                archiveRequest = request
                val prepared = ArchiveNativeWire.prepared(NativeArchive.prepareExport(archive, request))
                val archiveRaw = NativeArchive.exportBytes(archive, prepared.token)
                saved.put("archive-v1.json", archiveRaw)
                parse(archiveRaw)
                check(archiveRaw.contentEquals(baseline.raw.getValue("archive-v1.json")))
                phase.pendingAfter = pending(workspace)
                check(phase.pendingAfter == false)
                baseline.unchanged()
                phase.stage = "close"
                archiveCloseAttempted = true
                NativeArchive.close(archive)
                invalidArchive(archive, request)
                phase.archiveClosed = true
                archive = 0
                workspaceCloseAttempted = true
                NativeWorkspace.close(workspace)
                invalidWorkspace(workspace)
                phase.workspaceClosed = true
                workspace = 0
                baseline.unchanged()
                check(phase.elapsed() <= PHASE_MS)
                phase.stage = "completed"
            } }
        } catch (_: TimeoutCancellationException) {
            phase.reason = "deadline"
        } catch (_: Throwable) {
            phase.reason = "checks_failed"
        }
        try { withContext(NonCancellable + Dispatchers.IO) {
            // Never retry a close whose completion was not observed.
            if (archive > 0) {
                if (archiveCloseAttempted) phase.archiveClosed = null else {
                    archiveCloseAttempted = true
                    try {
                        NativeArchive.close(archive)
                        invalidArchive(archive, checkNotNull(archiveRequest))
                        phase.archiveClosed = true
                    } catch (_: Throwable) { phase.archiveClosed = null }
                }
                if (phase.archiveClosed != true) phase.reason = "resource_uncertain"
            }
            if (workspace > 0) {
                if (workspaceCloseAttempted) phase.workspaceClosed = null else {
                    workspaceCloseAttempted = true
                    try {
                        NativeWorkspace.close(workspace)
                        invalidWorkspace(workspace)
                        phase.workspaceClosed = true
                    } catch (_: Throwable) { phase.workspaceClosed = null }
                }
                if (phase.workspaceClosed != true) phase.reason = "resource_uncertain"
            }
            output?.let { saved ->
                val proof = localUtf8(phase.json(saved).toString())
                check(proof.size <= PROOF_CAP)
                writeNew(File(saved.root, "proof-v1.json"), proof)
            }
        } } catch (_: Throwable) { fail("Original AUTHOR restart proof capture refused") }
        if (output == null || phase.reason != null || phase.stage != "completed")
            fail("Original AUTHOR restart refused: ${phase.stage}/${phase.reason ?: "checks_failed"}")
    }

    private class RestartProof {
        private val start = SystemClock.elapsedRealtime()
        var stage = "admission"
        var reason: String? = null
        var importHash: String? = null
        var authorHash: String? = null
        var pendingBefore: Boolean? = null
        var pendingAfter: Boolean? = null
        var workspaceClosed: Boolean? = null
        var archiveClosed: Boolean? = null
        fun elapsed() = SystemClock.elapsedRealtime() - start
        fun json(output: Artifacts) = JSONObject().put("version", 1).put("scope", "original_author_external_restart_v1")
            .put("status", if (stage == "completed" && reason == null) "completed" else "refused")
            .put("stage", stage).put("reason", reason ?: JSONObject.NULL)
            .put("process", JSONObject().put("pid", Process.myPid()).put("uid", Process.myUid())
                .put("start_elapsed_ms", Process.getStartElapsedRealtime()))
            .put("package", PACKAGE).put("elapsed_ms", elapsed())
            .put("import_proof_sha256", importHash ?: JSONObject.NULL).put("author_proof_sha256", authorHash ?: JSONObject.NULL)
            .put("records", output.bindings()).put("pending_before", pendingBefore ?: JSONObject.NULL)
            .put("pending_after", pendingAfter ?: JSONObject.NULL).put("workspace_closed", workspaceClosed ?: JSONObject.NULL)
            .put("archive_closed", archiveClosed ?: JSONObject.NULL)
    }

    private class Artifacts(val root: File) {
        private val saved = mutableMapOf<String, JSONObject>()
        private var total = 0
        fun put(name: String, raw: ByteArray) {
            check(name in RECORDS && name !in saved && raw.size in 1..ARTIFACT_CAP && total + raw.size <= TOTAL_CAP)
            writeNew(File(root, name), raw)
            total += raw.size
            saved[name] = binding(raw)
        }
        fun record(name: String, raw: ByteArray): JSONObject { put(name, raw); return data(parse(raw)) }
        fun bindings() = JSONObject().also { value -> RECORDS.forEach { value.put(it, saved[it] ?: JSONObject.NULL) } }
    }

    /** The original fixed sidecars are read and bound; the model and database bytes are not read here. */
    private class Baseline(anchor: File) {
        private val pins = mutableMapOf<File, Pair<BasicFileAttributes, String>>()
        val raw = mutableMapOf<String, ByteArray>()
        val importRaw: ByteArray
        val authorRaw: ByteArray
        val author: JSONObject
        init {
            val imported = File(anchor, IMPORT_ROOT).also { directory(it, anchor) }
            entries(imported, setOf("import-v1.json"))
            importRaw = bound(File(imported, "import-v1.json"), PROOF_CAP)
            val root = File(anchor, AUTHOR_ROOT).also { directory(it, anchor) }
            entries(root, (BASE_RECORDS + BASE_TRACES + "proof-v1.json" + "workspace-v1" + "archive-staging").toSet())
            directory(File(root, "workspace-v1"), root)
            directory(File(root, "archive-staging"), root)
            authorRaw = bound(File(root, "proof-v1.json"), PROOF_CAP)
            author = parse(authorRaw)
            fields(author, "version", "scope", "status", "stage", "reason", "process", "package", "elapsed_ms",
                "prior_import_sha256", "profile", "job", "input_sha256", "review_sha256", "creation_id", "records", "traces")
            var total = 0
            for ((field, names) in listOf("records" to BASE_RECORDS, "traces" to BASE_TRACES)) {
                val bindings = author.getJSONObject(field)
                fields(bindings, *names.toTypedArray())
                for (name in names) {
                    val bytes = bound(File(root, name), ARTIFACT_CAP)
                    total += bytes.size
                    check(total <= TOTAL_CAP)
                    same(binding(bytes), bindings.getJSONObject(name))
                    raw[name] = bytes
                }
            }
        }
        private fun bound(file: File, cap: Int): ByteArray {
            val before = regular(file)
            return read(file, cap).also { unchanged(file, before); pins[file] = before to sha(it) }
        }
        fun envelope(name: String) = data(parse(raw.getValue(name)))
        fun unchanged() {
            pins.forEach { (file, pin) -> unchanged(file, pin.first); check(sha(read(file, ARTIFACT_CAP)) == pin.second) }
        }
    }

    private data class ProcessIdentity(val uid: Long, val start: Long)

    companion object {
        private const val PACKAGE = "org.locallore.app.litertverify"
        private const val IMPORT_ROOT = "original-author-import-proof-v1"
        private const val AUTHOR_ROOT = "original-author-proof-v1"
        private const val OUTPUT_ROOT = "original-author-restart-proof-v1"
        private const val ARTIFACT_CAP = 1_048_576
        private const val TOTAL_CAP = 2 * ARTIFACT_CAP
        private const val PROOF_CAP = 32_768
        private const val DATABASE_CAP = 64L * ARTIFACT_CAP
        private const val WORK_MS = 150_000L
        private const val PHASE_MS = 180_000L
        private val HASH = Regex("[0-9a-f]{64}")
        private val WORD = Regex("[A-Za-z0-9_-]{1,128}")
        private val CREATION = Regex("[0-9a-f]{32}")
        private val STORY = Regex("original-[0-9a-f]{32}")
        private val RECORDS = listOf("workspace-before-v1.json", "recover-v1.json", "snapshot-v1.json",
            "retry-v1.json", "workspace-after-v1.json", "archive-v1.json")
        private val BASE_RECORDS = listOf("input-v1.json", "begin-v1.json", "generated-v1.json", "review-v1.json", "create-v1.json", "retry-v1.json",
            "workspace-before-v1.json", "workspace-generated-v1.json", "workspace-reviewed-v1.json", "workspace-created-v1.json", "snapshot-created-v1.json", "snapshot-reopened-v1.json", "archive-v1.json")
        private val BASE_TRACES = listOf("worker-v2.json", "send-v2.json", "callback-v1.json", "status-v1.json")

        private fun selected(): Context {
            check(InstrumentationRegistry.getArguments().getString("class") ==
                "${OriginalAuthorRestartInstrumentedTest::class.java.name}#recordsOriginalAuthorAfterExternalRestartWithoutInference")
            val app = InstrumentationRegistry.getInstrumentation().targetContext.applicationContext
            check(BuildConfig.DEBUG && !BuildConfig.MODEL_RECEIPT_VERIFICATION && !BuildConfig.MODEL_VOLUME_VERIFICATION &&
                !BuildConfig.PHYSICAL_MODEL_VERIFICATION && !BuildConfig.INPUT_PROCESS_VERIFICATION)
            check(app.packageName == PACKAGE && app.applicationInfo.uid == Process.myUid() && Process.myUid() >= 10_000)
            check(Looper.myLooper() != Looper.getMainLooper())
            return app
        }
        // Resolve only the trusted Context alias; every constructed descendant remains strict.
        private fun anchor(context: Context) = context.noBackupFilesDir.canonicalFile.also { directory(it) }
        private fun exists(file: File) = Files.exists(file.toPath(), NOFOLLOW_LINKS)
        private fun directory(file: File, parent: File? = null) {
            check(file.isAbsolute && file.toPath().normalize() == file.toPath())
            var path = file.toPath()
            while (true) {
                check(Files.isDirectory(path, NOFOLLOW_LINKS) && !Files.isSymbolicLink(path))
                path = path.parent ?: break
            }
            check(file.canonicalFile == file)
            val stat = Os.lstat(file.path)
            check(stat.st_uid == Process.myUid())
            parent?.let { check(file.parentFile == it && stat.st_dev == Os.lstat(it.path).st_dev) }
        }
        private fun freshDirectory(parent: File, name: String) = File(parent, name).also {
            directory(parent)
            check(!exists(it))
            Files.createDirectory(it.toPath())
            directory(it, parent)
        }
        private fun regular(file: File): BasicFileAttributes {
            val parent = checkNotNull(file.parentFile)
            directory(parent)
            val attrs = Files.readAttributes(file.toPath(), BasicFileAttributes::class.java, NOFOLLOW_LINKS)
            val stat = Os.lstat(file.path)
            check(attrs.isRegularFile && !attrs.isSymbolicLink && attrs.fileKey() != null && file.canonicalFile == file)
            check(stat.st_uid == Process.myUid() && stat.st_nlink == 1L && stat.st_dev == Os.lstat(parent.path).st_dev)
            return attrs
        }
        private fun unchanged(file: File, before: BasicFileAttributes) {
            val after = regular(file)
            check(before.size() == after.size() && before.fileKey() == after.fileKey() && before.lastModifiedTime() == after.lastModifiedTime())
        }
        private fun entries(root: File, names: Set<String>) {
            Files.newDirectoryStream(root.toPath()).use { stream ->
                val actual = mutableSetOf<String>()
                for (path in stream) { check(actual.add(path.fileName.toString()) && actual.size <= names.size) }
                check(actual == names)
            }
        }
        private fun read(file: File, cap: Int): ByteArray {
            val before = regular(file)
            check(before.size() in 1..cap.toLong())
            val raw = ByteArray(cap + 1)
            var count = 0
            Files.newInputStream(file.toPath(), READ, NOFOLLOW_LINKS).use { input ->
                while (count < raw.size) {
                    val next = input.read(raw, count, raw.size - count)
                    if (next < 0) break
                    check(next > 0)
                    count += next
                }
            }
            check(count.toLong() == before.size() && count <= cap)
            unchanged(file, before)
            return raw.copyOf(count)
        }
        private fun writeNew(file: File, raw: ByteArray) {
            directory(checkNotNull(file.parentFile))
            check(raw.size in 1..ARTIFACT_CAP)
            FileChannel.open(file.toPath(), CREATE_NEW, WRITE, NOFOLLOW_LINKS).use { channel ->
                val buffer = ByteBuffer.wrap(raw)
                while (buffer.hasRemaining()) check(channel.write(buffer) > 0)
                channel.force(true)
            }
            check(regular(file).size() == raw.size.toLong())
        }
        private fun sha(raw: ByteArray) = MessageDigest.getInstance("SHA-256").digest(raw).joinToString("") { "%02x".format(it) }
        private fun binding(raw: ByteArray) = JSONObject().put("bytes", raw.size).put("sha256", sha(raw))
        private fun fields(value: JSONObject, vararg names: String) = check(value.keys().asSequence().toSet() == names.toSet())
        private fun integer(value: JSONObject, name: String, minimum: Long = 0, maximum: Long = Long.MAX_VALUE): Long {
            val number = value.get(name)
            check(number is Int || number is Long)
            return (number as Number).toLong().also { check(it in minimum..maximum) }
        }
        private fun text(value: JSONObject, name: String, pattern: Regex): String {
            val string = value.get(name)
            check(string is String && pattern.matches(string))
            return string
        }
        private fun completed(value: JSONObject, scope: String) {
            check(integer(value, "version") == 1L && value.get("scope") == scope && value.get("status") == "completed" &&
                value.get("stage") == "completed" && value.get("reason") === JSONObject.NULL && value.get("package") == PACKAGE)
            integer(value, "elapsed_ms", 0, PHASE_MS)
        }
        private fun process(value: JSONObject): ProcessIdentity {
            fields(value, "pid", "uid", "start_elapsed_ms")
            integer(value, "pid", 1, Int.MAX_VALUE.toLong())
            return ProcessIdentity(integer(value, "uid", 10_000, Int.MAX_VALUE.toLong()), integer(value, "start_elapsed_ms", 1))
        }
        private fun command(op: String) = JSONObject().put("op", op)
        private fun exchange(handle: Long, command: JSONObject): ByteArray {
            val raw = localUtf8(JSONObject().put("version", 1).put("command", command).toString())
            check(raw.size <= 24_576)
            return NativeWorkspace.call(handle, raw)
        }
        private fun data(value: JSONObject): JSONObject {
            fields(value, "version", "status", "data")
            check(integer(value, "version") == 1L && value.get("status") == "ok")
            return value.getJSONObject("data")
        }
        private fun creation(value: JSONObject, created: Boolean) {
            fields(value, "session", "scope", "revision", "created")
            text(value, "session", WORD)
            check(integer(value, "revision") == 0L && value.get("created") is Boolean && value.get("created") == created)
            fields(value.getJSONObject("scope"), "story", "branch")
        }
        private fun pending(handle: Long): Boolean {
            val value = data(parse(NativeWorkspace.pollInference(handle)))
            fields(value, "pending")
            return value.get("pending") !== JSONObject.NULL
        }
        private suspend fun invalidWorkspace(handle: Long) = withTimeout(5_000) {
            while (true) {
                val value = parse(exchange(handle, command("workspace")))
                if (value.optString("status") == "rejected") {
                    fields(value, "version", "status", "error")
                    check(integer(value, "version") == 1L && value.get("error") == "InvalidHandle")
                    break
                }
                data(value)
                delay(10)
            }
        }
        private fun invalidArchive(handle: Long, request: ByteArray) {
            val value = parse(NativeArchive.prepareExport(handle, request))
            fields(value, "version", "status", "error")
            check(integer(value, "version") == 1L && value.get("status") == "rejected" && value.get("error") == "InvalidHandle")
        }
        private fun parse(raw: ByteArray): JSONObject {
            val text = localText(raw, ARTIFACT_CAP)
            StrictJson(text).validate()
            val parser = JSONTokener(text)
            return (parser.nextValue() as JSONObject).also { check(parser.nextClean() == '\u0000') }
        }
        private fun same(expected: Any?, actual: Any?) {
            when (expected) {
                is JSONObject -> {
                    check(actual is JSONObject && expected.keys().asSequence().toSet() == actual.keys().asSequence().toSet())
                    expected.keys().forEach { same(expected.get(it), actual.get(it)) }
                }
                is JSONArray -> {
                    check(actual is JSONArray && expected.length() == actual.length())
                    for (index in 0 until expected.length()) same(expected.get(index), actual.get(index))
                }
                is Number -> check(actual is Number && expected.toString() == actual.toString())
                else -> check(expected == actual)
            }
        }
    }

    /** Android's permissive JSONTokener alone would accept duplicate keys and non-JSON syntax. */
    private class StrictJson(private val text: String) {
        private var position = 0
        private var values = 0
        fun validate() { value(0); space(); check(position == text.length) }
        private fun space() { while (position < text.length && text[position] in " \t\r\n") position++ }
        private fun take(c: Char): Boolean { space(); return if (position < text.length && text[position] == c) { position++; true } else false }
        private fun value(depth: Int) {
            check(depth <= 64 && ++values <= 100_000)
            space()
            check(position < text.length)
            when (text[position]) {
                '{' -> {
                    position++
                    val keys = mutableSetOf<String>()
                    if (!take('}')) {
                        do { space(); check(keys.add(string())); check(take(':')); value(depth + 1) } while (take(','))
                        check(take('}'))
                    }
                }
                '[' -> {
                    position++
                    if (!take(']')) { do { value(depth + 1) } while (take(',')); check(take(']')) }
                }
                '"' -> string()
                't' -> literal("true")
                'f' -> literal("false")
                'n' -> literal("null")
                else -> {
                    val match = NUMBER.find(text, position)
                    check(match != null && match.range.first == position)
                    val token = match.value
                    if (token.none { it in ".eE" }) check(token.toLongOrNull() != null)
                    else check(token.toDouble().isFinite())
                    position += token.length
                }
            }
        }
        private fun literal(value: String) { check(text.startsWith(value, position)); position += value.length }
        private fun string(): String {
            val start = position
            check(position < text.length && text[position++] == '"')
            while (position < text.length) {
                val c = text[position++]
                check(c >= ' ')
                if (c == '"') {
                    return (JSONTokener(text.substring(start, position)).nextValue() as String).also { localUtf8(it) }
                }
                if (c == '\\') {
                    check(position < text.length)
                    when (text[position++]) {
                        '"', '\\', '/', 'b', 'f', 'n', 'r', 't' -> Unit
                        'u' -> { repeat(4) { check(position < text.length && text[position++] in "0123456789abcdefABCDEF") } }
                        else -> error("JSON escape")
                    }
                }
            }
            error("JSON string")
        }
        companion object { private val NUMBER = Regex("-?(?:0|[1-9][0-9]*)(?:\\.[0-9]+)?(?:[eE][+-]?[0-9]+)?") }
    }
}

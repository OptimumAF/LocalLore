/* Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0 */
package org.locallore.app

import android.app.ActivityManager
import android.content.Context
import android.content.ContextWrapper
import android.os.Looper
import android.os.Process
import android.os.SystemClock
import android.system.Os
import androidx.test.ext.junit.runners.AndroidJUnit4
import androidx.test.platform.app.InstrumentationRegistry
import java.io.File
import java.io.InputStream
import java.nio.ByteBuffer
import java.nio.channels.FileChannel
import java.nio.file.Files
import java.nio.file.LinkOption.NOFOLLOW_LINKS
import java.nio.file.StandardOpenOption.CREATE_NEW
import java.nio.file.StandardOpenOption.READ
import java.nio.file.StandardOpenOption.WRITE
import java.nio.file.attribute.BasicFileAttributes
import java.security.MessageDigest
import java.util.concurrent.atomic.AtomicBoolean
import java.util.concurrent.atomic.AtomicLong
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.NonCancellable
import kotlinx.coroutines.delay
import kotlinx.coroutines.runBlocking
import kotlinx.coroutines.withContext
import kotlinx.coroutines.withTimeout
import org.json.JSONArray
import org.json.JSONObject
import org.json.JSONTokener
import org.junit.Assert.fail
import org.junit.Test
import org.junit.runner.RunWith

/** Explicitly selected, private factory/JNI/model experiment; no Activity or Compose substitute. */
@RunWith(AndroidJUnit4::class)
class OriginalAuthorModelInstrumentedTest {
    @Test fun importsTheVerifiedOriginalAuthorModelOnce() = runBlocking {
        val phase = ImportProof()
        var proof: File? = null
        try {
            withTimeout(PHASE_MS) { withContext(Dispatchers.IO) {
                val app = selected("importsTheVerifiedOriginalAuthorModelOnce")
                val anchor = anchor(app)
                val accepted = File(anchor, "local-model-v1")
                check(!exists(accepted) && !exists(File(anchor, "workspace-v1")))
                proof = freshDirectory(anchor, IMPORT_ROOT)
                phase.stage = "source"
                val sourceRoot = File(anchor, SOURCE_ROOT).also { directory(it, anchor) }
                entries(sourceRoot, setOf("model.litertlm"))
                val source = File(sourceRoot, "model.litertlm")
                val pin = regular(source, MODEL_BYTES)
                resources(app, anchor, MODEL_BYTES)
                val counts = SourceCounts(source, pin)
                phase.counts = counts
                phase.stage = "import"
                val store = CandidateLocalModel.store(app)
                val files = store.import(counts::open)
                phase.stage = "installed"
                val installed = checkNotNull(store.installed())
                check(files == installed && files.root == accepted && files.root.canonicalFile == accepted)
                directory(files.root, anchor); directory(files.cache, files.root)
                regular(files.model, MODEL_BYTES)
                check(files.model == File(accepted, "model.litertlm"))
                check(counts.opened.get() == 1L && counts.closed.get() == 1L && counts.bytes.get() == MODEL_BYTES && counts.offMain.get())
                unchanged(source, pin); entries(sourceRoot, setOf("model.litertlm"))
                check(!exists(File(anchor, "workspace-v1")))
                phase.accepted = identity()
                phase.stage = "completed"
            } }
        } catch (_: Throwable) { phase.reason = "checks_failed" }
        try { withContext(NonCancellable + Dispatchers.IO) {
            proof?.let { writeNew(File(it, "import-v1.json"), localUtf8(phase.json().toString())) }
        } } catch (_: Throwable) { fail("Original author import proof capture refused") }
        if (phase.reason != null || phase.stage != "completed") fail("Original author import refused: ${phase.stage}/checks_failed")
    }

    @Test fun recordsOneRealAuthorCreationAndInferenceFreeReopen() = runBlocking {
        val phase = AuthorProof()
        var artifacts: Artifacts? = null
        var diagnostics: DiagnosticArtifacts? = null
        var responseCapture: AuthorResponseCapture? = null
        var transport: NativeWorkspaceTransport? = null
        var owner: LocalInferenceOwner? = null
        var handle = 0L
        var passive = 0L
        var archive = 0L
        val worker = LiteRtWorkerTrace()
        val send = LiteRtSendTrace()
        val callbacks = LiteRtCallbackTrace()
        val statuses = LiteRtStatusTrace()
        var tracesObserved = false
        try {
            withTimeout(PHASE_MS) { withContext(Dispatchers.IO) {
                val app = selected("recordsOneRealAuthorCreationAndInferenceFreeReopen")
                val anchor = anchor(app)
                val priorFile = File(File(anchor, IMPORT_ROOT), "import-v1.json")
                directory(checkNotNull(priorFile.parentFile), anchor)
                val priorRaw = read(priorFile, ARTIFACT_CAP)
                val prior = parse(priorRaw)
                fields(prior, "version", "scope", "status", "stage", "reason", "process", "package", "model", "source_counts", "accepted", "elapsed_ms")
                check(prior.getInt("version") == 1 && prior.getString("scope") == "original_author_model_import_v1")
                check(prior.getString("status") == "completed" && prior.getString("stage") == "completed" && prior.isNull("reason"))
                check(prior.getString("package") == PACKAGE)
                val previous = prior.getJSONObject("process")
                fields(previous, "pid", "uid", "start_elapsed_ms")
                check(previous.getInt("uid") == Process.myUid())
                check(previous.getLong("start_elapsed_ms") < Process.getStartElapsedRealtime())
                same(identity(), prior.getJSONObject("model")); same(identity(), prior.getJSONObject("accepted"))
                val counts = prior.getJSONObject("source_counts")
                fields(counts, "opened", "closed", "bytes", "off_main")
                check(counts.getLong("opened") == 1L && counts.getLong("closed") == 1L && counts.getLong("bytes") == MODEL_BYTES && counts.getBoolean("off_main"))
                phase.prior = sha(priorRaw)
                val root = freshDirectory(anchor, AUTHOR_ROOT)
                artifacts = Artifacts(root)
                diagnostics = DiagnosticArtifacts(freshDirectory(anchor, DIAGNOSTIC_ROOT))
                val diagnostic = checkNotNull(diagnostics)
                val input = fixture()
                val inputRaw = localUtf8(OriginalStoryWire.input(input).toString())
                check(sha(inputRaw) == INPUT_SHA256) // Explicit synthetic consent before enabling raw capture.
                diagnostic.put("input-v1.json", inputRaw)
                val isolated = object : ContextWrapper(app) {
                    override fun getApplicationContext(): Context = this
                    override fun getNoBackupFilesDir(): File = root
                }
                check(isolated.applicationContext === isolated && isolated.applicationInfo.uid == Process.myUid())
                check(isolated.noBackupFilesDir.canonicalFile == root && isolated.packageName == PACKAGE)
                val store = CandidateLocalModel.store(app)
                val files = checkNotNull(store.installed())
                directory(files.root, anchor); directory(files.cache, files.root); regular(files.model, MODEL_BYTES)
                check(files.root == File(anchor, "local-model-v1") && files.model == File(files.root, "model.litertlm"))
                resources(app, anchor, 0)
                val loadAdmitted = AtomicBoolean()
                val config = CandidateLocalModel.config(files) {
                    store.admitRuntime()
                    directory(root, anchor)
                    // The initial loading margin is not reapplied after SDK allocation.
                    resources(app, anchor, 0, memory = loadAdmitted.compareAndSet(false, true))
                }
                phase.profile = parse(config.profileBytes())
                owner = config.createOwner(trace = worker, sendTrace = send, callbackTrace = callbacks, statusTrace = statuses)
                responseCapture = checkNotNull(owner).installAuthorResponseCapture()
                tracesObserved = true
                transport = NativeWorkspaceTransport(isolated, owner)
                val actual = checkNotNull(transport)
                val output = checkNotNull(artifacts)
                phase.stage = "native_open"
                val before = recorded(output, actual, "workspace-before-v1.json", command("workspace"))
                check(before.getJSONArray("stories").length() == 0)
                diagnostic.put("workspace-before-v1.json", read(File(output.root, "workspace-before-v1.json"), ARTIFACT_CAP))
                handle = actual.forkHandle()
                output.put("input-v1.json", inputRaw)
                phase.stage = "begin"
                val begun = recorded(output, actual, "begin-v1.json", command("authoring_begin").put("input", OriginalStoryWire.input(input)))
                val job = OriginalStoryWire.job(begun)
                check(job.provider == "local")
                phase.job = job.job; phase.inputHash = job.inputSha256
                phase.stage = "generate"
                val generatedReply = actual.exchange(command("authoring_generate").put("job", job.job))
                val generatedRaw = localUtf8(generatedReply.toString())
                output.put("generated-v1.json", generatedRaw)
                diagnostic.put("generated-v1.json", generatedRaw)
                // Only a returned operation with known SDK ownership permits this passive query.
                // Retain the rejected envelope before attempting to decode its successful data.
                closedAuthor(worker.snapshot(), send.snapshot(), callbacks.snapshot(), statuses.snapshot())
                check(!checkNotNull(owner).quarantined)
                val afterGeneration = actual.exchange(command("workspace"))
                diagnostic.put("workspace-after-v1.json", localUtf8(afterGeneration.toString()))
                same(before, data(afterGeneration))
                diagnostic.conserved = true
                val generated = OriginalStoryWire.generated(data(generatedReply))
                check(generated.job == job.job && generated.provider == "local" && generated.input == input)
                same(before, recorded(output, actual, "workspace-generated-v1.json", command("workspace")))
                closedAuthor(worker.snapshot(), send.snapshot(), callbacks.snapshot(), statuses.snapshot())
                check(!checkNotNull(owner).quarantined)
                phase.stage = "review"
                val review = OriginalStoryWire.review(recorded(output, actual, "review-v1.json", command("authoring_review")
                    .put("job", job.job).put("input", OriginalStoryWire.input(generated.input))
                    .put("proposal", OriginalStoryWire.proposal(generated.proposal)).put("title", TITLE)))
                check(review.job == job.job && review.input == generated.input && review.proposal == generated.proposal && review.title == TITLE)
                phase.reviewHash = review.reviewSha256
                same(before, recorded(output, actual, "workspace-reviewed-v1.json", command("workspace")))
                phase.stage = "create"
                phase.creationId = CREATION_ID
                val createCommand = command("authoring_create").put("job", job.job).put("review_sha256", review.reviewSha256).put("creation_id", CREATION_ID)
                val created = recorded(output, actual, "create-v1.json", createCommand)
                creation(created, true)
                val scope = created.getJSONObject("scope")
                val catalog = recorded(output, actual, "workspace-created-v1.json", command("workspace")).getJSONArray("stories")
                check(catalog.length() == 1)
                val story = catalog.getJSONObject(0)
                same(scope, story.getJSONObject("scope")); check(story.getString("title") == TITLE && story.getLong("revision") == 0L && story.getLong("drafts") == 0L)
                val createdSnapshot = recorded(output, actual, "snapshot-created-v1.json", command("play_snapshot")
                    .put("session", created.getString("session")).put("scope", scope).put("expected_revision", 0))
                snapshot(createdSnapshot, scope)
                val sdkBefore = sdkCounts(worker, send, callbacks, statuses)
                withContext(Dispatchers.Main) { actual.close() }
                invalidated(handle); handle = 0
                check(!checkNotNull(owner).quarantined)
                phase.stage = "reopen"
                val database = File(File(root, "workspace-v1"), "stories.sqlite3")
                directory(checkNotNull(database.parentFile), root); regular(database)
                passive = NativeWorkspace.openLocal(database.path, config.profileBytes()).also { check(it > 0) }
                noPending(passive)
                val retry = recorded(output, "retry-v1.json", native(passive, createCommand))
                creation(retry, false); same(scope, retry.getJSONObject("scope"))
                val restored = recorded(output, "snapshot-reopened-v1.json", native(passive, command("play_snapshot")
                    .put("session", retry.getString("session")).put("scope", scope).put("expected_revision", 0)))
                same(createdSnapshot, restored); noPending(passive)
                phase.stage = "archive"
                val staging = freshDirectory(root, "archive-staging")
                archive = NativeArchive.open(database.path, staging.path).also { check(it > 0) }
                val request = JSONObject().put("story", scope.getString("story")).put("branch", "main").put("expected_revision", 0)
                val prepared = ArchiveNativeWire.prepared(NativeArchive.prepareExport(archive, localUtf8(request.toString())))
                val archiveBytes = NativeArchive.exportBytes(archive, prepared.token)
                output.put("archive-v1.json", archiveBytes)
                val seed = parse(archiveBytes).getJSONObject("payload").getJSONObject("story").getJSONObject("seed")
                val player = seed.getString("player")
                check(createdSnapshot.getJSONObject("player").getString("observer") == player)
                same(seed.getJSONObject("actors").getJSONObject(player), createdSnapshot.getJSONObject("player").getJSONObject("self_state"))
                same(seed.get("profile"), createdSnapshot.get("rules"))
                val inventory = JSONObject()
                val items = seed.getJSONObject("items")
                items.keys().forEach { key -> if (items.getJSONObject(key).getString("owner") == player) inventory.put(key, items.get(key)) }
                same(inventory, createdSnapshot.getJSONObject("inventory"))
                val origin = seed.getJSONObject("initial_world")
                fields(origin, "version", "generation", "reviewed", "accepted", "title")
                check(origin.getInt("version") == 1 && origin.getString("title") == TITLE)
                same(OriginalStoryWire.input(input), origin.getJSONObject("reviewed"))
                same(OriginalStoryWire.proposal(generated.proposal), origin.getJSONObject("accepted"))
                val generation = origin.getJSONObject("generation")
                fields(generation, "input", "proposal", "model_profile", "model_configuration", "provider", "prompt_version", "schema_version", "response", "response_sha256")
                same(OriginalStoryWire.input(input), generation.getJSONObject("input")); same(OriginalStoryWire.proposal(generated.proposal), generation.getJSONObject("proposal"))
                same(phase.profile, generation.getJSONObject("model_configuration"))
                check(generation.getString("model_profile") == checkNotNull(phase.profile).getString("id") && generation.getString("provider") == "local")
                check(generation.getString("prompt_version") == "initial-world-v1" && generation.getString("schema_version") == "initial-world-v1")
                val response = localUtf8(generation.getString("response")); check(response.size in 1..8192)
                check(sha(response) == generation.getString("response_sha256")); same(parse(response), generation.getJSONObject("proposal"))
                NativeArchive.close(archive)
                val archiveClosed = parse(NativeArchive.prepareExport(archive, localUtf8(request.toString())))
                check(archiveClosed.optString("status") == "rejected" && archiveClosed.optString("error") == "InvalidHandle")
                archive = 0
                NativeWorkspace.close(passive); invalidated(passive); passive = 0
                same(sdkBefore, sdkCounts(worker, send, callbacks, statuses))
                closedAuthor(worker.snapshot(), send.snapshot(), callbacks.snapshot(), statuses.snapshot())
                phase.stage = "completed"
            } }
        } catch (_: Throwable) { phase.reason = if (owner?.quarantined == true) "resource_uncertain" else "checks_failed" }
        try { withContext(NonCancellable + Dispatchers.IO) {
            // Do not issue dependent operations against an uncertain SDK/native owner.
            if (owner?.quarantined != true) {
                try {
                    if (archive > 0) NativeArchive.close(archive)
                    if (passive > 0) { NativeWorkspace.close(passive); invalidated(passive) }
                    transport?.let { actual -> withContext(Dispatchers.Main) { actual.close() } }
                    if (handle > 0) invalidated(handle)
                } catch (_: Throwable) { phase.reason = "resource_uncertain" }
            } else phase.reason = "resource_uncertain"
            artifacts?.let { output ->
                if (tracesObserved) {
                    output.put("worker-v2.json", localUtf8(worker.snapshot().json()))
                    output.put("send-v2.json", localUtf8(send.snapshot().json()))
                    output.put("callback-v1.json", localUtf8(callbacks.snapshot().json()))
                    output.put("status-v1.json", localUtf8(statuses.snapshot().json()))
                }
                val proofRaw = localUtf8(phase.json(output).toString())
                writeNew(File(output.root, "proof-v1.json"), proofRaw)
                diagnostics?.finish(proofRaw, responseCapture,
                    phase.reason == "resource_uncertain" || owner?.quarantined == true)
            }
        } } catch (_: Throwable) { fail("Original author proof capture refused") }
        if (phase.reason != null || phase.stage != "completed") fail("Original author probe refused: ${phase.stage}/${phase.reason ?: "checks_failed"}")
    }

    private class SourceCounts(private val file: File, private val pin: BasicFileAttributes) {
        private val claimed = AtomicBoolean()
        val opened = AtomicLong(); val closed = AtomicLong(); val bytes = AtomicLong(); val offMain = AtomicBoolean(true)
        fun open(): InputStream {
            val worker = Looper.myLooper() != Looper.getMainLooper()
            offMain.set(offMain.get() && worker); check(worker)
            check(claimed.compareAndSet(false, true)); unchanged(file, pin)
            val input = Files.newInputStream(file.toPath(), READ, NOFOLLOW_LINKS)
            check(opened.incrementAndGet() == 1L)
            val ended = AtomicBoolean()
            return object : InputStream() {
                override fun read(): Int { val one = ByteArray(1); return if (read(one, 0, 1) < 0) -1 else one[0].toInt() and 255 }
                override fun read(buffer: ByteArray, offset: Int, length: Int): Int {
                    check(!ended.get()); val worker = Looper.myLooper() != Looper.getMainLooper()
                    offMain.set(offMain.get() && worker); check(worker)
                    return input.read(buffer, offset, length).also { if (it > 0) check(bytes.addAndGet(it.toLong()) <= MODEL_BYTES) }
                }
                override fun close() {
                    val worker = Looper.myLooper() != Looper.getMainLooper()
                    offMain.set(offMain.get() && worker); check(worker)
                    check(ended.compareAndSet(false, true)); input.close(); check(closed.incrementAndGet() == 1L); unchanged(file, pin)
                }
            }
        }
        fun json() = JSONObject().put("opened", opened.get()).put("closed", closed.get()).put("bytes", bytes.get()).put("off_main", offMain.get())
    }
    private class ImportProof {
        private val start = SystemClock.elapsedRealtime()
        var stage = "precheck"; var reason: String? = null; var counts: SourceCounts? = null; var accepted: JSONObject? = null
        fun json() = common("original_author_model_import_v1", stage, reason, start)
            .put("model", identity()).put("source_counts", counts?.json() ?: JSONObject().put("opened", JSONObject.NULL)
                .put("closed", JSONObject.NULL).put("bytes", JSONObject.NULL).put("off_main", JSONObject.NULL))
            .put("accepted", accepted ?: JSONObject.NULL)
    }
    private class AuthorProof {
        private val start = SystemClock.elapsedRealtime()
        var stage = "precheck"; var reason: String? = null; var prior: String? = null; var profile: JSONObject? = null
        var job: String? = null; var inputHash: String? = null; var reviewHash: String? = null; var creationId: String? = null
        fun json(output: Artifacts) = common("original_author_model_v1", stage, reason, start)
            .put("prior_import_sha256", prior ?: JSONObject.NULL).put("profile", profile ?: JSONObject.NULL)
            .put("job", job ?: JSONObject.NULL).put("input_sha256", inputHash ?: JSONObject.NULL)
            .put("review_sha256", reviewHash ?: JSONObject.NULL).put("creation_id", creationId ?: JSONObject.NULL)
            .put("records", output.bindings(RECORDS)).put("traces", output.bindings(TRACES))
    }
    private class Artifacts(val root: File) {
        private val saved = mutableMapOf<String, JSONObject>()
        private var total = 0L
        fun put(name: String, raw: ByteArray) {
            check(name in RECORDS + TRACES && name !in saved && raw.size in 1..ARTIFACT_CAP)
            check(total + raw.size <= 2L * ARTIFACT_CAP)
            writeNew(File(root, name), raw); total += raw.size
            saved[name] = JSONObject().put("bytes", raw.size).put("sha256", sha(raw))
        }
        fun bindings(names: List<String>) = JSONObject().also { result -> names.forEach { result.put(it, saved[it] ?: JSONObject.NULL) } }
    }

    /** Private synthetic evidence only. No response is logged or used to decide a world outcome. */
    private class DiagnosticArtifacts(val root: File) {
        private val saved = mutableMapOf<String, JSONObject>()
        private var total = 0L
        var conserved = false
        fun put(name: String, raw: ByteArray) {
            check(name in DIAGNOSTIC_FILES && name !in saved)
            val cap = when (name) { "input-v1.json" -> 4096; "response-v1.bin" -> 8192; else -> 262144 }
            check(raw.size in 1..cap && total + raw.size <= ARTIFACT_CAP)
            writeNew(File(root, name), raw); total += raw.size
            saved[name] = JSONObject().put("bytes", raw.size).put("sha256", sha(raw))
        }
        fun finish(proofRaw: ByteArray, capture: AuthorResponseCapture?, uncertain: Boolean) {
            val snapshot = capture?.snapshot()
            snapshot?.responseBytes()?.let { put("response-v1.bin", it) }
            val state: Any = when (snapshot?.state) {
                AuthorResponseCaptureState.EMPTY -> "empty"
                AuthorResponseCaptureState.RECORDED -> "recorded"
                AuthorResponseCaptureState.DUPLICATE -> "duplicate"
                AuthorResponseCaptureState.INVALID -> "invalid"
                null -> JSONObject.NULL
            }
            val complete = !uncertain && conserved && state == "recorded" && snapshot?.calls == 1 &&
                saved.keys == DIAGNOSTIC_FILES.toSet() && saved["input-v1.json"]?.getString("sha256") == INPUT_SHA256
            val value = JSONObject().put("version", 1).put("scope", "original_author_diagnostic_v1")
                .put("status", if (complete) "completed" else "refused")
                .put("reason", if (complete) JSONObject.NULL else if (uncertain) "resource_uncertain" else "checks_failed")
                .put("feature_acceptance", false).put("input_sha256", saved["input-v1.json"]?.getString("sha256") ?: JSONObject.NULL)
                .put("author_proof_sha256", sha(proofRaw))
                .put("capture", JSONObject().put("state", state).put("calls", snapshot?.calls ?: JSONObject.NULL)
                    .put("response", saved["response-v1.bin"] ?: JSONObject.NULL))
                .put("files", JSONObject().also { files -> DIAGNOSTIC_FILES.forEach { files.put(it, saved[it] ?: JSONObject.NULL) } })
            val raw = localUtf8(value.toString()); check(raw.size <= 32768)
            writeNew(File(root, "diagnostic-v1.json"), raw)
        }
    }

    companion object {
        private const val PACKAGE = "org.locallore.app.litertverify"
        private const val SOURCE_ROOT = "original-author-source-v1"
        private const val IMPORT_ROOT = "original-author-import-proof-v1"
        private const val AUTHOR_ROOT = "original-author-proof-v1"
        private const val DIAGNOSTIC_ROOT = "original-author-diagnostic-v1"
        private const val INPUT_SHA256 = "1180137865b47041f2827df2e5aac05bc8170b740da49970105648a191b37abb"
        private const val MODEL_BYTES = 2_588_147_712L
        private const val RESERVE = 2L * 1_073_741_824
        private const val PHASE_MS = 180_000L
        private const val ARTIFACT_CAP = 1_048_576
        private const val CREATION_ID = "ea4a25cdca2f4d6491820bf8a0176d31"
        private const val TITLE = "SYNTHETIC Island weather note"
        private val RECORDS = listOf("input-v1.json", "begin-v1.json", "generated-v1.json", "review-v1.json", "create-v1.json", "retry-v1.json",
            "workspace-before-v1.json", "workspace-generated-v1.json", "workspace-reviewed-v1.json", "workspace-created-v1.json", "snapshot-created-v1.json", "snapshot-reopened-v1.json", "archive-v1.json")
        private val TRACES = listOf("worker-v2.json", "send-v2.json", "callback-v1.json", "status-v1.json")
        private val DIAGNOSTIC_FILES = listOf("input-v1.json", "response-v1.bin", "generated-v1.json", "workspace-before-v1.json", "workspace-after-v1.json")
        private fun fixture() = OriginalInput("At a tiny island lantern hut, Eira asks keeper Tavi for a weather note. A single room, a brief shared fact, no possessions, and no beliefs are enough.",
            "Eira", "An island visitor.", listOf(OriginalCast("Tavi", "A quiet lantern keeper.")), "narrative_v1", StoryPresentation("plain", emptyList()))
        private fun selected(method: String): Context {
            check(InstrumentationRegistry.getArguments().getString("class") == "${OriginalAuthorModelInstrumentedTest::class.java.name}#$method")
            val context = InstrumentationRegistry.getInstrumentation().targetContext.applicationContext
            check(BuildConfig.DEBUG && !BuildConfig.MODEL_RECEIPT_VERIFICATION && !BuildConfig.MODEL_VOLUME_VERIFICATION && !BuildConfig.PHYSICAL_MODEL_VERIFICATION && !BuildConfig.INPUT_PROCESS_VERIFICATION)
            check(context.packageName == PACKAGE && context.applicationInfo.uid == Process.myUid())
            check(CandidateLocalModel.identity.bytes == MODEL_BYTES && CandidateLocalModel.identity.sha256 == CandidateLocalModel.MODEL_SHA256)
            return context
        }
        private fun identity() = JSONObject().put("bytes", MODEL_BYTES).put("sha256", CandidateLocalModel.MODEL_SHA256)
        private fun common(scope: String, stage: String, reason: String?, start: Long) = JSONObject().put("version", 1).put("scope", scope)
            .put("status", if (reason == null && stage == "completed") "completed" else "refused").put("stage", stage).put("reason", reason ?: JSONObject.NULL)
            .put("process", JSONObject().put("pid", Process.myPid()).put("uid", Process.myUid()).put("start_elapsed_ms", Process.getStartElapsedRealtime()))
            .put("package", PACKAGE).put("elapsed_ms", SystemClock.elapsedRealtime() - start)
        private fun anchor(context: Context) = context.noBackupFilesDir.canonicalFile.also { directory(it); check(Os.lstat(it.path).st_uid == context.applicationInfo.uid) }
        private fun exists(file: File) = Files.exists(file.toPath(), NOFOLLOW_LINKS)
        private fun directory(file: File, parent: File? = null) {
            check(file.isAbsolute && file.canonicalFile == file && file.toPath().normalize() == file.toPath())
            var p = file.toPath()
            while (true) { check(Files.isDirectory(p, NOFOLLOW_LINKS) && !Files.isSymbolicLink(p)); p = p.parent ?: break }
            val stat = Os.lstat(file.path); check(stat.st_uid == Process.myUid())
            parent?.let { check(file.parentFile == it && stat.st_dev == Os.lstat(it.path).st_dev) }
        }
        private fun freshDirectory(parent: File, name: String): File = File(parent, name).also { check(!exists(it)); Files.createDirectory(it.toPath()); directory(it, parent) }
        private fun regular(file: File, size: Long? = null): BasicFileAttributes {
            directory(checkNotNull(file.parentFile))
            check(file.canonicalFile == file)
            val attrs = Files.readAttributes(file.toPath(), BasicFileAttributes::class.java, NOFOLLOW_LINKS)
            val stat = Os.lstat(file.path)
            check(attrs.isRegularFile && !attrs.isSymbolicLink && attrs.fileKey() != null && (size == null || attrs.size() == size))
            check(stat.st_uid == Process.myUid() && stat.st_dev == Os.lstat(checkNotNull(file.parentFile).path).st_dev)
            return attrs
        }
        private fun unchanged(file: File, before: BasicFileAttributes) { val after = regular(file, before.size()); check(before.fileKey() == after.fileKey() && before.lastModifiedTime() == after.lastModifiedTime()) }
        private fun entries(root: File, names: Set<String>) = Files.newDirectoryStream(root.toPath()).use { check(it.map { p -> p.fileName.toString() }.toSet() == names) }
        private fun resources(context: Context, root: File, missingBytes: Long, memory: Boolean = true) {
            check(Looper.myLooper() != Looper.getMainLooper())
            check(root.usableSpace >= missingBytes + RESERVE)
            if (memory) {
                val info = ActivityManager.MemoryInfo()
                checkNotNull(context.getSystemService(ActivityManager::class.java)).getMemoryInfo(info)
                check(!info.lowMemory && info.availMem >= 4L * 1_073_741_824)
            }
        }
        private fun read(file: File, cap: Int): ByteArray {
            val before = regular(file); check(before.size() in 1..cap.toLong())
            val raw = ByteArray(cap + 1); var count = 0
            Files.newInputStream(file.toPath(), READ, NOFOLLOW_LINKS).use { input ->
                while (count < raw.size) { val n = input.read(raw, count, raw.size - count); if (n < 0) break; check(n > 0); count += n }
            }
            check(count <= cap && count.toLong() == before.size()); unchanged(file, before); return raw.copyOf(count)
        }
        private fun writeNew(file: File, raw: ByteArray) {
            directory(checkNotNull(file.parentFile)); check(raw.size <= ARTIFACT_CAP)
            FileChannel.open(file.toPath(), CREATE_NEW, WRITE, NOFOLLOW_LINKS).use { channel ->
                val buffer = ByteBuffer.wrap(raw); while (buffer.hasRemaining()) check(channel.write(buffer) > 0); channel.force(true)
            }
            regular(file, raw.size.toLong())
        }
        private fun sha(raw: ByteArray) = MessageDigest.getInstance("SHA-256").digest(raw).joinToString("") { "%02x".format(it) }
        private fun parse(raw: ByteArray): JSONObject { val parser = JSONTokener(localText(raw, ARTIFACT_CAP)); return (parser.nextValue() as JSONObject).also { check(parser.nextClean() == '\u0000') } }
        private fun fields(value: JSONObject, vararg names: String) { check(value.keys().asSequence().toSet() == names.toSet()) }
        private fun command(op: String) = JSONObject().put("op", op)
        private fun data(reply: JSONObject): JSONObject { fields(reply, "version", "status", "data"); check(reply.getInt("version") == 1 && reply.getString("status") == "ok"); return reply.getJSONObject("data") }
        private suspend fun recorded(output: Artifacts, transport: NativeWorkspaceTransport, name: String, command: JSONObject): JSONObject = recorded(output, name, transport.exchange(command))
        private fun recorded(output: Artifacts, name: String, reply: JSONObject): JSONObject { output.put(name, localUtf8(reply.toString())); return data(reply) }
        private fun native(handle: Long, command: JSONObject) = parse(NativeWorkspace.call(handle, localUtf8(JSONObject().put("version", 1).put("command", command).toString())))
        private fun creation(value: JSONObject, created: Boolean) {
            fields(value, "session", "scope", "revision", "created"); check(value.getBoolean("created") == created && value.getLong("revision") == 0L)
            val scope = value.getJSONObject("scope"); fields(scope, "story", "branch"); check(scope.getString("story") == "original-$CREATION_ID" && scope.getString("branch") == "main")
        }
        private fun snapshot(value: JSONObject, scope: JSONObject) {
            fields(value, "scope", "revision", "rules", "player", "inventory", "receipts"); same(scope, value.getJSONObject("scope"))
            check(value.getLong("revision") == 0L && value.getJSONArray("receipts").length() == 0)
            check(value.getJSONObject("player").getJSONObject("self_state").getString("name") == "Eira")
        }
        private fun noPending(handle: Long) { val reply = data(parse(NativeWorkspace.pollInference(handle))); fields(reply, "pending"); check(reply.isNull("pending")) }
        private suspend fun invalidated(handle: Long) = withTimeout(5_000) {
            while (true) { val reply = native(handle, command("workspace")); if (reply.optString("error") == "InvalidHandle") break; delay(10) }
        }
        private fun sdkCounts(worker: LiteRtWorkerTrace, send: LiteRtSendTrace, callback: LiteRtCallbackTrace, status: LiteRtStatusTrace): JSONObject {
            val w = JSONObject(worker.snapshot().json()); val s = JSONObject(send.snapshot().json())
            return JSONObject().put("worker", w.getJSONObject("counts")).put("creations", w.getJSONArray("creations"))
                .put("send", s.getJSONObject("counts")).put("formats", s.getJSONObject("format_counts"))
                .put("callback", JSONObject(callback.snapshot().json())).put("status", JSONObject(status.snapshot().json()))
        }
        private fun closedAuthor(worker: LiteRtWorkerSnapshot, send: LiteRtSendSnapshot, callback: LiteRtCallbackSnapshot, status: LiteRtStatusSnapshot) {
            check(worker.saturated.isEmpty() && !worker.timeSaturated && !worker.creationsSaturated && worker.creationsTotal == 1)
            check(worker.creations.single().let { it.role == LiteRtTraceRole.AUTHOR && it.returnedMs != null && it.failedMs == null && it.failure == LiteRtTraceFailure.NONE })
            for (event in listOf(LiteRtWorkerEvent.ENGINE_CREATE_RETURNED, LiteRtWorkerEvent.INITIALIZE_RETURNED, LiteRtWorkerEvent.CONVERSATION_CREATE_RETURNED,
                LiteRtWorkerEvent.SEND_RETURNED, LiteRtWorkerEvent.DONE_RETURNED, LiteRtWorkerEvent.CONVERSATION_CLOSE_KNOWN, LiteRtWorkerEvent.ENGINE_CLOSE_KNOWN)) check(worker.counts.getValue(event) == 1)
            check(worker.counts.getValue(LiteRtWorkerEvent.DRAIN_SETTLED) >= 1)
            for (event in listOf(LiteRtWorkerEvent.UNCERTAIN, LiteRtWorkerEvent.ERROR_ENTERED, LiteRtWorkerEvent.CANCEL_ENTERED)) check(worker.counts.getValue(event) == 0)
            check(send.saturated.isEmpty() && send.formatSaturated.isEmpty() && !send.timeSaturated)
            check(send.counts.getValue(LiteRtSendEvent.ASYNC_CALL_RETURNED) == 1 && send.counts.getValue(LiteRtSendEvent.ARGUMENTS_RETURNED) == 1)
            check(send.counts.getValue(LiteRtSendEvent.ASYNC_CALL_THROWN) == 0 && send.counts.getValue(LiteRtSendEvent.ARGUMENTS_THROWN) == 0)
            check(send.lastFormat == LiteRtSendFormat.JSON_OBJECT && send.formatCounts.getValue(LiteRtSendFormat.JSON_OBJECT) == 1 && send.formatCounts.getValue(LiteRtSendFormat.REGEX) == 0)
            check(callback.requests == 1 && !callback.requestsSaturated)
            val call = callback.calls.single(); check(call.role == LiteRtCallbackRole.AUTHOR && call.contextTokens == 4096 && call.maxOutputTokens == 1024 && call.saturated.isEmpty())
            check(call.counts.getValue(LiteRtCallbackCounter.OUTPUT_BYTES) in 1..8192 && call.counts.getValue(LiteRtCallbackCounter.OUTPUT_CHUNKS) > 0 && call.counts.getValue(LiteRtCallbackCounter.DONE) == 1)
            for (counter in listOf(LiteRtCallbackCounter.CANCELLED, LiteRtCallbackCounter.SDK_JNI, LiteRtCallbackCounter.OTHER)) check(call.counts.getValue(counter) == 0)
            check(status.saturated.isEmpty() && status.counts.values.all { it == 0 })
        }
        private fun same(expected: Any?, actual: Any?) {
            when (expected) {
                is JSONObject -> { check(actual is JSONObject); check(expected.keys().asSequence().toSet() == actual.keys().asSequence().toSet()); expected.keys().forEach { same(expected.get(it), actual.get(it)) } }
                is JSONArray -> { check(actual is JSONArray && expected.length() == actual.length()); for (i in 0 until expected.length()) same(expected.get(i), actual.get(i)) }
                is Number -> check(expected.toString() == actual.toString())
                else -> check(expected == actual)
            }
        }
    }
}

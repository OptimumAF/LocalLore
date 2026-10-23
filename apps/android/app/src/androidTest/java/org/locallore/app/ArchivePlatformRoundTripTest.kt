/* Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0 */
package org.locallore.app

import android.os.Looper
import androidx.test.ext.junit.runners.AndroidJUnit4
import androidx.test.platform.app.InstrumentationRegistry
import java.io.Closeable
import java.io.File
import java.io.InputStream
import java.io.ByteArrayOutputStream
import java.nio.file.Files
import java.nio.file.LinkOption
import java.nio.file.StandardOpenOption
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.runBlocking
import kotlinx.coroutines.withContext
import org.json.JSONArray
import org.json.JSONObject
import org.junit.Test
import org.junit.runner.RunWith

/** Synthetic JNI platform transfer only: no model, chooser, default workspace, or fixture deletion. */
@RunWith(AndroidJUnit4::class)
class ArchivePlatformRoundTripTest {
    private val fixture = "locallore-platform-roundtrip-v1"
    private val cap = 128 * 1024
    private val windowsStory = "platform-windows-v1"
    private val branches = listOf("main", "child", "sibling")

    @Test fun platformRoundTrip(): Unit {
        try {
            runBlocking {
                withContext(Dispatchers.IO) {
                    verify(Looper.myLooper() != Looper.getMainLooper(), "JNI must run on IO")
                    val args = InstrumentationRegistry.getArguments()
                    val phase = args.getString("platform_phase")
                    val run = args.getString("platform_run")
                    verify(phase == "outbound" || phase == "return", "Invalid platform phase")
                    verify(run != null && Regex("[a-z0-9-]{1,48}").matches(run), "Invalid platform run")
                    val root = ownedRun(requireNotNull(run), phase == "outbound")
                    if (phase == "outbound") outbound(root) else returned(root)
                }
            }
        } catch (failure: AssertionError) { throw failure }
        catch (_: Exception) {
            // Filesystem/JSON exception messages may contain private paths or payload text.
            throw AssertionError("Platform round-trip boundary failed")
        }
    }

    private fun outbound(root: File): Unit {
        val origin = asset("windows-origin.json")
        val continued = asset("windows-continued.json")
        verify(!origin.toString(Charsets.UTF_8).contains("EXCLUDED_PLATFORM_DRAFT"), "Source noncommitted draft must not transfer")
        val manifest = JSONObject(asset("expectations.json").toString(Charsets.UTF_8))
        verify(manifest.getInt("version") == 1 && manifest.getString("fixture") == fixture, "Fixture manifest mismatch")
        val expected = manifest.getJSONObject("windows")
        verify(expected.getString("story") == windowsStory && expected.getString("root") == "main" &&
            expected.getString("continuation_branch") == "sibling" &&
            expected.getString("continuation_turn") == "android-transfer-gift-v1", "Fixture scope mismatch")
        verify(expected.getJSONObject("branch_heads").keys().asSequence().toSet() == branches.toSet(), "Fixture branch set mismatch")
        branches.forEach { verify(expected.getJSONObject("branch_heads").getLong(it) == 2L, "Fixture head mismatch") }

        Workspace(newDirectory(root, "windows-workspace")).use { workspace ->
            val prepared = workspace.prepareImport(origin)
            verify(workspace.library().length() == 0, "Preview must not import into the library")
            val preview = prepared.getJSONObject("preview")
            verify(preview.getString("story_id") == windowsStory && preview.getInt("committed_turns") == 4,
                "Imported preview does not describe the golden history")
            workspace.commitImport(prepared)
            workspace.reopen()
            val library = workspace.library()
            // The existing workspace catalog lists story roots, not every branch.
            // Per-branch snapshots below and archive heads verify all timelines.
            verify(library.length() == 1, "The original story root must be imported once")
            verify((0 until library.length()).all { library.getJSONObject(it).getInt("drafts") == 0 },
                "Imported timelines must not resume source noncommitted work")
            compareSnapshots(workspace, expected.getJSONObject("snapshots"))
            val returned = workspace.export(scope(windowsStory, "main"), 2)
            verify(matchesHistoricalArchive(returned, origin), "Windows origin history changed after Android reopen")
            writeNew(root, "windows-return.json", returned)

            val sibling = scope(windowsStory, "sibling")
            val request = request(sibling, "android-transfer-gift-v1", 2, gift())
            workspace.session(sibling) { session ->
                workspace.commit(session, request)
                workspace.exactRetry(session, request, 3)
                workspace.duplicateGift(session, sibling, 3, "android-duplicate-gift-v1")
            }
            workspace.reopen()
            compareSnapshots(workspace, expected.getJSONObject("continued_snapshots"))
            val bytes = workspace.export(sibling, 3)
            verify(matchesHistoricalArchive(bytes, continued), "Android continuation differs from Windows golden history")
            writeNew(root, "windows-continued.json", bytes)
        }

        Workspace(newDirectory(root, "android-origin-workspace")).use { workspace ->
            val created = workspace.ok(command("create").put("seed", "lantern-quay-v1"))
            val originScope = created.getJSONObject("scope")
            verify(originScope.getString("story").isNotBlank() && originScope.getString("story") != windowsStory &&
                originScope.getString("branch") == "main" && created.getLong("revision") == 0L,
                "Host must create an independent original story")
            verify(workspace.library().getJSONObject(0).getString("title") == "Lantern Quay", "Original Host seed title mismatch")
            val session = created.getString("session")
            try {
                val request = request(originScope, "android-origin-gift-v1", 0, gift())
                workspace.commit(session, request)
                workspace.exactRetry(session, request, 1)
                workspace.duplicateGift(session, originScope, 1, "android-origin-duplicate-v1")
            } finally { workspace.closeSession(session, originScope) }
            val before = workspace.snapshot(originScope, 1)
            workspace.reopen()
            verify(sameJson(before, workspace.snapshot(originScope, 1)), "Android origin changed across reopen")
            writeNew(root, "android-origin.json", workspace.export(originScope, 1))
        }
    }

    private fun returned(root: File): Unit {
        val bytes = readFixture(File(root, "android-return.json"))
        val originalStory = JSONObject(readFixture(File(root, "android-origin.json")).toString(Charsets.UTF_8))
            .getJSONObject("payload").getJSONObject("story")
        val returnedStory = JSONObject(bytes.toString(Charsets.UTF_8)).getJSONObject("payload").getJSONObject("story")
        verify(sameJson(originalStory, returnedStory), "Returned story identity and seed must match this run's Android origin")
        Workspace(newDirectory(root, "android-return-workspace")).use { workspace ->
            val prepared = workspace.prepareImport(bytes)
            verify(workspace.library().length() == 0, "Return preview must not import before consent")
            val preview = prepared.getJSONObject("preview")
            val story = preview.getString("story_id")
            verify(story != windowsStory && preview.getString("title") == "Lantern Quay" &&
                preview.getString("root_branch") == "main" && preview.getInt("committed_turns") == 2,
                "Returned origin metadata mismatch")
            val originScope = scope(story, "main")
            workspace.commitImport(prepared)
            workspace.reopen()
            verify(workspace.library().length() == 1, "Returned origin must have one timeline")
            verify(workspace.export(originScope, 2).contentEquals(bytes), "Returned bytes changed after Android reopen")
            val before = workspace.snapshot(originScope, 2)
            val receipts = before.getJSONArray("receipts")
            verify(receipts.length() == 2, "Returned origin must retain both accepted receipts")
            val matches = (0 until receipts.length()).map { receipts.getJSONObject(it).getJSONObject("request") }
                .filter { it.getString("turn") == "windows-return-wait-v1" }
            verify(matches.size == 1, "Original Windows continuation receipt is missing")
            val original = matches.single()
            verify(sameJson(original, request(originScope, "windows-return-wait-v1", 1, waitOne())),
                "Original Windows continuation request changed")
            workspace.session(originScope) { session ->
                workspace.exactRetry(session, original, 2)
                workspace.duplicateGift(session, originScope, 2, "android-return-duplicate-v1")
                val final = request(originScope, "android-final-wait-v1", 2, waitOne())
                workspace.commit(session, final)
                workspace.exactRetry(session, final, 3)
            }
            val final = workspace.snapshot(originScope, 3)
            workspace.reopen()
            verify(sameJson(final, workspace.snapshot(originScope, 3)), "Final Android history changed across reopen")
            writeNew(root, "android-final.json", workspace.export(originScope, 3))
        }
    }

    private fun compareSnapshots(workspace: Workspace, expected: JSONObject): Unit {
        verify(expected.keys().asSequence().toSet() == branches.toSet(), "Golden snapshot branch set mismatch")
        branches.forEach { branch ->
            val golden = expected.getJSONObject(branch)
            verify(sameJson(workspace.snapshot(scope(windowsStory, branch), golden.getLong("revision")), golden),
                "Full player snapshot differs from engine-derived golden")
        }
    }

    private inner class Workspace(private val directory: File) : Closeable {
        private val database = File(directory, "stories.sqlite3")
        private val staging = newDirectory(directory, "staging")
        private var host = 0L
        private var archive = 0L
        init { open() }
        private fun open(): Unit {
            verify(host == 0L && archive == 0L, "Native owners must be closed before reopen")
            host = NativeWorkspace.open(database.absolutePath)
            verify(host > 0, "Native workspace did not open")
            try {
                archive = NativeArchive.open(database.absolutePath, staging.absolutePath)
                verify(archive > 0, "Native archive did not open")
            } catch (failure: Throwable) { NativeWorkspace.close(host); host = 0; throw failure }
        }
        fun reopen(): Unit { close(); open() }
        override fun close(): Unit {
            val previousArchive = archive.also { archive = 0 }
            val previousHost = host.also { host = 0 }
            try { if (previousArchive > 0) NativeArchive.close(previousArchive) }
            finally { if (previousHost > 0) NativeWorkspace.close(previousHost) }
            verify(staging.listFiles()?.isEmpty() == true, "Native staging must be empty after close")
        }
        fun reply(command: JSONObject): JSONObject {
            verify(host > 0, "Native workspace owner is closed")
            val input = JSONObject().put("version", 1).put("command", command).toString().toByteArray(Charsets.UTF_8)
            verify(input.size <= 24_576, "Host input exceeds its boundary")
            return envelope(NativeWorkspace.call(host, input))
        }
        fun ok(command: JSONObject): JSONObject = accepted(reply(command))
        fun library(): JSONArray = ok(command("workspace")).getJSONArray("stories")
        fun prepareImport(bytes: ByteArray): JSONObject = accepted(envelope(NativeArchive.prepareImport(archive, bytes)))
        fun commitImport(prepared: JSONObject): Unit {
            accepted(envelope(NativeArchive.commitImport(archive, prepared.getLong("token"))))
            verify(staging.listFiles()?.isEmpty() == true, "Import must drain its staging files")
        }
        fun export(scope: JSONObject, head: Long): ByteArray {
            val control = JSONObject().put("story", scope.getString("story")).put("branch", scope.getString("branch"))
                .put("expected_revision", head).toString().toByteArray(Charsets.UTF_8)
            val prepared = accepted(envelope(NativeArchive.prepareExport(archive, control)))
            verify(!prepared.getJSONObject("preview").getBoolean("noncommitted_workflow_transferred"),
                "Noncommitted workflow must not transfer")
            val output = NativeArchive.exportBytes(archive, prepared.getLong("token"))
            verify(output.size in 1..cap, "Fixture export exceeds its proof bound")
            verify(staging.listFiles()?.isEmpty() == true, "Export must drain its staging files")
            return output
        }
        fun <T> session(scope: JSONObject, block: (String) -> T): T {
            val session = ok(command("resume").put("scope", scope)).getString("session")
            try { return block(session) } finally { closeSession(session, scope) }
        }
        fun closeSession(session: String, scope: JSONObject): Unit {
            ok(scoped("close", session, scope))
        }
        private fun snapshot(session: String, scope: JSONObject, head: Long): JSONObject =
            ok(scoped("play_snapshot", session, scope).put("expected_revision", head))
        fun snapshot(scope: JSONObject, head: Long): JSONObject = session(scope) { session ->
            val snapshot = snapshot(session, scope, head)
            for (observer in listOf("mira", "sable", "omniscient")) {
                val reply = reply(scoped("inspect", session, scope).put("observer", observer).put("expected_revision", head))
                verify(reply.getString("status") == "rejected" && reply.getString("error") == "Forbidden",
                    "Non-Lab Host must reject nonplayer inspection")
            }
            snapshot
        }
        fun commit(session: String, request: JSONObject): JSONObject {
            val submitted = submit(session, request)
            verify(submitted.getString("phase") == "queued", "New typed turn must be queued")
            val scope = request.getJSONObject("scope")
            val turn = request.getString("turn")
            verify(ok(scoped("prepare", session, scope).put("turn", turn)).getString("phase") == "ready",
                "Actual fake inference must prepare the typed turn")
            val result = ok(scoped("commit", session, scope).put("turn", turn))
            verify(result.getString("phase") == "committed" && sameJson(result.getJSONObject("receipt").getJSONObject("request"), request),
                "Committed receipt must preserve the exact original request")
            return result
        }
        private fun submit(session: String, request: JSONObject): JSONObject =
            ok(command("submit").put("session", session).put("request", request).put("mode", "accepted"))
        fun exactRetry(session: String, request: JSONObject, head: Long): Unit {
            val scope = request.getJSONObject("scope")
            val before = snapshot(session, scope, head)
            val submitted = submit(session, request)
            verify(submitted.getString("phase") == "committed", "Exact retry must return its accepted receipt")
            verify(sameJson(submitted.getJSONObject("receipt").getJSONObject("request"), request), "Retry request must stay exact")
            val committed = ok(scoped("commit", session, scope).put("turn", request.getString("turn")))
            verify(sameJson(submitted, committed), "Exact retry commit must return the same outcome")
            verify(sameJson(before, snapshot(session, scope, head)), "Exact retry must not mutate canon")
        }
        fun duplicateGift(session: String, scope: JSONObject, head: Long, turn: String): Unit {
            val before = snapshot(session, scope, head)
            val reply = reply(command("submit").put("session", session).put("mode", "accepted")
                .put("request", request(scope, turn, head, gift())))
            verify(reply.getString("status") == "rejected" && reply.getString("error") == "Inventory",
                "New-key duplicate spend must reject as Inventory")
            verify(sameJson(before, snapshot(session, scope, head)), "Rejected duplicate spend must not mutate canon")
        }
    }

    private fun command(op: String) = JSONObject().put("op", op)
    private fun scope(story: String, branch: String) = JSONObject().put("story", story).put("branch", branch)
    private fun scoped(op: String, session: String, scope: JSONObject) = command(op).put("session", session).put("scope", scope)
    private fun gift() = command("give").put("item", "potion").put("to", "mira").put("quantity", 1)
    private fun waitOne() = command("wait").put("ticks", 1)
    private fun request(scope: JSONObject, turn: String, head: Long, action: JSONObject) = JSONObject()
        .put("version", 1).put("scope", scope).put("turn", turn).put("expected_revision", head)
        .put("intent", JSONObject().put("kind", "actions").put("value", JSONArray().put(action)))
    private fun envelope(bytes: ByteArray): JSONObject {
        verify(bytes.size in 1..262_144, "Native reply exceeds its boundary")
        return JSONObject(bytes.toString(Charsets.UTF_8)).also { verify(it.getInt("version") == 1, "Native protocol version mismatch") }
    }
    private fun accepted(reply: JSONObject): JSONObject {
        verify(reply.getString("status") == "ok", "Native operation did not accept the fixture")
        return reply.getJSONObject("data")
    }

    private fun ownedRun(run: String, fresh: Boolean): File {
        // Normalize Android's trusted per-user app-directory alias before constructing owned children.
        val noBackup = InstrumentationRegistry.getInstrumentation().targetContext.noBackupFilesDir.canonicalFile
        realDirectory(noBackup)
        val base = File(noBackup, "platform-roundtrip")
        if (!Files.exists(base.toPath(), LinkOption.NOFOLLOW_LINKS)) Files.createDirectory(base.toPath())
        realDirectory(base)
        val root = File(base, run)
        if (fresh) {
            Files.createDirectory(root.toPath())
            writeNew(root, "owner-v1", fixture.toByteArray(Charsets.US_ASCII))
        }
        realDirectory(root)
        verify(readFixture(File(root, "owner-v1")).contentEquals(fixture.toByteArray(Charsets.US_ASCII)), "Run ownership marker mismatch")
        return root
    }
    private fun newDirectory(parent: File, name: String): File = File(parent, name).also {
        Files.createDirectory(it.toPath()); realDirectory(it)
    }
    private fun realDirectory(directory: File): Unit {
        verify(Files.isDirectory(directory.toPath(), LinkOption.NOFOLLOW_LINKS) && !Files.isSymbolicLink(directory.toPath()) &&
            directory.absoluteFile == directory.canonicalFile, "Fixture directory must be real and nonlinked")
    }
    private fun writeNew(root: File, name: String, bytes: ByteArray): Unit {
        verify(name in setOf("owner-v1", "windows-return.json", "windows-continued.json", "android-origin.json", "android-final.json"),
            "Unsupported fixture output name")
        verify(bytes.size in 1..cap, "Fixture output exceeds its bound")
        Files.newOutputStream(File(root, name).toPath(), StandardOpenOption.CREATE_NEW, StandardOpenOption.WRITE).use { it.write(bytes) }
    }
    private fun readFixture(file: File): ByteArray {
        verify(Files.isRegularFile(file.toPath(), LinkOption.NOFOLLOW_LINKS) && !Files.isSymbolicLink(file.toPath()) &&
            file.absoluteFile == file.canonicalFile, "Fixture input must be a regular nonlink")
        return file.inputStream().use(::bounded)
    }
    private fun asset(name: String): ByteArray = InstrumentationRegistry.getInstrumentation().context.assets
        .open("platform-roundtrip-v1/$name").use(::bounded)
    private fun bounded(input: InputStream): ByteArray {
        val output = ByteArrayOutputStream()
        val buffer = ByteArray(8192)
        while (output.size() < cap) {
            val count = input.read(buffer, 0, minOf(buffer.size, cap - output.size()))
            if (count < 0) break
            if (count == 0) {
                val one = input.read()
                if (one < 0) break
                output.write(one)
            } else output.write(buffer, 0, count)
        }
        verify(input.read() == -1 && output.size() > 0, "Fixture input exceeds its bound or is empty")
        return output.toByteArray()
    }
    private fun matchesHistoricalArchive(currentBytes: ByteArray, historicalBytes: ByteArray): Boolean {
        // Static schema2/v1 assets remain compatibility inputs. Rust validates their import
        // and validates current exports. Only source schema and its payload digest may differ.
        val current = JSONObject(currentBytes.toString(Charsets.UTF_8))
        val historical = JSONObject(historicalBytes.toString(Charsets.UTF_8))
        verify(current.getInt("version") == 1 && historical.getInt("version") == 1, "Archive version drift")
        verify(current.getJSONObject("payload").getInt("source_database_schema_version") == 3 &&
            historical.getJSONObject("payload").getInt("source_database_schema_version") == 2, "Source schema drift")
        historical.getJSONObject("payload").put("source_database_schema_version", 3)
        historical.getJSONObject("integrity").put("payload_sha256", current.getJSONObject("integrity").getString("payload_sha256"))
        return sameJson(current, historical)
    }
    private fun sameJson(left: Any?, right: Any?): Boolean = when {
        left is JSONObject && right is JSONObject -> {
            val keys = left.keys().asSequence().toSet()
            keys == right.keys().asSequence().toSet() && keys.all { sameJson(left.get(it), right.get(it)) }
        }
        left is JSONArray && right is JSONArray -> left.length() == right.length() &&
            (0 until left.length()).all { sameJson(left.get(it), right.get(it)) }
        left is Number && right is Number -> left.toString() == right.toString()
        else -> left == right
    }
    private fun verify(condition: Boolean, message: String): Unit { if (!condition) throw AssertionError(message) }
}

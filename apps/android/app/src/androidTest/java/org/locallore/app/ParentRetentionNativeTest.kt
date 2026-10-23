/* Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0 */
package org.locallore.app

import androidx.test.platform.app.InstrumentationRegistry
import java.io.File
import java.util.UUID
import java.util.concurrent.Executors
import java.util.concurrent.TimeUnit
import org.json.JSONObject
import org.junit.Assert.*
import org.junit.Test

/** Actual JNI workers and Store deletion; the configured provider is explicitly synthetic. */
class ParentRetentionNativeTest {
    @Test fun deletionDuringObservedParentAndChildGenerationFencesOnlyParent() {
        val instrumentation = InstrumentationRegistry.getInstrumentation()
        assertEquals("org.locallore.app.parentverify", instrumentation.targetContext.packageName)
        val directory = File(instrumentation.targetContext.noBackupFilesDir, "retention-running-${UUID.randomUUID()}")
            .also { check(it.mkdir()) }
        val database = File(directory, "stories.sqlite3")
        val staging = File(directory, "staging").also { check(it.mkdir()) }
        var handle = 0L
        var archive = 0L
        val pool = Executors.newFixedThreadPool(2)
        var primary: Throwable? = null
        fun scope(branch: String) = JSONObject().put("story", "parent-retention-fixture").put("branch", branch)
        fun call(command: JSONObject) = JSONObject(NativeWorkspace.call(handle,
            JSONObject().put("version", 1).put("command", command).toString().toByteArray(Charsets.UTF_8)).toString(Charsets.UTF_8))
        fun data(reply: JSONObject): JSONObject { assertEquals("ok", reply.getString("status")); return reply.getJSONObject("data") }
        fun accepted(bytes: ByteArray) = data(JSONObject(bytes.toString(Charsets.UTF_8)))
        fun session(branch: String) = data(call(JSONObject().put("op", "resume").put("scope", scope(branch)))).getString("session")
        fun turn(op: String, session: String, branch: String) = JSONObject().put("op", op).put("session", session)
            .put("scope", scope(branch)).put("turn", "running-$branch")
        fun snapshot(session: String, branch: String, revision: Int) = data(call(JSONObject().put("op", "play_snapshot")
            .put("session", session).put("scope", scope(branch)).put("expected_revision", revision))).toString()
        try {
            handle = NativeWorkspace.open(database.canonicalPath).also { check(it > 0) }
            archive = NativeArchive.open(database.canonicalPath, staging.canonicalPath).also { check(it > 0) }
            val fixture = instrumentation.context.assets.open("parent-retention-v1.json").use { it.readBytes() }
            val prepared = accepted(NativeArchive.prepareImport(archive, fixture))
            accepted(NativeArchive.commitImport(archive, prepared.getLong("token")))
            val parent = session("parent"); val child = session("child"); val sibling = session("sibling")
            val childBefore = snapshot(child, "child", 4); val siblingBefore = snapshot(sibling, "sibling", 1)
            for ((id, branch, revision) in listOf(Triple(parent, "parent", 5), Triple(child, "child", 4))) {
                val request = JSONObject().put("version", 1).put("scope", scope(branch)).put("turn", "running-$branch")
                    .put("expected_revision", revision).put("intent", JSONObject().put("kind", "free_text")
                        .put("value", JSONObject().put("kind", "action").put("text", "I give my last potion to Mira.")))
                assertEquals("queued", data(call(JSONObject().put("op", "free_text").put("session", id).put("request", request))).getString("phase"))
            }
            val parentWorker = pool.submit<JSONObject> { call(turn("prepare", parent, "parent")) }
            val childWorker = pool.submit<JSONObject> { call(turn("prepare", child, "child")) }
            val deadline = System.nanoTime() + TimeUnit.SECONDS.toNanos(5)
            while (true) {
                val phases = listOf(data(call(turn("turn_status", parent, "parent"))).getString("phase"),
                    data(call(turn("turn_status", child, "child"))).getString("phase"))
                if (phases.all { it == "running" }) break
                check(phases.none { it in setOf("ready", "failed", "cancelled") } && System.nanoTime() < deadline) {
                    "Both actual native workers must overlap deletion"
                }
                Thread.sleep(1)
            }
            val request = JSONObject().put("story", "parent-retention-fixture").put("branch", "parent").put("expected_revision", 5)
            val consent = accepted(NativeArchive.prepareBranchDelete(archive, request.toString().toByteArray(Charsets.UTF_8)))
            assertFalse(parentWorker.isDone); assertFalse(childWorker.isDone)
            assertEquals("running", data(call(turn("turn_status", parent, "parent"))).getString("phase"))
            assertEquals("running", data(call(turn("turn_status", child, "child"))).getString("phase"))
            val deleted = accepted(NativeArchive.commitBranchDelete(archive, consent.getLong("token")))
            assertEquals(4, deleted.getInt("retained_through_revision"))
            assertEquals("Closed", parentWorker.get(10, TimeUnit.SECONDS).getString("error"))
            assertEquals("ready", data(childWorker.get(10, TimeUnit.SECONDS)).getString("phase"))
            assertEquals(childBefore, snapshot(child, "child", 4)); assertEquals(siblingBefore, snapshot(sibling, "sibling", 1))
            val commit = turn("commit", child, "child")
            val receipt = data(call(commit)).toString()
            assertEquals("committed", JSONObject(receipt).getString("phase"))
            assertEquals(receipt, data(call(commit)).toString())
            assertEquals("NotFound", call(JSONObject().put("op", "resume").put("scope", scope("parent"))).getString("error"))
        } catch (failure: Throwable) { primary = failure; throw failure }
        finally {
            var cleanupFailure: Throwable? = null
            fun cleanup(action: () -> Unit) {
                try { action() } catch (failure: Throwable) {
                    val previous = cleanupFailure
                    if (previous == null) cleanupFailure = failure else previous.addSuppressed(failure)
                }
            }
            cleanup { if (handle > 0) NativeWorkspace.close(handle) }
            var drained = false
            cleanup {
                pool.shutdown(); drained = pool.awaitTermination(10, TimeUnit.SECONDS)
                check(drained) { "Native worker ownership did not drain" }
            }
            // Close the archive even when worker drain or a prior assertion failed.
            cleanup { if (archive > 0) NativeArchive.close(archive) }
            if (drained && handle > 0 && archive > 0) cleanup {
                val workspaces = mutableListOf<Long>(); val archives = mutableListOf<Long>()
                try {
                    repeat(4) { workspaces += NativeWorkspace.open(database.canonicalPath).also { check(it > 0) } }
                    repeat(4) { archives += NativeArchive.open(database.canonicalPath, staging.canonicalPath).also { check(it > 0) } }
                } finally { workspaces.forEach(NativeWorkspace::close); archives.forEach(NativeArchive::close) }
            }
            cleanupFailure?.let { failure -> primary?.addSuppressed(failure) ?: throw failure }
        }
    }
}

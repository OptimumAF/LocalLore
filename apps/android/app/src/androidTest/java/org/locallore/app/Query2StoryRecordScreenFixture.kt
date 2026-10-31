/* Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0 */
package org.locallore.app

import androidx.test.platform.app.InstrumentationRegistry
import java.io.ByteArrayOutputStream
import java.io.File
import java.security.MessageDigest
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.withContext
import org.json.JSONArray
import org.json.JSONObject
import org.junit.Assert.*

/** Genuine synthetic Archive3 input. Rust validates/imports it; Kotlin never constructs history. */
internal class Query2StoryRecordScreenFixture(private val fixture: RecordFixture) {
    private fun asset(name: String): ByteArray = InstrumentationRegistry.getInstrumentation().context.assets.open(name).use { input ->
        val output = ByteArrayOutputStream()
        val block = ByteArray(8192)
        while (true) {
            val count = input.read(block)
            if (count < 0) break
            check(count > 0)
            check(output.size() + count <= 256 * 1024)
            output.write(block, 0, count)
        }
        output.toByteArray()
    }

    private val metadata = JSONObject(asset("query2-corrected-opaque-v1.json").toString(Charsets.UTF_8))
    val player: String = metadata.getString("player")
    val factId: String = metadata.getString("fact_id")
    val oldObservation: String = metadata.getString("old_observation")
    val newObservation: String = metadata.getString("new_observation")
    val correctionRevision: Long = metadata.getLong("correction_revision")
    val forbidden: List<String> = metadata.getJSONArray("forbidden").let { values ->
        (0 until values.length()).map(values::getString)
    }
    private val branches = metadata.getJSONObject("branches")
    lateinit var imported: ArchiveImported
        private set

    init {
        assertEquals(1, metadata.getInt("version"))
        assertTrue(validStoryRecordTurn(player))
        assertNotEquals("player", player)
        assertNotEquals(oldObservation, newObservation)
        assertTrue(forbidden.isNotEmpty() && forbidden.all { it.isNotEmpty() })
    }

    fun branch(role: String): String = branches.getJSONObject(role).getString("branch")
    fun head(role: String): Long = branches.getJSONObject(role).getLong("head")
    fun time(role: String): Long = branches.getJSONObject(role).getLong("story_time")
    fun drill(): StoryRecordScopedEvent {
        val value = metadata.getJSONObject("drill")
        val original = value.getJSONObject("original_scope")
        assertEquals(metadata.getString("story"), original.getString("story"))
        return StoryRecordScopedEvent(StoryRecordScope(imported.story, original.getString("branch")), value.getLong("sequence"))
    }

    suspend fun importArchive() = withContext(Dispatchers.IO) {
        val bytes = asset("query2-corrected-opaque-v1.llore")
        val archive = metadata.getJSONObject("archive")
        assertEquals(archive.getInt("bytes"), bytes.size)
        val hash = MessageDigest.getInstance("SHA-256").digest(bytes).joinToString("") { "%02x".format(it.toInt() and 255) }
        assertEquals(archive.getString("sha256"), hash)
        val workspace = File(fixture.root, "workspace-v1").also { check(it.mkdir()) }
        val staging = File(fixture.root, "query2-import-staging").also { check(it.mkdir()) }
        val database = File(workspace, "stories.sqlite3")
        // ArchiveRegistry requires an existing validated database. Opening the ordinary native
        // workspace initializes its schema; no create/reset/default-story command is issued.
        val initializer = NativeWorkspace.open(database.canonicalPath)
        check(initializer > 0)
        try {
            val envelope = JSONObject().put("version", 1).put("command", JSONObject().put("op", "workspace"))
            val reply = JSONObject(NativeWorkspace.call(initializer, envelope.toString().toByteArray(Charsets.UTF_8)).toString(Charsets.UTF_8))
            assertEquals("ok", reply.getString("status"))
            assertEquals(0, reply.getJSONObject("data").getJSONArray("stories").length())
        } finally { NativeWorkspace.close(initializer) }
        val owner = NativeArchive.open(database.canonicalPath, staging.canonicalPath)
        check(owner > 0)
        try {
            val prepared = ArchiveNativeWire.prepared(NativeArchive.prepareImport(owner, bytes))
            assertEquals(3, prepared.preview.version)
            assertEquals(metadata.getString("story"), prepared.preview.storyId)
            assertEquals(metadata.getString("root_branch"), prepared.preview.rootBranch)
            for (role in listOf("before", "corrected", "rediscovered"))
                assertEquals(head(role), prepared.preview.branchHeads[branch(role)])
            imported = ArchiveNativeWire.imported(NativeArchive.commitImport(owner, prepared.token))
            // The current native import preserves identity. The actual outcome, not an assumed ID,
            // is subsequently used for catalog selection and expected scoped tuples.
            assertEquals(prepared.preview.storyId, imported.story)
            assertEquals(prepared.preview.rootBranch, imported.branch)
            assertTrue(staging.listFiles()!!.isEmpty())
        } finally { NativeArchive.close(owner) }
    }

    suspend fun selectedOwner(role: String): RecordOwner {
        val owner = fixture.owner()
        val library = owner.gateway.initialize()
        val root = library.stories.single { it.story == imported.story && it.branch == imported.branch }
        val selected = owner.gateway.resumeSaved(SavedStory(imported.story, branch(role), root.title, head(role)))
        assertEquals(branch(role), checkNotNull(selected.selected).branch)
        assertEquals(head(role), selected.revision)
        assertBoundPlayer(owner, selected)
        return owner
    }

    suspend fun assertBoundPlayer(owner: RecordOwner, saved: SavedSnapshot? = null) {
        val current = saved ?: owner.gateway.snapshot()
        val actual = owner.data(owner.scoped("play_snapshot").put("expected_revision", current.revision))
        assertEquals(player, actual.getJSONObject("player").getString("observer"))
        assertNotEquals("player", actual.getJSONObject("player").getString("observer"))
    }

    /** Setup only: a separate real story with the same scalar event number is not a page grant. */
    suspend fun otherStory(owner: RecordOwner): SavedStory {
        val original = checkNotNull(owner.gateway.snapshot().selected)
        val created = owner.data(JSONObject().put("op", "create").put("seed", "lantern-quay-v1"))
        val scope = created.getJSONObject("scope")
        val sequence = drill().sequence.also { check(it in 1..8) }
        repeat(sequence.toInt()) {
            owner.commitIntent(JSONObject().put("kind", "actions").put("value", JSONArray()
                .put(JSONObject().put("op", "wait").put("ticks", 1))))
        }
        owner.data(JSONObject().put("op", "close").put("session", created.getString("session")).put("scope", scope))
        owner.gateway.resumeSaved(original)
        return owner.gateway.snapshot().stories.single { it.story == scope.getString("story") }
    }
}

/* Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0 */
package org.locallore.app

import android.content.Context
import android.content.ContextWrapper
import androidx.test.ext.junit.runners.AndroidJUnit4
import androidx.test.platform.app.InstrumentationRegistry
import java.io.File
import java.util.Collections
import java.util.UUID
import java.util.concurrent.atomic.AtomicInteger
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.NonCancellable
import kotlinx.coroutines.runBlocking
import kotlinx.coroutines.withContext
import org.json.JSONArray
import org.json.JSONObject
import org.junit.Assert.*
import org.junit.Test
import org.junit.runner.RunWith

/** Actual JNI/Store in new synthetic roots; no OS-death, UI or hidden-world equality claim. */
@RunWith(AndroidJUnit4::class)
class RetainedParentFallbackNativeTest {
    private companion object {
        const val ROOT = "SYNTHETIC process-restoration dialogue: Mira, caf\u00e9 and lanterns \uD83C\uDF0A.\n" +
            "Still unsent until my explicit Send."
        const val PREFIX = "SYNTHETIC retained-parent prefix: Mira, snow \u96ea and caf\u00e9 \uD83C\uDF0A.\n" +
            "Keep this accepted statement in the retained child."
        const val TAIL = "SYNTHETIC unreachable-parent tail: Mira, this belongs only to the parent after the child fork."
        const val DRAFT = "SYNTHETIC retired-parent unsent draft: Mira, lanterns \uD83C\uDF0A and snow \u96ea.\n" +
            "Never send or restore this after retirement."
        val READS = setOf("workspace", "branches", "resume", "open", "play_snapshot", "capabilities", "model_status", "close")
    }

    private class Owner(context: Context, hint: PlayDraftScope?) {
        val commands: MutableList<JSONObject> = Collections.synchronizedList(mutableListOf())
        val transport = NativeWorkspaceTransport(context)
        private val port = object : WorkspaceTransport {
            override suspend fun exchange(command: JSONObject): JSONObject {
                commands += JSONObject(command.toString()) // Observe original requests, never replace native replies.
                return transport.exchange(command)
            }
            override fun close() = transport.close()
        }
        val gateway = DurableGateway(port, autoCreateIfEmpty = false, initialScopeHint = hint)
        suspend fun reply(command: JSONObject): JSONObject = port.exchange(command).also {
            assertEquals(1, it.getInt("version"))
        }
        suspend fun data(command: JSONObject): JSONObject = reply(command).also {
            assertEquals("ok", it.getString("status"))
        }.getJSONObject("data")
        suspend fun view(snapshot: SavedSnapshot): JSONObject {
            val selected = checkNotNull(snapshot.selected)
            val binding = checkNotNull(gateway.forkContext(selected, snapshot.revision, 0))
            return data(JSONObject().put("op", "play_snapshot").put("session", binding.session)
                .put("scope", scope(selected)).put("expected_revision", snapshot.revision)).also {
                assertEquals(setOf("scope", "revision", "rules", "player", "inventory", "receipts"), keys(it))
                assertEquals(canonical(scope(selected)), canonical(it.getJSONObject("scope")))
                assertEquals(snapshot.revision, it.getLong("revision"))
                val player = it.getJSONObject("player")
                assertEquals("player", player.getString("observer"))
                assertEquals(canonical(scope(selected)), canonical(player.getJSONObject("scope")))
                assertEquals(snapshot.revision, player.getLong("revision"))
            }
        }
        fun assertOnlyReads() = assertTrue("Fallback dispatched a mutation", commands.all { it.getString("op") in READS })
        fun lastSubmission(): JSONObject = synchronized(commands) {
            JSONObject(commands.last { it.getString("op") == "free_text" }.toString())
        }
    }

    private class Fixture {
        private val app = InstrumentationRegistry.getInstrumentation().targetContext
        private val parent = app.noBackupFilesDir.canonicalFile
        val root = File(parent, "retained-parent-native-${UUID.randomUUID()}").also {
            check(it.mkdir() && it.canonicalFile.parentFile == parent)
        }
        private val context = object : ContextWrapper(app) {
            override fun getApplicationContext(): Context = this
            override fun getNoBackupFilesDir(): File = root
        }
        private val owners = mutableListOf<Owner>()
        private val forks = mutableListOf<NativeForkGateway>()
        val forkAttempts = AtomicInteger()
        fun owner(hint: PlayDraftScope? = null) = Owner(context, hint).also { owners += it }
        fun fork(owner: Owner) = NativeForkGateway(owner.transport::forkHandle,
            mutationObserver = { forkAttempts.incrementAndGet() }).also { forks += it }
        fun requestClose() {
            var failure: Throwable? = null
            fun close(action: () -> Unit) {
                try { action() } catch (next: Throwable) {
                    failure?.addSuppressed(next) ?: run { failure = next }
                }
            }
            forks.asReversed().forEach { close(it::close) }
            owners.asReversed().forEach { close(it.gateway::close) }
            failure?.let { throw it }
            // Adapter close is requested asynchronously: this does not prove joined drain.
            // Keep the exclusively created fixture; never adopt or remove another workspace.
        }
    }

    private data class World(val owner: Owner, val other: SavedStory, val root: SavedStory,
        val parent: SavedStory, val retained: SavedStory, val otherView: String,
        val rootView: String, val retainedView: String)

    private suspend fun send(owner: Owner, text: String, head: Long): SavedSnapshot {
        val prepared = owner.gateway.respondText(PlayInput(PlayInputKind.DIALOGUE, text), head)
        assertTrue(prepared is DemoResult.Prepared)
        assertTrue(owner.gateway.commitAsync(prepared) is DemoResult.Accepted)
        return owner.gateway.snapshot().also { assertEquals(head + 1, it.revision) }
    }

    private suspend fun fork(fixture: Fixture, owner: Owner, parent: SavedStory, child: String): SavedStory {
        val binding = checkNotNull(owner.gateway.forkContext(parent, parent.revision, 0))
        val input = BranchForkInput(binding.parent, child, parent.revision, parent.revision)
        val gateway = fixture.fork(owner)
        val registered = gateway.register(binding, input, true)
        assertEquals(BranchForkPhase.REGISTERED, registered.phase)
        val completed = gateway.run(registered.operation)
        assertEquals(BranchForkPhase.COMPLETED, completed.phase)
        assertTrue(checkNotNull(completed.outcome).created)
        return checkNotNull(owner.gateway.resumeSaved(parent.copy(branch = child)).selected).also {
            assertEquals(parent.revision, it.revision)
        }
    }

    private suspend fun setup(fixture: Fixture): World {
        val owner = fixture.owner()
        assertNull(owner.gateway.initialize().selected)
        owner.gateway.createSaved()
        val library = owner.gateway.createSaved()
        assertEquals(2, library.stories.size)
        assertEquals(library.stories.map { it.story }.sorted(), library.stories.map { it.story })
        val other = library.stories.first()
        val rootZero = library.stories.last()
        assertNotEquals(other.story, rootZero.story)
        owner.gateway.resumeSaved(rootZero)
        val root = checkNotNull(send(owner, ROOT, 0).selected)
        val parentOne = fork(fixture, owner, root, "retained-parent")
        val parentTwo = checkNotNull(send(owner, PREFIX, 1).selected)
        val retained = fork(fixture, owner, parentTwo, "retained-grandchild")
        owner.gateway.resumeSaved(parentTwo)
        val parent = checkNotNull(send(owner, TAIL, 2).selected)
        assertEquals(3L, parent.revision)
        assertEquals(parentOne.branch, parent.branch)
        assertEquals(4, fixture.forkAttempts.get())
        val otherView = canonical(owner.view(owner.gateway.resumeSaved(other)))
        val rootView = owner.view(owner.gateway.resumeSaved(root))
        assertReceipts(rootView, listOf(root.branch), listOf(ROOT))
        val childView = owner.view(owner.gateway.resumeSaved(retained))
        assertReceipts(childView, listOf(root.branch, parent.branch), listOf(ROOT, PREFIX))
        assertEquals(2L, childView.getLong("revision"))
        owner.gateway.resumeSaved(parent)
        return World(owner, other, root, parent, retained, otherView, canonical(rootView), canonical(childView))
    }

    private suspend fun retire(fixture: Fixture, world: World, extraReady: Boolean) = withContext(Dispatchers.IO) {
        val staging = File(fixture.root, "retirement-staging").also { check(it.mkdir()) }
        val handle = NativeArchive.open(File(fixture.root, "workspace-v1/stories.sqlite3").absolutePath, staging.absolutePath)
        check(handle > 0)
        var primary: Throwable? = null
        try {
            val request = scope(world.parent).put("expected_revision", 3).toString().toByteArray(Charsets.UTF_8)
            val prepared = ArchiveNativeWire.branchDeletionPrepared(NativeArchive.prepareBranchDelete(handle, request))
            val p = prepared.preview
            assertEquals(2, p.version)
            assertEquals(world.parent.story, p.storyId)
            assertEquals(world.parent.branch, p.branchId)
            assertEquals(world.root.title, p.title)
            assertEquals(world.root.branch, p.rootBranch)
            assertEquals(3L, p.expectedRevision)
            assertEquals(mapOf(world.retained.branch to 2L), p.retainedDescendants)
            assertEquals(mapOf(world.parent.branch to 2L), p.retainedHeads)
            assertTrue(p.removedBranches.isEmpty())
            assertEquals(mapOf("memory_job_packets" to 0L, "memory_jobs" to 0L, "derived_memory" to 0L,
                "event_witnesses" to 2L, "accepted_events" to 1L, "turns" to if (extraReady) 2L else 1L,
                "branch_projections" to 1L, "branch_entities" to 0L, "branches" to 0L), p.removedRows)
            assertEquals(1L, p.removedCommittedTurns)
            assertEquals(if (extraReady) 1L else 0L, p.removedNoncommittedTurns)
            val result = ArchiveNativeWire.branchDeleted(NativeArchive.commitBranchDelete(handle, prepared.token))
            assertEquals(world.parent.story, result.storyId)
            assertEquals(world.parent.branch, result.branchId)
            assertEquals(2L, result.retainedThroughRevision)
            assertEquals(0L, result.collectedBranches)
            assertEquals(if (extraReady) 2L else 1L, result.deletedTurns)
            assertEquals(listOf(world.parent.branch), result.invalidatedBranches)
        } catch (failure: Throwable) { primary = failure; throw failure }
        finally {
            // Synchronous raw owner close, even on an assertion failure; retain the original failure.
            try { NativeArchive.close(handle) }
            catch (cleanup: Throwable) { primary?.addSuppressed(cleanup) ?: throw cleanup }
        }
    }

    private suspend fun catalog(owner: Owner, world: World, childHead: Long): String {
        val data = owner.data(JSONObject().put("op", "branches").put("story", world.parent.story))
        assertEquals(2, data.getInt("version"))
        val rows = data.getJSONArray("branches")
        val byId = (0 until rows.length()).associate { rows.getJSONObject(it).let { row ->
            row.getJSONObject("scope").getString("branch") to row
        } }
        assertEquals(setOf(world.root.branch, world.parent.branch, world.retained.branch), byId.keys)
        assertEquals(3, rows.length())
        val parent = byId.getValue(world.parent.branch)
        assertEquals(true, parent.get("retired"))
        assertEquals(2L, parent.getLong("revision")) // Physical retained prefix, not public admission.
        assertEquals(0, parent.getInt("drafts"))
        assertEquals(world.root.branch, parent.getString("parent_branch"))
        assertEquals(1L, parent.getLong("fork_revision"))
        val child = byId.getValue(world.retained.branch)
        assertEquals(false, child.get("retired"))
        assertEquals(childHead, child.getLong("revision"))
        assertEquals(world.parent.branch, child.getString("parent_branch"))
        assertEquals(2L, child.getLong("fork_revision"))
        val root = byId.getValue(world.root.branch)
        assertEquals(false, root.get("retired"))
        assertEquals(1L, root.getLong("revision"))
        return canonical(data)
    }

    @Test fun parentRetirementFallsBackOnceAndPreservesOriginalGrandchildReceipts() = runBlocking {
        withFixture { fixture ->
            val world = setup(fixture)
            retire(fixture, world, extraReady = false)
            val reader = fixture.owner(PlayDraftScope(world.parent.story, world.parent.branch))
            val fallback = reader.gateway.initialize()
            assertEquals(world.other, fallback.selected)
            assertEquals(0L, fallback.revision)
            assertTrue(fallback.messages.isEmpty())
            assertTrue(fallback.selectionRestoreUnavailable)
            assertEquals(world.otherView, canonical(reader.view(fallback)))
            val resumed = reader.commands.filter { it.getString("op") == "resume" }
            assertEquals(1, resumed.size)
            assertEquals(canonical(scope(world.other)), canonical(resumed.single().getJSONObject("scope")))
            assertEquals("workspace", reader.commands.first().getString("op"))
            assertTrue(reader.commands.indexOfFirst { it.getString("op") == "branches" } in
                0 until reader.commands.indexOfFirst { it.getString("op") == "resume" })
            val before = reader.commands.count { it.getString("op") == "play_snapshot" }
            val again = reader.gateway.snapshot()
            assertEquals(world.other, again.selected)
            assertFalse(again.selectionRestoreUnavailable)
            assertTrue(reader.commands.count { it.getString("op") == "play_snapshot" } > before)
            val originalCatalog = catalog(reader, world, 2)
            val refused = reader.reply(JSONObject().put("op", "resume").put("scope", scope(world.parent)))
            assertEquals("rejected", refused.getString("status"))
            assertEquals("NotFound", refused.getString("error"))
            val retained = reader.gateway.resumeSaved(world.retained)
            assertFalse(retained.selectionRestoreUnavailable)
            assertEquals(setOf(world.root.branch, world.retained.branch), retained.timelines.map { it.branch }.toSet())
            assertEquals(world.retainedView, canonical(reader.view(retained)))
            assertReceipts(reader.view(retained), listOf(world.root.branch, world.parent.branch), listOf(ROOT, PREFIX))
            val root = reader.gateway.resumeSaved(world.root)
            assertEquals(world.rootView, canonical(reader.view(root)))
            val recovered = reader.gateway.recoverSaved()
            assertEquals(world.root, recovered.selected)
            assertFalse(recovered.selectionRestoreUnavailable)
            assertEquals(world.rootView, canonical(reader.view(recovered)))
            assertEquals(originalCatalog, catalog(reader, world, 2))
            assertEquals(4, fixture.forkAttempts.get())
            reader.assertOnlyReads()
        }
    }

    @Test fun cachedParentReadyIsClosedWhileRetainedChildReadyCommitsExactlyOnce() = runBlocking {
        withFixture { fixture ->
            val world = setup(fixture)
            val target = world.owner
            val targetReady = target.gateway.respondText(PlayInput(PlayInputKind.DIALOGUE, DRAFT), 3)
            assertTrue(targetReady is DemoResult.Prepared)
            val original = target.lastSubmission()
            val child = fixture.owner()
            val opened = child.gateway.initialize()
            assertEquals(world.other, opened.selected)
            val childBefore = child.gateway.resumeSaved(world.retained)
            assertEquals(world.retainedView, canonical(child.view(childBefore)))
            val text = "SYNTHETIC retained child: this explicit prepared turn survives parent retirement."
            val childReady = child.gateway.respondText(PlayInput(PlayInputKind.DIALOGUE, text), 2)
            assertTrue(childReady is DemoResult.Prepared)
            val originalChild = child.lastSubmission()
            retire(fixture, world, extraReady = true)
            for (op in listOf("commit", "prepare", "turn_status")) {
                val refused = target.reply(bound(op, original))
                assertEquals("rejected", refused.getString("status"))
                assertEquals("Closed", refused.getString("error"))
            }
            assertTrue(child.gateway.commitAsync(childReady) is DemoResult.Accepted)
            val accepted = child.gateway.snapshot()
            assertEquals(3L, accepted.revision)
            val view = child.view(accepted)
            assertReceipts(view, listOf(world.root.branch, world.parent.branch, world.retained.branch), listOf(ROOT, PREFIX, text))
            val repeated = child.data(bound("commit", originalChild))
            assertEquals("committed", repeated.getString("phase"))
            assertEquals(canonical(originalChild.getJSONObject("request")),
                canonical(repeated.getJSONObject("receipt").getJSONObject("request")))
            assertEquals(canonical(view.getJSONArray("receipts").getJSONObject(2)), canonical(repeated.getJSONObject("receipt")))
            assertEquals(canonical(view), canonical(child.view(child.gateway.snapshot())))
            catalog(child, world, 3)
            assertEquals(world.rootView, canonical(child.view(child.gateway.resumeSaved(world.root))))
            assertEquals(world.otherView, canonical(child.view(child.gateway.resumeSaved(world.other))))
            assertEquals(4, fixture.forkAttempts.get())
        }
    }

    private suspend fun withFixture(action: suspend (Fixture) -> Unit) {
        val fixture = Fixture()
        var primary: Throwable? = null
        try { action(fixture) } catch (failure: Throwable) { primary = failure; throw failure }
        finally {
            try { withContext(NonCancellable) { fixture.requestClose() } }
            catch (cleanup: Throwable) { primary?.addSuppressed(cleanup) ?: throw cleanup }
        }
    }

    private fun assertReceipts(view: JSONObject, branches: List<String>, words: List<String>) {
        val receipts = view.getJSONArray("receipts")
        assertEquals(branches.size, receipts.length())
        for (i in branches.indices) {
            val request = receipts.getJSONObject(i).getJSONObject("request")
            assertEquals(view.getJSONObject("scope").getString("story"), request.getJSONObject("scope").getString("story"))
            assertEquals(branches[i], request.getJSONObject("scope").getString("branch"))
            assertEquals(i.toLong(), request.getLong("expected_revision"))
            val intent = request.getJSONObject("intent")
            assertEquals("free_text", intent.getString("kind"))
            assertEquals("dialogue", intent.getJSONObject("value").getString("kind"))
            assertEquals(words[i], intent.getJSONObject("value").getString("text"))
            assertNotEquals(TAIL, intent.getJSONObject("value").getString("text"))
        }
    }
}

private fun keys(value: JSONObject): Set<String> = value.keys().asSequence().toSet()
private fun scope(story: SavedStory): JSONObject = JSONObject().put("story", story.story).put("branch", story.branch)
private fun bound(op: String, submission: JSONObject): JSONObject = JSONObject().put("op", op)
    .put("session", submission.getString("session")).put("scope", submission.getJSONObject("request").getJSONObject("scope"))
    .put("turn", submission.getJSONObject("request").getString("turn"))
private fun canonical(value: Any?): String = when (value) {
    is JSONObject -> value.keys().asSequence().toList().sorted().joinToString(",", "{", "}") {
        JSONObject.quote(it) + ":" + canonical(value.get(it))
    }
    is JSONArray -> (0 until value.length()).joinToString(",", "[", "]") { canonical(value.get(it)) }
    is String -> JSONObject.quote(value)
    null, JSONObject.NULL -> "null"
    else -> value.toString()
}

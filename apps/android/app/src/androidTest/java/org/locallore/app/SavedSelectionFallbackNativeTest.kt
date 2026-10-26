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
import kotlinx.coroutines.NonCancellable
import kotlinx.coroutines.runBlocking
import kotlinx.coroutines.withContext
import org.json.JSONArray
import org.json.JSONObject
import org.junit.Assert.*
import org.junit.Test
import org.junit.runner.RunWith

/** Actual JNI catalogs/replay in new synthetic roots; not an OS process-death or UI oracle. */
@RunWith(AndroidJUnit4::class)
class SavedSelectionFallbackNativeTest {
    private companion object {
        const val PARENT_TEXT = "SYNTHETIC saved-selection parent: caf\u00e9 and snow \u96ea.\nThese are only my words."
        val READS = setOf("workspace", "branches", "resume", "open", "play_snapshot", "capabilities", "model_status", "close")
    }

    private class Owner(context: Context, hint: PlayDraftScope?) {
        val calls: MutableList<String> = Collections.synchronizedList(mutableListOf())
        val transport = NativeWorkspaceTransport(context, operationObserver = { calls.add(it) })
        val resumedScopes = mutableListOf<PlayDraftScope>()
        val gateway = DurableGateway(object : WorkspaceTransport {
            override suspend fun exchange(command: JSONObject): JSONObject {
                if (command.getString("op") == "resume") {
                    val scope = command.getJSONObject("scope")
                    resumedScopes += PlayDraftScope(scope.getString("story"), scope.getString("branch"))
                }
                return transport.exchange(command) // Observe only; no synthetic reply/substitution.
            }
            override fun close() = transport.close()
        }, autoCreateIfEmpty = false, initialScopeHint = hint)
        suspend fun data(command: JSONObject): JSONObject {
            val reply = transport.exchange(command)
            assertEquals("ok", reply.getString("status"))
            return reply.getJSONObject("data")
        }
        suspend fun view(snapshot: SavedSnapshot): String {
            val selected = checkNotNull(snapshot.selected)
            val binding = checkNotNull(gateway.forkContext(selected, snapshot.revision, 0))
            val scope = JSONObject().put("story", selected.story).put("branch", selected.branch)
            val view = data(JSONObject().put("op", "play_snapshot").put("session", binding.session)
                .put("scope", scope).put("expected_revision", snapshot.revision))
            assertEquals(selected.story, view.getJSONObject("scope").getString("story"))
            assertEquals(selected.branch, view.getJSONObject("scope").getString("branch"))
            assertEquals(snapshot.revision, view.getLong("revision"))
            val player = view.getJSONObject("player")
            assertEquals("player", player.getString("observer"))
            assertEquals(canonical(scope), canonical(player.getJSONObject("scope")))
            assertEquals(snapshot.revision, player.getLong("revision"))
            return canonical(view)
        }
        fun assertOnlyReads() {
            assertTrue("Fallback/navigation dispatched a non-read Host operation", calls.all { it in READS })
        }
    }

    private class Fixture {
        private val app = InstrumentationRegistry.getInstrumentation().targetContext
        private val parent = app.noBackupFilesDir.canonicalFile
        val root = File(parent, "saved-selection-native-${UUID.randomUUID()}").also {
            check(it.mkdir() && it.canonicalFile.parentFile == parent)
        }
        private val context = object : ContextWrapper(app) {
            override fun getApplicationContext(): Context = this
            override fun getNoBackupFilesDir(): File = root
        }
        private val owners = mutableListOf<Owner>()
        private val forks = mutableListOf<NativeForkGateway>()
        private val archives = mutableListOf<NativeArchiveGateway>()
        val forkAttempts = AtomicInteger()
        fun owner(hint: PlayDraftScope? = null) = Owner(context, hint).also { owners += it }
        fun fork(owner: Owner) = NativeForkGateway(owner.transport::forkHandle,
            mutationObserver = { forkAttempts.incrementAndGet() }).also { forks += it }
        fun archive() = NativeArchiveGateway(context).also { archives += it }

        fun requestClose() {
            // All public adapter close calls are made even if another close reports failure.
            var failure: Throwable? = null
            fun close(action: () -> Unit) {
                try { action() } catch (next: Throwable) {
                    failure?.addSuppressed(next) ?: run { failure = next }
                }
            }
            forks.asReversed().forEach { close(it::close) }
            archives.asReversed().forEach { close(it::close) }
            owners.asReversed().forEach { close(it.gateway::close) }
            failure?.let { throw it }
            // Production workspace/archive closes are asynchronous requests, not drain proof.
            // Retain this one create-only synthetic root; no existing workspace is adopted/removed.
        }
    }

    private data class World(val a: SavedStory, val parent: SavedStory, val child: SavedStory,
        val parentView: String, val childView: String, val parentMessages: List<SceneMessage>)

    private suspend fun setup(fixture: Fixture): World {
        val owner = fixture.owner()
        try {
            assertNull(owner.gateway.initialize().selected)
            owner.gateway.createSaved()
            val two = owner.gateway.createSaved()
            assertEquals(2, two.stories.size)
            assertEquals(two.stories.map { it.story }.sorted(), two.stories.map { it.story })
            val a = two.stories.first()
            val b = two.stories.last()
            assertNotEquals(a.story, b.story)
            assertEquals(0L, owner.gateway.resumeSaved(a).revision)
            val before = owner.gateway.resumeSaved(b)
            assertEquals(0L, before.revision)
            assertEquals(TextProvider.SCRIPTED, before.textProvider)
            val prepared = owner.gateway.respondText(PlayInput(PlayInputKind.DIALOGUE, PARENT_TEXT), 0)
            assertTrue(prepared is DemoResult.Prepared)
            assertTrue(owner.gateway.commitAsync(prepared) is DemoResult.Accepted)
            val accepted = owner.gateway.snapshot()
            assertEquals(1L, accepted.revision)
            assertEquals(listOf(PARENT_TEXT), accepted.messages.filter { it.isPlayer }.map { it.text })
            val parent = checkNotNull(accepted.selected)
            val parentView = owner.view(accepted)
            val context = checkNotNull(owner.gateway.forkContext(parent, 1, 1))
            val input = BranchForkInput(context.parent, "saved-selection-child", 1, 1)
            val fork = fixture.fork(owner)
            val registered = fork.register(context, input, true)
            assertEquals(BranchForkPhase.REGISTERED, registered.phase)
            val result = fork.run(registered.operation)
            assertEquals(BranchForkPhase.COMPLETED, result.phase)
            assertTrue(checkNotNull(result.outcome).created)
            assertEquals(2, fixture.forkAttempts.get())
            val child = owner.gateway.resumeSaved(parent.copy(branch = input.childBranch))
            assertEquals(1L, child.revision)
            assertEquals(accepted.messages, child.messages) // Inherited receipt keeps its ancestor scope.
            return World(a, parent, checkNotNull(child.selected), parentView, owner.view(child), accepted.messages)
        } finally { owner.gateway.close() }
    }

    private suspend fun exerciseFallback(fixture: Fixture, world: World, hint: PlayDraftScope, retired: Boolean) {
        val owner = fixture.owner(hint)
        val fallback = owner.gateway.initialize()
        assertEquals(world.a, fallback.selected)
        assertEquals(0L, fallback.revision)
        assertTrue(fallback.messages.isEmpty())
        assertTrue(fallback.selectionRestoreUnavailable)
        assertEquals(listOf(PlayDraftScope(world.a.story, world.a.branch)), owner.resumedScopes)
        assertEquals("workspace", owner.calls.first())
        if (hint.story == world.parent.story) {
            assertTrue(owner.calls.indexOf("branches") in 0 until owner.calls.indexOf("resume"))
        }
        owner.view(fallback)
        val readsBefore = owner.calls.count { it == "play_snapshot" }
        val again = owner.gateway.snapshot()
        assertFalse(again.selectionRestoreUnavailable)
        assertEquals(world.a, again.selected)
        assertTrue(owner.calls.count { it == "play_snapshot" } > readsBefore)
        val parent = owner.gateway.resumeSaved(world.parent)
        assertFalse(parent.selectionRestoreUnavailable)
        assertEquals(world.parent, parent.selected)
        assertEquals(world.parentMessages, parent.messages)
        assertEquals(world.parentView, owner.view(parent))
        val catalogBefore = canonical(owner.data(JSONObject().put("op", "branches").put("story", world.parent.story)))
        if (retired) {
            assertTrue(parent.timelines.none { it.branch == world.child.branch })
            val refused = owner.transport.exchange(JSONObject().put("op", "resume").put("scope",
                JSONObject().put("story", world.child.story).put("branch", world.child.branch)))
            assertEquals("rejected", refused.getString("status"))
            assertEquals("NotFound", refused.getString("error"))
            try { owner.gateway.resumeSaved(world.child); fail("Retired child was selectable") }
            catch (failure: WorkspaceFailure) { assertEquals("NotFound", failure.category) }
            assertFalse(owner.gateway.resumeSaved(world.parent).selectionRestoreUnavailable)
        } else {
            assertTrue(parent.timelines.any { it.branch == world.child.branch })
            val child = owner.gateway.resumeSaved(world.child)
            assertFalse(child.selectionRestoreUnavailable)
            assertEquals(world.child, child.selected)
            assertEquals(world.childView, owner.view(child))
        }
        val recovered = owner.gateway.recoverSaved()
        assertFalse(recovered.selectionRestoreUnavailable)
        assertEquals(if (retired) world.parent else world.child, recovered.selected)
        assertEquals(catalogBefore, canonical(owner.data(JSONObject().put("op", "branches").put("story", world.parent.story))))
        val finalParent = owner.gateway.resumeSaved(world.parent)
        assertFalse(finalParent.selectionRestoreUnavailable)
        assertEquals(world.parentView, owner.view(finalParent))
        assertEquals(listOf(world.a.story, world.parent.story), finalParent.stories.map { it.story })
        assertEquals(listOf(0L, 1L), finalParent.stories.map { it.revision })
        assertEquals(2, fixture.forkAttempts.get())
        owner.assertOnlyReads()
    }

    @Test fun missingStoryHintFallsBackOnceWithoutChangingTheRealParentOrChild() = runBlocking {
        withFixture { fixture ->
            val world = setup(fixture)
            val missing = "missing-story-${UUID.randomUUID()}"
            assertTrue(missing != world.a.story && missing != world.parent.story)
            exerciseFallback(fixture, world, PlayDraftScope(missing, world.child.branch), retired = false)
        }
    }

    @Test fun missingChildHintFallsBackOnceWithoutCreatingOrSelectingThatChild() = runBlocking {
        withFixture { fixture ->
            val world = setup(fixture)
            val missing = "missing-child"
            assertTrue(missing != world.parent.branch && missing != world.child.branch)
            exerciseFallback(fixture, world, PlayDraftScope(world.parent.story, missing), retired = false)
        }
    }

    @Test fun retiredLeafHintFallsBackOnceAndNativeResumeStillRefusesIt() = runBlocking {
        withFixture { fixture ->
            val world = setup(fixture)
            val archive = fixture.archive()
            val prepared = archive.prepareBranch(world.child)
            assertEquals(world.child.story, prepared.preview.storyId)
            assertEquals(world.child.branch, prepared.preview.branchId)
            assertEquals(1L, prepared.preview.expectedRevision)
            assertTrue(prepared.preview.retainedDescendants.isEmpty())
            assertTrue(world.child.branch in prepared.preview.removedBranches)
            val deleted = archive.commitBranch(prepared.token)
            assertEquals(world.child.story, deleted.storyId)
            assertEquals(world.child.branch, deleted.branchId)
            assertNull(deleted.retainedThroughRevision)
            assertEquals(listOf(world.child.branch), deleted.invalidatedBranches)
            archive.close()
            exerciseFallback(fixture, world, PlayDraftScope(world.child.story, world.child.branch), retired = true)
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
}

private fun canonical(value: Any?): String = when (value) {
    is JSONObject -> value.keys().asSequence().toList().sorted().joinToString(",", "{", "}") {
        JSONObject.quote(it) + ":" + canonical(value.get(it))
    }
    is JSONArray -> (0 until value.length()).joinToString(",", "[", "]") { canonical(value.get(it)) }
    is String -> JSONObject.quote(value)
    null, JSONObject.NULL -> "null"
    else -> value.toString()
}

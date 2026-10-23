/* Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0 */
package org.locallore.app

import kotlinx.coroutines.CompletableDeferred
import kotlinx.coroutines.ExperimentalCoroutinesApi
import kotlinx.coroutines.NonCancellable
import kotlinx.coroutines.test.advanceUntilIdle
import kotlinx.coroutines.test.runCurrent
import kotlinx.coroutines.test.runTest
import kotlinx.coroutines.withContext
import org.junit.Assert.*
import org.junit.Test

/** Consent/lifetime tests use fakes; native ancestry/SQL behavior is tested in Rust. */
@OptIn(ExperimentalCoroutinesApi::class)
class BranchDeletionControllerTest {
    @Test fun rootCannotOpenAndOnlyTheExactRenderedChildConsentCanCommit(): Unit = runTest {
        val gateway = Gateway(); val closed = mutableListOf<Pair<BranchDeleted?, Boolean>>()
        val controller = BranchDeletionController(this, gateway) { result, uncertain -> closed += result to uncertain }
        controller.open(Child.copy(branch = "main"), "main"); controller.confirm(prepared(Child)); advanceUntilIdle()
        assertFalse(controller.state.value.visible); assertTrue(gateway.prepares.isEmpty())
        controller.open(Child, "main"); controller.open(Sibling, "main"); advanceUntilIdle()
        assertEquals(listOf(Child), gateway.prepares); assertTrue(gateway.commits.isEmpty())
        val consent = controller.state.value.prepared!!
        controller.confirm(consent.copy()); assertTrue(gateway.commits.isEmpty())
        controller.confirm(consent); controller.confirm(consent); advanceUntilIdle()
        assertEquals(listOf(42L), gateway.commits); assertEquals(deleted(Child), controller.state.value.deleted)
        assertTrue(closed.isEmpty()); controller.dismiss(); controller.dismiss(); advanceUntilIdle()
        assertEquals(listOf(deleted(Child) to false), closed)
        assertEquals(BranchDeletionUiState(), controller.state.value)
    }

    @Test fun capturedNativePreviewAndOutcomeCollectionsAreDefensiveAndUnmodifiable(): Unit = runTest {
        val gateway = Gateway()
        val descendants = linkedMapOf("child" to 12L); val heads = linkedMapOf("parent" to 9L)
        val removed = mutableListOf("old-ancestor"); val rows = linkedMapOf("turns" to 1_099_511_627_776L)
        val invalidated = mutableListOf("parent", "old-ancestor")
        val authoritative = preview(Child).copy(retainedDescendants = descendants, retainedHeads = heads,
            removedBranches = removed, removedRows = rows, removedCommittedTurns = 1_099_511_627_776L)
        gateway.onPrepare = { BranchDeletionPrepared(42, authoritative) }
        gateway.onCommit = { deleted(Child).copy(invalidatedBranches = invalidated) }
        val controller = BranchDeletionController(this, gateway) { _, _ -> }
        controller.open(Child, "main"); advanceUntilIdle()
        val consent = controller.state.value.prepared!!; assertEquals(authoritative, consent.preview)
        descendants.clear(); heads.clear(); removed.clear(); rows.clear()
        assertEquals(mapOf("child" to 12L), consent.preview.retainedDescendants)
        assertEquals(mapOf("parent" to 9L), consent.preview.retainedHeads)
        assertEquals(listOf("old-ancestor"), consent.preview.removedBranches)
        assertEquals(1_099_511_627_776L, consent.preview.removedRows["turns"])
        try { (consent.preview.retainedHeads as MutableMap<String, Long>).clear(); fail("Mutable ancestry") }
        catch (_: UnsupportedOperationException) { }
        try { (consent.preview.removedBranches as MutableList<String>).clear(); fail("Mutable removed branches") }
        catch (_: UnsupportedOperationException) { }
        controller.confirm(consent); advanceUntilIdle(); invalidated.clear()
        assertEquals(listOf("parent", "old-ancestor"), controller.state.value.deleted!!.invalidatedBranches)
        try { (controller.state.value.deleted!!.invalidatedBranches as MutableList<String>).clear(); fail("Mutable result") }
        catch (_: UnsupportedOperationException) { }
    }

    @Test fun mismatchedNativePreviewNeverPublishesConsentOrCommits(): Unit = runTest {
        val mutations: List<(BranchDeletionPrepared) -> BranchDeletionPrepared> = listOf(
            { it.copy(token = 0) },
            { it.copy(preview = it.preview.copy(version = 2)) },
            { it.copy(preview = it.preview.copy(storyId = "other-story")) },
            { it.copy(preview = it.preview.copy(branchId = "sibling")) },
            { it.copy(preview = it.preview.copy(rootBranch = "parent")) },
            { it.copy(preview = it.preview.copy(expectedRevision = 11)) },
            { it.copy(preview = it.preview.copy(title = "Different saved story")) },
        )
        for (mutate in mutations) {
            val gateway = Gateway(); gateway.onPrepare = { mutate(prepared(it)) }
            val controller = BranchDeletionController(this, gateway) { _, _ -> }
            controller.open(Child, "main"); advanceUntilIdle()
            assertNull(controller.state.value.prepared); assertTrue(gateway.commits.isEmpty())
            assertTrue(controller.state.value.notice!!.contains("could not be prepared"))
            assertTrue(gateway.cancels > 0); controller.dismiss(); advanceUntilIdle()
        }
    }

    @Test fun staleFailureConsumesConsentAndRetainedCallbackCannotBorrowSiblingToken(): Unit = runTest {
        val gateway = Gateway(); gateway.onCommit = { throw BranchDeletionFailure("Stale") }
        val controller = BranchDeletionController(this, gateway) { _, _ -> }
        controller.open(Child, "main"); advanceUntilIdle(); val old = controller.state.value.prepared!!
        controller.confirm(old); advanceUntilIdle(); controller.confirm(old)
        assertEquals(listOf(42L), gateway.commits); assertNull(controller.state.value.prepared)
        assertTrue(controller.state.value.notice!!.contains("new deletion preview"))
        controller.open(Sibling, "main"); advanceUntilIdle(); assertEquals(1, gateway.prepares.size)
        controller.dismiss(); advanceUntilIdle(); controller.open(Sibling, "main"); advanceUntilIdle()
        val fresh = controller.state.value.prepared!!; assertEquals(old.token, fresh.token)
        controller.confirm(old); assertSame(fresh, controller.state.value.prepared); assertEquals(1, gateway.commits.size)
        gateway.onCommit = { deleted(Sibling) }; controller.confirm(fresh); advanceUntilIdle()
        assertEquals(listOf(42L, 42L), gateway.commits); assertEquals("sibling", controller.state.value.deleted!!.branchId)
    }

    @Test fun cancellationDrainsNoncooperativePreviewBeforeClosingAndRevokesLateToken(): Unit = runTest {
        val release = CompletableDeferred<Unit>(); val gateway = Gateway()
        gateway.onPrepare = { withContext(NonCancellable) { release.await(); prepared(it) } }
        val closed = mutableListOf<Pair<BranchDeleted?, Boolean>>()
        val controller = BranchDeletionController(this, gateway) { value, uncertain -> closed += value to uncertain }
        controller.open(Child, "main"); runCurrent(); controller.cancel(); runCurrent()
        assertTrue(controller.state.value.visible && controller.state.value.closing && controller.state.value.busy)
        assertTrue(closed.isEmpty()); controller.open(Sibling, "main"); controller.confirm(prepared(Sibling))
        release.complete(Unit); advanceUntilIdle()
        assertEquals(listOf(null to false), closed); assertTrue(gateway.commits.isEmpty())
        assertTrue(gateway.cancels >= 2); assertEquals(BranchDeletionUiState(), controller.state.value)
    }

    @Test fun closeDuringNoncooperativeCommitReportsUncertaintyAfterDrainNotRollback(): Unit = runTest {
        val release = CompletableDeferred<Unit>(); val gateway = Gateway(); var actuallyDeleted = false
        gateway.onCommit = { withContext(NonCancellable) { release.await(); actuallyDeleted = true; deleted(Child) } }
        val closed = mutableListOf<Pair<BranchDeleted?, Boolean>>()
        val controller = BranchDeletionController(this, gateway) { value, uncertain -> closed += value to uncertain }
        controller.open(Child, "main"); advanceUntilIdle(); val consent = controller.state.value.prepared!!
        controller.confirm(consent); runCurrent(); controller.dismiss(); runCurrent()
        assertTrue(controller.state.value.notice!!.contains("may already have completed")); assertTrue(closed.isEmpty())
        controller.confirm(consent); controller.open(Sibling, "main"); release.complete(Unit); advanceUntilIdle()
        assertTrue(actuallyDeleted); assertEquals(listOf(42L), gateway.commits)
        assertEquals(listOf(null to true), closed); assertEquals(BranchDeletionUiState(), controller.state.value)
    }

    @Test fun disposalClosesOnceAndFencesNoncooperativePreviewAndCommit(): Unit = runTest {
        for (duringCommit in listOf(false, true)) {
            val gateway = Gateway(); val release = CompletableDeferred<Unit>()
            if (duringCommit) gateway.onCommit = { withContext(NonCancellable) { release.await(); deleted(Child) } }
            else gateway.onPrepare = { withContext(NonCancellable) { release.await(); prepared(it) } }
            val controller = BranchDeletionController(this, gateway) { _, _ -> fail("Disposed callback published") }
            controller.open(Child, "main")
            if (duringCommit) { advanceUntilIdle(); controller.confirm(controller.state.value.prepared!!) }
            runCurrent(); controller.dispose(); controller.dispose()
            controller.open(Sibling, "main"); controller.confirm(prepared(Sibling)); controller.dismiss(); controller.cancel()
            release.complete(Unit); advanceUntilIdle()
            assertEquals(1, gateway.closes); assertEquals(1, gateway.prepares.size)
            assertEquals(if (duringCommit) listOf(42L) else emptyList<Long>(), gateway.commits)
            assertEquals(BranchDeletionUiState(), controller.state.value)
        }
    }

    @Test fun nativeAndUnexpectedErrorsUseFixedGuidanceAndWrongScopeReplyIsUnconfirmed(): Unit = runTest {
        val gateway = Gateway(); val controller = BranchDeletionController(this, gateway) { _, _ -> }
        gateway.onPrepare = { throw BranchDeletionFailure("Full") }; controller.open(Child, "main"); advanceUntilIdle()
        assertTrue(controller.state.value.notice!!.contains("Local storage is full")); assertNull(controller.state.value.prepared)
        controller.dismiss(); advanceUntilIdle(); gateway.onPrepare = { prepared(it) }
        gateway.onCommit = { throw IllegalStateException("PRIVATE SELECT C:/private/story.db") }
        controller.open(Child, "main"); advanceUntilIdle(); controller.confirm(controller.state.value.prepared!!); advanceUntilIdle()
        assertTrue(controller.state.value.notice!!.contains("may already have completed")); assertFalse(controller.state.value.notice!!.contains("PRIVATE"))
        assertNull(controller.state.value.prepared); controller.dismiss(); advanceUntilIdle()
        gateway.onCommit = { deleted(Sibling) }; controller.open(Child, "main"); advanceUntilIdle()
        controller.confirm(controller.state.value.prepared!!); advanceUntilIdle()
        assertNull(controller.state.value.deleted); assertTrue(controller.state.value.notice!!.contains("could not be confirmed"))
        assertEquals("Timeline deletion failed", BranchDeletionFailure("PRIVATE").message)
    }

    private class Gateway : BranchDeletionGateway {
        val prepares = mutableListOf<SavedStory>(); val commits = mutableListOf<Long>()
        var cancels = 0; var closes = 0
        var onPrepare: suspend (SavedStory) -> BranchDeletionPrepared = { prepared(it) }
        var onCommit: suspend (Long) -> BranchDeleted = { deleted(prepares.last()) }
        override suspend fun prepareBranch(story: SavedStory): BranchDeletionPrepared { prepares += story; return onPrepare(story) }
        override suspend fun commitBranch(token: Long): BranchDeleted { commits += token; return onCommit(token) }
        override fun cancel() { cancels++ }
        override fun close() { closes++ }
    }
    private companion object {
        val Child = SavedStory("synthetic-story", "parent", "Original story", 12)
        val Sibling = Child.copy(branch = "sibling", revision = 2)
        fun preview(story: SavedStory) = BranchDeletionPreview(1, story.story, story.branch, story.title,
            "main", story.revision, mapOf("child" to 10L), mapOf(story.branch to 9L), emptyList(),
            mapOf("turns" to 6L, "accepted_events" to 3L), 2, 4, "Synthetic native retention warning")
        fun prepared(story: SavedStory) = BranchDeletionPrepared(42, preview(story))
        fun deleted(story: SavedStory) = BranchDeleted(story.story, story.branch, 9, 0, 6, listOf(story.branch))
    }
}

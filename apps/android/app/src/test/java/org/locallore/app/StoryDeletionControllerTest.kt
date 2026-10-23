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

/** Model-free consent/lifetime checks; no fake gateway is presented as native deletion evidence. */
@OptIn(ExperimentalCoroutinesApi::class)
class StoryDeletionControllerTest {
    @Test fun openingAutomaticallyPreviewsButOnlyExplicitRenderedConsentCanCommit(): Unit = runTest {
        val gateway = Gateway(); val closed = mutableListOf<StoryDeleted?>()
        val controller = StoryDeletionController(this, gateway, closed::add)
        val invented = prepared(Story, 22)
        controller.confirm(invented); controller.cancel(); controller.dismiss()
        assertTrue(gateway.commits.isEmpty())
        controller.open(Story); controller.open(Other); controller.confirm(invented)
        advanceUntilIdle()
        assertEquals(listOf(Story), gateway.prepares)
        assertTrue(gateway.commits.isEmpty())
        val consent = controller.state.value.prepared!!
        controller.confirm(consent.copy()) // Equal values are not the rendered consent object.
        assertTrue(gateway.commits.isEmpty())
        controller.confirm(consent); controller.confirm(consent)
        assertNull(controller.state.value.prepared)
        advanceUntilIdle()
        assertEquals(listOf(22L), gateway.commits)
        assertEquals(Deleted, controller.state.value.deleted)
        assertTrue(closed.isEmpty())
        controller.dismiss(); controller.dismiss(); advanceUntilIdle()
        assertEquals(listOf(Deleted), closed)
        assertEquals(StoryDeletionUiState(), controller.state.value)
    }

    @Test fun nativePreviewIsExactAndBothMapsAreDefensiveAndUnmodifiable(): Unit = runTest {
        val gateway = Gateway()
        val heads = linkedMapOf("main" to 4L, "sibling" to 2L)
        val rows = linkedMapOf("events" to 1_099_511_627_776L, "derived_packets" to 7L)
        val authoritative = preview(Story).copy(branchHeads = heads, rows = rows,
            committedTurns = 12, draftTurns = 3, noncommittedTurns = 5, derivedPackets = 7,
            privacyWarning = "Synthetic native warning", title = "<script>do not execute</script>")
        gateway.onPrepare = { StoryDeletionPrepared(22, authoritative) }
        val controller = StoryDeletionController(this, gateway) {}
        controller.open(Story); advanceUntilIdle()
        val captured = controller.state.value.prepared!!.preview
        assertEquals(authoritative, captured)
        heads.clear(); rows["events"] = 0
        assertEquals(mapOf("main" to 4L, "sibling" to 2L), captured.branchHeads)
        assertEquals(1_099_511_627_776L, captured.rows["events"])
        try { (captured.branchHeads as MutableMap<String, Long>)["late"] = 99L; fail("Mutable head map") }
        catch (_: UnsupportedOperationException) { }
        try { (captured.rows as MutableMap<String, Long>).clear(); fail("Mutable row map") }
        catch (_: UnsupportedOperationException) { }
        assertTrue(gateway.commits.isEmpty())
    }

    @Test fun staleFailureConsumesTokenAndRequiresFreshOpenAndFreshConsent(): Unit = runTest {
        val gateway = Gateway(); var token = 30L
        gateway.onPrepare = { prepared(it, ++token) }
        gateway.onCommit = { throw StoryDeletionFailure("Stale") }
        val closed = mutableListOf<StoryDeleted?>()
        val controller = StoryDeletionController(this, gateway, closed::add)
        controller.open(Story); advanceUntilIdle()
        val stale = controller.state.value.prepared!!
        controller.confirm(stale); advanceUntilIdle(); controller.confirm(stale)
        assertEquals(listOf(31L), gateway.commits)
        assertNull(controller.state.value.prepared)
        assertTrue(controller.state.value.notice!!.contains("new deletion preview"))
        controller.open(Story); advanceUntilIdle()
        assertEquals(1, gateway.prepares.size)
        controller.dismiss(); advanceUntilIdle()
        assertEquals(listOf<StoryDeleted?>(null), closed)
        gateway.onCommit = { Deleted }
        controller.open(Story); advanceUntilIdle()
        val fresh = controller.state.value.prepared!!
        controller.confirm(stale); assertEquals(listOf(31L), gateway.commits)
        controller.confirm(fresh); advanceUntilIdle()
        assertEquals(listOf(31L, 32L), gateway.commits)
        assertEquals(Deleted, controller.state.value.deleted)
    }

    @Test fun oldDialogCallbackCannotDeleteANewStoryEvenIfNativeTokenNumberIsReused(): Unit = runTest {
        val gateway = Gateway(); val controller = StoryDeletionController(this, gateway) {}
        controller.open(Story); advanceUntilIdle()
        val old = controller.state.value.prepared!!
        val retainedClick = { controller.confirm(old) }
        controller.cancel(); advanceUntilIdle()
        controller.open(Other); advanceUntilIdle()
        val fresh = controller.state.value.prepared!!
        assertEquals(old.token, fresh.token)
        retainedClick(); advanceUntilIdle()
        assertTrue(gateway.commits.isEmpty())
        assertSame(fresh, controller.state.value.prepared)
        gateway.onCommit = { StoryDeleted(Other.story, 1, 4) }
        controller.confirm(fresh); advanceUntilIdle()
        assertEquals(listOf(fresh.token), gateway.commits)
        assertEquals(Other.story, controller.state.value.deleted!!.storyId)
    }

    @Test fun preconsentCancellationWaitsForNoncooperativePreviewAndNeverCommits(): Unit = runTest {
        val gateway = Gateway(); val release = CompletableDeferred<Unit>()
        gateway.onPrepare = { withContext(NonCancellable) { release.await(); prepared(it, 22) } }
        val closed = mutableListOf<StoryDeleted?>()
        val controller = StoryDeletionController(this, gateway, closed::add)
        controller.open(Story); runCurrent()
        controller.cancel(); controller.dismiss(); runCurrent()
        assertTrue(controller.state.value.visible && controller.state.value.closing && controller.state.value.busy)
        assertTrue(closed.isEmpty())
        controller.open(Other); controller.confirm(prepared(Other, 22))
        release.complete(Unit); advanceUntilIdle()
        assertTrue(gateway.commits.isEmpty())
        assertEquals(listOf<StoryDeleted?>(null), closed)
        assertEquals(StoryDeletionUiState(), controller.state.value)
        assertTrue(gateway.cancels >= 2)
    }

    @Test fun closeDuringNoncooperativeCommitWaitsAndReportsNoFalseRollback(): Unit = runTest {
        val gateway = Gateway(); val release = CompletableDeferred<Unit>(); var actuallyDeleted = false
        gateway.onCommit = { withContext(NonCancellable) { release.await(); actuallyDeleted = true; Deleted } }
        val closed = mutableListOf<StoryDeleted?>()
        val controller = StoryDeletionController(this, gateway, closed::add)
        controller.open(Story); advanceUntilIdle()
        val consent = controller.state.value.prepared!!
        controller.confirm(consent); runCurrent(); controller.dismiss(); runCurrent()
        assertTrue(closed.isEmpty())
        assertTrue(controller.state.value.notice!!.contains("may already have completed"))
        controller.confirm(consent); controller.open(Other)
        release.complete(Unit); advanceUntilIdle()
        assertTrue(actuallyDeleted)
        assertEquals(listOf(22L), gateway.commits)
        assertEquals(listOf<StoryDeleted?>(null), closed)
        assertNull(controller.state.value.deleted)
        assertFalse(controller.state.value.visible)
    }

    @Test fun disposalClosesGatewayOnceAndFencesLateCommitAndRetainedCallbacks(): Unit = runTest {
        val gateway = Gateway(); val release = CompletableDeferred<Unit>()
        gateway.onCommit = { withContext(NonCancellable) { release.await(); Deleted } }
        val controller = StoryDeletionController(this, gateway) { fail("Disposed callback published") }
        controller.open(Story); advanceUntilIdle()
        val consent = controller.state.value.prepared!!
        controller.confirm(consent); runCurrent(); controller.dismiss(); runCurrent()
        controller.dispose(); controller.dispose()
        repeat(2) { controller.open(Other); controller.confirm(consent); controller.cancel(); controller.dismiss() }
        release.complete(Unit); advanceUntilIdle()
        assertEquals(1, gateway.closes)
        assertEquals(1, gateway.prepares.size)
        assertEquals(listOf(22L), gateway.commits)
        assertEquals(StoryDeletionUiState(), controller.state.value)
    }

    @Test fun disposedNoncooperativePreviewCannotReviveConsent(): Unit = runTest {
        val gateway = Gateway(); val release = CompletableDeferred<Unit>()
        gateway.onPrepare = { withContext(NonCancellable) { release.await(); prepared(it, 22) } }
        val controller = StoryDeletionController(this, gateway) { fail("Disposed preview released") }
        controller.open(Story); runCurrent(); controller.dispose()
        release.complete(Unit); advanceUntilIdle()
        assertEquals(StoryDeletionUiState(), controller.state.value)
        assertEquals(1, gateway.closes)
        assertTrue(gateway.commits.isEmpty())
    }

    @Test fun preparationAndCommitFailuresUseOnlyFixedSanitizedGuidance(): Unit = runTest {
        val gateway = Gateway(); val controller = StoryDeletionController(this, gateway) {}
        gateway.onPrepare = { throw IllegalStateException("SECRET SELECT C:/private/story.sqlite3") }
        controller.open(Story); advanceUntilIdle()
        assertTrue(controller.state.value.notice!!.contains("could not be prepared"))
        assertFalse(controller.state.value.notice!!.contains("SECRET"))
        assertNull(controller.state.value.prepared)
        controller.dismiss(); advanceUntilIdle()
        gateway.onPrepare = { prepared(it, 22) }
        gateway.onCommit = { throw IllegalStateException("SECRET DELETE private path") }
        controller.open(Story); advanceUntilIdle()
        val consent = controller.state.value.prepared!!
        controller.confirm(consent); advanceUntilIdle(); controller.confirm(consent)
        assertTrue(controller.state.value.notice!!.contains("may already have completed"))
        assertFalse(controller.state.value.notice!!.contains("SECRET"))
        assertNull(controller.state.value.prepared)
        assertEquals(listOf(22L), gateway.commits)
        assertEquals("Story deletion failed", StoryDeletionFailure("SECRET").message)
    }

    private class Gateway : StoryDeletionGateway {
        val prepares = mutableListOf<SavedStory>(); val commits = mutableListOf<Long>()
        var cancels = 0; var closes = 0
        var onPrepare: suspend (SavedStory) -> StoryDeletionPrepared = { prepared(it, 22) }
        var onCommit: suspend (Long) -> StoryDeleted = { Deleted }
        override suspend fun prepare(story: SavedStory): StoryDeletionPrepared { prepares += story; return onPrepare(story) }
        override suspend fun commit(token: Long): StoryDeleted { commits += token; return onCommit(token) }
        override fun cancel() { cancels++ }
        override fun close() { closes++ }
    }
    private companion object {
        val Story = SavedStory("synthetic-delete", "main", "Synthetic deletion", 4)
        val Other = Story.copy(story = "synthetic-other")
        val Deleted = StoryDeleted(Story.story, 2, 12)
        fun preview(story: SavedStory) = StoryDeletionPreview(1, story.story, story.title, "main", mapOf("main" to story.revision),
            12, 3, 5, 7, mapOf("events" to 21L, "derived_packets" to 7L), "Synthetic native privacy warning")
        fun prepared(story: SavedStory, token: Long) = StoryDeletionPrepared(token, preview(story))
    }
}

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

/** Fake-port ownership/consent controls, not native creation or gameplay evidence. Author UNRUN. */
@OptIn(ExperimentalCoroutinesApi::class)
class StoryCreationControllerTest {
    private companion object {
        val Preview = StoryCreationPreview("lantern-quay-v1", "a".repeat(64), "The Lantern Quay",
            "A built-in starter.", "fantasy_v1", listOf("You are Rowan.", "You carry one potion."))
        val Saved = SavedSnapshot(0, "You", emptyList(), "synthetic", 1,
            listOf(SavedStory("quay-synthetic", "main", "Reviewed title", 0)),
            SavedStory("quay-synthetic", "main", "Reviewed title", 0))
    }
    private class Gateway : StoryCreationGateway {
        var previews = 0
        val requests = mutableListOf<StoryCreationRequest>()
        var read: suspend () -> StoryCreationPreview = { Preview }
        var write: suspend (StoryCreationRequest) -> SavedSnapshot = { Saved }
        override suspend fun preview(): StoryCreationPreview { previews++; return read() }
        override suspend fun create(request: StoryCreationRequest): SavedSnapshot { requests += request; return write(request) }
    }

    @Test fun openingAndCancellingReadOnlyReviewNeverCreatesOrRequestsRefresh() = runTest {
        val gateway = Gateway()
        val closed = mutableListOf<StoryCreationClose>()
        val controller = StoryCreationController(gateway, this, closed::add)
        try {
            controller.open(); controller.open()
            assertTrue(controller.state.value.busy)
            advanceUntilIdle()
            val request = controller.state.value.review!!
            assertTrue(Regex("[0-9a-f]{32}").matches(request.creationId))
            assertEquals(Preview.defaultTitle, request.title)
            assertEquals(1, gateway.previews); assertTrue(gateway.requests.isEmpty())
            controller.dismiss(); controller.dismiss(); advanceUntilIdle()
            assertEquals(listOf(StoryCreationClose()), closed)
            assertFalse(controller.state.value.visible)
            assertTrue(gateway.requests.isEmpty())
        } finally { controller.dispose() }
    }

    @Test fun sameRenderTitleEditsUseLatestTextButOldOrEqualCopyConsentCannotCreate() = runTest {
        val gateway = Gateway()
        val closed = mutableListOf<StoryCreationClose>()
        val controller = StoryCreationController(gateway, this, closed::add)
        try {
            controller.open(); advanceUntilIdle()
            val rendered = controller.state.value.review!!
            controller.editTitle(rendered, "First edit")
            controller.editTitle(rendered, "Latest edit")
            val latest = controller.state.value.review!!
            assertEquals("Latest edit", latest.title)
            assertEquals(rendered.creationId, latest.creationId)
            assertSame(rendered.preview, latest.preview)
            controller.confirm(rendered); controller.confirm(latest.copy()); runCurrent()
            assertTrue(gateway.requests.isEmpty())
            assertSame(latest, controller.state.value.review)
            controller.confirm(latest); controller.confirm(latest)
            assertNull(controller.state.value.review)
            advanceUntilIdle()
            assertEquals(1, gateway.requests.size); assertSame(latest, gateway.requests.single())
            assertEquals(listOf(StoryCreationClose(saved = Saved)), closed)
            assertFalse(controller.state.value.visible)
            controller.confirm(latest); advanceUntilIdle()
            assertEquals(1, gateway.requests.size)
        } finally { controller.dispose() }
    }

    @Test fun titleBoundaryRefusesUnsafeInputWithoutTruncationOrWriting() = runTest {
        val gateway = Gateway()
        val controller = StoryCreationController(gateway, this) {}
        try {
            controller.open(); advanceUntilIdle()
            val rendered = controller.state.value.review!!
            val wave = String(Character.toChars(0x1f30a))
            for (invalid in listOf("", " leading", "trailing ", "line\nbreak", "tab\t", "nul\u0000", "x\u202e", "x\u2066",
                "\uD800", "\uDC00", "a".repeat(81), wave.repeat(81))) {
                controller.editTitle(rendered, invalid)
                val current = controller.state.value.review!!
                assertEquals(invalid, current.title)
                controller.confirm(current); runCurrent()
                assertTrue(gateway.requests.isEmpty())
                assertSame(current, controller.state.value.review)
            }
            controller.editTitle(rendered, wave.repeat(80))
            val valid = controller.state.value.review!!
            assertEquals(320, valid.title.toByteArray(Charsets.UTF_8).size)
            controller.confirm(valid); advanceUntilIdle()
            assertSame(valid, gateway.requests.single())
        } finally { controller.dispose() }
    }

    @Test fun previewDetailsAreCopiedAndFrozenEvenWhenThePortReusesMutableMetadata() = runTest {
        val details = mutableListOf("Original player detail")
        val original = Preview.copy(details = details)
        val gateway = Gateway().also { it.read = { original } }
        val controller = StoryCreationController(gateway, this) {}
        try {
            controller.open(); advanceUntilIdle()
            val first = controller.state.value.review!!
            assertNotSame(original, first.preview)
            details[0] = "Changed port value"
            assertEquals(listOf("Original player detail"), first.preview.details)
            try { (first.preview.details as MutableList<String>).add("forbidden"); fail("Mutable captured details") }
            catch (_: UnsupportedOperationException) { }
            controller.dismiss(); advanceUntilIdle()
            controller.open(); advanceUntilIdle()
            val second = controller.state.value.review!!
            assertNotSame(first.preview, second.preview)
            assertNotEquals(first.creationId, second.creationId)
            controller.editTitle(first, "Stale edit")
            controller.editTitle(first.copy(creationId = second.creationId), "Forged new ID")
            controller.confirm(first)
            assertSame(second, controller.state.value.review)
            assertTrue(gateway.requests.isEmpty())
        } finally { controller.dispose() }
    }

    @Test fun foreignPreviewOrCreationIdentityCannotEditOrConfirmAnotherReview() = runTest {
        val gateway = Gateway()
        val first = StoryCreationController(gateway, this) {}
        val second = StoryCreationController(gateway, this) {}
        try {
            first.open(); second.open(); advanceUntilIdle()
            val current = first.state.value.review!!
            val foreign = second.state.value.review!!
            first.editTitle(foreign, "Wrong owner")
            first.editTitle(current.copy(creationId = foreign.creationId), "Wrong ID")
            first.confirm(foreign); first.confirm(current.copy())
            assertSame(current, first.state.value.review)
            assertTrue(gateway.requests.isEmpty())
        } finally { first.dispose(); second.dispose() }
    }

    @Test fun cancelledNoncooperativePreviewDrainsBeforeCloseOrReopenAndNeverPublishes() = runTest {
        val ready = CompletableDeferred<StoryCreationPreview>()
        val gateway = Gateway().also { it.read = { withContext(NonCancellable) { ready.await() } } }
        val closed = mutableListOf<StoryCreationClose>()
        val controller = StoryCreationController(gateway, this, closed::add)
        try {
            controller.open(); runCurrent()
            controller.dismiss(); runCurrent()
            assertTrue(controller.state.value.closing); assertTrue(closed.isEmpty())
            controller.open(); runCurrent(); assertEquals(1, gateway.previews)
            ready.complete(Preview); advanceUntilIdle()
            assertEquals(listOf(StoryCreationClose()), closed)
            assertNull(controller.state.value.review); assertFalse(controller.state.value.visible)
            assertTrue(gateway.requests.isEmpty())
        } finally { ready.complete(Preview); controller.dispose() }
    }

    @Test fun cancelAfterCreateWaitsForFiniteWorkAndRefreshesWithoutLatePublicationOrRetry() = runTest {
        val ready = CompletableDeferred<SavedSnapshot>()
        val gateway = Gateway().also { it.write = { withContext(NonCancellable) { ready.await() } } }
        val closed = mutableListOf<StoryCreationClose>()
        val controller = StoryCreationController(gateway, this, closed::add)
        try {
            controller.open(); advanceUntilIdle()
            val request = controller.state.value.review!!
            controller.confirm(request); runCurrent()
            assertTrue(controller.state.value.creating)
            controller.dismiss(); controller.dismiss(); runCurrent()
            assertTrue(controller.state.value.closing); assertTrue(closed.isEmpty())
            controller.confirm(request); controller.open()
            ready.complete(Saved); advanceUntilIdle()
            assertEquals(listOf(StoryCreationClose(refreshRequired = true)), closed)
            assertSame(request, gateway.requests.single())
            assertFalse(controller.state.value.visible)
        } finally { ready.complete(Saved); controller.dispose() }
    }

    @Test fun createFailureConsumesConsentAndRequiresRefreshWithoutLeakingExceptionOrRetrying() = runTest {
        val gateway = Gateway().also { it.write = { error("PRIVATE_source_path_or_title") } }
        val closed = mutableListOf<StoryCreationClose>()
        val controller = StoryCreationController(gateway, this, closed::add)
        try {
            controller.open(); advanceUntilIdle()
            val request = controller.state.value.review!!
            controller.confirm(request); advanceUntilIdle()
            assertTrue(controller.state.value.visible)
            assertFalse(controller.state.value.busy)
            assertNull(controller.state.value.review)
            assertTrue(controller.state.value.notice!!.contains("may already exist"))
            assertFalse(controller.state.value.notice!!.contains("PRIVATE"))
            controller.confirm(request); controller.editTitle(request, "Retry"); controller.open(); advanceUntilIdle()
            assertEquals(1, gateway.requests.size); assertEquals(1, gateway.previews)
            controller.dismiss(); advanceUntilIdle()
            assertEquals(listOf(StoryCreationClose(refreshRequired = true)), closed)
        } finally { controller.dispose() }
    }

    @Test fun failedReadCanCloseWithoutRefreshButCannotBorrowAnOldConfirmation() = runTest {
        val gateway = Gateway().also { it.read = { error("PRIVATE_native_exception") } }
        val closed = mutableListOf<StoryCreationClose>()
        val controller = StoryCreationController(gateway, this, closed::add)
        try {
            controller.open(); advanceUntilIdle()
            assertNull(controller.state.value.review)
            assertFalse(controller.state.value.busy)
            assertFalse(controller.state.value.notice!!.contains("PRIVATE"))
            controller.confirm(StoryCreationRequest(Preview, "Unreviewed", "a".repeat(32)))
            assertTrue(gateway.requests.isEmpty())
            controller.dismiss(); advanceUntilIdle()
            assertEquals(listOf(StoryCreationClose()), closed)
        } finally { controller.dispose() }
    }

    @Test fun disposalFencesNoncooperativeReadAndCreateResultsWithoutClosingAnotherOwner() = runTest {
        for (duringCreate in listOf(false, true)) {
            val read = CompletableDeferred<StoryCreationPreview>()
            val write = CompletableDeferred<SavedSnapshot>()
            val gateway = Gateway()
            if (duringCreate) gateway.write = { withContext(NonCancellable) { write.await() } }
            else gateway.read = { withContext(NonCancellable) { read.await() } }
            val closed = mutableListOf<StoryCreationClose>()
            val controller = StoryCreationController(gateway, this, closed::add)
            try {
                controller.open(); runCurrent()
                if (duringCreate) controller.confirm(controller.state.value.review!!)
                runCurrent(); controller.dispose(); controller.dispose()
                read.complete(Preview); write.complete(Saved); advanceUntilIdle()
                controller.open(); controller.dismiss(); advanceUntilIdle()
                assertTrue(closed.isEmpty()); assertFalse(controller.state.value.visible)
                assertEquals(if (duringCreate) 1 else 0, gateway.requests.size)
                assertEquals(1, gateway.previews)
            } finally { read.complete(Preview); write.complete(Saved); controller.dispose() }
        }
    }
}

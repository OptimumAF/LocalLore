/* Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0 */
package org.locallore.app

import androidx.lifecycle.ViewModelStore
import kotlinx.coroutines.CompletableDeferred
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.ExperimentalCoroutinesApi
import kotlinx.coroutines.NonCancellable
import kotlinx.coroutines.test.*
import kotlinx.coroutines.withContext
import org.junit.After
import org.junit.Assert.*
import org.junit.Before
import org.junit.Test

/** Production Gateway+VM over native captured wire graphs; no native inference or persistence. */
@OptIn(ExperimentalCoroutinesApi::class)
class PlayerPresentationTimelineAdversarialTest {
    private val dispatcher = StandardTestDispatcher()
    private val stores = ViewModelStore()
    @Before fun setup() { Dispatchers.setMain(dispatcher) }
    @After fun close() { stores.clear(); Dispatchers.resetMain() }
    private fun model(transport: PresentationCaptureTransport) =
        ShellViewModel(transport.gateway()).also { stores.put("presentation", it) }
    private fun assertSelected(model: ShellViewModel, case: PresentationCapturedCase) {
        assertFalse(model.state.value.busy); assertFalse(model.state.value.recoveryRequired)
        assertEquals(case.story, model.state.value.selectedStory!!.story)
        assertEquals(case.branch, model.state.value.selectedStory!!.branch)
        assertEquals(case.revision, model.state.value.revision)
        assertCapturedPresentation(model.state.value.messages, case)
    }

    @Test fun exactCurrentTimelineObjectsNavigateAllGenuineHeadsWithoutMutatingAcceptedTurns() = runTest(dispatcher) {
        val corpus = PresentationCaptureCorpus(); val transport = PresentationCaptureTransport(corpus)
        val model = model(transport); advanceUntilIdle(); assertSelected(model, corpus.case("main"))
        for (id in listOf("corrected", "rediscovered", "main")) {
            val case = corpus.case(id)
            val current = model.state.value.timelines.single { it.story == case.story && it.branch == case.branch }
            model.resumeTimeline(current); advanceUntilIdle(); assertSelected(model, case)
        }
        transport.assertReadOnly(); corpus.assertUnchanged()
    }

    @Test fun equalButDistinctAndPreviouslyRenderedTimelineObjectsCannotDispatchAResume() = runTest(dispatcher) {
        val corpus = PresentationCaptureCorpus(); val transport = PresentationCaptureTransport(corpus)
        val model = model(transport); advanceUntilIdle(); assertSelected(model, corpus.case("main"))
        val old = model.state.value.timelines.single { it.branch == corpus.case("corrected").branch }
        val count = transport.resumes.size
        model.resumeTimeline(old.copy()); advanceUntilIdle(); assertEquals(count, transport.resumes.size)
        model.recover(); advanceUntilIdle(); assertSelected(model, corpus.case("main"))
        val fresh = model.state.value.timelines.single { it.branch == corpus.case("corrected").branch }
        assertEquals(old, fresh); assertNotSame(old, fresh)
        model.resumeTimeline(old); advanceUntilIdle(); assertEquals(count, transport.resumes.size)
        model.resumeTimeline(fresh); advanceUntilIdle(); assertEquals(count + 1, transport.resumes.size)
        assertSelected(model, corpus.case("corrected")); transport.assertReadOnly()
    }

    @Test fun aRetainedTimelineFromAnotherCapturedStoryHasNoCurrentSelectionAuthority() = runTest(dispatcher) {
        val corpus = PresentationCaptureCorpus(); val transport = PresentationCaptureTransport(corpus)
        val model = model(transport); advanceUntilIdle(); assertSelected(model, corpus.case("main"))
        val stale = model.state.value.timelines.single { it.branch == corpus.case("corrected").branch }
        val other = corpus.case("empty")
        assertNotEquals(stale.story, other.story)
        model.resume(other.saved()); advanceUntilIdle(); assertSelected(model, other)
        val count = transport.resumes.size
        model.resumeTimeline(stale); advanceUntilIdle(); assertEquals(count, transport.resumes.size)
        assertSelected(model, other); transport.assertReadOnly()
    }

    @Test fun busyAndDisposedViewsFenceNonCooperativeLateNativePresentationReplies() = runTest(dispatcher) {
        val corpus = PresentationCaptureCorpus(); val transport = PresentationCaptureTransport(corpus)
        val model = model(transport); advanceUntilIdle(); assertSelected(model, corpus.case("main"))
        val before = model.state.value
        val child = before.timelines.single { it.branch == corpus.case("corrected").branch }
        val entered = CompletableDeferred<Unit>(); val release = CompletableDeferred<Unit>()
        transport.beforePresentation = { entered.complete(Unit); withContext(NonCancellable) { release.await() } }
        try {
            model.resumeTimeline(child); runCurrent(); assertTrue(entered.isCompleted); assertTrue(model.state.value.busy)
            val count = transport.resumes.size
            model.resumeTimeline(child); runCurrent(); assertEquals(count, transport.resumes.size)
            stores.clear(); release.complete(Unit); advanceUntilIdle()
            assertEquals(before.selectedStory, model.state.value.selectedStory)
            assertEquals(before.revision, model.state.value.revision)
            assertEquals(before.messages, model.state.value.messages)
            assertEquals(1, transport.closes)
            model.resumeTimeline(child); advanceUntilIdle(); assertEquals(count, transport.resumes.size)
            transport.assertReadOnly()
        } finally { release.complete(Unit); stores.clear() }
    }

    @Test fun malformedNewHeadRetainsOldPresentationAndRequiresExplicitValidRecovery() = runTest(dispatcher) {
        val corpus = PresentationCaptureCorpus(); val transport = PresentationCaptureTransport(corpus)
        val model = model(transport); advanceUntilIdle(); assertSelected(model, corpus.case("main"))
        val before = model.state.value
        val child = before.timelines.single { it.branch == corpus.case("corrected").branch }
        transport.mutateNext = { it.put("private_author_payload", "PRIVATE_MALFORMED_PRESENTATION") }
        model.resumeTimeline(child); advanceUntilIdle()
        assertTrue(model.state.value.recoveryRequired)
        assertEquals(before.selectedStory, model.state.value.selectedStory)
        assertEquals(before.messages, model.state.value.messages)
        assertFalse(model.state.value.notice.orEmpty().contains("PRIVATE_MALFORMED_PRESENTATION"))
        val count = transport.resumes.size
        model.resumeTimeline(child); advanceUntilIdle(); assertEquals(count, transport.resumes.size)
        model.recover(); advanceUntilIdle(); assertSelected(model, corpus.case("corrected"))
        transport.assertReadOnly()
    }
}

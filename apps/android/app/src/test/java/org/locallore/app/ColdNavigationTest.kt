/* Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0 */
package org.locallore.app

import androidx.lifecycle.ViewModelStore
import java.io.IOException
import kotlinx.coroutines.CancellationException
import kotlinx.coroutines.CompletableDeferred
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.ExperimentalCoroutinesApi
import kotlinx.coroutines.test.StandardTestDispatcher
import kotlinx.coroutines.test.advanceUntilIdle
import kotlinx.coroutines.test.resetMain
import kotlinx.coroutines.test.runCurrent
import kotlinx.coroutines.test.runTest
import kotlinx.coroutines.test.setMain
import org.junit.After
import org.junit.Assert.assertArrayEquals
import org.junit.Assert.assertEquals
import org.junit.Assert.assertFalse
import org.junit.Assert.assertNull
import org.junit.Assert.assertSame
import org.junit.Assert.assertTrue
import org.junit.Before
import org.junit.Test

/** Startup and selection history over the existing captured native catalogs and replies. */
@OptIn(ExperimentalCoroutinesApi::class)
class ColdNavigationTest {
    private val dispatcher = StandardTestDispatcher()
    private val models = ViewModelStore()

    @Before fun setUp() { Dispatchers.setMain(dispatcher) }

    @After fun cleanUp() {
        models.clear()
        Dispatchers.resetMain()
    }

    private class MemoryNavigation(var value: PlayDraftScope? = null) : SavedNavigationStore {
        var loads = 0
        var failure: Exception? = null
        var beforeSave: suspend (PlayDraftScope?) -> Unit = {}
        val started = mutableListOf<PlayDraftScope?>()
        val completed = mutableListOf<PlayDraftScope?>()

        override suspend fun load(): PlayDraftScope? {
            loads++
            failure?.let { throw it }
            return value
        }

        override suspend fun save(value: PlayDraftScope?) {
            started += value
            beforeSave(value)
            this.value = value
            completed += value
        }
    }

    private fun PresentationCapturedCase.navigation() = PlayDraftScope(story, branch)

    private fun PresentationCaptureTransport.coldGateway(
        store: SavedNavigationStore? = null,
        taskHint: PlayDraftScope? = null,
    ) = DurableGateway(this, autoCreateIfEmpty = false, initialScopeHint = taskHint, navigationStore = store)

    private fun model(gateway: DurableGateway, store: SavedNavigationStore): ShellViewModel =
        ShellViewModel(gateway, navigationStore = store).also { models.put("shell", it) }

    @Test fun freshOwnerUsesExactStoredTimelineInsteadOfTheFirstCatalogStory() = runTest(dispatcher) {
        val corpus = PresentationCaptureCorpus()
        val target = corpus.case("corrected")
        val control = PresentationCaptureTransport(corpus)
        val cold = PresentationCaptureTransport(corpus)
        val store = MemoryNavigation(target.navigation())
        val withoutHint = control.coldGateway()
        val withHint = cold.coldGateway(store)
        try {
            assertEquals(corpus.case("empty").saved(), initializeCaptured(withoutHint).selected)
            assertEquals(listOf(corpus.case("empty").navigation()), control.resumes)

            val selected = initializeCaptured(withHint)
            assertEquals(target.saved(), selected.selected)
            assertFalse(selected.selectionRestoreUnavailable)
            assertCapturedPresentation(selected.messages, target)
            assertEquals(listOf(target.navigation()), cold.resumes)
            assertEquals(listOf("workspace", "branches", "resume", "open", "play_presentation_v2"),
                cold.commands.take(5).map { it.getString("op") })
            assertEquals(target.saved(), initializeCaptured(withHint).selected)
            assertEquals(1, store.loads)
            control.assertReadOnly()
            cold.assertReadOnly()
            corpus.assertUnchanged()
        } finally {
            withoutHint.close()
            withHint.close()
        }
    }

    @Test fun aValidSavedTaskHintTakesPrecedenceWithoutReadingTheColdHint() = runTest(dispatcher) {
        val corpus = PresentationCaptureCorpus()
        val disk = corpus.case("corrected")
        val task = corpus.case("rediscovered")
        val port = PresentationCaptureTransport(corpus)
        val store = MemoryNavigation(disk.navigation())
        val gateway = port.coldGateway(store, task.navigation())
        try {
            assertEquals(task.saved(), initializeCaptured(gateway).selected)
            assertEquals(listOf(task.navigation()), port.resumes)
            assertEquals(0, store.loads)
            port.assertReadOnly()
        } finally {
            gateway.close()
        }
    }

    @Test fun unavailableTimelineFallsBackVisiblyWithoutRememberingTheFallback() = runTest(dispatcher) {
        val corpus = PresentationCaptureCorpus()
        val previous = PlayDraftScope(corpus.case("main").story, "retired-child")
        val port = PresentationCaptureTransport(corpus)
        val store = MemoryNavigation(previous)
        val shell = model(port.coldGateway(store), store)
        advanceUntilIdle()

        val fallback = corpus.case("empty")
        assertEquals(fallback.saved(), shell.state.value.selectedStory)
        assertTrue(shell.state.value.notice.orEmpty().contains("Previously selected timeline is unavailable"))
        assertEquals(listOf(fallback.navigation()), port.resumes)
        assertEquals(previous, store.value)
        assertTrue(store.started.isEmpty())
        port.assertReadOnly()

        val explicit = corpus.case("corrected")
        shell.resume(explicit.saved())
        advanceUntilIdle()
        assertEquals(listOf(explicit.navigation()), store.completed)
        assertEquals(explicit.navigation(), store.value)
        assertEquals(explicit.saved(), shell.state.value.selectedStory)
        port.assertReadOnly()
    }

    @Test fun failedOptionalReadUsesTheNativeDefaultButCancellationPropagates() = runTest(dispatcher) {
        val corpus = PresentationCaptureCorpus()
        for (failure in listOf(IOException("Synthetic disk read failure"), SecurityException("Synthetic access refusal"))) {
            val port = PresentationCaptureTransport(corpus)
            val store = MemoryNavigation().apply { this.failure = failure }
            val gateway = port.coldGateway(store)
            try {
                assertEquals(corpus.case("empty").saved(), initializeCaptured(gateway).selected)
                assertEquals(1, store.loads)
                port.assertReadOnly()
            } finally {
                gateway.close()
            }
        }
        val port = PresentationCaptureTransport(corpus)
        val cancellation = CancellationException("Synthetic cancelled hint load")
        val store = MemoryNavigation().apply { failure = cancellation }
        val gateway = port.coldGateway(store)
        try {
            assertSame(cancellation, runCatching { gateway.initialize() }.exceptionOrNull())
            assertFalse(port.commands.any { it.getString("op") == "resume" })
        } finally {
            gateway.close()
        }
    }

    @Test fun storedCodecAcceptsOnlyTheBoundedVersionedPairOfIds() {
        val scope = PlayDraftScope("Story_A-1", "timeline-2")
        val expected = "1\nStory_A-1\ntimeline-2\n".toByteArray(Charsets.US_ASCII)
        assertArrayEquals(expected, encodeStoredNavigationHint(scope))
        assertEquals(scope, decodeStoredNavigationHint(expected))

        val maximum = PlayDraftScope("s".repeat(64), "b".repeat(64))
        val maximumBytes = checkNotNull(encodeStoredNavigationHint(maximum))
        assertEquals(132, maximumBytes.size)
        assertEquals(maximum, decodeStoredNavigationHint(maximumBytes))
        assertNull(encodeStoredNavigationHint(PlayDraftScope("story", "b".repeat(65))))
        for (malformed in listOf("", "2\nstory\nbranch\n", "01\nstory\nbranch\n", "1\nstory\nbranch",
            "1\r\nstory\r\nbranch\r\n", "1\nstory\nbranch\nextra\n", "1\n../story\nbranch\n",
            "1\n\nbranch\n", "1\nstory\nbranch\u0000\n", "1\nstory\nbrånch\n")) {
            assertNull("Accepted invalid hint bytes", decodeStoredNavigationHint(malformed.toByteArray()))
        }
        assertNull(decodeStoredNavigationHint(maximumBytes + 'x'.code.toByte()))
    }

    @Test fun onlyConfirmedSelectionsAreWrittenAndASlowWriteCannotRetargetTheNextLaunch() = runTest(dispatcher) {
        val corpus = PresentationCaptureCorpus()
        val initial = corpus.case("main")
        val selected = corpus.case("corrected")
        val presentationGate = CompletableDeferred<Unit>()
        val firstSaveGate = CompletableDeferred<Unit>()
        val store = MemoryNavigation().apply {
            beforeSave = { if (it == initial.navigation()) firstSaveGate.await() }
        }
        val port = PresentationCaptureTransport(corpus).apply {
            beforePresentation = { presentationGate.await() }
        }
        val shell = model(port.coldGateway(store, initial.navigation()), store)
        try {
            runCurrent()
            assertTrue(shell.state.value.busy)
            assertNull(shell.state.value.selectedStory)
            assertTrue(store.started.isEmpty())

            presentationGate.complete(Unit)
            runCurrent()
            assertEquals(initial.saved(), shell.state.value.selectedStory)
            assertEquals(listOf(initial.navigation()), store.started)
            assertTrue(store.completed.isEmpty())

            shell.resume(selected.saved())
            runCurrent()
            assertEquals(selected.saved(), shell.state.value.selectedStory)
            assertEquals(listOf(initial.navigation()), store.started)

            firstSaveGate.complete(Unit)
            advanceUntilIdle()
            assertEquals(listOf(initial.navigation(), selected.navigation()), store.completed)
            shell.recover()
            advanceUntilIdle()
            assertEquals(store.completed, store.started)
            assertEquals(2, store.completed.size)
            port.assertReadOnly()
        } finally {
            presentationGate.complete(Unit)
            firstSaveGate.complete(Unit)
        }

        models.clear()
        val fresh = PresentationCaptureTransport(corpus)
        val reopened = model(fresh.coldGateway(store), store)
        advanceUntilIdle()
        assertEquals(selected.saved(), reopened.state.value.selectedStory)
        assertEquals(listOf(selected.navigation()), fresh.resumes)
        fresh.assertReadOnly()
    }

    @Test fun unreadableNativePresentationDoesNotPersistAnUnconfirmedSelection() = runTest(dispatcher) {
        val corpus = PresentationCaptureCorpus()
        val target = corpus.case("corrected")
        val port = PresentationCaptureTransport(corpus).apply {
            mutateNext = { it.remove("scope") }
        }
        val store = MemoryNavigation(target.navigation())
        val shell = model(port.coldGateway(store), store)
        advanceUntilIdle()

        assertTrue(shell.state.value.recoveryRequired)
        assertNull(shell.state.value.selectedStory)
        assertTrue(store.started.isEmpty())

        shell.recover()
        advanceUntilIdle()
        assertFalse(shell.state.value.recoveryRequired)
        assertEquals(target.saved(), shell.state.value.selectedStory)
        assertEquals(listOf(target.navigation()), store.completed)
        port.assertReadOnly()
    }

    @Test fun uncertainWriteAcknowledgementCannotDeduplicateALaterReturnToTheOldTimeline() = runTest(dispatcher) {
        val corpus = PresentationCaptureCorpus()
        val initial = corpus.case("main")
        val selected = corpus.case("corrected")
        val port = PresentationCaptureTransport(corpus)
        val store = MemoryNavigation()
        store.beforeSave = { hint ->
            if (hint == selected.navigation()) {
                store.value = hint
                throw IOException("Synthetic write acknowledgement lost after publication")
            }
        }
        val shell = model(port.coldGateway(store, initial.navigation()), store)
        advanceUntilIdle()
        assertEquals(listOf(initial.navigation()), store.completed)

        shell.resume(selected.saved())
        advanceUntilIdle()
        assertEquals(selected.saved(), shell.state.value.selectedStory)
        assertFalse(shell.state.value.recoveryRequired)
        assertEquals(selected.navigation(), store.value)

        shell.resume(initial.saved())
        advanceUntilIdle()
        assertEquals(initial.saved(), shell.state.value.selectedStory)
        assertEquals(initial.navigation(), store.value)
        assertEquals(listOf(initial.navigation(), selected.navigation(), initial.navigation()), store.started)
        assertEquals(listOf(initial.navigation(), initial.navigation()), store.completed)
        port.assertReadOnly()
    }
}

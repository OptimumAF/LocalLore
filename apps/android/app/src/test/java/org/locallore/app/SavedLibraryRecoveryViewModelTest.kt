/* Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0 */
package org.locallore.app

import androidx.lifecycle.ViewModelStore
import kotlinx.coroutines.CompletableDeferred
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.ExperimentalCoroutinesApi
import kotlinx.coroutines.NonCancellable
import kotlinx.coroutines.test.StandardTestDispatcher
import kotlinx.coroutines.test.advanceUntilIdle
import kotlinx.coroutines.test.resetMain
import kotlinx.coroutines.test.runCurrent
import kotlinx.coroutines.test.runTest
import kotlinx.coroutines.test.setMain
import kotlinx.coroutines.withContext
import org.junit.After
import org.junit.Assert.assertEquals
import org.junit.Assert.assertFalse
import org.junit.Assert.assertNull
import org.junit.Assert.assertTrue
import org.junit.Before
import org.junit.Test
import org.locallore.app.ui.SavedLibraryStatus
import org.locallore.app.ui.savedLibraryStatus

@OptIn(ExperimentalCoroutinesApi::class)
class SavedLibraryRecoveryViewModelTest {
    private val dispatcher = StandardTestDispatcher()
    private val store = ViewModelStore()
    private val emptyLibrary = SavedSnapshot(
        revision = 0,
        potionOwner = "",
        messages = emptyList(),
        location = "/synthetic/no-backup/stories.sqlite3",
        schemaVersion = 1,
        stories = emptyList(),
        selected = null,
        databaseSchemaVersion = 5,
    )
    private val story = SavedStory("retained", "child", "Rain and Lanterns", 7)
    private val retainedLibrary = emptyLibrary.copy(
        revision = story.revision,
        potionOwner = "Mira",
        messages = listOf(SceneMessage(1, "Accepted narration", false)),
        stories = listOf(story),
        selected = story,
        uncommittedDrafts = 2,
        rulesProfile = "fantasy_v1",
        textProvider = TextProvider.SCRIPTED,
        timelines = listOf(SavedTimeline(story.story, story.branch, "main", 3, story.revision, 2)),
    )
    private val recoveryNotice =
        "Saved progress could not be confirmed. Retry recovery; existing saves are retained."

    @Before
    fun setup() {
        Dispatchers.setMain(dispatcher)
    }

    @After
    fun cleanup() {
        store.clear()
        Dispatchers.resetMain()
    }

    private fun model(gateway: DemoGateway) = ShellViewModel(gateway).also { store.put("model", it) }

    private class TestGateway(
        var open: suspend () -> SavedSnapshot?,
        var recover: suspend () -> SavedSnapshot? = { error("Unexpected recovery") },
    ) : DemoGateway {
        override val durable = true
        var openings = 0
            private set
        var recoveries = 0
            private set
        var closes = 0
            private set

        override suspend fun initialize(): SavedSnapshot? {
            openings++
            return open()
        }

        override suspend fun recoverSaved(): SavedSnapshot? {
            recoveries++
            return recover()
        }

        override suspend fun respond(action: DemoAction, revision: Long, mode: DemoMode): DemoResult =
            error("Unexpected turn")

        override fun close() {
            closes++
        }
    }

    @Test
    fun heldStartupOffersEmptyLibraryOnlyAfterConfirmedSnapshot() = runTest(dispatcher) {
        val startup = CompletableDeferred<SavedSnapshot?>()
        val gateway = TestGateway(open = { startup.await() })
        val model = model(gateway)
        runCurrent()

        val opening = model.state.value
        assertTrue(opening.busy)
        assertNull(opening.schemaVersion)
        assertNull(savedLibraryStatus(opening))

        startup.complete(emptyLibrary)
        advanceUntilIdle()

        val opened = model.state.value
        assertFalse(opened.busy)
        assertFalse(opened.recoveryRequired)
        assertEquals("Local saved library opened.", opened.notice)
        assertEquals(SavedLibraryStatus.EMPTY, savedLibraryStatus(opened))
        assertEquals(1, gateway.openings)
    }

    @Test
    fun missingStartupSnapshotRequiresRecoveryAndRetryOpensTheLibraryAgain() = runTest(dispatcher) {
        val gateway = TestGateway(open = { null })
        val model = model(gateway)
        advanceUntilIdle()

        val missing = model.state.value
        assertTrue(missing.recoveryRequired)
        assertFalse(missing.busy)
        assertEquals(recoveryNotice, missing.notice)
        assertNull(missing.storageLocation)
        assertNull(savedLibraryStatus(missing))

        val retry = CompletableDeferred<SavedSnapshot?>()
        gateway.open = { retry.await() }
        model.recover()
        runCurrent()
        assertTrue(model.state.value.busy)
        assertNull(savedLibraryStatus(model.state.value))
        assertEquals(2, gateway.openings)
        assertEquals(0, gateway.recoveries)

        retry.complete(emptyLibrary)
        advanceUntilIdle()
        assertFalse(model.state.value.recoveryRequired)
        assertEquals("Saved progress recovered.", model.state.value.notice)
        assertEquals(SavedLibraryStatus.EMPTY, savedLibraryStatus(model.state.value))
    }

    @Test
    fun missingRecoverySnapshotRetainsLastConfirmedStateUntilSuccessfulRetry() = runTest(dispatcher) {
        val recovery = CompletableDeferred<SavedSnapshot?>()
        val gateway = TestGateway(open = { retainedLibrary }, recover = { recovery.await() })
        val model = model(gateway)
        advanceUntilIdle()
        val confirmed = model.state.value
        assertEquals(retainedLibrary.messages, confirmed.messages)
        assertEquals(story, confirmed.selectedStory)

        model.recover()
        runCurrent()
        assertTrue(model.state.value.busy)
        assertEquals(confirmed.messages, model.state.value.messages)
        recovery.complete(null)
        advanceUntilIdle()

        assertEquals(confirmed.copy(recoveryRequired = true, notice = recoveryNotice), model.state.value)
        assertNull(savedLibraryStatus(model.state.value))
        assertEquals(1, gateway.openings)
        assertEquals(1, gateway.recoveries)

        gateway.recover = { retainedLibrary }
        model.recover()
        advanceUntilIdle()
        assertEquals(confirmed.copy(notice = "Saved progress recovered."), model.state.value)
        assertEquals(1, gateway.openings)
        assertEquals(2, gateway.recoveries)
    }

    @Test
    fun failedRecoverySuppressesEmptyAdviceEvenWithPreviouslyConfirmedEmptyCatalog() = runTest(dispatcher) {
        val gateway = TestGateway(open = { emptyLibrary }, recover = { throw WorkspaceFailure("Busy") })
        val model = model(gateway)
        advanceUntilIdle()
        val confirmed = model.state.value
        assertEquals(SavedLibraryStatus.EMPTY, savedLibraryStatus(confirmed))

        model.recover()
        advanceUntilIdle()

        val failed = model.state.value
        assertEquals(
            confirmed.copy(
                recoveryRequired = true,
                notice = "The local engine is busy. Wait briefly, then retry recovery. Saved progress is retained.",
            ),
            failed,
        )
        assertNull(savedLibraryStatus(failed))
    }

    @Test
    fun disposalFencesRetainedNullRecoveryFromChangingPresentedHistory() = runTest(dispatcher) {
        val recovery = CompletableDeferred<SavedSnapshot?>()
        val gateway = TestGateway(
            open = { retainedLibrary },
            recover = { withContext(NonCancellable) { recovery.await() } },
        )
        val model = model(gateway)
        advanceUntilIdle()
        model.recover()
        runCurrent()

        store.clear()
        val disposed = model.state.value
        model.recover()
        recovery.complete(null)
        advanceUntilIdle()

        assertEquals(disposed, model.state.value)
        assertEquals(retainedLibrary.messages, model.state.value.messages)
        assertEquals(1, gateway.recoveries)
        assertEquals(1, gateway.closes)
    }
}

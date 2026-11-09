/* Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0 */
package org.locallore.app

import androidx.compose.runtime.collectAsState
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.ui.test.*
import androidx.compose.ui.test.junit4.createComposeRule
import androidx.lifecycle.ViewModel
import androidx.lifecycle.ViewModelProvider
import androidx.lifecycle.ViewModelStore
import androidx.test.ext.junit.runners.AndroidJUnit4
import java.util.concurrent.CopyOnWriteArrayList
import java.util.concurrent.atomic.AtomicInteger
import kotlinx.coroutines.CancellationException
import kotlinx.coroutines.CompletableDeferred
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.NonCancellable
import kotlinx.coroutines.runBlocking
import kotlinx.coroutines.withContext
import kotlinx.coroutines.withTimeout
import org.junit.Assert.*
import org.junit.Rule
import org.junit.Test
import org.junit.runner.RunWith
import org.locallore.app.ui.LocalLoreScreen
import org.locallore.app.ui.LocalLoreTheme
import org.locallore.app.ui.StoryRecordHost

/** Real ShellViewModel/controller and production Compose; synthetic read ports only.
 * Source compilation is not Android execution, native cancellation or canonical evidence.
 */
@RunWith(AndroidJUnit4::class)
class StoryRecordCancellationScreenTest {
    @get:Rule val compose = createComposeRule()
    private val mounted = mutableStateOf<ShellViewModel?>(null)

    private fun content() = compose.setContent {
        LocalLoreTheme {
            mounted.value?.let { model ->
                val shell by model.state.collectAsState()
                LocalLoreScreen(shell, model::submit, model::setMode, model::cancel, model::reset,
                    onResume = model::resume, onRecover = model::recover,
                    onStoryRecord = model::openStoryRecord) {
                    StoryRecordHost(model)
                }
            }
        }
    }

    private fun <T> main(block: () -> T): T = runBlocking {
        withContext(Dispatchers.Main.immediate) { block() }
    }
    private fun shell(name: String): SemanticsNodeInteraction {
        compose.onNodeWithTag("story-list").performScrollToNode(hasTestTag(name))
        return compose.onNodeWithTag(name)
    }
    private fun record(name: String) = compose.onNodeWithTag(name).performScrollTo()
    private fun settled(model: ShellViewModel) {
        compose.waitUntil(8_000) { !model.state.value.busy && model.state.value.selectedStory != null }
        compose.waitForIdle()
        assertFalse(model.state.value.recoveryRequired)
    }
    private fun loaded(model: ShellViewModel, predicate: (StoryRecordState) -> Boolean = { true }) {
        compose.waitUntil(8_000) {
            val current = model.storyRecord.value
            current.visible && !current.loading && current.problem == null && predicate(current)
        }
        compose.waitForIdle()
    }
    private fun unavailable(model: ShellViewModel, detail: Boolean = false) {
        compose.waitUntil(8_000) {
            val current = model.storyRecord.value
            current.visible && if (detail) current.eventDetail?.let {
                !it.loading && it.problem == StoryRecordProblem.UNAVAILABLE
            } == true else !current.loading && current.problem == StoryRecordProblem.UNAVAILABLE
        }
        compose.waitForIdle()
        val tag = if (detail) "story-event-problem" else "story-record-problem"
        record(tag).assertIsDisplayed().assertTextEquals(StoryRecordProblem.UNAVAILABLE.message)
        compose.onNodeWithTag(if (detail) "story-event-loading" else "story-record-loading").assertDoesNotExist()
        record(if (detail) "story-event-retry" else "story-record-retry").assertIsEnabled()
        assertPrivateTextAbsent(model)
    }
    private fun assertPrivateTextAbsent(model: ShellViewModel) {
        assertFalse(model.storyRecord.value.toString().contains(PRIVATE))
        compose.onAllNodes(hasText(PRIVATE, substring = true), useUnmergedTree = true).assertCountEquals(0)
    }
    private fun open() = shell("story-record-open").assertIsEnabled().performClick()
    private fun closeRecord() {
        compose.onNodeWithTag("story-record-close").assertIsEnabled().performClick()
        compose.waitForIdle()
        compose.onNodeWithTag("story-record-dialog").assertDoesNotExist()
    }
    private fun gateEntered(gate: Gate) = compose.waitUntil(8_000) { gate.entered.isCompleted }
    private fun gateFinished(gate: Gate) {
        compose.waitUntil(8_000) { gate.finished.isCompleted }
        compose.waitForIdle()
    }
    private fun visibleLabel(text: String) {
        record("story-record-entry-0")
        compose.onNodeWithText(text, useUnmergedTree = true).performScrollTo().assertIsDisplayed()
    }

    @Test fun cancelledCurrentPageShowsSafeRetryAndReusesTheExactFrozenCursor() {
        val laterAttempts = AtomicInteger()
        val gateway = ReadGateway(STORY_A) { query ->
            if (query.cursor != null && laterAttempts.incrementAndGet() == 1)
                throw CancellationException("$PRIVATE /synthetic/unpublished/page")
            page(query, "Visible paged observation", paged = true)
        }
        val harness = Harness()
        try {
            content()
            val owner = harness.create(gateway); settled(owner.model)
            val originalShell = owner.model.state.value
            val saved = gateway.saved
            open(); loaded(owner.model)
            val first = owner.model.storyRecord.value
            assertEquals(StoryRecordContext(STORY_A, STORY_A.revision), first.context)
            assertEquals(CURSOR, first.nextCursor)
            record("story-record-next").assertIsEnabled().performClick()
            unavailable(owner.model)
            val failedQuery = gateway.queries.last()
            assertEquals(2, gateway.queries.size)
            assertEquals(CURSOR, failedQuery.cursor)
            assertEquals(2, failedQuery.version)
            assertEquals(StoryRecordSection.PROGRESSION, failedQuery.section)
            assertEquals("", failedQuery.search)
            assertEquals(first.context, failedQuery.context)
            assertEquals(CURSOR, owner.model.storyRecord.value.cursor)
            assertTrue(owner.model.storyRecord.value.entries.isEmpty())
            compose.waitForIdle()
            assertEquals("No automatic read follows cancellation", 2, gateway.queries.size)
            record("story-record-retry").performClick()
            loaded(owner.model) { it.cursor == CURSOR }
            assertEquals(3, gateway.queries.size)
            assertEquals(failedQuery, gateway.queries.last())
            visibleLabel("Visible paged observation")
            record("story-record-next").assertIsNotEnabled()
            assertPrivateTextAbsent(owner.model)
            closeRecord()
            harness.unchanged(owner, originalShell, saved)
        } finally { harness.close() }
    }

    @Test fun cancelledScopedDetailRendersSafeProblemAndRetriesTheSamePlayerLens() {
        val detailAttempts = AtomicInteger()
        val gateway = ReadGateway(STORY_A) { query ->
            if (query.section == StoryRecordSection.HISTORY) {
                if (detailAttempts.incrementAndGet() == 1) throw CancellationException("$PRIVATE /synthetic/event")
                event(query)
            } else page(query, "Underlying accepted record")
        }
        val harness = Harness()
        try {
            content()
            val owner = harness.create(gateway); settled(owner.model)
            val originalShell = owner.model.state.value
            val saved = gateway.saved
            open(); loaded(owner.model)
            val underlying = owner.model.storyRecord.value
            val reference = reference(STORY_A)
            record("story-record-scoped-source-0-0").assertIsEnabled().performClick()
            unavailable(owner.model, detail = true)
            val failedQuery = gateway.queries.last()
            assertEquals(2, gateway.queries.size)
            assertEquals(underlying.context, failedQuery.context)
            assertEquals(StoryRecordSection.HISTORY, failedQuery.section)
            assertEquals(2, failedQuery.version)
            assertEquals(exactEventSearch(reference), failedQuery.search)
            val detail = checkNotNull(owner.model.storyRecord.value.eventDetail)
            assertEquals(reference, detail.scopedReference)
            assertEquals(underlying.copy(eventDetail = detail), owner.model.storyRecord.value)
            assertNull(detail.entry)
            compose.waitForIdle(); assertEquals(2, gateway.queries.size)
            record("story-event-retry").performClick()
            loaded(owner.model) { it.eventDetail?.let { d -> !d.loading && d.problem == null && d.entry != null } == true }
            assertEquals(3, gateway.queries.size)
            assertEquals(failedQuery, gateway.queries.last())
            assertEquals(reference.originalScope, owner.model.storyRecord.value.eventDetail!!.entry!!.event!!.originalScope)
            compose.onNodeWithText("Visible event detail", useUnmergedTree = true).performScrollTo().assertIsDisplayed()
            assertPrivateTextAbsent(owner.model)
            compose.onNodeWithTag("story-event-back").assertIsEnabled().performClick()
            loaded(owner.model) { it.eventDetail == null }
            assertEquals(underlying, owner.model.storyRecord.value)
            visibleLabel("Underlying accepted record")
            closeRecord()
            harness.unchanged(owner, originalShell, saved)
        } finally { harness.close() }
    }

    @Test fun obsoletePageCancellationCannotReplaceSectionSelectionOrClosedAndReopenedRecords() {
        val gate = Gate()
        val reads = AtomicInteger()
        val gateway = ReadGateway(STORY_A) { query ->
            when (reads.incrementAndGet()) {
                1 -> gate.cancelAfterRelease()
                2 -> page(query, "Selected history remains visible")
                else -> page(query, "Reopened current page")
            }
        }
        val harness = Harness(gate)
        try {
            content()
            val owner = harness.create(gateway); settled(owner.model)
            val originalShell = owner.model.state.value
            val saved = gateway.saved
            open(); gateEntered(gate)
            assertTrue(owner.model.storyRecord.value.loading)
            record("story-record-loading").assertIsDisplayed()
            record("story-record-section-history").assertIsEnabled().performClick()
            loaded(owner.model) { it.section == StoryRecordSection.HISTORY }
            compose.onNodeWithTag("story-record-section-history").assertIsSelected()
            visibleLabel("Selected history remains visible")
            assertEquals(2, gateway.queries.size)
            closeRecord()
            open(); loaded(owner.model) { it.section == StoryRecordSection.PROGRESSION }
            val current = owner.model.storyRecord.value
            assertEquals(3, gateway.queries.size)
            assertFalse("Old producer must still be held until this explicit release", gate.finished.isCompleted)
            gate.release.complete(Unit); gateFinished(gate)
            assertEquals(current, owner.model.storyRecord.value)
            assertEquals(3, gateway.queries.size)
            compose.onNodeWithTag("story-record-problem").assertDoesNotExist()
            visibleLabel("Reopened current page")
            assertPrivateTextAbsent(owner.model)
            closeRecord()
            harness.unchanged(owner, originalShell, saved)
        } finally { harness.close() }
    }

    @Test fun oldDetailCancellationAfterBackCannotFinishTheReplacementDetail() {
        val old = Gate()
        val current = Gate()
        val details = AtomicInteger()
        val gateway = ReadGateway(STORY_A) { query ->
            if (query.section != StoryRecordSection.HISTORY) page(query, "Current evidence source")
            else if (details.incrementAndGet() == 1) old.cancelAfterRelease()
            else current.pageAfterRelease { event(query) }
        }
        val harness = Harness(old, current)
        try {
            content()
            val owner = harness.create(gateway); settled(owner.model)
            val originalShell = owner.model.state.value
            val saved = gateway.saved
            open(); loaded(owner.model)
            val underlying = owner.model.storyRecord.value
            record("story-record-scoped-source-0-0").performClick(); gateEntered(old)
            assertTrue(owner.model.storyRecord.value.eventDetail!!.loading)
            compose.onNodeWithTag("story-event-back").performClick()
            loaded(owner.model) { it.eventDetail == null }
            assertEquals(underlying, owner.model.storyRecord.value)
            record("story-record-scoped-source-0-0").performClick(); gateEntered(current)
            val pending = owner.model.storyRecord.value
            assertTrue(pending.eventDetail!!.loading)
            assertEquals(3, gateway.queries.size)
            assertFalse(old.finished.isCompleted)
            assertFalse(current.finished.isCompleted)
            old.release.complete(Unit); gateFinished(old)
            assertFalse("Fresh detail must remain held after obsolete completion", current.finished.isCompleted)
            assertEquals(pending, owner.model.storyRecord.value)
            compose.onNodeWithTag("story-event-loading").assertIsDisplayed()
            compose.onNodeWithTag("story-event-problem").assertDoesNotExist()
            current.release.complete(Unit); gateFinished(current)
            loaded(owner.model) { it.eventDetail?.let { d -> !d.loading && d.entry != null } == true }
            assertEquals(3, gateway.queries.size)
            assertEquals(gateway.queries[1], gateway.queries[2])
            assertEquals(reference(STORY_A), owner.model.storyRecord.value.eventDetail!!.scopedReference)
            compose.onNodeWithText("Visible event detail", useUnmergedTree = true).performScrollTo().assertIsDisplayed()
            compose.onNodeWithTag("story-event-back").performClick(); loaded(owner.model) { it.eventDetail == null }
            assertEquals(underlying, owner.model.storyRecord.value)
            closeRecord()
            harness.unchanged(owner, originalShell, saved)
        } finally { harness.close() }
    }

    @Test fun disposedOwnerAndRemountedScreenCannotBorrowOldReadsOrRetainedCallbacks() {
        val old = Gate()
        val retiredGateway = ReadGateway(STORY_A) { old.cancelAfterRelease() }
        val freshGateway = ReadGateway(STORY_B) { query -> page(query, "Fresh mounted story record") }
        val harness = Harness(old)
        try {
            content()
            val retired = harness.create(retiredGateway); settled(retired.model)
            open(); gateEntered(old)
            val oldQueries = retiredGateway.queries.toList()
            val retiredSaved = retiredGateway.saved
            val retained = listOf<() -> Unit>(retired.model::openStoryRecord, retired.model::retryStoryRecord,
                retired.model::nextRecordPage, retired.model::closeStoryRecord, retired.model::backToStoryRecord,
                retired.model::retryRecordEvent, { retired.model.recordSection(StoryRecordSection.KNOWLEDGE) },
                { retired.model.openScopedRecordEvent(reference(STORY_A), StoryRecordContext(STORY_A, STORY_A.revision)) })
            main { mounted.value = null; retired.store.clear() }
            compose.waitForIdle()
            assertEquals(1, retiredGateway.closes.get())
            val fresh = harness.create(freshGateway); settled(fresh.model)
            val originalFreshShell = fresh.model.state.value
            val saved = freshGateway.saved
            open(); loaded(fresh.model)
            val current = fresh.model.storyRecord.value
            assertEquals(StoryRecordContext(STORY_B, STORY_B.revision), current.context)
            main { retained.forEach { it() } }
            assertFalse("Disposed producer must remain held until explicit release", old.finished.isCompleted)
            old.release.complete(Unit); gateFinished(old)
            assertEquals(retiredSaved, retiredGateway.saved)
            assertEquals(oldQueries, retiredGateway.queries.toList())
            assertEquals(StoryRecordState(), retired.model.storyRecord.value)
            assertEquals(current, fresh.model.storyRecord.value)
            assertEquals(1, freshGateway.queries.size)
            visibleLabel("Fresh mounted story record")
            assertPrivateTextAbsent(fresh.model)
            closeRecord()
            open(); loaded(fresh.model)
            assertEquals(2, freshGateway.queries.size)
            visibleLabel("Fresh mounted story record")
            closeRecord()
            harness.unchanged(fresh, originalFreshShell, saved)
            assertTrue(retiredGateway.gameplay.isEmpty())
            assertEquals(0, retiredGateway.snapshots.get())
        } finally { harness.close() }
    }

    private data class Owner(val model: ShellViewModel, val store: ViewModelStore, val gateway: ReadGateway)
    private inner class Harness(vararg val gates: Gate) {
        private val owners = mutableListOf<Owner>()
        private val stores = mutableListOf<ViewModelStore>()
        fun create(gateway: ReadGateway): Owner = main {
            val store = ViewModelStore().also { stores += it }
            val model = ViewModelProvider(store, object : ViewModelProvider.Factory {
                @Suppress("UNCHECKED_CAST")
                override fun <T : ViewModel> create(modelClass: Class<T>): T = ShellViewModel(gateway) as T
            })[ShellViewModel::class.java]
            Owner(model, store, gateway).also { owners += it; mounted.value = model }
        }
        fun unchanged(owner: Owner, shell: ShellState, saved: SavedSnapshot) {
            assertEquals(shell, owner.model.state.value)
            assertEquals(saved, owner.gateway.saved)
            assertTrue("Read UI dispatched a gameplay operation", owner.gateway.gameplay.isEmpty())
            assertEquals("Browsing must not refresh native snapshots", 0, owner.gateway.snapshots.get())
            assertEquals(1, owner.gateway.initializes.get())
        }
        fun close() {
            // Release even when an assertion fails; no suspended noncooperative
            // task is left waiting for an unavailable UI callback.
            gates.forEach { it.release.complete(Unit) }
            main { mounted.value = null; stores.forEach { it.clear() } }
            runBlocking {
                withTimeout(12_000) {
                    gates.filter { it.entered.isCompleted }.forEach { it.finished.await() }
                }
            }
            compose.waitForIdle()
        }
    }

    private class Gate {
        val entered = CompletableDeferred<Unit>()
        val release = CompletableDeferred<Unit>()
        val finished = CompletableDeferred<Unit>()
        suspend fun cancelAfterRelease(): Nothing = withContext(NonCancellable) {
            entered.complete(Unit)
            try {
                withTimeout(10_000) { release.await() }
                throw CancellationException("$PRIVATE /synthetic/retired-read")
            } finally { finished.complete(Unit) }
        }
        suspend fun pageAfterRelease(value: () -> StoryRecordPage): StoryRecordPage = withContext(NonCancellable) {
            entered.complete(Unit)
            try {
                withTimeout(10_000) { release.await() }
                value()
            } finally { finished.complete(Unit) }
        }
    }

    private class ReadGateway(story: SavedStory, val read: suspend (StoryRecordQuery) -> StoryRecordPage) : DemoGateway {
        override val durable = true
        override val storyRecords = true
        val saved = SavedSnapshot(story.revision, "You", emptyList(), "synthetic-ui-read-only", 1,
            listOf(story), story, rulesProfile = "fantasy-v1")
        val queries = CopyOnWriteArrayList<StoryRecordQuery>()
        val gameplay = CopyOnWriteArrayList<String>()
        val initializes = AtomicInteger()
        val snapshots = AtomicInteger()
        val closes = AtomicInteger()
        override suspend fun initialize(): SavedSnapshot { initializes.incrementAndGet(); return saved }
        override suspend fun snapshot(): SavedSnapshot { snapshots.incrementAndGet(); return saved }
        override suspend fun readStoryRecord(query: StoryRecordQuery): StoryRecordPage { queries += query; return read(query) }
        private fun forbidden(name: String): Nothing { gameplay += name; throw AssertionError("Record UI called $name") }
        override suspend fun respond(action: DemoAction, revision: Long, mode: DemoMode): DemoResult = forbidden("respond")
        override suspend fun respondText(input: PlayInput, revision: Long): DemoResult = forbidden("respondText")
        override suspend fun commitAsync(result: DemoResult): DemoResult = forbidden("commitAsync")
        override fun commit(result: DemoResult): DemoResult = forbidden("commit")
        override fun cancel() { forbidden("cancel") }
        override fun reset() { forbidden("reset") }
        override suspend fun createSaved(): SavedSnapshot = forbidden("createSaved")
        override suspend fun resumeSaved(story: SavedStory): SavedSnapshot = forbidden("resumeSaved")
        override suspend fun recoverSaved(): SavedSnapshot = forbidden("recoverSaved")
        override suspend fun cancelSaved(): SavedSnapshot = forbidden("cancelSaved")
        override fun close() { closes.incrementAndGet() }
    }

    private companion object {
        const val PRIVATE = "PRIVATE-UI-READER-CANCEL"
        val STORY_A = SavedStory("cancel-screen-observatory", "child", "Synthetic Observatory", 4)
        val STORY_B = SavedStory("cancel-screen-garden", "main", "Synthetic Garden", 7)
        val CURSOR = "2:1:${"a".repeat(64)}"
        fun reference(story: SavedStory) = StoryRecordScopedEvent(StoryRecordScope(story.story, "ancestor"), 1)
        fun exactEventSearch(reference: StoryRecordScopedEvent) =
            "\"event\":{\"sequence\":${reference.sequence},\"scope\":{\"story\":\"${reference.originalScope.story}\",\"branch\":\"${reference.originalScope.branch}\"}"
        fun page(query: StoryRecordQuery, label: String, paged: Boolean = false): StoryRecordPage {
            val origin = if (query.section == StoryRecordSection.HISTORY) StoryRecordOrigin.RECORDED_MESSAGE else StoryRecordOrigin.CANONICAL_FIELD
            val key = if (query.cursor == null) "visible-first" else "visible-next"
            return StoryRecordPage(query, 10, if (paged) 2 else 1,
                listOf(StoryRecordEntry(key, "Visible source", label, origin, sources = listOf("Synthetic accepted source"),
                    scopedEventSources = listOf(reference(query.context.story)))),
                if (paged && query.cursor == null) CURSOR else null)
        }
        fun event(query: StoryRecordQuery): StoryRecordPage {
            val ref = reference(query.context.story)
            return StoryRecordPage(query, 10, 1, listOf(StoryRecordEntry("visible-event", "Event #1", "Visible event detail",
                StoryRecordOrigin.RECORDED_OBSERVATION, event = StoryRecordEvent(1, "synthetic-observation-turn", 10, ref.originalScope),
                scopedEventSources = listOf(ref))), null)
        }
    }
}

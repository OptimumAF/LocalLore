/* Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0 */
package org.locallore.app

import androidx.compose.runtime.SideEffect
import androidx.compose.runtime.collectAsState
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.ui.test.*
import androidx.compose.ui.test.junit4.createComposeRule
import androidx.lifecycle.ViewModel
import androidx.lifecycle.ViewModelProvider
import androidx.lifecycle.ViewModelStore
import androidx.test.ext.junit.runners.AndroidJUnit4
import java.util.concurrent.atomic.AtomicReference
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.runBlocking
import kotlinx.coroutines.withContext
import org.junit.Assert.*
import org.junit.Rule
import org.junit.Test
import org.junit.runner.RunWith
import org.locallore.app.ui.LocalLoreScreen
import org.locallore.app.ui.StoryRecordDialog

/** Actual JNI/Store/Compose browsing over a genuine synthetic native-produced Archive3.
 * Its corrections/discovery happened in the producer; these tests grant no Android author API.
 * Ordinary owner reopen is not Android process death. No model/provider inference is requested.
 */
@RunWith(AndroidJUnit4::class)
class Query2StoryRecordScreenTest {
    @get:Rule val compose = createComposeRule()
    private val active = mutableStateOf<ShellViewModel?>(null)
    private val renderedClick = AtomicReference<((StoryRecordScopedEvent) -> Unit)?>(null)

    private fun content() = compose.setContent {
        active.value?.let { model ->
            val shell by model.state.collectAsState()
            val record by model.storyRecord.collectAsState()
            val renderedContext = record.context
            val open: (StoryRecordScopedEvent) -> Unit = { model.openScopedRecordEvent(it, renderedContext) }
            SideEffect { renderedClick.set(open) }
            LocalLoreScreen(shell, model::submit, model::setMode, model::cancel, model::reset,
                onResume = model::resume, onRecover = model::recover, onTimeline = model::resumeTimeline,
                onStoryRecord = model::openStoryRecord) {
                StoryRecordDialog(record, model::closeStoryRecord, model::recordSection, model::recordSearch,
                    model::nextRecordPage, model::firstRecordPage, model::retryStoryRecord,
                    onEvent = { model.openRecordEvent(it, renderedContext) }, onScopedEvent = open,
                    onEventBack = model::backToStoryRecord, onEventRetry = model::retryRecordEvent)
            }
        }
    }

    private suspend fun createModel(fixture: RecordFixture, owner: RecordOwner): ShellViewModel = withContext(Dispatchers.Main) {
        val store = ViewModelStore().also { fixture.stores += it }
        ViewModelProvider(store, object : ViewModelProvider.Factory {
            @Suppress("UNCHECKED_CAST")
            override fun <T : ViewModel> create(modelClass: Class<T>): T = ShellViewModel(owner.gateway) as T
        })[ShellViewModel::class.java].also { active.value = it }
    }
    private fun settled(model: ShellViewModel, branch: String? = null) {
        compose.waitUntil(8_000) {
            val value = model.state.value
            val selected = value.selectedStory
            !value.busy && selected != null && (branch == null || selected.branch == branch)
        }
        compose.waitForIdle()
        assertFalse(model.state.value.recoveryRequired)
    }
    private fun loaded(model: ShellViewModel, predicate: (StoryRecordState) -> Boolean = { true }) {
        compose.waitUntil(8_000) {
            val state = model.storyRecord.value
            state.visible && !state.loading && state.problem == null && predicate(state)
        }
        compose.waitForIdle()
    }
    private fun shell(name: String): SemanticsNodeInteraction {
        compose.onNodeWithTag("story-list").performScrollToNode(hasTestTag(name))
        return compose.onNodeWithTag(name)
    }
    private fun record(name: String) = compose.onNodeWithTag(name).performScrollTo()
    private fun open(model: ShellViewModel) { shell("story-record-open").performClick(); loaded(model) }
    private fun close() { compose.onNodeWithTag("story-record-close").performClick(); compose.waitForIdle() }
    private fun section(model: ShellViewModel, section: StoryRecordSection) {
        record("story-record-section-${section.wire}").performClick()
        loaded(model) { it.section == section }
    }
    private fun search(model: ShellViewModel, text: String) {
        record("story-record-search").performTextReplacement(text)
        record("story-record-search-submit").performClick()
        loaded(model) { it.search == text }
    }
    private fun timeline(model: ShellViewModel, branch: String) {
        shell("timeline-library").performClick()
        compose.onNodeWithTag("timeline-$branch").performClick()
        settled(model, branch)
    }
    private fun label(reference: StoryRecordScopedEvent) =
        "Open event #${reference.sequence} \u00B7 ${reference.originalScope.story} / ${reference.originalScope.branch}"
    private fun exactSearch(reference: StoryRecordScopedEvent) =
        "\"event\":{\"sequence\":${reference.sequence},\"scope\":{\"story\":\"${reference.originalScope.story}\",\"branch\":\"${reference.originalScope.branch}\"}"

    private fun allSections(model: ShellViewModel, input: Query2StoryRecordScreenFixture, role: String): Map<StoryRecordSection, List<StoryRecordEntry>> {
        val expectedObservation = if (role == "rediscovered") input.newObservation else input.oldObservation
        val forbidden = input.forbidden + if (role == "rediscovered") emptyList() else listOf(input.newObservation)
        val result = linkedMapOf<StoryRecordSection, List<StoryRecordEntry>>()
        open(model)
        for (view in StoryRecordSection.entries) {
            section(model, view)
            val entries = mutableListOf<StoryRecordEntry>()
            var pages = 0
            while (true) {
                val page = model.storyRecord.value
                assertEquals(input.head(role), page.context!!.revision)
                assertEquals(input.time(role), page.storyTime)
                assertTrue(page.entries.all { it.eventSources.isEmpty() })
                for ((index, entry) in page.entries.withIndex()) {
                    for (canary in forbidden) {
                        assertFalse("A private/unobserved value entered a player record", entry.toString().contains(canary))
                        compose.onAllNodes(hasText(canary, substring = true)).assertCountEquals(0)
                    }
                    if (entry.origin == StoryRecordOrigin.AUTHOR_CORRECTION) {
                        assertEquals(StoryRecordSection.HISTORY, view)
                        assertEquals("author-correction:${input.correctionRevision}", entry.key)
                        assertEquals("History correction", entry.title)
                        assertEquals("History was corrected at revision #${input.correctionRevision}. This marker is not a witnessed event.", entry.text)
                        assertTrue(entry.sources.isEmpty() && entry.scopedEventSources.isEmpty())
                        assertNull(entry.event)
                        record("story-record-entry-$index")
                        val inside = hasAnyAncestor(hasTestTag("story-record-entry-$index"))
                        compose.onNode(inside and hasText(entry.text), useUnmergedTree = true).assertExists()
                        compose.onAllNodes(inside and hasClickAction(), useUnmergedTree = true).assertCountEquals(0)
                    }
                }
                entries += page.entries
                check(++pages <= 16)
                if (page.nextCursor == null) {
                    assertEquals(page.total, entries.size)
                    break
                }
                val next = page.nextCursor
                record("story-record-next").performClick()
                loaded(model) { it.cursor == next }
            }
            assertEquals(entries.size, entries.map { it.key }.toSet().size)
            result[view] = entries
        }
        val known = result.getValue(StoryRecordSection.KNOWLEDGE)
        assertTrue(known.none { it.origin == StoryRecordOrigin.CANONICAL_TRUTH })
        assertEquals(1, known.count { it.origin == StoryRecordOrigin.KNOWN_AS_OBSERVED &&
            it.title.substringBefore(" \u00B7 ") == input.factId && it.text == expectedObservation })
        val markers = result.getValue(StoryRecordSection.HISTORY).filter { it.origin == StoryRecordOrigin.AUTHOR_CORRECTION }
        assertEquals(if (role == "before") 0 else 1, markers.size)
        close()
        return result
    }

    private fun eventPage(model: ShellViewModel, reference: StoryRecordScopedEvent) {
        section(model, StoryRecordSection.HISTORY)
        search(model, exactSearch(reference))
        assertEquals(1, model.storyRecord.value.total)
        assertEquals(listOf(reference), model.storyRecord.value.entries.single().scopedEventSources)
        assertTrue(model.storyRecord.value.entries.single().eventSources.isEmpty())
    }
    private fun drill(model: ShellViewModel, reference: StoryRecordScopedEvent) {
        record("story-record-scoped-source-0-0").assertTextEquals(label(reference)).performClick()
        loaded(model) { it.eventDetail?.loading == false }
        val detail = checkNotNull(model.storyRecord.value.eventDetail)
        val entry = checkNotNull(detail.entry)
        val event = checkNotNull(entry.event)
        assertNull(detail.problem)
        assertEquals(reference, detail.scopedReference)
        assertEquals(StoryRecordOrigin.RECORDED_OBSERVATION, entry.origin)
        assertEquals(reference.sequence, event.sequence)
        assertEquals(reference.originalScope, event.originalScope)
        compose.onNodeWithTag("story-event-detail").assertIsDisplayed()
        compose.onNodeWithTag("story-event-back").performClick()
        loaded(model) { it.eventDetail == null }
    }

    @Test fun correctedOpaquePlayerRecordKeepsObservationsAndCorrectionMarkersSeparateAcrossReopen() = runBlocking {
        withRecordFixture { fixture ->
            val input = Query2StoryRecordScreenFixture(fixture)
            input.importArchive()
            val owner = input.selectedOwner("before")
            val model = createModel(fixture, owner)
            content(); settled(model, input.branch("before"))
            val before = owner.acceptedView()
            val calls = owner.transport.turnCalls.get()
            allSections(model, input, "before")
            assertTrue(before == owner.acceptedView())
            assertEquals(calls, owner.transport.turnCalls.get())

            timeline(model, input.branch("corrected"))
            input.assertBoundPlayer(owner)
            val corrected = owner.acceptedView()
            val correctedPages = allSections(model, input, "corrected")
            assertTrue(corrected == owner.acceptedView())
            assertEquals(calls, owner.transport.turnCalls.get())
            val current = checkNotNull(model.state.value.selectedStory)
            val legacy = owner.transport.exchange(owner.recordCommand(StoryRecordQuery(
                StoryRecordContext(current, current.revision), version = 1)))
            assertEquals("rejected", legacy.getString("status"))
            assertEquals("Version", legacy.getString("error")) // Actual native Domain2, not a fixture flag.

            compose.runOnIdle { active.value = null }
            compose.waitForIdle()
            fixture.closeOwnersAndDrain()
            val reopenedOwner = input.selectedOwner("corrected")
            val reopened = createModel(fixture, reopenedOwner)
            settled(reopened, input.branch("corrected"))
            assertTrue(corrected == reopenedOwner.acceptedView())
            val reopenedCalls = reopenedOwner.transport.turnCalls.get()
            assertEquals(correctedPages, allSections(reopened, input, "corrected"))
            assertTrue(corrected == reopenedOwner.acceptedView())

            // The producer performed this real native rediscovery before exporting the archive.
            // UI selection/browsing performs no discovery, generation, correction or commit.
            timeline(reopened, input.branch("rediscovered"))
            input.assertBoundPlayer(reopenedOwner)
            val rediscovered = reopenedOwner.acceptedView()
            allSections(reopened, input, "rediscovered")
            assertTrue(rediscovered == reopenedOwner.acceptedView())
            assertEquals(reopenedCalls, reopenedOwner.transport.turnCalls.get())
        }
    }

    @Test fun opaquePlayerSourceDrillUsesOriginalScopeAndRejectsStaleStoryCallbacks() = runBlocking {
        withRecordFixture { fixture ->
            val input = Query2StoryRecordScreenFixture(fixture)
            input.importArchive()
            val owner = input.selectedOwner("corrected")
            val other = input.otherStory(owner)
            val model = createModel(fixture, owner)
            content(); settled(model, input.branch("corrected"))
            val original = input.drill()
            assertNotEquals(input.branch("corrected"), original.originalScope.branch)
            val accepted = owner.acceptedView()
            val calls = owner.transport.turnCalls.get()
            open(model)
            eventPage(model, original) // A valid current-player ancestor grant exists first.
            val oldClick = checkNotNull(renderedClick.get())
            drill(model, original)
            assertTrue(accepted == owner.acceptedView())
            close()

            timeline(model, input.branch("rediscovered"))
            val leafAccepted = owner.acceptedView()
            open(model); eventPage(model, original)
            val currentLeaf = model.storyRecord.value
            compose.runOnIdle { oldClick(original) }
            compose.waitForIdle()
            assertEquals(currentLeaf, model.storyRecord.value)
            assertNull(model.storyRecord.value.eventDetail)
            drill(model, original) // Current rendered callback can open the same inherited tuple.
            assertTrue(leafAccepted == owner.acceptedView())
            close()

            shell("saved-library").performClick()
            compose.onNodeWithTag("saved-story-${other.story}").performClick()
            settled(model)
            assertEquals(other.story, model.state.value.selectedStory!!.story)
            val otherAccepted = owner.acceptedView()
            val otherReference = StoryRecordScopedEvent(StoryRecordScope(other.story, other.branch), original.sequence)
            open(model); eventPage(model, otherReference)
            val currentOther = model.storyRecord.value
            compose.runOnIdle { oldClick(otherReference) }
            compose.waitForIdle()
            assertEquals(currentOther, model.storyRecord.value)
            assertNull(model.storyRecord.value.eventDetail)
            drill(model, otherReference)
            assertTrue(otherAccepted == owner.acceptedView())
            assertEquals(calls, owner.transport.turnCalls.get())

            val disposedClick = checkNotNull(renderedClick.get())
            close()
            compose.runOnIdle { active.value = null; fixture.stores.forEach { it.clear() } }
            val disposed = model.storyRecord.value
            compose.runOnIdle { disposedClick(otherReference); oldClick(original) }
            compose.waitForIdle()
            assertEquals(disposed, model.storyRecord.value)
            assertEquals(calls, owner.transport.turnCalls.get())
            fixture.closeOwnersAndDrain()
            val finalOwner = fixture.owner()
            val library = finalOwner.gateway.initialize()
            finalOwner.gateway.resumeSaved(library.stories.single { it.story == other.story })
            assertTrue(otherAccepted == finalOwner.acceptedView())
            assertEquals(0, finalOwner.transport.turnCalls.get())
        }
    }
}

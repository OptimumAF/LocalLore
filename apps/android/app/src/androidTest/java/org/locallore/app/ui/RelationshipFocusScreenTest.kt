/* Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0 */
package org.locallore.app.ui

import androidx.compose.runtime.collectAsState
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.ui.semantics.SemanticsActions
import androidx.compose.ui.test.*
import androidx.compose.ui.test.junit4.createComposeRule
import androidx.lifecycle.ViewModelStore
import org.junit.After
import org.junit.Assert.*
import org.junit.Rule
import org.junit.Test
import org.locallore.app.*

/** Real controls/controller/VM with synthetic typed rows, not native eligibility proof. */
class RelationshipFocusScreenTest {
    @get:Rule val compose = createComposeRule()
    private val active = mutableStateOf<ShellViewModel?>(null)
    private val stores = mutableListOf<ViewModelStore>()

    @After fun closeModels() {
        if (stores.isNotEmpty()) compose.runOnIdle {
            active.value = null
            stores.forEach { it.clear() }
        }
    }

    private data class Harness(val model: ShellViewModel, val gateway: RelationshipGateway)

    private fun show(): Harness {
        compose.setContent {
            active.value?.let { model ->
                val frame by model.storyRecordFrames.collectAsState()
                val rendered = frame.state
                StoryRecordDialog(rendered,
                    { model.closeStoryRecord(rendered) },
                    { section -> model.recordSection(section, rendered) },
                    { text -> model.recordSearch(text, rendered) },
                    { model.nextRecordPage(rendered) },
                    { model.firstRecordPage(rendered) },
                    { model.retryStoryRecord(rendered) },
                    onScopedEvent = { ref -> model.openScopedRecordEvent(ref, rendered) },
                    onEventBack = { model.backToStoryRecord(rendered) },
                    onEventRetry = { model.retryRecordEvent(rendered) },
                    onFocusRelationship = { entry -> model.focusRecordRelationship(entry, rendered) },
                    onAllRelationships = { model.allRecordRelationships(rendered) })
            }
        }
        val gateway = RelationshipGateway()
        val model = compose.runOnIdle {
            val store = ViewModelStore().also { stores += it }
            ShellViewModel(gateway).also { store.put("relationship-focus", it); active.value = it }
        }
        settled(model, A)
        return Harness(model, gateway)
    }

    private fun settled(model: ShellViewModel, story: SavedStory) {
        compose.waitUntil(8_000) { !model.state.value.busy && model.state.value.selectedStory == story }
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

    private fun control(tag: String) = compose.onNodeWithTag(tag).performScrollTo()

    private fun openRelationships(model: ShellViewModel) {
        compose.runOnIdle { model.openStoryRecord() }
        loaded(model)
        compose.onNodeWithTag("story-record-relationship-target").assertDoesNotExist()
        control("story-record-section-relationships").performClick()
        loaded(model) { it.section == StoryRecordSection.RELATIONSHIPS }
        assertNull(model.storyRecord.value.relationshipTarget)
    }

    private fun close() {
        compose.onNodeWithTag("story-record-close").performClick()
        compose.waitForIdle()
        compose.onNodeWithTag("story-record-dialog").assertDoesNotExist()
    }

    @Test fun laterPageTargetFocusKeepsNativeDimensionsAndEvidenceWhileSearchReturnsToAll() {
        val h = show()
        openRelationships(h.model)
        assertEquals(9, h.model.storyRecord.value.total)
        assertEquals(8, h.model.storyRecord.value.entries.size)
        control("story-record-next").performClick()
        loaded(h.model) { it.cursor == SECOND_PAGE }
        assertEquals("mira", h.model.storyRecord.value.entries.single().relationshipTarget!!.id)
        control("story-record-search").performTextReplacement("Unsubmitted lookup")
        control("story-record-focus-relationship-0").performClick()
        loaded(h.model) { it.relationshipTarget?.id == "mira" && it.entries.size == 3 }
        control("story-record-relationship-target").assertTextEquals("Target · mira")
        control("story-record-search").assert(hasText(""))
        compose.onNodeWithTag("story-record-focus-relationship-0").assertDoesNotExist()
        assertEquals(3, h.model.storyRecord.value.total)
        assertTrue(h.model.storyRecord.value.entries.all { it.relationshipTarget?.id == "mira" })
        assertEquals(listOf("obligation", "respect", "trust"),
            h.model.storyRecord.value.entries.map { it.title.substringAfter(" · ") })
        control("story-record-next").assertIsNotEnabled()
        control("story-record-scoped-source-0-0").performClick()
        loaded(h.model) { it.eventDetail?.entry != null }
        compose.onNodeWithText("Synthetic witnessed relationship event").assertExists()
        compose.onNodeWithTag("story-event-back").performClick()
        loaded(h.model) { it.eventDetail == null && it.relationshipTarget?.id == "mira" }
        assertEquals(3, h.model.storyRecord.value.total)
        control("story-record-all-relationships").performClick()
        loaded(h.model) { it.relationshipTarget == null && it.entries.size == 8 }
        assertNull(h.gateway.reads.last().cursor)
        control("story-record-next").performClick()
        loaded(h.model) { it.cursor == SECOND_PAGE }
        control("story-record-focus-relationship-0").performClick()
        loaded(h.model) { it.relationshipTarget?.id == "mira" }
        control("story-record-search").performTextReplacement("Mira-neighbor")
        control("story-record-search-submit").performClick()
        loaded(h.model) { it.relationshipTarget == null && it.search == "Mira-neighbor" }
        assertEquals(3, h.model.storyRecord.value.total)
        assertTrue(h.model.storyRecord.value.entries.all { it.relationshipTarget?.id == "Mira-neighbor" })
        compose.onNodeWithTag("story-record-all-relationships").assertDoesNotExist()
        assertNull(h.gateway.reads.last().cursor)
        close()
        compose.runOnIdle {
            assertEquals(0, h.gateway.gameplayCalls)
            assertEquals(snapshot(A), h.gateway.saved)
        }
    }

    @Test fun retainedAndCopiedTargetsCannotRetargetCaseDistinctFocusReopenedViewOrAnotherStory() {
        val h = show()
        openRelationships(h.model)
        control("story-record-next").performClick()
        loaded(h.model) { it.cursor == SECOND_PAGE }
        val lowerEntry = h.model.storyRecord.value.entries.single()
        val oldLower = checkNotNull(control("story-record-focus-relationship-0")
            .fetchSemanticsNode().config[SemanticsActions.OnClick].action)
        control("story-record-first").performClick()
        loaded(h.model) { it.cursor == null && it.entries.size == 8 }
        control("story-record-focus-relationship-0").performClick()
        loaded(h.model) { it.relationshipTarget?.id == "Mira" }
        val upper = h.model.storyRecord.value
        assertTrue(upper.entries.all { it.relationshipTarget?.id == "Mira" })
        quiet(h, upper, oldLower)
        quiet(h, upper) { h.model.focusRecordRelationship(lowerEntry, upper); true }
        quiet(h, upper) { h.model.focusRecordRelationship(upper.entries.first().copy(), upper); true }
        val oldClear = checkNotNull(control("story-record-all-relationships")
            .fetchSemanticsNode().config[SemanticsActions.OnClick].action)
        close()
        openRelationships(h.model)
        control("story-record-focus-relationship-0").performClick()
        loaded(h.model) { it.relationshipTarget?.id == "Mira" }
        val reopened = h.model.storyRecord.value
        assertEquals(upper, reopened)
        assertNotSame(upper, reopened)
        quiet(h, reopened, oldLower)
        quiet(h, reopened, oldClear)
        close()
        compose.runOnIdle { h.model.resume(B) }
        settled(h.model, B)
        openRelationships(h.model)
        quiet(h, h.model.storyRecord.value, oldLower)
        control("story-record-focus-relationship-0").performClick()
        loaded(h.model) { it.relationshipTarget?.id == "Mira" }
        assertEquals(B.story, h.gateway.reads.last().context.story.story)
        control("story-record-all-relationships").performClick()
        loaded(h.model) { it.relationshipTarget == null }
        close()
        compose.runOnIdle {
            assertEquals(0, h.gateway.gameplayCalls)
            assertEquals(snapshot(B), h.gateway.saved)
        }
    }

    private fun quiet(h: Harness, expected: StoryRecordState, action: () -> Boolean) {
        val before = compose.runOnIdle { h.gateway.reads.toList() }
        compose.runOnIdle { action() }
        compose.waitForIdle()
        compose.runOnIdle {
            assertSame(expected, h.model.storyRecord.value)
            assertEquals(before, h.gateway.reads)
            assertEquals(0, h.gateway.gameplayCalls)
        }
    }

    private class RelationshipGateway : DemoGateway {
        override val durable = true
        override val storyRecords = true
        val reads = mutableListOf<StoryRecordQuery>()
        var saved = snapshot(A)
        var gameplayCalls = 0
        override suspend fun initialize() = saved
        override suspend fun snapshot() = saved
        override suspend fun resumeSaved(story: SavedStory): SavedSnapshot = snapshot(story).also { saved = it }
        override suspend fun respond(action: DemoAction, revision: Long, mode: DemoMode): DemoResult {
            gameplayCalls++; return DemoResult.Rejected("Synthetic reader only")
        }
        override suspend fun commitAsync(result: DemoResult): DemoResult { gameplayCalls++; return result }
        override fun cancel() { gameplayCalls++ }
        override fun reset() { gameplayCalls++ }
        override suspend fun readStoryRecord(query: StoryRecordQuery): StoryRecordPage {
            reads += query
            val reference = StoryRecordScopedEvent(StoryRecordScope(query.context.story.story, "ancestor"), 2)
            if (query.section == StoryRecordSection.HISTORY) return StoryRecordPage(query, 10, 1,
                listOf(StoryRecordEntry("witnessed-event", "Event #2", "Synthetic witnessed relationship event",
                    StoryRecordOrigin.RECORDED_OBSERVATION,
                    event = StoryRecordEvent(2, "synthetic-turn", 10, reference.originalScope),
                    scopedEventSources = listOf(reference))), null)
            if (query.section != StoryRecordSection.RELATIONSHIPS)
                return StoryRecordPage(query, 10, 0, emptyList(), null)
            val all = listOf("Mira", "Mira-neighbor", "mira").flatMap { target ->
                listOf("obligation", "respect", "trust").mapIndexed { index, dimension ->
                    StoryRecordEntry("${query.context.story.story}:$target:$dimension", "$target · $dimension",
                        (index - 1).toString(), StoryRecordOrigin.CANONICAL_FIELD,
                        scopedEventSources = listOf(reference), relationshipTarget = StoryRecordRelationshipTarget(target))
                }
            }
            // Synthetic transport answers only; production matching/counting remains native.
            val matching = when {
                query.relationshipTarget != null -> all.filter { it.relationshipTarget == query.relationshipTarget }
                query.search.isNotEmpty() -> all.filter { it.title.contains(query.search, ignoreCase = true) }
                else -> all
            }
            val offset = if (query.cursor == null) 0 else 8
            return StoryRecordPage(query, 10, matching.size, matching.drop(offset).take(8),
                if (matching.size > offset + 8) SECOND_PAGE else null)
        }
    }

    private companion object {
        val A = SavedStory("relationship-ui-a", "main", "SCRIPTED relationship A", 4)
        val B = SavedStory("relationship-ui-b", "main", "SCRIPTED relationship B", 4)
        const val SECOND_PAGE = "synthetic-relationship-page-2"
        fun snapshot(story: SavedStory) = SavedSnapshot(4, "You", emptyList(), "synthetic-database", 1,
            listOf(A, B), story, rulesProfile = "fantasy_v1", textProvider = TextProvider.SCRIPTED)
    }
}

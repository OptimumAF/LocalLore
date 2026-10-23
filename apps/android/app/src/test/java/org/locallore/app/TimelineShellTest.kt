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

/** Native metadata is supplied by a fake gateway; this suite implements no branch rules. */
@OptIn(ExperimentalCoroutinesApi::class)
class TimelineShellTest {
    private val dispatcher = StandardTestDispatcher()
    private val models = ViewModelStore()
    @Before fun setup(): Unit { Dispatchers.setMain(dispatcher) }
    @After fun cleanup(): Unit { models.clear(); Dispatchers.resetMain() }

    private class Stories : DemoGateway {
        override val durable = true
        override val storyRecords = true
        var story = "story-a"
        var selected = "main"
        var failRecovery = false
        var gate: CompletableDeferred<Unit>? = null
        var closes = 0
        var gameplay = 0
        val resumes = mutableListOf<SavedStory>()
        fun saved(): SavedSnapshot {
            val root = SavedStory(story, "main", "Original title", 2)
            val timelines = listOf(SavedTimeline(story, "child", "main", 1, 3, 2),
                SavedTimeline(story, "main", null, null, 2, 0))
            val current = timelines.single { it.branch == selected }
            return SavedSnapshot(current.revision, "You", emptyList(), "/synthetic", 1,
                listOf(root), SavedStory(story, selected, root.title, current.revision),
                current.uncommittedDrafts, textProvider = TextProvider.SCRIPTED, databaseSchemaVersion = 2, timelines = timelines)
        }
        override suspend fun initialize() = saved()
        override suspend fun snapshot() = saved()
        override suspend fun recoverSaved(): SavedSnapshot {
            if (failRecovery) error("Private transport detail must not be published")
            return saved()
        }
        override suspend fun resumeSaved(story: SavedStory): SavedSnapshot {
            resumes += story
            gate?.let { withContext(NonCancellable) { it.await() } }
            selected = story.branch
            return saved()
        }
        override suspend fun respond(action: DemoAction, revision: Long, mode: DemoMode): DemoResult {
            gameplay++; return DemoResult.Rejected("Inventory")
        }
        override fun close() { closes++ }
    }
    private class Deletes : StoryDeletionGateway {
        var preparedStory: SavedStory? = null
        override suspend fun prepare(story: SavedStory): StoryDeletionPrepared {
            preparedStory = story
            return StoryDeletionPrepared(1, StoryDeletionPreview(1, story.story, story.title, "main",
                mapOf("main" to 2L, "child" to 3L), 3, 2, 2, 0, emptyMap(), "Synthetic preview"))
        }
        override suspend fun commit(token: Long): StoryDeleted = error("Consent was not granted")
        override fun cancel() {}
        override fun close() {}
    }
    private class Archives : ArchiveGateway {
        override suspend fun prepareExport(story: SavedStory): ArchivePrepared = error("Not requested")
        override suspend fun prepareImport(bytes: ByteArray): ArchivePrepared = error("Not requested")
        override suspend fun exportBytes(token: Long): ByteArray = error("Not requested")
        override suspend fun commitImport(token: Long): ArchiveImported = error("Not requested")
        override fun cancel() {}
        override fun close() {}
    }
    private fun model(stories: Stories, deletes: Deletes? = null, archives: Archives? = null) =
        ShellViewModel(stories, archiveGateway = archives, deletionGateway = deletes).also { models.put("timeline", it) }

    @Test fun catalogSelectsChildUsingRootTitleAndPublishesNativeHeadAndDrafts(): Unit = runTest(dispatcher) {
        val stories = Stories(); val model = model(stories)
        advanceUntilIdle()
        val child = model.state.value.timelines.single { it.branch == "child" }
        model.resumeTimeline(child); advanceUntilIdle()
        assertEquals(listOf(SavedStory("story-a", "child", "Original title", 3)), stories.resumes)
        assertEquals("child", model.state.value.selectedStory?.branch)
        assertEquals(3L, model.state.value.revision); assertEquals(2, model.state.value.uncommittedDrafts)
        assertEquals("main", model.state.value.stories.single().branch)
        assertEquals(0, stories.gameplay)
        assertEquals(TextProvider.SCRIPTED, model.state.value.textProvider)
    }

    @Test fun changingTimelineDismissesThePriorRecordContext(): Unit = runTest(dispatcher) {
        val stories = Stories(); val model = model(stories); advanceUntilIdle()
        model.openStoryRecord(); advanceUntilIdle(); assertTrue(model.storyRecord.value.visible)
        model.resumeTimeline(model.state.value.timelines.first()); advanceUntilIdle()
        assertFalse(model.storyRecord.value.visible)
        model.openStoryRecord(); advanceUntilIdle()
        assertEquals("child", model.storyRecord.value.context?.story?.branch)
        assertEquals(3L, model.storyRecord.value.context?.revision)
    }

    @Test fun copiedRefreshedAndOtherStoryCallbacksCannotSelectCurrentTimeline(): Unit = runTest(dispatcher) {
        val stories = Stories(); val model = model(stories); advanceUntilIdle()
        val old = model.state.value.timelines.first()
        model.resumeTimeline(old.copy()); advanceUntilIdle(); assertTrue(stories.resumes.isEmpty())
        model.recover(); advanceUntilIdle()
        assertEquals(old, model.state.value.timelines.first())
        assertNotSame(old, model.state.value.timelines.first())
        model.resumeTimeline(old); advanceUntilIdle(); assertTrue(stories.resumes.isEmpty())
        val priorStory = model.state.value.timelines.first()
        stories.story = "story-b"; model.recover(); advanceUntilIdle()
        model.resumeTimeline(priorStory); advanceUntilIdle(); assertTrue(stories.resumes.isEmpty())
        model.resumeTimeline(model.state.value.timelines.first()); advanceUntilIdle()
        assertEquals("story-b", stories.resumes.single().story)
    }

    @Test fun busyRecoveryAndDisposalFenceRetainedSelector(): Unit = runTest(dispatcher) {
        val stories = Stories(); val model = model(stories); advanceUntilIdle()
        val child = model.state.value.timelines.first()
        val release = CompletableDeferred<Unit>(); stories.gate = release
        model.resumeTimeline(child); runCurrent(); assertTrue(model.state.value.busy)
        model.resumeTimeline(child); runCurrent(); assertEquals(1, stories.resumes.size)
        release.complete(Unit); advanceUntilIdle(); stories.gate = null
        val current = model.state.value.timelines.first()
        stories.failRecovery = true; model.recover(); advanceUntilIdle()
        assertTrue(model.state.value.recoveryRequired)
        assertFalse(model.state.value.notice.orEmpty().contains("Private"))
        model.resumeTimeline(current); advanceUntilIdle(); assertEquals(1, stories.resumes.size)
        models.clear(); model.resumeTimeline(current); advanceUntilIdle()
        assertEquals(1, stories.closes); assertEquals(1, stories.resumes.size)
    }

    @Test fun archiveAndWholeStoryDeletionGuardSelectionAndDeleteUsesRootHead(): Unit = runTest(dispatcher) {
        val stories = Stories(); val deletes = Deletes(); val model = model(stories, deletes, Archives())
        advanceUntilIdle(); model.openArchive()
        model.resumeTimeline(model.state.value.timelines.first()); advanceUntilIdle()
        assertTrue(stories.resumes.isEmpty())
        checkNotNull(model.archiveController).dismiss(); advanceUntilIdle()
        model.resumeTimeline(model.state.value.timelines.first()); advanceUntilIdle()
        model.openDeletion(); advanceUntilIdle()
        assertEquals(SavedStory("story-a", "main", "Original title", 2), deletes.preparedStory)
        model.resumeTimeline(model.state.value.timelines.single { it.branch == "main" }); advanceUntilIdle()
        assertEquals(1, stories.resumes.size)
    }

    @Test fun noncooperativeResumeCannotPublishAfterDisposal(): Unit = runTest(dispatcher) {
        val stories = Stories(); val model = model(stories); advanceUntilIdle()
        val release = CompletableDeferred<Unit>(); stories.gate = release
        val child = model.state.value.timelines.first()
        model.resumeTimeline(child); runCurrent(); models.clear()
        release.complete(Unit); advanceUntilIdle()
        assertEquals("main", model.state.value.selectedStory?.branch)
        assertEquals(2L, model.state.value.revision); assertFalse(model.state.value.busy)
        model.resumeTimeline(child); advanceUntilIdle()
        assertEquals(1, stories.resumes.size); assertEquals(1, stories.closes)
    }
}

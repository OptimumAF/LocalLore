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

/** These fakes exercise shell ownership and consent, never implement native retention rules. */
@OptIn(ExperimentalCoroutinesApi::class)
class BranchDeletionShellTest {
    private val dispatcher = StandardTestDispatcher()
    private val owners = ViewModelStore()
    @Before fun setup() { Dispatchers.setMain(dispatcher) }
    @After fun cleanup() { owners.clear(); Dispatchers.resetMain() }

    private class Stories : DemoGateway {
        override val durable = true
        override val storyRecords = true
        val reads = mutableListOf<StoryRecordQuery>()
        val textInputs = mutableListOf<PlayInput>()
        val textHeads = mutableListOf<Long>()
        var recordGate: CompletableDeferred<Unit>? = null
        var selected = "parent"
        var empty = false
        var removed = false
        var mutations = 0
        var reconciles = 0
        var closes = 0
        var failRecovery = false
        var failReconcile = false
        var initializeGate: CompletableDeferred<Unit>? = null
        fun saved(): SavedSnapshot {
            if (empty) return SavedSnapshot(0, "", emptyList(), "/synthetic/stories.sqlite3", 1,
                emptyList(), null, databaseSchemaVersion = 4, textProvider = TextProvider.SCRIPTED)
            val root = SavedStory("synthetic-story", "main", "Original title", 8)
            val timelines = listOfNotNull(
                SavedTimeline(root.story, "main", null, null, 8, 0),
                if (removed) null else SavedTimeline(root.story, "parent", "main", 4, 12, 2),
                SavedTimeline(root.story, "child", "parent", 10, 13, 0),
            )
            val current = timelines.single { it.branch == selected }
            return SavedSnapshot(current.revision, "You", listOf(SceneMessage(current.revision,
                "Confirmed ${current.branch}", false)), "/synthetic/stories.sqlite3", 1,
                listOf(root), root.copy(branch = current.branch, revision = current.revision,
                    title = if (current.branch == "main") root.title else "Selected display title"),
                current.uncommittedDrafts, databaseSchemaVersion = 4, timelines = timelines,
                textProvider = TextProvider.SCRIPTED)
        }
        override suspend fun readStoryRecord(query: StoryRecordQuery): StoryRecordPage {
            reads += query
            recordGate?.let { withContext(NonCancellable) { it.await() } }
            return StoryRecordPage(query, query.context.revision, 1,
                listOf(StoryRecordEntry("visible", "Visible", "Frozen selected timeline",
                    StoryRecordOrigin.CANONICAL_FIELD)), null)
        }
        override suspend fun respondText(input: PlayInput, revision: Long): DemoResult {
            textInputs += input; textHeads += revision; return DemoResult.Rejected("Inventory")
        }
        override suspend fun initialize(): SavedSnapshot { initializeGate?.await(); return saved() }
        override suspend fun snapshot() = saved()
        override suspend fun reconcileSaved(): SavedSnapshot {
            reconciles++
            if (failReconcile) error("private reconcile transport canary")
            selected = "main"
            return saved()
        }
        override suspend fun recoverSaved(): SavedSnapshot {
            if (failRecovery) error("private recovery transport canary")
            selected = "main"
            return saved()
        }
        override suspend fun respond(action: DemoAction, revision: Long, mode: DemoMode): DemoResult {
            mutations++; return DemoResult.Rejected("Inventory")
        }
        override suspend fun createSaved(): SavedSnapshot { mutations++; return saved() }
        override suspend fun resumeSaved(story: SavedStory): SavedSnapshot { mutations++; return saved() }
        override fun close() { closes++ }
    }

    private class Deletes(private val stories: Stories) : BranchDeletionGateway {
        val requests = mutableListOf<SavedStory>()
        val commits = mutableListOf<Long>()
        var closes = 0
        var cancels = 0
        var loseAcknowledgement = false
        var previewGate: CompletableDeferred<Unit>? = null
        var previewVersion = 1
        override suspend fun prepareBranch(story: SavedStory): BranchDeletionPrepared {
            requests += story
            previewGate?.let { withContext(NonCancellable) { it.await() } }
            return BranchDeletionPrepared(23, BranchDeletionPreview(previewVersion, story.story, story.branch,
                story.title, "main", story.revision, mapOf("child" to 13L), mapOf("parent" to 10L),
                emptyList(), mapOf("turns" to 3L), 1, 2, "Synthetic native retention warning"))
        }
        override suspend fun commitBranch(token: Long): BranchDeleted {
            commits += token
            stories.removed = true
            if (loseAcknowledgement) throw BranchDeletionFailure("Cancelled")
            return BranchDeleted("synthetic-story", "parent", 10, 0, 3, listOf("parent"))
        }
        override fun cancel() { cancels++ }
        override fun close() { closes++ }
    }

    private class WholeDeletes : StoryDeletionGateway {
        var prepares = 0
        override suspend fun prepare(story: SavedStory): StoryDeletionPrepared { prepares++; error("Not requested") }
        override suspend fun commit(token: Long): StoryDeleted = error("Not requested")
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
    private fun model(stories: Stories, deletes: Deletes, whole: WholeDeletes? = null, archives: Archives? = null) =
        ShellViewModel(stories, archiveGateway = archives, deletionGateway = whole,
            branchDeletionGateway = deletes).also { owners.put("branch", it) }

    @Test fun currentPreviewVersionTwoIsAcceptedAndFutureThreeRefused() = runTest(dispatcher) {
        for (version in listOf(2, 3)) {
            val stories = Stories(); val deletes = Deletes(stories).apply { previewVersion = version }
            val model = model(stories, deletes); advanceUntilIdle(); model.openBranchDeletion(); advanceUntilIdle()
            val state = checkNotNull(model.branchDeletionController).state.value
            if (version == 2) assertEquals(2, checkNotNull(state.prepared).preview.version)
            else { assertNull(state.prepared); assertEquals(1, deletes.cancels) }
            assertTrue(deletes.commits.isEmpty()); assertEquals(0, stories.mutations)
            owners.clear(); advanceUntilIdle()
        }
    }

    @Test fun childConsentUsesOriginalTitleAndCurrentChildHeadAndGuardsAllCompetingActions() = runTest(dispatcher) {
        val stories = Stories(); val deletes = Deletes(stories); val whole = WholeDeletes()
        val model = model(stories, deletes, whole, Archives()); advanceUntilIdle()
        val before = model.state.value
        model.openBranchDeletion(); advanceUntilIdle()
        assertEquals(listOf(SavedStory("synthetic-story", "parent", "Original title", 12)), deletes.requests)
        assertTrue(model.state.value.deletionActive)
        model.reset(); model.submit(DemoAction.GIVE_POTION); model.resume(before.stories.single())
        model.resumeTimeline(before.timelines.first()); model.recover(); model.openArchive(); model.openDeletion()
        model.openDiagnostics(); model.setMode(DemoMode.FAILED); model.openBranchDeletion(); advanceUntilIdle()
        assertEquals(0, stories.mutations); assertEquals(0, whole.prepares)
        assertEquals(1, deletes.requests.size); assertFalse(model.archive.value.visible)
        assertFalse(model.diagnostics.value.visible); assertEquals(DemoMode.ACCEPTED, model.state.value.mode)
        assertEquals(before.messages, model.state.value.messages); assertEquals(12L, model.state.value.revision)
        val controller = checkNotNull(model.branchDeletionController)
        val consent = checkNotNull(controller.state.value.prepared)
        controller.confirm(consent.copy()); advanceUntilIdle(); assertTrue(deletes.commits.isEmpty())
        controller.confirm(consent); advanceUntilIdle()
        assertEquals(listOf(23L), deletes.commits); assertEquals(0, stories.reconciles)
        assertTrue(model.state.value.deletionActive); assertEquals(before.messages, model.state.value.messages)
        controller.dismiss(); advanceUntilIdle()
        assertEquals(1, stories.reconciles); assertEquals(0, stories.mutations)
        assertFalse(model.state.value.deletionActive); assertEquals("main", model.state.value.selectedStory?.branch)
        assertEquals(8L, model.state.value.revision); assertEquals("Confirmed main", model.state.value.messages.single().text)
        assertEquals(listOf("main", "child"), model.state.value.timelines.map { it.branch })
        assertTrue(model.state.value.notice.orEmpty().contains("Timeline removed"))
        controller.confirm(consent); advanceUntilIdle(); assertEquals(listOf(23L), deletes.commits)
    }

    @Test fun lostCommitAcknowledgementReconcilesActualRetainedRootWithoutClaimingRollback() = runTest(dispatcher) {
        val stories = Stories(); val deletes = Deletes(stories).apply { loseAcknowledgement = true }
        val model = model(stories, deletes); advanceUntilIdle(); model.openBranchDeletion(); advanceUntilIdle()
        val controller = checkNotNull(model.branchDeletionController)
        controller.confirm(checkNotNull(controller.state.value.prepared)); advanceUntilIdle()
        assertTrue(stories.removed); assertNull(controller.state.value.deleted)
        assertTrue(controller.state.value.notice.orEmpty().contains("may already have completed"))
        assertEquals(12L, model.state.value.revision); assertEquals(0, stories.reconciles)
        controller.dismiss(); advanceUntilIdle()
        assertEquals(1, stories.reconciles); assertFalse(model.state.value.recoveryRequired)
        assertEquals("main", model.state.value.selectedStory?.branch); assertEquals(8L, model.state.value.revision)
        assertTrue(model.state.value.notice.orEmpty().contains("may already have completed"))
        assertFalse(model.state.value.notice.orEmpty().contains("rollback")); assertEquals(0, stories.mutations)
    }

    @Test fun cancellingPreviewAlwaysReconcilesWithoutCommittingOrInventingAnUncertainOutcome() = runTest(dispatcher) {
        val stories = Stories(); val deletes = Deletes(stories); val model = model(stories, deletes)
        advanceUntilIdle(); model.openBranchDeletion(); advanceUntilIdle()
        checkNotNull(model.branchDeletionController).cancel(); advanceUntilIdle()
        assertTrue(deletes.commits.isEmpty()); assertFalse(stories.removed)
        assertEquals(1, stories.reconciles); assertEquals("main", model.state.value.selectedStory?.branch)
        assertFalse(model.state.value.notice.orEmpty().contains("may already")); assertEquals(0, stories.mutations)
    }

    @Test fun noncooperativePreviewMustDrainBeforeReconciliationOrAnyNewShellOperation() = runTest(dispatcher) {
        val stories = Stories(); val release = CompletableDeferred<Unit>()
        val deletes = Deletes(stories).apply { previewGate = release }; val model = model(stories, deletes)
        advanceUntilIdle(); model.openBranchDeletion(); runCurrent()
        val controller = checkNotNull(model.branchDeletionController); controller.cancel(); runCurrent()
        assertTrue(model.state.value.deletionActive); assertTrue(controller.state.value.closing)
        assertEquals(0, stories.reconciles)
        model.reset(); model.submit(DemoAction.GIVE_POTION); model.openBranchDeletion(); runCurrent()
        assertEquals(0, stories.mutations); assertEquals(1, deletes.requests.size)
        release.complete(Unit); advanceUntilIdle()
        assertEquals(1, stories.reconciles); assertFalse(controller.state.value.visible)
        assertFalse(model.state.value.deletionActive); assertTrue(deletes.commits.isEmpty())
        assertTrue(deletes.cancels >= 2)
    }

    @Test fun rootBusyRecoveryAndDisposedOwnersCannotPrepareTimelineDeletion() = runTest(dispatcher) {
        val stories = Stories(); val initialized = CompletableDeferred<Unit>(); stories.initializeGate = initialized
        val deletes = Deletes(stories); val model = model(stories, deletes)
        model.openBranchDeletion(); runCurrent(); assertTrue(deletes.requests.isEmpty())
        initialized.complete(Unit); advanceUntilIdle()
        stories.failRecovery = true; model.recover(); advanceUntilIdle()
        assertTrue(model.state.value.recoveryRequired)
        model.openBranchDeletion(); advanceUntilIdle(); assertTrue(deletes.requests.isEmpty())
        stories.failRecovery = false; model.recover(); advanceUntilIdle()
        assertEquals("main", model.state.value.selectedStory?.branch)
        model.openBranchDeletion(); advanceUntilIdle(); assertTrue(deletes.requests.isEmpty())
        owners.clear(); model.openBranchDeletion(); advanceUntilIdle()
        assertEquals(1, deletes.closes); assertEquals(1, stories.closes); assertTrue(deletes.requests.isEmpty())
    }

    @Test fun failedReconciliationKeepsLastConfirmedCanonAndRequiresAuthoritativeRecovery() = runTest(dispatcher) {
        val stories = Stories(); val deletes = Deletes(stories); val model = model(stories, deletes)
        advanceUntilIdle(); val before = model.state.value
        model.openBranchDeletion(); advanceUntilIdle(); stories.failReconcile = true
        checkNotNull(model.branchDeletionController).dismiss(); advanceUntilIdle()
        assertTrue(model.state.value.recoveryRequired); assertFalse(model.state.value.deletionActive)
        assertEquals(before.selectedStory, model.state.value.selectedStory)
        assertEquals(before.messages, model.state.value.messages); assertEquals(before.revision, model.state.value.revision)
        assertFalse(model.state.value.notice.orEmpty().contains("private"))
        model.openBranchDeletion(); model.submit(DemoAction.GIVE_POTION)
        model.resumeTimeline(model.state.value.timelines.first()); advanceUntilIdle()
        assertEquals(1, deletes.requests.size); assertEquals(0, stories.mutations)
        model.recover(); advanceUntilIdle()
        assertFalse(model.state.value.recoveryRequired); assertEquals("main", model.state.value.selectedStory?.branch)
    }

    @Test fun disposalDuringNoncooperativePreviewClosesAndCannotReconcileOrReopen() = runTest(dispatcher) {
        val stories = Stories(); val release = CompletableDeferred<Unit>()
        val deletes = Deletes(stories).apply { previewGate = release }; val model = model(stories, deletes)
        advanceUntilIdle(); model.openBranchDeletion(); runCurrent(); owners.clear()
        release.complete(Unit); advanceUntilIdle()
        model.openBranchDeletion(); model.reset(); advanceUntilIdle()
        assertFalse(model.branchDeletion.value.visible); assertEquals(1, deletes.closes)
        assertEquals(0, stories.reconciles); assertEquals(0, stories.mutations)
        assertEquals(1, deletes.requests.size); assertEquals("parent", model.state.value.selectedStory?.branch)
    }

    @Test fun branchDeletionDismissesNoncooperativeRecordAndFencesRetainedTextAndRecordCallbacks() = runTest(dispatcher) {
        val stories = Stories(); val release = CompletableDeferred<Unit>(); stories.recordGate = release
        val deletes = Deletes(stories); val model = model(stories, deletes); advanceUntilIdle()
        try {
            val before = model.state.value
            model.openStoryRecord(); runCurrent()
            assertTrue(model.storyRecord.value.visible && model.storyRecord.value.loading)
            val oldContext = model.storyRecord.value.context
            model.openBranchDeletion(); runCurrent()
            assertEquals(StoryRecordState(), model.storyRecord.value)
            assertTrue(model.state.value.deletionActive)
            model.openStoryRecord(); model.recordSection(StoryRecordSection.KNOWLEDGE)
            model.recordSearch("retained"); model.nextRecordPage(); model.firstRecordPage()
            model.retryStoryRecord(); model.openRecordEvent(1, oldContext); model.retryRecordEvent()
            model.submitText(PlayInput(PlayInputKind.ACTION, "I give my last potion to Mira."))
            model.resumeTimeline(before.timelines.first()); runCurrent()
            assertEquals(1, stories.reads.size); assertTrue(stories.textInputs.isEmpty())
            assertEquals(0, stories.mutations); assertEquals(before.messages, model.state.value.messages)
            release.complete(Unit); advanceUntilIdle()
            assertEquals(StoryRecordState(), model.storyRecord.value)
            checkNotNull(model.branchDeletionController).dismiss(); advanceUntilIdle()
            stories.recordGate = null; model.openStoryRecord(); advanceUntilIdle()
            assertEquals("main", model.storyRecord.value.context?.story?.branch)
            assertEquals(8L, model.storyRecord.value.context?.revision)
            assertEquals(2, stories.reads.size); assertEquals(TextProvider.SCRIPTED, model.state.value.textProvider)
        } finally { release.complete(Unit); runCurrent() }
    }

    @Test fun textTurnAfterDeletionReconciliationUsesRetainedRootHeadAndPreservesOriginalInput() = runTest(dispatcher) {
        val stories = Stories(); val deletes = Deletes(stories); val model = model(stories, deletes)
        advanceUntilIdle(); model.openBranchDeletion(); advanceUntilIdle()
        val controller = checkNotNull(model.branchDeletionController)
        controller.confirm(checkNotNull(controller.state.value.prepared)); advanceUntilIdle()
        val input = PlayInput(PlayInputKind.DIALOGUE, "  A literal retained-root remark.\n")
        model.submitText(input); advanceUntilIdle(); assertTrue(stories.textInputs.isEmpty())
        controller.dismiss(); advanceUntilIdle()
        model.openStoryRecord(); advanceUntilIdle(); assertTrue(model.storyRecord.value.visible)
        model.submitText(input); advanceUntilIdle()
        assertEquals(listOf(input), stories.textInputs); assertEquals(listOf(8L), stories.textHeads)
        assertEquals(StoryRecordState(), model.storyRecord.value)
        assertEquals("main", model.state.value.selectedStory?.branch); assertEquals(8L, model.state.value.revision)
        assertEquals("Confirmed main", model.state.value.messages.single().text)
        assertEquals(0, stories.mutations); assertEquals(1, stories.reconciles)
    }

    @Test fun emptyLibraryNeverReadsOrSendsTextOrPreparesEitherDeletion() = runTest(dispatcher) {
        val stories = Stories().apply { empty = true }; val deletes = Deletes(stories); val whole = WholeDeletes()
        val model = model(stories, deletes, whole, Archives()); advanceUntilIdle()
        val before = model.state.value
        assertNull(before.selectedStory); assertTrue(before.timelines.isEmpty()); assertTrue(before.stories.isEmpty())
        model.openBranchDeletion(); model.openDeletion(); model.openStoryRecord(); model.openArchive()
        model.submitText(PlayInput(PlayInputKind.DIALOGUE, "A remark without a selected story."))
        model.submit(DemoAction.GIVE_POTION); advanceUntilIdle()
        assertEquals(before, model.state.value); assertTrue(stories.reads.isEmpty())
        assertTrue(stories.textInputs.isEmpty()); assertTrue(deletes.requests.isEmpty()); assertEquals(0, whole.prepares)
        assertFalse(model.branchDeletion.value.visible); assertFalse(model.storyRecord.value.visible)
        assertFalse(model.archive.value.visible); assertEquals(0, stories.mutations)
    }
}

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
import org.junit.Assert.*
import org.junit.Before
import org.junit.Test

/** Actual VM + actual fork controller, typed fake persistence/workspace/native ports.
 * These assertions test admission/wiring, never canonical fork or Android filesystem behavior.
 */
@OptIn(ExperimentalCoroutinesApi::class)
class BranchForkShellTest {
    private val dispatcher = StandardTestDispatcher()
    private val owners = ViewModelStore()
    private var next = 0
    @Before fun setup() { Dispatchers.setMain(dispatcher) }
    @After fun cleanup() { owners.clear(); Dispatchers.resetMain() }

    private class Hint(private val events: MutableList<String>, var value: BranchForkRecovery? = null) : ForkRecoveryPersistence {
        var failLoad = false; var failSave = false
        var onSave: ((BranchForkRecovery?) -> Unit)? = null
        val writes = mutableListOf<BranchForkRecovery?>()
        override fun load(): BranchForkRecovery? { if (failLoad) error("PRIVATE hint parse"); return value }
        override fun save(value: BranchForkRecovery?) {
            events += "save"
            if (failSave) error("PRIVATE disk path")
            onSave?.invoke(value)
            writes += value; this.value = value
        }
    }
    private class Stories(private val events: MutableList<String>) : DemoGateway {
        override val durable = true
        override val storyRecords = true
        var selected = Original
        var roots = listOf(Original, Other)
        var onSnapshot: (() -> Unit)? = null
        var closed = false; var ready = false; var pending = false
        var submissions = 0; var snapshots = 0; var creates = 0; var recoveries = 0
        val resumes = mutableListOf<SavedStory>()
        var initializeGate: CompletableDeferred<Unit>? = null
        var responseGate: CompletableDeferred<Unit>? = null
        fun context(story: SavedStory, head: Long, epoch: Long): BranchForkContext? =
            if (closed || !ready || pending || story != selected || head != selected.revision) null
            else BranchForkContext("session-${selected.story}-${selected.branch}", ForkScope(story.story, story.branch), head, epoch = epoch)
        fun saved() = SavedSnapshot(selected.revision, "You", emptyList(), "synthetic private workspace", 1,
            roots, selected, databaseSchemaVersion = 4, textProvider = TextProvider.SCRIPTED,
            timelines = listOf(SavedTimeline(selected.story, selected.branch, null, null, selected.revision, 0)))
        override suspend fun initialize(): SavedSnapshot { initializeGate?.await(); ready = true; return saved() }
        override suspend fun snapshot(): SavedSnapshot { snapshots++; onSnapshot?.invoke(); ready = true; return saved() }
        override suspend fun resumeSaved(story: SavedStory): SavedSnapshot { resumes += story; selected = story; ready = true; return saved() }
        override suspend fun createSaved(): SavedSnapshot { creates++; return saved() }
        override suspend fun recoverSaved(): SavedSnapshot { recoveries++; return saved() }
        override suspend fun cancelSaved(): SavedSnapshot { pending = false; return saved() }
        override suspend fun respond(action: DemoAction, revision: Long, mode: DemoMode): DemoResult {
            submissions++; pending = true; responseGate?.await(); pending = false; return DemoResult.Rejected("Inventory")
        }
        override suspend fun respondText(input: PlayInput, revision: Long): DemoResult { submissions++; return DemoResult.Rejected("Inventory") }
        override fun cancel() { pending = false }
        override fun close() { events += "workspace-close"; closed = true }
    }
    private class Forks(private val events: MutableList<String>) : BranchForkGateway {
        val registrations = mutableListOf<Pair<BranchForkContext, BranchForkInput>>()
        val runs = mutableListOf<Long>(); val lookups = mutableListOf<BranchForkInput>(); val cancels = mutableListOf<Long?>()
        var registerGate: CompletableDeferred<Unit>? = null
        var registerFailure = false
        var lookupResult = BranchForkLookup(false, null)
        override suspend fun register(context: BranchForkContext, input: BranchForkInput, consent: Boolean): BranchForkStatus {
            check(consent); events += "register"; registrations += context to input
            withContext(NonCancellable) { registerGate?.await() }
            if (registerFailure) error("PRIVATE lost ack")
            return BranchForkStatus(41, BranchForkPhase.REGISTERED, false)
        }
        override suspend fun run(operation: Long): BranchForkStatus {
            events += "run"; runs += operation
            val input = registrations.last().second
            return BranchForkStatus(operation, BranchForkPhase.COMPLETED, false,
                BranchForkOutcome(1, ForkScope(input.parent.story, input.childBranch), input.parent,
                    input.atRevision, input.atRevision, true))
        }
        override suspend fun status(operation: Long): BranchForkStatus = error("Unexpected status")
        override suspend fun lookup(input: BranchForkInput): BranchForkLookup { lookups += input; return lookupResult }
        override fun cancel(operation: Long?) { cancels += operation }
        override fun close() { events += "fork-close" }
    }
    private fun model(stories: Stories, forks: Forks, hint: Hint, archives: ArchiveGateway? = null,
        deletion: StoryDeletionGateway? = null, branchDeletion: BranchDeletionGateway? = null) =
        ShellViewModel(stories, archiveGateway = archives, deletionGateway = deletion,
            branchDeletionGateway = branchDeletion, forkGateway = forks,
            forkContextProvider = stories::context, forkRecoveryStore = hint).also { owners.put("fork-${next++}", it) }

    @Test fun realVmSavesRenderedIdentityBeforeNativeDispatchAndNeverAutoResumes() = runTest(dispatcher) {
        val events = mutableListOf<String>(); val stories = Stories(events); val forks = Forks(events); val hint = Hint(events)
        val model = model(stories, forks, hint); advanceUntilIdle()
        assertTrue(events.isEmpty()); model.openFork()
        val input = model.fork.value.input!!
        assertEquals(ForkScope(Original.story, Original.branch), input.parent)
        assertEquals(Original.revision, input.expectedParentRevision)
        assertTrue(model.state.value.forkActive)
        model.confirmFork(input, false); model.confirmFork(input.copy(), true); advanceUntilIdle()
        assertTrue(events.isEmpty())
        model.confirmFork(input, true); advanceUntilIdle()
        assertEquals(listOf("save", "register", "run"), events)
        assertEquals(BranchForkRecovery(1, input), hint.value)
        assertEquals(input, forks.registrations.single().second)
        assertEquals(Original, model.state.value.selectedStory)
        assertTrue(stories.resumes.isEmpty()); assertEquals(0, stories.snapshots)
        assertNotNull(model.fork.value.outcome)
    }
    @Test fun forkReviewFencesTurnLibraryArchiveDeletionAndRecordCallbacks() = runTest(dispatcher) {
        val events = mutableListOf<String>(); val stories = Stories(events); val forks = Forks(events)
        stories.selected = Original.copy(branch = "active-child") // Ensure branch deletion would otherwise be admissible.
        val archive = object : ArchiveGateway {
            override suspend fun prepareExport(story: SavedStory): ArchivePrepared = error("Unexpected export")
            override suspend fun prepareImport(bytes: ByteArray): ArchivePrepared = error("Unexpected import")
            override suspend fun exportBytes(token: Long): ByteArray = error("Unexpected export")
            override suspend fun commitImport(token: Long): ArchiveImported = error("Unexpected import")
            override fun cancel() {}; override fun close() {}
        }
        var deletionPreviews = 0
        val deletion = object : StoryDeletionGateway {
            override suspend fun prepare(story: SavedStory): StoryDeletionPrepared { deletionPreviews++; error("Unexpected deletion") }
            override suspend fun commit(token: Long): StoryDeleted = error("Unexpected deletion")
            override fun cancel() {}; override fun close() {}
        }
        val branch = object : BranchDeletionGateway {
            override suspend fun prepareBranch(story: SavedStory): BranchDeletionPrepared { deletionPreviews++; error("Unexpected deletion") }
            override suspend fun commitBranch(token: Long): BranchDeleted = error("Unexpected deletion")
            override fun cancel() {}; override fun close() {}
        }
        val model = model(stories, forks, Hint(events), archive, deletion, branch); advanceUntilIdle(); model.openFork()
        model.submit(DemoAction.GIVE_POTION); model.submitText(PlayInput(PlayInputKind.ACTION, "I wait."))
        model.resume(Other); model.reset(); model.recover(); model.setMode(DemoMode.FAILED)
        model.openArchive(); model.openDeletion(); model.openBranchDeletion(); model.openStoryRecord(); model.openDiagnostics()
        advanceUntilIdle()
        assertEquals(0, stories.submissions); assertEquals(0, stories.creates); assertEquals(0, stories.recoveries)
        assertTrue(stories.resumes.isEmpty()); assertEquals(DemoMode.ACCEPTED, model.state.value.mode)
        assertFalse(model.state.value.archiveActive); assertFalse(model.state.value.deletionActive)
        assertFalse(model.archive.value.visible); assertFalse(model.deletion.value.visible)
        assertFalse(model.storyRecord.value.visible); assertFalse(model.diagnostics.value.visible)
        assertEquals(0, deletionPreviews)
    }
    @Test fun boundaryReviewKeepsChildIdentityAndRejectsAnOldRenderedConfirmation() = runTest(dispatcher) {
        val events = mutableListOf<String>(); val stories = Stories(events); val forks = Forks(events)
        val model = model(stories, forks, Hint(events)); advanceUntilIdle(); model.openFork()
        val first = model.fork.value.input!!
        model.prepareForkBoundary(first, 0)
        val updated = model.fork.value.input!!
        assertEquals(first.childBranch, updated.childBranch); assertEquals(0L, updated.atRevision)
        assertEquals(first.parent, updated.parent); assertEquals(first.expectedParentRevision, updated.expectedParentRevision)
        model.confirmFork(first, true); advanceUntilIdle(); assertTrue(forks.registrations.isEmpty())
        model.confirmFork(updated, true); advanceUntilIdle(); assertEquals(updated, forks.registrations.single().second)
    }
    @Test fun restoredHintIsLookupOnlyAndMissingLookupNeverCreatesOrRerolls() = runTest(dispatcher) {
        val events = mutableListOf<String>(); val stories = Stories(events); val forks = Forks(events); val hint = Hint(events, Recovery)
        val model = model(stories, forks, hint); advanceUntilIdle()
        assertFalse(model.forkVisible.value); assertTrue(forks.registrations.isEmpty()); assertTrue(events.isEmpty())
        model.openFork(); assertTrue(model.fork.value.lookupOnly); assertEquals(Recovery.input, model.fork.value.input)
        model.confirmFork(model.fork.value.input!!, true); model.retryFork(true); model.lookupFork(); advanceUntilIdle()
        assertEquals(listOf(Recovery.input), forks.lookups); assertTrue(forks.registrations.isEmpty())
        assertEquals(Recovery, hint.value); assertEquals(Recovery.input, model.fork.value.input)
    }
    @Test fun unreadableRecoveryBlocksCreationUntilExplicitSuccessfulForget() = runTest(dispatcher) {
        val events = mutableListOf<String>(); val stories = Stories(events); val forks = Forks(events)
        val hint = Hint(events).also { it.failLoad = true }
        val model = model(stories, forks, hint); advanceUntilIdle(); model.openFork()
        assertNotNull(model.forkProblem.value); assertNull(model.fork.value.input)
        model.prepareForkBoundary(null, 0); model.forgetFork(false); advanceUntilIdle()
        assertTrue(hint.writes.isEmpty()); assertTrue(forks.registrations.isEmpty())
        model.forgetFork(true)
        assertNull(model.forkProblem.value); assertEquals(listOf<BranchForkRecovery?>(null), hint.writes)
        model.prepareForkBoundary(null, 0); assertNotNull(model.fork.value.input)
        assertTrue(forks.registrations.isEmpty())
    }
    @Test fun failedSaveCannotDispatchAndRetainsTheReviewedInputForExplicitRetry() = runTest(dispatcher) {
        val events = mutableListOf<String>(); val stories = Stories(events); val forks = Forks(events)
        val hint = Hint(events).also { it.failSave = true }
        val model = model(stories, forks, hint); advanceUntilIdle(); model.openFork()
        val input = model.fork.value.input!!; model.confirmFork(input, true); advanceUntilIdle()
        assertEquals(input, model.fork.value.input); assertTrue(forks.registrations.isEmpty()); assertNull(hint.value)
        assertFalse(model.fork.value.notice!!.contains("PRIVATE"))
        hint.failSave = false; model.confirmFork(input, true); advanceUntilIdle()
        assertEquals(input, forks.registrations.single().second)
    }
    @Test fun backgroundRetiresPresentationBeforeLateRegistrationAndKeepsExactRecovery() = runTest(dispatcher) {
        val events = mutableListOf<String>(); val stories = Stories(events); val forks = Forks(events)
        val gate = CompletableDeferred<Unit>(); forks.registerGate = gate
        val hint = Hint(events); val model = model(stories, forks, hint); advanceUntilIdle(); model.openFork()
        val input = model.fork.value.input!!; model.confirmFork(input, true); runCurrent()
        assertTrue(model.fork.value.busy); model.stopFork(); runCurrent()
        assertFalse(model.forkVisible.value); assertTrue(model.state.value.forkActive)
        model.submit(DemoAction.GIVE_POTION); model.resume(Other); runCurrent()
        assertEquals(0, stories.submissions); assertTrue(stories.resumes.isEmpty())
        gate.complete(Unit); advanceUntilIdle()
        assertTrue(forks.runs.isEmpty()); assertTrue(forks.cancels.contains(41L))
        assertFalse(model.state.value.forkActive); assertNull(model.fork.value.outcome)
        model.resume(Other); advanceUntilIdle(); model.openFork(); model.lookupFork(); advanceUntilIdle()
        assertEquals(Other, model.state.value.selectedStory); assertEquals(input, forks.lookups.single())
        assertTrue(model.fork.value.lookupOnly); assertEquals(BranchForkRecovery(1, input), hint.value)
    }
    @Test fun explicitKnownOutcomeResumeUsesExistingGatewayAndRejectsStaleOutcomeCallbacks() = runTest(dispatcher) {
        val events = mutableListOf<String>(); val stories = Stories(events); val forks = Forks(events)
        val model = model(stories, forks, Hint(events)); advanceUntilIdle(); model.openFork()
        model.confirmFork(model.fork.value.input!!, true); advanceUntilIdle()
        val outcome = model.fork.value.outcome!!
        assertTrue(stories.resumes.isEmpty()); model.resumeFork(outcome.copy()); advanceUntilIdle(); assertTrue(stories.resumes.isEmpty())
        model.resumeFork(outcome); advanceUntilIdle()
        assertEquals(outcome.scope.branch, stories.resumes.single().branch)
        assertEquals(outcome.scope.branch, model.state.value.selectedStory!!.branch)
        model.resumeFork(outcome); advanceUntilIdle(); assertEquals(1, stories.resumes.size)
        assertFalse(model.forkVisible.value)
    }
    @Test fun sequentialForkRequiresExplicitSuccessfulForgetAfterKnownOutcomeResume() = runTest(dispatcher) {
        val events = mutableListOf<String>(); val stories = Stories(events); val forks = Forks(events); val hint = Hint(events)
        val model = model(stories, forks, hint); advanceUntilIdle(); model.openFork()
        val first = model.fork.value.input!!
        model.confirmFork(first, true); advanceUntilIdle()
        val firstRecovery = BranchForkRecovery(1, first)
        model.resumeFork(model.fork.value.outcome!!); advanceUntilIdle()
        val parent = model.state.value.selectedStory!!
        assertEquals(first.childBranch, parent.branch)
        assertEquals(first.atRevision, parent.revision)
        assertEquals(firstRecovery, hint.value)
        assertTrue(model.forkRecoveryPending.value)
        val canonicalBeforeForget = stories.saved()

        // Resuming known success does not silently clear the original identity.
        // A second opening displays that old request, not a new request on P.
        model.openFork()
        val recovered = model.fork.value.input!!
        assertEquals(first, recovered)
        assertEquals(ForkScope(Original.story, Original.branch), recovered.parent)
        assertEquals(ForkScope(parent.story, parent.branch), model.fork.value.context!!.parent)
        assertTrue(model.fork.value.lookupOnly)
        model.prepareForkBoundary(recovered, parent.revision)
        model.confirmFork(recovered, true); model.retryFork(true); advanceUntilIdle()
        assertSame(recovered, model.fork.value.input)
        assertEquals(listOf(first), forks.registrations.map { it.second })
        assertEquals(1, forks.runs.size)

        model.forgetFork(false); advanceUntilIdle()
        assertEquals(firstRecovery, hint.value)
        assertEquals(listOf(firstRecovery), hint.writes)
        hint.failSave = true
        model.forgetFork(true); advanceUntilIdle()
        assertEquals(firstRecovery, hint.value)
        assertEquals(listOf(firstRecovery), hint.writes)
        assertTrue(model.forkRecoveryPending.value)
        assertTrue(model.fork.value.lookupOnly)
        assertSame(recovered, model.fork.value.input)
        assertFalse(model.fork.value.notice!!.contains("PRIVATE"))
        assertEquals(canonicalBeforeForget, stories.saved())
        assertEquals(listOf(first), forks.registrations.map { it.second })
        assertEquals(1, forks.runs.size)

        hint.failSave = false
        model.forgetFork(true); advanceUntilIdle()
        assertNull(hint.value)
        assertFalse(model.forkRecoveryPending.value)
        assertNull(model.fork.value.input)
        // Forget changes only recovery metadata, not selection, accepted head,
        // messages or native draft metadata. This JVM test has no Compose editor.
        assertEquals(canonicalBeforeForget, stories.saved())
        assertEquals(parent, model.state.value.selectedStory)
        assertEquals(parent.revision, model.state.value.revision)
        assertEquals(canonicalBeforeForget.messages, model.state.value.messages)
        assertEquals(canonicalBeforeForget.uncommittedDrafts, model.state.value.uncommittedDrafts)
        assertEquals(1, forks.registrations.size); assertEquals(1, forks.runs.size)

        model.closeFork(); advanceUntilIdle(); model.openFork()
        val second = model.fork.value.input!!
        assertEquals(ForkScope(parent.story, parent.branch), second.parent)
        assertEquals(parent.revision, second.expectedParentRevision)
        assertEquals(parent.revision, second.atRevision)
        assertNotEquals(first.childBranch, second.childBranch)
        assertFalse(model.fork.value.lookupOnly)
        assertNull(hint.value)
        assertEquals(1, forks.registrations.size); assertEquals(1, forks.runs.size)
        model.confirmFork(second, false); advanceUntilIdle()
        assertSame(second, model.fork.value.input)
        assertEquals(1, forks.registrations.size); assertEquals(1, forks.runs.size)
        model.confirmFork(second, true); advanceUntilIdle()
        assertEquals(listOf(first, second), forks.registrations.map { it.second })
        assertEquals(listOf(first.parent, second.parent), forks.registrations.map { it.first.parent })
        assertEquals(2, forks.runs.size)
        assertEquals(listOf("register", "run", "register", "run"), events.filter { it == "register" || it == "run" })
        assertEquals(listOf(firstRecovery, null, BranchForkRecovery(1, second)), hint.writes)
        assertEquals(BranchForkRecovery(1, second), hint.value)
        assertEquals(second.childBranch, model.fork.value.outcome!!.scope.branch)
        assertEquals(listOf(parent), stories.resumes) // The second fork never auto-resumes.
        assertEquals(canonicalBeforeForget, stories.saved())
        assertEquals(parent, model.state.value.selectedStory)
        assertEquals(parent.revision, model.state.value.revision)
        assertEquals(0, stories.submissions); assertEquals(0, stories.creates); assertEquals(0, stories.recoveries)
        assertTrue(forks.lookups.isEmpty())
    }
    @Test fun viewModelClearClosesForkBeforeTheSingleWorkspaceAndRetainsHint() = runTest(dispatcher) {
        val events = mutableListOf<String>(); val stories = Stories(events); val forks = Forks(events); val hint = Hint(events)
        val model = model(stories, forks, hint); advanceUntilIdle(); model.openFork()
        val input = model.fork.value.input!!; model.confirmFork(input, true); advanceUntilIdle()
        owners.clear(); advanceUntilIdle()
        assertTrue(events.indexOf("fork-close") >= 0)
        assertTrue(events.indexOf("fork-close") < events.indexOf("workspace-close"))
        assertEquals(BranchForkRecovery(1, input), hint.value)
        model.openFork(); model.confirmFork(input, true); model.resumeFork(BranchForkOutcome(1, ForkScope("story", "child"), input.parent, 0, 0, true))
        advanceUntilIdle(); assertEquals(1, forks.registrations.size)
    }
    @Test fun openingAndPendingTurnsHaveNoForkAdmissionAndOldLensCallbacksCannotConfirm() = runTest(dispatcher) {
        val events = mutableListOf<String>(); val stories = Stories(events); val forks = Forks(events)
        val gate = CompletableDeferred<Unit>(); stories.initializeGate = gate
        val model = model(stories, forks, Hint(events)); runCurrent(); model.openFork(); assertFalse(model.forkVisible.value)
        gate.complete(Unit); advanceUntilIdle(); model.openFork(); val old = model.fork.value.input!!
        model.closeFork(); model.openDiagnostics(); model.confirmFork(old, true); advanceUntilIdle()
        assertTrue(forks.registrations.isEmpty()); model.closeDiagnostics()
        val response = CompletableDeferred<Unit>(); stories.responseGate = response
        model.submit(DemoAction.GIVE_POTION); runCurrent(); model.openFork(); assertFalse(model.forkVisible.value)
        response.complete(Unit); advanceUntilIdle(); assertTrue(forks.registrations.isEmpty())
    }
    @Test fun successfulSaveCanSynchronouslyBackgroundVmWithoutLateDispatchOrLostIdentity() = runTest(dispatcher) {
        val events = mutableListOf<String>(); val stories = Stories(events); val forks = Forks(events); val hint = Hint(events)
        val model = model(stories, forks, hint); advanceUntilIdle(); model.openFork()
        val input = model.fork.value.input!!
        hint.onSave = { model.stopFork() }
        model.confirmFork(input, true); advanceUntilIdle()
        assertFalse(model.forkVisible.value); assertTrue(forks.registrations.isEmpty())
        assertEquals(BranchForkRecovery(1, input), hint.value)
        model.openFork(); model.lookupFork(); advanceUntilIdle()
        assertTrue(model.fork.value.lookupOnly); assertEquals(input, forks.lookups.single())
    }
    @Test fun lostRegistrationAckKeepsSameIdentityAndNeverAutomaticallyRetries() = runTest(dispatcher) {
        val events = mutableListOf<String>(); val stories = Stories(events); val forks = Forks(events).also { it.registerFailure = true }
        val hint = Hint(events); val model = model(stories, forks, hint); advanceUntilIdle(); model.openFork()
        val input = model.fork.value.input!!; model.confirmFork(input, true); advanceUntilIdle()
        assertEquals(1, forks.registrations.size); assertTrue(forks.runs.isEmpty()); assertTrue(model.fork.value.uncertain)
        forks.registerFailure = false; model.retryFork(false); advanceUntilIdle(); assertEquals(1, forks.registrations.size)
        model.retryFork(true); advanceUntilIdle()
        assertEquals(listOf(input, input), forks.registrations.map { it.second })
        assertEquals(BranchForkRecovery(1, input), hint.value)
    }
    @Test fun explicitRecoveredResumeRefreshesCurrentCatalogBeforeSelectingExactConfirmedChild() = runTest(dispatcher) {
        val events = mutableListOf<String>(); val stories = Stories(events)
        stories.selected = Other; stories.roots = listOf(Other)
        val outcome = BranchForkOutcome(1, ForkScope(Recovery.input.parent.story, Recovery.input.childBranch),
            Recovery.input.parent, Recovery.input.atRevision, 3, false)
        val forks = Forks(events).also { it.lookupResult = BranchForkLookup(true, outcome) }
        val hint = Hint(events, Recovery)
        val model = model(stories, forks, hint); advanceUntilIdle()
        model.openFork(); model.lookupFork(); advanceUntilIdle()
        assertSame(outcome, model.fork.value.outcome)
        assertEquals(listOf(Other), model.state.value.stories)
        assertEquals(Other, model.state.value.selectedStory)
        assertTrue(stories.resumes.isEmpty()); assertEquals(0, stories.snapshots)
        // Another owner has restored the story; only the actual explicit refresh reveals it.
        stories.onSnapshot = { stories.roots = listOf(Original, Other) }
        model.resumeFork(outcome.copy()); advanceUntilIdle()
        assertTrue(stories.resumes.isEmpty()); assertEquals(0, stories.snapshots)
        model.resumeFork(outcome); advanceUntilIdle()
        assertEquals(1, stories.snapshots)
        assertEquals(listOf(Original.copy(branch = Recovery.input.childBranch, revision = 3)), stories.resumes)
        assertEquals(Recovery.input.childBranch, model.state.value.selectedStory!!.branch)
        assertEquals(3L, model.state.value.revision)
        assertTrue(forks.registrations.isEmpty()); assertTrue(forks.runs.isEmpty())
        assertEquals(Recovery, hint.value)
    }
    private companion object {
        val Original = SavedStory("story", "main", "Original", 1)
        val Other = SavedStory("other-story", "main", "Other", 1)
        val Recovery = BranchForkRecovery(1, BranchForkInput(ForkScope("story", "main"), "restored-child", 1, 0))
    }
}

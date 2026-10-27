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

@OptIn(ExperimentalCoroutinesApi::class)
class OriginalStoryControllerTest {
    private val input=OriginalInput("A clockmaker crosses a frozen orchard.","Iris")
    private val proposal=OriginalProposal(listOf(OriginalLocation("Orchard","Frost covers the trees.")),0,
        listOf(OriginalCharacter("Tovin","A patient gardener.",0,listOf(0,1))),emptyList(),
        listOf(OriginalFact("The gate is shut.",listOf(1),0)),listOf(OriginalBelief(1,"The clock is late.","suspected")),emptyList())
    private class Port(val world: OriginalProposal): OriginalStoryGateway {
        val creates=mutableListOf<OriginalReview>(); val cancelled=mutableListOf<String>()
        lateinit var input: OriginalInput
        var generate: suspend ()->OriginalGenerated={ OriginalGenerated("job-1",input,world,"scripted") }
        var review: suspend (OriginalInput,OriginalProposal,String)->OriginalReview={ i,p,t -> OriginalReview("job-1","b".repeat(64),i,p,t,listOf("World truth: gate shut. Private belief: clock late.")) }
        var committing: suspend ()->Unit={}
        override suspend fun originalCapabilities()=OriginalCapabilities(true,"scripted")
        override suspend fun beginOriginal(input: OriginalInput): OriginalJob { this.input=input; return OriginalJob("job-1","a".repeat(64),"scripted") }
        override suspend fun generateOriginal(job: String)=generate()
        override suspend fun reviewOriginal(job: String,input: OriginalInput,proposal: OriginalProposal,title: String)=review(input,proposal,title)
        override suspend fun cancelOriginal(job: String): Boolean { cancelled+=job; return true }
        override suspend fun createOriginal(review: OriginalReview,creationId: String): SavedSnapshot {
            creates+=review; assertTrue(Regex("[0-9a-f]{32}").matches(creationId))
            committing()
            return SavedSnapshot(0,"Iris",emptyList(),"synthetic",1,emptyList(),SavedStory("original-$creationId","main",review.title,0))
        }
    }
    @Test fun editingRevokesConsentAndOnlyExactFreshReviewCreatesOnce()=runTest {
        val port=Port(proposal); lateinit var s: OriginalStoryUiState; val closed=mutableListOf<StoryCreationClose>()
        val c=OriginalStoryController(port,this,{s=it},closed::add)
        c.open(OriginalCapabilities(true,"scripted")); c.edit(s,input,null,"The Frozen Orchard")
        c.generate(s); advanceUntilIdle(); assertNotNull(s.proposal); assertTrue(port.creates.isEmpty())
        c.review(s); advanceUntilIdle(); val old=s; val review=s.review!!
        c.edit(s,s.input,s.proposal,"A Different Orchard"); assertNull(s.review)
        c.confirm(old,review); c.confirm(s,review); assertTrue(port.creates.isEmpty())
        c.review(s); advanceUntilIdle(); val fresh=s; val accepted=s.review!!
        c.confirm(fresh.copy(),accepted); c.confirm(fresh,accepted.copy()); assertTrue(port.creates.isEmpty())
        c.confirm(fresh,accepted); c.confirm(fresh,accepted); advanceUntilIdle()
        assertEquals(listOf(accepted),port.creates); assertEquals(1,closed.size); assertNotNull(closed.single().saved)
    }
    @Test fun lateGenerationIsDrainedBeforeCancelClosesAndNeverCreates()=runTest {
        val port=Port(proposal); lateinit var s: OriginalStoryUiState; val closed=mutableListOf<StoryCreationClose>()
        val gate=CompletableDeferred<OriginalGenerated>()
        port.generate={withContext(NonCancellable){gate.await()}}
        val c=OriginalStoryController(port,this,{s=it},closed::add)
        c.open(OriginalCapabilities(true,"scripted")); c.edit(s,input,null,"Orchard"); c.generate(s); runCurrent()
        c.dismiss(); runCurrent(); assertTrue(s.closing); assertTrue(closed.isEmpty())
        gate.complete(OriginalGenerated("job-1",input,proposal,"scripted")); advanceUntilIdle()
        assertEquals(listOf(StoryCreationClose()),closed); assertTrue(port.creates.isEmpty()); assertTrue(port.cancelled.contains("job-1"))
    }
    @Test fun foreignGenerationOrReviewCannotPublishConsent()=runTest {
        val port=Port(proposal); lateinit var s: OriginalStoryUiState
        val c=OriginalStoryController(port,this,{s=it}){}
        c.open(OriginalCapabilities(true,"scripted")); c.edit(s,input,null,"Orchard")
        port.generate={OriginalGenerated("foreign",input,proposal,"local")}; c.generate(s); advanceUntilIdle()
        assertNull(s.proposal); assertNull(s.review)
        port.generate={OriginalGenerated("job-1",input,proposal,"scripted")}; c.generate(s); advanceUntilIdle()
        port.review={i,p,t -> OriginalReview("foreign","b".repeat(64),i,p,t,emptyList())}
        c.review(s); advanceUntilIdle(); assertNull(s.review); assertTrue(port.creates.isEmpty()); c.dismiss(); advanceUntilIdle()
    }
    @Test fun disposalAndStaleEditorsCannotPublishOrCreate()=runTest {
        val port=Port(proposal); val values=mutableListOf<OriginalStoryUiState>()
        val gate=CompletableDeferred<OriginalGenerated>(); port.generate={withContext(NonCancellable){gate.await()}}
        val c=OriginalStoryController(port,this,values::add){}
        c.open(OriginalCapabilities(true,"scripted")); val old=values.last(); c.edit(old,input,null,"Orchard")
        val edited=values.last(); c.edit(old,input.copy(premise="Stale"),null,"Stale"); assertSame(edited,values.last())
        c.generate(edited); runCurrent(); c.dispose(); val count=values.size
        gate.complete(OriginalGenerated("job-1",input,proposal,"scripted")); advanceUntilIdle()
        c.generate(edited); c.edit(edited,input,null,"Late"); assertEquals(count,values.size); assertTrue(port.creates.isEmpty())
    }
    @Test fun nestedDraftsAreCopiedAndCastNamesTrackReviewedCharacters()=runTest {
        val port=Port(proposal); lateinit var s: OriginalStoryUiState
        val c=OriginalStoryController(port,this,{s=it}){}
        c.open(OriginalCapabilities(true,"scripted")); c.edit(s,input,null,"Orchard"); c.generate(s); advanceUntilIdle()
        val names=mutableListOf(0,1); val characters=mutableListOf(proposal.characters.single().copy(name="Sera",knownBy=names))
        c.edit(s,s.input,proposal.copy(characters=characters),s.title); names.clear(); characters.clear()
        assertEquals("Sera",s.input.cast.single().name); assertEquals(listOf(0,1),s.proposal!!.characters.single().knownBy)
        try { (s.proposal!!.characters as MutableList<*>).clear(); fail() } catch (_: UnsupportedOperationException) {}
        c.dismiss(); advanceUntilIdle()
    }
    @Test fun invalidInputStaysVisibleAndCannotGenerateOrCreate()=runTest {
        val port=Port(proposal); lateinit var s: OriginalStoryUiState
        val c=OriginalStoryController(port,this,{s=it}){}
        c.open(OriginalCapabilities(true,"scripted"))
        for(bad in listOf("", " outer", "line\nbreak", "a".repeat(1025),"\uD800")) {
            c.edit(s,input.copy(premise=bad),null,"Orchard"); c.generate(s); advanceUntilIdle()
            assertEquals(bad,s.input.premise); assertNull(s.job); assertTrue(port.creates.isEmpty())
        }
        c.dismiss(); advanceUntilIdle()
    }
    @Test fun disposalFromReadyFencesRetainedReviewAndEveryEditor()=runTest {
        val port=Port(proposal); val values=mutableListOf<OriginalStoryUiState>(); val closed=mutableListOf<StoryCreationClose>()
        val c=OriginalStoryController(port,this,values::add,closed::add)
        c.open(OriginalCapabilities(true,"scripted")); c.edit(values.last(),input,null,"Orchard")
        c.generate(values.last()); advanceUntilIdle(); c.review(values.last()); advanceUntilIdle()
        val ready=values.last(); val review=ready.review!!; c.dispose(); val count=values.size
        c.edit(ready,input,proposal,"Late"); c.confirm(ready,review); c.review(ready); c.generate(ready); c.dismiss(); advanceUntilIdle()
        assertEquals(count,values.size); assertTrue(port.creates.isEmpty()); assertTrue(closed.isEmpty())
        // No SDK/resource-reclamation claim: ShellViewModel owns shared transport retirement.
    }
    @Test fun disposalDuringCreateCannotPublishACommitThatReturnsLate()=runTest {
        val port=Port(proposal); val values=mutableListOf<OriginalStoryUiState>(); val closed=mutableListOf<StoryCreationClose>()
        val gate=CompletableDeferred<Unit>(); port.committing={withContext(NonCancellable){gate.await()}}
        val c=OriginalStoryController(port,this,values::add,closed::add)
        c.open(OriginalCapabilities(true,"scripted")); c.edit(values.last(),input,null,"Orchard")
        c.generate(values.last()); advanceUntilIdle(); c.review(values.last()); advanceUntilIdle()
        val ready=values.last(); c.confirm(ready,ready.review!!); runCurrent(); assertTrue(values.last().creating)
        c.dispose(); val count=values.size; gate.complete(Unit); advanceUntilIdle()
        assertEquals(1,port.creates.size); assertEquals(count,values.size); assertTrue(closed.isEmpty())
        // A late commit may exist. Cancelling the UI never asserts rollback or authorizes another Create.
    }
    @Test fun uncertainTemplateCreateCannotSwitchToOriginalOrLoseRequiredLibraryRefresh()=runTest {
        val port=Port(proposal); var writes=0; val closed=mutableListOf<StoryCreationClose>()
        val preview=StoryCreationPreview(DEFAULT_STORY_TEMPLATE,"a".repeat(64),"Lantern Quay","A built-in starter.","fantasy_v1",listOf("Player: Rowan"))
        val gateway=object: StoryCreationGateway {
            override fun originalStories(): OriginalStoryGateway=port
            override suspend fun preview()=preview
            override suspend fun create(request: StoryCreationRequest): SavedSnapshot {
                writes++; throw WorkspaceFailure("Io") // A native commit may have won before acknowledgement was lost.
            }
        }
        val c=StoryCreationController(gateway,this,closed::add)
        c.open(); advanceUntilIdle(); val rendered=c.state.value.review!!
        assertTrue(c.state.value.originalCapabilities!!.available)
        c.confirm(rendered); c.chooseOriginal(rendered); advanceUntilIdle()
        assertFalse(c.state.value.busy); assertNull(c.state.value.review); assertNull(c.state.value.original)
        c.chooseOriginal(rendered); c.confirm(rendered); advanceUntilIdle()
        assertNull(c.state.value.original); assertTrue(port.creates.isEmpty()); assertEquals(1,writes)
        c.dismiss(); advanceUntilIdle(); assertEquals(listOf(StoryCreationClose(refreshRequired=true)),closed)
        c.dispose()
    }
}

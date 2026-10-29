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
        c.edit(s,OriginalStoryEdit.Text(OriginalTextField.TITLE,"A Different Orchard")); assertNull(s.review)
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
        c.open(OriginalCapabilities(true,"scripted")); val old=values.last()
        c.edit(old,input.copy(cast=listOf(OriginalCast("Tovin","An orchard keeper."))),null,"Orchard") // Adding a row retires old indices.
        val edited=values.last(); c.edit(old,OriginalStoryEdit.Text(OriginalTextField.PREMISE,"Stale")); assertSame(edited,values.last())
        c.generate(edited); runCurrent(); c.dispose(); val count=values.size
        gate.complete(OriginalGenerated("job-1",port.input,proposal,"scripted")); advanceUntilIdle()
        c.generate(edited); c.edit(edited,OriginalStoryEdit.Text(OriginalTextField.TITLE,"Late")); assertEquals(count,values.size); assertTrue(port.creates.isEmpty())
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
            c.edit(s,OriginalStoryEdit.Text(OriginalTextField.PREMISE,bad)); c.generate(s); advanceUntilIdle()
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
        c.edit(ready,OriginalStoryEdit.Text(OriginalTextField.TITLE,"Late")); c.confirm(ready,review); c.review(ready); c.generate(ready); c.dismiss(); advanceUntilIdle()
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
        val creating=values.last(); c.edit(ready,OriginalStoryEdit.Text(OriginalTextField.PLAYER_NAME,"Late"))
        assertSame(creating,values.last())
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
    @Test fun sameRenderInputAndCastTextEditsKeepLatestCharactersAndFields()=runTest {
        val port=Port(proposal); lateinit var s: OriginalStoryUiState
        val c=OriginalStoryController(port,this,{s=it}){}
        c.open(OriginalCapabilities(true,"scripted"))
        c.edit(s,input.copy(cast=listOf(OriginalCast("Tovin","A gardener."))),null,"Orchard")
        val rendered=s
        c.edit(rendered,OriginalStoryEdit.Text(OriginalTextField.PREMISE,"A"))
        c.edit(rendered,OriginalStoryEdit.Text(OriginalTextField.PREMISE,"AB"))
        c.edit(rendered,OriginalStoryEdit.Text(OriginalTextField.PLAYER_DESCRIPTION,"A clockmaker."))
        c.edit(rendered,OriginalStoryEdit.Text(OriginalTextField.CAST_NAME,"Sera",0))
        c.edit(rendered,OriginalStoryEdit.Text(OriginalTextField.CAST_DESCRIPTION,"An orchard keeper.",0))
        c.edit(rendered,OriginalStoryEdit.Text(OriginalTextField.TITLE,"The Frozen Orchard"))
        assertEquals("AB",s.input.premise); assertEquals("A clockmaker.",s.input.playerDescription)
        assertEquals(OriginalCast("Sera","An orchard keeper."),s.input.cast.single()); assertEquals("The Frozen Orchard",s.title)
        assertNull(s.review); assertTrue(port.creates.isEmpty()); c.dismiss(); advanceUntilIdle()
    }
    @Test fun sameRenderWorldTextAndReferenceChoicesMergeWithoutRollback()=runTest {
        val world=proposal.copy(locations=proposal.locations+OriginalLocation("Courtyard","An open courtyard."))
        val port=Port(world); lateinit var s: OriginalStoryUiState
        val c=OriginalStoryController(port,this,{s=it}){}
        c.open(OriginalCapabilities(true,"scripted")); c.edit(s,input,null,"Orchard"); c.generate(s); advanceUntilIdle()
        val rendered=s
        c.edit(rendered,OriginalStoryEdit.Text(OriginalTextField.CHARACTER_NAME,"Sera",0))
        c.edit(rendered,OriginalStoryEdit.Text(OriginalTextField.CHARACTER_DESCRIPTION,"An orchard keeper.",0))
        c.edit(rendered,OriginalStoryEdit.Text(OriginalTextField.FACT_TEXT,"The gate is open.",0))
        c.edit(rendered,OriginalStoryEdit.ToggleKnown(OriginalKnown.FACT,0,0))
        c.edit(rendered,OriginalStoryEdit.ToggleKnown(OriginalKnown.FACT,0,1))
        c.edit(rendered,OriginalStoryEdit.ToggleRoute(0,1))
        c.edit(rendered,OriginalStoryEdit.ToggleRoute(1,0))
        assertEquals("Sera",s.proposal!!.characters.single().name); assertEquals("An orchard keeper.",s.proposal!!.characters.single().description)
        assertEquals("Sera",s.input.cast.single().name); assertEquals("The gate is open.",s.proposal!!.facts.single().text)
        assertEquals(listOf(0),s.proposal!!.facts.single().knownBy)
        assertEquals(setOf(OriginalRoute(0,1),OriginalRoute(1,0)),s.proposal!!.routes.toSet())
        assertNull(s.review); assertTrue(port.creates.isEmpty()); c.dismiss(); advanceUntilIdle()
    }
    @Test fun reviewAndStructuralChangesRetireEarlierEditorsAndConsent()=runTest {
        val port=Port(proposal); lateinit var s: OriginalStoryUiState
        val c=OriginalStoryController(port,this,{s=it}){}
        c.open(OriginalCapabilities(true,"scripted")); c.edit(s,input,null,"Orchard"); c.generate(s); advanceUntilIdle()
        val old=s; c.review(old); advanceUntilIdle(); val reviewed=s; val consent=s.review!!
        c.edit(old,OriginalStoryEdit.Text(OriginalTextField.PREMISE,"Stale pre-review callback"))
        assertSame(reviewed,s); assertSame(consent,s.review)
        c.edit(reviewed,OriginalStoryEdit.Remove(OriginalRows.FACT,0))
        val structural=s
        c.edit(reviewed,OriginalStoryEdit.Text(OriginalTextField.FACT_TEXT,"Stale removed row",0))
        c.confirm(reviewed,consent); c.confirm(s,consent); assertSame(structural,s); assertNull(s.review)
        assertTrue(s.proposal!!.facts.isEmpty()); assertTrue(port.creates.isEmpty()); c.dismiss(); advanceUntilIdle()
    }
    @Test fun structuralCastInsertionRemovalAndReorderRetireOldRowIndices()=runTest {
        val port=Port(proposal); lateinit var s: OriginalStoryUiState
        val c=OriginalStoryController(port,this,{s=it}){}
        c.open(OriginalCapabilities(true,"scripted"))
        c.edit(s,input.copy(cast=listOf(OriginalCast("One","First."),OriginalCast("Two","Second."))),null,"Orchard")
        val first=s
        c.edit(first,OriginalStoryEdit.Move(OriginalRows.CAST,0,1))
        val reordered=s; assertNotSame(first.editorEpoch,s.editorEpoch); assertEquals("Two",s.input.cast.first().name)
        c.edit(first,OriginalStoryEdit.Text(OriginalTextField.CAST_NAME,"Wrong",0)); assertSame(reordered,s)
        c.edit(reordered,OriginalStoryEdit.Remove(OriginalRows.CAST,1))
        val removed=s; assertNotSame(reordered.editorEpoch,s.editorEpoch)
        c.edit(reordered,OriginalStoryEdit.Text(OriginalTextField.PLAYER_DESCRIPTION,"Late removed-row frame")); assertSame(removed,s)
        c.edit(removed,OriginalStoryEdit.Add(OriginalRows.CAST))
        val addedRow=s
        c.edit(addedRow,OriginalStoryEdit.Text(OriginalTextField.CAST_NAME,"Three",1))
        c.edit(addedRow,OriginalStoryEdit.Text(OriginalTextField.CAST_DESCRIPTION,"Third.",1))
        val added=s; assertNotSame(removed.editorEpoch,s.editorEpoch)
        c.edit(removed,OriginalStoryEdit.Text(OriginalTextField.PLAYER_NAME,"Late")); assertSame(added,s)
        assertEquals(listOf("Two","Three"),s.input.cast.map { it.name }); assertNull(s.review); c.dismiss(); advanceUntilIdle()
    }
    @Test fun explicitDuplicateRowRemovalKeepsTheCorrectConcurrentTextEdit()=runTest {
        val world=proposal.copy(facts=listOf(proposal.facts.single(),proposal.facts.single()))
        val port=Port(world); lateinit var s: OriginalStoryUiState
        val c=OriginalStoryController(port,this,{s=it}){}
        c.open(OriginalCapabilities(true,"scripted")); c.edit(s,input,null,"Orchard"); c.generate(s); advanceUntilIdle()
        val rendered=s
        c.edit(rendered,OriginalStoryEdit.Text(OriginalTextField.FACT_TEXT,"Keep this edit.",0))
        c.edit(rendered,OriginalStoryEdit.Remove(OriginalRows.FACT,1))
        assertEquals(1,s.proposal!!.facts.size); assertEquals("Keep this edit.",s.proposal!!.facts[0].text)
        assertNotSame(rendered.editorEpoch,s.editorEpoch); assertNull(s.review)
        val fresh=s; c.edit(rendered,OriginalStoryEdit.Text(OriginalTextField.FACT_TEXT,"Stale",0)); assertSame(fresh,s)
        assertEquals(listOf("Keep this edit."),s.proposal!!.facts.map { it.text }); c.dismiss(); advanceUntilIdle()
    }
    @Test fun generationAndCancelRetireOldAndBusyEditorCallbacks()=runTest {
        val port=Port(proposal); lateinit var s: OriginalStoryUiState; val closed=mutableListOf<StoryCreationClose>()
        val c=OriginalStoryController(port,this,{s=it},closed::add)
        c.open(OriginalCapabilities(true,"scripted")); c.edit(s,input,null,"Orchard")
        val before=s; c.generate(before); val generating=s; advanceUntilIdle(); val ready=s
        assertNotSame(before.editorEpoch,ready.editorEpoch); assertNotSame(generating.editorEpoch,ready.editorEpoch)
        c.edit(before,OriginalStoryEdit.Text(OriginalTextField.PREMISE,"Before generation"))
        c.edit(generating,OriginalStoryEdit.Text(OriginalTextField.PREMISE,"During generation"))
        assertSame(ready,s)
        c.dismiss(); val closing=s; assertNotSame(ready.editorEpoch,closing.editorEpoch)
        c.edit(ready,OriginalStoryEdit.Text(OriginalTextField.PLAYER_NAME,"Late")); assertSame(closing,s)
        advanceUntilIdle(); assertEquals(listOf(StoryCreationClose()),closed); assertTrue(port.creates.isEmpty())
    }
    @Test fun sameRenderTextCanReturnToOriginalWithoutLosingOtherEdits()=runTest {
        val port=Port(proposal); lateinit var s: OriginalStoryUiState
        val c=OriginalStoryController(port,this,{s=it}){}
        c.open(OriginalCapabilities(true,"scripted"))
        c.edit(s,input.copy(cast=listOf(OriginalCast("Tovin","A gardener."))),null,"Orchard")
        val rendered=s
        for((field,original) in listOf(OriginalTextField.TITLE to rendered.title,OriginalTextField.PREMISE to rendered.input.premise,
            OriginalTextField.PLAYER_NAME to rendered.input.playerName,OriginalTextField.CAST_NAME to rendered.input.cast.single().name)) {
            c.edit(rendered,OriginalStoryEdit.Text(field,original+"!"))
            c.edit(rendered,OriginalStoryEdit.Text(OriginalTextField.PLAYER_DESCRIPTION,"Keep this independent edit."))
            c.edit(rendered,OriginalStoryEdit.Text(field,original)) // Explicit backspace to the rendered value is still an edit.
        }
        c.edit(rendered,OriginalStoryEdit.Text(OriginalTextField.CAST_DESCRIPTION,"Keep the nested description.",0))
        assertEquals(rendered.title,s.title); assertEquals(rendered.input.premise,s.input.premise); assertEquals(rendered.input.playerName,s.input.playerName)
        assertEquals("Tovin",s.input.cast.single().name); assertEquals("Keep the nested description.",s.input.cast.single().description)
        assertEquals("Keep this independent edit.",s.input.playerDescription); assertSame(rendered.editorEpoch,s.editorEpoch)
        assertNull(s.review); c.dismiss(); advanceUntilIdle()
    }
    @Test fun sameRenderNestedTextAndAbsoluteChoicesCanReturnToOriginal()=runTest {
        val world=proposal.copy(locations=proposal.locations+OriginalLocation("Courtyard","An open courtyard."),
            possessions=listOf(OriginalPossession("Token","A brass token.",0,null)))
        val port=Port(world); lateinit var s: OriginalStoryUiState
        val c=OriginalStoryController(port,this,{s=it}){}
        c.open(OriginalCapabilities(true,"scripted")); c.edit(s,input,null,"Orchard"); c.generate(s); advanceUntilIdle()
        val rendered=s; val p=s.proposal!!
        c.edit(rendered,OriginalStoryEdit.Text(OriginalTextField.CHARACTER_NAME,p.characters[0].name+"!",0))
        c.edit(rendered,OriginalStoryEdit.Text(OriginalTextField.CHARACTER_DESCRIPTION,"Keep this character edit.",0))
        c.edit(rendered,OriginalStoryEdit.Text(OriginalTextField.CHARACTER_NAME,p.characters[0].name,0))
        c.edit(rendered,OriginalStoryEdit.Text(OriginalTextField.FACT_TEXT,p.facts[0].text+"!",0))
        c.edit(rendered,OriginalStoryEdit.Text(OriginalTextField.FACT_TEXT,p.facts[0].text,0))
        for((field,away,back) in listOf(Triple(OriginalSelection.PROFILE,0,1),Triple(OriginalSelection.TONE,1,0),
            Triple(OriginalSelection.PLAYER_LOCATION,1,0),Triple(OriginalSelection.CHARACTER_LOCATION,1,0),
            Triple(OriginalSelection.FACT_DISCOVERABLE,0,1),Triple(OriginalSelection.BELIEF_BELIEVER,0,1),
            Triple(OriginalSelection.BELIEF_CONFIDENCE,2,1),Triple(OriginalSelection.POSSESSION_OWNER,1,0),Triple(OriginalSelection.POSSESSION_RETURN,2,0))) {
            c.edit(rendered,OriginalStoryEdit.Select(field,away)); c.edit(rendered,OriginalStoryEdit.Select(field,back))
        }
        assertEquals(rendered.input.profile,s.input.profile); assertEquals(rendered.input.presentation,s.input.presentation)
        assertEquals(p,s.proposal!!.copy(characters=s.proposal!!.characters.map { it.copy(description=p.characters[0].description) }))
        assertEquals("Keep this character edit.",s.proposal!!.characters[0].description); assertEquals(p.characters[0].name,s.input.cast.single().name)
        assertNull(s.review); c.dismiss(); advanceUntilIdle()
    }
    @Test fun sameRenderReferenceTogglesUseLatestStateAndOldEpochsCannotAct()=runTest {
        val world=proposal.copy(locations=proposal.locations+OriginalLocation("Courtyard","An open courtyard."))
        val port=Port(world); lateinit var s: OriginalStoryUiState
        val c=OriginalStoryController(port,this,{s=it}){}
        c.open(OriginalCapabilities(true,"scripted")); c.edit(s,input,null,"Orchard"); c.generate(s); advanceUntilIdle()
        val rendered=s
        c.edit(rendered,OriginalStoryEdit.ToggleKnown(OriginalKnown.FACT,0,0)); c.edit(rendered,OriginalStoryEdit.ToggleKnown(OriginalKnown.FACT,0,1))
        assertEquals(listOf(0),s.proposal!!.facts[0].knownBy)
        c.edit(rendered,OriginalStoryEdit.ToggleKnown(OriginalKnown.FACT,0,0)); c.edit(rendered,OriginalStoryEdit.ToggleKnown(OriginalKnown.FACT,0,1))
        assertEquals(rendered.proposal!!.facts[0].knownBy,s.proposal!!.facts[0].knownBy)
        c.edit(rendered,OriginalStoryEdit.ToggleKnown(OriginalKnown.CHARACTER,0,0)); c.edit(rendered,OriginalStoryEdit.ToggleKnown(OriginalKnown.CHARACTER,0,0))
        assertEquals(rendered.proposal.characters[0].knownBy.toSet(),s.proposal!!.characters[0].knownBy.toSet())
        c.edit(rendered,OriginalStoryEdit.ToggleRoute(0,1)); c.edit(rendered,OriginalStoryEdit.ToggleRoute(1,0))
        assertEquals(setOf(OriginalRoute(0,1),OriginalRoute(1,0)),s.proposal!!.routes.toSet())
        c.edit(rendered,OriginalStoryEdit.ToggleRoute(0,1)); assertEquals(listOf(OriginalRoute(1,0)),s.proposal!!.routes)
        c.edit(rendered,OriginalStoryEdit.ToggleRoute(1,0)); assertTrue(s.proposal!!.routes.isEmpty())
        c.review(s); advanceUntilIdle(); val accepted=s; val review=s.review!!
        c.edit(rendered,OriginalStoryEdit.ToggleKnown(OriginalKnown.FACT,0,0)); c.edit(rendered,OriginalStoryEdit.ToggleRoute(0,1))
        assertSame(accepted,s); assertSame(review,s.review); assertTrue(port.creates.isEmpty())
        c.edit(accepted,OriginalStoryEdit.Text(OriginalTextField.TITLE,accepted.title)); assertNull(s.review)
        c.confirm(accepted,review); c.confirm(s,review); assertTrue(port.creates.isEmpty())
        c.dismiss(); advanceUntilIdle()
    }
}

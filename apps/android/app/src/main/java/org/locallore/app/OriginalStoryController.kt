/* Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0 */
package org.locallore.app

import java.util.UUID
import kotlinx.coroutines.CancellationException
import kotlinx.coroutines.CoroutineScope
import kotlinx.coroutines.CoroutineStart
import kotlinx.coroutines.Job
import kotlinx.coroutines.NonCancellable
import kotlinx.coroutines.currentCoroutineContext
import kotlinx.coroutines.launch
import kotlinx.coroutines.withContext

internal data class OriginalStoryUiState(val input: OriginalInput = OriginalInput(), val proposal: OriginalProposal? = null,
    val title: String = "Original story", val provider: String, val job: String? = null, val review: OriginalReview? = null,
    val busy: Boolean = false, val creating: Boolean = false, val closing: Boolean = false, val notice: String? = null,
    val editorEpoch: Any = Any())

/** Drafts are inert author intent. Only an exact, explicitly reviewed native capability can create. */
internal class OriginalStoryController(private val gateway: OriginalStoryGateway, private val scope: CoroutineScope,
    private val publish: (OriginalStoryUiState) -> Unit, private val closed: (StoryCreationClose) -> Unit) {
    private var state: OriginalStoryUiState? = null
    private var generation = 0L
    private var active: Job? = null
    private var disposed = false
    private var createStarted = false
    private val creationId = UUID.randomUUID().toString().replace("-", "")
    fun open(capabilities: OriginalCapabilities) {
        if (disposed || state != null || !capabilities.available) return
        update(OriginalStoryUiState(provider=checkNotNull(capabilities.provider)))
    }
    private fun update(value: OriginalStoryUiState) { state=value; if(!disposed) publish(value) }
    private fun editable(expected: OriginalStoryUiState) = !disposed && state === expected && !expected.busy && !expected.closing && !createStarted
    fun edit(expected: OriginalStoryUiState, input: OriginalInput, proposal: OriginalProposal?, title: String) {
        val before=state ?: return
        if(disposed || before.editorEpoch !== expected.editorEpoch || expected.busy || expected.creating || expected.closing ||
            before.busy || before.creating || before.closing || createStarted) return
        if((expected.proposal==null)!=(proposal==null) || (before.proposal==null)!=(proposal==null))return
        // Every field intent revokes captured consent, even an equal-value edit.
        generation++
        val merged: OriginalInput
        val captured: OriginalProposal?
        try {
            merged=mergeOriginalInput(expected.input,input,before.input,mergeCast=proposal==null)
            captured=if(proposal==null)null else mergeOriginalWorld(checkNotNull(expected.proposal),proposal,checkNotNull(before.proposal)).frozen()
        } catch (_: OriginalEditConflict) {
            update(before.copy(editorEpoch=Any(),review=null,notice="The draft changed. Check the latest rows and try again.")); return
        }
        val reviewedInput = if(captured == null) merged.frozen() else merged.copy(
            cast=captured.characters.map { OriginalCast(it.name,it.description) }).frozen()
        update(before.copy(input=reviewedInput,proposal=captured,title=mergeOriginalTitle(expected.title,title,before.title),review=null,
            editorEpoch=if(originalStructureChanged(expected.input,input,expected.proposal,proposal))Any() else before.editorEpoch,
            notice="Review all changes before creating. Nothing is saved yet."))
    }
    fun generate(expected: OriginalStoryUiState) {
        if(!editable(expected) || !validOriginalInput(expected.input)) return
        val ticket=++generation; val input=expected.input.frozen()
        update(expected.copy(busy=true,review=null,editorEpoch=Any(),notice=if(expected.provider=="local") "Generating a draft locally…" else "Generating a synthetic scripted draft…"))
        run(ticket) {
            var begun: String? = null
            try {
                expected.job?.let { check(gateway.cancelOriginal(it)) }
                val job=gateway.beginOriginal(input); begun=job.job
                check(job.provider==expected.provider)
                if(current(ticket)) update(checkNotNull(state).copy(job=job.job))
                val generated=gateway.generateOriginal(job.job)
                check(generated.job==job.job && generated.provider==job.provider && generated.input==input)
                val proposal=generated.proposal.frozen()
                if(current(ticket)) update(checkNotNull(state).copy(input=input,proposal=proposal,review=null,editorEpoch=Any(),
                    notice="Edit the cast and world, then choose Review changes. World truth and private beliefs are separate."))
            } finally {
                if(!current(ticket) && begun!=null) withContext(NonCancellable) { gateway.cancelOriginal(checkNotNull(begun)) }
            }
        }
    }
    fun review(expected: OriginalStoryUiState) {
        val proposal=expected.proposal ?: return; val job=expected.job ?: return
        if(!editable(expected) || !validStoryTitle(expected.title) || !validOriginalDraft(expected.input,proposal)) return
        val ticket=++generation; val input=expected.input.frozen(); val captured=proposal.frozen(); val title=expected.title
        update(expected.copy(busy=true,review=null,editorEpoch=Any(),notice="Reviewing the starting world…"))
        run(ticket) {
            val result=gateway.reviewOriginal(job,input,captured,title).frozen()
            check(result.job==job && result.input==input && result.proposal==captured && result.title==title)
            if(current(ticket)) update(checkNotNull(state).copy(review=result,editorEpoch=Any(),notice="Read the accepted starting world. Only Create saves it."))
        }
    }
    fun confirm(expected: OriginalStoryUiState, review: OriginalReview) {
        if(!editable(expected) || expected.review !== review || review.job!=expected.job || review.input!=expected.input ||
            review.proposal!=expected.proposal || review.title!=expected.title) return
        createStarted=true; val ticket=++generation
        update(expected.copy(review=null,busy=true,creating=true,editorEpoch=Any(),notice="Creating the reviewed story. If stopped, refresh the library before trying again."))
        run(ticket) { val saved=gateway.createOriginal(review,creationId)
            if(current(ticket)) { generation++; state=null; closed(StoryCreationClose(saved=saved)) } }
    }
    fun dismiss() {
        val before=state ?: return
        if(disposed || before.closing) return
        val ticket=++generation; val previous=active
        update(before.copy(review=null,closing=true,busy=true,editorEpoch=Any(),notice="Finishing local work…"))
        active=scope.launch(start=CoroutineStart.LAZY) {
            previous?.join()
            try {
                val cancelled=before.job?.let { gateway.cancelOriginal(it) } ?: true
                if(!disposed && generation==ticket) { state=null; closed(StoryCreationClose(refreshRequired=createStarted || !cancelled)) }
            } catch (_: Exception) {
                if(!disposed && generation==ticket) update(checkNotNull(state).copy(notice="Local work could not be confirmed as finished. Close the app before continuing. No automatic retry was made."))
            }
        }
        previous?.cancel(); active?.start()
    }
    // This fences publication only. The parent retires the shared transport; cancellation is not SDK cleanup proof.
    fun dispose() { if(disposed)return; disposed=true; generation++; active?.cancel(); state=null }
    private fun current(ticket: Long)=!disposed && generation==ticket && state?.closing==false
    private fun run(ticket: Long, block: suspend () -> Unit) {
        active=scope.launch(start=CoroutineStart.LAZY) {
            try { block() } catch(cancelled: CancellationException) { throw cancelled }
            catch (_: Exception) { if(current(ticket)) update(checkNotNull(state).copy(review=null,
                notice=if(createStarted) "Creation could not be confirmed. Close to refresh the library." else "The draft could not be reviewed or generated. Nothing was created. Cancel to finish local work.")) }
            finally { if(active===currentCoroutineContext()[Job])active=null
                if(current(ticket))update(checkNotNull(state).copy(busy=false,creating=false)) }
        }; active?.start()
    }
}

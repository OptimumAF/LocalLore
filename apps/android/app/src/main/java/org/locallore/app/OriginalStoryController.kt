/* Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0 */
package org.locallore.app

import java.util.UUID
import kotlinx.coroutines.CancellationException
import kotlinx.coroutines.CoroutineScope
import kotlinx.coroutines.CoroutineStart
import kotlinx.coroutines.Job
import kotlinx.coroutines.NonCancellable
import kotlinx.coroutines.currentCoroutineContext
import kotlinx.coroutines.ensureActive
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
    // A native job may be acknowledged after the visible editor has retired.
    private var nativeJob: String? = null
    private var beginUnconfirmed = false
    private val creationId = UUID.randomUUID().toString().replace("-", "")
    fun open(capabilities: OriginalCapabilities) {
        if (disposed || state != null || !capabilities.available) return
        update(OriginalStoryUiState(provider=checkNotNull(capabilities.provider)))
    }
    private fun update(value: OriginalStoryUiState) { state=value; if(!disposed) publish(value) }
    private fun editable(expected: OriginalStoryUiState) = !disposed && state === expected && !expected.busy && !expected.closing && !createStarted
    /** Coherent whole-draft replacement requires the exact current view and retires all editors. */
    fun edit(expected: OriginalStoryUiState, input: OriginalInput, proposal: OriginalProposal?, title: String) {
        if(!editable(expected) || expected.creating || (expected.proposal==null)!=(proposal==null))return
        generation++
        publishEdit(expected.copy(input=input,proposal=proposal,title=title),Any())
    }
    /** Every actual form callback names its field or toggle; equal values remain explicit intents. */
    fun edit(expected: OriginalStoryUiState, intent: OriginalStoryEdit) {
        val before=state ?: return
        if(disposed || before.editorEpoch !== expected.editorEpoch || expected.busy || expected.creating || expected.closing ||
            before.busy || before.creating || before.closing || createStarted) return
        val next=try { applyOriginalEdit(before,intent) } catch (_: OriginalEditRefused) { return }
        generation++
        publishEdit(next,if(intent.structural())Any() else before.editorEpoch)
    }
    private fun publishEdit(next: OriginalStoryUiState,epoch: Any) {
        val captured=next.proposal?.frozen()
        val reviewedInput = if(captured == null) next.input.frozen() else next.input.copy(
            cast=captured.characters.map { OriginalCast(it.name,it.description) }).frozen()
        update(next.copy(input=reviewedInput,proposal=captured,review=null,editorEpoch=epoch,
            notice="Review all changes before creating. Nothing is saved yet."))
    }
    fun generate(expected: OriginalStoryUiState) {
        if(!editable(expected) || !OriginalStoryWire.valid(expected.input)) return
        val ticket=++generation; val input=expected.input.frozen()
        update(expected.copy(busy=true,job=null,review=null,editorEpoch=Any(),notice=if(expected.provider=="local") "Generating a draft locally…" else "Generating a synthetic scripted draft…"))
        if (!current(ticket)) return
        run(ticket) {
            var begun: String? = null
            try {
                // Observe finite control replies even when dismiss cancels this caller. Never
                // carry that cancellation shield into model generation.
                val job = withContext(NonCancellable) {
                    if (!current(ticket)) return@withContext null
                    nativeJob?.let {
                        check(gateway.cancelOriginal(it))
                        nativeJob = null
                    }
                    if (!current(ticket)) return@withContext null
                    begin(input).also {
                        nativeJob = it.job
                        begun = it.job
                    }
                } ?: return@run
                if (!current(ticket)) return@run
                check(job.provider==expected.provider)
                currentCoroutineContext().ensureActive()
                val generated=gateway.generateOriginal(job.job)
                check(generated.job==job.job && generated.provider==job.provider && generated.input==input)
                val proposal=generated.proposal.frozen()
                if(current(ticket)) update(checkNotNull(state).copy(input=input,proposal=proposal,job=job.job,review=null,editorEpoch=Any(),
                    notice="Edit the cast and world, then choose Review changes. World truth and private beliefs are separate."))
            } finally {
                // Dismiss joins this job and owns its cancellation acknowledgement.
                if(disposed && begun!=null) withContext(NonCancellable) { gateway.cancelOriginal(checkNotNull(begun)) }
            }
        }
    }
    private suspend fun begin(input: OriginalInput): OriginalJob {
        val priorUnconfirmed = beginUnconfirmed
        beginUnconfirmed = true
        try {
            return gateway.beginOriginal(input).also { beginUnconfirmed = false }
        } catch (failure: Exception) {
            // These Begin rejections occur before Rust installs a job. An unreadable or missing
            // reply gives no job ID to cancel and cannot prove that the dialog is safe to close.
            if (failure is LocalInferenceBusy || failure is WorkspaceFailure &&
                failure.category in setOf("Closed", "Busy", "Unsupported", "IdExhausted", "InvalidInput", "TooLarge")) {
                beginUnconfirmed = priorUnconfirmed
            }
            throw failure
        }
    }
    fun review(expected: OriginalStoryUiState) {
        val proposal=expected.proposal ?: return; val job=expected.job ?: return
        if(!editable(expected) || !validStoryTitle(expected.title) || !validOriginalDraft(expected.input,proposal) ||
            !OriginalStoryWire.valid(expected.input,proposal)) return
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
                check(!beginUnconfirmed)
                val cancelled=nativeJob?.let { gateway.cancelOriginal(it) } ?: true
                nativeJob = null
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

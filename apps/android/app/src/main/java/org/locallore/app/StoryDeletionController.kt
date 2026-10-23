/* Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0 */
package org.locallore.app

import java.util.Collections
import kotlinx.coroutines.CancellationException
import kotlinx.coroutines.CoroutineScope
import kotlinx.coroutines.CoroutineStart
import kotlinx.coroutines.Job
import kotlinx.coroutines.currentCoroutineContext
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.launch

data class StoryDeletionPreview(
    val version: Int,
    val storyId: String,
    val title: String,
    val rootBranch: String,
    val branchHeads: Map<String, Long>,
    val committedTurns: Long,
    val draftTurns: Long,
    val noncommittedTurns: Long,
    val derivedPackets: Long,
    val rows: Map<String, Long>,
    val privacyWarning: String,
)
data class StoryDeletionPrepared(val token: Long, val preview: StoryDeletionPreview)
data class StoryDeleted(val storyId: String, val deletedBranches: Long, val deletedTurns: Long)
data class StoryDeletionUiState(
    val visible: Boolean = false,
    val busy: Boolean = false,
    val closing: Boolean = false,
    val selected: SavedStory? = null,
    val prepared: StoryDeletionPrepared? = null,
    val deleted: StoryDeleted? = null,
    val notice: String? = null,
)
internal interface StoryDeletionGateway {
    suspend fun prepare(story: SavedStory): StoryDeletionPrepared
    suspend fun commit(token: Long): StoryDeleted
    fun cancel()
    fun close()
}
internal class StoryDeletionFailure(val category: String) : Exception("Story deletion failed")

/** Owner-thread consent only. Native preview/commit own deletion rules and authoritative counts. */
internal class StoryDeletionController(
    private val scope: CoroutineScope,
    private val gateway: StoryDeletionGateway,
    private val onClosed: (StoryDeleted?) -> Unit,
) {
    private val mutable = MutableStateFlow(StoryDeletionUiState())
    val state = mutable.asStateFlow()
    private var generation = 0L
    private var active: Job? = null
    private var disposed = false
    private var commitAttempted = false

    /** Opening starts one preview, never a deletion. Errors require close and a fresh open. */
    fun open(story: SavedStory) {
        if (disposed || mutable.value.visible || active != null) return
        commitAttempted = false
        mutable.value = StoryDeletionUiState(visible = true, selected = story)
        work(commit = false) { ticket ->
            val prepared = gateway.prepare(story)
            val preview = prepared.preview.copy(
                branchHeads = Collections.unmodifiableMap(LinkedHashMap(prepared.preview.branchHeads)),
                rows = Collections.unmodifiableMap(LinkedHashMap(prepared.preview.rows)),
            )
            if (current(ticket)) mutable.value = mutable.value.copy(prepared = prepared.copy(preview = preview),
                notice = "Review the complete native deletion preview. Nothing is deleted until you confirm.")
        }
    }

    fun confirm(expected: StoryDeletionPrepared) {
        if (disposed || !mutable.value.visible || mutable.value.busy || mutable.value.closing || mutable.value.deleted != null) return
        val prepared = mutable.value.prepared ?: return
        if (prepared !== expected) return // A retained old dialog cannot borrow a newer story's consent.
        // Consume consent before starting IO, including failures and uncertain acknowledgements.
        mutable.value = mutable.value.copy(prepared = null)
        commitAttempted = true
        work(commit = true) { ticket ->
            val deleted = gateway.commit(prepared.token)
            if (current(ticket)) mutable.value = mutable.value.copy(deleted = deleted,
                notice = "Story deletion completed. Close to refresh the saved-story library.")
        }
    }

    /** Both routes close after actual coroutine drain; callers must always reconcile the library. */
    fun cancel() = dismiss()
    fun dismiss() {
        if (disposed || !mutable.value.visible || mutable.value.closing) return
        val ticket = ++generation
        val previous = active
        val accepted = mutable.value.deleted
        mutable.value = mutable.value.copy(prepared = null, closing = true, busy = previous != null,
            notice = if (commitAttempted && accepted == null)
                "Deletion may already have completed. Waiting for work to finish before refreshing the library."
            else "Closing and waiting for local work to finish before refreshing the library.")
        gateway.cancel()
        previous?.cancel()
        scope.launch {
            previous?.join()
            if (disposed || generation != ticket) return@launch
            active = null
            // Revoke any capability returned by a noncooperative preview after the first cancel.
            gateway.cancel()
            mutable.value = StoryDeletionUiState()
            // Null means no accepted acknowledgement, not proof that deletion did not occur.
            onClosed(accepted)
        }
    }

    fun dispose() {
        if (disposed) return
        disposed = true
        generation++
        gateway.cancel()
        active?.cancel()
        gateway.close()
        mutable.value = StoryDeletionUiState()
    }
    private fun current(ticket: Long) = !disposed && generation == ticket && mutable.value.visible && !mutable.value.closing
    private fun work(commit: Boolean, block: suspend (Long) -> Unit) {
        val ticket = ++generation
        mutable.value = mutable.value.copy(busy = true, notice = null)
        val job = scope.launch(start = CoroutineStart.LAZY) {
            try { block(ticket) }
            catch (cancelled: CancellationException) {
                if (current(ticket)) mutable.value = mutable.value.copy(notice = deletionNotice(cancelled, commit))
                throw cancelled
            } catch (failure: Exception) {
                if (current(ticket)) mutable.value = mutable.value.copy(notice = deletionNotice(failure, commit))
            } finally {
                if (active === currentCoroutineContext()[Job]) active = null
                if (current(ticket)) mutable.value = mutable.value.copy(busy = false)
            }
        }
        active = job
        job.start()
    }
}

private fun deletionNotice(failure: Exception, commit: Boolean): String = when ((failure as? StoryDeletionFailure)?.category) {
    "Stale" -> "The story changed. Close to refresh the library, then open a new deletion preview."
    "NotFound", "UnknownStory" -> "The story is unavailable. Close to refresh the library."
    "Busy" -> "Local storage is busy. Close to refresh the library before preparing a new deletion."
    "Full" -> "Local storage is full. Close to refresh the library before preparing a new deletion."
    else -> if (commit) "The deletion outcome could not be confirmed. It may already have completed. Close to refresh the library before trying again."
        else "Deletion preview could not be prepared. Close to refresh the library, then try a new preview."
}

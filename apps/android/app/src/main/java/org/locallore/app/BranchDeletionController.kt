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

data class BranchDeletionPreview(
    val version: Int,
    val storyId: String,
    val branchId: String,
    val title: String,
    val rootBranch: String,
    val expectedRevision: Long,
    val retainedDescendants: Map<String, Long>,
    val retainedHeads: Map<String, Long>,
    val removedBranches: List<String>,
    val removedRows: Map<String, Long>,
    val removedCommittedTurns: Long,
    val removedNoncommittedTurns: Long,
    val privacyWarning: String,
)
data class BranchDeletionPrepared(val token: Long, val preview: BranchDeletionPreview)
data class BranchDeleted(
    val storyId: String,
    val branchId: String,
    val retainedThroughRevision: Long?,
    val collectedBranches: Long,
    val deletedTurns: Long,
    val invalidatedBranches: List<String>,
)
data class BranchDeletionUiState(
    val visible: Boolean = false,
    val busy: Boolean = false,
    val closing: Boolean = false,
    val selected: SavedStory? = null,
    val prepared: BranchDeletionPrepared? = null,
    val deleted: BranchDeleted? = null,
    val notice: String? = null,
)
internal interface BranchDeletionGateway {
    suspend fun prepareBranch(story: SavedStory): BranchDeletionPrepared
    suspend fun commitBranch(token: Long): BranchDeleted
    fun cancel()
    fun close()
}
internal class BranchDeletionFailure(val category: String) : Exception("Timeline deletion failed")

/** Native code owns retention rules; this owner binds explicit consent to one captured preview. */
internal class BranchDeletionController(
    private val scope: CoroutineScope,
    private val gateway: BranchDeletionGateway,
    private val onClosed: (BranchDeleted?, Boolean) -> Unit,
) {
    private val mutable = MutableStateFlow(BranchDeletionUiState())
    val state = mutable.asStateFlow()
    private var generation = 0L
    private var active: Job? = null
    private var disposed = false
    private var commitAttempted = false

    fun open(story: SavedStory, rootBranch: String) {
        if (disposed || mutable.value.visible || active != null || rootBranch.isBlank() ||
            story.branch == rootBranch || story.revision < 0) return
        commitAttempted = false
        mutable.value = BranchDeletionUiState(visible = true, selected = story)
        work(commit = false) { ticket ->
            val prepared = gateway.prepareBranch(story)
            val preview = prepared.preview
            if (prepared.token <= 0 || preview.version != 1 || preview.storyId != story.story ||
                preview.branchId != story.branch || preview.rootBranch != rootBranch ||
                preview.expectedRevision != story.revision || preview.title != story.title ||
                preview.branchId == preview.rootBranch) {
                gateway.cancel()
                throw BranchDeletionFailure("InvalidPreview")
            }
            val captured = prepared.copy(preview = preview.copy(
                retainedDescendants = immutableMap(preview.retainedDescendants),
                retainedHeads = immutableMap(preview.retainedHeads),
                removedBranches = immutableList(preview.removedBranches),
                removedRows = immutableMap(preview.removedRows),
            ))
            if (current(ticket)) mutable.value = mutable.value.copy(prepared = captured,
                notice = "Review the native timeline preview. Nothing is deleted until you confirm.")
        }
    }

    fun confirm(expected: BranchDeletionPrepared) {
        val before = mutable.value
        if (disposed || !before.visible || before.busy || before.closing || before.deleted != null) return
        val prepared = before.prepared ?: return
        if (prepared !== expected) return
        mutable.value = before.copy(prepared = null)
        commitAttempted = true
        work(commit = true) { ticket ->
            val deleted = gateway.commitBranch(prepared.token)
            if (deleted.storyId != prepared.preview.storyId || deleted.branchId != prepared.preview.branchId) {
                throw BranchDeletionFailure("InvalidResponse")
            }
            if (current(ticket)) mutable.value = mutable.value.copy(
                deleted = deleted.copy(invalidatedBranches = immutableList(deleted.invalidatedBranches)),
                notice = "Timeline deletion completed. Close to refresh the retained saved history.",
            )
        }
    }

    fun cancel() = dismiss()
    fun dismiss() {
        if (disposed || !mutable.value.visible || mutable.value.closing) return
        val ticket = ++generation
        val previous = active
        val accepted = mutable.value.deleted
        val uncertain = commitAttempted && accepted == null
        mutable.value = mutable.value.copy(prepared = null, closing = true, busy = previous != null,
            notice = if (uncertain)
                "Deletion may already have completed. Waiting for local work before refreshing saved timelines."
            else "Waiting for local work before refreshing saved timelines.")
        gateway.cancel()
        previous?.cancel()
        scope.launch {
            previous?.join()
            if (disposed || generation != ticket) return@launch
            active = null
            gateway.cancel() // Also revoke a late noncooperative preview's capability.
            mutable.value = BranchDeletionUiState()
            onClosed(accepted, uncertain)
        }
    }

    fun dispose() {
        if (disposed) return
        disposed = true
        generation++
        gateway.cancel()
        active?.cancel()
        gateway.close()
        mutable.value = BranchDeletionUiState()
    }
    private fun current(ticket: Long) = !disposed && generation == ticket && mutable.value.visible && !mutable.value.closing
    private fun work(commit: Boolean, block: suspend (Long) -> Unit) {
        val ticket = ++generation
        mutable.value = mutable.value.copy(busy = true, notice = null)
        val job = scope.launch(start = CoroutineStart.LAZY) {
            try { block(ticket) }
            catch (cancelled: CancellationException) {
                if (current(ticket)) mutable.value = mutable.value.copy(notice = branchDeletionNotice(cancelled, commit))
                throw cancelled
            } catch (failure: Exception) {
                if (current(ticket)) mutable.value = mutable.value.copy(notice = branchDeletionNotice(failure, commit))
            } finally {
                if (active === currentCoroutineContext()[Job]) active = null
                if (current(ticket)) mutable.value = mutable.value.copy(busy = false)
            }
        }
        active = job
        job.start()
    }
}
private fun immutableMap(source: Map<String, Long>): Map<String, Long> =
    Collections.unmodifiableMap(LinkedHashMap(source))
private fun immutableList(source: List<String>): List<String> =
    Collections.unmodifiableList(ArrayList(source))
private fun branchDeletionNotice(failure: Exception, commit: Boolean): String = when ((failure as? BranchDeletionFailure)?.category) {
    "Stale" -> "The timeline changed. Close to refresh saved timelines, then open a new deletion preview."
    "NotFound", "UnknownStory" -> "The timeline is unavailable. Close to refresh saved timelines."
    "Busy" -> "Local storage is busy. Close to refresh saved timelines before preparing a new deletion."
    "Full" -> "Local storage is full. Close to refresh saved timelines before preparing a new deletion."
    else -> if (commit) "The deletion outcome could not be confirmed. It may already have completed. Close to refresh saved timelines."
        else "Timeline deletion preview could not be prepared. Close to refresh saved timelines, then try a new preview."
}

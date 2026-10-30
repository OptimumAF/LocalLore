/* Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0 */
package org.locallore.app

import java.util.Collections

/** Presentation identity only; unresolved saved scopes are represented by null. */
internal sealed interface TranscriptScope {
    data object Demo : TranscriptScope
    data class Saved(val story: String, val branch: String) : TranscriptScope
}

/** A frozen visible-history witness, never an alternate accepted-history authority. */
internal class TranscriptSnapshot(val scope: TranscriptScope, messages: List<SceneMessage>) {
    val messages: List<SceneMessage> = Collections.unmodifiableList(ArrayList(messages))

    override fun equals(other: Any?): Boolean =
        other is TranscriptSnapshot && scope == other.scope && messages == other.messages

    override fun hashCode(): Int = 31 * scope.hashCode() + messages.hashCode()
}

internal data class TranscriptFollowState(
    val snapshot: TranscriptSnapshot?,
    val unread: Boolean = false,
)

internal data class TranscriptReadPosition(val snapshot: TranscriptSnapshot, val atEnd: Boolean)
internal data class TranscriptScrollRequest(val snapshot: TranscriptSnapshot, val targetMessageId: Long)
internal data class TranscriptFollowUpdate(
    val state: TranscriptFollowState,
    val request: TranscriptScrollRequest? = null,
)

internal fun captureTranscript(scope: TranscriptScope?, messages: List<SceneMessage>): TranscriptSnapshot? =
    scope?.let { TranscriptSnapshot(it, messages) }

internal fun latestTranscriptRequest(current: TranscriptSnapshot?): TranscriptScrollRequest? =
    current?.messages?.lastOrNull()?.let { TranscriptScrollRequest(current, it.id) }

internal fun transcriptRequestMatches(request: TranscriptScrollRequest, current: TranscriptSnapshot?): Boolean =
    current != null && request.snapshot == current && current.messages.lastOrNull()?.id == request.targetMessageId

/** Only a read witness for the exact previous history can authorize append-follow. */
internal fun updateTranscriptFollow(
    previous: TranscriptFollowState?,
    current: TranscriptSnapshot?,
    readPosition: TranscriptReadPosition?,
): TranscriptFollowUpdate {
    val before = previous?.snapshot
    if (current == null || before == null || before.scope != current.scope) {
        return TranscriptFollowUpdate(TranscriptFollowState(current))
    }
    if (before == current) {
        val read = readPosition?.snapshot == current && readPosition.atEnd
        return TranscriptFollowUpdate(TranscriptFollowState(current, previous.unread && !read))
    }
    val appended = current.messages.size > before.messages.size &&
        current.messages.subList(0, before.messages.size) == before.messages
    if (!appended) return TranscriptFollowUpdate(TranscriptFollowState(current))

    val follow = readPosition?.snapshot == before && readPosition.atEnd
    // Scheduling navigation does not establish that the new reply was actually read.
    return TranscriptFollowUpdate(
        TranscriptFollowState(current, unread = true),
        if (follow) latestTranscriptRequest(current) else null,
    )
}

/** Measured list coordinates, supplied with a snapshot-bound tail by the Compose layer. */
internal data class TranscriptViewport(
    val firstVisibleItemIndex: Int,
    val totalItemsCount: Int,
    val viewportStartOffset: Int,
    val viewportEndOffset: Int,
    val tailOffset: Int? = null,
    val tailSize: Int? = null,
)

internal fun transcriptEndReached(tailIndex: Int, viewport: TranscriptViewport): Boolean {
    if (tailIndex < 0 || tailIndex >= viewport.totalItemsCount ||
        viewport.firstVisibleItemIndex < 0 || viewport.firstVisibleItemIndex >= viewport.totalItemsCount ||
        viewport.viewportEndOffset <= viewport.viewportStartOffset) return false
    if (viewport.firstVisibleItemIndex > tailIndex) return true
    val offset = viewport.tailOffset ?: return false
    val size = viewport.tailSize ?: return false
    if (size <= 0) return false
    return offset.toLong() + size.toLong() <= viewport.viewportEndOffset.toLong()
}

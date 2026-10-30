/* Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0 */
package org.locallore.app.ui

import androidx.compose.foundation.interaction.DragInteraction
import androidx.compose.foundation.lazy.LazyListLayoutInfo
import androidx.compose.foundation.lazy.LazyListState
import androidx.compose.foundation.lazy.rememberLazyListState
import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.getValue
import androidx.compose.runtime.key
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.rememberUpdatedState
import androidx.compose.runtime.setValue
import androidx.compose.runtime.snapshotFlow
import kotlinx.coroutines.flow.first
import kotlinx.coroutines.flow.collect
import org.locallore.app.TranscriptFollowState
import org.locallore.app.TranscriptReadPosition
import org.locallore.app.TranscriptScrollRequest
import org.locallore.app.TranscriptSnapshot
import org.locallore.app.TranscriptViewport
import org.locallore.app.latestTranscriptRequest
import org.locallore.app.transcriptEndReached
import org.locallore.app.transcriptRequestMatches
import org.locallore.app.updateTranscriptFollow

// LocalLoreScreen emits brand, scene and state before an active transcript.
// With no messages, the state row is the read anchor for a subsequent first append.
private const val TranscriptPrefixItems = 3

private data class NavigationRequest(
    val request: TranscriptScrollRequest,
    val gesture: Long,
    val automatic: Boolean,
)

internal class TranscriptNavigation(
    val listState: LazyListState,
    val showLatest: Boolean,
    val latest: () -> Unit,
)

private fun LazyListLayoutInfo.matches(snapshot: TranscriptSnapshot, followingItems: Int): Boolean {
    if (totalItemsCount != TranscriptPrefixItems + snapshot.messages.size + followingItems ||
        visibleItemsInfo.isEmpty()) return false
    return visibleItemsInfo.all { item ->
        val index = item.index - TranscriptPrefixItems
        index !in snapshot.messages.indices || item.key == "message-${snapshot.messages[index].id}"
    }
}

private fun LazyListState.readPosition(snapshot: TranscriptSnapshot): TranscriptReadPosition {
    val tailIndex = TranscriptPrefixItems + snapshot.messages.lastIndex
    val layout = layoutInfo
    val tail = layout.visibleItemsInfo.firstOrNull { it.index == tailIndex }
    return TranscriptReadPosition(snapshot, transcriptEndReached(tailIndex, TranscriptViewport(
        firstVisibleItemIndex, layout.totalItemsCount, layout.viewportStartOffset,
        layout.viewportEndOffset, tail?.offset, tail?.size,
    )))
}

@Composable
internal fun rememberTranscriptNavigation(
    snapshot: TranscriptSnapshot?,
    followingItems: Int,
): TranscriptNavigation {
    val scope = snapshot?.scope
    val listState = key(scope) { rememberLazyListState() }
    val currentSnapshot by rememberUpdatedState(snapshot)
    val currentFollowingItems by rememberUpdatedState(followingItems)
    var unread by remember(scope) { mutableStateOf(false) }
    var readPosition by remember(scope) { mutableStateOf<TranscriptReadPosition?>(null) }
    var gesture by remember(scope) { mutableStateOf(0L) }
    var pending by remember(scope) { mutableStateOf<NavigationRequest?>(null) }

    LaunchedEffect(listState) {
        listState.interactionSource.interactions.collect { interaction ->
            if (interaction is DragInteraction.Start) {
                gesture += 1
                readPosition = null
                pending = null
            }
        }
    }
    LaunchedEffect(listState) {
        var previous: TranscriptFollowState? = null
        var lastLayout: LazyListLayoutInfo? = null
        var layoutBeforeHistory: LazyListLayoutInfo? = null
        snapshotFlow { Triple(currentSnapshot, listState.layoutInfo, listState.isScrollInProgress) }
            .collect { (current, layout, scrolling) ->
                // Decide with the OLD witness before measuring or acknowledging the new tail.
                if (previous?.snapshot != current) {
                    val update = updateTranscriptFollow(previous, current, readPosition)
                    previous = update.state
                    unread = update.state.unread
                    pending = update.request?.takeUnless { scrolling }
                        ?.let { NavigationRequest(it, gesture, automatic = true) }
                    readPosition = null
                    layoutBeforeHistory = lastLayout
                }
                // A remeasure must follow a history change. Same IDs alone cannot bind an
                // old row height to rewritten text, and an empty first layout is not a read.
                if (current != null && layout !== layoutBeforeHistory &&
                    layout.matches(current, currentFollowingItems)) {
                    readPosition = listState.readPosition(current)
                    val update = updateTranscriptFollow(previous, current, readPosition)
                    previous = update.state
                    unread = update.state.unread
                }
                lastLayout = layout
            }
    }
    LaunchedEffect(pending, snapshot, gesture) {
        val navigation = pending ?: return@LaunchedEffect
        val request = navigation.request
        fun current(): Boolean = navigation.gesture == gesture &&
            transcriptRequestMatches(request, currentSnapshot)
        if (!current()) return@LaunchedEffect
        snapshotFlow { listState.layoutInfo }.first {
            !current() || it.matches(request.snapshot, currentFollowingItems)
        }
        if (!current() || (navigation.automatic && listState.isScrollInProgress)) return@LaunchedEffect
        listState.scrollToItem(TranscriptPrefixItems + request.snapshot.messages.lastIndex)
        // Scrolling is not a read acknowledgement: only measured current-tail geometry
        // can clear unread. A long new message may still extend below the viewport.
        if (pending == navigation) pending = null
    }

    val captured = snapshot
    val showLatest = snapshot != null && snapshot.messages.isNotEmpty() &&
        (unread || (readPosition?.snapshot == snapshot && readPosition?.atEnd == false))
    return TranscriptNavigation(listState, showLatest) {
        val request = latestTranscriptRequest(captured)
        if (request != null && transcriptRequestMatches(request, currentSnapshot)) {
            pending = NavigationRequest(request, gesture, automatic = false)
        }
    }
}

/* Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0 */
package org.locallore.app

/** Native play_snapshot is the fixed player lens; the UI never supplies an actor observer. */
internal data class PlayerSnapshotBinding(val session: String,val scope: PlayDraftScope,val observer: String)
private val playerBindingId=Regex("[A-Za-z0-9_-]{1,64}")
internal fun bindPlayerSnapshot(session: String,scope: PlayDraftScope,rawObserver: Any?,previous: PlayerSnapshotBinding?): PlayerSnapshotBinding {
    val observer=rawObserver as? String ?: throw WorkspaceFailure("Malformed")
    if(!playerBindingId.matches(observer) || !playerBindingId.matches(scope.story) || !playerBindingId.matches(scope.branch) ||
        localUtf8(session).size !in 1..128)throw WorkspaceFailure("Malformed")
    val next=PlayerSnapshotBinding(session,scope,observer)
    if(previous!=null && previous!=next)throw WorkspaceFailure("Stale")
    return next
}

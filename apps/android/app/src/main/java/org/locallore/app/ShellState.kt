/* Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0 */
package org.locallore.app

enum class DemoAction { GIVE_POTION, TRY_ABILITY }
enum class DemoMode { ACCEPTED, MALFORMED, REJECTED, DELAYED, FAILED }
data class SceneMessage(val id: Long, val text: String, val isPlayer: Boolean)
data class ShellState(
    val busy: Boolean = false,
    val revision: Long = 0,
    val potionOwner: String = "You",
    val messages: List<SceneMessage> = emptyList(),
    val notice: String? = null,
    val mode: DemoMode = DemoMode.ACCEPTED,
    val recoveryRequired: Boolean = false,
)

sealed interface DemoResult {
    data class Prepared(val session: Long, val operation: Long) : DemoResult
    data class Accepted(val revision: Long, val potionOwner: String, val narration: String) : DemoResult
    data class Rejected(val category: String) : DemoResult
}

/** Preparation may suspend. Commit and publication share one non-suspending owner-thread step. */
fun interface DemoGateway {
    suspend fun respond(action: DemoAction, revision: Long, mode: DemoMode): DemoResult
    fun commit(result: DemoResult): DemoResult = result
    fun cancel() {}
    fun reset() {}
    fun close() {}
}

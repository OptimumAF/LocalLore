/* Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0 */
package org.locallore.app

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import kotlinx.coroutines.CancellationException
import kotlinx.coroutines.Job
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.launch

class ShellViewModel(private val gateway: DemoGateway) : ViewModel() {
    private val mutable = MutableStateFlow(ShellState())
    val state: StateFlow<ShellState> = mutable.asStateFlow()
    private var generation = 0L
    private var messageId = 0L
    private var pending: Job? = null

    fun setMode(mode: DemoMode) {
        if (!mutable.value.busy && !mutable.value.recoveryRequired) mutable.value = mutable.value.copy(mode = mode, notice = null)
    }

    fun submit(action: DemoAction) {
        if (mutable.value.busy || mutable.value.recoveryRequired) return
        val before = mutable.value
        val ticket = ++generation
        mutable.value = before.copy(busy = true, notice = null)
        pending = viewModelScope.launch {
            var committing = false
            try {
                val prepared = gateway.respond(action, before.revision, before.mode)
                // A cancelled/reset/obsolete session never attaches a late completion.
                if (ticket != generation || mutable.value.revision != before.revision) return@launch
                committing = true
                val result = gateway.commit(prepared)
                mutable.value = when (result) {
                    is DemoResult.Accepted -> before.copy(
                        revision = result.revision,
                        potionOwner = result.potionOwner,
                        messages = (before.messages + listOf(
                            SceneMessage(++messageId, action.description(), true),
                            SceneMessage(++messageId, result.narration, false),
                        )).takeLast(40),
                        notice = "Outcome accepted by the local engine.",
                    )
                    is DemoResult.Rejected -> before.copy(notice = rejectionNotice(result.category))
                    is DemoResult.Prepared -> error("Commit returned an unfinished operation")
                }
            } catch (cancelled: CancellationException) {
                throw cancelled
            } catch (_: Exception) {
                if (ticket == generation) mutable.value = if (committing) before.copy(
                    recoveryRequired = true,
                    notice = "Unable to confirm the outcome. Reset this in-memory demo to continue.",
                ) else before.copy(notice = "Response failed. Nothing changed; try again.")
            } finally {
                if (ticket == generation) mutable.value = mutable.value.copy(busy = false)
            }
        }
    }

    fun cancel() {
        if (!mutable.value.busy) return
        generation++
        gateway.cancel()
        pending?.cancel()
        pending = null
        mutable.value = mutable.value.copy(busy = false, notice = "Response cancelled. Nothing changed.")
    }

    fun reset() {
        generation++
        gateway.cancel()
        pending?.cancel()
        pending = null
        gateway.reset()
        mutable.value = ShellState()
    }

    override fun onCleared() {
        generation++
        gateway.close()
        pending?.cancel()
        pending = null
        mutable.value = mutable.value.copy(busy = false)
        super.onCleared()
    }
}

private fun DemoAction.description(): String = when (this) {
    DemoAction.GIVE_POTION -> "Give my potion to Mira."
    DemoAction.TRY_ABILITY -> "Try the unlearned blink ability."
}

private fun rejectionNotice(category: String): String = when (category) {
    "Inventory" -> "You no longer hold the potion. Nothing changed."
    "Ability" -> "Blink is not learned. Nothing changed."
    "Agency" -> "The proposal did not match your action. Nothing changed."
    "Malformed" -> "The response was malformed. Nothing changed; try again."
    "Provider" -> "The response failed. Nothing changed; try again."
    else -> "This response was rejected. Nothing changed; try again."
}

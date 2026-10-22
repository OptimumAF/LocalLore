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
        if (!mutable.value.busy) mutable.value = mutable.value.copy(mode = mode, notice = null)
    }

    fun submit(action: DemoAction) {
        if (mutable.value.busy) return
        val before = mutable.value
        val ticket = ++generation
        mutable.value = before.copy(busy = true, notice = null)
        pending = viewModelScope.launch {
            try {
                val result = gateway.respond(action, before.revision, before.mode)
                // A cancelled/reset/obsolete session never attaches a late completion.
                if (ticket != generation || mutable.value.revision != before.revision) return@launch
                mutable.value = when (result) {
                    is DemoResult.Accepted -> before.copy(
                        revision = result.revision,
                        potionOwner = result.potionOwner,
                        messages = (before.messages + listOf(
                            SceneMessage(++messageId, action.description(), true),
                            SceneMessage(++messageId, result.narration, false),
                        )).takeLast(40),
                        notice = "Sample outcome accepted.",
                    )
                    is DemoResult.Rejected -> before.copy(notice = rejectionNotice(result.category))
                }
            } catch (cancelled: CancellationException) {
                throw cancelled
            } catch (_: Exception) {
                if (ticket == generation) mutable.value = before.copy(notice = "Sample response failed. Nothing changed; try again.")
            } finally {
                if (ticket == generation) mutable.value = mutable.value.copy(busy = false)
            }
        }
    }

    fun cancel() {
        if (!mutable.value.busy) return
        generation++
        pending?.cancel()
        pending = null
        mutable.value = mutable.value.copy(busy = false, notice = "Response cancelled. Nothing changed.")
    }

    fun reset() {
        generation++
        pending?.cancel()
        pending = null
        mutable.value = ShellState()
    }

    override fun onCleared() {
        generation++
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
    "Agency" -> "The sample proposal did not match your action. Nothing changed."
    "Malformed" -> "The sample response was malformed. Nothing changed; try again."
    else -> "This sample response was rejected. Nothing changed; try again."
}

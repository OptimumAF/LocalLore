/* Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0 */
package org.locallore.app

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import java.io.InputStream
import kotlinx.coroutines.CancellationException
import kotlinx.coroutines.CoroutineDispatcher
import kotlinx.coroutines.CoroutineStart
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.Job
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.launch
import kotlinx.coroutines.withContext

internal enum class LocalModelSetupPhase { UNCHECKED, CHECKING, MISSING, PICKING, IMPORTING, STOPPING, READY, FAILED, OPENING, SESSION_HELD }

internal data class LocalModelSetupState(
    val phase: LocalModelSetupPhase = LocalModelSetupPhase.UNCHECKED,
    val notice: String = "Check the app's local model copy before continuing.",
) {
    val busy: Boolean get() = phase in setOf(LocalModelSetupPhase.CHECKING,
        LocalModelSetupPhase.IMPORTING, LocalModelSetupPhase.STOPPING)
    val ready: Boolean get() = phase == LocalModelSetupPhase.READY
    val canChoose: Boolean get() = phase in setOf(LocalModelSetupPhase.UNCHECKED,
        LocalModelSetupPhase.MISSING, LocalModelSetupPhase.FAILED)
}

/** File-operation admission only. It never creates an inference runtime or changes story state.
 * All entry points are called on Main. Cancellation invalidates results immediately, while the
 * operation remains reserved until its actual terminal return, including a blocking provider read.
 */
internal class LocalModelSetupViewModel(
    private val checkInstalled: suspend () -> Boolean,
    private val install: suspend (() -> InputStream) -> Unit,
    private val io: CoroutineDispatcher = Dispatchers.IO,
    private val canStart: () -> Boolean = { true },
) : ViewModel() {
    private val mutable = MutableStateFlow(LocalModelSetupState())
    val state = mutable.asStateFlow()
    private var pending: Job? = null
    private var generation = 0L
    private var foreground = false
    private var disposed = false
    private var refreshAfterDrain = false

    fun onForeground() {
        if (disposed) return
        foreground = true
        if (pending == null && holdIfClaimed()) return
        if (mutable.value.phase in setOf(LocalModelSetupPhase.PICKING, LocalModelSetupPhase.OPENING)) return
        if (pending != null) {
            if (mutable.value.phase == LocalModelSetupPhase.STOPPING) refreshAfterDrain = true
        } else recheck()
    }

    fun onBackground() {
        foreground = false
        refreshAfterDrain = false
        // A document picker is a separate foreground surface; keep only its pending selection.
        if (pending != null) cancel()
        else if (mutable.value.phase == LocalModelSetupPhase.READY) {
            mutable.value = LocalModelSetupState()
        }
    }

    fun recheck(): Boolean {
        if (!available() || mutable.value.phase in setOf(LocalModelSetupPhase.PICKING, LocalModelSetupPhase.OPENING)) return false
        if (holdIfClaimed()) return false
        return runOperation(LocalModelSetupPhase.CHECKING, "Checking the app's local model copy…", checkInstalled)
    }

    fun beginPicker(): Boolean {
        if (!available() || !mutable.value.canChoose) return false
        if (holdIfClaimed()) return false
        generation++
        mutable.value = LocalModelSetupState(LocalModelSetupPhase.PICKING, "Choose the model file already stored on this device.")
        return true
    }

    fun completePicker(open: (() -> InputStream)?) {
        if (disposed || pending != null || mutable.value.phase != LocalModelSetupPhase.PICKING) return
        if (holdIfClaimed()) return
        if (open == null) {
            mutable.value = LocalModelSetupState(LocalModelSetupPhase.UNCHECKED, "No file selected. Check the local copy or choose a file.")
            return
        }
        // Activity results may arrive before onStart. Only the explicit selected stream is retained
        // by this job; no persisted URI permission or provider metadata becomes trusted config.
        runOperation(LocalModelSetupPhase.IMPORTING, "Copying and verifying the selected file…") {
            install(open)
            true
        }
    }

    fun pickerFailed() {
        if (!disposed && mutable.value.phase == LocalModelSetupPhase.PICKING) {
            mutable.value = LocalModelSetupState(LocalModelSetupPhase.FAILED, "The file picker could not open. Try choosing a local file again.")
        }
    }

    fun cancel() {
        val current = pending ?: return
        generation++
        refreshAfterDrain = false
        mutable.value = LocalModelSetupState(LocalModelSetupPhase.STOPPING, "Stopping. Wait for the current file operation to finish.")
        current.cancel()
    }

    fun beginPlay(): Boolean {
        if (!available() || !mutable.value.ready) return false
        if (holdIfClaimed()) return false
        generation++
        mutable.value = LocalModelSetupState(LocalModelSetupPhase.OPENING, "Opening the local story library…")
        return true
    }

    fun playLaunchFailed() {
        if (!disposed && mutable.value.phase == LocalModelSetupPhase.OPENING) {
            mutable.value = LocalModelSetupState(LocalModelSetupPhase.FAILED, "The local story screen could not open. Check the model copy and try again.")
        }
    }

    internal fun dispose() {
        if (disposed) return
        disposed = true
        foreground = false
        generation++
        pending?.cancel()
    }

    override fun onCleared() { dispose() }

    private fun available() = !disposed && foreground && pending == null

    private fun holdIfClaimed(): Boolean {
        if (canStart()) return false
        mutable.value = LocalModelSetupState(LocalModelSetupPhase.SESSION_HELD,
            "Close the app completely before starting another local session.")
        return true
    }

    private fun runOperation(phase: LocalModelSetupPhase, notice: String, operation: suspend () -> Boolean): Boolean {
        if (disposed || pending != null) return false
        val token = ++generation
        mutable.value = LocalModelSetupState(phase, notice)
        val job = viewModelScope.launch(start = CoroutineStart.LAZY) {
            try {
                val present = withContext(io) { operation() }
                if (!disposed && token == generation) {
                    mutable.value = if (present) LocalModelSetupState(LocalModelSetupPhase.READY,
                        "The local copy matches the built-in size and SHA-256. Ready for local play.")
                    else LocalModelSetupState(LocalModelSetupPhase.MISSING, "Choose the verified local model file to continue.")
                }
            } catch (_: CancellationException) {
                // Publication may already have won. A later full check discovers it; never claim rollback.
                if (!disposed && token == generation) generation++
            } catch (_: Exception) {
                if (!disposed && token == generation) {
                    mutable.value = LocalModelSetupState(LocalModelSetupPhase.FAILED,
                        "The local file could not be verified. Existing stories are unchanged. Check free space and choose the expected file.")
                }
            } finally {
                finishOperation(token)
            }
        }
        pending = job
        // Also release a lazy child cancelled before its body ever starts. Completion callbacks for
        // this Main-owned job run after its body (or synchronously for pre-start Main cancellation).
        job.invokeOnCompletion { if (pending === job) finishOperation(token) }
        job.start()
        return true
    }

    private fun finishOperation(token: Long) {
        pending = null
        if (disposed) return
        if (mutable.value.phase == LocalModelSetupPhase.STOPPING || token != generation) {
            mutable.value = LocalModelSetupState(LocalModelSetupPhase.UNCHECKED,
                "File operation stopped. Check the local copy before continuing; a verified copy may already have been saved.")
        }
        if (foreground && refreshAfterDrain) {
            refreshAfterDrain = false
            recheck()
        }
    }
}

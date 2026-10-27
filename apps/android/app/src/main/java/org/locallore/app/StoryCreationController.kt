/* Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0 */
package org.locallore.app

import java.util.Collections
import java.util.UUID
import kotlinx.coroutines.CancellationException
import kotlinx.coroutines.CoroutineScope
import kotlinx.coroutines.CoroutineStart
import kotlinx.coroutines.Job
import kotlinx.coroutines.currentCoroutineContext
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.launch

internal data class StoryCreationUiState(
    val visible: Boolean = false,
    val busy: Boolean = false,
    val creating: Boolean = false,
    val closing: Boolean = false,
    val review: StoryCreationRequest? = null,
    val notice: String? = null,
)

/** Consent belongs to one displayed immutable review, never a replacement or automatic retry. */
internal class StoryCreationController(
    private val gateway: StoryCreationGateway,
    private val scope: CoroutineScope,
    private val onClosed: (StoryCreationClose) -> Unit,
) {
    private val mutable = MutableStateFlow(StoryCreationUiState())
    val state = mutable.asStateFlow()
    private var generation = 0L
    private var active: Job? = null
    private var disposed = false
    private var createStarted = false

    fun open() {
        if (disposed || mutable.value.visible || active != null) return
        val ticket = ++generation
        val creationId = UUID.randomUUID().toString().replace("-", "")
        createStarted = false
        mutable.value = StoryCreationUiState(visible = true, busy = true)
        launch(ticket) {
            val preview = try {
                val source = gateway.preview()
                // New identity even if a port reuses a DTO. Strings are immutable; the list is not.
                source.copy(details = Collections.unmodifiableList(ArrayList(source.details)))
            } catch (cancelled: CancellationException) {
                if (current(ticket)) mutable.value = mutable.value.copy(
                    notice = "Starter review stopped. No story was created.")
                throw cancelled
            } catch (_: Exception) {
                if (current(ticket)) mutable.value = mutable.value.copy(
                    notice = "Starter review is unavailable. No story was created. Close and try again.")
                return@launch
            }
            if (current(ticket)) mutable.value = mutable.value.copy(
                review = StoryCreationRequest(preview, preview.defaultTitle, creationId),
                notice = "Review this starter and title. Nothing is created until you choose Create.",
            )
        }
    }

    fun editTitle(expected: StoryCreationRequest, text: String) {
        val before = mutable.value
        val review = before.review ?: return
        if (disposed || !before.visible || before.busy || before.creating || before.closing || createStarted ||
            expected.preview !== review.preview || expected.creationId != review.creationId) return
        // A field intent replaces only title on the latest request, including edits before a frame.
        mutable.value = before.copy(review = review.copy(title = text), notice = null)
    }

    fun confirm(expected: StoryCreationRequest) {
        val before = mutable.value
        if (disposed || !before.visible || before.busy || before.creating || before.closing || createStarted ||
            before.review !== expected) return
        if (!validStoryTitle(expected.title)) {
            mutable.value = before.copy(notice = "Use a title of up to 80 characters without outer spaces, line breaks or control characters.")
            return
        }
        // Consume synchronously, before the coroutine or native boundary can yield.
        createStarted = true
        val ticket = ++generation
        mutable.value = before.copy(review = null, busy = true, creating = true,
            notice = "Creating the story. If stopped, it may already exist; close to refresh the library.")
        launch(ticket) {
            val saved = try { gateway.create(expected) }
            catch (cancelled: CancellationException) {
                if (current(ticket)) mutable.value = mutable.value.copy(
                    notice = "Creation was stopped. A story may already exist. Close to refresh the library.")
                throw cancelled
            } catch (_: Exception) {
                if (current(ticket)) mutable.value = mutable.value.copy(
                    notice = "Creation could not be confirmed. A story may already exist. Close to refresh the library.")
                return@launch
            }
            if (current(ticket)) finish(StoryCreationClose(saved = saved))
        }
    }

    fun dismiss() {
        val before = mutable.value
        if (disposed || !before.visible || before.closing) return
        val ticket = ++generation
        val previous = active
        val refresh = createStarted
        mutable.value = before.copy(review = null, closing = true, busy = previous != null,
            notice = if (refresh) "Finishing local work. A story may already exist; the library will refresh."
                else "Closing starter review…")
        val closing = scope.launch(start = CoroutineStart.LAZY) {
            previous?.join()
            if (!disposed && generation == ticket && mutable.value.visible && mutable.value.closing)
                finish(StoryCreationClose(refreshRequired = refresh))
        }
        active = closing
        previous?.cancel()
        closing.start()
    }

    fun dispose() {
        if (disposed) return
        disposed = true
        generation++
        active?.cancel()
        active = null
        mutable.value = StoryCreationUiState()
        // The parent owns transport retirement and recovery on its next coherent library read.
    }

    private fun current(ticket: Long) = !disposed && generation == ticket && mutable.value.visible && !mutable.value.closing
    private fun launch(ticket: Long, block: suspend () -> Unit) {
        val job = scope.launch(start = CoroutineStart.LAZY) {
            try { block() }
            finally {
                if (active === currentCoroutineContext()[Job]) active = null
                if (current(ticket)) mutable.value = mutable.value.copy(busy = false, creating = false)
            }
        }
        active = job
        job.start()
    }
    private fun finish(result: StoryCreationClose) {
        generation++
        active = null
        createStarted = false
        mutable.value = StoryCreationUiState()
        onClosed(result)
    }
}

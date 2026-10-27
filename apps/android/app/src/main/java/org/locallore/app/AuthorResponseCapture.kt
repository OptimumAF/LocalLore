/* Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0 */
package org.locallore.app

internal enum class AuthorResponseCaptureState { EMPTY, RECORDED, DUPLICATE, INVALID }

/** Private submitted-proposal observation only; never native validation, delivery or canon proof. */
internal class AuthorResponseCapture {
    private var state = AuthorResponseCaptureState.EMPTY
    private var calls = 0
    private var first: ByteArray? = null

    @Synchronized internal fun observe(role: String, response: ByteArray) {
        if (role != "author") return
        if (calls != 0) {
            calls = 2
            state = AuthorResponseCaptureState.DUPLICATE
            return
        }
        calls = 1
        // Any failed observation remains explicitly invalid, including a failed bounded copy.
        state = AuthorResponseCaptureState.INVALID
        if (response.size !in 1..MAX_BYTES) return
        try { localText(response, MAX_BYTES) } catch (_: Exception) { return }
        first = response.copyOf()
        state = AuthorResponseCaptureState.RECORDED
    }

    @Synchronized fun snapshot(): AuthorResponseSnapshot = AuthorResponseSnapshot(state, calls, first)

    companion object { const val MAX_BYTES = 8192 }
}

/** No data-class/toString byte rendering; each caller receives its own bounded copy. */
internal class AuthorResponseSnapshot internal constructor(
    val state: AuthorResponseCaptureState,
    val calls: Int,
    response: ByteArray?,
) {
    private val first = response?.copyOf()
    init {
        require(calls in 0..2 && (first == null || first.size in 1..AuthorResponseCapture.MAX_BYTES))
        require(when (state) {
            AuthorResponseCaptureState.EMPTY -> calls == 0 && first == null
            AuthorResponseCaptureState.RECORDED -> calls == 1 && first != null
            AuthorResponseCaptureState.DUPLICATE -> calls == 2
            AuthorResponseCaptureState.INVALID -> calls == 1 && first == null
        })
    }
    fun responseBytes(): ByteArray? = first?.copyOf()
}

/* Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0 */
package org.locallore.app

/** Closed diagnostic for the fixed-name native operation; contains no path or errno. */
internal enum class ModelPublicationResult {
    PUBLISHED, DESTINATION_EXISTS, UNSUPPORTED, IO_FAILURE, INVALID_INPUT, UNKNOWN;

    /** Observation does not authorize a retry, cleanup, fallback, or successful import. */
    fun requirePublished(onResult: (ModelPublicationResult) -> Unit = {}) {
        onResult(this)
        when (this) {
            PUBLISHED -> Unit
            DESTINATION_EXISTS, INVALID_INPUT -> throw LocalModelException(LocalModelFailure.UNSAFE_PATH)
            UNSUPPORTED, IO_FAILURE, UNKNOWN -> throw LocalModelException(LocalModelFailure.STORAGE)
        }
    }

    companion object {
        fun fromWire(result: Int): ModelPublicationResult = when (result) {
            0 -> PUBLISHED
            1 -> DESTINATION_EXISTS
            2 -> UNSUPPORTED
            3 -> IO_FAILURE
            4 -> INVALID_INPUT
            else -> UNKNOWN
        }
    }
}

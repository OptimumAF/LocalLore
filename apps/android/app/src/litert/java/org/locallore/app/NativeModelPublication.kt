/* Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0 */
package org.locallore.app

import java.io.File

/** Fixed names only; no model text, provider metadata or arbitrary destination crosses JNI. */
internal object NativeModelPublication {
    init { System.loadLibrary("locallore_android") }

    fun publish(root: File) {
        when (publishNoReplace(root.path.toByteArray(Charsets.UTF_8))) {
            0 -> Unit
            1, 4 -> throw LocalModelException(LocalModelFailure.UNSAFE_PATH)
            else -> throw LocalModelException(LocalModelFailure.STORAGE)
        }
    }

    private external fun publishNoReplace(root: ByteArray): Int
}

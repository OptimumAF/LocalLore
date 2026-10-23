/* Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0 */
package org.locallore.app

enum class PlayInputKind(val wire: String, val label: String) {
    ACTION("action", "Action"), DIALOGUE("dialogue", "Dialogue"),
}
data class PlayInput(val kind: PlayInputKind, val text: String)
enum class TextProvider(val label: String) {
    UNAVAILABLE("No local text provider"),
    SCRIPTED("Scripted fixture · no language model"),
    LOCAL("Local provider configured"),
}
internal const val MAX_PLAY_INPUT_BYTES = 2048
internal fun validPlayInput(input: PlayInput) = input.text.isNotBlank() &&
    validUnicode(input.text) &&
    input.text.toByteArray(Charsets.UTF_8).size <= MAX_PLAY_INPUT_BYTES &&
    input.text.none { it.isISOControl() && it != '\n' && it != '\t' }

private fun validUnicode(text: String): Boolean {
    var i = 0
    while (i < text.length) {
        val c = text[i++]
        if (c.isHighSurrogate()) {
            if (i == text.length || !text[i++].isLowSurrogate()) return false
        } else if (c.isLowSurrogate()) return false
    }
    return true
}

/* Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0 */
package org.locallore.app

/** UI identity only; an accepted revision is deliberately not part of a draft's scope. */
internal data class PlayDraftScope(val story: String, val branch: String)

/** Unsent editor contents. Restoring or resolving this value never submits a turn. */
internal data class PlayDraft(
    val scope: PlayDraftScope? = null,
    val input: PlayInput = PlayInput(PlayInputKind.ACTION, ""),
    val textNotRestored: Boolean = false,
) {
    fun resolve(scope: PlayDraftScope?, pending: Boolean): PlayDraft = when {
        pending -> this
        this.scope == scope -> this
        else -> PlayDraft(scope = scope)
    }

    fun edit(
        expectedScope: PlayDraftScope?,
        currentScope: PlayDraftScope?,
        input: PlayInput,
    ): PlayDraft = if (expectedScope == currentScope && currentScope == scope) {
        copy(input = input, textNotRestored = false)
    } else {
        this
    }
}

internal const val MAX_SAVED_PLAY_DRAFT_BYTES = 8192
private const val MAX_DRAFT_SCOPE_BYTES = 128

private fun validDraftUnicode(text: String): Boolean {
    var index = 0
    while (index < text.length) {
        val character = text[index++]
        if (character.isHighSurrogate()) {
            if (index == text.length || !text[index++].isLowSurrogate()) return false
        } else if (character.isLowSurrogate()) {
            return false
        }
    }
    return true
}

private fun validDraftScopePart(value: String): Boolean = value.isNotEmpty() &&
    value.length <= MAX_DRAFT_SCOPE_BYTES && validDraftUnicode(value) &&
    value.none { it.isISOControl() } &&
    value.toByteArray(Charsets.UTF_8).size <= MAX_DRAFT_SCOPE_BYTES

private fun restorableDraftText(text: String): Boolean =
    text.length <= MAX_SAVED_PLAY_DRAFT_BYTES && validDraftUnicode(text) &&
        text.toByteArray(Charsets.UTF_8).size <= MAX_SAVED_PLAY_DRAFT_BYTES

/**
 * Saves only scoped, bounded UI data. Invalid/oversized live text is never
 * truncated or repaired; the saved marker tells the restored editor it was
 * omitted. A prior omission remains visible until an explicit edit clears it.
 * Blank/control-bearing editor contents may be saved; Send validation is separate.
 */
internal fun savePlayDraft(draft: PlayDraft): List<Any>? {
    val scope = draft.scope ?: return null
    if (!validDraftScopePart(scope.story) || !validDraftScopePart(scope.branch)) return null
    val full = !draft.textNotRestored && restorableDraftText(draft.input.text)
    return listOf(
        1, scope.story, scope.branch, draft.input.kind.wire,
        if (full) draft.input.text else "", if (full) "full" else "omitted",
    )
}

/** Exact v1 wire: [Int(1), story, branch, kind.wire, text, full|omitted]. */
internal fun restorePlayDraft(value: Any?): PlayDraft? {
    val fields = value as? List<*> ?: return null
    if (fields.size != 6 || fields[0] !is Int || fields[0] != 1) return null
    val story = fields[1] as? String ?: return null
    val branch = fields[2] as? String ?: return null
    val kindWire = fields[3] as? String ?: return null
    val text = fields[4] as? String ?: return null
    val mode = fields[5] as? String ?: return null
    if (!validDraftScopePart(story) || !validDraftScopePart(branch)) return null
    val kind = PlayInputKind.entries.firstOrNull { it.wire == kindWire } ?: return null
    val omitted = when (mode) {
        "full" -> {
            if (!restorableDraftText(text)) return null
            false
        }
        "omitted" -> {
            if (text.isNotEmpty()) return null
            true
        }
        else -> return null
    }
    return PlayDraft(PlayDraftScope(story, branch), PlayInput(kind, text), omitted)
}

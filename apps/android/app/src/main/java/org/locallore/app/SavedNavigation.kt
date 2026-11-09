/* Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0 */
package org.locallore.app

// UI navigation intent only. Native catalogs and resume still determine available state.
private val NavigationId = Regex("[A-Za-z0-9_-]{1,64}")

internal fun encodeNavigationHint(scope: PlayDraftScope?): List<Any>? {
    if (scope == null || !NavigationId.matches(scope.story) || !NavigationId.matches(scope.branch)) return null
    return listOf(1, scope.story, scope.branch)
}

internal fun decodeNavigationHint(value: Any?): PlayDraftScope? {
    val fields = value as? List<*> ?: return null
    if (fields.size != 3 || fields[0] !is Int || fields[0] != 1) return null
    val story = fields[1] as? String ?: return null
    val branch = fields[2] as? String ?: return null
    return PlayDraftScope(story, branch).takeIf { encodeNavigationHint(it) != null }
}

internal const val STORED_NAVIGATION_LIMIT = 132

internal fun encodeStoredNavigationHint(scope: PlayDraftScope): ByteArray? =
    encodeNavigationHint(scope)?.joinToString(separator = "\n", postfix = "\n")?.toByteArray(Charsets.US_ASCII)

internal fun decodeStoredNavigationHint(bytes: ByteArray): PlayDraftScope? {
    if (bytes.size !in 1..STORED_NAVIGATION_LIMIT) return null
    val fields = bytes.toString(Charsets.US_ASCII).split('\n')
    if (fields.size != 4 || fields[0] != "1" || fields[3].isNotEmpty()) return null
    return decodeNavigationHint(listOf(1, fields[1], fields[2]))
}

/** An unresolved startup must not erase the restored hint before native validation. */
internal fun navigationHintToSave(previous: PlayDraftScope?, state: ShellState): PlayDraftScope? {
    if (!state.persistent) return null
    val selected = state.selectedStory
    val candidate = if (selected != null) PlayDraftScope(selected.story, selected.branch)
        else if (state.busy || state.recoveryRequired) previous else null
    return candidate?.takeIf { encodeNavigationHint(it) != null }
}

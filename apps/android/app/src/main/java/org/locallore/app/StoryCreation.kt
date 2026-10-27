/* Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0 */
package org.locallore.app

internal const val DEFAULT_STORY_TEMPLATE = "lantern-quay-v1"
internal data class StoryTemplateOption(val template: String, val defaultTitle: String,
    val description: String, val profile: String)
internal fun StoryCreationPreview.option() = StoryTemplateOption(template, defaultTitle, description, profile)
internal fun validStoryTemplateProfile(template: String, profile: String) = when (template) {
    DEFAULT_STORY_TEMPLATE -> profile == "fantasy_v1"
    "bracken-harbor-v1" -> profile == "narrative_v1"
    else -> false
}

/** Native-owned starter metadata; title editing is not gameplay or a seed import. */
internal data class StoryCreationPreview(val template: String, val seedSha256: String,
    val defaultTitle: String, val description: String, val profile: String, val details: List<String>)
internal data class StoryCreationRequest(val preview: StoryCreationPreview, val title: String, val creationId: String)
internal data class StoryCreationClose(val saved: SavedSnapshot? = null, val refreshRequired: Boolean = false)
internal interface StoryCreationGateway {
    // A null catalog is the legacy test-port capability only. The native gateway always overrides it.
    suspend fun templates(): List<StoryTemplateOption>? = null
    suspend fun previewTemplate(template: String): StoryCreationPreview {
        if (template != DEFAULT_STORY_TEMPLATE) throw WorkspaceFailure("UnsupportedSeed")
        return preview()
    }
    suspend fun preview(): StoryCreationPreview
    suspend fun create(request: StoryCreationRequest): SavedSnapshot
}

/** Presentation validation only; Rust validates again before persistent creation. */
internal fun validStoryTitle(title: String): Boolean {
    if (title.isEmpty() || title.trim() != title || title.toByteArray(Charsets.UTF_8).size > 320) return false
    var scalars = 0
    var index = 0
    while (index < title.length) {
        val first = title[index]
        val value = if (first.isHighSurrogate()) {
            if (index + 1 >= title.length || !title[index + 1].isLowSurrogate()) return false
            Character.toCodePoint(first, title[++index])
        } else { if (first.isLowSurrogate()) return false; first.code }
        if (Character.isISOControl(value) || value in 0x2028..0x202e || value in 0x2066..0x2069) return false
        if (++scalars > 80) return false
        index++
    }
    return true
}

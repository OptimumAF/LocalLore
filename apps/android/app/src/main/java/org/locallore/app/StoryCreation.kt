/* Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0 */
package org.locallore.app

import java.util.Locale

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
internal data class StoryPlayerSetup(val templateSha256: String, val setupSha256: String, val playerName: String)
internal data class StoryPresentation(val tone: String = "plain", val excludedPhrases: List<String> = emptyList())
internal data class StoryCreationPreview(val template: String, val seedSha256: String,
    val defaultTitle: String, val description: String, val profile: String, val details: List<String>,
    val playerSetup: StoryPlayerSetup? = null, val presentation: StoryPresentation? = null)
internal data class StoryCreationRequest(val preview: StoryCreationPreview, val title: String, val creationId: String)
internal data class StoryCreationClose(val saved: SavedSnapshot? = null, val refreshRequired: Boolean = false)
internal interface StoryCreationGateway {
    fun originalStories(): OriginalStoryGateway? = null
    // A null catalog is the legacy test-port capability only. The native gateway always overrides it.
    suspend fun templates(): List<StoryTemplateOption>? = null
    suspend fun previewTemplate(template: String): StoryCreationPreview {
        if (template != DEFAULT_STORY_TEMPLATE) throw WorkspaceFailure("UnsupportedSeed")
        return preview()
    }
    // Legacy fake-port capability only. The native gateway returns a strict configured preview or fails.
    suspend fun setupPreview(template: String, playerName: String?): StoryCreationPreview? = null
    // Legacy fake-port capability only. Production does not downgrade after a native error.
    suspend fun presentationPreview(template: String, playerName: String?, presentation: StoryPresentation?): StoryCreationPreview? = null
    suspend fun preview(): StoryCreationPreview
    suspend fun create(request: StoryCreationRequest): SavedSnapshot
}

/** Presentation validation only; Rust validates again before persistent creation. */
internal fun validStoryTitle(title: String): Boolean {
    return validStoryLabel(title, 80, 320)
}
internal fun validStoryPlayerName(name: String): Boolean = validStoryLabel(name, 64, 256)
internal fun hasReviewedPlayerName(request: StoryCreationRequest, draft: String?): Boolean =
    request.preview.playerSetup?.let { validStoryPlayerName(it.playerName) && draft == it.playerName } ?: (draft == null)
internal fun validStoryPresentation(value: StoryPresentation): Boolean =
    value.tone in setOf("plain", "warm", "brisk") && value.excludedPhrases.size <= 8 &&
        value.excludedPhrases.all { validStoryLabel(it, 64, 256) } &&
        value.excludedPhrases.sumOf { it.toByteArray(Charsets.UTF_8).size } <= 1024 &&
        value.excludedPhrases.map { it.lowercase(Locale.ROOT) }.toSet().size == value.excludedPhrases.size

/** A line is one literal phrase; preserve spaces/case and invalid empty/trailing lines for review. */
internal fun storyPresentationDraft(tone: String?, phrases: String?): StoryPresentation? {
    if (tone == null || phrases == null) return null
    val value = StoryPresentation(tone, if (phrases.isEmpty()) emptyList() else phrases.split('\n'))
    return value.takeIf(::validStoryPresentation)
}
internal fun hasReviewedCreation(request: StoryCreationRequest, name: String?, tone: String?, phrases: String?): Boolean {
    if (!hasReviewedPlayerName(request, name)) return false
    val presentation = request.preview.presentation ?: return tone == null && phrases == null
    return storyPresentationDraft(tone, phrases) == presentation
}

private fun validStoryLabel(title: String, maxScalars: Int, maxBytes: Int): Boolean {
    if (title.isEmpty() || title.trim() != title || title.toByteArray(Charsets.UTF_8).size > maxBytes) return false
    var scalars = 0
    var index = 0
    while (index < title.length) {
        val first = title[index]
        val value = if (first.isHighSurrogate()) {
            if (index + 1 >= title.length || !title[index + 1].isLowSurrogate()) return false
            Character.toCodePoint(first, title[++index])
        } else { if (first.isLowSurrogate()) return false; first.code }
        if (Character.isISOControl(value) || value in 0x2028..0x202e || value in 0x2066..0x2069) return false
        if (++scalars > maxScalars) return false
        index++
    }
    return true
}

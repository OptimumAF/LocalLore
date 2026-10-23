/* Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0 */
package org.locallore.app

/** Display contracts only. Rust owns eligibility, values, provenance and canonical history. */
enum class StoryRecordSection(val wire: String, val label: String) {
    PROGRESSION("profiles", "Progression"),
    HISTORY("history", "History"),
    RELATIONSHIPS("relationships", "Relationships"),
    KNOWLEDGE("knowledge", "Knowledge"),
}

enum class StoryRecordOrigin(val wire: String, val label: String) {
    CANONICAL_FIELD("canonical_field", "Canonical field"),
    CANONICAL_TRUTH("canonical_truth", "Known world fact"),
    RECORDED_STATEMENT("recorded_statement", "Recorded statement"),
    SUBJECTIVE_BELIEF("subjective_belief", "Belief · not established fact"),
    RECORDED_DISCOVERY("recorded_discovery", "Discovery"),
    RECORDED_OBSERVATION("recorded_observation", "Recorded observation"),
    RECORDED_MESSAGE("recorded_message", "Recorded message"),
    DERIVED_COMPARISON("derived_comparison", "Derived comparison"),
}

data class StoryRecordContext(val story: SavedStory, val revision: Long)
data class StoryRecordQuery(
    val context: StoryRecordContext,
    val section: StoryRecordSection = StoryRecordSection.PROGRESSION,
    val search: String = "",
    val cursor: String? = null,
)
data class StoryRecordEntry(
    val key: String,
    val title: String,
    val text: String,
    val origin: StoryRecordOrigin,
    val sources: List<String> = emptyList(),
    val eventSources: List<Long> = emptyList(),
    val event: StoryRecordEvent? = null,
)

data class StoryRecordEvent(val sequence: Long, val turn: String, val storyTime: Long)

data class StoryRecordEventDetail(
    val reference: Long,
    val loading: Boolean = true,
    val entry: StoryRecordEntry? = null,
    val problem: StoryRecordProblem? = null,
)
data class StoryRecordPage(
    val query: StoryRecordQuery,
    val storyTime: Long,
    val total: Int,
    val entries: List<StoryRecordEntry>,
    val nextCursor: String?,
    val limitations: List<String> = emptyList(),
)
enum class StoryRecordProblem(val message: String) {
    STALE("The story changed. Close this view and recover saved progress before reopening it."),
    UNAVAILABLE("The story record is unavailable. Close it or try again."),
    INVALID_RESPONSE("The local engine returned an invalid record. Nothing was changed by browsing."),
    BAD_SEARCH("The search is too long or contains unsupported characters."),
    TOO_LARGE("This record is too large to display safely."),
    EVENT_UNAVAILABLE("This event is not available in the current player view."),
}
class StoryRecordFailure(val problem: StoryRecordProblem) : Exception("Story record unavailable")
fun interface StoryRecordReader {
    suspend fun readStoryRecord(query: StoryRecordQuery): StoryRecordPage
}
data class StoryRecordState(
    val visible: Boolean = false,
    val loading: Boolean = false,
    val context: StoryRecordContext? = null,
    val section: StoryRecordSection = StoryRecordSection.PROGRESSION,
    val search: String = "",
    val cursor: String? = null,
    val storyTime: Long? = null,
    val total: Int = 0,
    val entries: List<StoryRecordEntry> = emptyList(),
    val nextCursor: String? = null,
    val limitations: List<String> = emptyList(),
    val problem: StoryRecordProblem? = null,
    val eventDetail: StoryRecordEventDetail? = null,
)

internal const val STORY_RECORD_PAGE_ROWS = 8
internal const val STORY_RECORD_SEARCH_BYTES = 256

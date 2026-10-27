/* Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0 */
package org.locallore.app

enum class DemoAction { GIVE_POTION, TRY_ABILITY }
enum class DemoMode { ACCEPTED, MALFORMED, REJECTED, DELAYED, FAILED }
data class SceneMessage(val id: Long, val text: String, val isPlayer: Boolean)
data class SavedStory(val story: String, val branch: String, val title: String, val revision: Long)
data class SavedTimeline(
    val story: String, val branch: String, val parentBranch: String?, val forkRevision: Long?,
    val revision: Long, val uncommittedDrafts: Int,
)
data class SavedSnapshot(
    val revision: Long, val potionOwner: String, val messages: List<SceneMessage>,
    val location: String, val schemaVersion: Int, val stories: List<SavedStory>, val selected: SavedStory?,
    val uncommittedDrafts: Int = 0,
    val rulesProfile: String = "unknown",
    val textProvider: TextProvider = TextProvider.UNAVAILABLE,
    val databaseSchemaVersion: Int? = null,
    val timelines: List<SavedTimeline> = emptyList(),
    val selectionRestoreUnavailable: Boolean = false,
)
data class ShellState(
    val busy: Boolean = false,
    val preparingResponse: Boolean = false,
    val revision: Long = 0,
    val potionOwner: String = "You",
    val messages: List<SceneMessage> = emptyList(),
    val notice: String? = null,
    val mode: DemoMode = DemoMode.ACCEPTED,
    val recoveryRequired: Boolean = false,
    val persistent: Boolean = false,
    val storageLocation: String? = null,
    val schemaVersion: Int? = null,
    val stories: List<SavedStory> = emptyList(),
    val selectedStory: SavedStory? = null,
    val uncommittedDrafts: Int = 0,
    val rulesProfile: String? = null,
    val textProvider: TextProvider = TextProvider.UNAVAILABLE,
    val databaseSchemaVersion: Int? = null,
    val archiveActive: Boolean = false,
    val deletionActive: Boolean = false,
    val forkActive: Boolean = false,
    val timelines: List<SavedTimeline> = emptyList(),
    val checkingCancellation: Boolean = false,
    val creationActive: Boolean = false,
)

sealed interface DemoResult {
    data class Prepared(val session: Long, val operation: Long) : DemoResult
    data class Accepted(val revision: Long, val potionOwner: String, val narration: String) : DemoResult
    data class Rejected(val category: String) : DemoResult
}

/** Preparation may suspend. Commit and publication share one non-suspending owner-thread step. */
fun interface DemoGateway {
    suspend fun respond(action: DemoAction, revision: Long, mode: DemoMode): DemoResult
    suspend fun respondText(input: PlayInput, revision: Long): DemoResult = DemoResult.Rejected("Unsupported")
    fun commit(result: DemoResult): DemoResult = result
    fun cancel() {}
    fun reset() {}
    fun close() {}
    val durable: Boolean get() = false
    val storyRecords: Boolean get() = false
    suspend fun readStoryRecord(query: StoryRecordQuery): StoryRecordPage =
        throw StoryRecordFailure(StoryRecordProblem.UNAVAILABLE)
    suspend fun initialize(): SavedSnapshot? = null
    suspend fun snapshot(): SavedSnapshot? = null
    suspend fun commitAsync(result: DemoResult): DemoResult = commit(result)
    suspend fun createSaved(): SavedSnapshot? { reset(); return null }
    suspend fun resumeSaved(story: SavedStory): SavedSnapshot? = null
    suspend fun recoverSaved(): SavedSnapshot? = snapshot()
    suspend fun reconcileSaved(): SavedSnapshot? = snapshot()
    suspend fun cancelSaved(): SavedSnapshot? { cancel(); return snapshot() }
}

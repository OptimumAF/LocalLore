/* Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0 */
package org.locallore.app

import org.json.JSONArray
import org.json.JSONObject
import org.junit.Assert.*
import org.junit.Test

/** Android JSON validation only; Store/JNI tests separately establish canonical authority. */
class ParentRetentionProtocolTest {
    private fun bytes(data: JSONObject) = JSONObject().put("version", 1).put("status", "ok").put("data", data)
        .toString().toByteArray(Charsets.UTF_8)
    private fun scope() = JSONObject().put("story", "original-story").put("branch", "parent")
    private fun prepared() = JSONObject().put("token", 7).put("preview", JSONObject()
        .put("version", 1).put("scope", scope()).put("title", "Original story").put("root_branch", "main")
        .put("expected_revision", 5).put("retained_descendants", JSONObject().put("child", 4))
        .put("retained_heads", JSONObject().put("parent", 4)).put("removed_branches", JSONArray())
        .put("removed_rows", JSONObject().put("derived_memory", 1).put("event_witnesses", 1)
            .put("accepted_events", 1).put("turns", 2).put("branch_projections", 1).put("branch_entities", 0).put("branches", 0))
        .put("removed_committed_turns", 1).put("removed_noncommitted_turns", 1).put("privacy_warning", "Export copies remain."))
    private fun rejects(action: () -> Unit) {
        try { action(); fail("Malformed consent accepted") }
        catch (failure: ArchiveFailure) { assertEquals("Integrity", failure.category) }
    }
    @Test fun exactRetainedParentConsentAndMalformedChanges() {
        val decoded = ArchiveNativeWire.branchDeletionPrepared(bytes(prepared()))
        assertEquals(7L, decoded.token); assertEquals(4L, decoded.preview.retainedHeads["parent"])
        assertEquals(mapOf("child" to 4L), decoded.preview.retainedDescendants)
        val mutations: List<(JSONObject) -> Unit> = listOf(
            { it.put("token", "7") }, { it.put("token", 0) },
            { it.put("extra", "PRIVATE-CANARY") },
            { it.getJSONObject("preview").put("version", 2) },
            { it.getJSONObject("preview").put("root_branch", "parent") },
            { it.getJSONObject("preview").getJSONObject("scope").put("story", "bad/path") },
            { it.getJSONObject("preview").put("expected_revision", 5.5) },
            { it.getJSONObject("preview").getJSONObject("retained_heads").put("main", 4) },
            { it.getJSONObject("preview").getJSONObject("retained_descendants").put("parent", 4) },
            { it.getJSONObject("preview").put("removed_branches", JSONArray().put("parent")) },
            { it.getJSONObject("preview").put("retained_heads", JSONObject()) },
            { it.getJSONObject("preview").getJSONObject("removed_rows").put("branches", 1) },
            { it.getJSONObject("preview").getJSONObject("removed_rows").put("turns", -1) },
            { it.getJSONObject("preview").put("removed_noncommitted_turns", 0) },
        )
        mutations.forEach { mutation -> rejects { ArchiveNativeWire.branchDeletionPrepared(bytes(prepared().also(mutation))) } }
        rejects { ArchiveNativeWire.branchDeletionPrepared(ByteArray(65537)) }
    }
    @Test fun deletionResultRequiresBoundedExactScopeAndInvalidationIds() {
        fun result() = JSONObject().put("scope", scope()).put("retained_through_revision", 4)
            .put("collected_branches", 0).put("deleted_turns", 2).put("invalidated_branches", JSONArray().put("parent"))
        val decoded = ArchiveNativeWire.branchDeleted(bytes(result()))
        assertEquals(4L, decoded.retainedThroughRevision); assertEquals(listOf("parent"), decoded.invalidatedBranches)
        val mutations: List<(JSONObject) -> Unit> = listOf(
            { it.put("retained_through_revision", "4") }, { it.put("collected_branches", 257) },
            { it.put("deleted_turns", -1) }, { it.put("invalidated_branches", JSONArray()) },
            { it.put("invalidated_branches", JSONArray().put("child")) },
            { it.put("invalidated_branches", JSONArray().put("parent").put("parent")) },
            { it.put("invalidated_branches", JSONArray().put("parent").put("earlier")) },
            { it.put("extra", true) },
        )
        mutations.forEach { mutation -> rejects { ArchiveNativeWire.branchDeleted(bytes(result().also(mutation))) } }
    }
    @Test fun schemaFourDeletionCountsHaveExactVersionedKeysAndPacketTotals() {
        fun currentBranch() = prepared().also { value ->
            val preview = value.getJSONObject("preview").put("version", 2)
            preview.getJSONObject("removed_rows").put("memory_jobs", 1).put("memory_job_packets", 3)
        }
        val branch = ArchiveNativeWire.branchDeletionPrepared(bytes(currentBranch())).preview
        assertEquals(2, branch.version); assertEquals(3L, branch.removedRows["memory_job_packets"])
        val branchMutations: List<(JSONObject) -> Unit> = listOf(
            { it.put("version", 3) },
            { it.getJSONObject("removed_rows").remove("memory_jobs") },
            { it.getJSONObject("removed_rows").put("memory_job_packets", -1) },
            { it.getJSONObject("removed_rows").put("foreign_table", 0) },
            { it.put("version", 1) },
        )
        branchMutations.forEach { mutation -> rejects {
            ArchiveNativeWire.branchDeletionPrepared(bytes(currentBranch().also { mutation(it.getJSONObject("preview")) }))
        } }
        fun story(version: Int): JSONObject {
            val rows = JSONObject().put("derived_memory", 2).put("event_witnesses", 1)
                .put("accepted_events", 1).put("turns", 2).put("branch_projections", 1)
                .put("branch_entities", 4).put("entities", 4).put("branches", 1).put("stories", 1)
            if (version >= 2) rows.put("branch_retention", 0)
            if (version == 3) rows.put("memory_jobs", 1).put("memory_job_packets", 3)
            return JSONObject().put("token", 9).put("preview", JSONObject().put("version", version)
                .put("story_id", "original-story").put("title", "Original story").put("root_branch", "main")
                .put("branch_heads", JSONObject().put("main", 5)).put("committed_turns", 1)
                .put("draft_turns", 1).put("noncommitted_turns", 1)
                .put("derived_packets", if (version == 3) 5 else 2).put("rows", rows)
                .put("privacy_warning", "Export copies remain."))
        }
        for (version in 1..3) {
            val preview = ArchiveNativeWire.deletionPrepared(bytes(story(version))).preview
            assertEquals(version, preview.version)
            assertEquals(if (version == 3) 5L else 2L, preview.derivedPackets)
        }
        val storyMutations: List<(JSONObject) -> Unit> = listOf(
            { it.put("version", 4) }, { it.put("version", 2) },
            { it.getJSONObject("rows").remove("memory_jobs") },
            { it.getJSONObject("rows").put("memory_job_packets", -1) },
            { it.getJSONObject("rows").put("foreign_table", 0) },
            { it.put("derived_packets", 2) }, { it.put("derived_packets", 6) },
            { it.getJSONObject("rows").put("derived_memory", Long.MAX_VALUE)
                .put("memory_job_packets", Long.MAX_VALUE); it.put("derived_packets", Long.MAX_VALUE) },
        )
        storyMutations.forEach { mutation -> rejects {
            ArchiveNativeWire.deletionPrepared(bytes(story(3).also { mutation(it.getJSONObject("preview")) }))
        } }
    }
    @Test fun archiveV2RequiresNonemptySortedRetirementMetadataAndPreservesV1() {
        fun data() = JSONObject().put("token", 1).put("preview", JSONObject()
            .put("version", 2).put("story_id", "original-story").put("title", "Original story").put("root_branch", "main")
            .put("branch_heads", JSONObject().put("main", 4).put("child", 4).put("parent", 4))
            .put("committed_turns", 6).put("bytes", 100).put("payload_sha256", "a".repeat(64))
            .put("privacy_warning", "Export copies remain.").put("noncommitted_workflow_transferred", false)
            .put("retired_branch_ids", JSONArray().put("collected").put("parent")))
        assertEquals(listOf("collected", "parent"), ArchiveNativeWire.prepared(bytes(data())).preview.retiredBranchIds)
        val legacy = data().also { it.getJSONObject("preview").put("version", 1).remove("retired_branch_ids") }
        assertTrue(ArchiveNativeWire.prepared(bytes(legacy)).preview.retiredBranchIds.isEmpty())
        val mutations: List<(JSONObject) -> Unit> = listOf(
            { it.put("version", 1) }, { it.remove("retired_branch_ids") },
            { it.put("retired_branch_ids", JSONObject.NULL) },
            { it.put("retired_branch_ids", JSONArray()) },
            { it.put("retired_branch_ids", JSONArray().put("main")) },
            { it.put("retired_branch_ids", JSONArray().put("parent").put("parent")) },
            { it.put("retired_branch_ids", JSONArray().put("parent").put("collected")) },
            { it.put("retired_branch_ids", JSONArray().put(7)) },
        )
        mutations.forEach { mutation -> rejects { ArchiveNativeWire.prepared(bytes(data().also { mutation(it.getJSONObject("preview")) })) } }
    }
}

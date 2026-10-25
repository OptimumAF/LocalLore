/* Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0 */
package org.locallore.app

import androidx.compose.material3.MaterialTheme
import androidx.compose.ui.test.assertTextEquals
import androidx.compose.ui.test.junit4.createComposeRule
import androidx.compose.ui.test.onNodeWithTag
import androidx.compose.ui.test.onNodeWithText
import androidx.compose.ui.test.performScrollTo
import androidx.test.ext.junit.runners.AndroidJUnit4
import org.json.JSONArray
import org.json.JSONObject
import org.junit.Assert.*
import org.junit.Rule
import org.junit.Test
import org.junit.runner.RunWith
import org.locallore.app.ui.ArchiveDialog

/**
 * Frozen D08.01/.02/.07 + M08.03 actual Android-decoder/Compose oracles, UNRUN at freeze.
 * Compile only, from apps/android (no device execution):
 *   ./gradlew.bat --offline :app:compileDebugAndroidTestKotlin
 * Future separately authorized instrumented runtime, not authorized by this packet:
 *   ./gradlew.bat --offline :app:connectedDebugAndroidTest
 *     -Pandroid.testInstrumentationRunnerArguments.class=org.locallore.app.ArchiveV3WireTest
 *
 * This is androidTest deliberately: host JVM android.jar JSONObject is a stub and
 * existing typed JVM tests never exercised ArchiveNativeWire. No replacement parser,
 * JNI/Store invocation, model, archive payload validation or new dependency is used.
 * These are synthetic transport fixtures shaped from actual Rust ArchivePreview serde
 * plus Registry success/token envelopes, NOT newly captured native producer output.
 * Producer preview empty retired IDs are OMITTED. Root also accepts explicit [] as
 * V3 input compatibility; that case is distinguished from the producer's serializer.
 * The Archive3 payload's REQUIRED possibly-empty array is a different contract.
 * committed_turns counts accepted canonical records,
 * including author corrections; branch heads cannot reconstruct that count.
 * Unchanged decoder should reject valid V3; predicted RED is not an executed result.
 */
@RunWith(AndroidJUnit4::class)
class ArchiveV3WireTest {
    @get:Rule val compose = createComposeRule()

    private val warning = "Full private story: all timelines, hidden seed facts, author corrections/reasons/prior truth, " +
        "private discovery source bindings, accepted input/narration and model/timing/provenance metadata. " +
        "Accepted records include play and author corrections. No weights, separate traces/raw prompts, caches or " +
        "noncommitted workflow keys/status. Imported sessions must not resume old pending operations."
    private val legacyWarning = "Full private story: all timelines, hidden seed facts, accepted input/narration and " +
        "model/timing/provenance metadata. No weights, separate traces/raw prompt logs, caches or noncommitted " +
        "workflow keys/status. Imported sessions must not resume old pending operations."

    private fun fixture(version: Int = 3, retired: Boolean = false): JSONObject {
        val heads = JSONObject().put("main", 1).put("child", 3)
        if (retired) heads.put("parent", 2)
        val preview = JSONObject().put("version", version).put("story_id", "synthetic-mixed")
            .put("title", "Synthetic mixed accepted history").put("root_branch", "main")
            .put("branch_heads", heads).put("committed_turns", 3).put("bytes", 1024)
            .put("payload_sha256", "a".repeat(64)).put("privacy_warning", if (version == 3) warning else legacyWarning)
            .put("noncommitted_workflow_transferred", false)
        if (retired) preview.put("retired_branch_ids", JSONArray(listOf("collected", "parent")))
        return JSONObject().put("version", 1).put("status", "ok")
            .put("data", JSONObject().put("token", 17).put("preview", preview))
    }

    private fun JSONObject.preview() = getJSONObject("data").getJSONObject("preview")
    private fun decode(value: JSONObject) = ArchiveNativeWire.prepared(value.toString().toByteArray(Charsets.UTF_8))
    private fun reject(value: JSONObject) {
        try {
            decode(value)
            fail("Malformed synthetic preview was accepted")
        } catch (failure: ArchiveFailure) { assertEquals("Integrity", failure.category) }
    }

    private fun assertAccepted(value: JSONObject, version: Int, retired: Boolean) {
        val result = decode(value)
        assertEquals(17L, result.token)
        assertEquals(version, result.preview.version)
        assertEquals("synthetic-mixed", result.preview.storyId)
        assertEquals("main", result.preview.rootBranch)
        assertEquals(3L, result.preview.branchHeads["child"])
        assertEquals(3, result.preview.committedTurns)
        assertNotEquals(3L, result.preview.branchHeads.values.sum())
        assertEquals(if (retired) listOf("collected", "parent") else emptyList<String>(), result.preview.retiredBranchIds)
        assertEquals(retired, value.preview().has("retired_branch_ids"))
        assertEquals(if (version == 3) warning else legacyWarning, result.preview.privacyWarning)
        assertFalse(result.preview.noncommittedWorkflowTransferred)
    }

    @Test fun existingV1AndV2PreviewContinuityUsesTheActualDecoder() {
        assertAccepted(fixture(1), 1, false)
        assertAccepted(fixture(2, true), 2, true)
    }

    @Test fun v3EmptyRetirementIsOmittedAndCanonicalCountIncludesAuthorRecords() {
        assertAccepted(fixture(), 3, false)
    }

    @Test fun v3RetainsSortedPhysicalAncestryAndCollectedIdentityTombstones() {
        assertAccepted(fixture(3, true), 3, true)
    }

    @Test fun v3AlsoAcceptsAnExplicitEmptyRetirementArrayAsCompatibleInput() {
        val value = fixture()
        value.preview().put("retired_branch_ids", JSONArray())
        val result = decode(value)
        assertEquals(3, result.preview.version)
        assertEquals(3, result.preview.committedTurns)
        assertTrue(result.preview.retiredBranchIds.isEmpty())
        assertTrue(value.preview().has("retired_branch_ids"))
    }

    @Test fun nativeTransportCountAndArtifactBoundsStayUnchanged() {
        val value = fixture()
        value.preview().put("committed_turns", 4096).put("bytes", MAX_ARCHIVE_BYTES)
        val result = decode(value)
        assertEquals(4096, result.preview.committedTurns)
        assertEquals(MAX_ARCHIVE_BYTES.toLong(), result.preview.bytes)
    }

    @Test fun nullWrongUnknownAndFutureFieldsCannotAcquirePreviewAuthority() {
        // Existing V1 negatives cannot pass merely because the decoder rejects all V3.
        for (version in listOf(1, 3)) {
            val mutations: List<(JSONObject) -> Unit> = listOf(
                { it.put("future", true) },
                { it.getJSONObject("data").put("future", true) },
                { it.preview().put("future", true) },
                { it.preview().put("author_reason", "synthetic reason") },
                { it.getJSONObject("data").put("preview", JSONObject.NULL) },
                { it.getJSONObject("data").put("preview", JSONArray()) },
                { it.put("version", 2) },
                { it.put("status", "future") },
                { it.getJSONObject("data").put("token", JSONObject.NULL) },
                { it.getJSONObject("data").put("token", 0) },
                { it.preview().put("version", JSONObject.NULL) },
                { it.preview().put("version", version.toString()) },
                { it.preview().put("version", 4) },
                { it.preview().put("version", 1.5) },
                { it.preview().put("branch_heads", JSONObject.NULL) },
                { it.preview().getJSONObject("branch_heads").remove("main") },
                { it.preview().getJSONObject("branch_heads").put("child", -1) },
                { it.preview().getJSONObject("branch_heads").put("child", "3") },
                { it.preview().put("committed_turns", JSONObject.NULL) },
                { it.preview().put("committed_turns", -1) },
                { it.preview().put("committed_turns", 0.5) },
                { it.preview().put("committed_turns", 4097) },
                { it.preview().put("bytes", MAX_ARCHIVE_BYTES.toLong() + 1) },
                { it.preview().put("payload_sha256", "not-a-checksum") },
                { it.preview().put("privacy_warning", JSONObject.NULL) },
                { it.preview().put("noncommitted_workflow_transferred", true) },
            )
            for (mutate in mutations) reject(fixture(version).also(mutate))
        }
    }

    @Test fun retiredPreviewMetadataCannotBeNullUnsortedOrOutOfBounds() {
        val bad: List<Any> = listOf(
            JSONObject.NULL, "parent", JSONArray(listOf("parent", "parent")),
            JSONArray(listOf("parent", "collected")), JSONArray(listOf("main")),
            JSONArray(listOf("bad/id")), JSONArray(listOf(1)),
            JSONArray((0..256).map { "old-${it.toString().padStart(3, '0')}" }),
            JSONArray((0..254).map { "old-${it.toString().padStart(3, '0')}" }),
        )
        for (version in listOf(2, 3)) for (ids in bad) {
            reject(fixture(version).also { it.preview().put("retired_branch_ids", ids) })
        }
        reject(fixture(1).also { it.preview().put("retired_branch_ids", JSONArray(listOf("parent"))) })
        reject(fixture(2).also { it.preview().put("retired_branch_ids", JSONArray()) })
        reject(fixture(2, true).also { it.preview().remove("retired_branch_ids") })
    }

    @Test fun importedOutcomeKeepsCanonicalRecordCountInTheExistingReplyShape() {
        // These are the existing import-result fields. Decoding them alone proves
        // neither a performed import nor that pending work/model loading was avoided.
        val wire = JSONObject().put("version", 1).put("status", "ok").put("data", JSONObject()
            .put("root", JSONObject().put("story", "synthetic-mixed").put("branch", "main"))
            .put("branches", 2).put("committed_turns", 3))
        val result = ArchiveNativeWire.imported(wire.toString().toByteArray(Charsets.UTF_8))
        assertEquals("synthetic-mixed", result.story)
        assertEquals("main", result.branch)
        assertEquals(2, result.branches)
        assertEquals(3, result.committedTurns)
    }

    @Test fun actualDialogLabelsV3CanonicalRecordsWithoutCallingThemGameplayTurns() {
        val prepared = decode(fixture())
        compose.setContent {
            MaterialTheme {
                ArchiveDialog(
                    ArchiveUiState(visible = true, selected = SavedStory("synthetic-mixed", "child", "Synthetic", 3),
                        prepared = prepared, kind = ArchiveKind.IMPORT),
                    {}, {}, {}, {}, {}, {}, {},
                )
            }
        }
        compose.onNodeWithTag("archive-preview").assertExists()
        compose.onNodeWithText("2 timelines · 3 accepted records · 1024 bytes").performScrollTo()
            .assertTextEquals("2 timelines · 3 accepted records · 1024 bytes")
        compose.onNodeWithText("2 timelines · 3 committed turns · 1024 bytes").assertDoesNotExist()
    }
}

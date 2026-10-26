/* Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0 */
package org.locallore.app

import androidx.test.ext.junit.runners.AndroidJUnit4
import org.json.JSONArray
import org.json.JSONObject
import org.junit.Assert.*
import org.junit.Test
import org.junit.runner.RunWith

/** Actual Android JSONObject decoder/encoder assertions, not JNI or creation authority.
 * Source-only handoff: coordinator must compile and execute this exact class.
 */
@RunWith(AndroidJUnit4::class)
class StoryCreationWireTest {
    private val template = "lantern-quay-v1"
    private val hash = "a".repeat(64)
    private val id = "b".repeat(32)
    private fun original(): JSONObject = JSONObject().put("version", 1).put("template", template)
        .put("seed_sha256", hash).put("default_title", "Lantern Quay").put("profile", "fantasy_v1")
        .put("description", "Original synthetic starter review.")
        .put("details", JSONArray().put("Player: Rowan").put("Inventory potion: 1"))
    private fun fields(value: JSONObject) = value.keys().asSequence().toSet()
    private fun preview(data: JSONObject = original()) = StoryCreationWire.preview(data)
    private fun request(title: String = "Original title", creationId: String = id,
        captured: StoryCreationPreview = preview()) = StoryCreationRequest(captured, title, creationId)
    private fun refused(category: String = "Malformed", block: () -> Unit) {
        try { block(); fail("Invalid creation wire accepted") }
        catch (failure: WorkspaceFailure) {
            assertEquals(category, failure.category)
            assertEquals("Workspace operation failed", failure.message)
        }
    }

    @Test fun exactClosedPreviewAcceptsIntegralVersionAndPreservesOriginalUnicodeMetadata() {
        val data = original().put("default_title", "Quay 雪 😀")
            .put("description", "Original \"quoted\" description \\ 雪\nsecond line")
            .put("details", JSONArray().put("Original é 😀\nline").put("literal \\u0020 remains text"))
        for (version in listOf<Any>(1, 1L)) {
            val decoded = preview(data.put("version", version))
            assertEquals(template, decoded.template); assertEquals(hash, decoded.seedSha256)
            assertEquals("Quay 雪 😀", decoded.defaultTitle); assertEquals("fantasy_v1", decoded.profile)
            assertEquals("Original \"quoted\" description \\ 雪\nsecond line", decoded.description)
            assertEquals(listOf("Original é 😀\nline", "literal \\u0020 remains text"), decoded.details)
        }
    }

    @Test fun previewRequiresExactlySevenKeysAndStrictVersionTemplateProfileAndHashTypes() {
        val keys = setOf("version", "template", "seed_sha256", "default_title", "description", "profile", "details")
        assertEquals(keys, fields(original()))
        for (key in keys) {
            refused { preview(original().also { it.remove(key) }) }
            refused { preview(original().put(key, JSONObject.NULL)) }
        }
        refused { preview(original().put("private", "ORIGINAL_PRIVATE_CANARY")) }
        for (wrong in listOf<Any>("1", 1.0, true, 0, 2, 4294967297L, JSONArray(), JSONObject())) {
            refused { preview(original().put("version", wrong)) }
        }
        for ((key, wrong) in listOf("template" to "foreign-starter", "profile" to "fantasy_v2",
            "seed_sha256" to "A".repeat(64), "seed_sha256" to "a".repeat(63), "seed_sha256" to "g".repeat(64))) {
            refused { preview(original().put(key, wrong)) }
        }
        for (key in listOf("template", "profile", "seed_sha256", "default_title", "description")) {
            for (wrong in listOf<Any>(1, true, JSONArray(), JSONObject())) {
                refused { preview(original().put(key, wrong)) }
            }
        }
    }

    @Test fun detailArrayHasFiniteNonemptyStringRowsAndPerRowUtf8Bounds() {
        refused { preview(original().put("details", "not an array")) }
        refused { preview(original().put("details", JSONArray())) }
        for (wrong in listOf<Any>(JSONObject.NULL, 1, true, JSONArray(), JSONObject(), "")) {
            refused { preview(original().put("details", JSONArray().put(wrong))) }
        }
        val sixtyFour = JSONArray().also { rows -> repeat(64) { rows.put("row-$it") } }
        assertEquals(64, preview(original().put("details", sixtyFour)).details.size)
        refused { preview(original().put("details", sixtyFour.put("row-64"))) }
        val boundary = "😀".repeat(512)
        assertEquals(2048, boundary.toByteArray(Charsets.UTF_8).size)
        assertEquals(listOf(boundary), preview(original().put("details", JSONArray().put(boundary))).details)
        refused { preview(original().put("details", JSONArray().put(boundary + "x"))) }
    }

    @Test fun descriptionUtf8AndWholePreviewByteCapsAcceptExactBoundaryAndRefuseOverflow() {
        val boundary = "😀".repeat(512)
        assertEquals(boundary, preview(original().put("description", boundary)).description)
        refused { preview(original().put("description", "")) }
        refused { preview(original().put("description", boundary + "x")) }
        val rows = JSONArray().also { array -> repeat(7) { array.put("x".repeat(2048)) }; array.put("x") }
        val exact = original().put("details", rows)
        val remaining = 16384 - exact.toString().toByteArray(Charsets.UTF_8).size
        assertTrue(remaining in 0..2046)
        rows.put(7, "x".repeat(remaining + 1))
        assertEquals(16384, exact.toString().toByteArray(Charsets.UTF_8).size)
        assertEquals(8, preview(exact).details.size)
        rows.put(7, "x".repeat(remaining + 2))
        assertEquals(16385, exact.toString().toByteArray(Charsets.UTF_8).size)
        refused { preview(exact) }
    }

    @Test fun decodedDetailsAreIndependentOfMutableInputAndCannotBeModifiedThroughTheList() {
        val rows = JSONArray().put("Original first").put("Original second")
        val data = original().put("details", rows)
        val captured = preview(data)
        rows.put(0, "Changed source row"); rows.put("Added source row")
        data.put("details", JSONArray().put("Replacement"))
        data.put("default_title", "Replacement title")
        assertEquals(listOf("Original first", "Original second"), captured.details)
        assertEquals("Lantern Quay", captured.defaultTitle)
        try {
            (captured.details as MutableList<String>).add("Forbidden mutable view")
            fail("Decoded details remained mutable")
        } catch (_: UnsupportedOperationException) { /* Exact unmodifiable-copy contract. */ }
        assertEquals(listOf("Original first", "Original second"), captured.details)
    }

    @Test fun commandIsOnlyTheFiveClosedCommandFieldsAndPreservesTheCapturedTitleAndIdentity() {
        val title = "Original \"title\" \\ 雪 😀"
        val captured = request(title)
        val first = StoryCreationWire.command(captured)
        assertEquals(setOf("op", "template", "seed_sha256", "title", "creation_id"), fields(first))
        assertEquals("create_named", first.get("op")); assertEquals(template, first.get("template"))
        assertEquals(hash, first.get("seed_sha256")); assertEquals(id, first.get("creation_id"))
        assertEquals(title, first.get("title"))
        assertFalse(first.has("version")); assertFalse(first.has("command")); assertFalse(first.has("details"))
        first.put("title", "Mutated encoded output").put("private", "ORIGINAL_PRIVATE_CANARY")
        val second = StoryCreationWire.command(captured)
        assertEquals(title, second.get("title")); assertFalse(second.has("private"))
        assertEquals(title, captured.title)
        // Well-formed metadata is not proof of a currently bundled seed; native still checks Stale.
        val stale = request(captured = preview().copy(seedSha256 = "0".repeat(64)))
        assertEquals("0".repeat(64), StoryCreationWire.command(stale).get("seed_sha256"))
    }

    @Test fun titleScalarUtf8AndForbiddenCodePointRulesApplyBeforeSendingAndToDefaultTitle() {
        val exact = "😀".repeat(80)
        assertEquals(160, exact.length); assertEquals(320, exact.toByteArray(Charsets.UTF_8).size)
        assertEquals(exact, StoryCreationWire.command(request(exact)).get("title"))
        assertEquals(exact, preview(original().put("default_title", exact)).defaultTitle)
        assertEquals("a".repeat(80), StoryCreationWire.command(request("a".repeat(80))).get("title"))
        val invalid = listOf("", " leading", "trailing ", "line\nfeed", "tab\tinside", "nul\u0000inside",
            "line\u2028separator", "paragraph\u2029separator", "bidi\u202Econtrol", "isolate\u2067control",
            "\uD800", "\uDC00", "x\uD800y", "x\uDC00y", "a".repeat(81), "😀".repeat(81))
        for (title in invalid) {
            refused("InvalidTitle") { StoryCreationWire.command(request(title)) }
            refused { preview(original().put("default_title", title)) }
        }
        // Printable punctuation is literal display text, not a path/command or additional native field.
        val literal = "../literal <title> {not an op}"
        assertEquals(literal, StoryCreationWire.command(request(literal)).get("title"))
    }

    @Test fun commandRejectsForeignTemplateMalformedHashesAndNoncanonicalCreationIds() {
        for (bad in listOf("", "a".repeat(31), "a".repeat(33), "A".repeat(32), "g".repeat(32),
            "../".repeat(11), "é".repeat(16), "a".repeat(31) + "\n")) {
            refused { StoryCreationWire.command(request(creationId = bad)) }
        }
        for (bad in listOf("", "a".repeat(63), "a".repeat(65), "A".repeat(64), "g".repeat(64))) {
            refused { StoryCreationWire.command(request(captured = preview().copy(seedSha256 = bad))) }
        }
        refused { StoryCreationWire.command(request(captured = preview().copy(template = "foreign-starter"))) }
    }
}

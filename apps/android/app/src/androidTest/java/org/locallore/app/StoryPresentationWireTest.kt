/* Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0 */
package org.locallore.app

import androidx.test.ext.junit.runners.AndroidJUnit4
import androidx.test.platform.app.InstrumentationRegistry
import java.io.File
import kotlinx.coroutines.runBlocking
import org.json.JSONArray
import org.json.JSONObject
import org.junit.Assert.*
import org.junit.Test
import org.junit.runner.RunWith

/** Strict wire, production adapter and opt-in probe checks; no model-quality claim. */
@RunWith(AndroidJUnit4::class)
class StoryPresentationWireTest {
    private fun settings(tone: String = "plain", phrases: List<String> = emptyList()) =
        JSONObject().put("version", 1).put("tone", tone).put("excluded_phrases", JSONArray(phrases))
    private fun original(presentation: JSONObject = settings()) = JSONObject().put("version", 1).put("template", DEFAULT_STORY_TEMPLATE)
        .put("template_sha256", "a".repeat(64)).put("setup_sha256", "b".repeat(64)).put("player_name", "Rowan")
        .put("default_title", "Lantern Quay").put("description", "Original starter.").put("profile", "fantasy_v1")
        .put("presentation", presentation).put("details", JSONArray().put("Player: Rowan"))
    private fun refused(category: String = "Malformed", action: () -> Unit) {
        try { action(); fail("Invalid presentation accepted") }
        catch (failure: WorkspaceFailure) { assertEquals(category, failure.category) }
    }

    @Test fun presentationPreviewRequiresClosedBoundedLiteralSettings() {
        val keys = setOf("version", "template", "template_sha256", "setup_sha256", "default_title", "description",
            "profile", "player_name", "presentation", "details")
        assertEquals(keys, original().keys().asSequence().toSet())
        val wave = String(Character.toChars(0x1f30a))
        val exact = (0..3).map { wave.repeat(63) + String(Character.toChars(0x1f300 + it)) }
        for (tone in listOf("plain", "warm", "brisk")) {
            val result = StoryCreationWire.presentationPreview(original(settings(tone, exact)))
            assertEquals(StoryPresentation(tone, exact), result.presentation)
            assertEquals(1024, result.presentation!!.excludedPhrases.sumOf { it.toByteArray(Charsets.UTF_8).size })
        }
        val literal = listOf("Red fog", "\u00df", "SS", "\u00e9", "e\u0301")
        val data = original(settings("warm", literal))
        val captured = StoryCreationWire.presentationPreview(data)
        val capturedSettings = captured.presentation!!
        data.getJSONObject("presentation").getJSONArray("excluded_phrases").put(0, "Changed source")
        assertEquals(literal, capturedSettings.excludedPhrases)
        try { (capturedSettings.excludedPhrases as MutableList<String>).clear(); fail("Mutable metadata") }
        catch (_: UnsupportedOperationException) {}
        for (key in keys) {
            refused { StoryCreationWire.presentationPreview(original().also { it.remove(key) }) }
            refused { StoryCreationWire.presentationPreview(original().put(key, JSONObject.NULL)) }
        }
        for (key in listOf("version", "tone", "excluded_phrases")) {
            refused { StoryCreationWire.presentationPreview(original(settings().also { it.remove(key) })) }
            refused { StoryCreationWire.presentationPreview(original(settings().put(key, JSONObject.NULL))) }
        }
        refused { StoryCreationWire.presentationPreview(original(settings().put("topic_filter", true))) }
        for (version in listOf<Any>(1.0, true, "1", 2)) refused {
            StoryCreationWire.presentationPreview(original(settings().put("version", version)))
        }
        for (tone in listOf("PLAIN", "gentle", "", "warm ")) refused { StoryCreationWire.presentationPreview(original(settings(tone))) }
        for (bad in listOf("", " leading", "trailing ", "line\nbreak", "x\u202e", "x\u2066", "nul\u0000",
            "\uD800", "\uDC00", "n".repeat(65), wave.repeat(65))) {
            refused { StoryCreationWire.presentationPreview(original(settings("plain", listOf(bad)))) }
        }
        for (bad in listOf(listOf("echo", "ECHO"), listOf("\u0130", "i\u0307"), exact + "z", (1..9).map { "phrase-$it" })) {
            refused { StoryCreationWire.presentationPreview(original(settings("plain", bad))) }
        }
        for (bad in listOf<Any>(true, 1, JSONObject.NULL, JSONObject())) refused {
            StoryCreationWire.presentationPreview(original(settings().put("excluded_phrases", JSONArray().put(bad))))
        }
        refused { StoryCreationWire.presentationPreview(original().put("private", "Unrequested")) }
        refused { StoryCreationWire.presentationPreview(original().put("details", JSONArray().put("x".repeat(16384)))) }
    }

    @Test fun presentedCreationPreservesLegacyWireAndProbeSemantics() {
        val preview = StoryCreationWire.presentationPreview(original(settings("warm", listOf("Red fog"))))
        val request = StoryCreationRequest(preview, "Original title", "c".repeat(32))
        val encoded = StoryCreationWire.command(request)
        assertEquals(setOf("op", "template", "template_sha256", "setup_sha256", "player_name", "presentation", "title", "creation_id"),
            encoded.keys().asSequence().toSet())
        assertEquals("create_presented", encoded.getString("op"))
        assertEquals("Red fog", encoded.getJSONObject("presentation").getJSONArray("excluded_phrases").getString(0))
        val configured = StoryCreationWire.command(request.copy(preview = preview.copy(presentation = null)))
        assertEquals(setOf("op", "template", "template_sha256", "setup_sha256", "player_name", "title", "creation_id"),
            configured.keys().asSequence().toSet())
        assertEquals("create_configured", configured.getString("op"))
        val named = StoryCreationWire.command(request.copy(preview = preview.copy(presentation = null, playerSetup = null)))
        assertEquals(setOf("op", "template", "seed_sha256", "title", "creation_id"), named.keys().asSequence().toSet())
        assertEquals("create_named", named.getString("op"))
        refused { StoryCreationWire.command(request.copy(preview = preview.copy(playerSetup = null))) }
        refused("InvalidInput") { StoryCreationWire.command(request.copy(preview = preview.copy(presentation = StoryPresentation("unknown")))) }

        val context = InstrumentationRegistry.getInstrumentation().targetContext
        assertTrue(BuildConfig.INPUT_PROCESS_VERIFICATION)
        assertEquals("org.locallore.app.draftprocessverify", context.packageName)
        val run = "cb92da7130f486e5"
        val root = File(context.noBackupFilesDir, "process-verify-v1/$run")
        ProcessVerificationProbe.configure(context, run, 54, false)
        try {
            ProcessVerificationProbe.created(null); ProcessVerificationProbe.operation("workspace"); ProcessVerificationProbe.saved(null)
            val files = listOf("created.json", "commands.json", "saved.json").map { File(root, it) }
            val before = files.map { it.readBytes() }
            ProcessVerificationProbe.operation("story_presentation"); ProcessVerificationProbe.operation("story_presentation_view")
            files.zip(before).forEach { (file, bytes) -> assertArrayEquals(bytes, file.readBytes()) }
            val previous = JSONObject(before[1].toString(Charsets.UTF_8)).getJSONObject("operations")
            ProcessVerificationProbe.operation("create_presented")
            val result = JSONObject(files[1].readText(Charsets.UTF_8))
            assertEquals(2, result.getInt("version"))
            val counts = result.getJSONObject("operations")
            assertEquals(14, counts.length())
            assertEquals(previous.keys().asSequence().toSet(), counts.keys().asSequence().toSet())
            for (key in previous.keys()) assertEquals(previous.getInt(key) + if (key == "create_named") 1 else 0, counts.getInt(key))
            assertArrayEquals(before[0], files[0].readBytes()); assertArrayEquals(before[2], files[2].readBytes())
        } finally { ProcessVerificationProbe.configure(context, null, 54, false) }
    }

    @Test fun nativePresentationGatewayRefusesMalformedOrForeignResults() = runBlocking {
        val calls = mutableListOf<JSONObject>()
        var mode = "ok"
        val source = mutableListOf("Red fog")
        var closes = 0
        val transport = object : WorkspaceTransport {
            override suspend fun exchange(command: JSONObject): JSONObject {
                calls += JSONObject(command.toString())
                assertEquals("story_presentation", command.getString("op"))
                assertEquals(setOf("op", "template", "player_name", "presentation"), command.keys().asSequence().toSet())
                if (mode == "rejected") return JSONObject().put("version", 1).put("status", "rejected").put("error", "InvalidInput")
                val metadata = if (command.isNull("presentation")) settings() else command.getJSONObject("presentation")
                val data = original(JSONObject(metadata.toString()))
                if (!command.isNull("player_name")) data.put("player_name", command.getString("player_name"))
                when (mode) {
                    "foreign" -> data.getJSONObject("presentation").put("tone", "brisk")
                    "malformed" -> data.put("presentation", JSONObject.NULL)
                    "mutate" -> { source[0] = "Changed caller"; data.getJSONObject("presentation").put("excluded_phrases", JSONArray(source)) }
                }
                return JSONObject().put("version", 1).put("status", "ok").put("data", data)
            }
            override fun close() { closes++ }
        }
        val gateway = DurableGateway(transport, autoCreateIfEmpty = false)
        try {
            assertEquals(StoryPresentation(), gateway.presentationPreview(DEFAULT_STORY_TEMPLATE, null, null).presentation)
            assertEquals(StoryPresentation("warm", listOf("Red fog")),
                gateway.presentationPreview(DEFAULT_STORY_TEMPLATE, "Marin", StoryPresentation("warm", source)).presentation)
            for (failure in listOf("foreign", "malformed", "rejected", "mutate")) {
                mode = failure
                try { gateway.presentationPreview(DEFAULT_STORY_TEMPLATE, "Marin", StoryPresentation("warm", source)); fail("Foreign response accepted") }
                catch (error: WorkspaceFailure) { assertEquals(if (failure == "rejected") "InvalidInput" else "Malformed", error.category) }
            }
            assertEquals(6, calls.size)
            assertTrue(calls.all { it.getString("op") == "story_presentation" })
        } finally { gateway.close(); gateway.close() }
        assertEquals(1, closes)
    }
}

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

/** Strict Android wire/adapter/probe checks; native setup authority is tested separately. */
@RunWith(AndroidJUnit4::class)
class StoryPlayerSetupWireTest {
    private fun original(name: String = "Rowan") = JSONObject().put("version", 1).put("template", DEFAULT_STORY_TEMPLATE)
        .put("template_sha256", "a".repeat(64)).put("setup_sha256", "b".repeat(64)).put("player_name", name)
        .put("default_title", "Lantern Quay").put("description", "Original bounded starter.").put("profile", "fantasy_v1")
        .put("details", JSONArray().put("Player: $name").put("Original visible fact."))
    private fun refused(category: String = "Malformed", block: () -> Unit) {
        try { block(); fail("Invalid setup wire accepted") }
        catch (failure: WorkspaceFailure) { assertEquals(category, failure.category) }
    }

    @Test fun configuredPreviewRequiresExactHashesNameAndClosedFields() {
        val keys = setOf("version", "template", "template_sha256", "setup_sha256", "default_title",
            "description", "profile", "player_name", "details")
        assertEquals(keys, original().keys().asSequence().toSet())
        val wave = String(Character.toChars(0x1f30a))
        for (name in listOf("Rowan", "e\u0301", "\u00e9", "n".repeat(64), wave.repeat(64))) {
            val data = original(name)
            val result = StoryCreationWire.setupPreview(data)
            val setup = result.playerSetup!!
            assertEquals(name, setup.playerName)
            assertEquals("a".repeat(64), result.seedSha256)
            assertEquals("a".repeat(64), setup.templateSha256)
            assertEquals("b".repeat(64), setup.setupSha256)
            data.getJSONArray("details").put(0, "Changed source detail")
            assertEquals("Player: $name", result.details[0])
            try { (result.details as MutableList<String>).clear(); fail("Mutable preview") }
            catch (_: UnsupportedOperationException) {}
        }
        for (key in keys) {
            refused { StoryCreationWire.setupPreview(original().also { it.remove(key) }) }
            refused { StoryCreationWire.setupPreview(original().put(key, JSONObject.NULL)) }
        }
        for (key in listOf("template_sha256", "setup_sha256")) for (bad in listOf("A".repeat(64), "a".repeat(63), "g".repeat(64))) {
            refused { StoryCreationWire.setupPreview(original().put(key, bad)) }
        }
        for (bad in listOf("", " outer", "outer ", "line\nbreak", "x\u202e", "x\u2067", "\uD800", "\uDC00",
            "n".repeat(65), wave.repeat(65))) refused { StoryCreationWire.setupPreview(original(bad)) }
        for (version in listOf<Any>(1.0, true, "1", 2)) refused { StoryCreationWire.setupPreview(original().put("version", version)) }
        refused { StoryCreationWire.setupPreview(original().put("seed_sha256", "a".repeat(64))) }
        refused { StoryCreationWire.setupPreview(original().put("profile", "narrative_v1")) }
        refused { StoryCreationWire.setupPreview(original().put("template", "foreign")) }
        refused { StoryCreationWire.setupPreview(original().put("details", JSONArray())) }
        refused { StoryCreationWire.setupPreview(original().put("details", JSONArray().put("x".repeat(2049)))) }
        refused { StoryCreationWire.setupPreview(original().put("details", JSONArray().also { rows -> repeat(65) { rows.put("row") } })) }
        refused { StoryCreationWire.setupPreview(original().put("description", "x".repeat(16384))) }
    }

    @Test fun configuredCommandsRemainDistinctFromLegacyNamedCreation() {
        val preview = StoryCreationWire.setupPreview(original("Marin"))
        val request = StoryCreationRequest(preview, "My original title", "c".repeat(32))
        val configured = StoryCreationWire.command(request)
        assertEquals(setOf("op", "template", "template_sha256", "setup_sha256", "player_name", "title", "creation_id"),
            configured.keys().asSequence().toSet())
        assertEquals("create_configured", configured.getString("op"))
        assertEquals("Marin", configured.getString("player_name"))
        assertEquals("a".repeat(64), configured.getString("template_sha256"))
        assertEquals("b".repeat(64), configured.getString("setup_sha256"))
        val legacy = StoryCreationWire.command(request.copy(preview = preview.copy(playerSetup = null)))
        assertEquals(setOf("op", "template", "seed_sha256", "title", "creation_id"), legacy.keys().asSequence().toSet())
        assertEquals("create_named", legacy.getString("op"))
        refused("InvalidInput") { StoryCreationWire.command(request.copy(preview = preview.copy(
            playerSetup = preview.playerSetup!!.copy(playerName = " invalid")))) }
        refused { StoryCreationWire.command(request.copy(preview = preview.copy(
            playerSetup = preview.playerSetup!!.copy(templateSha256 = "d".repeat(64))))) }
        refused { StoryCreationWire.command(request.copy(preview = preview.copy(
            playerSetup = preview.playerSetup!!.copy(setupSha256 = "bad")))) }

        // Actual opt-in probe files: the new read is metadata; configured creation
        // contributes to the existing named-creation semantic counter only.
        val context = InstrumentationRegistry.getInstrumentation().targetContext
        assertTrue(BuildConfig.INPUT_PROCESS_VERIFICATION)
        assertEquals("org.locallore.app.draftprocessverify", context.packageName)
        val run = "cb92da7130f486e5"
        val directory = File(context.noBackupFilesDir, "process-verify-v1/$run")
        ProcessVerificationProbe.configure(context, run, 53, false)
        try {
            ProcessVerificationProbe.created(null)
            ProcessVerificationProbe.operation("workspace")
            ProcessVerificationProbe.saved(null)
            val files = listOf("created.json", "commands.json", "saved.json").map { File(directory, it) }
            val before = files.map { it.readBytes() }
            ProcessVerificationProbe.operation("story_setup")
            files.zip(before).forEach { (file, bytes) -> assertArrayEquals(bytes, file.readBytes()) }
            val original = JSONObject(before[1].toString(Charsets.UTF_8)).getJSONObject("operations")
            ProcessVerificationProbe.operation("create_configured")
            val after = JSONObject(files[1].readText(Charsets.UTF_8))
            val counts = after.getJSONObject("operations")
            assertEquals(2, after.getInt("version"))
            assertEquals(original.keys().asSequence().toSet(), counts.keys().asSequence().toSet())
            assertEquals(14, counts.length())
            for (key in original.keys()) assertEquals(original.getInt(key) + if (key == "create_named") 1 else 0, counts.getInt(key))
            assertFalse(counts.has("create_configured")); assertFalse(counts.has("story_setup"))
            assertArrayEquals(before[0], files[0].readBytes()); assertArrayEquals(before[2], files[2].readBytes())
        } finally { ProcessVerificationProbe.configure(context, null, 53, false) }
    }

    @Test fun nativeGatewayNeverFallsBackOnConfiguredPreviewFailure() = runBlocking {
        val calls = mutableListOf<JSONObject>()
        var mode = "ok"
        val transport = object : WorkspaceTransport {
            override suspend fun exchange(command: JSONObject): JSONObject {
                calls += JSONObject(command.toString())
                assertEquals("story_setup", command.getString("op"))
                assertEquals(setOf("op", "template", "player_name"), command.keys().asSequence().toSet())
                if (mode == "rejected") return JSONObject().put("version", 1).put("status", "rejected").put("error", "InvalidInput")
                val requested = if (command.isNull("player_name")) "Rowan" else command.getString("player_name")
                val data = original(if (mode == "foreign") "Foreign" else requested)
                if (mode == "malformed") data.put("setup_sha256", true)
                return JSONObject().put("version", 1).put("status", "ok").put("data", data)
            }
            override fun close() {}
        }
        val gateway = DurableGateway(transport, autoCreateIfEmpty = false)
        try {
            assertEquals("Rowan", gateway.setupPreview(DEFAULT_STORY_TEMPLATE, null).playerSetup!!.playerName)
            val literal = "Marin e\u0301"
            assertEquals(literal, gateway.setupPreview(DEFAULT_STORY_TEMPLATE, literal).playerSetup!!.playerName)
            assertEquals(literal, calls.last().getString("player_name"))
            for (failure in listOf("foreign", "malformed", "rejected")) {
                mode = failure
                try { gateway.setupPreview(DEFAULT_STORY_TEMPLATE, literal); fail("Native error fell back") }
                catch (error: WorkspaceFailure) { assertEquals(if (failure == "rejected") "InvalidInput" else "Malformed", error.category) }
            }
            assertEquals(5, calls.size)
            assertTrue(calls.all { it.getString("op") == "story_setup" })
        } finally { gateway.close() }
    }
}

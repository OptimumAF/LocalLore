/* Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0 */
package org.locallore.app

import androidx.test.ext.junit.runners.AndroidJUnit4
import kotlinx.coroutines.runBlocking
import org.json.JSONArray
import org.json.JSONObject
import org.junit.Assert.*
import org.junit.Test
import org.junit.runner.RunWith

/** Android wire/transport tests; authored for separate execution, not part of the fixed creation19. */
@RunWith(AndroidJUnit4::class)
class StoryTemplateChoiceWireTest {
    private fun row(template: String = DEFAULT_STORY_TEMPLATE, profile: String = "fantasy_v1") =
        JSONObject().put("template", template).put("default_title", if (template == DEFAULT_STORY_TEMPLATE) "Lantern Quay" else "Bracken Harbor")
            .put("description", "Original starter description.").put("profile", profile)
    private fun catalog() = JSONObject().put("version", 1).put("templates",
        JSONArray().put(row()).put(row("bracken-harbor-v1", "narrative_v1")))
    private fun preview(option: JSONObject) = JSONObject(option.toString()).put("version", 1)
        .put("seed_sha256", "a".repeat(64)).put("details", JSONArray().put("Original player-visible fact."))
    private fun refused(block: () -> Unit) {
        try { block(); fail("Malformed catalog accepted") }
        catch (error: WorkspaceFailure) { assertEquals("Malformed", error.category) }
    }

    @Test fun catalogIsClosedTypedUniqueBoundedAndImmutable() {
        val source = catalog()
        val decoded = StoryCreationWire.templates(source)
        assertEquals(listOf(DEFAULT_STORY_TEMPLATE, "bracken-harbor-v1"), decoded.map { it.template })
        assertEquals(listOf("fantasy_v1", "narrative_v1"), decoded.map { it.profile })
        source.getJSONArray("templates").getJSONObject(0).put("default_title", "Changed input")
        assertEquals("Lantern Quay", decoded.first().defaultTitle)
        try { (decoded as MutableList<StoryTemplateOption>).clear(); fail("Mutable catalog") }
        catch (_: UnsupportedOperationException) {}
        for (version in listOf<Any>(true, "1", 1.0, 2, JSONObject.NULL)) refused {
            StoryCreationWire.templates(catalog().put("version", version))
        }
        refused { StoryCreationWire.templates(catalog().put("private", "unrequested")) }
        refused { StoryCreationWire.templates(catalog().also { it.remove("version") }) }
        for (rows in listOf(JSONArray(), JSONArray().put(row()).put(row()), JSONArray().put("not an object"),
            JSONArray().put(row("bracken-harbor-v1", "narrative_v1")),
            JSONArray().put(row()).put(row("unknown", "narrative_v1")),
            JSONArray().put(row()).put(row("bracken-harbor-v1", "fantasy_v1")),
            JSONArray().also { repeat(9) { _ -> it.put(row()) } })) {
            refused { StoryCreationWire.templates(catalog().put("templates", rows)) }
        }
        for (key in listOf("template", "default_title", "description", "profile")) {
            refused { StoryCreationWire.templates(catalog().put("templates", JSONArray().put(row().also { it.remove(key) }))) }
            refused { StoryCreationWire.templates(catalog().put("templates", JSONArray().put(row().put(key, true)))) }
        }
        refused { StoryCreationWire.templates(catalog().put("templates", JSONArray().put(row().put("details", JSONArray())))) }
        refused { StoryCreationWire.templates(catalog().put("templates", JSONArray().put(row().put("description", "x".repeat(2049))))) }
        refused { StoryCreationWire.templates(catalog().put("templates", JSONArray().put(row().put("default_title", " outer")))) }
    }

    @Test fun selectedNarrativePreviewAndCommandPreserveItsOwnTemplateAndHash() {
        val source = preview(row("bracken-harbor-v1", "narrative_v1"))
        val decoded = StoryCreationWire.preview(source)
        assertEquals("narrative_v1", decoded.profile)
        val request = StoryCreationRequest(decoded, "My Harbor", "b".repeat(32))
        val command = StoryCreationWire.command(request)
        assertEquals(setOf("op", "template", "seed_sha256", "title", "creation_id"), command.keys().asSequence().toSet())
        assertEquals("bracken-harbor-v1", command.getString("template"))
        assertEquals("a".repeat(64), command.getString("seed_sha256"))
        refused { StoryCreationWire.preview(source.put("profile", "fantasy_v1")) }
        refused { StoryCreationWire.command(request.copy(preview = decoded.copy(profile = "fantasy_v1"))) }
    }

    @Test fun productionGatewayRequestsNativeCatalogAndSelectedPreviewWithoutCreatingOrFallingBack() = runBlocking {
        val calls = mutableListOf<JSONObject>()
        var malformed = false
        val transport = object : WorkspaceTransport {
            override suspend fun exchange(command: JSONObject): JSONObject {
                calls += JSONObject(command.toString())
                val data = when (command.getString("op")) {
                    "story_templates" -> if (malformed) catalog().put("templates", JSONArray()) else catalog()
                    "story_template" -> preview(row(command.getString("template"), "narrative_v1"))
                    else -> error("Unexpected mutation or session operation")
                }
                return JSONObject().put("version", 1).put("status", "ok").put("data", data)
            }
            override fun close() {}
        }
        val gateway = DurableGateway(transport, autoCreateIfEmpty = false)
        assertEquals(2, gateway.templates().size)
        assertEquals("bracken-harbor-v1", gateway.previewTemplate("bracken-harbor-v1").template)
        assertEquals(setOf("op"), calls[0].keys().asSequence().toSet())
        assertEquals(setOf("op", "template"), calls[1].keys().asSequence().toSet())
        malformed = true
        try { gateway.templates(); fail("Malformed native catalog fell back") }
        catch (error: WorkspaceFailure) { assertEquals("Malformed", error.category) }
        assertEquals(listOf("story_templates", "story_template", "story_templates"), calls.map { it.getString("op") })
    }
}

/* Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0 */
package org.locallore.app

import java.util.Collections
import org.json.JSONArray
import org.json.JSONObject

/** Closed metadata only. The engine owns the starter, title validation and transaction. */
internal object StoryCreationWire {
    private val hash = Regex("[0-9a-f]{64}")
    private val creationId = Regex("[0-9a-f]{32}")
    fun templates(data: JSONObject): List<StoryTemplateOption> = try {
        check(data.toString().toByteArray(Charsets.UTF_8).size <= 16384)
        fields(data, setOf("version", "templates"))
        version(data)
        val rows = data.get("templates") as JSONArray
        check(rows.length() in 1..8)
        val options = (0 until rows.length()).map { index ->
            val row = rows.get(index) as JSONObject
            fields(row, setOf("template", "default_title", "description", "profile"))
            val template = row.get("template") as String
            val profile = row.get("profile") as String
            check(validStoryTemplateProfile(template, profile))
            val title = row.get("default_title") as String
            check(validStoryTitle(title))
            val description = row.get("description") as String
            check(description.isNotEmpty() && description.toByteArray(Charsets.UTF_8).size <= 2048)
            StoryTemplateOption(template, title, description, profile)
        }
        check(options.map { it.template }.toSet().size == options.size)
        check(options.first().template == DEFAULT_STORY_TEMPLATE)
        Collections.unmodifiableList(options)
    } catch (_: Exception) { throw WorkspaceFailure("Malformed") }

    fun preview(data: JSONObject): StoryCreationPreview = try {
        check(data.toString().toByteArray(Charsets.UTF_8).size <= 16384)
        fields(data, setOf("version", "template", "seed_sha256", "default_title", "description", "profile", "details"))
        version(data)
        val template = data.get("template") as String
        val profile = data.get("profile") as String
        check(validStoryTemplateProfile(template, profile))
        val sha = data.get("seed_sha256") as String
        check(hash.matches(sha))
        val title = data.get("default_title") as String
        check(validStoryTitle(title))
        val description = data.get("description") as String
        check(description.isNotEmpty() && description.toByteArray(Charsets.UTF_8).size <= 2048)
        val rows = data.get("details") as JSONArray
        check(rows.length() in 1..64)
        val details = (0 until rows.length()).map { index ->
            (rows.get(index) as String).also { check(it.isNotEmpty() && it.toByteArray(Charsets.UTF_8).size <= 2048) }
        }
        StoryCreationPreview(template, sha, title, description, profile, Collections.unmodifiableList(details))
    } catch (_: Exception) { throw WorkspaceFailure("Malformed") }

    fun command(request: StoryCreationRequest): JSONObject {
        if (!validStoryTitle(request.title)) throw WorkspaceFailure("InvalidTitle")
        if (!validStoryTemplateProfile(request.preview.template, request.preview.profile) || !hash.matches(request.preview.seedSha256) ||
            !creationId.matches(request.creationId)) throw WorkspaceFailure("Malformed")
        val setup = request.preview.playerSetup
        if (setup == null && request.preview.presentation != null) throw WorkspaceFailure("Malformed")
        if (setup == null) return JSONObject().put("op", "create_named").put("template", request.preview.template)
            .put("seed_sha256", request.preview.seedSha256).put("title", request.title).put("creation_id", request.creationId)
        if (!validStoryPlayerName(setup.playerName)) throw WorkspaceFailure("InvalidInput")
        if (!hash.matches(setup.templateSha256) || !hash.matches(setup.setupSha256) ||
            setup.templateSha256 != request.preview.seedSha256) throw WorkspaceFailure("Malformed")
        request.preview.presentation?.let { settings ->
            return JSONObject().put("op", "create_presented").put("template", request.preview.template)
                .put("template_sha256", setup.templateSha256).put("setup_sha256", setup.setupSha256)
                .put("player_name", setup.playerName).put("presentation", presentation(settings))
                .put("title", request.title).put("creation_id", request.creationId)
        }
        return JSONObject().put("op", "create_configured").put("template", request.preview.template)
            .put("template_sha256", setup.templateSha256).put("setup_sha256", setup.setupSha256)
            .put("player_name", setup.playerName).put("title", request.title).put("creation_id", request.creationId)
    }
    fun setupPreview(data: JSONObject): StoryCreationPreview = try {
        check(data.toString().toByteArray(Charsets.UTF_8).size <= 16384)
        fields(data, setOf("version", "template", "template_sha256", "setup_sha256", "default_title",
            "description", "profile", "player_name", "details"))
        val templateHash = data.get("template_sha256") as String
        val setupHash = data.get("setup_sha256") as String
        val name = data.get("player_name") as String
        check(hash.matches(templateHash) && hash.matches(setupHash) && validStoryPlayerName(name))
        // Reuse the closed, bounded old metadata decoder without changing its seven-key wire.
        val metadata = JSONObject().put("version", data.get("version")).put("template", data.get("template"))
            .put("seed_sha256", templateHash).put("default_title", data.get("default_title"))
            .put("description", data.get("description")).put("profile", data.get("profile")).put("details", data.get("details"))
        preview(metadata).copy(playerSetup = StoryPlayerSetup(templateHash, setupHash, name))
    } catch (_: Exception) { throw WorkspaceFailure("Malformed") }
    fun presentationPreview(data: JSONObject): StoryCreationPreview = try {
        check(data.toString().toByteArray(Charsets.UTF_8).size <= 16384)
        fields(data, setOf("version", "template", "template_sha256", "setup_sha256", "default_title",
            "description", "profile", "player_name", "presentation", "details"))
        val settings = data.get("presentation") as JSONObject
        fields(settings, setOf("version", "tone", "excluded_phrases"))
        version(settings)
        val rows = settings.get("excluded_phrases") as JSONArray
        check(rows.length() <= 8)
        val phrases = (0 until rows.length()).map { rows.get(it) as String }
        val presentation = StoryPresentation(settings.get("tone") as String, Collections.unmodifiableList(phrases))
        check(validStoryPresentation(presentation))
        val setup = JSONObject()
        for (key in data.keys()) if (key != "presentation") setup.put(key, data.get(key))
        setupPreview(setup).copy(presentation = presentation)
    } catch (_: Exception) { throw WorkspaceFailure("Malformed") }

    fun presentation(value: StoryPresentation): JSONObject {
        if (!validStoryPresentation(value)) throw WorkspaceFailure("InvalidInput")
        return JSONObject().put("version", 1).put("tone", value.tone).put("excluded_phrases", JSONArray(value.excludedPhrases))
    }
    private fun version(data: JSONObject) {
        val version = data.get("version")
        check((version is Int || version is Long) && (version as Number).toLong() == 1L)
    }
    private fun fields(data: JSONObject, expected: Set<String>) {
        check(data.keys().asSequence().toSet() == expected)
    }
}

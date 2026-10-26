/* Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0 */
package org.locallore.app

import java.util.Collections
import org.json.JSONArray
import org.json.JSONObject

/** Closed metadata only. The engine owns the starter, title validation and transaction. */
internal object StoryCreationWire {
    private const val TEMPLATE = "lantern-quay-v1"
    private val hash = Regex("[0-9a-f]{64}")
    private val creationId = Regex("[0-9a-f]{32}")
    fun preview(data: JSONObject): StoryCreationPreview = try {
        check(data.toString().toByteArray(Charsets.UTF_8).size <= 16384)
        fields(data, setOf("version", "template", "seed_sha256", "default_title", "description", "profile", "details"))
        val version = data.get("version")
        check((version is Int || version is Long) && (version as Number).toLong() == 1L)
        check(data.get("template") == TEMPLATE && data.get("profile") == "fantasy_v1")
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
        StoryCreationPreview(TEMPLATE, sha, title, description, "fantasy_v1", Collections.unmodifiableList(details))
    } catch (_: Exception) { throw WorkspaceFailure("Malformed") }

    fun command(request: StoryCreationRequest): JSONObject {
        if (!validStoryTitle(request.title)) throw WorkspaceFailure("InvalidTitle")
        if (request.preview.template != TEMPLATE || !hash.matches(request.preview.seedSha256) ||
            !creationId.matches(request.creationId)) throw WorkspaceFailure("Malformed")
        return JSONObject().put("op", "create_named").put("template", TEMPLATE)
            .put("seed_sha256", request.preview.seedSha256).put("title", request.title).put("creation_id", request.creationId)
    }
    private fun fields(data: JSONObject, expected: Set<String>) {
        check(data.keys().asSequence().toSet() == expected)
    }
}

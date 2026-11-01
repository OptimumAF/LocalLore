/* Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0 */
package org.locallore.app

import java.util.Collections
import org.json.JSONArray
import org.json.JSONObject

/** Presentation only. Native accepted history owns intent, eligibility and ancestor lineage. */
internal data class PlayerPresentation(
    val domainVersion: Int,
    val scope: PlayDraftScope,
    val revision: Long,
    val observer: String,
    val rules: String,
    val hasPotion: Boolean,
    val messages: List<SceneMessage>,
)

internal object PlayerPresentationWire {
    private val identifier = Regex("[A-Za-z0-9_-]{1,64}")
    private const val MAX_BYTES = 65536

    fun command(session: String, scope: PlayDraftScope, revision: Long): JSONObject {
        require(localUtf8(session).size in 1..128 && revision >= 0)
        require(identifier.matches(scope.story) && identifier.matches(scope.branch))
        return JSONObject().put("op", "play_presentation_v2").put("session", session)
            .put("scope", JSONObject().put("story", scope.story).put("branch", scope.branch))
            .put("expected_revision", revision)
    }

    fun decode(data: JSONObject, expectedScope: PlayDraftScope, expectedRevision: Long): PlayerPresentation = try {
        require(expectedRevision >= 0 && localUtf8(data.toString()).size <= MAX_BYTES)
        data.fields("version", "domain_version", "scope", "revision", "rules", "player", "inventory", "turns", "window")
        require(data.integer("version") == 2L)
        val domain = data.integer("domain_version").also { require(it in 1..2) }.toInt()
        val selectedScope = scope(data.getJSONObject("scope"))
        require(selectedScope == expectedScope && data.integer("revision") == expectedRevision)
        val rules = data.text("rules").also { require(it in setOf("fantasy_v1", "narrative_v1")) }
        val player = data.getJSONObject("player").also { it.fields("observer", "self_state") }
        val observer = player.id("observer")
        actor(player.getJSONObject("self_state"))
        val inventory = data.getJSONObject("inventory")
        for (key in inventory.keys().asSequence()) {
            require(identifier.matches(key))
            val item = inventory.getJSONObject(key).also { it.fields("owner", "quantity", "return_to", "healing") }
            require(item.id("owner") == observer)
            item.unsigned16("quantity")
            if (!item.isNull("return_to")) item.id("return_to")
            item.boolean("healing")
        }
        val window = data.getJSONObject("window").also { it.fields("total", "start", "end") }
        val total = window.integer("total").also { require(it in 0..4096) }
        val start = window.integer("start")
        require(window.integer("end") == total && start == maxOf(0, total - 20))
        val turns = data.getJSONArray("turns")
        require(turns.length().toLong() == total - start)
        val messages = mutableListOf<SceneMessage>()
        val identities = mutableSetOf<Pair<PlayDraftScope, String>>()
        val allEvents = mutableSetOf<Long>()
        var previous = 0L
        for (index in 0 until turns.length()) {
            val turn = turns.getJSONObject(index).also { it.fields("original_scope", "turn", "event_ids", "intent", "narration") }
            val original = scope(turn.getJSONObject("original_scope"))
            require(original.story == selectedScope.story)
            require(identities.add(original to turn.id("turn")))
            val events = turn.getJSONArray("event_ids")
            require(events.length() > 0)
            for (i in 0 until events.length()) {
                val sequence = integer(events.get(i))
                require(sequence in 1..expectedRevision && sequence > previous && allEvents.add(sequence))
                previous = sequence
            }
            val text = intent(turn.getJSONObject("intent"))
            val narration = turn.text("narration")
            val ordinal = start + index
            messages += SceneMessage(ordinal * 2 + 1, text, true)
            messages += SceneMessage(ordinal * 2 + 2, narration, false)
        }
        PlayerPresentation(domain, selectedScope, expectedRevision, observer, rules, inventory.has("potion"),
            Collections.unmodifiableList(ArrayList(messages)))
    } catch (failure: WorkspaceFailure) { throw failure }
    catch (_: Exception) { throw WorkspaceFailure("Malformed") }

    private fun actor(value: JSONObject) {
        value.fields("name", "location", "alive", "energy", "abilities", "attributes", "injuries", "affiliations", "goals")
        value.text("name"); value.text("location"); value.boolean("alive"); value.unsigned16("energy")
        val abilities = value.getJSONObject("abilities")
        for (key in abilities.keys().asSequence()) {
            require(identifier.matches(key)); abilities.unsigned16(key)
        }
        val attributes = value.getJSONObject("attributes")
        for (key in attributes.keys().asSequence()) {
            localUtf8(key)
            require(attributes.integer(key) in -32768..32767)
        }
        for (key in listOf("injuries", "affiliations", "goals")) strings(value.getJSONArray(key), ids = false)
    }

    private fun intent(value: JSONObject): String {
        value.fields("kind", "value")
        return when (value.text("kind")) {
            "actions" -> value.getJSONArray("value").also { actions ->
                require(actions.length() in 1..8)
                for (i in 0 until actions.length()) action(actions.getJSONObject(i))
            }.toString()
            "dialogue" -> value.getJSONObject("value").let {
                it.fields("text", "audience"); strings(it.getJSONArray("audience"), ids = true)
                it.text("text", 2048)
            }
            "free_text" -> value.getJSONObject("value").let {
                it.fields("kind", "text"); require(it.text("kind") in setOf("action", "dialogue"))
                it.text("text", 2048)
            }
            else -> error("Unknown accepted intent")
        }
    }

    /** Closed existing Command shapes; no availability, cost or world-state rules are executed. */
    private fun action(value: JSONObject) {
        when (value.text("op")) {
            "give" -> { value.fields("op", "item", "to", "quantity"); value.id("item"); value.id("to"); value.unsigned16("quantity") }
            "consume" -> { value.fields("op", "item"); value.id("item") }
            "use_ability", "learn" -> { value.fields("op", "ability"); value.id("ability") }
            "move" -> { value.fields("op", "to"); value.text("to") }
            "say" -> { value.fields("op", "text", "audience"); value.text("text", 2048); strings(value.getJSONArray("audience"), ids = true) }
            "believe" -> { value.fields("op", "claim_event"); require(value.integer("claim_event") > 0) }
            "discover" -> { value.fields("op", "fact"); value.id("fact") }
            "promise" -> {
                value.fields("op", "id", "to", "terms", "deadline", "return_item")
                value.id("id"); value.id("to"); value.text("terms", 2048); require(value.integer("deadline") >= 0)
                if (!value.isNull("return_item")) value.id("return_item")
            }
            "complete_promise" -> { value.fields("op", "id"); value.id("id") }
            "wait" -> { value.fields("op", "ticks"); value.unsigned16("ticks") }
            else -> error("Unknown accepted command")
        }
    }

    private fun scope(value: JSONObject): PlayDraftScope {
        value.fields("story", "branch")
        return PlayDraftScope(value.id("story"), value.id("branch"))
    }
    private fun strings(values: JSONArray, ids: Boolean) {
        val seen = mutableSetOf<String>()
        for (index in 0 until values.length()) {
            val text = values.get(index) as String
            localUtf8(text)
            require(seen.add(text) && (!ids || identifier.matches(text)))
        }
    }
    private fun JSONObject.fields(vararg keys: String) = require(this.keys().asSequence().toSet() == keys.toSet())
    private fun JSONObject.text(key: String, cap: Int = MAX_BYTES): String = (get(key) as String).also {
        require(localUtf8(it).size <= cap)
    }
    private fun JSONObject.id(key: String): String = text(key, 64).also { require(identifier.matches(it)) }
    private fun JSONObject.boolean(key: String) = get(key) as Boolean
    private fun JSONObject.integer(key: String) = integer(get(key))
    private fun JSONObject.unsigned16(key: String) = integer(key).also { require(it in 0..65535) }
    private fun integer(value: Any): Long {
        require(value is Int || value is Long)
        return (value as Number).toLong()
    }
}

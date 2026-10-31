/* Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0 */
package org.locallore.app

import org.json.JSONArray
import org.json.JSONObject

/** A fixed player lens over Host-v1. Unknown variants fail closed instead of becoming UI truth. */
internal object StoryRecordWire {
    fun command(session: String, query: StoryRecordQuery): JSONObject {
        if (!validStoryRecordSearch(query.search)) throw StoryRecordFailure(StoryRecordProblem.BAD_SEARCH)
        if (!validVersion(query)) throw StoryRecordFailure(StoryRecordProblem.INVALID_RESPONSE)
        if (query.version == 2 && query.cursor != null && !cursorPattern(query).matches(query.cursor))
            throw StoryRecordFailure(StoryRecordProblem.INVALID_RESPONSE)
        return JSONObject().put("op", "inspection_query").put("session", session).put("query",
            JSONObject().put("version", query.version).put("scope", JSONObject().put("story", query.context.story.story)
                .put("branch", query.context.story.branch)).put("expected_head", query.context.revision)
                .put("at_revision", JSONObject.NULL).put("observer", JSONObject().put("kind", "player"))
                .put("view", query.section.wire).put("limit", STORY_RECORD_PAGE_ROWS)
                .put("search", query.search).put("cursor", query.cursor ?: JSONObject.NULL))
    }

    fun decode(data: JSONObject, query: StoryRecordQuery): StoryRecordPage = try {
        if (data.toString().toByteArray(Charsets.UTF_8).size > 65536)
            throw StoryRecordFailure(StoryRecordProblem.TOO_LARGE)
        require(validVersion(query) && data.get("version") == query.version)
        val scope = data.getJSONObject("scope")
        require(scope.text("story") == query.context.story.story && scope.text("branch") == query.context.story.branch)
        require(data.number("head") == query.context.revision && data.number("revision") == query.context.revision)
        val observer = data.getJSONObject("observer")
        require(observer.length() == 1 && observer.text("kind") == "player")
        require(data.text("privacy") == "player_visible" && data.text("status") == "supported")
        require(data.text("view") == query.section.wire)
        val total = data.number("total").also { require(it in 0..65536) }.toInt()
        val time = data.number("story_time").also { require(it >= 0) }
        val rows = data.getJSONArray("rows")
        require(rows.length() <= STORY_RECORD_PAGE_ROWS && rows.length() <= total)
        val entries = (0 until rows.length()).map { row(rows.getJSONObject(it), query, time) }
        require(data.has("next_cursor"))
        require(entries.map { it.key }.toSet().size == entries.size)
        val eventIds = entries.mapNotNull { it.event?.sequence }
        require(eventIds.toSet().size == eventIds.size)
        val next = if (data.isNull("next_cursor")) null else data.text("next_cursor", 128).also {
            require(it.isNotEmpty() && it != query.cursor && it.all { ch -> ch.code in 33..126 })
            require(entries.isNotEmpty() && total > entries.size)
            require(cursorPattern(query).matches(it))
            val offset = it.split(':')[1].toInt()
            require(offset < total && offset >= entries.size)
        }
        val offset = query.cursor?.let {
            require(cursorPattern(query).matches(it))
            it.split(':')[1].toInt()
        } ?: 0
        require(offset <= total)
        if (next == null) require(offset + entries.size == total)
        else require(next.split(':')[1].toInt() == offset + entries.size)
        val unsupported = data.getJSONArray("unsupported")
        require(unsupported.length() <= 8)
        for (i in 0 until unsupported.length()) require(unsupported.get(i) is String && unsupported.getString(i).length <= 1024)
        StoryRecordPage(query, time, total, entries, next,
            if (unsupported.length() == 0) emptyList() else listOf("Only fields supported by the current story engine are shown."))
    } catch (failure: StoryRecordFailure) { throw failure }
    catch (_: Exception) { throw StoryRecordFailure(StoryRecordProblem.INVALID_RESPONSE) }

    private fun row(row: JSONObject, query: StoryRecordQuery, storyTime: Long): StoryRecordEntry {
        val key = row.text("key", 512)
        require(key.isNotEmpty())
        val origin = StoryRecordOrigin.entries.single { it.wire == row.text("origin") }
        return when (row.text("kind")) {
            "field" -> {
                require(query.section == StoryRecordSection.PROGRESSION && origin == StoryRecordOrigin.CANONICAL_FIELD)
                require(row.text("actor") == "player")
                val field = row.text("field", 512)
                val evidence = row.getJSONObject("source")
                StoryRecordEntry(key, field, fieldValue(row.getJSONObject("value")), origin,
                    listOf(source(evidence, query.context.revision)), listOfNotNull(eventSource(evidence)))
            }
            "relationship" -> {
                require(query.section == StoryRecordSection.RELATIONSHIPS && origin == StoryRecordOrigin.CANONICAL_FIELD)
                require(row.text("from") == "player")
                val dimension = row.text("dimension").also { require(it in setOf("respect", "trust", "obligation")) }
                val value = row.number("value").also { require(it in -32768..32767) }
                val evidence = row.getJSONObject("source")
                StoryRecordEntry(key, "${row.text("to")} · $dimension", value.toString(), origin,
                    listOf(source(evidence, query.context.revision)), listOfNotNull(eventSource(evidence)))
            }
            "knowledge" -> {
                require(query.section == StoryRecordSection.KNOWLEDGE)
                require(origin in setOf(StoryRecordOrigin.CANONICAL_TRUTH, StoryRecordOrigin.RECORDED_STATEMENT,
                    StoryRecordOrigin.SUBJECTIVE_BELIEF, StoryRecordOrigin.RECORDED_DISCOVERY))
                require(row.has("subject") && row.has("confidence"))
                val subject = if (row.isNull("subject")) null else row.text("subject", 512)
                val confidence = if (row.isNull("confidence")) null else row.text("confidence")
                when (origin) {
                    StoryRecordOrigin.SUBJECTIVE_BELIEF -> require(subject == "player" && confidence in setOf("uncertain", "suspected", "believed"))
                    StoryRecordOrigin.CANONICAL_TRUTH -> require(subject == null && confidence == null)
                    else -> require(subject != null && confidence == null)
                }
                val sources = row.getJSONArray("sources").also { require(it.length() in 1..64) }
                val evidence = (0 until sources.length()).map { sources.getJSONObject(it) }
                StoryRecordEntry(key, listOfNotNull(row.text("id", 512), subject, confidence).joinToString(" · "),
                    row.text("text"), origin, evidence.map { source(it, query.context.revision) },
                    evidence.mapNotNull(::eventSource).distinct())
            }
            "promise" -> {
                require(query.section == StoryRecordSection.PROMISES && query.version == 2 &&
                    origin == StoryRecordOrigin.DERIVED_COMPARISON)
                val id = row.text("id", 512)
                val from = row.text("from", 512)
                val to = row.text("to", 512)
                require(from == "player" || to == "player")
                val deadline = row.number("deadline").also { require(it >= 0) }
                val status = when (row.text("status")) {
                    "open" -> "Open"
                    "overdue" -> "Overdue"
                    "fulfilled" -> "Fulfilled"
                    else -> error("Unknown promise status")
                }
                require(row.has("return_item"))
                val item = if (row.isNull("return_item")) null else row.text("return_item", 512)
                val evidence = row.getJSONArray("sources").also { require(it.length() in 1..64) }
                val sources = (0 until evidence.length()).map { evidence.getJSONObject(it) }
                val labels = sources.map { scopedSourceLabel(it, query) }
                val references = sources.mapNotNull { scopedEventSource(it, query) }.distinct()
                StoryRecordEntry(key, "Promise · $id",
                    "From · $from\nTo · $to\nStatus · $status\nDue at story time · $deadline\n${row.text("terms")}" +
                        (item?.let { "\nReturn item · $it" } ?: ""),
                    origin, labels, scopedEventSources = references)
            }
            "message" -> {
                require(query.version == 1)
                require(query.section == StoryRecordSection.HISTORY && origin == StoryRecordOrigin.RECORDED_MESSAGE)
                val kind = row.text("message_kind").also { require(it in setOf("original_input", "narration")) }
                val ids = row.getJSONArray("event_ids").also { require(it.length() <= 64) }
                require(validStoryRecordTurn(row.text("turn", 64)))
                val eventIds = (0 until ids.length()).map { ids.integer(it).also { id -> require(id <= query.context.revision) } }
                require(eventIds.isNotEmpty() && eventIds.toSet().size == eventIds.size)
                StoryRecordEntry(key, if (kind == "original_input") "Recorded player input" else "Recorded narration",
                    row.text("text"), origin, eventIds.map { "Event #$it" }, eventIds)
            }
            "event" -> {
                require(query.section == StoryRecordSection.HISTORY && origin == StoryRecordOrigin.RECORDED_OBSERVATION)
                val event = row.getJSONObject("event")
                val scope = event.getJSONObject("scope")
                val originalScope = if (query.version == 2) readScope(scope, query) else null
                if (query.version == 1)
                    require(scope.text("story") == query.context.story.story && scope.text("branch") == query.context.story.branch)
                val sequence = event.number("sequence").also { require(it in 1..query.context.revision) }
                require(event.number("story_time") in 0..storyTime)
                val witnesses = event.getJSONArray("witnesses")
                require(strings(witnesses).contains("player"))
                strings(event.getJSONArray("participants"))
                val turn = event.text("turn", 64).also { require(validStoryRecordTurn(it)) }
                val reference = originalScope?.let { StoryRecordScopedEvent(it, sequence) }
                StoryRecordEntry(key, "Event #$sequence", effect(event.getJSONObject("consequence"), query.context.revision),
                    origin, listOf(reference?.let(::scopedEventLabel) ?: "Event #$sequence"),
                    if (reference == null) listOf(sequence) else emptyList(),
                    StoryRecordEvent(sequence, turn, event.number("story_time"), originalScope),
                    reference?.let { listOf(it) } ?: emptyList())
            }
            else -> error("Unknown record")
        }
    }

    private fun validVersion(query: StoryRecordQuery) = when (query.version) {
        1 -> query.section != StoryRecordSection.PROMISES
        2 -> query.section == StoryRecordSection.PROMISES || query.section == StoryRecordSection.HISTORY
        else -> false
    }
    private fun cursorPattern(query: StoryRecordQuery) = Regex("${query.version}:[1-9][0-9]{0,4}:[0-9a-f]{64}")
    private fun readScope(scope: JSONObject, query: StoryRecordQuery): StoryRecordScope {
        require(scope.length() == 2 && scope.has("story") && scope.has("branch"))
        val story = scope.text("story", 64)
        val branch = scope.text("branch", 64)
        require(story == query.context.story.story && validStoryRecordTurn(story) && validStoryRecordTurn(branch))
        return StoryRecordScope(story, branch)
    }
    private fun scopedEventSource(value: JSONObject, query: StoryRecordQuery): StoryRecordScopedEvent? {
        if (value.text("kind") != "scoped_event") return null
        require(value.length() == 2 && value.has("kind") && value.has("value"))
        val source = value.getJSONObject("value")
        require(source.length() == 2 && source.has("original_scope") && source.has("sequence"))
        return StoryRecordScopedEvent(readScope(source.getJSONObject("original_scope"), query),
            source.number("sequence").also { require(it in 1..query.context.revision) })
    }
    private fun scopedEventLabel(reference: StoryRecordScopedEvent) =
        "Event #${reference.sequence} · ${reference.originalScope.story} / ${reference.originalScope.branch}"
    private fun scopedSourceLabel(value: JSONObject, query: StoryRecordQuery): String =
        when (value.text("kind")) {
            "seed", "withheld" -> source(value, query.context.revision)
            "scoped_event" -> scopedEventLabel(checkNotNull(scopedEventSource(value, query)))
            else -> error("Unknown scoped source")
        }

    private fun fieldValue(value: JSONObject): String = when (value.text("type")) {
        "text" -> value.text("value")
        "bool" -> (value.get("value") as Boolean).toString()
        "number" -> value.number("value").toString()
        "texts" -> strings(value.getJSONArray("value")).joinToString(", ").ifEmpty { "None recorded" }
        "item" -> value.getJSONObject("value").let {
            val quantity = it.number("quantity").also { n -> require(n in 0..65535) }
            val healing = it.get("healing") as Boolean
            require(it.has("return_to") && it.text("owner", 512) == "player")
            val returnTo = if (it.isNull("return_to")) null else it.text("return_to", 512)
            "Owner: ${it.text("owner", 512)} · Quantity: $quantity · Healing: $healing" +
                (returnTo?.let { actor -> " · Return to: $actor" } ?: "")
        }
        else -> error("Unknown field")
    }

    private fun effect(e: JSONObject, head: Long): String = when (e.text("effect")) {
        "given" -> "${e.text("from")} gave ${e.unsigned16("quantity")} ${e.text("item")} to ${e.text("to")}."
        "consumed" -> "${e.text("actor")} consumed ${e.text("item")}.".also { require(e.has("healed")) } +
            (if (e.isNull("healed")) "" else " Healed: ${e.text("healed")}.")
        "ability_used" -> "${e.text("actor")} used ${e.text("ability")} (cost ${e.unsigned16("cost")})."
        "learned" -> "${e.text("actor")} learned ${e.text("ability")} (rank ${e.unsigned16("rank")})."
        "moved" -> "${e.text("actor")} moved from ${e.text("from")} to ${e.text("to")}."
        "said" -> "${e.text("speaker")} said: ${e.text("text")}".also { strings(e.getJSONArray("audience")); require(e.number("source") in 1..head) }
        "believed" -> "${e.text("believer")} held a belief: ${e.text("proposition")} (${e.text("confidence")}).".also {
            require(e.text("confidence") in setOf("uncertain", "suspected", "believed")); source(e.getJSONObject("source"), head)
            require(e.has("source_claim")); if (!e.isNull("source_claim")) require(e.number("source_claim") in 1..head)
        }
        "discovered" -> "${e.text("actor")} discovered ${e.text("fact")}."
        "promised" -> e.getJSONObject("commitment").let {
            e.text("id", 512)
            require(it.number("deadline") >= 0)
            source(it.getJSONObject("source"), head)
            require(it.has("return_item") && it.has("completed_by"))
            if (!it.isNull("return_item")) it.text("return_item", 512)
            if (!it.isNull("completed_by")) require(it.number("completed_by") in 1..head)
            "${it.text("from")} promised ${it.text("to")}: ${it.text("terms")}"
        }
        "promise_completed" -> "Promise ${e.text("id")} completed (event ${e.number("return_event").also { require(it in 1..head) }})."
        "time_advanced" -> "Story time advanced from ${e.number("from")} to ${e.number("to")}.".also {
            require(e.number("from") >= 0 && e.number("to") > e.number("from"))
        }
        else -> error("Unknown consequence")
    }

    private fun source(source: JSONObject, head: Long): String = when (source.text("kind")) {
        "seed" -> "Seed · ${source.text("value", 512)}"
        "event" -> "Event #${source.number("value").also { require(it in 1..head) }}"
        "withheld" -> "Evidence withheld"
        else -> error("Unknown source")
    }
    // Called only after the corresponding typed source has passed source() validation.
    private fun eventSource(source: JSONObject): Long? =
        if (source.text("kind") == "event") source.number("value") else null
    private fun strings(array: JSONArray): List<String> {
        require(array.length() <= 256)
        return (0 until array.length()).map { (array.get(it) as String).also { s -> require(s.toByteArray(Charsets.UTF_8).size <= 8192) } }
    }
    private fun JSONObject.text(key: String, max: Int = 8192): String = (get(key) as String).also {
        require(it.toByteArray(Charsets.UTF_8).size <= max)
    }
    private fun JSONObject.number(key: String): Long = integral(get(key))
    private fun JSONObject.unsigned16(key: String): Long = number(key).also { require(it in 0..65535) }
    private fun JSONArray.integer(index: Int): Long = integral(get(index)).also { require(it > 0) }
    private fun integral(value: Any): Long {
        require(value is Int || value is Long)
        return (value as Number).toLong()
    }
}

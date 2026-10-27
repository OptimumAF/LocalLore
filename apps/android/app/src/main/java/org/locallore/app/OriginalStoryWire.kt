/* Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0 */
package org.locallore.app

import org.json.JSONArray
import org.json.JSONObject

/** Closed author metadata. No Seed JSON or generation response is accepted from UI code. */
internal object OriginalStoryWire {
    private fun fields(o: JSONObject, vararg names: String) { check(o.keys().asSequence().toSet() == names.toSet()) }
    private fun text(o: JSONObject, key: String) = o.get(key) as? String ?: error("Wire")
    private fun number(o: JSONObject, key: String): Int {
        val n = o.get(key); check(n is Int || n is Long)
        return (n as Number).toLong().also { check(it in 0L..65535L) }.toInt()
    }
    private fun version(o: JSONObject) { check(number(o, "version") == 1) }
    private fun cap(o: JSONObject, max: Int) { check(localUtf8(o.toString()).size <= max) }
    private fun id(value: String): String = value.also { check(Regex("[A-Za-z0-9_-]{1,128}").matches(it)) }
    private fun hash(value: String): String = value.also { check(Regex("[0-9a-f]{64}").matches(it)) }
    private fun provider(value: String): String = value.also { check(it in setOf("scripted", "local")) }
    private fun label(value: String, bytes: Int = 512, scalars: Int = 512, empty: Boolean = false): String = value.also {
        check((empty || it.isNotEmpty()) && it.trim() == it && localUtf8(it).size <= bytes && it.codePointCount(0, it.length) <= scalars)
        check(it.codePoints().noneMatch { c -> Character.isISOControl(c) || c in 0x2028..0x202e || c in 0x2066..0x2069 })
    }
    private fun name(value: String) = label(value, 256, 64)
    private fun <T> rows(o: JSONObject, key: String, min: Int, max: Int, read: (JSONObject) -> T): List<T> {
        val a = o.get(key) as JSONArray; check(a.length() in min..max)
        return originalList((0 until a.length()).map { read(a.get(it) as JSONObject) })
    }
    private fun refs(o: JSONObject, key: String, actors: Int): List<Int> {
        val a = o.get(key) as JSONArray; check(a.length() <= actors)
        val result = (0 until a.length()).map { val n = a.get(it); check(n is Int || n is Long)
            (n as Number).toLong().also { check(it in 0 until actors.toLong()) }.toInt() }
        check(result.toSet().size == result.size); return originalList(result)
    }
    private fun nullableIndex(o: JSONObject, key: String, count: Int): Int? =
        if (o.get(key) === JSONObject.NULL) null else number(o, key).also { check(it < count) }
    private inline fun <T> decode(body: () -> T): T = try { body() } catch (_: Exception) { throw WorkspaceFailure("Malformed") }
    fun capabilities(o: JSONObject) = decode {
        fields(o,"available","provider","max_tokens"); check(o.get("available") is Boolean); check(number(o,"max_tokens") == 1024)
        val available = o.getBoolean("available")
        val p = if (o.get("provider") === JSONObject.NULL) null else provider(text(o,"provider"))
        check(available == (p != null)); OriginalCapabilities(available,p)
    }
    fun job(o: JSONObject) = decode { fields(o,"job","input_sha256","provider")
        OriginalJob(id(text(o,"job")),hash(text(o,"input_sha256")),provider(text(o,"provider"))) }
    fun input(value: OriginalInput): JSONObject = JSONObject().put("version",1).put("premise",value.premise)
        .put("player_name",value.playerName).put("player_description",value.playerDescription)
        .put("cast",JSONArray(value.cast.map { JSONObject().put("name",it.name).put("description",it.description) }))
        .put("profile",value.profile).put("presentation",StoryCreationWire.presentation(value.presentation))
    fun input(o: JSONObject): OriginalInput = decode {
        cap(o,4096); fields(o,"version","premise","player_name","player_description","cast","profile","presentation"); version(o)
        val p = o.getJSONObject("presentation"); fields(p,"version","tone","excluded_phrases"); version(p)
        val a = p.get("excluded_phrases") as JSONArray; check(a.length() <= 8)
        val presentation = StoryPresentation(text(p,"tone"),originalList((0 until a.length()).map { a.get(it) as String }))
        check(validStoryPresentation(presentation)); val profile = text(o,"profile"); check(profile in setOf("fantasy_v1","narrative_v1"))
        OriginalInput(label(text(o,"premise"),2048,1024),name(text(o,"player_name")),label(text(o,"player_description"),empty=true),
            rows(o,"cast",0,3) { fields(it,"name","description"); OriginalCast(name(text(it,"name")),label(text(it,"description"),empty=true)) },profile,presentation)
    }
    fun proposal(v: OriginalProposal): JSONObject = JSONObject().put("version",1)
        .put("locations",JSONArray(v.locations.map { JSONObject().put("name",it.name).put("description",it.description) }))
        .put("player_location",v.playerLocation).put("characters",JSONArray(v.characters.map {
            JSONObject().put("name",it.name).put("description",it.description).put("location",it.location).put("known_by",JSONArray(it.knownBy)) }))
        .put("routes",JSONArray(v.routes.map { JSONObject().put("from",it.from).put("to",it.to) }))
        .put("facts",JSONArray(v.facts.map { JSONObject().put("text",it.text).put("known_by",JSONArray(it.knownBy)).put("discoverable_at",it.discoverableAt ?: JSONObject.NULL) }))
        .put("beliefs",JSONArray(v.beliefs.map { JSONObject().put("believer",it.believer).put("text",it.text).put("confidence",it.confidence) }))
        .put("possessions",JSONArray(v.possessions.map { JSONObject().put("name",it.name).put("description",it.description).put("owner",it.owner).put("return_to",it.returnTo ?: JSONObject.NULL) }))
    fun proposal(o: JSONObject): OriginalProposal = decode {
        cap(o,8192); fields(o,"version","locations","player_location","characters","routes","facts","beliefs","possessions"); version(o)
        val locations = rows(o,"locations",1,4) { fields(it,"name","description"); OriginalLocation(name(text(it,"name")),label(text(it,"description"))) }
        val actors = (o.get("characters") as JSONArray).length()+1; check(actors in 2..4)
        val characters = rows(o,"characters",1,3) { fields(it,"name","description","location","known_by")
            OriginalCharacter(name(text(it,"name")),label(text(it,"description")),number(it,"location").also { n -> check(n < locations.size) },refs(it,"known_by",actors)) }
        val playerLocation = number(o,"player_location").also { check(it < locations.size) }
        OriginalProposal(locations,playerLocation,characters,
            rows(o,"routes",0,8) { fields(it,"from","to"); OriginalRoute(number(it,"from").also { n -> check(n < locations.size) },number(it,"to").also { n -> check(n < locations.size) }) },
            rows(o,"facts",0,8) { fields(it,"text","known_by","discoverable_at"); OriginalFact(label(text(it,"text")),refs(it,"known_by",actors),nullableIndex(it,"discoverable_at",locations.size)) },
            rows(o,"beliefs",0,6) { fields(it,"believer","text","confidence"); val confidence=text(it,"confidence"); check(confidence in setOf("uncertain","suspected","believed"))
                OriginalBelief(number(it,"believer").also { n -> check(n < actors) },label(text(it,"text")),confidence) },
            rows(o,"possessions",0,4) { fields(it,"name","description","owner","return_to"); OriginalPossession(name(text(it,"name")),label(text(it,"description")),number(it,"owner").also { n -> check(n < actors) },nullableIndex(it,"return_to",actors)) })
    }
    fun generated(o: JSONObject) = decode { cap(o,16384); fields(o,"job","input","proposal","provider")
        OriginalGenerated(id(text(o,"job")),input(o.getJSONObject("input")),proposal(o.getJSONObject("proposal")),provider(text(o,"provider"))) }
    fun review(o: JSONObject) = decode { cap(o,65536); fields(o,"job","review_sha256","input","proposal","title","details")
        val a=o.get("details") as JSONArray; check(a.length() in 1..128)
        OriginalReview(id(text(o,"job")),hash(text(o,"review_sha256")),input(o.getJSONObject("input")),proposal(o.getJSONObject("proposal")),
            text(o,"title").also { check(validStoryTitle(it)) },originalList((0 until a.length()).map { (a.get(it) as String).also { s -> check(s.isNotEmpty() && localUtf8(s).size <= 4096) } })) }
    fun cancelled(o: JSONObject): Boolean = decode { fields(o,"cancelled"); o.get("cancelled") as Boolean }
    fun valid(value: OriginalInput, world: OriginalProposal? = null): Boolean = try {
        input(input(value)); if(world != null) proposal(proposal(world)); true
    } catch (_: Exception) { false }
}

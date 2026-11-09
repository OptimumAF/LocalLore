/* Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0 */
package org.locallore.app

import java.io.File
import org.json.JSONArray
import org.json.JSONObject
import org.junit.Assert.*
import org.junit.Test

/** Full envelopes are genuine native fixtures, qualified by the separate Rust cohort. */
internal object SelfProfileFixtures {
    const val OBSERVER = "a-71be92c40d6f8a53c201-0"
    const val LOCATION = "l-71be92c40d6f8a53c201-1"
    data class Case(val domain: Int, val fantasy: Boolean) {
        val rules get() = if (fantasy) "fantasy" else "narrative"
        val story get() = "self-profile-$rules"
        val branch get() = if (domain == 1) "main" else "corrected"
        val revision get() = (if (fantasy) 5L else 2L) + domain - 1
        val scope get() = PlayDraftScope(story, branch)
        fun reply(): JSONObject {
            // Gradle's test worker runs in the app project; no stale-root search.
            val app = File(".").canonicalFile
            val assets = File(app, "src/androidTest/assets").canonicalFile
            val file = File(assets, "player-self-profile-domain$domain-$rules-v1.json").canonicalFile
            check(file.parentFile == assets && assets.toPath().startsWith(app.toPath()))
            check(file.isFile) { "Genuine native profile asset is a setup prerequisite: ${file.name}" }
            return JSONObject(file.readText(Charsets.UTF_8))
        }
        fun frame() = reply().getJSONObject("data")
        fun expected() = PlayerSelfProfile(
            OBSERVER, if (fantasy) "Arié 灯" else "Noor 灯", LOCATION, true, if (fantasy) 7 else 0,
            if (fantasy) listOf(PlayerAbility("chart-sense", 1), PlayerAbility("focus-step", 3)) else emptyList(),
            if (fantasy) listOf(PlayerAttribute("resolve", -7), PlayerAttribute("Élan", 23)) else emptyList(),
            listOf(if (fantasy) "cut-palm" else "sprained-wrist"),
            listOf("cartographers", "夜のギルド"), listOf("finish-chart", "守る"),
        )
    }
    val cases = listOf(Case(1, true), Case(2, true), Case(1, false), Case(2, false))
}

class PlayerSelfProfileWireTest {
    private val case = SelfProfileFixtures.Case(2, true)
    private fun read(frame: JSONObject) = PlayerPresentationWire.decode(frame, case.scope, case.revision)
    private fun actor(frame: JSONObject) = frame.getJSONObject("player").getJSONObject("self_state")
    private fun malformed(frame: JSONObject) {
        val original = frame.toString()
        try { read(frame); fail("Malformed self profile became a player presentation") }
        catch (failure: WorkspaceFailure) { assertEquals("Malformed", failure.category) }
        assertEquals(original, frame.toString())
    }

    @Test fun fourNativeDomainAndRulesFixturesPreserveEveryOpaqueSelfFieldAndAcceptedPresentation() {
        for (fixture in SelfProfileFixtures.cases) {
            val frame = fixture.frame()
            val original = frame.toString()
            val decoded = PlayerPresentationWire.decode(frame, fixture.scope, fixture.revision)
            assertEquals(fixture.domain, decoded.domainVersion)
            assertEquals(fixture.scope, decoded.scope)
            assertEquals(fixture.revision, decoded.revision)
            assertEquals(SelfProfileFixtures.OBSERVER, decoded.observer)
            assertEquals(fixture.expected(), decoded.playerProfile)
            assertEquals(frame.getJSONArray("turns").length() * 2, decoded.messages.size)
            assertEquals(frame.getJSONObject("inventory").length(), decoded.inventory.size)
            assertFalse(decoded.playerProfile.toString().contains("PRIVATE"))
            assertEquals(original, frame.toString())
        }
    }

    @Test fun decodedProfileIsDetachedFromJsonAndEveryNestedListIsUnmodifiable() {
        val frame = case.frame()
        val decoded = read(frame)
        val profile = decoded.playerProfile
        val expected = case.expected()
        val state = actor(frame)
        state.put("name", "MUTATED input").put("energy", 0)
            .put("abilities", JSONObject()).put("attributes", JSONObject())
            .put("injuries", JSONArray()).put("affiliations", JSONArray()).put("goals", JSONArray())
        assertEquals(expected, profile)
        fun <T> immutable(rows: List<T>, injected: T) {
            try { (rows as MutableList<T>).add(injected); fail("Decoded profile list is mutable") }
            catch (_: UnsupportedOperationException) { }
        }
        immutable(profile.abilities, PlayerAbility("forged", 9))
        immutable(profile.attributes, PlayerAttribute("forged", 9))
        immutable(profile.injuries, "forged")
        immutable(profile.affiliations, "forged")
        immutable(profile.goals, "forged")
        assertEquals(expected, decoded.playerProfile)
        assertEquals(decoded.inventory, read(frame).inventory)
        assertEquals(decoded.messages, read(frame).messages)
    }

    @Test fun knownEmptyCollectionsRemainACompleteProfileWhileMissingOrNullFieldsRefuse() {
        val empty = case.frame()
        actor(empty).put("abilities", JSONObject()).put("attributes", JSONObject())
            .put("injuries", JSONArray()).put("affiliations", JSONArray()).put("goals", JSONArray())
        assertEquals(case.expected().copy(abilities = emptyList(), attributes = emptyList(), injuries = emptyList(),
            affiliations = emptyList(), goals = emptyList()), read(empty).playerProfile)
        for (field in listOf("name", "location", "alive", "energy", "abilities", "attributes", "injuries", "affiliations", "goals")) {
            malformed(case.frame().also { actor(it).remove(field) })
            malformed(case.frame().also { actor(it).put(field, JSONObject.NULL) })
        }
        malformed(case.frame().also { it.getJSONObject("player").put("self_state", JSONObject.NULL) })
    }

    @Test fun privateExtraFieldsMistypedScalarsAndOutOfRangeNumbersRefuseTheWholeFrame() {
        val mutations: List<(JSONObject) -> Unit> = listOf(
            { it.put("private_beliefs", JSONArray().put("PRIVATE profile payload")) },
            { it.put("name", true) }, { it.put("location", 5) }, { it.put("alive", "true") },
            { it.put("energy", true) }, { it.put("energy", "7") }, { it.put("energy", 1.5) },
            { it.put("energy", -1) }, { it.put("energy", 65536) },
            { it.getJSONObject("abilities").put("chart-sense", true) },
            { it.getJSONObject("abilities").put("chart-sense", -1) },
            { it.getJSONObject("abilities").put("chart-sense", 65536) },
            { it.getJSONObject("abilities").put("bad ability id", 1) },
            { it.getJSONObject("attributes").put("resolve", -32769) },
            { it.getJSONObject("attributes").put("resolve", 32768) },
            { it.getJSONObject("attributes").put("resolve", "-7") },
        )
        for (mutate in mutations) malformed(case.frame().also { mutate(actor(it)) })
        malformed(case.frame().also { it.getJSONObject("player").put("other_actor", actor(it)) })
        malformed(case.frame().also { it.getJSONObject("player").put("observer", true) })
    }

    @Test fun unicodeStringsAndStructuralNumericBoundsAreLosslessWithoutNativeReachabilityClaims() {
        val frame = case.frame()
        val state = actor(frame)
        val exact = "I\u0301pek 海\nQuoted ‘goal’ 🧭"
        state.put("name", exact).put("location", "place\n灯").put("alive", false).put("energy", 65535)
            .put("abilities", JSONObject().put("zero-rank", 0).put("max-rank", 65535))
            .put("attributes", JSONObject().put("Élan", -32768).put("Resolve 海", 32767))
            .put("injuries", JSONArray().put(exact)).put("affiliations", JSONArray().put(exact))
            .put("goals", JSONArray().put(exact))
        val decoded = read(frame).playerProfile
        assertEquals(exact, decoded.name)
        assertEquals("place\n灯", decoded.location)
        assertFalse(decoded.alive)
        assertEquals(65535, decoded.energy)
        assertEquals(listOf(PlayerAbility("max-rank", 65535), PlayerAbility("zero-rank", 0)), decoded.abilities)
        assertEquals(setOf(PlayerAttribute("Élan", -32768), PlayerAttribute("Resolve 海", 32767)), decoded.attributes.toSet())
        assertEquals(listOf(exact), decoded.injuries)
        assertEquals(listOf(exact), decoded.affiliations)
        assertEquals(listOf(exact), decoded.goals)
        for (field in listOf("injuries", "affiliations", "goals")) {
            malformed(case.frame().also { actor(it).put(field, JSONArray().put("same").put("same")) })
            malformed(case.frame().also { actor(it).put(field, JSONArray().put(3)) })
        }
        malformed(case.frame().also { actor(it).put("name", "\uD800") })
    }

    @Test fun wrongScopeOrHeadCannotPublishAnOtherwiseValidSelfProfile() {
        for ((scope, revision) in listOf(PlayDraftScope("other-story", case.branch) to case.revision,
            PlayDraftScope(case.story, "other-branch") to case.revision, case.scope to case.revision + 1)) {
            try { PlayerPresentationWire.decode(case.frame(), scope, revision); fail("A foreign snapshot was accepted") }
            catch (failure: WorkspaceFailure) { assertEquals("Malformed", failure.category) }
        }
    }
}

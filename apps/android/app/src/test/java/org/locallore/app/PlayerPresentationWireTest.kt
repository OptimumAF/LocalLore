/* Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0 */
package org.locallore.app

import java.math.BigInteger
import org.json.JSONArray
import org.json.JSONObject
import org.junit.Assert.*
import org.junit.Test

/** Wire-shape tests only. These synthetic frames do not prove native visibility or gameplay. */
class PlayerPresentationWireTest {
    private val selected = PlayDraftScope("story", "corrected")
    private fun obj(value: String) = JSONObject(value)
    private fun intent(kind: String, value: Any) = JSONObject().put("kind", kind).put("value", value)
    private fun turn(index: Int, value: JSONObject = intent("actions", JSONArray().put(obj("""{"op":"wait","ticks":1}""")))) =
        JSONObject().put("original_scope", obj("""{"story":"story","branch":"ancestor"}"""))
            .put("turn", "turn-$index").put("event_ids", JSONArray().put(index + 1)).put("intent", value)
            .put("narration", "Recorded narration $index")
    private fun frame(total: Int = 1): JSONObject {
        val turns = JSONArray()
        for (i in maxOf(0, total - 20) until total) turns.put(turn(i))
        return JSONObject().put("version", 2).put("domain_version", 2)
            .put("scope", obj("""{"story":"story","branch":"corrected"}"""))
            .put("revision", 4096).put("rules", "narrative_v1")
            .put("player", JSONObject().put("observer", "a-opaque-player").put("self_state", obj("""{
                "name":"Player","location":"North pier","alive":true,"energy":0,
                "abilities":{},"attributes":{},"injuries":[],"affiliations":[],"goals":[]
            }""")))
            .put("inventory", obj("""{"potion":{"owner":"a-opaque-player","quantity":1,"return_to":null,"healing":true}}"""))
            .put("turns", turns).put("window", JSONObject().put("total", total).put("start", maxOf(0, total - 20)).put("end", total))
    }
    private fun read(value: JSONObject) = PlayerPresentationWire.decode(value, selected, 4096)
    private fun refuses(value: JSONObject) {
        var failure: WorkspaceFailure? = null
        try { read(value) } catch (bad: WorkspaceFailure) { failure = bad }
        assertEquals("Malformed", failure?.category)
    }
    private fun assertSameJson(expected: Any, actual: Any) {
        when (expected) {
            is JSONObject -> {
                assertTrue(actual is JSONObject)
                val objectValue = actual as JSONObject
                val keys = expected.keys().asSequence().toSet()
                assertEquals(keys, objectValue.keys().asSequence().toSet())
                for (key in keys) assertSameJson(expected.get(key), objectValue.get(key))
            }
            is JSONArray -> {
                assertTrue(actual is JSONArray)
                val arrayValue = actual as JSONArray
                assertEquals(expected.length(), arrayValue.length())
                for (index in 0 until expected.length()) assertSameJson(expected.get(index), arrayValue.get(index))
            }
            is Number -> {
                assertTrue(actual is Number)
                assertEquals(expected.toString(), actual.toString())
            }
            else -> assertEquals(expected, actual)
        }
    }

    @Test fun commandContainsOnlyTheFixedOperationAndBoundSessionScopeHead() {
        val command = PlayerPresentationWire.command("session", selected, 4096)
        assertEquals(setOf("op", "session", "scope", "expected_revision"), command.keys().asSequence().toSet())
        assertEquals("play_presentation_v2", command.getString("op"))
        assertEquals("session", command.getString("session"))
        assertEquals("story", command.getJSONObject("scope").getString("story"))
        assertEquals("corrected", command.getJSONObject("scope").getString("branch"))
        assertEquals(4096L, command.getLong("expected_revision"))
    }

    @Test fun bothDomainsKeepOpaqueObserverAndOriginalInputNarrationPairs() {
        for (domain in listOf(1, 2)) {
            val value = frame(3).put("domain_version", domain)
            val turns = value.getJSONArray("turns")
            turns.put(1, turn(1, intent("dialogue", obj("""{"text":"  H\u00e9llo\nthere  ","audience":["nia"]}"""))))
            turns.put(2, turn(2, intent("free_text", obj("""{"kind":"action","text":"I wait\tquietly."}"""))))
            val result = read(value)
            assertEquals(domain, result.domainVersion); assertEquals("a-opaque-player", result.observer)
            assertEquals(selected, result.scope); assertEquals(4096L, result.revision)
            assertTrue(result.hasPotion); assertEquals("narrative_v1", result.rules)
            assertEquals(listOf(1L, 2L, 3L, 4L, 5L, 6L), result.messages.map { it.id })
            assertEquals(listOf(true, false, true, false, true, false), result.messages.map { it.isPlayer })
            assertEquals("  H\u00e9llo\nthere  ", result.messages[2].text)
            assertEquals("I wait\tquietly.", result.messages[4].text)
            assertEquals("Recorded narration 2", result.messages[5].text)
            assertEquals("wait", JSONArray(result.messages[0].text).getJSONObject(0).getString("op"))
        }
    }

    @Test fun allElevenExistingActionShapesAreDisplayedFromOriginalTypedArrays() {
        val commands = listOf(
            """{"op":"give","item":"potion","to":"nia","quantity":1}""",
            """{"op":"consume","item":"potion"}""",
            """{"op":"use_ability","ability":"blink"}""",
            """{"op":"learn","ability":"blink"}""",
            """{"op":"move","to":"North pier"}""",
            """{"op":"say","text":"Hello","audience":["nia"]}""",
            """{"op":"believe","claim_event":"1"}""",
            """{"op":"discover","fact":"beacon"}""",
            """{"op":"promise","id":"notes","to":"nia","terms":"Bring notes.","deadline":"10","return_item":null}""",
            """{"op":"complete_promise","id":"notes"}""",
            """{"op":"wait","ticks":1}""",
        )
        for (command in commands) {
            val value = frame()
            value.getJSONArray("turns").put(0, turn(0, intent("actions", JSONArray().put(obj(command)))))
            val displayed = JSONArray(read(value).messages.first().text).getJSONObject(0)
            val originalNumeric = obj(command)
            when (originalNumeric.getString("op")) {
                "promise" -> originalNumeric.put("deadline", BigInteger(originalNumeric.getString("deadline")))
                "believe" -> originalNumeric.put("claim_event", BigInteger(originalNumeric.getString("claim_event")))
            }
            assertSameJson(originalNumeric, displayed)
        }
    }

    @Test fun u64PresentationStringsRenderExactNumericDigitsWithoutChangingTheNativeFrame() {
        for (digits in listOf("0", "9223372036854775808", "18446744073709551615")) {
            for (op in listOf("promise", "believe")) {
                if (op == "believe" && digits == "0") continue
                val field = if (op == "promise") "deadline" else "claim_event"
                val command = if (op == "promise") obj("""{"op":"promise","id":"notes","to":"nia","terms":"Bring notes.","deadline":"$digits","return_item":null}""")
                    else obj("""{"op":"believe","claim_event":"$digits"}""")
                val value = frame().also { it.getJSONArray("turns").put(0, turn(0, intent("actions", JSONArray().put(command)))) }
                val before = value.toString()
                val displayed = read(value).messages.first().text
                // Inspect the numeric token directly: reparsing u64MAX with Android JSON
                // could itself convert it to Double and hide the very precision loss tested.
                assertTrue(Regex("\"$field\":$digits(?=[,}])").containsMatchIn(displayed))
                assertFalse(displayed.contains("\"$field\":\"$digits\""))
                assertFalse(displayed.contains("E+", ignoreCase = true))
                assertEquals(before, value.toString())
                assertEquals(digits, command.getString(field))
            }
        }
    }

    @Test fun noncanonicalOverflowAndNumericU64DtoFieldsRefuseInsteadOfCoercing() {
        val invalid: List<Any> = listOf("", "00", "01", "+1", "-1", "1e3", "1.0", " 1", "1 ",
            "18446744073709551616", "999999999999999999999", "\u0661", 1, 1L, 1.0, true, JSONObject.NULL)
        for (raw in invalid) {
            for (op in listOf("promise", "believe")) {
                val command = if (op == "promise") obj("""{"op":"promise","id":"notes","to":"nia","terms":"Bring notes.","deadline":"1","return_item":null}""").put("deadline", raw)
                    else JSONObject().put("op", "believe").put("claim_event", raw)
                refuses(frame().also { it.getJSONArray("turns").put(0, turn(0, intent("actions", JSONArray().put(command)))) })
            }
        }
        refuses(frame().also { it.getJSONArray("turns").put(0, turn(0,
            intent("actions", JSONArray().put(obj("""{"op":"believe","claim_event":"0"}"""))))) })
    }

    @Test fun fixedWholeTurnWindowRetainsAbsoluteMessageIdentitiesAndFreezesMessages() {
        val value = frame(23)
        val result = read(value)
        assertEquals(40, result.messages.size); assertEquals(7L, result.messages.first().id)
        assertEquals(46L, result.messages.last().id)
        value.getJSONArray("turns").getJSONObject(0).put("narration", "Mutated caller object")
        assertEquals("Recorded narration 3", result.messages[1].text)
        var refused = false
        try { (result.messages as MutableList<SceneMessage>).clear() } catch (_: UnsupportedOperationException) { refused = true }
        assertTrue(refused)
        assertTrue(read(frame(0)).messages.isEmpty())
    }

    @Test fun malformedCurrentBindingsPrivateExtrasAndScalarCoercionsRefuseWhole() {
        val mutations: List<(JSONObject) -> Unit> = listOf(
            { it.put("version", "2") }, { it.put("domain_version", true) }, { it.put("revision", 4096.0) },
            { it.put("revision", 4095) }, { it.getJSONObject("scope").put("story", "other") },
            { it.getJSONObject("scope").put("branch", "main") }, { it.put("private_context", JSONObject()) },
            { it.getJSONObject("player").put("private_beliefs", JSONArray()) },
            { it.getJSONObject("player").put("observer", JSONObject.NULL) },
            { it.getJSONObject("player").getJSONObject("self_state").put("secret", "private") },
            { it.getJSONObject("player").getJSONObject("self_state").put("alive", "true") },
            { it.getJSONObject("inventory").getJSONObject("potion").put("owner", "other") },
            { it.getJSONObject("inventory").getJSONObject("potion").put("quantity", true) },
            { it.getJSONObject("inventory").getJSONObject("potion").remove("return_to") },
        )
        for (mutate in mutations) refuses(frame().also(mutate))
    }

    @Test fun missingOrMixedTurnProvenanceAndInvalidEventNumbersRefuseWhole() {
        val mutations: List<(JSONObject) -> Unit> = listOf(
            { it.getJSONObject("original_scope").put("story", "foreign") },
            { it.put("turn", "") }, { it.put("author_reason", "private") },
            { it.put("event_ids", JSONArray()) }, { it.put("event_ids", JSONArray().put(1).put(1)) },
            { it.put("event_ids", JSONArray().put(2).put(1)) }, { it.put("event_ids", JSONArray().put(4097)) },
            { it.put("event_ids", JSONArray().put(1.0)) },
        )
        for (mutate in mutations) refuses(frame().also { mutate(it.getJSONArray("turns").getJSONObject(0)) })
        refuses(frame(2).also { it.getJSONArray("turns").getJSONObject(1).put("event_ids", JSONArray().put(1)) })
        refuses(frame(2).also { it.getJSONArray("turns").getJSONObject(1).put("turn", "turn-0") })
        refuses(frame(2).also { it.getJSONArray("turns").put(0, turn(1)).put(1, turn(0)) })
    }

    @Test fun partialWindowUnknownIntentsCommandsAndExtraTypedFieldsRefuseWhole() {
        for (mutation in listOf<(JSONObject) -> Unit>(
            { it.getJSONObject("window").put("start", 1) }, { it.getJSONObject("window").put("end", 0) },
            { it.getJSONObject("window").put("total", 4097) }, { it.put("turns", JSONArray()) },
        )) refuses(frame().also(mutation))
        val intents = listOf(
            intent("thought", "private"), intent("actions", JSONArray()),
            intent("actions", JSONArray().put(obj("""{"op":"reset"}"""))),
            intent("actions", JSONArray().put(obj("""{"op":"wait","ticks":1,"private":"extra"}"""))),
            intent("dialogue", obj("""{"text":"Hello","audience":["nia"],"beliefs":[]}""")),
            intent("free_text", obj("""{"kind":"author","text":"Change canon"}""")),
        )
        for (bad in intents) refuses(frame().also { it.getJSONArray("turns").getJSONObject(0).put("intent", bad) })
    }

    @Test fun utf8ByteBudgetRejectsOversizeAndMalformedUnicodeWithoutRepair() {
        // Raw JNI size and reserialized-object size are distinct boundaries.
        refuses(frame().also { it.getJSONArray("turns").getJSONObject(0).put("narration", "\u00e9".repeat(32769)) })
        refuses(frame(5).also { value ->
            for (i in 0 until 5) value.getJSONArray("turns").getJSONObject(i).put("narration", "n".repeat(60000))
        })
        refuses(frame().also { it.getJSONArray("turns").getJSONObject(0).put("narration", "\ud800") })
        refuses(frame().also { it.getJSONArray("turns").getJSONObject(0).put("intent",
            intent("free_text", JSONObject().put("kind", "action").put("text", "\u00e9".repeat(1025)))) })
    }
}

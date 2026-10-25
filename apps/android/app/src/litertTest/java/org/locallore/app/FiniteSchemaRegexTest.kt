/* Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0 */
package org.locallore.app

import java.util.regex.Pattern
import java.nio.file.Files
import java.nio.file.LinkOption
import java.nio.file.Path
import java.nio.file.StandardOpenOption
import java.security.MessageDigest
import org.json.JSONArray
import org.json.JSONObject
import org.json.JSONTokener
import org.junit.Assert.*
import org.junit.Test

/** Canonical-language seam only; Pattern is not the pinned native compiler or an engine. */
class FiniteSchemaRegexTest {
    private val original = """{"additionalProperties":false,"properties":{"commands":{"items":{"oneOf":[{"additionalProperties":false,"properties":{"audience":{"enum":[["mira"]],"items":{"enum":["mira"]},"maxItems":4,"minItems":1,"type":"array"},"op":{"const":"say"},"text":{"const":"Where is the tideglass relic?"}},"required":["audience","op","text"],"type":"object"}]},"maxItems":1,"minItems":1,"type":"array"}},"required":["commands"],"type":"object"}"""
    private val escapedOriginal = """{"additionalProperties":false,"properties":{"commands":{"items":{"oneOf":[{"additionalProperties":false,"properties":{"audience":{"enum":[["mira"]],"items":{"enum":["mira"]},"maxItems":4,"minItems":1,"type":"array"},"op":{"const":"say"},"text":{"const":"Hello \"Mira\" \\ 雪.\nIs the tideglass here?"}},"required":["audience","op","text"],"type":"object"}]},"maxItems":1,"minItems":1,"type":"array"}},"required":["commands"],"type":"object"}"""
    private val question = "Where is the tideglass relic?"
    private fun body(audience: List<String>, text: String = question, op: String = "say"): String =
        "{\"commands\":[{\"audience\":" + JSONArray(audience).toString() + ",\"op\":" + JSONObject.quote(op) + ",\"text\":" + JSONObject.quote(text) + "}]}"
    private fun matches(schema: String, candidate: String): Boolean =
        Pattern.compile(requireNotNull(finiteSchemaRegex(schema))).matcher(candidate).matches()
    private fun properties(schema: JSONObject): JSONObject = schema.getJSONObject("properties").getJSONObject("commands")
        .getJSONObject("items").getJSONArray("oneOf").getJSONObject(0).getJSONObject("properties")
    private fun choices(names: List<String>): List<List<String>> = (1 until (1 shl names.size)).filter { Integer.bitCount(it) <= 4 }
        .map { mask -> names.filterIndexed { index, _ -> mask and (1 shl index) != 0 } }

    @Test fun exactOriginal425ByteSchemaAcceptsFullCanonicalOutput() {
        assertEquals(425, localUtf8(original).size)
        assertNotNull(finiteSchemaRegex(original))
        assertTrue(matches(original, body(listOf("mira"))))
        assertFalse(matches(original, body(emptyList())))
        assertFalse(matches(original, body(listOf("mira", "mira"))))
        exportOriginalPatternsIfRequested()
    }

    @Test fun independentAllAudienceSetsThroughSixRemainCompleteAndBounded() {
        val counts = listOf(1, 3, 7, 15, 30, 56)
        for (count in 1..6) {
            val names = (0 until count).map { "listener-$it" }
            val sets = choices(names)
            assertEquals(counts[count - 1], sets.size)
            val schema = JSONObject(original)
            properties(schema).getJSONObject("audience").put("enum", JSONArray(sets.map { JSONArray(it) }))
                .put("items", JSONObject().put("enum", JSONArray(names)))
            val encoded = schema.toString()
            for (set in sets) assertTrue("Missing finite choice", matches(encoded, body(set)))
            assertFalse(matches(encoded, body(listOf("foreign"))))
            if (count >= 2) assertFalse(matches(encoded, body(names.take(2).reversed())))
            if (count >= 5) assertFalse(matches(encoded, body(names.take(5))))
        }
    }

    @Test fun originalEscapedLongLiteralIsWholeAndWrongTruncatedPrefixesRefuse() {
        assertEquals(442, localUtf8(escapedOriginal).size)
        val text = "Hello \"Mira\" \\ 雪.\nIs the tideglass here?"
        assertTrue(localUtf8(text).size > 31)
        assertTrue(matches(escapedOriginal, body(listOf("mira"), text)))
        for (prefix in listOf(text.take(1), text.take(11), text.take(31))) {
            assertFalse("A quote-prefix is not the original literal", matches(escapedOriginal, body(listOf("mira"), prefix)))
        }
        assertFalse(matches(escapedOriginal, body(listOf("mira"), text + "x")))
    }

    @Test fun wrongTextOperationExtraMissingReorderedAndOuterWhitespaceRefuse() {
        val good = body(listOf("mira"))
        assertFalse(matches(original, body(listOf("mira"), "A different utterance")))
        assertFalse(matches(original, body(listOf("mira"), op = "give")))
        assertFalse(matches(original, good.replace("\"op\":\"say\",", "")))
        assertFalse(matches(original, good.replace("\"op\":\"say\",", "\"op\":\"say\",\"extra\":true,")))
        assertFalse(matches(original, "{\"commands\":[{\"text\":" + JSONObject.quote(question) + ",\"op\":\"say\",\"audience\":[\"mira\"]}]}"))
        for (candidate in listOf(" " + good, good + " ", good + "\n", good + "x", good.dropLast(1))) assertFalse(matches(original, candidate))
    }

    @Test fun everyRustRegexMetacharacterRemainsLiteralJsonData() {
        val literal = "\\.+*?()|[]{}^$ / \" \n\t雪🦉"
        val schema = JSONObject().put("const", literal).toString()
        assertTrue(matches(schema, JSONObject.quote(literal)))
        assertFalse(matches(schema, JSONObject.quote(literal.replace("*", "anything"))))
        assertFalse(matches(schema, "\"prefix\""))
    }

    @Test fun integerBooleanAndBudgetedNestedLiteralsUseCanonicalJson() {
        for (number in listOf(Long.MIN_VALUE, -1L, 0L, 1L, Long.MAX_VALUE)) {
            val schema = JSONObject().put("type", "integer").put("const", number).toString()
            assertTrue(matches(schema, number.toString()))
            assertFalse(matches(schema, "\"$number\""))
        }
        assertTrue(matches("""{"type":"boolean","const":true}""", "true"))
        assertFalse(matches("""{"const":true}""", "false"))
        val schema = """{"type":"object","const":{"z":false,"a":[1,"literal"]}}"""
        assertTrue(matches(schema, """{"a":[1,"literal"],"z":false}"""))
        assertFalse(matches(schema, """{"z":false,"a":[1,"literal"]}"""))
        assertNull(finiteSchemaRegex("""{"type":"string","const":1}"""))
    }

    @Test fun closedRequiredObjectsSortPropertiesWithoutExpandingCrossProducts() {
        val schema = """{"type":"object","additionalProperties":false,"required":["z","a"],"properties":{"z":{"enum":["c","d"]},"a":{"enum":["a","b"]}}}"""
        for (a in listOf("a", "b")) for (z in listOf("c", "d")) assertTrue(matches(schema, "{\"a\":\"$a\",\"z\":\"$z\"}"))
        assertFalse(matches(schema, """{"z":"c","a":"a"}"""))
        assertTrue(matches("""{"type":"object","additionalProperties":false,"required":[],"properties":{}}""", "{}"))
        assertTrue(matches("""{"type":"array","minItems":1,"maxItems":1,"items":{"oneOf":[{"const":true}]}}""", "[true]"))
    }

    @Test fun requiredAdditionalPropertiesAndSingleAlternativeSemanticsAreNeverApproximated() {
        val invalid = listOf(
            """{"oneOf":[]}""", """{"oneOf":[{"const":"a"},{"const":"a"}]}""",
            """{"oneOf":[{"const":"a"},{"const":"b"}]}""", """{"oneOf":[{"const":"a"}],"type":"string"}""",
            """{"type":"array","items":{"const":1},"minItems":0,"maxItems":1}""",
            """{"type":"array","items":[{"const":1}],"minItems":1,"maxItems":1}""",
            """{"type":"object","properties":{"a":{"const":1}},"required":[],"additionalProperties":false}""",
            """{"type":"object","properties":{"a":{"const":1}},"required":["a","a"],"additionalProperties":false}""",
            """{"type":"object","properties":{"a":{"const":1}},"required":["a"],"additionalProperties":true}"""
        )
        for (schema in invalid) assertNull(finiteSchemaRegex(schema))
    }

    @Test fun allRedundantEnumArrayConstraintsAreValidatedNotFiltered() {
        val schema = JSONObject(original)
        val audience = properties(schema).getJSONObject("audience")
        audience.put("maxItems", 0); assertNull(finiteSchemaRegex(schema.toString()))
        audience.put("maxItems", 4).put("minItems", 2); assertNull(finiteSchemaRegex(schema.toString()))
        audience.put("minItems", 1).put("items", JSONObject().put("enum", JSONArray(listOf("foreign"))))
        assertNull(finiteSchemaRegex(schema.toString()))
        audience.put("items", JSONObject().put("type", "string")); assertNotNull(finiteSchemaRegex(schema.toString()))
        audience.put("items", JSONObject().put("type", "integer")); assertNull(finiteSchemaRegex(schema.toString()))
        assertNull(finiteSchemaRegex("""{"type":"array","enum":[[]],"items":{"unknown":true}}"""))
        assertNull(finiteSchemaRegex("""{"type":"array","enum":[["a"]],"items":{"enum":["a"],"pattern":"a"}}"""))
        assertNull(finiteSchemaRegex("""{"enum":[]}"""))
        assertNull(finiteSchemaRegex("""{"enum":["a","a"]}"""))
        assertNull(finiteSchemaRegex("""{"type":"string","enum":["a",true]}"""))
        assertNull(finiteSchemaRegex("""{"enum":[1]}"""))
        assertNull(finiteSchemaRegex("""{"enum":[{"arbitrary":"object"}]}"""))
    }

    @Test fun unknownNonfiniteNullNarratorAndLenientJsonReturnNull() {
        for (schema in listOf("""{"type":"string"}""", """{"type":"string","maxLength":20}""",
            """{"const":"a","description":"ignored"}""", """{"enum":["a"],"pattern":"a"}""",
            """{"const":null}""", """{"const":1.5}""", """{"const":1e2}""", """{"const":NaN}""",
            """{"const":9223372036854775808}""", """{'const':'a'}""", """{const:"a"}""",
            """{"const":"a",}""", """{"const":[1,]}""", """{"const":"a"} // comment""",
            """{"const":"a"} {}""", """{"const":01}""", "null", "[]", "", "{")) assertNull(finiteSchemaRegex(schema))
    }

    @Test fun duplicateDecodedKeysAndUnpairedSurrogatesRefuse() {
        for (schema in listOf("""{"const":"a","const":"b"}""", """{"const":"a","con\u0073t":"b"}""",
            """{"const":{"a":1,"\u0061":2}}""", """{"const":"\uD800"}""", """{"const":"\uDC00"}""")) assertNull(finiteSchemaRegex(schema))
        assertNull(finiteSchemaRegex("{\"const\":\"" + '\uD800' + "\"}"))
        assertTrue(matches("""{"const":"\uD83E\uDD89"}""", JSONObject.quote("🦉")))
    }

    @Test fun depthTwelveNode512InputAndRegexUtf8BudgetsRefuseBeforeOverflow() {
        fun nested(depth: Int) = "{\"const\":" + "[".repeat(depth) + "0" + "]".repeat(depth) + "}"
        assertNotNull(finiteSchemaRegex(nested(11)))
        assertNull(finiteSchemaRegex(nested(12)))
        fun many(count: Int) = JSONObject().put("enum", JSONArray((0 until count).map { it.toString() })).toString()
        assertNotNull(finiteSchemaRegex(many(510)))
        assertNull(finiteSchemaRegex(many(511)))
        assertNull(finiteSchemaRegex(JSONObject().put("const", "x".repeat(32768)).toString()))
        assertNull(finiteSchemaRegex(JSONObject().put("const", "雪".repeat(11000)).toString()))
        assertNotNull(finiteSchemaRegex(JSONObject().put("const", ".".repeat(16000)).toString()))
        assertNull(finiteSchemaRegex(JSONObject().put("const", ".".repeat(16380)).toString()))
    }

    @Test fun inputSchemaIsImmutableAndNoDomainNamesSelectRepresentation() {
        val source = JSONObject(original)
        val before = source.toString()
        val result = finiteSchemaRegex(before)
        assertEquals(before, source.toString())
        assertEquals(result, finiteSchemaRegex(before))
        assertTrue(matches("""{"const":"an arbitrary literal unrelated to actors or actions"}""", JSONObject.quote("an arbitrary literal unrelated to actors or actions")))
        assertNull(finiteSchemaRegex("""{"op":"say","text":"a model claim","grant":true}"""))
    }

    /** Root-owned evidence path only; never used by the app or default test run. */
    private fun exportOriginalPatternsIfRequested() {
        val input = System.getenv("LOCALLORE_FINITE_ORACLE_CORPUS")
        val output = System.getenv("LOCALLORE_FINITE_ORACLE_OUTPUT")
        require((input == null) == (output == null)) { "Both finite export bindings required" }
        if (input == null || output == null) return
        val source = Path.of(input)
        val target = Path.of(output)
        require(source.isAbsolute && target.isAbsolute && !Files.isSymbolicLink(source))
        require(Files.isRegularFile(source, LinkOption.NOFOLLOW_LINKS))
        val bytes = Files.newInputStream(source).use { it.readNBytes(1_048_577) }
        require(bytes.size in 1..1_048_576)
        val parser = JSONTokener(localText(bytes, 1_048_576))
        val corpus = parser.nextValue() as? JSONObject ?: error("Finite corpus required")
        require(parser.nextClean() == '\u0000')
        require(corpus.keys().asSequence().toSet() == setOf("version", "scope", "cases", "refusals"))
        require(corpus.get("version") is Int && corpus.get("version") == 1)
        require(corpus.get("scope") == "locallore_llguidance_oracle_v1")
        val cases = corpus.get("cases") as? JSONArray ?: error("Finite cases required")
        val refusals = corpus.get("refusals") as? JSONArray ?: error("Finite refusals required")
        require(cases.length() in 1..16 && refusals.length() in 0..16)
        val result = JSONArray()
        val caseIds = mutableSetOf<String>()
        var sampleCount = 0
        for (index in 0 until cases.length()) {
            val case = cases.get(index) as? JSONObject ?: error("Finite case required")
            require(case.keys().asSequence().toSet() == setOf("id", "schema_json", "positives", "negatives"))
            val id = case.get("id") as? String ?: error("Finite ID required")
            require(id.matches(Regex("[a-z][a-z0-9-]{0,47}")) && caseIds.add(id))
            val schema = case.get("schema_json") as? String ?: error("Finite schema required")
            require(localUtf8(schema).size in 1..16_384)
            val sampleIds = mutableSetOf<String>()
            for (section in listOf("positives", "negatives")) {
                val samples = case.get(section) as? JSONArray ?: error("Finite samples required")
                require(samples.length() in 1..256)
                sampleCount += samples.length(); require(sampleCount <= 256)
                for (sampleIndex in 0 until samples.length()) {
                    val sample = samples.get(sampleIndex) as? JSONObject ?: error("Finite sample required")
                    require(sample.keys().asSequence().toSet() == setOf("id", "json"))
                    val sampleId = sample.get("id") as? String ?: error("Finite sample ID required")
                    require(sampleId.matches(Regex("[a-z][a-z0-9-]{0,47}")) && sampleIds.add(sampleId))
                    require(localUtf8(sample.get("json") as? String ?: error("Finite sample text required")).size in 1..16_384)
                }
            }
            val regex = finiteSchemaRegex(schema) ?: error("Unsupported finite case")
            result.put(JSONObject().put("index", index).put("schema_sha256", sha(localUtf8(schema))).put("regex", regex))
        }
        val refusalIds = mutableSetOf<String>()
        for (index in 0 until refusals.length()) {
            val refusal = refusals.get(index) as? JSONObject ?: error("Finite refusal required")
            require(refusal.keys().asSequence().toSet() == setOf("id", "error", "provider_calls", "canon_unchanged"))
            val id = refusal.get("id") as? String ?: error("Finite refusal ID required")
            require(id.matches(Regex("[a-z][a-z0-9-]{0,47}")) && refusalIds.add(id))
            require((refusal.get("error") as? String) in setOf("ClarificationRequired", "TooLarge"))
            require(refusal.get("provider_calls") is Int && refusal.get("provider_calls") == 0)
            require(refusal.get("canon_unchanged") is Boolean && refusal.get("canon_unchanged") == true)
        }
        // All semantic/size failures above occur before opening the create-only output.
        // Root also strictly validates the exact source corpus and the resulting artifact.
        val encoded = localUtf8(JSONObject().put("version", 1).put("scope", "locallore_finite_regex_corpus_v1")
            .put("source_corpus_sha256", sha(bytes)).put("cases", result).toString())
        require(encoded.size <= 2_097_152)
        Files.write(target, encoded, StandardOpenOption.CREATE_NEW, StandardOpenOption.WRITE)
    }

    private fun sha(bytes: ByteArray): String = MessageDigest.getInstance("SHA-256").digest(bytes)
        .joinToString("") { "%02x".format(it) }
}

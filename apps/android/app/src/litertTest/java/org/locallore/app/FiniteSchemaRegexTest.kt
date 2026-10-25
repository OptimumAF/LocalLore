/* Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0 */
package org.locallore.app

import java.util.regex.Pattern
import java.nio.file.Files
import java.nio.file.LinkOption
import java.nio.file.Path
import java.nio.file.StandardOpenOption
import java.security.MessageDigest
import com.google.gson.JsonArray
import com.google.gson.JsonElement
import com.google.gson.JsonObject
import com.google.gson.JsonParser
import com.google.gson.JsonPrimitive
import org.junit.Assert.*
import org.junit.Test

/** Finite JSON-spelling seam only; Pattern is not the pinned native compiler or an engine. */
class FiniteSchemaRegexTest {
    private val original = """{"additionalProperties":false,"properties":{"commands":{"items":{"oneOf":[{"additionalProperties":false,"properties":{"audience":{"enum":[["mira"]],"items":{"enum":["mira"]},"maxItems":4,"minItems":1,"type":"array"},"op":{"const":"say"},"text":{"const":"Where is the tideglass relic?"}},"required":["audience","op","text"],"type":"object"}]},"maxItems":1,"minItems":1,"type":"array"}},"required":["commands"],"type":"object"}"""
    private val escapedOriginal = """{"additionalProperties":false,"properties":{"commands":{"items":{"oneOf":[{"additionalProperties":false,"properties":{"audience":{"enum":[["mira"]],"items":{"enum":["mira"]},"maxItems":4,"minItems":1,"type":"array"},"op":{"const":"say"},"text":{"const":"Hello \"Mira\" \\ 雪.\nIs the tideglass here?"}},"required":["audience","op","text"],"type":"object"}]},"maxItems":1,"minItems":1,"type":"array"}},"required":["commands"],"type":"object"}"""
    private val question = "Where is the tideglass relic?"
    private fun quote(value: String): String = JsonPrimitive(value).toString()
    private fun strings(values: List<String>): JsonArray = JsonArray().apply { values.forEach { add(it) } }
    private fun body(audience: List<String>, text: String = question, op: String = "say"): String =
        "{\"commands\":[{\"audience\":" + strings(audience).toString() + ",\"op\":" + quote(op) + ",\"text\":" + quote(text) + "}]}"
    private fun matches(schema: String, candidate: String): Boolean =
        Pattern.compile(requireNotNull(finiteSchemaRegex(schema))).matcher(candidate).matches()
    private fun properties(schema: JsonObject): JsonObject {
        val commands = jsonObject(jsonObject(schema.get("properties")).get("commands"))
        val items = jsonObject(commands.get("items"))
        val only = jsonObject(jsonArray(items.get("oneOf")).get(0))
        return jsonObject(only.get("properties"))
    }
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
            val schema = JsonParser.parseString(original).asJsonObject
            val audience = jsonObject(properties(schema).get("audience"))
            audience.add("enum", JsonArray().apply { sets.forEach { add(strings(it)) } })
            audience.add("items", JsonObject().apply { add("enum", strings(names)) })
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

    private fun equivalent(schema: String, canonical: String, alternate: String) {
        assertEquals(JsonParser.parseString(canonical), JsonParser.parseString(alternate))
        assertTrue(matches(schema, canonical)); assertTrue(matches(schema, alternate))
    }

    @Test fun originalSpeechKeepsEveryCanonicalSpaceAndAddsOnlyEquivalentEscapedSpaces() {
        val canonical = body(listOf("mira"))
        equivalent(original, canonical, canonical.replace(" ", "\\u0020"))
        for (index in canonical.indices.filter { canonical[it] == ' ' }) {
            equivalent(original, canonical, canonical.substring(0, index) + "\\u0020" + canonical.substring(index + 1))
        }
        for (wrong in listOf("\\u0021", "\\u002f", "\\u002", "\\U0020", "\\u 020", "\\u000a")) {
            assertFalse(matches(original, canonical.replaceFirst(" ", wrong)))
        }
        assertFalse(matches(original, canonical.replace(" ", "")))
    }

    @Test fun literalBackslashUIsDataAndNeverDecodedAsAnActualSpaceByThePattern() {
        for (literal in listOf("\\u0020", "\\\\u0020", "a\\u0020 b", "\\u96ea 雪")) {
            val schema = JsonObject().apply { addProperty("const", literal) }.toString()
            val canonical = quote(literal)
            equivalent(schema, canonical, canonical.replace(" ", "\\u0020"))
            assertFalse(matches(schema, quote(literal.replace("\\u0020", " ").replace("\\u96ea", "雪"))))
        }
        assertFalse(matches("""{"const":" "}""", quote("\\u0020")))
        assertFalse(matches("""{"const":"\\u0020"}""", quote(" ")))
    }

    @Test fun nonAsciiScalarsHaveCompleteCaseFlexibleEscapesAndAstralPairs() {
        val literal = "雪 café 🦉\u007f\u0080"
        val schema = JsonObject().apply { addProperty("const", literal) }.toString()
        val canonical = quote(literal)
        val alternate = "\"\\u96Ea\\u0020caf\\u00E9\\u0020\\uD83e\\uDD89\u007f\\u0080\""
        equivalent(schema, canonical, alternate)
        equivalent("""{"const":"\u2028\u2029"}""", quote("\u2028\u2029"), "\"\\u2028\\u2029\"")
        for (wrong in listOf("\\uD83e", "\\uDD89", "\\uDD89\\uD83e", "\\uD83e\\uDD88", "\\uD83eX\\uDD89")) {
            assertFalse(matches("""{"const":"🦉"}""", "\"$wrong\""))
        }
        assertFalse(matches(schema, alternate.replace("\\u00E9", "\\u0065")))
        assertFalse(matches(schema, alternate.replace("\\u96Ea", "\\u96EZ")))
    }

    @Test fun stringKeysAndNestedLiteralValuesReceiveTheSameSpellingPolicy() {
        val schema = """{"const":{"a b":{"雪 key":["x y",{"🦉":"\\u0020 z"}]}}}"""
        val canonical = """{"a b":{"雪 key":["x y",{"🦉":"\\u0020 z"}]}}"""
        val alternate = canonical.replace(" ", "\\u0020").replace("雪", "\\u96eA").replace("🦉", "\\ud83e\\udd89")
        equivalent(schema, canonical, alternate)
        val objectSchema = """{"type":"object","additionalProperties":false,"required":["a b"],"properties":{"a b":{"const":"x y"}}}"""
        equivalent(objectSchema, """{"a b":"x y"}""", """{"a\u0020b":"x\u0020y"}""")
        assertFalse(matches(schema, alternate.replace("\\u0020", " ") + " "))
    }

    @Test fun asciiPunctuationControlsAndStructuralWhitespaceRemainExact() {
        val literal = "quote\" backslash\\ newline\n tab\t / {} [] .+*?()|^$"
        val schema = JsonObject().apply { addProperty("const", literal) }.toString()
        val canonical = quote(literal)
        equivalent(schema, canonical, canonical.replace(" ", "\\u0020"))
        for (candidate in listOf(canonical.replace("\\n", "\\u000a"), canonical.replace("\\t", "\\u0009"),
            canonical.replace("/", "\\/"), canonical.replace("\\\"", "\\u0022"))) assertFalse(matches(schema, candidate))
        val value = body(listOf("mira"))
        for (candidate in listOf(" " + value, value + " ", value.replaceFirst(":", ": "),
            value.replaceFirst(":", ":\\u0020"), value.replaceFirst(",", ",\t"))) assertFalse(matches(original, candidate))
        assertFalse(matches(original, value.replace("say", "\\u0073ay")))
        assertFalse(matches(original, value.replace("commands", "\\u0063ommands")))
    }

    @Test fun escapedSpaceEnumChoicesRetainTheirDecodedIdentityAndEveryCombination() {
        val schema = """{"enum":[["a b","c d"],["e f"]],"type":"array","items":{"enum":["a b","c d","e f"]},"minItems":1,"maxItems":2}"""
        for (canonical in listOf("""["a b","c d"]""", """["e f"]""")) {
            equivalent(schema, canonical, canonical.replace(" ", "\\u0020"))
        }
        assertFalse(matches(schema, """["c\u0020d","a\u0020b"]"""))
        assertNull(finiteSchemaRegex("""{"enum":["a b","a\u0020b"]}"""))
        assertNull(finiteSchemaRegex("""{"enum":["🦉","\uD83E\uDD89"]}"""))
    }

    @Test fun wholeScalarAlternativesAndTheirGroupsAreChargedToTheExistingOutputLimit() {
        fun schema(count: Int) = JsonObject().apply { addProperty("const", " ".repeat(count)) }.toString()
        // Per-space (?: |\\u0020) is13 bytes, plus14 bytes for existing outer/choice/quote framing.
        val allowed = (32768 - 14) / 13
        val regex = requireNotNull(finiteSchemaRegex(schema(allowed)))
        assertEquals(14 + allowed * 13, localUtf8(regex).size)
        assertEquals("\\A(?:(?:\"" + "(?: |\\\\u0020)".repeat(allowed) + "\"))\\z", regex)
        Pattern.compile(regex)
        exportPressurePatternIfRequested(schema(allowed), regex, allowed)
        // Java Pattern's recursive matcher is not the native compiler's stack model.
        // Check the complete maximum pattern above and representative combinations here.
        assertTrue(matches(schema(64), quote(" ".repeat(64))))
        assertTrue(matches(schema(64), "\"" + "\\u0020".repeat(64) + "\""))
        assertNull(finiteSchemaRegex(schema(allowed + 1)))
        assertNull(finiteSchemaRegex(JsonObject().apply { addProperty("const", "🦉".repeat(1500)) }.toString()))
    }

    @Test fun wrongTextOperationExtraMissingReorderedAndOuterWhitespaceRefuse() {
        val good = body(listOf("mira"))
        assertFalse(matches(original, body(listOf("mira"), "A different utterance")))
        assertFalse(matches(original, body(listOf("mira"), op = "give")))
        assertFalse(matches(original, good.replace("\"op\":\"say\",", "")))
        assertFalse(matches(original, good.replace("\"op\":\"say\",", "\"op\":\"say\",\"extra\":true,")))
        assertFalse(matches(original, "{\"commands\":[{\"text\":" + quote(question) + ",\"op\":\"say\",\"audience\":[\"mira\"]}]}"))
        for (candidate in listOf(" " + good, good + " ", good + "\n", good + "x", good.dropLast(1))) assertFalse(matches(original, candidate))
    }

    @Test fun everyRustRegexMetacharacterRemainsLiteralJsonData() {
        val literal = "\\.+*?()|[]{}^$ / \" \n\t雪🦉 <>&='"
        val schema = JsonObject().apply { addProperty("const", literal) }.toString()
        assertEquals("\"<>&='\"", quote("<>&='"))
        assertTrue(matches(schema, quote(literal)))
        assertFalse(matches(schema, quote(literal.replace("*", "anything"))))
        assertFalse(matches(schema, "\"prefix\""))
    }

    @Test fun integerBooleanAndBudgetedNestedLiteralsUseCanonicalJson() {
        for (number in listOf(Long.MIN_VALUE, -1L, 0L, 1L, Long.MAX_VALUE)) {
            val schema = JsonObject().apply { addProperty("type", "integer"); addProperty("const", number) }.toString()
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
        val schema = JsonParser.parseString(original).asJsonObject
        val audience = jsonObject(properties(schema).get("audience"))
        audience.addProperty("maxItems", 0); assertNull(finiteSchemaRegex(schema.toString()))
        audience.addProperty("maxItems", 4); audience.addProperty("minItems", 2); assertNull(finiteSchemaRegex(schema.toString()))
        audience.addProperty("minItems", 1); audience.add("items", JsonObject().apply { add("enum", strings(listOf("foreign"))) })
        assertNull(finiteSchemaRegex(schema.toString()))
        audience.add("items", JsonObject().apply { addProperty("type", "string") }); assertNotNull(finiteSchemaRegex(schema.toString()))
        audience.add("items", JsonObject().apply { addProperty("type", "integer") }); assertNull(finiteSchemaRegex(schema.toString()))
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
            """{"const":null}""", """{"const":1.0}""", """{"const":1.5}""", """{"const":1e2}""", """{"const":NaN}""",
            """{"const":9223372036854775808}""", """{'const':'a'}""", """{const:"a"}""",
            """{"const":"a",}""", """{"const":[1,]}""", """{"const":"a"} // comment""",
            """{"const":"a"} {}""", """{"const":01}""", "null", "[]", "", "{")) assertNull(finiteSchemaRegex(schema))
    }

    @Test fun duplicateDecodedKeysAndUnpairedSurrogatesRefuse() {
        for (schema in listOf("""{"const":"a","const":"b"}""", """{"const":"a","con\u0073t":"b"}""",
            """{"const":{"a":1,"\u0061":2}}""", """{"const":"\uD800"}""", """{"const":"\uDC00"}""")) assertNull(finiteSchemaRegex(schema))
        assertNull(finiteSchemaRegex("{\"const\":\"" + '\uD800' + "\"}"))
        assertTrue(matches("""{"const":"\uD83E\uDD89"}""", quote("🦉")))
    }

    @Test fun depthTwelveNode512InputAndRegexUtf8BudgetsRefuseBeforeOverflow() {
        fun nested(depth: Int) = "{\"const\":" + "[".repeat(depth) + "0" + "]".repeat(depth) + "}"
        assertNotNull(finiteSchemaRegex(nested(11)))
        assertNull(finiteSchemaRegex(nested(12)))
        fun many(count: Int) = JsonObject().apply { add("enum", strings((0 until count).map { it.toString() })) }.toString()
        assertNotNull(finiteSchemaRegex(many(510)))
        assertNull(finiteSchemaRegex(many(511)))
        assertNull(finiteSchemaRegex(JsonObject().apply { addProperty("const", "x".repeat(32768)) }.toString()))
        assertNull(finiteSchemaRegex(JsonObject().apply { addProperty("const", "雪".repeat(11000)) }.toString()))
        assertNotNull(finiteSchemaRegex(JsonObject().apply { addProperty("const", ".".repeat(16000)) }.toString()))
        assertNull(finiteSchemaRegex(JsonObject().apply { addProperty("const", ".".repeat(16380)) }.toString()))
    }

    @Test fun inputSchemaIsImmutableAndNoDomainNamesSelectRepresentation() {
        val source = JsonParser.parseString(original).asJsonObject
        val before = source.toString()
        val result = finiteSchemaRegex(before)
        assertEquals(before, source.toString())
        assertEquals(result, finiteSchemaRegex(before))
        assertTrue(matches("""{"const":"an arbitrary literal unrelated to actors or actions"}""", quote("an arbitrary literal unrelated to actors or actions")))
        assertNull(finiteSchemaRegex("""{"op":"say","text":"a model claim","grant":true}"""))
    }

    /** Native pressure input only: Java's recursive matcher is not the native pressure oracle. */
    private fun exportPressurePatternIfRequested(schema: String, regex: String, spaces: Int) {
        val name = System.getenv("LOCALLORE_FINITE_PRESSURE_OUTPUT") ?: return
        val target = Path.of(name)
        require(target.isAbsolute && !Files.isSymbolicLink(target))
        val positive = JsonArray().apply {
            add(JsonObject().apply { addProperty("id", "canonical"); addProperty("json", quote(" ".repeat(spaces))) })
            add(JsonObject().apply { addProperty("id", "escaped"); addProperty("json", "\"" + "\\u0020".repeat(spaces) + "\"") })
        }
        val negative = JsonArray().apply {
            listOf(quote(" ".repeat(spaces - 1)), quote(" ".repeat(spaces - 1) + "x"), "\"" + " ".repeat(spaces)).forEachIndexed { index, text ->
                add(JsonObject().apply { addProperty("id", "negative-$index"); addProperty("json", text) })
            }
        }
        val corpus = JsonObject().apply {
            addProperty("version", 1); addProperty("scope", "locallore_llguidance_oracle_v1")
            add("cases", JsonArray().apply { add(JsonObject().apply {
                addProperty("id", "space-budget-boundary"); addProperty("schema_json", schema)
                add("positives", positive); add("negatives", negative)
            }) }); add("refusals", JsonArray())
        }.toString()
        val patterns = JsonObject().apply {
            addProperty("version", 1); addProperty("scope", "locallore_finite_regex_corpus_v1")
            addProperty("source_corpus_sha256", sha(localUtf8(corpus)))
            add("cases", JsonArray().apply { add(JsonObject().apply {
                addProperty("index", 0); addProperty("schema_sha256", sha(localUtf8(schema))); addProperty("regex", regex)
            }) })
        }.toString()
        val wire = localUtf8(JsonObject().apply {
            addProperty("version", 1); addProperty("scope", "locallore_finite_pressure_v1")
            addProperty("spaces", spaces); addProperty("regex_bytes", localUtf8(regex).size)
            addProperty("corpus_json", corpus); addProperty("patterns_json", patterns)
        }.toString())
        require(wire.size <= 262144)
        Files.write(target, wire, StandardOpenOption.CREATE_NEW, StandardOpenOption.WRITE)
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
        val corpus = jsonObject(JsonParser.parseString(localText(bytes, 1_048_576)))
        require(corpus.keySet() == setOf("version", "scope", "cases", "refusals"))
        require(jsonInteger(corpus.get("version")) == 1L)
        require(jsonString(corpus.get("scope")) == "locallore_llguidance_oracle_v1")
        val cases = jsonArray(corpus.get("cases"))
        val refusals = jsonArray(corpus.get("refusals"))
        require(cases.size() in 1..16 && refusals.size() in 0..16)
        val result = JsonArray()
        val caseIds = mutableSetOf<String>()
        var sampleCount = 0
        for (index in 0 until cases.size()) {
            val case = jsonObject(cases.get(index))
            require(case.keySet() == setOf("id", "schema_json", "positives", "negatives"))
            val id = jsonString(case.get("id"))
            require(id.matches(Regex("[a-z][a-z0-9-]{0,47}")) && caseIds.add(id))
            val schema = jsonString(case.get("schema_json"))
            require(localUtf8(schema).size in 1..16_384)
            val regex = finiteSchemaRegex(schema) ?: error("Unsupported finite case")
            val compiled = Pattern.compile(regex)
            val sampleIds = mutableSetOf<String>()
            for (section in listOf("positives", "negatives")) {
                val samples = jsonArray(case.get(section))
                require(samples.size() in 1..256)
                sampleCount += samples.size(); require(sampleCount <= 256)
                for (sampleIndex in 0 until samples.size()) {
                    val sample = jsonObject(samples.get(sampleIndex))
                    require(sample.keySet() == setOf("id", "json"))
                    val sampleId = jsonString(sample.get("id"))
                    require(sampleId.matches(Regex("[a-z][a-z0-9-]{0,47}")) && sampleIds.add(sampleId))
                    val candidate = jsonString(sample.get("json"))
                    require(localUtf8(candidate).size in 1..16_384)
                    require(compiled.matcher(candidate).matches() == (section == "positives")) { "Original finite sample changed" }
                }
            }
            result.add(JsonObject().apply {
                addProperty("index", index); addProperty("schema_sha256", sha(localUtf8(schema))); addProperty("regex", regex)
            })
        }
        val refusalIds = mutableSetOf<String>()
        for (index in 0 until refusals.size()) {
            val refusal = jsonObject(refusals.get(index))
            require(refusal.keySet() == setOf("id", "error", "provider_calls", "canon_unchanged"))
            val id = jsonString(refusal.get("id"))
            require(id.matches(Regex("[a-z][a-z0-9-]{0,47}")) && refusalIds.add(id))
            require(jsonString(refusal.get("error")) in setOf("ClarificationRequired", "TooLarge"))
            require(jsonInteger(refusal.get("provider_calls")) == 0L)
            val unchanged = requireNotNull(refusal.get("canon_unchanged"))
            require(unchanged.isJsonPrimitive && unchanged.asJsonPrimitive.isBoolean && unchanged.asBoolean)
        }
        // All semantic/size failures above occur before opening the create-only output.
        // Root also strictly validates raw duplicate keys, the exact source corpus and artifact.
        val encoded = localUtf8(JsonObject().apply {
            addProperty("version", 1); addProperty("scope", "locallore_finite_regex_corpus_v1")
            addProperty("source_corpus_sha256", sha(bytes)); add("cases", result)
        }.toString())
        require(encoded.size <= 2_097_152)
        Files.write(target, encoded, StandardOpenOption.CREATE_NEW, StandardOpenOption.WRITE)
    }

    private fun jsonObject(element: JsonElement?): JsonObject { val value = requireNotNull(element); require(value.isJsonObject); return value.asJsonObject }
    private fun jsonArray(element: JsonElement?): JsonArray { val value = requireNotNull(element); require(value.isJsonArray); return value.asJsonArray }
    private fun jsonString(element: JsonElement?): String { val value = requireNotNull(element); require(value.isJsonPrimitive && value.asJsonPrimitive.isString); return value.asString }
    private fun jsonInteger(element: JsonElement?): Long {
        val value = requireNotNull(element)
        require(value.isJsonPrimitive && value.asJsonPrimitive.isNumber && value.asString.matches(Regex("-?(?:0|[1-9][0-9]*)")))
        return requireNotNull(value.asString.toLongOrNull())
    }

    private fun sha(bytes: ByteArray): String = MessageDigest.getInstance("SHA-256").digest(bytes)
        .joinToString("") { "%02x".format(it) }
}

/* Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0 */
package org.locallore.app

import com.google.gson.JsonArray
import com.google.gson.JsonElement
import com.google.gson.JsonObject
import com.google.gson.JsonParser
import com.google.gson.JsonPrimitive

/** A canonical finite representation only. The original schema/engine still validates outcomes. */
internal fun finiteSchemaRegex(schemaJson: String): String? = try {
    require(schemaJson.length in 1..FINITE_BYTES)
    require(localUtf8(schemaJson).size in 1..FINITE_BYTES)
    FiniteJsonSyntax(schemaJson).check()
    val parsed = JsonParser.parseString(schemaJson).objectValue()
    FiniteText().apply { append("\\A(?:"); schema(parsed); append(")\\z") }.text()
} catch (_: Exception) { null }

private const val FINITE_BYTES = 32_768
private const val FINITE_NODES = 512
private const val FINITE_DEPTH = 12
private const val REGEX_META = "\\.+*?()|[]{}^$"

/** Every append is budgeted before mutation, including escaped literals and grouping. */
private class FiniteText {
    private val output = StringBuilder()
    private var bytes = 0
    fun append(value: String) {
        require(value.length <= FINITE_BYTES - bytes)
        val size = localUtf8(value).size
        require(size <= FINITE_BYTES - bytes)
        bytes += size; output.append(value)
    }
    fun text(): String = output.toString()
    fun escaped(value: String) {
        var start = 0
        value.forEachIndexed { index, char ->
            if (char in REGEX_META) {
                append(value.substring(start, index)); append("\\"); append(char.toString()); start = index + 1
            }
        }
        append(value.substring(start))
    }
    fun schema(value: JsonObject) {
        val keys = value.namesSet()
        when {
            value.has("const") || value.has("enum") -> {
                val choices = finiteChoices(value)
                append("(?:")
                choices.forEachIndexed { index, choice -> if (index > 0) append("|"); escaped(choice) }
                append(")")
            }
            value.has("oneOf") -> {
                require(keys == setOf("oneOf"))
                val choices = value.get("oneOf").arrayValue()
                require(choices.size() == 1)
                schema(choices.get(0).objectValue())
            }
            value.get("type")?.stringValue() == "object" -> {
                require(keys == setOf("type", "properties", "required", "additionalProperties"))
                val additional = requireNotNull(value.get("additionalProperties"))
                require(additional.isJsonPrimitive && additional.asJsonPrimitive.isBoolean && !additional.asBoolean)
                val properties = value.get("properties").objectValue()
                val required = value.get("required").arrayValue()
                val names = (0 until required.size()).map { required.get(it).stringValue() }
                require(names.toSet().size == names.size && names.toSet() == properties.namesSet())
                escaped("{")
                properties.namesSet().sorted().forEachIndexed { index, name ->
                    if (index > 0) escaped(",")
                    escaped(quoted(name) + ":")
                    schema(properties.get(name).objectValue())
                }
                escaped("}")
            }
            value.get("type")?.stringValue() == "array" -> {
                require(keys == setOf("type", "items", "minItems", "maxItems"))
                require(value.get("minItems").finiteInteger() == 1L && value.get("maxItems").finiteInteger() == 1L)
                escaped("["); schema(value.get("items").objectValue()); escaped("]")
            }
            else -> error("Unsupported")
        }
    }
}

private fun JsonObject.namesSet(): Set<String> = keySet().toSet()
private fun JsonElement?.objectValue(): JsonObject { val value = requireNotNull(this); require(value.isJsonObject); return value.asJsonObject }
private fun JsonElement?.arrayValue(): JsonArray { val value = requireNotNull(this); require(value.isJsonArray); return value.asJsonArray }
private fun JsonElement?.stringValue(): String { val value = requireNotNull(this); require(value.isJsonPrimitive && value.asJsonPrimitive.isString); return value.asString }
private fun JsonElement?.integerOrNull(): Long? {
    val value = this ?: return null
    return if (value.isJsonPrimitive && value.asJsonPrimitive.isNumber && value.asString.matches(Regex("-?(?:0|[1-9][0-9]*)")))
        value.asString.toLongOrNull() else null
}
private fun JsonElement?.finiteInteger(): Long = integerOrNull() ?: error("Integer")
private fun quoted(value: String): String = JsonPrimitive(value).toString()
private fun literalType(value: JsonElement?, type: String): Boolean = value != null && when (type) {
    "string" -> value.isJsonPrimitive && value.asJsonPrimitive.isString
    "integer" -> value.integerOrNull() != null
    "boolean" -> value.isJsonPrimitive && value.asJsonPrimitive.isBoolean
    "array" -> value.isJsonArray
    "object" -> value.isJsonObject
    else -> false
}

private fun literalJson(value: JsonElement?): String = FiniteText().apply { literal(value) }.text()
private fun FiniteText.literal(element: JsonElement?) {
    val value = requireNotNull(element)
    require(!value.isJsonNull)
    when {
        value.isJsonPrimitive -> {
            val primitive = value.asJsonPrimitive
            when {
                primitive.isString -> { localUtf8(primitive.asString); append(quoted(primitive.asString)) }
                primitive.isBoolean -> append(primitive.asBoolean.toString())
                primitive.isNumber -> append(value.finiteInteger().toString())
                else -> error("Literal")
            }
        }
        value.isJsonArray -> {
            val array = value.asJsonArray
            append("[")
            for (index in 0 until array.size()) { if (index > 0) append(","); literal(array.get(index)) }
            append("]")
        }
        value.isJsonObject -> {
            val objectValue = value.asJsonObject
            append("{")
            objectValue.namesSet().sorted().forEachIndexed { index, key ->
                if (index > 0) append(",")
                append(quoted(key)); append(":"); literal(objectValue.get(key))
            }
            append("}")
        }
        else -> error("Literal")
    }
}

/** Validate every enum member against every supported sibling constraint; never filter it. */
private fun finiteChoices(schema: JsonObject): List<String> {
    val keys = schema.namesSet()
    if (schema.has("const")) {
        require(keys == setOf("const") || keys == setOf("const", "type"))
        val value = schema.get("const")
        if (schema.has("type")) require(literalType(value, schema.get("type").stringValue()))
        return listOf(literalJson(value))
    }
    require(schema.has("enum") && keys.all { it in setOf("enum", "type", "items", "minItems", "maxItems") })
    val values = schema.get("enum").arrayValue()
    require(values.size() in 1..FINITE_NODES)
    val type = if (schema.has("type")) schema.get("type").stringValue() else null
    require(type == null || type in setOf("string", "array"))
    val array = type == "array" || schema.has("items") || schema.has("minItems") || schema.has("maxItems")
    val min = if (schema.has("minItems")) schema.get("minItems").finiteInteger() else 0L
    val max = if (schema.has("maxItems")) schema.get("maxItems").finiteInteger() else FINITE_NODES.toLong()
    require(min in 0..FINITE_NODES.toLong() && max in min..FINITE_NODES.toLong())
    val items = if (schema.has("items")) schema.get("items").objectValue() else null
    if (items != null) validateFiniteItem(items)
    val result = (0 until values.size()).map { index ->
        val value = requireNotNull(values.get(index))
        require((value.isJsonPrimitive && value.asJsonPrimitive.isString) || value.isJsonArray)
        if (type != null) require(literalType(value, type))
        if (array) {
            require(value.isJsonArray && value.asJsonArray.size().toLong() in min..max)
            if (items != null) for (item in value.asJsonArray) require(matchesFiniteItem(item, items))
        }
        literalJson(value)
    }
    require(result.toSet().size == result.size)
    return result
}

private fun validateFiniteItem(schema: JsonObject) {
    when {
        schema.namesSet() == setOf("type") -> {
            val type = schema.get("type").stringValue()
            require(type in setOf("string", "integer", "boolean", "array", "object"))
        }
        schema.has("const") || schema.has("enum") -> finiteChoices(schema)
        schema.namesSet() == setOf("oneOf") -> {
            val choices = schema.get("oneOf").arrayValue()
            require(choices.size() == 1)
            validateFiniteItem(choices.get(0).objectValue())
        }
        else -> error("Items")
    }
}

private fun matchesFiniteItem(value: JsonElement, schema: JsonObject): Boolean = when {
    schema.namesSet() == setOf("type") -> literalType(value, schema.get("type").stringValue())
    schema.has("const") || schema.has("enum") -> literalJson(value) in finiteChoices(schema)
    schema.namesSet() == setOf("oneOf") -> {
        val alternatives = schema.get("oneOf").arrayValue()
        require(alternatives.size() == 1)
        matchesFiniteItem(value, alternatives.get(0).objectValue())
    }
    else -> error("Items")
}

/** Strict guard before Gson parsing, not an alternative schema or gameplay interpreter. */
private class FiniteJsonSyntax(private val input: String) {
    private var at = 0
    private var nodes = 0
    private fun space() { while (at < input.length && input[at] in " \t\r\n") at++ }
    private fun take(char: Char): Boolean = (at < input.length && input[at] == char).also { if (it) at++ }
    fun check() { value(0); space(); require(at == input.length) }
    private fun value(depth: Int) {
        require(depth <= FINITE_DEPTH && ++nodes <= FINITE_NODES)
        space(); require(at < input.length)
        when (input[at]) {
            '{' -> {
                at++; space(); val keys = mutableSetOf<String>()
                if (!take('}')) do {
                    space(); val key = string(); require(keys.add(key)); space(); require(take(':'))
                    value(depth + 1); space()
                    if (take('}')) break
                    require(take(','))
                } while (true)
            }
            '[' -> {
                at++; space()
                if (!take(']')) do {
                    value(depth + 1); space()
                    if (take(']')) break
                    require(take(','))
                } while (true)
            }
            '"' -> string()
            't' -> word("true")
            'f' -> word("false")
            'n' -> word("null")
            else -> {
                val start = at; take('-')
                if (!take('0')) { require(at < input.length && input[at] in '1'..'9'); while (at < input.length && input[at] in '0'..'9') at++ }
                require(input.substring(start, at).toLongOrNull() != null)
            }
        }
    }
    private fun word(word: String) { require(input.startsWith(word, at)); at += word.length }
    private fun string(): String {
        val start = at; require(take('"'))
        while (at < input.length) {
            val char = input[at++]
            if (char == '"') return JsonParser.parseString(input.substring(start, at)).stringValue().also { localUtf8(it) }
            require(char.code >= 32)
            if (char == '\\') {
                require(at < input.length)
                when (input[at++]) {
                    '"', '\\', '/', 'b', 'f', 'n', 'r', 't' -> Unit
                    'u' -> { require(at + 4 <= input.length && input.substring(at, at + 4).all { it in "0123456789abcdefABCDEF" }); at += 4 }
                    else -> error("Escape")
                }
            }
        }
        error("String")
    }
}

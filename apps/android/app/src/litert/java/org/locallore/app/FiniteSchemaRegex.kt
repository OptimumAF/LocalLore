/* Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0 */
package org.locallore.app

import org.json.JSONArray
import org.json.JSONObject
import org.json.JSONTokener

/** A canonical finite representation only. The original schema/engine still validates outcomes. */
internal fun finiteSchemaRegex(schemaJson: String): String? = try {
    require(schemaJson.length in 1..FINITE_BYTES)
    require(localUtf8(schemaJson).size in 1..FINITE_BYTES)
    FiniteJsonSyntax(schemaJson).check()
    val parsed = JSONObject(schemaJson)
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
    fun schema(value: JSONObject) {
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
                val choices = value.get("oneOf") as? JSONArray ?: error("Shape")
                require(choices.length() == 1)
                schema(choices.get(0) as? JSONObject ?: error("Shape"))
            }
            value.opt("type") == "object" -> {
                require(keys == setOf("type", "properties", "required", "additionalProperties"))
                require(value.get("additionalProperties") is Boolean && value.get("additionalProperties") == false)
                val properties = value.get("properties") as? JSONObject ?: error("Shape")
                val required = value.get("required") as? JSONArray ?: error("Shape")
                val names = (0 until required.length()).map { required.get(it) as? String ?: error("Shape") }
                require(names.toSet().size == names.size && names.toSet() == properties.namesSet())
                escaped("{")
                properties.namesSet().sorted().forEachIndexed { index, name ->
                    if (index > 0) escaped(",")
                    escaped(JSONObject.quote(name) + ":")
                    schema(properties.get(name) as? JSONObject ?: error("Shape"))
                }
                escaped("}")
            }
            value.opt("type") == "array" -> {
                require(keys == setOf("type", "items", "minItems", "maxItems"))
                require(value.get("minItems").finiteInteger() == 1L && value.get("maxItems").finiteInteger() == 1L)
                escaped("["); schema(value.get("items") as? JSONObject ?: error("Shape")); escaped("]")
            }
            else -> error("Unsupported")
        }
    }
}

private fun JSONObject.namesSet(): Set<String> = keys().asSequence().toSet()
private fun Any.finiteInteger(): Long = when (this) { is Int -> toLong(); is Long -> this; else -> error("Integer") }
private fun literalType(value: Any, type: String): Boolean = when (type) {
    "string" -> value is String
    "integer" -> value is Int || value is Long
    "boolean" -> value is Boolean
    "array" -> value is JSONArray
    "object" -> value is JSONObject
    else -> false
}

private fun literalJson(value: Any): String = FiniteText().apply { literal(value) }.text()
private fun FiniteText.literal(value: Any) {
    require(value !== JSONObject.NULL)
    when (value) {
        is String -> { localUtf8(value); append(JSONObject.quote(value)) }
        is Int, is Long, is Boolean -> append(value.toString())
        is JSONArray -> {
            append("[")
            for (index in 0 until value.length()) { if (index > 0) append(","); literal(value.get(index)) }
            append("]")
        }
        is JSONObject -> {
            append("{")
            value.namesSet().sorted().forEachIndexed { index, key ->
                if (index > 0) append(",")
                append(JSONObject.quote(key)); append(":"); literal(value.get(key))
            }
            append("}")
        }
        else -> error("Literal")
    }
}

/** Validate every enum member against every supported sibling constraint; never filter it. */
private fun finiteChoices(schema: JSONObject): List<String> {
    val keys = schema.namesSet()
    if (schema.has("const")) {
        require(keys == setOf("const") || keys == setOf("const", "type"))
        val value = schema.get("const")
        if (schema.has("type")) require(literalType(value, schema.get("type") as? String ?: error("Type")))
        return listOf(literalJson(value))
    }
    require(schema.has("enum") && keys.all { it in setOf("enum", "type", "items", "minItems", "maxItems") })
    val values = schema.get("enum") as? JSONArray ?: error("Shape")
    require(values.length() in 1..FINITE_NODES)
    val type = if (schema.has("type")) schema.get("type") as? String ?: error("Type") else null
    require(type == null || type in setOf("string", "array"))
    val array = type == "array" || schema.has("items") || schema.has("minItems") || schema.has("maxItems")
    val min = if (schema.has("minItems")) schema.get("minItems").finiteInteger() else 0L
    val max = if (schema.has("maxItems")) schema.get("maxItems").finiteInteger() else FINITE_NODES.toLong()
    require(min in 0..FINITE_NODES.toLong() && max in min..FINITE_NODES.toLong())
    val items = if (schema.has("items")) schema.get("items") as? JSONObject ?: error("Items") else null
    if (items != null) validateFiniteItem(items)
    val result = (0 until values.length()).map { index ->
        val value = values.get(index)
        require(value is String || value is JSONArray)
        if (type != null) require(literalType(value, type))
        if (array) {
            require(value is JSONArray && value.length().toLong() in min..max)
            if (items != null) for (item in 0 until value.length()) require(matchesFiniteItem(value.get(item), items))
        }
        literalJson(value)
    }
    require(result.toSet().size == result.size)
    return result
}

private fun validateFiniteItem(schema: JSONObject) {
    when {
        schema.namesSet() == setOf("type") -> {
            val type = schema.get("type") as? String ?: error("Type")
            require(type in setOf("string", "integer", "boolean", "array", "object"))
        }
        schema.has("const") || schema.has("enum") -> finiteChoices(schema)
        schema.namesSet() == setOf("oneOf") -> {
            val choices = schema.get("oneOf") as? JSONArray ?: error("Shape")
            require(choices.length() == 1)
            validateFiniteItem(choices.get(0) as? JSONObject ?: error("Shape"))
        }
        else -> error("Items")
    }
}

private fun matchesFiniteItem(value: Any, schema: JSONObject): Boolean = when {
    schema.namesSet() == setOf("type") -> literalType(value, schema.get("type") as? String ?: error("Type"))
    schema.has("const") || schema.has("enum") -> literalJson(value) in finiteChoices(schema)
    schema.namesSet() == setOf("oneOf") -> {
        val alternatives = schema.get("oneOf") as? JSONArray ?: error("Shape")
        require(alternatives.length() == 1)
        matchesFiniteItem(value, alternatives.get(0) as? JSONObject ?: error("Shape"))
    }
    else -> error("Items")
}

/** Syntax/duplicate guard around org.json, not an alternative schema or gameplay interpreter. */
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
            if (char == '"') return (JSONTokener(input.substring(start, at)).nextValue() as String).also { localUtf8(it) }
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

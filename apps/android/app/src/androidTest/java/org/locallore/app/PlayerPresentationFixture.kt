/* Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0 */
package org.locallore.app

import org.json.JSONArray
import org.json.JSONObject

/** Synthetic protocol fixture adapter only; never used by a native acceptance oracle. */
internal fun presentationFixture(legacy: JSONObject): JSONObject {
    val scope = legacy.getJSONObject("scope")
    val head = legacy.getLong("revision")
    val observer = legacy.getJSONObject("player").get("observer")
    val turns = JSONArray()
    val receipts = legacy.getJSONArray("receipts")
    for (i in 0 until receipts.length()) {
        val receipt = receipts.getJSONObject(i)
        val request = receipt.getJSONObject("request")
        turns.put(JSONObject().put("original_scope", request.getJSONObject("scope"))
            .put("turn", request.getString("turn"))
            .put("event_ids", JSONArray().put(request.optLong("expected_revision", i.toLong()) + 1))
            .put("intent", request.getJSONObject("intent")).put("narration", receipt.getString("narration")))
    }
    val inventory = JSONObject()
    for (key in legacy.getJSONObject("inventory").keys().asSequence()) {
        inventory.put(key, JSONObject().put("owner", observer).put("quantity", 1)
            .put("return_to", JSONObject.NULL).put("healing", true))
    }
    return JSONObject().put("version", 2).put("domain_version", 1).put("scope", scope)
        .put("revision", head).put("rules", legacy.getString("rules"))
        .put("player", JSONObject().put("observer", observer).put("self_state", JSONObject()
            .put("name", "Synthetic player").put("location", "quay").put("alive", true).put("energy", 10)
            .put("abilities", JSONObject()).put("attributes", JSONObject()).put("injuries", JSONArray())
            .put("affiliations", JSONArray()).put("goals", JSONArray())))
        .put("inventory", inventory).put("turns", turns)
        .put("window", JSONObject().put("total", turns.length()).put("start", 0).put("end", turns.length()))
}

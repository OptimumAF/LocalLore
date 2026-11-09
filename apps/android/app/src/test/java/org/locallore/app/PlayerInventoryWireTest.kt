/* Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0 */
package org.locallore.app

import org.json.JSONObject
import org.junit.Assert.*
import org.junit.Test

/** The complete golden must first equal actual Rust Host output in the native cohort. */
class PlayerInventoryWireTest {
    private val scope = PlayDraftScope("inventory-native", "corrected")
    private val player = "a-inventory-native-player"
    private val expected = listOf(PlayerInventoryItem("carry-azure", 7), PlayerInventoryItem("carry-zinc", 3))

    private fun frame(): JSONObject {
        val stream = checkNotNull(javaClass.classLoader?.getResourceAsStream("native-player-inventory-v1.json"))
        return stream.bufferedReader(Charsets.UTF_8).use { JSONObject(it.readText()).getJSONObject("data") }
    }
    private fun read(value: JSONObject) = PlayerPresentationWire.decode(value, scope, 1)
    private fun malformed(value: JSONObject) {
        val original = value.toString()
        try {
            read(value)
            fail("Malformed inventory was accepted")
        } catch (failure: WorkspaceFailure) {
            assertEquals("Malformed", failure.category)
        }
        assertEquals(original, value.toString())
    }

    @Test fun genuineOpaqueDomainTwoGoldenRetainsEveryNativeOwnedStackWithoutInventingPotion() {
        val value = frame()
        val original = value.toString()
        val result = read(value)
        assertEquals(2, result.domainVersion)
        assertEquals(scope, result.scope)
        assertEquals(1L, result.revision)
        assertEquals(player, result.observer)
        assertEquals(expected, result.inventory)
        assertFalse(result.hasPotion)
        assertTrue(result.messages.isEmpty())
        assertFalse(result.inventory.any { it.id.contains("PRIVATE") || it.id == "potion" || it.id == "brass-key" })
        assertEquals(original, value.toString())
    }

    @Test fun sortedImmutableInventoryIsDetachedFromJsonAndPreservesStructuralQuantityBounds() {
        val value = frame()
        val rows = value.getJSONObject("inventory")
        // Reverse input order; order comes from exact IDs rather than JSONObject iteration.
        val reversed = JSONObject().put("carry-zinc", rows.getJSONObject("carry-zinc"))
            .put("carry-azure", rows.getJSONObject("carry-azure"))
        value.put("inventory", reversed)
        val result = read(value)
        assertEquals(expected, result.inventory)
        try {
            (result.inventory as MutableList<PlayerInventoryItem>).add(PlayerInventoryItem("forged", 1))
            fail("Inventory list is mutable")
        } catch (_: UnsupportedOperationException) { }
        reversed.getJSONObject("carry-azure").put("quantity", 0)
        reversed.getJSONObject("carry-zinc").put("quantity", 65535)
        assertEquals(expected, result.inventory)
        // Zero is deliberately a structural wire mutant, not a reachable native stack.
        assertEquals(listOf(PlayerInventoryItem("carry-azure", 0), PlayerInventoryItem("carry-zinc", 65535)),
            read(value).inventory)
        assertEquals(expected, result.inventory)
    }

    @Test fun knownEmptyInventoryIsDistinctFromAnAbsentOrNullRequiredWireObject() {
        val empty = frame().put("inventory", JSONObject())
        assertEquals(emptyList<PlayerInventoryItem>(), read(empty).inventory)
        assertFalse(read(empty).hasPotion)
        malformed(frame().also { it.remove("inventory") })
        malformed(frame().put("inventory", JSONObject.NULL))
    }

    @Test fun malformedPrivateOrLossyRowsRefuseTheWholeFrameWithoutFilteringThemAway() {
        val mutations: List<(JSONObject) -> Unit> = listOf(
            { it.getJSONObject("inventory").getJSONObject("carry-azure").put("owner", "another-valid-actor") },
            { it.getJSONObject("inventory").getJSONObject("carry-azure").put("quantity", true) },
            { it.getJSONObject("inventory").getJSONObject("carry-azure").put("quantity", -1) },
            { it.getJSONObject("inventory").getJSONObject("carry-azure").put("quantity", 65536) },
            { it.getJSONObject("inventory").getJSONObject("carry-azure").put("quantity", 1.5) },
            { it.getJSONObject("inventory").getJSONObject("carry-azure").put("quantity", "7") },
            { it.getJSONObject("inventory").getJSONObject("carry-azure").remove("return_to") },
            { it.getJSONObject("inventory").getJSONObject("carry-zinc").put("return_to", true) },
            { it.getJSONObject("inventory").getJSONObject("carry-azure").put("healing", 1) },
            { it.getJSONObject("inventory").getJSONObject("carry-azure").put("name", "PRIVATE-UNTRUSTED-NAME") },
            { it.getJSONObject("inventory").put("bad item id", it.getJSONObject("inventory").getJSONObject("carry-azure")) },
        )
        for (mutate in mutations) malformed(frame().also(mutate))
    }

    @Test fun scopeHeadAndObservedOwnerMismatchCannotPublishEvenAnOtherwiseValidInventory() {
        for ((selected, revision) in listOf(
            PlayDraftScope("another-story", "corrected") to 1L,
            PlayDraftScope("inventory-native", "another-branch") to 1L,
            scope to 2L,
        )) {
            try {
                PlayerPresentationWire.decode(frame(), selected, revision)
                fail("A different selection accepted inventory")
            } catch (failure: WorkspaceFailure) {
                assertEquals("Malformed", failure.category)
            }
        }
        malformed(frame().also { it.getJSONObject("player").put("observer", "different-valid-player") })
    }
}

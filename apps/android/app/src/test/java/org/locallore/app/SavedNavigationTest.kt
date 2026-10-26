/* Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0 */
package org.locallore.app

import org.junit.Assert.*
import org.junit.Test

/** Pure navigation intent only; these checks do not execute a lifecycle, catalog or turn. */
class SavedNavigationTest {
    private val previous = PlayDraftScope("story-b", "child-2")
    private val selected = SavedStory("story-a", "main", "Display title", 7)

    @Test fun wireContainsOnlyExactVersionAndOriginalStableIds() {
        for (scope in listOf(previous, PlayDraftScope("A_0-z", "Z"), PlayDraftScope("a".repeat(64), "_".repeat(64)))) {
            val wire = encodeNavigationHint(scope)
            assertEquals(listOf(1, scope.story, scope.branch), wire)
            assertTrue(checkNotNull(wire)[0] is Int)
            assertEquals(scope, decodeNavigationHint(wire))
        }
        assertNull(encodeNavigationHint(null))
    }

    @Test fun invalidNativeIdsAreRefusedWholeWithoutTrimmingRepairOrTruncation() {
        val invalid = listOf("", "a".repeat(65), " story", "story ", "a/b", "a.b", "a:b", "a\\b",
            "a\n", "a\u0000", "é", "🌊", "\uD800", "\uDC00", "a\u2028b")
        for (id in invalid) {
            for (scope in listOf(PlayDraftScope(id, "main"), PlayDraftScope("story", id))) {
                assertNull("encode accepted invalid ID", encodeNavigationHint(scope))
                assertNull("decode accepted invalid ID", decodeNavigationHint(listOf(1, scope.story, scope.branch)))
            }
        }
    }

    @Test fun decoderRejectsWrongContainersLengthsTypesAndVersionRepresentations() {
        val bad: List<Any?> = listOf(
            null, "1,story,main", arrayOf<Any>(1, "story", "main"),
            mapOf("version" to 1, "story" to "story", "branch" to "main"),
            emptyList<Any>(), listOf(1, "story"), listOf(1, "story", "main", 0),
            listOf(null, "story", "main"), listOf(true, "story", "main"),
            listOf(1L, "story", "main"), listOf(1.0, "story", "main"),
            listOf("1", "story", "main"), listOf(0, "story", "main"), listOf(2, "story", "main"),
            listOf(1, null, "main"), listOf(1, "story", null),
            listOf(1, 123, "main"), listOf(1, "story", true),
            listOf(1, listOf("story"), "main"), listOf(1, "story", mapOf("branch" to "main")),
        )
        for (value in bad) assertNull("Malformed saved navigation accepted", decodeNavigationHint(value))
    }

    @Test fun navigationWireCannotSmuggleRevisionTurnTextOrProviderWork() {
        for (extra in listOf<Any>(7L, "turn-key", "unsent private words", mapOf("prepare" to true))) {
            assertNull(decodeNavigationHint(listOf(1, previous.story, previous.branch, extra)))
        }
        val original = listOf<Any>(1, previous.story, previous.branch)
        assertEquals(previous, decodeNavigationHint(original))
        assertEquals(listOf(1, "story-b", "child-2"), original)
    }

    @Test fun coherentActualSelectionReplacesPendingHintEvenDuringBusyOrRecovery() {
        for (busy in listOf(false, true)) for (recovery in listOf(false, true)) {
            val state = ShellState(persistent = true, selectedStory = selected, busy = busy,
                recoveryRequired = recovery)
            assertEquals(PlayDraftScope(selected.story, selected.branch), navigationHintToSave(previous, state))
        }
        val sameIdsNewHead = selected.copy(title = "Another display title", revision = Long.MAX_VALUE)
        assertEquals(navigationHintToSave(previous, ShellState(persistent = true, selectedStory = selected)),
            navigationHintToSave(null, ShellState(persistent = true, selectedStory = sameIdsNewHead)))
    }

    @Test fun unresolvedStartupAndRecoveryPreserveThePreviousHintThroughRepeatedSaves() {
        for ((busy, recovery) in listOf(true to false, false to true, true to true)) {
            val pending = ShellState(persistent = true, selectedStory = null, busy = busy,
                recoveryRequired = recovery)
            val once = navigationHintToSave(previous, pending)
            assertEquals(previous, once)
            val restored = decodeNavigationHint(encodeNavigationHint(once))
            assertEquals(previous, navigationHintToSave(restored, pending))
        }
        assertNull(navigationHintToSave(null, ShellState(persistent = true, busy = true)))
    }

    @Test fun settledEmptyAndNonpersistentStatesCannotRetainAnOldSelection() {
        assertNull(navigationHintToSave(previous, ShellState(persistent = true)))
        for (busy in listOf(false, true)) for (recovery in listOf(false, true)) {
            assertNull(navigationHintToSave(previous, ShellState(persistent = false,
                selectedStory = selected, busy = busy, recoveryRequired = recovery)))
        }
        // Settling empty destroys the hint; a later unresolved save cannot resurrect it.
        val empty = navigationHintToSave(previous, ShellState(persistent = true))
        assertNull(navigationHintToSave(empty, ShellState(persistent = true, recoveryRequired = true)))
    }

    @Test fun invalidCurrentOrPendingScopeNeverFallsBackToAnUnrelatedPreviousHint() {
        assertNull(navigationHintToSave(previous, ShellState(persistent = true,
            selectedStory = selected.copy(branch = "invalid/branch"), busy = true)))
        assertNull(navigationHintToSave(PlayDraftScope("invalid story", "main"),
            ShellState(persistent = true, recoveryRequired = true)))
        assertNull(navigationHintToSave(PlayDraftScope("story", "m".repeat(65)),
            ShellState(persistent = true, busy = true)))
    }
}

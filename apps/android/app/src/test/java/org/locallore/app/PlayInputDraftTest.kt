/* Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0 */
package org.locallore.app

import org.junit.Assert.*
import org.junit.Test

/** Pure unsent UI state/codec checks; no lifecycle, storage, provider or engine is executed. */
class PlayInputDraftTest {
    private val first = PlayDraftScope("story-a", "root")
    private val otherStory = PlayDraftScope("story-b", "root")
    private val otherBranch = PlayDraftScope("story-a", "fork")
    private val dialogue = PlayInput(PlayInputKind.DIALOGUE, "  Original words.\n\tStill just words.  ")

    @Test fun pendingSelectionRetainsRestoredDraftUntilScopeIsActuallyResolved() {
        val draft = PlayDraft(first, dialogue)
        assertSame(draft, draft.resolve(null, pending = true))
        assertSame(draft, draft.resolve(otherStory, pending = true))
        assertSame(draft, draft.resolve(otherBranch, pending = true))
        assertSame(draft, draft.resolve(first.copy(), pending = false))
        assertEquals(dialogue, draft.resolve(first, pending = true).input)
    }

    @Test fun settledStoryBranchAndNullChangesClearOnceAndDoNotKeepAHiddenPerStoryCache() {
        val draft = PlayDraft(first, dialogue, textNotRestored = true)
        for (scope in listOf(otherStory, otherBranch, null)) {
            val switched = draft.resolve(scope, pending = false)
            assertEquals(PlayDraft(scope), switched)
            assertEquals(PlayDraft(first), switched.resolve(first, pending = false))
        }
        // A new revision/title is not an input to this contract. Equal stable IDs retain it.
        assertSame(draft, draft.resolve(PlayDraftScope(first.story, first.branch), pending = false))
    }

    @Test fun editsRequireBothTheRenderedAndCurrentScopesToMatchTheDraft() {
        val draft = PlayDraft(first, dialogue, textNotRestored = true)
        val replacement = PlayInput(PlayInputKind.ACTION, "An unsubmitted action")
        for ((expected, current) in listOf(
            first to otherStory, first to otherBranch, otherStory to first,
            otherStory to otherStory, null to first, first to null, null to null,
        )) {
            assertSame(draft, draft.edit(expected, current, replacement))
        }
        val edited = draft.edit(first.copy(), first.copy(), replacement)
        assertEquals(PlayDraft(first, replacement), edited)
        assertEquals(dialogue, draft.input)
        assertTrue(draft.textNotRestored)
    }

    @Test fun unscopedDemoMayEditLiveButNeverProducesSavedData() {
        val demo = PlayDraft().edit(null, null, dialogue)
        assertEquals(dialogue, demo.input)
        assertNull(savePlayDraft(demo))
        assertEquals(PlayDraft(first), demo.resolve(first, pending = false))
    }

    @Test fun exactDialogueWhitespaceKindAndUtf8ContentsRoundTripWithoutSending() {
        val input = dialogue.copy(text = dialogue.text + " café 🌊")
        val draft = PlayDraft(first, input)
        val saved = checkNotNull(savePlayDraft(draft))
        assertEquals(listOf(1, "story-a", "root", "dialogue", input.text, "full"), saved)
        assertEquals(draft, restorePlayDraft(saved))
        assertEquals(input.text, draft.input.text)
        assertTrue(validPlayInput(input))
    }

    @Test fun boundedBlankOrControlBearingEditorTextIsNotConfusedWithSendEligibility() {
        for (text in listOf("", " \t\n ", "not sendable\u0000but unsent", "\u0085")) {
            val draft = PlayDraft(first, PlayInput(PlayInputKind.ACTION, text))
            assertEquals(draft, restorePlayDraft(savePlayDraft(draft)))
            assertFalse(validPlayInput(draft.input))
        }
    }

    @Test fun savedTextBoundIsUtf8BasedAndDoesNotChangeTheExistingSendBound() {
        for (text in listOf("a".repeat(8192), "é".repeat(4096), "🌊".repeat(2048))) {
            val draft = PlayDraft(first, PlayInput(PlayInputKind.DIALOGUE, text))
            val saved = checkNotNull(savePlayDraft(draft))
            assertEquals("full", saved[5])
            assertEquals(draft, restorePlayDraft(saved))
            assertFalse(validPlayInput(draft.input))
        }
        assertEquals(8192, MAX_SAVED_PLAY_DRAFT_BYTES)
        assertEquals(2048, MAX_PLAY_INPUT_BYTES)
    }

    @Test fun oversizedOrIllFormedLiveTextSavesOnlyAnOmissionMarkerWithoutChangingLiveText() {
        for (text in listOf("a".repeat(8193), "é".repeat(4097), "🌊".repeat(2049),
            "\uD800", "\uDC00", "\uD800x", "x\uDC00")) {
            val draft = PlayDraft(first, PlayInput(PlayInputKind.DIALOGUE, text))
            val saved = checkNotNull(savePlayDraft(draft))
            assertEquals(listOf(1, "story-a", "root", "dialogue", "", "omitted"), saved)
            val restored = checkNotNull(restorePlayDraft(saved))
            assertEquals(PlayDraft(first, PlayInput(PlayInputKind.DIALOGUE, ""), true), restored)
            assertEquals(text, draft.input.text)
        }
    }

    @Test fun repeatedRestorationRetainsOmissionNoticeUntilAnExplicitMatchingEdit() {
        val original = PlayDraft(first, PlayInput(PlayInputKind.DIALOGUE, "x".repeat(8193)))
        val restored = checkNotNull(restorePlayDraft(savePlayDraft(original)))
        val repeated = checkNotNull(restorePlayDraft(savePlayDraft(restored)))
        assertEquals(restored, repeated)
        assertTrue(repeated.resolve(null, pending = true).textNotRestored)
        assertTrue(repeated.edit(first, otherStory, dialogue).textNotRestored)
        val edited = repeated.edit(first, first, dialogue)
        assertFalse(edited.textNotRestored)
        assertEquals("full", checkNotNull(savePlayDraft(edited))[5])
        assertEquals(PlayDraft(first, dialogue), restorePlayDraft(savePlayDraft(edited)))
        // Even inconsistent live state cannot silently save text under an omission notice.
        assertEquals("", checkNotNull(savePlayDraft(restored.copy(input = dialogue)))[4])
    }

    @Test fun scopeCodecChecksBothIdsForUnicodeUtf8LengthAndControlsWithoutTrimming() {
        for (id in listOf("a".repeat(128), "é".repeat(64), "🌊".repeat(32), " spaced ")) {
            for (scope in listOf(PlayDraftScope(id, "root"), PlayDraftScope("story", id))) {
                val draft = PlayDraft(scope, dialogue)
                assertEquals(draft, restorePlayDraft(savePlayDraft(draft)))
            }
        }
        for (id in listOf("", "a".repeat(129), "é".repeat(65), "🌊".repeat(33),
            "bad\n", "bad\t", "bad\u0000", "bad\u007f", "bad\u0085", "\uD800", "\uDC00")) {
            for (scope in listOf(PlayDraftScope(id, "root"), PlayDraftScope("story", id))) {
                assertNull(savePlayDraft(PlayDraft(scope, dialogue)))
                assertNull(restorePlayDraft(listOf(1, scope.story, scope.branch, "action", "", "full")))
            }
        }
    }

    @Test fun decoderRejectsWrongShapeVersionTypesEnumsAndInconsistentOmission() {
        val full = listOf<Any>(1, "story-a", "root", "action", "original", "full")
        for (wrong in listOf(null, true, 1, "payload", emptyList<Any>(), full.dropLast(1),
            full + "extra", full.toTypedArray(), mapOf("version" to 1))) {
            assertNull(restorePlayDraft(wrong))
        }
        val badFields = listOf(
            0 to listOf<Any?>(0, 2, -1, 1L, 1.0, true, "1", null),
            1 to listOf<Any?>(1, true, null, listOf("story-a")),
            2 to listOf<Any?>(1, true, null),
            3 to listOf<Any?>("ACTION", "unknown", 0, true, null),
            4 to listOf<Any?>(0, true, null, listOf("original")),
            5 to listOf<Any?>("FULL", "unknown", 1, true, null),
        )
        for ((index, invalid) in badFields) for (value in invalid) {
            val payload = full.map { it as Any? }.toMutableList()
            payload[index] = value
            assertNull(restorePlayDraft(payload))
        }
        assertNull(restorePlayDraft(full.dropLast(1) + "omitted"))
        assertNotNull(restorePlayDraft(listOf(1, "story-a", "root", "dialogue", "", "omitted")))
    }

    @Test fun decoderRejectsOversizedOrMalformedSavedFullTextRatherThanRepairingIt() {
        for (text in listOf("x".repeat(8193), "é".repeat(4097), "🌊".repeat(2049),
            "\uD800", "\uDC00", "\uD800\uD800", "\uDC00\uD800")) {
            assertNull(restorePlayDraft(listOf(1, "story-a", "root", "action", text, "full")))
            assertNull(restorePlayDraft(listOf(1, "story-a", "root", "action", text, "omitted")))
        }
    }
}

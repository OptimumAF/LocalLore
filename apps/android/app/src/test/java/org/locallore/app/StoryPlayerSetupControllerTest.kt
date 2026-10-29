/* Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0 */
package org.locallore.app

import kotlinx.coroutines.CompletableDeferred
import kotlinx.coroutines.ExperimentalCoroutinesApi
import kotlinx.coroutines.NonCancellable
import kotlinx.coroutines.test.advanceUntilIdle
import kotlinx.coroutines.test.runCurrent
import kotlinx.coroutines.test.runTest
import kotlinx.coroutines.withContext
import org.junit.Assert.*
import org.junit.Test

/** Original fake-port name-review adversaries; no native/Android execution claim. */
@OptIn(ExperimentalCoroutinesApi::class)
class StoryPlayerSetupControllerTest {
    private val quay = StoryTemplateOption(DEFAULT_STORY_TEMPLATE, "Lantern Quay", "Original quay.", "fantasy_v1")
    private val harbor = StoryTemplateOption("bracken-harbor-v1", "Bracken Harbor", "Original harbor.", "narrative_v1")
    private fun configured(template: String, name: String?): StoryCreationPreview {
        val option = if (template == quay.template) quay else harbor
        val actualName = name ?: if (template == quay.template) "Rowan" else "Alex"
        return StoryCreationPreview(template, "a".repeat(64), option.defaultTitle, option.description, option.profile,
            listOf("Player: $actualName", "Original starting fact."), StoryPlayerSetup("a".repeat(64), "b".repeat(64), actualName))
    }
    private inner class Gateway : StoryCreationGateway {
        var read: suspend (String, String?) -> StoryCreationPreview? = { template, name -> configured(template, name) }
        val reads = mutableListOf<Pair<String, String?>>()
        val creates = mutableListOf<StoryCreationRequest>()
        var legacyReads = 0
        var write: suspend (StoryCreationRequest) -> SavedSnapshot = { error("Synthetic uncertain write") }
        override suspend fun templates() = listOf(quay, harbor)
        override suspend fun preview(): StoryCreationPreview { legacyReads++; error("Legacy fallback forbidden") }
        override suspend fun previewTemplate(template: String): StoryCreationPreview { legacyReads++; error("Legacy fallback forbidden") }
        override suspend fun setupPreview(template: String, playerName: String?): StoryCreationPreview? {
            reads += template to playerName
            return read(template, playerName)
        }
        override suspend fun create(request: StoryCreationRequest): SavedSnapshot { creates += request; return write(request) }
    }

    @Test fun editingRevokesOldConsentUntilAnExactExplicitNativeReview() = runTest {
        val gateway = Gateway()
        val controller = StoryCreationController(gateway, this) {}
        try {
            controller.open(); advanceUntilIdle()
            val original = controller.state.value.review!!
            controller.editTitle(original, "A retained title")
            val titleReview = controller.state.value.review!!
            controller.editPlayerName(original, "Marin")
            val dirty = controller.state.value.review!!
            assertNotSame(titleReview, dirty)
            assertEquals("A retained title", dirty.title)
            assertFalse(hasReviewedPlayerName(dirty, controller.state.value.playerNameDraft))
            controller.confirm(titleReview); controller.confirm(dirty)
            controller.reviewPlayerName(original); controller.reviewPlayerName(dirty.copy())
            assertEquals(1, gateway.reads.size); assertTrue(gateway.creates.isEmpty())
            controller.reviewPlayerName(dirty)
            assertNull(controller.state.value.review)
            assertTrue(controller.state.value.busy)
            controller.confirm(dirty); advanceUntilIdle()
            val accepted = controller.state.value.review!!
            assertEquals("Marin", accepted.preview.playerSetup!!.playerName)
            assertEquals("A retained title", accepted.title)
            assertEquals(original.creationId, accepted.creationId)
            assertTrue(hasReviewedPlayerName(accepted, controller.state.value.playerNameDraft))
            assertEquals(listOf(quay.template to null, quay.template to "Marin"), gateway.reads)
            controller.confirm(dirty); assertTrue(gateway.creates.isEmpty())
            controller.confirm(accepted); advanceUntilIdle()
            assertSame(accepted, gateway.creates.single())
        } finally { controller.dispose() }
    }

    @Test fun invalidDraftsStayLiteralAndCannotBeDroppedByChangingStarterOrCreating() = runTest {
        val gateway = Gateway()
        val controller = StoryCreationController(gateway, this) {}
        try {
            controller.open(); advanceUntilIdle()
            val rendered = controller.state.value.review!!
            val option = controller.state.value.templates[1]
            val wave = String(Character.toChars(0x1f30a))
            for (name in listOf("", " outer", "outer ", "line\nbreak", "tab\t", "x\u202e", "x\u2066", "\uD800",
                "\uDC00", "n".repeat(65), wave.repeat(65))) {
                controller.editPlayerName(rendered, name)
                val dirty = controller.state.value.review!!
                assertEquals(name, controller.state.value.playerNameDraft)
                controller.reviewPlayerName(dirty); controller.confirm(dirty); controller.chooseTemplate(dirty, option)
                assertSame(dirty, controller.state.value.review)
                assertEquals(name, controller.state.value.playerNameDraft)
                assertEquals(quay.template, dirty.preview.template)
                assertEquals(1, gateway.reads.size); assertTrue(gateway.creates.isEmpty())
            }
            for (name in listOf("e\u0301", "\u00e9", "n".repeat(64), wave.repeat(64))) {
                assertTrue(validStoryPlayerName(name))
                controller.editPlayerName(controller.state.value.review!!, name)
                controller.reviewPlayerName(controller.state.value.review!!); advanceUntilIdle()
                assertEquals(name, controller.state.value.review!!.preview.playerSetup!!.playerName)
            }
            assertTrue(gateway.creates.isEmpty())
        } finally { controller.dispose() }
    }

    @Test fun untouchedDefaultsFollowTemplatesWhileAnEditedValidNameCarriesAcrossThem() = runTest {
        val gateway = Gateway()
        val controller = StoryCreationController(gateway, this) {}
        try {
            controller.open(); advanceUntilIdle()
            controller.chooseTemplate(controller.state.value.review!!, controller.state.value.templates[1]); advanceUntilIdle()
            assertEquals("Alex", controller.state.value.playerNameDraft)
            assertEquals(harbor.template to null, gateway.reads.last())
            controller.editPlayerName(controller.state.value.review!!, "Marin")
            controller.chooseTemplate(controller.state.value.review!!, controller.state.value.templates[0]); advanceUntilIdle()
            assertEquals(quay.template to "Marin", gateway.reads.last())
            assertEquals("Marin", controller.state.value.playerNameDraft)
            assertEquals(quay.defaultTitle, controller.state.value.review!!.title)
            assertTrue(hasReviewedPlayerName(controller.state.value.review!!, controller.state.value.playerNameDraft))
            assertTrue(gateway.creates.isEmpty())
        } finally { controller.dispose() }
    }

    @Test fun foreignNameMetadataAndLostCapabilityCannotPublishOrFallBack() = runTest {
        for (fault in listOf("name", "template", "profile", "title", "description", "missing_setup", "lost", "error")) {
            val gateway = Gateway()
            val controller = StoryCreationController(gateway, this) {}
            try {
                controller.open(); advanceUntilIdle()
                controller.editPlayerName(controller.state.value.review!!, "Marin")
                gateway.read = { template, name ->
                    val good = configured(template, name)
                    when (fault) {
                        "name" -> good.copy(playerSetup = good.playerSetup!!.copy(playerName = "Foreign"))
                        "template" -> configured(harbor.template, name)
                        "profile" -> good.copy(profile = "narrative_v1")
                        "title" -> good.copy(defaultTitle = "Foreign")
                        "description" -> good.copy(description = "Foreign")
                        "missing_setup" -> good.copy(playerSetup = null)
                        "lost" -> null
                        else -> error("PRIVATE_source_path")
                    }
                }
                controller.reviewPlayerName(controller.state.value.review!!); advanceUntilIdle()
                assertNull(fault, controller.state.value.review)
                assertFalse(controller.state.value.notice!!.contains("PRIVATE"))
                assertEquals(0, gateway.legacyReads); assertTrue(gateway.creates.isEmpty())
                controller.open(); advanceUntilIdle(); assertEquals(2, gateway.reads.size)
            } finally { controller.dispose() }
        }
    }

    @Test fun cancelledNoncooperativeReviewDrainsBeforeCloseWithoutLatePublication() = runTest {
        val gateway = Gateway()
        val pending = CompletableDeferred<StoryCreationPreview>()
        val closed = mutableListOf<StoryCreationClose>()
        val controller = StoryCreationController(gateway, this, closed::add)
        try {
            controller.open(); advanceUntilIdle()
            controller.editPlayerName(controller.state.value.review!!, "Marin")
            val dirty = controller.state.value.review!!
            gateway.read = { _, _ -> withContext(NonCancellable) { pending.await() } }
            controller.reviewPlayerName(dirty); runCurrent()
            controller.dismiss(); controller.open(); runCurrent()
            assertTrue(controller.state.value.closing); assertTrue(closed.isEmpty())
            controller.confirm(dirty)
            pending.complete(configured(quay.template, "Marin")); advanceUntilIdle()
            assertEquals(listOf(StoryCreationClose()), closed)
            assertFalse(controller.state.value.visible); assertNull(controller.state.value.review)
            assertEquals(2, gateway.reads.size); assertTrue(gateway.creates.isEmpty())
        } finally { pending.complete(configured(quay.template, "Marin")); controller.dispose() }
    }

    @Test fun disposalFencesANoncooperativeSetupResultAndAllRetainedCallbacks() = runTest {
        val gateway = Gateway()
        val pending = CompletableDeferred<StoryCreationPreview>()
        val closed = mutableListOf<StoryCreationClose>()
        val controller = StoryCreationController(gateway, this, closed::add)
        try {
            controller.open(); advanceUntilIdle()
            controller.editPlayerName(controller.state.value.review!!, "Marin")
            val dirty = controller.state.value.review!!
            gateway.read = { _, _ -> withContext(NonCancellable) { pending.await() } }
            controller.reviewPlayerName(dirty); runCurrent(); controller.dispose()
            pending.complete(configured(quay.template, "Marin")); advanceUntilIdle()
            controller.open(); controller.editPlayerName(dirty, "Other"); controller.reviewPlayerName(dirty); controller.confirm(dirty)
            assertFalse(controller.state.value.visible); assertTrue(closed.isEmpty()); assertTrue(gateway.creates.isEmpty())
        } finally { pending.complete(configured(quay.template, "Marin")); controller.dispose() }
    }

    @Test fun retainedEditorsAndReviewTicketsCannotRetargetANewPreviewOrReopenedCreation() = runTest {
        val gateway = Gateway()
        val controller = StoryCreationController(gateway, this) {}
        try {
            controller.open(); advanceUntilIdle()
            val old = controller.state.value.review!!
            controller.editPlayerName(old, "Marin")
            val dirty = controller.state.value.review!!
            controller.reviewPlayerName(dirty); advanceUntilIdle()
            val reviewed = controller.state.value.review!!
            controller.editPlayerName(old, "Wrong"); controller.reviewPlayerName(dirty); controller.confirm(old)
            assertSame(reviewed, controller.state.value.review)
            controller.dismiss(); advanceUntilIdle(); controller.open(); advanceUntilIdle()
            val reopened = controller.state.value.review!!
            assertNotEquals(old.creationId, reopened.creationId)
            controller.editPlayerName(reviewed, "Wrong"); controller.reviewPlayerName(reviewed); controller.confirm(reviewed)
            assertSame(reopened, controller.state.value.review)
            assertEquals("Rowan", controller.state.value.playerNameDraft); assertTrue(gateway.creates.isEmpty())
        } finally { controller.dispose() }
    }

    @Test fun creationConsumesTheConfiguredReviewAndCannotBorrowLaterNameEdits() = runTest {
        val gateway = Gateway()
        val pending = CompletableDeferred<SavedSnapshot>()
        gateway.write = { withContext(NonCancellable) { pending.await() } }
        val controller = StoryCreationController(gateway, this) {}
        val saved = SavedSnapshot(0, "Player", emptyList(), "synthetic", 1, emptyList(), null)
        try {
            controller.open(); advanceUntilIdle()
            controller.editPlayerName(controller.state.value.review!!, "Marin")
            controller.reviewPlayerName(controller.state.value.review!!); advanceUntilIdle()
            val reviewed = controller.state.value.review!!
            controller.confirm(reviewed); controller.confirm(reviewed); controller.editPlayerName(reviewed, "Wrong")
            controller.reviewPlayerName(reviewed); runCurrent()
            assertSame(reviewed, gateway.creates.single())
            assertEquals("Marin", gateway.creates.single().preview.playerSetup!!.playerName)
            assertNull(controller.state.value.review)
            controller.dispose(); pending.complete(saved); advanceUntilIdle()
            assertFalse(controller.state.value.visible)
        } finally { pending.complete(saved); controller.dispose() }
    }
}

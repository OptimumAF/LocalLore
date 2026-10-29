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

/** Fake-port consent and ownership tests. Native persistence and Android execution are separate. */
@OptIn(ExperimentalCoroutinesApi::class)
class StoryTemplateChoiceControllerTest {
    private val quay = StoryCreationPreview(DEFAULT_STORY_TEMPLATE, "a".repeat(64), "Lantern Quay",
        "Original quay starter.", "fantasy_v1", listOf("You are Rowan."))
    private val harbor = StoryCreationPreview("bracken-harbor-v1", "b".repeat(64), "Bracken Harbor",
        "Original harbor starter.", "narrative_v1", listOf("You are Alex."))
    private inner class Gateway : StoryCreationGateway {
        var options = mutableListOf(quay.option(), harbor.option())
        var catalogRead: suspend () -> List<StoryTemplateOption>? = { options }
        var selectedRead: suspend (String) -> StoryCreationPreview = { if (it == quay.template) quay else harbor }
        var writes: suspend (StoryCreationRequest) -> SavedSnapshot = { error("Synthetic write not configured") }
        var catalogs = 0
        var legacyReads = 0
        val reads = mutableListOf<String>()
        val creates = mutableListOf<StoryCreationRequest>()
        override suspend fun templates(): List<StoryTemplateOption>? { catalogs++; return catalogRead() }
        override suspend fun preview(): StoryCreationPreview { legacyReads++; return quay }
        override suspend fun previewTemplate(template: String): StoryCreationPreview {
            reads += template
            return selectedRead(template)
        }
        override suspend fun create(request: StoryCreationRequest): SavedSnapshot { creates += request; return writes(request) }
    }

    @Test fun choosingReplacesTheReviewedFactsAndDefaultTitleWithoutCreatingOrAcceptingOldConsent() = runTest {
        val gateway = Gateway()
        val controller = StoryCreationController(gateway, this) {}
        try {
            controller.open(); advanceUntilIdle()
            val old = controller.state.value.review!!
            val choice = controller.state.value.templates[1]
            controller.chooseTemplate(old, choice)
            assertNull(controller.state.value.review)
            assertTrue(controller.state.value.busy)
            controller.confirm(old); controller.editTitle(old, "Stale edit")
            advanceUntilIdle()
            val current = controller.state.value.review!!
            assertEquals(harbor, current.preview)
            assertEquals(harbor.defaultTitle, current.title)
            assertEquals(old.creationId, current.creationId)
            assertNotSame(old.preview, current.preview)
            controller.confirm(old); controller.editTitle(old, "Stale edit")
            controller.chooseTemplate(old, controller.state.value.templates.first())
            assertSame(current, controller.state.value.review)
            assertEquals(listOf(quay.template, harbor.template), gateway.reads)
            assertEquals(1, gateway.catalogs); assertEquals(0, gateway.legacyReads)
            assertTrue(gateway.creates.isEmpty())
        } finally { controller.dispose() }
    }

    @Test fun editedTitleCarriesAcrossChoicesButForeignOrEqualCopyChooserTicketsDoNot() = runTest {
        val gateway = Gateway()
        val controller = StoryCreationController(gateway, this) {}
        try {
            controller.open(); advanceUntilIdle()
            val rendered = controller.state.value.review!!
            val choice = controller.state.value.templates[1]
            controller.editTitle(rendered, "My harbor story")
            val edited = controller.state.value.review!!
            controller.chooseTemplate(rendered, choice)
            controller.chooseTemplate(edited.copy(), choice)
            controller.chooseTemplate(edited, choice.copy())
            assertSame(edited, controller.state.value.review)
            assertEquals(1, gateway.reads.size)
            controller.chooseTemplate(edited, choice); advanceUntilIdle()
            assertEquals("My harbor story", controller.state.value.review!!.title)
            controller.chooseTemplate(controller.state.value.review!!, controller.state.value.templates[0])
            advanceUntilIdle()
            assertEquals(quay.template, controller.state.value.review!!.preview.template)
            assertEquals("My harbor story", controller.state.value.review!!.title)
            assertTrue(gateway.creates.isEmpty())
        } finally { controller.dispose() }
    }

    @Test fun catalogAndPreviewBindingFailureNeverFallsBackToTheLegacyPort() = runTest {
        for (fault in listOf("catalog_error", "empty", "duplicate", "unknown", "profile", "title", "description", "template")) {
            val gateway = Gateway()
            when (fault) {
                "catalog_error" -> gateway.catalogRead = { error("PRIVATE_native_path") }
                "empty" -> gateway.options.clear()
                "duplicate" -> gateway.options += quay.option()
                "unknown" -> gateway.options[1] = harbor.option().copy(template = "foreign-starter")
                "profile" -> gateway.selectedRead = { quay.copy(profile = "narrative_v1") }
                "title" -> gateway.selectedRead = { quay.copy(defaultTitle = "Foreign title") }
                "description" -> gateway.selectedRead = { quay.copy(description = "Foreign description") }
                "template" -> gateway.selectedRead = { harbor }
            }
            val controller = StoryCreationController(gateway, this) {}
            try {
                controller.open(); advanceUntilIdle()
                assertNull("fault $fault", controller.state.value.review)
                assertFalse(controller.state.value.busy)
                assertFalse(controller.state.value.notice!!.contains("PRIVATE"))
                assertEquals(0, gateway.legacyReads)
                assertTrue(gateway.creates.isEmpty())
            } finally { controller.dispose() }
        }
    }

    @Test fun mismatchedSelectedPreviewRevokesOldReviewWithoutCreatingOrAutomaticallyRetrying() = runTest {
        for (wrong in listOf(quay, harbor.copy(profile = "fantasy_v1"),
            harbor.copy(defaultTitle = "Other"), harbor.copy(description = "Other"))) {
            val gateway = Gateway()
            val controller = StoryCreationController(gateway, this) {}
            try {
                controller.open(); advanceUntilIdle()
                val old = controller.state.value.review!!
                gateway.selectedRead = { wrong }
                controller.chooseTemplate(old, controller.state.value.templates[1]); advanceUntilIdle()
                assertNull(controller.state.value.review)
                controller.confirm(old); controller.open(); advanceUntilIdle()
                assertEquals(2, gateway.reads.size)
                assertTrue(gateway.creates.isEmpty())
            } finally { controller.dispose() }
        }
    }

    @Test fun catalogAndDetailsAreFrozenBeforeThePortCanChangeThem() = runTest {
        val gateway = Gateway()
        val details = mutableListOf("Original harbor fact")
        gateway.selectedRead = { if (it == quay.template) quay else harbor.copy(details = details) }
        val controller = StoryCreationController(gateway, this) {}
        try {
            controller.open(); advanceUntilIdle()
            val options = controller.state.value.templates
            assertNotSame(gateway.options[1], options[1])
            gateway.options.clear()
            assertEquals(2, options.size)
            try { (options as MutableList<StoryTemplateOption>).clear(); fail("Mutable catalog") }
            catch (_: UnsupportedOperationException) {}
            controller.chooseTemplate(controller.state.value.review!!, options[1]); advanceUntilIdle()
            details[0] = "Changed port fact"
            assertEquals(listOf("Original harbor fact"), controller.state.value.review!!.preview.details)
            assertTrue(gateway.creates.isEmpty())
        } finally { controller.dispose() }
    }

    @Test fun cancelledSelectedReadDrainsBeforeClosingAndCannotPublishIntoReopenedReview() = runTest {
        val gateway = Gateway()
        val pending = CompletableDeferred<StoryCreationPreview>()
        val closed = mutableListOf<StoryCreationClose>()
        val controller = StoryCreationController(gateway, this, closed::add)
        try {
            controller.open(); advanceUntilIdle()
            gateway.selectedRead = { withContext(NonCancellable) { pending.await() } }
            val old = controller.state.value.review!!
            controller.chooseTemplate(old, controller.state.value.templates[1]); runCurrent()
            controller.dismiss(); controller.open(); runCurrent()
            assertTrue(controller.state.value.closing)
            assertTrue(closed.isEmpty())
            assertEquals(1, gateway.catalogs)
            controller.confirm(old)
            pending.complete(harbor); advanceUntilIdle()
            assertEquals(listOf(StoryCreationClose()), closed)
            assertFalse(controller.state.value.visible)
            assertNull(controller.state.value.review)
            assertTrue(gateway.creates.isEmpty())
        } finally { pending.complete(harbor); controller.dispose() }
    }

    @Test fun creationConsumesChooserAndOnlyTheExactSelectedReviewReachesTheWritePort() = runTest {
        val gateway = Gateway()
        val pending = CompletableDeferred<SavedSnapshot>()
        gateway.writes = { withContext(NonCancellable) { pending.await() } }
        val controller = StoryCreationController(gateway, this) {}
        try {
            controller.open(); advanceUntilIdle()
            controller.chooseTemplate(controller.state.value.review!!, controller.state.value.templates[1])
            advanceUntilIdle()
            val selected = controller.state.value.review!!
            val option = controller.state.value.templates[0]
            controller.confirm(selected.copy()); runCurrent()
            assertTrue(gateway.creates.isEmpty())
            controller.confirm(selected); controller.chooseTemplate(selected, option); runCurrent()
            assertSame(selected, gateway.creates.single())
            assertEquals(harbor.template, gateway.creates.single().preview.template)
            assertEquals(2, gateway.reads.size)
            assertNull(controller.state.value.review)
            controller.dispose()
            pending.complete(SavedSnapshot(0, "Player", emptyList(), "synthetic", 1, emptyList(), null)); advanceUntilIdle()
            assertFalse(controller.state.value.visible)
        } finally { pending.complete(SavedSnapshot(0, "Player", emptyList(), "synthetic", 1, emptyList(), null)); controller.dispose() }
    }
}

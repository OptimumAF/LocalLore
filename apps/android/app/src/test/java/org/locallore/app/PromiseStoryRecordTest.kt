/* Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0 */
package org.locallore.app

import androidx.lifecycle.ViewModelStore
import kotlinx.coroutines.CompletableDeferred
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.ExperimentalCoroutinesApi
import kotlinx.coroutines.NonCancellable
import kotlinx.coroutines.test.StandardTestDispatcher
import kotlinx.coroutines.test.advanceUntilIdle
import kotlinx.coroutines.test.resetMain
import kotlinx.coroutines.test.runCurrent
import kotlinx.coroutines.test.runTest
import kotlinx.coroutines.test.setMain
import kotlinx.coroutines.withContext
import org.json.JSONArray
import org.json.JSONObject
import org.junit.Assert.*
import org.junit.Test

/** Synthetic Host inspection rows exercise the real decoder; Rust owns eligibility/status. */
@OptIn(ExperimentalCoroutinesApi::class)
class PromiseStoryRecordTest {
    private val story = SavedStory("quay", "main", "Lantern Quay", 4)
    private val context = StoryRecordContext(story, 4)

    // Keep the original test compilable before the additive enum is implemented.
    private fun promises(): StoryRecordSection = try {
        StoryRecordSection.valueOf("PROMISES")
    } catch (missing: IllegalArgumentException) {
        throw AssertionError("The existing Rust promises view needs an Android section", missing)
    }

    private fun query() = StoryRecordQuery(context, promises())
    private fun scopedEvent(sequence: Any, branch: String = "main") = JSONObject()
        .put("kind", "scoped_event").put("value", JSONObject()
            .put("original_scope", JSONObject().put("story", "quay").put("branch", branch))
            .put("sequence", sequence))
    private fun promise(id: String = "return-key", from: String = "player", to: String = "mira") =
        JSONObject().put("kind", "promise").put("key", "promise:$id").put("id", id)
            .put("from", from).put("to", to).put("terms", "Return the borrowed brass key.")
            .put("deadline", 120L).put("status", "open").put("return_item", JSONObject.NULL)
            .put("sources", JSONArray().put(JSONObject().put("kind", "seed").put("value", "quay-seed")))
            .put("origin", "derived_comparison")

    private fun page(
        q: StoryRecordQuery,
        rows: List<JSONObject> = listOf(promise()),
        total: Int = rows.size,
        next: String? = null,
    ) = JSONObject().put("version", if (q.section == promises()) 2 else 1)
        .put("scope", JSONObject().put("story", q.context.story.story).put("branch", q.context.story.branch))
        .put("head", q.context.revision).put("revision", q.context.revision).put("story_time", 100L)
        .put("observer", JSONObject().put("kind", "player")).put("privacy", "player_visible")
        .put("status", "supported").put("view", q.section.wire).put("total", total)
        .put("rows", JSONArray(rows)).put("next_cursor", next ?: JSONObject.NULL).put("unsupported", JSONArray())

    private fun decode(row: JSONObject, q: StoryRecordQuery = query()) =
        StoryRecordWire.decode(page(q, listOf(row)), q).entries.single()

    private fun invalid(data: JSONObject, q: StoryRecordQuery) {
        try {
            StoryRecordWire.decode(data, q)
            fail("Malformed promise data must fail closed")
        } catch (failure: StoryRecordFailure) {
            assertEquals(StoryRecordProblem.INVALID_RESPONSE, failure.problem)
        }
    }

    private fun readPage(q: StoryRecordQuery): StoryRecordPage {
        if (q.section != promises()) return StoryRecordPage(q, 100, 0, emptyList(), null)
        val later = q.cursor != null
        return StoryRecordWire.decode(page(q, listOf(promise(if (later) "incoming" else "return-key")),
            2, if (later) null else "2:1:${"a".repeat(64)}"), q)
    }

    @Test fun sectionAndCommandSelectOnlyCurrentPlayerPromisesWithTheExistingPageBudget() {
        val q = query().copy(search = "Literal % '_", cursor = "2:1:${"a".repeat(64)}")
        assertEquals("promises", promises().wire)
        assertEquals("Promises", promises().label)
        val command = StoryRecordWire.command("bound-session", q)
        assertEquals(setOf("op", "session", "query"), command.keySet())
        assertEquals("inspection_query", command.getString("op"))
        assertEquals("bound-session", command.getString("session"))
        val wire = command.getJSONObject("query")
        assertEquals(setOf("version", "scope", "expected_head", "at_revision", "observer", "view", "limit", "search", "cursor"), wire.keySet())
        assertEquals(2, wire.getInt("version"))
        assertEquals("quay", wire.getJSONObject("scope").getString("story"))
        assertEquals("main", wire.getJSONObject("scope").getString("branch"))
        assertEquals(4L, wire.getLong("expected_head"))
        assertTrue(wire.isNull("at_revision"))
        assertEquals(setOf("kind"), wire.getJSONObject("observer").keySet())
        assertEquals("player", wire.getJSONObject("observer").getString("kind"))
        assertEquals("promises", wire.getString("view"))
        assertEquals(8, wire.getInt("limit"))
        assertEquals(q.search, wire.getString("search"))
        assertEquals(q.cursor, wire.getString("cursor"))
        for (legacy in StoryRecordSection.entries.filter { it != promises() }) {
            val original = StoryRecordWire.command("bound-session",
                StoryRecordQuery(context, legacy, q.search, "1:1:${"a".repeat(64)}"))
                .getJSONObject("query")
            assertEquals(1, original.getInt("version"))
            assertEquals(legacy.wire, original.getString("view"))
        }
    }

    @Test fun outgoingPromiseRendersExactTermsPartiesClockAndReturnItemWithoutChangingTheRow() {
        val row = promise().put("return_item", "brass-key")
        val before = row.toString()
        val entry = decode(row)
        assertEquals("promise:return-key", entry.key)
        assertEquals("Promise · return-key", entry.title)
        assertEquals("From · player\nTo · mira\nStatus · Open\nDue at story time · 120\nReturn the borrowed brass key.\nReturn item · brass-key", entry.text)
        assertEquals(StoryRecordOrigin.DERIVED_COMPARISON, entry.origin)
        assertEquals(listOf("Seed · quay-seed"), entry.sources)
        assertTrue(entry.eventSources.isEmpty())
        assertNull(entry.event)
        assertEquals(before, row.toString())
    }

    @Test fun incomingEligiblePromiseAndExplicitNullReturnItemRemainDistinctFromAbsence() {
        val row = promise("incoming", "mira", "player").put("sources",
            JSONArray().put(scopedEvent(3)))
        val entry = decode(row)
        assertEquals("Promise · incoming", entry.title)
        assertEquals("From · mira\nTo · player\nStatus · Open\nDue at story time · 120\nReturn the borrowed brass key.", entry.text)
        assertEquals(listOf("Event #3 · quay / main"), entry.sources)
        assertTrue(entry.eventSources.isEmpty())
        val missing = promise().also { it.remove("return_item") }
        val q = query()
        invalid(page(q, listOf(missing)), q)
    }

    @Test fun displayedStatusComesFromRustAndIsNotRecomputedFromThePageClockOrDeadline() {
        for ((wire, label) in listOf("open" to "Open", "overdue" to "Overdue", "fulfilled" to "Fulfilled")) {
            // Deliberately equal metadata for every status: this is a presenter
            // oracle, not a simulation of Rust's commitment-status rules.
            val entry = decode(promise().put("status", wire).put("deadline", 0L))
            assertEquals("From · player\nTo · mira\nStatus · $label\nDue at story time · 0\nReturn the borrowed brass key.", entry.text)
        }
        assertTrue(decode(promise().put("deadline", Long.MAX_VALUE)).text.contains("Due at story time · ${Long.MAX_VALUE}"))
    }

    @Test fun scopedSourcesPreserveOriginalBranchesWithoutFlatteningIntoCurrentEventLinks() {
        val evidence = JSONArray().put(JSONObject().put("kind", "seed").put("value", "quay-seed"))
            .put(scopedEvent(1, "ancestor"))
            .put(JSONObject().put("kind", "withheld"))
            .put(scopedEvent(1, "main"))
            .put(scopedEvent(1, "ancestor"))
        val entry = decode(promise().put("sources", evidence))
        assertEquals(listOf("Seed · quay-seed", "Event #1 · quay / ancestor", "Evidence withheld",
            "Event #1 · quay / main", "Event #1 · quay / ancestor"), entry.sources)
        assertTrue(entry.eventSources.isEmpty())
        assertEquals(StoryRecordOrigin.DERIVED_COMPARISON, entry.origin)
    }

    @Test fun promiseRowsRequireTheirSectionDerivedOriginAndAtLeastOnePlayerParty() {
        val q = query()
        for (origin in listOf("canonical_field", "canonical_truth", "recorded_statement", "unknown")) {
            invalid(page(q, listOf(promise().put("origin", origin))), q)
        }
        invalid(page(q, listOf(promise(from = "mira", to = "oren"))), q)
        for (section in StoryRecordSection.entries.filter { it != promises() }) {
            val other = q.copy(section = section)
            invalid(page(other, listOf(promise())), other)
        }
        invalid(page(q, listOf(promise().put("kind", "provenance"))), q)
    }

    @Test fun unknownStatusesAndNonIntegralOrNegativeDeadlinesFailClosed() {
        val q = query()
        for (value in listOf<Any>("pending", "OPEN", "completed", true, 1, JSONObject.NULL)) {
            invalid(page(q, listOf(promise().put("status", value))), q)
        }
        for (value in listOf<Any>(-1, true, 1.0, "120", JSONObject.NULL)) {
            invalid(page(q, listOf(promise().put("deadline", value))), q)
        }
    }

    @Test fun sourceArraysRequireBoundedTypedScopedReferencesAndRejectLegacyUnscopedEvents() {
        val q = query()
        val bad = listOf(
            JSONArray(),
            JSONArray(List(65) { JSONObject().put("kind", "withheld") }),
            JSONArray().put(true),
            JSONArray().put(JSONObject().put("kind", "invented").put("value", 1)),
            JSONArray().put(JSONObject().put("kind", "seed").put("value", true)),
            JSONArray().put(JSONObject().put("kind", "seed").put("value", "x".repeat(513))),
            JSONArray().put(JSONObject().put("kind", "event").put("value", 1)),
            JSONArray().put(JSONObject().put("kind", "scoped_event").put("value", 1)),
            JSONArray().put(JSONObject().put("kind", "scoped_event").put("value", JSONObject().put("sequence", 1))),
            JSONArray().put(scopedEvent(1).also {
                it.getJSONObject("value").put("original_scope", JSONObject().put("story", "quay").put("branch", true))
            }),
            JSONArray().put(scopedEvent(1).also {
                it.getJSONObject("value").getJSONObject("original_scope").put("story", "another-story")
            }),
            JSONArray().put(scopedEvent(1).also { it.getJSONObject("value").put("extra", "unreviewed") }),
            JSONArray().put(scopedEvent(1).also {
                it.getJSONObject("value").getJSONObject("original_scope").put("extra", "unreviewed")
            }),
        ) + listOf<Any>(0, -1, 5, true, 1.0, "1").map { value ->
            JSONArray().put(scopedEvent(value))
        } + listOf("", "bad/branch", "é", "a".repeat(65)).map { branch ->
            JSONArray().put(scopedEvent(1, branch))
        }
        for (sources in bad) invalid(page(q, listOf(promise().put("sources", sources))), q)
    }

    @Test fun responseScopeHeadObserverPrivacyAndPagingMustMatchTheFrozenQuery() {
        val q = query()
        val edits: List<(JSONObject) -> Unit> = listOf(
            { it.put("scope", JSONObject().put("story", "other").put("branch", "main")) },
            { it.put("head", 5) }, { it.put("revision", 3) }, { it.put("head", true) },
            { it.put("observer", JSONObject().put("kind", "omniscient")) },
            { it.put("observer", JSONObject().put("kind", "player").put("actor", "mira")) },
            { it.put("privacy", "inspector_only") }, { it.put("view", "history") },
            { it.put("version", 1) },
            { it.put("story_time", -1) }, { it.put("rows", JSONArray().put(promise()).put(promise())).put("total", 2) },
            { it.put("next_cursor", "arbitrary") },
        )
        for (edit in edits) invalid(page(q).also(edit), q)
    }

    @Test fun utf8TermsIdentifiersAndOptionalItemHaveBoundedTypedDisplayValues() {
        val terms = "é".repeat(4096)
        assertTrue(decode(promise().put("terms", terms)).text.endsWith(terms))
        assertEquals("Promise · ${"x".repeat(512)}", decode(promise().put("id", "x".repeat(512))).title)
        assertTrue(decode(promise().put("return_item", "x".repeat(512))).text.endsWith("Return item · ${"x".repeat(512)}"))
        val q = query()
        for ((field, value) in listOf(
            "terms" to (terms + "a"), "id" to "x".repeat(513), "key" to "x".repeat(513),
            "from" to "x".repeat(513), "to" to "x".repeat(513), "return_item" to "x".repeat(513),
            "terms" to true, "id" to 7, "from" to false, "return_item" to 7,
        )) {
            val row = if (field == "from") promise(to = "player") else promise()
            invalid(page(q, listOf(row.put(field, value))), q)
        }
    }

    @Test fun promisePagingAndLiteralSearchKeepTheSameStoryHeadAndResetTheCursor() = runTest {
        val calls = mutableListOf<StoryRecordQuery>()
        val controller = StoryRecordController({ q -> calls += q; readPage(q) }, this)
        controller.open(context); advanceUntilIdle()
        controller.select(promises()); advanceUntilIdle()
        assertEquals("Promise · return-key", controller.state.value.entries.single().title)
        controller.next(); advanceUntilIdle()
        assertEquals("2:1:${"a".repeat(64)}", calls.last().cursor)
        assertEquals("Promise · incoming", controller.state.value.entries.single().title)
        controller.search("Literal % '_"); advanceUntilIdle()
        assertEquals("Literal % '_", calls.last().search)
        assertEquals(promises(), calls.last().section)
        assertNull(calls.last().cursor)
        controller.first(); advanceUntilIdle()
        assertNull(calls.last().cursor)
        assertTrue(calls.all { it.context == context })
        assertNull(controller.state.value.problem)
        controller.dispose()
    }

    @Test fun aLatePromiseReadCannotReplaceAnotherStoryOrItsAcceptedHead() = runTest {
        val old = CompletableDeferred<Unit>()
        val other = context.copy(story = story.copy(story = "garden", revision = 7), revision = 7)
        val controller = StoryRecordController({ q ->
            if (q.section == promises()) {
                if (q.context == context) withContext(NonCancellable) { old.await() }
                StoryRecordWire.decode(page(q, listOf(promise(if (q.context == context) "obsolete" else "current"))), q)
            } else StoryRecordPage(q, 100, 0, emptyList(), null)
        }, this)
        controller.open(context); advanceUntilIdle()
        controller.select(promises()); runCurrent()
        controller.open(other); runCurrent()
        controller.select(promises()); runCurrent()
        val current = controller.state.value
        assertEquals(other, current.context)
        assertEquals("Promise · current", current.entries.single().title)
        old.complete(Unit); advanceUntilIdle()
        assertEquals(current, controller.state.value)
        controller.dispose()
    }

    @Test fun dismissAndDisposalRevokeLatePromiseRowsAndRetainedCallbacks() = runTest {
        for (dispose in listOf(false, true)) {
            val late = CompletableDeferred<Unit>()
            var promiseReads = 0
            val controller = StoryRecordController({ q ->
                if (q.section == promises()) {
                    promiseReads++
                    withContext(NonCancellable) { late.await() }
                    StoryRecordWire.decode(page(q), q)
                } else StoryRecordPage(q, 100, 0, emptyList(), null)
            }, this)
            controller.open(context); advanceUntilIdle()
            controller.select(promises()); runCurrent()
            if (dispose) controller.dispose() else controller.dismiss()
            controller.select(promises()); controller.next(); controller.retry()
            if (dispose) controller.open(context)
            late.complete(Unit); advanceUntilIdle()
            assertEquals(1, promiseReads)
            assertEquals(StoryRecordState(), controller.state.value)
            controller.dispose()
        }
    }

    @Test fun viewModelPromiseBrowsingDoesNotGenerateCommitCancelOrChangeSavedGameplay() = runTest {
        Dispatchers.setMain(StandardTestDispatcher(testScheduler))
        val store = ViewModelStore()
        val writes = mutableListOf<String>()
        val reads = mutableListOf<StoryRecordQuery>()
        val saved = SavedSnapshot(4, "You", listOf(SceneMessage(1, "Recorded prior turn", true)),
            "synthetic-private-workspace", 1, listOf(story), story)
        var snapshots = 0
        val gateway = object : DemoGateway {
            override val durable = true
            override val storyRecords = true
            override suspend fun initialize() = saved
            override suspend fun snapshot(): SavedSnapshot { snapshots++; return saved }
            override suspend fun respond(action: DemoAction, revision: Long, mode: DemoMode): DemoResult {
                writes += "respond"; error("Browsing has no generation authority")
            }
            override suspend fun commitAsync(result: DemoResult): DemoResult { writes += "commit"; return result }
            override fun cancel() { writes += "cancel" }
            override fun reset() { writes += "reset" }
            override fun close() { writes += "close" }
            override suspend fun readStoryRecord(query: StoryRecordQuery): StoryRecordPage {
                reads += query; return readPage(query)
            }
        }
        try {
            val model = ShellViewModel(gateway)
            store.put("promise-model", model)
            advanceUntilIdle()
            val before = model.state.value
            val writesBefore = writes.toList()
            val snapshotsBefore = snapshots
            model.openStoryRecord(); advanceUntilIdle()
            model.recordSection(promises()); advanceUntilIdle()
            model.nextRecordPage(); advanceUntilIdle()
            model.recordSearch("return"); advanceUntilIdle()
            model.firstRecordPage(); advanceUntilIdle()
            model.closeStoryRecord(); advanceUntilIdle()
            assertTrue(reads.any { it.section == promises() })
            assertTrue(reads.all { it.context == context })
            assertEquals(writesBefore, writes)
            assertEquals(snapshotsBefore, snapshots)
            assertEquals(before, model.state.value)
            assertEquals(StoryRecordState(), model.storyRecord.value)
            assertEquals(4L, saved.revision)
            assertEquals("You", saved.potionOwner)
        } finally {
            store.clear()
            Dispatchers.resetMain()
        }
    }
}

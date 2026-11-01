/* Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0 */
package org.locallore.app

import android.content.Context
import android.content.ContextWrapper
import androidx.lifecycle.ViewModelStore
import androidx.test.ext.junit.runners.AndroidJUnit4
import androidx.test.platform.app.InstrumentationRegistry
import androidx.test.runner.lifecycle.ActivityLifecycleMonitorRegistry
import androidx.test.runner.lifecycle.Stage
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.NonCancellable
import kotlinx.coroutines.delay
import kotlinx.coroutines.runBlocking
import kotlinx.coroutines.withContext
import kotlinx.coroutines.withTimeout
import org.json.JSONArray
import org.json.JSONObject
import org.junit.After
import org.junit.Assert.*
import org.junit.Before
import org.junit.Test
import org.junit.runners.model.MultipleFailureException
import org.junit.runner.RunWith
import java.io.File
import java.util.UUID
import java.util.concurrent.atomic.AtomicBoolean
import java.util.concurrent.atomic.AtomicInteger

/** Real player inspection, never a Kotlin reconstruction of engine eligibility or canon. */
@RunWith(AndroidJUnit4::class)
class StoryRecordInstrumentedTest {
    @Before fun noActivityBefore() = assertNoRecordActivities()
    @After fun noActivityAfter() = assertNoRecordActivities()

    @Test fun playerPaginationAndGiftHistoryAreReadOnlyAndSurviveStrictReopen() = runBlocking {
        withRecordFixture { fixture ->
            var owner = fixture.owner()
            val initial = owner.gateway.initialize()
            val query = StoryRecordQuery(StoryRecordContext(checkNotNull(initial.selected), initial.revision))
            val before = owner.acceptedView()
            val turnCalls = owner.transport.turnCalls.get()
            val first = owner.gateway.readStoryRecord(query)
            assertEquals(8, first.entries.size)
            assertTrue(first.total > 8)
            assertNotNull(first.nextCursor)
            val second = owner.gateway.readStoryRecord(query.copy(cursor = first.nextCursor))
            assertNull(second.nextCursor)
            val rows = first.entries + second.entries
            assertEquals(first.total, rows.size)
            assertEquals(rows.size, rows.map { it.key }.toSet().size)
            assertTrue(rows.all { it.origin == StoryRecordOrigin.CANONICAL_FIELD })
            assertTrue(rows.all { it.sources == listOf("Seed \u00B7 lantern-quay-v1") })
            assertEquals(100L, first.storyTime)
            val empty = owner.gateway.readStoryRecord(query.copy(search = "%' OR 1=1 -- [literal]"))
            assertEquals(0, empty.total)
            assertTrue(empty.entries.isEmpty())
            for (section in StoryRecordSection.values()) owner.gateway.readStoryRecord(query.copy(section = section))
            assertTrue("Browsing changed the accepted player view", before == owner.acceptedView())
            assertTrue("Browsing changed the saved presentation", initial == owner.gateway.snapshot())
            assertEquals("Browsing dispatched a turn or inference preparation", turnCalls, owner.transport.turnCalls.get())

            val prepared = owner.gateway.respond(DemoAction.GIVE_POTION, 0, DemoMode.ACCEPTED)
            assertTrue(prepared is DemoResult.Prepared)
            assertTrue(owner.gateway.commitAsync(prepared) is DemoResult.Accepted)
            val committed = owner.gateway.snapshot()
            assertEquals(1L, committed.revision)
            assertEquals(2, committed.messages.size)
            assertEquals("Not in your inventory", committed.potionOwner)
            val after = owner.acceptedView()
            val receipt = JSONObject(after).getJSONArray("receipts").getJSONObject(0)
            val turn = receipt.getJSONObject("request").getString("turn")
            val historyQuery = StoryRecordQuery(StoryRecordContext(checkNotNull(committed.selected), 1), StoryRecordSection.HISTORY)
            val history = owner.gateway.readStoryRecord(historyQuery)
            assertEquals(100L, history.storyTime)
            val original = receipt.getJSONObject("request").getJSONObject("scope")
            val reference = StoryRecordScopedEvent(StoryRecordScope(original.getString("story"), original.getString("branch")), 1)
            assertTrue(history.entries.any { it.origin == StoryRecordOrigin.RECORDED_OBSERVATION && it.scopedEventSources == listOf(reference) && it.eventSources.isEmpty() })
            assertTrue(history.entries.any { it.origin == StoryRecordOrigin.RECORDED_MESSAGE && it.scopedEventSources == listOf(reference) &&
                it.eventSources.isEmpty() && it.text.contains(receipt.getString("narration")) })
            val raw = owner.recordData(historyQuery).toString()
            assertTrue("History lost the original receipt key", raw.contains(turn))
            assertTrue(after == owner.acceptedView())
            fixture.closeOwnersAndDrain()
            owner = fixture.owner()
            val reopened = owner.gateway.initialize()
            assertTrue("Reopen changed the accepted transcript", committed == reopened)
            val restored = owner.gateway.readStoryRecord(historyQuery)
            assertTrue("Reopen changed player-visible history", history == restored)
            assertTrue("Reopen changed accepted receipts", after == owner.acceptedView())
        }
    }

    @Test fun actualClaimsBeliefsAndKnownTruthKeepDistinctOriginsAndObserverGrants() = runBlocking {
        withRecordFixture { fixture ->
            val owner = fixture.owner()
            owner.gateway.initialize()
            val claim = "SYNTHETIC RECORD CLAIM: the brass key sings at noon."
            owner.commitIntent(JSONObject().put("kind", "dialogue").put("value", JSONObject()
                .put("text", claim).put("audience", JSONArray().put("mira"))))
            owner.commitIntent(JSONObject().put("kind", "actions").put("value", JSONArray()
                .put(JSONObject().put("op", "believe").put("claim_event", 1))))
            val saved = owner.gateway.snapshot()
            assertEquals(2L, saved.revision)
            val before = owner.acceptedView()
            val turnCalls = owner.transport.turnCalls.get()
            val query = StoryRecordQuery(StoryRecordContext(checkNotNull(saved.selected), 2), StoryRecordSection.KNOWLEDGE)
            val page = owner.gateway.readStoryRecord(query)
            val statement = page.entries.single { it.origin == StoryRecordOrigin.RECORDED_STATEMENT }
            val belief = page.entries.single { it.origin == StoryRecordOrigin.SUBJECTIVE_BELIEF }
            assertTrue(statement.text.contains(claim))
            assertTrue(belief.text.contains(claim))
            val original = StoryRecordScope(query.context.story.story, query.context.story.branch)
            fun source(sequence: Long) = "Event #$sequence · ${original.story} / ${original.branch}"
            assertEquals(listOf(source(1)), statement.sources)
            assertEquals(setOf(source(1), source(2)), belief.sources.toSet())
            assertEquals(listOf(StoryRecordScopedEvent(original, 1)), statement.scopedEventSources)
            assertEquals(setOf(StoryRecordScopedEvent(original, 1), StoryRecordScopedEvent(original, 2)), belief.scopedEventSources.toSet())
            assertTrue(statement.eventSources.isEmpty() && belief.eventSources.isEmpty())
            val truths = page.entries.filter { it.origin == StoryRecordOrigin.KNOWN_AS_OBSERVED }
            assertTrue(truths.any { it.text.contains("SECRET-TIDE-731") }) // Known to the player in this seed.
            assertFalse(truths.any { it.text.contains(claim) })
            assertTrue(truths.all { "Seed \u00B7 lantern-quay-v1" in it.sources })
            for (hidden in listOf("The tideglass relic is in old-ruins.", "Rowan may possess the tideglass relic.", "An old repair mark")) {
                val hiddenPage = owner.gateway.readStoryRecord(query.copy(search = hidden))
                assertEquals("Hidden seed data contributed a visible match", 0, hiddenPage.total)
                assertTrue(hiddenPage.entries.isEmpty())
                assertFalse(page.entries.any { it.text.contains(hidden) })
            }
            for (observer in listOf(JSONObject().put("kind", "character").put("id", "mira"), JSONObject().put("kind", "omniscient"))) {
                val reply = owner.transport.exchange(owner.recordCommand(query, observer))
                assertEquals("rejected", reply.getString("status"))
                assertEquals("Forbidden", reply.getString("error"))
            }
            val history = owner.gateway.readStoryRecord(query.copy(section = StoryRecordSection.HISTORY))
            assertTrue(history.entries.any { it.origin == StoryRecordOrigin.RECORDED_MESSAGE && it.text.contains(claim) &&
                StoryRecordScopedEvent(original, 1) in it.scopedEventSources && it.eventSources.isEmpty() })
            assertTrue("Inspection changed accepted receipts, inventory or time", before == owner.acceptedView())
            assertTrue(saved == owner.gateway.snapshot())
            assertEquals("Inspection dispatched a turn or inference preparation", turnCalls, owner.transport.turnCalls.get())
        }
    }

    @Test fun androidJsonDecoderRejectsMalformedAndPrivatePagesWithoutEchoingPayloads() = runBlocking {
        withRecordFixture { fixture ->
            val owner = fixture.owner()
            val saved = owner.gateway.initialize()
            // This matrix deliberately retains explicit legacy Query1 coverage.
            val query = StoryRecordQuery(StoryRecordContext(checkNotNull(saved.selected), 0), version = 1)
            val original = owner.recordData(query)
            assertEquals(8, StoryRecordWire.decode(original, query).entries.size)
            val canary = "PRIVATE-DECODER-CANARY-9182"
            var cases = 0
            fun rejects(page: JSONObject, requested: StoryRecordQuery) {
                val index = cases++
                try { StoryRecordWire.decode(page, requested); fail("Malformed record accepted at case $index") }
                catch (failure: StoryRecordFailure) {
                    assertEquals(StoryRecordProblem.INVALID_RESPONSE, failure.problem)
                    assertFalse(failure.message.orEmpty().contains(canary))
                }
            }
            val mutations: List<(JSONObject) -> Unit> = listOf(
                { it.put("privacy", "private_omniscient") },
                { it.put("observer", JSONObject().put("kind", "character").put("id", canary)) },
                { it.getJSONObject("scope").put("story", canary) },
                { it.put("head", 1) },
                { it.put("revision", 1) },
                { it.put("view", "history") },
                { it.put("version", true) },
                { it.put("total", -1) },
                { it.put("next_cursor", canary) },
                { it.remove("next_cursor") },
                { it.getJSONArray("rows").getJSONObject(0).put("origin", canary) },
                { it.getJSONArray("rows").getJSONObject(0).put("origin", "subjective_belief") },
                { it.getJSONArray("rows").getJSONObject(0).put("actor", "mira") },
                { it.getJSONArray("rows").getJSONObject(0).put("source", JSONObject().put("kind", "event").put("value", 1)) },
                { it.getJSONArray("rows").put(it.getJSONArray("rows").getJSONObject(0)) },
                { it.getJSONArray("rows").put(1, it.getJSONArray("rows").getJSONObject(0)) },
            )
            for (mutate in mutations) rejects(JSONObject(original.toString()).also(mutate), query)
            val knowledgeQuery = query.copy(section = StoryRecordSection.KNOWLEDGE)
            val knowledge = owner.recordData(knowledgeQuery)
            assertTrue(StoryRecordWire.decode(knowledge, knowledgeQuery).entries.isNotEmpty())
            for (nullable in listOf("subject", "confidence")) {
                rejects(JSONObject(knowledge.toString()).also { it.getJSONArray("rows").getJSONObject(0).remove(nullable) }, knowledgeQuery)
            }
            rejects(JSONObject(knowledge.toString()).also {
                it.getJSONArray("rows").getJSONObject(0).put("sources", JSONArray())
            }, knowledgeQuery)
            val secondQuery = query.copy(cursor = original.getString("next_cursor"))
            val profilePages = listOf(query to original, secondQuery to owner.recordData(secondQuery))
            val itemPage = profilePages.first { (_, page) -> (0 until page.getJSONArray("rows").length()).any {
                page.getJSONArray("rows").getJSONObject(it).getJSONObject("value").getString("type") == "item"
            } }
            for (mutation in listOf<(JSONObject) -> Unit>({ it.remove("return_to") }, { it.put("owner", "mira") })) {
                val page = JSONObject(itemPage.second.toString())
                val rows = page.getJSONArray("rows")
                val item = (0 until rows.length()).map { rows.getJSONObject(it).getJSONObject("value") }
                    .first { it.getString("type") == "item" }.getJSONObject("value")
                mutation(item)
                rejects(page, itemPage.first)
            }
            val huge = JSONObject(original.toString()).put("unsupported", JSONArray().put(canary.repeat(8_000)))
            try { StoryRecordWire.decode(huge, query); fail("Oversized record accepted") }
            catch (failure: StoryRecordFailure) { assertEquals(StoryRecordProblem.TOO_LARGE, failure.problem) }
            assertEquals(0L, owner.gateway.snapshot().revision)
            assertTrue(owner.gateway.commitAsync(owner.gateway.respond(DemoAction.GIVE_POTION, 0, DemoMode.ACCEPTED)) is DemoResult.Accepted)
            val committed = owner.gateway.snapshot()
            val accepted = owner.acceptedView()
            val historyQuery = StoryRecordQuery(StoryRecordContext(checkNotNull(committed.selected), 1), StoryRecordSection.HISTORY, version = 1)
            val history = owner.recordData(historyQuery)
            for (ids in listOf(JSONArray(), JSONArray().put(1).put(1))) {
                val page = JSONObject(history.toString())
                val rows = page.getJSONArray("rows")
                (0 until rows.length()).map { rows.getJSONObject(it) }.first { it.getString("kind") == "message" }
                    .put("event_ids", ids)
                rejects(page, historyQuery)
            }
            assertTrue("Decoder rejection changed accepted state", accepted == owner.acceptedView())
        }
    }
}

internal fun assertNoRecordActivities() {
    InstrumentationRegistry.getInstrumentation().runOnMainSync {
        val monitor = ActivityLifecycleMonitorRegistry.getInstance()
        for (stage in Stage.values().filter { it != Stage.DESTROYED }) {
            assertEquals("Unexpected live activity at stage ${stage.name}", 0, monitor.getActivitiesInStage(stage).size)
        }
    }
}

/** Shared only by these two test files. Replies are observed, never changed. */
internal class RecordTransport(context: Context) : WorkspaceTransport {
    private val native = NativeWorkspaceTransport(context)
    val inFlight = AtomicInteger()
    val turnCalls = AtomicInteger()
    var session: String? = null
    var scope: JSONObject? = null
    override suspend fun exchange(command: JSONObject): JSONObject {
        inFlight.incrementAndGet()
        try {
            if (command.getString("op") in listOf("submit", "prepare", "commit")) turnCalls.incrementAndGet()
            val reply = native.exchange(command)
            if (command.getString("op") in listOf("create", "resume") && reply.getString("status") == "ok") {
                val data = reply.getJSONObject("data")
                session = data.getString("session")
                scope = JSONObject(data.getJSONObject("scope").toString())
            }
            return reply
        } finally { inFlight.decrementAndGet() }
    }
    override fun close() = native.close()
}

internal class RecordOwner(val transport: RecordTransport) {
    val gateway = DurableGateway(transport)
    fun scoped(op: String) = JSONObject().put("op", op).put("session", checkNotNull(transport.session))
        .put("scope", checkNotNull(transport.scope))
    suspend fun data(command: JSONObject): JSONObject {
        val reply = transport.exchange(command)
        assertEquals("Actual native operation was rejected", "ok", reply.getString("status"))
        return reply.getJSONObject("data")
    }
    suspend fun acceptedView(): String {
        val opened = data(scoped("open"))
        return data(scoped("play_snapshot").put("expected_revision", opened.getLong("revision"))).toString()
    }
    fun recordCommand(query: StoryRecordQuery, observer: JSONObject = JSONObject().put("kind", "player")) =
        JSONObject().put("op", "inspection_query").put("session", checkNotNull(transport.session)).put("query", JSONObject()
            .put("version", query.version).put("scope", JSONObject().put("story", query.context.story.story).put("branch", query.context.story.branch))
            .put("expected_head", query.context.revision).put("at_revision", JSONObject.NULL)
            .put("observer", observer).put("view", query.section.wire).put("limit", 8)
            .put("search", query.search).put("cursor", query.cursor ?: JSONObject.NULL))
    suspend fun recordData(query: StoryRecordQuery) = data(recordCommand(query))
    suspend fun commitIntent(intent: JSONObject) {
        val revision = data(scoped("open")).getLong("revision")
        val turn = UUID.randomUUID().toString()
        val request = JSONObject().put("version", 1).put("scope", checkNotNull(transport.scope))
            .put("turn", turn).put("expected_revision", revision).put("intent", intent)
        assertEquals("queued", data(JSONObject().put("op", "submit").put("session", checkNotNull(transport.session))
            .put("mode", "accepted").put("request", request)).getString("phase"))
        assertEquals("ready", data(scoped("prepare").put("turn", turn)).getString("phase"))
        assertEquals("committed", data(scoped("commit").put("turn", turn)).getString("phase"))
    }
}

internal class RecordFixture {
    companion object { private val ownershipClean = AtomicBoolean(true) }
    private val parent = InstrumentationRegistry.getInstrumentation().targetContext.noBackupFilesDir.canonicalFile
    val root: File
    private val owners = mutableListOf<RecordOwner>()
    val stores = mutableListOf<ViewModelStore>()
    init {
        check(ownershipClean.get()) { "Prior record fixture ownership is uncertain" }
        root = File(parent, "synthetic-story-record-${UUID.randomUUID()}").canonicalFile
        check(root.parentFile == parent && root.mkdir())
    }
    private val context = object : ContextWrapper(InstrumentationRegistry.getInstrumentation().targetContext) {
        override fun getApplicationContext(): Context = this
        override fun getNoBackupFilesDir(): File = root
    }
    fun owner() = RecordOwner(RecordTransport(context)).also { owners += it }
    suspend fun closeOwnersAndDrain() {
        try {
            withContext(Dispatchers.Main) { stores.forEach { it.clear() }; owners.forEach { it.gateway.close() } }
            withTimeout(8_000) { while (owners.any { it.transport.inFlight.get() != 0 }) delay(5) }
            withContext(Dispatchers.IO) {
                withTimeout(8_000) {
                    while (true) {
                        val handles = mutableListOf<Long>()
                        try {
                            repeat(4) { NativeWorkspace.open(File(root, "workspace-v1/stories.sqlite3").absolutePath)
                                .takeIf { it != 0L }?.let(handles::add) }
                            if (handles.size == 4) break
                        } finally { handles.forEach(NativeWorkspace::close) }
                        delay(5)
                    }
                }
            }
        } catch (failure: Throwable) { ownershipClean.set(false); throw failure }
    }
    suspend fun cleanup() {
        closeOwnersAndDrain()
        withContext(Dispatchers.IO) {
            check(root.canonicalFile.parentFile == parent && root.name.startsWith("synthetic-story-record-"))
            check(root.deleteRecursively()) { "Owned record fixture cleanup failed" }
        }
    }
}

internal suspend fun withRecordFixture(body: suspend (RecordFixture) -> Unit) {
    val fixture = RecordFixture()
    val failures = mutableListOf<Throwable>()
    try { body(fixture) } catch (failure: Throwable) { failures += failure }
    try { withContext(NonCancellable) { fixture.cleanup() } } catch (failure: Throwable) { failures += failure }
    MultipleFailureException.assertEmpty(failures)
}

/* Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0 */
package org.locallore.app

import android.os.SystemClock
import androidx.lifecycle.ViewModelStore
import androidx.test.ext.junit.runners.AndroidJUnit4
import kotlinx.coroutines.CompletableDeferred
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.delay
import kotlinx.coroutines.runBlocking
import kotlinx.coroutines.withContext
import kotlinx.coroutines.withTimeout
import org.json.JSONObject
import org.junit.After
import org.junit.Assert.*
import org.junit.Before
import org.junit.Test
import org.junit.runner.RunWith
import java.util.concurrent.atomic.AtomicInteger

/** Actual Rust play-v2 through JNI in an owned synthetic workspace, with no language model. */
@RunWith(AndroidJUnit4::class)
class PlayInputInstrumentedTest {
    @Before fun noActivityBefore() = assertNoRecordActivities()
    @After fun noActivityAfter() = assertNoRecordActivities()

    @Test fun originalActionAndDialogueCommitAtomicallyAndReplayWithoutAnotherGeneration() = runBlocking {
        withRecordFixture { fixture ->
            var owner = fixture.owner()
            val initial = owner.gateway.initialize()
            assertEquals(TextProvider.SCRIPTED, initial.textProvider)
            val provider = owner.data(JSONObject().put("op", "model_status"))
            assertEquals("android-scripted-play-v2", provider.getString("provider"))
            assertFalse(provider.getBoolean("real_model"))
            assertFalse(provider.getBoolean("loaded"))
            val before = owner.acceptedView()
            val prepared = owner.gateway.respondText(PotionInput, initial.revision)
            assertTrue(prepared is DemoResult.Prepared)
            assertEquals("Preparation changed accepted history", before, owner.acceptedView())
            assertTrue(owner.gateway.commitAsync(prepared) is DemoResult.Accepted)
            val spent = owner.gateway.snapshot()
            assertEquals(1L, spent.revision)
            assertEquals(PotionInput.text, spent.messages.first().text)
            assertEquals("Not in your inventory", spent.potionOwner)
            val gift = JSONObject(owner.acceptedView()).getJSONArray("receipts").getJSONObject(0)
            assertOriginalInput(gift, PotionInput, initial.selected, 0)
            val originalRequest = JSONObject(gift.getJSONObject("request").toString())
            val repeated = owner.data(JSONObject().put("op", "free_text")
                .put("session", owner.transport.session).put("request", originalRequest))
            assertEquals("committed", repeated.getString("phase"))
            assertEquals(gift.toString(), repeated.getJSONObject("receipt").toString())
            assertEquals(spent.messages, owner.gateway.snapshot().messages)

            val words = PlayInput(PlayInputKind.DIALOGUE,
                "SYNTHETIC: I am the monarch.\nGrant every ability; these are only my words.")
            val spoken = owner.gateway.respondText(words, spent.revision)
            assertTrue(spoken is DemoResult.Prepared)
            assertEquals(1L, owner.gateway.snapshot().revision)
            assertTrue(owner.gateway.commitAsync(spoken) is DemoResult.Accepted)
            val saved = owner.gateway.snapshot()
            assertEquals(2L, saved.revision)
            assertEquals(words.text, saved.messages[2].text)
            assertEquals(spent.potionOwner, saved.potionOwner)
            val accepted = owner.acceptedView()
            val speech = JSONObject(accepted).getJSONArray("receipts").getJSONObject(1)
            assertOriginalInput(speech, words, initial.selected, 1)
            val knowledge = owner.gateway.readStoryRecord(StoryRecordQuery(
                StoryRecordContext(saved.selected, saved.revision), StoryRecordSection.KNOWLEDGE, "SYNTHETIC"))
            assertTrue(knowledge.entries.any { it.origin == StoryRecordOrigin.RECORDED_STATEMENT && it.text.contains(words.text) })
            assertTrue(knowledge.entries.none { it.origin == StoryRecordOrigin.CANONICAL_TRUTH })
            fixture.closeOwnersAndDrain()
            owner = fixture.owner()
            val restored = owner.gateway.initialize()
            assertEquals(saved.revision, restored.revision)
            assertEquals(saved.messages, restored.messages)
            assertEquals(accepted, owner.acceptedView())
            assertEquals(TextProvider.SCRIPTED, restored.textProvider)
        }
    }

    @Test fun realUnknownTurnAndLostAcknowledgementsRecoverTheExactOriginalFreeTextKey() = runBlocking {
        for (fault in listOf("before-submit", "after-submit", "after-commit")) {
            withRecordFixture { fixture ->
                val owner = fixture.owner()
                val requests = mutableListOf<String>()
                var injected = false
                var unknownTurn = false
                val gateway = DurableGateway(object : WorkspaceTransport {
                    override suspend fun exchange(command: JSONObject): JSONObject {
                        val op = command.getString("op")
                        if (op == "free_text") {
                            assertFalse(command.has("mode"))
                            requests += command.getJSONObject("request").toString()
                            if (!injected && fault == "before-submit") {
                                injected = true
                                error("Synthetic acknowledgement fault")
                            }
                        }
                        val reply = owner.transport.exchange(command)
                        if (op == "turn_status" && reply.optString("error") == "UnknownTurn") unknownTurn = true
                        if (!injected && ((op == "free_text" && fault == "after-submit") ||
                                (op == "commit" && fault == "after-commit"))) {
                            injected = true
                            error("Synthetic acknowledgement fault")
                        }
                        return reply
                    }
                    override fun close() = owner.transport.close()
                })
                try {
                    val initial = gateway.initialize()
                    if (fault == "after-commit") {
                        assertTrue(gateway.commitAsync(gateway.respondText(PotionInput, 0)) is DemoResult.Accepted)
                    } else {
                        try { gateway.respondText(PotionInput, 0); fail("Fault was not injected") }
                        catch (_: IllegalStateException) { }
                        assertEquals(0L, gateway.snapshot().revision)
                    }
                    val recovered = gateway.recoverSaved()
                    assertTrue(fault, injected)
                    assertEquals(fault, fault == "before-submit", unknownTurn)
                    assertEquals(fault, if (fault == "before-submit") 2 else 1, requests.size)
                    assertEquals(fault, 1, requests.toSet().size)
                    assertEquals(1L, recovered.revision)
                    assertEquals(2, recovered.messages.size)
                    val receipts = JSONObject(owner.acceptedView()).getJSONArray("receipts")
                    assertEquals(1, receipts.length())
                    val receipt = receipts.getJSONObject(0)
                    assertEquals(JSONObject(requests.first()).toString(), receipt.getJSONObject("request").toString())
                    assertOriginalInput(receipt, PotionInput, initial.selected, 0)
                    assertEquals(recovered.messages, gateway.recoverSaved().messages)
                    fixture.closeOwnersAndDrain()
                    val reopened = fixture.owner()
                    assertEquals(recovered.messages, reopened.gateway.initialize().messages)
                    assertEquals(1, JSONObject(reopened.acceptedView()).getJSONArray("receipts").length())
                } finally { gateway.close() }
            }
        }
    }

    @Test fun cancellingOrDisposingActualPendingPreparationPreservesCanonAndReleasesOwners() = runBlocking {
        for (dispose in listOf(false, true)) {
            withRecordFixture { fixture ->
                val owner = fixture.owner()
                val entered = CompletableDeferred<Unit>()
                var turn: String? = null
                val gateway = DurableGateway(object : WorkspaceTransport {
                    override suspend fun exchange(command: JSONObject): JSONObject {
                        if (command.getString("op") == "free_text")
                            turn = command.getJSONObject("request").getString("turn")
                        if (command.getString("op") == "prepare") entered.complete(Unit)
                        return owner.transport.exchange(command)
                    }
                    override fun close() = owner.transport.close()
                })
                val model = inputModel(fixture, gateway)
                awaitEventShell(model)
                val before = owner.acceptedView()
                withContext(Dispatchers.Main) { model.submitText(PotionInput) }
                withTimeout(5_000) { entered.await() }
                // Observe the actual native worker, rather than infer it from a UI busy flag.
                withTimeout(3_000) {
                    while (owner.data(owner.scoped("turn_status").put("turn", checkNotNull(turn)))
                            .getString("phase") != "running") delay(5)
                }
                assertTrue(model.state.value.busy)
                assertEquals(0L, model.state.value.revision)
                assertTrue(model.state.value.messages.isEmpty())
                val start = SystemClock.elapsedRealtime()
                withContext(Dispatchers.Main) {
                    if (dispose) fixture.stores.forEach { it.clear() } else model.cancel()
                }
                withTimeout(3_000) {
                    while (model.state.value.busy || owner.transport.inFlight.get() != 0) delay(5)
                }
                assertTrue("Pending native cancellation/disposal exceeded the test bound",
                    SystemClock.elapsedRealtime() - start < 3_000)
                assertEquals(0L, model.state.value.revision)
                assertTrue(model.state.value.messages.isEmpty())
                if (!dispose) {
                    assertFalse(model.state.value.recoveryRequired)
                    assertEquals(before, owner.acceptedView())
                }
                fixture.closeOwnersAndDrain() // Reacquires all four real JNI slots before continuing.
                val reopened = fixture.owner()
                assertEquals(0L, reopened.gateway.initialize().revision)
                assertEquals(before, reopened.acceptedView())
            }
        }
    }

    @Test fun cancelAndDisposalFenceADeferredSubmissionBeforeTheNativeExchange() = runBlocking {
        for (dispose in listOf(false, true)) {
            withRecordFixture { fixture ->
                val owner = fixture.owner()
                val entered = CompletableDeferred<Unit>()
                val release = CompletableDeferred<Unit>()
                val finished = CompletableDeferred<Unit>()
                val cancels = AtomicInteger()
                var original: JSONObject? = null
                var cancelledTurn: String? = null
                val gateway = DurableGateway(object : WorkspaceTransport {
                    override suspend fun exchange(command: JSONObject): JSONObject {
                        if (command.getString("op") == "free_text") {
                            original = JSONObject(command.getJSONObject("request").toString())
                            entered.complete(Unit)
                            try { release.await(); return owner.transport.exchange(command) }
                            finally { finished.complete(Unit) }
                        }
                        if (command.getString("op") == "cancel") {
                            cancelledTurn = command.getString("turn")
                            cancels.incrementAndGet()
                        }
                        return owner.transport.exchange(command)
                    }
                    override fun close() = owner.transport.close()
                })
                val model = inputModel(fixture, gateway)
                awaitEventShell(model)
                val before = owner.acceptedView()
                try {
                    withContext(Dispatchers.Main) { model.submitText(PotionInput) }
                    withTimeout(5_000) { entered.await() }
                    withContext(Dispatchers.Main) {
                        if (dispose) fixture.stores.forEach { it.clear() } else model.cancel()
                    }
                    delay(40)
                    assertEquals("Cancellation crossed the native submit ordering gate", 0, cancels.get())
                    if (!dispose) assertTrue("Cancel completed before its original submission", model.state.value.busy)
                    release.complete(Unit)
                    withTimeout(5_000) { finished.await() }
                    if (!dispose) {
                        awaitEventShell(model)
                        assertEquals(1, cancels.get())
                        assertEquals(checkNotNull(original).getString("turn"), cancelledTurn)
                        val terminal = owner.data(owner.scoped("turn_status").put("turn", cancelledTurn))
                        assertEquals("cancelled", terminal.getString("phase"))
                        assertEquals(before, owner.acceptedView())
                    }
                    assertEquals(0L, model.state.value.revision)
                    assertTrue(model.state.value.messages.isEmpty())
                    fixture.closeOwnersAndDrain()
                    val reopened = fixture.owner()
                    assertEquals(0L, reopened.gateway.initialize().revision)
                    assertEquals(before, reopened.acceptedView())
                } finally { release.complete(Unit) }
            }
        }
    }
}

internal val PotionInput = PlayInput(PlayInputKind.ACTION, "I give my last potion to Mira.")

private fun assertOriginalInput(receipt: JSONObject, input: PlayInput, story: SavedStory, revision: Long) {
    assertEquals(2, receipt.getJSONObject("play").getInt("version"))
    assertEquals("android-scripted-play-v2", receipt.getJSONObject("play").getJSONObject("profile").getString("id"))
    val request = receipt.getJSONObject("request")
    assertEquals(1, request.getInt("version"))
    assertEquals(revision, request.getLong("expected_revision"))
    assertEquals(story.story, request.getJSONObject("scope").getString("story"))
    assertEquals(story.branch, request.getJSONObject("scope").getString("branch"))
    assertTrue(request.getString("turn").isNotBlank())
    assertEquals("free_text", request.getJSONObject("intent").getString("kind"))
    val original = request.getJSONObject("intent").getJSONObject("value")
    assertEquals(input.kind.wire, original.getString("kind"))
    assertEquals(input.text, original.getString("text"))
}

internal suspend fun inputModel(fixture: RecordFixture, gateway: DemoGateway): ShellViewModel = withContext(Dispatchers.Main) {
    val store = ViewModelStore().also { fixture.stores += it }
    ShellViewModel(gateway).also { store.put("synthetic-input", it) }
}

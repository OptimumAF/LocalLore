/* Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0 */
package org.locallore.app

import androidx.compose.ui.test.*
import androidx.compose.ui.test.junit4.createEmptyComposeRule
import androidx.lifecycle.Lifecycle
import androidx.lifecycle.ViewModelProvider
import androidx.test.core.app.ActivityScenario
import androidx.test.ext.junit.runners.AndroidJUnit4
import androidx.test.filters.SdkSuppress
import androidx.test.platform.app.InstrumentationRegistry
import androidx.test.runner.lifecycle.ActivityLifecycleCallback
import androidx.test.runner.lifecycle.ActivityLifecycleMonitorRegistry
import androidx.test.runner.lifecycle.Stage
import java.util.concurrent.atomic.AtomicBoolean
import java.util.concurrent.atomic.AtomicReference
import org.json.JSONObject
import org.junit.After
import org.junit.Rule
import org.junit.Test
import org.junit.runner.RunWith

/** Ordinary setup Start transition and real ShellViewModel; no test provider/factory substitutes. */
abstract class PhysicalModelUiHarness : PhysicalModelHarness() {
    @get:Rule val compose = createEmptyComposeRule()
    private var setup: ActivityScenario<LocalModelSetupActivity>? = null
    internal lateinit var play: LiteRtPlayActivity
    internal lateinit var actual: NativeWorkspaceTransport
    internal lateinit var model: ShellViewModel
    internal fun main(action: () -> Unit) = InstrumentationRegistry.getInstrumentation().runOnMainSync { action() }
    internal fun launch(deadline: PhoneDeadline) {
        check(CandidateLocalModel.canStart())
        val seen = AtomicReference<LiteRtPlayActivity?>()
        val duplicate = AtomicBoolean()
        val monitor = ActivityLifecycleMonitorRegistry.getInstance()
        val callback = ActivityLifecycleCallback { activity, stage ->
            if (activity.javaClass == LiteRtPlayActivity::class.java && stage == Stage.RESUMED) {
                if (seen.get() != null && seen.get() !== activity) duplicate.set(true)
                else seen.set(activity as LiteRtPlayActivity)
            }
        }
        main { monitor.addLifecycleCallback(callback) }
        try {
            lateinit var activity: LocalModelSetupActivity
            setup = ActivityScenario.launch(LocalModelSetupActivity::class.java)
            requireNotNull(setup).onActivity { check(it.javaClass == LocalModelSetupActivity::class.java); activity = it }
            compose.waitUntil(deadline.remaining(90_000)) { activity.setupController.state.value.phase == LocalModelSetupPhase.READY }
            main { check(activity.lifecycle.currentState == Lifecycle.State.RESUMED && CandidateLocalModel.canStart()) }
            compose.onNodeWithTag("model-start").performScrollTo().assertIsEnabled().performClick()
            compose.waitUntil(deadline.remaining()) { seen.get() != null && activity.isDestroyed }
            check(!duplicate.get())
            play = requireNotNull(seen.get())
            main {
                check(play.javaClass == LiteRtPlayActivity::class.java)
                actual = requireNotNull(play.constructedWorkspaceTransport)
                model = ViewModelProvider(play)[ShellViewModel::class.java]
            }
            settled(deadline)
            check(model.state.value.textProvider == TextProvider.LOCAL && model.state.value.selectedStory != null)
            trace() // Missing observation is never coerced to zero.
        } finally { main { monitor.removeLifecycleCallback(callback) } }
    }
    internal fun trace() = requireNotNull(CandidateLocalModel.receiptWorkerSnapshot())
    internal fun settled(deadline: PhoneDeadline) {
        compose.waitUntil(deadline.remaining()) { !model.state.value.busy }
        check(!model.state.value.recoveryRequired && !model.state.value.preparingResponse && !model.state.value.checkingCancellation)
        main { check(play.lifecycle.currentState == Lifecycle.State.RESUMED) }
    }
    internal fun node(tag: String): SemanticsNodeInteraction {
        compose.onNodeWithTag("story-list").performScrollToNode(hasTestTag(tag))
        return compose.onNodeWithTag(tag)
    }
    internal fun submit(kind: PlayInputKind, text: String, deadline: PhoneDeadline) {
        node("play-kind-${kind.wire}").performClick().assertIsSelected()
        node("play-input").performTextReplacement(text)
        node("play-input").assertTextContains(text)
        node("play-send").assertIsEnabled().performClick()
        settled(deadline)
    }
    internal suspend fun view(): JSONObject {
        check(!model.state.value.busy && !model.state.value.recoveryRequired)
        val chosen = requireNotNull(model.state.value.selectedStory)
        val scope = JSONObject().put("story", chosen.story).put("branch", chosen.branch)
        val handle = actual.forkHandle()
        val session = data(actual, JSONObject().put("op", "resume").put("scope", scope))
        return data(actual, JSONObject().put("op", "play_snapshot").put("session", session.getString("session"))
            .put("scope", scope).put("expected_revision", model.state.value.revision)).also { check(actual.forkHandle() == handle) }
    }
    internal fun knowledge(deadline: PhoneDeadline): List<StoryRecordEntry> {
        main { model.openStoryRecord() }
        compose.waitUntil(deadline.remaining()) { model.storyRecord.value.let { it.visible && !it.loading && it.problem == null } }
        main { model.recordSection(StoryRecordSection.KNOWLEDGE) }
        compose.waitUntil(deadline.remaining()) { model.storyRecord.value.let {
            it.visible && !it.loading && it.problem == null && it.section == StoryRecordSection.KNOWLEDGE
        } }
        val state = model.storyRecord.value
        check(state.nextCursor == null && state.total == state.entries.size)
        main { model.closeStoryRecord() }
        return state.entries
    }
    internal fun transcript(expected: Int) {
        check(model.state.value.messages.size == expected)
        for (message in model.state.value.messages) {
            val tag = "message-body-${message.id}"
            compose.onNodeWithTag("story-list").performScrollToNode(hasTestTag(tag))
            compose.onNodeWithTag(tag).assertTextEquals(message.text).assertIsDisplayed()
        }
    }
    internal fun closePlay(deadline: PhoneDeadline) {
        main { if (!play.isDestroyed) play.finish() }
        compose.waitUntil(deadline.remaining(5_000)) { play.isDestroyed }
        setup?.close(); setup = null
    }
    @After fun closeOnlyOwnedActivities() {
        if (::play.isInitialized && !play.isDestroyed) main { play.finish() }
        setup?.close(); setup = null
    }
    internal fun gift(receipt: JSONObject) {
        val intent = receipt.getJSONObject("request").getJSONObject("intent")
        check(intent.getString("kind") == "free_text" && intent.getJSONObject("value").getString("kind") == "action" &&
            intent.getJSONObject("value").getString("text") == PHONE_GIFT)
        val events = receipt.getJSONArray("events"); check(events.length() == 1)
        val outcome = events.getJSONObject(0).getJSONObject("outcome")
        check(outcome.getString("effect") == "given" && outcome.getString("item") == "potion" &&
            outcome.getString("from") == "player" && outcome.getString("to") == "mira" && outcome.getInt("quantity") == 1)
    }
}

@RunWith(AndroidJUnit4::class)
@SdkSuppress(minSdkVersion = 36)
class PhysicalModelGiftTest : PhysicalModelUiHarness() {
    @Test fun commitsGuardedPhoneGift() {
        val deadline = selected(PhysicalModelGiftTest::class.java, PhysicalModelPhase.GIFT)
        val checks = linkedMapOf<String, Boolean>()
        val env = io(deadline) { PhoneEnvironment(context) }
        val prior = io(deadline) { env.prior(PhysicalModelPhase.GIFT) }
        checked(checks, "prior_cancel_exact", prior.first.phase == PhysicalModelPhase.CANCEL)
        checked(checks, "process_identity_changed", prior.first.identity != env.identity)
        launch(deadline)
        val initial = io(deadline) { view() }
        checked(checks, "prior_story_exact", phoneHash(initial.getJSONObject("scope")) == prior.first.extras["story_sha256"])
        checked(checks, "initial_zero", initial.getLong("revision") == 0L && initial.getJSONArray("receipts").length() == 0 &&
            initial.getJSONObject("inventory").getJSONObject("potion").getString("owner") == "player")
        check(phoneWorkerZero(trace()))
        submit(PlayInputKind.ACTION, PHONE_GIFT, deadline)
        node("notice").assertTextEquals("Outcome accepted and saved by the local engine.")
        checked(checks, "fixed_input_once", model.state.value.messages.count { it.isPlayer && it.text == PHONE_GIFT } == 1)
        transcript(2)
        val after = io(deadline) { view() }
        val receipts = after.getJSONArray("receipts")
        checked(checks, "canonical_revision_one", after.getLong("revision") == 1L)
        checked(checks, "single_receipt", receipts.length() == 1)
        gift(receipts.getJSONObject(0))
        checked(checks, "gift_exact", !after.getJSONObject("inventory").has("potion"))
        val closed = trace(); phoneWorkerClosed(closed)
        checked(checks, "actual_two_roles", closed.creationsTotal == 2)
        checked(checks, "worker_close_verified", true)
        val record = receipts.getJSONObject(0).getJSONObject("play")
        val repairs = record.getInt("repairs"); val fallback = record.getBoolean("fallback")
        checked(checks, "zero_repair", repairs == 0); checked(checks, "zero_fallback", !fallback)
        val handle = io(deadline) {
            val accepted = requireNotNull(CandidateLocalModel.store(context).installed())
            val profile = JSONObject(localText(CandidateLocalModel.config(accepted).profileBytes(), 4096))
            check(phoneCanonical(profile) == phoneCanonical(record.getJSONObject("profile")))
            checked(checks, "accepted_post_sdk_full_recheck", true)
            actual.forkHandle()
        }
        closePlay(deadline)
        io(deadline) {
            checked(checks, "native_handle_closed", nativeClosed(handle, deadline))
            val memory = env.storage.snapshot(); checked(checks, "memory_eligible", PhysicalModelPolicy.ongoing(memory) == memory)
            val final = trace(); phoneWorkerClosed(final)
            env.write(PhysicalModelPhase.GIFT, deadline, PhoneCounts(), checks, prior, mapOf(
                "revision" to 1L, "receipt_count" to 1L, "receipts_sha256" to phoneHash(receipts),
                "story_sha256" to phoneHash(after.getJSONObject("scope")), "worker_trace_sha256" to phoneWorkerHash(final),
                "repairs" to repairs, "fallback" to fallback, "gift_receipt_sha256" to phoneHash(receipts.getJSONObject(0))),
                mapOf("gift-worker-v2.json" to final))
        }
    }
}

@RunWith(AndroidJUnit4::class)
@SdkSuppress(minSdkVersion = 36)
class PhysicalModelDialogueTest : PhysicalModelUiHarness() {
    @Test fun recordsLiteralPhoneDialogue() {
        val deadline = selected(PhysicalModelDialogueTest::class.java, PhysicalModelPhase.DIALOGUE)
        val checks = linkedMapOf<String, Boolean>()
        val env = io(deadline) { PhoneEnvironment(context) }
        val prior = io(deadline) { env.prior(PhysicalModelPhase.DIALOGUE) }
        checked(checks, "prior_gift_exact", prior.first.phase == PhysicalModelPhase.GIFT)
        checked(checks, "process_identity_changed", prior.first.identity != env.identity)
        launch(deadline)
        val initial = io(deadline) { view() }
        checked(checks, "prior_story_exact", phoneHash(initial.getJSONObject("scope")) == prior.first.extras["story_sha256"])
        val first = initial.getJSONArray("receipts")
        checked(checks, "gift_preserved", initial.getLong("revision") == 1L && first.length() == 1 &&
            phoneHash(first) == prior.first.extras["receipts_sha256"] && phoneHash(first.getJSONObject(0)) == prior.first.extras["gift_receipt_sha256"])
        val truths = knowledge(deadline).filter { it.origin == StoryRecordOrigin.CANONICAL_TRUTH }
        check(truths.isNotEmpty())
        submit(PlayInputKind.ACTION, "I use ability blink.", deadline)
        node("notice").assertTextEquals("Blink is not learned. Nothing changed.")
        check(io(deadline) { phoneHash(view()) == phoneHash(initial) })
        submit(PlayInputKind.ACTION, PHONE_GIFT, deadline)
        node("notice").assertTextEquals("You no longer hold the potion. Nothing changed.")
        check(io(deadline) { phoneHash(view()) == phoneHash(initial) })
        val guards = trace()
        checked(checks, "invalid_actions_no_sdk", phoneWorkerZero(guards))
        submit(PlayInputKind.DIALOGUE, PHONE_DIALOGUE, deadline)
        node("notice").assertTextEquals("Outcome accepted and saved by the local engine.")
        transcript(4)
        val after = io(deadline) { view() }
        val receipts = after.getJSONArray("receipts")
        checked(checks, "canonical_revision_two", after.getLong("revision") == 2L)
        checked(checks, "two_receipts", receipts.length() == 2)
        check(phoneHash(receipts.getJSONObject(0)) == prior.first.extras["gift_receipt_sha256"])
        val receipt = receipts.getJSONObject(1)
        val request = receipt.getJSONObject("request")
        val intent = request.getJSONObject("intent")
        val events = receipt.getJSONArray("events"); check(events.length() == 1)
        val event = events.getJSONObject(0); val outcome = event.getJSONObject("outcome")
        checked(checks, "literal_input", request.getLong("expected_revision") == 1L && phoneHash(request.getJSONObject("scope")) == phoneHash(after.getJSONObject("scope")) &&
            event.getLong("sequence") == 2L && outcome.getLong("source") == 2L && outcome.getString("effect") == "said" &&
            outcome.getString("speaker") == "player" && outcome.getString("text") == PHONE_DIALOGUE &&
            outcome.getJSONArray("audience").length() == 1 && outcome.getJSONArray("audience").getString(0) == "mira" &&
            intent.getString("kind") == "free_text" && intent.getJSONObject("value").getString("kind") == "dialogue" &&
            intent.getJSONObject("value").getString("text") == PHONE_DIALOGUE &&
            model.state.value.messages.count { it.isPlayer && it.text == PHONE_DIALOGUE } == 1)
        val knowledge = knowledge(deadline)
        checked(checks, "statement_not_truth", knowledge.count { it.origin == StoryRecordOrigin.RECORDED_STATEMENT && it.text == PHONE_DIALOGUE &&
            it.sources == listOf("Event #2") } == 1 && knowledge.none { it.origin == StoryRecordOrigin.CANONICAL_TRUTH && it.text == PHONE_DIALOGUE })
        checked(checks, "known_truth_unchanged", knowledge.filter { it.origin == StoryRecordOrigin.CANONICAL_TRUTH } == truths &&
            phoneHash(initial.getJSONObject("player").getJSONObject("facts")) == phoneHash(after.getJSONObject("player").getJSONObject("facts")))
        phoneWorkerClosed(trace()); checked(checks, "roles_closed", true)
        val record = receipt.getJSONObject("play")
        val repairs = record.getInt("repairs"); val fallback = record.getBoolean("fallback")
        checked(checks, "zero_repair", repairs == 0); checked(checks, "zero_fallback", !fallback)
        val handle = io(deadline) {
            val accepted = requireNotNull(CandidateLocalModel.store(context).installed())
            val profile = JSONObject(localText(CandidateLocalModel.config(accepted).profileBytes(), 4096))
            check(phoneCanonical(profile) == phoneCanonical(record.getJSONObject("profile")))
            checked(checks, "accepted_post_sdk_full_recheck", true)
            actual.forkHandle()
        }
        closePlay(deadline)
        io(deadline) {
            checked(checks, "native_handle_closed", nativeClosed(handle, deadline))
            val memory = env.storage.snapshot(); checked(checks, "memory_eligible", PhysicalModelPolicy.ongoing(memory) == memory)
            val final = trace(); phoneWorkerClosed(final)
            env.write(PhysicalModelPhase.DIALOGUE, deadline, PhoneCounts(), checks, prior, mapOf(
                "revision" to 2L, "receipt_count" to 2L, "receipts_sha256" to phoneHash(receipts), "story_sha256" to phoneHash(after.getJSONObject("scope")),
                "worker_trace_sha256" to phoneWorkerHash(final), "guards_trace_sha256" to phoneWorkerHash(guards), "repairs" to repairs, "fallback" to fallback,
                "gift_receipt_sha256" to phoneHash(receipts.getJSONObject(0)), "dialogue_receipt_sha256" to phoneHash(receipt)),
                mapOf("guards-worker-v2.json" to guards, "dialogue-worker-v2.json" to final))
        }
    }
}

@RunWith(AndroidJUnit4::class)
@SdkSuppress(minSdkVersion = 36)
class PhysicalModelReopenTest : PhysicalModelUiHarness() {
    @Test fun reopensPhoneReceiptsWithoutInference() {
        val deadline = selected(PhysicalModelReopenTest::class.java, PhysicalModelPhase.REOPEN)
        val checks = linkedMapOf<String, Boolean>()
        val env = io(deadline) { PhoneEnvironment(context) }
        val prior = io(deadline) { env.prior(PhysicalModelPhase.REOPEN) }
        checked(checks, "prior_dialogue_exact", prior.first.phase == PhysicalModelPhase.DIALOGUE)
        checked(checks, "process_identity_changed", prior.first.identity != env.identity)
        launch(deadline)
        checked(checks, "setup_ready", model.state.value.textProvider == TextProvider.LOCAL)
        val after = io(deadline) { view() }
        checked(checks, "prior_story_exact", phoneHash(after.getJSONObject("scope")) == prior.first.extras["story_sha256"])
        checked(checks, "canonical_revision_two", after.getLong("revision") == 2L)
        val receipts = after.getJSONArray("receipts")
        checked(checks, "receipts_exact", receipts.length() == 2 && phoneHash(receipts) == prior.first.extras["receipts_sha256"] &&
            phoneHash(receipts.getJSONObject(0)) == prior.first.extras["gift_receipt_sha256"] && phoneHash(receipts.getJSONObject(1)) == prior.first.extras["dialogue_receipt_sha256"])
        transcript(4)
        checked(checks, "retained_transcript", model.state.value.messages.filter { it.isPlayer }.map { it.text } == listOf(PHONE_GIFT, PHONE_DIALOGUE))
        checked(checks, "no_text", !model.state.value.busy && !model.state.value.preparingResponse && !model.state.value.checkingCancellation)
        checked(checks, "no_sdk", phoneWorkerZero(trace()))
        val counts = PhoneCounts()
        checked(checks, "source_unopened", counts.snapshot() == PhysicalSourceCounts()) // No PhoneSource is constructed in this phase.
        val handle = io(deadline) {
            checked(checks, "accepted_recheck", CandidateLocalModel.store(context).installed() != null)
            actual.forkHandle()
        }
        closePlay(deadline)
        io(deadline) {
            checked(checks, "native_handle_closed", nativeClosed(handle, deadline))
            val memory = env.storage.snapshot(); checked(checks, "memory_eligible", PhysicalModelPolicy.ongoing(memory) == memory)
            val final = trace(); check(phoneWorkerZero(final))
            env.write(PhysicalModelPhase.REOPEN, deadline, counts, checks, prior, mapOf(
                "revision" to 2L, "receipt_count" to 2L, "receipts_sha256" to phoneHash(receipts), "story_sha256" to phoneHash(after.getJSONObject("scope")),
                "worker_trace_sha256" to phoneWorkerHash(final), "gift_receipt_sha256" to phoneHash(receipts.getJSONObject(0)),
                "dialogue_receipt_sha256" to phoneHash(receipts.getJSONObject(1))), mapOf("reopen-worker-v2.json" to final))
        }
    }
}

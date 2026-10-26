/* Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0 */
package org.locallore.app

import android.os.Looper
import androidx.test.ext.junit.runners.AndroidJUnit4
import androidx.test.filters.SdkSuppress
import kotlinx.coroutines.CoroutineScope
import kotlinx.coroutines.Deferred
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.NonCancellable
import kotlinx.coroutines.SupervisorJob
import kotlinx.coroutines.async
import kotlinx.coroutines.cancel
import kotlinx.coroutines.delay
import kotlinx.coroutines.withContext
import kotlinx.coroutines.withTimeout
import org.json.JSONObject
import org.junit.Test
import org.junit.runner.RunWith

internal fun phoneWorkerHash(trace: LiteRtWorkerSnapshot) = phoneSha(trace.json().toByteArray(Charsets.US_ASCII))
internal fun phoneWorkerZero(trace: LiteRtWorkerSnapshot): Boolean = trace.counts.values.all { it == 0 } && trace.creationsTotal == 0 &&
    trace.lastMs.values.all { it == null } && trace.saturated.isEmpty() && !trace.timeSaturated && !trace.creationsSaturated
internal fun phoneUnsaturated(trace: LiteRtWorkerSnapshot) = check(trace.saturated.isEmpty() && !trace.timeSaturated && !trace.creationsSaturated)
internal fun phoneCount(trace: LiteRtWorkerSnapshot, value: Int, vararg events: LiteRtWorkerEvent) =
    check(events.all { trace.counts.getValue(it) == value })
internal fun phoneRoles(trace: LiteRtWorkerSnapshot, roles: List<LiteRtTraceRole>) {
    phoneUnsaturated(trace)
    check(trace.creationsTotal == roles.size && trace.creations.map { it.role } == roles)
    check(trace.creations.all { it.returnedMs != null && it.failedMs == null && it.failure == LiteRtTraceFailure.NONE })
}
internal fun phoneWorkerClosed(trace: LiteRtWorkerSnapshot) {
    phoneRoles(trace, listOf(LiteRtTraceRole.DIRECTOR, LiteRtTraceRole.NARRATOR))
    phoneCount(trace, 2, LiteRtWorkerEvent.CONVERSATION_CREATE_ENTERED, LiteRtWorkerEvent.CONVERSATION_CREATE_RETURNED,
        LiteRtWorkerEvent.SEND_ENTERED, LiteRtWorkerEvent.SEND_RETURNED, LiteRtWorkerEvent.DONE_ENTERED, LiteRtWorkerEvent.DONE_RETURNED,
        LiteRtWorkerEvent.DRAIN_SETTLED, LiteRtWorkerEvent.CONVERSATION_CLOSE_ENTERED, LiteRtWorkerEvent.CONVERSATION_CLOSE_KNOWN)
    phoneCount(trace, 0, LiteRtWorkerEvent.ERROR_ENTERED, LiteRtWorkerEvent.ERROR_RETURNED, LiteRtWorkerEvent.CANCEL_ENTERED,
        LiteRtWorkerEvent.CANCEL_RETURNED, LiteRtWorkerEvent.UNCERTAIN)
    phoneCount(trace, 1, LiteRtWorkerEvent.ENGINE_CLOSE_ENTERED, LiteRtWorkerEvent.ENGINE_CLOSE_KNOWN)
    check(trace.counts.getValue(LiteRtWorkerEvent.MESSAGE_RETURNED) > 0)
}
private fun inflight(trace: LiteRtWorkerSnapshot): Boolean {
    phoneUnsaturated(trace)
    phoneCount(trace, 0, LiteRtWorkerEvent.DONE_ENTERED, LiteRtWorkerEvent.ERROR_ENTERED,
        LiteRtWorkerEvent.CANCEL_ENTERED, LiteRtWorkerEvent.ENGINE_CLOSE_ENTERED, LiteRtWorkerEvent.UNCERTAIN)
    check(trace.creationsTotal <= 1)
    if (trace.counts.getValue(LiteRtWorkerEvent.SEND_RETURNED) != 1 || trace.counts.getValue(LiteRtWorkerEvent.MESSAGE_RETURNED) < 1) return false
    phoneRoles(trace, listOf(LiteRtTraceRole.DIRECTOR))
    phoneCount(trace, 1, LiteRtWorkerEvent.SEND_ENTERED, LiteRtWorkerEvent.SEND_RETURNED)
    return true
}
private fun closedCancellation(trace: LiteRtWorkerSnapshot, sampled: LiteRtWorkerSnapshot) {
    phoneRoles(trace, listOf(LiteRtTraceRole.DIRECTOR))
    phoneCount(trace, 1, LiteRtWorkerEvent.SEND_ENTERED, LiteRtWorkerEvent.SEND_RETURNED,
        LiteRtWorkerEvent.CANCEL_ENTERED, LiteRtWorkerEvent.CANCEL_RETURNED, LiteRtWorkerEvent.DRAIN_SETTLED,
        LiteRtWorkerEvent.CONVERSATION_CLOSE_ENTERED, LiteRtWorkerEvent.CONVERSATION_CLOSE_KNOWN,
        LiteRtWorkerEvent.ENGINE_CLOSE_ENTERED, LiteRtWorkerEvent.ENGINE_CLOSE_KNOWN)
    phoneCount(trace, 0, LiteRtWorkerEvent.UNCERTAIN)
    val done = trace.counts.getValue(LiteRtWorkerEvent.DONE_ENTERED)
    val error = trace.counts.getValue(LiteRtWorkerEvent.ERROR_ENTERED)
    check((done == 1 && error == 0 || done == 0 && error == 1) &&
        trace.counts.getValue(LiteRtWorkerEvent.DONE_RETURNED) == done && trace.counts.getValue(LiteRtWorkerEvent.ERROR_RETURNED) == error)
    check(trace.counts.keys == sampled.counts.keys && trace.counts.all { it.value >= sampled.counts.getValue(it.key) })
    check(trace.creations == sampled.creations)
}

/** Passive call-site accounting around the actual production transport; no scheduling/SDK substitute. */
private class PhoneCancellationObserved(private val actual: NativeWorkspaceTransport) : WorkspaceTransport {
    var submits = 0; var commits = 0; var cancelAcks = 0
    override suspend fun exchange(command: JSONObject): JSONObject {
        check(Looper.myLooper() == Looper.getMainLooper())
        when (command.getString("op")) {
            "free_text" -> {
                submits++
                val intent = command.getJSONObject("request").getJSONObject("intent")
                check(intent.getString("kind") == "free_text" && intent.getJSONObject("value").getString("kind") == "action" &&
                    intent.getJSONObject("value").getString("text") == PHONE_GIFT)
            }
            "commit" -> commits++
        }
        val reply = actual.exchange(command)
        if (command.getString("op") == "cancel") {
            check(reply.getString("status") == "ok" && reply.getJSONObject("data").getString("phase") == "cancelled")
            cancelAcks++
        }
        return reply
    }
    override fun close() { check(Looper.myLooper() == Looper.getMainLooper()); actual.close() }
}

@RunWith(AndroidJUnit4::class)
@SdkSuppress(minSdkVersion = 36)
class PhysicalModelCancellationTest : PhysicalModelHarness() {
    @Test fun cancelsAndJoinsWithoutCommit() {
        val deadline = selected(PhysicalModelCancellationTest::class.java, PhysicalModelPhase.CANCEL)
        io(deadline) {
            val checks = linkedMapOf<String, Boolean>()
            val env = PhoneEnvironment(context)
            val prior = env.prior(PhysicalModelPhase.CANCEL)
            checked(checks, "prior_import_exact", prior.first.phase == PhysicalModelPhase.IMPORT)
            checked(checks, "process_identity_changed", prior.first.identity != env.identity)
            val access = CandidateLocalModel.store(context)
            checked(checks, "accepted_recheck", access.installed() != null)
            access.admitRuntime(); checked(checks, "runtime_guard", true)
            check(!java.nio.file.Files.exists(java.io.File(env.storage.internal, "workspace-v1").toPath(), java.nio.file.LinkOption.NOFOLLOW_LINKS))
            val trace = LiteRtWorkerTrace()
            val actual = withContext(Dispatchers.Main.immediate) { CandidateLocalModel.createTransport(context, trace) }
            val observed = PhoneCancellationObserved(actual)
            val gateway = DurableGateway(observed)
            val scope = CoroutineScope(SupervisorJob() + Dispatchers.Main.immediate)
            var pending: Deferred<DemoResult>? = null
            try {
                val saved = withContext(Dispatchers.Main.immediate) { gateway.initialize() }
                checked(checks, "production_transport", saved.textProvider == TextProvider.LOCAL)
                val initial = view(actual, saved)
                checked(checks, "initial_canon_zero", initial.getLong("revision") == 0L && initial.getJSONArray("receipts").length() == 0 &&
                    initial.getJSONObject("inventory").getJSONObject("potion").getString("owner") == "player")
                val handle = actual.forkHandle()
                val preparing = scope.async { gateway.respondText(PlayInput(PlayInputKind.ACTION, PHONE_GIFT), 0) }.also { pending = it }
                var pulses = 0
                val sample = withContext(Dispatchers.Main.immediate) {
                    withTimeout(deadline.remaining(65_000)) {
                        var value = trace.snapshot()
                        while (true) {
                            check(preparing.isActive) { "Phone cancellation window missed" }
                            pulses++
                            if (inflight(value)) break
                            delay(5)
                            value = trace.snapshot()
                        }
                        check(preparing.isActive); value
                    }
                }
                checked(checks, "public_inference_sampled", true)
                checked(checks, "main_responsive", pulses > 0)
                withContext(Dispatchers.Main.immediate) { gateway.cancelSaved() }
                val result = withTimeout(deadline.remaining(70_000)) { preparing.await() }
                checked(checks, "cancel_ack_joined", observed.cancelAcks == 1 && preparing.isCompleted && result is DemoResult.Rejected && result.category == "Cancelled")
                checked(checks, "no_prepared", result !is DemoResult.Prepared)
                checked(checks, "no_commit", observed.commits == 0 && observed.submits == 1)
                closedCancellation(trace.snapshot(), sample)
                checked(checks, "terminal_drain", true); checked(checks, "known_sdk_close", true)
                check(actual.forkHandle() == handle)
                val after = view(actual, withContext(Dispatchers.Main.immediate) { gateway.snapshot() })
                checked(checks, "no_receipts", after.getLong("revision") == 0L && after.getJSONArray("receipts").length() == 0 && phoneHash(after) == phoneHash(initial))
                checked(checks, "model_intact", access.installed() != null)
                check(actual.forkHandle() == handle)
                withContext(Dispatchers.Main.immediate) { gateway.close() }
                checked(checks, "candidate_owner_retained", !CandidateLocalModel.canStart())
                checked(checks, "native_handle_closed", nativeClosed(handle, deadline))
                val memory = env.storage.snapshot()
                checked(checks, "memory_eligible", PhysicalModelPolicy.ongoing(memory) == memory)
                val final = trace.snapshot(); closedCancellation(final, sample)
                env.write(PhysicalModelPhase.CANCEL, deadline, PhoneCounts(), checks, prior, mapOf(
                    "revision" to 0L, "receipt_count" to 0L, "receipts_sha256" to phoneHash(after.getJSONArray("receipts")),
                    "story_sha256" to phoneHash(after.getJSONObject("scope")), "worker_trace_sha256" to phoneWorkerHash(final),
                    "sample_trace_sha256" to phoneWorkerHash(sample)),
                    mapOf("cancel-worker-v2.json" to final, "cancel-sample-worker-v2.json" to sample))
            } finally {
                withContext(NonCancellable + Dispatchers.Main.immediate) { gateway.close() }
                withContext(NonCancellable) {
                    try { withTimeout(deadline.remaining(5_000)) { pending?.await() } } catch (_: Throwable) { }
                    if (pending == null || pending?.isCompleted == true) scope.cancel()
                }
            }
        }
    }
}

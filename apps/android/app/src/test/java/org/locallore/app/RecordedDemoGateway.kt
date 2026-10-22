/* Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0 */
package org.locallore.app

import kotlinx.coroutines.delay
import org.json.JSONObject

/** An original Rust-generated sample, not a Kotlin implementation of domain rules. */
data class RecordedCase(
    val action: DemoAction,
    val fromRevision: Long,
    val requestJson: String,
    val proposalJson: String,
    val result: DemoResult,
    val rejectedProposalJson: String,
    val rejectedError: String,
)

/** Replaces only generation, with bounded deterministic raw proposal samples. */
fun interface SampleInferenceProvider {
    suspend fun propose(case: RecordedCase, mode: DemoMode): String
}

class LocalFakeInferenceProvider : SampleInferenceProvider {
    override suspend fun propose(case: RecordedCase, mode: DemoMode): String {
        delay(if (mode == DemoMode.DELAYED) 5_000L else 300L)
        return when (mode) {
            DemoMode.ACCEPTED, DemoMode.DELAYED -> case.proposalJson
            DemoMode.MALFORMED -> "{not-json"
            DemoMode.REJECTED -> case.rejectedProposalJson
            DemoMode.FAILED -> throw IllegalStateException("Synthetic provider failure")
        }
    }
}

/**
 * Matches a finite proposal to its recorded Rust validation result. It executes no rules,
 * infers no consequences, and rejects anything outside the four prevalidated samples.
 * Request/proposal/accepted receipt JSON stays available for the M03.03 native adapter.
 */
class RecordedDemoGateway(
    private val cases: List<RecordedCase>,
    private val provider: SampleInferenceProvider = LocalFakeInferenceProvider(),
) : DemoGateway {
    override suspend fun respond(action: DemoAction, revision: Long, mode: DemoMode): DemoResult {
        val case = cases.singleOrNull { it.action == action && it.fromRevision == revision }
            ?: return DemoResult.Rejected("UnsupportedFixture")
        val proposal = provider.propose(case, mode)
        if (proposal.toByteArray(Charsets.UTF_8).size > 16_384) return DemoResult.Rejected("TooLarge")
        return when (proposal) {
            case.proposalJson -> case.result
            case.rejectedProposalJson -> DemoResult.Rejected(case.rejectedError)
            else -> DemoResult.Rejected("Malformed")
        }
    }

    companion object {
        fun fromJson(text: String): RecordedDemoGateway {
            require(text.toByteArray(Charsets.UTF_8).size <= 65_536) { "Fixture too large" }
            val root = JSONObject(text)
            require(root.getInt("fixture_version") == 1 && root.getInt("contract_version") == 1)
            val scope = root.getJSONObject("scope")
            require(scope.getString("story") == "quay" && scope.getString("branch") == "main")
            require(root.getLong("initial_revision") == 0L && root.getString("initial_potion_owner") == "You")
            val rows = root.getJSONArray("cases")
            require(rows.length() == 4)
            val cases = (0 until rows.length()).map { index ->
                val row = rows.getJSONObject(index)
                val resolution = row.getJSONObject("resolution")
                val result = when (resolution.getString("kind")) {
                    "accepted" -> DemoResult.Accepted(
                        resolution.getLong("revision"), resolution.getString("potion_owner"),
                        resolution.getString("narration"),
                    )
                    "rejected" -> DemoResult.Rejected(resolution.getString("error"))
                    else -> error("Unknown fixture resolution")
                }
                RecordedCase(
                    DemoAction.valueOf(row.getString("action")), row.getLong("from_revision"),
                    row.getString("request_json"), row.getString("proposal_json"), result,
                    row.getString("rejected_proposal_json"), row.getString("rejected_error"),
                )
            }
            require(cases.map { it.action to it.fromRevision }.toSet().size == 4)
            return RecordedDemoGateway(cases)
        }
    }
}

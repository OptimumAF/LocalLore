/* Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0 */
package org.locallore.app

import java.util.Collections
import java.util.Locale

/** Descriptive author input only. Native code assigns IDs, rules and canonical records. */
internal data class OriginalCast(val name: String, val description: String)
internal data class OriginalInput(val premise: String = "", val playerName: String = "Player",
    val playerDescription: String = "", val cast: List<OriginalCast> = emptyList(),
    val profile: String = "narrative_v1", val presentation: StoryPresentation = StoryPresentation())
internal data class OriginalLocation(val name: String, val description: String)
internal data class OriginalCharacter(val name: String, val description: String, val location: Int, val knownBy: List<Int>)
internal data class OriginalRoute(val from: Int, val to: Int)
internal data class OriginalFact(val text: String, val knownBy: List<Int>, val discoverableAt: Int?)
internal data class OriginalBelief(val believer: Int, val text: String, val confidence: String)
internal data class OriginalPossession(val name: String, val description: String, val owner: Int, val returnTo: Int?)
internal data class OriginalProposal(val locations: List<OriginalLocation>, val playerLocation: Int,
    val characters: List<OriginalCharacter>, val routes: List<OriginalRoute>, val facts: List<OriginalFact>,
    val beliefs: List<OriginalBelief>, val possessions: List<OriginalPossession>)
internal data class OriginalCapabilities(val available: Boolean, val provider: String?)
internal data class OriginalJob(val job: String, val inputSha256: String, val provider: String)
internal data class OriginalGenerated(val job: String, val input: OriginalInput, val proposal: OriginalProposal, val provider: String)
internal data class OriginalReview(val job: String, val reviewSha256: String, val input: OriginalInput,
    val proposal: OriginalProposal, val title: String, val details: List<String>)
internal interface OriginalStoryGateway {
    suspend fun originalCapabilities(): OriginalCapabilities
    suspend fun beginOriginal(input: OriginalInput): OriginalJob
    suspend fun generateOriginal(job: String): OriginalGenerated
    suspend fun reviewOriginal(job: String, input: OriginalInput, proposal: OriginalProposal, title: String): OriginalReview
    suspend fun createOriginal(review: OriginalReview, creationId: String): SavedSnapshot
    suspend fun cancelOriginal(job: String): Boolean
}
internal fun <T> originalList(values: List<T>): List<T> = Collections.unmodifiableList(ArrayList(values))
internal fun OriginalInput.frozen() = copy(cast = originalList(cast.map { it.copy() }),
    presentation = presentation.copy(excludedPhrases = originalList(presentation.excludedPhrases)))
internal fun OriginalProposal.frozen() = copy(locations = originalList(locations.map { it.copy() }),
    characters = originalList(characters.map { it.copy(knownBy = originalList(it.knownBy)) }),
    routes = originalList(routes.map { it.copy() }), facts = originalList(facts.map { it.copy(knownBy = originalList(it.knownBy)) }),
    beliefs = originalList(beliefs.map { it.copy() }), possessions = originalList(possessions.map { it.copy() }))
internal fun OriginalReview.frozen() = copy(input = input.frozen(), proposal = proposal.frozen(), details = originalList(details))
internal fun originalText(value: String, bytes: Int, scalars: Int, empty: Boolean=false): Boolean = try {
    (empty || value.isNotEmpty()) && value.trim()==value && localUtf8(value).size<=bytes &&
        value.codePointCount(0,value.length)<=scalars && value.codePoints().noneMatch {
            Character.isISOControl(it) || it in 0x2028..0x202e || it in 0x2066..0x2069 }
} catch (_: Exception) { false }
/** Presentation prechecks; encoded aggregate bounds and all domain invariants remain native gates. */
internal fun validOriginalInput(v: OriginalInput): Boolean = originalText(v.premise,2048,1024) &&
    validStoryPlayerName(v.playerName) && originalText(v.playerDescription,512,512,true) &&
    v.profile in setOf("fantasy_v1","narrative_v1") && validStoryPresentation(v.presentation) && v.cast.size<=3 &&
    v.cast.all { validStoryPlayerName(it.name) && originalText(it.description,512,512,true) } &&
    (listOf(v.playerName)+v.cast.map { it.name }).map { it.lowercase(Locale.ROOT) }.toSet().size==v.cast.size+1
internal fun validOriginalDraft(v: OriginalInput,p: OriginalProposal): Boolean = validOriginalInput(v) &&
    p.locations.size in 1..4 && p.characters.size in 1..3 && p.playerLocation in p.locations.indices &&
    p.routes.size<=8 && p.facts.size<=8 && p.beliefs.size<=6 && p.possessions.size<=4 &&
    p.locations.all { validStoryPlayerName(it.name) && originalText(it.description,512,512) } &&
    p.characters.all { validStoryPlayerName(it.name) && originalText(it.description,512,512) && it.location in p.locations.indices } &&
    p.facts.all { originalText(it.text,512,512) } && p.beliefs.all { originalText(it.text,512,512) } &&
    p.possessions.all { validStoryPlayerName(it.name) && originalText(it.description,512,512) }

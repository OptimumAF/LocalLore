/* Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0 */
package org.locallore.app

/** Explicit UI targets, never inferred from equality with a captured draft. No native IDs or Seed. */
internal enum class OriginalTextField {
    PREMISE, PLAYER_NAME, PLAYER_DESCRIPTION, TITLE, EXCLUDED_PHRASES,
    CAST_NAME, CAST_DESCRIPTION, LOCATION_NAME, LOCATION_DESCRIPTION, CHARACTER_NAME, CHARACTER_DESCRIPTION,
    FACT_TEXT, BELIEF_TEXT, POSSESSION_NAME, POSSESSION_DESCRIPTION,
}
internal enum class OriginalSelection {
    PROFILE, TONE, PLAYER_LOCATION, CHARACTER_LOCATION, FACT_DISCOVERABLE, BELIEF_BELIEVER,
    BELIEF_CONFIDENCE, POSSESSION_OWNER, POSSESSION_RETURN,
}
internal enum class OriginalRows { CAST, FACT, BELIEF, POSSESSION }
internal enum class OriginalKnown { CHARACTER, FACT }
internal sealed interface OriginalStoryEdit {
    data class Text(val field: OriginalTextField,val value: String,val row: Int=0): OriginalStoryEdit
    data class Select(val field: OriginalSelection,val value: Int,val row: Int=0): OriginalStoryEdit
    data class ToggleKnown(val kind: OriginalKnown,val row: Int,val actor: Int): OriginalStoryEdit
    data class ToggleRoute(val from: Int,val to: Int): OriginalStoryEdit
    data class Add(val kind: OriginalRows): OriginalStoryEdit
    data class Remove(val kind: OriginalRows,val row: Int): OriginalStoryEdit
    data class Move(val kind: OriginalRows,val from: Int,val to: Int): OriginalStoryEdit
}
internal fun OriginalStoryEdit.structural() = this is OriginalStoryEdit.Add || this is OriginalStoryEdit.Remove || this is OriginalStoryEdit.Move
internal class OriginalEditRefused: IllegalStateException()
private fun index(value: Int,size: Int): Int = value.also { if(it !in 0 until size)throw OriginalEditRefused() }
private fun <T> List<T>.row(i: Int,change: (T)->T): List<T> {
    index(i,size); return mapIndexed { n,v -> if(n==i)change(v) else v }
}
private fun <T> List<T>.without(i: Int): List<T> { index(i,size); return filterIndexed { n,_ -> n!=i } }
private fun <T> List<T>.moved(from: Int,to: Int): List<T> {
    index(from,size); index(to,size); return toMutableList().also { it.add(to,it.removeAt(from)) }
}
private fun <T> List<T>.toggle(value: T)=if(value in this)this-value else this+value
private fun OriginalStoryUiState.world(change: (OriginalProposal)->OriginalProposal): OriginalStoryUiState =
    copy(proposal=change(proposal ?: throw OriginalEditRefused()))
private fun OriginalStoryUiState.cast(change: (List<OriginalCast>)->List<OriginalCast>): OriginalStoryUiState {
    if(proposal!=null)throw OriginalEditRefused()
    return copy(input=input.copy(cast=change(input.cast)))
}

/** Apply one named intent to the latest draft, including an explicit return to its rendered value. */
internal fun applyOriginalEdit(s: OriginalStoryUiState,e: OriginalStoryEdit): OriginalStoryUiState = when(e) {
    is OriginalStoryEdit.Text -> when(e.field) {
        OriginalTextField.PREMISE -> s.copy(input=s.input.copy(premise=e.value))
        OriginalTextField.PLAYER_NAME -> s.copy(input=s.input.copy(playerName=e.value))
        OriginalTextField.PLAYER_DESCRIPTION -> s.copy(input=s.input.copy(playerDescription=e.value))
        OriginalTextField.TITLE -> s.copy(title=e.value)
        OriginalTextField.EXCLUDED_PHRASES -> s.copy(input=s.input.copy(presentation=s.input.presentation.copy(
            excludedPhrases=if(e.value.isEmpty())emptyList() else e.value.split('\n'))))
        OriginalTextField.CAST_NAME -> s.cast { it.row(e.row) { c -> c.copy(name=e.value) } }
        OriginalTextField.CAST_DESCRIPTION -> s.cast { it.row(e.row) { c -> c.copy(description=e.value) } }
        OriginalTextField.LOCATION_NAME -> s.world { it.copy(locations=it.locations.row(e.row) { c -> c.copy(name=e.value) }) }
        OriginalTextField.LOCATION_DESCRIPTION -> s.world { it.copy(locations=it.locations.row(e.row) { c -> c.copy(description=e.value) }) }
        OriginalTextField.CHARACTER_NAME -> s.world { it.copy(characters=it.characters.row(e.row) { c -> c.copy(name=e.value) }) }
        OriginalTextField.CHARACTER_DESCRIPTION -> s.world { it.copy(characters=it.characters.row(e.row) { c -> c.copy(description=e.value) }) }
        OriginalTextField.FACT_TEXT -> s.world { it.copy(facts=it.facts.row(e.row) { c -> c.copy(text=e.value) }) }
        OriginalTextField.BELIEF_TEXT -> s.world { it.copy(beliefs=it.beliefs.row(e.row) { c -> c.copy(text=e.value) }) }
        OriginalTextField.POSSESSION_NAME -> s.world { it.copy(possessions=it.possessions.row(e.row) { c -> c.copy(name=e.value) }) }
        OriginalTextField.POSSESSION_DESCRIPTION -> s.world { it.copy(possessions=it.possessions.row(e.row) { c -> c.copy(description=e.value) }) }
    }
    is OriginalStoryEdit.Select -> when(e.field) {
        OriginalSelection.PROFILE -> s.copy(input=s.input.copy(profile=listOf("fantasy_v1","narrative_v1")[index(e.value,2)]))
        OriginalSelection.TONE -> s.copy(input=s.input.copy(presentation=s.input.presentation.copy(tone=listOf("plain","warm","brisk")[index(e.value,3)])))
        OriginalSelection.PLAYER_LOCATION -> s.world { it.copy(playerLocation=index(e.value,it.locations.size)) }
        OriginalSelection.CHARACTER_LOCATION -> s.world { p -> p.copy(characters=p.characters.row(e.row) { it.copy(location=index(e.value,p.locations.size)) }) }
        OriginalSelection.FACT_DISCOVERABLE -> s.world { p -> index(e.value,p.locations.size+1); p.copy(facts=p.facts.row(e.row) { it.copy(discoverableAt=if(e.value==0)null else e.value-1) }) }
        OriginalSelection.BELIEF_BELIEVER -> s.world { p -> p.copy(beliefs=p.beliefs.row(e.row) { it.copy(believer=index(e.value,p.characters.size+1)) }) }
        OriginalSelection.BELIEF_CONFIDENCE -> s.world { p -> p.copy(beliefs=p.beliefs.row(e.row) { it.copy(confidence=listOf("uncertain","suspected","believed")[index(e.value,3)]) }) }
        OriginalSelection.POSSESSION_OWNER -> s.world { p -> p.copy(possessions=p.possessions.row(e.row) { it.copy(owner=index(e.value,p.characters.size+1)) }) }
        OriginalSelection.POSSESSION_RETURN -> s.world { p -> index(e.value,p.characters.size+2); p.copy(possessions=p.possessions.row(e.row) { it.copy(returnTo=if(e.value==0)null else e.value-1) }) }
    }
    is OriginalStoryEdit.ToggleKnown -> s.world { p ->
        index(e.actor,p.characters.size+1)
        when(e.kind) {
            OriginalKnown.CHARACTER -> p.copy(characters=p.characters.row(e.row) { it.copy(knownBy=it.knownBy.toggle(e.actor)) })
            OriginalKnown.FACT -> p.copy(facts=p.facts.row(e.row) { it.copy(knownBy=it.knownBy.toggle(e.actor)) })
        }
    }
    is OriginalStoryEdit.ToggleRoute -> s.world { p ->
        index(e.from,p.locations.size); index(e.to,p.locations.size); if(e.from==e.to)throw OriginalEditRefused()
        val route=OriginalRoute(e.from,e.to)
        if(route !in p.routes && p.routes.size>=8)throw OriginalEditRefused()
        p.copy(routes=p.routes.toggle(route))
    }
    is OriginalStoryEdit.Add -> when(e.kind) {
        OriginalRows.CAST -> s.cast { if(it.size>=3)throw OriginalEditRefused(); it+OriginalCast("","") }
        OriginalRows.FACT -> s.world { if(it.facts.size>=8)throw OriginalEditRefused(); it.copy(facts=it.facts+OriginalFact("",emptyList(),null)) }
        OriginalRows.BELIEF -> s.world { if(it.beliefs.size>=6)throw OriginalEditRefused(); it.copy(beliefs=it.beliefs+OriginalBelief(0,"","uncertain")) }
        OriginalRows.POSSESSION -> s.world { if(it.possessions.size>=4)throw OriginalEditRefused(); it.copy(possessions=it.possessions+OriginalPossession("","",0,null)) }
    }
    is OriginalStoryEdit.Remove -> when(e.kind) {
        OriginalRows.CAST -> s.cast { it.without(e.row) }
        OriginalRows.FACT -> s.world { it.copy(facts=it.facts.without(e.row)) }
        OriginalRows.BELIEF -> s.world { it.copy(beliefs=it.beliefs.without(e.row)) }
        OriginalRows.POSSESSION -> s.world { it.copy(possessions=it.possessions.without(e.row)) }
    }
    is OriginalStoryEdit.Move -> when(e.kind) {
        OriginalRows.CAST -> s.cast { it.moved(e.from,e.to) }
        OriginalRows.FACT -> s.world { it.copy(facts=it.facts.moved(e.from,e.to)) }
        OriginalRows.BELIEF -> s.world { it.copy(beliefs=it.beliefs.moved(e.from,e.to)) }
        OriginalRows.POSSESSION -> s.world { it.copy(possessions=it.possessions.moved(e.from,e.to)) }
    }
}

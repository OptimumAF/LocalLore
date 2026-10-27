/* Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0 */
package org.locallore.app

/** Typed UI intent merge only. It never assigns native IDs or validates canonical state. */
private fun <T> field(old: T,next: T,current: T): T = if(next==old)current else next
private fun <T> movedRows(old: List<T>,next: List<T>): Boolean {
    if(old.size!=next.size)return true
    if(old==next)return false
    return old.indices.any { i -> old.count { it==old[i] }==1 && next.count { it==old[i] }==1 && next.indexOf(old[i])!=i }
}
internal fun originalStructureChanged(old: OriginalInput,next: OriginalInput,oldWorld: OriginalProposal?,nextWorld: OriginalProposal?): Boolean =
    movedRows(old.cast,next.cast) || (oldWorld!=null && nextWorld!=null && (
        movedRows(oldWorld.locations,nextWorld.locations) || movedRows(oldWorld.characters,nextWorld.characters) ||
        movedRows(oldWorld.facts,nextWorld.facts) || movedRows(oldWorld.beliefs,nextWorld.beliefs) || movedRows(oldWorld.possessions,nextWorld.possessions)))

internal class OriginalEditConflict: IllegalStateException()
private fun <T> rows(old: List<T>,next: List<T>,current: List<T>,merge: (T,T,T)->T): List<T> {
    if(old.size!=current.size)throw OriginalEditConflict() // Never guess indices for a foreign or stale frame.
    if(!movedRows(old,next))return next.indices.map { merge(old[it],next[it],current[it]) }
    // A stale removal among identical rows cannot identify a concurrently edited occurrence.
    // Refuse that ambiguous intent instead of dropping the edit or guessing a row identity.
    if(old.indices.any { current[it]!=old[it] && old.count { row -> row==old[it] }>1 })throw OriginalEditConflict()
    val available=old.indices.toMutableSet()
    return next.map { value ->
        val index=available.firstOrNull { old[it]==value }
        if(index==null)value else { available.remove(index); current[index] }
    }
}
private fun <T> choices(old: List<T>,next: List<T>,current: List<T>): List<T> {
    val removed=old.filter { it !in next }.toSet()
    return current.filter { it !in removed } + next.filter { it !in old && it !in current }
}
internal fun mergeOriginalInput(old: OriginalInput,next: OriginalInput,current: OriginalInput,mergeCast: Boolean=true): OriginalInput = current.copy(
    premise=field(old.premise,next.premise,current.premise),playerName=field(old.playerName,next.playerName,current.playerName),
    playerDescription=field(old.playerDescription,next.playerDescription,current.playerDescription),profile=field(old.profile,next.profile,current.profile),
    presentation=current.presentation.copy(tone=field(old.presentation.tone,next.presentation.tone,current.presentation.tone),
        excludedPhrases=field(old.presentation.excludedPhrases,next.presentation.excludedPhrases,current.presentation.excludedPhrases)),
    cast=if(!mergeCast)current.cast else rows(old.cast,next.cast,current.cast) { a,b,c -> c.copy(name=field(a.name,b.name,c.name),description=field(a.description,b.description,c.description)) })

internal fun mergeOriginalWorld(old: OriginalProposal,next: OriginalProposal,current: OriginalProposal): OriginalProposal = current.copy(
    playerLocation=field(old.playerLocation,next.playerLocation,current.playerLocation),
    locations=rows(old.locations,next.locations,current.locations) { a,b,c -> c.copy(name=field(a.name,b.name,c.name),description=field(a.description,b.description,c.description)) },
    characters=rows(old.characters,next.characters,current.characters) { a,b,c -> c.copy(name=field(a.name,b.name,c.name),
        description=field(a.description,b.description,c.description),location=field(a.location,b.location,c.location),knownBy=choices(a.knownBy,b.knownBy,c.knownBy)) },
    routes=choices(old.routes,next.routes,current.routes),
    facts=rows(old.facts,next.facts,current.facts) { a,b,c -> c.copy(text=field(a.text,b.text,c.text),knownBy=choices(a.knownBy,b.knownBy,c.knownBy),
        discoverableAt=field(a.discoverableAt,b.discoverableAt,c.discoverableAt)) },
    beliefs=rows(old.beliefs,next.beliefs,current.beliefs) { a,b,c -> c.copy(believer=field(a.believer,b.believer,c.believer),
        text=field(a.text,b.text,c.text),confidence=field(a.confidence,b.confidence,c.confidence)) },
    possessions=rows(old.possessions,next.possessions,current.possessions) { a,b,c -> c.copy(name=field(a.name,b.name,c.name),
        description=field(a.description,b.description,c.description),owner=field(a.owner,b.owner,c.owner),returnTo=field(a.returnTo,b.returnTo,c.returnTo)) })
internal fun mergeOriginalTitle(old: String,next: String,current: String)=field(old,next,current)

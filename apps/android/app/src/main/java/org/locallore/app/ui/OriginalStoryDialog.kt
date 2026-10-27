/* Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0 */
package org.locallore.app.ui

import androidx.compose.foundation.layout.*
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.verticalScroll
import androidx.compose.material3.*
import androidx.compose.runtime.Composable
import androidx.compose.runtime.key
import androidx.compose.ui.Modifier
import androidx.compose.ui.platform.testTag
import androidx.compose.ui.semantics.*
import androidx.compose.ui.unit.dp
import androidx.compose.ui.window.Dialog
import androidx.compose.ui.window.DialogProperties
import org.locallore.app.*

/** Structured descriptive author forms. This editor never constructs a Seed or native IDs. */
@Composable
internal fun OriginalStoryDialog(state: OriginalStoryUiState, onDismiss: () -> Unit,
    onEdit: (OriginalStoryUiState,OriginalInput,OriginalProposal?,String) -> Unit,
    onGenerate: (OriginalStoryUiState) -> Unit, onReview: (OriginalStoryUiState) -> Unit,
    onCreate: (OriginalStoryUiState,OriginalReview) -> Unit, exposeTestTags: Boolean) {
    val editable=!state.busy && !state.closing && !state.creating
    val input=state.input; val world=state.proposal
    fun editInput(next: OriginalInput)=onEdit(state,next,world,state.title)
    fun editWorld(next: OriginalProposal)=onEdit(state,input,next,state.title)
    Dialog(onDismissRequest=onDismiss,properties=DialogProperties(usePlatformDefaultWidth=false)) {
        Surface(Modifier.fillMaxWidth(0.94f).widthIn(max=560.dp).fillMaxHeight(0.9f)
            .testTag("original-story-dialog").semantics { testTagsAsResourceId=exposeTestTags },shape=MaterialTheme.shapes.large) {
            Column(Modifier.padding(16.dp),verticalArrangement=Arrangement.spacedBy(12.dp)) {
                Column(Modifier.weight(1f).verticalScroll(rememberScrollState()),verticalArrangement=Arrangement.spacedBy(12.dp)) {
                    Text("Write an original story",style=MaterialTheme.typography.titleLarge,modifier=Modifier.semantics { heading() })
                    Text(if(state.provider=="local") "Generation uses the selected local model. Review and edit its proposal before creating."
                        else "This build uses a synthetic scripted provider. It demonstrates the flow; it is not model generation.")
                    Text("Nothing is saved before Create. Author review includes private beliefs and world truth; these are not automatically player knowledge.")
                    if(state.busy) CircularProgressIndicator()
                    state.notice?.let { Text(it,Modifier.testTag("original-story-notice").semantics { liveRegion=LiveRegionMode.Polite }) }
                    OriginalField("Premise",input.premise,"original-premise",editable) { editInput(input.copy(premise=it)) }
                    OriginalField("Player name",input.playerName,"original-player-name",editable) { editInput(input.copy(playerName=it)) }
                    OriginalField("Player description (optional)",input.playerDescription,"original-player-description",editable) { editInput(input.copy(playerDescription=it)) }
                    Text("Use a short premise and concise descriptions, with one paragraph per field and no line breaks or outer spaces.")
                    OriginalChoice("Rules",listOf("Fantasy","Narrative"),if(input.profile=="fantasy_v1")0 else 1,editable) {
                        editInput(input.copy(profile=if(it==0)"fantasy_v1" else "narrative_v1")) }
                    OriginalChoice("Generated narration tone",listOf("Plain","Warm","Brisk"),listOf("plain","warm","brisk").indexOf(input.presentation.tone),editable) {
                        editInput(input.copy(presentation=input.presentation.copy(tone=listOf("plain","warm","brisk")[it]))) }
                    OriginalField("Phrases excluded from generated narration (one per line)",input.presentation.excludedPhrases.joinToString("\n"),"original-excluded-phrases",editable) {
                        editInput(input.copy(presentation=input.presentation.copy(excludedPhrases=if(it.isEmpty())emptyList() else it.split('\n')))) }
                    Text("Matches literal phrases, ignoring letter case, with up to eight phrases. This does not filter broad topics or player messages.")
                    if(world==null) {
                        Text("Starting cast hints (optional, up to three)",modifier=Modifier.semantics { heading() })
                        input.cast.forEachIndexed { index,c ->
                            OriginalField("Character ${index+1} name",c.name,"original-cast-$index-name",editable) { editInput(input.copy(cast=input.cast.replace(index,c.copy(name=it)))) }
                            OriginalField("Character ${index+1} description",c.description,"original-cast-$index-description",editable) { editInput(input.copy(cast=input.cast.replace(index,c.copy(description=it)))) }
                            OriginalAction("Remove character ${index+1}",editable) { editInput(input.copy(cast=input.cast.filterIndexed { i,_ -> i!=index })) }
                        }
                        if(input.cast.size<3) OriginalAction("Add cast hint",editable) { editInput(input.copy(cast=input.cast+OriginalCast("",""))) }
                    }
                    OriginalAction(if(world==null)"Generate draft" else "Regenerate from these inputs",editable && OriginalStoryWire.valid(input),"original-generate") { onGenerate(state) }
                    if(world!=null) {
                        Text("Edit the starting world",style=MaterialTheme.typography.titleMedium,modifier=Modifier.semantics { heading() })
                        val locations=world.locations.mapIndexed { i,l -> "${i+1}. ${l.name}" }
                        val actors=listOf(input.playerName)+world.characters.map { it.name }
                        world.locations.forEachIndexed { i,l ->
                            OriginalField("Location ${i+1} name",l.name,"original-location-$i-name",editable) { editWorld(world.copy(locations=world.locations.replace(i,l.copy(name=it)))) }
                            OriginalField("Location ${i+1} description",l.description,"original-location-$i-description",editable) { editWorld(world.copy(locations=world.locations.replace(i,l.copy(description=it)))) }
                        }
                        OriginalChoice("Player starts at",locations,world.playerLocation,editable) { editWorld(world.copy(playerLocation=it)) }
                        world.characters.forEachIndexed { i,c ->
                            OriginalField("Character ${i+1} name",c.name,"original-character-$i-name",editable) { editWorld(world.copy(characters=world.characters.replace(i,c.copy(name=it)))) }
                            OriginalField("Character ${i+1} description",c.description,"original-character-$i-description",editable) { editWorld(world.copy(characters=world.characters.replace(i,c.copy(description=it)))) }
                            OriginalChoice("${c.name} starts at",locations,c.location,editable) { editWorld(world.copy(characters=world.characters.replace(i,c.copy(location=it)))) }
                            OriginalKnown("Who knows ${c.name}'s description?",actors,c.knownBy,editable) { editWorld(world.copy(characters=world.characters.replace(i,c.copy(knownBy=it)))) }
                        }
                        Text("Travel routes (directed)",modifier=Modifier.semantics { heading() })
                        world.locations.indices.forEach { from -> world.locations.indices.filter { it!=from }.forEach { to ->
                            val route=OriginalRoute(from,to); val selected=route in world.routes
                            OriginalAction("${if(selected)"✓ " else ""}${world.locations[from].name} → ${world.locations[to].name}",editable && (selected || world.routes.size<8)) {
                                editWorld(world.copy(routes=if(selected)world.routes-route else world.routes+route)) }
                        } }
                        Text("World truth",modifier=Modifier.semantics { heading() })
                        world.facts.forEachIndexed { i,f ->
                            OriginalField("Fact ${i+1}",f.text,"original-fact-$i",editable) { editWorld(world.copy(facts=world.facts.replace(i,f.copy(text=it)))) }
                            OriginalKnown("Who knows fact ${i+1}?",actors,f.knownBy,editable) { editWorld(world.copy(facts=world.facts.replace(i,f.copy(knownBy=it)))) }
                            OriginalChoice("Discoverable at",listOf("Not location-discoverable")+locations,(f.discoverableAt?.plus(1) ?: 0),editable) {
                                editWorld(world.copy(facts=world.facts.replace(i,f.copy(discoverableAt=if(it==0)null else it-1)))) }
                            OriginalAction("Remove fact ${i+1}",editable) { editWorld(world.copy(facts=world.facts.filterIndexed { n,_ -> n!=i })) }
                        }
                        if(world.facts.size<8) OriginalAction("Add world fact",editable) { editWorld(world.copy(facts=world.facts+OriginalFact("",emptyList(),null))) }
                        Text("Private beliefs — may differ from truth",modifier=Modifier.semantics { heading() })
                        world.beliefs.forEachIndexed { i,b ->
                            OriginalChoice("Believer ${i+1}",actors,b.believer,editable) { editWorld(world.copy(beliefs=world.beliefs.replace(i,b.copy(believer=it)))) }
                            OriginalField("Belief ${i+1}",b.text,"original-belief-$i",editable) { editWorld(world.copy(beliefs=world.beliefs.replace(i,b.copy(text=it)))) }
                            OriginalChoice("Confidence",listOf("Uncertain","Suspected","Believed"),listOf("uncertain","suspected","believed").indexOf(b.confidence),editable) {
                                editWorld(world.copy(beliefs=world.beliefs.replace(i,b.copy(confidence=listOf("uncertain","suspected","believed")[it])))) }
                            OriginalAction("Remove belief ${i+1}",editable) { editWorld(world.copy(beliefs=world.beliefs.filterIndexed { n,_ -> n!=i })) }
                        }
                        if(world.beliefs.size<6) OriginalAction("Add private belief",editable) { editWorld(world.copy(beliefs=world.beliefs+OriginalBelief(0,"","uncertain"))) }
                        Text("Starting possessions (one each)",modifier=Modifier.semantics { heading() })
                        world.possessions.forEachIndexed { i,p ->
                            OriginalField("Possession ${i+1} name",p.name,"original-possession-$i-name",editable) { editWorld(world.copy(possessions=world.possessions.replace(i,p.copy(name=it)))) }
                            OriginalField("Possession ${i+1} description",p.description,"original-possession-$i-description",editable) { editWorld(world.copy(possessions=world.possessions.replace(i,p.copy(description=it)))) }
                            OriginalChoice("Owner",actors,p.owner,editable) { editWorld(world.copy(possessions=world.possessions.replace(i,p.copy(owner=it)))) }
                            OriginalChoice("Return obligation",listOf("None")+actors,p.returnTo?.plus(1) ?: 0,editable) { editWorld(world.copy(possessions=world.possessions.replace(i,p.copy(returnTo=if(it==0)null else it-1)))) }
                            OriginalAction("Remove possession ${i+1}",editable) { editWorld(world.copy(possessions=world.possessions.filterIndexed { n,_ -> n!=i })) }
                        }
                        if(world.possessions.size<4) OriginalAction("Add possession",editable) { editWorld(world.copy(possessions=world.possessions+OriginalPossession("","",0,null))) }
                    }
                    OriginalField("Save title",state.title,"original-title",editable) { onEdit(state,input,world,it) }
                    if(world!=null) OriginalAction("Review changes",editable && validStoryTitle(state.title) && OriginalStoryWire.valid(input,world),"original-review") { onReview(state) }
                    if(!OriginalStoryWire.valid(input,world)) Text("Complete the fields before generating or reviewing. Keep names and descriptions short; check the locations and who knows each fact.",color=MaterialTheme.colorScheme.error)
                    state.review?.let { review ->
                        Text("Reviewed starting world",modifier=Modifier.semantics { heading() })
                        review.details.forEach { Text(it) }
                        key(OriginalConsent(review)) { OriginalAction("Create",editable,"original-create") { onCreate(state,review) } }
                    }
                }
                OriginalAction(if(state.closing)"Finishing…" else "Cancel",!state.closing,"original-cancel",onDismiss)
            }
        }
    }
}
@Composable private fun OriginalField(label: String,value: String,tag: String,enabled: Boolean,onValue: (String)->Unit) {
    OutlinedTextField(value=value,onValueChange=onValue,label={Text(label)},enabled=enabled,modifier=Modifier.fillMaxWidth().testTag(tag))
}
@Composable private fun OriginalAction(label: String,enabled: Boolean,tag: String="",action: ()->Unit) {
    OutlinedButton(onClick=action,enabled=enabled,modifier=Modifier.fillMaxWidth().heightIn(min=48.dp).then(if(tag.isEmpty())Modifier else Modifier.testTag(tag))) { Text(label) }
}
@Composable private fun OriginalChoice(label: String,values: List<String>,selected: Int,enabled: Boolean,onValue: (Int)->Unit) {
    Text(label)
    values.forEachIndexed { i,value -> OriginalAction("${if(i==selected)"✓ " else ""}$value",enabled) { onValue(i) } }
}
@Composable private fun OriginalKnown(label: String,actors: List<String>,selected: List<Int>,enabled: Boolean,onValue: (List<Int>)->Unit) {
    Text(label)
    actors.forEachIndexed { i,name -> OriginalAction("${if(i in selected)"✓ " else ""}$name",enabled) { onValue(if(i in selected)selected-i else selected+i) } }
}
private fun <T> List<T>.replace(index: Int,value: T)=mapIndexed { i,old -> if(i==index)value else old }
private class OriginalConsent(private val value: Any) {
    override fun equals(other: Any?)=other is OriginalConsent && other.value===value
    override fun hashCode()=System.identityHashCode(value)
}

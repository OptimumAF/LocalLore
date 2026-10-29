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
    onEdit: (OriginalStoryUiState,OriginalStoryEdit) -> Unit,
    onGenerate: (OriginalStoryUiState) -> Unit, onReview: (OriginalStoryUiState) -> Unit,
    onCreate: (OriginalStoryUiState,OriginalReview) -> Unit, exposeTestTags: Boolean) {
    val editable=!state.busy && !state.closing && !state.creating
    val input=state.input; val world=state.proposal
    fun text(field: OriginalTextField,value: String,row: Int=0)=onEdit(state,OriginalStoryEdit.Text(field,value,row))
    fun select(field: OriginalSelection,value: Int,row: Int=0)=onEdit(state,OriginalStoryEdit.Select(field,value,row))
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
                    OriginalField("Premise",input.premise,"original-premise",editable) { text(OriginalTextField.PREMISE,it) }
                    OriginalField("Player name",input.playerName,"original-player-name",editable) { text(OriginalTextField.PLAYER_NAME,it) }
                    OriginalField("Player description (optional)",input.playerDescription,"original-player-description",editable) { text(OriginalTextField.PLAYER_DESCRIPTION,it) }
                    Text("Use a short premise and concise descriptions, with one paragraph per field and no line breaks or outer spaces.")
                    OriginalChoice("Rules",listOf("Fantasy","Narrative"),if(input.profile=="fantasy_v1")0 else 1,editable) {
                        select(OriginalSelection.PROFILE,it) }
                    OriginalChoice("Generated narration tone",listOf("Plain","Warm","Brisk"),listOf("plain","warm","brisk").indexOf(input.presentation.tone),editable) {
                        select(OriginalSelection.TONE,it) }
                    OriginalField("Phrases excluded from generated narration (one per line)",input.presentation.excludedPhrases.joinToString("\n"),"original-excluded-phrases",editable) {
                        text(OriginalTextField.EXCLUDED_PHRASES,it) }
                    Text("Matches literal phrases, ignoring letter case, with up to eight phrases. This does not filter broad topics or player messages.")
                    if(world==null) {
                        Text("Starting cast hints (optional, up to three)",modifier=Modifier.semantics { heading() })
                        input.cast.forEachIndexed { index,c ->
                            OriginalField("Character ${index+1} name",c.name,"original-cast-$index-name",editable) { text(OriginalTextField.CAST_NAME,it,index) }
                            OriginalField("Character ${index+1} description",c.description,"original-cast-$index-description",editable) { text(OriginalTextField.CAST_DESCRIPTION,it,index) }
                            OriginalAction("Remove character ${index+1}",editable) { onEdit(state,OriginalStoryEdit.Remove(OriginalRows.CAST,index)) }
                        }
                        if(input.cast.size<3) OriginalAction("Add cast hint",editable) { onEdit(state,OriginalStoryEdit.Add(OriginalRows.CAST)) }
                    }
                    OriginalAction(if(world==null)"Generate draft" else "Regenerate from these inputs",editable && OriginalStoryWire.valid(input),"original-generate") { onGenerate(state) }
                    if(world!=null) {
                        Text("Edit the starting world",style=MaterialTheme.typography.titleMedium,modifier=Modifier.semantics { heading() })
                        val locations=world.locations.mapIndexed { i,l -> "${i+1}. ${l.name}" }
                        val actors=listOf(input.playerName)+world.characters.map { it.name }
                        world.locations.forEachIndexed { i,l ->
                            OriginalField("Location ${i+1} name",l.name,"original-location-$i-name",editable) { text(OriginalTextField.LOCATION_NAME,it,i) }
                            OriginalField("Location ${i+1} description",l.description,"original-location-$i-description",editable) { text(OriginalTextField.LOCATION_DESCRIPTION,it,i) }
                        }
                        OriginalChoice("Player starts at",locations,world.playerLocation,editable) { select(OriginalSelection.PLAYER_LOCATION,it) }
                        world.characters.forEachIndexed { i,c ->
                            OriginalField("Character ${i+1} name",c.name,"original-character-$i-name",editable) { text(OriginalTextField.CHARACTER_NAME,it,i) }
                            OriginalField("Character ${i+1} description",c.description,"original-character-$i-description",editable) { text(OriginalTextField.CHARACTER_DESCRIPTION,it,i) }
                            OriginalChoice("${c.name} starts at",locations,c.location,editable) { select(OriginalSelection.CHARACTER_LOCATION,it,i) }
                            OriginalKnownChoices("Who knows ${c.name}'s description?",actors,c.knownBy,editable) { onEdit(state,OriginalStoryEdit.ToggleKnown(OriginalKnown.CHARACTER,i,it)) }
                        }
                        Text("Travel routes (directed)",modifier=Modifier.semantics { heading() })
                        world.locations.indices.forEach { from -> world.locations.indices.filter { it!=from }.forEach { to ->
                            val route=OriginalRoute(from,to); val selected=route in world.routes
                            OriginalAction("${if(selected)"✓ " else ""}${world.locations[from].name} → ${world.locations[to].name}",editable && (selected || world.routes.size<8)) {
                                onEdit(state,OriginalStoryEdit.ToggleRoute(from,to)) }
                        } }
                        Text("World truth",modifier=Modifier.semantics { heading() })
                        world.facts.forEachIndexed { i,f ->
                            OriginalField("Fact ${i+1}",f.text,"original-fact-$i",editable) { text(OriginalTextField.FACT_TEXT,it,i) }
                            OriginalKnownChoices("Who knows fact ${i+1}?",actors,f.knownBy,editable) { onEdit(state,OriginalStoryEdit.ToggleKnown(OriginalKnown.FACT,i,it)) }
                            OriginalChoice("Discoverable at",listOf("Not location-discoverable")+locations,(f.discoverableAt?.plus(1) ?: 0),editable) {
                                select(OriginalSelection.FACT_DISCOVERABLE,it,i) }
                            OriginalAction("Remove fact ${i+1}",editable) { onEdit(state,OriginalStoryEdit.Remove(OriginalRows.FACT,i)) }
                        }
                        if(world.facts.size<8) OriginalAction("Add world fact",editable) { onEdit(state,OriginalStoryEdit.Add(OriginalRows.FACT)) }
                        Text("Private beliefs — may differ from truth",modifier=Modifier.semantics { heading() })
                        world.beliefs.forEachIndexed { i,b ->
                            OriginalChoice("Believer ${i+1}",actors,b.believer,editable) { select(OriginalSelection.BELIEF_BELIEVER,it,i) }
                            OriginalField("Belief ${i+1}",b.text,"original-belief-$i",editable) { text(OriginalTextField.BELIEF_TEXT,it,i) }
                            OriginalChoice("Confidence",listOf("Uncertain","Suspected","Believed"),listOf("uncertain","suspected","believed").indexOf(b.confidence),editable) {
                                select(OriginalSelection.BELIEF_CONFIDENCE,it,i) }
                            OriginalAction("Remove belief ${i+1}",editable) { onEdit(state,OriginalStoryEdit.Remove(OriginalRows.BELIEF,i)) }
                        }
                        if(world.beliefs.size<6) OriginalAction("Add private belief",editable) { onEdit(state,OriginalStoryEdit.Add(OriginalRows.BELIEF)) }
                        Text("Starting possessions (one each)",modifier=Modifier.semantics { heading() })
                        world.possessions.forEachIndexed { i,p ->
                            OriginalField("Possession ${i+1} name",p.name,"original-possession-$i-name",editable) { text(OriginalTextField.POSSESSION_NAME,it,i) }
                            OriginalField("Possession ${i+1} description",p.description,"original-possession-$i-description",editable) { text(OriginalTextField.POSSESSION_DESCRIPTION,it,i) }
                            OriginalChoice("Owner",actors,p.owner,editable) { select(OriginalSelection.POSSESSION_OWNER,it,i) }
                            OriginalChoice("Return obligation",listOf("None")+actors,p.returnTo?.plus(1) ?: 0,editable) { select(OriginalSelection.POSSESSION_RETURN,it,i) }
                            OriginalAction("Remove possession ${i+1}",editable) { onEdit(state,OriginalStoryEdit.Remove(OriginalRows.POSSESSION,i)) }
                        }
                        if(world.possessions.size<4) OriginalAction("Add possession",editable) { onEdit(state,OriginalStoryEdit.Add(OriginalRows.POSSESSION)) }
                    }
                    OriginalField("Save title",state.title,"original-title",editable) { text(OriginalTextField.TITLE,it) }
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
@Composable private fun OriginalKnownChoices(label: String,actors: List<String>,selected: List<Int>,enabled: Boolean,onToggle: (Int)->Unit) {
    Text(label)
    actors.forEachIndexed { i,name -> OriginalAction("${if(i in selected)"✓ " else ""}$name",enabled) { onToggle(i) } }
}
private class OriginalConsent(private val value: Any) {
    override fun equals(other: Any?)=other is OriginalConsent && other.value===value
    override fun hashCode()=System.identityHashCode(value)
}

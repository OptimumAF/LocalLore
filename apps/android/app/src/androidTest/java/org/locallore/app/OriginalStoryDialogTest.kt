/* Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0 */
package org.locallore.app

import androidx.compose.material3.MaterialTheme
import androidx.compose.runtime.mutableStateOf
import androidx.compose.ui.semantics.SemanticsActions
import androidx.compose.ui.test.*
import androidx.compose.ui.test.junit4.createComposeRule
import kotlinx.coroutines.CoroutineScope
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.SupervisorJob
import kotlinx.coroutines.cancel
import org.junit.Assert.*
import org.junit.Rule
import org.junit.Test
import org.locallore.app.ui.OriginalStoryDialog

/** Real Compose/consent controller with a labelled fake gateway, not JNI/model evidence. */
class OriginalStoryDialogTest {
    @get:Rule val compose=createComposeRule()
    private class Port: OriginalStoryGateway {
        var generates=0; val creates=mutableListOf<OriginalReview>(); lateinit var input: OriginalInput
        val world=OriginalProposal(listOf(OriginalLocation("Orchard","A frozen orchard.")),0,
            listOf(OriginalCharacter("Sel","An orchard keeper.",0,listOf(0,1))),emptyList(),emptyList(),emptyList(),emptyList())
        override suspend fun originalCapabilities()=OriginalCapabilities(true,"scripted")
        override suspend fun beginOriginal(input: OriginalInput): OriginalJob { this.input=input; return OriginalJob("job-1","a".repeat(64),"scripted") }
        override suspend fun generateOriginal(job: String): OriginalGenerated { generates++; return OriginalGenerated(job,input,world,"scripted") }
        override suspend fun reviewOriginal(job: String,input: OriginalInput,proposal: OriginalProposal,title: String)=
            OriginalReview(job,"b".repeat(64),input,proposal,title,listOf("World truth is reviewed separately from private beliefs."))
        override suspend fun cancelOriginal(job: String)=true
        override suspend fun createOriginal(review: OriginalReview,creationId: String): SavedSnapshot { creates+=review
            return SavedSnapshot(0,"You",emptyList(),"synthetic",1,emptyList(),SavedStory("original-$creationId","main",review.title,0)) }
    }
    private fun form(port: Port,action: (OriginalStoryController,()->OriginalStoryUiState)->Unit) {
        val scope=CoroutineScope(SupervisorJob()+Dispatchers.Main.immediate)
        val state=mutableStateOf<OriginalStoryUiState?>(null)
        val controller=OriginalStoryController(port,scope,{state.value=it}){}
        controller.open(OriginalCapabilities(true,"scripted"))
        compose.setContent { MaterialTheme { state.value?.let { OriginalStoryDialog(it,controller::dismiss,
            controller::edit,controller::generate,controller::review,controller::confirm,true) } } }
        try { action(controller,{checkNotNull(state.value)}) } finally { compose.runOnIdle { controller.dispose(); scope.cancel() } }
    }
    @Test fun scriptedProviderIsLabelledAndGenerateDoesNotCreate() {
        val port=Port()
        form(port) { _,state ->
            compose.onNodeWithText("synthetic scripted provider",substring=true).performScrollTo().assertIsDisplayed()
            compose.onNodeWithTag("original-generate").performScrollTo().assertIsNotEnabled()
            compose.onNodeWithTag("original-premise").performScrollTo().performTextReplacement("A clockmaker enters a frozen orchard.")
            compose.onNodeWithTag("original-generate").performScrollTo().assertIsEnabled().performClick()
            compose.waitUntil(5000) { !state().busy && state().proposal!=null }
            compose.onNodeWithTag("original-character-0-name").performScrollTo().assert(hasText("Sel"))
            compose.onNodeWithTag("original-create").assertDoesNotExist()
            compose.runOnIdle { assertEquals(1,port.generates); assertTrue(port.creates.isEmpty()); assertNull(state().review) }
        }
    }
    @Test fun editsInvalidateReviewAndStaleCreateCannotBorrowNewConsent() {
        val port=Port()
        form(port) { controller,state ->
            compose.onNodeWithTag("original-premise").performScrollTo().performTextReplacement("A clockmaker enters a frozen orchard.")
            compose.onNodeWithTag("original-generate").performScrollTo().performClick()
            compose.waitUntil(5000) { !state().busy && state().proposal!=null }
            compose.onNodeWithTag("original-review").performScrollTo().assertIsEnabled().performClick()
            compose.waitUntil(5000) { state().review!=null && !state().busy }
            val first=state().review!!
            val oldCreate=checkNotNull(compose.onNodeWithTag("original-create").performScrollTo().fetchSemanticsNode().config[SemanticsActions.OnClick].action)
            compose.onNodeWithTag("original-title").performScrollTo().performTextReplacement("The reviewed orchard")
            compose.onNodeWithTag("original-create").assertDoesNotExist()
            compose.runOnIdle { oldCreate(); assertTrue(port.creates.isEmpty()); assertNull(state().review) }
            compose.onNodeWithTag("original-review").performScrollTo().performClick()
            compose.waitUntil(5000) { state().review!=null && !state().busy }
            compose.runOnIdle { oldCreate(); controller.confirm(state().copy(),state().review!!); assertTrue(port.creates.isEmpty()); assertNotSame(first,state().review) }
            compose.onNodeWithTag("original-create").performScrollTo().performClick()
            compose.waitUntil(5000) { port.creates.size==1 }
            compose.runOnIdle { assertEquals("The reviewed orchard",port.creates.single().title) }
        }
    }
}

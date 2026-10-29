/* Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0 */
package org.locallore.app

import org.junit.Assert.*
import org.junit.Test

/** Binding metadata only. Native scope/revision and fixed player-lens integration are tested separately. */
class OriginalPlayerBindingTest {
    private val scope=PlayDraftScope("original-synthetic","main")
    private fun refused(category: String,body: ()->Unit) {
        try { body(); fail("Invalid native player binding accepted") }
        catch(e: WorkspaceFailure) { assertEquals(category,e.category) }
    }
    @Test fun opaqueAndLegacyNativePlayersBindWithoutDerivingOrChoosingAnId() {
        for(observer in listOf("player","a-0123456789abcdef0123-0","a".repeat(64))) {
            val first=bindPlayerSnapshot("session-1",scope,observer,null)
            assertEquals(observer,first.observer); assertEquals(scope,first.scope); assertEquals("session-1",first.session)
            assertEquals(first,bindPlayerSnapshot("session-1",scope,observer,first))
        }
    }
    @Test fun sameLeaseCannotRetargetObserverScopeOrSession() {
        val first=bindPlayerSnapshot("session-1",scope,"a-0123456789abcdef0123-0",null)
        refused("Stale") { bindPlayerSnapshot("session-1",scope,"a-0123456789abcdef0123-1",first) }
        refused("Stale") { bindPlayerSnapshot("session-2",scope,first.observer,first) }
        refused("Stale") { bindPlayerSnapshot("session-1",scope.copy(branch="child"),first.observer,first) }
        refused("Stale") { bindPlayerSnapshot("session-1",scope.copy(story="another-story"),first.observer,first) }
        // Only explicit native attachment clears the gateway's old binding.
        assertEquals("another-player",bindPlayerSnapshot("session-2",scope.copy(story="another-story"),"another-player",null).observer)
    }
    @Test fun nativeObserverMustBeAnExactBoundedDomainId() {
        for(raw in listOf(null,1,1L,1.0,true,""," outer","x\ny","x/y","a".repeat(65),"\uD800","é")) {
            refused("Malformed") { bindPlayerSnapshot("session-1",scope,raw,null) }
        }
    }
}

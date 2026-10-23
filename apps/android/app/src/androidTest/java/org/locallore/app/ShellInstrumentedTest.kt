package org.locallore.app

import android.content.pm.PackageManager
import androidx.compose.ui.test.*
import androidx.compose.ui.test.junit4.createAndroidComposeRule
import androidx.lifecycle.ViewModelProvider
import androidx.test.ext.junit.runners.AndroidJUnit4
import org.junit.Assert.*
import org.junit.Before
import org.junit.Rule
import org.junit.Test
import org.junit.runner.RunWith

@RunWith(AndroidJUnit4::class)
class ShellInstrumentedTest {
    @get:Rule val compose = createAndroidComposeRule<MainActivity>()

    private fun tag(name: String): SemanticsNodeInteraction {
        compose.onNodeWithTag("story-list").performScrollToNode(hasTestTag(name))
        return compose.onNodeWithTag(name)
    }

    private fun idle() {
        compose.waitUntil(8_000) {
            !ViewModelProvider(compose.activity)[ShellViewModel::class.java].state.value.busy
        }
        compose.waitForIdle()
    }
    @Before fun freshSavedStory() {
        idle(); tag("reset-demo").performClick(); idle()
    }
    private fun choose(mode: DemoMode) {
        tag("mode-menu").performClick()
        compose.onNodeWithTag("mode-${mode.name}").performClick()
    }
    private fun give() { tag("give-potion").performClick() }
    private fun assertInitial() {
        tag("potion-owner").assertTextEquals("Healing potion · You")
        tag("revision").assertTextEquals("Accepted revision · 0")
    }

    @Suppress("DEPRECATION")
    @Test fun launchShowsHonestFixtureLabelAndNoPlatformCapabilities() {
        compose.onNodeWithText("Local Rust engine", substring = true).assertIsDisplayed()
        assertInitial()
        @Suppress("DEPRECATION")
        val info = compose.activity.packageManager.getPackageInfo(compose.activity.packageName, PackageManager.GET_PERMISSIONS)
        assertEquals(listOf("org.locallore.app.DYNAMIC_RECEIVER_NOT_EXPORTED_PERMISSION"), info.requestedPermissions?.toList().orEmpty())
        @Suppress("DEPRECATION")
        val permission = compose.activity.packageManager.getPermissionInfo(info.requestedPermissions!!.single(), 0)
        assertEquals(android.content.pm.PermissionInfo.PROTECTION_SIGNATURE, permission.protectionLevel)
    }

    @Test fun giftUsesRustAcceptedResultAndReuseCannotDuplicateIt() {
        give(); idle()
        tag("potion-owner").assertTextEquals("Healing potion · Mira")
        tag("revision").assertTextEquals("Accepted revision · 1")
        compose.onNodeWithTag("story-list").performScrollToNode(hasText("You give 1 potion to mira."))
        compose.onNodeWithText("You give 1 potion to mira.").assertIsDisplayed()
        give(); idle()
        tag("notice").assertTextContains("no longer hold", substring = true)
        tag("revision").assertTextEquals("Accepted revision · 1")
        assertEquals(2, ViewModelProvider(compose.activity)[ShellViewModel::class.java].state.value.messages.size)
    }

    @Test fun unlearnedAbilityAndBadProviderModesLeaveStateUnchanged() {
        tag("try-ability").performClick(); idle()
        tag("notice").assertTextContains("not learned", substring = true)
        assertInitial()
        for ((mode, text) in listOf(DemoMode.MALFORMED to "malformed", DemoMode.REJECTED to "did not match", DemoMode.FAILED to "failed")) {
            choose(mode); give(); idle()
            tag("notice").assertTextContains(text, substring = true)
            assertInitial()
        }
        choose(DemoMode.ACCEPTED); give(); idle()
        tag("potion-owner").assertTextEquals("Healing potion · Mira")
    }

    @Test fun cancelAndResetDuringDelayCannotPublishOldResult() {
        choose(DemoMode.DELAYED); give()
        tag("cancel-turn").performClick(); idle()
        tag("notice").assertTextContains("accepted saved history", substring = true)
        assertInitial()
        tag("reset-demo").performClick(); idle()
        assertInitial()
        give(); idle()
        tag("potion-owner").assertTextEquals("Healing potion · Mira")
    }

    @Test fun recreationRetainsAcceptedStateAndCancelsPendingWork() {
        give(); idle()
        compose.activityRule.scenario.recreate(); idle()
        tag("potion-owner").assertTextEquals("Healing potion · Mira")
        tag("reset-demo").performClick(); idle()
        choose(DemoMode.DELAYED); give()
        compose.activityRule.scenario.recreate(); idle()
        assertInitial()
        tag("notice").assertTextContains("accepted saved history", substring = true)
    }

    @Test fun activityDisposalRetainsDurableSavedStoryAndTranscript() {
        give(); idle()
        val before = ViewModelProvider(compose.activity)[ShellViewModel::class.java].state.value
        val path = java.io.File(checkNotNull(before.storageLocation))
        assertTrue(path.isFile)
        compose.activityRule.scenario.close()
        assertTrue("Disposal must retain the workspace database", path.isFile)
    }
}

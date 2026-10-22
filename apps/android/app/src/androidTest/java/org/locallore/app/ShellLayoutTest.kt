package org.locallore.app

import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.requiredSize
import androidx.compose.runtime.CompositionLocalProvider
import androidx.compose.ui.Modifier
import androidx.compose.ui.platform.LocalDensity
import androidx.compose.ui.test.*
import androidx.compose.ui.test.junit4.createComposeRule
import androidx.compose.ui.unit.Density
import androidx.compose.ui.unit.dp
import org.junit.Assert.assertTrue
import org.junit.Rule
import org.junit.Test
import org.locallore.app.ui.LocalLoreScreen

class ShellLayoutTest {
    @get:Rule val compose = createComposeRule()

    @Test fun smallViewportAndDoubleFontScaleKeepControlsReachable() {
        var given = false
        var reset = false
        compose.setContent {
            val density = LocalDensity.current.density
            CompositionLocalProvider(LocalDensity provides Density(density, 2f)) {
                Box(Modifier.requiredSize(320.dp, 340.dp)) {
                    LocalLoreScreen(ShellState(), { given = true }, {}, {}, { reset = true })
                }
            }
        }
        compose.onNodeWithTag("story-list").performScrollToNode(hasTestTag("give-potion"))
        compose.onNodeWithTag("give-potion").assertIsDisplayed().performClick()
        compose.onNodeWithTag("story-list").performScrollToNode(hasTestTag("reset-demo"))
        compose.onNodeWithTag("reset-demo").assertIsDisplayed().performClick()
        assertTrue(given)
        assertTrue(reset)
    }
}

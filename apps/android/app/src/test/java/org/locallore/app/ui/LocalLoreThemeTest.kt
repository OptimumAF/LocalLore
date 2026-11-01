/* Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0 */
package org.locallore.app.ui

import androidx.compose.material3.ColorScheme
import androidx.compose.ui.graphics.Color
import kotlin.math.pow
import org.junit.Assert.*
import org.junit.Test

/** Numerical palette regressions, not visual, TalkBack, or whole-screen accessibility proof. */
class LocalLoreThemeTest {
    // Independent sRGB calculation from WCAG 2.2 SC 1.4.3/1.4.11:
    // https://www.w3.org/WAI/WCAG22/Understanding/contrast-minimum.html
    // https://www.w3.org/WAI/WCAG22/Understanding/non-text-contrast.html
    private fun luminance(color: Color): Double {
        fun linear(value: Float): Double {
            val channel = value.toDouble()
            return if (channel <= 0.04045) channel / 12.92 else ((channel + 0.055) / 1.055).pow(2.4)
        }
        return 0.2126 * linear(color.red) + 0.7152 * linear(color.green) + 0.0722 * linear(color.blue)
    }

    private fun contrast(foreground: Color, background: Color): Double {
        val a = luminance(foreground); val b = luminance(background)
        return (maxOf(a, b) + 0.05) / (minOf(a, b) + 0.05)
    }

    private fun requireContrast(name: String, foreground: Color, background: Color, minimum: Double) {
        assertEquals("$name foreground opacity", 1f, foreground.alpha, 0f)
        assertEquals("$name background opacity", 1f, background.alpha, 0f)
        val actual = contrast(foreground, background)
        assertTrue("$name contrast $actual must be at least $minimum without rounding", actual >= minimum)
    }

    private fun textPairs(s: ColorScheme) = listOf(
        Triple("onPrimary/primary", s.onPrimary, s.primary),
        Triple("onPrimaryContainer/primaryContainer", s.onPrimaryContainer, s.primaryContainer),
        Triple("onSecondary/secondary", s.onSecondary, s.secondary),
        Triple("onSecondaryContainer/secondaryContainer", s.onSecondaryContainer, s.secondaryContainer),
        Triple("onTertiary/tertiary", s.onTertiary, s.tertiary),
        Triple("onTertiaryContainer/tertiaryContainer", s.onTertiaryContainer, s.tertiaryContainer),
        Triple("onBackground/background", s.onBackground, s.background),
        Triple("onSurface/surface", s.onSurface, s.surface),
        Triple("onSurfaceVariant/surface", s.onSurfaceVariant, s.surface),
        Triple("onSurfaceVariant/surfaceVariant", s.onSurfaceVariant, s.surfaceVariant),
        Triple("primary text/surface", s.primary, s.surface),
        Triple("onError/error", s.onError, s.error),
        Triple("onErrorContainer/errorContainer", s.onErrorContainer, s.errorContainer),
        Triple("error text/surface", s.error, s.surface),
        Triple("inverseOnSurface/inverseSurface", s.inverseOnSurface, s.inverseSurface),
        Triple("inversePrimary/inverseSurface", s.inversePrimary, s.inverseSurface),
    )

    @Test fun existingEightLightBrandAndContentRolesRemainExact() {
        val s = localLoreColorScheme(false)
        assertEquals(Color(0xFF18584E), s.primary)
        assertEquals(Color.White, s.onPrimary)
        assertEquals(Color(0xFFF8F5EC), s.surface)
        assertEquals(Color(0xFFF8F5EC), s.background)
        assertEquals(Color(0xFF202D2A), s.onSurface)
        assertEquals(Color(0xFF202D2A), s.onBackground)
        assertEquals(Color(0xFF4D5C56), s.onSurfaceVariant)
        assertEquals(Color(0xFF4D5C56), s.outline)
    }

    @Test fun lightNormalTextAndSemanticForegroundPairsMeetFourPointFive() {
        val s = localLoreColorScheme(false)
        assertTrue("The retained paper canvas stays light", luminance(s.surface) > 0.8)
        textPairs(s).forEach { (name, foreground, background) -> requireContrast(name, foreground, background, 4.5) }
    }

    @Test fun darkNormalTextAndSemanticForegroundPairsMeetFourPointFiveOnADarkCanvas() {
        val s = localLoreColorScheme(true)
        assertTrue("Night canvas must actually be dark", luminance(s.surface) < 0.05)
        assertTrue("Night body text must remain light", luminance(s.onSurface) > 0.5)
        textPairs(s).forEach { (name, foreground, background) -> requireContrast(name, foreground, background, 4.5) }
    }

    @Test fun bodyTextRemainsReadableAcrossAllMaterialSurfaceElevations() {
        for ((dark, s) in listOf(false to localLoreColorScheme(false), true to localLoreColorScheme(true))) {
            listOf("surfaceDim" to s.surfaceDim, "surfaceBright" to s.surfaceBright,
                "surfaceContainerLowest" to s.surfaceContainerLowest, "surfaceContainerLow" to s.surfaceContainerLow,
                "surfaceContainer" to s.surfaceContainer, "surfaceContainerHigh" to s.surfaceContainerHigh,
                "surfaceContainerHighest" to s.surfaceContainerHighest).forEach { (name, background) ->
                requireContrast("dark=$dark onSurface/$name", s.onSurface, background, 4.5)
            }
        }
    }

    @Test fun EssentialControlOutlinesAndFocusedIndicatorsMeetThreeAgainstTheirSurfaces() {
        for ((dark, s) in listOf(false to localLoreColorScheme(false), true to localLoreColorScheme(true))) {
            listOf("surface" to s.surface, "background" to s.background, "surfaceVariant" to s.surfaceVariant,
                "surfaceContainerHighest" to s.surfaceContainerHighest, "surfaceBright" to s.surfaceBright).forEach { (name, background) ->
                requireContrast("dark=$dark outline/$name", s.outline, background, 3.0)
            }
            requireContrast("dark=$dark focused primary/surface", s.primary, s.surface, 3.0)
        }
    }
}

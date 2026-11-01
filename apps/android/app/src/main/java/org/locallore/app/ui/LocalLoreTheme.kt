/* Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0 */
package org.locallore.app.ui

import androidx.compose.foundation.isSystemInDarkTheme
import androidx.compose.material3.ColorScheme
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.darkColorScheme
import androidx.compose.material3.lightColorScheme
import androidx.compose.runtime.Composable
import androidx.compose.ui.graphics.Color

internal fun localLoreColorScheme(darkTheme: Boolean): ColorScheme = if (darkTheme) {
    darkColorScheme(
        primary = Color(0xFF8FD5C3),
        onPrimary = Color(0xFF00382E),
        primaryContainer = Color(0xFF005044),
        onPrimaryContainer = Color(0xFFAEF2DF),
        inversePrimary = Color(0xFF18584E),
        secondary = Color(0xFFB5CCC2),
        onSecondary = Color(0xFF20362E),
        secondaryContainer = Color(0xFF364D44),
        onSecondaryContainer = Color(0xFFD1E8DD),
        tertiary = Color(0xFFB5CCC2),
        onTertiary = Color(0xFF20362E),
        tertiaryContainer = Color(0xFF364D44),
        onTertiaryContainer = Color(0xFFD1E8DD),
        background = Color(0xFF101916),
        onBackground = Color(0xFFE1EBDF),
        surface = Color(0xFF101916),
        onSurface = Color(0xFFE1EBDF),
        surfaceVariant = Color(0xFF34433D),
        onSurfaceVariant = Color(0xFFBECBBF),
        surfaceTint = Color(0xFF8FD5C3),
        inverseSurface = Color(0xFFE1EBDF),
        inverseOnSurface = Color(0xFF26342D),
        error = Color(0xFFFFB4AB),
        onError = Color(0xFF690005),
        errorContainer = Color(0xFF93000A),
        onErrorContainer = Color(0xFFFFDAD6),
        outline = Color(0xFF89978E),
        outlineVariant = Color(0xFF34433D),
        scrim = Color.Black,
        surfaceDim = Color(0xFF101916),
        surfaceBright = Color(0xFF364039),
        surfaceContainerLowest = Color(0xFF0B1410),
        surfaceContainerLow = Color(0xFF18211D),
        surfaceContainer = Color(0xFF1C2521),
        surfaceContainerHigh = Color(0xFF26302B),
        surfaceContainerHighest = Color(0xFF313B35),
    )
} else {
    lightColorScheme(
        primary = Color(0xFF18584E),
        onPrimary = Color.White,
        surface = Color(0xFFF8F5EC),
        background = Color(0xFFF8F5EC),
        onSurface = Color(0xFF202D2A),
        onBackground = Color(0xFF202D2A),
        onSurfaceVariant = Color(0xFF4D5C56),
        outline = Color(0xFF4D5C56),
    )
}

@Composable
internal fun LocalLoreTheme(
    darkTheme: Boolean = isSystemInDarkTheme(),
    content: @Composable () -> Unit,
) {
    MaterialTheme(colorScheme = localLoreColorScheme(darkTheme), content = content)
}

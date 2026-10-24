/* Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0 */
package org.locallore.app

import java.io.InputStream

/** Immutable construction seam. Normal setup supplies only the fixed built-in candidate. */
internal data class LocalModelSetupDependencies(
    val identity: LocalModelIdentity,
    val checkInstalled: suspend () -> Boolean,
    val install: suspend (() -> InputStream) -> Unit,
    val canStart: () -> Boolean,
    val openPlay: () -> Unit,
)

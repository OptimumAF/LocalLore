/* Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0 */
package org.locallore.app

/** Receipt-only construction seam; MainActivity retains its real ViewModel, UI and callbacks. */
class ReceiptComposeCancellationActivity : MainActivity() {
    internal val workerTrace = LiteRtWorkerTrace()
    internal lateinit var actualTransport: NativeWorkspaceTransport
        private set

    internal override fun createWorkspaceTransport(): NativeWorkspaceTransport =
        CandidateLocalModel.createTransport(applicationContext, workerTrace).also { actualTransport = it }
}

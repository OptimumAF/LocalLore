/* Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0 */
package org.locallore.app

import java.io.InputStream

/** The transaction is the sole receipt parser and runtime acceptance authority. */
internal class ReceiptCandidateModelAccess(private val transaction: ReceiptModelTransaction) : CandidateModelAccess {
    override fun plannedFiles(): LocalModelFiles = transaction.plannedFiles()
    override suspend fun installed(): LocalModelFiles? = transaction.installed()
    override suspend fun import(open: () -> InputStream): LocalModelFiles = transaction.import(open)
    override fun admitRuntime() = transaction.admitRuntime()
}

/* Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0 */
package org.locallore.app

import java.io.InputStream

/** Trusted debug-candidate access. Paths/identity never come from model output or an Intent. */
internal interface CandidateModelAccess {
    /** Planning only: construction, this call and transport construction perform no file IO. */
    fun plannedFiles(): LocalModelFiles
    suspend fun installed(): LocalModelFiles?
    suspend fun import(open: () -> InputStream): LocalModelFiles
    /** Synchronous, bounded admission on the existing worker's IO path, before SDK boundaries. */
    fun admitRuntime()
}

/** Preserve the existing publication protocol for every profile without receipt opt-in. */
internal class PublicationCandidateModelAccess(private val store: LocalModelStore) : CandidateModelAccess {
    override fun plannedFiles(): LocalModelFiles = store.plannedFiles()
    override suspend fun installed(): LocalModelFiles? = store.installed()
    override suspend fun import(open: () -> InputStream): LocalModelFiles = store.import(open)
    override fun admitRuntime() = store.admitRuntime()
}

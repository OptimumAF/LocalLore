/* Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0 */
package org.locallore.app

import java.util.Collections

/** Display values only. Rank, cost, eligibility and consequences remain native rules. */
data class PlayerAbility(val id: String, val rank: Int)
data class PlayerAttribute(val name: String, val value: Int)

/** A detached copy of the native player's self state at the enclosing accepted snapshot. */
data class PlayerSelfProfile(
    val observer: String,
    val name: String,
    val location: String,
    val alive: Boolean,
    val energy: Int,
    val abilities: List<PlayerAbility>,
    val attributes: List<PlayerAttribute>,
    val injuries: List<String>,
    val affiliations: List<String>,
    val goals: List<String>,
)

/** Also detach typed snapshots supplied by an in-process gateway before publication. */
internal fun PlayerSelfProfile.detachedCopy(): PlayerSelfProfile = copy(
    abilities = immutableProfileList(abilities),
    attributes = immutableProfileList(attributes),
    injuries = immutableProfileList(injuries),
    affiliations = immutableProfileList(affiliations),
    goals = immutableProfileList(goals),
)

private fun <T> immutableProfileList(values: List<T>): List<T> =
    Collections.unmodifiableList(ArrayList(values))

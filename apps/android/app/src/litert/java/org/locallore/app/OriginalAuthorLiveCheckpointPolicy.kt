/* Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0 */
package org.locallore.app

import java.nio.ByteBuffer
import java.nio.charset.CodingErrorAction

/** Fixed experiment bookkeeping, not native/process or inference authority. */
internal object OriginalAuthorLiveCheckpointPolicy {
    const val HOLD_NS = 120_000_000_000L
    const val STAT_CAP = 4096
    data class Window(val readyNs: Long, val expiresNs: Long)

    fun admitWindow(nowNs: Long, overallDeadlineNs: Long): Window {
        require(nowNs > 0 && overallDeadlineNs > nowNs)
        val expires = Math.addExact(nowNs, HOLD_NS)
        require(expires <= overallDeadlineNs)
        return Window(nowNs, expires)
    }

    /** A forced refusal is visible before close; otherwise the whole advertised lease is owed. */
    fun mayClose(window: Window, nowNs: Long, terminalForced: Boolean): Boolean {
        require(window.readyNs > 0 && Math.subtractExact(window.expiresNs, window.readyNs) == HOLD_NS)
        return terminalForced || nowNs >= window.expiresNs
    }

    fun startTicks(raw: ByteArray, expectedPid: Int): Long {
        require(expectedPid > 0 && raw.size in 1..STAT_CAP && raw.none { it == 0.toByte() })
        val text = Charsets.UTF_8.newDecoder().onMalformedInput(CodingErrorAction.REPORT)
            .onUnmappableCharacter(CodingErrorAction.REPORT).decode(ByteBuffer.wrap(raw)).toString()
        require(text.startsWith("$expectedPid ("))
        // comm can itself contain spaces and right parentheses; field3 follows the LAST ')'.
        val end = text.lastIndexOf(')')
        require(end >= "$expectedPid (".length && end + 2 < text.length && text[end + 1] == ' ')
        val fields = text.substring(end + 2).trimEnd('\n').split(Regex(" +"))
        require(fields.size >= 20 && fields[0].length == 1 && fields[0][0] in "RSDZTWtXxKPI")
        for (index in 1..18) require(Regex("-?[0-9]{1,20}").matches(fields[index]))
        val ticks = fields[19]
        require(Regex("[1-9][0-9]{0,18}").matches(ticks))
        return requireNotNull(ticks.toLongOrNull()).also { require(it > 0) }
    }
}

/* Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0 */
package org.locallore.app

import kotlinx.coroutines.CancellationException
import kotlinx.coroutines.CoroutineScope
import kotlinx.coroutines.Job
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.launch

/** Owner-thread UI adapter. Reads cannot prepare, commit, or cancel gameplay. */
internal class StoryRecordController(private val reader: StoryRecordReader, private val scope: CoroutineScope) {
    private val mutable = MutableStateFlow(StoryRecordState())
    val state = mutable.asStateFlow()
    private var generation = 0L
    private var pending: Job? = null
    private var disposed = false
    private var pageBoundary: Pair<StoryRecordQuery, Pair<Int, Long>>? = null

    fun open(context: StoryRecordContext) {
        if (!disposed) load(StoryRecordQuery(context))
    }
    fun select(section: StoryRecordSection) {
        val context = mutable.value.context ?: return
        if (!disposed) load(StoryRecordQuery(context, section, mutable.value.search))
    }
    fun search(text: String) {
        val current = mutable.value
        val context = current.context ?: return
        if (!disposed && !current.loading) load(StoryRecordQuery(context, current.section, text))
    }
    fun next() {
        val current = mutable.value
        val context = current.context ?: return
        if (!disposed && !current.loading && current.nextCursor != null)
            load(StoryRecordQuery(context, current.section, current.search, current.nextCursor))
    }
    fun first() {
        val current = mutable.value
        val context = current.context ?: return
        if (!disposed && !current.loading) load(StoryRecordQuery(context, current.section, current.search))
    }
    fun retry() {
        val current = mutable.value
        val context = current.context ?: return
        if (!disposed && !current.loading) load(StoryRecordQuery(context, current.section, current.search, current.cursor))
    }
    private fun load(query: StoryRecordQuery) {
        val identity = query.copy(cursor = null)
        if (query.cursor == null || pageBoundary?.first != identity) pageBoundary = null
        val boundary = pageBoundary?.second
        val ticket = ++generation
        pending?.cancel()
        mutable.value = StoryRecordState(visible = true, loading = true, context = query.context,
            section = query.section, search = query.search, cursor = query.cursor)
        if (!validStoryRecordSearch(query.search)) {
            mutable.value = mutable.value.copy(loading = false, problem = StoryRecordProblem.BAD_SEARCH)
            return
        }
        pending = scope.launch {
            try {
                val page = reader.readStoryRecord(query)
                if (disposed || ticket != generation) return@launch
                check(page.query == query && page.storyTime >= 0 && page.total in 0..65536)
                check(page.entries.size <= STORY_RECORD_PAGE_ROWS && page.total >= page.entries.size)
                check(page.entries.map { it.key }.toSet().size == page.entries.size)
                if (boundary != null) check(page.total == boundary.first && page.storyTime == boundary.second)
                check(page.nextCursor == null || (page.nextCursor != query.cursor && page.entries.isNotEmpty() &&
                    page.nextCursor.toByteArray(Charsets.UTF_8).size in 1..128))
                pageBoundary = identity to (page.total to page.storyTime)
                mutable.value = mutable.value.copy(loading = false, storyTime = page.storyTime, total = page.total,
                    entries = page.entries.map { it.copy(sources = it.sources.toList()) },
                    nextCursor = page.nextCursor, limitations = page.limitations.toList())
            } catch (cancelled: CancellationException) { throw cancelled }
            catch (failure: Exception) {
                if (!disposed && ticket == generation) mutable.value = mutable.value.copy(loading = false,
                    problem = (failure as? StoryRecordFailure)?.problem ?: StoryRecordProblem.INVALID_RESPONSE)
            }
        }
    }
    fun dismiss() {
        generation++
        pending?.cancel()
        pending = null
        pageBoundary = null
        mutable.value = StoryRecordState()
    }
    fun dispose() { disposed = true; dismiss() }
}

internal fun validStoryRecordSearch(text: String) =
    text.toByteArray(Charsets.UTF_8).size <= STORY_RECORD_SEARCH_BYTES && text.none { it.isISOControl() }

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
    fun openEvent(sequence: Long) {
        val current = mutable.value
        if (current.eventDetail == null) readEvent(current, sequence)
    }
    fun retryEvent() {
        val current = mutable.value
        val detail = current.eventDetail ?: return
        if (!detail.loading) readEvent(current, detail.reference, detail.scopedReference)
    }
    fun openScopedEvent(reference: StoryRecordScopedEvent) {
        val current = mutable.value
        if (current.eventDetail == null) readEvent(current, reference.sequence, reference)
    }
    private fun readEvent(current: StoryRecordState, sequence: Long, reference: StoryRecordScopedEvent? = null) {
        val context = current.context ?: return
        if (disposed || !current.visible || current.loading || current.problem != null ||
            sequence !in 1..context.revision) return
        if (reference == null && current.entries.none { sequence in it.eventSources }) return
        if (reference != null && current.entries.none { reference in it.scopedEventSources }) return
        val search = if (reference == null) "\"sequence\":$sequence," else {
            val original = reference.originalScope
            if (original.story != context.story.story || !validStoryRecordTurn(original.story) ||
                !validStoryRecordTurn(original.branch)) return
            // Search the exact serialized EventRow prefix in the CURRENT player
            // lens. Never open another branch session or flatten an ancestor ID.
            "\"event\":{\"sequence\":$sequence,\"scope\":{\"story\":\"${original.story}\",\"branch\":\"${original.branch}\"}"
        }
        val query = StoryRecordQuery(context, StoryRecordSection.HISTORY, search,
            version = if (reference == null) 1 else 2)
        val ticket = ++generation
        pending?.cancel()
        mutable.value = current.copy(eventDetail = StoryRecordEventDetail(sequence, scopedReference = reference))
        pending = scope.launch {
            try {
                val page = reader.readStoryRecord(query)
                if (disposed || ticket != generation) return@launch
                check(page.query == query && page.storyTime == current.storyTime && page.nextCursor == null)
                if (page.total == 0 && page.entries.isEmpty())
                    throw StoryRecordFailure(StoryRecordProblem.EVENT_UNAVAILABLE)
                check(page.total == 1 && page.entries.size == 1)
                val entry = page.entries.single()
                validateEntry(entry, query, page.storyTime)
                check(entry.origin == StoryRecordOrigin.RECORDED_OBSERVATION && entry.event?.sequence == sequence)
                check(entry.event?.originalScope == reference?.originalScope)
                mutable.value = mutable.value.copy(eventDetail = StoryRecordEventDetail(sequence, loading = false,
                    entry = freeze(entry), scopedReference = reference))
            } catch (cancelled: CancellationException) { throw cancelled }
            catch (failure: Exception) {
                if (!disposed && ticket == generation) mutable.value = mutable.value.copy(
                    eventDetail = StoryRecordEventDetail(sequence, loading = false,
                        problem = (failure as? StoryRecordFailure)?.problem ?: StoryRecordProblem.INVALID_RESPONSE,
                        scopedReference = reference))
            }
        }
    }
    fun back() {
        if (mutable.value.eventDetail == null) return
        generation++
        pending?.cancel()
        pending = null
        mutable.value = mutable.value.copy(eventDetail = null)
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
                val eventIds = page.entries.mapNotNull { it.event?.sequence }
                check(eventIds.toSet().size == eventIds.size)
                page.entries.forEach { validateEntry(it, query, page.storyTime) }
                if (boundary != null) check(page.total == boundary.first && page.storyTime == boundary.second)
                check(page.nextCursor == null || (page.nextCursor != query.cursor && page.entries.isNotEmpty() &&
                    page.nextCursor.toByteArray(Charsets.UTF_8).size in 1..128))
                pageBoundary = identity to (page.total to page.storyTime)
                mutable.value = mutable.value.copy(loading = false, storyTime = page.storyTime, total = page.total,
                    entries = page.entries.map(::freeze),
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

    private fun freeze(entry: StoryRecordEntry) = entry.copy(sources = entry.sources.toList(),
        eventSources = entry.eventSources.toList(), scopedEventSources = entry.scopedEventSources.toList())

    private fun validateEntry(entry: StoryRecordEntry, query: StoryRecordQuery, time: Long) {
        check(entry.key.isNotEmpty() && entry.eventSources.size <= 64 && entry.scopedEventSources.size <= 64)
        check(entry.eventSources.all { it in 1..query.context.revision } &&
            entry.eventSources.toSet().size == entry.eventSources.size)
        check(entry.scopedEventSources.distinct().size == entry.scopedEventSources.size)
        check(entry.scopedEventSources.all { ref ->
            ref.sequence in 1..query.context.revision && ref.originalScope.story == query.context.story.story &&
                validStoryRecordTurn(ref.originalScope.story) && validStoryRecordTurn(ref.originalScope.branch)
        })
        check(if (query.version == 1) entry.scopedEventSources.isEmpty() else entry.eventSources.isEmpty())
        if (entry.origin == StoryRecordOrigin.AUTHOR_CORRECTION)
            check(query.version == 2 && query.section == StoryRecordSection.HISTORY &&
                entry.sources.isEmpty() && entry.eventSources.isEmpty() &&
                entry.scopedEventSources.isEmpty() && entry.event == null)
        if (entry.origin == StoryRecordOrigin.RECORDED_OBSERVATION) {
            val event = checkNotNull(entry.event)
            check(query.section == StoryRecordSection.HISTORY && event.sequence in 1..query.context.revision &&
                event.storyTime in 0..time && validStoryRecordTurn(event.turn))
            if (query.version == 1) check(event.originalScope == null && entry.eventSources == listOf(event.sequence))
            else check(event.originalScope != null &&
                entry.scopedEventSources == listOf(StoryRecordScopedEvent(event.originalScope, event.sequence)))
        } else check(entry.event == null)
    }
}

internal fun validStoryRecordSearch(text: String) =
    text.toByteArray(Charsets.UTF_8).size <= STORY_RECORD_SEARCH_BYTES && text.none { it.isISOControl() }

internal fun validStoryRecordTurn(value: String) = value.length in 1..64 &&
    value.all { it in 'a'..'z' || it in 'A'..'Z' || it in '0'..'9' || it == '-' || it == '_' }

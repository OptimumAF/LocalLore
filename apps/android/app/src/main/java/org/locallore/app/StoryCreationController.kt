/* Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0 */
package org.locallore.app

import java.util.Collections
import java.util.UUID
import kotlinx.coroutines.CancellationException
import kotlinx.coroutines.CoroutineScope
import kotlinx.coroutines.CoroutineStart
import kotlinx.coroutines.Job
import kotlinx.coroutines.currentCoroutineContext
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.launch

internal data class StoryCreationUiState(
    val visible: Boolean = false,
    val busy: Boolean = false,
    val creating: Boolean = false,
    val closing: Boolean = false,
    val review: StoryCreationRequest? = null,
    val templates: List<StoryTemplateOption> = emptyList(),
    val playerNameDraft: String? = null,
    val playerNameEdited: Boolean = false,
    val toneDraft: String? = null,
    val excludedPhrasesDraft: String? = null,
    val notice: String? = null,
    val originalCapabilities: OriginalCapabilities? = null,
    val original: OriginalStoryUiState? = null,
)

/** Consent belongs to one displayed immutable review, never a replacement or automatic retry. */
internal class StoryCreationController(
    private val gateway: StoryCreationGateway,
    private val scope: CoroutineScope,
    private val onClosed: (StoryCreationClose) -> Unit,
) {
    private val mutable = MutableStateFlow(StoryCreationUiState())
    val state = mutable.asStateFlow()
    private var generation = 0L
    private var active: Job? = null
    private var disposed = false
    private var createStarted = false
    private var originalController: OriginalStoryController? = null
    fun chooseOriginal(expected: StoryCreationRequest) {
        val before=mutable.value
        if(disposed || !before.visible || before.busy || before.closing || before.review !== expected || before.original!=null) return
        val capabilities=before.originalCapabilities ?: return
        val port=gateway.originalStories() ?: return
        if(!capabilities.available)return
        generation++
        mutable.value=before.copy(review=null)
        originalController=OriginalStoryController(port,scope,
            { next -> if(!disposed && mutable.value.visible) mutable.value=mutable.value.copy(original=next) },::finish)
            .also { it.open(capabilities) }
    }
    fun editOriginal(expected: OriginalStoryUiState,input: OriginalInput,proposal: OriginalProposal?,title: String) =
        originalController?.edit(expected,input,proposal,title)
    fun generateOriginal(expected: OriginalStoryUiState) = originalController?.generate(expected)
    fun reviewOriginal(expected: OriginalStoryUiState) = originalController?.review(expected)
    fun confirmOriginal(expected: OriginalStoryUiState,review: OriginalReview) = originalController?.confirm(expected,review)

    fun open() {
        if (disposed || mutable.value.visible || active != null) return
        val ticket = ++generation
        val creationId = UUID.randomUUID().toString().replace("-", "")
        createStarted = false
        mutable.value = StoryCreationUiState(visible = true, busy = true)
        launch(ticket) {
            try {
                val catalog = gateway.templates()
                val originalCapabilities = gateway.originalStories()?.originalCapabilities()
                val options: List<StoryTemplateOption>
                val preview: StoryCreationPreview
                if (catalog == null) {
                    // Compatibility for original fake ports only; native errors never select this path.
                    preview = initialPreview(DEFAULT_STORY_TEMPLATE, legacyDefault = true)
                    check(preview.template == DEFAULT_STORY_TEMPLATE)
                    options = captureOptions(listOf(preview.option()))
                } else {
                    options = captureOptions(catalog)
                    preview = initialPreview(options.first().template)
                    check(preview.option() == options.first())
                }
                if (current(ticket)) mutable.value = mutable.value.copy(
                    templates = options, review = StoryCreationRequest(preview, preview.defaultTitle, creationId),
                    originalCapabilities = originalCapabilities,
                    playerNameDraft = preview.playerSetup?.playerName,
                    toneDraft = preview.presentation?.tone,
                    excludedPhrasesDraft = preview.presentation?.excludedPhrases?.joinToString("\n"),
                    notice = "Review this starter and title. Nothing is created until you choose Create.",
                )
            } catch (cancelled: CancellationException) {
                if (current(ticket)) mutable.value = mutable.value.copy(
                    notice = "Starter review stopped. No story was created.")
                throw cancelled
            } catch (_: Exception) {
                if (current(ticket)) mutable.value = mutable.value.copy(
                    notice = "Starter review is unavailable. No story was created. Close and try again.")
            }
        }
    }

    fun chooseTemplate(expected: StoryCreationRequest, option: StoryTemplateOption) {
        val before = mutable.value
        if (disposed || !before.visible || before.busy || before.creating || before.closing || createStarted ||
            before.review !== expected || before.templates.none { it === option } ||
            option.template == expected.preview.template) return
        if (expected.preview.playerSetup != null && !validStoryPlayerName(before.playerNameDraft ?: "")) {
            mutable.value = before.copy(notice = "Fix and review the player name before choosing another starter.")
            return
        }
        if (expected.preview.presentation != null && !hasReviewedCreation(expected, before.playerNameDraft,
                before.toneDraft, before.excludedPhrasesDraft)) {
            mutable.value = before.copy(notice = "Review the name and narration changes before choosing another starter.")
            return
        }
        val ticket = ++generation
        // Revoke the old confirmation synchronously before asking native code for the new view.
        mutable.value = before.copy(review = null, busy = true, notice = "Loading the selected starter…")
        launch(ticket) {
            try {
                val name = if (before.playerNameEdited) before.playerNameDraft else null
                val preview = when {
                    expected.preview.presentation != null -> presentedPreview(option.template, name, expected.preview.presentation)
                    expected.preview.playerSetup != null -> configuredPreview(option.template, name)
                    else -> capture(gateway.previewTemplate(option.template))
                }
                check(preview.option() == option)
                val title = if (expected.title == expected.preview.defaultTitle) preview.defaultTitle else expected.title
                if (current(ticket)) mutable.value = mutable.value.copy(
                    review = StoryCreationRequest(preview, title, expected.creationId),
                    playerNameDraft = preview.playerSetup?.playerName,
                    toneDraft = preview.presentation?.tone,
                    excludedPhrasesDraft = preview.presentation?.excludedPhrases?.joinToString("\n"),
                    notice = "Review this starter and title. Nothing is created until you choose Create.",
                )
            } catch (cancelled: CancellationException) {
                if (current(ticket)) mutable.value = mutable.value.copy(
                    notice = "Starter review stopped. No story was created.")
                throw cancelled
            } catch (_: Exception) {
                if (current(ticket)) mutable.value = mutable.value.copy(
                    notice = "The selected starter could not be reviewed. No story was created. Close and try again.")
            }
        }
    }

    fun editTone(expected: StoryCreationRequest, tone: String) {
        val before = mutable.value
        val review = before.review ?: return
        if (!presentationEditor(before, expected, review) || tone !in setOf("plain", "warm", "brisk")) return
        mutable.value = before.copy(review = review.copy(), toneDraft = tone,
            notice = "Review changes to update generated narration settings before creating the story.")
    }

    fun editExcludedPhrases(expected: StoryCreationRequest, text: String) {
        val before = mutable.value
        val review = before.review ?: return
        if (!presentationEditor(before, expected, review)) return
        mutable.value = before.copy(review = review.copy(), excludedPhrasesDraft = text,
            notice = "Review changes to update generated narration settings before creating the story.")
    }

    private fun presentationEditor(before: StoryCreationUiState, expected: StoryCreationRequest, review: StoryCreationRequest) =
        !disposed && before.visible && !before.busy && !before.creating && !before.closing && !createStarted &&
            review.preview.presentation != null && expected.preview === review.preview && expected.creationId == review.creationId

    fun editPlayerName(expected: StoryCreationRequest, text: String) {
        val before = mutable.value
        val review = before.review ?: return
        if (disposed || !before.visible || before.busy || before.creating || before.closing || createStarted ||
            review.preview.playerSetup == null || expected.preview !== review.preview ||
            expected.creationId != review.creationId) return
        // Copy even when the text matches: old consent cannot borrow a newly edited field.
        mutable.value = before.copy(review = review.copy(), playerNameDraft = text, playerNameEdited = true,
            notice = "Review changes to update your starting view before creating the story.")
    }

    fun reviewPlayerName(expected: StoryCreationRequest) = reviewChanges(expected)

    fun reviewChanges(expected: StoryCreationRequest) {
        val before = mutable.value
        if (disposed || !before.visible || before.busy || before.creating || before.closing || createStarted ||
            before.review !== expected || expected.preview.playerSetup == null ||
            hasReviewedCreation(expected, before.playerNameDraft, before.toneDraft, before.excludedPhrasesDraft)) return
        val name = before.playerNameDraft ?: return
        if (!validStoryPlayerName(name)) {
            mutable.value = before.copy(notice = "Use a player name of up to 64 characters without outer spaces, line breaks or control characters.")
            return
        }
        val presentation = storyPresentationDraft(before.toneDraft, before.excludedPhrasesDraft)
        if (expected.preview.presentation != null && presentation == null) {
            mutable.value = before.copy(notice = "Use up to eight distinct literal phrases, one per line, with no outer spaces or control characters.")
            return
        }
        val ticket = ++generation
        mutable.value = before.copy(review = null, busy = true, notice = "Reviewing story setup…")
        launch(ticket) {
            try {
                val preview = if (expected.preview.presentation == null) configuredPreview(expected.preview.template, name)
                    else presentedPreview(expected.preview.template, name, presentation)
                check(preview.option() == expected.preview.option())
                if (current(ticket)) mutable.value = mutable.value.copy(
                    review = expected.copy(preview = preview), playerNameDraft = name,
                    toneDraft = preview.presentation?.tone,
                    excludedPhrasesDraft = preview.presentation?.excludedPhrases?.joinToString("\n"),
                    notice = "Review this starting view. Nothing is created until you choose Create.",
                )
            } catch (cancelled: CancellationException) {
                if (current(ticket)) mutable.value = mutable.value.copy(
                    notice = "Story setup review stopped. No story was created.")
                throw cancelled
            } catch (_: Exception) {
                if (current(ticket)) mutable.value = mutable.value.copy(
                    notice = "Story setup could not be reviewed. No story was created. Close and try again.")
            }
        }
    }

    private suspend fun initialPreview(template: String, legacyDefault: Boolean = false): StoryCreationPreview {
        val presented = gateway.presentationPreview(template, null, null)
        if (presented != null) return capturePresented(presented, null, null)
        val setup = gateway.setupPreview(template, null)
        return if (setup != null) captureConfigured(setup, null)
            else capture(if (legacyDefault) gateway.preview() else gateway.previewTemplate(template))
    }
    private suspend fun configuredPreview(template: String, name: String?): StoryCreationPreview =
        captureConfigured(checkNotNull(gateway.setupPreview(template, name)), name)

    private fun captureConfigured(source: StoryCreationPreview, expectedName: String?): StoryCreationPreview {
        check(source.presentation == null)
        val setup = checkNotNull(source.playerSetup)
        check(validStoryPlayerName(setup.playerName) && (expectedName == null || setup.playerName == expectedName))
        check(Regex("[0-9a-f]{64}").matches(setup.templateSha256) &&
            Regex("[0-9a-f]{64}").matches(setup.setupSha256) && source.seedSha256 == setup.templateSha256)
        return capture(source)
    }

    private suspend fun presentedPreview(template: String, name: String?, presentation: StoryPresentation?): StoryCreationPreview {
        val settings = presentation?.let { it.copy(excludedPhrases = Collections.unmodifiableList(ArrayList(it.excludedPhrases))) }
        return capturePresented(checkNotNull(gateway.presentationPreview(template, name, settings)), name, settings)
    }
    private fun capturePresented(source: StoryCreationPreview, name: String?, expected: StoryPresentation?): StoryCreationPreview {
        val settings = checkNotNull(source.presentation)
        check(validStoryPresentation(settings) && settings == (expected ?: StoryPresentation()))
        return captureConfigured(source.copy(presentation = null), name).copy(
            presentation = settings.copy(excludedPhrases = Collections.unmodifiableList(ArrayList(settings.excludedPhrases))))
    }

    private fun capture(source: StoryCreationPreview): StoryCreationPreview {
        check(source.presentation == null) // Only the explicit presented-preview capability can supply these settings.
        check(validStoryTemplateProfile(source.template, source.profile))
        return source.copy(details = Collections.unmodifiableList(ArrayList(source.details)))
    }
    private fun captureOptions(source: List<StoryTemplateOption>): List<StoryTemplateOption> {
        check(source.size in 1..8)
        val options = source.map { it.copy() }
        check(options.first().template == DEFAULT_STORY_TEMPLATE)
        check(options.map { it.template }.toSet().size == options.size)
        check(options.all { validStoryTemplateProfile(it.template, it.profile) && validStoryTitle(it.defaultTitle) &&
            it.description.isNotEmpty() && it.description.toByteArray(Charsets.UTF_8).size <= 2048 })
        return Collections.unmodifiableList(options)
    }

    fun editTitle(expected: StoryCreationRequest, text: String) {
        val before = mutable.value
        val review = before.review ?: return
        if (disposed || !before.visible || before.busy || before.creating || before.closing || createStarted ||
            expected.preview !== review.preview || expected.creationId != review.creationId) return
        // A field intent replaces only title on the latest request, including edits before a frame.
        mutable.value = before.copy(review = review.copy(title = text), notice = null)
    }

    fun confirm(expected: StoryCreationRequest) {
        val before = mutable.value
        if (disposed || !before.visible || before.busy || before.creating || before.closing || createStarted ||
            before.review !== expected) return
        if (!hasReviewedCreation(expected, before.playerNameDraft, before.toneDraft, before.excludedPhrasesDraft)) {
            mutable.value = before.copy(notice = "Review the setup changes before creating the story.")
            return
        }
        if (!validStoryTitle(expected.title)) {
            mutable.value = before.copy(notice = "Use a title of up to 80 characters without outer spaces, line breaks or control characters.")
            return
        }
        // Consume synchronously, before the coroutine or native boundary can yield.
        createStarted = true
        val ticket = ++generation
        mutable.value = before.copy(review = null, busy = true, creating = true,
            notice = "Creating the story. If stopped, it may already exist; close to refresh the library.")
        launch(ticket) {
            val saved = try { gateway.create(expected) }
            catch (cancelled: CancellationException) {
                if (current(ticket)) mutable.value = mutable.value.copy(
                    notice = "Creation was stopped. A story may already exist. Close to refresh the library.")
                throw cancelled
            } catch (_: Exception) {
                if (current(ticket)) mutable.value = mutable.value.copy(
                    notice = "Creation could not be confirmed. A story may already exist. Close to refresh the library.")
                return@launch
            }
            if (current(ticket)) finish(StoryCreationClose(saved = saved))
        }
    }

    fun dismiss() {
        if(mutable.value.original!=null) { originalController?.dismiss(); return }
        val before = mutable.value
        if (disposed || !before.visible || before.closing) return
        val ticket = ++generation
        val previous = active
        val refresh = createStarted
        mutable.value = before.copy(review = null, closing = true, busy = previous != null,
            notice = if (refresh) "Finishing local work. A story may already exist; the library will refresh."
                else "Closing starter review…")
        val closing = scope.launch(start = CoroutineStart.LAZY) {
            previous?.join()
            if (!disposed && generation == ticket && mutable.value.visible && mutable.value.closing)
                finish(StoryCreationClose(refreshRequired = refresh))
        }
        active = closing
        previous?.cancel()
        closing.start()
    }

    fun dispose() {
        if (disposed) return
        disposed = true
        originalController?.dispose()
        generation++
        active?.cancel()
        active = null
        mutable.value = StoryCreationUiState()
        // The parent owns transport retirement and recovery on its next coherent library read.
    }

    private fun current(ticket: Long) = !disposed && generation == ticket && mutable.value.visible && !mutable.value.closing
    private fun launch(ticket: Long, block: suspend () -> Unit) {
        val job = scope.launch(start = CoroutineStart.LAZY) {
            try { block() }
            finally {
                if (active === currentCoroutineContext()[Job]) active = null
                if (current(ticket)) mutable.value = mutable.value.copy(busy = false, creating = false)
            }
        }
        active = job
        job.start()
    }
    private fun finish(result: StoryCreationClose) {
        originalController=null
        generation++
        active = null
        createStarted = false
        mutable.value = StoryCreationUiState()
        onClosed(result)
    }
}

/* Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0 */
package org.locallore.app

import org.json.JSONArray
import org.json.JSONObject
import java.util.UUID
import java.util.Collections
import java.util.concurrent.atomic.AtomicBoolean
import kotlinx.coroutines.NonCancellable
import kotlinx.coroutines.sync.Mutex
import kotlinx.coroutines.sync.withLock
import kotlinx.coroutines.withContext

/** IO confinement is supplied by the transport; the controller and tests share this protocol. */
internal interface WorkspaceTransport {
    suspend fun exchange(command: JSONObject): JSONObject
    fun close()
}

/** No gameplay rules or ledger live here. Only authoritative player snapshots reach the UI. */
internal class DurableGateway(
    private val transport: WorkspaceTransport,
    autoCreateIfEmpty: Boolean = true,
    initialScopeHint: PlayDraftScope? = null,
) : DemoGateway, StoryCreationGateway, OriginalStoryGateway {
    private var mayAutoCreate = autoCreateIfEmpty
    // Navigation IDs are an unresolved UI hint, never a saved engine/session.
    // Keep them through initialization failures, including failures after attach.
    private var pendingInitialScopeHint = initialScopeHint
    private var initialSelectionUnavailable = false
    override val durable = true
    override val storyRecords = true
    private var session: String? = null
    private var scope: JSONObject? = null
    private var revision = 0L
    private var operation: Pending? = null
    private var serial = 0L
    private var textProvider = TextProvider.UNAVAILABLE
    private val playerMetadataLock = Any()
    private var playerAttachment: Any = Any()
    private var coherentPlayerSnapshot = false
    private var playerBinding: PlayerSnapshotBinding? = null
    private data class PlayerReadOwner(val attachment: Any,val session: String,val scopeObject: JSONObject,val scope: PlayDraftScope)
    private fun invalidatePlayerSnapshot() = synchronized(playerMetadataLock) { coherentPlayerSnapshot=false }
    /** Called under playerMetadataLock. No native call or suspension is permitted in this guard. */
    private fun requirePlayerOwner(owner: PlayerReadOwner) {
        if(closed.get())throw WorkspaceFailure("Closed")
        if(playerAttachment !== owner.attachment || session!=owner.session || scope !== owner.scopeObject ||
            scope?.opt("story")!=owner.scope.story || scope?.opt("branch")!=owner.scope.branch)throw WorkspaceFailure("Stale")
    }
    private fun playerCommand(op: String,owner: PlayerReadOwner) = command(op).put("session",owner.session)
        .put("scope",JSONObject().put("story",owner.scope.story).put("branch",owner.scope.branch))
    private fun playerScopeMatches(value: JSONObject,owner: PlayerReadOwner) =
        value.opt("story")==owner.scope.story && value.opt("branch")==owner.scope.branch
    // Order cancellation after a finite native submit, never after generation/prepare.
    private val submissionGate = Mutex()
    private val closed = AtomicBoolean(false)
    private data class Pending(val session: String, val scope: JSONObject, val turn: String,
        val request: JSONObject, val mode: DemoMode?, val serial: Long, var cancelled: Boolean = false)

    /** Read-only UI binding, never a grant or a new native session. */
    internal fun forkContext(selected: SavedStory, expectedHead: Long, epoch: Long): BranchForkContext? = synchronized(playerMetadataLock) {
        val capturedSession = session ?: return@synchronized null
        val capturedScope = scope ?: return@synchronized null
        if (closed.get() || !coherentPlayerSnapshot || operation != null || epoch < 0 ||
            revision != expectedHead || selected.revision != revision || revision !in 0..FORK_MAX_REVISION ||
            capturedSession.toByteArray(Charsets.UTF_8).size !in 1..128 ||
            capturedScope.getString("story") != selected.story || capturedScope.getString("branch") != selected.branch ||
            !timelineId.matches(selected.story) || !timelineId.matches(selected.branch)) return@synchronized null
        BranchForkContext(capturedSession, ForkScope(selected.story, selected.branch), revision,
            view = "play", observer = "player", epoch = epoch)
    }

    private suspend fun call(command: JSONObject): JSONObject {
        check(!closed.get())
        val reply = transport.exchange(command)
        check(reply.getInt("version") == 1)
        if (reply.getString("status") != "ok") throw WorkspaceFailure(reply.optString("error", "Storage"))
        return reply.getJSONObject("data")
    }
    private fun command(op: String) = JSONObject().put("op", op)
    override suspend fun readStoryRecord(query: StoryRecordQuery): StoryRecordPage {
        val (owner, binding) = synchronized(playerMetadataLock) {
            val capturedSession = session ?: throw StoryRecordFailure(StoryRecordProblem.UNAVAILABLE)
            val capturedScope = scope ?: throw StoryRecordFailure(StoryRecordProblem.UNAVAILABLE)
            val bound = playerBinding
            if (closed.get() || !coherentPlayerSnapshot || bound == null)
                throw StoryRecordFailure(StoryRecordProblem.UNAVAILABLE)
            if (bound.session != capturedSession)
                throw StoryRecordFailure(StoryRecordProblem.STALE)
            PlayerReadOwner(playerAttachment, capturedSession, capturedScope, bound.scope) to bound
        }
        fun current() = synchronized(playerMetadataLock) {
            try {
                requirePlayerOwner(owner)
                coherentPlayerSnapshot && playerBinding == binding && operation == null &&
                    revision == query.context.revision &&
                    owner.scope.story == query.context.story.story && owner.scope.branch == query.context.story.branch
            } catch (_: WorkspaceFailure) { false }
        }
        if (!current()) throw StoryRecordFailure(StoryRecordProblem.STALE)
        val data = try { call(StoryRecordWire.command(owner.session, query)) }
        catch (failure: WorkspaceFailure) {
            throw StoryRecordFailure(if (failure.category in setOf("Stale", "Scope", "Session"))
                StoryRecordProblem.STALE else StoryRecordProblem.UNAVAILABLE)
        }
        if (!current()) throw StoryRecordFailure(StoryRecordProblem.STALE)
        return StoryRecordWire.decode(data, query, binding.observer)
    }
    private fun scoped(op: String, pending: Pending? = null): JSONObject = command(op)
        .put("session", pending?.session ?: checkNotNull(session))
        .put("scope", pending?.scope ?: checkNotNull(scope))
        .also { if (pending != null) it.put("turn", pending.turn) }

    override suspend fun initialize(): SavedSnapshot {
        if (session != null) return snapshot()
        return openLibrary(mayAutoCreate)
    }
    private suspend fun workspace(): JSONObject = call(command("workspace"))
    /** The existing native catalog wire, shared by initial selection and snapshots. */
    private fun workspaceStories(workspace: JSONObject): List<SavedStory> = try {
        fun fields(value: JSONObject, expected: Set<String>) {
            check(value.keys().asSequence().toSet() == expected)
        }
        fun text(value: JSONObject, key: String): String = value.get(key) as? String ?: error("Wire")
        fun count(value: JSONObject, key: String): Long {
            val raw = value.get(key)
            check(raw is Int || raw is Long)
            return (raw as Number).toLong().also { check(it >= 0) }
        }
        fields(workspace, setOf("persistent", "location", "schema_version", "database_schema_version", "stories"))
        check(workspace.get("persistent") == true && count(workspace, "schema_version") == 1L)
        check(count(workspace, "database_schema_version") == 5L)
        text(workspace, "location")
        val rows = workspace.get("stories") as? JSONArray ?: error("Wire")
        check(rows.length() <= 256)
        val stories = (0 until rows.length()).map { index ->
            val row = rows.get(index) as? JSONObject ?: error("Wire")
            fields(row, setOf("scope", "title", "revision", "drafts"))
            val scope = row.get("scope") as? JSONObject ?: error("Wire")
            fields(scope, setOf("story", "branch"))
            val story = text(scope, "story")
            val branch = text(scope, "branch")
            check(timelineId.matches(story) && timelineId.matches(branch))
            val revision = count(row, "revision")
            count(row, "drafts")
            SavedStory(story, branch, text(row, "title"), revision)
        }
        check(stories.map { it.story }.toSet().size == stories.size)
        stories
    } catch (_: Exception) {
        throw WorkspaceFailure("Malformed")
    }
    private suspend fun openLibrary(allowCreate: Boolean): SavedSnapshot {
        val workspace = workspace()
        val stories = workspaceStories(workspace)
        val hint = pendingInitialScopeHint
        val hintedRoot = hint?.let { candidate -> stories.singleOrNull { it.story == candidate.story } }
        val hintedTimeline = if (hintedRoot != null) {
            // Only native, strictly decoded active branch metadata can authorize resume.
            decodeTimelines(call(command("branches").put("story", hintedRoot.story)), hintedRoot)
                .singleOrNull { it.branch == hint?.branch }
        } else null
        initialSelectionUnavailable = hint != null && hintedTimeline == null
        // Automatic bootstrap is a one-time compatibility option. Never repeat an uncertain create.
        // The hint neither enables nor retries this independently configured compatibility path.
        mayAutoCreate = false
        if (stories.isEmpty() && !allowCreate) return emptySnapshot(workspace)
        attach(if (stories.isEmpty()) call(command("create").put("seed", "lantern-quay-v1")) else {
            val selected = if (hintedTimeline != null) {
                JSONObject().put("story", hintedTimeline.story).put("branch", hintedTimeline.branch)
            } else {
                val first = stories.first()
                JSONObject().put("story", first.story).put("branch", first.branch)
            }
            call(command("resume").put("scope", selected))
        })
        return snapshot()
    }
    private fun emptySnapshot(workspace: JSONObject): SavedSnapshot {
        check(workspace.getJSONArray("stories").length() == 0)
        return resolvedInitialSelection(SavedSnapshot(0, "", emptyList(), workspace.getString("location"), 1,
            emptyList(), null, databaseSchemaVersion = workspace.getInt("database_schema_version")))
    }
    private fun resolvedInitialSelection(saved: SavedSnapshot): SavedSnapshot {
        val unavailable = pendingInitialScopeHint != null && initialSelectionUnavailable
        pendingInitialScopeHint = null
        initialSelectionUnavailable = false
        return saved.copy(selectionRestoreUnavailable = unavailable)
    }
    override suspend fun reconcileSaved(): SavedSnapshot {
        invalidatePlayerSnapshot()
        mayAutoCreate = false
        operation?.cancelled = true
        operation = null
        closeSession()
        return openLibrary(allowCreate = false)
    }
    private fun attach(data: JSONObject) {
        val attachedSession=data.getString("session"); val attachedScope=data.getJSONObject("scope"); val head=data.getLong("revision")
        synchronized(playerMetadataLock) {
            if(closed.get())throw WorkspaceFailure("Closed")
            playerAttachment=Any(); coherentPlayerSnapshot=false; playerBinding=null
            session=attachedSession; scope=attachedScope; revision=head; operation=null
        }
    }
    override suspend fun snapshot(): SavedSnapshot {
        val owner=synchronized(playerMetadataLock) {
            coherentPlayerSnapshot=false
            val selectedSession=session
            if(selectedSession==null)null else {
                val selectedScope=checkNotNull(scope)
                PlayerReadOwner(playerAttachment,selectedSession,selectedScope,
                    PlayDraftScope(selectedScope.getString("story"),selectedScope.getString("branch")))
            }
        }
        if(owner==null)return openLibrary(allowCreate=false)
        fun currentPlayerScope() = synchronized(playerMetadataLock) { requirePlayerOwner(owner) }
        // Open refreshes revision from validated persisted canon before coherent player inspection.
        val opened = call(playerCommand("open",owner))
        check(playerScopeMatches(opened.getJSONObject("scope"),owner))
        val playerRevision=opened.getLong("revision")
        synchronized(playerMetadataLock) { requirePlayerOwner(owner); revision=playerRevision }
        val view = call(playerCommand("play_snapshot",owner).put("expected_revision", playerRevision))
        currentPlayerScope()
        check(playerScopeMatches(view.getJSONObject("scope"),owner))
        check(view.getLong("revision") == playerRevision)
        val player = view.getJSONObject("player")
        check(player.getLong("revision") == playerRevision)
        check(playerScopeMatches(player.getJSONObject("scope"),owner))
        val nativeObserver=player.get("observer")
        synchronized(playerMetadataLock) { requirePlayerOwner(owner); bindPlayerSnapshot(owner.session,owner.scope,nativeObserver,playerBinding) }
        val receipts = view.getJSONArray("receipts")
        val messages = mutableListOf<SceneMessage>()
        for (i in 0 until receipts.length()) {
            val receipt = receipts.getJSONObject(i)
            val request = receipt.getJSONObject("request")
            // Inherited accepted receipts keep their original ancestor scope. Rust's
            // player snapshot owns lineage/fork filtering; never rewrite those requests.
            val originalScope = request.getJSONObject("scope")
            check(originalScope.getString("story") == owner.scope.story)
            check(timelineId.matches(originalScope.getString("branch")))
            val intent = request.getJSONObject("intent")
            val playerText = when (intent.getString("kind")) {
                "actions" -> intent.getJSONArray("value").toString()
                "dialogue" -> intent.getJSONObject("value").getString("text")
                "free_text" -> intent.getJSONObject("value").getString("text")
                else -> "Recorded intention"
            }
            messages += SceneMessage(i * 2L + 1, playerText, true)
            messages += SceneMessage(i * 2L + 2, receipt.getString("narration"), false)
        }
        val workspace = workspace()
        // Host-v1's workspace contract and the SQLite implementation have separate versions.
        val databaseSchema = workspace.getInt("database_schema_version")
        check(databaseSchema == 5)
        val stories = workspaceStories(workspace)
        val root = checkNotNull(stories.singleOrNull { it.story == owner.scope.story })
        val timelines = decodeTimelines(call(command("branches").put("story", root.story)), root)
        val current = checkNotNull(timelines.singleOrNull { it.branch == owner.scope.branch })
        // A concurrent owner can advance between calls. Fail closed and recover a new
        // coherent snapshot rather than attaching a different head's catalog metadata.
        if (current.revision != playerRevision) throw WorkspaceFailure("Stale")
        textProvider = readTextProvider()
        val saved = SavedSnapshot(playerRevision, if (view.getJSONObject("inventory").has("potion")) "You" else "Not in your inventory",
            messages.takeLast(40), workspace.getString("location"), 1, stories,
            SavedStory(current.story, current.branch, root.title, current.revision), current.uncommittedDrafts,
            view.getString("rules"), textProvider, databaseSchemaVersion = databaseSchema, timelines = timelines)
        synchronized(playerMetadataLock) {
            requirePlayerOwner(owner)
            if(revision!=playerRevision)throw WorkspaceFailure("Stale")
            // Another read may have published while this read awaited catalogs/provider metadata.
            playerBinding=bindPlayerSnapshot(owner.session,owner.scope,nativeObserver,playerBinding)
            coherentPlayerSnapshot=true
        }
        return resolvedInitialSelection(saved)
    }
    private suspend fun readTextProvider(): TextProvider {
        val capabilities = call(command("capabilities"))
        val available = capabilities.get("free_text") as? Boolean ?: error("Invalid capability")
        if (!available) return TextProvider.UNAVAILABLE
        val status = call(command("model_status"))
        val real = status.get("real_model") as? Boolean ?: error("Invalid provider")
        val provider = status.get("provider") as? String ?: error("Invalid provider")
        val configured = status.get("status") as? String ?: error("Invalid provider")
        return when {
            real && provider.isNotBlank() && configured == "configured_native_owner" &&
                status.get("loaded") === JSONObject.NULL -> TextProvider.LOCAL
            !real && provider == "android-scripted-play-v2" &&
                configured == "configured_fixture_owner" && status.get("loaded") == false -> TextProvider.SCRIPTED
            else -> TextProvider.UNAVAILABLE
        }
    }
    override suspend fun respond(action: DemoAction, revision: Long, mode: DemoMode): DemoResult {
        check(operation == null)
        val actionCommand = when (action) {
            DemoAction.GIVE_POTION -> command("give").put("item", "potion").put("to", "mira").put("quantity", 1)
            DemoAction.TRY_ABILITY -> command("use_ability").put("ability", "blink")
        }
        val request = JSONObject().put("version", 1).put("scope", checkNotNull(scope))
            .put("turn", UUID.randomUUID().toString()).put("expected_revision", revision)
            .put("intent", JSONObject().put("kind", "actions").put("value", JSONArray().put(actionCommand)))
        return prepareRequest(request, mode)
    }
    override suspend fun respondText(input: PlayInput, revision: Long): DemoResult {
        check(operation == null)
        if (textProvider == TextProvider.UNAVAILABLE) return DemoResult.Rejected("Unsupported")
        if (!validPlayInput(input)) return DemoResult.Rejected("Malformed")
        val request = JSONObject().put("version", 1).put("scope", checkNotNull(scope))
            .put("turn", UUID.randomUUID().toString()).put("expected_revision", revision)
            .put("intent", JSONObject().put("kind", "free_text").put("value",
                JSONObject().put("kind", input.kind.wire).put("text", input.text)))
        return prepareRequest(request, null)
    }
    private fun submitCommand(pending: Pending): JSONObject = command(if (pending.mode == null) "free_text" else "submit")
        .put("session", pending.session).put("request", pending.request).also {
            pending.mode?.let { mode -> it.put("mode", mode.name.lowercase(java.util.Locale.ROOT)) }
        }
    private suspend fun prepareRequest(request: JSONObject, mode: DemoMode?): DemoResult {
        invalidatePlayerSnapshot()
        val pending = Pending(checkNotNull(session), checkNotNull(scope), request.getString("turn"), request, mode, ++serial)
        operation = pending // Keep the original key even if submit acknowledgement is lost.
        try {
            val submitted = submitOriginal(pending) ?: return DemoResult.Rejected("Cancelled")
            if (pending.cancelled) return DemoResult.Rejected("Cancelled")
            val prepared = if (submitted.getString("phase") == "queued") call(scoped("prepare", pending)) else submitted
            return result(prepared, pending)
        } catch (failure: WorkspaceFailure) {
            // An explicit rejection before acceptance cannot create canon; transport uncertainty stays pending.
            if (failure.category in setOf("Full", "Busy", "Database", "Integrity", "Io", "Internal")) throw failure
            if (operation === pending) operation = null
            return DemoResult.Rejected(failure.category)
        }
    }
    private suspend fun submitOriginal(pending: Pending): JSONObject? = withContext(NonCancellable) {
        submissionGate.withLock {
            if (pending.cancelled) null else call(submitCommand(pending))
        }
    }
    private fun result(data: JSONObject, pending: Pending): DemoResult {
        check(data.getString("turn") == pending.turn && sameScope(data.getJSONObject("scope"), pending.scope))
        check(data.getLong("expected_revision") == pending.request.getLong("expected_revision"))
        val resolved = when (data.getString("phase")) {
        "ready" -> DemoResult.Prepared(0, pending.serial)
        "committed" -> {
            val receipt = data.getJSONObject("receipt")
            check(sameJson(receipt.getJSONObject("request"), pending.request))
            DemoResult.Accepted(pending.request.getLong("expected_revision") + 1, "", receipt.getString("narration"))
        }
        "cancelled", "failed", "stale" -> {
            DemoResult.Rejected(data.optString("error").takeUnless { it.isBlank() || it == "null" } ?: "Cancelled")
        }
        else -> error("Unfinished")
        }
        // Decode the entire authoritative result before releasing its recovery key.
        if (resolved !is DemoResult.Prepared && operation === pending) operation = null
        return resolved
    }
    private fun acknowledgeCancellation(data: JSONObject, pending: Pending) {
        // An unfinished or foreign reply cannot release the original recovery key.
        check(data.getString("phase") in setOf("committed", "cancelled", "failed", "stale"))
        result(data, pending) // Validate the complete original binding before releasing it.
    }
    override suspend fun commitAsync(result: DemoResult): DemoResult {
        if (result !is DemoResult.Prepared) return result
        val pending = operation ?: return DemoResult.Rejected("Cancelled")
        if (pending.cancelled || result.operation != pending.serial) return DemoResult.Rejected("Cancelled")
        val data = try { call(scoped("commit", pending)) }
            catch (failure: Exception) {
                // The original key is the only authority after a lost commit acknowledgement.
                val status = try { call(scoped("turn_status", pending)) } catch (_: Exception) { throw failure }
                if (status.optString("phase") !in setOf("committed", "cancelled", "failed", "stale")) throw failure
                // Ready/queued work is still uncertain. Even a terminal-looking malformed
                // reply cannot discard the key or hide the primary storage error.
                return try { this.result(status, pending) } catch (_: Exception) { throw failure }
            }
        return this.result(data, pending)
    }
    override suspend fun recoverSaved(): SavedSnapshot {
        invalidatePlayerSnapshot()
        if (session == null) return initialize()
        operation?.let { pending ->
            if (pending.cancelled) {
                try { submissionGate.withLock { acknowledgeCancellation(call(scoped("cancel", pending)), pending) } }
                catch (failure: WorkspaceFailure) {
                    if (failure.category != "UnknownTurn") throw failure
                    if (operation === pending) operation = null
                }
                return snapshot()
            }
            var status = try { call(scoped("turn_status", pending)) }
                catch (failure: WorkspaceFailure) {
                    if (failure.category != "UnknownTurn") throw failure
                    submitOriginal(pending) ?: return snapshot()
                }
            if (status.getString("phase") == "queued") status = call(scoped("prepare", pending))
            if (status.getString("phase") == "ready") status = call(scoped("commit", pending))
            result(status, pending)
        }
        return snapshot()
    }
    override fun cancel() { operation?.cancelled = true }
    override suspend fun cancelSaved(): SavedSnapshot {
        invalidatePlayerSnapshot()
        operation?.let { pending ->
            pending.cancelled = true
            val status = try { submissionGate.withLock { call(scoped("cancel", pending)) } }
                catch (failure: WorkspaceFailure) {
                    if (failure.category != "UnknownTurn") throw failure
                    // Cancellation may beat submit on IO. The captured request remains
                    // cancelled even if its late submit later creates an uncommitted draft.
                    // Never discard a newer operation or regenerate this original key.
                    if (operation === pending) operation = null
                    return@let
                }
            acknowledgeCancellation(status, pending)
        }
        return snapshot()
    }
    private suspend fun closeSession() {
        val detached=synchronized(playerMetadataLock) {
            playerAttachment=Any(); coherentPlayerSnapshot=false; playerBinding=null
            Triple(playerAttachment,session,scope?.let { PlayDraftScope(it.getString("story"),it.getString("branch")) })
        }
        if (detached.second != null) {
            val selected=checkNotNull(detached.third)
            try { call(command("close").put("session",detached.second)
                .put("scope",JSONObject().put("story",selected.story).put("branch",selected.branch))) }
            catch (failure: WorkspaceFailure) {
                if (failure.category != "Closed") throw failure
            }
        }
        synchronized(playerMetadataLock) {
            if(playerAttachment === detached.first) {
                playerAttachment=Any(); session=null; scope=null; revision=0; playerBinding=null; coherentPlayerSnapshot=false
            }
        }
    }
    private suspend fun release() {
        invalidatePlayerSnapshot()
        operation?.let { pending ->
            pending.cancelled = true
            try {
                val status = submissionGate.withLock { call(scoped("cancel", pending)) }
                acknowledgeCancellation(status, pending)
            } catch (failure: WorkspaceFailure) {
                if (failure.category !in setOf("Closed", "UnknownTurn")) throw failure
                if (operation === pending) operation = null
            }
        }
        closeSession()
    }
    override fun originalStories(): OriginalStoryGateway = this
    private fun authoringReady() {
        if (closed.get()) throw WorkspaceFailure("Closed")
        if (operation != null) throw WorkspaceFailure("Busy")
    }
    override suspend fun originalCapabilities(): OriginalCapabilities {
        authoringReady(); return OriginalStoryWire.capabilities(call(command("authoring_capabilities")))
    }
    override suspend fun beginOriginal(input: OriginalInput): OriginalJob {
        authoringReady()
        val value=OriginalStoryWire.input(input.frozen()); OriginalStoryWire.input(value)
        return OriginalStoryWire.job(call(command("authoring_begin").put("input",value)))
    }
    override suspend fun generateOriginal(job: String): OriginalGenerated {
        authoringReady()
        return OriginalStoryWire.generated(call(command("authoring_generate").put("job",job))).also { check(it.job==job) }
    }
    override suspend fun reviewOriginal(job: String, input: OriginalInput, proposal: OriginalProposal, title: String): OriginalReview {
        authoringReady()
        val i=input.frozen(); val p=proposal.frozen()
        return OriginalStoryWire.review(call(command("authoring_review").put("job",job).put("input",OriginalStoryWire.input(i))
            .put("proposal",OriginalStoryWire.proposal(p)).put("title",title))).also {
            check(it.job==job && it.input==i && it.proposal==p && it.title==title)
        }
    }
    override suspend fun cancelOriginal(job: String): Boolean {
        if(closed.get()) throw WorkspaceFailure("Closed")
        return OriginalStoryWire.cancelled(call(command("authoring_cancel").put("job",job)))
    }
    override suspend fun createOriginal(review: OriginalReview, creationId: String): SavedSnapshot {
        authoringReady()
        check(Regex("[0-9a-f]{32}").matches(creationId) && Regex("[0-9a-f]{64}").matches(review.reviewSha256))
        release()
        val data=call(command("authoring_create").put("job",review.job).put("review_sha256",review.reviewSha256).put("creation_id",creationId))
        try {
            check(data.keys().asSequence().toSet()==setOf("session","scope","revision","created"))
            check(data.get("created") is Boolean)
            val selected=data.getJSONObject("scope")
            check(selected.keys().asSequence().toSet()==setOf("story","branch"))
            check(selected.get("story")=="original-$creationId" && selected.get("branch")=="main")
            val head=data.get("revision"); check((head is Int || head is Long) && (head as Number).toLong()>=0)
            check(localUtf8(data.get("session") as String).size in 1..128)
        } catch (_: Exception) { throw WorkspaceFailure("Malformed") }
        attach(data)
        return snapshot().also {
            val selected=it.selected
            check(selected!=null && selected.story=="original-$creationId" && selected.branch=="main" && selected.title==review.title)
        }
    }
    override suspend fun templates(): List<StoryTemplateOption> {
        if (closed.get()) throw WorkspaceFailure("Closed")
        if (operation != null) throw WorkspaceFailure("Busy")
        val data = call(command("story_templates"))
        if (closed.get()) throw WorkspaceFailure("Closed")
        return StoryCreationWire.templates(data)
    }
    override suspend fun preview(): StoryCreationPreview = previewTemplate(DEFAULT_STORY_TEMPLATE)
    override suspend fun previewTemplate(template: String): StoryCreationPreview {
        if (closed.get()) throw WorkspaceFailure("Closed")
        if (operation != null) throw WorkspaceFailure("Busy")
        val data = call(command("story_template").put("template", template))
        if (closed.get()) throw WorkspaceFailure("Closed")
        val preview = StoryCreationWire.preview(data)
        if (preview.template != template) throw WorkspaceFailure("Malformed")
        return preview
    }
    override suspend fun setupPreview(template: String, playerName: String?): StoryCreationPreview {
        if (closed.get()) throw WorkspaceFailure("Closed")
        if (operation != null) throw WorkspaceFailure("Busy")
        val data = call(command("story_setup").put("template", template).put("player_name", playerName ?: JSONObject.NULL))
        if (closed.get()) throw WorkspaceFailure("Closed")
        val preview = StoryCreationWire.setupPreview(data)
        if (preview.template != template || (playerName != null && preview.playerSetup?.playerName != playerName))
            throw WorkspaceFailure("Malformed")
        return preview
    }
    override suspend fun presentationPreview(template: String, playerName: String?, presentation: StoryPresentation?): StoryCreationPreview {
        if (closed.get()) throw WorkspaceFailure("Closed")
        if (operation != null) throw WorkspaceFailure("Busy")
        val expected = presentation?.let { it.copy(excludedPhrases = Collections.unmodifiableList(ArrayList(it.excludedPhrases))) }
            ?: StoryPresentation()
        val settings = if (presentation == null) JSONObject.NULL else StoryCreationWire.presentation(expected)
        val data = call(command("story_presentation").put("template", template)
            .put("player_name", playerName ?: JSONObject.NULL).put("presentation", settings))
        if (closed.get()) throw WorkspaceFailure("Closed")
        val preview = StoryCreationWire.presentationPreview(data)
        if (preview.template != template || (playerName != null && preview.playerSetup?.playerName != playerName) ||
            preview.presentation != expected) throw WorkspaceFailure("Malformed")
        return preview
    }
    override suspend fun create(request: StoryCreationRequest): SavedSnapshot {
        if (closed.get()) throw WorkspaceFailure("Closed")
        if (operation != null) throw WorkspaceFailure("Busy")
        val input = StoryCreationWire.command(request)
        release()
        val data = call(input)
        try {
            check(data.keys().asSequence().toSet() == setOf("session", "scope", "revision", "created"))
            check(data.get("created") is Boolean)
            val resultScope = data.getJSONObject("scope")
            check(resultScope.keys().asSequence().toSet() == setOf("story", "branch"))
            check(resultScope.get("story") == "quay-${request.creationId}" && resultScope.get("branch") == "main")
            val head = data.get("revision")
            check((head is Int || head is Long) && (head as Number).toLong() >= 0)
            check((data.get("session") as String).toByteArray(Charsets.UTF_8).size in 1..128)
        } catch (_: Exception) { throw WorkspaceFailure("Malformed") }
        attach(data)
        val saved = snapshot()
        val selected = saved.selected
        if (selected == null || selected.story != "quay-${request.creationId}" || selected.branch != "main" ||
            selected.title != request.title) {
            invalidatePlayerSnapshot()
            throw WorkspaceFailure("Stale")
        }
        return saved
    }
    override suspend fun createSaved(): SavedSnapshot {
        release()
        attach(call(command("create").put("seed", "lantern-quay-v1")))
        return snapshot()
    }
    override suspend fun resumeSaved(story: SavedStory): SavedSnapshot {
        release()
        attach(call(command("resume").put("scope", JSONObject().put("story", story.story).put("branch", story.branch))))
        return snapshot()
    }
    override fun close() {
        if (closed.compareAndSet(false, true)) {
            synchronized(playerMetadataLock) { playerAttachment=Any(); coherentPlayerSnapshot=false; playerBinding=null }
            operation?.cancelled=true; transport.close()
        }
    }
}
internal class WorkspaceFailure(val category: String) : Exception("Workspace operation failed")
private val timelineId = Regex("[A-Za-z0-9_-]{1,64}")

/** Metadata validation only. Replay, history eligibility and gameplay remain Rust-owned. */
private fun decodeTimelines(data: JSONObject, root: SavedStory): List<SavedTimeline> = try {
    check(data.toString().toByteArray(Charsets.UTF_8).size <= 60 * 1024)
    fun fields(value: JSONObject, expected: Set<String>) {
        check(value.keys().asSequence().toSet() == expected)
    }
    fun text(value: JSONObject, key: String): String = value.get(key) as? String ?: error("Wire")
    fun count(value: JSONObject, key: String): Long {
        val raw = value.get(key)
        check(raw is Int || raw is Long)
        return (raw as Number).toLong().also { check(it >= 0) }
    }
    fields(data, setOf("version", "story_id", "title", "root_branch", "branches"))
    check(count(data, "version") == 2L && text(data, "story_id") == root.story)
    check(text(data, "title") == root.title && text(data, "root_branch") == root.branch)
    check(timelineId.matches(root.story) && timelineId.matches(root.branch))
    val rows = data.get("branches") as? JSONArray ?: error("Wire")
    check(rows.length() in 1..256)
    val retiredBranches = mutableSetOf<String>()
    val timelines = (0 until rows.length()).map { index ->
        val row = rows.get(index) as? JSONObject ?: error("Wire")
        fields(row, setOf("scope", "parent_branch", "fork_revision", "revision", "drafts", "retired"))
        val itemScope = row.get("scope") as? JSONObject ?: error("Wire")
        fields(itemScope, setOf("story", "branch"))
        val story = text(itemScope, "story")
        val branch = text(itemScope, "branch")
        check(story == root.story && timelineId.matches(branch))
        val parent = if (row.isNull("parent_branch")) null else text(row, "parent_branch")
        check(parent == null || timelineId.matches(parent))
        val fork = if (row.isNull("fork_revision")) null else count(row, "fork_revision")
        val head = count(row, "revision")
        val drafts = count(row, "drafts")
        val retired = row.get("retired") as? Boolean ?: error("Wire")
        if (retired) {
            check(branch != root.branch && drafts == 0L)
            retiredBranches.add(branch)
        }
        check(drafts <= 4096 && (parent == null) == (fork == null))
        check((branch == root.branch) == (parent == null) && (fork == null || fork <= head))
        SavedTimeline(story, branch, parent, fork, head, drafts.toInt())
    }
    check(timelines.zipWithNext().all { (left, right) -> left.branch < right.branch })
    val byBranch = timelines.associateBy { it.branch }
    check(byBranch[root.branch]?.revision == root.revision)
    for (timeline in timelines) {
        var cursor = timeline
        val seen = mutableSetOf<String>()
        while (true) {
            check(seen.add(cursor.branch) && seen.size <= 32)
            val parent = cursor.parentBranch ?: break
            val ancestor = byBranch[parent] ?: error("Wire")
            check(checkNotNull(cursor.forkRevision) <= ancestor.revision)
            cursor = ancestor
        }
    }
    java.util.Collections.unmodifiableList(timelines.filter { it.branch !in retiredBranches })
} catch (_: Exception) {
    throw WorkspaceFailure("Malformed")
}
private fun sameScope(left: JSONObject, right: JSONObject) =
    left.getString("story") == right.getString("story") && left.getString("branch") == right.getString("branch")
private fun sameJson(left: Any?, right: Any?): Boolean = when {
    left is JSONObject && right is JSONObject -> {
        val keys = left.keys().asSequence().toSet()
        keys == right.keys().asSequence().toSet() && keys.all { sameJson(left.get(it), right.get(it)) }
    }
    left is JSONArray && right is JSONArray -> left.length() == right.length() &&
        (0 until left.length()).all { sameJson(left.get(it), right.get(it)) }
    left is Number && right is Number -> left.toString() == right.toString()
    else -> left == right
}

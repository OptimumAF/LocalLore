/* Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0 */
package org.locallore.app

import com.google.ai.edge.litertlm.Backend
import com.google.ai.edge.litertlm.Content
import com.google.ai.edge.litertlm.ConversationConfig
import com.google.ai.edge.litertlm.Engine
import com.google.ai.edge.litertlm.EngineConfig
import com.google.ai.edge.litertlm.Message
import com.google.ai.edge.litertlm.MessageCallback
import com.google.ai.edge.litertlm.LiteRtLmJniException
import com.google.ai.edge.litertlm.ResponseFormat
import com.google.ai.edge.litertlm.Role
import com.google.ai.edge.litertlm.SamplerConfig
import com.google.ai.edge.litertlm.ThinkingConfig
import java.io.ByteArrayOutputStream
import java.io.File
import java.security.MessageDigest
import java.util.concurrent.CancellationException
import kotlinx.coroutines.CoroutineScope
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.SupervisorJob
import kotlinx.coroutines.delay
import kotlinx.coroutines.launch
import kotlinx.coroutines.withContext

/** Trusted application configuration, never populated from a model response or player text. */
internal data class LiteRtWorkerConfig(
    val root: File,
    val model: File,
    val cache: File,
    val expectedModelBytes: Long,
    val modelSha256: String,
    val templateSha256: String,
    val workerSha256: String,
    val profileManifestSha256: String,
    val contextTokens: Int = 4096,
    val directorTokens: Int = 350,
    val narratorTokens: Int = 220,
    val deadlineMs: Long = 60_000,
    val repairLimit: Int = 1,
    val storageAdmission: () -> Unit = {},
) {
    init {
        require(expectedModelBytes > 0)
        listOf(modelSha256, templateSha256, workerSha256, profileManifestSha256).forEach {
            require(it.matches(Regex("[0-9a-f]{64}")))
        }
        require(contextTokens in 512..4096 && directorTokens in 1..350 && narratorTokens in 1..350)
        require(deadlineMs in 1..60_000 && repairLimit in 0..1)
    }

    /** Pair provenance and worker budgets; callers cannot supply a different native profile. */
    fun createOwner(
        limits: LocalInferenceLimits = LocalInferenceLimits(turnMs = deadlineMs),
        resources: LiteRtResources? = null,
        trace: LiteRtWorkerTrace? = null,
        sendTrace: LiteRtSendTrace? = null,
        callbackTrace: LiteRtCallbackTrace? = null,
        statusTrace: LiteRtStatusTrace? = null,
    ): LocalInferenceOwner {
        require(limits.turnMs == deadlineMs)
        lateinit var owner: LocalInferenceOwner
        val worker = LiteRtRoleWorker(this, resources ?: SdkLiteRtResources(sendTrace, statusTrace), trace, callbackTrace) { owner.close() }
        owner = LocalInferenceOwner(profileBytes(), worker, limits = limits)
        return owner
    }

    internal fun profileBytes(): ByteArray = localUtf8(
        """{"id":"android-litert-play-probe-v1","model_sha256":"$modelSha256","runtime_revision":"$LITERT_REVISION","template_sha256":"$templateSha256","worker_sha256":"$workerSha256","profile_manifest_sha256":"$profileManifestSha256","context_tokens":$contextTokens,"director_tokens":$directorTokens,"narrator_tokens":$narratorTokens,"deadline_ms":$deadlineMs,"repair_limit":$repairLimit}""",
    )

    internal fun validateRequest(request: LocalInferenceRequest) {
        request.validate()
        check(request.contextTokens == contextTokens && request.threads == 4)
        check(request.maxTokens <= if (request.role == "director") directorTokens else narratorTokens)
    }

    /** Runs on IO before SDK construction. Does not create directories, copy files or fall back. */
    internal fun admit(): LiteRtPaths {
        storageAdmission()
        val base = root.canonicalFile
        val weights = model.canonicalFile
        val scratch = cache.canonicalFile
        check(base.isDirectory && scratch.isDirectory && weights.isFile)
        check(weights.toPath().startsWith(base.toPath()) && scratch.toPath().startsWith(base.toPath()))
        check(scratch != base && weights.parentFile != null && weights != scratch)
        check(weights.length() == expectedModelBytes)
        val modified = weights.lastModified()
        val digest = MessageDigest.getInstance("SHA-256")
        weights.inputStream().use { input ->
            val buffer = ByteArray(64 * 1024)
            var count = 0L
            while (true) {
                val size = input.read(buffer)
                if (size < 0) break
                count += size
                check(count <= expectedModelBytes)
                digest.update(buffer, 0, size)
            }
            check(count == expectedModelBytes)
        }
        check(digest.digest().joinToString("") { "%02x".format(it) } == modelSha256)
        check(model.canonicalFile == weights && cache.canonicalFile == scratch && root.canonicalFile == base)
        check(weights.isFile && weights.length() == expectedModelBytes && weights.lastModified() == modified)
        storageAdmission()
        // Path-based SDK opening cannot authenticate hostile concurrent OS replacement after this read.
        return LiteRtPaths(weights.path, scratch.path, contextTokens)
    }
}

internal const val LITERT_REVISION = "bda624851d74be34d4e1f7fac1fc4155939539c7"
internal data class LiteRtPaths(val model: String, val cache: String, val contextTokens: Int)

/** SDK-neutral resource seam. Unit tests exercise lifecycle failures without loading a native model. */
internal fun interface LiteRtResources { fun engine(paths: LiteRtPaths): LiteRtEngineResource }
internal interface LiteRtEngineResource {
    fun initialize()
    fun conversation(request: LocalInferenceRequest): LiteRtConversationResource
    fun close(): Boolean
}
internal interface LiteRtConversationResource {
    fun send(request: LocalInferenceRequest, callbacks: LiteRtCallbacks)
    fun cancel()
    fun close(): Boolean
}
internal interface LiteRtCallbacks {
    /** Lazy mapping places SDK-visible message inspection inside the counted callback body. */
    fun message(read: () -> LiteRtChunk)
    fun done()
    fun error(cancelled: Boolean)
    /** Passive closed provenance only, after the original error path has fenced the owner. */
    fun errorCategory(category: LiteRtCallbackError) {}
}
internal data class LiteRtChunk(
    val modelRole: Boolean = true,
    val text: List<String> = emptyList(),
    val nonText: Boolean = false,
    val channels: Boolean = false,
    val tools: Boolean = false,
)

/**
 * Opt-in SDK 0.18.1 worker. Every turn gets a new engine; every role a new conversation.
 * Proofs here mean the public SDK terminal/body-drain/returned-close contract. They do not prove
 * JNI callback epilogues or hidden native waits whose status the SDK discards. Real active-model
 * ownership qualification is a separate gate. Unknown resources are retained, never parent-closed.
 */
internal class LiteRtRoleWorker(
    private val config: LiteRtWorkerConfig,
    private val resources: LiteRtResources = SdkLiteRtResources(),
    private val trace: LiteRtWorkerTrace? = null,
    private val callbackTrace: LiteRtCallbackTrace? = null,
    private val onUncertain: () -> Unit = {},
) : LocalRoleWorker {
    private val lock = Any()
    private val retained = mutableListOf<Any>()
    private var active: OwnedEngine? = null
    private var opening = false
    private var poisoned = false

    override suspend fun open(): LocalRoleEngine = withContext(Dispatchers.IO) {
        synchronized(lock) { check(!poisoned && !opening && active == null); opening = true }
        try {
            trace?.record(LiteRtWorkerEvent.ADMISSION_ENTERED)
            val paths = config.admit()
            trace?.record(LiteRtWorkerEvent.ADMISSION_RETURNED)
            trace?.record(LiteRtWorkerEvent.ENGINE_CREATE_ENTERED)
            val resource = resources.engine(paths)
            trace?.record(LiteRtWorkerEvent.ENGINE_CREATE_RETURNED)
            synchronized(lock) { retained += resource }
            trace?.record(LiteRtWorkerEvent.INITIALIZE_ADMISSION_ENTERED)
            config.storageAdmission()
            trace?.record(LiteRtWorkerEvent.INITIALIZE_ADMISSION_RETURNED)
            trace?.record(LiteRtWorkerEvent.INITIALIZE_ENTERED)
            resource.initialize() // Blocking initialization is not made interruptible by coroutine cancellation.
            trace?.record(LiteRtWorkerEvent.INITIALIZE_RETURNED)
            OwnedEngine(resource).also { synchronized(lock) { check(!poisoned); active = it } }
        } catch (_: Throwable) {
            unknown()
            throw LocalInferenceUncertain()
        } finally { synchronized(lock) { opening = false } }
    }

    private fun markUnknown() = synchronized(lock) { poisoned = true }
    private fun notifyUnknown() {
        // Factory hook synchronously fences the SAME owner. Its eventual native close is a separate
        // observation; scheduling close never establishes resource reclamation or rolls back history.
        if (synchronized(lock) { poisoned }) {
            try { onUncertain() } catch (_: Throwable) { }
            trace?.record(LiteRtWorkerEvent.UNCERTAIN)
        }
    }
    private fun unknown() { markUnknown(); notifyUnknown() }

    private inner class OwnedEngine(private val resource: LiteRtEngineResource) : LocalRoleEngine {
        private val roles = mutableListOf<OwnedCall>()
        private var starting = false
        private var startUnknown = false
        private var closing = false
        private var closed = false
        override suspend fun start(request: LocalInferenceRequest): LocalRoleCall = withContext(Dispatchers.IO) {
            var creationOrdinal = 0
            var creationReturned = false
            try {
                config.validateRequest(request)
                synchronized(lock) {
                    check(!poisoned && !closing && !closed && !starting && roles.all { it.closedKnown })
                    starting = true
                }
                trace?.record(LiteRtWorkerEvent.ROLE_ADMISSION_ENTERED)
                config.storageAdmission()
                trace?.record(LiteRtWorkerEvent.ROLE_ADMISSION_RETURNED)
                trace?.record(LiteRtWorkerEvent.CONVERSATION_CREATE_ENTERED)
                // Configured byte lengths are not tokenizer usage. Diagnostics cannot change admission.
                val observation = try { callbackTrace?.begin(
                    if (request.role == "director") LiteRtCallbackRole.DIRECTOR else LiteRtCallbackRole.NARRATOR,
                    request.contextTokens, request.maxTokens, localUtf8(request.prompt).size, localUtf8(request.schemaJson).size,
                ) } catch (_: Throwable) { null }
                // Request validation above admits only these two closed roles. No prompt/schema
                // or exception string enters the passive observation.
                creationOrdinal = trace?.creationEntered(when (request.role) {
                    "director" -> LiteRtTraceRole.DIRECTOR
                    else -> LiteRtTraceRole.NARRATOR
                }) ?: 0
                val conversation = resource.conversation(request)
                val call = OwnedCall(conversation, observation)
                synchronized(lock) { roles += call }
                // Retain the returned resource before doing diagnostic work.
                creationReturned = true
                trace?.creationReturned(creationOrdinal)
                trace?.record(LiteRtWorkerEvent.CONVERSATION_CREATE_RETURNED)
                try {
                    trace?.record(LiteRtWorkerEvent.SEND_ADMISSION_ENTERED)
                    config.storageAdmission()
                    trace?.record(LiteRtWorkerEvent.SEND_ADMISSION_RETURNED)
                    trace?.record(LiteRtWorkerEvent.SEND_ENTERED)
                    conversation.send(request, call)
                    trace?.record(LiteRtWorkerEvent.SEND_RETURNED)
                }
                catch (_: Throwable) { call.failedStart(); throw LocalInferenceUncertain() }
                call.started()
                call
            } catch (failure: Throwable) {
                synchronized(lock) { startUnknown = true }
                unknown()
                if (!creationReturned) trace?.creationFailed(creationOrdinal,
                    if (failure is CancellationException) LiteRtTraceFailure.CANCELLED else LiteRtTraceFailure.OTHER)
                throw LocalInferenceUncertain()
            } finally { synchronized(lock) { starting = false } }
        }

        override suspend fun close(): Boolean = withContext(Dispatchers.IO) {
            synchronized(lock) {
                if (closed) return@withContext !poisoned
                if (poisoned || closing || starting || startUnknown || roles.any { !it.closedKnown }) return@withContext false
                closing = true
            }
            trace?.record(LiteRtWorkerEvent.ENGINE_CLOSE_ENTERED)
            val known = try { resource.close() } catch (_: Throwable) { false }
            val result = synchronized(lock) {
                if (known && !poisoned && roles.all { it.closedKnown }) { closed = true; retained.remove(resource); active = null }
                else poisoned = true
                closed && !poisoned
            }
            if (result) trace?.record(LiteRtWorkerEvent.ENGINE_CLOSE_KNOWN)
            if (!result) notifyUnknown()
            result
        }
    }

    private inner class OwnedCall(
        private val resource: LiteRtConversationResource,
        private val observation: LiteRtCallbackCall?,
    ) : LocalRoleCall, LiteRtCallbacks {
        private val state = Any()
        private val cancelScope = CoroutineScope(SupervisorJob() + Dispatchers.IO)
        private val bytes = ByteArrayOutputStream()
        private var callbacks = 0
        private var terminal = false
        private var cancelled = false
        private var cancelRequested = false
        private var cancelRunning = false
        private var startReturned = false
        private var failed = false
        private var closing = false
        @Volatile var closedKnown = false
            private set

        private fun fail() { failed = true; closedKnown = false; markUnknown() }
        fun started() = synchronized(state) { startReturned = true }
        fun failedStart() { synchronized(state) { fail() }; notifyUnknown() }

        private fun callback(entered: LiteRtWorkerEvent, returned: LiteRtWorkerEvent, body: () -> Unit) {
            synchronized(state) { callbacks++; if (closedKnown || closing) fail() }
            trace?.record(entered)
            try { body() }
            catch (_: Throwable) { synchronized(state) { fail() } }
            finally {
                synchronized(state) { callbacks-- }; notifyUnknown()
                // Observed callback body exit, never a claim about hidden JNI epilogues.
                trace?.record(returned)
            }
        }

        override fun message(read: () -> LiteRtChunk) = callback(LiteRtWorkerEvent.MESSAGE_ENTERED, LiteRtWorkerEvent.MESSAGE_RETURNED) {
            synchronized(state) { if (terminal || failed) { fail(); return@callback } }
            val chunk = read()
            synchronized(state) {
                val before = bytes.size()
                check(chunk.modelRole && !chunk.nonText && !chunk.channels && !chunk.tools)
                chunk.text.forEach {
                    check(it.length <= 16_384)
                    val value = localUtf8(it)
                    check(bytes.size() + value.size <= 16_384)
                    bytes.write(value)
                }
                val text = localText(bytes.toByteArray(), 16_384)
                check(!text.contains("<think>", ignoreCase = true) && !text.contains("</think>", ignoreCase = true))
                // Only bytes that passed the original chunk/buffer checks, not SDK tokens or all callbacks.
                try { observation?.output(bytes.size() - before) } catch (_: Throwable) { }
            }
        }

        override fun done() {
            callback(LiteRtWorkerEvent.DONE_ENTERED, LiteRtWorkerEvent.DONE_RETURNED) { synchronized(state) {
                if (terminal) fail()
                terminal = true
            } }
            try { observation?.done() } catch (_: Throwable) { }
        }

        override fun error(cancelled: Boolean) = callback(LiteRtWorkerEvent.ERROR_ENTERED, LiteRtWorkerEvent.ERROR_RETURNED) { synchronized(state) {
            if (terminal) fail()
            terminal = true
            if (cancelled && cancelRequested) this.cancelled = true else fail()
        } }

        override fun errorCategory(category: LiteRtCallbackError) {
            try { observation?.error(category) } catch (_: Throwable) { }
        }

        private fun settled(): Boolean = terminal && callbacks == 0 && startReturned && !cancelRunning

        override suspend fun await(): LocalRoleResult = withContext(Dispatchers.IO) {
            while (true) {
                synchronized(state) {
                    if (failed) throw LocalInferenceUncertain()
                    if (settled()) return@withContext LocalRoleResult(true, if (cancelled || cancelRequested) byteArrayOf() else bytes.toByteArray())
                }
                delay(2)
            }
            @Suppress("UNREACHABLE_CODE")
            throw LocalInferenceUncertain()
        }

        /** Scheduling is nonblocking; drain includes the independently owned cancellation operation. */
        override fun cancel() {
            synchronized(state) {
                if (cancelRequested || closedKnown || closing) return
                cancelRequested = true
                cancelRunning = true
            }
            cancelScope.launch {
                try {
                    trace?.record(LiteRtWorkerEvent.CANCEL_ENTERED)
                    resource.cancel()
                    trace?.record(LiteRtWorkerEvent.CANCEL_RETURNED)
                }
                catch (_: Throwable) { synchronized(state) { fail() } }
                finally { synchronized(state) { cancelRunning = false }; notifyUnknown() }
            }
        }

        override suspend fun drain(): Boolean = withContext(Dispatchers.IO) {
            while (true) {
                synchronized(state) {
                    if (failed) return@withContext false
                    if (settled()) {
                        trace?.record(LiteRtWorkerEvent.DRAIN_SETTLED)
                        return@withContext true
                    }
                }
                delay(2)
            }
            @Suppress("UNREACHABLE_CODE")
            false
        }

        override suspend fun close(): Boolean = withContext(Dispatchers.IO) {
            synchronized(state) {
                if (closedKnown) return@withContext !failed
                if (closing || failed || !settled()) return@withContext false
                closing = true
            }
            trace?.record(LiteRtWorkerEvent.CONVERSATION_CLOSE_ENTERED)
            val known = try { resource.close() } catch (_: Throwable) { false }
            val result = synchronized(state) {
                // A callback concurrent with close remains uncertainty even if SDK close returns.
                if (known && !failed && callbacks == 0) closedKnown = true else fail()
                closedKnown
            }
            if (result) trace?.record(LiteRtWorkerEvent.CONVERSATION_CLOSE_KNOWN)
            if (!result) notifyUnknown()
            result
        }
    }
}

/** All application arguments are constructed before the observed public SDK call site. */
private data class SdkSendArguments(
    val prompt: String,
    val callback: MessageCallback,
    val maxOutputToken: Int,
    val thinkingConfig: ThinkingConfig,
    val responseFormat: ResponseFormat,
)

/** The default path calls the pinned SDK; resource tests need no native library or model. */
private class SdkLiteRtResources(
    private val sendTrace: LiteRtSendTrace? = null,
    private val statusTrace: LiteRtStatusTrace? = null,
) : LiteRtResources {
    override fun engine(paths: LiteRtPaths): LiteRtEngineResource {
        val engine = Engine(EngineConfig(
            modelPath = paths.model, backend = Backend.CPU(threadCount = 4),
            maxNumTokens = paths.contextTokens, cacheDir = paths.cache,
        ))
        return object : LiteRtEngineResource {
            override fun initialize() = engine.initialize()
            override fun close(): Boolean { engine.close(); return true }
            override fun conversation(request: LocalInferenceRequest): LiteRtConversationResource {
                val conversation = engine.createConversation(ConversationConfig(
                    tools = emptyList(), automaticToolCalling = false, channels = emptyList(),
                    samplerConfig = SamplerConfig(topK = 1, topP = 1.0, temperature = 0.0, seed = 1),
                    maxOutputToken = request.maxTokens, thinkingConfig = ThinkingConfig(false, 0),
                    enableResponseFormat = true, enableSpeculativeDecoding = false,
                ))
                return object : LiteRtConversationResource {
                    override fun send(request: LocalInferenceRequest, callbacks: LiteRtCallbacks) {
                        observedLiteRtSend(sendTrace, prepare = {
                            SdkSendArguments(request.prompt, object : MessageCallback {
                                override fun onMessage(message: Message) = callbacks.message {
                                    // SDK-private jsonToMessage normalizes raw roles and drops unknown raw
                                    // content kinds. Only SDK-exposed fields can be checked here.
                                    LiteRtChunk(
                                        modelRole = message.role == Role.MODEL,
                                        text = message.contents.contents.filterIsInstance<Content.Text>().map { it.text },
                                        nonText = message.contents.contents.any { it !is Content.Text },
                                        channels = message.channels.isNotEmpty(), tools = message.toolCalls.isNotEmpty(),
                                    )
                                }
                                override fun onDone() = callbacks.done()
                                override fun onError(throwable: Throwable) = observedLiteRtError(throwable, callbacks, statusTrace)
                            }, request.maxTokens, ThinkingConfig(false, 0), ResponseFormat.json(request.schemaJson))
                        }, dispatch = { arguments ->
                            // This is the public Kotlin call site, not an SDK body/JNI/native-entry
                            // observation. All application argument construction is complete above.
                            conversation.sendMessageAsync(
                                arguments.prompt, arguments.callback, maxOutputToken = arguments.maxOutputToken,
                                thinkingConfig = arguments.thinkingConfig, responseFormat = arguments.responseFormat,
                            )
                        })
                    }
                    override fun cancel() = conversation.cancelProcess()
                    override fun close(): Boolean { conversation.close(); return true }
                }
            }
        }
    }
}

/** Type identity only; no message, class name, stack, cause or hidden numeric status is read. */
internal fun liteRtCallbackError(throwable: Throwable): LiteRtCallbackError = when (throwable) {
    is CancellationException -> LiteRtCallbackError.CANCELLED
    is LiteRtLmJniException -> LiteRtCallbackError.SDK_JNI
    else -> LiteRtCallbackError.OTHER
}

/** Keep fencing first and preserve any original callback failure over diagnostic failures. */
internal fun observedLiteRtError(throwable: Throwable, callbacks: LiteRtCallbacks, statusTrace: LiteRtStatusTrace? = null) {
    try { callbacks.error(throwable is CancellationException) }
    finally {
        try { callbacks.errorCategory(liteRtCallbackError(throwable)) } catch (_: Throwable) { }
        // Default/regular owners do not retrieve exception text. The optional receipt trace
        // sees only a closed pinned-wrapper prefix result after the original fence.
        if (statusTrace != null) {
            try { statusTrace.record(liteRtDeclaredStatus(throwable)) } catch (_: Throwable) { }
        }
    }
}

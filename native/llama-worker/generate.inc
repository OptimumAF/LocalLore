// Adapted from the accepted experiment and pinned llama.cpp MIT API examples. See NOTICE.
static json generate(llama_model * model, const json & req, GenerationLimits limits) {
    const auto operation_start=clock_type::now();
    checkpoint();
    const auto vocab = llama_model_get_vocab(model);
    auto templates = common_chat_templates_init(model, "");
    if (!common_chat_templates_was_explicit(templates.get()) ||
        !common_chat_templates_support_enable_thinking(templates.get())) throw failure("unsupported_template");
    common_chat_templates_inputs inputs;
    common_chat_msg user;
    user.role = "user";
    user.content = req["prompt"].get<std::string>();
    inputs.messages.push_back(user);
    inputs.use_jinja = true;
    inputs.enable_thinking = false;
    inputs.chat_template_kwargs["enable_thinking"] = "false";
    inputs.chat_template_kwargs["preserve_reasoning"] = "false";
    inputs.tool_choice = COMMON_CHAT_TOOL_CHOICE_NONE;
    inputs.parallel_tool_calls = false;
    inputs.force_pure_content = true;
    // Both template schema formatting and grammar compilation consume the same
    // insertion-ordered schema; never reserialize it through the sorted transport map.
    const auto ordered_schema=locallore_ordered_schema(req["schema"]);
    if (!req["schema"].is_null()) inputs.json_schema = ordered_schema.dump();
    common_chat_session chat(templates.get(), vocab, inputs);
    // The official template tracks input parts; user text cannot create role tokens.
    std::vector<llama_token> tokens;
    bool first = true;
    for (const auto & part : chat.prompt().parts) {
        auto next = common_tokenize(vocab, part.text, first && llama_vocab_get_add_bos(vocab), !part.is_input);
        tokens.insert(tokens.end(), next.begin(), next.end());
        first = false;
    }
    const int max_tokens = limits.output_tokens;
    if (tokens.empty() || tokens.size() + max_tokens > 4096) throw failure("context_limit");
    auto cp = llama_context_default_params();
    cp.n_ctx = 4096;
    cp.n_batch = 512;
    cp.n_ubatch = 512;
    cp.n_threads = 4;
    cp.n_threads_batch = 4;
    cp.offload_kqv = false;
    cp.op_offload = false;
    cp.no_perf = true;
    cp.abort_callback = [](void *) { const bool stop=interrupted(); if(stop) ++abort_callbacks; return stop; };
    using context_ptr = std::unique_ptr<llama_context, decltype(&llama_free)>;
    context_ptr ctx(llama_init_from_model(model, cp), llama_free);
    if (!ctx) throw failure("context_failed");
    common_params_sampling sp;
    sp.seed = 42;
    sp.temp = 0.7f;
    sp.top_p = 0.8f;
    sp.top_k = 20;
    sp.min_p = 0;
    sp.penalty_present = 1.5f;
    sp.no_perf = true;
    chat.apply_sampling(sp);
    if (!req["schema"].is_null()) {
        // Pure-content chat formatting does not necessarily install its schema.
        // Apply the official converter explicitly; generated JSON starts at root.
        sp.grammar = {COMMON_GRAMMAR_TYPE_USER,
            json_schema_to_grammar(ordered_schema)};
        sp.grammar_lazy = false;
        sp.generation_prompt.clear();
    }
    using sampler_ptr = std::unique_ptr<common_sampler, decltype(&common_sampler_free)>;
    sampler_ptr sampler(common_sampler_init(model, sp), common_sampler_free);
    if (!sampler) throw failure("sampling_failed");
    using batch_ptr = std::unique_ptr<llama_batch_ext, decltype(&llama_batch_ext_free)>;
    batch_ptr batch(llama_batch_ext_init(ctx.get()), llama_batch_ext_free);
    if (!batch) throw failure("context_failed");
    json result = response(nullptr);
    result["metrics"]["contexts_created"] = ++contexts_created;
    result["metrics"]["model_loads"] = model_loads.load();
    result["metrics"]["input_tokens"] = tokens.size();
    const auto generation_start = clock_type::now();
    auto decode = [&](const llama_token * values, int count, int pos) {
        llama_batch_ext_clear(batch.get());
        for (int i = 0; i < count; ++i) {
            const int index = llama_batch_ext_add_token(batch.get(), 0, values[i]);
            const llama_pos position = pos + i;
            if (!llama_batch_ext_set_pos(batch.get(), index, &position)) throw failure("decode_failed");
        }
        llama_batch_ext_set_output_logits(batch.get(), count - 1, true);
        checkpoint();
        if (llama_process(ctx.get(), LLAMA_PROCESS_TYPE_DECODE, batch.get()) != 0) { checkpoint(); throw failure("decode_failed"); }
    };
    for (int pos = 0; pos < static_cast<int>(tokens.size()); pos += 512) {
        decode(tokens.data() + pos, std::min(512, static_cast<int>(tokens.size()) - pos), pos);
    }
    result["metrics"]["prefill_ms"] = elapsed(generation_start);
    const auto decode_start = clock_type::now();
    for (const auto token : tokens) common_sampler_accept(sampler.get(), token, false);
    common_chat_input generated;
    int output_tokens = 0;
    for (; output_tokens < max_tokens; ++output_tokens) {
        checkpoint();
        const auto token = common_sampler_sample(sampler.get(), ctx.get(), -1);
        common_sampler_accept(sampler.get(), token, true);
        if (llama_vocab_is_eog(vocab, token)) break;
        generated.append(common_token_to_piece(vocab, token, true), token);
        if (generated.size() > limits.text_bytes) throw failure("output_limit");
        decode(&token, 1, static_cast<int>(tokens.size()) + output_tokens);
    }
    const auto & final = chat.finish(generated);
    // Do not retain or expose reasoning, tool calls, or partly parsed role output.
    if (!final.reasoning_content.empty() || !final.tool_calls.empty() || final.content.size() > limits.text_bytes ||
        final.content.find("<think>") != std::string::npos || final.content.find("</think>") != std::string::npos)
        throw failure("unexpected_output");
    result["text"] = final.content;
    result["metrics"]["output_tokens"] = output_tokens;
    result["metrics"]["decode_ms"] = elapsed(decode_start);
    result["metrics"]["total_ms"] = elapsed(operation_start);
    checkpoint();
    return result;
}

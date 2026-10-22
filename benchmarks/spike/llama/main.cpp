// Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0
// Bounded host experiment using the pinned official simple/chat/sampling APIs.
// Batch/decode pattern adapted from llama.cpp examples/simple (MIT); see NOTICE.
#include "chat.h"
#include "common.h"
#include "log.h"
#include "json-schema-to-grammar.h"
#include "sampling.h"
#include "llama.h"
#include "nlohmann/json.hpp"
#include <chrono>
#include <iostream>
#include <memory>
#include <set>
#include <stdexcept>
#include <string>
#include <vector>

using json = nlohmann::json;
using clock_type = std::chrono::steady_clock;
struct failure : std::runtime_error { using std::runtime_error::runtime_error; };
struct backend { backend() { llama_backend_init(); } ~backend() { llama_backend_free(); } };
static double elapsed(clock_type::time_point start) {
    return std::chrono::duration<double, std::milli>(clock_type::now() - start).count();
}
static json response(const char * error) {
    return {{"version",1},{"status",error ? "error" : "completed"},{"text",""},
        {"error",error ? json(error) : json(nullptr)},{"load_ms",nullptr},
        {"generation_ms",nullptr},{"output_tokens",nullptr},{"input_tokens",nullptr},
        {"schema_enforced",false},{"thinking_disabled",false},{"template_applied",false}};
}
static json read_request() {
    std::string raw;
    char c;
    while (std::cin.get(c)) {
        if (raw.size() == 32768) throw failure("invalid_request");
        raw.push_back(c);
    }
    auto req = json::parse(raw);
    const std::set<std::string> keys = {"version","role","prompt","max_tokens","context_tokens","threads","schema"};
    if (!req.is_object() || req.size() != keys.size()) throw failure("invalid_request");
    for (const auto & key : keys) if (!req.contains(key)) throw failure("invalid_request");
    for (const auto & key : {"version","max_tokens","context_tokens","threads"})
        if (!req[key].is_number_integer() || req[key].is_boolean()) throw failure("invalid_request");
    if (req["version"] != 1 || req["context_tokens"] != 4096 || req["threads"] != 4 ||
        !req["role"].is_string() || (req["role"] != "director" && req["role"] != "narrator") ||
        !req["prompt"].is_string() || req["prompt"].get<std::string>().empty() ||
        req["max_tokens"].get<int>() < 1 || req["max_tokens"].get<int>() > 350 ||
        (!req["schema"].is_null() && !req["schema"].is_object())) throw failure("invalid_request");
    return req;
}
static json run(const char * model_path, const json & req) {
    backend backend_lifetime;
    const auto load_start = clock_type::now();
    auto mp = llama_model_default_params();
    mp.n_gpu_layers = 0;
    using model_ptr = std::unique_ptr<llama_model, decltype(&llama_model_free)>;
    model_ptr model(llama_model_load_from_file(model_path, mp), llama_model_free);
    if (!model) throw failure("model_load_failed");
    const auto vocab = llama_model_get_vocab(model.get());
    auto templates = common_chat_templates_init(model.get(), "");
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
    if (!req["schema"].is_null()) inputs.json_schema = req["schema"].dump();
    common_chat_session chat(templates.get(), vocab, inputs);
    // The official template tracks input parts; user text cannot create role tokens.
    std::vector<llama_token> tokens;
    bool first = true;
    for (const auto & part : chat.prompt().parts) {
        auto next = common_tokenize(vocab, part.text, first && llama_vocab_get_add_bos(vocab), !part.is_input);
        tokens.insert(tokens.end(), next.begin(), next.end());
        first = false;
    }
    const int max_tokens = req["max_tokens"].get<int>();
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
    using context_ptr = std::unique_ptr<llama_context, decltype(&llama_free)>;
    context_ptr ctx(llama_init_from_model(model.get(), cp), llama_free);
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
            json_schema_to_grammar(common_json::parse(req["schema"].dump()))};
        sp.grammar_lazy = false;
        sp.generation_prompt.clear();
    }
    using sampler_ptr = std::unique_ptr<common_sampler, decltype(&common_sampler_free)>;
    sampler_ptr sampler(common_sampler_init(model.get(), sp), common_sampler_free);
    if (!sampler) throw failure("sampling_failed");
    using batch_ptr = std::unique_ptr<llama_batch_ext, decltype(&llama_batch_ext_free)>;
    batch_ptr batch(llama_batch_ext_init(ctx.get()), llama_batch_ext_free);
    if (!batch) throw failure("context_failed");
    json result = response(nullptr);
    result["load_ms"] = elapsed(load_start);
    result["input_tokens"] = tokens.size();
    result["schema_enforced"] = !req["schema"].is_null() && !sp.grammar.empty();
    result["thinking_disabled"] = true;
    result["template_applied"] = true;
    const auto generation_start = clock_type::now();
    auto decode = [&](const llama_token * values, int count, int pos) {
        llama_batch_ext_clear(batch.get());
        for (int i = 0; i < count; ++i) {
            const int index = llama_batch_ext_add_token(batch.get(), 0, values[i]);
            const llama_pos position = pos + i;
            if (!llama_batch_ext_set_pos(batch.get(), index, &position)) throw failure("decode_failed");
        }
        llama_batch_ext_set_output_logits(batch.get(), count - 1, true);
        if (llama_process(ctx.get(), LLAMA_PROCESS_TYPE_DECODE, batch.get()) != 0) throw failure("decode_failed");
    };
    for (int pos = 0; pos < static_cast<int>(tokens.size()); pos += 512) {
        decode(tokens.data() + pos, std::min(512, static_cast<int>(tokens.size()) - pos), pos);
    }
    for (const auto token : tokens) common_sampler_accept(sampler.get(), token, false);
    common_chat_input generated;
    int output_tokens = 0;
    for (; output_tokens < max_tokens; ++output_tokens) {
        const auto token = common_sampler_sample(sampler.get(), ctx.get(), -1);
        common_sampler_accept(sampler.get(), token, true);
        if (llama_vocab_is_eog(vocab, token)) break;
        generated.append(common_token_to_piece(vocab, token, true), token);
        if (generated.size() > 16384) throw failure("output_limit");
        decode(&token, 1, static_cast<int>(tokens.size()) + output_tokens);
    }
    const auto & final = chat.finish(generated);
    // Do not retain or expose reasoning, tool calls, or partly parsed role output.
    if (!final.reasoning_content.empty() || !final.tool_calls.empty() || final.content.size() > 16384 ||
        final.content.find("<think>") != std::string::npos || final.content.find("</think>") != std::string::npos)
        throw failure("unexpected_output");
    result["text"] = final.content;
    result["output_tokens"] = output_tokens;
    result["generation_ms"] = elapsed(generation_start);
    return result;
}
int main(int argc, char ** argv) {
    // No downloader, argument parser, server, prompt cache, or raw text logger.
    common_log_pause(common_log_main());
    llama_log_set([](ggml_log_level, const char *, void *) {}, nullptr);
    json result;
    try {
        if (argc != 3 || std::string(argv[1]) != "--model") throw failure("invalid_request");
        result = run(argv[2], read_request());
    } catch (const failure & e) { result = response(e.what()); }
      catch (...) { result = response("runtime_failed"); }
    std::cout << result.dump(-1, ' ', false, json::error_handler_t::replace) << '\n';
    return result["status"] == "completed" ? 0 : 1;
}

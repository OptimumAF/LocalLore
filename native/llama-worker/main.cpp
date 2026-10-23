// Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0
#include "chat.h"
#include "common.h"
#include "log.h"
#include "json-schema-to-grammar.h"
#include "sampling.h"
#include "llama.h"
#include "nlohmann/json.hpp"
#include "schema_order.h"
#include "worker_launch.h"
#include <atomic>
#include <chrono>
#include <iostream>
#include <memory>
#include <mutex>
#include <set>
#include <stdexcept>
#include <string>
#include <thread>
#include <vector>
#ifdef _WIN32
#define NOMINMAX
#include <windows.h>
#endif
using json = nlohmann::json;
using clock_type = std::chrono::steady_clock;
struct failure : std::runtime_error { using std::runtime_error::runtime_error; };
static std::atomic<bool> cancelled{false};
static std::atomic<bool> busy{false};
static clock_type::time_point deadline;
static std::atomic<uint32_t> model_loads{0}, contexts_created{0};
static std::atomic<uint32_t> abort_callbacks{0};
static std::mutex output_lock;
static bool interrupted() { return cancelled.load() || clock_type::now() >= deadline; }
static void checkpoint() { if (interrupted()) throw failure("cancelled"); }
static double elapsed(clock_type::time_point start) { return std::chrono::duration<double,std::milli>(clock_type::now()-start).count(); }
static json response(const char * error) {
    return {{"version",1},{"id",0},{"status",error ? "error" : "completed"},{"error",error ? json(error) : json(nullptr)},
        {"text",""},{"metrics",{{"load_ms",0},{"prefill_ms",0},{"decode_ms",0},{"total_ms",0},{"input_tokens",0},{"output_tokens",0},{"model_loads",model_loads.load()},{"contexts_created",contexts_created.load()},{"abort_callbacks",abort_callbacks.load()}}}};
}
static void publish(json result, uint64_t id) {
    result["id"] = id;
    std::lock_guard<std::mutex> lock(output_lock);
    std::cout << result.dump() << '\n' << std::flush;
}
// Reject duplicate keys independently of the trusted parent parser.
static json parse(const std::string & raw) {
    std::vector<std::set<std::string>> objects;
    return json::parse(raw, [&](int, json::parse_event_t event, json & value) {
        if (event == json::parse_event_t::object_start) objects.emplace_back();
        if (event == json::parse_event_t::key && !objects.back().insert(value.get<std::string>()).second) throw failure("invalid_request");
        if (event == json::parse_event_t::object_end) objects.pop_back();
        return true;
    });
}
#include "generate.inc"

static int worker(const std::string & model_path) {
    common_log_pause(common_log_main());
    llama_log_set([](ggml_log_level,const char *,void *){},nullptr);
    llama_backend_init();
    using model_ptr = std::unique_ptr<llama_model, decltype(&llama_model_free)>;
    model_ptr model(nullptr,llama_model_free);
    std::thread work;
    uint64_t last = 0, active = 0;
    std::string raw;
    char byte;
    while (std::cin.get(byte)) {
        if (byte != '\n') {
            if (raw.size() >= 32768) break;
            raw.push_back(byte); continue;
        }
        uint64_t id = 0;
        try {
            const auto req = parse(raw); raw.clear();
            if (!req.is_object() || !req.contains("version") || req["version"] != 1 || !req.contains("id") || !req["id"].is_number_unsigned() || !req.contains("op") || !req["op"].is_string()) throw failure("invalid_request");
            id = req["id"].get<uint64_t>();
            const auto op = req["op"].get<std::string>();
            if (op == "cancel") {
                if (req.size()!=3 || id != active) throw failure("invalid_request");
                if (busy.load()) cancelled.store(true);
                continue; // Cancellation has one terminal original-operation reply, never an ack frame.
            }
            if (busy.load()) throw failure("busy");
            if (work.joinable()) work.join();
            if (id <= last || id == 0 || req.size() != (op == "generate" ? 4 : 3)) throw failure("invalid_request");
            last = id; active = id;
            if (op == "shutdown") { publish(response(nullptr),id); break; }
            if (op == "unload") { model.reset(); publish(response(nullptr),id); continue; }
            if (op == "status") { publish(response(nullptr),id); continue; }
            if (op != "load" && op != "generate") throw failure("invalid_request");
            if (op == "generate") {
                if (!model) throw failure("model_load_failed");
                auto g = req["generation"];
                if (!g.is_object() || g.size()!=4 || !g.contains("role") || !g["role"].is_string() || (g["role"]!="director" && g["role"]!="narrator") || !g.contains("prompt") || !g["prompt"].is_string() || g["prompt"].get<std::string>().empty() || g["prompt"].get<std::string>().find('\0')!=std::string::npos || !g.contains("schema") || (!g["schema"].is_null() && !g["schema"].is_object()) || !g.contains("max_tokens") || !g["max_tokens"].is_number_unsigned() || g["max_tokens"]<1 || g["max_tokens"]>350) throw failure("invalid_request");
            }
            cancelled.store(false); deadline=clock_type::now()+std::chrono::seconds(60);
            if (!locallore_launch_work(work,busy,[&,req,id,op] {
                json result;
                try {
                    if (op=="load") {
                        if (model) throw failure("busy");
                        const auto started=clock_type::now();
                        auto mp=llama_model_default_params(); mp.n_gpu_layers=0;
                        mp.progress_callback=[](float,void *) { const bool stop=interrupted(); if(stop) ++abort_callbacks; return !stop; };
                        model.reset(llama_model_load_from_file(model_path.c_str(),mp));
                        checkpoint();
                        if (!model) throw failure("model_load_failed");
                        ++model_loads;
                        result=response(nullptr); result["metrics"]["load_ms"]=elapsed(started);
                        result["metrics"]["total_ms"]=elapsed(started);
                    } else result=generate(model.get(),req["generation"]);
                } catch (const failure & e) { result=response(e.what()); }
                  catch (...) { result=response("runtime_failed"); }
                // Publish only after per-call RAII contexts/samplers have been destroyed.
                busy.store(false); publish(result,id);
            })) publish(response("runtime_failed"),id);
        } catch (const failure & e) { publish(response(e.what()),id); }
          catch (...) { publish(response("invalid_request"),id); }
    }
    cancelled.store(true);
    if (work.joinable()) work.join();
    model.reset(); llama_backend_free();
    return 0;
}
#ifdef _WIN32
int wmain(int argc,wchar_t **argv) {
    if (argc!=3 || std::wstring(argv[1])!=L"--model") return 2;
    const int count=WideCharToMultiByte(CP_UTF8,WC_ERR_INVALID_CHARS,argv[2],-1,nullptr,0,nullptr,nullptr);
    if (!count) return 2;
    std::string path(count,'\0');
    WideCharToMultiByte(CP_UTF8,WC_ERR_INVALID_CHARS,argv[2],-1,&path[0],count,nullptr,nullptr); path.pop_back();
    return worker(path);
}
#else
int main(int argc,char **argv) { if (argc!=3 || std::string(argv[1])!="--model") return 2; return worker(argv[2]); }
#endif

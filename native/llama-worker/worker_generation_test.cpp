// Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0
// Independent B1 FIRST against contract da794438. SOURCE-ONLY / UNCOMPILED / UNRUN.
// Missing actual header/API/compiler prerequisites are external SETUP_UNRUN, not RED.
// This executable has no arguments, environment/file/process/thread/model access.
// It checks actual DOM admission only, not raw parsing, grammar, inference or quality.
#include "worker_generation.h"
#include <array>
#include <cstdint>
#include <iostream>
#include <limits>
#include <string>

using json = nlohmann::json;
using Admission = GenerationAdmission;

struct Evidence {
    unsigned executed = 0, passed = 0, failed = 0;
    bool setup_unrun = false;
    std::array<const char *, 96> failed_ids{};

    template <class Case> void check(const char * id, Case test) {
        if (executed >= failed_ids.size()) { setup_unrun = true; return; }
        ++executed;
        bool accepted = false;
        try { accepted = test(); }
        catch (...) { accepted = false; } // No exception text, payload or stack is logged.
        if (accepted) ++passed;
        else failed_ids[failed++] = id;
    }

    int finish() const {
        // 90 fixed three-character IDs: even all failures plus this fixed schema
        // fit below1024 bytes. No raw request or implementation exception enters stdout.
        const char * status = setup_unrun ? "setup_unrun" : failed ? "failed" : "passed";
        std::cout << "{\"version\":1,\"kind\":\"worker_generation_review_v1\",\"status\":\""
                  << status << "\",\"executed\":" << executed << ",\"passed\":" << passed
                  << ",\"failed\":" << failed << ",\"ignored\":0,\"setup_unrun\":"
                  << (setup_unrun ? "true" : "false") << ",\"failed_case_ids\":[";
        for (unsigned i = 0; i < failed; ++i) {
            if (i) std::cout << ',';
            std::cout << '"' << failed_ids[i] << '"';
        }
        std::cout << "]}\n";
        return setup_unrun ? 2 : failed ? 1 : 0;
    }
};

static json request(const char * role, std::uint64_t tokens) {
    // Parse real JSON wire numbers. A C++ signed integer initializer would make
    // a different DOM type and is unsuitable as a positive unsigned control.
    return json::parse(std::string("{\"role\":\"") + role
        + "\",\"prompt\":\"Fixed synthetic input.\",\"schema\":{},\"max_tokens\":"
        + std::to_string(tokens) + "}");
}
static bool admitted(const json & value, Admission policy,
                     std::uint16_t tokens, std::size_t bytes) {
    const auto actual = locallore_generation_limits(value, policy);
    return actual && actual->output_tokens == tokens && actual->text_bytes == bytes;
}
static bool refused(const json & value, Admission policy) {
    return !locallore_generation_limits(value, policy);
}
static bool refused_in_both(const json & value) {
    return refused(value, Admission::LegacyPlayV1)
        && refused(value, Admission::InitialWorldExperimentalV1);
}
static json field(json value, const char * name, const json & replacement) {
    value[name] = replacement;
    return value;
}

int main() {
    Evidence evidence;
    try {
        const auto legacy = Admission::LegacyPlayV1;
        const auto experimental = Admission::InitialWorldExperimentalV1;
        const json director = request("director", 64);
        const json narrator = request("narrator", 350);
        const json author = request("author", 64);
        if (!director.at("max_tokens").is_number_unsigned()
            || !narrator.at("max_tokens").is_number_unsigned()
            || !author.at("max_tokens").is_number_unsigned()) {
            evidence.setup_unrun = true;
            return evidence.finish();
        }

        // Policy, defaults and exact requested counts. Ceilings are not returned counts.
        evidence.check("P01", [&] { const auto v = locallore_generation_limits(director);
            return v && v->output_tokens == 64 && v->text_bytes == 16384; });
        evidence.check("P02", [&] { const auto v = locallore_generation_limits(narrator);
            return v && v->output_tokens == 350 && v->text_bytes == 16384; });
        evidence.check("P03", [&] { return admitted(request("director", 1), legacy, 1, 16384); });
        evidence.check("P04", [&] { return admitted(request("director", 350), legacy, 350, 16384); });
        evidence.check("P05", [&] { return admitted(request("narrator", 1), legacy, 1, 16384); });
        evidence.check("P06", [&] { return refused(request("author", 1), legacy); });
        evidence.check("P07", [&] { return refused(author, legacy); });
        evidence.check("P08", [&] { return refused(request("author", 1024), legacy); });
        evidence.check("P09", [&] { return admitted(director, experimental, 64, 16384); });
        evidence.check("P10", [&] { return admitted(narrator, experimental, 350, 16384); });
        evidence.check("P11", [&] { return admitted(request("author", 1), experimental, 1, 8192); });
        evidence.check("P12", [&] { return admitted(author, experimental, 64, 8192); });
        evidence.check("P13", [&] { return admitted(request("author", 1024), experimental, 1024, 8192); });
        evidence.check("P14", [&] { return !locallore_generation_limits(author); });

        // Numeric representations and bounds, checked before narrowing to uint16.
        evidence.check("N01", [&] { return refused(request("director", 0), legacy); });
        evidence.check("N02", [&] { return refused(request("narrator", 351), legacy); });
        evidence.check("N03", [&] { return refused(request("director", 351), experimental); });
        evidence.check("N04", [&] { return refused(request("narrator", 351), experimental); });
        evidence.check("N05", [&] { return refused(request("author", 0), experimental); });
        evidence.check("N06", [&] { return refused(request("author", 1025), experimental); });
        evidence.check("N07", [&] { return refused_in_both(field(director, "max_tokens", true))
            && refused(field(author, "max_tokens", true), experimental); });
        evidence.check("N08", [&] { return refused_in_both(field(director, "max_tokens", -1))
            && refused(field(author, "max_tokens", -1), experimental); });
        // Explicit signed-positive DOM control; positive wire JSON is unsigned instead.
        evidence.check("N09", [&] { return refused_in_both(field(director, "max_tokens", json::number_integer_t(64)))
            && refused(field(author, "max_tokens", json::number_integer_t(64)), experimental); });
        evidence.check("N10", [&] { return refused_in_both(field(director, "max_tokens", 64.0))
            && refused(field(author, "max_tokens", 64.0), experimental); });
        evidence.check("N11", [&] { return refused_in_both(field(director, "max_tokens", "64"))
            && refused(field(author, "max_tokens", "64"), experimental); });
        evidence.check("N12", [&] { return refused_in_both(field(director, "max_tokens", nullptr))
            && refused(field(author, "max_tokens", nullptr), experimental); });
        evidence.check("N13", [&] { return refused_in_both(field(director, "max_tokens", json::array({64})))
            && refused(field(author, "max_tokens", json::array({64})), experimental); });
        evidence.check("N14", [&] { return refused_in_both(field(director, "max_tokens", json::object()))
            && refused(field(author, "max_tokens", json::object()), experimental); });
        evidence.check("N15", [&] { return refused_in_both(request("director", std::numeric_limits<std::uint64_t>::max()))
            && refused(request("author", std::numeric_limits<std::uint64_t>::max()), experimental); });
        evidence.check("N16", [&] { const auto number = json::parse("18446744073709551616");
            return refused_in_both(field(director, "max_tokens", number))
                && refused(field(author, "max_tokens", number), experimental); });
        evidence.check("N17", [&] { return refused(request("author", 65537), experimental); });
        evidence.check("N18", [&] { return refused(request("author", 66560), experimental); });
        evidence.check("N19", [&] { return refused(request("director", 65537), legacy); });
        evidence.check("N20", [&] { return refused(request("director", 65886), experimental); });

        // Root shape and the exact four-key contract. No opaque authority objects.
        evidence.check("S01", [&] { return refused_in_both(nullptr); });
        evidence.check("S02", [&] { return refused_in_both(json::array()); });
        evidence.check("S03", [&] { return refused_in_both("generation"); });
        evidence.check("S04", [&] { return refused_in_both(json::number_unsigned_t(1)); });
        evidence.check("S05", [&] { return refused_in_both(true); });
        evidence.check("S06", [&] { auto v = director; v.erase("role"); return refused_in_both(v); });
        evidence.check("S07", [&] { auto v = director; v.erase("prompt"); return refused_in_both(v); });
        evidence.check("S08", [&] { auto v = director; v.erase("schema"); return refused_in_both(v); });
        evidence.check("S09", [&] { auto v = director; v.erase("max_tokens"); return refused_in_both(v); });
        evidence.check("S10", [&] { return refused_in_both(field(director, "authority", json::parse("{\"grant\":true,\"op\":\"create\"}"))); });
        evidence.check("S11", [&] { auto v = director; v.erase("role"); v["Role"] = "director"; return refused_in_both(v); });
        evidence.check("S12", [&] { return refused_in_both(field(director, "prompt", nullptr)); });
        evidence.check("S13", [&] { return refused_in_both(field(director, "prompt", json::object())); });
        evidence.check("S14", [&] { return refused_in_both(field(director, "prompt", json::array())); });
        evidence.check("S15", [&] { return refused_in_both(field(director, "prompt", true)); });
        evidence.check("S16", [&] { return refused_in_both(field(director, "prompt", json::number_unsigned_t(1))); });

        // Role identity is exact and independent of content that looks like an operation.
        evidence.check("R01", [&] { return refused_in_both(field(director, "role", "tool")); });
        evidence.check("R02", [&] { return refused_in_both(field(director, "role", "Author")); });
        evidence.check("R03", [&] { return refused_in_both(field(director, "role", " author")); });
        evidence.check("R04", [&] { return refused_in_both(field(director, "role", "author ")); });
        evidence.check("R05", [&] { return refused_in_both(field(director, "role", "authoring_generate")); });
        evidence.check("R06", [&] { return refused_in_both(field(director, "role", true)); });
        evidence.check("R07", [&] { return refused_in_both(field(director, "role", nullptr)); });
        evidence.check("R08", [&] { return refused_in_both(field(director, "role", json::object())); });
        evidence.check("R09", [&] { return refused_in_both(field(director, "role", json::array())); });
        evidence.check("R10", [&] { return refused_in_both(field(director, "role", json::number_unsigned_t(1))); });

        const std::string ascii_limit(16384, 'x');
        std::string utf8_limit;
        for (unsigned i = 0; i < 8192; ++i) utf8_limit += "\xc3\xa9";
        evidence.check("T01", [&] { return refused(field(author, "prompt", ""), experimental); });
        evidence.check("T02", [&] { return refused(field(author, "prompt", std::string("x\0y", 3)), experimental); });
        evidence.check("T03", [&] { return admitted(field(author, "prompt", ascii_limit), experimental, 64, 8192); });
        evidence.check("T04", [&] { return refused(field(author, "prompt", ascii_limit + "x"), experimental); });
        evidence.check("T05", [&] { return admitted(field(author, "prompt", utf8_limit), experimental, 64, 8192); });
        evidence.check("T06", [&] { return refused(field(author, "prompt", utf8_limit + "x"), experimental); });
        evidence.check("T07", [&] { return admitted(field(director, "prompt", ascii_limit + "x"), experimental, 64, 16384); });
        evidence.check("T08", [&] { return admitted(field(director, "prompt", ascii_limit + "x"), legacy, 64, 16384); });
        evidence.check("T09", [&] { return refused_in_both(field(director, "prompt", "")); });
        evidence.check("T10", [&] { return refused_in_both(field(director, "prompt", std::string("x\0y", 3))); });
        evidence.check("T11", [&] { return admitted(field(author, "prompt", " "), experimental, 64, 8192); });
        evidence.check("T12", [&] { const auto v = field(author, "prompt", "{\"op\":\"create\",\"grant\":true}");
            return admitted(v, experimental, 64, 8192) && refused(v, legacy); });

        // Schema shape only. Exact canonical proposal/schema validation remains in Rust.
        evidence.check("C01", [&] { return refused(field(author, "schema", nullptr), experimental); });
        evidence.check("C02", [&] { return admitted(field(author, "schema", json::object()), experimental, 64, 8192); });
        evidence.check("C03", [&] { return refused(field(author, "schema", json::array()), experimental); });
        evidence.check("C04", [&] { return refused(field(author, "schema", true), experimental); });
        evidence.check("C05", [&] { return refused(field(author, "schema", "object"), experimental); });
        evidence.check("C06", [&] { return refused(field(author, "schema", json::number_unsigned_t(1)), experimental); });
        evidence.check("C07", [&] { const auto v = field(director, "schema", nullptr);
            return admitted(v, legacy, 64, 16384) && admitted(v, experimental, 64, 16384); });
        evidence.check("C08", [&] { const auto v = field(director, "schema", json::object());
            return admitted(v, legacy, 64, 16384) && admitted(v, experimental, 64, 16384); });
        evidence.check("C09", [&] { return refused_in_both(field(director, "schema", json::array())); });
        evidence.check("C10", [&] { return refused_in_both(field(director, "schema", true)); });
        evidence.check("C11", [&] { return refused_in_both(field(director, "schema", "object")); });
        evidence.check("C12", [&] { return refused_in_both(field(director, "schema", json::number_unsigned_t(1))); });

        evidence.check("E01", [&] { return refused(director, static_cast<Admission>(255)); });
        evidence.check("E02", [&] { return refused(author, static_cast<Admission>(255)); });
        evidence.check("I01", [&] { return admitted(author, experimental, 64, 8192)
            && admitted(director, experimental, 64, 16384) && refused(author, legacy)
            && admitted(narrator, legacy, 350, 16384)
            && admitted(request("author", 1), experimental, 1, 8192); });
        evidence.check("I02", [&] { auto v = author; const auto first = locallore_generation_limits(v, experimental);
            v["role"] = "director"; v["max_tokens"] = json::number_unsigned_t(350);
            const auto second = locallore_generation_limits(v, experimental);
            return first && second && first->output_tokens == 64 && first->text_bytes == 8192
                && second->output_tokens == 350 && second->text_bytes == 16384; });
        evidence.check("I03", [&] { const auto before = director;
            (void)locallore_generation_limits(director, legacy);
            (void)locallore_generation_limits(director, experimental);
            return director == before; });
        evidence.check("I04", [&] { const auto v = field(director, "prompt", "{\"role\":\"author\",\"op\":\"create\"}");
            return admitted(v, legacy, 64, 16384) && admitted(v, experimental, 64, 16384); });
    } catch (...) {
        // Closed fixture/harness construction failure, never a claimed behavioral RED.
        evidence.setup_unrun = true;
    }
    return evidence.finish();
}

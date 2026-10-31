// Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0
#pragma once
#include "nlohmann/json.hpp"
#include <cstddef>
#include <cstdint>
#include <optional>
#include <string>

enum class GenerationAdmission { LegacyPlayV1, InitialWorldExperimentalV1 };
struct GenerationLimits {
    std::uint16_t output_tokens;
    std::size_t text_bytes;
};

inline std::optional<GenerationLimits> locallore_generation_limits(
    const nlohmann::json & g,
    GenerationAdmission admission = GenerationAdmission::LegacyPlayV1) {
    if (admission != GenerationAdmission::LegacyPlayV1 &&
        admission != GenerationAdmission::InitialWorldExperimentalV1) return std::nullopt;
    if (!g.is_object() || g.size()!=4 || !g.contains("role") || !g["role"].is_string() || (g["role"]!="director" && g["role"]!="narrator") || !g.contains("prompt") || !g["prompt"].is_string() || g["prompt"].get<std::string>().empty() || g["prompt"].get<std::string>().find('\0')!=std::string::npos || !g.contains("schema") || (!g["schema"].is_null() && !g["schema"].is_object()) || !g.contains("max_tokens") || !g["max_tokens"].is_number_unsigned() || g["max_tokens"]<1 || g["max_tokens"]>350) return std::nullopt;
    return GenerationLimits{g["max_tokens"].get<std::uint16_t>(), 16384};
}

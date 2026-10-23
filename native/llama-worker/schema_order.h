// Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0
#pragma once
#include "json.h"
#include "nlohmann/json.hpp"

// The pinned converter fixes required-key order from `properties` insertion order,
// rather than the JSON Schema `required` array. Keep the branch discriminator first;
// alphabetical nlohmann::json transport order would force Give.item before Give.op.
inline common_json locallore_ordered_schema(const nlohmann::json & value, bool properties=false) {
    if (value.is_array()) {
        auto result=common_json::array();
        for (const auto & item:value) result.push_back(locallore_ordered_schema(item));
        return result;
    }
    if (!value.is_object()) return common_json::parse(value.dump());
    auto result=common_json::object();
    const std::vector<std::string> preferred={"op","text","item","to","quantity","audience","ability","claim_event","fact","ticks","event_ids","speaker"};
    if(properties) {
        for(const auto & key:preferred) if(value.contains(key)) result[key]=locallore_ordered_schema(value.at(key));
    }
    for(auto it=value.begin();it!=value.end();++it) {
        if (!result.contains(it.key())) result[it.key()]=locallore_ordered_schema(it.value(),it.key()=="properties");
    }
    return result;
}

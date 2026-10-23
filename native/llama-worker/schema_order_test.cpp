// Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0
// Development-only, model-free check using the actual pinned converter and grammar machine.
#include "schema_order.h"
#include "json-schema-to-grammar.h"
#include "llama-grammar.h"
#include <iostream>
#include <memory>
#include <stdexcept>
using json=nlohmann::json;
static bool matches(const std::string & grammar,const std::string & text) {
    std::unique_ptr<llama_grammar,decltype(&llama_grammar_free_impl)> owner(
        llama_grammar_init_impl(nullptr,grammar.c_str(),"root",false,nullptr,0,nullptr,0),llama_grammar_free_impl);
    if(!owner)throw std::runtime_error("grammar_parse");
    for(unsigned char c:text) {
        llama_grammar_accept(owner.get(),c);
        if(llama_grammar_get_stacks(owner.get()).empty())return false;
    }
    for(const auto & stack:llama_grammar_get_stacks(owner.get()))if(stack.empty())return true;
    return false;
}
static void require(bool condition,const char * label){if(!condition)throw std::runtime_error(label);}
int main(){
    try {
        // Construct through the same sorted transport JSON used in the real worker.
        const auto action=json::parse(R"({"type":"object","properties":{"commands":{"type":"array","minItems":1,"maxItems":8,"items":{"oneOf":[{"type":"object","properties":{"op":{"const":"give"},"item":{"type":"string"},"to":{"type":"string"},"quantity":{"type":"integer","minimum":1,"maximum":65535}},"required":["op","item","to","quantity"],"additionalProperties":false},{"type":"object","properties":{"op":{"const":"wait"},"ticks":{"type":"integer","minimum":1,"maximum":100}},"required":["op","ticks"],"additionalProperties":false}]}}},"required":["commands"],"additionalProperties":false})");
        const auto ordered=locallore_ordered_schema(action);
        require(json::parse(ordered.dump())==action,"unchanged_schema_semantics");
        const auto old=json_schema_to_grammar(common_json::parse(action.dump()));
        const auto fixed=json_schema_to_grammar(ordered);
        const std::string give=R"({"commands":[{"op":"give","item":"potion","to":"mira","quantity":1}]})";
        require(!matches(old,give),"original_rejects_op_first_give");
        require(matches(old,R"({"commands":[{"item":"potion","op":"give","quantity":1,"to":"mira"}]})"),"original_sorted_order_reproduced");
        require(matches(fixed,give),"fixed_accepts_op_first_give");
        require(matches(fixed,R"({"commands":[{"op":"wait","ticks":1}]})"),"wait_still_supported");
        require(!matches(fixed,R"({"commands":[{"op":"steal","item":"potion","to":"mira","quantity":1}]})"),"unknown_operation_rejects");
        require(!matches(fixed,R"({"commands":[{"op":"give","item":"potion","to":"mira","quantity":0}]})"),"quantity_bound_preserved");
        require(!matches(fixed,R"({"commands":[{"op":"give","item":"potion","to":"mira","quantity":1,"extra":true}]})"),"unknown_field_rejects");
        const auto narrator=json::parse(R"({"type":"object","properties":{"text":{"type":"string","maxLength":4096},"event_ids":{"const":[1]},"speaker":{"const":"narrator"}},"required":["text","event_ids","speaker"],"additionalProperties":false})");
        const auto narrator_fixed=json_schema_to_grammar(locallore_ordered_schema(narrator));
        require(matches(narrator_fixed,R"({"text":"You pass the potion to Mira.","event_ids":[1],"speaker":"narrator"})"),"text_first_narrator_supported");
        require(!matches(narrator_fixed,R"({"text":"You pass the potion to Mira.","event_ids":[2],"speaker":"narrator"})"),"event_reference_const_preserved");
        require(!matches(narrator_fixed,R"({"text":"You pass the potion to Mira.","event_ids":[1],"speaker":"mira"})"),"speaker_const_preserved");
        const auto dialogue=json::parse(R"({"type":"object","properties":{"commands":{"type":"array","minItems":1,"maxItems":1,"items":{"type":"object","properties":{"op":{"const":"say"},"text":{"const":"Hello Mira"},"audience":{"type":"array","items":{"type":"string"},"minItems":1,"maxItems":4}},"required":["op","text","audience"],"additionalProperties":false}}},"required":["commands"],"additionalProperties":false})");
        const auto dialogue_fixed=json_schema_to_grammar(locallore_ordered_schema(dialogue));
        require(matches(dialogue_fixed,R"({"commands":[{"op":"say","text":"Hello Mira","audience":["mira"]}]})"),"say_field_order_supported");
        require(!matches(dialogue_fixed,R"({"commands":[{"op":"say","text":"Changed words","audience":["mira"]}]})"),"dialogue_literal_preserved");
        std::cout<<R"({"status":"passed","native_grammar_assertions":13,"old_op_first_give_rejected":true,"fixed_op_first_give_accepted":true,"model_loaded":false})"<<'\n';
        return 0;
    }catch(const std::exception & error){std::cout<<json({{"status","failed"},{"case",error.what()}}).dump()<<'\n';return 1;}
}

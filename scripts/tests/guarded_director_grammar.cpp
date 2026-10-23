// Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0
// Development-only: actual pinned converter/grammar machine, no model/worker modification.
#include "schema_order.h"
#include "json-schema-to-grammar.h"
#include "llama-grammar.h"
#include <fstream>
#include <iostream>
#include <memory>
#include <stdexcept>
using json=nlohmann::json;
static bool matches(const std::string &grammar,const std::string &text) {
    std::unique_ptr<llama_grammar,decltype(&llama_grammar_free_impl)> owner(
        llama_grammar_init_impl(nullptr,grammar.c_str(),"root",false,nullptr,0,nullptr,0),llama_grammar_free_impl);
    if(!owner)throw std::runtime_error("grammar_parse");
    for(unsigned char c:text){llama_grammar_accept(owner.get(),c);if(llama_grammar_get_stacks(owner.get()).empty())return false;}
    for(const auto &stack:llama_grammar_get_stacks(owner.get()))if(stack.empty())return true;
    return false;
}
static std::string output(const json &value) {
    auto ordered=common_json::object();
    ordered["commands"]=common_json::array();
    for(const auto &command:value.at("commands"))ordered["commands"].push_back(locallore_ordered_schema(command,true));
    for(auto it=value.begin();it!=value.end();++it)if(it.key()!="commands")ordered[it.key()]=locallore_ordered_schema(it.value());
    return ordered.dump();
}
int main(int argc,char **argv){
    try {
        if(argc!=2)throw std::runtime_error("synthetic_case_file_required");
        std::ifstream input(argv[1]);json cases;input>>cases;
        if(cases.at("synthetic")!=true||cases.at("prompt_version")!="locallore-play-v2.3"||cases.at("cases").size()!=10)throw std::runtime_error("wrong_source_cases");
        unsigned assertions=0;
        for(const auto &test:cases.at("cases")) {
            const auto grammar=json_schema_to_grammar(locallore_ordered_schema(test.at("schema")));
            if(!matches(grammar,output(test.at("valid"))))throw std::runtime_error("valid_rejected:"+test.at("label").get<std::string>());
            assertions++;
            for(const auto &bad:test.at("invalid")) {
                if(matches(grammar,output(bad)))throw std::runtime_error("invalid_accepted:"+test.at("label").get<std::string>());
                assertions++;
            }
        }
        std::cout<<json({{"status","passed"},{"cases",10},{"native_grammar_assertions",assertions},{"model_loaded",false}}).dump()<<'\n';return 0;
    }catch(const std::exception &error){std::cout<<json({{"status","failed"},{"case",error.what()}}).dump()<<'\n';return 1;}
}

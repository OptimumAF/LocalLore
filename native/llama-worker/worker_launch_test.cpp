// Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0
#include "worker_launch.h"
#include <iostream>
#include <stdexcept>
#include <system_error>
int main() {
    std::atomic<bool> busy{false};
    std::atomic<unsigned> calls{0};
    std::thread work;
    auto task=[&] { ++calls; busy.store(false); };
    const bool failed=locallore_launch_work(work,busy,task,[](decltype(task)) -> std::thread {
        throw std::system_error(std::make_error_code(std::errc::resource_unavailable_try_again));
    });
    if(failed || busy.load() || work.joinable() || calls.load()!=0) throw std::runtime_error("failed_launch_cleanup");
    if(!locallore_launch_work(work,busy,task)) throw std::runtime_error("recovery_launch");
    work.join();
    if(busy.load() || calls.load()!=1) throw std::runtime_error("recovery_completion");
    std::cout << "{\"status\":\"passed\",\"native_launch_assertions\":3,\"model_loaded\":false}\n";
}

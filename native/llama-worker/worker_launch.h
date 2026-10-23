// Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0
#pragma once
#include <atomic>
#include <thread>
#include <utility>

// No operation owns native state unless its thread was actually created.
// The injectable launcher is used only by the model-free development test.
template<class Task, class Launcher>
bool locallore_launch_work(std::thread & work, std::atomic<bool> & busy, Task task, Launcher launch) {
    busy.store(true);
    try {
        work = launch(std::move(task));
        return true;
    } catch (...) {
        busy.store(false);
        return false;
    }
}
template<class Task>
bool locallore_launch_work(std::thread & work, std::atomic<bool> & busy, Task task) {
    return locallore_launch_work(work, busy, std::move(task), [](Task run) { return std::thread(std::move(run)); });
}

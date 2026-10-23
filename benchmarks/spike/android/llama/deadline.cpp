// Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0
// Standalone Android experiment only. No worker thread, signal logger or child.
#include <signal.h>
#include <unistd.h>

namespace {
constexpr unsigned int deadline_seconds = 90;
static_assert(deadline_seconds == 90, "Review the fixed experiment deadline before changing it");
}

// Linked directly into the executable; .init_array retention is audited after
// linking. Priority 101 runs before ordinary C++ dynamic initialization/main.
extern "C" __attribute__((constructor(101), used))
void locallore_android_arm_deadline() {
    sigset_t signals;
    if (signal(SIGALRM, SIG_DFL) == SIG_ERR ||
        sigemptyset(&signals) != 0 || sigaddset(&signals, SIGALRM) != 0 ||
        sigprocmask(SIG_UNBLOCK, &signals, nullptr) != 0) {
        _exit(124);
    }
    // Default SIGALRM terminates this process even after the host/ADB dies.
    // This is abrupt OS cleanup, not a cooperative model/session shutdown.
    alarm(deadline_seconds);
}
